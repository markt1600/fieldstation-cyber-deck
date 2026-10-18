let sharedArticlePath='';
window.addEventListener('message',event=>{
 const frame=document.querySelector('#kiwix-frame iframe');
 if(!frame||event.source!==frame.contentWindow||event.origin!=='http://'+location.hostname+':8766')return;
 if(event.data?.type==='fieldstation-page'&&typeof event.data.path==='string'&&event.data.path.startsWith('/kiwix/'))sharedArticlePath=event.data.path;
});
async function sharePublic(path,host=''){
 const dialog=document.querySelector('#share-dialog'),body=document.querySelector('#share-body');if(!dialog.open)dialog.showModal();body.textContent='Preparing QR code…';
 try{const r=await fetch('/api/share?'+new URLSearchParams({path,host}));const value=await r.json();if(!r.ok)throw Error(value.error);
 body.replaceChildren();const note=document.createElement('p');note.textContent='Connect the phone or tablet to the same Wi-Fi or Pi hotspot, then scan. Anyone on this local network can access the public library; private files and device controls are not shared.';body.append(note);
 const qr=document.createElement('div');qr.className='share-qr';qr.innerHTML=value.svg;body.append(qr);
 const link=document.createElement('a');link.href=value.url;link.textContent=value.url;link.style.overflowWrap='anywhere';body.append(link);
 if(value.addresses.length>1){const label=document.createElement('label');label.textContent='Network address (choose your Wi-Fi/Ethernet address):';const select=document.createElement('select');for(const address of value.addresses){const option=document.createElement('option');option.value=address;option.textContent=address;select.append(option);}select.value=value.host;select.onchange=()=>sharePublic(path,select.value);label.append(select);body.append(label);}
 const help=document.createElement('p');help.textContent='If it cannot connect, check the selected address, guest-network isolation and the firewall. Sharing needs TCP port 8766 on your private network.';body.append(help);
 }catch(e){body.textContent=e.message;}
}
document.querySelector('#share-close').onclick=()=>document.querySelector('#share-dialog').close();
document.querySelector('#share-article').onclick=()=>sharePublic(sharedArticlePath);
function addShareLinks(){
 document.querySelectorAll('[data-open]').forEach(open=>{if(open.dataset.shareAdded)return;const item=data.items.find(i=>i.id===open.dataset.open);if(!item||!['PDF','EPUB'].includes(item.format))return;open.dataset.shareAdded='1';const button=document.createElement('button');button.className='action';button.textContent='Share QR';button.onclick=()=>sharePublic('/shared?'+new URLSearchParams({id:item.id,page:'1'}));open.after(button);});
 document.querySelectorAll('main a[href^="/content/"],#viewer-body a[href^="/content/"]').forEach(link=>{
  if(link.dataset.shareAdded)return;link.dataset.shareAdded='1';
  const url=new URL(link.href),id=url.pathname.split('/').pop();const page=new URLSearchParams(url.hash.slice(1)).get('page')||'1';
  const button=document.createElement('button');button.className='action';button.textContent='Share QR';button.onclick=()=>sharePublic('/shared?'+new URLSearchParams({id,page}));link.after(button);
 });
}
new MutationObserver(addShareLinks).observe(document.body,{childList:true,subtree:true});
