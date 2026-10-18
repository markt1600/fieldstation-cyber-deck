let topicRenderKey='';
function renderBrowseModes(){
 const node=$('#browse-modes'),enabled=['library','education','languages'].includes(view);
 node.hidden=!enabled;$('#filter').hidden=view!=='downloads';
 if(!enabled){node.innerHTML='';return;}
 node.innerHTML=['reading','listening'].map(m=>'<button class="action" aria-pressed="'+(browseMode===m)+'" data-mode="'+m+'">'+(m==='reading'?'Reading · topics & chapters':'Listening · audio lessons')+'</button>').join('');
 node.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{browseMode=b.dataset.mode;$('#search').value='';delete $('#results').dataset.topics;renderRows()});
}
function renderMediaContents(){
 const audio=['MP3','M4A','OGG','WAV'],video=['MP4','WEBM','MKV','AVI','MOV','M4V'];
 const query=$('#search').value.toLowerCase();$('#search').placeholder='Search audio or video lessons';$('#search').setAttribute('aria-label','Search audio or video lessons');
 const items=data.items.filter(i=>i.status==='ready'&&(view==='movies'?([...audio,...video].includes(i.format)&&!(i.category==='Languages'&&audio.includes(i.format))):audio.includes(i.format)&&(view==='languages'?i.category==='Languages':view==='education'?i.category==='Education':!['Languages','Education'].includes(i.category)))).filter(i=>(i.title+' '+i.folder).toLowerCase().includes(query));
 const groups={};for(const item of items){const folder=item.folder.replaceAll('\\',' / ');const key=(!folder||folder==='.')?(item.category==='Movies'?'YouTube Downloads':'Library'):folder;(groups[key]??=[]).push(item);}
 $('#summary').textContent=items.length+' audio / video files · grouped by course or collection';
 const target=$('#results');const mediaKey=view+'|'+query+'|'+items.length;if(target.dataset.mediaKey===mediaKey&&target.querySelector('[data-media]'))return;target.dataset.mediaKey=mediaKey;delete target.dataset.topics;
 target.innerHTML=Object.entries(groups).map(([name,rows])=>'<details class="topic-group" '+(query?'open':'')+'><summary>'+esc(name)+' · '+rows.length+'</summary>'+rows.sort((a,b)=>a.title.localeCompare(b.title,undefined,{numeric:true})).map(i=>'<article class="row"><div class="row-text"><div class="row-title">'+esc(i.title.replace(/^\d+[-_ ]*/,'').replace(/[-_]/g,' '))+'</div></div><button class="action" data-media="'+esc(i.id)+'">Play</button></article>').join('')+'</details>').join('')||'<p>No audio or video is available in this section.</p>';
 target.querySelectorAll('[data-media]').forEach(b=>b.onclick=()=>openItem(data.items.find(i=>i.id===b.dataset.media)));
}
async function renderTopics(version){
 const target=$('#results'), key=view+'|'+scope+'|'+data.items.filter(i=>i.status==='ready').length;
 $('#summary').textContent='Browse by subject · select a chapter to read its page';
 if(target.dataset.topics===key)return;
 target.innerHTML='<p>Loading topics…</p>';target.dataset.topics=key;
 try{
  const response=await fetch('/api/topics');if(!response.ok)throw Error('Topic contents unavailable');const result=await response.json();
  if(version!==pdfSearchVersion){target.dataset.topics='';return;}
  const education=['Mathematics','Science','Humanities & study skills'],languages=['French','Mandarin','Other languages'];const groups=result.groups.filter(g=>view==='education'?education.includes(g.title):view==='languages'?languages.includes(g.title):![...education,...languages].includes(g.title));
  const link=(id,n)=>'/content/'+encodeURIComponent(id)+'#page='+Number(n);
  target.innerHTML='<p>Browse subjects, then choose a section. Chapter links open the exact PDF page. Source names are shown underneath.</p>'+groups.map(g=>'<details class="topic-group" data-topic="'+esc(g.title)+'"><summary>'+esc(g.title)+'</summary>'+g.items.map(b=>'<details class="topic-book"><summary>'+esc(b.label)+'</summary><p class="meta">'+esc(b.source)+' · '+esc(b.method)+'</p><a class="topic-link" target="_blank" rel="noopener" href="'+link(b.id,1)+'">Read from the beginning</a>'+b.entries.map(e=>'<a class="topic-link" style="margin-left:'+Math.min(e.depth||0,4)*12+'px" target="_blank" rel="noopener" href="'+link(b.id,e.page)+'">'+esc(e.title)+' <small>· PDF page '+Number(e.page)+'</small></a>').join('')+(!b.entries.length?'<p class="meta">Detailed contents are not available yet. Use topic search or read the source.</p>':'')+'</details>').join('')+'</details>').join('');
  const extras=data.items.filter(i=>['HTML','EPUB'].includes(i.format)&&i.status==='ready'&&(view==='education'?i.category==='Education':view==='languages'?i.category==='Languages':!['Education','Languages'].includes(i.category)));
  const recipes=extras.filter(i=>i.folder.toLowerCase().includes('recipes')),other=extras.filter(i=>!recipes.includes(i)&&!i.folder.includes('Knots and ropework'));
  for(const [label,items] of [['Recipes & cooking',recipes],['Other reading & interactive resources',other]])if(items.length){target.insertAdjacentHTML('beforeend','<details class="topic-group" data-topic="'+label+'"><summary>'+label+'</summary>'+items.map(i=>'<button class="topic-link" data-resource="'+esc(i.id)+'">'+esc(i.title)+'</button>').join('')+'</details>');}
  if(view==='library'){
   const knots=data.items.filter(i=>i.status==='ready'&&i.folder.includes('Knots and ropework')&&['MP4','WEBM'].includes(i.format));
   if(knots.length){
    let group=Array.from(target.querySelectorAll('[data-topic]')).find(n=>n.dataset.topic==='Knots & ropework');
    if(!group){group=document.createElement('details');group.className='topic-group';group.dataset.topic='Knots & ropework';group.innerHTML='<summary>Knots &amp; ropework</summary>';target.append(group);}
    group.insertAdjacentHTML('beforeend','<h3>Watch demonstrations · offline videos</h3>'+knots.map(i=>'<button class="topic-link" data-resource="'+esc(i.id)+'">'+esc(i.title)+' · Play in VLC</button>').join('')+extras.filter(i=>i.folder.includes('Knots and ropework')).map(i=>'<button class="topic-link" data-resource="'+esc(i.id)+'">Sources &amp; video credits</button>').join(''));
   }
  }
  target.querySelectorAll('[data-resource]').forEach(b=>b.onclick=()=>openItem(data.items.find(i=>i.id===b.dataset.resource)));
  const archives=data.items.filter(i=>i.format==='ZIM'&&i.status==='ready'&&(view==='education'?i.category==='Education':view==='languages'?i.category==='Languages':!['Education','Languages'].includes(i.category)));
  for(const a of archives){
   const text=(a.title+' '+a.name).toLowerCase();
   const subject=/wiktionary_fr/.test(text)?'French':/wiktionary_zh/.test(text)?'Mandarin':/wiktionary/.test(text)?'Dictionaries':/cooking/.test(text)?'Recipes & cooking':/gardening/.test(text)?'Food & growing':/ifixit|mechanics|electronics|diy\./.test(text)?'Repairs & maintenance':/mdwiki/.test(text)?'General health & medicines':/wikivoyage/.test(text)?'Travel & places':/phet/.test(text)?'Science':'Encyclopedias & reference';
   let group=Array.from(target.querySelectorAll('[data-topic]')).find(n=>n.dataset.topic===subject);
   if(!group){group=document.createElement('details');group.className='topic-group';group.dataset.topic=subject;group.innerHTML='<summary>'+esc(subject)+'</summary>';target.append(group);}
   const button=document.createElement('button');button.className='topic-link';const repairLabel=/ifixit/.test(text)?'Electronics & appliances — illustrated iFixit guides':/mechanics/.test(text)?'Cars & motorcycles — maintenance and troubleshooting':/diy\./.test(text)?'Home repairs — plumbing, toilets, fixtures and more':/electronics/.test(text)?'Electronics — circuits, components and troubleshooting':a.title;button.textContent=repairLabel+' — browse';button.onclick=()=>openItem(a);group.append(button);
  }

 }catch(e){target.textContent=e.message;delete target.dataset.topics;}
}

