#!/usr/bin/env python3
"""tools/difffuzz.py [--seconds N] [--out DIR] [--seed S] - look for DIFFERENCES.

Where tools/crashfuzz.py mutates existing scripts and looks only for
crashes and hangs, this GENERATES well-formed scripts from a small
grammar of the constructs this shell's bugs have lived in - parameter
expansions, quoting, field splitting, patterns, here-documents,
redirections, loops, functions, traps - and compares this shell with
dash: standard output and exit status. Standard error is not compared,
since the two word their messages differently; nor are the behaviours
GOALS.md records as deliberate divergences, which the grammar avoids.

Every value a script prints goes through printf '[%s]', so a field
boundary is visible and a splitting difference cannot hide. Each finding
is shrunk by deleting lines while the difference persists, and written
to --out with both outputs. Written at Iteration 471: the bugs of 444 to
470 were each found by hand, one test at a time, and nearly all of them
are shapes a generator reaches in seconds.
"""
import os, random, subprocess, sys, tempfile, time, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RELFSH = os.path.join(ROOT, 'relfsh')
DASH = shutil.which('dash')

VALUES = ['', 'a', 'a b', ' lead', 'trail ', 'a  b', '*', 'x*', '[ab]', 'a:b:c', '1', '10', '-n',
          'x\ty', 'a,b', '$x', "it's", 'q"q', '~', 'a/b/c', '.', '..', '?']
PATTERNS = ['*', '?', 'a*', '*b', '[ab]*', '[!a]*', '*[0-9]', '"*"', "'a'*", 'a\\*', '[[:alpha:]]*', '']
IFSES = [None, '', ':', ' :', ',', 'a', ' \t\n', ':,']

def word(r, depth=0):
    """a word that expands to something - as arguments, most of it quoted or not"""
    v = r.choice(['x', 'y', 'z'])
    forms = ['$' + v, '"$' + v + '"', '${' + v + '-dflt}', '"${' + v + ':-d f}"', '${' + v + ':+set}',
             '${#' + v + '}', '${' + v + '#' + r.choice(PATTERNS) + '}', '"${' + v + '%%' + r.choice(PATTERNS) + '}"',
             '$(( ' + str(r.randint(0, 9)) + ' ' + r.choice(['+', '-', '*', '%', '<<', '&', '|', '^']) + ' ' + str(r.randint(1, 9)) + ' ))',
             '"$@"', '$@', '"$*"', '$*', '$#', 'lit', "'s q'", '"d q"', 'a\\ b', '*.none']
    if depth < 2 and r.random() < 0.25:
        forms.append('"$(printf %s ' + word(r, depth + 1) + ')"')
        forms.append('$(printf "%s " ' + word(r, depth + 1) + ')')
    return r.choice(forms)

def quote(v):
    return "'" + v.replace("'", "'\\''") + "'"

