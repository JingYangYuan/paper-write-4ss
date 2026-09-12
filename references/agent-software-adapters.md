# Agent Software Adapters

本文档覆盖五类宿主：Claude Code、OpenCode、Codex、ZCode、OMP（Oh My Pi / Pi coding agent）。业务流程先按 `references/runtime-adapter.md` 使用通用能力名，再按下表映射到当前宿主。

## 1. 能力映射

| 通用能力 | Claude Code | OpenCode | Codex | ZCode | OMP |
|---|---|---|---|---|---|
| `read_file` | Read | 文件读取或 shell `cat/sed` | 文件读取或 shell `sed` | Read | Read |
| `search_text` | Grep/Glob | 搜索工具或 shell `rg` | shell `rg` | Bash 内 `rg`/`grep` + `find` | Grep/Glob（或 Bash `rg`） |
| `write_file` | Write/Edit | 文件编辑工具 | apply_patch 或文件编辑工具 | Write/Edit | Write/Edit |
| `run_shell` | Bash | shell/terminal | exec_command | Bash | Bash |
| `web_search` | WebSearch | 宿主搜索工具；无则记录缺失 | web search 工具；无则记录缺失 | WebSearch（或 exa web_search MCP） | `web_search`（或 exa MCP） |
| `web_fetch` | WebFetch | 宿主网页读取工具；无则记录缺失 | web open/fetch 工具；无则记录缺失 | WebFetch / web_reader MCP | `read`（URL）或 exa `web_fetch_exa` |
| `browser_control` | Chrome 扩展/浏览器 MCP；无则记录缺失 | 宿主浏览器能力；无则记录缺失 | 宿主浏览器能力；无则记录缺失 | 内置 browser-use（`mcp__node_repl__js` + browser client） | pi-chrome `chrome_*`（伴生扩展驱动真实 Chrome profile） |
| `ask_user` | AskUserQuestion 或直接提问 | 宿主提问能力或直接提问 | request_user_input 或直接提问 | AskUserQuestion 或直接提问 | `ask` 工具或直接提问 |
| `spawn_agent` | Task/subagent | OpenCode agent/subtask 能力；无则顺序复核 | Codex multi-agent/subagent 能力；无则顺序复核 | Agent 工具派发 subagent | `task` 工具派发 subagent |
| `parallel_review` | 多 Task 或 Agent Teams | 并行 subtask；无则 `sequential-review` | 并行 subagent；无则 `sequential-review` | 多 Agent 并行派发；无则 `sequential-review` | 单批 `tasks[]` 并行派发；无则 `sequential-review` |
| `guard_after_command` | `PostToolUse(Bash)` Hook | 显式运行 guard 命令 | 显式运行 guard 命令 | 注册后 config hook 自动触发；未注册或注册当次会话显式运行 | 显式运行 guard 命令（可用 `.omp/hooks/` 的 `tool_result` 扩展实现自动触发） |
| `guard_before_finish` | `Stop` Hook | 显式运行 guard 命令 | 显式运行 guard 命令 | 注册后 config hook 自动触发；未注册或注册当次会话显式运行 | 显式运行 guard 命令 |
| `project_memory` | `CLAUDE.md` 标记块 | OpenCode 项目规则文件；无则 `project-rules.md` | Codex/AGENTS 项目规则文件；无则 `project-rules.md` | 工作区 `AGENTS.md` 标记块；无则 `project-rules.md` | `.omp/AGENTS.md`（原生）或工作区 `AGENTS.md` 标记块；无则 `project-rules.md` |

## 2. Claude Code

- Claude Code 是原生宿主，保留 skill frontmatter hooks、项目级 `.claude/settings.json`、`CLAUDE.md` 和 Agent Teams 说明。
- `PostToolUse(Bash)` 实现 `guard_after_command`；`Stop` 实现 `guard_before_finish`。
- `CLAUDE.md` 是 `project_memory` 的 Claude Code 落点；维护方式见 `references/claude-md-writing-layer.md`。
- Agent Teams/teammate 是 Claude Code 专属高级并行形态。只有用户显式触发 Team 时，才读取 `references/claude-team-config.md` 与 `references/team-routing.md`。

## 3. OpenCode

- OpenCode 调用本 skill 时，必须先读取 `references/runtime-adapter.md` 与本文件，再按能力表执行。
- 无自动 Hook 时，在分析命令后显式运行：
  `python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace`。
- 交付前显式运行：
  `python3 scripts/paper_master_guard.py stop-check --workspace paper-workspace`。
- 若 OpenCode 没有可用 subagent 或并行任务能力，按派发清单顺序完成顾问复核，并在 `agent-brief.md` 与 `agent-synthesis` 记录 `sequential-review`。
- 若没有宿主项目规则文件，长期选择写入 `paper-workspace/_index/project-rules.md`，不要创建 `CLAUDE.md` 作为 OpenCode 的默认规则文件。

