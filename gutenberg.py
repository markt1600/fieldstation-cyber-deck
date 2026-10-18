"""Search the saved Gutenberg catalogue; source classification, no inferred ages."""
import sqlite3
from urllib.request import urlopen
from urllib.parse import quote
from pathlib import Path
from contextlib import closing
TOPICS={'':'All topics','P':'Literature & languages','PZ':'Children’s literature','Q':'Science & mathematics','T':'Technology & practical skills','S':'Agriculture','R':'Health & medicine','G':'Geography & travel','H':'Society & economics','D':'World history','E':'American history','F':'Local American history','B':'Philosophy & religion','N':'Art','M':'Music','L':'Education','K':'Law','J':'Politics','U':'Military science','V':'Naval science','A':'General reference','Z':'Books & libraries'}
def query(params):
    term=params.get('q',[''])[0][:200];topic=params.get('topic',[''])[0];audience=params.get('audience',[''])[0];sort=params.get('sort',['popular'])[0]
    try:page=max(0,min(5000,int(params.get('page',['0'])[0])))
    except ValueError:page=0
    where=[];args=[]
    shuffle=params.get('shuffle',['0'])[0]=='1'
    if shuffle:where.append('id IN (SELECT id FROM books ORDER BY rank LIMIT 500)')
    if term:
        where.append('(title LIKE ? ESCAPE "!" OR author LIKE ? ESCAPE "!")');literal=term.replace('!','!!').replace('%','!%').replace('_','!_');args += ['%'+literal+'%']*2
    if topic in TOPICS and topic:where.append('class LIKE ?');args.append(topic+'%')
    if audience=='children':where.append("class='PZ'")
    clause=' WHERE '+' AND '.join(where) if where else ''
    order={'title':'title COLLATE NOCASE,rank','author':'author COLLATE NOCASE,title COLLATE NOCASE'}.get(sort,'rank')
    if shuffle:order='random()';page=0
    with closing(sqlite3.connect(Path(__file__).parent/'data/gutenberg.sqlite3')) as c:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='books'").fetchone():
            return {'books':[],'total':0,'page':page,'pageSize':30,'topics':TOPICS,'available':False}
        c.row_factory=sqlite3.Row
        total=c.execute('SELECT count(*) FROM books'+clause,args).fetchone()[0]
        rows=[dict(r) for r in c.execute('SELECT * FROM books'+clause+' ORDER BY '+order+' LIMIT 30 OFFSET ?',args+[page*30])]
    return {'books':rows,'total':total,'page':page,'pageSize':30,'topics':TOPICS,'shuffle':shuffle}

def book(uid):
    with closing(sqlite3.connect(Path(__file__).parent/'data/gutenberg.sqlite3')) as c:
        c.row_factory=sqlite3.Row
        row=c.execute('SELECT * FROM books WHERE id=?',(int(uid),)).fetchone()
    if not row:raise ValueError('Book not found')
    b=dict(row);path=quote(b['title'].replace('/','-')[:230]+'.'+str(b['id']),safe='')
    with urlopen('http://127.0.0.1:8080/kiwix/content/gutenberg_en_all_2025-11/'+path,timeout=15) as r:
        body=r.read(12000001)
    if len(body)>12000000:raise ValueError('This large book needs the original reader.')
    return {'title':b['title'],'path':path,'html':body.decode('utf-8','replace')}
