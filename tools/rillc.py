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

def scan_nested(s, i, closer):          # from just inside an opener to just past its closer, strings in it skipped whole (789)
    stack = [closer]
    while i < len(s) and stack:
        c = s[i]
        if c == '\\': i += 2; continue
        if c == '"': i = scan_str(s, i); continue
        if c == "'":
            k = s.find("'", i + 1); i = k + 1 if k >= 0 else len(s); continue
        if c == '{': stack.append('}')
        elif c == '(': stack.append(')')
        elif c == stack[-1]: stack.pop()
        i += 1
    return None if stack else i                # None: never closed

def scan_str(s, i):                         # just past the "..." at i: its {...} and $(...) may hold strings of their own (789)
    i += 1
    while i < len(s):
        c = s[i]
        if c == '\\': i += 2; continue
        if c == '"': return i + 1
        if c == '{' or (c == '$' and s[i + 1:i + 2] == '('):
            j = scan_nested(s, i + (1 if c == '{' else 2), '}' if c == '{' else ')')
            i = j if j is not None else len(s); continue
        i += 1
    return len(s)

def tokenize(src):
    toks, line, sq, pos = [], 1, 0, 0
    while pos < len(src):
        if src[pos] == '"':                                       # a string, as scan_str finds its end (789)
            end = scan_str(src, pos); v = src[pos:end]
            toks.append(('str', v, line, pos, end)); line += v.count('\n'); pos = end; continue
        m = TOKEN.match(src, pos)
        if not m: pos += 1; continue                              # a character no token takes, passed over as finditer did
        k = m.lastgroup; v = m.group(); pos = m.end()
        if k == 'op' and v in ('[', ']'): sq = sq + 1 if v == '[' else max(sq - 1, 0)
        if k == 'nl' and sq: line += 1; continue                 # inside [ ]: the line goes on, as Python's (782)
        if k == 'nl': toks.append(('nl', v, line, m.start(), m.end())); line += 1
        elif k in ('ws', 'comment'): continue
        elif k == 'word' and v in KEYWORDS: toks.append(('kw', v, line, m.start(), m.end()))
        else:
            toks.append((k, v, line, m.start(), m.end()))
            if k == 'raw': line += v.count('\n')                 # a raw string over lines: the next token on its last (789)
    toks.append(('eof', '', line, len(src), len(src)))
    return toks

