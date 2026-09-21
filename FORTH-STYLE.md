# FORTH-STYLE.md — writing reliable Forth in this project

Practices that have actually prevented (or, more often, failed to
prevent) bugs here. Every rule below is followed by the concrete
incident that produced it, because a rule without its evidence is
just an opinion and gets discarded the first time it is inconvenient.
See `PROGRESS.md` for the full accounts.

This is not general Forth advice. It is advice for *this* kernel,
*this* codebase, and the specific ways code goes wrong in it.

---

## 1. The failure mode to design around

Forth does not tell you when you are wrong. There is no type checker,
no arity check, and no runtime error for a stack imbalance — the
program simply computes something else, or corrupts memory and fails
somewhere unrelated. Almost every rule here exists to compensate for
that one property.

The most common defect in this project is **not** faulty logic. It is
a word receiving something other than what it expected: an `(addr len)`
pair where a NUL-terminated address was wanted, an offset where an
address was wanted, arguments in the wrong order. Design for that.

---

## 2. Word size and shape

- **Keep words short enough to hold the whole stack in your head.**
  Twenty lines is comfortable; forty is where mistakes start. If a
  word needs a paragraph of commentary to explain what is on the stack
  halfway through, split it.
- **A word should do one thing, and its name should say which.**
  `SPLIT-AT-KEYWORD` splits; `RUN-SIMPLE-OR-PIPELINE` runs. A word
  that both decides and acts is a word whose callers cannot reuse the
  decision.
- **Prefer many small words to one large one**, even when the small
  ones have only one caller. `AT-SEMI?`, `AT-PIPE?`, `AT-END?` exist so
  the loops that use them read as English.

## 3. Stack parameters: three is the practical limit

Beyond three items, stack juggling (`ROT`, `2SWAP`, `OVER`) stops being
readable and starts being a source of defects.

- **0–2 parameters:** keep on the stack.
- **3:** acceptable, but comment the effect carefully.
- **4 or more:** use locals. Not optional.

> `FIND-TRIM-LEN` takes six parameters
> (`pat-addr pat-len val-addr val-len suffix? longest?`). It replaced
> four near-identical words. Writing it was only comfortable *because*
> the parameters could be named; on the stack it would have been
> unmaintainable. (Iteration 39)

**Every word gets a stack-effect comment**, without exception. All 180+
definitions in `shell.4` have one. They are the only type signatures
this language has.

## 4. Locals

A local here **is an ordinary `VARIABLE`**, saved on entry to the
declaring word and restored on every exit (`locals.4`). Consequences
worth knowing:

```forth
: COPY-ARGV ( src-argv src-argc --- )  {: CA-SRC CA-N :}
  CA-N @ ARGC ! ...
```

- Names before `|` are filled from the data stack, **left to right =
  deepest to top**, matching how the stack comment reads.
- Names after `|` are scratch: saved and restored the same way, but
  **zeroed**, not preserved.
- To *preserve* a value across a word instead of zeroing it, push it
  and take it straight back as an argument local:

  ```forth
  BODY-ARENA-TOP @  {: BODY-ARENA-TOP | ... :}
  ```

  This is how the body arena gets stack-discipline deallocation for
  free, on every exit path including an early `EXIT`.
- Because a local *is* the variable, **helper words that read the same
  name keep working** without being passed anything. `GLOB-MATCH`'s
  helpers read `GM-PATTERN` directly. A conventional locals frame would
  have forced rewriting every helper to take parameters.
- **The whole `{: ... :}` must be on one physical line.** `WORD` does
  not refill, and making it refill means calling `REFILL` mid-parse —
  the mechanism behind the multi-line `( )` comment corruption in
  Iteration 33. Diagnosed explicitly rather than misparsed.

## 5. Naming

- `WORD-NAME` — hyphenated, verb-first for actions (`RUN-PIPELINE`,
  `SAVE-WHILE-COND`), noun for values (`LINE-BUF`, `ARGC`).
- `NAME?` — a predicate returning a flag. `AT-SEMI?`, `VALID-NAME?`.
- `NAME!` / `NAME@` — stores/fetches, matching Forth convention.
- `(NAME)` — a runtime helper for a compiling word, not called
  directly.
- **Per-word scratch gets a per-word prefix**: `GM-*` for
  `GLOB-MATCH`, `NORM-*` for `NORMALIZE-OPERATORS`. This convention
  exists because there were no locals; **now that there are, prefer a
  local to a new prefixed global.** The prefixes that remain are a
  historical record of the workaround, not a pattern to extend.

## 6. Position-independence — the rule with the most teeth

