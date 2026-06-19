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

Prefer the connected GitHub app for PR metadata and thread reads. Use standalone `gh api` comment creation when individual inline-comment posting is required.

### Hard rules

1. Refresh the PR head SHA immediately before posting and pass that exact SHA as `commit_id` in every inline-comment payload.
2. Post one selected inline comment at a time.
3. Stop on the first failed comment. Do not submit the summary review after any inline failure.
4. Verify each path and new-file line against the current PR patch.
5. Use prose instead of a suggestion block when the replacement range is uncertain.
6. Never probe GitHub with test comments.
7. Submit the body-only summary review only after every selected inline comment succeeds.
8. Default the summary event to `COMMENT`. Approving, requesting changes, and resolving threads are separate mutations that require explicit user authorization.
9. Write each comment body to a temporary file. Build JSON with `jq --rawfile`; never interpolate a multiline body through shell substitution.
10. Let `gh` parse its own response with `--jq '.id'`. Do not pipe GitHub response JSON to standalone `jq`, because diff hunks can contain raw control characters.
11. Do not merge stderr into stdout when capturing an ID, and do not hide stderr; failure details must remain visible.
12. Post each comment with a separate command. Do not use a shell loop or helper function that can obscure which comment failed.

### Standalone inline-comment fallback

Refresh the head SHA:

```bash
gh api "repos/<owner>/<repo>/pulls/<number>" --jq '.head.sha'
```

Write the body to `/tmp/reviewer-comment-<n>.txt`, then post one comment:

```bash
ID=$(
  jq -n \
    --arg commit "<head-sha>" \
    --arg path "src/file.ts" \
    --argjson line 45 \
    --rawfile body /tmp/reviewer-comment-1.txt \
    '{commit_id:$commit, path:$path, line:$line, side:"RIGHT", body:$body}' \
  | gh api "repos/<owner>/<repo>/pulls/<number>/comments" \
      --method POST \
      --input - \
      --jq '.id'
) && test -n "$ID" && printf 'OK id=%s\n' "$ID"
```

For a multi-line range, include `start_line`, `start_side:"RIGHT"`, `line`, and `side:"RIGHT"`. If the command fails or returns no ID, stop immediately.

After every inline comment succeeds, write the summary body to a file and submit it:

```bash
ID=$(
  jq -n \
    --arg commit "<head-sha>" \
    --arg event "COMMENT" \
    --rawfile body /tmp/reviewer-summary.txt \
    '{commit_id:$commit, event:$event, body:$body}' \
  | gh api "repos/<owner>/<repo>/pulls/<number>/reviews" \
      --method POST \
      --input - \
      --jq '.id'
) && test -n "$ID" && printf 'OK review id=%s\n' "$ID"
```

### Comment body

State the defect, impact, and concrete fix. Keep the body proportional. Do not mention scores.

For a clean review, post `LGTM — no issues found.` as a `COMMENT` by default. Use `APPROVE` only when the user explicitly asks for approval. Use `REQUEST_CHANGES` only when the user explicitly asks for it and the platform permits it.
