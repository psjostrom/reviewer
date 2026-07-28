---
name: error-edges
description: INTERNAL — invoked only by the /reviewer:review orchestrator. Do not invoke directly; invoke /reviewer:review instead. Reviews error handling and loading/undefined state.
tools: Bash, Glob, Grep, Read
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/references/reviewer-contract.md` and apply `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/references/reviewers/error-edges.md` completely.

Work read-only. Return only structured findings per the contract, or exactly `No issues found`.
