# Agent Orchestration（顾问调度规范）

本文件规定顾问（子代理）的选派原则、等待门槛、档位分级、输出归档与跨模块协同方式。执行前须按 `references/runtime-adapter.md` §5 完成运行能力探测，并结合 `master/output-protocol.md`、`references/agent-registry.md` 及目标模块的 `agents/` 文件使用；涉及综述成稿时，同时遵守 `master/literature-review-protocol.md`。

## 1. 基本原则

- **按风险选派**：依据当前步骤的决策风险、材料复杂度、交接跨度与质量风险选派最少必要角色。严禁因研究范式（如实证/理论）或模块名称套用固定名单。派活清单须列明每个拟派角色解决的风险及未派角色的原因。
- **多席位辩论（可选）**：常规模式为单顾问单视角。若运行环境支持同角色多席位互辩（`multi_seat_debate`），须经用户确认方可使用；不支持时退回顺序复核，不单独为此增加能力探测步骤。
- **能力声明与工具映射**：顾问文件 frontmatter 不声明 `tools:` 或 `model:`（见 `references/runtime-adapter.md` §1.5）；可选的 `capabilities:` 仅表示能力意图。实际工具按 `references/runtime-adapter.md` §5 映射至通用动作；缺失能力须记录回退方式，不得虚构结果。
- **使用标准名执行**：用户口语简称或路径简写仅供阅读，执行前必须对照 `references/agent-registry.md` 解析为顾问 frontmatter 中的 `name:`（标准名）。
- **锁定派活清单**：派发前须在 `agent-brief.md` 中完整记录：用户或模块需求、标准名、顾问文件路径、档位（L0/L1/L2）、执行顺序、并行或顺序复核方式。中途增删角色须先更新清单并说明理由。
- **参考库分级回查**：按 T0/T1/T2 分级执行（详见 `references/agent-registry.md` §2）。各模块的必读清单、判据条目与角色附加项统一维护在 `modules/<module>/agents/_reference-base.md`。主流程负责向顾问提供 B1 切片（不超过 1200 字），顾问须在意见开头回填一行 `参考库回查: base=…; tier=…; 判据=…; 缺口=…`。T2 角色须逐条引用条目号与段落行号并填写缺口字段。不得要求每个顾问重复通读全模块参考库。
- **`design` 模块前置条件**：须先确认工作模式（FRAME/STORM/DESIGN/FULL）与研究取向。仅当任务需要使用学科框架库时，提取 3–8 个关键词调用 `frame_locator.py`，其输出仅作为输入线索，不替代研究者决策或顾问选派判断。
- **轻量任务跳过**：满足 L0 条件时可不派发顾问，但须在日志或最终回复中记录 `agent-skip` 及理由。
- **能力缺失降级**：运行环境不支持子代理或并行复核时，由主流程按同一角色清单依次复核，并在 `agent-brief.md`、意见文件与 `agent-synthesis` 中记录 `sequential-review` 及缺失的能力名。
- **输出规范**：顾问意见与综合报告采用中文 Markdown，涉及调度链、机制链、流程链、分歧处理链或退回链时附 Mermaid 图及 2–4 句中文解释；面向用户的最终回复按 `master/output-protocol.md` 第 6 节使用纯文本路径图。

## 1.5 结果等待门槛（`agent-completion-gate`）

派发顾问后，在所有已派发顾问返回有效结果或确认失败前，不得推进后续主流程。

- **禁止并行抢跑**：不得采用「先派发顾问、主流程继续推进、后续再补汇总」的流水线做法。支持同步派发时直接等待返回；仅支持异步派发时，应在结果回投后再恢复推进。不得虚构等待记录。
- **失败与重试**：发生并发限额、空返回、超时或模型无输出时判定为失败，最多重试 1 次。重试仍失败时，允许降级为顺序复核，并在 `agent-synthesis` 中记录 `agent-gate-block: failed×1 + sequential-review` 及失败原因。
- **有效返回判定**：返回值必须包含格式合法的 `参考库回查:` 行及实质判断正文；空返回、纯寒暄或缺失回查行均视为失败并触发重试。
- **终态记录**：派活清单中的执行状态须记录为 `completed(回合数/耗时)`、`failed×N→sequential-review` 或 `failed×N→用户裁决`。
- **能力映射**：具备 `spawn_agent` 能力时使用同步派发或等结果回投；缺失该能力时直接走顺序复核并记录能力缺失，不得标为「已派活」。

