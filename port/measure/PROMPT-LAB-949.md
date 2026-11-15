# For forth-vm-evolution: what relf did with 944's answers (relf Iterations 945-949), and what to try next

A prompt for a session of the lab, from relf at Iteration 949. Attach the lab's newest bundle and relf's
(relf-claude-iter949-*.bundle); relf's tree has everything quoted here - docs/progress/0900-0999.md for
each iteration, port/measure/ for 941-944's scripts, REPORT-944.md for the answers this follows. The lab
is reference for relf, not a working tree of it: change relf nothing; say what it should change.

---

We are continuing my project forth-vm-evolution. Attached: its newest bundle, and relf's at Iteration
949. Read the lab's HANDOFF.md first, as always; this message is an addition to its state, not a
replacement of it.

After relf's report of Iteration 944 (port/measure/REPORT-944.md in relf's tree: relfsh and rill3 on the
ten designs), relf took five things, each measured on relf's own workloads (tools/bench-vm.py's five
shell scripts and start, tests/cm/bench for rill3, the lab's five programs and bench/langs/bench.4 for
Forth), with the condition I set for all of them: **the Forth underneath stays generic, not skewed
towards relfsh**. What they found, in short:

1. **945 - CV8 without the C library** (engine/rt-linux.c, x86-64, i386, AArch64, RISC-V 64): system
   calls, sigaction with the kernel's own struct and restorers (i386 needs two: sigreturn for old-style
   frames, rt_sigreturn for SA_SIGINFO), sigsetjmp in assembly, an allocator (powers of two to 32 KB in
   256 KB regions, larger blocks mapped of their own), string functions a word at a time. relfsh64 at
   start 1,904 KB resident to 288 KB, start 0.61 of the time, run time the same; the engine 39,056 to
   29,464 bytes with the link made smaller (-s, no separate code segment, no build-id). Plain byte loops
   for memmove/strlen/memchr cost the realistic script 3 %; word-at-a-time ones won it back. Clang turned
   a memcpy that called memmove into a jump to itself; memcpy is memmove's alias now.
