# Routing Matrix（模块路由表）

本文件用于根据任务目标选择唯一主模块。每次仅加载一个主模块；涉及跨模块协同时，按需增派相邻模块的顾问进行风险预判（详见 `master/agent-orchestration.md`）。

## 1. 任务与模块对照表

| 任务需求 | 目标模块 | 入口与前置条件 |
|---|---|---|
| 选题定位、寻找理论锚点、概念/规范/阐释类理论设计、研究问题界定、实证或混合研究设计、预分析计划（PAP） | `design` | `paper-master-4ss/modules/design/SKILL.md`。须先确认模式（FRAME / STORM / DESIGN / FULL）与研究取向，不预设理论或实证路径 |
| 文献检索、文献综述撰写、文献地图、空白识别、假设推导、CNKI / Scholar 检索 | `lit` | `paper-master-4ss/modules/lit/SKILL.md`。综述正文须按 `master/literature-review-protocol.md` 交由 `write` 成稿，写入 `05-writing/literature-review.md` |
| 将已有素材转化为论文大纲、段落级写作蓝图、证据映射与缺口报告 | `outline` | `paper-master-4ss/modules/outline/SKILL.md` |
| 数据清洗、回归分析、因果识别、机器学习与因果 ML、质性编码、混合方法 | `analysis` | `paper-master-4ss/modules/analysis/SKILL.md`。方法范围见 §2 |
| 正文起草、章节改写、语言润色、反模式扫描、复杂度诊断 | `write` | `SKILL.md` |
| 全文审稿、编辑首筛、拒稿风险诊断、投稿前综合复核 | `check` | `paper-master-4ss/modules/check/SKILL.md` |
| 导出 Word、规范引文体例、套用期刊模板、组装投稿包、撰写投稿信/回复信 | `submission` | `paper-master-4ss/modules/submission/SKILL.md` |
| 从专著、论文、笔记、方法手册或工具日志中提取候选知识并生成更新包 | `update` | `paper-master-4ss/modules/update/SKILL.md` |
| 绘制理论机制图、分析框架图、演进模型、政策网络、因果图、纯矢量 SVG 及原图复刻 | `mechanigraph` | `paper-master-4ss/modules/mechanigraph/SKILL.md`。制图前通过选项确认风格偏好，制图后须执行无头 Chrome 渲染自检 |
| 阶段不清、整理项目状态、规划下一步或串联全流程 | `master`（总控） | 先读取 `_index/paper-roadmap.md`、`project-state.md`、`handoff-status.md`，再进入 `design` 确认模式与取向；不得未经确认直接跳转至 `analysis` |

注：`mechanismgraph` 与 `mechanigraph` 均指向 `mechanigraph` 模块。

## 2. `analysis` 模块方法范围

- **基础回归族**：描述统计、多重共线性（VIF）、异方差检验（BP）、自相关（DW）、模型设定检验（Hausman）、弱工具变量与过度识别检验；基准回归；二值与计数模型（Logit/Probit/Poisson/Tobit）、样本选择模型（Heckman）；中介效应与调节效应；分位数回归；Bootstrap 与稳健性检验。
- **面板与时间序列族**：面板固定效应与随机效应（FE/RE）、动态面板（GMM）；时间序列（ARMA/VAR/VECM）；空间计量（SAR/SDM/SEM）。
- **因果识别族**：工具变量与两阶段最小二乘（IV/2SLS/GMM）；双重差分与事件研究、多期 DID（含交错处理）；断点回归（RDD，含局部平滑性、安慰剂与带宽敏感性检验）；匹配与加权（PSM/CEM/IPW）；合成控制（SCM/SDID）。
- **质性族**：质性编码、主题分析、过程追踪、混合方法整合。
- **机器学习与因果 ML 族**：高维正则化（Lasso/Ridge/Elastic Net、后双选择 PDS）、树与集成模型（随机森林、梯度提升、XGBoost/LightGBM）、超参调优与交叉验证、样本外评估（RMSE/MAE/LogLoss/AUC）、聚类与降维（K-Means、PCA、因子分析）；因果 ML（DML 部分线性模型、IV 正则化选择）；异质性政策效应（因果森林、GATES、BLP）与重叠诊断。仅处理表格数据，不涵盖深度学习、图像及文本大模型训练。

<details>
<summary>方法全名对照表（Stata / R / Python 均提供完整可执行模板）</summary>

