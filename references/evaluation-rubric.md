# Evaluation Rubric

`paper-master-4ss` 使用 100 分 Rubric 评估论文项目当前状态。Rubric 只提供质量诊断，不替代研究者判断；除 `guard_before_finish` 的索引更新检查外，评分本身不阻断交付。

## 1. 总分结构

| 项目 | 满分 | 核心证据 |
|---|---:|---|
| 项目治理 | 10 | `project-state.md`、`handoff-status.md`、`input-registry.md`、`paper-roadmap.md`、流程日志 |
| 设计 | 15 | `frame-report-*.md`、`storm-report-*.md`、`design-report-*.md`、`full-report-*.md`、取向元数据与顾问综合 |
| 文献 | 15 | `paper-registry.csv`、`papers/`、`fulltext/`、`review-evidence.csv`、`review-outline.md`、`review-gaps.md` 与文献地图/空白/理论对话产物 |
| 大纲 | 10 | `paper-outline.md`、`paragraph-blueprint.md`、`evidence-map.md`、`gap-report.md` |
| 分析 | 25 | 仅当最新设计报告明确 `analysis_required: true` 时：分析计划、变量字典、真实执行 run-log、`script-index.md`、CSV 表格、图形、guard 审计 |
| 写作 | 15 | `05-writing/literature-review.md`（综述净稿）、`manuscript.md`、`manuscript-[slug]-[date].md`、章节草稿、正文格式合规检查、扫描报告、修订记录、顾问综合 |
| 投稿 | 10 | `submission.docx`、格式检查、引用缺口、投稿清单、cover/response letter |

## 2. 两个分数

- `maturity_score`：全流程成熟度，按 100 分总权重计算。早期项目会自然较低，用于判断距离完整论文包还有多远。
- `stage_score`：当前已启动模块归一化分数。用于判断已经开始的阶段是否扎实，不因尚未进入投稿阶段而过度扣分。

## 3. 每项记录格式

每个 Rubric 项必须记录：

| 字段 | 含义 |
|---|---|
| `score` | 当前得分 |
| `max` | 本项满分 |
| `evidence` | 支撑评分的文件、日志或审计结果 |
| `failure_attribution` | 未满分时的失败归因 |
| `fix_next` | 下一步修复动作 |

失败归因固定为六类：

- `提示`：任务说明、目标或验收标准不清。
- `工具`：工具不可用、调用方式错误或导出失败。
- `知识`：理论、文献、方法或期刊规范知识不足。
- `流程`：阶段交接、索引、日志或顾问派发缺失。
- `数据`：数据、变量、文本、访谈材料或证据不足。
- `执行环境`：Stata/R/Python、依赖、路径、权限、stdout/stderr 或 CLI 执行失败。

## 4. 运行方式

```bash
python3 scripts/paper_master_guard.py score-project --workspace paper-workspace --json
```

输出：

- `paper-workspace/_index/quality-score.md`
- `paper-workspace/_index/quality-score.json`

## 5. 使用规则

- 每次实质性模块执行后，更新 `_index/project-state.md` 与 `_index/handoff-status.md`，再运行 `score-project`。
- 最终回复必须说明质量分文件位置、当前 `stage_score`、`maturity_score` 和主要未通过项。
- 最新设计报告明确 `analysis_required: false` 时，分析项不计入 `maturity_score` 和 `stage_score`；未选路径不扣分。
- 分析模块的统计结论必须同时满足：run-log 无失败信号、输出文件存在、`script-index.md` 可追溯、guard 审计无阻断性问题。
- 评分低于满分时，优先按 `fix_next` 修复；不要只修改提示词而不修复脚本、日志、数据或流程证据。
