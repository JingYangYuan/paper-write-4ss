#!/usr/bin/env python3
"""
Example 内容按需截取器 —— 根据研究路由结果，仅提取对应的范文章节和提示词模板。

用法：
  # 交互模式（通过命令行参数指定路由）
  python example_extractor.py \
    --paradigm 社会学研究范式 \
    --method 量化实证 \
    --protocol 实证研究 \
    --out extracted_examples.md

  # JSON 模式（接收 method_router.py 的路由输出）
  python example_extractor.py --route route_report.json --out extracted_examples.md

  # 仅输出指定文件
  python example_extractor.py --paradigm 社会学研究范式 --method 量化实证 --files intro,findings

设计原则：
  路由完成后调用此脚本，只加载写作所需的最小范文集，避免 5 个 example 文件
  全部加载造成的 token 浪费（全部加载约 30KB → 截取后约 8-15KB）。
"""

import re
import sys
import os
import json
import argparse
from pathlib import Path
from collections import OrderedDict

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

# ── 路由到章节的映射表 ──────────────────────────────────────────
# 每个条目: { "heading_keywords": [...], "prompt_keywords": [...] }
# heading_keywords: 匹配范文章节标题（中文关键字匹配）
# prompt_keywords:  匹配提示词模板标题

EXAMPLE_MAP = {
    "intro_example.md": {
        "社会学研究范式": {
            "headings": ["社会学研究范式引言", "两种范式引言差异速查", "引言写作通用禁忌"],
        },
        "管理世界案例研究范式": {
            "headings": ["管理世界案例研究范式引言", "两种范式引言差异速查", "引言写作通用禁忌"],
        },
    },

    "lit_review_example.md": {
        # 综述范文已按 master/literature-review-protocol.md 重写为证据驱动结构，
        # 与发表范式无关，两种范式截取同一组章节。
        "社会学研究范式": {
            "headings": [
                "可选结构", "理论争论", "实证分歧", "概念与理论谱系", "方法边界",
                "段落示意", "交付前检查",
            ],
        },
        "管理世界案例研究范式": {
            "headings": [
                "可选结构", "理论争论", "实证分歧", "概念与理论谱系", "方法边界",
                "段落示意", "交付前检查",
            ],
        },
    },

    "framework_example.md": {
        "社会学研究范式": {
            "headings": [
                "分析框架在论文中的两种位置",
                "社会学研究范式分析框架",
                "维度分解型",
                "理论对话型",
                "分析框架提示词模板",
                "框架质量自检清单",
            ],
        },
        "管理世界案例研究范式": {
            "headings": [
                "分析框架在论文中的两种位置",
                "管理世界案例范式理论框架",
                "机制链型",
                "二维矩阵型",
                "分析框架提示词模板",
                "框架质量自检清单",
            ],
        },
    },

    "findings_example.md": {
        "社会学研究范式": {
            # 社会学范式下根据具体方法进一步筛选
            "量化实证": {
                "headings": [
                    "社会学研究范式：量化实证类",
                    "量化实证提示词",
                    "研究发现质量自检清单",
                ],
            },
            "质性田野或深度访谈": {
                "headings": [
                    "社会学研究范式：质性田野类",
                    "质性田野提示词",
                    "研究发现质量自检清单",
                ],
            },
            # 默认（未指定具体方法时）
            "_default": {
                "headings": [
                    "社会学研究范式：量化实证类",
                    "社会学研究范式：质性田野类",
                    "研究发现质量自检清单",
                ],
            },
        },
        "管理世界案例研究范式": {
            "headings": [
                "管理世界案例范式：研究发现",
                "管理世界案例提示词",
                "研究发现质量自检清单",
            ],
        },
    },

    "conclusion_example.md": {
        "社会学研究范式": {
            "headings": [
                "社会学研究范式结论",
                "两种范式结论差异速查",
                "结论写作反模式",
            ],
        },
        "管理世界案例研究范式": {
            "headings": [
                "管理世界案例范式结论",
                "两种范式结论差异速查",
                "结论写作反模式",
            ],
        },
    },
}


