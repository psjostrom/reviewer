# Acting on Selected Findings

Load this file only after the user selects findings from the review report.

## Safety gate

- Act only on selected finding numbers.
- Never merge the pull request.
- Never include scores, confidence labels, or internal reviewer names in GitHub comments.
- Preserve unrelated working-tree and staging changes.

## Fix directly

1. Confirm the target PR head has not changed since review. If it changed, re-check each selected finding against the new head.
2. Work on the PR branch in an isolated worktree when the current checkout is not already isolated on that branch.
3. Apply the smallest fix for each selected root cause.
4. Run proportionate tests, type checks, lint, and diff checks.
5. Show the resulting diff and verification evidence.
6. Commit or push only when the user already requested it or approves that separate action.
7. Do not resolve review threads unless the user explicitly asks for thread resolution after the fix is verified.

## Post review comments

Prefer the connected GitHub app for PR metadata and thread reads. Use standalone `gh api` comment creation when individual inline-comment posting is required. MCP-based posting (when a harness exposes it) must follow the same hard rules and authorization gates below — MCP is a transport, not a bypass.

### Hard rules

1. Refresh the PR head SHA immediately before posting and pass that exact SHA as `commit_id` in every inline-comment payload.
2. Post one selected inline comment at a time.
3. Stop on the first failed comment. Do not submit the summary review after any inline failure.
4. Verify each path and new-file line against the current PR patch. Anchor comments on commentable changed lines; if a finding concerns unchanged context, attach the comment to the nearest related changed line in that file (or post prose without a suggestion) rather than an uncommentable line.
5. Use prose instead of a suggestion block when the replacement range is uncertain.
6. Never probe GitHub with test comments.
7. Submit the body-only summary review only after every selected inline comment succeeds.
8. Default the summary event to `COMMENT`. Approving, requesting changes, and resolving threads are separate mutations that require explicit user authorization.
9. Write each comment body to a temporary file created with `mktemp`. Build JSON with `jq --rawfile`; never interpolate a multiline body through shell substitution. Clean up temp files after posting.
10. Let `gh` parse its own response with `--jq '.id'`. Do not pipe GitHub response JSON to standalone `jq`, because diff hunks can contain raw control characters.
11. Do not merge stderr into stdout when capturing an ID, and do not hide stderr; failure details must remain visible.
12. Post each comment with a separate command. Do not use a shell loop or helper function that can obscure which comment failed.

### Standalone inline-comment fallback

Refresh the head SHA:

```bash
gh api "repos/<owner>/<repo>/pulls/<number>" --jq '.head.sha'
```

Write the body with `mktemp`, then post one comment:

```bash
BODY=$(mktemp)
trap 'rm -f "$BODY"' EXIT
cat > "$BODY" <<'EOF'
Description of the issue.
EOF
ID=$(
  jq -n \
    --arg commit "<head-sha>" \
    --arg path "src/file.ts" \
    --argjson line 45 \
    --rawfile body "$BODY" \
    '{commit_id:$commit, path:$path, line:$line, side:"RIGHT", body:$body}' \
  | gh api "repos/<owner>/<repo>/pulls/<number>/comments" \
      --method POST \
      --input - \
      --jq '.id'
) && test -n "$ID" && printf 'OK id=%s\n' "$ID"
```

For a multi-line range, include `start_line`, `start_side:"RIGHT"`, `line`, and `side:"RIGHT"`. If the command fails or returns no ID, stop immediately.

After every inline comment succeeds, write the summary body to a `mktemp` file and submit it:

```bash
SUMMARY=$(mktemp)
trap 'rm -f "$SUMMARY"' EXIT
cat > "$SUMMARY" <<'EOF'
Review notes on <short scope>.

Main themes:
- <plain-language theme from the posted comments>
EOF
ID=$(
  jq -n \
    --arg commit "<head-sha>" \
    --arg event "COMMENT" \
    --rawfile body "$SUMMARY" \
    '{commit_id:$commit, event:$event, body:$body}' \
  | gh api "repos/<owner>/<repo>/pulls/<number>/reviews" \
      --method POST \
      --input - \
      --jq '.id'
) && test -n "$ID" && printf 'OK review id=%s\n' "$ID"
```

### Summary review body

Write for people reading the PR on GitHub. Keep it short; the inline comments carry the detail.

- Open with what was reviewed (PR/change scope), not the skill or tool name (`parallel-review`, "Parallel review", etc.).
- Summarize the substantive themes of the **posted** comments in plain language.
- Do not refer to chat-report numbering (`findings 1–12`, "selected findings", and similar). Those numbers exist only in the orchestrator report.
- Do not add process filler ("No merge from this review", "Happy to iterate…", and similar). Omit anything that is not useful to the PR author.

### Comment body

State the defect, impact, and concrete fix. Keep the body proportional. Do not mention scores.

For a clean review, post `LGTM — no issues found.` as a `COMMENT` by default. Use `APPROVE` only when the user explicitly asks for approval. Use `REQUEST_CHANGES` only when the user explicitly asks for it and the platform permits it.

Do **not** auto-try `APPROVE` on clean reviews. Do not treat a failed `APPROVE` as permission to post a different event unless the user explicitly asked for approval and GitHub returned HTTP 422 `Can not approve your own pull request`, in which case fall back to `COMMENT` with the **exact same body** (no prefixing), keep stderr visible, and use a `mktemp` body file.
