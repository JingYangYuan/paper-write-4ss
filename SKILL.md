---
name: paper-write-4ss
description: "中文社会科学论文写作系统。先通过 research_router.md 完成研究方法协议与发表范式双层路由，再按章节标准和范文提示词完成写作、润色和检查。支持规范研究、实证研究、阐释研究、混合研究四类方法协议，以及社会学研究范式和管理世界案例研究范式两类发表风格。配备 writing_scanner.py 与 complexity_analyzer.py，用于语言反模式扫描和文本复杂度诊断。"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Agent
argument-hint: "[文本路径] 后加 [路由/润色/扫描/检查/改写/复杂度]"
---

> **拆分版路径约定**：本包由 `paper-master-4ss/scripts/export_standalone.py` 从 `paper-master-4ss/modules/write/` 自动导出，是可独立安装的运行版。包内相对路径（`agents/`、`phases/`、`references/`、`master/` 等）相对本包根目录解析；跨模块路径 `paper-master-4ss/modules/<x>/...` 相对同级安装的 `paper-master-4ss/` 总控包解析。请勿直接编辑本包：修改总控模块后重新导出。

# write module-exp：中文社会科学论文写作系统

本系统面向中文社会科学论文写作。它的基本目标是把论文写作拆成可判断、可路由、可调用、可检查的流程。

使用本 Skill 时，不应直接进入正文生成。必须先完成研究路由，再调用撰写子 agent 生成章节草稿，随后进行整体风格调整，最后运行扫描器和复杂度诊断。

## 路径约定

- 本文件中的 `modules/...` 路径默认相对于 `paper-master-4ss/` 根目录解析；若从本模块目录直接运行，也可将同模块路径改用 `agents/...`、`chapters/...`、`examples/...`、`resources/...`、`scripts/...`。

## 全局输出协议

先读取并遵守 `master/output-protocol.md`。本模块所有写作规划、分段派发表、草稿说明、扫描报告摘要、顾问意见、综合文件和最终回复默认使用中文 Markdown；章节名、文献题名、变量名、命令和文件路径可保留原文。`writing-dispatch-plan`、多段写作 agent 派发、文风总控、scanner 循环修复、章节回流和 agent synthesis 链路必须使用 Mermaid 图示，并在图后附 2-4 条中文解释。

正文净稿执行单独格式协议：`paper-workspace/05-writing/literature-review.md`、`paper-workspace/05-writing/manuscript*.md` 与 `paper-workspace/05-writing/revisions/styled*.md` 的正文区只允许 `#`、`##`、`###`、`####` 标题层级和自然段。正文净稿不得包含 `**加粗**`、任务包、使用材料清单、未使用材料、待补证据、不可声称内容、Markdown 表格、引用块、代码块、HTML 注释、Mermaid 图示、任务清单或项目符号清单。内部 draft、source map、顾问意见和扫描报告继续按过程报告 Markdown 输出。

## 路径初始化（每次启动必须执行）

本 Skill 的 Python 脚本与当前 SKILL.md 位于同一 skill 包内，目录关系为：

```
<write模块根>/
├── SKILL.md          ← 本文件
├── scripts/          ← Python 脚本
├── chapters/
├── examples/
├── resources/
└── agents/
```

执行任何 `python3` 命令前，先 `cd` 到本 SKILL.md 所在目录：

```bash
cd "$(dirname "/path/to/SKILL.md")"
```

其中 `/path/to/...` 替换为本 SKILL.md 的实际路径（Skill 加载时系统已知该路径，直接使用即可，不要硬编码）。

验证脚本存在：
```bash
ls scripts/writing_scanner.py scripts/complexity_analyzer.py scripts/example_extractor.py scripts/method_router.py scripts/assemble_drafts.py
```

后续所有命令以 `scripts/` 相对路径调用，例如：
```bash
python3 scripts/writing_scanner.py --scan paper.md
```

