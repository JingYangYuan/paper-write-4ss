# Workspace Contract（工作区产物约定）

`paper-master-4ss` 统一输出位置，不强制输入位置。用户材料可位于任意路径，仅登记路径后直接引用。

除论文正文净稿（`manuscript*.md`、`revisions/styled*.md`、`literature-review.md`）外，各阶段核心报告默认使用中文 Markdown；涉及机制链、因果链、阶段流程、模块交接、理论嫁接、假设推导、写作派活、顾问调度或退回链路时，按 `master/output-protocol.md` 附 Mermaid 图；普通证据表、模型结果与引用清单使用 Markdown 表格或既有数据格式。正文净稿仅允许标题层级和自然段。用户层路径图按 `master/user-journey.md` 维护。

## 1. 目录结构

```text
paper-workspace/
├── 00-meta/
├── 01-design/
├── 02-literature/
├── 03-outline/
├── 04-analysis/
├── 05-writing/
├── 06-submission/
├── 07-update/
├── figures/
├── _logs/
│   ├── agents/
│   └── hook-audit/
└── _index/
```

## 2. 各阶段输出路径与核心产物

| 阶段 | 输出目录 | 核心产物 |
|---|---|---|
| `design` | `paper-workspace/01-design/` | `frame-report-*.md`、`storm-report-*.md`、`design-report-*.md`、`full-report-*.md`；设计报告须写明 `research_orientation` 与 `analysis_required` |
| `lit` | `paper-workspace/02-literature/` | `papers/`、`fulltext/`、唯一 `paper-registry.csv`、`review-evidence.csv`、`review-outline.md`、`review-gaps.md`、`literature-map.md`、`gap-map.md`、`hypothesis-derivation.md`（实证路径）；`plans/download-plan.tsv` 为按注册表即时生成的临时下载计划 |
| `outline` | `paper-workspace/03-outline/` | `paper-outline.md`、`paragraph-blueprint.md`、`evidence-map.md`、`gap-report.md` |
| `analysis` | `paper-workspace/04-analysis/` | `analysis-plan.md`、`variable-dictionary.csv`、`tables/`、`figures/`、`reports/results-brief.md` |
| `write` | `paper-workspace/05-writing/` | `literature-review.md`（独立综述正文）、`manuscript.md`、`manuscript-[slug]-[date].md`、`plans/`、`drafts/`、`assembly/`、`reviews/`（含 `paper-check-report-*`、`paper-check-matrix-*`、`paper-check-revision-list-*`）、`revisions/styled-[slug]-[date].md`、`scans/scan-report.md`；`check` 顾问综合写入 `_logs/agents/check-[YYYY-MM-DD]/agent-synthesis-check-[YYYY-MM-DD].md` |
| `submission` | `paper-workspace/06-submission/` | `submission.docx`、`format-check-report.md`、`citation-normalized.md`、`citation-gap-report.md`、`submission-checklist.md`、`cover-letter.md`、`response-letter.md` |
| `update` | `paper-workspace/07-update/` | `update-report.md`、`review-checklist.md`、`proposed-diffs/`、`evidence/`、`merge-instructions.md` |
| `mechanigraph` | `paper-workspace/figures/` | `mechanism-*.svg`（纯矢量主图）、`mechanism-*.png`（无头渲染预览图）、`mechanism-metadata-*.json`（构型与自检元数据） |

## 3. 日志与索引约定

- **流程与顾问日志**：流程日志写入 `paper-workspace/_logs/`；顾问意见与综合报告写入 `paper-workspace/_logs/agents/[module]-[YYYY-MM-DD]/`。
- **审计日志**：Guard 审计写入 `paper-workspace/_logs/hook-audit/`；分析命令审计文件命名为 `analysis-log-audit-[YYYY-MM-DD].md`。
- **索引文件**（均位于 `paper-workspace/_index/`）：
  - `project-state.md`：项目当前状态与关键风险；
  - `input-registry.md`：外部输入材料路径登记；
  - `handoff-status.md`：阶段交接状态与遗留风险；
  - `paper-roadmap.md`：面向用户的路径图、当前位置、下一步建议、暂缓事项与退回提示；
  - `quality-score.md` 与 `quality-score.json`：阶段得分、全流程成熟度、失败归因与修复建议；
  - `runtime-capabilities.md`：当前会话能力探测结果与工具映射；
  - `project-rules.md`：项目根无适用规则文件时的项目规则存储位置。

## 4. 输入登记模板（`input-registry.md`）

首次登记时将下表模板复制至 `paper-workspace/_index/input-registry.md` 并持续追加：

| ID | Path | Type | Source | Intended Use | Linked Module | Status | Notes |
|---|---|---|---|---|---|---|---|
| input-001 | `/absolute/or/user/provided/path` | pdf/csv/dta/docx/md/txt/folder/url | user/current-dir/web | literature/analysis/outline/write | lit/analysis/outline/write/design | registered/used/excluded | notes |

规则：
- 相对路径统一按用户发起请求时的当前工作目录解析。
- 所有下游产物须引用此处登记的 `Path` 或原始 URL。
