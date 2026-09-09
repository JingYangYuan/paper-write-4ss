# CLAUDE.md Writing Layer

本文档定义 `paper-master-4ss` 在 Claude Code 中如何创建、插入、更新和读取项目级 `CLAUDE.md`。`CLAUDE.md` 是 `project_memory` 的 Claude Code 落点；ZCode 的落点是工作区 `AGENTS.md` 标记块，套用同一套标记块纪律（下文所有 `CLAUDE.md` 规则对 ZCode 的 `AGENTS.md` 同样适用）；OpenCode 与 Codex 的项目记忆回退见 `references/runtime-adapter.md` 与 `references/agent-software-adapters.md`。

## 1. 落点规则

- `CLAUDE.md` 必须写入用户项目文件夹，不写入 `paper-master-4ss` skill 包目录。
- 仅当前宿主是 Claude Code，或用户明确要求兼容 Claude Code 时，才默认创建或更新 `CLAUDE.md`。
- ZCode 的项目记忆落点是工作区 `AGENTS.md` 的 paper-master 标记块（ZCode 原生向上搜索并加载 `AGENTS.md`）；仅当前宿主是 ZCode 时才创建或更新，标记块外内容同样不得覆盖。
- OpenCode/Codex 缺少宿主项目规则文件时，写入 `paper-workspace/_index/project-rules.md`，不得默认创建 `CLAUDE.md`。
- 默认项目文件夹是 `paper-workspace/` 所在目录的父目录。
- 若用户显式指定项目根目录，则以用户指定路径为准。
- 若当前工作目录还没有 `paper-workspace/`，先把当前工作目录视为项目根目录；创建 `paper-workspace/` 时保持二者关系一致。
- 不得创建 `/Users/yjy/.skills-manager/skills/paper-master-4ss/CLAUDE.md`，也不得在 skill 包目录创建 `AGENTS.md`。

## 2. 标记块

若项目级 `CLAUDE.md` 不存在，创建新文件。若已存在，不得覆盖全文，只维护以下标记块：

```markdown
<!-- paper-master-4ss:start -->
...本技能维护内容...
<!-- paper-master-4ss:end -->
```

更新时只替换标记块内的内容，保留用户在标记块外的其他规则。

## 3. 读取优先级

Claude Code 每次模块执行前，先读取项目级 `CLAUDE.md` 中的 paper-master 标记块，再读取 skill 包内协议文件。ZCode 先读取工作区 `AGENTS.md` 的 paper-master 标记块（用户级 `~/.zcode/AGENTS.md` 只作背景默认，不写入）。OpenCode/Codex 先读取宿主项目规则文件或 `_index/project-rules.md`。标记块中的用户选择是项目级约束。

若本次用户明确指令与项目级 `CLAUDE.md` 冲突：

1. 以本次用户明确指令为准。
2. 将新选择写回 paper-master 标记块。
3. 在过程日志或最终回复中说明已更新项目选择。

## 4. 写入时机

以下情况必须更新项目级 `CLAUDE.md`：

- 模块通过 `ask_user`、明确对话或用户命令获得稳定选择；结构化提问示例见 `references/ask-user-question-examples.md`。
- 用户改变既有选择。
- 用户显式触发 Team 并完成 Team 五项选择。
- Agent Teams 不可用并回退到普通 subagent/顺序复核。
- 用户指定新的项目根目录、输出路径或模块策略。

以下内容不得写入：

- 临时任务说明。
- 研究主题的详细隐私材料。
- 原始数据、访谈原文、身份映射表、敏感路径明细。
- 频繁变化的阶段状态、待办细节或日志全文。
- 用户 shell 配置文件全文、token、cookie 或认证信息。

## 5. 标记块结构

paper-master 标记块应使用以下结构：

```markdown
<!-- paper-master-4ss:start -->
## Paper Master 4SS Project Rules

### 固定死规则
- ...

### 用户选择记录
| 模块 | 选择项 | 当前值 | 来源/更新时间 |
|---|---|---|---|

### Team 配置状态
| 选择项 | 当前值 | 来源/更新时间 |
|---|---|---|

### 更新说明
- 最近一次更新:
- 若本次用户指令与旧选择冲突:
<!-- paper-master-4ss:end -->
```

## 6. 固定死规则

标记块中必须保留以下死规则：

