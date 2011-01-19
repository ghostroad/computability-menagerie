from pyparsing import *
from itertools import product, permutations
from pydot import Dot, Node, Edge
import textwrap

COMEAGER = 1
MEAGER = 0
COUNTABLE = 0
UNCOUNTABLE = 1

CLASS_ATTRIBUTES = ["cardinality", "category", "hdim", "pdim", "measure"]

class MenagerieParser:

    def __init__(self, menagerie):
        comment = Literal("#") + SkipTo(LineEnd())
        name = (Word(alphas+"_", alphanums+"_") + NotAny(Literal("("))).setParseAction(lambda t: menagerie.classMap[t[0]])
        justification = Optional(QuotedString("\"").setParseAction(lambda t: t[0] and DirectJustification(t[0]) or Obvious()), Unjustified())
        nonimplication = Literal("-/>").setParseAction(lambda t: menagerie.addNonimplication)
        implication = Literal("->").setParseAction(lambda t: menagerie.addImplication)
        impOp = nonimplication | implication
        implication = (name + impOp + name + justification).setParseAction(lambda t: t[1](t[0],t[2],t[3]))
        strictimp = (name + Literal("->>").suppress() + name + justification + justification).setParseAction(lambda t:  menagerie.addStrictImplication(t[0], t[1], t[2], t[3]))
        prop = Literal("meager").setParseAction(lambda t: (MEAGER, "category")) | Literal("comeager").setParseAction(lambda t: (COMEAGER, "category")) | Literal("countable").setParseAction(lambda t: (COUNTABLE, "cardinality")) | Literal("uncountable").setParseAction(lambda t: (UNCOUNTABLE, "cardinality"))
        setprop = (name + Optional(Literal("is").suppress()) + prop + justification).setParseAction(lambda t: menagerie.setProperty(t[0], t[1][1], t[1][0], t[2]))
        meas = Literal("M").setParseAction(lambda t: "measure") | Literal("HD").setParseAction(lambda t: "hdim") | Literal("PD").setParseAction(lambda t: "pdim")
        bit = Literal("0").setParseAction(lambda t: 0) | Literal("1").setParseAction(lambda t: 1)
        label = (name + QuotedString("\"")).setParseAction(lambda t: setattr(t[0], "longName", t[1]))
        reckoning = (meas + Literal("(").suppress() + name + Literal(")").suppress() + Literal("=").suppress() + bit + justification).setParseAction(lambda t: menagerie.setProperty(t[1], t[0], t[2], t[3]))
        self.database_parser = ZeroOrMore(implication | strictimp | setprop | label | reckoning | Literal(";") | comment) + StringEnd()

    def readFromFile(self, filename):
        self.database_parser.parseFile(filename)

    def read(self, source):
        self.database_parser.parseString(source)

class Menagerie:

    def __init__(self):
        self.classMap = ClassMap()
        self.warnings = []
        self.errors = []

    def __getitem__(self, name):
        if self.classMap.has_key(name):
            return self.classMap[name]
        else: return None

    def addStrictImplication(self, source, dest, forwardJustification, backwardJustification):
        self.addImplication(source, dest, forwardJustification)
        self.addNonimplication(dest, source, backwardJustification)

    def addImplication(self, source, dest, justification):
        implication = Implication(source, dest, justification)
        if source.doesNotImply(dest): 
            self.errors.append("Inconsistency detected: {0}, reason for change: {1}".format(source.doesNotImply(dest), justification.plain()))
            return
        
        if not source.implies(dest) or justification.weight() < source.implies(dest).justification.weight():
            if justification.empty(): self.warnings.append("Adding a fact without justification: {0}".format(implication))
            source.implications[dest] = implication

    def addNonimplication(self, source, dest, justification):
        nonimplication = Nonimplication(source, dest, justification)
        if source.implies(dest): 
            self.errors.append("Inconsistency detected: {0}, reason for change: {1}".format(source.implies(dest), justification.plain()))
            return
        
        if not source.doesNotImply(dest) or justification.weight() < source.doesNotImply(dest).justification.weight():
            if justification.empty(): self.warnings.append("Adding a fact without justification: {0}".format(nonimplication))
            source.nonimplications[dest] = nonimplication

    def classes(self):
        return self.classMap.values()

    def setProperty(self, cls, propertyName, value, justification):
        prop = getattr(cls, propertyName)
        if prop.known() and prop != value: 
            self.errors.append("Inconsistency detected: {0}, reason for change: {1}".format(prop, justification.plain()))
            return

        if not prop.known() or justification.weight() < prop.justification.weight():
            prop.set(value, justification)
            if justification.empty(): self.warnings.append("Adding a fact without justification: {0}".format(prop))

    def facts(self):
        for cls in self.classes():
            for prop in [getattr(cls, attr) for attr in CLASS_ATTRIBUTES if getattr(cls, attr).known()]: yield prop
            for imp in cls.implications.values(): yield imp
            for imp in cls.nonimplications.values(): yield imp

    def numFactsAndUnjustifiedFacts(self):
        numFacts = 0
        numUnjustifiedFacts = 0
        for fact in self.facts():
            numFacts += 1
            if fact.justification.empty(): numUnjustifiedFacts += 1
        return numFacts, numUnjustifiedFacts

