# Agent Prompt Blocks（顾问 Prompt 公共块仓库）

本文件集中维护 32 份顾问角色卡共用的标准协议片段，避免在多份角色卡中重复粘贴或产生版本分歧。各角色卡正文仅保留 `<!-- block: <ID> -->` 占位符，派发前由主流程按 ID 展开注入。

## 使用规则

- **展开时机**：按 `master/agent-orchestration.md` §3，在派发顾问前由主流程读取本文件对应段落全文，追加至顾问 prompt 末尾。
- **展开顺序**：先展开 `output-lang-diagram` 或 `output-scope-advice-only`，再展开对应模块的 `ref-*` 参考块。
- **单点维护**：不得在单个角色卡内私自修改公共块条文；需变更共用协议时统一修改本文件。
- **独立沙箱适配**：子代理无法直接读取本文件时，因块内容已展开并嵌入 prompt，执行不受影响。
- **专用规则归属**：各角色专属判据、输出字段与禁止事项保留在各自角色卡及对应 `agents/_reference-base.md`，不写入本文件。

---

## output-lang-diagram

- 输出语言与图示: 顾问意见使用中文 Markdown；若意见涉及机制、流程、派活、退回或风险传播，须按 `master/output-protocol.md` 附 Mermaid 图示，并在图后用 2–4 条中文解释关键节点、采纳路径和剩余风险。

## output-scope-advice-only

- 输出范围: 仅输出顾问意见正文，由主流程综合生成模块产物。顾问意见仅填写判据条目号、判断、依据、风险、建议五类内容；不得直接生成模块最终产物，不得替代主流程作出采纳决策。
- 意见开头须回填一行 `参考库回查:`，格式与角色卡指针行一致（`base=` / `tier=` / `判据=` / `缺口=`）。

## ref-design-sandbox-note

- 沙箱与注入: 子代理运行在独立沙箱中无法直接访问技能包内的 `frame/`、`references/`、`phases/` 时，主流程须按本角色判据条目号及 `_reference-base.md` B3 附加项先读取实际内容并嵌入 prompt 末尾；仅传递路径或行号区间不构成有效注入。

## ref-design-prefilter

- 初筛输入: 主流程从选题提取的关键词，以及 `paper-master-4ss/modules/design/scripts/frame_locator.py --keywords` 输出的候选框架、相关度分数、命中词与 `read_ranges` 行号区间。须先按行号区间读取 `paper-master-4ss/modules/design/frame/theory-frameworks-*.md`，证据不足时再扩展阅读相邻条目。

## ref-design-refs

- 必读模块参考: 按任务读取 `paper-master-4ss/modules/design/references/design-essence.md`、`idea-essence.md`、`storm-patterns.md`、`method-feasibility.md`（方法路由、识别策略、面板三问与学科偏好）、`qualitative-methods.md`、`argument-standards.md`（概念分析 / Toulmin / 反驳 / 规范 / 贡献类型 / 谱系 / 阐释）。
- 必读流程参考: 先确认工作模式（FRAME/STORM/DESIGN/FULL）与研究取向，再按模式读取 `paper-master-4ss/modules/design/phases/01-frame-mode.md`、`02-storm-mode.md`、`03-design-mode.md`、`04-full-pipeline.md`、`05-quality-gates.md`。

## ref-design-phases

- 模式与研究取向门槛: 未完成模式确认（`mode-lock`）与研究取向确认（`research_orientation`）前，仅做需求澄清，不得输出设计结论；纯理论路径可审查材料与论证可行性，不强制变量设计、统计功效或回归设定。

## ref-lit-refs

- 必读模块参考: 按任务读取 `paper-master-4ss/modules/lit/references/search-strategies.md`、`synthesis-guide.md`、`theory-frameworks.md`、`gap-to-hypothesis.md`、`channels.md`、`ncpssd.md`、`cnki.md`、`books.md`、`browser.md`、`publishers.md`、`install-dependencies.md`；涉及综述成稿时加读 `master/literature-review-protocol.md`。
- 必读流程参考: 按当前阶段读取 `paper-master-4ss/modules/lit/phases/phase-0-init.md`、`phase-1-search.md`、`phase-2-landscape.md`、`phase-3-hypothesis.md`。

