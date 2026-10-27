# strict(true): a failed command stops the script with its status, unless ?? handles it (839)
strict(true)
false ?? print("handled")
sh -c "exit 3"
print("not reached")
