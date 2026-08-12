# Reviewer

`reviewer` runs a risk-based, multi-agent code review with scored, verified
findings. It reviews pull requests, branch comparisons, or local changes and
stays read-only until you choose what to do with the results.

The shared workflow lives in
[`skills/parallel-review/SKILL.md`](skills/parallel-review/SKILL.md). The
harness commands and agent shells only adapt that workflow to Claude Code,
Codex, Cursor, and opencode.

## When to use it

Use Reviewer when you want an independent review before merge, especially when
you want several specialist perspectives, risk-based depth, or inline GitHub
comments.

Do not use it for:

- implementing a feature from scratch;
- a factual question or diagnosis without a requested fix;
- unchanged code with no PR, branch comparison, or local changes;
- merging a pull request. Reviewer never merges.

## Invoke it

The skill is intentionally explicit: it has
`disable-model-invocation: true`, so ambient prompts do not start a review.

| Harness | Invocation | Optional controls |
| --- | --- | --- |
| Codex | `Use $parallel-review to review ...` | `quick`, `standard`, `deep`; repository-relative paths |
| Claude Code | `/reviewer:review` or `/r` | `--quick`, `--deep`, `--opus`; PR number/URL or target |
| Cursor | `use parallel-review ...` or `/parallel-review` | `--quick`, `--deep`; repository-relative paths |
| opencode | `/parallel-review` | `--quick`, `--deep`, `--opus` (model config only) |

Examples:

```text
Use $parallel-review to review PR #6 with parallel subagents.
Use $parallel-review to review the current local changes with a quick review.
Use $parallel-review to review PR #6 deeply, limited to apps/web and packages/api.
```

```text
/r 6
/r --deep 6
/r --quick
```

```text
/parallel-review 6
/parallel-review --deep
/parallel-review --quick
```

The target can be a PR number or URL, a branch/base comparison, or omitted to
review tracked and untracked local changes. If the working tree is clean,
Reviewer can inspect the current branch's open PR. If no target exists, it
stops and reports that there is nothing to review.

## Review scope

Reviewer accepts these inputs:

- a PR number or URL;
- a branch or base comparison;
- current tracked, staged, unstaged, and untracked changes;
- optional repository-relative files or directories;
- a depth override: Quick, Standard, or Deep;
- an instruction to stop after reporting findings.

Path filters apply only to changed files. Reviewer resolves them from the
repository root, rejects absolute paths and paths outside the repository,
normalizes duplicates and nested paths, then filters the patch before risk
triage and dispatch. Reviewers may inspect related unchanged code as evidence,
but findings must identify a defect in scoped changed code.

## Workflow

### 1. Resolve the review mode

Exactly one mode is selected:

| Mode | Selected when |
| --- | --- |
| PR | A PR number or URL is supplied |
| BRANCH | A branch or base comparison is supplied |
| LOCAL | No PR is supplied and tracked or untracked changes exist |
| CURRENT PR | The tree is clean and the current branch has an open PR |

Reviewer reads repository guidance for every changed file, including each
`AGENTS.md` and `CLAUDE.md` in its directory chain. In PR mode it uses the PR
head revision, not an assumed matching local checkout.

### 2. Triage risk

Each changed file gets a tier:

| Tier | Typical files |
| --- | --- |
| Critical | Core logic, security, authentication, permissions, data processing, medical/financial calculations, migrations, public APIs |
| Standard | UI, utilities, configuration, build logic, ordinary application code |
| Low | Tests, documentation, comments, generated files, lockfiles |

The review reports a one-line change summary, the selected depth, why it was
selected, the panel that ran, and how to override the depth. For diffs above
1,500 lines, reviewers focus on Critical and Standard files; only Guidelines
and role-specific test checks inspect Low-tier files.

### 3. Select depth and panel

User overrides win. Otherwise:

| Depth | Automatic trigger | Universal reviewers |
| --- | --- | --- |
| Quick | Only Low-tier files | Bug Hunter, Guidelines |
| Standard | No Critical files and fewer than 400 changed lines | Bug Hunter, Guidelines, Test Reviewer when source changed |
| Deep | Any Critical file, at least 400 changed lines, or sensitive/plugin-dispatch changes | Bug Hunter, Guidelines, Error & Edge Cases, Architecture & Quality, Test Reviewer |

Small changes are still Deep when they touch medical or glucose math,
financial logic, authentication, security boundaries, public API compatibility,
migrations, coroutine/lifecycle behavior, native Connect IQ code, plugin
packaging, install scripts, reviewer dispatch, or agent discovery.

Standard depth skips Architecture & Quality and Error & Edge Cases. Use Deep
when structural, duplication, lifecycle, or edge-state coverage matters.

