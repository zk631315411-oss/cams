# V6 历史资产样本与构建方式

本目录存放旧前端使用的 V6 数据样本副本，用于历史交接和结构理解。它不是当前生产数据，也不是 V7 教材依据。表中的“生产路径”“最终依据”和 720 题等措辞均属于旧系统语境；当前 `data/source/questions.json` 实际为 718 题，`questions copy/` 仅是 706 题部分副本。

## 资产清单

| 资产 | 生产路径 | 说明 | 构建方式 |
|---|---|---|---|
| cards_v6_sentence.json | `data/cards/` | 全书句卡池，5199 张，`v6s_N#####` 坐标系。所有教材原文追溯的最终依据。 | 工具：`tools/build_v6_sentence_cards.py`。输入：`核心数据/源文/source/v6_clean.md`。从教材逐句切分，DeepSeek Flash 批处理生成 knowledge/type，citation 保留原文。需 DeepSeek API key。 |
| questions.json | `data/source/` | 正式题库，720 题，全教材 2-6 章。 | 工具：`tools/题库记录/parse_questions.py`。输入：`教材、答疑记录、习题与参考文献/习题/习题结构化/*_习题*.md`。纯 Python 标准库，无需额外依赖。 |
| card_page_map_v6.json | `data/page_maps/` | 句卡→教材页码映射。前端展示句卡时标注页码。 | 工具：`tools/句卡页码映射/build_v6_card_page_map.py`。输入：`cards_v6_sentence.json` + `CAMS中文版教材-V6.51.pdf`。用 PyMuPDF 逐页文本匹配定位，需要 PyMuPDF 依赖。 |
| kg_data.json | `data/derived/` | CAMS 教材知识图谱。602 个知识节点 + 633 条关系边 + 3719 张句卡挂载。前端用于概念导航和图谱弹窗。 | 工具：`tools/知识图谱/模拟高代提取/` 下 01-05 流水线。输入：`v6_clean.md` + `cards_v6_sentence.json`。10 步 LLM 流水线（MiMo + DS），详见该目录 README。 |
| questions/ | `data/derived/questions/` | 720 题 × 选项级证据绑定结果。每题一个 JSON（完整 pipeline 过程），含裁判判断、证据句卡引用、Plan B 补充（如有）。题目级一致率 80.5%。 | 工具：`tools/选项证据生成/新题解析模块复用/run_bindings.py`。输入：`questions.json` + `cards_v6_sentence.json` + `kg_data.json`。检索（BGE+BM25+KG）+ Flash 精排 + pro 盲判裁判。20 并发 ~40 分钟跑完全书。 |

---

## 约定

1. **原始事实层**的资产不由 pipeline 生成，由 `tools/` 目录下的工具一次性提取或人工整理后直接放入。
2. **Pipeline 产物**（`data/derived/`）全部由 `tools/` 或 `pipeline/` 目录下的脚本生成，逻辑上可随时删除后重跑。
3. **本目录**（`重要资产以及构建方式/`）存放上述资产的样本副本，用于交接审阅。前端不读取本目录。
4. 每个资产的构建脚本和输入来源必须记录在上表中，保持实时更新。
