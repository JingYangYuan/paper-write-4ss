# Paper Master 4SS — 子智能体注册表

> 本文件是 paper-master-4ss 所有内部子智能体的权威注册表。首次执行时由总控读取，按模块路由后派发对应顾问。
>
> 总智能体数: **46** | 覆盖子智能体模块: **7** | 更新日期: 2026-07-20

## 强制派发与参考库回查

- 命名规则：`Agent Name` 列是唯一可执行身份，必须等于对应 agent 文件 frontmatter 的 `name:`，也称 canonical agent name。`modules/.../agents/*.md` 是角色协议路径；短名如 `theory-consultant`、`chapter-draft-writer` 只能用于阅读、口语引用和矩阵简写，不得直接作为执行身份。
- 工具列是 Claude Code 兼容能力别名，不是跨宿主硬要求。Claude Code、OpenCode、Codex 与 ZCode 都必须先按 `references/runtime-adapter.md` 和 `references/agent-software-adapters.md` 映射到通用能力；例如 `Read`→`read_file`、`Grep`→`search_text`、`WebSearch`→`web_search`、`WebFetch`→`web_fetch`。
- 别名解析规则：短名必须在明确模块上下文中解析到本注册表对应行；跨模块、阶段不明或同名风险不明时，不得猜测，必须先回到本注册表按模块、阶段和路径选择 canonical agent name。
- 配送一致性门槛：实际派发的 agent 必须与用户选择、模块表格或跨模块矩阵经过规范化后的清单一致。派发清单必须保留“原文选择 → canonical agent name → agent 文件路径”的映射；若执行中需要增删，先记录变更理由再派发。
- 默认采用情境化调度：先说明当前决策风险、选择角色及未选择其他角色的理由，再派发最少必要智能体；不得仅按理论/实证标签、模块名称或固定数量派发。
- 所有智能体在给出判断前必须回到 `paper-master-4ss/modules/<module>/` 对应模块参考库寻找框架；输出必须包含 `## 参考库回查`，列出已读取路径、采用框架、依据条款和参考缺口。
- 所有智能体输出必须遵守 `master/output-protocol.md`：使用中文 Markdown；若涉及机制、流程、派发、回流或风险传播，必须附 Mermaid 图示和 2-4 条中文解释。
- Design 智能体必须接收主流程从选题中提取的 AI 关键词，以及 `paper-master-4ss/modules/design/scripts/frame_locator.py --keywords` 的候选 frame、相关度分数、命中词和 `read_ranges` 行号区间；必须先按行号区间读取候选 `paper-master-4ss/modules/design/frame/theory-frameworks-*.md`，证据不足时才扩展相邻条目。
- 若当前宿主不能真实并行，或缺少 `spawn_agent` / `parallel_review` 能力，按矩阵顺序执行并记录 `sequential-review` 与能力缺失原因；若任务属于轻量例外，必须记录 `agent-skip` 和跳过原因。

---

## 注册表

### Design 模块 (选题与设计) — 9 智能体

| # | Agent Name | 文件路径 | 职责 | 工具 |
|---|-----------|---------|------|------|
| 1 | `paper-design-theory-consultant` | `paper-master-4ss/modules/design/agents/theory-consultant.md` | 理论适配、机制链条、创新空间评估 | Read, Grep |
| 2 | `paper-design-method-consultant` | `paper-master-4ss/modules/design/agents/method-consultant.md` | 可检验性、操作化、识别路径、资料可得性 | Read, Grep |
| 3 | `paper-design-field-consultant` | `paper-master-4ss/modules/design/agents/field-consultant.md` | 学科位置、现实意义、领域贡献评估 | Read, Grep |
| 4 | `paper-design-journal-fit-consultant` | `paper-master-4ss/modules/design/agents/journal-fit-consultant.md` | 目标期刊/论文类型风格适配 | Read, Grep |
| 5 | `paper-design-critical-review-consultant` | `paper-master-4ss/modules/design/agents/critical-review-consultant.md` | 致命缺陷、弱论证、不可执行环节 | Read, Grep |
| 43 | `paper-design-concept-analysis-consultant` | `paper-master-4ss/modules/design/agents/concept-analysis-consultant.md` | 概念定义、边界案例、相邻概念与概念贡献复核 | Read, Grep |
| 44 | `paper-design-normative-argument-consultant` | `paper-master-4ss/modules/design/agents/normative-argument-consultant.md` | 规范前提、原则冲突、反例与制度含义复核 | Read, Grep |
| 45 | `paper-design-interpretive-history-consultant` | `paper-master-4ss/modules/design/agents/interpretive-history-consultant.md` | 文本语境、理论谱系与竞争诠释复核 | Read, Grep |
| 46 | `paper-design-argument-stress-test-consultant` | `paper-master-4ss/modules/design/agents/argument-stress-test-consultant.md` | Toulmin 论证链、限定语和最强反驳压力测试 | Read, Grep |

