# Legacy Chapter-2 Card Archive

Archived at: 2026-06-24T21:36:16+08:00

This folder stores legacy chapter-2 evidence pools after migration to the unified
`cards_v6_sentence.json` coordinate system.

Archived files:

- `cards_ch2.json`: legacy second-chapter sentence cards with `ch2s_...` ids.
- `cards_ch2_plus_v6_except_ch2_sentence.json`: old mixed evidence pool that combined `ch2s_...` and `v6x_...` ids.
- `ch2_old_to_v6s_map.json`: migration table from `ch2s_...` to `v6s_N...`.
- `migration_report.md`: migration summary and unresolved references, if any.

Current static teaching assets should not use `ch2s_...` as final evidence ids.
Use `cards_v6_sentence.json` / `v6s_N...` instead.
