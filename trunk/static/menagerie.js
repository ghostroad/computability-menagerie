var nodes;
var showProofsButton;
var weakArrows;
var excludeSelectedButton;
var numSelectedLink;
var viewSubgraphButton;
var excludedClassesDiv;
var selectedClassesDiv;
var numSelected = 0;
var currentSizeColoring;
var currentColoring;
var CATEGORY_CLASSES = "countable uncountableMeager uncountableComeager uncountableUnknown unknownMeager unknownUnknown";
var MEASURE_CLASSES = "level0 level1 level2 level3 level4 level3-4 level2-3 level2-4 level1-2 level0-3 level1-4 level0-1 level0-2 level0-3 level0-4";
var RECOLORING_CLASSES = "above eqAbove below eqBelow inc aboveInc belowInc eqInc notBetw betw possiblyBetw";

function getSelectedClasses() {
    var selected = [];
    nodes.each(function() {
	       if (this.selected) selected.push(this.id);
	       });
    return selected.join();
}

function recolorIfAppropriate() {
    if (numSelected == 1) SingleSelectedMode.apply();
    else if (numSelected == 2) PairSelectedMode.apply();
}

function activateKey(keyId) {
    $('#keys .key').hide();
    $(keyId).show();
}

var CategoryMode = {
    "handleSelect" : recolorIfAppropriate,
    "apply" : function() {
	window.location.hash = "category";
	currentColoring = CategoryMode;
	currentSizeColoring = CategoryMode;
	nodes.removeClass(MEASURE_CLASSES).addClass(function() {return $PROPERTIES[this.id][0];});
	activateKey('#categoryKey');
    },
    "switchToOtherSizeModeSilently" : function() {
	window.location.hash = "measure";	
	currentSizeColoring = MeasureMode;
    },
    "handleSizeColoringToggle" : function() {
	MeasureMode.apply();
    }
};

var MeasureMode = {
    "handleSelect" : recolorIfAppropriate,
    "apply" : function() {
	window.location.hash = "measure";
	currentColoring = MeasureMode;
	currentSizeColoring = MeasureMode;
	nodes.removeClass(CATEGORY_CLASSES).addClass(function() {return $PROPERTIES[this.id][1];});
	activateKey('#measureKey');
    },
    "switchToOtherSizeModeSilently" : function() {
	window.location.hash = "category";	
	currentSizeColoring = CategoryMode;
    },
    "handleSizeColoringToggle" : function() {
	CategoryMode.apply();
    }
};

var RecoloringMode = {
    "handleSelect" : function() {
	if (numSelected == 1) { SingleSelectedMode.apply(); }
	else if (numSelected == 2) { PairSelectedMode.apply(); }
	else {
	    nodes.removeClass(RECOLORING_CLASSES);
	    currentSizeColoring.apply();
	}
    },

    "handleSizeColoringToggle" : function() {
	currentSizeColoring.switchToOtherSizeModeSilently();
    }
};

var SingleSelectedMode = {
    "apply" : function() {
	$.getJSON($SCRIPT_ROOT + '/_recolorSingleSelected', { selectedClass: getSelectedClasses() }, 
		  function(data) {
		      if (numSelected == 1) {
			  nodes.removeClass(RECOLORING_CLASSES).addClass(function() { return data[this.id]; });
			  currentColoring = SingleSelectedMode;
			  activateKey('#singleRecoloringKey');
		      }
		  }
		 );
    }
};

$.extend(SingleSelectedMode, RecoloringMode);

var PairSelectedMode = {
    "apply" : function() {
	$.getJSON($SCRIPT_ROOT + '/_recolorPairSelected', { selectedClass: getSelectedClasses() }, 
		  function(data) {
		      if (numSelected == 2) {
			  nodes.removeClass(RECOLORING_CLASSES).addClass(function() { return data[this.id]; });
			  currentColoring = PairSelectedMode;
			  activateKey('#pairRecoloringKey');
		      }
		  }
		 );
    }
};

$.extend(PairSelectedMode, RecoloringMode);

function showExcludedClasses() {
    excludedClassesDiv.showing = window.setTimeout(function() {
						       excludedClassesDiv.show();
						   }, 300);
}

function showSelectedClasses() {
    selectedClassesDiv.showing = window.setTimeout(function() {
						       selectedClassesDiv
							   .html(function() {
								     var items = [];
								     nodes.each(function() {
										    if (this.selected) items.push('<li>' + $PROPERTIES[this.id][2] + '</li>');
										});
								     items.sort();
								     return '<ul>' + items.join("") + "</ul>";
								 }).show();
						   }, 300);
}

