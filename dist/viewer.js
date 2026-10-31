// Shared in-app reader. Explicit VLC fallback for unsupported video codecs.
function prepareViewer(title){
 const dialog=document.querySelector('#viewer'),body=document.querySelector('#viewer-body');
 body.querySelectorAll('audio,video').forEach(p=>p.pause());
 body.replaceChildren();document.querySelector('#viewer-title').textContent=title;
 if(!dialog.open)dialog.showModal();
 return body;
}
function openDocument(item){
 const body=prepareViewer(item.title||'Reader');
 const frame=document.createElement('iframe');frame.title=item.title||'Document';frame.className='document-frame';
 if(item.format==='HTML')frame.setAttribute('sandbox','allow-scripts allow-forms allow-downloads');
 frame.src=item.url;body.append(frame);
}
function openInlineVideo(item){
 const body=prepareViewer(item.title),player=document.createElement('video');
 player.controls=true;player.playsInline=true;player.preload='metadata';player.src=item.url;
 const note=document.createElement('p');note.className='dialog-note';note.setAttribute('role','status');
 note.textContent='Use Maximize for a larger player. If this file has no picture or sound, try VLC.';
 const fallback=document.createElement('button');fallback.className='action';fallback.textContent='Open in VLC';
 fallback.onclick=()=>{player.pause();launchVideoExternal(item);};
 player.onerror=()=>{note.textContent='This browser cannot play this file. Open it in VLC to use additional format support.';};
 body.append(player,note,fallback);
 player.play().catch(()=>{if(!player.error)note.textContent='Press Play to start the video.';});
}
document.addEventListener('click',e=>{
 const a=e.target.closest('a[href]');if(!a||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey||a.hasAttribute('download'))return;
 const u=new URL(a.href,location.href);
 const known=data.items.find(i=>new URL(i.url,location.href).pathname===u.pathname);
 if(known&&known.format!=='PDF')return;
 if(u.origin===location.origin&&u.pathname.startsWith('/content/')&&a.closest('#catalogue,#results,#ask-sources,#viewer-body')){
  e.preventDefault();
  const row=a.closest('.search-book,.topic-book,.ask-source');
  openDocument({title:row?.querySelector('h3,summary')?.textContent||a.textContent.trim()||'PDF reader',url:u.href,format:'PDF'});
 }
});
const maximizeViewer=document.createElement('button');maximizeViewer.id='viewer-maximize';maximizeViewer.className='action';maximizeViewer.textContent='Maximize';maximizeViewer.setAttribute('aria-pressed','false');
document.querySelector('#close').before(maximizeViewer);
document.querySelector('#close').textContent='Back';document.querySelector('#close').setAttribute('aria-label','Back to Fieldstation');
maximizeViewer.onclick=()=>{const active=document.querySelector('#viewer').classList.toggle('viewer-maximized');maximizeViewer.textContent=active?'Restore':'Maximize';maximizeViewer.setAttribute('aria-pressed',String(active));};
document.querySelector('#viewer').addEventListener('close',()=>{document.querySelector('#viewer').classList.remove('viewer-maximized');maximizeViewer.textContent='Maximize';maximizeViewer.setAttribute('aria-pressed','false');});

