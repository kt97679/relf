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
NATIVE_IMG       = kernel32.img
NATIVE_SHELL_IMG = kernel32-shell.img
OTHER_SHELL_IMG  =
else
NATIVE_ENGINE    = relf64
NATIVE_IMG       = kernel64.img
NATIVE_SHELL_IMG = kernel64-shell.img
OTHER_SHELL_IMG  = kernel32-shell.img
endif
# The i386 engine is built non-PIE: PIE costs it the TOS register, and
# README.md's compilation section has said so since Iteration 243.
CFLAGS32 ?= -m32 -O2 -Wall -fno-pie -no-pie
PYTHON  ?= python3

SHELL_SOURCES = extend.4 pool.4 shadow.4 save-system.4 shell.4 edit.4 tree.4
KERNEL_SOURCES = kernel.4 cross.4 extend.4

.PHONY: all help engines shell-images shells images check-images \
        test verify verify-update diff matrix posix mrsh shell interactive \
        busybox yash absg portability lint dead-words sizes profile bench bundle \
        clean distclean

all: engines shell-images shells

help:
	@echo 'Targets:'
	@echo '  all            engines and shell images (the default)'
	@echo '  engines        relf64 and relf32 from cv8.c'
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
cv8-ops.h: opcodes.tab tools/gen-opcodes.sh
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
relf64: cv8.c cv8-ops.h .relf-arch
	$(CC) $(CFLAGS) -o $@ $<
endif

ifeq ($(HOSTBITS),32)
relf32: cv8.c cv8-ops.h .relf-arch
	$(CC) $(CFLAGS) -o $@ $<
else
relf32: cv8.c cv8-ops.h .relf-arch
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
kernel64-shell.img: relf64 kernel64.img $(SHELL_SOURCES) tools/build-shell-image.sh
	@sh tools/build-shell-image.sh ./relf64 kernel64.img $@ $(SHELL_SOURCES)
endif

# LD_PRELOAD is cleared for the i386 build: a preload library for the
# host architecture can never be loaded into a 32-bit process, and the
# loader says so - noisily - on every invocation. Ubuntu and Mint set
# one system-wide (libgtk3-nocsd), so this is most people's first
# impression of `make` (Iteration 389).
ifeq ($(HOSTBITS),32)
# The native engine IS the 4-byte one here: there is no -m32 build, and
# relf32 is built natively.
kernel32-shell.img: relf32 kernel32.img $(SHELL_SOURCES) tools/build-shell-image.sh
	@LD_PRELOAD= sh tools/build-shell-image.sh ./relf32 kernel32.img $@ $(SHELL_SOURCES)
else
kernel32-shell.img: relf32 kernel32.img $(SHELL_SOURCES) tools/build-shell-image.sh
	@LD_PRELOAD= sh tools/build-shell-image.sh ./relf32 kernel32.img $@ $(SHELL_SOURCES)
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
relfasm-ops.S: opcodes.tab relfasm64.S tools/gen-opcodes.sh
	@sh tools/gen-opcodes.sh --asm relfasm64.S > $@.tmp && mv -f $@.tmp $@

# Linked to raw bytes: the source carries its own ELF header and single
# program header (Iteration 520, after kt97679/itsy-linux), so nothing
# of the linker's layout - sections, their table, page padding - is kept.
relfasm64: relfasm64.S relfasm-ops.S
	$(CC) -c -o relfasm64.o relfasm64.S
	ld -Ttext=0x400000 --oformat binary -o $@ relfasm64.o
	@chmod +x $@ && rm -f relfasm64.o
	@[ $$(wc -c < $@) -lt 65536 ] || { echo "relfasm64 outgrew 64 KB: move BSS_BASE and VM_OFF up in relfasm64.S" >&2; rm -f $@; exit 1; }

# ------------------------------------------------------------------
# The base images: a fixpoint, not a compile. Read the header.
# ------------------------------------------------------------------
check-images:
	@$(MAKE) --no-print-directory images IMAGES_CHECK=1

images: $(NATIVE_ENGINE) $(KERNEL_SOURCES)
	@set -e; \
	for bytes in 8 4; do \
	    case $$bytes in 8) img=kernel64.img ;; 4) img=kernel32.img ;; esac; \
	    wd=$$(mktemp -d); \
	    cp extend.4 cross.4 kernel.4 $(NATIVE_IMG) $(NATIVE_ENGINE) "$$wd/"; \
	    if [ $$bytes != 8 ]; then \
	        sed -i "s/^8 TARGET-CELL-BYTES !\$$/$$bytes TARGET-CELL-BYTES !/" "$$wd/cross.4"; \
	    fi; \
	    ( cd "$$wd" && printf 'S" extend.4" INCLUDED\nS" cross.4" INCLUDED\nBYE\n' \
	        | ./$(NATIVE_ENGINE) $(NATIVE_IMG) >boot.log 2>&1 ); \
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
	        echo "         a kernel.4 change - re-run with IMAGES_FORCE=1 and read"; \
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
	@$(PYTHON) tools/lint-comments.py *.4
	@$(PYTHON) tools/lint-tests.py

dead-words: all
	@$(PYTHON) tools/dead-words.py shell.4 edit.4 tree.4

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

distclean: clean
	@rm -f kernel64-shell.img kernel32-shell.img
