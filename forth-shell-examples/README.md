# forth-shell-examples — extending the shell from inside

This shell is written in Forth, and the `forth` builtin hands the rest
of its line to the Forth system the shell is running on. Anything
loaded that way becomes part of this shell - new builtins, hooks into
its loop - with no rebuild. Each file here is one example; load it at
the prompt, or in a script, or in the file `$ENV` names:

    forth 'S" forth-shell-examples/seq.4" INCLUDED'

The single quotes matter: they keep the shell from taking Forth's `"`
for its own. A path is relative to the current directory.

| file | what it adds |
|---|---|
| `seq.4` | `seq FIRST LAST`, a builtin: the smallest complete example of one |
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

- **There is no isolation.** A Forth error inside a loaded word aborts
  the whole shell, and a word that unbalances the stack corrupts it.
  That is the nature of the facility (`DO-FORTH` in `shell.4` says so).
- A Forth line is read 80 columns at a time: keep definitions to lines
  shorter than that, or a long one is cut and what follows it
  misread.
- What is loaded lives in this shell process only - load it again in
  the next shell, or put the `forth` line in your `$ENV` file.
