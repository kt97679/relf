# Makefile - the project's builds and suites, in one place.
#
# Added at Iteration 384. Everything here was already a script or a
# one-liner in PROGRESS.md; this file is the index of them, not a new
# build system. `make help` lists the targets.
#
# ==================================================================
# WHAT THIS DOES NOT DO
# ==================================================================
#
# It does not rebuild kernel64.img as a matter of course. That image is
# simultaneously the image cross.4 PRODUCES and the image cross.4 RUNS
# ON: rebuilding it is a fixpoint step, not a compile, and a wrong one
# is not a broken build but a subtly different shell. `make images`
# does it deliberately, into a temporary directory, and refuses to
# install the result unless it is byte-identical or IMAGES_FORCE=1 is
# given. `make check-images` is the read-only half, and tests/verify
# checks it on every run.
#
# Only the two KERNEL images, kernel64.img and kernel32.img, are
# committed: they are the bootstrap seed that cross.4 runs on, and
# cannot be rebuilt from nothing. The engines (untracked since 402) and
# the shell images (since 489) are build products; `make clean` removes
# the engines, `make distclean` the shell images too, and nothing here
# touches the kernel images.

CC      ?= cc
CFLAGS  ?= -O2 -Wall

# How wide a cell is on THIS host. On a 32-bit machine - ARMv7, i386,
# anything where a pointer is 4 bytes - the native engine runs the
# 4-byte image, and `kernel64.img` (8-byte) is not a RelF image as far as
# it is concerned. `make` on an ARMv7 board said exactly that and
# stopped (Iteration 397). Override with HOSTBITS=32 to see what such a
# host does from a 64-bit one.
HOSTBITS ?= $(shell getconf LONG_BIT 2>/dev/null || echo 64)
ifeq ($(HOSTBITS),32)
NATIVE_ENGINE    = relf32
NATIVE_IMG       = forth/kernel32.img
NATIVE_SHELL_IMG = kernel32-shell.img
OTHER_SHELL_IMG  =
else
NATIVE_ENGINE    = relf64
NATIVE_IMG       = forth/kernel64.img
NATIVE_SHELL_IMG = kernel64-shell.img
OTHER_SHELL_IMG  = kernel32-shell.img
endif
# The i386 engine is built non-PIE: PIE costs it the TOS register, and
# README.md's compilation section has said so since Iteration 243.
CFLAGS32 ?= -m32 -O2 -Wall -fno-pie -no-pie
PYTHON  ?= python3

SHELL_SOURCES = forth/extend.4 forth/safety.4 forth/pool.4 forth/shadow.4 forth/save-system.4 shell/shell.4 shell/edit.4 shell/tree.4
KERNEL_SOURCES = forth/kernel.4 forth/cross.4 forth/cross-core.4 forth/extend.4

.PHONY: all help engines shell-images shells images check-images \
        test verify verify-update diff matrix posix mrsh shell interactive \
        busybox yash absg portability lint dead-words sizes profile bench bundle \
        clean distclean

all: engines shell-images shells

help:
	@echo 'Targets:'
	@echo '  all            engines and shell images (the default)'
	@echo '  engines        relf64 and relf32 from engine/cv8.c'
	@echo '  shell-images   kernel64-shell.img and kernel32-shell.img'
	@echo '  shells         relfsh64, relfsh32 (engine and image, one file), relfsh'
	@echo '  images         re-cross-compile the base images (see the header)'
	@echo '  check-images   ... and only check they still reproduce'
	@echo ''
	@echo '  test           tests/run_tests.sh: the core, both cell widths'
	@echo '  diff           the differential cases against bash'
	@echo '  matrix         the construct and error matrix'
	@echo '  posix mrsh     the two acceptance suites'
	@echo '  shell          tests/shell: the shell'"'"'s own assertions'
	@echo '  interactive    the pty cases'
	@echo '  verify         every suite, against tests/BASELINE'
	@echo '  verify-update  ... and record the result as the new baseline'
	@echo ''
	@echo '  absg           the Advanced Bash-Scripting Guide examples (ABSG=/path)'
	@echo '  portability    the scaffolding: shebangs, locale pins, the bundle'
	@echo '  lint           comment lint over the Forth sources; host-sh lint over tests'
	@echo '  dead-words     unreachable definitions'
	@echo '  sizes          this shell against every other one installed'
	@echo '  profile        dispatch counts per word, on a realistic script'
	@echo '  bench          speed against the reference shells'
	@echo '  bundle         a git bundle of master, HEAD and the tag'
	@echo ''
	@echo '  clean          build products; distclean also the shell images'
	@echo ''
	@echo 'External corpora (fetched, not vendored - see each script'"'"'s header):'
	@echo '  busybox        BUSYBOX_TESTS=/path/to/ash_test make busybox'
	@echo '  yash           YASH_TESTS=/path/to/yash/tests make yash'