2. **946 - ten superinstructions, chosen over four families weighed alike** (tools/pair-corpus.py:
   each program's adjacent pairs as a share of its own dispatches, each family the mean of its
   programs, a pair ranked by the mean of the families - Forth programs, the Forth system (CORE, the
   lab's parse.fth), rill3, the shell): `>?BRANCH =?BRANCH DUP?BRANCH`, `(LOOP)BRANCH8`, and the pairs
   `CELLS+ CELL+@ DUPC@ DUP1- OVER+ DUP>R`. Dispatches: Forth programs -9.2 %, the system -7.9 %,
   rill3 -4.5 %, the shell -4.1 % (geomeans). Time on the assembly engine: the Forth programs 0.71-1.00,
   the shell 0.96-0.99. A trap on the way: programs that allocate as they load (bench.4's sieve, bubble,
   matrix) saved as images ran a thousand dispatches and stopped - and made `DUP @` and `?DUP ?BRANCH`
   look generic; counted without them, both were the shell's alone, and were dropped.
3. **947 - the layout lottery**: adding the ten handlers to cv8.c made the lab's sieve 17 % slower on
   the C engine as built (936's layout penalty: where GCC puts each handler). `-falign-labels=16`
   narrows it rather than ending it: the Forth programs geomean 0.963 aligned against unaligned
   (0.81-1.10: ackermann and sieve 0.81, bench.4's matrix 1.10), the shell 0.97-0.99, rill3 0.95-1.00;
   the engine 4 KB larger (33,560 bytes). Adopted.
4. **948 - rill3's collector from 1 MB**, the next collection at four times what lives (its first was
   at 16 MB): tests/cm/bench's calls 16.8 to 1.2 MB peak, its for loop 14.7 to 1.3, at the same speed.
   The assembly engine zeroed a freed 256 MB block on reuse - up to 6.8 times slower once the
   collector ran often - and maps a block past 32 KB of its own now.
5. **949 - packed names, the header reordered** (CV8.md 4.2 in relf's tree): a header is
   `[name][link][count][body]`, the count byte just before the body, so `>NAME` is `1-` (no scan) and
   bit 7 is free: it says "as written". A name is 4-bit nibbles in bytes: the 15 commonest symbols
   `E-RTASLOINDCPMF` take 4 bits, the next 15 `UHBGXKWV?Y>(#)+` take 8, any other byte 16; a name
   that would not pack shorter is laid as written. The symbols were ranked the same way as 946's pairs,
   over the kernel, the shell, rill3 and gforth's 1,836 words, each weighed alike
   (tools/name-symbols.py). The shell's 21,027 characters of names take 13,205 bytes (62.8 %), the
   kernel's 2,111 take 1,457, gforth's 14,404 would take 9,582 (66.5 %); the shell image 125,718 to
   118,883 bytes (-5.4 %), the kernel 10,861 to 10,882. FIND packs its key once (a 128-byte table, a
   nibble at a time): 74 ns a key before, 179 now, so compiling costs more - CPU time 1.03 on parse.fth,
   1.08 on CORE, 1.15 building the shell (dispatches +5.0, +6.4, +3.4 %: the scan and byte loops it
   replaced were cheap ones); rill3's 177 test scripts, compiled at each run, 0.99-1.01; the shell's scripts
   at run time not one dispatch more. 7-bit units, the first design, packed the shell's names to 15,543
   bytes and cost FIND +28-39 % in dispatches: a unit that is not a byte costs a shift and a mask per bit.

What I would like from the lab now - generic questions, on the lab's own workloads first, then relf's
where the lab's tools reach them; measured the lab's way (paired, interleaved, with intervals):

A. **Names.** The designs keep CV8's header and their names as written. Try 949's code on the
   designs the lab ranks by size (smallest, least-memory, portable-small): image bytes, and the outer
   interpreter's dispatches and time on parse.fth. Does the alphabet hold on the lab's own corpus - or
   on other Forths' word lists - and is a different split (14 + 16 symbols and 12-bit others; 13 + 32)
   better anywhere? tools/name-symbols.py prints those for relf's families: within 1 % of each other.

B. **The layout lottery.** How much of the speed differences between the designs - and of the search's
   fitness - is the C compiler's placement of handlers, not the design? For a few designs, the spread
   over builds that change nothing but layout (-falign-labels=16, -falign-jumps, handler order, a
   function or two moved) on the lab's machines. 947 saw 0.81-1.10 on one machine; if the spread is as
   wide elsewhere, a design's rank within that spread is noise.

C. **Superinstructions by families.** The search found fused pairs rarely chosen (665). Is that the
   pairs or the fitness - would 946's equal-weight ranking over the lab's families pick the same few
   pairs again, and are they worth their handlers' bytes and the layout cost in a portable design?
   relf's tools/pair-corpus.py is the method; its report is bench/reports/pair-corpus-946.txt.

D. **The runtime without the C library.** The lab's forth-arm (646) is already free of it; relf's
   rt-linux.c covers four architectures in one file. Compare them: bytes, resident memory at start and
   at peak, start time, and what each leaves out (relf's reads /etc/passwd alone for ~name; no NSS).

E. **For relf's next step, hybrid-native** - native code and CV8 code in one program, the native back
   end beside CV8 as decided (relf's QUESTIONS.md A33: CV8 stays; growth weighed against speed, "+50 %
   in code size and +5 % performance probably not worth it"). What do the lab's JIT designs
   (fastest-x86-64, small-jit, best-all-round) teach about:
   - which words are worth native code, per byte: by static or dynamic count, how many words hold how
     much of the time (the knee), and how stable that choice is across workloads;
   - the cost of a call that crosses between native and threaded code, both ways, and what calling
     convention keeps it low (the top of stack in a register, the stacks' registers, where the return
     address lives);
   - what made the JIT all or nothing per word (REPORT-944.md, 11: THROW, kernel variables, SYSCALL and
     SCAN, return-stack checks) - and which of those a mixed image avoids by design.
   Numbers on the lab's programs first; on relfsh and rill3 (port/lab/build.sh, port/measure/) if the
   ports still build.

For each, say what relf should take - as a mechanism, in the simplest form that does the job - and what
it should not, with the measurement behind it.