| 方法族 | 包含方法 |
|---|---|
| 基础回归族 | 描述统计（describe/sum/tabulate）、VIF、Breusch-Pagan、Durbin-Watson、Hausman、弱 IV 与过度识别检验、OLS/Logit/Probit/Poisson/Tobit/Heckman、中介效应、调节效应、分位数回归、Bootstrap、稳健性检验 |
| 面板与时间序列族 | 面板 FE/RE、动态面板 GMM（差分/系统）、ARMA、VAR、VECM、SAR/SDM/SEM 空间计量 |
| 因果识别族 | IV/2SLS/GMM、DID、事件研究、多期 DID（交错处理）、RDD（局部平滑性/安慰剂/带宽）、PSM/CEM/IPW、SCM/SDID |
| 质性族 | 质性编码、主题分析、过程追踪、混合方法（联合展示 joint display） |
| 机器学习与因果 ML 族 | Lasso/Ridge/Elastic Net、后双选择（PDS）、随机森林、梯度提升、XGBoost/LightGBM、K 折与重复交叉验证、样本外评估（RMSE/MAE/LogLoss/AUC）、K-Means、PCA、因子分析、DML 部分线性模型、IV 正则化选择、因果森林、GATES、BLP、重叠诊断 |

</details>

## 3. 易混淆场景边界

- **过程流程图 vs. 论文机制图**：过程报告中的逻辑链与流程图使用 Mermaid（见 `master/output-protocol.md`）；需进入论文正文的纯矢量机制图、因果图与分析框架图须交由 `mechanigraph` 生成 SVG/PNG。
- **语言润色 vs. 全文审稿**：仅修改语言或扫描表达问题路由至 `write`；涉及全文审稿、编辑首筛、拒稿风险与综合复核路由至 `check`。
- **内容审稿 vs. 投稿排版**：论证与证据问题由 `check` 审查并退回修改；Word 导出、引文体例、模板核对与投稿材料组装由 `submission` 处理。
- **项目成熟度评分**：由总控脚本 `paper_master_guard.py score-project` 执行，不属于独立业务模块。

## 4. 路由优先级

1. **显式指定优先**：用户明确指定目标模块时，直接按指定模块执行。
2. **基于材料与状态推断**：用户仅提供材料而未指明任务时，先登记输入至 `input-registry.md`，再读取 `project-state.md` 判断当前阶段。
3. **推进既有项目**：用户要求继续推进或整理项目状态时，读取 `_index/paper-roadmap.md`、`project-state.md` 与 `handoff-status.md`；若缺失 `paper-roadmap.md`，按 `master/user-journey.md` 依据现有产物补建。
4. **缺失关键信息时询问**：仅当研究主题或任务目标无法从项目状态推断时，向用户补充询问。

## 5. 顾问派发判定准则

输入路径登记、已有产物摘要、依赖检查、单文件格式校验及明确的单点转换操作不派发顾问（记录 `agent-skip`）。

其余任务依据决策风险、材料复杂度与交接跨度选择最少必要顾问，并在日志或回复中记录选派理由与未选角色的原因。不得仅因研究类型或模块名称套用固定人数。

## 6. 跨模块默认协同路径

- **全流程规划**：由 `design` 主导，先锁定模式与研究取向；仅当设计报告注明 `analysis_required: true` 时追加 `analysis` 识别顾问，其余路径依次进入 `lit`、`outline`、`write`。
- **文献到大纲**：由 `lit` 主导，视需要追加 `outline` 结构顾问与证据映射顾问预判结构承接能力。
- **文献综述成稿**：由 `lit` 完成检索、证据表与论证蓝图后，按 `master/literature-review-protocol.md` 交 `write` 的结构顾问与章节写手成稿，输出至 `05-writing/literature-review.md`。
- **分析到写作**：由 `analysis` 主导，视需要追加 `write` 审稿顾问预判结果声称边界。
- **写作—审稿—投稿**：`write` 交付正文净稿、扫描报告、source map、证据边界与目标期刊信息；`check` 执行综合复核并将实质问题精确退回对应模块；`check` 通过后方由 `submission` 执行 Word 导出与投稿整备。
- **机制图协同**：`design` 确定理论锚点后可调用 `mechanigraph` 绘制理论分析框架图；`analysis` 确定因果或中介路径后可调用 `mechanigraph` 绘制实证机制图；产物统一存放在 `paper-workspace/figures/`，供 `write` 在正文中引用。
