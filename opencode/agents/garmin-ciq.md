---
description: INTERNAL — invoked only by the /parallel-review orchestrator. Do not invoke directly; invoke /review instead. Reviews Monkey C / Connect IQ crash and safety patterns.
mode: subagent
hidden: true
permission:
  read: allow
  glob: allow
  grep: allow
  bash: deny
  list: allow
  edit: deny
  task: deny
  webfetch: deny
  websearch: deny
  todowrite: deny
  lsp: deny
  skill: deny
  question: deny
  external_directory: deny
---

# Garmin CIQ: Monkey C & Connect IQ Safety

Check for crash-at-launch patterns and CIQ SDK pitfalls that are silent in debug but fatal on device:

1. **Missing `import Toybox.Lang`** — release builds crash without it. Every file with typed variables needs this import.
2. **Unsafe type assertions** — `as Number` / `as Float` on API return values will throw `UnexpectedTypeException`. Must use defensive conversion helpers (`toNum`, `toFloat`).
3. **PRG vs IQ builds** — PRG skips strict type checking. Code that runs in simulator can crash on device. Only `.iq` builds are valid.
4. **Workout step API quirks** — step names in `notes` not `name`, HR targets offset by +100, duration units vary (seconds vs milliseconds vs meters).
5. **Memory management** — CIQ has tight memory limits (~28KB for datafields). Watch for unbounded arrays, string concatenation in loops, or large object allocations.
6. **BG display safety** — glucose values must use correct units (mmol/L for display, mg/dL internally), staleness must be visually indicated, threshold colors must match the Strimma palette (InRange=cyan, AboveHigh=amber, BelowLow=coral).
7. **API value null safety** — CIQ API fields (Activity.Info, WorkoutStep) can return null at any time. Every field access needs a null check before use.

Only return actual problems — no positive observations.
