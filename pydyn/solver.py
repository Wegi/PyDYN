import urllib.request
import urllib.error
import pydyn.patcher as  patcher
import re
import shutil
import tempfile
import os
import tarfile
import sys
import pickle
import subprocess
import json
import sqlite3
import time

from pkg_resources import Distribution
from pkg_resources import Requirement
from pkg_resources import parse_version
from pkg_resources import working_set

REP_URL = 'https://pypi.python.org/simple/'
REMWEIGHT = '-100'
NEWWEIGHT = '+20'
FAKEWEIGHT = '+9001'  ##fake metamodule
CACHE = dict()

class OPBTranslator:
    """An Class to transalte Module-Metadata to OPB and back"""

    def __init__(self, name, version=''):
        self.name = name.lower()
        self.version = version
        self.reqdict = dict()
        self.vardict = dict()

    def addDependency(self, name, version=''):
        self.name = name
        self.version = version

###############################################
####################### new method with meta.db

    def generateMetadata(self):
        """Generates a complete Dictionary of all (recursive) Dependencies of name.

        Returns a dictionary of the format {(name, version): [Requirement]}
        The translator makes some assumptions, i.e. all dependencys of "name" have to be fulfilled strictly. 
        """
        
        data = json.loads(open('meta.json', 'r').read())

        versionslist = versionsFromMeta(self.name, data)
        newver = newest(versionslist)
        self.version = newver
        reqs = list(dependenciesFor(self.name.lower(), self.version, data))
        self.reqdict.update({(self.name.lower(), self.version): reqs})
        todo = reqs
        strict = dict()
        for i in todo:
            strict.update({i.key: i})  ##Have to be fullfilled at all times
        
        for req in todo:
            vlist = versionsFromMeta(req.key, data)
            for version in vlist:
                if version in req:  ##only use if linktup fullfills requirement
                    templist = list(dependenciesFor(req.key, version, data))
                    for item in templist:
                        if item not in todo:
                            todo.append(item)

                    #update only if the requirement meets the strict requirements
                    if req.key in strict:
                        if version in strict[req.key]:
                            self.reqdict.update({(req.key, version): templist})
                    else:
                        self.reqdict.update({(req.key, version): templist})
#################################################
    


    def generateOPB(self, working_set=working_set, forCheck=False, checkOpts=('', '')):
        """Generate a opb Representation of a requirement-dict.

        The Requirement-dictionary gets parsed and a opb Instance of the
        Installation-Problem gets created. The resulting opb String
        should be parsable by all PBO-Solver, who comply to the
        DIMACS Format.

        forCheck has to be True only if yo use this method from checkFutureDependency() in the api.
        checkOpts is a tuple that holds name and version of the module to which you add dependencies.
        """

        retstr = ''
        minstring = 'min: '
        fakenames = set() ##dictionary for fakepackages
        conflicts = set()
        symtable = dict()
        symcounter = 1
        if not forCheck:
            for p in working_set:
                symtable.update({(p.key, p.version): 'x'+str(symcounter)})
                symcounter += 1
                minstring += REMWEIGHT+' '+symtable[(p.key, p.version)]+' '
        for key, reqlist in self.reqdict.items():
            if key not in symtable:
                symtable.update({key: 'x'+str(symcounter)})
                symcounter += 1
            minstring += NEWWEIGHT+' '+symtable[key]+' '
            if forCheck:
                for req in reqlist:
                    fakenames.add(req.key)
        if forCheck:
            for item in fakenames:
                symtable.update({(item.lower(), '0.0-fake'): 'x'+str(symcounter)})
                minstring += FAKEWEIGHT+' x'+str(symcounter)+' '
                symcounter += 1
        minstring += ';\n'
        retstr += minstring # minimization function
        retstr += '+1 '+symtable[(self.name.lower(), self.version)]+' >= 1;\n' # module you want to install
        if forCheck:
            retstr += '+1 '+symtable[(checkOpts[0].lower(), checkOpts[1])]+' >= 1;\n'

        for key, val in symtable.items():
            confstr = ''
            templist = []
            templist.append(val)
            for key2, val2 in symtable.items():
                if key[0] == key2[0] and key[1] != key2[1]:
                    templist.append(val2)
            fset = frozenset(templist)
            conflicts.add(fset)
        for item in conflicts:
            newset = set(item)
            for var in newset:
                confstr += '+1 '+var+' '
            confstr += '<= 1;\n'
        retstr += confstr  #conflicts

        # update reqdict with working_set
        if not forCheck:
            for p in working_set:
                self.reqdict.update({(p.key, p.version): p.requires()})
        for key, reqlist in self.reqdict.items():
            for req in reqlist:
                depstr = '-1 '+symtable[key]+' '
                switch = False
                for entry, sym in symtable.items():
                    if entry[0] == req.key and entry[1] in req:
                        depstr += '+1 '+sym+' '
                        switch = True
                if forCheck:
                    depstr += '+1 '+symtable[(req.key, '0.0-fake')]+' '
                depstr += '>= 0;\n'
                if switch: retstr += depstr # dependencies
        for key, val in symtable.items():
            self.vardict.update({val: key})
        return retstr

    def parseSolverOutput(self, output):
        """Parse the output of an opb-Solver.

        The output of the solver has to be in DIMACS format.
        The output of this method are two lists which indicate
        which modules are to be installed and which are not.
        """

        exp = re.search(r'^v .*$', output, flags=re.MULTILINE)
        solvablestr = re.search(r'^s.*', output, flags=re.MULTILINE)
        temp = solvablestr.group(0).split()
        solvable = False
        if temp[1] == 'OPTIMUM' and temp[2] == 'FOUND':
            solvable = True
        elif temp[1] == 'UNSATISFIABLE':
            solvable = False
        variables = exp.group(0).split()
        install = [self.vardict[var] for var in variables if var.startswith('x')]
        uninstall = [self.vardict[var[1:]] for var in variables if var.startswith('-')]
        return install, uninstall, solvable 

    def getFutureState(self, inst):
        """Give back a graph for drawing methods."""

        graph = dict()
        for i in inst:
            reqs = []
            for x in self.reqdict[i]:
                for j in inst:
                    if x.key == j[0]:
                        reqs.append(j)
                        break
            graph.update({i: reqs})
        return graph

