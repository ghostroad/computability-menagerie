from __future__ import unicode_literals
import unittest
from menagerie.core import *

class TestMenagerie(unittest.TestCase):

    def test_loads_properties_and_implications(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.readFromFile("database.txt")
        self.assertTrue(m["BN1R"] is not None)
        self.assertTrue(m["BBmin"].implies(m["BN1G"]))
        self.assertTrue(m["BBmin"].implies(m["BN1R"]))
        self.assertTrue(m["BBmin"].doesNotImply(m["BNDeltaTwo"]))
        self.assertEqual("If $A\oplus B$ is 1-random then $A$ and $B$ are Turing incomparable", unicode(m["BBmin"].implies(m["BN1R"]).justification))
        self.assertEqual("The class of 3-randoms has measure one", unicode(m["BB3R"].measure.justification))
        self.assertTrue(m["BB2G"].category == COMEAGER)
        self.assertTrue(m["BN3G"].category == MEAGER)
        self.assertTrue(m["DeltaTwo"].cardinality == COUNTABLE)
        self.assertTrue(m["JumpTraceable"].cardinality == UNCOUNTABLE)
        self.assertEqual("[Nies 2002, Reals which compute little]", unicode(m["JumpTraceable"].cardinality.justification))
        self.assertEqual(34, len(m.classes))
        numFacts, numUnjustifiedFacts = m.numFactsAndUnjustifiedFacts();
        self.assertEqual(117, numFacts)
        self.assertEqual(19, numUnjustifiedFacts)
        Deductions().apply(m)
        self.assertEquals(0, len(m.errors))
        BBmin = m["BBmin"]
        BN1R = m["BN1R"]
        self.assertEqual("""BN1R -/> BBmin
    Low1Rand -> BN1R
        Low1Rand -> NotDNC
            Low1Rand -> JumpTraceable
                UNJUSTIFIED
            JumpTraceable -> NotDNC
                JumpTraceable -> CET
                    [Nies 2002, Reals which compute little]
                CET -> NotDNC
                    UNJUSTIFIED
        NotDNC -> BN1R
            Every 1-random compute a diagonally noncomputable function [Ku\u010dera 1985, Measure, $\Pi^0_1$ classes, and complete extensions of PA]
    Low1Rand -/> BBmin
        BBmin -> BN1G
            If $A\oplus B$ is 1-generic then $A$ and $B$ are Turing incomparable
        Low1Rand -/> BN1G
            There is a noncomputable c.e.\ low for random [Ku\u010dera and Terwijn 1999, Lowness for the class of random sets] and every noncomputable c.e.\ set computes a 1-generic""", unicode(TextWriter().write(BN1R.doesNotImply(BBmin))))
        self.assertEqual("""BN1G -> BN2G""", unicode(TextWriter().write(m["BN1G"].implies(m["BN2G"]))))


    def test_load_a_database_from_a_string(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.read("A -> B\nM(B) = 1\n")
        self.assertEqual(2, len(m.classes))
        parser.read("A is countable")
        self.assertEqual(COUNTABLE, m["A"].cardinality)
        self.assertEqual(2, len(m.classes))

    def test_close_under_size_implications(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.read("A -> B\nB is countable")
        B = m["B"]
        self.assertEqual("hdim(B) = None", unicode(B.hdim))
        Deductions().apply(m)
        self.assertEqual(COUNTABLE, B.cardinality)
        self.assertEqual(MEAGER, B.category)
        self.assertEqual("B is countable", unicode(B.category.justification))
        self.assertEqual(0, B.hdim)
        self.assertEqual("hdim(B) = 0", unicode(B.hdim))
        self.assertEqual("B is countable", unicode(B.hdim.justification))
        self.assertTrue("Adding a fact without justification: B is countable" in m.warnings)
        parser.read("B is uncountable")
        self.assertTrue("Inconsistency detected: B is countable : UNJUSTIFIED, reason for change: UNJUSTIFIED" in m.errors)

    def test_close_under_implications(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.read("A -> B\nB -> C\nC -> D\nD -> E\nC -> E")
        A = m["A"]
        E = m["E"]
        Deductions().apply(m)
        self.assertTrue(A.implies(E))
        self.assertEqual("[A -> C : [A -> B : UNJUSTIFIED, B -> C : UNJUSTIFIED], C -> E : UNJUSTIFIED]" , A.implies(E).justification.plain())

    def test_derive_size_properties_from_implications(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.read("A -> B\nA is uncountable\nC -> D\nD is meager")
        A = m["A"]
        B = m["B"]
        C = m["C"]
        Deductions().apply(m)
        self.assertTrue(B.cardinality == UNCOUNTABLE)
        self.assertEqual("[A is uncountable : UNJUSTIFIED, A -> B : UNJUSTIFIED]", B.cardinality.justification.plain())
        self.assertTrue(C.category == MEAGER)
        self.assertEqual("[D is meager : UNJUSTIFIED, C -> D : UNJUSTIFIED]", C.category.justification.plain())
        
    def test_derive_nonimplications_from_size_properties(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.read("A is uncountable\nB is countable\nC -> B")
        A = m["A"]
        B = m["B"]
        C = m["C"]
        Deductions().apply(m)
        self.assertEqual("[A is uncountable : UNJUSTIFIED, B is countable : UNJUSTIFIED]", A.doesNotImply(B).justification.plain())
        self.assertEqual("[A is uncountable : UNJUSTIFIED, C is countable : [B is countable : UNJUSTIFIED, C -> B : UNJUSTIFIED]]", A.doesNotImply(C).justification.plain())

    def test_infer_nonimplications_from_transitivity_of_implication(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.read("A -> B\nC -/> B")
        A = m["A"]
        B = m["B"]
        C = m["C"]
        Deductions().apply(m)
        self.assertEqual("[A -> B : UNJUSTIFIED, C -/> B : UNJUSTIFIED]", C.doesNotImply(A).justification.plain())

    def test_write_latex_justification(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.readFromFile("database.txt")
        Deductions().apply(m)
        self.assertEqual("""\\begin{fact}{BNLFO -/> BBmin}
\\begin{fact}{BBmin -> NotPA}
\\begin{fact}{BBmin -> BN1R}
If $A\\oplus B$ is 1-random then $A$ and $B$ are Turing incomparable
\\end{fact}
\\begin{fact}{BN1R -> NotPA}
There is a $\\Pi^0_1$ class containing only 1-random reals, hence every PA degree computes a 1-random
\\end{fact}
\\end{fact}
\\begin{fact}{BNLFO -/> NotPA}
\\begin{fact}{HIF -> BNLFO}
Hyperimmune-free and low for $\\Omega$ implies computable [Miller and Nies] (See [Nies 2009, Computability and Randomness])
\\end{fact}
\\begin{fact}{HIF -/> NotPA}
Use the hyperimmune-free basis theorem
\\end{fact}
\\end{fact}
\\end{fact}
""", unicode(LatexWriter().write(m["BNLFO"].doesNotImply(m["BBmin"]))))
        
    def test_compiling_the_menagerie(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.read(u"""A -> B "A very elegant observation of E\u00C9yore." \nB -> C ""\nM(A) = 1""")
        Deductions().apply(m)
        exec(m.compile())
        self.assertTrue(menagerie["A"].implies(menagerie["C"]))
        self.assertEqual(1, menagerie["C"].measure)

if __name__ == "__main__":
    unittest.main()
        