**Never store or compile an absolute address that could outlive the
process.** Store an offset from `START` and add it back on use.

This applies to: execution tokens kept in variables (`!XT` / `@XT`),
the `BOOT` hook, locals' slot addresses, `BUFFER:` descriptor links,
and anything pointing into a `RESIZE`-able arena.

> Three separate crashes came from breaking this. A saved image
> reloads at a different address, so a stored xt is stale the moment
> it boots (Iterations 40, 41). And `realloc` genuinely relocates —
> measured, 7 moves in 15 calls — so a raw pointer into a growable
> arena is a use-after-free waiting to happen (Iteration 44).

> A fourth, in Iteration 419: `['] ALIAS-NAME-SLOT ... EXECUTE` in the
> completion code compiled an absolute xt into the shell image, and TAB
> segfaulted - but only on the 8-byte build. The 4-byte engine is built
> `-no-pie` and loads at the same address every time, so a stale
> address happened to be right there. **A position bug can pass at one
> width and fail at the other**, which is one more reason every
> interactive probe runs at both.

The corollary is that **offsets make growth safe**: because nothing
outside the body arena holds a pointer into it, the arena can be
`RESIZE`d freely. That is what removed two hardcoded limits.

## 7. Sentinels: never overload a value that is legal

Do not use "zero means absent" when zero is a value the field can
legitimately hold. Use a separate flag.

> `READ-NEXT-INPUT-LINE` used "`REPLAY-SRC` is non-zero" to mean "a
> replay is in progress". When `REPLAY-SRC` became an arena offset,
> the *first* allocation legitimately had offset 0 — so the outermost
> loop in every script silently did not replay. Fixed with an explicit
> `REPLAY-ACTIVE?`. (Iteration 44)

> **A flag with two meanings is a sentinel too** (Iteration 421).
> `ADD-WORD` flags a lone digit `QUOTED` to mean "an ordinary word, not a
> file descriptor", for the redirection scan. The case-pattern matcher
> read the same flag as "this pattern was quoted" and walked a glob-mark
> table nothing had filled in: `case x in 2)` was a segmentation fault.
> One bit, two readers, two meanings. Give the second meaning its own
> flag, or make every reader ask the question it means.

## 8. Keep flags with the data they describe

Parallel arrays drift. If a word describes another word, attach it.

> `ARGV-QUOTED` is a parallel array beside `ARGV`, and **every**
> stale-flag bug in this project is a copy that moved words without
> their flags: a vanishing `&&` (Iteration 28), a literal `;`
> (Iteration 47), a group body's `;` surviving into a pipeline stage
> (Iteration 49). Bash's `WORD_DESC` bundles the flags with the word
> and makes the whole class unrepresentable.

Until the structure changes, the rule is: **every copy carries the
flags** (`COPY-ARGV-Q`, never bare `COPY-ARGV`).

## 9. Reentrancy: globals do not survive a recursive call

If a word keeps state in globals and then calls something that can
reach it again, that state is gone.

> `RUN-TOKENIZED` split at `;` into global arrays, ran the left part,
> then read the remainder back — but a brace group on the left recurses
> into `SPLIT-SEMI` and overwrote it. `{ echo x; { echo y; }; echo z; }`
> lost the `z`. (Iteration 50)

Ask of any global: *can anything between the write and the read reach
this word again?* If yes, it must be a local or per-invocation
storage.

## 10. Orthogonality: one mechanism, not N special cases

When a third special case appears, stop and look for the mechanism.

> Groups needed to work as a `&&` segment, as a pipeline stage, and as
> a whole line. Rather than three code paths, one **group-depth count**
> made `;`/`&&`/`||`/`|` recognise their operator only at depth 0 — so
> none of the splitters needs to know what a group is. (Iteration 49)

> Nested `if` inside a loop body was not a loop feature: making replay
> a third **input source** meant every construct nested in a body
> worked at once, with `DO-IF` unchanged. (Iteration 42)

## 11. Duplication: merge it, because copies drift

Duplication is not mainly a size problem. It is a place where two
copies can disagree — and here, they always had.

> Six `AT-*?` predicates differed only in a literal; four had gained a
> depth check and two had not. `SPLIT-GROUP-PAREN` and
> `SPLIT-GROUP-BRACE` were the same twenty lines; **neither** counted
> depth, so `( a ( b ) c )` stopped at the inner `)`. Merging fixed a
> real bug both times. (Iterations 39, 50)

Audit periodically, not only when touching a feature.

## 12. Kernel hazards specific to this system

