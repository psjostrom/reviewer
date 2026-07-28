#!/usr/bin/env python3
"""Validate the full multi-harness reviewer plugin bundle."""

from __future__ import annotations

import json
import re
import stat
import sys
from pathlib import Path

import yaml


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "parallel-review"
LEGACY_SKILL_ROOT = PLUGIN_ROOT / "skills" / "review-pr"
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
CURSOR_MANIFEST = PLUGIN_ROOT / ".cursor-plugin" / "plugin.json"
CURSOR_MARKETPLACE = REPO_ROOT / ".cursor-plugin" / "marketplace.json"
INSTALL_CURSOR = REPO_ROOT / "install-cursor.sh"

HARNESS_REFS = ("codex.md", "cursor.md", "claude-code.md", "opencode.md")
MAX_SHELL_BODY_CHARS = 1200
MAX_ORCHESTRATOR_BODY_CHARS = 2500
OPENCODE_SKILLS_LINK = PLUGIN_ROOT / "opencode" / "skills"

REQUIRED_PATHS = (
    PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
    CURSOR_MANIFEST,
    SKILL_ROOT / "SKILL.md",
    SKILL_ROOT / "agents" / "openai.yaml",
    SKILL_ROOT / "references" / "reviewer-contract.md",
    SKILL_ROOT / "references" / "scoring.md",
    SKILL_ROOT / "references" / "github-actions.md",
    MARKETPLACE_PATH,
    CURSOR_MARKETPLACE,
    INSTALL_CURSOR,
    OPENCODE_SKILLS_LINK,
    *tuple(SKILL_ROOT / "references" / name for name in HARNESS_REFS),
)

REVIEWER_NAMES = {
    "agent-plugins",
    "architecture",
    "bug-hunter",
    "error-edges",
    "frontload-core",
    "frontload-integration",
    "garmin-ciq",
    "guidelines",
    "springa-api",
    "springa-react",
    "strimma-coroutine",
    "strimma-medical",
    "test-reviewer",
}

REVIEWER_MARKERS = {
    "agent-plugins": ("plugin surfaces", "discovery directories", "platform-specific syntax", "Cursor"),
    "architecture": ("workaround", "comments"),
    "bug-hunter": ("wrong results", "Never claim"),
    "error-edges": ("production-reachable", "Trace callers"),
    "frontload-core": ("model-visible payload", "index freshness", "savings"),
    "frontload-integration": ("CLI and MCP", "repository boundary", "unrelated user configuration"),
    "garmin-ciq": ("Connect IQ", "SDK"),
    "guidelines": ("exact violated rule", "Do not invent"),
    "springa-api": ("backward-incompatible", "Nightscout"),
    "springa-react": ("Next.js", "Loading"),
    "strimma-coroutine": ("process death", "DataStore"),
    "strimma-medical": ("18.0182", "temporal correctness"),
    "test-reviewer": ("Banned patterns", "network interceptors"),
}

PLACEHOLDERS = (
    "[TODO:",
    "TBD",
    "implement later",
)

ORCHESTRATOR_SHELLS = (
    (PLUGIN_ROOT / "commands" / "review.md", "claude-code.md"),
    (PLUGIN_ROOT / "opencode" / "commands" / "parallel-review.md", "opencode.md"),
)

AGENT_SHELL_DIRS = (
    PLUGIN_ROOT / "agents",
    PLUGIN_ROOT / "opencode" / "agents",
)


def reviewer_names_in(path: Path, ignored: set[str] | None = None) -> set[str]:
    ignored = ignored or set()
    if not path.exists():
        return set()
    return {reviewer.stem for reviewer in path.glob("*.md") if reviewer.stem not in ignored}


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path}: root must be an object")
        return {}
    return value


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end < 0:
        return "", text
    return text[: end + 5], text[end + 5 :]


def require_in_order(text: str, markers: tuple[str, ...], path: Path, label: str, errors: list[str]) -> None:
    position = -1
    for marker in markers:
        next_position = text.find(marker, position + 1)
        if next_position < 0:
            errors.append(f"{path}: missing ordered {label} marker {marker!r}")
            return
        position = next_position


