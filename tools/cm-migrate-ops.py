#!/usr/bin/env python3
"""tools/cm-migrate-ops.py - a rill3 script from 966's builtins to 967's value operations, and from 975's
element builtins to 976's.

Iteration 967 made a value the command and the operation its subcommand: `count $l` is `$l count`,
`has $m k` is `$m has k`, `join , @l` is `$l join ,`, and so for slice, keys, merge, split, upper, lower
and match. This rewrites the commands whose first word is one of those - at a line's start, after ; | && ||
or !, as if's, elif's or while's condition, inside $( ) @( ) blocks and double quotes - and leaves the rest
of the text as it was. A text as a command, $EDITOR file, is now run $EDITOR file: that a value is a text is
not known before the script runs, so those are not rewritten.

Iteration 976 made changing a list or a map its operations too: `set m[k] v` is `$m set k v`, `set
m[a][b] v` is `$m[a] set b v`, `append l x y` is `$l append x y`, `del m[k]` is `$m del k` - `set env[N] v`
and `del env[N]` so, `$env set N v`, `$env del N`. `set name v` stays: it changes a variable. `read
name[k]` has no one-line form - `read line`, then `$name set k $line` - so it is named, not rewritten.

    python3 tools/cm-migrate-ops.py file...           each file rewritten in place, the ones changed named
    python3 tools/cm-migrate-ops.py --check file...   the files it would change, nothing written: status 1 if any
    python3 tools/cm-migrate-ops.py --976 file...     976's rewrites only - for a script 967's left as it is
"""
import re
import sys

MOVED = {'count', 'has', 'slice', 'join', 'keys', 'merge', 'split', 'upper', 'lower', 'match'}
ARITY = {'count': (1, 1), 'keys': (1, 1), 'upper': (1, 1), 'lower': (1, 1), 'has': (2, 2), 'merge': (2, 2),
         'split': (2, 2), 'match': (2, 2), 'slice': (2, 3)}
ELEMENT = {'set', 'append', 'del', 'read'}
NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*(?:-[A-Za-z0-9_]+)*')
REDIR = re.compile(r'^(\d*>>?|\d*<|&>|<<)')
problems = []


def scan_word(s, i, close):
    """One word from i: its text, rewritten inside, and where it ends."""
    n, out = len(s), []
    while i < n:
        c = s[i]
        if c in ' \t\n;' or (close and c == close):
            break
        if c == '\\':
            if i + 1 < n and s[i + 1] == '\n':
                break
            out.append(s[i:i + 2]); i += 2; continue
        if c == "'":
            j = s.find("'", i + 1)
            j = n - 1 if j < 0 else j
            out.append(s[i:j + 1]); i = j + 1; continue
        if c == '"':
            t, i = scan_dq(s, i); out.append(t); continue
        if s.startswith('$((', i):
            t, i = scan_arith(s, i); out.append(t); continue
        if s.startswith('$(', i) or s.startswith('@(', i):
            t, i = scan_seq(s, i + 2, ')'); out.append(c + '(' + t + ')'); i += 1; continue
        if c == '[':
            t, i = scan_list(s, i + 1); out.append('[' + t + ']'); i += 1; continue
        if c == '{':
            t, i = scan_block(s, i); out.append(t); continue
        out.append(c); i += 1
    return ''.join(out), i


def scan_dq(s, i):
    n, out = len(s), ['"']
    i += 1
    while i < n and s[i] != '"':
        if s[i] == '\\':
            out.append(s[i:i + 2]); i += 2; continue
        if s.startswith('$((', i):
            t, i = scan_arith(s, i); out.append(t); continue
        if s.startswith('$(', i):
            t, i = scan_seq(s, i + 2, ')'); out.append('$(' + t + ')'); i += 1; continue
        out.append(s[i]); i += 1
    out.append('"')
    return ''.join(out), i + 1


def scan_arith(s, i):
    n, out, depth = len(s), ['$(('], 0
    i += 3
    while i < n:
        if s.startswith('))', i) and depth == 0:
            out.append('))'); return ''.join(out), i + 2
        if s.startswith('$((', i):
            t, i = scan_arith(s, i); out.append(t); continue
        if s.startswith('$(', i):
            t, i = scan_seq(s, i + 2, ')'); out.append('$(' + t + ')'); i += 1; continue
        if s[i] == '"':
            t, i = scan_dq(s, i); out.append(t); continue
        depth += {'(': 1, ')': -1}.get(s[i], 0)
        out.append(s[i]); i += 1
    return ''.join(out), i


