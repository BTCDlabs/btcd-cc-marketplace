#!/bin/bash

# Optimize Loop Stop Hook
# Adapted from ralph-loop's stop-hook.sh
# Prevents session exit when an optimize-loop is active
# Feeds Claude's output back as input to continue the loop

set -euo pipefail

# Read hook input from stdin
HOOK_INPUT=$(cat)

# State file lives in /tmp, keyed by session
HOOK_SESSION=$(echo "$HOOK_INPUT" | jq -r '.session_id // ""')
STATE_DIR="/tmp/claude-optimize"
OPTIMIZE_STATE_FILE="$STATE_DIR/loop-${HOOK_SESSION:-default}.md"

if [[ ! -f "$OPTIMIZE_STATE_FILE" ]]; then
  # No active loop - allow exit
  exit 0
fi

# Parse markdown frontmatter (YAML between ---) and extract values
FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$OPTIMIZE_STATE_FILE")
ACTIVE=$(echo "$FRONTMATTER" | grep '^active:' | sed 's/active: *//')
ITERATION=$(echo "$FRONTMATTER" | grep '^iteration:' | sed 's/iteration: *//')
MAX_ITERATIONS=$(echo "$FRONTMATTER" | grep '^max_iterations:' | sed 's/max_iterations: *//')
COMPLETION_PROMISE=$(echo "$FRONTMATTER" | grep '^completion_promise:' | sed 's/completion_promise: *//' | sed 's/^"\(.*\)"$/\1/')

# Check if loop is active — allow pausing by setting active: false
if [[ "$ACTIVE" != "true" ]]; then
  exit 0
fi

# Session isolation: only the session that started the loop should be blocked
STATE_SESSION=$(echo "$FRONTMATTER" | grep '^session_id:' | sed 's/session_id: *//' || true)
if [[ -n "$STATE_SESSION" ]] && [[ "$STATE_SESSION" != "$HOOK_SESSION" ]]; then
  exit 0
fi

# Validate numeric fields
if [[ ! "$ITERATION" =~ ^[0-9]+$ ]]; then
  echo "Warning: Optimize loop state file corrupted (iteration: '$ITERATION')" >&2
  rm "$OPTIMIZE_STATE_FILE"
  exit 0
fi

if [[ ! "$MAX_ITERATIONS" =~ ^[0-9]+$ ]]; then
  echo "Warning: Optimize loop state file corrupted (max_iterations: '$MAX_ITERATIONS')" >&2
  rm "$OPTIMIZE_STATE_FILE"
  exit 0
fi

# Check if max iterations reached
if [[ $MAX_ITERATIONS -gt 0 ]] && [[ $ITERATION -ge $MAX_ITERATIONS ]]; then
  echo "Optimize loop: Max iterations ($MAX_ITERATIONS) reached."
  rm "$OPTIMIZE_STATE_FILE"
  exit 0
fi

# Get transcript path from hook input
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path')

if [[ ! -f "$TRANSCRIPT_PATH" ]]; then
  echo "Warning: Optimize loop transcript not found" >&2
  rm "$OPTIMIZE_STATE_FILE"
  exit 0
fi

# Read last assistant message from transcript
if ! grep -q '"role":"assistant"' "$TRANSCRIPT_PATH"; then
  echo "Warning: No assistant messages in transcript" >&2
  rm "$OPTIMIZE_STATE_FILE"
  exit 0
fi

LAST_LINES=$(grep '"role":"assistant"' "$TRANSCRIPT_PATH" | tail -n 100)
if [[ -z "$LAST_LINES" ]]; then
  rm "$OPTIMIZE_STATE_FILE"
  exit 0
fi

# Parse last text block
set +e
LAST_OUTPUT=$(echo "$LAST_LINES" | jq -rs '
  map(.message.content[]? | select(.type == "text") | .text) | last // ""
' 2>&1)
JQ_EXIT=$?
set -e

if [[ $JQ_EXIT -ne 0 ]]; then
  echo "Warning: Failed to parse transcript JSON" >&2
  rm "$OPTIMIZE_STATE_FILE"
  exit 0
fi

# Check for completion promise
if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  PROMISE_TEXT=$(echo "$LAST_OUTPUT" | perl -0777 -pe 's/.*?<promise>(.*?)<\/promise>.*/$1/s; s/^\s+|\s+$//g; s/\s+/ /g' 2>/dev/null || echo "")

  if [[ -n "$PROMISE_TEXT" ]] && [[ "$PROMISE_TEXT" = "$COMPLETION_PROMISE" ]]; then
    echo "Optimize loop: Completion promise fulfilled."
    rm "$OPTIMIZE_STATE_FILE"
    exit 0
  fi
fi

# Continue loop - increment iteration
NEXT_ITERATION=$((ITERATION + 1))

# Extract prompt text (everything after closing ---)
PROMPT_TEXT=$(awk '/^---$/{i++; next} i>=2' "$OPTIMIZE_STATE_FILE")

if [[ -z "$PROMPT_TEXT" ]]; then
  echo "Warning: No prompt text in state file" >&2
  rm "$OPTIMIZE_STATE_FILE"
  exit 0
fi

# Update iteration atomically
TEMP_FILE="${OPTIMIZE_STATE_FILE}.tmp.$$"
sed "s/^iteration: .*/iteration: $NEXT_ITERATION/" "$OPTIMIZE_STATE_FILE" > "$TEMP_FILE"
mv "$TEMP_FILE" "$OPTIMIZE_STATE_FILE"

# Build system message
if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  SYSTEM_MSG="Optimize loop iteration $NEXT_ITERATION | To stop: output <promise>$COMPLETION_PROMISE</promise> (ONLY when TRUE)"
else
  SYSTEM_MSG="Optimize loop iteration $NEXT_ITERATION/$MAX_ITERATIONS"
fi

# Block stop and feed prompt back
jq -n \
  --arg prompt "$PROMPT_TEXT" \
  --arg msg "$SYSTEM_MSG" \
  '{
    "decision": "block",
    "reason": $prompt,
    "systemMessage": $msg
  }'

exit 0
