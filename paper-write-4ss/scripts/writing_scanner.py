#!/usr/bin/env python3
"""
中文学术写作综合扫描器 —— 纯检测 + 生成改写指令。绝不自动修改原文。

  工作流：扫描 → 生成指令 MD → AI 自然重写句子 → 再扫描 → 循环至 🔴高危归零。

覆盖规则（21 条）：
  A. 句式反模式
     A1  不是……而是……（含 9 种变体）
     A2  "对……进行……" 冗长句式
     A3  "通过……来……" 冗长句式
     A4  在……中/上/下 冗余前置
     A5  一方面……另一方面…… 框套
     A6  正是……才…… 框套

  B. 标点与节奏
     B1  正文破折号（零容忍，≥1 个即标记）
     B2  超长单句（>150 字）
     B3  分号滥用（≥3个/段）
     B4  超长段落（>500 字）
     B5  排比/列举结构 ≥4 项
     B6  双——插入语（AI 重写句子）
     B7  英文直引号 / 引号配对错误（零容忍，≥1 个即标记）

  C. 冗余标记
     C1  换言之 / 也就是说 / 这意味着 / 一言以蔽之
     C2  所谓……是 / 即（解释性）

  D. paper-write-4ss 标准合规
     D1  引言缺少"然而/但是/不过"转折 [I2]
     D2  引用形式单一（全文"Author (Year) 指出"占比过高）[L5]
     D3  结论以限制结尾而非展望 [C6]
     D4  逐条引号检视——每一处引号拉出由 AI 判断必要性

用法：
  python writing_scanner.py --scan <file.md>            # 快速扫描统计
  python writing_scanner.py --report <file.md>          # 完整 Markdown 报告
  python writing_scanner.py --instructions <file.md>    # 生成结构化改写指令 MD
  python writing_scanner.py --instructions <file.md> --out rewrite.md  # 指定输出
"""

import re
import sys
import os
import argparse
import json
from pathlib import Path
from collections import defaultdict, Counter

# ═══════════════════════════════════════════════════════
# 规则引擎
# ═══════════════════════════════════════════════════════

class Rule:
    """一条检测规则"""
    def __init__(self, rule_id, name, severity, category, check_fn, fix_hint=''):
        self.id = rule_id
        self.name = name
        self.severity = severity  # high / medium / low
        self.category = category  # syntax / rhythm / redundancy / compliance
        self.check = check_fn     # (text, para_idx, para, all_paras) -> list[Issue] | None
        self.fix_hint = fix_hint

class Issue:
    """一个检出问题"""
    def __init__(self, rule_id, severity, category, para_idx, context, detail, fix_hint=''):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.para_idx = para_idx
        self.context = context      # 原文片段
        self.detail = detail        # 具体说明
        self.fix_hint = fix_hint


# ── 预处理 ────────────────────────────────────────────
def preprocess(text: str):
    """移除代码块、标题、引用，返回纯文本段落列表"""
    clean = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    clean = re.sub(r'^>.*$', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'^#{1,6}\s.*$', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'^\|.*\|$', '', clean, flags=re.MULTILINE)  # tables
    return [p.strip() for p in clean.split('\n\n') if len(p.strip()) > 20]


def split_sentences(para: str) -> list[str]:
    return [s.strip() for s in re.split(r'[。；]', para) if s.strip()]


# ═══════════════════════════════════════════════════════
# ── A. 句式反模式 ──
# ═══════════════════════════════════════════════════════

BUSHI_PATTERNS = [
    (r'不是.{0,80}而是.{0,200}?(?:[。\.]|$)', '不是……而是……'),
    (r'并非.{0,80}而是.{0,200}?(?:[。\.]|$)', '并非……而是……'),
    (r'不在于.{0,80}而在于.{0,200}?(?:[。\.]|$)', '不在于……而在于……'),
    (r'不意味着.{0,80}而是.{0,200}?(?:[。\.]|$)', '不意味着……而是……'),
    (r'不只是.{0,80}(?:更是|而是).{0,200}?(?:[。\.]|$)', '不只是……更是/而是……'),
    (r'并不在于.{0,80}而在于.{0,200}?(?:[。\.]|$)', '并不在于……而在于……'),
    (r'不能[^，。,\.]{0,60}只能[^。\.]{0,200}?(?:[。\.]|$)', '不能……只能……'),
    (r'(?:[。；]|^)(?!不[安同会像再足断仅单管论妨免]{1})不[^\n，。；]{1,40}，[^\n]{0,20}而[^\n。；]{1,200}?(?:[。；]|$)', '不……，而……'),
    (r'与其说.{0,80}不如说.{0,200}?(?:[。\.]|$)', '与其说……不如说……'),
]

