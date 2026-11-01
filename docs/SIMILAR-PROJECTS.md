# Projects like kbool, and what rill3 may take from them (921)

The owner asked (920, after kbool's article) for a survey of projects like kbool, and action items from
it, measured against rill3's aims: a simple, minimal, expressive shell language; the smaller the binary,
the simpler the syntax and the shorter the scripts, the better; ideally one way to do each thing.

## Where rill3 stands (measured 921)

- Size: the engine `relf64` 45,360 bytes and the image `kernel64-cm.img` 87,040 bytes - about 132 KB;
  relfsh on the same engine, `relfsh64`, 174,404 (its image 129,028). On the assembly engine
  `relfasm64` (15,856 bytes) rill3's suite passes whole (922): 102,896 bytes together, against
  `relfshasm64`'s 144,900. On the same machine: dash 129,784; mksh 310,312; yash 445,352; bash
  1,446,024; busybox 2,124,608.
- Where the image's 76.5 KB above the kernel go (922, HERE after each file): the front end cm/cmc.4
  23.1 KB; Rill's runtime rill/rt.4 18.5; builtins cm/lib.4 8.6; relfsh's line editor 4.2 and the
  character widths 2.8; TAB 3.9; the case tables 3.0; the rest of cm/ 7.8; the Forth libraries 4.4.
  Across them: some 20 KB of word headers (1,084 named words - generated code finds the runtime by
  name, so its words keep their names) and 12.9 KB of quoted text (messages, and the Forth the
  front end writes out as text).
- Builtins: 37 names. Syntax: a word's first character decides its kind (899).
- The whole scripts (54 files, 714 lines that are not comments) as a corpus of real use: 23
  increments `set x $(( $x + ... ))`, 5 counts into a map (`if has $m $k { set m[$k] ... } else
  { set m[$k] 1 }`), 20 lists split from a text `[@(split ...)]`, 28 `$(count ...)`, 2 `|| exit`.

## The projects

- **kbool** (bash, 2026; https://github.com/Keksov/kbool): Free Pascal's classes, modules loaded by
  name and once (`kk.uses`), a class library; values returned in `RESULT` because `$( )` forks.
  For rill3: modules by name, loaded once; an independent review session; a test matrix across tools.
- **Bash Infinity / bash-oo-framework** (https://github.com/niieani/bash-oo-framework): `import`,
  named parameters, try/catch and exceptions with stack traces, a type system for objects. Its author
  advises against building big projects on all of it - complexity. For rill3: named parameters it has
  (`{|a b|}`); errors that stop the script with where.
- **Elvish** (https://elv.sh): the nearest relative - `var`/`set`/`del`, `put`, `each`, `{|x| }`,
  lists and maps, values through pipes, modules by `use`. A failing command is an exception that ends
  the script unless caught; `if` takes a value. For rill3: failure that stops by default; modules.
- **es** (Haahr and Rakitzis, 1993; https://github.com/wryun/es-shell): rc's syntax, lexical scope,
  first-class functions, exceptions; a function definition is just a lambda assigned to a variable.
  For rill3: one kind of function - `def` and a block in a variable are two today.
- **rc** (Plan 9; Duff): lists the one data type, one kind of quote, signals as functions, `<{cmd}`.
  For rill3: fewer forms; process substitution, perhaps.
- **Tcl**: the whole syntax in twelve rules (the Dodekalogue). For rill3: its syntax as a short
  numbered list of rules, every feature placed in one.
- **Oils / YSH** (https://www.oilshell.org): procs and funcs - two units of code; `use`,
  `source-guard`, `is-main`; a standard library written in YSH. For rill3: a library in the language
  itself; a file that knows whether it is the script or a library.
- **NGS** (https://ngs-lang.org): few big concepts - types for multiple dispatch, no classes,
  closures, exceptions; exit codes become exceptions; the standard library written in NGS.
- **Hush** (Lua-based shell, 2021): no user-defined types; a `?` after a command aborts on its failure.
- **Murex** (https://murex.rocks): typed pipes, JSON/YAML/CSV built in, try/catch, a test framework -
  much built in; the opposite of rill3's size aim, but its data formats show what scripts need.
- **Amber** (https://amber-lang.com): compiles to bash; failure must be handled, or the build fails;
  `main` blocks so a file can be imported; its users ask for argument parsing with `--help`.

## Action items

Each names the aim it serves; those marked (owner) change the language and need the owner's word.

1. **(owner) Failure stops the script.** A command that fails outside a condition - `if`, `while`,
   `&&`, `||`, `!` - ends the script with its status and the line, as Elvish, NGS and Amber do; `cmd
   || true` to go on. One rule, no try/catch. Aims: safer and shorter scripts. The corpus has only 2 `||
   exit`, so the gain is safety more than length.
2. **Done (924).** **Modules: `source` once, by name.** A second `source` of a file does nothing (an error now); a
   name with no `/` is looked for in a library path (next to the script, then `$env[RILL3_PATH]`).
   The same word, not a new one - kbool, Elvish, YSH. Aims: one way; shorter scripts.
3. **(owner) Counting.** 23 increments and 5 map counts in 714 lines. One form for it - `set n +=
   1`, or a missing key read as 0 in `$(( ))` - or none, keeping one way. Decide with the numbers.
4. **A library in rill3 itself, not the binary:** `lib/json.cm` (to and from JSON - Elvish, Murex,
   YSH have it built in), `lib/args.cm` (options and `--help` - Amber's users' wish; ws-args is the
   start). Shipped beside the binary, loaded by item 2. Aims: small binary; the language tested by its
   own library.
5. **(owner) OOP stays closures.** No classes, no `$obj.method` - a second way to call; es, Elvish
   and Hush have no user types either. The reference shows the pattern: an object a map of blocks,
   `inherited` by keeping the parent's block before overriding.
6. **(owner) One kind of function, as es has it.** `def f {|x| }` the same as a block in a
   variable, called by name - the defs table and its lookup gone. Aims: one way; a smaller front end.
7. **The rules, numbered and few.** The reference's syntax as a short list, as Tcl's twelve; each
   feature placed under one, a new rule argued for. Aim: simple syntax, kept so.
8. **A size budget.** 132 KB now, as dash. Each feature priced when added (as 909-919 were); the
   front end's ~1 KB (901); TAB completion's 3.5 KB only for the prompt. Aim: small binary.
9. **Move builtins that rill3 can write into the library** where speed allows - measured one by
   one. Aim: small binary.
10. **An independent review** of core changes - the collector, the parser - by a fresh session
    without the change's context, before it is committed (kbool's critic). Aim: fewer faults like 919's.
11. **Tests that do not need GNU tools.** The whole scripts call `date -d`, `seq` and GNU awk; run
    the suite with busybox's tools too, or keep tests to POSIX options. Aim: rill3 runs where sh does.

Not now: classes (kbool, Bash Infinity), multiple dispatch (NGS), typed pipes and built-in data formats
(Murex), process substitution `<{cmd}` (rc), parallel `each` (Elvish's peach), compiling to bash
(Amber) - each a large addition against the size and one-way aims.

## After 923

The image 87,040 bytes to 82,664: Rill's JSON reader and writer, its echo stage, its deep equality and
its decimals - reached by nothing of rill3 but through their own hooks, which tools/cm-reach.py had
counted as roots - taken out (-4.4 KB). rill3's suite runs on both engines in the verify.
