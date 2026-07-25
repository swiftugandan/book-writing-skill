# Editorial standards

These rules constrain **rigor**, not personality. The book's voice comes from the
drafts and from what the author tells you. Nothing here prescribes a subject, a
stance, or a style of humour.

## Voice

- Active voice. Direct second person. Natural contractions.
- A calm conversational tone: the register of an experienced colleague
  explaining something, not a keynote and not a manual.
- Short sentences. Short paragraphs. Precise verbs.
- Descriptive headings. A heading should tell the reader what they are about to
  learn, not label a territory.

## Structure

- **Concrete before abstract.** Introduce a problem or an example before the
  idea that explains it. A definition with nothing attached to it does not stick.
- Show important ideas as a progression: the situation before, the decision
  made, the consequence that followed.
- Define every technical term on first use. No unexplained acronyms, ever.

## Prohibitions

- No hype, no slogans, no consulting jargon, no executive-report register.
- No inflated claims. If the evidence supports "in the cases reported," do not
  write "always."
- No repetitive summary language. A paragraph that restates the previous
  paragraph in different words is filler and should be cut.

## The evidence classification

Intake labels every claim as **reported practice**, **interpretation**,
**established practice**, **evidence**, or **speculation**. That distinction must
survive into the prose.

Readers cannot evaluate a claim whose standing is hidden. Attribute reported
practice to whoever reported it. Mark interpretation as yours. Cite evidence.
Flag speculation as speculation, and never let a chain of inference arrive at a
confident conclusion its weakest link cannot support.

This is the single easiest thing to lose in revision, and the most expensive to
lose.

## Callouts

Four kinds, used sparingly: **Tip**, **Note**, **Warning**, **Rule of thumb**. A
callout earns its place by holding something that interrupts the flow.
A page with three callouts has no callouts.

## The AI-slop gate

This file does not reimplement AI-writing detection. That work belongs to the
**`avoid-ai-writing`** skill, installed at `~/.claude/skills/avoid-ai-writing`
and upstream at <https://github.com/conorbronsdon/avoid-ai-writing>.

Invoke it on every chapter before marking that chapter done. It catches the
mechanical tells that survive a rigor pass because none of them is factually
wrong: the rule-of-three padding, the "it's not just X, it's Y" construction,
the hollow transitional throat-clearing, the em-dash tic.

A chapter is not complete until it has been through that gate.
