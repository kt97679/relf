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

## Phase 6 (Iteration 792): one reference

docs/RILL-REFERENCE.md says what Rill is now - running a script, values,
texts, variables and scope, expressions, statements, commands, the library,
errors, signals, memory, and the differences from Python kept on purpose. Its
uncertain claims were run before it was written down (len counts bytes; for
over a record gives its keys; else if; cd blocks come back; max and min of
two); one did not hold (`in` on texts - contains() does that) and is not
claimed. Collection inside functions stays as it is (the user's choice of
the three in 791: documented, with the workaround).

## Iteration 793: three bugs from the review

- A record as text was its address (`echo $r` printed 140312999620808), and a
  list holding a list or a record broke the stack (R-ANY>TEXT left the value
  under its text: "index 2 past a list of 2"). Now a list on its own is still
  its items with a blank between; a list or a record inside another, and any
  record, show as Rill writes them - `[1 2]`, `{a: 1, name: "x"}`, texts in
  them quoted (R-SHOW). R-JOIN keeps its separator across an item's own join
  (a record inside a list turned " | " into ", ").
- A def inside a def: `a def inside a def - define inner at the top level`,
  not the engine's "Undefined word R:outer".
- Escapes: \n \t \r and \uXXXX (as UTF-8); a backslash before a mark, the
  mark; any other letter or digit after one is an error (`\q is no escape`) -
  `"caf\u00e9"` lost its backslash and printed cafu00e9. A bare word is not a
  string: no escapes there, as in the shell.
tests/rill/show.rill, errors/bad-escape, errors/nested-def.

## Iteration 794: overflow and division by zero are errors

Arithmetic wrapped silently: 9223372036854775807 + 1 was -9223372036854775808
(R-NONE, the not-set mark, at that), and a decimal past 9223372036854.775807
came out as another number (10000000000000.0 * 1000 gave 1864712049423.0...).
Now, in the runtime (R-ADD, R-MINUS, R-MUL, R-DIV, R-MODC; for decimals
R-DMUL and R-DDIV in unsigned double cells with exact bounds, floored as */
was, and R-N>D for a number made a decimal), and from both compilers:
- + - * past 64 bits, a decimal past 9223372036854.775807, a number made a
  decimal past it: `rill: a number too big for 64 bits (a decimal: past
  9223372036854.775807) (line N)`, status 2;
- / and % by zero: `rill: division by zero (line N)` - it was the engine's
  trap, without a line;
- a literal past them: a compile error, in both compilers alike;
  number() of a text past 64 bits, and exp() past the largest decimal: the
  run-time error;
- the runtime's own arithmetic too: R-ARITH (items), comparisons, sum() -
  which also now gives a decimal when any item is one (it truncated them).
