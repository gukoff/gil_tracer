# GIL tracer

No overhead GIL tracer for CPython on Linux.

Full introspection into GIL activity.

**Work-in-progres.**

## Next steps

- general library API
    - separate data collection from the frontends?

- collecting trace data
    - also add a speculative probe on sem_wait/pthread_cond_wait like in gilstats.py. It won't require debuginfo in CPython.
    - also collect events when take_gil started
    - find out why can't compile with BPF_RINGBUF_OUTPUT on Ubuntu 20.04. Likely culprit - https://github.com/iovisor/bcc/issues/2678 . Is it bad though?
    - does it make sense to also collect ustack to have more visibility into GIL operations within C-extensions?

- frontends
    - raw data to console or to file
    - transform to trace event format https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview
    - compute stats like gilstats.py
    - real-time monitor with stats and hotspots (which function waits for GIL the longest? Which one)
        - (check what py-spy uses)

- misc
    - use pyelftools to find symbols? Can find USDT probes?
    - use readelf to find symbols? It does support USDT.

## Install dependencies

### To trace with BCC

See https://github.com/iovisor/bcc/blob/master/INSTALL.md

### To trace with bpftrace

See https://github.com/bpftrace/bpftrace/blob/master/INSTALL.md

A particularly convenient option is https://github.com/bpftrace/bpftrace/blob/master/INSTALL.md#appimage-install


## Run tracer 

### Trace GIL with BCC

```shell
sudo /usr/bin/python3 main.py -p 7031
```

### Trace GIL with bpftrace

```shell
sudo bpftrace -p $pid tracing_programs/trace_without_lines.d
```

or

```shell
sudo bpftrace -p $pid tracing_programs/trace_with_lines.d
```