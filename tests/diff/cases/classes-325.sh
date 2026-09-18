# classes-325.sh - bracket expressions with character classes (XCU 9.3.5),
# in `case` and in pathname expansion. They were unsupported until
# Iteration 325: `[[:alpha:]]` matched nothing, because the scan for the
# closing bracket stopped at the `]` inside `:]`.
d=/tmp/relf-325
rm -rf $d; mkdir -p $d; : > $d/a1; : > $d/b2; : > $d/_x; : > $d/ZZ
case abc in [[:alpha:]]*) echo alpha;; *) echo no;; esac
case 5 in [[:digit:]]) echo digit;; *) echo no;; esac
case " " in [[:space:]]) echo space;; *) echo no;; esac
case A in [[:upper:]]) echo upper;; *) echo no;; esac
case A in [[:lower:]]) echo lower;; *) echo not-lower;; esac
case a in [[:alpha:][:digit:]]) echo either;; *) echo no;; esac
case 9 in [![:alpha:]]) echo negated;; *) echo no;; esac
case _ in [[:punct:]]) echo punct;; *) echo no;; esac
case f in [[:xdigit:]]) echo hex;; *) echo no;; esac
case g in [[:xdigit:]]) echo hex2;; *) echo not-hex;; esac
case ab in [[:alpha:]][[:alpha:]]) echo two;; *) echo no;; esac
case a1 in [[:alpha:]][[:digit:]]) echo mixed;; *) echo no;; esac
echo $d/[[:alpha:]][[:digit:]]
echo $d/[[:alpha:]]*
echo $d/[![:alpha:]]*
echo $d/[a-z][0-9]
v=abc9
echo "${v%[[:digit:]]}"
echo "${v#[[:alpha:]]}"
rm -rf $d
