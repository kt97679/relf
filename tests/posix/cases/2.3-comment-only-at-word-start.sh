# XCU 2.3 Token Recognition, rule 10. '#' begins a comment only when
# it starts a word; inside or at the end of a word it is ordinary.
printf '%s\n' abc#def
printf '%s\n' '#leading'
echo ok    # this really is a comment
