# a def as a stage takes no words or redirections (840)
def gen() { print(1) }
gen() > /tmp/x | sort
