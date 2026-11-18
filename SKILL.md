---
name: paper-write-4ss
description: "中文社会科学论文写作系统。先通过 research_router.md 完成研究方法协议与发表范式双层路由，再按章节标准和范文提示词完成写作、润色和检查。支持规范研究、实证研究、阐释研究、混合研究四类方法协议，以及社会学研究范式和管理世界案例研究范式两类发表风格。配备 writing_scanner.py 与 complexity_analyzer.py，用于语言反模式扫描和文本复杂度诊断。"
capabilities: read_file, write_file, run_shell, search_text, spawn_agent
---

> **拆分版路径约定**：本包由 `paper-master-4ss/scripts/export_standalone.py` 从 `paper-master-4ss/modules/write/` 自动导出，是可独立安装的运行版。包内相对路径（`agents/`、`phases/`、`references/`、`master/` 等）相对本包根目录解析；跨模块路径 `paper-master-4ss/modules/<x>/...` 相对同级安装的 `paper-master-4ss/` 总控包解析。请勿直接编辑本包：修改总控模块后重新导出。
>
> **宿主无关约定**：本包不预设宿主，也不在 frontmatter 声明 `tools`/`hooks`/`model` 等宿主专属键。启动时按 `references/runtime-adapter.md` §5 探测当前环境可用能力，再按通用能力名（`read_file`、`search_text`、`web_search`、`run_shell`、`spawn_agent` 等）执行；宿主样例见 `references/agent-software-adapters.md`（样例，非名单）。

# Paper Write 4SS：中文社会科学论文写作系统

> 参数提示：[文本路径] [路由|润色|扫描|检查|改写|复杂度]

本文件中的 `modules/...` 路径默认相对于 `paper-master-4ss/` 根目录解析；在模块目录内直接运行时可使用 `chapters/...`、`examples/...`、`resources/...`、`scripts/...`。

## 0. 模块边界与核心约束

### 0.1 职责定位

本模块负责章节起草、段落改写、术语统一、文风扫描与正文净稿输出；不承担全文审稿（`check`）、Word 排版与投稿打包（`submission`）或上游证据构建（`lit` / `analysis`）。表达规范统一维护于 `resources/style_gate.md`，本文件及 `chapters/`、`examples/`、`agents/` 仅引用规则编号，不重复复制条文。

### 0.2 三项阻断级要求

1. **引文可回查**：关键判断须能定位至证据表行或原文具体位置；未核验内容不得进入正文。
2. **材料不虚构**：数据、访谈、档案与统计量严格按既有材料撰写，缺口如实记录。
3. **正文净稿格式纯净化**：正文区仅保留 `#`–`####` 标题层级与自然段（`master/output-protocol.md` §2）。

### 0.3 产物与输出路径

| 产物类型 | 输出路径 |
|---|---|
| 分段章节草稿 | `paper-workspace/_logs/agents/write-[date]/` |
| 合并草稿、source map 与拼接检查 JSON | `paper-workspace/05-writing/drafts/`、`05-writing/assembly/` |
| 正文净稿 | `paper-workspace/05-writing/manuscript-[slug]-[date].md` |
| 风格统一稿 | `paper-workspace/05-writing/revisions/styled-[slug]-[date].md` |
| 扫描报告与改写指令 | `paper-workspace/05-writing/scans/` |
| 独立文献综述净稿 | `paper-workspace/05-writing/literature-review.md` |
| 正文矢量机制图 | `paper-workspace/figures/`（由 `mechanigraph` 生成） |

### 0.4 下游边界

本模块负责完成语言与章节论证动作；全文审稿、编辑首筛、拒稿风险诊断及 Word 导出按第 9 章交接给 `check` 与 `submission`。

## 1. 写作路由判定

### 1.1 三要素路由

| 判定维度 | 可选取值 | 决定内容 |
|---|---|---|
| 研究问题类型 | 评价制度 / 变量关系 / 过程与意义 / 方法与系统 | 章节重心与方法展开方式 |
| 主要材料（主轴） | 访谈田野档案（田野） / 调查与统计数据（计量） / 实验 / 理论文本（历史理论） / 方法论文本（方法批判） / 混合 | 结构与文体配方（`writing_style_subrouter.md` 规则零） |
| 目标期刊 | 社会学研究 / 管理世界 / 公共管理 / 未定 | 摘要、引文体例与写作风格 |

