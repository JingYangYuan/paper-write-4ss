# 研究方法与写作范式路由指南

本文档是 `write module` 的总入口。它合并了原来的 `method_protocol.md` 和 `paradigm_selector.md`，负责在正式写作前完成两层判断。

第一层是研究方法协议判断，也就是识别论文更接近规范研究、实证研究、阐释研究还是混合研究。

第二层是发表范式判断，也就是识别论文更适合社会学研究范式，还是管理世界案例研究范式。

两层判断完成后，Skill 才进入写作规划、分段派发、subagent 草稿撰写、文风总控和扫描器检查。

---

## 顾问派发闸门

研究路由输出后，必须派发 `agents/structure-writing-consultant.md` 作为写作规划子 agent，并把研究方法协议、发表范式、风格梯度、大纲或已有正文作为输入包；任务是文献综述时，输入包还必须包含 `master/literature-review-protocol.md` 与 lit 阶段交接的证据表，净稿落 `paper-workspace/05-writing/literature-review.md`。顾问必须输出 `writing-dispatch-plan`，写入项目工作区的 `paper-workspace/_logs/agents/write-[YYYY-MM-DD]/structure-writing-consultant.md`，并由主流程落盘到 `paper-workspace/05-writing/plans/writing-dispatch-plan-[slug]-[YYYY-MM-DD].md`。若任务是生成新正文，再按该计划多段派发 `agents/chapter-draft-writer.md`；每个 writer 输出必须按 `task_id` 独立保存为 `paper-workspace/_logs/agents/write-[YYYY-MM-DD]/paper-write-chapter-draft-writer--{task_id}.md`，随后必须运行 `scripts/assemble_drafts.py` 拼接草稿并生成 source map 和 assembly check（综述正文任务拼接结果的 `--manuscript` 落点同样为 `05-writing/literature-review.md`）。主 agent 阅读拼接稿与 source map，写入 `paper-workspace/05-writing/reviews/main-agent-review-[slug]-[YYYY-MM-DD].md` 后，才可进入论证复核、材料复核和文风总控。若任务是润色已有稿，则跳过 dispatch-plan 和 draft writer，直接进入 `style-consultant` 文风总控和扫描器循环。

---

## 一、使用原则

在开始写作之前，必须先完成研究路由。Skill 加载后，应使用 ask_user 工具向用户提问，不应跳过提问直接进入正文生成。

路由顺序如下。

1. 先判断研究方法协议
2. 再判断目标期刊与写作范式
3. 再派发规划 agent 生成 `writing-dispatch-plan`
4. 再按计划多段派发 subagent 草稿撰写
5. 运行 `assemble_drafts.py` 拼接草稿并由主 agent 阅读审查
6. 最后进行论证/材料复核、文风总控、语言扫描与复杂度检查

---

## 二、第一层：研究方法协议判断

### 目标

这一层解决的问题是：这篇论文属于哪一种知识生产方式。

### 方法协议的四种类型

| 类型 | 核心问题 | 常见材料 | 正文重心 | 高风险错误 |
| --- | --- | --- | --- | --- |
| 规范研究 | 应当如何判断、评价或安排 | 概念、经典理论、制度原则、伦理争议 | 概念界定、价值标准、反驳与制度含义 | 把价值判断写成经验事实 |
| 实证研究 | X 是否影响 Y，机制如何发生 | 调查数据、统计数据、文本数据、实验数据、网络数据 | 理论机制、变量操作化、模型设定、结果解释 | 只有模型，没有问题意识 |
| 阐释研究 | 行动者如何理解，制度过程如何形成 | 访谈、档案、政策文本、历史材料、案例过程 | 语境、过程、意义、机制解释 | 把案例复述误写成理论分析 |
| 混合研究 | 方法、技术或经验案例如何重塑研究实践 | 代码、日志、流程、案例、数据、文本 | 方法困境、系统设计、对照演示、方法论反思 | 技术说明与学术论证脱节 |

### ask_user 提问

Skill 应按顺序提问。

结构化示例模块统一遵守 `references/ask-user-question-examples.md`。第一层可使用以下 ask_user 示例：

```text
question: "你的研究问题属于哪一类？"
header: "研究问题"
options: [
  {label: "规范研究", description: "应当如何评价某个制度、概念或安排"},
  {label: "实证研究", description: "某个变量是否影响另一个变量，或机制如何发生"},
  {label: "阐释研究", description: "某个过程、行动或意义是如何形成的"},
  {label: "混合/方法研究", description: "某种方法、工具、系统或研究流程如何运作"}
]
```

