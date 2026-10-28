import json,urllib.request,pathlib,tarfile,zipfile,io,subprocess,hashlib,os,time
root=pathlib.Path('/media/library/Maps');root.mkdir(exist_ok=True)
assets=root/'assets';assets.mkdir(exist_ok=True)
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Fieldstation-offline-map-setup'})
 return urllib.request.urlopen(req,timeout=120).read()
def status(message):
 print(message,flush=True);(root/'download-status.json').write_text(json.dumps({'message':message,'updated':time.time()}))
def download(url,path):
 subprocess.run(['curl','-fL','--retry','5','-C','-','-o',str(path),url],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
status('Downloading map viewer assets')
for package,ver,files in [('maplibre-gl','5.6.2',{'dist/maplibre-gl.js':'maplibre.js','dist/maplibre-gl.css':'maplibre.css'}),('pmtiles','4.5.0',{'dist/pmtiles.js':'pmtiles.js'}),('@protomaps/basemaps','5.7.2',{'dist/basemaps.js':'basemaps.js'})]:
 meta=json.loads(get('https://registry.npmjs.org/'+package+'/'+ver));blob=get(meta['dist']['tarball'])
 digest=meta['dist']['integrity'];import base64
 assert base64.b64encode(hashlib.sha512(blob).digest()).decode()==digest.split('sha512-')[-1]
 with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as t:
  for source,target in files.items(): (assets/target).write_bytes(t.extractfile('package/'+source).read())
  for m in t.getmembers():
   if pathlib.PurePosixPath(m.name).name.lower().startswith('license') and m.isfile():(assets/(package.replace('/','-')+'-LICENSE')).write_bytes(t.extractfile(m).read())
status('Downloading offline label fonts and icons')
archive=root/'basemaps-assets.zip'
if not archive.exists():download('https://codeload.github.com/protomaps/basemaps-assets/zip/refs/heads/main',archive)
with zipfile.ZipFile(archive) as z:
 for info in z.infolist():
  rel=pathlib.PurePosixPath(*pathlib.PurePosixPath(info.filename).parts[1:])
  if info.is_dir() or '..' in rel.parts:continue
  if str(rel).startswith(('fonts/','sprites/')) or rel.name.lower().startswith('license'):
   p=assets/str(rel);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(info))
meta=json.loads(get('https://api.github.com/repos/protomaps/go-pmtiles/releases/tags/v1.31.2'))
a=next(a for a in meta['assets'] if a['name'].endswith('Linux_arm64.tar.gz'))
blob=get(a['browser_download_url']);assert 'sha256:'+hashlib.sha256(blob).hexdigest()==a['digest']
with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as t:
 m=next(m for m in t.getmembers() if pathlib.PurePosixPath(m.name).name=='pmtiles');(root/'pmtiles').write_bytes(t.extractfile(m).read());(root/'pmtiles').chmod(0o755)
builds=json.loads(get('https://build-metadata.protomaps.dev/builds.json'));build=sorted([b for b in builds if str(b['version']).startswith('4.')],key=lambda b:b['key'])[-1]
source='https://build.protomaps.com/'+build['key']
regions=[('world','World overview',8,None,[-180,-80,180,80]),('singapore-malaysia','Singapore & Malaysia',15,'98.8,0.5,119.6,7.8',[98.8,0.5,119.6,7.8]),('southeast-asia','Southeast Asia',12,'92,-11,142,29',[92,-11,142,29])]
manifest={'source':source,'downloaded':time.strftime('%Y-%m-%d'),'regions':[]}
for key,name,zoom,bbox,bounds in regions:
 status('Downloading '+name+' (zoom '+str(zoom)+')')
 p=root/(key+'.pmtiles');part=root/(key+'.partial.pmtiles')
 if not p.exists():
  if part.exists():part.unlink()
  cmd=[str(root/'pmtiles'),'extract',source,str(part),'--maxzoom='+str(zoom),'--download-threads=4']
  if bbox:cmd+=['--bbox='+bbox]
  subprocess.run(cmd,check=True);subprocess.run([str(root/'pmtiles'),'verify',str(part)],check=True);part.rename(p)
 manifest['regions'].append(dict(id=key,name=name,maxzoom=zoom,bounds=bounds,bytes=p.stat().st_size))
 (root/'manifest.json.tmp').write_text(json.dumps(manifest));(root/'manifest.json.tmp').replace(root/'manifest.json')
status('Map downloads complete')
