#!/usr/bin/env python3
"""gen-native-os.py - the assembly engine's primitive handlers as native routines.

docs/NATIVE.md section 10, Iteration 634. engine/relfasm64.4 implements
kernel.4's operating-system primitives as raw system calls in asm64, the
assembler the native back end uses, with conventions the native ones
renamed: top of stack r12 (native rbx), data stack pointer r13, at the
second item (native rbp), NEXT, where a native routine returns. So the
native routines are not written again: this takes each handler's text and
writes an NCODE routine of it - one source for both engines, as kernel.4
is for both kernels.

A primitive is bound to its handler by name - GETPID to L_getpid, FILE-SIZE
to L_filesize - and the label must be in engine/relfasm-ops.4's dispatch
table, so it is a handler the engine runs.

A handler is taken only if it keeps to its arguments, its system calls
and `scratch`: one that names the asm engine's r14 (its ip), r15 (its
return stack), rbx (its image base) or rbp, a macro of the VM (EXITNEXT,
RPUSH, SLOT, FLAG,), or any engine label but the SYS_ numbers, CELL and
scratch, needs a native design (NATIVE.md 10) and is listed as such.
usage: tools/gen-native-os.py OUT.4 [--report]    (from the repository's top)
"""
import re, sys

ENGINE = 'engine/relfasm64.4'
TABLE = 'engine/relfasm-ops.4'
KERNEL = 'forth/kernel.4'
# the stubs the shell names (Iteration 633's inventory) - the ones worth porting
WANTED = """FILE-SIZE FORK EXECVE WAITPID PIPE DUP2 GETENV SETENV CHDIR GETCWD SYS-ARGC
SYS-ARG GETPID UNSETENV ALLOCATE FREE RESIZE GETPWHOME ISATTY OPEN-DIR READ-DIR
CLOSE-DIR ACCESS KILL UMASK CPU-TIMES SIGNAL-ACTION SIGNALS-PENDING TERM-RAW
TERM-RESTORE FILE-KIND GETRLIMIT SETRLIMIT WAIT-NOHANG GETPPID ENV-AT SETPGID
TCSETPGRP WAIT-JOB FILE-MODE LOCAL-TIME DUP-FROM TRAP-XT!""".split()
FORBIDDEN = re.compile(r'\b(r14\w*|r15\w*|rbx|ebx|rbp|ebp|bx|bl|EXITNEXT,|RPUSH,|SLOT,|dispatch\w*)\b')
MACROS = 'engine/engine-macros.4'

def rename(l):
    l = re.sub(r'\br12d\b', 'ebx', l); l = re.sub(r'\br12\b', 'rbx', l)
    return re.sub(r'\br13\b', 'rbp', l)

def portable_macros():
    """engine-macros.4's colon words that are plain stack work - not the four
    that drive the VM (NEXT, EXITNEXT, RPUSH, SLOT, - its ip, return stack,
    table) - renamed as the handlers are: one source for them too (634)."""
    out, cur = [], None
    for line in open(MACROS, encoding='utf-8', errors='replace'):
        if line.startswith(': '):
            cur = [line.rstrip('\n')]
        elif cur is not None:
            cur.append(line.rstrip('\n'))
        if cur is not None and re.search(r';\s*(\\.*)?$', strip_comments(line)):
            text = ' '.join(strip_comments(l) for l in cur)
            if not FORBIDDEN.search(text) and 'NEXT,' not in text:
                out.append('\n'.join(rename(strip_comments(l)).rstrip() for l in cur))
            cur = None
    return out

def primitives_in_order():
    names = []
    for line in open(KERNEL, encoding='utf-8', errors='replace'):
        m = re.match(r'^PRIMITIVE\s+(\S+)', line)
        if m:
            names.append(m.group(1))
    return names

def table_in_order():
    return re.findall(r'(L_\w+) 0 Q,\+', open(TABLE).read())

def handlers():
    """{label: [lines]} - each handler from its `L_x L:` up to its last NEXT,
    before the next label: what follows that is shared code or data. A
    handler cut short leaves a local label undefined, and asm64's END-ASM
    refuses the build."""
    out, cur = {}, None
    for line in open(ENGINE, encoding='utf-8', errors='replace'):
        m = re.match(r'^(L_\w+) L:(.*)$', line.rstrip('\n'))
        if m:
            cur = m.group(1); out[cur] = [m.group(2)]; continue
        if cur is not None:
            out[cur].append(line.rstrip('\n'))
    for k, ls in out.items():
        ends = [i for i, l in enumerate(ls) if 'NEXT,' in strip_comments(l)]
        out[k] = ls[:ends[-1] + 1] if ends else []
    return out

