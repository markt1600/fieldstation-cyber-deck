"""Offline article suggestions. Topic pool is a saved Wikipedia Vital Articles list."""
import json,random,functools
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import urlopen
from urllib.parse import urljoin,urlparse
from concurrent.futures import ThreadPoolExecutor
ROOT='http://127.0.0.1:8080/kiwix/content/wikipedia_en_all_maxi_2026-08/'
class Images(HTMLParser):
    def __init__(self):super().__init__();self.images=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='img' and a.get('src') and int(a.get('width','0') or '0')>=100 and int(a.get('height','0') or '0')>=80:self.images.append(a['src'])
@functools.lru_cache(maxsize=1200)
def article(path):
    try:
        with urlopen(ROOT+path,timeout=4) as r:body=r.read(3000000).decode('utf-8','replace')
        parser=Images();parser.feed(body)
        for src in parser.images:
            url=urljoin(ROOT+path,src)
            if url.startswith(ROOT):return {'image':url[len(ROOT):]}
        return {'image':''}
    except Exception:return None
def suggestions():
    pool=json.loads((Path(__file__).parent/'data/wiki-topics.json').read_text())
    picks=random.sample(pool,min(18,len(pool)))
    with ThreadPoolExecutor(max_workers=6) as workers:results=list(workers.map(lambda b:article(b['path']),picks))
    return {'total':len(pool),'items':[{**b,**r} for b,r in zip(picks,results) if r is not None][:12]}
