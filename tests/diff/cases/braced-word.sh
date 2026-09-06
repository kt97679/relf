# The word in ${VAR:-word} is ordinary word text: it gets expanded,
# quote-stripped and field-split like any other (Iteration 104).
a=a
null=""
unset nope

# parameter expansion inside the word
b=B
echo ${nope:-$b} ${nope:-${b}Z} "${nope:-${b}Z}"

# command substitution inside the word
echo ${nope:-$(echo sub)}
echo "${nope:-$(echo sub)}"

# ...but NOT when the branch is not taken
set_var=x
echo ${set_var:-$(echo RAN)}

# arithmetic inside the word
echo ${nope:-$((2+3))}

# literal text in an unquoted word is field-split; quoted is not
n() {
  echo "n=$#"
}
n ${nope:-a b c}
n "${nope:-a b c}"
n ${nope:-"a b" c}

# "$@" inside the word keeps its own field boundaries
set -- p 'q r' s
n ${nope:-"$@"}
echo ${nope:-"$@"}

# ${VAR:=word} assigns the EXPANDED word
unset X
y=v
echo ${X:=$y} "[$X]"
unset X
echo ${X:=$(echo cs)} "[$X]"

# ${VAR:+word} likewise
echo ${a:+$b} ${nope:+$b}

# trim patterns are expanded too
HOME2=/root
x=/root/src/cmd
echo ${x#$HOME2}
echo ${x#${HOME2}}
p=posix/src/std
sl=/
echo ${p%%$sl*}

# a '}' inside quotes does not end the word
echo ${nope:-"}"} ${nope:-'}'}
echo ${a:+"}"}

# nesting
echo ${nope:-${also_nope:-deep}}
