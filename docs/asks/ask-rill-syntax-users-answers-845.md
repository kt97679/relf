# Answers to the users prompt, checked (847)

Five answers to `ask-rill-syntax-users-845.md`: Gemini, Grok, Qwen, DeepSeek and ChatGPT, as the
owner named them. They answer A as first sent, not A.1 - every sample writes `$cfg[logdir]/*.log`
and `"$s[file]"` in words, which A.1 makes errors, and none uses R10 or R11. The question's payload
is the mistakes that run and do the wrong thing; each such claim was checked against A's text,
against bash and dash, and against today's rill2.

## What held

| | finding | from | checked | verdict |
|---|---|---|---|---|
| U1 | `"hello {name}"` - Python's habit, and rill2's syntax today - prints its braces under A, silently | ChatGPT | rill2 today prints `hello ada`; A's R6 makes braces characters: every rill2 script and every Python habit would change meaning without a word | held - and the migration makes it worse |
| U2 | `for f in $(ls *.log)` loops once over the whole text | Qwen (for A′; A's R9 is the same) | bash and dash split it: `<a><b><c>`; A's R9 makes `$(...)` one item; rill2 today refuses it ("a list was wanted") | held - A as sent would turn a refusal into a silent wrong loop |
| U3 | a command held in a list, run as `@cmd` | Qwen's sample (`if @cmd {`) | A's R2 sends `@cmd` to "any other word starts a command" but never says the list's first element is the program; rill2 today refuses it | held - to be said |
| U4 | `@` forms people write that A lacks: `@$cfg[servers]`, `@$(...)`, `@ (...)`, `$args += @inputs` | Grok, Qwen, ChatGPT, Gemini - in their own samples | A has `@name`, `@name(...)`, `@(...)` only | held - each should be an error offering `@(...)` |
| U5 | test before building: argument boundaries for `$x` and `@x`; every static error before any command runs; the prompt parsing as scripts do | ChatGPT | a plan, not a claim | adopted as the implementation's acceptance tests |
| U6 | `"$s.file"` with a record: the record's text, then `.file` | DeepSeek, which called it refused | A's R3, R6: a `.` after a name is text, nothing refuses the record - silent | held, against its own verdict |

## What did not hold

- DeepSeek: `if [ -n "$x" ]` as "the most dangerous bash-reader error in A" - it works: bash prints
  true for `x="a b"` and false for an empty `x`, and in A `"$x"` is the same one argument.
- DeepSeek: `print(f"{x}")` printing the text `f"{x}"` - R5 refuses the bare `f`.
- DeepSeek: `for f in *.log` running over the working directory - R1 refuses the bare `f`; and a
  glob running where it is written is no mistake.
- Qwen: `if [ $n -gt 0 ]` "works by accident" - `[` is a command, and its status is what `if`
  takes: it works by design.
- Qwen: B's `print(n)` printing `(n)` - B is not specified that far, and YSH has no `print`; not
  checkable here.
- Gemini's samples do not parse under any of the designs (`if ? mycmd {`, `$[cfg.logidr]`), and
  its table finds no mistake that runs wrongly anywhere.
- Grok's samples use forms A lacks (`${f%.jpeg}`, `@$cfg[...]`) as if it had them - useful only
  as U4's evidence of what people will write.

## Scores

Readability, 1 to 5, as the five gave it (opinions, not measurements): A - bash readers 3.4,
Python/Ruby readers 3.0; A′ - 3.8 and 3.2; B - 2.6 and 3.4. A′ reads a little easier to a bash
user and B to a Python user; A is the one where the answers, checked, leave no mistake that runs
wrongly once U1-U6 are refused.

## Ranked

1. Qwen - grounded in the rules, U2 and U3. 2. ChatGPT - U1 and the test plan. 3. DeepSeek - the
most text, U6 half-seen, three claims wrong. 4. Grok - terse, forms A lacks. 5. Gemini - samples
that do not parse, nothing found.

## Adopted - A.2, nothing built yet

- **R12.** A `{name}` inside a `"..."` string, where `$name` is bound, is an error that says
  `$name`; `\{` or `'...'` keep the braces as text. (U1)
- **R13.** A `for` header that is one `$(...)` and nothing else is an error that says `@(...)`,
  its lines. (U2)
- **R14.** A command may start with `@name` or `@(...)`: the list's first element is the
  program, the rest its arguments - the shell's `"$@"`. (U3)
- **R15.** After `@` comes a name, a call `name(...)`, or `(`; anything else (`@$x`, `@ (`,
  `@name[`) is an error that offers `@(...)`. In code `@` spreads only inside `[...]` and a
  call's arguments: `$a += @b` is an error that says `$a += $b`. (U4)
- **R16.** A list or record put into a word or a string beside other text is an error that offers
  `${x[key]}` or `$(json($x))` - `"$s.file"` would otherwise print the record and `.file`. (U6)

U5's three tests are the implementation's acceptance tests. The question is answered: no more
models need this prompt.
