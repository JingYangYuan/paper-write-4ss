# Agent Orchestration Protocol

本协议定义 `paper-master-4ss` 的默认顾问派发方式。总控和各模块先按 `references/runtime-adapter.md` 与 `references/agent-software-adapters.md` 确认当前宿主能力，再按本文件确定派发强度，随后读取 `master/output-protocol.md`、`references/agent-registry.md` 和目标模块的 `agents/` 文件；涉及文献综述成稿时，还必须读取 `master/literature-review-protocol.md`。

## 1. 默认策略

- 默认采用情境化调度：先识别当前决策、材料、交接和质量风险，再选择最少必要顾问；不得只因理论/实证标签、模块名称或“实质性任务”自动派发固定数量。
- 全流程、主题模糊、材料复杂、跨模块串联或质量风险高时，可增加独立复核；派发清单必须说明每个角色解决的风险及未派发其他角色的理由。
- 普通 orchestration 是多 canonical agent 顾问派发；显式 Agent Team 是同一 canonical agent 的多视角辩论，二者不可互相替代。
- Agent 文件 frontmatter 中的 `tools:` 只表示 Claude Code 兼容能力别名。Claude Code、OpenCode、Codex、ZCode 与 OMP 都必须经 runtime adapter 映射到 `read_file`、`search_text`、`web_search`、`web_fetch`、`browser_control`、`spawn_agent` 等通用能力；缺少能力时按本协议记录回退，不得伪造工具结果。
- 派发前必须先规范化 agent 身份：凡用户选择、模块表格、路由矩阵或过程计划中出现短名、路径名或角色描述，都先对照 `references/agent-registry.md` 转成 agent 文件 frontmatter 的 `name:`，即 canonical agent name。`Agent Name` 是唯一执行身份；短名和 `modules/.../agents/*.md` 路径只作别名、阅读入口和角色协议路径。
- 规范化后的派发清单必须同时写出：用户选择或模块选择原文、canonical agent name、agent 文件路径、派发顺序、并行或 `sequential-review` 状态。实际派发不得偏离该清单；如需增删顾问，必须先更新清单并说明理由。
- 每个顾问必须先执行参考库回查：读取 `paper-master-4ss/modules/<module>/` 下本模块明确对应的 `references/`、`frame/`、`resources/`、`chapters/`、`scripts/` 或相关 phase 文件，并在顾问意见中列出已读取路径、采用框架、依据条款和参考缺口。
- Design 模块必须先确认 FRAME/STORM/DESIGN/FULL 模式和研究取向；只有任务确实需要学科框架库时，才从选题提取 3-8 个关键词并调用 `frame_locator.py`。脚本结果进入需要该证据的顾问输入包，不能替代用户选择或触发固定顾问名单。
- 轻量任务可以跳过顾问，但必须在最终回复或过程日志写明 `agent-skip` 和跳过原因。
- 若当前宿主不能真实并行或没有 `spawn_agent` / `parallel_review` 能力，按同一顾问列表顺序复核，并在 `agent-brief.md`、对应顾问输出和 `agent-synthesis` 记录 `sequential-review` 与能力缺失原因。
- 所有顾问输出、综合文件和最终回复遵守 `master/output-protocol.md`：使用中文 Markdown；顾问输出、综合文件和落盘报告若涉及派发链、机制链、流程链、分歧处理链或跨模块风险链，必须加入 Mermaid 图示和 2-4 条中文解释；直接发给用户的最终回复按 `master/output-protocol.md` 第 6 节使用纯文字路径导航。

## 1.5 派发完成硬门槛（agent-completion-gate，2026-09-05 实测修订）

- **同步阻塞铁律**：凡被派发的 canonical agent，主流程必须等待其到达终态（completed / failed-with-exhausted-retries）后才允许进入下一步。禁止"派发后台 agent + 先行推进其他阶段 + 事后补综合"的流水线写法——后台并行仅是执行方式，不是跳过等待的理由。
- **失败重试**：agent 派发失败（并发限额、模型无输出、超时）时，必须按顺序重试至多 2 次（重试间隔中不得推进主模块任务）；两次重试仍失败，才允许降级为 `sequential-review`（主流程按角色顺序复核），且必须在 agent-synthesis 中记录 `agent-gate-block: failed×2 + sequential-review` 与失败原因。
- **终态核验**：收到的 agent 返回值必须包含参考库回查与实质判断正文；空返回、纯寒暄、无参考回查的返回一律按 failed 处理并触发重试。
- **记录格式**：派发清单中的"执行状态"列改为终态记录：`completed(回合数/耗时)` / `failed×N→sequential-review` / `failed×N→用户裁决`。
- **宿主映射**：有 `spawn_agent` 能力的宿主用同步派发（等待返回值）实现本门槛；无 spawn_agent 宿主直接按 sequential-review 执行并记录能力缺失，不得伪造"已派发"。