def more(r, k, depth):
    """the constructs added once the first grammar ran clean (Iteration 472)"""
    v = r.choice(['x', 'y', 'z'])
    if k == 16:
        op = r.choice(['n=n+1', 'n+=2', 'n*=3', 'n<<=1', 'n?1:2', '(n+1)*2', 'n==0', 'n>1&&1', '-n', '!n', 'n%3', 'n-=1'])
        return 'n=' + str(r.randint(0, 5)) + "; printf '[%s]' $((" + op + ")) \"$n\"; echo"
    if k == 17:
        return "printf '[%s]' \"${" + v + r.choice(['%', '%%', '#', '##']) + r.choice(PATTERNS) + "}\" ${" + v + r.choice(['%', '##']) + r.choice(PATTERNS) + "}; echo"
    if k == 18:
        return "eval \"printf '[%s]' \\\"\\$" + v + "\\\" \\$" + v + "\"; echo"
    if k == 19:
        return "printf '[%s]' `printf '%s ' $" + v + "` \"`printf %s \\\"$" + v + "\\\"`\"; echo"
    if k == 20:
        return ('touch "$T/g1" "$T/g2" "$T/h1"; ' + r.choice(['set -f; ', 'set +f; ', '']) +
                "printf '[%s]' " + r.choice(['./g*', './?1', './[gh]1', './[!g]*', './none*', '"./g*"']) + '; echo; set +f')
    if k == 21:
        return ("while read -r a b; do printf '<%s|%s>' \"$a\" \"$b\"; done <<'EOF'\n" +
                '\n'.join(r.choice(VALUES + ['a b c', '  indent', 'x\\y']) for _ in range(r.randint(1, 3))) + '\nEOF\necho')
    if k == 22:
        return 'set -- ' + ' '.join(quote(r.choice(VALUES)) for _ in range(r.randint(1, 4))) + '; shift ' + str(r.randint(0, 2)) + "; printf '[%s]' $# \"$@\"; echo"
    if k == 23:
        a, b = word(r), word(r)
        opx = r.choice(['=', '!=', '-z', '-n', '-eq', '-lt', '-gt'])
        if opx in ('-z', '-n'):
            return 'test ' + opx + ' ' + a + ' && echo T || echo F'
        if opx in ('-eq', '-lt', '-gt'):
            return 'test ' + str(r.randint(0, 3)) + ' ' + opx + ' ' + str(r.randint(0, 3)) + ' && echo T || echo F'
        return 'test "' + a.strip('"') + '" ' + opx + ' "' + b.strip('"') + '" && echo T || echo F'
    if k == 24:
        return "f() { printf '[%s]' \"$#\" \"$@\"; }; f " + ' '.join(word(r) for _ in range(r.randint(0, 3))) + '; echo'
    # --- Iteration 478: the third grammar ---
    if k == 25:          # redirections on groups and simple commands
        tgt = '"$T/r' + str(r.randint(1, 2)) + '"'
        return r.choice([
            '{ echo g1; echo g2 >&2; } > ' + tgt + ' 2>&1; cat ' + tgt,
            '{ echo out; echo err >&2; } 2>/dev/null',
            'echo first > ' + tgt + '; echo second >> ' + tgt + '; cat < ' + tgt,
            '( echo sub >&2 ) 2>&1 | tr a-z A-Z',
            'exec 3>' + tgt + '; echo via3 >&3; exec 3>&-; cat ' + tgt,
            'cat <<EOF > ' + tgt + '\nbody $x\nEOF\ncat ' + tgt])
    if k == 26:          # nested quoting
        return r.choice([
            'printf \'[%s]\' "$(printf \'%s\' "a\\"b")"; echo',
            'printf \'[%s]\' "${' + v + ':+"q $' + v + '"}"; echo',
            'printf \'[%s]\' \'a\'"b"\\c"$' + v + '"; echo',
            'printf \'[%s]\' "`printf \'%s\' \\\\x`"; echo',
            'printf \'[%s]\' "$(echo "$(echo "in \'$' + v + '\'")")"; echo'])
    if k == 27:          # arithmetic literals and precedence
        e = r.choice(['0x1f', '010', '1+2*3', '(1+2)*3', '7/2', '-7/2', '7%-3', '1<<4|1', '~5', '!0+!1',
                      '3>2&&2>3||1', '1?2?3:4:5', '-(-(3))', '2*-3', '0x10+010+10'])
        return "printf '[%s]' $((" + e + ")); echo"
    if k == 28:          # break and continue with a count
        return ('for i in 1 2 3; do for j in a b c; do [ $j = ' + r.choice(['a', 'b', 'c']) + ' ] && ' +
                r.choice(['break', 'continue', 'break 2', 'continue 2']) + "; printf '%s%s ' $i $j; done; done; echo")
    if k == 29:          # EXIT traps in subshells
        return "( trap 'echo exiting' EXIT; echo body" + r.choice(['', '; exit 3', '; false']) + ' ); echo "st=$?"'
    if k == 30:          # <<- strips leading tabs
        return 'cat <<-EOF\n\tone\n\t\ttwo $' + v + '\n\tEOF'
    if k == 32:          # prefix assignments whose values have side effects (Iteration 481)
        # The words of a simple command are expanded before its assignments
        # (EXPANSION-ORDER.md stage 1). No redirection beside them yet: which
        # comes first, a redirection or an assignment, is stage 2.
        cmd = r.choice(["printf '[%s]'", 'sh -c \'printf "[%s]" "$v" "$@"\' sh'])
        return r.choice([
            'n=' + str(r.randint(0, 3)) + '; v=$((n+=1)) ' + cmd + ' "$n" $((n+=10)); echo " n=$n"',
            'unset w; v=${w=set} ' + cmd + ' "${w-unset}"; echo " w=${w-unset}"',
            'n=0; a=$((n+=1)) b=$((n*10)) sh -c \'echo "$a $b"\'; echo " n=$n"',
            'v=$(echo sub) ' + cmd + ' "$(echo word)" "${v-none}"; echo',
            'n=5; v=$((n*=2)) w=$n ' + cmd + ' "$n"; echo " n=$n"',
            'v=`exit 3` `exit ' + str(r.randint(0, 4)) + '`; echo "st=$?"'])
    if k == 31:          # IFS given to read
        return ("IFS=" + quote(r.choice([':', ' :', ',', ':,'])) + " read -r a b c <<'EOF'\n" +
                r.choice(['a:b:c', ' a : b ', 'a,,b', 'x:y:z:w', ':lead', 'trail:']) +
                "\nEOF\nprintf '[%s]' \"$a\" \"$b\" \"$c\"; echo")
    return None

