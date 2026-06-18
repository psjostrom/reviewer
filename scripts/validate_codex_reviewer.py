#!/usr/bin/env python3
"""Validate the portable Codex surface of the reviewer plugin."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "review-pr"
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"

REQUIRED_PATHS = (
    PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
    SKILL_ROOT / "SKILL.md",
    SKILL_ROOT / "agents" / "openai.yaml",
    SKILL_ROOT / "references" / "reviewer-contract.md",
    SKILL_ROOT / "references" / "scoring.md",
    SKILL_ROOT / "references" / "github-actions.md",
    MARKETPLACE_PATH,
)

REVIEWER_NAMES = {
    "architecture",
    "bug-hunter",
    "error-edges",
    "garmin-ciq",
    "guidelines",
    "springa-api",
    "springa-react",
    "strimma-coroutine",
    "strimma-medical",
    "test-reviewer",
}

PLACEHOLDERS = (
    "[TODO:",
    "TBD",
    "implement later",
)


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


def validate_manifest(errors: list[str]) -> None:
    path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
    if not path.exists():
        return
    manifest = load_json(path, errors)
    require(manifest.get("name") == "reviewer", f"{path}: name must be reviewer", errors)
    require(manifest.get("skills") == "./skills/", f"{path}: skills must be ./skills/", errors)
    for unsupported in ("hooks", "mcpServers", "apps"):
        require(unsupported not in manifest, f"{path}: unsupported unused field {unsupported}", errors)


def validate_marketplace(errors: list[str]) -> None:
    if not MARKETPLACE_PATH.exists():
        return
    marketplace = load_json(MARKETPLACE_PATH, errors)
    require(marketplace.get("name") == "agent-plugins", f"{MARKETPLACE_PATH}: unexpected name", errors)
    entries = marketplace.get("plugins")
    require(isinstance(entries, list), f"{MARKETPLACE_PATH}: plugins must be an array", errors)
    if not isinstance(entries, list):
        return
    reviewer = next((entry for entry in entries if entry.get("name") == "reviewer"), None)
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


def validate_skill(errors: list[str]) -> None:
    skill_path = SKILL_ROOT / "SKILL.md"
    metadata_path = SKILL_ROOT / "agents" / "openai.yaml"
    if skill_path.exists():
        text = skill_path.read_text(encoding="utf-8")
        require(text.startswith("---\n"), f"{skill_path}: missing YAML frontmatter", errors)
        require(re.search(r"^name:\s*review-pr\s*$", text, re.MULTILINE) is not None, f"{skill_path}: wrong name", errors)
        require("parallel" in text.lower() and "subagent" in text.lower(), f"{skill_path}: must require parallel subagents", errors)
        require("Do not merge" in text, f"{skill_path}: must explicitly forbid merging", errors)
    if metadata_path.exists():
        text = metadata_path.read_text(encoding="utf-8")
        require(
            re.search(r"^\s*allow_implicit_invocation:\s*false\s*$", text, re.MULTILINE) is not None,
            f"{metadata_path}: implicit invocation must be disabled",
            errors,
        )
        require("$review-pr" in text, f"{metadata_path}: default prompt must mention $review-pr", errors)


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
    for name, path in sorted(files.items()):
        text = path.read_text(encoding="utf-8")
        require("read-only" in text.lower(), f"{path}: must state read-only scope", errors)
        require("scope" in text.lower(), f"{path}: must define scope boundaries", errors)
        require(
            "reviewer-contract.md" in text or "No issues found" in text,
            f"{path}: must reference the common contract or define the empty result",
            errors,
        )


def validate_placeholders(errors: list[str]) -> None:
    roots = [PLUGIN_ROOT / ".codex-plugin", SKILL_ROOT, REPO_ROOT / ".agents" / "plugins"]
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
    for path in REQUIRED_PATHS:
        require(path.exists(), f"{path}: required path is missing", errors)
    validate_manifest(errors)
    validate_marketplace(errors)
    validate_skill(errors)
    validate_reviewers(errors)
    validate_placeholders(errors)

    if errors:
        print("Codex reviewer validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Codex reviewer validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
