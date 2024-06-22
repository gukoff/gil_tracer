struct data_t {
    u64 thread_id;
    u64 timestamp;
    u8 holds_gil;  // 1 if holds GIL, 0 if dropped GIL
};

BPF_PERF_OUTPUT(events);

int take_gil_exit(struct pt_regs *ctx) {
    u64 curr_tid = bpf_get_current_pid_tgid() & 0x00000000FFFFFFFF;
    u64 now = bpf_ktime_get_ns();

    struct data_t data = {};
    data.thread_id = curr_tid;
    data.timestamp = now;
    data.holds_gil = 1;


    events.perf_submit(ctx, &data, sizeof(data));
    // events.push(&data, 0 /* flags */);

    return 0;
};


int drop_gil_entry(struct pt_regs *ctx) {
    u64 curr_tid = bpf_get_current_pid_tgid() & 0x00000000FFFFFFFF;
    u64 now = bpf_ktime_get_ns();

    struct data_t data = {};
    data.thread_id = curr_tid;
    data.timestamp = now;
    data.holds_gil = 0;

    events.perf_submit(ctx, &data, sizeof(data));
    // events.push(&data, 0 /* flags */);

    return 0;
};