---
id: 27-address-by-name
when: before changing or reading one part of a structured document by a script or a pattern - an item of a numbered list, a row of a table, a column, a section
applies-when:
  - an edit finds its place by a number prefix, a count of separators or an offset
  - a script reads a value out of a table by its column's position
  - the document has more than one list, table or section of the same shape
  - an insertion "after the first one that sorts after" - in order
skip-when:
  - the whole document is regenerated from data each time
produces: for each structured edit or read - the name it was found by, the check that the name occurs once, and the changed unit read back with its neighbours
cost: low
---
# 19 — Find it by its name, then look at what changed

**Use it** whenever a script or a search-and-replace edits or reads one part
of a structured document.

**Why this exists.** In one week of one project, four faults with one cause -
a part of a document found by where it was, not by what it was:

* Open items were found by `index('\n3. ')`. The file's processing routine,
  numbered too, came first: seven iterations wrote open items over the routine's
  steps 3 to 5, and the real list of open items, never touched, went stale. A new
  session following the routine would have found three of its steps gone.
* The end of a table row was found by counting `|` from the row's start. It
  overran into the next row: three rows of an index received their neighbours'
  additions, and the check of the handoff passed it - it only checked that every
  file was listed.
* A held-out score was read from the table's third column. The third column
  was the score measured again; the correlation came back 0.999.
* A new entry was inserted before the first name that sorted after it. The new
  name sorted last; there was no such name, and the script died - the one safe
  failure of the four.

---

```
Before a script edits or reads part of a structured document:

1. ADDRESS BY NAME. Find the section by its heading, the item by its own
   text, the column by its header's name - never by a number prefix, a count
   of separators or an offset.

2. SCOPE THE SEARCH. Find the section first, by its heading; then search
   only between it and the next heading of its level. Two lists that look
   alike are two lists.

3. ONE MATCH OR STOP. The anchor must occur exactly once in its scope;
   zero or two is an error to stop on, not a first match to take.

4. READ BACK WHAT CHANGED. Print the changed unit - the item, the row, the
   column's values - and its neighbours. Check it is where you meant and
   that the neighbours are as they were. A check that the file is still
   valid is not this check.

5. THE EDGES. First, last, empty: inserting after the last item, a table
   without the column, a section with no items. Name what the script does
   for each.
```

## Artifact required

For every structured edit or read: the name it was found by (a heading, an
item's text, a header), the count showing that name occurs once in its scope,
and the changed unit printed back with its neighbours.
