---
id: 07-audience-research
when: before writing, and again before choosing where to publish
applies-when:
  - a write-up is intended for a specific venue, forum, community or team
  - you are about to guess what that audience wants
  - the work will be translated for a second audience
skip-when:
  - the artefact is internal and has exactly one known reader
produces: a named-audience note covering who is there, what that venue punishes, the metric being optimised, and the venue's formatting mechanics
cost: medium; mostly reading, and it replaces guessing
---

# 07 — Research the audience before writing, not after

**Use it** before a technical write-up is drafted, and again before choosing
where it goes.

**Why this exists.** This prompt was not derived from a failure of mine — it was
derived from someone else's document that did the job better than anything in
this library. Its method generalises, and three of its findings applied
immediately to work that had already been through six review rounds.

The insight that makes it work: **read what fails in a venue, not just what
succeeds.** Most people study the popular posts. The sharper material is in the
moderators' list of mistakes, and in the comment threads under articles that
were technically fine and got mauled anyway.

---

```
Before drafting, produce a short written note answering these. Quote real
sources -- specific threads, specific posts, specific comments. If you find
yourself writing what an audience is "probably" like, you have not done this
step.

1. WHO IS ACTUALLY THERE. Name real people or real recurring participants,
   and what they have built. If the audience includes people who have
   implemented the thing you are describing, every claim is going to be
   checked by someone with standing. Find one existing discussion of your
   exact topic and read it end to end.

2. THEIR VOCABULARY, NOT YOURS. What does the community call the things you
   have named yourself? Map your terms onto theirs in the first few
   paragraphs, and introduce your own coinages as local inventions. Using
   private names for public concepts reads as not knowing the field.

3. WHAT THE VENUE PUNISHES. Find the moderation guidance, the "common
   mistakes" post, and at least one thread where a competent article was
   received badly. Note the specific mechanism each time: formatting, a
   categorical claim, an unverified paraphrase, a missing version number, a
   terminology slip. These are cheaper to avoid than to recover from.

4. THE METRIC. Views, rating, bookmarks, comments, replies from experts,
   and adoption are different currencies and do not move together. Name the
   one you want. It determines the title, the length and the ending.

5. THE MECHANICS. Every venue has rules that cost you before anyone reads
   the argument: length limits and fold/cut behaviour, image expectations,
   how much bold is too much, link formatting, tags, difficulty labels,
   markdown dialect. List them and check the draft against the list.

6. THE ROUTE. How does anyone find this? Name the venues in order, and note
   for each whether resubmission is normal, whether self-promotion is
   penalised, and which tags apply. Betting one submission on one site is
   how good work disappears.

7. IF IT IS BEING TRANSLATED. A translation produced from a finished text
   in another language reads as one: calques, the source language's
   sentence rhythm, terms left untranslated where a native term exists.
   Some venues name machine translation as bad faith. A figure-and-
   structure audit cannot detect this. Budget a reading pass by a native
   speaker, and treat that as a different task from checking the numbers.
```

---

## Then check the draft against three tests

These are cheap, and the first two catch the commonest failure in technical
writing: burying the point.

**The first-three-sentences test.** The title plus the first three sentences
must answer two questions: is this for someone like me, and what do I get? Not
what the article is about — what the reader takes away. If paragraph two has
answered neither, the opening is about you rather than them.

**The skimmer test.** Strip everything except headings and images. Does what
remains make someone want to read? If the headings are labels rather than a
narrative, rewrite them as the story.

**The picture test.** Count the images. Zero is the usual answer and it is
almost always wrong. Anything that is currently a column of numbers, an ASCII
diagram, or a structure described in prose is a figure that has not been drawn
yet. A rough diagram beats no diagram; a stock photo is worse than either.

## Notes

**This is the step most likely to be skipped and most likely to pay.** It is
research, it produces no visible output, and it happens before the interesting
work. It is also the difference between writing for an imagined reader and
writing for a real one.

**Applied to this library's own articles**, the three tests above found: no
images at all in either part, an opening that said what the subject was but not
what the reader gets, and a Russian translation made from the finished English —
the exact shape that reads as machine-translated. Two were fixed in an hour. The
third needs a human.
