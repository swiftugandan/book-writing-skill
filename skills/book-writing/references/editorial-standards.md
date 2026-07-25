# Editorial standards

Read this **before drafting a chapter**, not after. The rules below are generation
constraints first and an audit checklist second.

Both halves matter, and the order matters. Writing to these constraints costs
nothing; repairing prose that ignored them costs a rewrite, and a heavy rewrite
flattens whatever voice the drafts gave the book. The
[`avoid-ai-writing`](https://github.com/conorbronsdon/avoid-ai-writing) skill warns
about this directly: over-polishing pushes text toward the statistical profile of
machine writing, which is the opposite of what the pass is for. A chapter written
to these constraints needs a light audit. A chapter written blind needs surgery.

These rules constrain **rigor**, not personality. The book's voice comes from the
drafts and from what the author tells you. Nothing here prescribes a subject, a
stance, or a style of humour.

---

# Part one: write to these

## Voice

- Active voice. Direct second person. Natural contractions.
- A calm conversational tone: the register of an experienced colleague
  explaining something, not a keynote and not a manual.
- Descriptive headings. A heading should tell the reader what they are about to
  learn, not label a territory.

## Rhythm

Structure is the strongest signal that prose was generated, and it is the hardest
to repair afterwards. Get it right while drafting.

- **Vary sentence length on purpose.** Mix short sentences of three to eight words
  with long ones past twenty. Uniform sentences in the fifteen-to-twenty-five word
  band read as machine output no matter how good the vocabulary is.
- **Vary paragraph length on purpose.** Some paragraphs are one sentence. Some run
  long. If every paragraph is three to five sentences, the page reads as generated.
- **Repeat the right word.** When a noun is correct, use it three times rather than
  cycling through synonyms. Forced variation reads as thesaurus abuse.
- **Do not pad to three.** Use two items, or four, when that is what there is. The
  reflexive triad is a tell.

## Structure

- **Concrete before abstract.** Introduce a problem or an example before the
  idea that explains it. A definition with nothing attached to it does not stick.
- Show important ideas as a progression: the situation before, the decision
  made, the consequence that followed.
- Define every technical term on first use. No unexplained acronyms, ever.
- Each paragraph should depend on the one before it. If two paragraphs can swap
  places without the reader noticing, the chapter is a list of points rather than
  an argument, and the beat sequence has been filled in rather than followed.

## Do not write

- **Em dashes.** At most one per thousand words. Use a comma, a colon, a full stop,
  or two sentences. This applies to headings too. A dash in a bulleted list after a
  bolded lead term is typography and does not count.
- **Hollow intensifiers**: genuinely, truly, real, quite frankly, to be honest,
  it's worth noting that. State the fact instead.
- **Hedge stacks**: could potentially, may eventually, might ultimately. Pick one
  word or drop both.
- **Transitional throat-clearing**: Moreover, Furthermore, Additionally, In
  conclusion, When it comes to, At the end of the day. If the connection needs
  announcing, the paragraphs are in the wrong order.
- **Announced significance**: Notably, Importantly, Interestingly, Here's what's
  interesting, The real question is. Let the fact carry itself.
- **The negation pivot**: "it's not X, it's Y," including the split-sentence form.
  Write the positive claim.
- **Inflated verbs** where a plain one is true: serves as, features, boasts,
  represents. Prefer *is* and *has*.
- **Hype vocabulary**: leverage, robust, comprehensive, seamless, delve, landscape,
  paradigm, game-changer, testament to, at its core.
- No inflated claims. If the evidence supports "in the cases reported," do not
  write "always."
- No repetitive summary language. A paragraph that restates the previous paragraph
  in different words is filler and should be cut.

## Keep

Removal is half the job. A chapter that clears every pattern above and reads
sterile has failed differently.

- Fragments, where they land.
- Sentences opening with *And* or *But*.
- A stated preference or reaction where the genre carries one.
- One idea left unresolved, when it honestly is.

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
callout earns its place by holding something that interrupts the flow. A page with
three callouts has no callouts.

---

# Part two: audit what you wrote

The constraints above reduce what the audit finds. They do not replace it. Nobody
holds forty rules in mind across nine pages of prose, and the tells that survive
drafting are the ones invisible from inside the draft.

Run the audit per chapter, before the chapter is marked done.

## Step one: the pattern audit

Invoke the **`avoid-ai-writing`** skill, installed at
`~/.claude/skills/avoid-ai-writing` and upstream at
<https://github.com/conorbronsdon/avoid-ai-writing>. This skill does not
reimplement that detection.

**Run it in detect mode first**, with `technical` voice. Detect mode reports
without rewriting, which matters here: a chapter drafted to Part One should come
back nearly clean, and a blanket rewrite of prose that is already good will strip
the irregularity that makes it read as human.

Then fix the flagged spans by hand, or run edit mode scoped to those spans. Do not
rewrite passages it did not flag.

## Step two: the rigor check

A pattern detector cannot see these. Check them yourself:

- Is every technical term defined on first use?
- Does every claim still carry its evidential standing from intake?
- Does the chapter still answer its driving question, and does every beat still
  serve that answer?
- Can any two paragraphs swap places without the reader noticing?

## Step three: the mechanical check

```bash
# em dashes per thousand words
grep -o '—' chapter-NN.html | wc -l
```

Against the target of one per thousand words. This is the cheapest tell to count
and the most common one to miss.

A chapter is not complete until it has been through all three.
