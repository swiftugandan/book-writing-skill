# {{BOOK_TITLE}}

## Working subtitle

{{SUBTITLE}}

## Promise

{{One paragraph: what the reader can do after finishing that they could not do
before. Name the outcome, not the topic.}}

## Audience

- {{Role}}
- {{Role}}
- {{Role}}

**Not the audience:** {{Who should be pointed elsewhere, and where to send them.}}

## Reading paths

**{{Path name}}:** Chapters {{list}}
{{What this path gives the reader, in one sentence.}}

**{{Path name}}:** {{Route}}
{{What this path gives the reader, in one sentence.}}

## Running examples

### Primary: {{Name}}

{{The example that recurs in every chapter. Start it small and under-specified
so it can grow across the book — an example that arrives fully formed has
nowhere to go.}}

### Variant: {{Name}}

{{An example that stresses something the primary cannot: scale, regulation,
modernization, or operational risk. Add a variant only when it exposes a real
difference.}}

---

# Part {{N}} — {{Part title}}

## Chapter {{N}}: {{Chapter title}}

**Question:** {{The single question this chapter answers. Every beat below must
serve this answer. If a beat does not, cut it or move it to another chapter.}}

- {{Beat}}
- {{Beat}}
- {{Beat}}
- {{Beat}}

**Field guide:** {{Reusable artifact the reader leaves with}}
**Primary example:** {{Slice of the running example}}
**Variant example:** {{Optional — omit if the chapter does not need one}}

## Chapter {{N}}: {{Chapter title}}

**Question:** {{...}}

- {{Beat}}
- {{Beat}}

**Field guide:** {{...}}
**Primary example:** {{...}}

---

# Back matter

## Appendix A: {{Title}}

- {{Item}}
- {{Item}}

## Glossary

{{Terms defined on first use in the body, collected here.}}

## Notes and references

- {{Sources for factual and research claims}}
- {{Attribution for reported practice, kept separate from interpretation}}

## Index

- Concepts
- Artifacts and templates
- Examples
- Risks and failure modes

---

# Standard chapter pattern

Each chapter uses this sequence. Beats marked *(where it fits)* may be omitted
when the chapter does not need them; the rest are required.

1. Opening situation
2. Chapter promise and reading time
3. Problem and consequences
4. Core concept in plain language
5. Step-by-step method
6. Primary worked example
7. Variant example *(where it fits)*
8. Failure modes and limitations
9. Reusable field guide
10. What to remember
11. Questions for the reader's team *(where it fits)*
12. One action to take next
13. Transition to the next chapter

# Page budget

- Front matter: {{N}}–{{N}} pages
- Part {{N}}: {{N}}–{{N}} pages
- Part {{N}}: {{N}}–{{N}} pages
- Back matter: {{N}}–{{N}} pages
- **Estimated total:** {{N}}–{{N}} pages

`bookkit.verify` compares measured page counts against this budget and warns on
drift, so an over-running chapter surfaces as a structural problem rather than
being absorbed silently.
