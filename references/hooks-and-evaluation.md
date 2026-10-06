# Hooks and Evaluation

本文档把 guard 审计与评估机制落到 `paper-master-4ss` 项目。目标是把高风险质量规则沉淀为机制层约束，而不是依赖顾问口头提醒。机制层由两个通用能力构成：`guard_after_command`（分析命令执行后复核 run-log 与产物）与 `guard_before_finish`（交付/停止前校验项目状态与交接状态）。任何宿主都可以通过**显式运行 guard 命令**满足这两个能力；有 hook 机制的宿主可通过注册器自动触发（见第 2 节），注册与否不改变 guard 的语义。

## 1. 双层 Guard 方案

- **Skill 层**：可复用脚本（`scripts/paper_master_guard.py`）随 `paper-master-4ss` 版本管理，是 guard 的唯一实现（单一事实源）。本包不在 skill frontmatter 声明任何 hooks。
- **宿主/项目层（可选）**：宿主自己的 hook 机制指向本包的 guard 脚本，从而自动触发。注册由 `scripts/register_host_hooks.py` 完成（见第 2 节），或由包外适配层/用户自行配置。
- **手动层（始终可用）**：任何宿主在任何时候都可以显式运行第 4 节的两条命令；注册失败、当次会话尚未生效、宿主无 hook 机制时一律走这一层。
- 注册或自动触发**不能替代**显式运行：当次会话若未确认 hook 已生效，仍显式运行两条命令。
- 不把本包当作 Claude Code plugin 安装，也不为它创建整套宿主专属配置（如 `.claude/settings.json` 全量模板）；需要自动触发时只用第 2 节的注册器**追加本包所需的 guard 项**，或让包外适配层接管。

## 2. 注册宿主 hooks（`scripts/register_host_hooks.py`）

```bash
python3 scripts/register_host_hooks.py --host auto    # 自动探测（默认）；无证据时不写任何文件
python3 scripts/register_host_hooks.py --host auto --check   # 只读查询（0=已注册，1=未注册，2=未知宿主）
python3 scripts/register_host_hooks.py --host <name>  # 显式指定宿主
python3 scripts/register_host_hooks.py --print        # 只打印将要写入/手工粘贴的配置，不写文件
python3 scripts/register_host_hooks.py --host <name> --remove   # 撤销本包插入的 guard 项
```

- 宿主名与目标文件、事件名、matcher 由脚本内置的 backend 定义；`--print` 可查看当前支持的宿主与生成的配置形状，未知宿主会打印**通用契约**（两条 guard 命令 + 退出码约定）供手工配置。
- **安全规则**：只在有明确证据时写入（`--host auto` 无证据时退出码 2 且不写任何文件）；写前备份为 `<file>.paper-master.bak`；只追加本包所需的 hook 项，不覆盖用户已有配置；幂等，重复执行不产生重复项。
- **运行时不变量优先**：若会话暴露了「外层运行时自带 hook 层」的标记（例如带有 preset/平台 hook 的 harness 环境变量），`--host auto` 直接判定为无需注册并退出码 2，**即使项目里恰好存在某宿主的配置目录也不写入**；确有需要时用 `--host <name>` 显式指定。
- **优先使用宿主已有的 hook 机制**：若宿主/包外适配层已经提供 guard 自动触发，不要重复注册。
- 退出码约定：`0` 成功/已注册；`1` 未注册（`--check`）或目标配置无法解析（不写）；`2` 未知宿主或自动探测无证据（不写）。
- 命令里的路径：优先使用本包内的显式相对路径或由包外适配层注入的根路径变量，**不要依赖 `${CLAUDE_PLUGIN_ROOT}`** 之类的宿主专有变量。
- 注册后仍需注意宿主对 hook stdout 的解析要求（例如某些宿主按 JSON 解析 stdout、纯文本会被判为 failed）；guard 脚本对这类宿主提供输出重定向的写法，见第 7 节样例。

## 3. Guard 职责边界

### `guard_after_command`（命令后审计）

触发条件：本会话执行过的命令/工具调用涉及 `Rscript`、`python3/python`、`.do/.R/.py`、`paper-workspace/04-analysis`，或 Stata MCP 调用（`stata_run_file`/`stata_run_selection`）等分析执行；调用后读取最新 run-log 复核。

处理器：`paper_master_guard.py post-bash`。

结果回灌：

- 检查最新 `paper-workspace/04-analysis/reports/run-log-[date].md`。
- 标记 `blocked`、`error`、`failed`、`traceback`、Stata `r(...)`、R `Execution halted`、非零退出码。
- 检查 run-log 是否记录 stdout/stderr 路径。
- 检查 run-log 登记的输出文件是否存在。
- 写入 `paper-workspace/_logs/hook-audit/analysis-log-audit-[date].md`。
- 默认退出 0（仅把问题写 stderr）；加 `--strict` 时存在审计问题退出 2，便于宿主把问题回灌给 agent。

