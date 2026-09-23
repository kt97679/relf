# The order of a simple command's expansions

Written at Iteration 479, before any code: the last two yash cases that
dash passes and this shell does not are this, and it is the one change
in the plan that reaches the hottest path in the shell. GOALS.md 1c
has carried it since 450.

## What POSIX asks

XCU 2.9.1, for a simple command:

1. Words that are assignments or redirections are set aside.
2. The other words are expanded; the first field is the command name.
3. Redirections are performed - their targets expanded, and opened.
4. Each assignment's value is expanded, then assigned.

yash's two cases test exactly steps 2-4:

    unset a
    a=$(echo A 3>|f1) 3>|f1 echo "$(test -f f1 || echo file does not exist $a)"

must print `file does not exist`: when the command word is expanded,
neither the redirection nor the assignment's own substitution has run.

    rm -f f2
    a=$(cat f2) 3>|$(echo f2) true

must be silent: the redirection creates f2 before the assignment's
substitution reads it.

## What is already right, and what is not

Measured at 479, against dash and bash:

| script | all three |
|---|---|
| `a=old; a=new echo "$a"` | `old` |
| `a=old; a=new b=$a sh -c 'echo $b'` | `new` |
| `unset a; a=1 echo ${a-unset}` | `unset` |
| `x=1; x=2 : $((x+=10)); echo $x` | `2` |

So what a word SEES is already right: assignments are APPLIED after
the words are expanded. What is wrong is only WHEN an assignment's own
expansions RUN - its command substitutions, `${x=...}`, `$((x=...))` -
which is in source order, first, before the words' and before any
redirection is performed.

## How this shell runs a simple command

- `EXEC-SIMPLE` lays out ARGV from the parsed items in SOURCE order:
  assignments, words and redirections as they were written.
- `EXPAND-AND-RUN` then:
  - `EXPAND-WORDS` expands every entry in one pass, in order - the
    assignment values included;
  - `PARSE-REDIRECTIONS` takes the redirection entries out of ARGV;
  - `PREFIX-COUNT` finds the assignments as the leading entries that
    look like `NAME=value` - by POSITION;
  - `TEMP-ASSIGN` applies them;
  - the command runs, and its redirections are performed: in the
    shell, saved and restored, for a builtin or a function; in the
    CHILD, after the fork, for an external command.

## How dash does it

`evalcommand` expands the arguments; expands the redirection targets
(`expredir`); performs the redirections IN THE SHELL, saving the
originals (`redirectsafe`, REDIR_PUSH); only then expands the
assignments; forks, and the child inherits the redirected descriptors;
and the shell restores its own.

## The plan, in three stages

Each stage is committed and verified on its own, and each stage's
behaviour on the table above must not move.

**Stage 1 - assignment values after the words.** `EXPAND-WORDS` makes
two passes over its saved entries: every entry that is not an
assignment, then the assignments. An assignment is always exactly one
field, so the assignments' output slots are known in advance - reserve
slots `0 .. nA-1`, expand the words from `nA` - and ARGV comes out in
the order PREFIX-COUNT expects without a permutation. This fixes the
first yash case and the order of side effects between words and
assignments. It does not move the redirections.

**Stage 2 - after the redirections, for a builtin or a function.**
There the shell already performs the redirections itself. The second
pass of stage 1 moves to after they are performed. This fixes the
second yash case, whose command is `true`.

**Stage 3 - after the redirections, for an external command.** The
redirections move into the shell, before the fork, saved and restored
as for a builtin, and the child inherits them instead of applying them.
This is dash's design and the largest step: here-documents, `exec`'s
kept redirections and noclobber all pass through it. Pipelines are not
affected - each stage is its own process, and "the shell" there is the
stage.

## How each stage is tested

- The two yash cases, and the four rows of the table.
- A differential case per stage, bash as the reference.
- A new family for `tools/difffuzz.py`: prefix assignments whose values
  have side effects - a substitution that creates a file, `${x=...}`,
  `$((n+=1))` - beside words and redirections that observe them.
- The whole suite, both corpora, and the pty transcripts for stage 3.

## What would make this the wrong change

If stage 1's reservation turns out not to hold - if some assignment can
expand to other than one field - the fallback is a permutation of the
pointer array and its parallel flag arrays after the second pass, which
is safe because the pointers are into one buffer that only grows during
a pass.
