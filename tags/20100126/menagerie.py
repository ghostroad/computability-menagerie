#! /usr/bin/env python

#
# The Menagerie Generator
# Joe Miller (started in 2008)
# Inspired by Bjoern Kjos-Hanssen's diagram of downward closed classes of Turing degrees (2002-2003)
#

# To change (maybe):
# (1) stop accepting facts without justification (or print louder warnings?)
# (2) parse class labels (for one thing, filtering doesn't work with labels)
# (3) more filtering options
# 		(a) all comperable to a given class (or list of classes)
#		(b) highlight filtered class(es)
#		(c) class lists defied in the database
#		(d) boolean combinations of defined class lists
# (4) merge equivalent classes automatically (so the diagram is always acyclic)
# (5) make the menagerie a proper data type (class)
# (6) parse once and query lots of times

# Notes:
#	* Uses pyparsing (a non-standard module)
# 	* Non-acyclic graphs are output with a pink background and
#		open implications are not displayed. Also, removal of
#		redundant edges is less rigorous
#	* Inconsistencies in the database also result in a pink
#		background and a warning

#	* An open implication is "weak" if it would imply no other
#		open implication using transitivity and known implications
#		(i.e., implied by no other open non-impication)
#		* Good to make them non-implications
#		* Displayed in dotted red

#	* An open implication is "strong" if no other open implication
#		would imply it using transitivity and known implications
#		* Good to make them implications
#		* Displayed in dotted green

import sys

Date = 'August 10, 2010'
Version = '0.2'

Error = False
def warning(s):
	global Error
	Error = True
	sys.stderr.write('%s \n' % s)

def error(s):	# Just quit
	sys.stderr.write('%s \n' % s)
	quit()

#
# The menagerie data
#

C = []		# classes
# I and P values have the format [0] or [state, desc, just, weight], where
#		state		either 1 or -1 (or sometimes 2)
#		desc		a printable description of state
#		just		a TeX string containing the justification of the state
#		weight		the weight of the current justification
I = []		# implications (and non-implicatios)
P = []		# size array (cardinality, category, packing dimension, Hausdorff dimension, measure)

# Ensure that a class is in our list (return index)
def ensure(a):
	if a in C: return C.index(a)
	C.append(a)
	for r in I: r.append([0])
	I.append([[0]]*len(C))
	I[-1][-1] = [2, printI(-1,-1,1), 'Reflexivity of implication', 1]	# set diagonal entries to 2
	P.append([[0]]*5)
	return len(C)-1

# Print an I value
def printI(i,j,k=0):
	if k==0: k = I[i][j]
	return C[i] + {-1:' -/> ', 1:' -> '}[k] + C[j]

# Print a P value
def printP(n,i,k=0):
	if k==0: k = P[n][i]
	if i < 2: return C[n] + ' is ' + { (0,-1):'countable', (0,1):'uncountable', (1,-1):'meager', (1,1):'comeager' }[(i,k)]
	else: return { 2:'PD', 3:'HD', 4:'M' }[i] + '(' + C[n] + ') = ' + str((k+1)/2)

# Derive justification and weight
#		input:		1 or 2 values of I or P
#		output:		[just, weight]
def Jst(*args):
	assert len(args) in (1,2)
	def wrap(v):
		s = '\\begin{fact}{' + v[1] + '}\n'
		if v[2]!="": s += v[2] + '\n'	# empty justifications are suppressed
		return s + '\\end{fact}' 
	if len(args) == 1: return [wrap(args[0]), 1+args[0][3]]
	else: return [wrap(args[0])+'\n'+wrap(args[1]), 1+args[0][3]+args[1][3]]

# Set I while checking consistency and keeping lightest justification
def setI(i,j,k,jst):
	if k*I[i][j][0] < 0: warning('Inconsistency detected: ' + printI(i,j,k))	### print more?
	elif I[i][j][0] == 0: I[i][j] = [k, printI(i,j,k)] + jst
	elif I[i][j][3] > jst[1]: I[i][j][2:4] = jst

# Set P while checking consistency and keeping lightest justification
def setP(n,i,k,jst):
	if k*P[n][i][0] < 0: warning('Inconsistency detected: ' + printP(n,i,k))	### print more?
	elif P[n][i][0] == 0: P[n][i] = [k, printP(n,i,k)] + jst
	elif P[n][i][3] > jst[1]: P[n][i][2:4] = jst

#
# Step 0: Get options
#

from optparse import OptionParser, OptionGroup

parser = OptionParser('Usage: %prog [options] database', version='%prog ' + Version + ' (' + Date + ')')

parser.set_defaults(open=(True,False),plain=False)
parser.add_option('-l', '--labels', dest='file',
	help='incude a file in the output; intended for node labels')
