# Which model helped (prompt 28, step 4)

| round | prompt | model, as the owner named it | new | wrong | verdict |
|---|---|---|---|---|---|
| 846 | review-845 | DeepSeek | a def's output captured by `$(f $x)` where a value was meant; bash's `$base[0].txt` against A's indexing in words - true in bash and dash | calls `$dir` in `ls $dir` a command substitution, and argues for B on it; its links are empty | useful: two of the round's best findings; picks B |
| 846 | review-845 | ChatGPT | the most findings (12); capture semantics unspecified (rill2 keeps all but one trailing newline, the shells none); one form for commands, another for expressions | its links are manuals (POSIX, YSH, Nushell, Python), not evidence for its claims | the most useful; picks A, `$( )` split |
| 846 | review-845 | Gemini | nothing the others lack (three findings, all theirs) | its choice - A′, a bare word read as a variable when one is bound - is xonsh's lookup, the trap measured in rill2 (`ls = 5`) | the least useful; its one proposal goes against the evidence |
| 846 | review-845 | Grok | `$x = cmd` as a capture's sugar (declined); the prompt's rule put plainly | nothing found wrong; no links | confirmation; picks A |
| 846 | review-845 | Qwen | `for $i in range(10)` reading the text "range(10)" under R3 as sent; an `if` header's command with no defined end | "greet bob passes bob" is R3's rule, not a fault; "`{` runs as a command" is a guess - the hole is the header's end | useful: a finding no other had; picks A |
| 847 | users-845 | Gemini | nothing | samples that parse under no design (`if ? mycmd {`, `$[cfg.logidr]`); no mistake found that runs wrongly | the least useful |
| 847 | users-845 | Grok | forms people will write that A lacks (`@$x[...]`, `@$(...)`) - U4's evidence | presents those forms as valid A | confirmation |
| 847 | users-845 | Qwen | `for f in $(ls *.log)` looping once (U2); a command run from a list, `@cmd` (U3) | `[` "works by accident" - it works by design; B's `print(n)` uncheckable | the most useful |
| 847 | users-845 | DeepSeek | `"$s.file"` with a record (U6), though it called it refused | `[ -n "$x" ]` as dangerous (it works); `print(f"{x}")` and `for f in *.log` (both refused by A) | useful, with care |
| 847 | users-845 | ChatGPT | `"hello {name}"` printing its braces (U1); a test plan (U5) | links are manuals, not evidence | useful |
| 848 | grammar-847 | Gemini | nothing the others lack | `and`/`or` swapped; `?` and `@` as operators; `?(...)` read as a capture; `print "..."` as a call; R13's hint `@ls` | the least useful |
| 848 | grammar-847 | DeepSeek | a statement starting with `{` (G2); `$x [0]` in code (G3); `@cmd` empty (G6); the static/run-time split | `a$b` called ambiguous - R3 decides it | the most useful |
| 848 | grammar-847 | ChatGPT | precedence unspecified (G1); `@(...)`'s lines (G5); nested captures (G7 - which found rill2's bug); record keys (G8) | "R10 does not say when the environment is read" - it does | useful |
| 848 | grammar-847 | Qwen | the static/run-time split, compactly | a grammar against R3 (`{}` no word) and R15 (`@$x`); misparses | useful, with care |
| 852 | command-model-review-851 | Gemini | nothing the others lack | rule numbers wrong; `[ -d ]` called silent (an error); `$obj[method] $obj` (no object is passed) | the least useful |
| 852 | command-model-review-851 | Grok | G3 decided as most did; streaming wanted | a computed key as a finding (its fix is the rule); "non-empty is true" against rule 11 | useful |
| 852 | command-model-review-851 | DeepSeek | `[` read right as an error; kinds borrowed from A.4; closures' lifetime | "3 3 3" (2 2 2); an Elvish claim not confirmed | useful |
| 852 | command-model-review-851 | ChatGPT | the missing basics (comments, escapes, continuation, export, value input, `if`'s boundary); identity, equality, printing; the three contracts | `PATH /tmp` as a command | the most useful |
| 852 | command-model-review-851 | Qwen | `continue`, never named; a split count for `words` | an unchecked link | useful |
