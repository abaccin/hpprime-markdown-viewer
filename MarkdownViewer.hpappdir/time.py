from hpprime import ticks as _ticks

dt = 0
_last = 0

def init():
  global _last, dt
  dt = 0
  _last = _ticks()

def update():
  global _last, dt
  now = _ticks()
  dt = (now - _last) / 1000.0
  _last = now
