# The six archetypes

These are not a catalogue of everything drawable. They are the shapes that
recurred across a real technical book, recovered from the one-off components its
chapters accumulated. Start from the closest worked example rather than from an
empty file. Each one already passes the checker.

## Flow

`assets/examples/flow.svg`

A sequence of steps, with the branches that matter. Use it when the reader needs
to know what happens next and what happens when something goes wrong.

The exceptional path is dashed rather than coloured, so it still reads as
exceptional in print. The decision point carries a heavier stroke as well as a
lighter fill.

Not for concurrent work. Two things happening at once want lanes, and lanes want
a different drawing.

## Pipeline

`assets/examples/pipeline.svg`

Ordered stages, each with a name and the command or artifact that carries it.
Use it when the stages are things a reader will type, or when the point is that
each stage feeds the next.

A timeline is this archetype with dates on the stages. It does not need its own
drawing.

## Cycle

`assets/examples/cycle.svg`

A loop that returns to its start. Use it for a process with no terminal state.

Four steps is the practical limit. Beyond that the loop stops reading as a loop
and becomes a ring of boxes, and a flow serves better.

## Layered stack

`assets/examples/layered-stack.svg`

Responsibility bands, most exposed at the top. Use it for architecture, for
ownership, or for anything where the reader's question is "what sits on top of
what".

Anything outside the boundary is dashed. That distinction is the usual reason to
draw the diagram at all, so it must not depend on colour.

## Node map

`assets/examples/node-map.svg`

Actors on one side, capabilities on the other, lines where they meet. Use it to
show which actors reach which capabilities, and to make the crossings visible.

Capabilities are squared and heavier-stroked; actors are rounded. Shape carries
the category so the two groups stay separable in greyscale.

Not a class diagram, and not for more than roughly eight nodes. Past that the
lines cross more than they inform and the content wants a matrix.

## Annotated anatomy

`assets/examples/annotated-anatomy.svg`

An artifact reproduced with leader lines naming its parts. This is the strongest
choice when a chapter introduces a template, because the reader sees the thing
and its vocabulary at the same time.

The artifact card is unfilled, so the one filled band has no tonal competition.

## What not to draw

**Matrices stay HTML tables.** `.matrix` in `interior.css` already handles values
across two axes. A table is not a drawing, it sets better, and it stays readable
when the book is retargeted.

**Lists stay lists.** A diagram earns its place when the relationship between
things is the point. If the content is a sequence of items with no relationship
beyond order, write the list.
