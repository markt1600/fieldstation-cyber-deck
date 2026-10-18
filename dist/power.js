(()=>{
 let busy=false;
 function confirmPower(action){
  if(busy)return;
  const reboot=action==='reboot',label=reboot?'Reboot':'Shut down';
  const d=document.createElement('dialog');d.className='power-dialog';
  d.innerHTML='<h2>'+label+' Fieldstation?</h2><p>'+(reboot?'Playback and transfers will stop. Fieldstation will restart.':'Playback and transfers will stop. Wait for the Pi to shut down before disconnecting power.')+'</p><p role="status" class="power-message"></p><div class="eq-actions"><button class="action secondary" data-cancel>Cancel</button><button class="action" data-confirm>'+label+'</button></div>';
  d.querySelector('[data-cancel]').onclick=()=>d.close();d.onclose=()=>d.remove();
  d.querySelector('[data-confirm]').onclick=async()=>{
   busy=true;d.querySelectorAll('button').forEach(b=>b.disabled=true);
   const message=d.querySelector('.power-message');message.textContent='Requesting '+label.toLowerCase()+'…';
   try{const r=await fetch('/api/power',{method:'POST',headers:{'Content-Type':'application/json','X-Fieldstation':'power'},body:JSON.stringify({action})});const result=await r.json();if(!r.ok)throw Error(result.error||'Power action failed.');message.textContent=reboot?'Rebooting… Fieldstation will return after startup.':'Shutting down…';}
   catch(e){busy=false;message.textContent=e.message;d.querySelectorAll('button').forEach(b=>b.disabled=false);}
  };
  document.body.append(d);d.showModal();d.querySelector('[data-cancel]').focus();
 }
 document.querySelector('#power-reboot').onclick=()=>confirmPower('reboot');
 document.querySelector('#power-shutdown').onclick=()=>confirmPower('shutdown');
})();
