#!/bin/sh
# tools/gen-opcodes.sh [--check] - the opcode map, from its one source.
#
# opcodes.tab lists every CV8 opcode and escape selector (Iteration 518;
# CV8.md 2.2). Without arguments this writes cv8-ops.h - the engine's
# dispatch tables - to standard output; the Makefile keeps the committed
# copy current, and it is committed so that `cc -o relf64 cv8.c` still
# needs nothing else.
#
# With --check it confirms that everything which must state the same
# numbers by itself still does, and says what differs:
#   - the table is consistent: the direct primitives numbered from 0, the
#     synthetic band at their count, the escape selectors from 0;
#   - kernel.4's PRIMITIVE lines, direct then escaped, name the table's
#     primitives in the table's order, and its `N OPCODE name` lines
#     match the tiny-word rows;
#   - cross.4's and shadow.4's opcode constants hold the table's numbers;
#   - cv8-ops.h is what this script would write now.
# tests/portability runs it. POSIX sh and awk only: no Python to build.
set -e
dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tab=$dir/engine/opcodes.tab

generate() {
    awk '
    /^#/ || NF == 0 { next }
    { kind = $1; num = $2; name = $3; lab = $4 }
    name == "BRANCH8" { b8 = num }
    kind == "direct"  { d = d (nd++ ? ", " : "") "&&" lab; next }
    kind == "escaped" { e = e (ne++ ? ", " : "") "&&" lab; next }
    { o = o (no++ ? ", " : "") "[" num "] = &&" lab }
    function wrap(s,    out, n, i, parts, line) {
        n = split(s, parts, ", "); line = "   "; out = ""
        for (i = 1; i <= n; i++) {
            if (length(line) + length(parts[i]) + 3 > 76) { out = out line " \\\n"; line = "   " }
            line = line " " parts[i] (i < n ? "," : "")
        }
        return out line
    }
    END {
        print "/*  engine/cv8-ops.h - GENERATED from engine/opcodes.tab by tools/gen-opcodes.sh."
        print " *  Do not edit: change engine/opcodes.tab and run make. The engine'\''s"
        print " *  dispatch tables - the direct primitives in order, the escaped"
        print " *  ones in order, every other opcode at its number (CV8.md 2.2).  */"
        printf "#define NDIRECT %d\n#define NESC    %d\n", nd, ne
        print "#define CV8_OPS_DIRECT \\";  print wrap(d)
        print "#define CV8_OPS_ESCAPED \\"; print wrap(e)
        print "#define CV8_OPS_OTHER \\";   print wrap(o)
        printf "#define OPC_BRANCH8 %s   /* the loop opcodes step over it */\n", b8
    }' "$tab"
}

