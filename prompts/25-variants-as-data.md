---
id: 25-variants-as-data
when: before adding the third variant of something by editing several places
applies-when:
  - adding one more variant (a machine, a backend, a gene, a format) means edits in several files or functions
  - two variants already share most of their code by copy
  - a new variant broke something far from where it was added
skip-when:
  - there will only ever be two variants, and both exist
produces: the variant's description as one data record, the shared code that reads it, and a test with a fictional extra variant that needs no code change
cost: medium, once
---
# 25 — The next variant is a row, not a copy

**Use it** when adding one more variant of anything means touching code in
several places.

**Why this exists.** The Paleocomputing project (Habr, 2026) put everything
that makes its first machine different - architecture, emulator, firmware,
disk, processor variants, memory limits - in one small file it calls the
machine's passport; one shared handler reads any passport, and the next
machine is meant to be a new file, not new code. To keep that from being a
promise, its tests build a second, fictional machine of another architecture
with no change to the code. Its own history shows why: a fixed copy of one
handler lived inside a package while the other copy was edited, and a machine
ran on the wrong processor variant until the copies were compared. In this
project every gene added in four iterations touched six to eight places in
the evolver - its list of late genes, the expressed set, the crossover
blocks, the expression rules, mutation, random drawing, the build options,
the dictionary dumps - and one addition reused a global name already taken,
which silently replaced another gene's pool.

---

```
Before adding this variant by hand, make it data.

1. LIST THE TOUCH POINTS. Find every place the existing variants are named or
   special-cased. Count them. Three or more for one new variant means the
   variants are code, not data.

2. ONE RECORD PER VARIANT. Move what distinguishes a variant into one record
   - a table row, a small file - holding everything the touch points needed:
   its values, the conditions under which it applies, what it adds to the
   build. The shared code reads the record; it does not name the variant.

3. A FICTIONAL VARIANT IN THE TESTS. Add a test variant that exists only in
   the test, different in every field, and require that it works with no
   code change. If it needs one, the record is incomplete.

4. NO SECOND COPIES. Anything still duplicated between variants is compared
   automatically, or removed.

5. KEEP THE OLD RESULTS. Converting must not change what existing variants
   produce: check outputs, sizes or identifiers before and after.
```

## Artifact required

The touch-point count before and after, the record format, and the fictional
variant's test passing with no code change.
