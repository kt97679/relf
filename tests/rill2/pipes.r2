# a def as a pipeline stage, and $(a ?? b) (840): Rill's last gaps in Rill 2
def gen() {
    print("b")
    print("a")
}
def shout() {
    for l in lines(read("/dev/stdin")) { print(l + "!") }
}
gen() | sort
gen() | sort | shout()
echo c | shout()
print(status)
x = $(sh -c "echo first; exit 1" ?? echo second)
print(x, status)
y = $(echo fine ?? echo not-run)
print(y)
z = $(gen() | sort)
print(z)