# ------------------------------------------------------------------
# Engines
# ------------------------------------------------------------------
# Named by cell width since Iteration 507: relf64 and relf32, one of
# them native. A 32-bit host builds relf32 with its own compiler flags,
# not -m32.
ifeq ($(HOSTBITS),32)
engines: relf32
else
engines: relf64 relf32
endif

# Rebuilt when the machine changes as well as when the source does. A
# binary from another architecture is newer than cv8.c and looks up to
# date, which is how an x86-64 engine ended up being exec'd on an ARMv7
# board (Iteration 402). The stamp holds `uname -m`.
HOSTARCH := $(shell uname -m 2>/dev/null || echo unknown)

.PHONY: force-arch-check
.relf-arch: force-arch-check
	@printf '%s\n' '$(HOSTARCH)' | cmp -s - $@ 2>/dev/null || printf '%s\n' '$(HOSTARCH)' > $@

# The engine's dispatch tables, generated from opcodes.tab, the opcode
# map's one source (Iteration 518). Committed, so `cc cv8.c` needs
# nothing else; regenerated here whenever the table changes, and held to
# it by tools/gen-opcodes.sh --check in tests/portability.
engine/cv8-ops.h: engine/opcodes.tab tools/gen-opcodes.sh
	@sh tools/gen-opcodes.sh > $@.tmp && mv -f $@.tmp $@

# The 8-byte-cell targets exist only where they can run. On a 32-bit
# host `relf64` used to be an ordinary rule - verification's rebuild step
# asked for kernel64-shell.img, and make compiled a 32-bit engine under
# the 64-bit name before the image build failed (seen on the ARMv7 board
# at Iteration 508). Now it says why, and makes nothing.
ifeq ($(HOSTBITS),32)
.PHONY: relf64 kernel64-shell.img relfsh64
relf64 kernel64-shell.img relfsh64:
	@echo "$@: an 8-byte-cell build cannot run on this 32-bit host" >&2; exit 1
else
relf64: engine/cv8.c engine/cv8-ops.h .relf-arch
	$(CC) $(CFLAGS) -o $@ $<
endif

ifeq ($(HOSTBITS),32)
relf32: engine/cv8.c engine/cv8-ops.h .relf-arch
	$(CC) $(CFLAGS) -o $@ $<
else
relf32: engine/cv8.c engine/cv8-ops.h .relf-arch
	$(CC) $(CFLAGS32) -o $@ $<
endif

# ------------------------------------------------------------------
# Shell images
#
# tools/build-shell-image.sh loads SHELL_SOURCES into a kernel image and
# saves the result, refusing one that does not start the shell or whose
# build reported errors. Until Iteration 506 the relfsh script did this,
# on first use; relfsh is a binary now, and make is what keeps it current.
# ------------------------------------------------------------------
# On a 64-bit host both are built; on a 32-bit one there is only the
# native 4-byte pair, and the 8-byte image cannot be run at all.
shell-images: $(NATIVE_SHELL_IMG) $(OTHER_SHELL_IMG)

ifneq ($(HOSTBITS),32)
kernel64-shell.img: relf64 forth/kernel64.img $(SHELL_SOURCES) tools/build-shell-image.sh
	@sh tools/build-shell-image.sh ./relf64 forth/kernel64.img $@ $(SHELL_SOURCES)
endif

# LD_PRELOAD is cleared for the i386 build: a preload library for the
# host architecture can never be loaded into a 32-bit process, and the
# loader says so - noisily - on every invocation. Ubuntu and Mint set
# one system-wide (libgtk3-nocsd), so this is most people's first
# impression of `make` (Iteration 389).
ifeq ($(HOSTBITS),32)
# The native engine IS the 4-byte one here: there is no -m32 build, and
# relf32 is built natively.
kernel32-shell.img: relf32 forth/kernel32.img $(SHELL_SOURCES) tools/build-shell-image.sh
	@LD_PRELOAD= sh tools/build-shell-image.sh ./relf32 forth/kernel32.img $@ $(SHELL_SOURCES)
