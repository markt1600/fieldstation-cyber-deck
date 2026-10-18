let videoOverrides={},musicLists=[],chosenList='',musicGenre='';
function trackKey(i){return [i.collection||'',i.folder.replaceAll('\\','/'),i.name].join('|');}
async function loadMusicLists(){try{const r=await fetch('/api/playlists');if(!r.ok)throw Error('Unable to load playlists');const d=await r.json();musicLists=d.playlists;videoOverrides=d.videoOverrides||{};}catch(e){console.error(e);}}
async function changeMusicList(payload){try{const r=await fetch('/api/playlists',{method:'POST',headers:{'Content-Type':'application/json','X-Fieldstation':'playlists'},body:JSON.stringify(payload)});const d=await r.json();if(!r.ok)throw Error(d.error);musicLists=d.playlists;videoOverrides=d.videoOverrides||{};renderMediaLibrary();}catch(e){alert(e.message);}}
loadMusicLists();
let mediaFiltersOpen=false;
let mediaKind='music',mediaGroup='genre',mediaSort='track',audioQueue=[],audioIndex=-1,mediaVisible=[];
const audioFormats=['MP3','M4A','OGG','WAV','FLAC'];
const audioDock=document.createElement('section');audioDock.id='audio-dock';audioDock.hidden=true;
audioDock.setAttribute('aria-label','Music player');
audioDock.innerHTML='<div><strong id="audio-title"></strong><small id="audio-detail"></small><span id="audio-message" role="status"></span></div><div class="audio-controls"><button id="audio-prev" aria-label="Previous track">⏮</button><audio id="persistent-audio" controls preload="metadata"></audio><button id="audio-next" aria-label="Next track">⏭</button><button id="audio-stop">Stop</button></div>';
document.body.append(audioDock);
const persistentAudio=audioDock.querySelector('audio');
function playAudio(item,queue){
 audioQueue=queue||[item];audioIndex=audioQueue.findIndex(i=>i.id===item.id);
 audioDock.hidden=false;document.body.classList.add('audio-playing');
 document.querySelector('#audio-title').textContent=item.title;
 document.querySelector('#audio-detail').textContent=[item.artist,item.album].filter(Boolean).join(' · ');
 document.querySelector('#audio-message').textContent='';
 persistentAudio.dataset.compatibility='';
 persistentAudio.dataset.format=item.format;
 persistentAudio.dataset.trackId=item.id;
 persistentAudio.src=item.url;
 persistentAudio.play().catch(e=>{document.querySelector('#audio-message').textContent=e.name==='NotAllowedError'?'Playback was blocked by the browser. Tap the player’s Play button to start.':e.name==='AbortError'?'':'Unable to start this track: '+e.message;});
 document.querySelector('#audio-prev').disabled=audioIndex<=0;
 document.querySelector('#audio-next').disabled=audioIndex>=audioQueue.length-1;
}
function audioStep(delta){const next=audioIndex+delta;if(next>=0&&next<audioQueue.length)playAudio(audioQueue[next],audioQueue);}
document.querySelector('#audio-prev').onclick=()=>audioStep(-1);
document.querySelector('#audio-next').onclick=()=>audioStep(1);
document.querySelector('#audio-stop').onclick=()=>{persistentAudio.pause();persistentAudio.removeAttribute('src');persistentAudio.load();audioDock.hidden=true;document.body.classList.remove('audio-playing');audioQueue=[];audioIndex=-1;};
persistentAudio.onplaying=()=>{document.querySelector('#audio-message').textContent='';};
persistentAudio.onended=()=>audioStep(1);
persistentAudio.onerror=()=>{
 if(persistentAudio.dataset.format==='M4A'&&!persistentAudio.dataset.compatibility&&[3,4].includes(persistentAudio.error?.code)){
  persistentAudio.dataset.compatibility='requested';
  document.querySelector('#audio-message').textContent='Preparing compatible lossless playback…';
  persistentAudio.src='/audio-compatible/'+encodeURIComponent(persistentAudio.dataset.trackId);
  persistentAudio.play().catch(e=>{if(e.name!=='AbortError')document.querySelector('#audio-message').textContent='Unable to play compatible audio: '+e.message;});
  return;
 }
 document.querySelector('#audio-message').textContent='Track unavailable or unsupported. Check the media drive, or try another track.';
};
function renderMediaLibrary(){
 const q=$('#search').value.toLowerCase().trim();$('#search').placeholder='Search title, artist, album, genre or folder';
 $('#search').setAttribute('aria-label',$('#search').placeholder);
 const modes=$('#browse-modes');modes.hidden=false;
 modes.innerHTML=['music','videos'].map(k=>'<button class="action" data-kind="'+k+'" aria-pressed="'+(mediaKind===k)+'">'+(k==='music'?'Music & audio':'Videos')+'</button>').join('')+'<label>Group <select id="media-group">'+(mediaKind==='music'?['genre','artist']:['folder']).map(k=>'<option value="'+k+'" '+(k===mediaGroup?'selected':'')+'>'+({genre:'Category → artist → album',artist:'Artist → album',folder:'Folder'}[k]||k)+'</option>').join('')+'</select></label><label>Sort <select id="media-sort">'+['title','genre','track','duration'].map(k=>'<option '+(k===mediaSort?'selected':'')+'>'+k+'</option>').join('')+'</select></label>';
 modes.insertAdjacentHTML('beforeend','<button class="action" id="rescan-media" '+(data.scanning?'disabled':'')+'>'+(data.scanning?'Scanning…':'Rescan media')+'</button>');
 $('#rescan-media').onclick=async()=>{const b=$('#rescan-media');b.disabled=true;b.textContent='Scanning…';try{const r=await fetch('/api/rescan',{method:'POST',headers:{'X-Fieldstation':'rescan'}});if(!r.ok)throw Error('Unable to start scan');await refresh();}catch(e){b.disabled=false;b.textContent='Rescan media';alert(e.message);}};
 modes.querySelectorAll('[data-kind]').forEach(b=>b.onclick=()=>{mediaKind=b.dataset.kind;limit=50;renderMediaLibrary();});
 $('#media-group').onchange=e=>{mediaGroup=e.target.value;renderMediaLibrary();};$('#media-sort').onchange=e=>{mediaSort=e.target.value;renderMediaLibrary();};
 let items=data.items.filter(i=>i.status==='ready'&&(mediaKind==='music'?audioFormats.includes(i.format)&&i.category!=='Languages':[ 'MP4','WEBM','MKV','AVI','MOV','M4V'].includes(i.format)));
 if(mediaKind==='music'){
 modes.insertAdjacentHTML('beforeend','<button class="action" id="browse-playlists">♫ Browse playlists</button>');$('#browse-playlists').onclick=()=>go('playlists');
 const genres=broadMusicCategories.filter(g=>items.some(i=>musicCategory(i)===g));
 modes.insertAdjacentHTML('beforeend','<label>Category <select id="music-genre"><option value="">All categories</option>'+genres.map(g=>'<option '+(musicGenre===g?'selected':'')+'>'+esc(g)+'</option>').join('')+'</select></label><label>Playlist <select id="music-list"><option value="">All music</option>'+musicLists.map(p=>'<option value="'+esc(p.id)+'" '+(chosenList===p.id?'selected':'')+'>'+esc(p.name)+'</option>').join('')+'</select></label><button class="action" id="new-list">New playlist</button>');
 $('#music-genre').onchange=e=>{musicGenre=e.target.value;limit=50;renderMediaLibrary();};
 $('#music-list').onchange=e=>{chosenList=e.target.value;limit=50;renderMediaLibrary();};
 $('#new-list').onclick=()=>{const name=prompt('Playlist name');if(name?.trim())changeMusicList({action:'create',name});};
 if(musicGenre)items=items.filter(i=>musicCategory(i)===musicGenre);
 const list=musicLists.find(p=>p.id===chosenList);if(list)items=items.filter(i=>list.tracks.includes(trackKey(i)));
 }
 // Keep section navigation independent of the filters available in each mode.
 const tabs=document.createElement('div');tabs.className='media-tabs';
 const filters=document.createElement('div');filters.className='media-filters';
 for(const control of [...modes.children]){
  (control.matches('[data-kind],#rescan-media')?tabs:filters).append(control);
 }
 const drawer=document.createElement('details');drawer.className='filter-panel';drawer.open=mediaFiltersOpen;drawer.innerHTML='<summary>Filter, sort & playlists</summary>';drawer.append(filters);drawer.ontoggle=()=>{mediaFiltersOpen=drawer.open;};modes.replaceChildren(tabs,drawer);
 items=items.filter(i=>[i.title,i.artist,i.album,i.genre,i.folder].join(' ').toLowerCase().includes(q));
 items.sort((a,b)=>mediaSort==='genre'?(a.genre||'Uncategorized').localeCompare(b.genre||'Uncategorized')||a.title.localeCompare(b.title):mediaSort==='duration'?(a.duration||0)-(b.duration||0):mediaSort==='track'?(parseInt(a.tracknumber)||0)-(parseInt(b.tracknumber)||0)||a.title.localeCompare(b.title):a.title.localeCompare(b.title,undefined,{numeric:true}));
 mediaVisible=items;if(mediaKind==='music'){renderMusicTree(items);return;}renderVideoLibrary(items);
}