# --asm SOURCE: the assembly engine's tables (ASM-ENGINE.md), and a stub
# for every handler SOURCE does not define yet, which names the opcode
# and exits - so the engine can be written one handler at a time and
# never jumps into garbage on the rest.
# --forth-ops: the same tables, for relfasm64.4 - the engine's Forth source
# (Iteration 549, SELF-HOSTING.md M5): opcodes.tab stays their one source.
# The repeated entries are counted loops inside colon words - relf does not
# run DO ... LOOP at the top level.
generate_forth_ops() {
    awk '
    function hex(s,   v, i) { v = 0; s = tolower(s); sub(/^0x/, "", s)
        for (i = 1; i <= length(s); i++) v = v * 16 + index("0123456789abcdef", substr(s, i, 1)) - 1
        return v }
    /^#/ || NF == 0 { next }
    { if ($1 == "escaped") esc[nesc++] = $4; else op[hex($2)] = $4 }
    END {
        print "\\ engine/relfasm-ops.4 - GENERATED from engine/opcodes.tab by tools/gen-opcodes.sh"
        print "\\ --forth-ops; do not edit. The engine'"'"'s two dispatch tables."
        print "8 ALIGN,"
        print "dispatch256 L:"
        line = ""
        for (i = 0; i < 128; i++) {
            line = line sprintf("%s 0 Q,+  ", (i in op) ? op[i] : "L_badop")
            if (i % 4 == 3) { print line; line = "" } }
        print ": CALL-ENTRIES ( --- ) 128 0 DO do_call 0 Q,+ LOOP ;  CALL-ENTRIES"
        print "esc_tab L:"
        line = ""
        for (i = 0; i < nesc; i++) {
            line = line sprintf("%s 0 Q,+  ", esc[i])
            if (i % 4 == 3) { print line; line = "" } }
        if (line != "") print line
        printf ": BAD-ESCAPES ( --- ) %d 0 DO L_badesc 0 Q,+ LOOP ;  BAD-ESCAPES\n", 256 - nesc
    }' "$tab"
}
generate_forth_consts() {
    awk '
    function hex(s,   v, i) { v = 0; s = tolower(s); sub(/^0x/, "", s)
        for (i = 1; i <= length(s); i++) v = v * 16 + index("0123456789abcdef", substr(s, i, 1)) - 1
        return v }
    /^#/ || NF == 0 { next }
    $3 == "BRANCH8" {
        print "\\ engine/relfasm-consts.4 - GENERATED from engine/opcodes.tab by tools/gen-opcodes.sh"
        print "\\ --forth-consts; do not edit."
        printf "%d CONSTANT OPC_BRANCH8      \\ the loop opcodes step over it\n", hex($2) }' "$tab"
}

case "${1:-}" in
    --forth-ops) generate_forth_ops; exit 0 ;;
    --forth-consts) generate_forth_consts; exit 0 ;;
    --check) ;;
    *)       generate; exit 0 ;;
esac

problems=0
bad() { echo "gen-opcodes: $*" >&2; problems=$((problems + 1)); }

# the table's own consistency. Numbers are parsed here, never left to
# awk: "0x01" + 0 is 1 in mawk and busybox awk, which pass the string to
# strtod, and 0 in gawk - so the first version of this check passed on
# Ubuntu and failed on the Gentoo board (Iteration 520).
awk '
function num(s,   v, i) {
    if (s !~ /^0[xX]/) return s + 0
    v = 0; s = tolower(substr(s, 3))
    for (i = 1; i <= length(s); i++) v = v * 16 + index("0123456789abcdef", substr(s, i, 1)) - 1
    return v
}
/^#/ || NF == 0 { next }
$1 == "direct"  { if (num($2) != nd) { printf "direct %s is not at %d\n", $3, nd; bad = 1 } nd++ }
$1 == "escaped" { if (num($2) != ne) { printf "selector %s is not %d\n", $3, ne; bad = 1 } ne++ }
$1 == "synth" && $3 == "LIT32" { if (num($2) != nd) { printf "LIT32 is not at the direct count %d\n", nd; bad = 1 } }
END { exit bad }' "$tab" >&2 || problems=$((problems + 1))

# every opcode's operand format is one the decoders know (Iteration 533):
# a typo there would not fail, it would misdecode every image quietly
awk '/^#/ || NF == 0 { next } $1 != "escaped" && $5 !~ /^(-|u8|i8|u16|i32|u64|b8|b16|slot|sel|data)$/ {
    printf "gen-opcodes: %s has no known operand format (\"%s\")\n", $3, $5; bad = 1 }
END { exit bad }' "$tab" >&2 || problems=$((problems + 1))

# kernel.4's primitives, in order
awk '/^#/ || NF == 0 { next } $1 == "direct" || $1 == "escaped" { print $3 }' "$tab" > /tmp/gen-opcodes.tab.$$
awk '/^ESCAPED/ { next } /^PRIMITIVE[ \t]/ { print $2 }' "$dir/forth/kernel.4" > /tmp/gen-opcodes.k4.$$
if ! cmp -s /tmp/gen-opcodes.tab.$$ /tmp/gen-opcodes.k4.$$; then
    bad "forth/kernel.4's PRIMITIVE lines differ from engine/opcodes.tab's direct and escaped rows:"
    diff /tmp/gen-opcodes.tab.$$ /tmp/gen-opcodes.k4.$$ | sed 's/^/    /' >&2 || true
