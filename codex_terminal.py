"""Loopback-only embedded Codex terminal with strict browser-origin checks."""
import sys,os,pty,fcntl,termios,struct,signal,json,codecs
from pathlib import Path
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'vendor-terminal'))
import tornado.web,tornado.websocket,tornado.ioloop
ORIGIN='http://127.0.0.1:8767'
class Local(tornado.web.RequestHandler):
 def prepare(self):
  if self.request.host!='127.0.0.1:8767':raise tornado.web.HTTPError(403)
 def set_default_headers(self):
  self.set_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors http://127.0.0.1:8765 http://localhost:8765")
  self.set_header('Cache-Control','no-store')
 def get(self,name='index.html'):
  if name not in ('index.html','xterm.js','xterm.css','fit.js','terminal.js'):raise tornado.web.HTTPError(404)
  self.set_header('Content-Type','text/html' if name.endswith('.html') else 'text/css' if name.endswith('.css') else 'application/javascript')
  self.write((BASE/'terminal-assets'/name).read_bytes())
class Terminal(tornado.websocket.WebSocketHandler):
 pid=None;fd=None;active=None
 def check_origin(self,origin):return origin==ORIGIN
 def prepare(self):
  if self.request.host!='127.0.0.1:8767' or self.request.headers.get('Origin')!=ORIGIN:raise tornado.web.HTTPError(403)
 def open(self):
  if Terminal.active is not None:self.close(1008,'A Codex terminal is already open.');return
  Terminal.active=self
  self.decoder=codecs.getincrementaldecoder('utf-8')('replace')
  self.pid,self.fd=pty.fork()
  if self.pid==0:
   os.chdir(BASE);os.environ['TERM']='xterm-256color';os.environ['COLORTERM']='truecolor'
   binary=str(Path.home()/'.local/bin/codex')
   os.execv(binary,[binary,'--no-daemon','-C',str(BASE)])
  os.set_blocking(self.fd,False)
  tornado.ioloop.IOLoop.current().add_handler(self.fd,self.readable,tornado.ioloop.IOLoop.READ)
 def readable(self,fd,events):
  try:
   raw=os.read(fd,16384)
   if not raw:self.close();return
   self.write_message(self.decoder.decode(raw))
  except BlockingIOError:pass
  except OSError:self.close()
 def on_message(self,message):
  try:
   d=json.loads(message)
   if d.get('type')=='input' and isinstance(d.get('data'),str):os.write(self.fd,d['data'].encode())
   elif d.get('type')=='resize':
    cols=max(20,min(300,int(d['cols'])));rows=max(5,min(150,int(d['rows'])))
    fcntl.ioctl(self.fd,termios.TIOCSWINSZ,struct.pack('HHHH',rows,cols,0,0))
  except (ValueError,TypeError,KeyError,OSError):self.close(1008,'Invalid terminal message')
 def on_close(self):
  if Terminal.active is self:Terminal.active=None
  if self.fd is not None:
   tornado.ioloop.IOLoop.current().remove_handler(self.fd);os.close(self.fd);self.fd=None
  if self.pid:
   try:os.kill(self.pid,signal.SIGHUP)
   except ProcessLookupError:pass
   pid=self.pid
   def reap():
    try:
     if os.waitpid(pid,os.WNOHANG)[0]==0:os.kill(pid,signal.SIGTERM);tornado.ioloop.IOLoop.current().call_later(2,reap)
    except (ProcessLookupError,ChildProcessError):pass
   tornado.ioloop.IOLoop.current().call_later(1,reap)
if __name__=='__main__':
 app=tornado.web.Application([(r'/ws',Terminal),(r'/',Local),(r'/(index.html|xterm.js|xterm.css|fit.js|terminal.js)',Local)],websocket_max_message_size=16384,websocket_ping_interval=20)
 app.listen(8767,address='127.0.0.1');tornado.ioloop.IOLoop.current().start()
