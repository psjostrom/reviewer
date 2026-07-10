#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import io
import importlib.util
import unittest
from unittest import mock
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("validate_codex_reviewer.py")
SPEC = importlib.util.spec_from_file_location("validate_codex_reviewer", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


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

    def test_rejects_frontload_mapping_outside_domain_section(self) -> None:
        mapping = "- Frontload: `frontload-core.md`, `frontload-integration.md`"
        text = self.skill_text.replace(f"{mapping}\n", "")
        text = f"{text}\n<!-- stale documentation: {mapping} -->\n"

        self.assertTrue(self.validate(text))

    def test_rejects_agent_plugins_mapping_outside_domain_section(self) -> None:
        mapping = "- Agent Plugins: `agent-plugins.md`"
        text = self.skill_text.replace(f"{mapping}\n", "")
        text = f"{text}\n<!-- stale documentation: {mapping} -->\n"

        self.assertTrue(self.validate(text))

    def test_rejects_standard_panel_without_matching_domain_reviewers(self) -> None:
        text = self.skill_text.replace(
            "Test Reviewer when source changed, all matching domain reviewers",
            "Test Reviewer when source changed",
        )

        self.assertTrue(self.validate(text))

    def test_rejects_ambiguous_changed_code_detection(self) -> None:
        text = self.skill_text.replace(
            "Detect Frontload only when the repository name is `frontload` or a root package\n"
            "manifest identifies the project as `frontload`.",
            "Detect from repository name and changed code:",
        )

        self.assertTrue(self.validate(text))


class ReviewerParityTests(unittest.TestCase):
    def test_rejects_reviewer_missing_from_claude_surface(self) -> None:
        errors: list[str] = []
        VALIDATOR.validate_reviewer_surface_parity(
            codex_reviewers={"bug-hunter", "frontload-core"},
            claude_reviewers={"bug-hunter"},
            opencode_reviewers={"bug-hunter", "frontload-core"},
            errors=errors,
        )

        self.assertIn("missing Claude reviewer agents: frontload-core", errors)

    def test_rejects_reviewer_missing_from_opencode_surface(self) -> None:
        errors: list[str] = []
        VALIDATOR.validate_reviewer_surface_parity(
            codex_reviewers={"bug-hunter", "frontload-core"},
            claude_reviewers={"bug-hunter", "frontload-core"},
            opencode_reviewers={"bug-hunter"},
            errors=errors,
        )

        self.assertIn("missing opencode reviewer agents: frontload-core", errors)


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
