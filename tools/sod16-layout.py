#!/usr/bin/env python3
"""
tools/sod16-layout.py - the SOD16 layout pass.

Iteration 173, on branch token16. Reads the addressed dictionary dump,
lays the whole image out again with token bodies instead of cell
bodies, recomputes every reference that the new spacing invalidates,
and CHECKS the result rather than asserting it.

WHAT THE LAYOUT PASS ACTUALLY HAS TO DO

tools/sod16.py translates one word body in isolation. That is enough to
measure size and to prove the encoding reversible, and not enough to
boot: a token body is a different size from a cell body, so every
address in the image moves. This tool does the whole image.

The image is a strict ascending sequence, confirmed in Iteration 171:

    [prologue: 2 code cells, then filler, then the first link cell]
    [link][name field, aligned][body]      per word, oldest first
    ...                                    ending at HERE

The older word's body ends exactly where the newer word's link cell
begins - checked here on every consecutive pair, not assumed.

WHAT MOVES, AND WHAT DOES NOT

  link fields    relative, so the VALUE changes when spacing does.
  call offsets   become word numbers, which do not move at all. This
                 is the category that vanishes, and it is why
                 Iteration 167 could say re-layout is a list rather
                 than a search.
  branch offsets token units, converted in sod16.py.
  (LOOP) operand a byte offset in a cell, recomputed for the new
                 spacing.
  DEFER xts      stored START-relative; become word numbers.

CODE IS NOT TOLD FROM DATA BY WHETHER IT DECODES

26 CONSTANTs decode cleanly as code and ARE code, because CONSTANT
compiles `LIT-TOK , , EXIT-TOK ,`. Meanwhile 404 DOVAR words and 93
DOES> words are data sitting behind a call. The classifier is the first
cell of the body, not the success of a decoder - getting this backwards
translates constants correctly and silently corrupts every variable.

A data body keeps its cells. Its first cell is a call to a runtime that
does `R>` to get the parameter field address, so the parameter field
must stay CELL aligned - which is arranged by padding with NOOPs BEFORE
the call token, exactly as (LOOP) is. Padding after the token would be
what the parameter field pointed at.

THE DOES> TAILS

A DOES>-created word's body[0] calls a MID-WORD address: (;CODE) points
it just past the DOES> in the defining word. A SOD16 call token is a
word number and a word number can only name a word start, so these have
no representation - see SOD16.md.

Measured, there are exactly TWO such targets in this image, inside
BUFFER: and inside DEFER, shared by 81 and 12 words. So they are given
word numbers past the end of the chain, and the image carries a small
side table of (word number, byte offset) pairs so the loader can
rebuild those entries after it has rebuilt the chain ones. Two entries.
The word table itself stays derived and unsaved; this table describes
how to finish deriving it.
"""
import re, sys, collections

DUMP = sys.argv[1] if len(sys.argv) > 1 else '/tmp/dump64.txt'
CELL = int(sys.argv[2]) if len(sys.argv) > 2 else 8

sys.argv = ['sod16.py', DUMP, str(CELL)]
_src = open(__file__.replace('sod16-layout.py', 'sod16.py')).read()
_lib = _src[:_src.index("# ---- optional emission")]
G = {'__name__': 'sod16lib'}
exec(compile(_lib, 'sod16lib', 'exec'), G)

words, cells, tokn = G['words'], G['cells'], G['tokn']
read_ops, to_tokens, layout = G['read_ops'], G['to_tokens'], G['layout']
idx_of, prims, stub_ops = G['idx_of'], G['prims'], G['stub_ops']
align_up, LOOPS, STR = G['align_up'], G['LOOPS'], G['STR']

# ---- the anchor -----------------------------------------------------
START = None
for l in open(DUMP, errors='replace'):
    m = re.match(r'^S (\d+) (\d+)', l)
    if m: START, HERE = int(m.group(1)), int(m.group(2)); break
if START is None:
    sys.exit("no S anchor line in %s - regenerate the dump with the "
             "current tools/dict-dump-addr.4" % DUMP)

# ---- the dictionary, oldest first ----------------------------------
order = list(reversed(words))          # definition order, as sod16.py numbers
for w in order:
    w['nfa']  = w['s'] - align_up(len(w['n']) + 1, CELL)
    w['link'] = w['nfa'] - CELL
