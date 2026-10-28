#!/usr/bin/env python3
"""tools/cmc.py SCRIPT.cm - the command model's front end, a prototype (858).

Reads a script in the draft's syntax (docs/COMMAND-MODEL.md) and writes, on standard output, Forth
for cm's runtime - cm/rt-cm.4, out.4, ctl.4 and lib.4, loaded on rill2's image. A reference to write
tests and scripts in while the syntax settles; the in-image compiler comes after it, as rillc.py
came before Rill's.

v0 has: commands of words; var, set (and set name[key]), put, echo, append, if/elif/else, for,
while, def, break, continue, return, count, range, merge; a value as the first word (rule 11); words
of text, numbers, true and false, "..." with $ in it, '...', $name and $name[key], ${name}, $( ) and
@( ), $(( )) and (( )), @name, [lists], [maps: v], [:], and {blocks} with |params|. Every variable
lives in an upvalue - boxed - so blocks capture by reference and a loop's variable is fresh each
iteration. Not yet: programs, pipes, redirections; a def seeing the script's variables.
"""
import re, sys

class CmError(Exception):
    pass

BUILTIN = {'var', 'set', 'put', 'echo', 'append', 'if', 'for', 'while', 'def', 'break', 'continue',
           'return', 'count', 'range', 'merge', 'true', 'false'}
NAME0, NAMEC = re.compile(r'[A-Za-z_]'), re.compile(r'[A-Za-z0-9_]')

# ---------------------------------------------------------------- reading
class Reader:
    def __init__(self, text, line=1):
        self.s, self.i, self.line = text, 0, line
    def peek(self, k=0):
        j = self.i + k
        return self.s[j] if j < len(self.s) else ''
    def get(self):
        c = self.peek(); self.i += 1
        if c == '\n': self.line += 1
        return c
    def err(self, msg):
        raise CmError('line %d: %s' % (self.line, msg))

def skip_blanks(r, newlines=False):
    while True:
        while r.peek() in (' ', '\t', '\r') or (newlines and r.peek() == '\n'):
            r.get()
        if r.peek() != '#':
            return
        while r.peek() not in ('\n', ''):              # a comment: from a word's start to the line's end
            r.get()
        if not newlines:
            return

def parse_cmds(r, close, closers):
    """Commands until close (None: the text's end), each (line, [word]); a word ends at a closer."""
    cmds, words, line = [], [], r.line
    while True:
        skip_blanks(r)
        c = r.peek()
        if c == '':
            if close: r.err('%s missing' % close)
            break
        if c == close:
            r.get(); break
        if c in ('\n', ';'):
            r.get()
            if words: cmds.append((line, words)); words = []
            continue
        if not words: line = r.line
        words.append(parse_word(r, closers))
    if words: cmds.append((line, words))
    return cmds

def parse_word(r, closers):
    """One word, its pieces: until a blank, a line's end, ; or a closer."""
    c = r.peek()
    if c == '[': r.get(); return [parse_list(r)]
    if c == '{': r.get(); return [parse_block(r)]
    if c == '(' and r.peek(1) == '(': r.get(); r.get(); return [parse_arith(r)]
    if c == '@':
        r.get()
        if r.peek() == '(': r.get(); return [('spread', ('cap', parse_cmds(r, ')', {')'})))]
        if NAME0.match(r.peek() or ' '): return [('spread', parse_var(r))]
        r.err('@ spreads a name or a ( ) - not this')
    pieces, text, bare = [], [], True
    def flush():
        if text: pieces.append(('t', ''.join(text))); text.clear()
    while True:
        c = r.peek()
        if c in ('', ' ', '\t', '\r', '\n', ';') or c in closers:
            break
        if c == '"':
            r.get(); flush(); bare = False; pieces.append(('q', parse_quoted(r)))
        elif c == "'":
            r.get(); flush(); bare = False; s = []
            while r.peek() != "'":
                if r.peek() == '': r.err("' missing")
                s.append(r.get())
            r.get(); pieces.append(('t', ''.join(s)))
        elif c == '$':
            r.get(); flush(); bare = False; pieces.append(parse_dollar(r))
        elif c == '\\':
            r.get(); text.append(r.get()); bare = False
        else:
            text.append(r.get())
    flush()
    if not pieces: r.err('a word was expected, not %r' % (r.peek() or 'the end'))
    if bare and len(pieces) == 1:
        s = pieces[0][1]
        if re.fullmatch(r'-?\d+', s): return [('n', int(s))]
        if s in ('true', 'false'): return [('b', s == 'true')]
    return pieces