def statement(r, depth=0):
    k = r.randrange(33)
    if k >= 16:
        m = more(r, k, depth)
        if m is not None:
            return m
        k = r.randrange(16)
    v = r.choice(['x', 'y', 'z'])
    if k == 0:
        return v + '=' + quote(r.choice(VALUES))
    if k == 1:
        return 'unset ' + v
    if k == 2:
        ifs = r.choice(IFSES)
        return 'unset IFS' if ifs is None else 'IFS=' + quote(ifs)
    if k == 3:
        return 'set -- ' + ' '.join(quote(r.choice(VALUES)) for _ in range(r.randint(0, 3)))
    if k in (4, 5, 6):
        return "printf '[%s]' " + ' '.join(word(r) for _ in range(r.randint(1, 3))) + '; echo'
    if k == 7:
        pats = ' | '.join(r.choice(PATTERNS) or '""' for _ in range(r.randint(1, 2)))
        return 'case ' + word(r) + ' in ' + pats + ') echo hit;; *) echo miss;; esac'
    if k == 8 and depth < 2:
        return 'for i in ' + ' '.join(word(r) for _ in range(r.randint(1, 3))) + "; do printf '<%s>' \"$i\"; done; echo"
    if k == 9:
        return 'test -n ' + word(r) + ' && echo yes || echo no'
    if k == 10 and depth < 2:
        return 'f() { ' + statement(r, depth + 1) + '; return ' + str(r.randint(0, 3)) + '; }; f ' + word(r) + '; echo "st=$?"'
    if k == 11:
        return 'cat <<' + r.choice(['EOF', "'EOF'"]) + '\n' + r.choice(['a $x b', 'lit', '${y-none}', '$(printf in)', 'c\\', '\t tab']) + '\nEOF'
    if k == 12:
        return ('printf \'%s\\n\' ' + word(r) + ' > "$T/f"; cat "$T/f"; printf \'%s\\n\' ' + word(r) +
                ' >> "$T/f"; wc -l < "$T/f" | tr -d " "')
    if k == 13 and depth < 2:
        return 'if ' + r.choice(['true', 'false', 'test -z "$x"', '[ "$y" = a ]']) + '; then ' + statement(r, depth + 1) + '; else echo else; fi'
    if k == 14:
        return 'read -r ' + ' '.join(r.sample(['p', 'q', 's'], r.randint(1, 3))) + " <<'EOF'\n" + r.choice(VALUES + ['a b c d']) + "\nEOF\nprintf '[%s]' \"$p\" \"$q\" \"$s\"; echo"
    return '(' + statement(r, depth + 1) + '); echo "sub=$?"' if depth < 2 else 'echo end'

