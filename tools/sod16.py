#!/usr/bin/env python3
"""
tools/sod16.py - translate RelF's compiled word bodies to a uniform
16-bit token stream, and PROVE the translation is lossless by decoding
it back and comparing.

Iteration 162, on branch token16.

WHY THE ROUND TRIP IS THE POINT

This session found two silent decoder bugs in analysis tools of exactly
this kind, and each invalidated numbers that had already been reported
with confidence:

  - call targets resolved as addr+value instead of addr+CELL+value,
    which matched 24 of 6,548 calls;
  - an inline counted string's length read as a CELL when `(S")` uses
    `COUNT`, so it is a BYTE - every word containing a string was
    silently truncated and the operation count was low by 21.5%.

Both produced plausible output. Neither was caught by inspection. An
engine built on an unvalidated translator would inherit the same class
of fault, and the symptom would be a corrupt image rather than a wrong
number. So this tool decodes its own output and asserts equality
against the input, per word, and reports how many words survive.

THE ENCODING

One 16-bit token per operation:

    0..255       primitive, index = token
    256..65535   call word number (token - 256)

Operands follow their token, as further 16-bit units:

    LIT      1 operand if 0 <= v <= 0xFFFF, else 2 (low, high)
    BRANCH   1 signed operand, offset in TOKEN units
    ?BRANCH  same
    (S")     inline counted string, byte-packed, padded to a token

Word numbers index a table rebuilt at load by walking the dictionary
link chain, so nothing about the table goes in the image.

SCOPE, STATED PLAINLY

This translates a FULLY BUILT image. It does not make the Forth
compiler emit tokens - `,` and `:` still build cell code, so a
translated image can run but cannot compile new definitions. That is
enough to measure size and dispatch on real code, which is the
question, and not enough to self-host, which is a later problem.
"""
import re, sys, collections

CELL = int(sys.argv[2]) if len(sys.argv) > 2 else 4
DUMP = sys.argv[1] if len(sys.argv) > 1 else '/tmp/dump3.txt'

prims = [l.split()[1] for l in open('kernel.4') if l.startswith('PRIMITIVE')]
tokn = {i * CELL + 1: n for i, n in enumerate(prims)}
idx_of = {n: i for i, n in enumerate(prims)}
LIT, BR, QBR = (prims.index(x) * CELL + 1 for x in ('LIT', 'BRANCH', '?BRANCH'))

words, cur, cells = [], None, {}
START_ADDR = None
for l in open(DUMP, errors='replace'):
    l = l.rstrip()
    m = re.match(r'^S (\d+) (\d+)', l)
    if m and START_ADDR is None: START_ADDR = int(m.group(1)); continue
    m = re.match(r'^N (-?\d+) (-?\d+) (.*)$', l)
    if m:
        cur = {'s': int(m.group(1)), 'e': int(m.group(2)), 'n': m.group(3).strip()}
        words.append(cur); continue
    m = re.match(r'^B (-?\d+) (-?\d+)\s*$', l)
    if m: cells[int(m.group(1))] = int(m.group(2))

# Word numbers run OLDEST FIRST, which is definition order.
#
# The dump walks the dictionary link chain from the newest word
# backwards, so `words` is newest-first. Numbering in that order would
# be a design bug: defining a new word makes it number 0 and shifts
# every existing number by one, invalidating every token already
# compiled. Reversing it means a new definition takes the next unused
# number and nothing that exists moves - which is the property that
# lets an xt be a word number at all.
#
# It also matches how a real load rebuilds the table: walk the chain to
# the end, then assign numbers coming back, so entry N is the Nth word
# ever defined.
order = list(reversed(words))
num = {w['s']: i for i, w in enumerate(order)}
by_name = {w['n']: w for w in words}
# LIT32 is a synthetic opcode: a literal too wide for one 16-bit
# operand, followed by two of them. It is NOT one of kernel.4's
# primitives, so it needs its own dispatch entry in the engine, and it
# takes the first index past the real ones rather than a high number
# like 255 - sod16.c's dispatch table has exactly len(prims) entries,
# and `goto *dispatch[255]` would read past the end of it. Appending is
# also what GOALS.md's rule for adding a primitive says to do.
LIT32 = len(prims)
assert LIT32 < 256, "no room for the LIT32 opcode below the call band"
# LIT64: a literal that does not fit LIT32's SIGNED 32 bits. Before this
# existed, to_tokens() masked every literal to 32 bits, so a wider one
# was silently truncated - the same fault CV8 had until Iteration 194,
# still present here because no 16-bit image had ever compiled anything.
LIT64 = len(prims) + 3
def _fits32(v):
    return -(1 << 31) <= v < (1 << 31)

src = "".join(open(f, errors='replace').read()
              for f in ['shell.4', 'locals.4', 'pool.4', 'save-system.4'])
DATA = (set(re.findall(r'CREATE\s+(\S+)', src)) |
        set(re.findall(r'BUFFER:\s+(\S+)', src)) |
        set(re.findall(r'^\s*VARIABLE\s+(\S+)', src, re.M)) |
        set(re.findall(r'CONSTANT\s+(\S+)', src)))

