---
description: INTERNAL — invoked only by the /parallel-review orchestrator. Do not invoke directly; invoke /parallel-review instead. Reviews test coverage and banned test patterns.
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
  external_directory: allow
---

Require an absolute `SHARED_ROOT=...` line from the orchestrator Task prompt. Do not rediscover the path and do not read repository-relative skill files.

Read `$SHARED_ROOT/references/reviewer-contract.md` and apply `$SHARED_ROOT/references/reviewers/test-reviewer.md` completely.

Work read-only. Return only structured findings per the contract, or exactly `No issues found`.