```text
question: "你的主要材料是什么？"
header: "主要材料"
options: [
  {label: "数据材料", description: "大规模调查数据、统计数据、实验数据或网络数据"},
  {label: "质性材料", description: "访谈、田野、档案、案例或历史材料"},
  {label: "理论文本", description: "理论文本、规范性文本或经典文献"},
  {label: "混合材料", description: "代码、日志、脚本、Agent 流程或多类材料混合"}
]
```

#### 问题一：你的研究问题属于哪一类？

可提示用户从下列方向选择。

- 应当如何评价某个制度、概念或安排
- 某个变量是否影响另一个变量
- 某个过程、行动或意义是如何形成的
- 某种方法、工具、系统或研究流程如何运作

#### 问题二：你的主要材料是什么？

可提示用户回答。

- 大规模调查数据、统计数据、实验数据
- 访谈、田野、档案、案例、历史材料
- 理论文本、规范性文本、经典文献
- 代码、日志、脚本、Agent 流程、方法系统
- 混合材料

#### 问题三：你的目标任务是什么？

可提示用户回答。

- 写概念辨析或规范论证
- 写实证分析
- 写案例解释或过程分析
- 写方法论论文、AI Agent 论文、系统设计论文
- 暂时不确定

### 协议层输出格式

Skill 应输出以下内容。

1. 主类型
2. 副类型
3. 类型权重
4. 判断依据
5. 推荐路径
6. 不推荐路径
7. 当前最应调用的提示词卡片
8. 硬停止问题

### 类型权重的推荐格式

```text
规范研究：0.00-1.00
实证研究：0.00-1.00
阐释研究：0.00-1.00
混合研究：0.00-1.00
```

不要强行三选一。允许混合型论文同时具有主路径和副路径。

---

## 三、第二层：发表范式判断

### 目标

这一层解决的问题是：这篇论文更适合按哪一种中文期刊写作范式展开。

本文区分两种常用发表范式。

1. 社会学研究范式
2. 管理世界案例研究范式

### 两种范式的核心差异

| 维度 | 社会学研究范式 | 管理世界案例研究范式 |
| --- | --- | --- |
| 目标期刊 | 《社会学研究》《社会》《中国社会科学》等 | 《管理世界》《公共管理学报》《中国行政管理》等 |
| 驱动逻辑 | 学术脉络中的知识缺口 → 经验困惑 → 实证分析 → 理论对话 | 中国现实问题 → 理论反常或实践悖论 → 案例研究 → 机制建构 |
| 理论角色 | 在文献脉络中定位贡献 | 从案例中建构机制、概念或模型 |
| 方法偏好 | 量化实证、质性田野、理论分析、混合方法 | 单案例、多案例、纵向案例、嵌入式案例 |
| 结论风格 | 总结发现、回到知识脉络、讨论意义与局限 | 总结机制模型、强调理论贡献、实践启示和政策含义 |

### ask_user 提问

第二层可使用以下 ask_user 示例：

```text
question: "你的目标期刊风格是什么？"
header: "期刊风格"
options: [
  {label: "社会学研究", description: "以学术脉络中的知识缺口为驱动，适合社会学研究风格"},
  {label: "管理世界", description: "以中国现实问题、案例机制和理论贡献为驱动"},
  {label: "公共管理", description: "面向治理、政策执行、组织和公共问题"},
  {label: "尚未确定", description: "由 Skill 根据主题、方法和材料推荐"}
]
```

#### 问题四：你的目标期刊风格是什么？

可提示用户回答。

- 社会学研究风格
- 管理世界风格
- 公共管理风格
- 尚未确定

#### 问题五：你的研究方法是什么？

可提示用户回答。

- 量化实证
- 质性田野或深度访谈
- 案例研究
- 理论分析
- 混合方法

#### 问题六：你的预期字数是多少？

可提示用户回答。

- 1.5 万字以下
- 1.5 万到 2.5 万字
- 2.5 万字以上

### 范式判定规则

根据前面的回答，Skill 应综合判断。

- 社会学期刊 + 量化/理论方法 → 社会学研究范式
- 社会学期刊 + 质性田野/民族志 → 社会学研究范式
- 管理世界或公共管理期刊 + 案例研究 → 管理世界案例研究范式
- 跨期刊投稿 + 案例研究 + 关注实践问题 → 管理世界案例研究范式
- 跨期刊投稿 + 非案例方法 + 关注学术脉络 → 社会学研究范式

---

## 四、双层路由后的写作路径

### 1. 规范研究路径

