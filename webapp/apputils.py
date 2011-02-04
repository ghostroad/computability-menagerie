from xml.dom import minidom
from menagerie.core import COUNTABLE, UNCOUNTABLE, MEAGER, COMEAGER

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

    def buildPropertiesMap(self):
        properties = {}
        decorator = HtmlClassDecorator()
        for cls in self.menagerie.classes:
            category = self.categoryLookupTable[(cls.cardinality.propertyValue, 
                                                 cls.category.propertyValue)]
            measure = self.measureClass(cls)
            properties[cls.name] = (category, measure, decorator.decorate(cls))
        return properties

    def measureClass(self, cls):
        largest = smallest = 0
        for attr in ["cardinality", "pdim", "hdim", "measure"]:
            prop = getattr(cls, attr)
            if prop == 1: smallest += 1
            if prop != 0 : largest += 1
        if largest == smallest: return "level{0}".format(largest) 
        else: return "level{0}-{1}".format(smallest, largest)

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
    

class HtmlClassDecorator:
    def decorate(self, cls):
        return '<span class="className">' + cls.displayName() + '</span>'

class HtmlWriter:
    def __init__(self):
        self.result = []
        self.classDecorator = HtmlClassDecorator()
    def write(self, item):
        self.result.append("<ul>")
        item.write(self)
        self.result.append("</ul>")
        return self
    def __repr__(self):
        return "".join(self.result)
    def beginFact(self, fact):
        self.result.append("<li>")
        fact.writeSummary(self)
        self.result.append("<ul>")
    def endFact(self):
        self.result.append("</ul></li>")
    def writeString(self, str):
        self.result.append(str)
    def writeClass(self, cls):
        self.result.append(self.classDecorator.decorate(cls));
    def writeImplication(self):
        self.result.append(" $\\Rightarrow$ ")
    def writeNonImplication(self):
        self.result.append(" $\\nRightarrow$ ")
    def writeLine(self, str):
        self.result.append("<li>{0}</li>".format(str))
    
classDecorator = HtmlClassDecorator()

