from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


SCRIPT_FILE = Path(__file__).resolve()
PHASE_DIR = next(parent for parent in SCRIPT_FILE.parents if (parent / "scripts" / "run_p7c_batch_ds.py").exists())
RUNNER_PATH = PHASE_DIR / "scripts" / "run_p7c_batch_ds.py"
SPEC = importlib.util.spec_from_file_location("run_p7c_batch_ds", RUNNER_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run coverage adjudication against an existing P7C JSON output.")
    parser.add_argument("--cards", required=True)
    parser.add_argument("--section-package", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--prompt",
        default=str(RUNNER.DEFAULT_COVERAGE_ADJUDICATION_PROMPT_PATH),
    )
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--raw-response", help="Reuse an existing adjudication raw response instead of calling the model.")
    parser.add_argument("--thinking-effort", default="none", choices=["none", "low", "medium", "high"])
    parser.add_argument("--max-tokens", type=int, default=20000)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--validation-retries", type=int, default=1)
    args = parser.parse_args()

    cards_path = Path(args.cards)
    package_path = Path(args.section_package)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    original = RUNNER.read_json(cards_path)
    task = RUNNER.read_json(package_path)
    prompt_template = Path(args.prompt).read_text(encoding="utf-8-sig")
    prompt = RUNNER.build_coverage_adjudication_prompt(prompt_template, task, original)
    prompt_path = output_dir / "coverage_adjudication.prompt.md"
    raw_path = output_dir / "coverage_adjudication.raw.txt"
    candidate_path = output_dir / "coverage_adjudication.cards.json"
    contract_report_path = output_dir / "coverage_adjudication.contract.md"
    validation_report_path = output_dir / "coverage_adjudication.validation.md"
    result_path = output_dir / "result.json"
    prompt_path.write_text(prompt, encoding="utf-8")

    if args.raw_response:
        raw = Path(args.raw_response).read_text(encoding="utf-8-sig")
        call_meta = {"source": "reused_raw_response", "path": RUNNER.path_for_json(Path(args.raw_response))}
    else:
        raw, call_meta = RUNNER.call_model(
            prompt,
            model=args.model,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            thinking_effort=args.thinking_effort,
        )
    raw_path.write_text(raw + "\n", encoding="utf-8")
    adjudicated = RUNNER.parse_json_object(raw)
    if adjudicated is None:
        RUNNER.write_json(result_path, {"status": "parse_failed", "call_meta": call_meta})
        raise SystemExit("Coverage adjudication response was not valid JSON.")

    normalizations = RUNNER.normalize_new_adjudicated_cards(original, adjudicated)
    contract_errors = RUNNER.validate_coverage_adjudication(original, adjudicated)
    contract_lines = [
        "# P7C Existing Coverage Adjudication Contract Report",
        "",
        f"error_count: {len(contract_errors)}",
        "",
    ]
    if contract_errors:
        contract_lines.extend(["## Errors", ""])
        contract_lines.extend(f"- {error}" for error in contract_errors)
    else:
        contract_lines.append("No contract errors.")
    contract_report_path.write_text("\n".join(contract_lines) + "\n", encoding="utf-8")
    RUNNER.write_json(candidate_path, adjudicated)

    validator_code, validator_output, validation_error_count = RUNNER.validate_cards(
        candidate_path,
        validation_report_path,
        package_path,
    )
    validation_attempts: list[dict] = [
        {
            "attempt": 0,
            "contract_error_count": len(contract_errors),
            "validation_error_count": validation_error_count,
        }
    ]
    for repair_attempt in range(1, max(0, args.validation_retries) + 1):
        if contract_errors or validator_code != 0 or validation_error_count is None or validation_error_count == 0:
            break
        validation_report = validation_report_path.read_text(encoding="utf-8-sig")
        previous_json = candidate_path.read_text(encoding="utf-8-sig")
        repair_prompt = f"""{prompt}

## 裁决JSON结构修复

裁决决定已经完成且保护合同已通过。只修复下列结构校验错误，必须保持所有裁决决定、既有card和新增card的业务内容不变。不得删除提升候选或把它改回`kg_only`。返回完整严格JSON。

validation_report:

```text
{validation_report}
```

previous_adjudication_json:

```json
{previous_json}
```
"""
        repair_prompt_path = output_dir / f"coverage_adjudication.validation_repair_{repair_attempt}.prompt.md"
        repair_raw_path = output_dir / f"coverage_adjudication.validation_repair_{repair_attempt}.raw.txt"
        repair_prompt_path.write_text(repair_prompt, encoding="utf-8")
        repair_raw, repair_meta = RUNNER.call_model(
            repair_prompt,
            model=args.model,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            thinking_effort=args.thinking_effort,
        )
        repair_raw_path.write_text(repair_raw + "\n", encoding="utf-8")
        repaired = RUNNER.parse_json_object(repair_raw)
        if repaired is None:
            validation_attempts.append({"attempt": repair_attempt, "status": "parse_failed"})
            continue
        normalizations.extend(RUNNER.normalize_new_adjudicated_cards(original, repaired))
        repaired_contract_errors = RUNNER.validate_coverage_adjudication(original, repaired)
        if repaired_contract_errors:
            contract_errors = repaired_contract_errors
            validation_attempts.append(
                {
                    "attempt": repair_attempt,
                    "status": "contract_failed",
                    "contract_errors": repaired_contract_errors,
                }
            )
            break
        adjudicated = repaired
        contract_errors = repaired_contract_errors
        RUNNER.write_json(candidate_path, adjudicated)
        validator_code, validator_output, validation_error_count = RUNNER.validate_cards(
            candidate_path,
            validation_report_path,
            package_path,
        )
        validation_attempts.append(
            {
                "attempt": repair_attempt,
                "status": "ok" if validation_error_count == 0 else "validation_failed",
                "validation_error_count": validation_error_count,
                "call_meta": repair_meta,
            }
        )

    contract_lines = [
        "# P7C Existing Coverage Adjudication Contract Report",
        "",
        f"error_count: {len(contract_errors)}",
        "",
    ]
    if contract_errors:
        contract_lines.extend(["## Errors", ""])
        contract_lines.extend(f"- {error}" for error in contract_errors)
    else:
        contract_lines.append("No contract errors.")
    contract_report_path.write_text("\n".join(contract_lines) + "\n", encoding="utf-8")
    original_card_count = len(original.get("cards") or [])
    final_card_count = len(adjudicated.get("cards") or [])
    accepted = not contract_errors and validator_code == 0 and validation_error_count == 0
    result = {
        "status": "accepted" if accepted else "rejected",
        "section_id": original.get("section_id"),
        "original_card_count": original_card_count,
        "final_card_count": final_card_count,
        "promoted_card_count": final_card_count - original_card_count,
        "contract_errors": contract_errors,
        "validation_error_count": validation_error_count,
        "validator_output": validator_output,
        "validation_attempts": validation_attempts,
        "normalizations": normalizations,
        "call_meta": call_meta,
        "source_cards_path": RUNNER.path_for_json(cards_path),
        "section_package_path": RUNNER.path_for_json(package_path),
        "candidate_path": RUNNER.path_for_json(candidate_path),
    }
    RUNNER.write_json(result_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not accepted:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
