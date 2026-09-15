#!/bin/bash
# tools/lab/build-cv8.sh [OUTDIR] - build every engine/image pair that
# CV8.md measures, at both cell widths, from a clean checkout.
#
# Needs: cc with -m32 (gcc-multilib), python3, and the committed
# relf/relf32/kernel.img/kernel32.img. Nothing here touches the tree:
# all output goes to OUTDIR (default /tmp/cv8-build).
#
# Every image is TRANSLATED from the cell image, exactly as SOD16's
# were: the Forth compiler still emits cells, so none of these can
# compile new definitions (tests/shell/run-forth). That is phase 3.
set -e
cd "$(dirname "$0")/../.."

# Every engine below is a measured or tested subject, so it runs in a
# predictable environment rather than whatever the caller exported.
# LD_PRELOAD is the one that bites: a desktop session that preloads a
# library into every process has it loaded into every engine here too,
# and when the engine is a 32-bit binary and the library is 64-bit,
# ld.so cannot load it and writes a line of complaint PER PROCESS -
# straight into the output a dump or a test comparison is reading.
unset LD_PRELOAD

O=${1:-/tmp/cv8-build}
mkdir -p "$O"
HOT='+,=,!,@,LSHIFT,RSHIFT,C@,C!,AND,OR,XOR,LIT,<,U<,OVER,DROP,DUP,SWAP,ROT,>R,R>,R@,NEGATE'
# The fold set lives in THREE places that must agree: this list (passed
# to the translator), the engine's generated table (gen-fold.py, from
# this list), and cv8.4's FOLD-OPS, which the image's own compiler uses
# to fold at run time. Check the third against the first.
CV8_LIST=$(sed -n "/^CREATE FOLD-OPS/,/^ALIGN/p" cv8.4 |
           grep -o "' [^ ]* >OP" | sed "s/^' //; s/ >OP$//" | paste -sd,)
[ "$CV8_LIST" = "$HOT" ] || {
    echo "fold set mismatch between build-cv8.sh and cv8.4's FOLD-OPS:"
    echo "  build-cv8.sh: $HOT"
    echo "  cv8.4:        $CV8_LIST"; exit 1; }
LAY=tools/layout.py

# ---- dictionary dumps (tr -d '\r', always) --------------------------
BOOT='S" pool.4" INCLUDED\nS" locals.4" INCLUDED\nS" save-system.4" INCLUDED\nS" shell.4" INCLUDED\nS" tools/dict-dump-addr.4" INCLUDED\nBYE\n'
printf "$BOOT" | ./relf   kernel.img   | tr -d '\r' > "$O/d64.txt"
printf "$BOOT" | ./relf32 kernel32.img | tr -d '\r' > "$O/d32.txt"
# A second pair of dumps with cv8.4 loaded, for the self-hosting images.
# cv8.4 is NOT in the others: it holds 64-bit literals that the 16-bit
# encodings cannot represent, and they only ever need to RUN, not compile.
# cv8-save.4 must come AFTER shell.4: it scrubs shell.4's tokenizer
# state. Without it SAVE-SYSTEM is the cell version and writes a RELF
# header, which the CV8 engine then refuses.
SELF='S" cv8.4" INCLUDED\nS" pool.4" INCLUDED\nS" locals.4" INCLUDED\nS" save-system.4" INCLUDED\nS" shell.4" INCLUDED\nS" cv8-save.4" INCLUDED\nS" tools/dict-dump-addr.4" INCLUDED\nBYE\n'
printf "$SELF" | ./relf   kernel.img   | tr -d '\r' > "$O/d64-self.txt"
printf "$SELF" | ./relf32 kernel32.img | tr -d '\r' > "$O/d32-self.txt"
# The same shell, with cv8b.4 on top: byte-granular headers. This is the
# densest working configuration in the tree and nothing built it until
# now, which is how the escaped band stayed broken for eight iterations.
SELFB='S" cv8.4" INCLUDED\nS" cv8b.4" INCLUDED\nS" pool.4" INCLUDED\nS" locals.4" INCLUDED\nS" save-system.4" INCLUDED\nS" shell.4" INCLUDED\nS" cv8-save.4" INCLUDED\nS" tools/dict-dump-addr.4" INCLUDED\nBYE\n'
printf "$SELFB" | ./relf   kernel.img   | tr -d '\r' > "$O/d64-selfb.txt"
printf "$SELFB" | ./relf32 kernel32.img | tr -d '\r' > "$O/d32-selfb.txt"
# bare kernel + cv8.4 only: boots into the interpreter, for the CORE suite
KONLY='S" cv8.4" INCLUDED\nS" tools/dict-dump-addr.4" INCLUDED\nBYE\n'
printf "$KONLY" | ./relf   kernel.img   | tr -d '\r' > "$O/k64.txt"
printf "$KONLY" | ./relf32 kernel32.img | tr -d '\r' > "$O/k32.txt"
# cv8b.4 on top of cv8.4: byte-granular dictionary headers. A separate
# dump because the overlay REPLACES SEARCH-WORDLIST and NAME> - the
# kernel's own versions compare names a cell at a time and assume the
# nfa is cell-aligned and zero-padded, and under byte headers it is
# neither.
KCV8B='S" cv8.4" INCLUDED\nS" cv8b.4" INCLUDED\nS" tools/dict-dump-addr.4" INCLUDED\nBYE\n'
# The 16-bit encodings have compiler overlays too, using the suffix `16`
# where cv8.4 uses `8`. Without these the SOD16 and CPT16 images can RUN
# but cannot compile a new definition - the same gap cv8.4 closed for
# CV8 in phase 3. Each needs its own dump, because the overlay replaces
# the code-emitting words.
printf "$KCV8B" | ./relf   kernel.img   | tr -d '\r' > "$O/kb64.txt"
printf "$KCV8B" | ./relf32 kernel32.img | tr -d '\r' > "$O/kb32.txt"

