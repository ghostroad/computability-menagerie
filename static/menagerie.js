var nodes;
var weakEdges;
var strongEdges;

var showClassDetailsButton;
var showImplicationsButton;
var viewSubgraphButton;
var showWeakOpenCheckbox;
var showStrongOpenCheckbox;
var numSelected = 0;
var recolored = false;

$(document).ready(function(){
  if (!window.Touch) hovertipInit();
  
  $('#help').hide();
  $('#toggleHelp').click( function() { $('#help').toggle(400); } );
  $('#toggleKey').click( function() { $('#key').toggle(400); } );

  nodes = $('g[class="node"]');
  weakEdges = $('g[id|="weak"]');
  strongEdges = $('g[id|="strong"]');
		     
		      
  showClassDetailsButton = $('#showClassDetails input')[0];
  if (window.Touch) $('#showClassDetails').show();
  showImplicationsButton = $('#showImplications')[0];
  viewSubgraphButton = $('#viewSubgraph')[0];
  showWeakOpenCheckbox = $('#showWeakOpen')[0];
  showStrongOpenCheckbox = $('#showStrongOpen')[0];

  disableButtonsIfAppropriate();

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
    node.addEventListener("click", function(evt) { evt.target.parentNode.toggleSelected(); recolorIfNecessary(); }, true);
    node.addEventListener("dblclick", function(evt) { showClassDetails(evt.target.parentNode.id); }, true);
  });
});

function disableButtonsIfAppropriate() {
      viewSubgraphButton.disabled = (numSelected < 2);
      showImplicationsButton.disabled = (numSelected != 2);
      showClassDetailsButton.disabled = (numSelected != 1);
}
function recolorIfNecessary() {
    if (numSelected == 1) {
	nodes.each(function() {
		       if (this.selected) {
			   $.getJSON($SCRIPT_ROOT + '/_recolor', { selectedClass: this.id }, 
				     function(data) {
					 if (numSelected == 1) applyColor(data);
				     }
				    );
		       };
		   });
    } else { restoreColor(); }
}

function restoreColor() {
    if (recolored) {
	nodes.each(function() {
		       $(this).removeClass('above properlyAbove below properlyBelow incomparable other');	  
		   });
	recolored = false;
    }
}

function applyColor(data) {
    nodes.each(function() {
		   $(this).addClass(data[this.id]);
	       });
    recolored = true;
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
  restoreColor();
}

function updateWeakOpen() {
  showWeakOpenCheckbox.checked ? weakEdges.show() : weakEdges.hide();
}

function updateStrongOpen() {
  showStrongOpenCheckbox.checked ? strongEdges.show() : strongEdges.hide();
}

function updateHash() {
  var showWeakOpen = showWeakOpenCheckbox.checked;
  var showStrongOpen = showStrongOpenCheckbox.checked;
  window.location.hash = showWeakOpen + '-' + showStrongOpen;
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

