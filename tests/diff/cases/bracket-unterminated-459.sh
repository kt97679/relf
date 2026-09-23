# A bracket expression that never closes is a literal `[` (XCU 2.13.1,
# Iteration 459, yash case-p.tst:318): `case [[ in [[)` matches in dash
# and bash, and here the rest of the pattern was swallowed by a bracket
# waiting for a `]` that never came.
case "[[" in [[) echo A;; *) echo no-A;; esac
case "[" in [) echo B;; *) echo no-B;; esac
case "[x" in [x) echo C;; *) echo no-C;; esac
case "[]" in []) echo E;; *) echo no-E;; esac
case "a[b" in a[b) echo J;; *) echo no-J;; esac
# ... while the closed ones keep working
case "x" in [x]) echo D;; *) echo no-D;; esac
case "a" in [[:alpha:]]) echo F;; *) echo no-F;; esac
case "]" in []]) echo G;; *) echo no-G;; esac
case "a" in [!b]) echo H;; *) echo no-H;; esac
v="[x"; echo "trim=[${v#[}]"
