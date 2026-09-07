# POSIX.1-2017 XCU 2.2.2 Single-Quotes - a single-quote must be
# terminated. An unterminated one is a syntax error, and the shell
# must reject the input rather than running any of it.
printf '%s\n' 'this quote is never closed