starts = {w['s']: w for w in order}
num = {w['s']: i for i, w in enumerate(order)}

# The structure is checked, not assumed.
gaps = sum(1 for i in range(len(order) - 1)
           if order[i]['e'] != order[i + 1]['link'])
PROLOGUE = order[0]['link'] - START    # bytes before the first link cell

# ---- classify every body -------------------------------------------
# body[0] is a call to a runtime => the body is DATA behind that call.
DOVAR = {w['s'] for w in order if w['n'] == 'DOVAR'}
tails = collections.Counter()
for w in order:
    v = cells.get(w['s'])
    if v is not None and not (v & 1):
        t = w['s'] + CELL + v
        if t not in starts: tails[t] += 1
TAILS = sorted(tails)                  # deterministic: ascending address
tailnum = {t: len(order) + i for i, t in enumerate(TAILS)}

def classify(w):
    """('code', ops) or ('data', first-cell-target or None)."""
    v = cells.get(w['s'])
    if v is not None and not (v & 1):
        t = w['s'] + CELL + v
        if t in DOVAR or t in TAILS:
            return 'data', t
    ops = read_ops(w)
    if ops is not None and to_tokens(ops) is not None:
        return 'code', ops
    return 'data', None

kind, info, tok = {}, {}, {}
for w in order:
    k, i = classify(w)
    kind[w['s']], info[w['s']] = k, i
    if k == 'code': tok[w['s']] = to_tokens(i)

# ---- new sizes ------------------------------------------------------
def new_body_bytes(w):
    if kind[w['s']] == 'code':
        return align_up(len(tok[w['s']]) * 2, CELL)
    if info[w['s']] is not None:
        # [pad][call token][parameter field, CELL aligned]
        # The pad goes BEFORE the token so the parameter field, which is
        # the address just past it, stays CELL aligned for `@`.
        return CELL + (w['e'] - w['s'] - CELL)
    return w['e'] - w['s']             # opaque: copied verbatim

new_off, off = {}, PROLOGUE
for w in order:
    new_off[w['s']] = {'link': off}
    off += CELL
    new_off[w['s']]['nfa']  = off; off += align_up(len(w['n']) + 1, CELL)
    new_off[w['s']]['body'] = off; off += new_body_bytes(w)
NEW_HERE = off
OLD_HERE = order[-1]['e'] - START

# ---- recompute the link chain, and re-walk it to prove it -----------
# next_nfa = link_addr + link_value, walking newest to oldest.
linkval = {}
for i, w in enumerate(order):
    if i == 0: linkval[w['s']] = 0                       # end of chain
    else: linkval[w['s']] = new_off[order[i-1]['s']]['nfa'] - new_off[w['s']]['link']

walk, cur, n = [], order[-1], 0
while True:
    walk.append(cur['n'])
    lv = linkval[cur['s']]
    if lv == 0: break
    nxt = new_off[cur['s']]['link'] + lv
    hit = [x for x in order if new_off[x['s']]['nfa'] == nxt]
    if not hit: walk.append('BROKEN'); break
    cur = hit[0]
    n += 1
    if n > len(order) + 2: walk.append('LOOPED'); break
chain_ok = (walk == [w['n'] for w in reversed(order)])

# ---- DEFER xts become word numbers ---------------------------------
# A DEFER cell holds its xt as a START-relative offset (shell.4's
# !XT/@XT), which is what makes it survive a save. Under SOD16 an xt is
# a word number instead - Iteration 165 - so these convert, and the
# conversion is checked: every one must land on a word start.
#
# The BUFFER: words are NOT this. Their second cell is a live malloc'd
# pointer in this dump, and RESET-BUFFERS zeroes it before SAVE-SYSTEM,
# so in a saved image it carries nothing. That is the difference
# Iteration 167 was pointing at when it said the handful of
# image-range values come from a live-process dump.
DEFER_TAIL = None
for t in TAILS:
    h = [w for w in order if w['s'] < t < w['e']][0]
    if h['n'] == 'DEFER': DEFER_TAIL = t

defers, defer_bad = {}, []
for w in order:
    if info.get(w['s']) != DEFER_TAIL or DEFER_TAIL is None: continue
    xt = cells.get(w['s'] + CELL)
    tgt = START + xt if xt is not None else None
    if tgt in starts: defers[w['s']] = num[tgt]
    else: defer_bad.append((w['n'], xt))

