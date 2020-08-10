!function(){String.prototype.startsWith||(String.prototype.startsWith=function(t,e){return this.substr(e||0,t.length)===t});var t=null,e={inheritAttrs:function(t,e){for(var i in e)e.hasOwnProperty(i)&&(t[i]instanceof Object&&e[i]instanceof Object&&"function"!=typeof e[i]?this.inheritAttrs(t[i],e[i]):t[i]=e[i]);return t},createMerge:function(t,e){var i={};return t&&this.inheritAttrs(i,this.cloneObj(t)),e&&this.inheritAttrs(i,e),i},extend:function(){return t?(Array.prototype.unshift.apply(arguments,[!0,{}]),t.extend.apply(t,arguments)):e.createMerge.apply(this,arguments)},cloneObj:function(t){if(Object(t)!==t)return t;var e=new t.constructor;for(var i in t)t.hasOwnProperty(i)&&(e[i]=this.cloneObj(t[i]));return e},addEvent:function(e,i,n){t?t(e).on(i+".treant",n):e.addEventListener?e.addEventListener(i,n,!1):e.attachEvent?e.attachEvent("on"+i,n):e["on"+i]=n},findEl:function(e,i,n){if(n=n||document,t){var r=t(e,n);return i?r.get(0):r}if("#"===e.charAt(0))return n.getElementById(e.substring(1));if("."===e.charAt(0)){var o=n.getElementsByClassName(e.substring(1));return o.length?o[0]:null}throw new Error("Unknown container element")},getOuterHeight:function(i){return"function"==typeof i.getBoundingClientRect?i.getBoundingClientRect().height:t?Math.ceil(t(i).outerHeight())+1:Math.ceil(i.clientHeight+e.getStyle(i,"border-top-width",!0)+e.getStyle(i,"border-bottom-width",!0)+e.getStyle(i,"padding-top",!0)+e.getStyle(i,"padding-bottom",!0)+1)},getOuterWidth:function(i){return"function"==typeof i.getBoundingClientRect?i.getBoundingClientRect().width:t?Math.ceil(t(i).outerWidth())+1:Math.ceil(i.clientWidth+e.getStyle(i,"border-left-width",!0)+e.getStyle(i,"border-right-width",!0)+e.getStyle(i,"padding-left",!0)+e.getStyle(i,"padding-right",!0)+1)},getStyle:function(t,e,i){var n="";return document.defaultView&&document.defaultView.getComputedStyle?n=document.defaultView.getComputedStyle(t,"").getPropertyValue(e):t.currentStyle&&(e=e.replace(/\-(\w)/g,function(t,e){return e.toUpperCase()}),n=t.currentStyle[e]),i?parseFloat(n):n},addClass:function(i,n){t?t(i).addClass(n):e.hasClass(i,n)||(i.classList?i.classList.add(n):i.className+=" "+n)},hasClass:function(t,e){return(" "+t.className+" ").replace(/[\n\t]/g," ").indexOf(" "+e+" ")>-1},toggleClass:function(e,i,n){t?t(e).toggleClass(i,n):n?e.classList.add(i):e.classList.remove(i)},setDimensions:function(e,i,n){t?t(e).width(i).height(n):(e.style.width=i+"px",e.style.height=n+"px")},isjQueryAvailable:function(){return void 0!==t&&t}},i=function(){this.reset()};i.prototype={reset:function(){return this.loading=[],this},processNode:function(t){for(var e=t.nodeDOM.getElementsByTagName("img"),i=e.length;i--;)this.create(t,e[i]);return this},removeAll:function(t){for(var e=this.loading.length;e--;)this.loading[e]===t&&this.loading.splice(e,1);return this},create:function(t,i){var n=this,r=i.src;function o(){n.removeAll(r),t.width=t.nodeDOM.offsetWidth,t.height=t.nodeDOM.offsetHeight}if(0!==i.src.indexOf("data:")){if(this.loading.push(r),i.complete)return o();e.addEvent(i,"load",o),e.addEvent(i,"error",o),i.src+=(i.src.indexOf("?")>0?"&":"?")+(new Date).getTime()}else o()},isNotLoading:function(){return 0===this.loading.length}};var n={store:[],createTree:function(t){var e=this.store.length;return this.store.push(new r(t,e)),this.get(e)},get:function(t){return this.store[t]},destroy:function(t){var e=this.get(t);if(e){e._R.remove();for(var i=e.drawArea;i.firstChild;)i.removeChild(i.firstChild);for(var n=i.className.split(" "),r=[],o=0;o<n.length;o++){var s=n[o];"Treant"!==s&&"Treant-loaded"!==s&&r.push(s)}i.style.overflowY="",i.style.overflowX="",i.className=r.join(" "),this.store[t]=null}return this}},r=function(t,n){this.reset=function(t,n){if(this.initJsonConfig=t,this.initTreeId=n,this.id=n,this.CONFIG=e.extend(r.CONFIG,t.chart),this.drawArea=e.findEl(this.CONFIG.container,!0),!this.drawArea)throw new Error('Failed to find element by selector "'+this.CONFIG.container+'"');return e.addClass(this.drawArea,"Treant"),this.drawArea.innerHTML="",this.imageLoader=new i,this.nodeDB=new o(t.nodeStructure,this),this.connectionStore={},this.loaded=!1,this._R=new Raphael(this.drawArea,100,100),this},this.reload=function(){return this.reset(this.initJsonConfig,this.initTreeId).redraw(),this},this.reset(t,n)};r.prototype={getNodeDb:function(){return this.nodeDB},addNode:function(t,e){this.nodeDB.get(t.id);this.CONFIG.callback.onBeforeAddNode.apply(this,[t,e]);var i=this.nodeDB.createNode(e,t.id,this);return i.createGeometry(this),i.parent().createSwitchGeometry(this),this.positionTree(),this.CONFIG.callback.onAfterAddNode.apply(this,[i,t,e]),i},redraw:function(){return this.positionTree(),this},positionTree:function(t){var i=this;if(this.imageLoader.isNotLoading()){var n=this.root();this.CONFIG.rootOrientation;this.resetLevelData(),this.firstWalk(n,0),this.secondWalk(n,0,0,0),this.positionNodes(),this.CONFIG.animateOnInit&&setTimeout(function(){n.toggleCollapse()},this.CONFIG.animateOnInitDelay),this.loaded||(e.addClass(this.drawArea,"Treant-loaded"),"[object Function]"===Object.prototype.toString.call(t)&&t(i),i.CONFIG.callback.onTreeLoaded.apply(i,[n]),this.loaded=!0)}else setTimeout(function(){i.positionTree(t)},10);return this},firstWalk:function(t,e){t.prelim=null,t.modifier=null,this.setNeighbors(t,e),this.calcLevelDim(t,e);var i=t.leftSibling();if(0===t.childrenCount()||e==this.CONFIG.maxDepth)t.prelim=i?i.prelim+i.size()+this.CONFIG.siblingSeparation:0;else{for(var n=0,r=t.childrenCount();n<r;n++)this.firstWalk(t.childAt(n),e+1);var o=t.childrenCenter()-t.size()/2;i?(t.prelim=i.prelim+i.size()+this.CONFIG.siblingSeparation,t.modifier=t.prelim-o,this.apportion(t,e)):t.prelim=o,t.stackParent?t.modifier+=this.nodeDB.get(t.stackChildren[0]).size()/2+t.connStyle.stackIndent:t.stackParentId&&(t.prelim=0)}return this},apportion:function(t,e){for(var i=t.firstChild(),n=i.leftNeighbor(),r=1,o=this.CONFIG.maxDepth-e;i&&n&&r<=o;){for(var s=0,h=0,a=n,l=i,d=0;d<r;d++)a=a.parent(),l=l.parent(),h+=a.modifier,s+=l.modifier,void 0!==l.stackParent&&(s+=l.size()/2);var c=n.prelim+h+n.size()+this.CONFIG.subTeeSeparation-(i.prelim+s);if(c>0){for(var u=t,f=0;u&&u.id!==a.id;)u=u.leftSibling(),f++;if(u)for(var p=t,g=c/f;p.id!==a.id;)p.prelim+=c,p.modifier+=c,c-=g,p=p.leftSibling()}r++,(i=0===i.childrenCount()?t.leftMost(0,r):i=i.firstChild())&&(n=i.leftNeighbor())}},secondWalk:function(t,e,i,n){if(e<=this.CONFIG.maxDepth){var r,o,s=t.prelim+i,h=n,a=this.CONFIG.nodeAlign,l=this.CONFIG.rootOrientation;if("NORTH"===l||"SOUTH"===l?(r=this.levelMaxDim[e].height,o=t.height,t.pseudo&&(t.height=r)):"WEST"!==l&&"EAST"!==l||(r=this.levelMaxDim[e].width,o=t.width,t.pseudo&&(t.width=r)),t.X=s,t.pseudo?"NORTH"===l||"WEST"===l?t.Y=h:"SOUTH"!==l&&"EAST"!==l||(t.Y=h+(r-o)):t.Y="CENTER"===a?h+(r-o)/2:"TOP"===a?h+(r-o):h,"WEST"===l||"EAST"===l){var d=t.X;t.X=t.Y,t.Y=d}"SOUTH"===l?t.Y=-t.Y-o:"EAST"===l&&(t.X=-t.X-o),0!==t.childrenCount()&&(0===t.id&&this.CONFIG.hideRootNode?this.secondWalk(t.firstChild(),e+1,i+t.modifier,n):this.secondWalk(t.firstChild(),e+1,i+t.modifier,n+r+this.CONFIG.levelSeparation)),t.rightSibling()&&this.secondWalk(t.rightSibling(),e,i,n)}},positionNodes:function(){var t={x:this.nodeDB.getMinMaxCoord("X",null,null),y:this.nodeDB.getMinMaxCoord("Y",null,null)},e=t.x.max-t.x.min,i=t.y.max-t.y.min,n={x:t.x.max-e/2,y:t.y.max-i/2};this.handleOverflow(e,i);var r,o,s,h={x:this.drawArea.clientWidth/2,y:this.drawArea.clientHeight/2},a=h.x-n.x,l=h.y-n.y,d=t.x.min+a<=0?Math.abs(t.x.min):0,c=t.y.min+l<=0?Math.abs(t.y.min):0;for(r=0,o=this.nodeDB.db.length;r<o;r++)if(s=this.nodeDB.get(r),this.CONFIG.callback.onBeforePositionNode.apply(this,[s,r,h,n]),0===s.id&&this.CONFIG.hideRootNode)this.CONFIG.callback.onAfterPositionNode.apply(this,[s,r,h,n]);else{s.X+=d+(e<this.drawArea.clientWidth?a:this.CONFIG.padding),s.Y+=c+(i<this.drawArea.clientHeight?l:this.CONFIG.padding);var u=s.collapsedParent(),f=null;u?(f=u.connectorPoint(!0),s.hide(f)):s.positioned?s.show():(s.nodeDOM.style.left=s.X+"px",s.nodeDOM.style.top=s.Y+"px",s.positioned=!0),0===s.id||0===s.parent().id&&this.CONFIG.hideRootNode?!this.CONFIG.hideRootNode&&s.drawLineThrough&&s.drawLineThroughMe():this.setConnectionToParent(s,f),this.CONFIG.callback.onAfterPositionNode.apply(this,[s,r,h,n])}return this},handleOverflow:function(i,n){var r=i<this.drawArea.clientWidth?this.drawArea.clientWidth:i+2*this.CONFIG.padding,o=n<this.drawArea.clientHeight?this.drawArea.clientHeight:n+2*this.CONFIG.padding;if(this._R.setSize(r,o),"resize"===this.CONFIG.scrollbar)e.setDimensions(this.drawArea,r,o);else if(e.isjQueryAvailable()&&"native"!==this.CONFIG.scrollbar){if("fancy"===this.CONFIG.scrollbar){var s=t(this.drawArea);if(s.hasClass("ps-container"))s.find(".Treant").css({width:r,height:o}),s.perfectScrollbar("update");else{var h=s.wrapInner('<div class="Treant"/>');h.find(".Treant").css({width:r,height:o}),h.perfectScrollbar()}}}else this.drawArea.clientWidth<i&&(this.drawArea.style.overflowX="auto"),this.drawArea.clientHeight<n&&(this.drawArea.style.overflowY="auto");return this},setConnectionToParent:function(t,e){var i,n=t.stackParentId,r=n?this.nodeDB.get(n):t.parent(),o=e?this.getPointPathString(e):this.getPathString(r,t,n);return this.connectionStore[t.id]?(i=this.connectionStore[t.id],this.animatePath(i,o)):(i=this._R.path(o),this.connectionStore[t.id]=i,t.pseudo&&delete r.connStyle.style["arrow-end"],r.pseudo&&delete r.connStyle.style["arrow-start"],i.attr(r.connStyle.style),(t.drawLineThrough||t.pseudo)&&t.drawLineThroughMe(e)),t.connector=i,this},getPointPathString:function(t){return["_M",t.x,",",t.y,"L",t.x,",",t.y,t.x,",",t.y].join(" ")},animatePath:function(t,e){return t.hidden&&"_"!==e.charAt(0)&&(t.show(),t.hidden=!1),t.animate({path:"_"===e.charAt(0)?e.substring(1):e},this.CONFIG.animation.connectorsSpeed,this.CONFIG.animation.connectorsAnimation,function(){"_"===e.charAt(0)&&(t.hide(),t.hidden=!0)}),this},getPathString:function(t,e,i){var n=t.connectorPoint(!0),r=e.connectorPoint(!1),o=this.CONFIG.rootOrientation,s=t.connStyle.type,h={},a={};"NORTH"===o||"SOUTH"===o?(h.y=a.y=(n.y+r.y)/2,h.x=n.x,a.x=r.x):"EAST"!==o&&"WEST"!==o||(h.x=a.x=(n.x+r.x)/2,h.y=n.y,a.y=r.y);var l,d,c=n.x+","+n.y,u=h.x+","+h.y,f=a.x+","+a.y,p=r.x+","+r.y,g=(h.x+a.x)/2+","+(h.y+a.y)/2;if(i){if(d="EAST"===o||"WEST"===o?r.x+","+n.y:n.x+","+r.y,"step"===s||"straight"===s)l=["M",c,"L",d,"L",p];else if("curve"===s||"bCurve"===s){var m,y=t.connStyle.stackIndent;"NORTH"===o?m=r.x-y+","+(r.y-y):"SOUTH"===o?m=r.x-y+","+(r.y+y):"EAST"===o?m=r.x+y+","+n.y:"WEST"===o&&(m=r.x-y+","+n.y),l=["M",c,"L",m,"S",d,p]}}else"step"===s?l=["M",c,"L",u,"L",f,"L",p]:"curve"===s?l=["M",c,"C",u,f,p]:"bCurve"===s?l=["M",c,"Q",u,g,"T",p]:"straight"===s&&(l=["M",c,"L",c,p]);return l.join(" ")},setNeighbors:function(t,e){return t.leftNeighborId=this.lastNodeOnLevel[e],t.leftNeighborId&&(t.leftNeighbor().rightNeighborId=t.id),this.lastNodeOnLevel[e]=t.id,this},calcLevelDim:function(t,e){return this.levelMaxDim[e]={width:Math.max(this.levelMaxDim[e]?this.levelMaxDim[e].width:0,t.width),height:Math.max(this.levelMaxDim[e]?this.levelMaxDim[e].height:0,t.height)},this},resetLevelData:function(){return this.lastNodeOnLevel=[],this.levelMaxDim=[],this},root:function(){return this.nodeDB.get(0)}};var o=function(t,e){this.reset(t,e)};o.prototype={reset:function(t,i){this.db=[];var n=this;return i.CONFIG.animateOnInit&&(t.collapsed=!0),function t(r,o){var s=n.createNode(r,o,i,null);if(r.children){if(r.childrenDropLevel&&r.childrenDropLevel>0)for(;r.childrenDropLevel--;){var h=e.cloneObj(s.connStyle);(s=n.createNode("pseudo",s.id,i,null)).connStyle=h,s.children=[]}var a=r.stackChildren&&!n.hasGrandChildren(r)?s.id:null;null!==a&&(s.stackChildren=[]);for(var l=0,d=r.children.length;l<d;l++)null!==a?(s=n.createNode(r.children[l],s.id,i,a),l+1<d&&(s.children=[])):t(r.children[l],s.id)}}(t,-1),this.createGeometries(i),this},createGeometries:function(t){for(var e=this.db.length;e--;)this.get(e).createGeometry(t);return this},get:function(t){return this.db[t]},walk:function(t){for(var e=this.db.length;e--;)t.apply(this,[this.get(e)]);return this},createNode:function(t,e,i,n){var r=new s(t,this.db.length,e,i,n);if(this.db.push(r),e>=0){var o=this.get(e);if(t.position)if("left"===t.position)o.children.push(r.id);else if("right"===t.position)o.children.splice(0,0,r.id);else if("center"===t.position)o.children.splice(Math.floor(o.children.length/2),0,r.id);else{var h=parseInt(t.position);1===o.children.length&&h>0?o.children.splice(0,0,r.id):o.children.splice(Math.max(h,o.children.length-1),0,r.id)}else o.children.push(r.id)}return n&&(this.get(n).stackParent=!0,this.get(n).stackChildren.push(r.id)),r},getMinMaxCoord:function(t,e,i){e=e||this.get(0),i=i||{min:e[t],max:e[t]+("X"===t?e.width:e.height)};for(var n=e.childrenCount();n--;){var r=e.childAt(n),o=r[t]+("X"===t?r.width:r.height),s=r[t];o>i.max&&(i.max=o),s<i.min&&(i.min=s),this.getMinMaxCoord(t,r,i)}return i},hasGrandChildren:function(t){for(var e=t.children.length;e--;)if(t.children[e].children)return!0;return!1}};var s=function(t,e,i,n,r){this.reset(t,e,i,n,r)};s.prototype={reset:function(t,i,n,r,o){return this.id=i,this.parentId=n,this.treeId=r.id,this.prelim=0,this.modifier=0,this.leftNeighborId=null,this.stackParentId=o,this.pseudo="pseudo"===t||t.pseudo,this.meta=t.meta||{},this.image=t.image||null,this.link=e.createMerge(r.CONFIG.node.link,t.link),this.connStyle=e.createMerge(r.CONFIG.connectors,t.connectors),this.connector=null,this.drawLineThrough=!1!==t.drawLineThrough&&(t.drawLineThrough||r.CONFIG.node.drawLineThrough),this.collapsable=!1!==t.collapsable&&(t.collapsable||r.CONFIG.node.collapsable),this.collapsed=t.collapsed,this.text=t.text,this.nodeInnerHTML=t.innerHTML,this.nodeHTMLclass=(r.CONFIG.node.HTMLclass?r.CONFIG.node.HTMLclass:"")+(t.HTMLclass?" "+t.HTMLclass:""),this.nodeHTMLid=t.HTMLid,this.children=[],this},getTree:function(){return n.get(this.treeId)},getTreeConfig:function(){return this.getTree().CONFIG},getTreeNodeDb:function(){return this.getTree().getNodeDb()},lookupNode:function(t){return this.getTreeNodeDb().get(t)},Tree:function(){return n.get(this.treeId)},dbGet:function(t){return this.getTreeNodeDb().get(t)},size:function(){var t=this.getTreeConfig().rootOrientation;return this.pseudo?-this.getTreeConfig().subTeeSeparation:"NORTH"===t||"SOUTH"===t?this.width:"WEST"===t||"EAST"===t?this.height:void 0},childrenCount:function(){return this.collapsed||!this.children?0:this.children.length},childAt:function(t){return this.dbGet(this.children[t])},firstChild:function(){return this.childAt(0)},lastChild:function(){return this.childAt(this.children.length-1)},parent:function(){return this.lookupNode(this.parentId)},leftNeighbor:function(){if(this.leftNeighborId)return this.lookupNode(this.leftNeighborId)},rightNeighbor:function(){if(this.rightNeighborId)return this.lookupNode(this.rightNeighborId)},leftSibling:function(){var t=this.leftNeighbor();if(t&&t.parentId===this.parentId)return t},rightSibling:function(){var t=this.rightNeighbor();if(t&&t.parentId===this.parentId)return t},childrenCenter:function(){var t=this.firstChild(),e=this.lastChild();return t.prelim+(e.prelim-t.prelim+e.size())/2},collapsedParent:function(){var t=this.parent();return!!t&&(t.collapsed?t:t.collapsedParent())},leftMost:function(t,e){if(t>=e)return this;if(0!==this.childrenCount())for(var i=0,n=this.childrenCount();i<n;i++){var r=this.childAt(i).leftMost(t+1,e);if(r)return r}},connectorPoint:function(t){var e=this.Tree().CONFIG.rootOrientation,i={};return this.stackParentId&&("NORTH"===e||"SOUTH"===e?e="WEST":"EAST"!==e&&"WEST"!==e||(e="NORTH")),"NORTH"===e?(i.x=this.pseudo?this.X-this.Tree().CONFIG.subTeeSeparation/2:this.X+this.width/2,i.y=t?this.Y+this.height:this.Y):"SOUTH"===e?(i.x=this.pseudo?this.X-this.Tree().CONFIG.subTeeSeparation/2:this.X+this.width/2,i.y=t?this.Y:this.Y+this.height):"EAST"===e?(i.x=t?this.X:this.X+this.width,i.y=this.pseudo?this.Y-this.Tree().CONFIG.subTeeSeparation/2:this.Y+this.height/2):"WEST"===e&&(i.x=t?this.X+this.width:this.X,i.y=this.pseudo?this.Y-this.Tree().CONFIG.subTeeSeparation/2:this.Y+this.height/2),i},pathStringThrough:function(){var t=this.connectorPoint(!0),e=this.connectorPoint(!1);return["M",t.x+","+t.y,"L",e.x+","+e.y].join(" ")},drawLineThroughMe:function(t){var i=t?this.Tree().getPointPathString(t):this.pathStringThrough();this.lineThroughMe=this.lineThroughMe||this.Tree()._R.path(i);var n=e.cloneObj(this.connStyle.style);delete n["arrow-start"],delete n["arrow-end"],this.lineThroughMe.attr(n),t&&(this.lineThroughMe.hide(),this.lineThroughMe.hidden=!0)},addSwitchEvent:function(t){var i=this;e.addEvent(t,"click",function(e){if(e.preventDefault(),!1===i.getTreeConfig().callback.onBeforeClickCollapseSwitch.apply(i,[t,e]))return!1;i.toggleCollapse(),i.getTreeConfig().callback.onAfterClickCollapseSwitch.apply(i,[t,e])})},collapse:function(){return this.collapsed||this.toggleCollapse(),this},expand:function(){return this.collapsed&&this.toggleCollapse(),this},toggleCollapse:function(){var t=this.getTree();if(!t.inAnimation){t.inAnimation=!0,this.collapsed=!this.collapsed,e.toggleClass(this.nodeDOM,"collapsed",this.collapsed),t.positionTree();var i=this;setTimeout(function(){t.inAnimation=!1,t.CONFIG.callback.onToggleCollapseFinished.apply(t,[i,i.collapsed])},t.CONFIG.animation.nodeSpeed>t.CONFIG.animation.connectorsSpeed?t.CONFIG.animation.nodeSpeed:t.CONFIG.animation.connectorsSpeed)}return this},hide:function(e){e=e||!1;var i=this.hidden;this.hidden=!0,this.nodeDOM.style.overflow="hidden";var n=this.getTree(),r=this.getTreeConfig(),o={opacity:0};if(e&&(o.left=e.x,o.top=e.y),!this.positioned||i?(this.nodeDOM.style.visibility="hidden",t?t(this.nodeDOM).css(o):(this.nodeDOM.style.left=o.left+"px",this.nodeDOM.style.top=o.top+"px"),this.positioned=!0):t?t(this.nodeDOM).animate(o,r.animation.nodeSpeed,r.animation.nodeAnimation,function(){this.style.visibility="hidden"}):(this.nodeDOM.style.transition="all "+r.animation.nodeSpeed+"ms ease",this.nodeDOM.style.transitionProperty="opacity, left, top",this.nodeDOM.style.opacity=o.opacity,this.nodeDOM.style.left=o.left+"px",this.nodeDOM.style.top=o.top+"px",this.nodeDOM.style.visibility="hidden"),this.lineThroughMe){var s=n.getPointPathString(e);i?this.lineThroughMe.attr({path:s}):n.animatePath(this.lineThroughMe,n.getPointPathString(e))}return this},hideConnector:function(){var t=this.Tree(),e=t.connectionStore[this.id];return e&&e.animate({opacity:0},t.CONFIG.animation.connectorsSpeed,t.CONFIG.animation.connectorsAnimation),this},show:function(){this.hidden;this.hidden=!1,this.nodeDOM.style.visibility="visible";this.Tree();var e={left:this.X,top:this.Y,opacity:1},i=this.getTreeConfig();return t?t(this.nodeDOM).animate(e,i.animation.nodeSpeed,i.animation.nodeAnimation,function(){this.style.overflow=""}):(this.nodeDOM.style.transition="all "+i.animation.nodeSpeed+"ms ease",this.nodeDOM.style.transitionProperty="opacity, left, top",this.nodeDOM.style.left=e.left+"px",this.nodeDOM.style.top=e.top+"px",this.nodeDOM.style.opacity=e.opacity,this.nodeDOM.style.overflow=""),this.lineThroughMe&&this.getTree().animatePath(this.lineThroughMe,this.pathStringThrough()),this},showConnector:function(){var t=this.Tree(),e=t.connectionStore[this.id];return e&&e.animate({opacity:1},t.CONFIG.animation.connectorsSpeed,t.CONFIG.animation.connectorsAnimation),this}},s.prototype.buildNodeFromText=function(t){if(this.image&&(image=document.createElement("img"),image.src=this.image,t.appendChild(image)),this.text)for(var e in this.text)if(e.startsWith("data-"))t.setAttribute(e,this.text[e]);else{var i=document.createElement(this.text[e].href?"a":"p");this.text[e].href&&(i.href=this.text[e].href,this.text[e].target&&(i.target=this.text[e].target)),i.className="node-"+e,i.appendChild(document.createTextNode(this.text[e].val?this.text[e].val:this.text[e]instanceof Object?"'val' param missing!":this.text[e])),t.appendChild(i)}return t},s.prototype.buildNodeFromHtml=function(t){if("#"===this.nodeInnerHTML.charAt(0)){var e=document.getElementById(this.nodeInnerHTML.substring(1));e?((t=e.cloneNode(!0)).id+="-clone",t.className+=" node"):t.innerHTML="<b> Wrong ID selector </b>"}else t.innerHTML=this.nodeInnerHTML;return t},s.prototype.createGeometry=function(e){if(0===this.id&&e.CONFIG.hideRootNode)return this.width=0,void(this.height=0);var i=e.drawArea,n=document.createElement(this.link.href?"a":"div");n.className=this.pseudo?"pseudo":s.CONFIG.nodeHTMLclass,this.nodeHTMLclass&&!this.pseudo&&(n.className+=" "+this.nodeHTMLclass),this.nodeHTMLid&&(n.id=this.nodeHTMLid),this.link.href&&(n.href=this.link.href,n.target=this.link.target),t?t(n).data("treenode",this):n.data={treenode:this},this.pseudo||(n=this.nodeInnerHTML?this.buildNodeFromHtml(n):this.buildNodeFromText(n),(this.collapsed||this.collapsable&&this.childrenCount()&&!this.stackParentId)&&this.createSwitchGeometry(e,n)),e.CONFIG.callback.onCreateNode.apply(e,[this,n]),i.appendChild(n),this.width=n.offsetWidth,this.height=n.offsetHeight,this.nodeDOM=n,e.imageLoader.processNode(this)},s.prototype.createSwitchGeometry=function(t,i){i=i||this.nodeDOM;var n=e.findEl(".collapse-switch",!0,i);return n||((n=document.createElement("a")).className="collapse-switch",i.appendChild(n),this.addSwitchEvent(n),this.collapsed&&(i.className+=" collapsed"),t.CONFIG.callback.onCreateNodeCollapseSwitch.apply(t,[this,i,n])),n},r.CONFIG={maxDepth:100,rootOrientation:"NORTH",nodeAlign:"CENTER",levelSeparation:30,siblingSeparation:30,subTeeSeparation:30,hideRootNode:!1,animateOnInit:!1,animateOnInitDelay:500,padding:15,scrollbar:"native",connectors:{type:"curve",style:{stroke:"black"},stackIndent:15},node:{link:{target:"_self"}},animation:{nodeSpeed:450,nodeAnimation:"linear",connectorsSpeed:450,connectorsAnimation:"linear"},callback:{onCreateNode:function(t,e){},onCreateNodeCollapseSwitch:function(t,e,i){},onAfterAddNode:function(t,e,i){},onBeforeAddNode:function(t,e){},onAfterPositionNode:function(t,e,i,n){},onBeforePositionNode:function(t,e,i,n){},onToggleCollapseFinished:function(t,e){},onAfterClickCollapseSwitch:function(t,e){},onBeforeClickCollapseSwitch:function(t,e){},onTreeLoaded:function(t){}}},s.CONFIG={nodeHTMLclass:"node"};var h,a={make:function(t){var e,i=t.length;for(this.jsonStructure={chart:null,nodeStructure:null};i--;)(e=t[i]).hasOwnProperty("container")?this.jsonStructure.chart=e:e.hasOwnProperty("parent")||e.hasOwnProperty("container")||(this.jsonStructure.nodeStructure=e,e._json_id=0);return this.findChildren(t),this.jsonStructure},findChildren:function(t){for(var e=[0];e.length;){for(var i=e.pop(),n=this.findNode(this.jsonStructure.nodeStructure,i),r=0,o=t.length,s=[];r<o;r++){var h=t[r];h.parent&&h.parent._json_id===i&&(h._json_id=this.getID(),delete h.parent,s.push(h),e.push(h._json_id))}s.length&&(n.children=s)}},findNode:function(t,e){var i,n;if(t._json_id===e)return t;if(t.children)for(i=t.children.length;i--;)if(n=this.findNode(t.children[i],e))return n},getID:(h=1,function(){return h++})},l=function(e,i,r){e instanceof Array&&(e=a.make(e)),r&&(t=r),this.tree=n.createTree(e),this.tree.positionTree(i)};l.prototype.destroy=function(){n.destroy(this.tree.id)},window.Treant=l}();
