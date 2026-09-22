# A tilde's result is as if quoted: not field-split, not a pattern
# (XCU 2.6.1; Iteration 435, yash tilde-p.tst:218). HOME with blanks in
# it made `~` two words.
HOME='/path/with  space'; printf '[%s]' ~; echo
HOME='/p/a b'; printf '[%s]' ~/x; echo
HOME='/p/*'; printf '[%s]' ~; echo
HOME='/p q'; printf '[%s]' ${u-~}; echo
HOME='/p q'; x=~; printf '[%s]\n' "$x"
HOME=/h; printf '[%s]' a~ "~"; echo   # (x=~ in an argument: bash expands it, POSIX not - GOALS.md)