else
kernel32-shell.img: relf32 forth/kernel32.img $(SHELL_SOURCES) tools/build-shell-image.sh
	@LD_PRELOAD= sh tools/build-shell-image.sh ./relf32 forth/kernel32.img $@ $(SHELL_SOURCES)
endif

# ------------------------------------------------------------------
# The shells: one file each, the engine with its shell image inside and
# a trailer by which the engine finds it (tools/embed.sh; Iteration 506).
# relfsh is the native pair; on a 64-bit host relfsh32 is the 4-byte
# one, which the suites run too.
# ------------------------------------------------------------------
# relfsh64 and relfsh32 by width (Iteration 507), and relfsh a link to
# the native one: the name people type, and the one the suites run.
ifeq ($(HOSTBITS),32)
SHELLS = relfsh32 relfsh
NATIVE_SHELL = relfsh32
else
SHELLS = relfsh64 relfsh32 relfsh
NATIVE_SHELL = relfsh64
endif
shells: $(SHELLS)

ifneq ($(HOSTBITS),32)
relfsh64: relf64 kernel64-shell.img tools/embed.sh
	@sh tools/embed.sh ./relf64 kernel64-shell.img $@
endif

relfsh: $(NATIVE_SHELL)
	@ln -sf $(NATIVE_SHELL) $@

relfsh32: relf32 kernel32-shell.img tools/embed.sh
	@LD_PRELOAD= sh tools/embed.sh ./relf32 kernel32-shell.img $@

# ------------------------------------------------------------------
# The assembly engine (ASM-ENGINE.md): x86-64, no libc. Not part of
# `all` until it runs everything cv8.c runs. Its dispatch tables come
# from opcodes.tab, with a stub for each handler not written yet.
# ------------------------------------------------------------------
# The engine's tables, from opcodes.tab, in Forth (Iteration 549).
engine/relfasm-ops.4: engine/opcodes.tab tools/gen-opcodes.sh
	@sh tools/gen-opcodes.sh --forth-ops > $@.tmp && mv -f $@.tmp $@

# Linked to raw bytes: the source carries its own ELF header and single
# program header (Iteration 520, after kt97679/itsy-linux), so nothing
# of the linker's layout - sections, their table, page padding - is kept.
# The single-file shell on the assembly engine, as relfsh64 is on cv8.c.
relfshasm64: relfasm64 kernel64-shell.img tools/embed.sh
	@sh tools/embed.sh ./relfasm64 kernel64-shell.img $@

engine/relfasm-consts.4: engine/opcodes.tab tools/gen-opcodes.sh
	@sh tools/gen-opcodes.sh --forth-consts > $@.tmp && mv -f $@.tmp $@

# The assembly engine, assembled by relf itself (SELF-HOSTING.md M5,
# Iteration 549): its source is relfasm64.4, in Forth - asm64.4's syntax -
# run on the C engine; no assembler or linker. The result rebuilds itself
# identically (make verify's asm:fixpoint).
ASM_SOURCES = engine/relfasm64.4 forth/asm64.4 engine/engine-macros.4 forth/extend.4 engine/relfasm-ops.4 engine/relfasm-consts.4
relfasm64: $(ASM_SOURCES) forth/kernel64.img relf64
	@rm -f relfasm64.forth
	@./relf64 forth/kernel64.img < engine/relfasm64.4 > relfasm64.log 2>&1 || true
	@if grep -q 'Undefined word\|asm64:\|dictionary full' relfasm64.log || [ ! -x relfasm64.forth ]; then \
	    echo "relfasm64: relf did not assemble it:" >&2; grep -v '^OK' relfasm64.log | head -5 >&2; rm -f relfasm64.forth; exit 1; fi
	@mv -f relfasm64.forth $@ && rm -f relfasm64.log
	@[ $$(wc -c < $@) -lt 65536 ] || { echo "relfasm64 outgrew 64 KB: move BSS_BASE and VM_OFF up in engine/relfasm64.4" >&2; rm -f $@; exit 1; }

