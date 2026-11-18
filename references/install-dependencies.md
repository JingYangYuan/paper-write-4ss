# Paper Master 4SS — 外部依赖与验收规范

路由至目标模块前须核对对应外部依赖；缺失强制依赖时应中止推进并引导安装，不得在依赖不满足的情况下继续执行。

## 〇、按任务类型快速判定

| 目标模块 / 场景 | 必需或可选依赖 | 缺失时的影响 |
|---|---|---|
| 仅做基础脚本与导出校验 | Python 3、`pandoc`（§一） | 无法运行包内辅助脚本或导出 Word |
| `lit`：英文检索下载 / 中文 NCPSSD 定位 | Python 3 + `requests`、`httpx`、`pymupdf`（或 `pypdf`），可选 `LITDOWN_EMAIL` | 无法运行 `lit-down` 英文与 NCPSSD 定位下载脚本 |
| `lit`：CNKI 取全文 / 浏览器 CDP 兜底 | `browser_control` 后端（`ego-browser`）与可见浏览器窗口（需机构 IP 及人工处理部分登录/验证） | 无法执行 CNKI 全文取回与浏览器 CDP 兜底，仅可做 NCPSSD 定位、英文 HTTP 渠道与本地库检索 |
| `lit`：本地文献库管理（可选） | Zotero Desktop + Connector + `zotero-local-mcp` | 不阻断检索，题录与全文仅保存在 `paper-workspace/02-literature/` |
| `analysis`：定量分析 | 按所选语言配置 Stata (+ `statamcp`) / R (+ `Rscript` 及所需包) / Python 3 (+ `venv` 及所需包) | 无法运行对应语言分析，仅可输出分析脚本而不能产出统计结果 |
| `write` | Python 3（仅标准库，无第三方依赖） | 无法运行文风扫描与复杂度分析脚本 |
| `submission` | Python 3（强制）；`pandoc`、`python-docx`、`lxml`（导出与格式检查） | 无法导出 `.docx` 及执行版式检查 |
| `mechanigraph` | Python 3（强制）；Google Chrome / Chromium（推荐，用于无头渲染 PNG 自检） | 仍可生成纯矢量 SVG，但缺少自动 PNG 视觉自检 |
| `outline` / `check` / `update` | 无外部依赖 | 无影响 |

---

## 一、总控基础检查

```bash
python3 --version    # 所有 Python 辅助脚本的最低要求
pandoc --version     # submission 模块 Markdown 转 Word 依赖
```

## 二、分模块依赖与验收命令

### 2.1 `design`

- **路径**：`paper-master-4ss/modules/design/`
- **依赖**：Python 3 标准库（`scripts/frame_locator.py` 无第三方依赖）。
- **验收**：

```bash
python3 paper-master-4ss/modules/design/scripts/frame_locator.py --help
```

### 2.2 `lit`

- **路径**：`paper-master-4ss/modules/lit/`
- **详细安装与排障**：`paper-master-4ss/modules/lit/references/install-dependencies.md`
- **依赖**：
  - 英文与 NCPSSD 定位下载：`requests`、`httpx`、`pymupdf`（或 `pypdf`），建议设置 `LITDOWN_EMAIL`；
  - 强制（仅 CNKI 取全文与浏览器 CDP 兜底）：`browser_control` 后端（ego lite + `ego-browser` 命令）及可见浏览器窗口；
  - 可选：Zotero Desktop + Connector、Zotero MCP（`zotero-local-mcp`）。
- **验收**：按 `paper-master-4ss/modules/lit/references/install-dependencies.md` 校验 Python 包与脚本；启动 CNKI 取全文前按 `references/runtime-adapter.md` §5 与 `paper-master-4ss/modules/lit/references/browser.md` 确认 `ego-browser` 可用性，并在知网页面确认顶栏出现机构名称。

### 2.3 `outline`

- **路径**：`paper-master-4ss/modules/outline/`
- **依赖**：无外部脚本或运行时依赖。
- **验收**：

```bash
test -f paper-master-4ss/modules/outline/SKILL.md
test -f paper-master-4ss/modules/outline/references/outline-patterns.md
test -f paper-master-4ss/modules/outline/references/output-formats.md
```

### 2.4 `analysis`

- **路径**：`paper-master-4ss/modules/analysis/`
- **依赖**：依据实际选用的语言生态配置环境，安装命令、镜像源与排障以各语言独立文档为准：

