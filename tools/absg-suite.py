#!/usr/bin/env python3
"""tools/absg-suite.py - examples from the Advanced Bash-Scripting Guide.

    git clone https://github.com/pmarinov/bash-scripting-guide /tmp/absg
    ABSG=/tmp/absg python3 tools/absg-suite.py [--keep DIR]

The guide is about bash, so most of its examples use bash-only
features. The ones a POSIX shell should run are found the way the
busybox and yash corpora were used (Iterations 369-388): run each under
dash, keep those dash runs successfully and repeatably, and compare
this shell's stdout and status against dash's on exactly those.

Safety first, because these are arbitrary scripts from a book:
  - only the chapters about the LANGUAGE (expansion, quoting, loops,
    tests, here-documents, functions, arithmetic) are considered;
  - an example naming any command that changes the system - rm, mv,
    mount, kill, shutdown, dd, chmod, network tools, sudo - is skipped;
  - each runs in its own empty temporary directory, with a timeout,
    stdin closed and HOME pointed at that directory.

Prints the counts and the list of examples dash passes and this shell
does not; --keep DIR writes each of those as a script, for triage into
tests/diff/cases.
"""
import os, re, subprocess, sys, tempfile, shutil

ABSG = os.environ.get('ABSG', '/tmp/absg')
HERE = os.path.dirname(os.path.abspath(__file__))
RELFSH = os.path.abspath(os.path.join(HERE, '..', 'relfsh'))
CHAPTERS = ('param_substit', 'string_manipulation', 'quoting', 'escapingsection',
            'special_chars', 'loops', 'loops1', 'nested_loops', 'loopcontrol',
            'test_constructs', 'fto', 'comparison_ops', 'nestedifthen', 'opprecedence',
            'arithmetic_operators', 'arith_exp', 'here_docs', 'functions',
            'complex_functions', 'local_variables', 'variables', 'var_subst',
            'untyped', 'assignment', 'other_type_vars', 'testbranch', 'case_select',
            'command_subst', 'subshells', 'exit_status', 'internal_variables',
            'internal_commands', 'list_cons', 'io_redirection', 'redircb',
            'globbingref', 'aliases', 'zeros', 'operations')
DANGER = re.compile(r'\b(rm|mv|mount|umount|kill|killall|shutdown|reboot|halt|dd|'
                    r'chmod|chown|mkfs|fdisk|sudo|su|wget|curl|ssh|ftp|nc|ping|'
                    r'crontab|passwd|useradd|userdel|ifconfig|route|iptables|'
                    r'eject|format|sync|tee|/dev/sd|/dev/hd|\bat\b|batch)\b')
BASHISM = re.compile(r'\[\[|\(\(|\bdeclare\b|\btypeset\b|\blet\b|\bshopt\b|\bselect\b|'
                     r'<<<|\$\{[^}]*(\[|\^|,|:[0-9-])|\bfunction\b|\barray\b|&>|\|&|'
                     r'\bsource\b|\bmapfile\b|\breadarray\b|\$RANDOM|\$SECONDS|'
                     r'\$BASH|\bbuiltin\b|\benable\b|\bcompgen\b|\bpushd\b|\bpopd\b')

def examples(path):
    text = open(path, encoding='utf-8', errors='replace').read()
    i = 0
    while True:
        j = text.find('\u25caexample{', i)
        if j < 0:
            return
        k = j + len('\u25caexample{')
        depth, m = 1, k
        while m < len(text) and depth:
            if text[m] == '{': depth += 1
            elif text[m] == '}': depth -= 1
            m += 1
        yield text[k:m-1]
        i = m

def run(shell, script, d):
    env = {'PATH': os.environ['PATH'], 'HOME': d, 'LC_ALL': 'C', 'USER': 'someone'}
    try:
        p = subprocess.run(shell + [script], cwd=d, env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, timeout=10)
        return p.returncode, p.stdout
    except subprocess.TimeoutExpired:
        return 'timeout', b''

def main():
    keep = None
    if '--keep' in sys.argv:
        keep = sys.argv[sys.argv.index('--keep') + 1]
        os.makedirs(keep, exist_ok=True)
    pages = os.path.join(ABSG, 'pages')
    if not os.path.isdir(pages):
        sys.exit('no guide at %s: see the header of this file' % ABSG)
    counts = dict(found=0, language=0, safe=0, posix=0, dash_ok=0, agree=0)
    differ = []
    for name in sorted(os.listdir(pages)):
        chapter = name.split('.')[0]
        for n, ex in enumerate(examples(os.path.join(pages, name))):
            counts['found'] += 1
            if chapter not in CHAPTERS:
                continue
            counts['language'] += 1
            body = re.sub(r'\u25ca\w+\{([^}]*)\}', r'\1', ex)   # inline markup
            if DANGER.search(body):
                continue
            counts['safe'] += 1
            if BASHISM.search(body):
                continue
            counts['posix'] += 1
            d = tempfile.mkdtemp(prefix='absg-')
            script = os.path.join(d, 'ex.sh')
            open(script, 'w').write(body + '\n')
            a = run(['dash'], script, d)
            b = run(['dash'], script, d)
            if a[0] != 0 or a != b:
                shutil.rmtree(d, ignore_errors=True)
                continue
            counts['dash_ok'] += 1
            mine = run([RELFSH], script, d)
            if mine == a:
                counts['agree'] += 1
            else:
                tag = '%s-%d' % (chapter, n)
                differ.append(tag)
                if keep:
                    shutil.copy(script, os.path.join(keep, tag + '.sh'))
            shutil.rmtree(d, ignore_errors=True)
    print('examples found %(found)d; in language chapters %(language)d; '
          'safe to run %(safe)d; no obvious bashism %(posix)d' % counts)
    print('dash runs %d cleanly and repeatably; this shell agrees on %d, differs on %d'
          % (counts['dash_ok'], counts['agree'], len(differ)))
    for t in differ:
        print('  differs: %s' % t)

main()
