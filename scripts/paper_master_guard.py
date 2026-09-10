#!/usr/bin/env python3
"""Mechanical guards for paper-master-4ss projects.

The script is intentionally standard-library only. It can be called from
Claude Code hooks, OpenCode/Codex explicit guard calls, or manual runs
inside any project that contains a paper-workspace directory.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


TODAY = datetime.now().date().isoformat()
FAILURE_TYPES = ("提示", "工具", "知识", "流程", "数据", "执行环境")
ANALYSIS_COMMAND_RE = re.compile(
    r"(stata_run_file|stata_run_selection|Rscript|python3?\b|\.do\b|\.R\b|\.py\b|paper-workspace/04-analysis|paper-workspace\\04-analysis)",
    re.IGNORECASE,
)
ERROR_RE = re.compile(
    r"(\bblocked\b|\berror\b|\bfailed\b|traceback|execution halted|error in |r\([0-9]+\)|"
    r"exit\s*(code|status)?\s*[:=]?\s*[1-9][0-9]*|退出码\s*[:：]?\s*[1-9][0-9]*)",
    re.IGNORECASE,
)


def read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}
    return data if isinstance(data, dict) else {"_payload": data}


def iter_values(value: Any):
    if isinstance(value, dict):
        for item in value.values():
            yield from iter_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_values(item)
    elif isinstance(value, str):
        yield value


def command_from_hook(payload: dict[str, Any]) -> str:
    candidates: list[str] = []
    for key in ("command", "cmd", "tool_input", "tool_response", "tool_output"):
        if key in payload:
            candidates.extend(str(x) for x in iter_values(payload[key]))
    candidates.extend(str(x) for x in iter_values(payload))
    for text in candidates:
        if ANALYSIS_COMMAND_RE.search(text):
            return text
    return candidates[0] if candidates else ""


def workspace_path(arg: str) -> Path:
    return Path(arg).expanduser().resolve()


def analysis_root(workspace: Path) -> Path:
    return workspace / "04-analysis"


def latest_file(paths: list[Path]) -> Path | None:
    existing = [p for p in paths if p.exists()]
    if not existing:
        return None
    return max(existing, key=lambda p: p.stat().st_mtime)


def latest_analysis_run_log(workspace: Path) -> Path | None:
    reports = analysis_root(workspace) / "reports"
    logs = sorted(reports.glob("run-log*.md")) if reports.exists() else []
    return latest_file(logs)


def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def parse_run_log_outputs(text: str) -> list[str]:
    outputs: list[str] = []
    for line in text.splitlines():
        row = split_markdown_row(line)
        if len(row) < 4 or row[0].lower() in {"date", "---"}:
            continue
        output_cell = row[3]
        if output_cell in {"", "-"}:
            continue
        for part in re.split(r"<br\s*/?>|,|;", output_cell):
            token = part.strip().strip("`")
            if token and token != "-":
                outputs.append(token)
    return outputs


def output_exists(workspace: Path, token: str) -> bool:
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        return candidate.exists()
    analysis = analysis_root(workspace)
    direct_candidates = [
        Path.cwd() / token,
        workspace / token,
        analysis / token,
        analysis / "reports" / token,
        analysis / "tables" / token,
        analysis / "figures" / token,
        analysis / "data" / token,
    ]
    if any(p.exists() for p in direct_candidates):
        return True
    name = Path(token).name
    if name:
        return any(analysis.rglob(name)) if analysis.exists() else False
    return False


def audit_analysis_logs(workspace: Path, command: str) -> tuple[str, list[str], Path | None]:
    issues: list[str] = []
    log_path = latest_analysis_run_log(workspace)
    if not workspace.exists():
        return "skip", [f"未发现工作区: {workspace}"], None
    if log_path is None:
        return "issues", ["未找到 paper-workspace/04-analysis/reports/run-log*.md。"], None

    text = log_path.read_text(encoding="utf-8", errors="replace")
    if ERROR_RE.search(text):
        issues.append("run-log 包含 blocked/error/failed/traceback/非零退出码/Stata r(...) 等失败信号。")
    if not re.search(r"stdout", text, re.IGNORECASE) or not re.search(r"stderr", text, re.IGNORECASE):
        issues.append("run-log 未记录 stdout/stderr 路径；无法完成执行日志闭环。")

    missing_outputs = [out for out in parse_run_log_outputs(text) if not output_exists(workspace, out)]
    if missing_outputs:
        sample = ", ".join(missing_outputs[:8])
        suffix = " ..." if len(missing_outputs) > 8 else ""
        issues.append(f"run-log 中登记的输出文件不存在: {sample}{suffix}")

    status = "issues" if issues else "ok"
    if not command:
        issues.append("Hook 输入中未解析到 Bash 命令；已仅按最新 run-log 审计。")
        status = "issues"
    return status, issues, log_path


def write_audit_report(workspace: Path, status: str, issues: list[str], command: str, log_path: Path | None) -> Path:
    out_dir = workspace / "_logs" / "hook-audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"analysis-log-audit-{TODAY}.md"
    body = [
        "# Analysis Log Audit",
        "",
        f"- Date: {TODAY}",
        f"- Status: {status}",
        f"- Command: `{command.strip()[:400] if command else 'unparsed'}`",
        f"- Run log: `{log_path}`" if log_path else "- Run log: `missing`",
        "",
        "## Issues",
    ]
    if issues:
        body.extend(f"- {issue}" for issue in issues)
    else:
        body.append("- 未发现阻断性日志问题。")
    body.append("")
    out.write_text("\n".join(body), encoding="utf-8")
    return out


def cmd_post_bash(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    payload = read_stdin_json()
    command = command_from_hook(payload)
    if command and not ANALYSIS_COMMAND_RE.search(command):
        return 0

    status, issues, log_path = audit_analysis_logs(workspace, command)
    if status == "skip":
        return 0
    report = write_audit_report(workspace, status, issues, command, log_path)
    if issues:
        print(f"paper-master-4ss analysis audit found issues. See {report}", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
    else:
        print(f"paper-master-4ss analysis audit passed. See {report}")
    return 0


def key_artifacts(workspace: Path) -> list[Path]:
    candidates: list[Path] = []
    for sub in ["01-design", "02-literature", "03-outline", "04-analysis", "05-writing", "06-submission", "07-update"]:
        root = workspace / sub
        if root.exists():
            candidates.extend(p for p in root.rglob("*") if p.is_file() and p.name != ".DS_Store")
    logs = workspace / "_logs"
    if logs.exists():
        candidates.extend(
            p
            for p in logs.rglob("*")
            if p.is_file() and p.name != ".DS_Store" and "hook-audit" not in p.parts
        )
    return candidates


def cmd_stop_check(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    if not workspace.exists():
        return 0
    artifacts = key_artifacts(workspace)
    if not artifacts:
        return 0
    latest = latest_file(artifacts)
    assert latest is not None
    required = [workspace / "_index" / "project-state.md", workspace / "_index" / "handoff-status.md"]
    stale_or_missing: list[str] = []
    latest_mtime = latest.stat().st_mtime
    for path in required:
        if not path.exists():
            stale_or_missing.append(f"缺失: {path}")
        elif path.stat().st_mtime + 0.001 < latest_mtime:
            stale_or_missing.append(f"过期: {path} 早于最新产物 {latest}")
    if stale_or_missing:
        print("paper-master-4ss guard_before_finish blocked completion: index files must be updated.", file=sys.stderr)
        for item in stale_or_missing:
            print(f"- {item}", file=sys.stderr)
        return 2
    return 0


def has_files(path: Path, patterns: list[str]) -> list[Path]:
    found: list[Path] = []
    if not path.exists():
        return found
    for pattern in patterns:
        found.extend(p for p in path.glob(pattern) if p.is_file() and p.name != ".DS_Store")
    return sorted(set(found))


def has_any_file(path: Path) -> bool:
    return path.exists() and any(p.is_file() and p.name != ".DS_Store" for p in path.rglob("*"))


def agent_synthesis(workspace: Path, module: str) -> list[Path]:
    root = workspace / "_logs" / "agents"
    if not root.exists():
        return []
    return sorted(root.glob(f"{module}-*/agent-synthesis-{module}-*.md"))


def latest_design_report(workspace: Path) -> Path | None:
    """Return the latest old-architecture design or FULL report."""
    root = workspace / "01-design"
    if not root.exists():
        return None
    reports = list(root.glob("design-report-*.md")) + list(root.glob("full-report-*.md"))
    return latest_file(reports)


def design_metadata(workspace: Path) -> dict[str, str]:
    """Read the orientation metadata written by the restored DESIGN/FULL flow."""
    report = latest_design_report(workspace)
    if report is None:
        return {}
    text = report.read_text(encoding="utf-8", errors="replace")
    metadata: dict[str, str] = {}
    for key in ("research_orientation", "analysis_required"):
        match = re.search(rf"(?im)^\s*{key}\s*:\s*([^\n#]+)", text)
        if match:
            metadata[key] = match.group(1).strip().strip("`\"'").lower()
    return metadata


def selected_design_paradigm(workspace: Path) -> str:
    """Compatibility name: return the latest confirmed research orientation."""
    return design_metadata(workspace).get("research_orientation", "")


def analysis_is_required(workspace: Path) -> bool:
    value = design_metadata(workspace).get("analysis_required")
    if value in {"false", "no", "否", "0"}:
        return False
    # Preserve legacy-project scoring until a report explicitly opts out.
    return True


def score_design(workspace: Path) -> dict[str, Any]:
    return score_module(
        workspace,
        "01-design",
        "design",
        15,
        ["frame-report-*.md", "storm-report-*.md", "design-report-*.md", "full-report-*.md"],
        "补齐 FRAME、STORM、DESIGN 或 FULL 报告；在 DESIGN/FULL 报告中写明研究取向、analysis_required、风险与下游交接。",
    )


def item(name: str, max_score: int, score: int, evidence: list[str], attribution: str, fix_next: str) -> dict[str, Any]:
    return {
        "name": name,
        "score": max(0, min(score, max_score)),
        "max": max_score,
        "evidence": evidence or ["未发现可评分证据"],
        "failure_attribution": attribution if score < max_score else "",
        "fix_next": fix_next if score < max_score else "保持当前证据链并在下一阶段继续更新索引。",
    }


def score_governance(workspace: Path) -> dict[str, Any]:
    idx = workspace / "_index"
    evidence: list[str] = []
    score = 0
    for filename, points in [("project-state.md", 3), ("handoff-status.md", 3), ("input-registry.md", 2)]:
        path = idx / filename
        if path.exists():
            score += points
            evidence.append(str(path))
    roadmap = idx / "paper-roadmap.md"
    if roadmap.exists():
        score += 1
        evidence.append(str(roadmap))
    if (workspace / "_logs").exists():
        score += 1
        evidence.append(str(workspace / "_logs"))
    missing = []
    for filename in ("project-state.md", "handoff-status.md", "input-registry.md", "paper-roadmap.md"):
        if not (idx / filename).exists():
            missing.append(filename)
    if not (workspace / "_logs").exists():
        missing.append("_logs/")
    fix_next = "补齐 " + "、".join(missing) + "。" if missing else "保持当前证据链并在下一阶段继续更新索引。"
    if "paper-roadmap.md" in missing:
        fix_next += " 旧项目缺少路线图不阻断交付，但下一次启动或实质模块完成时应按 master/user-journey.md 补建。"
    return item("项目治理", 10, score, evidence, "流程", fix_next)


def score_module(workspace: Path, name: str, label: str, max_score: int, patterns: list[str], fix_next: str) -> dict[str, Any]:
    root = workspace / name
    core = has_files(root, patterns)
    synth = agent_synthesis(workspace, label)
    evidence = [str(p) for p in core[:8] + synth[:3]]
    if not root.exists() or not has_any_file(root):
        return item(label, max_score, 0, evidence, "流程", fix_next)
    base = int(max_score * 0.35)
    core_points = min(int(max_score * 0.45), len(core) * max(1, int(max_score * 0.45 / max(1, len(patterns)))))
    synth_points = int(max_score * 0.20) if synth else 0
    return item(label, max_score, base + core_points + synth_points, evidence, "知识", fix_next)


def score_lit(workspace: Path) -> dict[str, Any]:
    root = workspace / "02-literature"
    evidence: list[str] = []
    missing: list[str] = []
    score = 0
    if not root.exists() or not has_any_file(root):
        return item(
            "lit", 15, 0, evidence, "流程",
            "初始化 paper-registry、papers/fulltext、review-evidence、review-outline 和 review-gaps，再补文献地图与空白分析。"
        )

    score += 2
    registry = root / "paper-registry.csv"
    registry_ids: set[str] = set()
    if registry.exists():
        evidence.append(str(registry))
        try:
            with registry.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            registry_ids = {row.get("paper_id", "") for row in rows if row.get("paper_id")}
            header = set(rows[0].keys()) if rows else set(registry.read_text(encoding="utf-8-sig", errors="replace").splitlines()[0].split(","))
            required = {"paper_id", "title", "download_status", "pdf_path", "parse_status", "fulltext_path", "reading_status"}
            if required <= header:
                score += 3
            else:
                missing.append("paper-registry.csv 的路径与状态字段")
        except (OSError, csv.Error, IndexError):
            missing.append("可读取的 paper-registry.csv")
    else:
        missing.append("paper-registry.csv")

    for directory in ("papers", "fulltext"):
        path = root / directory
        if path.is_dir():
            score += 1
            evidence.append(str(path))
        else:
            missing.append(f"{directory}/")

    evidence_table = root / "review-evidence.csv"
    if evidence_table.exists():
        evidence.append(str(evidence_table))
        try:
            with evidence_table.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            header = set(rows[0].keys()) if rows else set(evidence_table.read_text(encoding="utf-8-sig", errors="replace").splitlines()[0].split(","))
            required = {"claim_id", "paper_id", "evidence_level", "source_location", "review_status"}
            evidence_ids = {row.get("paper_id", "") for row in rows if row.get("paper_id")}
            if not required <= header:
                missing.append("review-evidence.csv 的 claim 与来源字段")
            elif evidence_ids - registry_ids:
                missing.append("证据表中可回查的 paper_id")
            else:
                score += 3
        except (OSError, csv.Error, IndexError):
            missing.append("可读取的 review-evidence.csv")
    else:
        missing.append("review-evidence.csv")

    for filename in ("review-outline.md", "review-gaps.md"):
        path = root / filename
        if path.exists():
            score += 1
            evidence.append(str(path))
        else:
            missing.append(filename)

    maps = has_files(root, ["literature-map*.md", "gap-map*.md", "hypothesis-derivation*.md"])
    if maps:
        score += 1
        evidence.extend(str(path) for path in maps[:2])
    else:
        missing.append("文献地图、空白表或理论对话产物")

    synth = agent_synthesis(workspace, "lit")
    if synth:
        score += 2
        evidence.extend(str(path) for path in synth[:2])
    else:
        missing.append("_logs/agents/lit-*/agent-synthesis-lit-*.md")

    fix_next = "补齐 " + "、".join(missing) + "。" if missing else "保持注册表、证据映射、论证蓝图和缺口报告同步更新。"
    attribution = "流程" if any("registry" in value or "evidence" in value or "outline" in value for value in missing) else "知识"
    return item("lit", 15, min(score, 15), evidence, attribution, fix_next)


def score_analysis(workspace: Path) -> dict[str, Any]:
    root = workspace / "04-analysis"
    evidence: list[str] = []
    score = 0
    if not root.exists() or not has_any_file(root):
        return item("analysis", 25, 0, evidence, "数据", "补齐分析计划、变量字典、真实执行日志、script-index 和表图产物。")
    score += 5
    for path, points in [
        (root / "data" / "variable-dictionary.csv", 3),
        (root / "reports" / "script-index.md", 4),
    ]:
        if path.exists():
            score += points
            evidence.append(str(path))
    run_log = latest_analysis_run_log(workspace)
    if run_log:
        evidence.append(str(run_log))
        text = run_log.read_text(encoding="utf-8", errors="replace")
        score += 5 if not ERROR_RE.search(text) else 2
    tables = has_files(root / "tables", ["*.csv"])
    figs = has_files(root / "figures", ["*.png", "*.pdf"])
    if tables:
        score += 4
        evidence.extend(str(p) for p in tables[:4])
    if figs:
        score += 2
        evidence.extend(str(p) for p in figs[:2])
    audits = has_files(workspace / "_logs" / "hook-audit", ["analysis-log-audit-*.md"])
    if audits:
        evidence.append(str(audits[-1]))
        text = audits[-1].read_text(encoding="utf-8", errors="replace").lower()
        score += 2 if "status: ok" in text else 1
    return item("analysis", 25, score, evidence, "执行环境", "修复 run-log 中的阻断项，补齐 stdout/stderr、script-index、CSV 表格和可追溯图形。")


def score_write(workspace: Path) -> dict[str, Any]:
    root = workspace / "05-writing"
    evidence: list[str] = []
    score = 0
    missing: list[str] = []
    if not root.exists() or not has_any_file(root):
        return item(
            "write",
            15,
            0,
            evidence,
            "流程",
            "补齐 writing-dispatch-plan、多 writer 输出、assemble_drafts 拼接结果、主 agent 审查、修订稿和扫描报告。",
        )

    score += 1

    final_drafts = [
        p for p in sorted(root.glob("*.md"))
        if p.name == "literature-review.md"
        or p.name == "manuscript.md"
        or p.name.startswith("manuscript-")
    ]
    if final_drafts:
        evidence.extend(str(p) for p in final_drafts[:2])
    else:
        missing.append("05-writing/literature-review.md 或 manuscript*.md 顶层净稿")

    plans = has_files(root / "plans", ["writing-dispatch-plan-*.md", "*.md"])
    if plans:
        score += 2
        evidence.extend(str(p) for p in plans[:2])
    else:
        missing.append("plans/writing-dispatch-plan-*.md")

    writer_outputs = has_files(
        workspace / "_logs" / "agents",
        ["write-*/paper-write-chapter-draft-writer--*.md"],
    )
    if writer_outputs:
        score += 2 if len(writer_outputs) >= 2 else 1
        evidence.extend(str(p) for p in writer_outputs[:4])
        if len(writer_outputs) == 1:
            missing.append("第二个及以上 task_id 独立 writer 输出（长文/全文任务需要多段派发）")
    else:
        missing.append("_logs/agents/write-*/paper-write-chapter-draft-writer--{task_id}.md")

    drafts = has_files(root / "drafts", ["draft-*.md", "*.md"])
    if drafts:
        score += 2
        evidence.extend(str(p) for p in drafts[:2])
    else:
        missing.append("drafts/draft-*.md")

    source_maps = has_files(root / "assembly", ["source-map-*.md", "*source-map*.md"])
    assembly_checks = has_files(root / "assembly", ["assembly-check-*.json", "*assembly*.json"])
    if source_maps or assembly_checks:
        score += 2
        evidence.extend(str(p) for p in (source_maps[:2] + assembly_checks[:2]))
    else:
        missing.append("assembly/source-map-*.md 与 assembly-check-*.json")

    reviews = has_files(root / "reviews", ["main-agent-review-*.md", "paper-check-report-*.md", "paper-check-matrix-*.md"])
    if reviews:
        score += 2
        evidence.extend(str(p) for p in reviews[:2])
    else:
        missing.append("reviews/main-agent-review-*.md 或 paper-check-report-*.md")

    revisions = has_files(root / "revisions", ["styled-*.md", "*.md"])
    if revisions:
        score += 2
        evidence.extend(str(p) for p in revisions[:2])
    else:
        missing.append("revisions/styled-*.md")

    scans = has_files(root / "scans", ["scan-report-*.md", "rewrite-instructions-*.md", "*.md"])
    if scans:
        score += 1
        evidence.extend(str(p) for p in scans[:2])
    else:
        missing.append("scans/scan-report-*.md")

    synth = agent_synthesis(workspace, "write") + agent_synthesis(workspace, "check")
    if synth:
        score += 1
        evidence.extend(str(p) for p in synth[:2])
    else:
        missing.append("_logs/agents/write-*/agent-synthesis-write-*.md 或 check-*/agent-synthesis-check-*.md")

    fix_next = "补齐 " + "、".join(missing) + "。" if missing else "保持多 writer 派发、脚本拼接、主审查和扫描闭环。"
    attribution = "流程" if any("review" in item or "assemble" in item or "writer" in item for item in missing) else "知识"
    return item("write", 15, score, evidence, attribution, fix_next)


def compute_scores(workspace: Path) -> dict[str, Any]:
    items = [
        score_governance(workspace),
        score_design(workspace),
        score_lit(workspace),
        score_module(workspace, "03-outline", "outline", 10, ["*.md"], "补齐 paper-outline、evidence-map、gap-report 和 writing-plan。"),
        *([score_analysis(workspace)] if analysis_is_required(workspace) else []),
        score_write(workspace),
        score_module(workspace, "06-submission", "submission", 10, ["*.md", "*.docx"], "补齐 submission-checklist、format-check-report、citation-gap-report 和投稿文档。"),
    ]
    total = sum(x["score"] for x in items)
    max_total = sum(x["max"] for x in items)
    started = [x for x in items if x["score"] > 0 or x["name"] == "项目治理"]
    started_max = sum(x["max"] for x in started) or max_total
    started_score = sum(x["score"] for x in started)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "failure_types": list(FAILURE_TYPES),
        "maturity_score": round(total / max_total * 100, 1) if max_total else 0,
        "stage_score": round(started_score / started_max * 100, 1) if started_max else 0,
        "raw_score": total,
        "raw_max": max_total,
        "items": items,
    }


def write_score_outputs(workspace: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    idx = workspace / "_index"
    idx.mkdir(parents=True, exist_ok=True)
    json_path = idx / "quality-score.json"
    md_path = idx / "quality-score.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = [
        "# Quality Score",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Stage score: {payload['stage_score']}",
        f"- Maturity score: {payload['maturity_score']}",
        f"- Raw score: {payload['raw_score']}/{payload['raw_max']}",
        "",
        "| Item | Score | Evidence | Failure attribution | Fix next |",
        "|---|---:|---|---|---|",
    ]
    for entry in payload["items"]:
        evidence = "<br>".join(entry["evidence"])
        rows.append(
            f"| {entry['name']} | {entry['score']}/{entry['max']} | {evidence} | "
            f"{entry['failure_attribution'] or '-'} | {entry['fix_next']} |"
        )
    rows.append("")
    md_path.write_text("\n".join(rows), encoding="utf-8")
    return md_path, json_path


def cmd_score_project(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    if not workspace.exists():
        if args.json:
            print(json.dumps({"status": "skip", "reason": f"workspace not found: {workspace}"}, ensure_ascii=False))
        return 0
    payload = compute_scores(workspace)
    md_path, json_path = write_score_outputs(workspace, payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Wrote {md_path} and {json_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="paper-master-4ss hook and rubric guard")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("post-bash", "stop-check", "score-project"):
        p = sub.add_parser(name)
        p.add_argument("--workspace", default="paper-workspace")
        if name == "score-project":
            p.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "post-bash":
        return cmd_post_bash(args)
    if args.command == "stop-check":
        return cmd_stop_check(args)
    if args.command == "score-project":
        return cmd_score_project(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
