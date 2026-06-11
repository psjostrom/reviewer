# Reviewer (`/reviewer:review`, alias `/r`)

Multi-agent code review with scored issues. Reviews a PR or local diff; scores every finding; then fixes directly or posts inline PR comments. Auto-detects the project (Strimma, Springa, Garmin CIQ) and adds matching domain agents.

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

- `commands/review.md` — the orchestrator (depth selection, dispatch, scoring, posting).
- `agents/*.md` — the reviewer subagents (universal + per-project domain agents for Strimma, Springa, Garmin CIQ).
