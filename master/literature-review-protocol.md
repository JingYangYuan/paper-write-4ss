# Literature Review Writing Protocol

本协议是 lit 与 write 共用的综述写作接口。lit 负责可追溯的文献、证据和论证准备；write 负责将这些材料写成可直接进入论文的章节。用户直接要求“写文献综述”时，lit 完成准备后必须按本协议调用 write 的写作流程，不得另起一套正文模板。

## 1. 共享输入

准备和改写综述前，先读取以下项目内材料：

- 02-literature/paper-registry.csv：题录、稳定 paper_id、PDF/全文路径、处理状态和 citation key。
- 02-literature/review-evidence.csv：正文判断与原文证据的唯一映射表。
- 02-literature/review-outline.md：研究问题、段落顺序、每段承担的论证动作和引用的 claim ID。
- 02-literature/review-gaps.md：未能成文的判断、缺少的全文或不可声称内容。

其中 review-evidence.csv 至少包含以下字段：

    claim_id,paragraph_id,argument_role,claim,stance,paper_id,citation_key,evidence_level,
    source_location,source_excerpt,study_design_or_text,scope_conditions,
    permitted_paraphrase,not_supported,review_status

- evidence_level 只能为 fulltext、abstract、theory_text 或 unverified。
- fulltext、theory_text 用于机制、方法批评、效应量、争议判断和强空白判断，必须给出页码、章节或可定位段落。
- abstract 只能支持摘要明确陈述的研究对象、设计和概括性发现，不能扩写为机制、因果或领域共识。
- unverified 不得进入正文，只能留在 review-gaps.md。

## 2. 论证与空白规则

- 段落围绕一个可争论判断写作，比较文献在概念、对象、材料、方法和情境上的关系，再说明它们是互补、冲突还是不可直接比较。允许一处判断由多篇文献分组支持。
- 段落须推进研究问题或理论对话，不按数据库、国别或“作者逐篇发现”组织。
- 每个研究不足必须说明检索范围、最近先例、已覆盖内容、仍未解释的具体问题及其理论意义。未检索到只可表述为“在本次检索范围内尚未发现”。
- “非显著”“证据接近零”和“证据不足”必须分别处理。换一个人群、数据或方法本身不构成贡献。
- 理论、规范和阐释研究以概念区分、论证前提、竞争立场、反例/反诠释与文本出处组织，不强制使用变量、机制或实证发现结构。

## 3. 交付与改写

- 正文唯一落点为 05-writing/literature-review.md。它只包含标题层级、自然段和实际引用的参考文献，不包含检索日志、文献地图、证据表、待补证据或 Mermaid。
- 综述正文由 write 按其审查和文风流程生成；字数、分节和语言比例以用户要求和目标期刊为准，既有范文只作可选结构参考。
- 修改已有综述前，先在 review-evidence.csv 标记保留、修改、移除或新增的 claim，并将失效判断移入 review-gaps.md。不得在没有证据映射的情况下静默改写核心论证。
- 关键证据尚未满足时，可以交付边界明确的初稿；正文外记录缺口，不得将未验证的机制、共识或空白写成定论。

## 4. 复核

交付前检查：

1. 每个关键判断、争议、方法批评和效应数值均能回查 claim_id 与原文位置。
2. 正文每一段都在 review-outline.md 中有对应的论证任务，并使用已核验的 claim。
3. 文后参考文献只列正文实际引用的条目，且均可回查 paper_id 或理论文本出处。
4. review-gaps.md 中的未核验内容没有进入正文。
