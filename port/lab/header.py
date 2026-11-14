#!/usr/bin/env python3
"""port/lab/header.py IMAGE MAKEFILE - the length of a forth-vm-evolution design's image header.

The design's loader (vm.c's load_image, ENC 3) reads: the magic, 8 bytes; a thread count and that
many thread heads; a DOES> tail count and, with SPEC, that many pairs and five cells of locals; THROW's
offset; and, if the magic says F_HOTCALLS, a count byte and that many two-byte offsets. Then the image.
Printed: the header's length in bytes. SPEC and HOTCALLS are the design's Makefile flags."""
import struct, sys, re
img = open(sys.argv[1], 'rb').read(); mk = open(sys.argv[2]).read()
C = img[4]; get = lambda o: struct.unpack_from('<Q' if C == 8 else '<I', img, o)[0]
spec = '-DSPEC=1' in mk; hot = re.search(r'-DHOTCALLS=[1-9]', mk) is not None
o = 8; nth = get(o); o += C + nth * C
nt = get(o); o += C
if spec: o += nt * 2 * C + 5 * C
else: o += nt * 2 * C
o += C                                   # THROW's offset
if hot and img[7] & 0x20: k = img[o]; o += 1 + 2 * k
print(o)