if sys.version_info[0] == 3 and sys.version_info[1] == 2 and sys.version_info[2] < 3:
    urllib.request = patcher ##module bugged in 3.2.0 to 3.2.2

def versionsFromMeta(name, data):
    if name in data:
        for version in data[name].keys():
            yield version

def dependenciesFor(name, version, data):
    for item in data[name][version]:
        yield Requirement.parse(item)

def parseURL(name):
    """Provides a linklist for a module.

    name has to be the name of a module hosted on PyPi. 
    This function parses all links on PyPi for this module and returns
    a list of tuples (link to module as .tar.gz, version).
    """

    resp = urllib.request.urlopen(REP_URL+name+'/')
    data = resp.read()
    text = data.decode('utf-8')
    linkiter = re.findall(r"<a href=\"([\.\.|https?].*?packages.*/.*%s-(.*)\.tar\.gz.*?)\""%name, text, re.IGNORECASE)
    for link, version in linkiter:
        if link.startswith('http'):
            yield (link, version)
        else:
            yield (REP_URL+name+'/'+link, version)

def downloadPackage(link):
    """Downloads a module.

    Module gets saved as .tar.gz in /tmp and its path gets returned.
    The file has to be unlinked manually. (use os.unlink())
    """

    print('---- Beginning Download of '+link)
    temp = tempfile.NamedTemporaryFile(delete=False)
    try:
        with urllib.request.urlopen(link) as response, open(temp.name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except urllib.error.HTTPError:
        print("Downloadlink probably dead")
        temp.name = None
    print('#### finished download')
    return temp.name

def getDependencies(paths, name, version):
    """Parses Dependencies from setup.py of tarred module.

    paths is the path to the module as .tar.gz. name and version
    are the name and version of the module, that has to be parsed.
    Parses only if the install_requires String lists all the dependencies.
    Returns a List of [Requirement] objects.
    """

    try:
        tarball = tarfile.open(paths, mode='r')
    except tarfile.ReadError:
        print('Error: Not a tarfile, ignore it')
    else:
        try:
            setupfile = tarball.getmember(tarball.next().name+'/setup.py')
        except KeyError:
            print('Error: No setup.py in tarball')
        else:
            f = tarball.extractfile(setupfile)
            content = f.read().decode('utf-8')
            rawstring = re.findall(r'install_requires=\[(.*?)\]', content, flags=re.DOTALL)

            if rawstring:
                deplist = re.findall(r'"(.*?)"', rawstring[0])
                deplist.extend(re.findall(r"'(.*?)'", rawstring[0]))
            else:
                deplist = []
            reqlist = []
            for req in deplist:
                reqlist.append(Requirement.parse(req))
            f.close()
        return reqlist

def newest(linklist):
    """Returns the newest module in a list of versions."""

    newest_version = ''
    for version in linklist:
        if parse_version(version) > parse_version(newest_version):
            newest_version = version
    return newest_version

def installRecommendation(install, uninstall, working_set=working_set, tuples=False):
    """Human Readable advice on which modules have to be installed on
    current Working Set.
    """
    installList = []
    for i in install:
        is_in = False
        for p in working_set:
            if i[0] == p.key and i[1] == p.version:
                is_in = True
                break
        if not is_in: 
            if not tuples:
                print('~~ Install: '+i[0]+' version '+i[1])
            else:
                installList.append((i[0], i[1]))
    for u in uninstall:
        is_in = False
        for p in working_set:
            if u[0] == p.key and u[1] == p.version:
                is_in = True
                break
        if is_in: 
            if not tuples:
                print('~~ Uninstall: '+u[0]+' version '+u[1])
    return installList
                

def loadCache(path='pydyn.cache'):
    try:
        global CACHE 
        CACHE = pickle.load(open(path, 'rb'))
    except IOError:
        print('Warning: Could not load Cache')

def saveCache(path='pydyn.cache'):
    try:
        pickle.dump(CACHE, open(path, 'wb'))
        print('Dumping cache')
    except IOError:
        print('Warning: Could not save Cache')

def parseCheckOutput(install):
    """Parses the preparsed solver output with respect to fakevariables"""

    retstr = '### Keep the following dependencies:\n'
    inconStr = ''
    consistent = True
    for item in install:
        if item[1] != '0.0-fake':
            retstr += item[0]+' version '+item[1]+'\n'
        else: 
            consistent = False
            inconStr += item[0]+'\n'
    if not consistent:
        retstr += '### WARNING: The dependencies can only be kept consistent without the following packages:\n'
        retstr += inconStr
    return retstr

def callSolver(inputfile, solver='./wbo/wbo', options=[]):
    """Call a solver with an opb instance.

    Returns output in DIMACS format.
    """
    optionstr = ' '
    for i in options:
        optionstr += i+' '
    return subprocess.getoutput(solver+optionstr+inputfile)