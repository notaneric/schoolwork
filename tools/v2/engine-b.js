const TOTAL_RECALLABLE = Q.length + GLOSSARY.length; // 118 + 94 = 212

// ===== icons (one inline-SVG line set, defined in <defs> at the top of <body>) =====
const ic=(n,cls='ic')=>`<svg class="${cls}" aria-hidden="true"><use href="#i-${n}"/></svg>`;

// ===== review pointers =====
const L=['A','B','C','D','E'];
function khanFor(q){ return q.khan || KHAN[q.lec] || null; }
function pointerRows(q){
  const rows=[];
  if(q.lec) rows.push(`<span class="row">${ic('book','ic ic-16')}<span>Review: ${q.lec}.</span></span>`);
  const k=khanFor(q);
  if(k) rows.push(`<span class="row">${ic('play','ic ic-16')}<a href="https://youtu.be/${k[0]}" target="_blank" rel="noopener">${k[1]}</a></span>`);
  if(q.vid) rows.push(`<span class="row">${ic('play','ic ic-16')}<a href="${q.vid.u}" target="_blank" rel="noopener">Prof. Meyers: ${q.vid.t}</a></span>`);
  return rows.length ? `<div class="lec">${rows.join('')}</div>` : '';
}

// ===== utilities =====
function shuffleArr(a){ for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; }
function hash(s){ let h=0; for(let i=0;i<s.length;i++){ h=(Math.imul(h,31)+s.charCodeAt(i))|0; } return (h>>>0).toString(36); }
function escapeHtml(s){ return s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
const STOP=new Set(['the','a','an','of','to','is','it','in','on','and','or','its','with','that','so','as','are','by','for','than','from','not','be','no','at','into','only','how','which','when','their','they','this','more','less','higher','lower','over','time']);
function keywords(s){ return [...new Set(s.toLowerCase().replace(/[^a-z0-9\s]/g,' ').split(/\s+/).filter(w=>w.length>2&&!STOP.has(w)))]; }
function highlightHits(model, ans){
  const have=new Set(keywords(ans));
  return escapeHtml(model).replace(/[A-Za-z][A-Za-z0-9-]+/g, w =>
    have.has(w.toLowerCase()) ? `<span class="hit">${w}</span>` : w);
}
const PIN_RE=/none of the above|not enough info|nothing needs to happen/i;
function buildPerm(q){
  const n=q.o.length, idx=[...Array(n).keys()];
  if(q.nosh) return idx;
  const pinned=idx.filter(i=>PIN_RE.test(q.o[i]));
  const free=shuffleArr(idx.filter(i=>!pinned.includes(i)));
  return [...free,...pinned];
}
function filtered(){ return Q.map((q,gi)=>({q,gi})).filter(x=>FCH==='all'||x.q.chId===FCH); }
// interleave so no two consecutive items share a chapter
function interleave(a){
  if(a.length<3) return shuffleArr(a);
  shuffleArr(a);
  const groups={}; a.forEach(x=>{ (groups[x.q.chId]=groups[x.q.chId]||[]).push(x); });
  const out=[]; let last=null;
  // optimal greedy: each step take from the chapter with the most items left that isn't `last`
  for(let n=0;n<a.length;n++){
    const keys=shuffleArr(Object.keys(groups).filter(k=>groups[k].length));
    let best=null,bc=-1;
    for(const k of keys){ if(k===last) continue; if(groups[k].length>bc){ bc=groups[k].length; best=k; } }
    if(best===null) best=keys[0];            // only `last` chapter remains (unavoidable adjacency)
    out.push(groups[best].pop()); last=best;
    if(!groups[best].length) delete groups[best];
  }
  return out;
}
const REDUCED=()=>!!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches);

