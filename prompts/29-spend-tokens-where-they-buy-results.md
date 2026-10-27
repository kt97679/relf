---
id: 29-spend-tokens-where-they-buy-results
when: at a session's start, and whenever you write a record, a report or a reply, read a pasted input, or ask other models - in work that runs over many sessions
applies-when:
  - every session starts by reading the project's own documents
  - records (a log, an index, a state file) are written every session
  - inputs arrive raw - listings, logs, whole files - or several models answer one question
skip-when:
  - a one-off question in a fresh session: nothing accumulates
produces: the big sinks named and measured, each cut with its size before and after; records written once
cost: low - habits, and a measurement before and after
---
# 29 — Spend tokens where they buy results

**Use it** when a project's sessions keep getting heavier: at a session's start, at
every record, report and reply, when reading what someone pasted, when asking other
models.

**Why this exists.** Every model call reads everything in its context again; a
session of fifty tool calls reads its first message fifty times. Caching makes the
repeats cheaper, not free, and no more useful. In one project (forth-vm-evolution,
Iterations 535-542) the sinks were whole things, not words:

* **the state file every session read whole** had grown to 59 KB of accumulated
  history; the present fitted in 12.5 KB, the rest moved verbatim to a reference
  read on demand;
* **a directory listing of thousands of lines** was pasted to answer a question a
  one-screen `du` summary answers;
* **five models answered each question**; in two rounds one answer carried the
  round and two added little;
* **each step's facts were written four or five times** - the log, the index, the
  state file, the batch's notes, the reply.

Trimming polite words would have saved nothing measurable beside these. Two sources
say the same, and add that an unclear request is the costliest of all, through the
wrong answer and retry it causes: "Токеномика для самых маленьких"
(habr.com/ru/articles/1099264) and "Две грамматики за один вечер"
(github.com/melixetian/ai-playbook, Grammar.md - whose percentages its own appendix
marks as illustrative and unreproduced: measure, do not quote them).

---

```
Before a session, and at each record, report, input and question:

1. Find the big sinks first and measure them: what every session reads whole,
   what a long session carries (pasted inputs, tool outputs), how many answers
   a question gets, how often one fact is written. Cut those before any wording.

2. Keep the state a session starts from as a card - the present, the next
   step, the open decisions, the routine - with a size you check. History and
   background move to a reference read on demand, verbatim: nothing is lost,
   only no longer read by default (prompt 07, item 11).

3. One fact, one home. The detail lives in its document; a log entry says
   what, the numbers and the files in a few lines and points there; an index
   line is one sentence (prompt 12, item 8).

4. Inputs and outputs: aggregates and the lines that matter, never whole
   files, listings or logs. Ask for summaries - a `du` table, the failing lines
   and their neighbours - not dumps; cut tool output to what the next decision
   needs (prompt 11, item 11).

5. Ask clearly once rather than vaguely twice: the result wanted, the
   conditions that matter, how it will be checked. A vague request costs a
   wrong answer and a retry; a hidden assumption in a question gets a confident
   answer to it.

6. Other models' answers carry a length cap and arrive one at a time, each
   assessed before the next is asked for; stop when the question is answered,
   and keep a ledger of which model helped (prompt 28).

7. Replies lead with the answer; detail when asked. Start a fresh session at
   natural breakpoints, from the card.

8. Spend more where it pays: a deciding example, the code that matters, a
   stronger model for a hard step, a plan before a wide change. Judge by the
   cost of the finished task - the human's time included - not by one call's
   tokens. Measure before and after; never add claimed savings up - they
   overlap.

9. A sequence of steps that recurs - in every routine run, every session, or
   typed by hand a second time with more to come - becomes a script, tested
   like any change. The script does the mechanics; the judgment stays with
   the session, marked by TODO lines the script leaves. A one-off analysis
   keeps its script beside its result, but is not made into a general tool.
```

## Artifact required

At a session's start: the size of what it read whole. At a cut: the sink, its size
before and after, and where the moved text went. For other models: the ledger line
per answer.