def validate_domain_reviewer_wiring(text: str, skill_path: Path, errors: list[str]) -> None:
    domain_heading = "### Domain reviewers"
    dispatch_heading = "## 6. Dispatch parallel reviewers"
    domain_start = text.find(domain_heading)
    dispatch_start = text.find(dispatch_heading, domain_start + len(domain_heading))
    require(domain_start >= 0, f"{skill_path}: missing Domain reviewers section", errors)
    require(dispatch_start > domain_start, f"{skill_path}: Domain reviewers section must precede dispatch", errors)
    if domain_start < 0 or dispatch_start <= domain_start:
        return

    domain_section = text[domain_start:dispatch_start]
    normalized_domain_section = re.sub(r"\s+", " ", domain_section)
    for marker in (
        'basename of the git repository root',
        "**Strimma** — basename contains `Strimma`",
        "**Springa** — basename contains `Springa`",
        "**Garmin/Connect IQ** — basename contains `garmin`",
        "**Frontload** — basename is `frontload`",
        "**Agent Plugins** — basename is `agent-plugins`",
        "Domain reviewers run at Standard and Deep, never Quick.",
        "### Test Reviewer at Standard depth",
        "Skip Test Reviewer at Standard when the scoped diff is exclusively Low-tier",
    ):
        require(marker in normalized_domain_section or marker in text, f"{skill_path}: missing active domain reviewer invariant {marker!r}", errors)

    for marker in (
        "| Standard | No Critical files and fewer than 400 changed lines | Bug Hunter, Guidelines, Test Reviewer when source changed, all matching domain reviewers |",
        "| Deep | Any Critical file or at least 400 changed lines | All universal reviewers and all matching domain reviewers |",
        "**Codex / Cursor:** inline both into the child prompt",
        "**Claude Code / opencode:** pass orchestration context only",
    ):
        require(marker in text, f"{skill_path}: missing domain panel wiring {marker!r}", errors)


def validate_manifest(errors: list[str]) -> None:
    path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
    if not path.exists():
        return
    manifest = load_json(path, errors)
    require(manifest.get("name") == "reviewer", f"{path}: name must be reviewer", errors)
    require(manifest.get("skills") == "./skills/", f"{path}: skills must be ./skills/", errors)
    interface = manifest.get("interface")
    require(isinstance(interface, dict), f"{path}: interface must be an object", errors)
    capabilities = interface.get("capabilities") if isinstance(interface, dict) else None
    capabilities_are_strings = isinstance(capabilities, list) and all(isinstance(value, str) for value in capabilities)
    require(
        capabilities_are_strings and {"Interactive", "Read", "Write"}.issubset(set(capabilities)),
        f"{path}: interface capabilities must include Interactive, Read, and Write",
        errors,
    )
    default_prompt = interface.get("defaultPrompt") if isinstance(interface, dict) else None
    require(
        isinstance(default_prompt, list)
        and all(isinstance(value, str) for value in default_prompt)
        and any("$parallel-review" in value for value in default_prompt),
        f"{path}: defaultPrompt must mention $parallel-review",
        errors,
    )
    require(
        not isinstance(default_prompt, list) or all("$review-pr" not in str(value) for value in default_prompt),
        f"{path}: defaultPrompt must not mention legacy $review-pr",
        errors,
    )
    for unsupported in ("hooks", "mcpServers", "apps"):
        require(unsupported not in manifest, f"{path}: unsupported unused field {unsupported}", errors)


def validate_cursor_manifest(errors: list[str]) -> None:
    if not CURSOR_MANIFEST.exists():
        return
    manifest = load_json(CURSOR_MANIFEST, errors)
    require(manifest.get("name") == "reviewer", f"{CURSOR_MANIFEST}: name must be reviewer", errors)
    require(manifest.get("skills") == "./skills/", f"{CURSOR_MANIFEST}: skills must be ./skills/", errors)


