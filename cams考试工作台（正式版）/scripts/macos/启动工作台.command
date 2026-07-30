#!/bin/bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"

require_m3_platform
root="$(workbench_root "$0")"
python="$(require_runtime "$root")"
port="${CAMS_PORT:-8765}"
url="http://127.0.0.1:$port"

if ! curl --silent --fail "$url/api/health" >/dev/null 2>&1; then
  "$python" "$root/backend/api.py" --workspace-root "$root" --port "$port" >"$root/data/control/api.log" 2>&1 &
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    sleep 1
    if curl --silent --fail "$url/api/health" >/dev/null 2>&1; then break; fi
  done
fi
if ! curl --silent --fail "$url/api/health" >/dev/null 2>&1; then
  echo "The workbench did not start. See $root/data/control/api.log" >&2
  exit 1
fi
open "$url"
