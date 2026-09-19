# bracket-dash-369.sh - a quoted `-` inside a bracket expression is a
# member, not a range: `[0"-"9]` matches three characters where `[0-9]`
# matches ten. Two faults (Iteration 369): the pattern builder did not
# escape a quoted dash, and the matcher read `[0\-9]` as a range from
# backslash to 9 - empty - because it tested for a range before
# resolving the escape.
case - in [0\-9]) echo "dash-member";; *) echo "no";; esac
case 9 in [0\-9]) echo "nine-member";; *) echo "no";; esac
case 5 in [0\-9]) echo "no-five";; *) echo "five-not-in-set";; esac
case 5 in [0-9]) echo "five-in-range";; *) echo "no";; esac
case - in [0-9]) echo "no";; *) echo "dash-not-in-range";; esac
case a in [a\-c]) echo "a-member";; *) echo "no";; esac
case b in [a\-c]) echo "no";; *) echo "b-not-member";; esac
case - in [a\-c]) echo "dash-member-2";; *) echo "no";; esac
d=/tmp/relf-369.$$
rm -rf $d; mkdir -p $d; cd $d
: > f0; : > f1; : > f9
echo f[0"-"9]
echo f[0-9]
echo f[09]
cd /tmp; rm -rf $d
# A `]` is marked and escaped the same way: quoted it is a member,
# unquoted it terminates the bracket (Iteration 370).
case ']' in [a\]]) echo "bracket-member";; *) echo "no";; esac
case a in [a\]]) echo "a-still-member";; *) echo "no";; esac
case ']' in []]) echo "leading-bracket";; *) echo "no";; esac
case b in [abc]) echo "plain-set";; *) echo "no";; esac
# and an unquoted dash from an expansion is a live range, a quoted one
# is a member
x=-9
case 5 in [0$x]) echo "expanded-range";; *) echo "no";; esac
case 5 in [0"$x"]) echo "no";; *) echo "quoted-member";; esac
case - in [0"$x"]) echo "quoted-dash-member";; *) echo "no";; esac