def script(r):
    lines = ['T=.', 'x=a y=\'a b\' z=']
    lines += [statement(r) for _ in range(r.randint(3, 9))]
    lines.append('echo "last=$?"')
    return '\n'.join(lines) + '\n'

def run(argv, text, scratch):
    p = os.path.join(scratch, 's.sh')
    with open(p, 'w') as f:
        f.write(text)
    try:
        # A relative path and no arguments: anything that differs between
        # the two scratch directories must not reach the output.
        c = subprocess.run(argv + ['s.sh'], cwd=scratch, capture_output=True, timeout=10,
                           env=dict(os.environ, LC_ALL='C'))
        return c.stdout, c.returncode
    except subprocess.TimeoutExpired:
        return b'<timeout>', -1

BASH = shutil.which('bash')

def outputs(text, shells):
    res = []
    for sh in shells:
        d = tempfile.mkdtemp(prefix='dfz-')
        try:
            res.append(run(sh, text, d))
        finally:
            shutil.rmtree(d, ignore_errors=True)
    return res

def differs(text):
    """dash's result and this shell's - equal unless there is a finding"""
    d, s = outputs(text, [[DASH], [RELFSH]])
    # A finding is a difference from BOTH references, which agree with each
    # other. Where dash and bash disagree the question is open, and this
    # shell's answer - whichever side it takes - is not a finding: a
    # leading non-whitespace IFS character inside a parameter is an empty
    # field in bash and here and none in dash, and `$@` in a here-document
    # with IFS empty joins with nothing in dash and with spaces in bash
    # (Iteration 471). GOALS.md records the choices made on purpose.
    if d != s and BASH:
        (b,) = outputs(text, [[BASH, '--posix']])
        if b != d:
            return s, s
    return d, s

def shrink(text):
    lines = text.split('\n')
    i = 2
    while i < len(lines):
        trial = lines[:i] + lines[i + 1:]
        d, s = differs('\n'.join(trial))
        if d != s:
            lines = trial
        else:
            i += 1
    return '\n'.join(lines)

def main():
    a = sys.argv[1:]
    secs = int(a[a.index('--seconds') + 1]) if '--seconds' in a else 60
    out = a[a.index('--out') + 1] if '--out' in a else os.path.join(ROOT, 'tests', 'fuzzfinds')
    seed = int(a[a.index('--seed') + 1]) if '--seed' in a else int(time.time())
    if not DASH:
        print('difffuzz: dash is not installed; it is the reference'); return 2
    r = random.Random(seed)
    end = time.time() + secs
    n = found = 0
    seen = set()
    while time.time() < end:
        text = script(r)
        n += 1
        d, s = differs(text)
        if d == s:
            continue
        small = shrink(text)
        key = hashlib.sha1(small.encode()).hexdigest()[:10]
        if key in seen:
            continue
        seen.add(key)
        found += 1
        os.makedirs(out, exist_ok=True)
        d, s = differs(small)
        with open(os.path.join(out, 'diff-' + key + '.sh'), 'w') as f:
            f.write('# difffuzz seed %d: dash %r status %d / this shell %r status %d\n' % (seed, d[0], d[1], s[0], s[1]))
            f.write(small)
        print('DIFF', key, 'dash', d, 'relf', s)
    print('difffuzz: %d scripts, %d difference(s), seed %d' % (n, found, seed))
    return 1 if found else 0

if __name__ == '__main__':
    sys.exit(main())
