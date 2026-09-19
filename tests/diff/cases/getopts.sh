# getopts: flags, an argument attached and separate, clustering,
# unknown options, OPTIND after the loop, and OPTARG not lingering.
set -- -a -b val -c rest
while getopts "abc:" opt 2>/dev/null
do
  echo "opt=$opt arg=[$OPTARG]"
done
echo "ind=$OPTIND"

set -- -c val -a -z
OPTIND=1
while getopts "abc:" o 2>/dev/null
do
  echo "o=$o a=[$OPTARG]"
done

set -- -ab -cX
OPTIND=1
while getopts "abc:" q 2>/dev/null
do
  echo "q=$q v=[$OPTARG]"
done

set -- plain -a
OPTIND=1
getopts "a" r 2>/dev/null
echo "nonopt r=$r ind=$OPTIND"