def check_bushi(text, para_idx, para, all_paras):
    issues = []
    for pat, name in BUSHI_PATTERNS:
        for m in re.finditer(pat, para):
            issues.append(Issue(
                'A1', 'high', 'syntax', para_idx,
                context=m.group()[:200],
                detail=f'变体: {name}',
                fix_hint='改为直接肯定陈述。如"不是A而是B"→直接陈述B，A的信息作为次要补充'
            ))
    # Dedup overlapping
    return _dedup(issues)


def check_dui_jinxing(text, para_idx, para, all_paras):
    issues = []
    for m in re.finditer(r'对.{2,40}进行.{2,30}', para):
        issues.append(Issue(
            'A2', 'low', 'syntax', para_idx,
            context=m.group()[:100],
            detail=f'"对…进行…" 可简化',
            fix_hint='改为直接动词。如"对数据进行清洗"→"清洗数据"'
        ))
    return issues


def check_tongguo_lai(text, para_idx, para, all_paras):
    issues = []
    for m in re.finditer(r'通过.{2,40}来[^，。；]{3,30}', para):
        issues.append(Issue(
            'A3', 'low', 'syntax', para_idx,
            context=m.group()[:100],
            detail=f'"通过…来…" 可简化',
            fix_hint='删"来"字，或改为"以……"结构'
        ))
    return issues


def check_zai_locative(text, para_idx, para, all_paras):
    locs = re.findall(r'在[^在]{3,60}?(?:中|上|下)[，,，]', para)
    if len(locs) >= 2:
        return [Issue(
            'A4', 'low', 'syntax', para_idx,
            context=para[:150],
            detail=f'{len(locs)} 处"在……中/上/下"前置',
            fix_hint='至少一半改为直接陈述，删除冗余"在"字'
        )]
    return []


def check_yifangmian(text, para_idx, para, all_paras):
    if re.search(r'一方面.{0,50}另一方面', para):
        return [Issue(
            'A5', 'low', 'syntax', para_idx,
            context=para[:150],
            detail='"一方面……另一方面……" 框套',
            fix_hint='打破二元框套，用更自然的递进或并列结构重组'
        )]
    return []


def check_zhengshi_cai(text, para_idx, para, all_paras):
    if re.search(r'正是.{0,40}才', para):
        return [Issue(
            'A6', 'low', 'syntax', para_idx,
            context=para[:150],
            detail='"正是……才……" 强调框套',
            fix_hint='改为更平实的因果或条件陈述'
        )]
    return []


# ═══════════════════════════════════════════════════════
# ── B. 标点与节奏 ──
# ═══════════════════════════════════════════════════════

def check_dash_density(text, para_idx, para, all_paras):
    # 跳过参考文献条目（论文标题中的主副标题——是标准格式）
    if re.match(r'^[一-鿿]{2,4}[、，]?\d{4}[，,]', para):
        return []
    cnt = para.count('——')
    # 零容忍：正文中出现任何——都标记
    if cnt >= 1:
        return [Issue(
            'B1', 'high', 'rhythm', para_idx,
            context=para[:200],
            detail=f'{cnt} 个 ——（{len(para)} 字段落，{cnt/(len(para)/100):.1f}/百字）',
            fix_hint='AI自然重写整个句子，彻底消除破折号。不得机械替换为其他标点。若句子结构依赖——才能成立，说明句子本身需要重构。'
        )]
    return []


def check_long_sentence(text, para_idx, para, all_paras):
    # 跳过英文参考文献条目（作者列表长是格式要求）
    if re.match(r'^[A-Z][a-z]+,\s[A-Z]\.', para):
        return []
    issues = []
    for s in split_sentences(para):
        if len(s) > 150:
            issues.append(Issue(
                'B2', 'medium', 'rhythm', para_idx,
                context=s[:200],
                detail=f'{len(s)} 字',
                fix_hint='在逻辑断点处拆分为 2-3 句'
            ))
    return issues


