# CAMS V7 教研工作台前端

前端使用 HTML、CSS 和原生 JavaScript；`server.py` 仅按需渲染当前教材 PDF 页，不调用检索模型、LLM、新题解析 API 或学生答疑 API。

顶部保留“看书备课 / 新题解析 / 学生答疑”工作模式及应用内前进、后退导航。后两种模式当前保留输入与状态位，提交操作会在 v7 API 接入前保持禁用。

## 发布包契约

运行时先请求 `data/releases/v7/textbook-active.json`，加载其中 `release_path` 下的：

- `manifest.json`：教材版本、来源、数量、校验状态与文件哈希。
- `chapters.json`：教材目录和单元顺序。
- `units.json`：双语教材知识单元及页码、上下文。
- `page-map.json`：中文和英文 PDF 的同页映射。
- `textbook-zh.pdf`、`textbook-en.pdf`：可切换或同页对照的教材原文。

若存在可选的 `data/releases/v7/active.json`，前端仅在其冻结单元哈希与教材包一致时加载 `questions.json` 与 `evidence.json`。如果不存在证据包，教材仍可阅读；界面会明确显示“题目证据待发布”，不会回退到 v6 数据或实验跑批目录。

## 模块边界

- `js/store.js` 验证和装配教材包，并校验可选证据包与教材版本一致。
- `js/reader.js` 渲染教材目录以及中文、英文、对照 PDF 阅读器（图片渲染 + 虚拟滚动加载，支持缩放和分页跳转）。
- `js/panel.js` 渲染右侧详情面板：首页（`renderHome`）、单元详情（`renderUnit`）、题目证据链（`renderQuestion`）、工作流模式（`renderWorkflow`）。
- `js/search.js` 搜索教材单元、题目和已发布解析。
- `js/app.js` 主控模块：路由、历史导航（前进/后退栈）、工作模式切换、顶层协调。
- `js/layout.js` 可拖拽面板布局：TOC/详情面板宽度调节、PDF 阅读区高度调节、布局持久化到 localStorage。
- `js/utils.js` 工具函数库：HTML 转义、文本处理、DOM 辅助。
- `js/feedback.js` 本地反馈收集（localStorage 存储 + JSON 导出）。

发布命令见 `../tools/v7_release/README.md`。

本地启动：`python server.py --port 5175`。不要使用普通静态服务器启动阅读器，否则 PDF 页面渲染接口不可用。
