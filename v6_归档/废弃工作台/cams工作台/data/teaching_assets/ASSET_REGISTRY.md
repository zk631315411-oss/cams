# Teaching Assets 可信度台账

本台账只覆盖 `cams工作台/data/teaching_assets/`。旧 `data/` 根目录中的实验文件、历史证据包和旧版资产不进入本轮可信度审查。

## 审查口径

- 完全可信的原始事实层：教材原文、题库题干、题库选项、题库答案。
- 待定原始层：教研解析、学生答疑原文。它们可以作为线索，但本轮不自动视为可信结论。
- 结构化层：由原始事实层解析而来，默认中可信；若源文脏结构、字段缺失或回贴失败，则降级。
- 自动推断层：默认候选，不等于正式结论；必须标注证据等级、推断方法和人工审核状态。
- 教研确认层：目前计划新增 `teaching_review_decisions.json`，专门保存确认、驳回、改名、合并、拆分、补证据等人工决定。

## 可信度等级

- `trusted`：只允许来自教研确认，不由程序自动授予。
- `high_candidate`：自动关系证据强，字段完整，可进入优先审核。
- `medium_candidate`：有教材依据或合理结构，但缺题目证据、缺人工确认或存在轻微不确定。
- `low_candidate`：间接证据、粗匹配、答疑绑定或 KG 辅助关系，必须明显标注仅供参考。
- `invalid_or_blocked`：源数据冲突、关键字段缺失、证据无法回贴、答案选项冲突等，不能作为教学结论。

## 关系审查规则

- 原文句子 -> 考点：必须能追溯到句卡或 quote 回贴；否则 `invalid_or_blocked`。
- 考点 -> 题目：必须来自选项级证据或人工确认；题目级粗匹配只能 `low_candidate`。
- 题目选项 -> 教材句卡：正确选项有 `direct` 证据才可 `high_candidate`；`indirect` 为 `medium_candidate`；`none` 或题目数据问题为 `invalid_or_blocked`。
- 答疑 -> 考点/题目/句卡：本轮只作为学生疑问线索，最高 `low_candidate`，除非未来人工确认。
- KG 概念 -> 句卡/考点：只辅助概念探索，不决定答案或考点是否成立。

## 资产清单

| 文件 | 层级 | 上游 | 当前下游 | 可信口径 | 人工修改规则 |
|---|---|---|---|---|---|
| `chapters/ch2_extracted.json` | 结构化层 | 第二章教材原文，`build_ch2_extracted_chapter.py` | 原文阅读区、原文-考点映射 | 中可信。负责阅读结构，不直接判断考点 | 不建议手改，修源文后重跑 |
| `cards_v6_sentence.json` | 结构化层/证据池 | 全书教材原文句级生成流程 | 证据展示、选项证据、基础考点候选、KG/QA 辅助 | 中可信。句卡是证据池，不等于考点 | 不建议手改，修源文/脚本后重跑 |
| `questions.json` | 原始事实结构化层 | 题库题干、选项、答案、解析解析流程 | 题目列表、选项证据、考点-题目关系 | 题干/选项/答案视为完全可信；解析待定 | 题目字段冲突先标红，不自动修 |
| `option_evidence_map.json` | 自动推断层 | `questions.json` + `cards_v6_sentence.json` + 四角色法 | 题目/选项证据、题目反推考点、易错线索 | 候选。按 direct/indirect/none 和数据问题分级 | 不直接手改，问题写反馈后重跑 |
| `exam_points_from_option_evidence_mvp.json` | 自动推断层 | `option_evidence_map.json`，`build_exam_points_from_option_evidence.py` | 被统一考点层吸收 | 候选。只说明题目证据可反推什么 | 不直接手改 |
| `exam_points_teaching_mvp.json` | 自动推断层/统一候选考点层 | `cards_v6_sentence.json` + `chapters/ch2_extracted.json` + `exam_points_from_option_evidence_mvp.json` + `option_evidence_map.json` | 原文标注、考点列表、考点详情 | 全部为候选，不等于正式考点 | 不直接手改，人工意见写入 review decisions |
| `sentence_exam_point_map.json` | 自动推断层/映射层 | `exam_points_teaching_mvp.json` + `chapters/ch2_extracted.json` | 原文下划线标注 | 候选映射。必须能按 card_id 或 quote 回贴 | 不直接手改，重跑生成 |
| `qa.json` | 待定原始结构化层 | 学生答疑记录结构化提取 | 答疑展示、错因线索 | 答疑原文可信度待定，本轮只作线索 | 修正应回到答疑结构化流程 |
| `qa_bindings.json` | 自动推断层 | `qa.json` + `questions.json` + 句卡/题目匹配 | 答疑关联、错因线索 | 最高 `low_candidate`，不直接生成正式考点 | 不直接手改 |
| `question_card_map.json` | 自动推断层/粗匹配 | 题目级检索匹配 | 题目级候选概念/候选证据 | 粗粒度，仅供参考，不作为选项解析依据 | 不直接手改 |
| `kg_data.json` | 自动推断层/概念关系 | 句卡/章节/概念关系整理 | 右侧概念树、关系探索 | 辅助理解，不决定考点或答案 | 不直接手改 |
| `card_relations.json` | 自动推断层/关系补充 | 句卡关系整理 | 概念/图谱探索 | 辅助关系，不决定考点 | 不直接手改 |
| `exam_points_v6_legacy_fallback.json` | 历史兜底层 | 旧版候选考点流程 | 对照/fallback | 旧逻辑产物，部分关系较粗 | 只读对照 |

## 待新增人工确认资产

`teaching_review_decisions.json`

建议结构：

```json
{
  "version": "0.1",
  "decisions": [
    {
      "target_type": "exam_point",
      "target_id": "ep_basic_v6s_n00018",
      "decision": "confirmed",
      "teacher_note": "基础定义，保留为考点",
      "updated_at": "2026-06-08"
    }
  ]
}
```

自动资产可以反复重跑，人工确认只写入该文件，避免丢失。