# ---- what the inline-operand words expect --------------------------
#
# kernel.4 line 252 states it: "(LOOP) and (+LOOP) are followed by an
# inline loop start address. (?DO) and (LEAVE) are followed by an
# inline leave address." Three more words carry an inline counted
# string. All seven read that inline data off the return stack, in
# FORTH, with CELL-width arithmetic - which makes them the one part of
# the system that a change of code representation cannot ignore.
#
# The governing rule here, and the reason sod16.c stays eight lines
# from relf.c: ONLY THE OPCODE STREAM BECOMES TOKENS. Inline operands
# and inline strings keep cell granularity and cell alignment, so
# (LOOP)'s `DUP @ +` and `CELL+`, and (S")'s `COUNT ... ALIGNED`, all
# keep working with no kernel change at all.
#
#   (S") (.") (ABORT")  `R> COUNT ... ALIGNED >R` - the counted string
#       must start at the very next address after the call token, so
#       NO padding may precede it, and execution resumes at the next
#       CELL-aligned address after it.
#   (LOOP) (+LOOP)      `>R DUP @ +` reads a CELL at the very next
#       address after the call token, and `CELL+` skips one. So the
#       operand must be CELL-aligned, which is arranged by padding with
#       NOOP tokens BEFORE the call token - padding after it would be
#       what `@` read.
#
# (?DO) and (LEAVE) are refused, not translated. Their operand is an
# ABSOLUTE address: RESOLVE-LEAVE compiles a bare `HERE` into it. That
# is a latent fault in the cell image too - an absolute address does not
# survive the relocation a saved image performs on every load - and it
# is invisible today only because both words have ZERO call sites in
# this image. Anything that adds a ?DO or a LEAVE to shell.4 breaks
# saved images before it ever reaches SOD16.
STR_WORDS  = ('(S")', '(.")', '(ABORT")')
LOOP_WORDS = ('(LOOP)', '(+LOOP)')
# (POSTPONE) is the eighth inline-operand word - its own comment in
# kernel.4 says "has inline argument". `R> DUP DUP @ + SWAP CELL+ >R`
# reads a CELL holding a relative address to another word's body and
# skips it. Iteration 175 thought this needed a source change, on the
# grounds that an xt is a word number. Iteration 176 found that is not
# so: `: EXECUTE ( xt --- ) >R ;` is pure Forth, not a primitive, and
# works by making the xt the RETURN ADDRESS, so an xt must be an
# executable address in either engine. A CALL TOKEN is a word number; an
# XT is an address; they are different things and Iteration 165
# conflated them.
#
# So this operand carries across like the others. Its value is a
# relative address into ANOTHER word, which a per-word translator
# cannot resolve, so it is passed through here and relocated by
# tools/layout.py, which is the pass that knows where words land.
XT_WORDS   = ('(POSTPONE)',)

# locals.4's L-EMIT compiles "the offset as a literal, then a relative
# call to the runtime word, which does the + START itself". So a LIT
# followed by a call to one of those four runtime words is not a value,
# it is an offset into the image, and the layout pass has to move it.
#
# Such a literal is ALWAYS encoded in the 32-bit form, whatever its
# current value. Relocating it changes the value, and if the encoding
# could shrink or grow with the value the body would change size after
# the layout had already been computed from it.
#
# The four are found through the variables holding their xts rather
# than by name.
LOCALS_RT = set()
for _n in ('L-LSAVE-XT', 'L-L!-XT', 'L-LZERO-XT', 'L-LRESTORE-XT'):
    _w = by_name.get(_n)
    if _w:
        _v = cells.get(_w['s'] + CELL)
        if _v: LOCALS_RT.add(START_ADDR + _v)
BAD_WORDS  = ('(?DO)', '(LEAVE)')

STR  = {by_name[n]['s'] for n in STR_WORDS  if n in by_name}
LOOPS = {by_name[n]['s'] for n in LOOP_WORDS if n in by_name}
BAD  = {by_name[n]['s'] for n in BAD_WORDS  if n in by_name}
XTS  = {by_name[n]['s'] for n in XT_WORDS   if n in by_name}

def align_up(x, a): return (x + a - 1) // a * a

# ---- decode a word body to an operation list -----------------------
EXIT_TOK = idx_of['EXIT'] * CELL + 1

# The three primitives that take an operand. A stub for one of these is
# the only place in the image where a token stream is genuinely
# ambiguous - see the driver.
OPERAND_PRIMS = ('LIT', 'BRANCH', '?BRANCH')

def stub_ops(w):
    """The two ops of a PRIMITIVE stub body, or None if this is not one."""
    if w['e'] - w['s'] != 2 * CELL: return None
    v0 = cells.get(w['s'])
    if cells.get(w['s'] + CELL) != EXIT_TOK or v0 not in tokn: return None
    return [('P', tokn[v0]), ('P', 'EXIT')]

# Mid-word addresses that are entered from outside: the DOES> tails.
# Code cannot be said to end before one of these.
ENTRIES = set()
for _w in words:
    _v = cells.get(_w['s'])
    if _v is not None and not (_v & 1):
        _t = _w['s'] + CELL + _v
        if _t not in num: ENTRIES.add(_t)

def code_end(w):
    """Address where this word's CODE ends. Usually w['e'].

    A body span is everything up to the next HEADER, which is not the
    same as a word's code: shell.4 compiles unheadered table entries
    between definitions (`' DO-WAIT S" wait" BUILTIN`), and they land
    inside the previous word's span. DO-ULIMIT and DO-UNALIAS each
    carry one, and decoding ran off into a counted string.

    The rule: code ends at the first EXIT that nothing can jump past.
    If code continued beyond an EXIT, something would have to reach it,
    and the only ways in are a branch or an outside entry point - fall
    through is impossible past an EXIT. So an EXIT with no branch
    target and no DOES> entry beyond it is the end.
    """
    a, reach = w['s'], w['s']
    for e in ENTRIES:
        if w['s'] < e < w['e']: reach = max(reach, e)
    while a < w['e']:
        v = cells.get(a)
        if v is None: return w['e']
        if v & 1:
            nm = tokn.get(v)
            if nm is None: return w['e']
            if v in (BR, QBR):
                reach = max(reach, a + CELL + cells.get(a + CELL, 0))
                a += 2 * CELL
            elif v == LIT: a += 2 * CELL
            else:
                a += CELL
                # STRICTLY greater. A branch whose target is exactly
                # the address after this EXIT means code resumes there;
                # `>=` treated that as the end and truncated 106 bodies,
                # dropping 49 KB of real code while the round trip
                # stayed green, because it only ever saw the part that
                # was kept.
                if nm == 'EXIT' and a > reach: return a
        else:
            t = a + CELL + v
            a += CELL
            if t in BAD: return w['e']
            if t in LOOPS or t in XTS: a += CELL
            elif t in STR:
                n = (cells.get(a) or 0) & 0xFF
                a += align_up(1 + n, CELL)
    return w['e']

