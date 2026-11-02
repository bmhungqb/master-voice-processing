#!/usr/bin/env bash
# Clone CopyNE at a fixed commit and build a Python 3.10 venv with the pinned requirements.
# Usage: WORK=/content/work bash setup_env.sh        (defaults to ./work next to this script)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${WORK:-$HERE/work}"
REPO="${REPO:-$WORK/CopyNE}"
VENV="${VENV:-$WORK/venv310}"
COMMIT=e6c0c574421f4b251e7693d9fc3bf4749e29aeeb   # upstream HEAD on 2024-06-03

mkdir -p "$WORK"
[ -d "$REPO/.git" ] || git clone https://github.com/zsLin177/CopyNE.git "$REPO"
git -C "$REPO" checkout -q "$COMMIT"

command -v uv >/dev/null 2>&1 || pip install -q uv
# Python 3.10 on purpose: the code needs torch 2.0.1 (no wheels for Python >= 3.12) and imports `imp`.
[ -x "$VENV/bin/python" ] || uv venv --python 3.10 "$VENV"
uv pip install --python "$VENV/bin/python" -r "$HERE/requirements-eval.txt"

"$VENV/bin/python" - <<'PY'
import torch, torchaudio
print("torch", torch.__version__, "| torchaudio", torchaudio.__version__, "| cuda available:", torch.cuda.is_available())
PY
echo "REPO=$REPO"
echo "VENV=$VENV"