def parse_quoted(r):
    pieces, text = [], []
    while True:
        c = r.peek()
        if c == '': r.err('" missing')
        if c == '"': r.get(); break
        if c == '\\':
            r.get(); e = r.get(); text.append({'n': '\n', 't': '\t'}.get(e, e))
        elif c == '$':
            r.get()
            if text: pieces.append(('t', ''.join(text))); text = []
            pieces.append(parse_dollar(r))
        else:
            text.append(r.get())
    if text: pieces.append(('t', ''.join(text)))
    return pieces

def parse_var(r):
    n = []
    while NAMEC.match(r.peek() or ' '): n.append(r.get())
    keys = []
    while r.peek() == '[':
        r.get(); skip_blanks(r); keys.append(parse_word(r, {']'})); skip_blanks(r)
        if r.get() != ']': r.err('] missing after a key')
    return ('v', ''.join(n), keys)

def parse_arith(r):
    depth, e, line = 0, [], r.line
    while True:
        c = r.peek()
        if c == '': r.err(')) missing')
        if c == ')' and depth == 0 and r.peek(1) == ')': r.get(); r.get(); break
        if c == '(': depth += 1
        if c == ')': depth -= 1
        e.append(r.get())
    return ('ar', ''.join(e), line)

def parse_dollar(r):
    c = r.peek()
    if c == '(' and r.peek(1) == '(': r.get(); r.get(); return parse_arith(r)
    if c == '(': r.get(); return ('cap', parse_cmds(r, ')', {')'}))
    if c == '{':
        r.get(); n = []
        while r.peek() != '}':
            if r.peek() == '': r.err('} missing')
            n.append(r.get())
        r.get(); return ('v', ''.join(n), [])
    if NAME0.match(c or ' '): return parse_var(r)
    return ('t', '$')

def parse_list(r):
    """[words] a list; [key: value ...] a map; [:] an empty one."""
    words = []
    while True:
        skip_blanks(r, newlines=True)
        c = r.peek()
        if c == '': r.err('] missing')
        if c == ']': r.get(); break
        words.append(parse_word(r, {']'}))
    if words == [[('t', ':')]]: return ('map', [])
    def key(w): return len(w) == 1 and w[0][0] == 't' and len(w[0][1]) > 1 and w[0][1].endswith(':')
    if words and key(words[0]):
        if len(words) % 2: r.err('a map: key: value, each key a word ending in :')
        pairs = []
        for k, v in zip(words[0::2], words[1::2]):
            if not key(k): r.err('a map: key: value, each key a word ending in :')
            pairs.append((k[0][1][:-1], v))
        return ('map', pairs)
    return ('list', words)

def parse_block(r):
    skip_blanks(r); params = []
    if r.peek() == '|':
        r.get()
        while True:
            skip_blanks(r); c = r.peek()
            if c == '|': r.get(); break
            if not NAME0.match(c or ' '): r.err("a block's parameters are names between | |")
            n = []
            while NAMEC.match(r.peek() or ' '): n.append(r.get())
            params.append(''.join(n))
    return ('blk', params, parse_cmds(r, '}', set()))

# ---------------------------------------------------------------- making Forth
class Frame:
    def __init__(self, kind, parent, name):
        self.kind, self.parent, self.name = kind, parent, name
        self.nslots, self.captures = 1, []                  # slot 0: a def's number
    def slot(self):
        self.nslots += 1; return self.nslots - 1

class Var:
    def __init__(self, name, frame, slot, boxed=True):
        self.name, self.frame, self.slot, self.boxed = name, frame, slot, boxed

class Scope:
    def __init__(self, frame, parent):
        self.frame, self.parent, self.vars = frame, parent, {}
    def find(self, name):
        s = self
        while s:
            if name in s.vars: return s.vars[name]
            s = s.parent
        return None

def bare(w, name=None):
    ok = len(w) == 1 and w[0][0] == 't'
    return ok and (name is None or w[0][1] == name)

