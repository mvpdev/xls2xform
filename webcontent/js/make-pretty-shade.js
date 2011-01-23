var xformer = (function(options){
	var img, div, defaultOpts, opts;

	defaultOpts = {
		'opacity': 0.7,
		pulseTime: 750
	}
	opts = $.extend(defaultOpts, options);

	div = $("<div />", {'style': 'position:fixed;right:75px;width:114px;height:127px;top:7px;z-index:-1'});
	div.append(img);
	function loadXformer() {
		img = $("<img />");
		img.css({'opacity':0});
		img.load(function(){
		  div.appendTo('body');
		  $(this).animate({'opacity':opts.opacity});
		});
		img.attr('src','/sm/images/xls2xformer.png');
	}
	return {
	  load: loadXformer,
	  pulse: function(cb){
	    if('function'!==typeof cb) {
	      var cb = function(){}
        }
	    img.animate({'opacity':1}, opts.pulseTime, function(){
	      img.animate({'opacity': opts.opacity}, opts.pulseTime, cb)
	    })
	  }
	}
})({opacity:0.69});

var PrettyShade = (function(){
	var bgSrc	=	"/sm/images/shading/bg-shade.png";
	function appearImage() {
		$('#tabs').css("padding", "10px 40px");
		$('#tabs').css("backgroundImage", "url("+bgSrc+")");
	}
	return appearImage;
})();

$(function(){
    xformer.load();
    if($(window).width()>800) {
    	PrettyShade();
    }
});
