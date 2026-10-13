// ===== HOME: the Exam 2 study plan, one step per chapter in study-guide topic order =====
// A step is done when every one of its questions is in `recalled` (Learn mastery writes it),
// so the plan reads the same storage key the engine already keeps. Nothing here is typed.
let readSet = new Set(lsGet('chem1211e2_read_v1',[]));
let showDone = false; // finished steps ahead of the current one fold into a single row
function saveRead(){ lsSet('chem1211e2_read_v1',[...readSet]); }
function plural(n,one,many){ return n+' '+(n===1?one:many); }
function btn(cls,fn,label){ return `<button class="btn ${cls}" onclick="${fn}">${label}</button>`; }
function guideFor(id){ return GUIDE.find(g=>g.ch===id); }
function topicsLabel(g){ return g.topics.replace(/^Study guide t/,'T'); }
function stepState(c){
  const qs=Q.filter(q=>q.chId===c.id), got=qs.filter(q=>recalled.has(qId(q))).length;
  return {n:qs.length, got, done:qs.length>0&&got===qs.length, read:readSet.has(c.id), terms:GLOSSARY.filter(g=>g.ch===c.id).length};
}
function planState(){
  const st=CHAPTERS.map(stepState);
  let next=st.findIndex(s=>!s.done); if(next<0) next=CHAPTERS.length; // all ten done: the mixed exam is next
  return {st, next, fresh:st.every(s=>!s.got&&!s.read), done:st.filter(s=>s.done).length};
}
function renderProgress(){
  const el=document.getElementById('plan-done'); if(!el) return;
  el.textContent=`${planState().done} of ${CHAPTERS.length} done`;
}
function stepTag(p,s){ return p.fresh ? 'Start here' : (s && (s.got||s.read)) ? 'Continue here' : 'Up next'; }
function stepStatus(s,cur){ return s.done ? 'Done' : s.got ? `${s.got} of ${s.n} recalled` : (s.read && !cur) ? 'Guide read' : ''; }
// a fully recalled step practices everything again; a partial one resumes with what is left
function practiceLabel(s){ const left=s.n-s.got;
  return (s.got && !s.done) ? (left===1 ? 'Practice the last question' : `Practice the last ${left}`) : `Practice ${plural(s.n,'question','questions')}`; }
