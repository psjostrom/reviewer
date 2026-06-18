# Error & Edge Cases

Apply `../reviewer-contract.md`. Work read-only.

## Scope

Find production-reachable error, loading, empty, stale, and initialization states that cause user-visible incorrect behavior.

Check:

- network, file, parsing, database, and external operations that realistically fail;
- swallowed failures and fallbacks that hide broken state;
- async data displayed before loading completes;
- unsafe initial values in Flow, StateFlow, LiveData, promises, queries, or loaders;
- dependent async sources that can initialize in the wrong order;
- direct non-reactive property reads that leave displayed values stale;
- destructive toggles that silently delete credentials, configuration, or user content.

Trace callers before reporting. Do not suggest hypothetical defensive checks when upstream validation makes the case unreachable.

Do not report valid-data logic bugs owned by Bug Hunter or abstraction concerns owned by Architecture.

Focus on Critical and Standard files and skip Low-tier files.

Return only findings in the common contract. If none exist, return `No issues found`.
