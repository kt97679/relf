# A group whose opener is alone on the line, reached as an '&&'/'||'
# segment rather than as a whole line. Before Iteration 152 the body
# ran and printed correctly but the construct left status 127: only
# RUN-TOKENIZED's copy of the group dispatch carried the ARGC=1
# multi-line arm, so the lone '{' segment fell through and was
# executed as a command name. Output alone would not have caught it -
# this case exists for the statuses.
true && {
echo brace-after-and
}
echo "st=$?"

false || {
echo brace-after-or
}
echo "st=$?"

true && (
echo paren-after-and
)
echo "st=$?"

# The same group as a whole line, which always worked - here so a fix
# that broke the working path could not pass.
{
echo brace-alone
}
echo "st=$?"

# A group followed by a pipe must still fall through to the pipeline
# splitter rather than running alone, which is what the AT-GROUP-END?
# guard inside DISPATCH-GROUP is for.
(echo piped) | tr a-z A-Z
echo "st=$?"
