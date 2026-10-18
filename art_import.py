"""Resumable, rights-filtered offline museum collection importer."""
import concurrent.futures, hashlib, html, io, json, os, re, shutil, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image
ROOT=Path('/media/library/Art'); TARGET=3000

def atomic(path,data):
    tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8'); tmp.replace(path)
def get(url):
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'FieldstationOfflineGallery/1.0 (personal educational collection)'})
            with urllib.request.urlopen(req,timeout=45) as r:return r.read(25000000)
        except Exception:
            if attempt==3:raise
            time.sleep(2**attempt)
def clean(s):return html.unescape(re.sub('<[^>]+>',' ',s or '')).strip()
def themes(w):
    text=' '.join([w['title'],w['medium'],w['culture'],w['type'],' '.join(w['tags'])]).lower()
    groups={
      'Landscapes & nature':r'landscape|mountain|river|garden|tree|forest|flower|nature|water lil',
      'People & portraits':r'portrait|woman|women|man\b|men\b|child|family|figure|people',
      'Cities & everyday life':r'city|cities|street|paris|chicago|interior|market|village|house|bedroom',
      'Sea & sky':r'sea\b|ocean|wave|coast|boat|ship|sky|cloud|sunset',
      'Faith & mythology':r'buddha|christ|virgin|saint|god|deity|myth|religio|temple|sacred',
      'Animals':r'animal|bird|horse|lion|tiger|cat\b|dog\b|fish',
      'Still life':r'still life|fruit|vase|bouquet',
      'Photography':r'photograph|gelatin|albumen|daguerreotype',
      'Asian art':r'japan|chin[ae]|korea|india|tibet|nepal|asia|indonesia|thailand|cambodia',
      'African art':r'africa|congo|yoruba|benin|nigeria|egypt',
      'Sculpture & objects':r'sculpture|bronze|ceramic|vessel|textile|carving|mask|pottery|furniture|jewel',
      'Prints & drawings':r'print|drawing|etching|woodblock|lithograph|engraving',
      'Paintings':r'painting|oil on|watercolor|watercolour|tempera',
    }
    out=[k for k,v in groups.items() if re.search(v,text)]
    if w['highlight']:out.insert(0,'Museum highlights')
    return out or ['Across the collection']
def aic(d):
    if not d.get('is_public_domain') or not d.get('image_id'):return
    return dict(id='aic-'+str(d['id']),title=d['title'],artist=d.get('artist_title') or 'Artist not recorded',artist_info=d.get('artist_display') or '',biography='',date=d.get('date_display') or '',year=d.get('date_start'),medium=d.get('medium_display') or '',culture=d.get('place_of_origin') or '',type=d.get('artwork_type_title') or '',tags=(d.get('subject_titles') or [])+(d.get('style_titles') or []),description=clean(d.get('description')),credit=d.get('credit_line') or '',dimensions=d.get('dimensions') or '',highlight=bool(d.get('is_boosted')),museum='Art Institute of Chicago',source='https://www.artic.edu/artworks/'+str(d['id']),license='Image: public domain / CC0. Description: Art Institute of Chicago, CC BY 4.0 (HTML formatting removed).',image_source='https://www.artic.edu/iiif/2/'+d['image_id']+'/full/!1400,1400/0/default.jpg')
def cma(d):
    if d.get('share_license_status')!='CC0' or not d.get('images',{}).get('web'):return
    creators=d.get('creators') or []; info='; '.join(x['description'] for x in creators)
    return dict(id='cma-'+str(d['id']),title=d['title'],artist='; '.join(x['description'].split(' (')[0] for x in creators) or 'Artist not recorded',artist_info=info or ', '.join(d.get('culture') or []),biography=clean('\n\n'.join(x.get('biography') or '' for x in creators)),date=d.get('creation_date') or '',year=d.get('creation_date_earliest'),medium=d.get('technique') or '',culture=', '.join(d.get('culture') or []),type=d.get('type') or '',tags=[d.get('department') or '',d.get('collection') or ''],description=clean(d.get('description')),fact=clean(d.get('did_you_know')),credit=d.get('creditline') or '',dimensions=d.get('measurements') or '',highlight=bool(d.get('is_highlight')),museum='Cleveland Museum of Art',source=d['url'],license='Image and museum metadata: CC0, Cleveland Museum of Art.',image_source=d['images']['web']['url'])
def metadata(url):
    folder=ROOT/'metadata';folder.mkdir(exist_ok=True);p=folder/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if p.exists():return json.loads(p.read_text())
    d=json.loads(get(url));atomic(p,d);return d

