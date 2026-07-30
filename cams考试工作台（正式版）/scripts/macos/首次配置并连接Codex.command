#!/bin/bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"

require_m3_platform
source_root="$(workbench_root "$0")"
target_root="$(install_root)"

if [ "$source_root" != "$target_root" ]; then
  if [ -e "$target_root" ]; then
    echo "Existing workbench found at: $target_root" >&2
    echo "It was not overwritten. Re-run this script from that directory, or choose another CAMS_INSTALL_ROOT." >&2
    exit 1
  fi
  mkdir -p "$(dirname "$target_root")"
  ditto "$source_root" "$target_root"
fi

root="$target_root"
xattr -dr com.apple.quarantine "$root" 2>/dev/null || true
chmod +x "$root"/scripts/macos/*.command
python="$(require_runtime "$root")"

"$python" -c "import numpy, sklearn, sentence_transformers, torch; print('Python retrieval runtime ready.')"
write_project_mcp_config "$root" "$python"
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n' | "$python" "$root/backend/mcp_server.py" --workspace-root "$root" | grep -q 'list_questions'
run_backup "$root" "$python" "first-configuration"

echo "CAMS initial configuration is complete. Open the CAMS project folder in Codex, then reopen Codex so it loads .codex/config.toml."
echo "Daily use: double-click 启动工作台.command."
