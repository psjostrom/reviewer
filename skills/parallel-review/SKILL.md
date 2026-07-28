---
name: parallel-review
description: Use when reviewing a pull request, branch diff, repository path, staged changes, unstaged changes, or untracked code before merge, especially when parallel specialist reviewers or scored findings are wanted.
disable-model-invocation: true
---

# Parallel Code Review

Run a risk-based code review with a right-sized panel of parallel specialist subagents. Keep review read-only until the user chooses findings to fix or post.

## Inputs

Interpret the user's prompt for:

- PR number or URL;
- branch or base comparison;
- `quick`, `standard`, or `deep` depth override;
- local/current changes when no PR is named;
- one or more optional repository-relative path filters;
- an explicit instruction to stop after reporting.

Invocation of this skill authorizes the parallel reviewer fan-out described below. If subagent tools are unavailable, disclose that the specialist panel cannot run and ask whether to continue as a single-agent review. Do not silently simulate multiple reviewers.

Resolve every relative `references/...` path below from the directory containing this `SKILL.md`.

## 1. Resolve review mode

Choose exactly one:

- **PR:** A PR number or URL was supplied.
- **BRANCH:** A branch or base comparison was supplied.
- **LOCAL:** No PR was supplied and tracked or untracked changes exist.
- **CURRENT PR:** The working tree is clean and the current branch has an open PR.

For current-branch discovery, use local `git` and `gh pr view`. If no target exists, report that there is nothing to review and stop.

## 2. Resolve optional path scope

Treat user-supplied files and directories as repository-relative path filters.

1. Resolve each path from the repository root.
2. Reject absolute paths. Reject any path that resolves outside the repository.
3. Normalize duplicate and nested filters without changing their meaning.
4. Filter the changed-file list and patch to matching changed paths before risk triage or reviewer dispatch.
5. If no changed files match the path filters, report that there is nothing in scope and stop.

Path filters restrict review targets; they do not make unchanged files reviewable. Reviewers may inspect directly related source outside the path scope as read-only evidence. Findings must identify a defect in scoped changed code.

## 3. Gather exact context

Remain read-only.

### Repository guidance

For every changed file, read every `AGENTS.md` in the directory chain from the repository root through the file's parent directory. Also read every `CLAUDE.md` in that same chain for migration compatibility. Apply guidance broad-to-narrow; nearer files override broader files. When `AGENTS.md` and `CLAUDE.md` conflict at the same scope, follow `AGENTS.md`.

### PR mode

Prefer the connected GitHub app for PR metadata, changed filenames, patch, comments, reviews, and check status. Use `gh` only for gaps such as current-branch discovery, Actions logs, exact head content, or standalone inline-comment posting.

Capture:

- base and head refs and SHAs;
- title, body, draft state, and changed-file count;
- full patch or per-file patches;
- review comments and unresolved threads;
- check status;
- total added and deleted lines.

Never read a local file as PR-head source unless the local `HEAD` equals the PR head SHA. Otherwise inspect the target revision through GitHub or `git show` when that commit is locally available.

After gathering PR metadata and patches, apply any path filters before calculating changed-file counts, risk tiers, or line totals.

### Branch mode

Resolve the requested branch and comparison base without checking either out. Use `git diff <base>...<branch>` and `git diff --stat <base>...<branch>`, adding `-- <path filters>` when filters were supplied. Stop if either revision is ambiguous or unavailable.

### Local mode

Gather tracked staged and unstaged changes without changing staging:

```bash
git diff HEAD
git diff --stat HEAD
git ls-files --others --exclude-standard
```

When path filters were supplied, add `-- <path filters>` to each command.

Read untracked files directly with bounded reads and include them in the changed-file list. Never use `git add -N`.

## 4. Triage risk

Write a one-line summary of what the change does. Assign every changed file:

| Tier | Files |
| --- | --- |
| Critical | Core logic, security, authentication, permissions, data processing, medical/financial calculations, migrations, public API contracts |
| Standard | UI, utilities, configuration, build logic, ordinary application code |
| Low | Tests, documentation, comments-only changes, generated files, lockfiles |

Count changed lines from the patch.

For diffs above 1,500 lines, announce that reviewers will focus on Critical and Standard files. Only Guidelines and role-specific test checks inspect Low-tier files.

## 5. Select depth and panel

User overrides win. Otherwise:

| Depth | Trigger | Panel |
| --- | --- | --- |
| Quick | Only Low-tier files | Bug Hunter, Guidelines |
| Standard | No Critical files and fewer than 400 changed lines | Bug Hunter, Guidelines, Test Reviewer when source changed, all matching domain reviewers |
| Deep | Any Critical file or at least 400 changed lines | All universal reviewers and all matching domain reviewers |