若当前目录是 write 模块目录，所有 `paper-workspace` 输出必须使用项目工作区的绝对路径，例如 `/abs/project/paper-workspace/05-writing/...`。不得把 `paper-workspace/` 误写到 skill 包内部。

---

## 零、多智能体并行触发

默认按 `master/agent-orchestration.md` 积极派发本模块顾问。遇到全文草拟、章节重写、多约束润色、引言/文献综述/方法/发现/结论段落撰写或章节质量复核时，必须并行派发本模块顾问。派发前先读取对应 agent 定义，并把研究路由、大纲、段落级写作蓝图、已有正文、证据映射、章节标准和目标风格作为输入包。实际派发以 `references/agent-registry.md` 中的 canonical agent name 为准；下表路径只作为角色协议路径。

| 触发场景 | 可派发 agent |
|---|---|
| 写作规划、章节/小节拆分、分段派发表 | `agents/structure-writing-consultant.md` |
| 章节、分节或段落正文草稿撰写 | `agents/chapter-draft-writer.md` |
| 问题意识、论点、证据和理论对话 | `agents/argument-consultant.md` |
| 文献、数据、访谈、案例和正文嵌入 | `agents/material-integration-consultant.md` |
| 全文文风总控、术语统一、扫描器改写循环 | `agents/style-consultant.md` |
| ch01-ch10 章节标准复核 | `agents/chapter-standard-reviewer.md` |

主流程只负责派发 agent、用脚本合并草稿、落盘、阅读审查合并稿、运行扫描器和记录综合决策；不直接承担正文初稿或最终风格重写。所有 agent 输出写入项目工作区的 `paper-workspace/_logs/agents/write-[YYYY-MM-DD]/`，并生成 `agent-synthesis-write-[YYYY-MM-DD].md`。若当前环境不能真实并行，则按同一角色顺序处理，并记录 `sequential-review`。

### 写作顾问触发点

- 研究路由完成后，必须派发 `paper-write-structure-writing-consultant` 作为写作规划子 agent，输出 `writing-dispatch-plan`；`structure-writing-consultant` 只作短名别名。
- `writing-dispatch-plan` 必须优先由 `paper-workspace/03-outline/paragraph-blueprint-[slug]-[YYYY-MM-DD].md` 派生，包含章节/小节拆分、段落编号、段落大意、每段写作任务、输入材料、对应章节标准、范文片段、证据映射、上下文边界、禁止声称内容和派发顺序；不得在已有段落蓝图充分时自行重拆结构。
- 正文生成阶段必须按 `writing-dispatch-plan` 多段派发 `paper-write-chapter-draft-writer`。短文本至少形成一个任务包；全文初稿按章节、小节或段落多次派发，同一 agent 文件可并行复用；`chapter-draft-writer` 只作短名别名。
- 每个 draft writer 输出必须包含正文草稿、使用材料清单、未使用材料、待补证据和不可声称内容，并独立保存为 `paper-workspace/_logs/agents/write-[YYYY-MM-DD]/paper-write-chapter-draft-writer--{task_id}.md`。其中 `## 正文草稿` 只能写可合并的论文正文，不得夹带任务包、清单、表格或说明文字；元信息只能放在 `## 使用材料清单` 等后续区块。禁止多个任务覆盖同一个 writer 文件。
- 正文草稿、正文净稿和风格统一稿不得出现项目过程版本标签或英文命题编号，如“第三版”“第二版”“v3”“v2”“压缩版”“本轮”“本次任务”“P1”“P2”“P3”等；这些标签只能用于计划、日志、文件名、扫描报告和索引。若输入材料含此类标签，写入论文正文时必须改写为“本文”“本研究”“这一框架”“上述命题”“命题一/二/三”等论文内生表述。
- 多个 draft writer 完成后，主流程必须先运行 `scripts/assemble_drafts.py` 合并草稿，输出内部草稿 `paper-workspace/05-writing/drafts/draft-[slug]-[YYYY-MM-DD].md`、正文净稿 `paper-workspace/05-writing/manuscript-[slug]-[YYYY-MM-DD].md`、`paper-workspace/05-writing/assembly/source-map-[slug]-[YYYY-MM-DD].md` 和 `paper-workspace/05-writing/assembly/assembly-check-[slug]-[YYYY-MM-DD].json`。拼接脚本失败或正文净稿格式检查失败时不得进入后续顾问复核。
- 拼接完成后，主 agent 必须阅读全文和 source map，写入 `paper-workspace/05-writing/reviews/main-agent-review-[slug]-[YYYY-MM-DD].md`。该审查须判断章节顺序、任务覆盖、段落来源、材料越界、缺失任务和不可声称内容，并明确“通过”或“阻断项”。
- 主 agent 审查通过或已记录阻断项后，才可并行派发 `paper-write-argument-consultant` 与 `paper-write-material-integration-consultant`，复核问题意识、证据嵌入和理论对话；短名不得直接作为执行身份。
- 主流程只用脚本合并各段草稿并保留段落来源，不直接重写正文。
- 交付前，必须派发 `paper-write-style-consultant` 作为全文文风总控，统一术语、句式节奏、学理化梯度、章节衔接和扫描器改写指令，保存为正文净稿 `paper-workspace/05-writing/revisions/styled-[slug]-[YYYY-MM-DD].md`，再运行扫描器；`style-consultant` 只作短名别名。
- 轻量扫描或单句润色若跳过顾问，必须记录 `agent-skip`。

