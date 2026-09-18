# Behaviours learned from other shells' test suites

Other projects test their shells against the same standard this one
follows, and their suites are a map of what is worth checking. Their
test *files* are their own work, under their own licences, so nothing is
copied here. What is written down instead is the **behaviour** each test
establishes, in this project's own words - a fact about POSIX shells,
not anyone's expression of it - and the cases in tests/diff are written
from these descriptions.

Each entry says where the behaviour was noticed, what a shell must do,
and which case here covers it.

## From busybox's ash suite (noticed Iteration 329-330)

1. **`break n` leaves n enclosing loops**, and `continue n` continues
   the n'th enclosing loop, counting outwards from the innermost. A
   count larger than the nesting depth leaves every loop.
   → `tests/diff/cases/loop-control-329.sh`

2. **`case` does not disturb `$?` before a body runs.** The status seen
   inside a body is the one from before the `case`; `case` itself yields
   0 only when no pattern matched.
   → `tests/diff/cases/loop-control-329.sh`

3. **A function may override a regular builtin but not a special one.**
   Defining `true()` makes `true` call the function - in a pipeline, in
   a subshell, in a command substitution - while `exit`, `set`, `shift`
   and the rest of XCU 2.14's special builtins are found first and
   cannot be shadowed.
   → `tests/diff/cases/builtin-override-330.sh`

4. **A backslash-newline is removed before tokens are recognised**, so
   an operator may be split across lines: `&\`+newline+`&` is `&&`,
   `|\`+newline+`|` is `||`, and `;\`+newline+`;` is `;;`.
   → not yet implemented here; recorded in GOALS.md

5. **A command substitution inside a here-document is shell code**: the
   quotes within it are quotes, not literal characters, and backquotes
   work as well as `$( )`.
   → not yet implemented here; recorded in GOALS.md

6. **`"$@"` with no positional parameters produces no words, but any
   adjacent quoted empty string still produces one empty word**, so
   `"$@"""` is a single empty argument.
   → not yet implemented here; recorded in GOALS.md
