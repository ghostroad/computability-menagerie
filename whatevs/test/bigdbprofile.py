import hotshot, hotshot.stats
from menagerie_core import *

def load():
    m = Menagerie()
    parser = MenagerieParser(m)
    parser.readFromFile("bn1g.txt")
    Deductions().apply(m)
    DotRenderer(m).render(showOpenImplications=True).to_string()

prof = hotshot.Profile("bigdb.prof")

prof.runcall(load)
