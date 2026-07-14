from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = next(parent for parent in TEST_DIR.parents if (parent / "scripts" / "run_p7c_batch_ds.py").exists())
V4_RUNNER_PATH = PHASE_DIR / "phases" / "P7C" / "tests" / "coverage_decomposition_v4" / "run_patch_rebuild_strict.py"
BASE_PROMPT_PATH = PHASE_DIR / "phases" / "P7C" / "tests" / "coverage_decomposition_v4" / "prompts" / "coverage_patch_v3.md"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V4 = load_module("coverage_decomposition_v4_for_v5", V4_RUNNER_PATH)


def option_value(name: str) -> str | None:
    try:
        index = sys.argv.index(name)
    except ValueError:
        return None
    return sys.argv[index + 1] if index + 1 < len(sys.argv) else None


def prepare_effective_prompt() -> None:
    addendum_path = option_value("--patch-prompt")
    artifact_dir = option_value("--artifact-dir")
    if not addendum_path or not artifact_dir or option_value("--arm") != "variant":
        return
    effective_path = Path(artifact_dir) / "effective_coverage_patch_prompt.md"
    effective_path.parent.mkdir(parents=True, exist_ok=True)
    effective = (
        BASE_PROMPT_PATH.read_text(encoding="utf-8-sig").rstrip()
        + "\n\n"
        + Path(addendum_path).read_text(encoding="utf-8-sig").strip()
        + "\n"
    )
    effective_path.write_text(effective, encoding="utf-8")
    prompt_index = sys.argv.index("--patch-prompt") + 1
    sys.argv[prompt_index] = str(effective_path)


if __name__ == "__main__":
    prepare_effective_prompt()
    raise SystemExit(V4.V3.main())