// ===== audio + haptics (feedback, not decoration) =====
let actx=null; const getCtx=()=>{ if(!actx) actx=new (window.AudioContext||window.webkitAudioContext)(); return actx; };
function tone(f,type,v,s,d){ try{ const c=getCtx(),o=c.createOscillator(),g=c.createGain(); o.connect(g);g.connect(c.destination);
  o.type=type;o.frequency.value=f; g.gain.setValueAtTime(0,c.currentTime+s); g.gain.linearRampToValueAtTime(v,c.currentTime+s+.015);
  g.gain.exponentialRampToValueAtTime(.0001,c.currentTime+s+d); o.start(c.currentTime+s); o.stop(c.currentTime+s+d+.01);}catch(e){} }
const playCorrect=()=>{tone(523,'sine',.13,0,.4);tone(659,'sine',.11,.07,.38);tone(784,'sine',.1,.14,.36);};
const playWrong=()=>{tone(200,'sawtooth',.11,0,.15);tone(160,'sawtooth',.09,.12,.2);};
const playClick=()=>{tone(880,'sine',.045,0,.06);};
const playFinish=()=>{[523,659,784,1047].forEach((f,i)=>tone(f,'sine',.15,i*.13,.5));};
const vibe=p=>{try{navigator.vibrate&&navigator.vibrate(p);}catch(e){}};

// ===== persistence (light, robust: keyed by content hash; keys unchanged from the S137 build) =====
function lsGet(k,def){ try{ const v=localStorage.getItem(k); return v==null?def:JSON.parse(v); }catch(e){ return def; } }
function lsSet(k,v){ try{ localStorage.setItem(k,JSON.stringify(v)); }catch(e){} }
let stars = new Set(lsGet('chem1211u1_stars',[]));
function saveStars(){ lsSet('chem1211u1_stars',[...stars]); }
// recalled-from-cold: only items produced from memory (Learn master OR Recall "Got it")
let recalled = new Set(lsGet('chem1211u1_recalled_v1',[]));
function saveRecalled(){ lsSet('chem1211u1_recalled_v1',[...recalled]); }
function qId(q){ return 'q'+hash(q.q+'|'+q.o.join('~')+'|'+(q.d||'')); }
function gId(g){ return 'g'+hash(g.t); }

// ===== state =====
let FCH='all', MODE='home', HTAB='study';
const screens=['home','flash','learn','match','recall','videos','close'];
function show(id){ screens.forEach(s=>document.getElementById(s).classList.toggle('on', s===id)); MODE=id; }
function setBar(pct){ const b=document.getElementById('top-bar'); b.style.display=pct>=0?'block':'none'; b.firstElementChild.style.width=Math.max(0,Math.min(100,pct))+'%'; }

