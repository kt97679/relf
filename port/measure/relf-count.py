#!/usr/bin/env python3
"""port/measure/relf-count.py DIR - builds relf's counting engine into DIR: engine/cv8.c with every dispatch
counted per instruction address (tools/knee-model.py's patch), into a file named by $COUNTS, mapped shared
so forked children count too. DIR/relf-count runs an image (relf-count IMAGE ...), DIR/relfsh-count the
shell (kernel64-shell.img embedded). To count:  python3 -c "open('c.bin','wb').write(bytes(1 << 20))";
COUNTS=c.bin DIR/relfsh-count tests/bench-vm/realistic.sh; then cv8-prof.py kernel64-shell.img c.bin."""
import os, subprocess, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
d = sys.argv[1]; os.makedirs(d, exist_ok=True)
def patch(t, a, b):
    assert t.count(a) == 1, a
    return t.replace(a, b)
src = open(os.path.join(R, 'engine/cv8.c')).read()
src = patch(src, '#define PROF(k)\n#define PROFIP(a)\n#define PROFDUMP',
            '#include <sys/mman.h>\nstatic unsigned int *prof_map;\nstatic UNS64 prof_base;\n'
            '#define PROF(k)\n#define PROFIP(a) (prof_map[((a) - prof_base) & 0x3FFFF]++)\n#define PROFDUMP')
src = patch(src, '    NEXT();\ndo_call:',
            '    prof_base = cbase;\n    { int fd = open(getenv("COUNTS"), O_RDWR);\n'
            '      prof_map = mmap(0, 262144 * sizeof(unsigned int), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);\n'
            '      close(fd); }\n    NEXT();\ndo_call:')
open(os.path.join(d, 'relf-count.c'), 'w').write(src)
subprocess.run(['cc', '-O2', '-I', os.path.join(R, 'engine'), '-o', os.path.join(d, 'relf-count'), os.path.join(d, 'relf-count.c')], check=True)
subprocess.run(['sh', os.path.join(R, 'tools/embed.sh'), os.path.join(d, 'relf-count'), os.path.join(R, 'kernel64-shell.img'), os.path.join(d, 'relfsh-count')], check=True, cwd=R)
print(d + '/relf-count', d + '/relfsh-count')