推荐结构如下。

1. 问题提出
2. 概念界定
3. 理论资源
4. 规范标准
5. 争议与反驳
6. 制度或实践含义
7. 结论

推荐卡片如下。

- 概念辨析卡
- 规范论证卡
- 反驳卡
- 制度评价卡
- 结论卡

### 2. 实证研究路径

推荐结构如下。

1. 研究问题
2. 文献争议
3. 理论机制
4. 研究假设
5. 数据与变量
6. 模型与方法
7. 结果解释
8. 稳健性检验
9. 讨论与结论

推荐卡片如下。

- 引言卡
- 文献综述卡
- 理论机制卡
- 研究假设卡
- 变量操作化卡
- 模型设定卡
- 结果解释卡
- 讨论卡

### 3. 阐释研究路径

推荐结构如下。

1. 经验现象
2. 解释困惑
3. 概念工具
4. 材料来源
5. 案例叙述
6. 机制解释
7. 理论回扣
8. 结论

推荐卡片如下。

- 案例阐释卡
- 过程分析卡
- 话语分析卡
- 历史制度分析卡
- 理论回扣卡

### 4. 混合研究路径

推荐结构如下。

1. 经验问题
2. 方法困境
3. 理论资源
4. 技术或流程设计
5. 案例演示
6. 方法论反思
7. 适用边界
8. 结论

推荐卡片如下。

- 方法困境卡
- 流程设计卡
- 对照演示卡
- 审计层分析卡
- 方法论讨论卡
- 复杂度调节卡

---

## 五、两种发表范式下的结构差异

### 社会学研究范式

标准结构如下。

1. 标题 + 摘要 + 关键词
2. 引言
3. 文献综述 / 理论框架
4. 研究方法与数据
5. 经验分析 / 研究发现
6. 理论对话
7. 结论与讨论

### 管理世界案例研究范式

标准结构如下。

1. 标题 + 摘要 + 关键词
2. 引言
3. 文献综述与理论框架
4. 研究设计
5. 案例分析 / 研究发现
6. 理论贡献
7. 结论与启示

---

## 六、硬停止问题

出现以下情况时，Skill 不应直接跳入完整正文生成或派发 `chapter-draft-writer`，而应先提醒用户补充信息。

1. 用户要写实证论文，但没有提供数据来源、变量或模型
2. 用户要写文献综述，且既没有文献清单或检索范围，也没有 `02-literature/` 中 lit 阶段交接的 `review-evidence.csv`、`review-outline.md` 等证据材料
3. 用户要写案例分析，但没有提供案例材料
4. 用户要做规范评价，但没有说明评价标准
5. 用户要写方法论论文，但没有提供系统、流程、代码或案例材料
6. 用户只说要“润色”，但没有说明章节、目标期刊或文本用途

硬停止不等于拒绝。即使信息不足，也应输出一个基于现有信息的初步判断，并明确列出待确认项。

---

## 七、最终输出格式

完成双层判断后，Skill 应按以下格式输出。

### 一、研究方法协议判断

- 主类型
- 副类型
- 类型权重
- 判断依据

### 二、发表范式判断

- 目标范式
- 判定理由
- 与另一范式的差异

### 三、推荐写作路径

- 推荐结构
- 推荐章节顺序
- 当前最适合先写哪一部分
- `writing-dispatch-plan` 拆分方式：单章节 / 多章节并行 / 小节分批 / 段落任务包

### 四、推荐调用文件

- 章节标准文件
- 范文文件
- 提示词卡片
- `writing-dispatch-plan` 所需材料
- `chapter-draft-writer` 单任务包所需材料

### 五、硬停止问题与待确认项

- 当前缺失信息
- 用户需要补充的内容

### 六、范文截取脚本调用

路由完成后，调用 `example_extractor.py` 按范式和方法截取对应范文，避免加载全部 5 个文件：

```bash
python3 scripts/example_extractor.py \
  --paradigm {社会学研究范式|管理世界案例研究范式} \
  --method {量化实证|质性田野或深度访谈|案例研究} \
  --protocol {实证研究|规范研究|阐释研究|混合研究} \
  --out extracted_examples.md
```

截取后的文件仅包含当前路由所需的范文章节和提示词模板（约 8-15KB），大幅减少后续章节写作阶段的 token 消耗。

### 七、writing-dispatch-plan 与 chapter-draft-writer 输入包

进入新正文撰写前，主流程必须先把以下输入包传给 `agents/structure-writing-consultant.md`，生成 `writing-dispatch-plan`：

