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
O=${1:-/tmp/cv8-build}
mkdir -p "$O"
HOT='+,=,!,@,LSHIFT,RSHIFT,C@,C!,AND,OR,XOR,LIT,<,U<,OVER,DROP,DUP,SWAP,ROT,>R,R>,R@,NEGATE'
LAY=tools/sod16-layout.py

# ---- dictionary dumps (tr -d '\r', always) --------------------------
BOOT='S" pool.4" INCLUDED\nS" locals.4" INCLUDED\nS" save-system.4" INCLUDED\nS" shell.4" INCLUDED\nS" tools/dict-dump-addr.4" INCLUDED\nBYE\n'
printf "$BOOT" | ./relf   kernel.img   | tr -d '\r' > "$O/d64.txt"
printf "$BOOT" | ./relf32 kernel32.img | tr -d '\r' > "$O/d32.txt"

# ---- images -----------------------------------------------------------
img() {  # img NAME CELL OPTIONS...
    local n=$1 c=$2; shift 2
    local d="$O/d64.txt"; [ "$c" = 4 ] && d="$O/d32.txt"
    python3 $LAY "$d" "$c" "$@" --emit-image "$O/$n.img" > "$O/$n.log" \
        || { echo "layout failed: $n"; tail -5 "$O/$n.log"; exit 1; }
    printf '%-14s %7d bytes\n' "$n" "$(stat -c%s "$O/$n.img")"
}
img sod16-64   8                                   # control: == SOD16
img sod16-32   4
img cpt16-64   8 --cpt 1 --skip-pad
img cpt16-32   4 --cpt 1 --skip-pad
img cptf-64    8 --cpt 3 --dataprims --fold --fold-set "$HOT"
img cptf-32    4 --cpt 2 --dataprims --fold --fold-set "$HOT"
img cv8-64     8 --v8 --cpt 3 --dataprims --fold --fold-set "$HOT"
img cv8-32     4 --v8 --cpt 2 --dataprims --fold --fold-set "$HOT"
# VM-SURVEY.md: CV8 plus the specialisations borrowed from other VMs
SPECS=loc,var,tiny,small,imm
img spec-64    8 --v8 --cpt 3 --dataprims --fold --fold-set "$HOT" --spec $SPECS
img spec-32    4 --v8 --cpt 2 --dataprims --fold --fold-set "$HOT" --spec $SPECS

# ---- engines ----------------------------------------------------------
# relf.c itself is the cell engine (VM registers are locals since
# Iteration 189). vm-lab.c is the experimental engine; its options:
#   ENC=1 SOD16 table  ENC=2 CPT16  ENC=3 CV8 byte stream
#   REG=1 VM registers in locals   FOLD=1 folded prim+EXIT opcodes
#   SCALE=S call scale shift       SKIPPAD=1 SOD16 loader skips NOOPs
#   PROFILE=1 dispatch/call histogram to $VMPROF at exit
cp tools/lab/vm-lab.c "$O/"
python3 tools/lab/gen-tos.py "$O/vm-lab.c" > "$O/vm-lab-tos.c"
cc -O2 -o "$O/relf64"  relf.c
cc -m32 -O2 -o "$O/relf32" relf.c
cc -O2 -DENC=1 -DREG=1 -DSKIPPAD=1 -DSCALE=1 -o "$O/sod16p-64" "$O/vm-lab.c"
cc -m32 -O2 -DENC=1 -DREG=1 -DSKIPPAD=1 -DSCALE=1 -o "$O/sod16p-32" "$O/vm-lab.c"
cc -O2 -DENC=2 -DREG=1 -DSCALE=1 -o "$O/cpt16-64" "$O/vm-lab.c"
cc -m32 -O2 -DENC=2 -DREG=1 -DSCALE=1 -o "$O/cpt16-32" "$O/vm-lab.c"
python3 tools/lab/gen-fold.py "$O/vm-lab.c" "$HOT" > /dev/null
cc -O2 -DENC=2 -DREG=1 -DFOLD=1 -DSCALE=3 -o "$O/cptf-64" "$O/vm-lab.c"
cc -m32 -O2 -DENC=2 -DREG=1 -DFOLD=1 -DSCALE=2 -o "$O/cptf-32" "$O/vm-lab.c"
python3 tools/lab/gen-fold.py "$O/vm-lab.c" "$HOT" v8 > /dev/null
cc -O2 -DENC=3 -DREG=1 -DFOLD=1 -DSCALE=3 -o "$O/cv8-64" "$O/vm-lab.c"
cc -m32 -O2 -DENC=3 -DREG=1 -DFOLD=1 -DSCALE=2 -o "$O/cv8-32" "$O/vm-lab.c"
python3 tools/lab/gen-fold.py "$O/vm-lab-tos.c" "$HOT" v8 > /dev/null
cc -O2 -DENC=3 -DREG=1 -DFOLD=1 -DSCALE=3 -o "$O/cv8t-64" "$O/vm-lab-tos.c"
cc -m32 -O2 -fno-pie -no-pie -DENC=3 -DREG=1 -DFOLD=1 -DSCALE=2 \
    -o "$O/cv8t-32" "$O/vm-lab-tos.c"
cc -O2 -DENC=3 -DREG=1 -DFOLD=1 -DSCALE=3 -DSPEC=1 -DSHAREDCALL=1 \
    -o "$O/spec-64" "$O/vm-lab-tos.c"
cc -m32 -O2 -fno-pie -no-pie -DENC=3 -DREG=1 -DFOLD=1 -DSCALE=2 -DSPEC=1 \
    -DSHAREDCALL=1 -o "$O/spec-32" "$O/vm-lab-tos.c"
cc -O2 -DENC=3 -DREG=1 -DFOLD=1 -DSCALE=3 -DSPEC=1 -DPROFILE=1 \
    -o "$O/spec-64-prof" "$O/vm-lab-tos.c" 2>/dev/null

# ---- smoke test: every pair must agree with dash ----------------------
want=$(for w in fn str arith; do dash tests/bench-vm/$w.sh; done)
chk() {
    got=$(for w in fn str arith; do "$O/$1" "$2" tests/bench-vm/$w.sh; done)
    [ "$got" = "$want" ] && echo "ok    $1 $(basename "$2")" \
                         || { echo "WRONG $1 $2"; exit 1; }
}
chk relf64    kernel-shell.img;       chk relf32    kernel32-shell.img
chk sod16p-64 "$O/sod16-64.img";      chk sod16p-32 "$O/sod16-32.img"
chk cpt16-64  "$O/cpt16-64.img";      chk cpt16-32  "$O/cpt16-32.img"
chk cptf-64   "$O/cptf-64.img";       chk cptf-32   "$O/cptf-32.img"
chk cv8-64    "$O/cv8-64.img";        chk cv8-32    "$O/cv8-32.img"
chk cv8t-64   "$O/cv8-64.img";        chk cv8t-32   "$O/cv8-32.img"
chk spec-64   "$O/spec-64.img";       chk spec-32   "$O/spec-32.img"
