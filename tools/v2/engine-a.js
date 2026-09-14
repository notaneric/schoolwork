// ===== Diagram generators — LIGHT theme (dark ink on paper) — CHEM 1211 Unit 1 =====
const DG = (() => {
  // Factor-label "railroad track": given x (factor)(factor) = result.
  // given = {n:'text'};  factors = [{n:'top', d:'bottom'}, ...]
  function dimtrack(given, factors, result){
    const ink='#1F1E1B', mut='#6A675F', acc='#3F46DF', ln='#D3CEC3';
    const frac=(n,d)=>`<span style="display:inline-flex;flex-direction:column;text-align:center;line-height:1.25"><span style="padding:0 8px 2px">${n}</span><span style="padding:2px 8px 0;border-top:1.5px solid ${ink}">${d}</span></span>`;
    const box=(inner)=>`<span style="display:inline-flex;align-items:center;padding:5px 4px;border:1px solid ${ln};border-radius:6px;background:#FDFCF9">${inner}</span>`;
    let s=`<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:7px;font-family:'Cascadia Code',ui-monospace,Consolas,monospace;font-size:14px;color:${ink};padding:6px 4px">`;
    s+=`<span style="font-weight:700">${given.n}</span>`;
    factors.forEach(f=>{ s+=`<span style="color:${mut}">&times;</span>`+box(frac(f.n,f.d)); });
    s+=`<span style="color:${mut}">=</span><span style="font-weight:700;color:${acc}">${result}</span>`;
    return s+`</div>`;
  }
  return { dimtrack };
})();
const DT = DG.dimtrack;
