import pydyn.api as api

def timeout(func, args=(), kwargs={}, timeout_duration=10, default=None):
    """This function will spawn a thread and run the given function
    using the args, kwargs and return the given default value if the
    timeout_duration is exceeded.
    """

    import threading
    import sys


    class InterruptableThread(threading.Thread):

        def __init__(self):
            threading.Thread.__init__(self)
            self.result = default

        def run(self):
            self.result = func(*args, **kwargs)
    it = InterruptableThread()
    it.start()
    it.join(timeout_duration)
    if it.isAlive():
        return it.result
    else:
        return it.result

if __name__ == '__main__':
    problem = api.Problem('adhocracy', solverprog='minisat+', solverOptions=[])
    res = timeout(problem.solve, timeout_duration=5)
    print('timed out ')
