// ===== HOME: the Exam 2 study plan as a Notion-style page (cover, icon, properties, database views) =====
// A step is done when every one of its questions is in `recalled` (Learn mastery writes it),
// so the plan reads the same storage key the engine already keeps. Nothing here is typed.
let readSet = new Set(lsGet('chem1211e2_read_v1',[]));
let showDone = false; // finished steps ahead of the current one fold into a single row
function saveRead(){ lsSet('chem1211e2_read_v1',[...readSet]); }

// ---- look: Notion palette, per-step icon + color, and the reader's own choices ----
// [icon/stroke color, block background, pill background, pill text]; icon colors are darkened from
// Notion's text colors so every glyph keeps 3:1 on its own tint (Notion's yellow on yellow is 2.5:1)
const NC = {gray:['#6F6E6A','#F0EFED','rgba(28,19,1,.11)','#494846'], brown:['#8A5A44','#F5EDE9','rgba(127,51,0,.157)','#584437'],
  orange:['#C2620A','#FBEBDE','rgba(196,88,0,.204)','#6A4222'], yellow:['#A87320','#F9F3DC','rgba(209,156,0,.282)','#655121'],
  green:['#3B7556','#E8F1EC','rgba(0,96,38,.157)','#2A533C'], blue:['#2F6F96','#E5F2FC','rgba(0,118,217,.204)','#264A72'],
  purple:['#7E559E','#F3EBF9','rgba(92,0,163,.14)','#553B69'], pink:['#AD3F7A','#FAE9F1','rgba(183,0,78,.153)','#68354E'],
  red:['#C13F3A','#FCE9E7','rgba(206,24,0,.165)','#6D3531']};
const STEP_LOOK = {light:['ch-light','yellow'], bohr:['ch-bohr','orange'], qm:['ch-dual','purple'], qn:['ch-orbital','blue'],
  econf:['ch-config','green'], ions:['ch-magnet','red'], ptable:['ch-table','brown'], trends:['ch-trend','pink'],
  bonds:['ch-bond','purple'], names:['ch-name','green']};
const ICONS = ['ch-atom','ch-flask','ch-light','ch-bohr','ch-dual','ch-orbital','ch-config','ch-magnet','ch-table','ch-trend','ch-bond','ch-name'];
const COVERS = [['spectrum','Hydrogen spectrum'],['table','Periodic table'],['grid','Graph paper'],
  ['sand','Sand'],['sky','Sky'],['sage','Sage'],['lilac','Lilac'],['none','No cover']];
const LOOK_DEF = {cover:'spectrum', icon:'ch-atom', color:'blue', view:'plan', font:'default', small:false, full:false};
let LOOK = Object.assign({}, LOOK_DEF, lsGet('chem1211e2_look_v1',{}));
// anything that did not come from these lists falls back to the default, so storage can never inject markup
if(!COVERS.some(c=>c[0]===LOOK.cover)) LOOK.cover=LOOK_DEF.cover;
if(!ICONS.includes(LOOK.icon)) LOOK.icon=LOOK_DEF.icon;
if(!NC[LOOK.color]) LOOK.color=LOOK_DEF.color;
if(!['plan','board','gallery'].includes(LOOK.view)) LOOK.view=LOOK_DEF.view;
if(!['default','serif','mono'].includes(LOOK.font)) LOOK.font=LOOK_DEF.font;
function saveLook(){ lsSet('chem1211e2_look_v1',LOOK); }
function lookFor(c){ return STEP_LOOK[c.id] || ['ch-flask','gray']; }
function tile(icon,color,cls){ const k=NC[color]; return `<span class="itile ${cls||''}" style="--tb:${k[1]};--tc:${k[0]}">${ic(icon)}</span>`; }
function pill(text,color,dot){ const k=NC[color]; return `<span class="pill${dot?' pill-st':''}" style="--pb:${k[2]};--pt:${k[3]};--pd:${dot||k[0]}">${text}</span>`; }

