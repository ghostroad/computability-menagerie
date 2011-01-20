import hotshot, hotshot.stats
from menagerie2 import *

def load():
    m = Menagerie()
    parser = MenagerieParser(m)
    parser.readFromFile("bn1g.txt")
    Deductions().apply(m)
    DotRenderer(m).render(showWeakOpenImplications=True, showStrongOpenImplications=False).to_string()

prof = hotshot.Profile("bigdb.prof")

prof.runcall(load)
