# Codex 历史侧栏 provider 同步修复交接

## 目标

把 Codex 历史会话里用于侧栏过滤的 provider 元数据统一为：

```text
cc_switch
```

只同步 Codex 看到的 provider 名称，不修改真实服务商配置，不修改 API key，不修改 base_url，不删除会话，不重建数据库。

## 当前已确认的状态

配置层正常：

```text
C:\Users\hp\.codex\config.toml
  model_provider = "cc_switch"
  [model_providers.cc_switch]
  base_url = "http://127.0.0.1:15721/v1"

C:\Users\hp\.cc-switch\cc-switch.db
  providers 表中 9 个 Codex provider 模板都是 cc_switch
  proxy_live_backup.original_config 也是 cc_switch
```

问题在历史会话源数据：

```text
C:\Users\hp\.codex\sessions\...\rollout-*.jsonl
```

这些 rollout 文件里的 `session_meta.payload.model_provider` 仍然是旧 provider。Codex 重启/加载时会从这些 `session_meta` 回填 SQLite，所以之前只改 `state_5.sqlite` 会被恢复成旧值。

已抽样确认：

```text
019ec1c9-02fa-75c0-abe6-6c97d0a6092f
  rollout 中 11 条 session_meta 全是 xmai

019ec197-49e2-74d2-8a98-2c89715e1e11
  rollout 中 14 条 session_meta 全是 xmai

019eb702-66e8-7cd3-a43a-a12c552e2893
  rollout 中 155 条 session_meta 全是 coding

当前新线程 019ec1ee-8c0b-7e31-9625-7668f4e75729
  rollout 中 6 条 session_meta 全是 cc_switch
```

主库中所有非 `cc_switch` 的 42 条线程，`threads.model_provider` 与对应 rollout 里的 `session_meta.payload.model_provider` 完全一致，`mismatch = 0`。因此旧 provider 回退源头已经基本坐实为 rollout `session_meta`。

## DS 疑问答复

### 1. Codex Desktop 现在关了吗？

没有。

用户当前仍在 Codex Desktop 里和本线程对话，并且只读进程检查也能看到多个 Codex 进程和一个 CC Switch 进程仍在运行，例如：

```text
Codex.exe
codex.exe
node_repl.exe
cc-switch.exe
```

所以现在不能执行正式修改。正式改 rollout 和 SQLite 前，用户必须先完整退出 Codex Desktop。建议 CC Switch 也一起退出。

### 2. CC Switch 的 provider 模板是谁改完的？

这是前面抢救过程中手动补丁改好的，不是已经确认的 CC Switch 官方原生行为。

当前只读核验结果是：

```text
C:\Users\hp\.cc-switch\cc-switch.db
providers 表中 9 个 app_type = codex 的 settings_config 都已经是 cc_switch
proxy_live_backup.original_config 解析后的 config 也是 cc_switch
```

核验到每个 Codex provider 模板都包含：

```toml
model_provider = "cc_switch"
[model_providers.cc_switch]
name = "cc_switch"
```

并且没有旧的：

```text
model_provider = "xmai"
model_provider = "coding"
model_provider = "my_codex"
model_provider = "gpt"
model_provider = "custom"
```

因此，只要 CC Switch 继续使用当前数据库里的这些模板，热切换不应再把 `config.toml` 覆盖回旧 provider 名。

但注意：这不是官方保证。如果 CC Switch 未来升级、重置 provider、重新导入 provider，或者从其他默认模板重建配置，仍可能重新写回旧名。修复后建议做一次热切换测试，并复查：

```text
C:\Users\hp\.codex\config.toml
C:\Users\hp\.cc-switch\cc-switch.db providers.settings_config
C:\Users\hp\.cc-switch\cc-switch.db proxy_live_backup.original_config
```

### 3. archived_sessions 目录存在吗？有多少 rollout？

存在。

只读统计结果：

```text
C:\Users\hp\.codex\sessions
  rollout_count = 62
  session_meta_lines = 710
  provider_counts:
    FAC: 11
    my_codex: 151
    coding: 374
    gpt: 137
    xmai: 27
    cc_switch: 10

C:\Users\hp\.codex\archived_sessions
  rollout_count = 29
  session_meta_lines = 314
  provider_counts:
    FAC: 5
    coding: 235
    my_codex: 73
    gpt: 1
```

因此正式同步范围应包含：

```text
C:\Users\hp\.codex\sessions
C:\Users\hp\.codex\archived_sessions
```

但仍然只改每个 rollout JSONL 中：

```text
type == "session_meta"
payload.model_provider
```

不要改对话正文或 tool 输出中的普通文本。

## 退出要求

执行修改前，建议用户先完整退出：

```text
Codex Desktop
CC Switch
```

至少必须退出 Codex Desktop，避免它同时写入：

