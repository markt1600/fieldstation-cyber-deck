"""Read-only X1202 gauge monitoring. No charging or shutdown control."""
from collections import deque
from contextlib import closing
import threading
import time
import sqlite3
import subprocess
from pathlib import Path

LOG_PATH=Path.home()/'.local/state/fieldstation/battery-history.sqlite3'
_tracking={'saved_samples':0,'started_at':None,'last_saved_at':None,'error':None}

def init_log():
    LOG_PATH.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(LOG_PATH)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS samples (timestamp REAL PRIMARY KEY, voltage_v REAL, reported_percent REAL, status TEXT NOT NULL)')
        rows=db.execute('SELECT timestamp,voltage_v,reported_percent FROM samples WHERE status=? ORDER BY timestamp DESC LIMIT 360',('ok',)).fetchall()
        count,first,last=db.execute('SELECT count(*),min(timestamp),max(timestamp) FROM samples').fetchone()
    with _lock:
        _history.extend({'timestamp':t,'voltage_v':v,'reported_percent':p} for t,v,p in reversed(rows))
        _tracking.update(saved_samples=count,started_at=first,last_saved_at=last,error=None)

def save_sample(reading, timestamp):
    with closing(sqlite3.connect(LOG_PATH)) as db, db:
        db.execute('INSERT INTO samples VALUES (?,?,?,?)',(timestamp,reading['voltage_v'] if reading else None,reading['reported_percent'] if reading else None,'ok' if reading else 'read_error'))
    with _lock:
        _tracking['saved_samples']+=1
        _tracking['started_at']=_tracking['started_at'] or timestamp
        _tracking['last_saved_at']=timestamp
        _tracking['error']=None
        if reading:_history.append(dict(reading))

_lock=threading.Lock()
_reading=None
_power=None
_power_timestamp=None
_power_connected_since=None
_history=deque(maxlen=360)
_started=False

def decode(raw):
    if len(raw)!=4: raise ValueError('Incomplete gauge reading')
    voltage=((raw[0]<<8)|raw[1])*1.25/1000/16
    charge=((raw[2]<<8)|raw[3])/256
    if not 0 < voltage < 5.5 or not 0 <= charge <= 110:
        raise ValueError('Gauge reading outside supported range')
    return {'voltage_v':round(voltage,4),'reported_percent':round(charge,3)}

def status():
    with _lock:
        reading=dict(_reading) if _reading else None
        history=list(_history)
        tracking=dict(_tracking)
        power=_power if _power_timestamp and time.time()-_power_timestamp<20 else None
        connected_since=_power_connected_since if power is True else None
    age=max(0,time.time()-reading['timestamp']) if reading else None
    return {'status':'waiting' if age is None else ('live' if age<20 else 'stale'),
            'age_seconds':round(age,1) if age is not None else None,
            'external_power':power,'power_connected_since':connected_since,'power_source':'X1202 GPIO6','verified':False,'readings':reading,'history':history,'tracking':tracking}

def start():
    global _started
    if _started:return
    _started=True
    threading.Thread(target=_run,daemon=True,name='X1202-readonly').start()

def _run():
    global _reading, _power, _power_timestamp, _power_connected_since
    try:
        from smbus2 import SMBus
    except ImportError:return
    log_ready=False
    next_save=0
    while True:
        reading=None
        try:
            result=subprocess.run(['gpioget','-c','gpiochip0','--bias','disabled','--numeric','GPIO6'],capture_output=True,text=True,timeout=2)
            value=result.stdout.strip() if result.returncode==0 else ''
            with _lock:
                observed={'1':True,'0':False}.get(value)
                observed_at=time.time()
                if observed is not True:
                    _power_connected_since=None
                elif _power is not True or not _power_timestamp or observed_at-_power_timestamp>=20:
                    _power_connected_since=observed_at
                _power=observed
                _power_timestamp=observed_at
        except (OSError,subprocess.SubprocessError):
            with _lock:
                _power=None
                _power_connected_since=None
        try:
            with SMBus(1) as bus:
                reading=decode(bus.read_i2c_block_data(0x36,2,4))
            reading['timestamp']=time.time()
            with _lock:
                _reading=reading
        except (OSError,ValueError):
            pass
        if time.monotonic()>=next_save:
            try:
                if not log_ready:
                    init_log()
                    log_ready=True
                save_sample(reading,time.time())
            except (OSError,sqlite3.Error):
                with _lock:_tracking['error']='Unable to save battery history'
            next_save=time.monotonic()+30
        time.sleep(5)
