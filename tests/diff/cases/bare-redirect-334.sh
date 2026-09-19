# bare-redirect-334.sh - entry 11 of tests/from-others/CATALOGUE.md: a
# command that is only redirections performs them and yields 0. This
# shell ignored such a command entirely until Iteration 334, so the
# common `> file` idiom created nothing.
d=/tmp/relf-334.$$
rm -rf $d; mkdir -p $d; cd $d
>a.tmp
ls a.tmp
   >b.tmp
ls b.tmp
> c.tmp
ls c.tmp
echo "status=$?"
echo content > d.tmp
wc -c < d.tmp
> d.tmp
wc -c < d.tmp
echo first > e.tmp
>> e.tmp
wc -l < e.tmp
mkdir sub
>sub/f.tmp
ls sub/f.tmp
< a.tmp
echo "read-only-redirect=$?"
v=g.tmp
>$v
ls g.tmp
for n in 1 2 3; do > "h$n.tmp"; done
ls h1.tmp h2.tmp h3.tmp
cd /tmp; rm -rf $d
