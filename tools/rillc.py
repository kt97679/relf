#!/usr/bin/env python3
"""tools/rillc.py FILE.rill [--list] - Rill's stage-1a compiler, a prototype (Iteration 736).

SHELL-LANGUAGE.md Part 5 puts Rill's compiler in Forth, in Rill's own
image. This is its prototype, in Python, to try the design and measure
the code it makes before the Forth one is written - and to be that one's
oracle after: both must make the same Forth. It reads a Rill script and
prints Forth for rill/rt.4's image; --list prints each Rill line with
the Forth made of it instead.

Stage 1a: integers, text, variables (fixed kinds), + - * / %, the
comparisons, and or not, strings with $name and {expr}, echo, if / else
if / else, while, x += n, def with parameters (numbers) and -> kind,
return, calls. Not yet: commands, lists, records, the rest.
"""
import re, sys

class Error(Exception): pass

TOKEN = re.compile(r'''
   (?P<nl>\n) | (?P<ws>[ \t]+) | (?P<comment>\#[^\n]*)
 | (?P<num>\d+)
 | (?P<str>"(?:[^"\\]|\\.)*") | (?P<raw>'[^']*')
 | (?P<var>\$[A-Za-z_][A-Za-z0-9_]*)
 | (?P<op>==|!=|<=|>=|\+=|-=|->|[-+*/%<>=(){},;])
 | (?P<word>[^\s"'$(){},;<>=]+)
''', re.X)
KEYWORDS = {'if', 'else', 'while', 'def', 'return', 'and', 'or', 'not', 'for', 'in'}

def tokenize(src):
    toks, line = [], 1
    for m in TOKEN.finditer(src):
        k = m.lastgroup; v = m.group()
        if k == 'nl': toks.append(('nl', v, line)); line += 1
        elif k in ('ws', 'comment'): continue
        elif k == 'word' and v in KEYWORDS: toks.append(('kw', v, line))
        else: toks.append((k, v, line))
    toks.append(('eof', '', line))
    return toks

