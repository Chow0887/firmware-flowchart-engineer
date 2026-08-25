---
name: firmware-flowchart-engineer
description: Create, reconstruct, audit, repair, or extend editable diagrams.net/draw.io flowcharts for firmware, embedded software, assembly, state machines, calculator workflows, keypad/LCD routines, and predefined functions. Use when a user asks for professional electronic-engineering flowcharts, source-to-flowchart tracing, arrow or decision verification, multi-page hierarchy, preservation of user-edited diagrams, or editable .drawio output.
---

# Firmware Flowchart Engineer

Produce engineering documentation that is logically faithful to the implementation and remains easy to edit in diagrams.net. Treat source code and stated hardware behavior as the authority; treat screenshots and existing charts as presentation references unless the user explicitly says otherwise.

## Select the operating mode

- **Create**: derive new editable flowcharts from firmware source or a written design.
- **Reconstruct**: reproduce supplied screenshots as editable draw.io pages, then correct only confirmed errors.
- **Audit**: inspect logic, return paths, labels, arrow direction, symbols, and hierarchy without modifying files.
- **Repair**: correct a copy of an existing diagram after tracing the corresponding source behavior.
- **Expand**: add detailed predefined-function flowcharts beside or on linked pages.
- **Preserve and append**: keep every existing user-edited cell unchanged and add new material outside the occupied bounds or in new pages.

State the selected mode and the source of truth before changing a file. If preservation was requested, never silently clean up, restyle, resize, reroute, or rename existing content.

## Work from evidence

1. Inventory the provided source files, images, and draw.io files.
2. Trace the actual control flow before drawing. Follow calls, returns, jumps, fall-through paths, state changes, flags, active-low inputs, register return codes, and error exits.
3. Build a compact trace table: entry, input, predicate, branch outcomes, side effects, calls, return value, and destination.
4. Mark conflicts between the implementation, comments, screenshot, and user description. Do not invent behavior to make a chart look tidy.
5. Read [references/source-tracing.md](references/source-tracing.md) when tracing assembly, C, state machines, register return codes, or hardware I/O.

For source-dependent work, cite labels, functions, or line locations in the working notes so every important chart branch can be traced back to evidence.

## Design the hierarchy before drawing

Use separate pages when detail would obscure the parent workflow. Prefer this hierarchy:

1. Main program and state machine
2. Feature workflow
3. Input/parser routine
4. Operation dispatch
5. Normal, logic, or advanced operations
6. Shared predefined functions and hardware helpers

At the parent level, show a predefined-process symbol with the exact routine name. Add a detailed routine beside the parent chart only when the user asks for side-by-side detail and space permits; otherwise create a clearly named page and a cross-page reference.

## Draw control flow precisely

- Give each decision diamond one question or predicate.
- Label every outgoing decision branch at the diamond boundary. Use semantic labels such as `Yes/No`, `Pressed/Not pressed`, `FEh/FDh/Operator`, or actual mode values.
- Use a rectangle for processing, a predefined-process symbol for a called routine, a parallelogram for external input/output, and a terminator for entry, return, or terminal transfer.
- Distinguish **call then return** from **jump/terminal transfer**. A called routine normally rejoins its caller; a menu revert or reset may terminate the current path.
- Make loops visibly close at a named loop entry. Avoid arrows that appear to terminate in empty space.
- Show error paths and the recovery destination. Do not merge success and failure paths before their different side effects have occurred.
- Replace ambiguous words such as `Operator` with the actual condition where space permits, for example `R7 = operator key (A-D)`.
- Avoid single-letter connector labels unless they are actual keypad values or established net names.

Read [references/drawio-conventions.md](references/drawio-conventions.md) before creating or materially editing a draw.io file.

## Preserve user-approved diagrams

When the user says not to modify completed flowcharts:

1. Create a new output file; never overwrite the approved file.
2. Parse the existing draw.io XML and record the page IDs, cell IDs, geometry, styles, values, and edge terminals.
3. Add only uniquely prefixed cell IDs, such as `pfunc_...`.
4. Place additions beyond the existing occupied bounds or on new pages.
5. Do not rewrite existing cell XML merely to normalize formatting or compression.
6. After saving, compare the original cell records with the new file and confirm they are unchanged.

If preservation and a requested layout cannot both be satisfied, preserve the existing chart and explain the placement compromise.

## Build editable draw.io output

- Deliver `.drawio` XML, not a flattened screenshot.
- Prefer uncompressed diagram XML while generating and auditing; diagrams.net can open it directly and it is safer to inspect and diff.
- Use stable, descriptive page names and unique cell IDs.
- Use orthogonal connectors, explicit arrowheads, consistent routing, and sufficient spacing for later edits.
- Keep text as text and shapes as native draw.io cells.
- Set page dimensions or canvas bounds to include every appended routine.
- Use restrained engineering colors only when they encode meaning; never rely on color alone.

## Validate before delivery

Perform three passes:

1. **Semantic pass**: compare every decision and terminal path against the trace table and source.
2. **Structural pass**: run `python scripts/audit_drawio.py <file.drawio>`. Resolve every error; review warnings deliberately.
3. **Visual pass**: open or render every page at readable scale. Check overlaps, clipped text, backward arrowheads, line crossings, branch-label placement, missing returns, excessive whitespace, and alignment.

For preserved diagrams, additionally confirm that all original page/cell signatures match. Report any known ambiguity instead of presenting an assumption as verified behavior.

## Deliver the result

Provide:

- the editable `.drawio` file;
- a short summary of pages added or changed;
- the source or evidence used for logical verification;
- validation results and any unresolved ambiguity;
- a note confirming whether approved existing cells were preserved unchanged.