// ---- plan state ----
function plural(n,one,many){ return n+' '+(n===1?one:many); }
function btn(cls,fn,label){ return `<button class="btn ${cls}" onclick="${fn}">${label}</button>`; }
function guideFor(id){ return GUIDE.find(g=>g.ch===id); }
function topicsLabel(g){ return g.topics.replace(/^Study guide t/,'t'); }
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
  const d=planState().done; el.textContent=`${d} of ${CHAPTERS.length} done`;
  const b=document.getElementById('plan-bar'); if(b) b.style.width=Math.round(d/CHAPTERS.length*100)+'%';
}
const STATUS=[['Not started','gray','#8E8B86'],['In progress','blue','#2783DE'],['Done','green','#46A171']];
function statusOf(s){ return s.done?2:(s.got||s.read)?1:0; }
function statusPill(s){ const [t,c,d]=STATUS[statusOf(s)]; return pill(t,c,d); }
function bar(s,bare){ const pct=s.n?Math.round(s.got/s.n*100):0;
  return `<span class="bar-w"><span class="bar" style="--bc:${NC[s.done?'green':'blue'][0]}"><i style="width:${pct}%"></i></span>${bare?'':`<span class="bar-n">${s.got}/${s.n}</span>`}</span>`; }
function stepTag(p,s){ return p.fresh ? 'Start here' : (s && (s.got||s.read)) ? 'Continue here' : 'Up next'; }
// a fully recalled step practices everything again; a partial one resumes with what is left
function practiceLabel(s){ const left=s.n-s.got;
  return (s.got && !s.done) ? (left===1 ? 'Practice the last question' : `Practice the last ${left}`) : `Practice ${plural(s.n,'question','questions')}`; }
function stepActions(i,c,s){
  const pr=`practiceCh('${c.id}')`, rd=`readStep(${i})`, pl=practiceLabel(s);
  return `<div class="step-act">` + (s.read||s.got
    ? btn('btn-primary',pr,pl) + btn('btn-ghost',rd,'Reread the guide')
    : btn('btn-primary',rd,'Read the guide') + btn('btn-ghost',pr,pl)) + `</div>`;
}

