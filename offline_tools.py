"""Fixed desktop tools and bounded, local-only translation requests."""
import json
from pathlib import Path
import subprocess
import threading
import time

ROOT = Path('/media/library/Tools/Translation')
LANGUAGES = {'en': 'English', 'ja': 'Japanese', 'ms': 'Malay', 'fr': 'French', 'ko': 'Korean'}
LOCK = threading.Lock()
APPS = {'writer': ['libreoffice', '--writer'], 'calc': ['libreoffice', '--calc'],
        'pdf': ['libreoffice', '--draw'], 'calculator': ['galculator']}

def status():
    ready = all((ROOT/'models'/pair/'metadata.json').is_file()
                for lang in LANGUAGES if lang != 'en' for pair in ('en_'+lang, lang+'_en'))
    return {'ready': ready, 'languages': LANGUAGES}

def translate(payload):
    source, target, text = payload.get('source'), payload.get('target'), payload.get('text')
    if source not in LANGUAGES or target not in LANGUAGES or not isinstance(text, str) or not 0 < len(text.strip()) <= 2000:
        raise ValueError('Choose two languages and enter up to 2,000 characters.')
    if source == target: return {'text': text, 'pivot': False}
    if not status()['ready']: raise RuntimeError('Language models are still being installed.')
    if not LOCK.acquire(blocking=False): raise RuntimeError('Another translation is running. Please try again shortly.')
    try:
        result = subprocess.run([str(ROOT/'venv/bin/python'), str(Path(__file__).with_name('translation_worker.py'))],
            input=json.dumps({'source': source, 'target': target, 'text': text}), capture_output=True, text=True, timeout=90)
        if result.returncode: raise RuntimeError('Translation could not finish. Try a shorter passage.')
        return json.loads(result.stdout)
    finally:
        LOCK.release()

def launch(name):
    if name not in APPS: raise ValueError('Choose a listed document tool.')
    result = subprocess.run(['systemd-run', '--user', '--collect', '--unit=fieldstation-tool-'+str(time.time_ns()),
        '--property=StandardOutput=journal', '--property=StandardError=journal', *APPS[name]], capture_output=True, text=True, timeout=10)
    if result.returncode: raise RuntimeError('Could not launch the desktop tool.')
    return {'ok': True}
