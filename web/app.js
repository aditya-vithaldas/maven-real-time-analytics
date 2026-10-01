import {LiveConversation} from './live.js';
const $=id=>document.getElementById(id);
const session=crypto.randomUUID();let config,mode=1,live=null;
const states=Object.fromEntries([1,2,3,4].map(id=>[id,{messages:[],busy:false,draft:'',voiceInput:'',voiceOutput:'',voiceTrace:[]}]));
const el=(tag,cls,text)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node;};
const fmt=value=>typeof value==='number'?new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(value):String(value??'—');
async function api(path,data){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const result=await r.json();if(!r.ok)throw Error(result.error||'Request failed');return result;}
function render(){
 const current=config.modes.find(m=>m.id===mode),state=states[mode];
 for(const b of $('tabs').children){const selected=Number(b.dataset.mode)===mode;b.setAttribute('aria-selected',selected);b.tabIndex=selected?0:-1;}
 $('panel').setAttribute('aria-labelledby','tab-'+mode);$('level').textContent=`LEVEL 0${mode} / 04`;$('title').textContent=current.name;$('description').textContent=current.description;
 $('prompt').textContent=current.prompt;$('prompt-length').textContent=current.prompt.length.toLocaleString()+' characters';
 $('prompt-inheritance').textContent=current.summaryBase||'';$('prompt-inheritance').hidden=!current.summaryBase;
 $('prompt-heads').start=current.summary[0].label.charCodeAt(0)-64;
 $('prompt-heads').replaceChildren(...current.summary.map(head=>{const item=el('li'),letter=el('span','summary-letter',head.label),text=el('div');letter.setAttribute('aria-hidden','true');text.append(el('strong','',head.heading),el('p','',head.detail));item.append(letter,text);return item;}));
 $('question').value=state.draft;$('send').disabled=state.busy;$('question').disabled=state.busy;
 renderMessages();$('status').textContent=state.busy?'Formulating the query and reading the database…':live?'Listening · Gemini 3.8 Live':'Ready to explore';
}
function currentAnswer(state){
 if(state.voiceInput||state.voiceOutput||state.voiceTrace.length)return {text:state.voiceOutput,live:true,firstSpeechMs:state.voiceFirstSpeechMs,usage:state.voiceUsage,trace:state.voiceTrace,queries:state.voiceTrace.filter(t=>t.name==='run_query'&&!t.result.error).map(t=>t.result)};
 const lastUser=state.messages.findLastIndex(m=>m.role==='user');
 return state.messages.slice(lastUser+1).findLast(m=>m.role==='assistant'||m.role==='error');
}
function renderMessages(){
 const state=states[mode],box=$('messages');box.replaceChildren();
 const latestUser=state.messages.findLast(m=>m.role==='user');
 const question=state.voiceInput||latestUser?.text;
 const msg=currentAnswer(state);
 if(!question&&!msg){
  const empty=el('div','empty');empty.append(el('div','empty-icon','✦'),el('h3','',`Try ${config.modes.find(m=>m.id===mode).name.toLowerCase()}`),el('p','','One question. One primary result. Ask for a total, a trend, or a comparison.'));
  const suggestions=el('div','suggestions');for(const q of ['What were my sales yesterday?','Show daily sales for September 2026.','Compare sales by region.']){const b=el('button','',q);b.type='button';b.append(el('span','','↗'));b.onclick=()=>{states[mode].draft=q;$('question').value=q;$('question').focus();};suggestions.append(b);}empty.append(suggestions);box.append(empty);
 }else{
  if(question){const current=el('div','current-question');current.append(el('span','eyebrow','CURRENT QUESTION'),el('h3','',question));box.append(current);}
  if(msg){
   const item=el('article','primary-result');
   const selected=msg.trace?.findLast(t=>t.name==='show_widget'&&t.result.widget)?.result;
   const query=selected?.query||msg.queries?.filter(q=>q.rows?.length).at(-1);
   if(query){renderChart(item,query,selected?.widget);}
   if(msg.text)item.append(el('p',msg.role==='error'?'result-error':'result-explanation',msg.text));
   if(!query&&!msg.text)item.append(el('p','',state.busy?'Reading the database…':'Preparing your result…'));
   if(msg.trace?.length){const details=el('details','evidence');details.append(el('summary','',`Database evidence · ${msg.trace.length} tool calls`));
    for(const t of msg.trace){details.append(el('pre','',t.name+'\n'+JSON.stringify(t.args,null,2)+(t.result.error?'\nERROR: '+t.result.error:'')));if(t.result.rows)details.append(renderTable(t.result));else if(t.name!=='show_widget'&&!t.result.error)details.append(el('pre','',JSON.stringify(t.result,null,2)));}item.append(details);}
   box.append(item);
  }else box.append(el('div','pending-result','Formulating your query and reading the database…'));
 }
 renderMetrics(msg,state);
 box.scrollTop=0;
}
function renderMetrics(msg,state){
 const voice=msg?.live||(!state.busy&&Boolean(live))||!msg&&!state.busy;
 const elapsed=voice?msg?.firstSpeechMs??state.voiceFirstSpeechMs??(state.voiceEndedAt!==undefined?Math.max(0,performance.now()-state.voiceEndedAt):undefined):state.busy&&state.requestStartedAt?performance.now()-state.requestStartedAt:msg?.responseMs??msg?.elapsedMs;
 const row=el('div','metric');row.append(el('span','',voice?'Time to first speech':'Text completion time'),el('strong','',typeof elapsed==='number'?(elapsed/1000).toFixed(2)+'s':'—'));
 row.title=voice?'From the end of your question to the first audible assistant audio. The value freezes when speech starts.':'Time until the complete typed response arrives.';
 $('timings').dataset.metric=voice?'first-speech':'text-completion';$('timings').dataset.elapsedMs=typeof elapsed==='number'?String(elapsed):'';
 $('timings').replaceChildren(row);
}
function renderTable(q){const wrap=el('div','table-wrap'),table=el('table'),head=el('thead'),tr=el('tr');q.columns.forEach(c=>tr.append(el('th','',c)));head.append(tr);table.append(head);const body=el('tbody');for(const row of q.rows){const r=el('tr');row.forEach(v=>r.append(el('td','',fmt(v))));body.append(r);}table.append(body);wrap.append(table);if(q.truncated)wrap.append(el('p','warning','Showing the first 200 rows; the result is truncated.'));return wrap;}
function renderChart(item,q,widget){
 const numeric=widget?.valueColumn?q.columns.indexOf(widget.valueColumn):q.columns.findIndex((_,i)=>q.rows.some(r=>typeof r[i]==='number'));
 const label=widget?.labelColumn?q.columns.indexOf(widget.labelColumn):q.columns.findIndex((_,i)=>i!==numeric&&q.rows.some(r=>typeof r[i]==='string'));
 const dated=label>=0&&q.rows.every(r=>typeof r[label]==='string'&&/^\d{4}-\d{2}/.test(r[label]));
 const kind=widget?.type||(numeric<0?'table':q.rows.length===1?'number':dated?'line':'bar');
 const title=widget?.title||q.columns[numeric]||'Query result',unit=widget?.unit||'';
 const visual=el('section','result-visual');visual.append(el('div','widget-type',({number:'TOTAL',line:'TIME SERIES',bar:'COMPARISON',table:'DETAILS'})[kind]),el('h3','widget-title',title));
 if(kind==='number'){
  const card=el('div','number-card');card.append(el('strong','',fmt(q.rows[0][numeric])),el('span','',unit||q.columns[numeric]));visual.append(card);
 }else if(kind==='table')visual.append(renderTable(q));
 else if(kind==='line'){
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 620 280');svg.setAttribute('role','img');svg.setAttribute('aria-label',title+' trend');svg.classList.add('line-chart');
  const lineRows=q.rows.filter(r=>typeof r[numeric]==='number'&&Number.isFinite(r[numeric])).slice().sort((a,b)=>dated?String(a[label]).localeCompare(String(b[label])):0);
  if(!lineRows.length){visual.append(renderTable(q));item.append(visual);return;}
  const values=lineRows.map(r=>r[numeric]),min=Math.min(0,...values),max=Math.max(...values,min+1),span=max-min;
  const points=values.map((v,i)=>[58+i*540/Math.max(1,values.length-1),230-(v-min)/span*195]);
  const add=(tag,attrs,text)=>{const node=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))node.setAttribute(k,v);if(text!==undefined)node.textContent=text;svg.append(node);};
  for(let i=0;i<5;i++){const y=230-i*195/4;add('line',{x1:58,x2:600,y1:y,y2:y,stroke:'#e5eaf4'});add('text',{x:48,y:y+4,'text-anchor':'end',fill:'#78879f','font-size':10},new Intl.NumberFormat('en',{notation:'compact',maximumFractionDigits:1}).format(min+span*i/4));}
  add('polyline',{points:points.map(p=>p.join(',')).join(' '),fill:'none',stroke:'#456dde','stroke-width':3,'stroke-linejoin':'round'});
  for(let i=0;i<points.length;i++){const dot=document.createElementNS(ns,'circle');dot.setAttribute('cx',points[i][0]);dot.setAttribute('cy',points[i][1]);dot.setAttribute('r',3);dot.setAttribute('fill','#456dde');const tooltip=document.createElementNS(ns,'title');tooltip.textContent=fmt(lineRows[i][label])+': '+fmt(values[i])+' '+unit;dot.append(tooltip);svg.append(dot);}
  for(const i of new Set([0,Math.floor((lineRows.length-1)/2),lineRows.length-1]))add('text',{x:points[i][0],y:253,'text-anchor':i===lineRows.length-1?'end':i===0?'start':'middle',fill:'#78879f','font-size':10},String(lineRows[i][label]).slice(0,10));
  visual.append(svg,el('p','chart-caption',(unit?unit+' · ':'')+lineRows.length+' data points · hover a point for its value'));
 }else{
  const values=q.rows.filter(r=>typeof r[numeric]==='number'&&Number.isFinite(r[numeric])).slice(0,10),max=Math.max(...values.map(r=>Math.abs(Number(r[numeric])||0)),1),bars=el('div','bars');
  values.forEach((r,i)=>{const row=el('div','bar-row');const text=label>=0?fmt(r[label]):String(i+1),l=el('span','bar-label',text);l.title=text;const track=el('div','bar-track'),bar=el('div','bar');bar.style.width=(Math.abs(Number(r[numeric])||0)/max*100)+'%';if(Number(r[numeric])<0)bar.classList.add('negative');track.append(bar);row.append(l,track,el('span','bar-value',fmt(r[numeric])));bars.append(row);});visual.append(bars);if(unit)visual.append(el('p','chart-caption',unit));if(q.rows.length>10)visual.append(el('p','warning','Chart shows the first 10 rows. Full returned data is available in database evidence.'));
 }
 if(kind!=='table'&&q.rows.some(r=>r[numeric]===null||typeof r[numeric]!=='number'))visual.append(el('p','warning','Missing or non-numeric values are omitted from the chart. See evidence for the source rows.'));
 if(q.truncated)visual.append(el('p','warning','Result truncated to the first 200 rows. Narrow the query for a complete chart.'));
 item.append(visual);
}
function stopLive(){if(live)live.close();live=null;$('mic').classList.remove('active');$('mic').querySelector('span').textContent='Start talking';$('voice-status').textContent='Gemini 3.8 Live';$('status').textContent='Ready to explore';}
function choose(id){if(id===mode)return;states[mode].draft=$('question').value;stopLive();mode=id;render();}
$('form').onsubmit=async event=>{
 event.preventDefault();const id=mode,state=states[id],question=$('question').value.trim();if(!question||state.busy)return;
 stopLive();state.messages.push({role:'user',text:question});state.draft='';state.busy=true;
 const started=performance.now();state.requestStartedAt=started;render();
 try{const result=await api('/api/query',{mode:id,question,session});state.messages.push({role:'assistant',text:result.answer,...result,responseMs:performance.now()-started});}
 catch(error){state.messages.push({role:'error',text:error.message,responseMs:performance.now()-started});}
 finally{state.busy=false;if(mode===id)render();}
};
$('question').addEventListener('input',()=>states[mode].draft=$('question').value);
$('question').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();$('form').requestSubmit();}});
$('copy').onclick=async()=>{try{await navigator.clipboard.writeText(config.modes.find(m=>m.id===mode).prompt);$('copy').textContent='Copied';setTimeout(()=>$('copy').textContent='Copy',1400);}catch{$('status').textContent='Select the prompt text to copy it.';}};
$('show-app-prompt').onclick=async()=>{
 $('app-prompt-dialog').showModal();$('app-prompt').textContent='Loading app-building prompt…';$('copy-app-prompt').disabled=true;
 try{const r=await fetch('/api/app-prompt');if(!r.ok)throw Error('Could not load the app-building prompt.');const result=await r.json();$('app-prompt').textContent=result.prompt;$('app-prompt').scrollTop=0;$('copy-app-prompt').disabled=false;}
 catch(error){$('app-prompt').textContent=error.message;}
};
$('close-app-prompt').onclick=()=>$('app-prompt-dialog').close();
$('app-prompt-dialog').onclick=event=>{if(event.target!==$('app-prompt-dialog'))return;const box=event.target.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)event.target.close();};
$('copy-app-prompt').onclick=async()=>{try{await navigator.clipboard.writeText($('app-prompt').textContent);$('copy-app-prompt').textContent='Copied';setTimeout(()=>$('copy-app-prompt').textContent='Copy',1400);}catch{$('copy-app-prompt').textContent='Select text to copy';}};
$('mic').onclick=async()=>{
 if(live){stopLive();return;}if(states[mode].busy)return;
 const id=mode,state=states[id];state.voiceFirstSpeechMs=undefined;state.voiceEndedAt=undefined;$('status').textContent='Connecting to Gemini 3.8 Live…';$('mic').classList.add('active');$('mic').querySelector('span').textContent='Stop talking';
 const connection=new LiveConversation({
  status:s=>{if(mode===id){$('status').textContent=s+' · Gemini 3.8 Live';$('voice-status').textContent=s;}},
  questionStart:()=>{state.voiceFirstSpeechMs=undefined;state.voiceEndedAt=undefined;if(mode===id)renderMetrics({live:true},state);},
  questionEnd:(at,source)=>{if(state.voiceFirstSpeechMs!==undefined)return;state.voiceEndedAt=at;state.voiceTimingSource=source;if(mode===id)renderMetrics({live:true},state);},
  input:text=>{if(!state.voiceStartedAt)state.voiceStartedAt=performance.now();state.voiceInput+=text;if(mode===id)renderMessages();},output:text=>{state.voiceOutput+=text;if(mode===id)renderMessages();},
  tool:trace=>{state.voiceTrace.push(trace);if(mode===id)renderMessages();if(mode===id)$('status').textContent=trace.name==='run_query'?'Database returned '+(trace.result.rows?.length||0)+' rows':'Discovering database structure';},
  firstReply:timing=>{state.voiceFirstSpeechMs=timing.elapsedMs;state.voiceEndedAt=undefined;state.voiceTimingSource=timing.source;if(mode===id)renderMetrics({live:true,firstSpeechMs:timing.elapsedMs},state);},
  metrics:usage=>{state.voiceUsage=usage;},
  interrupted:()=>{if(state.voiceOutput)state.voiceOutput+=' [interrupted]';},
  complete:()=>{if(state.voiceInput)state.messages.push({role:'user',text:state.voiceInput});if(state.voiceOutput||state.voiceTrace.length)state.messages.push({role:'assistant',live:true,text:state.voiceOutput||'Database tool completed.',firstSpeechMs:state.voiceFirstSpeechMs,timingSource:state.voiceTimingSource,usage:state.voiceUsage,trace:state.voiceTrace,queries:state.voiceTrace.filter(t=>t.name==='run_query'&&!t.result.error).map(t=>t.result)});state.voiceInput='';state.voiceOutput='';state.voiceTrace=[];state.voiceStartedAt=0;state.voiceEndedAt=undefined;state.voiceUsage=undefined;if(mode===id)renderMessages();},
  error:text=>{state.messages.push({role:'error',text});if(mode===id){stopLive();renderMessages();}}
 });live=connection;
 try{await connection.connect(id);}catch(error){if(live===connection){state.messages.push({role:'error',text:error.message});stopLive();renderMessages();}}
};
window.addEventListener('pagehide',stopLive);
setInterval(()=>{if(config&&(states[mode].busy||states[mode].voiceStartedAt))renderMetrics(currentAnswer(states[mode]),states[mode]);},500);
try{const r=await fetch('/api/config');config=await r.json();
 for(const m of config.modes){const b=el('button','tab');b.id='tab-'+m.id;b.dataset.mode=m.id;b.setAttribute('role','tab');b.setAttribute('aria-controls','panel');b.append(el('span','tab-num',String(m.id)));const text=el('div');text.append(el('strong','',m.name),el('small','',m.description));b.append(text);b.onclick=()=>choose(m.id);b.onkeydown=e=>{let next;if(e.key==='ArrowRight')next=mode%4+1;if(e.key==='ArrowLeft')next=(mode+2)%4+1;if(e.key==='Home')next=1;if(e.key==='End')next=4;if(next){e.preventDefault();choose(next);$('tab-'+next).focus();}};$('tabs').append(b);}
 render();
}catch{$('status').textContent='The local server is unavailable. Start server.py and reload.';}
