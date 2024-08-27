from queue import Queue
import threading
from typing import Dict, List
from rich.text import Text
from statistics import mean
import time

from textual.app import App, ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.containers import Container
from textual.widgets import DataTable, Footer, Label, Static
from textual_plotext import PlotextPlot
from datetime import datetime
from collections import defaultdict
from typing import List
import traces

from models.models import Event, ThreadState

from models.models import ThreadStats


COL_THREADID = r"Thread ID"
COL_HELD = r"%Held"
COL_WAITED = r"%Waited"
COL_FREE = r"%Free"

TABLE_HEADER = [COL_THREADID, COL_HELD, COL_WAITED, COL_FREE]


class CurrentTime(Static):
    def on_mount(self) -> None:
        self.set_interval(
            0.25, lambda: self.update(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )


class GotNewRows(Message):
    def __init__(
        self,
        rows: List[ThreadStats],
        past_total_loads: List[float],
        past_avg_loads: Dict[str, float],
    ) -> None:
        super().__init__()
        self.rows = rows
        self.past_total_loads = past_total_loads
        self.past_avg_loads = past_avg_loads


class TerminalReporter:
    def __init__(self, pid: int):
        self._pid = pid
        self._timeline = GilTimeline()
        self._buffer_ns = 500_000_000  # 0.5s
        self._interval_ns = 1_000_000_000  # 1s

    def _feed_timeline(self, queue):
        while True:
            event: Event = queue.get()
            self._timeline.consume_event(event)

    def subscribe(self, queue: Queue):
        t = threading.Thread(target=self._feed_timeline, args=[queue], daemon=True)
        t.start()
        app = TerminalUI(self._pid, self._timeline)
        app.run()


class GilTimeline:
    def __init__(self):
        self.events_per_thread = defaultdict(
            lambda: {
                ThreadState.wait: traces.TimeSeries(default=0),
                ThreadState.hold: traces.TimeSeries(default=0),
                ThreadState.free: traces.TimeSeries(default=0),
            }
        )
        self.gil_held = traces.TimeSeries(default=0)
        self.tracing_start_time = time.clock_gettime_ns(time.CLOCK_BOOTTIME)

    def consume_event(self, e: Event):
        if (
            self.gil_held.is_empty()
            or self.tracing_start_time < e.timestamp < self.gil_held.first_key()
        ):
            # if the first event is dropping GIL, then at the start we were holding GIL. And vice versa.
            if e.new_state == ThreadState.free:
                self.gil_held[self.tracing_start_time] = 1
            else:
                self.gil_held[self.tracing_start_time] = 0

        if e.new_state == ThreadState.free:
            self.gil_held[e.timestamp] = 0
        elif e.new_state == ThreadState.hold:
            self.gil_held[e.timestamp] = 1

        if e.thread_id not in self.events_per_thread:
            if e.new_state == ThreadState.free:
                # if the first event we saw for the thread is dropping GIL, then at the start it was holding GIL
                self.events_per_thread[e.thread_id][ThreadState.hold].default = 1

        self.events_per_thread[e.thread_id][e.new_state][e.timestamp] = 1
        for other_state in set(ThreadState) - {e.new_state}:
            self.events_per_thread[e.thread_id][other_state][
                e.timestamp
            ] = 0  # turn off other states for this thread

    def get_thread_stats(self, ts_begin: int, ts_end: int):
        return {
            thread_id: {
                ThreadState.wait: events[ThreadState.wait]
                .distribution(ts_begin, ts_end)
                .get(1, 0),
                ThreadState.hold: events[ThreadState.hold]
                .distribution(ts_begin, ts_end)
                .get(1, 0),
                ThreadState.free: events[ThreadState.free]
                .distribution(ts_begin, ts_end)
                .get(1, 0),
            }
            for thread_id, events in self.events_per_thread.items()
        }

    def get_total_hold(self, ts_begin: int, ts_end: int):
        return self.gil_held.distribution(ts_begin, ts_end).get(1, 0)


class UpdateThread(threading.Thread):
    """
    Thread that periodically updates data on the Terminal UI.
    """

    def __init__(self, app: App, timeline: GilTimeline, poll_interval_ns: int) -> None:
        self._app = app
        self._update_requested = threading.Event()
        self._update_requested.set()
        self._canceled = threading.Event()
        self._timeline = timeline
        self._poll_interval_ns = poll_interval_ns
        super().__init__()

    def run(self) -> None:
        buffer_ns = 500_000_000  # 0.5s
        interval_ns = self._poll_interval_ns

        while self._update_requested.wait():
            try:
                if self._canceled.is_set():
                    return
                self._update_requested.clear()

                current_time = time.clock_gettime_ns(time.CLOCK_BOOTTIME)

                thread_stats = self._timeline.get_thread_stats(
                    current_time - buffer_ns - interval_ns,
                    current_time - buffer_ns,
                )

                records = [
                    ThreadStats(
                        tid=thread_id,
                        waited=stats[ThreadState.wait],
                        held=stats[ThreadState.hold],
                        free=stats[ThreadState.free],
                    )
                    for thread_id, stats in thread_stats.items()
                ]

                past_total_loads = [
                    self._timeline.get_total_hold(
                        current_time - buffer_ns - interval_ns * (i + 1),
                        current_time - buffer_ns - interval_ns * i,
                    )
                    for i in range(60)  # total datapoints
                ]

                past_avg_loads = {
                    "1s": self._timeline.get_total_hold(
                        current_time - buffer_ns - 1_000_000_000,
                        current_time - buffer_ns,
                    ),
                    "10s": self._timeline.get_total_hold(
                        current_time - buffer_ns - 10_000_000_000,
                        current_time - buffer_ns,
                    ),
                    "1m": self._timeline.get_total_hold(
                        current_time - buffer_ns - 60_000_000_000,
                        current_time - buffer_ns,
                    ),
                }

                self._app.post_message(
                    GotNewRows(records, past_total_loads, past_avg_loads)
                )
            except Exception as e:
                with open("/tmp/comm.txt", "w") as fout:
                    fout.write(str(e))

    def cancel(self) -> None:
        self._canceled.set()
        self._update_requested.set()

    def schedule_update(self) -> None:
        self._update_requested.set()


class Legend(Widget):
    start = datetime.now()
    last_update = reactive(start)

    def __init__(self, pid: int):
        super().__init__()
        self._pid = str(pid)

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Label(f"[b]PID[/]: {self._pid}", id="pid"),
                Label(id="duration"),
                Label(id="last_update"),
                Label(id="avg1s"),
                Label(id="avg10s"),
                Label(id="avg60s"),
                id="metadata_container",
            ),
            Container(PlotextPlot(), id="gil_usage_graph_container"),
            id="legend_container",
        )

    def watch_last_update(self, last_update: datetime) -> None:
        """Called when the last_update attribute changes."""
        self.query_one("#duration", Label).update(
            f"[b]Duration[/]: {int((last_update - self.start).total_seconds()):>3}s"
        )
        self.query_one("#last_update", Label).update(
            f"[b]Last update[/]: {last_update.strftime('%H:%M:%S')}"
        )