def validate_marketplace(errors: list[str]) -> None:
    if not MARKETPLACE_PATH.exists():
        return
    marketplace = load_json(MARKETPLACE_PATH, errors)
    require(marketplace.get("name") == "agent-plugins", f"{MARKETPLACE_PATH}: unexpected name", errors)
    entries = marketplace.get("plugins")
    require(isinstance(entries, list), f"{MARKETPLACE_PATH}: plugins must be an array", errors)
    if not isinstance(entries, list):
        return
    for index, entry in enumerate(entries):
        require(isinstance(entry, dict), f"{MARKETPLACE_PATH}: plugins[{index}] must be an object", errors)
    reviewer = next((entry for entry in entries if isinstance(entry, dict) and entry.get("name") == "reviewer"), None)
    require(reviewer is not None, f"{MARKETPLACE_PATH}: missing reviewer entry", errors)
    if not isinstance(reviewer, dict):
        return
    require(
        reviewer.get("source") == {"source": "local", "path": "./plugins/reviewer"},
        f"{MARKETPLACE_PATH}: reviewer source must be ./plugins/reviewer",
        errors,
    )
    policy = reviewer.get("policy")
    require(
        policy == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        f"{MARKETPLACE_PATH}: reviewer policy is invalid",
        errors,
    )


def validate_cursor_marketplace(errors: list[str]) -> None:
    if not CURSOR_MARKETPLACE.exists():
        return
    marketplace = load_json(CURSOR_MARKETPLACE, errors)
    require(marketplace.get("name") == "agent-plugins", f"{CURSOR_MARKETPLACE}: unexpected name", errors)
    entries = marketplace.get("plugins")
    require(isinstance(entries, list), f"{CURSOR_MARKETPLACE}: plugins must be an array", errors)
    if not isinstance(entries, list):
        return
    names = {entry.get("name") for entry in entries if isinstance(entry, dict)}
    require("reviewer" in names, f"{CURSOR_MARKETPLACE}: missing reviewer entry", errors)
    require("shipwright" in names, f"{CURSOR_MARKETPLACE}: missing shipwright entry", errors)
    reviewer = next((entry for entry in entries if isinstance(entry, dict) and entry.get("name") == "reviewer"), None)
    if isinstance(reviewer, dict):
        require(
            reviewer.get("source") == "./plugins/reviewer",
            f"{CURSOR_MARKETPLACE}: reviewer source must be ./plugins/reviewer",
            errors,
        )


def validate_install_cursor(errors: list[str]) -> None:
    if not INSTALL_CURSOR.exists():
        return
    mode = INSTALL_CURSOR.stat().st_mode
    require(mode & stat.S_IXUSR, f"{INSTALL_CURSOR}: must be executable", errors)
    text = INSTALL_CURSOR.read_text(encoding="utf-8")
    for marker in (
        "CURSOR_PLUGINS_LOCAL",
        "Refusing to install",
        "is not a plugin directory or symlink",
        'cp -R "$src" "$dest"',
        "pwd -P",
        "is_available_plugin",
        "assert_dest_under_plugins",
        "not an available Cursor plugin name",
        "is not installed at",
    ):
        require(marker in text, f"{INSTALL_CURSOR}: missing install safety marker {marker!r}", errors)


