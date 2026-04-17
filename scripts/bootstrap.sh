#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
BIN="$VENV/bin"
LOCAL_BIN="$HOME/.local/bin"

mkdir -p "$LOCAL_BIN"

if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
fi

"$BIN/python" -m pip install -U pip
"$BIN/python" -m pip install -e "$ROOT"

ln -sfn "$BIN/hermes-clip" "$LOCAL_BIN/hermes-clip"

cat <<EOF
Boot done.
- venv: $VENV
- cli:  $LOCAL_BIN/hermes-clip
- run:  hermes-clip serve
EOF
