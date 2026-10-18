"""Local NetworkManager Wi-Fi controls. Secrets never enter command arguments."""
import os,re,shutil,subprocess,threading,uuid

LOCK=threading.Lock()
def split_fields(line):
    return [re.sub(r'\\(.)',r'\1',v) for v in re.split(r'(?<!\\):',line)]

def nm(*args, secret_fd=None):
    kwargs={'capture_output':True,'text':True,'timeout':50,'env':dict(os.environ,LC_ALL='C')}
    if secret_fd is not None:kwargs['pass_fds']=(secret_fd,)
    result=subprocess.run([shutil.which('nmcli'),'--wait','35',*args],**kwargs)
    if result.returncode:raise RuntimeError('Wi-Fi operation failed. Check the password, signal and NetworkManager permissions in the Pi desktop.')
    return result.stdout.strip()

def supported():return os.name!='nt' and bool(shutil.which('nmcli'))

def status(scan=False):
    if not supported():
        ssid='';state='unavailable'
        if os.name=='nt':
            try:
                raw=subprocess.run(['netsh','wlan','show','interfaces'],capture_output=True,text=True,timeout=8).stdout
                m=re.search(r'^\s*SSID\s*:\s*(.+)$',raw,re.M)
                if m:ssid=m[1].strip();state='connected'
            except (OSError,subprocess.SubprocessError):pass
        return dict(supported=False,ssid=ssid,state=state,enabled=None,networks=[],message='Network selection and radio controls are available on the Pi with NetworkManager. Use Windows Wi-Fi settings on this development computer.')
    enabled=nm('radio','wifi')=='enabled'
    devices=[split_fields(line) for line in nm('-t','-f','DEVICE,TYPE,STATE','device','status').splitlines()]
    device=next((d[0] for d in devices if len(d)>2 and d[1]=='wifi' and d[2]=='connected'),None) or next((d[0] for d in devices if len(d)>1 and d[1]=='wifi'),None)
    if not device:return dict(supported=True,enabled=enabled,state='no adapter',ssid='',networks=[])
    rows=[]
    if enabled:
        raw=nm('-t','-f','IN-USE,SSID,SIGNAL,SECURITY,BSSID','device','wifi','list','ifname',device,'--rescan','yes' if scan else 'no')
        for line in raw.splitlines():
            f=split_fields(line)
            if len(f)==5 and f[1]:rows.append(dict(active=f[0]=='*',ssid=f[1],signal=int(f[2] or 0),security=f[3],bssid=f[4]))
    ssid=next((r['ssid'] for r in rows if r['active']),'')
    return dict(supported=True,enabled=enabled,device=device,ssid=ssid,state='connected' if ssid else 'disconnected' if enabled else 'off',networks=sorted(rows,key=lambda r:-r['signal']))

def change(payload):
    if not supported():raise ValueError('Use the Pi for these controls; Windows uses its own Wi-Fi settings.')
    if not LOCK.acquire(False):raise ValueError('Another Wi-Fi change is in progress.')
    try:
        action=payload.get('action')
        if action=='radio':
            if type(payload.get('enabled')) is not bool:raise ValueError('Invalid radio setting.')
            nm('radio','wifi','on' if payload['enabled'] else 'off');return {'message':'Wi-Fi enabled.' if payload['enabled'] else 'Wi-Fi disabled.'}
        if action!='connect':raise ValueError('Unknown Wi-Fi action.')
        bssid=payload.get('bssid');password=payload.get('password','')
        if not isinstance(password,str) or len(password)>256 or any(c in password for c in '\r\n\x00'):raise ValueError('Invalid password.')
        info=status();ap=next((a for a in info['networks'] if a['bssid']==bssid),None)
        if not ap:raise ValueError('Network is no longer listed. Refresh the network list.')
        security=ap['security']
        if '802.1X' in security or 'WEP' in security:raise ValueError('Configure enterprise or legacy networks using the Pi desktop network settings.')
        secured='WPA' in security
        if secured and not password:raise ValueError('Enter the network password.')
        ident=str(uuid.uuid4());created=False;fd=None
        try:
            args=['connection','add','type','wifi','ifname',info['device'],'con-name','Fieldstation '+ap['ssid'],'connection.uuid',ident,'ssid',ap['ssid'],'connection.autoconnect','yes']
            if secured:args+=['wifi-sec.key-mgmt','sae' if 'WPA3' in security and 'WPA2' not in security else 'wpa-psk']
            nm(*args);created=True
            args=['connection','up','uuid',ident,'ifname',info['device']]
            if secured:
                fd=os.memfd_create('wifi-secret',os.MFD_CLOEXEC)
                os.write(fd,('802-11-wireless-security.psk:'+password+'\n').encode());os.lseek(fd,0,0)
                args+=['passwd-file',f'/proc/self/fd/{fd}']
            nm(*args,secret_fd=fd)
            return {'message':'Connected to '+ap['ssid']+'.'}
        except Exception:
            if created:
                try:nm('connection','delete','uuid',ident)
                except Exception:pass
            raise
        finally:
            if fd is not None:os.close(fd)
    finally:LOCK.release()