def text_code(s):
    if '"' not in s and all(32 <= ord(ch) < 127 for ch in s):
        return 'S" %s" TXT' % s
    b = s.encode('utf-8')
    return ' '.join(str(x) for x in b) + ' %d CHARS>TXT' % len(b)

class Gen:
    def __init__(self):
        self.out, self.n, self.defs = [], 0, {}
    def fresh(self, p):
        self.n += 1; return 'CM.%s%d' % (p, self.n)
    def err(self, line, msg):
        raise CmError('line %d: %s' % (line, msg))

    # ---- variables
    def cap_index(self, frame, v, line):
        if frame.kind != 'block':
            self.err(line, '$%s: a def sees only its parameters and its own variables (v0)' % v.name)
        if v not in frame.captures: frame.captures.append(v)
        return frame.captures.index(v)
    def ref(self, v, frame, line):                       # v's cell (boxed) or value (a number): here
        if v.frame is frame: return '%d LS@' % v.slot
        return '%d E@' % self.cap_index(frame, v, line)
    def read(self, name, scope, frame, line):
        v = scope.find(name)
        if v is None: self.err(line, 'no variable $%s - var makes one' % name)
        return self.ref(v, frame, line) + (' UPV@' if v.boxed else '')

    # ---- values
    def piece(self, p, scope, frame, line):
        k = p[0]
        if k == 't': return text_code(p[1])
        if k == 'n':
            return ('%d D-NUM' if -(1 << 61) < p[1] < (1 << 61) else '%d N>ITEM-D') % p[1]
        if k == 'b': return 'TRUE-BOX' if p[1] else 'FALSE-BOX'
        if k == 'v':
            code = self.read(p[1], scope, frame, line)
            for key in p[2]: code += ' ' + self.word(key, scope, frame, line) + ' D-AT'
            return code
        if k == 'q':
            if not p[1]: return 'S" " TXT'
            code = self.piece(p[1][0], scope, frame, line) + ' D-STR'
            for q in p[1][1:]: code += ' ' + self.piece(q, scope, frame, line) + ' JOIN'
            return code
        if k == 'cap': return "['] %s CAPTURE ONE" % self.capture_word(p[1], scope, frame)
        if k == 'ar': return self.arith(p[1], scope, frame, p[2])
        if k == 'list': return self.args(p[1], scope, frame, line)
        if k == 'map':
            code = 'R-NEW-RECORD K-REC R-BOX'
            for key, w in p[1]: code += ' DUP %s %s D-SET' % (text_code(key), self.word(w, scope, frame, line))
            return code
        if k == 'blk': return self.block(p, scope, frame, line)
        if k == 'spread': self.err(line, '@ spreads into a command\'s words or a list - not here')
        raise CmError('a piece of kind %s' % k)
    def word(self, w, scope, frame, line):
        if len(w) == 1: return self.piece(w[0], scope, frame, line)
        code = self.piece(w[0], scope, frame, line) + ' D-STR'
        for p in w[1:]: code += ' ' + self.piece(p, scope, frame, line) + ' JOIN'
        return code
    def args(self, words, scope, frame, line):
        code = 'ARGL'
        for w in words:
            if len(w) == 1 and w[0][0] == 'spread':
                inner = w[0][1]
                lst = ("['] %s CAPTURE" % self.capture_word(inner[1], scope, frame)) if inner[0] == 'cap' \
                    else self.piece(inner, scope, frame, line)
                code += ' ' + lst + ' ARG@'
            else:
                code += ' ' + self.word(w, scope, frame, line) + ' ARG'
        return code
    def capture_word(self, cmds, scope, frame):
        name = self.fresh('C')
        self.out.append(': %s ( --- )\n  %s ;' % (name, self.body(cmds, Scope(frame, scope), frame)))
        return name
    def block(self, p, scope, frame, line):
        _, params, cmds = p
        f = Frame('block', frame, 'a block'); s = Scope(f, scope)
        for q in params: s.vars[q] = Var(q, f, f.slot())
        name = self.fresh('B')
        body = self.body(cmds, s, f)
        bind = ('%d BLK-BIND' % len(params)) if params else 'DROP'
        self.out.append(': %s ( args --- )\n  %d FRAME %s\n  %s\n  UNFRAME ;' % (name, f.nslots, bind, body))
        caps = ' '.join(self.ref(v, frame, line) for v in f.captures)
        return ("%s %d ['] %s BLK-NEW" % (caps, len(f.captures), name)).strip()

    def arith(self, text, scope, frame, line):
        r, toks = Reader(text, line), []
        while True:
            while r.peek() in (' ', '\t', '\n', '\r'): r.get()
            c = r.peek()
            if c == '': break
            if c.isdigit():
                d = []
                while r.peek().isdigit(): d.append(r.get())
                toks.append(('num', int(''.join(d))))
            elif c == '$':
                r.get(); toks.append(('val', parse_dollar(r)))
            elif c + r.peek(1) in ('==', '!=', '<=', '>=', '&&', '||'):
                toks.append(('op', r.get() + r.get()))
            elif c in '+-*/%<>()!':
                toks.append(('op', r.get()))
            else:
                r.err('(( )) holds numbers, $values and operators - not %r' % c)
        pos = [0]
        def peek(): return toks[pos[0]][1] if pos[0] < len(toks) and toks[pos[0]][0] == 'op' else None
        def take(): pos[0] += 1; return toks[pos[0] - 1]
        def primary():
            if pos[0] >= len(toks): self.err(line, '(( )) ends too soon')
            t = take()
            if t[0] == 'num': return '%d D-NUM' % t[1]
            if t[0] == 'val': return self.piece(t[1], scope, frame, line)
            if t[1] == '(':
                e = orx()
                if peek() != ')': self.err(line, ') missing in (( ))')
                take(); return e
            if t[1] == '-': return primary() + ' D-NEG'
            if t[1] == '!': return primary() + ' D-TRUE? 0= D-BOOL'
            self.err(line, 'in (( )): %s where a value goes' % t[1])
        def mul():
            e = primary()
            while peek() in ('*', '/', '%'): op = take()[1]; e += ' %s %s' % (primary(), {'*': 'D*', '/': 'D/', '%': 'D%'}[op])
            return e
        def add():
            e = mul()
            while peek() in ('+', '-'): op = take()[1]; e += ' %s %s' % (mul(), 'D+' if op == '+' else 'D-')
            return e
        def cmp():
            e = add()
            if peek() in ('==', '!=', '<', '<=', '>', '>='):
                op = take()[1]; e += ' %s %s' % (add(), {'==': 'D==', '!=': 'D!=', '<': 'D<', '<=': 'D<=', '>': 'D>', '>=': 'D>='}[op])
            return e
        def andx():
            e = cmp()
            while peek() == '&&': e = '%s D-TRUE? IF %s D-TRUE? D-BOOL ELSE FALSE-BOX THEN' % (e, cmp()) if take() else e
            return e
        def orx():
            e = andx()
            while peek() == '||': e = '%s D-TRUE? IF TRUE-BOX ELSE %s D-TRUE? D-BOOL THEN' % (e, andx()) if take() else e
            return e
        e = orx()
        if pos[0] != len(toks): self.err(line, 'in (( )): more than one expression')
        return e

    # ---- commands
    def body(self, cmds, scope, frame):
        return '\n  '.join(self.cmd(line, words, scope, frame) for line, words in cmds) or ''
    def flag(self, words, scope, frame, line):          # a condition: a flag
        if words and bare(words[0], '!'): return self.flag(words[1:], scope, frame, line) + ' 0='
        if len(words) == 1 and words[0][0][0] != 't':
            return self.word(words[0], scope, frame, line) + ' D-TRUE?'
        if words and bare(words[0]) and words[0][0][1] in self.defs:
            return self.cmd(line, words, scope, frame) + ' STATUS @ 0='
        self.err(line, 'a condition: (( )), a value, ! and one of them, or a def called')
    def cmd(self, line, words, scope, frame):
        head = words[0]
        name = head[0][1] if bare(head) else None
        rest = words[1:]
        if name in ('var', 'set'):
            if len(rest) != 2 or not bare(rest[0]): self.err(line, '%s name value' % name)
            target, value = rest[0][0][1], self.word(rest[1], scope, frame, line)
            if name == 'var':
                if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', target): self.err(line, 'var: a name, not %s' % target)
                v = Var(target, frame, frame.slot()); scope.vars[target] = v
                return '%s UPV-NEW %d LS!' % (value, v.slot)
            m = re.fullmatch(r'([A-Za-z_][A-Za-z0-9_]*)((?:\[[^\]]+\])*)', target)
            if not m: self.err(line, 'set: a name, or name[key] - not %s' % target)
            keys = re.findall(r'\[([^\]]+)\]', m.group(2))
            v = scope.find(m.group(1))
            if v is None: self.err(line, 'set: no variable %s - var makes one' % m.group(1))
            if not keys: return '%s %s UPV!' % (value, self.ref(v, frame, line))
            code = self.read(m.group(1), scope, frame, line)
            kw = [parse_word(Reader(k, line), set()) for k in keys]
            for k in kw[:-1]: code += ' %s D-AT' % self.word(k, scope, frame, line)
            return '%s %s %s D-SET' % (code, self.word(kw[-1], scope, frame, line), value)
        if name in ('put', 'echo'):
            return '%s %s' % (self.args(rest, scope, frame, line), 'PUTS' if name == 'put' else 'ECHO')
        if name in ('count', 'range', 'merge'):
            return '%s %s-OF' % (self.args(rest, scope, frame, line), name.upper())
        if name == 'append':
            if not rest or not bare(rest[0]): self.err(line, 'append name values')
            return '%s %s APPEND' % (self.read(rest[0][0][1], scope, frame, line), self.args(rest[1:], scope, frame, line))
        if name in ('true', 'false'):
            return '%d STATUS !' % (0 if name == 'true' else 1)
        if name in ('break', 'continue'):
            v = scope.find('%loop')
            if v is None: self.err(line, '%s outside a loop' % name)
            return '%s %s' % (self.ref(v, frame, line), name.upper())
        if name == 'return':
            v = scope.find('%def')
            st = '0' if not rest else self.word(rest[0], scope, frame, line) + ' D>N'
            return '%s %s RETURN' % (st, self.ref(v, frame, line))
        if name == 'if':
            return self.if_cmd(rest, scope, frame, line)
        if name in ('for', 'while'):
            if not rest or rest[-1][0][0] != 'blk' or rest[-1][0][1]: self.err(line, '%s ... { body } - a block with no parameters' % name)
            return (self.for_cmd if name == 'for' else self.while_cmd)(rest, scope, frame, line)
        if name == 'def':
            return self.def_cmd(rest, scope, frame, line)
        if name is not None and name in self.defs:
            return '%s %d CM.D.%s# @ [\'] CM.D.%s DEF-CALL' % (self.args(rest, scope, frame, line), self.defs[name], name, name)
        if name is None:                                    # rule 11: a value as the first word
            return '%s %s CALL-VALUE' % (self.args(rest, scope, frame, line), self.word(head, scope, frame, line))
        self.err(line, '%s: no such command - programs come later (v0)' % name)
    def inline(self, blk, scope, frame, line):
        if blk[0][0] != 'blk' or blk[0][1]: self.err(line, 'a block with no parameters was expected')
        return self.body(blk[0][2], Scope(frame, scope), frame)
    def if_cmd(self, rest, scope, frame, line):
        i = next((j for j, w in enumerate(rest) if w[0][0] == 'blk'), None)
        if i is None: self.err(line, 'if condition { ... }')
        code = '%s IF\n  %s' % (self.flag(rest[:i], scope, frame, line), self.inline(rest[i], scope, frame, line))
        tail = rest[i + 1:]
        if tail:
            if bare(tail[0], 'else'):
                if len(tail) != 2: self.err(line, 'else { ... }')
                code += '\n  ELSE\n  %s' % self.inline(tail[1], scope, frame, line)
            elif bare(tail[0], 'elif'):
                code += '\n  ELSE\n  %s' % self.if_cmd(tail[1:], scope, frame, line)
            else: self.err(line, 'after if\'s block: else or elif')
        return code + '\n  THEN'
    def loop_body(self, blk, scope, frame, line, loopvar=None):
        s = Scope(frame, scope); idv = Var('%loop', frame, frame.slot(), boxed=False); s.vars['%loop'] = idv
        pre = ''
        if loopvar:
            v = Var(loopvar, frame, frame.slot()); s.vars[loopvar] = v
            pre = '%d LS@ UPV-NEW %d LS!\n  ' % (v.slot, v.slot)      # fresh each iteration
        name = self.fresh('L')
        self.out.append(': %s ( --- )\n  %s%s ;' % (name, pre, self.body(blk[0][2], s, frame)))
        return name, idv, (v if loopvar else None)
    def for_cmd(self, rest, scope, frame, line):
        if len(rest) < 2 or not bare(rest[0]): self.err(line, 'for name words... { body }')
        src = frame.slot()
        source = self.args(rest[1:-1], scope, frame, line)
        if len(rest) == 3 and rest[1][0][0] != 'spread': source += ' FOR-ONE'
        name, idv, v = self.loop_body(rest[-1], scope, frame, line, rest[0][0][1])
        return "%s %d LS!  %d %d %d ['] %s C-FOR" % (source, src, src, v.slot, idv.slot, name)
    def while_cmd(self, rest, scope, frame, line):
        cond = self.fresh('W')
        self.out.append(': %s ( --- f )\n  %s ;' % (cond, self.flag(rest[:-1], scope, frame, line)))
        name, idv, _ = self.loop_body(rest[-1], scope, frame, line)
        return "%d ['] %s ['] %s C-WHILE" % (idv.slot, cond, name)
    def def_cmd(self, rest, scope, frame, line):
        if frame.kind != 'main' or scope.parent: self.err(line, 'def is for the script\'s top level (v0)')
        if len(rest) != 2 or not bare(rest[0]) or rest[1][0][0] != 'blk': self.err(line, 'def name { ... }')
        dname, (_, params, cmds) = rest[0][0][1], rest[1][0]
        f = Frame('def', None, dname); s = Scope(f, None)
        s.vars['%def'] = Var('%def', f, 0, boxed=False)
        for q in params: s.vars[q] = Var(q, f, f.slot())
        body = self.body(cmds, s, f)
        self.out.append(": CM.D.%s-IMPL ( --- )\n  %s ;\n' CM.D.%s-IMPL IS CM.D.%s  %d CM.D.%s# !" % (dname, body, dname, dname, f.nslots - 1, dname))
        return ''

