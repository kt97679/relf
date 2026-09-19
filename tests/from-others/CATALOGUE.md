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

## Second batch from busybox's ash suite (Iteration 334)

11. **A command that is only redirections still performs them.** `> f`
    creates or truncates f and yields 0, with no command run; the same
    holds for `< f`, which opens and closes it. This shell did nothing
    at all with such a command, which is why several of the suite's
    tests failed at their setup lines rather than at what they meant to
    check.
    → `tests/diff/cases/bare-redirect-334.sh`

12. **The word after a redirection operator is not field-split.** With
    `v='a b'`, `echo x >$v` writes to the single file named `a b` rather
    than to two files; a shell that splits it either writes to the first
    or reports an ambiguity. What a shell does when the target expands to
    several fields is unspecified - bash calls it an ambiguous redirect,
    dash uses the single name it read - and this shell follows dash.
    → `tests/diff/cases/redir-target-335.sh`

## Third batch from busybox's ash suite (Iteration 336)

13. **`exit` with no operand inside a trap uses the status the shell had
    when the trap was entered**, not the status of the last command the
    trap itself ran. So `trap 'echo done; exit' EXIT` preserves the
    script's status rather than replacing it with the echo's 0.
    → `tests/diff/cases/trap-exit-336.sh`

14. **A background child that has exited must be reaped even while the
    shell is running builtins.** Until it is waited for it stays a
    zombie, and `kill -0` on a zombie succeeds - so a script that spins
    on `kill -0 $!` waiting for its child never sees it finish.
    → `tests/diff/cases/trap-exit-336.sh`

## Fourth batch from busybox's ash suite (Iteration 337)

15. **A backslash inside a bracket expression hides the character after
    it**, so `[\q]` matches `q` and `[\]]` matches `]`. The scan for the
    closing bracket has to skip the escaped character too, or `[\]]`
    looks as if it ended at the first `]`.
    → `tests/diff/cases/bracket-escape-337.sh` (pathname expansion)

16. **The same holds for a `case` pattern**: the quoting is per
    character, so `[\q]` matches `q`, `a\*` matches only a literal star,
    and `a\*b*` keeps the escaped star and the live one.
    → `tests/diff/cases/case-quoting-341.sh`

