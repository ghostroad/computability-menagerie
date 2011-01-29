var settings = {
    "coloring" : "measure",
    "showOpen" : "false",
    "showKey"  : "false",
    "showHelp" : "false"
};

var nodes;
var showProofsButton;
var nonstrictArrows;
var openArrows;
var excludeSelectedButton;
var numSelectedLink;
var viewSubgraphButton;
var excludedClassesDiv;
var selectedClassesDiv;
var numSelected = 0;
var currentSizeColoring;
var currentColoring;
var restoreCheckedClassesButton;
var CATEGORY_CLASSES = "countable uncountableMeager uncountableComeager uncountableUnknown unknownMeager unknownUnknown";
var MEASURE_CLASSES = "level0 level1 level2 level3 level4 level3-4 level2-3 level2-4 level1-2 level0-3 level1-4 level0-1 level0-2 level0-3 level0-4";
var RECOLORING_CLASSES = "above eqAbove below eqBelow inc eqComp eqInc aboveComp aboveInc belowComp belowInc comp compInc";

function getSelectedClasses() {
    var selected = [];
    nodes.each(function() {
	       if (this.selected) selected.push(this.id);
	       });
    return selected.join();
}

function recolorIfAppropriate() {
    if (numSelected > 0) RecoloringMode.apply();
}

function activateKey(keyId) {
    $('#keys .key').hide();
    $(keyId).show();
}

var CategoryMode = {
    "handleSelect" : recolorIfAppropriate,
    "apply" : function() {
	updateHash("coloring", "category");
	currentColoring = CategoryMode;
	currentSizeColoring = CategoryMode;
	nodes.removeClass(MEASURE_CLASSES).addClass(function() {return $PROPERTIES[this.id][0];});
	activateKey('#categoryKey');
    },
    "switchToOtherSizeModeSilently" : function() {
	updateHash("coloring", "measure");
	currentSizeColoring = MeasureMode;
    },
    "handleSizeColoringToggle" : function() {
	MeasureMode.apply();
    }
};

var MeasureMode = {
    "handleSelect" : recolorIfAppropriate,
    "apply" : function() {
	updateHash("coloring", "measure");
	currentColoring = MeasureMode;
	currentSizeColoring = MeasureMode;
	nodes.removeClass(CATEGORY_CLASSES).addClass(function() {return $PROPERTIES[this.id][1];});
	activateKey('#measureKey');
    },
    "switchToOtherSizeModeSilently" : function() {
	updateHash("coloring", "category");
	currentSizeColoring = CategoryMode;
    },
    "handleSizeColoringToggle" : function() {
	CategoryMode.apply();
    }
};

var RecoloringMode = {
    "apply" : function() {
	var cacheSelected = getSelectedClasses();
	$.getJSON($SCRIPT_ROOT + '/_recolor', { selectedClasses: cacheSelected }, 
		  function(data) {
		      if (getSelectedClasses() == cacheSelected) {
			  nodes.removeClass(RECOLORING_CLASSES).addClass(function() { return data[this.id]; });
			  currentColoring = RecoloringMode;
			  activateKey('#recoloringKey');
		      }
		  }
		 );
    },

    "handleSelect" : function() {
	if (numSelected > 0) { RecoloringMode.apply(); }
	else {
	    nodes.removeClass(RECOLORING_CLASSES);
	    currentSizeColoring.apply();
	}
    },

    "handleSizeColoringToggle" : function() {
	currentSizeColoring.switchToOtherSizeModeSilently();
    }
};

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
				   }, 500);
}

function toggleNonstrictArrowHighlight() {
    if (nonstrictArrows.highlighted) {
	nonstrictArrows.removeClass("highlightArrow");
	nonstrictArrows.highlighted = false;
    }
    else {
	nonstrictArrows.addClass("highlightArrow");
	nonstrictArrows.highlighted = true;
    }
}

