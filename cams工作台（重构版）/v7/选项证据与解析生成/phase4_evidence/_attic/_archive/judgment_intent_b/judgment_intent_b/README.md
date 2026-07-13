# B线测试：题干意图优先裁判

本目录用于测试 B 线裁判 prompt：在判断选项前，先让 LLM 明确题干意图和判断标准，再进入选项裁判。

## 目标

当前盲判 prompt 直接要求模型根据候选 unit 判断选项，容易在以下题型中摇摆：

- 两个选项都有局部教材依据，但题干问的是“最佳/首先/最能”之类的排序题。
- 选项都接近正确，但判断维度不同，例如“剩余风险显著降低”与“仍需进一步控制”。
- 操作型题目缺少显式流程边，模型用常识补流程。

B 线只测试裁判协议，不修改召回、KG 扩展、P5 术语处理或证据池。

## 文件

- `prompt_intent_v1.md`：intent-first 裁判 prompt 模板。
- `run_intent_adjudication.py`：独立 runner，复用主脚本的检索、LLM 调用、解析和校验函数，只替换 prompt。
- `output/`：测试输出目录。

## 默认题组

默认题组分为两类：

- 冲突/双合理题：`v7_q_000006`、`v7_q_000009`、`v7_q_000012`、`v7_q_000026`、`v7_q_000039`
- 干净对照题：`v7_q_000001`、`v7_q_000003`、`v7_q_000016`、`v7_q_000030`、`v7_q_000045`

## 运行

```powershell
python "D:\守正公司工作区\cams考试\cams工作台（重构版）\v7\选项证据与解析生成\phase4_evidence\tests\judgment_intent_b\run_intent_adjudication.py" --concurrency 5 --model deepseek-v4-pro
```

指定单题：

```powershell
python "D:\守正公司工作区\cams考试\cams工作台（重构版）\v7\选项证据与解析生成\phase4_evidence\tests\judgment_intent_b\run_intent_adjudication.py" --question-id v7_q_000026
```

默认启用当前主线使用的 KG 与 P5，以保持检索层不变；如需隔离纯 prompt 效果，可加：

```powershell
--disable-kg --disable-p5
```

## 产物

- `questions/q_*.json`：每题完整结果，包含 `question_intent`、`judgment_standard`、`competing_option_analysis`。
- `intent_judgment_results.jsonl`：简表 JSONL。
- `intent_judgment_report.md`：人读报告。
- `reference_comparison.csv`、`reference_comparison.md`：跑完后与既有参考汇总做后置对照。参考答案不会进入 prompt。