def retag(ops):
    """Mark literals that are really image offsets. Positional, like
    every other operand rule here: only the call that follows says what
    the value means."""
    for j in range(len(ops) - 1):
        if (ops[j][0] == 'LIT' and ops[j + 1][0] == 'C'
                and ops[j + 1][1] in LOCALS_RT):
            ops[j] = ('LITOFF', ops[j][1])
    return ops

def read_ops(w):
    # A PRIMITIVE stub is not threaded code. cross.4's PRIMITIVE emits
    # `"HEADER DUP , ,-T EXIT-TOKEN ,-T`, so the body is exactly
    # [prim-token, EXIT]. Read as code, LIT/BRANCH/?BRANCH swallow that
    # trailing EXIT as their operand: the word LIT translated to "push
    # 9" rather than "LIT; EXIT". Detected by shape rather than by name,
    # because locals.4 redefines EXIT and a name test picks the wrong
    # word.
    st = stub_ops(w)
    if st is not None:
        # A PRIMITIVE's body is NOT folded, even though `op EXIT` would
        # fold: the runtime compiler inlines a primitive by reading the
        # first byte of its body (cv8.4, COMPILE,8), so that byte must
        # be the plain opcode. Folding made `+` compile as `+;EXIT`,
        # which ended the caller's definition early.
        return st

    out, a, end = [], w['s'], code_end(w)
    while a < end:
        if ALIGN_TAILS and a in ENTRIES and a != w['s']:
            out.append(('ALN', ALIGN_TAILS))
        v = cells.get(a)
        if v is None: return None
        if v & 1:
            nm = tokn.get(v)
            if nm is None: return None
            if v == LIT:
                out.append(('LIT', cells.get(a + CELL, 0))); a += 2 * CELL
            elif v in (BR, QBR):
                out.append(('BR' if v == BR else 'QBR', cells.get(a + CELL, 0)))
                a += 2 * CELL
            else:
                out.append(('P', nm)); a += CELL
        else:
            t = a + CELL + v
            if t in BAD: return None          # absolute-address operand
            out.append(('C', t)); a += CELL
            if t in LOOPS:
                out.append(('OPD', cells.get(a, 0))); a += CELL
            elif t in XTS:
                out.append(('XT', cells.get(a, 0))); a += CELL
            elif t in STR:
                n = (cells.get(a) or 0) & 0xFF
                blob = align_up(1 + n, CELL)
                # Keep the STRING BYTES, not the cells that hold them.
                # The cell image pads the tail to CELL from the body
                # start and the token image pads it from a different
                # position, so the pad bytes are not comparable and are
                # not part of the string. Comparing the bytes is what
                # makes the round trip test the string rather than the
                # padding.
                raw = bytearray()
                for k in range(0, blob, CELL):
                    raw += (cells.get(a + k, 0) & ((1 << (8 * CELL)) - 1)
                            ).to_bytes(CELL, 'little')
                out.append(('STR', bytes(raw[:1 + n]))); a += blob
    out = retag(out)
    if SPEC: out = specialise(out)
    return fold_exit(out) if FOLD else out

def branch_targets(ops):
    cs, c = [], 0
    for k, pl in ops: cs.append(c); c += op_cells(k, pl)
    tg = set()
    for j, (k, pl) in enumerate(ops):
        if k in ('BR', 'QBR'): tg.add(cs[j] + CELL + pl)
        if k == 'OPD': tg.add(cs[j] + pl)
        if k == 'ALN': tg.add(cs[j])
    return cs, tg

_DOVAR = [w['s'] for w in words if w['n'] == 'DOVAR']
def is_var(t):
    v = cells.get(t)
    return bool(_DOVAR) and v is not None and not (v & 1) and t + CELL + v == _DOVAR[0]

def _expect(n):
    sh = CELL.bit_length() - 1
    E = {'0=': [('LIT', 0), ('P', '='), ('P', 'EXIT')],
         '-': [('P', 'NEGATE'), ('P', '+'), ('P', 'EXIT')],
         '<>': [('P', '='), ('C', '0='), ('P', 'EXIT')],
         '0<': [('LIT', 0), ('P', '<'), ('P', 'EXIT')],
         '>': [('P', 'SWAP'), ('P', '<'), ('P', 'EXIT')],
         '2DUP': [('P', 'OVER'), ('P', 'OVER'), ('P', 'EXIT')],
         '2DROP': [('P', 'DROP'), ('P', 'DROP'), ('P', 'EXIT')],
         'CHAR+': [('LIT', 1), ('P', '+'), ('P', 'EXIT')],
         '1+': [('LIT', 1), ('P', '+'), ('P', 'EXIT')],
         'CELL+': [('LIT', CELL), ('P', '+'), ('P', 'EXIT')],
         'CELLS': [('LIT', sh), ('P', 'LSHIFT'), ('P', 'EXIT')],
         '1-': [('LIT', -1), ('P', '+'), ('P', 'EXIT')],
         'INVERT': [('LIT', -1), ('P', 'XOR'), ('P', 'EXIT')],
         'COUNT': [('P', 'DUP'), ('LIT', 1), ('P', '+'), ('P', 'SWAP'), ('P', 'C@'), ('P', 'EXIT')],
         'ALIGNED': [('LIT', CELL), ('LIT', 1), ('C', '-'), ('P', '+'), ('LIT', CELL),
                     ('P', 'NEGATE'), ('P', 'AND'), ('P', 'EXIT')]}
    return E[n]

