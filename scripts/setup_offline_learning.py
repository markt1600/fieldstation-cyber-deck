from pathlib import Path
import os,secrets,subprocess
if not os.path.ismount('/media/library'):raise SystemExit('Mount the SSD first.')
home=Path('/media/library/Education/Kolibri');home.mkdir(parents=True,exist_ok=True)
(home/'options.ini').write_text('[Deployment]\nHTTP_PORT = 8085\nZIP_CONTENT_PORT = 8086\nLISTEN_ADDRESS = 127.0.0.1\nURL_PATH_PREFIX = /kolibri/\nDISABLE_PING = True\n')
env=dict(os.environ,KOLIBRI_HOME=str(home));exe=str(Path.home()/'fieldstation-kolibri/bin/kolibri')
credential=Path.home()/'.config/fieldstation-kolibri-admin'
if not credential.exists():
    password=secrets.token_urlsafe(24)
    result=subprocess.run([exe,'manage','provisiondevice','--facility','Fieldstation','--superusername','fieldstation-admin','--superuserpassword',password,'--preset','informal','--language_id','en','--noinput'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if result.returncode:raise SystemExit('Provisioning failed')
    fd=os.open(credential,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:f.write('Username: fieldstation-admin\nPassword: '+password+'\n')
unit=Path.home()/'.config/systemd/user/fieldstation-kolibri.service'
unit.write_text('[Unit]\nDescription=Fieldstation offline learning\nConditionPathIsMountPoint=/media/library\nAfter=network.target\n[Service]\nEnvironment=KOLIBRI_HOME=/media/library/Education/Kolibri\nExecStart=%h/fieldstation-kolibri/bin/kolibri start --foreground\nRestart=on-failure\nTimeoutStopSec=45\n[Install]\nWantedBy=default.target\n')
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
subprocess.run(['systemctl','--user','enable','--now','fieldstation-kolibri'],check=True)
subprocess.run([exe,'manage','importchannel','network','c9d7f950ab6b5a1199e3d6c10d7f0103'],env=env,check=True)
