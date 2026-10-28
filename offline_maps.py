"""Local map files and bounded, local-only BRouter requests."""
import json, math, os, threading, sqlite3, re
from contextlib import closing
from pathlib import Path
from urllib.parse import unquote, urlencode
from urllib.request import urlopen

ROOT = Path(os.environ.get('FIELD_MAPS', '/media/library/Maps'))
LOCK = threading.Lock()
PLACES = None

def address_search(query,lon=None,lat=None):
    db=ROOT/'addresses.sqlite3'
    if not db.is_file():return []
    aliases={'rd':'road','st':'street','ave':'avenue','jln':'jalan','lor':'lorong','blk':'block'}
    tokens=[aliases.get(t,t) for t in re.findall(r'\w+',query.casefold())][:16]
    if len(tokens)>2:tokens=[t for t in tokens if t not in {'singapore','malaysia'}]
    if not tokens:return []
    match=' AND '.join('"'+t+'"*' for t in tokens)
    with closing(sqlite3.connect(f'file:{db}?mode=ro',uri=True)) as c:
        rows=c.execute('SELECT p.name,p.context,p.kind,p.number,p.lon,p.lat,bm25(search) FROM search JOIN places p ON p.id=search.rowid WHERE search MATCH ? ORDER BY bm25(search) LIMIT 300',(match,)).fetchall()
    def rank(r):
        distance=(r[4]-lon)**2+(r[5]-lat)**2 if lon is not None and lat is not None else 0
        number_ok=not any(t[0].isdigit() for t in tokens) or r[3].casefold() in tokens
        return (not number_ok,r[0].casefold()!=query.casefold(),distance,r[6])
    rows.sort(key=rank);seen=set();out=[]
    for name,context,kind,number,x,y,_ in rows:
        key=(name.casefold(),context.casefold(),round(x,2),round(y,2))
        if key in seen:continue
        seen.add(key);out.append(dict(name=name,context=context,kind=kind,country=context or kind,lon=x,lat=y))
        if len(out)==12:break
    return out

def search(query,lon=None,lat=None):
    global PLACES
    if PLACES is None:
        try: PLACES=json.loads((ROOT/'places.json').read_text())
        except (OSError,ValueError): PLACES=[]
    query=query.strip().casefold()[:100]
    if len(query)<2:return []
    addresses=address_search(query,lon,lat)
    matches=[p for p in PLACES if query in p['search']]
    matches.sort(key=lambda p:(p['name'].casefold()!=query,not p['name'].casefold().startswith(query),-p['population']))
    places=[{k:v for k,v in p.items() if k not in ('search','population')} for p in matches[:12]]
    exact=[p for p in places if p['name'].casefold()==query]
    return (exact[:2]+addresses+places)[:16]

def manifest():
    try: data = json.loads((ROOT/'manifest.json').read_text())
    except (OSError, ValueError): data = {'regions': []}
    data['regions'] = [r for r in data['regions'] if (ROOT/(r['id']+'.pmtiles')).is_file()]
    try: data['download'] = json.loads((ROOT/'download-status.json').read_text())['message']
    except (OSError, ValueError, KeyError): data['download'] = 'No map downloads found.'
    data['routing'] = (ROOT/'routing-ready.json').is_file()
    return data

def file_path(route):
    rel = Path(unquote(route.removeprefix('/map-data/')))
    if rel.is_absolute() or '..' in rel.parts: return None
    p = (ROOT/rel).resolve()
    if not p.is_relative_to(ROOT.resolve()): return None
    allowed = rel.parts and rel.parts[0] == 'assets' and p.suffix in {'.js','.css','.pbf','.png','.json'}
    if len(rel.parts)==1 and rel.name in {r['id']+'.pmtiles' for r in manifest()['regions']}: allowed=True
    return p if allowed and p.is_file() else None

def route(params):
    profile = params.get('profile', ['car-fast'])[0]
    if profile not in {'car-fast','trekking','walking'}: raise ValueError('Unknown travel mode.')
    points = params.get('points',[''])[0].split('|')
    if len(points)!=2: raise ValueError('Choose a start and destination.')
    normalized=[]
    for point in points:
        pair=point.split(',')
        if len(pair)!=2: raise ValueError('Invalid coordinates.')
        lon,lat=map(float,pair)
        if not all(map(math.isfinite,(lon,lat))) or not (95<=lon<=120 and 0<=lat<10):
            raise ValueError('Offline routing covers Singapore and Malaysia only.')
        normalized.append(f'{lon:.6f},{lat:.6f}')
    if not LOCK.acquire(False): raise ValueError('A route is already being calculated. Try again shortly.')
    try:
        query=urlencode(dict(lonlats='|'.join(normalized),profile=profile,alternativeidx=0,format='geojson',timode=2))
        with urlopen('http://127.0.0.1:17777/brouter?'+query,timeout=125) as response:
            return json.loads(response.read(12_000_000))
    finally: LOCK.release()
