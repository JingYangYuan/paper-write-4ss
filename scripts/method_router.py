#!/usr/bin/env python3
"""
write module 方法路由器。

定位：
  1. 从研究主题、摘要或草稿中识别研究方法类型。
  2. 输出规范研究、实证研究、阐释研究、混合研究四类权重。
  3. 给出推荐路径、提示词卡片和硬停止问题。

用法：
  python3 scripts/method_router.py paper.md
  python3 scripts/method_router.py paper.md --json
  python3 scripts/method_router.py paper.md --out route_report.md
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path


KEYWORDS = {
    "normative": [
        "应当", "应该", "规范", "正当性", "合法性", "价值", "伦理", "公共性", "公平", "正义",
        "制度评价", "批判", "概念辨析", "理论批判", "权利", "义务", "责任",
    ],
    "empirical": [
        "变量", "模型", "回归", "数据", "样本", "问卷", "假设", "显著", "稳健性", "异质性",
        "中介", "调节", "因变量", "自变量", "DID", "OLS", "Logit", "面板", "固定效应", "SNA",
        "实验", "文本分析", "网络分析", "操作化", "识别策略",
    ],
    "interpretive": [
        "案例", "访谈", "田野", "民族志", "档案", "历史", "话语", "文本", "行动者", "意义",
        "过程", "情境", "叙事", "制度过程", "政策过程", "阐释", "理解", "实践逻辑",
    ],
    "mixed": [
        "方法论", "AI", "Agent", "Skill", "智能体", "流程", "协议", "路由", "审计", "基础设施",
        "可复现", "自动化", "复杂度", "扫描器", "脚本", "Python", "代码", "日志", "系统设计",
    ],
}

CARDS = {
    "normative": ["概念辨析卡", "规范论证卡", "反驳卡", "制度评价卡", "结论卡"],
    "empirical": ["引言卡", "文献综述卡", "理论机制卡", "研究假设卡", "变量操作化卡", "模型设定卡", "结果解释卡", "讨论卡"],
    "interpretive": ["案例阐释卡", "过程分析卡", "话语分析卡", "历史制度分析卡", "理论回扣卡"],
    "mixed": ["方法困境卡", "流程设计卡", "对照演示卡", "审计层分析卡", "方法论讨论卡", "复杂度调节卡"],
}

ROUTES = {
    "normative": "规范研究路径",
    "empirical": "实证研究路径",
    "interpretive": "阐释研究路径",
    "mixed": "混合研究路径",
}

ROUTE_STRUCTURES = {
    "normative": ["问题提出", "概念界定", "理论资源", "规范标准", "争议与反驳", "制度或实践含义", "结论"],
    "empirical": ["研究问题", "文献争议", "理论机制", "研究假设", "数据与变量", "模型与方法", "结果解释", "稳健性检验", "讨论与结论"],
    "interpretive": ["经验现象", "解释困惑", "概念工具", "材料来源", "案例叙述", "机制解释", "理论回扣", "结论"],
    "mixed": ["经验问题", "方法困境", "理论资源", "技术或流程设计", "案例演示", "方法论反思", "适用边界", "结论"],
}


@dataclass
class RouteReport:
    file: str
    scores: dict[str, float]
    primary_type: str
    secondary_type: str | None
    primary_route: str
    secondary_route: str | None
    route_structure: list[str]
    prompt_cards: list[str]
    hard_stop_questions: list[str]
    evidence: dict[str, list[str]]


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    return text


def collect_evidence(text: str) -> dict[str, list[str]]:
    evidence: dict[str, list[str]] = {}
    for key, kws in KEYWORDS.items():
        hits = []
        for kw in kws:
            if re.search(re.escape(kw), text, flags=re.IGNORECASE):
                hits.append(kw)
        evidence[key] = hits
    return evidence


def normalize_scores(raw: dict[str, float]) -> dict[str, float]:
    total = sum(raw.values())
    if total <= 0:
        return {k: 0.25 for k in raw}
    return {k: round(v / total, 3) for k, v in raw.items()}


def infer_hard_stops(text: str, primary: str) -> list[str]:
    stops: list[str] = []

    has_data = re.search(r"数据|样本|变量|模型|回归|问卷|访谈|案例|档案|文本", text, re.IGNORECASE)
    has_lit = re.search(r"文献|研究|理论|综述|学者|指出|认为|发现", text)
    has_method = re.search(r"方法|模型|回归|访谈|案例|文本分析|网络分析|DID|SNA|OLS|Logit|民族志", text, re.IGNORECASE)
    has_norm = re.search(r"标准|原则|价值|正当性|合法性|伦理|公共性", text)

    if primary == "empirical":
        if not has_data:
            stops.append("实证路径缺少数据来源、样本、变量或模型信息。")
        if not has_method:
            stops.append("实证路径缺少方法设定。需说明使用 OLS、Logit、DID、SNA、文本分析或其他方法。")
    elif primary == "interpretive":
        if not re.search(r"案例|访谈|田野|档案|历史|文本|话语|政策", text):
            stops.append("阐释路径缺少案例、访谈、文本、档案或历史材料。")
    elif primary == "normative":
        if not has_norm:
            stops.append("规范路径缺少明确的评价标准，例如正当性、合法性、公共性、效率、公平或伦理原则。")
    elif primary == "mixed":
        if not has_method:
            stops.append("混合路径缺少方法或流程说明。需说明系统、脚本、协议、案例或对照材料。")

    if not has_lit:
        stops.append("未检测到清晰的文献或理论资源。写作文献综述、理论机制或讨论部分前需要补充。")

    if not stops:
        stops.append("未触发硬停止。仍需在生成正文前人工确认研究对象、目标章节和目标期刊。")
    return stops


def route_text(text: str, source: str = "<memory>") -> RouteReport:
    clean = strip_markdown(text)
    evidence = collect_evidence(clean)
    raw = {k: len(v) + 0.2 for k, v in evidence.items()}

    # 结构性加权。
    if re.search(r"研究假设|因变量|自变量|稳健性|固定效应|操作化", clean):
        raw["empirical"] += 2.0
    if re.search(r"方法论|基础设施|可复现|审计|复杂度|Skill|Agent", clean, re.IGNORECASE):
        raw["mixed"] += 2.0
    if re.search(r"访谈材料|田野材料|历史过程|话语分析|政策文本", clean):
        raw["interpretive"] += 1.5
    if re.search(r"正当性|规范基础|价值标准|制度评价", clean):
        raw["normative"] += 1.5

    scores = normalize_scores(raw)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = ranked[0][0]
    secondary = ranked[1][0] if ranked[1][1] >= 0.22 else None

    cards = CARDS[primary][:]
    if secondary:
        cards.extend([c for c in CARDS[secondary][:2] if c not in cards])

    return RouteReport(
        file=source,
        scores=scores,
        primary_type=primary,
        secondary_type=secondary,
        primary_route=ROUTES[primary],
        secondary_route=ROUTES[secondary] if secondary else None,
        route_structure=ROUTE_STRUCTURES[primary],
        prompt_cards=cards,
        hard_stop_questions=infer_hard_stops(clean, primary),
        evidence=evidence,
    )


def cn_type(key: str | None) -> str:
    mapping = {
        "normative": "规范研究",
        "empirical": "实证研究",
        "interpretive": "阐释研究",
        "mixed": "混合研究",
        None: "无",
    }
    return mapping.get(key, key or "无")


def to_markdown(report: RouteReport) -> str:
    lines = [f"# 方法路由报告：{Path(report.file).name}\n"]
    lines.append("## 一、类型权重\n")
    lines.append("| 类型 | 权重 | 命中证据 |")
    lines.append("| --- | ---: | --- |")
    for key, score in report.scores.items():
        evidence = "、".join(report.evidence.get(key, [])[:12]) or "未明显命中"
        lines.append(f"| {cn_type(key)} | {score:.3f} | {evidence} |")

    lines.append("\n## 二、路由结果\n")
    lines.append(f"主类型：{cn_type(report.primary_type)}")
    lines.append(f"副类型：{cn_type(report.secondary_type)}")
    lines.append(f"主路径：{report.primary_route}")
    if report.secondary_route:
        lines.append(f"副路径：{report.secondary_route}")

    lines.append("\n## 三、推荐结构\n")
    for i, item in enumerate(report.route_structure, start=1):
        lines.append(f"{i}. {item}")

    lines.append("\n## 四、建议调用的提示词卡片\n")
    for card in report.prompt_cards:
        lines.append(f"- {card}")

    lines.append("\n## 五、硬停止与待确认项\n")
    for item in report.hard_stop_questions:
        lines.append(f"- {item}")

    lines.append("\n## 六、使用建议\n")
    lines.append("先用本报告确定方法路径，再读取 `resources/research_router.md` 确定目标期刊风格，最后进入 `chapters/` 和 `examples/` 调用章节标准与提示词。")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="write module 方法路由器")
    parser.add_argument("file", help="待判断的 Markdown 或文本文件")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--out", help="输出报告路径")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"文件不存在：{args.file}")
        return 1

    text = path.read_text(encoding="utf-8")
    report = route_text(text, str(path))

    if args.json:
        output = json.dumps(asdict(report), ensure_ascii=False, indent=2)
    else:
        output = to_markdown(report)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"方法路由报告已保存 → {args.out}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