parser.add_option('-c', '--classes', dest='class_string', metavar='CLASSES',
	help='resrict to the subgraph containing the classes in the string CLASSES')
parser.add_option('-p', '--plain', action='store_true', dest='plain',
	help='do not use class properties to determine node style')
parser.add_option('-w', '--weak', action='store_const', const=(True,False), dest='open',
	help='display only the weakest open implications (default)')
parser.add_option('-s', '--strong', action='store_const', const=(False,True), dest='open',
	help='display only the strongest open implications')
parser.add_option('-b', '--both', action='store_const', const=(True,True), dest='open',
	help='display both the weakest and strongest open implications')
parser.add_option('-n', '--neither', action='store_const', const=(False,False), dest='open',
	help='display no open implications')
parser.add_option('-j', '--justify', dest='justify', metavar='CLASS | "CLASS_1 CLASS_2"',
	help='justify the properties of CLASS or the relationship between CLASS_1 and CLASS_2; do not output a .dot file')

(options, args) = parser.parse_args()
if len(args)>1: parser.error('too many arguments')
if len(args)<1: parser.error('no database file specified')
import os
Database = args[0]
if not os.path.exists(Database):
	parser.error('database file "' + Database + '" does not exist')
Weak, Strong = options.open
Plain = options.plain
Labels = options.file
if Labels:
	Labels = options.file
	if not os.path.exists(Labels):
		parser.error('label file "' + Labels + '" does not exist')
Classes = options.class_string
if Classes: Classes = Classes.split()
Justify = options.justify
if Justify:
	Justify = Justify.split()
	if len(Justify) not in (1,2): parser.error('invalid justification request')

#
# Step 1a: Get data
#

# Implications
def Imp(a,op,b,jst1,jst2=''):
	i, j = ensure(a), ensure(b)
	if op=='->' or op=='->>':
		if i!=j: setI(i,j,1,[jst1,1])	# ignore self-implications
	if op=='-/>': setI(i,j,-1,[jst1,1])
	if op=='->>': setI(j,i,-1,[jst2,1])

# Cardinality and Category
def Prop(a,b,jst):
	j, k = { 'countable':(0,-1), 'uncountable':(0,1), 'meager':(1,-1), 'comeager':(1,1) }[b]
	setP(ensure(a),j,k,[jst,1])

# Measure and Dimension
def Meas(m,a,b,jst):
	i = { 'PD':2, 'HD':3, 'M':4 }[m]
	setP(ensure(a),i,2*int(b)-1,[jst,1])

Fs = 0	# facts ("a ->> b" counts as two)
Js = 0	# justifications
# Silly helper functions (there must be a better way)
def incFs(): global Fs; Fs += 1
def incJs(): global Js; Js += 1

########################
########################
#
# File Format:
#
# Comment: # As you might expect
# Semicolons are optional
#
# Inclusion: a -> b ["justify"]
# Non-inclusion: a -/> b ["justify"]
# Strict inclusion: a ->> b ["justify implication" ["justify strictness"]]
# Cardinality, Category: a [is] countable ["justify"] (or uncountable, comeager, meager)
# Packing dimension, Hausdorff dimension, Measure: PD(a) = 0 ["justify"] (or HD, M; or 1)
#
# Justification is preferably LaTeX: "No $\Delta^0_2$ set is 2-random"
# Use an empty justification string (i.e., "") for things that should be obvious
#
########################
########################

from pyparsing import *

comment = Literal( "#" ) + SkipTo( LineEnd() )
name = Word( alphas+"_", alphanums+"_" )
justification = Optional( quotedString.setParseAction( removeQuotes, incJs ) , "UNJUSTIFIED" ).setParseAction( incFs )
impOp = Literal( "-/>" ) | Literal( "->" )
implication = ( name + impOp + name + justification ).setParseAction(lambda s,l,t: Imp(t[0],t[1],t[2],t[3]))
strictimp = ( name + Literal( "->>" ) + name + justification + justification ).setParseAction(lambda s,l,t: Imp(t[0],t[1],t[2],t[3],t[4]))
prop = Literal( "meager" ) | Literal( "comeager" ) | Literal( "countable" ) | Literal( "uncountable" )
setprop = ( name + Optional( Literal( "is" ).suppress() ) + prop + justification ).setParseAction(lambda s,l,t: Prop(t[0],t[1],t[2]))
meas = Literal( "M" ) | Literal( "HD" ) | Literal( "PD" )
bit = Literal( "0" ) | Literal( "1" )
reckoning = ( meas + Literal( "(" ).suppress() + name + Literal( ")" ).suppress() + Literal( "=" ).suppress() + bit + justification ).setParseAction(lambda s,l,t: Meas(t[0],t[1],t[2],t[3]))
database = ZeroOrMore( implication | strictimp | setprop | reckoning | Literal( ";" ) | comment ) + StringEnd()

