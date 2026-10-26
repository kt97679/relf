def note(x):
    if x == "": return
    print("note: %s" % x)
note(""); note("one")
def first_big(l):
    for x in l:
        if x > 10:
            print("big: %s" % x); return
    print("none big")
first_big([1, 20, 30]); first_big([1, 2])
def evens_to_six(l):
    for i, x in enumerate(l):
        if x % 2 == 1: continue
        if x > 6: return
        print("even %d: %d" % (i, x))
    print("all even ones")
evens_to_six([1, 2, 3, 4, 8, 10]); evens_to_six([2, 4])
def until_zero(l):
    i = 0
    while i < len(l):
        if l[i] == 0: break
        if l[i] < 0: return
        i = i + 1
    print("stopped at %d" % i)
until_zero([3, 0, 5]); until_zero([3, -1, 5])
total = 0
for k in range(3000): total = total + k + 2 + 3
print("total %d" % total)
print("40000 calls, past the data stack's 32768 cells")
for j in range(2): note("round %d" % j)
print("done")
