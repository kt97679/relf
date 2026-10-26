# Rill's roadmap (Iteration 762)

The order comes from what the three pilots measured
(docs/PILOT-NATIVE-BY-SOURCE.md): the cheapest fixes first, then the cause
behind most of Rill's defects and much of its slowness, then the open
gaps, then speed, then putting Rill to work. Each phase is measured as the
last iterations were: the search's four criteria (docs/RILL-SEARCH.md),
and defect logs on real scripts.

## Phase 1: catch the slips the pilots found - done in 762

- A bare word that names a variable, in an expression, is an error in both
  compilers ("x is a variable - $x, or "x" for the text"); in a command's
  arguments a bare word is its text, as before. It catches the three `$`
  slips of the pilots, and found a fourth no output check had: dead-words'
  `[e for e in ...]`, a list of the text "e", hidden while no IS line was
  dead.
- tools/rill-forth-lint.py reports a name defined again that the kernel
  has, or, in a program (.fth), that the runtime has - the pilots' CURRENT,
  KILL, BASE and PARSE; and it found three in the compiler itself, DEPTH,
  LIT and SRC, now SM-DEPTH, TEXT-LIT and RS-SRC. `[']` in a definition is
  no longer reported in a program loaded when it runs.
- tests/rill/pilots.rill holds each defect the pilots found in Rill;
  tests/rill/errors/ the programs both compilers must reject;
  tests/rill/pilots/is-lines.4 the IS-line case dead-words' three versions
  now agree on.

## Phase 2: kinds for lists and records - designed in 763 (docs/RILL-KINDS.md)

The first attempt, kinds decided binding by binding, broke on reused names
and showed the order of binding was never sound for loops; the design is now
one kind per variable over its whole scope, inferred by a first pass.


Every value taken out of a list or record is a boxed item: four of Rill's
thirteen pilot defects were that, and so is much of its time against the
hand-written Forth (1.4x). A kind inferred for each list and record field
where it can be known - from literals, pushes, a def's result - so a list
of texts holds texts: conversions at compile time, mismatches caught
there, fewer boxes and kind checks at run time. The largest piece of work
here; through the search, so its cost in source and generated Forth is
measured.

Step 3 (766): element kinds for lists, in the Python compiler behind gene
elemkinds - correct on the corpus, 24 of 40 lists typed, and no faster.
Step 4 (767): lists of a known element kind stored unboxed, gene unbox -
correct, and slower (items boxed anew wherever the kind is not known).
Both genes taken out by the search's rule; their code is in the history
(docs/RILL-KINDS.md). Phase 2 ends with `infer`: sound kinds. Phase 4
begins with a profile of where the dispatches go, not with a guess.

## Phase 3: the gaps still open

`continue` in while loops; `return` inside a loop that has a `continue`;
`a[i][j] = v`; defs as commands with arguments, or a clear error; a
built-in `format`, so scripts stop calling printf; runtime errors that name
the Rill line - behind a debug switch if they cost speed.

## Phase 4: speed - begun from a profile in 768 (docs/RILL-PROFILE.md)

tools/rill-profile.py: the matcher was three quarters of native-by-source;
rebuilt one word per instruction, the program linked - 51 % fewer
dispatches there, 37 % less time; dead-words 5.7 % fewer from the arena and
list fixes.