def candidates():
    cache=ROOT/'candidates.json'
    if cache.exists():return json.loads(cache.read_text())
    pool={}
    def add(w):
        if w and w['id'] not in pool:
            w['topics']=themes(w);pool[w['id']]=w
    fields='id,title,image_id,is_public_domain,is_boosted,artist_title,artist_display,date_display,date_start,medium_display,place_of_origin,artwork_type_title,subject_titles,style_titles,description,credit_line,dimensions'
    for page in range(1,11):
        q={'query':{'term':{'is_public_domain':True}},'limit':100,'page':page,'fields':fields.split(',')}
        data=metadata('https://api.artic.edu/api/v1/artworks/search?params='+urllib.parse.quote(json.dumps(q)))
        for d in data['data']:add(aic(d))
        print('AIC metadata',page,len(pool),flush=True);time.sleep(.2)
    # Diversify beyond the popular Western paintings; retain museum-selected highlights first.
    for filt in [{'highlight':1,'limit':400},{'type':'Photograph','limit':450},{'department':'Chinese Art','limit':250},{'department':'Japanese Art','limit':250},{'department':'Indian and Southeast Asian Art','limit':150},{'department':'African Art','limit':150},{'department':'Egyptian and Ancient Near Eastern Art','limit':150},{'type':'Painting','limit':700},{'type':'Sculpture','limit':300},{'type':'Print','limit':1000}]:
        url='https://openaccess-api.clevelandart.org/api/artworks/?'+urllib.parse.urlencode(dict(cc0=1,has_image=1,**filt))
        data=metadata(url)
        for d in data['data']:add(cma(d))
        print('CMA metadata',filt,len(pool),flush=True);time.sleep(.3)
    # Highlights first, then round-robin topics to keep photography and world art represented.
    items=list(pool.values()); ordered=[x for x in items if x['highlight']];seen={x['id'] for x in ordered}
    buckets=[[x for x in items if t in x['topics'] and x['id'] not in seen] for t in ['Photography','Asian art','African art','Paintings','Prints & drawings','Sculpture & objects','Landscapes & nature','People & portraits']]
    while any(buckets):
        for bucket in buckets:
            while bucket and bucket[0]['id'] in seen:bucket.pop(0)
            if bucket:
                x=bucket.pop(0);ordered.append(x);seen.add(x['id'])
    ordered.extend(x for x in items if x['id'] not in seen);atomic(cache,ordered);return ordered

def download(w):
    path=ROOT/'images'/(w['id']+'.jpg');thumb=ROOT/'thumbs'/(w['id']+'.jpg')
    if not path.exists() or not thumb.exists():
        blob=get(w['image_source'])
        with Image.open(io.BytesIO(blob)) as im:
            im.load();im=im.convert('RGB');im.thumbnail((1600,1600))
            tmp=path.with_suffix('.tmp');im.save(tmp,'JPEG',quality=90);tmp.replace(path)
            im.thumbnail((400,400));tmp=thumb.with_suffix('.tmp');im.save(tmp,'JPEG',quality=83);tmp.replace(thumb)
    return dict(w,image='/art-image/'+w['id']+'.jpg',thumbnail='/art-thumb/'+w['id']+'.jpg',sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def main():
    if not Path('/media/library').is_mount():raise RuntimeError('Internal library drive is not mounted')
    if shutil.disk_usage('/media/library').free<5*1024**3:raise RuntimeError('Less than 5 GB free')
    ROOT.mkdir(exist_ok=True);(ROOT/'images').mkdir(exist_ok=True);(ROOT/'thumbs').mkdir(exist_ok=True)
    status=ROOT/'status.json';atomic(status,dict(state='Preparing museum catalogue',target=TARGET,downloaded=0,updated=time.time()))
    works=[w for w in candidates() if w['id'].startswith('cma-')];ready=[];fail=[]
    atomic(status,dict(state='Downloading',target=TARGET,downloaded=0,updated=time.time()))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for start in range(0,len(works),40):
            batch=works[start:start+min(40,TARGET-len(ready))]
            futures={pool.submit(download,w):w for w in batch}
            for f in concurrent.futures.as_completed(futures):
                try:ready.append(f.result())
                except Exception as e:fail.append(dict(id=futures[f]['id'],error=str(e)))
            ready.sort(key=lambda x:(not x['highlight'],x['artist'],x['title']))
            atomic(ROOT/'catalogue.json',ready);atomic(ROOT/'failures.json',fail)
            atomic(status,dict(state='Downloading',target=TARGET,downloaded=len(ready),failed=len(fail),updated=time.time()))
            print('Downloaded',len(ready),'failed',len(fail),flush=True)
            if len(ready)>=TARGET:break
    atomic(status,dict(state='Complete' if len(ready)>=TARGET else 'Incomplete',target=TARGET,downloaded=len(ready),failed=len(fail),updated=time.time()))
if __name__=='__main__':
    try:main()
    except Exception as e:
        atomic(ROOT/'status.json',dict(state='Import paused: '+str(e),target=TARGET,downloaded=len(json.loads((ROOT/'catalogue.json').read_text())) if (ROOT/'catalogue.json').exists() else 0,updated=time.time()))
        raise

