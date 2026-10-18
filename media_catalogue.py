"""Incremental media tags; no network metadata lookups."""
import json, sqlite3
from contextlib import closing
from pathlib import Path
DB=Path(__file__).parent/'data'/'media.sqlite3'
AUDIO={'.mp3','.m4a','.ogg','.wav','.flac'}
_cache={}
def metadata(path):
    stamp=f'{path.stat().st_size}:{path.stat().st_mtime_ns}'
    if path.suffix.lower() in {'.mp4','.m4v','.mov'}:stamp+=':video-tags-v1'
    cached=_cache.get(str(path))
    if cached and cached[0]==stamp:return cached[1]
    DB.parent.mkdir(exist_ok=True)
    with closing(sqlite3.connect(DB)) as c, c:
        c.execute('CREATE TABLE IF NOT EXISTS tags(path TEXT PRIMARY KEY,stamp TEXT,data TEXT)')
        row=c.execute('SELECT stamp,data FROM tags WHERE path=?',(str(path),)).fetchone()
        if row and row[0]==stamp:
            result=json.loads(row[1]);_cache[str(path)]=(stamp,result);return result
        result={}
        if path.suffix.lower() in AUDIO:
            try:
                from mutagen import File
                f=File(path,easy=True)
                if f is not None:
                    for key in ('title','artist','album','genre','tracknumber'):
                        values=f.get(key,[]) if f.tags else []
                        if not values and f.tags:
                            frame=f.tags.get({'title':'TIT2','artist':'TPE1','album':'TALB','genre':'TCON','tracknumber':'TRCK'}[key])
                            values=getattr(frame,'text',[])
                        if values:result[key]=str(values[0])
                    result['duration']=round(f.info.length,1)
            except Exception:pass
        if path.suffix.lower() in {'.mp4','.m4v','.mov'}:
            try:
                from mutagen.mp4 import MP4
                video=MP4(path);tags=video.tags or {}
                for key,atom in [('title','\xa9nam'),('artist','\xa9ART'),('genre','\xa9gen'),('show','tvsh')]:
                    if tags.get(atom):result[key]=str(tags[atom][0])
                if tags.get('stik'):result['videoKind']={6:'music',9:'movie',10:'tv'}.get(tags['stik'][0],'')
                result['duration']=round(video.info.length,1)
            except Exception:pass
        c.execute('INSERT OR REPLACE INTO tags VALUES(?,?,?)',(str(path),stamp,json.dumps(result)))
        _cache[str(path)]=(stamp,result)
        return result
