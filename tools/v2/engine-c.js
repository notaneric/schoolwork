function videosInit(){ setBar(-1); show('videos');
  document.getElementById('vid-list').innerHTML = VIDEOS.map(g=>
    `<div class="vid-group"><h4>${g.ch}</h4><div class="vid-list">`+
    g.items.map(v=>`<a class="vid-row" href="https://youtu.be/${v[0]}" target="_blank" rel="noopener">`+
      `<span class="vid-play">${ic('play','ic ic-16')}</span>`+
      `<span class="vid-tx"><h5>${v[1]}</h5><p>${v[2]}</p></span>`+
      ic('ext','ic ic-16 vid-ext')+`</a>`).join('')+
    `</div></div>`).join('');
  window.scrollTo(0,0);
}

// ===== keyboard =====
document.addEventListener('keydown',e=>{
  if(MODE==='flash'){
    if(e.key===' '||e.key==='Enter'){ e.preventDefault(); fcFlip(); }
    else if(e.key==='ArrowLeft'){ e.preventDefault(); fcNav(-1); }
    else if(e.key==='ArrowRight'){ e.preventDefault(); fcNav(1); }
    else if(e.key.toLowerCase()==='s'){ fcStar(); }
  } else if(MODE==='learn'){
    if(lnStage==='produce'){
      const t=document.activeElement && document.activeElement.id==='learn-input';
      if(e.key==='Enter'&&(e.ctrlKey||e.metaKey||!t)&&!e.repeat&&performance.now()-lnStageAt>350){ e.preventDefault(); revealOptions(); }
      else if(!t && /^[123]$/.test(e.key)){ setConf({'1':'guess','2':'think','3':'sure'}[e.key]); }
    } else if(lnStage==='recognize'){
      if(/^[1-9]$/.test(e.key)){ const pos=+e.key-1; const it=lnQ[lnPos]; if(it&&pos<it.perm.length&&!lnDone) learnPick(it.perm[pos]); }
      else if((e.key==='Enter')&&lnDone){ e.preventDefault(); learnNext(); }
    }
  } else if(MODE==='recall'){
    const t=document.activeElement && document.activeElement.id==='rc-input';
    if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){ e.preventDefault(); recallReveal(); }
    else if(document.getElementById('rc-reveal').style.display!=='none' && /^[123]$/.test(e.key)){ recallGrade({'1':'miss','2':'close','3':'got'}[e.key]); }
  }
});

// ===== init =====
renderHome();