let bookReaderVersion=0;
async function openBookReader(book){
 const version=++bookReaderVersion,body=prepareViewer(book.title);body.innerHTML='<p role="status">Opening book…</p>';
 const original=()=>readDiscovery('gutenberg_en_all_2025-11',{title:book.title,path:encodeURIComponent(book.title.replace('/','-').substring(0,230)+'.'+book.id)});
 try{
  const r=await fetch('/api/gutenberg-book?id='+encodeURIComponent(book.id));if(!r.ok)throw Error('This book could not be opened in the adjustable reader.');const result=await r.json();if(version!==bookReaderVersion||!$('#viewer').open)return;
  let saved={};try{saved=JSON.parse(localStorage.getItem('book-reader-'+book.id)||'{}')}catch{}
  let font=Math.max(14,Math.min(32,Number(saved.font)||20));
  body.innerHTML='<div class="book-controls"><button class="action" id="book-prev">← Previous</button><button class="action" id="book-next">Next →</button><label>Text size <select id="book-font">'+[14,16,18,20,22,24,28,32].map(n=>'<option value="'+n+'" '+(n===font?'selected':'')+'>'+n+' px</option>').join('')+'</select></label><button class="action secondary" id="book-save">Save bookmark</button><button class="action secondary" id="book-resume">Go to bookmark</button><button class="action secondary" id="book-original">Original layout</button></div><p id="book-position" role="status"></p><iframe id="book-frame" title="Book text"></iframe>';
  const frame=$('#book-frame');frame.setAttribute('sandbox','allow-same-origin');
  const doc=new DOMParser().parseFromString(result.html,'text/html');
  doc.querySelectorAll('script,iframe,object,embed,form,input,button,meta,base,link').forEach(n=>n.remove());
  const rootURL=archiveURL('gutenberg_en_all_2025-11',result.path);
  doc.querySelectorAll('*').forEach(n=>{for(const a of [...n.attributes])if(a.name.startsWith('on')||['srcdoc','srcset'].includes(a.name))n.removeAttribute(a.name);if(n.hasAttribute('src')){const u=new URL(n.getAttribute('src'),rootURL);if(u.origin===new URL(rootURL).origin)n.setAttribute('src',u.href);else n.removeAttribute('src');}if(n.tagName==='A'&&n.hasAttribute('href')&&!n.getAttribute('href').startsWith('#'))n.removeAttribute('href');});
  const csp=doc.createElement('meta');csp.httpEquiv='Content-Security-Policy';csp.content="default-src 'none'; img-src http://"+location.hostname+":8766 data:; style-src 'unsafe-inline';";doc.head.prepend(csp);
  const style=doc.createElement('style');style.id='reader-style';style.textContent='html{background:#f5f0e6;color:#252722;scroll-behavior:auto}body{box-sizing:border-box;max-width:72ch;margin:0 auto!important;padding:20px 28px!important;font-family:Georgia,serif!important;line-height:1.65!important;font-size:'+font+'px!important}p,li{font-size:1em!important}img,svg{max-width:100%;height:auto}pre{white-space:pre-wrap}a{color:#264e73}';doc.head.append(style);
  function progress(){const d=frame.contentDocument?.documentElement;return d?d.scrollTop/Math.max(1,d.scrollHeight-d.clientHeight):0}
  function jump(p){const d=frame.contentDocument.documentElement;frame.contentWindow.scrollTo(0,Math.max(0,Math.min(1,p))*(d.scrollHeight-d.clientHeight));update()}
  function update(){const d=frame.contentDocument?.documentElement;if(!d)return;$('#book-position').textContent=Math.round(progress()*100)+'% through book · pages adapt to your screen and text size';$('#book-prev').disabled=d.scrollTop<1;$('#book-next').disabled=d.scrollTop+d.clientHeight>=d.scrollHeight-2;}
  frame.onload=()=>{frame.contentWindow.addEventListener('scroll',update,{passive:true});jump(saved.position||0);};frame.srcdoc='<!doctype html>'+doc.documentElement.outerHTML;
  const turn=delta=>{frame.contentWindow.scrollBy(0,delta*Math.max(100,frame.clientHeight-40));update()};$('#book-prev').onclick=()=>turn(-1);$('#book-next').onclick=()=>turn(1);
  $('#book-font').onchange=e=>{const p=progress();font=Number(e.target.value);frame.contentDocument.body.style.setProperty('font-size',font+'px','important');jump(p);};
  $('#book-save').onclick=()=>{try{saved={position:progress(),font};localStorage.setItem('book-reader-'+book.id,JSON.stringify(saved));$('#book-position').textContent='Bookmark saved on this browser · '+Math.round(saved.position*100)+'%';$('#book-resume').disabled=false;}catch{$('#book-position').textContent='This browser could not save the bookmark.';}};
  $('#book-resume').disabled=saved.position===undefined;$('#book-resume').onclick=()=>jump(saved.position||0);$('#book-original').onclick=()=>{$('#viewer').close();original();};
 }catch(e){if(version!==bookReaderVersion||!$('#viewer').open)return;body.innerHTML='<p>'+esc(e.message)+'</p><button class="action" id="book-fallback">Open original book</button>';$('#book-fallback').onclick=()=>{$('#viewer').close();original()};}
}

const fieldstationSites={tools:{title:'Offline tools',url:'/tools.html',offline:true},kolibri:{title:'Khan Academy · Offline learning',url:'/learning.html',offline:true},games:{title:'Games',url:'/games.html',offline:true},maps:{title:'Offline maps',url:'/maps.html',offline:true},meridian:{title:'Meridian',url:'https://dailymag.marktan.ai/'},marktan:{title:'marktan.ai',url:'https://www.marktan.ai/'}};
function openFieldstationSite(key){
 const site=fieldstationSites[key];if(!site)return;
 closeKiwix(false);kiwixReading=true;document.body.classList.add('reading-kiwix');
 for(const id of ['art','home','catalogue','private','energy','browser','discover','ask','spotify','codex','playlists-page','youtube'])$('#'+id).hidden=true;
 $('#kiwix-reader').hidden=false;$('#kiwix-title').textContent=site.title;
 $('#share-article').hidden=true;$('#kiwix-start').hidden=false;$('#kiwix-start').textContent=site.offline?'Back to overview':'Site home';
 document.querySelectorAll('nav button[data-view],nav button[data-site]').forEach(b=>{const active=b.dataset.site===key;b.classList.toggle('active',active);if(active)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
 const frame=document.createElement('iframe');frame.title=site.title;frame.src=site.url;
 frame.setAttribute('sandbox','allow-scripts allow-same-origin allow-forms allow-popups allow-downloads');frame.referrerPolicy='strict-origin-when-cross-origin';frame.allowFullscreen=true;
 $('#kiwix-frame').replaceChildren(frame);$('#kiwix-start').onclick=()=>{frame.src=site.url};
 document.querySelector('footer span:last-child').textContent=site.offline?'Available offline':'Internet required';window.scrollTo(0,0);
 $('#kiwix-return').focus();
}
document.querySelectorAll('[data-site]').forEach(button=>button.onclick=()=>openFieldstationSite(button.dataset.site));