# The native back end's first proof (docs/NATIVE.md, N1a, Iteration 610):
# a small program compiled by forth/native.4 into x86-64 code; it prints 169.
native-n1a: forth/native-n1a.4 forth/native.4 forth/asm64.4 forth/extend.4 forth/kernel64.img relf64
	@rm -f $@ && ./relf64 forth/kernel64.img < forth/native-n1a.4 > native-n1a.log 2>&1 || true
	@if [ ! -x $@ ] || grep -q 'Undefined word\|native:\|asm64:' native-n1a.log; then \
	    echo "native-n1a: not built:" >&2; tr -d '\r' < native-n1a.log | grep -v '^OK$$' | head -5 >&2; rm -f $@; exit 1; fi
	@rm -f native-n1a.log

# N1c-1b (Iteration 616): forth/native-cross.4's first milestone - words with
# CV8-format headers and native bodies; a native walker lists every name.
native-n1c: forth/native-n1c.4 forth/native-cross.4 forth/cross-core.4 forth/native.4 forth/native-rt.4 forth/asm64.4 forth/extend.4 forth/kernel64.img relf64
	@rm -f $@ && ./relf64 forth/kernel64.img < forth/native-n1c.4 > native-n1c.log 2>&1 || true
	@if [ ! -x $@ ] || grep -q 'Undefined word\|native:\|asm64:' native-n1c.log; then \
	    echo "native-n1c: not built:" >&2; tr -d '\r' < native-n1c.log | grep -v '^OK$$' | head -5 >&2; rm -f $@; exit 1; fi
	@rm -f native-n1c.log

# N2 (Iteration 638): the native shell - the shell's sources loaded into the native
# kernel, saved by forth/save-system-native.4 as an ELF executable.
relfsh-native: native-kernel forth/save-system-native.4 $(SHELL_SOURCES) tools/build-native-shell.sh
	@sh tools/build-native-shell.sh $@

# N1c-3 (Iteration 624): the native kernel - kernel.4 entire, kernel-native.4's
# back end in part 9's place - booting to its own prompt; CORE against CV8's.
native-kernel: forth/native-kernel.4 forth/kernel-native.4 forth/native-cross.4 forth/native.4 forth/native-rt.4 forth/native-locals.4 forth/native-sig.4 forth/kernel.4 engine/relfasm64.4 engine/relfasm-ops.4 tools/gen-native-os.py relf64
	@python3 tools/gen-native-os.py native-os.4
	@sed '/^\\ PART 10: TOP LEVEL/,$$d' forth/kernel.4 > native-kcut9.4 && echo END-CROSS >> native-kcut9.4
	@{ echo CROSS-COMPILE; sed -n '/^\\ PART 10: TOP LEVEL/,$$p' forth/kernel.4; } > native-kcut10.4
	@rm -f $@ && ./relf64 forth/kernel64.img < forth/native-kernel.4 > native-kernel.log 2>&1 || true
	@if [ ! -x $@ ] || grep -q 'Undefined word\|native\(-cross\)*: \|asm64:' native-kernel.log \
	    || ! tr -d '\r' < native-kernel.log | grep -q 'forward calls waiting: *$$'; then \
	    echo "native-kernel: not built:" >&2; tr -d '\r' < native-kernel.log | grep -v '^OK$$' | tail -3 >&2; rm -f $@; exit 1; fi
	@rm -f native-kernel.log native-kcut9.4 native-kcut10.4 native-os.4

# N1c-2 (Iteration 623): kernel.4 through part 9, natively, with kernel-native.4's
# back end; the native kernel's own compiler, at run time, against CV8's.
native-k9: forth/native-k9.4 forth/kernel-native.4 forth/native-cross.4 forth/native.4 forth/native-rt.4 forth/native-locals.4 forth/kernel.4 tests/native/kernel-rc.4 engine/relfasm64.4 tools/gen-native-os.py relf64
	@python3 tools/gen-native-os.py native-os.4
	@sed '/^\\ PART 10: TOP LEVEL/,$$d' forth/kernel.4 > native-kcut9.4 && echo END-CROSS >> native-kcut9.4
	@rm -f $@ && ./relf64 forth/kernel64.img < forth/native-k9.4 > native-k9.log 2>&1 || true
	@if [ ! -x $@ ] || grep -q 'Undefined word\|native\(-cross\)*: \|asm64:' native-k9.log \
	    || ! tr -d '\r' < native-k9.log | grep -q 'forward calls waiting: WARM *$$'; then \
	    echo "native-k9: not built:" >&2; tr -d '\r' < native-k9.log | grep -v '^OK$$' | tail -3 >&2; rm -f $@; exit 1; fi
	@rm -f native-k9.log native-kcut9.4 native-os.4