def check_semicolon_abuse(text, para_idx, para, all_paras):
    cnt = para.count('；')
    if cnt >= 3:
        return [Issue(
            'B3', 'low', 'rhythm', para_idx,
            context=para[:200],
            detail=f'{cnt} 个分号（{len(para)}字段落）',
            fix_hint='将分号连接的超长并列结构改为独立句'
        )]
    return []


def check_long_paragraph(text, para_idx, para, all_paras):
    # 跳过纯英文段落（Abstract）和参考文献条目
    if sum(1 for c in para if c.isascii() and c.isalpha()) / max(len(para), 1) > 0.3:
        return []
    if len(para) > 500:
        return [Issue(
            'B4', 'medium', 'rhythm', para_idx,
            context=para[:200],
            detail=f'{len(para)} 字段落',
            fix_hint='在主题切换处拆分段落，每段聚焦一个子主题'
        )]
    return []


def check_double_dash_insert(text, para_idx, para, all_paras):
    """B6: 双——插入语 —— AI 重写句子"""
    # 跳过参考文献条目
    if re.match(r'^[一-鿿]{2,4}[、，]?\d{4}[，,]', para):
        return []
    # 检测 ——……—— 双破折号插入语
    matches = re.findall(r'——[^。\n——]{3,50}——', para)
    if matches:
        return [Issue(
            'B6', 'high', 'rhythm', para_idx,
            context=para[:200],
            detail=f'{len(matches)} 处双——插入语：{matches[0][:60]}',
            fix_hint='AI自然重写句子，将插入语融入主句或用括号替代。不得机械替换标点。'
        )]
    return []


def check_quote_marks(text, para_idx, para, all_paras):
    """B7: 英文直引号 / 引号配对错误 — 零容忍"""
    # 跳过参考文献条目和纯英文段落
    if re.match(r'^[一-鿿]{2,4}[、，]?\d{4}[，,]', para):
        return []
    if sum(1 for c in para if c.isascii() and c.isalpha()) / max(len(para), 1) > 0.3:
        return []
    issues = []

    # 检测英文直引号 " (U+0022)
    straight = [m.start() for m in re.finditer(r'"', para)]
    if straight:
        # 确认不是出现在代码或 URL 中
        context_preview = para[max(0, straight[0]-15):min(len(para), straight[-1]+30)]
        issues.append(Issue(
            'B7', 'high', 'rhythm', para_idx,
            context=context_preview[:200],
            detail=f'{len(straight)} 处英文直引号 " (U+0022)，必须改为中文引号 " (U+201C) / " (U+201D)',
            fix_hint='将所有 " 替换为中文左引号 " 或右引号 "。AI 需根据上下文判断开闭位置，自然改写所在句子。'
        ))

    # 检测 "…" 配对错误（左引号用作右引号）
    wrong_pairs = re.findall(r'“[^”“]{1,150}“', para)
    if wrong_pairs:
        issues.append(Issue(
            'B7', 'high', 'rhythm', para_idx,
            context=f'{wrong_pairs[0][:150]}' if wrong_pairs else para[:150],
            detail=f'{len(wrong_pairs)} 处 "" 配对错误（第二个 " 应为 "），此情况多由输入法误操作产生',
            fix_hint='将第二个 " (U+201C) 改为 " (U+201D)。AI 需根据上下文判断开闭位置，自然改写所在句子。'
        ))

    return issues


def check_parallelism(text, para_idx, para, all_paras):
    """检测 ≥4 项的列举排比"""
    patterns = [
        (r'(?:其一|其二|其三|其四|其五)', '其一…其N'),
        (r'(?:第一[，,]|第二[，,]|第三[，,]|第四[，,]|第五[，,])', '第一…第N'),
        (r'(?:一是|二是|三是|四是|五是)', '一是…五是'),
    ]
    for pat, name in patterns:
        found = re.findall(pat, para)
        if len(found) >= 4:
            return [Issue(
                'B5', 'low', 'rhythm', para_idx,
                context=para[:200],
                detail=f'{name} 列举 {len(found)} 项',
                fix_hint='≥4 项的机械列举考虑合并或改用更自然的叙述结构'
            )]
    return []


# ═══════════════════════════════════════════════════════
# ── C. 冗余标记 ──
# ═══════════════════════════════════════════════════════

