"""Read-only VeraCrypt browsing; passwords are handled only by native VeraCrypt."""
import os, secrets, shutil, subprocess, threading
from pathlib import Path

VIDEO = {'.mp4','.mkv','.avi','.mov','.webm','.m4v'}
PREVIEW = {'.pdf','.jpg','.jpeg','.png','.gif','.webp','.bmp','.txt','.docx'}

class PrivateFiles:
    def __init__(self):
        self.container = os.environ.get('FIELD_CONTAINER', '')
        self.root = Path(os.environ.get('FIELD_PRIVATE_MOUNT', 'V:/' if os.name == 'nt' else str(Path.home()/'.local/share/fieldstation/private-mount')))
        self.token = None
        self.owned = False
        self.busy = False
        self.processes = []
        self.operation = threading.Lock()

    def executable(self):
        candidates = [os.environ.get('FIELD_VERACRYPT'), shutil.which('veracrypt')]
        if os.name == 'nt': candidates.append('C:/Program Files/VeraCrypt/VeraCrypt.exe')
        return next((str(p) for p in candidates if p and Path(p).is_file()), None)

    def mounted(self):
        return self.root.exists() if os.name == 'nt' else os.path.ismount(self.root)

    def status(self):
        if self.owned and not self.mounted(): self.owned=False; self.token=None
        return dict(unlocked=bool(self.owned and self.token), mounted=self.owned, busy=self.busy,
                    configured=bool(self.container), available=bool(self.executable()), token=self.token)

    def unlock(self, container=None):
        if not self.operation.acquire(False): raise ValueError('Another private-file operation is in progress.')
        self.busy=True
        try:
            if self.owned or self.mounted(): raise ValueError('Mount location is already in use. Eject the existing mount before unlocking.')
            exe=self.executable()
            if not exe: raise ValueError('Install VeraCrypt, or set FIELD_VERACRYPT to its executable path and restart.')
            p=Path(container or self.container).expanduser()
            if not (container or self.container) or not p.is_absolute() or not p.is_file(): raise ValueError('Enter the full path to an existing container file.')
            self.container=str(p.resolve())
            if os.name == 'nt':
                if str(self.root).replace('\\','/').rstrip('/') not in [c+':' for c in 'DEFGHIJKLMNOPQRSTUVWXYZ']:
                    raise ValueError('FIELD_PRIVATE_MOUNT must be a dedicated drive letter, e.g. V:/')
                # Wipe cache before mounting, as disabling caching does not erase old entries.
                wipe=subprocess.run([exe,'/q','/w'],timeout=30)
                if wipe.returncode: raise ValueError('VeraCrypt could not clear its password cache.')
                cmd=[exe,'/q','/v',self.container,'/l',str(self.root)[0],'/m','ro','/c','n','/h','n','/tryemptypass','n']
            else:
                if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')): raise ValueError('Start Fieldstation in the Pi desktop session for the password prompt.')
                self.root.mkdir(parents=True,exist_ok=True)
                if any(self.root.iterdir()): raise ValueError('Private mount directory must be empty.')
                cmd=[exe,'--mount','--mount-options=ro',self.container,str(self.root)]
            # Deliberately no password/PIM/keyfile arguments and no credential handling here.
            result=subprocess.run(cmd)
            if self.mounted(): self.owned=True
            if result.returncode or not self.owned: raise ValueError('Unlock cancelled or failed. Check VeraCrypt for details.')
            self.token=secrets.token_urlsafe(32)
            return self.status()
        finally: self.busy=False;self.operation.release()

    def authorize(self, token):
        self.status()
        if not self.token or not secrets.compare_digest(token or '',self.token): raise PermissionError('Private files are locked. Unlock again.')

    def path(self, rel, token):
        self.authorize(token)
        rel=Path(rel)
        if rel.is_absolute() or rel.drive or '..' in rel.parts: raise PermissionError('Invalid private path.')
        p=self.root/rel
        # Reject links/junctions rather than allowing paths outside the container.
        for candidate in [p,*p.parents]:
            if candidate==self.root.parent: break
            if candidate.is_symlink() or getattr(candidate,'is_junction',lambda:False)(): raise PermissionError('Links are not browsable.')
            if candidate==self.root: break
        if not p.resolve().is_relative_to(self.root.resolve()): raise PermissionError('Invalid private path.')
        return p

    def listing(self, rel, token):
        p=self.path(rel,token)
        if not p.is_dir(): raise ValueError('Folder unavailable.')
        items=[]
        for child in p.iterdir():
            if child.is_symlink() or getattr(child,'is_junction',lambda:False)(): continue
            if child.name.startswith('.') or child.name in {'System Volume Information','$RECYCLE.BIN'}: continue
            try: items.append(dict(name=child.name,path=child.relative_to(self.root).as_posix(),directory=child.is_dir(),size=child.stat().st_size if child.is_file() else 0,extension=child.suffix.lower()))
            except OSError: continue
        return sorted(items,key=lambda i:(not i['directory'],i['name'].casefold()))

    def eject(self):
        if not self.operation.acquire(False): raise ValueError('Finish or cancel the VeraCrypt password prompt first.')
        self.busy=True
        try:
            # Revoke all URLs/requests immediately, even if normal dismount subsequently fails.
            self.token=None
            for p in self.processes:
                if p.poll() is None:
                    p.terminate()
                    try:p.wait(timeout=5)
                    except subprocess.TimeoutExpired: pass
            self.processes=[]
            if not self.owned:return self.status()
            exe=self.executable()
            if not exe: raise ValueError('VeraCrypt unavailable. Dismount manually; browser access is blocked.')
            cmd=[exe,'/q','/d',str(self.root)[0]] if os.name=='nt' else [exe,'--dismount',str(self.root)]
            result=subprocess.run(cmd)
            if os.name=='nt':subprocess.run([exe,'/q','/w'],timeout=30)
            if self.mounted(): raise ValueError('Still mounted: close any external viewers, then press Eject again. Browser access is blocked.')
            self.owned=False
            if result.returncode: raise ValueError('Volume is no longer mounted, but VeraCrypt reported an error.')
            return self.status()
        finally:self.busy=False;self.operation.release()

PRIVATE=PrivateFiles()
