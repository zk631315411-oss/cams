# CAMS 教研工作台资产包

这个目录集中存放 `index.html` 教研工作台当前应优先读取的资产。`data/` 根目录里仍保留历史实验文件、旧版资产和临时证据包，但前端展示、教研验收和后续数据修订应优先看本目录。

## 使用原则

- 本目录是工作台 MVP 的资产入口，不代表所有资产都已经教研确认。
- 自动生成资产必须保留 `status`、`confidence`、`source`、`needs`、`validation_issues` 等审核字段。
- 题目级粗映射只能作为召回参考，不能作为选项级解析或考点确认依据。
- 选项级证据、考点、原文标注都必须能追溯到教材原文或明确标注“缺证据/需人工”。
- 不直接修改旧版 fallback 资产。若需要调整，生成新版本并更新本 README。

## 当前主资产

| 文件 | 用途 | 来源 | 可信度/状态 | 是否建议人工改 |
|---|---|---|---|---|
| `chapters/ch2_extracted.json` | 第二章原文阅读区结构，含段落、句卡 ID、目录 | `build_ch2_extracted_chapter.py` | 主阅读资产 | 不建议手改，修源文后重跑 |
| `cards_v6_sentence.json` | 全书句卡池，当前阅读区和证据展示依赖 | 全书句级卡片生成流程 | 证据池，非考点卡 | 不建议手改，修源文/脚本后重跑 |
| `questions.json` | 题库题干、选项、答案、解析 | 题库解析流程 | 基础题目资产 | 可修源数据问题后重跑 |
| `option_evidence_map.json` | 题目/选项到教材句卡的绑定结果 | 四角色法，证据池为全书句卡 | MVP 主证据资产，需教研抽查 | 不建议直接改，问题写反馈后重跑 |
| `exam_points_from_option_evidence_mvp.json` | 从选项级证据反推的候选考点 | `build_exam_points_from_option_evidence.py` | 候选考点，不是正式考点 | 不建议直接改，后续会被教学考点层替代 |
| `qa.json` | 学生答疑结构化记录 | 答疑提取流程 | 学生疑问来源 | 修正应回到答疑结构化流程 |
| `qa_bindings.json` | 答疑与句卡/概念的绑定 | `bind_qa.py` | 可参考，需抽查 | 不建议直接改 |

## 辅助资产

| 文件 | 用途 | 注意事项 |
|---|---|---|
| `question_card_map.json` | 题目级粗粒度候选句卡映射 | 仅供参考，不能直接作为选项证据 |
| `kg_data.json` | 概念/章节关系数据 | 用于右侧概念关系，不等同于考点层 |
| `card_relations.json` | 句卡/概念关系补充 | 用于探索，不直接决定考点 |
| `exam_points_v6_legacy_fallback.json` | 旧版候选考点兜底/对照 | 旧逻辑产物，部分映射较粗，只用于对比和 fallback |

## 待新增资产

| 文件 | 目标 |
|---|---|
| `exam_points_teaching_mvp.json` | 教研视角的统一考点层：基础定义、题目反推、答疑反推、易错预警分来源管理 |
| `sentence_exam_point_map.json` | 原文句子/句卡到考点的映射：让阅读区知道哪些句子是考点、为什么是、关联哪些题目和错因 |

## 状态说明

- `confirmed`：教研已确认。
- `ai_candidate`：AI 候选，未确认。
- `needs_evidence`：有候选考点或题目关系，但教材证据不足。
- `needs_manual`：自动流程无法可靠判断，需人工处理。
- `rejected`：教研确认不是考点或证据不成立。

## 当前 MVP 已知限制

- `exam_points_from_option_evidence_mvp.json` 主要覆盖题目/选项直接证据，容易漏掉教材基础定义句。
- 第二章阅读区只能显示第二章原文。全书证据池里的跨章节证据可在右侧详情显示，但不会出现在第二章原文中。
- `common_trap` 和 `student_confusion` 当前主要来自题目/选项推断，尚未完整融合学生答疑高频统计。