class Deductions:
    def apply(self, menagerie):
        self.__closeUnderSizeImplications(menagerie)
        cyclic = self.__closeImplicationsUnderTransitivityAndDetectCycles(menagerie)
        self.__deriveSizePropertiesFromImplications(menagerie)
        if not cyclic:
            self.__deriveNonimplicationsFromSizeProperties(menagerie)
            self.__inferNonimplicationsFromTransivityOfImplication(menagerie)

    def __closeUnderSizeImplications(self, menagerie):
        for cls in menagerie.classes():
            if cls.cardinality == COUNTABLE:
                for prop, val in [("category", MEAGER), ("measure", 0), ("hdim", 0), ("pdim", 0)]:
                    menagerie.setProperty(cls, prop, val, cls.cardinality)
            elif cls.pdim == 0:
                for prop, val in [("category", MEAGER), ("measure", 0), ("hdim", 0)]:
                    menagerie.setProperty(cls, prop, val, cls.pdim)
            elif cls.hdim == 0:
                menagerie.setProperty(cls, "measure", 0, cls.hdim)
            elif cls.measure == 1:
                for prop, val in [("cardinality", UNCOUNTABLE), ("hdim", 1), ("pdim", 1)]:
                    menagerie.setProperty(cls, prop, val, cls.measure)
            if cls.hdim == 1:
                for prop, val in [("cardinality", UNCOUNTABLE), ("pdim", 1)]:
                    menagerie.setProperty(cls, prop, val, cls.hdim)
            elif cls.category == COMEAGER:
                for prop, val in [("cardinality", UNCOUNTABLE), ("pdim", 1)]:
                    menagerie.setProperty(cls, prop, val, cls.category)
            elif cls.pdim == 1:
                menagerie.setProperty(cls, "cardinality", UNCOUNTABLE, cls.pdim)

    def __closeImplicationsUnderTransitivityAndDetectCycles(self, menagerie):
        cyclic = False
        for b, a, c in product(menagerie.classes(), repeat=3):
            if a.implies(b) and b.implies(c):
                if a is c: 
                    menagerie.errors.append("Graph is cyclic: {0} and {1}".format(a.implies(b).plain(), b.implies(c).plain()))
                    cyclic = True
                else: 
                    menagerie.addImplication(a, c, CompositeJustification(a.implies(b), b.implies(c)))
        return cyclic

    def __deriveSizePropertiesFromImplications(self, menagerie):
        for cls in menagerie.classes():
            for implication in cls.implications.values():
                supercls = implication.dest
                for attr in CLASS_ATTRIBUTES:
                    clsprop = getattr(cls, attr)
                    if clsprop == 1: menagerie.setProperty(supercls, attr, 1, CompositeJustification(clsprop, implication))
                    superclsprop = getattr(supercls, attr)
                    if superclsprop == 0: menagerie.setProperty(cls, attr, 0, CompositeJustification(superclsprop, implication))

    def __deriveNonimplicationsFromSizeProperties(self, menagerie):
        for a, b in product(menagerie.classes(), repeat=2):
            for attr in CLASS_ATTRIBUTES:
                if getattr(a, attr) == 1 and getattr(b, attr) == 0:
                    menagerie.addNonimplication(a, b, CompositeJustification(getattr(a, attr), getattr(b, attr)))
    
    def __inferNonimplicationsFromTransivityOfImplication(self, menagerie):
        for a, b, c in product(menagerie.classes(), repeat=3):
            if c.implies(a) and b.doesNotImply(a): menagerie.addNonimplication(b, c, CompositeJustification(c.implies(a), b.doesNotImply(a)))
            if a.implies(b) and a.doesNotImply(c): menagerie.addNonimplication(b, c, CompositeJustification(a.implies(b), a.doesNotImply(c)))

class ClassMap(dict):
    def __getitem__(self, key):
        if key not in self:
            self[key] = ClassNode(key)
        return self.get(key)

