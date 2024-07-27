from utils.bcc_import_trick import bcc_import_trick

bcc_import_trick()

import argparse
from queue import Queue
import threading

from reporters.stdout import StdoutReporter
from reporters.terminal import TerminalReporter
from tracers.bcc_trace_only_gil import OnlyGilBccTracer
from tracers.bcc_trace_with_lines import GilWithLinesBccTracer
from utils.symbol_finder import find_binaries_by_symbols


parser = argparse.ArgumentParser(
    description="Time/Print GIL stats per-thread",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument("-p", "--pid", type=int, required=True, help="trace this PID only")
parser.add_argument(
    "-b",
    "--binary",
    type=str,
    required=False,
    default=None,
    help="""
Binary that contains the GIL-management symbols.
Usually it's either the python executable itself or a shared library such as libpython3.10d.so.1.0.

You can manually find the needed library by reading the /proc/{pid}/maps file or calling `ldd {python_executable}`.
Then check which of these libraries define the threading primitives: `nm --defined-only --dynamic {lib_path} | grep gil`.
""",
)
parser.add_argument(
    "-m",
    "--mode",
    type=str,
    choices=["gil", "gil_and_lines"],
    required=False,
    default="gil",
    help="""
Tracing mode.
- gil - only trace operations on GIL
- gil_and_lines - also trace on which Python instruction the program takes/drops GIL.
                  This mode requires CPython compiled with --with-dtrace. 
""",
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    choices=["stdout", "terminal_app"],
    required=False,
    default="terminal_app",
    help="""
Output format.
- stdout - prints raw events to stdout
- terminal_app - shows aggregated stats in an interactive terminal UI. 
""",
)


def main():
    args = parser.parse_args()

    binary = args.binary
    if binary is None:
        found_binaries = find_binaries_by_symbols(
            args.pid, ["take_gil", "python_line", "pthread_cond_wait", "sem_wait"]
        )
        if "take_gil" not in found_binaries and args.mode in ("gil", "gil_and_lines"):
            raise Exception("Found no debug info in the binaries, can not trace GIL")

        if "python_line" not in found_binaries and args.mode == "gil_and_lines":
            raise Exception(
                "CPython isn't compiled with --with-dtrace, can not trace with line info"
            )

        binary = found_binaries["take_gil"]

    if args.mode == "gil":
        tracer = OnlyGilBccTracer(binary=binary, pid=args.pid)
    else:
        tracer = GilWithLinesBccTracer(binary=binary, pid=args.pid)

    event_queue = Queue()

    if args.output == "stdout":
        reporter = StdoutReporter()
    else:
        reporter = TerminalReporter(args.pid)

    tracer_thread = threading.Thread(
        target=tracer.trace, args=[event_queue], daemon=True
    )
    tracer_thread.start()
    reporter.subscribe(event_queue)


if __name__ == "__main__":
    main()
