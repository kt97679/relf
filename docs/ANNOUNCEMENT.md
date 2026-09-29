# ANNOUNCEMENT.md - facts for the announcement article

The user's plan (Iteration 549): an announcement article for ForthHub
and Habr once the project settles down. This file keeps the facts it
will need - each with where it was measured and how to measure it again
- and the caveats that keep it honest. Kept current: whenever a headline
number changes, it changes here. The fuller record is PROGRESS.md (the
log), FINDINGS.md (measurements), OPTIMIZATIONS.md (what was tried).

**Re-measure every number before publishing**; the commands are below.
All measurements so far: one x86-64 machine (a container), nothing else
running, best of three unless said; plus the user's ARM board and a
second x86-64 machine for correctness runs.

## What relf is, in one paragraph

A Forth system and a POSIX shell written in it. A small engine - in C,
or in x86-64 assembly with no C library - runs a byte-token-threaded
image; the kernel image is cross-compiled from Forth source by Forth,
and the shell is Forth code on top. Since Iteration 548 relf assembles
its own assembly engine from Forth source, byte for byte what GNU as and
ld make, and that engine rebuilds itself.

## Headline facts

**Self-hosting** (548-549; SELF-HOSTING.md). relf assembles its x86-64
engine from its Forth source (relfasm64.4, via asm64.4, a 351-line
x86-64 assembler in Forth). Proven byte-identical to GNU as + ld
building the former assembly source - 15,176 bytes - and that engine,
run on the same program, writes itself again, identical: a fixpoint.
**Since 549 the engine's only source is Forth**: `make relfasm64` is
relf running on the C engine; no assembler or linker is involved.
`make verify` checks the fixpoint on every run (asm:fixpoint).

**Another Forth builds the same kernel** (542). gforth 0.7.3, running
relf's cross-compiler (cross.4) unmodified, produces relf's kernel
images - 64-bit and 32-bit - byte for byte: a diverse double-compile.
`make verify` row ddc:gforth.

**Sizes** (549):

| artefact | bytes | note |
|---|---:|---|
| assembly engine (relfasm64) | 15,176 | static, no C library, x86-64 |
| C engine (relf64), stripped | 39,136 | dynamically linked with libc |
| kernel image, 64-bit cells | 9,359 | the Forth kernel |
| kernel image, 32-bit cells | 8,871 | same source |
| shell image, 64-bit | 118,580 | kernel + extensions + the shell |
| **the whole shell, one file** (relfshasm64) | **133,772** | engine + image, static |

**Source** (549, lines): kernel.4 1,853; the shell 13,300 (shell.4
8,199, tree.4 3,991, edit.4 708, pool.4 193, shadow.4 292); cross.4
699; extend.4 158; save-system.4 211; C engine cv8.c 1,710; assembly
engine 2,416 (relfasm64.4, in Forth; comments included); the assembler
asm64.4 351. About 20,800 in all.

**Speed against other languages and Forths** (543; FINDINGS.md 1.1;
`python3 bench/langs/run.py`). Seven small programs, one Forth text for
every Forth, checksums checked against C's; ms, best of three, process
start included:

| | fib(32) | loop 30M | sieve 5M | bubble 3000 | matrix 150 | fannkuch 9 | collatz 1e5 | geo. mean vs relf |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C (gcc -O2) | 4 | 10 | 23 | 19 | 3 | 33 | 19 | 0.08x |
| Go 1.22 | 13 | 22 | 27 | 7 | 5 | 21 | 24 | 0.09x |
| **relf, assembly engine** | **55** | **92** | **421** | **84** | **130** | **362** | **231** | **1.00x** |
| relf, C engine | 58 | 90 | 490 | 103 | 137 | 330 | 218 | 1.04x |
| gforth-fast 0.7.3 | 59 | 87 | 106 | 72 | 78 | 234 | 146 | 0.66x |
| gforth 0.7.3 | 61 | 77 | 129 | 93 | 82 | 338 | 152 | 0.74x |
| pforth 2.0.1 | 150 | 173 | 393 | 279 | 353 | 1,114 | 419 | 2.19x |
| Ruby 3.2 | 228 | 615 | 430 | 364 | 181 | 855 | 427 | 2.57x |
| Python 3.12 | 208 | 844 | 445 | 260 | 163 | 445 | 515 | 2.34x |

