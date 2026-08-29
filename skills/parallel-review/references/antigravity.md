# Antigravity parallel reviewer instructions

Multi-agent parallel code review runtime reference for Google Antigravity.

## Role Parity & Dispatch Routing

When `/parallel-review` runs in Google Antigravity, the orchestrator MUST spawn independent review subagents concurrently using the `invoke_subagent` tool.

### Child model floor (required)

- **Default Floor**: `Model: "flash"` (Gemini 3.7 Flash) MUST be specified for each subagent.
- **Complex Override**: If reviewing deep cryptographic, concurrency-sensitive, or complex medical logic, `Model: "pro"` may be specified.
- **Inheritance**: `Model: "inherit"` is accepted if the parent session is running on a high-capability Gemini model.

### Subagent Dispatch

Pass all active subagents in a single `invoke_subagent` call so they run concurrently in the background:

```json
{
  "Subagents": [
    {
      "TypeName": "research",
      "Role": "Bug Hunter",
      "Model": "flash",
      "Prompt": "<Bug Hunter Prompt containing instructions and diff>"
    },
    {
      "TypeName": "research",
      "Role": "Guidelines Reviewer",
      "Model": "flash",
      "Prompt": "<Guidelines Reviewer Prompt containing instructions and diff>"
    }
  ]
}
```

## Reviewer Prompts

Each subagent prompt must be self-contained and incorporate the full diff/files under review and the specialized instructions below.

### 1. `bug-hunter`
Read [`skills/parallel-review/references/reviewers/bug-hunter.md`](reviewers/bug-hunter.md).
Role: Logic and correctness specialist. Focus on logic errors, off-by-one errors, broken conditionals, null dereferences, unhandled state transitions, and unintended regression.

### 2. `guidelines`
Read [`skills/parallel-review/references/reviewers/guidelines.md`](reviewers/guidelines.md).
Role: Repository and code conventions specialist. Focus on project idiom conformance, naming, documentation requirements, and avoiding forbidden patterns.

### 3. `error-edges`
Read [`skills/parallel-review/references/reviewers/error-edges.md`](reviewers/error-edges.md).
Role: Resilience and boundary specialist. Focus on error handling, edge cases, malformed payloads, timeout recovery, resource exhaustion, and partial failure modes.

### 4. `architecture`
Read [`skills/parallel-review/references/reviewers/architecture.md`](reviewers/architecture.md).
Role: System design and structural specialist. Focus on component boundaries, dependency direction, abstraction leaks, coupling, and single source of truth violations.

### 5. `test-reviewer`
Read [`skills/parallel-review/references/reviewers/test-reviewer.md`](reviewers/test-reviewer.md).
Role: Test completeness and regression verification specialist. Focus on missing test paths, assertions on internal mock states instead of visible behaviors, and flaky setup.

### 6. `strimma-coroutine`
Read [`skills/parallel-review/references/reviewers/strimma-coroutine.md`](reviewers/strimma-coroutine.md).
Role: Strimma Kotlin coroutine specialist. Focus on CoroutineScope lifecycle, structured concurrency leaks, Dispatcher selection, and cancellation propagation.

### 7. `strimma-medical`
Read [`skills/parallel-review/references/reviewers/strimma-medical.md`](reviewers/strimma-medical.md).
Role: Glucose calculation and medical safety specialist. Focus on critical glucose tracking invariants, unit conversions (mg/dL vs mmol/L), alarm dispatch, and stale data suppression.

### 8. `springa-api`
Read [`skills/parallel-review/references/reviewers/springa-api.md`](reviewers/springa-api.md).
Role: Springa Next.js and backend route specialist. Focus on server action safety, database transactions, auth session validation, and API rate limiting.

### 9. `springa-react`
Read [`skills/parallel-review/references/reviewers/springa-react.md`](reviewers/springa-react.md).
Role: Springa client UI and React hooks specialist. Focus on hydration mismatches, unnecessary re-renders, hook dependency correctness, and loading state transitions.

### 10. `garmin-ciq`
Read [`skills/parallel-review/references/reviewers/garmin-ciq.md`](reviewers/garmin-ciq.md).
Role: Garmin Connect IQ Monkey C specialist. Focus on peak memory limits, battery conservation, foreground/background data sync, and device profile matrix constraints.

### 11. `agent-plugins`
Read [`skills/parallel-review/references/reviewers/agent-plugins.md`](reviewers/agent-plugins.md).
Role: Cross-platform plugin consistency specialist. Focus on cross-harness manifest parity (Claude, Codex, Cursor, opencode, Antigravity) and path resolution symmetry.

### 12. `frontload-core`
Read [`skills/parallel-review/references/reviewers/frontload-core.md`](reviewers/frontload-core.md).
Role: Frontload core business logic specialist. Focus on core invariant preservation and domain event dispatch correctness.

### 13. `frontload-integration`
Read [`skills/parallel-review/references/reviewers/frontload-integration.md`](reviewers/frontload-integration.md).
Role: Frontload third-party integration specialist. Focus on external API boundary contracts, webhook idempotency, and retry backoff.

## Review Aggregation and Scoring

After all subagents report back:
1. Aggregate and deduplicate findings following [`skills/parallel-review/references/scoring.md`](scoring.md) and [`skills/parallel-review/references/reviewer-contract.md`](reviewer-contract.md).
2. Report confidence-ranked issues to the user with exact line references.
3. Await user instructions before offering any edits or automated fixes.
