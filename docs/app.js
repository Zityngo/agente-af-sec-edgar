(()=>{'use strict';
const DATA=window.AF_DATA;if(!DATA){document.body.prepend('No se cargaron los datos; comprueba data.js.');return;}
const q=s=>document.querySelector(s),qa=s=>Array.from(document.querySelectorAll(s));
const format=(v,n=1)=>Number(v).toLocaleString('es-ES',{minimumFractionDigits:n,maximumFractionDigits:n});
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pdf='https://drive.google.com/file/d/1uXRFicl0oCIEEyiQ8H7oG4GCswe1uiJh/view?usp=drivesdk';q('#pdf-main').href=pdf;q('#pdf-main').target='_blank';q('#pdf-main').rel='noopener noreferrer';
const metrics={revenue:{name:'Ingresos',color:'#4cdbbd'},ebit:{name:'EBIT',color:'#61a6ee'},net:{name:'Beneficio neto',color:'#f5bb65'},cfo:{name:'Flujo operativo',color:'#a9c6ed'},capex:{name:'CAPEX pagado',color:'#f9a76e'},fcf:{name:'FCF',color:'#fb7884'},roic:{name:'ROIC proxy',color:'#4cdbbd'},roe:{name:'ROE',color:'#65a6f3'}};
const plot=(selector,detailSelector,fields,initial=4,percent=false)=>{
 const data=DATA.history;const colors=fields.map(f=>metrics[f].color);const values=data.flatMap(d=>fields.map(f=>d[f]));const max=Math.max(...values),min=Math.min(0,...values);
 const W=900,H=262,left=56,right=24,top=17,bottom=45,w=W-left-right,h=H-top-bottom;
 const x=i=>left+i*w/(data.length-1),y=v=>top+h-(v-min)/(max-min||1)*h;
 const ticks=4;
 let s=`<svg viewBox="0 0 ${W} ${H}" role="group" aria-label="Gráfico con ${fields.join(', ')}"><title>Series financieras FY2022 a FY2026</title>`;
 for(let j=0;j<=ticks;j++){const val=min+(max-min)*j/ticks;const yy=y(val);s+=`<line class="chart-grid" x1="${left}" y1="${yy}" x2="${W-right}" y2="${yy}"/><text class="chart-label" x="${left-10}" y="${yy+4}" text-anchor="end">${format(val,0)}${percent?'%':''}</text>`}
 data.forEach((d,i)=>{s+=`<text class="chart-label" x="${x(i)}" y="${H-8}" text-anchor="middle">${d.year}</text>`});
 fields.forEach((f,k)=>{let path=data.map((d,i)=>(i?'L':'M')+x(i).toFixed(1)+','+y(d[f]).toFixed(1)).join(' ');s+=`<path class="chart-series" d="${path}" stroke="${colors[k]}"/>`;data.forEach((d,i)=>s+=`<circle class="chart-point" data-point="${i}" cx="${x(i)}" cy="${y(d[f])}" r="4.5" fill="${colors[k]}" stroke="#122738"><title>${d.year} ${metrics[f].name}: ${format(d[f],1)}${percent?' %':' B$'}</title></circle>`) });
 s+='</svg><div class="chart-legend">'+fields.map((f,k)=>`<span><i style="background:${colors[k]}"></i>${metrics[f].name}</span>`).join('')+'</div>';
 q(selector).innerHTML=s;const points=qa(selector+' .chart-point');
 const activate=i=>{points.forEach(n=>n.classList.toggle('active',Number(n.dataset.point)===i));const d=data[i];const items=fields.map(f=>`<b style="color:${metrics[f].color}">${metrics[f].name}: ${format(d[f],1)}${percent?' %':' B$'}</b>`).join(' · ');q(detailSelector).innerHTML=`<strong>FY${d.year}</strong> · ${items}`;};
 points.forEach(el=>{el.addEventListener('pointerenter',()=>activate(Number(el.dataset.point)));el.addEventListener('click',()=>activate(Number(el.dataset.point))) });
 activate(initial);
};
const legendStyle=document.createElement('style');legendStyle.innerText='.chart-legend{display:flex;gap:18px;justify-content:center;flex-wrap:wrap;margin-top:-4px;font-size:10px;color:var(--muted)}.chart-legend span{display:flex;align-items:center;gap:6px}.chart-legend i{display:inline-block;width:10px;height:10px;border-radius:100%}';document.head.append(legendStyle);
// Microsoft: simultaneous metric selection. All values are FY in USD billions.
const growthAllowed=['revenue','ebit','net','cfo'];
const growthInputs=qa('#growth-metrics input[type="checkbox"]');
const selectedGrowth=()=>growthInputs.filter(e=>e.checked).map(e=>e.value);
function updateGrowthChart(){
  const chosen=selectedGrowth();
  if(!chosen.length)return;
  plot('#growth-chart','#growth-detail',chosen);
  q('#growth-hint').textContent=chosen.length===1?'1 métrica seleccionada':`${chosen.length} métricas superpuestas · valores en miles de millones de USD`;
}
growthInputs.forEach(input=>input.addEventListener('change',()=>{
  if(!selectedGrowth().length){input.checked=true;q('#growth-hint').textContent='Selecciona al menos una métrica.';return;}
  updateGrowthChart();
}));
q('#growth-all').addEventListener('click',()=>{growthInputs.forEach(e=>e.checked=true);updateGrowthChart()});
q('#growth-one').addEventListener('click',()=>{growthInputs.forEach(e=>e.checked=e.value==='revenue');updateGrowthChart()});
updateGrowthChart();

// Peers: chart ONE metric at a time for selected companies (keeps visual legible).
// SEC data are annual, not necessarily on the same fiscal year-end date. Gaps stay gaps.
const peerYears=[2022,2023,2024,2025,2026];
const peerMetrics={
 revenue:'Ingresos',ebit:'EBIT',net:'Beneficio neto',cfo:'CFO',capex:'CAPEX',fcf:'FCF',
 ebit_margin:'Margen EBIT',fcf_margin:'Margen FCF'
};
const peers=DATA.peerHistory||[];
const peerInputs=qa('#peer-companies input[type="checkbox"]');
const peerSelected=()=>peers.filter(p=>peerInputs.some(i=>i.value===p.ticker&&i.checked));
const missing=v=>!Number.isFinite(v);
let peerActiveYear=2025;
function renderPeers(){
 const area=q('#peer-chart'),detail=q('#peer-detail');
 const field=q('#peer-metric').value;
 const pct=field.endsWith('_margin');
 const indexChoice=q('#peer-scale');
 if(pct){indexChoice.value='absolute';indexChoice.disabled=true;indexChoice.title='Los márgenes se comparan directamente en porcentaje.';}
 else{indexChoice.disabled=false;indexChoice.title='';}
 const indexed=indexChoice.value==='indexed'&&!pct;
 const sel=peerSelected();
 if(!sel.length){area.innerHTML='<p class="mini-caption">Marca al menos una empresa para mostrar el gráfico.</p>';detail.textContent='';return;}
 const notes=[];
 const all=[];
 const series=sel.map(company=>{
   const m=new Map(company.records.map(r=>[r.year,r]));
   const base=m.get(2022)?.[field];
   const badBaseline=indexed && (missing(base)||base<=0);
   if(badBaseline)notes.push(`${company.name}: FY2022 es cero, negativo o ausente; índice no calculable.`);
   const data=peerYears.map(yr=>{
     const raw=m.get(yr)?.[field];
     if(missing(raw)||badBaseline)return null;
     const v=indexed?raw/base*100:raw;
     if(Number.isFinite(v))all.push(v);
     return v;
   });
   if(missing(m.get(2026)?.[field]))notes.push(`${company.name}: FY2026 aún no disponible (último FY${Math.max(...company.records.map(r=>r.year))}).`);
   return {company,data};
 });
 if(!all.length){area.innerHTML='<p class="mini-caption">No hay datos suficientes para esta selección y este tipo de gráfico. Cambia la métrica o la escala.</p>';detail.textContent=notes.join(' ');return;}
 const W=900,H=288,left=73,right=29,top=24,bottom=50,w=W-left-right,h=H-top-bottom;
 let min=Math.min(0,...all),max=Math.max(0,...all);
 if(max===min){max+=1;min-=1;}
 const margin=(max-min)*.07;min=min<0?min-margin:min;max+=margin;
 const x=i=>left+i*w/(peerYears.length-1);
 const y=v=>top+h-(v-min)/(max-min)*h;
 const units=indexed?'índice':pct?'%':' B$';
 let svg=`<svg viewBox="0 0 ${W} ${H}" role="group" aria-label="Comparativa SEC de ${esc(peerMetrics[field])} por ejercicios 2022 a 2026"><title>Comparativa de ${esc(peerMetrics[field])}, ${indexed?'índice base FY2022':'datos anuales SEC'}</title>`;
 for(let j=0;j<=4;j++){const value=min+(max-min)*j/4, yy=y(value);
   svg+=`<line class="chart-grid" x1="${left}" y1="${yy}" x2="${W-right}" y2="${yy}"/><text class="chart-label" x="${left-12}" y="${yy+4}" text-anchor="end">${format(value, indexed?0:1)}${pct?'%':''}</text>`;
 }
 peerYears.forEach((yr,i)=>svg+=`<text class="chart-label" x="${x(i)}" y="${H-9}" text-anchor="middle">${yr}</text>`);
 series.forEach(({company,data})=>{
   let fragment=[];
   const flush=()=>{if(fragment.length>1)svg+=`<path d="${fragment.join(' ')}" fill="none" stroke="${company.color}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>`;fragment=[];};
   data.forEach((v,i)=>{
     if(v===null){flush();return;}
     fragment.push((fragment.length?'L':'M')+x(i).toFixed(1)+','+y(v).toFixed(1));
   });flush();
   data.forEach((v,i)=>{
     if(v===null)return;
     const actual=company.records.find(r=>r.year===peerYears[i]);
     const label=`${company.name}, FY${peerYears[i]} (cierre ${actual?.close||'—'}), ${peerMetrics[field]}: ${format(v,indexed?1:2)} ${units}`;
     svg+=`<circle class="chart-point peer-point" tabindex="0" role="button" data-year="${peerYears[i]}" cx="${x(i)}" cy="${y(v)}" r="5" fill="${company.color}" stroke="#152637" aria-label="${esc(label)}"><title>${esc(label)}</title></circle>`;
   });
 });
 svg+='</svg>';
 svg+='<div class="chart-legend peer-legend">'+series.map(({company})=>`<span><i style="background:${company.color}"></i>${esc(company.name)} (${company.ticker})</span>`).join('')+'</div>';
 area.innerHTML=svg;
 const active=year=>{
   peerActiveYear=year;
   qa('#peer-chart .peer-point').forEach(el=>el.classList.toggle('active',Number(el.dataset.year)===year));
   const parts=series.map(({company,data})=>{
     const v=data[peerYears.indexOf(year)];
     const str=v==null?'sin dato':`${format(v,indexed?1:2)}${units}`;
     const close=company.records.find(r=>r.year===year)?.close;
     return `<span class="peer-detail-item" style="--series:${company.color}"><i></i><b>${esc(company.name)}</b>: ${str}${close?` <small>(${esc(close)})</small>`:''}</span>`;
   });
   detail.innerHTML=`<strong>FY${year}</strong><div class="peer-detail-items">${parts.join('')}</div>`;
 };
 qa('#peer-chart .peer-point').forEach(el=>{
   const act=()=>active(Number(el.dataset.year));
   el.addEventListener('pointerenter',act);el.addEventListener('focus',act);el.addEventListener('click',act);
   el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();act();}});
 });
 active(peerActiveYear);
 const footer=DATA.peerHistoryNote||'Fuente SEC EDGAR; años fiscales no totalmente sincronizados.';
 q('#peer-footnote').textContent=footer+(notes.length?' ⚠ '+notes.join(' '):'');
};
qa('#peer-companies input').forEach(el=>el.addEventListener('change',()=>{
 if(!peerSelected().length)el.checked=true;
 renderPeers();
}));
q('#peer-metric').addEventListener('change',renderPeers);
q('#peer-scale').addEventListener('change',renderPeers);
q('#peer-all').addEventListener('click',()=>{peerInputs.forEach(el=>el.checked=true);renderPeers()});
q('#peer-only-msft').addEventListener('click',()=>{peerInputs.forEach(el=>el.checked=el.value==='MSFT');renderPeers()});
renderPeers();
plot('#return-chart','#return-detail',['roic','roe'],4,true);
plot('#cash-chart','#cash-detail',['cfo','capex','fcf']);
const sum=DATA.business_segments.reduce((a,d)=>a+d.value,0);q('#segments').innerHTML=DATA.business_segments.map(d=>`<div class="segment-row"><div class="segment-label"><span>${esc(d.name)}</span><b>${format(d.value)} B$</b></div><div class="segment-track"><div class="segment-fill" style="width:${(d.value/sum*100).toFixed(2)}%"></div></div><div class="segment-grow">${d.growth>=0?'+':''}${d.growth}% en FY2026 · ${(d.value/sum*100).toFixed(1)}% de los segmentos</div></div>`).join('');
q('#peer-rows').innerHTML=DATA.peers.map(d=>`<tr class="${d.ticker==='MSFT'?'focus-row':''}"><td>${esc(d.name)} <span style="font-size:10px;color:var(--muted)">${d.ticker}</span></td><td>${format(d.pe,1)}x</td><td>${format(d.ev_ebitda,1)}x</td><td style="color:${d.fcf_yield<0?'var(--red)':'var(--ink)'}">${format(d.fcf_yield,2)}%</td></tr>`).join('');
const F=DATA.financial;
const state={fcf0:DATA.dcf.starting_fcf,g1:18,g2:10,r:9,terminal:3.5,price:DATA.price};
const dcf=(a,flag=false)=>{
 const {fcf0,g1,g2,r,terminal}=a;if(r<=terminal)return {valid:false};let f=fcf0,pv=0;
 for(let t=1;t<=10;t++){f*=1+(t<=5?g1:g2)/100;pv+=f/(1+r/100)**t}
 const tv=f*(1+terminal/100)/(r/100-terminal/100)/(1+r/100)**10;
 return {valid:true,value:(pv+tv)/DATA.shares_billion,terminalPct:100*tv/(pv+tv)};
};
const controls=['fcf0','g1','g2','r','terminal'];
function updateDCF(){controls.forEach(k=>{if(k==='fcf0')q('#fcf0-v').textContent=format(state[k],1)+' B$';else q('#'+k+'-v').textContent=format(state[k],k==='terminal'?2:1)+' %'});q('#market-v').textContent=format(state.price,2)+' $';
 const res=dcf(state),bad=q('#dcf-invalid');bad.hidden=res.valid;if(!res.valid){q('#dcf-value').innerHTML='— <span>$</span>';q('#dcf-sign').textContent='Hipótesis incompatibles';return}
 q('#dcf-value').innerHTML=`${format(res.value,1)} <span>$</span>`;
 const upside=(res.value/state.price-1)*100;q('#dcf-sign').textContent=`${upside>=0?'+':''}${format(upside,1)} % frente al precio de ${format(state.price,2)} $`;
 q('#dcf-sign').style.color=upside>0?'var(--teal)':'var(--orange)';
 const refs=[res.value,state.price,DATA.analysts.target],denom=Math.max(...refs)*1.12;
 [['bar-dcf',refs[0]],['bar-market',refs[1]],['bar-consensus',refs[2]]].forEach(([id,val])=>q('#'+id).style.width=(val/denom*100)+'%');
 q('#safety').textContent=format(res.value*.8,1)+' $';q('#terminal-weight').textContent=format(res.terminalPct,0)+' %';q('#fcf-input').textContent=format(state.fcf0,1)+' B$';
 const target=state.price;let lo=-10,hi=90;const v0=dcf({...state,g1:lo}).value,v1=dcf({...state,g1:hi}).value;let reverse='Fuera de rango';
 if(v0<=target&&v1>=target){for(let j=0;j<80;j++){const mid=(lo+hi)/2;if(dcf({...state,g1:mid}).value<target)lo=mid;else hi=mid}reverse='~'+format((lo+hi)/2,1)+' %'}
 q('#reverse').textContent=reverse;
}
function preset(name){const c=DATA.dcf.cases[name];Object.assign(state,{fcf0:DATA.dcf.starting_fcf,g1:c.g1,g2:c.g2,r:c.r,terminal:c.terminal,price:DATA.price});controls.forEach(k=>q('#'+k).value=state[k]);q('#market-price').value=state.price;qa('[data-case]').forEach(el=>el.classList.toggle('selected',el.dataset.case===name));updateDCF()}
qa('[data-case]').forEach(b=>b.addEventListener('click',()=>preset(b.dataset.case)));
controls.forEach(k=>q('#'+k).addEventListener('input',e=>{state[k]=Number(e.target.value);qa('[data-case]').forEach(b=>b.classList.remove('selected'));updateDCF()}));
q('#market-price').addEventListener('input',e=>{state.price=Math.max(1,Number(e.target.value)||1);updateDCF()});
q('#reset-dcf').addEventListener('click',()=>preset('base'));preset('base');
q('#question-list').innerHTML=DATA.questions.map(([question,answer])=>`<details><summary>${esc(question)}</summary><p>${esc(answer)}</p></details>`).join('');
const glossary=new Map(DATA.glossary);
const modal=q('#term-dialog');function openTerm(term){const info=glossary.get(term);if(!info)return;q('#term-title').textContent=term;q('#term-text').textContent=info;if(typeof modal.showModal==='function')modal.showModal();else alert(term+' — '+info)}
qa('[data-term]').forEach(b=>b.addEventListener('click',()=>openTerm(b.dataset.term)));
q('#glossary-list').innerHTML=DATA.glossary.map(([t,d])=>`<button type="button" data-gloss="${esc(t)}" title="${esc(d)}">${esc(t)} ↗</button>`).join('');
qa('[data-gloss]').forEach(b=>b.addEventListener('click',()=>openTerm(b.dataset.gloss)));
q('#gloss-search').addEventListener('input',e=>{const t=e.target.value.toLowerCase();qa('[data-gloss]').forEach(b=>{const term=b.dataset.gloss;b.hidden=!(term.toLowerCase().includes(t)||glossary.get(term).toLowerCase().includes(t))})});
q('#sources-list').innerHTML=DATA.sources.map(s=>`<div class="source-card"><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">[${esc(s.id)}] ${esc(s.name)} ↗</a><p>${esc(s.detail)}</p></div>`).join('');
q('#ask-copy').addEventListener('click',async()=>{let userText=q('#custom-question').value.trim();if(!userText){q('#copy-status').textContent='Escribe una pregunta primero.';return}
 const prompt=`Actúa como analista fundamental independiente y mentor. Analiza Microsoft (NASDAQ:MSFT) a fecha 13/10/2026 con datos verificables SEC FY2022–FY2026 (10-K y 10-Q), siguiendo ingresos→márgenes→ROIC→balance→CFO-CAPEX/FCF→valoración. Distingue dato SEC, hipótesis y estimaciones; no inventes cifras. El FCF FY2026 es 66,987 B$, CAPEX 115,948 B$, CFO 182,935 B$; precio de referencia 541,15 USD (12/10). Responde con escenarios negativo/base/positivo, indicadores que invalidan la tesis y riesgos. Mi pregunta es: ${userText}`;
 try{await navigator.clipboard.writeText(prompt);q('#copy-status').textContent='✓ Consulta copiada. Pégala en ChatGPT.'}catch(_){let f=document.createElement('textarea');f.value=prompt;document.body.append(f);f.select();document.execCommand('copy');f.remove();q('#copy-status').textContent='Consulta preparada. Puedes pegarla en ChatGPT.'}
});
const root=document.documentElement;let saved=null;try{saved=localStorage.getItem('af-theme')}catch(_){/* local-only preview */}if(saved==='light')root.dataset.theme='light';
q('#theme-btn').addEventListener('click',()=>{root.dataset.theme=root.dataset.theme==='light'?'dark':'light';try{localStorage.setItem('af-theme',root.dataset.theme)}catch(_){}});
const obs=new IntersectionObserver(entries=>{entries.filter(e=>e.isIntersecting).forEach(e=>{qa('.sidebar a').forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+e.target.id))})},{rootMargin:'-15% 0px -75% 0px'});qa('main > section[id]').forEach(s=>obs.observe(s));
})();