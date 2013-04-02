"""API for the PyDYN Application.

Please use this module instead of calling the other modules directly.
This way you'll have safe calls and won't have to deal with changing
requirements/names/formats.
All methods asume you have set the solver and working set accordingly to your
wishes / configuration.
Use the installationFor() Method firsthand.
"""

import solver
import depgraph

from pkg_resources import WorkingSet

_solver = 'minisat+'
_working_set = None
_installList = []
_uninstallList = []

def installFor(name):
    """Set the parameter for the module which you want to install.

    Use this function (once) before calling drawXY() / getInstallLists() / getInstallStrings() / etc.
    """
    solver.loadCache()
    with open('pydyn.opb', 'w') as f:
        f.write(solver.generateOPB(name, working_set=_working_set if _working_set 
            else solver.generateOPB.__defaults__[0]))
    solver.saveCache()
    global _installList
    global _uninstallList
    _installList, _uninstallList = solver.parseSolverOutput(solver._callSolver('pydyn.opb', solver=_solver))

def loadCache(path):
    """Load another cache file."""
    solver.loadCache(path)

def saveCache(path):
    """Save the cache to another file than pydyn.cache"""
    solver.saveCache(path)

def getInstallLists(name):
    """Get two lists of which modules to install or uninstall.

    Returns two lists install, uninstall. 
    The Content of the Lists is a tuple with (name, version).
    """
    return _installList, _uninstallList

def setSolver(solver):
    """Set the opb-solver to use. (standard is minisat+)

    The Solver has to accept the opb Format and generate 
    his output according to DIMACS regulations as of 2013.
    """
    _solver = solver

def setWorkingSet(paths):
    """Set the Working Set to paths.

    The Working Set is the active module path where your modules for a 
    project reside.
    paths has to be a list of paths.
    """
    _working_set = WorkingSet(paths)

def setDefaultWorkingSet():
    """Set the Working Set back to default (sys.path).

    The Working Set is the active module path where your modules for a 
    project reside.
    """
    _working_set = None

def getInstallStrings():
    """Parses the output of installFor().

    Get a Human Readable String which gives Install / uninstall advice.
    """
    solver.installRecommendation(_installList, _uninstallList)

def drawPNG():
    """Output a .png file with the dependency graph after parsed module would be installed.

    A module should have been parsed with installFor() before calling this function
    """
    graph = solver.getFutureState(_installList)
    depgraph.graphToPNG(graph)

def drawSVG():
    """Output a .svg file with the dependency graph after parsed module would be installed.

    A module should have been parsed with installFor() before calling this function
    graphviz package has to be installed on UNIX Systems.
    """
    graph = solver.getFutureState(_installList)
    depgraph.graphToSVG(graph)    