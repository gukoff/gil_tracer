from psutil import Process
from subprocess import Popen, PIPE


def find_binaries_by_symbols(pid: int, symbols):
    """
    For each symbol, find the binaries (shared libraries and excutables)
    mapped by the given process that expose this symbol.

    Multiple binaries can expose the same symbol, and we can't tell which one is actually used;
    this function currently just tries to guess. This is not necessary, ideally we should set
    the probes in all binaries that export the desired symbol.
    """
    symbol_tables = {binary: read_symbols(binary) for binary in collect_binaries(pid)}
    result = {}
    for symbol in symbols:
        binaries_with_symbol = [
            binary
            for binary, symbols in symbol_tables.items()
            # This filter is pretty dumb. It seems to do the job but surely will miss some edge cases.
            # We only check if the binary has a symbol that starts with the desired symbol because some symbols in "nm" output contain @-suffixes.
            if b" " + symbol.encode() in symbols
        ]
        if binaries_with_symbol:
            binaries_with_symbol.sort(
                key=lambda binary: 0 if "libc." in binary else 1
            )  # give higher priority to be chosen to libc
            result[symbol] = binaries_with_symbol[0] if binaries_with_symbol else None
    return result


def collect_binaries(pid: int):
    p = Process(pid=pid)
    binaries = {
        p.exe(),  #  the python binary itself may contain symbols
    }

    for mapped_file in p.memory_maps():
        candidate = mapped_file.path
        if candidate.endswith(".so") or ".so." in candidate:
            binaries.add(candidate)  # found shared library

    return binaries


def read_symbols(binary):
    return (
        read_stdout(["/usr/bin/nm", "--defined-only", binary])
        + b"\n"
        + read_stdout(["/usr/bin/nm", "--defined-only", "--dynamic", binary])
    )


def read_stdout(cmd):
    with Popen(cmd, stdout=PIPE, stderr=PIPE) as proc:
        out, err = proc.communicate()
        return out
