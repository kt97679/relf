#!/usr/bin/env python3
"""tools/feature-cost.py - what each shell feature costs, in code and in trouble.

Iteration 502, for GOALS.md "What comes next", item 4: before designing
a shell language of our own, find where the POSIX one's cost lives. Two
measures per feature:

  code      lines of code (not comments, not blank) in the colon
            definitions of shell.4, tree.4 and edit.4 that implement it;
  trouble   how many PROGRESS.md iterations name it in their title - a
            proxy for how hard it was to get right, not just to have.

Words are assigned to features by the rules below, in order, first match
wins - FORTH-STYLE.md's per-feature prefixes make the names carry it.
The rules are the judgement in this measurement; they are here to be
read and argued with. Words no rule claims are reported as such.
"""
import os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (feature, POSIX-required?, word-name regex). Order matters.
RULES = [
    ('line editor, history, completion', False, r'^(ED-|KEY|HIST|SEARCH|CMP-|COMPLET|EDIT|LINE-ED|TERM)'),
    ('prompt escapes',                   False, r'^(PD-|PROMPT|PS[124])'),
    ('the forth builtin',                False, r'FORTH'),
    ('arithmetic',                       True,  r'^(AE-|ARITH|XE-ARITH)|ARITH'),
    ('test and [',                       True,  r'^(TEST-|TP-|DO-TEST|DO-BRACKET)'),
    ('echo, printf, backslash escapes',  True,  r'^(PF-|PRINTF|DO-ECHO|DO-PRINTF|ECHO|EMIT-ESCAPE|ESCAPE|BS-)'),
    ('getopts',                          True,  r'^(GO-|DO-GETOPTS|GETOPTS)'),
    ('read',                             True,  r'^(READ-|DO-READ|RD-)'),
    ('cd and pwd',                       True,  r'^(CD-|DO-CD|DO-PWD|PWD|LOGICAL)'),
    ('ulimit, umask, kill, times',       True,  r'^(UL-|DO-ULIMIT|ULIMIT|UMS-|UMASK|DO-UMASK|KILL|DO-KILL|TIMES|DO-TIMES)'),
    ('traps and signals',                True,  r'(TRAP|SIG|INTR|DEFERRED)'),
    ('job control',                      True,  r'^(JOB|\.JOB|FG|BG|DO-FG|DO-BG|DO-JOBS|DO-WAIT|WAIT|EXEC-BG|TCSET|NOTICE|REAP)|FOREGROUND'),
    ('aliases',                          True,  r'^(AL-|ALIAS|SET-ALIAS|FIND-ALIAS|TRY-ALIAS|DO-ALIAS|DO-UNALIAS)'),
    ('here-documents',                   True,  r'^(HD|HEREDOC|PREPARE-.*HEREDOC)|HEREDOC'),
    ('pathname expansion and patterns',  True,  r'GLOB|MAGIC|^(SORT-MATCHES|FPM-|UNESCAPE-TO-PATH|CLOSED-BRACKET|GP-|GM-|GF-|BRACKET|PATTERN|CC-(IS|ALPHA|DIGIT|MATCH)|MATCH|FIELD-IS-PATTERN|CL-)'),
    ('field splitting (IFS)',            True,  r'^(IFS|XS-|EMIT-EXPANDED-CHAR|POS-PARAM-BREAK)|SPLIT'),
    ('command substitution',             True,  r'(CMDSUB|BACKQUOTE|SUBST)'),
    ('parameter expansion',              True,  r'^(XE-PARAM|POS-|SPECIAL-PARAM|FIND-FWD|FIND-BWD|FIND-TRIM|TRIM|EMIT-ALL-POS|LINENO)|PARAM'),
    ('quoting, $\'...\', word encoding', True,  r'^(ENC|XQ-|DSQ|STRIP-QUOTES|QUOTE|PRINT-ENC)|SQUOTE|DQUOTE|QUOTE'),
    ('the expander, in general',         True,  r'^(XE-|EXPAND|EW|EMIT|COPY-LITERAL|GROW|ARGV|ADD-WORD|ADD-MATCH|DROP-ARGV|PASSWD|TILDE|EXPANSION|ALL-LITERAL|JOIN-ARGV|ROOM-FOR-ARG|ARGS-BUFFER|TW-)'),
    ('lexer and parser',                 True,  r'^(SCAN|PARSE|TOKEN|TOK-|LEX|RESERVED|SYNTAX|SRC-|COPY-SRC|REFILL|SPLICE|PEEK|NEXT|EXPECT|NODE|VEC|WORD|KEYWORD|KW-|DOLLAR|IONUM|TEXT>|I-|PRINT-NODE|TREE-DUMP|LIST-NODE|DUMP|SIMPLE-ITEM|OP>|ONE-SIMPLE|CLOSER|\.OP|AT-END|BLANK|DRAIN|OP-|NAME-TOKEN|VALID-NAME|NAME-TABLE)|CONT'),
    ('redirections',                     True,  r'(REDIR|^RD|APPLY|^FD|NOCLOBBER|DUP-|^OPEN)'),
    ('variables and the environment',    True,  r'(SHVAR|^SET-|EXPORT|UNSET|READONLY|^XP-|^TEMP-|^EWA|ASSIGN|^VAR|ENV|LOCAL|SHIFT|SET-POS|^VALUE-|LOOKUP-VAR)'),
    ('functions',                        True,  r'(FUNC|^FT-|RETURN)'),
    ('options and tracing (set)',        True,  r'^(OPT|XTRACE|VERBOSE|ERREXIT|SET-BAD-OPTION|DO-SET|EMIT-OPTION|LIST-OPTIONS)'),
    ('execution and control flow',       True,  r'^\(?(EXEC|RUN|TYPE|HAS-SLASH|BUILD-BUILTIN|NOTE-EXEC|COMMAND-|INDEX-|TREE|LIST|PIPE|STAGE|FORK|CMD|DISPATCH|CC-|PATH|LOCATE|TRY-EXEC|BUILTIN|FIND-BUILTIN|SPECIAL-BUILTIN|EVAL|DO-EVAL|DOT|DO-DOT|SOURCE|BREAK|CONTINUE|DO-BREAK|DO-CONTINUE|DO-EXIT|DO-RETURN|DO-COMMAND|DO-EXEC|DO-HASH|DO-TYPE|LOOP|SUBSHELL|FINAL)'),
    ('other builtins',                   True,  r'^DO-'),
    ('startup and the main loop',        True,  r'^(MAIN|SHELL|STARTUP|INIT|BOOT|INTERACTIVE)'),
    ('memory, strings, output (plumbing)', True, r'^(BODY-|SAFE-|\.STR|STRDUP|N>STR|CSTR|MEM|BUF|ALLOC|POOL|STR|\.|TYPE-|CHAR|DIGIT|UPPER|LOWER|NUM|HEX|BYTE|COUNT|BL-|SPACE|NL|CR-)'),
]

