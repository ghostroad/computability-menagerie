import unittest
from menagerie2 import *


class TestMenagerieWithLargeDB(unittest.TestCase):

    def test_loads_a_large_db(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.readFromFile("bn1g.txt")
        Deductions().apply(m)
        print DotRenderer(m).render(showWeakOpenImplications=True, showStrongOpenImplications=False).to_string()

if __name__ == "__main__":
    unittest.main()
        
