# paper-write-4ss

`paper-write-4ss` 是一个中文社会科学论文写作辅助 skill。它主要面向社会学、管理学、公共管理等领域，帮助用户完成论文结构设计、章节写作、草稿润色和语言规范检查。

这个 skill 的核心思路很简单：先判断论文适合哪种写作范式，再按章节调用对应标准和范文，最后用扫描器检查常见语言问题。

## 能做什么

- 判断论文更适合社会学研究范式还是管理世界案例研究范式。
- 辅助写作标题、摘要、引言、文献综述、研究方法、研究发现、分析框架、结论等部分。
- 提供各章节的写作标准、结构模板和范文提示词。
- 检查中文学术写作中的常见问题，例如口语化表达、破折号、英文引号、套路化句式等。
- 生成修改指令，再由 AI 对句子做自然改写。

## 适合谁用

适合正在写中文社会科学论文的人，尤其是：

- 准备投稿《社会学研究》《社会》《中国社会科学》等社会学期刊
- 准备投稿《管理世界》《公共管理学报》《中国行政管理》等管理或公共管理期刊
- 需要把论文草稿改得更像正式期刊论文
- 需要检查论文里不够规范的中文学术表达

它不负责统计分析、数据清洗、查重、伦理审查，也不适合作为英文论文写作工具。

## 基本使用流程

1. 先确定论文范式
   使用前需要明确目标期刊、研究方法和大致字数。skill 会据此判断采用社会学研究范式，还是管理世界案例研究范式。

2. 按章节查标准
   写某一章时，先读 `chapters/` 中对应的章节规范。如果有范文，再读 `examples/` 中对应的示例。

3. 生成或改写文本
   根据章节标准，让 AI 写作、润色或重构草稿。修改时以自然改写为主，不做机械替换。

4. 运行扫描器检查
   草稿完成后，用 `scripts/writing_scanner.py` 检查高风险表达，再根据结果继续修改。

## 常用命令

快速扫描一篇 Markdown 草稿：

```bash
python3 scripts/writing_scanner.py --scan paper.md
```

生成完整检查报告：

```bash
python3 scripts/writing_scanner.py --report paper.md --out report.md
```

生成可执行的改写指令：

```bash
python3 scripts/writing_scanner.py --instructions paper.md --out instructions.md
```

推荐的润色循环：

```text
扫描草稿 -> 生成改写指令 -> AI 自然重写 -> 再次扫描 -> 直到高风险问题归零
```

## 目录说明

```text
paper-write-4ss/
├── SKILL.md                  # skill 的主说明和调用规则
├── README.md                 # 当前文件，给用户看的快速说明
├── chapters/                 # 分章节写作标准
├── examples/                 # 范文和可复用提示词
├── resources/                # 范式选择、术语表、速查表、写作模式
└── scripts/
    └── writing_scanner.py    # 中文学术写作扫描器
```

## 章节文件怎么找

| 写作任务 | 主要文件 |
| --- | --- |
| 选题、标题、摘要 | `chapters/ch02-topic-material.md` |
| 引言 | `chapters/ch03-genesis-question.md`、`examples/intro_example.md` |
| 文献综述 | `chapters/ch04-lit-review.md`、`chapters/ch05-lit-technique.md`、`examples/lit_review_example.md` |
| 研究方法 | `chapters/ch06-material-method.md` |
| 研究发现 | `chapters/ch07-organizing-materials.md`、`examples/findings_example.md` |
| 分析框架或理论对话 | `chapters/ch08-theory-dialogue.md`、`examples/framework_example.md` |
| 结论与讨论 | `chapters/ch09-conclusion.md`、`examples/conclusion_example.md` |
| 投稿规范和参考文献 | `chapters/ch10-submission-ethics.md` |

如果只是想快速查一下结构、比例或常见问题，优先看：

```text
resources/cheatsheet.md
```

如果不确定自己的论文属于哪种范式，优先看：

```text
resources/paradigm_selector.md
```

## 写作时特别注意

本 skill 对输出文本有几条硬性要求：

- 正文中不要嵌入完整论文标题，使用作者和年份来引用。
- 不使用一文中、该文等口语化表述。
- 避免先否定再转向的套路句式。
- 正文不使用破折号。
- 不用脚本机械替换标点，必须根据语义自然改写。
- 引号只在必要时使用，并统一使用中文引号。

这些要求主要服务于一个目标：让论文表达更接近期刊论文的正式语体。

## 一句话总结

`paper-write-4ss` 的定位是一套面向中文社会科学论文的写作路由、章节标准、范文提示词和语言扫描流程。用它时，先定范式，再按章节写，最后用扫描器把明显不规范的表达清掉。

## 联系方式

- 作者邮箱：[jingyangyuan101@gmail.com](mailto:jingyangyuan101@gmail.com)
