"""Offline library browser. Python 3 standard library only."""
import argparse, hashlib, json, mimetypes, os, re, shutil, socket, time, subprocess
import zipfile, xml.etree.ElementTree as ET
import sys
from private_files import PRIVATE, PREVIEW
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'vendor'))
import catalogue
import ask_library
import playlists
import playlist_ai
import category_playlists
import threading
import media_catalogue
import topics
import video_thumbnails
import gutenberg
import youtube_browse
import discovery
import art_gallery
import wifi
import sharing
import air_quality
import battery_status
import audio_settings
import audio_compat
import codex_launcher
import power_control
import offline_maps
import games
import offline_tools
import kolibri_proxy
import learning_status
ALLOWED = {'.pdf', '.epub', '.zim', '.mp3', '.m4a', '.ogg', '.wav', '.mp4', '.webm', '.mkv', '.avi', '.mov', '.m4v', '.flac', '.html'}
CACHE = {'at': 0, 'items': [], 'files': {}}
VIDEO = {'.mp4', '.webm', '.mkv', '.avi', '.mov', '.m4v'}

def vlc_path():
    candidates = [os.environ.get('FIELD_VLC'), shutil.which('vlc')]
    if os.name == 'nt':
        candidates += [str(Path(os.environ.get(k, 'C:/Program Files')) / 'VideoLAN/VLC/vlc.exe') for k in ('ProgramFiles', 'ProgramFiles(x86)', 'LOCALAPPDATA')]
    return next((p for p in candidates if p and Path(p).is_file()), None)

def launch_video(uid):
    inventory()
    p = CACHE['files'].get(uid)
    if p is None: raise ValueError('Video unavailable or still downloading.')
    p = p.resolve()
    if not p.is_file() or p.suffix.lower() not in VIDEO or not any(p.is_relative_to(r.resolve()) for r in [ROOT, *media_roots()]):
        raise ValueError('Video unavailable.')
    return launch_vlc(p)

