var settings = {
    "coloring" : "measure",
    "showKey"  : "false",
    "showHelp" : "false"
};

var nodes;
var showProofsButton;
var nonstrictArrows;
var excludeSelectedButton;
var numSelectedLink;
var viewSubgraphButton;
var excludedClassesDiv;
var selectedClassesDiv;
var nodeDataDiv;
var numSelected = 0;
var currentSizeColoring;
var currentColoring;
var restoreCheckedClassesButton;

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
	nodes.removeClass(function() { return this.sizeColor; }).addClass(function() {
									      this.sizeColor = $PROPERTIES[this.id][0];
									      return this.sizeColor;
									  });
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
	nodes.removeClass(function() { return this.sizeColor;}).addClass(function() {
									     this.sizeColor = $PROPERTIES[this.id][1];
									     return this.sizeColor;
									 });
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
			  nodes.removeClass(function() {
						return this.recolor;})
			      .addClass(function() { 
					    this.recolor = data[this.id] || "";
					    return this.recolor;
					});
			  
			  currentColoring = RecoloringMode;
			  activateKey('#recoloringKey');
		      }
		  }
		 );
    },

    "handleSelect" : function() {
	if (numSelected > 0) { RecoloringMode.apply(); }
	else {
	    nodes.removeClass(function() {
				  var recolor = this.recolor;
				  this.recolor = "";
				  return recolor;
			      });
	    currentSizeColoring.apply();
	}
    },

    "handleSizeColoringToggle" : function() {
	currentSizeColoring.switchToOtherSizeModeSilently();
    }
};

function showNodeData(event) {
    var nodeId = event.target.parentNode.id;
    var viewportX = event.pageX - $(window).scrollLeft();
	var viewportY = event.pageY - $(window).scrollTop();
	var width = $(window).width();
	if ((viewportX < width - 200) || (viewportY > 200)) {
	    nodeDataDiv.css({
				    'bottom':'auto',
				    'left':'auto',
				    'top': '10px',
				    'right': '10px'});
	      } else {
		  nodeDataDiv.css({
				    'top' : 'auto',
				    'right' : 'auto',
				    'bottom': '10px',
				    'left': '10px'});
	      }
    nodeDataDiv.showing = window.setTimeout(function() {
        nodeDataDiv.html("Loading...").load($SCRIPT_ROOT + '/_properties/' + nodeId).show();
    }, 300);
}

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
										    if (this.selected) items.push('<li><span class="className">' + $PROPERTIES[this.id][2] + '</span></li>');
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
    var parameters = {};
    if ($CLASSES) parameters["classes"] = $CLASSES;
    ($SHOW_OPEN=="true") ? parameters["showOpen"] = "false" : parameters["showOpen"] = "true";
    window.location = buildGraphUrl(parameters);
}

$(document).ready(function(){
		      //if (!window.Touch) hovertipInit();

		      nodes = $('g[class="node"]');
		      nonstrictArrows = $('g[id|="nonstrict"]');

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

              nodeDataDiv = $('#nodeData')

		      toggleNonstrictArrowHighlight();

              nodes.hover(function(event) {postponeHidingDiv(nodeDataDiv); showNodeData(event);}, function() {hideDiv(nodeDataDiv); });
		      nodes.each(function(i, node) {
				     node.selected = false; 
				     node.sizeColor = "";
				     node.recolor = "";
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

		      readAndApplySettings();
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
    window.location = buildGraphUrl({"classes" : unselected.join()});
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
    window.open(buildGraphUrl({"classes" : getSelectedClasses()}));
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
    var checkedBoxes = $('#excludedClasses :checkbox:checked');
    if (checkedBoxes.length == $('#excludedClasses :checkbox').length) {
	window.location = buildGraphUrl({});
    } else {
	var classesToDisplay = [];
	checkedBoxes.each(function() {
			      classesToDisplay.push(this.value);
			  });
	nodes.each(function() {
		       classesToDisplay.push(this.id);
		   });
	window.location = buildGraphUrl({"classes" : classesToDisplay.join()});
    }
}

function restoreAll() {
    window.location = buildGraphUrl({});
}

function buildGraphUrl(parameters) {
    if (!('showOpen' in parameters))  parameters['showOpen'] = $SHOW_OPEN;
    return $SCRIPT_ROOT + '/?' + $.param(parameters) + window.location.hash;
}

