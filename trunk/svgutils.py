from xml.dom import minidom
from menagerie2 import COUNTABLE, UNCOUNTABLE, MEAGER, COMEAGER

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
        self.cardinalityAndCategoryLookupTable = {(COUNTABLE, MEAGER): "countable", 
                                                  (UNCOUNTABLE, MEAGER): "uncountableMeager", 
                                                  (UNCOUNTABLE, COMEAGER): "uncountableComeager",
                                                  (UNCOUNTABLE, None): "uncountableUnknown", 
                                                  (None, MEAGER): "unknownMeager", 
                                                  (None, None): "unknownUnknown"}

    def buildCardinalityAndCategoryMap(self):
        result = {}
        for cls in self.menagerie.classes:
            result[cls.name] = self.cardinalityAndCategoryLookupTable[(cls.cardinality.propertyValue, cls.category.propertyValue)]
        return result
