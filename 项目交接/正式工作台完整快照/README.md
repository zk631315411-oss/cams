# CAMS 正式工作台完整快照

本目录保存 2026-07-30 的正式工作台 Windows 开发基线。快照包含原目录的全部内容，包括 `.venv`、BGE-M3 模型、395 题数据、冻结教材和索引、独立 `.git` 历史及本机运行文件。

## 基线

- 原路径：`D:/守正公司工作区/cams考试工作台（正式版）/`
- 原独立 Git HEAD：`d93697374eab7ad5d23813c9ca5ae708eaf7192f`
- 原独立 Git 状态：`main`，工作树干净，无远端
- 父 CAMS 仓库交接标签：`formal-workbench-handoff-20260730`
- 压缩格式：`tar.gz`，按 1 GiB 拆分为 Git LFS 分卷
- 压缩包字节数：`1790622503`
- 压缩包 SHA-256：`6A2A04B6542B04AA7849B637BDC5A5D29F13982D11A99FD4AFBFAF061B0539B1`
- 解包文件数：`39655`
- 解包文件总字节数：`3666008974`
- BGE-M3 `pytorch_model.bin` SHA-256：`B5E0CE3470ABF5EF3831AA1BD5553B486803E83251590AB7FF35A117CF6AAD38`

| 分卷 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `formal-workbench-20260730.tar.gz.part-000` | 1073741824 | `5CA3474D4F955B191E318C7520A0B95FCBFA16AD47B3E7F76BFF2424D9DA22BB` |
| `formal-workbench-20260730.tar.gz.part-001` | 716880679 | `36A6898CB4117FE7F2805FDE3BB7007568674872FA01A78CE3153A928FC285CA` |

## 公司管理员验收

```powershell
git clone <current-repository-url>
cd cams
git lfs pull
powershell -ExecutionPolicy Bypass -File ".\项目交接\正式工作台完整快照\restore-snapshot.ps1" -Destination "D:\CAMS交接验收"
```

脚本先校验两个分卷，再重组并校验完整压缩包，最后解压到指定目录。解压后工作台位于 `<Destination>/cams考试工作台（正式版）/`。

管理员完成异机复原后，应将全部分支、标签和 LFS 对象镜像到公司私有仓库：

```powershell
git clone --mirror <current-repository-url> cams-mirror.git
cd cams-mirror.git
git lfs fetch --all origin
git remote add company <company-private-repository-url>
git push --mirror company
git lfs push --all company
```

## 边界

- 快照用于离职交接、复原和取证，不作为日常开发目录。
- 日常维护使用仓库根目录的 `cams考试工作台（正式版）/`。
- 当前仍是 Windows 开发候选版：395 题处于 `evidence_research / active`，`releases/` 为空，BGE-M3、恢复流程和 macOS M3 尚未完成验收。
- Git 历史中出现过的旧 API Key 必须在供应商后台吊销；不得通过快照恢复旧密钥。
