#!/usr/bin/env python3
"""Assemble write-module draft fragments produced by chapter draft writers.

The script is intentionally standard-library only. It validates that every
task_id in a writing-dispatch-plan has exactly one writer output, then extracts
the writer's body section and creates a combined draft plus a source map. When
--manuscript is provided, it also renders a clean manuscript that contains only
paper headings and body paragraphs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


WRITER_PREFIX = "paper-write-chapter-draft-writer--"
WRITER_SECTION_HEADINGS = (
    "任务包",
    "正文草稿",
    "使用材料清单",
    "未使用材料",
    "待补证据",
    "不可声称内容",
)
FORBIDDEN_MANUSCRIPT_HEADINGS = {
    "任务包",
    "使用材料清单",
    "未使用材料",
    "待补证据",
    "不可声称内容",
    "文风总控处理记录",
    "判断",
    "依据",
    "风险",
    "建议",
}


@dataclass
class WriterDraft:
    task_id: str
    path: Path
    task_pack: str
    body: str
    materials: str
    evidence_gaps: str
    forbidden_claims: str


def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def parse_plan_task_ids(plan_text: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    task_ids: list[str] = []
    lines = plan_text.splitlines()
    i = 0
    while i < len(lines):
        cells = split_markdown_row(lines[i])
        lowered = [cell.strip().lower() for cell in cells]
        if "task_id" not in lowered:
            i += 1
            continue
        task_col = lowered.index("task_id")
        i += 1
        while i < len(lines):
            row = split_markdown_row(lines[i])
            if not row:
                break
            if is_separator_row(row):
                i += 1
                continue
            if task_col >= len(row):
                errors.append(f"计划表存在缺少 task_id 列的行: {lines[i].strip()}")
                i += 1
                continue
            task_id = normalize_task_id(row[task_col])
            if task_id:
                task_ids.append(task_id)
            i += 1
        break
    if not task_ids:
        errors.append("writing-dispatch-plan 中未解析到任何 task_id。")

    duplicates = sorted({tid for tid in task_ids if task_ids.count(tid) > 1})
    if duplicates:
        errors.append("writing-dispatch-plan 存在重复 task_id: " + ", ".join(duplicates))
    return task_ids, errors


def normalize_task_id(value: str) -> str:
    value = value.strip().strip("`")
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", "-", value)
    return value


def section(text: str, heading: str) -> str:
    start_pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    start = start_pattern.search(text)
    if not start:
        return ""
    content_start = text.find("\n", start.end())
    if content_start == -1:
        return ""
    content_start += 1

    stop_headings = [re.escape(item) for item in WRITER_SECTION_HEADINGS if item != heading]
    stop_pattern = re.compile(rf"^##\s+(?:{'|'.join(stop_headings)})\s*$", re.MULTILINE)
    stop = stop_pattern.search(text, content_start)
    content_end = stop.start() if stop else len(text)
    return text[content_start:content_end].strip()


def writer_task_id(path: Path) -> str | None:
    stem = path.stem
    if not stem.startswith(WRITER_PREFIX):
        return None
    task_id = stem[len(WRITER_PREFIX) :]
    return normalize_task_id(task_id)


def collect_writer_files(draft_dir: Path) -> tuple[dict[str, Path], list[str]]:
    errors: list[str] = []
    files_by_task: dict[str, Path] = {}
    for path in sorted(draft_dir.glob(f"{WRITER_PREFIX}*.md")):
        task_id = writer_task_id(path)
        if not task_id:
            continue
        if task_id in files_by_task:
            errors.append(
                f"发现重复 writer 输出 task_id={task_id}: {files_by_task[task_id]} ; {path}"
            )
            continue
        files_by_task[task_id] = path
    return files_by_task, errors


def read_writer(path: Path, task_id: str) -> tuple[WriterDraft | None, list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    task_pack = section(text, "任务包")
    body = section(text, "正文草稿")
    materials = section(text, "使用材料清单")
    evidence_gaps = section(text, "待补证据")
    forbidden_claims = section(text, "不可声称内容")

    if not task_pack:
        errors.append(f"{path} 缺少 `## 任务包`。")
    if not body:
        errors.append(f"{path} 缺少非空 `## 正文草稿`。")
    if errors:
        return None, errors
    return (
        WriterDraft(
            task_id=task_id,
            path=path,
            task_pack=task_pack,
            body=body,
            materials=materials,
            evidence_gaps=evidence_gaps,
            forbidden_claims=forbidden_claims,
        ),
        [],
    )


def write_outputs(
    plan: Path,
    out: Path,
    source_map: Path,
    ordered: list[WriterDraft],
    manuscript: Path | None = None,
) -> None:
    generated = datetime.now().isoformat(timespec="seconds")
    out.parent.mkdir(parents=True, exist_ok=True)
    source_map.parent.mkdir(parents=True, exist_ok=True)
    if manuscript is not None:
        manuscript.parent.mkdir(parents=True, exist_ok=True)

    draft_lines = [
        f"# 合并草稿：{plan.stem}",
        "",
        f"- Generated at: {generated}",
        f"- Source plan: `{plan}`",
        f"- Task count: {len(ordered)}",
        "",
    ]
    for item in ordered:
        draft_lines.extend(
            [
                f"## {item.task_id}",
                "",
                f"<!-- source: {item.path} -->",
                "",
                item.body,
                "",
            ]
        )
    out.write_text("\n".join(draft_lines).rstrip() + "\n", encoding="utf-8")

    map_lines = [
        f"# Draft Source Map：{plan.stem}",
        "",
        f"- Generated at: {generated}",
        f"- Source plan: `{plan}`",
        f"- Combined draft: `{out}`",
        "",
        "| task_id | writer output | body chars | materials | evidence gaps | forbidden claims |",
        "|---|---|---:|---|---|---|",
    ]
    for item in ordered:
        map_lines.append(
            "| {task_id} | `{path}` | {chars} | {materials} | {gaps} | {claims} |".format(
                task_id=item.task_id,
                path=item.path,
                chars=len(item.body),
                materials=compact_cell(item.materials),
                gaps=compact_cell(item.evidence_gaps),
                claims=compact_cell(item.forbidden_claims),
            )
        )
    map_lines.append("")
    map_lines.append("## Task Packages")
    for item in ordered:
        map_lines.extend(["", f"### {item.task_id}", "", item.task_pack])
    source_map.write_text("\n".join(map_lines).rstrip() + "\n", encoding="utf-8")

    if manuscript is not None:
        manuscript.write_text(render_manuscript(ordered), encoding="utf-8")


def render_manuscript(ordered: list[WriterDraft]) -> str:
    parts: list[str] = []
    for item in ordered:
        body = item.body.strip()
        if body:
            parts.append(body)
    return "\n\n".join(parts).rstrip() + "\n"


def validate_manuscript(text: str) -> list[str]:
    errors: list[str] = []
    in_code = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("```"):
            in_code = not in_code
            errors.append(f"正文净稿第 {line_no} 行包含代码块或 Mermaid fence。")
            continue
        if in_code:
            errors.append(f"正文净稿第 {line_no} 行位于代码块内。")
            continue
        if "<!--" in stripped or "-->" in stripped:
            errors.append(f"正文净稿第 {line_no} 行包含 HTML 注释。")
        if re.search(r"\*\*[^*\n]+\*\*", stripped):
            errors.append(f"正文净稿第 {line_no} 行包含 Markdown 加粗。")
        if re.match(r"^\|.*\|$", stripped):
            errors.append(f"正文净稿第 {line_no} 行包含 Markdown 表格。")
        if stripped.startswith(">"):
            errors.append(f"正文净稿第 {line_no} 行包含引用块。")
        if re.match(r"^#{5,6}\s+", stripped):
            errors.append(f"正文净稿第 {line_no} 行标题层级超过 ####。")
        heading = re.match(r"^#{1,4}\s+(.+)$", stripped)
        if heading and heading.group(1).strip() in FORBIDDEN_MANUSCRIPT_HEADINGS:
            errors.append(f"正文净稿第 {line_no} 行包含过程性标题 `{heading.group(1).strip()}`。")
        if re.match(r"^[-*+]\s+", stripped):
            errors.append(f"正文净稿第 {line_no} 行包含项目符号清单。")
        if re.match(r"^\d+[.)]\s+", stripped):
            errors.append(f"正文净稿第 {line_no} 行包含编号清单。")
        if re.match(r"^[-*+]\s+\[[ xX]\]\s+", stripped):
            errors.append(f"正文净稿第 {line_no} 行包含任务清单。")
        if stripped.lower().startswith("mermaid"):
            errors.append(f"正文净稿第 {line_no} 行包含 Mermaid 标记。")
        if re.search(r"\bGenerated at:|\bSource plan:|\bTask count:|source:", stripped):
            errors.append(f"正文净稿第 {line_no} 行包含拼接元数据。")
    return errors


def compact_cell(text: str) -> str:
    if not text.strip():
        return "-"
    compact = re.sub(r"\s+", " ", text.strip())
    compact = compact.replace("|", "\\|")
    return compact[:180] + ("..." if len(compact) > 180 else "")


def payload(status: str, errors: list[str], **extra: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "errors": errors,
    }
    data.update(extra)
    return data


def write_json(path: Path | None, data: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def assemble(args: argparse.Namespace) -> int:
    plan = Path(args.plan).expanduser().resolve()
    draft_dir = Path(args.draft_dir).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    source_map = Path(args.source_map).expanduser().resolve()
    manuscript = Path(args.manuscript).expanduser().resolve() if args.manuscript else None
    json_path = Path(args.json).expanduser().resolve() if args.json else None

    errors: list[str] = []
    if not plan.exists():
        errors.append(f"计划文件不存在: {plan}")
    if not draft_dir.exists():
        errors.append(f"writer 输出目录不存在: {draft_dir}")
    if errors:
        write_json(json_path, payload("error", errors))
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    task_ids, plan_errors = parse_plan_task_ids(plan.read_text(encoding="utf-8", errors="replace"))
    errors.extend(plan_errors)
    writers, writer_errors = collect_writer_files(draft_dir)
    errors.extend(writer_errors)

    missing = [task_id for task_id in task_ids if task_id not in writers]
    if missing:
        errors.append("缺少 writer 输出: " + ", ".join(missing))

    unreferenced = sorted(task_id for task_id in writers if task_id not in set(task_ids))
    if unreferenced:
        errors.append("发现未被 writing-dispatch-plan 引用的 writer 输出: " + ", ".join(unreferenced))

    ordered: list[WriterDraft] = []
    if not errors:
        for task_id in task_ids:
            draft, draft_errors = read_writer(writers[task_id], task_id)
            errors.extend(draft_errors)
            if draft:
                ordered.append(draft)

    common = {
        "plan": str(plan),
        "draft_dir": str(draft_dir),
        "planned_task_ids": task_ids,
        "writer_files": {task_id: str(path) for task_id, path in writers.items()},
        "task_count": len(task_ids),
        "out": str(out),
        "manuscript": str(manuscript) if manuscript else None,
        "source_map": str(source_map),
    }
    if manuscript is not None and not errors:
        manuscript_text = render_manuscript(ordered)
        manuscript_errors = validate_manuscript(manuscript_text)
        if manuscript_errors:
            errors.extend(manuscript_errors)

    if errors:
        write_json(json_path, payload("error", errors, **common))
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    write_outputs(plan, out, source_map, ordered, manuscript)
    write_json(json_path, payload("ok", [], assembled_task_ids=[item.task_id for item in ordered], **common))
    print(f"Assembled {len(ordered)} draft fragments -> {out}")
    if manuscript is not None:
        print(f"Clean manuscript -> {manuscript}")
    print(f"Source map -> {source_map}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assemble paper-write chapter draft fragments")
    parser.add_argument("--plan", required=True, help="writing-dispatch-plan Markdown file")
    parser.add_argument("--draft-dir", required=True, help="agent log directory containing writer outputs")
    parser.add_argument("--out", required=True, help="combined draft Markdown path")
    parser.add_argument("--manuscript", help="optional clean manuscript Markdown path")
    parser.add_argument("--source-map", required=True, help="source map Markdown path")
    parser.add_argument("--json", help="optional assembly check JSON path")
    return parser


def main(argv: list[str] | None = None) -> int:
    return assemble(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
