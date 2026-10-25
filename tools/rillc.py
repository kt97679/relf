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
import importlib.util, os, re, sys
_spec = importlib.util.spec_from_file_location('rill_genes', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rill-genes.py'))
_genes = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_genes)
GENES = _genes.read_genes()            # rill/genes.tsv and RILL_GENES: the genome both compilers read (749)

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
        self.infer = None       # gene infer (764), the first pass: (def or None, name) -> the kinds it is bound to
        self.fixed = None       # ... the second: (def or None, name) -> the one kind it has, their join
        self.dal = {}; self.da_depth = 0; self.da_next = []   # certainly set (772): the block depth each name was set at
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
    def skey(self): return self.current if self.locals is not None else None
    # certainly set (772): a name set in a block is certainly set in it, and in the blocks within, from
    # there on; leaving the block forgets it, unless it was set before the block. A read of a text, a
    # list, a record or an item that is not certainly set checks the variable is - 0 is never one of them.
    def da_key(self, name): return (self.current if self.locals is not None and name in self.locals else None, name)
    def da_mark(self, name):
        if self.dal.get(self.da_key(name), -1) < 0: self.dal[self.da_key(name)] = self.da_depth
    def da_enter(self, names):
        self.da_depth += 1
        for n in names: self.da_mark(n)
    def da_leave(self):
        for k in [k for k, d in self.dal.items() if d == self.da_depth]: self.dal[k] = -1
        self.da_depth -= 1
    def num_into(self, k):                # a loop's count or index stored in a variable of kind k (771)
        return '' if k == 'number' else ' 1000000 *' if k == 'decimal' else ' K-NUM R-BOX'
    def bind(self, name, kind):
        """A binding of name to a value of kind: the kind the variable has from here (gene infer, 764)."""
        sc = self.scope(); self.names.add(name)
        if self.infer is not None: self.infer.setdefault((self.skey(), name), set()).add(kind)
        elif self.fixed is not None and (self.skey(), name) in self.fixed: kind = self.fixed[(self.skey(), name)]
        sc[name] = kind; return kind
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
            if op in ('and', 'or'):                 # short-circuit (755): the right side only when it decides
                if getattr(self, 'stack', None): self.depth -= 1        # the left one dropped before the right is made
                rcode, rkind = self.expr(self.PREC[op] + 1)
                code, kind = '%s DUP %sIF DROP %s THEN' % (code, '' if op == 'and' else '0= ', rcode), 'bool'
                continue
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
            if bk == 'any': return '%s %s R-IN-ANY%s' % (self.box(a, ak), b, neg), 'bool'      # 758
            raise Error('line %d: in needs a list or a record' % line)
        if op in ('==', '!=') and ak == 'any' and bk == 'any':                        # two items (758)
            return '%s %s R-BOX=%s' % (a, b, '' if op == '==' else ' 0='), 'bool'
        if op in ('==', '!=') and 'text' in (ak, bk) and ak in ('text', 'any') and bk in ('text', 'any'):
            return '%s %s R-T=%s' % (self.to_text(a, ak), self.to_text(b, bk), '' if op == '==' else ' 0='), 'bool'
        if op in ('==', '!=') and ak in ('list', 'record', 'any') and bk == ak and ak != 'any':
            raise Error('line %d: comparing lists or records is not in stage 2' % line)
        if 'decimal' in (ak, bk) and ak in ('number', 'decimal', 'any') and bk in ('number', 'decimal', 'any'):
            dec = lambda c, k: c + ' 1000000 *' if k == 'number' else (c + ' R-ANY>NUM 1000000 *' if k == 'any' else c)
            a, b = dec(a, ak), dec(b, bk)
            if getattr(self, 'stack', None): self.depth -= 1
            f = {'+': '+', '-': '-', '*': '1000000 */', '/': '>R 1000000 R> */', '%': 'MOD', '==': '=', '!=': '<>',
                 '<': '<', '>': '>', '<=': '> 0=', '>=': '< 0='}[op]
            return '%s %s %s' % (a, b, f), ('decimal' if op in '+-*/%' else 'bool')
        a, b = self.to_num(a, ak, line), self.to_num(b, bk, line)
        ak = bk = 'number'
        if getattr(self, 'stack', None): self.depth -= 1
        kind = 'number' if op in '+-*/%' else 'bool'
        short = {('+', '1'): '1+', ('-', '1'): '1-', ('>', '0'): '0>', ('<', '0'): '0<', ('==', '0'): '0=', ('!=', '0'): '0<>'}
        if GENES['short'] and (op, b) in short: return '%s %s' % (a, short[(op, b)]), kind      # one word (gene short, 749)
        forth = {'+': '+', '-': '-', '*': '*', '/': '/', '%': 'MOD', '==': '=', '!=': '<>', '<': '<', '>': '>', '<=': '> 0=', '>=': '< 0='}[op]
        return '%s %s %s' % (a, b, forth), kind
    def unary(self):
        tok = self.peek()
        if tok[1] == 'not': self.i += 1; c, k = self.unary(); return self.truth(c, k) + ' 0=', 'bool'
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
                    code, kind = '%s %s R-GET' % (self.lit_text(f), code), 'any'      # a field's name a literal, shared too (750)
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
            if self.peek()[1] == ',': self.i += 1; continue                # [a, b, c] as well as [a b c] (758)
            tok = self.peek()
            if tok[0] == 'word' and re.fullmatch(r'@[A-Za-z_][A-Za-z0-9_]*', tok[1]):    # [@refs more]: a spread (744)
                self.i += 1
                if self.kind_of(tok[1][1:], tok[2]) != 'list': raise Error('line %d: %s is not a list' % (tok[2], tok[1]))
                code.append('R.%s @ OVER SWAP R-EXTEND' % tok[1][1:]); continue
            c, kd = self.term()
            code.append('%s OVER R-PUSH' % self.box(c, kd))
        self.take('op', ']'); return ' '.join(code), 'list'
    def comprehension(self, j):
        start = self.i; self.i = j + 1                            # for x in src [if cond]
        name = self.take('word')[1]; second = None
        if self.peek()[1] == ',': self.i += 1; second = self.take('word')[1]     # [e for k, v in src] (754)
        self.take('kw', 'in')
        sc, sk = self.expr()
        if sk == 'any': sc, sk = sc + ' R-UNBOX DROP', 'list'          # an item holding a list - a def's parameter (758)
        if sk not in ('list', 'record') or (sk == 'record' and not second):
            raise Error('line %d: for needs a list' % self.peek()[2])
        tmp = '%s.src%d' % (name, j); self.names.update([name, tmp])
        nk = self.bind(name, 'any' if not second else 'number' if sk == 'list' else 'text')
        if second: self.bind(second, 'any')
        cond = None
        self.da_enter([name] + ([second] if second else []))
        if self.peek()[1] == 'if': self.i += 1; cond, ck = self.expr()
        end = self.i; self.take('op', ']'); after = self.i
        self.i = start; ec, ek = self.expr(); self.i = after
        self.da_leave()
        item = '%s OVER R-PUSH' % self.box(ec, ek)
        body = '%s IF %s THEN' % (cond, item) if cond else item
        if second and sk == 'record':                                   # the key a text, or its box where $name is an item (764)
            return ('R-NEW-LIST %s R.%s ! R.%s @ R-KEYS R-LEN 0 ?DO R.%s @ R-KEYS I R-AT%s R.%s ! '
                    'R.%s @ R-VALS I R-AT R.%s ! %s LOOP' % (sc, tmp, tmp, tmp, ' R-ANY>TEXT' if nk == 'text' else '',
                                                           name, tmp, second, body)), 'list'
        if second:
            return ('R-NEW-LIST %s R.%s ! R.%s @ R-LEN 0 ?DO I%s R.%s ! R.%s @ I R-AT R.%s ! %s LOOP' %
                    (sc, tmp, tmp, self.num_into(nk), name, tmp, second, body)), 'list'
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
        in_arg, self.in_arg = getattr(self, 'in_arg', False), False      # a command's argument: a bare word is its text (762)
        tok = self.take()
        k, v, line = tok[:3]
        if v == '[': return self.literal_list()
        if v == '{': self.skip_nl(); return self.literal_record()
        if k == 'word' and v in ('true', 'false'): return ('-1' if v == 'true' else '0'), 'bool'   # 759: booleans
        if k == 'word' and re.fullmatch(r'-?\d+\.\d+', v):               # a decimal (754): fixed point, six places
            whole, frac = v.lstrip('-').split('.'); n = int(whole) * 1000000 + int((frac + '000000')[:6])
            return str(-n if v.startswith('-') else n), 'decimal'
        if k == 'word' and re.fullmatch(r'-?\d+', v):
            if getattr(self, 'stack', None): self.depth += 1
            return v, 'number'
        if k == 'var' and getattr(self, 'stack', None) and v[1:] in self.stack:
            at = self.depth + len(self.stack) - 1 - self.stack.index(v[1:])
            self.depth += 1
            return {0: 'DUP', 1: 'OVER'}.get(at, '%d PICK' % at), 'number'
        if k == 'var' and v[1:] == getattr(self, 'loopvar', None): return 'I', 'number'      # gene loopvar (753)
        if k == 'var' and v[1:] in ('args', 'script') and v[1:] not in self.vars and \
                (self.locals is None or v[1:] not in self.locals):
            return ('R-ARGS', 'list') if v[1:] == 'args' else ('R-SCRIPT', 'text')       # 744
        if k == 'var':
            kv = self.kind_of(v[1:], line)
            if kv in ('text', 'list', 'record', 'any') and self.dal.get(self.da_key(v[1:]), -1) < 0:
                return 'R.%s @ DUP 0= IF S" %s" R-UNSET THEN' % (v[1:], v[1:]), kv     # maybe not set here (772)
            return 'R.%s @' % v[1:], kv
        if v == '$(':
            c = self.command(capture=True); self.take('op', ')')
            return c + ' R-CHECK', 'text'
        if k == 'str': return self.string(v[1:-1], line), 'text'
        if k == 'raw': return self.lit(v[1:-1]), 'text'
        if v == '(':
            if self.run_ahead():
                c = self.command() + ' 0='; self.take('op', ')'); return c, 'bool'   # a run is a term (745)
            c, kd = self.expr(); self.take('op', ')'); return c, kd
        if k == 'word' and self.peek()[1] == '(':
            return self.call(v, line)
        if k == 'word' and not in_arg and (v in self.vars or (self.locals is not None and v in self.locals)):
            raise Error('line %d: %s is a variable - $%s, or "%s" for the text' % (line, v, v, v))   # a slip of the $ rule (762)
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
        else:
            args = [(self.to_num(c, k, line), 'number') for c, k in args]   # a pure def's are numbers (749)
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
        if name == 'range':                                            # Python's: up to, not with, its end (770)
            if len(a) not in (1, 2, 3): raise Error('line %d: range() takes 1 to 3 arguments' % line)
            n = [self.to_num(c, k, line) for c, k in a]
            if len(a) == 1: return '0 %s R-RANGE' % n[0], 'list'
            if len(a) == 2: return '%s %s R-RANGE' % tuple(n), 'list'
            return '%s %s %s R-RANGE-STEP' % tuple(n), 'list'
        if name == 'number': need(1); return '%s R-NUMBER' % self.to_text(*a[0]), 'number'
        if name == 'text': need(1); return self.to_text(*a[0]), 'text'
        cont = lambda x: x[0] + ' R-UNBOX DROP' if x[1] == 'any' else x[0]        # an item holding a list or record (758)
        if name == 'push': need(2); return '%s %s R-PUSH' % (self.box(*a[1]), cont(a[0])), None
        if name == 'extend': need(2); return '%s %s R-EXTEND' % (cont(a[0]), cont(a[1])), None
        if name == 'shift': need(1); return '%s R-SHIFT' % cont(a[0]), 'any'
        if name == 'first': need(1); return '%s 0 R-AT' % cont(a[0]), 'any'
        if name == 'values': need(1); return '%s R-VALS' % cont(a[0]), 'list'                     # 758
        if name == 'sort': need(1); return '%s R-SORT' % cont(a[0]), 'list'
        if name == 'split': need(2); return '%s %s R-SPLIT' % (self.to_text(*a[0]), self.to_text(*a[1])), 'list'
        if name == 'slice':                                            # a list's; a text's and a record's (754)
            word, kd = {'text': ('R-TSLICE', 'text'), 'record': ('R-RSLICE', 'record')}.get(a[0][1], ('R-SLICE', 'list'))
            if len(a) == 2:
                rest = {'R-SLICE': 'OVER R-LEN', 'R-TSLICE': 'OVER @', 'R-RSLICE': 'OVER R-KEYS R-LEN'}[word]
                return '%s %s %s %s' % (a[0][0], self.to_num(*a[1], line), rest, word), kd
            need(3); return '%s %s %s %s' % (a[0][0], self.to_num(*a[1], line), self.to_num(*a[2], line), word), kd
        if name == 'keys': need(1); return '%s R-KEYS' % (a[0][0] + ' R-UNBOX DROP' if a[0][1] == 'any' else a[0][0]), 'list'
        if name in ('read', 'upper', 'lower', 'trim', 'base'):              # 754: texts and files
            need(1); return '%s %s' % (self.to_text(*a[0]), {'read': 'R-READ', 'upper': 'R-UPPER', 'lower': 'R-LOWER',
                                                                'trim': 'R-TRIM', 'base': 'R-BASE'}[name]), 'text'
        if name == 'write': need(2); return '%s %s R-WRITE' % (self.to_text(*a[0]), self.to_text(*a[1])), None
        if name in ('starts', 'ends'):
            need(2); return '%s %s %s' % (self.to_text(*a[0]), self.to_text(*a[1]), 'R-STARTS' if name == 'starts' else 'R-ENDS'), 'bool'
        if name == 'sum': need(1); return '%s R-SUM' % a[0][0], 'number'
        dec = lambda c, k: c if k == 'decimal' else c + ' 1000000 *' if k == 'number' else c + ' R-ANY>DEC'   # 760
        if name in ('max', 'min') and len(a) == 1:                     # max(list), min(list): an item (760)
            return '%s %s' % (a[0][0] + ' R-UNBOX DROP' if a[0][1] == 'any' else a[0][0], 'R-LMAX' if name == 'max' else 'R-LMIN'), 'any'
        if name == 'log': need(1); return '%s R-LOG' % dec(*a[0]), 'decimal'
        if name == 'exp': need(1); return '%s R-EXP' % dec(*a[0]), 'decimal'
        if name == 'decimal': need(1); return '%s R-TEXT>DEC' % self.to_text(*a[0]), 'decimal'
        if name == 'contains': need(2); return '%s %s R-CONTAINS' % (self.to_text(*a[0]), self.to_text(*a[1])), 'bool'
        if name == 'replace': need(3); return '%s %s %s R-REPLACE' % tuple(self.to_text(*x) for x in a), 'text'
        if name in ('max', 'min'):
            need(2); kd = 'decimal' if 'decimal' in (a[0][1], a[1][1]) else 'number'
            conv = (lambda c, k: c + ' 1000000 *' if k == 'number' else c) if kd == 'decimal' else (lambda c, k: self.to_num(c, k, line))
            return '%s %s %s' % (conv(*a[0]), conv(*a[1]), name.upper()), kd
        if name == 'at': need(3); return '%s %s %s R-AT-OR' % (a[0][0], self.to_text(*a[1]), self.box(*a[2])), 'any'
        if name == 'sort-by': need(3); return '%s %s %s R-SORT-BY' % (a[0][0], self.to_text(*a[1]), self.to_text(*a[2])), 'record'
        if name == 'arg':                                              # 744; arg(n, default) 747
            if len(a) == 2 and GENES['argdefault']: return '%s R-ARG %s R-DEFAULT' % (self.to_num(*a[0], line), self.to_text(*a[1])), 'text'
            need(1); return '%s R-ARG' % self.to_num(*a[0], line), 'text'
        if name == 'match': need(2); return '%s %s R-MATCH' % (self.to_text(*a[0]), self.to_text(*a[1])), 'list'   # 746
        if name == 'all': need(2); return '%s %s R-ALL' % (self.to_text(*a[0]), self.to_text(*a[1])), 'list'
        if name == 'sub': need(3); return '%s %s %s R-SUB' % (self.to_text(*a[0]), self.to_text(*a[1]), self.to_text(*a[2])), 'text'
        if name == 'env': need(1); return '%s R-ENV' % self.to_text(*a[0]), 'text'
        if name == 'default': need(2); return '%s %s R-DEFAULT' % (self.to_text(*a[0]), self.to_text(*a[1])), 'text'
        return None
    def shared(self, code):
        """Gene littext (750): a literal text made once, as the program is read - R-LIT-n."""
        if not GENES['littext']: return code
        if code not in self.lits: self.lits[code] = len(self.lits) + 1
        return 'R-LIT-%d' % self.lits[code]
    def lit(self, s):
        return self.shared('S" %s" R-TEXT' % s if '"' not in s else self.bytes_lit(s))
    def bytes_lit(self, s):
        return ' '.join('%d' % b for b in s.encode()) + ' %d R-BYTES' % len(s.encode())
    def string(self, body, line, typed=False):
        parts, pieces, i, lit = [], [], 0, ''   # pieces: ('lit', text) or ('code', code) - for echolit (753)
        while i < len(body):
            c = body[i]
            if c == '\\' and i + 1 < len(body):
                lit += {'n': '\n', 't': '\t'}.get(body[i + 1], body[i + 1]); i += 2; continue
            if body.startswith('$(', i):
                if lit: parts.append(self.lit_text(lit) if not typed else ''); pieces.append(('lit', lit)); lit = ''
                depth, j = 1, i + 2
                while depth: depth += {'(': 1, ')': -1}.get(body[j], 0); j += 1
                sub = Compiler.__new__(Compiler); sub.__dict__ = dict(self.__dict__)
                sub.t = tokenize(body[i + 2:j - 1]); sub.i = 0
                parts.append(sub.command(capture=True) + ' R-CHECK'); pieces.append(('code', parts[-1])); i = j; continue
            m = re.match(r'\$([A-Za-z_][A-Za-z0-9_]*)', body[i:])
            if m or c == '{':
                if lit: parts.append(self.lit_text(lit) if not typed else ''); pieces.append(('lit', lit)); lit = ''
                if m:
                    name = m.group(1); i += m.end()
                    code, kind = ('I', 'number') if name == getattr(self, 'loopvar', None) else ('R.%s @' % name, self.kind_of(name, line))
                    while kind in ('record', 'any'):                  # "$host.name": a field, in a string too
                        f = re.match(r'\.([A-Za-z_][A-Za-z0-9_]*)', body[i:])
                        if not f: break
                        code = ('%s R-UNBOX DROP' % code) if kind == 'any' else code
                        code, kind = '%s %s R-GET' % (self.lit_text(f.group(1)), code), 'any'; i += f.end()
                    parts.append(self.to_text(code, kind)); pieces.append(('code', parts[-1]))
                else:
                    depth, j = 1, i + 1
                    while depth: depth += {'{': 1, '}': -1}.get(body[j], 0); j += 1
                    sub = Compiler.__new__(Compiler); sub.__dict__ = dict(self.__dict__)
                    sub.t = tokenize(body[i + 1:j - 1]); sub.i = 0
                    c2, k2 = sub.expr(); parts.append(self.to_text(c2, k2)); pieces.append(('code', parts[-1])); i = j
                continue
            lit += c; i += 1
        if typed: return pieces + [('lit', lit)]
        if lit or not parts: parts.append(self.lit_text(lit))
        return parts[0] if len(parts) == 1 else '%s %d R-CONCAT' % (' '.join(parts), len(parts))
    def lit_text(self, s):
        if '"' in s or '\n' in s or '\t' in s: return self.shared(self.bytes_lit(s))
        return self.shared('S" %s" R-TEXT' % s)
    KCODE = {'number': 'K-NUM', 'text': 'K-TEXT', 'bool': 'K-BOOL', 'list': 'K-LIST', 'record': 'K-REC', 'decimal': 'K-DEC'}
    def to_text(self, code, kind):
        if kind == 'text': return code
        if kind == 'any': return code + ' R-ANY>TEXT'
        if kind == 'list': return code + ' S"  " R-TEXT R-JOIN'          # a list as text: its items, a blank between
        if kind == 'decimal': return code + ' R-DEC>TEXT'                 # 754
        if kind == 'bool': return code + ' R-BOOL>TEXT'                   # 759: true or false
        return code + ' R-NUM'
    def to_num(self, code, kind, line):
        if kind in ('number', 'bool'): return code
        if kind == 'decimal': return code + ' 1000000 /'                   # 754: its whole part
        if kind == 'any': return code + ' R-ANY>NUM'
        raise Error('line %d: a number is needed here, not a %s' % (line, kind))
    def convert(self, code, kind, want, line):
        """A value made the kind a def's -> names: found by the search (749) - with purestack off, a
        parameter is a box, and fib returned the box's address as its number."""
        if want in (None, kind) or want == 'any': return code
        if want in ('number', 'bool'): return self.to_num(code, kind, line)
        if want == 'text': return self.to_text(code, kind)
        if kind == 'any': return code + ' R-UNBOX DROP'
        raise Error('line %d: this returns a %s, not a %s' % (line, kind, want))
    def box(self, code, kind):
        return code if kind == 'any' else '%s %s R-BOX' % (code, self.KCODE[kind])

    # statements
    def block(self):
        self.take('op', '{'); out = []
        self.da_enter(self.da_next); self.da_next = []
        self.skip_nl()
        while self.peek()[1] != '}':
            out.append(self.statement()); self.skip_nl()
        self.take('op', '}'); self.da_leave(); return ' '.join(o for o in out if o)
    def statement(self):
        k, v, line = self.peek()[:3]
        start = self.i
        if v == 'if': out = self.if_()
        elif k == 'word' and v == 'cd' and self.peek(1)[1] not in ('=', '(', '['):     # cd DIR, cd DIR { ... } (760)
            self.i += 1; r = self.arg_item(); c = self.to_text(*r) if isinstance(r, tuple) else r
            out = 'R-CWD-PUSH %s R-CD %s R-CWD-POP' % (c, self.block()) if self.peek()[1] == '{' else '%s R-CD' % c
        elif v == 'while':
            self.i += 1; c = self.cond()
            out = 'BEGIN %s WHILE %s REPEAT' % (c, self.block())
        elif v == 'return':
            if getattr(self, 'hoists', None) and True in self.hoists:
                raise Error('line %d: return inside a loop that has a continue - not yet' % line)
            self.i += 1; c, kd = self.expr()
            want = self.funcs[self.current][1] if getattr(self, 'current', None) else None
            c = self.convert(c, kd, want, line)                   # to the def's -> kind (749: a boxed parameter returned)
            if getattr(self, 'stack', None):
                c += ' NIP' * len(self.stack); self.depth -= 1        # the result, the parameters dropped under it
            out = '%s EXIT' % c
        elif v == 'def': out = self.def_(); return ''
        elif v == 'for': out = self.for_()
        elif v == 'break':
            self.i += 1; out = '-1 R-BRK ! EXIT' if getattr(self, 'hoists', None) and self.hoists[-1] else 'LEAVE'
        elif k == 'word' and v == 'continue':
            if not (getattr(self, 'hoists', None) and self.hoists[-1]): raise Error('line %d: continue outside a for loop' % line)
            self.i += 1; out = 'EXIT'
        elif k == 'word' and v == 'par' and self.peek(1)[1] == 'for':
            self.i += 1; out = self.for_(par=True)
        elif k == 'word' and v == 'fail' and self.peek(1)[1] != '(':
            self.i += 1; c, kd = self.expr(); out = '%s R-FAIL' % self.to_text(c, kd)       # 744
        elif k == 'word' and v == 'exit' and self.peek(1)[1] != '(':
            self.i += 1
            if self.peek()[0] in ('nl', 'eof') or self.peek()[1] in (';', '}'): out = '0 R-EXIT'
            else: c, kd = self.expr(); out = '%s R-EXIT' % self.to_num(c, kd, line)
        elif k == 'word' and v == 'on' and self.peek(1)[1] == 'EXIT':
            self.i += 2; self.on_n = getattr(self, 'on_n', 0) + 1
            self.defs.append(': R-EXIT-%d %s ;' % (self.on_n, self.block()))
            out = "['] R-EXIT-%d R-ON-EXIT" % self.on_n
        elif k == 'word' and self.peek(1)[1] == '[' and self.peek(1)[3] == self.peek()[4]:
            name = v; self.i += 2
            ic, ik = self.expr(); self.take('op', ']'); self.take('op', '=')
            c, kd = self.expr(); ck = self.kind_of(name, line)
            if ck == 'list': out = '%s R.%s @ %s R-SET' % (self.box(c, kd), name, self.to_num(ic, ik, line))
            elif ck == 'record': out = '%s %s R.%s @ R-PUT' % (self.box(c, kd), self.to_text(ic, ik), name)
            elif ck == 'any': out = '%s %s R.%s @ R-ASSIGN-ANY' % (self.box(c, kd), self.box(ic, ik), name)   # 758
            else: raise Error('line %d: $%s is not a list or a record' % (line, name))
        elif k == 'word' and self.peek(1)[1] in ('=', '+=', '-='):
            name = v; self.i += 1; op = self.take()[1]
            c, kd = self.expr()
            sc = self.scope()
            if op != '=':
                vk = self.kind_of(name, line)
                if vk not in ('number', 'any', 'decimal'): raise Error('line %d: %s needs a number to change' % (line, op))
                c, kd = self.binop('+' if op == '+=' else '-', 'R.%s @' % name, vk, c, kd)
                if vk == 'any': c, kd = self.box(c, kd), 'any'          # an item holding a number stays an item (758)
            elif self.infer is not None: pass                                # the first pass: every binding as it comes (764)
            elif name in sc and sc[name] in ('text', 'number') and kd == 'any':
                c, kd = (self.to_text(c, kd), 'text') if sc[name] == 'text' else (self.to_num(c, kd, line), 'number')   # 758
            elif name in sc and sc[name] == 'decimal' and kd == 'number':
                c, kd = c + ' 1000000 *', 'decimal'                  # a number into a decimal variable (771)
            elif name in sc and sc[name] == 'any' and kd != 'any':
                c, kd = self.box(c, kd), 'any'                      # an item takes any value, boxed (754)
            elif name in sc and sc[name] != kd:
                raise Error('line %d: $%s is %s; it cannot become %s' % (line, name, sc[name], kd))
            if self.infer is not None: self.bind(name, kd)
            else: sc[name] = kd; self.names.add(name)
            if op == '=': self.da_mark(name)                                 # certainly set from here (772)
            out = '%s R.%s !' % (c, name)
        elif GENES['warn'] and k == 'word' and v == 'warn' and self.peek(1)[1] != '(':   # warn ...: the err port (747; a gene 751)
            self.i += 1
            parts, _ = self.args((';', '}'))
            if not parts: out = '0 0 R-TEXT R-ERR-TYPE'
            else: out = ' S"  " R-TEXT '.join(parts) + ' %d R-CONCAT R-ERR-TYPE' % (2 * len(parts) - 1)
        elif k == 'word' and v == 'echo' and not self.plumbed():
            self.i += 1
            if GENES['echolit']: out = self.echo_typed()
            else:
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
        word = {False: 'PL-STAGE', True: 'PL-STAGE-L', 'X': 'PL-STAGE-X'}
        body = ' '.join('%s %s %s' % (s[0], '-1' if k == len(stages) - 1 else '0', word[s[1]])
                        for k, s in enumerate(stages))
        return '%s PL-BEGIN %s PL-END' % ('-1' if capture else '0', body)
    def echo_typed(self):
        """Gene echolit (753): echo's items typed as they come - a literal run (words, raw texts, the
        literal parts of strings, the blanks between items) one S" ... " TYPE, no text made for it."""
        pieces, first = [], True
        while self.peek()[0] not in ('nl', 'eof') and self.peek()[1] not in (';', '}'):
            tok = self.peek()
            if not first and tok[3] != self.t[self.i - 1][4]: pieces.append(('lit', ' '))
            first = False
            if tok[0] == 'str': self.i += 1; pieces += self.string(tok[1][1:-1], tok[2], typed=True)
            elif tok[0] == 'raw': self.i += 1; pieces.append(('lit', tok[1][1:-1]))
            elif tok[0] == 'kw' or tok[1] in (',', '=', '==', '!=', '<=', '>=', '+=', '-=', '->'):
                self.i += 1; pieces.append(('lit', tok[1]))
            elif tok[0] == 'word' and self.peek(1)[1] != '(' and not re.fullmatch(r'-?\d+', tok[1]):
                self.i += 1; pieces.append(('lit', tok[1]))
            else: pieces.append(('code', self.arg_item()))
        out, lit = [], ''
        for kind, x in pieces:
            if kind == 'lit': lit += x; continue
            if lit: out.append(self.typed_lit(lit)); lit = ''
            out.append(x + ' R-TYPE')
        if lit: out.append(self.typed_lit(lit))
        return ' '.join(out + ['R-NL'])
    def typed_lit(self, s):
        if '"' in s or '\n' in s or '\t' in s: return self.bytes_lit(s) + ' R-TYPE'
        return 'S" %s" TYPE' % s
    def arg_item(self):
        tok = self.peek()
        if tok[1] == '{':
            self.i += 1; c, kd = self.expr(); self.take('op', '}')
        elif tok[0] == 'kw' or tok[1] in (',', '=', '==', '!=', '<=', '>=', '+=', '-=', '->') or (tok[0] == 'word' and tok[1] in ('true', 'false')):
            c, kd = self.lit(self.take()[1]), 'text'              # a keyword, an operator, true or false: plain text in an argument
        else:
            self.in_arg = True; c, kd = self.term()
        return self.to_text(c, kd)
    def args(self, stop, spread=False):
        """The arguments to the end of the statement; items touching each
        other join into one, as sh's words do (RILL-LEDGER.md 732)."""
        parts, redirs = [], []
        while self.peek()[0] not in ('nl', 'eof') and self.peek()[1] not in stop:
            tok, nxt = self.peek(), self.peek(1)
            if stop and tok[0] == 'word' and tok[1] in self.PORTS and nxt[1] in ('>', '>>') and nxt[3] == tok[4]:
                self.i += 1; redirs.append(self.redirect(tok[1])); continue
            if stop and tok[1] in ('>', '>>', '<') and '|' in stop:
                redirs.append(self.redirect('in' if tok[1] == '<' else 'out')); continue
            if spread and tok[0] == 'word' and re.fullmatch(r'@[A-Za-z_][A-Za-z0-9_]*', tok[1]):
                self.i += 1; name = tok[1][1:]
                if self.kind_of(name, tok[2]) != 'list': raise Error('line %d: @%s is not a list' % (tok[2], name))
                parts.append('R.%s @ OVER SWAP R-EXTEND' % name); kinds_spread = True
                continue
            touching = parts and tok[3] == self.t[self.i - 1][4] and not parts[-1].endswith('R-EXTEND')
            c = self.arg_item()
            if touching: parts[-1] = '%s %s 2 R-CONCAT' % (parts[-1], c)
            else: parts.append(c)
        if spread:
            parts = [p if p.endswith('R-EXTEND') else p + ' K-TEXT R-BOX OVER R-PUSH' for p in parts]
        return parts, redirs
    def stage(self):
        stop = (';', '}', ')', '??', '|')
        j = self.i                                                   # a spread ahead in the stage? (744)
        while self.t[j][0] not in ('nl', 'eof') and self.t[j][1] not in stop:
            if self.t[j][0] == 'word' and re.fullmatch(r'@[A-Za-z_][A-Za-z0-9_]*', self.t[j][1]): break
            j += 1
        spread = self.t[j][0] == 'word' and self.t[j][1].startswith('@')
        tok = self.peek()
        if tok[0] == 'word' and tok[1] in self.funcs and self.peek(1)[1] != '(':      # a def as a stage (745)
            self.i += 1; parts, redirs = self.args(stop, False)
            if parts: raise Error('line %d: a def in a pipeline takes no arguments yet' % tok[2])
            return ' '.join(redirs + ["['] R:%s" % tok[1]]), 'X'
        parts, redirs = self.args(stop, spread)
        if spread: return ' '.join(redirs + ['R-NEW-LIST'] + parts), True
        return ' '.join(redirs + parts) + ' %d' % len(parts), False
    def redirect(self, port):
        op = self.take()[1]
        tok = self.peek()
        if op != '<' and tok[0] == 'word' and tok[1] in ('out', 'err') and tok[3] == self.t[self.i - 1][4]:
            self.i += 1                                           # a port joined to another: err>out
            return '%d %d R-RD-DUP' % (self.PORTS[tok[1]], self.PORTS[port])
        c, kd = self.term()
        code = '%s %s %d R-RD-FILE' % (self.to_text(c, kd), self.MODES[op], self.PORTS[port])
        return code + (' 1 2 R-RD-DUP' if port == 'all' else '')
    def run_ahead(self):
        """After a (: a run, unless its second token makes it an expression."""
        second = self.peek(1)
        return self.peek()[0] == 'word' and second[1] != '(' and not (second[0] in ('kw', 'op') and second[1] in
                ('in', 'not', 'and', 'or', '==', '!=', '<', '>', '<=', '>=')) and second[1] not in self.PREC
    def truth(self, code, kind):
        """Gene truth (751): an empty text, list or record is false."""
        if not GENES['truth']: return code
        if kind in ('text', 'list'): return code + ' @ 0<>'
        if kind == 'record': return code + ' @ @ 0<>'
        if kind == 'any': return code + ' R-ANY>BOOL'
        return code
    def cond(self):
        if self.peek()[1] != '(': raise Error('line %d: a condition is in ( )' % self.peek()[2])
        c, kd = self.expr(); return self.truth(c, kd)
    def loopvar_ok(self, name):
        """The body ahead (its { the current token) leaves the index to I alone: no loop inside it, no
        break or continue, no par, no def, no on EXIT, and nothing assigned to the variable."""
        j, depth = self.i, 0
        while True:
            k, v = self.t[j][0], self.t[j][1]
            if v == '{': depth += 1
            elif v == '}':
                depth -= 1
                if depth == 0: return True
            elif (k == 'kw' and v in ('for', 'def', 'break')) or (k == 'word' and v in ('continue', 'par', 'EXIT')):   # break a keyword (770)
                return False
            elif k == 'word' and v == name and self.t[j + 1][1] in ('=', '+=', '-=', '['): return False
            j += 1
    def has_continue(self):
        """Does the block ahead hold a continue at its own level (not in a loop inside it)?"""
        j, stack, pending = self.i, [], False
        while True:
            k, v = self.t[j][0], self.t[j][1]
            if v == '{': stack.append('loop' if pending else 'block'); pending = False
            elif v == '}':
                stack.pop()
                if not stack: return False
            elif v in ('for', 'while') and k == 'kw': pending = True
            elif k == 'word' and v == 'continue' and 'loop' not in stack[1:]: return True
            j += 1
    def loop_body(self):
        hoists = getattr(self, 'hoists', [])
        if not self.has_continue():
            hoists.append(False); self.hoists = hoists
            code = self.block(); hoists.pop(); return code
        self.body_n = getattr(self, 'body_n', 0) + 1; n = self.body_n
        hoists.append(True); self.hoists = hoists
        code = self.block(); hoists.pop()
        self.defs.append(': R-BODY-%d %s ;' % (n, code))
        return 'R-BODY-%d R-BRK @ IF 0 R-BRK ! LEAVE THEN' % n
    def par_wrap(self, body, par):
        return 'R-PAR-FORK IF %s R-PAR-DONE THEN' % body if par else body
    def range_commas(self):               # the commas at range( ... )'s own level: two mean a step
        depth, n, j = 0, 0, self.i + 2
        while self.t[j][0] != 'eof':
            v = self.t[j][1]
            if v in ('(', '[', '{'): depth += 1
            elif v in (')', ']', '}'):
                if depth == 0: return n
                depth -= 1
            elif v == ',' and depth == 0: n += 1
            j += 1
        return n
    def for_(self, par=False):
        self.take('kw', 'for'); a = self.take('word')[1]; b = None
        if self.peek()[1] == ',': self.i += 1; b = self.take('word')[1]
        self.take('kw', 'in'); line = self.peek()[2]
        if GENES['rangeloop'] and self.peek()[1] == 'range' and self.peek(1)[1] == '(' and self.range_commas() < 2:   # a counted loop
            self.i += 2; lo, lk = self.expr()                          # range(b) or range(a, b): a step goes the list's way (770)
            if self.peek()[1] == ',': self.i += 1; hi, hk = self.expr()
            else: lo, lk, hi, hk = '0', 'number', lo, lk
            self.take('op', ')')
            if b: raise Error('line %d: for i, x needs a list' % line)
            box = self.num_into(self.bind(a, 'number'))                 # an item or a decimal, where $a is bound to others too
            self.da_next = [a]
            if GENES['loopvar'] and not par and self.loopvar_ok(a):        # gene loopvar (753)
                outer = getattr(self, 'loopvar', None); self.loopvar = a
                body = self.loop_body(); self.loopvar = outer
                return '%s %s TUCK MAX SWAP 2DUP ?DO %s LOOP OVER < IF 1-%s R.%s ! ELSE DROP THEN' % (
                    self.to_num(hi, hk, line), self.to_num(lo, lk, line), body, box, a)     # the last value kept, as Python
            out = '%s %s TUCK MAX SWAP ?DO I%s R.%s ! %s LOOP' % (self.to_num(hi, hk, line), self.to_num(lo, lk, line), box, a,
                                                                 self.par_wrap(self.loop_body(), par))
            return 'R-PAR-BEGIN %s R-PAR-END' % out if par else out
        sc, sk = self.expr()
        tmp = '%s.src%d' % (a, self.i); self.names.update([a, tmp])
        if sk == 'record':                                               # for k, v in a record
            key, val = (a, b) if b else (a, None)
            kk = self.bind(key, 'text'); self.da_next = [key] + ([val] if val else [])
            if val: self.bind(val, 'any')
            setv = ('R.%s @ R-VALS I R-AT R.%s ! ' % (tmp, val)) if val else ''
            out = ('%s R.%s ! R.%s @ R-KEYS R-LEN 0 ?DO R.%s @ R-KEYS I R-AT%s R.%s ! %s%s LOOP'
                   % (sc, tmp, tmp, tmp, ' R-ANY>TEXT' if kk == 'text' else '', key, setv, self.par_wrap(self.loop_body(), par)))
            return 'R-PAR-BEGIN %s R-PAR-END' % out if par else out
        if sk not in ('list', 'any'): raise Error('line %d: for needs a list or a record' % line)
        if sk == 'any': sc += ' R-UNBOX DROP'
        idx, item = (a, b) if b else (None, a)
        self.da_next = [item] + ([idx] if idx else [])
        self.bind(item, 'any')
        seti = ''
        if idx: seti = 'I%s R.%s ! ' % (self.num_into(self.bind(idx, 'number')), idx)
        out = ('%s R.%s ! R.%s @ R-LEN 0 ?DO %sR.%s @ I R-AT R.%s ! %s LOOP'
               % (sc, tmp, tmp, seti, tmp, item, self.par_wrap(self.loop_body(), par)))
        return 'R-PAR-BEGIN %s R-PAR-END' % out if par else out
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
        if GENES['purestack'] and self.pure(params):                    # gene purestack (749)
            self.pure_defs = getattr(self, 'pure_defs', set()) | {name}
            self.stack, self.depth = params, 0
            body = self.block()
            self.stack = None
            tail = '' if kind else ' DROP' * len(params)
            body = (re.sub(r' DUP NIP\b', '', ' ' + body + tail) if GENES['dupnip'] else ' ' + body + tail).strip()
            self.defs.append(': R:%s %s ;' % (name, body)); self.current = None
            return
        outer = self.locals; self.locals = {p: 'any' for p in params}
        self.names.update(params)
        if self.infer is not None:
            for p in params: self.bind(p, 'any')
        if self.fixed is not None:
            self.locals.update({n: k for (d, n), k in self.fixed.items() if d == name})
        self.da_next = list(params)
        body = self.block()
        scratch = [n for n in self.locals if n not in params]
        self.names.update(scratch)
        self.defs.append(': R:%s SHADOW{ %s | %s } %s ;' % (name, ' '.join('R.' + p for p in params),
                                                         ' '.join('R.' + s for s in scratch), body))
        self.locals = outer; self.current = None
    def program(self):
        main = []; self.skip_nl(); self.lits = {}
        if self.fixed is not None: self.vars.update({n: k for (d, n), k in self.fixed.items() if d is None})
        while self.peek()[0] != 'eof':
            line = self.peek()[2]; start = self.i
            out = self.statement()
            if out: main.append(out)
            self.lines.append((line, out))
            self.skip_nl()
        return ('\n'.join('VARIABLE R.%s' % n for n in sorted(self.names)) + '\n' +
                ''.join('%s CONSTANT R-LIT-%d\n' % (c, n) for c, n in self.lits.items()) +
                '\n'.join(self.defs) + '\n: R-MAIN %s ;\nR-MAIN\n' % ' '.join(main))

if __name__ == '__main__':
    src = open(sys.argv[1], encoding='utf-8').read()
    c = Compiler(src)
    try:
        if GENES['infer']:                                    # gene infer (764): a first pass for the kinds, the second for the code
            c.infer = {}; c.program()
            fixed = {key: (ks.pop() if len(ks) == 1 else 'decimal' if ks == {'number', 'decimal'} else 'any')
                     for key, ks in c.infer.items()}                 # a number and a decimal join to a decimal (771)
            c = Compiler(src); c.fixed = fixed
        forth = c.program()
    except Error as e: sys.exit('rillc: %s: %s' % (sys.argv[1], e))
    if '--list' in sys.argv:
        print(forth)
    else:
        sys.stdout.write(forth)
