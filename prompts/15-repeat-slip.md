# 15 — the second time is a tool

**Fires when** you fix a mistake and recognise it - or a search of the
log shows it - as one you have made before.

**Skip when** the mistake is new. Then record it well (`12`), so the
second time is recognised.

## Why this exists

Care does not prevent a repeated slip; it only lowers the odds per
occasion, and a long project has many occasions. In a shell project's
native compiler, written in Forth, a helper word was defined three times
inside a section that put definitions into a special word list, where
nothing searched for it: three failed builds, three rounds of reading
"Undefined word" messages, a week apart, each fixed by moving one line.
Beside them, two slips of the same family - a word defined below its
first use, and a list created before the word that fills it, so the
word's own code landed where the list's data belonged. Each was found by
debugging, none by looking: every time, the code read correctly to the
person who wrote it.

A twenty-line check - which definitions sit between "make this word
list current" and "put the old one back", and which of them are called
from outside - would have caught all three at once.

## Do this

1. **Search the log for the class, not the instance.** Not "N-STUB24
   undefined" but "defined inside a word list section", "used before
   defined". A slip that recurs under different names is still one slip.

2. **On the second occurrence, mechanise.** Write the check that would
   have caught both occurrences: a lint over the sources, an assertion
   in the build, a rule in the acceptance suite. Make it fail on the
   old, broken version before trusting it (`16`).

3. **If it cannot be mechanised, change the shape.** Put such helpers in
   a fixed place, name them so the mistake is visible, or remove the
   construct that invites it - and say in the log why a check was not
   possible.

4. **Record the class in the register** of known hazards, with the
   iterations where it struck, so the third session meeting it starts
   from the list.

## Artifact required

The search for earlier occurrences of the class, with what it found; and
either the check (with its failing run on the broken version) or the
reason it cannot exist and the change of shape made instead.
