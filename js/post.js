$( ".wrap .post" ).each(function() {
  // alert(this.id)
  this.load( "posts/" + this.id )
})
