# P7D Edge Review v1 Regression

## 目的

验证P7D第二版职责：规则校验只确认结构合同，独立LLM逐条审核P7C flow edge，并把derivation、review_status和审核历史分开保存。

## 自动测试

```powershell
python -m unittest discover -s phases\P7D\tests\edge_review_v1 -p "test_*.py" -v
```

覆盖：

- 合法card通过纯结构检查
- 规则校验器不把文本相关性误当成语义确认
- node_category、证据范围等结构错误被阻塞
- 显式且支持的边自动accepted
- P7C声明的functional_dependency即使LLM赞成仍保持pending
- 方向不成立的边rejected
- LLM输出不完整时所有边保持pending
- P7D不修改P7C输入对象
- 人工决定追加history并重算card pass/fail

## 真实试跑

输入：`P7C purpose_aligned_regression_v1/outputs/ds_pro_none_purpose_v15/CH06-S09/cards.raw.json`

输出：`outputs/p7d_edge_review_ch06s09_v1`

配置：`deepseek-v4-pro, thinking=none, concurrency=4`。

具体结论见`RESULTS.md`。
