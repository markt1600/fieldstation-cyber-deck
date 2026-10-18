let artState={q:'',topic:'',artist:'',museum:'',sort:'highlights',page:0,seed:Date.now()},artRequest=0,artLoaded=false;
function renderArt(){if(artLoaded){refreshArtStatus();return;}artLoaded=true;const root=$('#art');root.innerHTML=`<div class="art-lead"><button class="action" id="art-exhibition-start">▶ Exhibition</button><p id="art-progress" class="meta" role="status"></p><button class="action secondary" id="art-refresh">Refresh</button><button class="action" id="art-surprise">Shuffle</button></div><div class="art-topics" id="art-topics"></div><form id="art-form" class="tools"><label class="search"><input type="search" id="art-query" aria-label="Search art" placeholder="Search an artist, artwork or subject"></label><button class="action">Search</button><button type="button" class="action secondary" id="art-reset">Reset</button></form><details class="art-filters"><summary>Choose artist, museum & sort order</summary><div class="tools"><label>Artist <select id="art-artist"></select></label><label>Museum <select id="art-museum"></select></label><label>Order <select id="art-sort"><option value="highlights">Museum highlights first</option><option value="shuffle">Shuffle</option><option value="artist">Artist A–Z</option><option value="oldest">Oldest first</option></select></label></div></details><div id="art-summary" class="section-label" aria-live="polite"></div><div id="art-grid" class="art-grid"></div><div id="art-paging" class="tools"></div>`;
 $('#art-exhibition-start').onclick=startExhibition;
 $('#art-refresh').onclick=()=>loadArt();
 $('#art-form').onsubmit=e=>{e.preventDefault();artState.q=$('#art-query').value;artState.page=0;loadArt()};
 $('#art-reset').onclick=()=>{artState={q:'',topic:'',artist:'',museum:'',sort:'highlights',page:0,seed:Date.now()};$('#art-query').value='';loadArt()};
 $('#art-surprise').onclick=()=>{artState.sort='shuffle';artState.seed=Date.now();artState.page=0;loadArt()};
 for(const key of ['artist','museum','sort'])$('#art-'+key).onchange=e=>{artState[key]=e.target.value;artState.page=0;loadArt()};loadArt();
}
async function loadArt(){const request=++artRequest;$('#art-summary').textContent='Opening the gallery…';try{
 const r=await fetch('/api/art?'+new URLSearchParams(artState));if(!r.ok)throw Error('Art gallery is unavailable.');const d=await r.json();if(request!==artRequest)return;
 $('#art-progress').textContent=d.status.state==='Complete'?`${d.available.toLocaleString()} works saved for offline viewing · Public-domain museum images`:`${d.available.toLocaleString()} of ${d.status.target.toLocaleString()} works ready offline · ${d.status.state}. The collection grows as images arrive.`;
 $('#art-topics').innerHTML='<button class="art-topic '+(!artState.topic?'selected':'')+'" data-topic=""><span>All art</span><small>'+d.available+' works</small></button>'+d.topics.map(t=>`<button class="art-topic ${t.name===artState.topic?'selected':''}" data-topic="${esc(t.name)}"><img src="${t.cover}" alt="" loading="lazy"><span>${esc(t.name)}</span><small>${t.count} works</small></button>`).join('');
 $('#art-topics').querySelectorAll('[data-topic]').forEach(b=>b.onclick=()=>{artState.topic=b.dataset.topic;artState.page=0;loadArt()});
 $('#art-artist').innerHTML='<option value="">All artists</option>'+d.artists.map(a=>`<option value="${esc(a.name)}">${esc(a.name)} (${a.count})</option>`).join('');$('#art-artist').value=artState.artist;
 $('#art-museum').innerHTML='<option value="">All museums</option>'+d.museums.map(m=>`<option>${esc(m)}</option>`).join('');$('#art-museum').value=artState.museum;$('#art-sort').value=artState.sort;
 $('#art-summary').textContent=`${artState.topic||'The collection'} · ${d.total.toLocaleString()} works${d.total?' · Page '+(d.page+1)+' of '+Math.ceil(d.total/36):''}`;
 $('#art-grid').innerHTML=d.items.map((w,n)=>`<button class="art-card" data-art="${n}"><div class="art-picture"><img src="${w.thumbnail}" alt="${esc(w.title)}" loading="lazy"></div><div class="art-caption">${w.highlight?'<span class="eyebrow">Museum highlight</span>':''}<strong>${esc(w.title)}</strong><span>${esc(w.artist)}</span><small>${esc(w.date)} · ${esc(w.type)}</small></div></button>`).join('')||'<p>No matching works. Try another subject or clear the filters.</p>';
 $('#art-grid').querySelectorAll('[data-art]').forEach(b=>b.onclick=()=>openArtwork(d.items,Number(b.dataset.art)));
 $('#art-paging').innerHTML=`<button class="action" id="art-prev" ${!d.page?'disabled':''}>← Previous page</button><button class="action" id="art-next" ${(d.page+1)*36>=d.total?'disabled':''}>Next page →</button>`;
 for(const [id,step] of [['art-prev',-1],['art-next',1]])$('#'+id).onclick=()=>{artState.page+=step;loadArt();$('#art-form').scrollIntoView({block:'start'})};
 }catch(e){if(request===artRequest)$('#art-summary').textContent=e.message;}
}
function openArtwork(works,n){const w=works[n];prepareViewer(w.title);const body=$('#viewer-body');body.innerHTML=`<div class="art-view-controls"><button class="action secondary" id="art-back" ${n===0?'disabled':''}>← Previous work</button><button class="action secondary" id="art-forward" ${n===works.length-1?'disabled':''}>Next work →</button></div><div class="art-detail"><figure><img src="${w.image}" alt="${esc(w.title)}"><figcaption>${esc(w.title)} · ${esc(w.date)}</figcaption></figure><section><span class="eyebrow">${esc(w.museum)}</span><h2>${esc(w.title)}</h2><h3>${esc(w.artist)}</h3><p>${esc(w.artist_info)}</p>${w.biography?'<details><summary>About the artist</summary><p>'+esc(w.biography)+'</p></details>':''}<dl><dt>Date</dt><dd>${esc(w.date||'Not recorded')}</dd><dt>Medium</dt><dd>${esc(w.medium||w.type)}</dd><dt>Origin</dt><dd>${esc(w.culture||'Not recorded')}</dd><dt>Dimensions</dt><dd>${esc(w.dimensions||'Not recorded')}</dd></dl><h3>About this work</h3><p class="art-description">${esc(w.description||'The museum has not supplied an extended description for this work. The catalogue details above are available offline.')}</p>${w.fact?'<h3>Look closer</h3><p>'+esc(w.fact)+'</p>':''}<p class="meta">${esc(w.credit)}</p><p class="meta">${esc(w.license)}</p><a href="${esc(w.source)}" target="_blank" rel="noopener" class="action secondary">Museum record ↗ (online)</a></section></div>`;
 $('#art-back').onclick=()=>openArtwork(works,n-1);$('#art-forward').onclick=()=>openArtwork(works,n+1);
}

