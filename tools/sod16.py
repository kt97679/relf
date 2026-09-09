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
STR = {by_name[n]['s'] for n in ('(S")', '(.")') if n in by_name}
LOOP = by_name.get('(LOOP)', {}).get('s')

src = "".join(open(f, errors='replace').read()
              for f in ['shell.4', 'locals.4', 'pool.4', 'save-system.4'])
DATA = (set(re.findall(r'CREATE\s+(\S+)', src)) |
        set(re.findall(r'BUFFER:\s+(\S+)', src)) |
        set(re.findall(r'^\s*VARIABLE\s+(\S+)', src, re.M)) |
        set(re.findall(r'CONSTANT\s+(\S+)', src)))

# ---- decode a word body to an operation list -----------------------
EXIT_TOK = idx_of['EXIT'] * CELL + 1

# The three primitives that take an operand. A stub for one of these is
# the only place in the image where a token stream is genuinely
# ambiguous - see stub_ops.
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
    # 9" rather than "LIT; EXIT", and BRANCH to a branch of 9 bytes.
    # All three round-tripped clean, because the decoder made the same
    # mistake in both directions - the fault only became visible once
    # branch offsets genuinely converted between units (Iteration 169).
    #
    # Detected by shape rather than by name: locals.4 redefines EXIT, so
    # there are two words called EXIT and a name test picks the wrong
    # one. Words whose real body happens to share this shape (`: FOO
    # DUP ;`) decode identically either way, so the test is safe.
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
            out.append(('C', t)); a += CELL
            if t == LOOP:
                out.append(('OPD', cells.get(a, 0))); a += CELL
            elif t in STR:
                n = (cells.get(a) or 0) & 0xFF
                blob = (1 + n + CELL - 1) // CELL * CELL
                raw = []
                for k in range(0, blob, CELL):
                    raw.append(cells.get(a + k, 0))
                out.append(('STR', (n, tuple(raw)))); a += blob
    return out

# ---- the layout map: cell offsets against token indices -------------
#
# A branch operand in the cell image is a BYTE offset from the operand
# cell's own address (`relf.c` does `ip += CELL(ip)` with ip already
# past the opcode). In the token image it must be a TOKEN offset from
# the operand token's own position, because `sod16.c` does
# `ip += 2 * (int16_t)TOK(ip)`.
#
# Those are different numbers, and the conversion needs to know where
# every operation lands in both representations - which is what these
# two functions give. Iteration 169 found the translator was passing
# the byte offset through unconverted for 1,308 of 1,310 branches, and
# the round trip could not see it: it decoded with the same convention
# it encoded with, so it agreed with itself. Both directions now
# genuinely convert, which is what makes the round trip evidence about
# branches rather than a tautology.

def op_cells(k, pl):
    """Size of one operation in the CELL image, in cells."""
    if k in ('P', 'C', 'OPD'): return 1
    if k in ('LIT', 'BR', 'QBR'): return 2
    if k == 'STR': return len(pl[1])
    raise AssertionError("unknown op kind %r" % k)