TINY_AT = None
def tiny_at():
    """old body address -> tiny opcode name, ONLY where the compiled body
    is exactly the definition the engine's opcode implements."""
    global TINY_AT, FOLD
    if TINY_AT is None:
        TINY_AT, saved, fsaved = {}, set(SPEC), FOLD
        SPEC.clear(); FOLD = False        # read the real bodies, unrewritten
        nm_of = {w['s']: w['n'] for w in words}
        for w in words:
            if w['n'] in X_TINY:
                o = read_ops(w)
                if o is None: continue
                o = [(k, nm_of.get(p, p) if k == 'C' else p) for k, p in o]
                if o == _expect(w['n']): TINY_AT[w['s']] = w['n']
        SPEC.update(saved); FOLD = fsaved
        missing = set(X_TINY) - set(TINY_AT.values())
        if missing: print("tiny: no exact body match for %s" % sorted(missing))
    return TINY_AT

LOCNAME = {}
def specialise(ops):
    cs, tg = branch_targets(ops)
    if not LOCNAME:
        for w in words:
            if w['s'] in LOCALS_RT: LOCNAME[w['s']] = w['n']
    out, j = [], 0
    while j < len(ops):
        k, pl = ops[j]
        nxt = ops[j + 1] if j + 1 < len(ops) else None
        free = j + 1 < len(ops) and cs[j + 1] not in tg   # nothing enters mid-pattern
        if ('loc' in SPEC and k == 'LITOFF' and nxt and nxt[0] == 'C'
                and nxt[1] in LOCNAME and free):
            out.append(('LOC', (LOCNAME[nxt[1]], pl))); j += 2; continue
        if ('var' in SPEC and k == 'C' and is_var(pl) and nxt in (('P', '@'), ('P', '!'))
                and free):
            out.append(('VF' if nxt[1] == '@' else 'VS', pl)); j += 2; continue
        if ('imm' in SPEC and k == 'LIT' and -128 <= pl <= 127 and free
                and nxt in (('P', '+'), ('P', '='))):
            out.append(('ADDI' if nxt[1] == '+' else 'EQI', pl)); j += 2; continue
        if 'tiny' in SPEC and k == 'C' and pl in tiny_at():
            out.append(('P', tiny_at()[pl])); j += 1; continue
        out.append(ops[j]); j += 1
    return out

NOFOLD = ('EXIT', 'BRANCH', '?BRANCH', 'NOOP')
FOLDSET = None        # None = every primitive; else a set of names
def fold_exit(ops):
    """Fold `prim EXIT` into one folded opcode, unless something can
    enter at the EXIT: a branch or loop target, or a DOES> tail."""
    cs, c = [], 0
    for k, pl in ops: cs.append(c); c += op_cells(k, pl)
    targets = set()
    for j, (k, pl) in enumerate(ops):
        if k in ('BR', 'QBR'): targets.add(cs[j] + CELL + pl)
        if k == 'OPD': targets.add(cs[j] + pl)
        if k == 'ALN': targets.add(cs[j])
    out, j = [], 0
    while j < len(ops):
        k, pl = ops[j]
        nxt = ops[j + 1] if j + 1 < len(ops) else None
        if nxt == ('P', 'EXIT') and cs[j + 1] not in targets:
            if k == 'P' and pl not in NOFOLD and (FOLDSET is None or pl in FOLDSET):
                out.append(('PX', pl)); j += 2; continue
            if k in ('ADDI', 'EQI'):
                out.append((k + 'X', pl)); j += 2; continue
            if k == 'LIT' and 0 <= pl <= 0xFFFF and (FOLDSET is None or 'LIT' in FOLDSET):
                out.append(('LITX', pl)); j += 2; continue
        out.append(ops[j]); j += 1
    return out

# ---- the layout map: cell offsets against token offsets -------------
#
# A branch operand in the cell image is a BYTE offset from the operand
# cell's own address (`relf.c` does `ip += CELL(ip)` with ip already
# past the opcode). In the token image it must be a TOKEN offset from
# the operand token's own position, because `sod16.c` does
# `ip += 2 * (int16_t)TOK(ip)`.
#
# Those are different numbers, and the conversion needs to know where
# every operation lands in both representations - which is what layout()
# gives. Iteration 169 found the translator was passing the byte offset
# through unconverted for 1,308 of 1,310 branches, and the round trip
# could not see it: it decoded with the same convention it encoded with,
# so it agreed with itself. Both directions now genuinely convert.
#
# Every position here is a BYTE offset from the start of the body, in
# each image. Bodies start CELL-aligned in both.

FOLD = False          # set by the layout pass: fold EXIT into prims
ALIGN_TAILS = 0       # set by the layout pass: DOES> tails aligned to this
FOLDBASE = 128        # folded opcode = FOLDBASE + primitive index
V8 = False            # byte-stream mode: 1-byte ops, 2-byte calls
V8_FOLDLIST = []      # v8: folded opcodes are 73 + position in this list
V8_LIT32, V8_DOVAR, V8_DODOES, V8_LIT8, V8_LIT8X, V8_FOLD0 = 68, 69, 70, 71, 72, 73
V8_CALLTOK = [None]   # layout pass binds: old target addr -> scaled value
V8_FORCE4 = set()     # (kind, payload) pinned to the WIDE slot form.
# Same problem as V8_FORCE3, for VF/VS/LOC: a slot is 2 bytes if the
# scaled value fits 15 bits and 3 if not, so its width depends on where
# its target landed. At a call scale of 3 every slot in a 70 KB image
# fits; at scale 0 many do not.
V8_FORCE3 = set()     # targets pinned to the 3-byte call form.
# A call's width depends on where its target landed, and 98% of calls
# are BACKWARD - the target is already placed, so the width is known
# exactly. The ~2% that are forward references have no offset yet, so
# the layout pass pins them here and they are emitted far regardless of
# how small the value turns out to be. The far form encodes any value
# the near form can, so pinning costs a byte and is never wrong; what
# matters is that sizing and emission make the SAME choice, or the body
# is not the length the placement reserved for it.
VARCALL = True        # 10xxxxxx = 2-byte call, 11xxxxxx = 3-byte
VARSLOT = True        # 0xxxxxxx+1 = 15-bit slot, 1xxxxxxx+2 = 23-bit
OP_CTX = [None]       # (ops, j) while sizing, so op_bytes can see context
V8_LIT64, V8_ESC = 0x7C, 0x7D

