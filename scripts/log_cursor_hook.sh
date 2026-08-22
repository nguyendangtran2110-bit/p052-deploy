#!/usr/bin/env bash
# Cursor hook wrapper: capture raw hook input for debugging, then delegate to
# the shared AI usage logger. Keep stdout reserved for the hook response JSON.
set +e

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$ROOT" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
  ROOT="$(cd "$SCRIPT_DIR/.." 2>/dev/null && pwd)"
fi

RAW_INPUT="$(cat)"
LOG_DIR="$ROOT/.ai-log"
mkdir -p "$LOG_DIR" 2>/dev/null

{
  printf '%s\n' '--- cursor hook event ---'
  printf 'ts=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null)"
  printf 'cwd=%s\n' "$(pwd)"
  printf 'args=%s\n' "$*"
  printf '%s\n' 'stdin<<EOF'
  printf '%s\n' "$RAW_INPUT"
  printf '%s\n' 'EOF'
} >> "$LOG_DIR/cursor-hook-debug.log" 2>/dev/null

printf '%s' "$RAW_INPUT" | bash "$ROOT/scripts/_pyrun.sh" "$ROOT/scripts/log_hook.py" "$@"
exit $?
