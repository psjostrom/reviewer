# Cursor Dispatch Reference

Read this file completely only when parallel review is running in Cursor. The shared `SKILL.md` owns triage, depth selection, synthesis, scoring, and the decision gate.

## Harness identification

You are in **Cursor** when this plugin is installed under `~/.cursor/plugins/local/reviewer` (or `CURSOR_PLUGINS_LOCAL`) and the user explicitly invokes the `parallel-review` skill — for example "use parallel-review" or `/parallel-review` when Cursor surfaces the slash command. The skill sets `disable-model-invocation: true`; do not auto-invoke it from ambient chat.

## Spawn children

Cursor has no custom `reviewer:*` subagent types. Inspect the live `Task` tool schema and dispatch with the closest available general-purpose subagent type (commonly `generalPurpose`).

Conceptual shape:

```text
Task({ subagent_type, prompt, model })
```

### Child model floor (required)

Specialist reviewers are parallel, structured, read-only workers. Do **not** run them on frontier Grok (or other frontier controller models).

| Role class | Required child model | Notes |
| --- | --- | --- |
| All selected specialist reviewers | `composer-2.5-fast` | Default Cursor worker tier for this skill |

Rules:

1. When the live `Task` schema exposes `model`, pass `model: "composer-2.5-fast"` on **every** specialist child. Do not omit it and inherit the parent/controller model.
2. Never select `cursor-grok-*`, bare `grok`, Opus-class, or other frontier IDs for specialist children unless the user explicitly overrides the reviewer model for that run.
3. If the schema has no usable `model` selector, disclose that children may inherit the controller model, ask whether to continue, and do not claim Composer workers ran.
4. Never fabricate unsupported arguments.
5. Inline the complete `references/reviewer-contract.md` plus exactly one specialist prompt from `references/reviewers/<role>.md` in each child prompt, along with mode/target, summary, tiered files, guidance, and structured-findings-only requirement.
6. Prefer patch retrieval instructions (PR URL, `gh pr diff`, `git show`, or a brief on-disk patch path) over stuffing multi-thousand-line patches into every child prompt. Keep the child self-contained enough to review without the parent transcript.
7. Launch every selected reviewer in one parallel batch.
8. If `Task` or subagents are unavailable, disclose that the specialist panel cannot run and ask whether to continue as a single-agent review. Do not silently simulate multiple reviewers.
9. If one child fails, retry that role once with a narrower prompt (same Composer model); if it still fails, disclose the missing coverage.
10. Do not assume `./install-cursor.sh list` points at the checkout under review. The live install symlink may target another clone or worktree; load skill/adapter text from this skill's resolved `references/...` paths for the active review revision.

Resolve every `references/...` path from the directory containing this skill's `SKILL.md` for the revision being executed.

## Specialist roles

Load shared specialist bodies from `references/reviewers/`:

| Role | Shared prompt |
| --- | --- |
| Bug Hunter | `bug-hunter.md` |
| Guidelines | `guidelines.md` |
| Error & Edge Cases | `error-edges.md` |
| Architecture & Quality | `architecture.md` |
| Test Reviewer | `test-reviewer.md` |
| Strimma Coroutine & Lifecycle | `strimma-coroutine.md` |
| Strimma Medical Data Integrity | `strimma-medical.md` |
| Springa API Contract & Schema | `springa-api.md` |
| Springa React & Next.js Patterns | `springa-react.md` |
| Garmin/Connect IQ | `garmin-ciq.md` |
| Frontload Core Correctness | `frontload-core.md` |
| Frontload Integration & Safety | `frontload-integration.md` |
| Agent Plugins Surface Parity | `agent-plugins.md` |

## Decision gate

Follow the shared decision gate, scoring rules, and no-merge rules exactly. Act on fixes or GitHub posting only after the user selects findings and an action.
