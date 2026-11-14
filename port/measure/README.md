# port/measure/ - how 941-944 measured relfsh and rill3 on the lab's designs

Everything here runs from relf's top directory. `WORK` is any scratch directory; `LAB` a directory with
the lab's designs copied in and built (`cp -r .../designs/NAME LAB/; make -C LAB/NAME` - the default
target, `forth`, an x86-64 engine with 8-byte cells; their `forth32` was not tried). Used for 941-944:
the lab at f248f3e (its Iteration 665), relf at the commit this file is in.

The machine: Intel Xeon @ 2.30 GHz, 2 vCPUs, 4 MB L2, 8 GB, a Firecracker VM under Linux 6.18.44,
Ubuntu 24.04.5; gcc 13.3.0 (relf), clang 18.1.3 (the designs' Makefiles), Python 3.13, gforth 0.7.3.

## Build

    make                                                   # relf's engines and images (relfsh64 ...)
    for d in LAB/*/; do sh port/lab/build.sh $d WORK/$(basename $d).img; done          # relfsh
    sh port/gforth/build.sh WORK/relfsh-gforth.fi                                      # relfsh on gforth
    for d in LAB/*/; do PROGRAM=rill3 sh port/lab/build.sh $d WORK/rill/$(basename $d).img; done
    MAP=1 sh port/lab/build.sh LAB/portable-knee WORK/knee-m.img                       # and WORK/knee-m.img.map

rill3-native (943) is built as tools/build-native-shell.sh builds the shell, with build-cm-image.sh's
sources and forth/save-system-native.4: see docs/progress/0900-0999.md, Iteration 943.

## Time - tools/bench-vm.py

    sh port/measure/mk-cfg.sh relfsh LAB WORK > WORK/cfg
    WL="start loop fn str arith realistic" SCALE=5 python3 tools/bench-vm.py 12 WORK/cfg

12 rounds, the configurations interleaved in each, the first configuration the base; medians and a 95 %
interval of the ratio; CPU time from wait4, children included; `start` is 20 runs of `-c true`. For
rill3 (no `-c`): `mk-cfg.sh rill3 LAB WORK/rill`, a directory W with tests/cm/bench's loop.cm and
calls.cm, its for.cm with `range 300` made `range 900`, and nop.cm (`var x 0`), then
`WL="nop loop calls for" WDIR=W WEXT=.cm python3 tools/bench-vm.py 12 WORK/cfg`.

## Size, outputs, memory - measure.py

    cc -O2 -o port/measure/rsstrace port/measure/rsstrace.c
    sh port/measure/scaled.sh 5 WORK/w5                    # bench-vm's five at SCALE=5, and start.sh
    python3 port/measure/measure.py WORK/cfg WORK/w5 .sh WORK/w5/start.sh WORK/measure.json

Size is the engine (a .fi's .so beside it too) and the image; each workload's output is checked against
the first configuration's; memory is rsstrace's at the process's exit (ptrace's exit event): Rss,
Anonymous, VmHWM (the peak), KB.

## Correctness

    sh port/measure/suite.sh /abs/wrapper WORK/suite.txt   # tests/shell, the wrapper a #! sh running a build
    sh port/measure/cmsuite.sh /abs/wrapper                 # tests/cm's 192: the runtime's, scripts, prompt

## Where the bytes go

    python3 port/measure/design-bytes.py WORK/knee-m.img.map WORK/knee-m.img 80 8969
    python3 port/measure/cv8-bytes.py kernel64-shell.img forth/kernel64.img

80 is port/lab/header.py's header length (every design's), 8969 the design's own image.img less it.

## Dispatches and profiles

    python3 port/measure/relf-count.py WORK/rc             # CV8 counting engines: relf-count, relfsh-count
    make -n -C LAB/portable-knee forth -B         # its command; -DPROFILE=1 added, -o forth-prof: KNEE-PROF
    python3 port/measure/count-dispatch.py WORK/rc KNEE-PROF LAB/portable-knee/image.img WORK/portable-knee.img
    VMPROF=WORK/p.txt KNEE-PROF WORK/knee-m.img tests/bench-vm/realistic.sh
    LAB/portable-knee/forth LAB/portable-knee/image.img < port/measure/kdump.4 | grep '^K' > WORK/kmap
    DESIGN_SRC=LAB/portable-knee/src python3 port/measure/design-prof.py WORK/p.txt WORK/knee-m.img.map WORK/knee-m.img WORK/kmap
    python3 -c "open('WORK/c.bin','wb').write(bytes(1 << 20))"
    COUNTS=WORK/c.bin THIS_SH=WORK/rc/relfsh-count WORK/rc/relfsh-count tests/bench-vm/realistic.sh
    python3 port/measure/cv8-prof.py kernel64-shell.img WORK/c.bin

A design's PROFILE=1 dump (DISPATCH256) counts every call twice - its first byte (0x80-0xFF) and the
pseudo-op 256: count-dispatch.py and design-prof.py take it once. Before 944 it was taken twice.
design-ops.py names a design's opcodes from its src (written for portable-knee's genes).

## A JIT design's refusals

    make -n -C LAB/fastest-x86-64 forth-libc   # its command, -DJITLOG=1 added, -o forth-jitlog
    JITLOG=WORK/jl.txt LAB/fastest-x86-64/forth-jitlog WORK/fx-m.img tests/bench-vm/realistic.sh
    python3 port/measure/jit-roots.py KMAP WORK/fx-m.img.map WORK/jl.txt            # roots, by words blocked
    python3 port/measure/jit-why.py KMAP WORK/fx-m.img.map PROF WORK/jl.txt 20      # the hottest, each's chain

## Results, as measured (results/)

relfsh-bench.txt and relfsh-measure.json (942's table), rill3-bench.txt and rill3-measure.json (943's),
dispatches.txt, bytes-*.txt, realistic-*.txt, the two bench configurations (`$WORK` for the scratch path).
inputs/ is the lab's bench/*.fth as fed to both: each repeated (`: BX n 0 DO BENCH LOOP ; BX`), BYE.