function musicActions(i){
 if(mediaKind!=='music')return '';
 const favorite=musicLists.find(p=>p.id==='favorites')?.tracks.includes(trackKey(i));
 return '<button class="action" data-fav="'+esc(i.id)+'" aria-label="'+(favorite?'Unfavorite':'Favorite')+' '+esc(i.title)+'" aria-pressed="'+!!favorite+'">'+(favorite?'★':'☆')+'</button><button class="action" data-addlist="'+esc(i.id)+'">+ Playlist</button>'+(chosenList&&chosenList!=='favorites'?'<button class="action" data-remove="'+esc(i.id)+'">Remove</button>':'');
}
function bindMusicActions(target,items){
 const key=b=>trackKey(items.find(i=>i.id===b));
 target.querySelectorAll('[data-fav]').forEach(b=>b.onclick=()=>changeMusicList({action:b.getAttribute('aria-pressed')==='true'?'remove':'add',playlist:'favorites',track:key(b.dataset.fav)}));
 target.querySelectorAll('[data-remove]').forEach(b=>b.onclick=()=>changeMusicList({action:'remove',playlist:chosenList,track:key(b.dataset.remove)}));
 target.querySelectorAll('[data-addlist]').forEach(b=>b.onclick=()=>{
  const dialog=document.createElement('dialog');dialog.innerHTML='<h2>Add to playlist</h2><label>Playlist <select>'+musicLists.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.name)+'</option>').join('')+'</select></label><button class="action" data-save>Add</button><button class="action" data-cancel>Cancel</button>';
  dialog.querySelector('[data-save]').onclick=()=>{changeMusicList({action:'add',playlist:dialog.querySelector('select').value,track:key(b.dataset.addlist)});dialog.close();};dialog.querySelector('[data-cancel]').onclick=()=>dialog.close();dialog.onclose=()=>dialog.remove();document.body.append(dialog);dialog.showModal();
 });
}

