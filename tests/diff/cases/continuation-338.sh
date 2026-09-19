# continuation-338.sh - entry 17 of tests/from-others/CATALOGUE.md: a
# backslash-newline is a line continuation everywhere, including inside
# a reserved word, so a line ending `i\` followed by `f true; then` is
# `if true; then`. Two things were wrong (Iteration 338): the backslash
# marked the word quoted, and a quoted word is never reserved; and the
# token text is the raw source, so the continuation was still in it when
# the word was compared with the reserved words.
i\
f true; then echo if-ok; fi
wh\
ile false; do :; done; echo while-ok
f\
or i in 1 2; do ec\
ho "for-ok $i"; done
cas\
e x in x) echo case-ok;; esac
echo a\ b
echo "quoted \
still-joined"
x=va\
lue; echo "$x"
whi\
le false; do :; done
echo end
