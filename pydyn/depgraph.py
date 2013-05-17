import pkg_resources
import os.path
import argparse

from subprocess import check_call

def getGraph(paths=None):
    """Gives you a Dictionary of all the Dependencys.

    The key is the name of the module wich has the dependency (could be 0
    dependencies) and the value is a List of names of Distributions the key depends on.

    If the paths argument is None its uses the default path.
    paths must be iterable.
    """

    wset = pkg_resources.working_set
    if paths:
        wset = pkg_resources.WorkingSet(paths)
    versions = dict()
    for p in wset:
        versions.update({p.key: p.version})
    graph = dict([((p.key, p.version), [(n.key, versions[n.key]) for n in p.requires()]) for p in wset])
    return graph

def graphToDot(graph, output="output.dot", show_disconnected=True):
    """Ouputs the graph in the dot format.

    The format of graph has to be like the one getGraph() returns.
    output is the output-file.
    if show_disconnected is True it shows Distributions without dependencies as well.
    """
    ##TODO Optimize layout
    wset = pkg_resources.working_set
    with open(output, 'w') as f:
        f.write('digraph DependencyGraph {\n')
        for dist, deplist in graph.items():
            if show_disconnected and not deplist:
                f.write('"'+dist[0]+'-'+dist[1]+'"\n')
            for d in deplist:
                f.write('"'+dist[0]+'-'+dist[1]+'" -> "'+d[0]+'-'+d[1]+'"\n')
        f.write('}')

def graphToPNG(graph, output="output.png", show_disconnected=True):
    """Output a graph as PNG.

    Only works on UNIX-Systems with the graphviz-tool installed.
    This method will create/overwrite a .dot file too.
    The format of graph has to be like the one getGraph() returns.
    output is the output-file.
    if show_disconnected is True it shows Distributions without dependencies as well.
    """

    dotout = os.path.splitext(output)[0]+'.dot'
    graphToDot(graph, dotout, show_disconnected)
    try:
        check_call(['dot', '-Tpng', dotout, '-o', output])
    except CalledProcessError:
        print('Error: An error ocurred during conversion to PNG. Make sure you have graphviz installed')

def graphToSVG(graph, output="output.svg", show_disconnected=True):
    """Output a graph as PNG.

    Only works on UNIX-Systems with the graphviz-tool installed.
    This method will create/overwrite a .dot file too.
    The format of graph has to be like the one getGraph() returns.
    output is the output-file.
    if show_disconnected is True it shows Distributions without dependencies as well.
    """
    
    dotout = os.path.splitext(output)[0]+'.dot'
    graphToDot(graph, dotout, show_disconnected)
    try:
        check_call(['dot', '-Tsvg', dotout, '-o', output])
    except CalledProcessError:
        print('Error: An error ocurred during conversion to PNG. Make sure you have graphviz installed')    

def graphToTerminal(graph, show_disconnected=True):
    """Output a graph as a Text Representation on the Terminal.

    The format of graph has to be like the one getGraph() returns.
    output is the output-file.
    if show_disconnected is True it shows Distributions without dependencies as well.
    """

    for dist, deplist in graph.items():
        if show_disconnected and not deplist:
            print('"'+dist+'"')
        for d in deplist:
            print('"'+dist+'" -> "'+d+'"')

if __name__ == "__main__":
    # Ugly Ugly Function, i'm sorry
    parser = argparse.ArgumentParser(description="Create a .dot or .PNG representation of Distributions.")
    parser.add_argument('--path', '-p', action='append', 
        help='Custom path for Distributions, can be used multiple times')
    parser.add_argument('--png', action='store_true',
        help='Use if output should be .png. Works only on UNIX Systems which have the graphviz-tool installed')
    parser.add_argument('--output', '-o', action='store',
        help='Specify Output-File (.dot or .png if --png used)')
    parser.add_argument('--connected', '-c', action='store_false',
        help='If used only Distributions with Dependencies will be shown')
    parser.add_argument('--text', '-t', action='store_true',
        help='Use this parameter if a terminal-output of the Distribution should be given')
    args = vars(parser.parse_args())
    if args['png']:
        graphToPNG(getGraph(paths=args['path'] if args['path'] else getGraph.__defaults__[0]), 
            output=args['output'] if args['output'] else graphToPNG.__defaults__[0], 
            show_disconnected=args['connected'])
    else:
        graphToDot(getGraph(paths=args['path'] if args['path'] else getGraph.__defaults__[0]), 
            output=args['output'] if args['output'] else graphToDot.__defaults__[0], 
            show_disconnected=args['connected'])
    if args['text']:
        graphToTerminal(getGraph(paths=args['path'] if args['path'] else getGraph.__defaults__[0]),
            show_disconnected=args['connected'])