async function refreshArtStatus(){try{const d=await(await fetch('/api/art-status')).json();if(view==='art'&&$('#art-progress'))$('#art-progress').textContent=d.state==='Complete'?`${d.downloaded.toLocaleString()} works saved for offline viewing · Public-domain museum images`:`${d.downloaded.toLocaleString()} of ${d.target.toLocaleString()} works ready offline · ${d.state}. Use Refresh collection to see new arrivals.`;}catch{}}

let exhibitionRun=0,exhibitionTimer=null;
async function startExhibition(){
 const run=++exhibitionRun,seed=Date.now();let page=0,queue=[],shown=0,total=0,loading=false;
 const panel=document.createElement('dialog');panel.id='art-exhibition';panel.setAttribute('aria-label','Art exhibition');
 panel.innerHTML='<img alt=""><p role="status">Opening exhibition…</p><button class="action" aria-label="Exit exhibition">Exit ✕</button>';
 document.body.append(panel);panel.showModal();
 const leave=()=>{if(run!==exhibitionRun)return;++exhibitionRun;clearTimeout(exhibitionTimer);document.removeEventListener('fullscreenchange',fullscreenChanged);if(document.fullscreenElement===panel)document.exitFullscreen().catch(()=>{});panel.remove();$('#art-exhibition-start')?.focus();};
 const fullscreenChanged=()=>{if(!document.fullscreenElement)leave();};
 const artwork=panel.querySelector('img');artwork.style.cursor='pointer';artwork.setAttribute('aria-label','Next artwork');artwork.setAttribute('role','button');artwork.tabIndex=0;artwork.onclick=()=>next();artwork.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();next();}};
 panel.querySelector('button').onclick=leave;panel.addEventListener('cancel',e=>{e.preventDefault();leave();});
 if(panel.requestFullscreen)panel.requestFullscreen().then(()=>document.addEventListener('fullscreenchange',fullscreenChanged)).catch(()=>{});
 async function next(){
  if(run!==exhibitionRun||loading)return;
  clearTimeout(exhibitionTimer);loading=true;
  try{
   if(!queue.length){
    const response=await fetch('/api/art?'+new URLSearchParams({sort:'shuffle',seed,page}),{signal:AbortSignal.timeout(15000)});
    if(!response.ok)throw Error('Gallery unavailable');const d=await response.json();if(run!==exhibitionRun)return;
    queue=d.items;total=d.total;page++;if(!queue.length){panel.querySelector('p').textContent='No artwork available. Exit and try again.';return;}
   }
   const work=queue.shift(),image=new Image();image.src=work.image;await image.decode();if(run!==exhibitionRun)return;
   const visible=panel.querySelector('img');visible.src=image.src;visible.alt=work.title+' — '+work.artist;panel.querySelector('p').textContent=work.title+' · '+work.artist+(work.date?' · '+work.date:'');
   if(++shown>=total){page=0;shown=0;queue=[];}
   exhibitionTimer=setTimeout(next,30000);
  }catch{if(run===exhibitionRun){panel.querySelector('p').textContent='Skipping unavailable artwork…';exhibitionTimer=setTimeout(next,3000);}}finally{loading=false;}
 }
 next();
}
