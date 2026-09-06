# An operator after a compound command, and the exit status a compound
# command leaves behind.
if true; then echo n; fi && echo m
if false; then echo n; fi && echo m
if false; then echo n; fi || echo o
if false; then true; else echo e; fi && echo z
if true; then false; fi && echo w
if false
then
  echo x
fi
echo "st=$?"
if true
then
  false
fi
echo "st2=$?"

# An operator after "done"/"esac" belongs to the enclosing line, the
# same as one after "fi" (Iteration 106). And a loop that runs no
# iterations exits 0, not with the status of the condition that
# stopped it.
while false
do
  echo never
done && echo after-while-and
echo "s=$?"

for i in a b
do
  echo "i=$i"
done && echo after-for-and

for i in
do
  echo never
done && echo after-empty-for

case x in
y)
  echo never
  ;;
esac && echo after-esac-and

case x in
x)
  echo matched
  ;;
esac && echo after-esac-matched

while false
do
  echo never
done || echo after-while-or
echo "s2=$?"

# a suffix that is a whole further command, not just an operator
for i in 1
do
  echo "loop=$i"
done; echo after-semi

# nested: the inner "done" suffix must not be taken for the outer's
for i in 1 2
do
  while false
  do
    echo never
  done && echo inner-suffix
done && echo outer-suffix
