function renderAsk(){
 const root=document.querySelector('#ask');if(root.dataset.ready)return;root.dataset.ready='true';
 root.innerHTML='<p>Ask a small offline model about your PDFs and Wikipedia. Answers include source passages. Gutenberg and private files are not included.</p><form id="ask-form"><label for="ask-scope">Search in</label> <select id="ask-scope"><option value="all">PDFs + Wikipedia</option><option value="pdf">PDFs only</option><option value="wikipedia">Wikipedia only</option></select><br><label for="ask-question">Your question</label><textarea id="ask-question" required minlength="3" maxlength="600" rows="3" placeholder="For example: How can I collect rainwater?"></textarea><button class="action" id="ask-submit">Ask the library</button></form><p id="ask-status" role="status">Checking local model…</p><div id="ask-answer" aria-live="polite"></div><div id="ask-sources"></div><section class="ask-performance" aria-label="Local model and performance"><p id="ask-model">Local model: checking…</p><p id="ask-stats">Performance will appear after an answer.</p><small>Generation speed excludes model loading and reading the prompt. Total time includes retrieval, loading and inference.</small></section>';
 fetch('/api/ask').then(r=>r.json()).then(s=>{document.querySelector('#ask-model').textContent='Model: '+s.model+' · '+s.runtime;document.querySelector('#ask-status').textContent=s.ready?'Local model ready · loads only while answering.':'Model not installed · matching passages are still available.'}).catch(()=>{document.querySelector('#ask-status').textContent='Unable to check the local model.'});
 document.querySelector('#ask-form').onsubmit=async e=>{
  e.preventDefault();const button=document.querySelector('#ask-submit'),status=document.querySelector('#ask-status'),answer=document.querySelector('#ask-answer'),sources=document.querySelector('#ask-sources');
  button.disabled=true;status.textContent='Finding passages and preparing an answer… This may take a minute.';answer.replaceChildren();sources.replaceChildren();
  try{
   const response=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json','X-Fieldstation':'ask'},body:JSON.stringify({question:document.querySelector('#ask-question').value,scope:document.querySelector('#ask-scope').value})});const result=await response.json();if(!response.ok)throw Error(result.error||'Unable to answer.');
   answer.textContent=result.answer;
   const stats=result.stats;
   const fmt=(value,digits=1)=>Number.isFinite(value)?value.toFixed(digits):'unavailable';
   document.querySelector('#ask-stats').textContent=stats?`Last answer: ${fmt(stats.tokensPerSecond)} tokens/s · ${fmt(stats.outputTokens,0)} output tokens · ${fmt(stats.inputTokens,0)} input tokens · ${fmt(stats.generationSeconds)} s generating · ${fmt(stats.totalSeconds)} s total`:'No model generation for this question.';
   if(stats)document.querySelector('#ask-model').textContent='Model: '+stats.model+' · llama.cpp · CPU · 4 threads';
   status.textContent=result.generated?'AI summary · check the source passages; a small model can make mistakes. Model unloaded.':'Source search · no AI answer generated.';
   status.textContent+=' '+(result.sourceStatus||'');
   if(result.sources.length)sources.innerHTML='<h2>Source passages</h2>'+result.sources.map(s=>`<article class="ask-source"><a href="${esc(s.kind==='wikipedia'?'http://'+location.hostname+':8766'+s.url:s.url)}" target="_blank" rel="noopener">[${s.number}] ${esc(s.title)} · ${esc(s.label||'PDF page '+s.page)} ↗</a><p>${esc(s.excerpt)}</p></article>`).join('');
   sources.querySelectorAll('a').forEach((link,n)=>{const source=result.sources[n];if(source.kind==='wikipedia')link.onclick=e=>{const item=data.items.find(i=>i.name===source.archive+'.zim');if(item){e.preventDefault();openKiwix(item,source.articlePath)}}});
  }catch(error){status.textContent=error.message}finally{button.disabled=false}
 };
}
