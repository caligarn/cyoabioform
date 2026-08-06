/* The sample player.

   A beat is a run of footage that ends at a prompt. Its stills cross-fade on a
   loop so the story keeps moving underneath the prompt instead of freezing
   while you decide; the choices and the brief fade up a beat after it starts.

   Three targets are not literal beat ids:
     $back    return to the prompt you just answered — the fail states use this
     $<name>  read the target out of state, set earlier by data-set="name=beat"
*/
var player = document.getElementById('player');
if(player){
  var HOLD = 2200;                 /* ms per still */
  var PROMPT = 2400;               /* ms before the choices fade up */
  var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var beats = {}, state = {}, from = 'start', cycle = null, prompt = null;
  [].slice.call(player.querySelectorAll('.beat')).forEach(function(b){
    beats[b.getAttribute('data-beat')] = b;
  });

  function play(id){
    var b = beats[id];
    if(!b) return;
    clearInterval(cycle); clearTimeout(prompt);
    Object.keys(beats).forEach(function(k){ beats[k].classList.toggle('on', k === id); });
    var imgs = [].slice.call(b.querySelectorAll('.stage img'));
    imgs.forEach(function(im, i){ im.classList.toggle('on', i === 0); });
    b.querySelector('.stage').style.setProperty('--run', (imgs.length * HOLD) + 'ms');
    if(calm){ b.classList.add('up'); return; }
    b.classList.remove('up');
    prompt = setTimeout(function(){ b.classList.add('up'); }, Math.min(PROMPT, imgs.length * HOLD));
    if(imgs.length < 2) return;
    var at = 0;
    cycle = setInterval(function(){
      imgs[at].classList.remove('on');
      at = (at + 1) % imgs.length;
      imgs[at].classList.add('on');
    }, HOLD);
  }

  function resolve(target){
    if(target === '$back') return from;
    return target.replace(/\$(\w+)/g, function(_, key){ return state[key] || ''; });
  }

  player.addEventListener('click', function(e){
    var go = e.target.closest('[data-go]');
    if(!go) return;
    var set = go.getAttribute('data-set');
    if(set){ var kv = set.split('='); state[kv[0]] = kv[1]; }
    var here = player.querySelector('.beat.on').getAttribute('data-beat');
    var next = resolve(go.getAttribute('data-go'));   /* reads the old `from` */
    from = here;
    if(next === 'start'){ state = {}; from = 'start'; }
    play(next);
  });

  play('start');
}
