#!/usr/bin/env python3
"""
中文学术写作综合扫描器 —— 纯检测 + 生成改写指令。绝不自动修改原文。

  工作流：扫描 → 生成指令 MD → AI 自然重写句子 → 再扫描 → 循环至 🔴高危归零。

覆盖规则（25 条，按四大类组织）：
  A. 句式反模式（7 条）
     ...
  B. 标点与节奏（8 条）
     ...
  C. 冗余标记（2 条）
     ...
  D. write module 标准合规（8 条）
     D1-D8 [同上]
     D9  英文缩写过度使用 / 跨节未重新展开

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
    def __init__(self, rule_id, name, severity, category, check_fn,
                 scope='para', fix_hint=''):
        self.id = rule_id
        self.name = name
        self.severity = severity  # high / medium / low
        self.category = category  # syntax / rhythm / redundancy / compliance
        self.check = check_fn     # (text, para_idx, para, all_paras) -> list[Issue] | None
        self.scope = scope        # 'para'（段落级）或 'full'（全文级，仅运行一次）
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
    """移除代码块、标题、引用、表格，返回纯文本段落列表"""
    clean = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    clean = re.sub(r'^>.*$', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'^#{1,6}\s.*$', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'^\|.*\|$', '', clean, flags=re.MULTILINE)
    return [p.strip() for p in clean.split('\n\n') if len(p.strip()) > 20]


def split_sentences(para: str) -> list[str]:
    return [s.strip() for s in re.split(r'[。；]', para) if s.strip()]


def _is_ref_entry(para: str) -> bool:
    """检查是否为参考文献条目。

    匹配中文参考文献（支持多作者，以顿号分隔）和英文参考文献。
    示例：
      陈云松、范晓光，2016，《...》，《...》第12期。
      李强，1997，《...》，《...》第4期。
      Adler, N. E., Epel, E. S., ... (2000). ...
      Jackman, M. R., & Jackman, R. W. (1973). ...
    """
    # 中文参考文献：作者名（含顿号分隔） + 逗号 + 年份
    if re.match(r'^[一-鿿、]{2,40}[，,]\s*\d{4}[，,)]', para):
        return True
    # 英文参考文献：以 "Surname, Initial." 开头
    if re.match(r'^[A-Z][a-zÀ-ÿ]+,\s+[A-Z]\.', para):
        return True
    # 纯代码/公式行不是参考文献
    if para.startswith('`') or para.startswith('$$'):
        return False
    return False


def _is_english_heavy(para: str, threshold=0.3) -> bool:
    """检查是否为英文为主的段落"""
    return sum(1 for c in para if c.isascii() and c.isalpha()) / max(len(para), 1) > threshold


# ═══════════════════════════════════════════════════════
# ── A. 句式反模式（7 条，全部段落级）──
# ═══════════════════════════════════════════════════════

# A1: 不是……而是…… 及其 9 种变体
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

def check_a1_bushi(text, para_idx, para, all_paras):
    """A1: 不是……而是…… 及其 9 种变体"""
    issues = []
    for pat, name in BUSHI_PATTERNS:
        for m in re.finditer(pat, para):
            issues.append(Issue(
                'A1', 'high', 'syntax', para_idx,
                context=m.group()[:200],
                detail=f'变体: {name}',
                fix_hint='改为直接肯定陈述。如"不是A而是B"→直接陈述B，A的信息作为次要补充'
            ))
    return _dedup(issues)


def check_a2_dui_jinxing(text, para_idx, para, all_paras):
    """A2: "对……进行……" 冗长句式"""
    issues = []
    for m in re.finditer(r'对.{2,40}进行.{2,30}', para):
        issues.append(Issue(
            'A2', 'low', 'syntax', para_idx,
            context=m.group()[:100],
            detail='"对…进行…" 可简化',
            fix_hint='改为直接动词。如"对数据进行清洗"→"清洗数据"'
        ))
    return issues


def check_a3_tongguo_lai(text, para_idx, para, all_paras):
    """A3: "通过……来……" 冗长句式"""
    issues = []
    for m in re.finditer(r'通过.{2,40}来[^，。；]{3,30}', para):
        issues.append(Issue(
            'A3', 'low', 'syntax', para_idx,
            context=m.group()[:100],
            detail='"通过…来…" 可简化',
            fix_hint='删"来"字，或改为"以……"结构'
        ))
    return issues


def check_a4_zai_locative(text, para_idx, para, all_paras):
    """A4: "在……中/上/下" 冗余前置"""
    locs = re.findall(r'在[^在]{3,60}?(?:中|上|下)[，,，]', para)
    if len(locs) >= 2:
        return [Issue(
            'A4', 'low', 'syntax', para_idx,
            context=para[:150],
            detail=f'{len(locs)} 处"在……中/上/下"前置',
            fix_hint='至少一半改为直接陈述，删除冗余"在"字'
        )]
    return []


def check_a5_yifangmian(text, para_idx, para, all_paras):
    """A5: "一方面……另一方面……" 框套"""
    if re.search(r'一方面.{0,50}另一方面', para):
        return [Issue(
            'A5', 'low', 'syntax', para_idx,
            context=para[:150],
            detail='"一方面……另一方面……" 框套',
            fix_hint='打破二元框套，用更自然的递进或并列结构重组'
        )]
    return []


def check_a6_zhengshi_cai(text, para_idx, para, all_paras):
    """A6: "正是……才……" 强调框套"""
    if re.search(r'正是.{0,40}才', para):
        return [Issue(
            'A6', 'low', 'syntax', para_idx,
            context=para[:150],
            detail='"正是……才……" 强调框套',
            fix_hint='改为更平实的因果或条件陈述'
        )]
    return []


def check_a7_zhi_suoyi(text, para_idx, para, all_paras):
    """A7: "之所以……是因为……" —— 典型的 AI 生成口癖，中文社会科学论文中极少自然出现"""
    if re.search(r'之所以.{0,80}是因为', para):
        return [Issue(
            'A7', 'medium', 'syntax', para_idx,
            context=para[:200],
            detail='"之所以……是因为……"句式（AI 口癖）',
            fix_hint='改为直接因果陈述。如"之所以A，是因为B"→"A的原因在于B"或"A，因为B"。中文社科论文极少使用此句式，自然写作中通常用"由于/因为/其根源在于"替代。'
        )]
    return []


# ═══════════════════════════════════════════════════════
# ── B. 标点与节奏（8 条，全部段落级）──
# ═══════════════════════════════════════════════════════

def check_b1_dash(text, para_idx, para, all_paras):
    """B1: 破折号综合检测 —— 合并原 B1（零容忍存在）+ B6（双插入语）+ B8（机械替换痕迹）。

    三类子检测独立运行，同一段落可能同时触发多个。
    """
    if _is_ref_entry(para):
        return []
    issues = []

    # ── B1a: 正文破折号存在（零容忍，每段≥1 个即标记）──
    cnt = para.count('——')
    if cnt >= 1:
        issues.append(Issue(
            'B1', 'high', 'rhythm', para_idx,
            context=para[:200],
            detail=f'{cnt} 个 ——（{len(para)} 字段落，{cnt/(len(para)/100):.1f}/百字）',
            fix_hint='AI 自然重写整个句子，彻底消除破折号。不得用冒号、逗号或括号机械替换。若句子结构依赖——才能成立，说明句子本身需要重构。'
        ))

    # ── B1b: 双破折号插入语 ——……—— ──
    double_dash = re.findall(r'——[^。\n——]{3,50}——', para)
    if double_dash:
        issues.append(Issue(
            'B1', 'high', 'rhythm', para_idx,
            context=para[:200],
            detail=f'{len(double_dash)} 处双——插入语：{double_dash[0][:60]}',
            fix_hint='AI 自然重写句子，将插入语融入主句。不得机械替换标点。'
        ))

    # ── B1c: 破折号机械替换痕迹 —— 仅检测高置信度长括号插入（≥25字）──
    paren_inserts = re.findall(r'（([^）]{25,80})）', para)
    for m in paren_inserts:
        if re.search(r'\d{4}', m):           # 排除引用标注
            continue
        if re.search(r'[A-Za-z]{4,}', m):    # 排除英文内容
            continue
        if re.search(r'[等参阅见按]', m):      # 排除引用标记
            continue
        if not re.search(r'[，。；、]', m):    # 排除无标点的纯术语列表
            continue
        if not re.search(r'(?:是|为|在|使|将|把|被|可以|需要|具有|产生|形成|构成|参与|进行|通过|依赖|决定|影响|塑造|改变)', m):
            continue
        issues.append(Issue(
            'B1', 'medium', 'rhythm', para_idx,
            context=m[:80],
            detail=f'疑似双破折号机械替换为括号：长插入语"{m[:40]}..."',
            fix_hint='全角括号内含完整主谓从句（≥25字），可能是双破折号插入语的机械替换。应自然重写句子，将插入语融入主句或改为独立句子。'
        ))

    return issues if issues else []


def check_b2_long_sentence(text, para_idx, para, all_paras):
    """B2: 超长单句 >150 字"""
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


def check_b3_semicolon_abuse(text, para_idx, para, all_paras):
    """B3: 分号滥用 ≥3 个/段"""
    cnt = para.count('；')
    if cnt >= 3:
        return [Issue(
            'B3', 'low', 'rhythm', para_idx,
            context=para[:200],
            detail=f'{cnt} 个分号（{len(para)}字段落）',
            fix_hint='将分号连接的超长并列结构改为独立句'
        )]
    return []


def check_b4_long_paragraph(text, para_idx, para, all_paras):
    """B4: 超长段落 >500 字"""
    if _is_english_heavy(para):
        return []
    if len(para) > 500:
        return [Issue(
            'B4', 'medium', 'rhythm', para_idx,
            context=para[:200],
            detail=f'{len(para)} 字段落',
            fix_hint='在主题切换处拆分段落，每段聚焦一个子主题'
        )]
    return []


def check_b5_parallelism(text, para_idx, para, all_paras):
    """B5: 排比/列举 ≥4 项"""
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


def check_b6_quote_marks(text, para_idx, para, all_paras):
    """B6: 英文直引号 / 引号配对错误 —— 零容忍"""
    if _is_ref_entry(para) or _is_english_heavy(para):
        return []
    issues = []

    # 检测英文直引号 " (U+0022)
    straight = [m.start() for m in re.finditer(r'"', para)]
    if straight:
        context_preview = para[max(0, straight[0]-15):min(len(para), straight[-1]+30)]
        issues.append(Issue(
            'B6', 'high', 'rhythm', para_idx,
            context=context_preview[:200],
            detail=f'{len(straight)} 处英文直引号 " (U+0022)，必须改为中文引号 " (U+201C) / " (U+201D)',
            fix_hint='将所有 " 替换为中文左引号 " 或右引号 "。AI 需根据上下文判断开闭位置，自然改写所在句子。'
        ))

    # 检测 "" 配对错误（左引号用作右引号）
    wrong_pairs = re.findall(r'“[^“”]{1,150}“', para)
    if wrong_pairs:
        issues.append(Issue(
            'B6', 'high', 'rhythm', para_idx,
            context=f'{wrong_pairs[0][:150]}' if wrong_pairs else para[:150],
            detail=f'{len(wrong_pairs)} 处 "" 配对错误（第二个 " 应为 "），此情况多由输入法误操作产生',
            fix_hint='将第二个 " (U+201C) 改为 " (U+201D)。AI 需根据上下文判断开闭位置，自然改写所在句子。'
        ))

    return issues


def check_b7_weak_colon(text, para_idx, para, all_paras):
    """B7: 弱冒号模式 —— 短引导语（≤12字）后直接跟冒号 + 完整解释从句。

    如："它告诉我们：项目型定量研究中的……"、"X在于：完整从句"
    冒号前后形成"标签：答案"结构，冒号仅起装饰作用。
    """
    if _is_ref_entry(para):
        return []
    issues = []

    weak_colons = re.findall(
        r'([^。；\n]{1,12}'
        r'(?:告诉我们|表明|揭示|指出|显示|提示|意味着|在于|就是|正是)'
        r')[：]([^。；\n]{15,80}[。；])',
        para
    )
    for intro, body in weak_colons:
        if body.count('；') >= 2 or body.count('、') >= 4:
            continue
        if body.strip().startswith(('"', '"', '"')):
            continue
        if re.search(r'(?:概念化|定义|称之|命名|分为|包括|如下)', intro):
            continue
        snippet = (intro + '：' + body)[:80]
        issues.append(Issue(
            'B7', 'medium', 'rhythm', para_idx,
            context=snippet,
            detail=f'弱冒号模式：短引导语后冒号+完整从句"{snippet[:50]}..."',
            fix_hint='短引导语（≤12字）后不宜直接用冒号引出完整从句。应自然重写：去掉冒号改为逗号衔接，或重构句子使解释性内容融入主句。'
        ))

    return issues if issues else []


def check_b8_integrable_paren(text, para_idx, para, all_paras):
    """B8: 可融入括号插入语 —— 短括号（6-25字）含融入信号词，独立于主句之外。

    如："（就像科学论文的作者制度一样）"、"（特别是理由层和判断层）"、"（尤其是研究生助理）"
    这些内容含"就像/特别是/尤其是/亦即/换言之"等信号词，应通过逗号或从句融入主句。
    """
    if _is_ref_entry(para):
        return []
    issues = []

    integrable_parens = re.findall(r'（([^）]{6,25})）', para)
    for m in integrable_parens:
        if re.search(r'\d{4}', m):
            continue
        if re.search(r'[A-Za-z]{4,}', m):
            continue
        if not re.search(r'(?:就像|如同|特别是|尤其是|亦即|换言之|也就是|包括|例如|比如|正是|恰恰)', m):
            continue
        full_match = re.search(r'（' + re.escape(m) + r'）', para)
        if full_match:
            before = para[:full_match.start()].strip()
            after = para[full_match.end():].strip()
            if len(before) >= 5 and len(after) >= 5:
                issues.append(Issue(
                    'B8', 'medium', 'rhythm', para_idx,
                    context=f'（{m}）',
                    detail=f'可融入括号插入语：内容"{m}"含融入信号词，且独立于主句之外',
                    fix_hint='短括号插入语含"就像/特别是/尤其是"等可融入信号词时，应自然重写将其融入主句（如改用逗号引出、改为从句、或前置为话题），而非让括号打断句子节奏。'
                ))

    return issues if issues else []


# ═══════════════════════════════════════════════════════
# ── C. 冗余标记（2 条，全部段落级）──
# ═══════════════════════════════════════════════════════

# C1 重述标记
REDUNDANT_MARKERS = [
    (r'换言之[，,]', '换言之'),
    (r'也就是说[，,]', '也就是说'),
    (r'这意味着[，,]', '这意味着'),
    (r'一言以蔽之[，,:：]', '一言以蔽之'),
    (r'换句话说[，,]', '换句话说'),
]

def check_c1_redundant_markers(text, para_idx, para, all_paras):
    """C1: 冗余重述标记 —— 换言之/也就是说/这意味着/一言以蔽之/换句话说"""
    issues = []
    for pat, name in REDUNDANT_MARKERS:
        for m in re.finditer(pat, para):
            issues.append(Issue(
                'C1', 'low', 'redundancy', para_idx,
                context=para[max(0, m.start()-20):min(len(para), m.end()+40)],
                detail=f'重述标记: {name}',
                fix_hint='删除重述标记，直接陈述。若需保留转折，改用更简洁的表达'
            ))
    return issues


def check_c2_explanatory(text, para_idx, para, all_paras):
    """C2: "所谓/即"解释性冗余 —— 所谓……是/即 等解释性标记"""
    issues = []
    patterns = [
        (r'所谓.{0,30}?(?:是|指的是|即)[，,]', '所谓……是……'),
        (r'(?<!\w)即[^使便将是可]{1}', '即（解释性）'),
    ]
    for pat, name in patterns:
        for m in re.finditer(pat, para):
            issues.append(Issue(
                'C2', 'low', 'redundancy', para_idx,
                context=para[max(0, m.start()-20):min(len(para), m.end()+40)],
                detail=f'标记: {name}',
                fix_hint='删除解释性标记，改为直接陈述'
            ))
    return issues


# ═══════════════════════════════════════════════════════
# ── D. 合规检查（4 条，全部全文级）──
# ═══════════════════════════════════════════════════════

def check_d1_intro_turn(text, para_idx, para, all_paras):
    """D1: 引言部分必须有"然而/但是/不过"转折 [I2]"""
    intro_match = re.search(r'(?:问题的提出|引言).*?(?=##\s*二[、,，])', text, re.DOTALL)
    if intro_match:
        intro = intro_match.group()
        if not re.search(r'然而|但是|不过', intro):
            return [Issue(
                'D1', 'low', 'compliance', -1,
                context='引言部分',
                detail='未检测到"然而/但是/不过"转折词（非强制性提示）',
                fix_hint='可考虑在引言中通过转折引出研究缺口，但非硬性要求 [write module I2]'
            )]
    return []


def check_d2_citation_variety(text, para_idx, para, all_paras):
    """D2: 引用形式多样性 —— 需 ≥3 种引用形式"""
    full = '\n'.join(all_paras)
    author_year_lead = len(re.findall(r'[一-鿿]{2,4}[（(]\d{4}[）)]', full))
    parenthetical = len(re.findall(r'[（(][一-鿿]{2,4}[^）)]{0,20}\d{4}[）)]', full))
    domain_name = len(re.findall(r'既有[^\n]{2,20}研究[^\n]{0,10}(?:表明|指出|认为|普遍)', full))
    concept_lead = len(re.findall(r'[“”][^“”]{2,20}[“”](?:这一概念|这一术语)', full))

    variety_score = sum(1 for x in [author_year_lead, parenthetical, domain_name, concept_lead] if x >= 3)
    if variety_score < 3:
        return [Issue(
            'D2', 'medium', 'compliance', -1,
            context='全文引用形式统计',
            detail=f'作者-年份前置:{author_year_lead} | 后置括注:{parenthetical} | 领域代作者:{domain_name} | 概念引领:{concept_lead}',
            fix_hint=f'当前仅有 {variety_score}/4 种引用形式。需 ≥3 种 [write module L5]'
        )]
    return []


def check_d3_conclusion_ending(text, para_idx, para, all_paras):
    """D3: 结论不以研究限制结尾 [C6]"""
    concl_match = re.search(r'(?:五、结论|结论与讨论).*', text, re.DOTALL)
    if not concl_match:
        return []
    concl = concl_match.group()
    concl_paras = [p.strip() for p in concl.split('\n\n') if len(p.strip()) > 30]
    if not concl_paras:
        return []
    last_para = concl_paras[-1]
    if re.match(r'(?:本文的?(?:局限|不足|限制)|研究(?:局限|不足|限制))', last_para):
        return [Issue(
            'D3', 'medium', 'compliance', -1,
            context=last_para[:200],
            detail='结论以研究限制结尾',
            fix_hint='将研究限制移至倒数第二段，最后一段以未来展望收尾 [write module C6]'
        )]
    return []


def check_d4_unnecessary_quotes(text, para_idx, para, all_paras):
    """D4: 逐条引号检视 —— 每一处引号拉出由 AI 判断必要性（必要最少原则）"""
    issues = []
    seq = 0

    for p_idx, p in enumerate(all_paras):
        if _is_ref_entry(p) or _is_english_heavy(p):
            continue

        quotes_cn = re.findall(r'“[^“”]{1,300}”', p)
        quotes_en = re.findall(r'"[^"]{1,300}"', p)

        for q in quotes_cn + quotes_en:
            inner = q[1:-1]
            inner_len = len(inner)
            seq += 1

            q_pos = p.find(q)
            ctx_start = max(0, q_pos - 30)
            ctx_end = min(len(p), q_pos + len(q) + 30)
            context_window = p[ctx_start:ctx_end]
            context_highlighted = context_window.replace(q, f'「{q}」')

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


def check_d5_param_pvalue_density(text, para_idx, para, all_paras):
    """D5: 量化论文参数p值行内密度检测。

    定量论文中发现应以叙述性语言呈现，统计参数应收入表格而非散布于正文。
    检测所有行内 p 值表述（含系数伴随、p值、经验p值等变体），避免正文沦为回归输出堆砌。

    覆盖模式：
      系数从2.983（p<0.01）        → 系数 + 数字 + 括号p值
      保持在0.184（p<0.01）        → 数字 + 括号p值（无系数关键词）
      （有序logit系数-0.002，p=0.935）→ 模型名 + 系数 + p值
      （系数0.268，p<0.01）         → 传统系数-p值对
      bdiff经验p值0.010            → p值变体
      p=0.935                      → 裸p值
    """
    issues = []

    # 核心 p 值模式（最通用的指标）
    # p<0.01, p<0.05, p<0.10, p=0.935, p = 0.088 等
    pval_re = re.compile(r'(?<![a-zA-Z])p\s*[<>=＝]\s*0?\.\d+')

    # p值 / 经验p值 变体（bdiff 输出常见）
    pval_named_re = re.compile(r'(?:经验)?p值\s*\d+\.\d+')

    # 逐段落统计
    para_matches = []
    for p_idx, p in enumerate(all_paras):
        if _is_ref_entry(p) or _is_english_heavy(p):
            continue
        # 跳过表格行、代码块和表格注释
        if p.startswith('|') or p.startswith('`') or p.startswith('$$'):
            continue
        # 跳过表格显著性标注行（如 "* p<0.10, ** p<0.05, *** p<0.01"）
        if re.match(r'^[\*\s]*[*†‡§¶#]+\s*p\s*[<]', p):
            continue
        # 跳过表格注释行（如 "*注：..."）
        if re.match(r'^\*注[：:]', p):
            continue

        pvals = pval_re.findall(p)
        pvals_named = pval_named_re.findall(p)

        # 去重计数（同一位置可能被两种模式捕获）
        total = len(pvals) + len(pvals_named)

        if total >= 3:
            para_matches.append((p_idx, total, p))

    # 全文总计
    total_paper = sum(m for _, m, _ in para_matches)

    # 报告：段落级（≥3处/段）为 high，全文级（≥10处）为 medium
    for p_idx, cnt, p in para_matches:
        # 提取 p 值上下文用于展示
        pval_samples = pval_re.findall(p) + pval_named_re.findall(p)
        samples_str = '、'.join(pval_samples[:6])
        issues.append(Issue(
            'D5', 'high', 'compliance', p_idx,
            context=p[:250],
            detail=f'该段 {cnt} 处行内 p 值表述：{samples_str}',
            fix_hint='正文禁止出现系数值与p值的行内配对（如"系数0.268，p<0.01"或"0.268（p<0.01）"）。统计参数全部收入表格，正文仅以定性语言报告方向与显著性层级：正向显著、在1%水平上正向显著、不显著、边际显著。唯一例外：置换检验的精确p值（如"经验p值0.010"）可保留，但每段不超过1处。'
        ))

    if total_paper >= 10 and not any(i.para_idx == -2 for i in issues):
        issues.append(Issue(
            'D5', 'medium', 'compliance', -2,
            context=f'全文共计 {total_paper} 处行内 p 值表述',
            detail=f'全文行内 p 值表述密度过高（{total_paper} 处）',
            fix_hint='统计参数全部收入表格。正文仅以定性语言报告方向与显著性层级：正向显著、在1%/5%/10%水平上显著、不显著、边际显著。禁止系数值与p值的行内配对。'
        ))

    return issues


def check_d7_journal_book_in_text(text, para_idx, para, all_paras):
    """D7: 正文嵌入期刊名/书名检测。

    检测正文中嵌入完整期刊名或书名的非学术写法，包括：
      - 在《XX》上发表 / 在《XX》上刊发 / 发表于《XX》
      - 在《XX》中 / 在其《XX》一书中 / 在其《XX》著作中
      - 《XX》上的研究 / 《XX》的最新综述
      - 《XX》（英文名）模式中的中文书名嵌入

    期刊名和书名应仅出现在参考文献条目中，正文使用作者-年份引用格式。
    """
    if _is_ref_entry(para):
        return []

    issues = []

    # ── 模式1：在《XX》上发表/刊发 ──
    pub_patterns = [
        (r'在《[^》]{1,40}》[上中]发[表刊]', '在《XX》上发表/刊发'),
        (r'发表于《[^》]{1,40}》', '发表于《XX》'),
        (r'在《[^》]{1,40}》[上中]的', '在《XX》上的'),
        (r'《[^》]{1,40}》[上中]的(?:最新|开创性|系统|一项|这篇|该)?', '《XX》上的（研究/综述等）'),
    ]
    for pat, name in pub_patterns:
        for m in re.finditer(pat, para):
            # 排除参考文献条目中常见的 "发表于《XX》"
            issues.append(Issue(
                'D7', 'high', 'compliance', para_idx,
                context=para[max(0, m.start()-30):min(len(para), m.end()+40)],
                detail=f'{name}：正文中嵌入了完整期刊名',
                fix_hint='期刊名应仅出现在参考文献条目中。正文使用作者-年份引用格式。如"张三（2020）在《社会学研究》上发表"→"张三（2020）"；"发表于《管理世界》"→删除，改为作者-年份引用。'
            ))

    # ── 模式2：在其《XX》一书中/著作中 ──
    book_patterns = [
        (r'在其《[^》]{1,50}》一[书中]', '在其《XX》一书中'),
        (r'在其(?:民族志)?著作《[^》]{1,50}》[中里]', '在其著作《XX》中'),
        (r'在其《[^》]{1,50}》教材中', '在其《XX》教材中'),
        (r'的(?:经典)?著作《[^》]{1,50}》[中里]', '的著作《XX》中'),
    ]
    for pat, name in book_patterns:
        for m in re.finditer(pat, para):
            issues.append(Issue(
                'D7', 'high', 'compliance', para_idx,
                context=para[max(0, m.start()-30):min(len(para), m.end()+40)],
                detail=f'{name}：正文中嵌入了完整书名',
                fix_hint='书名应仅出现在参考文献条目中。正文使用作者-年份引用格式。如"在其《公共领域》一书中"→删去书名，仅保留"洛夫兰（Lofland，1998）"；"在其民族志著作《为生命而舞》中"→"黄（Huang，2025）"。'
            ))

    # ── 模式3："一文中"/"该文"非学术口语 ──
    colloquial_patterns = [
        (r'.{2,20}一文中', '一文中'),
        (r'该文[^献档]', '该文'),
    ]
    for pat, name in colloquial_patterns:
        for m in re.finditer(pat, para):
            issues.append(Issue(
                'D7', 'high', 'compliance', para_idx,
                context=para[max(0, m.start()-20):min(len(para), m.end()+40)],
                detail=f'"{name}"：非学术口语表述',
                fix_hint='"一文中""该文"属于非学术口语。改为作者-年份引用格式或直接陈述。如"张三（2020）一文中"→"张三（2020）"；"该文指出"→"该研究指出"或删除换为引文。'
            ))

    return issues if issues else []


def check_d8_bilingual_paren_gloss(text, para_idx, para, all_paras):
    """D8: 中英对照括号过度使用检测。

    中文论文中过度使用 English（中文）或 中文（English）对照括号，
    是翻译腔或 AI 生成文本的典型特征，破坏行文流畅性。

    检测三种模式：
      1. 英文词（中文翻译）——英文在前、中文在后，属翻译稿写法
      2. 同一段落中 中文（英文）出现 ≥3 次
      3. 全文同一术语的 中文（英文）括号标注重复出现（首次标注可接受）

    《社会学研究》等中文期刊的惯例：
      - 成熟概念直接用中文，无需英文
      - 新概念首现时中文在前、（English）在后，之后统一用中文
      - 禁止 improvised resilience（即兴韧性）这种英文在前的写法
    """
    if _is_ref_entry(para):
        return []

    issues = []

    # ── 模式1：英文词（中文翻译）——英文在前，中文翻译在后 ──
    # 例如：improvised resilience（即兴韧性）、civil inattention（礼貌性不注意）
    # 匹配：至少3个英文字母开头的词 + （中文翻译）
    en_cn_pattern = re.compile(
        r'[A-Za-z][a-z]{2,}(?:\s[A-Za-z][a-z]{2,}){0,4}'
        r'[（(][一-鿿]{2,20}[）)]'
    )
    for m in re.finditer(en_cn_pattern, para):
        matched = m.group()
        issues.append(Issue(
            'D8', 'high', 'compliance', para_idx,
            context=para[max(0, m.start()-15):min(len(para), m.end()+25)],
            detail=f'英文在前、中文在后的对照括号："{matched}"',
            fix_hint='中文论文中不应出现"English（中文）"的写法。改为中文在前或仅用中文：①若是成熟概念，直接写中文，去掉英文；②若是新概念首现，改为"中文（English）"；③后续出现时只用中文。'
        ))

    # ── 模式2：同一段落内中文（英文）括号标注过于密集（≥3处）──
    cn_en_parens = re.findall(r'[一-鿿]{2,15}[（(][A-Za-z][A-Za-z&\s-]{2,40}[）)]', para)
    # 排除作者-年份引用（如"桑普森等人（Sampson, Raudenbush & Earls，1997）"）
    cn_en_glosses = []
    for m in cn_en_parens:
        inner = re.search(r'[（(]([^）)]+)[）)]', m)
        if inner:
            content = inner.group(1)
            if re.match(r'^[A-Z][a-z]+,\s[A-Z]', content):
                continue
            if re.match(r'^[A-Z][a-z]+(?:&|\sand\s)[A-Z]', content):
                continue
            if re.search(r'\d{4}', content):
                continue
            cn_en_glosses.append(m)

    if len(cn_en_glosses) >= 3:
        samples = '、'.join(cn_en_glosses[:4])
        issues.append(Issue(
            'D8', 'medium', 'compliance', para_idx,
            context=para[:200],
            detail=f'该段 {len(cn_en_glosses)} 处中文（英文）括号标注：{samples}',
            fix_hint='同一段落中出现 ≥3 处中英对照括号，学术写作中过于密集。成熟概念（如"集体效能""社会资本""面子工作"）无需加英文；新概念仅在首现处标注一次。'
        ))

    return issues if issues else []


def check_d6_coding_parens(text, para_idx, para, all_paras):
    """D6: 行内编码说明括号检测。

    检测正文中以括号包裹变量编码规则的模式，如：
      （未签订劳动合同记为1）
      （城镇或居民户口记为1）
      （保留1—5有效取值）

    这类括号内容属于代码簿/附录层级，不应出现在正文行文中。
    正文应概述变量的分析含义，具体编码规则留在附录。
    """
    issues = []

    # 编码赋值关键词
    coding_kw = '(?:记为|定义为|赋值为|取值为|编码为|记作)'

    # 模式1：（条件描述 + 记为/定义为 + 编码值）
    coding_pat = re.compile(
        r'[（(]'
        r'(?![^）)]*(?:p\s*[<>=＝]|p值|经验p|参见|例如|详见|即|如\s|图\d|表\d|注[：:]))'
        r'(?:.{0,15})?'
        + coding_kw +
        r'.{0,30}'
        r'[）)]'
    )

    # 模式2：（保留/限定 + 数字范围）如 （保留1—5有效取值）、（取值范围1—5）
    val_range_pat = re.compile(
        r'[（(]'
        r'(?:保留|限[定于]|仅保留|取值[范围]?|限定范围)'
        r'.{0,30}'
        r'\d'
        r'.{0,15}'
        r'[）)]'
    )

    # 逐段落扫描
    for p_idx, p in enumerate(all_paras):
        if _is_ref_entry(p) or _is_english_heavy(p):
            continue
        if p.startswith('|') or p.startswith('`') or p.startswith('$$'):
            continue
        # 跳过表格下方的注释行（以"注："或"* "开头）
        if re.match(r'^[\*\s]*[注註*]', p):
            continue

        matches_coding = coding_pat.findall(p)
        matches_range = val_range_pat.findall(p)
        all_parens = [m for m in re.finditer(r'[（(][^）)]*(?:记为|定义为|赋值为|取值为|编码为|记作|保留|限[定于]|仅保留|取值)[^）)]*[）)]', p)]

        if all_parens:
            samples = [m.group()[:50] for m in all_parens[:5]]
            samples_str = '、'.join(samples)
            issues.append(Issue(
                'D6', 'high', 'compliance', p_idx,
                context=p[:250],
                detail=f'{len(all_parens)} 处行内编码说明括号：{samples_str}',
                fix_hint='正文不应出现变量编码操作指令（记为/定义为/赋值为/保留取值等括号）。将编码规则移至附录，正文仅保留变量的分析含义概述。例如"（未签订劳动合同记为1）"→正文只需说明"风险暴露指数由四类风险加总构成，具体编码见附录"。'
            ))

    return issues


def check_d9_abbreviation_overuse(text, para_idx, para, all_paras):
    """D9: 英文缩写过度使用 / 跨节未重新展开。

    中文学术写作中，英文缩写应在每大节首次出现时重新给出全称。
    检测三项：
      1. 段落内缩写密度过高（≥4 处）→ high
      2. 跨节使用但未在当节重新展开 → medium
      3. 同一缩写多次出现但未与中文全称交替 → medium
    """
    if _is_ref_entry(para) or _is_english_heavy(para):
        return []
    if para.startswith('|') or para.startswith('`'):
        return []

    issues = []

    # 检测大写拉丁缩写（2-5 字符）
    abbr_re = re.compile(r'\b([A-Z]{2,5})\b')
    compound_re = re.compile(r'\b([A-Z]{2,5}[-+][A-Z]{2,5})\b')

    abbrs_simple = [m.group(1) for m in abbr_re.finditer(para)]
    abbrs_compound = [m.group(1) for m in compound_re.finditer(para)]
    all_abbrs = abbrs_simple + abbrs_compound

    if not all_abbrs:
        return []

    unique_abbrs = list(dict.fromkeys(all_abbrs))

    # ── D9a: 段落缩写密度过高 ──
    if len(all_abbrs) >= 4:
        issues.append(Issue(
            'D9', 'high', 'compliance', para_idx,
            context=para[:250],
            detail=f'该段英文缩写密度过高：{len(all_abbrs)} 处（{", ".join(unique_abbrs[:8])}）',
            fix_hint='中文学术论文不应依赖英文缩写。直接使用中文全称——"自我决定理论"而非 SDT、"激情二元模型"而非 DMP、"社会交换理论"而非 SET。英文缩写是英文学术写作的习惯，在中文学术写作中属于冗余杂质，会打断读者阅读节奏。保留缩写仅在两种情形：复合模型名（如 SDT-DMP 双阶段模型）和统计方法标准缩写（如 SEM、CFA）。'
        ))

    # ── D9b: 检查该段中的缩写是否在当段或附近段落有中文全称定义 ──
    definition_re = re.compile(
        r'[一-鿿]{2,20}'
        r'[（(]'
        r'(?:[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,5}[，,]\s*)?'
        r'([A-Z]{2,5})'
        r'[）)]'
    )
    # 在当段及前后各2段中搜索定义
    search_start = max(0, para_idx - 2)
    search_end = min(len(all_paras), para_idx + 3)
    search_text = '\n'.join(all_paras[search_start:search_end])
    defined_nearby = set()
    for m in definition_re.finditer(search_text):
        defined_nearby.add(m.group(1))

    undefined_abbrs = [a for a in unique_abbrs if a not in defined_nearby]
    if undefined_abbrs and len(unique_abbrs) >= 2:
        issues.append(Issue(
            'D9', 'medium', 'compliance', para_idx,
            context=para[:200],
            detail=f'附近未找到中文全称定义的缩写：{", ".join(undefined_abbrs[:5])}',
            fix_hint=f'中文学术论文应优先使用中文全称而非英文缩写。该段使用的缩写（{", ".join(undefined_abbrs[:5])}）在前后2段内未见全称定义。建议直接以中文全称替代这些缩写，而非补充定义。英文学术写作习惯不适用于中文学术写作语境。'
        ))

    return issues if issues else []


def check_d10_arrow_shorthand(text, para_idx, para, all_paras):
    """D10: 括号内箭头速记符号检测。

    中文学术论文的正文应使用自然语言描述变量关系和方向，
    不应出现括号内以箭头（↑↓→）标注方向的速记写法，如：
      （深度↑、享受↑、倦怠↓）
      （频率↑但享受↓）
    这种写法属于表格注释或 PPT 讲义风格，不属于学术论文正文的规范表达。
    """
    if _is_ref_entry(para) or _is_english_heavy(para):
        return []
    if para.startswith('|') or para.startswith('`'):
        return []

    issues = []

    # 检测括号内含 ↑ 或 ↓ 的内容（每个括号独立计数）
    arrow_parens = re.findall(r'（([^）]{3,120}[↑↓][^）]{0,120})）', para)
    if arrow_parens:
        samples = [m[:60] for m in arrow_parens[:3]]
        issues.append(Issue(
            'D10', 'high', 'compliance', para_idx,
            context=para[:250],
            detail=f'{len(arrow_parens)} 处括号内箭头速记：{"; ".join(samples)}',
            fix_hint='学术论文正文不应出现"（XX↑、XX↓）"式箭头速记。应改为自然语言描述方向和关系。例如"（深度↑、享受↑、倦怠↓）"→改写为"即深度更高、享受感更强、倦怠程度更低"。箭头速记属于表格或 PPT 讲义的写法。'
        ))

    return issues if issues else []


def check_d11_excessive_parens(text, para_idx, para, all_paras):
    """D11: 括号插入语密度过高 / 可融入括号检测。

    中文学术论文中过度使用括号插入语是翻译腔或 AI 生成文本的典型特征。
    括号打断句子节奏，迫使读者在两条思维路径之间切换。
    大多数括号插入语（解释、列举、补充说明）可以融入主句或以逗号引出。

    检测三项：
      1. 段落内括号密度过高（≥4 对）→ high
      2. 全中文括号插入语（无引用/技术标记）→ medium（逐条标记，每段最多3条）
      3. 以"如/即/例如/包括"开头的可融入括号 → medium
    """
    if _is_ref_entry(para) or _is_english_heavy(para):
        return []
    if para.startswith('|') or para.startswith('`'):
        return []

    issues = []

    # 提取所有中文括号内容
    all_parens = re.findall(r'（([^）]{1,300})）', para)

    # 排除引用类括号（含年份+作者名、统计量、p值）
    technical_parens = []
    prose_parens = []
    for p in all_parens:
        stripped = p.strip()
        # 纯年份/数字引用：仅含数字、分号、逗号、空格和少量标点
        if re.match(r'^[\d\s,;，；、&\-–—\.]+$', stripped) and re.search(r'\d{4}', stripped):
            technical_parens.append(p)
            continue
        # 引用/技术类：含 4 位数字年份 + 英文名，或统计符号
        if re.search(r'\d{4}', stripped) and re.search(r'[A-Z]', stripped):
            technical_parens.append(p)
            continue
        if re.search(r'[≈β=<>][\s\d]', stripped) or re.search(r'[np]\s*[<>=]', stripped):
            technical_parens.append(p)
            continue
        if re.search(r'[pfn]\s*[=<>]', stripped) or re.search(r'Δ\w', stripped):
            technical_parens.append(p)
            continue
        # 纯英文缩写标记（量表名、统计方法等）
        if re.match(r'^[A-Z]{2,6}$', stripped) or re.match(r'^[A-Z][a-z]+\s[A-Z]', stripped):
            technical_parens.append(p)
            continue
        # 混合模式：含英文名的中英对照定义（首次定义可接受）
        if re.search(r'[A-Z][a-z]{3,}', stripped) and len(stripped) < 60:
            technical_parens.append(p)
            continue
        prose_parens.append(p)

    # ── D11a: 段落括号密度过高（仅统计可融入的散文性括号，排除引用和技术标注）──
    if len(prose_parens) >= 4:
        samples = [p.strip()[:40] for p in prose_parens[:4]]
        issues.append(Issue(
            'D11', 'high', 'compliance', para_idx,
            context=para[:250],
            detail=f'该段可融入括号过多：{len(prose_parens)} 对非技术性括号插入语（{"; ".join(samples)}）',
            fix_hint='中文学术论文应避免括号插入语打断句子节奏。解释性内容改为逗号引出，列举性内容改为自然叙述，补充说明改写为独立短句。引用和技术标注的括号保留。'
        ))

    # ── D11b: 全中文可融入括号插入语 ──
    integrable_count = 0
    samples = []
    for p in prose_parens:
        stripped = p.strip()
        chinese_chars = len(re.findall(r'[一-鿿]', stripped))
        # 至少含3个中文字符，以中文为主
        if chinese_chars < 3:
            continue
        integrable_count += 1
        if len(samples) < 4:
            samples.append(stripped[:40])

    if integrable_count >= 3:
        issues.append(Issue(
            'D11', 'medium', 'compliance', para_idx,
            context=para[:250],
            detail=f'{integrable_count} 处中文括号插入语可融入正文：{"; ".join(samples[:3])}',
            fix_hint='全中文括号插入语几乎都可以融入正文。改写方式：(1) 括号内为解释→用逗号或"即"引出；(2) 括号内为列举→改为冒号引出或自然叙述；(3) 括号内为补充说明→改为独立短句或"其中""例如"引出。'
        ))

    # ── D11c: 以信号词开头的可融入括号 ──
    signal_parens = [p for p in prose_parens if re.match(r'^(?:如|即|例如|包括|尤其是|特别是|正如|其中)', p.strip())]
    if signal_parens:
        samples_str = '; '.join([p.strip()[:50] for p in signal_parens[:3]])
        issues.append(Issue(
            'D11', 'medium', 'compliance', para_idx,
            context=para[:250],
            detail=f'{len(signal_parens)} 处以"如/即/例如/包括"等开头的括号插入语：{samples_str}',
            fix_hint='以"如/即/例如"开头的括号插入语可以通过逗号直接融入主句。例如"（如张三，2020）"→"，如张三（2020）"；"（即前文所述机制）"→"，即前文所述机制"。去掉括号，用逗号衔接。'
        ))

    return issues if issues else []


# ═══════════════════════════════════════════════════════
# 规则注册表（27 条）
# ═══════════════════════════════════════════════════════

ALL_RULES = [
    # A. 句式反模式（7 条，全部段落级）
    Rule('A1', '不是……而是……句式（含9种变体）', 'high', 'syntax', check_a1_bushi),
    Rule('A2', '"对……进行……"冗长句式', 'low', 'syntax', check_a2_dui_jinxing),
    Rule('A3', '"通过……来……"冗长句式', 'low', 'syntax', check_a3_tongguo_lai),
    Rule('A4', '"在……中/上/下"冗余前置', 'low', 'syntax', check_a4_zai_locative),
    Rule('A5', '"一方面……另一方面……"框套', 'low', 'syntax', check_a5_yifangmian),
    Rule('A6', '"正是……才……"强调框套', 'low', 'syntax', check_a6_zhengshi_cai),
    Rule('A7', '"之所以……是因为……"句式（AI口癖）', 'medium', 'syntax', check_a7_zhi_suoyi),

    # B. 标点与节奏（8 条，全部段落级）
    Rule('B1', '破折号综合检测（存在/双插入语/机械替换痕迹）', 'high', 'rhythm', check_b1_dash),
    Rule('B2', '超长单句 (>150字)', 'medium', 'rhythm', check_b2_long_sentence),
    Rule('B3', '分号滥用 (≥3个/段)', 'low', 'rhythm', check_b3_semicolon_abuse),
    Rule('B4', '超长段落 (>500字)', 'medium', 'rhythm', check_b4_long_paragraph),
    Rule('B5', '排比/列举 ≥4项', 'low', 'rhythm', check_b5_parallelism),
    Rule('B6', '英文直引号 / 引号配对错误', 'high', 'rhythm', check_b6_quote_marks),
    Rule('B7', '弱冒号模式（短引导语+冒号+完整从句）', 'medium', 'rhythm', check_b7_weak_colon),
    Rule('B8', '可融入括号插入语（含融入信号词的短括号）', 'medium', 'rhythm', check_b8_integrable_paren),

    # C. 冗余标记（2 条，全部段落级）
    Rule('C1', '冗余重述标记（换言之/也就是说/这意味着等）', 'low', 'redundancy', check_c1_redundant_markers),
    Rule('C2', '"所谓/即"解释性冗余', 'low', 'redundancy', check_c2_explanatory),

    # D. 合规检查（8 条，D7、D8 为段落级）
    Rule('D1', '引言转折词提示 [I2]（非强制）', 'low', 'compliance', check_d1_intro_turn, scope='full'),
    Rule('D2', '引用形式单一', 'medium', 'compliance', check_d2_citation_variety, scope='full'),
    Rule('D3', '结论以限制结尾 [C6]', 'medium', 'compliance', check_d3_conclusion_ending, scope='full'),
    Rule('D4', '逐条引号检视（必要最少原则）', 'medium', 'compliance', check_d4_unnecessary_quotes, scope='full'),
    Rule('D5', '量化论文参数p值行内密度 [E-new]', 'high', 'compliance', check_d5_param_pvalue_density, scope='full'),
    Rule('D6', '行内编码说明括号 [M0b]', 'high', 'compliance', check_d6_coding_parens, scope='full'),
    Rule('D7', '正文嵌入期刊名/书名（在《XX》上发表/在其《XX》中/发表于《XX》）', 'high', 'compliance', check_d7_journal_book_in_text),
    Rule('D8', '中英对照括号过度使用（English（中文）/ 中文（English）泛滥）', 'high', 'compliance', check_d8_bilingual_paren_gloss),
    Rule('D9', '英文缩写过度使用 / 跨节未重新展开', 'high', 'compliance', check_d9_abbreviation_overuse),
    Rule('D10', '括号内箭头速记符号（↑↓→）', 'high', 'compliance', check_d10_arrow_shorthand),
    Rule('D11', '括号插入语密度过高 / 可融入括号', 'high', 'compliance', check_d11_excessive_parens),
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
        if rule.scope == 'full':
            result = rule.check(text, 0, '', all_paras)
            if result:
                all_issues.extend(result)
        else:
            for p_idx, para in enumerate(all_paras):
                result = rule.check(text, p_idx, para, all_paras)
                if result:
                    all_issues.extend(result)

    sev_order = {'high': 0, 'medium': 1, 'low': 2}
    all_issues.sort(key=lambda x: (sev_order.get(x.severity, 3), x.para_idx))
    return all_issues


# ═══════════════════════════════════════════════════════
# 输出：改写指令 Markdown
# ═══════════════════════════════════════════════════════

# 全局 IRON RULES（生成改写指令时置顶）
IRON_RULES = [
    '改写后不得引入新的"不是……而是……"句式。',
    '不得用标点符号机械替换破折号（如 ——→：、——→，、——→（））。必须 AI 自然重写整个句子。若原句依赖破折号才能表达语义关系（解释、转折、递进、插入），则句子结构本身需要重构。',
    '改写后正文中不得出现任何破折号（——）。',
    '改写后不得引入新的"之所以……是因为……"句式（AI 口癖）。',
    '不得用脚本或正则机械替换标点符号。所有标点修改必须由 AI 理解句意后自然重写句子。',
]


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

    # IRON RULES
    lines.append('---\n')
    lines.append('## 改写任务清单\n')
    lines.append('> **执行方式**：从上到下逐条处理。每条任务包含：要修改的原文 + 改写要求。\n')
    for i, ir in enumerate(IRON_RULES):
        lines.append(f'> **IRON RULE {i+1}**：{ir}\n')
    lines.append('')

    # 逐条改写任务
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
    return 0


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
    hi = sum(1 for i in issues if i.severity == 'high')
    md_count = sum(1 for i in issues if i.severity == 'medium')
    lo = sum(1 for i in issues if i.severity == 'low')
    print(f'改写指令已生成 → {out}')
    print(f'共 {len(issues)} 条任务（高{hi} 中{md_count} 低{lo}）')
    print(f'\n请将以下 prompt 发送给当前宿主 agent：')
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
  %(prog)s --instructions paper.md      # 生成改写指令 MD（供当前宿主 agent 执行）
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
