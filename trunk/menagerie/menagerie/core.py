from pyparsing import *
from collections import defaultdict
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


class ClassNotFoundError(Exception):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "No class named {0} found.".format(self.name)

class Menagerie:

    def __init__(self):
        self.implicationsMatrix = []
        self.nonimplicationsMatrix = []
        self.classCounter = 0
        self.classes = []
        self.classMap = ClassMap(self)
        self.warnings = []
        self.errors = []

    def __getitem__(self, name):
        if name in self.classMap: 
            return self.classMap.get(name)
        else:
            raise ClassNotFoundError(name)

    def addStrictImplication(self, source, dest, forwardJustification, backwardJustification):
        self.addImplication(source, dest, forwardJustification)
        self.addNonimplication(dest, source, backwardJustification)

    def addImplication(self, source, dest, justification):
        implication = Implication(source, dest, justification)
        if source.doesNotImply(dest): 
            self.errors.append("Inconsistency detected: {0}, reason for change: {1}".format(source.doesNotImply(dest), justification.plain()))
            return
        
        existingImplication = source.implies(dest)
        if not existingImplication:
            self.implicationsMatrix[source.index][dest.index] = implication
            source.implications.append(implication)
            if justification.empty(): self.warnings.append("Adding a fact without justification: {0}".format(implication))
        elif justification.weight < existingImplication.justification.weight:
            existingImplication.justification = justification
            existingImplication.weight = justification.weight + 1
            if justification.empty(): self.warnings.append("Adding a fact without justification: {0}".format(implication))


    def addNonimplication(self, source, dest, justification):
        nonimplication = Nonimplication(source, dest, justification)
        if source.implies(dest): 
            self.errors.append("Inconsistency detected: {0}, reason for change: {1}".format(source.implies(dest), justification.plain()))
            return
        
        existingNonimplication = source.doesNotImply(dest)
        if not existingNonimplication:
            self.nonimplicationsMatrix[source.index][dest.index] = nonimplication
            source.nonimplications.append(nonimplication)
            if justification.empty(): self.warnings.append("Adding a fact without justification: {0}".format(nonimplication))
        elif existingNonimplication.justification.weight > justification.weight:
            existingNonimplication.justification = justification
            existingNonimplication.weight = justification.weight + 1
            if justification.empty(): self.warnings.append("Adding a fact without justification: {0}".format(nonimplication))


    def setProperty(self, cls, propertyName, value, justification):
        prop = getattr(cls, propertyName)
        if prop.known() and prop != value: 
            self.errors.append("Inconsistency detected: {0}, reason for change: {1}".format(prop, justification.plain()))
            return

        if not prop.known() or justification.weight < prop.justification.weight:
            prop.set(value, justification)
            if justification.empty(): self.warnings.append("Adding a fact without justification: {0}".format(prop))

    def facts(self):
        for cls in self.classes:
            for prop in [getattr(cls, attr) for attr in CLASS_ATTRIBUTES if getattr(cls, attr).known()]: yield prop
            for imp in cls.implications: yield imp
            for imp in cls.nonimplications: yield imp

    def numFactsAndUnjustifiedFacts(self):
        numFacts = 0
        numUnjustifiedFacts = 0
        for fact in self.facts():
            numFacts += 1
            if fact.justification.empty(): numUnjustifiedFacts += 1
        return numFacts, numUnjustifiedFacts
    
    def compile(self):
        result = ["from menagerie.core import *", "menagerie = Menagerie()"]
        for cls in self.classes:
            result.append("{0} = menagerie.classMap[\"{1}\"]".format(cls.identifier(), cls.name))
            if cls.longName: result.append("{0}.longName = {1}".format(cls.identifier(), repr(cls.longName)))
        weights = sorted(set(fact.weight for fact in self.facts()))
        for weight in weights:
            for fact in self.facts():
                if fact.weight == weight:
                    result.append(fact.compileAdd())
        return "\n".join(result)

