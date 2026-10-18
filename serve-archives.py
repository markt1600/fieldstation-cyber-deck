import os
from pathlib import Path
archives=sorted(str(p) for p in Path('/media/library/Offline Library').rglob('*.zim'))
if not archives: raise SystemExit('No archives found')
os.execv('/usr/bin/kiwix-serve',['kiwix-serve','--address=127.0.0.1','--port=8080','--urlRootLocation=/kiwix',*archives])
