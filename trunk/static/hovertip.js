/**
 *  Adapted from Hovertip by Dave Cohen
 *  by Mushfeq Khan <http://www.math.wisc.edu/~khan> to use a single div for tooltips,
 *  to load content via Ajax and to be compatible with SVG target elements
 * 
 *  Originally by Dave Cohen <http://dave-cohen.com>
 *  
 *  With ideas and and javascript code borrowed from many folks.
 *  (See URLS in the comments)
 *  
 *  Licensed under GPL. 
 *  Requires jQuery.js.  <http://jquery.com>, 
 *  which may be distributed under a different licence.
 *  
 */


hovertipIsVisible = function(el) {
  return el.css('display') != 'none';
}

// show the tooltip under the mouse.
// Introduce a delay, so tip appears only if cursor rests on target for more than an instant.
hovertipShowUnderMouse = function(el, event) {
  var nodeId = event.target.parentNode.id;
  if (hovertipIsVisible(el) && el.owner == nodeId) hovertipHideCancel(el);
  if (hovertipIsVisible(el) && el.owner != nodeId) el.hide();
    if (!hovertipIsVisible(el)) {
	var viewportX = event.pageX - $(window).scrollLeft();
	var viewportY = event.pageY - $(window).scrollTop();
	var width = $(window).width();

	el.ht.showing = // keep reference to timer
	window.setTimeout(function() {

			      if ((viewportX < width - 200) || (viewportY > 200)) {
				  el.ht.tip.css({
						    'position':'fixed',
						    'bottom':'auto',
						    'left':'auto',
						    'top': '10px',
						    'right': '10px'});
			      } else {
				  el.ht.tip.css({
						    'position':'fixed',
						    'top' : 'auto',
						    'right' : 'auto',
						    'bottom': '10px',
						    'left': '10px'});
			      }
				  el.ht.tip.html("Loading...").load($SCRIPT_ROOT + '/_properties/' + nodeId).show();
			      el.owner = nodeId;
			  }, el.ht.config.showDelay);
    }
};

// do not hide
hovertipHideCancel = function(el) {
  if (el.ht.hiding) {
    window.clearTimeout(el.ht.hiding);
    el.ht.hiding = null;
  }  
};

// Hide a tooltip, but only after a delay.
// The delay allow the tip to remain when user moves mouse from target to tooltip
hovertipHideLater = function(el) {
  if (el.ht.showing) {
    window.clearTimeout(el.ht.showing);
    el.ht.showing = null;
  }
  if (el.ht.hiding) {
    window.clearTimeout(el.ht.hiding);
    el.ht.hiding = null;
  }
  el.ht.hiding = 
  window.setTimeout(function() {
      if (el.ht.hiding) {
        // fadeOut, slideUp do not work on Konqueror
        el.ht.tip.hide();
      }
    }, el.ht.config.hideDelay);
};


function hovertipInit() {
  var hovertipConfig = {'attribute':'hovertip',
                        'showDelay': 600,
                        'hideDelay': 300};
  
    var hovertipDiv = $('div.hovertip');
    hovertipDiv.ht = {};
    hovertipDiv.owner = null;
    hovertipDiv.ht.config = hovertipConfig;

    
    hovertipDiv.css('display', 'block').hide();
    
    hovertipDiv.ht.tip = hovertipDiv.hover(function() {
					       hovertipHideCancel(hovertipDiv);
					   }, function() {
					       hovertipHideLater(hovertipDiv);
					   }).css('position', 'absolute');

    var hoverables = $('g[class="node"]');
    hoverables.hover(function(event) {
			 hovertipShowUnderMouse(hovertipDiv, event);
		     },
		     function() {
			 hovertipHideLater(hovertipDiv);
		     });
 }