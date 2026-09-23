# set -o pipefail (POSIX.1-2024): a pipeline's status is that of the last
# command in it that failed, and 0 only if every command succeeded
# (Iteration 473). bash is the reference: the dash installed here, 0.5.12,
# predates it.
set -o pipefail
false | true;                     echo "1 $?"
true | false | true;              echo "2 $?"
(exit 3) | (exit 5) | true;       echo "3 $?"
true | true;                      echo "4 $?"
! false | true;                   echo "5 $?"
x=$( (exit 4) | true );           echo "6 $?"
( (exit 6) | true );              echo "7 $?"
set +o pipefail
false | true;                     echo "8 $?"
# the last pipeline of a subshell: its final stage would run in place,
# with nobody left to collect the others' statuses
( set -o pipefail; (exit 7) | true ); echo "9 $?"
