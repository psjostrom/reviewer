#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


SHA_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


def repository_identity(repo_root: Path) -> str:
    remote = subprocess.run(
        ["git", "-C", str(repo_root), "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if remote:
        return remote
    common_dir = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return common_dir


def state_home() -> Path:
    override = os.environ.get("REVIEWER_STATE_HOME")
    if override:
        return Path(override)
    xdg_state = os.environ.get("XDG_STATE_HOME")
    return Path(xdg_state) / "reviewer" if xdg_state else Path.home() / ".local" / "state" / "reviewer"


def receipt_path(args: argparse.Namespace) -> Path:
    identity = {
        "repo": repository_identity(Path(args.repo_root).resolve()),
        "mode": args.mode,
        "target": args.target,
        "paths": sorted(set(args.path)),
    }
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return state_home() / f"{key}.json"


def read_receipt(args: argparse.Namespace) -> None:
    path = receipt_path(args)
    if not path.exists():
        print(json.dumps({"status": "missing"}))
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps({"status": "found", "baseSha": payload["baseSha"], "headSha": payload["headSha"]}))


def record_receipt(args: argparse.Namespace) -> None:
    base_sha = args.base_sha.lower()
    head_sha = args.head_sha.lower()
    if not SHA_RE.fullmatch(base_sha) or not SHA_RE.fullmatch(head_sha):
        raise SystemExit("base and head must be full 40- or 64-character hexadecimal SHAs")

    path = receipt_path(args)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"baseSha": base_sha, "headSha": head_sha}, sort_keys=True) + "\n"
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(json.dumps({"status": "recorded", "baseSha": base_sha, "headSha": head_sha}))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Read or record Reviewer commit baselines.")
    subparsers = result.add_subparsers(dest="command", required=True)
    for command in ("read", "record"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--repo-root", required=True)
        subparser.add_argument("--mode", choices=("pr", "branch"), required=True)
        subparser.add_argument("--target", required=True)
        subparser.add_argument("--path", action="append", default=[])
        if command == "record":
            subparser.add_argument("--base-sha", required=True)
            subparser.add_argument("--head-sha", required=True)
    return result


def main() -> None:
    args = parser().parse_args()
    if args.command == "read":
        read_receipt(args)
    else:
        record_receipt(args)


if __name__ == "__main__":
    main()