REDUNDANT_MARKERS = [
    (r'换言之[，,]', '换言之'),
    (r'也就是说[，,]', '也就是说'),
    (r'这意味着[，,]', '这意味着'),
    (r'一言以蔽之[，,:：]', '一言以蔽之'),
    (r'换句话说[，,]', '换句话说'),
    (r'所谓.{0,30}?(?:是|指的是|即)[，,]', '所谓……是……'),
    (r'(?<!\w)即[^使便将是可]{1}', '即（解释性）'),
]

def check_redundant_markers(text, para_idx, para, all_paras):
    issues = []
    for pat, name in REDUNDANT_MARKERS:
        for m in re.finditer(pat, para):
            issues.append(Issue(
                'C1' if name != '即（解释性）' else 'C2',
                'low', 'redundancy', para_idx,
                context=para[max(0,m.start()-20):min(len(para),m.end()+40)],
                detail=f'标记: {name}',
                fix_hint='删除重述标记，直接陈述。若需保留转折，改用更简洁的表达'
            ))
    return issues


# ═══════════════════════════════════════════════════════
# ── D. paper-write-4ss 合规 ──
# ═══════════════════════════════════════════════════════

def check_intro_turn(text, para_idx, para, all_paras):
    """D1: 引言部分必须有"然而/但是/不过"转折 [I2]"""
    # Only run once on the full text
    if para_idx != 0:
        return []
    # Find intro section (between 一、问题的提出 and 二、)
    full = '\n'.join(all_paras)
    intro_match = re.search(r'(?:问题的提出|引言).*?(?=##\s*二[、,，])', text, re.DOTALL)
    if intro_match:
        intro = intro_match.group()
        if not re.search(r'然而|但是|不过', intro):
            return [Issue(
                'D1', 'high', 'compliance', -1,
                context='引言部分',
                detail='未检测到"然而/但是/不过"转折词',
                fix_hint='在引言第1-3段插入转折词，紧跟研究缺口描述 [paper-write-4ss I2]'
            )]
    return []


def check_citation_variety(text, para_idx, para, all_paras):
    """D2: 引用形式多样性 [L5] — 全文级别，仅运行一次"""
    if para_idx != 0:
        return []
    full = '\n'.join(all_paras)
    # Count citation forms
    author_year_lead = len(re.findall(r'[一-鿿]{2,4}[（(]\d{4}[）)]', full))
    parenthetical = len(re.findall(r'[（(][一-鿿]{2,4}[^）)]{0,20}\d{4}[）)]', full))
    domain_name = len(re.findall(r'既有[^\n]{2,20}研究[^\n]{0,10}(?:表明|指出|认为|普遍)', full))
    concept_lead = len(re.findall(r'["“][^”\"]{2,20}["”](?:这一概念|这一术语)', full))

    variety_score = sum(1 for x in [author_year_lead, parenthetical, domain_name, concept_lead] if x >= 3)
    if variety_score < 3:
        return [Issue(
            'D2', 'medium', 'compliance', -1,
            context=f'全文引用形式统计',
            detail=f'作者-年份前置:{author_year_lead} | 后置括注:{parenthetical} | 领域代作者:{domain_name} | 概念引领:{concept_lead}',
            fix_hint=f'当前仅有 {variety_score}/4 种引用形式。需 ≥3 种 [paper-write-4ss L5]'
        )]
    return []


def check_conclusion_ending(text, para_idx, para, all_paras):
    """D3: 结论不以研究限制结尾 [C6] — 仅检查结论最后一段"""
    # Find conclusion section
    full = '\n'.join(all_paras)
    concl_match = re.search(r'(?:五、结论|结论与讨论).*', text, re.DOTALL)
    if not concl_match:
        return []
    concl = concl_match.group()
    # Get last paragraph of conclusion
    concl_paras = [p.strip() for p in concl.split('\n\n') if len(p.strip()) > 30]
    if not concl_paras:
        return []
    last_para = concl_paras[-1]
    # Check if it starts with limitation language
    if re.match(r'(?:本文的?(?:局限|不足|限制)|研究(?:局限|不足|限制))', last_para):
        return [Issue(
            'D3', 'medium', 'compliance', -1,
            context=last_para[:200],
            detail='结论以研究限制结尾',
            fix_hint='将研究限制移至倒数第二段，最后一段以未来展望收尾 [paper-write-4ss C6]'
        )]
    return []


