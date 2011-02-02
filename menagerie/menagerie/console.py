from core import *
import os, stat, sys, time

def modificationTime(fileName):
    return time.localtime(os.stat(fileName)[stat.ST_MTIME])

def formatTime(t):
    return time.strftime("%m/%d/%Y %I:%M:%S %p", t)

def main():
    dbFile = sys.argv[1]
    if not os.path.exists(dbFile): 
        print "{0} not found.".format(dbFile)
        return
    
    dbModTime = modificationTime(dbFile)
    print "Processing database file {0}, last modified at {1}.".format(dbFile, formatTime(dbModTime))

    pyFile = os.path.splitext(os.path.basename(dbFile))[0]
    pyFilename = pyFile + ".py"
    if os.path.exists(pyFilename):
        pyFileModTime = modificationTime(pyFilename)
        print "{0} found, last updated at {1}.".format(pyFilename, formatTime(pyFileModTime))
        if pyFileModTime < dbModTime:
            print "Out of date. Recompiling..."
            m = Menagerie()
            MenagerieParser(m).readFromFile(dbFile)
            Deductions().apply(m)
            open(pyFilename, "w").write(m.compile())
            print "Done."
        else:
            m = __import__(pyFile).menagerie
    else:
        print "No compiled file found. Compiling..."
        m = Menagerie()
        MenagerieParser(m).readFromFile(dbFile)
        Deductions().apply(m)
        open(pyFilename, "w").write(m.compile())
        print "Done."
