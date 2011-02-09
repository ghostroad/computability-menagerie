from flask import Flask, jsonify, request, render_template, make_response
from menagerie.core import DotRenderer, CLASS_ATTRIBUTES
from menagerie.webapp import app
from apputils import *
from os import getenv


class menagerieView(object):
    def __init__(self, f):
        self.f = f
        self.__name__ = f.__name__
    def __call__(self, *args, **kwargs):
        return self.f(app.config['menagerie'], *args, **kwargs)


@app.route('/')
@menagerieView
def displayMenagerie(m):
    classesParam = request.args.get("classes", "")
    showOpenImplications = request.args.get("showOpen", None) == "true"
    classes = classesParam and [m[clsName] for clsName in classesParam.split(",")] or m.classes
    excludedClasses = sorted(set(m.classes).difference(classes), cmp = lambda x, y: cmp(x.displayName(), y.displayName()))
    g = DotRenderer(m, classes, showOpenImplications).render()
    processedSvg = SVGPostProcessor().process(g)
    
    response = make_response(render_template("menagerie.html", graph = processedSvg, showOpen=showOpenImplications, propertiesMap = app.config['propertiesMap'], excludedClasses = excludedClasses, classesParam = classesParam, gatewayPage = app.config['gatewayPage']))
    response.headers["Content-Type"] = "application/xhtml+xml"
    return response

@app.route('/showProofs/<className>')
@menagerieView
def showClassDetails(m, className):
    cls = m[className]
    properties = {"cls" : cls}
    for attr in CLASS_ATTRIBUTES:
        prop = getattr(cls, attr)
        properties[attr] = HtmlWriter().write(prop)
    return render_template("classDetail.html", **properties)

@app.route('/showProofs/<classA>/<classB>')
@menagerieView
def showImplications(m, classA, classB):
    A = m[classA]
    B = m[classB]
    forwardImplication = A.implies(B) or A.doesNotImply(B) or UnknownImplication(A, B)
    backwardImplication = B.implies(A) or B.doesNotImply(A) or UnknownImplication(B, A)
    return render_template("implications.html", implications=[HtmlWriter().write(forwardImplication), 
                                                              HtmlWriter().write(backwardImplication)], clsA=A, clsB=B)

@app.route('/_recolor')
@menagerieView
def recolor(m):
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
                if possiblyAbove: color = "eqBelow"
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
@menagerieView
def properties(m, className):
    return render_template("properties.html", cls = m[className])

@app.template_filter('decorate')
def decorate(cls):
    return classDecorator.decorate(cls)

