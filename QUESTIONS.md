# QUESTIONS.md — what is waiting on the user

Kept at the user's request (Iteration 514): every question raised with
the user is written here, with where it came from, the options and a
recommendation, so none lives only in a chat reply. **Nothing is
deleted.** An answered question moves to "Answered", with the answer
and where the decision was recorded; an open one stays open for as long
as it takes, and the work that depends on it says so and waits.

When a reply to the user asks something, the question goes here in the
same iteration.

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

**Q2. The two-bit call tag: take the format change? (501)**
A 1 GB code space instead of 4 MB, with 64 one-byte opcodes; measured
performance-neutral (with a frequency-ranked layout, fewer second
dispatches than today: 0.61% against 0.78%, for 145 bytes). It is a
format version and a renumbering of every opcode.
*Recommendation*: not now - the shell image is 120 KB, and nothing
needs more than 4 MB. But **decide before the assembly engine's
Milestone 1**: after it, the change costs both engines.

**Q3. One source for the opcode numbering? (CV8.md 13)**
Four hand-maintained places number the opcodes (CV8.md 2.2), and the
assembly engine would be a fifth. `kernel.4` - or a small generator -
could emit the tables every engine includes.
*Recommendation*: yes, as the first step of Milestone 1, so the
assembly engine's table is generated rather than typed.

**Q4. `LSAVE`/`LRESTORE` as real primitives? (CV8.md 13)**
The locals opcodes know a Forth data structure (CV8.md 6.3); as real
primitives, with the Forth versions deleted, five cells and a fallback
go.
*Recommendation*: yes, before the assembly engine - one special case
fewer to port. Small.

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

## Your notes, captured (514)

- **The input line limit, 80 to 256 columns** - done at 514.
- **SHELL-LANGUAGE.md**: a formal specification, POSIX constructs
  translated into Rill, why "Rill", what each language can do that the
  other cannot, and text-block indentation argued pro and con - Part 3,
  written at 514; Q7 and Q8 wait for you.
- **The assembly engine**: x86-64 first, 32-bit later; the environment
  as the C engine has it - A2 and A3.
