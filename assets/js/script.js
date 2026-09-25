/* The script page has a sidebar of branches and nothing else to run. This is
   the hub's nav highlight and only that; site.js is not loaded here because
   it expects the board and the budget calculator to exist. */
var navLinks = {};
document.querySelectorAll('nav.side a[data-nav]').forEach(function(a){ navLinks[a.getAttribute('data-nav')] = a; });
var secs = [].slice.call(document.querySelectorAll('main section[id]'));
var navTick = false;
function navSync(){
  navTick = false;
  if(!secs.length) return;
  var line = window.innerHeight * 0.18, cur = secs[0];
  for(var i=0;i<secs.length;i++){
    if(secs[i].getBoundingClientRect().top <= line) cur = secs[i];
  }
  if(window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) cur = secs[secs.length-1];
  Object.keys(navLinks).forEach(function(k){ navLinks[k].classList.toggle('on', k === cur.id); });
  var on = navLinks[cur.id];
  if(on && on.scrollIntoViewIfNeeded){ on.scrollIntoViewIfNeeded(false); }
}
window.addEventListener('scroll', function(){
  if(!navTick){ navTick = true; requestAnimationFrame(navSync); }
}, {passive:true});
window.addEventListener('resize', navSync);
navSync();