Domain reviewers are detected from repository identity and root manifests, not
arbitrary changed-text mentions:

| Repository | Added domain reviewers |
| --- | --- |
| Strimma | Coroutine & Lifecycle; Medical Data Integrity |
| Springa | API Contract & Schema; React & Next.js Patterns |
| Garmin/Connect IQ | Garmin/Connect IQ |
| Frontload | Core Correctness; Integration & Safety |
| agent-plugins | Agent Plugins Surface Parity |
| Other repositories | None |

Domain reviewers run at Standard and Deep, never Quick. At Standard, Test
Reviewer runs for source/logic changes and is skipped for documentation-only,
comments-only, generated, lockfile, or test-only changes.

### 4. Dispatch read-only specialists

Reviewer loads the common contract, one prompt per selected role, and the active
harness adapter before dispatching. It launches one child per selected role in
one parallel batch. Every child receives the mode, target revision, change
summary, tiered files, repository guidance, patch or precise retrieval
instructions, and the structured findings contract.

Specialists:

- Bug Hunter — reachable behavioral defects and regressions.
- Guidelines — repository and project-rule violations.
- Error & Edge Cases — failure paths and unusual state transitions.
- Architecture & Quality — structural defects, coupling, duplication, and
  maintainability risks.
- Test Reviewer — missing or misleading coverage for changed behavior.
- Domain roles — project-specific contracts listed above.

Children are read-only. They do not edit, stage, commit, push, post comments,
approve, request changes, or merge. If a child fails, Reviewer retries that
role once with a narrower prompt and discloses missing coverage if it fails
again. If subagent tools are unavailable, Reviewer says so and asks whether to
continue as a single-agent review; it never pretends a panel ran.

### 5. Synthesize and score

The controller rejects positive observations and findings without a changed-code
location or credible causal path. It resolves line numbers against the target
patch, merges exact and semantic duplicates, preserves the strongest evidence,
and attaches a test gap to its demonstrated bug instead of creating a second
finding.

Scores are internal prioritization values shown in the report:

| Score | Meaning |
| ---: | --- |
| 0–10 | False positive, pre-existing condition, or unsupported claim |
| 11–25 | Nitpick or low-confidence concern |
| 26–50 | Real but minor issue |
| 51–75 | Moderate issue that should probably be fixed |
| 76–90 | Important verified defect or explicit guidance violation |
| 91–100 | Confirmed critical bug, security issue, corruption, data loss, or safety risk |

Critical-tier files add 10 points, capped at 100. Low-tier files subtract 10,
floored at 0. Before assigning a score above 75, the controller directly
verifies the claim against source, definitions, dependencies, tests, CI, or
repository guidance. It does not execute PR code during the initial review;
claims needing execution stay at 50 or below with the required verification
named.

The user-facing report contains:

1. a two-to-four-sentence summary;
2. an Issues table for scores above 25;
3. a Probably Fine table for scores 25 or below;
4. the decision question asking which findings to address.

Findings use this evidence shape internally:

```text
Description: what is wrong
File: repository-relative path
Code context: smallest exact changed snippet
Line: best-effort new-file line number
Reason: category tag
Suggestion: concrete fix
Evidence: execution path, contract, test, or source fact
```

If there are no findings, the specialist contract uses `No issues found` and
the synthesis reports a clean review.

## Decision gate

Initial review is read-only. If the input says `stop after reporting`, Reviewer
stops immediately after the initial report. Otherwise, Reviewer asks which
numbered findings to address. In PR mode it also asks whether to fix them
directly or post them as GitHub review comments. It does not edit, comment,
approve, request changes, commit, push, or merge before the user chooses.

### Fix selected findings

After explicit selection, the controller:

1. refreshes the PR head if applicable;
2. uses an isolated PR worktree when the current checkout is not already the
   target branch;
3. fixes only selected root causes;
4. runs proportionate checks and inspects the diff;
5. shows verification evidence.

Commit and push still require separate user authorization. Review threads are
not resolved unless explicitly requested.

### Post selected findings

GitHub inline comments must:

- use the current PR head SHA;
- be posted one at a time;
- stop on the first failure;
- anchor to current changed lines;
- use `COMMENT` by default;
- omit scores, confidence labels, and internal reviewer names.

The body-only summary review is submitted only after every selected inline
comment succeeds. Reviewer never uses posting as a path to merge.

The complete posting contract, including the `gh api` fallback, is in
[`skills/parallel-review/references/github-actions.md`](skills/parallel-review/references/github-actions.md).

## Harness behavior

### Codex

Install the local marketplace and plugin, then start a new task so the skill
list refreshes:

```sh
codex plugin marketplace add .
codex plugin add reviewer@agent-plugins
```

