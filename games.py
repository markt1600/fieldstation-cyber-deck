"""Fixed offline game launchers for the local Pi desktop."""
import os
from pathlib import Path
import subprocess
import threading
import time
ROOT = Path.home() / 'fieldstation-games/root'
LOCK = threading.Lock()
EXTRA = {'kart': ('SuperTuxKart','/usr/games/supertuxkart'), 'supertux': ('SuperTux','/usr/games/supertux2'), 'bubbles': ('Frozen Bubble','/usr/games/frozen-bubble'), 'transport': ('OpenTTD','/usr/games/openttd'), 'hedgewars': ('Hedgewars','/usr/games/hedgewars'), 'action': ('Blob Wars','/usr/games/blobwars'), 'catan': ('Pioneers','/usr/games/pioneers'), 'monopoly': ('GTKAtlantic','/usr/games/gtkatlantic'), 'rts': ('Warzone 2100','/usr/games/warzone2100'), 'solitaire': ('Solitaire · Aisleriot','/usr/games/sol'), 'freecell': ('FreeCell','/usr/games/ace-freecell'), 'spider': ('Spider Solitaire','/usr/games/ace-spider'), 'mahjong': ('Mahjongg','/usr/games/gnome-mahjongg')}
GAMES = {'doom': 'Doom · Freedoom', 'blocks': 'Falling blocks', 'chess': 'Chess', 'pacman': 'Pac-Man style', 'city': 'LinCity-NG'}
GAMES.update({key: value[0] for key,value in EXTRA.items()})

def extra_prefix():
    return ['/usr/bin/bwrap', '--bind', '/', '/', '--dev', '/dev', '--dev-bind', '/dev/dri', '/dev/dri', '--overlay-src', '/usr', '--overlay-src', str(ROOT/'usr'), '--ro-overlay', '/usr']

def command(game):
    base = ROOT / 'usr'
    if game == 'kart':
        return extra_prefix()+['/usr/games/supertuxkart', '--root=/usr/share/games/supertuxkart', '--windowed', '--screensize=960x540']
    if game == 'rts':
        return [str(base/'games/warzone2100.real'), '--datadir='+str(base/'share/games/warzone2100'), '--window', '--resolution=960x540', '--noshadows']
    if game == 'monopoly':
        return extra_prefix()+['--unshare-net','/usr/bin/python3',str(Path(__file__).with_name('scripts')/'offline_monopoly.py')]
    if game in EXTRA:
        return extra_prefix()+[EXTRA[game][1]]
    if game == 'doom':
        return [str(base/'games/crispy-doom'), '-iwad', str(base/'share/games/doom/freedoom2.wad'), '-window', '-width', '960', '-height', '600']
    prefix = ['/usr/bin/bwrap', '--bind', '/', '/', '--tmpfs', '/usr/share']
    shares = {item.name: item for item in Path('/usr/share').iterdir()}
    shares.update({item.name: item for item in (base/'share').iterdir() if item.name in {'games','lincity-ng'}})
    for name, source in shares.items():
        prefix += ['--ro-bind', str(source), '/usr/share/'+name]
    if game == 'blocks': return prefix + [str(base/'games/ltris2')]
    if game == 'city': return prefix + [str(base/'games/lincity-ng')]
    if game == 'pacman': return [str(base/'games/pacman')]
    if game == 'chess':
        return prefix + [str(base/'games/xboard'), '-settingsFile', str(ROOT/'etc/xboard/xboard.conf'), '-fcp', str(base/'games/gnuchess')+' --xboard', '-scp', str(base/'games/gnuchess')+' --xboard', '-size', 'Medium', '-saveSettingsOnExit', 'false']
    raise ValueError('Unknown game.')
def launch(game):
    if game not in GAMES: raise ValueError('Unknown game.')
    with LOCK:
        state = subprocess.run(['systemctl','--user','is-active','fieldstation-game'],capture_output=True,text=True,timeout=5)
        if state.stdout.strip() in {'active','activating'}:
            raise RuntimeError('A game is already open. Close it before starting another.')
        args = command(game)
        if not Path(args[0]).is_file(): raise RuntimeError('This game is not installed on the Pi yet.')
        subprocess.run(['systemctl','--user','reset-failed','fieldstation-game'],capture_output=True,timeout=5)
        result = subprocess.run(['systemd-run','--user','--collect','--unit=fieldstation-game',
            '--property=StandardOutput=append:'+str(Path.home()/'fieldstation-games/game.log'), '--property=StandardError=append:'+str(Path.home()/'fieldstation-games/game.log'), '--setenv=LD_LIBRARY_PATH='+str(ROOT/'usr/lib/aarch64-linux-gnu'), '/usr/bin/python3', str(Path(__file__).resolve()), '--run', game],capture_output=True,text=True,timeout=10)
        if result.returncode: raise RuntimeError('Could not open the game in the desktop session.')
        time.sleep(1)
        state = subprocess.run(['systemctl','--user','is-active','fieldstation-game'],capture_output=True,text=True,timeout=5)
        if state.stdout.strip() != 'active': raise RuntimeError('The game could not start. Check the game service log.')
        return {'ok': True, 'title': GAMES[game]}

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3 or sys.argv[1] != '--run' or sys.argv[2] not in GAMES:
        raise SystemExit('Choose a listed game.')
    if sys.argv[2] not in EXTRA:
        try:
            for fonts in ['misc', '75dpi']:
                subprocess.run(['xset','+fp',str(ROOT/'usr/share/fonts/X11'/fonts)],capture_output=True,timeout=3)
            subprocess.run(['xset','fp','rehash'],capture_output=True,timeout=3)
        except subprocess.TimeoutExpired:
            pass
    os.environ['SUPERTUXKART_DATADIR']='/usr/share/games/supertuxkart'
    os.environ['LD_LIBRARY_PATH']=str(ROOT/'usr/lib/aarch64-linux-gnu')
    args = command(sys.argv[2])
    os.execvpe(args[0],args,os.environ)
