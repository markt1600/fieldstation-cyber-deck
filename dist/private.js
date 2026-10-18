let privateToken=null,privateFolder='',privateBlob=null,privateViewing=false,privateBusy=false;
const privateChannel=typeof BroadcastChannel==='undefined'?null:new BroadcastChannel('fieldstation-private');
const privateThumbs=new Map();let privateThumbObserver=null;
function clearPrivate(){privateThumbObserver?.disconnect();for(const url of privateThumbs.values())URL.revokeObjectURL(url);privateThumbs.clear();privateToken=null;privateFolder='';if(privateViewing){$('#viewer').close();$('#viewer-body').replaceChildren();privateViewing=false}if(privateBlob){URL.revokeObjectURL(privateBlob);privateBlob=null}$('#private').replaceChildren()}
privateChannel?.addEventListener('message',()=>{clearPrivate();if(view==='private')renderPrivate()});
$('#viewer').addEventListener('close',()=>{privateViewing=false;if(privateBlob){URL.revokeObjectURL(privateBlob);privateBlob=null}});
async function privateAPI(action,payload){
 const headers={'X-Fieldstation':'private','X-Private-Token':privateToken||''};
 if(payload!==undefined)headers['Content-Type']='application/json';
 const response=await fetch('/api/private/'+action,{method:payload===undefined?'GET':'POST',headers,cache:'no-store',body:payload===undefined?undefined:JSON.stringify(payload)});
 if(!response.ok){let error=await response.json();throw Error(error.error||'Private file request failed.')}
 return response.json();
}
async function renderPrivate(){
 if(privateBusy)return;
 const panel=$('#private');
 try{
  const state=await privateAPI('status');privateToken=state.token;
  if(!state.unlocked){
   privateThumbObserver?.disconnect();for(const url of privateThumbs.values())URL.revokeObjectURL(url);privateThumbs.clear();
   panel.innerHTML='<p class="dialog-note">'+(state.mounted?'Browser access blocked. The volume still needs to be ejected.':state.busy?'Complete or cancel the VeraCrypt password prompt.':'Locked. Your password is entered in VeraCrypt’s own window.')+'</p>'+
    '<p class="dialog-note">Master Backup April 2020 · Library drive</p>'+
    '<button class="action" id="private-unlock" '+(state.busy||state.mounted?'disabled':'')+'>Unlock</button> <button class="action" id="private-eject" '+(!state.mounted?'hidden':'')+'>Eject</button><p id="private-message" class="dialog-note"></p>';
   $('#private-unlock').onclick=async()=>{await privateAction('unlock',{})};
   $('#private-eject').onclick=ejectPrivate;return;
  }
  const result=await privateAPI('list?path='+encodeURIComponent(privateFolder));
  if(view!=='private')return;
  panel.innerHTML='<div class="tools"><button class="action" id="private-up">Up a folder</button><button class="action" id="private-eject">Eject & lock</button></div><p class="dialog-note">Read-only · '+esc(privateFolder||'Container root')+'</p><p id="private-message" class="dialog-note"></p><div id="private-items"></div>';
  $('#private-up').disabled=!privateFolder;$('#private-up').onclick=()=>{privateFolder=privateFolder.split('/').slice(0,-1).join('/');renderPrivate()};$('#private-eject').onclick=ejectPrivate;
  const rows=$('#private-items');
  const videoGrid=document.createElement('div');videoGrid.className='video-grid';
  privateThumbObserver?.disconnect();
  const currentThumbToken=privateToken;
  privateThumbObserver=new IntersectionObserver(entries=>{for(const entry of entries){if(!entry.isIntersecting)continue;privateThumbObserver.unobserve(entry.target);loadPrivateThumb(entry.target,currentThumbToken);}});
  result.items.forEach(item=>{if(!item.directory&&['.mp4','.mkv','.avi','.mov','.webm','.m4v'].includes(item.extension)){const card=document.createElement('article');card.className='video-card';const button=document.createElement('button');button.className='video-preview';button.setAttribute('aria-label','Play '+item.name);button.innerHTML='<span aria-hidden="true">▶</span>';const img=document.createElement('img');img.alt='';img.hidden=true;img.dataset.path=item.path;button.append(img);button.onclick=()=>viewPrivate(item);const title=document.createElement('div');title.className='row-text row-title';title.textContent=item.name;card.append(button,title);videoGrid.append(card);privateThumbObserver.observe(button);button.dataset.path=item.path;return;}const row=document.createElement('article');row.className='row';row.innerHTML='<div class="row-text"><div class="row-title">'+esc(item.name)+'</div><div class="meta">'+(item.directory?'Folder':size(item.size))+'</div></div>';const b=document.createElement('button');b.className='action';b.textContent=item.directory?'Browse':'View';b.onclick=()=>{if(item.directory){privateFolder=item.path;renderPrivate()}else viewPrivate(item)};row.append(b);rows.append(row)});
  if(videoGrid.children.length)rows.append(videoGrid);
  if(!result.items.length)rows.textContent='This folder is empty.';
 }catch(e){panel.textContent=e.message}
}
async function privateAction(action,payload){
 privateBusy=true;const message=$('#private-message');if(message)message.textContent=action==='unlock'?'Enter your password in the VeraCrypt window…':'Closing viewers and dismounting…';
 try{await privateAPI(action,payload);privateBusy=false;await renderPrivate()}catch(e){privateBusy=false;await renderPrivate();const m=$('#private-message');if(m)m.textContent=e.message}
}
async function ejectPrivate(){clearPrivate();privateChannel?.postMessage('lock');await privateAction('eject',{})}
async function viewPrivate(item){
 const media=['.mp4','.mkv','.avi','.mov','.webm','.m4v'];
 const office=['.doc','.docx','.odt','.rtf','.xls','.xlsx','.ppt','.pptx'];
 const currentToken=privateToken;
 $('#viewer-title').textContent=item.name;const body=$('#viewer-body');body.replaceChildren();privateViewing=true;$('#viewer').showModal();
 const note=document.createElement('p');note.className='dialog-note';body.append(note);
 const external=async()=>{try{const result=await privateAPI('open',{path:item.path});note.textContent=result.message}catch(e){note.textContent=e.message}};
 if(media.includes(item.extension)){await external();return}
 if(office.includes(item.extension)){const b=document.createElement('button');b.className='action';b.textContent='Open in LibreOffice';b.onclick=external;body.append(b);note.textContent='DOCX preview shows text only. Use LibreOffice for full formatting; close it before ejecting.';if(item.extension!=='.docx')return}
 try{
  const response=await fetch('/api/private/file?path='+encodeURIComponent(item.path),{headers:{'X-Fieldstation':'private','X-Private-Token':currentToken},cache:'no-store'});
  if(!response.ok)throw Error((await response.json()).error);
  const blob=await response.blob();if(currentToken!==privateToken||!privateViewing)return;
  if(['.txt','.docx'].includes(item.extension)){const pre=document.createElement('pre');pre.style.whiteSpace='pre-wrap';pre.textContent=await blob.text();if(currentToken===privateToken&&privateViewing)body.append(pre)}
  else {privateBlob=URL.createObjectURL(blob);const el=document.createElement(item.extension==='.pdf'?'iframe':'img');el.src=privateBlob;el.style.width='100%';if(item.extension==='.pdf'){el.title=item.name;el.style.height='65vh'}else {el.alt=item.name;el.style.objectFit='contain';el.style.maxHeight='65vh'}body.append(el)}
 }catch(e){note.textContent=e.message}
}
setInterval(async()=>{if(!privateToken||privateBusy)return;try{const s=await privateAPI('status');if(s.token!==privateToken){clearPrivate();if(view==='private')renderPrivate()}}catch{clearPrivate()}},2000);

async function loadPrivateThumb(button,token){
 const path=button.dataset.path;const img=button.querySelector('img');
 try{
  let url=privateThumbs.get(path);
  if(!url){
   const response=await fetch('/api/private/thumbnail?path='+encodeURIComponent(path),{headers:{'X-Fieldstation':'private','X-Private-Token':token},cache:'no-store'});
   if(!response.ok)return;
   const blob=await response.blob();
   if(token!==privateToken||!button.isConnected)return;
   url=privateThumbs.get(path);
   if(!url){if(privateThumbs.size>=128){const oldest=privateThumbs.keys().next().value;URL.revokeObjectURL(privateThumbs.get(oldest));privateThumbs.delete(oldest);}url=URL.createObjectURL(blob);privateThumbs.set(path,url);}
  }
  if(token!==privateToken||!button.isConnected)return;
  img.src=url;img.hidden=false;
 }catch{}
}