### Subagent 规划-多段撰写-文风总控流水线

该流水线的规划文件、agent synthesis 和最终交付说明必须遵守 `master/output-protocol.md`，并用 Mermaid 表达“规划 agent → 多段 draft writer → assemble_drafts 拼接 → 主 agent 阅读审查 → 论证/材料复核 → 文风总控 → scanner 循环 → 章节复核”的链路。

正文撰写任务必须按以下顺序执行：

1. 读取 `resources/research_router.md`，完成研究方法、发表范式和风格路由。
2. 运行 `example_extractor.py` 截取相关范文，读取对应 `chapters/ch*.md` 标准。
3. 优先读取 `paper-workspace/03-outline/paragraph-blueprint-[slug]-[YYYY-MM-DD].md`；若不存在，必须在 `writing-dispatch-plan` 中记录缺失并降低拆分置信度。派发 `paper-write-structure-writing-consultant` 生成 `writing-dispatch-plan`，并落盘到项目工作区的 `paper-workspace/05-writing/plans/writing-dispatch-plan-[slug]-[YYYY-MM-DD].md`。
4. 按 `writing-dispatch-plan` 多段派发 `paper-write-chapter-draft-writer`。每个 writer 只接收一个章节、小节或段落任务包；长文按章节/小节多次派发，同一 canonical agent 可并行复用，但每个任务必须独立落盘为 `paper-workspace/_logs/agents/write-[YYYY-MM-DD]/paper-write-chapter-draft-writer--{task_id}.md`。
5. 运行拼接脚本。所有路径使用项目工作区绝对路径：
   ```bash
   python3 scripts/assemble_drafts.py \
     --plan /abs/project/paper-workspace/05-writing/plans/writing-dispatch-plan-[slug]-[YYYY-MM-DD].md \
     --draft-dir /abs/project/paper-workspace/_logs/agents/write-[YYYY-MM-DD] \
     --out /abs/project/paper-workspace/05-writing/drafts/draft-[slug]-[YYYY-MM-DD].md \
     --manuscript /abs/project/paper-workspace/05-writing/manuscript-[slug]-[YYYY-MM-DD].md \
     --source-map /abs/project/paper-workspace/05-writing/assembly/source-map-[slug]-[YYYY-MM-DD].md \
     --json /abs/project/paper-workspace/05-writing/assembly/assembly-check-[slug]-[YYYY-MM-DD].json
   ```
