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

42. **Inside double quotes, a single quote in a `${...}` word is
    literal** while a double quote still quotes: `"${x:+'b c' d}"` is
    one field reading `'b c' d`. This shell drops the single quotes.
    The flag from Iteration 361 was right; what it lacked was the
    distinction the trim cases were pointing at. A single quote is
    literal in a VALUE word (`:-`, `:+`, `:=`, `:?` and their plain
    forms) and still quotes in a trim PATTERN (`#`, `##`, `%`, `%%`), so
    `"${x##*'*'}"` matches a literal star. The operator is known before
    the word is scanned, so the scanner sets the flag from it.
    → `tests/diff/cases/quoted-in-word-363.sh`

43. **Quoting inside a run of IFS whitespace.** `${x:+b '' c}` is three
    fields, `${x:+b ''}` two, `${x:+'' b}` two, and `${x:+ '' }` one:
    the quoted part closes a field only when there is something to
    close, and a run of whitespace is broken in two by quoting that
    falls inside it.
    → `tests/diff/cases/quoted-field-run-364.sh`

## Twelfth batch from busybox's ash suite (Iteration 369)

44. **A here-document delimiter undergoes quote removal**, not "drop
    every quote character": `<<"\name"` ends at a line reading `\name`,
    and a backslash inside double quotes keeps itself unless what
    follows is one of the four it can quote there.
    → `tests/diff/cases/heredoc-delim-369.sh`

