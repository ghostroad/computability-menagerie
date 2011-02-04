import unittest
from menagerie.core import *
from apputils import * 

class TestAppUtils(unittest.TestCase):

    def test_generate_html_output_of_justifications(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.readFromFile("database.txt")
        Deductions().apply(m)
        BBmin = m["BBmin"]
        BN3G = m["BN3G"]
        actual = HtmlWriter().write(BBmin.implies(BN3G))
        self.assertTrue(str(actual).startswith("""<ul><li><span class="className">minimal or computable</span> $\Rightarrow$ <span class="className">bounds no 3-generic</span><ul><li><span class="className">minimal or computable</span> $\Rightarrow$ <span class="className">bounds no 2-generic</span><ul><li><span class="className">minimal or computable</span>"""))

        self.assertEqual('<ul><li><span class="className">not DNC in 0\'</span> is uncountable<ul><li><span class="className">low for Kurtz random</span> is uncountable<ul><li>pdim(<span class="className">low for Kurtz random</span>) = 1<ul><li>UNJUSTIFIED</li></ul></li></ul></li><li><span class="className">low for Kurtz random</span> $\\Rightarrow$ <span class="className">not DNC in 0\'</span><ul><li><span class="className">low for Kurtz random</span> $\\Rightarrow$ <span class="className">hyperimmune-free</span><ul><li>[Downey, Griffiths and Reid 2004, On Kurtz randomness]</li></ul></li><li><span class="className">hyperimmune-free</span> $\\Rightarrow$ <span class="className">not DNC in 0\'</span><ul><li>UNJUSTIFIED</li></ul></li></ul></li></ul></li></ul>', str(HtmlWriter().write(m["NotDNCinZP"].cardinality)))

    def test_generate_dot_output(self):
        m = Menagerie()
        parser = MenagerieParser(m)
        parser.readFromFile("database.txt")
        Deductions().apply(m)
        classesToShow = [m[name] for name in ["LowSchnorr", "LowKurtz", "BBmin", "BB1G", "BNLFO", "NotHigh", "CET", "BN2G", "BN3G", "NotPAinZP"]]
        graph = DotRenderer(m, classesToShow).render()
        processedSvg = SVGPostProcessor().process(graph)
        self.assertTrue("<g class=\"node\" id=\"BN2G\">\n<ellipse" in processedSvg.toxml())
    
    def test_coloring_by_measure(self):
        measureLookupTable = {(COUNTABLE,   0, 0, 0) : "level0",
                              (UNCOUNTABLE, 0, 0, 0) : "level1",
                              (UNCOUNTABLE, 1, 0, 0) : "level2",
                              (UNCOUNTABLE, 1, 1, 0) : "level3",
                              (UNCOUNTABLE, 1, 1, 1) : "level4",
                              (UNCOUNTABLE, 1, 1, None) : "level3-4",
                              (UNCOUNTABLE, 1, None, 0) : "level2-3",
                              (UNCOUNTABLE, 1, None, None) : "level2-4",
                              (UNCOUNTABLE, None, 0, 0) : "level1-2",
                              (UNCOUNTABLE, None, None, 0) : "level1-3",
                              (UNCOUNTABLE, None, None, None) : "level1-4",
                              (None, 0, 0, 0) : "level0-1",
                              (None, None, 0, 0) : "level0-2",
                              (None, None, None, 0) : "level0-3",
                              (None, None, None, None) : "level0-4" }
        for props in measureLookupTable:
            cls = ClassNode("A", None, None)
            for index, attr in enumerate(["cardinality", "pdim", "hdim", "measure"]):
                getattr(cls, attr).propertyValue = props[index]
            self.assertEqual(measureLookupTable[props], Coloring(None).measureClass(cls))



if __name__ == "__main__":
    unittest.main()
        