database.parseFile(Database)

########################
########################

n = len(C)

#
# Step 1b: Print short summary of data
#

#sys.stderr.write('Database file: %s \n' % Database)
sys.stderr.write('%d Classes\n' % n)
sys.stderr.write('%d Facts\n' % Fs)
sys.stderr.write('%d Unjustified Facts\n' % (Fs-Js))

#
# Step 2: Close under size property implications
#

for i in range(n):
	if P[i][0][0]==-1:			# Countable
		jst = Jst(P[i][0])
		setP(i,1,-1,jst); setP(i,2,-1,jst); setP(i,3,-1,jst); setP(i,4,-1,jst)
	elif P[i][2][0]==-1:		# Packing Dim = 0
		jst = Jst(P[i][2])
		setP(i,1,-1,jst); setP(i,3,-1,jst); setP(i,4,-1,jst)
	elif P[i][3][0]==-1:		# Hausdorff Dim = 0
		jst = Jst(P[i][3])
		setP(i,4,-1,jst)
	elif P[i][4][0]==1:			# Measure = 1
		jst = Jst(P[i][4])
		setP(i,3,1,jst); setP(i,2,1,jst); setP(i,0,1,jst);
	if P[i][3][0]==1:			# Hausdorff Dim = 1
		jst = Jst(P[i][3])
		setP(i,2,1,jst); setP(i,0,1,jst)
	elif P[i][1][0]==1:			# Comeager
		jst = Jst(P[i][1])
		setP(i,2,1,jst); setP(i,0,1,jst)
	elif P[i][2][0]==1:			# Packing Dim = 1
		jst = Jst(P[i][2])
		setP(i,0,1,jst)

#
# Step 3: Run transitive closure algorithm on the implications
#		Note: also detect if the graph is not acyclic

Acyclic = True

# Run Floyd-Warshall
for k in range(n):
	for i in range(n):
		for j in range(n):
			if I[i][k][0]==1 and I[k][j][0]==1:
				if i==j: Acyclic = False
				else: setI(i,j,1,Jst(I[i][k],I[k][j]))

if not Acyclic:
	Weak = Strong = False	# Don't bother with nonimplications if the graph is not acyclic
	warning('Warning: the implication graph is not acyclic. Make it so!')

#
# Step 4: Use implications to infer size properties
#

from copy import deepcopy
Ptemp = deepcopy(P)
for i in range(n):
	for j in range(n):
		if I[i][j][0]==1:
			for k in range(5):
				if Ptemp[i][k][0]==1: setP(j,k,1,Jst(P[i][k],I[i][j]))
				if Ptemp[j][k][0]==-1: setP(i,k,-1,Jst(P[j][k],I[i][j]))

# Note: no further need for consistency checking after this.
# However, we still use setP and setI because they minimize justifications

#
# Step 5: Use size properties to infer additional non-implications
#

if Weak or Strong:
	for i in range(n):
		for j in range(n):
			if I[i][j][0]==0:	# Before step 5, all non-implications have justification weight 1
				for k in range(5):
					if P[i][k][0]==1 and P[j][k][0]==-1:
						setI(i,j,-1,Jst(P[i][k],P[j][k]))
						# Want to try all possibilities to minimize justifications, hence no "break" command here

#
# Step 6: Infer non-implications from transitivity of implication
#

if Weak or Strong:
	# Much like Floyd-Warshall
	for k in range(n):
		for i in range(n):
			for j in range(n):
				if I[j][k][0]==1 and I[i][k][0]==-1: setI(i,j,-1,Jst(I[j][k],I[i][k]))
				if I[k][i][0]==1 and I[k][j][0]==-1: setI(i,j,-1,Jst(I[k][i],I[k][j]))

#
# Step 7a: Output justification if that is what is requested 
#

if Justify:
	print """\\documentclass{amsart}

\\makeatletter
\\newenvironment{fact}[1]
{
	\\setlength{\\parindent}{0cm}
	{\\tt #1}
	
	\\setlength{\\leftmargin}{1cm}
	\\advance\\linewidth -\\leftmargin
	\\advance\\@totalleftmargin\\leftmargin
	\\@setpar{{\\@@par}}
	\\parshape 1 \\@totalleftmargin \\linewidth
	\\ignorespaces
}
{\\par}
\\makeatother

\\begin{document}
"""
	jst = []
	for c in Justify: # check if the classes are real
		if c not in C: error('Error: ' + c + ' is not the name of a class')
	i = C.index(Justify[0])
	if len(Justify) == 1:
		for k in range(5):
			if P[i][k][0]: jst.append(Jst(P[i][k])[0])
	else:
		j = C.index(Justify[1])
		if I[i][j][0]: jst.append(Jst(I[i][j])[0])
		if I[j][i][0]: jst.append(Jst(I[j][i])[0])
	if len(jst): print jst[0]
	for s in jst[1:]:
		print '\n\\bigskip\\hrule\\bigskip\n'
		print s
	print '\n\\end{document}'
	quit()

