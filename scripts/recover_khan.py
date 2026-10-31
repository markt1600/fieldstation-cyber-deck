"""Recover missing Khan Academy files from the public Kolibri mirror, verifying hashes."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import hashlib, json, os, re, sqlite3, subprocess, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

HOME = Path('/media/library/Education/Kolibri')
CHANNEL = 'c9d7f950ab6b5a1199e3d6c10d7f0103'
MIRROR = 'https://kolibri-demo.learningequality.org/content/storage/'

def recover(row):
    checksum, extension, size = row
    if not re.fullmatch('[0-9a-f]{32}', checksum) or not re.fullmatch('[a-zA-Z0-9]+', extension):
        return {'file':str(checksum), 'error':'Invalid catalogue filename'}
    relative = f'{checksum[0]}/{checksum[1]}/{checksum}.{extension}'
    dest = HOME / 'content/storage' / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_name(dest.name + '.recovery-part')
    for attempt in range(3):
        try:
            digest = hashlib.md5(); count = 0
            with urlopen(Request(MIRROR+relative, headers={'User-Agent':'Fieldstation offline learning recovery'}),timeout=30) as source, temp.open('wb') as target:
                while chunk := source.read(262144):
                    target.write(chunk); digest.update(chunk); count += len(chunk)
                    if size is not None and count > size: raise ValueError('File exceeds catalogue size')
            if digest.hexdigest() != checksum or (size is not None and count != size):
                raise ValueError('Catalogue checksum or size mismatch')
            os.replace(temp,dest)
            return {'file':dest.name,'bytes':count,'recovered':True}
        except Exception as error:
            failure=str(error)
            if temp.exists():temp.unlink()
            if isinstance(error,(ValueError,HTTPError)) and (not isinstance(error,HTTPError) or error.code in (403,404)):
                break
            if attempt < 2: time.sleep(2*(attempt+1))
    return {'file':dest.name,'error':failure}

def main():
    if not os.path.ismount('/media/library'):raise SystemExit('SSD not mounted')
    with sqlite3.connect(HOME/'content/databases'/f'{CHANNEL}.sqlite3') as db:
        rows=db.execute('SELECT id, extension, file_size FROM content_localfile').fetchall()
    missing=[]
    for row in rows:
        h,ext,size=row; p=HOME/'content/storage'/h[0]/h[1]/f'{h}.{ext}'
        if not p.is_file() or (size is not None and p.stat().st_size != size):missing.append(row)
    state={'state':'recovering','total_missing':len(missing),'checked':0,'recovered':0,'recovered_bytes':0,'failed':[],'started':time.time()}
    report=HOME/'recovery-status.json'
    def save():
        temp=report.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2));temp.replace(report)
    save();print('Missing files:',len(missing),flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(recover,row) for row in missing]):
            result=future.result();state['checked']+=1
            if result.get('recovered'):
                state['recovered']+=1;state['recovered_bytes']+=result['bytes']
            else:state['failed'].append(result)
            if state['checked']%25==0 or state['checked']==len(missing):
                save();print('Checked',state['checked'],'recovered',state['recovered'],'failed',len(state['failed']),flush=True)
    state['state']='indexing';save()
    exe=Path.home()/'fieldstation-kolibri/bin/kolibri'
    subprocess.run([str(exe),'manage','scanforcontent','--channel-import-mode','none','--channels',CHANNEL],env=dict(os.environ,KOLIBRI_HOME=str(HOME)),check=True)
    state['state']='finished';state['finished']=time.time();save()
    print('Recovery finished:',state['recovered'],'recovered;',len(state['failed']),'unavailable',flush=True)

if __name__=='__main__':main()
