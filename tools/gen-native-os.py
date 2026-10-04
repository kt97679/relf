#!/usr/bin/env python3
"""gen-native-os.py - the assembly engine's primitive handlers as native routines.

docs/NATIVE.md section 10; Iteration 634, closures since 635. engine/
relfasm64.4 implements kernel.4's operating-system primitives as raw system
calls in asm64, the assembler the native back end uses, with conventions
the native ones renamed: top of stack r12 (native rbx), data stack pointer
r13, at the second item (native rbp), NEXT, where a native routine returns.
So the native routines are not written again: this writes each wanted
handler as an NCODE routine - one source for both engines, as kernel.4 is
for both kernels.

A handler comes with its CLOSURE: the engine's subroutines it calls
(alloc_block, env_find - and theirs), as labelled code, and the constants
it names, with their defining expressions (and theirs). The engine's data
is one chain rooted at BSS_BASE; here BSS_BASE is N-RTDATA, the native
runtime's region below the data stack, so every handler finds its data at
the same layout. engine-macros.4's colon words that are plain stack work go
across too. A primitive is bound to its handler by name (GETPID L_getpid),
the label required to be in engine/relfasm-ops.4's dispatch table.

A handler is refused, with the reason, if anything in its closure names the
asm engine's r14 (its ip), r15 (its return stack), rbx (its image base) or
rbp, a macro that drives the VM, or a constant of the engine's own memory
layout (TEXTORG and what hangs from it, but the chain re-rooted).
usage: tools/gen-native-os.py OUT.4 [--report]    (from the repository's top)
"""
import re, sys

ENGINE = 'engine/relfasm64.4'
MACROS = 'engine/engine-macros.4'
TABLE = 'engine/relfasm-ops.4'
# the stubs the shell names (Iteration 633's inventory) - the ones worth porting
WANTED = """FILE-SIZE FORK EXECVE WAITPID PIPE DUP2 GETENV SETENV CHDIR GETCWD SYS-ARGC
SYS-ARG GETPID UNSETENV ALLOCATE FREE RESIZE GETPWHOME ISATTY OPEN-DIR READ-DIR
CLOSE-DIR ACCESS KILL UMASK CPU-TIMES SIGNAL-ACTION SIGNALS-PENDING TERM-RAW
TERM-RESTORE FILE-KIND GETRLIMIT SETRLIMIT WAIT-NOHANG GETPPID ENV-AT SETPGID
TCSETPGRP WAIT-JOB FILE-MODE LOCAL-TIME DUP-FROM TRAP-XT!
OPEN-FILE CLOSE-FILE REPOSITION-FILE FILE-POSITION READ WRITE POLL TYPE
SYS-EXIT BYE
TCP-LISTEN TCP-ACCEPT TCP-CONNECT SYSTEM DELETE-FILE GETFSIZE SETFSIZE RAW-MODE
TCGETPGRP CHMOD""".split()
# The third row (640): the rest the engine implements - the examples' TCP
# servers among them (tests/shell/run-examples) - so no primitive the asm
# engine has is a stub natively.
FORCED = ['set_argv0']   # the start's, not a handler's: RELF_ARGV0, $0 (640)
# The second row (638): what forth/native-rt.4 hand-wrote in N1b, before
# this existed - its OPEN-FILE's mode table did not create a file for <>,
# and $0 read past its NUL. The engine's are the shell's tested semantics;
# these, laid after native-rt.4's, shadow them in the kernel's build.
# MOVE FILL COMPARE stay native-rt.4's: pure, CORE-checked, COMPARE faster;
# and since 644 CSTRLEN and SCAN, made faster there, with tests/native/
# kernel-str.4 against CV8 (the profile put them at 6-14 % of the shell).
FORBIDDEN = re.compile(r'\b(r14\w*|r15\w*|rbx|ebx|bx|bl|EXITNEXT,|RPUSH,|SLOT,|dispatch\w*)\b')
# rbp is the engine's scratch - its VM is r12-r15 and rbx - and natively
# the data stack: it becomes r12, free natively (r12 and r13 are what the
# renaming moves into rbx and rbp). TCP-LISTEN keeps a socket in it (640).
REGMAP = {'r12': 'rbx', 'r12d': 'ebx', 'r13': 'rbp', 'rbp': 'r12', 'ebp': 'r12d'}
ALIASES = {'SIGNAL-ACTION': 'L_sigaction', 'SIGNALS-PENDING': 'L_sigpending',   # named
           'REPOSITION-FILE': 'L_reposfile', 'FILE-POSITION': 'L_filepos',       # otherwise
           'DELETE-FILE': 'L_delfile'}
NATIVE = {'int_throw'}                  # supplied by forth/native-sig.4 (636)
NORETURN = {'sig_restorer'}             # rt_sigreturn: no fall into the next label
SIGFILE = 'forth/native-sig.4'
ROOT = 'BSS_BASE'                       # the data chain's root: re-rooted
LAYOUT = {'TEXTORG', 'VM_OFF', 'VM_BASE', 'MEM_SIZE', 'MEMSIZE'}   # the engine's own memory

