(()=>{
 const $=s=>document.querySelector(s),dialog=$('#wifi-dialog');let state=null,busy=false;
 async function api(payload,scan=false){const r=await fetch('/api/wifi'+(scan?'?scan=1':''),{method:payload?'POST':'GET',headers:{'X-Fieldstation':'wifi',...(payload?{'Content-Type':'application/json'}:{})},body:payload?JSON.stringify(payload):undefined});const data=await r.json();if(!r.ok)throw Error(data.error);return data;}
 async function refresh(scan=false){try{state=await api(null,scan);$('#wifi-status').textContent=state.ssid?'Wi-Fi: '+state.ssid:state.state==='off'?'Wi-Fi off':state.supported?'Wi-Fi: '+state.state:'Wi-Fi settings';$('#wifi-status').title=state.ssid||state.state;if(dialog.open&&!busy)render();}catch(e){$('#wifi-status').textContent='Wi-Fi unavailable';if(dialog.open)$('#wifi-message').textContent=e.message;}}
 async function action(payload){busy=true;$('#wifi-message').textContent='Applying Wi-Fi change…';$('#wifi-controls').querySelectorAll('button,input,select').forEach(e=>e.disabled=true);try{const r=await api(payload);$('#wifi-message').textContent=r.message;}catch(e){$('#wifi-message').textContent=e.message;}finally{if(payload.password)payload.password='';busy=false;await refresh();}}
 function render(){const root=$('#wifi-controls');root.replaceChildren();if(!state)return;
  const note=document.createElement('p');note.className='dialog-note';note.textContent=state.supported?'Changing networks or switching Wi-Fi off can interrupt downloads. Your offline library will still work.':state.message;root.append(note);if(!state.supported)return;
  const bar=document.createElement('div');bar.className='wifi-toolbar';
  const radio=document.createElement('button');radio.className='wifi-toggle';radio.type='button';radio.setAttribute('role','switch');radio.setAttribute('aria-checked',String(state.enabled));radio.setAttribute('aria-label','Wi-Fi');radio.textContent=state.enabled?'Wi-Fi ON':'Wi-Fi OFF';radio.onclick=()=>action({action:'radio',enabled:!state.enabled});bar.append(radio);
  if(!state.enabled){root.append(bar);const off=document.createElement('p');off.textContent='Wi-Fi is off. Turn it on to find nearby networks.';root.append(off);return;}
  const scan=document.createElement('button');scan.className='action secondary';scan.textContent='Scan again';scan.onclick=async()=>{scan.disabled=true;$('#wifi-message').textContent='Scanning nearby networks…';await refresh(true);$('#wifi-message').textContent='';};bar.append(scan);root.append(bar);
  const list=document.createElement('div');list.className='wifi-networks';list.setAttribute('aria-label','Available Wi-Fi networks');const seen=new Set();
  for(const ap of [...state.networks].sort((a,b)=>Number(b.active)-Number(a.active)||b.signal-a.signal)){
   if(seen.has(ap.ssid))continue;seen.add(ap.ssid);
   const row=document.createElement('button');row.type='button';row.className='wifi-network';row.disabled=ap.active;
   const name=document.createElement('strong');name.textContent=ap.ssid;
   const detail=document.createElement('span');detail.textContent=(ap.active?'Connected · ':'')+ap.signal+'% signal · '+(ap.security||'Open');row.append(name,detail);
   row.onclick=()=>{
    root.querySelector('.wifi-connect-form')?.remove();
    const form=document.createElement('form');form.className='wifi-connect-form';const heading=document.createElement('strong');heading.textContent='Connect to '+ap.ssid;form.append(heading);
    const password=document.createElement('input');password.type='password';password.autocomplete='new-password';password.placeholder='Network password';password.setAttribute('aria-label','Password for '+ap.ssid);password.required=ap.security.includes('WPA');if(password.required)form.append(password);
    const submit=document.createElement('button');submit.className='action';submit.textContent='Connect';form.append(submit);form.onsubmit=e=>{e.preventDefault();const value=password.value;password.value='';action({action:'connect',bssid:ap.bssid,password:value});};row.after(form);password.required?password.focus():submit.focus();
   };list.append(row);
  }
  if(!seen.size){const empty=document.createElement('p');empty.textContent='No networks found. Try scanning again.';list.append(empty);}root.append(list);

 }
 $('#wifi-status').onclick=()=>{dialog.showModal();$('#wifi-message').textContent='Scanning nearby networks…';if(state)render();refresh(true).then(()=>{if(state)$('#wifi-message').textContent='';});};$('#wifi-close').onclick=()=>dialog.close();dialog.addEventListener('close',()=>$('#wifi-controls').replaceChildren());refresh();setInterval(()=>{if(!dialog.open&&!busy)refresh();},30000);
})();
