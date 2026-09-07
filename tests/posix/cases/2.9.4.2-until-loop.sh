# POSIX.1-2017 XCU 2.9.4.2 The until Loop.
#
# until is a compound command of the same standing as while; it runs
# the body until the condition succeeds. It is one of the five
# compound commands the grammar defines and is not optional.
i=0
until [ "$i" -ge 3 ]
do
    echo "i=$i"
    i=$((i + 1))
done
echo "done $i"