# ---- images -----------------------------------------------------------
img() {  # img NAME CELL OPTIONS...
    local n=$1 c=$2; shift 2
    local d="$O/d64.txt"; [ "$c" = 4 ] && d="$O/d32.txt"
    case "$*" in *--cv8-compiler*) d="$O/d64-self.txt"
        [ "$c" = 4 ] && d="$O/d32-self.txt";; esac
    case "$n" in fkernel-64) d="$O/k64.txt";; fkernel-32) d="$O/k32.txt";;
                 cv8b-64|cv8b-k64) d="$O/kb64.txt";;
                 cv8b-32|cv8b-k32) d="$O/kb32.txt";;
                 noesc-64) d="$O/k64.txt";; noesc-32) d="$O/k32.txt";;
                 selfb-64) d="$O/d64-selfb.txt";; selfb-32) d="$O/d32-selfb.txt";; esac
    python3 $LAY "$d" "$c" "$@" --emit-image "$O/$n.img" > "$O/$n.log" \
        || { echo "layout failed: $n"; tail -5 "$O/$n.log"; exit 1; }
    printf '%-14s %7d bytes\n' "$n" "$(stat -c%s "$O/$n.img")"
}
img cv8-64     8 --v8 --cpt 3 --dataprims --fold --fold-set "$HOT" --no-varcall --no-varslot
img cv8-32     4 --v8 --cpt 2 --dataprims --fold --fold-set "$HOT" --no-varcall --no-varslot
# VM-SURVEY.md: CV8 plus the specialisations borrowed from other VMs
SPECS=loc,var,tiny,small,imm
img spec-64    8 --v8 --cpt 3 --dataprims --fold --fold-set "$HOT" --spec $SPECS
img spec-32    4 --v8 --cpt 2 --dataprims --fold --fold-set "$HOT" --spec $SPECS
# self-hosting: --cv8-compiler swaps cv8.4's X8 bodies into X, so the
# image's own compiler emits CV8 (phase 3). tests/shell/run-forth.
img self-64    8 --v8 --cpt 3 --dataprims --fold --fold-set "$HOT" --spec $SPECS --cv8-compiler
img self-32    4 --v8 --cpt 2 --dataprims --fold --fold-set "$HOT" --spec $SPECS --cv8-compiler
# The byte-header shell. A call scale of 0 is not optional here - byte
# headers exist because nothing needs cell alignment any more - so the
# 14-bit near call reaches only 16 KB and most calls in a 60 KB image
# take the 3-byte far form. It still comes out the smallest image in
# the ladder.
img selfb-64   8 --v8 --cpt 0 --bytehdr --dataprims --fold --fold-set "$HOT" --spec $SPECS --cv8-compiler
img selfb-32   4 --v8 --cpt 0 --bytehdr --dataprims --fold --fold-set "$HOT" --spec $SPECS --cv8-compiler
# A CV8 image that boots into the INTERPRETER: the ANS CORE suite needs
# one, because a shell image feeds Forth source to the shell instead.
img fkernel-64 8 --v8 --cpt 3 --dataprims --fold --fold-set "$HOT" --spec $SPECS --cv8-compiler
img fkernel-32 4 --v8 --cpt 2 --dataprims --fold --fold-set "$HOT" --spec $SPECS --cv8-compiler
# s6: byte-granular dictionary headers. The link stops being a cell and
# becomes a 1-3 byte DISTANCE BACKWARD from the nfa, tag byte last, so
# it is read backward - the tag sits at nfa-1 because it is the first
# byte anyone reads. Names and code bodies stop being padded, and with
# nothing needing cell alignment the call scale drops to 0.
#
# --cv8-compiler is NOT optional here. Without it the image carries the
# kernel's own SEARCH-WORDLIST, which assumes a cell link and an aligned
# name, and the image boots and then segfaults on the first lookup. The
# run-only pair below is built anyway because it is the honest SIZE
# figure for the encoding - the self-hosting pair carries cv8b.4's
# replacement words as well - but it is never run, and the k in its name
# is the reminder.
img cv8b-k64   8 --v8 --cpt 0 --bytehdr --dataprims --fold --fold-set "$HOT" --spec $SPECS
img cv8b-k32   4 --v8 --cpt 0 --bytehdr --dataprims --fold --fold-set "$HOT" --spec $SPECS
img cv8b-64    8 --v8 --cpt 0 --bytehdr --dataprims --fold --fold-set "$HOT" --spec $SPECS --cv8-compiler
img cv8b-32    4 --v8 --cpt 0 --bytehdr --dataprims --fold --fold-set "$HOT" --spec $SPECS --cv8-compiler
# The OLD numbering, without the escaped band, which is now the default
# everywhere else. Kept as a stage so the two stay comparable and so
# the engine's refusal path - an image using the band against an engine
# built without it - has something to refuse.
img noesc-64     8 --v8 --cpt 3 --dataprims --fold --fold-set "$HOT" --spec $SPECS --cv8-compiler --no-escape
img noesc-32     4 --v8 --cpt 2 --dataprims --fold --fold-set "$HOT" --spec $SPECS --cv8-compiler --no-escape

