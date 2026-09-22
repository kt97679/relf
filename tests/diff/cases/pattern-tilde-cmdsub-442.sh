# A trim's pattern is a context of its own (Iteration 442, yash
# param-p.tst:324, :359): a leading tilde is expanded there even inside
# double quotes, and an unquoted substitution's output is pattern text.
bracket() { for b_; do printf '[%s]' "$b_"; done; echo; }
HOME=/home/foo a=/home/foo/bar b=/usr/home/foo
bracket ${a#~}  "${a#~}"  ${a#"~"}
bracket ${a##~} "${a##~}" ${a##"~"}
bracket ${b%~}  "${b%~}"  ${b%"~"}
bracket ${b%%~} "${b%%~}" ${b%%"~"}
w='ab\bc'
bracket ${w#$(echo '*')b}  "${w#$(echo '*')b}"  ${w#"$(echo '*')b"}
bracket ${w##$(echo '*')b} "${w##$(echo '*')b}" ${w##"$(echo '*')b"}
bracket ${w%b$(echo '*')}  "${w%b$(echo '*')}"  ${w%"b$(echo '*')"}
bracket ${w%%b$(echo '*')} "${w%%b$(echo '*')}" ${w%%"b$(echo '*')"}
p=/tmp/x; bracket ${p#$(dirname "$p")/} "${p#"$(dirname "$p")"/}"
