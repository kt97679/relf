# tests/rill/order.rill in Python: its expected output
words = ["apple", "Apple", "banana", "app", "", "été", "zebra", "10", "9"]
for a in ["apple", "app", "été", "9"]:
    print(a, ' '.join(w for w in words if a < w), len([w for w in words if a >= w]))
x = words[1]
if x > "A": print("an item and a text")
b = lambda v: 'true' if v else 'false'
print(b("b" > "a"), b("a" <= "a"), b("Z" < "a"))
