# Runtime Adapter（运行环境能力适配规范）

本规范定义 `paper-master-4ss` 与运行环境之间的通用能力接口。业务流程仅以通用能力名描述操作，执行前将通用能力映射至当前运行环境的真实工具；能力缺失时按对应回退方案处理并如实记录，不得虚构执行结果。

除本文档及明确需要说明映射关系的场景（采用「动作（`capability_id`）」首次标注）外，业务文本统一使用中文动作名称。

## 1. 通用能力定义与缺失回退

| 能力标识 | 对应动作 | 缺失时的回退方案 |
|---|---|---|
| `read_file`（读文件） | 读取 `SKILL.md`、模块协议、用户材料及产物 | 中止当前步骤，请用户提供可读路径或读取权限，不得凭记忆补全内容 |
| `search_text`（全文检索） | 在技能包、项目目录或材料中检索关键词与条款 | 改用环境自带检索工具或 shell `rg`；仍不可用时记录能力缺失并人工逐份读取 |
| `write_file`（写文件） | 将产物、日志、索引与项目规则写入 `paper-workspace/` | 仅执行只读分析任务，不得声称已完成文件写入 |
| `run_shell`（执行命令） | 运行 Python / R / Stata / pandoc 及依赖检查命令 | 仅输出待执行命令并标注未运行，不得声称已执行 |
| `web_search`（联网检索） | 线上检索关键词、核心文献与公开资料 | 记录 `web_search=能力缺失`，不得虚构检索结果 |
| `web_fetch`（抓取网页） | 读取网页正文、摘要页、API 响应或公开全文 | 将目标文献标记为待核验，不得记为已读 |
| `browser_control`（可见浏览器控制） | 驱动真实可见浏览器进行点击、输入、等待与截图（主要用于 CNKI 取全文及 Turnstile/CDP 兜底） | 记录 `浏览器控制不可用` 并停止该来源阶段；不得用联网检索、网页抓取或顾问意见替代 CNKI 取全文。统一后端为 `ego-browser`（详见 `paper-master-4ss/modules/lit/references/browser.md`、`paper-master-4ss/modules/lit/references/cnki.md`） |
| `ask_user`（选项式提问） | 确认研究方向、处理阻断状态或固化长期选择 | 在无交互通道时采用最小可行默认方案，并在日志中标注为推断选择而非用户确认 |
| `spawn_agent`（单子代理派发） | 派发单个顾问或写手子任务 | 由主流程按同一角色清单依次执行顺序复核 |
| `parallel_review`（并行复核） | 多名顾问并行复核或多写手并行起草 | 改用顺序复核，并在记录中标注 `sequential-review` |
| `multi_seat_debate`（多席位辩论，可选） | 同一顾问角色开启多个席位互相质询 | 按 `sequential-review` 处理，不单独为此增加环境探测步骤 |
| `guard_after_command`（命令后审计） | 核对分析命令后的 run-log、stdout/stderr、报错与输出文件 | 手动执行 `paper_master_guard.py post-bash`（见 §3） |
| `guard_before_finish`（交付前检查） | 核对项目索引是否已同步至最新产物 | 手动执行 `paper_master_guard.py stop-check`（见 §3） |
| `project_memory`（项目规则记忆） | 持久化稳定的项目级规范与用户选择 | 回退写入 `paper-workspace/_index/project-rules.md` |

## 1.5 文件头元数据（Frontmatter）

`SKILL.md` 与 `modules/*/agents/*.md` 仅使用与运行环境无关的元数据字段：

```yaml
---
name: <标准名>                  # 必填；技能或顾问的唯一标识
description: <一句话职责>        # 必填；导出脚本按 ^description: 解析，须保持单行格式
capabilities: read_file, search_text   # 可选；声明该文件意图使用的通用能力子集
---
```

参数提示置于正文首行引用块（`> 参数提示：…`），不使用已废弃的 `invocable` 与 `args_hint` 字段（`export_standalone.py` 导出时会自动剥离此类历史键）。

