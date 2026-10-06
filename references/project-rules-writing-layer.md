# Project Rules Writing Layer

本文档定义 `paper-master-4ss` 如何通过 `project_memory` 在**用户项目**中创建、插入、更新和读取项目级规则文件。本包不预设文件名：优先使用当前宿主**已有**的项目规则文件（如 Claude Code 兼容层的 `CLAUDE.md`、Antigravity 的 `GEMINI.md`、工作区 `AGENTS.md`、`.omp/AGENTS.md`，或任何宿主会加载的规则文件），套用同一套标记块纪律；只有确认没有宿主规则文件时，才回退到 `paper-workspace/_index/project-rules.md`。任何宿主都不得把项目规则写进 `paper-master-4ss` skill 包目录。

## 1. 落点规则

- 项目规则必须写入用户项目文件夹，不写入 `paper-master-4ss` skill 包目录。
- 先探测当前宿主已有的项目规则文件（见 `references/runtime-adapter.md` §4 与 §5）；**只在已确认属于当前宿主的规则文件里创建或更新标记块**，不要为不存在的宿主凭空新建文件。
- 宿主没有项目规则文件时，写入 `paper-workspace/_index/project-rules.md`。
- Claude Code 兼容层下的默认落点是项目根 `CLAUDE.md`（仅当探测结果为 Claude Code 或用户明确要求兼容 Claude Code 时）。
- 默认项目文件夹是 `paper-workspace/` 所在目录的父目录。
- 若用户显式指定项目根目录，则以用户指定路径为准。
- 若当前工作目录还没有 `paper-workspace/`，先把当前工作目录视为项目根目录；创建 `paper-workspace/` 时保持二者关系一致。
- 不得创建 `/Users/yjy/.skills-manager/skills/paper-master-4ss/CLAUDE.md`、`AGENTS.md` 或任何规则文件在 skill 包目录内。

## 2. 标记块

若目标项目规则文件不存在（且已确认该文件名属于当前宿主），创建新文件。若已存在，不得覆盖全文，只维护以下标记块：

```markdown
<!-- paper-master-4ss:start -->
...本技能维护内容...
<!-- paper-master-4ss:end -->
```

更新时只替换标记块内的内容，保留用户在标记块外的其他规则。

## 3. 读取优先级

每次模块执行前，先读取当前宿主项目规则文件中的 paper-master 标记块，再读取 skill 包内协议文件。宿主没有规则文件时读取 `paper-workspace/_index/project-rules.md`。标记块中的用户选择是项目级约束。

若本次用户明确指令与项目规则冲突：

1. 以本次用户明确指令为准。
2. 将新选择写回 paper-master 标记块（或在无宿主规则文件时写 `_index/project-rules.md`）。
3. 在过程日志或最终回复中说明已更新项目选择。

## 4. 写入时机

以下情况必须更新 `project_memory`：

- 模块通过 `ask_user`、明确对话或用户命令获得稳定选择；结构化提问示例见 `references/user-question-examples.md`。
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