# ---- the escaped band (Iteration 202) -------------------------------
# Half the primitive band was OS/libc wrappers: 34 of 68 opcodes for
# 3.2% of static sites and 0.006% of dispatches. They now live behind
# ESC + a one-byte selector, which costs one byte at 143 sites and
# frees 32 opcodes - the one resource this encoding cannot widen later.
# EMIT and KEY stay direct: they are the only two plausibly hot ones,
# and the profile that says otherwise is from scripts that print little.
ESCAPE = False        # --escape: OFF until the BUF-ALLOC fault is found
ESC_PRIMS_ALL = set("""BYE OPEN-FILE CLOSE-FILE READ-LINE WRITE-LINE READ-FILE
WRITE-FILE SYSTEM REPOSITION-FILE FILE-POSITION DELETE-FILE FILE-SIZE FORK
EXECVE WAITPID PIPE DUP2 GETENV SETENV SYS-EXIT CHDIR GETCWD SYS-ARGC SYS-ARG
GETPID UNSETENV ALLOCATE FREE RESIZE GETPWHOME GETFSIZE SETFSIZE""".split())

ESC_PRIMS = set()     # populated from ESC_PRIMS_ALL when --escape is on

def cv8_op(name):
    """(opcode, escaped) for a primitive. Non-escaped primitives keep
    kernel.4's order, compacted; escaped ones get an ESC selector."""
    esc, plain = [], []
    for n in prims:
        (esc if n in ESC_PRIMS else plain).append(n)
    if name in ESC_PRIMS: return esc.index(name), True
    return plain.index(name), False

# ---- specialisations borrowed from other VMs (CV8 only; CV8.md 10) ----
SPEC = set()          # any of: 'loc' 'tiny' 'var' 'small'
V8_PFA = [None]       # layout pass binds: old var address -> new PFA >> S
V8_LOC = [None]       # layout pass binds: old START offset -> new >> S
X_LIT0, X_LIT1, X_LITM1, X_VF, X_VS = 0x60, 0x61, 0x62, 0x63, 0x64
X_LOC = {'LSAVE': 0x65, 'LRESTORE': 0x66, 'L!': 0x67, 'LZERO': 0x68}
TINY_NAMES = ['0=', '-', '<>', '0<', '>', '2DUP', '2DROP', 'CHAR+', '1+',
              'CELL+', 'CELLS', '1-', 'INVERT', 'COUNT', 'ALIGNED']
X_TINY = {n: 0x69 + i for i, n in enumerate(TINY_NAMES)}
# Lua 5.4 kept exactly these immediate forms (OP_ADDI, OP_EQI): LIT n +, LIT n =
X_IMM = {'ADDI': 0x78, 'ADDIX': 0x79, 'EQI': 0x7A, 'EQIX': 0x7B}

def op_cells(k, pl):
    """Size of one operation in the CELL image, in bytes."""
    if k == 'ALN': return 0
    if k in ('VF', 'VS'): return 2 * CELL           # call + @/!
    if k in ('ADDI', 'EQI'): return 3 * CELL        # LIT n + op
    if k in ('ADDIX', 'EQIX'): return 4 * CELL      # ... + EXIT
    if k == 'LOC': return 3 * CELL                  # LIT off + call
    if k == 'PX': return 2 * CELL
    if k == 'LITX': return 3 * CELL
    if k in ('P', 'C', 'OPD', 'XT'): return CELL
    if k in ('LIT', 'LITOFF', 'BR', 'QBR'): return 2 * CELL
    if k == 'STR': return align_up(len(pl), CELL)
    raise AssertionError("unknown op kind %r" % k)

def op_bytes(k, pl, t):
    """Size of one operation in the TOKEN image, in bytes, at offset t."""
    if k == 'ALN': return (-t) % pl
    if V8:
        if k == 'C' and VARCALL:
            if OP_CTX[0] is not None and before_operand(*OP_CTX[0]): return 3
            if pl in V8_FORCE3: return 3
            return 2 if V8_CALLTOK[0] is None or V8_CALLTOK[0](pl) < (1 << 14) else 3
        if k in ('VF', 'VS', 'LOC'):
            if not VARSLOT: return 3
            if (k, pl) in V8_FORCE4: return 4
            v = slotval(k, pl)
            return 3 if v is None or v < (1 << 15) else 4
        if k in X_IMM: return 2
        if k == 'LIT' and pl in (0, 1, -1) and 'small' in SPEC: return 1
        if k == 'P' and pl in ESC_PRIMS: return 2
        if k in ('P', 'PX'): return 1
        if k == 'C': return 2
        if k in ('LIT', 'LITX'):
            if 0 <= pl < 256: return 2
            if 0 <= pl <= 0xFFFF: return 3
            if -(1 << 31) <= pl < (1 << 31): return 5
            return 1 + CELL
        if k == 'LITOFF': return 5
        if k in ('BR', 'QBR'): return 3
    if k == 'PX': return 2
    if k == 'LITX': return 4
    if k in ('P', 'C'): return 2
    if k == 'LIT':
        if 0 <= pl <= 0xFFFF: return 4          # LIT + one token
        if _fits32(pl): return 6                # LIT32 + two tokens
        return 2 + CELL                         # LIT64 + CELL/2 tokens
    if k == 'LITOFF': return 6          # always the 32-bit form
    if k in ('BR', 'QBR'): return 4
    if k in ('OPD', 'XT'): return CELL
    if k == 'STR': return align_up(t + len(pl), CELL) - t
    raise AssertionError("unknown op kind %r" % k)

