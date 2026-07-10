---
description: "Review uncommitted changes or a PR — scored issues, interactive fixing or inline GitHub comments"
agent: reviewer
---

# Code Review

Review code changes, score every issue, and either fix locally or post as inline PR comments.

**Argument:** "$ARGUMENTS"

## Step 0: Parse Arguments

Parse `$ARGUMENTS` for flags (remove each recognized flag from the argument string):
- If it contains `--opus`, remove it from the argument string. (opencode configures subagent models per-agent in opencode.json — see the reviewer README.)
- If it contains `--deep`, force **Deep** review depth (full agent panel) in Step 4.
- If it contains `--quick`, force **Quick** review depth (minimal panel) in Step 4.
- `--deep` and `--quick` are mutually exclusive; if both are present, `--deep` wins.

The remaining argument (after removing all flags) is used in Step 1.

## Step 1: Determine Review Mode

- If the remaining argument contains a number, this is a **PR review** of that PR number.
- If the remaining argument is empty, check `git status` and `git diff`:
  - If there are uncommitted changes (staged or unstaged), this is a **local review**.
  - If the working tree is clean, check if the current branch has a PR open (`gh pr view`). If yes, treat as PR review. If no, tell the user there's nothing to review and stop.

Set the review mode: `LOCAL` or `PR`.

## Step 2: Gather Context

1. Read all CLAUDE.md and AGENTS.md files in the repo (root + any in directories touched by the changes).
2. Get the diff:
   - **LOCAL mode:** Use `git diff HEAD` to capture all tracked changes (staged and unstaged) without modifying the index. Then list untracked files with `git ls-files --others --exclude-standard` and read each one directly with the read tool. Do NOT use `git add -N` — it mutates the index.
   - **PR mode:** `gh pr diff <number>`. Also capture the PR HEAD commit SHA: `gh pr view <number> --json headRefOid -q .headRefOid` — this is needed for posting review comments later.
3. Get the list of changed files.

## Step 3: Triage the Diff

Before launching agents, understand what you're reviewing. Classify every changed file into one of these risk tiers:

| Tier | What belongs here | Why |
|------|-------------------|-----|
| **Critical** | Core logic, data processing, security, medical calculations, financial math, API contracts | Bugs here cause real harm |
| **Standard** | UI components, utilities, configuration, build files | Normal review scrutiny |
| **Low** | Tests, documentation, comments-only changes, dependency lockfiles | Review for correctness but don't hunt for design issues |

Build a one-line summary of the diff — what is this change actually doing? This summary and the tier assignments go into every agent prompt so they know where to focus.

**Large diff handling (>1500 lines):** Don't just warn — act. Tell the user: "This is a large diff (N lines). I'll focus agents on the critical-tier files first. Lower-tier files get lighter scrutiny." Then limit agent scope to critical + standard tiers. Low-tier files only get checked by the Guidelines agent.

## Step 4: Detect Project & Launch Review Agents

### Project Detection

Determine the project type from the basename of the git repository root (`basename $(git rev-parse --show-toplevel)`):

- **Strimma** — basename contains `Strimma`. Android/Kotlin CGM medical app.
- **Springa** — basename contains `Springa`. Next.js/TypeScript workout + BG system.
- **Garmin CIQ** — basename contains `garmin`. Monkey C Connect IQ apps (SugarField, SugarGraph, SugarWave, StepField, NextStepField).
- **Frontload** — basename is `frontload` or a root package manifest identifies the project as `frontload`.
- **Agent Plugins** — basename is `agent-plugins` or the repo contains `.agents/plugins/marketplace.json` and `plugins/reviewer/`.
- **Generic** — anything else. Run universal agents only.

### Select review depth (right-size the panel to risk)

The dominant cost of this command is the **number of agents** — each one independently re-reads the diff and source, so a 5-agent panel on a 200-line copy change is mostly wasted spend. Pick a depth from the Step 3 triage **before** dispatching, using the risk tiers and diff size already computed there.

