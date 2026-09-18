# redirect-rw-298.sh - `<>` opens a file for reading AND writing (XCU
# 2.7.1), creating it if it is not there. The parser recognised it but
# handed it to the executor as a plain `<`, so it opened read-only and
# failed on a file that did not exist (Iteration 298).
d=/tmp/relf-rw-298.$$
exec 8<> $d
echo hello >&8
exec 8>&-
echo "new file: [$(cat $d)]"
printf 'abc\ndef\n' > $d.2
exec 9<> $d.2
read first <&9
echo "read: [$first]"
exec 9>&-
cat <> $d.3 ; echo "created: [$(ls $d.3 >/dev/null 2>&1 && echo yes)]"
exec 7<> $d.2
echo XYZ >&7
exec 7>&-
echo "overwritten: [$(cat $d.2 | tr '\n' ' ')]"
rm -f $d $d.2 $d.3