6. 主 agent 阅读 `draft-[slug]-[YYYY-MM-DD].md`、`manuscript-[slug]-[YYYY-MM-DD].md`、`source-map-[slug]-[YYYY-MM-DD].md` 和 `assembly-check-[slug]-[YYYY-MM-DD].json`，写入 `paper-workspace/05-writing/reviews/main-agent-review-[slug]-[YYYY-MM-DD].md`。审查未完成或正文净稿格式不合规时不得进入论证、材料或文风顾问。
7. 派发 `paper-write-argument-consultant` 与 `paper-write-material-integration-consultant` 复核草稿，修正论证和材料嵌入问题；采纳决策写入 `agent-synthesis-write-[YYYY-MM-DD].md`。
8. 派发 `paper-write-style-consultant` 作为文风总控，统一全文风格、术语、句式节奏、学理化梯度和章节衔接，输出正文净稿 `paper-workspace/05-writing/revisions/styled-[slug]-[YYYY-MM-DD].md`，不得输出建议清单替代正文。
9. 运行 `python3 scripts/writing_scanner.py --report /abs/project/paper-workspace/05-writing/revisions/styled-[slug]-[YYYY-MM-DD].md --out /abs/project/paper-workspace/05-writing/scans/scan-report-[slug]-[YYYY-MM-DD].md`。
10. 运行 `python3 scripts/writing_scanner.py --instructions /abs/project/paper-workspace/05-writing/revisions/styled-[slug]-[YYYY-MM-DD].md --out /abs/project/paper-workspace/05-writing/scans/rewrite-instructions-[slug]-[YYYY-MM-DD].md`。
11. 运行 `python3 scripts/writing_scanner.py --scan /abs/project/paper-workspace/05-writing/revisions/styled-[slug]-[YYYY-MM-DD].md` 记录快速统计。
12. 若扫描器发现高危问题，`style-consultant` 作为文风总控必须按 `rewrite-instructions` 自然重写，再次运行 `--scan`，循环至高危归零；无法归零时，在扫描报告和最终回复中记录残余问题。
13. 最后派发 `paper-write-chapter-standard-reviewer` 做章节硬门槛复核。
14. 完整质量门交给 `paper-master-4ss/modules/check/`：scanner 循环与 `chapter-standard-reviewer` 完成后，不得把全文审稿、编辑首筛、拒稿风险诊断或投稿前综合自检做成 write 内部检查。语言扫描与复杂度诊断仍留 write。将正文净稿、扫描报告、source map、证据边界和目标期刊信息按 `master/handoff-checklists.md` 的 `write -> check` 交接。

已有草稿润色任务不进入 `writing-dispatch-plan` 和 `paper-write-chapter-draft-writer`，直接从 `paper-write-style-consultant` 文风总控、`writing_scanner.py --report`、`writing_scanner.py --instructions` 和 `writing_scanner.py --scan` 开始。

### 文献综述的统一入口

处理文献综述时，先读取 `master/literature-review-protocol.md`。若项目中已有 `02-literature/review-evidence.csv`、`review-outline.md` 与 `review-gaps.md`，它们是正文的优先输入；不得从通用范文重新发明论证结构或丢失 claim_id、paper_id 与原文定位。

综述正文的唯一落点为 `paper-workspace/05-writing/literature-review.md`。改写前在证据表标记保留、修改、移除或新增的判断；正文完成后复核每个关键判断是否仍能回查证据表。检索日志、文献地图、缺口清单和过程注释不得混入该正文。

## 零、总入口：研究路由

正式写作前，优先读取：

```text
resources/research_router.md
```

该文件已经合并原来的 `method_protocol.md` 与 `paradigm_selector.md`。它负责两层判断。

第一层是研究方法协议判断：规范研究、实证研究、阐释研究、混合研究。

第二层是发表范式判断：社会学研究范式、管理世界案例研究范式。

第三层是写作风格判断：学理化梯度与小处入手策略。详见：

```text
resources/writing_style_subrouter.md
```

