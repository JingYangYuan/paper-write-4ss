# Paper Master 4SS — 顾问注册表

本文件定义全包 32 个顾问角色的标准名称、文件路径、职责边界与回查级别。该表格同时作为 `scripts/paper_master_guard.py agent-check` 的解析源，表头列序与字段格式须保持固定。

> 顾问总数：**32** ｜ 覆盖模块：**9** ｜ 回查底座版本：`*-2026.10.24` ｜ 修订日期：2026-10-28

## 1. 命名与调度规则

- **以标准名为唯一执行标识**：表中的「标准名」须与对应顾问文件 frontmatter 中的 `name:` 完全一致。简称仅用于口语或简写说明，不得作为执行标识；跨模块或同名易混时，须查表确认模块与完整路径。
- **派活清单要求**：每次派发须在 `agent-brief.md` 保留完整映射链：`用户/模块需求 -> 标准名 -> 文件路径 -> 顺序 -> 并行/顺序复核`。中途增删角色须先更新清单并说明理由。
- **能力声明映射**：顾问文件内的能力声明不构成运行环境硬约束；实际可用性以 `references/runtime-adapter.md` §5 探测结果为准，缺失能力须按 `master/agent-orchestration.md` 记录回退，不得虚构结果。
- **按情境最小化派发**：依据当前步骤的决策风险决定选派角色，不得因研究范式或模块名称套用固定名单。档位（L0 / L1 / L2）与升降档条件见 `master/agent-orchestration.md` §1.6；各模块 L1 默认角色定义在对应 `agents/_reference-base.md` 的 B3。
- **输出格式**：顾问输出须遵守 `master/output-protocol.md`（中文 Markdown；涉及机制、流程、派活、退回或风险传播时附 Mermaid 图与 2–4 句中文解释）。
- **`design` 模块前置输入**：派发 `design` 顾问前，须由主流程提供选题关键词及 `paper-master-4ss/modules/design/scripts/frame_locator.py --keywords` 输出的候选框架、相关度分数、命中词与 `read_ranges` 行号区间；顾问先按指定区间读取 `frame/theory-frameworks-*.md`，不足时再扩展至相邻条目。
- **能力缺失降级**：运行环境不支持并行或子代理派发时，按相同清单顺序复核并记录 `sequential-review` 及缺失原因；轻量任务跳过顾问时记录 `agent-skip` 及理由。

## 2. 参考库回查级别（T0 / T1 / T2）

各模块的必读参考清单、判据条目与角色附加项统一维护在 `modules/<module>/agents/_reference-base.md`。顾问文件仅保留单行指针：

```text
参考库回查: base=<module>-2026.10.24; tier=<T0|T1|T2>; 判据=<C01,C02,…>; 缺口=<无|按需记录>
```

| 级别 | 适用对象 | 核查要求 | 执行方 |
|---|---|---|---|
| **T0（免回查）** | 符合 `master/agent-orchestration.md` §2 例外条件的轻量任务 | 仅记录 `agent-skip` 及跳过理由 | 主流程 |
| **T1（指针回查，默认）** | 除 T0、T2 外的常规顾问 | 主流程注入 B1 切片（≤1200 字）；顾问回填 `base-id`、判据条目号与缺口字段 | 主流程注入 |
| **T2（实质回查）** | ① 写手角色（`chapter-draft-writer`、`code-writer`、`svg-designer`）；② 持阻断权的关键关卡（`critical-review`、`draft-review`、`check-reviewer`、`review-gate`、`gap-review`、`variable-cleaning`）；③ 结论直接进入正文净稿或投稿包的意见 | 须逐条引用判据条目号及原文段落行号，并必填缺口字段；`guard` 按模块抽检日志 | 顾问自读 + `guard` 抽检 |

**机械校验命令**（退出码 `0` 表示通过，`2` 表示阻断）：

```bash
python3 scripts/paper_master_guard.py agent-check                                   # 校验全部 32 份角色卡与 9 份底座
python3 scripts/paper_master_guard.py agent-check --module analysis                 # 校验单个模块
python3 scripts/paper_master_guard.py agent-check --workspace paper-workspace --json  # 同时抽检工作区顾问日志
```

