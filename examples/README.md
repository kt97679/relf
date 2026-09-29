# examples — extending the shell from inside

This shell is written in Forth, and the `forth` builtin hands the rest
of its line to the Forth system the shell is running on. Anything
loaded that way becomes part of this shell - new builtins, hooks into
its loop - with no rebuild. Each file here is one example; load it at
the prompt, or in a script, or in the file `$ENV` names:

    forth 'S" examples/seq.4" INCLUDED'

The single quotes matter: they keep the shell from taking Forth's `"`
for its own. A path is relative to the current directory.

| file | what it adds |
|---|---|
| `seq.4` | `seq FIRST LAST`, a builtin: the smallest complete example of one |
| `map.4` | `map set KEY VALUE`, `map get KEY`, `map keys`: an associative array - the data structure a POSIX shell has none of |
| `prompt-command.4` | bash's `PROMPT_COMMAND`: a hook run before every prompt |
| `tcp-echo.4` | `tcp-echo PORT`, a TCP echo server |
| `http-hello.4` | `http-hello PORT`, an HTTP server answering with a counter |

## How a builtin is made

A builtin is a Forth word. Its arguments are `ARGC @` and `n ARGV@`,
each a NUL-terminated string (`0 ARGV@` is its own name); it reports
its status with `n LAST-STATUS !`; output is `TYPE` and `CR`, errors
`ERR-TYPE` and `ERR-NL`. Then:

    ' DO-SEQ S" seq" BUILTIN

names it, and the shell finds it like any other builtin - in a
pipeline, in a function, in the background with `&`.

## The network examples

`TCP-LISTEN ( port loopback? --- fd ior )`, `TCP-ACCEPT ( fd --- fd'
ior )` and `TCP-CONNECT ( c-addr port --- fd ior )` are engine
primitives, added for these examples (Iteration 505; CV8.md 2.2). A
socket is an ordinary descriptor: `READ` and `WRITE` it, `CLOSE-FILE`
it. Both servers listen on 127.0.0.1 only, and run until interrupted,
so start them with `&`.

## What to know first

- **A Forth error fails that one command.** An undefined word, a THROW,
  a division by zero, an address outside the shell's memory, a word that
  leaves the stack deeper or shallower than it found it, or a runaway
  recursion or push loop that overflows a stack: `$?` is 1, the message
  goes to standard error, and the shell goes on (A24, A26; the stack
  check since Iteration 582, stack overflow since 586).
- **But there is no isolation.** A word that stores into the shell's own
  memory - or takes more than 16 cells from the stack and then pushes,
  writing over the shell's own cells - can still bring the shell down.
  That is the nature of the facility (`DO-FORTH` and `RUN-CAUGHT` in
  `shell.4` say so).
- A Forth line is read 256 columns at a time (80 until Iteration 514):
  keep definitions to lines shorter than that, or a long one is cut and
  what follows it misread.
- What is loaded lives in this shell process only - load it again in
  the next shell, or put the `forth` line in your `$ENV` file.