- 研究路由结果：方法协议、发表范式、风格梯度。
- 写作目标：全文、章节、分节或段落。
- 大纲或已有正文：章节结构、上下文位置和前后承接。
- 章节标准：对应 `chapters/ch*.md` 的硬性门槛。
- 范文截取：`example_extractor.py` 输出的相关模板。
- 证据材料：文献、数据、访谈、案例、图表或分析结果。
- 禁止声称内容：材料不足、未运行结果、未核验文献和用户明确排除内容。

`writing-dispatch-plan` 必须把写作目标拆成可派发任务包，每个任务包包含 `task_id`、章节/小节、段落功能、输入材料、章节标准、范文片段、证据映射、上下文边界、禁止声称内容和派发顺序。

随后主流程按 `writing-dispatch-plan` 把单个任务包传给 `agents/chapter-draft-writer.md`。每个 draft writer 输出必须保存为 `paper-workspace/_logs/agents/write-[YYYY-MM-DD]/paper-write-chapter-draft-writer--{task_id}.md`，不得覆盖其它任务。

所有 writer 输出完成后，主流程必须在 write 模块目录运行拼接脚本。若当前目录是 skill 包内的 ``，所有 `paper-workspace` 参数必须使用项目工作区绝对路径，避免误写到 skill 包内部：

```bash
python3 scripts/assemble_drafts.py \
  --plan /abs/project/paper-workspace/05-writing/plans/writing-dispatch-plan-[slug]-[YYYY-MM-DD].md \
  --draft-dir /abs/project/paper-workspace/_logs/agents/write-[YYYY-MM-DD] \
  --out /abs/project/paper-workspace/05-writing/drafts/draft-[slug]-[YYYY-MM-DD].md \
  --source-map /abs/project/paper-workspace/05-writing/assembly/source-map-[slug]-[YYYY-MM-DD].md \
  --json /abs/project/paper-workspace/05-writing/assembly/assembly-check-[slug]-[YYYY-MM-DD].json
```

拼接脚本负责按计划顺序合并各段草稿，并检查缺失任务、重复 `task_id`、空正文草稿和未被计划引用的 writer 输出。脚本失败时不得继续派发后续顾问。

拼接完成后，主 agent 必须阅读 `draft-[slug]-[YYYY-MM-DD].md`、`source-map-[slug]-[YYYY-MM-DD].md` 和 `assembly-check-[slug]-[YYYY-MM-DD].json`，将审查写入 `paper-workspace/05-writing/reviews/main-agent-review-[slug]-[YYYY-MM-DD].md`。主审查必须覆盖章节顺序、任务覆盖、段落来源、材料越界、缺失任务和不可声称内容。主审查完成后，再进入 `argument-consultant`、`material-integration-consultant`、`style-consultant` 文风总控和 `writing_scanner.py`。

---

## 八、与仓库其他文件的关系

- `resources/research_router.md`：总入口，负责方法协议和范式选择
- `chapters/`：具体章节写作标准
- `examples/`：范文和提示词模板
- `agents/structure-writing-consultant.md`：写作规划与 `writing-dispatch-plan` agent
- `agents/chapter-draft-writer.md`：按单个任务包撰写章节、分节或段落草稿 agent
- `agents/style-consultant.md`：全文文风总控 agent
- `scripts/method_router.py`：自动生成方法路由报告
- `scripts/assemble_drafts.py`：按 `writing-dispatch-plan` 拼接多个 writer 输出并生成 source map
- `scripts/writing_scanner.py`：语言反模式和合规扫描
- `scripts/complexity_analyzer.py`：文本复杂度诊断

---

## 九、总控提示词

```text
请启动 write module 的研究路由系统。

你必须先使用 ask_user，依次完成以下判断。

第一层是研究方法协议判断：
1. 研究问题属于哪一类
2. 主要材料是什么
3. 目标任务是什么

第二层是发表范式判断：
4. 目标期刊风格是什么
5. 研究方法是什么
6. 预期字数是多少

在用户回答后，请输出：

一、研究方法协议判断
二、发表范式判断
三、推荐写作路径
四、推荐调用文件
五、硬停止问题与待确认项

不要在没有完成上述判断前直接进入完整正文生成，也不要越过 `structure-writing-consultant` 的 `writing-dispatch-plan` 直接派发 chapter-draft-writer。生成新正文时，不得跳过 `assemble_drafts.py` 拼接和主 agent 阅读审查。
不要虚构文献、数据、变量、案例和结论。
如果信息不足，先给出初步判断，再列出需要补充的内容。
```
