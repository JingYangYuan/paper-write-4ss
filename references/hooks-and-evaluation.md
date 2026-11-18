# Hooks and Evaluation（执行审计与交付检查规范）

本规范定义两项强制性过程校验的触发条件、检查内容与配置方式：
1. **命令后审计（`post-bash`）**：执行分析命令后，核对 run-log 记录、stdout/stderr 路径、报错信号及登记输出文件是否存在。
2. **交付前检查（`stop-check`）**：模块交付或会话停止前，核对 `_index/project-state.md` 与 `_index/handoff-status.md` 是否已同步至最新产物。

运行环境配置自动 hook 后可自动触发上述检查；无论是否配置 hook，只要当前会话未能确认自动 hook 已生效，均须手动运行第 4 节命令。

## 1. 三层架构与纪律

- **校验脚本层**：`scripts/paper_master_guard.py` 为唯一校验实现。技能包 frontmatter 不声明任何 hooks。
- **自动触发层（可选）**：通过 `scripts/register_host_hooks.py` 将上述两项校验注册至运行环境的 hook 配置，或由包外适配层配置。
- **手动兜底层（始终可用）**：在无 hook 支持、注册失败或未确认生效时，直接通过命令行执行第 4 节命令。

注册自动触发时仅增量添加本包所需的两项 guard，不覆盖已有配置，也不向包内写入环境专有模板。

## 2. 自动 Hook 注册（可选）

```bash
python3 scripts/register_host_hooks.py --host auto            # 自动探测并注册（无明确配置证据时不写入）
python3 scripts/register_host_hooks.py --host auto --check    # 只读查询注册状态（0=已注册，1=未注册，2=未知环境）
python3 scripts/register_host_hooks.py --host <name>          # 指定配置名称注册
python3 scripts/register_host_hooks.py --print                # 预览生成的配置片段或通用契约，不写入文件
python3 scripts/register_host_hooks.py --host <name> --remove # 移除本包注册的 hook 项
```

注册边界与退出码约定：
- **安全写入**：写入前自动备份为 `<file>.paper-master.bak`；仅增量修改 hook 项且支持幂等重复执行；配置文件解析失败时不写入任何内容。
- **内置 Hook 让位**：若当前会话已存在外层运行环境提供的 hook 层，`--host auto` 直接退出（退出码 `2`）而不写入本地配置；确需覆盖时须显式指定 `--host <name>`。
- **退出码**：`0` 表示成功或已注册；`1` 表示未注册（`--check`）或配置文件解析失败；`2` 表示未识别环境或自动探测无证据（未写入）。
- **路径与输出处理**：命令路径使用显式路径而不依赖 `${CLAUDE_PLUGIN_ROOT}` 等专有变量；若运行环境将 hook 的 stdout 解析为严格 JSON，须按第 7 节 B 型格式在命令末尾重定向 `>/dev/null`。

## 3. 审计与检查内容

### 3.1 命令后审计（`post-bash`）

- **触发条件**：当前会话执行了 `Rscript`、`python3`/`python`、`.do`/`.R`/`.py` 脚本、`paper-workspace/04-analysis` 相关命令或 Stata MCP 调用（`stata_run_file` / `stata_run_selection`）。
- **检查动作**：
  1. 读取最新的 `paper-workspace/04-analysis/reports/run-log-[date].md`；
  2. 检索 `blocked`、`error`、`failed`、`traceback`、Stata `r(...)`、R `Execution halted` 及非零退出码等失败信号；
  3. 检查 run-log 是否记录 stdout/stderr 路径；
  4. 核对 run-log 登记的输出文件是否真实存在；
  5. 将审计结果写入 `paper-workspace/_logs/hook-audit/analysis-log-audit-[date].md`。
- **退出行为**：默认退出码为 `0`（异常信息写入 stderr 与审计报告）；附加 `--strict` 时发现问题返回退出码 `2` 以阻断后续流程。不得将执行失败或未核验脚本的产出写入统计结论。

### 3.2 交付前检查（`stop-check`）

- **触发条件**：会话结束前或模块交付前。
- **阻断规则**：
  - 项目不存在 `paper-workspace/` 时放行（退出码 `0`）；
  - 工作区尚无业务模块产物及流程日志时放行（退出码 `0`）；
  - 存在模块产物或流程日志，但 `_index/project-state.md` 或 `_index/handoff-status.md` 缺失，或修改时间早于最新关键产物时，阻断交付（退出码 `2`）。

## 4. 手动执行命令

```bash
python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace
python3 scripts/paper_master_guard.py post-bash --workspace paper-workspace --strict
python3 scripts/paper_master_guard.py stop-check --workspace paper-workspace
python3 scripts/paper_master_guard.py score-project --workspace paper-workspace --json
```

## 5. 产物文件路径

- `paper-workspace/_logs/hook-audit/analysis-log-audit-[YYYY-MM-DD].md`
- `paper-workspace/_index/quality-score.md`
- `paper-workspace/_index/quality-score.json`

## 6. 异常处理

- **`post-bash` 发现问题**：先修正脚本、重新执行并更新 run-log 与输出文件，再撰写分析结论。
- **`stop-check` 阻断**：同步更新 `_index/project-state.md` 与 `_index/handoff-status.md`（补充最新产物、质量分、阻断项与下一步建议）后重跑检查。
- **评分偏低**：依据 `quality-score.md` 中的 `failure_attribution` 与 `fix_next` 补齐证据、日志或交接文件。
- **自动注册不适用**：不修改配置文件，直接使用 `--print` 输出手工配置，或统一使用第 4 节手动命令。

## 7. 交互式向导与配置格式

若自动探测无法定位配置文件，可使用交互式向导保存配置到 `<项目根目录>/.paper-master/host-profile.json`：

```bash
python3 scripts/register_host_hooks.py --detect   # 扫描目录树中含 hooks 键的 JSON 文件
python3 scripts/register_host_hooks.py --setup    # 交互式配置目标文件、格式与 matcher 并注册
python3 scripts/register_host_hooks.py --check    # 查询注册状态
python3 scripts/register_host_hooks.py --print    # 仅打印配置片段
python3 scripts/register_host_hooks.py --remove   # 撤销本包注册项
```

三种 JSON 格式说明如下（完整片段见 `references/agent-software-adapters.md` §2，配置时将 `<ROOT>` 替换为本技能包根目录的绝对路径）：

| 格式 | 结构特征 | 常见适用场景 |
|---|---|---|
| A | `hooks.<PostEvent>` 与 `hooks.Stop` 各嵌套一层 `hooks` 数组 | 项目级配置文件 |
| B | `hooks.events.<PostEvent>`，附带 `hooks.enabled` 开关 | 用户级配置文件（常需追加 `>/dev/null`） |
| C | 命名空间块内 Post 事件嵌套 `hooks` 数组，Stop 为扁平数组 | 命名空间隔离式项目配置 |

上述配置自下一次会话起自动生效；完成注册的当前会话仍须按第 4 节手动执行校验。
