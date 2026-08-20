#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import io
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("validate_codex_reviewer.py")
SPEC = importlib.util.spec_from_file_location("validate_codex_reviewer", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
PLUGIN_ROOT = VALIDATOR.PLUGIN_ROOT
INSTALL_OPENCODE = PLUGIN_ROOT / "install-opencode.sh"


class DomainReviewerWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill_path = VALIDATOR.SKILL_ROOT / "SKILL.md"
        self.skill_text = self.skill_path.read_text(encoding="utf-8")

    def validate(self, text: str) -> list[str]:
        errors: list[str] = []
        VALIDATOR.validate_domain_reviewer_wiring(text, self.skill_path, errors)
        return errors

    def test_accepts_active_frontload_mapping_and_panel_wiring(self) -> None:
        self.assertEqual(self.validate(self.skill_text), [])

    def test_rejects_missing_strimma_detection(self) -> None:
        text = self.skill_text.replace("**Strimma** — basename contains `Strimma`", "**Strimma** — omitted")
        self.assertTrue(self.validate(text))

    def test_rejects_standard_panel_without_matching_domain_reviewers(self) -> None:
        text = self.skill_text.replace(
            "Test Reviewer when source changed, all matching domain reviewers",
            "Test Reviewer when source changed",
        )
        self.assertTrue(self.validate(text))

    def test_rejects_missing_harness_transport_split(self) -> None:
        text = self.skill_text.replace("**Codex / Cursor:** inline both into the child prompt", "inline always")
        self.assertTrue(self.validate(text))

    def test_rejects_missing_standalone_plugin_detection(self) -> None:
        text = self.skill_text.replace(
            ", or root `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` manifests (standalone plugin)",
            "",
        )
        self.assertTrue(self.validate(text))


class ReviewerParityTests(unittest.TestCase):
    def test_rejects_reviewer_missing_from_claude_surface(self) -> None:
        errors: list[str] = []
        VALIDATOR.validate_reviewer_surface_parity(
            codex_reviewers={"bug-hunter", "frontload-core"},
            claude_reviewers={"bug-hunter"},
            opencode_reviewers={"bug-hunter", "frontload-core"},
            cursor_reviewers={"bug-hunter", "frontload-core"},
            errors=errors,
        )

        self.assertIn("missing Claude reviewer agents: frontload-core", errors)

    def test_rejects_reviewer_missing_from_opencode_surface(self) -> None:
        errors: list[str] = []
        VALIDATOR.validate_reviewer_surface_parity(
            codex_reviewers={"bug-hunter", "frontload-core"},
            claude_reviewers={"bug-hunter", "frontload-core"},
            opencode_reviewers={"bug-hunter"},
            cursor_reviewers={"bug-hunter", "frontload-core"},
            errors=errors,
        )

        self.assertIn("missing opencode reviewer agents: frontload-core", errors)

    def test_rejects_reviewer_missing_from_cursor_surface(self) -> None:
        errors: list[str] = []
        VALIDATOR.validate_reviewer_surface_parity(
            codex_reviewers={"bug-hunter", "frontload-core"},
            claude_reviewers={"bug-hunter", "frontload-core"},
            opencode_reviewers={"bug-hunter", "frontload-core"},
            cursor_reviewers={"bug-hunter"},
            errors=errors,
            expected_reviewers={"bug-hunter", "frontload-core"},
        )

        self.assertIn("missing Cursor reviewer roles: frontload-core", errors)


class SharedCoreTests(unittest.TestCase):
    def test_accepts_harness_adapter_wiring(self) -> None:
        errors: list[str] = []
        VALIDATOR.validate_harness_adapters(errors)
        self.assertEqual(errors, [])

    def test_rejects_missing_role_in_cursor_adapter(self) -> None:
        path = VALIDATOR.SKILL_ROOT / "references" / "cursor.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(original.replace("| `bug-hunter.md` |", "| `removed.md` |"), encoding="utf-8")
            errors: list[str] = []
            VALIDATOR.validate_harness_adapters(errors)
            self.assertTrue(any("'bug-hunter'" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")


class ThinShellTests(unittest.TestCase):
    def test_accepts_current_specialist_shells(self) -> None:
        errors: list[str] = []
        VALIDATOR.validate_thin_shells(errors)
        self.assertEqual(errors, [])

    def test_rejects_fat_specialist_body(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "agents" / "bug-hunter.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(original + ("\n" + "x" * VALIDATOR.MAX_SHELL_BODY_CHARS), encoding="utf-8")
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("exceeds" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_repo_relative_specialist_prompt_marker(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "agents" / "bug-hunter.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(
                original.replace(
                    "${CLAUDE_PLUGIN_ROOT}/skills/parallel-review/references/reviewers/bug-hunter.md",
                    "skills/parallel-review/references/reviewers/bug-hunter.md",
                ),
                encoding="utf-8",
            )
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("plugin-absolute path" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_opencode_orchestrator_repo_local_fallback(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "opencode" / "commands" / "parallel-review.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(original + '\nAlso try "$(pwd)/.opencode" as fallback.\n', encoding="utf-8")
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("must not trust repo-local" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_shared_root_shell_assignment_without_task_injection(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "opencode" / "commands" / "parallel-review.md"
        original = path.read_text(encoding="utf-8")
        weakened = original.replace(
            "include the absolute `SHARED_ROOT=<path>` line in every Task prompt so bash-denied children do not rediscover it.",
            "Set SHARED_ROOT= locally before continuing.",
        )
        try:
            path.write_text(weakened, encoding="utf-8")
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("Task prompt payload" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_opencode_adapter_without_task_shared_root_payload(self) -> None:
        path = VALIDATOR.SKILL_ROOT / "references" / "opencode.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(
                original.replace(
                    "SHARED_ROOT=<absolute path from orchestrator resolution>",
                    "SHARED_ROOT=$HOME/.config/opencode/skills/parallel-review",
                ),
                encoding="utf-8",
            )
            errors: list[str] = []
            VALIDATOR.validate_harness_adapters(errors)
            self.assertTrue(any("Task prompt payload" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_positive_rediscovery_wording(self) -> None:
        path = VALIDATOR.SKILL_ROOT / "references" / "opencode.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(
                original.replace(
                    "Do **not** require specialists to rediscover `$SHARED_ROOT`",
                    "Always require specialists to rediscover `$SHARED_ROOT`",
                ),
                encoding="utf-8",
            )
            errors: list[str] = []
            VALIDATOR.validate_harness_adapters(errors)
            self.assertTrue(any("forbid specialist SHARED_ROOT rediscovery" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_external_directory_allow_only_in_body(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "opencode" / "agents" / "bug-hunter.md"
        original = path.read_text(encoding="utf-8")
        frontmatter, body = VALIDATOR.split_frontmatter(original)
        weakened_frontmatter = frontmatter.replace(
            "external_directory: allow",
            "external_directory: deny",
        )
        try:
            path.write_text(
                weakened_frontmatter + "Note external_directory: allow in prose.\n" + body,
                encoding="utf-8",
            )
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("external_directory" in error and "bug-hunter" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_external_directory_inside_scalar_description(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "opencode" / "agents" / "bug-hunter.md"
        original = path.read_text(encoding="utf-8")
        frontmatter, body = VALIDATOR.split_frontmatter(original)
        # Remove the real permission key; leave allow only inside a scalar value.
        poisoned = frontmatter.replace("  external_directory: allow\n", "").replace(
            "description: INTERNAL — invoked only by the /parallel-review orchestrator. Do not invoke directly; invoke /parallel-review instead. Reviews changed code for runtime bugs.\n",
            "description: |\n  INTERNAL agent.\n  external_directory: allow\n",
        )
        try:
            path.write_text(poisoned + body, encoding="utf-8")
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("external_directory" in error and "bug-hunter" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_duplicate_external_directory_keys(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "opencode" / "agents" / "bug-hunter.md"
        original = path.read_text(encoding="utf-8")
        frontmatter, body = VALIDATOR.split_frontmatter(original)
        duplicated = frontmatter.replace(
            "  external_directory: allow\n",
            "  external_directory: allow\n  external_directory: allow\n",
        )
        try:
            path.write_text(duplicated + body, encoding="utf-8")
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("external_directory" in error and "bug-hunter" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_top_level_external_directory_without_permission(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "opencode" / "agents" / "bug-hunter.md"
        original = path.read_text(encoding="utf-8")
        frontmatter, body = VALIDATOR.split_frontmatter(original)
        weakened = frontmatter.replace("  external_directory: allow\n", "").replace(
            "permission:\n",
            "external_directory: allow\npermission:\n",
        )
        try:
            path.write_text(weakened + body, encoding="utf-8")
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("external_directory" in error and "bug-hunter" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_disconnected_shared_root_phrases(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "opencode" / "agents" / "bug-hunter.md"
        original = path.read_text(encoding="utf-8")
        frontmatter, body = VALIDATOR.split_frontmatter(original)
        weakened = body.replace(
            "Require an absolute `SHARED_ROOT=...` line from the orchestrator Task prompt. Do not rediscover the path and do not read repository-relative skill files.",
            "Mention $SHARED_ROOT somewhere.\n\nDo not rediscover unrelated state.\n\nRequire an absolute path for something else.",
        )
        try:
            path.write_text(frontmatter + weakened, encoding="utf-8")
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("must require injected SHARED_ROOT" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_opencode_specialist_bash_allow(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "opencode" / "agents" / "bug-hunter.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(original.replace("bash: deny", "bash: allow"), encoding="utf-8")
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("bash: deny" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")

    def test_rejects_primary_external_directory_allow_only_in_body(self) -> None:
        path = VALIDATOR.PLUGIN_ROOT / "opencode" / "agents" / "reviewer.md"
        original = path.read_text(encoding="utf-8")
        frontmatter, body = VALIDATOR.split_frontmatter(original)
        weakened_frontmatter = frontmatter.replace(
            "external_directory: allow",
            "external_directory: deny",
        )
        try:
            path.write_text(
                weakened_frontmatter + "Set external_directory: allow somehow.\n" + body,
                encoding="utf-8",
            )
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("primary agent must allow external_directory" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")


class OpenCodeInstallTests(unittest.TestCase):
    def test_install_only_migrates_exact_legacy_links_in_every_scope_and_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            project.mkdir()
            env = {**os.environ, "HOME": str(home)}

            for scope, target, cwd, argv in (
                (
                    "global",
                    home / ".config" / "opencode",
                    PLUGIN_ROOT,
                    ("install",),
                ),
                (
                    "project",
                    project / ".opencode",
                    project,
                    ("install", "--project"),
                ),
            ):
                links = (
                    ("agents", "reviewer.md"),
                    ("commands", "parallel-review.md"),
                    ("skills", "parallel-review"),
                )
                for category, name in links:
                    link = target / category / name
                    link.parent.mkdir(parents=True, exist_ok=True)
                    link.symlink_to(
                        root
                        / "agent-plugins"
                        / "plugins"
                        / "reviewer"
                        / "opencode"
                        / category
                        / name
                    )

                foreign = target / "agents" / "bug-hunter.md"
                foreign_target = PLUGIN_ROOT / "opencode" / ".." / ".." / f"{scope}-foreign.md"
                foreign.symlink_to(foreign_target)

                install = subprocess.run(
                    [str(INSTALL_OPENCODE), *argv],
                    cwd=cwd,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(install.returncode, 0, install.stderr)
                for category, name in links:
                    self.assertEqual(
                        (target / category / name).readlink(),
                        PLUGIN_ROOT / "opencode" / category / name,
                    )
                self.assertEqual(foreign.readlink(), foreign_target)

    def test_global_install_and_uninstall_only_touch_owned_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            target = home / ".config" / "opencode"
            foreign = target / "commands" / "foreign.md"
            foreign.parent.mkdir(parents=True)
            foreign.symlink_to(home / "foreign.md")
            env = {**os.environ, "HOME": str(home)}

            install = subprocess.run(
                [str(INSTALL_OPENCODE), "install"],
                cwd=PLUGIN_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertTrue((target / "agents" / "reviewer.md").is_symlink())
            self.assertTrue((target / "commands" / "parallel-review.md").is_symlink())

            uninstall = subprocess.run(
                [str(INSTALL_OPENCODE), "uninstall"],
                cwd=PLUGIN_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertFalse((target / "agents" / "reviewer.md").exists())
            self.assertFalse((target / "commands" / "parallel-review.md").exists())
            self.assertTrue(foreign.is_symlink())

    def test_project_install_list_and_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            env = {**os.environ, "HOME": str(Path(tmp) / "home")}

            install = subprocess.run(
                [str(INSTALL_OPENCODE), "install", "--project"],
                cwd=project,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertTrue((project / ".opencode" / "agents" / "reviewer.md").is_symlink())

            listed = subprocess.run(
                [str(INSTALL_OPENCODE), "list", "--project"],
                cwd=project,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertIn("Reviewer installed:", listed.stdout)

            uninstall = subprocess.run(
                [str(INSTALL_OPENCODE), "uninstall", "--project"],
                cwd=project,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertFalse((project / ".opencode" / "agents" / "reviewer.md").exists())

    def test_rejects_invalid_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for argv in (("install", "reviewer"), ("list", "--project", "extra"), ("unknown",)):
                result = subprocess.run(
                    [str(INSTALL_OPENCODE), *argv],
                    cwd=PLUGIN_ROOT,
                    env={**os.environ, "HOME": tmp},
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0, argv)

    def test_preserves_traversal_target_at_reviewer_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            command = home / ".config" / "opencode" / "commands" / "parallel-review.md"
            command.parent.mkdir(parents=True)
            foreign_target = PLUGIN_ROOT / "opencode" / ".." / ".." / "foreign.md"
            command.symlink_to(foreign_target)
            env = {**os.environ, "HOME": str(home)}

            install = subprocess.run(
                [str(INSTALL_OPENCODE), "install"],
                cwd=PLUGIN_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertEqual(command.readlink(), foreign_target)

            uninstall = subprocess.run(
                [str(INSTALL_OPENCODE), "uninstall"],
                cwd=PLUGIN_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertEqual(command.readlink(), foreign_target)

    def test_rejects_monorepo_command_suffix(self) -> None:
        path = PLUGIN_ROOT / "opencode" / "commands" / "parallel-review.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(
                original.replace(
                    "*/opencode/commands/parallel-review.md)",
                    "*/plugins/reviewer/opencode/commands/parallel-review.md)",
                ),
                encoding="utf-8",
            )
            errors: list[str] = []
            VALIDATOR.validate_thin_shells(errors)
            self.assertTrue(any("standalone command suffix" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")


class StandalonePackagingTests(unittest.TestCase):
    def test_manifests_name_standalone_repository(self) -> None:
        expected = "https://github.com/psjostrom/reviewer"
        for path in (
            PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
            PLUGIN_ROOT / ".cursor-plugin" / "plugin.json",
        ):
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")).get("repository"),
                expected,
            )

    def test_domain_wiring_accepts_catalog_and_standalone_roots(self) -> None:
        errors: list[str] = []
        VALIDATOR.validate_domain_reviewer_wiring(
            VALIDATOR.SKILL_ROOT.joinpath("SKILL.md").read_text(encoding="utf-8"),
            VALIDATOR.SKILL_ROOT / "SKILL.md",
            errors,
        )
        self.assertEqual(errors, [])


class ValidatorOutputTests(unittest.TestCase):
    def test_failure_banner_matches_bundle_scope(self) -> None:
        stderr = io.StringIO()

        def fail_parity(errors: list[str]) -> None:
            errors.append("forced parity failure")

        with mock.patch.object(VALIDATOR, "validate_cross_platform_reviewer_parity", side_effect=fail_parity):
            with contextlib.redirect_stderr(stderr):
                status = VALIDATOR.main()

        self.assertEqual(status, 1)
        self.assertIn("Reviewer validation failed:", stderr.getvalue())
        self.assertNotIn("Codex reviewer validation failed:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