校验内容包括：① 32 份顾问文件完整且模块分布符合预期（design 4 / lit 4 / outline 3 / analysis 8 / write 4 / check 1 / submission 2 / update 4 / mechanigraph 2）；② frontmatter 合法（`name:` 与注册表一致、含 `description:`、未声明 `tools:` 或 `model:`）；③ 指针行恰好 1 行且符合规范（T2 角色至少引用 3 条判据）；④ `base=` 与所属模块 `_reference-base.md` 的 `base-id` 一致，且所引 `C**` 条目均存在于 B2 节。

## 3. 顾问注册清单

### Design（选题与研究设计）— 4 个

| # | 标准名 | 文件路径 | 核心职责 | 回查 |
|---|---|---|---|:-:|
| 1 | `paper-design-theory-consultant` | `paper-master-4ss/modules/design/agents/theory-consultant.md` | 理论适配、机制链条构建、理论创新空间评估 | T1 |
| 2 | `paper-design-method-consultant` | `paper-master-4ss/modules/design/agents/method-consultant.md` | 可检验性、概念操作化、识别路径、资料可得性评估 | T1 |
| 3 | `paper-design-positioning-consultant` | `paper-master-4ss/modules/design/agents/positioning-consultant.md` | 领域定位、贡献可见度、期刊/论文类型适配及风险评估 | T1 |
| 4 | `paper-design-critical-review-consultant` | `paper-master-4ss/modules/design/agents/critical-review-consultant.md` | 识别致命缺陷、最强反例与不可执行环节；持有阶段放行阻断权 | T2 |

**调用时机**：须先确认 `design` 模式与研究取向，再按概念冲突、材料方法可行性、领域定位、期刊限制或反驳风险按需选派。原概念/规范/阐释/论证四项范式复核已整合至 `paper-master-4ss/modules/design/SKILL.md` 对应章节，不单独占用顾问编号。

---

### Lit（文献综述）— 4 个

| # | 标准名 | 文件路径 | 核心职责 | 回查 |
|---|---|---|---|:-:|
| 5 | `paper-lit-search-strategy-consultant` | `paper-master-4ss/modules/lit/agents/search-strategy-consultant.md` | 检索词设计、来源组合、分阶段路线、补检策略及 CNKI 权限边界 | T1 |
| 6 | `paper-lit-theory-map-consultant` | `paper-master-4ss/modules/lit/agents/theory-map-consultant.md` | 梳理理论谱系、概念关系、争议脉络与知识空白（不直接推导假设） | T1 |
| 7 | `paper-lit-evidence-screening-consultant` | `paper-master-4ss/modules/lit/agents/evidence-screening-consultant.md` | 裁决单篇纳入状态、证据等级、排除理由、待核验字段及证据相称性 | T1 |
| 8 | `paper-lit-hypothesis-bridge-consultant` | `paper-master-4ss/modules/lit/agents/hypothesis-bridge-consultant.md` | 核查「空白—理论—机制—假设」之间的逻辑桥接关系 | T2 |

**调用时机**：检索（Phase 1）-> 文献地图（Phase 2）-> 筛选与证据裁决（随 Phase 1/2 执行）-> 假设推导（Phase 3）-> 交 `write` 成稿（遵循 `master/literature-review-protocol.md`）。

---

### Outline（大纲构建）— 3 个

| # | 标准名 | 文件路径 | 核心职责 | 回查 |
|---|---|---|---|:-:|
| 9 | `paper-outline-structure-consultant` | `paper-master-4ss/modules/outline/agents/structure-consultant.md` | 判定论文结构类型（学位/期刊/实证/阐释/规范/综述）与章节深度 | T1 |
| 10 | `paper-outline-evidence-map-consultant` | `paper-master-4ss/modules/outline/agents/evidence-map-consultant.md` | 材料功能归类、证据与章节论点映射及证据等级达标检查 | T1 |
| 11 | `paper-outline-gap-review-consultant` | `paper-master-4ss/modules/outline/agents/gap-review-consultant.md` | 核查章节顺序、层级承接、材料与论证缺口；持有进入写作阻断权 | T2 |

**调用时机**：材料扫描（Phase 1）-> 大纲构建（Phase 2）-> 质量检查（Phase 3）。

---

### Analysis（数据分析）— 8 个

