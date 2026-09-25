# QUESTIONS.md — what is waiting on the user

Kept at the user's request (Iteration 514): every question raised with
the user is written here, with where it came from, the options and a
recommendation, so none lives only in a chat reply. **Nothing is
deleted.** An answered question moves to "Answered", with the answer
and where the decision was recorded; an open one stays open for as long
as it takes, and the work that depends on it says so and waits.

When a reply to the user asks something, the question goes here in the
same iteration.

## What blocks what - in the order the work needs them

1. *(Q2, Q3 and Q4, which blocked the assembly engine's Milestone 1,
   were answered at 516.)*
2. **Before its Milestone 4**: **Q5** (`~user`) and **Q6** (the time
   zone). Each has a default, recommended below, that the engine
   would follow unless you choose otherwise.
3. **Before any Rill implementation begins** - the design waits on
   these; no code does: **Q7** (text blocks), **Q8** (the other open
   points), **Q10** (structured values across processes), **Q11** (the
   default lifetime of a job).
4. **Blocking nothing**: Q1 (the space options), Q9 (divergences kept
   on purpose), Q12 (binary plugins).

## Open

**Q1. The space audit: which, if any? (509)**
`tools/image-budget.py` found: headers are 21.6% of the 64-bit shell
image and 23.1% of the 32-bit; full cells holding offsets or sizes come
to about 2 KB, at 64-bit only; every DOVAR word carries three unused
bytes, about 2 KB. Options:
(a) an image that keeps names only for a documented extension API -
about a sixth smaller at both widths, and `forth` sees only that API;
(b) 4-byte fields for the offset cells - ~2 KB, 64-bit only;
(c) DOVAR without the three bytes - ~2 KB, against the one rule for a
parameter field that four past defects came from (FORTH-STYLE.md 12);
(d) none.
*Recommendation*: (a) if size matters to you - it is the only lever
at both widths; I would leave (b) and (c). *Blocks*: nothing.

**Q5. `~user` without libc (513).**
libc's `getpwnam` also asks NSS (LDAP, systemd-homed); an engine with no
libc can read only `/etc/passwd`. Keep the primitive's contract - as you
decided for the environment (A3) - with the assembly engine reading
`/etc/passwd`?
*Recommendation*: yes; the reduction is inherent to having no libc.

**Q6. The time zone without libc (513).**
`LOCAL-TIME` (prompt escapes `\t`, `\D{...}`) uses `localtime_r`, which
reads `TZ` and `/etc/localtime` (TZif).
*Recommendation*: keep the contract; the assembly engine gives UTC
first, and the TZif reader is its own later step.

**Q7. Rill's text blocks: indentation, or a delimiter? (503, 514)**
You asked for pros and cons, especially with several levels of
indentation: SHELL-LANGUAGE.md, "Text blocks", sets out four designs
with a nested example of each.
*Recommendation*: the closing delimiter whose indentation is the
margin (design C there).

**Q8. Rill's other open questions (503).** Records at the prompt
(JSON on a marked port?); a softer failure rule at the prompt than in
scripts; the kernel in Forth. And the name - SHELL-LANGUAGE.md, "Why
Rill", says why; it is easy to change.

**Q10. Rill: how structured values cross a process boundary (515, 516).**
*Refined at 516, from the user's proposal*: JSON in the environment,
recognised - but by the script's use, not the value's content: every
value arrives as text; a list or record exports as JSON automatically;
a structural operation on text (`$CFG.host`, iterating, spreading)
decodes it there, an error if it is not JSON; scalars are never
converted, so `VERSION=1.0` stays `1.0`. SHELL-LANGUAGE.md Part 4 shows
why detection by content misfires (the "Norway problem").
*Recommendation now*: that. The earlier options follow.
The environment is `NAME=VALUE` strings for every program, most not
Rill. Options, argued in SHELL-LANGUAGE.md Part 4: (1) only text is
exported, and a structure crosses by explicit encoding
(`export CFG = json($cfg)`, `from-json($CFG)` on the other side);
(2) automatic, with a marker variable recording each export's kind -
seamless, but stale when anything in between changes the value, and
it re-reads text unasked; (3) lists tied to a separator, as zsh's
`PATH`. For Rill-to-Rill calls, a value port (descriptor 3, JSON) that
carries a script's `return` value back to its caller.
*Recommendation*: (1), JSON as the standard codec, plus value ports
for Rill-to-Rill calls; never functions in the environment (bash's
exported functions were Shellshock).