def validate_skill(errors: list[str]) -> None:
    skill_path = SKILL_ROOT / "SKILL.md"
    metadata_path = SKILL_ROOT / "agents" / "openai.yaml"
    if skill_path.exists():
        text = skill_path.read_text(encoding="utf-8")
        require(text.startswith("---\n"), f"{skill_path}: missing YAML frontmatter", errors)
        require(re.search(r"^name:\s*parallel-review\s*$", text, re.MULTILINE) is not None, f"{skill_path}: wrong name", errors)
        require(
            re.search(r"^disable-model-invocation:\s*true\s*$", text, re.MULTILINE) is not None,
            f"{skill_path}: must set disable-model-invocation: true",
            errors,
        )
        require("# Parallel Code Review" in text, f"{skill_path}: wrong title", errors)
        require("parallel" in text.lower() and "subagent" in text.lower(), f"{skill_path}: must require parallel subagents", errors)
        require("Do not merge" in text, f"{skill_path}: must explicitly forbid merging", errors)
        require(
            "from the directory containing this `SKILL.md`" in text,
            f"{skill_path}: must define relative reference resolution",
            errors,
        )
        require(
            re.search(
                r"For every changed file, read every `AGENTS\.md`.*Also read every `CLAUDE\.md`.*Apply guidance broad-to-narrow",
                text,
                re.DOTALL,
            )
            is not None,
            f"{skill_path}: must load both complete guidance chains broad-to-narrow",
            errors,
        )
        for marker in (
            "repository-relative path filters",
            "Resolve each path from the repository root",
            "Reject any path that resolves outside the repository",
            "Filter the changed-file list and patch",
            "If no changed files match the path filters",
            "Findings must identify a defect in scoped changed code",
        ):
            require(marker in text, f"{skill_path}: missing path-scope invariant {marker!r}", errors)
        validate_domain_reviewer_wiring(text, skill_path, errors)
        for adapter in HARNESS_REFS:
            require(f"`references/{adapter}`" in text, f"{skill_path}: must reference harness adapter {adapter!r}", errors)
        require_in_order(
            text,
            (
                "## 7. Synthesize and score",
                "Do not execute PR code during the review phase.",
                "## 8. Stop at the decision gate",
                "If the user selects an action",
            ),
            skill_path,
            "review gate",
            errors,
        )
    if metadata_path.exists():
        text = metadata_path.read_text(encoding="utf-8")
        require(
            re.search(r'^\s*display_name:\s*"Parallel Code Review"\s*$', text, re.MULTILINE) is not None,
            f"{metadata_path}: display name must be Parallel Code Review",
            errors,
        )
        require(
            re.search(r"^\s*allow_implicit_invocation:\s*false\s*$", text, re.MULTILINE) is not None,
            f"{metadata_path}: implicit invocation must be disabled",
            errors,
        )
        require("$parallel-review" in text, f"{metadata_path}: default prompt must mention $parallel-review", errors)
        require("$review-pr" not in text, f"{metadata_path}: must not mention legacy $review-pr", errors)


def validate_harness_adapters(errors: list[str]) -> None:
    for name in HARNESS_REFS:
        path = SKILL_ROOT / "references" / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        require(
            "### Child model floor (required)" in text,
            f"{path}: missing child model floor section",
            errors,
        )
        for role in sorted(REVIEWER_NAMES):
            require(
                f"{role}.md`" in text,
                f"{path}: missing shared reviewer wiring for {role!r}",
                errors,
            )
    codex_path = SKILL_ROOT / "references" / "codex.md"
    if codex_path.exists():
        text = codex_path.read_text(encoding="utf-8")
        require("fork_context: false" in text, f"{codex_path}: must require self-contained subagent threads", errors)
        require("gpt-5.6-terra" in text, f"{codex_path}: must require Terra child model", errors)
        require("medium" in text, f"{codex_path}: must require medium child effort", errors)
    cursor_path = SKILL_ROOT / "references" / "cursor.md"
    if cursor_path.exists():
        text = cursor_path.read_text(encoding="utf-8")
        require("composer-2.5-fast" in text, f"{cursor_path}: must require Composer child model", errors)
        require("cursor-grok" in text.lower() or "frontier Grok" in text, f"{cursor_path}: must forbid frontier Grok children", errors)
    claude_path = SKILL_ROOT / "references" / "claude-code.md"
    if claude_path.exists():
        text = claude_path.read_text(encoding="utf-8")
        require("**sonnet**" in text, f"{claude_path}: must default specialists to sonnet", errors)
    opencode_path = SKILL_ROOT / "references" / "opencode.md"
    if opencode_path.exists():
        text = opencode_path.read_text(encoding="utf-8")
        require("opencode.json" in text, f"{opencode_path}: must document mid-tier opencode.json models", errors)
        require("Do not default specialists to Opus" in text, f"{opencode_path}: must forbid Opus defaults", errors)
        require(
            injects_shared_root_into_task_prompt(text),
            f"{opencode_path}: must require absolute SHARED_ROOT in the Task prompt payload",
            errors,
        )
        require(
            forbids_specialist_shared_root_rediscovery(text),
            f"{opencode_path}: must forbid specialist SHARED_ROOT rediscovery",
            errors,
        )


