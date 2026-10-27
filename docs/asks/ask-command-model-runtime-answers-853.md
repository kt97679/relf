# Answers to the command model's runtime prompt, checked (854)

Six answers to `ask-command-model-runtime-853.md`: ChatGPT, DeepSeek, Grok, Gemini, and two from
Qwen, as the owner named them. The premises they could not see were checked in relf's own source.

## Checked in relf (no answer could)

- **The collector traces.** rill2's runtime (rill/rt.4, Iteration 776) copies everything its roots
  reach into a new arena, forwarding as it goes: cycles - the object convention's map, block, box,
  map - are reclaimed. Every answer asked for a tracing collector; it exists.
- **But it runs only between top-level statements**, and its roots are a table of registered
  variables (512 at most). Boxes, blocks, value queues and coroutine stacks are not roots; an
  endless pipeline never reaches the top level, so it would never collect; and since the collector
  moves objects, a value on a Forth stack at a safe point must be found and updated, or kept off
  the stacks there. This is the runtime's largest piece, and no answer saw it.
- **Stacks can be switched.** The kernel has `SP@ SP! RP@ RP!` - coroutines are buildable in Forth.
- **poll is there.** The C engine has a `poll` operation (engine/cv8.c) and kernel.4 `FD-POLL`.

## What held

| | finding | from | verdict |
|---|---|---|---|
| T1 | captured variables in boxes, Lua's upvalues - only what a block captures pays | DeepSeek (cells, citing Ertl and Paysan's Forth closures), Grok, Gemini, Qwen's second; ChatGPT and Qwen's first prefer heap frames | adopted: boxes; frames work too |
| T2 | function stages as coroutines, each with its own stacks and its own exception handler, values through bounded queues | ChatGPT, DeepSeek, Grok, both of Qwen's | adopted |
| T3 | programs in a pipeline: non-blocking pipes and one poll loop; drain stderr too; ignore SIGPIPE, EPIPE ending the producer quietly (`yes \| head -1`) | all six; stderr ChatGPT, SIGPIPE DeepSeek | adopted |
| T4 | `break`, `continue`, `return` carry their target's identity; a stale target is an error | ChatGPT (control records), DeepSeek (an ownership token), Gemini and Qwen's second (generation IDs) | adopted - a bare code would let a stale block, run inside another loop, break that loop |
| T5 | rule 11: names known when compiling are called directly; a value goes through one dispatch on its kind | all six | adopted |
| T6 | an order: closures and the collector, value and byte output, control transfer, coroutines, programs through poll, then measuring | ChatGPT | adopted, the collector first |

## What did not hold

- Grok and Qwen's first answer: a block that outlived its loop "has no CATCH frame", so its `break`
  reaches the top level and is an error - run inside another loop, it breaks that loop, silently.
- Gemini: pull thunks with "deadlock risk none, O(1)" - a producer written as a loop with `put`
  must first be made resumable by the compiler, which it passes over; "zero-cost" CATCH - CATCH
  saves pointers on every entry.
- Qwen's second answer: `return $x` returning a value - `return` ends with a status; values go out
  by `put`. Qwen's first: checks not in the draft's syntax (`drop m`, `1 put`).
- Not checked: DeepSeek's Ertl and Paysan cycle counts, and its embed, Atlast, BCForth references;
  ChatGPT's warning about primitives holding C-stack state across a switch - to test in the
  prototype (relf keeps both Forth stacks in VM memory).

## Ranked

1. ChatGPT - control records with identity, the poll loop with stderr, the order, the warning
about native state. 2. DeepSeek - cells, per-coroutine handlers, SIGPIPE, a box-everything
fallback. 3. Qwen's second - upvalues, generation IDs, O_NONBLOCK. 4. Grok - sound, but the stale
block wrong. 5. Gemini - thunks glossed. 6. Qwen's first - frames, the stale block wrong, checks
not in the draft's syntax.

## Adopted

The runtime plan in docs/COMMAND-MODEL.md (854). The question is answered; nothing is left to ask
of other models before a prototype.
