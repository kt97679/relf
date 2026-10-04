# PROGRESS.md — RelF self-hosting project log

This log exists so future work (including future Claude sessions, which
have no memory of prior ones) doesn't silently retry a path already
found to be wrong. **For project context, priorities, the phase plan and
the register of approaches tried and rejected, read `GOALS.md` first** -
that is the stable reference. The log is what was actually done, in
order, and shouldn't repeat what is stated there.

## How the log is kept (since Iteration 631)

- **The entries live in volumes**, `docs/progress/NNNN-MMMM.md`, a
  hundred iterations each, oldest first. This file is the entry point:
  this policy, the Index, and the list of volumes at the end.
- **A new entry goes at the bottom of the current volume** - the newest
  one in the list - and gets its line in the Index here, in the same
  commit. An entry whose Index line is missing is half written (582-630
  were, and 631 put their lines in).
- **Iteration N00 starts a new volume:** `docs/progress/0N00-0N99.md`,
  with the same four-line header as the others, added to the list
  below. The volume before it is closed from then on.
- **A closed volume never changes.** `tests/verify` records each closed
  volume's `cksum` as a `progress:NNNN-MMMM` row: a new row when a volume
  closes is the one expected change, and any other is a mistake. A wrong
  entry is corrected forward - a new entry, in the current volume, naming
  the one it corrects - never edited where it stands.
- **To find an entry:** the Index below, or `grep -n 'Iteration 138:'
  docs/progress/*.md`. Iteration numbers are global, so a "see Iteration
  138" anywhere in the tree stays good.
- The volumes were cut from one 1.46 MB file at Iteration 631, unchanged:
  concatenated without their four-line headers they are that file's
  entries, byte for byte. The published articles link the branch
  `article-2026`, whose single file is untouched.

The **Index** below is how to use the log: find the entry, read that
entry, don't read the log. It is long because there are many entries,
not because it is padded - and the oldest entries are the ones the other
documents cite most, so nothing is archived or trimmed by age.

## Index

Every entry, in order. Titles are the entries' own. `mrsh a->b`
marks the entries that moved the goal-8 acceptance count; **bold**
marks an entry cited by `GOALS.md`, `FORTH-STYLE.md`,
`PARSE-EXPAND-PLAN.md` or `README.md`, which is the closest thing to a
marker for "still load-bearing". Find an entry by searching for
`Iteration N:`.

### 1-4 — Engine: phases 1, 2, 5, 6

- 1 — scaffolding
- 2 — no-libc x86-64 engine, 8-byte cells
- 3 — phase 5 (libc, native endianness, computed-goto, ARM64)
- 4 — phase 6, i386/32-bit cell width (parameterized, verified working)

### 5-13 — Shell v0.1-v0.8 (phase 7)

- **5** — POSIX shell, v0.1 (process-control primitives + shell.4)
- 6 — shell `-c` mode + a real test suite for shell.4
- 7 — pipes and redirection
- 8 — quoting and escaping
- 9 — $VAR expansion
- 10 — if/then/else/fi
- **11** — while/do/done
- 12 — unset
- 13 — $(...) command substitution

### 14-16 — mrsh suite adopted; phase A

- **14** — adopt mrsh's test suite as goal 8, establish baseline
- **15** — phase A: crash-hardening
- **16** — phase A: script-file invocation (phase A done)

### 17-30 — Phases B and C: semantics and control structures

- **17** — phase B: shell-local variable assignment
- **18** — phase B: ';' (multiple commands per line)
- **19** — phase B: '&&'/'||' (conditional chaining)
- **20** — phase B: command grouping ('( )' and '{ ; }')
- **21** — fix if/while reading from the wrong input source in script-file mode
- **22** — phase B: if/then/else/fi nesting (phase B done)
- **23** — phase C: for/in/do/done loops
- **24** — operators no longer require surrounding whitespace
- **25** — same-line 'if COND; then BODY; fi' support
- **26** — fix a real, pre-existing token-corruption bug in $VAR/$(...) expansion
- **27** — phase C: case/in/esac (with glob-pattern matching)
- **28** — phase C: shell functions (`name() { ... }`)
- **29** — phase C: `return`
- **30** — phase C: `break`/`continue`

### 31-37 — Phases D and F: expansions and the first builtins

- **31** — phase D: positional parameters (`$1`-`$9`, `$#`, `$@`/`$*`, `set`)
- **32** — phase D: parameter-expansion modifiers (default/assign/alternate value, length)
- **33** — phase D: `${VAR%word}`/`${VAR%%word}`/ `${VAR#word}`/`${VAR##word}` (prefix/suffix removal), plus a significant kernel-behavior discovery
- **34** — phase D: tilde expansion
- **35** — phase D: arithmetic expansion (`$((...))`)
- **36** — phase D: `IFS`-based field splitting (Phase D complete)
- **37** — phase F: `:`, `test`/`[` (string, numeric, limited file-existence tests)

### 38-44 — Locals, the prebuilt image, and the arena

- **38** — `locals.4` - named, per-invocation locals
- **39** — converting `shell.4` to locals, and two real deduplications
- **40** — prebuilt shell image - ~128x faster startup, and the acceptance criterion unblocked
- **41** — pool allocator, memory outside the image, and reproducible images
- **42** — replay as an input source - nested constructs inside loop and function bodies
- 43 — per-invocation body storage - loops nest
- **44** — offset-based growable arena - two hardcoded limits gone

### 45-80 — Climbing the mrsh count

