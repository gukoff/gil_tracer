usdt:/home/gukov/.pyenv/versions/3.10.14/lib/libpython3.10.so.1.0:python:line
{
    @last_filename[tid] = str(arg0);
    @last_function[tid] = str(arg1);
    @last_line_number[tid] = arg2;
}

uretprobe:/home/gukov/.pyenv/versions/3.10.14/lib/libpython3.10.so.1.0:take_gil*
{
    printf(
        "%d|take|%s|%s|%s|%d\n",
        tid,
        strftime("%H:%M:%S.%f", nsecs),
        @last_filename[tid],
        @last_function[tid],
        @last_line_number[tid])
}

uprobe:/home/gukov/.pyenv/versions/3.10.14/lib/libpython3.10.so.1.0:drop_gil*
{
    printf(
        "%d|drop|%s|%s|%s|%d\n",
        tid,
        strftime("%H:%M:%S.%f", nsecs),
        @last_filename[tid],
        @last_function[tid],
        @last_line_number[tid])
}
