import os
from subprocess import Popen, PIPE


def find_binaries_by_symbols(pid: int, symbols):
    symbol_tables = {
        binary: read_symbols(binary)
        for binary in collect_binaries(pid)
    }
    result = {}
    for symbol in symbols:
        binaries_with_symbol = [
            binary
            for binary, symbols in symbol_tables.items()
            if b" " + symbol.encode() in symbols  # plain substring check
        ]
        if binaries_with_symbol:
            binaries_with_symbol.sort(key=lambda binary: 0 if 'libc' in binary else 1)  # give higher priority to libc
            result[symbol] = binaries_with_symbol[0] if binaries_with_symbol else None 
    return result


def collect_binaries(pid: int):
    binaries = {os.path.realpath(f'/proc/{pid}/exe')}  #  the python binary itself

    with open(f'/proc/{pid}/maps') as fin:
        for line in fin:
            parts = line.split()
            if len(parts) >= 6:
                binary = parts[5]
                if binary.endswith('.so') or '.so.' in binary:
                    binaries.add(binary)  # found shared library
    
    return binaries


def read_symbols(binary):
    return (
        read_stdout(["/usr/bin/nm", "--defined-only", binary]) +
        b'\n' +
        read_stdout(["/usr/bin/nm", "--defined-only", "--dynamic", binary])
    )


def read_stdout(cmd):
    with Popen(cmd, stdout=PIPE, stderr=PIPE) as proc:
        out, err = proc.communicate()
        return out

