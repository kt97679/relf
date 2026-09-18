# pure-sh-bible-327.sh - the idioms from dylanaraps/pure-sh-bible, a
# corpus of pure-POSIX techniques written by someone else entirely.
# The read loop at the heart of several of them - `while read -r line
# || [ -n "$line" ]` - looped for ever here until Iteration 327: `read`
# left its variable untouched at end of input where POSIX assigns the
# empty string.
# --- Strip pattern from start of string
lstrip() {
    # Usage: lstrip "string" "pattern"
    printf '%s\n' "${1##$2}"
}

# --- Strip pattern from end of string
rstrip() {
    # Usage: rstrip "string" "pattern"
    printf '%s\n' "${1%%$2}"
}

# --- Trim leading and trailing white-space from string
trim_string() {
    # Usage: trim_string "   example   string    "

    # Remove all leading white-space.
    # '${1%%[![:space:]]*}': Strip everything but leading white-space.
    # '${1#${XXX}}': Remove the white-space from the start of the string.
    trim=${1#${1%%[![:space:]]*}}

    # Remove all trailing white-space.
    # '${trim##*[![:space:]]}': Strip everything but trailing white-space.
    # '${trim%${XXX}}': Remove the white-space from the end of the string.
    trim=${trim%${trim##*[![:space:]]}}

    printf '%s\n' "$trim"
}

# --- Trim all white-space from string and truncate spaces
# shellcheck disable=SC2086,SC2048
trim_all() {
    # Usage: trim_all "   example   string    "

    # Disable globbing to make the word-splitting below safe.
    set -f

    # Set the argument list to the word-splitted string.
    # This removes all leading/trailing white-space and reduces
    # all instances of multiple spaces to a single ("  " -> " ").
    set -- $*

    # Print the argument list as a string.
    printf '%s\n' "$*"

    # Re-enable globbing.
    set +f
}

# --- Split a string on a delimiter
split() {
    # Disable globbing.
    # This ensures that the word-splitting is safe.
    set -f

    # Store the current value of 'IFS' so we
    # can restore it later.
    old_ifs=$IFS

    # Change the field separator to what we're
    # splitting on.
    IFS=$2

    # Create an argument list splitting at each
    # occurance of '$2'.
    #
    # This is safe to disable as it just warns against
    # word-splitting which is the behavior we expect.
    # shellcheck disable=2086
    set -- $1

    # Print each list value on its own line.
    printf '%s\n' "$@"

    # Restore the value of 'IFS'.
    IFS=$old_ifs

    # Re-enable globbing.
    set +f
}

# --- Trim quotes from a string
trim_quotes() {
    # Usage: trim_quotes "string"

    # Disable globbing.
    # This makes the word-splitting below safe.
    set -f

    # Store the current value of 'IFS' so we
    # can restore it later.
    old_ifs=$IFS

    # Set 'IFS' to ["'].
    IFS=\"\'

    # Create an argument list, splitting the
    # string at ["'].
    #
    # Disable this shellcheck error as it only
    # warns about word-splitting which we expect.
    # shellcheck disable=2086
    set -- $1

    # Set 'IFS' to blank to remove spaces left
    # by the removal of ["'].
    IFS=

    # Print the quote-less string.
    printf '%s\n' "$*"

    # Restore the value of 'IFS'.
    IFS=$old_ifs

    # Re-enable globbing.
    set +f
}

# --- Get the first N lines of a file
head() {
    # Usage: head "n" "file"
    while IFS= read -r line; do
        printf '%s\n' "$line"
        i=$((i+1))
        [ "$i" = "$1" ] && return
    done < "$2"

    # 'read' used in a loop will skip over
    # the last line of a file if it does not contain
    # a newline and instead contains EOF.
    #
    # The final line iteration is skipped as 'read'
    # exits with '1' when it hits EOF. 'read' however,
    # still populates the variable.
    #
    # This ensures that the final line is always printed
    # if applicable.
    [ -n "$line" ] && printf %s "$line"
}

# --- Get the number of lines in a file
lines() {
    # Usage: lines "file"

    # '|| [ -n "$line" ]': This ensures that lines
    # ending with EOL instead of a newline are still
    # operated on in the loop.
    #
    # 'read' exits with '1' when it sees EOL and
    # without the added test, the line isn't sent
    # to the loop.
    while IFS= read -r line || [ -n "$line" ]; do
        lines=$((lines+1))
    done < "$1"

    printf '%s\n' "$lines"
}

# --- Count files or directories in directory
count() {
    # Usage: count /path/to/dir/*
    #        count /path/to/dir/*/
    [ -e "$1" ] \
        && printf '%s\n' "$#" \
        || printf '%s\n' 0
}

# --- Get the directory name of a file path
dirname() {
    # Usage: dirname "path"

    # If '$1' is empty set 'dir' to '.', else '$1'.
    dir=${1:-.}

    # Strip all trailing forward-slashes '/' from
    # the end of the string.
    #
    # "${dir##*[!/]}": Remove all non-forward-slashes
    # from the start of the string, leaving us with only
    # the trailing slashes.
    # "${dir%%"${}"}": Remove the result of the above
    # substitution (a string of forward slashes) from the
    # end of the original string.
    dir=${dir%%"${dir##*[!/]}"}

    # If the variable *does not* contain any forward slashes
    # set its value to '.'.
    [ "${dir##*/*}" ] && dir=.

    # Remove everything *after* the last forward-slash '/'.
    dir=${dir%/*}

    # Again, strip all trailing forward-slashes '/' from
    # the end of the string (see above).
    dir=${dir%%"${dir##*[!/]}"}

    # Print the resulting string and if it is empty,
    # print '/'.
    printf '%s\n' "${dir:-/}"
}

# --- Get the base-name of a file path
basename() {
    # Usage: basename "path" ["suffix"]

    # Strip all trailing forward-slashes '/' from
    # the end of the string.
    #
    # "${1##*[!/]}": Remove all non-forward-slashes
    # from the start of the string, leaving us with only
    # the trailing slashes.
    # "${1%%"${}"}:  Remove the result of the above
    # substitution (a string of forward slashes) from the
    # end of the original string.
    dir=${1%${1##*[!/]}}

    # Remove everything before the final forward-slash '/'.
    dir=${dir##*/}

    # If a suffix was passed to the function, remove it from
    # the end of the resulting string.
    dir=${dir%"$2"}

    # Print the resulting string and if it is empty,
    # print '/'.
    printf '%s\n' "${dir:-/}"
}

# --- Check if a number is a float
is_float() {
    # Usage: is_float "number"

    # The test checks to see that the input contains
    # a '.'. This filters out whole numbers.
    [ -z "${1##*.*}" ] &&
        printf %f "$1" >/dev/null 2>&1
}

# --- Check if a number is an integer
is_int() {
    # usage: is_int "number"
    printf %d "$1" >/dev/null 2>&1
}

lstrip "hello world" "hello "
rstrip "hello world" " world"
trim_string "    Hello,  World    "
trim_all "    Hello,    World    "
split "apples,oranges,pears" ","
split "1, 2, 3, 4, 5" ", "
trim_quotes "\"Hello\""
trim_quotes "'Hello'"
dirname "/user/bin/cat"; dirname "/user/bin/"; dirname "cat"; dirname "/"
basename "/user/bin/cat"; basename "/user/bin/cat" ".cat"; basename "/user/bin/"
printf 'one\ntwo\nthree\n' > /tmp/psb-327.txt
lines /tmp/psb-327.txt
head 2 /tmp/psb-327.txt
n=0; while IFS= read -r line || [ -n "$line" ]; do n=$((n+1)); done < /tmp/psb-327.txt
echo "read-loop=$n"
printf 'no-trailing-newline' > /tmp/psb-327b.txt
n=0; while IFS= read -r line || [ -n "$line" ]; do n=$((n+1)); done < /tmp/psb-327b.txt
echo "no-newline=$n"
x=old; read x < /dev/null; echo "eof-clears=[$x] rc=$?"
rm -f /tmp/psb-327.txt /tmp/psb-327b.txt
