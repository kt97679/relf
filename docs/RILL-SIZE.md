# Where Rill's image goes - the audit, and what would keep it small (Iteration 826)

At the user's asking, when kernel64-rill.img (91,526 bytes) had grown to 70 % of relfsh's
kernel64-shell.img (130,348). Measured by tools/rill-size.py, which builds the image a file at a
time and walks its dictionary; run it again whenever the image grows.

| layer | bytes | share | words | headers | bodies |
|---|---:|---:|---:|---:|---:|
| kernel64.img and the shared Forth (extend, safety, pool, shadow, save-system) | 14,839 | 16 % | 458 | 4,102 | 10,441 |
| genes | 193 | 0 % | 15 | 159 | 34 |
| rt.4, the runtime | 20,538 | 22 % | 418 | 3,965 | 16,573 |
| regex.4 | 4,560 | 5 % | 95 | 931 | 3,629 |
| the characters' widths (shell.4's tables) | 4,109 | 4 % | 12 | 121 | 3,988 |
| edit-shim.4 and edit.4, the prompt's editor | 8,187 | 9 % | 165 | 2,060 | 6,127 |
| **compile.4, the image's compiler** | **39,044** | **43 %** | 466 | 4,440 | 34,604 |

Headers - a word's link, count byte and name - are 15.8 KB of the image (17 %): what EVALUATE needs
of the runtime's words, since the compiler writes Forth as text, and what nothing needs of the
compiler's and the editor's own once the image is built. The compiler holds 882 string literals,
7,152 bytes of text: Forth it writes (`S" R-NEW-LIST" OUT+`), tokens it compares (`S" (" CUR-IS?`, 23
times), and 116 error messages, 3,852 bytes. Repeated literals cost about 2.8 KB. The largest words:
ZERO-WIDTH (2,595, a table), LIBRARY (2,361), BINOP (1,623), WIDE-CHARS (1,049, a table), DEF-STMT,
FOR-STMT. The genes cost 6.6 KB together, purestack 1,368 and infer 1,128 the most; the search that
chose them (RILL-SEARCH.md) weighed speed, generated Forth and source - never the image's bytes. Five
runtime words nothing uses: LM-K, R-EXEC, RC-D, RC-HI, RC-LO.

## What would keep it small (QUESTIONS.md Q39)

1. **Two images**: scripts without the editor, the prompt with it - the script image 91.5 KB to
   about 79.2 KB, nothing slower or lost; `rill` with no script at a terminal loads the second.
2. **The genes scored again with the image's bytes in the score** (tools/rill-search.py): up to
   6.6 KB at stake; the search's own numbers show most genes buying 3 % or less - perhaps 1-3 KB.
3. **The compiler's repeated literals as words** - a token compared (`(`, `)`, `{`, `}`), the prefix
   `rillc: line ` (15 times): perhaps 1-1.5 KB of the 2.8 KB; the oracle checks it.
4. **The five dead words**: some 0.2 KB.
5. **No names for words nothing looks up** - the compiler's 466, the editor's 165, the runtime's own
   helpers: up to 7-8 KB, but it needs a kernel feature (a definition without a header, or an image
   stripped and relinked), and the kernel is every image's.
6. Not recommended: shorter error messages (3.9 KB - their clarity is the point); an image without
   its compiler (43 %) - the prompt and `rill script.rill` need it.
