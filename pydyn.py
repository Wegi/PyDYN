"""API for the PyDYN Application.

Please use this module instead of calling the other modules directly.
This way you'll have safe calls and won't have to deal with changing
requirements/names/formats.
All methods asume you have set the solver and working set accordingly to your
wishes / configuration.
"""

import solver
import depgraph

from pkg_resources import WorkingSet

_solver = 'minisat+'
_working_set = None

solver.loadCache()

def loadCache(path):
    """Load another cache file."""
    solver.loadCache(path)

def saveCache(path):
    """Save the cache to another file than pydyn.cache"""
    solver.saveCache(path)

def getInstallLists(name):
    """Get two lists of which modules to install or uninstall.

    Returns two lists install, uninstall. 
    The Content of the Lists ist a tuple with (name, version).
    """
    with open('pydyn.opb', 'w') as f:
        f.write(solver.generateOPB(name, working_set=_working_set if _working_set 
            else solver.generateOPB.__defaults__[0]))
    solver.saveCache()
    return solver.parseSolverOutput(solver._callSolver('pydyn.opb', solver=_solver))

def setSolver(solver):
    """Set the opb-solver to use. (standard is minisat+)

    The Solver has to accept the opb Format and generate 
    his output according to DIMACS regulations as of 2013.
    """
    _solver = solver

def setWorkingSet(paths):
    """Set the Working Set to paths.

    paths has to be a list of paths.
    """
    _working_set = WorkingSet(paths)

def setDefaultWorkingSet():
    """Set the Working Set back to default."""
    _working_set = None

def getInstallStrings(install, uninstall):
    """Parses the output of getInstallLists.

    Get a Human Readable String which gives Install / uninstall advice.
    """
    solver.installRecommendation(install, uninstall)

def drawPNG(name):
    """Output a .png file with the dependency graph after name would be installed."""
    i, u = getInstallLists(name)
    graph = solver.getFutureState(i)
    depgraph.graphToPNG(graph)