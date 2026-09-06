# A loop written entirely on one line (Iteration 117). Until now the
# body had to follow on its own lines; this form was a syntax error.
for i in 1 2 3; do echo "i=$i"; done
for i in a b; do printf '%s ' "$i"; done; echo

# the word list and the body are expanded at different times: the list
# once, when the loop starts, the body on every iteration
w="p q"
for i in $w; do echo "w:$i"; done
n=0
for i in 1 2 3; do n=$((n+1)); echo "n=$n"; done

# while, with the condition re-evaluated each time
i=0
while [ $i -lt 3 ]; do i=$((i+1)); echo "c=$i"; done
echo "after=$i"

# a condition that is itself several commands
j=0
while true; [ $j -lt 2 ]; do j=$((j+1)); echo "j=$j"; done

# nesting: the inner loop is a body line of the outer one
for i in 1 2; do for k in a b; do printf '%s%s ' "$i" "$k"; done; done; echo

# a suffix after done, and $? from a loop that ran nothing
for i in 1; do echo one; done && echo and-ran
for i in ; do echo never; done && echo empty-ran
echo "s=$?"

# break and continue
for i in 1 2 3 4; do if [ $i = 3 ]; then break; fi; echo "b=$i"; done
for i in 1 2 3; do if [ $i = 2 ]; then continue; fi; echo "c2=$i"; done

# quoted words holding the keywords are not keywords
for i in "do" "done"; do echo "q=$i"; done

# still works spread over lines
for i in 1 2
do
  echo "m=$i"
done
