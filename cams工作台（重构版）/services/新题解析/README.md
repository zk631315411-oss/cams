# 新题解析 API（端口 8765）

> 历史 V6 实验：代码仍读取 V6 句卡和旧数据路径，部分依赖文件已不存在。当前不能视为可用的 V7 分析 API。

## 文件清单

| 文件 | 来源 | 职责 |
|---|---|---|
| `app.py` | `新题解析模块/api/server.py` | HTTP 服务（`http.server`），路由分发 |
| `logic.py` | `新题解析模块/pipeline/run_pipeline.py` | 核心流水线：拆题 → 检索 → 盲判 → 解析 → 校验 |
| `evidence_pool.py` | `新题解析模块/pipeline/evidence_pool.py` | 加载 BGE/BM25/句卡池，runtime 单例 |
| `question_parser.py` | `新题解析模块/pipeline/question_parser.py` | LLM 拆解题干+选项，regex 优先 → LLM 兜底 |
| `run_agentic_search_experiment.py` | `四角色法/` | Agentic 检索（planner + 多路召回） |
| `run_blind_q212_experiment.py` | `四角色法/` | 盲判裁判 prompt 构建 + 结果规范化 |
| `run_step1.py` | `四角色法/` | LLM 调用封装、路径常量、工具函数 |
| `prompts/*.md` | `新题解析模块/prompts/` | LLM 用到的 prompt 模板（4个） |

所有文件同一目录，无子包结构，`import xxx` 直接引用。

## 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/new-question/health` | 健康检查 |
| GET | `/api/new-question/drafts` | 草稿列表（最近 50 条） |
| GET | `/api/new-question/drafts/<id>` | 读取草稿 |
| POST | `/api/new-question/analyze` | `{"text":"...", "top_k":30}` → 分析新题 |
| DELETE | `/api/new-question/drafts/<id>` | 删除草稿 |

## 流水线步骤（logic.py）

1. **拆题** — `question_parser.py`：从粘贴文本拆出 stem + options{A..D} + detected_answer
2. **检索规划** — planner LLM：为每个选项生成 search_queries / must_terms
3. **证据召回** — `retrieve_for_option()`：BGE + BM25 + 精确短语 + 关系扩展
4. **盲判裁判** — adjudicator LLM：不依赖标准答案，基于句卡证据判断选项对错
5. **答案复核** — reviewer LLM：逐项复核裁判是否有误
6. **考查方向** — LLM 提炼一句"这道题在考什么"

## 外部依赖（pip）

- `openai` — DeepSeek API（兼容 OpenAI SDK）
- `sentence-transformers` — BGE `BAAI/bge-small-zh-v1.5`
- `jieba` — 中文分词
- `numpy` — 向量运算

需要的环境变量：`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DS_MODEL`

## 当前状态

HTTP 外壳可能启动，但完整分析链依赖缺失的 V6 句卡/KG 资产，当前不保证可用。

### 已处理的问题
- 所有 `sys.path` / `from pipeline.xxx` 改为同目录直接 import
- KG 文件缺失 → 容忍降级，不阻塞启动
- `card_relations.json` 缺失 → 已有 `.exists()` 容错
- 数据路径指向新工作区 `data/`

### 待处理
- KG 数据需从 `kg_data.json` 重建 `sections/edges/card_section_map` 三个视图
- `card_relations.json` 需从旧工作区迁移

## 启动

```bash
cd "D:\守正公司工作区\cams考试\cams工作台（重构版）\services\新题解析"
python app.py
# → http://127.0.0.1:8765
```
