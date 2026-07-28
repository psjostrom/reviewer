# opencode Dispatch Reference

Read this file completely only when parallel review is running in opencode. The shared `SKILL.md` owns triage, depth selection, synthesis, scoring, and the decision gate.

## Harness identification

You are in **opencode** when the user invokes `/parallel-review` on the primary `reviewer` agent from this plugin.

Never load shared reviewer files relative to the reviewed repository. Resolve `$SHARED_ROOT` only from the global install symlink under `~/.config/opencode` as specified in `opencode/commands/parallel-review.md`.

## Orchestrator entry

The thin command shell is `opencode/commands/parallel-review.md`. It parses opencode-specific flags, then you execute the shared workflow.

`install-opencode.sh` symlinks `plugins/reviewer/opencode/` (including `skills` → `../skills`) into `~/.config/opencode/`. Shared files are **not** in the reviewed repository. Stop with an install instruction if `$SHARED_ROOT` cannot be resolved from the trusted global symlink.

Reviewer agent frontmatter must set `external_directory: allow` so `$SHARED_ROOT` reads succeed outside the reviewed checkout. Keep specialist `edit: deny` and other write-denials.

## Argument parsing (opencode-specific)

Parse `$ARGUMENTS` before shared workflow steps:

- `--opus` → remove from the argument string and note that opencode configures subagent models in `opencode.json`, not per-call flags (`--opus` does not change the child model here)
- `--deep` / `--quick` → depth overrides (`--deep` wins if both are present)
- Remove recognized flags; pass the remainder to shared input parsing as PR number/URL, branch/base comparison, or empty for local/current PR discovery

### Child model floor (required)

opencode Task calls do not take per-call model overrides. Configure specialist agents to a Sonnet-class (or equivalent mid-tier) model in `opencode.json`, not Opus/frontier defaults:

```json
{
  "agent": {
    "bug-hunter": { "model": "anthropic/claude-sonnet-4-20250514" },
    "guidelines": { "model": "anthropic/claude-sonnet-4-20250514" },
    "error-edges": { "model": "anthropic/claude-sonnet-4-20250514" },
    "architecture": { "model": "anthropic/claude-sonnet-4-20250514" },
    "test-reviewer": { "model": "anthropic/claude-sonnet-4-20250514" }
  }
}
```

Use the same mid-tier model for any domain reviewers you enable. Do not default specialists to Opus. Announce when child models are controlled only by `opencode.json`.

## Spawn children

Dispatch via opencode's `Task` tool with bare agent names matching `opencode/agents/<role>.md`.

**Prompt transport:** pass orchestration context only, and always include the absolute path the orchestrator already resolved:

```text
SHARED_ROOT=<absolute path from orchestrator resolution>
```

Also include mode/target, summary, tiered files, guidance, and patch or retrieval instructions. Do **not** require specialists to rediscover `$SHARED_ROOT` (most have `bash: deny`). Each specialist shell reads `$SHARED_ROOT/references/reviewer-contract.md` and `$SHARED_ROOT/references/reviewers/<role>.md` using that injected absolute path.

| Role | `subagent_type` | Shared prompt |
| --- | --- | --- |
| Bug Hunter | `bug-hunter` | `bug-hunter.md` |
| Guidelines | `guidelines` | `guidelines.md` |
| Error & Edge Cases | `error-edges` | `error-edges.md` |
| Architecture & Quality | `architecture` | `architecture.md` |
| Test Reviewer | `test-reviewer` | `test-reviewer.md` |
| Strimma Coroutine & Lifecycle | `strimma-coroutine` | `strimma-coroutine.md` |
| Strimma Medical Data Integrity | `strimma-medical` | `strimma-medical.md` |
| Springa API Contract & Schema | `springa-api` | `springa-api.md` |
| Springa React & Next.js Patterns | `springa-react` | `springa-react.md` |
| Garmin/Connect IQ | `garmin-ciq` | `garmin-ciq.md` |
| Frontload Core Correctness | `frontload-core` | `frontload-core.md` |
| Frontload Integration & Safety | `frontload-integration` | `frontload-integration.md` |
| Agent Plugins Surface Parity | `agent-plugins` | `agent-plugins.md` |

Launch every selected reviewer in one parallel batch. Do not introduce Claude plugin prefixes or Codex skill syntax into opencode dispatch.

If the `Task` tool is unavailable, disclose that the specialist panel cannot run and ask whether to continue as a single-agent review.

## GitHub posting

After the decision gate, follow `$SHARED_ROOT/references/github-actions.md` for standalone `gh api` posting.
