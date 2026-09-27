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

## Stage 1 landed (480); what stage 2 has to get past (481)

Stage 1 is Iteration 480, with yash simple-p.tst:11 passing; the
reservation held - an assignment is always one entry, since `NAME=` is
never empty and never split. It also retired a workaround: 345 had made
an assignment-only command keep the FIRST substitution's status because
under source order that matched the references; with the order right,
POSIX's LAST-performed rule matches them instead.

`tools/difffuzz.py` has a family for this now: prefix assignments whose
values have side effects, beside words that observe them. It has teeth:
the 479 build prints `[1][11]` for
`n=0; v=$((n+=1)) printf "[%s]" "$n" $((n+=10))`, where 480, dash and
bash print `[0][10]`.

Reading the run path for stage 2 found three things the plan above did
not know:

1. A builtin's redirections are performed inside `RUN-A-BUILTIN`,
   reached through `DISPATCH` from `RUN-EXPANDED` - AFTER `TEMP-ASSIGN`
   in `EXPAND-AND-RUN` has applied the prefix. The assignment pass has
   to move to between the redirections and `TEMP-ASSIGN`.
2. `GLOB-FIELDS`, at the end of `EXPAND-WORDS`, uses the `EW-*` arrays
   as its own scratch. A pass 2 deferred past `EXPAND-WORDS` must first
   copy the pending assignment entries - text, node and flags - out of
   them.
3. Performed early, the redirections must not be performed again by
   `RUN-A-BUILTIN` (so `REDIR-N` is 0 while it runs), and `END-REDIRECT`
   must come after the command, before `TEMP-RESTORE`.

The hook, then, for a regular builtin that has both redirections and
assignments: pass 1 with the assignment slots holding their raw text as
placeholders; `PARSE-REDIRECTIONS`; `BEGIN-REDIRECT`, stopping if it
fails; pass 2 from the saved entries into slots 0 .. n-1; `TEMP-ASSIGN`;
`RUN-EXPANDED` with no redirections of its own; `TEMP-RESTORE`;
`END-REDIRECT`. A special builtin, a function and an external command
keep stage 1's order until the same hook is shown safe for each. An
assignment-only command with redirections, `a=$(cat f) >f`, is the same
shape through `APPLY-BARE-REDIRS`.

## Stage 2 landed (482); where the references part company (484)

Stage 2 is Iteration 482, for a regular builtin: yash simple-p.tst:18
passes, and with it the last of yash's expansion-order cases.

Then the question for the rest was measured rather than assumed. The
probe is `v=$(test -e q && echo yes >r || echo no >r) 3>q CMD; cat r` -
`yes` if the redirection was performed before the assignment was
expanded:

| CMD | this shell | dash | bash --posix |
|---|---|---|---|
| `true`, a regular builtin | yes | yes | no |
| `:`, a special builtin | no | yes | no |
| `f`, a function | no | yes | no |
| `/bin/true`, external | no | yes | no |

dash follows XCU 2.9.1 for every kind of command; bash expands the
assignments first for every kind. So for the three kinds stage 2 did not
take, this shell agrees with bash and not with the standard - and no
corpus tests them, since the references disagree.

Taking them would be the standard's order and dash's, and it has real
costs: a special builtin brings `exec`, whose redirections must outlive
the command (the early undo record would take them back), and `eval`
and `.`, which run other commands; stage 3 moves every external
command's redirections into the shell before the fork. That is left
here as the recorded next step, not done: the standard is on its side,
and nothing that can be observed today asks for it.