def scan_list(s, i):
    """A list's or an index's insides, to its ]: words, none a command."""
    n, out = len(s), []
    while i < n and s[i] != ']':
        if s[i] in ' \t\n':
            out.append(s[i]); i += 1; continue
        if s[i] == '#':
            j = s.find('\n', i); j = n if j < 0 else j
            out.append(s[i:j]); i = j; continue
        t, j = scan_word(s, i, ']')
        if j == i:
            out.append(s[i]); i += 1; continue
        out.append(t); i = j
    return ''.join(out), i


def scan_block(s, i, arms=False):
    """A block from its {: its parameters, its commands - or, a case's, its arms - to its }."""
    j = i + 1
    head = '{'
    m = re.match(r'[ \t]*\|[^|\n]*\|', s[j:])
    if m:
        head += m.group(0); j += m.end()
    t, j = scan_seq(s, j, '}', arms)
    return head + t + '}', j + 1


def scan_seq(s, i, close, arms=False):
    """Commands from i to the unmatched close: their text, rewritten, and where close is."""
    n = len(s)
    toks = []
    heredocs = []          # the delimiters of here-documents begun on this line
    first = None           # the command's first word, so far
    after_hd = False
    while i < n:
        c = s[i]
        if close and c == close:
            break
        if c in ' \t':
            j = i
            while j < n and s[j] in ' \t':
                j += 1
            toks.append(('ws', s[i:j])); i = j; continue
        if c == '\\' and i + 1 < n and s[i + 1] == '\n':
            toks.append(('ws', '\\\n')); i += 2; continue
        if c == '\n':
            toks.append(('nl', '\n')); i += 1; first = None
            for d, quoted in heredocs:               # a here-document's lines - its $( )s, unless its END quoted
                while i < n:
                    j = s.find('\n', i); j = n if j < 0 else j + 1
                    if s[i:j].strip() == d:
                        toks.append(('ws', s[i:j])); i = j
                        break
                    if quoted:
                        toks.append(('ws', s[i:j])); i = j; continue
                    out = []
                    while i < j:
                        if s[i] == '\\':
                            out.append(s[i:i + 2]); i += 2
                        elif s.startswith('$((', i):
                            t, i = scan_arith(s, i); out.append(t)
                        elif s.startswith('$(', i):
                            t, i = scan_seq(s, i + 2, ')'); out.append('$(' + t + ')'); i += 1
                        else:
                            out.append(s[i]); i += 1
                    toks.append(('ws', ''.join(out)))
            heredocs = []
            continue
        if c == '#':
            j = s.find('\n', i); j = n if j < 0 else j
            toks.append(('ws', s[i:j])); i = j; continue
        if c == ';' or s.startswith('&&', i) or s.startswith('||', i) or c in '|&':
            k = 2 if s.startswith('&&', i) or s.startswith('||', i) else 1
            toks.append(('sep', s[i:i + k])); i += k; first = None; continue
        start = i
        if c == '{' and first == 'case':
            w, i = scan_block(s, i, arms=True)
        else:
            w, i = scan_word(s, i, close)
        if i == start:
            toks.append(('ws', c)); i += 1; continue
        toks.append(('word', w, start))
        if first is None:
            first = w
        if after_hd:
            heredocs.append((w.strip('\'"'), w[:1] in '\'"')); after_hd = False
        elif w.startswith('<<'):
            d = w[2:].lstrip('-')
            if d:
                heredocs.append((d.strip('\'"'), d[:1] in '\'"'))
            else:
                after_hd = True
    return rewrite(s, toks, arms), i


def value_word(w):
    """A word as a command's first, a value: a bare one quoted; a spread, its one value - a spread
    was its words, and count, has... took the one value it held."""
    if w.startswith('@('):
        return '[' + w + '][0]'
    if w.startswith('@'):
        return '$' + w[1:] + '[0]'
    if w[:1] in '$"\'[{':
        return w
    return "'" + w + "'" if "'" not in w else '"' + w + '"'


def transform(words, line):
    """The words of one command, the first a moved builtin's name: its words now, or None."""
    name, args = words[0], words[1:]
    redir = []
    for k, a in enumerate(args):
        if REDIR.match(a):
            redir, args = args[k:], args[:k]
            break
    if name == 'join':
        if not args:
            problems.append('%d: join with no separator' % line); return None
        sep, items = args[0], args[1:]
        if len(items) == 1 and items[0].startswith('@') and not items[0].startswith('@('):
            lst = '$' + items[0][1:]
        else:
            lst = '[' + ' '.join(items) + ']'
        return [lst, 'join', sep] + redir
    lo, hi = ARITY[name]
    if not lo <= len(args) <= hi:
        problems.append('%d: %s given %d words' % (line, name, len(args))); return None
    return [value_word(args[0]), name] + args[1:] + redir


