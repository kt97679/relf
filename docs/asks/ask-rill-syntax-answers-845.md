# Answers to the review prompt, checked (846)

Five answers to `ask-rill-syntax-review-845.md`: DeepSeek, ChatGPT, Gemini, Grok and Qwen, as the
owner named them. Three pick A (ChatGPT, Grok, Qwen), one B (DeepSeek), one A′ with names looked
up (Gemini). Each claim was checked against R1-R9 as sent, against bash and dash, and against
today's builds; nothing is adopted unchecked.

## What held - holes in A as sent

| | finding | raised by | checked | verdict |
|---|---|---|---|---|
| 1 | `NAME=value cmd` - one command's environment - undefined | all five | R1-R9 silent; bash, dash: the child's environment; rill2 today reads it as code: `LC_ALL=C printf ...` is "C is not defined" | held |
| 2 | `$( )` holding a command or an expression: `$(f $x)` against `$(f($x))` | DeepSeek, ChatGPT, Grok, Gemini; Qwen as `$(editor)` | silent only where a def may run as a command, which R2 allowed; neither language allows it today | held |
| 3 | `$x[0]` in a word: A indexes, bash appends `[0]` as text | DeepSeek, ChatGPT, Grok, Qwen | bash, dash: `$base[0].txt` is `file[0].txt`, `${arr[1]}` indexes; rill2 today is bash's in words (`$b[0].txt` is `file[0].txt`) - A would change a habit silently | held |
| 4 | a `$` not before a name | DeepSeek, ChatGPT, Grok, Qwen | R3, R6 silent; shells: `$`, `a$` text, `$5` an argument; rill2 today: all text, `$5` too - a bash user's `cp $1 $2` copies a file named `$1` | held |
| 5 | `@` in an expression, `[1, @rest]` | DeepSeek, ChatGPT, Grok, Qwen | R9 uses it in a comprehension's source; no rule defines it | held |
| 6 | where a command ends in a one-line block | DeepSeek, ChatGPT, Grok, Qwen | undefined; rill2 today takes the `}` as a word (845) | held - and wider: A's own `if grep -q ERROR $f {` needs `{` to end a command, and `find . -exec rm {} \;` needs `{}` to stay a word |
| 7 | environment variables | DeepSeek, ChatGPT | R1 silent; rill2 today: `$HOME` "is not defined", the environment read by `env("HOME")` | held |
| 8 | the prompt showing a value | ChatGPT, Grok, Gemini, Qwen | R2 makes `2 ** 10` and `$x` expressions, silent on showing them; rill2's prompt prints nothing | held |
| 9 | `for $i in range(10)` iterating the text "range(10)" | Qwen | R3 as sent makes `range(10)` a word | held |
| 10 | what a capture keeps | ChatGPT | the shells drop every trailing newline; rill2 drops one: `$(printf "a\n\n\n")` is 3 characters long | held |

## What did not hold

- Gemini's choice: a bare word read as a variable when one is bound. That is the name lookup the
  study's first lesson rejects; in rill2 it makes `ls -l` fail once a variable is named `ls`.
- DeepSeek's case for B: "in `ls $dir`, `$dir` is a command substitution" - it is a variable's.
  Its references came without links.
- Qwen: "`greet bob` passes bob when `$bob` is alice" - that is R3's rule, the design's point (the
  real risk, defs run as commands, is finding 2); "`{ echo hi }` runs a command `{`" - not
  decidable from A as sent; finding 6 is the hole.
- ChatGPT's links: manuals, sound, but none shows its particular claims.

## What no answer said (probes, 846)

- rill2 today rejects `{}` and `{a,b}` in a command's words ("a value was expected"): `find -exec`
  cannot be written.
- rill2 today reads a line's leading `NAME=value` as an assignment, not a command's environment.
- A's own examples rely on rules it never states: `{` ending an `if` header's command, `}` ending
  a command inside a block.

## Ranked

1. ChatGPT - the most findings, the deepest on A′ and B. 2. DeepSeek - two of the best findings,
a recommendation resting on a slip. 3. Qwen - the one finding no other had. 4. Grok - confirms.
5. Gemini - nothing new, and a recommendation against the evidence.

## Adopted into A - A.1, nothing built yet (Q46 is still the owner's)

1. **`NAME=value` words before a command** set that command's environment, as POSIX. A line of
   only `NAME=value` words is an error that says `$NAME = "value"` or `setenv(...)`.
2. **A def is called only as `name(...)`**; a def's name where a command goes is an error that
   says so, as in both languages today. With that, `$(f $x)` is an error when `f` is a def, and
   `$( )` stays one form - the first token still decides, with no silent case left.
3. **No indexing by `$name[`** in a command's words or a string: an error that offers `${name[key]}`
   (bash's own form) to index, or `${name}[key]` for the text. In code, `$x[0]` indexes.
   Never silently bash's meaning, never silently A's.
4. **A `$` before anything but a letter, `_`, `{`, `(` or a digit is text** (`$`, `a$`).
   `$1` to `$9` are the script's arguments; inside a def they are an error - its arguments are
   its parameters.
5. **`@` spreads in code too**: `[1, @rest]`, `f(@args)`; R9's comprehension source is this rule.
6. **Braces are characters in words** (`{}`, `x{y}`; no brace expansion), but a lone `{` word ends
   an `if`/`while`/`for` header's command and opens its block, and a lone `}` word ends a command
   and closes the open block.
7. **The environment**: an unbound `$NAME` in capitals reads the environment, and an unset one is
   an error when read - never an empty string; `$env[name]` reads any, `setenv` and `NAME=value
   cmd` write. A lowercase `$name` must be bound in the script, so its typo is caught before
   running. (The alternative: `$env[NAME]` only - stricter, less shell-like.)
8. **At the prompt, an expression statement shows its value**; a script's is discarded. A bare
   word stays a command - nothing is looked up.
9. **A `(` in an unquoted word is an error** with its hints - `@range(10)`, `$(...)`, quotes - so
   `for $i in range(10)` is refused, not run over the text.
10. **`$(...)` drops every trailing newline**, as the shells do.

Not adopted: a separate form for expressions, `$[expr]` (ChatGPT) - with 2, `$( )` has no silent
case left; `$x = cmd` as a capture (Grok) - R5's error is louder; Gemini's lookup.

## The other prompts

The review settled what A lacked. The grammar prompt is worth sending once its brief carries
A.1 - the grammar to check is A.1's; `ask-rill-syntax-grammar-846.md` is that. The users prompt
still adds (`-846` too); prior art adds least now.