def launch_vlc(p):
    exe = vlc_path()
    if not exe: raise RuntimeError('VLC is not installed or could not be found. Install VLC, or set FIELD_VLC to its executable path and restart Fieldstation.')
    if os.name != 'nt' and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        raise RuntimeError('Start Fieldstation from the Pi desktop session so VLC can open a window.')
    if not p.is_file(): raise ValueError('Video file is unavailable.')
    # Public and private playback deliberately share this exact launch path.
    return subprocess.Popen([exe, '--intf=qt', '--no-fullscreen', '--no-start-paused', '--no-one-instance', '--no-qt-video-autoresize', '--no-qt-recentplay', '--width=800', '--height=450', '--', str(p)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def category(path, media=False):
    if media: return 'Movies'
    s = str(path).lower()
    if 'languages' in s: return 'Languages'
    if 'education' in s: return 'Education'
    if 'medical' in s: return 'Medical'
    if 'emergency' in s or 'practical' in s: return 'Practical'
    if 'wikipedia' in s: return 'Wikipedia'
    return 'Books'

def media_roots():
    configured=os.environ.get("FIELD_MEDIA_ROOTS")
    return [Path(p).resolve() for p in json.loads(configured)] if configured else [MEDIA, ROOT.parent/"Videos", ROOT.parent/"MP3s"]

SCAN_LOCK=threading.Lock()
SCAN_ERROR=""
def inventory():
    if time.time()-CACHE["at"]>60 and SCAN_LOCK.acquire(blocking=False):
        def refresh_inventory():
            global SCAN_ERROR
            try:
                _scan_inventory();SCAN_ERROR=""
            except Exception as e:SCAN_ERROR=str(e)
            finally:SCAN_LOCK.release()
        threading.Thread(target=refresh_inventory,daemon=True).start()
    return CACHE["items"]

def _scan_inventory():
    if time.time() - CACHE['at'] < 8: return CACHE['items']
    items, files, seen = [], {}, set()
    visited=set()
    titles = {}
    queue_file = ROOT / 'Education' / 'download-queue.json'
    try:
        queue = json.loads(queue_file.read_text(encoding='utf-8-sig'))
        for q in queue: titles[q['Name']] = q['Title']
    except (OSError, ValueError): queue = []
    try:
        extra=json.loads((ROOT / 'download-queue.json').read_text(encoding='utf-8-sig'))
        queue += extra
        for q in extra: titles[q['Name']]=q['Title']
    except (OSError,ValueError): pass
    for root, is_media in [(ROOT, False)]+[(r,True) for r in media_roots()]:
        if not root.is_dir(): continue
        for parent, dirs, names in os.walk(root):
            if Path(parent).resolve().is_relative_to(PRIVATE.root.resolve()): dirs[:]=[];continue
            dirs[:] = [d for d in dirs if not d.startswith('.') and not Path(parent, d).is_symlink() and not Path(parent,d).resolve().is_relative_to(PRIVATE.root.resolve())]
            for name in names:
                if name.startswith('.'): continue
                p = Path(parent, name)
                if PRIVATE.container and p.resolve() == Path(PRIVATE.container).resolve(): continue
                partial = name.endswith('.part')
                actual = name[:-5] if partial else name
                ext = Path(actual).suffix.lower()
                if ext not in ALLOWED or p.is_symlink(): continue
                try:
                    resolved = p.resolve()
                    if not resolved.is_relative_to(root.resolve()): continue
                    size = p.stat().st_size
                except OSError: continue
                if str(resolved) in visited: continue
                visited.add(str(resolved))
                uid = hashlib.sha256(str(resolved).encode()).hexdigest()[:20]
                title = titles.get(actual, Path(actual).stem.replace('_', ' '))
                title = {'wikipedia en all maxi 2026-08': 'Wikipedia · English with pictures', 'gutenberg en all 2025-11': 'Project Gutenberg · English books', 'phet mul all 2026-08': 'PhET · Interactive simulations', 'appropedia en all maxi 2026-02': 'Appropedia · Practical skills', 'mdwiki en all maxi 2025-11': 'MDWiki · Medical reference'}.get(title, title)
                item = dict(id=uid, title=title, name=actual, category=category(p, is_media), format=ext[1:].upper(), size=size, status='downloading' if partial else 'ready', folder=str(p.parent.relative_to(root)), url='/content/'+uid)
                if is_media:item['folder']=str(Path(root.name)/p.parent.relative_to(root))
                if not partial and (ext in media_catalogue.AUDIO or ext in VIDEO):
                    item.update(media_catalogue.metadata(p))
                    item['collection']=root.name if is_media else item['folder']
                items.append(item); seen.add(actual)
                if not partial: files[uid] = resolved
    for q in queue:
        if q['Name'] not in seen:
            items.append(dict(id=hashlib.sha256(q['Url'].encode()).hexdigest()[:20], title=q['Title'], name=q['Name'], category=category(Path(q['Folder']) if 'Size' in q else Path('Education') / q['Folder']), format=Path(q['Name']).suffix[1:].upper(), size=0, status='queued', folder=q['Folder'], url=None))
    items.sort(key=lambda x: (x['status'] != 'ready', x['title'].lower()))
    CACHE.update(at=time.time(), items=items, files=files)
    return items

def index_inventory():
    inventory()
    # The PDF worker must not mistake a pending initial scan for an empty drive.
    with SCAN_LOCK:
        return CACHE['items']

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def send_json(self, value, status=200):
        data = json.dumps(value).encode()
        self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    def do_PATCH(self):
        if self.path.startswith('/kolibri/'): return kolibri_proxy.serve(self)
        return self.send_json({'error':'Method not allowed.'},405)
    do_PUT = do_PATCH
    do_DELETE = do_PATCH
    def do_POST(self):
        if self.path.startswith('/kolibri/'): return kolibri_proxy.serve(self)
        if self.path in {'/api/tools/launch', '/api/tools/translate'}:
            host = self.headers.get('Host', '')
            if self.client_address[0] not in {'127.0.0.1','::1'} or host not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'} or self.headers.get('Origin') != 'http://' + host or self.headers.get('X-Fieldstation') != 'tools':
                return self.send_json({'error':'Open tools from Fieldstation on the Pi.'},403)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 16000: raise ValueError('Invalid request size.')
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict): raise ValueError('Invalid request.')
                result=offline_tools.launch(payload.get('app')) if self.path.endswith('/launch') else offline_tools.translate(payload)
                return self.send_json(result)
            except (ValueError,TypeError) as e: return self.send_json({'error':str(e)},400)
            except (RuntimeError,OSError,subprocess.TimeoutExpired) as e: return self.send_json({'error':str(e)},503)
        if self.path == '/api/games/launch':
            host = self.headers.get('Host', '')
            if self.client_address[0] not in {'127.0.0.1','::1'} or host not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'} or self.headers.get('Origin') != 'http://' + host or self.headers.get('X-Fieldstation') != 'games':
                return self.send_json({'error':'Launch games from Fieldstation on the Pi.'},403)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 128: raise ValueError('Invalid request.')
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict): raise ValueError('Invalid request.')
                return self.send_json(games.launch(payload.get('game')))
            except (ValueError,TypeError): return self.send_json({'error':'Choose a listed game.'},400)
            except (RuntimeError,OSError,subprocess.TimeoutExpired) as e: return self.send_json({'error':str(e)},503)
        if self.path == '/api/power':
            host = self.headers.get('Host', '')
            if self.client_address[0] not in {'127.0.0.1', '::1'} or host not in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'} or self.headers.get('Origin') != 'http://' + host or self.headers.get('X-Fieldstation') != 'power':
                return self.send_json({'error': 'Local same-origin request required.'}, 403)
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 256: raise ValueError('Invalid request size.')
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict): raise ValueError('Invalid request.')
                return self.send_json(power_control.request(payload.get('action')))
            except (ValueError, TypeError): return self.send_json({'error': 'Choose reboot or shutdown.'}, 400)
            except (RuntimeError, OSError, subprocess.TimeoutExpired) as e: return self.send_json({'error': str(e)}, 503)
        if self.path == '/api/codex/launch':
            host=self.headers.get('Host','')
            if host not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'} or self.headers.get('Origin')!='http://'+host or self.headers.get('X-Fieldstation')!='codex':
                return self.send_json({'error':'Local same-origin request required'},403)
            try:return self.send_json(codex_launcher.launch())
            except (RuntimeError,OSError) as e:return self.send_json({'error':str(e)},503)
        if urlparse(self.path).path == '/api/audio-settings':
            host=self.headers.get('Host','')
            if host not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'} or self.headers.get('Origin')!='http://'+host or self.headers.get('X-Fieldstation')!='audio':
                return self.send_json({'error':'Local same-origin request required.'},403)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 2048: raise ValueError('Invalid audio request size.')
                return self.send_json(audio_settings.save(json.loads(self.rfile.read(length))))
            except (ValueError,TypeError) as e: return self.send_json({'error':str(e)},400)
            except OSError: return self.send_json({'error':'Unable to save audio settings.'},503)
        if self.path == '/api/ask':
            host=self.headers.get('Host','')
            if host not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'} or self.headers.get('Origin')!='http://'+host or self.headers.get('X-Fieldstation')!='ask': return self.send_json({'error':'Local request required'},403)
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=4096: raise ValueError('Invalid request size')
                payload=json.loads(self.rfile.read(n))
                if not isinstance(payload,dict): raise ValueError('Invalid request')
                result=ask_library.answer(payload.get('question'),dict(CACHE['files']),payload.get('scope','all'))
                return self.send_json(result)
            except ValueError as e: return self.send_json({'error':str(e)},400)
            except Exception: return self.send_json({'error':'The local model could not complete this question. Check the runtime or try again.'},503)
        if self.path == '/api/rescan':
            host=self.headers.get('Host','')
            if host not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'} or self.headers.get('Origin')!='http://'+host or self.headers.get('X-Fieldstation')!='rescan':return self.send_json({'error':'Local request required'},403)
            CACHE['at']=0
            inventory()
            return self.send_json({'scanning':SCAN_LOCK.locked()})
        if self.path == "/api/playlists":
            host=self.headers.get("Host","")
            if host not in {f"127.0.0.1:{self.server.server_port}",f"localhost:{self.server.server_port}"} or self.headers.get("Origin")!="http://"+host or self.headers.get("X-Fieldstation")!="playlists":return self.send_json({"error":"Local request required"},403)
            try:
                n=int(self.headers.get("Content-Length","0"))
                if not 0<n<=600000:raise ValueError("Invalid request")
                payload=json.loads(self.rfile.read(n))
                if not isinstance(payload,dict):raise ValueError("Invalid request")
                if payload.get('action')=='generate_categories': return self.send_json(category_playlists.start(inventory()))
                if payload.get('action')=='generate': return self.send_json(playlist_ai.start(payload,inventory()))
                return self.send_json(playlists.run(payload))
            except (ValueError,TypeError) as e:return self.send_json({"error":str(e)},400)
        if self.path == '/api/wifi': return self.wifi_request(True)
        if self.path.startswith('/api/private/'): return self.private_request(post=True)
        if self.path != '/api/play': return self.send_error(404)
        # Require a same-origin JSON request, rejecting cross-site native app launches.
        hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        host = self.headers.get('Host', '')
        if host not in hosts or self.headers.get('Origin') != 'http://' + host or self.headers.get('X-Fieldstation') != 'play':
            return self.send_json({'error': 'Local same-origin request required.'}, 403)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024 or self.headers.get('Content-Type') != 'application/json': raise ValueError()
            payload = json.loads(self.rfile.read(length))
            uid = payload.get('id') if isinstance(payload, dict) else None
            if not isinstance(uid, str) or not re.fullmatch(r'[a-f0-9]{20}', uid): raise ValueError()
        except (ValueError, TypeError): return self.send_json({'error': 'Invalid playback request.'}, 400)
        try: launch_video(uid)
        except ValueError as e: return self.send_json({'error': str(e)}, 404)
        except (RuntimeError, OSError) as e: return self.send_json({'error': str(e)}, 503)
        return self.send_json({'message': 'VLC launch requested in a separate window. Use VLC to check playback.'})
    def do_HEAD(self): self.do_GET(head=True)
    def do_GET(self, head=False):
        if self.path.startswith('/kolibri/'): return kolibri_proxy.serve(self,head)
        route = urlparse(self.path).path
        if route == '/api/art-status': return self.send_json(art_gallery.status())
        if route == '/api/art': return self.send_json(art_gallery.query(parse_qs(urlparse(self.path).query)))
        if route == '/api/discovery': return self.send_json(discovery.suggestions())
        if route == '/api/codex':return self.send_json(codex_launcher.status())
        if route == '/api/audio-settings': return self.send_json(audio_settings.status())
        if route == '/api/battery': return self.send_json(battery_status.status())
        if route == '/api/air-quality': return self.send_json(air_quality.status())
        if route == '/api/ask': return self.send_json(ask_library.status())
        if route == '/api/playlist-ai': return self.send_json(playlist_ai.status(parse_qs(urlparse(self.path).query).get('id',[''])[0]))
        if route == '/api/category-playlists': return self.send_json(category_playlists.status())
        if route == '/api/playlists': return self.send_json(playlists.run())
        if route == '/api/wifi': return self.wifi_request()
        if route == '/api/share':
            params=parse_qs(urlparse(self.path).query)
            try:return self.send_json(sharing.share(params.get('path',[''])[0],params.get('host',[''])[0]))
            except ValueError as e:return self.send_json({'error':str(e)},400)
        if route == '/api/gutenberg':
            return self.send_json(gutenberg.query(parse_qs(urlparse(self.path).query)))
        if route == '/api/youtube':
            try:return self.send_json(youtube_browse.search(parse_qs(urlparse(self.path).query).get('q',[''])[0]))
            except Exception:return self.send_json({'error':'YouTube search is unavailable. Check internet access or try another search.'},503)
        if route == '/api/gutenberg-book':
            try:return self.send_json(gutenberg.book(parse_qs(urlparse(self.path).query).get('id',[''])[0]))
            except Exception:return self.send_json({'error':'Book reader unavailable. Try the original book.'},503)
        if route == '/api/topics':
            return self.send_json(topics.tree())
        if route == '/api/catalogue':
            params=parse_qs(urlparse(self.path).query)
            return self.send_json(catalogue.query(params.get('q',[''])[0],params.get('id',[''])[0],params.get('category',[''])[0]))
        if route.startswith('/api/private/'):
            if head: return self.send_error(405)
            return self.private_request()
        if route == '/api/tools/status': return self.send_json(offline_tools.status())
        if route == '/api/learning-status': return self.send_json(learning_status.status())
        if route == '/api/maps': return self.send_json(offline_maps.manifest())
        if route == '/api/maps/search':
            params=parse_qs(urlparse(self.path).query)
            try:
                lon=float(params.get('lon',['0'])[0]);lat=float(params.get('lat',['0'])[0])
                if not (-180<=lon<=180 and -90<=lat<=90):raise ValueError()
                return self.send_json(offline_maps.search(params.get('q',[''])[0][:100],lon,lat))
            except ValueError:return self.send_json({'error':'Invalid search coordinates.'},400)
        if route == '/api/maps/route':
            if self.headers.get('Host','') not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}:return self.send_json({'error':'Local request required.'},403)
            try:return self.send_json(offline_maps.route(parse_qs(urlparse(self.path).query)))
            except ValueError as e:return self.send_json({'error':str(e)},400)
            except Exception:return self.send_json({'error':'No route available. Check coverage, road access, or try a shorter route.'},503)
        if route == '/api/library':
            items = inventory()
            try: disk = shutil.disk_usage(ROOT); storage = dict(total=disk.total, free=disk.free)
            except OSError: storage = None
            try:
                with socket.create_connection(('127.0.0.1', 8080), timeout=.2): kiwix=True
            except OSError: kiwix=False
            return self.send_json(dict(items=items, scanning=SCAN_LOCK.locked(), scanError=SCAN_ERROR, storage=storage, libraryConnected=ROOT.is_dir(), mediaConnected=any(r.is_dir() for r in media_roots()), mediaSources=[dict(path=str(r),connected=r.is_dir()) for r in media_roots()], kiwix=kiwix, root=str(ROOT), media=str(MEDIA)))
        if route.startswith('/map-data/'):
            p=offline_maps.file_path(route)
            if p is None:return self.send_error(404)
        elif route in ('/maps.html','/maps.js'):
            p=BASE/'dist'/route[1:]
        elif route.startswith(('/art-image/','/art-thumb/')):
            p=art_gallery.image_path(route.rsplit('/',1)[-1],route.startswith('/art-thumb/'))
            if p is None:return self.send_error(404)
        elif route.startswith('/api/video-thumbnail/'):
            uid=route.rsplit('/',1)[-1]
            if not re.fullmatch(r'[a-f0-9]{20}',uid): return self.send_error(404)
            inventory(); source=CACHE['files'].get(uid)
            if source is None: return self.send_error(404)
            source=source.resolve()
            if source.suffix.lower() not in VIDEO or source.is_relative_to(PRIVATE.root.resolve()) or not any(source.is_relative_to(r.resolve()) for r in [ROOT,*media_roots()]): return self.send_error(403)
            try:p=video_thumbnails.thumbnail(source)
            except OSError:return self.send_error(404)
            if p is None:return self.send_error(404)
        elif route.startswith(('/content/','/audio-compatible/')):
            inventory(); p=CACHE['files'].get(route.split('/')[-1])
            if p is None: return self.send_error(404, 'File unavailable or still downloading')
            # Resolve again at open time to reject replacements with out-of-root links.
            resolved=p.resolve()
            if resolved.is_relative_to(PRIVATE.root.resolve()): return self.send_error(403)
            if not any(resolved.is_relative_to(r.resolve()) for r in [ROOT, *media_roots()]): return self.send_error(403)
            if route.startswith('/audio-compatible/'):
                try: p=audio_compat.compatible(resolved)
                except (OSError, ValueError, subprocess.SubprocessError): return self.send_error(422, 'Unable to prepare compatible audio')
        else:
            assets={'/tools.html':'tools.html','/tools.css':'tools.css','/tools.js':'tools.js','/game-art/kart.png':'game-art/kart.png','/game-art/supertux.svg':'game-art/supertux.svg','/game-art/bubbles.png':'game-art/bubbles.png','/game-art/hedgewars.png':'game-art/hedgewars.png','/game-art/action.png':'game-art/action.png','/game-art/catan.png':'game-art/catan.png','/game-art/monopoly.png':'game-art/monopoly.png','/game-art/rts.png':'game-art/rts.png','/game-art/solitaire.png':'game-art/solitaire.png','/game-art/freecell.png':'game-art/freecell.png','/game-art/spider.png':'game-art/spider.png','/game-art/mahjong.svg':'game-art/mahjong.svg','/game-art/transport.png':'game-art/transport.png','/game-art/credits.txt':'game-art/credits.txt','/game-art/doom.png':'game-art/doom.png','/game-art/blocks.png':'game-art/blocks.png','/game-art/chess.svg':'game-art/chess.svg','/game-art/pacman.png':'game-art/pacman.png','/game-art/city.png':'game-art/city.png','/learning.html':'learning.html','/learning.js':'learning.js','/games.html':'games.html','/games.js':'games.js','/power.js':'power.js','/art.js':'art.js','/playlists-page.js':'playlists-page.js','/codex.js':'codex.js','/energy.js':'energy.js','/viewer.js':'viewer.js','/spotify.js':'spotify.js','/air.js':'air.js','/':'index.html','/ask.js':'ask.js','/app.js':'app.js','/videos.js':'videos.js','/media.js':'media.js','/topics.js':'topics.js','/wifi.js':'wifi.js','/sharing.js':'sharing.js','/catalogue.js':'catalogue.js','/private.js':'private.js','/style.css':'style.css','/favicon.svg':'favicon.svg'}
            if route not in assets: return self.send_error(404)
            p=BASE/'dist'/assets[route]
        try:
            f=p.open('rb'); size=os.fstat(f.fileno()).st_size
        except OSError: return self.send_error(404)
        start,end=0,size-1; status=200
        request_range=self.headers.get('Range')
        if request_range:
            match=re.fullmatch(r'bytes=(\d*)-(\d*)', request_range)
            if not match or not any(match.groups()):
                f.close(); return self.send_error(416)
            a,b=match.groups()
            if a: start=int(a); end=min(int(b),size-1) if b else size-1
            else: start=max(0,size-int(b))
            if start>end or start>=size:
                f.close(); self.send_response(416); self.send_header('Content-Range',f'bytes */{size}'); self.end_headers(); return
            status=206
        self.send_response(status)
        self.send_header('Content-Type',mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
        self.send_header('Content-Length',str(max(0,end-start+1)))
        self.send_header('Accept-Ranges','bytes')
        self.send_header('X-Content-Type-Options','nosniff')
        if p.suffix.lower() in {'.epub','.zim'} or parse_qs(urlparse(self.path).query).get('download')==['1']: self.send_header('Content-Disposition', "attachment; filename*=UTF-8''"+quote(p.name))
        if status==206: self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        try:
            if not head:
                f.seek(start); remain=end-start+1
                while remain>0:
                    data=f.read(min(1024*1024,remain))
                    if not data: break
                    self.wfile.write(data); remain-=len(data)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError): pass
        finally: f.close()

    def wifi_request(self, post=False):
        host=self.headers.get('Host','')
        if host not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'} or self.headers.get('X-Fieldstation')!='wifi' or (post and self.headers.get('Origin')!='http://'+host):
            return self.send_json({'error':'Local same-origin request required.'},403)
        try:
            if post:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=2048 or self.headers.get('Content-Type')!='application/json':raise ValueError('Invalid Wi-Fi request.')
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict):raise ValueError('Invalid Wi-Fi request.')
                return self.send_json(wifi.change(payload))
            return self.send_json(wifi.status(parse_qs(urlparse(self.path).query).get('scan')==['1']))
        except ValueError as e:return self.send_json({'error':str(e)},400)
        except (OSError,RuntimeError,subprocess.SubprocessError):return self.send_json({'error':'Wi-Fi service unavailable. Check NetworkManager and desktop permissions.'},503)

    def private_request(self, post=False):
        host=self.headers.get('Host','')
        hosts={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        if host not in hosts or self.headers.get('X-Fieldstation')!='private' or (post and self.headers.get('Origin')!='http://'+host):
            return self.send_json({'error':'Local private-file request required.'},403)
        route=urlparse(self.path).path
        token=self.headers.get('X-Private-Token','')
        try:
            if post:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=8192 or self.headers.get('Content-Type')!='application/json':raise ValueError('Invalid request.')
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict):raise ValueError('Invalid request.')
                if route=='/api/private/unlock':
                    container=payload.get('container')
                    if container is not None and not isinstance(container,str):raise ValueError('Invalid container path.')
                    result=PRIVATE.unlock(container)
                elif route=='/api/private/eject':result=PRIVATE.eject()
                elif route=='/api/private/open':
                    rel=payload.get('path')
                    if not isinstance(rel,str):raise ValueError('Invalid file.')
                    p=PRIVATE.path(rel,token)
                    if not p.is_file():raise ValueError('File unavailable.')
                    if p.suffix.lower() in VIDEO:proc=launch_vlc(p)
                    elif p.suffix.lower() in {'.doc','.docx','.odt','.rtf','.xls','.xlsx','.ppt','.pptx'}:
                        exe=os.environ.get('FIELD_LIBREOFFICE') or shutil.which('libreoffice') or shutil.which('soffice')
                        if not exe and Path('C:/Program Files/LibreOffice/program/soffice.exe').is_file():exe='C:/Program Files/LibreOffice/program/soffice.exe'
                        if not exe:raise ValueError('Install LibreOffice for full document viewing. DOCX text can also be previewed here.')
                        proc=subprocess.Popen([exe,'--view','--norestore',str(p)])
                    else:raise ValueError('No external viewer configured for this file type.')
                    PRIVATE.processes.append(proc);result={'message':'Viewer launch requested. Close the viewer before ejecting.'}
                else:return self.send_error(404)
                return self.send_json(result)
            if route=='/api/private/status':return self.send_json(PRIVATE.status())
            rel=parse_qs(urlparse(self.path).query).get('path',[''])[0]
            if route=='/api/private/list':return self.send_json({'items':PRIVATE.listing(rel,token)})
            if route=='/api/private/thumbnail':
                p=PRIVATE.path(rel,token)
                if not p.is_file() or p.suffix.lower() not in VIDEO | video_thumbnails.PRIVATE_IMAGES:raise ValueError('Not an image or video file.')
                raw=video_thumbnails.private_preview(p)
                PRIVATE.authorize(token)
                self.send_response(200);self.send_header('Content-Type','image/jpeg');self.send_header('Content-Length',str(len(raw)))
                self.send_header('Cache-Control','no-store, max-age=0');self.send_header('Cross-Origin-Resource-Policy','same-origin');self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
                self.wfile.write(raw);return
            if route!='/api/private/file':return self.send_error(404)
            p=PRIVATE.path(rel,token)
            if not p.is_file() or p.suffix.lower() not in PREVIEW:raise ValueError('This file type needs an external viewer.')
            if p.stat().st_size>64*1024*1024:raise ValueError('Inline preview is limited to 64 MiB.')
            if p.suffix.lower()=='.docx':
                with zipfile.ZipFile(p) as archive:
                    info=archive.getinfo('word/document.xml')
                    if info.file_size>8*1024*1024:raise ValueError('Document text is too large to preview.')
                    root=ET.fromstring(archive.read(info))
                    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    content='\n'.join(''.join(n.itertext()) for n in root.findall('.//w:p',ns))
                raw=content.encode('utf-8');mime='text/plain; charset=utf-8'
            else:
                raw=p.read_bytes();mime=mimetypes.guess_type(p.name)[0] or 'text/plain'
            PRIVATE.authorize(token)
            self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store, max-age=0');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cross-Origin-Resource-Policy','same-origin');self.end_headers()
            for offset in range(0,len(raw),65536):
                try:PRIVATE.authorize(token)
                except PermissionError:break
                self.wfile.write(raw[offset:offset+65536])
        except PermissionError as e:return self.send_json({'error':str(e)},403)
        except (ValueError,OSError,RuntimeError,zipfile.BadZipFile,KeyError,ET.ParseError,subprocess.SubprocessError) as e:
            return self.send_json({'error':str(e)},400)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--library', default=os.environ.get('FIELD_LIBRARY','D:/Offline Library' if os.name=='nt' else '/media/library/Offline Library'))
    parser.add_argument('--media', default=os.environ.get('FIELD_MEDIA','D:/YouTube Downloads' if os.name=='nt' else '/media/library/YouTube Downloads'))
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args(); ROOT=Path(args.library).resolve(); MEDIA=Path(args.media).resolve()
    if not PRIVATE.container:
        PRIVATE.container=str(ROOT.parent / 'Master Backup April 2020')
    air_quality.start()
    battery_status.start()
    sharing.start(sys.modules[__name__])
    catalogue.start(index_inventory, lambda: CACHE['files'])
    print(f'Fieldstation running at http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
