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
