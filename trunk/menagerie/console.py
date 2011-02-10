from core import *
import os, stat, sys, time
from optparse import OptionParser, OptionGroup
import pyparsing

VERSION = "0.1"
info = sys.stderr

consoleParser = OptionParser('Usage: %prog [options] database', version='%prog ' + VERSION)

consoleParser.set_defaults(open=(True,False),plain=False)
consoleParser.add_option('-c', '--classes', dest='class_string', metavar='CLASSES',
                  help='resrict to the subgraph containing the classes in the string CLASSES')
consoleParser.add_option('-p', '--plain', action='store_true', dest='plain',
                  help='do not use class properties to determine node style')
consoleParser.add_option('-w', '--weak', action='store_const', const=(True,False), dest='open',
                  help='display only the weakest open implications (default)')
consoleParser.add_option('-s', '--strong', action='store_const', const=(False,True), dest='open',
                  help='display only the strongest open implications')
consoleParser.add_option('-b', '--both', action='store_const', const=(True,True), dest='open',
                  help='display both the weakest and strongest open implications')
consoleParser.add_option('-n', '--neither', action='store_const', const=(False,False), dest='open',
                  help='display no open implications')
consoleParser.add_option('-j', '--justify', dest='justify', metavar='CLASS | "CLASS_1 CLASS_2"',
                  help='justify the properties of CLASS or the relationship between CLASS_1 and CLASS_2; do not output a .dot file')

webappParser = OptionParser('Usage: %prog database', version='%prog ' + VERSION)

def modificationTime(fileName):
    return time.localtime(os.stat(fileName)[stat.ST_MTIME])

def importOrCompileMenagerie(errorHandler, args):
    if len(args)>1: errorHandler.error('Too many arguments')
    if len(args)<1: errorHandler.error('No database file specified')

    dbFile = args[0]
    if not os.path.exists(dbFile): errorHandler.error("{0} not found".format(dbFile))
    
    dbModTime = modificationTime(dbFile)
    pyFile = os.path.splitext(os.path.basename(dbFile))[0]
    pyFilename = pyFile + ".py"
    if os.path.exists(pyFilename) and modificationTime(pyFilename) >= dbModTime:
        sys.path.append(os.getcwd())
        return __import__(pyFile).menagerie
    else:
        info.write("Compiling...")
        m = Menagerie()
        try:
            MenagerieParser(m).readFromFile(dbFile)
        except pyparsing.ParseException as e:
            compilationError("\nThere was an error parsing the database file:\n{0}".format(e))
        Deductions().apply(m)
        if m.errors:
            info.write("\nErrors found:\n")
            for error in m.errors:
                info.write(error.encode('utf-8') + "\n")
                compilationError('Aborting compilation.')
        open(pyFilename, "w").write(m.compile())
        info.write("Done.\n")
        return m

def compilationError(message):
    info.write(message)
    info.write("\n")
    sys.exit(1)

def webappMain():
    options, args = webappParser.parse_args()
    m = importOrCompileMenagerie(webappParser, args)
    app = configureApp(m)
    app.run(debug=True)

def configureApp(m):
    from menagerie.webapp import app
    from menagerie.webapp.apputils import Coloring
    app.config['menagerie'] = m
    app.config['propertiesMap'] = Coloring(m).buildPropertiesMap()
    app.config['gatewayPage'] = "http://www.math.wisc.edu/~jmiller/menagerie.html"
    return app

def consoleMain():
    options, args = consoleParser.parse_args()
    m = importOrCompileMenagerie(consoleParser, args)

    if options.justify:
        justify(m, options.justify.split(), consoleParser)
    else:
        renderGraph(m, options.open[0], options.open[1], options.plain, options.class_string, consoleParser)

def renderGraph(m, showWeak, showStrong, plain, classes, errorHandler):
    try:
        classes = classes and [m[clsName] for clsName in classes.split()] or []
    except ClassNotFoundError as e:
        errorHandler.error(str(e))
    g = DotCommandLineRenderer(m, classes, showWeak, showStrong, plain).render()
    print g.to_string()

def justify(m, classes, errorHandler):
    if len(classes) == 1:
        justifyOne(m, classes[0], errorHandler)
    elif len(classes) == 2:
        if classes[0] == classes[1]:
            justifyOne(m, classes[0], errorHandler)
        else:
            justifyTwo(m, classes[0], classes[1], errorHandler)
    else:
        errorHandler.error("Invalid justification request.")

def justifyTwo(m, classA, classB, errorHandler):
    try:
        A = m[classA]
        B = m[classB]
    except ClassNotFoundError as e:
        errorHandler.error(str(e))
    
    forwardImplication = A.implies(B) or A.doesNotImply(B) or UnknownImplication(A, B)
    backwardImplication = B.implies(A) or B.doesNotImply(A) or UnknownImplication(B, A)

    beginDocument()
    print LatexWriter().write(forwardImplication)
    print '\n\\bigskip\\hrule\\bigskip\n'
    print LatexWriter().write(backwardImplication)
    endDocument()

def justifyOne(m, clsName, errorHandler):
    try:
        cls = m[clsName]
    except ClassNotFoundError as e:
        errorHandler.error(e)

    beginDocument()
    for attr in CLASS_ATTRIBUTES:
        prop = getattr(cls, attr)
        print LatexWriter().write(prop)
        print '\n\\bigskip\\hrule\\bigskip\n'
    endDocument()

    

def beginDocument():
    print """\\documentclass{amsart}
\\usepackage[utf8]{inputenc}
\\makeatletter
\\newenvironment{fact}[1]
{
	\\setlength{\\parindent}{0cm}
	{\\tt #1}
	
	\\setlength{\\leftmargin}{1cm}
	\\advance\\linewidth -\\leftmargin
	\\advance\\@totalleftmargin\\leftmargin
	\\@setpar{{\\@@par}}
	\\parshape 1 \\@totalleftmargin \\linewidth
	\\ignorespaces
}
{\\par}
\\makeatother

\\begin{document}
"""

def endDocument():
    print "\\end{document}"
