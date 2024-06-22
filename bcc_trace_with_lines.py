from bcc import BPF, USDT

def trace_with_lines(binary: str, pid: int):
    with open('./tracing_programs/trace_with_lines.c') as fin:
        code = fin.read()

    usdt = USDT(pid=pid)
    usdt.enable_probe(probe="line", fn_name="trace_line")
    bpf = BPF(text=code, usdt_contexts=[usdt], cflags=["-Wno-macro-redefined"])

    bpf.attach_uretprobe(
        name=binary,
        sym_re="^take_gil",
        fn_name="take_gil_exit",
        pid=pid,
    )

    bpf.attach_uprobe(
        name=binary,
        sym_re="^drop_gil",
        fn_name="drop_gil_entry",
        pid=pid
    )

    perf_buffer = bpf["events"]

    def handle_event(cpu, data, size):
        event = perf_buffer.event(data)
        print(event.holds_gil, event.timestamp, event.thread_id, event.filename, event.function, event.line_number)

    perf_buffer.open_perf_buffer(handle_event)

    while True:
        bpf.perf_buffer_poll()