def before_operand(ops, j):
    """True if op j is a call whose inline CELL operand follows it."""
    return (ops[j][0] == 'C' and j + 1 < len(ops)
            and ops[j + 1][0] in ('OPD', 'XT'))

def pad_before(ops, j, t):
    """NOOP padding needed before op j so an inline operand lands aligned.
    A call before an operand ALWAYS uses the 3-byte far form, so the
    padding does not depend on how far the target happens to be. With
    VARCALL a near call is 2 bytes and a far one 3; letting the distance
    decide made (POSTPONE) and (LOOP) read a misaligned operand."""
    if before_operand(ops, j):
        return (-(t + (3 if (V8 and VARCALL) else 2))) % CELL
    return 0

def layout(ops):
    """(cell offset -> token offset, cell offsets, token offsets, totals).

    One entry per operation start, plus one for the position just past
    the last operation, because a branch forward out of the final
    operation targets exactly there."""
    c2t, cs, ts, c, t = {}, [], [], 0, 0
    for j, (k, pl) in enumerate(ops):
        OP_CTX[0] = (ops, j)
        t += pad_before(ops, j, t)
        if k == 'ALN': t += op_bytes(k, pl, t)
        c2t[c] = t; cs.append(c); ts.append(t)
        c += op_cells(k, pl)
        if k != 'ALN': t += op_bytes(k, pl, t)
    OP_CTX[0] = None
    c2t[c] = t
    return c2t, cs, ts, c, t

# ---- encode an operation list to 16-bit tokens ---------------------
MASK = 0xFFFF

G_CALLTOK = [None]
def CALLTOK(target, n):
    """Call token for a call to old address `target` (word number n).
    SOD16 default; the layout pass rebinds this for CPT16."""
    return 256 + n
G_CALLTOK[0] = CALLTOK

def slotval(k, pl):
    """scaled slot value for a VF/VS (variable) or LOC (locals) op,
    or None during the sizing pass before the layout is known."""
    try:
        return V8_PFA[0](pl) if k in ('VF', 'VS') else V8_LOC[0](pl[1])
    except Exception:
        return None

def emit_slot(b, v, wide=False):
    if not VARSLOT:
        b.append(v & 0xFF); b.append((v >> 8) & 0xFF); return
    if v < (1 << 15) and not wide:
        b.append(v >> 8); b.append(v & 0xFF)
    else:
        assert v < (1 << 23), "slot %d out of 23 bits" % v
        b.append(0x80 | (v >> 16)); b.append((v >> 8) & 0xFF); b.append(v & 0xFF)

def to_bytes_v8(ops):
    """The v8 byte stream for one body. Same layout() as the 16-bit
    stream, so padding and branch conversion share one definition."""
    c2t, cs, ts, _, ttot = layout(ops)
    b = bytearray()
    def le(v, n): b.extend((v & ((1 << (8 * n)) - 1)).to_bytes(n, 'little'))
    for j, (k, pl) in enumerate(ops):
        while len(b) < ts[j]: b.append(idx_of['NOOP'])
        assert len(b) == ts[j], "v8 layout and emission disagree"
        if k == 'ALN': continue
        if k == 'P' and pl in X_TINY: b.append(X_TINY[pl])
        elif k == 'P' and pl in ESC_PRIMS:
            i_, _ = cv8_op(pl); b.append(V8_ESC); b.append(i_)
        elif k == 'P': b.append(cv8_op(pl)[0])
        elif k in X_IMM:
            b.append(X_IMM[k]); b.append(pl & 0xFF)
        elif k in ('VF', 'VS'):
            b.append(X_VF if k == 'VF' else X_VS)
            emit_slot(b, slotval(k, pl) or 0, (k, pl) in V8_FORCE4)
        elif k == 'LOC':
            b.append(X_LOC[pl[0]])
            emit_slot(b, slotval(k, pl) or 0, (k, pl) in V8_FORCE4)
        elif k == 'LIT' and pl in (0, 1, -1) and 'small' in SPEC:
            b.append({0: X_LIT0, 1: X_LIT1, -1: X_LITM1}[pl])
        elif k == 'PX':
            assert pl not in ESC_PRIMS, "cannot fold an escaped primitive"
            b.append(V8_FOLD0 + V8_FOLDLIST.index(pl))
        elif k in ('LIT', 'LITX'):
            x = k == 'LITX'
            if 0 <= pl < 256: b.append(V8_LIT8X if x else V8_LIT8); b.append(pl)
            elif 0 <= pl <= 0xFFFF:
                b.append(V8_FOLD0 + V8_FOLDLIST.index('LIT') if x else idx_of['LIT']); le(pl, 2)
            elif -(1 << 31) <= pl < (1 << 31):
                assert not x; b.append(V8_LIT32); le(pl, 4)
            else:
                # A value wider than 32 bits. Until Iteration 194 this
                # was silently masked to 32 bits and sign-extended, so
                # $123456789ABC evaluated differently under CV8 than
                # under the cell engine. Now it gets a full cell.
                assert not x, "cannot fold EXIT into a LIT64"
                b.append(V8_LIT64); le(pl, CELL)
        elif k == 'LITOFF': b.append(V8_LIT32); le(pl, 4)
        elif k == 'C':
            v = V8_CALLTOK[0](pl) if V8_CALLTOK[0] else 0
            if VARCALL:
                if before_operand(ops, j):
                    assert v < (1 << 22), "call target %d out of 22 bits" % v
                    b.append(0xC0 | (v >> 16)); b.append((v >> 8) & 0xFF)
                    b.append(v & 0xFF)
                elif v < (1 << 14) and pl not in V8_FORCE3:
                    b.append(0x80 | (v >> 8)); b.append(v & 0xFF)
                else:
                    assert v < (1 << 22), "varcall target %d out of 22 bits" % v
                    b.append(0xC0 | (v >> 16)); b.append((v >> 8) & 0xFF)
                    b.append(v & 0xFF)
            else:
                assert 0 <= v < 0x8000, "v8 call value %d out of 15 bits" % v
                b.append(0x80 | (v >> 8)); b.append(v & 0xFF)
        elif k in ('BR', 'QBR'):
            b.append(idx_of['BRANCH' if k == 'BR' else '?BRANCH'])
            tgt = cs[j] + CELL + pl
            if tgt not in c2t: return None
            le(c2t[tgt] - (ts[j] + 1), 2)       # from the operand, in bytes
        elif k == 'XT': le(pl, CELL)
        elif k == 'OPD':
            tgt = cs[j] + pl
            if tgt not in c2t: return None
            le(c2t[tgt] - ts[j], CELL)
        elif k == 'STR':
            b.extend(pl); b.extend(bytes(op_bytes(k, pl, ts[j]) - len(pl)))
    while len(b) < ttot: b.append(idx_of['NOOP'])
    return list(b)