// Build branches from the whole filtered catalogue; render songs only in opened albums.
const openMusicBranches=new Set();
function musicTree(items,byGenre){
 const root=new Map();
 for(const item of items){
  const path=[...(byGenre?[musicCategory(item)]:[]),item.artist?.trim()||'Unknown artist',item.album?.trim()||'Unknown album · '+item.folder];
  let branch=root;
  path.forEach((label,index)=>{if(!branch.has(label))branch.set(label,index===path.length-1?[]:new Map());const next=branch.get(label);if(Array.isArray(next))next.push(item);else branch=next;});
 }
 return root;
}
function renderMusicTree(items){
 const target=$('#results');delete target.dataset.topics;delete target.dataset.mediaKey;
 target.replaceChildren();
 if(mediaGroup==='genre'&&!musicGenre){$('#summary').textContent=items.length+' tracks · browse a category or start a mix';renderMusicCategories(target,items);return;}
 if(musicGenre){const back=document.createElement('button');back.className='action secondary';back.textContent='← All music categories';back.onclick=()=>{musicGenre='';renderMediaLibrary();};target.append(back);}
 const tree=musicTree(items,false);
 $('#summary').textContent=items.length+' tracks · '+tree.size+' '+'artists'+' · expand to browse albums and songs';
 if(!items.length){target.innerHTML='<p>No tracks match these filters or this playlist.</p>';return;}
 const play=document.createElement('button');play.className='action';play.textContent='Play all matching tracks';play.onclick=()=>playAudio(items[0],items);target.append(play);
 for(const [label,makeQueue] of (musicGenre?[['Shuffle',shuffledMusic],['AI Top 10',categoryTopTen]]:[['Shuffle',shuffledMusic]])){const b=document.createElement('button');b.className='action secondary';b.textContent=label;b.onclick=async()=>{if(label==='AI Top 10')await loadMusicLists();const queue=makeQueue(items);if(queue.length)playAudio(queue[0],queue);};target.append(b);}
 const collapse=document.createElement('button');collapse.className='action';collapse.textContent='Collapse all';collapse.onclick=()=>{openMusicBranches.clear();renderMusicTree(items);};target.append(collapse);
 function addBranches(parent,branches,path){
  for(const [label,value] of [...branches].sort(([a],[b])=>a.localeCompare(b,undefined,{numeric:true}))){
   const key=JSON.stringify([mediaGroup,...path,label]);
   const details=document.createElement('details');details.className='topic-group music-branch';
   const summary=document.createElement('summary');summary.textContent=label+' · '+value.size+(' albums');
   if(Array.isArray(value))summary.textContent=label+' · '+value.length+' songs';
   summary.insertAdjacentHTML('afterbegin',categoryGraphic(Array.isArray(value)?'Other Audio':'Music Videos & Concerts'));details.append(summary);const body=document.createElement('div');body.className='music-children';details.append(body);let built=false;
   function populate(){if(built)return;built=true;
    if(value instanceof Map)addBranches(body,value,[...path,label]);
    else {
     const button=document.createElement('button');button.className='action';button.textContent='Play album';button.onclick=()=>playAudio(value[0],value);body.append(button);
     const rows=document.createElement('div');rows.innerHTML=value.map(i=>'<article class="row"><div class="row-text"><div class="row-title">'+esc((i.tracknumber?i.tracknumber+'. ':'')+i.title)+'</div><div class="meta">'+esc(i.duration?Math.floor(i.duration/60)+':'+String(Math.floor(i.duration%60)).padStart(2,'0'):'')+'</div></div>'+musicActions(i)+'<button class="action" data-track="'+esc(i.id)+'">Play</button></article>').join('');body.append(rows);
     bindMusicActions(rows,value);rows.querySelectorAll('[data-track]').forEach(b=>b.onclick=()=>playAudio(value.find(i=>i.id===b.dataset.track),value));
    }
   }
   if(openMusicBranches.has(key)){populate();details.open=true;}
   details.addEventListener('toggle',()=>{if(!details.isConnected)return;if(details.open){openMusicBranches.add(key);populate();}else openMusicBranches.delete(key);});
   parent.append(details);
  }
 }
 const artistGrid=document.createElement('div');artistGrid.className='music-artist-grid';target.append(artistGrid);addBranches(artistGrid,tree,[]);
}