| 分析语言 | 依赖配置文档 |
|---|---|
| Python | `paper-master-4ss/modules/analysis/references/python-ecosystem-setup.md` |
| R | `paper-master-4ss/modules/analysis/references/r-ecosystem-setup.md` |
| Stata | `paper-master-4ss/modules/analysis/references/stata-ecosystem-setup.md` |

### 2.5 `write`

- **路径**：``
- **依赖**：Python 3 标准库（无需额外安装包）。

| 脚本 | 功能 |
|---|---|
| `scripts/complexity_analyzer.py` | 中文社科文本复杂度诊断 |
| `scripts/writing_scanner.py` | 中文学术写作 25 类反模式扫描 |
| `scripts/method_router.py` | 研究方法类型识别与路由 |
| `scripts/example_extractor.py` | 范文按需切片提取 |

- **验收**：

```bash
python3 scripts/complexity_analyzer.py --help
python3 scripts/writing_scanner.py --help
python3 scripts/method_router.py --help
python3 scripts/example_extractor.py --help
```

### 2.6 `check`

- **路径**：`paper-master-4ss/modules/check/`
- **依赖**：无外部运行时依赖（审稿报告写入 `05-writing/reviews/`）。
- **验收**：

```bash
test -f paper-master-4ss/modules/check/SKILL.md
test -f paper-master-4ss/modules/check/glossary.md
test -f paper-master-4ss/modules/check/patterns.md
test -f paper-master-4ss/modules/check/cheatsheet.md
```

### 2.7 `submission`

- **路径**：`paper-master-4ss/modules/submission/`
- **详细安装说明**：`paper-master-4ss/modules/submission/references/install-dependencies.md`
- **依赖**：Python 3（强制）；`pandoc`（Word 导出）、`python-docx` 与 `lxml`（版式校验）。
- **验收**：

```bash
python3 paper-master-4ss/modules/submission/scripts/export_docx.py --help
python3 paper-master-4ss/modules/submission/scripts/check_docx_format.py --help
python3 paper-master-4ss/modules/submission/scripts/sanitize_reference_docx.py --help
python3 paper-master-4ss/modules/submission/scripts/check_citations.py --help
```

### 2.8 `update`

- **路径**：`paper-master-4ss/modules/update/`
- **依赖**：无外部脚本或运行时依赖。
- **验收**：

```bash
test -f paper-master-4ss/modules/update/SKILL.md
```

### 2.9 `mechanigraph`

- **路径**：`paper-master-4ss/modules/mechanigraph/`
- **依赖**：

| 依赖 | 用途 | 是否强制 |
|---|---|---|
| Python 3 | 运行生成与渲染脚本 | 强制 |
| Google Chrome / Chromium | 无头渲染 SVG 为 PNG 进行视觉自检（支持 Chrome CLI 或 Selenium） | 可选（建议配置） |
| `selenium`, `webdriver-manager` | 通过 Python 驱动 Chrome 无头渲染 | 可选（系统已有 Chrome CLI 时可不装） |

- **安装参考**：

```bash
# macOS 安装 Google Chrome
brew install --cask google-chrome

# 可选：安装 Selenium 支持
python3 -m pip install --user selenium webdriver-manager
```

- **验收**：

```bash
python3 paper-master-4ss/modules/mechanigraph/scripts/generate_mechanism.py --help
python3 paper-master-4ss/modules/mechanigraph/scripts/render_svg.py
```

- **缺失 Chrome 的降级行为**：`generate_mechanism.py` 仍正常输出纯矢量 SVG 与元数据至 `paper-workspace/figures/`；`render_svg.py` 输出降级提示，不阻断主流程，仅跳过自动 PNG 视觉核查（需人工在浏览器打开预览）。

## 三、全模块批量验收脚本

