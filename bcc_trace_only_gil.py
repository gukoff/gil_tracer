from bcc import BPF

def trace_only_gil(binary: str, pid: int):
    with open('./tracing_programs/trace_only_gil.c') as fin:
        code = fin.read()

    bpf = BPF(text=code, cflags=["-Wno-macro-redefined"])

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
        print(event.holds_gil, event.timestamp, event.thread_id)

    perf_buffer.open_perf_buffer(handle_event)

    while True:
        bpf.perf_buffer_poll()
