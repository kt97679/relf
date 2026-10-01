#!/usr/bin/env python3
"""tests/interactive/width-probe.py - wide and zero-width characters.

Runs with the pty suite, like search-probe.py and complete-probe.py. The
editor moves the cursor by columns (CSI n D), and a character's columns
are not one: CJK and emoji take two, combining marks none (Iteration
604; before, every character took one, and each wide one put the cursor
a column off). pty_session's render counts one column a character, so
it cannot see this; this follows the editor's own movements with each
character's real width - unicodedata's, as a terminal would - and checks
where the cursor ends up, after the prompt and the text before it.
Exit status is the number of checks that failed.
"""
import os, pty, re, select, sys, time, unicodedata

SHELL = os.path.abspath(os.environ.get('THIS_SH', os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'relfsh')).split()[0])


def width(ch):
    if unicodedata.combining(ch) or unicodedata.category(ch) in ('Mn', 'Me') \
            or ch in '\u200b\u200c\u200d\u200e\u200f\u2060\ufeff':
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1


def cursor_column(out):
    """The cursor's column on the last line, after these bytes."""
    col = 0
    i = 0
    s = out
    while i < len(s):
        c = s[i]
        if c == '\x1b':
            m = re.match(r'\x1b\[(\d*)([A-Za-z])', s[i:])
            if m:
                n = int(m.group(1) or 1)
                if m.group(2) == 'D':
                    col = max(0, col - n)
                elif m.group(2) == 'C':
                    col += n
                i += m.end()
                continue
            i += 1
            continue
        if c in '\r\n':
            col = 0
        elif c == '\x08':
            col = max(0, col - 1)
        elif c >= ' ':
            col += width(c)
        i += 1
    return col


def session(ps1, keys):
    pid, fd = pty.fork()
    if pid == 0:
        os.execve(SHELL, [SHELL, '-i'], {'PATH': '/usr/bin:/bin', 'PS1': ps1, 'TERM': 'dumb',
                                         'HOME': '/tmp', 'LANG': 'C.UTF-8'})
    out = b''

    def rd(t):
        nonlocal out
        end = time.time() + t
        while True:
            left = end - time.time()
            if left <= 0:
                return
            r, _, _ = select.select([fd], [], [], left)
            if r:
                try:
                    out += os.read(fd, 65536)
                except OSError:
                    return
    rd(0.5)
    start = len(out)
    for k in keys:
        os.write(fd, k.encode('utf-8'))
        rd(0.15)
    try:
        os.kill(pid, 9)
        os.waitpid(pid, 0)
    except OSError:
        pass
    return out[start:].decode('utf-8', 'replace')


LEFT, BS = '\x1b[D', '\x7f'
# (name, PS1, keys, the cursor's expected column: the prompt's width
# plus the columns of the text before the cursor)
cases = [
    ('CJK typed: the cursor after it', '$ ', ['漢', '字'], 2 + 4),
    ('CJK, Left: back over a two-column character', '$ ', ['漢', '字', LEFT], 2 + 2),
    ('CJK, two Lefts and an insert', '$ ', ['漢', '字', LEFT, LEFT, 'a'], 2 + 1),
    ('CJK, Backspace takes two columns', '$ ', ['漢', '字', BS], 2 + 2),
    ('emoji, Left', '$ ', ['😀', 'b', LEFT], 2 + 2),
    ('a combining mark takes no column', '$ ', ['e', '\u0301', 'x', LEFT], 2 + 1),
    ('Cyrillic still one column each', '$ ', ['ж', 'и', LEFT], 2 + 1),
    ('a wide character in the prompt', '漢$ ', ['a', 'b', LEFT], 4 + 1),
]
checks = []
for name, ps1, keys, want in cases:
    got = cursor_column(session(ps1, keys))
    checks.append(('%s (column %d, want %d)' % (name, got, want), got == want))

failed = [n for n, ok in checks if not ok]
for n in failed:
    print("FAIL width-probe: %s" % n)
print("%d width checks, %d failed" % (len(checks), len(failed)))
sys.exit(len(failed))