class Deductions:
    def apply(self, menagerie):
        self.__closeUnderSizeImplications(menagerie)
        cyclic = self.__closeImplicationsUnderTransitivityAndDetectCycles(menagerie)
        self.__deriveSizePropertiesFromImplications(menagerie)
        if not cyclic:
            self.__deriveNonimplicationsFromSizeProperties(menagerie)
            self.__inferNonimplicationsFromTransivityOfImplication(menagerie)

    def __closeUnderSizeImplications(self, menagerie):
        for cls in menagerie.classes:
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
        for b, a, c in product(menagerie.classes, repeat=3):
            if a.implies(b) and b.implies(c):
                if a is c: 
                    menagerie.errors.append("Graph is cyclic: {0} and {1}".format(a.implies(b).plain(), b.implies(c).plain()))
                    cyclic = True
                else: 
                    menagerie.addImplication(a, c, CompositeJustification(a.implies(b), b.implies(c)))
        return cyclic

    def __deriveSizePropertiesFromImplications(self, menagerie):
        for cls in menagerie.classes:
            for implication in cls.implications:
                supercls = implication.dest
                for attr in CLASS_ATTRIBUTES:
                    clsprop = getattr(cls, attr)
                    if clsprop == 1: menagerie.setProperty(supercls, attr, 1, CompositeJustification(clsprop, implication))
                    superclsprop = getattr(supercls, attr)
                    if superclsprop == 0: menagerie.setProperty(cls, attr, 0, CompositeJustification(superclsprop, implication))

    def __deriveNonimplicationsFromSizeProperties(self, menagerie):
        for a, b in product(menagerie.classes, repeat=2):
            for attr in CLASS_ATTRIBUTES:
                if getattr(a, attr) == 1 and getattr(b, attr) == 0:
                    menagerie.addNonimplication(a, b, CompositeJustification(getattr(a, attr), getattr(b, attr)))
    
    def __inferNonimplicationsFromTransivityOfImplication(self, menagerie):
        imp = menagerie.implicationsMatrix
        nonimp = menagerie.nonimplicationsMatrix
        for a, b, c in product(menagerie.classes, repeat=3):
            cimpa = imp[c.index][a.index]
            bnotimpa = nonimp[b.index][a.index]
            aimpb = imp[a.index][b.index]
            anotimpc = nonimp[a.index][c.index]
            if cimpa and bnotimpa: menagerie.addNonimplication(b, c, CompositeJustification(cimpa, bnotimpa))
            if aimpb and anotimpc: menagerie.addNonimplication(b, c, CompositeJustification(aimpb, anotimpc))

class ClassMap(defaultdict):
    def __init__(self, menagerie):
        self.menagerie = menagerie
    def __missing__(self, key):
        newClass = ClassNode(key, self.menagerie.classCounter, self.menagerie)
        self.menagerie.classCounter += 1
        self.menagerie.classes.append(newClass)
        self.__expandImplicationsMatrices()
        self[key] = newClass
        return newClass
    def __expandImplicationsMatrices(self):
        for row in self.menagerie.implicationsMatrix:
            row.append(None)
        self.menagerie.implicationsMatrix.append([None]*self.menagerie.classCounter)
        for row in self.menagerie.nonimplicationsMatrix:
            row.append(None)
        self.menagerie.nonimplicationsMatrix.append([None]*self.menagerie.classCounter)

class ClassNode(object):
    __slots__ = ["index", "menagerie", "name", "longName", "implications", 
                 "nonimplications", "cardinality", "category", "measure", "hdim", "pdim"]
    def __init__(self, name, index, menagerie):
        self.index = index
        self.menagerie = menagerie
        self.name = name
        self.longName = None
        self.implications = []
        self.nonimplications = []
        self.cardinality = Cardinality(self)
        self.category = Category(self)
        self.measure = Property(self, "measure")
        self.hdim = Property(self, "hdim")
        self.pdim = Property(self, "pdim")
    def displayName(self):
        return self.longName or self.name
    def implies(self, other):
        return self.menagerie.implicationsMatrix[self.index][other.index]
    def doesNotImply(self, other):
        return self.menagerie.nonimplicationsMatrix[self.index][other.index]
    def implicationUnknown(self, other):
        return not (self.implies(other) or self.doesNotImply(other))
    def incomparableTo(self, other):
        return self.doesNotImply(other) and other.doesNotImply(self)
    def identifier(self):
        return self.name
    def __repr__(self):
        return self.name


class NonEmpty(object):
    __slots__ = []
    def empty(self):
        return False

