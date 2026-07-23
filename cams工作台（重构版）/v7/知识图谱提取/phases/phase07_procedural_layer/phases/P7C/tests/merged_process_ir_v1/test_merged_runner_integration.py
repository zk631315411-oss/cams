from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TEST_FILE = Path(__file__).resolve()
PHASE_DIR = next(
    parent
    for parent in TEST_FILE.parents
    if (parent / "scripts" / "run_p7c_batch_ds.py").exists()
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_module("run_p7c_batch_ds_merged_test", PHASE_DIR / "scripts" / "run_p7c_batch_ds.py")
P7D_VALIDATOR = load_module(
    "validate_and_route_cards_merged_test",
    PHASE_DIR / "scripts" / "validate_and_route_cards.py",
)

SECTION_ID = "TEST-S01"
UNIT_ID = "v7u_TEST001"
QUOTE = "When an event occurs, the institution acts."


def candidate_payload() -> dict:
    return {
        "candidate_id": "s1c_001",
        "unit_ids": [UNIT_ID],
        "proposition": "An event triggers an institutional action.",
        "source_quotes": [QUOTE],
        "relation_cues": ["when"],
        "candidate_frame": {
            "trigger_or_context": ["An event occurs"],
            "basis_or_condition": [],
            "focal_handling_or_judgment": "The institution acts",
            "outcomes_or_paths": [],
        },
        "evidence_spans": [{"unit_id": UNIT_ID, "quote": QUOTE}],
        "induction": None,
        "cross_unit_basis": None,
    }


def process_ir_payload() -> dict:
    return {
        "section_id": SECTION_ID,
        "episodes": [
            {
                "episode_id": "ep_001",
                "source_candidate_ids": ["s1c_001"],
                "focal_question": "How does the institution act after the event?",
                "title": "Event triggers institutional action",
                "card_nature": "execution",
                "elements": [
                    {
                        "element_id": "e001",
                        "role": "context",
                        "node_type": "E1_event_signal",
                        "label": "An event occurs",
                        "evidence_unit_ids": [UNIT_ID],
                        "modality": None,
                    },
                    {
                        "element_id": "e002",
                        "role": "action",
                        "node_type": "P2_execution",
                        "label": "The institution acts",
                        "evidence_unit_ids": [UNIT_ID],
                        "modality": None,
                    },
                ],
                "relations": [
                    {
                        "relation_id": "r001",
                        "kind": "trigger",
                        "trigger_mode": "event",
                        "trigger_element_id": "e001",
                        "process_element_id": "e002",
                        "condition": None,
                        "evidence_unit_ids": [UNIT_ID],
                        "source_quote": QUOTE,
                    }
                ],
                "split_reason": None,
            }
        ],
        "candidate_audit": [
            {
                "candidate_id": "s1c_001",
                "disposition": "mapped",
                "episode_ids": ["ep_001"],
                "reason": "The candidate supplies the event-to-action relation.",
            }
        ],
        "skip_reason": None,
    }


class MergedRunnerIntegrationTests(unittest.TestCase):
    def test_merged_runner_compiles_and_always_runs_structure_validation(self):
        candidate = candidate_payload()
        task = {
            "section_id": SECTION_ID,
            "section_title": "Merged runner test",
            "section_text_with_unit_anchors": f"[{UNIT_ID}|1] {QUOTE}",
            "units": [
                {
                    "unit_id": UNIT_ID,
                    "en_quote": QUOTE,
                    "knowledge_zh": "An event triggers an institutional action.",
                }
            ],
        }
        responses = iter(
            [
                {
                    "section_id": SECTION_ID,
                    "section_title": "Merged runner test",
                    "propositions": [candidate],
                    "skip_reason": None,
                },
                {
                    "section_id": SECTION_ID,
                    "gap_propositions": [],
                    "skip_reason": "No uncovered candidate frames.",
                },
                process_ir_payload(),
            ]
        )

        def fake_call_model(*_args, **_kwargs):
            return json.dumps(next(responses)), {"model": "fake"}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packages_dir = root / "packages"
            section_dir = packages_dir / SECTION_ID
            section_dir.mkdir(parents=True)
            (section_dir / "task.json").write_text(json.dumps(task), encoding="utf-8")
            run_dir = root / "run"
            with (
                mock.patch.object(RUNNER, "call_model", side_effect=fake_call_model),
                mock.patch.object(
                    RUNNER,
                    "validate_cards",
                    return_value=(0, "validated", 0),
                ) as validate_cards_mock,
            ):
                manifest = RUNNER.run_section_merged_process_ir(
                    SECTION_ID,
                    run_dir,
                    packages_dir,
                    "S1 template",
                    "S1.2 template",
                    "Process IR template",
                    "fake-model",
                    "none",
                    4096,
                    10,
                    1,
                    0,
                    False,
                )

            self.assertEqual(manifest["status"], "ok")
            self.assertEqual(
                manifest["structure_validation_owner"],
                "P7C_required_merged_process_ir",
            )
            validate_cards_mock.assert_called_once()
            self.assertTrue((run_dir / SECTION_ID / "process_ir.json").exists())
            self.assertTrue((run_dir / SECTION_ID / "compile_audit.json").exists())
            self.assertTrue((run_dir / SECTION_ID / "cards.raw.json").exists())

    def test_compiled_card_is_accepted_by_p7d_structure_validator(self):
        compiler = load_module(
            "process_ir_compiler_for_p7d_test",
            PHASE_DIR / "scripts" / "process_ir_compiler_v1.py",
        )
        card = compiler.compile_process_ir_to_cards(
            process_ir_payload(),
            SECTION_ID,
            "Test",
        )["cards_payload"]["cards"][0]
        package = {
            "section_id": SECTION_ID,
            "units": [{"unit_id": UNIT_ID}],
        }
        schema = json.loads(
            (PHASE_DIR / "inputs" / "procedural_schema_v2.json").read_text(
                encoding="utf-8-sig"
            )
        )
        result = P7D_VALIDATOR.validate_card_structure(card, package, schema)
        self.assertEqual(result["structure_status"], "pass", result)


if __name__ == "__main__":
    unittest.main()