**触发场景**: 必须先确认 design 模式与研究取向。随后按概念冲突、材料/方法可行性、领域定位、规范原则、文本语境、期刊限制或反驳风险选择角色；任一角色可服务不同研究取向。

---

### Lit 模块 (文献综述) — 5 智能体

| # | Agent Name | 文件路径 | 职责 | 工具 |
|---|-----------|---------|------|------|
| 6 | `paper-lit-search-strategy-consultant` | `paper-master-4ss/modules/lit/agents/search-strategy-consultant.md` | 检索词设计、来源组合、阶段路线、补洞策略 | Read, Grep, WebSearch, WebFetch |
| 7 | `paper-lit-theory-map-consultant` | `paper-master-4ss/modules/lit/agents/theory-map-consultant.md` | 理论谱系梳理、概念关系、争议脉络、知识空白 | Read, Grep |
| 8 | `paper-lit-evidence-quality-consultant` | `paper-master-4ss/modules/lit/agents/evidence-quality-consultant.md` | 证据等级、方法质量、结论稳健性、适用边界 | Read, Grep |
| 9 | `paper-lit-hypothesis-bridge-consultant` | `paper-master-4ss/modules/lit/agents/hypothesis-bridge-consultant.md` | 空白→框架→机制→假设桥接关系检查 | Read, Grep |
| 10 | `paper-lit-screening-consultant` | `paper-master-4ss/modules/lit/agents/screening-consultant.md` | 论文纳入/排除/待核验分类复核 | Read, Grep |

**触发场景**: 文献检索(Phase 1)→文献地图(Phase 2)→假设推导(Phase 3)→论证准备与正文交接(Phase 4，正文按 `master/literature-review-protocol.md` 由 write 生成)。

---

### Outline 模块 (大纲构建) — 5 智能体

| # | Agent Name | 文件路径 | 职责 | 工具 |
|---|-----------|---------|------|------|
| 11 | `paper-outline-structure-consultant` | `paper-master-4ss/modules/outline/agents/structure-consultant.md` | 判断论文结构类型(毕业论文/期刊/实证/阐释/规范/综述) | Read, Grep |
| 12 | `paper-outline-material-classification-consultant` | `paper-master-4ss/modules/outline/agents/material-classification-consultant.md` | 文献/设计/数据/用户材料归类到论文功能位置 | Read, Grep |
| 13 | `paper-outline-chapter-logic-consultant` | `paper-master-4ss/modules/outline/agents/chapter-logic-consultant.md` | 章节顺序、标题层级、论证递进、承接关系 | Read, Grep |
| 14 | `paper-outline-evidence-map-consultant` | `paper-master-4ss/modules/outline/agents/evidence-map-consultant.md` | 材料证据→章节论点映射、支撑充足性检查 | Read, Grep |
| 15 | `paper-outline-gap-review-consultant` | `paper-master-4ss/modules/outline/agents/gap-review-consultant.md` | 章节缺口、材料缺口、论证缺口、写作风险 | Read, Grep |

**触发场景**: 材料扫描(Phase 1)→大纲构建(Phase 2)→质量检查(Phase 3)。

---

### Analysis 模块 (数据分析) — 13 智能体