class ClassNode:
    def __init__(self, name):
        self.name = name
        self.longName = None
        self.implications = {}
        self.nonimplications = {}
        self.cardinality = Cardinality(self)
        self.category = Category(self)
        self.measure = Property(self, "measure")
        self.hdim = Property(self, "hdim")
        self.pdim = Property(self, "pdim")
    def implies(self, other):
        return self.implications.get(other)
    def doesNotImply(self, other):
        return self.nonimplications.get(other)
    def implicationUnknown(self, other):
        return not (self.implies(other) or self.doesNotImply(other))
    def __hash__(self): # this should hurt performance, but actually improves it.
        return hash(self.name)
    def __eq__(self, other):
        return self.name == other.name
    def __repr__(self):
        return self.name

class NonEmpty:
    def empty(self):
        return False

class Justifiable(NonEmpty):
    def plain(self):
        return "{0} : {1}".format(self, self.justification.plain())
    def write(self, out):
        out.beginFact(self)
        self.justification.write(out)
        out.endFact()
    def weight(self):
        return 1 + self.justification.weight()

class Property(Justifiable):
    def __init__(self, cls, propertyName):
        self.cls = cls
        self.propertyValue = None
        self.propertyName = propertyName
        self.justification = Empty()
    def known(self):
        return self.propertyValue is not None
    def set(self, propertyValue, justification):
        self.propertyValue = propertyValue
        self.justification = justification
    def __repr__(self):
        return "{0}({1}) = {2}".format(self.propertyName, self.cls, self.propertyValue)
    def writeSummary(self, out):
        if not self.known(): 
            out.writeString("The {0} of ".format(self.propertyName))
            out.writeClass(self.cls)
            out.writeString(" is not known.")
        else:
            self.writeSummaryKnown(out)
    def writeSummaryKnown(self, out):
        out.writeString(self.propertyName + "(")
        out.writeClass(self.cls)
        out.writeString(") = {0}".format(self.propertyValue))
    def __eq__(self, other):
        return self.propertyValue == other
    def __ne__(self, other):
        return self.propertyValue != other

class IsProperty(Property):
    def __repr__(self):
        return "{0} is {1}".format(self.cls, self.prettyPropertyValue())
    def writeSummaryKnown(self, out):
        out.writeClass(self.cls)
        out.writeString(" is ")
        out.writeString(self.prettyPropertyValue())

class Cardinality(IsProperty):
    def __init__(self, cls):
        IsProperty.__init__(self, cls, "cardinality")
    def prettyPropertyValue(self):
        return self.propertyValue and "uncountable" or "countable"

class Category(IsProperty):
    def __init__(self, cls):
        IsProperty.__init__(self, cls, "category")
    def prettyPropertyValue(self):
        return self.propertyValue and "comeager" or "meager"
    

class Implication(Justifiable):
    def __init__(self, source, dest, justification):
        self.source = source
        self.dest = dest
        self.justification = justification
    def writeSummary(self, out):
        out.writeClass(self.source)
        out.writeImplication()
        out.writeClass(self.dest)
    def __repr__(self):
        return "{0} -> {1}".format(self.source, self.dest)

class Nonimplication(Implication):
    def __repr__(self):
        return "{0} -/> {1}".format(self.source, self.dest)
    def writeSummary(self, out):
        out.writeClass(self.source)
        out.writeNonImplication()
        out.writeClass(self.dest)

class DirectJustification(NonEmpty):
    def __init__(self, justification):
        self.justification = justification
    def weight(self):
        return 1
    def __repr__(self):
        return self.justification
    def plain(self):
        return self.justification
    def write(self, out):
        out.writeLine(self.justification)
        
class Empty:
    def write(self, out):
        pass

class Obvious(DirectJustification):
    def __init__(self):
        DirectJustification.__init__(self, None)
    def write(self, out):
        pass

class Unjustified(DirectJustification):
    def __init__(self):
        DirectJustification.__init__(self, "UNJUSTIFIED")
    def empty(self):
        return True

class CompositeJustification(NonEmpty):
    def __init__(self, *children):
        self.children = children
    def weight(self):
        result = 1
        for child in self.children:
            result += child.weight();
        return result
    def __repr__(self):
        return self.children.__repr__()
    def plain(self):
        return "[" + ", ".join([child.plain() for child in self.children]) + "]"
    def write(self, out):
        for child in self.children:
            child.write(out)
                                       
class TextWriter:
    def __init__(self):
        self.result = []
        self.indentLevel = 0
    def __currIndent(self):
        return "    " * self.indentLevel
    def write(self, item):
        item.write(self)
        return self
    def __repr__(self):
        return "\n".join(self.result)
    def beginFact(self, fact):
        self.result.append(self.__currIndent() + str(fact))
        self.indentLevel += 1
    def endFact(self):
        self.indentLevel -= 1
    def writeString(self, str):
        self.result.append(self.__currIndent() + str)
    def writeLine(self, str):
        self.result.append(self.__currIndent() + str)

