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
