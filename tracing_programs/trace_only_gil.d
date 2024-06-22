uretprobe:/home/gukov/.pyenv/versions/3.10.14/lib/libpython3.10.so.1.0:take_gil*
{
    printf(
        "%d|take|%s\n",
        tid,
        strftime("%H:%M:%S.%f", nsecs)
    )
}

uprobe:/home/gukov/.pyenv/versions/3.10.14/lib/libpython3.10.so.1.0:drop_gil*
{
    printf(
        "%d|drop|%s\n",
        tid,
        strftime("%H:%M:%S.%f", nsecs)
    )
}
