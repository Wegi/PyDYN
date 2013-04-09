"""API for the PyDYN Application.

Please use this module instead of calling the other modules directly.
This way you'll have safe calls and won't have to deal with changing
requirements/names/formats.
All methods asume you have set the solver and working set accordingly to your
wishes / configuration.
Create a DepInstance Object first if you want to work with dependencys and not just check it.
"""

import solver
import depgraph
import pkg_resources

class DepInstance:

    def __init__(self, name, solverprog='./wbo/wbo', solverOptions=['-file-format=opb'], wset=None):
        """Set the parameter for the module which you want to install."""

        solver.loadCache()
        self.solverprog = solverprog
        self.solverOptions = solverOptions
        if wset: self.wset = wset
        else: self.wset = pkg_resources.working_set

        reqdict, version = solver.generateMetadata(name)
        with open('pydyn.opb', 'w') as f:
            f.write(solver.generateOPB(reqdict, name, version, working_set=self.wset))
        solver.saveCache() 
        self.installList, self.uninstallList, self.solvable = \
        solver.parseSolverOutput(solver._callSolver('pydyn.opb', solver=self.solverprog, options=self.solverOptions))

    def getInstallLists(self):
        """Get two lists of which modules to install or uninstall.

        Returns two lists install, uninstall. 
        The Content of the Lists is a tuple with (name, version).
        """
        return self.installList, self.uninstallList

    def setSolver(self, solverprog, solverOptions=[]):
        """Set the opb-solver to use. (standard is minisat+)

        The Solver has to accept the opb Format and generate 
        his output according to DIMACS regulations as of 2013.
        """

        self.solverprog = solverprog
        self.solverOptions = solverOptions

    def setWorkingSet(self, paths):
        """Set the Working Set to paths.

        The Working Set is the active module path where your modules for a 
        project reside.
        paths has to be a list of paths.
        """
        self.wset = pkg_resources.WorkingSet(paths)

    def setDefaultWorkingSet(self):
        """Set the Working Set back to default (sys.path).

        The Working Set is the active module path where your modules for a 
        project reside.
        """
        self.wset = pkg_resources.working_set

    def getInstallStrings(self):
        """Parses the output of installFor().

        Get a Human Readable String which gives Install / uninstall advice.
        """
        solver.installRecommendation(self.installList, self.uninstallList)

    def drawPNG(self):
        """Output a .png file with the dependency graph after parsed module would be installed.

        A module should have been parsed with installFor() before calling this function
        """
        graph = solver.getFutureState(self.installList)
        depgraph.graphToPNG(graph)

    def drawSVG(self):
        """Output a .svg file with the dependency graph after parsed module would be installed.

        A module should have been parsed with installFor() before calling this function
        graphviz package has to be installed on UNIX Systems.
        """
        graph = solver.getFutureState(self.installList)
        depgraph.graphToSVG(graph)

    def isSolvable(self):
        """Returns wether the current instance is satisfiable or not. (Run InstallFor() beforehand)"""

        return self.solvable 

def checkFutureDependency(module, depname):
    """Check if dependencies of module keep consistent after adding depname
    to the list of dependencies.
    """

    solver.loadCache()
    reqdict, version = solver.generateMetadata(module)
    reqdict2, version2 = solver.generateMetadata(depname)
    reqdict.update(reqdict2)
    with open('pydyn.opb', 'w') as f:
        f.write(solver.generateOPB(reqdict, module, version, forCheck=True, checkOpts=(depname, version2)))
    output = solver._callSolver('pydyn.opb', solver=_solver)
    solver.saveCache()
    install, uninstall, solvable = solver.parseSolverOutput(output)
    print(solver.parseCheckOutput(install, uninstall))