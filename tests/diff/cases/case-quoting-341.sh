# case-quoting-341.sh - catalogue entry 16. A `case` pattern keeps its
# quoting per character: `[\q]` matches q, `a\*` matches only a literal
# star, and `a\*b*` keeps the escaped star AND the live one. Until
# Iteration 341 a pattern with any quoting in it was compared literally,
# which was right for `a\*` by accident and wrong for the rest.
case q in [\q]) echo "escaped-bracket";; *) echo "no";; esac
case Q in [\q]) echo "no";; *) echo "bracket-not-matched";; esac
case 'a*' in a\*) echo "escaped-star";; *) echo "no";; esac
case ab in a\*) echo "no";; *) echo "star-is-literal";; esac
case 'a*bc' in a\*b*) echo "partly-quoted";; *) echo "no";; esac
case axbc in a\*b*) echo "no";; *) echo "partly-quoted-rejects";; esac
case abc in a*c) echo "live-star";; esac
case ab in ab) echo "plain-literal";; esac
case ab in x) echo "no";; *) echo "fallthrough";; esac
case ab in x|a*) echo "second-alternative";; esac
case x in 'x') echo "fully-quoted";; esac
case '*' in '*') echo "quoted-star-literal";; esac
case a in '*') echo "no";; *) echo "quoted-star-not-wild";; esac
case '?' in \?) echo "escaped-question";; esac
case z in \?) echo "no";; *) echo "question-is-literal";; esac
case '[' in \[) echo "escaped-bracket-char";; esac
