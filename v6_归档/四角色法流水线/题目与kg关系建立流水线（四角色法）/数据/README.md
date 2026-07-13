# 四角色法数据清单

本目录是四角色法流水线的便携数据快照，来源主要是 `cams工作台/data`。

## 正式教材证据池

- `data/cards_ch2.json`：第二章教材句卡。它是教材原文证据句，不是考点卡。
- `data/cards_v6_sentence.json`：全书 V6 句级教材证据池。`citation` 是 `source/v6_clean.md` 的原句，`knowledge/type` 由 DeepSeek Flash 标注。它也是教材证据句，不是考点卡。

最终 `evidence_cards[].card_id` 只能引用上述教材句卡中的真实 `card_id`。

## 题目与答案

- `data/questions.json`：题目、选项、标准答案、教研解析。
- `data/qa.json`、`data/qa_all.txt`：题库/问答文本辅助材料。

## 辅助召回资产

- `data/card_relations.json`：句卡之间的相邻、相关关系，只能用于召回扩展，不能当教材依据。
- `data/kg_data.json`：知识图谱数据，只能用于概念导航/辅助召回，不能当教材依据。
- `data/agentic_search_eval_v2/kg/sections.json`
- `data/agentic_search_eval_v2/kg/edges.json`
- `data/agentic_search_eval_v2/kg/card_section_map.json`

## 参考资产

- `data/question_card_map.json`：题目到句卡的粗映射，仅供参考，不满足选项级解析验收标准。
- `data/exam_points_ch2.json`：第二章考点探索资产，可参考但不能替代教材证据。
- `source/v6_clean.md`：V6 全书清洗后原文，供重建 `cards_v6_sentence.json` 或人工追溯原文使用。

## 铁律

1. 不把 `kg_data.json`、`card_relations.json`、`question_card_map.json` 当最终教材证据。
2. 不把 `cards_ch2.json` 或 `cards_v6_sentence.json` 叫考点卡。
3. 选项级解析要能回到真实教材句卡；证据不足时必须标注 `none`、`indirect` 或 `needs_manual`。
