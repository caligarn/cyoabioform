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
  /* Cross-check against the figure this model replaced: what one finished cut shot
     works out to, given the board's provisional 32 pilot / 361 full-film cut shots.
     If it lands outside $80-450, either the roll price or that range is wrong. */
  function check(label, rolls, cuts){
    if(!cuts) return '';
    var lo = rolls*v.low*buf/cuts, hi = rolls*v.high*buf/cuts;
    var off = hi < 80 || lo > 450;
    return '<div class="row sub"><span>' + label + '</span><span>' + money(lo) + '</span>'
      + '<span>' + money(hi) + '</span><span class="mid">'
      + (off ? 'outside $80–450' : 'within $80–450') + '</span></div>';
  }
  document.getElementById('calcout').innerHTML =
    '<div class="row h"><span>Scope</span><span>Low</span><span>High</span><span>Mid</span></div>'
    + row('Pilot · base', v.pilot, 1)
    + row('Pilot · with buffer', v.pilot, buf, true)
    + row('Full film · base', v.full, 1)
    + row('Full film · with buffer', v.full, buf, true)
    + '<div class="row h"><span>Cross-check</span><span>Low</span><span>High</span><span>vs July 23</span></div>'
    + check('Per finished cut shot · pilot', v.pilot, 32)
    + check('Per finished cut shot · film', v.full, 361);
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

/* ways to join: build the lane picker from the cards, and keep the mailto in sync */
var jbLane = document.getElementById('jb-lane');
if(jbLane){
  var jbNote = document.getElementById('jb-note');
  var jbSend = document.getElementById('jb-send');
  var lanes = [].slice.call(document.querySelectorAll('#join .card.lane')).map(function(c){
    return {lane: c.getAttribute('data-lane'), task: c.getAttribute('data-task')};
  });
  lanes.forEach(function(l){
    var o = document.createElement('option');
    o.value = l.lane; o.textContent = l.lane;
    jbLane.appendChild(o);
  });
  function jbSync(){
    var picked = lanes.filter(function(l){ return l.lane === jbLane.value; })[0];
    var lane = picked ? picked.lane : 'not sure yet';
    var task = picked ? picked.task : 'whatever is most useful';
    var body = 'Hi Minh,\n\nI’d like to take a lane on CYOA: The Bioform.\n\n'
      + 'Lane: ' + lane + '\nFirst task I’d take: ' + task + '\n\n'
      + (jbNote.value.trim() ? jbNote.value.trim() + '\n' : 'Who I am:\nSomething I’ve made:\nTools I already pay for:\n');
    jbSend.href = 'mailto:minh@fantastic.day?subject=' + encodeURIComponent('CYOA: The Bioform — ' + lane)
      + '&body=' + encodeURIComponent(body);
  }
  jbLane.addEventListener('change', jbSync);
  jbNote.addEventListener('input', jbSync);
  jbSync();
}
