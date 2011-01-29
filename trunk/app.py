from flask import Flask, jsonify, request, render_template, make_response
from menagerie2 import *
from apputils import *
from time import sleep
from os import getenv

m = Menagerie()
parser = MenagerieParser(m)
parser.readFromFile(getenv("MENAGERIE_DATABASE_FILE") or "database.txt")
Deductions().apply(m)
propertiesMap = Coloring(m).buildPropertiesMap()

app = Flask(__name__)

@app.route('/')
def displayMenagerie():
    classesParam = request.args.get("classes", None)
    classes = classesParam and [m[clsName] for clsName in classesParam.split(",")] or m.classes
    excludedClasses = sorted(set(m.classes).difference(classes), cmp = lambda x, y: cmp(x.displayName(), y.displayName()))
    g = DotRenderer(m, classes).render(displayLongNames=True)
    processedSvg = SVGPostProcessor().process(g)
    
    response = make_response(render_template("menagerie.html", graph = processedSvg, propertiesMap = propertiesMap, excludedClasses = excludedClasses))
    response.headers["Content-Type"] = "application/xhtml+xml"
    return response

@app.route('/showProofs/<className>')
def showClassDetails(className):
    cls = m[className]
    properties = {"cls" : cls}
    for attr in CLASS_ATTRIBUTES:
        prop = getattr(cls, attr)
        properties[attr] = HtmlWriter().write(prop)
    return render_template("classDetail.html", **properties)

@app.route('/showProofs/<classA>/<classB>')
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
                if other.doesNotImply(cls): result[other.name] = "above"
                else: result[other.name] = "eqAbove"
            elif cls.doesNotImply(other): 
                if other.implies(cls): result[other.name] = "below"
                elif other.doesNotImply(cls): result[other.name] = "inc"
                else: result[other.name] = "belowInc"
            else:
                if other.implies(cls): result[other.name] = "eqBelow"
                elif other.doesNotImply(cls): result[other.name] = "aboveInc"
                else: result[other.name] = "eqInc"
    return jsonify(result)

@app.route('/_recolorPairSelected')
def recolorPairSelected():
    selectedClasses = request.args.get('selectedClass', None).split(",")
    A, B = m[selectedClasses[0]], m[selectedClasses[1]]
    if A.implies(B): return jsonify(buildMap(m, A, B))
    elif A.doesNotImply(B):
        if B.doesNotImply(A):
            return jsonify(dict((cls.name, "notBetw") for cls in m.classes))
        else: return jsonify(buildMap(m, B, A))
    else:
        if B.doesNotImply(A): return jsonify(buildMap(m, A, B))
        elif B.implies(A): return jsonify(buildMap(m, A, B))
        else:
            result = {}
            for C in m.classes:
                if C.incomparableTo(A) or C.incomparableTo(B) or (C.doesNotImply(A) and C.doesNotImply(B)) or (A.doesNotImply(C) and B.doesNotImply(C)): result[C.name] = "notBetw"
                else: result[C.name] = "possiblyBetw"
            return jsonify(result)

@app.route('/_properties/<className>')
def properties(className):
    return render_template("properties.html", cls = m[className])

@app.template_filter('decorate')
def decorate(cls):
    return classDecorator.decorate(cls)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


    