## 2. 轻量任务例外

以下任务可不派发顾问：

- 仅登记输入路径、查看项目状态或摘要已有产物。
- 单文件格式检查、依赖检查或明确的转换命令。
- 用户明确要求只回答一个事实性问题，且不进入论文流程。

例外不得用于跳过设计、文献、分析、写作或投稿的质量复核；不得用于跳过 agent 的参考库回查。

## 3. 输出落盘

每次派发顾问时创建：

```text
paper-workspace/_logs/agents/[module]-[YYYY-MM-DD]/
├── agent-brief.md
├── [agent-name].md
└── agent-synthesis-[module]-[YYYY-MM-DD].md
```

`agent-brief.md` 记录研究主题、输入路径、当前阶段、已知产物、用户约束、需要顾问判断的问题，并附规范化派发清单：用户选择或模块选择原文、canonical agent name、agent 文件路径、派发顺序、并行或 `sequential-review` 状态。

每个 `[agent-name].md` 保存该顾问的原始意见，沿用顾问文件中的“参考库回查/判断/依据/风险/建议”结构。

Write 模块的 `paper-write-chapter-draft-writer` 是特殊的可重复派发 canonical writer：同一 canonical agent 可按 `writing-dispatch-plan` 的多个 `task_id` 并行或顺序执行，但每个任务必须独立落盘为 `paper-write-chapter-draft-writer--{task_id}.md`。这些 writer 输出必须经 `scripts/assemble_drafts.py` 拼接，生成 draft、source map 和 assembly check，并由主 agent 阅读审查后，才可进入 argument、material、style 和 chapter-reviewer 顾问链。

`agent-synthesis` 必须包含：

- 派发清单：用户选择或模块选择原文、canonical agent name、agent 文件路径、派发顺序、并行或 `sequential-review` 状态、输入摘要。
- 核心共识：哪些判断一致。
- 核心分歧：哪些判断冲突。
- 采纳决策：主流程采纳了什么。
- 未采纳理由：哪些建议暂不采纳及原因。
- 后续风险：进入下一阶段前仍需处理的问题。

`agent-synthesis` 必须使用中文 Markdown；若存在派发链、分歧处理链、跨模块风险链或回流链，必须加入 Mermaid `flowchart LR` 或 `flowchart TD` 图示，并在图后解释关键节点、采纳路径和剩余风险。

## 4. 索引更新

模块结束后，总控或模块主流程必须把以下内容写入：

- `paper-workspace/_index/project-state.md`：本次顾问派发状态、关键风险、已生成产物、下一步建议。
- `paper-workspace/_index/handoff-status.md`：进入下阶段时应交接的顾问结论和未解决风险。
- `paper-workspace/_index/paper-roadmap.md`：按 `master/user-journey.md` 更新当前位置、推荐下一步、暂不建议事项和回流提醒。

## 5. 跨模块默认链路

当用户请求全流程、继续推进、整理项目或当前阶段不清时，先确定主模块，再按相邻阶段追加顾问：

| 当前主任务 | 默认追加顾问 |
|---|---|
| 选题/设计 | lit 的 `search-strategy` 预判文献可检索性；analysis 的 `identification-model` 预判方法可行性 |
| 文献综述 | design 的 `theory-consultant` 校准理论锚点；outline 的 `structure-consultant` 预判结构承接；正文成稿按 `master/literature-review-protocol.md` 交接 write 的 `structure-writing` 与 `chapter-draft-writer` |
| 大纲构建 | write 的 `structure-writing` 预判写作顺序；analysis 的 `result-reporting` 预判经验章节需求 |
| 数据分析 | write 的 `argument-consultant` 预判结果声称边界；submission 的 `citation-integrity` 预判引用回流 |
| 写作润色 | check 的 editorial-screening、argument-integrity、ethics-conformance 做综合复核；通过质量门后才交 submission |
| 全流程审稿 | check 的 editorial-screening + argument-integrity + ethics-conformance（完整审稿并行，必须等待终态）；实质修改精确回流 write 或前序模块 |
| 投稿整备 | write 的 `chapter-standard-reviewer` 复核需回流正文的问题；check 已通过后再处理格式与投稿包 |

跨模块顾问只做预判和风险提示，不替代主模块执行。
