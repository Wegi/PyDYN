##
## TODO build in caching

import urllib.request
import urllib.error
import patcher
import re
import shutil
import tempfile
import os
import tarfile
import sys

from pkg_resources import Distribution
from pkg_resources import Requirement
from pkg_resources import parse_version

REP_URL = 'https://pypi.python.org/simple/'

def parseURL(name):
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
    #TODO are zip packages legal?

def downloadPackage(link):
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
    #Parse the files given in paths and extract their EGG-INFO
    #return dictionary with (name, version) -> [Requirement]

    tarball = tarfile.open(paths, mode='r')
    depdict = dict()
    try:
        setupfile = tarball.getmember(tarball.next().name+'/setup.py')
    except KeyError:
        print('could not open .tar.gz-tempfile')
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
    
    os.unlink(paths) ## Cleanup, have to do this after metadata
    return depdict

def newest(linklist):
    newest_version = linklist[0]
    for link, version in linklist:
        if parse_version(version) > parse_version(newest_version[1]):
            newest_version = (link, version)
    return newest_version

def generateMetadata(name):
    linklist = parseURL(name)
    newver = newest(linklist)
    temp = downloadPackage(newver[0])
    if temp:
        reqdict = getDependencies(temp, name.lower(), newver[1])
        todo = reqdict[(name.lower(), newver[1])][:]
    else:
        reqdict = dict()
        todo = []
    for req in todo:
        llist = parseURL(req.key)
        for linktup in llist:
            if linktup[1] in req:
                ntemp = downloadPackage(linktup[0])
                if ntemp:
                    tempdict = getDependencies(ntemp, req.key, linktup[1])
                    todo.extend(tempdict[(req.key, linktup[1])])
                else:
                    tempdict = dict()
                reqdict.update(tempdict)       
    print(reqdict)


if __name__ == '__main__':
    if sys.version_info[0] == 3 and sys.version_info[1] == 2 and sys.version_info[2] < 3:
        urllib.request = patcher ##module bugged in 3.2.0 to 3.2.2
    generateMetadata('adhocracy')