- 技能加载顺序：先按 `references/runtime-adapter.md` §5 探测宿主能力并读取项目级 `project_memory`，再读 `SKILL.md`、`references/install-dependencies.md`、`master/routing-matrix.md`、`master/agent-orchestration.md`、`master/output-protocol.md`、`master/user-journey.md`；`references/agent-software-adapters.md` 只作样例对照；显式 Claude Code Team 请求再读 `references/multiagent-team-config.md` 与 `references/team-routing.md`。
- 输出路径：正式产物统一写入项目内 `paper-workspace/`；用户输入材料只登记路径，不搬运。
- 参考库回查：所有 agent、teammate 和顾问意见必须包含 `## 参考库回查`，列出已读取路径、采用框架、依据条款和参考缺口。
- Team 显式触发：只有用户显式触发 Team，才进入 `references/team-routing.md`；显式触发后仍必须完成用户选择门槛，不得自动派发；当前宿主无 Agent Teams 形态时回退为 `parallel_review` 或 `sequential-review`。
- Teammate 消息限制：每条消息不超过 3 句话；长内容写入文件并发送路径。
- Update pending 规则：`update` 模块只生成 `pending` 候选更新包，不直接修改核心技能文件。
- 分析真实性：没有真实数据、脚本执行结果或可核验证据时，不得伪造变量、统计结果、访谈摘录、显著性、引用字段或投稿状态。
- Guard 审计：分析执行后必须执行 `guard_after_command`；最终停止或交付前必须执行 `guard_before_finish`，检查 `project-state.md` 与 `handoff-status.md` 是否随最新产物更新。宿主可自动触发时用自动触发；否则显式运行 `scripts/paper_master_guard.py post-bash|stop-check`（见 `references/hooks-and-evaluation.md`）。
- Rubric 评分：每次实质性模块执行后运行 `paper_master_guard.py score-project`，把阶段质量分、全流程成熟度、失败归因和下一步修复写入 `_index/quality-score.md` 与 `_index/quality-score.json`。
- Agent 文件策略：不复制 agent 文件到宿主 agent 目录（如 `.claude/agents/`），只通过导向说明引用 `modules/*/agents/*.md`。
- `project_memory` 落点：优先当前宿主已有的项目规则文件的 paper-master 标记块；没有宿主规则文件时写入 `paper-workspace/_index/project-rules.md`；不得写入 skill 文件夹。

## 7. 用户选择记录

按模块记录用户已确认选择。未确认时写 `未确认`，不得替用户猜测并固化。

| 模块 | 必须记录的选择 |
|---|---|
| `design` | 模式选择、学科领域、目标期刊、数据来源、方法偏好 |
| `lit` | 检索模式、是否启用 `web_search`、本地文献库、Zotero、Annual Reviews、引文链、CNKI、Google Scholar |
| `outline` | 论文目的、学历层次、论文类型、目标期刊范式、预期字数、素材处理方式 |
| `analysis` | 分析语言、数据路径、变量角色、模型/识别偏好、质性/混合方法路径、允许执行的 CLI |
| `write` | 研究方法协议、发表范式、写作风格梯度、引言起笔策略、润色/扫描偏好 |
| `submission` | 稿件路径、投稿样式、Word 模板、引用体例、是否生成 cover letter 或 response letter |
| `update` | 更新目的、目标模块、是否 self-update、证据补强要求、风险等级偏好 |
| `mechanigraph` | 拓扑构型流派、外围大边框样式（实线/虚线/无外框）、分箱与连线风格（实线为主/虚实结合）、是否需要无头 Chrome 视觉复核 |
| `teamagent` | 是否启用 Team、Team 规模、显示模式、是否 plan approval、是否允许 teammate 直接写文件 |

## 8. Team 配置状态

显式 Team 请求后，应记录：

- 是否已提示用户启用宿主对应的实验开关（Claude Code 兼容层为 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`）。
- 用户选择的显示模式（Claude Code 兼容层为 `teammateMode`）。
- Agent Teams 是否可用。
- 若回退，回退原因和采用的普通派发方式（`parallel_review` 或 `sequential-review`）。

后续 Team 执行默认沿用项目级显示模式、Plan approval 与 teammate 写文件权限；只有用户明确改选时才更新。

## 9. 更新方式

更新 `project_memory`（当前宿主项目规则文件的 paper-master 标记块，或 `_index/project-rules.md`）时：

1. 定位项目根目录。
2. 读取现有项目规则文件（如存在）。
3. 保留标记块外的用户内容。
4. 合并或替换 paper-master 标记块。
5. 在标记块内记录更新时间、选择来源和冲突处理。

不要把模块日志、agent 原始意见或大段报告塞进项目规则文件。这些内容应写入 `paper-workspace/_logs/`。
