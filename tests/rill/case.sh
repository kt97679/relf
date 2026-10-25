# tests/rill/case.rill in sh: its expected output
for a in "--no-apply" "-h" "--help" "file.txt" "x" "abc" "a1" "[x]" "" "*" "other"; do
    case $a in
        --no-apply) echo "$a: apply off" ;;
        -h|--help) echo "$a: help" ;;
        *.txt) echo "$a: a text file" ;;
        ?) echo "$a: one character" ;;
        [a-c]??|[!0-9]1) echo "$a: a class" ;;
        '[x]') echo "$a: brackets, quoted" ;;
        "") echo "$a: empty" ;;
        \*) echo "$a: a star" ;;
        *) echo "$a: anything else" ;;
    esac
done
want=abc
case abc in "$want") echo "a variable as the pattern" ;; esac
case nothing in a) echo never ;; esac
echo done
