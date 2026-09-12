#!/usr/bin/env python3
"""gen-tos.py vm.c > vm-tos.c - top-of-stack caching, mechanically.
Hot primitives get hand-written TOS bodies; every other primitive is
wrapped SPILL / unchanged body / FILL, so its memory-stack view (and
SP@, DEPTH, the syscalls) is exactly what it was."""
import re, sys
s = open(sys.argv[1]).read()
HOT = {
 'L_lit':    'PUSHT(OPND16(ip)); ip += 2; NEXT();',
 'L_lit8':   'PUSHT(BYTE(ip)); ip += 1; NEXT();',
 'L_lit8x':  'PUSHT(BYTE(ip)); ip = RS; rp += CELL_BYTES; NEXT();',
 'L_drop':   'POPT(); NEXT();',
 'L_dup':    'PUSHT(tos); NEXT();',
 'L_swap':   't = NOS; NOS = tos; tos = t; NEXT();',
 'L_rot':    't = CELL(dsp + CELL_BYTES); CELL(dsp + CELL_BYTES) = NOS; NOS = tos; tos = t; NEXT();',
 'L_over':   't = NOS; PUSHT(t); NEXT();',
 'L_cfetch': 'tos = BYTE(tos); NEXT();',
 'L_fetch':  'tos = CELL(tos); NEXT();',
 'L_cstore': 'BYTE(tos) = (UNS8)NOS; tos = CELL(dsp + CELL_BYTES); dsp += 2 * CELL_BYTES; NEXT();',
 'L_store':  'CELL(tos) = NOS; tos = CELL(dsp + CELL_BYTES); dsp += 2 * CELL_BYTES; NEXT();',
 'L_and':    'tos &= NOS; dsp += CELL_BYTES; NEXT();',
 'L_or':     'tos |= NOS; dsp += CELL_BYTES; NEXT();',
 'L_xor':    'tos ^= NOS; dsp += CELL_BYTES; NEXT();',
 'L_fromr':  'PUSHT(RS); rp += CELL_BYTES; NEXT();',
 'L_tor':    'RPUSH(tos); POPT(); NEXT();',
 'L_rfetch': 'PUSHT(RS); NEXT();',
 'L_eq':     'tos = -(UNS64)(NOS == tos); dsp += CELL_BYTES; NEXT();',
 'L_ugt':    'tos = -(UNS64)(NOS < tos); dsp += CELL_BYTES; NEXT();',
 'L_gt':     'tos = -(UNS64)((INT64)NOS < (INT64)tos); dsp += CELL_BYTES; NEXT();',
 'L_plus':   'tos += NOS; dsp += CELL_BYTES; NEXT();',
 'L_negate': 'tos = -tos; NEXT();',
 'L_lshift': 'tos = NOS << tos; dsp += CELL_BYTES; NEXT();',
 'L_rshift': 'tos = NOS >> tos; dsp += CELL_BYTES; NEXT();',
 'L_dovar':  'PUSHT((ip + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1)); ip = RS; rp += CELL_BYTES; NEXT();',
 'L_lit0':   'PUSHT(0); NEXT();',
 'L_lit1':   'PUSHT(1); NEXT();',
 'L_litm1':  'PUSHT(~(UNS64)0); NEXT();',
 'L_vf':     '{ UNS64 a = SLOT(); PUSHT(CELL(a)); } NEXT();',
 'L_vs':     '{ UNS64 a = SLOT(); CELL(a) = tos; POPT(); } NEXT();',
 'L_lstore': '{ UNS64 a = SLOT(); CELL(a) = tos; POPT(); } NEXT();',
 'L_zeq':    'tos = -(UNS64)(tos == 0); NEXT();',
 'L_sub':    'tos = NOS - tos; dsp += CELL_BYTES; NEXT();',
 'L_ne':     'tos = -(UNS64)(NOS != tos); dsp += CELL_BYTES; NEXT();',
 'L_zlt':    'tos = -(UNS64)((INT64)tos < 0); NEXT();',
 'L_sgt':    'tos = -(UNS64)((INT64)tos < (INT64)NOS); dsp += CELL_BYTES; NEXT();',
 'L_2dup':   '{ UNS64 a_ = NOS, b_ = tos; PUSHT(a_); PUSHT(b_); } NEXT();',
 'L_2drop':  'tos = CELL(dsp + CELL_BYTES); dsp += 2 * CELL_BYTES; NEXT();',
 'L_charp':  'tos += 1; NEXT();',
 'L_onep':   'tos += 1; NEXT();',
 'L_cellp':  'tos += CELL_BYTES; NEXT();',
 'L_cells':  'tos <<= CELL_SHIFT; NEXT();',
 'L_onem':   'tos -= 1; NEXT();',
 'L_invert': 'tos = ~tos; NEXT();',
 'L_count':  '{ UNS64 a_ = tos; tos = a_ + 1; PUSHT(BYTE(a_)); } NEXT();',
 'L_aligned':'tos = (tos + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1); NEXT();',
 'L_addi':   'tos += (UNS64)(INT64)(int8_t)BYTE(ip); ip += 1; NEXT();',
 'L_addix':  'tos += (UNS64)(INT64)(int8_t)BYTE(ip); ip = RS; rp += CELL_BYTES; NEXT();',
 'L_eqi':    'tos = -(UNS64)(tos == (UNS64)(INT64)(int8_t)BYTE(ip)); ip += 1; NEXT();',
 'L_eqix':   'tos = -(UNS64)(tos == (UNS64)(INT64)(int8_t)BYTE(ip)); ip = RS; rp += CELL_BYTES; NEXT();',
 'L_0branch':'t = tos; POPT(); if (t) ip += 2; else ip += BROFF(ip); NEXT();',
}
NOSTACK = {'L_noop', 'L_exit', 'L_branch', 'L_dodoes', 'L_lsave', 'L_lrest', 'L_lzero'}   # never touch the data stack
fend = s.index("\n#if FOLD\n#define EXITNEXT")
start = s.index("L_noop:")
sec = s[start:fend]
out, labs = [], [(m.start(), m.group(1)) for m in re.finditer(r'^(L_\w+):', sec, re.M)]
pos0 = 0; res = sec[:labs[0][0]]
for i, (pos, lab) in enumerate(labs):
    nxt = labs[i + 1][0] if i + 1 < len(labs) else len(sec)
    blk = sec[pos:nxt]
    # keep trailing preprocessor lines (#if/#else/#endif) that belong between blocks
    lines = blk.splitlines(True)
    tail = ''
    while lines and lines[-1].lstrip().startswith('#'): tail = lines.pop() + tail
    blk = ''.join(lines)
    if lab in HOT:
        blk = '%s: %s\n' % (lab, HOT[lab])
    elif lab not in NOSTACK:
        blk = blk.replace(lab + ':', lab + ': SPILL();', 1).replace('NEXT();', 'FILLNEXT();')
    res += blk + tail
