# Hooks and Evaluation

本文档把 guard 审计与评估机制落到 `paper-master-4ss` 项目。目标是把高风险质量规则沉淀为机制层约束，而不是依赖顾问口头提醒。Claude Code 可用 Hooks 自动触发；ZCode 通过 `scripts/register_zcode_hooks.py` 把 guard 注册进 `~/.zcode/cli/config.json` 后自动触发；OpenCode 与 Codex 按 `references/runtime-adapter.md` 显式运行同一 guard 命令。

## 1. 双层 Guard 方案

- Skill 层保存可复用脚本和 Claude Code 默认 Hook 配置，随 `paper-master-4ss` 版本管理。
- Claude Code 项目层可在用户论文项目根目录的 `.claude/settings.json` 启用 Hook，命令指向本 skill 的 `scripts/paper_master_guard.py`。
- ZCode 层由 `scripts/register_zcode_hooks.py` 把 PostToolUse(Bash) 与 Stop hooks 写入 `~/.zcode/cli/config.json` 并开启 `hooks.enabled`；首次注册的当次会话仍显式运行本文件第 5 节命令，后续会话自动触发。
- OpenCode 与 Codex 不要求创建 `.claude/settings.json`；若宿主没有自动 Hook，执行分析命令后和交付前显式运行本文件第 5 节命令。
- 项目层自动配置优先用于真实生效；手动命令用于 OpenCode/Codex、迁移和自包含说明。

## 2. Claude Code 项目级 `.claude/settings.json` 模板

把 `<PAPER_MASTER_4SS_ROOT>` 替换为本 skill 目录绝对路径，例如 `/Users/yjy/.skills-manager/skills/paper-master-4ss`。

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 <PAPER_MASTER_4SS_ROOT>/scripts/paper_master_guard.py post-bash --workspace paper-workspace"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 <PAPER_MASTER_4SS_ROOT>/scripts/paper_master_guard.py stop-check --workspace paper-workspace"
          }
        ]
      }
    ]
  }
}
```

若项目已有 `.claude/settings.json`，只合并 `hooks` 节点，不覆盖用户原有配置。OpenCode/Codex 不使用此模板，除非用户明确要兼容 Claude Code。

## 3. ZCode 注册

ZCode 不执行 skill frontmatter hooks；hooks 只来自 `~/.zcode/cli/config.json`（默认关闭，需 `hooks.enabled: true`）或插件 `hooks/hooks.json`。ZCode 宿主首次调用本 skill 时运行：

```bash
python3 scripts/register_zcode_hooks.py            # 注册（幂等，写前自动备份）
python3 scripts/register_zcode_hooks.py --check    # 只读查询注册状态
python3 scripts/register_zcode_hooks.py --remove   # 撤销注册
```

注册器把 `PostToolUse`（matcher `^Bash$`，正则、区分大小写）与 `Stop` 两个 command hook 写入用户配置，命令指向本包绝对路径的 `paper_master_guard.py`，只追加不覆盖，保留其他配置键。guard 命令的 stdout 经 `>/dev/null` 丢弃——ZCode 按 strict-schema JSON 解析 hook stdout，纯文本会标记为 failed；退出码与 stderr 保持有效：post-bash 通过为 0，stop-check 阻断为 2。guard 在没有 `paper-workspace/` 的目录静默退出，注册对其他项目无副作用。注册当次会话仍按第 5 节显式运行；配置从下一次会话起自动触发。

## 4. Guard 职责边界

### `guard_after_command` / Claude Code `PostToolUse(Bash)`

触发条件：Bash 命令涉及 `Rscript`、`python3/python`、`.do/.R/.py` 或 `paper-workspace/04-analysis`；Stata MCP 调用（statamcp 的 `stata_run_file`/`stata_run_selection`）同样按分析执行对待，调用后读取最新 run-log 复核。

处理器：`paper_master_guard.py post-bash`。

结果回灌：

- 检查最新 `paper-workspace/04-analysis/reports/run-log-[date].md`。
- 标记 `blocked`、`error`、`failed`、`traceback`、Stata `r(...)`、R `Execution halted`、非零退出码。
- 检查 run-log 是否记录 stdout/stderr 路径。
- 检查 run-log 登记的输出文件是否存在。
- 写入 `paper-workspace/_logs/hook-audit/analysis-log-audit-[date].md`。

`guard_after_command` 不能撤销已经执行的命令；它只负责把错误和证据缺口回灌给 agent。Claude Code 可由 `PostToolUse(Bash)` 自动触发；ZCode 注册后自动触发（注册当次会话显式运行）；OpenCode/Codex 必须显式运行 `paper_master_guard.py post-bash`。分析报告必须读取该审计文件，不能把失败或未验证脚本写成统计结论。

### `guard_before_finish` / Claude Code `Stop`

触发条件：会话停止前。

处理器：`paper_master_guard.py stop-check`。

阻断规则：

- 若当前项目没有 `paper-workspace/`，不阻断。
- 若没有模块产物或流程日志，不阻断。
- 若已有模块产物或流程日志，但 `_index/project-state.md` 或 `_index/handoff-status.md` 缺失/早于最新关键产物，`exit 2` 阻断停止。

`guard_before_finish` 是交付前的机制约束：模块产物写完后必须更新项目状态和交接状态。Claude Code 可由 `Stop` Hook 自动触发；ZCode 注册后自动触发（注册当次会话显式运行）；OpenCode/Codex 必须显式运行 `paper_master_guard.py stop-check`。

## 5. 手动命令

```bash
python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace
python3 scripts/paper_master_guard.py stop-check --workspace paper-workspace
python3 scripts/paper_master_guard.py score-project --workspace paper-workspace --json
```

## 6. 输出文件

- `paper-workspace/_logs/hook-audit/analysis-log-audit-[YYYY-MM-DD].md`
- `paper-workspace/_index/quality-score.md`
- `paper-workspace/_index/quality-score.json`

## 7. 失败处理

- Guard 审计有问题：先修复日志、脚本执行或输出文件，再写分析结论。
- `guard_before_finish` 阻断：更新 `project-state.md` 和 `handoff-status.md`，说明最新产物、质量分、阻断项和下一步。
- Rubric 分数低：读取 `quality-score.md` 的 `failure_attribution` 和 `fix_next`，按数据、工具、流程、知识、提示或执行环境归因修复。