## ref-lit-phases

- 阶段门槛: 检索阶段未完成不进入文献地图；文献地图未区分「已有研究无效应」与「尚未研究」不进入假设推导；假设推导未通过桥接检查不进入写作交接。
- 唯一登记源: 纳入文献以 `02-literature/paper-registry.csv` 为唯一登记源（含核读状态与全文路径）；证据等级以 `02-literature/review-evidence.csv` 的 `evidence_level` 为准。

## ref-outline-refs

- 必读模块参考: 按任务读取 `paper-master-4ss/modules/outline/references/outline-patterns.md`（实证 / 阐释 / 规范 / 综述模板、范式微调、字数分配及学位论文五章结构）与 `output-formats.md`。
- 必读流程参考: 按当前阶段读取 `paper-master-4ss/modules/outline/phases/01-scan-materials.md`、`02-build-outline.md`、`03-quality-check.md`。

## ref-outline-phases

- 阶段门槛: 材料扫描未完成不进入大纲构建；大纲构建未完成不开展质量检查；质量检查的缺口结论须区分「补齐材料可解决」与「须重构大纲」。

## ref-analysis-refs

- 必读模块参考: 按任务读取 `paper-master-4ss/modules/analysis/references/quantitative-model-router.md`、`quantitative-reporting-standards.md`、`qualitative-routing-design.md`、`qualitative-analysis-methods.md`、`qualitative-quality-integration.md`、`python-ecosystem-setup.md`、`r-ecosystem-setup.md`、`stata-ecosystem-setup.md`。
- 必读流程参考: 按当前阶段读取 `paper-master-4ss/modules/analysis/phases/01-init-and-routing.md`、`02-quant-cleaning.md`、`03-basic-regression.md`、`04-extended-models.md`、`05-qualitative-and-mixed.md`、`06-export-and-quality-gates.md`，并核对命令行执行门槛。

## ref-analysis-runtime

- 运行与产物要求: 分析结论须可追溯至命令行执行记录；未执行或执行失败的模型仅记入限制与阻断说明，不得写入统计结论。表格默认导出 CSV，采用论文宽表结构（模型编号行、因变量行、变量系数行、括号内 t/z 值行、固定效应「是/否」行、观测值行、中文注释行），并使用 `display_name` 可发表展示名。

## ref-write-refs

- 必读模块参考: 按任务读取 `resources/research_router.md`、`writing_style_subrouter.md`、`patterns.md`、`cheatsheet.md`、`glossary.md`。
- 必读章节参考: 按当前写作章节读取 `chapters/ch01-form-logic.md` 至 `ch10-submission-ethics.md` 中对应标准。

## ref-write-tooling

- 必读工具参考: 涉及文风扫描时读取 `scripts/writing_scanner.py` 的调用协议（`--report` / `--instructions` / `--scan`）与扫描输出格式。

## ref-write-clean-copy

- 正文净稿要求: `manuscript*.md`、`revisions/styled*.md`、`05-writing/literature-review.md` 仅允许 `#` 至 `####` 标题层级与自然段；不得出现加粗、表格、引用块、代码块、HTML 注释、Mermaid 图、任务清单或过程元信息。

## ref-check-refs

- 必读模块参考: 按审阅维度读取 `paper-master-4ss/modules/check/chapters/ch01-outline-selection-design-writing.md`、`ch02-title.md`、`ch04-abstract.md`、`ch05-keywords.md`、`ch06-introduction.md`、`ch07-body.md`、`ch08-conclusion.md`、`ch09-notes-and-references.md`、`ch10-technical-standards.md`、`ch12-submission.md`，以及 `paper-master-4ss/modules/check/patterns.md`、`cheatsheet.md`。

## ref-check-protocol

- 审阅协议:
  1. 为每项问题提供原文位置/证据、对应规范或期刊要求、严重度、诊断、修改动作、退回模块及复核标准。
  2. 严重度仅使用 `阻断`、`重要`、`优化` 三级；仅诚信、事实/引文、核心证据或论证闭环问题可判为 `阻断`。
  3. 缺少引文原文或期刊规则时标注「待核验」，不得推断为违规。
  4. 已提供目标期刊规则时优先按其公开要求核验；未提供时明确标注 `期刊特定核验: 未执行`。

