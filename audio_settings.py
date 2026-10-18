"""Validated, atomic preferences shared by the UI and audio controller."""
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

SETTINGS = Path.home()/'.config/fieldstation/audio.json'
DEFAULTS = {'bass_db':6.0,'frequency_hz':120.0,'mode':'always'}

def validate(value):
    if not isinstance(value,dict) or set(value)!=set(DEFAULTS):
        raise ValueError('Provide bass amount, frequency and mode.')
    for key,low,high in [('bass_db',0,12),('frequency_hz',90,180)]:
        v=value[key]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low<=v<=high:
            raise ValueError('Audio setting outside its allowed range.')
    if value['mode'] not in ('always','adaptive'):
        raise ValueError('Choose always-on or volume-dependent bass.')
    return dict(value)

def read():
    try:
        return validate(json.loads(SETTINGS.read_text()))
    except (OSError,ValueError):
        return dict(DEFAULTS)

def save(value):
    value=validate(value)
    SETTINGS.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=SETTINGS.parent,prefix='.audio-')
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(value,f)
        os.replace(name,SETTINGS)
    finally:
        if os.path.exists(name): os.unlink(name)
    return status()

def status():
    services={}
    for name in ('spotify','audio-dsp','loudness'):
        try:
            p=subprocess.run(['systemctl','--user','is-active','fieldstation-'+name+'.service'],
                             capture_output=True,text=True,timeout=2)
            services[name]=p.stdout.strip()=='active'
        except (OSError,subprocess.SubprocessError):
            services[name]=False
    return {'settings':read(),'services':services}
