#!/usr/bin/env python3
"""image-dump.py IMAGE - the dictionary of a saved cell image, as text.

Emits exactly what tools/dict-dump-addr.4 emits when RUN inside the
image:

    S <start> <here>
    H <nfa> <raw count byte>
    N <body-start> <body-end> <name>
    B <addr> <value>          (one per body cell)

so that tools/layout.py can consume either. The difference is that this
reads the image FILE. Producing the dump by running the image needs a
cell engine, which is the one thing standing between this project and
retiring relf.c - see GOALS.md, "Known shortcuts".

Addresses here are START-RELATIVE, which is what a saved image already
stores. The Forth dumper prints absolute run-time addresses and prints
`S <start> <here>` so layout.py can subtract; this prints S 0 <here>
and the rest follows.

FINDING THE WORD LIST. A saved image has an 8-byte header and no
directory: the engine loads it and starts executing at offset 0, so
nothing records where FORTH-WORDLIST lives. It is found by SHAPE
instead - a wordlist is a cell holding 32 (the thread count) followed
by 32 plausible in-image offsets. On the kernel image exactly one
candidate matches, with all 32 threads populated. That is a heuristic,
so it is checked: the walk must reach both COLD and FORTH-WORDLIST, and
every word's body must lie inside the image.
"""

import sys

THREADS_EXPECTED = 32


class Image:
    def __init__(self, path):
        d = open(path, 'rb').read()
        if d[:4] != b'RELF':
            raise SystemExit("%s: not a RELF image" % path)
        self.cell = d[4]
        self.img = d[8:]
        self.mask = (1 << (self.cell * 8)) - 1
        self.sign = 1 << (self.cell * 8 - 1)

    def u(self, off):
        return int.from_bytes(self.img[off:off + self.cell], 'little')

    def s(self, off):
        v = self.u(off)
        return v - (self.mask + 1) if v & self.sign else v

    def find_wordlist(self):
        """The one cell holding the thread count with 32 usable heads after it."""
        n, hits = len(self.img) // self.cell, []
        for i in range(n - THREADS_EXPECTED - 1):
            if self.u(i * self.cell) != THREADS_EXPECTED:
                continue
            heads = [self.u((i + 1 + k) * self.cell) for k in range(THREADS_EXPECTED)]
            if any(h and not (0 < h < len(self.img)) for h in heads):
                continue
            live = sum(1 for h in heads if h)
            if live >= THREADS_EXPECTED // 2:
                hits.append((i * self.cell, live))
        if not hits:
            raise SystemExit("image-dump: no word list found - has the thread "
                             "count changed from %d?" % THREADS_EXPECTED)
        if len(hits) > 1:
            raise SystemExit("image-dump: %d word-list candidates at %s; the "
                             "shape test is no longer unique and this tool "
                             "needs a real directory in the image header"
                             % (len(hits), [h[0] for h in hits]))
        return hits[0][0]

    def walk(self, wl):
        """Every nfa in every thread. Chains are not in address order."""
        out = []
        for t in range(1, THREADS_EXPECTED + 1):
            nfa = self.u(wl + t * self.cell)
            seen = set()
            while nfa:
                if nfa in seen or not (0 < nfa < len(self.img)):
                    raise SystemExit("image-dump: broken chain at %d" % nfa)
                seen.add(nfa)
                out.append(nfa)
                link = self.s(nfa - self.cell)
                nfa = (nfa - self.cell + link) if link else 0
        return out

    def name(self, nfa):
        return self.img[nfa + 1:nfa + 1 + (self.img[nfa] & 31)].decode('latin1')


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: image-dump.py IMAGE [HERE]")
    im = Image(sys.argv[1])
    wl = im.find_wordlist()
    nfas = im.walk(wl)

    names = {im.name(n) for n in nfas}
    for required in ('COLD', 'FORTH-WORDLIST'):
        if required not in names:
            raise SystemExit("image-dump: walked %d words without finding %s - "
                             "the word list at %d is not the right one"
                             % (len(nfas), required, wl))

    # Descending by address, as the Forth dumper emits: newest first, and
    # a body ends where the NEXT word by ADDRESS begins its link cell.
    nfas.sort(reverse=True)
    here = len(im.img)

    # The PROLOGUE: the cells before the first word's link cell. Execution
    # starts at offset 0, so this region is real code and layout.py
    # rebuilds it specially - it is not part of any word's body and the
    # Forth dumper never walks it. cv8.4 emits these as P records; so
    # does this.
    out = ["S 0 %d " % here]
    first_link = min(nfas) - im.cell
    for a in range(0, first_link, im.cell):
        out.append("P %d %d " % (a, im.s(a)))
    for i, nfa in enumerate(nfas):
        cnt = im.img[nfa] & 31
        body = nfa + 1 + cnt
        body += (-body) % im.cell                      # ALIGNED
        end = here if i == 0 else nfas[i - 1] - im.cell
        if not (body <= end <= len(im.img)):
            raise SystemExit("image-dump: word %r has a body outside the image"
                             % im.name(nfa))
        out.append("H %d %d " % (nfa, im.img[nfa]))
        out.append("N %d %d %s" % (body, end, im.name(nfa)))
        for a in range(body, end, im.cell):
            out.append("B %d %d " % (a, im.s(a)))
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == '__main__':
    main()
