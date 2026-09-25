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
var ids = ['low','high','pilot','full','buf','target'];
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
  /* What one finished cut shot works out to, given the board's provisional
     32 pilot / 361 full-film cut shots. The July 23 call put this at $80-450. */
  function check(label, rolls, cuts){
    if(!cuts) return '';
    var lo = rolls*v.low*buf/cuts, hi = rolls*v.high*buf/cuts;
    var off = hi < 80 || lo > 450;
    return '<div class="row sub"><span>' + label + '</span><span>' + money(lo) + '</span>'
      + '<span>' + money(hi) + '</span><span class="mid">'
      + (off ? 'outside $80–450' : 'within $80–450') + '</span></div>';
  }
  /* The verdict: does the film fit the hard-cost target? Judged on the high end,
     because a budget that only holds at the cheapest possible model is not a budget. */
  function verdict(){
    if(!v.target) return '';
    var hi = v.full*v.high*buf, lo = v.full*v.low*buf;
    var word, room;
    if(hi <= v.target){ word = 'fits'; room = (v.target/hi).toFixed(1) + '× headroom'; }
    else if(lo <= v.target){ word = 'fits at the low end'; room = 'over by ' + money(hi-v.target) + ' at the high'; }
    else { word = 'does not fit'; room = 'over by ' + money(lo-v.target) + ' even at the low'; }
    return '<div class="row big"><span>Against the ' + money(v.target) + ' target</span>'
      + '<span></span><span>' + room + '</span><span class="mid">' + word + '</span></div>';
  }
  document.getElementById('calcout').innerHTML =
    '<div class="row h"><span>Scope</span><span>Low</span><span>High</span><span>Mid</span></div>'
    + row('Pilot · base', v.pilot, 1)
    + row('Pilot · with buffer', v.pilot, buf, true)
    + row('Full film · base', v.full, 1)
    + row('Full film · with buffer', v.full, buf, true)
    + '<div class="row h"><span>Cross-check</span><span>Low</span><span>High</span><span>vs July 23</span></div>'
    + check('Per finished cut shot · pilot', v.pilot, 32)
    + check('Per finished cut shot · film', v.full, 361)
    + verdict();
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

/* Sheet-strip passes are still served from the generation CDN rather than from
   assets/img/exp/, so a load can fail (expired object, blocked network). Degrade
   to a labelled placeholder instead of a broken-image icon. */
function passFailed(img){
  var fig = img.closest('.pass');
  if(fig) fig.classList.add('missing');
}
[].slice.call(document.querySelectorAll('.pass img')).forEach(function(img){
  img.addEventListener('error', function(){ passFailed(img); });
  /* This file is deferred, so an image can finish failing before the listener is
     attached and never fire one. complete with no intrinsic width means it already
     errored -- check for that too rather than trusting the event alone. */
  if(img.complete && img.naturalWidth === 0) passFailed(img);
});

/* Lightbox. Every content image on the page opens in place rather than in a new
   tab. The .pass images are wrapped in a link to the full-size file and the
   reference frames are not, so the source is taken from the link where one
   exists (it is the higher-resolution original) and from the img otherwise.
   The link stays in the markup: with JS off, clicking still opens the file. */
var lb = null, lbGroup = [], lbAt = 0, lbReturn = null;

function lbSrc(img){
  var a = img.closest('a[href]');
  return (a && /\.(png|jpe?g|webp|gif|avif)(\?|$)/i.test(a.getAttribute('href')))
    ? a.getAttribute('href') : (img.currentSrc || img.src);
}
/* Captions differ by kind: a .pass figcaption is a bare label, a reference-wall
   one is a <b> title plus a <span> of prose. Reading textContent off both runs
   them together, so split the two parts and let the styling separate them. */
function lbCaption(img){
  var cap = img.closest('figure');
  cap = cap && cap.querySelector('figcaption');
  if(!cap) return {title: (img.alt || '').trim(), detail: ''};
  var b = cap.querySelector('b'), sp = cap.querySelector('span');
  if(b) return {title: b.textContent.trim(), detail: sp ? sp.textContent.trim() : ''};
  return {title: cap.textContent.trim(), detail: ''};
}
/* Arrow keys move within the row you opened from -- a character's passes, one
   reference grid -- rather than across the whole page, which would be useless. */
