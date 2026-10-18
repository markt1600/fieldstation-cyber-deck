#!/usr/bin/env python3
"""Follow the master knob with smooth bass compensation; keep EQ headroom."""
import json
import re
import subprocess
import time
import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'fieldstation'))
import audio_settings

def run(*args):
    return subprocess.check_output(args, text=True, timeout=3)

def boost_for_volume(volume, settings=None):
    settings = settings or audio_settings.DEFAULTS
    if settings['mode']=='always':
        return settings['bass_db']
    x=max(0.0,min(1.0,(volume-0.20)/0.60))
    return settings['bass_db']*(1-x*x*(3-2*x))

def main():
    node = None
    gain = 0.0
    last_gain = None
    last_freq = None
    frequency = 120.0
    next_discover = 0
    while True:
        try:
            if time.monotonic() >= next_discover:
                objects = json.loads(run('pw-dump'))
                nodes = {o.get('info',{}).get('props',{}).get('node.name'):o['id']
                         for o in objects if o['type'] == 'PipeWire:Interface:Node'}
                new_node = nodes.get('fieldstation_dsp')
                if new_node is None:
                    node = None
                    time.sleep(1)
                    continue
                if new_node != node:
                    physical = nodes['alsa_output.platform-soc_107c000000_sound.stereo-fallback']
                    current = run('wpctl','get-volume','@DEFAULT_AUDIO_SINK@')
                    volume = re.search(r'Volume: ([0-9.]+)',current).group(1)
                    run('wpctl','set-volume',str(new_node),volume)
                    run('wpctl','set-mute',str(new_node),'1' if 'MUTED' in current else '0')
                    run('wpctl','set-default',str(new_node))
                    run('wpctl','set-volume',str(physical),'1.0')
                    node = new_node
                    last_gain = None
                    print('DSP default output ready',flush=True)
                next_discover = time.monotonic()+5
            volume=float(re.search(r'Volume: ([0-9.]+)',run('wpctl','get-volume',str(node))).group(1))
            settings=audio_settings.read()
            target=boost_for_volume(volume,settings)
            frequency += 0.18*(settings['frequency_hz']-frequency)
            if abs(settings['frequency_hz']-frequency)<0.1:
                frequency=settings['frequency_hz']
            gain += 0.18*(target-gain)
            if abs(target-gain)<0.01:
                gain=target
            if last_gain is None or abs(last_gain-gain)>0.02 or (gain==target and gain!=last_gain) or last_freq is None or abs(last_freq-frequency)>0.1:
                params={'bassL:Gain':round(gain,3),'bassR:Gain':round(gain,3),
                        'preL:Gain':round(-gain-1,3),'preR:Gain':round(-gain-1,3)}
                params.update({'bassL:Freq':round(frequency,2),'bassR:Freq':round(frequency,2)})
                # SPA Props params is an alternating key/value structure.
                pairs=' '.join(json.dumps(k)+' '+str(v) for k,v in params.items())
                run('pw-cli','set-param',str(node),'Props','{ params = [ '+pairs+' ] }')
                last_gain=gain
                last_freq=frequency
            time.sleep(0.10)
        except (subprocess.SubprocessError,ValueError,KeyError,AttributeError) as exc:
            print('Waiting for audio: '+str(exc),flush=True)
            node=None
            next_discover=0
            time.sleep(2)

if __name__=='__main__':
    main()
