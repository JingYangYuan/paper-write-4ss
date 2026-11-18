#!/usr/bin/env python3
"""草稿硬闸门（draft gate）：子代理写手输出不过闸，assemble_drafts 拒收。

解决的三个老问题：
  1. 写手不守提示词：输出结构残缺、字数跑偏、任务包外扩写——结构化校验拦下。
  2. AI 味与防御性写法混进正文：正文草稿经 writing_scanner 全规则扫描（含全篇
     预算制），high 不归零不过闸。
  3. 引文张冠李戴：正文里每个「作者（年份）」夹注必须在「草稿元数据」的
     citations_used 中申报出处（证据表行或材料编号），未申报即拒收。

用法：
  python3 scripts/draft_gate.py <writer-draft.md> [--task-id W3] [--json out.json]

退出码：0 通过；1 拒收（errors 非空）。
写手输出契约见 agents/chapter-draft-writer.md：Markdown 各节 + `## 草稿元数据`
下的 ```json 块（task_id / chapter / target_words / actual_words /
citations_used / materials_used / constraints_ack）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from writing_scanner import scan_all  # noqa: E402

REQUIRED_SECTIONS = ("参考库回查", "任务包", "正文草稿", "使用材料清单", "草稿元数据")

_INTEXT_CITE = re.compile(
    r"([一-鿿·]{2,4}|[A-Z][A-Za-zÀ-ÿ\-]+)"
    r"(?:\s+et\s+al\.?|、[一-鿿·]{2,4})?[（(](\d{4})[）)]"
)

_WORD_TOLERANCE = 0.30  # 字数允许 ±30%


def _section(text: str, heading: str) -> str:
    pat = re.compile(rf"^##\s*{re.escape(heading)}\s*$", re.MULTILINE)
    m = pat.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s+\S+", rest, re.MULTILINE)
    return rest[:nxt.start()] if nxt else rest


def _extract_json_block(section_text: str) -> dict | None:
    m = re.search(r"```json\s*(\{.*?\})\s*```", section_text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _count_words(body: str) -> int:
    cleaned = re.sub(r"[#*`>|\-]", "", body)
    return len(re.sub(r"\s", "", cleaned))


def _format_decoration_errors(body: str) -> list[str]:
    errors: list[str] = []
    for line_no, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("```"):
            errors.append(f"正文草稿第 {line_no} 行含代码块 fence。")
        if "<!--" in stripped or "-->" in stripped:
            errors.append(f"正文草稿第 {line_no} 行含 HTML 注释。")
        if re.search(r"\*\*[^*\n]+\*\*", stripped):
            errors.append(f"正文草稿第 {line_no} 行含 Markdown 加粗。")
        if re.match(r"^\|.*\|$", stripped):
            errors.append(f"正文草稿第 {line_no} 行含 Markdown 表格。")
        if stripped.startswith(">"):
            errors.append(f"正文草稿第 {line_no} 行含引用块。")
        if re.match(r"^[-*+]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            errors.append(f"正文草稿第 {line_no} 行含列表项（正文只允许标题与自然段）。")
        if re.search(r"mermaid", stripped, re.IGNORECASE):
            errors.append(f"正文草稿第 {line_no} 行疑似 Mermaid。")
    return errors


def validate_writer_file(path: Path, expect_task_id: str | None = None) -> tuple[list[str], dict]:
    """返回 (errors, meta)。errors 非空即拒收。"""
    errors: list[str] = []
    meta: dict = {}
    text = path.read_text(encoding="utf-8", errors="replace")

    # 1. 结构完整
    for sec in REQUIRED_SECTIONS:
        if not _section(text, sec).strip():
            errors.append(f"缺少非空 `## {sec}` 节。")

    meta_section = _section(text, "草稿元数据")
    body = _section(text, "正文草稿")
    if not body.strip():
        return errors, meta

    # 2. 元数据 JSON 合法且字段齐
    parsed = _extract_json_block(meta_section)
    if parsed is None:
        errors.append("`## 草稿元数据` 缺少合法的 ```json 代码块（无法解析）。")
    else:
        meta = parsed
        for field in ("task_id", "chapter", "actual_words", "citations_used", "constraints_ack"):
            if field not in parsed:
                errors.append(f"草稿元数据缺字段 `{field}`。")
        ack = parsed.get("constraints_ack") or {}
        if isinstance(ack, dict):
            for key, label in (
                ("no_preview", "不写前向结构预告"),
                ("no_defense", "不写防御性辩护"),
                ("no_buzz", "不用管理学黑话"),
            ):
                if not ack.get(key):
                    errors.append(f"constraints_ack.{key} 未确认为 true（{label}）。")

        # task_id 一致性
        declared_id = str(parsed.get("task_id", "")).strip()
        if not declared_id:
            errors.append("草稿元数据 task_id 为空。")
        elif expect_task_id and declared_id != expect_task_id:
            errors.append(f"task_id 不符：元数据={declared_id}，期望={expect_task_id}。")

        # 3. 字数（申报值与实测值都要过）
        actual = _count_words(body)
        if "actual_words" in parsed and abs(int(parsed["actual_words"] or 0) - actual) > max(30, actual * 0.1):
            errors.append(f"actual_words 申报 {parsed['actual_words']}，实测 {actual}，相差过大（按无空白字符计）。")
        tw = parsed.get("target_words")
        if isinstance(tw, list) and len(tw) == 2 and all(isinstance(x, int) for x in tw):
            lo, hi = tw
            lo_eff, hi_eff = lo * (1 - _WORD_TOLERANCE), hi * (1 + _WORD_TOLERANCE)
            if not (lo_eff <= actual <= hi_eff):
                errors.append(f"字数 {actual} 超出任务包目标 [{lo},{hi}] 的 ±30% 区间 [{int(lo_eff)},{int(hi_eff)}]。")

    # 4. 正文装饰禁令
    errors.extend(_format_decoration_errors(body))

    # 5. 扫描器全规则（含预算制）：high 必须为 0
    issues = scan_all(body)
    highs = [i for i in issues if i.severity == "high"]
    for iss in highs[:20]:
        errors.append(f"扫描器 high 未归零 [{iss.rule_id}] {iss.detail}｜片段：{iss.context[:80]}")
    if len(highs) > 20:
        errors.append(f"……另有 {len(highs) - 20} 条 high 未列出。")

    # 6. 引文申报（张冠李戴闸门）
    if parsed is not None:
        declared = set()
        for c in parsed.get("citations_used") or []:
            if isinstance(c, dict) and "author" in c and "year" in c:
                declared.add((str(c["author"]), str(c["year"])))
        in_text = set(_INTEXT_CITE.findall(body))
        for name, year in sorted(in_text):
            hit = any(name in d or d in name for d, y in declared if y == year)
            if not hit:
                errors.append(
                    f"正文夹注 {name}（{year}）未在 citations_used 申报出处——"
                    f"写手必须给每个引用声明证据来源（证据表行/材料编号），否则视为疑似张冠李戴。"
                )
        # 申报了出处但没写进正文的引用不算错（可能支撑的是数据而非观点）

    return errors, meta


def main() -> int:
    parser = argparse.ArgumentParser(description="草稿硬闸门：不过闸不拼接")
    parser.add_argument("file", help="写手输出 Markdown 文件")
    parser.add_argument("--task-id", help="期望的 task_id（来自 writing-dispatch-plan）")
    parser.add_argument("--json", dest="json_out", help="判定结果 JSON 输出路径")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"❌ 文件不存在：{path}")
        return 1

    errors, meta = validate_writer_file(path, args.task_id)
    verdict = {
        "file": str(path),
        "task_id": meta.get("task_id") or args.task_id,
        "status": "pass" if not errors else "fail",
        "error_count": len(errors),
        "errors": errors,
    }
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"判定结果 → {args.json_out}")
    if errors:
        print(f"❌ 拒收：{len(errors)} 项未过闸")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("✅ 通过：结构、字数、扫描器 high=0、引文申报全部合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
