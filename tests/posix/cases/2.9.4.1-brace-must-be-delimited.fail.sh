# POSIX.1-2017 XCU 2.9.4.1 Grouping Commands, and 2.9 Reserved Words.
#
# '{' is a RESERVED WORD, not an operator: it is only recognised as a
# separate, unquoted token in command-name position. So "{echo" is an
# ordinary word and this input has a '}' with no group to close - the
# shell must reject it rather than quietly doing nothing.
#
# This is the distinction that keeps '(' and ')' out of the reserved
# word list: an operator self-delimits, so "(echo hi)" needs no
# spaces, while "{ echo hi; }" does.
{echo hi;}
