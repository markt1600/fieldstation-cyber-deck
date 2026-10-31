"""Install additional offline games into the user-local game runtime."""
from pathlib import Path
import subprocess
import re
import sys
import shutil
packages = sys.argv[1:] or 'supertuxkart supertux frozen-bubble openttd openttd-opengfx openttd-opensfx hedgewars blobwars pioneers pioneers-console gtkatlantic monopd warzone2100 aisleriot ace-of-penguins gnome-mahjongg'.split()
base=Path.home()/'fieldstation-games'
cache=base/'packages-extra'; cache.mkdir(parents=True,exist_ok=True)
plan=subprocess.check_output(['apt-get','-s','install',*packages],text=True)
needed=re.findall(r'^Inst (\S+)',plan,re.M)
print('Downloading',len(needed),'packages',flush=True)
subprocess.run(['apt','download',*needed],cwd=cache,check=True)
for p in sorted(cache.glob('*.deb')):
    print('Extracting',p.name,flush=True)
    subprocess.run(['dpkg-deb','-x',str(p),str(base/'root')],check=True)
schemas=base/'root/usr/share/glib-2.0/schemas'
schemas.mkdir(parents=True,exist_ok=True)
for source in Path('/usr/share/glib-2.0/schemas').glob('*.xml'):
    if not (schemas/source.name).exists():shutil.copy2(source,schemas/source.name)
subprocess.run(['glib-compile-schemas',str(schemas)],check=True)
print('Installation complete',flush=True)
