# 学生答疑 API（端口 8766）

## 文件清单

| 文件 | 来源 | 职责 |
|---|---|---|
| `app.py` | `学生答疑模块_agentic/api/server.py` | HTTP 服务（`http.server`） |
| `logic.py` | `学生答疑模块_agentic/pipeline/run_pipeline.py` | 主流程编排 |
| `input_parser.py` | 同上 pipeline/ | 解析学生输入（疑问+答案+选项） |
| `question_matcher.py` | 同上 | 匹配学生问题到正式题库题目 |
| `free_answer.py` | 同上 | 脱离题目框架的开放式回答 |
| `concept_free_answer.py` | 同上 | 概念层面的自由回答 |
| `claim_planner.py` | 同上 | 规划待核实的事实点 |
| `evidence_retriever.py` | 同上 | 证据检索（共用新题解析的 runtime） |
| `evidence_judge.py` | 同上 | 证据裁判 |
| `evidence_selector.py` | 同上 | 精选展示用的证据句卡 |
| `reply_reviewer.py` | 同上 | 复核生成的回复 |
| `prompts/*.md` | 旧模块 prompts/ | LLM prompt 模板 |

所有文件同一目录，`import xxx` 直接引用。检索运行时通过 `../新题解析/evidence_pool.py` 动态加载，与新题解析共享同一份 BGE/BM25/句卡池。

## 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/student-qa/health` | 健康检查 |
| GET | `/api/student-qa/drafts` | 草稿列表 |
| GET | `/api/student-qa/drafts/<id>` | 读取草稿 |
| POST | `/api/student-qa/analyze` | `{"text":"...", "top_k":12}` → 分析答疑 |
| DELETE | `/api/student-qa/drafts/<id>` | 删除草稿 |

## 流水线步骤

1. **解析输入** — `input_parser`：拆解学生粘贴文本
2. **匹配题目** — `question_matcher`：在正式题库中找到最匹配的题目
3. **自由回答** — `free_answer` / `concept_free_answer`：无框架约束的初步回答
4. **规划事实点** — `claim_planner`：提取需要教材证据支撑的断言
5. **检索证据** — `evidence_retriever`：从教材句卡池中召回相关句卡
6. **裁判证据** — `evidence_judge`：判断每张句卡对断言的支撑程度
7. **精选展示** — `evidence_selector`：挑出最有力的证据句卡
8. **复核回复** — `reply_reviewer`：最终把关

## 依赖关系

- **共用新题解析的 runtime**：`evidence_retriever.py` 动态加载 `../新题解析/evidence_pool.py`，复用 BGE 模型、BM25 索引、句卡池
- **读取题库**：`question_matcher.py` 读取 `data/source/questions.json`
- **外部 pip**：`openai`、`sentence-transformers`、`jieba`、`numpy`（与 新题解析 相同）

## 启动

```bash
cd "D:\守正公司工作区\cams考试\cams工作台（重构版）\services\学生答疑"
python app.py
# → http://127.0.0.1:8766
```
