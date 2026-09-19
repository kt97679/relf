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
   → `tests/diff/cases/heredoc-continuation-332.sh`

5. **A command substitution inside a here-document is shell code**: the
   quotes within it are quotes, not literal characters, and backquotes
   work as well as `$( )`.
   → `tests/diff/cases/heredoc-continuation-332.sh`

6. **`"$@"` with no positional parameters produces no words, but any
   adjacent quoted empty string still produces one empty word**, so
   `"$@"""` is a single empty argument.
   → `tests/diff/cases/at-empty-333.sh`

## From bash's own suite, by probing bash rather than reading it (Iteration 331)

bash's test files could not be fetched here, and would be its work in
any case. What was done instead is the same thing one level further
back: take the *areas* its suite covers - variables and environments,
redirection, arithmetic, expansion, quoting, functions, traps - and
establish each behaviour by asking bash and dash directly. The
descriptions below are of the behaviour; the cases are written here from
them.

7. **Arithmetic understands `base#digits`** for bases 2 to 36, with the
   digits above 9 written as letters, so `2#101` is 5, `16#ff` is 255
   and `36#z` is 35. This shell returned the base itself.
   → `tests/diff/cases/arith-bash-331.sh`

8. **`++` and `--` assign.** `a++` yields the old value and leaves the
   variable one higher; `++a` assigns first and yields the new value;
   `--` likewise downwards. This shell parsed them as a pair of unary
   signs, so the value came out right and the variable never changed -
   the worst of the two behaviours, since dash rejects them outright and
   bash assigns. They must not assign in the untaken branch of `?:`.
   → `tests/diff/cases/arith-bash-331.sh`

9. **A variable assignment in front of a command is visible to that
   command and gone afterwards**, including when the command is a
   function; a `local` in a function is visible to the functions it
   calls. (Already correct here.)

10. **A command substitution's trailing newlines are removed, but inner
    ones are kept**, and an empty substitution yields an empty word.
    (Already correct here.)