function lbScope(img){
  var box = img.closest('.passes, .vgrid, .heroreel, .grid2, .grid3') || img.closest('section');
  return [].slice.call(box ? box.querySelectorAll('img') : [img]);
}

function lbBuild(){
  lb = document.createElement('div');
  lb.className = 'lb';
  lb.setAttribute('role', 'dialog');
  lb.setAttribute('aria-modal', 'true');
  lb.innerHTML =
    '<button class="lb-x" aria-label="Close">Close</button>'
    + '<button class="lb-nav lb-prev" aria-label="Previous image">&#8249;</button>'
    + '<figure class="lb-fig"><img alt="">'
    + '<p class="lb-dead">This image could not be loaded.<br>'
    + '<a class="lb-open" target="_blank" rel="noopener">Open the file directly</a></p>'
    + '<figcaption><b></b><span></span></figcaption></figure>'
    + '<button class="lb-nav lb-next" aria-label="Next image">&#8250;</button>';
  document.body.appendChild(lb);
  lb.addEventListener('click', function(e){
    if(e.target.closest('.lb-x')) return lbClose();
    if(e.target.closest('.lb-prev')) return lbGo(-1);
    if(e.target.closest('.lb-next')) return lbGo(1);
    if(!e.target.closest('.lb-fig')) lbClose();   /* backdrop */
  });
}
function lbShow(){
  var img = lbGroup[lbAt];
  var full = lb.querySelector('img'), cap = lb.querySelector('figcaption');
  var src = lbSrc(img);
  lb.classList.remove('dead');
  lb.querySelector('.lb-open').href = src;
  full.onerror = function(){ lb.classList.add('dead'); };
  full.src = src;
  full.alt = img.alt || '';
  var c = lbCaption(img);
  cap.querySelector('b').textContent = c.title
    + (lbGroup.length > 1 ? '  ·  ' + (lbAt + 1) + ' of ' + lbGroup.length : '');
  var d = cap.querySelector('span');
  d.textContent = c.detail;
  d.hidden = !c.detail;
  var many = lbGroup.length > 1;
  lb.querySelector('.lb-prev').hidden = !many;
  lb.querySelector('.lb-next').hidden = !many;
}
function lbGo(d){
  lbAt = (lbAt + d + lbGroup.length) % lbGroup.length;
  lbShow();
}
function lbOpen(img){
  if(!lb) lbBuild();
  lbGroup = lbScope(img);
  lbAt = Math.max(0, lbGroup.indexOf(img));
  lbReturn = document.activeElement;
  lbShow();
  document.body.classList.add('lb-on');
  lb.classList.add('on');
  lb.querySelector('.lb-x').focus();
}
function lbClose(){
  if(!lb) return;
  lb.classList.remove('on');
  document.body.classList.remove('lb-on');
  lb.querySelector('img').removeAttribute('src');   /* stop a large download mid-flight */
  if(lbReturn && lbReturn.focus) lbReturn.focus();
}

document.addEventListener('click', function(e){
  var img = e.target.closest('main img');
  /* A pass whose image failed to load hides the img and shows a placeholder, so
     the click lands on the wrapping link instead. Catch that too, or it would
     open a tab -- the one behaviour this replaces. */
  if(!img){
    var a = e.target.closest('main a[href]');
    if(a && /\.(png|jpe?g|webp|gif|avif)(\?|$)/i.test(a.getAttribute('href'))) img = a.querySelector('img');
  }
  if(!img) return;
  e.preventDefault();
  lbOpen(img);
});
document.addEventListener('keydown', function(e){
  if(!lb || !lb.classList.contains('on')) return;
  if(e.key === 'Escape') lbClose();
  else if(e.key === 'ArrowLeft') lbGo(-1);
  else if(e.key === 'ArrowRight') lbGo(1);
  else if(e.key === 'Tab'){            /* keep focus inside the dialog */
    var f = [].slice.call(lb.querySelectorAll('button')).filter(function(b){ return !b.hidden; });
    var i = f.indexOf(document.activeElement);
    e.preventDefault();
    f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
  }
});
/* Images that are not inside a link have no keyboard affordance of their own. */
[].slice.call(document.querySelectorAll('main img')).forEach(function(img){
  if(img.closest('a[href]')) return;
  img.tabIndex = 0;
  img.setAttribute('role', 'button');
  img.addEventListener('keydown', function(e){
    if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); lbOpen(img); }
  });
});
