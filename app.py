from flask import Flask, jsonify, request, render_template, make_response
from menagerie2 import *
from apputils import *
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


@app.route('/_recolor')
def recolor():
    selectedClasses = [m[className] for className in request.args.get('selectedClasses', None).split(",")]
    remaining = set(m.classes).difference(selectedClasses)
    result = {}
    for other in remaining:
        color = "inc"
        above = below = possiblyAbove = possiblyBelow = comparable = possiblyComparable = True
        for selected in selectedClasses:
            above = above and selected.implies(other)
            below = below and other.implies(selected)
            possiblyAbove = possiblyAbove and not selected.doesNotImply(other)
            possiblyBelow = possiblyBelow and not other.doesNotImply(selected)
            comparable = comparable and (selected.implies(other) or other.implies(selected))
            possiblyComparable = possiblyComparable and not selected.incomparableTo(other)
        if possiblyComparable:
            if above:
                if possiblyBelow: color = "eqAbove"
                else: color = "above"
            elif below:
                if possiblyAbove: color = "eqAbove"
                else: color = "below"
            elif possiblyAbove:
                if possiblyBelow:
                    color = comparable and "eqComp" or "eqInc"
                else:
                    color = comparable and "aboveComp" or "aboveInc"
            elif possiblyBelow:
                color = comparable and "belowComp" or "belowInc"
            else:
                color = comparable and "comp" or "compInc"
        result[other.name] = color
    return jsonify(result)
            
@app.route('/_properties/<className>')
def properties(className):
    return render_template("properties.html", cls = m[className])

@app.template_filter('decorate')
def decorate(cls):
    return classDecorator.decorate(cls)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
