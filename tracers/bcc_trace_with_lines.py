from pathlib import Path
from queue import Queue
from models.models import Event, ThreadState


class GilWithLinesBccTracer:
    def __init__(self, binary: str, pid: int) -> None:
        self.binary = binary
        self.pid = pid

    def trace(self, event_destination: Queue):
        # delay bcc import to runtime in case the user doesn't have bcc installed
        # and wants to trace using bpftrace
        from bcc import BPF, USDT

        code_file = Path(__file__).parent.parent / "tracing_programs" / "trace_with_lines.c"
        code = code_file.read_text()

        usdt = USDT(pid=self.pid)
        usdt.enable_probe(probe="line", fn_name="trace_line")
        bpf = BPF(text=code, usdt_contexts=[usdt], cflags=["-Wno-macro-redefined"])

        bpf.attach_uprobe(
            name=self.binary,
            sym_re="^take_gil",
            fn_name="take_gil_entry",
            pid=self.pid,
        )

        bpf.attach_uretprobe(
            name=self.binary,
            sym_re="^take_gil",
            fn_name="take_gil_exit",
            pid=self.pid,
        )

        bpf.attach_uprobe(
            name=self.binary, sym_re="^drop_gil", fn_name="drop_gil_entry", pid=self.pid
        )

        perf_buffer = bpf["events"]

        def handle_event(cpu, data, size):
            event = perf_buffer.event(data)

            event_destination.put(
                Event(
                    timestamp=event.timestamp,
                    thread_id=event.thread_id,
                    location=(
                        f"{event.filename.decode()} | {event.function.decode()}:{event.line_number}"
                        if event.event_type == 0
                        else None
                    ),
                    new_state=ThreadState(event.event_type),
                )
            )

        perf_buffer.open_perf_buffer(handle_event)

        while True:
            bpf.perf_buffer_poll()