// ---- Plan view: the ordered list, current step opened up ----
function stepRow(i,p){
  const c=CHAPTERS[i], s=p.st[i], g=guideFor(c.id), cur=i===p.next, [icn,col]=lookFor(c);
  return `<li class="step${s.done?' done':''}${cur?' next':''}"><button class="step-row" onclick="readStep(${i})">`+
    tile(icn,col)+`<span class="step-tx">${cur?`<span class="step-tag">${stepTag(p,s)}</span>`:''}<span class="step-t">${g.title}</span>`+
    `<span class="step-s">Step ${i+1}, ${topicsLabel(g)}, ${plural(s.n,'question','questions')}</span>`+
    `<span class="step-meta-in">${statusPill(s)}${s.got?bar(s):''}</span></span>`+
    `<span class="step-meta">${statusPill(s)}${bar(s)}</span>`+`</button>${cur?stepActions(i,c,s):''}</li>`;
}
function finalRow(p, fin){
  return `<li class="step final${fin?' next':''}"><div class="step-row">${tile('exam','gray')}`+
    `<span class="step-tx">${fin?`<span class="step-tag">${stepTag(p,null)}</span>`:''}<span class="step-t">Mixed exam</span>`+
    `<span class="step-s">Step ${CHAPTERS.length+1}, all ${Q.length} questions, chapters shuffled together</span></span>`+
    (fin?'':btn('btn-ghost step-start','startFinal()','Start'))+`</div>`+
    (fin?`<div class="step-act">${btn('btn-primary','startFinal()','Start the mixed exam')}</div>`:'')+`</li>`;
}
function renderPlanList(p){
  const lead=Math.min(p.next,CHAPTERS.length), rows=[];
  // every step before the current one is done by construction, so two or more fold into one row
  if(lead>=2) rows.push(`<li class="step done done-sum"><button class="step-row" onclick="toggleDone()" aria-expanded="${showDone}">`+
    `<span class="itile" style="--tb:${NC.green[1]};--tc:${NC.green[0]}">${ic('check')}</span><span class="step-tx"><span class="step-t">Steps 1 to ${lead} done</span></span>`+
    `<span class="step-tog">${showDone?'Hide':'Show'}</span></button></li>`);
  for(let i=0;i<CHAPTERS.length;i++) if(i>=lead || lead<2 || showDone) rows.push(stepRow(i,p));
  rows.push(finalRow(p, p.next===CHAPTERS.length));
  return `<ol class="plan" id="plan">${rows.join('')}</ol>`;
}
// ---- Board view: the same steps grouped by status, still in order inside each column ----
function renderBoard(p){
  const cols=[[],[],[]];
  CHAPTERS.forEach((c,i)=>{ const s=p.st[i], g=guideFor(c.id), [icn,col]=lookFor(c), cur=i===p.next;
    cols[statusOf(s)].push(`<button class="bcard${cur?' next':''}" onclick="readStep(${i})">${cur?`<span class="step-tag">${stepTag(p,s)}</span>`:''}`+
      `<span class="card-hd">${tile(icn,col,'itile-sm')}<span class="card-t">${g.title}</span></span>`+
      `<span class="card-s">Step ${i+1}, ${plural(s.n,'question','questions')}</span>${bar(s)}</button>`); });
  return `<div class="board">` + STATUS.map(([t,c,d],k)=>`<div class="bcol" style="--colbg:${NC[c][1]}"><div class="bcol-h">${pill(t,c,d)}<span class="bcol-n">${cols[k].length}</span></div>`+
    (cols[k].join('') || `<div class="bcol-empty">No steps yet</div>`)+`</div>`).join('') + `</div>`;
}
// ---- Gallery view: one card per step with its own cover ----
function renderGallery(p){
  const cards=CHAPTERS.map((c,i)=>{ const s=p.st[i], g=guideFor(c.id), [icn,col]=lookFor(c), cur=i===p.next, k=NC[col];
    return `<button class="gcard${cur?' next':''}" onclick="readStep(${i})"><span class="gcover" style="--cb:${k[1]};--pat:${patternURL(icn,k[0])}">${tile(icn,col,'itile-lg')}</span>`+
      `<span class="gbody">${cur?`<span class="step-tag">${stepTag(p,s)}</span>`:''}<span class="card-t">${g.title}</span>`+
      `<span class="card-s">Step ${i+1}, ${topicsLabel(g)}</span><span class="gmeta">${statusPill(s)}${bar(s)}</span></span></button>`; });
  const fin=p.next===CHAPTERS.length, k=NC.gray;
  cards.push(`<div class="gcard final${fin?' next':''}"><span class="gcover" style="--cb:${k[1]};--pat:${patternURL('exam',k[0])}">${tile('exam','gray','itile-lg')}</span>`+
    `<span class="gbody">${fin?`<span class="step-tag">${stepTag(p,null)}</span>`:''}<span class="card-t">Mixed exam</span>`+
    `<span class="card-s">Step ${CHAPTERS.length+1}, all ${Q.length} questions</span>${btn(fin?'btn-primary':'btn-ghost','startFinal()','Start the mixed exam')}</span></div>`);
  return `<div class="gallery">${cards.join('')}</div>`;
}
function nextBar(p){
  if(p.next>=CHAPTERS.length) return `<div class="nextbar">${tile('exam','gray')}<span class="step-tx"><span class="step-tag">${stepTag(p,null)}</span>`+
    `<span class="step-t">Step ${CHAPTERS.length+1}: Mixed exam</span></span>${btn('btn-primary','startFinal()','Start the mixed exam')}</div>`;
  const i=p.next, c=CHAPTERS[i], s=p.st[i], [icn,col]=lookFor(c);
  const go=(s.read||s.got) ? btn('btn-primary',`practiceCh('${c.id}')`,practiceLabel(s)) : btn('btn-primary',`readStep(${i})`,'Read the guide');
  return `<div class="nextbar">${tile(icn,col)}<span class="step-tx"><span class="step-tag">${stepTag(p,s)}</span>`+
    `<span class="step-t">Step ${i+1}: ${guideFor(c.id).title}</span></span>${go}</div>`;
}
function renderHome(){
  applyLook(); document.body.dataset.mode=MODE;
  const p=planState();
  document.getElementById('views').innerHTML=[['plan','Plan','ch-list'],['board','Board','ch-board'],['gallery','Gallery','ch-gallery']].map(([v,l,i])=>
    `<button class="vtab${LOOK.view===v?' on':''}" role="tab" aria-selected="${LOOK.view===v}" onclick="setView('${v}')">${ic(i,'ic ic-16')}${l}</button>`).join('');
  document.getElementById('db-view').innerHTML = LOOK.view==='board' ? nextBar(p)+renderBoard(p) : LOOK.view==='gallery' ? nextBar(p)+renderGallery(p) : renderPlanList(p);
  const bd=document.querySelector('#db-view .board'), bc=bd && bd.querySelector('.bcard.next');
  if(bc && bd.scrollWidth>bd.clientWidth) bd.scrollLeft += bc.closest('.bcol').getBoundingClientRect().left - bd.getBoundingClientRect().left; // phone: show the current card's column
  const nv=VIDEOS.reduce((a,g)=>a+g.items.length,0);
  const tools=[['pen','blue','Recall key terms',`${GLOSSARY.length} terms, typed from memory`,"openTool('recall')"],
    ['book','brown','Key terms list',`All ${GLOSSARY.length} definitions, searchable`,'openTerms()'],
    ['cards','orange','Preview cards',`Flip through all ${Q.length} questions`,"openTool('flash')"],
    ['bolt','yellow','Match','Timed term matching',"openTool('match')"],
    ['play','red','Videos',`${nv} videos, grouped by topic`,"openTool('videos')"]];
  document.getElementById('tools').innerHTML=tools.map(([i,col,t,s,fn])=>
    `<button class="tool" onclick="${fn}">${tile(i,col,'itile-sm')}<span class="step-tx"><span class="tool-t">${t}</span>`+
    `<span class="tool-s">${s}</span></span>${ic('chev-r','ic step-go')}</button>`).join('');
  renderProgress(); renderCrumbs('home');
}
function setView(v){ LOOK.view=v; saveLook(); playClick(); renderHome(); }
function toggleDone(){ showDone=!showDone; playClick(); renderHome();
  const b=document.querySelector('#plan .done-sum .step-row'); if(b) b.focus(); } // the re-render dropped focus to <body>

