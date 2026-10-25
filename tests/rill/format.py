# tests/rill/format.rill in Python: its expected output
print('%5d|%-5d|%05d|%+d|% d|%d' % (42, 42, 42, 42, 42, -7))
print('%x %X %5x %-6X| %x %.4d' % (255, 255, 4096, 171, -255, 12))
print('%.3f|%8.2f|%-8.1f|%08.3f|%.0f|%f' % (3.14159, 2.5, -1.26, -3.5, 7.7, 0.1))
print('%s|%10s|%-10s|%.2s|%5.1s|' % ('abc', 'right', 'left', 'truncate', 'xyz'))
print('%s has %d items (%.1f%%)' % ('list', 3, 42.857))
print('%s and %s' % (42, 2.5))
print('no conversions at all')
rows = [['alpha', 1.5, 3], ['beta', 12.25, 41], ['gamma-delta', 0.333, 7]]
for r in rows: print('%-11s %8.3f %4d' % (r[0], r[1], r[2]))
n = 3
t = '%d%%' % (n * 10)
print(t, len(t))
print('%+.2f %+d % .1f' % (1.006, 0, 2.24))