def validate_reviewers(errors: list[str]) -> None:
    reviewers_dir = SKILL_ROOT / "references" / "reviewers"
    if not reviewers_dir.exists():
        errors.append(f"{reviewers_dir}: missing reviewer prompt directory")
        return
    files = {path.stem: path for path in reviewers_dir.glob("*.md")}
    missing = sorted(REVIEWER_NAMES - files.keys())
    extra = sorted(files.keys() - REVIEWER_NAMES)
    require(not missing, f"{reviewers_dir}: missing reviewers: {', '.join(missing)}", errors)
    require(not extra, f"{reviewers_dir}: unexpected reviewers: {', '.join(extra)}", errors)
    normalized_bodies: dict[str, str] = {}
    for name, path in sorted(files.items()):
        text = path.read_text(encoding="utf-8")
        require("read-only" in text.lower(), f"{path}: must state read-only scope", errors)
        require("scope" in text.lower(), f"{path}: must define scope boundaries", errors)
        require(
            "reviewer-contract.md" in text or "No issues found" in text,
            f"{path}: must reference the common contract or define the empty result",
            errors,
        )
        for marker in REVIEWER_MARKERS.get(name, ()):
            require(marker in text, f"{path}: missing role-specific marker {marker!r}", errors)
        normalized = re.sub(r"\s+", " ", text).strip().lower()
        duplicate = next((other for other, body in normalized_bodies.items() if body == normalized), None)
        require(duplicate is None, f"{path}: duplicates reviewer prompt {duplicate}", errors)
        normalized_bodies[name] = normalized


def validate_reviewer_surface_parity(
    codex_reviewers: set[str],
    claude_reviewers: set[str],
    opencode_reviewers: set[str],
    errors: list[str],
    expected_reviewers: set[str] | None = None,
    cursor_reviewers: set[str] | None = None,
) -> None:
    surfaces: list[tuple[str, set[str]]] = [
        ("Codex reviewer prompts", codex_reviewers),
        ("Claude reviewer agents", claude_reviewers),
        ("opencode reviewer agents", opencode_reviewers),
    ]
    if cursor_reviewers is not None:
        surfaces.append(("Cursor reviewer roles", cursor_reviewers))
    expected = expected_reviewers or set().union(*(reviewers for _, reviewers in surfaces))
    for label, reviewers in surfaces:
        missing = sorted(expected - reviewers)
        extra = sorted(reviewers - expected)
        if missing:
            errors.append(f"missing {label}: {', '.join(missing)}")
        if extra:
            errors.append(f"unexpected {label}: {', '.join(extra)}")


