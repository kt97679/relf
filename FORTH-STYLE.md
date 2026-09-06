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
  an explicit `0 >` test. Caused four segfaults in Iteration 15.
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
  minimum.

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
  behaviour is right, not the reasoning. (Iteration 48)
- **A hang is a test result.** `run-break-continue` hanging was the
  clearest signal that function parsing had broken.
- **Measure before concluding.** Claiming a cause without checking it
  produced a wrong entry in `PROGRESS.md` that survived an iteration
  (fork/exec vs. compile time). If a claim is checkable in one
  command, check it.

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