relf: in gforth's class (faster on calls, level on the loop, 1.35-1.5x
behind over all); 2.2-2.6x faster than pforth, Ruby and Python; ~12x
slower than C and Go. Why gforth is ahead - not native code, but which
words are primitives - is FINDINGS.md 1.1a.

**The shell against dash and bash** (534; FINDINGS.md 1.2). The same
script, identical output: dash 2.5 ms, bash 7.6 ms, relf 75.7 ms
(assembly engine). **Startup the other way round: relf 287 us, dash 748,
bash 1,108.** Scripts are relf's weak side (~30x dash): the shell's work
is fine-grained Forth; accepted for simplicity (QUESTIONS.md A13).

**Memory** (551; FINDINGS.md 8; `python3 tools/mem-profile.py`), kB,
idle -> after a workload:

| shell | resident | private |
|---|---|---|
| **relf, assembly engine** | **196 -> 240** | **196 -> 240** |
| dash | 1,968 -> 1,988 | 100 -> 120 |
| busybox ash | 1,604 -> 1,812 | 248 -> 392 |
| bash | 3,604 -> 3,736 | 1,548 -> 1,660 |

The smallest resident footprint (no C library); in private memory below
busybox ash, about twice dash, an eighth of bash. A third less than at
545 (308 -> 196 idle): the allocator's memory is zero, so the shell's
buffers are not filled at boot, and they are carved from one arena, so
none is touched until used (551).

**Correctness, checked on every `make verify`** (BASELINE): the CORE
test suite, 2,136 checks, output identical on both engines; a
differential suite of 131 cases; 421 cases in a matrix against bash and
dash as references; 48 POSIX cases; 21 from the mrsh suite; 23 through
a pseudo-terminal (line editor, job control); 83 shell test files, 874
assertions; reproducible images, both cell widths, rebuilt and compared
byte for byte - about seventy rows in all.

**Platforms**: x86-64 (C and assembly engines), i386 (32-bit cells, C),
ARMv7 (an NVIDIA Tegra board running Gentoo; C engine, 32-bit cells) -
one Forth source for 64- and 32-bit images.

**The engine's design, briefly**: byte-token threading (CV8 format, 10
versions); 64 one-byte opcodes and 74 escaped primitives; calls of 2 or
3 bytes to a 4 MB region, which is the whole dictionary (A17); images
position-independent; the dispatch loop at the CPU's indirect-jump rate
(0.8 ns, FINDINGS.md 1.3).