// Library navigation keeps subjects, resources and chapter links on separate levels.
let libraryLimit=48,librarySubject='',libraryBook='',libraryTree=null,libraryTreePromise=null,libraryDrawKey='';
const libraryLabels={
 'Parenting & family life':['Parenting & family life','Practical guides for young children, teenagers and positive discipline','♡'],
 'Emergency preparedness & first aid':['First aid & emergencies','Emergency handbooks and first aid guides','✚'],
 'General health & medicines':['Health & medicines','Community care, prevention and medicine references','♡'],
 'Dental health':['Teeth & dental care','Dental guides and oral health','◇'],
 'Family & child health':['Family & children','Child health, childbirth and family care','⌂'],
 'Water & sanitation':['Water & sanitation','Clean water, toilets and waste','≈'],
 'Energy & electricity':['Energy & electricity','Power, circuits and clean energy','ϟ'],
 'Food & growing':['Gardening & growing','Plants, farming and food security','❧'],
 'Shelter & environmental safety':['Homes & safety','Healthy homes and environmental hazards','⌂'],
 'Community & environment':['Community & environment','Community health and natural resources','◎'],
 'Knots & ropework':['Knots & ropework','Illustrated steps and video demonstrations','∞'],
 'Repairs & maintenance':['Repairs & DIY','Fix electronics, vehicles and your home','⚒'],
 'Recipes & cooking':['Cooking & recipes','Cookbooks and cooking questions','♨'],
 'Travel & places':['Travel & places','Destinations and practical travel guides','↗'],
 'Mathematics':['Mathematics','Algebra, calculus, geometry and statistics','∑'],'Science':['Science','Biology, physics, chemistry and astronomy','⚛'],'Humanities & study skills':['Humanities & study skills','History, social sciences and learning','▤'],'French':['French','Courses, student texts and audio lessons','Fr'],'Mandarin':['Mandarin','Courses, pronunciation and audio lessons','文'],'Other languages':['Other languages','Additional language resources','◎'],'Interactive learning':['Interactive learning','Simulations and learning collections','▧'],
 'Reference & reading':['Books & reference','Encyclopedias, books and supporting references','▤']
};
function libraryResources(tree){
 const items=data.items.filter(i=>i.status==='ready'&&(view==='education'?i.category==='Education':view==='languages'?i.category==='Languages':!['Movies','Education','Languages'].includes(i.category))&&['PDF','ZIM','HTML','EPUB','WEBM','MP4','MP3','M4A','FLAC','OGG','WAV'].includes(i.format));
 const byID=new Map(tree.groups.flatMap(g=>g.items.map(b=>[b.id,{...b,subject:g.title}])));
 return items.map(item=>{
  const meta=byID.get(item.id),name=(item.name+' '+item.folder).toLowerCase();let subject=meta?.subject||'Reference & reading',title=meta?.label||item.title,description='';
  if(item.format==='ZIM'){
   const rules=[[/wikipedia/,'Reference & reading','Wikipedia','Illustrated encyclopedia'],[/gutenberg/,'Reference & reading','Project Gutenberg','Classic novels, poetry and nonfiction'],[/appropedia/,'Community & environment','Appropedia','Practical skills and sustainable living'],[/ifixit/,'Repairs & maintenance','iFixit','Illustrated repair guides'],[/mechanics/,'Repairs & maintenance','Vehicle maintenance','Cars, motorcycles and troubleshooting'],[/electronics/,'Energy & electricity','Electrical engineering','Circuits and electronics'],[/diy\./,'Repairs & maintenance','Home improvement','Home repairs and DIY'],[/gardening/,'Food & growing','Gardening & landscaping','Plants, gardens and growing'],[/cooking/,'Recipes & cooking','Seasoned Advice','Cooking questions and answers'],[/mdwiki/,'General health & medicines','MDWiki','Medical reference'],[/wikivoyage/,'Travel & places','Wikivoyage','Worldwide travel guide']];
   const match=rules.find(r=>r[0].test(name));if(match)[,subject,title,description]=match;
  }else if(/recipes|cooking/.test(name))subject='Recipes & cooking';
  else if(/parenting/.test(name)){subject='Parenting & family life';description=/training guide/i.test(name)?'Reference and activities for parent educators and facilitators':/teens/i.test(name)?'Family guidebook for parents and teenagers':/young children/i.test(name)?'Parent handbook for families with young children':'Practical positive discipline guidance for parents and caregivers';}
  else if(/knots|ropework/.test(name))subject='Knots & ropework';
  if(view==='education'&&item.format==='ZIM')subject='Interactive learning';if(view==='languages'){subject=/french|wiktionary_fr/i.test(name)?'French':/mandarin|chinese|wiktionary_zh/i.test(name)?'Mandarin':'Other languages';if(!meta)title=item.title.replace(/_/g,' ').replace(/^FSI\s*[-–]?\s*/i,'');}
  return {item,meta,subject,title,description};
 });
}
function libraryCard(r){return '<article class="library-resource"><div class="resource-symbol" aria-hidden="true">'+categoryGraphic(audioFormats.includes(r.item.format)?'Music Videos & Concerts':r.item.format==='ZIM'?'World & Asian':'Learning & How-to')+'</div><div class="format">'+esc(r.item.format==='ZIM'?'COLLECTION':r.item.format)+'</div><div class="row-text"><h3>'+esc(r.title)+'</h3><p>'+esc(r.description||(r.meta?.pages?r.meta.pages+' pages':'Available offline'))+'</p></div><div class="library-actions"><button class="action" data-lib-open="'+esc(r.item.id)+'">'+(audioFormats.includes(r.item.format)?'Listen':['WEBM','MP4'].includes(r.item.format)?'Watch':r.item.format==='ZIM'?'Browse':'Read')+'</button>'+(r.meta?.entries.length?'<button class="action secondary" data-lib-contents="'+esc(r.item.id)+'">Contents</button>':'')+'</div></article>';}
async function renderLibrary(version){
 const root=$('#results'),q=$('#search').value.trim().toLowerCase();$('#filter').hidden=true;$('#search').placeholder='Search books, subjects and chapters';$('#search').setAttribute('aria-label',$('#search').placeholder);
 $('#browse-modes').hidden=true;
 const key=JSON.stringify([view,librarySubject,libraryBook,q,libraryLimit,data.items.length]);if(libraryDrawKey===key&&root.dataset.library===key)return;
 root.dataset.library=key;libraryDrawKey=key;
 try{
  if(!libraryTree){root.innerHTML='<p role="status">Loading your library…</p>';libraryTreePromise??=fetch('/api/topics').then(r=>{if(!r.ok)throw Error('Could not load the library index.');return r.json()}).finally(()=>libraryTreePromise=null);libraryTree=await libraryTreePromise;}
  if(version!==pdfSearchVersion){libraryDrawKey='';delete root.dataset.library;return;}
  const all=libraryResources(libraryTree),groups=[...new Set(all.map(r=>r.subject))];
  const selected=all.find(r=>r.item.id===libraryBook),label=libraryLabels[librarySubject]?.[0]||librarySubject;
  let html='<div class="library-breadcrumb"><button class="action secondary" data-lib-subject="">All subjects</button>'+(librarySubject?'<span aria-hidden="true">/</span><button class="action secondary" data-lib-subject="'+esc(librarySubject)+'">'+esc(label)+'</button>':'')+'</div>';
  if(selected&&!q){
   $('#summary').textContent=selected.title;
   html+='<div class="section-heading"><h2>'+esc(selected.title)+'</h2><button class="action" data-lib-open="'+esc(selected.item.id)+'">Read from beginning</button></div><p class="meta">'+esc(selected.meta.method)+' · '+selected.meta.pages+' pages</p><div class="library-chapters">'+selected.meta.entries.map(e=>'<button class="topic-link" data-lib-page="'+Number(e.page)+'" data-lib-id="'+esc(selected.item.id)+'">'+esc(e.title)+'<small>Page '+Number(e.page)+'</small></button>').join('')+'</div>';
  }else if(!librarySubject&&!q){
   $('#summary').textContent=all.length+' resources · '+groups.length+' subjects · available offline';
   const featured=view==='library'?['wikipedia','gutenberg','ifixit','appropedia'].map(n=>all.find(r=>r.item.format==='ZIM'&&r.item.name.toLowerCase().includes(n))).filter(Boolean):all.filter(r=>r.item.format==='ZIM');
   html+='<h2>'+ (view==='languages'?'Dictionaries & reference':view==='education'?'Explore & learn':'Start exploring')+'</h2><div class="library-featured">'+featured.map(libraryCard).join('')+'</div><div class="section-heading"><h2>Browse by subject</h2><button class="action secondary" data-lib-subject="*">View all resources</button></div><div class="library-subjects">'+groups.map(g=>{const [title,description,icon]=libraryLabels[g]||[g,'Books and guides','▤'];return '<button class="library-subject" data-lib-subject="'+esc(g)+'"><span class="library-icon" aria-hidden="true">'+icon+'</span><strong>'+esc(title)+'</strong><span>'+esc(description)+'</span><small>'+all.filter(r=>r.subject===g).length+' resources →</small></button>';}).join('')+'</div>';
  }else{
   const rows=all.filter(r=>(!librarySubject||librarySubject==='*'||r.subject===librarySubject)&&(!q||[r.title,r.subject,r.description,r.item.folder,...(r.meta?.entries||[]).map(e=>e.title)].join(' ').toLowerCase().includes(q)));
   $('#summary').textContent=rows.length+' resources'+(q?' matching “'+$('#search').value.trim()+'”':'');
   html+='<h2>'+(q?'Search results':librarySubject==='*'?'All resources':esc(label))+'</h2><div class="library-resource-grid">'+rows.slice(0,libraryLimit).map(libraryCard).join('')+'</div>'+(rows.length?'':'<p class="empty">No titles or chapters match. Try another word or choose All subjects.</p>');
   if(rows.length>libraryLimit)html+='<button class="action" id="library-more">Show more resources</button>';
   if(q)html+='<section id="library-text-results" aria-live="polite"><h2>Inside the PDFs</h2><p>Searching page text…</p></section>';
  }
  root.innerHTML=html;$('#library-more')?.addEventListener('click',()=>{libraryLimit+=48;renderRows()});
  root.querySelectorAll('[data-lib-subject]').forEach(b=>b.onclick=()=>{librarySubject=b.dataset.libSubject;libraryBook='';libraryLimit=48;$('#search').value='';renderRows();window.scrollTo(0,0)});
  root.querySelectorAll('[data-lib-open]').forEach(b=>b.onclick=()=>{const r=all.find(r=>r.item.id===b.dataset.libOpen);openItem({...r.item,title:r.title})});
  root.querySelectorAll('[data-lib-contents]').forEach(b=>b.onclick=()=>{libraryBook=b.dataset.libContents;$('#search').value='';renderRows();window.scrollTo(0,0)});
  root.querySelectorAll('[data-lib-page]').forEach(b=>b.onclick=()=>openDocument({title:all.find(r=>r.item.id===b.dataset.libId).title,format:'PDF',url:'/content/'+encodeURIComponent(b.dataset.libId)+'#page='+Number(b.dataset.libPage)}));
  if(q){clearTimeout(pdfSearchTimer);pdfSearchTimer=setTimeout(async()=>{try{const response=await fetch('/api/catalogue?q='+encodeURIComponent(q));if(!response.ok)throw Error('PDF text search unavailable.');const result=await response.json();if(version!==pdfSearchVersion)return;const eligible=new Set(all.filter(r=>!librarySubject||librarySubject==='*'||r.subject===librarySubject).map(r=>r.item.id));const hits=result.hits.filter(h=>eligible.has(h.id));$('#library-text-results').innerHTML='<h2>Inside the PDFs</h2>'+ (hits.length?groupedPdfResults(hits,result.books):'<p>No indexed page matches. Scanned pages may not contain searchable text.</p>');}catch(e){if(version===pdfSearchVersion&&$('#library-text-results'))$('#library-text-results').textContent=e.message;}},250);}
 }catch(e){root.innerHTML='<p role="alert">'+esc(e.message)+'</p><button class="action" id="library-retry">Try again</button>';libraryDrawKey='';delete root.dataset.library;$('#library-retry').onclick=()=>renderRows();}
}