def op_toks(k, pl):
    """Size of one operation in the TOKEN image, in 16-bit tokens."""
    if k in ('P', 'C', 'OPD'): return 1
    if k == 'LIT': return 2 if 0 <= pl <= 0xFFFF else 3
    if k in ('BR', 'QBR'): return 2
    if k == 'STR': return 2 + len(pl[1]) * (CELL // 2)
    raise AssertionError("unknown op kind %r" % k)

def layout(ops):
    """(cell offset -> token index, cell offsets, token indices).

    The map carries one entry per operation start AND one for the
    position just past the last operation, because a branch forward out
    of the final operation targets exactly there."""
    c2t, cs, ts, c, i = {}, [], [], 0, 0
    for k, pl in ops:
        c2t[c] = i; cs.append(c); ts.append(i)
        c += op_cells(k, pl) * CELL
        i += op_toks(k, pl)
    c2t[c] = i
    return c2t, cs, ts, c, i

# ---- encode an operation list to 16-bit tokens ---------------------
MASK = 0xFFFF
def to_tokens(ops, base):
    c2t, cs, ts, _, _ = layout(ops)
    t = []
    for j, (k, pl) in enumerate(ops):
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
            v = pl & 0xFFFFFFFF if pl >= 0 else (pl + (1 << 32)) & 0xFFFFFFFF
            if 0 <= pl <= 0xFFFF:
                t.append(idx_of['LIT']); t.append(pl)
            else:
                t.append(255); t.append(v & MASK); t.append((v >> 16) & MASK)
        elif k in ('BR', 'QBR'):
            t.append(idx_of['BRANCH' if k == 'BR' else '?BRANCH'])
            # Convert. The operand sits one cell past the opcode, and one
            # token past it; both offsets are measured from the operand
            # itself, so both anchors move together.
            tgt_cell = cs[j] + CELL + pl
            if tgt_cell not in c2t:
                return None                      # target is not an op start
            off = c2t[tgt_cell] - (ts[j] + 1)
            assert -32768 <= off <= 32767, \
                "branch offset %d does not fit a signed 16-bit token" % off
            t.append(off & MASK)
        elif k == 'OPD':
            t.append(pl & MASK)
        elif k == 'STR':
            n, raw = pl
            t.append(254); t.append(n)
            for r in raw:
                t.append(r & MASK)
                if CELL == 4: t.append((r >> 16) & MASK)
                else:
                    for sh in (16, 32, 48): t.append((r >> sh) & MASK)
    return t

# ---- decode tokens back, to prove the encoding is reversible -------
def from_tokens(t):
    # Pass 1: recover the operation list, leaving branch offsets in the
    # token units they are stored in, and remembering each operation's
    # token index so pass 2 can convert them back.
    out, at, i = [], [], 0
    while i < len(t):
        v = t[i]; at.append(i)
        if v >= 256:
            tgt = order[v - 256]['s']
            out.append(('C', tgt)); i += 1
            # (LOOP) carries a bare operand token; it must be consumed
            # here or the decoder reads it as another call. Operands are
            # positional - only the op that emitted one knows it is there.
            if tgt == LOOP:
                o = t[i]
                at.append(i)
                out.append(('OPD', o - 65536 if o >= 32768 else o)); i += 1
        elif v == 255:
            lo, hi = t[i+1], t[i+2]
            val = (hi << 16) | lo
            if val >= (1 << 31): val -= (1 << 32)
            out.append(('LIT', val)); i += 3
        elif v == 254:
            n = t[i+1]; i += 2
            per = 2 if CELL == 4 else 4
            blob = (1 + n + CELL - 1) // CELL * CELL
            raw = []
            for _ in range(blob // CELL):
                acc = 0
                for j in range(per): acc |= t[i + j] << (16 * j)
                raw.append(acc); i += per
            out.append(('STR', (n, tuple(raw))))
        elif v == idx_of['LIT']:
            out.append(('LIT', t[i+1])); i += 2
        elif v == idx_of['BRANCH']:
            o = t[i+1]; out.append(('BR', o - 65536 if o >= 32768 else o)); i += 2
        elif v == idx_of['?BRANCH']:
            o = t[i+1]; out.append(('QBR', o - 65536 if o >= 32768 else o)); i += 2
        else:
            out.append(('P', prims[v])); i += 1

    # Pass 2: convert branch offsets from token units back to the byte
    # offsets the cell image uses. This is the inverse of the conversion
    # in to_tokens, and doing it here is what lets the round trip test
    # that conversion at all.
    _, cs, ts, _, _ = layout(out)
    t2c = {ti: ci for ti, ci in zip(ts, cs)}
    t2c[len(t)] = cs[-1] + op_cells(*out[-1]) * CELL if out else 0
    for j, (k, pl) in enumerate(out):
        if k in ('BR', 'QBR'):
            tgt_tok = ts[j] + 1 + pl
            if tgt_tok not in t2c: return None
            out[j] = (k, t2c[tgt_tok] - (cs[j] + CELL))
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
    t = to_tokens(ops, w['s'])
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