class HtmlWriter:
    def __init__(self):
        self.result = []
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
        self.result.append('<span class="className">' + (cls.longName or cls.name) + '</span>');
    def writeImplication(self):
        self.result.append(" $\\rightarrow$ ")
    def writeNonImplication(self):
        self.result.append(" $\\nrightarrow$ ")
    def writeLine(self, str):
        self.result.append("<li>{0}</li>".format(str))
    

class LatexWriter:
    def __init__(self):
        self.result = []
    def write(self, item):
        item.write(self)
        return self
    def __repr__(self):
        return "".join(self.result)
    def beginFact(self, fact):
        self.result.append("\\begin{fact}{")
        fact.writeSummary(self)
        self.result.append("}\n")
    def endFact(self):
        self.result.append("\\end{fact}\n")
    def writeClass(self, cls):
        self.result.append(cls.name)
    def writeImplication(self):
        self.result.append(" -> ")
    def writeNonImplication(self):
        self.result.append(" -/> ")
    def writeString(self, str):
        self.result.append(str)
    def writeLine(self, str):
        self.result.append(str + "\n")


class DotRenderer:
    def __init__(self, menagerie):
        self.menagerie = menagerie
    def render(self, showOnly = [], showWeakOpenImplications = False, showStrongOpenImplications = False, displayLongNames = False):
        if showOnly: 
            classes = set([self.menagerie[name] for name in showOnly])
        else: classes = set(self.menagerie.classes())

        graph = Dot(rankdir = "BT")
        graph.set_name("\"The Computability Menagerie\"")
        if self.menagerie.errors: graph.set_bgcolor("pink")
        self.__addClasses(graph, displayLongNames, classes)
        self.__addEdges(graph, classes)
        if showWeakOpenImplications or showStrongOpenImplications: self.__addOpenImplications(graph, showWeakOpenImplications, showStrongOpenImplications, classes)
        return graph

    def __addOpenImplications(self, graph, showWeakOpenImplications, showStrongOpenImplications, classes):
        idCounter = 0
        for a, b in permutations(classes, 2):
            if a.implicationUnknown(b):
                strong = weak = True
                for c in classes:
                    if (c is not a) and (c is not b):
                        if c.implies(a) and c.implicationUnknown(b): weak = False
                        if b.implies(c) and a.implicationUnknown(c): weak = False
                        if a.implies(c) and c.implicationUnknown(b): strong = False
                        if c.implies(b) and a.implicationUnknown(c): strong = False
                if weak and showWeakOpenImplications:
                    edge = Edge(a.name, b.name)
                    edge.set_color("red")
                    edge.set_style("dashed")
                    edge.set_id('"weak-{0}"'.format(idCounter))
                    idCounter += 1
                    graph.add_edge(edge)
                if strong and showStrongOpenImplications:
                    edge = Edge(a.name, b.name)
                    edge.set_color("green")
                    edge.set_style("dashed")
                    edge.set_id('"strong-{0}"'.format(idCounter))
                    idCounter += 1
                    graph.add_edge(edge)
                        
    def __addClasses(self, graph, displayLongNames, classes):
        for cls in classes:
            node = self.__createNodeFor(cls)
            if displayLongNames and cls.longName: 
                node.set_label("\\n".join(textwrap.wrap(cls.longName, 12)))
            graph.add_node(node)

    def __addEdges(self, graph, classes):
        for cls in classes:
            for dest in classes.intersection(cls.implications):
                for other in classes.intersection(cls.implications):
                    if (other is not dest) and other.implies(dest): break
                else:
                    graph.add_edge(Edge(cls.name, dest.name))


    def __createNodeFor(self, cls):
        node = Node(cls.name)
        node.set_id('"' + cls.name + '"')
        node.set_fontsize(12)
        if cls.category == MEAGER:
            node.set_style("filled")
            if cls.cardinality == COUNTABLE:
                node.set_color("grey")
            elif cls.cardinality == UNCOUNTABLE:
                node.set_color("black")
            else:
                node.set_color("red")
        elif not cls.category.known():
            node.set_shape("box")
            node.set_margin("0.22,0.1")
            node.set_color("red")
            if cls.cardinality == COUNTABLE:
                node.set_style("")
            elif cls.cardinality == UNCOUNTABLE:
                node.set_style("filled")
            else:
                node.set_style("filled, dashed")
        else:
            node.set_shape("box")
            node.set_margin("0.22,0.1")
            node.set_style("filled")

        k=0
        for attr in ["measure", "pdim", "hdim"]:
            if not getattr(cls, attr).known(): node.set_fontcolor("red")
            if getattr(cls, attr) == 1: k = k + 1
        node.set_fillcolor("#" + ['CCCCCC','00FF00','00FFFF','0000FF'][k])
        
	return node