# N1c-1c (Iteration 618): kernel.4's parts 0-3 compiled natively, with
# tests/native/kernel-cut.4; it must print what CV8's kernel prints for it.
native-k3: forth/native-k3.4 forth/native-cross.4 forth/native.4 forth/native-rt.4 forth/kernel.4 tests/native/kernel-cut.4 relf64
	@sed '/^\\ PART 9: THE COMPILER/,$$d' forth/kernel.4 > native-kcut.4 && echo END-CROSS >> native-kcut.4
	@rm -f $@ && ./relf64 forth/kernel64.img < forth/native-k3.4 > native-k3.log 2>&1 || true
	@if [ ! -x $@ ] || grep -q 'Undefined word\|native\|asm64:' native-k3.log; then \
	    echo "native-k3: not built:" >&2; tr -d '\r' < native-k3.log | grep -v '^OK$$' | head -5 >&2; rm -f $@; exit 1; fi
	@rm -f native-k3.log native-kcut.4

# N1b (Iteration 611): tests/native/prims.4 compiled natively; it must print
# what CV8 prints for it (tests/native/cv8-prims.4) - tests/verify compares.
native-n1b: forth/native-n1b.4 forth/native.4 forth/native-rt.4 tests/native/prims.4 forth/asm64.4 forth/extend.4 forth/kernel64.img relf64
	@rm -f $@ && ./relf64 forth/kernel64.img < forth/native-n1b.4 > native-n1b.log 2>&1 || true
	@if [ ! -x $@ ] || grep -q 'Undefined word\|native:\|asm64:' native-n1b.log; then \
	    echo "native-n1b: not built:" >&2; tr -d '\r' < native-n1b.log | grep -v '^OK$$' | head -5 >&2; rm -f $@; exit 1; fi
	@rm -f native-n1b.log

# ------------------------------------------------------------------
# The base images: a fixpoint, not a compile. Read the header.
# ------------------------------------------------------------------
check-images:
	@$(MAKE) --no-print-directory images IMAGES_CHECK=1

images: $(NATIVE_ENGINE) $(KERNEL_SOURCES)
	@set -e; \
	for bytes in 8 4; do \
	    case $$bytes in 8) img=forth/kernel64.img ;; 4) img=forth/kernel32.img ;; esac; \
	    wd=$$(mktemp -d); \
	    cp forth/extend.4 forth/cross.4 forth/cross-core.4 forth/kernel.4 $(NATIVE_IMG) $(NATIVE_ENGINE) "$$wd/"; \
	    if [ $$bytes != 8 ]; then \
	        sed -i "s/^8 TARGET-CELL-BYTES !\$$/$$bytes TARGET-CELL-BYTES !/" "$$wd/cross.4"; \
	    fi; \
	    ( cd "$$wd" && printf 'S" extend.4" INCLUDED\nS" cross.4" INCLUDED\nBYE\n' \
	        | ./$(NATIVE_ENGINE) $(notdir $(NATIVE_IMG)) >boot.log 2>&1 ); \
	    if grep -qiE 'undefined word|segmentation fault' "$$wd/boot.log"; then \
	        echo "$$img: cross-compile failed"; cat "$$wd/boot.log"; rm -rf "$$wd"; exit 1; \
	    fi; \
	    if cmp -s "$$wd/built.img" "$$img"; then \
	        echo "$$img: reproduces"; \
	    elif [ "$$IMAGES_CHECK" = 1 ]; then \
	        echo "$$img: DIFFERS from the committed image"; rm -rf "$$wd"; exit 1; \
	    elif [ "$$IMAGES_FORCE" = 1 ]; then \
	        cp "$$wd/built.img" "$$img"; echo "$$img: replaced (IMAGES_FORCE=1)"; \
	    else \
	        echo "$$img: DIFFERS. The sources produce a different image than the"; \
	        echo "         one committed. If that is intended - an engine change,"; \
	        echo "         a forth/kernel.4 change - re-run with IMAGES_FORCE=1 and read"; \
	        echo "         tests/verify's image:*-fixpoint lines afterwards."; \
	        rm -rf "$$wd"; exit 1; \
	    fi; \
	    rm -rf "$$wd"; \
	done

