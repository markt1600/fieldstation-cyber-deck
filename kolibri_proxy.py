"""Same-origin access to the loopback-only Kolibri learning service."""
import http.client

def serve(handler, head=False):
    host=handler.headers.get('Host','')
    if handler.client_address[0] not in {'127.0.0.1','::1'}:
        return handler.send_json({'error':'Open lessons on the Fieldstation screen.'},403)
    if handler.command not in {'GET','HEAD'} and handler.headers.get('Origin') != 'http://'+host:
        return handler.send_json({'error':'Same-origin request required.'},403)
    try:
        size=int(handler.headers.get('Content-Length','0'))
        if not 0 <= size <= 8*1024*1024: raise ValueError()
    except ValueError:return handler.send_json({'error':'Invalid request size.'},400)
    body=handler.rfile.read(size) if size else None
    headers={k:v for k,v in handler.headers.items() if k.lower() not in {'connection','transfer-encoding','accept-encoding'}}
    connection=http.client.HTTPConnection('127.0.0.1',8085,timeout=60)
    started=False
    try:
        connection.request('HEAD' if head else handler.command,handler.path,body,headers)
        response=connection.getresponse()
        handler.send_response(response.status)
        for k,v in response.getheaders():
            if k.lower() not in {'connection','transfer-encoding','server','date','x-frame-options'}:handler.send_header(k,v)
        handler.send_header('X-Frame-Options','SAMEORIGIN')
        handler.end_headers();started=True
        if not head:
            while True:
                chunk=response.read(65536)
                if not chunk:break
                handler.wfile.write(chunk)
    except (OSError,http.client.HTTPException):
        if not started:return handler.send_json({'error':'Offline learning is starting. Please try again shortly.'},503)
    finally:connection.close()
