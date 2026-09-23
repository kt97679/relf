# A backslash escapes the character after it even when the backslash is
# itself an IFS character - it never delimits (Iteration 460, yash
# read-p.tst:185). Both the field scan and the step over a delimiter
# tested IFS first.
printf 'a\\b\n'   | { IFS='\' read a b; echo "1 [$a][$b]"; }
printf 'A \\ B\n' | { IFS=' \' read a b; echo "2 [$a][$b]"; }
printf 'A \\ B\n' | { IFS=' -\' read a b; echo "3 [$a][$b]"; }
printf 'a\\b\n'   | { IFS='\' read -r a b; echo "4 [$a][$b]"; }
printf 'A\\ A \\ \\B\\  C\\\\C\\-C\\\\-D\n' | {
    IFS=' -\' read a b c d; echo "5 [$a] [$b] [$c] [$d]"
}
# ... while the ordinary shapes are unchanged
printf 'a b c\n' | { read a b; echo "6 [$a][$b]"; }
printf 'x:y\n'   | { IFS=: read a b; echo "7 [$a][$b]"; }
printf ' a \n'   | { read a; echo "8 [$a]"; }
# A continuation between an operator's characters (yash quote-p.tst:301)
f=foo
echo "9 ${f:\
+x} ${f#\
#f} ${f%\
%o}"