// ===== session tally (for the close card; never persisted, never gamified) =====
let SES={mode:null,answers:0,seen:new Set(),cold:new Set(),miss:{},seenCh:{},closed:false};
function sesStart(mode){ SES={mode,answers:0,seen:new Set(),cold:new Set(),miss:{},seenCh:{},closed:false}; }
function sesLog(id,ch,ok,cold){
  SES.answers++; SES.seen.add(id); SES.seenCh[ch]=(SES.seenCh[ch]||0)+1;
  if(cold) SES.cold.add(id);
  if(!ok) SES.miss[ch]=(SES.miss[ch]||0)+1;
}
function sesWeakest(){
  let best=null, br=0, bm=0;
  for(const ch in SES.seenCh){ const m=SES.miss[ch]||0, r=m/SES.seenCh[ch];
    if(m>0 && (r>br || (r===br && m>bm))){ best=ch; br=r; bm=m; } }
  return best;
}
const PILE_CHECK_SVG='<svg class="ic draw" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="14" width="18" height="6" rx="1.5"/><path d="M5.5 10.5h13"/><path class="chk" d="m9 5.5 2 2 4-4"/></svg>';
function renderClose(o){
  const weak=sesWeakest();
  const wl = weak ? `Weakest chapter: <b>${SHORT[weak]}</b>, start here next` : 'No chapter missed this session';
  const el=document.getElementById('close');
  el.innerHTML=`<div class="close-card" role="status">
    <div class="close-k">${o.kicker}</div>
    <div class="close-t">${o.title}</div>
    <p class="close-s">${o.sub}</p>
    <div class="stats">
      <div class="stat g">${PILE_CHECK_SVG}<span class="n" data-n="${o.g}">0</span><span class="l">${o.gl}</span></div>
      <div class="stat a">${ic('pile')}<span class="n" data-n="${o.a}">0</span><span class="l">${o.al}</span></div>
      <div class="stat w">${ic('flag')}<span class="l">${wl}</span></div>
    </div>
    <div class="close-actions">${o.actions.map(a=>`<button class="btn ${a.primary?'btn-primary':'btn-ghost'}" onclick="${a.fn}">${a.label}</button>`).join('')}</div>
  </div>`;
  clearInterval(mTimer); setBar(-1); show('close'); window.scrollTo(0,0);
  countUp(el);
}
function countUp(root){
  const els=[...root.querySelectorAll('.n[data-n]')];
  if(REDUCED()){ els.forEach(e=>e.textContent=e.dataset.n); return; }
  const t0=performance.now(), D=600;
  const step=now=>{ const p=Math.min(1,(now-t0)/D), e=1-Math.pow(1-p,4);
    els.forEach(el=>el.textContent=Math.round(+el.dataset.n*e)); if(p<1) requestAnimationFrame(step); else els.forEach(el=>el.textContent=el.dataset.n); };
  requestAnimationFrame(step);
}
// "<- Set" after >= 5 answers, or a Learn/Recall round ending, shows the summary before home.
function sesClose(kind){
  SES.closed=true;
  const cold=SES.cold.size, learning=SES.seen.size-cold, back={label:'Back to set',fn:'goHome()',primary:true};
  if(kind==='exit') renderClose({kicker:SES.mode==='exam'?'Mixed Exam, stopped early':(SES.mode==='recall'?'Recall, stopped early':'Learn, stopped early'),
    title:`Recalled ${cold} from cold`, sub:'Only answers you produced from memory count. The rest come back next time.',
    g:cold, gl:'recalled from cold', a:learning, al:'still learning', actions:[back]});
  else if(kind==='round') renderClose({kicker:'Learn', title:`Round ${lnRound} done`,
    sub:"Every item you didn't produce twice comes back. That repetition is the point.",
    g:cold, gl:'recalled from cold', a:learning, al:'still learning',
    actions:[{label:'Back to set',fn:'goHome()'},{label:'Next round',fn:'nextRound()',primary:true}]});
  else if(kind==='finish') renderClose({kicker:'Learn complete', title:`All ${LN.length} recalled from cold`,
    sub:'You produced every answer from memory at least twice. That is the kind of studying that transfers to the exam.',
    g:cold, gl:'recalled from cold', a:learning, al:'still learning', actions:[back]});
  else if(kind==='exam'){
    const pct=Math.round(examScore/lnQ.length*100), cm=LN.filter(x=>x.cm).length;
    const msg = pct>=90?'Exam-strong. Do a Recall pass on anything below to lock it.' : pct>=75?'Solid. Clean up the misses in Learn.' : 'Keep going. Run Learn on the weak chapters.';
    renderClose({kicker:'Mixed Exam', title:`${examScore} of ${lnQ.length} correct (${pct}%)`,
      sub:msg+(cm?` <b>${cm}</b> you were confident on but missed. Start there.`:''),
      g:examScore, gl:'correct', a:lnQ.length-examScore, al:'missed', actions:[back]});
  }
  else if(kind==='recall') renderClose({kicker:'Recall complete', title:`Recalled ${rcGot} of ${rc.length} from cold`,
    sub:'Only the ones you produced from a blank count. Come back and the misses will feel easier.',
    g:rcGot, gl:'recalled from cold', a:rc.length-rcGot, al:'still learning', actions:[back]});
  if(kind!=='exit'&&kind!=='round') playFinish();
}

