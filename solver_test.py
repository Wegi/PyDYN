#point system points/times solution was found
#times solution was found
#more packages to test
#one gotrough with optimized options one without

## npSolver+ glucose(INC) + satsolver.sh müssen im ausführenden Ordner liegen
## java auf VM installieren

import pydyn.api as api
import json
from multiprocessing import Process, Pipe
from collections import OrderedDict

# tuple is cases solved, cases unsolved
solveddata = {'./wbo': [0, 0],
              'minisat+': [0, 0],
              './clasp-2.1.3-x86_64-linux': [0, 0],
              './npSolver-pbo': [0, 0],
              'java -jar sat4j-pb.jar': [0, 0],
              './pb2sat+zchaff': [0, 0]}

pointsdata = {'./wbo': 0,
              'minisat+': 0,
              './clasp-2.1.3-x86_64-linux': 0,
              './npSolver-pbo': 0,
              'java -jar sat4j-pb.jar': 0,
              './pb2sat+zchaff': 0}

solverlist = OrderedDict([('./wbo', ['-file-format=opb']),
                          ('minisat+', []),
                          ('./clasp-2.1.3-x86_64-linux', []),
                          ('./npSolver-pbo', ['.']),
                          ('java -jar sat4j-pb.jar', []),
                          ('./pb2sat+zchaff', [])])

#unsolvable for minisat: adhocracy, 'deliverance' , 'tiddlywebplugins.tiddlyspace', 'sentry'
modulelist = ['lxml', 'distribute', 'boto', 'zc.buildout', 'pip',
              'simplejson', 'setuptools', 'requests', 'django', 'paste',
              'Jinja2', 'virtualenv', 'nose', 'PasteDeploy', 'psycopg2',
              'python-dateutil', 'sqlalchemy', 'coverage', 'pycrypto',
              'pastescript', 'flask', 'werkzeug', 'fabric', 'pymongo',
              'kombu', 'mysql-python', 'south', 'paramiko', 'zope.interface',
              'celery', 'anyjson', 'httplib2', 'pytz', 'greenlet', 'gunicorn',
              'six', 'pygments', 'meld3', 'graphite-web', 'webob', 'mako',
              'setuptools-git', 'supervisor', 'carbon', 'selenium', 'suds',
              'MarkupSafe', 'zc.recipe.egg', 'msgpack-python', 'redis',
              'minitage.paste', 'gevent', 'amqplib',
              'logilab-common', 'logilab-astng', 'versiontools', 'beautifulsoup',
              'pylint', 'eggtestinfo', 'termcolor',
              'pep8', 'unittest2', 'billiard', 'docutils', 'beaker',
              'mock', 'ssh', 'django-celery', 'sphinx', 'decorator',
              'django-debug-toolbar', 'twisted', 'ordereddict', 'raven',
              'vnc2flv', 'numpy', 'Formencode', 'py', 'markdown', 'pyyaml',
              'unidecode', 'django-appconf', 'oauth2', 'aspen', 'django_compressor',
              'amqp', 'pyrabbit', 'statsd', 'html5lib', 'adrest', 'ipython',
              'pyparsing', 'iso8601', 'django-extensions', 'pygeoip', 'chameleon',
              'python-daemon']

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
            self.pipe.send((result.installList, result.uninstallList, result.solvable))

    parent_conn, child_conn = Pipe()
    p = InterruptableProcess(child_conn)
    p.start()
    p.join(timeout_duration)
    if p.is_alive():
        p.terminate()
        pass
    if parent_conn.poll():
        return parent_conn.recv()
    else:
        return None


def deviationpoints(wboresult, solverresult):
    xfact = 100/(len(wboresult[0])+len(wboresult[1]))
    wboinstallNames = set([item[0] for item in wboresult[0]])
    wbounintsallNames = set([item[0] for item in wboresult[1]])
    solverintsallNames = set([item[0] for item in wboresult[0]])
    solverunintsallNames = set([item[0] for item in wboresult[1]])
    deviationcount = len(wboinstallNames.symmetric_difference(solverintsallNames))
    deviationcount += len(wbounintsallNames.symmetric_difference(solverunintsallNames))
    return (100 - (deviationcount*xfact))

if __name__ == '__main__':
    for module in modulelist:
        lastwbo = None
        pointfac = 0
        for solver, opts in solverlist.items():
            curpoints = 0
            print('processing: '+module+' with '+solver)
            problem = api.Problem(module, solverprog=solver, solverOptions=opts)
            res = timeout(problem.solve, timeout_duration=10)
            print('returning from'+module+' with '+solver)
            if res:
                if res[2]:  # solvable
                    solveddata[solver][0] += 1
                else:
                    solveddata[solver][1] += 1
                    curpoints -= 50
                if solver is './wbo':
                    curpoints += 100
                    lastwbo = (res[0], res[1])
                    pointsdata[solver] += curpoints
                else:
                    curpoints += deviationpoints(lastwbo, (res[0], res[1]))
                    pointsdata[solver] += curpoints
            else:
                solveddata[solver][1] += 1
                pointsdata[solver] += -50

    json.dump({'solved': solveddata, 'points': pointsdata}, open('solvertest_1_unoptimized.json', 'w'))
