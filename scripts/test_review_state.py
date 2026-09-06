import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("review_state.py")
BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40
LATER_HEAD_SHA = "3" * 40


class ReviewStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "remote", "add", "origin", "git@github.com:example/project.git"],
            check=True,
        )
        self.env = {**os.environ, "REVIEWER_STATE_HOME": str(self.root / "state")}

    def run_state(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=check,
            capture_output=True,
            text=True,
            env=self.env,
        )

    def test_records_and_reads_a_pr_review_receipt(self) -> None:
        self.run_state(
            "record",
            "--repo-root",
            str(self.repo),
            "--mode",
            "pr",
            "--target",
            "18",
            "--base-sha",
            BASE_SHA,
            "--head-sha",
            HEAD_SHA,
        )

        result = self.run_state(
            "read",
            "--repo-root",
            str(self.repo),
            "--mode",
            "pr",
            "--target",
            "18",
        )

        self.assertEqual(
            json.loads(result.stdout),
            {"status": "found", "baseSha": BASE_SHA, "headSha": HEAD_SHA},
        )

    def test_advances_an_existing_review_receipt(self) -> None:
        common_args = (
            "--repo-root",
            str(self.repo),
            "--mode",
            "pr",
            "--target",
            "18",
            "--base-sha",
            BASE_SHA,
        )
        self.run_state("record", *common_args, "--head-sha", HEAD_SHA)
        self.run_state("record", *common_args, "--head-sha", LATER_HEAD_SHA)

        result = self.run_state(
            "read",
            "--repo-root",
            str(self.repo),
            "--mode",
            "pr",
            "--target",
            "18",
        )

        self.assertEqual(
            json.loads(result.stdout),
            {"status": "found", "baseSha": BASE_SHA, "headSha": LATER_HEAD_SHA},
        )

    def test_scoped_and_unscoped_reviews_have_separate_receipts(self) -> None:
        self.run_state(
            "record",
            "--repo-root",
            str(self.repo),
            "--mode",
            "pr",
            "--target",
            "18",
            "--path",
            "src/api",
            "--base-sha",
            BASE_SHA,
            "--head-sha",
            HEAD_SHA,
        )

        result = self.run_state(
            "read",
            "--repo-root",
            str(self.repo),
            "--mode",
            "pr",
            "--target",
            "18",
        )

        self.assertEqual(json.loads(result.stdout), {"status": "missing"})

    def test_rejects_invalid_shas_without_writing_state(self) -> None:
        result = self.run_state(
            "record",
            "--repo-root",
            str(self.repo),
            "--mode",
            "pr",
            "--target",
            "18",
            "--base-sha",
            "not-a-sha",
            "--head-sha",
            HEAD_SHA,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "state").exists())


if __name__ == "__main__":
    unittest.main()
