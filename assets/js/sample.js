/* The sample player.

   A beat is a run of footage that ends at a prompt. Its stills cross-fade on a
   loop so the story keeps moving underneath the prompt instead of freezing
   while you decide; the choices and the brief fade up a beat after it starts.

   Three targets are not literal beat ids:
     $back    return to the prompt you just answered — the fail states use this
     $<name>  read the target out of state, set earlier by data-set="name=beat"

   The frame library is ~30 MB, so a beat's frames only load when it plays.
   Whenever a beat starts, the frames of every beat you could reach from it are
   warmed in the background, which is what keeps the cut instant on click.
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
    warmNext(b);
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

  /* pull the frames of everywhere this beat can go into cache, quietly */
  var warmed = {};
  function warm(id){
    var b = beats[id];
    if(!b || warmed[id]) return;
    warmed[id] = true;
    [].slice.call(b.querySelectorAll('.stage img')).forEach(function(im){
      var pre = new Image();
      pre.src = im.getAttribute('src');
    });
  }
  function warmNext(b){
    [].slice.call(b.querySelectorAll('[data-go]')).forEach(function(go){
      warm(resolve(go.getAttribute('data-go')));
    });
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