目标期刊允许标注「未定」，此时按通用社科体例处理（摘要与关键词给出要素清单而不限定死字数）。完整协议判定读取 `resources/research_router.md`，文体配方与梯度策略读取 `resources/writing_style_subrouter.md`。动笔前须先将研究问题转化为机制问句（关注「如何、在何种条件下」而非仅问「是否存在」），按机制问句所需论证维度划分正文节次。

### 1.2 章节标准与参考范文映射

| 论文要素 | 规范代号 | 标准文件 | 参考范文 |
|---|---|---|---|
| 形式逻辑与结构变体 | — | `chapters/ch01-form-logic.md` | — |
| 标题、摘要、关键词 | `[G1]`–`[G4]`、`[A1]`–`[A5]` | `chapters/ch02-topic-material.md` | — |
| 引言 | `[I1]`–`[I7]` | `chapters/ch03-genesis-question.md` | `examples/intro_example.md` |
| 文献综述 | `[L1]`–`[L6]` | `master/literature-review-protocol.md` + `ch04`、`ch05` | `examples/lit_review_example.md` |
| 材料与方法 | `[M0]`–`[M5]` | `chapters/ch06-material-method.md` | — |
| 经验分析 | `[E1]`–`[E5]` | `chapters/ch07-organizing-materials.md` | `examples/findings_example.md` |
| 理论对话 / 分析框架 | `[T1]`–`[T5]` | `chapters/ch08-theory-dialogue.md` | `examples/framework_example.md` |
| 结论与讨论 | `[C1]`–`[C6]` | `chapters/ch09-conclusion.md` | `examples/conclusion_example.md` |
| 参考文献与伦理 | `[R1]`–`[R3]` | `chapters/ch10-submission-ethics.md` | — |

### 1.3 跳过路由的例外

单句改写、术语统一、旧稿润色或局部补写可直接进入第 7 章执行扫描与改写，并在日志中记一行跳过路由原因。

## 2. 学术写作规范

- **2.1 引文与证据**：核心论断须可回查至证据或原文位置，未核验文献不入正文（`exp-cite-01`）。
- **2.2 材料与数据说明**：进入结果前须交代三层理由（为何选用该数据集、为何选择相应波次、时间跨度如何服务识别设计），具体变量名、问卷模块与清洗细节放入脚注或附录（`exp-var-01`）。
- **2.3 统计结果表述**：参数全部入表，正文报告影响方向与显著性层级，不逐格复述回归表；需比较效应量或边际效应时可给出该数值与显著性（每段不超过一处）并说明量纲与参照类别（`exp-param-01`）。
- **2.4 术语与缩写**：全文保持一致，首次出现标注为「中文术语（英文原文）」（`exp-bilingual-order-01`）；缩写首现给出全称，跨节再次使用时按需展开（`exp-abbr-01`）。
- **2.5 正文净稿格式**：仅保留 `#`–`####` 标题与自然段，严禁出现加粗、表格、引用块、代码块、Mermaid 图、任务清单或过程标签（`master/output-protocol.md` §2）。
- **2.6 参考文献体例**：遵循目标期刊体例；未指定期刊时默认采用 GB/T 7714 与作者—年份夹注，条目中的书名/篇名引号不得删去（`exp-quote-ref-01`）。
- **2.7 摘要与关键词**：依目标期刊稿约；未定期刊时摘要控制在 250–350 字并覆盖研究问题、材料方法、主要发现与理论贡献四要素；关键词 3–8 个（GB/T 7713），多数期刊限制 3–5 个。
- **2.8 不可声称边界**：上游标明不得声称的结论、待核验引文及超范围推断严禁写入正文。

## 3. 表达质量检查分层

| 级别 | 涉及内容 | 处置方式 |
|---|---|---|
| 阻断 | 第 2 章八项规范 | 须彻底修正，不得带入下游交接 |
| 重要 | 论证与结构 | 写入改写指令逐条核查修改 |
| 优化 | 语言偏好 | 仅提示建议，允许作者保留 |