## 1.6 派发档位（L0 / L1 / L2）

依据四个维度判定档位：**判断分歧度**（能否机械校验）、**写入不可逆性**、**来源与诚信风险**（结论是否进入正文或投稿包）、**交接跨度**（产物是否传递至下游模块）。

| 档位 | 适用条件 | 派发数量 | 执行方式 |
|---|---|---|---|
| **L0（`agent-skip`）** | 须同时满足：①输出可由脚本或人工直接核验；②无不可逆写入；③不产生需承担学术责任的声称；④不涉及跨模块交接 | 0 | 主流程直接执行，日志记录 `agent-skip: <原因>` |
| **L1（单点复核）** | ①分歧集中于单一维度（理论/方法/结构/文风/引用体例）；②输入文件 ≤3 个且上游产物 ≤1 个；③写入可回滚或无写入 | 1（取该模块风险最高角色） | 派发 1 次，注入 `_reference-base.md` 的 B1 切片；不启用 worktree |
| **L2（串联复核）** | 满足任一项：①跨模块交接；②不可逆写入（正文净稿落盘、代码执行、导出投稿包）；③涉及因果声称或引用对应等诚信风险；④用户明确要求全流程、完整审阅或达到可投稿状态 | 2–4（按模块链路串行） | 按序派发；起草者与复核者须分离；多写手并行写入同一工作目录时须用 worktree 隔离 |

**各模块 L1 默认角色**（同步维护于各模块 `agents/_reference-base.md` 的 B3）：

| 模块 | L1 默认标准名 | 选派依据 |
|---|---|---|
| design | `paper-design-critical-review-consultant` | 持有阶段放行阻断权，优先暴露致命缺陷 |
| lit | `paper-lit-hypothesis-bridge-consultant` | 验证空白到假设的桥接合理性，防止下游整体偏离 |
| outline | `paper-outline-gap-review-consultant` | 缺口结论直接决定是否具备写作条件 |
| analysis | `paper-analysis-identification-consultant` | 识别策略有误时后续稳健性检验无意义 |
| write | `paper-write-draft-review-consultant` | 单次覆盖论证强度、材料嵌入与章节门槛 |
| check | `paper-check-reviewer` | 模块内唯一综合审稿角色 |
| submission | `paper-submission-conformance-consultant` | 统筹核查版式规范与引文一致性 |
| update | `paper-update-review-gate-consultant` | 负责 `pending` 更新包的风险守门 |
| mechanigraph | `paper-mechanigraph-topology-consultant`（单图复刻走 L0） | 拓扑构型错误会导致整张矢量图返工 |

**升档条件**（满足任一项即升档并记录理由）：两角色结论冲突需第三方裁决；发现上游证据缺口须退回；结论将进入正文净稿或投稿包；用户在 L1 之后要求达到可投稿标准。

**降档处理**：L1 顾问返回无效结果时按 §1.5 重试 1 次；仍失败则由主流程按顺序复核补全，记录 `agent-gate-block`，不得伪造已派发记录。

**运行纪律**：
- 不自动启动 `workflow` 编排；L2 属于顺序派发，不等同于 `workflow`。
- 并行写入须开 worktree；若无必要，采用串行起草加 `assemble_drafts.py` 拼接更稳妥。
- 需引入另一模型独立对照时，不新增顾问文件，直接通过 `agy_run` 调用，结论以「外部对照」身份写入 `agent-synthesis`，不占用顾问编号。

## 2. 免派发顾问的例外情形

以下轻量任务可直接由主流程执行（须在日志中记录 `agent-skip` 及原因，免予参考库回查，对应 T0 级）：
- 登记输入路径、查询项目状态、摘要已有产物；
- 单文件格式检查、依赖检查或明确的单步格式转换；
- 单张机制图的快速生成或原图复刻（可由主流程或 `svg-designer` 直接完成；宏大跨层次理论框架图仍须先派 `topology-consultant` 审定构型，再由 `svg-designer` 绘制与自检）；
- 仅回答不进入论文正文的事实性咨询。

上述例外不得用于绕过设计、文献、分析、写作与投稿环节的质量复核。

## 3. 顾问输出归档与注入规范

