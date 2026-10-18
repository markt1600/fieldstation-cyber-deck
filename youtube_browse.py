"""Read public YouTube search metadata; no account cookies or media downloads."""
import json,re,time,threading
from urllib.request import Request,urlopen
from urllib.parse import urlencode
_cache={};_lock=threading.Lock()
def search(query):
    query=query.strip()[:150] or 'science nature documentary'
    with _lock:cached=_cache.get(query)
    if cached and time.time()-cached[0]<300:return cached[1]
    req=Request('https://www.youtube.com/results?'+urlencode({'search_query':query,'hl':'en'}),headers={'User-Agent':'Mozilla/5.0','Accept-Language':'en-US,en;q=0.9'})
    with urlopen(req,timeout=15) as response:html=response.read(12000000).decode('utf-8','replace')
    match=re.search(r'(?:var\s+ytInitialData\s*=|window\["ytInitialData"\]\s*=)\s*',html)
    if not match:raise ValueError('YouTube search is unavailable. Check internet access and try again.')
    data=json.JSONDecoder().raw_decode(html[match.end():])[0];videos=[];seen=set()
    def text(node):return node.get('simpleText','') or ''.join(r.get('text','') for r in node.get('runs',[]))
    def walk(node):
        if isinstance(node,list):
            for child in node:walk(child)
        elif isinstance(node,dict):
            video=node.get('videoRenderer')
            if video:
                uid=video.get('videoId','')
                if re.fullmatch(r'[A-Za-z0-9_-]{11}',uid) and uid not in seen:
                    seen.add(uid);videos.append({'id':uid,'title':text(video.get('title',{})),'channel':text(video.get('ownerText',{})),'duration':text(video.get('lengthText',{})),'views':text(video.get('shortViewCountText',{}))})
            else:
                for child in node.values():walk(child)
    walk(data)
    if not videos:raise ValueError('No videos found. Try a different search; YouTube may also be temporarily unavailable.')
    result={'query':query,'videos':videos[:24]}
    with _lock:
        if len(_cache)>40:_cache.clear()
        _cache[query]=(time.time(),result)
    return result
