# the same program in Rill and in Rill 2 (838): side.rill and side.r2 print side.expected, both
x = 7
y = x * 2 + 1
print(y)
name = "ada"
print("hello {name}, twice {x * 2}")
l = [3, 1, 2]
print(l[0], len(l), l[-1])
p = {name: "ada", born: 1815}
print(p["born"], "born" in p)
for i in range(3) { if i != 1 { print("i {i}") } }
def sq(n) { return n * n }
print(sq(9))
dir = "/tmp"
ls $dir > /dev/null
n = $(printf 'a\nb\n' | wc -l)
print("lines {n}")
false
if status != 0 { print("failed") }
print(-7 / 2, -7 % 2, 7 / 2)
c = 0
c += 1
print(c)
