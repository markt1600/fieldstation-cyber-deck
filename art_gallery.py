"""Read-only offline art catalogue and safe image lookup."""
import json, random, re, threading
from collections import Counter
from pathlib import Path
ROOT=Path('/media/library/Art')
_lock=threading.Lock(); _stamp=None; _works=[]
def records():
    global _stamp,_works
    p=ROOT/'catalogue.json'
    try:stamp=p.stat().st_mtime_ns
    except OSError:return []
    with _lock:
        if stamp!=_stamp:
            _works=json.loads(p.read_text(encoding='utf-8'));_stamp=stamp
        return _works

def query(params):
    allworks=records();items=allworks
    val=lambda k:params.get(k,[''])[0]
    if val('id'):
        return {'work':next((x for x in items if x['id']==val('id')),None)}
    q=val('q').casefold().strip();topic=val('topic');artist=val('artist');museum=val('museum')
    if topic:items=[x for x in items if topic in x['topics']]
    if artist:items=[x for x in items if artist==x['artist']]
    if museum:items=[x for x in items if museum==x['museum']]
    if q:items=[x for x in items if q in ' '.join([x['title'],x['artist'],x['artist_info'],x['description'],x['medium'],x['culture'],*x['topics']]).casefold()]
    try:page=max(0,min(int(val('page') or 0),1000));seed=int(val('seed') or 0)
    except ValueError:page=seed=0
    sort=val('sort')
    if sort in ('','highlights'):
        names=['van Gogh','Monet','Rembrandt','Renoir','Degas','Cézanne','Gauguin','Turner','Caravaggio','Botticelli','Rodin','Hokusai','Hiroshige','Dürer','Goya','El Greco','Rubens','Manet','Matisse','Picasso','Stieglitz','Atget','Steichen','Weston']
        def rank(w):return next((i for i,n in enumerate(names) if n.casefold() in w['artist'].casefold()),len(names))
        items=sorted(items,key=lambda w:(not w.get('highlight'),rank(w),w['artist'],w['title']))
    if sort=='shuffle':items=list(items);random.Random(seed).shuffle(items)
    elif sort=='oldest':items=sorted(items,key=lambda x:x.get('year') if x.get('year') is not None else 9999)
    elif sort=='artist':items=sorted(items,key=lambda x:(x['artist'],x['title']))
    try:status=json.loads((ROOT/'status.json').read_text())
    except (OSError,ValueError):status={'state':'Not downloaded','downloaded':len(allworks),'target':3000}
    topics=Counter(t for x in allworks for t in x['topics']);artists=Counter(x['artist'] for x in allworks)
    covers={t:next(x['thumbnail'] for x in allworks if t in x['topics']) for t in topics}
    return dict(items=items[page*36:page*36+36],total=len(items),available=len(allworks),page=page,pageSize=36,status=status,topics=[dict(name=t,count=n,cover=covers[t]) for t,n in topics.most_common()],artists=[dict(name=a,count=n) for a,n in sorted(artists.items())],museums=sorted(set(x['museum'] for x in allworks)))

def image_path(name,thumbnail=False):
    if not re.fullmatch(r'(aic|cma)-\d+\.jpg',name):return None
    root=(ROOT/('thumbs' if thumbnail else 'images')).resolve();p=(root/name).resolve()
    return p if p.is_relative_to(root) and p.is_file() else None

def status():
    try:return json.loads((ROOT/"status.json").read_text())
    except (OSError,ValueError):return dict(state="Not downloaded",downloaded=0,target=3000)
