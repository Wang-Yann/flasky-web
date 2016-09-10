
$('#bottom').click(function() {
var hash = (!window.location.hash)? "#top":window.location.hash;
console.log(hash);
if ( hash === '#top' )
{
window.location.hash = '';  //防止刷新时，又回到锚点处
window.scrollTo(10,10); 
}
});   

$(document).ready(function(){
$('.nav li a').each(function(){
        $this=$(this);
        if ($this[0].href==String(window.location))
        {
        $this.parent().addClass('active');
        
            };
    })


});
	
  

    
    


