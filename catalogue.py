"""Local public-PDF catalogue. Incremental SQLite FTS5, one page per search hit."""
import json, os, re, sqlite3, threading, time
from contextlib import closing
from pathlib import Path

DB = Path(os.environ.get('FIELD_INDEX', str(Path(__file__).parent / 'data' / 'catalogue.sqlite3')))
STATE = {'running': False, 'current': '', 'error': ''}

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('CREATE TABLE IF NOT EXISTS books(id TEXT PRIMARY KEY, stamp TEXT, title TEXT, category TEXT, folder TEXT, pages INTEGER, toc TEXT, excerpt TEXT, status TEXT)')
    c.execute('CREATE VIRTUAL TABLE IF NOT EXISTS pages USING fts5(id UNINDEXED, page UNINDEXED, text, tokenize="unicode61")')
    return c

def index_once(items, files):
    from pypdf import PdfReader
    ready = {i['id']: i for i in items if i['format']=='PDF' and i['status']=='ready' and i['id'] in files}
    with closing(connect()) as c:
        for row in c.execute('SELECT id FROM books').fetchall():
            if row['id'] not in ready:
                c.execute('DELETE FROM pages WHERE id=?', (row['id'],))
                c.execute('DELETE FROM books WHERE id=?', (row['id'],))
        c.commit()
        for uid, item in ready.items():
            p = files[uid]
            stat = p.stat(); stamp = f'{stat.st_size}:{stat.st_mtime_ns}'
            old = c.execute('SELECT stamp FROM books WHERE id=?',(uid,)).fetchone()
            if old and old['stamp']==stamp: continue
            STATE['current'] = item['title']
            toc=[]; preview=[]; count=0; readable=0; status='indexed'
            try:
                reader=PdfReader(p)
                if reader.is_encrypted: raise ValueError('Encrypted PDF: excluded from text indexing')
                count=len(reader.pages)
                def outline(nodes, depth=0):
                    for node in nodes:
                        if isinstance(node,list): outline(node,depth+1)
                        else:
                            try:
                                n=reader.get_destination_page_number(node)
                                if n is not None and n>=0: toc.append({'title':str(node.title),'page':n+1,'depth':depth})
                            except Exception: pass
                outline(reader.outline)
                c.execute('DELETE FROM pages WHERE id=?',(uid,))
                for n,page in enumerate(reader.pages,1):
                    text=page.extract_text() or ''
                    if text.strip(): readable+=1
                    if n<=8 and text.strip(): preview.append(text)
                    c.execute('INSERT INTO pages(id,page,text) VALUES(?,?,?)',(uid,n,text))
                if not readable: status='needs OCR'
                elif readable<count: status=f'indexed; {count-readable} pages have no text'
                if p.stat().st_mtime_ns!=stat.st_mtime_ns: raise ValueError('File changed during indexing')
            except Exception as e:
                c.execute('DELETE FROM pages WHERE id=?',(uid,))
                status='unavailable: '+str(e)[:180]; stamp=''
            excerpt=re.sub(r'\s+',' ',' '.join(preview)).strip()[:1800]
            c.execute('INSERT OR REPLACE INTO books VALUES(?,?,?,?,?,?,?,?,?)',(uid,stamp,item['title'],item['category'],item['folder'],count,json.dumps(toc),excerpt,status))
            c.commit()
    STATE['current']=''

def start(inventory, files):
    def worker():
        while True:
            STATE.update(running=True,error='')
            try: index_once(list(inventory()),dict(files()))
            except Exception as e: STATE['error']=str(e)
            finally: STATE.update(running=False,current='')
            time.sleep(90)
    threading.Thread(target=worker,daemon=True,name='pdf-index').start()

def query(term='', uid='', category=''):
    with closing(connect()) as c:
        if uid:
            row=c.execute('SELECT * FROM books WHERE id=?',(uid,)).fetchone()
            if not row: return {'error':'This PDF is not indexed yet.'}
            result=dict(row); result['toc']=json.loads(result['toc']); return result
        books=[dict(r) for r in c.execute('SELECT id,title,category,folder,pages,status FROM books ORDER BY category,title')]
        if category:books=[b for b in books if b['category']==category]
        hits=[]
        # Quoting user terms treats punctuation as text, never FTS operators.
        words=re.findall(r'\w+',term[:300],re.UNICODE)[:16]
        if words:
            match=' AND '.join('"'+w+'"' for w in words)
            hits=[dict(r) for r in c.execute('SELECT pages.id,pages.page,books.title,books.category,snippet(pages,2,\'\',\'\',\' … \',36) AS excerpt FROM pages JOIN (SELECT id,title,category FROM books) AS books ON books.id=pages.id WHERE pages MATCH ? AND (? = \'\' OR books.category=?) ORDER BY bm25(pages) LIMIT 100',(match,category,category))]
        return {'books':books,'hits':hits,'state':dict(STATE),'query':term,'limit':100}
