"""Explicitly requested AI refresh of category mixes; other playlists stay intact."""
import json, re, threading, time, uuid
from pathlib import Path
import playlist_ai, playlists

NAMES=['Pop','Rock','Hip-Hop & R&B','Jazz & Blues','Classical','Electronic & Ambient','Country & Folk','World & Asian','Soundtracks & Stage','Other Audio']
STATE=Path(__file__).parent/'data/category-playlists.json'
LOCK=threading.Lock()
active=False

def category(i):
    g=i.get('genre','').lower();context=' '.join(i.get(k,'') for k in ['artist','album','folder']).lower()
    for pattern,name in [(r'podcast|speech|audiobook|language|educational','Other Audio'),(r'soundtrack|musical|anime|film score|stage','Soundtracks & Stage'),(r'classical|baroque|symphon|opera|chamber','Classical')]:
        if re.search(pattern,g):return name
    if re.search(r'world|latin|reggae|hawai|c-pop|j-pop|k-pop|mandarin|cantopop|chinese|asian|bossa',g) or re.search(r'[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]',i.get('artist','')):return 'World & Asian'
    for pattern,name in [(r'jazz|blues|fusion','Jazz & Blues'),(r'hip.?hop|rap|r&b|soul|funk|rhythmic','Hip-Hop & R&B'),(r'country|folk|singer.songwriter|acoustic|bluegrass','Country & Folk'),(r'electro|dance|ambient|ambience|new age|trance|house|techno|goa|chill','Electronic & Ambient'),(r'rock|metal|punk|alternative|grunge|ska','Rock'),(r'pop|easy listening|disco|holiday','Pop')]:
        if re.search(pattern,g):return name
    return 'Classical' if re.search(r'bach|beethoven|mozart|vivaldi|chopin|ravel',context) else 'Other Audio'

def read():
    try:return json.loads(STATE.read_text())
    except (OSError,ValueError):return {'state':'idle','lists':{},'message':'Generate AI Top 10 playlists from your current library.'}

def save(s):
    STATE.parent.mkdir(parents=True,exist_ok=True)
    tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(s));tmp.replace(STATE)

def status():
    with LOCK:
        s=read()
        if s['state']=='running' and not active:s.update(state='interrupted',message='Generation was interrupted. Existing completed lists are saved; regenerate to finish.')
        return s

def start(items):
    global active
    tracks=[i for i in items if i.get('status')=='ready' and i.get('format') in playlist_ai.FORMATS and i.get('category') not in ('Languages','Education') and not i.get('name','').startswith('._')]
    if not tracks:raise ValueError('Wait for the music library scan to finish.')
    if not playlist_ai.BIN.is_file():raise ValueError('Codex is not installed.')
    with LOCK, playlist_ai.LOCK:
        if active or any(j['state']=='running' for j in playlist_ai.JOBS.values()):raise ValueError('An AI playlist job is already running.')
        token=uuid.uuid4().hex;playlist_ai.JOBS[token]={'state':'running','created':time.time()}
        s=read();s.update(state='running',message='Starting category Top 10s…',completed=0,total=len(NAMES),errors=[],started=time.time());save(s);active=True
    threading.Thread(target=generate,args=(tracks,token,s),daemon=True).start()
    return status()

def generate(tracks,token,s):
    global active
    try:
        original={p['id']:p for p in playlists.run()['playlists']}
        for name in NAMES:
            pool=[t for t in tracks if category(t)==name]
            s['message']='Curating '+name+'…'
            with LOCK:save(s)
            if pool:
                jid=uuid.uuid4().hex
                with playlist_ai.LOCK:playlist_ai.JOBS[jid]={'state':'running','created':time.time()}
                playlist_ai.generate(jid,'Top 10 best-known, widely loved songs in '+name+'. Prioritize recognizable classics and artist variety. Use at most two songs per artist; avoid duplicate versions and spoken recordings. This is editorial curation, not measured chart rankings.',10,pool)
                result=playlist_ai.status(jid)
                if result['state']=='ready':
                    payload={'action':'create','name':name+' — AI Top 10','tracks':[t['key'] for t in result['tracks']]}
                    old_id=s.setdefault('lists',{}).get(name,{}).get('id')
                    if old_id in original:payload.update(action='update',playlist=old_id,revision=original[old_id]['revision'])
                    try:
                        saved=playlists.run(payload);pid=old_id if payload['action']=='update' else saved['created_id']
                        s['lists'][name]={'id':pid,'count':len(payload['tracks']),'updated':time.time(),'explanation':result['explanation']}
                    except ValueError as e:s['errors'].append(name+': '+str(e))
                else:s['errors'].append(name+': '+result['message'])
                with playlist_ai.LOCK:playlist_ai.JOBS.pop(jid,None)
            else:s['errors'].append(name+': no available music')
            s['completed']+=1
            with LOCK:save(s)
        s.update(state='partial' if s['errors'] else 'complete',message='Category playlists refreshed.' if not s['errors'] else 'Finished with some categories unchanged. See details below.',finished=time.time())
    except Exception:
        s.update(state='error',message='Generation stopped. Completed lists are saved; try again.')
    finally:
        with LOCK:active=False;save(s)
        with playlist_ai.LOCK:playlist_ai.JOBS.pop(token,None)
