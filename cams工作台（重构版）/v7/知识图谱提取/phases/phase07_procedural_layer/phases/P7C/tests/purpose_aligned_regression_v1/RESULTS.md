# P7C Purpose-Aligned Regression v1 Results

## 运行配置

```text
model: deepseek-v4-pro
thinking_effort: none
主抽取并发: 10（v13）
validation_retries: 1
coverage_adjudication: true
```

主要产物：

- 10-section统一批次：`outputs/ds_pro_none_purpose_v13`
- CH02-S04恢复测试：`outputs/ds_pro_none_purpose_v14/ds_pro_none_purpose_v14/CH02-S04`
- CH06-S09最终语义回归：`outputs/ds_pro_none_purpose_v15/CH06-S09`
- 冻结旧产物裁决测试：`outputs/existing_v10_ch03s07_adjudication_normalized`

## 当时流程与当前迁移

本回归建立时，P7C包含三层：

1. 主抽取生成`coverage_audit + flow_nodes + flow_edges`。
2. 结构校验失败时，携带错误报告自动修复一次。
3. 独立coverage adjudication只复核原`kg_only`候选，允许提升成卡，但不得新增候选或改动已有卡。

P7整体目标调整后，正式结构校验和边级语义审核已经迁入P7D。P7C生产CLI默认不再执行第2步；自动结构修复只保留为`--inline-structure-validation`兼容诊断。P7C输出现在是候选正本，不能依据这里的`review_status`直接进入最终答案。

## 最终组合验收

| section | cards | 校验 | coverage裁决 | 语义结论 |
|---|---:|---:|---|---|
| CH02-S04 | 1 | 0错误 | 提升0 | 负面新闻→调查→审计发现链成立；审计到上游犯罪识别为功能依赖，正确标记`needs_review` |
| CH03-S02 | 0 | 0错误 | 提升0 | 环境犯罪普通机制由KG承接 |
| CH03-S03 | 0 | 0错误 | 提升0 | BMPE普通犯罪方法由KG承接 |
| CH03-S07 | 3 | 0错误 | 提升1 | 金融机构检测、FIU综合分析、执法响应拆成局部卡，未再串到定罪刑罚 |
| CH05-S02 | 1 | 0错误 | 提升0 | DPA要求触发整改与组织配置变化；未用声誉损害触发整改 |
| CH05-S04 | 1 | 0错误 | 提升0 | 母国政策到东道国本地化调整形成连通结构 |
| CH06-S09 | 4 | 0错误 | 无KG候选 | 覆盖当地要求、风险偏好更高标准、卸任后PEP分类维持、监控/KYC调整 |
| CH06-S10 | 2 | 0错误 | 提升0 | 覆盖UBO阈值与持股计算、无自然人UBO例外路径 |
| CH07-S03 | 2 | 0错误 | 提升0 | 覆盖可疑还贷拒绝与贷款核销审批两条独立处置链 |
| CH08-S05 | 1 | 0错误 | 无KG候选 | 覆盖EDD→识别UBO/真实目的→有助于缓解风险 |

最终组合结果为10/10个section结构校验通过。两个KG负例保持0张，未出现裁决误提升。

## 关键回归

### CH03-S07覆盖裁决

冻结的v10产物原有1张卡。独立裁决将两个已有`kg_only`候选提升为卡，最终得到3张，合同错误和结构错误均为0。

统一v13批次中，主抽取已召回FIU和执法链，裁决再提升金融机构监控识别链，最终同样为3张。说明裁决轮可以修复“候选已发现但KG/P7C边界判错”的漏抽。

### CH02-S04空响应

v13调用消耗完生成预算但返回空正文，原产物为`parse_failed`。批处理器现在把空正文和不可解析正文计入API重试，而不是把HTTP成功直接视为生成成功；该行为由单元测试覆盖。v14真实重跑首轮成功生成1张卡，因此没有再次触发重试。

### CH06-S09情态与召回

v13的4张卡存在三类语义漂移：凭`must`增加“持续”、把规范性动作写成“已经调整”、把`escalate`翻译成“上报”。

收紧情态后，v14虽消除漂移，却错误收缩为1张。进一步明确“单句、纯义务、无复杂步骤不是跳过理由”后，v15恢复4条应成关系，同时保留`may choose`、`some organizations`和`may remain`，且三类语义漂移均未复现。

## 自动保障

当前34项单元测试覆盖：

- 当前section证据边界、节点显式证据和source unit覆盖
- 孤立节点、连通分量、entry→process→exit可达性
- `functional_dependency`与`needs_review`一致性
- `relation_type`端点约束和真实分支条件
- `coverage_audit`完整性与独立裁决保护合同
- 校验失败修复、初次解析失败重试和裁决结果规范化
- 规范性情态、持续性限定和`escalate`语义的Prompt合同
- 验证报告对卡内`flow_edges`的真实计数

## 剩余风险

P7C候选召回和定向回归已经通过，可以进入更大样本生成。最终程序边是否可用由P7D逐边审核决定；P7C coverage裁决仍只能复核主抽取已写入`coverage_audit`的`kg_only`候选，无法恢复主抽取完全没有发现的候选。
