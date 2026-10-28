"""Fixed offline game launchers for the local Pi desktop."""
import os
from pathlib import Path
import subprocess
import threading
import time
ROOT = Path.home() / 'fieldstation-games/root'
LOCK = threading.Lock()
GAMES = {'doom': 'Doom · Freedoom', 'blocks': 'Falling blocks', 'chess': 'Chess', 'pacman': 'Pac-Man style', 'city': 'LinCity-NG'}
def command(game):
    base = ROOT / 'usr'
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
    for fonts in ['misc', '75dpi']:
        subprocess.run(['xset','+fp',str(ROOT/'usr/share/fonts/X11'/fonts)],capture_output=True,timeout=5)
    subprocess.run(['xset','fp','rehash'],capture_output=True,timeout=5)
    args = command(sys.argv[2])
    os.execvpe(args[0],args,os.environ)