# Words in these files belong to a feature whatever their names.
BY_FILE = {'edit.4': 'line editor, history, completion'}

# Title keywords for the trouble count, per feature.
TROUBLE = {
    'line editor, history, completion': r'line editor|history|complet|TAB|cursor|\^R|edit\.4',
    'prompt escapes': r'prompt|PS1|PS2|PS4',
    'arithmetic': r'arithmetic|\$\(\(',
    'test and [': r'\btest\b|\[ ',
    'echo, printf, backslash escapes': r'\becho\b|printf|backslash',
    'getopts': r'getopts',
    'read': r'\bread\b',
    'traps and signals': r'trap|signal|SIGINT|\^C|SIGQUIT|kill',
    'job control': r'\bjob|\bwait\b|\bfg\b|\bbg\b|background|foreground|\$!',
    'aliases': r'alias',
    'here-documents': r'here-doc|heredoc|<<',
    'pathname expansion and patterns': r'glob|pathname|pattern|bracket|\bcase\b',
    'field splitting (IFS)': r'IFS|field|split',
    'command substitution': r'command substitution|\$\(|backquote',
    'parameter expansion': r'parameter|\$\{|\btrim|\$@|\$\*|\$#|positional',
    'quoting, $\'...\', word encoding': r'quot|escape|\$\'',
    'lexer and parser': r'pars|lex|token|keyword|reserved|syntax|continuation|newline',
    'redirections': r'redirect|descriptor|>&|noclobber|dup',
    'variables and the environment': r'variable|export|unset|readonly|assign|environment|local',
    'functions': r'function|\breturn\b',
    'options and tracing (set)': r'set -|option|xtrace|errexit|-e\b',
    'execution and control flow': r'pipeline|subshell|\bexec\b|\bloop|\bfor\b|\bwhile\b|\buntil\b|\bif\b|compound|exit status|\bbreak\b|continue|\beval\b|\bdot\b|\bsource|command tree|\bPATH\b',
    'the expander, in general': r'expan|tilde|word',
    'ulimit, umask, kill, times': r'ulimit|umask|\btimes\b',
    'cd and pwd': r'\bcd\b|\bpwd\b|PWD',
}

def words():
    out = []
    for f in ('shell.4', 'tree.4', 'edit.4'):
        L = open(os.path.join(ROOT, f)).read().split('\n')
        starts = [i for i, l in enumerate(L) if re.match(r'^: \S', l)]
        for k, i in enumerate(starts):
            j = starts[k + 1] if k + 1 < len(starts) else len(L)
            code = sum(1 for l in L[i:j] if l.strip() and not l.strip().startswith('\\'))
            out.append((f, L[i].split()[1], code))
    return out

def classify(f, name):
    if f in BY_FILE:
        return BY_FILE[f]
    for feat, _, rx in RULES:
        if re.search(rx, name):
            return feat
    return '(no rule)'

def main():
    posix = {feat: p for feat, p, _ in RULES}
    code = collections.Counter(); nwords = collections.Counter(); unclaimed = []
    for f, name, n in words():
        feat = classify(f, name)
        code[feat] += n; nwords[feat] += 1
        if feat == '(no rule)': unclaimed.append((n, name))
    titles = re.findall(r'^## Iteration \d+\S*: (.*)$', open(os.path.join(ROOT, 'PROGRESS.md')).read(), flags=re.M)
    trouble = {feat: sum(1 for t in titles if re.search(rx, t, flags=re.I)) for feat, rx in TROUBLE.items()}
    total = sum(code.values())
    print('%d lines of code in %d definitions (shell.4, tree.4, edit.4); %d iteration titles\n'
          % (total, sum(nwords.values()), len(titles)))
    print('%-34s %5s %6s %6s %6s  %s' % ('feature', 'words', 'lines', '%', 'cum %', 'trouble'))
    cum = 0
    for feat, n in code.most_common():
        cum += n
        tag = '' if posix.get(feat, True) else '  (not POSIX)'
        print('%-34s %5d %6d %5.1f%% %5.1f%%  %5s%s' % (feat, nwords[feat], n, 100.0 * n / total,
              100.0 * cum / total, trouble.get(feat, '-'), tag))
    if unclaimed:
        unclaimed.sort(reverse=True)
        print('\nunclaimed, largest first: ' + ', '.join('%s (%d)' % (w, n) for n, w in unclaimed[:25]))

main()
