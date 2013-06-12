import pydyn.api as api
from multiprocessing import Process, Pipe

def timeout(func, args=(), kwargs={}, timeout_duration=10):
    """This function will spawn a thread and run the given function
    using the args, kwargs and return the given default value if the
    timeout_duration is exceeded.
    """

    class InterruptableProcess(Process):

        def __init__(self, pipe):
            Process.__init__(self)
            self.pipe = pipe

        def run(self):
            result = func(*args, **kwargs)
            self.pipe.send(result)

    parent_conn, child_conn = Pipe()
    p = InterruptableProcess(child_conn)
    p.start()
    p.join(timeout_duration)
    if p.is_alive():
        p.terminate()
    if parent_conn.poll():
        return parent_conn.recv()
    else:
        return None

if __name__ == '__main__':
    problem = api.Problem('adhocracy', solverprog='minisat+', solverOptions=[])
    res = timeout(problem.solve, timeout_duration=5)
    if res:
        print(res)
    else:
        print('no result')