- **`DO`/`LOOP` with `start = limit` runs the entire unsigned range**,
  not zero iterations. Guard every loop whose count can be zero with
  an explicit `0 >` test. Caused four segfaults in Iteration 15 — and
  then two more much later, in words written *after* that rule existed:
  `TYPE-N-TO-TOK` (Iteration 88, `${p%%/*}` segfaulted) and `DO-SHIFT`
  (89, `shift 0` hung). **Writing the rule down did not retire the
  class.** What retired it was auditing every `DO` in the file and
  asking of each one whether its count can be zero — do that after
  adding any loop, and prefer a differential case that exercises the
  zero path.
  **And again in Iteration 401**, with a twist the audit question
  misses: `EMIT-DECIMAL` and `N>STR` printed their digits with
  `DIGIT-N @ 0 DO`, after a loop that produced no digits ONLY for the
  most negative cell — which `NEGATE` returns unchanged, so the digit
  loop's `DUP 0 >` was false at once. Asked "can this count be zero?",
  a reader thinking of ordinary numbers answers no. Ask it of the
  type's boundary values — zero, one, the largest and the most negative
  cell — not the typical ones. `$((1<<31))` segfaulted on a 4-byte
  build; the 8-byte build had the same fault waiting at `$((1<<63))`.
- **A multi-line `( ... )` comment can corrupt parsing** once enough
  code precedes it, surfacing as a cascade of unrelated "Undefined
  word" errors. Use `\` line comments for anything multi-line. A
  sudden cascade of undefined words should make you look for this
  first. (Iteration 33)
- **Do not inherit the caller's `BASE`.** A loadable file must save
  `BASE`, force `DECIMAL`, and restore it. `tester.fr` leaves `BASE`
  at 16; `locals.4`'s `32 WORD` was read as `0x32` = the character
  `2`, so `WORD` delimited names on the digit 2. Prefer `[CHAR] x` and
  `BL` to numeric character constants. (Iteration 38)
- **Define before use.** One linear source file; a word used before
  its definition is an "Undefined word" at load. This has caught
  something in roughly a third of iterations. For genuine mutual
  recursion use `DEFER` / `IS` (`locals.4`):

  ```forth
  DEFER FOO-CALL        \ callable from here on
  ...
  : FOO ... ;
  ' FOO IS FOO-CALL     \ patched once the real word exists
  ```

  The stored value is a `START`-relative offset, so it survives into a
  saved image, and an unpatched `DEFER` is a no-op rather than a jump
  to address zero — a forgotten patch shows up as "nothing happened"
  instead of a segfault. This replaced fourteen hand-written
  variable/caller/patch triples (Iteration 77).
- **A full fixed table must never fail silently.** `SET-SHVAR` does
  nothing when its 32 slots are full, so the 33rd variable produces
  wrong output rather than an error. Same for `MAX-FUNCS`,
  `MAX-ARGS`. Growable is the goal; diagnosing overflow is the
  minimum. Line-editor history was one until Iteration 408 — 32 slots
  of 256 bytes, so the 33rd command evicted the first and a longer line
  was cut short, both without a word. A user asked "why 32?", and
  there was no answer.
- **`ENSURE-BUFFER` can move the buffer.** Growing a `BUFFER:` may
  reallocate it, so an address taken before the growth points at freed
  memory after it. Grow first, then take every address:

  ```forth
  HIST-TEXT# @ OVER + 1+ ENSURE-BUFFER HIST-TEXT   \ grow ...
  HIST-TEXT HIST-TEXT# @ + SWAP MOVE              \ ... THEN address it
  ```

  Every growable buffer written since Iteration 408 says so in a
  comment at the point of growth.
- **`AND` and `OR` do not short-circuit.** `A B OR IF` evaluates `B`
  even when `A` has already decided — harmless for a comparison, fatal
  when `B` is only defined on some inputs: `1 32 LSHIFT` is undefined
  on a 4-byte cell, so a guard written as `CELLBYTES 4 = ... OR` still
  runs it there. Put the deciding test first and `EXIT` out of it
  (Iteration 415; the same fact cost a profiling detour in 367).
- **The kernel is small; check a word exists before relying on it.**
  There is no `2>R` here. Iteration 409 used it, the definition
  aborted, every later word in the file was undefined, and
  `SAVE-SYSTEM` still wrote an image — one that booted into the bare
  Forth prompt instead of the shell. Since Iteration 410 the image
  build refuses any build whose log complains, so this now fails
  loudly; before that it failed silently and `make` said success.
- **A stack slip in an address computation stores somewhere else.**
  `0 HIST-TEXT HIST-TEXT# @ R@ + C!` — one `+` short — stored a
  terminator at an OFFSET rather than an address, a wild write that
  surfaced as a segfault on the first command (Iteration 408). Any word
  that stores through a computed address needs a test that actually
  executes it; this one was caught only because the pty suite typed a
  line.
