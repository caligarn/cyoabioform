document.addEventListener('click', function(e){
  var b = e.target.closest('button.copy');
  if(!b) return;
  var t = b.getAttribute('data-copy');
  var done = function(){ var o=b.textContent; b.textContent='Copied'; b.classList.add('done');
    setTimeout(function(){ b.textContent=o; b.classList.remove('done'); },1400); };
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(t).then(done, function(){fallback(t,done);});
  } else { fallback(t,done); }
});
function fallback(t,cb){
  var ta=document.createElement('textarea'); ta.value=t; ta.style.position='fixed'; ta.style.opacity='0';
  document.body.appendChild(ta); ta.select();
  try{ document.execCommand('copy'); cb(); }catch(err){}
  document.body.removeChild(ta);
}

/* scene board filter */
var q = document.getElementById('q');
var rows = Array.prototype.slice.call(document.querySelectorAll('#board-t tbody tr'));
var cnt = document.getElementById('cnt');
var actFilter = '*';
function applyFilter(){
  var term = (q.value||'').toLowerCase().trim();
  var n = 0;
  rows.forEach(function(r){
    var okA = actFilter === '*' || r.getAttribute('data-act') === actFilter;
    var okQ = !term || r.getAttribute('data-hay').indexOf(term) !== -1;
    var show = okA && okQ;
    r.classList.toggle('hide', !show);
    if(show) n++;
  });
  cnt.textContent = n + ' of ' + rows.length + ' scenes';
}
q.addEventListener('input', applyFilter);
document.querySelectorAll('.chip[data-act]').forEach(function(c){
  c.addEventListener('click', function(){
    document.querySelectorAll('.chip[data-act]').forEach(function(x){x.classList.remove('on');});
    c.classList.add('on'); actFilter = c.getAttribute('data-act'); applyFilter();
  });
});
applyFilter();

/* budget */
var ids = ['low','high','pilot','full','buf'];
function el(i){ return document.getElementById('c_'+i); }
function money(n){ return '$' + Math.round(n).toLocaleString('en-US'); }
function calc(){
  var v = {};
  ids.forEach(function(i){ v[i] = parseFloat(el(i).value) || 0; });
  var buf = 1 + v.buf/100;
  function row(label, shots, mult, big){
    var lo = shots*v.low*mult, hi = shots*v.high*mult, mid = (lo+hi)/2;
    return '<div class="row'+(big?' big':'')+'"><span>'+label+'</span><span>'+money(lo)+'</span>'
      +'<span>'+money(hi)+'</span><span class="mid">'+money(mid)+'</span></div>';
  }
  document.getElementById('calcout').innerHTML =
    '<div class="row h"><span>Scope</span><span>Low</span><span>High</span><span>Mid</span></div>'
    + row('Pilot · base', v.pilot, 1)
    + row('Pilot · with buffer', v.pilot, buf, true)
    + row('Full film · base', v.full, 1)
    + row('Full film · with buffer', v.full, buf, true);
}
ids.forEach(function(i){ el(i).addEventListener('input', calc); });
calc();

/* nav highlight */
var navLinks = {};
document.querySelectorAll('nav.side a[data-nav]').forEach(function(a){ navLinks[a.getAttribute('data-nav')] = a; });
var secs = [].slice.call(document.querySelectorAll('main section[id]'));
var navTick = false;
function navSync(){
  navTick = false;
  var line = window.innerHeight * 0.18, cur = secs[0];
  for(var i=0;i<secs.length;i++){
    if(secs[i].getBoundingClientRect().top <= line) cur = secs[i];
  }
  if(window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) cur = secs[secs.length-1];
  Object.keys(navLinks).forEach(function(k){ navLinks[k].classList.toggle('on', k === cur.id); });
}
window.addEventListener('scroll', function(){
  if(!navTick){ navTick = true; requestAnimationFrame(navSync); }
}, {passive:true});
window.addEventListener('resize', navSync);
navSync();

/* sample player */
/* Each beat is a run of footage that loops until you answer it, the way the
   film keeps playing underneath a prompt. Stills stand in for the footage. */
var sam = document.getElementById('sampler');
if(sam){
  var HOLD = 2200;                 /* ms per still */
  var PROMPT = 2400;               /* ms before the choices fade up */
  var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var beats = {}, cycle = null, prompt = null;
  [].slice.call(sam.querySelectorAll('.beat')).forEach(function(b){
    beats[b.getAttribute('data-beat')] = b;
  });

  function samPlay(id){
    clearInterval(cycle); clearTimeout(prompt);
    Object.keys(beats).forEach(function(k){ beats[k].classList.toggle('on', k === id); });
    var b = beats[id];
    var imgs = [].slice.call(b.querySelectorAll('.stage img'));
    var choices = b.querySelector('.choices');
    imgs.forEach(function(im, i){ im.classList.toggle('on', i === 0); });
    b.querySelector('.stage').style.setProperty('--run', (imgs.length * HOLD) + 'ms');
    if(calm){ choices.classList.add('up'); return; }
    choices.classList.remove('up');
    prompt = setTimeout(function(){ choices.classList.add('up'); }, Math.min(PROMPT, imgs.length * HOLD));
    if(imgs.length < 2) return;
    var at = 0;
    cycle = setInterval(function(){
      imgs[at].classList.remove('on');
      at = (at + 1) % imgs.length;
      imgs[at].classList.add('on');
    }, HOLD);
  }

  sam.addEventListener('click', function(e){
    var go = e.target.closest('[data-go]');
    if(go){ samPlay(go.getAttribute('data-go')); return; }
    if(e.target.closest('[data-restart]')) samPlay('start');
  });
  samPlay('start');
}
