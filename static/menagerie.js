var nodes;
var weakEdges;
var strongEdges;

var showImplicationsButton;
var viewSubgraphButton;
var showWeakOpenCheckbox;
var showStrongOpenCheckbox;
var numSelected = 0;

$(document).ready(function(){

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
      if (this.getAttribute('class') == 'node') {
        this.setAttribute('class', 'selected');
        this.selected = true;
        numSelected++;
      } else {
        this.setAttribute('class', 'node');
        this.selected = false;
        numSelected--;
      }
      $('#numSelected').text(numSelected);
      viewSubgraphButton.disabled = (numSelected < 2);
      showImplicationsButton.disabled = (numSelected != 2);
    };
    node.addEventListener("click", function(evt) { evt.target.parentNode.toggleSelected(); }, true);
    node.addEventListener("dblclick", function(evt) { showClassDetails(evt.target.parentNode.id); }, true);
  });

});

function disableButtons() {
  showImplicationsButton.disabled = true;
  viewSubgraphButton.disabled = true;
}

function showClassDetails(node) {
  disableButtons();
  window.open('showClassDetails/' + node);
}

function showImplications() {
  disableButtons();
  var url = 'showImplications';
  nodes.each(function(i, node) {
    if (node.selected) url += '/'+node.id;
  });
  window.open(url);
}

function viewSubgraph() {
  disableButtons();
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