| # | 标准名 | 文件路径 | 核心职责 | 回查 |
|---|---|---|---|:-:|
| 12 | `paper-analysis-variable-discovery-consultant` | `paper-master-4ss/modules/analysis/agents/variable-discovery-consultant.md` | 输出字段清单、19 类变量角色映射与质量预判（`variable-discovery-pack`） | T1 |
| 13 | `paper-analysis-variable-cleaning-consultant` | `paper-master-4ss/modules/analysis/agents/variable-cleaning-consultant.md` | 复核清洗逻辑、样本筛选、缺失与异常值及变量字典；持有清洗定稿阻断权 | T2 |
| 14 | `paper-analysis-analysis-plan-consultant` | `paper-master-4ss/modules/analysis/agents/analysis-plan-consultant.md` | 从上游设计与发现包抽取分析蓝图，产出 `analysis-execution-plan` | T1 |
| 15 | `paper-analysis-identification-consultant` | `paper-master-4ss/modules/analysis/agents/identification-consultant.md` | 裁决模型选择、识别策略、固定效应与标准误设定，并开具检验清单 | T2 |
| 16 | `paper-analysis-code-writer` | `paper-master-4ss/modules/analysis/agents/code-writer.md` | 按 `task_id` 编写主回归、机制扩展或因果稳健性可执行代码草案 | T2 |
| 17 | `paper-analysis-qual-mixed-consultant` | `paper-master-4ss/modules/analysis/agents/qual-mixed-consultant.md` | 负责质性编码、主题分析、过程追踪与混合方法整合设计 | T1 |
| 18 | `paper-analysis-reporting-consultant` | `paper-master-4ss/modules/analysis/agents/reporting-consultant.md` | 裁决报告规范（CSV 宽表、`display_name`），编写导出脚本草案与 `script-index` | T2 |
| 19 | `paper-analysis-ml-causal-consultant` | `paper-master-4ss/modules/analysis/agents/ml-causal-consultant.md` | 裁决机器学习适用性、防泄漏折分、样本外指标、PDS/DML/IV 选择及 CATE 声称边界 | T2 |

**调用时机**：`variable-discovery` -> `variable-cleaning` -> 命令行清洗 -> `analysis-plan` -> （若为 `ml` 模式则增派 `ml-causal-consultant`，未过门槛则退回 `regression`）-> `identification` -> `code-writer`（按 `task_id`）-> 命令行执行与审计 -> `reporting` -> 导出。

---

### Write（论文写作）— 4 个

| # | 标准名 | 文件路径 | 核心职责 | 回查 |
|---|---|---|---|:-:|
| 20 | `paper-write-structure-writing-consultant` | `agents/structure-writing-consultant.md` | 制定写作规划与 `writing-dispatch-plan` 十列表，确定分段派活顺序 | T1 |
| 21 | `paper-write-draft-review-consultant` | `agents/draft-review-consultant.md` | 按「论证强度/材料嵌入/章节门槛」三维度复核并给出是否通过结论 | T2 |
| 22 | `paper-write-chapter-draft-writer` | `agents/chapter-draft-writer.md` | 按单个 `task_id` 起草章节或分节草稿（唯一可按任务重复派发的写手） | T2 |
| 23 | `paper-write-style-consultant` | `agents/style-consultant.md` | 全文文风统一、扫描器 `rewrite-instructions` 改写循环与正文净稿定稿 | T2 |

**调用时机**：`structure-writing` -> `chapter-draft-writer`（按 `task_id` 分段）-> `assemble_drafts.py` 拼接与主流程审阅 -> `draft-review` -> `style-consultant` -> 扫描器循环。起草者与评审者须分开派发。

---

### Check（全流程审稿检查）— 1 个

| # | 标准名 | 文件路径 | 核心职责 | 回查 |
|---|---|---|---|:-:|
| 24 | `paper-check-reviewer` | `paper-master-4ss/modules/check/agents/reviewer.md` | 执行 10 维矩阵与三组核查清单（题摘引言/正文结尾/引文技术规范），输出问题矩阵与四值结论 | T2 |

**调用时机**：完整审稿时派发 `paper-check-reviewer` 并等待结果后综合写入 `agent-synthesis-check`；仅做单项检查时须记录未覆盖维度及原因。

---

