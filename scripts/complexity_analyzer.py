#!/usr/bin/env python3
"""
write module 文本复杂度分析器。

定位：
  1. 计算中文社会科学文本的句法、词汇、篇章、论证和模板化风险。
  2. 输出 Markdown 或 JSON 报告。
  3. 只做诊断和改写建议，不自动替换原文。

用法：
  python3 scripts/complexity_analyzer.py paper.md
  python3 scripts/complexity_analyzer.py paper.md --json
  python3 scripts/complexity_analyzer.py paper.md --out complexity_report.md
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


SENT_SPLIT_RE = re.compile(r"[。！？!?；;]")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
WORD_RE = re.compile(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z\-]+|\d+(?:\.\d+)?")

ACADEMIC_TERMS = [
    "制度", "机制", "结构", "行动者", "合法性", "治理", "公共性", "国家", "社会", "组织",
    "变量", "模型", "样本", "回归", "假设", "因果", "识别", "稳健性", "异质性", "中介", "调节",
    "规范", "价值", "正当性", "概念", "理论", "范式", "方法论", "阐释", "话语", "文本",
    "基础设施", "可复现", "自动化", "审计", "复杂度", "分类", "路由", "协议",
]

ABSTRACT_SUFFIXES = ("性", "化", "度", "主义", "机制", "结构", "逻辑", "范式", "过程", "能力", "意识")

CONNECTORS = [
    "因此", "所以", "但是", "然而", "不过", "同时", "此外", "进而", "从而", "由于", "因为",
    "首先", "其次", "最后", "一方面", "另一方面", "换言之", "也就是说", "由此", "进一步",
]

TEMPLATE_PATTERNS = [
    r"具有重要意义", r"提供了新的视角", r"在一定程度上", r"值得注意的是", r"综上所述",
    r"随着.{0,20}发展", r"本文从.{0,30}出发", r"不仅.{0,40}而且", r"不是.{0,80}而是",
    r"一方面.{0,80}另一方面", r"通过.{2,40}来", r"对.{2,40}进行",
]

ARGUMENT_MARKERS = [
    "研究问题", "问题意识", "理论机制", "研究假设", "数据", "变量", "模型", "案例", "材料",
    "发现", "结果", "讨论", "贡献", "局限", "边界", "解释", "机制", "证据",
]


@dataclass
class ComplexityReport:
    file: str
    char_count: int
    sentence_count: int
    paragraph_count: int
    avg_sentence_len: float
    sentence_len_std: float
    long_sentence_ratio: float
    avg_paragraph_len: float
    lexical_diversity: float
    term_density: float
    abstract_word_density: float
    connector_density: float
    template_risk_density: float
    argument_marker_density: float
    punctuation_entropy: float
    syntactic_score: float
    lexical_score: float
    discourse_score: float
    argument_score: float
    anti_template_score: float
    overall_score: float
    level: str
    advice: list[str]


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", text)
    text = re.sub(r"\[[^\]]+\]\([^\)]*\)", "", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\|.*\|$", "", text, flags=re.MULTILINE)
    return text


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) >= 20]


def split_sentences(text: str) -> list[str]:
    sentences = [s.strip() for s in SENT_SPLIT_RE.split(text) if len(s.strip()) >= 2]
    return sentences


def tokenize(text: str) -> list[str]:
    return WORD_RE.findall(text)


def count_matches(patterns: Iterable[str], text: str) -> int:
    total = 0
    for pat in patterns:
        total += len(re.findall(pat, text))
    return total


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def safe_ratio(num: float, den: float) -> float:
    return num / den if den else 0.0


def entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((v / total) * math.log(v / total, 2) for v in counter.values())


def analyze_text(text: str, source: str = "<memory>") -> ComplexityReport:
    clean = strip_markdown(text)
    paragraphs = split_paragraphs(clean)
    joined = "\n\n".join(paragraphs) if paragraphs else clean
    sentences = split_sentences(joined)
    words = tokenize(joined)

    char_count = len(CHINESE_RE.findall(joined))
    sentence_count = len(sentences)
    paragraph_count = len(paragraphs)
    sent_lengths = [len(CHINESE_RE.findall(s)) for s in sentences]
    para_lengths = [len(CHINESE_RE.findall(p)) for p in paragraphs]

    avg_sentence_len = statistics.mean(sent_lengths) if sent_lengths else 0.0
    sentence_len_std = statistics.pstdev(sent_lengths) if len(sent_lengths) >= 2 else 0.0
    long_sentence_ratio = safe_ratio(sum(1 for x in sent_lengths if x > 90), len(sent_lengths))
    avg_paragraph_len = statistics.mean(para_lengths) if para_lengths else 0.0

    word_count = len(words)
    unique_words = len(set(words))
    lexical_diversity = safe_ratio(unique_words, word_count)

    term_hits = sum(joined.count(t) for t in ACADEMIC_TERMS)
    term_density = safe_ratio(term_hits, max(char_count, 1)) * 1000

    abstract_hits = sum(1 for w in words if w.endswith(ABSTRACT_SUFFIXES))
    abstract_word_density = safe_ratio(abstract_hits, max(word_count, 1))

    connector_hits = sum(joined.count(c) for c in CONNECTORS)
    connector_density = safe_ratio(connector_hits, max(sentence_count, 1))

    template_hits = count_matches(TEMPLATE_PATTERNS, joined)
    template_risk_density = safe_ratio(template_hits, max(sentence_count, 1))

    argument_hits = sum(joined.count(m) for m in ARGUMENT_MARKERS)
    argument_marker_density = safe_ratio(argument_hits, max(paragraph_count, 1))

    punctuation_counter = Counter(ch for ch in joined if ch in "，。；：！？、（）《》“”")
    punctuation_entropy = entropy(punctuation_counter)

    # 评分逻辑：不是越复杂越好，而是看是否处于中文社科论文的可控区间。
    syntactic_score = 100
    syntactic_score -= abs(avg_sentence_len - 45) * 0.9
    syntactic_score -= long_sentence_ratio * 70
    syntactic_score += min(sentence_len_std, 35) * 0.25
    syntactic_score = clamp(syntactic_score)

    lexical_score = 100
    lexical_score -= abs(lexical_diversity - 0.55) * 80
    lexical_score += min(term_density, 18) * 1.8
    lexical_score += min(abstract_word_density, 0.45) * 20
    lexical_score = clamp(lexical_score)

    discourse_score = 100
    discourse_score -= abs(avg_paragraph_len - 230) * 0.08
    if connector_density > 0.75:
        discourse_score -= (connector_density - 0.75) * 35
    discourse_score += min(punctuation_entropy, 3.0) * 4
    discourse_score = clamp(discourse_score)

    argument_score = clamp(60 + argument_marker_density * 7, 0, 100)
    anti_template_score = clamp(100 - template_risk_density * 80)

    overall_score = (
        0.25 * syntactic_score
        + 0.25 * lexical_score
        + 0.23 * discourse_score
        + 0.12 * argument_score
        + 0.15 * anti_template_score
    )

    if overall_score >= 80:
        level = "稳定"
    elif overall_score >= 65:
        level = "可用"
    elif overall_score >= 50:
        level = "需修订"
    else:
        level = "高风险"

    advice: list[str] = []
    if avg_sentence_len > 65:
        advice.append("平均句长偏高。建议拆分长句，把条件、机制和结论分别写成独立句。")
    if long_sentence_ratio > 0.2:
        advice.append("长句比例偏高。优先处理超过 90 字的句子。")
    if avg_paragraph_len > 350:
        advice.append("段落偏长。建议按一个段落只承担一个论证任务的原则拆分。")
    if template_risk_density > 0.18:
        advice.append("模板化表达密度偏高。建议删除空泛意义句，改为问题、材料或机制陈述。")
    if connector_density > 0.75:
        advice.append("连接词密度偏高。建议减少机械过渡词，让段落内部逻辑承担衔接功能。")
    if not advice:
        advice.append("复杂度处于可控范围。建议继续结合章节标准进行人工通读。")

    return ComplexityReport(
        file=source,
        char_count=char_count,
        sentence_count=sentence_count,
        paragraph_count=paragraph_count,
        avg_sentence_len=round(avg_sentence_len, 2),
        sentence_len_std=round(sentence_len_std, 2),
        long_sentence_ratio=round(long_sentence_ratio, 3),
        avg_paragraph_len=round(avg_paragraph_len, 2),
        lexical_diversity=round(lexical_diversity, 3),
        term_density=round(term_density, 3),
        abstract_word_density=round(abstract_word_density, 3),
        connector_density=round(connector_density, 3),
        template_risk_density=round(template_risk_density, 3),
        argument_marker_density=round(argument_marker_density, 3),
        punctuation_entropy=round(punctuation_entropy, 3),
        syntactic_score=round(syntactic_score, 2),
        lexical_score=round(lexical_score, 2),
        discourse_score=round(discourse_score, 2),
        argument_score=round(argument_score, 2),
        anti_template_score=round(anti_template_score, 2),
        overall_score=round(overall_score, 2),
        level=level,
        advice=advice,
    )


def to_markdown(report: ComplexityReport) -> str:
    rows = [
        ("中文字符数", report.char_count),
        ("句子数", report.sentence_count),
        ("段落数", report.paragraph_count),
        ("平均句长", report.avg_sentence_len),
        ("句长标准差", report.sentence_len_std),
        ("长句比例", report.long_sentence_ratio),
        ("平均段落长度", report.avg_paragraph_len),
        ("词汇多样性", report.lexical_diversity),
        ("术语密度", report.term_density),
        ("抽象词密度", report.abstract_word_density),
        ("连接词密度", report.connector_density),
        ("模板化风险密度", report.template_risk_density),
        ("论证标记密度", report.argument_marker_density),
        ("标点熵", report.punctuation_entropy),
    ]
    score_rows = [
        ("句法复杂度", report.syntactic_score),
        ("词汇复杂度", report.lexical_score),
        ("篇章复杂度", report.discourse_score),
        ("论证复杂度", report.argument_score),
        ("反模板化得分", report.anti_template_score),
        ("综合复杂度", report.overall_score),
    ]

    lines = [f"# 文本复杂度报告：{Path(report.file).name}\n"]
    lines.append(f"**综合判断**：{report.level}\n")
    lines.append("## 基础指标\n")
    lines.append("| 指标 | 数值 |")
    lines.append("| --- | ---: |")
    for name, value in rows:
        lines.append(f"| {name} | {value} |")

    lines.append("\n## 复杂度得分\n")
    lines.append("| 维度 | 得分 |")
    lines.append("| --- | ---: |")
    for name, value in score_rows:
        lines.append(f"| {name} | {value} |")

    lines.append("\n## 修改建议\n")
    for item in report.advice:
        lines.append(f"- {item}")

    lines.append("\n## 解释\n")
    lines.append("综合复杂度不是越高越好。`write module` 将中文社会科学论文的目标状态设为可控复杂度，也就是句法不过度堆叠，词汇保持学术密度，篇章衔接清楚，模板化表达较低。")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="write module 文本复杂度分析器")
    parser.add_argument("file", help="待分析的 Markdown 或文本文件")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--out", help="输出报告路径")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"文件不存在：{args.file}")
        return 1

    text = path.read_text(encoding="utf-8")
    report = analyze_text(text, str(path))

    if args.json:
        output = json.dumps(asdict(report), ensure_ascii=False, indent=2)
    else:
        output = to_markdown(report)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"复杂度报告已保存 → {args.out}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