```text
C:\Users\hp\.codex\sqlite\state_5.sqlite-wal
C:\Users\hp\.codex\sessions\...\rollout-*.jsonl
```

## 必须备份

新建时间戳备份目录，例如：

```text
D:\ai-math\codex抢救\provider_sync_before_YYYYMMDD_HHMMSS
```

至少备份：

```text
C:\Users\hp\.codex\sqlite\state_5.sqlite
C:\Users\hp\.codex\sqlite\state_5.sqlite-wal
C:\Users\hp\.codex\sqlite\state_5.sqlite-shm
C:\Users\hp\.codex\state_5.sqlite
C:\Users\hp\.codex\state_5.sqlite-wal   如果存在
C:\Users\hp\.codex\state_5.sqlite-shm   如果存在
C:\Users\hp\.codex\session_index.jsonl
C:\Users\hp\.codex\.codex-global-state.json
所有将被修改的 rollout-*.jsonl
```

不要覆盖旧备份：

```text
D:\ai-math\codex抢救\backup_20260614
D:\ai-math\codex抢救\current_before_provider_patch_20260614_004456
D:\ai-math\codex抢救\current_before_provider_patch_20260614_005344
```

## 修改范围

### 1. 修改 rollout JSONL

扫描：

```text
C:\Users\hp\.codex\sessions
C:\Users\hp\.codex\archived_sessions
```

只修改 JSONL 中满足以下条件的记录：

```json
{
  "type": "session_meta",
  "payload": {
    "model_provider": "旧值"
  }
}
```

把旧值改成：

```json
"model_provider": "cc_switch"
```

旧值包括但不限于：

```text
xmai
coding
my_codex
gpt
FAC
custom
```

不要改其他 JSONL 记录类型，例如：

```text
response_item
event_msg
function_call_output
custom_tool_call
custom_tool_call_output
```

不要对整个文件做纯文本全局替换。必须逐行 JSON 解析，只改 `type == "session_meta"` 的 `payload.model_provider`。

### 2. 修改主 SQLite

数据库：

```text
C:\Users\hp\.codex\sqlite\state_5.sqlite
```

执行：

```sql
update threads
set model_provider = 'cc_switch'
where model_provider is not null
  and model_provider != 'cc_switch';
```

### 3. 修改旧位置 SQLite

数据库：

```text
C:\Users\hp\.codex\state_5.sqlite
```

执行同样 SQL：

```sql
update threads
set model_provider = 'cc_switch'
where model_provider is not null
  and model_provider != 'cc_switch';
```

这一步可能是 no-op，但建议同步做，避免旧库参与回填或兼容逻辑。

## 不要修改

不要修改：

```text
C:\Users\hp\.codex\config.toml
C:\Users\hp\.cc-switch\cc-switch.db
C:\Users\hp\.cc-switch\settings.json
API key
真实 base_url
CC Switch provider id
providers.name
providers.is_current
currentProviderCodex
session_index.jsonl
.codex-global-state.json
```

`session_index.jsonl` 已确认只记录：

```text
id
thread_name
updated_at
```

它不是 provider 回退源头，除非验证阶段另有发现，否则不要改。

## 建议执行流程

1. 用户退出 Codex Desktop 和 CC Switch。
2. 运行 dry-run：
   - 统计将修改多少个 rollout 文件。
   - 统计将修改多少条 `session_meta`。
   - 统计旧 provider 分布。
   - 统计两个 SQLite 中 `threads.model_provider` 分布。
3. 备份所有目标文件。
4. 修改 rollout JSONL 的 `session_meta.payload.model_provider`。
5. 修改两个 SQLite 的 `threads.model_provider`。
6. 运行验证。
7. 用户重新打开 CC Switch 和 Codex Desktop。

## 验证项

修改后检查：

```sql
select model_provider, count(*)
from threads
group by model_provider
order by model_provider;
```

两个 SQLite 都应只剩：

```text
cc_switch
```

再扫描所有被修改的 rollout：

```text
所有 session_meta.payload.model_provider 都应为 cc_switch
```

重点线程必须仍能读取：

```text
019ec1c9-02fa-75c0-abe6-6c97d0a6092f
019ec197-49e2-74d2-8a98-2c89715e1e11
019eb702-66e8-7cd3-a43a-a12c552e2893
```

重启 Codex 后验证：

```text
list_threads 是否显示旧线程
按标题搜索是否能找到：
  读取最新聊天记录
  回复丢失对话
  检查未关闭进程
```

## 重要风险提示

这次修复只解决 provider 元数据不一致。

如果同步后侧栏仍不显示，还可能存在第二层问题：

```text
Codex Desktop 运行时缓存
archived 标记
workspace/root 路径规范化
backfill_state 水位
project-order / thread-workspace-root-hints
Codex Desktop 自身列表过滤逻辑
```

但不要在第一轮同步里同时改这些。先只做 provider 源数据同步，验证后再决定是否查第二层侧栏索引。