class Justifiable(NonEmpty):
    __slots__ = []
    def plain(self):
        return "{0} : {1}".format(self, self.justification.plain())
    def write(self, out):
        out.beginFact(self)
        self.justification.write(out)
        out.endFact()

class Property(Justifiable):
    __slots__ = ["cls", "propertyName", "propertyValue", "justification", "weight"]
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
        self.weight = justification.weight + 1
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
    def compileAdd(self):
        return "menagerie.setProperty({0}, \"{1}\", {2}, {3})".format(self.cls.identifier(), self.propertyName, self.propertyValue, self.justification.compileReference())
    def compileReference(self):
        return "{0}.{1}".format(self.cls.identifier(), self.propertyName)

class IsProperty(Property):
    __slots__ = []
    def __repr__(self):
        return "{0} is {1}".format(self.cls, self.prettyPropertyValue())
    def writeSummaryKnown(self, out):
        out.writeClass(self.cls)
        out.writeString(" is ")
        out.writeString(self.prettyPropertyValue())

class Cardinality(IsProperty):
    __slots__ = []
    def __init__(self, cls):
        IsProperty.__init__(self, cls, "cardinality")
    def prettyPropertyValue(self):
        return self.propertyValue and "uncountable" or "countable"

class Category(IsProperty):
    __slots__ = []
    def __init__(self, cls):
        IsProperty.__init__(self, cls, "category")
    def prettyPropertyValue(self):
        return self.propertyValue and "comeager" or "meager"
    

class Implication(Justifiable):
    __slots__ = ["source", "dest", "justification", "weight"]
    def __init__(self, source, dest, justification):
        self.source = source
        self.dest = dest
        self.justification = justification
        self.weight = self.justification.weight + 1
    def writeSummary(self, out):
        out.writeClass(self.source)
        out.writeImplication()
        out.writeClass(self.dest)
    def compileAdd(self):
        return "menagerie.addImplication({0}, {1}, {2})".format(self.source.identifier(), self.dest.identifier(), self.justification.compileReference())
    def compileReference(self):
        return "{0}.implies({1})".format(self.source.identifier(), self.dest.identifier())
    def __repr__(self):
        return "{0} -> {1}".format(self.source, self.dest)

class Nonimplication(Implication):
    __slots__ = []
    def __repr__(self):
        return "{0} -/> {1}".format(self.source, self.dest)
    def compileAdd(self):
        return "menagerie.addNonimplication({0}, {1}, {2})".format(self.source.identifier(), self.dest.identifier(), self.justification.compileReference())
    def compileReference(self):
        return "{0}.doesNotImply({1})".format(self.source.identifier(), self.dest.identifier())
    def writeSummary(self, out):
        out.writeClass(self.source)
        out.writeNonImplication()
        out.writeClass(self.dest)

class DirectJustification(NonEmpty):
    __slots__ = ["justification", "weight"]
    def __init__(self, justification):
        self.justification = justification
        self.weight = 1
    def __repr__(self):
        return self.justification
    def plain(self):
        return self.justification
    def write(self, out):
        out.writeLine(self.justification)
    def compileReference(self):
        return "DirectJustification({0})".format(repr(self.justification))
        
class Empty(object):
    __slots__ = []
    def write(self, out):
        pass

class Obvious(DirectJustification):
    __slots__ = []
    def __init__(self):
        DirectJustification.__init__(self, None)
    def compileReference(self):
        return "Obvious()"
    def write(self, out):
        pass

class Unjustified(DirectJustification):
    __slots__ = []
    def __init__(self):
        DirectJustification.__init__(self, "UNJUSTIFIED")
    def empty(self):
        return True
    def compileReference(self):
        return "Unjustified()"

class CompositeJustification(NonEmpty):
    __slots__ = ["children", "weight"]
    def __init__(self, *children):
        self.children = children
        self.weight = 1
        for child in self.children:
            self.weight += child.weight
    def __repr__(self):
        return self.children.__repr__()
    def plain(self):
        return "[" + ", ".join([child.plain() for child in self.children]) + "]"
    def compileReference(self):
        return "CompositeJustification({0})".format(", ".join([child.compileReference() for child in self.children]))
    def write(self, out):
        for child in self.children:
            child.write(out)
                                       
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


