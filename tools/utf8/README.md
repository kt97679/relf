# tools/utf8 - Iteration 722's UTF-8 probes (not yet in the suites)

- cases.txt and run-cases.sh: 24 one-line cases - UTF-8 and stray high
  bytes through echo, printf, ${#v}, ${v#h?}, case and bracket patterns,
  IFS of two bytes, read, a here-document, command substitution,
  globbing UTF-8 names, names that must not take UTF-8 - each run on
  dash, bash and relf's shells in the C locale, the output compared as
  bytes. run-cases.sh expects a directory g/ holding files named é, ü
  and aé beside it (the glob case), and writes c1.sh..c24.sh there.
- edit-probe.py SHELL: eight line-editor cases on a terminal - ^T, a
  4-byte emoji under backspace, ^W and ^Y over Cyrillic words, history,
  a stray 0xFF typed and passed, TAB completing a UTF-8 file name, cursor
  right. Its history check looks for the two lines adjacent, which the
  redraw between them defeats: read the transcript (722 did).
