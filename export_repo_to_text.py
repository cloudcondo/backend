#!/usr/bin/env python3
"""
Export a codebase into a single *plain text* file for ChatGPT review.

Usage:
  python export_repo_to_text.py [OUTPUT_PATH]
                                [--max-bytes 200000]
                                [--include-sensitive]
                                [--include-binaries]
                                [--autocommit]
                                [--commit-message "msg"]
                                [--git-include-ignored]
                                [--git-init]

Defaults:
  OUTPUT_PATH: repo_dump.txt
  --max-bytes: 200000 (skip files larger than this; set 0 to disable size check)

Notes:
  - By default, file discovery uses `git ls-files` (tracked files only).
  - With --autocommit, we stage and commit first so new files are tracked.
  - Use --git-include-ignored to force-add ignored files too (careful: secrets).
  - Use --git-init to initialize a repo if none exists.
  - Falls back to walking the directory if Git is unavailable.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

ROOT = Path.cwd()

DEFAULT_MAX_BYTES = 200_000
DEFAULT_OUTPUT = "repo_dump.txt"

SKIP_NAMES = {".DS_Store", "Thumbs.db"}
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "staticfiles",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
SKIP_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".dylib",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".mp3",
    ".wav",
    ".mp4",
    ".mov",
    ".avi",
    ".sqlite",
    ".sqlite3",
    ".db",
}
SENSITIVE_BASENAMES = {".env", ".env.local", ".envrc", ".secrets", "secrets.json"}


def sh(args, check=True, text=True):
    return subprocess.run(
        args,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
        text=text,
    )


def parse_args(argv):
    out_path = Path(DEFAULT_OUTPUT)
    max_bytes = DEFAULT_MAX_BYTES
    include_sensitive = False
    include_binaries = False
    autocommit = False
    commit_message = None
    git_include_ignored = False
    git_init = False

    i = 0
    if i < len(argv) and not argv[i].startswith("-"):
        out_path = Path(argv[i])
        i += 1
    while i < len(argv):
        a = argv[i]
        if a == "--max-bytes" and i + 1 < len(argv):
            try:
                max_bytes = int(argv[i + 1])
            except ValueError:
                pass
            i += 2
            continue
        if a == "--include-sensitive":
            include_sensitive = True
            i += 1
            continue
        if a == "--include-binaries":
            include_binaries = True
            i += 1
            continue
        if a == "--autocommit":
            autocommit = True
            i += 1
            continue
        if a == "--commit-message" and i + 1 < len(argv):
            commit_message = argv[i + 1]
            i += 2
            continue
        if a == "--git-include-ignored":
            git_include_ignored = True
            i += 1
            continue
        if a == "--git-init":
            git_init = True
            i += 1
            continue
        i += 1

    return (
        out_path,
        max_bytes,
        include_sensitive,
        include_binaries,
        autocommit,
        commit_message,
        git_include_ignored,
        git_init,
    )


def ensure_git_repo(git_init: bool) -> bool:
    try:
        res = sh(["git", "rev-parse", "--is-inside-work-tree"])
        return res.stdout.strip() == "true"
    except Exception:
        if not git_init:
            return False
        try:
            sh(["git", "init"])
            print("[info] initialized new Git repository")
            return True
        except Exception as e:
            print(f"[warn] git init failed: {e}", file=sys.stderr)
            return False


def git_autocommit(commit_message: str | None, include_ignored: bool) -> None:
    """Stage and commit all changes locally. Uses inline identity so it never fails on missing config."""
    if not ensure_git_repo(git_init=False):
        # not a repo; nothing to do
        print("[info] not a Git repo; autocommit skipped")
        return
    try:
        # Stage everything normally
        sh(["git", "add", "-A"])
        # Optionally force-add ignored files too
        if include_ignored:
            # '.' ensures recursion; -f forces ignored files in
            sh(["git", "add", "-f", "."])
            # Also pick up currently-ignored tracked deletions/renames
            try:
                ignored = sh(
                    ["git", "ls-files", "-i", "--exclude-standard"]
                ).stdout.splitlines()
                if ignored:
                    # Best-effort force add; ignore failures
                    sh(["git", "add", "-f"] + ignored, check=False)
            except Exception:
                pass

        # Show staged summary for diagnostics
        staged = sh(
            ["git", "diff", "--cached", "--name-only"], check=False
        ).stdout.strip()
        if not staged:
            print("[info] nothing staged; no commit made")
            return

        if not commit_message:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"auto-commit before export ({ts})"

        # Commit with inline identity so global config is not required
        res = sh(
            [
                "git",
                "-c",
                "user.name=Repo Exporter",
                "-c",
                "user.email=exporter@local",
                "commit",
                "-m",
                commit_message,
            ],
            check=False,
        )
        if res.returncode != 0:
            print(res.stdout)
            print(res.stderr, file=sys.stderr)
            raise RuntimeError("git commit failed")
        print(f"[info] Auto-commit created with {len(staged.splitlines())} path(s).")
    except Exception as e:
        print(f"[warn] autocommit skipped: {e}", file=sys.stderr)


def iter_git_files() -> Iterable[Path]:
    try:
        res = sh(["git", "ls-files"])
        for line in res.stdout.splitlines():
            p = ROOT / line.strip()
            if p.is_file():
                yield p
    except Exception:
        # Fallback if Git not available
        for dirpath, dirnames, filenames in os.walk(ROOT):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                yield Path(dirpath) / name


def looks_binary(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(4096)
        return b"\x00" in chunk
    except Exception:
        return True


def should_skip(path: Path, include_sensitive: bool, include_binaries: bool) -> bool:
    if path.name in SKIP_NAMES:
        return True
    if not include_sensitive and path.name in SENSITIVE_BASENAMES:
        return True
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if not include_binaries and path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def write_binary_preview(out, path: Path):
    try:
        with open(path, "rb") as f:
            data = f.read(2048)
        out.write("[binary] first 2KB hex preview ({}) bytes:\n".format(len(data)))
        out.write(data.hex() + "\n")
    except Exception:
        out.write("[binary] <unreadable>\n")


def main():
    (
        out_path,
        max_bytes,
        include_sensitive,
        include_binaries,
        autocommit,
        commit_message,
        git_include_ignored,
        git_init,
    ) = parse_args(sys.argv[1:])

    # Optionally initialize a repo
    if git_init and not ensure_git_repo(git_init=True):
        print(
            "[warn] could not initialize Git; continuing without autocommit",
            file=sys.stderr,
        )

    # Commit first if requested
    if autocommit:
        git_autocommit(commit_message, include_ignored=git_include_ignored)

    files = []
    for p in iter_git_files():
        try:
            rel = p.relative_to(ROOT)
        except Exception:
            rel = p
        if should_skip(
            rel, include_sensitive=include_sensitive, include_binaries=include_binaries
        ):
            continue
        try:
            size = (ROOT / rel).stat().st_size
        except Exception:
            continue
        if max_bytes and size > max_bytes:
            continue
        files.append(rel)

    files.sort()

    sep = "=" * 80
    header = [
        "PROJECT EXPORT (plain text)",
        f"Root: {ROOT}",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"Files included: {len(files)}",
        f"Max bytes per file: {max_bytes if max_bytes else 'no limit'}",
        f"include_sensitive: {include_sensitive}",
        f"include_binaries: {include_binaries}",
        f"autocommit: {autocommit}",
        f"git_include_ignored: {git_include_ignored}",
        "WARNING: If include_sensitive=True, secrets like .env are included in this export.",
        sep,
        "",
    ]
    out_path.write_text("\n".join(header), encoding="utf-8")

    with open(out_path, "a", encoding="utf-8", newline="\n") as out:
        for rel in files:
            abs_path = ROOT / rel
            out.write(f"\n{sep}\nFILE: {rel}\n{sep}\n")
            if include_binaries and looks_binary(abs_path):
                write_binary_preview(out, abs_path)
                continue
            try:
                text = abs_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                if include_binaries:
                    write_binary_preview(out, abs_path)
                continue
            out.write(text.rstrip("\n") + "\n")

    print(f"Wrote {out_path.resolve()} with {len(files)} files.")


if __name__ == "__main__":
    main()