## ref-check-matrix-output

- 输出格式: 中文 Markdown，按「参考库回查—发现—问题矩阵—限制—建议」组织。问题矩阵固定包含字段：`check_id`、检查维度、原文位置/证据、依据、严重度、诊断、修改动作、退回模块、复核标准。涉及退回时附 Mermaid 图，并说明主路径、证据缺口与未派发角色。

## ref-submission-refs

- 必读模块参考: 按任务读取 `paper-master-4ss/modules/submission/references/citation-rules.md`、`journal-style-sociological-research.md`、`install-dependencies.md`。
- 工具参考: 涉及格式或引文核查时，读取 `paper-master-4ss/modules/submission/scripts/` 中对应脚本的说明与调用方式。

## ref-update-refs

- 必读模块参考: `paper-master-4ss/modules/update/references/source-types.md`、`update-schema.md`、`review-rubric.md`、`target-registry.md`。
- 必读流程参考: 按阶段读取 `paper-master-4ss/modules/update/phases/01-purpose-routing.md`、`02-social-science-extraction.md`、`03-literature-enrichment.md`、`04-target-surface-routing.md`、`05-compatibility-and-risk-gates.md`、`06-review-package.md`。
- 按需参考: 材料或候选条目指向特定模块时，读取对应 `paper-master-4ss/modules/update/references/targets/<module>-targets.md`。

## ref-mechanigraph-refs

- 必读模块参考: `paper-master-4ss/modules/mechanigraph/references/design_system.md`（坐标系统、组件尺寸、防穿透公式、间隙标准）、`drawing_patterns_reference.md`（8 类构型几何样板）、`layout_catalog.md`（拓扑分类名录与案例）。
- 必用工具: `paper-master-4ss/modules/mechanigraph/scripts/render_svg.py`（无头渲染与视觉核查）、`paper-master-4ss/modules/mechanigraph/resources/academic_defs.svg`（标准箭头 marker）。

---

## 块 ID 与原重复文本对照

| 块 ID | 替代的原重复协议片段 | 原重复次数 |
|---|---|---:|
| `output-lang-diagram` | 输出语言与 Mermaid 图示要求 | 42 |
| `output-scope-advice-only` | 顾问仅输出意见正文与回查行要求 | 39 |
| `ref-design-sandbox-note` | `design` 独立沙箱内容注入说明 | 5 |
| `ref-design-prefilter` | `frame_locator.py` 初筛输入与行号读取要求 | 5 |
| `ref-design-refs` | `design` 模块参考与流程参考读取说明 | 5 |
| `ref-design-phases` | `design` 模式与研究取向前置门槛 | 5 |
| `ref-lit-refs` / `ref-lit-phases` | `lit` 模块参考与阶段门槛 | 5 / 5 |
| `ref-outline-refs` / `ref-outline-phases` | `outline` 模块参考与阶段门槛 | 5 / 5 |
| `ref-analysis-refs` | `analysis` 模块必读参考清单 | 13 |
| `ref-analysis-runtime` | `analysis` 执行追溯与宽表导出要求 | 2 |
| `ref-write-refs` | `write` 模块与章节参考清单 | 12 |
| `ref-write-tooling` | `writing_scanner.py` 调用参考 | 6 |
| `ref-write-clean-copy` | `write` 正文净稿格式约束 | 3 |
| `ref-check-refs` | `check` 章节与速查参考清单 | 3 |
| `ref-check-protocol` | `check` 审阅分级与待核验协议 | 3 |
| `ref-check-matrix-output` | `check` 问题矩阵输出格式 | 3 |
| `ref-submission-refs` | `submission` 体例与工具脚本参考 | 6 |
| `ref-update-refs` | `update` 规范与阶段参考清单 | 5 |
| `ref-mechanigraph-refs` | `mechanigraph` 制图规范与渲染工具参考 | 2 |
