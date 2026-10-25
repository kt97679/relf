# tests/rill/glob.rill in Python: its expected output
import sys; sys.path = sys.path[1:]   # this file is glob.py: the library's glob, not itself
import glob, os, tempfile, shutil
tmp = tempfile.mkdtemp(); here = os.getcwd(); os.chdir(tmp)
os.makedirs('docs'); os.makedirs('sub')
for f in ['a.txt', 'b.txt', 'c.md', '.hidden.txt', 'docs/one.md', 'docs/two.md', 'docs/three.txt', 'sub/x1', 'sub/x22']: open(f, 'w').close()
for p in ["*.txt", "*", "docs/*.md", "docs/t*", "sub/x?", "[ab]*", ".*", "nomatch*", "a.txt", "missing.txt", "docs/*.none"]:
    print('%s: %s' % (p, ' '.join(sorted(glob.glob(p)))))
os.chdir(here)
print('%d under an absolute path' % len(glob.glob(tmp + '/*.txt')))
shutil.rmtree(tmp)
