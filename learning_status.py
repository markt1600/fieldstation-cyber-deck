"""Cached progress of the SSD-backed Khan Academy import."""
from pathlib import Path
import sqlite3, subprocess, threading, time
HOME=Path('/media/library/Education/Kolibri')
_cache={};_when=0;_lock=threading.Lock()
def status():
    global _cache,_when
    with _lock:
        if time.monotonic()-_when<30 and _cache:return _cache
        result={'total_bytes':66933846231,'stored_bytes':0,'state':'unavailable'}
        run=subprocess.run(['systemctl','--user','is-active','fieldstation-khan-download'],capture_output=True,text=True,timeout=5)
        result['state']='downloading' if run.stdout.strip() in {'active','activating'} else 'idle'
        folder=HOME/'content/storage'
        if folder.is_dir():
            size=subprocess.run(['du','-sb',str(folder)],capture_output=True,text=True,timeout=10)
            if size.returncode==0:result['stored_bytes']=int(size.stdout.split()[0])
        result['path']=str(HOME)
        _cache=result;_when=time.monotonic();return result
