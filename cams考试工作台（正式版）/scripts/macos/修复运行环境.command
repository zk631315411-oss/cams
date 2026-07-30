#!/bin/bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"

require_m3_platform
root="$(workbench_root "$0")"
python="$(require_runtime "$root")"
wheelhouse="$root/wheelhouse/macos-arm64"
lockfile="$root/requirements-macos-arm64.lock"

run_backup "$root" "$python" "before-repair"
if [ -d "$wheelhouse" ] && [ -f "$lockfile" ]; then
  "$python" -m pip install --no-index --find-links "$wheelhouse" -r "$lockfile"
  "$root/scripts/macos/检查环境.command"
  exit 0
fi

echo "Offline repair assets are missing. This source bundle is not a validated M3 release." >&2
read -r -p "Use the Tsinghua PyPI mirror for an explicit online repair? [y/N] " answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
  "$python" -m pip install --upgrade -r "$root/backend/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
  "$root/scripts/macos/检查环境.command"
fi