# ---- engines ----------------------------------------------------------
# relf.c itself is the cell engine (VM registers are locals since
# Iteration 189). vm-lab.c is the experimental engine; its options:
#   REG=1 VM registers in locals   FOLD=1 folded prim+EXIT opcodes
#   SCALE=S call scale shift       SKIPPAD=1 SOD16 loader skips NOOPs
#   PROFILE=1 dispatch/call histogram to $VMPROF at exit
cp tools/lab/vm-lab.c "$O/"
python3 tools/lab/gen-tos.py "$O/vm-lab.c" > "$O/vm-lab-tos.c"
cc -O2 -o "$O/relf64"  relf.c
cc -m32 -O2 -o "$O/relf32" relf.c
python3 tools/lab/gen-fold.py "$O/vm-lab.c" "$HOT" > /dev/null
python3 tools/lab/gen-fold.py "$O/vm-lab.c" "$HOT" v8 > /dev/null
cc -O2 -DREG=1 -DFOLD=1 -DSCALE=3 -DVARCALL=0 -DVARSLOT=0 -o "$O/cv8-64" "$O/vm-lab.c"
cc -m32 -O2 -DREG=1 -DFOLD=1 -DSCALE=2 -DVARCALL=0 -DVARSLOT=0 -o "$O/cv8-32" "$O/vm-lab.c"
python3 tools/lab/gen-fold.py "$O/vm-lab-tos.c" "$HOT" v8 > /dev/null
cc -O2 -DREG=1 -DFOLD=1 -DSCALE=3 -o "$O/cv8t-64" "$O/vm-lab-tos.c"
cc -m32 -O2 -fno-pie -no-pie -DREG=1 -DFOLD=1 -DSCALE=2 -DVARCALL=0 -DVARSLOT=0 \
    -o "$O/cv8t-32" "$O/vm-lab-tos.c"
