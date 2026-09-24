# DASH.md — this shell and dash

dash 0.5.12, the Ubuntu package on the development machine, is the
reference this shell is measured against: the differential suite, the
construct matrix and both corpora compare with it, alongside bash. This
file is where the comparison stands (§1), how dash runs a script, read
from its source (§2), and what was taken from it and what was not (§3).

## 1. Where this shell stands (measured at Iteration 491)

### Correctness

| suite | this shell | dash |
|---|---|---|
| yash 2.56.1's POSIX tests | **1752 passed**, 23 failed | 1650 passed, 125 failed |
| busybox's ash tests | **255 passed**, 102 failed | 231 passed, 126 failed |
| differential cases (against bash and dash) | 131 of 131 | - |
| construct matrix | 421 passed, 1 inconclusive | - |
| POSIX, mrsh | 46 and 21, none failed | - |

Of the cases dash passes, this shell fails two of yash's - alias torture
tests - and two of busybox's: a timing race in `signal1`, and
`var_leaks`, a deliberate choice (below). Neither corpus shows a crash
or a hang.

### Features

All 31 POSIX special and regular builtins, including `fg` and `bg` with
real job control. Of dash's `set -o` options this shell has `allexport
errexit monitor notify noclobber noexec noglob nounset verbose xtrace`,
and not `ignoreeof`, `vi`, `emacs`, `privileged`, `nolog` or `debug`
(`interactive` and `stdin` are invocation flags in dash's list).

Three things this shell has that dash 0.5.12 does not: `$'...'` and
`set -o pipefail` from POSIX.1-2024 (Iterations 473-474); a line editor
with history, prompts with `\j` and `\D{format}`; and `forth`, which
drops into the system the shell is written in.

Where it follows bash rather than dash, deliberately - each is recorded
in GOALS.md with its reason:

- `echo` does not process backslash escapes, as in bash; dash's does.
- `a=b exec 1>&1` exports `a`, as bash does.
- For a special builtin, a function or an external command, prefix
  assignments are expanded before the redirections are performed, as in
  bash; dash follows XCU 2.9.1's order, which this shell follows only
  for a regular builtin (EXPANSION-ORDER.md).
- `return` outside a function, in a loop, reports and carries on.

And one where it follows dash rather than busybox's ash: a
here-document line that joins to exactly the delimiter does not end the
document.

### Speed

`tools/op-bench.py`: each operation in a loop, CPU time of the shell and
its children, per operation, the empty loop subtracted from the rest.

| operation | dash µs | this shell µs | ratio |
|---|---|---|---|
| an empty loop iteration | 1.36 | 61.0 | 45 |
| `x=abc` | 0.03 | 0.63 | 25 |
| `y=$x$x` | 0.10 | 11.8 | 122 |
| `y=$((i*3+7))` | 0.25 | 21.1 | 84 |
| `y=${PWD#/}` | 0.18 | 15.9 | 90 |
| a function call | 0.14 | 5.2 | 36 |
| `true` | 1.06 | 0.84 | 0.8 |
| `echo hello > /dev/null` | 3.23 | 12.5 | 3.9 |
| `/usr/bin/true` | 689 | 794 | 1.2 |
| `y=$(echo x)` | 99 | 182 | 1.8 |
| `y=$(/bin/true)` | 778 | 866 | 1.1 |
| `/bin/true \| /bin/true` | 1,527 | 1,662 | 1.1 |

Three classes, as there were at Iteration 268: in-process work is 25 to
120 times dash's - interpretation, all of it; builtins are at parity or
near it; anything that starts a process is within 1.1-1.8x, because
process creation dominates both.

**In-process work has got slower.** Iteration 268 measured the empty
loop iteration at 34.5 µs, and dash at 1.38 - the same as dash measures
today on this machine. So the 61 µs is this shell's own drift, about
1.8x over two hundred iterations of correctness work, and it has not
been profiled. It belongs to PERFORMANCE.md's question, not to any one
change.

### Size and startup

    dash binary                129,784 bytes (stripped)
    this engine, stripped       39,128
      + the 64-bit shell image 118,840   = 157,968

    startup, -c :       dash 1.14 ms   this engine 1.05 ms   bash 1.17 ms

The engine is timed as the `relfsh` wrapper finally runs it; the
wrapper, a shell script, adds about 2 ms of its own.

### What that adds up to

- **Interactive use**: the speed is invisible. What a person waits for
  here takes microseconds.
- **Scripts that mostly run programs** - build wrappers, init scripts,
  `configure`: close to dash. Starting a process costs about the same.
- **Scripts that do heavy work in the shell itself** - long `while
  read` loops, parsing in pure shell: this is where 25-120x lives, and
  no tuning at this level will hide it. Native compilation, GOALS.md's
  end state, is what would close it.
- **As /bin/sh for a distribution**: no. dash exists because boot time
  and package scripts add up.

Where it is competitive is not throughput but being a shell you can
open: the whole implementation is readable Forth that rebuilds itself
from its own image, and `forth` drops into it live.

## 2. How dash runs a script

**Input** (`input.c`). The script is read in `BUFSIZ` blocks (8 KB) and
handed to the lexer a character at a time (`pgetc`). Alias values are
pushed in front of the input as strings (`pushstring`). dash reads
standard input in blocks too, so a script fed on stdin whose commands
`read` the same stdin sees a different position than POSIX intends:
`printf 'read x\necho "got [$x]"\nhello\n' | dash` prints `got []`,
while bash and this shell - reading a line at a time - give `read` the
second line, as POSIX says, and run only `hello`.

**The main loop** (`main.c`, `cmdloop`). Set a stack mark, `parsecmd`
one complete command, `evaltree` it, `popstackmark` - the tree and every
temporary string of its expansion are freed at once. This is the loop
`tree.4`'s `TREE-RUN` now has.

**Memory** (`memalloc.c`). A stack allocator: `stalloc` bumps a pointer,
`setstackmark`/`popstackmark` release everything since the mark. Growing
strings are built at the top of the stack (`STARTSTACKSTR`, `stnputs`,
`grabstackstr`). A function's tree is copied into malloc'd memory when it
is defined (`copyfunc`). This shell's arena, offset-addressed and reset per
command, and its per-function copy of the body's range, are the same idea.

**The parser** (`parser.c`, `nodetypes`). Recursive descent into nodes:
`NCMD` (assignments, words, redirections), `NPIPE`, `NREDIR`,
`NBACKGND`, `NSUBSHELL`, `NAND`, `NOR`, `NSEMI`, `NIF`, `NWHILE`,
`NUNTIL`, `NFOR`, `NCASE`/`NCLIST`, `NDEFUN`, `NNOT`, and a word node
`NARG`. Reserved words are recognised only where the grammar asks
(`checkkwd`). So far this is `tree.4`'s parser. The difference is the
word:

**Words are encoded at parse time.** `NARG.text` is not the word as
written. `readtoken1` rewrites it with control bytes (`parser.h`):

| byte | meaning |
|---|---|
| `CTLESC` | the next character is quoted |
| `CTLVAR` *type* *name* `=` ... `CTLENDVAR` | `$name`, `${name-word}`, `${name#pat}`, ...; *type* says which |
| `CTLBACKQ` | a command substitution; its commands are ALREADY PARSED, in `NARG.backquote` |
| `CTLARI` ... `CTLENDARI` | `$((...))` |
| `CTLQUOTEMARK` | a double-quoted region starts or ends |

Quote removal, quoting of pattern characters, the boundaries of every
expansion, and the parse of every `$(...)` are decided once, when the
command is read.

**The expander** (`expand.c`, `expandarg`/`argstr`). One pass over the
encoded word: `strcspn` finds the next control byte, `stnputs` copies the
literal run before it, and a control byte dispatches to `evalvar`,
`expbackq` (which runs the pre-parsed node list) or `expari`. Field
splitting does not look at characters as they are emitted: the expander
records which output regions came from unquoted expansions
(`recordregion`) and `ifsbreakup` splits only those, afterwards.
Pathname expansion (`expandmeta`) works on the result, where `CTLESC`
still marks what was quoted.

**The evaluator** (`eval.c`). `evaltree` switches on the node type.
`evalcommand` expands the words and assignments, finds the command, and:
a builtin runs in-process with buffered output; a function runs its
copied tree; an external command is started with `vforkexec` - vfork and
exec. When the shell is in a child whose only remaining job is this
command (`EV_EXIT`: the last command of `sh -c`, of a subshell, of a
pipeline stage or a command substitution), it execs without forking.

**Lookup.** Variables: a 39-bucket hash table (`var.c`, `hashvar`).
Commands: a 31-bucket table (`exec.c`) holding functions, builtins and
external commands with the index of the `PATH` entry they were found in,
so a command is searched for once. Builtins: `bsearch` in a sorted table.

**Arithmetic** (`arith_yacc.c`). Recursive descent over the text, at
every evaluation - not cached.

**Builtins** (`builtins.def.in`): 38 names - `.`, `:`, `[`, `alias`,
`bg`, `break`, `cd`/`chdir`, `command`, `continue`, `echo`, `eval`,
`exec`, `exit`, `export`, `false`, `fg`, `getopts`, `hash`, `jobs`,
`kill`, `local`, `printf`, `pwd`, `read`, `readonly`, `return`, `set`,
`shift`, `test`, `times`, `trap`, `true`, `type`, `ulimit`, `umask`,
`unalias`, `unset`, `wait`.

This shell has 23: `:`, `[`, `alias`, `break`, `cd`, `command`,
`continue`, `eval`, `exit`, `export`, `forth`, `getopts`, `pwd`, `read`,
`readonly`, `return`, `set`, `shift`, `test`, `ulimit`, `unalias`,
`unset`, `wait`. Missing, of dash's: **`echo`, `printf`, `true`,
`false`**, `.`, `exec`, `kill`, `local`, `trap`, `type`, `hash`,
`times`, `umask`, `jobs`, `fg`, `bg`.

## 3. What was taken from dash, and what was not

Iteration 268's reading ended in six recommendations, in order of payoff
for effort. Five were taken:

1. **Builtins** for `echo`, `printf`, `true`, `false` and the rest
   (269): `echo` went from 838 µs, a fork and an exec, to microseconds.
2. **Exec, don't fork, in a child with one command left** - dash's
   `EV_EXIT` - for the last command of a substitution, a pipeline stage,
   a subshell, a background job and `sh -c` (269; the last stage of a
   background pipeline at 449).
3. **A command-location cache**, cleared when `PATH` changes (269).
4. **A hashed variable table** (272).
5. **Words encoded at parse time and expanded in one pass** (273-283):
   the lexer records quoting, references and substitutions, and the
   expander copies literal runs in bulk.

Not taken: **`vfork` or `posix_spawn`**, about 75 µs per external
command. A Forth VM cannot safely run in a vfork child, so it would be
an engine primitive that forks, applies the redirections and execs in
C - larger than it looks.

Not worth taking: dash's block reads of standard input, which are wrong
for `read` (§2); its uncached arithmetic; and its stack allocator, whose
job this shell's per-command arena and retired buffers already do.
