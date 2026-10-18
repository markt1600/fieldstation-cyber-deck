"""Single serial reader shared by all dashboard requests."""
import threading
import time
import struct

_lock = threading.Lock()
_reading = None
_started = False

def parse_frame(frame):
    if len(frame) != 32 or frame[:4] != b'\x42\x4d\x00\x1c':
        return None
    if sum(frame[:-2]) != int.from_bytes(frame[-2:], 'big') or frame[29]:
        return None
    pm = struct.unpack('>3H', frame[10:16])
    return dict(zip(('pm1', 'pm25', 'pm10'), pm))

def status():
    with _lock:
        reading = dict(_reading) if _reading else None
    if not reading:
        return {'status': 'waiting', 'readings': None}
    age = max(0, time.time() - reading.pop('timestamp'))
    return {'status': 'live' if age < 15 else 'stale',
            'age_seconds': round(age, 1), 'readings': reading, 'unit': 'µg/m³'}

def start():
    global _started
    if _started: return
    _started = True
    threading.Thread(target=_read, daemon=True, name='PMS7003').start()

def _read():
    global _reading
    try:
        import serial
    except ImportError:
        return
    while True:
        try:
            with serial.Serial('/dev/ttyAMA0', 9600, timeout=1, exclusive=True) as port:
                buf = bytearray()
                while True:
                    buf.extend(port.read(min(port.in_waiting or 1, 4096)))
                    while len(buf) >= 4:
                        i = buf.find(b'\x42\x4d')
                        if i < 0:
                            buf[:] = buf[-1:]
                            break
                        del buf[:i]
                        if len(buf) < 4: break
                        if buf[2:4] != b'\x00\x1c':
                            del buf[0]
                            continue
                        if len(buf) < 32: break
                        reading = parse_frame(bytes(buf[:32]))
                        if reading is None:
                            del buf[0]
                            continue
                        del buf[:32]
                        reading['timestamp'] = time.time()
                        with _lock: _reading = reading
        except (OSError, serial.SerialException):
            time.sleep(5)
