#!/bin/bash
# Run this only on the target M3 Mac after providing a relocatable CPython 3.11 runtime.
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib.sh"

require_m3_platform
root="$(workbench_root "$0")"
python_home="${CAMS_MAC_PYTHON_HOME:-}"
model_path="${CAMS_MAC_MODEL_PATH:-$root/runtime/models/bge-m3}"
if [ -z "$python_home" ] || [ ! -x "$python_home/bin/python3" ]; then
  echo "Set CAMS_MAC_PYTHON_HOME to a relocatable macOS arm64 CPython 3.11 runtime before building." >&2
  exit 1
fi
if [ ! -f "$model_path/config.json" ]; then
  echo "Set CAMS_MAC_MODEL_PATH to the local BGE-M3 model directory." >&2
  exit 1
fi

python="$python_home/bin/python3"
version="$($python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "$version" != "3.11" ]; then echo "CPython 3.11 is required; found $version." >&2; exit 1; fi

stage="$root/dist/CAMS考试工作台-macos-arm64"
archive="$root/dist/CAMS考试工作台-macos-arm64.tar.gz"
rm -rf "$stage" "$archive"
mkdir -p "$stage" "$stage/wheelhouse/macos-arm64" "$stage/runtime/models"
rsync -a --delete --exclude '.venv' --exclude 'runtime' --exclude 'dist' --exclude '__pycache__' --exclude '.git' "$root/" "$stage/"
ditto "$python_home" "$stage/runtime/python"
ditto "$model_path" "$stage/runtime/models/bge-m3"

build_venv="$(mktemp -d)/cams-build-venv"
trap 'rm -rf "${build_venv%/cams-build-venv}"' EXIT
"$python" -m venv "$build_venv"
build_python="$build_venv/bin/python"
"$build_python" -m pip install --upgrade pip
"$build_python" -m pip install -r "$stage/backend/requirements.txt"
"$build_python" -m pip freeze | sort > "$stage/requirements-macos-arm64.lock"
"$build_python" -m pip download --dest "$stage/wheelhouse/macos-arm64" -r "$stage/requirements-macos-arm64.lock"
stage_python="$stage/runtime/python/bin/python3"
"$stage_python" -m pip install --no-index --find-links "$stage/wheelhouse/macos-arm64" -r "$stage/requirements-macos-arm64.lock"
"$stage_python" -c "import numpy, sklearn, sentence_transformers, torch; print('Portable runtime imports passed')"

chmod +x "$stage"/scripts/macos/*.command
(cd "$stage" && find . -type f -not -name 'manifest.sha256' -exec shasum -a 256 {} \; | sort) > "$stage/manifest.sha256"
(cd "$root/dist" && tar -czf "$(basename "$archive")" "$(basename "$stage")")
shasum -a 256 "$archive" > "$archive.sha256"
echo "M3 package prepared: $archive"
echo "Run the full acceptance checklist on a clean M3 account before calling it a formal release."
