---
name: review-pr
description: Use when reviewing a pull request, branch diff, staged changes, unstaged changes, or untracked code before merge, especially when the user wants parallel specialist reviewers, scored findings, or GitHub review comments.
---

# Review Pull Request

Run a risk-based code review with a right-sized panel of parallel specialist subagents. Keep review read-only until the user chooses findings to fix or post.

## Inputs

Interpret the user's prompt for:

- PR number or URL;
- `quick`, `standard`, or `deep` depth override;
- local/current changes when no PR is named;
- an explicit instruction to stop after reporting.

Invocation of this skill authorizes the parallel reviewer fan-out described below. If subagent tools are unavailable, disclose that the specialist panel cannot run and ask whether to continue as a single-agent review. Do not silently simulate multiple reviewers.

## 1. Resolve review mode

Choose exactly one:

- **PR:** A PR number or URL was supplied.
- **LOCAL:** No PR was supplied and tracked or untracked changes exist.
- **CURRENT PR:** The working tree is clean and the current branch has an open PR.

For current-branch discovery, use local `git` and `gh pr view`. If no target exists, report that there is nothing to review and stop.

## 2. Gather exact context

Remain read-only.

### Repository guidance

Read the root `AGENTS.md` plus the closest applicable `AGENTS.md` for each changed file. Also read applicable `CLAUDE.md` files for migration compatibility. When they conflict, follow `AGENTS.md` for this Codex workflow.

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

### Local mode

Gather tracked staged and unstaged changes without changing staging:

```bash
git diff HEAD
git diff --stat HEAD
git ls-files --others --exclude-standard
```

Read untracked files directly with bounded reads and include them in the changed-file list. Never use `git add -N`.

## 3. Triage risk

Write a one-line summary of what the change does. Assign every changed file:

| Tier | Files |
| --- | --- |
| Critical | Core logic, security, authentication, permissions, data processing, medical/financial calculations, migrations, public API contracts |
| Standard | UI, utilities, configuration, build logic, ordinary application code |
| Low | Tests, documentation, comments-only changes, generated files, lockfiles |

Count changed lines from the patch.

For diffs above 1,500 lines, announce that reviewers will focus on Critical and Standard files. Only Guidelines and role-specific test checks inspect Low-tier files.

## 4. Select depth and panel

User overrides win. Otherwise:

| Depth | Trigger | Panel |
| --- | --- | --- |
| Quick | Only Low-tier files | Bug Hunter, Guidelines |
| Standard | No Critical files and fewer than 400 changed lines | Bug Hunter, Guidelines, Test Reviewer when source changed, all matching domain reviewers |
| Deep | Any Critical file or at least 400 changed lines | All universal reviewers and all matching domain reviewers |

Treat a small diff as Deep when it touches medical/glucose math, financial logic, authentication, security boundaries, public API compatibility, coroutine/lifecycle behavior, migrations, or native Connect IQ code.

Always state the selected depth, why, the panel, and how the user can override it.

### Universal reviewers

- Bug Hunter: `references/reviewers/bug-hunter.md`
- Guidelines: `references/reviewers/guidelines.md`
- Error & Edge Cases, Deep only: `references/reviewers/error-edges.md`
- Architecture & Quality, Deep only: `references/reviewers/architecture.md`
- Test Reviewer, Deep or Standard with changed source: `references/reviewers/test-reviewer.md`

### Domain reviewers

Detect from repository name and changed code:

- Strimma: `strimma-coroutine.md`, `strimma-medical.md`
- Springa: `springa-api.md`, `springa-react.md`
- Garmin/Connect IQ: `garmin-ciq.md`
- Generic: no domain reviewer

Domain reviewers run at Standard and Deep, never Quick.

## 5. Dispatch parallel reviewers

Read `references/reviewer-contract.md` and every selected reviewer prompt before dispatch.

Spawn one built-in Codex subagent per selected reviewer in one parallel batch. Use a read-oriented agent type when available. Each prompt must include:

1. the complete common reviewer contract;
2. exactly one specialist reviewer prompt;
3. the review mode and target revision;
4. the one-line change summary;
5. changed files with risk tiers;
6. applicable repository guidance;
7. the relevant patch, or precise instructions for retrieving target-revision source read-only;
8. a requirement to return only the structured findings contract.

Do not give reviewers write tasks. Wait for every selected reviewer before synthesis. If one fails, retry that role once with a narrower prompt; if it still fails, disclose the missing coverage.

## 6. Synthesize and score

Read and follow `references/scoring.md`.

Verify all claims that could score above 75 against target-revision source, applicable guidance, tests, or a narrow executable check. Do not let reviewer confidence substitute for evidence.

## 7. Stop at the decision gate

After reporting, ask which numbered findings to address.

In PR mode also ask whether to:

- fix selected findings directly; or
- post selected findings as GitHub review comments.

Do not edit, comment, approve, request changes, commit, push, or merge before the user answers. Do not merge under any path.

If the user selects an action, read `references/github-actions.md` and follow it exactly.