def reviewer_names_from_adapter(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    return {role for role in REVIEWER_NAMES if f"{role}.md`" in text}


def validate_cross_platform_reviewer_parity(errors: list[str]) -> None:
    validate_reviewer_surface_parity(
        codex_reviewers=reviewer_names_in(SKILL_ROOT / "references" / "reviewers"),
        claude_reviewers=reviewer_names_in(PLUGIN_ROOT / "agents"),
        opencode_reviewers=reviewer_names_in(PLUGIN_ROOT / "opencode" / "agents", ignored={"reviewer"}),
        cursor_reviewers=reviewer_names_from_adapter(SKILL_ROOT / "references" / "cursor.md"),
        errors=errors,
        expected_reviewers=set(REVIEWER_NAMES),
    )


def specialist_reads_shared_prompt(body: str, role: str) -> bool:
    markers = (
        f"${{CLAUDE_PLUGIN_ROOT}}/skills/parallel-review/references/reviewers/{role}.md",
        f"$SHARED_ROOT/references/reviewers/{role}.md",
    )
    return any(marker in body for marker in markers)


def injects_shared_root_into_task_prompt(text: str) -> bool:
    """True when text requires absolute SHARED_ROOT in the specialist Task payload."""
    markers = (
        "SHARED_ROOT=<absolute path from orchestrator resolution>",
        "Pass `SHARED_ROOT=<absolute path>` in every specialist Task prompt",
        "include the absolute `SHARED_ROOT=<path>` line in every Task prompt",
    )
    return any(marker in text for marker in markers)


def forbids_specialist_shared_root_rediscovery(text: str) -> bool:
    """True only for explicit negative wording (not polarity-ambiguous substrings)."""
    return (
        re.search(
            r"(?i)do\s+(?:\*\*)?not(?:\*\*)?\s+require\s+specialists\s+to\s+rediscover",
            text,
        )
        is not None
    )


def _load_frontmatter_mapping(frontmatter: str) -> dict | None:
    """Parse markdown frontmatter YAML; reject duplicate mapping keys."""
    if not frontmatter:
        return None
    content = frontmatter.strip()
    if content.startswith("---"):
        content = content[3:]
    if content.endswith("---"):
        content = content[:-3]
    content = content.strip()
    if not content:
        return None

    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict:
        mapping: dict = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    None,
                    None,
                    f"duplicate key {key!r}",
                    key_node.start_mark,
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping,
    )
    try:
        data = yaml.load(content, Loader=UniqueKeyLoader)
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def frontmatter_external_directory_allow(frontmatter: str) -> bool:
    """True when permission.external_directory is exactly allow."""
    data = _load_frontmatter_mapping(frontmatter)
    if data is None:
        return False
    permission = data.get("permission")
    if not isinstance(permission, dict):
        return False
    return permission.get("external_directory") == "allow"


def requires_injected_absolute_shared_root(body: str) -> bool:
    """True when body ties absolute SHARED_ROOT injection to a no-rediscover rule."""
    return (
        re.search(
            r"(?is)Require an absolute\s+`SHARED_ROOT=\.\.\.`\s+line from the orchestrator Task prompt\.\s*"
            r"Do not rediscover",
            body,
        )
        is not None
    )


def is_opencode_agent_path(path: Path) -> bool:
    try:
        path.resolve().relative_to((PLUGIN_ROOT / "opencode" / "agents").resolve())
        return True
    except ValueError:
        return False