Skill 加载后，应使用 ask_user 向用户提问。除非用户已经明确给出全部信息，否则不得跳过路由。

### ask_user 提问顺序

结构化示例模块统一遵守 `references/ask-user-question-examples.md`。本节为总入口提问清单；更完整的分层示例见 `resources/research_router.md` 与 `resources/writing_style_subrouter.md`。

第一层，研究方法协议判断。

1. 你的研究问题属于哪一类？
   - 应当如何评价某个制度、概念或安排
   - 某个变量是否影响另一个变量
   - 某个过程、行动或意义是如何形成的
   - 某种方法、工具、系统或研究流程如何运作

2. 你的主要材料是什么？
   - 大规模调查数据、统计数据、实验数据
   - 访谈、田野、档案、案例、历史材料
   - 理论文本、规范性文本、经典文献
   - 代码、日志、脚本、Agent 流程、方法系统
   - 混合材料

3. 你的目标任务是什么？
   - 写概念辨析或规范论证
   - 写实证分析
   - 写案例解释或过程分析
   - 写方法论论文、AI Agent 论文、系统设计论文
   - 暂时不确定

第二层，发表范式判断。

4. 你的目标期刊风格是什么？
   - 社会学研究风格
   - 管理世界风格
   - 公共管理风格
   - 尚未确定

5. 你的研究方法是什么？
   - 量化实证
   - 质性田野或深度访谈
   - 案例研究
   - 理论分析
   - 混合方法

6. 你的预期字数是多少？
   - 1.5 万字以下
   - 1.5 万到 2.5 万字
   - 2.5 万字以上

第三层，写作风格判断。详见 `resources/writing_style_subrouter.md`。

7. 你的论文整体倾向于哪种学理化程度？
   - 轻度：从具体处落笔，让问题意识从现象中浮现，术语精简
   - 中度：术语与经验各半，直接陈述判断（默认）
   - 重度：概念链推进，理论语言主导全篇
   - 混合：不同章节采用不同梯度

8. 你希望引言从哪种"小处"入手？
   - 悖论（展现一对反常现象）
   - 制度后果（展现制度漏洞如何制造问题）
   - 代际断裂（展现知识如何在传递中丢失）
   - 统计数据（用对比数据建立经验基础）
   - 训练场景（展现新手进入实践时的真实遭遇）
   - 不确定，请推荐

总入口结构化示例：

```text
question: "你的研究问题属于哪一类？这会决定后续写作路径和章节标准。"
header: "研究类型"
options: [
  {label: "实证研究", description: "检验变量关系、机制或因果效应，重点写理论机制、变量和模型"},
  {label: "阐释研究", description: "解释过程、行动或意义形成，重点写语境、材料和机制"},
  {label: "规范研究", description: "评价制度、概念或安排，重点写概念界定、价值标准和反驳"},
  {label: "混合/方法研究", description: "讨论方法、系统或研究流程如何运作，重点写方法困境和系统设计"}
]
```

### 路由输出格式

完成提问后，先输出以下内容，再进入写作。

一、研究方法协议判断
- 主类型
- 副类型
- 类型权重
- 判断依据

二、发表范式判断
- 目标范式
- 判定理由
- 与另一范式的差异

三、写作风格判断
- 整体梯度
- 各章节梯度分配（如为混合）
- 引言起笔策略
- 与默认边界的差异

四、推荐写作路径
- 推荐结构
- 推荐章节顺序
- 当前最适合先写哪一部分

五、推荐调用文件
- 章节标准文件
- 范文文件
- 提示词卡片

六、硬停止问题与待确认项
- 当前缺失信息
- 用户需要补充的内容

---

## 一、论文七要素标准

一篇完整的学术论文由七大要素构成。