def check_unnecessary_quotes(text, para_idx, para, all_paras):
    """D4: 逐条引号检视 — 每一处引号拉出来由 AI 判断必要性（必要最少原则）"""
    issues = []
    seq = 0

    for p_idx, p in enumerate(all_paras):
        # 跳过参考文献条目和纯英文段落
        if re.match(r'^[一-鿿]{2,4}[、，]?\d{4}[，,]', p):
            continue
        if sum(1 for c in p if c.isascii() and c.isalpha()) / max(len(p), 1) > 0.3:
            continue

        # 同时检测中文引号 "" 和英文直引号 ""
        quotes_cn = re.findall(r'“[^”“]{1,300}”', p)
        quotes_en = re.findall(r'"[^"]{1,300}"', p)

        for q in quotes_cn + quotes_en:
            inner = q[1:-1]
            inner_len = len(inner)
            seq += 1

            # 获取引文前后各 30 字的上下文
            q_pos = p.find(q)
            ctx_start = max(0, q_pos - 30)
            ctx_end = min(len(p), q_pos + len(q) + 30)
            context_window = p[ctx_start:ctx_end]
            # 在上下文中高亮引文位置
            context_highlighted = context_window.replace(q, f'「{q}」')

            # 判断可能属于哪类引号
            if inner_len > 50:
                hint = '长引文（>50字），多为直接引述。请确认：这是原文直接引述吗？是→保留引号；否→改为间接转述并删除引号。'
                sev = 'medium'
            elif inner_len <= 3:
                hint = '极短引号（≤3字）。几乎不可能是必要的。检查：是专有学术名词吗？是→保留；否→删除引号，直接写这个词。'
                sev = 'high'
            else:
                hint = '短引号。逐条判断：①直接引述原文？②首次提出的专有学术概念？③反讽/非常规用法？若三项皆否→删除引号，直接陈述。'
                sev = 'medium'

            issues.append(Issue(
                'D4', sev, 'compliance', p_idx,
                context=context_highlighted[:300],
                detail=f'[{seq}] 被引号包裹的词/句：「{inner[:80]}」（{inner_len}字）',
                fix_hint=hint
            ))

    return issues


# ═══════════════════════════════════════════════════════
# 规则注册表
# ═══════════════════════════════════════════════════════

ALL_RULES = [
    # A. 句式反模式
    Rule('A1', '不是……而是……句式', 'high', 'syntax', check_bushi),
    Rule('A2', '"对……进行……"冗长句式', 'low', 'syntax', check_dui_jinxing),
    Rule('A3', '"通过……来……"冗长句式', 'low', 'syntax', check_tongguo_lai),
    Rule('A4', '"在……中/上/下"冗余前置', 'low', 'syntax', check_zai_locative),
    Rule('A5', '"一方面……另一方面……"框套', 'low', 'syntax', check_yifangmian),
    Rule('A6', '"正是……才……"强调框套', 'low', 'syntax', check_zhengshi_cai),

    # B. 标点与节奏
    Rule('B1', '正文破折号（零容忍）', 'high', 'rhythm', check_dash_density),
    Rule('B2', '超长单句 (>150字)', 'medium', 'rhythm', check_long_sentence),
    Rule('B3', '分号滥用 (≥3个/段)', 'low', 'rhythm', check_semicolon_abuse),
    Rule('B4', '超长段落 (>500字)', 'medium', 'rhythm', check_long_paragraph),
    Rule('B5', '排比/列举 ≥4项', 'low', 'rhythm', check_parallelism),
    Rule('B6', '双——插入语（AI 重写句子）', 'high', 'rhythm', check_double_dash_insert),
    Rule('B7', '英文直引号 / 引号配对错误', 'high', 'rhythm', check_quote_marks),

    # C. 冗余标记
    Rule('C1', '冗余重述标记', 'low', 'redundancy', check_redundant_markers),

    # D. paper-write-4ss 合规
    Rule('D1', '引言缺少转折词 [I2]', 'high', 'compliance', check_intro_turn),
    Rule('D2', '引用形式单一 [L5]', 'medium', 'compliance', check_citation_variety),
    Rule('D3', '结论以限制结尾 [C6]', 'medium', 'compliance', check_conclusion_ending),
    Rule('D4', '逐条引号检视（必要最少原则）', 'medium', 'compliance', check_unnecessary_quotes),
]


