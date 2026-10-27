# strings: an expression's own "..." inside { } - the rest of the string was lost, silently, till 842
s = {file: "a", lines: 3}
print("{s["file"]}")
print("x {s["lines"]} y")
print("{s["file"]} has {s["lines"]}")
print("<{s["file"] + "{s["lines"] * 2}!"}>, done")
print(len("{s["file"]}xyz"), "tail")
print("{s['file']} has {s['lines']}")
