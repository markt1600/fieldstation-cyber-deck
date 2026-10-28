document.querySelectorAll('[data-game]').forEach(button=>button.onclick=async()=>{
 const buttons=document.querySelectorAll('[data-game]'),status=document.querySelector('#status');
 buttons.forEach(b=>b.disabled=true);status.textContent='Opening game on the Pi…';
 try{const response=await fetch('/api/games/launch',{method:'POST',headers:{'Content-Type':'application/json','X-Fieldstation':'games'},body:JSON.stringify({game:button.dataset.game})});const result=await response.json();if(!response.ok)throw Error(result.error||'Unable to launch game.');status.textContent=result.title+' is open on the Pi. Close its window to return.';}
 catch(error){status.textContent=error.message;}finally{buttons.forEach(b=>b.disabled=false);}
});