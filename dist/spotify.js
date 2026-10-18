let spotifyLoaded=false, eqSaving=false;
function renderSpotify(){
 const root=document.querySelector('#spotify');
 if(spotifyLoaded){refreshSpotifyStatus();return;}
 spotifyLoaded=true;
 root.innerHTML=`<div class="spotify-card"><div class="spotify-title"><h2>Spotify Connect</h2><span id="spotify-state" role="status">Checking…</span></div><p>Open Spotify on your phone, tap the device picker and choose <strong>Fieldstation</strong>. Connect both devices to the same Wi-Fi. Internet and Spotify Premium are required.</p><p class="spotify-hint">Use your phone to choose music and control playback. For the full volume range, raise Spotify’s volume and use the physical knob to set your listening level.</p></div>
 <form id="eq-form" class="spotify-card"><div class="spotify-title"><h2>Speaker EQ</h2><span id="eq-state" role="status"></span></div>
 <label for="eq-bass">Bass boost <output id="eq-bass-value">+6 dB</output></label><input id="eq-bass" type="range" min="0" max="12" step="0.5" value="6">
 <label for="eq-frequency">Bass centre <output id="eq-frequency-value">120 Hz</output></label><input id="eq-frequency" type="range" min="90" max="180" step="5" value="120">
 <label for="eq-mode">Boost behaviour</label><select id="eq-mode"><option value="always">Always on</option><option value="adaptive">Reduce as volume rises</option></select>
 <p class="spotify-hint">Applies to Spotify and local music. Adaptive mode follows the physical/master volume: full boost below 20%, fading to zero at 80%. Headroom and a −1 dB limiter remain active; more boost can reduce overall loudness. Deep bass below 70 Hz is rolled off. Boost above +6 dB is for enclosure testing: reduce it if the speakers distort or rattle.</p>
 <div class="eq-actions"><button class="action" type="submit">Apply EQ</button><button class="action" type="button" id="eq-reset">Reset to +6 dB / 120 Hz</button></div><p id="eq-message" role="status" aria-live="polite"></p></form>`;
 const labels=()=>{document.querySelector('#eq-bass-value').textContent='+'+document.querySelector('#eq-bass').value+' dB';document.querySelector('#eq-frequency-value').textContent=document.querySelector('#eq-frequency').value+' Hz';};
 root.querySelectorAll('input').forEach(i=>i.addEventListener('input',labels));
 root.querySelector('#eq-form').onsubmit=async e=>{e.preventDefault();await saveEQ();};
 root.querySelector('#eq-reset').onclick=async()=>{setEQ({bass_db:6,frequency_hz:120,mode:'always'});await saveEQ();};
 refreshSpotifyStatus(true);
}
function setEQ(s){document.querySelector('#eq-bass').value=s.bass_db;document.querySelector('#eq-frequency').value=s.frequency_hz;document.querySelector('#eq-mode').value=s.mode;document.querySelector('#eq-bass-value').textContent='+'+s.bass_db+' dB';document.querySelector('#eq-frequency-value').textContent=s.frequency_hz+' Hz';}
function showAudioStatus(d){document.querySelector('#spotify-state').textContent=d.services.spotify?'Ready · Fieldstation':'Spotify unavailable';document.querySelector('#eq-state').textContent=d.services['audio-dsp']&&d.services.loudness?'EQ active':'EQ unavailable';}
async function refreshSpotifyStatus(load=false){
 if(!spotifyLoaded||document.querySelector('#spotify').hidden)return;
 try{const r=await fetch('/api/audio-settings',{signal:AbortSignal.timeout(5000)});if(!r.ok)throw Error();const d=await r.json();showAudioStatus(d);if(load)setEQ(d.settings);}
 catch{document.querySelector('#spotify-state').textContent='Status unavailable';document.querySelector('#eq-state').textContent='Status unavailable';}
}
async function saveEQ(){
 if(eqSaving)return;eqSaving=true;
 const form=document.querySelector('#eq-form'),msg=document.querySelector('#eq-message');
 form.querySelectorAll('button').forEach(b=>b.disabled=true);msg.textContent='Applying…';
 try{const r=await fetch('/api/audio-settings',{method:'POST',headers:{'Content-Type':'application/json','X-Fieldstation':'audio'},body:JSON.stringify({bass_db:Number(document.querySelector('#eq-bass').value),frequency_hz:Number(document.querySelector('#eq-frequency').value),mode:document.querySelector('#eq-mode').value}),signal:AbortSignal.timeout(7000)});const d=await r.json();if(!r.ok)throw Error(d.error||'Unable to save EQ');showAudioStatus(d);msg.textContent=d.services.loudness&&d.services['audio-dsp']?'Saved. EQ transitions smoothly to these settings.':'Saved, but the audio service is unavailable.';}
 catch(e){msg.textContent=e.message||'Unable to save EQ. Try again.';}
 finally{eqSaving=false;form.querySelectorAll('button').forEach(b=>b.disabled=false);}
}
setInterval(()=>refreshSpotifyStatus(),5000);
