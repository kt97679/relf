# trims-273.sh - ${x#p} ${x##p} ${x%p} ${x%%p} (Iteration 273): the
# literal-and-one-star forms answered by a substring search, the general
# forms by the matcher, and quoted pattern characters taken literally.
show() { printf '[%s]' "$@"; printf '\n'; }
s=/usr/local/lib/libfoo.so.1.2
show "${s##*/}" "${s#*/}" "${s%/*}" "${s%%/*}"
show "${s##*.}" "${s#*.}" "${s%.*}" "${s%%.*}"
show "${s#/usr}" "${s%1.2}" "${s#nomatch}" "${s%nomatch}"
show "${s#/usr*}" "${s##/usr*}" "${s%*.2}" "${s%%*.2}"
show "${s#*}" "${s##*}" "${s%*}" "${s%%*}" "${s#}" "${s%}"
show "${s#*lib}" "${s##*lib}" "${s%lib*}" "${s%%lib*}"
show "${s#*zzz}" "${s%zzz*}" "${s##zzz*}" "${s%%*zzz}"
e=
show "${e#*/}" "${e##*}" "${e%x*}" "${unset_var%%*}" "${unset_var#a}"
a=aaaa
show "${a#a}" "${a##a}" "${a#*a}" "${a##*a}" "${a%a*}" "${a%%a*}" "${a#aa*}"
# the general path
show "${s#*/*/}" "${s##*/l*}" "${s%.[0-9]*}" "${s%%.[0-9]*}" "${s#/?sr}"
show "${s#*[/]}" "${s%[.]*}" "${s##*[!0-9.]}"
# quoted pattern characters are literal
x='a*b*c'
show "${x#"*"}" "${x#*\*}" "${x##*'*'}" "${x%'*'*}" "${x%%\**}" "${x#a"*"}"
z='[ab]c?d'
show "${z#\[ab\]}" "${z#[ab]}" "${z%'?'d}" "${z%?d}" "${z#"[ab]"}"
# patterns from expansions: unquoted they are patterns, quoted they are not
p='*/'
show "${s##$p}" "${s##"$p"}"
q='l*'
show "${s%$q}" "${s%"$q"}"
# inside double quotes the pattern is still a pattern
show "${s##*/}" "${x#*"*"}"
# nested
d=/tmp/dir/file.txt
show "${d%/${d##*/}}" "${d##${d%/*}/}"