- **45** — `#` comments and same-line `; do` - mrsh 2 -> 4 passed  `mrsh 2->4`
- 46 — multi-stage pipelines, `!` negation, and a real pre-existing expansion bug
- **47** — `elif`, and closing a hazard open since Iteration 28
- **48** — `(` and `)` as self-delimiting operators
- **49** — groups as ordinary commands - mrsh 4 -> 6 passed  `mrsh 4->6`
- **50** — duplication audit - two merges, two latent bugs
- 51 — `shift`, `readonly`, `command -v`
- 52 — table-driven DISPATCH, and the `forth` builtin
- 53 — bitwise/shift operators and arithmetic assignment — mrsh 6 -> 7 passed  `mrsh 6->7`
- 54 — the `read` builtin
- 55 — file-descriptor redirection — mrsh 7 -> 8 passed  `mrsh 7->8`
- 56 — here-documents
- 57 — builtins as pipeline stages
- 58 — redirection on pipeline stages
- 59 — `alias` and `unalias`
- 60 — unterminated quotes are a syntax error — mrsh 8 -> 9  `mrsh 8->9`
- 61 — `getopts`, and `set --`
- 62 — subshell function bodies — mrsh 9 -> 10 passed  `mrsh 9->10`
- 63 — nested function definitions
- 64 — multi-line groups — mrsh 10 -> 11 passed  `mrsh 10->11`
- 65 — `return` inside a loop — mrsh 11 -> 12 passed  `mrsh 11->12`
- 66 — field splitting of command substitution, and the assignment exception
- 67 — `$IFS` actually controls field splitting — mrsh 12 -> 13  `mrsh 12->13`
- 68 — `readonly -p` — mrsh 13 -> 14 passed  `mrsh 13->14`
- 69 — `command -v` for reserved words and aliases, and LF-only output
- 70 — line continuation
- **71** — quoting inside `$(...)`
- 72 — braceless compound function bodies, and functions inside `$(...)` — mrsh 14 -> 15 passed  `mrsh 14->15`
- **73** — backquote command substitution
- 74 — background jobs — mrsh 15 -> 16 passed  `mrsh 15->16`
- 75 — same-line `case` arms
- 76 — compound commands as pipeline stages — attempted and reverted, with the design established
- **77** — `DEFER` / `IS`
- 78 — compound pipeline stages, second attempt — reverted
- **79** — third attempt — the isolated diagnostic paid off, and found the *next* obstacle
- 80 — compound pipeline stages — mrsh 16 -> 17 passed  `mrsh 16->17`

### 81-107 — The differential suite, and audits it made possible

- 81 — the alias conformance case is the same conflict
- 82 — auditing the 17 passes for hollowness
- 83 — a differential test suite, and two bugs it found immediately
- 84 — *(number not used)*
- 85 — performance baseline
- **86** — an unquoted empty expansion yields no field
- 87 — a written plan for parse-then-expand
- **88** — a segfault found by the plan's own first step
- 89 — auditing every `DO` — one more hang
- 90 — auditing the fixed tables — a silent failure, a crash, and two limits that pre-empted a diagnosis
- 91 — the recorded and-or reentrancy bug, demonstrated and fixed
- 92 — an operator after `fi`, and the status an untaken `if` leaves
- 93 — multi-line quoted strings
- 94 — is startup cost the reason the loop is slow? No — but the wrapper is 43% of startup
- 95 — positional parameters inside `${...}`, and what `word.sh` actually needs
- 96 — `~user` expansion
- 97 — recording that `~user` via `/etc/passwd` is a shortcut
- **98** — tilde in assignments
- 99 — `$*` lost characters after it
- 100 — `"$@"` as separate fields
- 101 — `done`/`esac` suffixes — diagnosed precisely, not implemented
- 102 — a trailing backslash run, counted by parity
- 103 — the fourth in-place-growth bug, where Iteration 99 predicted it
- 104 — the word in `${VAR:-word}` is word text
- **105** — `$(...)` gets the whole language, by deleting the parser that gave it a subset  `mrsh 17->18`
- 106 — the `done`/`esac` suffix, as specified in 101
- 107 — an unterminated compound command hangs

### 108-121 — Parse-then-expand (PARSE-EXPAND-PLAN.md Stage 1)

