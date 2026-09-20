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
# It does not rebuild kernel.img as a matter of course. That image is
# simultaneously the image cross.4 PRODUCES and the image cross.4 RUNS
# ON: rebuilding it is a fixpoint step, not a compile, and a wrong one
# is not a broken build but a subtly different shell. `make images`
# does it deliberately, into a temporary directory, and refuses to
# install the result unless it is byte-identical or IMAGES_FORCE=1 is
# given. `make check-images` is the read-only half, and tests/verify
# checks it on every run.
#
# The four .img files and the two engine binaries are COMMITTED, which
# is why `make clean` leaves them alone; `make distclean` is the one
# that removes build products, and even it does not touch the base
# images.

CC      ?= cc
CFLAGS  ?= -O2 -Wall
# The i386 engine is built non-PIE: PIE costs it the TOS register, and
# README.md's compilation section has said so since Iteration 243.
CFLAGS32 ?= -m32 -O2 -Wall -fno-pie -no-pie
PYTHON  ?= python3

SHELL_SOURCES = extend.4 pool.4 shadow.4 save-system.4 shell.4 edit.4 tree.4
KERNEL_SOURCES = kernel.4 cross.4 extend.4

.PHONY: all help engines shell-images images check-images \
        test verify verify-update diff matrix posix mrsh shell interactive \
        lint dead-words sizes profile bench bundle clean distclean

all: engines shell-images

help:
	@echo 'Targets:'
	@echo '  all            engines and shell images (the default)'
	@echo '  engines        relf and relf32 from cv8.c'
	@echo '  shell-images   kernel-shell.img and kernel32-shell.img'
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
	@echo '  lint           comment lint over the Forth sources'
	@echo '  dead-words     unreachable definitions'
	@echo '  sizes          this shell against every other one installed'
	@echo '  profile        dispatch counts per word, on a realistic script'
	@echo '  bench          speed against the reference shells'
	@echo '  bundle         a git bundle of master, HEAD and the tag'
	@echo ''
	@echo '  clean          build products; distclean also the shell images'
	@echo ''
	@echo 'External corpora (not in this tree): tools/busybox-suite.sh.'

# ------------------------------------------------------------------
# Engines
# ------------------------------------------------------------------
engines: relf relf32

relf: cv8.c
	$(CC) $(CFLAGS) -o $@ $<

relf32: cv8.c
	$(CC) $(CFLAGS32) -o $@ $<

# ------------------------------------------------------------------
# Shell images
#
# relfsh builds these itself when they are older than their sources -
# these rules just give make the same dependency list, so `make` after
# editing shell.4 leaves a current image behind rather than making the
# next command pay for it.
# ------------------------------------------------------------------
shell-images: kernel-shell.img kernel32-shell.img

kernel-shell.img: relf kernel.img $(SHELL_SOURCES)
	@./relfsh -c true </dev/null >/dev/null

kernel32-shell.img: relf32 kernel32.img $(SHELL_SOURCES)
	@RELF_BIN=./relf32 RELF_IMG=./kernel32.img ./relfsh -c true </dev/null >/dev/null

# ------------------------------------------------------------------
# The base images: a fixpoint, not a compile. Read the header.
# ------------------------------------------------------------------
check-images:
	@$(MAKE) --no-print-directory images IMAGES_CHECK=1

images: relf $(KERNEL_SOURCES)
	@set -e; \
	for bytes in 8 4; do \
	    case $$bytes in 8) img=kernel.img ;; 4) img=kernel32.img ;; esac; \
	    wd=$$(mktemp -d); \
	    cp extend.4 cross.4 kernel.4 kernel.img relf "$$wd/"; \
	    if [ $$bytes != 8 ]; then \
	        sed -i "s/^8 TARGET-CELL-BYTES !\$$/$$bytes TARGET-CELL-BYTES !/" "$$wd/cross.4"; \
	    fi; \
	    ( cd "$$wd" && printf 'S" extend.4" INCLUDED\nS" cross.4" INCLUDED\nBYE\n' \
	        | ./relf kernel.img >boot.log 2>&1 ); \
	    if grep -qiE 'undefined word|segmentation fault' "$$wd/boot.log"; then \
	        echo "$$img: cross-compile failed"; cat "$$wd/boot.log"; rm -rf "$$wd"; exit 1; \
	    fi; \
	    if cmp -s "$$wd/kernel.img" "$$img"; then \
	        echo "$$img: reproduces"; \
	    elif [ "$$IMAGES_CHECK" = 1 ]; then \
	        echo "$$img: DIFFERS from the committed image"; rm -rf "$$wd"; exit 1; \
	    elif [ "$$IMAGES_FORCE" = 1 ]; then \
	        cp "$$wd/kernel.img" "$$img"; echo "$$img: replaced (IMAGES_FORCE=1)"; \
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
test: all
	@sh tests/run_tests.sh

diff: all
	@tests/diff/run-all

matrix: all
	@tests/matrix/run

posix: all
	@sh tests/posix/run.sh

mrsh: all
	@bash tests/mrsh-suite/run.sh

shell: all
	@cd tests/shell && ./run-all

interactive: all
	@cd tests/interactive && $(PYTHON) run_cases.py

verify: all
	@sh tests/verify

verify-update: all
	@sh tests/verify --update

# ------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------
lint:
	@$(PYTHON) tools/lint-comments.py *.4

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
# removes kernel.img or kernel32.img.
# ------------------------------------------------------------------
clean:
	@rm -f *.o core boot.log
	@rm -rf build

distclean: clean
	@rm -f kernel-shell.img kernel32-shell.img
