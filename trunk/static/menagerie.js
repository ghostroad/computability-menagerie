var nodes;
var showClassDetailsButton;
var showImplicationsButton;
var viewSubgraphButton;
var numSelected = 0;
var currentSizeColoring;
var currentColoring;
var CATEGORY_CLASSES = "countable uncountableMeager uncountableComeager uncountableUnknown unknownMeager unknownUnknown";
var MEASURE_CLASSES = "level0 level1 level2 level3 level4 level3-4 level2-3 level2-4 level1-2 level0-3 level1-4 level0-1 level0-2 level0-3 level0-4";
var SINGLE_SELECTED_CLASSES = "above properlyAbove below properlyBelow incomparable other";
var PAIR_SELECTED_CLASSES = "between other";

function getSelectedClasses() {
    var selected = [];
    nodes.each(function() {
	       if (this.selected) selected.push(this.id);
	       });
    return selected;
}

function recolorIfAppropriate() {
    if (numSelected == 1) SingleSelectedMode.apply();
    else if (numSelected == 2) PairSelectedMode.apply();
}

var CategoryMode = {
    "coloringMap" : $CATEGORY,
    "handleSelect" : recolorIfAppropriate,
    "apply" : function() {
	window.location.hash = "category";
	currentColoring = CategoryMode;
	currentSizeColoring = CategoryMode;
	nodes.removeClass(MEASURE_CLASSES).addClass(function() {return $CATEGORY[this.id];});
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
	$.getJSON($SCRIPT_ROOT + '/_recolorSingleSelected', { selectedClass: '' + getSelectedClasses() }, 
		  function(data) {
		      if (numSelected == 1) {
			  nodes.removeClass(PAIR_SELECTED_CLASSES).addClass(function() { return data[this.id]; });
			  currentColoring = SingleSelectedMode;
		      }
		  }
		 );
    },
    "handleSelect" : function() {
	if (numSelected == 1) return;
	if (numSelected == 2) { PairSelectedMode.apply(); }
	else {
	    nodes.removeClass(SINGLE_SELECTED_CLASSES);
	    currentSizeColoring.apply();
	}
    },

    "handleSizeColoringToggle" : function() {
	currentSizeColoring.switchToOtherSizeModeSilently();
    }
};

var PairSelectedMode = {
    "apply" : function() {
	$.getJSON($SCRIPT_ROOT + '/_recolorPairSelected', { selectedClass: '' + getSelectedClasses() }, 
		  function(data) {
		      if (numSelected == 2) {
			  nodes.removeClass(SINGLE_SELECTED_CLASSES).addClass(function() { return data[this.id]; });
			  currentColoring = PairSelectedMode;
		      }
		  }
		 );
    },

    "handleSelect" : function() {
	if (numSelected == 2) return;
	if (numSelected == 1) { SingleSelectedMode.apply(); }
	else {
	    nodes.removeClass(PAIR_SELECTED_CLASSES);
	    currentSizeColoring.apply();
	}
    },

    "handleSizeColoringToggle" : function() {
	currentSizeColoring.switchToOtherSizeModeSilently();
    }
};

$(document).ready(function(){
		      if (!window.Touch) hovertipInit();
  
		      $('#toggleHelp').click( function() { $('#help').toggle(400); } );
		      $('#toggleKey').click( function() { $('#keys').toggle(400); } );

		      nodes = $('g[class="node"]');
		     
		      showClassDetailsButton = $('#showClassDetails input')[0];
		      if (window.Touch) $('#showClassDetails').show();
		      showImplicationsButton = $('#showImplications')[0];
		      viewSubgraphButton = $('#viewSubgraph')[0];

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
	MeasureMode.apply();
    } else {
	CategoryMode.apply();
    }
}

function disableButtonsIfAppropriate() {
      viewSubgraphButton.disabled = (numSelected < 2);
      showImplicationsButton.disabled = (numSelected != 2);
      showClassDetailsButton.disabled = (numSelected != 1);
}

function disableButtons() {
    showClassDetailsButton.disabled = true;
    showImplicationsButton.disabled = true;
    viewSubgraphButton.disabled = true;
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
    var selected = [];
    nodes.each(function(i, node) {
		   if (node.selected) { selected.push(node.id); };
	       });
    var url = $SCRIPT_ROOT + '?classes=' + selected;
    window.location = url;
}

function unselectAll() {
    nodes.each(function(i, node) {
		   if (node.selected) { node.toggleSelected(); }
	       }); 
    currentColoring.handleSelect();
}

function handleOpenImplicationPreferences() {
    var hash = window.location.hash;
    var showWeakOpen;
    var showStrongOpen;
    if (hash) {
	var split = hash.substring(1).split('-');
	showWeakOpen = split[0] == 'true';
	showStrongOpen = split[1] == 'true';
    }
    showWeakOpenCheckbox.checked = showWeakOpen;
    showStrongOpenCheckbox.checked = showStrongOpen;
    updateStrongOpen();
    updateWeakOpen();
}

