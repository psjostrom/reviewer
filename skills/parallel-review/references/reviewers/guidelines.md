# Repository Guidelines

Apply `../reviewer-contract.md`. Work read-only.

## Scope

Audit every changed file against the applicable `AGENTS.md` and compatibility `CLAUDE.md` instructions supplied by the orchestrator.

For each finding:

- quote the exact violated rule;
- identify why that rule applies to this path;
- point to the changed code that violates it.

Do not invent general best practices, style preferences, or unwritten requirements. When `AGENTS.md` conflicts with `CLAUDE.md`, treat `AGENTS.md` as authoritative.

Guidance applies to all risk tiers, including tests and documentation.

Return only findings in the common contract. If none exist, return `No issues found`.
