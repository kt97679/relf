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
for l in open(DUMP, errors='replace'):
    l = l.rstrip()
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
BAD_WORDS  = ('(?DO)', '(LEAVE)')

STR  = {by_name[n]['s'] for n in STR_WORDS  if n in by_name}
LOOPS = {by_name[n]['s'] for n in LOOP_WORDS if n in by_name}
BAD  = {by_name[n]['s'] for n in BAD_WORDS  if n in by_name}

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

def read_ops(w):
    # A PRIMITIVE stub is not threaded code. cross.4's PRIMITIVE emits
    # `"HEADER DUP , ,-T EXIT-TOKEN ,-T`, so the body is exactly
    # [prim-token, EXIT]. Read as code, LIT/BRANCH/?BRANCH swallow that
    # trailing EXIT as their operand: the word LIT translated to "push
    # 9" rather than "LIT; EXIT". Detected by shape rather than by name,
    # because locals.4 redefines EXIT and a name test picks the wrong
    # word.
    st = stub_ops(w)
    if st is not None: return st

    out, a = [], w['s']
    while a < w['e']:
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

def op_cells(k, pl):
    """Size of one operation in the CELL image, in bytes."""
    if k in ('P', 'C', 'OPD'): return CELL
    if k in ('LIT', 'BR', 'QBR'): return 2 * CELL
    if k == 'STR': return align_up(len(pl), CELL)
    raise AssertionError("unknown op kind %r" % k)

def op_bytes(k, pl, t):
    """Size of one operation in the TOKEN image, in bytes, at offset t."""
    if k in ('P', 'C'): return 2
    if k == 'LIT': return 4 if 0 <= pl <= 0xFFFF else 6
    if k in ('BR', 'QBR'): return 4
    if k == 'OPD': return CELL
    if k == 'STR': return align_up(t + len(pl), CELL) - t
    raise AssertionError("unknown op kind %r" % k)

def pad_before(ops, j, t):
    """NOOP padding needed before op j so an inline operand lands aligned."""
    if ops[j][0] == 'C' and j + 1 < len(ops) and ops[j + 1][0] == 'OPD':
        return (-(t + 2)) % CELL      # operand sits 2 bytes after the call
    return 0

def layout(ops):
    """(cell offset -> token offset, cell offsets, token offsets, totals).

    One entry per operation start, plus one for the position just past
    the last operation, because a branch forward out of the final
    operation targets exactly there."""
    c2t, cs, ts, c, t = {}, [], [], 0, 0
    for j, (k, pl) in enumerate(ops):
        t += pad_before(ops, j, t)
        c2t[c] = t; cs.append(c); ts.append(t)
        c += op_cells(k, pl)
        t += op_bytes(k, pl, t)
    c2t[c] = t
    return c2t, cs, ts, c, t

# ---- encode an operation list to 16-bit tokens ---------------------
MASK = 0xFFFF

def to_tokens(ops):
    """The 16-bit token stream for one word body, or None if it cannot
    be encoded. Positions come from layout(), and padding is emitted by
    catching up to the position layout() assigned, so the two cannot
    drift apart."""
    c2t, cs, ts, _, ttot = layout(ops)
    t = []
    for j, (k, pl) in enumerate(ops):
        while len(t) * 2 < ts[j]: t.append(idx_of['NOOP'])   # padding
        assert len(t) * 2 == ts[j], "layout and emission disagree"
        if k == 'P':
            i = idx_of[pl]
            assert i < 256, "primitive index %d exceeds the 0..255 band" % i
            t.append(i)
        elif k == 'C':
            n = num.get(pl)
            if n is None: return None            # call outside the dump
            assert n + 256 <= 65535, "word number %d exceeds the token field" % n
            t.append(256 + n)
        elif k == 'LIT':
            v = pl & ((1 << 32) - 1)
            if 0 <= pl <= 0xFFFF:
                t.append(idx_of['LIT']); t.append(pl)
            else:
                t.append(LIT32); t.append(v & MASK); t.append((v >> 16) & MASK)
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
            if (k < len(t) and t[k] >= 256 and order[t[k] - 256]['s'] in LOOPS
                    and (2 * k + 2) % CELL == 0 and (2 * i + 2) % CELL != 0):
                i = k; continue
        at.append(i)
        if v >= 256:
            tgt = order[v - 256]['s']
            out.append(('C', tgt)); i += 1
            if tgt in LOOPS:
                at.append(i)
                raw = 0
                for j in range(CELL // 2): raw |= t[i + j] << (16 * j)
                if raw >= 1 << (8 * CELL - 1): raw -= 1 << (8 * CELL)
                out.append(('OPD', raw)); i += CELL // 2
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