| Depth | When | Agents dispatched |
| ----- | ---- | ----------------- |
| **Deep** | Any **Critical-tier** file present, OR diff ≥ 400 lines changed, OR user passed `--deep` | Full panel: all universal agents + all matching domain agents |
| **Standard** _(default)_ | No Critical-tier files and diff < 400 lines | Bug Hunter, Guidelines, Test Reviewer + **all matching domain agents**. **Skip** Architecture and Error & Edge Cases. |
| **Quick** | Diff touches **only Low-tier** files (tests, docs, comments, lockfiles), OR user passed `--quick` | Bug Hunter + Guidelines only |

Rules:

- The agents carrying the most correctness and domain value — **Bug Hunter, Guidelines, Test Reviewer, and the domain agents** — survive every non-Quick depth. Only the two generalists (**Architecture**, **Error & Edge Cases**) are dropped at Standard depth; they yield mostly structural/polish findings that are acceptable to skip on a small, low-risk diff. Be aware this is a real coverage tradeoff: duplication, over-broad abstraction, and edge-state findings come from those two.
- At **Standard** depth, skip **Test Reviewer** only when no source/logic files changed (diff is tests + docs + config only); otherwise it runs.
- **Always state the chosen depth and a one-line reason**, and how to override — e.g. _"Standard depth (no critical files, 250 lines changed): running 4 agents, skipping Architecture and Error & Edge Cases. Re-run with `--deep` for the full panel."_ This keeps the coverage tradeoff visible so the user can escalate.
- Size is a heuristic, not a rule. If the diff *looks* riskier than its size — touches medical/glucose math, financial logic, API contracts, coroutine/lifecycle, native CIQ code, plugin packaging, install scripts, or reviewer dispatch wiring — bump to **Deep** even if no file was tiered Critical.

### Agent Dispatch

**Launch the agents for the selected depth in parallel in a SINGLE response.** Each Task call uses a `subagent_type` from the tables below; the subagent's instructions are loaded automatically from its agent file. The `prompt` you pass to each agent should contain only the orchestration context:
- The diff
- The file list with risk tiers from Step 3
- The one-line diff summary
- All CLAUDE.md / AGENTS.md content

**Checklist — verify the agents for the selected depth are dispatched:**
- [ ] Agent 1 — Bug Hunter _(all depths)_
- [ ] Agent 2 — Guidelines Checker _(all depths)_
- [ ] Agent 3 — Error & Edge Cases _(Deep only)_
- [ ] Agent 4 — Architecture & Quality _(Deep only)_
- [ ] Agent 5 — Test Reviewer _(Deep + Standard-with-source)_
- [ ] Domain agents _(Deep + Standard; skipped at Quick — if detected: S1/S2 for Strimma, P1/P2 for Springa, G1 for Garmin, F1/F2 for Frontload, A1 for Agent Plugins)_

Each agent MUST return its findings as a structured list. For each issue found, include all of these on clearly labeled lines:
- **Description:** what's wrong
- **File:** file path relative to repo root
- **Code context:** quote the exact line(s) of code where the issue exists (copy-paste from the diff or file). This is more reliable than line numbers.
- **Line:** best-effort line number. If unsure, write "unknown" — the orchestrator will find it from the code context.
- **Reason:** category tag (e.g. "bug", "CLAUDE.md violation", "error handling", "style", "tests", "comments", "coroutine", "medical", "api-contract", "react", "security")
- **Suggestion:** concrete fix

If no issues are found, the agent must say "No issues found" — not return an empty list silently.

**Focusing agents:** Tell each agent the risk tiers. Agents should spend most of their effort on Critical-tier files, normal effort on Standard-tier, and only check Low-tier for their specific concern (e.g. Test Reviewer checks tests, but Bug Hunter skips test files).

---

### Universal Agents (subset by depth — see depth table above)

| Agent | subagent_type |
|-------|---------------|
| 1 — Bug Hunter | `bug-hunter` |
| 2 — Guidelines Checker | `guidelines` |
| 3 — Error & Edge Cases | `error-edges` |
| 4 — Architecture & Quality | `architecture` |
| 5 — Test Reviewer | `test-reviewer` |

### Domain Agents (based on detected project)