function stepActions(i,c,s){
  const pr=`practiceCh('${c.id}')`, rd=`readStep(${i})`, pl=practiceLabel(s);
  return `<div class="step-act">` + (s.read||s.got
    ? btn('btn-primary',pr,pl) + btn('btn-ghost',rd,'Reread the guide')
    : btn('btn-primary',rd,'Read the guide') + btn('btn-ghost',pr,pl)) + `</div>`;
}
function stepRow(i,p){
  const c=CHAPTERS[i], s=p.st[i], g=guideFor(c.id), cur=i===p.next, st=stepStatus(s,cur);
  return `<li class="step${s.done?' done':''}${cur?' next':''}"><button class="step-row" onclick="readStep(${i})">`+
    `<span class="step-n">${s.done?ic('check','ic ic-16'):i+1}</span>`+
    `<span class="step-tx">${cur?`<span class="step-tag">${stepTag(p,s)}</span>`:''}<span class="step-t">${g.title}</span>`+
    `<span class="step-s">${topicsLabel(g)}, ${plural(s.n,'question','questions')}</span>${st?`<span class="step-st step-st-in">${st}</span>`:''}</span>`+
    (st?`<span class="step-st">${st}</span>`:'')+ic('chev-r','ic step-go')+`</button>${cur?stepActions(i,c,s):''}</li>`;
}
function renderHome(){
  const p=planState(), lead=Math.min(p.next,CHAPTERS.length), rows=[];
  // every step before the current one is done by construction, so two or more fold into one row
  if(lead>=2){
    rows.push(`<li class="step done done-sum"><button class="step-row" onclick="toggleDone()" aria-expanded="${showDone}">`+
      `<span class="step-n">${ic('check','ic ic-16')}</span><span class="step-tx"><span class="step-t">Steps 1 to ${lead} done</span></span>`+
      `<span class="step-tog">${showDone?'Hide':'Show'}</span></button></li>`);
  }
  for(let i=0;i<CHAPTERS.length;i++) if(i>=lead || lead<2 || showDone) rows.push(stepRow(i,p));
  const fin=p.next===CHAPTERS.length;
  rows.push(`<li class="step final${fin?' next':''}"><div class="step-row">`+
    `<span class="step-n">${CHAPTERS.length+1}</span><span class="step-tx">${fin?`<span class="step-tag">${stepTag(p,null)}</span>`:''}`+
    `<span class="step-t">Mixed exam</span><span class="step-s">All ${Q.length} questions, chapters shuffled together</span></span>`+
    (fin?'':btn('btn-ghost step-start','startFinal()','Start'))+`</div>`+
    (fin?`<div class="step-act">${btn('btn-primary','startFinal()','Start the mixed exam')}</div>`:'')+`</li>`);
  document.getElementById('plan').innerHTML=rows.join('');
  const nv=VIDEOS.reduce((a,g)=>a+g.items.length,0);
  const tools=[['pen','Recall key terms',`${GLOSSARY.length} terms, typed from memory`,"openTool('recall')"],
    ['book','Key terms list',`All ${GLOSSARY.length} definitions, searchable`,'openTerms()'],
    ['cards','Preview cards',`Flip through all ${Q.length} questions`,"openTool('flash')"],
    ['bolt','Match','Timed term matching',"openTool('match')"],
    ['play','Videos',`${nv} videos, grouped by topic`,"openTool('videos')"]];
  document.getElementById('tools').innerHTML=tools.map(([i,t,s,fn])=>
    `<button class="tool" onclick="${fn}"><span class="tool-ic">${ic(i)}</span><span class="step-tx"><span class="tool-t">${t}</span>`+
    `<span class="tool-s">${s}</span></span>${ic('chev-r','ic step-go')}</button>`).join('');
  renderProgress();
}
function toggleDone(){ showDone=!showDone; playClick(); renderHome();
  const b=document.querySelector('#plan .done-sum .step-row'); if(b) b.focus(); } // the re-render dropped focus to <body>
function readStep(i){
  const c=CHAPTERS[i], g=guideFor(c.id), s=stepState(c), last=i+1>=CHAPTERS.length;
  FCH=c.id; playClick(); readSet.add(c.id); saveRead();
  document.getElementById('read-pos').textContent=`Step ${i+1} of ${CHAPTERS.length}`;
  const nx = last ? ['startFinal()', `Mixed exam, all ${Q.length} questions`] : [`readStep(${i+1})`, guideFor(CHAPTERS[i+1].id).title];
  document.getElementById('read-body').innerHTML=`<div class="g-topics">${g.topics}</div><h1 class="read-h">${g.title}</h1>${g.html}`+
    `<div class="read-do">${btn('btn-primary',`practiceCh('${c.id}')`,practiceLabel(s))}`+
    (s.terms?btn('btn-ghost',`recallCh('${c.id}')`,`Recall ${plural(s.terms,'key term','key terms')}`):'')+`</div>`+
    `<button class="read-next" onclick="${nx[0]}"><span class="step-tx"><span class="rn-l">Next: step ${i+2}</span><span class="rn-t">${nx[1]}</span></span>${ic('chev-r')}</button>`;
  show('read'); window.scrollTo(0,0);
}
function practiceCh(id){ FCH=id; enter('learn'); }
function recallCh(id){ FCH=id; enter('recall'); }
function startFinal(){ FCH='all'; enter('exam'); }
function openTool(m){ FCH='all'; enter(m); }
function openTerms(){ FCH='all'; playClick(); document.getElementById('term-filter').value=''; show('terms'); renderTerms(); window.scrollTo(0,0); }