元数据规则：
- `capabilities:` 仅作意图声明，不构成运行权限限制；未声明该字段表示可使用当前运行环境提供的全部能力。
- 包内文件禁止声明特定环境的专有键（`tools:`、`allowed-tools:`、`hooks:`、`model:`、`user-invocable:`、`argument-hint:`）。模型选择遵循运行环境默认策略。
- 若特定运行环境需要限制工具列表，应在包外适配层配置，不在本包内增设专有字段。

## 2. 执行与记录原则

- 先完成能力探测再执行模块流程，业务文本中不硬编码特定运行环境的专有工具名。
- 缺失 `web_search`、`web_fetch`、`browser_control`、`spawn_agent`、`parallel_review` 或自动审计能力时，必须在过程日志、`agent-brief.md`、`agent-synthesis` 或最终回复中写明缺失项及替代方案，禁止静默降级。
- 能力缺失不放宽真实性要求，严禁伪造检索结果、页面操作、脚本执行、统计指标、审计记录或顾问意见；缺乏必需能力时应中止对应步骤并说明原因。

## 3. 审计与评分命令（手动入口）

以下三条命令为各运行环境通用的手动入口：

```bash
python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace
python3 scripts/paper_master_guard.py stop-check --workspace paper-workspace
python3 scripts/paper_master_guard.py score-project --workspace paper-workspace --json
```

触发时机：
1. 执行分析命令后若未触发自动审计，运行第一条命令（加 `--strict` 可在存在审计问题时返回退出码 `2`）。
2. 模块交付或会话结束前若未触发自动检查，运行第二条命令（存在缺失或过期索引时返回退出码 `2`）。
3. 实质性执行完任一模块后，运行第三条命令生成或更新质量评分。

即使运行环境已配置自动 hook，在本次会话未确认其真实生效前，仍须手动运行上述命令。

### 3.1 自动触发注册（可选）

当运行环境支持 hook 配置时，可通过通用注册脚本在包外配置自动审计：

```bash
python3 scripts/register_host_hooks.py --detect   # 只读：扫描含 hooks 键的 JSON 配置文件
python3 scripts/register_host_hooks.py --setup    # 交互向导：选择配置文件、配置格式与 matcher
python3 scripts/register_host_hooks.py --check    # 只读：检查当前注册状态
python3 scripts/register_host_hooks.py --print    # 仅输出配置片段，不写入文件
python3 scripts/register_host_hooks.py --remove   # 移除本包注册的 hook 项
```

`--setup` 将配置答案保存至 `.paper-master/host-profile.json` 以便复用；脚本写入前会创建备份，仅追加或移除本包条目。具体三种 JSON 格式见 `references/agent-software-adapters.md` §2。若运行环境自带内置 hook 机制，可直接使用其自带机制。

## 4. 项目规则读取与写入优先级

项目规则仅保存稳定的长期选择与固定约束，不保存临时任务、隐私材料、认证凭据或过程日志。

读取优先级（自高向低合并）：
1. 当前运行环境已加载的项目级规则文件；
2. 项目工作区约定规则文件（如 `AGENTS.md`）中的 `paper-master-4ss` 标记块；
3. `paper-workspace/_index/project-rules.md`。

当用户当次指令与历史规则冲突时，以当次指令为准并同步更新标记块或 `project-rules.md`。写入时仅修改上述标记块内部或 `project-rules.md`，严禁写入技能包目录（维护细节见 `references/project-rules-writing-layer.md`）。

## 5. 会话启动能力探测流程

每次会话首次进入本包时执行一次能力探测（后续步骤直接读取探测结果，环境变化时重新覆盖即可）：

1. **清点工具**：列举当前会话实际可用的全部工具名称。
2. **语义映射**：将工具对照 §1 映射至 13 项核心通用能力（`multi_seat_debate` 不单独探测）；不确定的工具可参照 `references/agent-software-adapters.md` §1 的形态表归类，无法判断时标记为 `unknown`。
3. **写入记录**：将结果写入 `paper-workspace/_index/runtime-capabilities.md`，表格格式固定如下：

   | 能力 | 可用性（yes/no/unknown） | 环境工具 | 回退方式 |
   |---|---|---|---|

   同时在该文件中列明缺失的能力列表及判断依据。
4. **按表执行与记录**：同一会话内依据该表执行对应动作或回退方案，并在日志或回复中明确交代任何能力缺失与降级措施。
