# Team Routing Protocol

本文档定义 `paper-master-4ss` 在 Claude Code Agent Teams 中的显式触发、用户确认、focal canonical agent 选择、同一 subagent 多席位化和辩论式 teammate 路由规则。Agent Teams/teammate 是 Claude Code 专属高级并行形态；ZCode 调用本 skill 时按 `references/agent-software-adapters.md` 回退为 Agent 工具并行 subagent 派发，OpenCode/Codex 回退到普通顾问派发或 `sequential-review`。

## 1. 触发边界

只有当用户显式出现以下意图时，才进入 Team 路由：

- `agentteam`
- `teamagent`
- `Agent Team`
- `teammate`
- `团队智能体`
- `升格子智能体`
- 明确要求使用 Claude Code Team/Teams

普通的“全流程规划”“完整检查”“继续推进”“多智能体复核”仍按 `master/agent-orchestration.md` 处理，不自动创建 Agent Team。当前宿主不是 Claude Code 时，即使用户使用了 Team 相关词，也必须说明该高级形态不可用，并回退到普通 orchestration。

Team 与普通 subagent 派发的边界必须保持清楚：普通 orchestration 是多 canonical agent 顾问派发；显式 Agent Team 是同一 canonical agent 的多视角辩论。Team 不得把多个不同 subagent 直接拼成团队，否则退化为普通顾问矩阵。

## 2. 进入 Team 前的必读文件

显式 Team 请求的加载顺序：

1. 项目级 `CLAUDE.md`（位于用户项目文件夹，不在 skill 包内）。
2. `references/runtime-adapter.md` 与 `references/agent-software-adapters.md`。
3. `SKILL.md`。
4. `references/claude-team-config.md`。
5. `references/team-routing.md`。
6. `master/agent-orchestration.md`。
7. `master/output-protocol.md`。
8. `references/agent-registry.md`。

若用户请求已指定某个业务模块，再读取对应 `modules/<module>/SKILL.md` 和候选 focal agent 文件。

## 3. 用户选择门槛

进入 Team 路由后，必须让用户确认以下五项选择。未完成确认前，不得创建 team，不得自行派发 teammate。

| 选择项 | 可选项 | 默认推荐 |
|---|---|---|
| 是否启用 team | 启用 Agent Team（提示成本较高，但效果很好）；不启用，改用普通 subagent/顺序复核 | 由用户确认 |
| Team 规模 | 2 席轻量验证；3-5 席标准辩论；分阶段辩论团队 | 3-5 席标准辩论；analysis 推荐分阶段 |
| 显示模式 | `in-process`；`auto` | 默认 `in-process` |
| Plan approval | 启用；不启用 | 涉及写文件、脚本执行、投稿导出、update 时启用 |
| Teammate 写文件权限 | 不允许写文件；只允许写日志目录；允许写模块正式输出目录 | 只允许写各自独占的 `paper-workspace/_logs/agents/team-[date]/teammate-[canonical-agent]-[perspective].md` |

结构化提问示例见 `references/ask-user-question-examples.md`。Team 选择门槛可按以下 `ask_user` 示例分组确认：

```text
question: "是否启用 Agent Team？Team 会把同一 canonical agent 升格为多席位辩论，提示成本较高但复核更强。"
header: "启用Team"
options: [
  {label: "启用Team", description: "进入 Team 路由，继续确认规模、显示模式、审批和写文件权限"},
  {label: "不启用", description: "回退到普通 subagent 派发或顺序复核"}
]
```

```text
question: "请确认 Team 规模、显示模式、plan approval 和 teammate 写文件权限。"
header: "Team配置"
options: [
  {label: "标准辩论", description: "3-5 席标准辩论，in-process 显示，写操作启用 plan approval，只允许写独占日志文件"},
  {label: "轻量验证", description: "2 席轻量验证，适合快速复核和低成本场景"},
  {label: "分阶段团队", description: "按阶段组织辩论，适合 analysis、submission 或 update 等高风险任务"}
]
```

Team 规模表示同一 subagent 的辩论席位数量，不表示不同 subagent 数量。确认结果必须写入项目级 `CLAUDE.md` 的 paper-master 标记块。后续 Team 执行默认沿用这些选择；只有用户明确改选时才更新。