s = s[:start] + res + s[fend:]
s = s.replace("#define FOLDBASE 128", """#define FOLDBASE 128
#define TOSCACHE 1""", 1)
# tos register, fill on entry
s = s.replace("static void virtual_machine(void) {\n    VMREGS", """static void virtual_machine(void) {
    VMREGS
    UNS64 tos = CELL(dsp); dsp += CELL_BYTES;       /* fill */
#define NOS CELL(dsp)
#if GUARD
#define PUSHT(x) do { UNS64 v_ = (x); dsp -= CELL_BYTES; \\
        CELL(dsp) = tos; tos = v_; } while (0)
#else
#define PUSHT(x) do { UNS64 v_ = (x); dsp -= CELL_BYTES; \\
        if (dsp < dsp_limit) stack_fault(0); CELL(dsp) = tos; tos = v_; } while (0)
#endif
#define POPT() do { tos = CELL(dsp); dsp += CELL_BYTES; } while (0)
#undef VMPUSH
#define VMPUSH PUSHT
#define SPILL() do { dsp -= CELL_BYTES; CELL(dsp) = tos; } while (0)
#define FILLNEXT() do { POPT(); NEXT(); } while (0)
#if ENC == 3
#define BROFF(a) ((int16_t)LD16(a))
#else
#define BROFF(a) (2 * (int16_t)TOK(a))
#endif""", 1)
sys.stdout.write(s)
