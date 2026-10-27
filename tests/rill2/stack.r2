# stack mode (837): a def of numbers runs on Forth's stack - tests/rill/run runs this with RILL2_STACK=0
# too, and the output is the same either way
def fib(n) {
    if n < 2 { return n }
    return fib(n - 1) + fib(n - 2)
}
def fact(k) {
    if k <= 1 { return 1 }
    return k * fact(k - 1)
}
def gcd(a, b) {
    if b == 0 { return a }
    return gcd(b, a % b)
}
def ack(m, n) {
    if m == 0 { return n + 1 }
    elif n == 0 { return ack(m - 1, 1) }
    return ack(m - 1, ack(m, n - 1))
}
def clamp(x, lo, hi) {
    if x < lo { return lo }
    if x > hi { return hi }
    return x
}
def sign(x) {
    if x > 0 and not (x == 0) { return 1 }
    elif x < 0 or x < -100 { return -1 }
    return 0
}
def sq_sum(a, b) { return a * a + b * b }
def plus_one(a, b) { return sq_sum(a, b) + 1 }   # a def of numbers calling another
def mix(n) { return n / 2 - -n % 3 }            # / and %, unary minus
print(fib(20), fact(10), gcd(84, 36), ack(2, 3))
print(clamp(15, 0, 10), clamp(-5, 0, 10), clamp(5, 0, 10))
print(sign(5), sign(-5), sign(0), plus_one(3, 4), mix(7), mix(-7))
print(fib(2.5), fact(3.0), clamp(1.5, 0, 1))      # not whole numbers: the def as any other's
print(fact(20))                                   # past 62 bits: boxed, and right
x = 10
def uses_global(n) { return n + x }               # reads the script's x: not a def of numbers
def truth(n) { return n > 3 }                     # gives a truth: not one either
print(uses_global(5), truth(5), truth(1))
