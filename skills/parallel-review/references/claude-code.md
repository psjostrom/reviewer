# Claude Code Dispatch Reference

Read this file completely only when parallel review is running in Claude Code. The shared `SKILL.md` owns triage, depth selection, synthesis, scoring, and the decision gate.

## Harness identification

You are in **Claude Code** when the user invokes `/reviewer:review` or its `/r` alias from this plugin.

Require `${CLAUDE_PLUGIN_ROOT}` for every shared-file read. Never load `skills/parallel-review/...` relative to the reviewed repository.

## Orchestrator entry

The thin command shell is `commands/review.md`. It parses Claude-specific flags, then you execute the shared workflow.

Always load shared files with `${CLAUDE_PLUGIN_ROOT}` so paths resolve from the installed plugin, not the reviewed repository:

- `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/references/claude-code.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/references/reviewer-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/references/reviewers/<role>.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/references/scoring.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/references/github-actions.md`

## Argument parsing (Claude-specific)

Parse `$ARGUMENTS` before shared workflow steps:

- `--opus` → subagent model **opus** (explicit user override only)
- `--deep` / `--quick` → depth overrides (`--deep` wins if both are present)
- Remove recognized flags; pass the remainder to shared input parsing as PR number/URL, branch/base comparison, or empty for local/current PR discovery

### Child model floor (required)

| Role class | Default child model | Override |
| --- | --- | --- |
| All selected specialist reviewers | **sonnet** | **opus** only when `--opus` is present |

Do not run specialist reviewers on Opus/frontier models unless the user passed `--opus`. Orchestrator cost trimming (for example launching with Sonnet) must not be undone by spawning Opus children by default.

## Spawn children

Dispatch via Claude Code's `Agent` tool with `subagent_type` values from this table.

**Prompt transport:** pass orchestration context only (mode/target, summary, tiered file list, guidance, patch or retrieval instructions). Each specialist shell loads the contract and role via `${CLAUDE_PLUGIN_ROOT}` — do not inline those bodies into the Agent prompt.

| Role | `subagent_type` | Shared prompt |
| --- | --- | --- |
| Bug Hunter | `reviewer:bug-hunter` | `bug-hunter.md` |
| Guidelines | `reviewer:guidelines` | `guidelines.md` |
| Error & Edge Cases | `reviewer:error-edges` | `error-edges.md` |
| Architecture & Quality | `reviewer:architecture` | `architecture.md` |
| Test Reviewer | `reviewer:test-reviewer` | `test-reviewer.md` |
| Strimma Coroutine & Lifecycle | `reviewer:strimma-coroutine` | `strimma-coroutine.md` |
| Strimma Medical Data Integrity | `reviewer:strimma-medical` | `strimma-medical.md` |
| Springa API Contract & Schema | `reviewer:springa-api` | `springa-api.md` |
| Springa React & Next.js Patterns | `reviewer:springa-react` | `springa-react.md` |
| Garmin/Connect IQ | `reviewer:garmin-ciq` | `garmin-ciq.md` |
| Frontload Core Correctness | `reviewer:frontload-core` | `frontload-core.md` |
| Frontload Integration & Safety | `reviewer:frontload-integration` | `frontload-integration.md` |
| Agent Plugins Surface Parity | `reviewer:agent-plugins` | `agent-plugins.md` |

Launch every selected reviewer in one parallel response. Pass the child model from the floor above (sonnet unless `--opus`).

If the `Agent` tool is unavailable, disclose that the specialist panel cannot run and ask whether to continue as a single-agent review.

## GitHub posting

After the decision gate, follow `${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/references/github-actions.md` for every posting path. Claude GitHub MCP tools may be used only as a transport that still obeys those hard rules (head SHA refresh, one comment at a time, default `COMMENT`, explicit user authorization for `APPROVE` / `REQUEST_CHANGES`, no stderr hiding, stop on first failure). MCP must not bypass the shared posting contract.
