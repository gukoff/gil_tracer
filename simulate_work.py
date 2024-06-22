import threading

def some_func1(): pass
def some_func2(): pass

def do_nothing():
    while True:
        some_func1()
        some_func2()


def main():
    t1 = threading.Thread(target=do_nothing)
    t2 = threading.Thread(target=do_nothing)

    t1.start()
    t2.start()

    t1.join()
    t2.join()


if __name__ =="__main__":
    main()
