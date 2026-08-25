# Draw.io Engineering Conventions

Apply these conventions consistently across every page unless the user supplies an established house style.

## Symbols

| Meaning | Native draw.io shape |
|---|---|
| Entry, return, terminal transfer | Terminator / rounded rectangle |
| Processing or assignment | Rectangle |
| Decision or multi-way predicate | Diamond |
| Called routine | Predefined process / rectangle with double side bars |
| User, keypad, LCD, file, or peripheral I/O | Parallelogram |
| Cross-page continuation | Off-page connector or named reference |
| Annotation only | Note/callout with no control-flow arrow |

Do not use an oval merely as a decorative grouping if it can be mistaken for a terminator.

## Branches and connectors

- Default direction is top to bottom; secondary branches go left or right.
- Attach each connector to a shape boundary, never its center or nearby empty space.
- Put the arrowhead at the destination.
- Label a decision branch adjacent to its first segment.
- Route orthogonally and minimize bends.
- Avoid crossing through nodes, branch labels, or other arrowheads.
- If a crossing is unavoidable, use a line jump or rearrange the layout so the paths cannot be confused.
- Use a named connector when a long return line would circle most of the page.
- Make merge points explicit. Do not let two lines merely touch visually without sharing a vertex or junction.

## Page hierarchy and naming

Use page names that communicate scope, for example:

```text
01 Main Program
02 RUN_CALCULATOR
03 READ_DECIMAL
04 Operation Dispatch
05 EXEC_NORMAL
06 Advanced Operations
07 Shared Predefined Functions
```

Use exact source routine names as the first line of predefined-process labels. Add a plain-language subtitle only when it improves readability.

## Visual system

A restrained default palette:

- Main/control flow: dark blue outline, very light blue fill
- Decisions: amber outline or pale amber fill
- I/O: teal outline or pale teal fill
- Errors: red outline or pale red fill
- Shared subroutines: purple outline or pale purple fill
- Connectors/text: near-black

Use color consistently and keep printed grayscale legible. Use one font family, consistent font sizes, and enough padding for editable text.

## Layout

- Align nodes to a grid and keep repeated branches symmetrical where logic permits.
- Reserve enough horizontal space for labels and enough vertical space for arrowheads.
- Keep titles outside the control-flow graph.
- Prefer several readable pages over one extremely tall or wide page.
- Place side-by-side predefined-function detail beyond the original chart's occupied boundary and visually separate it with a heading or light container.

## Preserve-and-append protocol

When preserving an approved chart:

1. Duplicate the source file to a new filename.
2. Record a signature for every existing cell: page ID, cell ID, parent, value, style, source, target, and geometry XML.
3. Allocate a unique prefix for all additions.
4. Append cells without reserializing or normalizing old cells when practical.
5. Expand only canvas/page bounds if necessary; disclose that metadata change.
6. Compare signatures after saving. Any changed original cell is a failure unless the user authorized that exact edit.

## Final visual checklist

- All text is readable at normal zoom.
- No clipped text or shapes.
- No arrows point backward accidentally.
- Every decision exit is labeled.
- Every call/return relationship is accurate.
- No orphan nodes or dangling connectors.
- Loopbacks clearly target the loop entry.
- Error paths show recovery or terminal behavior.
- Cross-page references have matching names.
- Page titles and routine names match the source.
- The file remains editable in diagrams.net.