| Project | Agent | subagent_type |
|---------|-------|---------------|
| Strimma | S1 — Coroutine & Lifecycle | `strimma-coroutine` |
| Strimma | S2 — Medical Data Integrity | `strimma-medical` |
| Springa | P1 — API Contract & Schema | `springa-api` |
| Springa | P2 — React & Next.js Patterns | `springa-react` |
| Garmin CIQ | G1 — Monkey C & CIQ Safety | `garmin-ciq` |
| Frontload | F1 — Core Correctness | `frontload-core` |
| Frontload | F2 — Integration & Safety | `frontload-integration` |
| Agent Plugins | A1 — Surface Parity | `agent-plugins` |

## Step 5: Synthesize & Deduplicate

When all agents return, do these in order:

### 5a. Collect raw findings

List every issue from every agent. Note which agent reported it.

### 5b. Cross-reference findings

Look for connections between agent findings that tell a bigger story:
- Agent 1 found a potential null deref AND Agent 3 found missing error handling on the same code path → that's one issue, not two. Keep the more specific one.
- Agent 4 flagged a workaround AND Agent 2 found a CLAUDE.md violation for the same pattern → mention the CLAUDE.md rule in the workaround issue. One issue, stronger evidence.
- Agent 5 found missing tests for code that Agent 1 flagged as buggy → the missing test makes the bug worse. Note this in the bug's description.

### 5c. Deduplicate

Remove exact duplicates (same file + same code context + same description). Remove semantic duplicates: if two agents flagged the same underlying problem on the same code, keep the one with the clearer description and more actionable suggestion.

**Root-cause deduplication:** Multiple symptoms of the same root cause are ONE issue, not separate issues. Example: "no loading state handling" and "UI flickers when data loads" are the same root cause (missing loading state). "Complex state logic" and "race condition from async state" are the same root cause (wrong async pattern). Merge these into a single issue that describes the root cause and lists the symptoms. This prevents inflating the issue count with variations of the same problem.

### 5d. Resolve line numbers

For each issue, use the quoted code context to find the actual line number:
- **LOCAL mode:** Read the file with the read tool, search for the quoted code.
- **PR mode:** Search the diff gathered in Step 2. If the code isn't in the diff, use `git show <pr-branch>:<path>` — do NOT try to read files that only exist on the PR branch.

If an agent provided a line number, verify it matches the quoted code. If it doesn't, use the code context.

## Step 6: Score Every Issue

Score each deduplicated issue 0-100:

- **0-10**: False positive. Pre-existing issue, or doesn't stand up to scrutiny.
- **11-25**: Nitpick. Stylistic preference not backed by CLAUDE.md / AGENTS.md or clear bug evidence.
- **26-50**: Minor. Real but low-impact. Won't cause problems in practice.
- **51-75**: Moderate. Real issue that should probably be fixed. Could cause problems.
- **76-90**: Important. Verified real issue. Will impact functionality or violates explicit CLAUDE.md / AGENTS.md rule.
- **91-100**: Critical. Confirmed bug, data loss risk, or security issue.

**The "Probably Fine" bucket is valuable.** A review that pushes everything to >50 or drops to 0 is poorly calibrated. Most real reviews should have items in the 11-50 range — things worth noting but not worth blocking a PR over. If your review has zero "Probably Fine" items, reconsider whether you're inflating scores.

**Scoring adjustments based on risk tier:**
- Issues in Critical-tier files get +10 to their base score (capped at 100). A moderate bug in glucose conversion is more important than the same bug in a settings screen.
- Issues in Low-tier files get -10 from their base score (floor of 0). A nitpick in a test file is less important than the same nitpick in production code.

**Mandatory verification for scores >75:**
Any issue you're about to score above 75 MUST be verified before assigning that score. Read the actual source code (not just the diff) and confirm the claim holds. Specifically:
- **"X doesn't exist" / "will fail compilation"** — These are the most common false positives. APIs, constants, and functions change across SDK versions. If an agent claims something doesn't exist, check the actual codebase — if it compiles, the agent is wrong. Score 0.
- **"Race condition" / "null deref"** — Trace the actual execution path. Is the race reachable? Does the caller already guard against null?
- **CLAUDE.md / AGENTS.md violations** — Open the file and verify the rule is actually stated, not paraphrased from memory.