function toggleOpenImplications() {
    if (settings["showOpen"] == "false") {
	openArrows.show();
	updateHash("showOpen", "true");
    } else {
	openArrows.hide();
	updateHash("showOpen", "false");
    }
}

$(document).ready(function(){
		      if (!window.Touch) hovertipInit();

		      nodes = $('g[class="node"]');
		      nonstrictArrows = $('g[id|="nonstrict"]');
		      openArrows = $('g[id|="strong"],g[id|="weak"]'); 

		      $('#toggleHelp,#dismissHelp').click( function() { 
						  settings["showHelp"] == "true" ? 
						      updateHash("showHelp", "false") : updateHash("showHelp", "true");
						  $('#help').toggle();
					      });

		      $('#toggleKey').click( function() { 
						 settings["showKey"] == "true" ? 
						      updateHash("showKey", "false") : updateHash("showKey", "true");
						 $('#keys').toggle(); 
					      });

		      showProofsButton = $('#showProofs');
		      viewSubgraphButton = $('#viewSubgraph');
		      excludeSelectedButton = $('#excludeSelected');
		      restoreCheckedClassesButton = $('#restoreChecked');

		      excludedClassesDiv = $('#excludedClasses');
		      $('#excludedClassesLink').hover(showExcludedClasses, function() { hideDiv(excludedClassesDiv); });
		      excludedClassesDiv.hover(function() { postponeHidingDiv(excludedClassesDiv); },
					       function() { hideDiv(excludedClassesDiv);});	      

		      selectedClassesDiv = $('#selectedClasses');
		      numSelectedLink = $('#numSelectedLink');
		      numSelectedLink.hover(showSelectedClasses, function() {hideDiv(selectedClassesDiv); });
		      selectedClassesDiv.hover(function() { postponeHidingDiv(selectedClassesDiv); },
					       function() { hideDiv(selectedClassesDiv);});	      

		      readAndApplySettings();
		      toggleNonstrictArrowHighlight();

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

function readAndApplySettings() {
    var hash = window.location.hash;
    var keyValuePairs = hash ? hash.substring(1).split(",") : [];
    $(keyValuePairs).each(function() {
			      var pieces = this.split("=");
			      settings[pieces[0]] = pieces[1];
			  });
    if (settings["coloring"] == "category") {
	$('#coloringModeSelector').val("category");
	CategoryMode.apply(); 
    } else {
	$('#coloringModeSelector').val("measure");
	MeasureMode.apply();
    }
    if (settings["showOpen"] == "false") openArrows.hide();
    if (settings["showKey"] == "true") $('#keys').show();
    if (settings["showHelp"] == "true") $('#help').show();
}

function updateHash(key, value) {
    settings[key] = value;
    var result = [];
    for (var v in settings) {
	result.push(v + "=" + settings[v]);
    }
    window.location.hash = result.join();
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
    window.location = $SCRIPT_ROOT + '?classes=' + unselected.join() + window.location.hash;
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
    var url = $SCRIPT_ROOT + '?classes=' + getSelectedClasses() + window.location.hash;
    window.location = url;
}

function unselectAll() {
    nodes.each(function(i, node) {
		   if (node.selected) { node.toggleSelected(); }
	       }); 
    currentColoring.handleSelect();
}

function enableRestoreChecked() {
    var checkedBoxes = $('#excludedClasses :checkbox:checked');
    if (checkedBoxes.length > 0) restoreCheckedClassesButton.removeClass("disabled"); else restoreCheckedClassesButton.addClass("disabled");
}

function restoreChecked() {
    var classesToDisplay = [];
    $('#excludedClasses :checkbox:checked').each(function() {
						     classesToDisplay.push(this.value);
						 });
    nodes.each(function() {
		   classesToDisplay.push(this.id);
	       });
    var url = $SCRIPT_ROOT + '?classes=' + classesToDisplay + window.location.hash;
    window.location = url;
}

function restoreAll() {
    var url = $SCRIPT_ROOT + "/" + window.location.hash;
    window.location = url;
}