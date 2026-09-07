# Reviewer

Reviewer runs risk-based parallel code review for pull requests, branch diffs,
repository paths, and local changes. It selects a panel of specialist agents,
deduplicates and scores their findings, verifies high-confidence claims, and
stops before making changes or posting comments.

Reviewer is an opinionated starter kit. Its universal reviewers work in any
repository, but the bundled domain specialists are written for the maintainer's
projects. Add specialists for your own architecture and risks to get the full
value from the parallel panel.

## Install

### Claude Code

```sh
claude plugin marketplace add psjostrom/agent-plugins
claude plugin install reviewer@agent-plugins
```

### Codex

```sh
codex plugin marketplace add psjostrom/agent-plugins
codex plugin add reviewer@agent-plugins
```

Start a new task after installation so Codex discovers the skill.

### Cursor

The public marketplace listing is not available. Clone this repository and load
it as a local Cursor plugin.

### OpenCode

Clone this repository first. A global install is required because the command
loads shared reviewer prompts through trusted paths under
`~/.config/opencode`. `--project` adds local discovery links but does not
replace the global install.

```sh
./install-opencode.sh install
./install-opencode.sh install --project
```

Inspect or remove matching scope with:

```sh
./install-opencode.sh list
./install-opencode.sh list --project
./install-opencode.sh uninstall
./install-opencode.sh uninstall --project
```

### Antigravity

```sh
agy plugin install https://github.com/psjostrom/reviewer
# Or from a local clone:
agy plugin install .
```

## Use

| Harness | Invocation |
| --- | --- |
| Claude Code | `/reviewer:review` |
| Codex | `$parallel-review` |
| Cursor | `/parallel-review` |
| OpenCode | `/parallel-review` |
| Antigravity | `/parallel-review` |

Examples:

```text
$parallel-review review PR #42
/reviewer:review --deep
/parallel-review review the current changes in src/api
```

Reviewer chooses `quick`, `standard`, or `deep` from the changed files and
diff size. Override it with `--quick` or `--deep`. Use `--full` to re-review the
complete target, or `--since <full SHA>` to choose an incremental baseline for
a PR or implicit branch review. `--full` and `--since` are mutually exclusive.
Add `stop after reporting` to skip the follow-up action prompt.

The first PR review is full. Later reviews default to new commits plus directly
affected callers, contracts, and tests. Local working-tree and explicit base
reviews always use their complete requested diff.

## Included reviewers

The universal panel provides broad coverage:

| Reviewer | Focus |
| --- | --- |
| Bug Hunter | Runtime behavior and correctness |
| Guidelines | Applicable `AGENTS.md` and `CLAUDE.md` rules |
| Error & Edge Cases | Loading, failure, empty, stale, and initialization states |
| Architecture & Quality | Complexity, coupling, and misleading documentation |
| Test Reviewer | Missing behavioral coverage and weak test design |

The bundled domain reviewers are examples tailored to these repositories:

| Repository family | Specialists |
| --- | --- |
| Springa | API/schema and React/Next.js |
| Springa Native | Expo/React Native UI and Springa backend integration |
| Strimma | Kotlin coroutine/lifecycle and medical data integrity |
| Garmin | Connect IQ and Monkey C safety |
| Agent plugins | Cross-harness packaging and discovery parity |

Other repositories receive the universal panel only.

## Adapt it to your repositories

Put rules every reviewer should enforce in your repository's `AGENTS.md`.
Create domain specialists when a risk deserves an independent review pass—for
example, a public API contract, billing model, device lifecycle, or safety
calculation.

For durable customization, fork Reviewer and make that fork your installed
source. For a one-machine experiment, use a local clone; do not edit a
harness-managed installation because an update can replace those files.

Each specialist has one canonical prompt under
[`skills/parallel-review/references/reviewers/`](skills/parallel-review/references/reviewers/).
Add its repository detection rule to
[`skills/parallel-review/SKILL.md`](skills/parallel-review/SKILL.md), then keep
the harness role tables and thin Claude Code/OpenCode shells aligned. The
validator reports any missing surface:

```sh
python3 scripts/validate_codex_reviewer.py
```

Copy one existing domain specialist end to end rather than inventing a second
dispatch mechanism.

## Safety and review behavior

The initial review is read-only. Reviewer never edits the reviewed checkout,
posts comments, approves, commits, pushes, or merges until it reports findings
and you select an action. It may store only the completed base/head pair in
local user state so installed harnesses on the same machine share the next
incremental baseline.

Unresolved findings are carried forward from the current conversation or PR
threads. A saved baseline never advances past findings that exist only in the
conversation.

## Development

Shared behavior lives in
[`skills/parallel-review/SKILL.md`](skills/parallel-review/SKILL.md). Claude
Code and OpenCode command shells stay thin. Preserve [`opencode/skills`](opencode/skills)
as a symlink to `../skills`.

Run before changes land:

```sh
python3 scripts/validate_codex_reviewer.py
python3 -m unittest scripts/test_validate_codex_reviewer.py scripts/test_review_state.py
python3 -m json.tool plugin.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .cursor-plugin/plugin.json >/dev/null
agy plugin validate .
test -L opencode/skills
git diff --check
```

Licensed under [MIT](LICENSE).
