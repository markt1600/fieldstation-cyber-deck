import urllib.request,zipfile,io,json,pathlib
places={}
for source in ['cities15000','SG','MY']:
 print('Downloading GeoNames '+source,flush=True)
 data=urllib.request.urlopen('https://download.geonames.org/export/dump/'+source+'.zip',timeout=120).read()
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  for line in z.read(source+'.txt').decode().splitlines():
   f=line.split('\t')
   if len(f)<19:continue
   places[f[0]]=dict(name=f[1],country=f[8],lon=float(f[5]),lat=float(f[4]),population=int(f[14] or 0),search=' '.join(f[1:4]).casefold())
root=pathlib.Path('/media/library/Maps');(root/'places.json').write_text(json.dumps(list(places.values()),ensure_ascii=False));print('Places',len(places))
(root/'places-attribution.txt').write_text('GeoNames geographical database, CC BY 4.0. https://www.geonames.org/ https://creativecommons.org/licenses/by/4.0/ Downloaded 2026-10-28')
