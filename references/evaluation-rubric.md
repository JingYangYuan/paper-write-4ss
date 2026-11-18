# Evaluation Rubric（项目质量评分规范）

`paper-master-4ss` 采用 100 分制 Rubric 对论文项目当前状态进行客观评估。评分仅用于质量诊断与缺口定位，不替代研究者学术判断；除 `stop-check` 对索引同步的校验外，分数本身不阻断任务交付。

## 1. 评分权重与核心证据

| 评估维度 | 满分 | 核查证据 |
|---|---:|---|
| 项目治理 | 10 | `_index/project-state.md`、`_index/handoff-status.md`、`_index/input-registry.md`、`_index/paper-roadmap.md`、`_logs/` |
| 研究设计 | 15 | `01-design/` 下 `frame-report-*.md`、`storm-report-*.md`、`design-report-*.md`、`full-report-*.md`、取向元数据与顾问综合 |
| 文献综述 | 15 | `02-literature/` 下 `paper-registry.csv`、`papers/`、`fulltext/`、`review-evidence.csv`、`review-outline.md`、`review-gaps.md` 及文献地图/空白/理论对话产物 |
| 论文大纲 | 10 | `03-outline/` 下 `paper-outline.md`、`paragraph-blueprint.md`、`evidence-map.md`、`gap-report.md` |
| 数据分析 | 25 | 仅当最新设计报告明确 `analysis_required: true` 时计分：分析计划、变量字典、`run-log`、`script-index.md`、CSV 表格、图形及 guard 审计 |
| 论文写作 | 15 | `05-writing/` 下 `literature-review.md`、`manuscript*.md`、章节草稿、格式检查、扫描报告、修订记录、`reviews/paper-check-report-*.md` 及 `write`/`check` 顾问综合（同类综合证据不重复计分） |
| 投稿整备 | 10 | `06-submission/` 下 `submission.docx`、格式检查、引文缺口报告、投稿清单及 cover/response letter |

## 2. 双口径分值说明

- **`maturity_score`（全流程成熟度）**：按 100 分总权重计算，反映当前产物距完整可投稿论文包的整体完成度（项目早期分值较低属正常情况）。
- **`stage_score`（当前阶段得分）**：仅对已启动模块按权重归一化计算，用于评估已推进阶段的扎实程度，不因后续阶段尚未开展而扣分。

## 3. 单项记录字段与失败归因

每个维度记录以下五个字段：

| 字段 | 说明 |
|---|---|
| `score` | 当前实际得分 |
| `max` | 该维度满分 |
| `evidence` | 支撑得分的产物文件、日志或审计记录路径 |
| `failure_attribution` | 未获满分时的失败归因分类 |
| `fix_next` | 下一步具体修复动作 |

`failure_attribution` 固定分为六类：
- `提示`：任务目标、指令或验收标准不明确；
- `工具`：工具不可用、调用方式错误或文件导出失败；
- `知识`：理论框架、文献、方法论或期刊规范依据不足；
- `流程`：阶段交接、索引更新、过程日志或顾问调度缺失；
- `数据`：实证数据、变量、文本、访谈材料或原文证据不足；
- `执行环境`：Stata / R / Python 运行时、依赖包、路径权限、stdout/stderr 或命令行执行失败。

## 4. 执行命令与输出

```bash
python3 scripts/paper_master_guard.py score-project --workspace paper-workspace --json
```

输出文件：
- `paper-workspace/_index/quality-score.md`
- `paper-workspace/_index/quality-score.json`

## 5. 使用规范

- 每次实质性执行模块后，先同步 `_index/project-state.md` 与 `_index/handoff-status.md`，再执行 `score-project`。
- 最终回复须报告质量分文件路径、当前 `stage_score`、`maturity_score` 及主要未通过项。
- 若最新设计报告明确 `analysis_required: false`，数据分析维度自动从 `maturity_score` 与 `stage_score` 分母中剔除，不予扣分。
- 数据分析维度的统计结论须同时满足：run-log 无报错信号、输出文件存在、`script-index.md` 可追溯、guard 审计无阻断问题。
- 出现扣分项时，应优先依据 `fix_next` 补齐对应产物、日志或脚本执行证据。
