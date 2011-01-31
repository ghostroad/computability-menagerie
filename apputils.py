from xml.dom import minidom
from menagerie_core import COUNTABLE, UNCOUNTABLE, MEAGER, COMEAGER, HtmlClassDecorator

classDecorator = HtmlClassDecorator()

class UnknownImplication:
    def __init__(self, src, dest):
        self.src = src
        self.dest = dest
    def write(self, out):
        out.beginFact(self)
        out.endFact()
    def writeSummary(self, out):
        out.writeString("It is not known whether ")
        out.writeClass(self.src)
        out.writeImplication()
        out.writeClass(self.dest)
        out.writeString(".")


class SVGPostProcessor:
    def process(self, graph):
        rawSource = graph.create_svg()
        xmlSource = minidom.parseString(rawSource)
        svgtag = xmlSource.getElementsByTagName("svg")[0]
        self.__deleteTitles(svgtag)
        return svgtag

    def __deleteTitles(self, node):
        if not node.childNodes: return
        for child in node.childNodes:
            if child.nodeName == "title": node.removeChild(child)
            else: self.__deleteTitles(child)

class Coloring:
    def __init__(self, menagerie):
        self.menagerie = menagerie
        self.categoryLookupTable = {(COUNTABLE, MEAGER): "countable", 
                                    (UNCOUNTABLE, MEAGER): "uncountableMeager", 
                                    (UNCOUNTABLE, COMEAGER): "uncountableComeager",
                                    (UNCOUNTABLE, None): "uncountableUnknown", 
                                    (None, MEAGER): "unknownMeager", 
                                    (None, None): "unknownUnknown"}
        self.measureLookupTable = {(COUNTABLE,   0, 0, 0) : "level0",
                                   (UNCOUNTABLE, 0, 0, 0) : "level1",
                                   (UNCOUNTABLE, 1, 0, 0) : "level2",
                                   (UNCOUNTABLE, 1, 1, 0) : "level3",
                                   (UNCOUNTABLE, 1, 1, 1) : "level4",
                                   (UNCOUNTABLE, 1, 1, None) : "level3-4",
                                   (UNCOUNTABLE, 1, None, 0) : "level2-3",
                                   (UNCOUNTABLE, 1, None, None) : "level2-4",
                                   (UNCOUNTABLE, None, 0, 0) : "level1-2",
                                   (UNCOUNTABLE, None, None, 0) : "level0-3",
                                   (UNCOUNTABLE, None, None, None) : "level1-4",
                                   (None, 0, 0, 0) : "level0-1",
                                   (None, None, 0, 0) : "level0-2",
                                   (None, None, None, 0) : "level0-3",
                                   (None, None, None, None) : "level0-4" }

    def buildPropertiesMap(self):
        properties = {}
        decorator = HtmlClassDecorator()
        for cls in self.menagerie.classes:
            category = self.categoryLookupTable[(cls.cardinality.propertyValue, 
                                                 cls.category.propertyValue)]
            measure = self.measureLookupTable[(cls.cardinality.propertyValue, cls.pdim.propertyValue, 
                                               cls.hdim.propertyValue, cls.measure.propertyValue)]
            properties[cls.name] = (category, measure, decorator.decorate(cls))
        return properties


def buildMap(menagerie, A, B):
    result = {}
    for C in menagerie.classes:
        if (A.implies(C) and (C).implies(B)):
            result[C.name] = "betw"
        elif A.doesNotImply(C) or C.doesNotImply(B):
            result[C.name] = "notBetw"
        else:
            result[C.name] = "possiblyBetw"
    return result
    

