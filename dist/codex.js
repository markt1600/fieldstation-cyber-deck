let codexPageReady=false;
function renderCodex(){
 const root=document.querySelector('#codex');if(codexPageReady)return;codexPageReady=true;
 root.innerHTML=`<div class="spotify-card"><div class="eq-actions"><h2>Codex</h2><button class="action" id="codex-max">Maximize</button></div><p>Online assistant on this Pi. Click Start Codex below, then sign in with ChatGPT when prompted. Use your keyboard to chat and approve actions. Your session stays open while browsing Fieldstation; refreshing the page ends it.</p></div><iframe id="codex-frame" title="Codex terminal" src="http://127.0.0.1:8767/" style="width:100%;height:65vh;min-height:320px;border:0;border-radius:10px"></iframe>`;
 root.querySelector('#codex-max').onclick=()=>{const full=root.dataset.full!=='true';root.dataset.full=String(full);root.style.cssText=full?'position:fixed;inset:0;z-index:1000;background:#101518;padding:12px;display:flex;flex-direction:column':'';root.querySelector('#codex-frame').style.height=full?'100%':'65vh';root.querySelector('#codex-max').textContent=full?'Restore':'Maximize';};
}