Unverified claims stay at 50 max. Only verified issues can score above 75.

To score the rest: spot-check issues that seem uncertain. Trust clear-cut agent findings (obvious bugs, explicit rule quotes) and verify only ambiguous ones.

**How to verify source code:**
- **LOCAL mode:** Read the file directly with the read tool.
- **PR mode:** The changed files may not exist on your current branch. Use `git show <pr-branch>:<path>` or look at the diff context already gathered in Step 2. Do NOT try to read files that only exist on the PR branch — it will fail or show the wrong version.

## Step 7: Print Results

**Do NOT include raw agent findings in the output.** The agent dispatch, raw findings, cross-referencing, and deduplication are internal orchestrator work. The user only sees the final scored results below.

Start with a brief summary of the changes, then the issue tables.

**Summary (always print first):**

```
## Summary

<2-4 sentences: what this change does, which areas of the codebase it touches, and any notable design choices. Not a file list — capture the intent and scope.>
```

**Issues (score > 25):**

```
## Issues (N found)

| #  | Score | File:Line | Issue | Reason |
|----|-------|-----------|-------|--------|
| 1  | 92    | Foo.kt:45 | Null deref when sensor disconnects | bug |
| 2  | 78    | Bar.kt:12 | Missing boundary check on delta | error handling |
...
```

**Probably Fine (score <= 25):**

```
## Probably Fine (N found)

| #  | Score | File:Line | Issue | Reason |
|----|-------|-----------|-------|--------|
| 5  | 18    | Foo.kt:50 | Naming convention nitpick | style |
...
```

If there are zero issues in a category, say so: "No issues found" / "No low-confidence items".

Number all issues sequentially across both tables.

## Step 8: Ask What To Do

Ask the user:

```
Which issues should I address? (e.g. "1,2,3" or "all >50" or "none")
```

In **PR mode**, also ask whether to **fix directly** or **post as review comments**. Fixing directly means checking out the PR branch, editing the files, and pushing — this is faster when reviewing your own PR. Example prompt:

```
Fix directly or post as review comments? (fix/comment)
```

Wait for the user's response. Do not proceed until they answer.

## Step 9: Act on Selected Issues

### LOCAL mode — Fix directly

For each selected issue:
1. Read the file at the issue location.
2. Apply the fix using the edit tool.
3. Briefly state what was changed.

After all fixes, show a summary of what was changed.

### PR mode — Fix directly (if user chose "fix")

1. Fetch and check out the PR branch: `gh pr checkout <number>`.
2. For each selected issue, read the file and apply the fix using the edit tool.
3. After all fixes, show a summary of what was changed.
4. Resolve any review threads whose issues were fixed. For each fixed issue, find the matching review thread and resolve it:
   ```bash
   # Get thread IDs
   gh api graphql -f query='query { repository(owner:"OWNER", name:"REPO") { pullRequest(number:N) { reviewThreads(first:50) { nodes { id isResolved comments(first:1) { nodes { body path line } } } } } } }'
   # Resolve each thread that matches a fixed issue (by file path + code context)
   gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "THREAD_ID"}) { thread { isResolved } } }'
   ```
5. Ask the user if they want to commit and push the fixes to the PR branch.

### PR mode — Post inline review comments

**HARD RULES — these are non-negotiable. Every recipe below was verified end-to-end against a real PR; deviating reintroduces the failure modes they prevent.**

