# getopts: flags, an argument attached and separate, clustering,
# unknown options, OPTIND after the loop, and OPTARG not lingering.
set -- -a -b val -c rest
while getopts "abc:" opt
do
  echo "opt=$opt arg=[$OPTARG]"
done
echo "ind=$OPTIND"

set -- -c val -a -z
OPTIND=1
while getopts "abc:" o
do
  echo "o=$o a=[$OPTARG]"
done

set -- -ab -cX
OPTIND=1
while getopts "abc:" q
do
  echo "q=$q v=[$OPTARG]"
done

set -- plain -a
OPTIND=1
getopts "a" r
echo "nonopt r=$r ind=$OPTIND"
