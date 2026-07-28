---
description: "Review uncommitted changes or a PR — scored issues, interactive fixing or inline GitHub comments"
agent: reviewer
---

# Code Review

**Argument:** "$ARGUMENTS"

## Active harness

You are the **opencode** orchestrator for parallel review on the `reviewer` primary agent.

Resolve the shared skill root from the **global** install symlink only (never from the reviewed repository):

```bash
SHARED_ROOT=""
f="${HOME}/.config/opencode/commands/parallel-review.md"
if [ -L "$f" ]; then
  real=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$f")
  case "$real" in
    */plugins/reviewer/opencode/commands/parallel-review.md)
      candidate=$(cd "$(dirname "$real")/../../skills/parallel-review" && pwd)
      if [ -f "$candidate/SKILL.md" ] && [ -d "$candidate/references/reviewers" ]; then
        SHARED_ROOT="$candidate"
      fi
      ;;
  esac
fi
if [ -z "$SHARED_ROOT" ]; then
  echo "Could not resolve shared parallel-review skill root from ~/.config/opencode. Run ./install-opencode.sh install reviewer first." >&2
  exit 1
fi
printf 'SHARED_ROOT=%s\n' "$SHARED_ROOT"
```

Read completely, in order, using absolute paths under `$SHARED_ROOT`:

1. `$SHARED_ROOT/SKILL.md`
2. `$SHARED_ROOT/references/opencode.md`

## opencode argument parsing

Before following the shared workflow, parse `$ARGUMENTS`:

- `--opus` → remove it; opencode configures subagent models in `opencode.json`, not per-call flags
- `--deep` / `--quick` → depth overrides (`--deep` wins if both are present)
- Remove recognized flags; use the remainder for shared input parsing (PR number/URL, branch/base comparison, or empty for local/current PR)

Then execute the shared workflow end-to-end. Do not duplicate triage tables, scoring rubrics, or posting recipes here.

When dispatching specialists, include the absolute `SHARED_ROOT=<path>` line in every Task prompt so bash-denied children do not rediscover it.