## 4. Codex

- Codex 调用本 skill 时，必须按 `references/runtime-adapter.md` 映射本地文件读取、`rg`、shell、web、用户确认和可用的 subagent 能力。
- 无自动 Hook 时，在分析命令后显式运行：
  `python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace`。
- 交付前显式运行：
  `python3 scripts/paper_master_guard.py stop-check --workspace paper-workspace`。
- 若没有可用多 agent 能力，按同一 canonical agent 清单顺序复核，并记录 `sequential-review`。
- 若没有 Codex 项目规则文件，长期选择写入 `paper-workspace/_index/project-rules.md`，不要创建 `CLAUDE.md` 作为 Codex 的默认规则文件。

## 5. ZCode

- ZCode 调用本 skill 时，必须先读取 `references/runtime-adapter.md` 与本文件，再按能力表执行。
- ZCode 不执行 skill frontmatter hooks：首次调用先运行 `python3 scripts/register_zcode_hooks.py`（幂等，写前备份；详见 `references/hooks-and-evaluation.md` 第 3 节），把 guard hooks 注册进 `~/.zcode/cli/config.json` 并开启 `hooks.enabled`；注册当次会话仍显式运行：
  `python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace` 与
  `python3 scripts/paper_master_guard.py stop-check --workspace paper-workspace`，后续会话由 config hooks 自动触发。
- 派发顾问用 Agent 工具（subagent），可在单条消息里并行派发多个实现 `parallel_review`；不可并行时记录 `sequential-review`。Agent Teams/teammate 是 Claude Code 专属形态，ZCode 不创建 Team，等价回退为并行 subagent 派发。
- 结构化提问用 AskUserQuestion；网页检索用 WebSearch/WebFetch 或已接入的 exa/web_reader MCP；Zotero 操作用已接入的 zotero MCP；桌面操纵用已接入的 computer-use MCP。
- 长期选择写入工作区 `AGENTS.md` 的 paper-master 标记块（维护纪律见 `references/claude-md-writing-layer.md`）；不要为 ZCode 默认创建 `CLAUDE.md`。

## 6. OMP（Oh My Pi / Pi coding agent）

- OMP 调用本 skill 时，必须先读取 `references/runtime-adapter.md` 与本文件，再按能力表执行。
- 文件与搜索用 `read` / `grep` / `glob`；命令用 `bash`；网页检索用 `web_search` 或已接入的 exa MCP，`read` 可直接读 URL 正文。
- 顾问派发用 `task` 工具，单批 `tasks[]` 即 `parallel_review`；只读调研用 `scout`，不可并行时记录 `sequential-review`。OMP 无 Agent Teams 形态，显式 Team 请求回退为普通顾问派发。
- 结构化提问用 `ask` 工具；Zotero 操作用已接入的 zotero MCP。
- **`browser_control` 用 pi-chrome `chrome_*` 工具**：驱动用户真实 Chrome profile。CNKI 阶段必须先读 `paper-master-4ss/modules/lit/references/pi-chrome-browser.md`（安装、授权、目标模型、失败恢复），再按 `references/cnki-kns8s-closed-loop.md` 执行。关键约束：不传 `targetId`、点击与读取走 `chrome_evaluate`、异步脚本不得 `awaitPromise`、Cookie 走回环 sink `paper-master-4ss/modules/lit/scripts/cnki/cookie_sink.py`。插件从本项目的离线发行仓 <https://github.com/JingYangYuan/pi-chrome-mirror> 安装（`git clone` 后 `omp install .`；自带含 `offscreen` 保活的完整伴生扩展），不使用上游官方安装通道。
- OMP 不自动触发 paper-master guard：执行分析命令后显式运行 `python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace`，交付前显式运行 `stop-check`。如需自动触发，可在 `.omp/hooks/` 用 `tool_result` 事件扩展实现（见 OMP hooks 文档）。
- 长期选择写入 `.omp/AGENTS.md`（OMP 原生项目上下文）的 paper-master 标记块，或工作区 `AGENTS.md`；不要为 OMP 默认创建 `CLAUDE.md`。

## 7. 共同回退规则

- 各宿主都不得因为缺少某项能力而伪造结果；只能记录能力缺失、用户暂缓、网络不可达或顺序复核。
- CNKI、Google Scholar、Zotero MCP、浏览器操纵和网页摘要抓取必须由实际可用工具完成；普通搜索或顾问意见不能替代 CNKI 完成状态。
- 各宿主都必须保持 `paper-workspace/` 输出结构、agent canonical name、质量评分文件和 guard 命令不变。