def _dedup(issues):
    """去除重叠匹配，保留更精确的"""
    if len(issues) < 2:
        return issues
    issues.sort(key=lambda x: (x.para_idx, len(x.context)))
    kept = []
    for iss in issues:
        overlaps = False
        for k in kept:
            if (iss.para_idx == k.para_idx and
                iss.context[:40] in k.context):
                overlaps = True
                break
        if not overlaps:
            kept.append(iss)
    return kept


# ═══════════════════════════════════════════════════════
# 扫描入口
# ═══════════════════════════════════════════════════════

def scan_all(text: str) -> list[Issue]:
    """执行全部规则，返回问题列表"""
    all_paras = preprocess(text)
    all_issues = []

    for rule in ALL_RULES:
        # 全文级规则 (para_idx == 0 or -1) 只跑一次
        if rule.id.startswith('D'):
            result = rule.check(text, 0, '', all_paras)
            if result:
                all_issues.extend(result)
        else:
            # 段落级规则
            for p_idx, para in enumerate(all_paras):
                result = rule.check(text, p_idx, para, all_paras)
                if result:
                    all_issues.extend(result)

    # Sort by severity then by position
    sev_order = {'high': 0, 'medium': 1, 'low': 2}
    all_issues.sort(key=lambda x: (sev_order.get(x.severity, 3), x.para_idx))
    return all_issues


# ═══════════════════════════════════════════════════════
# 输出：改写指令 Markdown
# ═══════════════════════════════════════════════════════

def generate_instructions(text: str, issues: list[Issue], source_file: str) -> str:
    """生成结构化改写指令 MD"""
    lines = []
    lines.append(f'# 改写指令：{Path(source_file).name}\n')
    lines.append(f'> 由 `writing_scanner.py` 自动生成 | 共 {len(issues)} 条任务\n')
    lines.append('---\n')

    # 按类别分组统计
    lines.append('## 概览\n')
    lines.append('| 类别 | 规则 | 数量 | 严重度 |')
    lines.append('|------|------|------|--------|')
    cat_counts = defaultdict(lambda: defaultdict(int))
    for iss in issues:
        cat_counts[iss.category][iss.rule_id] += 1
    for cat in ['syntax', 'rhythm', 'redundancy', 'compliance']:
        for rid, cnt in sorted(cat_counts[cat].items()):
            rule = next((r for r in ALL_RULES if r.id == rid), None)
            if rule:
                lines.append(f'| {cat} | {rule.name} | {cnt} | {rule.severity} |')
    lines.append('')

    # 逐条改写任务
    lines.append('---\n')
    lines.append('## 改写任务清单\n')
    lines.append('> **执行方式**：从上到下逐条处理。每条任务包含：要修改的原文 + 改写要求。\n')
    lines.append('> **IRON RULE 1**：改写后不得引入新的"不是……而是……"句式。\n')
    lines.append('> **IRON RULE 2**：不得用脚本机械替换标点符号（如 `——→：`）。必须 AI 自然重写整个句子。\n')
    lines.append('> **IRON RULE 3**：改写后正文中不得出现任何破折号（——）。\n')

    for i, iss in enumerate(issues):
        sev_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(iss.severity, '⚪')
        rule = next((r for r in ALL_RULES if r.id == iss.rule_id), None)
        rule_name = rule.name if rule else iss.rule_id

        lines.append(f'### [{i+1}] {sev_emoji} [{iss.rule_id}] {rule_name}\n')
        lines.append(f'- **严重度**: {iss.severity}')
        lines.append(f'- **类别**: {iss.category}')
        if iss.para_idx >= 0:
            lines.append(f'- **段落索引**: {iss.para_idx}')
        lines.append(f'- **详情**: {iss.detail}')
        lines.append(f'- **改写要求**: {iss.fix_hint}')
        lines.append(f'\n**原文片段**：\n')
        lines.append(f'> {iss.context[:500]}\n')
        lines.append(f'\n> ✏️ 请改写以上原文，只输出改写后的文本。\n')
        lines.append('---\n')

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

