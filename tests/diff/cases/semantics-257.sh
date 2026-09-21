# semantics-257.sh - C division, a division by zero that stops only its
# command, ${#}, "$*" joined with IFS, quoted and empty case patterns,
# one-line case, and the case word as one word (Iteration 257).
echo $((-7/2)) $((7/-2)) $((-7%2)) $((7%3)) $((6/2))
set -- a b c
echo "${#} $#"
IFS=:; echo "$*"; IFS=; echo "$*"; unset IFS; echo "$*"; IFS=' '; echo "[$*]"
f() { echo "in f"; }
for w in 'a*b' 'axb' ''; do
  case $w in
    'a*b') r=literal ;;
    a\*b) r=escaped ;;
    a?b) r=any ;;
    '') r=empty ;;
    *) r=none ;;
  esac
  echo "$w=$r"
done
case a in "a") r=one ;; esac; echo "r=$r"
case b in a) echo A ;; b) echo B ;; esac
case x in x) f ;; y) echo no ;; esac; echo after-f-case
case in in in) echo in-word ;; esac
case z in
  z) echo multi ;;
esac
# Division and remainder by zero were checked here against bash, which
# reports the error and carries on. POSIX makes an expansion error end a
# non-interactive shell (XCU 2.8.1), dash does, and this shell does since
# Iteration 427 - so those checks are in tests/shell/run-special-error,
# against dash's behaviour, and GOALS.md lists the divergence from bash.
echo $((7/2)) ok
for w in '' x; do case $w in '') echo E;; *) echo N;; esac; done
x=''
case "$x" in '') echo E2 ;; esac
x="a b"
case $x in "a b") echo joined ;; *) echo split ;; esac