// ===== HOME =====
function renderProgress(){
  document.getElementById('rc-n').textContent=recalled.size;
  document.getElementById('rc-of').textContent=`of ${TOTAL_RECALLABLE}`;
}
function renderHome(){
  const counts={all:Q.length}; CHAPTERS.forEach(c=>counts[c.id]=Q.filter(q=>q.chId===c.id).length);
  const chips=[{id:'all',short:'All'}].concat(CHAPTERS.map(c=>({id:c.id,short:c.short})));
  document.getElementById('chips').innerHTML = chips.map(c=>
    `<button class="chip ${FCH===c.id?'active':''}" aria-pressed="${FCH===c.id}" onclick="setFilter('${c.id}')">${c.short}<span class="cc">${counts[c.id]}</span></button>`).join('');
  const gl=GLOSSARY.filter(g=>FCH==='all'||g.ch===FCH);
  const nq=(FCH==='all'?Q.length:counts[FCH]);
  document.getElementById('m-q').textContent = nq;
  document.getElementById('m-q2').textContent = nq;
  document.getElementById('m-t').textContent = gl.length;
  document.getElementById('m-t2').textContent = gl.length;
  document.getElementById('m-ch').textContent = FCH==='all' ? `${CHAPTERS.length} chapters` : SHORT[FCH];
  renderTerms();
  renderProgress();
}
function renderTerms(){
  if(document.getElementById('panel-terms').hidden) return;
  const f=(document.getElementById('term-filter').value||'').trim().toLowerCase();
  const gl=GLOSSARY.filter(g=>(FCH==='all'||g.ch===FCH) && (!f || (g.t+' '+g.d).toLowerCase().includes(f)));
  document.getElementById('term-list').innerHTML = gl.length
    ? gl.map(g=>`<div class="term"><div class="t">${g.t}</div><div class="d">${g.d}</div></div>`).join('')
    : `<div class="terms-empty">No terms match "${escapeHtml(f)}" in this chapter.</div>`;
}
function setTab(t){ HTAB=t; playClick();
  document.getElementById('panel-study').hidden = t!=='study';
  document.getElementById('panel-terms').hidden = t!=='terms';
  ['study','terms'].forEach(k=>{ const b=document.getElementById('tab-'+k); b.classList.toggle('on',k===t); b.setAttribute('aria-selected', k===t?'true':'false'); });
  if(t==='terms') renderTerms();
}
function setFilter(id){ FCH=id; playClick(); renderHome(); }
function enter(mode){ playClick();
  if(mode==='recall'){ sesStart('recall'); recallInit(); }
  else if(mode==='flash') fcInit();
  else if(mode==='learn'){ sesStart('learn'); learnInit(false); }
  else if(mode==='exam'){ sesStart('exam'); learnInit(true); }
  else if(mode==='match'){ show('match'); matchStart(); }
  else if(mode==='videos') videosInit();
}
function goHome(){
  if((MODE==='learn'||MODE==='recall') && SES.answers>=5 && !SES.closed){ sesClose('exit'); return; }
  playClick(); clearInterval(mTimer); setBar(-1); show('home'); renderHome(); window.scrollTo(0,0);
}

