import unittest
from menagerie_core import *


class TestMenagerieWithLargeDB(unittest.TestCase):

    def test_loads_a_large_db(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.readFromFile("bn1g.txt")
        Deductions().apply(m)
        DotRenderer(m).render().write("whatever.dot")

if __name__ == "__main__":
    unittest.main()
        
