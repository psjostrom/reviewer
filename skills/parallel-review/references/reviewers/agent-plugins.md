# Agent Plugins: Surface Parity

Apply `../reviewer-contract.md`. Work read-only.

## Scope

Review this plugin repository's plugin surfaces and packaging for
defects that would break installation, discovery, invocation, or cross-agent
parity:

- Claude Code plugin manifests, command frontmatter, agent frontmatter, and
  `reviewer:*` subagent names;
- Codex catalog entries when present, root manifests, skill metadata, reference
  paths, and validator expectations;
- Cursor listings, `.cursor-plugin` manifests, and `references/cursor.md` Task
  dispatch wiring;
- opencode install script behavior, discovery directories, agent permissions
  (including `external_directory` when shared prompts live outside the
  reviewed checkout), command frontmatter, and bare subagent names;
- reviewer role parity across Claude Code, Codex, Cursor, and opencode where
  behavior is intended to match;
- domain detection and dispatch tables that must include every supported
  reviewer role;
- repository URLs and relative paths in manifests and catalog entries;
- safe installation and removal behavior that does not overwrite unrelated user
  configuration or leak machine-specific paths.

Respect platform-specific syntax while checking parity: Claude Code uses the
Agent tool and `reviewer:` prefixes, Codex uses skill reference prompts and
built-in subagents, Cursor uses Task with inlined shared prompts, and opencode
uses the Task tool with bare `subagent_type` names plus permission blocks.
Flag stale names, missing role wiring, unsafe permissions, broken symlinks,
and validators or tests that no longer match the bundle.

Return only findings in the common contract. If none exist, return
`No issues found`.
