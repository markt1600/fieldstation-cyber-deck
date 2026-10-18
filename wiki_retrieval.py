"""Bounded retrieval from the local Wikipedia ZIM; never fetch the web."""
import re
from html.parser import HTMLParser
from urllib.parse import urlencode, quote, unquote
from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None

def fetch(path):
    opener=build_opener(ProxyHandler({}), NoRedirect())
    with opener.open('http://127.0.0.1:8080'+path,timeout=12) as response:
        raw=response.read(4_000_001)
    if len(raw)>4_000_000: raise ValueError('Article too large')
    return raw.decode('utf-8',errors='replace')

class Links(HTMLParser):
    def __init__(self,prefix):
        super().__init__();self.prefix=prefix;self.links=[];self.current=None;self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href','')
            if href.startswith(self.prefix) and not any(x in unquote(href[len(self.prefix):]) for x in (':','..','\\')):
                self.current=href;self.text=[]
    def handle_data(self,text):
        if self.current:self.text.append(text)
    def handle_endtag(self,tag):
        if tag=='a' and self.current:
            self.links.append((self.current,' '.join(''.join(self.text).split())))
            self.current=None

class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.current=None;self.skip=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','sup','table','nav'):self.skip.append(tag)
        if tag=='p' and not self.skip:self.current=[]
    def handle_endtag(self,tag):
        if tag=='p' and self.current is not None:
            text=' '.join(''.join(self.current).split())
            if len(text)>90:self.parts.append(text)
            self.current=None
        if self.skip and tag==self.skip[-1]:self.skip.pop()
    def handle_data(self,text):
        if self.current is not None and not self.skip:self.current.append(text)

def retrieve(words,files):
    archives=sorted((p for p in files.values() if p.name.startswith('wikipedia_en_') and p.suffix=='.zim' and p.is_file()),key=lambda p:p.name,reverse=True)
    if not archives:return [],'Wikipedia archive is not connected.'
    if not words:return [],'No Wikipedia search terms.'
    archive=archives[0].stem;prefix='/kiwix/content/'+quote(archive,safe='')+'/'
    try:
        links=Links(prefix)
        links.feed(fetch('/kiwix/search?'+urlencode({'content':archive,'pattern':' '.join(words[:8])})))
        results=[];seen=set()
        for path,title in links.links[:5]:
            if path in seen:continue
            seen.add(path)
            try:
                article=Paragraphs();article.feed(fetch(path))
            except (OSError,ValueError):continue
            # Rank paragraphs by query coverage; preserve article order for readability.
            ranked=sorted(enumerate(article.parts),key=lambda pair:(-sum(w in re.findall(r'\w+',pair[1].lower()) for w in words),pair[0]))[:2]
            excerpt='\n\n'.join(p for _,p in sorted(ranked))[:1800]
            if not excerpt:continue
            results.append({'title':title,'kind':'wikipedia','archive':archive,'articlePath':path[len(prefix):], 'url':path,'excerpt':excerpt,'label':'Wikipedia · '+archive.rsplit('_',1)[-1]})
            if len(results)==2:break
        return results, 'Wikipedia searched locally.' if results else 'No matching Wikipedia articles found.'
    except (OSError,ValueError):return [],'Wikipedia search unavailable. Start Kiwix to include it; PDF search still works.'
