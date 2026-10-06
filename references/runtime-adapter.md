# Runtime Adapter

本文档定义 `paper-master-4ss` 的宿主无关能力层。业务协议只引用本文档的能力名，不引用任何宿主的工具名。当前会话实际可用的工具由 §5 的运行时探测得出，已知宿主的样例映射见 `references/agent-software-adapters.md`——那份文档是**样例参考**，不是宿主名单，也不约束适配方式。

## 1. 通用能力名

| 能力名 | 用途 | 缺失时处理 |
|---|---|---|
| `read_file` | 读取 `SKILL.md`、模块协议、用户材料和产物 | 停止当前步骤，请用户提供可读路径或权限 |
| `search_text` | 在 skill 包、项目目录和材料中全文检索 | 可退化为宿主可用搜索或 shell `rg`；仍不可用时记录能力缺失 |
| `write_file` | 写入 `paper-workspace/` 产物、日志、索引和项目规则 | 未获写权限时停止写入型任务 |
| `run_shell` | 执行 Python/R/Stata/pandoc/依赖检查等命令 | 只能给出待执行命令，不得声称已运行 |
| `web_search` | 在线检索关键词、核心文献和公开资料 | 记录 `web_search=能力缺失`，不得伪造搜索结果 |
| `web_fetch` | 打开网页、摘要页、API 响应或公开全文 | 无法抓取时把文献列为待核验 |
| `browser_control` | 驱动可见浏览器完成 CNKI 等必须网页操纵的来源：导航、页内脚本、点击填写、就绪等待、截图 | 记录 `浏览器控制不可用` 并停止该来源阶段（不得用 `web_search`/`web_fetch` 或顾问意见替代 CNKI 完成状态）；后端与适配见 lit 模块 `references/pi-chrome-browser.md` 与 `references/cnki-kns8s-closed-loop.md` |
| `ask_user` | 结构化询问、确认方向、阻断确认和长期选择固化 | 无交互能力时采用最小可行默认，并记录为推断而非用户确认 |
| `spawn_agent` | 派发一个 canonical agent 顾问或 writer | 无独立 agent 能力时由主流程按角色顺序复核 |
| `parallel_review` | 多 canonical agent 并行复核或多 writer 并行草拟 | 不可并行时记录 `sequential-review` |
| `guard_after_command` | 分析命令后审计 run-log、stdout/stderr 和输出存在性 | 显式运行 `paper_master_guard.py post-bash` |
| `guard_before_finish` | 交付前检查索引是否随最新产物更新 | 显式运行 `paper_master_guard.py stop-check` |
| `project_memory` | 持久化稳定项目规则和用户选择 | 无宿主项目记忆文件时写入 `paper-workspace/_index/project-rules.md` |

## 1.5 Frontmatter 契约

本包的 `SKILL.md` 与 `modules/*/agents/*.md` 只使用宿主无关的元数据键：

```yaml
---
name: <canonical name>          # 必填；宿主与脚本按此名寻址
description: <一句话职责>        # 必填；导出脚本按 ^description: 读取，不得改格式
capabilities: read_file, search_text   # 可选；该文件需要的通用能力子集
invocable: true                 # 可选；允许用户直接调用
args_hint: "[主题] [可选: 期刊]"  # 可选；参数提示
---
```

规则：

- 这些键**只是元数据**，不承载执行权限，任何宿主都必须按「不认识即忽略」处理，不得因未知键报错或拒绝加载。
- 不写 `capabilities:` 表示**不声明能力限制**（等价于「该文件可用当前宿主提供的全部能力」），不表示「无能力」。
- 不得在本包内写宿主专属的 `tools:`、`allowed-tools:`、`hooks:`、`model:`、`user-invocable:`、`argument-hint:`。模型选择由宿主默认策略决定，不逐文件声明。
- 若某宿主需要按自己的能力名重新声明这些信息（例如需要 per-skill 工具限制），由**该宿主的适配层**在包外完成；本包不为此保留宿主专属字段。

## 2. 执行规则