45. **A backslash-newline may sit inside `<<-` as well as `<<`**, so
    `cat <<\` + newline + `- EOF` is a stripping here-document.
    → `tests/diff/cases/heredoc-delim-369.sh`

46. **A quoted `-` inside a bracket expression is a member, not a
    range**: `[0"-"9]` matches three characters where `[0-9]` matches
    ten. The dash has to be marked like the other metacharacters so the
    pattern builder can escape it when quoted - but without counting as
    a reason to expand the word against the file system, since a word
    with a dash in it is not a pattern.
    → `tests/diff/cases/bracket-dash-369.sh`

47. **A backslash-newline between `$` and what it names** is invisible:
    `echo 1:$\` + newline + `1` prints `1:1`. This shell prints `$1`.
    The scanners for `$name`, `${...}`, `$(...)` and `$((...))` all
    position themselves relative to the `$`, so removing a continuation
    after it means either re-basing all four or normalising the line
    before the lexer sees it; neither is small. (Not fixed.)

## Thirteenth batch from busybox's ash suite (Iteration 370)

48. **A quoted `]` inside a bracket expression is a member**, so
    `[a\]]` matches `a` and `]`. Like the dash, it has to be marked when
    unquoted - otherwise escaping it would break every ordinary
    `[abc]` - and marked without counting as a reason to expand the word.
    → `tests/diff/cases/bracket-dash-369.sh`

49. **A dash from an unquoted expansion is a live range.**
    `x=-9; echo f[0$x]` is `f[0-9]`, while `f[0"$x"]` is the three
    characters. Expansion regions mark their metacharacters in a
    separate pass, which knew about `*`, `?` and `[` but not about `-`
    and `]`.
    → `tests/diff/cases/bracket-dash-369.sh`

50. **A dash produced by ARITHMETIC** follows the same rule as any
    other: live unquoted, a member when quoted. What was marking it was
    the aside capture - the expression's SOURCE is emitted into the
    output to be expanded, marks are recorded for it, and then the text
    is taken back out while the marks stay, pointing at offsets the
    result reuses.
    → `tests/diff/cases/expansion-word-371.sh`

51. **A backslash in a `${...}` word quotes what follows**, unless the
    expansion is itself inside double quotes, where the double-quote
    rule applies. This shell used the double-quote rule always, so
    `${x:+a\*b}` kept its backslash.
    → `tests/diff/cases/expansion-word-371.sh`

52. **A space inside a `${...}` word splits a surrounding word.**
    `H${x:+ }H` is two fields. The split was left pending by the
    expansion and then never performed, because the text that ended the
    run of whitespace arrived in BULK - through the run emitter rather
    than character by character - and only the per-character path knew
    about a pending split.
    → `tests/diff/cases/quoted-field-run-364.sh`

53. **A redirection's saved descriptors belong to the shell.** A
    redirected command could see fd 64 - and fd 63, this shell's script
    file - in `/proc/self/fd`. Real shells mark those copies
    close-on-exec; this shell has no fcntl, so the child closes
    everything above 9 before it execs.
    → `tests/diff/cases/saved-fd-372.sh`

## From yash's POSIX suite (Iteration 375)

yash ships 253 test files, about a hundred of them written "for any
POSIX-compliant shell" and named `-p.tst`. They are read the same way as
busybox's: the behaviour goes in this project's own words, the cases
here are written from that.

Two pieces of scaffolding first, both about the harness rather than the
shell. It drives itself with aliases and `LINENO`, so it has to run
under `bash -O expand_aliases` rather than dash; and it copies the
testee into a temporary directory, so this shell needs an absolute-path
wrapper rather than the usual relative one.

54. **`sh -s` reads commands from standard input and takes its operands
    as positional parameters**, with an optional `--` before them. Most
    of yash's suite starts the shell that way. This shell had no `-s` at
    all: it fell through to "run the file named by the first argument",
    found none, and exited 127 - 228 of the suite's cases in one miss.
    → `tests/shell/run-invocation`

55. **`sh -c command name args...`** sets `$0` from the name and the
    positional parameters from the rest. Only the two-argument form was
    handled.
    → `tests/shell/run-invocation`

56. **A syntax error inside `eval` ends a non-interactive shell.**
    `eval fi; echo reached` printed `reached` here and prints nothing in
    dash. The top level already exited; the nested parse returned
    instead, which is right for a command substitution's own parse and
    wrong for eval's.
    → `tests/shell/run-special-error`

57. **An error in a special builtin ends a non-interactive shell**
    (XCU 2.8.1) - and it is the ERROR that is fatal, not a non-zero
    status, so `eval false` and a `.` script that fails carry on. This
    was GOALS.md item 5k, left open since Iteration 326 as needing a
    decision; yash's suite provided the evidence.
    → `tests/shell/run-special-error`

58. **The shell's own option letters may be combined and repeated**:
    `sh -es a` is `-e -s` with `a` as the first positional parameter,
    `-o name` takes the next argument, and `--` ends them. This shell
    compared the first argument against four exact strings, so `-es` was
    read as a file name. 204 of yash's cases start a shell this way.
    → `tests/shell/run-invocation`

59. **`unalias` on a name that is not an alias is an error**, status 1
    with a message. This answered 0 and said nothing.
    → busybox and yash both check it

60. **`--` ends the options of `alias` and `unalias`**, so `alias -- a`
    prints `a` and `alias --` prints them all. dash does not do this;
    yash's suite requires it and so does XCU 1.4.

61. **`test -b -c -p -S -h -L -u -g -k`** were all missing: `FILE-KIND`
    answers none, regular, directory or other, which cannot tell a block
    device from a socket or see the set-user bit. Done in Iteration 378
    with a `FILE-MODE` primitive beside it, which returns `st_mode` and
    takes a flag for stat or lstat, so `-h` can see a link.
    → `tests/diff/cases/test-filetypes-378.sh`

62. **`test -e` and `test -s` must not OPEN the file.** Opening a FIFO
    with no writer blocks for ever, so `test -e pipe` hung this shell.
    Nothing here had ever made a FIFO. `-e` is a stat that follows the
    link; `-s` opens only a regular file or a directory, and answers 0
    for anything else, as dash does.
    → `tests/diff/cases/test-filetypes-378.sh`

## From yash's POSIX suite, continued (Iteration 379)

63. **`umask`'s symbolic forms**: a clause may hold more than one
    operator (`u=r+w`), and the permission part may name another who
    (`g=u` copies u's current bits, as `chmod` does). Both were refused
    as a bad mask. `-S` before an operand is ignored rather than
    printing.
    → `tests/shell/run-umask`

64. **An assignment before a SPECIAL builtin persists** (XCU 2.9.1):
    `v=tmp :` leaves `v` set afterwards, while `v=tmp cd .` does not.
    The same POSIX-versus-bash choice as entry 57, decided the same way.
    → `tests/shell/run-special-error`

65. **`set -u` applies to the trim operators.** `${foo#bar}` on an unset
    parameter is an error; only the forms that handle unset themselves -
    `-`, `+`, `=`, `?` and their `:` variants - are exempt.
    → `tests/shell/run-options`

66. **A command that expands to nothing takes the status of its last
    command substitution**: `$(false)` alone is 1. The rule was already
    implemented for assignment-only commands (Iteration 345) and not for
    this one.
    → `tests/diff/cases/`, covered by the empty-command checks

## From yash's arithmetic tests (Iteration 380)

67. **`&&` and `||` evaluate their right operand only when they must.**
    `x=0; $((x && 1/0))` is 0, not a division by zero, and
    `$((0 && (y=9)))` leaves `y` alone. The dead side is still parsed,
    to move the cursor past it.
    → `tests/diff/cases/arith-bash-331.sh`

68. **A value with a leading `+` is a number**: `p=+1; $((p))` is 1.
    Read as characters it came out as -49.
    → `tests/diff/cases/arith-bash-331.sh`

69. **`>>` is an ARITHMETIC shift**: `$((-14>>3))` is -2, not a huge
    positive number. Forth's `RSHIFT` is logical, so the sign bit was
    being shifted in as data.
    → `tests/diff/cases/arith-bash-331.sh`

70. **`<<=`, `>>=`, `&=`, `^=` and `|=`** were missing; only the five
    arithmetic compound assignments existed. `x <= 3` must stay a
    comparison, which is why the three-character forms check that the
    first two characters match.
    → `tests/diff/cases/arith-bash-331.sh`

## From yash's cd and parameter tests (Iteration 381)

71. **CDPATH is not searched when the operand begins with `./` or
    `../`** (XCU `cd` step 5). This shell searched it, so `cd ./dev`
    could land in a CDPATH directory instead of the one asked for.
    → `tests/diff/cases/cd-logical-319.sh`

72. **An empty CDPATH entry means the current directory, and a
    destination found there is not announced.** `cd` prints the new
    directory only when the operand was found somewhere else.
    → `tests/diff/cases/cd-logical-319.sh`

73. **A `~` at the start of a `${...}` word is a tilde prefix**:
    `HOME=/foo; echo ${a-~}` prints `/foo`. The character before it is
    the operator, so the "where does this tilde stand" test said "not at
    a word start" and left it literal.
    → `tests/diff/cases/quoted-in-word-363.sh`

## From yash's alias tests (Iteration 382)

74. **A word is still in command name position after the assignments
    and redirections that precede it**, so `>/dev/null e args` and
    `a=A s args` substitute an alias named `e` or `s` (XCU 2.3.1). An
    assignment itself is not a command name and is not substituted.
    → `tests/shell/run-alias-position`

75. **An alias may expand to nothing, or to blanks.** The line then
    holds no command at all: nothing runs and the exit status is left
    alone, so `false` followed by a line holding only a blank alias
    still reports 1. The parser must stay strict everywhere else -
    `echo A; ; echo B` and `if; then` are still errors - which is why
    the "this command vanished" flag is set by the alias substitution
    itself rather than inferred from an empty command.
    → `tests/shell/run-alias-position`

76. **An alias may expand to a reserved word**, so `alias begin={` makes
    `begin ...; }` a group, and a blank alias before a newline lets a
    pipeline continue onto the next line. Neither works here: reserved
    words are recognised before alias substitution is tried at that
    position. (Not fixed.)

## From yash's error tests (Iteration 383)

77. **A redirection that fails on a SPECIAL builtin ends a
    non-interactive shell**, like any other error in one:
    `: < /nonexistent` stops the script. The status elsewhere stays 1,
    which is bash's; dash reports 2 and POSIX asks only for non-zero.
    → `tests/shell/run-special-error`

78. **An assignment that fails means the command does not run at all.**
    A non-interactive shell has already ended by then; an interactive
    one has to SKIP the command rather than run it without the
    assignment. `readonly a=1` then `a=2 set` listed every variable
    here.
    → `tests/shell/run-special-error`
