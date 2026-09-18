# How far behind dash is this shell? (measured, Iteration 304)

Every figure here was measured on this container with the build at
Iteration 303, against dash 0.5.12 and bash 5.x.

## Features: close, with four real gaps

Of the 31 POSIX special and regular builtins, this shell has all but
two: **`fg` and `bg`**. `jobs` exists (Iteration 299) but keeps a job
table rather than doing job control: there are no process groups and no
terminal handover, which is what `fg`/`bg` need.

The other gaps, in the order they would bite a script:

| gap | dash | here |
|---|---|---|
| `set -C` (noclobber) | yes | unsupported |
| `set -a` (allexport) | yes | unsupported |
| `set -v` (verbose) | yes | unsupported |
| `set -b`, ignoreeof, nolog, vi, emacs | yes | unsupported |
| `ulimit` | every resource | `-f` only |
| `command -p` | yes | ignored |
| assignment to a readonly variable | ends the shell | reports and continues |
| job-completion notices | `[1] + Done ...` | none |
| `-i` on the command line | yes | taken for a file name |

Everything else a POSIX script uses is present and tested: all the
expansions, arithmetic with every operator, quoting, redirections
including `<>` and `>&-`, here-documents, functions, traps by name and
number, `getopts`, `read` with `IFS` and backslashes, aliases, `local`,
`times`, `umask`, `hash`, `type`, `command`, and signal statuses.

**And two things this shell has that dash does not**: a line editor with
cursor keys and history (dash has none without libedit), and `forth`,
which drops into the underlying system.

## Correctness: at parity on everything both are tested against

    POSIX suite        46 / 46        mrsh suite   21 / 21
    differential       49 / 49        matrix      420 / 420
    interactive        19 / 22 (3 known-divergent)

The differential cases compare this shell's output with bash's or
dash's, byte for byte, on 49 scripts written around bugs found here.
The three interactive divergences are the newline dash writes after `^C`
and its job notices.

## Speed: 20 to 26 times slower in the shell, at parity in a process

    workload        dash     bash     relf      x dash
    loop             3.0      6.2     64.6       21x
    fn               1.7      4.5     39.5       24x
    str              1.9      4.8     36.1       20x
    arith            2.0      4.7     51.4       26x
    realistic mix    7.2      9.8     54.5      7.6x
    literal-heavy    2.2      4.9     23.0       11x

The realistic mix - 400 lines read in a `while read` loop with trims,
`case` matching and arithmetic, plus four external commands - is the
honest number for script work: **7.6x dash, 5.6x bash**. Anything
dominated by processes is at parity: an external command is 1.2x dash, a
command substitution 0.7x BASH, a pipeline 1.1x dash.

Why, in one line: both are AST walkers (PERFORMANCE.md), but dash's
nodes are compiled C while these are interpreted Forth at 3.36 ns a
dispatch, four times the engine's own 0.82 ns because the token stream
defeats the branch predictor.

## Size and startup: comparable

    dash binary          129,784 bytes
    this engine           39,808        + image 81,912 = 121,720
    bash binary        1,446,024

    startup (-c :)   dash 0.97 ms   relf 1.23 ms   bash 1.39 ms

So: a self-hosted shell in the same size class as dash, starting as
fast, passing the same conformance suites, missing four features of
substance, and an order of magnitude slower at in-process work.

## Assessment (Iteration 316)

A system-shaped script - option parsing, `${...}` work, a 200-iteration
loop, a few externals - measured today:

    dash 4.7 ms    bash 8.6 ms    this shell 28.2 ms
    6.0x dash, 3.3x bash, 24 ms of absolute difference

**Where it stands.** Feature coverage is level with dash apart from
`fg`/`bg`. Correctness is level on everything both are tested against:
52 differential cases against bash and dash, 420 matrix cases, the POSIX
and mrsh suites, and 22 interactive cases on a pseudo-terminal, all
passing. It is 122 KB against dash's 130 KB, starts in 1.23 ms against
0.97, and has a line editor with history, which dash does not.

**Is the speed a show stopper? It depends entirely on the duty.**

- *Interactive use*: no. Everything a person waits for here is
  microseconds against the tens of milliseconds a human notices. The
  editor, history and prompts are indistinguishable from dash's.
- *Scripts that mostly run programs* - build wrappers, init scripts,
  `configure` - largely no. Starting a process is 1.0-1.2x dash here,
  and that is where such scripts spend their time. The 6x above is on
  the part that is not the fork.
- *Scripts that do heavy work in the shell itself* - parsing files in
  pure shell, long `while read` loops - yes. That is where 20-26x lives,
  and no amount of tuning at this level will hide it.
- */bin/sh for a distribution*: no, and it should not pretend
  otherwise. dash exists because boot time and package scripts add up,
  and a 6x multiplier on the shell-side half of that is the wrong
  trade.

**Why the gap will not close by tuning.** PERFORMANCE.md and
RESEARCH-VM.md measured it: dispatch costs 3.36 ns against the engine's
own 0.82 in a tight loop - indirect branches the predictor cannot
follow - and the profile is flat. Half of a realistic script's
dispatches are in general-purpose Forth words, expansion is 24%, the
tree walk 8%. Careful work might find 2x. Native compilation is what
closes 6x, and that is Phase 4, not an afternoon.

**Where it is genuinely competitive.** Not on throughput. On being a
shell you can open: `forth` drops into the system the shell is written
in, live, and the whole implementation is 8,000 lines of readable source
that rebuilds itself from its own image. For a small system where a
self-contained 122 KB shell plus engine matters, or for anyone who wants
to read and change a POSIX shell rather than use one, that is a real
offer. As a faster dash it is not, and saying so is more useful than
optimism.