cc -O2 -DREG=1 -DFOLD=1 -DSCALE=3 -DSPEC=1 -DSHAREDCALL=1 \
    -o "$O/spec-64" "$O/vm-lab-tos.c"
cc -m32 -O2 -fno-pie -no-pie -DREG=1 -DFOLD=1 -DSCALE=2 -DSPEC=1 \
    -DSHAREDCALL=1 -o "$O/spec-32" "$O/vm-lab-tos.c"
cc -O2 -DREG=1 -DFOLD=1 -DSCALE=3 -DSPEC=1 -DPROFILE=1 \
    -o "$O/spec-64-prof" "$O/vm-lab-tos.c" 2>/dev/null
# fixed-width-call/slot build, for comparison with the variable forms
cc -O2 -DREG=1 -DFOLD=1 -DSCALE=3 -DSPEC=1 -DSHAREDCALL=1 \
    -DVARCALL=0 -DVARSLOT=0 -o "$O/fixedw-64" "$O/vm-lab-tos.c"
# s6 engines: spec with SCALE=0, because byte-granular headers leave
# call targets byte-aligned. The engine never READS a dictionary link -
# only SOD16 does, to number its calls - so the whole byte-granular
# header change is invisible to it and the scale is the only difference
# in the binary. DOESFAR matches cv8.4's three-byte DOES> call, which
# scale 0 requires: the two-byte form's 14-bit field of scaled units
# reaches 131 KB at scale 3 but only 16 KB at scale 0.
cc -O2 -DREG=1 -DFOLD=1 -DSCALE=0 -DSPEC=1 -DSHAREDCALL=1 -DDOESFAR=1 \
    -o "$O/cv8b-64" "$O/vm-lab-tos.c"
cc -m32 -O2 -fno-pie -no-pie -DREG=1 -DFOLD=1 -DSCALE=0 -DSPEC=1 \
    -DSHAREDCALL=1 -DDOESFAR=1 -o "$O/cv8b-32" "$O/vm-lab-tos.c"
# Escaped-band engines: spec plus -DESCAPE=1. An engine WITHOUT the band
# refuses an image that uses it rather than misreading it, so these have
# to be built in matching pairs with the esc-* images.
cc -O2 -DREG=1 -DFOLD=1 -DSCALE=3 -DSPEC=1 -DSHAREDCALL=1 -DESCAPE=0 \
    -o "$O/noesc-64" "$O/vm-lab-tos.c"
cc -m32 -O2 -fno-pie -no-pie -DREG=1 -DFOLD=1 -DSCALE=2 -DSPEC=1 \
    -DSHAREDCALL=1 -DESCAPE=0 -o "$O/noesc-32" "$O/vm-lab-tos.c"

# ---- smoke test: every pair must agree with dash ----------------------
want=$(for w in fn str arith; do dash tests/bench-vm/$w.sh; done)
chk() {
    got=$(for w in fn str arith; do "$O/$1" "$2" tests/bench-vm/$w.sh; done)
    [ "$got" = "$want" ] && echo "ok    $1 $(basename "$2")" \
                         || { echo "WRONG $1 $2"; exit 1; }
}
chk relf64    kernel-shell.img;       chk relf32    kernel32-shell.img
chk cv8-64    "$O/cv8-64.img";        chk cv8-32    "$O/cv8-32.img"
chk cv8t-64   "$O/cv8-64.img";        chk cv8t-32   "$O/cv8-32.img"
chk spec-64   "$O/spec-64.img";       chk spec-32   "$O/spec-32.img"
chk spec-64   "$O/self-64.img";       chk spec-32   "$O/self-32.img"
chk cv8b-64   "$O/selfb-64.img";      chk cv8b-32   "$O/selfb-32.img"
