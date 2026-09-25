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
tab=$dir/opcodes.tab

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
        print "/*  cv8-ops.h - GENERATED from opcodes.tab by tools/gen-opcodes.sh."
        print " *  Do not edit: change opcodes.tab and run make. The engine'\''s"
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
generate_asm() {
    awk -v src="$1" '
    function hex(s,   v, i) { v = 0; s = tolower(s); sub(/^0x/, "", s)
        for (i = 1; i <= length(s); i++) v = v * 16 + index("0123456789abcdef", substr(s, i, 1)) - 1
        return v }
    BEGIN { while ((getline line < src) > 0)
                if (line ~ /^L[A-Za-z0-9_]*:/) { sub(/:.*/, "", line); def[line] = 1 } }
    /^#/ || NF == 0 { next }
    { kind = $1; name = $3; lab = $4
      if (kind == "escaped") esc[nesc++] = lab; else op[hex($2)] = lab
      if (!(lab in seen)) { seen[lab] = 1; order[nlab++] = lab; label_name[lab] = name } }
    END {
        print "/*  relfasm-ops.S - GENERATED from opcodes.tab by tools/gen-opcodes.sh"
        print " *  --asm; do not edit. The dispatch tables, and stubs for the handlers"
        print " *  relfasm64.S does not have yet. One section, as the engine is: it is"
        print " *  a single segment behind a hand-written ELF header.  */"
        print "    .balign 8"
        print "dispatch256:"
        for (i = 0; i < 128; i++) printf "    .quad %s\n", (i in op) ? op[i] : "L_badop"
        print "    .rept 128\n    .quad do_call\n    .endr"
        print "esc_tab:"
        for (i = 0; i < nesc; i++) printf "    .quad %s\n", esc[i]
        printf "    .rept %d\n    .quad L_badesc\n    .endr\n", 256 - nesc
        for (i = 0; i < nlab; i++) {
            l = order[i]; if (l in def) continue
            printf "%s:\n    lea rsi, [rip + %s_name]\n    jmp unimpl\n", l, l
            names = names sprintf("%s_name: .asciz \"%s (%s)\"\n", l, label_name[l], l)
        }
        printf "%s", names
    }' "$tab"
}

# --asm-consts: the constants the assembly source uses, for inclusion at
# its TOP - GAS picks an instruction's form where it meets a symbol, and a
# constant defined later is taken for memory (520, 529).
generate_asm_consts() {
    awk '/^#/ || NF == 0 { next } $3 == "BRANCH8" { printf "    .equ OPC_BRANCH8, %s\n", $2 }' "$tab"
}

case "${1:-}" in
    --asm)   generate_asm "$2"; exit 0 ;;
    --asm-consts) generate_asm_consts; exit 0 ;;
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

# the folded returns: opcodes.tab's fold rows, in order, are cross.4's
# FOLD-NAMES, each with ;EXIT - two sources of one numbering, unchecked
# until Iteration 536 removed four of them and renumbered the rest
fn=$(awk '/^CREATE FOLD-NAMES/ { f = 1; next } f && /NAMES,/ { for (i = 3; i <= NF; i++) printf "%s ", $i; next } f { exit }' "$dir/cross.4")
fr=$(awk '$1 == "fold" { n = $3; sub(/;EXIT$/, "", n); printf "%s ", n }' "$tab")
[ "$fn" = "$fr" ] || bad "cross.4's FOLD-NAMES ($fn) are not opcodes.tab's fold rows ($fr)"
nf=$(awk '$1 == "fold" { n++ } END { print n + 0 }' "$tab")
grep -q "^$nf CONSTANT #FOLD" "$dir/cross.4" || bad "cross.4's #FOLD is not $nf, the fold rows in opcodes.tab"

