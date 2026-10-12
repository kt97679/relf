# tools/utf8 - Iteration 722's UTF-8 probes

In the suites since 723: tests/shell/run-utf8 (the 23 byte cases, dash's
bytes recorded, and the function-name case by status; also on relfsh32
in verify), and the interactive suite's edit-utf8-* and edit-transpose-*
cases. These are the probes as first run.

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

- gen-zero-width.py: shell.4's ZERO-WIDTH table from Python's Unicode
  database, glibc's wcwidth rule (Mn, Me, Cf but the soft hyphen,
  Hangul's medial and final jamo). Rerun it on a newer Python for a newer
  Unicode and paste its output over the table (725).
- scripts-probe.py: nine scripts' editing against bash's readline (724-725).
- more-cases.txt: 724's extra byte-class cases, in run-utf8 since 725.
