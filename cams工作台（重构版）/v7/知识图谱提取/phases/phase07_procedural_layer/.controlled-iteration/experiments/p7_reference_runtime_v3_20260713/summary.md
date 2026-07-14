# Experiment p7_reference_runtime_v3_20260713

- Objective: 让REFERENCES保持正本方向不变，同时支持反向渲染和受P7D门禁约束的双向证明遍历
- Hypothesis: 集中式运行策略、全边condition门禁和snapshot一致性校验可以修正人读箭头并支持依据到判断的反向遍历，同时阻止条件绕过、未审核边和复用ID的新边进入证明
- Changed variable: REFERENCES运行时方向、条件门禁与审核snapshot匹配策略
- Execution status: ran
- Verdict: accept
- Issue count: 4

## Evaluation

REFERENCES正本方向保持process_to_auxiliary；两套draw.io渲染均派生为auxiliary_to_process；证明运行时支持受P7D门禁约束的双向REFERENCES遍历，并阻止未满足condition、pending最终使用、rejected、未审核和snapshot已变化的边进入最终证明。

## Next Action

对v5补丁后的CH06-S10 E4/E5/E6重新运行P7D，审核通过后再生成完整阈值到UBO认定结果的最终证明路径。

## Run Return Codes

```json
{
  "development": {
    "baseline": 0,
    "variant": 0
  }
}
```