- **A `\` comment runs to the end of the line, and takes any code with
  it.** `-1 VALUE-FAILED? !  \ the status the caller reports EXIT`
  compiles no `EXIT`: one edit in Iteration 357 appended that comment to
  two lines ending in `EXIT`, and `printf` and `kill` with no arguments
  fell through their usage messages - `printf` into a segfault. The
  mirror of the `( )` trap; `tools/lint-comments.py` checks both now
  (Iteration 426).
- **Grow every array of a parallel set, in one word.** The job table is
  five arrays; `JOB-ADD` grew two of them, and the 65th background job
  wrote past the other three (Iteration 426). The function table is
  seven, and 419 grew all seven through one word and a `DEFER` - that is
  the shape: a single grow word that names every array, so a new array
  cannot be forgotten in one of several places.
- **A writer with no bound is an overflow waiting for a long input.**
  `B-CHAR` stores and advances, and nothing checks where; `PATHBUF` is 256
  bytes, and a 250-character command name ran the `PATH` search's
  "dir/name" into the next buffer (Iteration 421, found by the crash
  fuzzer). Size the destination to the input before building into it -
  every growable `BUFFER:` has `ENSURE-BUFFER` for exactly this.
- **Expand at a moment when nothing else is being expanded.** `PS4` was
  expanded inside the trace of a command whose own words were still in
  the expansion buffers, and any expansion in `PS4` corrupted them. The
  safe moment is the start of the command, where it is exactly as safe as
  the command's own expansion - and guard against re-entry, because a
  `$(...)` in `PS4` runs a command that would expand `PS4` again
  (Iteration 421).
- **A walk inside a loop over the same list is quadratic.** `CMP-NTH`
  finds the i-th completion candidate by walking from the start; called
  for each candidate inside a loop over candidates, for every addition,
  it made collecting a few thousand names cubic, and TAB on an empty
  line never finished (Iteration 414). Walk once, carrying a pointer.

## 13. Testing

**Three layers, all in use here:**

- **Unit / isolated diagnostic.** Build the algorithm standalone,
  prove it, *then* wire it in. `GLOB-MATCH` passed 22 cases before
  touching `shell.4`; the arithmetic evaluator passed 22 and caught two
  bugs early. This is the single highest-value habit in the project.
- **Regression.** `tests/shell/run-*` — one file per feature, added in
  the same commit as the feature, never deleted. 331 assertions.
- **Functional / differential.** Run the same script through `relfsh`
  and through `bash` and require identical stdout and exit status
  (`tests/mrsh-suite/run.sh`). A reference implementation is worth more
  than any number of hand-written expectations.

**Habits that repeatedly paid:**

- **Test the negative case.** `if true; then A; elif true; then B; fi`
  must print only `A`. Testing only the cases where a feature *fires*
  missed that the elif body ran anyway. (Iteration 47)
- **Test what the bug was, not just that the feature works.** Every
  fixed bug gets an assertion reproducing it.
- **Check *why* a test passes.** `run-case` stayed green through a
  change that was still wrong — the leftover `)` became an empty
  pattern that happened to match nothing. A green suite says the
  behaviour is right, not the reasoning. (Iteration 48) The general rule:
  `prompts/03-audit-tooling.md`.
- **A hang is a test result.** `run-break-continue` hanging was the
  clearest signal that function parsing had broken.
- **Measure before concluding.** Claiming a cause without checking it
  produced a wrong entry in `PROGRESS.md` that survived an iteration
  (fork/exec vs. compile time). If a claim is checkable in one
  command, check it. The general rule:
  `prompts/10-price-before-refactor.md`.
- **A check must be able to fail — show it failing.** Run a new check
  against the code from before the fix: the image-build check against
  the old wrapper (it exits 0 and installs a broken image), the Home/End
  checks against the old editor (exactly the screen/tmux and rxvt ones
  fail). A check never seen failing may not be checking anything.
  (Iterations 410, 412) The general rule:
  `prompts/03-audit-tooling.md`.
- **Where there is no reference to record from, state the rule.** The
  pty transcripts are recorded from dash, and dash has no `^R` and no
  completion; `search-probe.py` and `complete-probe.py` are assertions,
  each named for the rule it checks, run with the same suite.
  (Iterations 409-411)
- **Look for crashes on purpose, and rank failures by severity** - the
  method is `prompts/13-severity-first.md`. This project's tool is
  `tools/crashfuzz.py`; its first 200 seconds found two bugs, one of them
  a regression four iterations old, and three earlier segfaults had each
  been found by accident (Iteration 421).
- **A crash in the engine can be read as a Forth backtrace.** Build the
  engine with `-O0 -g`, run the image under gdb, and at the SIGSEGV print
  `ip - cbase` and the return-stack cells minus `cbase`;
  `tools/image-where.py IMAGE` names the word each offset is in. That
  turned "segmentation fault" into `EXEC-CASE -> PATTERN-MATCHES? ->
  PATTERN-FROM-MARKS` in one run (Iteration 421).
- **When two builds differ, make the compiler say what it did.** The
  widening cross-compile was "located" by comparing bytes — the first
  offset where one image equalled the other shifted by sixteen — and
  the answer was wrong: a run of zeros equals itself shifted by any
  amount. Logging `ALLOT-T`, then every header, then every literal, on
  both hosts, and diffing the logs, found it in three steps. Trivial
  matches are the first thing an inference-by-comparison finds.
  (Iterations 405, 415)

## 14. When a DSL is worth building

The question came up directly: should this project add a friendlier
language on top of Forth? The answer was no, and the reasoning
generalizes.

**Build a small facility when:**

- The friction is a *missing primitive*, not syntax. The real costs
  here were no locals and no memory allocator — both closed by ~65
  and ~40 lines respectively, both immediately reused everywhere.
- It is standard. `ALLOCATE`/`FREE`/`RESIZE` is Forth-2012's own
  wordset, not an invention; `{: ... :}` follows Forth-2012 locals.
  Standard spellings cost nothing to learn and are not a private
  dialect.
- It composes with what exists. Locals compose with `>R`/`R>`, with
  the existing `VARIABLE`s, and with the deferred-word pattern.

**Do not build one when:**

- It would be a layer only one subsystem uses. A parser DSL serving
  only `shell.4` is something the self-hosting goal would later have
  to bootstrap.
- The real problem is architectural. A nicer syntax would not have
  fixed loop-body nesting; per-invocation state did.
- You have not measured the friction. Count the actual defects and
  where they came from before designing a solution to them.

**The test that settled it:** add the missing primitives, convert real
code, and see whether the pain remains. It did not.

## 15. Two cell widths, and a cross-compiler between them

This system runs at 8-byte and 4-byte cells, and `cross.4` builds
either width's image on either width's host. Everything below was found
by running the other width, or the other host — most of it by an ARMv7
board, after four hundred iterations on x86-64 alone.

- **`NEGATE` cannot make the most negative cell positive.** It returns
  it unchanged. Converting a signed number digit by digit after
  `DUP 0< IF NEGATE THEN` therefore fails at exactly one value. Take
  the magnitude as a DOUBLE, where it fits:

  ```forth
  S>D TUCK DABS <# #S ROT SIGN #>     \ c-addr u, correct for every cell
  ```

  (Iteration 401)
- **A shift by the cell width or more is undefined.** The engine's
  `LSHIFT` and `RSHIFT` are C shifts. `x 32 RSHIFT` on a 4-byte cell is
  not 0; in practice it was `x`, and the cross-compiler filled the high
  half of 8-byte fields with copies of the low half. Guard any shift
  whose count can reach the width. (Iteration 403)
- **A literal the host cannot hold wraps, silently.** On a 4-byte host
  `4294967296` reads as 0 and `2147483648` as its negative, with no
  error. Target source must not contain a literal of 2^31 or more:
  compute it at run time - `1 31 LSHIFT` - AFTER the narrow-cell case
  has exited, so the computation only runs where it is defined. Of 388
  literals in `kernel.4`, two did this, and an 8-byte image built on a
  32-bit host had a `LITERAL` that tested the wrong range. (Iteration
  415)
- **Cross-compiler words must ask about the host, not only the
  target.** `TARGET-CELL-BYTES` says what is being built; `1 CELLS` says
  what is doing the building, and arithmetic happens in the second.
  `LITERAL-T` asked only about the target, and its fits-in-32-bits test
  was always false on a 32-bit host; `SIGNED-T` asked both and was
  right. The kernel's own `LITERAL` asks about the width it runs on
  (`CELLBYTES-TOK`), which is the same question in the other place.
  (Iterations 403, 415)
- **Test both widths, and both hosts.** Four combinations: an 8-byte
  host building each width, and a 4-byte host building each width. For
  four hundred iterations only the first two were ever run, and the
  fourth hid two bugs. `tests/run_tests.sh` now runs all four wherever
  an i386 engine can be built, and `make HOSTBITS=32` with
  `CC='cc -m32 -fno-pie -no-pie'` makes a 64-bit machine behave as a
  32-bit host.
