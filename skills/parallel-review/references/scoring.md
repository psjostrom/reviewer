# Synthesis and Scoring

Use this after every selected reviewer has returned.

## Normalize

Reject positive observations and findings without a changed-code location or a credible causal path. Resolve each line number from the quoted code context against the PR patch or target revision. Never trust a supplied line number without checking it.

## Cross-reference and deduplicate

1. Collect all findings and record the reporting reviewer.
2. Merge exact duplicates.
3. Merge semantic duplicates sharing one root cause, even when reviewers describe different symptoms.
4. Preserve the strongest evidence and most actionable suggestion.
5. When a test gap corresponds to a demonstrated bug, attach the gap to the bug instead of creating a separate blocking issue.
6. When a repository-guidance violation describes the same defect as another reviewer, quote the applicable rule in the merged issue.

## Score

Assign every remaining issue a score from 0–100:

| Score | Meaning |
| --- | --- |
| 0–10 | False positive, pre-existing condition, or unsupported claim |
| 11–25 | Nitpick or low-confidence concern |
| 26–50 | Real but minor issue unlikely to cause material problems |
| 51–75 | Moderate issue that should probably be fixed |
| 76–90 | Important verified defect or explicit guidance violation |
| 91–100 | Confirmed critical bug, security issue, corruption, data-loss, or safety risk |

Adjust the base score:

- Critical-tier file: `+10`, capped at 100.
- Low-tier file: `-10`, floored at 0.

The score is an internal prioritization aid. Never include it in GitHub comments.

## Mandatory verification above 75

Before assigning a score above 75, directly verify the claim against the target revision:

- Compilation/API claim: inspect the actual definition, dependency version, generated type, or existing CI result.
- Race or lifecycle claim: trace a reachable execution ordering and existing guards.
- Null/undefined claim: trace the successful-data path and all caller validation.
- Repository-guidance claim: quote the exact applicable `AGENTS.md` or `CLAUDE.md` rule.
- Security/data-loss/safety claim: identify the concrete input, operation, and user-visible impact.

Do not execute PR code during initial review. If an executable compiler, test, build, or runtime check is required, leave the finding at 50 or below and state the exact verification needed. Such checks require separate user authorization and an isolated environment that cannot alter the reviewed checkout.

Unverified claims remain at 50 or below.

## Report

Start with:

```markdown
## Summary

<2–4 sentences describing intent, touched areas, design choices, review depth, and reviewer panel>
```

Then print:

```markdown
## Issues (N found)

| # | Score | File:Line | Issue | Reason |
| --- | ---: | --- | --- | --- |
```

Include scores above 25 in `Issues`. Put scores of 25 or below in:

```markdown
## Probably Fine (N found)
```

Number findings continuously across both tables. If a section is empty, state `No issues found` or `No low-confidence items`.

Finish by asking which findings to address. In PR mode, also ask whether the selected findings should be fixed directly or posted as review comments. Do not take either action in the same turn as the initial report.
