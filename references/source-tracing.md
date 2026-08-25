# Firmware Source-Tracing Guide

Use this guide to turn embedded source into an evidence-backed flowchart. Record what the program does, not what a comment or an earlier chart appears to intend.

## Build the trace table

For each routine, capture:

| Field | What to record |
|---|---|
| Entry | Label/function and all callers |
| Inputs | Registers, RAM, parameters, pins, flags, global state |
| Outputs | Registers, RAM, flags, peripherals, display state |
| Decisions | Exact instruction or expression and its polarity |
| Calls | Callee and whether control returns |
| Exits | Return, jump, reset, wait loop, or state transition |
| Errors | Detection condition, indication, cleanup, recovery |

Trace all reachable exits. If a routine has multiple return codes, map every value to its meaning at both the producer and consumer.

## Assembly control-flow rules

- A label is a location, not automatically a flowchart step. Collapse straight-line implementation detail only when no externally meaningful state is lost.
- `CALL`, `LCALL`, or `ACALL` transfers to a subroutine and normally returns to the next instruction. Show a predefined process at the caller; detail the callee separately.
- `RET` returns to the caller. `RETI` also restores interrupt control; do not merge an ISR return with an ordinary return.
- An unconditional jump is a transfer, not a call. Do not draw a return arrow unless the code can return.
- Conditional jumps describe predicates whose polarity depends on the instruction. Translate the actual taken/not-taken meanings into plain branch labels.
- Fall-through is a real path. Include it even when the source lacks an explicit jump.
- Register values are context-sensitive. Trace where a return code was assigned before naming its branch.
- Stack pushes/pops matter when they preserve return values or affect nested calls. A value restored after a call may change the apparent output register.

## Active-low and hardware inputs

For active-low pins, distinguish electrical level from user action:

| Electrical test | Semantic label |
|---|---|
| Pin = 0 | Pressed / asserted |
| Pin = 1 | Released / not asserted |

Show debounce, press/release waits, and early-exit behavior if they materially affect control flow. Do not label a zero-level branch `No` merely because the bit value is zero.

## State machines

- Identify the state variable, legal values, initialization, transitions, and actions performed in each state.
- Separate event detection from state transition when both matter.
- A main-loop dispatcher should show where each branch rejoins the loop.
- If a routine changes state and then returns, show both the state update and the return.
- If a reset/revert routine never comes back to the current workflow, use a terminal transfer instead of implying a normal subroutine return.

## Input and return-code protocols

When a keypad/parser routine returns a value in a register, model it as a multi-way classification when appropriate. Example:

```text
READ_DECIMAL returns:
  FEh -> revert request
  FDh -> clear request
  00h..09h -> digit handled internally or returned digit
  A..D/# -> operator or confirmation key
```

Verify the real code before using these values. Do not put the vague label `Operator` on an edge if the branch also permits `#` or other control keys.

## Arithmetic and error paths

- Show width and signedness when they affect overflow, borrow, or range checks.
- Separate divide-by-zero, invalid input, arithmetic overflow, and display-format overflow if the firmware handles them differently.
- For subtraction, state whether the result is signed, magnitude-plus-flag, two's complement, or saturated.
- For multiplication/power, show where overflow is checked—per iteration or only at the end.
- For square root, state whether the result is exact, rounded, or floor integer root.

## Resolve conflicts

Use this priority unless the user specifies another authority:

1. Executed source behavior
2. Hardware interface definition and verified requirements
3. Tests or observed behavior
4. Current editable diagram
5. Screenshot, prose summary, or code comments

When source behavior appears defective, document both `implemented behavior` and `recommended behavior`. Do not silently draw the recommendation as though it already exists.
