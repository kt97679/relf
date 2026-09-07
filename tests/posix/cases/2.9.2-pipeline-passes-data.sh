# XCU 2.9.2. Each command's standard output is connected to the next
# command's standard input, through any number of stages.
printf 'a\nb\nc\n' | wc -l
printf 'a\nb\nc\n' | cat | cat | wc -l
printf 'x\n' | { read -r v; printf 'got=%s\n' "$v"; }
