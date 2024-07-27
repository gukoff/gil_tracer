struct data_t {
    u64 thread_id;
    u64 timestamp;
    u8 event_type;  // 0 if started waiting for GIL, 1 if took GIL, 2 if dropped GIL
};

BPF_PERF_OUTPUT(events);


int take_gil_entry(struct pt_regs *ctx) {
    u64 now = bpf_ktime_get_ns();
    u64 curr_tid = bpf_get_current_pid_tgid() & 0x00000000FFFFFFFF;

    struct data_t data = {};
    data.thread_id = curr_tid;
    data.timestamp = now;
    data.event_type = 0;


    events.perf_submit(ctx, &data, sizeof(data));
    // events.push(&data, 0 /* flags */);

    return 0;
};


int take_gil_exit(struct pt_regs *ctx) {
    u64 now = bpf_ktime_get_ns();
    u64 curr_tid = bpf_get_current_pid_tgid() & 0x00000000FFFFFFFF;

    struct data_t data = {};
    data.thread_id = curr_tid;
    data.timestamp = now;
    data.event_type = 1;


    events.perf_submit(ctx, &data, sizeof(data));
    // events.push(&data, 0 /* flags */);

    return 0;
};


int drop_gil_entry(struct pt_regs *ctx) {
    u64 now = bpf_ktime_get_ns();
    u64 curr_tid = bpf_get_current_pid_tgid() & 0x00000000FFFFFFFF;

    struct data_t data = {};
    data.thread_id = curr_tid;
    data.timestamp = now;
    data.event_type = 2;

    events.perf_submit(ctx, &data, sizeof(data));
    // events.push(&data, 0 /* flags */);

    return 0;
};