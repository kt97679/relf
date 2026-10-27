# an index past the end, inside a def: its line
def third(l) {
    return l[2]
}
print(third([1, 2, 3]))
print(third([1]))