- 各类宿主都必须先判断自身能力，再执行模块流程；不得把某宿主专属工具名当作通用要求。
- frontmatter 的 `capabilities:` 是宿主无关的声明，执行时必须通过本适配层映射到当前宿主实际提供的工具；声明之外的能力也不得凭空声称可用。
- 缺少 `web_search`、`web_fetch`、`browser_control`、`spawn_agent`、`parallel_review` 或自动 guard 时，必须在过程日志、`agent-brief.md`、`agent-synthesis` 或最终回复中记录能力状态和回退方式。
- 能力缺失不得改变真实性边界：不能伪造网页检索、CNKI/Scholar 页面操纵、脚本执行、统计结果、guard 审计或 agent 意见。

## 3. Guard 调用

自动 Hook 不是必需接口；以下命令是各宿主共同的手动 guard 接口：

```bash
python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace
python3 scripts/paper_master_guard.py stop-check --workspace paper-workspace
python3 scripts/paper_master_guard.py score-project --workspace paper-workspace --json
```

执行分析命令后若宿主没有自动 `guard_after_command`，必须显式运行第一条；模块交付前若宿主没有自动 `guard_before_finish`，必须显式运行第二条；每次实质性模块执行后仍必须运行评分命令。默认退出码：post-bash 通过为 0（加 `--strict` 时审计问题为 2），stop-check 阻断为 2。

### 3.1 机制层自注册（可选）

宿主有 hook 接口时，可在包外或由用户显式把同一 guard 注册进该宿主的 hook 配置：

```bash
python3 scripts/register_host_hooks.py --check                 # 只读查询
python3 scripts/register_host_hooks.py                        # 注册（auto 判定宿主）
python3 scripts/register_host_hooks.py --host zcode           # 指定宿主
python3 scripts/register_host_hooks.py --print --host <name>  # 只打印片段，不写文件
python3 scripts/register_host_hooks.py --remove                # 撤销
```

脚本只在有明确证据（宿主专属环境变量或项目内宿主配置目录）时写入，否则不修改任何文件；注册幂等、写前备份、只追加不覆盖。已知宿主的 hook 存放位置与事件形状见 `references/hooks-and-evaluation.md`。宿主已有自己的 hook 机制（插件 preset、平台级配置）时优先用宿主的，无需运行本脚本。

## 4. Project Memory

`project_memory` 只保存稳定选择和死规则，不保存临时任务、原始隐私材料、token、cookie、日志全文或阶段待办。

优先级：

1. 当前宿主已有的项目级规则文件。
2. 工作区中任一项目规则文件（如 `AGENTS.md`、`GEMINI.md`、`.omp/AGENTS.md` 或该宿主约定的其他文件名）内的 paper-master 标记块。具体宿主用哪个文件名由该宿主的自动注入机制决定，本包不预定名单。
3. `paper-workspace/_index/project-rules.md`。

读取时以上述顺序合并；本次用户明确指令优先于历史项目规则。写入时只更新当前宿主可安全维护的 paper-master 标记块或 `project-rules.md`，不得写入 skill 包目录。标记块与写作纪律见 `references/project-rules-writing-layer.md`。

## 5. 能力探测程序

会话启动（或任务首次进入本包）时执行一次，结果作为本次会话后续步骤的唯一能力依据：

1. **列能力**：列出当前会话实际可用的工具名（宿主的原生工具清单），不以本包任何文档中的宿主机名为准。
2. **映射**：把工具名按语义映射到 §1 的 13 个能力名。映射优先用已知样例（`references/agent-software-adapters.md`），无样例时按用途判断；无法判断的能力标 `unknown`。
3. **落盘**：把结果写入 `paper-workspace/_index/runtime-capabilities.md`，固定表格：

   | 能力 | 可用性（yes/no/unknown） | 宿主工具 | 回退方式 |
   |---|---|---|---|

   同时列出缺失能力清单与探测依据（宿主线索、判断理由）。
4. **复用**：同一会话内的后续步骤只读该文件，不重复探测；宿主能力或会话发生变化时重跑并覆盖（幂等）。
5. **回退**：按 §1 的「缺失时处理」执行；`write_file` 缺失时只做只读任务；hook 自动触发缺失时显式运行 §3 命令；`browser_control` 缺失时停止该来源阶段，不得用 `web_search`/`web_fetch` 冒充完成状态。
6. **记录**：能力缺失与回退方式必须出现在过程日志或最终回复中，不得静默降级。
