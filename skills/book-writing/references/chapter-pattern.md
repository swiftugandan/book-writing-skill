# The chapter pattern

Every chapter follows the same beat sequence. Readers learn the rhythm within
two chapters and stop having to work out where they are; you stop having to
reinvent chapter structure fourteen times.

Beats marked **required** appear in every chapter. Beats marked **where it fits**
are omitted when the chapter does not need them — omit them cleanly rather than
padding.

`assets/chapter.template.html` carries these beats as comment markers.

## The beats

**1. Opening situation** *(required)*
A concrete scene: someone with a problem, before any abstraction. Two or three
paragraphs. *Omit it and* the chapter opens on a definition, which gives the
reader nothing to attach the definition to.

**2. Chapter promise and reading time** *(required)*
What the reader will be able to do, and how long it takes. *Omit it and* readers
cannot decide whether to read now, skim, or skip — which breaks the reading
paths the blueprint promised.

**3. Problem and consequences** *(required)*
Why the opening situation goes wrong, and what it costs. *Omit it and* the
method that follows looks like a preference rather than a fix.

**4. Core concept in plain language** *(required)*
The one idea, named and defined, before any procedure. *Omit it and* readers
follow the steps without understanding when the steps do not apply.

**5. Step-by-step method** *(required)*
The procedure, numbered, each step an action. *Omit it and* the chapter is an
essay the reader cannot act on.

**6. Primary worked example** *(required)*
The book's running example carried through the method just described. *Omit it
and* the method stays abstract; readers cannot tell whether they have done it
right.

**7. Variant example** *(where it fits)*
A second example that stresses scale, regulation, or operational risk. Include
it only when it exposes something the primary structurally cannot.

**8. Failure modes and limitations** *(required)*
Where the method breaks, and what it does not address. *Omit it and* the chapter
reads as advocacy, and readers discover the limits in production.

**9. Reusable field guide** *(required)*
A template, checklist, or worksheet the reader can lift out and use. *Omit it
and* the chapter's value expires the moment it is read.

**10. What to remember** *(required)*
Three to five points, each a claim rather than a topic. *Omit it and* readers
retain the example instead of the idea.

**11. Questions for the reader's team** *(where it fits)*
Questions that turn the chapter into a conversation at the reader's own
organization.

**12. One action to take next** *(required)*
A single concrete next step, doable this week. *Omit it and* the chapter closes
without transferring anything.

**13. Transition to the next chapter** *(required)*
One or two sentences establishing the question the next chapter answers. *Omit
it and* the parts read as an anthology rather than an argument.

## Pagination discipline

Pages are laid out by hand. Three rules:

- **Never orphan a heading** at the foot of a page. If a heading cannot carry at
  least two lines of the text beneath it, move the whole heading to the next
  page.
- **Never split a worked example** across a page break. The reader needs the
  setup and the result in view together.
- **Move a beat, do not tighten leading.** When a page is one line over, the fix
  is to move a whole element to the next page — never to compress the type. The
  interior's rhythm is the design; local exceptions to it read as errors.

`.page { overflow: hidden }` keeps the trim clean, which means overset content
disappears silently rather than raising an error. `bookkit.verify` measures every
page for exactly this reason — run it before believing a chapter is done.
