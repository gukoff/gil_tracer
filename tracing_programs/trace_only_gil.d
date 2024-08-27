uretprobe:*:take_gil*
{
    printf(
        "%d|take|%s\n",
        tid,
        strftime("%H:%M:%S.%f", nsecs)
    )
}

uprobe:*:drop_gil*
{
    printf(
        "%d|drop|%s\n",
        tid,
        strftime("%H:%M:%S.%f", nsecs)
    )
}
