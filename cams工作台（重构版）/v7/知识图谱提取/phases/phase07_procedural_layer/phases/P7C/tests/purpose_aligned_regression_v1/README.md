# P7C Purpose-Aligned Regression v1

## 目的

本测试依据P7C正式目的定义，验证四类质量问题：

1. 是否遗漏基础KG无法充分表达的局部程序性或判断性有向结构。
2. 是否把基础KG已经足以表达的普通事实、案例、指标或一般机制重复包装成card。
3. 节点、边、方向、条件和主体是否均可追溯到当前section证据。
4. LLM必要功能推理是否与显式证据分离，并进入人工复核。

本测试不读取具体题目、选项或参考答案，也不测试跨section桥接。

## 样本

定向回归共10个section：

```text
召回：CH06-S09、CH06-S10、CH07-S03、CH08-S05
KG边界：CH02-S04、CH03-S02、CH03-S03
方向与并行结构：CH03-S07、CH05-S02
图连通性：CH05-S04
```

每个section的语义验收点见`regression_cases.json`。验收不固定card数量；同一section可以同时包含应成卡和不应成卡的局部主题。

## 自动校验

运行校验器单元测试：

```powershell
python -m unittest discover -s phases\P7C\tests\purpose_aligned_regression_v1 -p "test_*.py" -v
```

覆盖规则：

- 节点只能使用`explicit`。
- 边只能使用`explicit`或`functional_dependency`。
- `functional_dependency`必须对应`needs_review`并在`review_notes`中标记“LLM推理”。
- 所有证据必须属于当前section，且被`source_unit_ids`覆盖。
- 每个节点必须参与边，整张图必须连通。
- 至少存在一条entry经process到exit的有向路径。
- `REFERENCES`、`PRODUCES`和`DECIDES`端点类型必须正确。
- `relation_type`默认省略；填写时必须满足业务语义和端点约束。
- 顶层`coverage_audit`必须记录候选命题的`p7c_card/kg_only`决定，并引用输出card。
- 兼容诊断模式下，结构校验失败时批处理器可携带错误报告自动修复一次；生产默认已将正式结构校验交给P7D。
- 空正文或不可解析正文必须触发API重试，不能因HTTP成功直接落为`parse_failed`。
- 独立coverage adjudication只复核原`kg_only`候选；不得新增候选、修改已有卡或越过候选证据范围。
- 验证报告分别统计卡内`flow_edge_count`、派生索引`derived_edge_count`和桥接边。

## DS定向回归

```powershell
python scripts\run_p7c_batch_ds.py `
  --sections CH06-S09,CH06-S10,CH07-S03,CH08-S05,CH02-S04,CH03-S02,CH03-S03,CH03-S07,CH05-S02,CH05-S04 `
  --output-dir phases\P7C\tests\purpose_aligned_regression_v1\outputs `
  --run-id ds_pro_none_purpose_v1 `
  --model deepseek-v4-pro `
  --thinking-effort none `
  --concurrency 10 `
  --validation-retries 1 `
  --coverage-adjudication
```

## 验收口径

最终逐section审查五项：

```text
P7C层信息是否遗漏
是否重复基础KG
主体、方向和条件是否正确
是否存在强行线性化或虚构通用出口
显式证据与LLM推理是否清楚分离
```

产卡数量、类型分散度和relation_type覆盖率不作为质量目标。

当前自动测试共34项。P7C生产顺序为主抽取和独立coverage裁决；正式结构与语义审核由P7D负责。旧结构修复回归仍保留，用于显式开启的兼容诊断。

本轮结果和剩余问题见`RESULTS.md`。
