# A braced word - the `word` of ${a+word}, ${a-word} and their : forms -
# is an expansion result, split as a whole and IN ORDER (Iteration 430,
# yash fsplit-p.tst). Its literal text was split a character at a time
# while the expansions inside it were split at the end of the word, so
# ${a+$b $c} gave x p y q.
a=1 b='x y' c='p q'
printf '[%s]' ${a+$b $c}; echo
printf '[%s]' ${u-$b $b}; echo
printf '[%s]' ${a+-$b-}; echo
printf '[%s]' ${a:+$b-$c}; echo
printf '[%s]' ${a+"x y" z}; echo
printf '[%s]' ${a+x  y}; echo
printf '[%s]' ${a+ x }; echo
printf '[%s]' "${a+x  y}"; echo
v=1 o='-a -b'; printf '[%s]' ${v:+$o} end; echo
set -- '1 2' 3; printf '[%s]' ${a+$@ z}; echo
IFS=' 0' n='1 2'
printf '[%s]' ${n+-${n}- -$(echo '3 4')- -`echo '5 6'`- -$((708))-}; echo
IFS=:
printf '[%s]' ${a+x::y}; echo