### Submission（投稿整备）— 2 个

| # | 标准名 | 文件路径 | 核心职责 | 回查 |
|---|---|---|---|:-:|
| 25 | `paper-submission-conformance-consultant` | `paper-master-4ss/modules/submission/agents/conformance-consultant.md` | 统筹检查版式清单、正文引文与文后参考文献一一对应及题录缺口 | T2 |
| 26 | `paper-submission-journal-package-consultant` | `paper-master-4ss/modules/submission/agents/journal-package-consultant.md` | 核查投稿包完整性、声明材料、cover/response letter 及退回裁决 | T1 |

**调用时机**：`conformance`（版式与引文一致性核查）-> `journal-package`（最终打包复核）。

---

### Update（知识更新包）— 4 个

| # | 标准名 | 文件路径 | 核心职责 | 回查 |
|---|---|---|---|:-:|
| 27 | `paper-update-extraction-consultant` | `paper-master-4ss/modules/update/agents/extraction-consultant.md` | 判定更新目的（六类 + `mixed` + `self-update`），抽取候选更新条目并作风险初判 | T1 |
| 28 | `paper-update-literature-enrichment-consultant` | `paper-master-4ss/modules/update/agents/literature-enrichment-consultant.md` | 为学科知识、方法协议与文献策略类候选条目补充文献证据、争议与适用边界 | T1 |
| 29 | `paper-update-target-routing-consultant` | `paper-master-4ss/modules/update/agents/target-routing-consultant.md` | 查询 `target-registry`，执行目标面四分类与 `self-update: true` 标记确认 | T1 |
| 30 | `paper-update-review-gate-consultant` | `paper-master-4ss/modules/update/agents/review-gate-consultant.md` | 评估风险等级、验证方式与跨模块影响，负责 `pending` 状态守门 | T2 |

**调用时机**：`extraction` -> `literature-enrichment`（按需）-> `target-routing` -> `review-gate`。涉及 `self-update` 时须经 `target-routing` 与 `review-gate` 双重审核。

---

### Mechanigraph（学术机制图）— 2 个

| # | 标准名 | 文件路径 | 核心职责 | 回查 |
|---|---|---|---|:-:|
| 31 | `paper-mechanigraph-topology-consultant` | `paper-master-4ss/modules/mechanigraph/agents/topology-consultant.md` | 因果实体提取、8 类经典拓扑构型匹配、画布预算与风格选项设计 | T1 |
| 32 | `paper-mechanigraph-svg-designer` | `paper-master-4ss/modules/mechanigraph/agents/svg-designer.md` | 纯矢量 SVG 几何计算、字阶排版、零灰色规范与无头渲染视觉自检 | T2 |

**调用时机**：`topology-consultant` -> 通过选项确认风格偏好 -> `svg-designer`（绘制、渲染与自检）。单图快速复刻可直接走 L0。

---

## 4. 已退役名称对照表

已退役名称仅用于查阅历史日志，不再保留执行别名；解析时一律映射至右侧现行标准名或模块段落。

