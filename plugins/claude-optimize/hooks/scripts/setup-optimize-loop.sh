#!/bin/bash

# Optimize Loop Setup Script
# Adapted from ralph-loop's setup script for optimize-specific loop

set -euo pipefail

# State file lives in /tmp to avoid polluting the user's repo
STATE_DIR="/tmp/claude-optimize"
mkdir -p "$STATE_DIR"

# Parse arguments
PROMPT_PARTS=()
MAX_ITERATIONS=10
COMPLETION_PROMISE="null"

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      cat << 'HELP_EOF'
Optimize Loop - Guided autonomous optimization loop

USAGE:
  /optimize:loop [OPTIONS]

OPTIONS:
  --max-iterations <n>           Maximum iterations (default: 10)
  --completion-promise '<text>'  Promise phrase for completion
  -h, --help                     Show this help

DESCRIPTION:
  Starts a guided optimization loop. On the first iteration, runs a full
  report and asks for approval. On subsequent iterations, executes approved
  optimizations and re-scores.

EXAMPLES:
  /optimize:loop
  /optimize:loop --max-iterations 20
  /optimize:loop --completion-promise 'All scores above 80' --max-iterations 15
HELP_EOF
      exit 0
      ;;
    --max-iterations)
      if [[ -z "${2:-}" ]] || ! [[ "$2" =~ ^[0-9]+$ ]]; then
        echo "Error: --max-iterations requires a positive integer" >&2
        exit 1
      fi
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --completion-promise)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --completion-promise requires a text argument" >&2
        exit 1
      fi
      COMPLETION_PROMISE="$2"
      shift 2
      ;;
    *)
      PROMPT_PARTS+=("$1")
      shift
      ;;
  esac
done

# Build prompt - use default optimize prompt if none provided
if [[ ${#PROMPT_PARTS[@]} -gt 0 ]]; then
  PROMPT="${PROMPT_PARTS[*]}"
else
  PROMPT="You are running the Claude Optimize autonomous loop. Follow the iteration workflow from the /optimize:loop command instructions. On the first iteration, run a full optimization report and present it to the user for approval. On subsequent iterations, execute approved optimizations and track progress."
fi

STATE_FILE="$STATE_DIR/loop-${CLAUDE_CODE_SESSION_ID:-default}.md"

# Check for existing paused loop
if [[ -f "$STATE_FILE" ]]; then
  EXISTING_FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$STATE_FILE")
  EXISTING_ACTIVE=$(echo "$EXISTING_FRONTMATTER" | grep '^active:' | sed 's/active: *//')
  EXISTING_ITERATION=$(echo "$EXISTING_FRONTMATTER" | grep '^iteration:' | sed 's/iteration: *//')

  if [[ "$EXISTING_ACTIVE" == "false" ]]; then
    # Resume paused loop - set active back to true
    TEMP_FILE="${STATE_FILE}.tmp.$$"
    sed 's/^active: false/active: true/' "$STATE_FILE" > "$TEMP_FILE"
    mv "$TEMP_FILE" "$STATE_FILE"

    echo "Resuming paused optimize loop at iteration $EXISTING_ITERATION."
    echo ""
    # Extract and echo the prompt
    awk '/^---$/{i++; next} i>=2' "$STATE_FILE"
    exit 0
  fi

  # Already active - warn and continue
  echo "Warning: Optimize loop already active at iteration $EXISTING_ITERATION. Continuing." >&2
  awk '/^---$/{i++; next} i>=2' "$STATE_FILE"
  exit 0
fi

if [[ -n "$COMPLETION_PROMISE" ]] && [[ "$COMPLETION_PROMISE" != "null" ]]; then
  COMPLETION_PROMISE_YAML="\"$COMPLETION_PROMISE\""
else
  COMPLETION_PROMISE_YAML="null"
fi

cat > "$STATE_FILE" <<EOF
---
active: true
iteration: 1
session_id: ${CLAUDE_CODE_SESSION_ID:-}
max_iterations: $MAX_ITERATIONS
completion_promise: $COMPLETION_PROMISE_YAML
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
---

$PROMPT
EOF

# Output setup message
cat <<EOF
Optimize loop activated!

Iteration: 1
Max iterations: $MAX_ITERATIONS
Completion promise: $(if [[ "$COMPLETION_PROMISE" != "null" ]]; then echo "$COMPLETION_PROMISE"; else echo "none"; fi)
State file: $STATE_FILE

The stop hook will keep you iterating on optimizations.

To pause: Run the pause script (see loop instructions).
To resume: Run /optimize:loop again.
To cancel: Run the pause script or delete the state file.
EOF

echo ""
echo "$PROMPT"

if [[ "$COMPLETION_PROMISE" != "null" ]]; then
  echo ""
  echo "To complete this loop, output: <promise>$COMPLETION_PROMISE</promise>"
  echo "ONLY when the statement is completely and genuinely TRUE."
fi
