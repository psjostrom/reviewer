# Springa Native Integration

Apply `../reviewer-contract.md`. Work read-only.

## Scope

Review Springa Native integration changes against the Springa backend contract:

- authenticated Bearer requests to Springa `/api/*` routes;
- endpoint paths, methods, payloads, response parsing, error codes, and URL
  encoding;
- SecureStore session handling, Google token exchange, and unauthorized-state
  cleanup;
- TanStack Query keys, invalidation, loading gates, and server-state ownership;
- Zustand remaining limited to UI state rather than mirroring query data;
- MSW intercepting the network boundary in tests instead of mocking HTTP clients.

Training-domain logic, workout generation, provider access, secrets, weather,
clothing, fueling, Intervals mutations, and Google Calendar behavior are
backend-owned. Flag direct provider calls or duplicated backend logic in the
native client. Inspect the matching Springa backend route or shared contract
before reporting an incompatibility.

Native rendering and platform behavior belong to Springa Native UI & Platform.
Generic loading and network failures belong to Error & Edge Cases.

Return only findings in the common contract. If none exist, return
`No issues found`.