// ===== FLASHCARDS (Preview — recognition, non-mastery) =====
let fc=[], fi=0, fFlip=false;
function fcInit(){ fc=filtered(); fi=0; fFlip=false; setBar(-1); show('flash'); fcRender(); window.scrollTo(0,0); }
function fcRender(){
  const {q,gi}=fc[fi];
  document.getElementById('fc-kick-f').textContent = SHORT[q.chId];
  const d=document.getElementById('fc-diagram');
  if(q.d){ d.innerHTML=q.d; d.style.display='block'; } else { d.style.display='none'; d.innerHTML=''; }
  document.getElementById('flashcard').classList.toggle('has-diagram', !!q.d);
  document.getElementById('fc-q').innerHTML = q.q;
  document.getElementById('fc-a').innerHTML = q.o[q.a];
  document.getElementById('fc-exp').innerHTML = q.e + pointerRows(q);
  document.getElementById('fc-star').classList.toggle('on', stars.has(gi));
  document.getElementById('fc-count').textContent = `${fi+1} of ${fc.length}`;
  document.getElementById('fc-progress').textContent = `${fi+1} of ${fc.length}`;
  document.getElementById('fc-prev').disabled = fi===0;
  document.getElementById('fc-next').disabled = fi===fc.length-1;
  fFlip=false; document.getElementById('flashcard').classList.remove('flipped');
}
function fcFlip(){ fFlip=!fFlip; document.getElementById('flashcard').classList.toggle('flipped',fFlip); playClick(); }
function fcNav(dir){ const n=fi+dir; if(n<0||n>=fc.length) return; fi=n; fcRender(); playClick(); vibe([15]); }
function fcStar(){ const gi=fc[fi].gi; if(stars.has(gi)) stars.delete(gi); else { stars.add(gi); vibe([25]);} saveStars(); document.getElementById('fc-star').classList.toggle('on',stars.has(gi)); }
function fcShuffle(){ shuffleArr(fc); fi=0; fcRender(); playClick(); }