**Q11. Rill: the default lifetime of a job (515).**
`par` covers fork-join work; a server started for a test run, a
coprocess, and a daemon need jobs as values (`spawn`, `kill`, `wait`,
ports to talk through). What happens to a job its script never waited
for: it runs on, orphaned (as in sh); it is stopped when the script
ends; or it is stopped when the block that started it ends.
*Recommendation*: stopped when the script ends, by default - no orphan
is an accident; `with` binds a job to a block; `detach` lets one
outlive the script; at the interactive prompt, jobs live as long as the
shell, as in sh.

**Q12. Forth plugins in image form? (516)** The user's thought: load
compiled extensions, not source. What it takes: a plugin compiled
against one shell image calls that image's words by their offsets, so
loading it means relocating its own calls by where it lands, resolving
its calls into the host by name (`FIND`), and linking its headers into
the host's 32 hashed threads - a small linker, perhaps 150 lines of
Forth; variable slots and branches are relative already and move
untouched. What it buys, measured: loading from source costs about
0.4 ms per KB, so for extensions of a few KB nothing; it matters for
extensions of tens of KB, for distributing one without its source, and
as a first step towards GOALS.md item 6, where Forth writes machine
code into images. *Recommendation*: design recorded, build when an
extension is big enough to need it. CV8.md 13.

**Q9. Divergences kept on purpose - revisit any? (GOALS.md)**
Recorded as deliberate, listed so they are not forgotten:
`return` outside a function inside a loop reports and carries on, as
bash does, where dash leaves the script (426); `a=b exec 1>&1` exports
`a`, as bash does (424); the expansion order for special builtins,
functions and external commands is bash's (484); `echo` processes no
escapes, as bash's does. *Recommendation*: keep them all.

## Answered

**A1. The five questions of Iteration 499** - answered at 500 and
recorded in GOALS.md "What comes next": measure the two-bit call tag
(done, 501); design a shell language from its own principles (Rill,
503); no two-pass compiler, audit the full cells instead (509);
an assembly engine; examples of `forth` with sockets (505).

**A2. The assembly engine's architecture (513 -> 514).** x86-64 now;
the 32-bit engine is revisited when the 64-bit one is complete.
ASM-ENGINE.md.

**A3. The environment in the assembly engine (513 -> 514).** Keep the
C engine's behaviour, for consistency between engines: the engine keeps
the environment, as libc does, and `EXECVE` passes it. No shell change.
ASM-ENGINE.md.

**A4. The bare engines (507).** Kept, beside the single-file shells:
they run the kernels, which bootstrap everything. And everything is
named by cell width - `relf64`/`relf32`, `kernel64`/`kernel32`,
`relfsh64`/`relfsh32`.

**A5. `prompts/` and the article (497).** The prompt library is kept
whole - you extend it across projects - and the article about the
Forth shell is written when the project is complete.

**A6. The two-bit call tag (Q2; 501 -> 516).** Not now: the format
stays, and switching later is not a big deal, in the user's words.

**A7. One source for the opcode numbering (Q3; CV8.md 13 -> 516).**
Yes, as the assembly engine's Milestone 1's first step.

**A8. `LSAVE`/`LRESTORE` as real primitives (Q4; CV8.md 13 -> 516).**
Yes. Looked at closely it is less small than first said: the Forth
versions report overflow with `ABORT"`, a catchable error, and an engine
that owns the save stack must still raise exactly that. So: the engine
owns the stack, and the five cells at image offset 8 become one - a
word the engine calls to report the error in Forth. **Done at 517**,
with the image format's version raised to 6.

## Your notes, captured (514)

- **The input line limit, 80 to 256 columns** - done at 514.
- **SHELL-LANGUAGE.md**: a formal specification, POSIX constructs
  translated into Rill, why "Rill", what each language can do that the
  other cannot, and text-block indentation argued pro and con - Part 3,
  written at 514; Q7 and Q8 wait for you.
- **The assembly engine**: x86-64 first, 32-bit later; the environment
  as the C engine has it - A2 and A3.

## Your notes, captured (516)

- **JSON in environment variables, detected** - Q10, refined: detection
  by the script's use rather than the value's content.
- **"Can't change the libc contract; data comes back only through
  stdout, stderr and the exit code"** - right, with two refinements
  (the arguments, and every inherited descriptor):
  SHELL-LANGUAGE.md Part 4, "What a process can exchange".
- **Forth plugins in image form** - Q12, with what it would take.