#
# Step 7b: Extract a subgraph
#

if Classes:
	N = []
	Ptemp = []
	Ctemp = []
	
	for c in Classes:
		if c in C:
			i = C.index(c)
			N.append(i)
			Ctemp.append(c)
			Ptemp.append(P[i])
		else: warning('Warning: ' + c + ' is not the name of a class')
	m = len(N)
	
	Itemp = [[0]*m for i in range(m)]
	for i in range(m):
		for j in range(m):
			Itemp[i][j] = I[N[i]][N[j]]
	
	I, P, C, n = Itemp, Ptemp, Ctemp, m

#
# Step 8: Find the weak and/or strong open implications
#

if Weak or Strong:
	W = []
	S = []

	for i in range(n):
		for j in range(n):
			if I[i][j][0]==0:
				if Weak:
					for k in range(n):
						if k!=i and k!=j:	# should be redundent
							if I[k][i][0]==1 and I[k][j][0]==0: break
							if I[j][k][0]==1 and I[i][k][0]==0: break
					else: W.append((i,j))
				if Strong:
					for k in range(n):
						if k!=i and k!=j:	# should be redundent
							if I[i][k][0]==1 and I[k][j][0]==0: break
							if I[i][k][0]==0 and I[k][j][0]==1: break
					else: S.append((i,j))

#
# Step 9: Mark redundant implications (with 2)
#		Note: leaves a lot of extra edges if the graph is not acyclic (but who cares)
#

for i in range(n):
	for j in range(n):
		if I[i][j][0]==1:
			for k in range(n):
				if I[k][i][0]>0 or I[j][k][0]>0: continue		# handle non-acyclic graphs somewhat gracefully
				if I[i][k][0]==1 and k!=j and I[k][j][0]>0:
					I[i][j][0] = 2
					break

#
# Step 10: Output the .dot file
#

# Determine node style based on size properties
#		meager: ellipse, comeager: box
#		M=1: blue, else HD=1: green, else PD=1: cyan, else grey
#		countable: no border, uncountable: black border
#		any red denotes some sort of ignorance
def Style(P):
	# Category and Cardinality
	if P[1][0]==-1:
		s = 'shape = ellipse, style = filled, color = '
		s = s + {-1:'grey', 0:'red', 1:'black'}[P[0][0]]
	elif P[1][0]==0:
		s = 'shape = box, color = red, style = '
		s = s + {-1: '""', 0:'"filled, dashed"', 1:'filled'}[P[0][0]]
	else: s = 'shape = box, style = filled'

	# Measure and Dimension
	u = k = 0
	for i in range(2,5):
		if P[i][0]==0: u = u + 1
		if P[i][0]==1: k = k + 1
	s = s + ', fillcolor = "#' + ['CCCCCC','00FF00','00FFFF','0000FF'][k] + '"'
	if u>0: s = s + ', fontcolor = red'
	return s

print """//
// Generated by the Menagerie Generator
//

digraph G {

graph [
	rankdir = BT		// put smaller classes lower down"""

if Error: print "\tbgcolor = pink"

print ']'

if Labels:
	print
	f = open(Labels)
	for line in f: print line,
	f.close()
	print

if not Plain:
	print """
//
// Node Styles
//
"""
	for i in range(n):
		print C[i], '[', Style(P[i]), ']'

print """
//
// Inclusions
//
"""

for i in range(n):
	for j in range(n):
		if I[i][j][0]==1: print C[i], '->', C[j]

if Weak or Strong:
	print """
//
// Open Questions
//"""

if Weak:
	print """
edge [
	color = red, style = dashed
#	constraint = false
]
"""
	# Note: working a litte hard here because having unconstrained
	#		edges in both directions sometimes causes dot to crash?
	for i, j in W:
		if (j,i) in W:
			if i<j: print C[i], '->', C[j], '[dir = both]'
		else: print C[i], '->', C[j]

if Strong:
	print """
edge [
	color = green, style = dashed
#	constraint = false
]
"""
	# Note: working a litte hard here because having unconstrained
	#		edges in both directions sometimes causes dot to crash?
	for i, j in S:
		if (j,i) in S:
			if i<j: print C[i], '->', C[j], '[dir = both]'
		else: print C[i], '->', C[j]

print '\n}'

#
# The End
#