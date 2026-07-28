# Codex Dispatch Reference

Read this file completely only when parallel review is running in Codex. The shared `SKILL.md` owns triage, depth selection, synthesis, scoring, and the decision gate.

## Harness identification

You are in **Codex** when the active plugin exposes `$parallel-review` / the `parallel-review` skill from this plugin's `./skills/` tree.

## Spawn children

Use Codex built-in subagent dispatch. Inspect the live tool schema before calling it.

### Child model floor (required)

Specialist reviewers are parallel, structured, read-only workers. Prefer Terra over Sol.

| Role class | Required child model | Required effort |
| --- | --- | --- |
| All selected specialist reviewers | `gpt-5.6-terra` | `medium` |

Rules:

- Spawn one built-in Codex subagent per selected reviewer in one parallel batch.
- Prefer self-contained child threads without full-history inheritance (`fork_context: false` when the tool exposes that field).
- Prefer a read-oriented agent type, but never combine an explicit agent type, model, or reasoning override with a full-history fork.
- When the live spawn schema exposes `model` and `reasoning_effort` (or equivalent effort field), pass both: `gpt-5.6-terra` + `medium`. Specifying only the model is not enough.
- Do not let specialists inherit a Sol/high/max controller by omission.
- Never select `gpt-5.6-sol` (or higher effort than medium) for specialist children unless the user explicitly overrides the reviewer model for that run.
- If the schema hides model/effort selectors, disclose the limitation, ask whether to continue with inherited children, and do not claim Terra/medium workers ran.
- Never fabricate unsupported arguments.

Each child prompt must inline:

1. the complete `references/reviewer-contract.md`;
2. exactly one specialist prompt from `references/reviewers/<role>.md`;
3. review mode and target revision;
4. the one-line change summary;
5. changed files with risk tiers;
6. applicable repository guidance;
7. the relevant patch or precise read-only retrieval instructions;
8. a requirement to return only the structured findings contract.

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

## Failure handling

If subagent tools are unavailable, disclose that the specialist panel cannot run and ask whether to continue as a single-agent review.

If one child fails, retry that role once with a narrower prompt. If it still fails, disclose the missing coverage and continue synthesis with the remaining reviewers.