| # | Agent Name | 文件路径 | 职责 | 工具 |
|---|-----------|---------|------|------|
| 16 | `paper-analysis-variable-inventory-consultant` | `paper-master-4ss/modules/analysis/agents/variable-inventory-consultant.md` | 数据字段、标签、codebook、问卷和既有变量字典查找 | Read, Grep |
| 17 | `paper-analysis-variable-role-mapping-consultant` | `paper-master-4ss/modules/analysis/agents/variable-role-mapping-consultant.md` | 候选变量映射到 Y/X/control/fe/cluster/weight/id/time/mechanism/mediator/moderator/heterogeneity/threshold/nonlinear/instrument/treatment/post/running/cutoff | Read, Grep |
| 18 | `paper-analysis-variable-quality-consultant` | `paper-master-4ss/modules/analysis/agents/variable-quality-consultant.md` | 缺失、类型、异常值、重复、特殊缺失码、面板唯一性和样本口径风险 | Read, Grep |
| 19 | `paper-analysis-variable-cleaning-consultant` | `paper-master-4ss/modules/analysis/agents/variable-cleaning-consultant.md` | 基于 variable-discovery-pack 复核变量清洗、样本筛选、缺失处理、异常值、变量字典 | Read, Grep |
| 20 | `paper-analysis-analysis-plan-consultant` | `paper-master-4ss/modules/analysis/agents/analysis-plan-consultant.md` | 从 design/lit/outline/变量发现包抽取完整变量蓝图与执行任务表 | Read, Grep |
| 21 | `paper-analysis-identification-model-consultant` | `paper-master-4ss/modules/analysis/agents/identification-model-consultant.md` | 模型选择、识别策略、固定效应、标准误、因果推断复核 | Read, Grep |
| 22 | `paper-analysis-main-regression-code-writer` | `paper-master-4ss/modules/analysis/agents/main-regression-code-writer.md` | 描述统计、基准模型、主回归和基础诊断代码草案 | Read, Grep |
| 23 | `paper-analysis-mechanism-extension-code-writer` | `paper-master-4ss/modules/analysis/agents/mechanism-extension-code-writer.md` | 中介、机制、调节、异质性、门槛、非线性、交互和分组检验代码草案 | Read, Grep |
| 24 | `paper-analysis-causal-robustness-code-writer` | `paper-master-4ss/modules/analysis/agents/causal-robustness-code-writer.md` | DiD、IV、RDD、PSM、面板、稳健性和安慰剂检验代码草案 | Read, Grep |
| 25 | `paper-analysis-robustness-consultant` | `paper-master-4ss/modules/analysis/agents/robustness-consultant.md` | 稳健性检验、异质性检验、机制检验、安慰剂检验复核 | Read, Grep |
| 26 | `paper-analysis-qual-mixed-consultant` | `paper-master-4ss/modules/analysis/agents/qual-mixed-consultant.md` | 质性编码、主题分析、内容分析、过程追踪、混合方法 | Read, Grep |
| 27 | `paper-analysis-result-reporting-consultant` | `paper-master-4ss/modules/analysis/agents/result-reporting-consultant.md` | 表格/图形/统计报告/质性摘录/中文结果段落复核 | Read, Grep |
| 28 | `paper-analysis-export-reporting-code-writer` | `paper-master-4ss/modules/analysis/agents/export-reporting-code-writer.md` | 表格、图形、script-index、结果报告和质量门控导出代码草案 | Read, Grep |

**触发场景**: 变量查找三 agent → variable-discovery-pack → variable-cleaning → analysis-plan → identification → main-regression-code + mechanism-extension-code + causal-robustness-code (并行) → robustness + reporting → export-reporting-code → CLI 执行与质量门控。

---

### Write 模块 (论文写作) — 6 智能体

| # | Agent Name | 文件路径 | 职责 | 工具 |
|---|-----------|---------|------|------|
| 29 | `paper-write-structure-writing-consultant` | `agents/structure-writing-consultant.md` | 写作规划、章节/小节拆分、`writing-dispatch-plan`、分段派发顺序 | Read, Grep |
| 30 | `paper-write-argument-consultant` | `agents/argument-consultant.md` | 问题意识、论点、证据、理论对话、贡献表达 | Read, Grep |
| 31 | `paper-write-material-integration-consultant` | `agents/material-integration-consultant.md` | 文献/数据/访谈/案例与正文论证嵌入方式 | Read, Grep |
| 32 | `paper-write-chapter-draft-writer` | `agents/chapter-draft-writer.md` | 按 `writing-dispatch-plan` 的单个任务包撰写章节、分节或段落草稿 | Read, Grep |
| 33 | `paper-write-style-consultant` | `agents/style-consultant.md` | 全文文风总控、术语统一、句式节奏、学理化梯度、扫描器改写循环 | Read, Grep |
| 34 | `paper-write-chapter-standard-reviewer` | `agents/chapter-standard-reviewer.md` | 章节任务、硬性门槛、反模式、交付质量(按ch01-ch10) | Read, Grep |

**触发场景**: structure-writing 生成 `writing-dispatch-plan` → chapter-draft-writer 多段撰写(可并行) → argument + material-integration 复核 → style-consultant 文风总控 → scanner 循环 → chapter-reviewer。

