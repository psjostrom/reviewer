# Reviewer

Risk-based parallel code review for Claude Code, Codex, Cursor, opencode, and Antigravity.
It dispatches specialist reviewers, deduplicates findings, and keeps initial
review read-only until you select an action.

## Install and use

### Antigravity

Install directly from GitHub or local directory:

```sh
agy plugin install https://github.com/psjostrom/reviewer
# Or from local clone:
agy plugin install .
```

Invoke `/parallel-review` (or `use parallel-review`). Antigravity dispatches all 13 reviewer roles concurrently via `invoke_subagent` using Gemini Flash floor.

### Codex

Reviewer stays available through the thin Agent Plugins catalog:

```sh
codex plugin marketplace add psjostrom/agent-plugins
codex plugin add reviewer@agent-plugins
```

Start a new task, then invoke `$parallel-review`.

### Claude Code

Install from the Agent Plugins marketplace, then invoke `/reviewer:review` or
`/r`:

```sh
claude plugin marketplace add psjostrom/agent-plugins
claude plugin install reviewer@agent-plugins
```

### Cursor

The standalone [`psjostrom/reviewer`](https://github.com/psjostrom/reviewer)
Cursor marketplace listing is pending review and is not yet available to
install. After acceptance, reload Cursor and invoke:

```text
use parallel-review to review PR #6
/parallel-review --deep
```

### opencode

Global install is required. It creates trusted symlinks under
`~/.config/opencode`; `--project` adds discovery links only and does not replace
global install.

```sh
./install-opencode.sh install
./install-opencode.sh install --project
```

Invoke `/parallel-review`. Configure specialist models in `opencode.json`;
Task calls do not set models per invocation. Uninstall matching scope:

```sh
./install-opencode.sh uninstall
./install-opencode.sh uninstall --project
```

Inspect either scope with `./install-opencode.sh list [--project]`.

## Review behavior

Invoke `$parallel-review`, `/reviewer:review`, `/r`, or `/parallel-review`
depending on harness. Use `--deep` for all specialists, `--quick` for universal
reviewers only, and `stop after reporting` to prevent a follow-up action prompt.
Reviewer never edits, posts, approves, commits, pushes, or merges during initial
review.

## Migration

Old Agent Plugins checkout commands:

```sh
./install-opencode.sh install reviewer
./install-opencode.sh uninstall reviewer
```

Become:

```sh
./install-opencode.sh install
./install-opencode.sh uninstall
```

The Codex catalog route remains unchanged.

## Development

Keep all four platform surfaces aligned. Shared behavior lives in
[`skills/parallel-review/SKILL.md`](skills/parallel-review/SKILL.md); Claude and
opencode command shells stay thin. Preserve
[`opencode/skills`](opencode/skills) as a symlink to `../skills`.

Run before changes land:

```sh
python3 scripts/validate_codex_reviewer.py
python3 -m unittest scripts/test_validate_codex_reviewer.py
python3 -m json.tool plugin.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .cursor-plugin/plugin.json >/dev/null
agy plugin validate .
test -L opencode/skills
git diff --check
```

Licensed under [MIT](LICENSE).
