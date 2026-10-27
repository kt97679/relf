# the gaps closed at 839 (docs/RILL2.md, "Rill and Rill 2 side by side"): each feature once - tests/rill/run
# runs this with RILL2_STACK=0 too
on EXIT { print("on EXIT ran") }
name = "rill2"
def usage(n) {
    print("""
        usage: {n} [-v] FILE
          -v    say more
        """)
}
usage(name)
t = """
    a\tb "quoted" \{literal}
      deeper
    """
print(t)
print(len(t))
l = [3, 1.5, 2]
print(sum(l), max(l), min(l), abs(-4), abs(-2.5))
rows = [{n: "b", v: 2}, {n: "a", v: 9}, {n: "c", v: 5}]
for r in sort_by(rows, "v", "desc") { print(r["n"], r["v"]) }
print(len(sort_by(rows, "n")), sort_by(rows, "n")[0]["n"])
print(replace("a-b-c", "-", "+"), findall("a1b22c333", "[0-9]+"), get({x: 1}, "y", "none here"), get([5, 6], -1, 0))
setenv("RILL2_X", "set by setenv")
sh -c 'echo $RILL2_X'
print(range(10, 0, -3), pop([1, 2, 3]), len(glob("/etc/host*")) > 0)
l = [1, 2, 3, 4]
print([x * x for x in l])
print([x for x in l if x % 2 == 0])
print([w + "!" for w in ["a", "b"]], [k for k in {p: 1, q: 2}])
def evens(xs) { return [x for x in xs if x % 2 == 0] }
print(evens(range(7)))
x = "outer"
print([x for x in [1, 2]], x)
grid = [[r * 3 + c for c in range(3)] for r in range(2)]
print(grid)
print([
    n * 2
    for n in l
    if n > 2
])
print(["for" for i in [1]], [1, 2])
for i, x in ["a", "b"] { print(i, x) }
for k, v in {p: 1, q: [2]} { print(k, v) }
for j in range(10, 0, -4) { print("step", j) }
def kind(f) {
    case f {
        "*.txt" "*.md" { return "text" }
        "*.r2" { return "rill2" }
        "*" { return "other" }
    }
}
print(kind("a.md"), kind("x.r2"), kind("bin"))
here = $(pwd)
cd /tmp {
    pwd
}
print($(pwd) == here)                  # back where it was - wherever the tests run
print(index("hello", "ll"), index([1, 2, 3], 3), index("abc", "z"))
l = ["a b", "c"]
printf '[%s]' @l
echo
n = 5
echo "n is {n + 1}" and $n{n * 2} 'not {n}'
sh -c "echo err >&2" 2>&1 | tr a-z A-Z
sh -c "echo out" >&2 2> /dev/null
echo both &> /tmp/rill2-gaps-both.txt
cat /tmp/rill2-gaps-both.txt
false ?? print("false failed, status {status}")
true ?? print("not printed")
printf '%s|' @args
echo