---

### Submission 模块 (投稿整备) — 3 智能体

| # | Agent Name | 文件路径 | 职责 | 工具 |
|---|-----------|---------|------|------|
| 35 | `paper-submission-format-check-consultant` | `paper-master-4ss/modules/submission/agents/format-check-consultant.md` | Word 导出、版式规范、模板适配、标题层级和投稿格式风险 | Read, Grep |
| 36 | `paper-submission-citation-integrity-consultant` | `paper-master-4ss/modules/submission/agents/citation-integrity-consultant.md` | 正文引用、文后参考文献、题录缺口和引用体例一致性 | Read, Grep |
| 37 | `paper-submission-journal-package-consultant` | `paper-master-4ss/modules/submission/agents/journal-package-consultant.md` | 投稿包完整性、声明材料、cover/response letter 和回流项 | Read, Grep |

**触发场景**: 格式检查+引用完整性(并行) → 投稿包复核。

---

### Update 模块 (全包候选更新) — 5 智能体

| # | Agent Name | 文件路径 | 职责 | 工具 |
|---|-----------|---------|------|------|
| 38 | `paper-update-purpose-routing-consultant` | `paper-master-4ss/modules/update/agents/purpose-routing-consultant.md` | 区分学科知识、写作范式、方法协议、流程协议、工具模板、self-update 或 mixed | Read, Grep |
| 39 | `paper-update-knowledge-extraction-consultant` | `paper-master-4ss/modules/update/agents/knowledge-extraction-consultant.md` | 从材料中抽取理论、写作范式、方法协议、流程协议和工具模板候选项 | Read, Grep |
| 40 | `paper-update-literature-enrichment-consultant` | `paper-master-4ss/modules/update/agents/literature-enrichment-consultant.md` | 为学科知识、方法协议和文献策略类候选补充证据、争议状态和适用边界 | Read, Grep, WebSearch, WebFetch |
| 41 | `paper-update-target-routing-consultant` | `paper-master-4ss/modules/update/agents/target-routing-consultant.md` | 读取 target registry 和模块 targets 文件，路由到目标模块、目标面、目标文件和建议位置 | Read, Grep |
| 42 | `paper-update-review-gate-consultant` | `paper-master-4ss/modules/update/agents/review-gate-consultant.md` | 复核来源、证据、风险等级、self-update、验证方式、跨模块影响和 pending 状态 | Read, Grep |

**触发场景**: 目的路由→候选抽取→文献补强(按需)→统一目标面路由→兼容性与风险门控→审核包。

---

## 跨模块并行触发矩阵

| 论文阶段 | 可并行派发的智能体组合 |
|---------|---------------------|
| **选题/研究设计** | 先完成 design 模式与取向确认；按概念、材料/方法、领域、规范、阐释、期刊或反驳风险选择必要角色，不设固定组合 |
| **文献综述** | search-strategy + theory-map (并行) → evidence-quality + screening (并行) → hypothesis-bridge → 交接 write 流程成稿（按 `master/literature-review-protocol.md`，正文落 `05-writing/literature-review.md`） |
| **大纲构建** | structure + material-classification (并行) → chapter-logic + evidence-map (并行) → gap-review |
| **数据分析** | variable-inventory + variable-role-mapping + variable-quality (并行) → variable-discovery-pack → variable-cleaning → analysis-plan → identification-model → main-regression-code + mechanism-extension-code + causal-robustness-code (并行) → robustness + result-reporting → export-reporting-code → CLI执行与质量门控 |
| **论文写作** | structure-writing(规划/dispatch-plan) → chapter-draft-writer(多段可并行) → argument + material-integration(复核) → style-consultant(文风总控) → scanner循环 → chapter-reviewer |
| **投稿整备** | format-check + citation-integrity (并行) → journal-package |
| **知识更新** | purpose-routing → knowledge-extraction + literature-enrichment(按需) → target-routing → review-gate；self-update 必须 target-routing + review-gate 双重审核 |

---

## 路径前缀

所有路径相对于 skill 根目录:

```
/Users/yjy/.skills-manager/skills/paper-master-4ss/
```

Agent 文件均为独立 Markdown 文件，包含 frontmatter (name/description/model/tools) + 职责说明 + 参考库回查协议 + 审阅重点 + 输出格式。

---

*注册表维护者: paper-master-4ss 总控 | 自动生成于 2026-06-12*
