# GIL tracer

GIL tracer for CPython on Linux based on eBPF. 

Introspection of the GIL activity of your app.

**This project is work-in-progress.**

## Next steps

- new collectors
  - bpftrace
  - perf
  - raw ftrace 
 
- misc
    - use pyelftools to find symbols? Can it find USDT probes?
    - also add a speculative probe on sem_wait/pthread_cond_wait like in gilstats.py. It won't require debuginfo in CPython.
    - find out why can't compile with BPF_RINGBUF_OUTPUT on Ubuntu 20.04. Likely culprit - https://github.com/iovisor/bcc/issues/2678 . But do we need it?
    - should collect ustack to have more visibility into GIL operations within C-extensions?
    - can utilize libunwind?
    - allow to instrument the traced app with a c-extenstion containing the necessary probes; either USDT or compiled with `-g` flag. ([like per4m](https://github.com/maartenbreddels/per4m/blob/master/per4m/pytrace.cpp))
       - this extension may also expose the raw GIL address to facilitate the sem_wait/pthread_cond_wait technique above

- other reporters
    - run textual in the browser
    - output raw data to console or to file
    - transform to trace event format like per4m https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview
    - compute stats like [gilstats.py](https://github.com/sumerc/gilstats.py)

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
