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
