---
description: "Review uncommitted changes or a PR — scored issues, interactive fixing or inline GitHub comments"
argument-hint: "[PR number]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Edit", "Write", "Agent", "AskUserQuestion", "mcp__plugin_github_github__add_comment_to_pending_review", "mcp__plugin_github_github__pull_request_review_write", "mcp__plugin_github_github__pull_request_read"]
---

# Code Review

**Argument:** "$ARGUMENTS"

## Active harness

You are the **Claude Code** orchestrator for parallel review.

Read completely, in order (plugin-absolute paths):

1. `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/SKILL.md`
2. `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/references/claude-code.md`

## Claude argument parsing

Before following the shared workflow, parse `$ARGUMENTS`:

- `--opus` → subagent model **opus** (default **sonnet**)
- `--deep` / `--quick` → depth overrides (`--deep` wins if both are present)
- Remove recognized flags; use the remainder for shared input parsing (PR number/URL, branch/base comparison, or empty for local/current PR)

Then execute the shared workflow end-to-end. Do not duplicate triage tables, scoring rubrics, or posting recipes here.