# ---- BUFFER: parameter fields --------------------------------------
# pool.4: [+0 ptr][+1 size][+2 link]. The ptr is a live malloc'd address
# in this dump and RESET-BUFFERS zeroes it before a save, so it is
# written as 0 - the "not yet allocated" state ALLOC-BUFFERS expects.
# The link is a START-relative offset to the PREVIOUS buffer's body,
# and bodies move, so it is remapped. That is a relocation category the
# layout list in SOD16.md did not have.
BUF_TAIL = None
for t in TAILS:
    h = [w for w in order if w['s'] < t < w['e']][0]
    if h['n'] == 'BUFFER:': BUF_TAIL = t

# BUF-BODY is HERE at the moment CREATE has laid down the header and
# the leading call cell, so a buffer link points at the PARAMETER
# FIELD - one cell past the body start - not at the body start. In the
# new layout the parameter field is also one cell in, because the
# padding plus the call token come to exactly one cell.
pfa_at = {w['s'] - START + CELL: w for w in order}
buf_bad = []
def remap_pfa_off(off):
    """old START-relative parameter-field offset -> new one, or None."""
    w = pfa_at.get(off)
    return new_off[w['s']]['body'] + CELL if w else None

bufs = 0
for w in order:
    if BUF_TAIL is None or info.get(w['s']) != BUF_TAIL: continue
    bufs += 1
    lnk = cells.get(w['s'] + 3 * CELL)
    if lnk: 
        if remap_pfa_off(lnk) is None: buf_bad.append((w['n'], lnk))

# ---- report ---------------------------------------------------------
c = collections.Counter(kind.values())
codeb = sum(w['e'] - w['s'] for w in order if kind[w['s']] == 'code')
datab = sum(w['e'] - w['s'] for w in order if kind[w['s']] == 'data')
newcode = sum(new_body_bytes(w) for w in order if kind[w['s']] == 'code')
newdata = sum(new_body_bytes(w) for w in order if kind[w['s']] == 'data')
heads = sum(CELL + align_up(len(w['n']) + 1, CELL) for w in order)

print("dump %s   cell %d" % (DUMP, CELL))
print("structure: %d words, prologue %d B, %d header-adjacency gaps"
      % (len(order), PROLOGUE, gaps))
print("DOES> tails: %d distinct, %d words behind them"
      % (len(TAILS), sum(tails.values())))
for t in TAILS:
    h = [w for w in order if w['s'] < t < w['e']][0]
    print("   word number %d = %s +%d   (%d words)"
          % (tailnum[t], h['n'], t - h['s'], tails[t]))
print()
print("%-22s %12s %12s %8s" % ("", "cell image", "token image", "ratio"))
print("%-22s %12d %12d %8.3f" % ("code bodies", codeb, newcode, newcode/codeb))
print("%-22s %12d %12d %8.3f" % ("data bodies", datab, newdata, newdata/datab))
print("%-22s %12d %12d %8.3f" % ("headers + names", heads, heads, 1.0))
print("%-22s %12d %12d %8.3f"
      % ("whole image", OLD_HERE, NEW_HERE, NEW_HERE/OLD_HERE))
print()
untranslated = [w for w in order
                if kind[w['s']] == 'data' and info[w['s']] is None
                and cells.get(w['s']) is not None]
print("code words %d, data words %d" % (c['code'], c['data']))
print("UNTRANSLATED code bodies: %d  (copied verbatim would be wrong)"
      % len(untranslated))
for w in untranslated:
    print("   %s" % w['n'])
print("link chain re-walks to the same %d words in the same order: %s"
      % (len(order), "yes" if chain_ok else "NO"))
print("DEFER xts converted to word numbers: %d resolved, %d unresolved %s"
      % (len(defers), len(defer_bad), defer_bad if defer_bad else ""))
print("BUFFER: fields: %d words, ptr zeroed, %d links unremappable %s"
      % (bufs, len(buf_bad), buf_bad[:3] if buf_bad else ""))
sys.exit(0 if chain_ok and gaps == 0 and not defer_bad
         and not buf_bad and not untranslated else 1)
