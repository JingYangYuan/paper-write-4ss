<p align="center">
  <img src="docs/banner.svg" alt="paper-write-4ss" width="100%">
</p>

# Paper 论文写作 4SS（write 模块独立版）

中文社会科学论文写作系统。先通过 research_router.md 完成研究方法协议与发表范式双层路由，再按章节标准和范文提示词完成写作、润色和检查。支持规范研究、实证研究、阐释研究、混合研究四类方法协议，以及社会学研究范式和管理世界案例研究范式两类发表风格。配备 writing_scanner.py 与 complexity_analyzer.py，用于语言反模式扫描和文本复杂度诊断。

本包由 `paper-master-4ss/scripts/export_standalone.py` 从总控包 `paper-master-4ss/modules/write/` 自动导出：

- 包内相对路径相对本包根目录解析；
- `master/` 与 `references/` 中的协议/治理文件是导出时拷贝的快照；
- 跨模块路径 `paper-master-4ss/modules/<x>/...` 相对同级安装的总控包解析；
- 更新方式：修改总控包对应模块后运行
  `python3 paper-master-4ss/scripts/export_standalone.py write` 重新导出，勿直接编辑本包。

## 它做什么

先经研究方法协议与发表范式双层路由，再按章节标准和范文提示词写作、润色和检查。产出正文净稿（标题层级 + 自然段），过程材料不得拼进正文。

配备 `writing_scanner.py` 与 `complexity_analyzer.py`，用于语言反模式扫描和文本复杂度诊断。

## 路由

| 层 | 选项 |
|---|---|
| 方法协议 | 规范、实证、阐释、混合 |
| 发表风格 | 社会学研究范式 / 管理世界案例研究范式 |

## 使用

将本目录安装为宿主 skill（与 `paper-master-4ss` 总控包同级）。入口见 `SKILL.md`。
