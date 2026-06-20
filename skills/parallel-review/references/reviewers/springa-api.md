# Springa API Contract & Schema

Apply `../reviewer-contract.md`. Work read-only.

## Scope

Find backward-incompatible changes to:

- REST endpoint paths and methods;
- request and response shapes;
- Turso schema and migrations;
- Nightscout-compatible `/api/v1/entries` and `/api/v1/treatments` behavior;
- shared contracts consumed by Strimma or Garmin clients.

When a body field, query parameter, response property, or database shape changes, inspect every in-repository client and migration path.

Check applicable repository guidance for Nightscout details such as `.json` GET suffixes, MongoDB-style query parameters, and exact response shapes. Do not assume a rule that is not present in guidance or existing compatibility tests.

Do not report React rendering issues or generic architecture concerns.

Return only findings in the common contract. If none exist, return `No issues found`.