fi
ndirect=$(awk '/^#/ || NF == 0 { next } $1 == "direct" { n++ } END { print n + 0 }' "$tab")
kdirect=$(awk '/^ESCAPED/ { exit } /^PRIMITIVE[ \t]/ { n++ } END { print n + 0 }' "$dir/forth/kernel.4")
[ "$ndirect" = "$kdirect" ] || bad "forth/kernel.4 has $kdirect primitives before ESCAPED, engine/opcodes.tab $ndirect direct ones"
rm -f /tmp/gen-opcodes.tab.$$ /tmp/gen-opcodes.k4.$$

# kernel.4's tiny words: `N OPCODE name`. Read from a file, not a pipe:
# a `while` at the end of a pipeline runs in a subshell, where `bad`
# counted into a copy of `problems` - the first version of this printed
# the complaint and then said everything agreed (found by breaking it on
# purpose, Iteration 518).
awk '/^#/ || NF == 0 { next } $1 == "tiny" { print $2, $3 }' "$tab" > /tmp/gen-opcodes.tiny.$$
while read -r num name; do
    dec=$(printf '%d' "$num")
    grep -q "^$dec OPCODE $name[ \t]" "$dir/forth/kernel.4" ||
        bad "forth/kernel.4 does not declare \`$dec OPCODE $name\`, as engine/opcodes.tab has it"
done < /tmp/gen-opcodes.tiny.$$
rm -f /tmp/gen-opcodes.tiny.$$

# cross.4's and shadow.4's constants: FILE NAME-OF-CONSTANT TABLE-NAME
while read -r file const name; do
    num=$(awk -v n="$name" '/^#/ { next } $3 == n && $1 != "escaped" { print $2; exit }' "$tab")
    [ -n "$num" ] || { bad "engine/opcodes.tab has no opcode $name"; continue; }
    dec=$(printf '%d' "$num")
    # Fields compared exactly: a name like VAR@+OP is not a pattern (the
    # first version used grep -E, where + is a quantifier, and a name with
    # a + in it could never match itself - Iteration 532)
    awk -v d="$dec" -v c="$const" '$1 == d && $2 == "CONSTANT" && $3 == c { f = 1 } END { exit !f }' "$dir/$file" ||
        bad "$file's $const is not $dec ($name in engine/opcodes.tab)"
done <<EOF
forth/cross.4 EXIT-OP EXIT
forth/cross.4 LIT16-OP LIT
forth/cross.4 BRANCH-OP BRANCH
forth/cross.4 0BRANCH-OP ?BRANCH
forth/cross.4 LIT0-OP push0
forth/cross.4 VAR@-OP VAR@
forth/cross.4 VAR!-OP VAR!
forth/cross.4 ADDI-OP ADDI
forth/cross.4 EQI-OP EQI
forth/cross.4 LIT64-OP LIT64
forth/cross.4 ESC-OP ESC
forth/cross.4 LOOP-OP (LOOP)
forth/cross.4 BRANCH8-OP BRANCH8
forth/cross.4 0BRANCH8-OP ?BRANCH8
forth/shadow.4 LSAVE-OP LSAVE
forth/shadow.4 LRESTORE-OP LRESTORE
forth/shadow.4 L!-OP L!
forth/shadow.4 LZERO-OP LZERO
EOF

# the committed header is the one this table makes
if ! generate | cmp -s - "$dir/engine/cv8-ops.h"; then
    bad "engine/cv8-ops.h is not what engine/opcodes.tab makes: run make"
fi

if [ "$problems" -gt 0 ]; then
    echo "gen-opcodes: $problems problem(s)" >&2
    exit 1
fi
echo "gen-opcodes: engine/opcodes.tab, forth/kernel.4, forth/cross.4, forth/shadow.4 and engine/cv8-ops.h agree"