def strip_comments(s):
    s = re.sub(r'(^|\s)\\\s.*$', '', s)
    s = re.sub(r'(^|\s)\(\s[^)]*\)', ' ', s)
    return s

def rename(l):            # all at once: r13 becomes rbp, and rbp r12, in one pass
    return re.sub(r'\b(r12d|r12|r13|rbp|ebp)\b', lambda m: REGMAP[m.group(1)], l)

def read_engine():
    text = open(ENGINE, encoding='utf-8', errors='replace').read()
    consts = []                         # (name, expression), in file order
    for line in text.split('\n'):
        m = re.match(r'^(.*\S)\s+CONSTANT\s+(\S+)', strip_comments(line))
        if m and 'HERE-A' in m.group(1):
            continue                     # measured where it stands: kept in its label's body
        if m and not m.group(1).strip().startswith(':'):
            consts.append((m.group(2), m.group(1).strip()))
    labels = {}                         # top-level label -> its lines, to the next one
    order = []
    cur = None
    for line in text.split('\n'):
        m = re.match(r'^([A-Za-z_][\w-]*) L:(.*)$', line)
        if m:
            cur = m.group(1); labels[cur] = [m.group(2)]; order.append(cur); continue
        c = strip_comments(line)
        if cur is not None and (not re.match(r'^\s*\S.*\s+CONSTANT\s+\S+', c) or 'HERE-A' in c):
            labels[cur].append(line)     # a CONSTANT line is the constants' (open_modes's
    nxt = {a: b for a, b in zip(order, order[1:])}   # NOPENMODES made it look like code, 638)
    data = set()
    for k, ls in labels.items():
        # code ends at its last NEXT, ret or jmp - a handler may end in a jump
        # to a shared tail (FILE-SIZE to ud_ior), a tail in NEXT, (635)
        ends = [i for i, l in enumerate(ls) if re.search(r'(NEXT,|ret,|jmp,)', strip_comments(l))]
        if ends:
            labels[k] = ls[:ends[-1] + 1]
        elif all(re.fullmatch(r'-?\d+|[CWLQ]?,A|S,', t) for t in
                 ' '.join(strip_comments(l) for l in ls if 'CONSTANT' not in l).split()) \
                and ' '.join(ls).strip():
            labels[k] = [l for l in ls if strip_comments(l).strip()]     # data: m_passwd's bytes
            data.add(k)
        elif k in NORETURN:
            labels[k] = [l for l in ls if strip_comments(l).strip()]
        elif ' '.join(strip_comments(l) for l in ls).strip() and k in nxt:
            # it falls into the label after it (FILE-SIZE into ud_ior): the
            # fall made a jump, as code can be laid anywhere here (635)
            labels[k] = ls + ['%s jmp,' % nxt[k]]
        else:
            labels[k] = []
    return consts, labels, data

def portable_macros():
    out, cur = [], None
    for line in open(MACROS, encoding='utf-8', errors='replace'):
        if line.startswith(': '):
            cur = [line.rstrip('\n')]
        elif cur is not None:
            cur.append(line.rstrip('\n'))
        if cur is not None and re.search(r';\s*$', strip_comments(line).rstrip()):
            text = ' '.join(strip_comments(l) for l in cur)
            if not FORBIDDEN.search(text) and 'NEXT,' not in text:
                out.append('\n'.join(rename(strip_comments(l)).rstrip() for l in cur))
            cur = None
    return out

def addresses(line, labels):
    """A label used as an ADDRESS - inside [ ], or as an immediate before # -
    is asm64's label value: an offset where ORG is 0, as in the native image,
    an address only where ORG is the load address. So it becomes the address
    at run time, `label ORG @ - N-START @ +`, right whatever ORG is (616's
    OPEN-FILE fix; GETPWHOME's lea of m_passwd, 635). Calls and jumps are
    relative and keep the bare label."""
    def fix(tok):
        return '%s ORG @ - N-START @ +' % tok if tok in labels and not tok.isdigit() else tok
    line = re.sub(r'\[([^\]]*)\]', lambda m: '[ ' + ' '.join(fix(t) for t in m.group(1).split()) + ' ]', line)
    return re.sub(r'(\S+)(\s+#\s)', lambda m: fix(m.group(1)) + m.group(2), line)