`guard_after_command` 不能撤销已经执行的命令；它只负责把错误和证据缺口回灌给 agent。审计文件必须被分析报告读取，不能把失败或未验证脚本写成统计结论。自动触发由宿主 hook 提供（见第 2 节与第 7 节样例）；无自动触发时**必须**显式运行 `paper_master_guard.py post-bash`。

### `guard_before_finish`（交付前阻断）

触发条件：会话停止前 / 模块交付前。

处理器：`paper_master_guard.py stop-check`。

阻断规则：

- 若当前项目没有 `paper-workspace/`，不阻断。
- 若没有模块产物或流程日志，不阻断。
- 若已有模块产物或流程日志，但 `_index/project-state.md` 或 `_index/handoff-status.md` 缺失/早于最新关键产物，`exit 2` 阻断停止。

`guard_before_finish` 是交付前的机制约束：模块产物写完后必须更新项目状态和交接状态。自动触发由宿主 hook 提供；无自动触发时**必须**显式运行 `paper_master_guard.py stop-check`。

## 4. 手动命令

```bash
python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace
python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace --strict   # 审计问题即 exit 2
python3 scripts/paper_master_guard.py stop-check --workspace paper-workspace
python3 scripts/paper_master_guard.py score-project --workspace paper-workspace --json
```

## 5. 输出文件

- `paper-workspace/_logs/hook-audit/analysis-log-audit-[YYYY-MM-DD].md`
- `paper-workspace/_index/quality-score.md`
- `paper-workspace/_index/quality-score.json`

## 6. 失败处理

- Guard 审计有问题：先修复日志、脚本执行或输出文件，再写分析结论。
- `guard_before_finish` 阻断：更新 `project-state.md` 和 `handoff-status.md`，说明最新产物、质量分、阻断项和下一步。
- Rubric 分数低：读取 `quality-score.md` 的 `failure_attribution` 和 `fix_next`，按数据、工具、流程、知识、提示或执行环境归因修复。
- 注册器报未知宿主或探测无证据：不改任何文件，按 `--print` 的通用契约手工配置，或始终显式运行第 4 节命令。

## 7. 已知宿主注册样例（样例，非宿主名单）

下列形状由 `register_host_hooks.py --print` 生成，仅用于对照；其他宿主按第 2 节的通用契约自行配置。把 `<PAPER_MASTER_4SS_ROOT>` 替换为本 skill 目录绝对路径（例如 `/Users/yjy/.skills-manager/skills/paper-master-4ss`）。

**Claude Code 兼容层** — 项目根 `.claude/settings.json`（只合并 `hooks` 节点）：

```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "Bash", "hooks": [ { "type": "command",
        "command": "python3 <PAPER_MASTER_4SS_ROOT>/scripts/paper_master_guard.py post-bash --workspace paper-workspace" } ] }
    ],
    "Stop": [
      { "matcher": "", "hooks": [ { "type": "command",
        "command": "python3 <PAPER_MASTER_4SS_ROOT>/scripts/paper_master_guard.py stop-check --workspace paper-workspace" } ] }
    ]
  }
}
```

**Antigravity** — 项目根 `.agents/hooks.json`：

```json
{
  "paper-master-guard": {
    "PostToolUse": [
      { "matcher": "run_command", "hooks": [ { "type": "command",
        "command": "python3 <PAPER_MASTER_4SS_ROOT>/scripts/paper_master_guard.py post-bash --workspace paper-workspace" } ] }
    ],
    "Stop": [
      { "type": "command",
        "command": "python3 <PAPER_MASTER_4SS_ROOT>/scripts/paper_master_guard.py stop-check --workspace paper-workspace" }
    ]
  }
}
```

**ZCode** — `~/.zcode/cli/config.json`（由 `--host zcode` 写入；`hooks.enabled: true`，matcher 为正则 `^Bash$`，guard stdout 经 `>/dev/null` 丢弃，因为 ZCode 按 strict-schema JSON 解析 hook stdout、纯文本会被标记为 failed）：

```json
{
  "hooks": {
    "enabled": true,
    "events": {
      "PostToolUse": [
        { "matcher": "^Bash$", "hooks": [ { "type": "command", "timeoutMs": 30000,
          "command": "python3 <PAPER_MASTER_4SS_ROOT>/scripts/paper_master_guard.py post-bash --workspace paper-workspace >/dev/null" } ] }
      ],
      "Stop": [
        { "hooks": [ { "type": "command", "timeoutMs": 30000,
          "command": "python3 <PAPER_MASTER_4SS_ROOT>/scripts/paper_master_guard.py stop-check --workspace paper-workspace >/dev/null" } ] }
      ]
    }
  }
}
```

`scripts/register_zcode_hooks.py` 是 `--host zcode` 的等价 shim，保留给历史文档与已有用户的调用习惯。guard 在没有 `paper-workspace/` 的目录静默退出，注册对其他项目无副作用；注册当次会话仍按第 4 节显式运行，配置从下一次会话起自动触发。
