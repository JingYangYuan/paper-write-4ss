#!/usr/bin/env python3
"""
中文学术写作综合扫描器 —— 纯检测 + 生成改写指令。绝不自动修改原文。

  工作流：扫描 → 生成指令 MD → AI 自然重写句子 → 再扫描 → 循环至 🔴high 归零。

严重度语义（与 resources/style_gate.md 三层对齐）：
  high   = 规范层硬错：引号配对、缩写未展开、箭头速记、引号滥用、诚信问题。
           可机械核验，故要求归零。
  medium = 惯例层：句式与标点密度、系数行内报告、书名入正文、中英对照密度、
           编码括号。只生成改写指令，是否采纳由作者与审查文件决定。
  low    = 偏好层：括号插入语密度等本仓库风格选择，仅作提示。

预算制（DOC_BUDGETS，按十篇顶刊语料校准，见 99-经验总结报告）：
  同一规则的全篇检出次数超过预算 → 全部升级为 high，必须改写到预算内。
  语料中零出现的模式（后文预告、自我辩护否定、管理学黑话）预算为 0。
  语料中真实出现的模式给小额预算（如"不是……而是"≤ 2、"首次"≤ 2）。

覆盖规则（38 条，按六大类组织）：
  A. 句式反模式（7 条）
  B. 标点与节奏（8 条）
  C. 冗余标记（2 条）
  D. write module 标准合规（11 条）
  E. 防御性写法与八股元话语（9 条，预算制）
     E1 前向结构预告（下文将/下一节将……，语料零出现）
     E2 防御性否定（这并不意味着/或许有人会……，语料零出现）
     E3 强调性元话语（值得注意的是/需要指出的是，预算 1）
     E4 缺陷总结散布（"本文的不足"出现在非尾部章节）
     E5 复述型元话语（综上所述/正如前文所述，预算 2）
     E6 自夸硬宣称（填补空白/开创性/里程碑，预算 0）
     E7 八股四字格（方兴未艾/日新月异/由此可见，预算 1）
     E8 管理学黑话（赋能/抓手/闭环/底层逻辑，预算 0）
     E9 "首次"宣称（语料中限定范围的"首次尝试"可用，预算 2）
  F. 引文一致性（2 条）
     F1 罗列式综述（只综不述：≥ 3 句作者（年份）开头且无争论定位词）
     F3 夹注与参考文献表交叉核对（作者-年份组合对不上 → 疑似张冠李戴）

用法：
  python writing_scanner.py --scan <file.md>            # 快速扫描统计
  python writing_scanner.py --report <file.md>          # 完整 Markdown 报告
  python writing_scanner.py --instructions <file.md>    # 生成结构化改写指令 MD
  python writing_scanner.py --check <file.md>           # JSON 机读结果（闸门用，high>0 时退出码 1）
  python writing_scanner.py --budgets                   # 打印预算表
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
    (r'与其[^。\n]{0,60}不如[^。\n]{0,200}?(?:[。\.]|$)', '与其……不如……'),
    (r'与其说.{0,80}毋宁说.{0,200}?(?:[。\.]|$)', '与其说……毋宁说……'),
]

def check_a1_bushi(text, para_idx, para, all_paras):
    """A1: 不是……而是…… 及其 9 种变体"""
    issues = []
    for pat, name in BUSHI_PATTERNS:
        for m in re.finditer(pat, para):
            issues.append(Issue(
                'A1', 'medium', 'syntax', para_idx,
                context=m.group()[:200],
                detail=f'变体: {name}',
                fix_hint='先否定后肯定是汉语学术论证的基本手段，不必逢遇必改（见 style_gate.md exp-negpos-01）。仅在以下情形改写：同一节内三次以上，或该结构成为段落主干。改写时直接陈述B，把A处置为次要补充；若被否定的那一项正是本文要驳倒的既有立场，保留原结构。'
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

    # ── B1a: 破折号密度（同段超过两处才报，单处正常使用不报）──
    cnt = para.count('——')
    if cnt >= 3:
        issues.append(Issue(
            'B1', 'medium', 'rhythm', para_idx,
            context=para[:200],
            detail=f'{cnt} 个 ——（{len(para)} 字段落，{cnt/(len(para)/100):.1f}/百字）',
            fix_hint='破折号是 GB/T 15834 列明的规范标点，正常使用不必改写（见 style_gate.md exp-dash-01）。本段密度偏高：保留承担真实解释功能的一处，其余改由从句顺接或独立短句。改写须重写句子，不得用冒号、逗号或括号机械换位。'
        ))

    # ── B1b: 双破折号插入语 ——……—— ──
    double_dash = re.findall(r'——[^。\n——]{3,50}——', para)
    if double_dash:
        issues.append(Issue(
            'B1', 'medium', 'rhythm', para_idx,
            context=para[:200],
            detail=f'{len(double_dash)} 处双——插入语：{double_dash[0][:60]}',
            fix_hint='双破折号插入语打断句子，宜融入主句或改为独立句子。改写须重写句子，不得机械替换标点。'
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
            'D5', 'medium', 'compliance', p_idx,
            context=p[:250],
            detail=f'该段 {cnt} 处行内 p 值表述：{samples_str}',
            fix_hint='正文以方向与显著性层级叙述、完整参数入表，不逐格复述回归表（见 style_gate.md exp-param-01）。本段行内参数密集，保留真正需要比较效应量、解释边际效应或锁定机制的那一处，并说明量纲与参照类别；其余改为定性叙述。判据是这段文字在解释结果，还是在复读表格。'
        ))

    if total_paper >= 10 and not any(i.para_idx == -2 for i in issues):
        issues.append(Issue(
            'D5', 'low', 'compliance', -2,
            context=f'全文共计 {total_paper} 处行内 p 值表述',
            detail=f'全文行内 p 值表述密度过高（{total_paper} 处）',
            fix_hint='全文行内参数偏多时，优先把可表格化的结果移入表格，保留需要解释的那几处（style_gate.md exp-param-01）。这是风格取舍，不是硬错。'
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
                'D7', 'medium', 'compliance', para_idx,
                context=para[max(0, m.start()-30):min(len(para), m.end()+40)],
                detail=f'{name}：正文中嵌入了完整期刊名',
                fix_hint='期刊名与卷期不进正文，改用作者-年份夹注（style_gate.md exp-booktitle-01）。如"张三（2020）在《社会学研究》上发表"→"张三（2020）"；"发表于《管理世界》"→删去刊名，保留作者-年份。'
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
                'D7', 'medium', 'compliance', para_idx,
                context=para[max(0, m.start()-30):min(len(para), m.end()+40)],
                detail=f'{name}：正文中嵌入了完整书名',
                fix_hint='先确认这个书名是论证对象还是文献出处（style_gate.md exp-booktitle-01）。若是论证对象（如"费孝通在《乡土中国》中把差序格局描述为……"），保留书名并补作者与年份；若只是出处标注，改作者-年份夹注。'
            ))

    # ── 模式3："一文中"/"该文"非学术口语 ──
    colloquial_patterns = [
        (r'.{2,20}一文中', '一文中'),
        (r'该文[^献档]', '该文'),
    ]
    for pat, name in colloquial_patterns:
        for m in re.finditer(pat, para):
            issues.append(Issue(
                'D7', 'medium', 'compliance', para_idx,
                context=para[max(0, m.start()-20):min(len(para), m.end()+40)],
                detail=f'"{name}"：回指表述',
                fix_hint='指代必须落在具体文献上（style_gate.md exp-yiwen-01）。"张三（2020）提出"优于"该文提出"；同段内确需回指时"该文"可用一次，跨段回指须重出作者与年份。'
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
                'D6', 'medium', 'compliance', p_idx,
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

    检测三项（均属偏好层，仅提示）：
      1. 段落内括号密度过高（≥4 对）→ low
      2. 全中文括号插入语（无引用/技术标记）→ low（逐条标记，每段最多3条）
      3. 以"如/即/例如/包括"开头的可融入括号 → low
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
            'D11', 'low', 'compliance', para_idx,
            context=para[:250],
            detail=f'该段可融入括号过多：{len(prose_parens)} 对非技术性括号插入语（{"; ".join(samples)}）',
            fix_hint='括号插入语是学术写作的正常节奏工具，保留与否由句子节奏决定（style_gate.md exp-paren-01）。本段数量偏多，优先处理那些可用逗号顺接的解释性插入；引用与技术参数括号照常使用。'
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
            'D11', 'low', 'compliance', para_idx,
            context=para[:250],
            detail=f'{integrable_count} 处中文括号插入语可融入正文：{"; ".join(samples[:3])}',
            fix_hint='这些括号可以融入正文，但不是必须：(1) 括号内为解释→可用逗号或"即"引出；(2) 括号内为列举→可改冒号引出；(3) 括号内为补充说明→可改独立短句。保留括号也有理由（防歧义、标出旁注），取舍记入审查文件。'
        ))

    # ── D11c: 以信号词开头的可融入括号 ──
    signal_parens = [p for p in prose_parens if re.match(r'^(?:如|即|例如|包括|尤其是|特别是|正如|其中)', p.strip())]
    if signal_parens:
        samples_str = '; '.join([p.strip()[:50] for p in signal_parens[:3]])
        issues.append(Issue(
            'D11', 'low', 'compliance', para_idx,
            context=para[:250],
            detail=f'{len(signal_parens)} 处以"如/即/例如/包括"等开头的括号插入语：{samples_str}',
            fix_hint='以"如/即/例如"开头的括号插入语可以改为逗号衔接（style_gate.md exp-paren-01）；是否改由句子节奏决定，属于风格取舍。'
        ))

    return issues if issues else []


# ═══════════════════════════════════════════════════════
# ═════════════════════════════════════════════════════
# ── E. 防御性写法与八股元话语（预算制，2026-10 十篇顶刊语料校准）──
# ═════════════════════════════════════════════════════

# E1: 前向结构预告（语料十篇零出现 → 预算 0，high）
E1_PREVIEW = re.compile(
    r'(?:下文将|后文将|后文会|将在后文|下文中将|下一[节章]将|'
    r'第[一二三四五六七八九十\d]+[节章]将(?:介绍|讨论|分析|展开|呈现|阐述|说明)|'
    r'详见后文|后见详述|留待后文|将在下文|如下文所示|如后文所示|此点留待)'
)

def check_e1_preview(text, para_idx, para, all_paras):
    hits = E1_PREVIEW.findall(para)
    if hits:
        return [Issue('E1', 'high', 'defense', para_idx,
                      context=para[:250],
                      detail=f'前向结构预告：{hits[0]}（顶刊语料中零出现，读者不需要路线图）',
                      fix_hint='删掉预告句。章节该说什么，读者翻到那一章自然知道；预告只暴露对结构的不自信。若怕读者迷路，说明结构本身需要重新。')]
    return []


# E2: 防御性否定与自问自答（语料零出现 → 预算 0，high）
E2_DEFENSE = re.compile(
    r'(?:这并(?:不意味着|不代表)|笔者无意|笔者深知|难免存在|(?:或许|可能)有人会(?:认为|质疑|问)|'
    r'有人可能会(?:认为|质疑|问)|不难发现|无需赘言|自不待言)'
)

def check_e2_defense(text, para_idx, para, all_paras):
    hits = E2_DEFENSE.findall(para)
    if hits:
        return [Issue('E2', 'high', 'defense', para_idx,
                      context=para[:250],
                      detail=f'防御性写法：{hits[0]}（为论文预写辩护，语料零出现）',
                      fix_hint='删掉防御句，直接陈述事实。真有反驳意见，像 Lei 那样在讨论部分先问先答（有证据的回答）；没证据的预设质疑只是稻草人。')]
    return []


# E3: 强调性元话语（语料仅渠敬东 1 处 → 预算 1）
E3_EMPHASIS = re.compile(r'(?:值得注意的是|需要指出的是|需要强调的是|必须指出[，,]?|特别值得注意)')

def check_e3_emphasis(text, para_idx, para, all_paras):
    hits = E3_EMPHASIS.findall(para)
    if hits:
        return [Issue('E3', 'medium', 'defense', para_idx,
                      context=para[:250],
                      detail=f'强调性元话语：{hits[0]}（全篇预算 1 次）',
                      fix_hint='删掉"值得注意的是"直接说事。真正值得注意的内容，读者自己会注意；靠元话语抬高重要性的句子，多半内容本身不够硬。')]
    return []


# E4: 缺陷总结散布（只允许出现在结论/讨论/局限类章节，其余位置 high）
E4_FLAW = re.compile(
    r'(?:本文的不足|本研究的不足|本文的局限|本研究局限|存在以下(?:不足|局限)|'
    r'(?:笔者|作者).{0,6}(?:能力|水平)有限|力有不逮)'
)

_TAIL_HEADINGS = re.compile(r'(结论|讨论|结语|总结|小结|尾议|局限|余论)')

def check_e4_flaw_scatter(text, para_idx, para, all_paras):
    """全文级：逐块扫描，带标题上下文判断是否尾部章节。"""
    issues = []
    current_tail = False
    blocks = re.split(r'\n\s*\n', text)
    p_idx = 0
    for block in blocks:
        stripped = block.strip()
        if re.match(r'^#{1,6}\s', stripped):
            current_tail = bool(_TAIL_HEADINGS.search(stripped))
            continue
        is_para = len(stripped) > 20
        if is_para and not current_tail and E4_FLAW.search(stripped):
            issues.append(Issue('E4', 'high', 'defense', p_idx,
                          context=stripped[:250],
                          detail='缺陷总结出现在非尾部章节：论文正文不应为自己的毛病写辩护',
                          fix_hint='删掉这段自我检讨。具体数据的诚实说明（如周飞舟自报产量浮夸）放脚注；系统性局限只在结论章按"承认→削弱→指向未来"三拍写一次。'))
        if is_para:
            p_idx += 1
    return issues


# E5: 复述型元话语（语料：正如前文所述 1、不再赘述 1 → 预算 2）
E5_RESTATE = re.compile(
    r'(?:综上所述|总而言之|正如前文所述|前文已[经]?[提及指出谈到]|'
    r'上文[提到指出]|不再赘述|通过上述分析|通过以上分析)'
)

def check_e5_restate(text, para_idx, para, all_paras):
    hits = E5_RESTATE.findall(para)
    if hits:
        return [Issue('E5', 'medium', 'defense', para_idx,
                      context=para[:250],
                      detail=f'复述型元话语：{hits[0]}（全篇预算 2 次）',
                      fix_hint='结论不复述前文，而是开新层次：同义反复换成边界条件、反向关系句或未答之问（周飞舟："控制越严密，则越难以知晓地方的实际情况"）。')]
    return []


# E6: 自夸硬宣称（语料零出现 → 预算 0，high）
E6_BOAST = re.compile(
    r'(?:填补了?.{0,8}空白|开创性|开创了?.{0,8}(?:研究|领域|范式)|里程碑式|'
    r'重要的?理论意义和?现实意义|重要的?理论与现实意义)'
)

def check_e6_boast(text, para_idx, para, all_paras):
    hits = E6_BOAST.findall(para)
    if hits:
        return [Issue('E6', 'high', 'defense', para_idx,
                      context=para[:250],
                      detail=f'自夸硬宣称：{hits[0]}（贡献由正文兑现，不由形容词宣称）',
                      fix_hint='删掉宣称句。贡献写法：正文做到了什么写什么（陈龙的类型学贡献是在证据齐备后才补"给埃德沃兹的二分加一格"）。限定范围的具体贡献（如"首次尝试"）另见 E9 预算。')]
    return []


# E7: 八股四字格（语料仅渠敬东 1 处 → 预算 1）
E7_CLICHE = re.compile(
    r'(?:方兴未艾|如火如荼|日新月异|层出不穷|应运而生|不容忽视|毋庸置疑|'
    r'由此可见|大有可为|势在必行|任重道远|意义深远|深刻变革|深刻影响)'
)

def check_e7_cliche(text, para_idx, para, all_paras):
    hits = E7_CLICHE.findall(para)
    if hits:
        return [Issue('E7', 'medium', 'defense', para_idx,
                      context=para[:250],
                      detail=f'八股四字格/空泛形容：{"、".join(sorted(set(hits)))}（全篇预算 1 次）',
                      fix_hint='换成具体内容："日新月异"删掉后写具体变化（陈龙写"直线距离不能超过500米……间隔不能少于5分钟"，具体规则比形容更有冲击力）。')]
    return []


# E8: 管理学黑话（语料零出现 → 预算 0，high）
E8_BUZZ = re.compile(r'(?:赋能|抓手|闭环|底层逻辑|深度融合|颗粒度|组合拳|新质)')

def check_e8_buzz(text, para_idx, para, all_paras):
    hits = E8_BUZZ.findall(para)
    if hits:
        return [Issue('E8', 'high', 'defense', para_idx,
                      context=para[:250],
                      detail=f'管理学黑话/网络流行语：{"、".join(sorted(set(hits)))}（学术语料零出现）',
                      fix_hint='换成实指："赋能"写具体谁给谁提供了什么资源；"底层逻辑"写机制本身；"闭环"写回路的具体环节。')]
    return []


# E9: "首次"宣称（语料中莫怡青 2 处均为限定范围用法 → 预算 2）
E9_FIRST = re.compile(r'首次')

def check_e9_first(text, para_idx, para, all_paras):
    hits = E9_FIRST.findall(para)
    if hits:
        return [Issue('E9', 'medium', 'defense', para_idx,
                      context=para[:250],
                      detail='"首次"宣称（全篇预算 2 次，且须限定范围）',
                      fix_hint='限定范围才可用（"中国背景下的首次尝试"可以，裸的"首次发现"不行）；能删则删，让文献表自己说话。')]
    return []


# ═════════════════════════════════════════════════════
# ── F. 引文一致性（张冠李戴与只综不述）──
# ═════════════════════════════════════════════════════

# F1: 罗列式综述（只综不述）
_F1_CITE_SENT = re.compile(r'^[^，。；、（）]{2,20}（\d{4}）')
_F1_JUDGE = re.compile(
    r'(?:但是|然而|不过|相比之下|相反|其实|实际上|问题在于|争议|分歧|'
    r'矛盾在于|遗憾的是|恰恰|不同的是|却|而对|未能|回避了|避开了|忽视了|简单化)'
)

def check_f1_listing_review(text, para_idx, para, all_paras):
    sentences = split_sentences(para)
    cite_sents = [s for s in sentences if _F1_CITE_SENT.match(s)]
    # 判分词必须在作者自己的句子（非引用开头句）里才算定位；纯罗列段全部句子都是引用句
    own_sents = [s for s in sentences if not _F1_CITE_SENT.match(s)]
    has_own_judgment = any(_F1_JUDGE.search(s) for s in own_sents) if own_sents else False
    if len(cite_sents) >= 3 and not has_own_judgment:
        names = [s[:s.index('（')] if '（' in s else s[:8] for s in cite_sents[:4]]
        return [Issue('F1', 'high', 'citation', para_idx,
                      context=para[:250],
                      detail=f'罗列式综述（只综不述）：{len(cite_sents)} 句以"作者（年份）"开头并列转述（{"、".join(names)}），作者自己的句子无争论定位词',
                      fix_hint='综述的合格单位是"可争论的判断"，不是文献数量。改法：先把这几篇按立场分组（谁支持A、谁支持B、分歧在哪一维），再用"然而/相比之下/问题在于"接住自己的位置——周飞舟批三类文献每批完必留门；"分成三个方面最后汇集到一起"是最需要避免的假综合。')]
    return []


# F3: 夹注与参考文献交叉核对（张冠李戴检测）
def check_f3_citation_crosscheck(text, para_idx, para, all_paras):
    """全文级：正文夹注的（作者, 年份）组合须能在参考文献表中找到同名同年条目。"""
    m = re.search(r'^#{0,6}\s*(?:参考文献|引用文献|References)\s*$', text,
                  re.IGNORECASE | re.MULTILINE)
    if not m:
        return []
    refs_text = text[m.end():]
    body = text[:m.start()]

    ref_pairs = set()
    for line in refs_text.splitlines():
        line = line.strip().lstrip('-*•·0123456789. ').strip()
        if len(line) < 6:
            continue
        ym = re.search(r'(\d{4})', line)
        if not ym:
            continue
        year = ym.group(1)
        mc = re.match(r'^([一-鿿·]{2,4}(?:[、，,][一-鿿·]{2,4}){0,6})', line)
        if mc:
            ref_pairs.add((mc.group(1), year))
            continue
        me = re.match(r'^([A-Z][A-Za-zÀ-ÿ\-]+)', line)
        if me:
            ref_pairs.add((me.group(1), year))

    if not ref_pairs:
        return []

    intext = re.findall(
        r'([一-鿿·]{2,4}|[A-Z][A-Za-zÀ-ÿ\-]+)'
        r'(?:\s+et\s+al\.?|\s+and\s+[A-Z][A-Za-zÀ-ÿ\-]+)?[（(](\d{4})[）)]',
        body)

    issues = []
    for name, year in sorted(set(intext)):
        ok = False
        for rn, ry in ref_pairs:
            if ry != year:
                continue
            if rn and rn[0].isascii():
                if rn.split()[0].lower() == name.lower():
                    ok = True
                    break
            else:
                if name in rn or rn in name:
                    ok = True
                    break
        if not ok:
            pos = -1
            for pat in (f'{name}（{year}）', f'{name}({year})', f'{name}，{year}'):
                pos = body.find(pat)
                if pos >= 0:
                    break
            snippet = body[max(0, pos - 40):pos + 60].replace('\n', ' ') if pos >= 0 else f'{name}（{year}）'
            issues.append(Issue('F3', 'high', 'citation', -1,
                          context=snippet,
                          detail=f'作者-年份组合"{name}（{year}）"未能在参考文献表中找到同名同年条目——疑似张冠李戴、年份错记或文献表缺条',
                          fix_hint='逐条核对：打开原文核对作者、年份、结论是否真的属于这篇文献（张冠李戴是审稿一票否决项）；若为转引，改成"转引自"并核对二手来源。'))
    return issues


# ═════════════════════════════════════════════════════
# ── 全篇预算（超出即全部升级 high；预算 0 的规则直接以 high 检出）──
# 校准依据：十篇顶刊语料（不是而是×3、首次×2、显而易见×1、正如前文所述×1）
# ═════════════════════════════════════════════════════

DOC_BUDGETS = {
    'A1': 2,   # 不是……而是……及变体（含与其……不如……）
    'A7': 1,   # 之所以……是因为……
    'E3': 1,   # 值得注意的是类强调元话语
    'E5': 2,   # 综上所述/正如前文所述类复述元话语
    'E7': 1,   # 八股四字格
    'E9': 2,   # 首次（须限定范围）
}

def apply_budgets(issues: list[Issue]) -> list[Issue]:
    """超出全篇预算的规则，其全部检出升级为 high（含原本 medium/low 的）。"""
    counts = Counter(i.rule_id for i in issues if i.severity != 'high')
    for iss in issues:
        budget = DOC_BUDGETS.get(iss.rule_id)
        if budget is not None and iss.severity != 'high' and counts[iss.rule_id] > budget:
            iss.severity = 'high'
            iss.detail += f' ‼︎ 全篇出现 {counts[iss.rule_id]} 次，超出预算 {budget} 次，全部升级为 high'
    return issues


# 规则注册表（38 条）
# ═══════════════════════════════════════════════════════

ALL_RULES = [
    # A. 句式反模式（7 条，全部段落级）
    Rule('A1', '不是……而是……句式（含9种变体）', 'medium', 'syntax', check_a1_bushi),
    Rule('A2', '"对……进行……"冗长句式', 'low', 'syntax', check_a2_dui_jinxing),
    Rule('A3', '"通过……来……"冗长句式', 'low', 'syntax', check_a3_tongguo_lai),
    Rule('A4', '"在……中/上/下"冗余前置', 'low', 'syntax', check_a4_zai_locative),
    Rule('A5', '"一方面……另一方面……"框套', 'low', 'syntax', check_a5_yifangmian),
    Rule('A6', '"正是……才……"强调框套', 'low', 'syntax', check_a6_zhengshi_cai),
    Rule('A7', '"之所以……是因为……"句式（AI口癖）', 'medium', 'syntax', check_a7_zhi_suoyi),

    # B. 标点与节奏（8 条，全部段落级）
    Rule('B1', '破折号密度与双插入语检测', 'medium', 'rhythm', check_b1_dash),
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
    Rule('D5', '量化论文参数p值行内密度 [E-new]', 'medium', 'compliance', check_d5_param_pvalue_density, scope='full'),
    Rule('D6', '行内编码说明括号 [M0b]', 'medium', 'compliance', check_d6_coding_parens, scope='full'),
    Rule('D7', '正文嵌入期刊名/书名（在《XX》上发表/在其《XX》中/发表于《XX》）', 'medium', 'compliance', check_d7_journal_book_in_text),
    Rule('D8', '中英对照括号过度使用（English（中文）/ 中文（English）泛滥）', 'high', 'compliance', check_d8_bilingual_paren_gloss),
    Rule('D9', '英文缩写过度使用 / 跨节未重新展开', 'high', 'compliance', check_d9_abbreviation_overuse),
    Rule('D10', '括号内箭头速记符号（↑↓→）', 'high', 'compliance', check_d10_arrow_shorthand),
    Rule('D11', '括号插入语密度过高 / 可融入括号', 'low', 'compliance', check_d11_excessive_parens),

    # E. 防御性写法与八股元话语（9 条，预算制见 DOC_BUDGETS）
    Rule('E1', '前向结构预告（下文将/下一节将，语料零出现）', 'high', 'defense', check_e1_preview),
    Rule('E2', '防御性否定与自问自答（这并不意味着/或许有人会，语料零出现）', 'high', 'defense', check_e2_defense),
    Rule('E3', '强调性元话语（值得注意的是/需要指出的是，预算1）', 'medium', 'defense', check_e3_emphasis),
    Rule('E4', '缺陷总结散布于非尾部章节（"本文的不足"出现在正文）', 'high', 'defense', check_e4_flaw_scatter, scope='full'),
    Rule('E5', '复述型元话语（综上所述/正如前文所述，预算2）', 'medium', 'defense', check_e5_restate),
    Rule('E6', '自夸硬宣称（填补空白/开创性/里程碑，预算0）', 'high', 'defense', check_e6_boast),
    Rule('E7', '八股四字格（方兴未艾/由此可见，预算1）', 'medium', 'defense', check_e7_cliche),
    Rule('E8', '管理学黑话（赋能/抓手/底层逻辑，预算0）', 'high', 'defense', check_e8_buzz),
    Rule('E9', '"首次"宣称（须限定范围，预算2）', 'medium', 'defense', check_e9_first),

    # F. 引文一致性（2 条）
    Rule('F1', '罗列式综述（只综不述：≥3句作者（年份）开头且无争论定位）', 'high', 'citation', check_f1_listing_review),
    Rule('F3', '夹注与参考文献表交叉核对（作者-年份对不上→疑似张冠李戴）', 'high', 'citation', check_f3_citation_crosscheck, scope='full'),
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
    """执行全部规则，应用全篇预算，返回问题列表"""
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

    all_issues = apply_budgets(all_issues)

    sev_order = {'high': 0, 'medium': 1, 'low': 2}
    all_issues.sort(key=lambda x: (sev_order.get(x.severity, 3), x.para_idx))
    return all_issues


# ═══════════════════════════════════════════════════════
# 输出：改写指令 Markdown
# ═══════════════════════════════════════════════════════

# 全局 IRON RULES（生成改写指令时置顶）
IRON_RULES = [
    '改写后不得引入新的"不是……而是……"句式（全篇含变体预算 2 次）。',
    '不得用标点符号机械替换破折号（如 ——→：、——→，、——→（））。必须 AI 自然重写整个句子。若原句依赖破折号才能表达语义关系（解释、转折、递进、插入），则句子结构本身需要重构。',
    '改写后正文中不得出现任何破折号（——）。',
    '改写后不得引入新的"之所以……是因为……"句式（AI 口癖）。',
    '不得用脚本或正则机械替换标点符号。所有标点修改必须由 AI 理解句意后自然重写句子。',
    '不得引入前向结构预告（下文将/下一节将/第三节将介绍）——真实顶刊零出现，删掉预告直接写内容。',
    '不得引入防御性写法（这并不意味着/或许有人会质疑/不难发现/笔者无意）——删掉辩护直接陈述。',
    '系统性局限只在结论章按"承认→削弱→指向未来"三拍写一次；正文各处不得散布"本文的不足"。',
    '不得引入八股四字格与空泛形容（方兴未艾/日新月异/深刻影响）——换成具体规则、数字或机制。',
    '改写不得虚构或变换引文信息：作者、年份、结论归属必须与原文献一致（张冠李戴是审稿一票否决项）。',
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
    for cat in ['syntax', 'rhythm', 'redundancy', 'compliance', 'defense', 'citation']:
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
    print(f'  类别: 句式{cat_counts.get("syntax",0)} 标点节奏{cat_counts.get("rhythm",0)} 冗余{cat_counts.get("redundancy",0)} 合规{cat_counts.get("compliance",0)} 防御性写法{cat_counts.get("defense",0)} 引文一致性{cat_counts.get("citation",0)}')

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


def cmd_check(args):
    """JSON 机读结果，供 draft_gate.py 等闸门消费。high>0 时退出码 1。"""
    text = Path(args.file).read_text(encoding='utf-8')
    issues = scan_all(text)
    sev_counts = Counter(i.severity for i in issues)
    rule = {r.id: r.name for r in ALL_RULES}
    data = {
        'file': str(args.file),
        'status': 'fail' if sev_counts['high'] else 'pass',
        'counts': {
            'high': sev_counts['high'],
            'medium': sev_counts['medium'],
            'low': sev_counts['low'],
            'total': len(issues),
        },
        'budgets': dict(DOC_BUDGETS),
        'issues': [
            {
                'rule': i.rule_id,
                'rule_name': rule.get(i.rule_id, i.rule_id),
                'severity': i.severity,
                'category': i.category,
                'para': i.para_idx,
                'detail': i.detail,
                'context': i.context[:300],
            }
            for i in issues
        ],
    }
    out = json.dumps(data, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(out, encoding='utf-8')
        print(f'检查结果已保存 → {args.out}')
    else:
        print(out)
    return 1 if sev_counts['high'] else 0


def cmd_budgets(args):
    print('全篇预算表（超出即全部升级 high；校准依据：十篇顶刊语料）')
    print()
    print('| 规则 | 预算 | 语义 |')
    print('|---|---|---|')
    semantics = {
        'A1': '不是而是及变体：真实论文使用极少（十篇共 3 次）',
        'A7': '之所以是因为：AI 口癖',
        'E3': '值得注意的是类强调元话语：语料仅 1 次',
        'E5': '综上所述/正如前文所述类复述：语料仅 2 次',
        'E7': '八股四字格：语料仅 1 次',
        'E9': '首次（须限定范围）：语料 2 次均为"首次尝试/首次评估"',
    }
    for rid, b in DOC_BUDGETS.items():
        r = next((x for x in ALL_RULES if x.id == rid), None)
        print(f"| {rid} {r.name if r else ''} | {b} | {semantics.get(rid, '')} |")
    zero_budget = [r for r in ALL_RULES if r.id.startswith(('E1', 'E2', 'E6', 'E8', 'F1', 'F3'))]
    print()
    print('预算 0（任何一次即 high）：' + '、'.join(f'{r.id} {r.name}' for r in zero_budget))
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
  %(prog)s --check paper.md             # JSON 机读结果（闸门用，high>0 退出码 1）
  %(prog)s --budgets                    # 打印全篇预算表
        """,
    )
    parser.add_argument('file', nargs='?', help='目标 Markdown 文件')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--scan', action='store_true', help='快速扫描统计')
    group.add_argument('--report', action='store_true', help='完整 Markdown 报告')
    group.add_argument('--instructions', action='store_true', help='生成结构化改写指令 MD')
    group.add_argument('--check', action='store_true', help='JSON 机读结果（high>0 退出码 1，闸门用）')
    group.add_argument('--budgets', action='store_true', help='打印全篇预算表')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('--out', help='输出文件路径')

    args = parser.parse_args()

    if args.budgets:
        return cmd_budgets(args)

    if not args.file:
        parser.error('需要提供目标文件（--budgets 除外）')
    if not os.path.exists(args.file):
        print(f'❌ 文件不存在：{args.file}')
        return 1

    if args.scan:
        return cmd_scan(args)
    elif args.report:
        return cmd_report(args)
    elif args.instructions:
        return cmd_instructions(args)
    elif args.check:
        return cmd_check(args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
