"""Quick S2 v2 validation run — saves outputs, prints model reasons for failures."""
import json, sys, shutil
from pathlib import Path

PHASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHASE / "scripts"))
from run_p7c_batch_ds import build_s2_prompt, call_model, read_json  # type: ignore

V2_PROMPT = (PHASE / "phases/P7C/prompts/kg_boundary_adjudication_v2.md").read_text(encoding="utf-8-sig")
PACKAGES = PHASE / "phases/P7B/section_packages"
EXPECTED_RAW = json.loads((PHASE / "phases/P7C/tests/s2_kg_projection_v1/expected_decisions.json").read_text(encoding="utf-8"))
EXPECTED = EXPECTED_RAW["sections"]

S1_DIRS = [
    PHASE / "phases/P7C/outputs/p7c_s11_s12_smoke_v2_20260714",
    PHASE / "phases/P7C/outputs/p7c_s11_s12_holdout_v1_20260714",
]
SECTION_IDS = ["CH02-S04", "CH06-S10", "CH07-S03", "CH08-S05"]

OUT = PHASE / "phases/P7C/outputs/s2_v2_check"
if OUT.exists():
    shutil.rmtree(str(OUT))
OUT.mkdir(parents=True)


def load_s1(section_id: str) -> list[dict]:
    for d in S1_DIRS:
        f = d / section_id / "s1_propositions.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))["propositions"]
    raise FileNotFoundError(section_id)


def parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw)


def main():
    all_ok = True
    for section_id in SECTION_IDS:
        task = read_json(PACKAGES / section_id / "task.json")
        props = load_s1(section_id)
        prompt = build_s2_prompt(V2_PROMPT, task, props, kg_input_version="projection_v1")
        raw, meta = call_model(prompt, "deepseek-v4-pro", 20000, 240.0, "none")
        result = parse_json(raw)

        sdir = OUT / section_id
        sdir.mkdir(parents=True)
        (sdir / "prompt.md").write_text(prompt, encoding="utf-8")
        (sdir / "response.raw.txt").write_text(raw, encoding="utf-8")
        (sdir / "response.parsed.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        actual = {str(r["candidate_id"]): r["decision"] for r in result.get("boundary_decisions", [])}
        exp = EXPECTED[section_id]["decisions"]

        correct = sum(actual.get(cid) == exp[cid] for cid in exp)
        wrong_kg = [cid for cid, d in exp.items() if d == "p7c_candidate" and actual.get(cid) == "kg_only"]
        wrong_p7c = [cid for cid, d in exp.items() if d == "kg_only" and actual.get(cid) == "p7c_candidate"]

        print(f"{section_id}: {correct}/{len(exp)} correct", end="")
        if wrong_kg or wrong_p7c:
            all_ok = False
            print()
            for cid in exp:
                if actual.get(cid) == exp[cid]:
                    continue
                print(f"  X {cid}: expected={exp[cid]} actual={actual.get(cid, '?')}")
                for dec in result.get("boundary_decisions", []):
                    if dec.get("candidate_id") == cid:
                        rsn = dec.get("reason", "N/A")
                        print(f"    reason: {rsn[:300]}")
        else:
            print("  OK")

    print(f"\nOutputs: {OUT}")
    if all_ok:
        print("PASS")
    else:
        print("FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