def validate_thin_shells(errors: list[str]) -> None:
    if OPENCODE_SKILLS_LINK.exists() or OPENCODE_SKILLS_LINK.is_symlink():
        require(
            OPENCODE_SKILLS_LINK.is_symlink() and OPENCODE_SKILLS_LINK.resolve() == (PLUGIN_ROOT / "skills").resolve(),
            f"{OPENCODE_SKILLS_LINK}: must symlink to plugins/reviewer/skills",
            errors,
        )

    for path, adapter in ORCHESTRATOR_SHELLS:
        if not path.exists():
            errors.append(f"{path}: missing orchestrator shell")
            continue
        text = path.read_text(encoding="utf-8")
        _, body = split_frontmatter(text)
        if path.name == "review.md":
            require(
                "${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/SKILL.md" in text,
                f"{path}: must load SKILL.md via CLAUDE_PLUGIN_ROOT",
                errors,
            )
            require(
                f"${{CLAUDE_PLUGIN_ROOT}}/skills/parallel-review/references/{adapter}" in text,
                f"{path}: must load harness adapter via CLAUDE_PLUGIN_ROOT",
                errors,
            )
        else:
            require("$SHARED_ROOT/SKILL.md" in text, f"{path}: must load SKILL.md via SHARED_ROOT", errors)
            require(
                f"$SHARED_ROOT/references/{adapter}" in text,
                f"{path}: must load harness adapter via SHARED_ROOT",
                errors,
            )
            require("realpath" in text or "os.path.realpath" in text, f"{path}: must resolve install symlink", errors)
            require("~/.config/opencode" in text or "${HOME}/.config/opencode" in text, f"{path}: must use global install path", errors)
            require("$(pwd)/.opencode" not in text, f"{path}: must not trust repo-local .opencode", errors)
            require(
                injects_shared_root_into_task_prompt(text),
                f"{path}: must instruct injecting absolute SHARED_ROOT into every Task prompt payload",
                errors,
            )
        require(
            len(body) <= MAX_ORCHESTRATOR_BODY_CHARS,
            f"{path}: orchestrator body exceeds {MAX_ORCHESTRATOR_BODY_CHARS} chars (likely fat orchestrator)",
            errors,
        )
        for forbidden in ("## Step 5: Synthesize", "Score each deduplicated issue", "git add -N"):
            require(forbidden not in body, f"{path}: must not duplicate shared workflow content ({forbidden!r})", errors)

    for directory in AGENT_SHELL_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            if path.stem == "reviewer":
                continue
            text = path.read_text(encoding="utf-8")
            frontmatter, body = split_frontmatter(text)
            role = path.stem
            require(
                specialist_reads_shared_prompt(body, role),
                f"{path}: must instruct reading shared reviewer prompt via plugin-absolute path",
                errors,
            )
            if is_opencode_agent_path(path):
                require("$SHARED_ROOT" in body, f"{path}: opencode shell must use SHARED_ROOT", errors)
                require(
                    requires_injected_absolute_shared_root(body),
                    f"{path}: opencode shell must require injected SHARED_ROOT",
                    errors,
                )
                require(
                    frontmatter_external_directory_allow(frontmatter),
                    f"{path}: opencode shell must allow external_directory for SHARED_ROOT reads",
                    errors,
                )
                data = _load_frontmatter_mapping(frontmatter)
                permission = data.get("permission") if isinstance(data, dict) else None
                require(
                    isinstance(permission, dict) and permission.get("bash") == "deny",
                    f"{path}: opencode specialist must set bash: deny",
                    errors,
                )
            else:
                require("${CLAUDE_PLUGIN_ROOT}" in body, f"{path}: Claude shell must use CLAUDE_PLUGIN_ROOT", errors)
            require(
                len(body) <= MAX_SHELL_BODY_CHARS,
                f"{path}: specialist shell body exceeds {MAX_SHELL_BODY_CHARS} chars (likely divergent prose)",
                errors,
            )
            for marker in REVIEWER_MARKERS.get(role, ()):
                require(marker not in body, f"{path}: must not re-host specialist marker {marker!r}", errors)

    primary = PLUGIN_ROOT / "opencode" / "agents" / "reviewer.md"
    if primary.exists():
        text = primary.read_text(encoding="utf-8")
        frontmatter, _ = split_frontmatter(text)
        require(
            frontmatter_external_directory_allow(frontmatter),
            f"{primary}: primary agent must allow external_directory for SHARED_ROOT reads",
            errors,
        )
        require("$SHARED_ROOT" in text, f"{primary}: primary agent must reference SHARED_ROOT", errors)
        require(
            injects_shared_root_into_task_prompt(text),
            f"{primary}: must instruct injecting absolute SHARED_ROOT into every specialist Task prompt",
            errors,
        )