即使用户允许 teammate 写日志目录，teammate 也只能写自己的独占报告文件；`team-brief.md`、`team-synthesis-[YYYY-MM-DD].md`、索引文件和任何共享文件都必须由 Lead 串行创建或整合，不得让多个 teammate 同时写入。

## 4. 环境不可用时的回退

若当前宿主不是 Claude Code、Agent Teams 未启用、Claude Code 版本不支持、终端模式不可用或用户选择不启用 team：

1. 读取 `references/claude-team-config.md`。
2. 用简短中文说明可选配置方式。
3. 不修改用户的 shell 配置或 `~/.claude.json`。
4. 回退到 `master/agent-orchestration.md` 的普通 subagent/顺序复核。
5. 在 `project_memory` 与过程日志中记录回退原因；Claude Code 可写入项目级 `CLAUDE.md`，ZCode 写入工作区 `AGENTS.md` 标记块，OpenCode/Codex 缺少宿主规则文件时写入 `paper-workspace/_index/project-rules.md`。

## 5. Subagent 升格为 Teammate

本技能不复制 `modules/*/agents/*.md` 到 `.claude/agents/`。升格前必须先按 `references/agent-registry.md` 把用户选择、模块短名或 Team 路由矩阵中的 focal agent 规范化为 canonical agent name。创建 Team 时，所有 teammate 使用同一个 canonical agent name 和同一个 agent 文件作为角色协议，但必须分配不同辩论视角。

标准辩论视角：

| Team 规模 | 必须分配的辩论视角 |
|---|---|
| 2 席 | 主张者、反方审稿人 |
| 3 席 | 主张者、反方审稿人、证据边界审查 |
| 4 席 | 主张者、反方审稿人、方法风险审查、证据边界审查 |
| 5 席 | 主张者、反方审稿人、方法风险审查、证据边界审查、综合裁判 |

若任务不是经验研究，可把“方法风险审查”替换为更贴合该 focal agent 的风险视角，例如结构风险、期刊适配风险、写作声称风险或格式合规风险。替换必须写入 `team-brief.md`。

teammate 的创建说明必须包含：

