# A lone digit as a case pattern (Iteration 421). ADD-WORD flags an
# unquoted single digit QUOTED - "an ordinary word, not a descriptor" -
# and the pattern matcher read that as a quoted pattern and looked for
# glob marks that had never been recorded: `case x in 2)` was a
# segmentation fault, and with a variable subject it matched only by
# luck. Found by yash's case-p.tst; located with gdb and
# tools/image-where.py. Every form, literal and not.
case x in 2) echo p;; *) echo star-literal;; esac
case 2 in 2) echo two;; esac
case 0 in 0) echo zero;; esac
case a in b|2) echo p;; *) echo star-alt;; esac
case 2 in 2|3) echo alt2;; esac
case 3 in 2|3) echo alt3;; esac
x=2; case $x in 2) echo var;; esac
x=3; case $x in 2) echo wrong;; *) echo right;; esac
case "$x" in 3) echo quoted-subject;; esac
case 2 in "2") echo quoted-pattern;; esac
case 2 in '2') echo single-quoted;; esac
case 2 in [0-9]) echo class;; esac
case 12 in 12) echo two-digit;; esac
for n in 1 2 3; do case $n in 1) echo one;; 2) echo two;; *) echo other;; esac; done
f() { case $1 in 5) echo five;; esac; }; f 5
case 2 in
    0) echo a;;
    2) echo no-final-semicolons
esac
