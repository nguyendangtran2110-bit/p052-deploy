#!/usr/bin/env python3
"""
Scan Codex extension/CLI transcripts and append user prompts to .ai-log/session.jsonl.

This covers the OpenAI Codex extension inside Cursor, which writes local
transcripts under ~/.codex/sessions but is not intercepted by Cursor hooks.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

VN_TZ = timezone(timedelta(hours=7))


def git(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def parse_ts(value: str) -> str:
    if not value:
        return datetime.now(VN_TZ).isoformat()
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(VN_TZ).isoformat()
    except Exception:
        return datetime.now(VN_TZ).isoformat()


def repo_name() -> str:
    origin = git(["git", "remote", "get-url", "origin"])
    if not origin:
        return Path(git(["git", "rev-parse", "--show-toplevel"]) or ".").name
    repo = origin.rstrip("/").split("/")[-1]
    return repo[:-4] if repo.endswith(".git") else repo


def iter_transcripts(codex_sessions: Path):
    if not codex_sessions.exists():
        return
    yield from sorted(codex_sessions.glob("**/*.jsonl"), key=lambda p: p.stat().st_mtime)


def logged_keys(log_file: Path) -> set[str]:
    """Build dedupe keys from session.jsonl so no separate state file is needed."""
    seen = set()
    if not log_file.exists():
        return seen

    with log_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("tool") != "codex" or entry.get("event") != "UserPromptSubmit":
                continue
            transcript_path = entry.get("transcript_path")
            ts = entry.get("ts")
            prompt = entry.get("prompt")
            if transcript_path and ts and prompt:
                seen.add(f"{transcript_path}:{ts}:{prompt[:1000]}")
    return seen


def extract_entries(path: Path, repo_root: str, base: dict, seen: set[str]):
    cwd = ""
    model = "codex"
    session_id = ""

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            payload = row.get("payload") or {}
            row_type = row.get("type")

            if row_type == "session_meta":
                cwd = payload.get("cwd") or cwd
                session_id = payload.get("session_id") or payload.get("id") or session_id
                continue

            if row_type == "event_msg" and payload.get("type") == "thread_settings_applied":
                settings = payload.get("thread_settings") or {}
                model = settings.get("model") or model
                cwd = settings.get("cwd") or cwd
                continue

            if cwd and Path(cwd).resolve() != Path(repo_root).resolve():
                continue

            if row_type != "event_msg" or payload.get("type") != "user_message":
                continue

            prompt = (payload.get("message") or "").strip()
            if not prompt:
                continue

            ts = parse_ts(row.get("timestamp", ""))
            key = f"{path}:{ts}:{prompt[:1000]}"
            if key in seen:
                continue

            yield key, {
                **base,
                "ts": ts,
                "tool": "codex",
                "event": "UserPromptSubmit",
                "session_id": session_id,
                "model": model,
                "prompt": prompt[:1000],
                "turn_id": "",
                "transcript_path": str(path),
            }


def scan_once(args) -> int:
    repo_root = git(["git", "rev-parse", "--show-toplevel"]) or os.getcwd()
    log_dir = Path(os.environ.get("AI_LOG_DIR", ".ai-log"))
    log_file = log_dir / "session.jsonl"
    codex_sessions = Path(args.sessions_dir).expanduser()

    seen = logged_keys(log_file)
    base = {
        "repo": repo_name(),
        "branch": git(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "commit": git(["git", "rev-parse", "--short", "HEAD"]),
        "student": git(["git", "config", "user.email"]),
    }

    entries = []
    for transcript in iter_transcripts(codex_sessions) or []:
        for key, entry in extract_entries(transcript, repo_root, base, seen):
            entries.append(entry)
            seen.add(key)

    if args.dry_run:
        print(json.dumps({"would_log": len(entries), "entries": entries[-5:]}, ensure_ascii=False, indent=2))
        return 0

    if entries:
        log_dir.mkdir(exist_ok=True)
        with log_file.open("a", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"[ai-log] Codex session scan: logged {len(entries)} prompt(s).", file=sys.stderr)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Scan Codex session transcripts into AI log.")
    parser.add_argument("--sessions-dir", default="~/.codex/sessions")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--watch", action="store_true", help="Keep scanning every --interval seconds.")
    parser.add_argument("--interval", type=float, default=10.0)
    args = parser.parse_args()

    if args.watch:
        while True:
            scan_once(args)
            time.sleep(args.interval)
    return scan_once(args)


if __name__ == "__main__":
    sys.exit(main())