# ------------------------------------------------------------------
# Suites
# ------------------------------------------------------------------
# Each script is run the way its shebang asks: run_tests.sh uses bash
# arrays, `local` and `set -o pipefail`, and `sh tests/run_tests.sh` on a
# machine where /bin/sh is dash fails at line 36 (Iteration 390 - the
# Makefile got this wrong from the start).
test: all
	@bash tests/run_tests.sh

diff: all
	@tests/diff/run-all

matrix: all
	@tests/matrix/run

posix: all
	@sh tests/posix/run.sh

mrsh: all
	@sh tests/mrsh-suite/run.sh

shell: all
	@cd tests/shell && sh ./run-all

interactive: all
	@cd tests/interactive && $(PYTHON) run_cases.py

verify: all
	@sh tests/verify

verify-update: all
	@sh tests/verify --update

# ------------------------------------------------------------------
# External corpora. Neither suite is vendored - they belong to their
# own projects, under their own licences - so each target wants the
# path to a fetched copy. The script headers say how to fetch them.
# ------------------------------------------------------------------
busybox: all
	@test -n "$(BUSYBOX_TESTS)" || { \
	    echo 'set BUSYBOX_TESTS=/path/to/busybox/shell/ash_test'; exit 1; }
	@sh tools/busybox-suite.sh "$(BUSYBOX_TESTS)" "$$(pwd)/relfsh"

yash: all
	@test -n "$(YASH_TESTS)" || { \
	    echo 'set YASH_TESTS=/path/to/yash/tests'; exit 1; }
	@sh tools/yash-suite.sh "$(YASH_TESTS)" "$$(pwd)/relfsh"

# ------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------
# The Advanced Bash-Scripting Guide's examples that dash runs cleanly,
# compared against this shell (Iteration 412). Not vendored:
#   git clone https://github.com/pmarinov/bash-scripting-guide /tmp/absg
ABSG ?= /tmp/absg
absg: all
	@ABSG=$(ABSG) $(PYTHON) tools/absg-suite.py

portability: all
	@sh tests/portability

lint:
	@$(PYTHON) tools/lint-comments.py forth/*.4 shell/*.4 engine/*.4
	@$(PYTHON) tools/lint-tests.py

dead-words: all
	@$(PYTHON) tools/dead-words.py shell/shell.4 shell/edit.4 shell/tree.4

sizes: all
	@sh tests/sizes

profile: all
	@$(PYTHON) tools/profile.py

bench: all
	@sh tests/bench

bundle:
	@name=relf-$$(git rev-parse --short HEAD)-$$(date -u +%Y%m%d-%H%M%S).bundle; \
	git bundle create "$$name" HEAD master cell-engine-final >/dev/null 2>&1; \
	echo "$$name"

# ------------------------------------------------------------------
# Cleaning. The base images and the engine binaries are committed
# artifacts; distclean removes what a build regenerates, and nothing
# removes kernel64.img or kernel32.img.
# ------------------------------------------------------------------
clean:
	@rm -f *.o core boot.log
	@rm -rf build

# The engines go with `clean` now that they are build products rather
# than tracked files: on a machine where the last build was for another
# architecture, keeping them is the fault above (Iteration 402).
	@rm -f relf relf64 relf32 relfsh relfsh64 relfsh32 .relf-arch .relf-native-img
# The assembly engine and what is generated for it (Iteration 552): the
# engine relf assembles, its tables from opcodes.tab, and the files an
# assembly leaves; the names from before 549, when it was GNU as's.
	@rm -f relfasm64 relfshasm64 engine/relfasm-ops.4 engine/relfasm-consts.4 relfasm64.forth relfasm64.log
	@rm -f relfasm-ops.S relfasm-consts.S relfasm64.o
	@rm -f kernel64-shell.img kernel32-shell.img engine/cv8-ops.h.tmp

distclean: clean
	@rm -f kernel64-shell.img kernel32-shell.img
