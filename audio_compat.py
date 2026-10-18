"""Lossless browser fallback cache; original media remains untouched."""
import hashlib
import subprocess
import threading
from pathlib import Path

CACHE = Path.home()/'.cache/fieldstation/audio-compatible'
_lock = threading.Lock()

def compatible(source):
    source = Path(source)
    if source.suffix.lower() != '.m4a':
        raise ValueError('Fallback supports M4A audio only')
    stat = source.stat()
    key = hashlib.sha256(f'{source.resolve()}:{stat.st_size}:{stat.st_mtime_ns}'.encode()).hexdigest()
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE/(key+'.flac')
    with _lock:
        if target.exists():
            return target
        partial = CACHE/(key+'.partial.flac')
        try:
            subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(source),
                            '-map','0:a:0','-vn','-c:a','flac',str(partial)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
            partial.replace(target)
        finally:
            partial.unlink(missing_ok=True)
    return target
