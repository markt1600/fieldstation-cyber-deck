"""Fixed, local-only terminal launcher. No caller-supplied commands."""
import os,subprocess,threading,time
from pathlib import Path
BIN=Path.home()/'.local/bin/codex'
LOCK=threading.Lock()
last_launch=0
def status():
 return {'installed':BIN.is_file(),'interface':'terminal','internet_required':True}
def launch():
 global last_launch
 if not BIN.is_file():raise RuntimeError('Codex is not installed.')
 if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):raise RuntimeError('The Pi desktop session is unavailable.')
 with LOCK:
  if time.monotonic()-last_launch<5:return {'message':'Codex launch already requested.'}
  subprocess.Popen(['/usr/bin/x-terminal-emulator','-e',str(BIN),'-C',str(Path(__file__).resolve().parent)],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
  last_launch=time.monotonic()
 return {'message':'Codex opened in a terminal. Complete sign-in there, then type your request. Close the terminal to return here.'}
