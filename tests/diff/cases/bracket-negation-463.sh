# Right after a `[`, a `!` or `^` negates the set, so a QUOTED one has to
# be told apart from a live one - and no mark was ever recorded for
# either (Iteration 463, busybox ash-quoting/quoted_punct).
case '!' in [\!]) echo A;; *) echo no-A;; esac
case '!' in ['!']) echo B;; *) echo no-B;; esac
case 'a' in [\!a]) echo C;; *) echo no-C;; esac
case '^' in [\^]) echo D;; *) echo no-D;; esac
case 'b' in [\^b]) echo E;; *) echo no-E;; esac
# ... while a live one still negates
case 'x' in [!a]) echo F;; *) echo no-F;; esac
case 'a' in [!a]) echo no-G;; *) echo G;; esac
case 9 in [![:alpha:]]) echo H;; *) echo no-H;; esac
v='!'; case 'x' in [$v]) echo no-I;; *) echo I;; esac
d=${TMPDIR:-/tmp}/relf-463.$$
mkdir -p "$d" && cd "$d" && touch a.txt b.txt
echo [!a].txt [ab].txt ['!']*
cd / && rm -rf "$d"
