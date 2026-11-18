---
base-id: write-2026.10.24
module: write
---

# write 模块参考库回查底座

本文件是 `write` 模块 4 个顾问角色的唯一参考回查源。各顾问卡仅保留指针行 `参考库回查: base=write-2026.10.24; tier=…; 判据=…; 缺口=…`。

## B1 核心摘录（≤1200 字，主流程注入用）

写作阶段实行起草与评审分离：`chapter-draft-writer` 仅输出章节草稿，`draft-review-consultant` 出具评审结论，`style-consultant` 统筹全文文风与净稿定稿，三者上下文职责不混同。

写作从派活计划出发：`structure-writing-consultant` 产出的 `writing-dispatch-plan` 为十列表（`task_id`、章节/小节、段落功能、输入材料、章节标准、范文片段、证据映射、上下文边界、禁止声称内容、派活顺序）。任务优先依据 `paragraph-blueprint` 中标为「可写」的段落生成，不擅自重构大纲结构；需调整结构时退回 `outline` 处理。

草稿评审在一张评审表中覆盖三项核心维度：论证强度（问题意识—论点—证据—理论对话—贡献表达成链）、材料嵌入（引文后有分析、数据以表格为主正文做定性解释、访谈案例转化为论证资源）与章节门槛（对照 `chapters/ch01–ch10` 的规范与常见失败）。三项共读同一份合并草稿与对应章节标准。

文风总控交付正文净稿而非修改意见清单：统一术语、指称、句式节奏、学理化梯度与章节衔接，并依据扫描器 `rewrite-instructions` 自然重写句意（不机械替换标点、不新增材料、不越界扩大结论）。`styled-*.md` 仅允许标题层级与自然段。

正文净稿禁令：`manuscript*.md`、`revisions/styled*.md`、`05-writing/literature-review.md` 严禁包含加粗、表格、引用块、代码块、HTML 注释、Mermaid 图、任务清单或过程元信息。草稿的过程元信息仅可置于 `## 正文草稿` 之外的指定区域。

本模块不承担全文审稿、编辑首筛、拒稿风险诊断或投稿包检查（交由 `check` 与 `submission` 模块）。

## B2 判据条目

C01 计划优先：任务源自 `writing-dispatch-plan`，优先取 `paragraph-blueprint` 中「可写」段落；结构缺陷退回 `outline` 处理。

C02 任务包完备性：每个 `task_id` 具备章节功能、段落大意、上下文边界、输入材料、章节标准、证据映射与禁止声称内容；缺项标「需补」，不得带缺放行。

C03 拆分粒度与顺序：章节/小节/段落任务不重复、不缺漏、顺序正确；发现错位先修订计划再派发。

C04 论证链条：问题意识、中心论点、证据、理论对话与贡献表达逻辑贯通，理论概念服务解释而非堆砌。

C05 贡献表述克制：研究贡献具体、克制、可追溯，不作空泛拔高。

C06 材料论证化嵌入：文献引用后有分析，数据以表格为主、正文做定性解释，访谈与案例紧扣论点分析。

C07 证据边界遵守：材料仅限任务输入包；缺失摘要或未入证据链的文献不得写入正文证据。

C08 章节标准达标：依据对应 `chapters/ch01-form-logic.md` 至 `ch10-submission-ethics.md` 逐条核查门槛与常见失败。

C09 章节功能到位：核查本章是否完成应有论证功能、是否越位承担他章功能、是否需退回大纲或材料阶段。

C10 单任务纪律（`writer`）：仅完成指定 `task_id`，不擅自扩写他章、重排任务或将任务大意直接拼入正文。

C11 定量结果写法：正文仅做方向与显著性层级的定性解释，统计参数归表，不在正文中行内并置系数与 p 值。

C12 禁止虚构内容：严禁虚构文献、作者、年份、数据、访谈摘录、显著性、模型输出或政策事实。

C13 正文净稿纯净度：草稿正文区与 `styled-*.md` 仅含 `#`–`####` 标题与自然段，不含任何禁用装饰或过程元信息。

C14 全文文风统一：术语、指称、衔接与梯度全文一致，消除口语化、标题嵌入、弱冒号与过度引号。

C15 扫描—改写循环：依据 `rewrite-instructions` 自然重写并重跑 `--scan` 至 `high` 项归零；无法归零时如实记录残余项与原因。

C16 起草与评审分离：`chapter-draft-writer` 不得自审放行；评审由 `draft-review-consultant` 完成，文风由 `style-consultant` 总控。

C17 拼接与主审前置：多任务草稿须经 `assemble_drafts.py` 拼接生成 draft、source map 与 assembly check，并由主流程审阅后方进入评审链。

C18 交接边界：按 `master/handoff-checklists.md` 向 `check` 交付正文净稿、扫描报告、source map、证据边界与目标期刊信息；不越界替代审稿与投稿模块。

C19 阶段前置门控：研究路由未定不规划结构；`writing-dispatch-plan` 未落盘不派发写手；主审未完成不派发评审；扫描未通过不定稿净稿。

C20 可追溯要求：判断指向具体 `ch*.md` 条款、计划 `task_id` 或扫描器输出；缺口标注「待核验」。

## B3 角色附加项

| 标准名 | 判据条目 | 附加参考 | 派活档位 |
|---|---|---|---|
| `paper-write-structure-writing-consultant` | C01 C02 C03 C17 C19 | `resources/research_router.md` 第七节、`resources/patterns.md`、`03-outline/paragraph-blueprint-*.md` | T1 |
| `paper-write-draft-review-consultant` | C04 C05 C06 C07 C08 C09 C16 C20 | `chapters/ch01–ch10` 对应章、`resources/patterns.md`、`resources/cheatsheet.md` | T2（含通过/不通过阻断） |
| `paper-write-chapter-draft-writer` | C10 C11 C12 C13 C19 C20 | `writing-dispatch-plan` 单任务包、`chapters/ch*.md` 当章标准、`resources/writing_style_subrouter.md` | T2（writer） |
| `paper-write-style-consultant` | C13 C14 C15 C19 | `resources/writing_style_subrouter.md`、`resources/style_gate.md`、`scripts/writing_scanner.py`（`--report`/`--instructions`/`--scan`） | T2（正文净稿落盘） |

L1 默认单点角色：`paper-write-draft-review-consultant`（单次覆盖论证强度、材料嵌入与章节门槛）。
