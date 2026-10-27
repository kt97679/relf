#!/usr/bin/env rill2
# tests/rill2/tour.r2 - every part of Rill 2 (docs/RILL2.md); tests/rill/run checks its output

# --- values
n = 7                                  # whole numbers
d = 2.5                                # decimals
s = "tab\tquote\" brace\{"             # strings: \n \t \" \\ \{
r = 'raw: no \t, no {n}'               # single quotes: as written
print(n, d, s)
print(r)
print("n is {n}, twice {n * 2}")       # {expr} in a string
print(true, false, none)
l = [1, 2, 3]                          # lists
p = {name: "ada", "born": 1815}        # records: keys a name or a string
print(l, p["name"], p["born"])

# --- expressions
print(n + 2 * 3, (n + 2) * 3, n / 2, n % 2, -n)
print(d * 2, n + d)                    # decimals and numbers mix
print("ab" + "cd", n > 5 and not (n == 9), n < 5 or n == 7)
print(l[0], l[-1], l[1:], l[:-1])      # index from 0, or from the end; slices
print("hello"[1], "hello"[1:4])
total = (1 +
         2 +
         3)                            # inside brackets, a line goes on
also = 10 -
    4                                  # and after an operator
print(total, also)

# --- assignment
n += 1
n *= 2
l[0] = 10
p["born"] += 1
grid = [[0, 0], [0, 0]]
grid[1][0] = 5
print(n, l, p["born"], grid)

# --- control
if n > 100 { print("big") } elif n > 10 { print("medium") } else { print("small") }
if n > 100 {
    print("big")
}
else {
    print("not big")
}
i = 0
while true {
    i += 1
    if i == 2 { continue }
    if i > 4 { break }
    print("while", i)
}
for x in [1, 2, 3, 4, 5] {
    if x % 2 == 0 { continue }
    if x > 4 { break }
    print("odd", x)
}
for k in p { print("key", k) }        # a record's keys
for j in range(2, 5) { print("range", j) }

# --- defs
def fib(k) {
    if k < 2 { return k }
    return fib(k - 1) + fib(k - 2)
}
print(fib(20))
print(later(3))                        # a def called before it is defined
def later(x) { return x * 100 }
def first_big(xs, limit) {
    for x in xs {
        if x > limit { return x }      # return from inside a loop
    }
}
print(first_big([1, 5, 9], 4), first_big([1, 2], 4))
x = "global"
def g() { return x }
def f(x) { return g() }                # a def's names are its own
print(f("param"))
def count() {
    c = 0
    for i in range(3) { c += 1 }
    return c
}
print(count(), i)                      # i here is the script's

# --- library
print(str(42) + "!", int("12") + 1, int(3.9), decimal("1.25") + 1)
print(len("hello"), len(l), len(p), keys(p), has(p, "name"))
w = []
append(w, "b")
append(w, "a")
print(sort(w), join(w, "-"), split("a,b,,c", ","), words("  x  y "))
print(trim("  pad  "), starts("hello", "he"), ends("hello", "lo"), contains("hello", "ell"))
print(match("key=val", "(\\w+)=(\\w+)"), sub("a1b22", "[0-9]+", "#"))
print(json({a: [1, 2.5, "x"]}), from_json("[1, 2]")[1])
write("/tmp/rill2-tour.txt", "one\ntwo\n")
print(lines(read("/tmp/rill2-tour.txt")))
print(env("RILL2_TOUR"), args())

# --- the shell
echo plain words, and $n           # a line that is no assignment, call or name: a command
printf '%s|%s\n' 'single quotes' "double quotes"
printf "b\na\n" | sort | head -1 > /tmp/rill2-tour.out   # | > >> < 2>
echo appended >> /tmp/rill2-tour.out
cat < /tmp/rill2-tour.out
sh -c "exit 4" 2> /dev/null
print(status)                      # the last command's status
word = $(echo shout | tr a-z A-Z)  # $( ): a command's output
print(word, status)
sleep 0 &                          # & : to the background, its job in job
print(wait(job))
ls = "a variable"
!ls /tmp > /dev/null               # !: a command, though ls names a variable
print(status)
cd /tmp
pwd