1. **NO SCORES IN COMMENTS.** Never write scores, confidence levels, or numbers like "(82/100)" or "[72]" in PR comments. Scores are internal — the PR author must never see them.
2. **ALWAYS pass bodies via `jq --rawfile`. NEVER `--arg "$(cat ...)"` and NEVER inline multi-line strings into jq.** Reading the file into a shell variable risks ARG_MAX and loses control characters; inline newlines in jq cause parse errors. The only safe pattern: `write` the body file, then `jq -n --rawfile body /tmp/body.txt ...`.
3. **NEVER use standalone `jq` to parse `gh api` response bodies.** GitHub returns review-comment responses with raw newlines in `diff_hunk` and `body` fields (technically broken JSON). Standalone `jq` rejects it with `Invalid string: control characters from U+0000 through U+001F must be escaped`. **Use gh's built-in `--jq` filter** (e.g. `gh api ... --jq '.id'`) — gh's parser tolerates the broken JSON.
4. **NEVER use `2>&1` to capture gh output into a variable.** It mixes stderr noise with the JSON. Let stderr pass through to the terminal naturally.
5. **NEVER define a shell function for posting.** Shell-version differences (bash 3 macOS vs bash 5 vs zsh), `local` keyword behavior, and PATH inheritance have repeatedly produced "command not found: cat/jq" failures inside functions. **One bash invocation per inline comment.** No loops, no functions, no `FAILED=""` accumulator.
6. **STOP on first failure. Do NOT post the summary review if any inline comment failed.** Submitted reviews are permanent. A summary that lists "Issues not posted inline: /tmp/c1.txt" is exactly the failure mode this rule prevents. If anything fails, halt and ask the user how to proceed.
7. **VERIFY SUGGESTION LINES.** The `line` field determines which line a `suggestion` block replaces. If it points to the wrong line (e.g. function signature instead of the line with the bug), the suggestion will be destructive. When unsure, use prose.
8. **NEVER probe the API with test comments.** Posted comments cannot be deleted. Every test pollutes the PR.

**Why individual comments (not bundled in `POST /reviews`):** GitHub's review API is atomic — if you bundle N inline comments and ANY line can't resolve, ALL comments are rejected. GitHub truncates large diffs and silently drops small hunks, making line resolution unpredictable. Post each comment as a standalone `POST /pulls/{n}/comments` call.

**Posting flow — 4 steps. In order, no shortcuts:**

```
1. Refresh head SHA (defends against intervening force-pushes)
2. Post each inline comment in its own bash invocation; verify success after each
3. If ANY comment failed → STOP. Tell the user. Do NOT proceed to step 4.
4. After ALL comments succeeded → submit the body-only review
```

#### Step 1 — Refresh head SHA

```bash
gh api repos/<owner>/<repo>/pulls/<number> --jq .head.sha
```

Use this SHA for every subsequent call. If more than ~1 minute has passed, refresh again — a force-push will invalidate every comment with `commit_id is not part of the pull request`.

#### Step 2 — Post each inline comment

**Two-tool-call pattern per comment:** (1) `write` the body file, (2) `bash` the post.

Use the `write` tool for the body file (handles backticks, quotes, code fences, dollar signs, and nested fenced blocks safely):

```
write /tmp/c1.txt:
Description of the issue.

Multiline bodies with `backticks` and "quotes" are safe.

```suggestion
fixed code on the target line
```
```

Then post in a single bash call. **Single-line comment** (no `start_line`):

```bash
ID=$(jq -n \
    --arg commit "<HEAD_SHA>" \
    --arg path "src/Foo.kt" \
    --argjson line 45 \
    --rawfile body /tmp/c1.txt \
    '{commit_id:$commit, path:$path, line:$line, side:"RIGHT", body:$body}' \
  | gh api "repos/<owner>/<repo>/pulls/<number>/comments" --method POST --input - --jq '.id'
) && echo "OK id=$ID" || { echo "FAIL — see stderr above"; exit 1; }
```

**Multi-line comment** (suggestion spanning multiple lines, or prose covering a region) — add `start_line` and `start_side`:

```bash
ID=$(jq -n \
    --arg commit "<HEAD_SHA>" \
    --arg path "src/Foo.kt" \
    --argjson start_line 30 \
    --argjson line 32 \
    --rawfile body /tmp/c1.txt \
    '{commit_id:$commit, path:$path, start_line:$start_line, line:$line, start_side:"RIGHT", side:"RIGHT", body:$body}' \
  | gh api "repos/<owner>/<repo>/pulls/<number>/comments" --method POST --input - --jq '.id'
) && echo "OK id=$ID" || { echo "FAIL — see stderr above"; exit 1; }
```

