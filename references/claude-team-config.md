# Claude Team Config Reference

本文档只提供 Claude Code Agent Teams 的配置参考。它不得自动修改用户的 shell 配置、`~/.claude.json` 或任何系统级文件。

## 1. 功能边界

- Agent Teams 是 Claude Code 的实验功能。启用前应先确认当前 Claude Code 版本支持该功能。
- 本技能只在用户显式触发 `teamagent`、`Agent Team`、`teammate`、`团队智能体`、`升格` 等意图时进入 Team 路由。
- 若环境未启用 Agent Teams，先向用户说明配置方式，再回退到 `master/agent-orchestration.md` 的普通 subagent 或顺序复核协议。
- 不得因为任务复杂就自动创建 Agent Team；Team 创建必须经过用户选择确认。

## 2. 版本与环境检查

建议用户先在 Claude Code 所在终端检查版本：

```bash
claude --version
```

若用户要求启用 Team，但环境变量未设置或 Claude Code 不支持，应提示用户完成配置后重新启动 Claude Code 会话。

## 3. 环境变量启用方式

临时启用方式：

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

长期启用可由用户自行加入 shell 配置文件，例如 `~/.zshrc` 或 `~/.bashrc`。本技能不得自动写入这些文件。

## 4. `~/.claude.json` 配置示例

用户也可以手动在 `~/.claude.json` 中加入：

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "in-process"
}
```

本示例只供用户复制或人工参考；本技能不得自动创建或修改 `~/.claude.json`。

## 5. 显示模式

`teammateMode` 可选值：

| 值 | 行为 | 建议场景 |
|---|---|---|
| `in-process` | 所有 teammate 在主 Claude Code 终端内运行 | 初次使用、轻量验证、无需多窗口 |
| `auto` | Claude Code 自动选择可用模式 | 用户不确定终端能力时 |

显式 Team 请求时，必须让用户选择显示模式，并把选择写入项目级 `CLAUDE.md` 的 paper-master 标记块。

## 6. 配置状态记录

项目级 `CLAUDE.md` 的 paper-master 标记块中应记录：

- 是否已提示用户启用 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`。
- 用户选择的 `teammateMode`。
- 若 Team 不可用，本次回退到普通 subagent 或顺序复核的原因。

这些记录只描述项目协作偏好和环境状态，不得包含用户 shell 配置文件全文或敏感 token。