def strip_comments(s):
    s = re.sub(r'(^|\s)\\\s.*$', '', s)
    s = re.sub(r'(^|\s)\(\s[^)]*\)', ' ', s)
    return s

def engine_constants(names):
    """The engine's CONSTANT lines a set of handlers needs, other than scratch."""
    out = []
    for line in open(ENGINE, encoding='utf-8', errors='replace'):
        m = re.match(r'^\s*(\S+)\s+CONSTANT\s+(\S+)', line)
        if m and m.group(2) in names and m.group(2) not in ('scratch', 'CELL') and re.fullmatch(r'-?\d+', m.group(1)):
            out.append('%s CONSTANT %s' % (m.group(1), m.group(2)))
    return out

def main():
    out_path = sys.argv[1]
    # By name, as the handlers are named: GETPID L_getpid, FILE-SIZE L_filesize.
    # (Position does not do it: OPCODE lines take numbers of their own and
    # the table fills gaps with L_badop - the first version bound GETPID
    # to L_badop, and this check stopped it.) The label must be one the
    # engine's dispatch table holds: a handler the engine really runs.
    hs = handlers()
    table = set(table_in_order())
    norm = {}
    for l in hs:
        norm.setdefault(l[2:].replace('_', '').lower(), l)
    bind = {}
    for name in WANTED:
        l = norm.get(re.sub(r'[^a-z0-9]', '', name.lower()))
        if l and l in table:
            bind[name] = l
    for name, label in (('GETPID', 'L_getpid'), ('FORK', 'L_fork'), ('DUP2', 'L_dup2')):
        assert bind.get(name) == label, 'binding by name failed at %s: %s' % (name, bind.get(name))
    etext = open(ENGINE).read()
    engine_words = set(re.findall(r'\bCONSTANT\s+(\S+)', etext))
    engine_labels = set(re.findall(r'\bLABEL\s+(\S+)', etext)) | set(re.findall(r'^(\S+) L:', etext, re.M))
    engine_labels = {l for l in engine_labels if not l.isdigit()}
    ported, refused, used_consts = [], [], set()
    for name in WANTED:
        label = bind.get(name)
        body = hs.get(label)
        if not body:
            refused.append((name, 'no handler %s' % label)); continue
        code = [strip_comments(l) for l in body]
        text = ' '.join(code)
        bad = FORBIDDEN.search(text)
        # any label of the engine's - a handler's, or one of its own
        # subroutines (alloc_block, env_find): the first version knew only
        # the L_ handlers, and reported ALLOCATE and GETENV ported
        other = [w for w in text.split() if w in engine_labels and w != label]
        if bad:
            refused.append((name, 'names %s' % bad.group(1))); continue
        if other:
            refused.append((name, 'calls the engine\'s %s' % other[0])); continue
        consts = {w for w in text.split() if w in engine_words}
        unknown_data = [w for w in consts if not w.startswith('SYS_') and w not in ('CELL', 'scratch')]
        if unknown_data:
            refused.append((name, 'uses engine data %s' % unknown_data[0])); continue
        used_consts |= consts
        native = []
        for l in code:
            l = rename(l).replace('NEXT,', '195 C,A')
            if l.strip():
                native.append('  ' + l.strip())
        ported.append((name, label, native))
    with open(out_path, 'w') as f:
        f.write('\\ native-os.4 - GENERATED by tools/gen-native-os.py from engine/relfasm64.4;\n')
        f.write('\\ do not edit. The asm engine\'s handlers as native routines (NATIVE.md 10):\n')
        f.write('\\ r12 -> rbx, r13 -> rbp, NEXT, -> ret. Included after native-rt.4.\n')
        f.write('8 CONSTANT CELL\n')
        f.write('N-RTDATA CONSTANT scratch     \\ 256 bytes, in the runtime page below the data stack\n')
        for c in engine_constants(used_consts):
            f.write(c + '\n')
        for m in portable_macros():
            f.write(m + '\n')
        for name, label, native in ported:
            f.write('NCODE %s   \\ %s\n' % (name, label))
            f.write('\n'.join(native) + '\n')
            f.write('NEND\n')
    if '--report' in sys.argv:
        print('ported %d: %s' % (len(ported), ' '.join(n for n, _, _ in ported)))
        print('need a native design %d:' % len(refused))
        for n, why in refused:
            print('  %-16s %s' % (n, why))

if __name__ == '__main__':
    main()