// ---- covers: generated art (no image files), plus Notion-style solid colors ----
let svgN=0;
function spectrumSVG(){ // hydrogen's four visible emission lines at their real wavelengths
  const id='glow'+(++svgN), x=l=>(300+(l-400)/300*600).toFixed(1);
  let s=`<svg viewBox="0 0 1200 280" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><filter id="${id}" x="-2" y="0" width="5" height="1"><feGaussianBlur stdDeviation="7"/></filter></defs>`+
    `<rect width="1200" height="280" fill="#15141B"/>`;
  [[410.2,'#7C4DFF'],[434.0,'#4457FF'],[486.1,'#2EC4F5'],[656.3,'#FF4433']].forEach(([l,c])=>{
    s+=`<rect x="${x(l)-7}" y="0" width="14" height="164" fill="${c}" opacity=".5" filter="url(#${id})"/><rect x="${x(l)-1.5}" y="0" width="3" height="164" fill="${c}"/>`; });
  for(let l=400;l<=700;l+=50) s+=`<path d="M${x(l)} 176v8" stroke="#6B6875" stroke-width="1.5"/><text x="${x(l)}" y="202" fill="#9A97A4" font-size="13" text-anchor="middle" font-family="Segoe UI,system-ui,sans-serif">${l} nm</text>`;
  return s+`</svg>`;
}
const ELEM='H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split(' ');
function elemPos(z){ // [column, row, block]; Lu and Lr sit in group 3 and La to Yb / Ac to No form the f rows, as on his handout
  if(z===1) return [1,1,'s']; if(z===2) return [18,1,'n'];
  for(const [z0,per] of [[3,2],[11,3]]) if(z>=z0&&z<z0+8){ const k=z-z0; return k<2?[k+1,per,'s']:[k+11,per,k===7?'n':'p']; }
  for(const [z0,per] of [[19,4],[37,5]]) if(z>=z0&&z<z0+18){ const g=z-z0+1; return [g,per,g<=2?'s':g<=12?'d':g===18?'n':'p']; }
  for(const [z0,per,fr] of [[55,6,8.5],[87,7,9.5]]) if(z>=z0&&z<z0+32){ const k=z-z0;
    if(k<2) return [k+1,per,'s']; if(k<16) return [k+2,fr,'f']; if(k===16) return [3,per,'d']; const g=k-13; return [g,per,g<=12?'d':g===18?'n':'p']; }
}
function tableSVG(){
  const B={s:'pink',d:'blue',p:'yellow',f:'green',n:'purple'}, P=27, T=24;
  let s=`<svg viewBox="-12 -10 510 278" preserveAspectRatio="xMidYMid meet" aria-hidden="true">`;
  ELEM.forEach((sym,i)=>{ const [c,r,b]=elemPos(i+1), k=NC[B[b]], x=(c-1)*P, y=(r-1)*P;
    s+=`<rect x="${x}" y="${y}" width="${T}" height="${T}" rx="3" fill="${k[2]}"/><text x="${x+T/2}" y="${y+16}" fill="${k[3]}" font-size="10" font-weight="600" text-anchor="middle" font-family="Segoe UI,system-ui,sans-serif">${sym}</text>`; });
  return s+`</svg>`;
}
function coverArt(name){ return name==='spectrum' ? spectrumSVG() : name==='table' ? tableSVG() : ''; }
function patternURL(icon,color){ // the step's own icon, tiled faintly, for step covers and gallery cards
  const sym=document.getElementById('i-'+icon); if(!sym) return 'none';
  const svg=`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 96 96'><g transform='translate(36 36)' fill='none' stroke='${color}' stroke-opacity='.24' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'>${sym.innerHTML.replace(/"/g,"'")}</g></svg>`;
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
}
function applyLook(){
  const r=document.documentElement;
  r.dataset.font=LOOK.font; r.classList.toggle('small',!!LOOK.small); r.classList.toggle('full',!!LOOK.full);
  const cv=document.getElementById('home-cover');
  if(cv.dataset.cover!==LOOK.cover){ cv.dataset.cover=LOOK.cover; cv.querySelector('.cover-art').innerHTML=coverArt(LOOK.cover); }
  document.getElementById('home').classList.toggle('no-cover', LOOK.cover==='none');
  const k=NC[LOOK.color], pi=document.getElementById('home-icon');
  pi.style.setProperty('--tb',k[1]); pi.style.setProperty('--tc',k[0]); pi.innerHTML=ic(LOOK.icon);
}

