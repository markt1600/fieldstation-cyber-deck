let catalogueTerm='',catalogueCategory='',catalogueRequest=0,catalogueLimit=24,catalogueTopics=new Map(),catalogueLoaded=false;
function renderCatalogue(){
 const root=$('#catalogue');
 if(!root.dataset.built){root.dataset.built='1';root.innerHTML='<form id="pdf-search-form" class="tools"><label class="search"><input id="pdf-query" type="search" placeholder="Search a title, chapter or words inside a PDF" aria-label="Search PDF collection"></label><button class="action">Search</button><button class="action secondary" type="button" id="pdf-clear">Clear</button></form><details class="filter-panel"><summary>Filter by collection</summary><div class="tools catalogue-filters">'+[['','All PDFs'],['Education','Education'],['Languages','Languages'],['Medical','Health'],['Practical','Practical skills'],['Books','Books']].map(([v,t])=>'<button class="action secondary" data-pdf-category="'+v+'" aria-pressed="'+(!v)+'">'+t+'</button>').join('')+'</div></details><p class="meta">Searches your PDF collection. For encyclopedia articles or novels, use <button class="text-action" id="pdf-explore">Books & Wikipedia</button>.</p><p id="pdf-state" role="status"></p><div id="pdf-results"></div>';
 let timer;$('#pdf-query').oninput=e=>{catalogueTerm=e.target.value;catalogueLimit=24;clearTimeout(timer);timer=setTimeout(loadCatalogue,300)};
 $('#pdf-search-form').onsubmit=e=>{e.preventDefault();clearTimeout(timer);loadCatalogue()};
 $('#pdf-clear').onclick=()=>{catalogueTerm='';$('#pdf-query').value='';catalogueLimit=24;loadCatalogue();$('#pdf-query').focus()};
 root.querySelectorAll('[data-pdf-category]').forEach(b=>b.onclick=()=>{catalogueCategory=b.dataset.pdfCategory;catalogueLimit=24;loadCatalogue()});$('#pdf-explore').onclick=()=>go('discover');
 }
 if(!catalogueLoaded)loadCatalogue();
}
async function loadCatalogue(){
 const request=++catalogueRequest;$('#pdf-state').textContent='Searching your collection…';
 try{
 const [response,treeResponse]=await Promise.all([fetch('/api/catalogue?'+new URLSearchParams({q:catalogueTerm,category:catalogueCategory})),catalogueTopics.size?Promise.resolve(null):fetch('/api/topics')]);
 if(!response.ok)throw Error('Could not load the PDF collection. Try Search again.');const result=await response.json();
 if(treeResponse?.ok){const tree=await treeResponse.json();catalogueTopics=new Map(tree.groups.flatMap(g=>g.items.map(b=>[b.id,{...b,subject:g.title}])))}
 if(request!==catalogueRequest)return;catalogueLoaded=true;
 $('#catalogue').querySelectorAll('[data-pdf-category]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.pdfCategory===catalogueCategory)));
 const books=result.books.filter(b=>!catalogueCategory||b.category===catalogueCategory),q=catalogueTerm.trim().toLowerCase();
 const title=b=>catalogueTopics.get(b.id)?.label||b.title;
 const matching=q?books.filter(b=>[title(b),b.title,b.folder,...(catalogueTopics.get(b.id)?.entries||[]).map(e=>e.title)].join(' ').toLowerCase().includes(q)):books;
 const cards=rows=>'<div class="catalogue-grid">'+rows.map(b=>'<article class="catalogue-card"><div class="resource-symbol" aria-hidden="true">'+categoryGraphic('Learning & How-to')+'</div><span class="meta">'+esc(catalogueTopics.get(b.id)?.subject||b.category)+'</span><h3>'+esc(title(b))+'</h3><p>'+b.pages+' pages'+(b.status.includes('OCR')?' · Scanned document':'')+'</p><p class="meta">'+esc(b.folder.split(/[\\/]/).filter(Boolean).pop()||b.category)+'</p><div class="catalogue-chapter-preview">'+(catalogueTopics.get(b.id)?.entries||[]).slice(0,2).map(e=>'<a data-share-added="1" href="/content/'+encodeURIComponent(b.id)+'#page='+Number(e.page)+'">'+esc(e.title)+' <small>· p. '+Number(e.page)+'</small></a>').join('')+'</div><div class="library-actions"><button class="action" data-pdf-read="'+esc(b.id)+'">Read</button><button class="action secondary" data-book="'+esc(b.id)+'">Contents</button></div></article>').join('')+'</div>';
 const hits=result.hits.map(h=>({...h,title:title(h)}));
 $('#pdf-state').textContent=q?matching.length+' title or chapter matches · '+hits.length+(hits.length===result.limit?'+':'')+' page matches':books.length+' PDFs · choose a book to read or explore its contents';
 let html=q?'<h2>Books & chapters</h2>'+(matching.length?cards(matching.slice(0,catalogueLimit)):'<p>No title matches. Page-text matches appear below.</p>'):cards(matching.slice(0,catalogueLimit));
 if(matching.length>catalogueLimit)html+='<button class="action secondary" id="catalogue-more">Show more books</button>';
 if(q)html+='<h2 class="catalogue-results-heading">Inside the PDFs</h2>'+(hits.length===result.limit?'<p class="meta">First '+result.limit+' page matches shown. Refine your search for more specific results.</p>':'')+(hits.length?groupedPdfResults(hits,books.map(b=>({...b,title:title(b)}))):'<div class="empty">No searchable text matched. Try fewer words; scanned pages may need text recognition.</div>');
 if(!books.length)html='<p class="empty">No PDFs in this collection yet. Choose All PDFs to browse the other collections.</p>';
 html+='<details class="filter-panel"><summary>About this index</summary><p>'+esc(result.state.error?'Indexing issue: '+result.state.error:result.state.running?'Currently indexing: '+result.state.current:'New and changed PDFs are checked automatically.')+' Scanned pages without text may not appear in search.</p></details>';
 $('#pdf-results').innerHTML=html;
 $('#catalogue-more')?.addEventListener('click',()=>{catalogueLimit+=24;loadCatalogue()});
 $('#pdf-results').querySelectorAll('[data-book]').forEach(b=>b.onclick=()=>showBook(b.dataset.book));
 $('#pdf-results').querySelectorAll('[data-pdf-read]').forEach(b=>b.onclick=()=>{const book=books.find(i=>i.id===b.dataset.pdfRead);openDocument({title:title(book),format:'PDF',url:'/content/'+encodeURIComponent(book.id)})});
 }catch(e){if(request===catalogueRequest){catalogueLoaded=false;$('#pdf-state').textContent=e.message;}}
}
async function showBook(id){
 const body=prepareViewer('Book contents');body.innerHTML='<p role="status">Loading contents…</p>';
 try{const r=await fetch('/api/catalogue?id='+encodeURIComponent(id));if(!r.ok)throw Error('Contents unavailable.');const b=await r.json();if(b.error)throw Error(b.error);if(!$('#viewer').open)return;
 const meta=catalogueTopics.get(id),title=meta?.label||b.title,entries=meta?.entries||b.toc;$('#viewer-title').textContent=title;
 body.innerHTML='<p>'+b.pages+' pages · '+esc(meta?.subject||b.category)+'</p><button class="action" id="contents-read">Read from beginning</button><h3>Contents</h3>'+(entries.length?'<div class="library-chapters">'+entries.map(t=>'<button class="topic-link" data-contents-page="'+Number(t.page)+'">'+esc(t.title)+'<small>Page '+Number(t.page)+'</small></button>').join('')+'</div>':'<p>No reliable chapter links yet. Read the book or search its text.</p>')+'<details class="filter-panel"><summary>Preview & source details</summary><p>'+esc(b.excerpt||'No extractable text. This document may need text recognition.')+'</p><p class="meta">'+esc(meta?.method||b.status)+'</p></details>';
 const read=page=>openDocument({title,format:'PDF',url:'/content/'+encodeURIComponent(id)+'#page='+page});$('#contents-read').onclick=()=>read(1);body.querySelectorAll('[data-contents-page]').forEach(button=>button.onclick=()=>read(Number(button.dataset.contentsPage)));
 }catch(e){if($('#viewer').open)body.textContent=e.message;}
}

function groupedPdfResults(hits,books=[]){
 const metadata=new Map(books.map(b=>[b.id,b])),groups=new Map();
 for(const hit of hits){const book=metadata.get(hit.id)||hit;
  const multipart=['Medical','Practical'].includes(book.category)&&book.folder&&/Where There Is No|Community Guide/.test(book.folder);
  const key=multipart?book.folder:hit.id;const title=multipart?book.folder.split(/[\\/]/).pop():hit.title;
  if(!groups.has(key))groups.set(key,{title,category:hit.category,hits:[]});groups.get(key).hits.push(hit);
 }
 return [...groups.values()].map(g=>'<section class="search-book"><h3>'+esc(g.title)+'</h3><p class="meta">'+esc(g.category)+' · '+g.hits.length+' matching page'+(g.hits.length===1?'':'s')+' shown</p>'+g.hits.sort((a,b)=>a.id===b.id?Number(a.page)-Number(b.page):a.title.localeCompare(b.title,undefined,{numeric:true})).map(b=>'<article class="row"><div class="row-text"><div class="meta">'+(b.title!==g.title?esc(b.title)+' · ':'')+'PDF page '+Number(b.page)+'</div><p>'+esc(b.excerpt)+'</p></div><a class="action" target="_blank" rel="noopener" href="/content/'+encodeURIComponent(b.id)+'#page='+Number(b.page)+'">Read page</a></article>').join('')+'</section>').join('');
}

const discovery={"books": [{"title": "Frankenstein; Or, The Modern Prometheus", "author": "Mary Wollstonecraft Shelley", "rank": 1, "path": "Frankenstein%3B%20Or%2C%20The%20Modern%20Prometheus_cover.84"}, {"title": "Moby Dick; Or, The Whale", "author": "Herman Melville", "rank": 2, "path": "Moby%20Dick%3B%20Or%2C%20The%20Whale_cover.2701"}, {"title": "Romeo and Juliet", "author": "William Shakespeare", "rank": 3, "path": "Romeo%20and%20Juliet_cover.1513"}, {"title": "Pride and Prejudice", "author": "Jane Austen", "rank": 4, "path": "Pride%20and%20Prejudice_cover.1342"}, {"title": "Alice's Adventures in Wonderland", "author": "Lewis Carroll", "rank": 5, "path": "Alice%27s%20Adventures%20in%20Wonderland_cover.11"}, {"title": "The Strange Case of Dr. Jekyll and Mr. Hyde", "author": "Robert Louis Stevenson", "rank": 6, "path": "The%20Strange%20Case%20of%20Dr.%20Jekyll%20and%20Mr.%20Hyde_cover.43"}, {"title": "The Complete Works of William Shakespeare", "author": "William Shakespeare", "rank": 7, "path": "The%20Complete%20Works%20of%20William%20Shakespeare_cover.100"}, {"title": "A Room with a View", "author": "E. M. (Edward Morgan) Forster", "rank": 8, "path": "A%20Room%20with%20a%20View_cover.2641"}, {"title": "Middlemarch", "author": "George Eliot", "rank": 9, "path": "Middlemarch_cover.145"}, {"title": "The King in Yellow", "author": "Robert W. (Robert William) Chambers", "rank": 10, "path": "The%20King%20in%20Yellow_cover.8492"}, {"title": "The Scarlet Letter", "author": "Nathaniel Hawthorne", "rank": 11, "path": "The%20Scarlet%20Letter_cover.25344"}, {"title": "Little Women; Or, Meg, Jo, Beth, and Amy", "author": "Louisa May Alcott", "rank": 12, "path": "Little%20Women%3B%20Or%2C%20Meg%2C%20Jo%2C%20Beth%2C%20and%20Amy_cover.37106"}, {"title": "The Legend of Sleepy Hollow", "author": "Washington Irving", "rank": 13, "path": "The%20Legend%20of%20Sleepy%20Hollow_cover.41"}, {"title": "Dracula", "author": "Bram Stoker", "rank": 14, "path": "Dracula_cover.345"}, {"title": "The Blue Castle: a novel", "author": "L. M. (Lucy Maud) Montgomery", "rank": 15, "path": "The%20Blue%20Castle%3A%20a%20novel_cover.67979"}, {"title": "Beowulf: An Anglo-Saxon Epic Poem", "author": "Anonymous", "rank": 16, "path": "Beowulf%3A%20An%20Anglo-Saxon%20Epic%20Poem_cover.16328"}, {"title": "The Enchanted April", "author": "Elizabeth Von Arnim", "rank": 17, "path": "The%20Enchanted%20April_cover.16389"}, {"title": "The Adventures of Ferdinand Count Fathom — Complete", "author": "T. (Tobias) Smollett", "rank": 18, "path": "The%20Adventures%20of%20Ferdinand%20Count%20Fathom%20%E2%80%94%20Complete_cover.6761"}, {"title": "Cranford", "author": "Elizabeth Cleghorn Gaskell", "rank": 19, "path": "Cranford_cover.394"}, {"title": "Twenty years after", "author": "Alexandre Dumas", "rank": 20, "path": "Twenty%20years%20after_cover.1259"}], "wikipedia": [{"title": "Solar power", "path": "Solar_power"}, {"title": "Water purification", "path": "Water_purification"}, {"title": "Agriculture", "path": "Agriculture"}, {"title": "Electricity", "path": "Electricity"}, {"title": "Mathematics", "path": "Mathematics"}, {"title": "French language", "path": "French_language"}, {"title": "Standard Chinese", "path": "Standard_Chinese"}, {"title": "Singapore", "path": "Singapore"}]};

let discoveryTab='books',wikiRequest=0;
function archiveURL(name,path){return 'http://'+location.hostname+':8766/kiwix/content/'+name+'/'+path;}
function readDiscovery(name,entry){const item=data.items.find(i=>i.name===name+'.zim'&&i.status==='ready');if(!item||!data.kiwix){alert('Connect the library drive and start Kiwix to read this collection.');return;}openKiwix({...item,title:entry.title},entry.path);}
function renderDiscovery(){
 const root=$('#discover');if(root.dataset.built)return;root.dataset.built='1';
 root.innerHTML='<div class="tools discovery-tabs"><button class="action" id="show-books">Books</button><button class="action" id="show-wiki">Wikipedia</button></div><section id="gutenberg-browser"></section><section id="wiki-browser" hidden><div class="section-heading"><h2>Explore something new</h2><button class="action" id="wiki-shuffle">Shuffle topics</button></div><p id="wiki-status" role="status"></p><div id="wiki-cards" class="discovery-grid wiki-grid"></div></section>';
 buildGutenbergBrowser();
 function tab(which){discoveryTab=which;$('#gutenberg-browser').hidden=which!=='books';$('#wiki-browser').hidden=which!=='wiki';$('#show-books').setAttribute('aria-pressed',which==='books');$('#show-wiki').setAttribute('aria-pressed',which==='wiki');if(which==='wiki')loadWiki();}
 $('#show-books').onclick=()=>tab('books');$('#show-wiki').onclick=()=>tab('wiki');$('#wiki-shuffle').onclick=loadWiki;tab(discoveryTab);
}
async function loadWiki(){
 const request=++wikiRequest;$('#wiki-status').textContent='Finding topics in your offline collection…';$('#wiki-shuffle').disabled=true;
 try{const response=await fetch('/api/discovery');if(!response.ok)throw Error('Wikipedia suggestions are unavailable. Try again.');const result=await response.json();if(request!==wikiRequest)return;
 $('#wiki-status').textContent='A fresh selection from '+result.total.toLocaleString()+' essential topics · saved Wikipedia Vital Articles list.';
 $('#wiki-cards').innerHTML=result.items.map((b,n)=>'<button class="discovery-card" data-wiki="'+n+'"><span class="discovery-art"><span class="cover-fallback" aria-hidden="true">'+esc(b.title)+'</span>'+(b.image?'<img loading="lazy" alt="" src="'+esc(archiveURL('wikipedia_en_all_maxi_2026-08',b.image))+'">':'')+'</span><strong>'+esc(b.title)+'</strong><small>Read offline →</small></button>').join('')||'<p>No suggestions available. Please check Kiwix.</p>';
 $('#wiki-cards').querySelectorAll('img').forEach(i=>i.onerror=()=>i.remove());$('#wiki-cards').querySelectorAll('[data-wiki]').forEach(b=>b.onclick=()=>readDiscovery('wikipedia_en_all_maxi_2026-08',result.items[Number(b.dataset.wiki)]));
 }catch(e){if(request===wikiRequest)$('#wiki-status').textContent=e.message;}finally{if(request===wikiRequest)$('#wiki-shuffle').disabled=false;}
}

let gutenbergPage=0,gutenbergRequest=0,gutenbergShuffle=false;
function buildGutenbergBrowser(){
 const root=$('#gutenberg-browser');root.innerHTML='<div class="section-heading"><h2>Browse Gutenberg books</h2><button class="action" id="gb-shuffle">Shuffle top 500</button><button class="action secondary" id="gb-ranked">Ranked view</button></div><p>Start with popular reads from the November 2025 archive.</p><details class="filter-panel"><summary>Search, filter &amp; sort</summary><div class="wifi-form"><label>Title or author<input id="gb-query" type="search"></label><label>Topic<select id="gb-topic"><option value="">All topics</option></select></label><label>Audience<select id="gb-audience"><option value="">All books · ages unclassified</option><option value="children">Children’s literature</option></select></label><label>Sort by<select id="gb-sort"><option value="popular">Popularity · saved November 2025 order</option><option value="title">Title A–Z</option><option value="author">Author A–Z</option></select></label></div><p class="meta">Children’s literature is a subject category; ages and reading levels are unclassified.</p></details><p id="gb-count" role="status"></p><div id="gb-results" class="discovery-grid book-grid"></div><div class="tools"><button class="action" id="gb-prev">Previous</button><button class="action" id="gb-next">Next</button></div>';
 $('#gb-shuffle').onclick=()=>{gutenbergShuffle=true;gutenbergPage=0;loadGutenberg()};$('#gb-ranked').onclick=()=>{gutenbergShuffle=false;gutenbergPage=0;loadGutenberg()};
 let timer;$('#gb-query').oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>{gutenbergPage=0;loadGutenberg();},250)};
 for(const id of ['gb-topic','gb-audience','gb-sort'])$('#'+id).onchange=()=>{gutenbergPage=0;loadGutenberg()};
 $('#gb-prev').onclick=()=>{gutenbergPage=Math.max(0,gutenbergPage-1);loadGutenberg()};$('#gb-next').onclick=()=>{gutenbergPage++;loadGutenberg()};loadGutenberg();
}
async function loadGutenberg(){
 const request=++gutenbergRequest;const params=new URLSearchParams({q:$('#gb-query').value,topic:$('#gb-topic').value,audience:$('#gb-audience').value,sort:$('#gb-sort').value,page:gutenbergPage,shuffle:gutenbergShuffle?1:0});
 try{const response=await fetch('/api/gutenberg?'+params);if(!response.ok)throw Error('Book catalogue unavailable');const result=await response.json();if(request!==gutenbergRequest)return;
 if($('#gb-topic').options.length===1)for(const [value,label] of Object.entries(result.topics)){if(value){const o=document.createElement('option');o.value=value;o.textContent=label;$('#gb-topic').append(o);}}
 $('#gb-count').textContent=result.total.toLocaleString()+' books · page '+(result.page+1)+' of '+Math.max(1,Math.ceil(result.total/result.pageSize));$('#gb-prev').disabled=!result.page;$('#gb-next').disabled=(result.page+1)*result.pageSize>=result.total;
 if(result.shuffle){$('#gb-count').textContent='Shuffled from the top 500 · '+result.total+' match your filters';$('#gb-prev').disabled=true;$('#gb-next').disabled=true;}
 $('#gb-results').innerHTML=result.books.map((b,n)=>'<button class="discovery-card" data-gb="'+n+'"><span class="discovery-art"><span class="cover-fallback" aria-hidden="true">'+esc(b.title)+'</span><img loading="lazy" alt="" src="'+esc(archiveURL('gutenberg_en_all_2025-11','covers/'+encodeURIComponent(b.id)+'_cover_image.jpg'))+'"></span><strong>'+esc(b.title)+'</strong><small>'+esc(b.author)+'</small></button>').join('')||'<p>No books match these filters.</p>';
 $('#gb-results').querySelectorAll('img').forEach(i=>i.onerror=()=>i.remove());
 $('#gb-results').querySelectorAll('[data-gb]').forEach(button=>button.onclick=()=>openBookReader(result.books[Number(button.dataset.gb)]));
 }catch(e){$('#gb-count').textContent=e.message;}
}
