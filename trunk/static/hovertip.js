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


var hovertipMouseX;
var hovertipMouseY;
function hovertipMouseUpdate(e) {
  var mouse = hovertipMouseXY(e);
  hovertipMouseX = mouse[0];
  hovertipMouseY = mouse[1];
}

// http://www.howtocreate.co.uk/tutorials/javascript/eventinfo
function hovertipMouseXY(e) {
  if( !e ) {
    if( window.event ) {
      //Internet Explorer
      e = window.event;
    } else {
      //total failure, we have no way of referencing the event
      return;
    }
  }
  if( typeof( e.pageX ) == 'number' ) {
    //most browsers
    var xcoord = e.pageX;
    var ycoord = e.pageY;
  } else if( typeof( e.clientX ) == 'number' ) {
    //Internet Explorer and older browsers
    //other browsers provide this, but follow the pageX/Y branch
    var xcoord = e.clientX;
    var ycoord = e.clientY;
    var badOldBrowser = ( window.navigator.userAgent.indexOf( 'Opera' ) + 1 ) ||
      ( window.ScriptEngine && ScriptEngine().indexOf( 'InScript' ) + 1 ) ||
      ( navigator.vendor == 'KDE' );
    if( !badOldBrowser ) {
      if( document.body && ( document.body.scrollLeft || document.body.scrollTop ) ) {
        //IE 4, 5 & 6 (in non-standards compliant mode)
        xcoord += document.body.scrollLeft;
        ycoord += document.body.scrollTop;
      } else if( document.documentElement && ( document.documentElement.scrollLeft || document.documentElement.scrollTop ) ) {
        //IE 6 (in standards compliant mode)
        xcoord += document.documentElement.scrollLeft;
        ycoord += document.documentElement.scrollTop;
      }
    }
  } else {
    //total failure, we have no way of obtaining the mouse coordinates
    return;
  }
  return [xcoord, ycoord];
}


hovertipIsVisible = function(el) {
  return el.css('display') != 'none';
}

// show the tooltip under the mouse.
// Introduce a delay, so tip appears only if cursor rests on target for more than an instant.
hovertipShowUnderMouse = function(el, event) {
  var nodeId = event.target.parentNode.id
  if (hovertipIsVisible(el) && el.owner == nodeId) hovertipHideCancel(el);
  if (hovertipIsVisible(el) && el.owner != nodeId) el.hide();
    if (!hovertipIsVisible(el)) {
	el.ht.showing = // keep reference to timer
	window.setTimeout(function() {
			      el.ht.tip.css({
						'position':'absolute',
						'top': (hovertipMouseY + 20) + 'px',
						'left': (hovertipMouseX + 20) + 'px'})
				  .show().load($SCRIPT_ROOT + '/_properties/' + nodeId);
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
                        'showDelay': 900,
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
    hoverables.mousemove(hovertipMouseUpdate);
}