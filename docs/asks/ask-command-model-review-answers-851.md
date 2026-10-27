# Answers to the command model's review prompt, checked (852)

Five answers to `ask-command-model-review-851.md`: Gemini, Grok, DeepSeek, ChatGPT and Qwen, as the
owner named them. None found the direction wrong; all found the draft's contracts unfinished.
Claims about the draft were checked against its text; claims about other languages against their
documentation.

## What held

| | finding | from | checked | verdict |
|---|---|---|---|---|
| H1 | a function's `echo` output corrupts a capture meant for `put` | all five | rule 2 says a capture takes "a function's values" but never that `echo` stays out; Elvish's capture takes both, byte lines as values (elv.sh, Effective Elvish) | held: captures take value output only |
| H2 | blocks made in a loop all see the loop's last value | all five | by-reference closures over one loop variable do; Go changed exactly this in 1.22 - a fresh variable each iteration, "one of the most common Go mistakes" (go.dev, LoopvarExperiment), at a cost only where a closure captures it | held: fresh per iteration |
| H3 | `return` and `break` inside blocks undecided | Grok, DeepSeek, ChatGPT, Qwen | the draft's leaning; Ruby's `return` in a block leaves the enclosing method | held: `return` the nearest def, `break` and `continue` the nearest loop, through blocks - and `continue`, never named by the draft (Qwen) |
| H4 | an endless generator hangs a buffered function pipeline | Grok, DeepSeek, ChatGPT | the draft allowed buffering | held: function stages must stream - how is the runtime prompt's question |
| H5 | `(( ))` given text, and kinds | Grok, DeepSeek, ChatGPT, Qwen | rule 7 and G8 left both open | held: kinds kept apart; `(( ))` takes numbers and text that reads exactly as one |
| H6 | `[ -d $d ]` against lists | all five | rule 11 makes a list first word an error - loud, as DeepSeek, ChatGPT and Qwen read it | held as a diagnostic: the error says `test` |
| H7 | a failing program in a capture (G3) | split: Grok, ChatGPT, Qwen keep the output and set the status; DeepSeek, Gemini make it an error | Elvish raises on every failing program; a user named that his reason not to use it, and its maintainers answered with a grep wrapper tolerating exit 1 (elvish issue 497) - our `grep -c` | held, as the three say: output kept, `status` set, `strict` stops unless tested |
| H8 | missing basics: comments, escapes, line continuation; `export`; how a function reads its value input; where `if`'s condition ends | ChatGPT; `continue` from Qwen | none in the draft | held |
| H9 | objects suffice for everyday scripts; users would miss first delegation and an implicit `self` or method syntax, then identity, equality, printing | all five; the last from ChatGPT, introspection from DeepSeek | questions for evidence | held - the objects prompt's to weigh |

## What did not hold

- Gemini: the rule numbers (lists are rule 5, captures rule 2); `[ -d /tmp ]` as a silent wrong
  result - rule 11 makes it an error; "`$obj[method] $obj`" - the draft passes no object, methods
  close over `self`; its G8 reads two ways.
- Grok's third finding - a computed key, `$m[$k]` - finds nothing: its fix is the draft's rule; its
  G8, "non-empty text is true", goes against rule 11.
- DeepSeek: "3 3 3" - over `range 3` the shared variable ends at 2, as the others say; its claim
  that Elvish's `return` is caught only by `fn` was not confirmed here (H3 stands on Ruby).
- ChatGPT: `PATH /tmp` is no command in the draft (`set PATH /tmp`) - its point, no `export`, held.
- Qwen: its Elvish link (elv.sh/ref/pipelines.html) unchecked; a `.{...}` map literal not needed.

## Ranked

1. ChatGPT - the most findings, the missing basics, and the three contracts to settle first: value
and byte output, control flow through blocks, conversion at the edge. 2. DeepSeek - reads the rules
right, kinds from A.4; small slips. 3. Qwen - `continue`, a split count, `[` read right. 4. Grok -
sound, one non-finding. 5. Gemini - wrong rule numbers, a loud error called silent.

## Adopted - C.1, nothing built yet

Rules 2, 8, 9, 10 and 11 amended, 12 and 13 new, in docs/COMMAND-MODEL.md: captures take value
output only, one value or several; a failing command keeps its output and sets `status`, `strict`
stopping it unless tested; function stages stream; a fresh loop variable each iteration; `export`;
`return`, `break`, `continue` through blocks; a boolean first word gives its status, a list says
`test`; kinds; comments, escapes, lines, and blocks as a command's last words. The question is
answered.