function postponeHidingDiv(div) {
    if (div.hiding) {
	window.clearTimeout(div.hiding);
	div.hiding = null;
    }
}

function hideDiv(div) {
    if (div.showing) {
	window.clearTimeout(div.showing);
	div.showing = null;
    }
    div.hiding = window.setTimeout(function() {
				       div.hide();
				   }, 300);
}

function toggleWeakArrowHighlight() {
    if (weakArrows.highlighted) {
	weakArrows.removeClass("highlightArrow");
	weakArrows.highlighted = false;
    }
    else {
	weakArrows.addClass("highlightArrow");
	weakArrows.highlighted = true;
    }
}

$(document).ready(function(){
		      if (!window.Touch) hovertipInit();

		      nodes = $('g[class="node"]');
		      weakArrows = $('g[id|="weak"]');

		      $('#toggleHelp').click( function() { $('#help').toggle(); } );
		      $('#toggleKey').click( function() { $('#keys').toggle(); } );
		      showProofsButton = $('#showProofs').click(showProofs);
		      viewSubgraphButton = $('#viewSubgraph').click(viewSubgraph);
		      excludeSelectedButton = $('#excludeSelected').click(excludeSelected);

		      excludedClassesDiv = $('#excludedClasses');
		      $('#excludedClassesLink').hover(showExcludedClasses, function() { hideDiv(excludedClassesDiv); });
		      excludedClassesDiv.hover(function() { postponeHidingDiv(excludedClassesDiv); }, 
					       function() { hideDiv(excludedClassesDiv);});		      
		      selectedClassesDiv = $('#selectedClasses');
		      numSelectedLink = $('#numSelectedLink');
		      numSelectedLink.hover(showSelectedClasses, function() {hideDiv(selectedClassesDiv); });
		      selectedClassesDiv.hover(function() { postponeHidingDiv(selectedClassesDiv); }, 
					       function() { hideDiv(selectedClassesDiv);});		      

		      disableButtonsIfAppropriate();
		      detectCurrentColoring();
		      toggleWeakArrowHighlight();

		      nodes.each(function(i, node) {
				     node.selected = false; 
				     node.toggleSelected = function() {
					 if (!this.selected) {
					     $(this).addClass('selected');
					     this.selected = true;
					     numSelected++;
					 } else {
					     $(this).removeClass('selected');
					     this.selected = false;
					     numSelected--;
					 }
					 $('#numSelected').text(numSelected);
	
					 disableButtonsIfAppropriate();
				     };
				     node.addEventListener("click", function(evt) { 
							       evt.target.parentNode.toggleSelected(); currentColoring.handleSelect(); }, true);
				     node.addEventListener("dblclick", function(evt) { showClassDetails(evt.target.parentNode.id); }, true);
				 });
		  });

function detectCurrentColoring() {
    var hash = window.location.hash;
    if (hash == "#measure") {
	$('#coloringModeSelector')[0].value = 'measure';
	MeasureMode.apply();
    } else {
	$('#coloringModeSelector')[0].value = 'category';
	CategoryMode.apply();
    }
}

function disableButtonsIfAppropriate() {
    enable(numSelected > 1, viewSubgraphButton, viewSubgraph); 
    enable(numSelected == 2 || numSelected == 1, showProofsButton, showProofs);
    enable(numSelected > 0 && numSelected <= nodes.length - 2, excludeSelectedButton, excludeSelected);
    enable(numSelected > 0, numSelectedLink, function() { });
}

function enable(condition, anchor, action) {
    if (condition) { 
	anchor.removeClass("disabled");    
    } else {
	anchor.addClass("disabled");
    }
}

function excludeSelected() {
    var unselected = [];
    nodes.each(function() { if (!this.selected) unselected.push(this.id); });
    window.location = $SCRIPT_ROOT + '?classes=' + unselected.join();
}

function showProofs() {
    var url = $SCRIPT_ROOT + '/showProofs';
    nodes.each(function(i, node) {
		   if (node.selected) url += '/'+node.id;
	       });
    window.open(url);
}

function showClassDetails(nodeId) {
    window.open($SCRIPT_ROOT + '/showProofs/' + nodeId);
}

function viewSubgraph() {
    var url = $SCRIPT_ROOT + '?classes=' + getSelectedClasses();
    window.location = url;
}

function unselectAll() {
    nodes.each(function(i, node) {
		   if (node.selected) { node.toggleSelected(); }
	       }); 
    currentColoring.handleSelect();
}
