# A backslash produced by an unquoted expansion escapes the next
# character in pathname expansion, as bash and dash have it (Iteration
# 428; busybox glob_bkslash_in_var, yash quote-p.tst). A word whose only
# glob characters are escaped that way is not a pattern at all.
d=${TMPDIR:-/tmp}/glob-bs-428.$$
mkdir -p "$d/testdir.TMP" && cd "$d" || exit 1
: > testdir.TMP/name; : > 'a*b'; : > 'a\b'; : > ab
b='test*.TMP/\name'; printf '[%s]\n' $b            # matches testdir.TMP/name
b='a\*b'; printf '[%s]\n' $b                        # not a pattern: stays a\*b
b='nomatch\*'; printf '[%s]\n' $b                   # no match: stays as written
b='a\\*'; printf '[%s]\n' $b                        # escaped backslash, live star
b='a\xb'; printf '[%s]\n' $b                        # no glob character at all
printf '[%s]\n' "$b"                                # quoted: never a pattern
cd / && rm -rf "$d"
