#!/bin/bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"

require_m3_platform
root="$(workbench_root "$0")"
python="$(require_runtime "$root")"
"$python" -c "import numpy, sklearn, sentence_transformers, torch; print('Python dependencies: OK')"
test -f "$root/data/infrastructure/index/manifest.json"
test -f "$root/data/infrastructure/kg/manifest.json"
test -d "$root/runtime/models/bge-m3"
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n' | "$python" "$root/backend/mcp_server.py" --workspace-root "$root" | grep -q 'write_codex_review'
PYTHONPATH="$root/backend" CAMS_BGE_MODEL_PATH="$root/runtime/models/bge-m3" "$python" -c "from retrieval.service import search_evidence; result=search_evidence('$root', 'risk assessment', 1); assert result.get('results'); print('Retrieval smoke test: OK')"
echo "CAMS environment check passed."