// ---- popovers: Change cover, Change icon, Style (Notion's page menu) ----
let POP=null;
function closePops(){ document.querySelectorAll('.pop').forEach(p=>p.hidden=true); document.querySelectorAll('[aria-haspopup]').forEach(b=>b.setAttribute('aria-expanded','false')); POP=null; }
function togglePop(name, anchor){
  const was=POP===name; closePops(); if(was) return;
  const el=document.getElementById('pop-'+name); renderPop(name); el.hidden=false; POP=name;
  anchor.setAttribute('aria-expanded','true');
  const a=anchor.getBoundingClientRect(), w=el.offsetWidth, vw=document.documentElement.clientWidth;
  el.style.top=(a.bottom+window.scrollY+6)+'px';
  el.style.left=Math.max(8, Math.min(name==='cover'||name==='style' ? a.right-w : a.left, vw-w-8))+'px';
  const f=el.querySelector('button'); if(f) f.focus();
}
function renderPop(name){
  const el=document.getElementById('pop-'+name);
  if(name==='cover') el.innerHTML=`<div class="pop-h">Cover</div><div class="cv-grid">`+COVERS.map(([k,l])=>
    `<button class="cv-opt${LOOK.cover===k?' on':''}" aria-pressed="${LOOK.cover===k}" onclick="setLook('cover','${k}')"><span class="cv-th" data-cover="${k}">${coverArt(k)}</span><span class="cv-l">${l}</span></button>`).join('')+`</div>`;
  else if(name==='icon') el.innerHTML=`<div class="pop-h">Icon</div><div class="ic-grid">`+ICONS.map(n=>
    `<button class="ic-opt${LOOK.icon===n?' on':''}" aria-pressed="${LOOK.icon===n}" aria-label="${n.slice(3)}" onclick="setLook('icon','${n}')" style="--tc:${NC[LOOK.color][0]}">${ic(n)}</button>`).join('')+
    `</div><div class="pop-h">Color</div><div class="col-grid">`+Object.keys(NC).map(c=>
    `<button class="col-opt${LOOK.color===c?' on':''}" aria-pressed="${LOOK.color===c}" aria-label="${c}" onclick="setLook('color','${c}')" style="--sw:${NC[c][0]}"></button>`).join('')+`</div>`;
  else el.innerHTML=`<div class="pop-h">Style</div><div class="font-grid">`+[['default','Default'],['serif','Serif'],['mono','Mono']].map(([k,l])=>
    `<button class="font-opt f-${k}${LOOK.font===k?' on':''}" aria-pressed="${LOOK.font===k}" onclick="setLook('font','${k}')"><span class="font-ag">Ag</span><span class="font-l">${l}</span></button>`).join('')+`</div>`+
    [['small','Small text'],['full','Full width']].map(([k,l])=>`<button class="sw-row" role="switch" aria-checked="${!!LOOK[k]}" onclick="setLook('${k}',${!LOOK[k]})"><span>${l}</span><span class="sw${LOOK[k]?' on':''}"><i></i></span></button>`).join('');
}
function setLook(k,v){
  LOOK[k]=v; saveLook(); playClick();
  if(MODE==='home') renderHome(); else applyLook();
  if(k==='cover'||k==='icon') closePops(); else if(POP){ renderPop(POP); const f=document.querySelector('#pop-'+POP+' .on, #pop-'+POP+' [aria-checked]'); if(f) f.focus(); }
}
document.addEventListener('mousedown', e=>{ if(POP && !e.target.closest('.pop') && !e.target.closest('[aria-haspopup]')) closePops(); });
document.addEventListener('keydown', e=>{ if(e.key==='Escape' && POP){ const b=document.querySelector('[aria-haspopup][aria-expanded="true"]'); closePops(); if(b) b.focus(); } });