Treat a small diff as Deep when it touches medical/glucose math, financial logic, authentication, security boundaries, public API compatibility, coroutine/lifecycle behavior, migrations, or native Connect IQ code.
Also treat a small diff as Deep when it changes plugin packaging, install scripts, reviewer dispatch wiring, or agent discovery conventions.

Always state the selected depth, why, the panel, and how the user can override it.

### Universal reviewers

- Bug Hunter: `references/reviewers/bug-hunter.md`
- Guidelines: `references/reviewers/guidelines.md`
- Error & Edge Cases, Deep only: `references/reviewers/error-edges.md`
- Architecture & Quality, Deep only: `references/reviewers/architecture.md`
- Test Reviewer, Deep or Standard with changed source: `references/reviewers/test-reviewer.md`

### Domain reviewers

Detect domain reviewers from repository identity and project manifests, not
arbitrary changed-text mentions. Use the basename of the git repository root
(`basename "$(git rev-parse --show-toplevel)"`) plus root manifests as specified:

- **Strimma** — basename contains `Strimma` (case-sensitive contains match). Dispatch `strimma-coroutine.md` and `strimma-medical.md`.
- **Springa** — basename contains `Springa`. Dispatch `springa-api.md` and `springa-react.md`.
- **Garmin/Connect IQ** — basename contains `garmin`. Dispatch `garmin-ciq.md`.
- **Frontload** — basename is `frontload`, or a root package manifest identifies the project as `frontload`. Dispatch `frontload-core.md` and `frontload-integration.md`.
- **Agent Plugins** — basename is `agent-plugins`, or the repo contains `.agents/plugins/marketplace.json` and `plugins/reviewer/`. Dispatch `agent-plugins.md`.
- **Generic** — anything else. No domain reviewer.

Domain reviewers run at Standard and Deep, never Quick.

### Test Reviewer at Standard depth

At **Standard** depth, run Test Reviewer when any changed file is source/logic (not only tests, documentation, comments-only changes, generated files, or lockfiles). Skip Test Reviewer at Standard when the scoped diff is exclusively Low-tier files of those kinds. At **Deep**, always include Test Reviewer.

## 6. Dispatch parallel reviewers

Read `references/reviewer-contract.md` and every selected reviewer prompt before dispatch.

Identify the active harness and read the matching adapter completely:

- Codex: `references/codex.md`
- Cursor: `references/cursor.md`
- Claude Code: `references/claude-code.md`
- opencode: `references/opencode.md`

Follow that adapter for parallel child dispatch, including its **child model floor** and **prompt transport**. Shared requirements for every harness:

1. Spawn one child per selected reviewer in one parallel batch.
2. Apply the active harness adapter's required child model/effort (mid-tier workers by default — not frontier controller models) whenever the live schema allows explicit selection.
3. Deliver the complete common reviewer contract and exactly one specialist reviewer prompt by the harness transport:
   - **Codex / Cursor:** inline both into the child prompt (plus mode/target, summary, tiered files, guidance, and patch or retrieval instructions). Prefer retrieval instructions over stuffing multi-thousand-line patches into every child.
   - **Claude Code / opencode:** pass orchestration context only (mode/target, summary, tiered files, guidance, patch or retrieval instructions). The thin specialist shell loads contract + role via `${CLAUDE_PLUGIN_ROOT}` or the absolute `$SHARED_ROOT` the orchestrator injects. Do not re-inline those bodies in the child prompt.
4. Every child must still receive the review mode and target revision, the one-line change summary, changed files with risk tiers, applicable repository guidance, the relevant patch or precise read-only retrieval instructions, and a requirement to return only the structured findings contract.
5. Do not give reviewers write tasks.
6. Wait for every selected reviewer before synthesis, then close completed reviewer threads when the harness exposes that capability.
7. If one child fails, retry that role once with a narrower prompt; if it still fails, disclose the missing coverage.
8. If subagent tools are unavailable, disclose that the specialist panel cannot run and ask whether to continue as a single-agent review. Do not silently simulate multiple reviewers.

## 7. Synthesize and score

Read and follow `references/scoring.md`.

Verify all claims that could score above 75 through read-only inspection of target-revision source, applicable guidance, dependency metadata, generated definitions, existing test code, or existing CI results. Do not execute PR code during the review phase. If direct proof requires a compiler, test, build, or other executable check, keep the issue at 50 or below and state the exact verification still needed. Run executable verification only after the user explicitly authorizes it in an isolated environment that cannot modify the reviewed checkout.

## 8. Stop at the decision gate

After reporting, ask which numbered findings to address.

In PR mode also ask whether to:

- fix selected findings directly; or
- post selected findings as GitHub review comments.

Do not edit, comment, approve, request changes, commit, push, or merge before the user answers. Do not merge under any path.

If the user selects an action, read `references/github-actions.md` and follow it exactly.
