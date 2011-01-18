from flask import Flask, jsonify, request, render_template, make_response
from menagerie2 import *
from svgutils import *

m = Menagerie()
parser = MenagerieParser(m)
parser.readFromFile("database.txt")
Deductions().apply(m)


app = Flask(__name__)


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

@app.route('/')
def displayMenagerie():
    classesParam = request.args.get("classes", None)
    classNames = classesParam and classesParam.split(",") or []
    g = DotRenderer(m).render(showOnly = classNames, displayLongNames=True, showWeakOpenImplications = True, showStrongOpenImplications = True)
    processedSvg = SVGPostProcessor().process(g)
    
    classes = classNames and [m[className] for className in classNames] or m.classes()
    response = make_response(render_template("menagerie.html", graph = processedSvg.toxml(), classes = classes))
    response.headers["Content-Type"] = "application/xhtml+xml"
    return response

@app.route('/showClassDetails/<className>')
def showClassDetails(className):
    cls = m[className]
    properties = {"cls" : cls}
    for attr in CLASS_ATTRIBUTES:
        prop = getattr(cls, attr)
        properties[attr] = HtmlWriter().write(prop)
    return render_template("classDetail.html", **properties)

@app.route('/showImplications/<classA>/<classB>')
def showImplications(classA, classB):
    A = m[classA]
    B = m[classB]
    implications = [];
    forwardImplication = A.implies(B) or A.doesNotImply(B) or UnknownImplication(A, B)
    backwardImplication = B.implies(A) or B.doesNotImply(A) or UnknownImplication(B, A)

    implications.append(str(HtmlWriter().write(forwardImplication)))
    implications.append(str(HtmlWriter().write(backwardImplication)))
    
    return render_template("implications.html", implications=implications, clsA=A, clsB=B)


@app.route('/_recolor')
def recolor():
    cls = m[request.args.get('selectedClass', None)]
    classes = [m[clsName] for clsName in request.args.get("classes", None).split(",")]
    result = {"properlyAbove" : [], "above" : [], "properlyBelow": [], "below": [], "incomparable" : [], "other" : []}
    for other in classes:
        if other is not cls:
            if cls.implies(other): 
                if other.doesNotImply(cls): result["properlyAbove"].append(other.name)
                else: result["above"].append(other.name)
            elif other.implies(cls):
                if cls.doesNotImply(other): result["properlyBelow"].append(other.name)
                else: result["below"].append(other.name)
            elif cls.doesNotImply(other) and other.doesNotImply(cls):
                result["incomparable"].append(other.name)
            else: result["other"].append(other.name)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
