import threading
import argparse
from time import sleep


def some_func1():
    pass


def some_func2():
    pass


def do_nothing():
    while True:
        some_func1()
        some_func2()


def do_sleep():
    while True:
        sleep(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sleepers", type=int, default=1, help="Number of sleeper threads")
    parser.add_argument("--workers", type=int, default=2, help="Number of worker threads")
    args = parser.parse_args()

    sleeper_count = args.sleepers
    worker_count = args.workers

    print(f"Starting {sleeper_count} sleepers and {worker_count} workers")

    threads = [
        threading.Thread(target=do_nothing, daemon=True) for _ in range(worker_count)
    ] + [
        threading.Thread(target=do_sleep, daemon=True) for _ in range(sleeper_count)
    ]

    for w in threads:
        w.start()

    for w in threads:
        w.join()


if __name__ == "__main__":
    main()
