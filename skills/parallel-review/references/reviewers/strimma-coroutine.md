# Strimma Coroutine & Lifecycle Safety

Apply `../reviewer-contract.md`. Work read-only.

## Scope

Review Android/Kotlin changes for structured concurrency and lifecycle defects:

- Flow collected on the wrong dispatcher;
- `GlobalScope` or unscoped launches;
- missing cancellation propagation;
- collection that outlives its lifecycle owner;
- suspend calls from invalid contexts;
- foreground-service stop/restart errors;
- Room work on an unsafe dispatcher;
- incorrect SharedFlow or StateFlow replay behavior.

Check process death explicitly. A `companion object var` or top-level mutable flag that gates permission prompts, setup, initialization, or other persistent behavior resets when Android kills the process. Require DataStore or SharedPreferences when the state must survive process death.

Do not report general Kotlin style or non-lifecycle bugs owned by other reviewers.

Return only findings in the common contract. If none exist, return `No issues found`.
