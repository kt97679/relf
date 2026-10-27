# Questions for other models (prompt 28)

Each file is one self-contained prompt: paste it whole; nothing is attached. Every premise in
them was checked against the builds of Iteration 845 first - the probes' outputs are quoted as
they ran.

| prompt | asks | suits |
|---|---|---|
| `ask-rill-syntax-review-845.md` | an adversarial review of proposal A (and A′, B): scripts that run and do the wrong thing, worst first | the strongest reasoning model at hand, in its slow ("thinking") mode; two from different makers if possible - they find different holes |
| `ask-rill-syntax-users-845.md` | six tasks written in A, A′, B, bash and Python; the first mistakes a bash user and a Python/Ruby user would make, and which a compiler could refuse | two different general models, for two views; no search needed |
| `ask-rill-syntax-grammar-845.md` | a grammar for A; every lookahead, whitespace dependence and ambiguity; twelve tricky lines parsed | a strong coding model, thinking mode |
| `ask-rill-syntax-prior-art-845.md` | what the field learned on sigils, bare words, mode switching, structured values to programs, interpolation - each claim linked, documented or anecdotal | a model with web search or a deep-research mode; its answer is only as good as its links |

Suggested order: review, users, grammar, prior art - if the first answers settle Q46, the rest
need not be sent.

## Rounds

- **846 - the review, back.** Five answers (DeepSeek, ChatGPT, Gemini, Grok, Qwen), every claim
  checked: `ask-rill-syntax-answers-845.md`, the ledger `model-usefulness.md`. Three picked A; ten
  holes held, filled as A.1.
- **847 - the users round, back.** Five answers (Gemini, Grok, Qwen, DeepSeek, ChatGPT) to the
  845 version, every claim checked: `ask-rill-syntax-users-answers-845.md`. Five mistakes that
  would run wrongly became refusals, A.2 (R12-R16). The question is answered - `-846` need not go.
- **848 - the grammar round, back.** Four answers (Gemini, DeepSeek, ChatGPT, Qwen), every claim
  checked: `ask-rill-syntax-grammar-answers-847.md`. One parser shape agreed; six gaps measured on
  rill2 and filled, A.3 (R17-R22); and a wrong premise found - rill2 does not run `$(...)` inside a
  command's words.
- **Nothing more to send.** Review, users and grammar are answered; prior art would add least.
  What is left is the owner's: Q46.

**Bringing answers back.** Paste them one at a time, saying which model wrote each. For each,
Claude says what it adds that the earlier ones did not, what is wrong, and whether the question
is answered, and logs it in `model-usefulness.md` here. Before anything is used, every claim is
checked - a claim about a script becomes a test, run; a reference is looked up - and the results
go in `ask-rill-syntax-answers-845.md`: what held, what was wrong and how it was shown, the
answers ranked, what is adopted. Nothing is adopted unchecked. (Prompt 28 names
`results/drafts/` and `results/model-usefulness.md`; this repository keeps every document under
`docs/`, so here they are `docs/asks/`.)
