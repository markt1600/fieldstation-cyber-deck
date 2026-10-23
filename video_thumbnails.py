"""Small, local frame previews for public videos only (caller validates paths)."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import threading
from io import BytesIO

PRIVATE_IMAGES = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

CACHE = Path(__file__).parent / 'data/video-thumbnails'
LOCK = threading.Lock()
FAILED = set()

def private_preview(path):
    """Return a frame in memory only; never write private media to the disk cache."""
    if path.suffix.lower() in PRIVATE_IMAGES:
        from PIL import Image, ImageOps
        with LOCK, Image.open(path) as source:
            source.seek(0)
            preview = ImageOps.exif_transpose(source)
            preview.thumbnail((480, 320))
            if preview.mode != 'RGB':
                preview = preview.convert('RGB')
            output = BytesIO()
            preview.save(output, format='JPEG', quality=82)
            return output.getvalue()
    exe=shutil.which('ffmpeg')
    if not exe: raise RuntimeError('Video previews require ffmpeg.')
    with LOCK:
        for position in ('10','0'):
            result=subprocess.run([exe,'-nostdin','-loglevel','quiet','-threads','1',
                '-ss',position,'-i',str(path),'-map','0:v:0','-frames:v','1',
                '-vf','scale=320:180:force_original_aspect_ratio=decrease',
                '-threads','1','-f','image2pipe','-vcodec','mjpeg','pipe:1'],
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=12)
            if result.returncode==0 and result.stdout.startswith(b'\xff\xd8'):
                return result.stdout
    raise ValueError('No video preview available.')

def thumbnail(path):
    stat = path.stat()
    key = hashlib.sha256(f'{path}:{stat.st_size}:{stat.st_mtime_ns}'.encode()).hexdigest()
    target = CACHE / (key + '.jpg')
    if target.is_file(): return target
    exe = shutil.which('ffmpeg')
    if not exe or key in FAILED: return None
    with LOCK:
        if target.is_file(): return target
        if key in FAILED: return None
        CACHE.mkdir(parents=True, exist_ok=True)
        temp = CACHE / (key + '.tmp.jpg')
        try:
            artwork = None
            probe = shutil.which('ffprobe')
            if probe:
                info = subprocess.run([probe, '-v', 'error', '-show_streams', '-of', 'json', str(path)], capture_output=True, text=True, timeout=10)
                if info.returncode == 0:
                    streams = json.loads(info.stdout).get('streams', [])
                    artwork = next((s['index'] for s in streams if s.get('disposition', {}).get('attached_pic')), None)
            attempts = [('0', f'0:{artwork}')] if artwork is not None else []
            attempts += [('10', '0:v:0'), ('0', '0:v:0')]
            for position, stream in attempts:
                result = subprocess.run([exe, '-nostdin', '-loglevel', 'error', '-y',
                    '-threads', '1', '-ss', position, '-i', str(path), '-map', stream,
                    '-frames:v', '1', '-vf', 'scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2',
                    '-threads', '1', '-q:v', '5', str(temp)],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
                if result.returncode == 0 and temp.exists() and temp.stat().st_size:
                    temp.replace(target)
                    return target
        except (OSError, subprocess.TimeoutExpired):
            pass
        finally:
            temp.unlink(missing_ok=True)
        FAILED.add(key)
        return None
