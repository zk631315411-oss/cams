# CH06-S10补丁重审测试

## 结论

原补丁不能直接重跑P7D：`p7card_CH06-S10_001`缺少`entry -> process -> exit`有向路径，结构校验失败，语义审核不会执行。

实验变体将语义重复的N2“识别UBO”和N5“合计持股并比较阈值”合并成一个assessment process，不增加无原文依据的`PRECEDES`。合并后结构为`closed_flow`，P7D完成全部4条边审核。

## 审核结果

| edge | 关系 | P7D状态 | 最终答案可用 |
|---|---|---|---|
| E1 | 审查所有权结构 -> 综合UBO判断 | accepted | 是 |
| E2 | 综合UBO判断 -> 持股阈值标准 | pending / llm_inference | 否 |
| E3 | 综合UBO判断 -> 直接和间接持股信息 | accepted | 是 |
| E6 | 综合UBO判断 -> UBO认定结果 | pending / llm_inference | 否 |

E2与E6的节点、方向、限定词和并列检查均得到支持；pending来自现行政策：跨unit必要归纳属于`llm_inference`，必须人工确认。

## 证明路径

```text
retrieval:
直接和间接持股信息 --reverse E3 accepted--> 综合UBO判断 --E6 pending--> UBO认定结果

retrieval:
持股阈值标准 --reverse E2 pending--> 综合UBO判断 --E6 pending--> UBO认定结果

final:
两条路径均不可用，因为E2或E6仍为pending。
```

## 产物边界

旧v23 P7D产物未移动、未覆盖。实验baseline保存了CH06-S10相关审核的过滤快照与SHA256归档清单。生产P7C card未被修改；合并卡仅存在于受控实验目录。