**Why this success-detection pattern works:**
- On 2xx, `gh api --jq '.id'` prints the comment id (gh's internal jq tolerates GitHub's raw-newline JSON). `&& echo OK` runs.
- On 4xx/5xx, gh prints `gh: <message> (HTTP <code>)` plus the full error JSON to stderr and exits non-zero. The `--jq` filter doesn't run. `|| echo FAIL` runs.
- Exit code propagates correctly through the `jq | gh api` pipe (last command's status).
- Stderr passes to the terminal so you can see the error verbatim.

**After each post, look at the output.** If it printed `FAIL`, **STOP**. One bad line number often means the diff context shifted (force-push, stale SHA) and subsequent comments will likely fail too. Tell the user what failed and ask how to proceed.

#### Step 3 — Submit the summary review (only after all inline comments succeeded)

`write` the summary body, then post:

```bash
ID=$(jq -n \
    --arg commit "<HEAD_SHA>" \
    --arg event "COMMENT" \
    --rawfile body /tmp/review-body.txt \
    '{commit_id:$commit, event:$event, body:$body}' \
  | gh api "repos/<owner>/<repo>/pulls/<number>/reviews" --method POST --input - --jq '.id'
) && echo "OK review id=$ID" || echo "FAIL — see stderr above"
```

**Event selection:**
- `"COMMENT"` — when inline comments were posted, or any non-clean review.
- `"APPROVE"` — clean review (no issues > 25). See "Clean review" below for the self-PR fallback.
- `"REQUEST_CHANGES"` — never on your own PR (HTTP 422 `Can not request changes on your own pull request`). Use `"COMMENT"` instead.

**NEVER include a "Issues not posted inline" footer.** If inline posts failed, you stopped at Step 2 per Hard Rule 6 and never reached this step.

**Comment body format:**
- Issue description in plain language
- Concrete suggestion when the fix is a simple code change (and you've verified the line is correct):
  ````
  ```suggestion
  corrected code here
  ```
  ````
- If the fix spans multiple lines, use `start_line` and `line` together
- If unsure about the exact line, describe the fix in prose — no suggestion block

**Summary tone:** Brief, proportional to severity. 1-2 sentences. Appreciative if mostly good, constructive if real problems exist.

## Notes

- Never auto-fix or auto-post without the user choosing which issues to act on.
- When in doubt about a score, round down. Better to show a low-confidence item in "Probably Fine" than to hide it.
- For PR mode, never post issues the user didn't select.
- **PR mode — clean review:** If no issues scored above 25, post a review with `"event": "APPROVE"` and a brief body like "LGTM — no issues found." If APPROVE fails (GitHub rejects approving your own PR with HTTP 422 `Can not approve your own pull request`), fall back to `"event": "COMMENT"` **with the exact same body** — do not prepend "LGTM" or any other prefix. Doing so produces double-prefixed bodies like "**LGTM** — LGTM — no issues found." Do not ask the user first; a clean review means approval.
  ```bash
  # Body file — exact same content for both APPROVE and COMMENT paths
  echo "LGTM — no issues found." > /tmp/lgtm.txt

  # Try APPROVE first
  ID=$(jq -n --arg commit "$COMMIT_SHA" --arg event "APPROVE" --rawfile body /tmp/lgtm.txt \
      '{commit_id:$commit, event:$event, body:$body}' \
    | gh api "repos/${REPO}/pulls/${PR_NUMBER}/reviews" --method POST --input - --jq '.id' 2>/dev/null)
  if [ $? -eq 0 ] && [ -n "$ID" ]; then
    echo "APPROVED id=$ID"
  else
    # Fall back to COMMENT — SAME body, no prefixing
    ID=$(jq -n --arg commit "$COMMIT_SHA" --arg event "COMMENT" --rawfile body /tmp/lgtm.txt \
        '{commit_id:$commit, event:$event, body:$body}' \
      | gh api "repos/${REPO}/pulls/${PR_NUMBER}/reviews" --method POST --input - --jq '.id'
    ) && echo "COMMENTED id=$ID" || echo "FAIL — see stderr above"
  fi
  ```
