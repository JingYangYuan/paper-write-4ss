# Routing Matrix

先判断用户目标，确定一个主模块，再按 `master/agent-orchestration.md` 决定是否追加相邻模块顾问。不要把全部业务模块一次性读入上下文；跨模块任务先加载主模块，再加载必要顾问文件做风险预判。

| 用户意图 | 内部模块 | 入口 |
|---|---|---|
| 选题、理论锚点、概念/规范/阐释理论设计、研究问题、实证或混合研究设计、PAP | design | `paper-master-4ss/modules/design/SKILL.md`（先确认 FRAME/STORM/DESIGN/FULL 与研究取向，不预设理论或实证） |
| 文献检索、文献综述、文献地图、研究空白、假设推导、CNKI/Scholar | lit | `paper-master-4ss/modules/lit/SKILL.md`（综述正文按 `master/literature-review-protocol.md` 交接 write，唯一落点 `05-writing/literature-review.md`） |
| 已有材料转论文结构、大纲、证据映射、缺口报告 | outline | `paper-master-4ss/modules/outline/SKILL.md` |
| 数据清洗、描述统计、回归诊断(VIF/BP/DW/Hausman/弱IV/过度识别)、基准回归、Logit/Probit/Poisson/Tobit/Heckman、面板FE/RE/动态GMM、IV/2SLS/GMM、DID/事件研究/多期DID(交错处理)、RDD(局部平滑性/安慰剂/带宽)、PSM/CEM/IPW、SCM/SDID、分位数、中介/调节、时间序列(ARMA/VAR/VECM)、空间计量(SAR/SDM/SEM)、Bootstrap/稳健性、质性编码、混合方法。三语言模板(Stata/R/Python)自含完整可执行代码。 | analysis | `paper-master-4ss/modules/analysis/SKILL.md` |
| 正文写作、章节改写、润色、语言扫描、复杂度诊断 | write | `SKILL.md` |
| 全文审稿、编辑首筛、内容与形式联合检查、拒稿风险诊断、投稿前综合自检 | check | `paper-master-4ss/modules/check/SKILL.md` |
| 投稿前的 Word、引文体例、模板、投稿包、cover letter、response letter | submission | `paper-master-4ss/modules/submission/SKILL.md` |
| 更新知识边界、补充理论框架、补充写作范式、补充方法/流程协议、补充工具模板、从书籍/论文/笔记/方法手册/工具日志吸收知识，或为 update 模块自身生成待审核更新包 | update | `paper-master-4ss/modules/update/SKILL.md` |
| 不知道下一步、整理项目状态、串联全流程 | master | 先读 `_index/paper-roadmap.md`、`_index/project-state.md` 与 `_index/handoff-status.md`，再由 design 确认模式和研究取向；不得默认进入 analysis |

意图消歧：仅语言润色/扫描 → write；全文审稿/编辑首筛/拒稿风险/投稿前综合自检 → check；仅 Word/引文体例/模板/投稿包 → submission；项目成熟度评分 → master guard。

## 优先级

1. 用户明确指定模块时，按指定模块执行。
2. 用户给出材料但目标不明时，先登记输入，再扫描 `project-state.md` 判断阶段。
3. 用户说“继续”“下一步”“整理一下”时，先读 `_index/paper-roadmap.md`、`_index/project-state.md` 与 `_index/handoff-status.md`；若路线图缺失，则按 `master/user-journey.md` 根据现有索引和产物补建。
4. 如果缺少研究主题或任务目标，先简短询问；如果可从项目状态推断，则不问。

## 顾问派发

路径登记、已有产物摘要、依赖检查、单文件格式检查和明确的单点转换任务可不派发 agent，其他任务也应按当前决策风险选择最少必要角色；必须在日志或最终回复记录 `agent-skip` 或“选择/未选择角色”的理由。全流程、材料复杂或阶段不清时可增加交叉复核，但不得只因理论/实证标签或模块名称自动派发。

## 跨模块默认链路

- 全流程规划：design 主导，先完成模式与研究取向确认；仅在蓝图的 `analysis_required: true` 时再追加 analysis/identification-model，其他路径进入 lit、outline 与 write。
- 文献到大纲：lit 主导，追加 outline/structure 和 outline/evidence-map 预判结构承接。
- 综述成稿：lit 主导，完成证据表与论证蓝图后按 `master/literature-review-protocol.md` 交接 write/structure-writing 与 write/chapter-draft-writer 成稿，正文落 `05-writing/literature-review.md`。
- 分析到写作：analysis 主导，追加 write/argument 和 write/material-integration 预判结果声称边界。
- 写作到审稿到投稿：write 交出正文净稿、扫描报告、source map、证据边界和目标期刊信息 → check 做综合复核并将实质问题精确回流 design/lit/outline/analysis/write → 通过质量门后 submission 处理Word、体例与投稿包。