| # | 要素 | 核心功能 | 篇幅参考 |
|---|------|---------|---------|
| 1 | 标题 + 摘要 + 关键词 | 凝练全文精华，供检索和第一判断 | 标题 ≤ 25 字；摘要 300-500 字 |
| 2 | 引言 | 论证研究合法性 | 约占全文 10-15% |
| 3 | 文献综述 / 理论框架 | 定位知识脉络，建立分析框架 | 约占全文 15-20% |
| 4 | 研究方法与数据 | 叙事性呈现研究过程 | 约占全文 8-12% |
| 5 | 经验分析 / 研究发现 | 以逻辑组织材料，呈现发现 | 约占全文 30-40% |
| 6 | 理论对话 | 回到知识脉络，提炼理论贡献 | 约占全文 10-15% |
| 7 | 结论与讨论 | 总结全文，延展意义 | 约占全文 10-15% |

---

## 二、各章节写作标准

详细写作标准、硬性门槛、迭代规则和反模式已下沉到 `chapters/` 目录。处理具体章节的写作或润色请求时，应先 Read 对应 chapter 文件，再 Read 对应 example 文件。

| 论文要素 | 标准代号 | 详细标准 | 结构模板与提示词 |
|---------|---------|-----------|-----------------|
| 研究路由 | — | `resources/research_router.md` | — |
| 选题与形式逻辑 | — | `chapters/ch01-form-logic.md` + `chapters/ch02-topic-material.md` | — |
| 标题设计 | [G1]-[G4] | `chapters/ch02-topic-material.md` | — |
| 摘要与关键词 | [A1]-[A5] | `chapters/ch02-topic-material.md` | — |
| 引言 | [I1]-[I7] | `chapters/ch03-genesis-question.md` | `examples/intro_example.md` |
| 文献综述 | [L1]-[L6] | `master/literature-review-protocol.md` + `chapters/ch04-lit-review.md` + `chapters/ch05-lit-technique.md` | `examples/lit_review_example.md` |
| 研究方法与数据 | [M0]-[M5] | `chapters/ch06-material-method.md` | — |
| 经验分析 / 研究发现 | [E1]-[E5] | `chapters/ch07-organizing-materials.md` | `examples/findings_example.md` |
| 理论对话 / 分析框架 | [T1]-[T5] | `chapters/ch08-theory-dialogue.md` | `examples/framework_example.md` |
| 结论与讨论 | [C1]-[C6] | `chapters/ch09-conclusion.md` | `examples/conclusion_example.md` |
| 参考文献格式 | [R1]-[R3] | `chapters/ch10-submission-ethics.md` | — |

### 使用协议

0. **路由后截取**：完成研究路由后，运行 `example_extractor.py` 按范式和方法截取对应范文章节，避免加载全部 5 个 example 文件。详见第五节自动化工具。
1. 写前查阅：处理某章节写作请求时，先读取对应 chapter 文件，再读取截取后的 example 文件。
2. 润色对照：对已有文本进行润色时，以 chapter 文件中的标准为检查清单。
3. 快速决策：材料组织逻辑、开头风格、理论对话路径等决策表集中在 `resources/cheatsheet.md`。
4. 标注体系：范文中的 [Gx][Ix][Lx][Mx][Ex][Tx][Cx][Rx] 标注均对应各 chapter 文件中的硬性标准条目。

---

## 三、全文质量检查清单

论文提交前，按以下顺序检查。

### 第一轮：结构完整性

- [ ] 七大要素齐全
- [ ] 各部分篇幅比例合理
- [ ] 各级标题逻辑连贯

### 第二轮：论证严密性

- [ ] 引言有转折词、研究缺口和贡献陈述
- [ ] 文献综述有分析框架和交汇段落
- [ ] 经验分析各分节递进
- [ ] 理论对话回到引言脉络
- [ ] 结论覆盖总结、延展、限制和展望

### 第三轮：材料与引文

- [ ] 关键判断、争议和方法批评可回查证据表中的原文位置
- [ ] 引文服务于段落论证，而非逐篇罗列
- [ ] 文献引用前后密度均衡
- [ ] 正文引用与参考文献列表对应

### 第四轮：语言规范