def validate_references(errors: list[str]) -> None:
    contract_path = SKILL_ROOT / "references" / "reviewer-contract.md"
    scoring_path = SKILL_ROOT / "references" / "scoring.md"
    actions_path = SKILL_ROOT / "references" / "github-actions.md"
    if contract_path.exists():
        text = contract_path.read_text(encoding="utf-8")
        for marker in ("Work read-only", "No issues found", "Evidence standard", "Do not return compliments"):
            require(marker in text, f"{contract_path}: missing invariant {marker!r}", errors)
    if scoring_path.exists():
        text = scoring_path.read_text(encoding="utf-8")
        for marker in (
            "Mandatory verification above 75",
            "Do not execute PR code during initial review",
            "Unverified claims remain at 50 or below",
            "Never include it in GitHub comments",
            "Do not include raw per-reviewer dumps",
        ):
            require(marker in text, f"{scoring_path}: missing invariant {marker!r}", errors)
    if actions_path.exists():
        text = actions_path.read_text(encoding="utf-8")
        for pattern, label in (
            (r"Never merge the pull request", "merge prohibition"),
            (r"Do not resolve review threads unless the user explicitly asks", "thread-resolution authorization"),
            (r"Default the summary event to `COMMENT`", "default COMMENT event"),
            (r"Approving, requesting changes, and resolving threads are separate mutations that require explicit user authorization", "separate mutation authorization"),
            (r"Use `APPROVE` only when the user explicitly asks", "approval authorization"),
            (r"Use `REQUEST_CHANGES` only when the user explicitly asks", "request-changes authorization"),
            (r"pass that exact SHA as `commit_id` in every inline-comment payload", "head SHA payload requirement"),
            (r"\{commit_id:\$commit, path:\$path, line:\$line, side:\"RIGHT\", body:\$body\}", "single-line inline payload"),
            (r"include `start_line`, `start_side:\"RIGHT\"`, `line`, and `side:\"RIGHT\"`", "multi-line inline payload"),
            (r"jq --rawfile", "rawfile body handling"),
            (r"Stop on the first failed comment", "failure stop"),
            (r"mktemp", "mktemp body files"),
            (r"Do \*\*not\*\* auto-try `APPROVE` on clean reviews", "no auto APPROVE"),
            (r"MCP must not bypass the shared posting contract|MCP-based posting", "MCP follows hard rules"),
            (r"### Summary review body", "summary body section"),
            (r"not the skill or tool name", "summary forbids skill/tool naming"),
            (r"Do not refer to chat-report numbering", "summary forbids finding-number refs"),
            (r"Do not add process filler", "summary forbids process filler"),
        ):
            require(re.search(pattern, text) is not None, f"{actions_path}: missing invariant {label!r}", errors)
        require("Self-PR clean review fallback" not in text, f"{actions_path}: must not ship Self-PR APPROVE fallback block", errors)
        require("/tmp/lgtm.txt" not in text, f"{actions_path}: must not use fixed /tmp/lgtm.txt", errors)
        require_in_order(
            text,
            (
                "Refresh the PR head SHA immediately before posting",
                "mktemp",
                "{commit_id:$commit, path:$path, line:$line, side:\"RIGHT\", body:$body}",
                "After every inline comment succeeds",
                "{commit_id:$commit, event:$event, body:$body}",
            ),
            actions_path,
            "comment posting",
            errors,
        )


def validate_placeholders(errors: list[str]) -> None:
    roots = [
        PLUGIN_ROOT / ".codex-plugin",
        PLUGIN_ROOT / ".cursor-plugin",
        SKILL_ROOT,
        REPO_ROOT / ".agents" / "plugins",
        REPO_ROOT / ".cursor-plugin",
    ]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".json", ".yaml", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8")
            for placeholder in PLACEHOLDERS:
                require(placeholder not in text, f"{path}: contains placeholder {placeholder!r}", errors)


def main() -> int:
    errors: list[str] = []
    require(not LEGACY_SKILL_ROOT.exists(), f"{LEGACY_SKILL_ROOT}: legacy skill directory must be removed", errors)
    for path in REQUIRED_PATHS:
        require(path.exists(), f"{path}: required path is missing", errors)
    validate_manifest(errors)
    validate_cursor_manifest(errors)
    validate_marketplace(errors)
    validate_cursor_marketplace(errors)
    validate_install_cursor(errors)
    validate_skill(errors)
    validate_harness_adapters(errors)
    validate_reviewers(errors)
    validate_cross_platform_reviewer_parity(errors)
    validate_thin_shells(errors)
    validate_references(errors)
    validate_placeholders(errors)

    if errors:
        print("Reviewer validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Reviewer validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
