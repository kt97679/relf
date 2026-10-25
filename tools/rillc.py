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

 | (?P<str>"(?:[^"\\]|\\.)*") | (?P<raw>'[^']*')
 | (?P<var>\$[A-Za-z_][A-Za-z0-9_]*)
 | (?P<op>\$\(|==|!=|<=|>=|>>|\+=|-=|->|\?\?|[<>=(){},;|\[\]])
 | (?P<word>[^\s"'$(){},;<>=\[\]]+)
''', re.X)
KEYWORDS = {'if', 'else', 'while', 'def', 'return', 'and', 'or', 'not', 'for', 'in', 'break'}

def tokenize(src):
    toks, line = [], 1
    for m in TOKEN.finditer(src):
        k = m.lastgroup; v = m.group()
        if k == 'nl': toks.append(('nl', v, line, m.start(), m.end())); line += 1
        elif k in ('ws', 'comment'): continue
        elif k == 'word' and v in KEYWORDS: toks.append(('kw', v, line, m.start(), m.end()))
        else: toks.append((k, v, line, m.start(), m.end()))
    toks.append(('eof', '', line, len(src), len(src)))
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
        tok = self.t[self.i][:3] if False else self.t[self.i]
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
    PREC = {'or': 1, 'and': 2, 'in': 3, 'not in': 3, '==': 3, '!=': 3, '<': 3, '<=': 3, '>': 3, '>=': 3, '+': 4, '-': 4, '*': 5, '/': 5, '%': 5}
    def expr(self, minp=1):
        code, kind = self.unary()
        while True:
            op = self.peek()[1]
            if op == 'not' and self.peek(1)[1] == 'in': op = 'not in'
            if op not in self.PREC or self.peek()[0] not in ('op', 'kw', 'word') or self.PREC[op] < minp: return code, kind
            self.i += 2 if op == 'not in' else 1
            rcode, rkind = self.expr(self.PREC[op] + 1)
            code, kind = self.binop(op, code, kind, rcode, rkind)
    def binop(self, op, a, ak, b, bk):
        line = self.peek()[2]
        if op in ('and', 'or'):
            return '%s %s %s' % (a, b, op.upper()), 'bool'
        if op in ('in', 'not in'):
            neg = ' 0=' if op == 'not in' else ''
            if bk == 'record': return '%s %s R-HAS%s' % (self.to_text(a, ak), b, neg), 'bool'
            if bk == 'list': return '%s %s R-IN%s' % (self.box(a, ak), b, neg), 'bool'
            raise Error('line %d: in needs a list or a record' % line)
        if op in ('==', '!=') and 'text' in (ak, bk) and ak in ('text', 'any') and bk in ('text', 'any'):
            return '%s %s R-T=%s' % (self.to_text(a, ak), self.to_text(b, bk), '' if op == '==' else ' 0='), 'bool'
        if op in ('==', '!=') and ak in ('list', 'record', 'any') and bk == ak and ak != 'any':
            raise Error('line %d: comparing lists or records is not in stage 2' % line)
        a, b = self.to_num(a, ak, line), self.to_num(b, bk, line)
        ak = bk = 'number'
        if getattr(self, 'stack', None): self.depth -= 1
        kind = 'number' if op in '+-*/%' else 'bool'
        short = {('+', '1'): '1+', ('-', '1'): '1-', ('>', '0'): '0>', ('<', '0'): '0<', ('==', '0'): '0=', ('!=', '0'): '0<>'}
        if (op, b) in short: return '%s %s' % (a, short[(op, b)]), kind      # one word, not a literal and an operator
        forth = {'+': '+', '-': '-', '*': '*', '/': '/', '%': 'MOD', '==': '=', '!=': '<>', '<': '<', '>': '>', '<=': '> 0=', '>=': '< 0='}[op]
        return '%s %s %s' % (a, b, forth), kind
    def unary(self):
        tok = self.peek()
        if tok[1] == 'not': self.i += 1; c, k = self.unary(); return c + ' 0=', 'bool'
        if tok[1] == '-' and tok[0] == 'word': self.i += 1; c, k = self.unary(); return c + ' NEGATE', 'number'
        return self.term()
    def term(self):
        code, kind = self.term0()
        while True:                                   # $x[i] and $x.f, touching what they follow
            nxt, prev = self.peek(), self.t[self.i - 1]
            if nxt[1] == '[' and nxt[3] == prev[4]:
                self.i += 1; ic, ik = self.expr(); self.take('op', ']')
                if kind == 'list': code, kind = '%s %s R-AT' % (code, self.to_num(ic, ik, nxt[2])), 'any'
                elif kind == 'record': code, kind = '%s %s R-GET' % (self.to_text(ic, ik), code), 'any'
                elif kind == 'any': code, kind = '%s R-UNBOX DROP %s R-AT' % (code, self.to_num(ic, ik, nxt[2])), 'any'
                else: raise Error('line %d: only a list or a record is indexed' % nxt[2])
            elif nxt[0] == 'word' and nxt[1].startswith('.') and nxt[3] == prev[4] and kind in ('record', 'any'):
                self.i += 1
                for f in nxt[1][1:].split('.'):
                    code = ('%s R-UNBOX DROP' % code) if kind == 'any' else code
                    code, kind = 'S" %s" R-TEXT %s R-GET' % (f, code), 'any'
            else:
                return code, kind
    def literal_list(self):
        """[ items ] or [expr for x in src if cond]; the [ taken."""
        j, depth = self.i, 0
        while not (depth == 0 and self.t[j][1] == ']'):          # a comprehension? a for at this level
            if self.t[j][1] in ('[', '(', '{'): depth += 1
            elif self.t[j][1] in (']', ')', '}'): depth -= 1
            elif depth == 0 and self.t[j][1] == 'for': return self.comprehension(j)
            j += 1
        code = ['R-NEW-LIST']
        while self.peek()[1] != ']':
            if self.peek()[0] == 'var' and False: pass
            c, kd = self.term()
            code.append('%s OVER R-PUSH' % self.box(c, kd))
        self.take('op', ']'); return ' '.join(code), 'list'
    def comprehension(self, j):
        start = self.i; self.i = j + 1                            # for x in src [if cond]
        name = self.take('word')[1]; self.take('kw', 'in')
        sc, sk = self.expr()
        if sk != 'list': raise Error('line %d: for needs a list' % self.peek()[2])
        tmp = '%s.src%d' % (name, j); self.names.update([name, tmp])
        self.scope()[name] = 'any'
        cond = None
        if self.peek()[1] == 'if': self.i += 1; cond, ck = self.expr()
        end = self.i; self.take('op', ']'); after = self.i
        self.i = start; ec, ek = self.expr(); self.i = after
        item = '%s OVER R-PUSH' % self.box(ec, ek)
        body = '%s IF %s THEN' % (cond, item) if cond else item
        return ('R-NEW-LIST %s R.%s ! R.%s @ R-LEN 0 ?DO R.%s @ I R-AT R.%s ! %s LOOP' %
                (sc, tmp, tmp, tmp, name, body)), 'list'
    def literal_record(self):
        code = ['R-NEW-RECORD']
        while self.peek()[1] != '}':
            k = self.take()
            if k[0] == 'word' and k[1].endswith(':'): key = k[1][:-1]
            elif k[0] in ('raw', 'str') and self.peek()[1] == ':': key = k[1][1:-1]; self.i += 1
            else: raise Error('line %d: a record field is name: value' % k[2])
            c, kd = self.expr()
            code.append('%s %s 2 PICK R-PUT' % (self.box(c, kd), self.lit_text(key)))
            if self.peek()[1] == ',': self.i += 1
            self.skip_nl()
        self.take('op', '}'); return ' '.join(code), 'record'
    def term0(self):
        tok = self.take()
        k, v, line = tok[:3]
        if v == '[': return self.literal_list()
        if v == '{': self.skip_nl(); return self.literal_record()
        if k == 'word' and re.fullmatch(r'-?\d+', v):
            if getattr(self, 'stack', None): self.depth += 1
            return v, 'number'
        if k == 'var' and getattr(self, 'stack', None) and v[1:] in self.stack:
            at = self.depth + len(self.stack) - 1 - self.stack.index(v[1:])
            self.depth += 1
            return {0: 'DUP', 1: 'OVER'}.get(at, '%d PICK' % at), 'number'
        if k == 'var': return 'R.%s @' % v[1:], self.kind_of(v[1:], line)
        if v == '$(':
            c = self.command(capture=True); self.take('op', ')')
            return c + ' R-CHECK', 'text'
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
        lib = self.library(name, args, line)
        if lib: return lib
        if name not in self.funcs: raise Error('line %d: %s() is not defined (a def comes before its use)' % (line, name))
        params, kind = self.funcs[name]
        if len(args) != len(params): raise Error('line %d: %s() takes %d arguments' % (line, name, len(params)))
        if name not in getattr(self, 'pure_defs', set()):
            args = [(self.box(c, k), 'any') for c, k in args]          # a def's parameters are boxes
        word = 'RECURSE' if name == getattr(self, 'current', None) else 'R:%s' % name   # Forth hides a word until its ;
        if getattr(self, 'stack', None): self.depth += (1 if kind else 0) - len(args)
        return ' '.join(a[0] for a in args) + ' ' + word, kind
    def library(self, name, args, line):
        a = args
        def need(n, *kinds):
            if len(a) != n: raise Error('line %d: %s() takes %d arguments' % (line, name, n))
        if name == 'len':
            need(1); c, k = a[0]
            if k == 'any': return '%s R-UNBOX DROP @' % c, 'number'
            if k == 'record': return '%s R-KEYS @' % c, 'number'
            return '%s @' % c, 'number'                            # a text's or a list's count
        if name in ('words', 'lines'): need(1); return '%s %s' % (self.to_text(*a[0]), {'words': 'R-SPLIT-WS', 'lines': 'R-LINES'}[name]), 'list'
        if name == 'join': need(2); return '%s %s R-JOIN' % (a[0][0], self.to_text(*a[1])), 'text'
        if name == 'range': need(2); return '%s %s R-RANGE' % (self.to_num(*a[0], line), self.to_num(*a[1], line)), 'list'
        if name == 'number': need(1); return '%s R-NUMBER' % self.to_text(*a[0]), 'number'
        if name == 'text': need(1); return self.to_text(*a[0]), 'text'
        if name == 'push': need(2); return '%s %s R-PUSH' % (self.box(*a[1]), a[0][0]), None
        if name == 'extend': need(2); return '%s %s R-EXTEND' % (a[0][0], a[1][0]), None
        if name == 'shift': need(1); return '%s R-SHIFT' % a[0][0], 'any'
        if name == 'first': need(1); return '%s 0 R-AT' % a[0][0], 'any'
        if name == 'slice':
            if len(a) == 2: return '%s %s OVER R-LEN R-SLICE' % (a[0][0], self.to_num(*a[1], line)), 'list'
            need(3); return '%s %s %s R-SLICE' % (a[0][0], self.to_num(*a[1], line), self.to_num(*a[2], line)), 'list'
        if name == 'keys': need(1); return '%s R-KEYS' % a[0][0], 'list'
        return None
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
            if body.startswith('$(', i):
                if lit: parts.append(self.lit_text(lit)); lit = ''
                depth, j = 1, i + 2
                while depth: depth += {'(': 1, ')': -1}.get(body[j], 0); j += 1
                sub = Compiler.__new__(Compiler); sub.__dict__ = dict(self.__dict__)
                sub.t = tokenize(body[i + 2:j - 1]); sub.i = 0
                parts.append(sub.command(capture=True) + ' R-CHECK'); i = j; continue
            m = re.match(r'\$([A-Za-z_][A-Za-z0-9_]*)', body[i:])
            if m or c == '{':
                if lit: parts.append(self.lit_text(lit)); lit = ''
                if m:
                    name = m.group(1); i += m.end()
                    code, kind = 'R.%s @' % name, self.kind_of(name, line)
                    while kind in ('record', 'any'):                  # "$host.name": a field, in a string too
                        f = re.match(r'\.([A-Za-z_][A-Za-z0-9_]*)', body[i:])
                        if not f: break
                        code = ('%s R-UNBOX DROP' % code) if kind == 'any' else code
                        code, kind = 'S" %s" R-TEXT %s R-GET' % (f.group(1), code), 'any'; i += f.end()
                    parts.append(self.to_text(code, kind))
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
    KCODE = {'number': 'K-NUM', 'text': 'K-TEXT', 'bool': 'K-BOOL', 'list': 'K-LIST', 'record': 'K-REC'}
    def to_text(self, code, kind):
        if kind == 'text': return code
        if kind == 'any': return code + ' R-ANY>TEXT'
        if kind == 'list': return code + ' S"  " R-TEXT R-JOIN'          # a list as text: its items, a blank between
        return code + ' R-NUM'
    def to_num(self, code, kind, line):
        if kind in ('number', 'bool'): return code
        if kind == 'any': return code + ' R-ANY>NUM'
        raise Error('line %d: a number is needed here, not a %s' % (line, kind))
    def box(self, code, kind):
        return code if kind == 'any' else '%s %s R-BOX' % (code, self.KCODE[kind])

    # statements
    def block(self):
        self.take('op', '{'); out = []
        self.skip_nl()
        while self.peek()[1] != '}':
            out.append(self.statement()); self.skip_nl()
        self.take('op', '}'); return ' '.join(o for o in out if o)
    def statement(self):
        k, v, line = self.peek()[:3]
        start = self.i
        if v == 'if': out = self.if_()
        elif v == 'while':
            self.i += 1; c = self.cond()
            out = 'BEGIN %s WHILE %s REPEAT' % (c, self.block())
        elif v == 'return':
            self.i += 1; c, kd = self.expr()
            if getattr(self, 'stack', None):
                c += ' NIP' * len(self.stack); self.depth -= 1        # the result, the parameters dropped under it
            out = '%s EXIT' % c
        elif v == 'def': out = self.def_(); return ''
        elif v == 'for': out = self.for_()
        elif v == 'break': self.i += 1; out = 'LEAVE'
        elif k == 'word' and self.peek(1)[1] == '[' and self.peek(1)[3] == self.peek()[4]:
            name = v; self.i += 2
            ic, ik = self.expr(); self.take('op', ']'); self.take('op', '=')
            c, kd = self.expr(); ck = self.kind_of(name, line)
            if ck == 'list': out = '%s R.%s @ %s R-SET' % (self.box(c, kd), name, self.to_num(ic, ik, line))
            elif ck == 'record': out = '%s %s R.%s @ R-PUT' % (self.box(c, kd), self.to_text(ic, ik), name)
            else: raise Error('line %d: $%s is not a list or a record' % (line, name))
        elif k == 'word' and self.peek(1)[1] in ('=', '+=', '-='):
            name = v; self.i += 1; op = self.take()[1]
            c, kd = self.expr()
            sc = self.scope()
            if op != '=':
                if self.kind_of(name, line) != 'number': raise Error('line %d: %s needs a number to change' % (line, op))
                c, kd = self.binop('+' if op == '+=' else '-', 'R.%s @' % name, 'number', c, kd)
            elif name in sc and sc[name] != kd:
                raise Error('line %d: $%s is %s; it cannot become %s' % (line, name, sc[name], kd))
            sc[name] = kd; self.names.add(name)
            out = '%s R.%s !' % (c, name)
        elif k == 'word' and v == 'echo' and not self.plumbed():
            self.i += 1
            parts, _ = self.args((';', '}'))
            out = ' SPACE '.join(p + ' R-TYPE' for p in parts) + (' R-NL' if parts else 'R-NL')
        elif k == 'word' and self.peek(1)[1] == '(':
            self.i += 1; c, kd = self.call(v, line); out = c + ('' if kd is None else ' DROP')
        elif k in ('word', 'str', 'raw', 'var'):
            run = self.command()
            if self.peek()[1] == '??':
                self.i += 1; other = self.statement()
                out = '%s IF %s THEN' % (run, other)            # the guard runs when the command fails
            else:
                out = run + ' R-CHECK'                           # failure stops the script
        else: raise Error('line %d: cannot read %r here' % (line, v))
        return out
    def plumbed(self):
        """Does the statement from here redirect or pipe? Then echo runs as a
        program, with its ports where the statement puts them."""
        j = self.i
        while self.t[j][0] not in ('nl', 'eof') and self.t[j][1] not in (';', '}', '??'):
            if self.t[j][1] in ('>', '>>', '<', '|'): return True
            j += 1
        return False
    PORTS = {'in': 0, 'out': 1, 'err': 2, 'all': 1}
    MODES = {'>': 'W/O', '>>': 'A/O', '<': 'R/O'}
    def command(self, capture=False):
        """A pipeline to the end of the statement; compiles to its status - or,
        captured, to its output and then its status."""
        stages = [self.stage()]
        while self.peek()[1] == '|':
            self.i += 1; self.skip_nl(); stages.append(self.stage())
        body = ' '.join('%s %s PL-STAGE' % (s, '-1' if k == len(stages) - 1 else '0') for k, s in enumerate(stages))
        return '%s PL-BEGIN %s PL-END' % ('-1' if capture else '0', body)
    def arg_item(self):
        tok = self.peek()
        if tok[1] == '{':
            self.i += 1; c, kd = self.expr(); self.take('op', '}')
        elif tok[0] == 'kw' or tok[1] in (',', '=', '==', '!=', '<=', '>=', '+=', '-=', '->'):
            c, kd = self.lit(self.take()[1]), 'text'              # a keyword, an operator: plain text in an argument
        else:
            c, kd = self.term()
        return self.to_text(c, kd)
    def args(self, stop):
        """The arguments to the end of the statement; items touching each
        other join into one, as sh's words do (RILL-LEDGER.md 732)."""
        parts, redirs = [], []
        while self.peek()[0] not in ('nl', 'eof') and self.peek()[1] not in stop:
            tok, nxt = self.peek(), self.peek(1)
            if stop and tok[0] == 'word' and tok[1] in self.PORTS and nxt[1] in ('>', '>>') and nxt[3] == tok[4]:
                self.i += 1; redirs.append(self.redirect(tok[1])); continue
            if stop and tok[1] in ('>', '>>', '<') and '|' in stop:
                redirs.append(self.redirect('in' if tok[1] == '<' else 'out')); continue
            touching = parts and tok[3] == self.t[self.i - 1][4]
            c = self.arg_item()
            if touching: parts[-1] = '%s %s 2 R-CONCAT' % (parts[-1], c)
            else: parts.append(c)
        return parts, redirs
    def stage(self):
        parts, redirs = self.args((';', '}', ')', '??', '|'))
        return ' '.join(redirs + parts) + ' %d' % len(parts)
    def redirect(self, port):
        op = self.take()[1]
        tok = self.peek()
        if op != '<' and tok[0] == 'word' and tok[1] in ('out', 'err') and tok[3] == self.t[self.i - 1][4]:
            self.i += 1                                           # a port joined to another: err>out
            return '%d %d R-RD-DUP' % (self.PORTS[tok[1]], self.PORTS[port])
        c, kd = self.term()
        code = '%s %s %d R-RD-FILE' % (self.to_text(c, kd), self.MODES[op], self.PORTS[port])
        return code + (' 1 2 R-RD-DUP' if port == 'all' else '')
    def cond(self):
        self.take('op', '(')
        second = self.peek(1)
        if self.peek()[0] == 'word' and second[1] != '(' and not (second[0] in ('kw', 'op') and second[1] in
                ('in', 'not', 'and', 'or', '==', '!=', '<', '>', '<=', '>=')) and second[1] not in self.PREC:
            c = self.command() + ' 0='                           # a run: its success
        else:
            c, kd = self.expr()
        self.take('op', ')'); return c
    def for_(self):
        self.take('kw', 'for'); a = self.take('word')[1]; b = None
        if self.peek()[1] == ',': self.i += 1; b = self.take('word')[1]
        self.take('kw', 'in'); line = self.peek()[2]
        if self.peek()[1] == 'range' and self.peek(1)[1] == '(':        # a counted loop, no list made
            self.i += 2; lo, lk = self.expr(); self.take('op', ','); hi, hk = self.expr(); self.take('op', ')')
            if b: raise Error('line %d: for i, x needs a list' % line)
            self.scope()[a] = 'number'; self.names.add(a)
            return '%s 1+ %s ?DO I R.%s ! %s LOOP' % (self.to_num(hi, hk, line), self.to_num(lo, lk, line), a, self.block())
        sc, sk = self.expr()
        tmp = '%s.src%d' % (a, self.i); self.names.update([a, tmp])
        if sk == 'record':                                               # for k, v in a record
            key, val = (a, b) if b else (a, None)
            self.scope()[key] = 'text'
            if val: self.scope()[val] = 'any'; self.names.add(val)
            setv = ('R.%s @ R-VALS I R-AT R.%s ! ' % (tmp, val)) if val else ''
            return ('%s R.%s ! R.%s @ R-KEYS R-LEN 0 ?DO R.%s @ R-KEYS I R-AT R-ANY>TEXT R.%s ! %s%s LOOP'
                    % (sc, tmp, tmp, tmp, key, setv, self.block()))
        if sk not in ('list', 'any'): raise Error('line %d: for needs a list or a record' % line)
        if sk == 'any': sc += ' R-UNBOX DROP'
        idx, item = (a, b) if b else (None, a)
        self.scope()[item] = 'any'; self.names.add(item)
        seti = ''
        if idx: self.scope()[idx] = 'number'; self.names.add(idx); seti = 'I R.%s ! ' % idx
        return ('%s R.%s ! R.%s @ R-LEN 0 ?DO %sR.%s @ I R-AT R.%s ! %s LOOP'
                % (sc, tmp, tmp, seti, tmp, item, self.block()))
    def if_(self):
        self.take('kw', 'if'); c = self.cond()
        if getattr(self, 'stack', None): self.depth -= 1               # IF takes the flag
        then = self.block(); save = self.i; self.skip_nl()
        if self.peek()[1] == 'else':
            self.i += 1
            other = self.if_() if self.peek()[1] == 'if' else self.block()
            return '%s IF %s ELSE %s THEN' % (c, then, other)
        self.i = save
        return '%s IF %s THEN' % (c, then)
    def pure(self, params):
        """Does the body ahead only compute - no assignment, string, command,
        echo or loop? Then its parameters stay on the data stack (Iteration
        738): read with DUP, OVER or PICK, dropped under the result by NIP."""
        j, depth = self.i, 0
        while True:
            k, v = self.t[j][0], self.t[j][1]
            if v == '{': depth += 1
            elif v == '}':
                depth -= 1
                if depth == 0: return True
            elif k in ('str', 'raw') or v in ('=', '+=', '-=', '$(', 'while', 'for', '|', '>>', '??') and k != 'word':
                # < and > are comparisons here: with no command in the body, nothing is redirected
                return False
            elif k == 'var' and v[1:] not in params: return False
            elif k == 'word' and not re.fullmatch(r'-?\d+', v) and v not in self.PREC and v != '-' and self.t[j + 1][1] != '(':
                return False                                     # a command, echo, a bare word
            elif v in ('=', '+=', '-='): return False
            j += 1
    def def_(self):
        self.take('kw', 'def'); name = self.take('word')[1]; params = []
        while self.peek()[0] == 'word': params.append(self.take()[1])
        kind = None
        if self.peek()[1] == '->': self.i += 1; kind = self.take('word')[1]
        self.funcs[name] = (params, kind); self.current = name
        if self.pure(params):
            self.pure_defs = getattr(self, 'pure_defs', set()) | {name}
            self.stack, self.depth = params, 0
            body = self.block()
            self.stack = None
            tail = '' if kind else ' DROP' * len(params)
            body = re.sub(r' DUP NIP\b', '', ' ' + body + tail).strip()
            self.defs.append(': R:%s %s ;' % (name, body)); self.current = None
            return
        outer = self.locals; self.locals = {p: 'any' for p in params}
        self.names.update(params)
        body = self.block()
        scratch = [n for n in self.locals if n not in params]
        self.names.update(scratch)
        self.defs.append(': R:%s SHADOW{ %s | %s } %s ;' % (name, ' '.join('R.' + p for p in reversed(params)),
                                                         ' '.join('R.' + s for s in scratch), body))
        self.locals = outer; self.current = None
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
