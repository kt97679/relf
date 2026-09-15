# attic

Code that is no longer built or tested, kept because deleting it would
make a decision hard to audit later. Git history has it either way;
this directory makes it visible.

**Nothing here is built, run, or tested.** It was correct when it was
retired and will rot from the moment anything around it changes. Treat
it as a record of a design that was tried, not as code to reuse
without re-reading.

## What is here and why

Iteration 218 retired every engine except CV8. CV8 gives both the
densest code and the best measured performance, and the encoding
ladder existed to establish that - which it did. Carrying eight more
encodings past the point where the question is settled costs build
time on every change and, worse, keeps eight more shapes that a change
to the shared translator can silently break.

| file | what it was |
|---|---|
| `sod16.c` | the standalone SOD16 engine, 16-bit tokens, calls by word NUMBER |
| `sod16.4` | the SOD16 compiler overlay - twice the size of `cpt16.4`, which is the argument for CPT16 |
| `cpt16.4` | the CPT16 compiler overlay, calls computed arithmetically |
| `thread-chase.c`, `thread-chase.S` | microbenchmark: cell-threaded vs token-threaded call, same visit sequence, so the two differ only in how a call finds its target |
| `size-estimate.py` | whole-image size under alternative code-unit widths, with the 16-bit stream as reference |

## Reviving something

The stages were removed from `tools/lab/build-cv8.sh` and
`tools/lab/forth-tests.sh` in the same commit that moved these files,
so `git show` on that commit is the recipe. The translator,
`tools/sod16.py`, still carries its 16-bit paths: they were left alone
because it is one file shared with CV8 and cutting it apart is surgery,
not deletion.

The ladder's measurements are in `ENCODING-COMPARISON.md` and
`PROGRESS.md`; `ARTICLE.md` depends on them. If those numbers ever
need reproducing rather than citing, revive from the tag or the commit
rather than from here.
