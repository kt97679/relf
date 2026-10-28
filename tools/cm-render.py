#!/usr/bin/env python3
"""tools/cm-render.py SCRIPT.cm [s2=1,s9=1,...] - a script in the command model's syntax, printed in a
genome's (Iteration 865).

tools/cmc.py reads the script into its tree; this prints the tree in the concrete syntax the genome
names (cm/genes.tsv): s2 `var x = v`, s7 `(cmd)` captures in words, s8 `{x}` in quoted texts, s9 prefix
arithmetic. A rendering is right when the genome's front end, cm/cmc.4 as tools/cm-genes.py makes it,
reads it back into the same tree - so the Forth it makes is cmc.py's for the original, token for token;
tools/cm-syntax-search.py checks that. Comments are not kept. Prints the text, and on standard error a
count of the characters the syntax made special - escaped, or a ${name} - its hazard count.
"""
import importlib.util, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('cmc', os.path.join(ROOT, 'tools', 'cmc.py'))
cmc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cmc)

class Unrenderable(Exception):
    pass

PREC = {'||': 1, '&&': 2, '==': 3, '!=': 3, '<': 3, '<=': 3, '>': 3, '>=': 3, '+': 4, '-': 4, '*': 5, '/': 5, '%': 5}

class Printer:
    def __init__(self, g):
        self.g, self.escapes = g, 0

    # ---- texts
    def bare(self, s, first, alone, prev_text, closer):
        """A text piece, bare, with \\ before whatever this syntax would read otherwise - here: closer ends a
        word inside a list, a key or a capture; [ { } @ # begin something at a word's start."""
        if prev_text:                                   # two texts side by side stay two pieces: quote the second
            if "'" in s: raise Unrenderable("two texts side by side, the second holding '")
            self.escapes += 2; return "'" + s + "'"
        if s == '':
            return "''"
        special = set(' \t\n\r;"\'$\\') | ({closer} if closer else set())
        if self.g.get('s7'): special.add('(')
        out = []
        for i, ch in enumerate(s):
            esc = ch in special or (i == 0 and first and (ch in '[{}@#' or (ch == '(' and s[1:2] == '(')))
            if esc: self.escapes += 1; out.append('\\' + ch)
            else: out.append(ch)
        t = ''.join(out)
        if t != s and "'" not in s:                     # a text that needs escapes: quoted, once
            self.escapes -= len(t) - len(s) - 1; t = "'" + s + "'"
        if alone and t == s and (re.fullmatch(r'-?\d+', s) or s in ('true', 'false')):
            self.escapes += 1; t = '\\' + s
        return t

    def quoted(self, pieces):
        out = []
        for i, p in enumerate(pieces):
            if p[0] == 't':
                for ch in p[1]:
                    if ch in '\\"': out.append('\\' + ch); self.escapes += 1
                    elif ch == '\n': out.append('\\n')
                    elif ch == '\t': out.append('\\t')
                    elif ch == '$' and not self.g.get('s8'): out.append('\\$'); self.escapes += 1
                    elif ch == '{' and self.g.get('s8'): out.append('\\{'); self.escapes += 1
                    else: out.append(ch)
            elif self.g.get('s8'):                       # {x}, {(cmd)}, {((e))}
                out.append('{' + self.subst(p, braces=True) + '}')
            else:
                nxt = pieces[i + 1] if i + 1 < len(pieces) else None
                out.append(self.dollar(p, nxt))
        return '"' + ''.join(out) + '"'

    # ---- $ substitutions
    def var(self, p, nxt):
        name, keys = p[1], p[2]
        s = '$' + name + ''.join('[' + self.word(k, closer=']') + ']' for k in keys)
        if nxt is not None and nxt[0] == 't' and nxt[1][:1] and (re.match(r'[A-Za-z0-9_\[]', nxt[1][0])):
            if keys: raise Unrenderable('$x[k] before a [')
            self.escapes += 1; s = '${' + name + '}'
        return s

    def dollar(self, p, nxt):
        if p[0] == 'v': return self.var(p, nxt)
        if p[0] == 'cap': return '$(' + self.cmds(p[1]) + ')'
        if p[0] == 'ar': return '$((' + self.arith(p) + '))'
        if p[0] == 't' and p[1] == '$': return '$'
        raise Unrenderable('a %s inside a quoted text' % p[0])

    def subst(self, p, braces):
        """Inside {...} of s8: a name, (cmd) or ((e)) - the $ left out."""
        if p[0] == 'v': return p[1] + ''.join('[' + self.word(k, closer=']') + ']' for k in p[2])
        if p[0] == 'cap': return '(' + self.cmds(p[1]) + ')'
        if p[0] == 'ar': return '((' + self.arith(p) + '))'
        raise Unrenderable('a %s inside {}' % p[0])

    # ---- arithmetic: cmc.py keeps its text; read it into a tree
    def arith(self, p):
        r, toks = cmc.Reader(p[1], p[2]), []
        while True:
            while r.peek() in (' ', '\t', '\n', '\r'): r.get()
            c = r.peek()
            if c == '': break
            if c.isdigit():
                d = []
                while r.peek().isdigit(): d.append(r.get())
                toks.append(('num', int(''.join(d))))
            elif c == '$':
                r.get(); toks.append(('val', cmc.parse_dollar(r)))
            elif c + r.peek(1) in ('==', '!=', '<=', '>=', '&&', '||'):
                toks.append(('op', r.get() + r.get()))
            else:
                toks.append(('op', r.get()))
        pos = [0]
        def peek(): return toks[pos[0]][1] if pos[0] < len(toks) and toks[pos[0]][0] == 'op' else None
        def take(): pos[0] += 1; return toks[pos[0] - 1]
        def primary():
            t = take()
            if t[0] in ('num', 'val'): return t
            if t[1] == '(':
                e = level(1)
                take(); return e
            return ('un', t[1], primary())
        def level(n):
            if n == 6: return primary()
            e = level(n + 1)
            while peek() in PREC and PREC[peek()] == n:
                op = take()[1]; e = ('bin', op, e, level(n + 1))
                if n == 3: break                         # one comparison, as cmc.py reads it
            return e
        tree = level(1)
        return (' ' + self.prefix(tree, top=True) + ' ') if self.g.get('s9') else (' ' + self.infix(tree, 0, False) + ' ')

    def leaf(self, t):
        if t[0] == 'num': return str(t[1])
        p = t[1]
        if p[0] == 'v': return self.var(p, None)
        if p[0] == 'cap': return '$(' + self.cmds(p[1]) + ')'
        if p[0] == 'ar': return '$((' + self.arith(p) + '))'
        raise Unrenderable('a %s in (( ))' % p[0])

    def infix(self, t, ctx, right):
        if t[0] in ('num', 'val'): return self.leaf(t)
        if t[0] == 'un': return t[1] + self.infix(t[2], 6, False)
        op, n = t[1], PREC[t[1]]
        s = '%s %s %s' % (self.infix(t[2], n, False), op, self.infix(t[3], n, True))
        return '(%s)' % s if n < ctx or (n == ctx and (right or n == 3)) else s

    def prefix(self, t, top=False):
        if t[0] in ('num', 'val'): return self.leaf(t)
        if t[0] == 'un': s = '%s %s' % (t[1], self.prefix(t[2]))
        else:
            ops, a = [t[3]], t[2]                        # a left-leaning chain of one operator: one list
            while a[0] == 'bin' and a[1] == t[1] and PREC[t[1]] != 3:
                ops.append(a[3]); a = a[2]
            s = '%s %s' % (t[1], ' '.join(self.prefix(x) for x in [a] + ops[::-1]))
        return s if top else '(' + s + ')'

    # ---- words and commands
    def piece(self, p, i, pieces, cond, closer):
        k, first, alone = p[0], i == 0, len(pieces) == 1
        nxt = pieces[i + 1] if i + 1 < len(pieces) else None
        if k == 't': return self.bare(p[1], first, alone, i > 0 and pieces[i - 1][0] == 't', closer)
        if k == 'n': return str(p[1])
        if k == 'b': return 'true' if p[1] else 'false'
        if k == 'q': return self.quoted(p[1])
        if k == 'v': return self.var(p, nxt)
        if k == 'cap':
            body = self.cmds(p[1])
            if self.g.get('s7'): return '(' + (' ' if body.startswith('(') else '') + body + ')'
            return '$(' + body + ')'
        if k == 'ar': return ('((' if cond and alone else '$((') + self.arith(p) + '))'
        if k == 'list': return '[' + ' '.join(self.word(w, closer=']') for w in p[1]) + ']'
        if k == 'map':
            if not p[1]: return '[:]'
            return '[' + '  '.join('%s: %s' % (self.key(kk), self.word(w, closer=']')) for kk, w in p[1]) + ']'
        if k == 'blk':
            params = ('|' + ' '.join(p[1]) + '| ') if p[1] else ''
            return '{ ' + params + self.cmds(p[2], closer=None) + ' }'
        if k == 'spread':
            inner = p[1]
            if inner[0] == 'v': return '@' + self.var(inner, nxt)[1:]
            return '@(' + self.cmds(inner[1]) + ')'
        raise Unrenderable('a piece of kind %s' % k)

    def key(self, k):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', k): raise Unrenderable('a map key %r' % k)
        return k

    def word(self, w, closer=None, cond=False):
        return ''.join(self.piece(p, i, w, cond, closer) for i, p in enumerate(w))

    def command(self, words, closer=None):
        out, seg = [], []
        for i, w in enumerate(words):
            b = w[0][1] if len(w) == 1 and w[0][0] == 't' else None
            if b in ('&&', '||', '|'):
                out += self.segment(seg, closer) + [b]; seg = []
            else:
                seg.append(w)
        out += self.segment(seg, closer)
        return ' '.join(out)

    def segment(self, seg, closer):
        out = []
        for i, w in enumerate(seg):
            prev = seg[i - 1][0][1] if i and len(seg[i - 1]) == 1 and seg[i - 1][0][0] == 't' else None
            out.append(self.word(w, closer, cond=prev in ('if', 'while', 'elif', '!')))
            if (self.g.get('s2') and i == 1 and len(seg) == 3 and len(seg[0]) == 1 and seg[0][0][0] == 't'
                    and seg[0][0][1] in ('var', 'set')):
                out.append('=')
        return out

    def cmds(self, cmds, sep='; ', closer=')'):
        return sep.join(self.command(words, closer) for line, words in cmds)

def render(text, g):
    p = Printer(g)
    return p.cmds(cmc.parse_cmds(cmc.Reader(text), None, set()), sep='\n', closer=None) + '\n', p.escapes

def genome(spec):
    g = {}
    for item in filter(None, spec.split(',')):
        k, v = item.split('='); g[k] = int(v)
    return g

if __name__ == '__main__':
    if len(sys.argv) not in (2, 3):
        sys.stderr.write('usage: cm-render.py SCRIPT.cm [s2=1,...]\n'); sys.exit(2)
    try:
        out, esc = render(open(sys.argv[1], encoding='utf-8').read(), genome(sys.argv[2] if len(sys.argv) > 2 else ''))
    except (Unrenderable, cmc.CmError) as e:
        sys.stderr.write('cm-render: %s: %s\n' % (sys.argv[1], e)); sys.exit(1)
    sys.stdout.write(out); sys.stderr.write('escapes %d\n' % esc)
