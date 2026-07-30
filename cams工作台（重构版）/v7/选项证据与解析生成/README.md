# V7 选项证据与解析生产链

本目录保存 V7 检索索引、395 题正式母版、选项级盲判证据、解析母版和软件小节导出。正式工作台应用不读取本目录运行态，而是通过独立导入流程建立自己的题目档案。

## 正式资产

| 资产 | 路径 | 口径 |
|---|---|---:|
| 双语知识单元 | `../work/base_units/units/v7_bilingual_units.json` | 4,973 |
| 检索适配单元 | `../work/base_units/units/v7_units_as_cards.json` | 4,973 |
| 正式结构化题库 | `phase3.5_questions/output/v7_questions.json` | 395 |
| 检索索引 | `phase3_index/output/index/v7_index_5614abb1c4bf.pkl` | 冻结索引 |
| 单题证据与盲判 | `phase4_evidence/output/questions/q_v7_q_*.json` | 395 |
| 单题解析母版 | `phase4_evidence/output/explanations/v7_q_*.md` | 395 |
| 软件小节 | `phase4_evidence/output/software_export/sections/p*-ch*-h*.md` | 63 |

`教材、答疑记录、习题与参考文献/习题/v7习题/v7结构化文本/` 是来源与派生格式快照，不是正式题库母版。

## 目录

```text
选项证据与解析生成/
├── phase3_index/            # 冻结单元检索索引
├── phase3.5_questions/      # 395 题正式结构化母版
├── phase4_evidence/
│   ├── 盲判流程/             # blind_adjudication.py
│   ├── 解析撰写/             # 解析生成与软件导出
│   ├── 质量审查/             # 机械与 LLM 质量检查
│   ├── md-to-docx/          # DOCX 转换
│   └── output/              # 正式内容与历史过程报告
├── config/                  # 历史配置说明；yaml 文件不是有效运行配置
└── scripts/                 # 辅助检查脚本
```

## 当前状态

- Phase 3：索引已完成。README 中的索引清单以实际 `output/index/` 为准。
- Phase 3.5：395 题母版已终审修改。`prepare_questions.py` 仍面向旧输入字段，**禁止直接运行**，否则可能生成空题并覆盖正式输出。
- Phase 4：395 题盲判、证据和解析已生成；质量报告早于部分终审，只能作为过程记录。
- 软件导出：395 题全部分配到 63 个 `p*-ch*-h*` 小节。最终章节归属以这些小节和 `export_results.json` 为准。
- Phase 5-8/P7：未完成研究实验，不属于当前正式交付链。

## Phase 4 调试入口

生产母版已经存在。以下命令只用于显式新输出目录的调试，不得覆盖 `phase4_evidence/output/`：

```powershell
Set-Location phase4_evidence/盲判流程
python blind_adjudication.py `
  --question-id v7_q_000009 `
  --concurrency 1 `
  --enable-kg `
  --enable-p5 `
  --output-dir ../output/debug_v7_q_000009
```

`--limit N` 按 `question_id` 排序取前 N 题，不代表“人工复核题抽样”。脚本没有 `--all` 参数。

## 约束

1. 盲判阶段不读取参考答案；参考答案只用于后置冲突审计。
2. 正式证据必须回到真实 `v7u_N*`、英文原文和页码。
3. KG/P5 只扩展候选池，不单独构成答案依据。
4. 根 `blind_judgment_results.jsonl` 仅含最后一次局部运行的 35 条汇总，不是 395 题覆盖清单。
5. 91 题、148 题等“需复核”数字均来自不同时间的过程报告，不能代表当前终审后的验收状态。
6. 发布或导入前应以当前文件重新生成质量清单，并保留人工批准记录。