def split_target(w):
    """name[k1]...[kn]: the name and the keys' words - or None, when w is not a name and its keys."""
    m = NAME.match(w)
    if not m:
        return None
    name, rest, keys, i = m.group(0), w[m.end():], [], 0
    while i < len(rest):
        if rest[i] != '[':
            return None
        j, depth = i + 1, 0
        while j < len(rest):
            c = rest[j]
            if c == "'":
                k = rest.find("'", j + 1)
                if k < 0:
                    return None
                j = k + 1; continue
            if c == '"':
                k = j + 1
                while k < len(rest) and rest[k] != '"':
                    k += 2 if rest[k] == '\\' else 1
                j = k + 1; continue
            if c in '[(':
                depth += 1
            elif c in '])':
                if depth == 0:
                    if c == ')':
                        return None
                    break
                depth -= 1
            j += 1
        if j >= len(rest):
            return None
        keys.append(rest[i + 1:j]); i = j + 1
    return name, keys


def transform976(words, line):
    """set name[k].. v, append name values, del name[k]..: their words as operations now, or None."""
    name, args = words[0], words[1:]
    if not args:
        return None
    t = split_target(args[0])
    if t is None:
        return None
    var, keys = t
    if name == 'read':
        if keys:
            problems.append('%d: read %s - read line, then $%s set %s $line' % (line, args[0], var, keys[-1]))
        return None
    if name == 'append':
        return ['$' + args[0], 'append'] + args[1:]
    if not keys:
        return None
    last = keys[-1]
    if re.match(r'^[^$\'"\[{@]*[*?]', last):
        problems.append('%d: %s %s - its key a glob as a word' % (line, name, args[0])); return None
    value = '$' + var + ''.join('[' + k + ']' for k in keys[:-1])
    if name == 'del':
        if len(args) != 1:
            problems.append('%d: del given %d words' % (line, len(args))); return None
        return [value, 'del', last]
    return [value, 'set', last] + args[1:]


def rewrite(s, toks, arms):
    out, cmd = [], []
    for t in toks + [('nl', '')]:
        if t[0] in ('nl', 'sep'):
            if cmd:
                out.extend(rewrite_cmd(s, cmd, arms))
            cmd = []
            out.append(t[1])
        else:
            cmd.append(t)
    return ''.join(out)


def rewrite_cmd(s, cmd, arms):
    """One command's tokens: the moved builtins in it - its first word's, a condition's - rewritten."""
    if arms:
        return [t[1] for t in cmd]
    wi = [k for k, t in enumerate(cmd) if t[0] == 'word']
    ws = [cmd[k][1] for k in wi]

    def past_bangs(j):
        while j < len(ws) and ws[j] == '!':
            j += 1
        return j
    starts = []
    j = past_bangs(0)
    if j < len(ws):
        starts.append(j)
        if ws[j] in ('if', 'while') and past_bangs(j + 1) < len(ws):
            starts.append(past_bangs(j + 1))
    for k in range(1, len(ws)):
        if ws[k] == 'elif' and ws[k - 1].startswith('{') and past_bangs(k + 1) < len(ws):
            starts.append(past_bangs(k + 1))
    texts = [t[1] for t in cmd]
    for st in sorted(set(starts), reverse=True):
        if ws[st] in ELEMENT and st == starts[0]:
            new = transform976(ws[st:], s.count('\n', 0, cmd[wi[st]][2]) + 1)
            if new is not None:
                texts[wi[st]:wi[-1] + 1] = [' '.join(new)] + [''] * (wi[-1] - wi[st])
            continue
        if ws[st] not in MOVED or ONLY976:
            continue
        end = st + 1
        while end < len(ws) and not ws[end].startswith('{'):
            end += 1
        new = transform(ws[st:end], s.count('\n', 0, cmd[wi[st]][2]) + 1)
        if new is None:
            continue
        texts[wi[st]:wi[end - 1] + 1] = [' '.join(new)] + [''] * (wi[end - 1] - wi[st])
    return texts


def migrate(text):
    t, i = scan_seq(text, 0, None)
    return t + text[i:]


ONLY976 = False


def main(argv):
    global ONLY976
    if argv[:1] == ['--976']:
        ONLY976, argv = True, argv[1:]
    check = argv[:1] == ['--check']
    files = argv[1:] if check else argv
    changed = 0
    for f in files:
        old = open(f).read()
        del problems[:]
        new = migrate(old)
        for p in problems:
            print('%s:%s - left as it was' % (f, p), file=sys.stderr)
        if new != old:
            changed += 1
            print(f)
            if not check:
                open(f, 'w').write(new)
    return 1 if check and changed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
