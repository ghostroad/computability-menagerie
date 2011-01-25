var nodes;
var showClassDetailsButton;
var showImplicationsButton;
var excludeSelectedButton;
var viewSubgraphButton;
var numSelected = 0;
var currentSizeColoring;
var currentColoring;
var CATEGORY_CLASSES = "countable uncountableMeager uncountableComeager uncountableUnknown unknownMeager unknownUnknown";
var MEASURE_CLASSES = "level0 level1 level2 level3 level4 level3-4 level2-3 level2-4 level1-2 level0-3 level1-4 level0-1 level0-2 level0-3 level0-4";
var RECOLORING_CLASSES = "above properlyAbove below properlyBelow incomparable other between";
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
    "coloringMap" : $CATEGORY,
    "handleSelect" : recolorIfAppropriate,
    "apply" : function() {
	window.location.hash = "category";
	currentColoring = CategoryMode;
	currentSizeColoring = CategoryMode;
	nodes.removeClass(MEASURE_CLASSES).addClass(function() {return $CATEGORY[this.id];});
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
    "coloringMap" : $MEASURE,
    "handleSelect" : recolorIfAppropriate,
    "apply" : function() {
	window.location.hash = "measure";
	currentColoring = MeasureMode;
	currentSizeColoring = MeasureMode;
	nodes.removeClass(CATEGORY_CLASSES).addClass(function() {return $MEASURE[this.id];});
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
    },
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
    },

    "handleSelect" : function() {
	if (numSelected == 2) { PairSelectedMode.apply(); }
	else if (numSelected == 1) { SingleSelectedMode.apply(); }
	else {
	    nodes.removeClass(RECOLORING_CLASSES);
	    currentSizeColoring.apply();
	}
    },

    "handleSizeColoringToggle" : function() {
	currentSizeColoring.switchToOtherSizeModeSilently();
    }
};

$(document).ready(function(){
		      if (!window.Touch) hovertipInit();
  
		      $('#toggleHelp').click( function() { $('#help').toggle(); } );
		      $('#toggleKey').click( function() { $('#keys').toggle(); } );

		      nodes = $('g[class="node"]');
		     
		      showClassDetailsButton = $('#showClassDetails input')[0];
		      if (window.Touch) $('#showClassDetails').show();
		      showImplicationsButton = $('#showImplications')[0];
		      viewSubgraphButton = $('#viewSubgraph')[0];
		      excludeSelectedButton = $('#excludeSelected')[0];

		      disableButtonsIfAppropriate();
		      detectCurrentColoring();

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
    viewSubgraphButton.disabled = (numSelected < 2);
    showImplicationsButton.disabled = (numSelected != 2);
    showClassDetailsButton.disabled = (numSelected != 1);
    excludeSelectedButton.disabled = (numSelected == 0 || (nodes.length - numSelected) < 2);
}

function excludeSelected() {
    var unselected = [];
    nodes.each(function() { if (!this.selected) unselected.push(this.id); });
    window.location = $SCRIPT_ROOT + '?classes=' + unselected.join();
}

function showClassDetails(node) {
    window.open($SCRIPT_ROOT + '/showClassDetails/' + node);
}

function showClassDetailsClicked() {
    nodes.each( function() {
		     if (this.selected) showClassDetails(this.id);
		} );
}

function showImplications() {
    var url = $SCRIPT_ROOT + '/showImplications';
    nodes.each(function(i, node) {
		   if (node.selected) url += '/'+node.id;
	       });
    window.open(url);
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
