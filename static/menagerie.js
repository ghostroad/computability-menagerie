var nodes;
var weakEdges;
var strongEdges;

var showImplicationsButton;
var viewSubgraphButton;
var showWeakOpenCheckbox;
var showStrongOpenCheckbox;
var numSelected = 0;

$(document).ready(function(){
  hovertipInit();
  
  $('#help').hide();
  $('#toggleHelp').click( function() { $('#help').toggle(400); } );

  nodes = $('g[class="node"]');
  weakEdges = $('g[id|="weak"]');
  strongEdges = $('g[id|="strong"]');

  showImplicationsButton = $('#showImplications')[0];
  viewSubgraphButton = $('#viewSubgraph')[0];
  showWeakOpenCheckbox = $('#showWeakOpen')[0];
  showStrongOpenCheckbox = $('#showStrongOpen')[0];

  handleOpenImplicationPreferences();

  nodes.each(function(i, node) {
    node.selected = false; 
    node.toggleSelected = function() {
      if (this.getAttribute('class') != 'selected') {
        this.setAttribute('class', 'selected');
        this.selected = true;
        numSelected++;
      } else {
        this.setAttribute('class', 'node');
        this.selected = false;
        numSelected--;
      }
      $('#numSelected').text(numSelected);

      if (numSelected == 1) {
        var classes = nodes.map(function() { return this.id; }).toArray().join(",");
	nodes.each(function() {
	  if (this.selected) {
            $.getJSON($SCRIPT_ROOT + '/_recolor', { selectedClass: this.id, classes: classes }, 
              function(data) {
                if (numSelected == 1) applyColor(data);
              }
            );
          };
        });
      } else {
        nodes.each(function() {
          if (!this.selected) this.setAttribute('class', 'node');	  
        });
      }

      viewSubgraphButton.disabled = (numSelected < 2);
      showImplicationsButton.disabled = (numSelected != 2);
    };
    node.addEventListener("click", function(evt) { evt.target.parentNode.toggleSelected(); }, true);
    node.addEventListener("dblclick", function(evt) { showClassDetails(evt.target.parentNode.id); }, true);
  });

});

function applyColor(data) {
  for (var cls in data) {
    var nodesToRecolor= data[cls];
    for (var i = 0; i < nodesToRecolor.length; i++){ 
      document.getElementById(nodesToRecolor[i]).setAttribute("class", cls);
    } 
  }
}

function disableButtons() {
  showImplicationsButton.disabled = true;
  viewSubgraphButton.disabled = true;
}

function showClassDetails(node) {
  window.open('showClassDetails/' + node);
}

function showImplications() {
  var url = 'showImplications';
  nodes.each(function(i, node) {
    if (node.selected) url += '/'+node.id;
  });
  window.open(url);
}

function viewSubgraph() {
  disableButtons(); // hack for firefox weirdness with back button
  var selected = [];
  nodes.each(function(i, node) {
    if (node.selected) { selected.push(node.id); };
  });
  var url = '?classes=' + selected;
  window.location = url;
}

function unselectAll() {
  nodes.each(function(i, node) {
    if (node.selected) { node.toggleSelected(); }
  }); 
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