```markdown
你是 paper-master-4ss 的 teammate，focal canonical agent name 是 `<paper-module-agent-name>`，本席位辩论视角是 `<perspective>`。开始工作前先读取：
- `modules/<module>/agents/<agent-file>.md`
- `master/output-protocol.md`
- 与本任务相关的 `modules/<module>/references/`、`phases/`、`frame/`、`resources/`、`chapters/` 或 `scripts/`

你必须遵守该 agent 文件中的职责、参考库回查协议、审阅重点和输出格式，但只从本席位辩论视角给出判断。
输出必须包含 `## 参考库回查`、`## 本席位判断`、`## 对其他可能立场的反驳或让步`、`## Lead 可采纳结论`。
详细报告写入指定路径，给 Lead 的消息不超过 3 句话，只返回结论摘要和文件路径。
```

作为 teammate 运行时，`model` 和 `tools` 不由 agent frontmatter 决定；实际模型和工具权限由 Claude Code Team 创建时的 Lead 环境决定。

## 6. Focal Agent 路由矩阵

下表只推荐 focal canonical agent 的候选来源，不是 Team 成员清单。每次创建 Team 前，Lead 必须先对照 `references/agent-registry.md` 展开为 canonical agent name，并在 `team-brief.md` 与 `team-synthesis` 记录“用户选择或矩阵短名原文 → focal canonical agent name → agent 文件路径 → 辩论视角分配”。

| 主任务 | 推荐 focal agent | 说明 |
|---|---|---|
| design | `critical-review-consultant`；也可按任务选择 `theory-consultant`、`method-consultant` 或 `journal-fit-consultant` | Team 用于围绕一个设计判断做正反辩论；多 agent 设计复核仍走普通 orchestration |
| lit | `evidence-quality-consultant`；检索策略争议用 `search-strategy-consultant`；假设桥接争议用 `hypothesis-bridge-consultant` | CNKI/Scholar 状态必须按用户选择记录；不同文献角色并行复核仍走普通 orchestration |
| outline | `gap-review-consultant`；结构争议用 `structure-consultant`；证据映射争议用 `evidence-map-consultant` | 材料多、结构选择不明或证据映射复杂时，只围绕一个 focal agent 建立 debate team |
| analysis | 分阶段选择一个 focal agent：变量阶段用 `variable-quality-consultant`；识别阶段用 `identification-model-consultant`；代码阶段用对应 code writer；稳健性阶段用 `robustness-consultant`；报告阶段用 `result-reporting-consultant` | 不一次性升格 13 个 agent；每阶段只围绕一个 focal agent 做辩论 |
| write | `chapter-standard-reviewer`；论证争议用 `argument-consultant`；风格争议用 `style-consultant`；草稿生成争议用 `chapter-draft-writer` | 全文写作按 dispatch-plan 分段；长草稿写文件 |
| submission | `journal-package-consultant`；格式风险用 `format-check-consultant`；引用风险用 `citation-integrity-consultant` | 投稿整备需先检查依赖；不替代 write 大规模重写 |
| update | `review-gate-consultant`；目标路由争议用 `target-routing-consultant`；知识抽取争议用 `knowledge-extraction-consultant` | 所有候选保持 `pending`；不得直接修改核心模块文件 |

跨模块任务不得把多个模块 agent 混成一个 Team。必须先按阶段拆分，再为每个阶段创建一个“单 agent debate team”；若某阶段需要多 canonical agent 协作，先回到 `master/agent-orchestration.md` 的普通顾问派发，再选择其中一个争议点升格为 Team。

## 7. 共享任务与消息规则

- 每个 teammate 同时保持 3-6 个明确任务；单个任务应能在 5-15 分钟内形成一个可审阅产物。
- 同一 Team 内所有 teammate 必须读取同一个 focal agent 文件，并围绕不同辩论视角回应同一任务包。
- 日常沟通使用私信；广播只用于任务范围变更、阻断性风险和最终共识。
- 每条 teammate 消息不超过 3 句话。
- 需要传递详细内容时，写入 `paper-workspace/_logs/agents/team-[YYYY-MM-DD]/` 或用户确认的输出目录，并只发送文件路径。
- Lead 负责综合与采纳，不把 teammate 长报告直接贴回主上下文。

## 8. Plan Approval

以下情况必须建议启用 plan approval：

- teammate 可能写入文件。
- 需要执行分析脚本、转换文档或调用外部 CLI。
- 涉及投稿导出、引用整理或 Word 模板处理。
- 涉及 `update` 模块、候选协议或核心技能文件。

启用 plan approval 后，teammate 先提交计划，Lead 审核通过后才能执行。若用户明确选择不启用，应把该选择写入项目级 `CLAUDE.md`，并在最终回复中标注风险。

## 9. 输出落盘

Team 相关日志默认写入：

```text
paper-workspace/_logs/agents/team-[YYYY-MM-DD]/
├── team-brief.md
├── teammate-[canonical-agent]-[perspective].md
└── team-synthesis-[YYYY-MM-DD].md
```

并发写入规则：

- `team-brief.md` 只能由 Lead 在派发前写入或更新。
- 每个 teammate 只能写自己的 `teammate-[canonical-agent]-[perspective].md`，且 `perspective` 必须在 `team-brief.md` 中预先登记，避免文件名冲突。
- `team-synthesis-[YYYY-MM-DD].md` 只能由 Lead 在收齐各 teammate 独占报告后串行整合生成；不得让 teammate 直接写入或并发追加。
- 若未来需要共享草稿、共享证据表或共享 synthesis，必须先拆成 teammate 独占输入/输出文件，再由 Lead 合并为共享文件。

`team-brief.md` 必须包含：

- 用户确认的 Team 五项选择。
- focal canonical agent name、agent 文件路径、选择理由。
- 辩论视角分配：teammate 名称、视角、任务包、输出路径。
- 与普通 orchestration 的边界说明：本 Team 只围绕一个 canonical agent 辩论。

`team-synthesis` 必须包含：

- 用户确认的 Team 五项选择。
- focal canonical agent name、agent 文件路径、辩论视角分配。
- 每个 teammate 的执行状态、退出状态和必要的运行诊断信息。
- 同一 subagent 各视角的核心共识、核心冲突和不可调和分歧。
- Lead 的采纳决策、未采纳理由和后续风险。
- 回退、阻断或需要用户改选的事项。

所有 Team synthesis 必须遵守 `master/output-protocol.md`，涉及调度链、分歧处理链或回流链时使用 Mermaid。
