# 运行资源

`runtime` 用于保存不适合普通源码仓库的本地运行资源。

## 当前内容

- `models/manifest.json`：CAMS 使用的 BGE-M3 快照、路径和权重哈希。
- `models/bge-m3/`：`BAAI/bge-m3` 的 Sentence Transformers PyTorch 文件，排除了 ONNX 副本。
- `models/bge-m3/README.md`：上游模型卡，不是 CAMS 运行说明。

`manifest.json` 中的 `status=ready` 只表示模型资产已经放置，不证明 Python 依赖兼容、模型可加载或真实检索通过。

## 路径优先级

1. `CAMS_BGE_MODEL_PATH`。
2. 工作台内 `runtime/models/bge-m3`。
3. 本机 Hugging Face 缓存/模型标识；代码仍按离线模式加载。

正式交付包应固定使用第 2 种路径，避免依赖用户缓存。

## 当前故障与验收

现有 Windows 组合 `sentence-transformers 3.4.1` + `transformers 4.57.6` 在 tokenizer 阶段加载失败。接手者应在隔离环境确定精确兼容版本并生成平台锁文件。

验收必须在断网状态下完成：

1. 校验模型权重 SHA-256。
2. 加载本地模型。
3. 对非空文本执行 `encode`。
4. 完成一次一般检索和一次题目检索。

macOS 正式包还需要 `runtime/python` 中经过重定位验证的 arm64 Python；当前目录没有该运行时。