def main():
    out_path = sys.argv[1]
    consts, labels, data = read_engine()
    cdef = dict(consts)
    table = set(re.findall(r'(L_\w+) 0 Q,\+', open(TABLE).read()))
    norm = {}
    for l in labels:
        if l.startswith('L_'):
            norm.setdefault(l[2:].replace('_', '').lower(), l)

    def const_closure(names, seen):
        """the constants named, and those their expressions name; None if
        the closure reaches the engine's own memory layout"""
        for n in names:
            if n in seen or n not in cdef:
                continue
            if n in LAYOUT:
                return None
            seen.add(n)
            if n == ROOT:
                continue                 # re-rooted: what it hung from is cut
            if const_closure(cdef[n].split(), seen) is None:
                return None
        return seen

    def closure(label, code_seen, const_seen):
        """why it is refused, or None; fills code_seen and const_seen"""
        if label in code_seen or label in NATIVE:
            return None
        body = labels.get(label)
        if not body:
            return 'no code for %s' % label
        code_seen.add(label)
        text = ' '.join(strip_comments(l) for l in body)
        if label in data:
            return None
        # rbx is the asm engine's image base; a subroutine that saves and
        # restores it uses it as scratch, and the native top of stack survives
        # (env_find, 635); a handler may not touch it at all
        check = text
        if not label.startswith('L_') and 'rbx push,' in text and 'rbx pop,' in text:
            check = re.sub(r'\b(rbx|ebx)\b', 'scratch-ok', text)
        bad = FORBIDDEN.search(check)
        if bad:
            return '%s names %s' % (label, bad.group(1))
        for tok in text.split():
            if tok in labels and tok != label and not tok.isdigit():
                why = closure(tok, code_seen, const_seen)
                if why:
                    return why
        if const_closure([t for t in text.split() if t in cdef], const_seen) is None:
            return '%s reaches the engine\'s own memory layout' % label
        return None

    ported, refused, all_code, all_consts = [], [], set(), set()
    for name in WANTED:
        label = ALIASES.get(name) or norm.get(re.sub(r'[^a-z0-9]', '', name.lower()))
        if not label or label not in table:
            refused.append((name, 'no handler in the dispatch table')); continue
        cs, ks = set(), set()
        why = closure(label, cs, ks)
        if why:
            refused.append((name, why)); continue
        ported.append((name, label)); all_code |= cs; all_consts |= ks
    for name, label in (('GETPID', 'L_getpid'), ('FORK', 'L_fork'), ('DUP2', 'L_dup2')):
        assert (name, label) in ported, 'binding by name failed at %s' % name

    for f in FORCED:                     # the start's subroutines, with their closures
        cs = set()
        why = closure(f, cs, all_consts)
        assert not why, 'the start needs %s: %s' % (f, why)
        all_code |= cs
    # the chain's cells the native start fills, as the asm engine's start does
    # (native-kernel.4): emitted whether a routine names them or not (635)
    const_closure(['argc_v', 'argv_v', 'envp_v', 'argbase', 't_raw_fd', 'img_limit'], all_consts)
    # and the save stack's, for forth/native-locals.4 (637)
    const_closure(['lsave_sp', 'lsave_stack', 'LSAVE_MAX'], all_consts)
    # a handler is reached by jumps too - a fall into L_read (638): every
    # ported one gets its label at its routine's start, and one reached but
    # not wanted is laid as a subroutine
    handler_of = {label: name for name, label in ported}
    subs = [l for l in labels if l in all_code and l not in handler_of]
    with open(out_path, 'w') as f:
        f.write('\\ native-os.4 - GENERATED by tools/gen-native-os.py from engine/relfasm64.4;\n')
        f.write('\\ do not edit. The asm engine\'s handlers as native routines (NATIVE.md 10):\n')
        f.write('\\ r12 -> rbx, r13 -> rbp, NEXT, -> ret; its data chain rooted at N-RTDATA.\n')
        f.write('8 CONSTANT CELL\n')
        for n, e in consts:              # in the engine's order: each after what it names
            if n in all_consts:
                f.write('%s CONSTANT %s\n' % ('N-RTDATA' if n == ROOT else e, n))
        for m in portable_macros():
            f.write(m + '\n')
        for s in subs + [label for _, label in ported]:
            f.write('LABEL %s\n' % s)
        if 'free_block' in subs:
            f.write('LABEL alloc_end\n')
        for s in subs:                   # the subroutines: labelled code; a shared
            f.write('N-MARK %s\n%s L:\n' % (s, s))   # its NEXT, returns; N-MARK: the map (643)
            for l in labels[s]:
                l = addresses(rename(strip_comments(l)).replace('NEXT,', '195 C,A'), labels).strip()
                if l:
                    f.write('  ' + l + '\n')
            if s == 'free_block':        # the allocator's end, and the native signal code
                f.write('alloc_end L:\n')
                f.write(open(SIGFILE).read())
        for name, label in ported:
            f.write('NCODE %s   \\ %s\n' % (name, label))
            f.write('%s L:\n' % label)
            for l in labels[label]:
                l = addresses(rename(strip_comments(l)).replace('NEXT,', '195 C,A'), labels).strip()
                if l:
                    f.write('  ' + l + '\n')
            f.write('NEND\n')
    if '--report' in sys.argv:
        print('ported %d: %s' % (len(ported), ' '.join(n for n, _ in ported)))
        print('with %d of the engine\'s subroutines: %s' % (len(subs), ' '.join(subs)))
        print('need a native design %d:' % len(refused))
        for n, why in refused:
            print('  %-16s %s' % (n, why))

if __name__ == '__main__':
    main()