### 3.2 重要级：论证与结构核查

- **论点先行**：每节前三句须明确呈现该节核心判断；
- **材料功能性**：若删去某段材料后论断依然成立，则该材料属于冗余装饰，须重新定位或删除；
- **逻辑递进**：明确与上节属于补充、限定还是反驳关系后方可使用「进一步」等递进连接；
- **结论回扣**：理论对话与结论须回到引言定位的知识脉络，不得在结尾另起新话题。

### 3.3 优化级：标点与表达（详见 `resources/style_gate.md`）

- 破折号按规范使用；同段超过两处或仅承担可由从句顺接的解释时改写（`exp-dash-01`）。
- 「不是……而是……」在同一节出现三次以上或成为段落主干结构时改写（`exp-negpos-01`）。
- 冒号与括号在单段内超过三处时精简（`exp-colon-01`、`exp-paren-01`）。
- 引号仅用于直引原文、首现界定特殊概念及反讽（`exp-quote-bound-01`）。
- 著作名可入正文承担概念溯源，篇名与刊名优先改入夹注（`exp-booktitle-01`）。

### 3.4 风格偏好声明

本模块默认偏好（黑白矢量图、克制使用引号与破折号、减少三点式排比列举）属于可覆盖偏好而非强制规范；当目标期刊样文、合作者要求或旧稿既有文风有明确要求时，以外部要求优先。

## 4. 分章论证动作规范

### 4.1 七要素与结构变体

规范论文包含七项核心要素：题摘（检索入口）、缘起/引言（研究合法性）、综述（知识脉络定位）、方法与材料（过程透明）、经验分析（证据支撑）、理论对话（贡献提炼）、结论（边界与延展）。采用三段式递进、误区辨析或「症结—出路」等结构变体时，须说明被合并或省略要素的替代承接安排。

### 4.2 分章动作与合格判据

| 章节 | 核心论证动作 | 常见失误 | 合格判据 |
|---|---|---|---|
| 题摘 | 标题容纳对象与核心判断；摘要覆盖四要素 | 堆砌术语、摘要退化为背景介绍 | 仅读标题摘要即可判断研究内容与贡献 |
| 引言 | 现象 -> 现有解释失效 -> 切入视角与理由 -> 逻辑推进 -> 材料方法 | 背景过长、缺口空泛、承诺与正文脱节 | 五动作完整，研究缺口落到具体维度或条件 |
| 综述 | 定位学术争论、比较证据、指明何处不可裁决 | 逐篇罗列文献、无定位批评 | 每段推进一个可争论判断并可回查证据 |
| 方法与材料 | 说明研究对象、材料选择、进入方式、分析路径与局限 | 只报数据集名称不论证选用理由 | 读者可判断研究过程成立，操作细节入附录 |
| 经验分析 | 材料呈现 -> 论断 -> 与既有解释关系 -> 概念命名 | 以表代文、逐行复读表格、伪递进 | 每个分析单元完成「材料—判断—理论关系」三问 |
| 理论对话 | 回到引言定位的文献脉络，对比新发现与旧知识 | 脱离正文突然拔高、生硬套用框架 | 对话对象与引言定位文献前后一致 |
| 结论 | 分层发现 -> 适用边界 -> 未答问题 -> 后续研究方向 | 复述摘要、空泛谈局限、以局限句收尾 | 四要素完整，末段不以研究局限收束 |

### 4.3 篇幅参考区间

以下比例仅用于结构体检而非硬性配额：引言 10–20%、综述与框架 15–25%、方法与材料 8–15%、经验发现 30–45%、理论对话 8–15%、结论 8–12%。显著偏离时须说明理由，要素缺席须交代替代安排。

### 4.4 摘要与结论的区分

摘要与结论可共享核心发现，但表述层次不同：摘要以四要素各一句概括全文；结论须展开分层发现、边界条件、未决问题与后续方向。避免摘要与结论逐句重复。

## 5. 范文使用规则

