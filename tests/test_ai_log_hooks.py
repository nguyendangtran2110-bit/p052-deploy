import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_codex_windows_hook_command_logs_prompt(tmp_path):
    hooks = json.loads((REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    command = hooks["hooks"]["UserPromptSubmit"][0]["hooks"][0]["commandWindows"]
    payload = {
        "hook_event_name": "UserPromptSubmit",
        "prompt": "PYTEST_CODEX_WINDOWS_HOOK",
        "turn_id": "pytest-codex-windows-hook",
        "model": "codex",
    }
    env = os.environ.copy()
    env["AI_LOG_DIR"] = str(tmp_path)

    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        input=json.dumps(payload),
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"continue": True}
    entries = [
        json.loads(line)
        for line in (tmp_path / "session.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert entries[-1]["prompt"] == payload["prompt"]
    assert entries[-1]["turn_id"] == payload["turn_id"]
