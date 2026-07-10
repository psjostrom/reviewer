# Reviewer

Multi-agent code review with scored, verified findings. The plugin supports Claude Code, Codex, and opencode.

## opencode

Run the install script from the repo root:

```sh
./install-opencode.sh install reviewer          # global (~/.config/opencode/)
./install-opencode.sh install reviewer --project # per-project (.opencode/)
```

Uninstall:

```sh
./install-opencode.sh uninstall reviewer
./install-opencode.sh uninstall reviewer --project
```

List available plugins:

```sh
./install-opencode.sh list
```

The script symlinks files from `plugins/reviewer/opencode/` into the opencode discovery directories, so edits to the source files are immediately live.

After installing, use the command:

```text
/parallel-review 123      # review PR #123
/parallel-review          # review current local diff (or the current branch's open PR)
/parallel-review --deep   # force the full agent panel
/parallel-review --quick  # force the minimal panel
```

The `/parallel-review` command runs on a custom `reviewer` primary agent (defined in `opencode/agents/reviewer.md`) that dispatches the review subagents via the Task tool, scores findings, and either fixes locally or posts inline PR comments via the `gh` CLI.

For Standard and Deep reviews, opencode auto-detects Strimma, Springa, Garmin
Connect IQ, Frontload, and agent-plugins repositories and adds the matching
domain reviewers.

**Model selection:** opencode's Task tool doesn't support per-call model overrides. To run reviewers on a specific model, set the `model` field on each review agent in your `opencode.json`:

```json
{
  "agent": {
    "bug-hunter": { "model": "anthropic/claude-opus-4-20250514" },
    "guidelines": { "model": "anthropic/claude-opus-4-20250514" }
  }
}
```

The `--opus` flag is accepted but has no effect in opencode — configure models in `opencode.json` instead.

## Codex

Install this repository as a local marketplace:

```sh
codex plugin marketplace add .
codex plugin add reviewer@agent-plugins
```

Start a new Codex thread after installation so the skill list refreshes.

Invoke the skill explicitly:

```text
Use $parallel-review to review PR #6 with parallel subagents.
Use $parallel-review to review the current local changes with a quick review.
Use $parallel-review to review local changes under src/auth.
Use $parallel-review to review PR #6 deeply, limited to apps/web and packages/api.
```

The skill reviews PRs, branch comparisons, staged/unstaged/untracked local changes, or those targets restricted to repository-relative files and directories. It chooses Quick, Standard, or Deep depth from the scoped diff risk and size. It remains read-only until it reports findings and you select which issues to fix or post as GitHub comments. It never merges a pull request.

For Standard and Deep reviews, Codex auto-detects Strimma, Springa, Garmin
Connect IQ, Frontload, and agent-plugins repositories and adds the matching
domain reviewers. Frontload reviews add separate core-correctness and
integration-safety agents.

## Claude Code

Use `/reviewer:review` or its `/r` alias.

Multi-agent code review with scored issues. Reviews a PR or local diff; scores every finding; then fixes directly or posts inline PR comments. Auto-detects the project (Strimma, Springa, Garmin CIQ, Frontload, agent-plugins) and adds matching domain agents.

```
/r <pr-number>   # review a PR
/r               # review the current local diff (or the current branch's open PR)
```

## Cost & efficiency

A full review fans out several subagents, each reasoning over the diff — so cost scales with **how many agents run** and **how much context each one carries**. The command and agents are tuned to keep both down. For the cheapest run, launch reviews with the `cr` alias (below).

### 1. Launch with the `cr` alias (recommended)

```sh
alias cr='claude --strict-mcp-config --model sonnet'
```

Then: `cr` → `/r <pr>`.

This does two things a running session can't do for itself:

- **`--strict-mcp-config` loads zero MCP servers.** A normal session injects every plugin MCP server's tool schemas (github, playwright, sentry, app-store-connect, …) plus any project `.mcp.json` into the orchestrator's context on every turn — a review uses none of them. `--strict-mcp-config` with no `--mcp-config` drops the whole surface. Posting still works: the command posts PR comments via the `gh` CLI (Bash), not via the github MCP server, so dropping MCP costs the review nothing.
- **`--model sonnet` runs the orchestrator on Sonnet** instead of Opus (~5× cheaper input). The orchestration — triage, dispatch, dedup, scoring, posting — is structured work Sonnet handles well. Use Opus only when you want maximum reviewer judgment on a high-stakes diff.

> Why not `settings.json`? Disabling MCP via `disabledMcpjsonServers` / `permissions.deny` is **session/project-wide** — it would also kill those servers for your normal sessions. The alias scopes the trim to review launches only. A skill cannot disable its own session's MCP at runtime.

### 2. Review depth scales to diff risk (automatic)

The command picks a depth from the Step 3 triage before dispatching:

| Depth | When | Agents |
| --- | --- | --- |
| **Deep** | any Critical-tier file, or ≥400 lines changed, or `--deep` | full panel (all universal + domain agents) |
| **Standard** (default) | no Critical files, <400 lines | Bug Hunter, Guidelines, Test Reviewer + domain agents (skips Architecture + Error & Edges) |
| **Quick** | only Low-tier files (tests, docs, config, lockfiles), or `--quick` | Bug Hunter + Guidelines |

Override per run:

```
/r <pr> --deep      # force the full panel (regain Architecture + Error & Edges findings)
/r <pr> --quick     # force the minimal panel
/r <pr> --opus      # run the review subagents on Opus
```

The command always announces the chosen depth and how to escalate, so the coverage tradeoff is never silent. **Standard depth drops the two generalist agents** — structural/duplication and edge-state findings come from those, so use `--deep` when you want them.

### 3. Subagents are read-only and MCP-free

Every review agent declares `tools: Bash, Glob, Grep, Read`. This prunes the entire MCP tool surface from each subagent's context (the biggest saving, since it would otherwise load once per agent) and structurally enforces that reviewers never write, fix, or post — only the orchestrator does.

## Files

- `.claude-plugin/plugin.json` — Claude Code plugin metadata.
- `commands/review.md` — Claude orchestrator.
- `agents/*.md` — Claude reviewer agents.
- `.codex-plugin/plugin.json` — Codex plugin metadata.
- `skills/parallel-review/SKILL.md` — Codex orchestrator.
- `skills/parallel-review/references/` — Codex scoring, action safety, contract, and specialist prompts.
- `scripts/validate_codex_reviewer.py` — deterministic reviewer bundle validation.
- `opencode/agents/reviewer.md` — opencode orchestrator (primary agent).
- `opencode/agents/*.md` — opencode reviewer subagents.
- `opencode/commands/parallel-review.md` — opencode orchestrator command.
