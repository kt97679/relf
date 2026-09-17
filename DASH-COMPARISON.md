# DASH-COMPARISON.md — how dash runs a script, and what to take from it

Iteration 268. Read against dash 0.5.12's source (the Ubuntu package this
machine's `/bin/dash` comes from; `src/` is 15,800 lines of C, of which
parser, expander, evaluator, command lookup and variables are 6,168) and
measured with `tools/op-bench.py`. The question asked: how dash executes
scripts, how that differs from this shell, what can be reused, and
whether dash is faster because it has more builtins.

**Short answer.** Since Iterations 263-265 this shell has dash's shape -
parse one complete command into a tree, execute it, throw it away. What
remains different is (1) which commands run in-process, (2) how words are
represented and expanded, (3) how names are looked up, (4) how processes
are started, and (5) that every step here is threaded Forth on a VM.
More builtins do not explain the benchmark scripts - their loops call
nothing that is a builtin in dash and a program here - but they explain
most of the difference on ordinary scripts, where `echo`, `printf`,
`true` and `false` cost a fork and an exec each: 260 to 750 times what
dash pays.

## 1. How dash executes a script

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

## 2. Measured

`tools/op-bench.py`: each operation in a `while` loop, CPU of the shell
and its children, best of three, per operation, the empty loop
subtracted from the rest.

| operation | dash µs | relf µs | ratio |
|---|---|---|---|
| an empty loop iteration (`[`, `$((i+1))`) | 1.38 | 34.5 | 25 |
| `x=abc` | ~0 | 2.1 | - |
| `y=$x$x` | ~0 | 5.1 | - |
| `y=$((i*3+7))` | 0.08 | 10.3 | 130 |
| `y=${PWD#/}` | 0.06 | 9.7 | 170 |
| `f` (a function) | 0.07 | 7.2 | 107 |
| `true` | 1.0 | 776 | **750** |
| `echo hello > /dev/null` | 3.2 | 838 | **260** |
| `/usr/bin/true` | 646 | 721 | 1.1 |
| `y=$(echo x)` | 85 | 969 | 11 |
| `y=$(/bin/true)` | 695 | 927 | 1.3 |
| `/bin/true \| /bin/true` | 1,485 | 1,727 | 1.2 |

Three classes:

1. **In-process work: 25 to 170 times.** Here the whole difference is
   interpretation. The empty iteration is about 7,900 VM dispatches
   (Iteration 266), about 4.4 ns each; dash does the same in about 1.4
   µs of native code. It is a product of two factors: more steps than
   dash takes (a character-at-a-time expander where dash copies runs;
   linear searches where dash hashes; words copied tree -> ARGV ->
   output), and each step a threaded-code dispatch rather than a few
   machine instructions.
2. **Commands that are builtins in dash and programs here: 260 to 750
   times.** A fork and an exec, about 800 µs, against a function call.
   This is the builtin question, and for scripts that call `echo`,
   `printf`, `true` or `false` in a loop - most scripts - it is the
   difference that matters.
3. **External commands: 1.1 to 1.3 times.** Process creation dominates
   both. What this shell adds: `fork` where dash uses `vfork` (about
   75 µs on `/usr/bin/true`); a `PATH` search that tries `execve` in
   each directory until one works (about 70 µs with this machine's
   nine-entry `PATH`); and a SECOND fork when a command substitution or a
   pipeline stage runs an external command - the child forks again
   instead of exec'ing (about 230 µs each).

## 3. What to take from dash

**Status (Iteration 269): items 1-3 are done** - the four builtins, exec
without fork, the location cache. Measured again with
`tools/op-bench.py`: `echo` 838 -> 5.5 µs (dash 2.5), `true` 776 -> about
0 (dash 1.0), `$(echo x)` 969 -> 169 (dash 81), `$(/bin/true)` 927 -> 746
(dash 637), `/bin/true | /bin/true` 1,727 -> 1,343 (dash 1,245),
`/usr/bin/true` 721 -> 661 (dash 564). In-process work is unchanged, as
expected: 20-30 times dash's.

In order of payoff for effort:

1. **Builtins: `echo`, `printf`, `true`, `false`.** Then `.`, `exec`,
   `kill`, `trap`, `type`, `local`, `umask`, `times`. Each call in a
   script goes from about 800 µs to microseconds. `echo` and `true` are
   a few lines; `printf` needs its format language. Where POSIX leaves
   `echo` open, follow dash (`-n` only, backslash escapes always).
2. **Exec, don't fork, in a child with one command left** (dash's
   `EV_EXIT`): the last command of a command substitution, a pipeline
   stage, a subshell, a background job, and of `sh -c`. Saves a fork per
   such command - about 230 µs, and a process.
3. **Find external commands once.** A command-location cache keyed by
   name, cleared when `PATH` changes, filled by checking each directory
   for an executable file rather than by failed `execve`s.
4. **Hash the variable table.** `FIND-SHVAR` searches every variable
   with `CSTR=`; a small hash table makes a lookup independent of how
   many variables a script has. Functions and builtins likewise (the
   builtin table is short; functions are 16 at most today).
5. **Encode words at parse time, and expand in one pass.** The largest
   of these, and the one that attacks the 40-75% of dispatches spent in
   expansion (Iteration 266's profile). `tree.4`'s lexer already scans
   every quote, `$`, backquote and pattern character; recording what it
   finds - quoted characters escaped, variable references and their
   operators marked, command substitutions and arithmetic delimited, and
   `$(...)` parsed into a subtree stored with the word - lets a new
   expander copy literal runs in bulk, split only the regions that need
   it, glob using the escapes (Iteration 267's `GLOB-MARK` becomes
   unnecessary), and run a command substitution's tree in the child
   without parsing it again. It replaces most of `shell.4`'s expansion
   code rather than adding to it; it deserves its own plan document,
   as COMMAND-TREE-PLAN.md did.
6. **Start processes with `vfork` or `posix_spawn`.** About 75 µs per
   external command. A VM cannot safely run Forth in a vfork child, so
   this is an engine primitive that forks, applies the redirections
   and execs in C - larger than it looks, and worth doing after 2 and 3.

Not worth taking: dash's block reads of standard input (wrong for
`read`, as above); its arithmetic (not cached either; ours could be
parsed with the tree instead - part of item 5); its stack allocator (this
shell's per-command arena and retired buffers already do that job).

**What stays after all six.** Items 1-3 close most of the distance on
ordinary scripts, which spend their time starting commands. Items 4-5
reduce the number of dispatches for in-process work, perhaps by half
again; the cost of each dispatch remains, and closing that part is Phase
4's business (JIT/AOT), not the shell's.