**The process**: 549 iterations, each logged in PROGRESS.md with the
number that decided it; every change checked against a recorded
baseline before it is committed; the measured and the rejected kept
(FINDINGS.md, OPTIMIZATIONS.md, GOALS.md's "Tried and rejected").

## Milestones (the recent ones; PROGRESS.md for all)

- 506: the shell as one executable (engine + image appended).
- 523: the assembly engine complete - no libc, 134 KB shell in one file.
- 528-539: opcodes measured; runtime words kept; superinstructions and
  folded returns removed for simplicity; 64 one-byte opcodes.
- 542: gforth builds relf's kernels byte for byte.
- 544: UTC everywhere; verification in a non-UTC zone.
- 545: the dictionary checked (4 MB, the call reach).
- 548: **self-hosted** - relf assembles its own engine, identical to GNU
  as's, and the engine rebuilds itself.
- 549: the engine's only source is Forth; GNU as leaves the build.

## How to re-measure

    make verify                          # every correctness row, ~15 min
    python3 bench/langs/run.py           # speed against languages, Forths
    python3 tools/mem-profile.py         # memory against dash, ash, bash
    python3 tools/asm-test.py            # the assembler against GNU as
    python3 tools/bench-vm.py 10 CONFIG  # the shell's own benchmarks

Needs: gcc, Go, Python 3, Ruby, gforth, pforth, dash, bash, busybox.

## Caveats to state in the article

- One machine for speed and memory; say which, and re-measure there.
- gforth 0.7.3 is from 2014 (14 June; 0.7.0 was 2008 - this line said
  2008 until the seventh review, Iteration 583); newer gforth is faster.
- "relf beats Python and Ruby" is on these seven small programs; the
  shell's scripts, by contrast, are ~30x slower than dash.
- Resident memory counts shared C-library pages in every process; the
  private column is the fair one per process.
- The self-hosting claim is for the x86-64 assembly engine; the C engine
  (for other platforms, and the bootstrap) is built by a C compiler.

## Audience research (prompt 14, Iteration 553)

Done by prompt 14's method before any draft: real threads, not a guess
at what readers are "probably" like. Gaps are stated at the end.

**1. Who is actually there.** ForthHub (github.com/ForthHub/discussion,
~130 stars, issues and Discussions): Ruvim Pinka (`ruv`), who writes
exact analyses of the standard's semantics (#103, POSTPONE in edge
cases) - every conformance claim will be read by someone who helps
write the standard; Mitch Bradley (Open Firmware, #132); Anthony Howe
(post4, #132); Lars Brinkhoff, whose lbForth the ForthHub wiki lists as
a self-hosting metacompiled Forth bootstrapping from a few lines of C -
the nearest prior art to relf's bootstrap, which the article must name
and compare with, not discover in the comments. And the author: #92
(Dec 2020, kt97679), SOD32 reduced from 32 primitives to 7, measured
708 times slower, with the question whether @ ! and lit could go too.
Habr: a large Russian Forth community (SP-Forth, forth.org.ru), and a
translated series on bootstrapping a Forth from a 512-byte seed
(Miniforth) - self-hosting is a theme this audience already reads.

**2. Their vocabulary.** Threaded code (direct/indirect/token), primi-
tives, inner and outer interpreter, metacompilation (for what relf's
cross.4 does), target image, word sets, "the pearl of Forth" -
CREATE DOES> (#2's list of what makes a Forth recognizable: RPN, one
cell size, visible stacks, CREATE DOES>). relf's own names - "escaped
primitive", "the map", "folded return" - must be introduced as local
names for known things: an escaped primitive is a two-byte token.

**3. What the venues punish.** On Habr: an article with only a console
in it - a 2017 Forth article's comments complained they saw no graphics
at all, just a dull black text console (the picture test); a vague
"which implementation?" - readers asked the author exactly that; and
the "yet another Forth" reflex - a Habr Forth article says only the
lazy have not written their own Forth. The answer to "why this one?"
has to be in the first three sentences. On ForthHub: a conformance
claim broader than what is tested - say "passes the CORE tests (Hayes/
Gerry Jackson's core.fr, both engines)", never "standard Forth"; relf
lacks CORE EXT and other word sets by choice (A23), and says so.
Machine translation: a Russian text made from a finished English one
reads as translated (prompt 14, item 7) - the author writes or reads it
natively.

**4. The metric.** Replies from implementers - the people above - not
views. That argues for a precise, checkable article that invites
measurement ("here is how to reproduce every number"), ending with the
open questions relf has (Q15's opcode choices, the 30x-dash gap),
since #92 got its answer by asking one.

**5. Mechanics.** ForthHub: a GitHub issue or Discussion ("Show and
tell"), GitHub markdown, images by upload, no length limit but threads
are read in email digests - the first paragraph is the whole article
for most. Habr: hubs (Forth has none of its own - "Программирование",
"Ненормальное программирование", "Assembler", "Системное
программирование"), a cut after the introduction, images expected,
tags.

**6. The route.** ForthHub first (the implementers, English), then
comp.lang.forth (where #81's author cross-posted), then Habr (Russian,
written natively), then r/Forth. One submission each; ForthHub threads
stay open for years (#92 is still open).

**7. Translation.** Two texts, not one translated: the Habr audience
wants the story (from 7 primitives to a self-hosted shell), ForthHub
the facts and the method.

**Hooks the research found.** The arc from #92 - 7 primitives and 708x
slower, to 64 opcodes chosen by measured dispatch counts, in gforth's
class - is the story, and it is the author's own. #14 asks what Forth
is for beyond Forth systems and embedded work: a POSIX shell that is
smaller in memory than busybox ash is one answer. Extensibility, not
the stack, is what Habr's commenters said Forth is: the shell's `forth`
builtin, the assembler written in Forth, the engine assembled by it.

**Gaps.** ForthHub's comment threads could not be read: GitHub shows
no comments to a logged-out fetch, and its API's unauthenticated limit
was spent on this sandbox's shared address. How #92 and ChatFORTH
(#147, an AI-related Forth) were received is unknown - and relf was
built with an AI doing much of the work, which the article should state
plainly rather than leave to be discovered. Worth reading, logged in,
before drafting.

**Figures (A25, 554)**: ASCII art, not images - the author's choice,
and ForthHub's email digests keep text and drop pictures. Diagrams at
most 60-64 columns wide, for phones. The picture test of prompt 14 then
reads: whatever is a structure described in prose becomes an ASCII
diagram - the bootstrap chain, the image layout, the dispatch loop.


## Motivation - a draft from the author's story (Iteration 556)

The author's own account, reworded; the facts are his. Written in
English for ForthHub; the Habr version should be written in Russian,
not translated from this (prompt 14, item 7).

**A suggested opening** (prompt 14's first-three-sentences test - who
it is for, and what they get, before the story):

> This is a POSIX shell written in Forth: one static file of 135 KB,
> about 200 kB of memory at idle, and extensible from inside, in Forth.
> Underneath it is a Forth that compiles itself and assembles its own
> x86-64 engine. Here is why it exists.

**The story:**

> I have long been a fan of Forth. What fascinates me most is that one
> person can bring up a working Forth on a new platform in a few days -
> the whole system, compiler included, small enough for one mind to
> hold.
>
> In the 1990s I came across SOD32, Lennart Benschop's Forth: a small
> virtual machine running a machine-independent image. I found it
> beautiful. It had two weaknesses - the limits built into its design,
> and its speed - and RelF, Relative Forth, began as my attempt to fix
> them. It worked, but the gain in speed was modest, and after a while
> I put it aside.
>
> Meanwhile another thought kept coming back: the shell is an
> underrated tool. Most of the glue in our systems - the code that
> connects programs, files and processes - is exactly what the shell is
> good at. Written in Python instead, glue grows longer, and every extra
> line is another place for a mistake, because Python lacks the shell's
> expressiveness for that job. But the shell has two weaknesses of its
> own: it can be extended only with external programs, and it offers
> almost nothing in the way of data structures.
>
> That is where the two ideas met. A shell written in Forth could be
> small and frugal, because Forth is; and it could be extended from
> inside, in Forth itself, given the right builtin. That is how this
> project started.

**Optional bridge** (from the audience research; the author decides):
between RelF and the shell sits ForthHub #92 (December 2020) - SOD32
reduced from 32 primitives to 7, measured 708 times slower. It shows
the same instinct as the rest of the story, and some of ForthHub's
readers will remember the thread.

**Sizes as of Iteration 556** (tests/BASELINE; they grew with the trap
handler and the compile-only list - take any figure above for the
announcement from here, or from the baseline then current): the
assembly engine 15,440 bytes; the whole shell on it, one static file,
134,948 bytes; the C engine's shell 158,628 bytes (x86-64).

## The article, drafted (Iteration 570)

docs/ARTICLE-forthhub.md - for ForthHub, in English; the Habr version
is the author's to write in Russian, not a translation (prompt 14, 7).
Built from this file's facts, re-measured where they could have moved:
sizes and test counts from tests/BASELINE, memory from
tools/mem-profile.py (196 kB resident on the assembly engine, 244 after
work; dash 1,968 resident but 100 private), every shell example run on
both engines first. Its figures are ASCII, under 64 columns (A25).
Prompt 14's tests: the first three sentences say what it is and what
the reader gets; the section heads read as the story; each structure
is a figure - the layers, the bootstrap chain, the memory table.
Exactness, for a standard-writer's reading: "passes the CORE tests"
with what they are, never "standard Forth"; the slow case stated plain;
where each number comes from. Named: lbForth, as the prior art.
For the author to settle, marked [author: ...] in the draft: the #92
paragraph, other prior art, the words on how it was built (an AI wrote
most of it - to be said plainly, as the research concluded), the
repository's URL.

The working copy of the article is now a Claude Doc the author edits;
docs/ARTICLE-forthhub.md mirrors it. The author's changes so far: the
#92 paragraph cut (not related to this project); relfsh, not relf, in
the title and the lede; The shell moved up, right after Why - show it
working first, explain after. And one naming rule, applied through
the text: relfsh is the shell, RelF the Forth; file and program names
(relf64, relfasm64, the relf directory) stay as they are.

Speed, measured again for the article's tables (September 27, 2026,
one core of an Intel Xeon at 2.1 GHz). The shell, tools/bench-vm.py,
CPU time against dash, ten rounds: relfsh 20 to 28 times slower on the
five workloads (asm engine 20-27, C engine 21-28), starting in 0.56 of
dash's time. The Forth, bench/langs/run.py: RelF 2.0-2.4 times faster
than pforth, Python and Ruby; 1.5-1.7 times SLOWER than gforth - the
earlier summary "in gforth's class" was too kind, and is gone; 11-14
times slower than C and Go. bench/langs/run.py had looked for
kernel64.img at the top level since 555's restructure moved it to
forth/ - RelF printed nothing, the run said so; fixed.

## The Habr article, in the author's own style (Iteration 570)

docs/ARTICLE-habr.md, mirrored from its Claude Doc. The author asked for
the English article rewritten in Russian in the style of his Habr
articles - read for it: his 14 articles' openings, and three in full
(535186 on Forth primitives, 546998 announcing ossh, 882860 on
encryption). What they share, and what the Russian text follows:
no section headings, even at six minutes - flowing first-person
prose; an opening that is a concrete trigger or a personal story; a
terminal session or code early, each introduced by one plain sentence
and explained after; questions anticipated ("Кто-то спросит...",
"Предвижу вопрос..."); honest caveats ("Хочу сразу отметить...");
measurements in tables, with the exact commands; bullets only for
parallel cases; an ending that asks readers to point out mistakes.
His spelling: форт and форт система in lower case; tools and languages
in Latin, lower case (sod32, ruby, go, python); people's names in Latin;
numbers without separators; «guillemets». His hubs so far: Ненормальное
программирование (the Forth article), *nix, Настройка Linux,
Системное администрирование.
Choices: the title "relfsh: POSIX shell, написанный на форте", shaped
like ossh's; decimal commas, versions keep their points; the closing
question made self-contained - how the 64 opcodes were chosen is said
in it, since the English text lost that explanation with the #92
paragraph. 1,819 words; diagrams re-padded for Cyrillic and checked by
script (joints aligned, widest line 63 columns).

## After the fifth and sixth reviews (Iteration 571)

Two reviews by other Claude instances built relf, ran it and checked the
articles against the repository. Their findings, each checked here:

The user's decision on Habr: keep improving BOTH texts. When the article
is finished he will contact Habr, explain how it was written, show the
project and the text; if they confirm it cannot be published as it is
(rule 4: texts written or edited with neural networks), he keeps a
corrected reference text to write his own from.

Bugs a reader meets in minutes: Ctrl-C in loops - fixed, 571; the line
editor counts bytes, so Backspace in Cyrillic leaves half a character;
PWD not set at startup when the environment lacks it (POSIX requires
it); the demo's first line shows nothing - the prompt's redraw (\r and
erase to end of line) wipes an unterminated `5 `. printf '%.2f': for
"what it is not".

Article claims to correct: calls are relative to the IMAGE BASE, not to
the call site (kernel.4's CALL,; two bytes reach the first 16 KB of the
image) - 570's wording was wrong; "smallest by far" and "starts faster
than dash" hold against a dynamically linked dash only - a static musl
dash is about as small (to be measured here); the speed ratios include
dash's own startup, the workloads being tiny - size them so dash takes
100 ms or more; say the benchmarks ran on a VM, or run them on fury;
"only that command fails" holds for errors the system detects - a stray
store kills the shell; the fuzzing sentence: 173 of the 1,000 programs
were set aside where dash and bash disagree, and yash's 9 were
legitimate differences, not bugs; the closing question is answered in
CV8.md (Gforth; Proebsting's superoperators) - name them, ask sharper;
the sod32 and Benschop links are dead (XS4ALL); the README's sizes are
old; 90 test files, not 91 (run-all is the driver); the random
instruction check accepts equivalent encodings; authorship - 646 of the
650 commits are Claude's: "almost all", and the author's part named;
bash (enable -f), ksh93 and zsh load compiled builtins - the story's
"only external programs" is POSIX sh's; initramfs needs more than a
shell (busybox). Content: show DO-SEQ, the builtin API in five lines;
why the assembly engine is not faster (ASM-ENGINE.md: both at the
indirect-jump floor; its point is no libc); Claude earlier than the end;
long lists and the wide table in spoilers (Habr's rule for mobile);
versions of dash, bash, busybox; the UTC wording.

Measured again (Iteration 576, the container - a VM, one vCPU). Memory:
relfsh asm 200 kB resident idle, a static musl dash 192 - as small, not
"smallest by far"; the file 137,612 bytes against 169,720. Speed at
SCALE=25, where startup no longer dominates: 41-59x dash on scripts;
start 0.53 of dash's, where a static dash takes 0.45. The article's
tables and sentences need these numbers - and a named CPU (fury) would
be better than the container's masked one.

## After the seventh review (Iterations 582-583)

The Habr article, reviewed in a separate chat - blind first, then
against this file and QUESTIONS.md; it built the branch, ran the demo,
`make test` and `make verify`, and tested in a pseudo-terminal. Its
findings, by the review's numbers, and what became of them:

- #1, an unbalanced stack killed the shell (`forth '1 2 3'`, `forth
  'DROP'` - silently on relfasm64), where the article said a Forth error
  fails its command only. The user: fix it. Iteration 582, RUN-CAUGHT:
  the stack put back, "stack changed by N cells", status 1, 16 padding
  cells; both articles now name the check and what is still unsafe (a
  store into the shell's memory, more than 16 cells taken).
- #2, `make test` does not run every suite: it runs CORE and the shell
  suite at both widths and the comparison with bash; `make verify` runs
  every suite. Said so, both. And `make verify` failed on a clone made
  as Try it says - no local master: fixed in 582.
- #3, "every suite runs on both engines": what both engines share, named.
- #4, DDC's scope: the kernel only - the rest RelF builds, the C engine
  a C compiler. Added, both; and who proposed DDC - Henry Spencer, 1998,
  as Wheeler's dissertation says; Wheeler formalised it. Rewritten, both.
- #5, examples/README.md still said "no isolation, an error aborts the
  shell", from before A24. Rewritten in 582.
- #6, the static dash is built with -Os: said, both, and why it is slower
  at scripts - it is in the table for memory and start.
- #7, "on any machine, one command": what bench-report.sh needs is at its
  top, and what is missing is skipped. Both.
- #8, the assembly engine "no faster" beside a Forth table where it is
  15% faster: 0-5% on scripts, about 15% on the Forth programs, matrix
  and fannkuch faster on C. Both.
- #9, seq is eight lines of code, not a dozen; map's 33 are without
  comments. Both.
- #10, 131 and 132: the parliament and the rewrites ran over 131 scripts,
  the 132nd came later. Both.
- #11, Backspace and Cyrillic: withdrawn by the reviewer - it works.
- #12, $ENV is read by interactive shells only (POSIX): both.
- #13, a Forth primer for readers who do not know Forth: two sentences,
  Habr only - ForthHub's readers know it.
- #14, "the whole stack" reads as the data stack: "chain", both.
- #15, «15592 байта». #16, the English copy's broken fence and "here-
  documents": the copies are the Docs' exports now (below).
- #17, «далеко впереди»: 4 to 13 times less resident memory. Both.
- #18, dash's start still weighs (1.7 ms, 5-9%): "at most a tenth". Both.
- #19, the ratios from the rounded table differ by 0.01: "from the
  unrounded times"; C and Go 16 to 17 times. Both.
- #20, mutation testing: random opcode swaps out of 3,699 sites, one of
  the 20 caught only after a test was added. Both.
- #21, the assembler knows only what the engine needs and refuses the
  rest. Both. #22, gforth 0.7.3 is Ubuntu's, from 2014. Both.
- #23, language: the clear errors applied (hyphens, calques, «Чисел с
  плавающей точкой», «равнозначных кодировок», «регистровым операндом»,
  the UTC sentence, «раскрытий», Proebsting's genitive, the self-harness
  sentence); the matters of taste left to the author.
- #24 (the 2013-2016 gap), #25 (SOD32's case), Claude in the lede: the
  author's; open. #26, the two 1,564 kB rows: right (Iteration 585) - in
  fury's report 20260928T2234Z, which the articles use, dash and relfsh
  on the C engine both read 1,564 kB resident, private 120 and 400.
  relfsh-C's resident moves between runs (1,624 at 2221Z, 1,528 on
  09-29) with the shared C library pages its Rss counts (928-1,024 kB);
  dash's stays 1,564. The Benschop link, which only the Habr text had:
  in both now.

Unchanged: the numbers from fury (the memory at rest measured here with
the new shell as before, 196-200 kB); the byline dates, set at
publication.

The copies. docs/ARTICLE-*.md were written by hand from the Docs, and
an earlier check compared sizes - equal by coincidence, not proof; the
English copy had a broken fence the Doc does not. Now each copy is the
Doc's own markdown export, saved as a file of the Doc (Claude Docs
create blob) and read into the container by the Artifact tool, less
the byline line. The export's conventions replace the hand-made ones.