每次派发顾问均须建立独立归档目录：

```text
paper-workspace/_logs/agents/[module]-[YYYY-MM-DD]/
├── agent-brief.md
├── [agent-name].md
└── agent-synthesis-[module]-[YYYY-MM-DD].md
```

- **`agent-brief.md`**：记录研究主题、输入路径、当前阶段、已知产物、用户约束、待判断问题及完整派活清单。
- **公共块与参考注入**：派发前必须读取 `references/agent-prompt-blocks.md`，将角色卡中的每个 `<!-- block: <ID> -->` 展开为对应正文追加至 prompt 末尾，同时按 `agents/_reference-base.md` B3 注入 B1 切片与附加参考内容。仅传递文件路径或 block ID 视为未注入。
- **`[agent-name].md`**：保存顾问原始输出，须包含：参考库回查行、判断结论、依据、风险与修改建议。
- **按 `task_id` 拆分归档**：`paper-write-chapter-draft-writer` 与 `paper-analysis-code-writer` 支持按 `task_id` 多次派发，须分别归档为 `[agent-name]--{task_id}.md`。`write` 章节草稿须经 `scripts/assemble_drafts.py` 生成合并草稿、source map 与检查结果并由主流程审阅后，方可交由 `paper-write-draft-review-consultant` 与 `paper-write-style-consultant` 复核。
- **`agent-synthesis-[module]-[YYYY-MM-DD].md`** 须包含以下六项：
  1. **派活清单**：用户/模块原需求、标准名、文件路径、档位、执行顺序、并行/顺序复核方式及输入摘要；
  2. **核心共识**：多方一致的判断（若引用同一批底座条目，须注明同源，不得计为多次独立验证）；
  3. **核心分歧**：互相冲突的意见；
  4. **采纳决策**：主流程采纳的结论；
  5. **未采纳理由**：暂不采纳的建议及依据；
  6. **后续风险**：进入下一阶段前仍需处理的问题。

`agent-synthesis` 须使用中文 Markdown；存在派活链、分歧处理链、跨模块风险链或退回链时，须附 Mermaid `flowchart LR` 或 `flowchart TD` 及节点说明。

## 4. 索引同步要求

顾问调度完成后，须同步更新以下索引文件：
- `paper-workspace/_index/project-state.md`：更新派活状态、关键风险、新增产物与下一步建议；
- `paper-workspace/_index/handoff-status.md`：更新供下游阶段使用的已采纳结论与未解决风险；
- `paper-workspace/_index/paper-roadmap.md`：按 `master/user-journey.md` 更新当前阶段、推荐下一步、暂缓事项与退回提示。

## 5. 跨模块协同默认顾问

全流程推进、整理状态或阶段不清时，在主模块之外可按需增派相邻阶段顾问（仅提供风险预判，不替代主模块执行）：

| 当前主流程 | 建议增派的跨模块顾问 |
|---|---|
| 选题 / 研究设计 | `paper-lit-search-strategy-consultant`（评估文献可检索性）；`paper-analysis-identification-consultant`（评估实证方法可行性） |
| 文献综述 | `paper-design-theory-consultant`（校准理论锚点）；`paper-outline-structure-consultant`（预判大纲承接）；成稿阶段按 `master/literature-review-protocol.md` 交 `write` 的 `paper-write-structure-writing-consultant` 与 `paper-write-chapter-draft-writer` |
| 大纲构建 | `paper-write-structure-writing-consultant`（规划写作顺序）；`paper-analysis-reporting-consultant`（明确经验章节所需表图） |
| 数据分析 | `paper-write-draft-review-consultant`（界定结果可声称边界）；`paper-submission-conformance-consultant`（检查引用退回风险） |
| 写作润色 | `paper-check-reviewer`（综合复核，通过后方可进入 `submission`） |
| 全流程审稿 | `paper-check-reviewer`（按完整审稿单派发并等待交回；实质修改精确退回前置模块） |
| 投稿整备 | `paper-write-draft-review-consultant`（复核需退回正文的修改项；经 `check` 通过后再调整排版与投稿包） |
| 学术机制图 | `paper-design-theory-consultant`（复核因果中介逻辑）；`paper-analysis-reporting-consultant`（校准实证变量关系）；`paper-write-style-consultant`（核对插图排版与图题体例） |