- [ ] 无“一文中”“该文”等非学术口语
- [ ] 无“以……为例”等标题套路化表达
- [ ] 无空泛创新宣称
- [ ] 无未定义缩写
- [ ] 无正文中嵌入完整论文标题
- [ ] 引号符合必要最少原则

---

## 四、写作约束

以下约束适用于本 Skill 生成或指导的所有学术文本。

1. 禁止在正文行文中嵌入完整论文标题。使用作者和年份引用格式。
2. 禁止使用“一文中”“该文”等非学术口语表述。
3. 避免使用“不是……而是……”句式及其变体。以直接陈述替代先否定后肯定的对立结构。
4. 正文禁止使用破折号。参考文献条目中的论文标题除外。消除破折号时，不得用冒号（：）、逗号（，）或括号（（））直接替换——必须自然重写整个句子，改变句子结构以表达原意。
5. 禁止使用脚本或正则表达式机械替换标点符号（包括但不限于 `——→：`、`——→，`、`——→（）`）。所有标点修改必须由 AI 理解句意后自然重写句子。
6. 避免弱冒号模式：短引导语（如"它告诉我们""X在于""X揭示"等≤12字短语）后不宜直接用冒号引出完整从句。应改为逗号衔接或重构句子。
7. 避免可融入括号：含"就像/特别是/尤其是/亦即/换言之"等信号词的短括号插入语（6-25字），应通过逗号或从句融入主句，而非用括号打断节奏。
8. 引号只在必要时使用。必要场景包括直接引述、首次提出的特殊概念、反讽或非常规用法。
9. 正文引号必须统一为中文引号。
10. 不得删除参考文献条目中的引号。参考文献条目中论文标题所含的引号（如调查名称、专有概念等原文照录的引号）属于文献信息完整性的一部分，不得移除。扫描器在 B1（破折号）、B6（英文引号）和 D4（引号检视）规则中已自动跳过参考文献段落。
11. 定量论文正文中禁止出现系数值与p值的行内配对表述。具体而言：正文不得出现"系数为X.XXX（p<0.XX）""X.XXX（p<0.01）""（系数0.268，p<0.01）"等将回归系数与显著性水平并置的行内形式。统计参数应全部收入表格，正文仅以定性语言报告结果的方向和显著性层级，如"正向显著""在1%水平上正向显著""不显著""边际显著"等。唯一的例外是：可以出现"经验p值X.XXX"和"bdiff经验p值X.XXX"等基于置换检验的精确p值，但每段不超过1处。
12. 禁止中英对照括号的翻译腔写法。具体而言：(a) 正文禁止出现 improvised resilience（即兴韧性）等英文在前、中文翻译在后的对照括号——中文论文中应使用中文术语在前、英文原文在后（若确需标注），或直接使用中文术语；(b) 同一段落中中文（English）括号标注不得超过 2 处，成熟学术概念（如集体效能、社会资本、面子工作、归因理论等）无需加注英文；(c) 同一术语的中英对照标注全文仅首现处需要，后续一律使用中文术语。
13. 复杂度诊断只用于文本质量校准，不用于规避检测。

### 润色循环工作流

所有文本修改必须遵循扫描、指令、重写、再扫描循环。

```text
1. 运行 writing_scanner.py --instructions 生成改写指令
2. AI 阅读指令，逐条自然重写句子——不得用冒号、逗号或括号机械替换破折号
3. 运行 writing_scanner.py --scan 验证（含 B8 破折号机械替换痕迹检测）
4. 若仍有高危检出，回到步骤 1
5. 循环至高危归零；若无法归零，明确记录残余问题和原因
```

---

## 五、自动化工具

### 方法路由器

```bash
python3 scripts/method_router.py paper.md
python3 scripts/method_router.py paper.md --out route_report.md
python3 scripts/method_router.py paper.md --json
```

### 写作扫描器

