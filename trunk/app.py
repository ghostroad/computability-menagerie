from flask import Flask, jsonify, request, render_template, make_response
from menagerie2 import *
from svgutils import *
from os import getenv

m = Menagerie()
parser = MenagerieParser(m)
parser.readFromFile(getenv("MENAGERIE_DATABASE_FILE") or "database.txt")
Deductions().apply(m)
category, measure = Coloring(m).buildPropertiesMaps()

app = Flask(__name__)

@app.route('/')
def displayMenagerie():
    classesParam = request.args.get("classes", None)
    classes = classesParam and [m[clsName] for clsName in classesParam.split(",")] or m.classes
    decorator = HtmlClassDecorator()
    excludedClasses = sorted([decorator.decorate(cls) for cls in set(m.classes).difference(classes)])
    g = DotRenderer(m, classes).render(displayLongNames=True)
    processedSvg = SVGPostProcessor().process(g)
    
    response = make_response(render_template("menagerie.html", graph = processedSvg, category = category, measure = measure, excludedClasses = excludedClasses))
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

    implications.append(HtmlWriter().write(forwardImplication))
    implications.append(HtmlWriter().write(backwardImplication))
    
    return render_template("implications.html", implications=implications, clsA=A, clsB=B)


@app.route('/_recolorSingleSelected')
def recolorSingleSelected():
    cls = m[request.args.get('selectedClass', None)]
    result = {}
    for other in m.classes:
        if other is not cls:
            if cls.implies(other): 
                if other.doesNotImply(cls): result[other.name] = "properlyAbove"
                else: result[other.name] = "above"
            elif other.implies(cls):
                if cls.doesNotImply(other): result[other.name] = "properlyBelow"
                else: result[other.name] = "below"
            elif cls.doesNotImply(other) and other.doesNotImply(cls):
                result[other.name] = "incomparable"
            else: result[other.name] = "other"
    return jsonify(result)

@app.route('/_recolorPairSelected')
def recolorPairSelected():
    selectedClasses = request.args.get('selectedClass', None).split(",")
    A, B = m[selectedClasses[0]], m[selectedClasses[1]]
    result = {}
    for C in m.classes:
        if (A.implies(C) and (C).implies(B)) or (B.implies(C) and C.implies(A)):
            result[C.name] = "between"
        else:
            result[C.name] = "other"
    return jsonify(result)

@app.route('/_properties/<className>')
def properties(className):
    return render_template("properties.html", cls = m[className])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
