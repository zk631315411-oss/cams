# 题库章节映射数据

## 文件说明

| 文件 | 说明 |
|------|------|
| `question_chapter_mappings.jsonl` | 原版章节映射（基于语义相似度 + Agent审核） |
| `question_chapter_mappings_agent.jsonl` | 新版章节映射（基于子代理对题目知识点的判断） |
| `chapter_similarity_candidates.jsonl` | 每道题的章节相似度候选数据（BGE + BM25） |
| `chapter_similarity_candidates.md` | 章节相似度候选的可读审查报告 |
| `reviewed_decisions.json` | Agent审核策略（覆盖规则） |
| `question_chapter_mapping_review.md` | 最终章节映射的可读审查报告 |
| `chapter_batches/` | 按章节分组的题目批次 |

## 两种映射的区别

### 原版映射（`question_chapter_mappings.jsonl`）

- **生成方式**：`chapter_mapping.py` 对每道题的题干+选项做 BGE + BM25 检索，按 RRF 分数排序，取最相似的章节作为候选。然后由 Agent 审核策略（`reviewed_decisions.json`）确认或覆盖。
- **判断依据**：题目文本与教材文本的语义相似度。
- **局限**：文本相似但考点不同时会误归。例如题目提到"交易监控"但实际考的是"三道防线对交易监控的监督职责"，文本相似度会归到 CH47（交易监控），而非 CH34（三道防线）。
- **覆盖范围**：395 题，每题 1-2 个章节。

### 新版映射（`question_chapter_mappings_agent.jsonl`）

- **生成方式**：将 395 题分批委托给子代理（LLM agent），每批 20 题并发处理。子代理阅读完整的题目文本（题干+所有选项+中英文），然后基于题目所考查的知识点判断归属章节。
- **判断依据**：题目考查的知识点与教材章节主题的匹配。
- **优势**：能区分"文本相似但考点不同"的情况，对跨章节题目能给出多章节归属。
- **局限**：子代理只读了章节目录（章节标题+节标题），没有读教材原文正文。因此它的判断依据是"题目文本让我联想到哪些章节的主题"，而非"教材原文中哪些内容直接支撑了这道题的答案"。
- **覆盖范围**：395 题全覆盖，每题 1-3 个章节，涉及 49 个不同章节。

### 如何选择

- **作为章节映射的参考标准**：新版映射更准确（基于知识点而非文本相似度）
- **用于跨章节检测**：新旧映射可以同时使用。新版映射作为"题目应该归哪章"的参考，盲判引用的 unit 的 `heading_context[0]`（章标题）作为"实际证据来源章节"，两者对比得出跨章节标记。旧版映射保留作对比，辅助审核人员判断"是映射错了还是引用确实跨了"

## 章节分配的判断逻辑

子代理的映射逻辑是：理解题目在考什么知识点，然后把这个知识点映射到教材中讲解该知识点的章节。

例如 `v7_q_000048`：
- 题干："哪种运营情况可能表明洗钱活动正在通过一家接受存款的金融机构进行？"
- 正确答案："客户对大额面值钞票需求增加"
- 子代理判断：**CH01**（洗钱基础概念中的危险信号）+ **CH07**（零售和商业银行洗钱风险）
- 原版映射：**CH06**（金融服务中的洗钱风险）

两者的区别在于：子代理识别出考点是"零售银行场景下的洗钱危险信号"（CH07）和"洗钱基础概念"（CH01），而文本相似度匹配到的是"金融服务中的洗钱风险"（CH06）这个更宽泛的章节。

## 章节分布统计

| 章节 | 题数 | 章节标题 |
|------|------|---------|
| CH42 | 43 | Onboarding AFC controls |
| CH15 | 40 | Money laundering risks associated with DNFBPs |
| CH41 | 29 | Governance and oversight |
| CH36 | 28 | Types of risk assessment |
| CH34 | 26 | Three lines of defense |
| CH47 | 26 | Transaction monitoring |
| CH01 | 26 | Money Laundering and Financial Crime |
| CH31 | 25 | Cooperation between authorities |
| CH20 | 25 | AFC guidance from leading international organizations |
| CH49 | 23 | Concluding an investigation and suspicious activity reporting |
| CH24 | 21 | US AML/CFT regulatory landscape |
| CH19 | 21 | Financial Action Task Force |
| 其他 | 各 1-18 | （共37个章节） |