def compile_cm(src):
    cmds = parse_cmds(Reader(src), None, set())
    g = Gen()
    for line, words in cmds:                                # defs known before their first call
        if bare(words[0], 'def') and len(words) == 3 and bare(words[1]) and words[2][0][0] == 'blk':
            g.defs[words[1][0][1]] = len(words[2][0][1])
    main = Frame('main', None, 'the script'); s = Scope(main, None)
    s.vars['%def'] = Var('%def', main, 0, boxed=False)
    lines = []
    for line, words in cmds:                                # a safe point before each of the script's own
        c = g.cmd(line, words, s, main)
        if c: lines.append('R-GC?  ' + c)
    out = ['S" cm/rt-cm.4" INCLUDED  S" cm/out.4" INCLUDED  S" cm/ctl.4" INCLUDED  S" cm/lib.4" INCLUDED']
    out += ['DEFER CM.D.%s  VARIABLE CM.D.%s#' % (d, d) for d in g.defs]
    out += g.out
    out.append(': CM.MAIN ( --- )\n  %s ;' % '\n  '.join(lines))
    out.append("%d ' CM.MAIN DEF-RUN" % (main.nslots - 1))
    return '\n'.join(wrap(l) for l in '\n'.join(out).split('\n')) + '\n'

def wrap(line, width=100):
    """A long line cut at its words - an S\" text\", ['] X and ' X kept whole, as they read on from
    their own line: the Forth reading it takes lines of a bounded length (858: a word cut in two,
    "Undefined word R"; ['] at a line's end, "Not found")."""
    if len(line) <= width: return line
    lead = line[:len(line) - len(line.lstrip())] or '  '
    units, cur, lines = re.findall(r'S" [^"]*"|(?:\[\x27\]|\x27)\s+\S+|\S+', line), '', []   # ['] X and ' X kept whole too: a parsing word reads its name from its own line
    for u in units:
        if cur and len(cur) + 1 + len(u) > width:
            lines.append(cur); cur = lead + u
        else:
            cur = (cur + ' ' + u) if cur else (line[:len(line) - len(line.lstrip())] + u)
    lines.append(cur)
    return '\n'.join(lines)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write('usage: cmc.py SCRIPT.cm\n'); sys.exit(2)
    try:
        sys.stdout.write(compile_cm(open(sys.argv[1], encoding='utf-8').read()))
    except CmError as e:
        sys.stderr.write('cmc: %s: %s\n' % (sys.argv[1], e)); sys.exit(1)