Typed lists (phase 2); regular expressions compiled to Forth rather than
interpreted by backtracking (the first pilot's time); temporaries released
(the arena frees nothing); Rill on relf's native kernel rather than the
VM - likely the largest single gain, waiting on forth-vm-evolution
(GOALS.md 12).

## Phase 5: Rill at work

The repository's Python tools and shell scripts rewritten one at a time,
each held to the original's output byte for byte; smallest and most used
first, starting with run-utf8 and gen-opcodes. relfsh running Rill scripts
itself, the shell and the language on one runtime. Once the rewrites are
done, the Python compiler frozen as a regression oracle and only the
Forth compiler grows.

## Phase 6: a reference

One Rill reference - syntax, the kind rules, the library - from
docs/SHELL-LANGUAGE.md's parts; each settled decision in RILL-LEDGER.md.

## Phase 3 progress (Iteration 779): break, continue and return in loops

Two crashes found on the way and fixed: `break` in a while loop compiled to
LEAVE, which only leaves DO loops - ignored on its own, a crash nested in a
for loop; `return` from inside a for loop left the loop's frame on the
return stack - the def returned to a garbage address. Neither was in the
corpus. Now:
- return unwinds the loops of the word it is in: UNLOOP for each DO loop, and
  a counted loop's two cells dropped under the value;
- a while loop whose body holds break or continue (at its own level) makes
  the body a word, as a for loop with continue does (745); its stop flag is
  checked before the condition, so the condition is not evaluated again;
- return inside such a body word sets R-RET with the value in R-RETV and
  leaves the word; each loop around stops and passes it on, and the def
  returns R-RETV.
tests/rill/flow.rill against tests/rill/flow.py (Python): 13 lines, every
combination. Every example compiles to the same Forth as before.

## Phase 3 progress (Iteration 780): a[i][j] = v; items to library calls; defs as commands

- `a[i][j] = v`, `+=`, `-=`, to any depth: the container read down the chain
  (the first index by the variable's kind, each later one R-INDEX-ANY), the
  last index assigned through R-ASSIGN-ANY. The Forth compiler reads each
  index's tokens again where its code goes. tests/rill/chain.rill as Python.
- Found on the way, a crash: join, slice, sum, at and sort-by passed an item
  (a list read out of a list or record) on still boxed. Unboxed now, as
  keys, max, min and the rest have been since 758.
- A def called like a command with arguments: both compilers name it and
  show the call - `greet is a def: call it as greet(...)`
  (tests/rill/errors/def-args.rill).

Still open in phase 3: a built-in format; run-time errors naming the Rill
line. Phase 5's three waiting rewrites (gen-opcodes, pack-results,
run-utf8) need abs() and more of the library first.

## Phase 3 done (Iteration 781): format, and errors that name the line

- `format(f, a, ...)`: Python's % formatting - s d i f x X %%, the flags
  - 0 + and space, width and precision; too few or too many values are
  errors, as in Python. One difference, on purpose: f rounds Rill's exact
  decimals half away from zero, where Python rounds the binary float - they
  differ only on an exact tie (1.005, 2.25). tests/rill/format.rill as
  Python.
- A run-time error names the line of the statement running, innermost first:
  `rill: index 5 past a list of 3 (line 4)`. Nothing is paid at run time:
  each statement marks, as it is compiled (`[ n R-MARK ]`), where its code
  starts; an error looks down the return stack for the innermost address in
  the script's own code. Gene lines (on). Every example compiles to the same
  code as before once the marks are taken out. The driver no longer adds
  `rill: error -40xx` after a message Rill has printed itself; the kernel's
  own errors (a crash, a division by zero) still print only their number -
  the return stack is unwound by the time they are caught.

## Phase 5 (Iteration 782): gen-opcodes in Rill, as the shell script

examples/rill/gen-opcodes.rill now runs, and in all four of its modes
(generate, --forth-ops, --forth-consts, --check) says what
tools/gen-opcodes.sh says, byte for byte, with the same status; tests/rill/run
checks --check. Rill took ~29 ms where the shell took 5-7 (most of it
compiling the script); --check 141 ms against 113. What it needed:
- abs(): a number's or decimal's absolute value; a path's absolute form, as
  Python's abspath. dir(): as dirname.
- == and != compare lists and records by what they hold, as Python (records
  in any order; 1 == 1.0, inside lists too).
- at() on a list (the item, negative from the end, or the default) and on an
  item, besides a record. It crashed on a list.
- a comprehension's `if` takes a value's truth, as an if does: a match() or
  a text filtered nothing before - every item passed.
- a newline inside [ ] does not end the statement, as Python's.
- number() reads 0x hex, as the shell's $((...)), in either case.
The draft itself: bare names in comprehensions, its own def called as a
command, byname by a loop that returns, the top three directories up, a
diff on two process substitutions made a loop, a blank-tolerant pattern.
tests/rill/library2.rill as Python. Still waiting: pack-results (setenv,
a case statement), run-utf8 (load).

## Phase 5 (Iteration 783): setenv, and a case statement

- `setenv(name, value)`: env(name) sees it, and so does every command run
  after it - Rill starts commands through env, so NAME=value goes right after
  env in the vector; the strings live in the C heap. tests/rill/setenv.rill.
- `case subject { pat pat { block } ... }`, as the shell's case: patterns
  with * ? [...] (! or ^ to negate, ranges) and \, several to an arm, the
  first arm that matches runs. A quoted pattern is the text itself, as in
  the shell; $x and unquoted patterns are globs. The subject is held on the
  stack only while the patterns are tried and dropped before a block runs,
  so return, loops and the collector never see it. tests/rill/case.rill
  against the same cases in sh.
pack-results now stops at line 19: a def reads $stage, set further down -
which Python allows and Rill (772) does not.

## Phase 5 (Iteration 784): now(); what pack-results needs still

- `now()`: seconds since 1970 by the local clock (the kernel has
  LOCAL-TIME, no epoch clock; days from the date as days_from_civil) - a
  clock for durations. Agrees with Python's local clock to the second.
- examples/rill/pack-results.rill: the stage directory made before the
  defs that write into it (a def reads only what is set above it).

pack-results now stops at line 25. What it needs, each a piece of language:
1. a command's status as a number: `code((cmd ...))` (lines 25, 68);
2. a command held in a variable, run: `$cmd all> file` (line 25);
3. defs called as commands with arguments: `note "..."` (a dozen lines) -
   today an error that shows the call form (780);
4. a glob as a for loop's source: `for f in $dir/relf-claude-iter*.bundle`;
5. `cmd ?? fallback` after a command that fails (lines 42-60), to check.
Worth weighing too: a def reading a global set further down, as Python
allows (Rill's rule since 772: only what is set above it).

## Iteration 785: the script's variables, as Python's

A def reads the script's variables when it runs, set above it or below it,
as a Python function reads its module's globals. Assigning inside a def
still makes a local, as Python's without `global`.
- The first pass (gene infer) registers each def where it stands and
  compiles its body once the script's top level is through, so the body
  sees every variable the script sets, with the kind it ends up with. The
  second pass compiles in source order and takes those kinds from the
  first. (A pure stack def reads only its parameters: compiled in place.)
- Calling the def before the variable is set is a run-time error naming the
  line - Rill's NameError: `rill: $limit is not set (line 12)`.
- Numbers too, now: a number that may be read before it is set (in a def or
  at the top level, a loop variable after a loop that never ran) holds
  R-NONE, the most negative 64-bit value, until it is set; a read that may
  find it unset checks. Before, it read 0. Only such reads pay (a compare);
  every example compiles to the same code as before. The one cost of the
  sentinel: a script whose number really is -9223372036854775808 would be
  told it is not set.
- A name the script never sets is still a compile error.
- Only $name reads look forward: index assignment, += and @spreads of a
  variable set only further down stay compile errors.
- Found and fixed on the way: the Python compiler's $name inside a string
  had no unset check (the image's has had one since 772 - the oracle had no
  test with such a read), nor $args or $script; one read_var now serves both.
- One effect to know: an error inside a def's body is found after the
  script's top level, so it may be reported after an error further down.
tests/rill/globals.rill. pack-results next stops at line 66: @args as a
spread (the built-in $args is not a spreadable name yet).

## Iteration 786: commands' status, on EXIT on a signal, glob, texts in order

- An unknown function's error names it and says whether it is defined further
  down: `is-odd() is defined further down: a def comes before its use`; a
  typo: `nonesuch() is not defined`. Defs stay defined before their use (the
  user and I agreed: simpler, and no script needed mutual recursion).
- `@args` spreads the script's arguments, in a command and in a list.
- `code((cmd args))`: a command's status, a number (tests/rill/code.rill: as
  the shell's $?). `(true)` and `(false)` alone in a condition are the
  literals now, not the programs: `while (true)` forked `true` each round.
- `on EXIT` runs when INT or TERM stops the script, which exits 128 + the
  signal, as the shell's trap would. Only a script with on EXIT catches them;
  its safe points (R-GC?S) look at the signals every 1024th time and at the
  first after each command - SIGNALS-PENDING scans every flag (~27 ns), so a
  look at every safe point tripled a tight loop. A wait a signal cut short is
  waited again (it read as the command failing - TERM ended a while loop with
  status 0). A signal at the very end still gives 128 + it. Tested: TERM on a
  script in a command, INT on one in a loop that runs none.
- `glob(pattern)`: the paths it matches, sorted - wildcards in the last part,
  a leading . only for a pattern that has one; [] when none, as Python's
  (tests/rill/glob.rill against Python's glob). Not implicit in for loops:
  one way, said once.
- `<`, `<=`, `>`, `>=` on texts, in Python's order (bytes, as UTF-8 keeps it);
  two items by their kinds at run time (R-ANY-CMP) - which also fixes items
  holding decimals, compared truncated before (1.5 < 1.7 was false); a text
  and a number cannot be ordered: an error naming the line.
- Errors inside a string's {...} and $(...) name the script's line (both
  compilers said line 1), exactly, a string over several lines too.
- The lint caught the glob words named as the collector's (G-LIST): renamed.
- pack-results: note(...) calls, step(name, command text) run with sh -c,
  glob() for its three loops, sub() for trim-end, no on INT / on TERM. It
  next stops at line 44: `??` inside $(...).

## Iteration 787: pack-results in Rill, as the shell script

examples/rill/pack-results.rill runs and says what tools/pack-results.sh says
with the optional work off - the same files in the pack, each the same once
the steps' seconds and the dates are masked, the same printed summary, stderr
and status; --help and an unknown argument as the shell's too. To compare
again: run both with `--no-apply --no-clean --no-bench --no-profile
--no-verify`, unpack each pack, mask `status N, S s` and the dates, diff.
(Not in tests/rill/run: it runs make and writes packs into the checkout.)
What it needed:
- `$(a ?? b)`: a's output, or - a failing - b's after it, as the shell's
  $(a || b), a line break kept between (tests/rill/capture-or.rill as sh).
- `"$x.f"` with x an item: a record's field, else x's text and .f, decided
  at run time (R-DOT) - a parameter holding a text, "$name.log", crashed.
- sub()'s replacement: \1 .. \9 the groups, \\ a backslash, as sed's
  (tests/rill/subst.rill as sed). It was taken as written.
- The draft: `try { } else { }` written as a condition with and; the
  shell's help text in its header; its own path made absolute before the
  cd, the top three directories up; lines-text() for files of lines.
Still waiting: run-utf8.

## Iteration 788: run-utf8 in Rill - phase 5's three waiting rewrites all run

examples/rill/run-utf8.rill says what tests/shell/run-utf8 says against both
relfsh builds (30 assertions, 0 failed) and against bash (the same one
failure, word for word, status 1); tests/rill/run checks it against ./relfsh.
~200 ms against the shell's ~100. It carries tests/shell/lib.sh's two helpers
itself rather than loading them: no load - one file, read whole. A def cannot
add to a global (an assignment makes a local, as Python's), so its check
returns 1 for a failure and the top level counts.

With gen-opcodes (782) and pack-results (787), all three rewrites phase 5
waited on now run and say what the scripts they rewrite say.

## Iteration 789: double quotes inside a string's {...} and $(...)

`"{join($l, ", ")}"` and `"$(echo "x")"`: inside {...} and $(...) a double
quote starts a string of its own (which may hold {...} again) and a '...'
is passed over whole - both tokenizers (scan_str / SN-STR) and both
interpolation scanners (scan_nested / SN-NEST). 773's error, which said to
use single quotes, is now only for a { or a $( never closed. On the way:
- the image's compiler's string reader was not re-entrant - its part count
  and literal length and the echo mode were single variables, which a string
  inside a string's {...} reset (a crash); they are kept on the stack across
  each sub-compile now. rillc.py's sub-compilers are objects of their own.
- the image's $( ... ) scanner inside strings counted parentheses past the
  end of an unclosed one; SN-NEST stops there.
- a string or raw string over several lines: the tokens after it were given
  lines too early, in both compilers; its lines are counted now.
A literal { in a double-quoted string is still an interpolation: '...' it.
tests/rill/nested.rill; errors/quote-in-braces (an unclosed { now),
errors/line-after-string.

## Iteration 790: arithmetic and order on items with decimals in them

An item holding a decimal now takes part in arithmetic and comparison as
Python's float does: `l[0] += 1`, `$l[0] * 2`, `$r.a + $r.b`, `$l[0] < 2`
all failed with "a value of the wrong kind" - an item next to a number was
read as a whole number (R-ANY>NUM). Now, when an item meets a number or an
item (not a decimal - that path was already right):
- + - * / %: R-ARITH decides at run time - a decimal on either side, the
  decimal operation; else the whole-number one - and its result is an item.
  So an accumulator given items (`total += $x`) becomes an item, as the first
  pass joins its kinds; x[i] += v and a variable's += take the same road.
- == != < <= > >= against a number: R-CMP-AN / R-CMP-NA put both on one scale
  first; the result stays a plain truth value, nothing boxed.
- the short forms (1+, 0= ...) are not used on an item, as rillc.py's binop
  checks them only after this.
One difference kept on purpose: / of two whole numbers is still the integer
division (7 / 2 is 3, as the shell's $((7/2))); Python 3 would say 3.5.
Cost: dead-words over shell/*.4 113 -> 118 ms, native-by-source 229 -> 238
(best of three), both outputs as before. Found on the way: an item += 0.5 in
the image's compiler truncated the decimal. tests/rill/itemarith.rill as
Python.

## Iteration 791: out of memory inside a function, said plainly

The collector runs only at the safe points between the script's top-level
statements (776): there, nothing but the registered variables can point
into the arena. Inside a function two more things can - the outer values its
locals shadow (saved as it runs), and the caller's half-evaluated expression
on the data stack - and the collector knows neither. So a function that loops
long, making garbage, fills the 128 MB arena: before, `rill: the arena is
full`, then R-MAIN and error -2; now `rill: out of memory - 128 MB in use since
the last collection, which happens between the script's top-level
statements, not inside a function (line 3)`, status 2. The workaround: keep
the long loop at the top level and call the function from it - each of its
rounds is a safe point.

Collection inside functions is a design decision, not a fix: it needs a
precise record of the active functions' locals and of their shadowed outer
values, and call sites compiled so that no arena pointer waits on the data
stack across a call (or the collector to pin what a stack word might point
to). Left for the user to choose.
