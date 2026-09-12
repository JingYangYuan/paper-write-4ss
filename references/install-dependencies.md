# Paper Master 4SS — 依赖安装路径

本文档按模块列出 paper-master-4ss 下所有脚本、模板和运行时的外部依赖，以及各模块自带的安装说明位置。总控路由前先检查目标模块的依赖状态，缺失时引导安装。

---

## 一、总控快速检查

```bash
python3 --version    # 所有 Python 脚本的最低要求
pandoc --version     # submission 模块 Markdown → Word 导出
```

---

## 二、各模块依赖明细

### 2.1 design 模块

**路径**: `paper-master-4ss/modules/design/`

**依赖**: 无外部依赖。`scripts/frame_locator.py` 仅使用 Python 3 标准库（argparse, json, re, dataclasses, pathlib）。

**验收**:
```bash
python3 paper-master-4ss/modules/design/scripts/frame_locator.py --help
```

---

### 2.2 lit 模块

**路径**: `paper-master-4ss/modules/lit/`

**详细安装说明**: `paper-master-4ss/modules/lit/references/install-dependencies.md`

**依赖**:

| 依赖 | 用途 | 强制 |
|------|------|------|
| 浏览器控制后端（ZCode 内置 browser-use，或 OMP pi-chrome） | CNKI 网页操纵（kns8s 专业检索） | 是 |
| 可见浏览器窗口（ZCode 面板，或 OMP `Pi Session:` 标签） | CNKI 登录、验证码人工完成 | 是 |
| Zotero Desktop + Connector | 本地文献库保存与去重 | 否 |
| Zotero MCP（推荐 `zotero-local-mcp`） | 代理检索本地库、写入题录/摘要、读取附件全文 | 否 |

**快速检查**:
ZCode 后端为内置能力，无需安装；OMP 后端需一次性加载 pi-chrome 伴生 Chrome 扩展（`pi install npm:pi-chrome` → `/chrome onboard` → `/chrome authorize` → `/chrome doctor`），详见 `paper-master-4ss/modules/lit/references/pi-chrome-browser.md` 与公开文档 <https://github.com/JingYangYuan/pi-chrome-cnki>；npm 不可用或扩展"装了连不上"时用离线镜像 <https://github.com/JingYangYuan/pi-chrome-mirror>。CNKI 阶段开始前按 `paper-master-4ss/modules/lit/references/cnki-kns8s-closed-loop.md` §2 做可用性检查（列标签页/新建标签页/导航 + 读取轻量页面状态）。

---

### 2.3 outline 模块

**路径**: `paper-master-4ss/modules/outline/`

**依赖**: 无外部依赖。纯 Markdown 处理，不包含脚本或运行时。

**验收**:
```bash
test -f paper-master-4ss/modules/outline/SKILL.md
test -f paper-master-4ss/modules/outline/references/outline-patterns.md
test -f paper-master-4ss/modules/outline/references/output-formats.md
```

---

### 2.4 analysis 模块

**路径**: `paper-master-4ss/modules/analysis/`

**三语言模板各自依赖，按用户所选语言按需安装：**

#### Python 模板 (`templates/python-analysis-template.py`)

| 包 | 用途 | 强制 |
|----|------|------|
| numpy, pandas | 数据处理 | 是 |
| scipy | 统计检验 | 是 |
| statsmodels | 回归诊断、Logit/Probit/Poisson/Tobit/Heckman | 是 |
| linearmodels | 面板 FE/RE/GMM、IV/2SLS | 否（面板/IV 时必装） |
| matplotlib, seaborn | 图形导出 | 否（出图时必装） |

```bash
python3 -m pip install --user numpy pandas scipy statsmodels
# 面板/IV 分析追加:
python3 -m pip install --user linearmodels
# 出图追加:
python3 -m pip install --user matplotlib seaborn
```

#### R 模板 (`templates/r-analysis-template.R`)

| 包 | 用途 | 强制 |
|----|------|------|
| ggplot2, dplyr, tidyr, tibble, purrr, readr | 核心数据处理与绑图 | 是 |
| haven, readxl | 读取 Stata/Excel 数据 | 否 |
| fixest, lfe | 高维固定效应 | 否（面板时推荐） |
| AER, ivreg | IV/2SLS | 否 |
| MatchIt, cobalt | PSM/CEM | 否 |

```r
install.packages(c("ggplot2", "dplyr", "tidyr", "tibble", "purrr", "readr"))
```

#### Stata 模板 (`templates/stata-analysis-template.do`)

| 包 | 用途 | 强制 |
|----|------|------|
| outreg2 / estout | 回归表导出 | 是 |
| reghdfe | 高维固定效应 | 否（FE 时必装） |
| ivreg2 | IV/2SLS 诊断 | 否（IV 时必装） |
| psmatch2 | PSM | 否 |