// ===== LEARN + MIXED EXAM (produce-then-reveal, effortful retirement, interleaved) =====
let LN=[], lnQ=[], lnPos=0, lnRound=0, lnStage='produce', lnConf=null, lnProduced=false, lnDone=false, examMode=false, examScore=0, lnStageAt=0;
const ROUND=7;
function learnInit(exam){
  examMode=!!exam;
  LN = filtered().map(x=>({q:x.q, id:qId(x.q), status:'new', c:0, pc:0, cm:false}));
  lnRound=0; examScore=0; show('learn');
  document.getElementById('learn-title').textContent = examMode ? 'Mixed Exam' : 'Learn';
  setPileLabels();
  if(examMode){ lnQ=interleave(LN.slice()); lnQ.forEach(x=>x.perm=buildPerm(x.q)); lnPos=0; startStage(); }
  else buildRound();
  window.scrollTo(0,0);
}
function setPileLabels(){
  const lab = examMode ? ['Remaining','Missed','Correct'] : ['Remaining','Still learning','Mastered'];
  ['l-remain','l-learn','l-master'].forEach((id,i)=>document.getElementById(id).textContent=lab[i]);
}
function notMastered(){ return LN.filter(x=>x.status!=='master'); }
function tally(){ return {master:LN.filter(x=>x.status==='master').length, learn:LN.filter(x=>x.status==='learning').length, remain:LN.filter(x=>x.status==='new').length}; }
function updateMastery(){
  const tot=LN.length; let c;
  if(examMode){ const answered=lnPos+(lnDone?1:0); c={master:examScore, learn:answered-examScore, remain:tot-answered}; }
  else c=tally();
  document.getElementById('bar-master').style.width=(c.master/tot*100)+'%';
  document.getElementById('bar-learn').style.width=(c.learn/tot*100)+'%';
  document.getElementById('bar-remain').style.width=(c.remain/tot*100)+'%';
  document.getElementById('c-remain').textContent=c.remain;
  document.getElementById('c-learn').textContent=c.learn;
  document.getElementById('c-master').textContent=c.master;
  setBar(examMode ? (lnPos+(lnDone?1:0))/lnQ.length*100 : -1);
}
function buildRound(){
  const pool=notMastered();
  if(!pool.length){ learnFinish(); return; }
  lnRound++;
  const cmiss=shuffleArr(pool.filter(x=>x.cm));
  const learn=shuffleArr(pool.filter(x=>x.status==='learning'&&!x.cm));
  const fresh=shuffleArr(pool.filter(x=>x.status==='new'));
  const cmFront=cmiss.slice(0,ROUND);
  const rest=interleave([...learn,...fresh]).slice(0,Math.max(0,ROUND-cmFront.length));
  lnQ=[...cmFront,...rest];
  lnQ.forEach(x=>x.perm=buildPerm(x.q));
  lnPos=0;
  startStage();
}
function nextRound(){ playClick(); SES.closed=false; show('learn'); buildRound(); window.scrollTo(0,0); }
function startStage(){ lnStage='produce'; lnConf=null; lnProduced=false; lnDone=false; lnStageAt=performance.now(); renderLearn(); }
function renderLearn(){
  const it=lnQ[lnPos], q=it.q;
  updateMastery();
  document.getElementById('learn-round').textContent = examMode ? `${lnPos+1} of ${lnQ.length}` : 'Round '+lnRound;
  document.getElementById('learn-kick').textContent = SHORT[q.chId];
  document.getElementById('learn-pos').textContent = `Question ${lnPos+1} of ${lnQ.length}`;
  const d=document.getElementById('learn-diagram');
  if(q.d){ d.innerHTML=q.d; d.style.display='block'; } else { d.style.display='none'; d.innerHTML=''; }
  document.getElementById('learn-q').innerHTML=q.q;
  // produce stage
  document.getElementById('learn-produce').style.display='block';
  document.getElementById('learn-input').value='';
  document.querySelectorAll('#learn-produce .conf').forEach(c=>c.classList.remove('on'));
  const grid=document.getElementById('learn-opts'); grid.style.display='none'; grid.innerHTML='';
  const fb=document.getElementById('learn-fb'); fb.style.display='none'; fb.className='fb';
  document.getElementById('learn-next').style.display='none';
  const card=document.getElementById('learn-card'); card.style.animation='none'; void card.offsetWidth; card.style.animation='rise .2s cubic-bezier(.25,1,.5,1) both';
  window.scrollTo({top:0,behavior:'smooth'});
}
function setConf(c){ lnConf=c; document.querySelectorAll('#learn-produce .conf').forEach(b=>b.classList.toggle('on',b.dataset.c===c)); }
function revealOptions(){
  if(lnStage!=='produce') return;
  const it=lnQ[lnPos], q=it.q;
  lnProduced = document.getElementById('learn-input').value.trim().length>=2;
  if(!lnConf) lnConf='guess';
  lnStage='recognize';
  document.getElementById('learn-produce').style.display='none';
  const grid=document.getElementById('learn-opts'); grid.style.display='flex';
  it.perm.forEach((oi,pos)=>{ const b=document.createElement('button'); b.className='opt'; b.dataset.orig=oi;
    b.innerHTML=`<span class="opt-l">${L[pos]}</span><span class="opt-txt">${q.o[oi]}</span>`; b.onclick=()=>learnPick(oi); grid.appendChild(b); });
  playClick(); window.scrollTo({top:document.getElementById('learn-opts').offsetTop-80,behavior:'smooth'});
}
function optByOrig(o){ return [...document.querySelectorAll('#learn-opts .opt')].find(b=>+b.dataset.orig===o); }
function learnPick(origIdx){
  if(lnStage!=='recognize'||lnDone) return; lnDone=true; playClick();
  const it=lnQ[lnPos], q=it.q, ok=origIdx===q.a;
  [...document.querySelectorAll('#learn-opts .opt')].forEach(b=>b.disabled=true);
  let becameMaster=false;
  if(ok){
    it.c++; if(lnProduced) it.pc++; it.cm=false;
    if(it.c>=2 && it.pc>=1 && it.status!=='master'){ it.status='master'; becameMaster=true; recalled.add(it.id); saveRecalled(); }
    else if(it.status!=='master') it.status='learning';
    playCorrect(); vibe([40]);
    if(examMode) examScore++;
  } else {
    const w=optByOrig(origIdx); w.classList.add('wrong'); w.querySelector('.opt-l').innerHTML=ic('x','ic ic-16');
    if(it.status!=='master') it.status='learning';
    if(lnConf==='sure') it.cm=true;
    playWrong(); vibe([120,40,120]);
  }
  // the correct option is the only saturated element, whichever was picked
  const right=optByOrig(q.a); right.classList.add('correct'); right.querySelector('.opt-l').innerHTML=ic('check','ic ic-16');
  sesLog(it.id, q.chId, ok, becameMaster);
  updateMastery(); renderProgress();
  const fb=document.getElementById('learn-fb'); fb.style.display='block'; fb.className='fb '+(ok?'ok':'no');
  document.getElementById('learn-fb-l').innerHTML = (ok?ic('check','ic ic-16'):ic('x','ic ic-16')) + '<span>' + (ok
    ? (becameMaster?'Correct, and recalled from cold':'Correct. Produce it once more to lock it in')
    : (lnConf==='sure'?'You were Certain, and wrong. This one comes back first':'Not quite, it stays in the deck')) + '</span>';
  const wrote = lnProduced ? `<div class="your-answer">You answered: <b>${escapeHtml(document.getElementById('learn-input').value.trim())}</b></div>` : '';
  document.getElementById('learn-fb-t').innerHTML = q.e + wrote + pointerRows(q);
  const nb=document.getElementById('learn-next'); nb.style.display='flex';
  nb.textContent = lnPos<lnQ.length-1 ? 'Continue' : (examMode ? 'See exam score' : (notMastered().length?'Finish round':'See results'));
}
function learnNext(){ playClick(); vibe([15]); lnPos++;
  if(lnPos>=lnQ.length){ examMode ? examDone() : roundDone(); }
  else startStage();
}
function roundDone(){
  const c=tally();
  if(c.master===LN.length){ learnFinish(); return; }
  sesClose('round');
}
function learnFinish(){ sesClose('finish'); }
function examDone(){ sesClose('exam'); }

