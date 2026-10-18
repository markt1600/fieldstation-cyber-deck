"""Local desktop power actions through logind; no elevated shell commands."""
import subprocess
import time

def request(action):
    methods = {'reboot': ('CanReboot', 'Reboot'), 'shutdown': ('CanPowerOff', 'PowerOff')}
    if action not in methods:
        raise ValueError('Choose reboot or shutdown.')
    check, method = methods[action]
    prefix = ['/usr/bin/busctl', 'call', 'org.freedesktop.login1', '/org/freedesktop/login1', 'org.freedesktop.login1.Manager']
    result = subprocess.run(prefix + [check], capture_output=True, text=True, timeout=8)
    if result.returncode or result.stdout.strip() != 's "yes"':
        raise RuntimeError('Power control is not permitted in this desktop session. Use the desktop power menu.')
    result = subprocess.run(['/usr/bin/systemd-run', '--user', '--collect', '--on-active=2s', '--unit=fieldstation-power-' + str(time.time_ns()), *prefix, method, 'b', 'false'], capture_output=True, text=True, timeout=8)
    if result.returncode:
        raise RuntimeError('Could not schedule the power action. Please try the desktop power menu.')
    return {'ok': True, 'action': action}