- **108** — expansion stops writing over its own input
- **109** — deleting the word rather than auditing its callers
- **110** — one word for normalize-then-tokenize, and the caller that was missing it
- 111 — tokenize the normalized line where it already is
- 112 — word boundaries recorded by the pass that finds them
- 113 — expansion becomes a word you can call later
- **114** — a word is expanded when its command runs  `mrsh 18->19`
- **115** — retire the limitation notes Stage 1 made false  *(written retrospectively in 122)*
- **116** — measuring what Stage 1 cost
- 117 — a loop written entirely on one line
- 118 — a function defined entirely on one line
- **119** — normalizing each line once instead of twice
- **120** — `~user` through NSS instead of /etc/passwd
- **121** — what a fresh machine needs, written down
- 122 — the documents that can rot
- 123 — correcting Iteration 122, from upstream's own harness
- 124 — the reference shell was the ceiling
- **125** — `ulimit`, and goal 8 is met  `mrsh 19->20`
- 126 — a conformance harness scored by consensus, not by bash
- 127 — seven reference shells, and the 32-bit half finally run
- **128** — the size axis of the comparison, as a script
- **129** — where the image bytes actually go, and why Forth being "compact" does not make this the smallest shell
- **130** — what the compiled code is actually made of (`DENSITY-PLAN.md`)
- **131** — correcting the density numbers; longer superinstructions are worth 1.3%
- **132** — two tag bits, and where `LIT` goes
- **133** — how the branch merge would work, and why not to do it
- **134** — keep the dispatch loop, put the payload above the index
- **135** — a review of `shell.4` for size: no duplicated logic, idioms instead
- **136** — every buffer out of the image (i386 total below `dash`)
- **137** — one `LENTER`/`LEXIT` instead of three cells per local (+42% loop, revertable alone)
- **138** — the size comparison was mixing word sizes
- **139** — reading the field: `VM-RESEARCH.md`
- **140** — token threading measured: 3.26x/6.51x smaller, no dispatch cost
- **141** — the prototype: size confirmed, speed 1.14-1.28x and 140's 0.98 was an artifact
- **142** — the token-threading design written out (`TOKEN-THREADING.md`)
- **143** — `ONE-LINE-LOOP?` is a symptom: two conformance bugs, one silent
- **144** — the audit: `until` silently does nothing, plus three more same-line faults
- **145** — why `(`/`)` are not reserved words; `$( (list) )` read as arithmetic
- **146** — a systematic POSIX corpus: 47 cases, eleven new gaps
- **147** — triage: the 21 failures are six faults; stop auditing, start fixing
- **148** — the freeze: reproducible build, `tests/verify`, `tests/BASELINE`
- **149** — revert 137; `GOALS.md` carries the whole plan
- **150** — the shell image did not build from a path over ~36 characters
- **151** — neither stack was bounded; overflow corrupted the dictionary
- **152** — one duplicated block had drifted; `true && {` left status 127
- **153** — the interactive prompt was on stdout, corrupting every piped script
- **154** — two silent failures given diagnostics; a third found (`LINE-MAX`)
- **155** — both images regenerated and checked; `tests/bench` made a measurement
- **156** — encoding comparison against SOD32; the freeze; the data-address finding
- **157** — the speed half: packing costs 20-66%; the threading figure was wrong
- **158** — variable-length tokens, and what the word table costs as it grows
- **159** — token width sweep; the uniform 16-bit token; the derived-table idea
- **160** — the 16-bit token prototype on real code, and a census bug that mattered
- **161** — `ENCODING-COMPARISON.md` regenerated from the fixed census
- **162** — branch `token16`: a translator that proves itself by round trip
- **163** — the dispatch core runs real translated words; the table is derived
- **164** — named SOD16; the gap stated honestly
- **165** — an xt is a word number, and the numbering was backwards
- **166** — `sod16.c`: the whole engine differs from `relf.c` by eight lines
- **167** — re-layout is tractable, because the image is already relative
- **168** — the handoff: `SOD16.md`, and `GOALS.md` brought up to date

### 169-208 — not indexed

The index stops at 168 and the log does not. Entries 169 through 208 -
the whole CV8 arc, from `INNER-INTERPRETER.md` through self-hosting and
`SAVE-SYSTEM` - are in the file but were never added here. Noted rather
than quietly fixed, because "the index is complete" is exactly the kind
of assumption this file exists to stop: search for `Iteration N:` and
do not trust the absence of a line below.

### 209 — the article repository, merged back

- **209** — hashed word list, buffered I/O, and the CV8 toolchain
  reworked for 32 threads
