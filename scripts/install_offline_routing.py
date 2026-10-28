import pathlib,json,urllib.request,subprocess,tarfile,zipfile,io,hashlib,os
root=pathlib.Path('/media/library/Maps');r=root/'routing';r.mkdir(exist_ok=True)
def get(u):return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Fieldstation'}),timeout=120).read()
def dl(url,p):
 if p.exists():return
 part=p.with_suffix(p.suffix+'.part');subprocess.run(['curl','-fL','--retry','5','-C','-','-o',str(part),url],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);part.replace(p)
print('Downloading ARM64 Java runtime',flush=True)
a=json.loads(get('https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=aarch64&image_type=jre&os=linux&vendor=eclipse'))[0]['binary']['package'];p=r/'jre.tar.gz';dl(a['link'],p);assert hashlib.sha256(p.read_bytes()).hexdigest()==a['checksum']
with tarfile.open(p) as t:t.extractall(r,filter='data')
java=next(r.glob('*/bin/java'));java.chmod(0o755)
print('Downloading BRouter 1.7.10',flush=True)
p=r/'brouter.zip';dl('https://github.com/abrensch/brouter/releases/download/v1.7.10/brouter-1.7.10.zip',p)
with zipfile.ZipFile(p) as z:
 for info in z.infolist():
  rel=pathlib.PurePosixPath(info.filename)
  if info.is_dir() or '..' in rel.parts or rel.is_absolute():continue
  target=r/str(rel);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(info))
jar=next(r.rglob('brouter*.jar'));profiles=next(r.rglob('car-fast.brf')).parent
# Derive a pedestrian profile from the bundled foot-routing template.
import re
walking=(profiles/'hiking-mountain.brf').read_text()
walking=re.sub(r'(assign\s+SAC_scale_limit\s+)3\b',r'\g<1>1',walking)
walking=re.sub(r'(assign\s+hiking_routes_preference\s+)0\.20\b',r'\g<1>0.0',walking)
(profiles/'walking.brf').write_text(walking)
segments=r/'segments4';segments.mkdir(exist_ok=True)
for lon in range(95,120,5):
 for lat in [0,5]:
  name=f'E{lon}_N{lat}.rd5';print('Downloading '+name,flush=True);dl('https://brouter.de/brouter/segments4/'+name,segments/name)
custom=r/'customprofiles';custom.mkdir(exist_ok=True)
unit=pathlib.Path.home()/'.config/systemd/user/fieldstation-routing.service'
unit.write_text(f'''[Unit]
Description=Fieldstation offline routing
After=default.target
[Service]
ExecStart={java} -Xmx768M -DmaxRunningTime=120 -cp {jar} btools.server.RouteServer {segments} {profiles} {custom} 17777 1 127.0.0.1
Restart=on-failure
RestartSec=5
[Install]
WantedBy=default.target
''')
subprocess.run(['systemctl','--user','daemon-reload'],check=True);subprocess.run(['systemctl','--user','enable','--now','fieldstation-routing'],check=True)
(root/'routing-ready.json').write_text(json.dumps({'engine':'BRouter 1.7.10','region':'Singapore and Malaysia','profiles':['car-fast','walking','trekking']}));print('Routing ready',flush=True)
