"""Run one question through the option-level pipeline."""

import argparse

import run_step1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single CAMS question through step1.")
    parser.add_argument("--id", default="2.1_1", help="Question id to run. Default: 2.1_1")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing valid output.")
    parser.add_argument(
        "--retrieval",
        choices=["baseline", "agentic"],
        default="agentic",
        help="Retrieval mode. Default: agentic",
    )
    parser.add_argument("--card-scan", choices=["off", "correct", "all"], default="correct")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(
        run_step1.main(ids=[args.id], limit=1, force=args.force, retrieval_mode=args.retrieval, card_scan_mode=args.card_scan)
    )
