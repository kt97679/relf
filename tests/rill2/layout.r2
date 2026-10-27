# else and elif (rill2: from the prototype's layout.mini) on the lines after their block's } (832): a lone else ran as a command - and both branches
x = 5
if x < 2 {
    print("small")
}
elif x < 9 {
    print("middle")
}
else {
    print("big")
}
if x > 9 { print("never") }

print("after")