class DotRenderer(object):
    def __init__(self, menagerie, classes = [], showOpenImplications = False):
        self.menagerie = menagerie
        self.classes = set(classes or self.menagerie.classes)
        self.showOpenImplications = showOpenImplications
    def render(self):
        graph = Dot(rankdir = "BT")
        graph.set_name("\"The Computability Menagerie\"")
        if self.menagerie.errors: graph.set_bgcolor("pink")
        self.__addClasses(graph)
        self.__addEdges(graph)
        self.addOpenImplicationsIfAppropriate(graph)
        return graph

    def addOpenImplicationsIfAppropriate(self, graph):
        if self.showOpenImplications: self.addOpenImplications(graph, True, True)

    def __addClasses(self, graph):
        for cls in self.classes:
            graph.add_node(self.createNodeFor(cls))

    def __addEdges(self, graph):
        for cls in self.classes:
            implied = self.classes.intersection(imp.dest for imp in cls.implications)
            for dest in implied:
                for other in implied:
                    if (other is not dest) and other.implies(dest): break
                else:
                    edge = Edge(cls.name, dest.name)
                    if not dest.doesNotImply(cls): edge.set_id("nonstrict-\\E")
                    graph.add_edge(edge)

    def addOpenImplications(self, graph, showWeakOpenImplications, showStrongOpenImplications):
        weakEdges = {}
        strongEdges = {}
        imp, nonimp = self.menagerie.implicationsMatrix, self.menagerie.nonimplicationsMatrix
        idCounter = 0
        for a, b in permutations(self.classes, 2):
            if a.implicationUnknown(b):
                strong = weak = True
                for c in self.classes:
                    if (c is not a) and (c is not b):
                        if imp[c.index][a.index] and not (imp[c.index][b.index] or nonimp[c.index][b.index]): weak = False
                        if imp[b.index][c.index] and not (imp[a.index][c.index] or nonimp[a.index][c.index]): weak = False
                        if imp[a.index][c.index] and not (imp[c.index][b.index] or nonimp[c.index][b.index]): strong = False
                        if imp[c.index][b.index] and not (imp[a.index][c.index] or nonimp[a.index][c.index]): strong = False
                if weak and showWeakOpenImplications:
                    if (b.name, a.name) in weakEdges: 
                        weakEdges[(b.name, a.name)].set_dir("both")
                    else:
                        edge = Edge(a.name, b.name)
                        edge.set_color("red")
                        edge.set_style("dashed")
                        edge.set_id('"weak-{0}"'.format(idCounter))
                        idCounter += 1
                        graph.add_edge(edge)
                        weakEdges[(a.name, b.name)] = edge
                if strong and showStrongOpenImplications:
                    if (b.name, a.name) in strongEdges:
                        strongEdges[(b.name, a.name)].set_dir("both")
                    else:
                        edge = Edge(a.name, b.name)
                        edge.set_color("green")
                        edge.set_style("dashed")
                        edge.set_id('"strong-{0}"'.format(idCounter))
                        idCounter += 1
                        graph.add_edge(edge)
                        strongEdges[(a.name, b.name)] = edge
                        

    def createNodeFor(self, cls):
        node = Node(cls.name)
        node.set_id('"' + cls.name + '"')
        node.set_fontsize(10)
        node.set_color("black")
        node.set_style("filled")
        node.set_color("lightgrey")
        node.set_margin("0.0825,0.0412")
        node.set_label("\\n".join(textwrap.wrap(cls.displayName(), 12)))
	return node

class DotCommandLineRenderer(DotRenderer):
    def __init__(self, menagerie, classes = [], showWeakOpenImplications = False, showStrongOpenImplications = False, plain = False):
        super(DotCommandLineRenderer, self).__init__(menagerie, classes, False)
        self.showWeakOpenImplications = showWeakOpenImplications
        self.showStrongOpenImplications = showStrongOpenImplications
        self.plain = plain

    def addOpenImplicationsIfAppropriate(self, graph):
        if self.showWeakOpenImplications or self.showStrongOpenImplications: self.addOpenImplications(graph, self.showWeakOpenImplications, 
                                                                                              self.showStrongOpenImplications)
        
    def createNodeFor(self, cls):
        node = Node(cls.name)
        node.set_label("\\n".join(textwrap.wrap(cls.displayName(), 12)))
        if self.plain: return node
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