def cmd_scan(args):
    text = Path(args.file).read_text(encoding='utf-8')
    issues = scan_all(text)
    if not issues:
        print('✅ 未检出任何问题。')
        return 0

    # Summary
    sev_counts = Counter(i.severity for i in issues)
    cat_counts = Counter(i.category for i in issues)
    print(f'检出 {len(issues)} 个问题：')
    print(f'  严重度: 高{sev_counts["high"]} 中{sev_counts["medium"]} 低{sev_counts["low"]}')
    print(f'  类别: 句式{cat_counts.get("syntax",0)} 标点节奏{cat_counts.get("rhythm",0)} 冗余{cat_counts.get("redundancy",0)} 合规{cat_counts.get("compliance",0)}')

    if args.verbose:
        for i, iss in enumerate(issues):
            if not args.verbose >= 2 and iss.severity == 'low':
                continue
            rule = next((r for r in ALL_RULES if r.id == iss.rule_id), None)
            name = rule.name if rule else iss.rule_id
            print(f'\n[{i+1}] [{iss.severity}] [{iss.rule_id}] {name}')
            print(f'  上下文: {iss.context[:150]}...')
            print(f'  详情: {iss.detail}')
    return 0  # always exit 0 (counts are printed, not error codes)


def cmd_report(args):
    text = Path(args.file).read_text(encoding='utf-8')
    issues = scan_all(text)

    lines = ['# AI 写作不良习惯扫描报告\n']
    lines.append(f'**文件**: `{args.file}`\n')
    lines.append(f'**总问题数**: {len(issues)}\n')

    lines.append('## 按规则汇总\n')
    lines.append('| 规则ID | 规则名称 | 数量 | 严重度 |')
    lines.append('|--------|---------|------|--------|')
    counts = Counter(i.rule_id for i in issues)
    for rid, cnt in counts.most_common():
        rule = next((r for r in ALL_RULES if r.id == rid), None)
        lines.append(f'| {rid} | {rule.name if rule else "?"} | {cnt} | {rule.severity if rule else "?"} |')

    lines.append('\n## 详细列表\n')
    for i, iss in enumerate(issues):
        rule = next((r for r in ALL_RULES if r.id == iss.rule_id), None)
        lines.append(f'### [{i+1}] [{iss.severity}] [{iss.rule_id}] {rule.name if rule else "?"}')
        lines.append(f'- **段落**: {iss.para_idx}')
        lines.append(f'- **详情**: {iss.detail}')
        lines.append(f'- **片段**: {iss.context[:200]}')
        lines.append(f'- **建议**: {iss.fix_hint}')
        lines.append('')

    out = args.out or str(Path(args.file).with_suffix('.scan_report.md'))
    Path(out).write_text('\n'.join(lines), encoding='utf-8')
    print(f'报告已保存 → {out}')
    return 0


def cmd_instructions(args):
    text = Path(args.file).read_text(encoding='utf-8')
    issues = scan_all(text)

    if not issues:
        print('✅ 未检出任何问题，无需生成改写指令。')
        return 0

    md = generate_instructions(text, issues, args.file)
    out = args.out or str(Path(args.file).with_suffix('.rewrite_instructions.md'))
    Path(out).write_text(md, encoding='utf-8')
    print(f'改写指令已生成 → {out}')
    print(f'共 {len(issues)} 条任务（高{sum(1 for i in issues if i.severity=="high")} 中{sum(1 for i in issues if i.severity=="medium")} 低{sum(1 for i in issues if i.severity=="low")}）')
    print(f'\n请将以下 prompt 发送给 Claude Code：')
    print(f'  "请按照 {out} 中的改写任务清单，逐条对原文进行润色。"')
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='中文学术写作综合扫描器 — 检出问题 → 生成改写指令',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --scan paper.md              # 快速扫描统计
  %(prog)s --scan paper.md -v           # 显示高+中严重度
  %(prog)s --scan paper.md -vv          # 显示全部
  %(prog)s --report paper.md            # 完整 Markdown 报告
  %(prog)s --instructions paper.md      # 生成改写指令 MD（供 Claude Code 执行）
        """,
    )
    parser.add_argument('file', help='目标 Markdown 文件')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--scan', action='store_true', help='快速扫描统计')
    group.add_argument('--report', action='store_true', help='完整 Markdown 报告')
    group.add_argument('--instructions', action='store_true', help='生成结构化改写指令 MD')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('--out', help='输出文件路径')

    args = parser.parse_args()
    if not os.path.exists(args.file):
        print(f'❌ 文件不存在：{args.file}')
        return 1

    if args.scan:
        return cmd_scan(args)
    elif args.report:
        return cmd_report(args)
    elif args.instructions:
        return cmd_instructions(args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
