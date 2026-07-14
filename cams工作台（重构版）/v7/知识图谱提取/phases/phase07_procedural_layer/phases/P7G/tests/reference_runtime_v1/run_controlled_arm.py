from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = TEST_DIR.parents[3]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["baseline", "variant"], required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if args.arm == "baseline":
        baseline_path = Path(args.baseline_ref) if args.baseline_ref else TEST_DIR / "baseline_behavior.json"
        observed = json.loads(baseline_path.read_text(encoding="utf-8"))
        result = {
            "arm": "baseline",
            "tests_passed": True,
            "desired_contract_satisfied": False,
            "observed": observed,
            "failed_contracts": [
                "REFERENCES display is not auxiliary-to-process",
                "REFERENCES has no reverse proof traversal",
                "renderers do not recognize current node_category values",
                "proof traversal does not apply P7D edge gates",
            ],
        }
        return_code = 0
    else:
        command = [sys.executable, "-m", "unittest", "discover", "-s", str(TEST_DIR), "-p", "test_*.py", "-v"]
        completed = subprocess.run(command, cwd=PHASE_DIR, text=True, capture_output=True, check=False)
        (artifact_dir / "unittest.stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (artifact_dir / "unittest.stderr.txt").write_text(completed.stderr, encoding="utf-8")
        result = {
            "arm": "variant",
            "tests_passed": completed.returncode == 0,
            "desired_contract_satisfied": completed.returncode == 0,
            "test_command": command,
            "return_code": completed.returncode,
        }
        return_code = completed.returncode

    (artifact_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