| 已退役名称 | 处置方式 | 现行标准名 / 归属位置 |
|---|---|---|
| `paper-design-field-consultant` | 并入 | `paper-design-positioning-consultant` |
| `paper-design-journal-fit-consultant` | 并入 | `paper-design-positioning-consultant` |
| `paper-design-concept-analysis-consultant` | 降级 | `paper-master-4ss/modules/design/SKILL.md` §范式专属复核清单·概念 |
| `paper-design-normative-argument-consultant` | 降级 | `paper-master-4ss/modules/design/SKILL.md` §范式专属复核清单·规范 |
| `paper-design-interpretive-history-consultant` | 降级 | `paper-master-4ss/modules/design/SKILL.md` §范式专属复核清单·阐释 |
| `paper-design-argument-stress-test-consultant` | 降级 | `paper-master-4ss/modules/design/SKILL.md` §范式专属复核清单·论证 |
| `paper-lit-evidence-quality-consultant` | 并入 | `paper-lit-evidence-screening-consultant` |
| `paper-lit-screening-consultant` | 并入 | `paper-lit-evidence-screening-consultant` |
| `paper-outline-material-classification-consultant` | 并入 | `paper-outline-evidence-map-consultant` |
| `paper-outline-chapter-logic-consultant` | 并入 | `paper-outline-gap-review-consultant` |
| `paper-analysis-variable-inventory-consultant` | 并入 | `paper-analysis-variable-discovery-consultant` |
| `paper-analysis-variable-role-mapping-consultant` | 并入 | `paper-analysis-variable-discovery-consultant` |
| `paper-analysis-variable-quality-consultant` | 并入 | `paper-analysis-variable-discovery-consultant` |
| `paper-analysis-identification-model-consultant` | 并入 | `paper-analysis-identification-consultant` |
| `paper-analysis-robustness-consultant` | 并入 | `paper-analysis-identification-consultant` |
| `paper-analysis-main-regression-code-writer` | 并入 | `paper-analysis-code-writer` |
| `paper-analysis-mechanism-extension-code-writer` | 并入 | `paper-analysis-code-writer` |
| `paper-analysis-causal-robustness-code-writer` | 并入 | `paper-analysis-code-writer` |
| `paper-analysis-result-reporting-consultant` | 并入 | `paper-analysis-reporting-consultant` |
| `paper-analysis-export-reporting-code-writer` | 并入 | `paper-analysis-reporting-consultant` |
| `paper-write-argument-consultant` | 并入 | `paper-write-draft-review-consultant` |
| `paper-write-material-integration-consultant` | 并入 | `paper-write-draft-review-consultant` |
| `paper-write-chapter-standard-reviewer` | 并入 | `paper-write-draft-review-consultant` |
| `paper-check-editorial-screening-reviewer` | 并入 | `paper-check-reviewer` |
| `paper-check-argument-integrity-reviewer` | 并入 | `paper-check-reviewer` |
| `paper-check-ethics-conformance-reviewer` | 并入 | `paper-check-reviewer` |
| `paper-submission-format-check-consultant` | 并入 | `paper-submission-conformance-consultant` |
| `paper-submission-citation-integrity-consultant` | 并入 | `paper-submission-conformance-consultant` |
| `paper-update-purpose-routing-consultant` | 并入 | `paper-update-extraction-consultant` |
| `paper-update-knowledge-extraction-consultant` | 并入 | `paper-update-extraction-consultant` |

## 5. 各阶段默认调度组合

| 工作阶段 | 默认调度链路 |
|---|---|
| 选题 / 研究设计 | 先确定 `design` 模式与研究取向，再按实际风险选派；L1 默认 `paper-design-critical-review-consultant` |
| 文献综述 | `search-strategy` + `theory-map`（并行）-> `evidence-screening` -> `hypothesis-bridge` -> 交 `write`（遵循 `master/literature-review-protocol.md`） |
| 大纲构建 | `structure` -> `evidence-map` -> `gap-review` |
| 数据分析 | `variable-discovery` -> `variable-cleaning` -> 命令行清洗 -> `analysis-plan` -> （`ml` 模式下 `ml-causal-consultant`）-> `identification` -> `code-writer`（按 `task_id`）-> 执行与审计 -> `reporting` |
| 论文写作 | `structure-writing` -> `chapter-draft-writer`（按 `task_id`）-> 主流程审查 -> `draft-review` -> `style-consultant` -> 扫描改写循环 |
| 全流程审稿 | `check-reviewer` -> `agent-synthesis-check`（单项检查须注明未覆盖维度） |
| 投稿整备 | `conformance` -> `journal-package` |
| 知识更新 | `extraction` -> `literature-enrichment`（按需）-> `target-routing` -> `review-gate`（`self-update` 须双重审核） |
| 学术机制图 | `topology-consultant` -> 风格选项确认 -> `svg-designer` |

若需引入另一模型提供独立对照意见，不新增顾问文件，直接通过 `agy_run` 调用并将结论以「外部对照」写入 `agent-synthesis`。

## 6. 路径与文件结构约定

所有路径均相对于 `paper-master-4ss/` 根目录解析。每个顾问文件保持统一结构：YAML frontmatter（`name` / `description` / 可选 `capabilities`）+ 职责说明 + 单行 `参考库回查:` 指针 + `<!-- block: … -->` 公共块占位符 + 输入材料 + 审阅重点 + 输出格式。公共块正文统一维护于 `references/agent-prompt-blocks.md`。
