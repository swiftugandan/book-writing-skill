# The blueprint format

`STRUCTURE.md` is the book's architecture. Write it before any prose, and treat
it as the contract every later session works against.

A book is written over many sessions. Without a written architecture, chapter 9
drifts from chapter 2: the running example mutates, the audience widens, the
same idea gets introduced twice under different names. The blueprint is what
makes the book one book.

Start from `assets/STRUCTURE.template.md`.

## Required fields, in order

| Field | Purpose |
|---|---|
| Promise | One paragraph: what the reader can do afterward that they could not do before |
| Audience | Named roles, plus an explicit *not* the audience |
| Reading paths | Two or three named routes through the chapters |
| Running examples | One primary, plus variants that stress scale, regulation, or risk |
| Parts → chapters | Per chapter: driving question, beat list, field guide, worked example |
| Back matter | Appendices, glossary, notes and references, index |
| Standard chapter pattern | The beat sequence every chapter follows |
| Page budget | Per part, summing to a target total |

## The driving question

**Every chapter declares one question, and every beat in that chapter must serve
the answer.** This is the format's central constraint.

A chapter without a driving question becomes a topic dump: it accumulates
everything related to its subject, in no particular order, ending when the
author runs out of material. A chapter with one has a test for every paragraph:
does this move the reader toward the answer? A beat that fails the test is cut
or moved to the chapter whose question it actually serves.

Write the question the way a reader would ask it, not as a heading in disguise. "Why doesn't faster coding produce faster delivery?" is a question.
"Understanding delivery bottlenecks" is a topic.

If you cannot state a chapter's question in one sentence, the chapter is doing
more than one job. Split it.

## Choosing the running examples

Pick **one** primary example and start it small and under-specified: a vague
request, an ambiguous rule, a system nobody fully understands. An example that
arrives fully formed has nowhere to go, and you will need it to grow across
every chapter.

Add a variant only when it exposes something the primary structurally cannot:
regulatory constraint, organizational scale, legacy migration, or the
consequences of operational failure. Two examples that make the same point are
one example and a distraction.

## Reading paths

Name each path for the reader who takes it, and say in one sentence what that
path gives them. Paths are a promise that the book can be read in parts, so
every chapter on a path must stand up without the chapters that path skips.

## Writing the blueprint's prose

The blueprint is not scaffolding that gets thrown away. Most of it is printed.

| Blueprint field | Where it appears in the book |
|---|---|
| Promise | Preface, back cover, `{{PROMISE}}` |
| Subtitle | Title page, front cover, `{{SUBTITLE}}` |
| Reading paths | The "How to read this book" page, `{{PATH_NAME}}` and `{{PATH_DESCRIPTION}}` |
| Chapter title | Chapter opener and every running head, `{{CHAPTER_TITLE}}` |
| Driving question | The chapter deck, `{{DRIVING_QUESTION}}` |
| Audience outcomes | Back cover, `{{OUTCOME_1}}` and siblings |

So **read Part One of `references/editorial-standards.md` before writing the
blueprint**, not only before drafting a chapter. Everything there applies. A chapter
title with hype vocabulary in it repeats on every left-hand page for twelve pages.

Four traps are specific to blueprint prose, because its fields are short and
declarative in a way body prose is not:

- **The promise is not marketing copy.** It states what the reader will be able to
  do. "This comprehensive guide will transform how your team ships software" says
  nothing and uses two flagged words doing it. Name the capability.
- **The audience is a list of roles, not a false range.** "Whether you are a junior
  developer or a CTO" means everyone, which means nobody. This is why the format
  requires an explicit *not* the audience: it forces a real boundary.
- **Chapter titles describe, they do not label.** "Understanding deployment" is a
  territory. A title should tell a reader what they will be able to do, in the same
  register the chapter itself uses.
- **Beat lists are not padded to a count.** Four beats when there are four. Two when
  there are two. A chapter padded to a satisfying number has beats that fail the
  driving-question test by construction.

Audit the blueprint once it is written, the same way a chapter is audited: run
`avoid-ai-writing` in detect mode over `STRUCTURE.md`. It is far cheaper to fix a
promise now than after it has been set in a preface, a back cover, and a chapter deck.

## The page budget

The budget is not decorative. `bookkit.verify` compares measured page counts
against it and warns on drift, so a chapter that runs long surfaces as a
structural problem (usually a chapter answering two questions) rather than
being absorbed silently into a longer book.

Set budgets per part, and let individual chapters vary within them.

## Companion volumes

A companion volume is this phase run again into a subfolder: its own
`STRUCTURE.md`, its own chapters, sharing the same `assets/interior.css` so the
two volumes look like one product. Give it its own promise, its own audience,
and a table mapping "if you need X, read the other volume." Do not merge the
sources.