| 使用档位 | 允许做法 | 禁止做法 |
|---|---|---|
| 风格参照 | 领会学术论证节奏与表述分寸 | 照抄句式、过渡连接词与固定段落顺序 |
| 问题诊断 | 使用范文中的「常见失败」清单自查当前稿件 | 按范文结构机械比对字数或段落数量 |
| 禁用边界 | — | 将注释标签写进正文、套用固定模板句骨架、照搬范文贡献条数 |

路由确定后可运行 `scripts/example_extractor.py` 仅提取「可选结构 + 常见失败」作为参考，并在提取文本前标注「以下仅作参照，不作为固定骨架」。反例对比详见 `examples/contrasts_example.md`。

## 6. 风格参数选集

详见 `resources/writing_style_subrouter.md`：
- **风格梯度**：轻档（小处切入、术语精简）、中档（术语与经验平衡、直接判断，默认）、重档（概念链推进、理论语言主导）。梯度默认建议：标题轻–中、摘要中、引言轻、综述中、框架中–重、方法与发现轻–中、理论对话中–重、结论轻–中–重。
- **起笔策略（15 类）**：悖论、制度后果、代际断裂、统计数字、训练场景、个案异常、概念误用、历史转折、分类边界、日常实践、技术中介、政策执行缝隙、组织流程、文献沉默、评价困境。
- **结尾策略（7 类）**：总结收束、发现回扣、纵横延展、限制转展望、理论升维、开放设想、实践回响。

## 7. 工具脚本与质量闸门

### 7.1 文风扫描器（38 条规则，全篇预算制）

```bash
python3 scripts/writing_scanner.py --scan paper.md
python3 scripts/writing_scanner.py --report paper.md --out report.md
python3 scripts/writing_scanner.py --instructions paper.md --out instructions.md
python3 scripts/writing_scanner.py --check paper.md            # JSON 机读，high>0 返回退出码 1
python3 scripts/writing_scanner.py --budgets                   # 输出全篇预算配置表
```

`high` 级包含可机械核验的规范错误、诚信隐患及预算超限项（如「不是…而是…」≤ 2 次、「之所以…是因为…」≤ 1 次、防御性预告/自辩/黑话预算 0、罗列式综述、引文交叉核对失败），交付前须清零；`medium` 级生成改写指令；`low` 级仅作提示。预算标准见 `resources/style_gate.md` §五。

### 7.2 扫描—改写循环

```text
1. 运行 --instructions 生成改写指令
2. 逐条自然重写句子（不得用冒号、逗号、括号机械替换标点）
3. 运行 --scan 或 --check 复检（退出码 0 通过）
4. 确保 high 项归零，记录 medium 项取舍理由
```

若 `high` 项确因客观原因无法归零，须在扫描报告与最终回复中写明残余项及理由。

### 7.3 复杂度诊断

```bash
python3 scripts/complexity_analyzer.py paper.md --out complexity_report.md
```

仅用于诊断表达质量，不得用于刻意规避检测（`exp-complexity-01`）。

### 7.4 草稿准入闸门（`draft_gate.py`）

```bash
python3 scripts/draft_gate.py <写手输出.md> --task-id W3 [--json verdict.json]
```

写手输出须通过该闸门方可进入拼接。脚本逐项核查：元数据块完整（含 `## 草稿元数据`）、JSON 合法、字数在任务包 ±30% 范围内、无正文装饰违禁项、扫描器 `high=0`、正文全部夹注均在 `citations_used` 中声明证据来源。未过闸门时须由写手按报错整篇重写重交，不接受局部补丁拼凑。

### 7.5 草稿拼接（`assemble_drafts.py`）

```bash
python3 scripts/assemble_drafts.py \
  --plan /abs/project/paper-workspace/05-writing/plans/writing-dispatch-plan-[slug]-[date].md \
  --draft-dir /abs/project/paper-workspace/_logs/agents/write-[date] \
  --out /abs/project/paper-workspace/05-writing/drafts/draft-[slug]-[date].md \
  --manuscript /abs/project/paper-workspace/05-writing/manuscript-[slug]-[date].md \
  --source-map /abs/project/paper-workspace/05-writing/assembly/source-map-[slug]-[date].md \
  --json /abs/project/paper-workspace/05-writing/assembly/assembly-check-[slug]-[date].json
```

