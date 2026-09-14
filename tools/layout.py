#!/usr/bin/env python3
"""
tools/layout.py - the layout pass: place every word, then re-encode.

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

ARGV = list(sys.argv)          # sod16.py's argv is faked below; keep ours
DUMP = sys.argv[1] if len(sys.argv) > 1 else '/tmp/dump64.txt'
CELL = int(sys.argv[2]) if len(sys.argv) > 2 else 8

sys.argv = ['sod16.py', DUMP, str(CELL)]
_src = open(__file__.replace('layout.py', 'sod16.py')).read()
_lib = _src[:_src.index("# ---- optional emission")]
G = {'__name__': 'sod16lib'}
exec(compile(_lib, 'sod16lib', 'exec'), G)

# Encoding options, parsed BEFORE any body is classified, because they
# change what read_ops() returns and so the size of every body.
def _opt(name, default=None):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default
CPT = int(_opt('--cpt')) if '--cpt' in ARGV else None   # scale shift S
DATAPRIMS = '--dataprims' in ARGV
if '--fold' in ARGV: G['FOLD'] = True
if '--fold-set' in ARGV: G['FOLDSET'] = set(_opt('--fold-set').split(','))
if CPT is not None and CPT > 1: G['ALIGN_TAILS'] = 1 << CPT
V8 = '--v8' in ARGV
if V8:
    G['V8'] = True
    G['V8_FOLDLIST'] = _opt('--fold-set', '').split(',')

# --bytehdr: byte-granular dictionary headers. The link is 1-3 bytes with
# its tag byte LAST (read backward from the nfa), names are not padded,
# code bodies are not padded at the end, and the call scale is 0. Only
# bodies that hold cell-sized things - data words, and code with inline
# cell operands or a builtin tail - get their START aligned. This needs
# the cv8b.4 overlay in the image, since the kernel's own SEARCH-WORDLIST
# and NAME> assume a cell link and an aligned name.
BYTEHDR = '--bytehdr' in ARGV
if BYTEHDR and not (V8 and CPT == 0):
    sys.exit("--bytehdr requires --v8 --cpt 0")


def linklen(d):
    return 1 if d < 128 else (2 if d < 16384 else 3)


def linkbytes(d, n):
    if n == 1: return bytes([d])
    if n == 2: return bytes([d & 0xFF, 0x80 | (d >> 8)])
    return bytes([d & 0xFF, (d >> 8) & 0xFF, 0xC0 | (d >> 16)])
if '--spec' in ARGV: G['SPEC'].update(_opt('--spec').split(','))
if '--escape' in ARGV:
    G['ESCAPE'] = True
    G['ESC_PRIMS'].update(G['ESC_PRIMS_ALL'])
if '--no-varcall' in ARGV: G['VARCALL'] = False
if '--no-varslot' in ARGV: G['VARSLOT'] = False
UB = 1 if V8 else 2                # bytes per stream unit
DOVARP = len(G['prims']) + 1       # after LIT32
DODOES = len(G['prims']) + 2

# --- phase 3: swap the CV8 compiler words in (cv8.4) -----------------
# cv8.4 defines its words as `;8`, `IF8`, ... because redefining `;` in
# the CELL image would break the cell compiler on the very next
# definition. Here the body of each `X8` becomes the body of `X`, so the
# emitted image's compiler emits CV8. The `X8` names stay, harmlessly.
# The suffix is a parameter, not a constant: every stage that emits its
# own encoding ships an overlay using the same trick with a different
# suffix (cv8.4 uses '8', cpt16.4 uses '16').
if '--compiler-overlay' in ARGV:
    OVERLAY_SUFFIX = ARGV[ARGV.index('--compiler-overlay') + 1]
elif '--cv8-compiler' in ARGV:
    OVERLAY_SUFFIX = '8'
else:
    OVERLAY_SUFFIX = None
CV8_COMPILER = OVERLAY_SUFFIX is not None
SRC_OF = {}          # destination word start -> source word start

words, cells, tokn = G['words'], G['cells'], G['tokn']
read_ops, to_tokens, layout = G['read_ops'], G['to_tokens'], G['layout']
retag = G['retag']
idx_of, prims, stub_ops = G['idx_of'], G['prims'], G['stub_ops']
align_up, LOOPS, STR = G['align_up'], G['LOOPS'], G['STR']
code_end = G['code_end']

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

if CV8_COMPILER:
    # `X8` body becomes `X`'s body, so the image's compiler emits CV8.
    _by = {}
    for w in order:
        _by.setdefault(w['n'], []).append(w)
    _n, _miss, _unmatched = 0, [], []
    for w in order:
        if (len(w['n']) <= len(OVERLAY_SUFFIX)
                or not w['n'].endswith(OVERLAY_SUFFIX)): continue
        tgt = w['n'][:-len(OVERLAY_SUFFIX)]
        if tgt not in _by:
            _unmatched.append(w['n']); continue
        dst = _by[tgt][-1]
        if kind[w['s']] != 'code' or info[w['s']] is None:
            _miss.append(w['n']); continue
        kind[dst['s']], info[dst['s']] = 'code', list(info[w['s']])
        # A swapped body's operand offsets are relative to the SOURCE
        # word's old address, so anything that resolves an inline
        # address must use that base, not the destination's.
        SRC_OF[dst['s']] = w['s']
        _n += 1
    print("compiler overlay '%s': %d word bodies swapped in%s%s"
          % (OVERLAY_SUFFIX, _n, "; NOT translatable: %s" % _miss if _miss else "",
             "; no such target: %s" % _unmatched if _unmatched else ""))

if not V8:
    for w in order:
        if kind[w['s']] == 'code': tok[w['s']] = to_tokens(info[w['s']])
# In V8 the token stream is sized INSIDE the placement walk instead -
# see `size_here` below. Sizing everything first, as this did, meant no
# word had an address yet, so every call was assumed to be the 2-byte
# near form. At a call scale of 3 that guess is always right (the 14-bit
# field reaches 131 KB); at scale 0 it reaches 16 KB, and a 70 KB image
# has targets past it, so bodies came out longer than the space
# reserved for them - "body size drift".

# ---- new sizes ------------------------------------------------------
def tail_bytes(w):
    """Unheadered data compiled after this word's code - see code_end.

    A PRIMITIVE stub is read by shape, not by walking, so code_end does
    not apply to it and would report its second cell as a tail."""
    if kind[w['s']] != 'code' or stub_ops(w) is not None: return 0
    return w['e'] - code_end(w)

def body_needs_align(w):
    """In bytehdr mode only these bodies start on a cell boundary."""
    if kind[w['s']] != 'code': return True
    if tail_bytes(w): return True
    return any(k in ('OPD', 'XT', 'STR', 'ALN') for k, _ in (info[w['s']] or []))


def new_body_bytes(w):
    if kind[w['s']] == 'code':
        if BYTEHDR:
            # A TAIL is unheadered data - the BUILTIN table is the one
            # that matters - and it is read with `@`, so its entries
            # must be cell-aligned. Byte headers drop the padding that
            # used to guarantee that for free, so the code in front of
            # a tail is still padded up to a cell. Without this the
            # table lands at an odd offset and FIND-BUILTIN fetches a
            # cell across a boundary: the low 48 bits of the pointer
            # are right and the top two bytes are the neighbours.
            if tail_bytes(w):
                return align_up(len(tok[w['s']]) * UB, CELL) + tail_bytes(w)
            return len(tok[w['s']]) * UB
        return align_up(len(tok[w['s']]) * UB, CELL) + tail_bytes(w)
    if info[w['s']] is not None:
        # [pad][call token][parameter field, CELL aligned]
        # The pad goes BEFORE the token so the parameter field, which is
        # the address just past it, stays CELL aligned for `@`.
        return CELL + (w['e'] - w['s'] - CELL)
    return w['e'] - w['s']             # opaque: copied verbatim

# The thread each word belongs to, needed BEFORE placement in bytehdr
# mode: a link's length depends on its distance, and its distance is to
# the previous word in the same thread. Hashing needs only the name and
# the thread count, both known now.
_FW = [w for w in order if w['n'] == 'FORTH-WORDLIST']
if not _FW:
    sys.exit("no FORTH-WORDLIST in the dump")
_NTH = cells.get(_FW[0]['s'] + CELL, 0)
if not (1 <= _NTH <= 4096):
    sys.exit("FORTH-WORDLIST declares %r threads" % _NTH)


def _wl_hash(name):
    b = name.encode('latin-1')
    v = len(b) ^ (b[0] << 1)
    if len(b) > 1:
        v ^= b[1] << 2
    return v & (_NTH - 1)


_prev_in_thread, _last = {}, {}
for w in order:
    h = _wl_hash(w['n'])
    _prev_in_thread[w['s']] = _last.get(h)
    _last[h] = w['s']

_MIDBODY = [False]


def _placed_val(target):
    """Scaled call value for an ALREADY PLACED target, or None.

    Mirrors new_target_off, which cannot be used here because it is
    defined after the emission helpers. The two must agree: this decides
    how many bytes a call occupies, that one decides what goes in them."""
    if target in new_off and 'body' in new_off[target]:
        # SKIPPAD is set further down the file, so it is read lazily
        # rather than captured - this runs before that line.
        if (globals().get('SKIPPAD') and not DATAPRIMS
                and kind[target] == 'data' and info[target] is not None):
            return (new_off[target]['body'] + CELL - 2) >> CPT
        return new_off[target]['body'] >> CPT
    # A target INSIDE a body, not at its start. new_target_off resolves
    # these through layout(); so must this, or every one of them gets
    # pinned to the far form and the image grows for no reason.
    if _MIDBODY[0]:
        return None          # see below
    for h in order:
        if h['s'] < target < h['e']:
            if h['s'] not in new_off or 'body' not in new_off[h['s']]:
                return None                      # container not placed yet
            # layout() re-enters calltok_len, which re-enters this
            # function. One level is all that is ever needed; deeper
            # than that, pin rather than risk unbounded recursion.
            _MIDBODY[0] = True
            try:
                c2t_ = layout(info[h['s']])[0]
            finally:
                _MIDBODY[0] = False
            if (target - h['s']) not in c2t_:
                return None
            return (new_off[h['s']]['body'] + c2t_[target - h['s']]) >> CPT
    return None


def _pfa_val(target):
    """Scaled parameter-field value for an already placed data word."""
    if target in new_off and 'body' in new_off[target]:
        return (new_off[target]['body'] + CELL) >> CPT
    return None


def size_here(w):
    """Tokenise one word against the words placed before it.

    Every backward call - 98% of them - gets its exact offset, so its
    width is known rather than guessed. A forward reference has no
    offset yet, so it is pinned to the 3-byte form and stays pinned at
    emission."""
    if kind[w['s']] != 'code' or info[w['s']] is None:
        return
    for o in info[w['s']]:
        k = o[0] if isinstance(o, (tuple, list)) else o
        if k == 'C':
            if _placed_val(o[1]) is None:
                G['V8_FORCE3'].add(o[1])
        elif k in ('VF', 'VS'):
            if _pfa_val(o[1]) is None:
                G['V8_FORCE4'].add((k, o[1]))
        elif k == 'LOC':
            # A LOC slot resolves through remap_pfa_off/remap_body_off,
            # neither of which exists yet. Pin it: 926 of them in the
            # shell image, so a byte each, against a layout that
            # otherwise cannot be sized at all.
            G['V8_FORCE4'].add((k, o[1]))
    G['V8_CALLTOK'][0] = lambda tg: (_placed_val(tg) or 0)
    G['V8_PFA'][0] = lambda tg: _pfa_val(tg)
    tok[w['s']] = to_tokens(info[w['s']])
    G['V8_CALLTOK'][0] = None
    G['V8_PFA'][0] = None


new_off, off = {}, PROLOGUE
LINKLEN = {}
for w in order:
    if V8: size_here(w)
    if BYTEHDR:
        pv = _prev_in_thread[w['s']]
        # Bound from above: the nfa lands at most 3 bytes past `off`, so
        # a link sized for that distance always fits the real one.
        ll = 1 if pv is None else linklen(off + 3 - new_off[pv]['nfa'])
        LINKLEN[w['s']] = ll
        new_off[w['s']] = {'link': off}; off += ll
        new_off[w['s']]['nfa'] = off;   off += len(w['n']) + 1
        if body_needs_align(w): off = align_up(off, CELL)
        new_off[w['s']]['body'] = off;  off += new_body_bytes(w)
    else:
        new_off[w['s']] = {'link': off}
        off += CELL
        new_off[w['s']]['nfa']  = off; off += align_up(len(w['n']) + 1, CELL)
        new_off[w['s']]['body'] = off; off += new_body_bytes(w)
NEW_HERE = off
OLD_HERE = order[-1]['e'] - START

# ---- recompute the link chains, and re-walk them to prove it --------
# The word list is HASHED: as many chains as there are threads, each
# linked newest to oldest. The thread count is read out of the image
# being translated rather than assumed, so this file has no opinion
# about it and cannot disagree with kernel.4.
FW = [w for w in order if w['n'] == 'FORTH-WORDLIST']
if not FW:
    sys.exit("no FORTH-WORDLIST in the dump")
FW = FW[0]
FW_PF = FW['s'] + CELL                       # parameter field: [n][heads]
NTHREADS = cells.get(FW_PF, 0)
if not (1 <= NTHREADS <= 4096):
    sys.exit("FORTH-WORDLIST declares %r threads" % NTHREADS)


def wl_hash(name):
    """kernel.4's HASH, and cross.4's THASH. All three must agree."""
    b = name.encode('latin-1')
    v = len(b) ^ (b[0] << 1)
    if len(b) > 1:
        v ^= b[1] << 2
    return v & (NTHREADS - 1)


# Definition order within each thread; `order` is already oldest first.
threads = [[] for _ in range(NTHREADS)]
for w in order:
    threads[wl_hash(w['n'])].append(w)

linkval = {}
for t in threads:
    for i, w in enumerate(t):
        if i == 0:
            linkval[w['s']] = 0                          # end of chain
        elif BYTEHDR:
            # a DISTANCE backward from this nfa, always positive
            linkval[w['s']] = (new_off[w['s']]['nfa']
                               - new_off[t[i - 1]['s']]['nfa'])
            assert linkval[w['s']] < (1 << LINKLEN[w['s']] * 7 + (1 if LINKLEN[w['s']] > 1 else 0)), \
                "link does not fit at %s" % w['n']
        else:
            linkval[w['s']] = (new_off[t[i - 1]['s']]['nfa']
                               - new_off[w['s']]['link'])

# The heads, as offsets from START, which is how the image stores them
# and what COLD relocates. An empty thread stays 0.
HEADS = [new_off[t[-1]['s']]['nfa'] if t else 0 for t in threads]

# Walk every chain back and check the union is exactly the dictionary.
by_nfa = {new_off[w['s']]['nfa']: w for w in order}
seen_names, broken = [], False
for t, head in zip(threads, HEADS):
    if not head:
        continue
    cur, n = by_nfa[head], 0
    while True:
        seen_names.append(cur['n'])
        lv = linkval[cur['s']]
        if lv == 0:
            break
        nxt = by_nfa.get(new_off[cur['s']]['nfa'] - lv if BYTEHDR
                         else new_off[cur['s']]['link'] + lv)
        if nxt is None:
            broken = True
            break
        cur = nxt
        n += 1
        if n > len(order) + 2:
            broken = True
            break
chain_ok = (not broken
            and sorted(seen_names) == sorted(w['n'] for w in order))

# The heads live in FORTH-WORDLIST's own parameter field, which is DATA
# and would otherwise be copied out of the dump verbatim - with the
# addresses of the image we were translating FROM. Overwrite them.
for i, h in enumerate(HEADS):
    cells[FW_PF + (i + 1) * CELL] = h

# ---- xts are ADDRESSES, and get relocated --------------------------
# Iteration 176. `: EXECUTE ( xt --- ) >R ;` is pure Forth, not a
# primitive: it makes the xt the return address, and EXIT jumps to it.
# So an xt has to be an executable address in either engine. A CALL
# TOKEN is a word number; an XT is an address. Iteration 165 conflated
# them, and 175 refused (POSTPONE) on the strength of that.
#
# Nothing here converts an xt to a word number. Everything here moves
# an offset to where its target landed.
body_at = {w['s'] - START: w for w in order}

def remap_body_off(off):
    w = body_at.get(off)
    return new_off[w['s']]['body'] if w else None

# (POSTPONE)'s inline operand: a relative address from the operand cell
# to another word's body. sod16.py passes it through because a per-word
# translator cannot see where other words land.
xt_ok, xt_bad, xt_new = 0, [], {}
for w in order:
    if kind[w['s']] != 'code': continue
    ops = info[w['s']]
    _, cs, ts, _, _ = layout(ops)
    for j, (k, pl) in enumerate(ops):
        if k != 'XT': continue
        tgt = (SRC_OF.get(w['s'], w['s']) + cs[j]) + pl - START
        n2 = remap_body_off(tgt)
        if n2 is None: xt_bad.append((w['n'], tgt))
        else:
            xt_ok += 1
            # RELOCATE it, do not merely count it: the operand is a byte
            # offset from its own cell to the target's body, and both
            # move. Until Iteration 196 the old value was passed through
            # and only checked, which no translated image ever noticed -
            # nothing in one COMPILES, so (POSTPONE) never ran. It runs
            # as soon as the image has its own compiler (cv8.4).
            xt_new[(w['s'], j)] = n2 - (new_off[w['s']]['body'] + ts[j])

# ---- DEFER xts -----------------------------------------------------
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

# A DEFER cell holds a START-relative offset to a word body (shell.4's
# !XT/@XT). It stays an offset; it just points somewhere else now.
defers, defer_bad = {}, []
for w in order:
    if info.get(w['s']) != DEFER_TAIL or DEFER_TAIL is None: continue
    xt = cells.get(w['s'] + CELL)
    new = remap_body_off(xt) if xt is not None else None
    if new is not None: defers[w['s']] = new
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

# ---- the BUILTIN table ---------------------------------------------
# shell.4 compiles its builtin table at HERE between definitions, so
# the entries have no headers and land inside the previous word's tail
# (see code_end). Each is [link][xt][len][name], and BOTH the link and
# the xt are START-relative offsets into an image whose bodies have all
# moved. BUILTIN-LIST holds the head, also as an offset.
#
# The entries move as a block with the tail that contains them, so a
# new offset is the tail's new position plus the same distance in.
tail_start = {}          # old address of a code word's tail
for w in order:
    if tail_bytes(w):
        tail_start[w['s']] = code_end(w)

def remap_tail_addr(addr):
    """old absolute address inside some tail -> new image offset."""
    for s0, ts_ in tail_start.items():
        w = starts[s0]
        if ts_ <= addr < w['e']:
            head = align_up(len(tok[s0]) * UB, CELL)
            return new_off[s0]['body'] + head + (addr - ts_)
    return None

BL = [w for w in order if w['n'] == 'BUILTIN-LIST']
builtins, bi_bad = 0, []
if BL:
    head = cells.get(BL[0]['s'] + CELL)          # parameter field
    o = head
    seen = set()
    while o and o not in seen:
        seen.add(o)
        a = START + o
        if remap_tail_addr(a) is None: bi_bad.append(('entry', o)); break
        xt = cells.get(a + CELL)
        if remap_body_off(xt) is None: bi_bad.append(('xt', o, xt))
        builtins += 1
        o = cells.get(a)                          # link to previous
    if remap_tail_addr(START + head) is None: bi_bad.append(('head', head))

# ---- the four remaining offset cells --------------------------------
# save-system.4 enumerates these, so they do not have to be guessed.
# SS-UNRELOCATE: "COLD is the authority on which cells these are, and
# there are exactly two: DP and FORTH-WORDLIST." SET-BOOT adds BOOT,
# and pool.4 adds BUF-LIST. Everything else that holds an offset is
# either scrubbed by SS-SCRUB or is one of the categories above.
#
# DP and FORTH-WORDLIST are ABSOLUTE in a live dump, because COLD added
# START to them at boot, and are written back as offsets. BOOT and
# BUF-LIST are offsets at rest.
def pfa_of(name):
    w = [x for x in order if x['n'] == name]
    return w[0]['s'] + CELL if w else None

fixed, fixed_bad = {}, []
_dp = pfa_of('DP')
if _dp: fixed['DP'] = NEW_HERE
_fw = pfa_of('FORTH-WORDLIST')
# The first cell of the word list is the THREAD COUNT, not a chain head.
# It used to be the head, and this line still forced it to the newest
# word's nfa - so a translated image began its boot relocation loop with
# `<address> 1 DO`, which counts up to 2^64. The image hung before it
# printed its banner. The heads themselves are patched into `cells`
# where the threads are computed.
if _fw: fixed['FORTH-WORDLIST'] = NTHREADS
_bt = pfa_of('BOOT')
if _bt:
    v = cells.get(_bt)
    # The dump session never runs SET-BOOT, so BOOT is 0 and the image
    # comes up at the Forth interpreter. Point it at MAIN so the image
    # is turnkey, which is what relfsh's image is: otherwise the only
    # way in is to type MAIN, and that eats the stdin a shell script
    # needs.
    _main = [x for x in order if x['n'] == 'MAIN']
    if not v and _main: fixed['BOOT'] = new_off[_main[0]['s']]['body']
    elif not v: fixed['BOOT'] = 0
    elif remap_body_off(v) is not None: fixed['BOOT'] = remap_body_off(v)
    else: fixed_bad.append(('BOOT', v))
_bl = pfa_of('BUF-LIST')
if _bl:
    v = cells.get(_bl)
    if not v: fixed['BUF-LIST'] = 0
    elif remap_pfa_off(v) is not None: fixed['BUF-LIST'] = remap_pfa_off(v)
    else: fixed_bad.append(('BUF-LIST', v))
if BL:
    h = cells.get(BL[0]['s'] + CELL)
    if h: fixed['BUILTIN-LIST'] = remap_tail_addr(START + h)

def tk(v): return (v & 0xFFFF).to_bytes(2, 'little')

# ---- CPT16: call tokens are scaled image offsets, not word numbers ---
SKIPPAD = '--skip-pad' in ARGV
def new_target_off(target):
    """old absolute call-target address -> new image offset."""
    if target in new_off:
        # A data body is [NOOP pad][call token][parameter field]. The pad
        # exists only to align the parameter field; a call may land on
        # the token itself and skip executing the NOOPs.
        if (SKIPPAD and not DATAPRIMS and kind[target] == 'data'
                and info[target] is not None):
            return new_off[target]['body'] + CELL - 2
        return new_off[target]['body']
    h = [x for x in order if x['s'] < target < x['e']][0]
    c2t_, _, _, _, _ = layout(info[h['s']])
    return new_off[h['s']]['body'] + c2t_[target - h['s']]
def calltok_addr(target):
    if CPT is None:
        return 256 + (num[target] if target in num else tailnum[target])
    off = new_target_off(target)
    assert off % (1 << CPT) == 0, "call target %d not %d-aligned" % (off, 1 << CPT)
    v = 256 + (off >> CPT)
    assert v <= 0xFFFF, "call target offset %d beyond CPT16 reach" % off
    return v
if CPT is not None:
    G['G_CALLTOK'][0] = lambda target, n: calltok_addr(target)
def v8val(target):
    off = new_target_off(target)
    assert off % (1 << CPT) == 0, "v8 call target %d not aligned" % off
    return off >> CPT
if V8: G['V8_CALLTOK'][0] = v8val
def v8pfa(target):
    off = new_off[target]['body'] + CELL          # [DOVAR][pad] is one cell
    assert off % (1 << CPT) == 0 and (off >> CPT) < (1 << 23)
    return off >> CPT
def v8loc(old):
    n2 = remap_pfa_off(old)
    if n2 is None: n2 = remap_body_off(old)
    assert n2 is not None and n2 % (1 << CPT) == 0, old
    assert (n2 >> CPT) < (1 << 23), "locals slot %d beyond 23-bit reach" % n2
    return n2 >> CPT
G['V8_PFA'][0] = v8pfa
G['V8_LOC'][0] = v8loc
def callbytes(target):
    if V8:
        v = v8val(target)
        if G['VARCALL']:
            if v < (1 << 14): return bytes([0x80 | (v >> 8), v & 0xFF])
            return bytes([0xC0 | (v >> 16), (v >> 8) & 0xFF, v & 0xFF])
        return bytes([0x80 | (v >> 8), v & 0xFF])
    return tk(calltok_addr(target))

# ---- emit the token image -------------------------------------------
def emit(path):
    """Write the token image. Layout and values all come from above."""
    # Name flag bytes and prologue cells come from the dump's H and P
    # lines; DUMP itself masks the flags off and never walks the
    # prologue, so both were added in Iteration 174.
    flag, pro = {}, {}
    for l in open(DUMP, errors='replace'):
        m = re.match(r'^H (\d+) (\d+)', l)
        if m: flag[int(m.group(1))] = int(m.group(2)) & 0xFF
        m = re.match(r'^P (\d+) (-?\d+)', l)
        if m: pro[int(m.group(1))] = int(m.group(2))

    M = (1 << (8 * CELL)) - 1
    def cel(v): return (v & M).to_bytes(CELL, 'little')
    def tk(v):  return (v & 0xFFFF).to_bytes(2, 'little')

    img = bytearray()
    # Prologue. The first two cells are calls - ip = base starts here -
    # and become call tokens. The remaining cells are kept at their own
    # cell positions, so the region keeps its size and the first link
    # cell stays where the layout expects it.
    for i in (0, 1):
        v = pro[START + i * CELL]
        img += callbytes(START + i * CELL + CELL + v)
    while len(img) < PROLOGUE - 3 * CELL: img += b'\x00'
    for i in (2, 3, 4): img += cel(pro[START + i * CELL])
    assert len(img) == PROLOGUE, "prologue emitted %d, expected %d" % (len(img), PROLOGUE)

    # Builtin entries: old address -> new image offset, for the links.
    bi_new = {START + o: remap_tail_addr(START + o) for o in seen} if BL else {}

    for w in order:
        s0 = w['s']
        assert len(img) == new_off[s0]['link'], "link drift at %s" % w['n']
        if BYTEHDR: img += linkbytes(linkval[s0], LINKLEN[s0])
        else:       img += cel(linkval[s0])
        nm = w['n'].encode('latin-1')
        img += bytes([flag.get(w['nfa'], 0x80 | len(nm))]) + nm
        # pad to the body: a cell boundary in the classic layout, or only
        # as far as body_needs_align() asked for in the byte layout
        while len(img) < new_off[s0]['body']: img += b'\x00'
        assert len(img) == new_off[s0]['body'], "body drift at %s" % w['n']

        if kind[s0] == 'code':
            # Re-encode with the relocated locals-slot literals. Safe to
            # do after the layout was computed because a LITOFF is
            # always the 32-bit form, so its size does not depend on its
            # value; the assertion below is what proves that held.
            ops2 = list(info[s0])
            for (ws, j), nv in lit_new.items():
                if ws == s0: ops2[j] = ('LITOFF', nv)
            for (ws, j), nv in xt_new.items():
                if ws == s0: ops2[j] = ('XT', nv)
            if V8: img += bytes(to_tokens(ops2))
            else:
                for t_ in to_tokens(ops2): img += tk(t_)
            # Must match new_body_bytes exactly: pad when there is no
            # byte header at all, or when there is one and a tail
            # follows that needs its entries aligned.
            if not BYTEHDR or tail_bytes(w):
                while len(img) % CELL: img += b'\x00'
            # Unheadered tail, with its builtin entries relocated.
            # Derived from tail_bytes, not from code_end directly, so a
            # PRIMITIVE stub - which code_end does not apply to - cannot
            # grow a spurious tail here while the layout says it has none.
            a = w['e'] - tail_bytes(w)
            while a < w['e']:
                v = cells.get(a, 0)
                if a in bi_new:                      # [link][xt][len][name]
                    lk = cells.get(a, 0)
                    img += cel(bi_new.get(START + lk, 0) if lk else 0)
                    img += cel(remap_body_off(cells.get(a + CELL, 0)) or 0)
                    img += cel(cells.get(a + 2 * CELL, 0))
                    a += 3 * CELL
                    continue
                img += cel(v); a += CELL
        else:
            n = info[s0]
            if n is None:                            # opaque, copied whole
                a = s0
                while a < w['e']: img += cel(cells.get(a, 0)); a += CELL
            else:
                if DATAPRIMS and n in DOVAR:
                    # [DOVAR][pad][PFA]: the primitive pushes ALIGNED(ip)
                    img += (bytes([69]) + b'\x00' * (CELL - 1)) if V8 else (tk(DOVARP) + b'\x00' * (CELL - 2))
                elif DATAPRIMS:
                    # [DODOES][tail][pad][PFA]: pushes ALIGNED(ip) as the
                    # return address the tail's R> expects, jumps to tail
                    img += (bytes([70]) + callbytes(n) + b'\x00' * (CELL - 3)) if V8 else (tk(DODOES) + tk(calltok_addr(n)) + b'\x00' * (CELL - 4))
                else:
                    img += b'\x00' * (CELL - 2)     # pad BEFORE the token
                    img += tk(calltok_addr(n))
                vals = [cells.get(s0 + k * CELL, 0)
                        for k in range(1, (w['e'] - s0) // CELL)]
                if s0 in defers: vals[0] = defers[s0]
                elif n == BUF_TAIL:
                    vals[0] = 0                      # ptr, as RESET-BUFFERS
                    if len(vals) > 2 and vals[2]:
                        vals[2] = remap_pfa_off(vals[2])
                elif w['n'] in fixed: vals[0] = fixed[w['n']]
                for v in vals: img += cel(v)
        assert len(img) == new_off[s0]['body'] + new_body_bytes(w), \
            "body size drift at %s" % w['n']

    assert len(img) == NEW_HERE, "image %d, layout said %d" % (len(img), NEW_HERE)

    _flags = ((1 if G['VARCALL'] else 0) | (2 if G['VARSLOT'] else 0)
              | (4 if G['SPEC'] else 0) | 8 | (16 if BYTEHDR else 0)) if V8 else 0
    hdr = (b'SOD1' if CPT is None else (b'CV8' if V8 else b'CPT') + bytes([48 + CPT]))
    hdr += bytes([CELL, ord('L') if G['SPEC'] else 0, 1 if V8 else 0, _flags])
    # The engine cannot derive the word table from one chain any more,
    # so the header carries every thread head: a count, then that many
    # START-relative offsets. SOD16 needs them to number its calls; the
    # other encodings name a call by address and ignore this entirely.
    hdr += cel(NTHREADS)
    for h in HEADS:
        hdr += cel(h)
    hdr += cel(len(TAILS))
    for t in TAILS:
        h = [x for x in order if x['s'] < t < x['e']][0]
        c2t_, _, _, _, _ = layout(info[h['s']])
        hdr += cel(num[h['s']]) + cel(c2t_[t - h['s']])
    # SPEC images always carry the 5-cell locals header, so the format
    # does not depend on what was loaded. A bare kernel has no save
    # stack: the header is zeroed, and no LOC opcode is ever emitted
    # (there are no calls to a locals runtime to rewrite).
    if G['SPEC'] and not [w for w in order if w['n'] == 'LSAVE-MAX']:
        hdr += cel(0) * 5
    if G['SPEC'] and [w for w in order if w['n'] == 'LSAVE-MAX']:
        # CV8 locals opcodes: where the save stack lives, its limit, and the
        # Forth words to fall back to. Offsets from base, one cell each.
        def body_of(n): return new_off[[w for w in order if w['n'] == n][-1]['s']]['body']
        lmax = [w for w in order if w['n'] == 'LSAVE-MAX'][-1]
        lmax_v = [pl for k, pl in info[lmax['s']] if k in ('LIT', 'LITX')][0]
        hdr += cel(body_of('LSAVE-SP') + CELL) + cel(body_of('LSAVE-STACK') + CELL)
        hdr += cel(lmax_v) + cel(body_of('LSAVE')) + cel(body_of('LRESTORE'))
    open(path, 'wb').write(hdr + bytes(img))
    return len(hdr), len(img)

# ---- literals that hold offsets -------------------------------------
# locals.4's L-EMIT: "Two cells: the offset as a literal, then a
# relative call to the runtime word, which does the + START itself."
#
# So a locals-using word's body carries LIT <offset from START to a
# slot word's body>. That is position-INDEPENDENT, which is why it
# survives a save, and it is not layout-INDEPENDENT, which is why SOD16
# has to move it: the bodies are all somewhere else now.
#
# The four runtime words are found through the variables that hold
# their xts, not by name, so renaming them cannot silently break this.
# The signature is positional, like every other operand in this file:
# a LIT is an offset only when a call to one of those four follows it.
LOCALS_RT = set()
for _n in ('L-LSAVE-XT', 'L-L!-XT', 'L-LZERO-XT', 'L-LRESTORE-XT'):
    _p = pfa_of(_n)
    if _p:
        _v = cells.get(_p)
        if _v: LOCALS_RT.add(START + _v)

lit_ok, lit_bad, lit_new = 0, [], {}
for w in order:
    if kind[w['s']] != 'code': continue
    ops = info[w['s']]
    for j in range(len(ops) - 1):
        if ops[j][0] not in ('LIT', 'LITOFF'): continue
        if ops[j + 1][0] != 'C': continue
        if ops[j + 1][1] not in LOCALS_RT: continue
        v = ops[j][1]
        n2 = remap_pfa_off(v)
        if n2 is None: n2 = remap_body_off(v)
        if n2 is None: lit_bad.append((w['n'], v))
        else: lit_ok += 1; lit_new[(w['s'], j)] = n2

# ---- report ---------------------------------------------------------
c = collections.Counter(kind.values())
codeb = sum(w['e'] - w['s'] for w in order if kind[w['s']] == 'code')
datab = sum(w['e'] - w['s'] for w in order if kind[w['s']] == 'data')
newcode = sum(new_body_bytes(w) for w in order if kind[w['s']] == 'code')
tails_kept = [(w['n'], tail_bytes(w)) for w in order if tail_bytes(w)]
newdata = sum(new_body_bytes(w) for w in order if kind[w['s']] == 'data')
heads = sum(CELL + align_up(len(w['n']) + 1, CELL) for w in order)
heads_new = (sum(LINKLEN[w['s']] + len(w['n']) + 1 for w in order)
             if BYTEHDR else heads)

EMIT = None
for i, a in enumerate(ARGV):
    if a == '--emit-image': EMIT = ARGV[i + 1]

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
print("%-22s %12d %12d %8.3f" % ("headers + names", heads, heads_new,
                                     heads_new / heads))
print("%-22s %12d %12d %8.3f"
      % ("whole image", OLD_HERE, NEW_HERE, NEW_HERE/OLD_HERE))
print()
untranslated = [w for w in order
                if kind[w['s']] == 'data' and info[w['s']] is None
                and cells.get(w['s']) is not None]
print("code words %d, data words %d" % (c['code'], c['data']))
print("UNTRANSLATED code bodies: %d  (copied verbatim would be wrong)"
      % len(untranslated))
print("unheadered tails carried after code: %s" % (tails_kept or "none"))
if tails_kept:
    print("BUILTIN table: %d entries relocated, %d unresolved %s"
          % (builtins, len(bi_bad), bi_bad[:3] if bi_bad else ""))
for w in untranslated:
    print("   %s" % w['n'])
print("link chain re-walks to the same %d words in the same order: %s"
      % (len(order), "yes" if chain_ok else "NO"))
print("(POSTPONE) operands relocated: %d resolved, %d unresolved %s"
      % (xt_ok, len(xt_bad), xt_bad[:3] if xt_bad else ""))
print("DEFER xts relocated: %d resolved, %d unresolved %s"
      % (len(defers), len(defer_bad), defer_bad if defer_bad else ""))
print("BUFFER: fields: %d words, ptr zeroed, %d links unremappable %s"
      % (bufs, len(buf_bad), buf_bad[:3] if buf_bad else ""))
print("locals slot literals relocated: %d resolved, %d unresolved %s"
      % (lit_ok, len(lit_bad), lit_bad[:3] if lit_bad else ""))
print("named offset cells: %d set, %d unresolved %s"
      % (len(fixed), len(fixed_bad), fixed_bad if fixed_bad else ""))
for k in sorted(fixed): print("   %-16s -> %d" % (k, fixed[k]))
for i, a in enumerate(ARGV):
    if a == '--symbols':
        with open(ARGV[i + 1], 'w') as f:
            for w in order:
                f.write("%d %d %s %s\n" % (new_off[w['s']]['body'],
                        new_body_bytes(w), kind[w['s']], w['n']))
if EMIT:
    h, b = emit(EMIT)
    print("wrote %s: %d B header + %d B image" % (EMIT, h, b))

sys.exit(0 if chain_ok and gaps == 0 and not defer_bad and not xt_bad
         and not buf_bad and not untranslated and not bi_bad and not fixed_bad
         and not lit_bad else 1)
