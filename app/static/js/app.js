(() => {
  'use strict';
  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => [...r.querySelectorAll(s)];
  const pretty = v => JSON.stringify(v, null, 2);
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const dt = v => { if (!v) return '—'; const d=new Date(v); return Number.isNaN(d.getTime())?String(v):d.toLocaleString('es-CL'); };
  const bytes = n => { if (!Number.isFinite(Number(n))) return '—'; const u=['B','KB','MB','GB','TB']; let x=Number(n),i=0; while(x>=1024&&i<u.length-1){x/=1024;i++;} return `${x.toFixed(i?1:0)} ${u[i]}`; };
  const riskClass = r => r==='DANGEROUS'?'status--offline':r==='WRITE'?'status--warning':'status--online';
  const status = (ok,label) => `<span class="status ${ok?'status--online':'status--offline'}">${esc(label)}</span>`;
  function toast(message, ok=true){ const host=$('.toast-stack'); if(!host)return; const n=document.createElement('div'); n.className='toast'+(ok?'':' is-error'); n.textContent=message; host.appendChild(n); setTimeout(()=>n.remove(),4200); }
  async function api(url, opts={}){
    const init={...opts,headers:{'Content-Type':'application/json',...(opts.headers||{})}};
    const res=await fetch(url,init); let body=null; try{body=await res.json();}catch{body={};}
    if(!res.ok){ const e=body?.error; throw Object.assign(new Error(e?.message || body?.detail || `HTTP ${res.status}`),{status:res.status,code:e?.code,body}); }
    return body;
  }

  let agentCatalog=[];
  async function loadCatalog(){ if(agentCatalog.length)return agentCatalog; const d=await api('/api/v1/agents'); agentCatalog=d.agents; return agentCatalog; }
  function findAction(agent,action){ const a=agentCatalog.find(x=>x.id===agent); return a?.actions?.find(x=>x.name===action); }

  const modal=$('#approval-modal'); let modalResolve=null;
  function closeApproval(value=false){ if(!modal)return; modal.classList.add('hidden'); modal.setAttribute('aria-hidden','true'); const r=modalResolve; modalResolve=null; r?.(value); }
  $('#approval-close')?.addEventListener('click',()=>closeApproval(false)); $('#approval-cancel')?.addEventListener('click',()=>closeApproval(false));
  function confirmApproval(summary,detail){
    if(!modal) return Promise.resolve(confirm(summary));
    $('#approval-summary').textContent=summary; $('#approval-detail').textContent=detail; modal.classList.remove('hidden');modal.setAttribute('aria-hidden','false');
    return new Promise(resolve=>{modalResolve=resolve; const btn=$('#approval-confirm'); const handler=()=>{btn.removeEventListener('click',handler);closeApproval(true)};btn.addEventListener('click',handler,{once:true});});
  }

  async function executeControlled(agent,action,payload){
    await loadCatalog(); const info=findAction(agent,action); if(!info) throw new Error('Acción no registrada.');
    if(info.risk_level==='READ'||info.risk_level==='PREPARE') return api(`/api/v1/agents/${encodeURIComponent(agent)}/execute`,{method:'POST',body:JSON.stringify({action,payload})});
    const req=await api('/api/v1/approvals/request',{method:'POST',body:JSON.stringify({agent,action,target:'',payload})});
    const ok=await confirmApproval(`${info.risk_level}: ${agent} / ${action}`,`Approval ID: ${req.approval_id}\nExpira: ${dt(req.expires_at)}\n\nPayload asociado:\n${pretty(payload)}`);
    if(!ok) throw new Error('Acción cancelada por el usuario.');
    const decision=await api(`/api/v1/approvals/${req.approval_id}/decision`,{method:'POST',body:JSON.stringify({decision:'approve'})});
    return api(`/api/v1/agents/${encodeURIComponent(agent)}/execute`,{method:'POST',body:JSON.stringify({action,payload,approval_id:req.approval_id,approval_token:decision.approval_token})});
  }

  const samples={
    list_unread:{source:'microsoft',limit:20},
    send_email:{source:'microsoft',to:['destino@example.com'],subject:'Asunto',body:'Mensaje'},
    list_events:{source:'microsoft',start:new Date().toISOString(),end:new Date(Date.now()+86400000).toISOString(),limit:50},
    create_event:{source:'microsoft',subject:'Reunión',start:new Date(Date.now()+3600000).toISOString(),end:new Date(Date.now()+7200000).toISOString(),timezone:'America/Santiago',attendees:[],body:''},
    list_chats:{limit:30},system_health:{},tcp_check:{host:'127.0.0.1',port:8000,timeout:3},git_status:{path:'C:\\DEV\\AGENTES'},inspect_repo:{path:'C:\\DEV\\AGENTES'},github_repos:{limit:50},run_tests:{path:'C:\\DEV\\AGENTES',command:['python','-m','pytest','-q'],timeout:180},list_tasks:{status:'pending'},create_task:{title:'Nueva tarea',priority:'MEDIUM',source:'ui'},list_reminders:{status:'pending'},find_pending:{},healthcheck:{},security_posture:{}
  };

  async function dashboard(){
    const d=await api('/api/ui/dashboard/summary');
    $('#metric-agents').textContent=d.metrics.agents_total;$('#metric-active').textContent=d.metrics.agents_active;$('#metric-integrations').textContent=d.metrics.integrations_connected;$('#metric-errors').textContent=d.metrics.recent_errors;$('#metric-tasks').textContent=d.metrics.tasks_pending;$('#metric-auto').textContent=d.metrics.automations_enabled;
    $('#dashboard-agents').innerHTML=d.agents.slice(0,6).map(a=>`<article class="agent-card ${a.status==='ONLINE'?'is-running':'is-warning'}"><div class="agent-card__head"><div class="agent-card__icon">${esc(a.id.slice(0,2).toUpperCase())}</div>${status(a.status==='ONLINE',a.status)}</div><h3 class="agent-card__title">${esc(a.display_name)}</h3><p class="agent-card__description">${esc(a.description)}</p><div class="agent-card__footer"><span class="badge">${esc(a.integration||'core')}</span><a class="btn btn--sm btn--secondary" href="/ui/agents#executor" data-agent-open="${esc(a.id)}">ABRIR</a></div></article>`).join('');
    $('#dashboard-health').innerHTML=Object.entries({API:d.health.api,Base:d.health.database,Microsoft:d.health.microsoft,Google:d.health.google,GitHub:d.health.github,Uptime:`${d.health.uptime_seconds}s`}).map(([k,v])=>`<div class="kv-row"><div class="kv-key">${esc(k)}</div><div class="kv-value">${esc(v)}</div></div>`).join('');
    $('#dashboard-audit').innerHTML=d.recent_audit.length?d.recent_audit.map(x=>`<div class="kv-row"><div class="kv-key">${esc(x.agent)}</div><div class="kv-value">${esc(x.action)} · ${esc(x.status)}<br><span class="text-muted">${esc(dt(x.timestamp))}</span></div></div>`).join(''):'<span class="text-muted">Sin eventos.</span>';
    $('#command-form').addEventListener('submit',async e=>{e.preventDefault();const out=$('#command-result');out.textContent='Resolviendo...';try{const r=await api('/api/v1/command',{method:'POST',body:JSON.stringify({text:$('#command-text').value})});out.textContent=pretty(r);toast('Comando ejecutado')}catch(err){out.textContent=pretty(err.body||{error:err.message});toast(err.message,false)}});
  }

  async function agentsPage(){
    const d=await api('/api/v1/agents');agentCatalog=d.agents;const real=d.agents.filter(a=>a.id!=='orchestrator');
    $('#agents-grid').innerHTML=d.agents.map(a=>`<article class="agent-card ${a.status==='ONLINE'?'is-running':'is-warning'}"><div class="agent-card__head"><div class="agent-card__icon">${esc(a.id.slice(0,2).toUpperCase())}</div>${status(a.status==='ONLINE',a.status)}</div><h3 class="agent-card__title">${esc(a.display_name)}</h3><p class="agent-card__description">${esc(a.description)}</p><div class="agent-card__meta"><span class="text-muted">Integración: ${esc(a.integration||'core')}</span><span class="text-muted">Última: ${esc(dt(a.last_execution))}</span><span class="text-muted">Acciones: ${(a.actions||[]).map(x=>`${esc(x.name)} [${esc(x.risk_level)}]`).join(' · ')||'Core'}</span></div><div class="agent-card__footer"><span class="badge">${esc(a.integration||'core')}</span>${a.id==='orchestrator'?'<span class="badge badge--blue">CORE</span>':`<button class="btn btn--sm btn--secondary" data-open-agent="${esc(a.id)}">ABRIR</button>`}</div></article>`).join('');
    const agentSel=$('#agent-select'), actionSel=$('#action-select');agentSel.innerHTML=real.map(a=>`<option value="${esc(a.id)}">${esc(a.display_name)}</option>`).join('');
    function fill(){const a=real.find(x=>x.id===agentSel.value);$('#agent-title').textContent=a?.display_name||'Agente';$('#agent-description').textContent=a?.description||'';$('#agent-category').textContent=a?.integration||'local';actionSel.innerHTML=(a?.actions||[]).map(x=>`<option value="${esc(x.name)}">${esc(x.name)}</option>`).join('');setAction();}
    function setAction(){const a=findAction(agentSel.value,actionSel.value);$('#action-risk').className=`status ${riskClass(a?.risk_level)}`;$('#action-risk').textContent=a?.risk_level||'—';$('#payload-json').value=pretty(samples[actionSel.value]||{});}
    agentSel.addEventListener('change',fill);actionSel.addEventListener('change',setAction);fill();
    $$('[data-open-agent]').forEach(b=>b.addEventListener('click',()=>{agentSel.value=b.dataset.openAgent;fill();$('#executor').scrollIntoView({behavior:'smooth'})}));
    $('#agent-form').addEventListener('submit',async e=>{e.preventDefault();const out=$('#agent-result');let payload;try{payload=JSON.parse($('#payload-json').value||'{}')}catch{return toast('Payload JSON inválido',false)}out.textContent='Ejecutando...';try{const r=await executeControlled(agentSel.value,actionSel.value,payload);out.textContent=pretty(r);toast(r.message||'Ejecutado',r.success)}catch(err){out.textContent=pretty(err.body||{error:err.message});toast(err.message,false)}});
    $('#agent-health').addEventListener('click',async()=>{try{$('#agent-result').textContent=pretty(await api(`/api/v1/agents/${agentSel.value}/health`))}catch(e){toast(e.message,false)}});
  }

  async function integrationsPage(){
    async function render(){const d=await api('/api/v1/integrations');const wrap=$('#integration-list');wrap.innerHTML=d.integrations.map(s=>`<div class="integration-row"><div class="integration-main"><div class="integration-logo">${esc(s.provider.slice(0,2).toUpperCase())}</div><div><div class="integration-name">${esc(s.provider.toUpperCase())}</div><div class="integration-detail">${esc(s.capabilities.join(' · '))}</div></div></div>${status(s.status==='CONNECTED',s.status)}<div class="row">${s.provider==='microsoft'?`<button class="btn btn--sm btn--primary" data-ms="connect">${s.authenticated?'RECONECTAR':'CONECTAR'}</button><button class="btn btn--sm btn--secondary" data-ms="test">PROBAR</button><button class="btn btn--sm btn--danger" data-ms="disconnect">DESCONECTAR</button>`:s.provider==='google'?`<button class="btn btn--sm btn--primary" data-google="connect">${s.authenticated?'RECONECTAR':'CONECTAR'}</button><button class="btn btn--sm btn--secondary" data-google="test">PROBAR</button><button class="btn btn--sm btn--danger" data-google="disconnect">DESCONECTAR</button>`:`<button class="btn btn--sm btn--primary" data-gh="connect">${s.authenticated?'RECONECTAR':'CONECTAR'}</button><button class="btn btn--sm btn--secondary" data-gh="test">PROBAR</button><button class="btn btn--sm btn--danger" data-gh="disconnect">DESCONECTAR</button>`}</div></div>`).join('');wire();}
    function show(v){$('#integration-result').textContent=typeof v==='string'?v:pretty(v)}
    async function verify(url){try{show(await api(url));toast('Integración verificada')}catch(e){show(e.body||e.message);toast(e.message,false)}}
    function wire(){
      $('[data-ms="connect"]')?.addEventListener('click',async()=>{try{const b=await api('/auth/microsoft/device-login',{method:'POST',body:'{}'});show(`Código: ${b.user_code}\nURL: ${b.verification_uri}\n\n${b.message}`);if(b.verification_uri)window.open(b.verification_uri,'_blank','noopener');const timer=setInterval(async()=>{try{const s=await api(`/auth/microsoft/device-login/status/${b.job_id}`);show(s);if(s.status!=='pending'){clearInterval(timer);render()}}catch{clearInterval(timer)}},2500)}catch(e){show(e.body||e.message);toast(e.message,false)}});
      $('[data-ms="test"]')?.addEventListener('click',()=>verify('/auth/microsoft/me'));$('[data-ms="disconnect"]')?.addEventListener('click',async()=>{try{show(await api('/auth/microsoft/disconnect',{method:'POST',body:'{}'}));render()}catch(e){toast(e.message,false)}});
      $('[data-google="connect"]')?.addEventListener('click',async()=>{try{const b=await api('/auth/google/login',{method:'POST',body:'{}'});show(b);window.open(b.authorization_url,'_blank','noopener')}catch(e){show(e.body||e.message);toast(e.message,false)}});
      $('[data-google="test"]')?.addEventListener('click',()=>verify('/auth/google/me'));$('[data-google="disconnect"]')?.addEventListener('click',async()=>{try{show(await api('/auth/google/disconnect',{method:'POST',body:'{}'}));render()}catch(e){toast(e.message,false)}});
      $('[data-gh="connect"]')?.addEventListener('click',async()=>{try{show(await api('/auth/github/connect',{method:'POST',body:'{}'}));render()}catch(e){show(e.body||e.message);toast(e.message,false)}});$('[data-gh="test"]')?.addEventListener('click',()=>verify('/auth/github/me'));$('[data-gh="disconnect"]')?.addEventListener('click',async()=>{try{show(await api('/auth/github/disconnect',{method:'POST',body:'{}'}));render()}catch(e){toast(e.message,false)}});
    }
    $('#integrations-refresh').addEventListener('click',render);await render();
  }

  async function tasksPage(){
    async function reload(){const [t,r]=await Promise.all([api('/api/v1/tasks'),api('/api/v1/reminders')]);$('#task-body').innerHTML=t.tasks.length?t.tasks.map(x=>`<tr><td>${x.id}</td><td>${esc(x.title)}</td><td>${esc(x.priority)}</td><td>${esc(x.assigned_to||'—')}</td><td>${esc(dt(x.due_at))}</td><td>${esc(x.status)}</td><td>${x.status==='pending'?`<button class="btn btn--sm btn--success" data-complete="${x.id}">COMPLETAR</button>`:'—'}</td></tr>`).join(''):'<tr><td colspan="7">Sin tareas.</td></tr>';$$('[data-complete]').forEach(b=>b.addEventListener('click',async()=>{try{await executeControlled('task','complete_task',{id:Number(b.dataset.complete)});toast('Tarea completada');reload()}catch(e){toast(e.message,false)}}));$('#reminder-body').innerHTML=r.reminders.length?r.reminders.map(x=>`<tr><td>${x.id}</td><td>${esc(x.text)}</td><td>${esc(x.priority)}</td><td>${esc(dt(x.run_at))}</td><td>${esc(x.status)}</td></tr>`).join(''):'<tr><td colspan="5">Sin recordatorios.</td></tr>'}
    $('#task-form').addEventListener('submit',async e=>{e.preventDefault();const raw=$('#task-due').value;const p={title:$('#task-title').value,priority:$('#task-priority').value,due_at:raw?new Date(raw).toISOString():null,assigned_to:$('#task-assigned').value||null,source:'ui'};try{await executeControlled('task','create_task',p);e.target.reset();toast('Tarea creada');reload()}catch(err){toast(err.message,false)}});
    $('#reminder-form').addEventListener('submit',async e=>{e.preventDefault();const p={text:$('#reminder-text').value,priority:$('#reminder-priority').value,run_at:new Date($('#reminder-at').value).toISOString()};try{await executeControlled('reminder','create_reminder',p);e.target.reset();toast('Recordatorio creado');reload()}catch(err){toast(err.message,false)}});$('#tasks-refresh').addEventListener('click',reload);await reload();
  }

  async function automationsPage(){
    const cat=(await api('/api/v1/agents')).agents.filter(a=>a.id!=='orchestrator');const sel=$('#auto-agent');sel.innerHTML=cat.map(a=>`<option value="${esc(a.id)}">${esc(a.display_name)}</option>`).join('');
    function actions(){const a=cat.find(x=>x.id===sel.value);$('#auto-action').innerHTML=(a?.actions||[]).filter(x=>['READ','PREPARE'].includes(x.risk_level)).map(x=>`<option value="${esc(x.name)}">${esc(x.name)} · ${esc(x.risk_level)}</option>`).join('');$('#auto-payload').value=pretty(samples[$('#auto-action').value]||{})}sel.addEventListener('change',actions);$('#auto-action').addEventListener('change',()=>$('#auto-payload').value=pretty(samples[$('#auto-action').value]||{}));actions();
    async function reload(){const d=await api('/api/v1/automations');$('#automation-body').innerHTML=d.automations.length?d.automations.map(x=>`<tr><td>${x.id}</td><td>${esc(x.name)}</td><td>${esc(x.agent)} / ${esc(x.action)}</td><td>${esc(x.schedule)}</td><td>${status(x.enabled,x.status)}</td><td>${esc(dt(x.last_run))}</td><td>${esc(dt(x.next_run))}</td><td><div class="row"><button class="btn btn--sm btn--secondary" data-toggle="${x.id}" data-enabled="${x.enabled}">${x.enabled?'PAUSAR':'ACTIVAR'}</button><button class="btn btn--sm btn--danger" data-delete="${x.id}">ELIMINAR</button></div></td></tr>`).join(''):'<tr><td colspan="8">Sin automatizaciones.</td></tr>';$$('[data-toggle]').forEach(b=>b.addEventListener('click',async()=>{try{await api(`/api/v1/automations/${b.dataset.toggle}`,{method:'PATCH',body:JSON.stringify({enabled:b.dataset.enabled!=='true'})});reload()}catch(e){toast(e.message,false)}}));$$('[data-delete]').forEach(b=>b.addEventListener('click',async()=>{if(!confirm('¿Eliminar automatización?'))return;try{await api(`/api/v1/automations/${b.dataset.delete}`,{method:'DELETE'});reload()}catch(e){toast(e.message,false)}}))}
    $('#automation-form').addEventListener('submit',async e=>{e.preventDefault();let parameters;try{parameters=JSON.parse($('#auto-payload').value||'{}')}catch{return toast('JSON inválido',false)}try{await api('/api/v1/automations',{method:'POST',body:JSON.stringify({name:$('#auto-name').value,agent:sel.value,action:$('#auto-action').value,parameters,schedule:$('#auto-schedule').value,enabled:true})});e.target.reset();$('#auto-schedule').value='interval:60';actions();toast('Automatización creada');reload()}catch(err){toast(err.message,false)}});await reload();
  }

  async function monitoringPage(){
    async function reload(){try{const [m,h,a]=await Promise.all([executeControlled('monitoring','system_health',{}),api('/api/v1/health'),api('/api/v1/agents')]);const d=m.data;$('#cpu-value').textContent=`${d.cpu_percent.toFixed(1)}%`;$('#memory-value').textContent=`${d.memory_percent.toFixed(1)}%`;$('#disk-value').textContent=`${d.disk_percent.toFixed(1)}%`;$('#process-value').textContent=d.process_count;$('#cpu-bar').style.width=`${Math.min(100,d.cpu_percent)}%`;$('#memory-bar').style.width=`${Math.min(100,d.memory_percent)}%`;$('#disk-bar').style.width=`${Math.min(100,d.disk_percent)}%`;$('#memory-detail').textContent=`Disponible ${bytes(d.memory_available)} de ${bytes(d.memory_total)}`;$('#disk-detail').textContent=`Libre ${bytes(d.disk_free)} de ${bytes(d.disk_total)}`;$('#boot-detail').textContent=`Inicio: ${dt(d.boot_time*1000)}`;$('#health-detail').innerHTML=Object.entries(h).filter(([k])=>k!=='agents').map(([k,v])=>`<div class="kv-row"><div class="kv-key">${esc(k)}</div><div class="kv-value">${esc(typeof v==='object'?pretty(v):v)}</div></div>`).join('');$('#health-agents').innerHTML=a.agents.map(x=>`<tr><td>${esc(x.display_name)}</td><td>${status(x.status==='ONLINE',x.health)}</td><td>${esc(x.integration||'core')}</td><td>${esc(dt(x.last_execution))}</td></tr>`).join('')}catch(e){toast(e.message,false)}}
    $('#health-refresh').addEventListener('click',reload);$('#tcp-form').addEventListener('submit',async e=>{e.preventDefault();try{$('#tcp-result').textContent=pretty(await executeControlled('monitoring','tcp_check',{host:$('#tcp-host').value,port:Number($('#tcp-port').value),timeout:3}))}catch(err){$('#tcp-result').textContent=pretty(err.body||{error:err.message})}});await reload();setInterval(reload,10000);
  }

  async function auditPage(){
    async function reload(){const q=new URLSearchParams();[['limit','#audit-limit'],['actor','#audit-actor'],['agent','#audit-agent'],['action','#audit-action'],['risk_level','#audit-risk'],['status','#audit-status'],['correlation_id','#audit-correlation']].forEach(([k,s])=>{const v=$(s).value;if(v)q.set(k,v)});if($('#audit-from').value)q.set('date_from',new Date($('#audit-from').value).toISOString());if($('#audit-to').value)q.set('date_to',new Date($('#audit-to').value).toISOString());const d=await api(`/api/v1/audit?${q}`);$('#audit-body').innerHTML=d.events.length?d.events.map(x=>`<tr data-audit-id="${esc(x.audit_id)}"><td>${esc(dt(x.timestamp))}</td><td>${esc(x.actor)}</td><td>${esc(x.agent)}</td><td>${esc(x.action)}</td><td><span class="status ${riskClass(x.risk_level)}">${esc(x.risk_level)}</span></td><td>${status(x.status==='SUCCESS',x.status)}</td><td>${x.duration_ms} ms</td><td class="code">${esc(x.correlation_id)}</td></tr>`).join(''):'<tr><td colspan="8">Sin eventos.</td></tr>';$$('[data-audit-id]').forEach(tr=>tr.addEventListener('click',async()=>{$('#audit-detail').textContent=pretty(await api(`/api/v1/audit/${tr.dataset.auditId}`))}))}
    $('#audit-refresh').addEventListener('click',reload);$('#audit-clear').addEventListener('click',()=>{$$('#audit-from,#audit-to,#audit-actor,#audit-agent,#audit-action,#audit-risk,#audit-status,#audit-correlation').forEach(x=>x.value='');reload()});await reload();
  }

  async function settingsPage(){const d=await api('/api/ui/settings');$('#settings-list').innerHTML=Object.entries(d).map(([k,v])=>`<div class="kv-row"><div class="kv-key">${esc(k)}</div><div class="kv-value code">${esc(typeof v==='object'?pretty(v):v)}</div></div>`).join('')}

  const page=document.body.dataset.page;const runners={dashboard,agents:agentsPage,integrations:integrationsPage,tasks:tasksPage,automations:automationsPage,monitoring:monitoringPage,audit:auditPage,settings:settingsPage};
  Promise.resolve(runners[page]?.()).catch(e=>{console.error(e);toast(e.message||String(e),false);$('#api-status')?.classList.replace('status--online','status--offline')});
})();
