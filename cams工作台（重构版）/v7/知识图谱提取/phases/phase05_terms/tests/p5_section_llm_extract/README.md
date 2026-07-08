# P5 section-level LLM extraction test

This directory tests whether an LLM can extract P5 dictionary candidates directly from CAMS v7 section text.

P5 is only a term dictionary layer:

```text
1. abbreviation <-> full form
2. Chinese <-> English
3. aliases / synonyms
4. occurrence evidence / location index
```

P5 does not create core points, CP relations, KG logic edges, or replacements for P3/P4.

## Inputs

```text
phases/phase01_chapter_index/outputs/all_chapters_units.jsonl
phases/phase00_quality_gate/outputs/eligible_units.jsonl
```

The P1 file provides chapter/section/unit order and English section text. The P0 file provides optional `terms` hints.

## Run examples

Run the first five sections in the default `first5` scope:

```powershell
python run_p5_section_llm_extract_ds.py --limit 5 --run-slug p5_section_llm_extract_first5
```

Run the current repair smoke sample:

```powershell
python run_p5_section_llm_extract_ds.py --section-id CH01-S05 --section-id CH03-S07 --section-id CH04-S01 --model deepseek-v4-pro --disable-thinking --concurrency 3 --run-slug p5_section_llm_extract_repair_smoke
```

API key lookup order:

```text
DEEPSEEK_API_KEY, DS_API_KEY, DS_KEY
```

Optional base URL env vars are `DEEPSEEK_BASE_URL` or `DS_BASE_URL`; otherwise the script uses `https://api.deepseek.com/v1`.

## Outputs

```text
runs/<run_slug>/sections/<section_id>/input_section_terms.json
runs/<run_slug>/sections/<section_id>/raw_response.txt
runs/<run_slug>/sections/<section_id>/parsed_response.json
runs/<run_slug>/sections/<section_id>/repair_log.json       # only when repairs happen
runs/<run_slug>/sections/<section_id>/run_manifest.json
runs/<run_slug>_summary.json
outputs/<run_slug>.jsonl
previews/<run_slug>_preview.md
manual_reviews/*.md
```

`raw_response.txt` preserves the original model response. `parsed_response.json`, output JSONL, and preview files use the repaired JSON, because validation runs after repair.

`manual_reviews/` records human review notes for P5A outputs. These notes do not mutate the original model output. They provide keep / merge / review / drop guidance for the later P5B merge and cleanup layer.

## Repair policy

The repair pass is intentionally small and auditable. It only fixes two known model slips before strict validation:

1. If an occurrence has `evidence_type: "abbreviation_full_form"` but its `evidence_quote` does not contain a parenthetical full-form structure, the occurrence is downgraded to `mention`.
2. If an item in `abbreviations` does not literally appear in the section text or in `terms_hint`, the abbreviation is removed.

The abbreviation evidence check also includes `section_title`, because some headings contain the abbreviation while the section body only describes its details. Uppercase abbreviations may match simple plural mentions, such as `PEPs`, `FIUs`, `SARs`, `UBOs`, or `NBFIs`.

Each repair is recorded in `review_flags`, `repair_log.json`, and `run_manifest.json`. The manifest exposes `repair_count`, `repair_counts`, and full `repairs`, so repair activity remains visible instead of being silently hidden.

## Validation policy

Validation runs after repair and remains strict. A section fails if, after repair, it still has malformed output, mismatched `section_id`, invalid `terms`, empty term identities, overlong notes, abbreviations unsupported by section text or hints, missing occurrences, invalid occurrence unit IDs, duplicate occurrences, or `abbreviation_full_form` evidence without parenthetical evidence.

The script exits with code `1` if any selected section fails validation.