def to_tokens(ops):
    if V8: return to_bytes_v8(ops)
    """The 16-bit token stream for one word body, or None if it cannot
    be encoded. Positions come from layout(), and padding is emitted by
    catching up to the position layout() assigned, so the two cannot
    drift apart."""
    c2t, cs, ts, _, ttot = layout(ops)
    t = []
    for j, (k, pl) in enumerate(ops):
        while len(t) * 2 < ts[j]: t.append(idx_of['NOOP'])   # padding
        assert len(t) * 2 == ts[j], "layout and emission disagree"
        if k == 'ALN':
            pass                                  # padding already emitted
        elif k == 'PX':
            t.append(FOLDBASE + idx_of[pl])
        elif k == 'LITX':
            t.append(FOLDBASE + idx_of['LIT']); t.append(pl)
        elif k == 'P':
            i = idx_of[pl]
            assert i < 256, "primitive index %d exceeds the 0..255 band" % i
            t.append(i)
        elif k == 'C':
            n = num.get(pl)
            if n is None: return None            # call outside the dump
            assert n + 256 <= 65535, "word number %d exceeds the token field" % n
            t.append(G_CALLTOK[0](pl, n))
        elif k == 'LITOFF':
            v = pl & ((1 << 32) - 1)
            t.append(LIT32); t.append(v & MASK); t.append((v >> 16) & MASK)
        elif k == 'LIT':
            if 0 <= pl <= 0xFFFF:
                t.append(idx_of['LIT']); t.append(pl)
            elif _fits32(pl):
                v = pl & ((1 << 32) - 1)
                t.append(LIT32); t.append(v & MASK); t.append((v >> 16) & MASK)
            else:
                v = pl & ((1 << (8 * CELL)) - 1)
                t.append(LIT64)
                for sh in range(0, 8 * CELL, 16):
                    t.append((v >> sh) & MASK)
        elif k in ('BR', 'QBR'):
            t.append(idx_of['BRANCH' if k == 'BR' else '?BRANCH'])
            # Convert. Both offsets are measured from the operand
            # itself, which sits one cell past the opcode in the cell
            # image and one token past it here, so the anchors move
            # together.
            tgt = cs[j] + CELL + pl
            if tgt not in c2t: return None        # not an operation start
            off = (c2t[tgt] - (ts[j] + 2)) // 2
            assert -32768 <= off <= 32767, \
                "branch offset %d does not fit a signed 16-bit token" % off
            t.append(off & MASK)
        elif k == 'XT':
            # Relative address into another word. Relocated by the
            # layout pass, which is the only place that knows the new
            # position of the target; passed through unchanged here.
            for sh in range(0, 8 * CELL, 16):
                t.append((pl & ((1 << (8 * CELL)) - 1)) >> sh & MASK)
        elif k == 'OPD':
            # (LOOP)'s operand stays a CELL holding a BYTE offset, so
            # `DUP @ +` needs no change. The distance is recomputed for
            # the new layout; the units do not change, the spacing does.
            tgt = cs[j] + pl
            if tgt not in c2t: return None
            off = c2t[tgt] - ts[j]
            for sh in range(0, 8 * CELL, 16):
                t.append((off & ((1 << (8 * CELL)) - 1)) >> sh & MASK)
        elif k == 'STR':
            # No marker token. The counted string must begin at the very
            # next address after the call token, because that is where
            # (S") looks for it. The tail is zero-padded to the next CELL
            # boundary, which is where ALIGNED resumes.
            body = pl + bytes(op_bytes(k, pl, ts[j]) - len(pl))
            for i in range(0, len(body), 2):
                t.append(body[i] | (body[i + 1] << 8))
    while len(t) * 2 < ttot: t.append(idx_of['NOOP'])
    return t