```stata
ssc install outreg2
ssc install estout
ssc install reghdfe
ssc install ivreg2
```

详细安装、镜像配置、验收命令和故障排除见各语言专属文档：

| 语言 | 文档 |
|------|------|
| Python | `paper-master-4ss/modules/analysis/references/python-ecosystem-setup.md` |
| R | `paper-master-4ss/modules/analysis/references/r-ecosystem-setup.md` |
| Stata | `paper-master-4ss/modules/analysis/references/stata-ecosystem-setup.md` |

---

### 2.5 write 模块

**路径**: ``

**依赖**: 无外部依赖。以下四个脚本均仅使用 Python 3 标准库：

| 脚本 | 用途 |
|------|------|
| `scripts/complexity_analyzer.py` | 中文社科文本复杂度诊断 |
| `scripts/writing_scanner.py` | 中文学术写作 25 条反模式扫描 |
| `scripts/method_router.py` | 研究方法类型识别与路由 |
| `scripts/example_extractor.py` | 范文按需截取 |

**验收**:
```bash
python3 scripts/complexity_analyzer.py --help
python3 scripts/writing_scanner.py --help
python3 scripts/method_router.py --help
python3 scripts/example_extractor.py --help
```

---

### 2.6 check 模块

**路径**: `paper-master-4ss/modules/check/`

**依赖**: 无外部依赖。纯 Markdown 知识库与 agent 流程；完整审稿的产物写入 `05-writing/reviews/`。

**验收**:
```bash
test -f paper-master-4ss/modules/check/SKILL.md
test -f paper-master-4ss/modules/check/glossary.md
test -f paper-master-4ss/modules/check/patterns.md
test -f paper-master-4ss/modules/check/cheatsheet.md
```

---

### 2.7 submission 模块

**路径**: `paper-master-4ss/modules/submission/`

**详细安装说明**: `paper-master-4ss/modules/submission/references/install-dependencies.md`

**依赖**:

| 依赖 | 用途 | 强制 |
|------|------|------|
| Python 3 | 所有脚本运行 | 是 |
| pandoc | Markdown → Word 导出 | 否（仅导出时） |
| python-docx | Word 格式检查、reference docx 清洗 | 否（仅格式检查时） |
| lxml | docx XML 处理 | 否（仅格式检查时） |

**安装（macOS）**:
```bash
brew install pandoc
python3 -m pip install --user python-docx lxml
```

**验收**:
```bash
python3 paper-master-4ss/modules/submission/scripts/export_docx.py --help
python3 paper-master-4ss/modules/submission/scripts/check_docx_format.py --help
python3 paper-master-4ss/modules/submission/scripts/sanitize_reference_docx.py --help
python3 paper-master-4ss/modules/submission/scripts/check_citations.py --help
```

---

### 2.8 update 模块

**路径**: `paper-master-4ss/modules/update/`

**依赖**: 无外部依赖。纯 agent 派发，不包含脚本或运行时。

**验收**:
```bash
test -f paper-master-4ss/modules/update/SKILL.md
```

---

## 三、一键验收脚本

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
test -f paper-master-4ss/modules/lit/references/cnki-kns8s-closed-loop.md && echo "lit/闭环协议 OK"
test -f paper-master-4ss/modules/lit/scripts/cnki/kns8s-download.sh && echo "lit/下载器 OK"

echo ""
echo "=== outline ==="
test -f paper-master-4ss/modules/outline/SKILL.md && echo "outline/SKILL.md OK"

echo ""
echo "=== analysis ==="
python3 -c "
import importlib, sys
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
echo ""
echo "=== check ==="
test -f paper-master-4ss/modules/check/SKILL.md && echo "check/SKILL.md OK"
test -f paper-master-4ss/modules/check/glossary.md && echo "check/glossary.md OK"
test -f paper-master-4ss/modules/check/patterns.md && echo "check/patterns.md OK"
test -f paper-master-4ss/modules/check/cheatsheet.md && echo "check/cheatsheet.md OK"

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
echo "=== DONE ==="
```

---

## 四、模块级安装说明索引

各模块如需更详细的安装指引（如浏览器控制可用性检查、Zotero MCP 环境变量、pandoc 模板调试），直接读取模块自己的安装文档：

| 模块 | 详细安装说明 |
|------|-------------|
| lit | `paper-master-4ss/modules/lit/references/install-dependencies.md` |
| submission | `paper-master-4ss/modules/submission/references/install-dependencies.md` |

其余模块（design / outline / analysis / write / update）仅有本文档中的依赖声明，不设独立安装说明。
