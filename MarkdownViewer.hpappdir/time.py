from hpprime import *

dt = 0
_last = 0

def init():
  global _last, dt
  dt = 0
  _last = eval('ticks()')

def update():
  global _last, dt
  now = eval('ticks()')
  dt = (now - _last) / 1000.0
  _last = now