- 技能加载顺序：先读 `references/runtime-adapter.md`、`references/agent-software-adapters.md` 和项目级 `project_memory`，再读 `SKILL.md`、`references/install-dependencies.md`、`master/routing-matrix.md`、`master/agent-orchestration.md`、`master/output-protocol.md`、`master/user-journey.md`；显式 Claude Code Team 请求再读 `references/claude-team-config.md` 与 `references/team-routing.md`。
- 输出路径：正式产物统一写入项目内 `paper-workspace/`；用户输入材料只登记路径，不搬运。
- 参考库回查：所有 agent、teammate 和顾问意见必须包含 `## 参考库回查`，列出已读取路径、采用框架、依据条款和参考缺口。
- Team 显式触发：只有用户显式触发 Team，才进入 `references/team-routing.md`；显式触发后仍必须完成用户选择门槛，不得自动派发。
- Teammate 消息限制：每条消息不超过 3 句话；长内容写入文件并发送路径。
- Update pending 规则：`update` 模块只生成 `pending` 候选更新包，不直接修改核心技能文件。
- 分析真实性：没有真实数据、脚本执行结果或可核验证据时，不得伪造变量、统计结果、访谈摘录、显著性、引用字段或投稿状态。
- Guard 审计：分析执行后的命令必须接受 `guard_after_command` 审计；最终停止或交付前必须让 `guard_before_finish` 检查 `project-state.md` 与 `handoff-status.md` 是否随最新产物更新。Claude Code 可由 Hook 自动触发；ZCode 注册 `register_zcode_hooks.py` 后自动触发；OpenCode/Codex 显式运行 guard 命令。
- Rubric 评分：每次实质性模块执行后运行 `paper_master_guard.py score-project`，把阶段质量分、全流程成熟度、失败归因和下一步修复写入 `_index/quality-score.md` 与 `_index/quality-score.json`。
- Agent 文件策略：不复制 `.claude/agents`，只通过导向说明引用 `modules/*/agents/*.md`。
- `project_memory` 落点：Claude Code 写入用户项目文件夹的 `CLAUDE.md`；ZCode 写入工作区 `AGENTS.md` 标记块；OpenCode/Codex 缺少宿主规则文件时写入 `paper-workspace/_index/project-rules.md`；不得写入 skill 文件夹。

## 7. 用户选择记录

按模块记录用户已确认选择。未确认时写 `未确认`，不得替用户猜测并固化。

| 模块 | 必须记录的选择 |
|---|---|
| `design` | 模式选择、学科领域、目标期刊、数据来源、方法偏好 |
| `lit` | 检索模式、是否启用 WebSearch、本地文献库、Zotero、Annual Reviews、引文链、CNKI、Google Scholar |
| `outline` | 论文目的、学历层次、论文类型、目标期刊范式、预期字数、素材处理方式 |
| `analysis` | 分析语言、数据路径、变量角色、模型/识别偏好、质性/混合方法路径、允许执行的 CLI |
| `write` | 研究方法协议、发表范式、写作风格梯度、引言起笔策略、润色/扫描偏好 |
| `submission` | 稿件路径、投稿样式、Word 模板、引用体例、是否生成 cover letter 或 response letter |
| `update` | 更新目的、目标模块、是否 self-update、证据补强要求、风险等级偏好 |
| `teamagent` | 是否启用 Team、Team 规模、显示模式、是否 plan approval、是否允许 teammate 直接写文件 |

## 8. Team 配置状态

显式 Team 请求后，应记录：

- 是否已提示用户启用 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`。
- 用户选择的 `teammateMode`。
- Agent Teams 是否可用。
- 若回退，回退原因和采用的普通派发方式。

后续 Team 执行默认沿用项目级 `teammateMode`、Plan approval 与 teammate 写文件权限；只有用户明确改选时才更新。

## 9. 更新方式

更新项目级 `CLAUDE.md`（ZCode 下为工作区 `AGENTS.md` 标记块）时：

1. 定位项目根目录。
2. 读取现有 `CLAUDE.md` / `AGENTS.md`（如存在）。
3. 保留标记块外的用户内容。
4. 合并或替换 paper-master 标记块。
5. 在标记块内记录更新时间、选择来源和冲突处理。

不要把模块日志、agent 原始意见或大段报告塞进 `CLAUDE.md` 或 `AGENTS.md`。这些内容应写入 `paper-workspace/_logs/`。