# kernel.4's primitives, in order
awk '/^#/ || NF == 0 { next } $1 == "direct" || $1 == "escaped" { print $3 }' "$tab" > /tmp/gen-opcodes.tab.$$
awk '/^ESCAPED/ { next } /^PRIMITIVE[ \t]/ { print $2 }' "$dir/kernel.4" > /tmp/gen-opcodes.k4.$$
if ! cmp -s /tmp/gen-opcodes.tab.$$ /tmp/gen-opcodes.k4.$$; then
    bad "kernel.4's PRIMITIVE lines differ from opcodes.tab's direct and escaped rows:"
    diff /tmp/gen-opcodes.tab.$$ /tmp/gen-opcodes.k4.$$ | sed 's/^/    /' >&2 || true
fi
ndirect=$(awk '/^#/ || NF == 0 { next } $1 == "direct" { n++ } END { print n + 0 }' "$tab")
kdirect=$(awk '/^ESCAPED/ { exit } /^PRIMITIVE[ \t]/ { n++ } END { print n + 0 }' "$dir/kernel.4")
[ "$ndirect" = "$kdirect" ] || bad "kernel.4 has $kdirect primitives before ESCAPED, opcodes.tab $ndirect direct ones"
rm -f /tmp/gen-opcodes.tab.$$ /tmp/gen-opcodes.k4.$$

# kernel.4's tiny words: `N OPCODE name`. Read from a file, not a pipe:
# a `while` at the end of a pipeline runs in a subshell, where `bad`
# counted into a copy of `problems` - the first version of this printed
# the complaint and then said everything agreed (found by breaking it on
# purpose, Iteration 518).
awk '/^#/ || NF == 0 { next } $1 == "tiny" { print $2, $3 }' "$tab" > /tmp/gen-opcodes.tiny.$$
while read -r num name; do
    dec=$(printf '%d' "$num")
    grep -q "^$dec OPCODE $name[ \t]" "$dir/kernel.4" ||
        bad "kernel.4 does not declare \`$dec OPCODE $name\`, as opcodes.tab has it"
done < /tmp/gen-opcodes.tiny.$$
rm -f /tmp/gen-opcodes.tiny.$$

# cross.4's and shadow.4's constants: FILE NAME-OF-CONSTANT TABLE-NAME
while read -r file const name; do
    num=$(awk -v n="$name" '/^#/ { next } $3 == n && $1 != "escaped" { print $2; exit }' "$tab")
    [ -n "$num" ] || { bad "opcodes.tab has no opcode $name"; continue; }
    dec=$(printf '%d' "$num")
    # Fields compared exactly: a name like VAR@+OP is not a pattern (the
    # first version used grep -E, where + is a quantifier, and a name with
    # a + in it could never match itself - Iteration 532)
    awk -v d="$dec" -v c="$const" '$1 == d && $2 == "CONSTANT" && $3 == c { f = 1 } END { exit !f }' "$dir/$file" ||
        bad "$file's $const is not $dec ($name in opcodes.tab)"
done <<EOF
cross.4 EXIT-OP EXIT
cross.4 LIT16-OP LIT
cross.4 BRANCH-OP BRANCH
cross.4 0BRANCH-OP ?BRANCH
cross.4 LIT0-OP push0
cross.4 VAR@-OP VAR@
cross.4 VAR!-OP VAR!
cross.4 ADDI-OP ADDI
cross.4 EQI-OP EQI
cross.4 LIT64-OP LIT64
cross.4 ESC-OP ESC
cross.4 LOOP-OP (LOOP)
shadow.4 LSAVE-OP LSAVE
shadow.4 LRESTORE-OP LRESTORE
shadow.4 L!-OP L!
shadow.4 LZERO-OP LZERO
EOF

# the committed header is the one this table makes
if ! generate | cmp -s - "$dir/cv8-ops.h"; then
    bad "cv8-ops.h is not what opcodes.tab makes: run make"
fi

if [ "$problems" -gt 0 ]; then
    echo "gen-opcodes: $problems problem(s)" >&2
    exit 1
fi
echo "gen-opcodes: opcodes.tab, kernel.4, cross.4, shadow.4 and cv8-ops.h agree"
