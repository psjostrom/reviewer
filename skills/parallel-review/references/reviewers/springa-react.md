# Springa React & Next.js Patterns

Apply `../reviewer-contract.md`. Work read-only.

## Scope

Review changed React and Next.js code for:

- unnecessary `'use client'` boundaries;
- missing `await` on async Next.js request APIs such as `cookies()`, `headers()`, `params`, and `searchParams`;
- stale closures and incorrect hook dependencies;
- invalid server action usage;
- missing framework error boundaries where required;
- components made client-side despite being viable server components.

Inspect the repository's actual Next.js version and established patterns before making version-specific claims.

Loading, error, and undefined-state mechanics belong to Error & Edge Cases. API contract changes belong to Springa API.

Return only findings in the common contract. If none exist, return `No issues found`.