```bash
python3 scripts/writing_scanner.py --scan paper.md
python3 scripts/writing_scanner.py --report paper.md --out report.md
python3 scripts/writing_scanner.py --instructions paper.md --out instructions.md
```

### 草稿拼接器

```bash
python3 scripts/assemble_drafts.py \
  --plan /abs/project/paper-workspace/05-writing/plans/writing-dispatch-plan-[slug]-[YYYY-MM-DD].md \
  --draft-dir /abs/project/paper-workspace/_logs/agents/write-[YYYY-MM-DD] \
  --out /abs/project/paper-workspace/05-writing/drafts/draft-[slug]-[YYYY-MM-DD].md \
  --manuscript /abs/project/paper-workspace/05-writing/manuscript-[slug]-[YYYY-MM-DD].md \
  --source-map /abs/project/paper-workspace/05-writing/assembly/source-map-[slug]-[YYYY-MM-DD].md \
  --json /abs/project/paper-workspace/05-writing/assembly/assembly-check-[slug]-[YYYY-MM-DD].json
```

`--out` 生成内部合并草稿，保留 task_id、source 注释和拼接元数据；`--manuscript` 生成正文净稿，只包含标题层级和自然段。若正文净稿包含加粗、表格、引用块、代码块、HTML 注释、Mermaid、任务清单或项目符号清单，拼接器必须失败并把错误写入 `assembly-check` JSON。

### 范文截取器

路由完成后，按范式和方法截取对应 example 章节，避免加载全部文件浪费 token。

```bash
# 交互模式
python3 scripts/example_extractor.py \
  --paradigm 社会学研究范式 \
  --method 量化实证 \
  --protocol 实证研究 \
  --out extracted_examples.md

# JSON 路由模式（接收路由输出）
python3 scripts/example_extractor.py --route route_report.json --out extracted_examples.md

# 仅截取指定文件
python3 scripts/example_extractor.py --paradigm 社会学研究范式 --method 量化实证 --files intro,findings

# 预览截取计划
python3 scripts/example_extractor.py --paradigm 社会学研究范式 --method 量化实证 --list
```

### 复杂度分析器

```bash
python3 scripts/complexity_analyzer.py paper.md --out complexity_report.md
python3 scripts/complexity_analyzer.py paper.md --json
```

---

## 六、范文与提示词系统

本 Skill 为论文核心章节提供范文和可复用提示词模板。

| 论文部分 | 文件 | 内容 |
|---------|------|------|
| 引言 | `examples/intro_example.md` | 社会学量化、质性、管理世界案例三种引言模式 |
| 文献综述 | `examples/lit_review_example.md` | 证据驱动综述：可选结构、段落示意与交付前检查 |
| 分析框架 | `examples/framework_example.md` | 维度分解型、理论对话型、机制链型、矩阵型框架 |
| 研究发现 | `examples/findings_example.md` | 量化实证、质性田野、案例研究三种发现模式 |
| 结论与讨论 | `examples/conclusion_example.md` | 社会学范式和管理世界范式结论模式 |

---

## 七、支持文件

| 文件 | 功能 |
|------|------|
| `resources/research_router.md` | 总入口，负责方法协议和发表范式双层判断 |
| `resources/writing_style_subrouter.md` | 第三层风格路由：学理化梯度与小处入手策略 |
| `resources/glossary.md` | 关键术语及定义 |
| `resources/patterns.md` | 写作技法与模式 |
| `resources/cheatsheet.md` | 快速参考、决策表和检查清单 |
| `chapters/` | 分章节写作标准 |
| `examples/` | 范文和提示词 |
| `scripts/method_router.py` | 方法路由器 |
| `scripts/example_extractor.py` | 范文截取器——按路由结果截取对应 example 章节 |
| `scripts/assemble_drafts.py` | 多个 `chapter-draft-writer` 输出的拼接、source map 和完整性检查 |
| `scripts/writing_scanner.py` | 写作扫描器 |
| `scripts/complexity_analyzer.py` | 文本复杂度分析器 |
