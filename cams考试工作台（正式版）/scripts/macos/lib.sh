#!/bin/bash
# Shared helpers for CAMS macOS M3 delivery scripts.
set -euo pipefail

script_dir() { cd "$(dirname "$1")" && pwd; }
workbench_root() { cd "$(script_dir "$1")/../.." && pwd; }
install_root() { printf '%s\n' "${CAMS_INSTALL_ROOT:-$HOME/CAMS考试工作台}"; }

require_m3_platform() {
  if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "arm64" ]; then
    echo "This delivery only supports macOS Apple Silicon (arm64)." >&2
    exit 1
  fi
}

python_bin() {
  local root="$1"
  if [ -x "$root/runtime/python/bin/python3" ]; then
    printf '%s\n' "$root/runtime/python/bin/python3"
  elif [ -x "$root/runtime/python/bin/python3.11" ]; then
    printf '%s\n' "$root/runtime/python/bin/python3.11"
  else
    return 1
  fi
}

require_runtime() {
  local root="$1"
  local python
  python="$(python_bin "$root")" || { echo "Missing bundled macOS Python runtime. Run build-package.command on an M3 Mac first." >&2; exit 1; }
  if [ ! -d "$root/runtime/models/bge-m3" ]; then
    echo "Missing bundled BGE-M3 model: $root/runtime/models/bge-m3" >&2
    exit 1
  fi
  printf '%s\n' "$python"
}

write_project_mcp_config() {
  local root="$1" python="$2" config="$root/.codex/config.toml"
  mkdir -p "$root/.codex"
  if [ -f "$config" ] && grep -q '^\[mcp_servers.cams_workbench\]' "$config"; then
    echo "Existing CAMS project MCP configuration retained: $config"
    return
  fi
  if [ -f "$config" ]; then
    cp "$config" "$config.backup-$(date +%Y%m%d-%H%M%S)"
  fi
  cat >> "$config" <<EOF

[mcp_servers.cams_workbench]
command = "$python"
args = ["$root/backend/mcp_server.py", "--workspace-root", "$root"]
env = { CAMS_WORKSPACE_ROOT = "$root", CAMS_BGE_MODEL_PATH = "$root/runtime/models/bge-m3" }
EOF
  echo "Project MCP configuration created: $config"
}

run_backup() {
  local root="$1" python="$2" reason="$3"
  "$python" "$root/backend/backup.py" --workspace-root "$root" --reason "$reason" >/dev/null
}