// ===== RECALL (typed produce-from-memory over the glossary) =====
let rc=[], ri=0, rcDir='td', rcGot=0, rcMiss=0;
function recallInit(){ rc=shuffleArr(GLOSSARY.filter(g=>FCH==='all'||g.ch===FCH).slice()); ri=0; rcGot=0; rcMiss=0; setBar(-1); show('recall');
  recallRender(); window.scrollTo(0,0);
}
function recallRender(){
  const g=rc[ri];
  document.getElementById('rc-count').textContent=`${ri+1} of ${rc.length}`;
  document.getElementById('rc-strip-got').style.width=(rcGot/rc.length*100)+'%';
  document.getElementById('rc-strip-miss').style.width=(rcMiss/rc.length*100)+'%';
  document.getElementById('rc-dir').textContent = rcDir==='td'?'Term to definition':'Definition to term';
  document.getElementById('rc-prompt-l').textContent = rcDir==='td'?'Define this term':'Name this term';
  document.getElementById('rc-term').textContent = rcDir==='td'? g.t : g.d;
  const inp=document.getElementById('rc-input'); inp.value=''; inp.disabled=false;
  document.getElementById('rc-reveal-btn').style.display='flex';
  document.getElementById('rc-reveal').style.display='none';
  window.scrollTo({top:0,behavior:'smooth'});
}
function recallReveal(){
  const inp=document.getElementById('rc-input');
  if(inp.value.trim().length<1){ inp.focus(); return; }
  const g=rc[ri], model = rcDir==='td'? g.d : g.t;
  document.getElementById('rc-model').innerHTML = highlightHits(model, inp.value);
  document.getElementById('rc-yours').innerHTML = `You wrote: <b>${escapeHtml(inp.value.trim())}</b>`;
  document.getElementById('rc-reveal').style.display='block';
  document.getElementById('rc-reveal-btn').style.display='none';
  inp.disabled=true; playClick();
  window.scrollTo({top:document.getElementById('rc-reveal').offsetTop-60,behavior:'smooth'});
}
function recallGrade(grade){
  const g=rc[ri], id=gId(g);
  if(grade==='got'){ recalled.add(id); rcGot++; playCorrect(); vibe([30]); }
  else { recalled.delete(id); rcMiss++; if(grade==='miss'){ playWrong(); vibe([90]); } }
  sesLog(id, g.ch, grade==='got', grade==='got');
  saveRecalled(); renderProgress();
  ri++; if(ri>=rc.length) recallDone(); else recallRender();
}
function recallFlip(){ rcDir = rcDir==='td'?'dt':'td'; playClick(); recallRender(); }
function recallDone(){ sesClose('recall'); }