- **210** — the escaped-band fault is a double SPILL; 203-205 corrected
- **211** — layout.py sized every call before anything had an address
- **212** — tails need alignment too; LOC pinning measured and removed
- **213** — the byte-header shell: NAME> must be exact, so pad before the link
- **214-227** — one engine, one read, and four wrong guesses
- **228-236** — conformance, and what the standard's own tests found
- **237-242** — the relf.c retirement, prepared but not done
- **243** — +LOOP fixed; CV8 hosts itself and relf.c is retired
- **244** — byte-granular headers in the product
- **245** — READ and WRITE; the file words move into Forth; five old bugs
- **246** — POLL: KEY waits, KEY? and MS
- **247** — escaped primitives stop costing opcodes; format version 3
- **248** — GOALS.md audited; a too-long line no longer runs its tail
- **249** — growable line buffers; stale values; function bodies; a test that compared nothing
- **250** — the word arrays grow; positional parameters past nine
- **251** — expansion output, command substitution, for lists and here-documents grow
- **252** — variable values and the variable table grow; three stale-state bugs
- **253** — guard pages on by default; the regression was a stack underflow in shell.4
- **254** — RAW-MODE; tests on a pseudo-terminal
- **255** — redirections on builtins and functions; what follows a function call; $$
- **256** — until, eval, for w, NAME=value cmd; nested one-line loops
- **257** — division, ${#}, "$*", case patterns and one-line case; division by zero
- **258** — encoding audit: short backward branches; loops end in a branch; nothing in code aligned
- **259** — variable slots relative to themselves
- **260** — interpreter hot spots: 2SWAP, libc string primitives, DOES> @ inlined
- **261** — COMMAND-TREE-PLAN.md: parse once into a tree, execute the tree
- **262** — test coverage before the rewrite: matrix, interactive, syntax errors, dead code
- **263** — command tree Stage A: tree.4, the lexer and parser; CATCH and THROW
- **264** — command tree Stage B: the executor beside the old path (RELF_TREE=1)
- **265** — command tree Stage C: the tree path is the shell; the line-based shell deleted
- **266** — command tree Stage D: measured; parse-time decisions instead of a tree compiler
- **267** — pathname expansion; directory primitives
- **268** — DASH-COMPARISON.md: how dash runs a script; tools/op-bench.py
- **269** — echo/printf/true/false builtins; exec without fork; command location cache
- **270** — non-whitespace IFS (tests/posix 46/46); set -e -u -x -f -n -o, $-, `.`, exec, type, hash
- **271** — trap and signals; kill, umask, times, local; `set` lists variables; Ctrl-C at the prompt
- **272** — hashed variable index; `set` on an empty table; size lines split
- **273** — EXPANSION-PLAN.md; its Stage 0: trims by substring search; quoted and nested trim patterns
- **274** — expansion Stage A: the lexer encodes each word; tree-dump -e; parse cases
- **275** — expansion Stage B begun: the encoded path for simple words, behind RELF_EXP
- **276** — Stage B continued: every construct on the encoded path; three faults left there
- **277** — Stage B passes both ways: the three faults fixed; a tilde rule corrected
- **278** — splitting by recorded regions; str -16% of the dispatches
- **279** — the walker's cursor and name scan; str -16.9%, loop +3.1%
- **280** — read pForth (mykesforth is unreachable); the headerless-image idea, measured
- **281** — the last three words that could not be encoded; Stage C's precondition met
- **282** — Stage C: the encoded expander is the only one; the scanner deleted
- **283** — command substitutions run from their parsed subtrees (-9% on a substitution loop)
- **284** — measured: compiling arithmetic is not worth it; a second assignment word is split
- **285** — fixed: every assignment in a prefix keeps its value whole
- **286** — expansions inside $(( )) are performed; ~, octal and hex constants
- **287** — coverage probed; the arithmetic audit: ternary, comma, invalid constants
- **288** — read: IFS fields, backslashes, line continuation, end-of-file status
- **289** — cd -, PWD/OLDPWD, alias listing, unalias -a; the probe finishes clean
- **290** — probing job control and signals: trap with a numeric condition breaks the shell
- **291** — the numeric signal bug: one stray NIP; signals get a differential case
- **292** — why dash and bash are faster (PERFORMANCE.md); the builtin table is hashed
- **293** — the expander's per-word bookkeeping; dispatch counts overstate what the clock shows
- **294** — the expansion path's fixed toll; the interpreter's real cost is branch misprediction
- **295** — $0 expanded to nothing; a five-line script that hangs the shell, recorded
- **296** — the hang: `>&-` never closed anything; a failed duplicate went unreported
- **297** — `exec 3>file` opened the file and lost it; the close that followed the open
- **298** — `<>` opens for reading and writing; the rest of the redirection sweep is clean
- **299** — a signal-killed child exits 128+n; the jobs builtin and set -m
- **300** — nested backquotes; a line continuation in $(( )) - a regression from 286
- **301** — a pseudo-terminal harness: the interactive shell is testable, and seven gaps are named
- **302** — PS1/PS2, blank lines, the newline on ^D; an interruptible signal mode
- **303** — a line editor: cursor keys, editing keys and history; the harness renders
- **304** — measured the distance to dash (VERSUS-DASH.md): four features, 7.6x on real work
- **305** — set -a and -v; RESEARCH-VM.md opened; noclobber needs a stat primitive
- **306** — `command NAME args` and `-p` (it only did `-v`); the `-i` flag
- **307** — the `command -p` bug reduced and fixed; `set -C` with a FILE-KIND primitive
- **308** — ulimit over every resource, on new getrlimit/setrlimit primitives
- **309** — job completion notices at the prompt (without the command text yet)
- **310** — the notice's command text: a pipeline keeps its vector in field 1
- **311** — chasing the intermittent job case: what it is not
- **312** — the flakiness was the harness: a prompt has to be stable, not just present
- **313** — the ^C cases: a signal sent while the editor waits is not seen at all
- **314** — ^C at the prompt works: the editor polls instead of blocking
- **315** — ^C during a command; every interactive case now matches dash
- **316** — an assessment: where this shell competes and where it does not
- **317** — POSIX sweep: test's grammar (-a, -o, !, parens) and its file tests
- **318** — command -V, export -p, $PPID; two new primitives
- **319** — cd keeps the logical path; -P, -L and CDPATH
- **320** — fg and bg, process groups and the terminal; the last POSIX builtins
- **321** — foreground process groups; ^Z still does not stop a job
- **322** — ^Z works: an ignored signal is inherited through exec
- **323** — an attempt at the notice's status, reverted; what was measured
- **324** — the notice keeps the job's status: Terminated, not Done
- **325** — character classes in patterns: [[:alpha:]] and the rest
- **326** — dash's manual page as a checklist: unset -f, and readonly unset
- **327** — the pure-sh-bible as a corpus: read at end of input
- **328** — bash's manual where the references agree: getopts operands, ${#*}
- **329** — busybox's ash suite: break n, continue n, and case's exit status
- **330** — behaviours, not files: a catalogue, and functions overriding builtins
- **331** — bash's areas, probed not copied: base#digits, ++ and --
- **332** — the catalogue's own list: here-document substitutions, split operators
- **333** — the last catalogued behaviour: a quoted empty word beside "$@"
- **334** — a command that is only redirections; and a lookahead that asked for input
- **335** — a redirection's target is not field-split
- **336** — exit inside a trap; and zombies reaped while builtins run
- **337** — escapes inside bracket expressions; three more behaviours catalogued
- **338** — a continuation inside a reserved word
- **339** — special parameters in the operator forms; ${#+word}
- **340** — groundwork for case patterns: the glob marks, recorded and gated
- **341** — case patterns keep their quoting, per character
- **342** — return in a loop's condition
- **343** — a length of -1 from the joiner; the here-document hang narrowed
- **344** — an empty redirection target is not dropped
- **345** — wait %n, bare wait's status, and the first substitution in an assignment
- **346** — getopts reports its errors; a backquote crash catalogued
- **347** — the backquote crash re-measured: the text, not the output
- **348** — the backquote crash fixed: a re-fetch outside its test
- **349** — assignments beside a redirection reach the shell
- **350** — the other order of assignment and redirection; command's options
- **351** — a pool for here-document bodies; numbered ones catalogued
- **352** — assessed the recognizer mechanism: not for this shell, and why
- **353** — CSTR," replaces 26 byte-built literals
- **354** — tests for CSTR," itself; one more measurement on the numbered here-document
- **355** — four fixes: numbered here-documents, background stdin, trap return, quoted empty fields
- **356** — the length of a special parameter; command's not-found report
- **357** — assignments applied left to right as they expand; readonly reports
- **358** — positional parameters are fields, not a space-joined string
- **359** — an empty quoted field: measured, attempted, reverted
- **360** — a bare return in a trap; and where the splitting really happens
- **361** — an empty quoted field is a field
- **362** — assessed Lisp, Lua and MicroPython as substrates: no, and why
- **363** — quotes in a ${} word: literal in a value, quoting in a pattern
- **364** — quoting inside a run of whitespace
- **365** — re-profiled and three hot words fixed: -6.7% dispatches, -2.9% time
- **366** — the name validator; and bundles that can be pulled
- **367** — AND does not short-circuit; and a `[` is not always a pattern
- **368** — a runaway directory, ten documents to the attic, and an index
- **369** — here-document delimiters, `<<-` continuations, quoted dashes in brackets
- **370** — quoted brackets, and dashes from expansions
- **371** — stale marks from the aside capture; escapes in a ${} word
- **372** — a pending split through the bulk emitter; saved descriptors; PARITY with dash
- **373** — a variable-lookup cache: built, measured, reverted
- **374** — what the bookkeeping costs: 1%, so the refactor is off
- **375** — yash's POSIX suite, and the two invocation forms it wanted
- **376** — a special builtin's error ends the shell: GOALS 5k decided
- **377** — the shell's own command line, parsed properly: +204 cases
- **378** — file-type tests, an engine primitive, and a FIFO that hung the shell
- **379** — umask's symbolic forms, and three POSIX rules from yash
- **380** — four arithmetic bugs: short-circuiting, signs, shifts, assignments
- **381** — CDPATH's two rules, and a tilde in a ${} word; busybox 212, past dash
- **382** — aliases after prefixes, and aliases that expand to nothing
- **383** — redirection errors on special builtins; yash's error suite complete
- **384** — a Makefile, and the benchmark script moved into the tree
- **385** — a redirection before the assignments
- **386** — `set -b`, and `set -v` that actually does something
- **387** — the yash corpus runner, and both corpora wired into the Makefile
- **388** — aliases that expand to reserved words; ahead of dash on both corpora
- **389** — prompts are expanded; and LD_PRELOAD cleared for the i386 build
- **390** — two faults in the test setup, both reported from outside
- **391** — tests for the scaffolding; PS4; CHECKING.md
- **392** — the suites inherited the terminal, and waited there
- **393** — a baseline that travels: machine-dependent lines, and the locale everywhere
- **394** — a suite that died silently; and the i386 half as a host fact
- **395** — a test that asserted the machine's HOME
- **396** — a loader message inside the test output
- **397** — a 32-bit HOST, where kernel.img is the wrong image
- **398** — the core suite on a 32-bit host: native and other, not 8 and 4
- **399** — a machine with no dash: four suites that assumed one
- **400** — bash clears PS1, so the wrapper never sees it
- **401** — the most negative cell, printed backwards through memory
- **402** — the engines leave the repository
- **403** — undefined shifts in the cross-compiler; and a dead-word regression
- **404** — a prompt channel bash cannot strip; and three honest counts
- **405** — the board verifies clean; and the widening bug located to one offset
- **406** — the pty suite had a clock assumption of its own
- **407** — bytecode out of the repository; a prompt library; the editor's gaps named
- **408** — history holds the session; and a line is no longer 256 characters
- **409** — ^R: reverse incremental history search
- **410** — a build that saves a broken image fails now, and says why
- **411** — TAB completes filenames
- **412** — Home/End under tmux; bash's prompt escapes; a guide's worth of examples
- **413** — test's integer operands; .gitignore in the handoff prompt and the suite
- **414** — TAB completes command names; the listing is sorted
- **415** — the widening cross-compile, fixed; and the lead that pointed the wrong way
- **416** — the board confirms the widening fix; TAB on an empty line was slow there
- **417** — FORTH-STYLE catches up; the fourth host/target combination; the prompt's clock
- **418** — completing a word that already holds an escaped blank
- **419** — the function and alias tables grow; both complete as commands
- **420** — completing inside quotes; a case-pattern crash found and recorded
- **421** — four crashes fixed; a crash fuzzer; the corpora ranked by severity
- **422** — a value dimension for the matrix; test's counted rules; export, IFS, OPTIND, read
- **423** — case patterns and subjects are not field-split; many_ifs passes
- **424** — command takes special properties away; backslashes in case patterns
- **425** — the log that stops retries; the documents deduplicated against prompts/
- **426** — the fuzzer's two crashes: a swallowed EXIT, and a job table that grew two arrays of five
- **427** — an arithmetic error ends a non-interactive shell; 257's choice reversed on evidence
- **428** — a backslash from an expansion escapes in pathname expansion
- **429** — line continuation inside $ constructs
- **430** — the corpora re-run; fields out of order in a braced word: diagnosed, attempted, reverted
- **431** — the braced-word fix, finished: one splitter, and quotes placed before the blanks they precede
- **432** — set -a for the shell's own assignments; OPTARG unset; the dot builtin as a special builtin
- **433** — a file with no #! line is run as a script, by this shell
- **434** — skipping a nested word; ${1:=x} is an error; ${#:=x}; an assertion that could not exist
- **435** — a tilde is not split; a lone - is ignored; $0 is the invocation name
- **436** — yash 1699/76; a regression from 435 caught; $0 through a wrapper; ${...} in here-documents; test's -a and -o; write errors
- **437** — any assignment to PATH forgets where commands were
- **438** — busybox 216; \" in double-quoted backquotes; command exec keeps its redirections
- **439** — set -v echoes each line once; THIS_SH made absolute for every test
- **440** — a captured word takes its regions with it; an operator needs an operand
- **441** — cd's options, every letter; "$@""$@" with no parameters is no field
- **442** — a trim's pattern is a context of its own: tildes, and substitutions that match
- **443** — command's options, alone or combined; -p with -v
- **444** — reserved words are not aliases; a vanished alias leaves the command owed
- **445** — yash 1723; a continuation before a length `#`; a nested brace's quoting left behind
- **446** — busybox 218; break and continue in a loop's condition
- **447** — a trap that never ran; a wait that never noticed a signal
- **448** — 447's other half: a trap belongs between commands, not inside one
- **449** — busybox 219; $! is the last process of a background pipeline
- **450** — yash 1724; an unquoted ${#a} is field-split
- **451** — many_ifs profiled: flat; a child no longer resets traps it has none of
- **452** — the same alias again after a trailing blank
- **453** — yash 1727; alias names: odd characters, and continuations in them
- **454** — yash 1738; a candidate word is a candidate anywhere
- **455** — busybox 220; an alias that continues the construct around it
- **456** — yash 1739; a line continuation in an IO number
- **457** — busybox 242 with THIS_SH set; ${##1}; a continuation in a function name
- **458** — busybox 247; a signal that kills a command is named; a redirection target joins
- **459** — yash 1742; a bracket expression that never closes is a literal [
- **460** — a backslash is not a delimiter; an operator may be split by a continuation
- **461** — yash 1745; a pending here-document belongs to the command around a substitution
- **462** — a reserved word is not an alias only where one would be reserved
- **463** — yash 1747; a quoted `!` or `^` in a bracket expression
- **464** — a here-document's continued line is not its terminator
- **465** — a test asked the host which shell `sh` is; the 8-byte rows on a 32-bit host
- **466** — descriptors of two digits or more
- **467** — a word that looks like a descriptor is not one
- **468** — busybox 249; a trap may run inside a trap
- **469** — a name exported before it has a value; GOALS.md pruned
- **470** — the intermittent differential case: bash's own race
- **471** — a differential fuzzer; three field-splitting bugs it found
- **472** — a wider fuzzing grammar; the rest of test's two-argument rule
- **473** — set -o pipefail (POSIX.1-2024)
- **474** — $'...' (POSIX.1-2024)
- **475** — LINENO
- **476** — \j and \D{format} in prompts
- **477** — a lint for tests that run the host's sh
- **478** — the fuzzer's third grammar: 25133 scripts, clean
- **479** — EXPANSION-ORDER.md: the design, before the code
- **480** — the words before the assignments (stage 1)
- **481** — yash 1751; a fuzzing family for stage 1, with teeth; stage 2's obstacles
- **482** — a regular builtin's redirections before its assignments (stage 2)
- **483** — yash 1752, busybox 255; a command inherits the script's high descriptors
- **484** — where the references part company on expansion order
- **485** — found: a script descriptor at 64 or above can be overwritten
- **486** — saved descriptors from the kernel (a new engine primitive), not fixed slots
- **487** — the Tegra verifies 486; the matrix asks bash for POSIX mode
- **488** — two open items restored to GOALS.md, deleted by accident at 476
- **489** — repository cleanup, part 1: only the files that are needed
- **490** — the engine source: three dead macros, and comments that pointed at nothing
- **491** — CV8.md: one document for the engine, checked against the source
- **492** — DASH.md, measured afresh; PERFORMANCE.md takes the research questions
- **493** — GOALS.md to the present; README rewritten; every document one topic
- **494** — the tests' own files: one empty stray, one undocumented probe
- **495** — the 1.8x drift bisected; the profiler and coverage tools, broken at 490, fixed
- **496** — the three unaudited areas: prompts/, three documents read through, the tests' documents
- **497** — two decisions of the user's recorded: prompts/ is kept whole, and an article is planned
- **498** — a check broken for 190 iterations: the long-path image build lacked edit.4
- **499** — the user's list for what comes next, recorded with its open questions
- **500** — the user's answers to 499's questions, recorded as decisions
- **501** — the opcode experiment: a 1 GB code space would cost nothing measurable
- **502** — where the POSIX language's cost lives: no feature halves it; re-read text is the trouble
- **503** — Rill: a shell language designed from 502's measurements
- **504** — startup files: /etc/profile, ~/.profile and $ENV, as dash reads them
- **505** — forth-shell-examples: new builtins, PROMPT_COMMAND, and servers, with TCP in the engine
- **506** — relfsh is a binary: the engine with the shell image inside it
- **507** — everything named by cell width: relf64/relf32, kernel64/kernel32, relfsh64/relfsh32
- **508** — the ARMv7 board on 507: two things the rename left for a 32-bit host
- **509** — the space audit: 2 KB in full cells, and headers are a fifth of the image
- **510** — the source audit, first pass: four duplicates merged, four untested paths tested
- **511** — the audit's second pass: two helpers extracted, and `[`'s error found on stdout
- **512** — the audit's third pass: one PATH search, one file reader - and a documented trap walked into
- **513** — the assembly engine designed: 63 libc functions, and a Milestone 0 in C
- **514** — QUESTIONS.md; 256-column lines; Rill specified; the assembly engine's decisions
- **515** — Rill discussed: structured values across processes, and jobs with lifetimes
- **516** — JSON in the environment, recognised by use; what a process can exchange; plugins; Q2-Q4 answered
- **517** — the locals save stack moves into the engine: five cells become one; format 6
- **518** — the opcode map has one source: opcodes.tab; tables generated, the Forth checked
- **519** — the assembly engine's Milestone 1: the core, identical to cv8.c on the CORE suite
- **520** — the board's gawk finding fixed; the assembly engine made minimal: 11 KB, one segment
- **521** — the assembly engine's Milestone 2: kernels, CORE suite and shell image all identical
- **522** — the shell runs on the assembly engine: 130 of 131 differential cases
- **523** — the assembly engine complete: every primitive, every suite, W^X, one 135 KB file
- **524** — measured: the assembly shell is faster on shell work and starts 2.5x faster than dash
- **525** — the assembly engine joins make verify on x86-64 hosts: eight rows
- **526** — the dispatch loop measured: both engines on the indirect-jump floor; tuning left out
- **527** — superinstruction candidates measured: 21% from 32 pairs, ~20% from eight runtime words
- **528** — +! an opcode: 2.19% fewer dispatches; format 7; unassigned opcodes trap; the cold end tracked
- **529** — ?DUP an opcode: 2.63% fewer dispatches; the loop words' failure diagnosed
- **530** — the loop words as opcodes: I, (LOOP), (?DO) - 13.9% fewer dispatches since 528
- **531** — EXECUTE and @XT as opcodes: 14.95% fewer dispatches since 528
- **532** — the first superinstructions: VAR@ fused with +, <, 1+, C@ - 4.62% fewer; 18.9% since 528
- **533** — decoders read operand formats from opcodes.tab; compare-and-branch fused: 3.40% fewer, 21.6% since 528
- **534** — measured in time against 527, dash and bash; BUF-ZERO is 0 FILL
- **535** — optimization stopped (A13); self-hosting proposed: SELF-HOSTING.md, Q17
- **536** — simplified: nine superinstructions and four unused folds gone; 111 one-byte opcodes -> 98; format 8
- **537** — self-hosting M0 groundwork: the reference corpus, 450 instruction shapes with GNU as's bytes
- **538** — no folded returns: 22 opcodes and handlers gone, a body ends in EXIT; 98 one-byte opcodes -> 76; format 9
- **539** — 64 one-byte opcodes: nine cold primitives escaped, CHAR+ INVERT ALIGNED colon words; format 10
- **540** — the reference corpus from GNU as's listing: 453 real instruction shapes, no data taken for code
- **541** — M0 begun: asm64.4, the Forth assembler's first encoder, and tools/asm-test.py
- **542** — M0's encoder complete: 452 of 452 shapes; gforth builds both kernels identical; relf against C, Go, Python, Ruby
- **543** — findings captured (FINDINGS.md); seven benchmarks against gforth, pforth and five languages; one-pass assembler designed
- **544** — UTC everywhere (A16); verify runs in TZ=UTC-9; why gforth is faster; the region against the call reach (Q19)
- **545** — the region is 4 MB, the call reach (A17); UNUSED, ALLOT checked; memory measured against dash, ash, bash; OPTIMIZATIONS.md
- **546** — M1 complete: an ELF executable written entirely from Forth exits 42; CHMOD; relfsh's memory captured for after self-hosting (A18)
- **547** — M2 done: the whole engine translated (0 lines left); M3 begun - it assembles, 4 short jumps still too far
- **548** — SELF-HOSTED: relf assembles its engine identical to GNU as's (M3), and that engine rebuilds itself (M4)
- **549** — M5: the engine's only source is Forth (relfasm64.4); GNU as leaves the build; ANNOUNCEMENT.md
- **550** — the user's runs of 549: two findings - untracked generated files; a suite that inherited the caller's PS1
- **551** — relfsh's memory a third less: ALLOCATE's memory zero, the buffers carved from one arena (308 -> 196 kB idle)
- **552** — polish: compile-only words refuse outside a definition; `.(`; make clean; TESTING-IDEAS.md
- **553** — coverage of every source; prompt 14; ForthHub audience research; A23
- **554** — a Forth error fails its command only (A24): CATCH/THROW in the kernel, errors to stderr; CONVERT fixed; coverage 67 → 13 words never run
- **555** — the tree restructured: engine/, forth/, shell/, docs/, examples/; README rewritten
- **556** — traps THROW (A26: a zero divisor fails its command); compile-only words by a list of xts (A27); names over 31 refused
- **557** — coverage 9 words never run (93%); editor keys tested through a pty; tools/metamorph.py: 1,170 rewritings, 0 findings
- **558** — relf runs its own harness (940 assertions, both engines); a parliament of seven shells: relf never against a strong majority
- **559** — tools/shfuzz.py: 1,000 random programs, 0 findings (yash in relf's seat: 9); mutation survivors read - bg on a second job was untested, now a pty case
- **560** — the pty suite 219 s -> 48 s; strange environments: the assembly engine crashed under any ulimit -v below 1 GB - fixed
- **561** — PATH unset: dash's default (A28); the command search reads the PATH variable, exported or not
- **562** — set lists inherited variables (sorted, as dash); A29: no empty PATH entry searches the current directory
- **563** — signal storms (tools/chaos.py; run-signal-storm): every trap run, every sum exact; the address-space floor measured; round trips of set, export -p, trap, alias
- **564** — the user's fury and rage runs: a job-notice race I had recorded as fact (fixed); completion checks on rage wait for their result
- **565** — a here-document bug found by ncurses's configure: fixed; that 32,301-line script now runs as under dash
- **566** — the assembler against GNU as at random: memory push, pop and xchg were assembled as register ones, silently - fixed; asm:fuzz-mismatches
- **567** — the line editor against bash's readline: a blank line made the next prompt PS2 (fixed); word keys missing (Q30); POSIX's own examples, 33 checks
- **568** — the word keys (A30): C-w, M-b, M-f, M-d, M-Backspace, C-y with a kill buffer; 81 of 88 keystroke tests as bash, the 7 left deliberate
- **569** — the special built-ins' POSIX examples, 31 checks: readonly lost its flag on inherited variables, and readonly -p did not quote - both fixed
- **570** — the announcement article, drafted for ForthHub (docs/ARTICLE-forthhub.md)
- **571** — Ctrl-C stops the command line (A31): loops, lists, subshells, command substitution, `wait`, and a runaway Forth word; 5 pty cases
- **572** — fury and rage: intr-subshell's fresh line was a race; a child dead of ^C now gives it; a child that survives the ^C lets the line go on, as dash (a case)
- **573** — PWD at startup, as XCU 2.5.3 (A32): set and exported under env -i, a stale or dotted one replaced; FILE-MODE gives inode and device
- **574** — output that ends without a newline stays: the editor redraws from the prompt's start, not column 0 (2 pty cases)
- **575** — the line editor works in characters: UTF-8 text moves, deletes and counts columns as characters, Cyrillic words are words (4 pty cases)
- **576** — measured again, as the reviews asked: a static musl dash is as small as relfsh and starts faster; at a size where startup does not dominate, scripts run 41-59x slower than dash, not 20-28x
- **577** — tools/bench-report.sh: the article's numbers on any machine, into one report; the benchmarks skip what is not installed
- **578** — the articles corrected, both: calls base-relative, what a trap does and does not catch, the fuzzer's 173 set aside, the opcode question's prior art, authorship, the static dash, sizes; the README's sizes
- **579** — the numbers section, both articles, from fury's full report: a named CPU, the static dash, workloads 25 times larger, every Forth and language; Z3 re-modelled with unsigned backward calls
- **580** — examples/map.4, an associative array as a builtin; the testing list explained (the matrix's contexts, the parliament's seven shells and majority, mutation testing's 20 of 30); about 210 kB
- **581** — the articles' links point at the branch article-2026, the version they describe; Try it clones it

### 582-607 — the published shell: fixes, fuzzers, the announcement

- 582 — an unbalanced stack fails its command
- 583 — the seventh review, in both articles
- 584 — the bundle's name, made by a script
- 585 — fury's numbers after 582
- 586 — stack overflow fails its command; the eighth review's code
- 587 — the eighth review in both articles
- 588 — the machine-written passages, and Thompson explained
- 589 — the forth prompt's own stack
- 590 — the ninth review in both articles
- 591 — including under CATCH
- 592 — the tenth review in both articles
- 593 — the include buffer's bound
- 594 — the numbers 593 changed
- 595 — a fuzzer for the forth builtin, and the gap
- 596 — the claim scoped to what the system detects
- 597 — the new row where the engine does not run
- 598 — ^C at random moments
- 599 — the size 598 changed
- 600 — a key typed after ^C belongs to the next line
- 601 — the return stack, and a jump into what is not code
- 602 — Forth calling back into the shell
- 603 — readonly on an unset name; and the campaign before it
- 604 — characters of two columns, and of none
- 605 — the benchmark report on a 32-bit host
- 606 — a ^C that came before the forth builtin was ready
- 607 — the ForthHub announcement, recorded

### 608-631 — the native back end: N0, N1 and N2 begun

- 608 — N0 - a native-code back end, designed
- 609 — A33 - the native back end's decisions
- 610 — N1a - the first native program
- 611 — N1b-1 - CV8's computational primitives, native
- 612 — N1b-2 - the rest of what kernel.4 calls
- 613 — N1c-0 - kernel.4, mapped for the native kernel
- 614 — no split of kernel.4 - the native side substitutes
- 615 — N1c-1a - cross.4's shared core
- 616 — N1c-1b - target headers over native code
- 617 — ^C held while INCLUDED takes its file
- 618 — N1c-1c - kernel.4's first quarter, native
- 619 — N1c-2a - kernel.4 through part 8, native
- 620 — three faults in the native cross compiler
- 621 — parts 4-8's words, tested against CV8
- 622 — N1c-2b - part 9, its back end skipped
- 623 — N1c-2c - the native kernel's own compiler
- 624 — N1c-3 - the native kernel boots, and passes CORE
- 625 — N2 begins - the first measurement
- 626 — data off code's cache lines
- 627 — against C, and pushes inline
- 628 — literals folded into the next operation
- 629 — a compare fused with its branch; OVER fused with its operation
- 630 — DO loops in registers
- 631 — housekeeping: the log in volumes; three new prompts, four amended
- 632 — a lint for the native compiler's sources, and its self-test
- 633 — N2: the native shell's primitives inventoried; one source for them, relfasm64.4
- 634 — 22 primitives generated from the asm engine's handlers; 21 to go, and why
- 635 — 42 of 43: closures, the data chain re-rooted, the start's capture
- 636 — SIGNAL-ACTION natively: the last of the 43
- 637 — the shell's own Forth runs natively: shadow.4's locals through a native OP, and SLOT,
- 638 — the native shell saved (relfsh-native); the differential suite 132 of 132
- 639 — the traps natively, the engine's stack layout and guard pages: run-forth-errors 69 of 69
- 640 — the main shell suite passes natively; every primitive the engine has, ported
- 641 — every suite natively: pty, mrsh, posix, both fuzzers - N2's shell complete
- 642 — the native shell's speed: 8.5-8.8 times CV8's, 4.5-6.3 times dash's time

### Not tied to an iteration

- 2026-09-01 — Design discussion: phase 5 direction, and a rejected byte-opcode idea
- Assessment: reusing mrsh's test suite

---

## Volumes

| volume | iterations | state |
|---|---|---|
| `docs/progress/0001-0099.md` | 1-99, with the phase 5 design discussion and the mrsh assessment | closed |
| `docs/progress/0100-0199.md` | 100-199 | closed |
| `docs/progress/0200-0299.md` | 200-299 | closed |
| `docs/progress/0300-0399.md` | 300-399 | closed |
| `docs/progress/0400-0499.md` | 400-499 | closed |
| `docs/progress/0500-0599.md` | 500-599 | closed |
| `docs/progress/0600-0699.md` | 600- | **current** |
