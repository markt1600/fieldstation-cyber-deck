"""Run Monopoly client and server in the same private network namespace."""
import subprocess
import time
server=subprocess.Popen(['/usr/sbin/monopd'])
try:
    time.sleep(0.5)
    if server.poll() is not None: raise SystemExit('Local board-game server failed')
    raise SystemExit(subprocess.call(['/usr/games/gtkatlantic']))
finally:
    server.terminate()
    try: server.wait(timeout=5)
    except subprocess.TimeoutExpired: server.kill(); server.wait()