// ===== MATCH (Warm-up — recognition game, never touches mastery) =====
let mPairs=[], mTiles=[], mSel=null, mMatched=0, mTime=0, mTimer=null, mStarted=false, mBusy=false;
function matchStart(){
  clearInterval(mTimer); mTimer=null; mStarted=false; mTime=0; mSel=null; mMatched=0; mBusy=false; setBar(-1);
  document.getElementById('match-timer').textContent='0.0s';
  document.getElementById('match-win').classList.remove('on');
  document.getElementById('match-play').style.display='flex';
  const pool=shuffleArr(GLOSSARY.filter(g=>FCH==='all'||g.ch===FCH).slice());
  mPairs=pool.slice(0,6);
  mTiles=[]; mPairs.forEach((p,i)=>{ mTiles.push({pid:i,type:'t',text:p.t}); mTiles.push({pid:i,type:'d',text:p.d}); });
  shuffleArr(mTiles);
  document.getElementById('match-grid').innerHTML = mTiles.map((t,idx)=>
    `<button class="tile" data-i="${idx}" onclick="matchTap(${idx})"><span class="${t.type==='t'?'tt':''}">${t.text}</span></button>`).join('');
  window.scrollTo(0,0);
}
function tileEl(i){ return document.querySelector(`#match-grid .tile[data-i="${i}"]`); }
function matchTap(idx){
  if(mBusy) return; const el=tileEl(idx); if(!el||el.classList.contains('gone')) return;
  if(!mStarted){ mStarted=true; mTimer=setInterval(()=>{ mTime+=0.1; document.getElementById('match-timer').textContent=mTime.toFixed(1)+'s'; },100); }
  if(mSel===null){ mSel=idx; el.classList.add('sel'); playClick(); return; }
  if(mSel===idx){ el.classList.remove('sel'); mSel=null; return; }
  const a=mTiles[mSel], b=mTiles[idx], first=tileEl(mSel);
  if(a.pid===b.pid && a.type!==b.type){
    el.classList.add('ok'); first.classList.remove('sel'); first.classList.add('ok'); playCorrect(); vibe([30]);
    const s1=mSel,s2=idx; mSel=null; mMatched++;
    setTimeout(()=>{ tileEl(s1).classList.add('gone'); tileEl(s2).classList.add('gone'); },260);
    if(mMatched===mPairs.length) setTimeout(matchWin,320);
  } else {
    el.classList.add('sel','err'); first.classList.add('err'); playWrong(); vibe([90,40,90]); mBusy=true;
    const s1=mSel,s2=idx; mSel=null;
    setTimeout(()=>{ [s1,s2].forEach(i=>{ const t=tileEl(i); if(t) t.classList.remove('sel','err'); }); mBusy=false; },460);
  }
}
function matchWin(){
  clearInterval(mTimer); playFinish();
  const t=mTime, best=lsGet('chem1211u1_matchbest',null), isBest=best==null||t<best;
  if(isBest) lsSet('chem1211u1_matchbest',+t.toFixed(1));
  document.getElementById('match-play').style.display='none';
  const win=document.getElementById('match-win');
  win.innerHTML=`<div class="close-card" role="status">
    <div class="close-k">Match</div>
    <div class="close-t">${t.toFixed(1)}s</div>
    <p class="close-s">${isBest?'New best time.':'Best so far: '+(best==null?'none':best+'s')+'.'} Warm-up done. Now go produce them in <b>Recall</b>. That's what sticks.</p>
    <div class="close-actions"><button class="btn btn-ghost" onclick="matchStart()">Play again</button>
      <button class="btn btn-primary" onclick="enter('recall')">Recall${ic('chev-r','ic ic-16')}</button></div></div>`;
  win.classList.add('on');
  window.scrollTo(0,0);
}

