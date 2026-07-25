# `book-writing` skill — design

**Date:** 2026-07-25
**Status:** Approved for planning

## Purpose

A single Claude skill that turns a folder of raw source material into a produced book through six
phases: a structural blueprint, per-chapter typeset HTML, and a merged, verified PDF.

The skill carries **structure** (how a book is architected) and **design** (how the interior is
built and rendered). It deliberately carries **no subject matter and no prose voice** — those are
inferred from the drafts and from the user's instructions.

Distilled from [`swiftugandan/specification-driven-delivery-book`](https://github.com/swiftugandan/specification-driven-delivery-book),
which contains a working instance of this pipeline: a conference transcript (`RAW_TRANSCRIPT.md`)
became a blueprint (`BOOK_STRUCTURE.md`), an editorial rule set
(`.cursor/rules/book-editorial-standards.mdc`), 33 hand-paginated HTML files, and merged PDFs.

## Non-goals

- Reproducing any content from the source book.
- Prescribing a voice. The editorial standards constrain *rigor* (define terms on first use,
  separate reported practice from evidence), not *personality*.
- Index generation, cover art beyond a minimal template, multi-volume tooling. A companion volume
  is phase ② run again into a subfolder — documentation, not a feature.

## Packaging

Single skill at `skills/book-writing/`, using progressive disclosure. `SKILL.md` is a short router;
heavy material lives in `references/`, `assets/`, and `scripts/`, loaded only for the active phase.

```
skills/book-writing/
  SKILL.md                        router: the six phases, when to read what
  references/
    blueprint-format.md           the STRUCTURE.md contract
    chapter-pattern.md            canonical chapter beat sequence
    editorial-standards.md        voice + rigor rules; delegates to avoid-ai-writing
    interior-design.md            design tokens, core components, layout discipline
    production.md                 pagination, render, merge, verify
  assets/
    interior.css                  the shared core stylesheet
    STRUCTURE.template.md
    chapter.template.html
    front-matter.template.html
    cover.template.html
  scripts/
    paginate.py                   measure extents, write counter offsets + manifest
    render.sh                     headless Chrome, one PDF per HTML
    merge.py                      pypdf assembly in manifest order
    verify.py                     geometry + clipping + CSS-layering checks
```

No plugin or marketplace wrapper.

## Inputs and outputs

**Input:** `drafts/` at the project root. Any mix of transcripts, notes, articles, outlines,
existing prose, or reference PDFs. The skill reads whatever is there; it does not require a
particular format.

**Outputs, in a `book/` working directory:**

| Artifact | Phase |
|---|---|
| `STRUCTURE.md` | ② |
| `assets/interior.css` (project copy, tokens filled in) | ③ |
| `book/chapter-NN.html`, `front-matter.html`, `appendix-*.html` | ④ |
| `book/book.manifest.json` | ⑥ |
| `book/<title>.pdf` | ⑥ |

## The pipeline

```
drafts/ ──①──▶ STRUCTURE.md ──③──▶ interior.css + proof chapter
         intake      ②                    design
                     │                        │
                     └──────────④─────────────┴──▶ chapter-NN.html
                              draft                     │
                                                    ⑤ editorial gate
                                                        │
                                                    ⑥ paginate → render → merge → verify
```

### ① Intake

Inventory `drafts/`. Extract, into a scratch working note, the material the blueprint needs:

- The driving problem the book exists to address.
- Distinct claims, and for each: is it reported practice, established practice, evidence, or
  speculation? This classification is carried forward into the editorial standards and must
  survive into the prose.
- Stories and anecdotes usable as chapter openers.
- Candidate running examples.

Voice and subject matter are read out of the drafts at this phase. The skill supplies neither.

If `drafts/` is empty or absent, stop and say so. Do not invent source material.

### ② Blueprint → `STRUCTURE.md`

Written to the format in `references/blueprint-format.md`. Required fields, in order:

| Field | Purpose |
|---|---|
| Promise | One paragraph: what the reader can do afterward |
| Audience | Named roles, plus an explicit *not* the audience |
| Reading paths | 2–3 named routes through the chapters |
| Running examples | One primary, plus variants stressing scale, regulation, or risk |
| Parts → chapters | Per chapter: **driving question**, beat list, field guide, worked example |
| Back matter | Appendices, glossary, notes and references, index |
| Standard chapter pattern | The beat sequence every chapter follows |
| Page budget | Per part, summing to a target total |

**The driving question per chapter is mandatory.** It is the constraint that prevents a chapter
from degrading into a topic dump: every beat in the chapter must serve the answer.

The page budget is not decorative — phase ⑥ compares measured page counts against it and reports
drift, so an over-running chapter is caught as a structural problem rather than absorbed silently.

### ③ Interior design system

`references/interior-design.md` plus `assets/interior.css`.

**Tokens.** The look is parameterized at the top of the stylesheet so the system is not welded to
the source book's appearance:

```css
--page-w  --page-h  --margin      /* default 7in × 10in, .65in */
--ink  --paper  --accent          /* default: near-black, white, one restrained spot color */
--serif  --sans  --mono           /* default: Charter / Avenir Next / monospace */
```

Defaults reproduce a technical-publisher interior. Changing the six tokens retargets the whole book.

**Two-layer CSS.** Analysis of the source repo found ~25 selectors present in 20+ of its 33 files,
and 128 selectors present in only 1–2 files — and the entire style block duplicated into every
file. The skill separates these deliberately:

- **Core layer** — `assets/interior.css`, linked by every page file. Page frame (`.page`,
  `.with-head`, `.running-head`, `.page-number`, `.folio-title`), typographic scale, and the stable
  component vocabulary: `eyebrow`, `deck`, `lead`, `dropcap`, `opener-number`, `principle`, `quote`,
  `callout` (+ variants), `label`, `spec`, `artifact`, `steps`, `checklist`, `comparison-row`,
  `matrix`, `flow-box`, `columns-2`, `columns-3`, `sidebar-grid`, `small`, `micro`, `rule`,
  `accent-rule`, `signature`.
- **Chapter-local layer** — an optional `<style>` block in a single chapter file, for a diagram that
  chapter alone needs (a use-case map, a kanban board, a calendar). Must be prefixed `ch-` and must
  not redefine a core selector. `verify.py` enforces both rules.

This is the honest model of how the source book was actually built, with the duplication removed
and the ad-hoc layer given a name and a boundary.

**Layout discipline**, carried over from the source's editorial standards:

- Diagrams are functional and must read in grayscale. Never carry meaning in color alone.
- No slide-deck pages, full-page dark panels, card walls, gradients, or shadows.
- Continuous editorial rhythm: generous margins, quiet running heads, folios, captions.

### ④ Chapter drafting

One chapter at a time, blueprint → hand-paginated HTML. Beats from
`references/chapter-pattern.md`, generalized from the source book's two variants (13 beats for the
main volume, 11 for the handbook). Each beat marked **required** or **where it fits**:

1. Opening situation *(required)*
2. Chapter promise and reading time *(required)*
3. Problem and consequences *(required)*
4. Core concept in plain language *(required)*
5. Step-by-step method *(required)*
6. Primary worked example *(required)*
7. Variant example — enterprise, regulated, or at-scale *(where it fits)*
8. Failure modes and limitations *(required)*
9. Reusable field guide *(required)*
10. What to remember *(required)*
11. Questions for the reader's team *(where it fits)*
12. One action to take next *(required)*
13. Transition to the next chapter *(required)*

Pages are laid out by hand as `.page` divs. The skill's guidance covers how to break prose across
pages without orphaning a heading or splitting a worked example.

### ⑤ Editorial gate

`references/editorial-standards.md` holds the rigor rules, adapted from the source's
`book-editorial-standards.mdc`:

- Active voice, direct second person, natural contractions, calm conversational tone.
- Introduce a concrete problem or example before the abstraction.
- Short sentences, short paragraphs, precise verbs, descriptive headings.
- Define technical terms on first use; no unexplained acronyms.
- No hype, consulting jargon, slogans, inflated claims, or repetitive summary language.
- Preserve the intake classification: distinguish reported practice, interpretation, established
  practice, evidence, and speculation.
- Callouts only when useful: Tip, Note, Warning, Rule of thumb.

The mechanical AI-slop pass is delegated, not reimplemented: invoke the **`avoid-ai-writing`** skill
(installed at `~/.claude/skills/avoid-ai-writing`; upstream
[`conorbronsdon/avoid-ai-writing`](https://github.com/conorbronsdon/avoid-ai-writing)) on each
chapter before marking it done. A chapter is not complete until it has passed this gate.

### ⑥ Production

`references/production.md` plus the four scripts.

**The problem being solved.** The source book hardcodes `counter-reset: page 14`, `26`, `38`, `50`
… — a 12-page budget per chapter, assigned by hand. Two failure modes follow, and both are silent:

1. A chapter that runs to 13 pages makes every downstream folio wrong.
2. `.page { overflow: hidden }` means overset content is clipped without any error — text simply
   disappears off the bottom of a page.

**The fix.**

- `paginate.py` measures the real content extent of every `.page` in every file (headless Chrome,
  DOM measurement), writes `book.manifest.json` (file order, measured page count, start folio), and
  rewrites each file's `counter-reset` offset from measured values rather than from a guess.
- `render.sh` prints one PDF per HTML via headless Chrome.
- `merge.py` assembles in manifest order with pypdf.
- `verify.py` **hard-fails** on:
  - page geometry ≠ 504 × 720 pt (or the token-derived equivalent),
  - any `.page` whose content extent exceeds its box — the clipping check,
  - a chapter-local selector that is unprefixed or shadows a core selector,
  - folio discontinuity across the manifest.

  and **warns** on measured page count drifting from the `STRUCTURE.md` page budget.

Render and merge keep the source book's approach — headless Chrome per file, pypdf assembly. Only
the pagination and verification steps are new.

## Design rationale

**Why one skill, not three.** Design tokens, the editorial voice, and the blueprint are shared
context that all phases need. Splitting into `book-structure` / `book-chapter` / `book-production`
would force duplicating that context or cross-referencing between skills, and would give the user
three triggers to remember for what is one linear job. Progressive disclosure gets the context
economy without the fragmentation.

**Why the blueprint is a file, not a conversation.** A book is written over many sessions. The
blueprint is the durable contract between them; without it, chapter 9 drifts from chapter 2.

**Why verification is mandatory rather than advisory.** Both production failure modes are silent.
An advisory check that a tired author skips is equivalent to no check.

## Open items

None. Scope is fixed as above.
