## v5优先修正规则

以下规则优先于前文的一般偏好：

1. 严格区分调查阶段。`initial investigation`、`further investigative efforts`和`evidence suggested`不是同一个source动作。后续调查或证据暗示的结论不得挂到“初始调查”process上，即使旧process的`evidence_unit_ids`包含相关unit。只有原文明示了准确的新process时才新增该process；否则对应claim输出`unresolved`。
2. 当补充已有card会引入新的process和exit，却无法形成已有entry到新exit的有证据路径时，优先为该gap新建不含entry的最小开放card。不要为了结构连通增加无证据的`PRECEDES`。例如计算/比较到分类可以独立成`process + auxiliary + exit`局部判断卡。
3. `require, required, need, must, should`也是必须保留的限定词。原文为“需要/必须进行评估”时，process标签必须写成“需要/必须进行……”，相关边同时填写对应`qualifier`，不能只把义务藏在标题、condition或review_notes中。
4. 每个claim独立决定。一个claim证据充分可以构图，另一个claim证据不足可以`unresolved`；不得为了让多个claim共用一个supplement而复用语义不匹配的source。
5. 最小化新增边。计算/比较card只需参照必要输入或标准并产生分类；场景设置开放card只需`REFERENCES`；不得追加与gap无关的流程连接。
