---
id: 28-ask-other-models
when: before settling a challenge alone that turns on knowledge outside the repository, a fresh reading of code, a field's established methods, or a search for prior art or programs to test against
applies-when:
  - the answer lives in documentation, papers or other people's code - an instruction set, a toolchain's behaviour, a literature - not in a measurement here
  - code grew quickly and its invariants are subtle: fresh eyes find what the author's do not
  - a decision rests on methods a field has settled (statistics, search, measurement) that you would otherwise reconstruct
  - you need programs, projects or prior art to test against, and memory is all you have
skip-when:
  - a measurement, a build or a test here answers it faster and surer
  - the question needs the repository's state, and no prompt can carry enough of it
produces: one line weighing the challenge - other models useful or not, and why; when useful, one self-contained prompt per question in results/drafts/ask-<topic>-<iteration>.md for the owner to relay; when answers return, results/drafts/ask-<topic>-answers-<iteration>.md - every claim checked, the answers ranked, what is adopted
cost: medium - the owner relays; the checking is the work
---
# 28 — Ask other models when they can help, then check every word

**Use it** at every challenge, as a question to answer in one line: would another
model help here? Most of the time the answer is no - a measurement here settles it.
When the answer is yes, write the prompts; the owner relays them to the models he
chooses and brings the answers back.

**Why this exists.** In one project (forth-vm-evolution, Iterations 479-515), four
rounds of questions to other models - and what each taught:

* **A search** (479-480): programs to test against. Five answers, every one
  checked against its source; some licences and claims were wrong. What held gave
  the held-out applications the search still measures against.
* **An instruction set** (511-512): porting a copy-and-patch JIT to 32-bit ARM.
  Checked with a cross compiler, an emulator, the kernel's source and an
  assembler: the encodings held; two recommended compiler flags were wrong (one
  makes the literal pools it was meant to prevent; one is refused outright on that
  CPU, though an answer called it "the magic flag"); the distribution's default
  stack protector, which none mentioned, mattered. A working round trip came of it.
* **A field's methods** (511-513): selecting under measurement noise. **The
  prompt was wrong twice** - it put the noise at 2-3% (it is 0.96%) and said the
  reference was measured once a run (it is paired, every round). The answers were
  sound for the question asked and mostly irrelevant to the real one; checking
  their premises against the data found the real question (not noise at all).
* **A fresh reading** (511-515): a bug hunt in the JIT. Most claims were wrong -
  one confidently ("high") - and one was a real bug, found by its effect: turned
  into a test, it printed 5 where 7 was right.

So: other models know things this repository does not, and read code without
the author's blind spots; they are also confidently wrong, invent references, and
answer the question asked even when it was the wrong question.

---

```
At a challenge, before settling it alone:

1. Name the challenge in one line and its kind: knowledge outside the
   repository, a fresh reading of code, a field's methods, a search.

2. If a measurement, a build or a test here would answer it faster and
   surer, say so in one line and do that instead.

3. Otherwise write the prompts - one per question (different expertise,
   different attachments, and depth is shared out between questions in one
   prompt), each in results/drafts/ask-<topic>-<iteration>.md:
   - self-contained: what exists, what is already known (so it is not
     repeated), what to answer, in what form;
   - every premise in it checked against the repository and its data first -
     a wrong premise gets a sound answer to the wrong question;
   - the answer asked as checkable claims: exact encodings, flags, triggers,
     numbers, references with links - and "unsure" where unsure;
   - code embedded when the target cannot take attachments (one file to
     paste), attached otherwise; nothing secret;
   - an answer contract at its end (Iteration 542 - answers are read in
     full, so their length is paid for): at most about 900 words; the
     question not restated; each claim with how to check it; references as a
     list with links; "unsure" where unsure.
   Say which kind of model suits each prompt.

4. The owner pastes the answers one at a time (Iteration 542). On each:
   say in a few lines what it adds that the earlier ones did not, what is
   wrong, and whether the question is answered - if it is, the rest need not
   be asked; log it in results/model-usefulness.md (the round, the model as
   the owner names it, new / wrong / verdict).
   Then, with the answers in, check every claim before using any:
   - a claim about code becomes a test, run where it applies (both widths,
     every variant);
   - a claim about a tool or an instruction set is tried with that tool;
   - a number is measured here; a reference is looked up.
   Write results/drafts/ask-<topic>-answers-<iteration>.md: what held, what
   was wrong and how it was shown, what turned up that no answer said, the
   answers ranked, and what is adopted. Adopt nothing unchecked.

5. Index both files; record the round in the progress log.
```

## Artifact

For every challenge: the one-line weighing (step 1-2). When prompts are written:
the files, each self-contained, with its premises' sources named. When answers
return: the verification file - each claim with how it was checked and its verdict.
