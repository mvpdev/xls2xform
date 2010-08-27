var PrettyShade = (function(){
	var bgSrc	=	"/sm/images/shading/bg-shade.png";
	function appearImage() {
		$('#tabs').css("padding", "10px 40px");
		$('#tabs').css("backgroundImage", "url("+bgSrc+")");
	}
	return appearImage;
})();

if($(window).width()>800) {
	PrettyShade();
}