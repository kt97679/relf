# A $(...) body is ordinary shell text, run through the real tokenizer
# rather than a private whitespace-splitter (Iteration 105).

# several commands
echo $(echo a; echo b)
echo "$(echo a; echo b)"

# nesting
echo $(echo $(echo deep))
echo "outer: $(echo inner: $(echo core))"

# a body spanning several physical lines
echo $(
	echo a
	echo b
)
echo `
	echo bq
`

# pipes and redirection inside the body
echo $(printf 'x\ny\n' | tr a-z A-Z)

# a compound command inside the body. Written across lines: a loop
# written entirely on ONE line is a separate, pre-existing gap (the
# body must follow on its own lines), unrelated to this case.
echo $(
	for i in 1 2 3
	do
		printf "%s" "$i"
	done
)
echo $(if true; then echo yes; else echo no; fi)

# quoting inside the body
echo "$(echo "a b")"
echo $(echo 'c   d')

# exit status propagates
echo $(exit 0) ; echo "s=$?"

# empty and blank bodies produce nothing and no field
n() {
  echo "n=$#"
}
n $(true)
n "$(true)"
n $( )
echo "[$(true)]"

# text either side survives
echo A$(echo b)C
