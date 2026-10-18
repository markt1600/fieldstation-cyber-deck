let selectedVideoCategory='';
const videoCategoryIcons={'Movies':'🎬','TV Shows':'📺','Documentaries':'🌍','Music Videos & Concerts':'♫','Learning & How-to':'📚','News & Podcasts':'◉','Sports':'⚽','Personal & Family':'⌂','Bonus Features':'★','Uncategorized':'▤','Support Files & Incomplete Downloads':'⚙'};
const videoCategories=['Movies','TV Shows','Documentaries','Music Videos & Concerts','Learning & How-to','News & Podcasts','Sports','Personal & Family','Bonus Features','Uncategorized','Support Files & Incomplete Downloads'];
function classifyVideo(i){
 const folder=(i.folder||'').replaceAll('\\','/'),parts=folder.split('/'),text=[i.title,i.name,folder,i.genre,i.show].join(' ').toLowerCase();
 const result=(category,collection,reason)=>({category,collection:collection||'Other',reason});
 const part=parts.find(x=>/itunes extras|\.ite$/i.test(x));
 if(/\.tmp(?:\/|$)/i.test(folder)||i.name==='download.m4v')return result('Support Files & Incomplete Downloads','Temporary downloads','Temporary download path or filename');
 if(part&&/\/(images|motion)\//i.test(folder+'/'))return result('Support Files & Incomplete Downloads','Menu animations','iTunes menu asset path');
 if(part)return result('Bonus Features',part.replace(/\s*-?\s*iTunes.*$/i,'').replace(/\.ite$/i,''),'iTunes extras package');
 if(/penny movies|family videos|home videos|vacation|ziprider|family recording/.test(text))return result('Personal & Family','Family recordings','Family collection or recording title');
 if(/knots and ropework|tutorial|how[- ]to|lesson|lecture|choreography|cooking tutorial/.test(text))return result('Learning & How-to',/knots/.test(text)?'Knots & ropework':'Tutorials & demonstrations','Instructional title or collection');
 if(/baseball|world series|sports|football match|basketball game/.test(text))return result('Sports',parts.at(-1),'Sports title or collection');
 if(/documentar(?:y|ies)|planet earth|blue planet|nova documentary/.test(text))return result('Documentaries',i.show||'Documentaries','Documentary title or genre');
 if(/tiny desk|concert|music video|skidvid|\(live\)|live at|live in/.test(text)||i.videoKind==='music')return result('Music Videos & Concerts',i.artist||parts.at(-2)||'Performances','Music performance title or embedded tag');
 if(/podcasts|ac360|evening news|nightly news|meet the press|rachel maddow|today show/.test(text))return result('News & Podcasts',parts.at(-1),'Podcast or news programme collection');
 const tvIndex=parts.findIndex(x=>/^tv shows$/i.test(x));
 if(tvIndex>=0||i.videoKind==='tv'||/\bseason\s*\d|\bs\d{1,2}e\d{1,3}\b|\d{1,2}x\d{2}\b|rurouni kenshin.*\(tv\)/.test(text))return result('TV Shows',i.show||(tvIndex>=0?parts[tvIndex+1]:parts.at(-1)).replace(/^\d+\s*/,'').replace(/[, ]+season\s*\d+.*/i,'').replace(/\s*\(TV\).*/i,''),'Episode pattern, series collection or embedded tag');
 if(i.videoKind==='movie'||parts.some(x=>/^movies$/i.test(x))||/kiki.s delivery service|my sassy girl/.test(text))return result('Movies','Films','Movie collection, recognized title or embedded tag');
 // An artist directory is evidence only when there is a named album beneath it.
 if(parts[0]==='MP3s'&&parts.length>=3&&!/backup|downloads/i.test(parts[1]))return result('Music Videos & Concerts',parts[1],'Artist and album collection (inferred)');
 return result('Uncategorized','Needs review','Not enough reliable metadata');
}
const openVideoBranches=new Set();
function redundantVideoGroup(category,label){
 const normalize=s=>s.toLowerCase().replace(/[^a-z0-9]/g,'');
 return normalize(category)===normalize(label)||['Other','Manually categorized','Needs review'].includes(label)||({Movies:['Films'], 'Personal & Family':['Family recordings'], 'Learning & How-to':['Tutorials & demonstrations'], 'Music Videos & Concerts':['Performances']}[category]||[]).includes(label);
}
function renderVideoLibrary(items){
 $('#media-group').parentElement.hidden=true;
 const root=new Map();
 for(const i of items){const auto=classifyVideo(i),category=videoOverrides[trackKey(i)]||auto.category;let groups=root.get(category);if(!groups){groups=new Map();root.set(category,groups);}const name=category===auto.category?auto.collection:'Manually categorized';if(!groups.has(name))groups.set(name,[]);groups.get(name).push({item:i,auto,category});}
 const target=$('#results');target.replaceChildren();delete target.dataset.topics;delete target.dataset.mediaKey;
 $('#summary').textContent=items.length+' videos · browse by content · new files categorized automatically';
 if(!items.length){target.textContent='No matching videos available.';return;}
 if(!selectedVideoCategory){
  const grid=document.createElement('div');grid.className='music-category-grid video-category-grid';
  for(const category of videoCategories){const groups=root.get(category);if(!groups)continue;const count=[...groups.values()].reduce((n,r)=>n+r.length,0);const button=document.createElement('button');button.className='video-category-tile';button.innerHTML=categoryGraphic(category)+'<strong>'+esc(category)+'</strong><small>'+count+' videos</small>';button.onclick=()=>{selectedVideoCategory=category;renderMediaLibrary();};grid.append(button);}
  target.append(grid);return;
 }
 const back=document.createElement('button');back.className='action secondary';back.textContent='← All video categories';back.onclick=()=>{selectedVideoCategory='';renderMediaLibrary();};target.append(back);

 for(const category of videoCategories){if(category!==selectedVideoCategory)continue;let groups=root.get(category);if(!groups)continue;
  const direct=category==='Music Videos & Concerts';
  if(direct)groups=new Map([[category,[...groups.values()].flat().sort((a,b)=>a.item.title.localeCompare(b.item.title))]]);
  openVideoBranches.add(category);
  const count=[...groups.values()].reduce((n,r)=>n+r.length,0);
  const buildCategory=()=>{
   const holder=document.createElement('div');
   for(const [label,rows] of [...groups].sort(([a],[b])=>a.localeCompare(b))){const buildRows=()=>{
    const body=document.createElement('div');body.className='video-grid';
    for(const {item,auto,category:cat} of rows){
     const row=document.createElement('article');row.className='video-card';row.innerHTML='<button class="video-preview" data-preview aria-label="Play '+esc(item.title)+'"><span aria-hidden="true">▶</span><img loading="lazy" alt="" src="/api/video-thumbnail/'+encodeURIComponent(item.id)+'"></button><div class="row-text"><div class="row-title">'+esc(item.title)+'</div><div class="meta">'+esc(cat==='Music Videos & Concerts'?musicVideoArtist(item):(videoOverrides[trackKey(item)]?'Your category':auto.reason))+'</div></div><button class="action" data-play>Play</button><button class="action" data-category>Category…</button>';
     row.querySelector('[data-play]').onclick=()=>openVideo(item);
     row.querySelector('[data-preview]').onclick=()=>openVideo(item);
     row.querySelector('img').onerror=e=>{e.target.hidden=true;};
     row.querySelector('[data-category]').onclick=()=>{const d=document.createElement('dialog');d.innerHTML='<h2>Video category</h2><p>'+esc(item.title)+'</p><label>Category <select><option value="">Automatic — '+esc(auto.category)+'</option>'+videoCategories.map(c=>'<option '+(videoOverrides[trackKey(item)]===c?'selected':'')+'>'+esc(c)+'</option>').join('')+'</select></label><button class="action" data-save>Save</button><button class="action" data-cancel>Cancel</button>';d.querySelector('[data-save]').onclick=()=>{changeMusicList({action:'classify',track:trackKey(item),category:d.querySelector('select').value});d.close();};d.querySelector('[data-cancel]').onclick=()=>d.close();d.onclose=()=>d.remove();document.body.append(d);d.showModal();};body.append(row);
    }return body;
   };if(redundantVideoGroup(category,label))holder.append(buildRows());else addGroup(holder,label+' · '+rows.length,category+'|'+label,buildRows);}return holder;
  };
  if(direct){const heading=document.createElement('h2');heading.textContent=category+' · '+count+' videos';target.append(heading,buildCategory());}
  else addGroup(target,category+' · '+count+' videos',category,buildCategory);
 }
 function addGroup(parent,label,key,build){const d=document.createElement('details');d.className='topic-group';const s=document.createElement('summary');if(videoCategoryIcons[key]){const icon=document.createElement('span');icon.className='video-category-icon';icon.setAttribute('aria-hidden','true');icon.textContent=videoCategoryIcons[key];s.append(icon,document.createTextNode(label));}else s.textContent=label;d.append(s);let built=false;const populate=()=>{if(!built){d.append(build());built=true;}};if(openVideoBranches.has(key)){populate();d.open=true;}d.ontoggle=()=>{if(!d.isConnected)return;if(d.open){openVideoBranches.add(key);populate();}else openVideoBranches.delete(key);};parent.append(d);}
}

function categoryGraphic(name){
 const paths={
 film:'<rect x="3" y="5" width="26" height="22" rx="2"/><path d="M9 5v22M23 5v22M3 11h6M3 21h6M23 11h6M23 21h6"/>',
 tv:'<rect x="3" y="8" width="26" height="19" rx="3"/><path d="m10 3 6 5 6-5M12 30h8"/>',
 globe:'<circle cx="16" cy="16" r="13"/><ellipse cx="16" cy="16" rx="6" ry="13"/><path d="M3 16h26M6 9h20M6 23h20"/>',
 music:'<path d="M12 24V7l15-3v17M12 12l15-3"/><ellipse cx="8" cy="24" rx="4" ry="3"/><ellipse cx="23" cy="21" rx="4" ry="3"/>',
 book:'<path d="M16 8C12 4 6 4 3 5v22c5-2 9-1 13 2 4-3 8-4 13-2V5c-5-1-9 0-13 3Zm0 0v21"/>',
 sport:'<circle cx="16" cy="16" r="13"/><path d="m16 9 7 5-3 8h-8l-3-8 7-5ZM16 3v6M29 16l-6-2M24 27l-4-5M8 27l4-5M3 16l6-2"/>',
 home:'<path d="m3 15 13-12 13 12M7 12v17h18V12M13 29V18h6v11"/>',
 star:'<path d="m16 3 4 9 10 1-8 7 3 10-9-5-9 5 3-10-8-7 10-1Z"/>',
 wave:'<path d="M3 16h4l3-11 5 22 5-22 3 11h6"/>',
 disc:'<circle cx="16" cy="16" r="13"/><circle cx="16" cy="16" r="4"/><path d="M6 14a10 10 0 0 1 8-8M18 26a10 10 0 0 0 8-8"/>'};
 const key=({'Movies':'film','TV Shows':'tv','Documentaries':'globe','Music Videos & Concerts':'music','Learning & How-to':'book','Sports':'sport','Personal & Family':'home','Bonus Features':'star','World & Asian':'globe','Soundtracks & Stage':'film','Electronic & Ambient':'wave','Classical':'music','Country & Folk':'home','Pop':'star','Rock':'wave','Jazz & Blues':'music','Hip-Hop & R&B':'disc'})[name]||'disc';
 return '<svg class="category-graphic" viewBox="0 0 32 32" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'+paths[key]+'</svg>';
}

function musicVideoArtist(item){
 const artist=(item.artist||item.albumartist||'').trim();
 if(artist&&!/^unknown(?: artist)?$/i.test(artist))return artist;
 const parts=(item.folder||'').replaceAll('\\','/').split('/').filter(Boolean);
 const index=parts.findIndex(p=>p.toLowerCase()==='mp3s');
 if(index>=0&&parts.length>index+2&&!/^(unknown|various|backup|downloads)/i.test(parts[index+1]))return parts[index+1];
 const titledArtist=(item.title||'').match(/^(.{2,100}?)\s+[-–—]\s+\S/);
 if(titledArtist&&!/^\d+$/.test(titledArtist[1]))return titledArtist[1].trim();
 return 'Artist unavailable';
}