def parse_sections(filepath: str) -> list[dict]:
    """将 Markdown 文件解析为节列表。

    每个节: {level, title, content, start_line}
    从 # 标题到下一个同级或更高级标题之间的内容为一个节。
    """
    sections = []
    with open(filepath, encoding='utf-8') as f:
        lines = f.readlines()

    current = None
    for i, line in enumerate(lines):
        m = re.match(r'^(#{1,4})\s+(.+?)(?:\s*\{[^}]*\})?\s*$', line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if current:
                current['content'] = ''.join(lines[current['start_line']:i])
                current['end_line'] = i
                sections.append(current)
            current = {'level': level, 'title': title, 'start_line': i}
    if current:
        current['content'] = ''.join(lines[current['start_line']:])
        sections.append(current)

    return sections


def match_heading(title: str, keywords: list[str]) -> bool:
    """检查标题是否匹配任一关键字（中文包含匹配）。"""
    for kw in keywords:
        if kw in title:
            return True
    return False


def extract_example(filename: str, paradigm: str, method: str = None) -> str:
    """从指定 example 文件中截取与路由匹配的章节。

    Args:
        filename: 如 "intro_example.md"
        paradigm: "社会学研究范式" 或 "管理世界案例研究范式"
        method: "量化实证" / "质性田野或深度访谈" / "案例研究" / None

    Returns:
        拼接后的 Markdown 文本
    """
    filepath = EXAMPLES_DIR / filename
    if not filepath.exists():
        return f"> ⚠ 未找到文件：{filepath}\n\n"

    sections = parse_sections(str(filepath))
    file_map = EXAMPLE_MAP.get(filename, {})

    # 获取该范式对应的 heading 列表
    paradigm_cfg = file_map.get(paradigm, {})
    if not paradigm_cfg:
        return f"> ⚠ 文件 {filename} 中未定义范式 '{paradigm}' 的映射\n\n"

    # 如果 headings 是 dict（有方法细分），则进一步解析
    if isinstance(paradigm_cfg, dict) and "headings" not in paradigm_cfg:
        # 有方法细分
        method_cfg = paradigm_cfg.get(method) if method else None
        if not method_cfg:
            method_cfg = paradigm_cfg.get("_default", {})
        headings = method_cfg.get("headings", [])
    else:
        headings = paradigm_cfg.get("headings", [])

    if not headings:
        return f"> ⚠ 未匹配到任何章节\n\n"

    # 筛选匹配的节
    matched = []
    for sec in sections:
        if match_heading(sec['title'], headings):
            matched.append(sec)

    if not matched:
        return f"> ⚠ 在 {filename} 中未找到匹配的章节（关键字：{headings}）\n\n"

    # 拼接输出
    output_parts = []
    file_title = filename.replace('.md', '')
    output_parts.append(f"<!-- 来源：examples/{filename} | 范式：{paradigm} | 方法：{method or '默认'} -->\n")
    for sec in matched:
        output_parts.append(sec['content'].rstrip() + '\n')

    return '\n'.join(output_parts)


def extract_all(paradigm: str, method: str = None,
                protocol: str = None,
                files: list[str] = None) -> str:
    """根据路由参数截取全部相关 example 内容。

    Args:
        paradigm: 发表范式
        method: 研究方法（量化实证 / 质性田野或深度访谈 / 案例研究）
        protocol: 方法协议（实证研究 / 规范研究 / 阐释研究 / 混合研究）
        files: 限定文件列表，None 表示全部

    Returns:
        拼接后的完整 Markdown 文本
    """
    if files is None:
        files = list(EXAMPLE_MAP.keys())

    result_parts = []
    result_parts.append(
        f"# 范文与提示词（按需截取）\n\n"
        f"- 发表范式：{paradigm}\n"
        f"- 研究方法：{method or '默认'}\n"
        f"- 方法协议：{protocol or '默认'}\n\n"
        f"---\n\n"
    )

    for fname in files:
        if fname in EXAMPLE_MAP:
            content = extract_example(fname, paradigm, method)
            result_parts.append(content)
            result_parts.append('\n---\n\n')

    return '\n'.join(result_parts)


def main():
    parser = argparse.ArgumentParser(
        description='Example 内容按需截取器 —— 根据研究路由结果截取对应范文章节'
    )
    parser.add_argument('--paradigm', type=str,
                        choices=['社会学研究范式', '管理世界案例研究范式'],
                        help='发表范式')
    parser.add_argument('--method', type=str,
                        choices=['量化实证', '质性田野或深度访谈', '案例研究',
                                 '理论分析', '混合方法'],
                        help='研究方法')
    parser.add_argument('--protocol', type=str,
                        choices=['实证研究', '规范研究', '阐释研究', '混合研究'],
                        help='方法协议')
    parser.add_argument('--files', type=str,
                        help='限定文件，逗号分隔。如 intro,findings')
    parser.add_argument('--route', type=str,
                        help='JSON 路由报告文件路径（method_router.py 输出）')
    parser.add_argument('--out', type=str,
                        help='输出文件路径（默认输出到 stdout）')
    parser.add_argument('--list', action='store_true',
                        help='列出所有可用文件和当前路由的截取计划')

    args = parser.parse_args()

    # JSON 路由模式：从路由报告读取参数
    paradigm = args.paradigm
    method = args.method
    protocol = args.protocol

    if args.route:
        try:
            with open(args.route, encoding='utf-8') as f:
                route = json.load(f)
            paradigm = paradigm or route.get('paradigm') or route.get('发表范式')
            method = method or route.get('method') or route.get('研究方法')
            protocol = protocol or route.get('protocol') or route.get('方法协议')
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"⚠ 无法读取路由报告：{e}", file=sys.stderr)

    if not paradigm:
        print("错误：需要指定 --paradigm 或 --route", file=sys.stderr)
        sys.exit(1)

    # 解析文件列表
    files = None
    if args.files:
        files = [f"{f.strip()}_example.md" if not f.strip().endswith('.md')
                 else f.strip()
                 for f in args.files.split(',')]

    # --list 模式
    if args.list:
        print(f"发表范式：{paradigm}")
        print(f"研究方法：{method or '默认'}")
        print(f"方法协议：{protocol or '默认'}")
        print()
        target_files = files or list(EXAMPLE_MAP.keys())
        for fname in target_files:
            if fname in EXAMPLE_MAP:
                cfg = EXAMPLE_MAP[fname].get(paradigm, {})
                if isinstance(cfg, dict) and "headings" not in cfg:
                    mcfg = cfg.get(method) or cfg.get("_default", {})
                    headings = mcfg.get("headings", [])
                else:
                    headings = cfg.get("headings", [])
                print(f"  {fname}: {len(headings)} 节")
                for h in headings:
                    print(f"    - {h}")
        return

    # 截取
    output = extract_all(paradigm=paradigm, method=method, protocol=protocol,
                         files=files)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding='utf-8')
        print(f"✅ 截取完成 → {args.out}  ({len(output)} 字符)", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