One exception, on purpose: + 1 and - 1 compile to 1+ and 1- and are not
checked - counting by one cannot reach 2^63; only a value already at the
very edge would wrap. Cost: dead-words over shell/*.4 122 -> 130 ms,
native-by-source 254 -> 263 (best of three), outputs the same. A name clash
the lint caught first: R-SUB is regex.4's sub(), so subtraction is R-MINUS.
tests/rill/overflow-add, overflow-mul, overflow-dec, zero-div;
errors/big-number, errors/big-decimal.

## Iteration 795: a pipeline fails when a stage fails

A pipeline's status was its last stage's: `false | cat` succeeded, so the one
place where shell scripts lose errors lost them in Rill too. Now its status is
the rightmost stage that failed, or 0 - bash's pipefail - with one exception:
an earlier stage stopped because its reader stopped (SIGPIPE: `yes | head -1`)
is not a failure. `cmd | other ?? true` accepts a failure as before, and
`code((a | b))` reads the status. Scripts where a stage may say "nothing"
(grep finding nothing: 1) need `?? true` there now - run-utf8, pack-results
(--verify) and intrfuzz-stress got it.
Found on the way, older: a pipeline run inside another's arguments
(`echo {code((a | b))}` - echo, an external command there, its argument a
pipeline) overwrote the outer one's state - its pids, pipe ends,
redirections; the last-stage status had hidden it. PL-BEGIN now puts the
outer pipeline aside (in the C heap) and PL-END puts it back - named as it
runs, since a BUFFER:'s memory comes at boot, not from the build.
tests/rill/pipefail.rill; code.rill's `exit 3 | cat` now 3 (sh says 0).

## Iteration 796: a list's items are expressions

`[$x - 1]` was three items ($x, "-", 1) and commas did not help
(`[($x - 1), $x * 2]` gave 4,5,*,2): items were single terms. Now each item
is an expression, in both compilers, spaces or commas between - an item
ends where no operator goes on, so `[1 2 3]`, `[a b c]` and `[--flag value]`
read as before; `[1 -2]` is still two items (a glued sign is the number's).
An operator meant as text is quoted: gen-opcodes' `[- u8 ...]` became
`['-' u8 ...]` (compiling the same as before). On the way, unary minus: in
rillc.py it called a decimal a number and negated a text silently; now `-x`
keeps a number's and a decimal's kind, an item's through R-ANY-NEG, and a
text is a compile error. tests/rill/listexpr.rill.

## Iteration 797: bin/rill - scripts run as commands

`bin/rill script.rill args` runs a script; with bin/ on PATH (or bin/rill
linked into a directory on it - the link is followed back) a script that
starts `#!/usr/bin/env rill` runs as a command, whatever its name: the
runtime now takes a file whose first line starts #! as Rill, not only a
*.rill (R-SHEBANG?; no Forth source starts so). `rill -c 'code' args` for a
line or two, `rill --forth script` for the Forth it compiles to, `rill
--help`. The image is rebuilt when missing or older than rill/*.4 and
rill/genes.tsv, its line on stderr; RILL_HOME, RILL_ENGINE, RILL_IMAGE look
elsewhere. Not top-level `rill`: rill/ is the sources' directory.
tests/rill/run checks a #! script through PATH (its arguments, its status
3), -c through a link, --forth.

## Iteration 798: the everyday functions the review missed

- `+` joins two lists (a new list) and two texts - a text and an item too,
  and two items holding texts or lists at run time (R-ARITH-AA). A text and
  a number keep the old reading (the text as a number).
- `pop(l)`: the last item, taken out. `delete(x, key)`: a record's field (its
  hash table, if it has one, made again - the slots counted the old places)
  or a list's item, negative from the end; as Python's `del`.
- `find(x, part)`: a part's first place in a text (bytes) or an item's index
  in a list; -1 when not there.
- `sort-by(rows, field)` and `sort-by(rows, field, desc)`: a list of records
  by a field, stable, its values compared as sort() compares (the old
  sort-by(record, field, order) stays). sort() of records is an error that
  says so (it sorted them by address), and a number and a decimal sort by
  value (they sorted by kind: [2 1.5 1 3] gave 1 2 3 1.5).
- `part in text` and `not in`, as Python's.
tests/rill/everyday.rill against Python.

## Iteration 799: one way each - the library (review of duplication, step 1 of 4)

The language has one way to do each thing; what a standard command does
well, the command does. Removed, with the one way that stays:

- `first(l)`: `$l[0]`. `text(x)`: `"$x"`. `contains(t, p)`: `p in t`.
  `values(r)`: `[$v for k, v in $r]`. `extend(l, m)`: `l = [@l @m]`, or
  `push` in a loop. `arg(n)`, `arg(n, d)`: `$args[i]`, `at($args, i, d)`.
- `shift(l)`, `pop(l)`, `delete(x, key)`: one `pop(x, key)` - a list's item
  (negative from the end) or a record's field, taken out and returned.
- `max(a, b)`, `min(a, b)`: `max([$a $b])` (the item itself, as Python's).
- `sort-by(record, ...)`: sort-by takes a list of records only.
- `fail "m"`: `echo "m" out>err; exit 1`. `warn m`: `echo m out>err`, now
  in-process (an echo whose only redirection is a closing out>err).
- `par for`: `xargs -P`, or `sh -c '... & ... wait'`.
- By commands: `format` (printf), `now()` (date +%s), `upper`/`lower` (tr),
  `base`/`dir`/abs of a path (basename, dirname, realpath), `log`/`exp`
  (awk). Inside a loop of thousands a command costs a process a round:
  native-by-source uppercases a file at once, one tr, not one a word.

Genes warn and argdefault gone with what they switched. Found on the way
and fixed: len() of an item holding a record gave an address; a
redirection after a braced argument was not seen (`echo {...} out>err`),
and a `>` inside braces was taken for one; a message ending in a number
had two blanks before "(line n)". Spreads take an item holding a list
(a def's parameter), checked at run time. The image: 73,605 bytes to
69,641. Six of the eight rewrites are now longer than their originals
(tools/rill-audit.py): the price of fewer conveniences.

## Iteration 800: one way each - the operators (step 2 of 4)

- `x += v`, `x -= v`, `x[i] += v`, `a[i][j] -= v`: gone for `x = $x + v`,
  `x[i] = $x[i] + v`. A compile error says what to write. Their paths were
  the most intricate in both compilers (IA-ARITH, IA-CHANGE and the
  first-pass rules of ASSIGN); 80 uses rewritten, none needing parentheses.
- `+` on texts and lists (798): gone for interpolation and `[@a @b]`. `+`
  adds numbers; a text or a list on either side is a compile error that
  names the one way.
- Found on the way, fixed: `$r[a][c]` - an item indexed by a text - was
  read as a list's item ("a number is needed here"); assignment already
  went through R-INDEX-ANY. A number keeps the fast way, another key goes
  through R-INDEX-ANY. (Still open: a number on an item holding a record,
  `$r[a][0]`, is not checked.)
- The image: 69,641 bytes to 68,401.

## Iteration 801: one way each - a field is $r[f] (step 3 of 4)

- `$r.f`, `$r.a.b`, `$x[i].f`, `at(...).f`: gone for `$r[f]`, `$r[a][b]`,
  `$x[i][f]`, `at(...)[f]` - brackets index lists and records alike. A
  compile error says so.
- In a string `"$x.f"` is x and then the text `.f`, the shell's reading,
  for every kind; a field is `"{$r[f]}"`. `"$r.f"` with a record r is a
  compile error, so an old script does not change its output silently.
  R-DOT (787), which decided for an item when the script ran, is gone.
- 142 field reads rewritten at the offsets the compiler itself logged (a
  copy of rillc.py that reported each field it compiled, with its kinds
  settled). Four of them were items holding texts - "$name.log", "$w.sh",
  "$f.bak" - where R-DOT gave text: put back by hand. A key that is also a
  variable's name is quoted: `$o["delete"]`.
- The image: 68,401 bytes to 68,193.
- An item read by a text key, `$x[name]` (a loop's record), goes through
  R-FIELD-ANY: no key boxed, as `$x.name` was (R-INDEX-ANY boxed it, an
  allocation a read); by a number, R-ITEM-ANY. Both check what the item
  holds: `$r[a][0]` on a record, open since 800, is an error, not a read of
  the record's insides. 300,000 reads: 95 ms with `$r.n` (800), 97 ms now;
  gen-opcodes --check 99 ms to 104 ms.

## Iteration 802: one way each - the syntax (step 4 of 4)

- Lists and records take a comma between items and none after the last:
  `[1, 2, 3]`, `{a: 1, b: 2}` (spaces between were the second way, 758 and
  796). A missing or a trailing comma is a compile error that shows the
  form. Expression lists now read as calls and records already did.
- `def name(a, b) -> kind { ... }`: a def is written as it is called
  (`def name a b` before); `def name()` with none.
- Output redirections name their port: `out> f`, `out>> f`, `err> f`,
  `all> f`; a plain `>` or `>>` is a compile error. `< f` stays the input.
- A list inside a list or a record shows with commas, `[1, [2, 3]]`, so what
  echo shows is again Rill as written (and Python's).
- Rewritten from the compiler's own log, as in 801: 281 commas put at the
  ends of items, 14 redirections given their port; 50 def headers by
  pattern. Five error tests; the audit reads `def f(a, b)` headers.
- The image: 68,337 bytes to 68,857 (the separators checked, the messages).

The duplication review is done: 799-802 took out the second ways and the
conveniences commands give. The image went from 73,605 bytes (798) to
68,857.

## Iteration 805: return, echo's options, a run named like a variable

Worked most severe first (prompts/13):
- **A crash.** A def that names no kind left whatever `return` gave it on
  the data stack, a cell a call (nothing dropped it at the call): `def g(a)
  { return $a }` called 200,000 times ended in `relf: data stack overflow`,
  `rill: error -3`, no line. Now a value comes only from a def that names
  its kind: `g names no kind, so returns no value: def g(...) -> kind`.
- **A refusal.** A bare `return` was refused anywhere ("unexpected '\n'").
  It now leaves a def that names no kind - from an if, a loop, or a loop
  body made a word of its own (where the def no longer fetches R-RETV,
  which it would leave behind; tests/rill/return.rill's 40,000 calls pass
  the data stack's 32,768 cells, and crash with that fetch put back). In
  stack mode it drops the parameters. In a def that names a kind it is an
  error; at the top level `return` is one too - exit ends a script.
  errors/dollar.rill (762) used a top-level `return made`: inside a def now.
- **Silent wrong results.** `(ready)`, `ready` a variable, ran a program
  named ready (through env: the else branch, a message on stderr); now an
  error naming `($ready)` and `(env ready)`. `echo -n x` printed `-n x` in
  the shell's process, and `echo -n x | cat` ran /bin/echo, which took the
  option: `-n`, `-e`, `-E` written out are an error in both, and in a
  capture. Found and left open (GOALS.md 15): echo piped or captured is
  /bin/echo, so a spread (`echo @xs` prints `@xs`, piped the items), a `-n`
  from a variable and a lone `--help` still differ.
Both compilers alike; rillc.py's Forth unchanged for all 64 programs that
compiled before. Six error tests and return.rill, each failing on 804's
build. The image: 68,857 bytes to 69,689 (the messages naming the def).
The review's third section is QUESTIONS.md Q34.

## Iteration 807: echo is Rill's however it runs; what that found; keys gone

- **echo, one program.** Piped, redirected (other than a closing out>err)
  or captured, echo was /bin/echo; in the shell's process, Rill's. They
  differed on a spread (`echo @xs` printed `@xs`, piped the items), on a
  `-n` or `-e` from a variable (/bin/echo took them as options) and on a
  lone `--help` (coreutils' help). Now an echo stage's words are a list,
  as a spread's are, and PL-ECHO runs Rill's echo in a child, as a def runs
  as a stage (PL-STAGE-X; its xt kept with !XT - `[']` in a saved
  definition went stale, and the first try segfaulted). In the process
  `@name` is its items, each as a command's argument is (R-ANY>TEXT), a
  blank between (R-WORDS>TEXT). Seven programs compile differently, only
  where an echo stage became PL-ECHO; their outputs are unchanged.
- **A crash, from 744's spreads.** The image's compiler kept a stage's
  list form in globals (SP-FORM, SP-PEND), and a capture among the
  stage's words compiled a stage of its own and reset them:
  `printf '%s|' @xs $(echo z) | cat` segfaulted. COMMAND saves and
  restores them; echo's form comes back on the stack (form 2), not in one.
- **A spread misread.** The look ahead for a spread stopped at the first
  `)`, a capture's included, and counted a spread inside a capture for the
  stage around it: rillc.py printed `y|@xs|` for `printf '%s|' $(echo y)
  @xs`. Both compilers skip bracketed groups now.
- **A refusal, from 799.** `echo $(echo a) | cat` was "unexpected '|'" in
  both compilers: the statement scan (scan_stmt, NEST+) did not count `$(`
  as a bracket, so the capture's `)` took its depth below zero and the
  pipe went unseen. It counts `$(` now.
- **keys() removed** (QUESTIONS.md A34): `len($r)` counts a record's
  fields, `[$k for k, v in $r]` lists them. Rewriting its uses found that
  a comprehension's variables are the script's (GOALS.md 15).
tests/rill/echo.rill, spread-capture.rill, capture-pipe.rill: each failed
on 806's build (echo through both compilers; spread-capture by a
segmentation fault in the image's, `y|@xs|` from rillc.py's; capture-pipe
refused by both) and passes. One line of echo.rill, an echo stage inside
an echo stage's words, passed on 806 too: a guard for the saved form.
The image: 69,689 bytes to 70,017.

## Iteration 808: a comprehension's variables are its own

A comprehension bound its variables in the script (or the def) around it,
as a `for` statement does: `[$k for k, c in $r]` made `c` a variable, so a
bare-word field `$x[a][c]` further down was refused (807 met it), a script
variable of the same name was overwritten (`k = 5` gave `b` after a
comprehension over a record's fields; `y = "keep"` gave its last item),
and the name could be read after the `]` (its last item). Now each is the
comprehension's own, as Python 3's: inside it, name is name.cJ (J its
for's token, as the source's name.srcJ), found innermost first
(rillc.py's cname, compile.4's CNAME and CM-RENAME); its source list is
still read outside it, and after the `]` the name is the script's again.
A counted loop's index gives way to a comprehension's own name of the
same (term0 and string() checked the loop first). tests/rill/
comprehension-scope.rill against Python: the refusal, the overwritten
number and text failed on 807 - each its own program - and pass; nested
comprehensions of one name, a counted loop's `i`, a def's own `w` passed
on 807 too and are guards. errors/comprehension-var-after.rill: `$q` after
the `]` is "not set" (807 gave its last item). 14 programs compile
differently: the comprehensions' own variables declared and rooted, and
intrfuzz-stress's loop `j`, once merged with a comprehension's `j`, a
number now rather than an item. The image: 70,017 bytes to 70,558.
