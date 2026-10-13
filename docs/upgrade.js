/* A.Fundamental 2.3: additive layer on top of complete 2.1 dashboard. */
(()=>{'use strict';
const D=window.AF_DATA?.AF23;
if(!D){console.error('No AF23 data available');return;}
const $=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
const money=['revenue','ebit','net_income','cfo','capex','fcf','assets','equity','debt_total','cash','net_debt','ebitda_derived','fcf_ttm'];
const pct=['gross_margin','ebit_margin','net_margin','fcf_margin','roic_estimated','roe_avg','roe_ttm'];
const groups={growth:['revenue','ebit','net_income','ebit_margin','net_margin','eps_diluted'],cash:['cfo','capex','fcf','fcf_ttm','fcf_margin'],returns:['gross_margin','ebit_margin','net_margin','fcf_margin','roic_estimated','roe_avg','roe_ttm'],balance:['assets','equity','debt_total','cash','net_debt','netdebt_ebitda']};
const active={company:'MSFT',mode:'annual',group:'growth',quarter:'Q4',count:8,metric:'revenue'};
const cat=D.metricCatalog;
const customName=k=>cat[k]?.name||k;
const getUnit=k=>cat[k]?.unit||'B$';
const fmt=(n,d=1)=>n===null||n===undefined||!Number.isFinite(n)?'—':Number(n).toLocaleString('es-ES',{minimumFractionDigits:d,maximumFractionDigits:d});
const valFmt=(k,v)=>v==null?'—':fmt(v,k==='eps_diluted'?2:(pct.includes(k)?1:(k==='netdebt_ebitda'?2:1)))+' '+getUnit(k);
const absFmt=(k,d)=>d==null?'—':(d>=0?'+':'−')+fmt(Math.abs(d),k==='eps_diluted'||k==='netdebt_ebitda'?2:1)+' '+getUnit(k);
function diff(k,a,b){if(a==null||b==null)return {abs:null,pct:null};const delta=a-b;return {abs:delta,pct:b>0?100*delta/b:null};}
function pctFmt(p){return p===null?'n.m.':(p>=0?'+':'−')+fmt(Math.abs(p),1)+' %';}
function label(r,mode){return mode==='annual'?'FY'+r.fy:('FY'+r.fy+' '+r.q);}
const fyear=r=>r.fy*4+parseInt(r.q?.replace('Q','')||0,10);
function all(){return active.mode==='annual'?D.annual[active.company]:D.quarterly[active.company]}
function visible(){let arr=all().slice();if(active.mode==='same')arr=arr.filter(x=>x.q===active.quarter);if(active.mode==='quarter'&&active.count<24)arr=arr.slice(-active.count);return arr;}
function prevRecord(rec,records){
 const idx=records.findIndex(x=>x.fy===rec.fy && x.q===rec.q && x.end===rec.end);
 if(idx<0)return null;
 if(active.mode==='same')return records.find(r=>r.q===rec.q&&r.fy===rec.fy-1)||null;
 return idx>0?records[idx-1]:null;
}
function chart(container, detail, labels, series, unit){
 const W=1010,H=300,L=60,R=26,T=20,B=54,w=W-L-R,h=H-T-B;
 const values=series.flatMap(s=>s.values.filter(v=>v!==null&&Number.isFinite(v)));
 if(!values.length){container.innerHTML='<div class="af23-empty">Datos no disponibles para el periodo o las compañías elegidas.</div>';detail.textContent='No se representan cifras ausentes.';return;}
 let min=Math.min(...values),max=Math.max(...values);
 if(min>=0)min=0;else min*=1.08;
 if(max<=0)max=0;else max*=1.09;
 const X=i=>L+(labels.length===1?w/2:i*w/(labels.length-1)),Y=v=>T+h-((v-min)/(max-min||1))*h;
 let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Gráfica financiera interactiva de ${labels.length} periodos">`;
 for(let j=0;j<5;j++){let v=min+j*(max-min)/4,y=Y(v);svg+=`<line class="chart-grid" x1="${L}" y1="${y}" x2="${W-R}" y2="${y}"/><text class="chart-label" x="${L-9}" y="${y+4}" text-anchor="end">${fmt(v,1)}</text>`;}
 const stride=labels.length>18?3:(labels.length>9?2:1);
 labels.forEach((lab,i)=>{if(i%stride===0||i===labels.length-1)svg+=`<text class="chart-label" x="${X(i)}" y="${H-15}" text-anchor="middle">${lab.replace('FY','').replace(' ','·')}</text>`});
 series.forEach((s,si)=>{
  let d='',open=false;
  s.values.forEach((v,i)=>{if(v==null||!Number.isFinite(v)){open=false;return;}d+=(open?'L':'M')+X(i).toFixed(1)+','+Y(v).toFixed(1)+' ';open=true;});
  svg+=`<path class="chart-series" d="${d}" stroke="${s.color}" stroke-width="3"/>`;
  s.values.forEach((v,i)=>{if(v==null||!Number.isFinite(v))return;svg+=`<circle class="chart-point af23-point" tabindex="0" role="button" data-period="${i}" cx="${X(i)}" cy="${Y(v)}" r="5" fill="${s.color}" stroke="#091a26"><title>${s.name}, ${labels[i]}: ${fmt(v,2)} ${unit}</title></circle>`;});
 });svg+='</svg>';
 svg+='<div class="chart-legend">'+series.map(s=>`<span><i style="background:${s.color}"></i>${s.name}</span>`).join('')+'</div>';
 container.innerHTML=svg;
 const activate=i=>{const items=series.map(s=>`<span><b style="color:${s.color}">${s.name}</b>: ${s.values[i]==null?'—':fmt(s.values[i],2)+' '+unit}</span>`);detail.innerHTML=`<strong>${labels[i]}</strong> · ${items.join(' · ')}`;container.querySelectorAll('.af23-point').forEach(p=>p.classList.toggle('active',Number(p.dataset.period)===i));};
 container.querySelectorAll('.af23-point').forEach(el=>{el.addEventListener('mouseenter',()=>activate(+el.dataset.period));el.addEventListener('click',()=>activate(+el.dataset.period));el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate(+el.dataset.period)}})});
 activate(labels.length-1);
}
function syncSelectors(){
 $('#af23-quarter-wrap').hidden=active.mode!=='same';$('#af23-count-wrap').hidden=active.mode!=='quarter';
 const valid=groups[active.group].filter(k=>active.mode==='annual'?k!=='roe_ttm'&&k!=='fcf_ttm':k!=='roic_estimated'&&k!=='roe_avg'&&k!=='eps_diluted'&&k!=='ebitda_derived');
 if(!valid.includes(active.metric))active.metric=valid.find(k=>!['roe_ttm','netdebt_ebitda'].includes(k))||valid[0];
 for(const sel of ['#af23-chart-metric','#af23-compare-metric']){
  const element=$(sel),previous=element.value;
  element.innerHTML=valid.map(k=>`<option value="${k}">${customName(k)}</option>`).join('');
  element.value=sel==='#af23-chart-metric'?active.metric:(valid.includes(previous)?previous:active.metric);
 }
}
function renderTable(){
 const arr=visible(),allRows=all(),cols=groups[active.group].filter(k=>active.mode==='annual'?k!=='roe_ttm'&&k!=='fcf_ttm':k!=='roic_estimated'&&k!=='roe_avg'&&k!=='eps_diluted'&&k!=='ebitda_derived');
 const head=['<thead><tr><th>Métrica</th>',...arr.map(r=>`<th>${label(r,active.mode)}<small>${r.end}</small></th>`),'</tr></thead>'].join('');
 let rows='';
 for(const metric of cols){
  const meta=cat[metric]||{};
  const kind=meta.kind==='raw'?'SEC':meta.kind==='calculated'?'ƒx':'proxy';
  rows+=`<tr><th><span>${meta.name||metric}</span><small class="af23-origin">${kind} · <button type="button" class="af23-info-btn" title="Ver definición y fórmula" data-def="${metric}">ⓘ Fórmula</button></small></th>`;
  for(const r of arr){let before=prevRecord(r,allRows),change=diff(metric,r[metric],before?.[metric]);
    rows+=`<td><strong>${valFmt(metric,r[metric])}</strong><span class="af23-delta">${absFmt(metric,change.abs)}</span><span class="af23-percent">${pctFmt(change.pct)}</span></td>`;
  }rows+='</tr>';
 }
 $('#af23-table').innerHTML=head+'<tbody>'+rows+'</tbody>';
 $$('#af23-table .af23-info-btn').forEach(btn=>btn.addEventListener('click',()=>{
 const m=cat[btn.dataset.def],txt=[m.name,m.definition,m.formula||'Dato proveniente de etiquetas SEC/registro del motor.'].join(' · ');
 $('#af23-view-note').textContent=txt;
 }));
 $('#af23-view-note').textContent=active.mode==='annual'?'Valores de FY2022 a FY2026 según disponibilidad; variación contra el ejercicio fiscal anterior.':active.mode==='quarter'?'Trimestres INDIVIDUALES: variación absoluta y relativa respecto al trimestre inmediatamente anterior. ROE TTM, FCF TTM cuando hay cobertura.':'Cada columna es el mismo trimestre fiscal en un año distinto; variación interanual YoY y comparación directa de periodos.';
 const keys=arr.map(r=>label(r,active.mode));
 const chosen=active.metric,info=cat[chosen];chart($('#af23-metric-chart'),$('#af23-hover'),keys,[{name:info.name,color:'#4cdbbd',values:arr.map(r=>r[chosen])}],getUnit(chosen));
 fillPairControls(arr,cols);
 updateReading();
}
function fillPairControls(arr,cols){
 for(const sel of ['#af23-compare-a','#af23-compare-b']){
  const e=$(sel),before=e.value;
  e.innerHTML=arr.map((r,i)=>`<option value="${i}">${label(r,active.mode)}</option>`).join('');
  if(before!==''&&+before>=0&&+before<arr.length)e.value=before;
  else e.value=sel.endsWith('-a')?String(Math.max(0,arr.length-2)):String(arr.length-1);
 }
 if($('#af23-compare-a').value===$('#af23-compare-b').value&&arr.length>1)$('#af23-compare-a').value=String(arr.length-2);
 updatePair();
}
function updatePair(){
 const rows=visible(),a=rows[+$('#af23-compare-a').value],b=rows[+$('#af23-compare-b').value],k=$('#af23-compare-metric').value;
 if(!a||!b){$('#af23-compare-result').textContent='Selecciona dos periodos';return;}
 const d=diff(k,b[k],a[k]);$('#af23-compare-result').innerHTML=`<span><b>${label(a,active.mode)}</b><strong>${valFmt(k,a[k])}</strong></span><span class="af23-versus">⇒</span><span><b>${label(b,active.mode)}</b><strong>${valFmt(k,b[k])}</strong></span><span class="af23-change"><b>Cambio absoluto</b><strong>${absFmt(k,d.abs)}</strong><b>Cambio porcentual</b><strong>${pctFmt(d.pct)}</strong></span>`;
}
function updateReading(){
 const texts={growth:'🟢 Crecimiento: ingresos y EBIT mejoran a largo plazo, pero el beneficio GAAP puede incorporar ganancias de inversiones; no extrapolar un único trimestre.',cash:'🟠 Caja: CFO aumenta; CAPEX elevado hace que el FCF no siga el ritmo. Vigilar FCF TTM y recuperación del rendimiento sobre la inversión.',returns:'🟠 Retornos: márgenes operativos fuertes y ROIC anual elevado pero descendente. ROIC trimestral no calculado sin una base comparable robusta.',balance:'🟢 Balance: deuda neta manejable. Diferenciar efectivo de inversiones a corto plazo y de arrendamientos. Una deuda neta negativa indica caja neta.'};
 $('#af23-reading').textContent=texts[active.group];
}
const peerState={metric:'roic_estimated',sel:new Set(['MSFT','ORCL','GOOGL','AMZN','CRM'])};
function renderPeers(){
 const yrs=[2022,2023,2024,2025,2026],k=peerState.metric,unit=getUnit(k),series=[];
 for(const [ticker,name] of Object.entries(D.companies))if(peerState.sel.has(ticker))series.push({name,color:D.colors[ticker],values:yrs.map(y=>D.annual[ticker].find(r=>r.fy===y)?.[k]??null)});
 chart($('#af23-peer-chart'),$('#af23-peer-detail'),yrs.map(y=>'FY'+y),series,unit);
 const header='<table class="af23-data-table af23-peer-table"><thead><tr><th>Compañía</th>'+yrs.map(y=>`<th>FY${y}</th>`).join('')+'</tr></thead><tbody>';
 const rows=series.map(s=>'<tr><th>'+s.name+'</th>'+s.values.map(v=>`<td><strong>${valFmt(k,v)}</strong></td>`).join('')+'</tr>').join('');
 $('#af23-peer-tbl').innerHTML=header+rows+'</tbody></table>';
}
$('#af23-company').innerHTML=Object.entries(D.companies).map(([k,n])=>`<option value="${k}">${n} (${k})</option>`).join('');
$('#af23-peer-checks').insertAdjacentHTML('beforeend',Object.entries(D.companies).map(([ticker,name])=>`<label><input type="checkbox" value="${ticker}" checked> <span class="series-dot" style="--series:${D.colors[ticker]}"></span>${name}</label>`).join(''));
$('#af23-company').addEventListener('change',e=>{active.company=e.target.value;renderTable()});
$('#af23-mode').addEventListener('change',e=>{active.mode=e.target.value;syncSelectors();renderTable()});
$('#af23-quarter').addEventListener('change',e=>{active.quarter=e.target.value;renderTable()});
$('#af23-count').addEventListener('change',e=>{active.count=+e.target.value;renderTable()});
$('#af23-group').addEventListener('change',e=>{active.group=e.target.value;syncSelectors();renderTable()});
$('#af23-chart-metric').addEventListener('change',e=>{active.metric=e.target.value;renderTable()});
['#af23-compare-a','#af23-compare-b','#af23-compare-metric'].forEach(sel=>$(sel).addEventListener('change',updatePair));
$('#af23-peer-metric').addEventListener('change',e=>{peerState.metric=e.target.value;renderPeers()});
$$('#af23-peer-checks input').forEach(el=>el.addEventListener('change',()=>{
 if(!el.checked&&peerState.sel.size===1){el.checked=true;return;}
 if(el.checked)peerState.sel.add(el.value);else peerState.sel.delete(el.value);renderPeers();
}));
$('#af23-peer-all').addEventListener('click',()=>{$$('#af23-peer-checks input').forEach(e=>e.checked=true);peerState.sel=new Set(Object.keys(D.companies));renderPeers()});
$('#af23-peer-msft').addEventListener('click',()=>{$$('#af23-peer-checks input').forEach(e=>e.checked=e.value==='MSFT');peerState.sel=new Set(['MSFT']);renderPeers()});
syncSelectors();renderTable();renderPeers();
})();