```bash
#!/bin/bash
# paper-master-4ss 全模块依赖验收
# 从 paper-master-4ss/ 根目录执行

SKILL_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$SKILL_ROOT"

echo "=== Python ==="
python3 --version || echo "MISSING: python3"

echo ""
echo "=== pandoc ==="
pandoc --version 2>/dev/null | head -1 || echo "MISSING: pandoc"

echo ""
echo "=== design ==="
python3 paper-master-4ss/modules/design/scripts/frame_locator.py --help >/dev/null 2>&1 && echo "OK" || echo "MISSING"

echo ""
echo "=== lit ==="
test -f paper-master-4ss/modules/lit/SKILL.md && echo "lit/SKILL.md OK"
test -f paper-master-4ss/modules/lit/references/channels.md && echo "lit/渠道总表 OK"
test -f paper-master-4ss/modules/lit/references/ncpssd.md && echo "lit/NCPSSD 协议 OK"
test -f paper-master-4ss/modules/lit/references/cnki.md && echo "lit/CNKI 取全文协议 OK"
test -f paper-master-4ss/modules/lit/references/books.md && echo "lit/书轮协议 OK"
test -f paper-master-4ss/modules/lit/references/browser.md && echo "lit/浏览器兜底协议 OK"
test -f paper-master-4ss/modules/lit/scripts/probe_channels.py && echo "lit/探活脚本 OK"
test -f paper-master-4ss/modules/lit/scripts/ncpssd_search.py && echo "lit/NCPSSD 检索器 OK"
test -f paper-master-4ss/modules/lit/scripts/enrich_crossref.py && echo "lit/Crossref 定位器 OK"
test -f paper-master-4ss/modules/lit/scripts/download.py && echo "lit/并发下载器 OK"
test -f paper-master-4ss/modules/lit/scripts/books_libgen.py && echo "lit/LibGen 书轮 OK"
test -f paper-master-4ss/modules/lit/scripts/verify_content.py && echo "lit/内容校验器 OK"
test -f paper-master-4ss/modules/lit/scripts/cnki_prepare.py && echo "lit/知网建队器 OK"
test -f paper-master-4ss/modules/lit/scripts/cnki_fetch_batch.mjs && echo "lit/知网直取 worker OK"
test -f paper-master-4ss/modules/lit/scripts/cnki_report.py && echo "lit/知网核验器 OK"

echo ""
echo "=== outline ==="
test -f paper-master-4ss/modules/outline/SKILL.md && echo "outline/SKILL.md OK"

echo ""
echo "=== analysis ==="
python3 -c "
import importlib
for pkg in ['numpy','pandas','scipy','statsmodels']:
    try:
        importlib.import_module(pkg)
        print(f'{pkg} OK')
    except ImportError:
        print(f'{pkg} MISSING')
" || echo "analysis/Python check failed"

echo ""
echo "=== write ==="
python3 scripts/complexity_analyzer.py --help >/dev/null 2>&1 && echo "complexity_analyzer OK"
python3 scripts/writing_scanner.py --help >/dev/null 2>&1 && echo "writing_scanner OK"

echo ""
echo "=== check ==="
test -f paper-master-4ss/modules/check/SKILL.md && echo "check/SKILL.md OK"
test -f paper-master-4ss/modules/check/glossary.md && echo "check/glossary.md OK"
test -f paper-master-4ss/modules/check/patterns.md && echo "check/patterns.md OK"
test -f paper-master-4ss/modules/check/cheatsheet.md && echo "check/cheatsheet.md OK"

echo ""
echo "=== submission ==="
python3 -c "
import importlib
for pkg in ['docx','lxml']:
    try:
        importlib.import_module(pkg)
        print(f'{pkg} OK')
    except ImportError:
        print(f'{pkg} MISSING')
" || echo "submission/Python check failed"
python3 paper-master-4ss/modules/submission/scripts/export_docx.py --help >/dev/null 2>&1 && echo "export_docx OK"

echo ""
echo "=== update ==="
test -f paper-master-4ss/modules/update/SKILL.md && echo "update/SKILL.md OK"

echo ""
echo "=== mechanigraph ==="
python3 paper-master-4ss/modules/mechanigraph/scripts/generate_mechanism.py --help >/dev/null 2>&1 && echo "generate_mechanism OK"
test -f paper-master-4ss/modules/mechanigraph/SKILL.md && echo "mechanigraph/SKILL.md OK"
echo "=== DONE ==="
```

## 四、模块详细安装文档索引

仅 `lit` 与 `submission` 设有独立安装说明文档，其余模块依赖声明均在本文件内完整列出：

| 模块 | 详细文档路径 |
|---|---|
| `lit` | `paper-master-4ss/modules/lit/references/install-dependencies.md` |
| `submission` | `paper-master-4ss/modules/submission/references/install-dependencies.md` |
