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

class Solution:

    def __init__(self, name, installList, uninstallList, solvable, opb_translator):
        self.name = name
        self.installList = installList
        self.uninstallList = uninstallList
        self.solvable = solvable
        self.opb_translator = opb_translator


    def getInstallStrings(self):
        """Parses the output of installFor().

        Get a Human Readable String which gives Install / uninstall advice.
        """
        solver.installRecommendation(self.installList, self.uninstallList)

    def drawPNG(self):
        """Output a .png file with the dependency graph after parsed module would be installed.

        A module should have been parsed with installFor() before calling this function
        """
        graph = self.opb_translator.getFutureState(self.installList)
        depgraph.graphToPNG(graph)

    def drawSVG(self):
        """Output a .svg file with the dependency graph after parsed module would be installed.

        A module should have been parsed with installFor() before calling this function
        graphviz package has to be installed on UNIX Systems.
        """
        graph = self.opb_translator.getFutureState(self.installList)
        depgraph.graphToSVG(graph)

class Problem:

    def __init__(self, name, solverprog='./wbo/wbo', solverOptions=['-file-format=opb'], wset=None):
        """Set the parameter for the module which you want to install."""

        solver.loadCache()
        self.solverprog = solverprog
        self.solverOptions = solverOptions
        self.name = name
        if wset: self.wset = wset
        else: self.wset = pkg_resources.working_set

        self.opb_translator = solver.OPBTranslator(name)
        self.opb_translator.generateMetadata()
        
        solver.saveCache()

    def solve(self):
        """Solve the Instance. Creates an opb file and inputs it in the solver"""
        with open('pydyn.opb', 'w') as f:
            f.write(self.opb_translator.generateOPB(working_set=self.wset))
        output = solver.callSolver('pydyn.opb', solver=self.solverprog, options=self.solverOptions)
        installList, uninstallList, solvable = self.opb_translator.parseSolverOutput(output)
        return Solution(self.name, installList, uninstallList, solvable, self.opb_translator)

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

    def checkFutureDependency(self, depname):
        """Check if dependencies of module keep consistent after adding depname
        to the list of dependencies.
        """

        solver.loadCache()
        module = self.opb_translator.name
        version = self.opb_translator.version
        self.opb_translator.addDependency(depname)
        self.opb_translator.generateMetadata()

        with open('pydyn.opb', 'w') as f:
            f.write(self.opb_translator.generateOPB(forCheck=True, checkOpts=(module, version)))
        output = solver.callSolver('pydyn.opb', solver=self.solverprog, options=self.solverOptions)
        solver.saveCache()
        installList, uninstallList, solvable = self.opb_translator.parseSolverOutput(output)
        return Solution(self.name, installList, uninstallList, solvable)
        print(solver.parseCheckOutput(self.installList))