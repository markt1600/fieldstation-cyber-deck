"""Download the five-language offline translation collection to the SSD."""
from pathlib import Path
import json,urllib.request,zipfile,shutil,subprocess
from concurrent.futures import ThreadPoolExecutor
ROOT=Path('/media/library/Tools/Translation')
def fetch(p):
    pair=p['from_code']+'_'+p['to_code']; dest=ROOT/'models'/pair
    if (dest/'metadata.json').exists():return
    archive=ROOT/(pair+'.part')
    print('Downloading',pair,flush=True)
    subprocess.run(['curl','--fail','--location','--retry','3','--user-agent','Mozilla/5.0','--output',str(archive),next(u for u in p['links'] if u.startswith('https://'))],check=True)
    temp=ROOT/'models'/(pair+'.extract');temp.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            target=(temp/info.filename).resolve()
            if not target.is_relative_to(temp.resolve()):raise ValueError('Unsafe archive path')
        z.extractall(temp)
    meta=next(temp.rglob('metadata.json'));src=meta.parent
    if not (src/'model/model.bin').is_file() or not (src/'sentencepiece.model').is_file():raise ValueError('Incomplete translation model')
    src.rename(dest)
    shutil.rmtree(temp)
    archive.unlink()
    print('Installed',pair,flush=True)
def main():
    if not Path('/media/library').is_mount():raise SystemExit('SSD is not mounted')
    ROOT.mkdir(parents=True,exist_ok=True);(ROOT/'models').mkdir(exist_ok=True)
    index=json.load(urllib.request.urlopen('https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json'))
    packages=[p for p in index if (p['from_code']=='en' and p['to_code'] in ['ja','ms','fr','ko']) or (p['to_code']=='en' and p['from_code'] in ['ja','ms','fr','ko'])]
    if len(packages)!=8:raise ValueError('Expected eight language models')
    (ROOT/'model-sources.json').write_text(json.dumps(packages,indent=2))
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(fetch,packages))
    print('All eight translation models installed',flush=True)
if __name__=='__main__':main()