# ---- decode tokens back, to prove the encoding is reversible -------
def from_tokens(t):
    # Pass 1: recover the operation list, leaving branch and loop
    # offsets as stored, and remembering each operation's byte offset so
    # pass 2 can convert them back. Byte offset is always 2*index: every
    # token is two bytes, padding included.
    out, at, i = [], [], 0
    while i < len(t):
        v = t[i]
        if v == idx_of['NOOP']:
            # Padding before a (LOOP) call is NOOPs, and so is a real
            # NOOP. Tell them apart the only way available: look past
            # the run and see whether a loop call follows at exactly the
            # aligned position. Operands are positional; so is this.
            k = i
            while k < len(t) and t[k] == idx_of['NOOP']: k += 1
            if (k < len(t) and t[k] >= 256
                    and order[t[k] - 256]['s'] in (LOOPS | XTS)
                    and (2 * k + 2) % CELL == 0 and (2 * i + 2) % CELL != 0):
                i = k; continue
        at.append(i)
        if v >= 256:
            tgt = order[v - 256]['s']
            out.append(('C', tgt)); i += 1
            if tgt in LOOPS or tgt in XTS:
                at.append(i)
                raw = 0
                for j in range(CELL // 2): raw |= t[i + j] << (16 * j)
                if raw >= 1 << (8 * CELL - 1): raw -= 1 << (8 * CELL)
                out.append(('OPD' if tgt in LOOPS else 'XT', raw))
                i += CELL // 2
            elif tgt in STR:
                n = t[i] & 0xFF
                nb = align_up(2 * i + 1 + n, CELL) - 2 * i
                body = bytearray()
                for j in range(nb // 2):
                    body.append(t[i + j] & 0xFF); body.append(t[i + j] >> 8)
                at.append(i)
                out.append(('STR', bytes(body[:1 + n]))); i += nb // 2
        elif v == LIT32:
            val = (t[i+2] << 16) | t[i+1]
            if val >= (1 << 31): val -= (1 << 32)
            out.append(('LIT', val)); i += 3
        elif v == idx_of['LIT']:
            out.append(('LIT', t[i+1])); i += 2
        elif v == idx_of['BRANCH']:
            o = t[i+1]; out.append(('BR', o - 65536 if o >= 32768 else o)); i += 2
        elif v == idx_of['?BRANCH']:
            o = t[i+1]; out.append(('QBR', o - 65536 if o >= 32768 else o)); i += 2
        else:
            out.append(('P', prims[v])); i += 1

    # Pass 2: convert branch and loop offsets back to the cell image's
    # byte offsets. This is the inverse of the conversion in to_tokens,
    # and doing it here is what lets the round trip test that conversion
    # at all rather than agreeing with itself.
    retag(out)
    _, cs, ts, ctot, _ = layout(out)
    t2c = {tb: cb for tb, cb in zip(ts, cs)}
    t2c[len(t) * 2] = ctot
    for j, (k, pl) in enumerate(out):
        if k in ('BR', 'QBR'):
            tgt = ts[j] + 2 + 2 * pl
            if tgt not in t2c: return None
            out[j] = (k, t2c[tgt] - (cs[j] + CELL))
        elif k == 'OPD':
            tgt = ts[j] + pl
            if tgt not in t2c: return None
            out[j] = (k, t2c[tgt] - cs[j])
    return out

# ---- optional emission of a loadable token file --------------------
# Format is deliberately plain text: the point of this prototype is to
# be checkable by eye and by diff, not to be fast to load. A binary
# image is a later concern, and premature here.
#
#   W <wordnum> <ntokens> <name>
#   T <tok> <tok> ...
#
# The engine rebuilds its dispatch table from this the same way a real
# load would rebuild it from the dictionary link chain: word N is the
# Nth W record, in chain order. Nothing about the table is stored.
EMIT = None
if '--emit' in sys.argv:
    EMIT = open(sys.argv[sys.argv.index('--emit') + 1], 'w')

ok = fail = skipped = ambiguous = 0
tot_cell = tot_tok = 0
failures = []
for w in words:
    span = w['e'] - w['s']
    if w['n'] in DATA:
        skipped += 1; tot_cell += span; tot_tok += span; continue
    ops = read_ops(w)
    if ops is None:
        skipped += 1; tot_cell += span; tot_tok += span; continue
    t = to_tokens(ops)
    if t is None:
        skipped += 1; tot_cell += span; tot_tok += span; continue

    # The stub for LIT, BRANCH or ?BRANCH encodes to [prim, EXIT], which
    # cannot be told from "prim, with EXIT as its operand" - by exactly
    # the positional-operand rule that makes the encoding work
    # everywhere else. That ambiguity is inherited, not introduced: the
    # cell body has it too, and either engine executing one of these
    # three words would consume the EXIT as an operand and run on past
    # the word. The bodies exist so the NAME resolves, not to be run.
    # So they are translated and counted for size, and excluded from the
    # equality check with a reason rather than silently passing it.
    stub = stub_ops(w)
    if stub is not None and stub[0][1] in OPERAND_PRIMS:
        ambiguous += 1
        tot_cell += span; tot_tok += len(t) * 2
        if EMIT:
            EMIT.write("W %d %d %s\n" % (num[w['s']], len(t), w['n']))
            EMIT.write("T " + " ".join(str(x) for x in t) + "\n")
        continue

    back = from_tokens(t)
    if back is None:
        # The token stream did not decode at all - a branch offset landed
        # somewhere that is not an operation boundary. Reported, not
        # raised: this tool is meant to be wired into tests/verify, where
        # a traceback is a worse diagnostic than a named word.
        fail += 1
        if len(failures) < 3:
            failures.append((w['n'], -1, 'undecodable', 'branch target is not an op start'))
    elif back == ops:
        ok += 1
    else:
        fail += 1
        if len(failures) < 3:
            for j, (a, b) in enumerate(zip(ops, back)):
                if a != b: failures.append((w['n'], j, a, b)); break
            else: failures.append((w['n'], -1, len(ops), len(back)))
    tot_cell += span; tot_tok += len(t) * 2
    if EMIT:
        EMIT.write("W %d %d %s\n" % (num[w['s']], len(t), w['n']))
        EMIT.write("T " + " ".join(str(x) for x in t) + "\n")

if EMIT: EMIT.close()
print("dump %s  cell %d" % (DUMP, CELL))
print("round trip: %d words reproduce exactly, %d differ, %d skipped,"
      " %d ambiguous by construction"
      % (ok, fail, skipped, ambiguous))
for f in failures: print("   MISMATCH %s op %d: was %r, back %r" % f)
print()
print("word bodies: cell %d B   token %d B   %.3fx"
      % (tot_cell, tot_tok, tot_tok / tot_cell))
sys.exit(1 if fail else 0)
