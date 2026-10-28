"""Build a local OSM street/address index; source stays on the SSD."""
import pathlib,subprocess,sys,sqlite3,json,re,time
root=pathlib.Path('/media/library/Maps');deps=root/'osmium-python'
if not (deps/'osmium').exists():subprocess.run([sys.executable,'-m','pip','install','--only-binary=:all:','--target',str(deps),'osmium==4.3.2'],check=True)
sys.path.insert(0,str(deps));import osmium
pbf=root/'malaysia-singapore-brunei.osm.pbf'
if not pbf.exists():
 part=pbf.with_suffix('.pbf.part');subprocess.run(['curl','-fL','--retry','5','-C','-','-o',str(part),'https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf'],check=True);part.rename(pbf)
db=root/'addresses.building.sqlite3'
if db.exists():db.unlink()
c=sqlite3.connect(db);c.execute('CREATE TABLE places (id INTEGER PRIMARY KEY,name TEXT,context TEXT,kind TEXT,number TEXT,lon REAL,lat REAL)');c.execute("CREATE VIRTUAL TABLE search USING fts5(text, tokenize='unicode61 remove_diacritics 2')")
def norm(s):
 pairs={'rd':'road','st':'street','ave':'avenue','jln':'jalan','lor':'lorong','blk':'block'}
 return ' '.join(pairs.get(t,t) for t in re.findall(r'\w+',s.casefold()))
count=0
class Handler(osmium.SimpleHandler):
 def useful(self,t):return any(k.startswith('addr:') for k in t) or ('name' in t and any(k in t for k in ['highway','building','amenity','shop','tourism','place']))
 def save(self,t,lon,lat):
  global count
  number=t.get('addr:housenumber','');street=t.get('addr:street',t.get('addr:place',''));address=t.get('addr:full','') or ' '.join(x for x in [number,street] if x)
  name=t.get('name',t.get('name:en',''));label=address or name
  if not label:return
  if address and name and name.casefold() not in address.casefold():label=name+' - '+address
  context=', '.join(dict.fromkeys(t[k] for k in ['addr:suburb','addr:city','addr:state','addr:postcode'] if t.get(k)))
  kind='address' if number or t.get('addr:full') else 'street' if t.get('highway') else 'place'
  count+=1;c.execute('INSERT INTO places VALUES (?,?,?,?,?,?,?)',(count,label,context,kind,number,lon,lat))
  words=' '.join(v for k,v in t.items() if k.startswith(('addr:','name','alt_name','official_name')))
  c.execute('INSERT INTO search(rowid,text) VALUES (?,?)',(count,norm(words)))
  if count%10000==0:c.commit();print('Indexed',count,flush=True)
 def node(self,n):
  if not n.tags:return
  t=dict(n.tags)
  if self.useful(t) and n.location.valid():self.save(t,n.location.lon,n.location.lat)
 def way(self,w):
  if not w.tags:return
  t=dict(w.tags)
  if not self.useful(t):return
  points=[n.location for n in w.nodes if n.location.valid()]
  if points:
   # A real node on the road/building outline, not a centroid in a different road.
   p=points[len(points)//2];self.save(t,p.lon,p.lat)
print('Indexing streets, addresses and landmarks',flush=True)
Handler().apply_file(str(pbf),locations=True,idx='flex_mem')
c.commit();c.execute("INSERT INTO search(search) VALUES('optimize')");c.commit();c.close();db.replace(root/'addresses.sqlite3');(root/'address-status.json').write_text(json.dumps({'records':count,'date':time.strftime('%Y-%m-%d'),'source':'Geofabrik / OpenStreetMap'}));print('Address index complete',count,flush=True)
