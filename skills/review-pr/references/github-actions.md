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
7. Resolve an existing review thread only when its issue was actually fixed and verified.

## Post review comments

Prefer the connected GitHub app for PR metadata and thread reads. Use standalone `gh api` comment creation when individual inline-comment posting is required.

### Hard rules

1. Refresh the PR head SHA immediately before posting.
2. Post one selected inline comment at a time.
3. Stop on the first failed comment. Do not submit the summary review after any inline failure.
4. Verify each path and new-file line against the current PR patch.
5. Use prose instead of a suggestion block when the replacement range is uncertain.
6. Never probe GitHub with test comments.
7. Submit the body-only summary review only after every selected inline comment succeeds.
8. Use `COMMENT` for a non-clean self-review. Do not request changes on the author's own PR.

### Comment body

State the defect, impact, and concrete fix. Keep the body proportional. Do not mention scores.

For a clean review, try `APPROVE` with `LGTM — no issues found.` When GitHub rejects self-approval, fall back to `COMMENT` with the exact same body.
