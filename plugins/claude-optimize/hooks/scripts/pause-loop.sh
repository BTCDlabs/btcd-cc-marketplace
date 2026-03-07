#!/bin/bash

# Pause or cancel the optimize loop without needing Edit tool approval

set -euo pipefail

STATE_DIR="/tmp/claude-optimize"
STATE_FILE="$STATE_DIR/loop-${CLAUDE_CODE_SESSION_ID:-default}.md"

ACTION="${1:-pause}"

if [[ ! -f "$STATE_FILE" ]]; then
  echo "No active optimize loop found."
  exit 0
fi

case "$ACTION" in
  pause)
    TEMP_FILE="${STATE_FILE}.tmp.$$"
    sed 's/^active: true/active: false/' "$STATE_FILE" > "$TEMP_FILE"
    mv "$TEMP_FILE" "$STATE_FILE"
    echo "Optimize loop paused. Run /optimize:loop to resume."
    ;;
  cancel)
    rm -f "$STATE_FILE"
    echo "Optimize loop cancelled."
    ;;
  status)
    FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$STATE_FILE")
    echo "$FRONTMATTER"
    ;;
  *)
    echo "Usage: pause-loop.sh [pause|cancel|status]" >&2
    exit 1
    ;;
esac
