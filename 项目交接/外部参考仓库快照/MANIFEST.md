# 外部参考仓库快照清单

生成时间：2026-07-30

| 快照 | 原目录 | 上游/原远端 | HEAD | 快照时未提交项 | 大小 | SHA-256 |
|---|---|---|---|---:|---:|---|
| `DeepRefine-Skill.tar.gz` | `参考项目rag/DeepRefine-Skill/` | `https://github.com/HKUST-KnowComp/DeepRefine-Skill.git` | `e7f55f4` | 0 | 6.06 MB | `c4646f77d9d41b389ff6ccfe68a680e5381bcdd6d358968f4aeaa4e4219585e3` |
| `LightRAG.tar.gz` | `参考项目rag/LightRAG/` | `https://github.com/HKUDS/LightRAG.git` | `c67f055` | 2 | 14.49 MB | `03955c34bb722d8b76a52d16499a6645e8385a5a0b3d44bf8387af136b07f5fc` |
| `weknora-reference.tar.gz` | `参考项目rag/weknora/` | `https://github.com/Tencent/WeKnora.git` | `0392b739` | 4 | 99.31 MB | `4ee783de355a39cfe6f4bea7a577149eb692d3fd18cd59c63a80a8773ab9b05e` |
| `TreeKG-reference.tar.gz` | `cams工作台（重构版）/tools/知识图谱/提取/参考代码2/` | `https://github.com/lzl8800/TreeKG.git` | `7e9ee5f` | 0 | 0.41 MB | `49e13c35b3c43814d21a1fc2741a7716022043f32942079e2b7ff7f6a5c70003` |
| `weknora-v6-reuse.tar.gz` | `v6_归档/选项证据生成/weknora复用/` | `https://github.com/Tencent/WeKnora.git` | `0392b739` | 2 | 99.45 MB | `09906ba6daf95a5453f0814e608342e32d6e10f0aabf24508d0be83b9450dd41` |

“快照时未提交项”是 `git status --porcelain` 的记录数，只用于说明快照不是纯上游提交。压缩包内保留完整工作树和 `.git`，因此未提交修改也包含在内。

## 恢复

1. 在父目录解压对应 `tar.gz`。
2. 进入解压后的仓库执行 `git status`，核对 HEAD 和本地差异。
3. 不要把这些仓库当作 CAMS 正式依赖；需要继续研究时再单独建分支或远端。

本轮上传前已删除真实 `.env`，并对匹配到的凭据字面量做了脱敏。快照不用于恢复任何密钥。
