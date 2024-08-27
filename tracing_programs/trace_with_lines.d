usdt:*:python:line
{
    @last_filename[tid] = str(arg0);
    @last_function[tid] = str(arg1);
    @last_line_number[tid] = arg2;
}

uretprobe:*:take_gil*
{
    printf(
        "%d|take|%s|%s|%s|%d\n",
        tid,
        strftime("%H:%M:%S.%f", nsecs),
        @last_filename[tid],
        @last_function[tid],
        @last_line_number[tid])
}

uprobe:*:drop_gil*
{
    printf(
        "%d|drop|%s|%s|%s|%d\n",
        tid,
        strftime("%H:%M:%S.%f", nsecs),
        @last_filename[tid],
        @last_function[tid],
        @last_line_number[tid])
}
