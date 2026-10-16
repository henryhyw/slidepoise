# Automatic and gated workflows

Choose the workflow from the user's request. Do not ask users to select a mode when their instructions already make the choice clear.

## Automatic workflow

The Agent develops and reviews content, selects resources, generates designs, reconstructs and inspects the deck without routine approval pauses. Ask only when a material unresolved choice needs the user's input. Automatic work still requires intelligible writing and actual visual judgement.

## Gated workflow

When the user asks to review a stage before the next begins, that checkpoint is binding. Record the selected stage and current decision in a lightweight run note. Honour the requested gate without imposing approval on every slide or inventing a fixed sequence of additional gates.

For an intent or content gate, show enough substance to review the communication itself.

- The plain-language proposition and the reason it matters to this audience.
- Each slide's intended takeaway and the actual explanation supporting it.
- The necessary actors, actions and relationships, including why one page follows another.
- Any unresolved choice that materially changes the message.

Section names and statements about what a future slide will explain are insufficient. The user must be able to judge whether the proposed explanation is understandable. Keep draft headlines distinct from internal planning labels.

Wait for the user's explicit approval before generation or other work dependent on that content. Read-only research and source clarification can continue. Silence, elapsed time, a reviewer endorsement and a completed form are not approval. If approval covers only some pages, carry forward exactly that scope.

After approval, proceed within the agreed message. Return to the affected checkpoint when a substantive change to the argument, claim or relationship becomes necessary. Routine spelling, fitting and visual corrections do not need renewed approval unless the user requested it.

An explicit later request for automatic completion can replace the gated workflow. Preserve earlier accepted content and constraints.

## Other useful checkpoints

Offer a checkpoint when an unresolved choice would materially change audience, evidence, page count, brand identity, required assets, cost or number of creative calls. Depending on the request, this could be a style direction, a representative sample, a set of slide candidates or an identity-sensitive illustration edit. These are optional unless the user requests them.

## Records and archives

Record the actual user decision and the content or artifact it covers. An approval record establishes authorization to continue. It does not establish writing quality or visual quality. Existing `work/human-approvals.json` files may be read as legacy history. A specific filename is unnecessary.

When the user rejects a deck and asks to restart, archive the rejected work and mark earlier acceptance records as historical. Start the new content independently. Keep useful factual sources and exact assets available, while respecting exclusions on previous copy, designs and references.

The host Agent traces which downstream artifacts depend on a changed decision. Do not implement aesthetic approval or content judgement as a deterministic workflow state machine.
