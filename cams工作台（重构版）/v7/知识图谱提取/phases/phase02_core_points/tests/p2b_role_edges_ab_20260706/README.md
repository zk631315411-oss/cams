# P2B role edges AB test

Purpose: test whether DeepSeek variants can reliably turn P2A `core_point` nodes into section-local `core_point -> unit` role edges.

Scope:

- P2A defines core_point nodes.
- P2B assigns unit roles for each core_point.
- P2B may mark a unit as `exclude` when P2A evidence is too broad.
- P2B does not create cross-section or cross-chapter relations.

AB variants:

- `flash_thinking`: `deepseek-v4-flash` with thinking enabled and `reasoning_effort=high`.
- `pro_no_thinking`: `deepseek-v4-pro` with thinking disabled.

Default samples:

- `CH02-S06`: tests support-boundary decisions around cyber-enabled crime.
- `CH05-S04`: tests non-contiguous definition-then-expansion structure.

Run:

```powershell
python "D:\守正公司工作区\cams考试\cams工作台（重构版）\v7\知识图谱提取\phases\phase02_core_points\tests\p2b_role_edges_ab_20260706\run_p2b_ab.py" --section-id CH02-S06 --section-id CH05-S04
```

Outputs are written under `runs/<run_slug>/<section_id>/<variant>/`.