class Compiler:
    def __init__(self, src):
        self.t = tokenize(src); self.i = 0
        self.vars = {}          # script variable -> kind
        self.funcs = {}         # name -> (params, kind)
        self.locals = None      # kinds of the def being compiled
        self.defs = []          # Forth of each def
        self.names = set()      # every VARIABLE needed
        self.lines = []         # (rill line, forth) for --list

    def peek(self, k=0): return self.t[self.i + k]
    def take(self, kind=None, val=None):
        tok = self.t[self.i]
        if (kind and tok[0] != kind) or (val and tok[1] != val):
            raise Error('line %d: expected %s, found %r' % (tok[2], val or kind, tok[1]))
        self.i += 1; return tok
    def skip_nl(self):
        while self.peek()[0] in ('nl',) or self.peek()[1] == ';': self.i += 1

    def scope(self): return self.locals if self.locals is not None else self.vars
    def kind_of(self, name, line):
        if self.locals is not None and name in self.locals: return self.locals[name]
        if name in self.vars: return self.vars[name]
        raise Error('line %d: $%s is not set' % (line, name))

    # expressions, by precedence climbing: each returns (forth, kind)
    PREC = {'or': 1, 'and': 2, '==': 3, '!=': 3, '<': 3, '<=': 3, '>': 3, '>=': 3, '+': 4, '-': 4, '*': 5, '/': 5, '%': 5}
    def expr(self, minp=1):
        code, kind = self.unary()
        while True:
            op = self.peek()[1]
            if op not in self.PREC or self.peek()[0] not in ('op', 'kw') or self.PREC[op] < minp: return code, kind
            self.i += 1
            rcode, rkind = self.expr(self.PREC[op] + 1)
            code, kind = self.binop(op, code, kind, rcode, rkind)
    def binop(self, op, a, ak, b, bk):
        line = self.peek()[2]
        if op in ('and', 'or'):
            return '%s %s %s' % (a, b, op.upper()), 'bool'
        if op in ('==', '!=') and ak == 'text' and bk == 'text':
            return '%s %s R-T=%s' % (a, b, '' if op == '==' else ' 0='), 'bool'
        if ak != 'number' or bk != 'number':
            raise Error('line %d: %s needs numbers, has %s and %s' % (line, op, ak, bk))
        forth = {'+': '+', '-': '-', '*': '*', '/': '/', '%': 'MOD', '==': '=', '!=': '<>', '<': '<', '>': '>', '<=': '> 0=', '>=': '< 0='}[op]
        return '%s %s %s' % (a, b, forth), ('number' if op in '+-*/%' else 'bool')
    def unary(self):
        tok = self.peek()
        if tok[1] == 'not': self.i += 1; c, k = self.unary(); return c + ' 0=', 'bool'
        if tok[1] == '-' and tok[0] == 'op': self.i += 1; c, k = self.unary(); return c + ' NEGATE', 'number'
        return self.term()
    def term(self):
        tok = self.take()
        k, v, line = tok
        if k == 'num': return v, 'number'
        if k == 'var': return 'R.%s @' % v[1:], self.kind_of(v[1:], line)
        if k == 'str': return self.string(v[1:-1], line), 'text'
        if k == 'raw': return self.lit(v[1:-1]), 'text'
        if v == '(' : c, kd = self.expr(); self.take('op', ')'); return c, kd
        if k == 'word' and self.peek()[1] == '(':
            return self.call(v, line)
        if k == 'word': return self.lit(v), 'text'
        raise Error('line %d: unexpected %r' % (line, v))
    def call(self, name, line):
        self.take('op', '('); args = []
        while self.peek()[1] != ')':
            args.append(self.expr())
            if self.peek()[1] == ',': self.i += 1
        self.take('op', ')')
        if name == 'len':
            return '%s @' % args[0][0], 'number'
        if name not in self.funcs: raise Error('line %d: %s() is not defined (a def comes before its use)' % (line, name))
        params, kind = self.funcs[name]
        if len(args) != len(params): raise Error('line %d: %s() takes %d arguments' % (line, name, len(params)))
        return ' '.join(a[0] for a in args) + ' R:%s' % name, kind
    def lit(self, s):
        return 'S" %s" R-TEXT' % s if '"' not in s else self.bytes_lit(s)
    def bytes_lit(self, s):
        return ' '.join('%d' % b for b in s.encode()) + ' %d R-BYTES' % len(s.encode())
    def string(self, body, line):
        parts, i, lit = [], 0, ''
        while i < len(body):
            c = body[i]
            if c == '\\' and i + 1 < len(body):
                lit += {'n': '\n', 't': '\t'}.get(body[i + 1], body[i + 1]); i += 2; continue
            m = re.match(r'\$([A-Za-z_][A-Za-z0-9_]*)', body[i:])
            if m or c == '{':
                if lit: parts.append(self.lit_text(lit)); lit = ''
                if m:
                    name = m.group(1); i += m.end()
                    parts.append(self.to_text('R.%s @' % name, self.kind_of(name, line)))
                else:
                    depth, j = 1, i + 1
                    while depth: depth += {'{': 1, '}': -1}.get(body[j], 0); j += 1
                    sub = Compiler.__new__(Compiler); sub.__dict__ = dict(self.__dict__)
                    sub.t = tokenize(body[i + 1:j - 1]); sub.i = 0
                    c2, k2 = sub.expr(); parts.append(self.to_text(c2, k2)); i = j
                continue
            lit += c; i += 1
        if lit or not parts: parts.append(self.lit_text(lit))
        return parts[0] if len(parts) == 1 else '%s %d R-CONCAT' % (' '.join(parts), len(parts))
    def lit_text(self, s):
        if '"' in s or '\n' in s or '\t' in s: return self.bytes_lit(s)
        return 'S" %s" R-TEXT' % s
    def to_text(self, code, kind):
        return code if kind == 'text' else code + ' R-NUM'

    # statements
    def block(self):
        self.take('op', '{'); out = []
        self.skip_nl()
        while self.peek()[1] != '}':
            out.append(self.statement()); self.skip_nl()
        self.take('op', '}'); return ' '.join(o for o in out if o)
    def statement(self):
        k, v, line = self.peek()
        start = self.i
        if v == 'if': out = self.if_()
        elif v == 'while':
            self.i += 1; self.take('op', '('); c, kd = self.expr(); self.take('op', ')')
            out = 'BEGIN %s WHILE %s REPEAT' % (c, self.block())
        elif v == 'return':
            self.i += 1; c, kd = self.expr(); out = '%s EXIT' % c
        elif v == 'def': out = self.def_(); return ''
        elif k == 'word' and self.peek(1)[1] in ('=', '+=', '-='):
            name = v; self.i += 1; op = self.take()[1]
            c, kd = self.expr()
            sc = self.scope()
            if op != '=':
                if self.kind_of(name, line) != 'number' or kd != 'number': raise Error('line %d: %s needs numbers' % (line, op))
                c = 'R.%s @ %s %s' % (name, c, '+' if op == '+=' else '-')
            elif name in sc and sc[name] != kd:
                raise Error('line %d: $%s is %s; it cannot become %s' % (line, name, sc[name], kd))
            sc[name] = kd; self.names.add(name)
            out = '%s R.%s !' % (c, name)
        elif k == 'word' and v == 'echo':
            self.i += 1; parts = []
            while self.peek()[0] not in ('nl', 'eof') and self.peek()[1] not in (';', '}'):
                if self.peek()[1] == '{':
                    self.i += 1; c, kd = self.expr(); self.take('op', '}')
                else:
                    c, kd = self.term()
                parts.append(self.to_text(c, kd) + ' R-TYPE')
            out = ' SPACE '.join(parts) + (' R-NL' if parts else 'R-NL')
        elif k == 'word' and self.peek(1)[1] == '(':
            self.i += 1; c, kd = self.call(v, line); out = c + ('' if kd is None else ' DROP')
        else: raise Error('line %d: cannot read %r here' % (line, v))
        return out
    def if_(self):
        self.take('kw', 'if'); self.take('op', '('); c, kd = self.expr(); self.take('op', ')')
        then = self.block(); save = self.i; self.skip_nl()
        if self.peek()[1] == 'else':
            self.i += 1
            other = self.if_() if self.peek()[1] == 'if' else self.block()
            return '%s IF %s ELSE %s THEN' % (c, then, other)
        self.i = save
        return '%s IF %s THEN' % (c, then)
    def def_(self):
        self.take('kw', 'def'); name = self.take('word')[1]; params = []
        while self.peek()[0] == 'word': params.append(self.take()[1])
        kind = None
        if self.peek()[1] == '->': self.i += 1; kind = self.take('word')[1]
        self.funcs[name] = (params, kind)
        outer = self.locals; self.locals = {p: 'number' for p in params}
        self.names.update(params)
        body = self.block()
        scratch = [n for n in self.locals if n not in params]
        self.names.update(scratch)
        self.defs.append(': R:%s SHADOW{ %s | %s } %s ;' % (name, ' '.join('R.' + p for p in reversed(params)),
                                                         ' '.join('R.' + s for s in scratch), body))
        self.locals = outer
    def program(self):
        main = []; self.skip_nl()
        while self.peek()[0] != 'eof':
            line = self.peek()[2]; start = self.i
            out = self.statement()
            if out: main.append(out)
            self.lines.append((line, out))
            self.skip_nl()
        return ('\n'.join('VARIABLE R.%s' % n for n in sorted(self.names)) + '\n' +
                '\n'.join(self.defs) + '\n: R-MAIN %s ;\nR-MAIN\n' % ' '.join(main))

if __name__ == '__main__':
    src = open(sys.argv[1], encoding='utf-8').read()
    c = Compiler(src)
    try: forth = c.program()
    except Error as e: sys.exit('rillc: %s: %s' % (sys.argv[1], e))
    if '--list' in sys.argv:
        print(forth)
    else:
        sys.stdout.write(forth)
