import hotshot, hotshot.stats
from menagerie2 import *

def load():
    m = Menagerie()
    parser = MenagerieParser(m)
    parser.readFromFile("bn1g.txt")
    Deductions().apply(m)

prof = hotshot.Profile("bigdb.prof")

prof.runcall(load)