// ---- top bar breadcrumbs ----
function renderCrumbs(kind,i){
  const k=NC[LOOK.color], root=`<span class="crumb-ic" style="--tc:${k[0]}">${ic(LOOK.icon,'ic ic-16')}</span>Exam 2 study plan`;
  let h = kind==='home' ? `<span class="crumb cur">${root}</span>` : `<button class="crumb" onclick="goHome()">${root}</button><span class="crumb-sep">/</span>`;
  if(kind==='read'){ const c=CHAPTERS[i], [icn,col]=lookFor(c); h+=`<span class="crumb cur"><span class="crumb-ic" style="--tc:${NC[col][0]}">${ic(icn,'ic ic-16')}</span><span class="crumb-t">${guideFor(c.id).title}</span></span>`; }
  if(kind==='terms') h+=`<span class="crumb cur">Key terms</span>`;
  document.getElementById('crumbs').innerHTML=h;
  document.getElementById('tb-back').hidden = kind==='home';
}

// ---- step page: its own cover and icon, Notion properties, the guide, then practice ----
function prop(icon,label,value){ return `<div class="prop"><span class="prop-k">${ic(icon,'ic ic-16')}${label}</span><span class="prop-v">${value}</span></div>`; }
function readStep(i){
  const c=CHAPTERS[i], g=guideFor(c.id), last=i+1>=CHAPTERS.length, [icn,col]=lookFor(c), k=NC[col];
  FCH=c.id; playClick(); readSet.add(c.id); saveRead(); closePops();
  const s=stepState(c);
  const cv=document.getElementById('read-cover'); cv.style.setProperty('--cb',k[1]); cv.style.setProperty('--pat',patternURL(icn,k[0]));
  const ri=document.getElementById('read-icon'); ri.style.setProperty('--tb',k[1]); ri.style.setProperty('--tc',k[0]); ri.innerHTML=ic(icn);
  document.getElementById('read-title').textContent=g.title;
  document.getElementById('read-props').innerHTML=
    prop('ch-status','Status',statusPill(s)) + prop('ch-list','Topics',g.topics) +
    prop('ch-hash','Questions',`${bar(s,true)}${s.got} of ${s.n} recalled`) + (s.terms?prop('book','Key terms',String(s.terms)):'') +
    prop('ch-trend','Step',`<span id="read-pos">Step ${i+1} of ${CHAPTERS.length+1}</span>`);
  const nx = last ? ['startFinal()', `Mixed exam, all ${Q.length} questions`, 'exam', 'gray'] : [`readStep(${i+1})`, guideFor(CHAPTERS[i+1].id).title, ...lookFor(CHAPTERS[i+1])];
  document.getElementById('read-body').innerHTML=g.html+
    `<div class="read-do">${btn('btn-primary',`practiceCh('${c.id}')`,practiceLabel(s))}`+
    (s.terms?btn('btn-ghost',`recallCh('${c.id}')`,`Recall ${plural(s.terms,'key term','key terms')}`):'')+`</div>`+
    `<button class="read-next" onclick="${nx[0]}">${tile(nx[2],nx[3],'itile-sm')}<span class="step-tx"><span class="rn-l">Next: step ${i+2}</span><span class="rn-t">${nx[1]}</span></span>${ic('chev-r')}</button>`;
  renderCrumbs('read',i); show('read'); window.scrollTo(0,0);
}
function practiceCh(id){ FCH=id; closePops(); enter('learn'); }
function recallCh(id){ FCH=id; closePops(); enter('recall'); }
function startFinal(){ FCH='all'; closePops(); enter('exam'); }
function openTool(m){ FCH='all'; closePops(); enter(m); }
function openTerms(){ FCH='all'; playClick(); closePops(); document.getElementById('term-filter').value=''; renderCrumbs('terms'); show('terms'); renderTerms(); window.scrollTo(0,0); }
