"""Persistent, device-local music playlists."""
import sqlite3,uuid,hashlib,json
from contextlib import closing
from pathlib import Path
DB=Path(__file__).parent/'data'/'playlists.sqlite3'
def revision(name,tracks):return hashlib.sha256(json.dumps([name,tracks],ensure_ascii=False).encode()).hexdigest()[:20]
def checked_tracks(value):
 if not isinstance(value,list) or len(value)>500 or any(not isinstance(x,str) or not 1<=len(x)<=1000 for x in value):raise ValueError('Use up to 500 valid tracks.')
 if len(set(value))!=len(value):raise ValueError('A track can only appear once in a playlist.')
 return value

def run(payload=None):
 with closing(sqlite3.connect(DB,timeout=10)) as c, c:
  c.execute('CREATE TABLE IF NOT EXISTS lists(id TEXT PRIMARY KEY,name TEXT NOT NULL)')
  c.execute('CREATE TABLE IF NOT EXISTS songs(list_id TEXT,track TEXT,PRIMARY KEY(list_id,track))')
  c.execute('CREATE TABLE IF NOT EXISTS video_categories(track TEXT PRIMARY KEY,category TEXT)')
  c.execute("INSERT OR IGNORE INTO lists VALUES('favorites','Favorites')")
  if payload:
   action=payload.get('action');pid=payload.get('playlist','');track=payload.get('track','')
   if action=='classify':
    category=payload.get('category','')
    if category not in ('','Movies','TV Shows','Documentaries','Music Videos & Concerts','Learning & How-to','News & Podcasts','Sports','Personal & Family','Bonus Features','Support Files & Incomplete Downloads','Uncategorized'):raise ValueError('Invalid category.')
    if not isinstance(track,str) or not 1<=len(track)<=1000:raise ValueError('Invalid video.')
    if category:c.execute('INSERT OR REPLACE INTO video_categories VALUES(?,?)',(track,category))
    else:c.execute('DELETE FROM video_categories WHERE track=?',(track,))
   elif action in ('update','delete'):
    row=c.execute('SELECT name FROM lists WHERE id=?',(pid,)).fetchone()
    if not row:raise ValueError('Playlist not found. Refresh the page.')
    old=[r[0] for r in c.execute('SELECT track FROM songs WHERE list_id=? ORDER BY rowid',(pid,))]
    if payload.get('revision')!=revision(row[0],old):raise ValueError('This playlist changed while you were editing. Reopen it before saving.')
    if action=='delete':
     if pid=='favorites':raise ValueError('Favorites is built in. You can remove its tracks instead.')
     c.execute('DELETE FROM songs WHERE list_id=?',(pid,));c.execute('DELETE FROM lists WHERE id=?',(pid,))
    else:
     name=str(payload.get('name','')).strip();tracks=checked_tracks(payload.get('tracks'))
     if not name or len(name)>80:raise ValueError('Use a playlist name of 1–80 characters.')
     c.execute('UPDATE lists SET name=? WHERE id=?',(name,pid));c.execute('DELETE FROM songs WHERE list_id=?',(pid,));c.executemany('INSERT INTO songs VALUES(?,?)',[(pid,t) for t in tracks])
   elif action=='create':
    name=str(payload.get('name','')).strip()
    if not name or len(name)>80:raise ValueError('Use a playlist name of 1–80 characters.')
    new_id=uuid.uuid4().hex;tracks=checked_tracks(payload.get('tracks',[]));c.execute('INSERT INTO lists VALUES(?,?)',(new_id,name));c.executemany('INSERT INTO songs VALUES(?,?)',[(new_id,t) for t in tracks])
   elif action in ('add','remove'):
    if not c.execute('SELECT 1 FROM lists WHERE id=?',(pid,)).fetchone():raise ValueError('Playlist not found.')
    if not isinstance(track,str) or not 1<=len(track)<=1000:raise ValueError('Invalid track.')
    if action=='add':c.execute('INSERT OR IGNORE INTO songs VALUES(?,?)',(pid,track))
    else:c.execute('DELETE FROM songs WHERE list_id=? AND track=?',(pid,track))
   else:raise ValueError('Unknown playlist action.')
  result={'videoOverrides':dict(c.execute('SELECT track,category FROM video_categories')),'playlists':[{'id':pid,'name':name,'tracks':[r[0] for r in c.execute('SELECT track FROM songs WHERE list_id=? ORDER BY rowid',(pid,))]} for pid,name in c.execute('SELECT id,name FROM lists ORDER BY rowid').fetchall()]}

  for p in result["playlists"]:p["revision"]=revision(p["name"],p["tracks"])
  if payload and payload.get("action")=="create":result["created_id"]=new_id
  return result
