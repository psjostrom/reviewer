# Reviewer Contract

Apply this contract to every specialist reviewer prompt.

## Operating boundary

- Work read-only. Do not edit files, stage changes, create commits, push, post comments, approve, request changes, or merge.
- Review only defects introduced or exposed by the supplied change, except for the `Late discovery` case below.
- In incremental mode, stay inside the supplied comparison and its directly affected callers, contracts, and tests. Do not rescan unrelated unchanged code. User-supplied path filters remain a hard finding boundary.
- A directly verified pre-baseline defect encountered while tracing that impact cone may be reported as the sole changed-code exception; prefix its description with `Late discovery:`.
- Spend most effort on Critical-tier files, normal effort on Standard-tier files, and only role-specific effort on Low-tier files.
- Inspect surrounding source when needed to prove a claim. In PR mode, use the PR head revision rather than assuming the local checkout matches.
- Ignore compiler or linter findings unless they reveal a behavioral problem the automated tool cannot explain by itself.
- Do not return compliments, confirmations, or positive observations as findings.

## Finding format

Return a structured list. Every finding must contain:

```text
Description: <what is wrong>
File: <repository-relative path>
Code context: <exact changed line or smallest exact snippet>
Line: <best-effort new-file line number, or unknown>
Reason: <short category tag>
Suggestion: <concrete fix>
Evidence: <execution path, contract, test, or source fact proving the claim>
```

If there are no findings, return exactly:

```text
No issues found
```

## Evidence standard

- Trace actual callers before claiming an input can be null, undefined, stale, or malformed.
- Verify repository APIs and constants before claiming something does not exist or cannot compile.
- Distinguish a demonstrated defect from a question. Prefix unresolved questions with `Verify:` and provide the exact check needed.
- Do not inflate several symptoms of the same root cause into separate findings.
- Keep suggestions proportional. Do not prescribe broad refactors for narrow defects.