`--out` 生成保留 `task_id` 与来源注释的内部草稿；`--manuscript` 生成正文净稿。若写手输出未过 `draft_gate` 或净稿包含禁用装饰符号，脚本报错退出并写入 `assembly-check` JSON，不得流入下游复核。

### 7.6 执行目录初始化

执行 `scripts/` 下 Python 脚本前，先切换至本 `SKILL.md` 所在目录，工作区输出统一传入绝对路径：

```bash
cd "$(dirname "/path/to/SKILL.md")"
```

## 8. 顾问协作与防漂移约束

默认由单主流程执笔；仅当全文初稿需多章并行或开展多章并行重写时按需派发 `agents/` 下四个顾问（`structure-writing-consultant`、`chapter-draft-writer`、`draft-review-consultant`、`style-consultant`，标准名以 `references/agent-registry.md` 为准；起草者与评审者须分离；未派发时记录 `agent-skip`）。

**长会话防漂移三项硬约束**：
1. **任务包最小化**：派发写作任务仅携带当前任务包所需蓝图、证据行、边界与不可声称清单，不携带更早轮次对话与全量文献。
2. **规则重读**：每次写作任务包开头须显式要求重读 `style_gate.md` §五预算表与对应章节 `chapters/ch*.md` 的常见失败清单。
3. **闸门拦截**：写手输出一律经 `draft_gate.py`（§7.4）机检，不合格直接退回重写。

最小输入包包括：路由结论（含文体配方名）、任务范围、证据映射与边界、不可声称清单及目标期刊。写作规划优先派生自 `03-outline/paragraph-blueprint-[slug]-[date].md`（缺失时记录并基于合理逻辑重构结构）。拼接后主流程可对正文做连贯性润色（不改事实与证据边界），并须重跑 §7.2 扫描循环。所有交付产物命名均带 `[slug]-[date]`。

## 9. 阶段交接

交接清单详见 `master/handoff-checklists.md`：向 `check` 交付最新正文净稿、格式合规状态、扫描报告、修订记录、source map（仅作追溯）、研究问题、证据边界、待核验引文清单及目标期刊信息。本模块不执行全文审稿、编辑首筛、Word 导出与投稿打包。

## 附录 A：模块文件索引

| 路径 | 内容 |
|---|---|
| `resources/style_gate.md` | 规范/惯例/偏好三层表达规则表与全篇预算表 |
| `resources/top-journal-craft.md` | 顶刊写作准则与五类文体配方 |
| `resources/research_router.md`、`writing_style_subrouter.md` | 方法协议与范式路由；文体配方、梯度、起笔与结尾选集 |
| `resources/cheatsheet.md`、`patterns.md`、`glossary.md` | 决策速查、论证技法与术语表 |
| `chapters/ch01`–`ch10` | 分章写作规范与常见失败 |
| `examples/` | 5 篇可选结构范文及 `contrasts_example.md` 反例对照 |
| `scripts/` | 扫描器、草稿闸门、复杂度分析、范文提取、草稿拼接与方法路由脚本 |

## 附录 B：外部标准依据

| 标准 / 依据 | 覆盖范围 | 模块内落点 |
|---|---|---|
| GB/T 15834《标点符号用法》 | 破折号、冒号、括号、引号规范 | `exp-dash-01`、`exp-colon-01`、`exp-paren-01`、`exp-quote-cn-01` |
| GB/T 7713、GB/T 7714 | 摘要四要素、关键词数量、术语一致与引文规范 | §2.4、§2.6、§2.7 |
| 目标期刊稿约与 `submission/references/journal-style-*.md` | 篇幅、摘要字数、关键词数量与图表体例 | §2.6、§2.7、§4.3 |
| 学术诚信规范 | 引文可回查、材料不虚构、统计报告完整 | §0.2、`exp-cite-01` |
| `master/output-protocol.md` | 正文净稿格式与插图规范 | §2.5、§4.2 |