const broadMusicCategories=['Pop','Rock','Hip-Hop & R&B','Jazz & Blues','Classical','Electronic & Ambient','Country & Folk','World & Asian','Soundtracks & Stage','Other Audio'];
const musicCategoryIcons=['♫','♬','◉','♩','𝄞','⌁','♧','◎','▣','♪'];
function musicCategory(i){
 const g=(i.genre||'').toLowerCase(),context=[i.artist,i.album,i.folder].join(' ').toLowerCase();
 if(/podcast|speech|audiobook|language|educational/.test(g))return 'Other Audio';
 if(/soundtrack|musical|anime|film score|stage/.test(g))return 'Soundtracks & Stage';
 if(/classical|baroque|symphon|opera|chamber/.test(g))return 'Classical';
 if(/world|latin|reggae|hawai|c-pop|j-pop|k-pop|mandarin|cantopop|chinese|asian|bossa/.test(g)||/[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]/.test(i.artist||''))return 'World & Asian';
 if(/jazz|blues|fusion/.test(g))return 'Jazz & Blues';
 if(/hip.?hop|rap|r&b|soul|funk|rhythmic/.test(g))return 'Hip-Hop & R&B';
 if(/country|folk|singer.songwriter|acoustic|bluegrass/.test(g))return 'Country & Folk';
 if(/electro|dance|ambient|ambience|new age|trance|house|techno|goa|chill/.test(g))return 'Electronic & Ambient';
 if(/rock|metal|punk|alternative|grunge|ska/.test(g))return 'Rock';
 if(/pop|easy listening|disco|holiday/.test(g))return 'Pop';
 if(/bach|beethoven|mozart|vivaldi|chopin|ravel/.test(context))return 'Classical';
 return 'Other Audio';
}
function uniqueMusic(items){const seen=new Set();return items.filter(i=>{const k=[i.artist||'',i.title||i.name].join('|').toLowerCase().replace(/\s+/g,' ').trim();if(seen.has(k))return false;seen.add(k);return true;});}
function shuffledMusic(items){const out=uniqueMusic(items);for(let i=out.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[out[i],out[j]]=[out[j],out[i]];}return out;}
function categoryTopTen(items){
 const name=musicCategory(items[0]||{}),list=musicLists.find(p=>p.name===name+' — AI Top 10');
 if(!list){go('playlists');setTimeout(()=>document.querySelector('#category-ai-panel')?.scrollIntoView({block:'center'}),100);return [];}
 const available=new Map(items.map(i=>[trackKey(i),i]));return list.tracks.map(k=>available.get(k)).filter(Boolean).slice(0,10);
}

