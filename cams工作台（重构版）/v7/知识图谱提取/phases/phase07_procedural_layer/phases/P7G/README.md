# P7G：按题生成证明路径

## 定位

P7G面向题目或业务场景组装证明路径。当前先提供card内最小证明路径运行时；跨card路径仍需等待P7E桥接审核完成后支持。

P7G不修改P7C正本，也不把派生邻接写回`flow_edges`。

## Card内边运行规则

```text
PRECEDES    只沿正本方向遍历
PRODUCES    只沿正本方向遍历
DECIDES     只沿正本方向遍历，且必须满足condition
FEEDBACK    只沿正本方向遍历
REFERENCES  可双向遍历；正向读作“process参照auxiliary”，反向读作“auxiliary作为依据供process参照”
```

`REFERENCES`没有因果或时序含义。从input/standard反向进入process后，必须继续经过已审核接受的`PRODUCES`或满足条件的`DECIDES`，才能形成指向结果或分类的最终证明。

所有边的`condition`都是路径门禁，而不只是显示文字：`REFERENCES.condition`限定输入或标准的适用范围，`PRECEDES.condition`限定单一路径的逻辑前提，`DECIDES.condition`限定分支。调用方未提供完全一致的已满足条件时不得遍历；`DECIDES`缺少condition时同样不得遍历。

## P7D门禁

```text
accepted + answer_eligible=true     可进入最终证明路径
pending + retrieval_eligible=true   只可进入检索扩展路径
rejected                            不可遍历
未找到P7D审核记录                   不可遍历
审核snapshot与当前边不一致          视为未审核，不可遍历
```

Card级`pass/fail`是汇总信息；运行时逐边执行上述门禁，并在每个proof step中保留`review_status`、存储方向和实际遍历方向。

审核关联不能只匹配`card_id + edge_id`。当前边必须与P7D的`source_edge_snapshot`一致；补丁若复用旧edge_id但改变端点、类型、条件、relation_type、derivation或证据unit，旧审核立即失效。

## 当前实现

```text
scripts/p7_edge_runtime.py
```

示例：

```powershell
python scripts/p7_edge_runtime.py `
  --cards <cards.raw.json> `
  --edge-reviews <p7d_edge_reviews.jsonl> `
  --card-id <card_id> `
  --start-node <input_or_standard_node_id> `
  --target-node <exit_node_id> `
  --condition <satisfied_decision_condition> `
  --mode final
```

输出的每一步同时记录：

```text
stored_source / stored_target      P7C正本方向
source / target                    本次遍历方向
traversal_direction                forward或reverse
proof_reading                      不夸大因果的中文读法
review_status / eligibility        P7D门禁结果
```
