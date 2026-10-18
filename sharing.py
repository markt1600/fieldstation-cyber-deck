"""Separate, read-only LAN listener for public documents and Kiwix."""
import html,ipaddress,json,re,socket,threading,urllib.request,urllib.error
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs,quote
import qrcode
PORT=8766
APP=None

def addresses():
    return sorted({r[4][0] for r in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET) if ipaddress.ip_address(r[4][0]).is_private and not ipaddress.ip_address(r[4][0]).is_loopback and not ipaddress.ip_address(r[4][0]).is_link_local})

def share(path,host=''):
    u=urlsplit(path)
    if u.scheme or u.netloc or not (u.path.startswith('/kiwix/') or u.path=='/shared'):raise ValueError('Only public library pages can be shared.')
    ips=addresses()
    if not ips:raise ValueError('No local network address found. Connect to Wi-Fi or enable the Pi hotspot.')
    if host and host not in ips:raise ValueError('Choose a listed network address.')
    url='http://'+(host or ips[0])+':'+str(PORT)+path
    qr=qrcode.QRCode(border=4);qr.add_data(url);qr.make(fit=True);matrix=qr.get_matrix();n=len(matrix)
    squares=''.join(f'<rect x="{x}" y="{y}" width="1" height="1"/>' for y,row in enumerate(matrix) for x,on in enumerate(row) if on)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}"><rect width="{n}" height="{n}" fill="white"/><g fill="black">{squares}</g></svg>'
    return dict(url=url,svg=svg,addresses=ips,host=host or ips[0])

class PublicHandler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):self.send_error(403,'Device controls are not shared')
    def do_HEAD(self):self.do_GET(True)
    def do_GET(self,head=False):
        route=urlsplit(self.path).path
        if route.startswith('/kiwix/'):
            # Fixed upstream: never proxy arbitrary hosts or forward client credentials.
            headers={'Accept-Encoding':'identity'}
            if self.headers.get('Range'):headers['Range']=self.headers['Range']
            try:
                request=urllib.request.Request('http://127.0.0.1:8080'+self.path,headers=headers,method='HEAD' if head else 'GET')
                upstream=urllib.request.urlopen(request,timeout=30)
                with upstream:
                    if upstream.geturl() != request.full_url:
                        dest=urlsplit(upstream.geturl());self.send_response(302);self.send_header('Location',dest.path+('?' + dest.query if dest.query else ''));self.end_headers();return
                    mime=upstream.headers.get('Content-Type','application/octet-stream')
                    # Relay current page to the parent reader; no private data is included.
                    ishtml='text/html' in mime and not head
                    if ishtml:
                        raw=upstream.read();notice=b'<script>parent.postMessage({type:"fieldstation-page",path:location.pathname+location.search+location.hash},"*");window.addEventListener("hashchange",()=>parent.postMessage({type:"fieldstation-page",path:location.pathname+location.search+location.hash},"*"));</script>'
                        raw+=notice
                    self.send_response(upstream.status);self.send_header('Content-Type',mime)
                    for name in ['Content-Disposition','Content-Range','Accept-Ranges']:
                        if upstream.headers.get(name):self.send_header(name,upstream.headers[name])
                    if ishtml:self.send_header('Content-Length',str(len(raw)))
                    elif upstream.headers.get('Content-Length'):self.send_header('Content-Length',upstream.headers['Content-Length'])
                    self.send_header('Cache-Control','no-store');self.end_headers()
                    if not head:
                        if ishtml:self.wfile.write(raw)
                        else:
                            while True:
                                block=upstream.read(1024*1024)
                                if not block:break
                                self.wfile.write(block)
            except urllib.error.HTTPError as e:self.send_error(e.code)
            except (OSError,urllib.error.URLError):
                try:self.send_error(503,'Kiwix is unavailable')
                except OSError:pass
            return
        params=parse_qs(urlsplit(self.path).query)
        uid=params.get('id',[''])[0] if route=='/shared' else route.removeprefix('/content/')
        if route!='/shared' and not route.startswith('/content/'):return self.send_error(404)
        APP.inventory();p=APP.CACHE['files'].get(uid)
        if not p or p.suffix.lower() not in {'.pdf','.epub'} or p.resolve().is_relative_to(APP.PRIVATE.root.resolve()):return self.send_error(404)
        if route.startswith('/content/'):return APP.Handler.do_GET(self,head)
        page=params.get('page',['1'])[0];page=page if page.isdigit() and len(page)<7 else '1'
        view='/content/'+uid+'#page='+page;download='/content/'+uid+'?download=1'
        raw=('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Shared from Fieldstation</title><style>body{font:18px system-ui;max-width:650px;margin:40px auto;padding:20px}a{display:block;padding:18px;margin:16px 0;background:#eee}</style><h1>'+html.escape(p.stem)+'</h1><p>Shared from your local Fieldstation.</p><a href="'+view+'">Open'+(' at PDF page '+page if p.suffix.lower()=='.pdf' else ' book')+'</a><a href="'+download+'">Download '+p.suffix[1:].upper()+'</a><p>Keep the downloaded file to read after disconnecting. Article-to-PDF conversion is not included.</p>').encode()
        self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers()
        if not head:self.wfile.write(raw)

def start(app,port=8766):
    global APP,PORT
    APP=app;PORT=port
    server=ThreadingHTTPServer(('0.0.0.0',port),PublicHandler)
    threading.Thread(target=server.serve_forever,daemon=True,name='public-library').start()
    return server