function renderMusicCategories(target,items){
 const grid=document.createElement('div');grid.className='music-category-grid';
 for(const [n,name] of broadMusicCategories.entries()){
  const tracks=items.filter(i=>musicCategory(i)===name);if(!tracks.length)continue;
  const card=document.createElement('article');card.className='music-category-card';
  const browse=document.createElement('button');browse.className='category-browse';browse.innerHTML=categoryGraphic(name)+'<strong>'+esc(name)+'</strong><small>'+tracks.length+' tracks</small>';browse.onclick=()=>{musicGenre=name;renderMediaLibrary();};
  const actions=document.createElement('div');actions.className='category-actions';
  for(const [label,makeQueue] of [['Shuffle',shuffledMusic],['AI Top 10',categoryTopTen]]){const button=document.createElement('button');button.className='action secondary';button.textContent=label;button.setAttribute('aria-label',label+' — '+name);button.onclick=async()=>{if(label==='AI Top 10')await loadMusicLists();const queue=makeQueue(tracks);if(queue.length)playAudio(queue[0],queue);};actions.append(button);}
  card.append(browse,actions);grid.append(card);
 }
 target.append(grid);const note=document.createElement('p');note.className='meta';note.textContent='AI Top 10 plays the saved AI-curated category playlist. Refresh these mixes at the bottom of Playlists after adding music.';target.append(note);
}
