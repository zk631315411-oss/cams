# 检索模块

本目录是教材证据检索实现。`service.py` 是业务入口，`assets.py` 负责冻结资产和模型，`pipeline.py` 实现算法，`cli.py` 是调试入口。

## 两类检索

- `search_evidence`：一般检索。使用单个查询的 BGE-M3 + 对应语言 BM25，经 RRF 融合后做 KG 扩展；不生成题目检索头，不启用 P5，不生成选项补充池。
- `retrieve_question_evidence`：题目检索。生成中英文题干/选项检索头，启用 P5 术语归一、BGE-M3、双语 BM25、RRF、按检索头保底、KG 扩展和选项补充池。

完整输入输出见 [检索契约](../../docs/retrieval-contract.md)。

## 文件

- `service.py`：合并 `settings.toml` 与调用参数，选择一般或题目模式。
- `assets.py`：解析工作台路径、校验 manifest 资产哈希、加载 pickle/KG/P5、缓存资产、懒加载 BGE-M3。
- `pipeline.py`：分词、BM25、BGE、RRF、检索头平衡、KG 扩展和输出组装。
- `cli.py`：`search` 与 `question` 命令。当前直接执行会遇到导入错误，且题目模式的 `--top-k` 没有传入配置；修复前不能作为正式入口。

## 默认参数

| 参数 | 默认值 | 当前作用 |
| --- | ---: | --- |
| `profile` | `v7_legacy_202607` | 记录重构版参数快照名称 |
| `top_k` | 20 | 每个检索头、每种向量/词面路线的候选数 |
| `merge_top_k` | 30 | RRF 主候选上限 |
| `kg_max_extra` | 30 | KG 扩展候选上限 |
| `per_option_limit` | 3 | 每个选项补充池上限；一般检索强制为 0 |
| `per_head_minimum` | 2 | 题目检索每个检索头的最低保底轮数 |
| `rrf_k` | 60 | RRF 排名平滑参数，必须大于 0 |
| `section_context_range` | 4 | 当前只定义和校验，算法未使用；不得直接删除，需对照重构版确认 |
| `enable_kg` | true | 是否加载并执行 KG 扩展 |
| `enable_p5` | 题目模式 true | 是否启用 P5 术语归一；一般检索强制 false |

## 资产与缓存

读取 `data/infrastructure/textbook`、`index`、`kg` 和 `terms`。资产按工作台根目录及 KG/P5 开关缓存在进程内；磁盘资产更新后必须重启进程，当前没有热刷新接口。

BGE 模型优先使用 `CAMS_BGE_MODEL_PATH`，其次使用 `runtime/models/bge-m3`，最后使用离线 Hugging Face 标识。代码强制离线加载。

## 当前故障

Windows 现有 `sentence-transformers 3.4.1` 与 `transformers 4.57.6` 组合无法加载本地模型。模型目录和 manifest 存在不等于检索可用。修复后必须验证：离线模型加载、一次非空 `encode`、一般检索和题目检索。
