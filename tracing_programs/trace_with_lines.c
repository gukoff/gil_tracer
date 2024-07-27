struct python_line_context_t {
    char filename[64];
    char function[64];
    u32 line_number;
};

BPF_HASH(py_context, u64, struct python_line_context_t);


struct data_t {
    u64 thread_id;
    u64 timestamp;
    u8 event_type;  // 0 if started waiting for GIL, 1 if took GIL, 2 if dropped GIL
    char filename[64];
    char function[64];
    u32 line_number;
};

BPF_PERF_OUTPUT(events);

static int emit_event(struct pt_regs *ctx, u8 event_type, bool include_location) {
    u64 now = bpf_ktime_get_ns();
    u64 curr_tid = bpf_get_current_pid_tgid() & 0x00000000FFFFFFFF;

    struct data_t data = {};
    data.thread_id = curr_tid;
    data.timestamp = now;
    data.event_type = event_type;

    if (include_location) {
        struct python_line_context_t* thread_py_context = py_context.lookup(&curr_tid);
        if (thread_py_context) {
            for (u32 i = 0; i < sizeof(data.filename); ++i) {
                data.filename[i] = thread_py_context->filename[i];
            }
            for (u32 i = 0; i < sizeof(data.function); ++i) {
                data.function[i] = thread_py_context->function[i];
            }
            data.line_number = thread_py_context->line_number;
        }
    }

    events.perf_submit(ctx, &data, sizeof(data));
    // events.push(&data, 0 /* flags */);

    return 0;
}


int take_gil_entry(struct pt_regs *ctx) {
    return emit_event(ctx, /* event_type */ 0, /*include_location*/ true);
};

int take_gil_exit(struct pt_regs *ctx) {
    return emit_event(ctx, /* event_type */ 1, /*include_location*/ false);
};

int drop_gil_entry(struct pt_regs *ctx) {
    return emit_event(ctx, /* event_type */ 2, /*include_location*/ false);
};


int trace_line(struct pt_regs *ctx) {
    u64 curr_tid = bpf_get_current_pid_tgid() & 0x00000000FFFFFFFF;

    struct python_line_context_t data = {};

    bpf_usdt_readarg_p(1, ctx, data.filename, sizeof(data.filename));
    bpf_usdt_readarg_p(2, ctx, data.function, sizeof(data.function));
    bpf_usdt_readarg(3, ctx, &data.line_number);

    py_context.update(&curr_tid, &data);
    
    return 0;
};
