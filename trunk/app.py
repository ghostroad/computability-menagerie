from flask import Flask, request, render_template, make_response
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
    g = DotRenderer(m).render(showOnly = classes and classes.split(","), displayLongNames=True, showWeakOpenImplications = request.args.get("showWeakOpen", False), showStrongOpenImplications = request.args.get("showStrongOpen", False))
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
        if prop.known(): 
            out = HtmlWriter()
            prop.write(out)
            properties[attr] = out
        else:
            properties[attr] = "<ul><li> The {0} of <span class=\"className\">{1}</span> is not known.</li></ul>".format(prop.propertyName, cls.longName or cls.name) # fix this ugliness
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

if __name__ == '__main__':
    app.run(debug=True)
