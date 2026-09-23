# A name exported while it has no value has the export attribute at once,
# so a later assignment reaches children (Iteration 469). This shell's
# "exported" was "in the process environment", where a valueless name
# cannot go, and the attribute was forgotten.
export FOO
FOO=bar
sh -c 'echo "1 [$FOO]"'
export A B
A=1; B=2
sh -c 'echo "2 [$A$B]"'
# still unset in a child until it is assigned
export PEND
sh -c 'echo "3 [${PEND-unset}]"'
# unset drops the attribute
export GONE
unset GONE
GONE=x
sh -c 'echo "4 [${GONE-unset}]"'
# an ordinary variable stays unexported
PLAIN=p
sh -c 'echo "5 [${PLAIN-unset}]"'