class Compiler:
    def __init__(self, src):
        self.t = tokenize(src); self.i = 0; self.src = src
        self.has_on_exit = any(self.t[j][1] == 'on' and self.t[j + 1][1] == 'EXIT' for j in range(len(self.t) - 1))   # 786
        self.none_init = set()  # the script's numbers read where they may not be set: R-NONE until they are (785) - one set, shared with sub-compilers
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
    def case_pattern(self):              # a case arm's pattern (783): a string or $x, a term; else touching tokens, as written
        if self.peek()[0] in ('str', 'raw', 'var'):                    # quoted: the text itself, as the shell's
            q = self.peek()[0] != 'var'; c, kd = self.term(); return self.to_text(c, kd), 'R-T=' if q else 'R-GLOB?'
        j = self.i; start = self.t[j][3]
        while True:
            j += 1
            if self.t[j][0] in ('nl', 'eof') or self.t[j][3] != self.t[j - 1][4] or self.t[j][1] == '{': break
        text = self.src[start:self.t[j - 1][4]]; self.i = j
        return self.lit_text(text), 'R-GLOB?'
    def case_(self):                     # case subject { pat pat { block } ... }: the first arm with a pattern that matches
        self.i += 1; sc, sk = self.expr(); code = [self.to_text(sc, sk)]; self.take('op', '{'); arms = 0
        while True:
            self.skip_nl()
            if self.peek()[1] == '}': self.i += 1; break
            pats = []
            while self.peek()[1] != '{':
                if self.peek()[0] in ('nl', 'eof'): raise Error('line %d: a case arm is patterns, then a block' % self.peek()[2])
                pats.append(self.case_pattern())
            if not pats: raise Error('line %d: a case arm is patterns, then a block' % self.peek()[2])
            test = ' '.join(('DUP %s %s' if n == 0 else 'OVER %s %s OR') % p for n, p in enumerate(pats))
            code.append('%s IF DROP %s ELSE' % (test, self.block())); arms += 1
        return ' '.join(code) + ' DROP' + ' THEN' * arms
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
        return '' if k == 'number' else ' R-N>D' if k == 'decimal' else ' K-NUM R-BOX'
    def bind(self, name, kind):
        """A binding of name to a value of kind: the kind the variable has from here (gene infer, 764)."""
        sc = self.scope(); self.names.add(name)
        if self.infer is not None: self.infer.setdefault((self.skey(), name), set()).add(kind)
        elif self.fixed is not None and (self.skey(), name) in self.fixed: kind = self.fixed[(self.skey(), name)]
        sc[name] = kind; return kind
    def spread_code(self, name, line):    # @name: its items - the script's arguments for @args, unless it set its own (786)
        if name == 'args' and name not in self.vars and (self.locals is None or name not in self.locals): return 'R-ARGS'
        k = self.kind_of(name, line)
        if k == 'any': return 'R.%s @ R-AS-LIST' % name                        # an item: its list, checked (799)
        if k != 'list': raise Error('line %d: @%s is not a list' % (line, name))
        return 'R.%s @' % name
    def read_var(self, name, line):       # $name, in an expression or a string - the image's READ-VAR (785)
        if name in ('args', 'script') and name not in self.vars and (self.locals is None or name not in self.locals):
            return ('R-ARGS', 'list') if name == 'args' else ('R-SCRIPT', 'text')       # 744
        kv = self.kind_of(name, line, forward=True)
        if kv in ('text', 'list', 'record', 'any') and self.dal.get(self.da_key(name), -1) < 0:
            return 'R.%s @ DUP 0= IF S" %s" R-UNSET THEN' % (name, name), kv     # maybe not set here (772)
        if self.dal.get(self.da_key(name), -1) < 0 and self.da_key(name)[0] is None:   # a number of the script's (785):
            self.none_init.add(name)                                                   # R-NONE until it is set
            return 'R.%s @ DUP R-NONE = IF S" %s" R-UNSET THEN' % (name, name), kv
        return 'R.%s @' % name, kv
    def kind_of(self, name, line, forward=False):
        if self.locals is not None and name in self.locals: return self.locals[name]
        if name in self.vars: return self.vars[name]
        if forward and self.locals is not None and self.fixed is not None and (None, name) in self.fixed:
            return self.fixed[(None, name)]              # a def reads a global set further down, as Python's (785)
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
            if bk == 'text': return '%s %s SWAP R-CONTAINS%s' % (self.to_text(a, ak), b, neg), 'bool'   # a part of a text (798)
            raise Error('line %d: in needs a list, a record or a text' % line)
        if op == '+' and {ak, bk} & {'text', 'list'}:                               # one way each (800)
            raise Error('line %d: + adds numbers - texts join in a string, lists as [@a @b]' % line)
        if op in ('==', '!=') and ak == 'any' and bk == 'any':                        # two items (758)
            return '%s %s R-BOX=%s' % (a, b, '' if op == '==' else ' 0='), 'bool'
        if op in ('==', '!=') and 'text' in (ak, bk) and ak in ('text', 'any') and bk in ('text', 'any'):
            return '%s %s R-T=%s' % (self.to_text(a, ak), self.to_text(b, bk), '' if op == '==' else ' 0='), 'bool'
        if op in ('<', '<=', '>', '>=') and ak == 'any' and bk == 'any':           # two items: their kinds decide, as Python's (786)
            return '%s %s R-ANY-CMP %s' % (a, b, {'<': '0<', '<=': '0> 0=', '>': '0>', '>=': '0< 0='}[op]), 'bool'
        if op in ('<', '<=', '>', '>=') and 'text' in (ak, bk) and ak in ('text', 'any') and bk in ('text', 'any'):   # 786
            return '%s %s R-TCMP %s' % (self.to_text(a, ak), self.to_text(b, bk),
                                        {'<': '0<', '<=': '0> 0=', '>': '0>', '>=': '0< 0='}[op]), 'bool'   # texts in order, as Python's
        if op in ('==', '!=') and ak in ('list', 'record', 'any') and bk in ('list', 'record', 'any'):   # by what they hold (782)
            return '%s %s R-BOX=%s' % (self.box(a, ak), self.box(b, bk), '' if op == '==' else ' 0='), 'bool'
        if 'decimal' in (ak, bk) and ak in ('number', 'decimal', 'any') and bk in ('number', 'decimal', 'any'):
            dec = lambda c, k: c + ' R-N>D' if k == 'number' else (c + ' R-ANY>DEC' if k == 'any' else c)   # an item holding a decimal too (774)
            a, b = dec(a, ak), dec(b, bk)
            if getattr(self, 'stack', None): self.depth -= 1
            f = {'+': 'R-ADD', '-': 'R-MINUS', '*': 'R-DMUL', '/': 'R-DDIV', '%': 'R-MODC', '==': '=', '!=': '<>',   # checked (794)
                 '<': '<', '>': '>', '<=': '> 0=', '>=': '< 0='}[op]
            return '%s %s %s' % (a, b, f), ('decimal' if op in '+-*/%' else 'bool')
        if 'any' in (ak, bk) and ak in ('number', 'any') and bk in ('number', 'any'):   # an item: a decimal in it counts (790)
            if op in ('+', '-', '*', '/', '%'):
                if getattr(self, 'stack', None): self.depth -= 1
                return '%s %s %d %s' % (a, b, '+-*/%'.index(op),
                                        'R-ARITH-AA' if ak == bk else 'R-ARITH-AN' if ak == 'any' else 'R-ARITH-NA'), 'any'
            if ak != bk:
                if getattr(self, 'stack', None): self.depth -= 1
                return '%s %s %s %s' % (a, b, 'R-CMP-AN' if ak == 'any' else 'R-CMP-NA',
                                        {'==': '=', '!=': '<>', '<': '<', '>': '>', '<=': '> 0=', '>=': '< 0='}[op]), 'bool'
        a, b = self.to_num(a, ak, line), self.to_num(b, bk, line)
        ak = bk = 'number'
        if getattr(self, 'stack', None): self.depth -= 1
        kind = 'number' if op in '+-*/%' else 'bool'
        short = {('+', '1'): '1+', ('-', '1'): '1-', ('>', '0'): '0>', ('<', '0'): '0<', ('==', '0'): '0=', ('!=', '0'): '0<>'}
        if GENES['short'] and (op, b) in short: return '%s %s' % (a, short[(op, b)]), kind      # one word (gene short, 749)
        forth = {'+': 'R-ADD', '-': 'R-MINUS', '*': 'R-MUL', '/': 'R-DIV', '%': 'R-MODC', '==': '=', '!=': '<>', '<': '<', '>': '>', '<=': '> 0=', '>=': '< 0='}[op]   # checked (794)
        return '%s %s %s' % (a, b, forth), kind
    def unary(self):
        tok = self.peek()
        if tok[1] == 'not': self.i += 1; c, k = self.unary(); return self.truth(c, k) + ' 0=', 'bool'
        if tok[1] == '-' and tok[0] == 'word':                         # a number's, a decimal's, an item's own kind (796)
            self.i += 1; c, k = self.unary()
            if k == 'decimal': return c + ' NEGATE', 'decimal'
            if k == 'any': return c + ' R-ANY-NEG', 'any'
            return self.to_num(c, k, tok[2]) + ' NEGATE', 'number'
        return self.term()
    def term(self):
        code, kind = self.term0()
        while True:                                   # $x[i] and $x.f, touching what they follow
            nxt, prev = self.peek(), self.t[self.i - 1]
            if nxt[1] == '[' and nxt[3] == prev[4]:
                self.i += 1; ic, ik = self.expr(); self.take('op', ']')
                if kind == 'list': code, kind = '%s %s R-AT' % (code, self.to_num(ic, ik, nxt[2])), 'any'
                elif kind == 'record': code, kind = '%s %s R-GET' % (self.to_text(ic, ik), code), 'any'
                elif kind == 'any' and ik == 'number': code, kind = '%s %s R-ITEM-ANY' % (code, ic), 'any'      # a list's item, checked (801)
                elif kind == 'any' and ik == 'text': code, kind = '%s %s R-FIELD-ANY' % (ic, code), 'any'       # a record's field, no key boxed (801)
                elif kind == 'any': code, kind = '%s %s R-INDEX-ANY' % (self.box(ic, ik), code), 'any'      # either, as it holds (800)
                else: raise Error('line %d: only a list or a record is indexed' % nxt[2])
            elif nxt[0] == 'word' and nxt[1].startswith('.') and nxt[3] == prev[4] and kind in ('record', 'any'):   # one way: $r[f] (801)
                raise Error('line %d: a field is read as $r[f], not $r.f' % nxt[2])
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
            tok = self.peek()
            if tok[0] == 'word' and re.fullmatch(r'@[A-Za-z_][A-Za-z0-9_]*', tok[1]):    # [@refs, more]: a spread (744)
                self.i += 1
                code.append('%s OVER SWAP R-EXTEND' % self.spread_code(tok[1][1:], tok[2]))
            else:
                c, kd = self.expr()                                     # an item: an expression (796)
                code.append('%s OVER R-PUSH' % self.box(c, kd))
            if self.peek()[1] == ',':                                   # commas between, one way (802)
                self.i += 1
                if self.peek()[1] == ']': raise Error('line %d: no comma after the last item' % self.peek()[2])
            elif self.peek()[1] != ']': raise Error('line %d: items are separated by commas: [a, b]' % self.peek()[2])
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
        if self.peek()[1] == 'if': self.i += 1; cond, ck = self.expr(); cond = self.truth(cond, ck)   # as an if's (782)
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
            if self.peek()[1] == ',':                                   # commas between, one way (802)
                self.i += 1; self.skip_nl()
                if self.peek()[1] == '}': raise Error('line %d: no comma after the last field' % self.peek()[2])
            else:
                self.skip_nl()
                if self.peek()[1] != '}': raise Error('line %d: fields are separated by commas: {a: 1, b: 2}' % self.peek()[2])
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
            if n > 2 ** 63 - 1: raise Error('line %d: %s is too big for a decimal (at most 9223372036854.775807)' % (line, v))   # 794
            return str(-n if v.startswith('-') else n), 'decimal'
        if k == 'word' and re.fullmatch(r'-?\d+', v):
            if abs(int(v)) > 2 ** 63 - 1: raise Error('line %d: %s is too big for a number (64 bits)' % (line, v))   # 794
            if getattr(self, 'stack', None): self.depth += 1
            return v, 'number'
        if k == 'var' and getattr(self, 'stack', None) and v[1:] in self.stack:
            at = self.depth + len(self.stack) - 1 - self.stack.index(v[1:])
            self.depth += 1
            return {0: 'DUP', 1: 'OVER'}.get(at, '%d PICK' % at), 'number'
        if k == 'var' and v[1:] == getattr(self, 'loopvar', None): return 'I', 'number'      # gene loopvar (753)
        if k == 'var': return self.read_var(v[1:], line)
        if v == '$(':
            c = self.capture(); self.take('op', ')')
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
        if name == 'code':                                             # code((cmd args)): its status, a number (786)
            if self.peek()[1] == '(': self.i += 1
            if self.t[self.i - 1][1] != '(' or self.t[self.i - 2][1] != '(' or not (self.peek()[1] in ('true', 'false') or self.run_ahead()):
                raise Error('line %d: code() takes a command in ( ): code((cmd args))' % line)
            c = self.command(); self.take('op', ')'); self.take('op', ')'); return c, 'number'
        while self.peek()[1] != ')':
            args.append(self.expr())
            if self.peek()[1] == ',': self.i += 1
        self.take('op', ')')
        lib = self.library(name, args, line)
        if lib: return lib
        if name not in self.funcs:                       # named, and whether it is further down (786)
            later = any(self.t[j][0] == 'kw' and self.t[j][1] == 'def' and self.t[j + 1][1] == name for j in range(len(self.t) - 1))
            raise Error('line %d: %s() is %s' % (line, name, 'defined further down: a def comes before its use' if later else 'not defined'))
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
        cont = lambda x: x[0] + ' R-UNBOX DROP' if x[1] == 'any' else x[0]        # an item holding a list or record (758)
        a = args
        def need(n, *kinds):
            if len(a) != n: raise Error('line %d: %s() takes %d arguments' % (line, name, n))
        if name == 'len':
            need(1); c, k = a[0]
            if k == 'any': return '%s R-ANY-LEN' % c, 'number'            # a record's fields counted (799)
            if k == 'record': return '%s R-KEYS @' % c, 'number'
            return '%s @' % c, 'number'                            # a text's or a list's count
        if name in ('words', 'lines'): need(1); return '%s %s' % (self.to_text(*a[0]), {'words': 'R-SPLIT-WS', 'lines': 'R-LINES'}[name]), 'list'
        if name == 'abs':                                               # a number's or a decimal's (a path's: realpath, 799)
            need(1)
            if a[0][1] in ('number', 'decimal'): return '%s ABS' % a[0][0], a[0][1]
            if a[0][1] == 'any': return '%s R-ANY-ABS' % a[0][0], 'any'
            raise Error('line %d: abs needs a number' % line)
        if name == 'join': need(2); return '%s %s R-JOIN' % (cont(a[0]), self.to_text(*a[1])), 'text'   # an item unboxed (779)
        if name == 'range':                                            # Python's: up to, not with, its end (770)
            if len(a) not in (1, 2, 3): raise Error('line %d: range() takes 1 to 3 arguments' % line)
            n = [self.to_num(c, k, line) for c, k in a]
            if len(a) == 1: return '0 %s R-RANGE' % n[0], 'list'
            if len(a) == 2: return '%s %s R-RANGE' % tuple(n), 'list'
            return '%s %s %s R-RANGE-STEP' % tuple(n), 'list'
        if name == 'number': need(1); return '%s R-NUMBER' % self.to_text(*a[0]), 'number'
        if name == 'glob': need(1); return '%s R-GLOB' % self.to_text(*a[0]), 'list'          # the paths it matches, sorted (786)
        if name == 'setenv': need(2); return '%s %s R-SETENV' % (self.to_text(*a[0]), self.to_text(*a[1])), None   # 783
        if name == 'push': need(2); return '%s %s R-PUSH' % (self.box(*a[1]), cont(a[0])), None
        if name == 'sort': need(1); return '%s R-SORT' % cont(a[0]), 'list'
        if name == 'split': need(2); return '%s %s R-SPLIT' % (self.to_text(*a[0]), self.to_text(*a[1])), 'list'
        if name == 'slice':                                            # a list's; a text's and a record's (754)
            word, kd = {'text': ('R-TSLICE', 'text'), 'record': ('R-RSLICE', 'record')}.get(a[0][1], ('R-SLICE', 'list'))
            if len(a) == 2:
                rest = {'R-SLICE': 'OVER R-LEN', 'R-TSLICE': 'OVER @', 'R-RSLICE': 'OVER R-KEYS R-LEN'}[word]
                return '%s %s %s %s' % (cont(a[0]), self.to_num(*a[1], line), rest, word), kd
            need(3); return '%s %s %s %s' % (cont(a[0]), self.to_num(*a[1], line), self.to_num(*a[2], line), word), kd
        if name == 'keys': need(1); return '%s R-KEYS' % (a[0][0] + ' R-UNBOX DROP' if a[0][1] == 'any' else a[0][0]), 'list'
        if name in ('read', 'trim'):                                        # 754: texts and files
            need(1); return '%s %s' % (self.to_text(*a[0]), {'read': 'R-READ', 'trim': 'R-TRIM'}[name]), 'text'
        if name == 'write': need(2); return '%s %s R-WRITE' % (self.to_text(*a[0]), self.to_text(*a[1])), None
        if name in ('starts', 'ends'):
            need(2); return '%s %s %s' % (self.to_text(*a[0]), self.to_text(*a[1]), 'R-STARTS' if name == 'starts' else 'R-ENDS'), 'bool'
        if name == 'sum': need(1); return '%s R-SUM' % cont(a[0]), 'any'   # a decimal among them, a decimal (794)
        if name in ('max', 'min'):                                     # max(list), min(list): an item (760; of two values no more, 799)
            need(1)
            return '%s %s' % (a[0][0] + ' R-UNBOX DROP' if a[0][1] == 'any' else a[0][0], 'R-LMAX' if name == 'max' else 'R-LMIN'), 'any'
        if name == 'decimal': need(1); return '%s R-TEXT>DEC' % self.to_text(*a[0]), 'decimal'
        if name == 'replace': need(3); return '%s %s %s R-REPLACE' % tuple(self.to_text(*x) for x in a), 'text'
        if name == 'at':                                                # a record's field; a list's item (782); or the default
            need(3)
            if a[0][1] == 'list': return '%s %s %s R-AT-OR-L' % (a[0][0], self.to_num(*a[1], line), self.box(*a[2])), 'any'
            if a[0][1] == 'any': return '%s %s %s R-AT-OR-ANY' % (a[0][0], self.box(*a[1]), self.box(*a[2])), 'any'
            return '%s %s %s R-AT-OR' % (a[0][0], self.to_text(*a[1]), self.box(*a[2])), 'any'
        if name == 'sort-by':                                          # a list's records by a field (798; a record's entries no more, 799)
            if len(a) == 2: a = a + [(self.lit_text('asc'), 'text')]
            need(3)
            if a[0][1] == 'record': raise Error('line %d: sort-by sorts a list of records' % line)
            return '%s %s %s R-SORT-BY-L' % (cont(a[0]), self.to_text(*a[1]), self.to_text(*a[2])), 'list'
        if name == 'pop':                                               # pop(x, key): a list's item (negative from the end) or a record's field, out (799)
            need(2)
            if a[0][1] == 'list': return '%s %s R-POP-L' % (a[0][0], self.to_num(*a[1], line)), 'any'
            if a[0][1] == 'any': return '%s %s R-POP-ANY' % (a[0][0], self.box(*a[1])), 'any'
            if a[0][1] == 'record': return '%s %s R-POP-R' % (a[0][0], self.to_text(*a[1])), 'any'
            raise Error('line %d: pop needs a list or a record' % line)
        if name == 'find':                                                                            # 798
            need(2)
            if a[0][1] == 'list': return '%s %s R-FIND-L' % (a[0][0], self.box(*a[1])), 'number'
            if a[0][1] == 'any': return '%s %s R-FIND-ANY' % (a[0][0], self.box(*a[1])), 'number'
            return '%s %s R-FIND-T' % (self.to_text(*a[0]), self.to_text(*a[1])), 'number'
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
    def sub_tokens(self, text, first):    # a string's {...} or $(...), its tokens on the script's lines (786)
        return [(k, v, ln + first - 1, s, e) for (k, v, ln, s, e) in tokenize(text)]
    def string(self, body, line, typed=False):
        parts, pieces, i, lit = [], [], 0, ''   # pieces: ('lit', text) or ('code', code) - for echolit (753)
        while i < len(body):
            c = body[i]
            if c == '\\' and i + 1 < len(body):                    # \n \t \r \uXXXX; \ before a mark, the mark (793)
                e = body[i + 1]
                if e == 'u' and re.fullmatch(r'[0-9a-fA-F]{4}', body[i + 2:i + 6]): lit += chr(int(body[i + 2:i + 6], 16)); i += 6; continue
                if e.isalnum() and e not in 'ntr': raise Error('line %d: \\%s is no escape - \\n \\t \\r \\uXXXX, or \\ before a mark' % (line, e))
                lit += {'n': '\n', 't': '\t', 'r': '\r'}.get(e, e); i += 2; continue
            if body.startswith('$(', i):
                if lit: parts.append(self.lit_text(lit) if not typed else ''); pieces.append(('lit', lit)); lit = ''
                j = scan_nested(body, i + 2, ')')                       # strings in it skipped whole (789)
                if j is None: raise Error('line %d: a $( in a string is not closed' % line)
                sub = Compiler.__new__(Compiler); sub.__dict__ = dict(self.__dict__)
                sub.t = self.sub_tokens(body[i + 2:j - 1], line + body[:i + 2].count('\n')); sub.i = 0
                parts.append(sub.capture() + ' R-CHECK'); pieces.append(('code', parts[-1])); i = j; continue
            m = re.match(r'\$([A-Za-z_][A-Za-z0-9_]*)', body[i:])
            if m or c == '{':
                if lit: parts.append(self.lit_text(lit) if not typed else ''); pieces.append(('lit', lit)); lit = ''
                if m:
                    name = m.group(1); i += m.end()
                    code, kind = ('I', 'number') if name == getattr(self, 'loopvar', None) else self.read_var(name, line)
                    if kind == 'record' and re.match(r'\.[A-Za-z_]', body[i:]):     # "$r.f" gone: one way, {$r[f]} (801)
                        raise Error('line %d: a field in a string is written {$r[f]}' % line)
                    parts.append(self.to_text(code, kind)); pieces.append(('code', parts[-1]))
                else:
                    j = scan_nested(body, i + 1, '}')                       # strings in it skipped whole (789)
                    if j is None: raise Error('line %d: a { in a string is not closed' % line)
                    sub = Compiler.__new__(Compiler); sub.__dict__ = dict(self.__dict__)
                    sub.t = self.sub_tokens(body[i + 1:j - 1], line + body[:i + 1].count('\n')); sub.i = 0
                    c2, k2 = sub.expr(); parts.append(self.to_text(c2, k2)); pieces.append(('code', parts[-1])); i = j
                continue
            lit += c; i += 1
        if typed: return pieces + [('lit', lit)]
        if lit or not parts: parts.append(self.lit_text(lit))
        return parts[0] if len(parts) == 1 else '%s %d R-CONCAT' % (' '.join(parts), len(parts))
    def lit_text(self, s):
        if '"' in s or '\n' in s or '\t' in s or '\r' in s: return self.shared(self.bytes_lit(s))
        return self.shared('S" %s" R-TEXT' % s)
    KCODE = {'number': 'K-NUM', 'text': 'K-TEXT', 'bool': 'K-BOOL', 'list': 'K-LIST', 'record': 'K-REC', 'decimal': 'K-DEC'}
    def to_text(self, code, kind):
        if kind == 'text': return code
        if kind == 'any': return code + ' R-ANY>TEXT'
        if kind == 'list': return code + ' S"  " R-TEXT R-JOIN'          # a list as text: its items, a blank between
        if kind == 'decimal': return code + ' R-DEC>TEXT'                 # 754
        if kind == 'bool': return code + ' R-BOOL>TEXT'                   # 759: true or false
        if kind == 'record': return code + ' R-SHOW-REC'                  # 793: {k: v, ...}, not its address
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
    RKC = {'text': 'K-TEXT', 'list': 'K-LIST', 'record': 'K-REC', 'any': 'K-ANY'}
    def statement(self):                 # gene gc (776): a safe point before each statement of the top level
        v = self.peek()[1]; line = self.peek()[2]
        gc = (GENES['gc'] and self.locals is None and not getattr(self, 'stack', None)
              and not getattr(self, 'in_exit', False) and v not in ('def', 'on'))
        out = self.statement_inner()
        if GENES['lines'] and v != 'def': out = ('[ %d R-MARK ] %s' % (line, out)).strip()   # gene lines (781)
        sp = 'R-GC?S' if self.has_on_exit else 'R-GC?'           # a script with on EXIT polls for INT and TERM too (786)
        return sp + ' ' + out if gc and out else (sp if gc else out)
    def root_kind(self, n):              # what a variable registers as, for the collector: None if nothing
        if n in getattr(self, 'roots', {}): return self.roots[n]
        k = self.vars.get(n)
        return k if k in self.RKC else None
    def statement_inner(self):
        k, v, line = self.peek()[:3]
        start = self.i
        if v == 'if': out = self.if_()
        elif k == 'word' and v == 'cd' and self.peek(1)[1] not in ('=', '(', '['):     # cd DIR, cd DIR { ... } (760)
            self.i += 1; r = self.arg_item(); c = self.to_text(*r) if isinstance(r, tuple) else r
            out = 'R-CWD-PUSH %s R-CD %s R-CWD-POP' % (c, self.block()) if self.peek()[1] == '{' else '%s R-CD' % c
        elif v == 'while':
            self.i += 1; c = self.cond()
            body = self.loop_body('begin', whileloop=True)
            if isinstance(body, tuple):                                       # its body a word: break, continue (779)
                call, ret = body
                stop = 'R-BRK @ R-RET @ OR' if ret else 'R-BRK @'
                out = 'BEGIN %s 0= IF %s ELSE 0 THEN WHILE %s REPEAT 0 R-BRK !' % (stop, c, call)
                if ret: out += self.after_body()
            else: out = 'BEGIN %s WHILE %s REPEAT' % (c, body)
        elif v == 'return':
            self.i += 1; c, kd = self.expr()
            want = self.funcs[self.current][1] if getattr(self, 'current', None) else None
            c = self.convert(c, kd, want, line)                   # to the def's -> kind (749: a boxed parameter returned)
            if getattr(self, 'stack', None):
                c += ' NIP' * len(self.stack); self.depth -= 1        # the result, the parameters dropped under it
            c += self.unwind(True)                                    # out of the loops it is in (779)
            out = '%s R-RETV ! -1 R-RET ! EXIT' % c if self.in_body() else '%s EXIT' % c
        elif v == 'def': out = self.def_(); return ''
        elif v == 'for': out = self.for_()
        elif v == 'break':
            self.i += 1; out = '-1 R-BRK ! EXIT' if getattr(self, 'hoists', None) and self.hoists[-1] else 'LEAVE'
        elif k == 'word' and v == 'continue':
            if not (getattr(self, 'hoists', None) and self.hoists[-1]): raise Error('line %d: continue outside a for loop' % line)
            self.i += 1; out = 'EXIT'
        elif k == 'word' and v == 'case' and self.peek(1)[1] not in ('(', '=', '+=', '-=', '['):
            out = self.case_()                                                          # 783
        elif k == 'word' and v == 'exit' and self.peek(1)[1] != '(':
            self.i += 1
            if self.peek()[0] in ('nl', 'eof') or self.peek()[1] in (';', '}'): out = '0 R-EXIT'
            else: c, kd = self.expr(); out = '%s R-EXIT' % self.to_num(c, kd, line)
        elif k == 'word' and v == 'on' and self.peek(1)[1] == 'EXIT':
            self.i += 2; self.on_n = getattr(self, 'on_n', 0) + 1
            self.in_exit = True; body = self.block(); self.in_exit = False          # no safe point in it (776)
            self.defs.append(': R-EXIT-%d %s ;' % (self.on_n, body))
            out = "['] R-EXIT-%d R-ON-EXIT" % self.on_n
        elif k == 'word' and self.peek(1)[1] == '[' and self.peek(1)[3] == self.peek()[4]:
            name = v; self.i += 2
            ic, ik = self.expr(); self.take('op', ']')
            chain = []                                            # a[i][j] = v: the indexes before the last (779)
            while self.peek()[1] == '[' and self.peek()[3] == self.t[self.i - 1][4]:
                self.i += 1; chain.append((ic, ik)); ic, ik = self.expr(); self.take('op', ']')
            op = self.take()[1]
            if op in ('+=', '-='): raise Error('line %d: += and -= are gone: write x[i] = $x[i] + v' % line)   # one way (800)
            if op != '=': raise Error('line %d: expected =, found %s' % (line, op))
            c, kd = self.expr(); ck = self.kind_of(name, line)
            if chain:                                             # the container read down the chain, an item
                jc, jk = chain[0]
                if ck == 'list': cc = 'R.%s @ %s R-AT' % (name, self.to_num(jc, jk, line))
                elif ck == 'record': cc = '%s R.%s @ R-GET' % (self.to_text(jc, jk), name)
                elif ck == 'any': cc = '%s R.%s @ R-INDEX-ANY' % (self.box(jc, jk), name)
                else: raise Error('line %d: $%s is not a list or a record' % (line, name))
                for jc, jk in chain[1:]: cc = '%s %s R-INDEX-ANY' % (self.box(jc, jk), cc)
                out = '%s %s %s R-ASSIGN-ANY' % (self.box(c, kd), self.box(ic, ik), cc)
            if chain: pass
            elif ck == 'list': out = '%s R.%s @ %s R-SET' % (self.box(c, kd), name, self.to_num(ic, ik, line))
            elif ck == 'record': out = '%s %s R.%s @ R-PUT' % (self.box(c, kd), self.to_text(ic, ik), name)
            elif ck == 'any': out = '%s %s R.%s @ R-ASSIGN-ANY' % (self.box(c, kd), self.box(ic, ik), name)   # 758
            else: raise Error('line %d: $%s is not a list or a record' % (line, name))
        elif k == 'word' and self.peek(1)[1] in ('=', '+=', '-='):
            name = v; self.i += 1; op = self.take()[1]
            if op != '=': raise Error('line %d: += and -= are gone: write x = $x + v' % line)   # one way (800)
            c, kd = self.expr()
            sc = self.scope()
            if self.infer is not None: pass                                # the first pass: every binding as it comes (764)
            elif name in sc and sc[name] in ('text', 'number') and kd == 'any':
                c, kd = (self.to_text(c, kd), 'text') if sc[name] == 'text' else (self.to_num(c, kd, line), 'number')   # 758
            elif name in sc and sc[name] == 'decimal' and kd == 'number':
                c, kd = c + ' R-N>D', 'decimal'                  # a number into a decimal variable (771)
            elif name in sc and sc[name] == 'any' and kd != 'any':
                c, kd = self.box(c, kd), 'any'                      # an item takes any value, boxed (754)
            elif name in sc and sc[name] != kd:
                raise Error('line %d: $%s is %s; it cannot become %s' % (line, name, sc[name], kd))
            if self.infer is not None: self.bind(name, kd)
            else: sc[name] = kd; self.names.add(name)
            if op == '=': self.da_mark(name)                                 # certainly set from here (772)
            out = '%s R.%s !' % (c, name)
        elif k == 'word' and v == 'echo' and self.echo_err() is not None:   # echo ... out>err: one line to the err port, in-process (799)
            end = self.echo_err()
            sub = Compiler.__new__(Compiler); sub.__dict__ = dict(self.__dict__)
            sub.t = self.t[self.i + 1:end] + [('eof', '', line, 0, 0)]; sub.i = 0
            parts, _ = sub.args((';', '}')); self.i = end + 3
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
    def scan_stmt(self):
        """The statement from here, brackets skipped (799): its end, and its
        first redirection or pipe outside brackets (None if none)."""
        j, depth, first = self.i, 0, None
        while True:
            k, v = self.t[j][0], self.t[j][1]
            if k in ('nl', 'eof') or (depth == 0 and v in (';', '}', '??')): return j, first
            if depth == 0 and first is None and v in ('>', '>>', '<', '|'): first = j
            if k == 'op' and v in ('(', '[', '{'): depth += 1
            elif k == 'op' and v in (')', ']', '}'): depth -= 1
            j += 1
    def echo_err(self):
        """Is the first redirection or pipe of the echo from here its closing
        out>err? Then the index of that out."""
        j, first = self.scan_stmt()
        if first is None or first != j - 2 or j - 3 <= self.i: return None
        o, g, e = self.t[j - 3], self.t[j - 2], self.t[j - 1]
        if (o[1], g[1], e[1]) != ('out', '>', 'err') or g[3] != o[4] or e[3] != g[4]: return None
        return j - 3
    def plumbed(self):
        """Does the statement from here redirect or pipe? Then echo runs as a
        program, with its ports where the statement puts them."""
        return self.scan_stmt()[1] is not None
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
            if stop and tok[1] in ('>', '>>') and '|' in stop:             # output to a named port, one way (802)
                raise Error('line %d: output goes to a port: out> file, out>> file' % tok[2])
            if stop and tok[1] == '<' and '|' in stop:
                redirs.append(self.redirect('in')); continue
            if spread and tok[0] == 'word' and re.fullmatch(r'@[A-Za-z_][A-Za-z0-9_]*', tok[1]):
                self.i += 1; name = tok[1][1:]
                parts.append('%s OVER SWAP R-EXTEND' % self.spread_code(name, tok[2])); kinds_spread = True
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
            if parts: raise Error('line %d: %s is a def: call it as %s(...) - as a command it takes no arguments' % (tok[2], tok[1], tok[1]))   # 779
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
    def capture(self):                    # $( cmd [?? cmd] ... ): its output, then its status - ?? runs the next if one fails (787)
        c = self.command(capture=True)
        while self.peek()[1] == '??':
            self.i += 1; c = '%s DUP IF DROP %s >R R-CAP-JOIN R> THEN' % (c, self.command(capture=True))
        return c
    def run_ahead(self):
        """After a (: a run, unless its second token makes it an expression."""
        second = self.peek(1)
        if self.peek()[1] in ('true', 'false') and second[1] == ')': return False   # (true): the literal, not the program (786)
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
            elif (k == 'kw' and v in ('for', 'def', 'break')) or (k == 'word' and v in ('continue', 'EXIT')):   # break a keyword (770)
                return False
            elif k == 'word' and v == name and self.t[j + 1][1] in ('=', '+=', '-=', '['): return False
            j += 1
    # loops and their way out (779): each word compiled keeps the loops it is inside (self.loops) - a DO
    # loop's frame on the return stack, a counted loop's two cells on the data stack; a return leaves them.
    # In a loop body made a word of its own (break or continue in it), a return sets R-RET and leaves the
    # word; each loop around passes it on, and the def it is in returns R-RETV.
    def unwind(self, value):
        out = ''
        for k in reversed(getattr(self, 'loops', [])):
            if k == 'do2': out += ' NIP NIP UNLOOP' if value else ' 2DROP UNLOOP'
            elif k == 'do': out += ' UNLOOP'
        return out
    def in_body(self): return bool(getattr(self, 'hoists', None)) and True in self.hoists
    def has_return(self):
        """Does the block ahead (its { the current token) hold a return, at any depth?"""
        j, depth = self.i, 0
        while True:
            k, v = self.t[j][0], self.t[j][1]
            if v == '{': depth += 1
            elif v == '}':
                depth -= 1
                if depth == 0: return False
            elif k == 'kw' and v == 'return': return True
            j += 1
    def after_body(self):                 # after a loop whose body word may return: pass it on, or return it
        if self.in_body(): return ' R-RET @ IF%s EXIT THEN' % self.unwind(False)
        return ' R-RET @ IF 0 R-RET !%s R-RETV @ EXIT THEN' % self.unwind(False)
    def has_continue(self, breaks=False):
        """Does the block ahead hold a continue at its own level (not in a loop inside it) - or a break, asked?"""
        j, stack, pending = self.i, [], False
        while True:
            k, v = self.t[j][0], self.t[j][1]
            if v == '{': stack.append('loop' if pending else 'block'); pending = False
            elif v == '}':
                stack.pop()
                if not stack: return False
            elif v in ('for', 'while') and k == 'kw': pending = True
            elif k == 'word' and v == 'continue' and 'loop' not in stack[1:]: return True
            elif breaks and k == 'kw' and v == 'break' and 'loop' not in stack[1:]: return True   # a while's break (779)
            j += 1
    def loop_body(self, kind='do', whileloop=False):
        hoists = getattr(self, 'hoists', [])
        loops = getattr(self, 'loops', [])
        if not (self.has_continue(breaks=whileloop)):
            hoists.append(False); self.hoists = hoists; loops.append(kind); self.loops = loops
            code = self.block(); hoists.pop(); loops.pop(); return code
        self.body_n = getattr(self, 'body_n', 0) + 1; n = self.body_n
        ret = self.has_return()
        hoists.append(True); self.hoists = hoists; self.loops = []        # a word of its own: no loops around in it
        code = self.block(); hoists.pop(); self.loops = loops
        self.defs.append(': R-BODY-%d %s ;' % (n, code))
        if whileloop: return 'R-BODY-%d' % n, ret
        if ret: return 'R-BODY-%d R-BRK @ R-RET @ OR IF 0 R-BRK ! LEAVE THEN' % n, ret
        return 'R-BODY-%d R-BRK @ IF 0 R-BRK ! LEAVE THEN' % n, ret
    def for_body(self, kind):             # a for loop's body, and what follows the loop if its body word may return (779)
        b = self.loop_body(kind)
        if isinstance(b, tuple): return b[0], (self.after_body() if b[1] else '')
        return b, ''
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
    def for_(self):
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
            if GENES['loopvar'] and self.loopvar_ok(a):        # gene loopvar (753)
                outer = getattr(self, 'loopvar', None); self.loopvar = a
                body, after = self.for_body('do2'); self.loopvar = outer
                return '%s %s TUCK MAX SWAP 2DUP ?DO %s LOOP OVER < IF 1-%s R.%s ! ELSE DROP THEN%s' % (
                    self.to_num(hi, hk, line), self.to_num(lo, lk, line), body, box, a, after)     # the last value kept, as Python
            body, after = self.for_body('do')
            out = '%s %s TUCK MAX SWAP ?DO I%s R.%s ! %s LOOP%s' % (self.to_num(hi, hk, line), self.to_num(lo, lk, line), box, a,
                                                                 body, after)
            return out
        sc, sk = self.expr()
        tmp = '%s.src%d' % (a, self.i); self.names.update([a, tmp])
        if self.locals is None: self.__dict__.setdefault('roots', {})[tmp] = 'record' if sk == 'record' else 'list'   # 776
        if sk == 'record':                                               # for k, v in a record
            key, val = (a, b) if b else (a, None)
            kk = self.bind(key, 'text'); self.da_next = [key] + ([val] if val else [])
            if val: self.bind(val, 'any')
            setv = ('R.%s @ R-VALS I R-AT R.%s ! ' % (tmp, val)) if val else ''
            body, after = self.for_body('do')
            out = ('%s R.%s ! R.%s @ R-KEYS R-LEN 0 ?DO R.%s @ R-KEYS I R-AT%s R.%s ! %s%s LOOP%s'
                   % (sc, tmp, tmp, tmp, ' R-ANY>TEXT' if kk == 'text' else '', key, setv, body, after))
            return out
        if sk not in ('list', 'any'): raise Error('line %d: for needs a list or a record' % line)
        if sk == 'any': sc += ' R-UNBOX DROP'
        idx, item = (a, b) if b else (None, a)
        self.da_next = [item] + ([idx] if idx else [])
        self.bind(item, 'any')
        seti = ''
        if idx: seti = 'I%s R.%s ! ' % (self.num_into(self.bind(idx, 'number')), idx)
        body, after = self.for_body('do')
        out = ('%s R.%s ! R.%s @ R-LEN 0 ?DO %sR.%s @ I R-AT R.%s ! %s LOOP%s'
               % (sc, tmp, tmp, seti, tmp, item, body, after))
        return out
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
    def skip_block(self):                 # past the block ahead, its { the current token
        depth = 0
        while True:
            v = self.peek()[1]; self.i += 1
            if v == '{': depth += 1
            elif v == '}':
                depth -= 1
                if depth == 0: return
    def def_(self):
        start = self.i
        self.take('kw', 'def'); name = self.take('word')[1]; params = []
        if self.locals is not None: raise Error('line %d: a def inside a def - define %s at the top level' % (self.t[start][2], name))   # 793
        if self.peek()[1] != '(' or self.peek()[3] != self.t[self.i - 1][4]:   # def f(a, b): as it is called, one way (802)
            raise Error("line %d: a def's parameters go in parentheses: def f(a, b)" % self.t[start][2])
        self.i += 1
        while self.peek()[1] != ')':
            params.append(self.take('word')[1])
            if self.peek()[1] == ',':
                self.i += 1
                if self.peek()[1] == ')': raise Error('line %d: no comma after the last parameter' % self.peek()[2])
            elif self.peek()[1] != ')': raise Error('line %d: parameters are separated by commas: def f(a, b)' % self.peek()[2])
        self.i += 1
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
        if self.infer is not None and not getattr(self, 'pd_now', False):   # the first pass: the body once the script's top
            self.__dict__.setdefault('postponed', []).append(start)          # level is through - every global it sets known (785)
            self.skip_block(); self.current = None; return
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
        if self.infer is not None:                                    # the defs' bodies, the first pass's last (785)
            self.pd_now = True
            for s in getattr(self, 'postponed', []): self.i = s; self.statement()
            self.pd_now = False
        return ('\n'.join('VARIABLE R.%s' % n for n in sorted(self.names)) + '\n' +
                (''.join('R.%s %s R-ROOT\n' % (n, self.RKC[self.root_kind(n)]) for n in sorted(self.names) if self.root_kind(n))
                 if GENES['gc'] else '') +
                ''.join('R-NONE R.%s !\n' % n for n in sorted(self.names) if n in self.none_init) +
                ''.join('%s R-FIX CONSTANT R-LIT-%d\n' % (c, n) for c, n in self.lits.items()) +
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