class TerminalUI(App):
    CSS_PATH = "terminal.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "sort_by_thread_id", "Sort By Thread ID"),
        ("w", "sort_by_waited", "Sort By Waited%"),
        ("h", "sort_by_held", "Sort By Held%"),
        ("f", "sort_by_free", "Sort By Free%"),
        ("f", "sort_by_free", "Sort By Free%"),
        ("space", "toggle_pause", "Pause/Continue"),
    ]

    rows = reactive([])

    _column_header_click_action_map = {
        COL_THREADID: "sort_by_thread_id",
        COL_WAITED: "sort_by_waited",
        COL_HELD: "sort_by_held",
        COL_FREE: "sort_by_free",
    }

    def __init__(self, pid: int, timeline: GilTimeline) -> None:
        super().__init__()
        self._pid = pid
        self._timeline = timeline
        self._poll_interval_ns = 1_000_000_000  # 1s
        self._update_thread = UpdateThread(self, timeline, self._poll_interval_ns)
        self._current_sort = (COL_THREADID, False, None)
        self._paused = False

    def compose(self) -> ComposeResult:
        yield Container(Label("[i]GIL Tracer[/]  🔎"), id="head")
        yield Legend(pid=self._pid)
        yield DataTable(header_height=1, show_cursor=False, zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        self._update_thread.start()

        self.set_interval(
            self._poll_interval_ns / 1_000_000_000, self._update_thread.schedule_update
        )
        self.populate_table()

    def on_unmount(self) -> None:
        self._update_thread.cancel()
        if self._update_thread.is_alive():
            self._update_thread.join()

    def populate_table(self) -> None:
        table = self.query_one(DataTable)

        table.clear(columns=False)
        if not table.columns:  # first render
            for col in TABLE_HEADER:
                table.add_column(
                    Text(col, justify="left").on(
                        click=f"app.{self._column_header_click_action_map[col]}"
                    ),
                    key=col,
                    width=len(col) + 1,  # leave space for △/▽ sorting symbols
                )

        table.add_rows(
            [
                (
                    stats.tid,
                    100 * stats.held,
                    100 * stats.waited,
                    100 * max(0, 1 - stats.waited - stats.held),
                )
                for stats in self.rows
            ]
        )
        self.sort_table()

    def update_sort_key(self, column, key=None):
        [current_col, current_sort, _] = self._current_sort
        new_sort = True if current_col != column else not current_sort
        self._current_sort = (column, new_sort, key)
        self.sort_table()

    def sort_table(self):
        table = self.query_one(DataTable)

        [column, sort, key] = self._current_sort
        for col in table.columns.values():
            col.label.plain = col.key.value  # reset all triangles

        col = table.columns.get(column)
        col.label.plain = column + ("▽" if sort else "△")

        table.sort(column, reverse=sort, key=key)

    def action_sort_by_thread_id(self) -> None:
        self.update_sort_key(COL_THREADID)

    def action_sort_by_waited(self) -> None:
        self.update_sort_key(COL_WAITED)

    def action_sort_by_held(self) -> None:
        self.update_sort_key(COL_HELD)

    def action_sort_by_free(self) -> None:
        self.update_sort_key(COL_FREE)

    def on_got_new_rows(self, message: GotNewRows) -> None:
        if not self._paused:
            with self.batch_update():
                self.query_one(Legend).last_update = datetime.now()
                self.rows = message.rows

                plot = self.query_one(PlotextPlot)
                plot.plt.clear_data()
                xs = [
                    -x for x in range(len(message.past_total_loads))
                ]  # assumin 1 data point == 1 second
                ys = [100 * x for x in message.past_total_loads]  # percentage
                plot.plt.plot(xs, ys, marker="braille")
                plot.plt.ylim(0.0, 100.0)
                plot.plt.title("% time GIL held")
                plot.refresh()

                self.query_one("#avg1s", Label).update(
                    f"[b]Avg 1s  %Held[/]: {message.past_avg_loads['1s'] * 100:0.1f}%"
                )
                self.query_one("#avg10s", Label).update(
                    f"[b]Avg 10s %Held[/]: {message.past_avg_loads['10s'] * 100:0.1f}%"
                )
                self.query_one("#avg60s", Label).update(
                    f"[b]Avg 1m  %Held[/]: {message.past_avg_loads['1m'] * 100:0.1f}%"
                )

    def watch_rows(self) -> None:
        self.populate_table()

    def action_toggle_pause(self) -> None:
        self._paused = not self._paused
