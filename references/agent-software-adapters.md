# 运行环境工具形态与 Hook 格式对照

本文档为运行环境适配参考表，按工具的功能形态与 hook 配置结构进行归类，不维护固定软件名单。会话启动时应按 `references/runtime-adapter.md` §5 探测实际能力并写入 `paper-workspace/_index/runtime-capabilities.md`；遇到表中未覆盖的新工具形态时，直接按通用回退方案处理，无需修改本包。

## 1. 工具形态与通用能力映射

| 工具形态 | 特征描述 | 映射能力 | 优先级 |
|---|---|---|---|
| 专用文件读取工具 | 支持读取文本或非文本文件 | `read_file` | 首选 |
| 仅命令行读取 | 无专用读取工具，通过 shell（`cat` / `sed` / `Get-Content`）读取 | `read_file` | 降级 |
| 专用全文检索工具 | 支持 grep / glob 跨目录检索 | `search_text` | 首选 |
| 仅命令行检索 | 无专用检索工具，通过 shell（`rg` / `grep`）检索 | `search_text` | 降级 |
| 专用文件写入工具 | 支持整文件覆写或局部编辑 | `write_file` | 首选 |
| 补丁式编辑工具 | 支持按上下文 diff 应用补丁（如 `apply_patch`） | `write_file` | 等价 |
| 命令执行环境 | 支持在指定工作目录及超时限制下执行 shell 命令 | `run_shell` | 必需 |
| 联网搜索工具 | 返回网页检索条目与摘要 | `web_search` | 可选 |
| 网页抓取工具 | 按 URL 获取网页正文内容 | `web_fetch` | 可选 |
| 可见浏览器控制 | 通过外部命令驱动真实浏览器进行交互与截图 | `browser_control` | 见 `paper-master-4ss/modules/lit/references/browser.md`、`paper-master-4ss/modules/lit/references/cnki.md` |
| 结构化提问工具 | 支持每次 1–4 个问题、每题 2–4 个选项的交互 | `ask_user` | 首选 |
| 纯文本对话确认 | 无结构化提问工具，在回复正文列明选项供确认 | `ask_user` | 降级 |
| 单子代理派发工具 | 支持派发单个独立子任务 | `spawn_agent` | 可选 |
| 批量子代理派发工具 | 支持在单次调用或并发调用中派发多个独立子任务 | `parallel_review` | 可选 |
| 同角色多席位辩论 | 支持同角色多席位互辩 | `multi_seat_debate`（可选） | 缺失时按 `sequential-review` 处理 |
| 命令后事件钩子 | 运行环境在工具调用后自动执行配置命令 | `guard_after_command` | 见 §2 |
| 会话结束前事件钩子 | 运行环境在会话停止前自动执行配置命令 | `guard_before_finish` | 见 §2 |
| 项目规则自动加载 | 运行环境自动读取工作区内的项目指令文件 | `project_memory` | 见 §4 |

无法归类或无法确定可用性时，一律标记为 `unknown`，按 `references/runtime-adapter.md` §1 的对应回退方案执行，不得假定可用。

## 2. Hook 配置格式（A / B / C 三型）

自动 hook 根据运行环境配置文件的嵌套结构分为以下三种格式。其中 `<ROOT>` 须替换为本技能包根目录的绝对路径。

**A 型：项目级配置（事件下嵌套 `hooks` 数组）**

```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "<命令工具名>", "hooks": [ { "type": "command", "command": "python3 <ROOT>/scripts/paper_master_guard.py post-bash --workspace paper-workspace" } ] }
    ],
    "Stop": [
      { "matcher": "", "hooks": [ { "type": "command", "command": "python3 <ROOT>/scripts/paper_master_guard.py stop-check --workspace paper-workspace" } ] }
    ]
  }
}
```

**B 型：用户级配置（`events` 嵌套并附带 `enabled` 开关）**

