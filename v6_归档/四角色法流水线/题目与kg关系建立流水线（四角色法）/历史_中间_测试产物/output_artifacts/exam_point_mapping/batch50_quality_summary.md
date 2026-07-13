# 50题批量运行质量汇总

## 总览

- 合并池结果题数：51
- status 分布：
  - answered：39
  - partial：11
  - evidence_insufficient：1
- validation issue 题数：2
- 映射表选项行：210
- 候选考点：69
- 选项证据状态分布：
  - direct：99
  - indirect：77
  - none：34

说明：因为 `2.1_1` 已先用合并池跑过一次，本轮 `--limit 50` 又继续跑了 50 个 pending，所以当前合并池结果总数是 51。

## 需要精修的题

以下题目建议后续用 `card-scan correct` 单独精修，或交给教研人工确认：

- `2.1_15`：partial，direct=2，indirect=3，issues=1
- `2.1_16`：partial，direct=2，indirect=2
- `2.1_17`：partial，direct=4，indirect=1
- `2.1_24`：partial，direct=1，indirect=3，none=1
- `2.1_25`：evidence_insufficient，none=4
- `2.1_36`：partial，direct=1，indirect=2，none=2
- `2.1_38`：partial，direct=2，issues=1
- `2.1_41`：partial，direct=1，indirect=2，none=1
- `2.1_44`：partial，direct=1，indirect=3
- `2.1_45`：partial，direct=2，indirect=2，none=1
- `2.1_47`：partial，direct=1，indirect=3
- `2.1_49`：partial，direct=2，indirect=2，none=1

另有若干 answered 题存在 wrong options 为 none 的情况，不一定是错误；多选题/排除项中，错误选项没有直接证据有时是合理的。但这些题如果要进入正式教研库，仍建议抽样人工看一遍。

## 对卡池质量的判断

合并卡池可以继续推进。

理由：

- 第二章内证据和跨章补充证据能够同时被召回。
- 已跑出的 51 题中，39 题为 answered，占比约 76%。
- 候选考点和选项映射表结构稳定，没有出现 card_id 缺失、错误选项误收考点、候选考点无证据等结构性问题。
- 之前第二章池无法解释的跨章题，如欧盟反洗钱指令、第三方反腐败条款，已经能被合并池解释。

限制：

- `cards_v6_except_ch2_sentence.json` 的 `knowledge/type` 仍是规则占位，不是 DS Flash 精标。
- 快速批量模式关闭了 `card-scan correct`，因此 partial/evidence_insufficient 题需要二次精修。
- 候选考点名称仍偏题目选项表达，后续需要做教研口径的命名规范化和语义去重。

## 当前建议

可以继续推进批量生产，但采用两阶段策略：

1. 用快速模式继续铺量，生成题目-选项-证据-候选考点映射。
2. 对 partial、evidence_insufficient、validation issue 题目进行精修。
3. 全量后再做候选考点去重、命名规范化和教研确认。
