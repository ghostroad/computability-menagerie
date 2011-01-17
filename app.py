from flask import Flask, jsonify, request, render_template, make_response
from menagerie2 import *
from svgutils import *

m = Menagerie()
parser = MenagerieParser(m)
parser.readFromFile("database.txt")
Deductions().apply(m)


app = Flask(__name__)



@app.route('/')
def displayMenagerie():
    classes = request.args.get("classes", None)
    g = DotRenderer(m).render(showOnly = classes and classes.split(","), displayLongNames=True, showWeakOpenImplications = True, showStrongOpenImplications = True)
    processedSvg = SVGPostProcessor().process(g)
    response = make_response(render_template("menagerie.html", graph = processedSvg.toxml()))
    response.headers["Content-Type"] = "application/xhtml+xml"
    return response

@app.route('/properties')
def showProperties():
    className = request.args.get("className", None)
    cls = m[className]
    return render_template("properties.html", cls = cls)

@app.route('/showClassDetails/<className>')
def showClassDetails(className):
    cls = m[className]
    properties = {}
    for attr in CLASS_ATTRIBUTES:
        prop = getattr(cls, attr)
        out = HtmlWriter()
        prop.write(out)
        properties[attr] = out
    return render_template("classDetail.html", **properties)

@app.route('/showImplications/<classA>/<classB>')
def showImplications(classA, classB):
    A = m[classA]
    B = m[classB]
    implications = [];
    forwardImplication = A.implies(B) or A.doesNotImply(B)
    backwardImplication = B.implies(A) or B.doesNotImply(A)
    if forwardImplication:
        out = HtmlWriter()
        forwardImplication.write(out)
        implications.append(out)
    if backwardImplication:
        out = HtmlWriter()
        backwardImplication.write(out)
        implications.append(out)
    return render_template("implications.html", implications=implications)


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
