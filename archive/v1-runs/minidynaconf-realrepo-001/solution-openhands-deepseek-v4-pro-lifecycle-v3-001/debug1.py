import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minidynaconf import MiniDynaconf

s = MiniDynaconf(defaults={'host': 'localhost', 'port': 5432})
print('_data:', s._effective._data)
print('exists host:', s._effective.exists('host'))
print('get host:', s._effective.get('host'))

try:
    print('attr host:', s.host)
except AttributeError as e:
    print('attr FAILED:', e)