Invoke with `$parallel-review`. Specialist children default to
`gpt-5.6-terra` at `medium` effort. Codex inlines the complete reviewer
contract and exactly one role prompt into each child. If the live spawn schema
does not expose model/effort selectors, the controller must disclose and use
the documented inherited-controller fallback; it must not claim Terra workers
ran.

### Claude Code

Install `reviewer`, then invoke `/reviewer:review` or `/r`. Claude defaults
specialists to Sonnet; `--opus` is an explicit opt-in. `--deep` and `--quick`
override automatic depth, with `--deep` winning if both are present. Claude
loads shared files through `${CLAUDE_PLUGIN_ROOT}` and passes orchestration
context to thin specialist shells.

For cheaper launches, the existing plugin guide supports:

```sh
alias cr='claude --strict-mcp-config --model sonnet'
```

This keeps the review session MCP-free; GitHub posting uses the documented
`gh` path after the decision gate.

### Cursor

Install the local copy for development or install from the Cursor marketplace.
Invoke explicitly because ambient invocation is disabled:

```text
use parallel-review to review PR #6
/parallel-review --deep
```

Cursor dispatches general-purpose `Task` children with
`composer-2.5-fast`, inlines the common contract and role prompt, and does not
use frontier Grok for specialists. If the live schema cannot select or prove
that model, the controller must disclose the limitation.

Local iteration from this checkout:

```sh
./install-cursor.sh install reviewer
./install-cursor.sh uninstall reviewer
./install-cursor.sh list
```

Reload the Cursor window after installing or reinstalling.

### opencode

Install globally for trusted shared-skill resolution. A project install adds
project-local discovery links, but it is not sufficient by itself because the
command deliberately resolves shared files only from the trusted global
symlink:

```sh
./install-opencode.sh install reviewer
./install-opencode.sh install reviewer --project
```

Invoke `/parallel-review`. The command resolves the shared skill through the
trusted global install symlink and passes `SHARED_ROOT` to every child.
Specialist model selection belongs in `opencode.json`; Task calls do not take
per-call model overrides. The `--opus` flag is accepted for compatibility but
does not change the child model. Configure a Sonnet-class or equivalent
mid-tier model for specialist agents rather than Opus/frontier defaults.

Uninstall with the matching scope:

```sh
./install-opencode.sh uninstall reviewer
./install-opencode.sh uninstall reviewer --project
```

## Troubleshooting

| Symptom | Meaning | Action |
| --- | --- | --- |
| `Nothing to review` | No PR, comparison, local change, or current open PR exists | Supply a PR/branch or make the target change present |
| `Nothing in scope` | Path filters match no changed files | Use repository-relative paths that are part of the diff |
| Specialist panel unavailable | The harness lacks usable child dispatch | Decide whether to continue as one reviewer; do not treat it as parallel coverage |
| Standard review feels too shallow | Architecture and edge reviewers are Deep-only | Re-run with `--deep` or `deep` |
| `--opus` has no effect in opencode | opencode chooses models from `opencode.json` | Configure each specialist agent there |
| Shared files cannot be resolved in opencode | Plugin was not installed from the trusted symlink | Run `./install-opencode.sh install reviewer` |
| PR comment fails | Posting stops intentionally at first failure | Refresh the head and retry only after checking the failed request |

## Source map

- [`skills/parallel-review/SKILL.md`](skills/parallel-review/SKILL.md) — shared
  workflow, mode resolution, triage, dispatch, synthesis, and decision gate.
- [`skills/parallel-review/references/reviewer-contract.md`](skills/parallel-review/references/reviewer-contract.md)
  — read-only child contract and finding format.
- [`skills/parallel-review/references/scoring.md`](skills/parallel-review/references/scoring.md)
  — deduplication, scores, verification threshold, and report format.
- [`skills/parallel-review/references/github-actions.md`](skills/parallel-review/references/github-actions.md)
  — authorized fix and GitHub-posting actions.
- [`skills/parallel-review/references/{codex,claude-code,cursor,opencode}.md`](skills/parallel-review/references/)
  — harness dispatch, model floors, prompt transport, and fallback rules.
- [`skills/parallel-review/references/reviewers/`](skills/parallel-review/references/reviewers/)
  — sole specialist role bodies.
- `commands/`, `opencode/`, `.cursor-plugin/`, and `agents/` — discovery and
  thin harness shells; they do not replace the shared workflow.

## Validation

After changing reviewer platform files, run:

```sh
python3 plugins/reviewer/scripts/validate_codex_reviewer.py
```

If validator logic changes, also run:

```sh
python3 -m unittest plugins/reviewer/scripts/test_validate_codex_reviewer.py
```