```json
{
  "hooks": {
    "enabled": true,
    "events": {
      "PostToolUse": [
        { "matcher": "<正则或工具名>", "hooks": [ { "type": "command", "timeoutMs": 30000, "command": "python3 <ROOT>/scripts/paper_master_guard.py post-bash --workspace paper-workspace >/dev/null" } ] }
      ],
      "Stop": [
        { "hooks": [ { "type": "command", "timeoutMs": 30000, "command": "python3 <ROOT>/scripts/paper_master_guard.py stop-check --workspace paper-workspace >/dev/null" } ] }
      ]
    }
  }
}
```

注：部分 B 型运行环境将 hook 的 stdout 解析为严格 JSON，输出纯文本会导致执行被判失败，此时应在命令末尾追加 `>/dev/null`，仅保留退出码与 stderr。

**C 型：命名空间块配置（Post 事件嵌套 `hooks` 数组，Stop 为扁平数组）**

```json
{
  "paper-master-guard": {
    "PostToolUse": [
      { "matcher": "<命令工具名>", "hooks": [ { "type": "command", "command": "python3 <ROOT>/scripts/paper_master_guard.py post-bash --workspace paper-workspace" } ] }
    ],
    "Stop": [
      { "type": "command", "command": "python3 <ROOT>/scripts/paper_master_guard.py stop-check --workspace paper-workspace" }
    ]
  }
}
```

上述三种格式均调用 `scripts/paper_master_guard.py` 并遵循统一退出码约定（`post-bash` 正常为 `0`，`--strict` 发现问题为 `2`；`stop-check` 阻断为 `2`）。未检测到 `paper-workspace/` 目录时，脚本静默退出（退出码 `0`），不会影响其他项目。

## 3. 通用注册脚本

使用 `scripts/register_host_hooks.py` 管理配置文件中的 hook 注册项：

```bash
python3 scripts/register_host_hooks.py --detect    # 只读：列出目录树中含 hooks 键的 JSON 文件
python3 scripts/register_host_hooks.py --setup     # 交互向导：选择配置文件、格式与 matcher，保存 profile 并注册
python3 scripts/register_host_hooks.py --check     # 只读：查询两条 hook 是否已注册
python3 scripts/register_host_hooks.py --print     # 只读：打印待配置片段，不写入文件
python3 scripts/register_host_hooks.py --remove    # 撤销：仅移除本包注册的 hook 项
```

profile 默认保存至 `<项目根目录>/.paper-master/host-profile.json`（可通过 `--profile <file>` 指定路径），记录目标配置文件、格式类型、事件路径及 matcher 名称。脚本执行写入前会备份原文件为 `*.paper-master.bak`，仅增量修改 hook 字段，JSON 解析失败时不做任何写入。若运行环境自带内置 hook 机制，可直接使用其自带机制而无需运行本脚本。

## 4. 项目规则（`project_memory`）

优先写入当前运行环境已加载的项目规则文件内的 `paper-master-4ss` 标记块；无此类文件时回退写入 `paper-workspace/_index/project-rules.md`，严禁写入技能包目录（详见 `references/project-rules-writing-layer.md`）。

## 5. 运行环境适配契约

1. **禁止虚构能力**：缺失任一能力时须如实记录缺失、暂缓执行、网络不可达或采用顺序复核，不得声称已完成对应工具操作。
2. **禁止声明环境专属 Frontmatter**：技能与顾问文件仅使用 `name`、`description` 及可选 `capabilities`，不得包含 `tools`、`allowed-tools`、`hooks`、`model`、`user-invocable`、`argument-hint`（`invocable`、`args_hint` 已废弃）。
3. **工具名仅作探测线索**：任何具体工具签名仅用于环境识别，实际执行通过通用能力映射完成。
4. **不依赖插件变量**：不依赖 `*_PLUGIN_ROOT` 等特定运行时变量，不假定 frontmatter 中的 hooks 生效，不修改全局系统设置。
5. **文档使用动作描述**：业务规程中使用通用能力或动作名称，不使用特定环境的专有工具名。
6. **允许包外扩展覆盖**：运行环境可通过外部 preset、插件或项目规则文件提供更精确的工具映射与自动审计，但须保持产物结构不变。
7. **保持输出契约稳定**：所有运行环境下，`paper-workspace/` 目录结构、顾问标准名、质量评分文件（`_index/quality-score.md` / `.json`）及 guard 命令接口须保持一致。