17. **A backslash-newline inside a reserved word is a continuation**, so
    a line ending `i\` followed by `f true; then` is `if true; then`.
    This shell joined the word but marked it quoted, and a quoted word
    is not a reserved word; the token's text is also the raw source, so
    the continuation was still in it at the comparison.
    → `tests/diff/cases/continuation-338.sh`

18. ~~A newline in an alternate value~~ - not a newline problem at all.
    The test uses `${$+...}`, and the special parameters had no value in
    the operator forms, so the alternate was never taken.
    → `tests/diff/cases/special-param-339.sh`

19. **`${#+word}` names the parameter `#` with an operator**, not the
    length of `+word`; `${#}` is still the count and `${#name}` still a
    length.
    → `tests/diff/cases/special-param-339.sh`

## Fifth batch from busybox's ash suite (Iterations 341-342)

20. **`return` in a loop's condition leaves its own status.**
    `while return 2; do :; done` in a function returns 2; the loop's own
    saved status must not overwrite it.
    → `tests/diff/cases/return-in-condition-342.sh`

21. **A here-document delimiter that expands to nothing still
    delimits.** `cat <<- $a` with `a` empty or unset ends at a line
    matching the delimiter as written. The operator and its target
    travel through the expander as words, so an empty delimiter was
    dropped like any other empty word and every redirection after it
    shifted: the here-document took the wrong file descriptor and its
    reader hung on a pipe nobody closed.
    → `tests/diff/cases/heredoc-empty-delim-344.sh`

## Sixth batch from busybox's ash suite (Iteration 345)

22. **`wait %n` names a job**, as `kill %n` does, and reports that job's
    status - including a job the shell has already reaped, whose status
    it kept.
    → `tests/diff/cases/wait-job-status-345.sh`

23. **`wait` with no operands yields 0**, whatever the children did.

24. **An assignment made only of command substitutions takes the status
    of the FIRST of them.** `v=`exit 2` `false`` is 2 in bash and dash
    alike, though XCU 2.9.1 reads as though it should be the last.

25. **`getopts` reports an unknown option and a missing argument**
    unless the optstring starts with a colon. dash writes
    `Illegal option -q`, bash `illegal option -- q`; this shell follows
    dash. In that mode `OPTARG` is left empty, where silent mode sets it
    to the offending letter.
    → `tests/shell/run-getopts-msg`

26. **A backslash inside a backquote substitution** is removed only
    before a backquote, a backslash or a dollar; every other backslash
    stays. This shell crashed on any of the others - the copier
    re-fetched a character outside the test that decides whether to skip
    one, so each such backslash left a value on the stack.
    → `tests/diff/cases/backquote-escape-348.sh`

## Seventh batch from busybox's ash suite (Iteration 349)

27. **A command of assignments and redirections only sets the variables
    in the shell itself**, in either order: `> f var=ok` and
    `var=ok > f` both leave `var` set afterwards.
    `> f var=ok` works since Iteration 349 and `var=ok > f` since 350:
    with the assignment first the caller applies it temporarily, and the
    count of prefixes has to be taken before `TEMP-ASSIGN` removes them
    from the list - not merely before the redirection words go, which is
    what 349's attempt assumed.
    → `tests/diff/cases/assign-redirect-349.sh`

28. **`command` takes more than one option.** `command -p -V name` and
    `command -v -p name` are both valid.
    → `tests/diff/cases/wait-job-status-345.sh`

## Eighth batch from busybox's ash suite (Iteration 351)

29. **A command may have more than one here-document.**
    `cmd <<A 3<<B` feeds A to standard input and B to file descriptor 3.
    Two things were wrong here, and only the first is fixed: one buffer
    held one prepared body, so both redirections ran from whichever was
    prepared last.

30. **A here-document on a numbered descriptor reaches that
    descriptor.** `cat 3<<E` then `<&3` reads the body in dash; here fd
    3 is not open. Observed, not explained: the parse is right -
    `tree-dump` prints `(redir 3 << "E" (body ...))` - and an unnumbered
    here-document works, in simple commands and compounds alike.
    Iteration 355 found it: the pipe's read end can land ON the
    descriptor being redirected - fd 3 is the lowest free one when the
    command says `3<<E` - so the copy is a no-op and the close after it
    destroys the descriptor.
    → `tests/diff/cases/heredoc-fd-355.sh`

## Ninth batch from busybox's ash suite (Iteration 355)

31. **An asynchronous command reads /dev/null** unless it redirects its
    own input, so `cat &` in a script finishes instead of swallowing the
    rest of the file.
    → `tests/diff/cases/bg-stdin-355.sh`

32. **`return n` in a trap sets the status that stands afterwards**,
    where `$?` is otherwise put back to what it was before the trap; the
    return also carries on out of the enclosing function.
    → `tests/diff/cases/trap-return-355.sh`

33. **An empty field is dropped only when NOTHING in the word was
    quoted.** `${x:+\'\'}` and `${x:+""}` each make one empty argument:
    the quoting that appears during expansion counts as much as a quote
    at the start of the word.
    → `tests/diff/cases/quoted-empty-355.sh`

## Tenth batch from busybox's ash suite (Iteration 356)

34. **`${#?}` is the length of `$?`**, and so for the other special
    parameters; `${#+word}` remains the parameter `#` with an operator.
    What tells them apart is whether a brace or a word follows.
    → `tests/diff/cases/special-length-356.sh`

35. **`command` reports a name it cannot find** - `NAME: not found` for
    `-V` - and answers greater than zero. dash and this shell say 127,
    bash says 1; POSIX asks only for non-zero.
    → `tests/diff/cases/command-306.sh`

36. **Assignments in one command are expanded and applied left to
    right**, so `X=usbdev1.2 X=${X#usbdev} B=${X%%.*}` leaves B as `1`.
    Both references do this and this shell does not: it expands every
    word first and applies the assignments afterwards, so each one sees
    the values from before the command. The command's own words must
    still see the OLD values - `A=1 echo $A` prints nothing in both
    references - so the fix cannot simply apply them earlier; the
    assignment words have to be expanded after the command words, one at
    a time, each after the previous is applied. (Not fixed.)

37. **Assigning to a readonly variable is an error**: the message goes
    to standard error and the status is 2. Done in Iteration 357 for a
    plain assignment. Two parts are not: with a redirection beside it
    the status is still 0 here, because the assignment is applied before
    the redirection is in place and the caller overwrites the status;
    and dash ENDS a non-interactive shell on it, which this shell does
    not, in line with the other special-builtin differences.

38. **A special builtin keeps the variables assigned in front of it.**
    `VAR=val2 eval ...` leaves VAR set in dash and ash; this shell
    follows bash and drops it. Deliberate, recorded in GOALS.md 5k, and
    the reason busybox's var_leak stays red.

## Eleventh batch from busybox's ash suite (Iteration 358)

39. **Unquoted `$*` and `$@` make one field per positional parameter**,
    whatever IFS holds - `IFS=:; for x in $*` gives a field per
    parameter, not one field split on colons. Quoted `"$*"` joins with
    IFS's first character, or with nothing when IFS is set and empty,
    and inside an assignment nothing is split at all, so both forms
    join.
    → `tests/diff/cases/ifs-fields-358.sh`

40. **An empty field made by quoting is a field.** With `e` unset and
    `b=" b "`, `echo a "$e"$b c` prints `a`, an empty argument, `b`, `c`
    - two spaces between `a` and `b`. The quoted part contributes no
    characters, but it means the leading IFS space in `$b` ends a field
    rather than being absorbed as leading whitespace.

    What Iteration 359 measured. The same word with a NON-empty quoted
    part splits correctly: `"x"$b` gives two arguments here and in dash.
    The word-level quoted flag is set either way - `""$v` with v empty
    yields one empty argument, as it should. So the shell knows the word
    was quoted; what it does not know is that the FIELD was. An attempt
    to carry that as a field-level flag, set where the expander enters a
    quoted region and cleared at each field break, changed nothing,
    which says the expander never enters a region for an empty pair of
    quotes.

    Iteration 360 found where it really happens, by forcing the
    suspected branch to split unconditionally and seeing NOTHING change:
    an unquoted variable's value is not emitted character by character
    at all. It is written out whole and its extent recorded as a region,
    and `XE-SPLIT` walks those regions afterwards, splitting inside each
    and taking the text between them as literal. A quoted part that
    emits no characters leaves no text between regions, so the splitter
    cannot tell it was there. The fix belongs in that pass - a region
    that starts a word needs to know whether quoting preceded it - not
    in the per-character emitter. (Still not fixed.)

41. **`return` with no operand inside a trap** takes the status the
    shell had when the trap was entered, as `exit` does.
    → `tests/diff/cases/trap-return-355.sh`
