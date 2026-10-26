# tests/rill/from-json.rill's output, by Python's json and Rill's two rules (null an empty text; six places, truncated)
import json
from decimal import Decimal, ROUND_DOWN
def conv(x):
    if x is None: return ''
    if isinstance(x, bool): return x
    if isinstance(x, float): return Decimal(repr(x)).quantize(Decimal('0.000001'), rounding=ROUND_DOWN)
    if isinstance(x, list): return [conv(i) for i in x]
    if isinstance(x, dict): return {k: conv(v) for k, v in x.items()}
    return x
def dtext(d):
    s = format(d, 'f').rstrip('0'); return s + '0' if s.endswith('.') else s
def show(x):
    return ('true' if x else 'false') if isinstance(x, bool) else dtext(x) if isinstance(x, Decimal) else str(x)
def dumps(x):
    if isinstance(x, (bool, Decimal)): return show(x)
    if isinstance(x, list): return '[' + ','.join(dumps(i) for i in x) + ']'
    if isinstance(x, dict): return '{' + ','.join(json.dumps(k, ensure_ascii=False) + ':' + dumps(v) for k, v in x.items()) + '}'
    return json.dumps(x, ensure_ascii=False)
t = r'{"name": "relf", "n": 3, "pi": 3.14159, "ok": true, "off": false, "none": null, "tags": ["a", "b\u00e9\ud83d\ude00"], "deep": {"x": [1, [2, {"y": -0.5}]]}}'
v = conv(json.loads(t))
print(*[show(v[k]) for k in ('name', 'n', 'pi', 'ok', 'off')], '[%s]' % v['none'], len(v['tags']), v['tags'][1], show(v['deep']['x'][1][1]['y']))
print(dumps(v))
nums = conv(json.loads('[0, -7, 9223372036854775807, 1e3, 2.5E+2, -1.25e-2, 0.1234567, 1.0, 10]'))
print(dumps(nums))
print(nums[2] - 1, show(nums[3] + 1), show(nums[6] * 2))
w = conv(json.loads(r' [ {"k": "v", "k": "w", "a b": [ ] , "q\"": {}} ] '))
print(dumps(w), len(w[0]), w[0]['k'])
r = {'name': 'x', 'a "q"': [1, Decimal('2.5'), True], 'ctl': 'a\tb\n\x01'}
print(dumps(r))
print(dumps('plain'), dumps(42), dumps(Decimal('-1.5')), dumps(False), dumps([]), dumps({}))
print('true')
