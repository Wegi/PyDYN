import urllib.request
import urllib.error
import patcher
import re
import shutil
import tempfile
import os
import tarfile
import sys
import pickle
import subprocess

from pkg_resources import Distribution
from pkg_resources import Requirement
from pkg_resources import parse_version
from pkg_resources import working_set

REP_URL = 'https://pypi.python.org/simple/'
REMWEIGHT = '-100'
NEWWEIGHT = '+20'
_VARDICT = dict()
CACHE = dict()
_REQ = dict()

if sys.version_info[0] == 3 and sys.version_info[1] == 2 and sys.version_info[2] < 3:
    urllib.request = patcher ##module bugged in 3.2.0 to 3.2.2

def parseURL(name):
    """Provides a linklist for a module.

    name has to be the name of a module hosted on PyPi. 
    This function parses all links on PyPi for this module and returns
    a list of tuples (link to module as .tar.gz, version).
    """

    resp = urllib.request.urlopen(REP_URL+name+'/')
    data = resp.read()
    text = data.decode('utf-8')
    linkiter = re.findall(r"<a href=\"([\.\.|https?].*-{1}(.*?)\.tar\.gz.*?)\"", text)
    linklist = []
    for link, version in linkiter:
        if link.startswith('http'):
            linklist.append((link, version))
        else:
            linklist.append((REP_URL+name+'/'+link, version))
    return linklist
    #TODO zip packages

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
    Returns a dictionary of the format {(name, version): [Requirement]}
    """

    tarball = tarfile.open(paths, mode='r')
    depdict = dict()
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
        depdict = {(name.lower(), version): reqlist}
        f.close()
    return depdict

def newest(linklist):
    """Returns the newest module in a linklist."""

    newest_version = linklist[0]
    for link, version in linklist:
        if parse_version(version) > parse_version(newest_version[1]):
            newest_version = (link, version)
    return newest_version

def generateMetadata(name):
    """Generates a complete Dictionary of all (recursive) Dependencies of name.

    Returns a dictionary of the format {(name, version): [Requirement]}
    """

    linklist = parseURL(name)
    newver = newest(linklist)
    temp = downloadPackage(newver[0])
    if temp:
        reqdict = getDependencies(temp, name.lower(), newver[1])
        todo = reqdict[(name.lower(), newver[1])][:]
        os.unlink(temp) ## Cleanup
    else:
        reqdict = dict()
        todo = []
    for req in todo:
        llist = parseURL(req.key)
        for linktup in llist:
            if linktup[1] in req and (req.key, linktup[1]) not in CACHE and \
            (req.key, linktup[1]) not in reqdict:
                print('---- Cache miss '+req.key+'-'+linktup[1])
                ntemp = downloadPackage(linktup[0])
                if ntemp:
                    tempdict = getDependencies(ntemp, req.key, linktup[1])
                    if req not in todo and (req.key, linktup[1]) not in reqdict:
                        todo.extend(tempdict[(req.key, linktup[1])])
                    os.unlink(ntemp) ## Cleanup
                else:
                    tempdict = dict()
                reqdict.update(tempdict)
            elif linktup[1] in req and (req.key, linktup[1]) in CACHE and \
            (req.key, linktup[1]) not in reqdict:
                print('++++ Cache hit '+req.key+'-'+linktup[1])
                if req not in todo and (req.key, linktup[1]) not in reqdict:
                        todo.extend(CACHE[(req.key, linktup[1])])
                reqdict.update({(req.key, linktup[1]): CACHE[(req.key, linktup[1])]})
    CACHE.update(reqdict)
    return reqdict, newver[1]

def generateOPB(name, working_set=working_set):
    """Generate a opb Representation of a requirement-dict.

    The Requirement-dictionary gets parsed and a opb Instance of the
    Installation-Problem gets created. The resulting opb String
    should be parsable by all PBO-Solver, who comply to the
    DIRACS Format.
    """

    retstr = ''
    minstring = 'min: '
    reqdict, version = generateMetadata(name)
    conflicts = set()
    symtable = dict()
    symcounter = 1
    for p in working_set:
        symtable.update({(p.key, p.version): 'x'+str(symcounter)})
        symcounter += 1
        minstring += REMWEIGHT+' '+symtable[(p.key, p.version)]+' '
    for key, reqlist in reqdict.items():
        if key not in symtable:
            symtable.update({key: 'x'+str(symcounter)})
            symcounter += 1
        minstring += NEWWEIGHT+' '+symtable[key]+' '
    minstring += ';\n'
    retstr += minstring # minimization function
    retstr += '+1 '+symtable[(name.lower(), version)]+' >= 1;\n' # module you want to install

    for key, val in symtable.items():
        for key2, val2 in symtable.items():
            if key[0] == key2[0] and key[1] != key2[1]:
                conflicts.add(frozenset([symtable[key], symtable[key2]]))
    for fset in conflicts:
        cset = set(fset)
        retstr += '+1 '+cset.pop()+' +1 '+cset.pop()+' <= 1;\n' # conflicts

    # update reqdict with working_set
    for p in working_set:
        reqdict.update({(p.key, p.version): p.requires()})
    global _REQ
    _REQ = reqdict
    for key, reqlist in reqdict.items():
        for req in reqlist:
            depstr = '-1 '+symtable[key]+' '
            switch = False
            for entry, sym in symtable.items():
                if entry[0] == req.key and entry[1] in req:
                    depstr += '+1 '+sym+' '
                    switch = True
            depstr += '>= 0;\n'
            if switch: retstr += depstr # dependencies
    for key, val in symtable.items():
        _VARDICT.update({val: key})
    return retstr

def parseSolverOutput(output):
    """Parse the output of a opb.Solver.

    The output of the solve has to be in DIMACS format.
    The output of this method are two lists which indicate
    which modules are to be installed and which are not.
    """

    exp = re.search(r'^v .*$', output, flags=re.MULTILINE)
    solvablestr = re.search(r'^s.*', output, flags=re.MULTILINE)
    temp = solvablestr.split()
    solvable = False
    if temp[1] == 'OPTIMUM' and temp[2] == 'FOUND':
        solvable = True
    elif temp[1] == 'UNSATISFIABLE':
        solvable = False
    variables = exp.group(0).split()
    install = [_VARDICT[var] for var in variables if var.startswith('x')]
    uninstall = [_VARDICT[var[1:]] for var in variables if var.startswith('-')]
    return install, uninstall, solvable 

def installRecommendation(install, uninstall, working_set=working_set):
    """Human Readable advice on which modules have to be installed on
    current Working Set.
    """

    for i in install:
        is_in = False
        for p in working_set:
            if i[0] == p.key and i[1] == p.version:
                is_in = True
                break
        if not is_in: print('~~ Install: '+i[0]+' version '+i[1])
    for u in uninstall:
        is_in = False
        for p in working_set:
            if u[0] == p.key and u[1] == p.version:
                is_in = True
                break
        if is_in: print('~~ Uninstall: '+u[0]+' version '+u[1])

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

def getFutureState(inst):
    """Give back a graph for drawing methods.

    Don't clear the global _REQ after the corresponding opb generation.
    """
    graph = dict()
    for i in inst:
        reqs = []
        for x in _REQ[i]:
            for j in inst:
                if x.key == j[0]:
                    reqs.append(j)
                    break
        graph.update({i: reqs})
    return graph

###Intern Methods, do not use from ouside modules
def _callSolver(inputfile, solver='minisat+'):
    """Call a solver with an opb instance.

    Returns output in DIMACS format.
    """

    return subprocess.check_output([solver, inputfile]).decode('utf-8')

if __name__ == '__main__':
    loadCache()
    with open('pydyn.opb', 'w') as f:
        f.write(generateOPB(sys.argv[1]))
    inst, unin = parseSolverOutput(_callSolver('pydyn.opb', solver='minisat+'))
    installRecommendation(inst, unin)
    saveCache()