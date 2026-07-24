# v7 MinerU Phase 0/1 Quality Report

Generated at: 2026-07-01T13:06:33

## Conclusion

- The split zh/en PDFs are usable as page anchors.
- The new MinerU markdown files are usable as structured text sources.
- MinerU markdown contains no page markers, so page attribution must come from split PDF page text matching.
- No term replacement has been applied in this phase; zh text remains raw MinerU output.

## Outputs

- zh merged md: `D:\守正公司工作区\cams考试\教材、答疑记录、习题与参考文献\教材原文\v7\mineru提取\v7_zh_mineru_merged.md`
- en merged md: `D:\守正公司工作区\cams考试\教材、答疑记录、习题与参考文献\教材原文\v7\mineru提取\v7_en_mineru_merged.md`
- page aligned text: `D:\守正公司工作区\cams考试\cams工作台（重构版）\v7\work\sources\v7_page_aligned_text.json`
- block-page matches: `D:\守正公司工作区\cams考试\cams工作台（重构版）\v7\work\sources\v7_mineru_block_page_matches.json`

## MinerU Markdown

| Lang | Source files | Chars | Headings | HTML tables | PAGE markers |
|---|---:|---:|---:|---:|---:|
| zh | 3 | 344237 | 629 | 19 | 0 |
| en | 3 | 984770 | 792 | 19 | 0 |

## PDF Page Text

| Lang | Pages | Median chars | Low text pages |
|---|---:|---:|---|
| zh | 547 | 578 | [1] |
| en | 547 | 1903 | [] |

## MinerU Block Page Matching

| Lang | Blocks | Direct | Inherited short | Unmatched | Usable rate |
|---|---:|---:|---:|---:|---:|
| zh | 4446 | 2731 | 1712 | 3 | 0.9993 |
| en | 4430 | 3692 | 736 | 2 | 0.9995 |

## Decision

Phase 1 should use `resplit_from_md`: English MinerU markdown is the main unit-cutting anchor, Chinese MinerU markdown is the display/alignment source, and split PDF page text is the page attribution source.
