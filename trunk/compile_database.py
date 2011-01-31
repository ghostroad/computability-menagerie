from menagerie2 import *
import sys
database = sys.argv[1]
m = Menagerie()
MenagerieParser(m).readFromFile(database)
Deductions().apply(m)
print m.compile()
