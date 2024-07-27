import threading
from sys import argv


def some_func1():
    pass


def some_func2():
    pass


def do_nothing():
    while True:
        some_func1()
        some_func2()


def main():
    worker_count = 2 if len(argv) < 2 else int(argv[1])

    workers = [
        threading.Thread(target=do_nothing, daemon=True) for _ in range(worker_count)
    ]
    for w in workers:
        w.start()

    for w in workers:
        w.join()


if __name__ == "__main__":
    main()
