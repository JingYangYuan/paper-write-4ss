# paper-write-4ss Skill Specification

## Skill Overview

**Name:** paper-write-4ss (中文学术写作系统)

**Purpose:** A comprehensive Chinese academic writing system designed to assist social science researchers in writing high-quality papers for peer-reviewed journals. The system is grounded in empirical analysis of published papers from authoritative journals like 《社会学研究》(Sociological Research), 《管理世界》(Management World), and 《中国社会科学》(Chinese Social Sciences Quarterly).

**Target Audience:** Chinese social science researchers, particularly those publishing in sociology, management, public administration, and related fields.

---

## Core Capabilities

### 1. **Paradigm Selection & Routing**
The skill begins by diagnosing the user's research type through three diagnostic questions:
- **Target journal style** (sociology vs. management journals)
- **Research methodology** (quantitative, qualitative, case study, theoretical)
- **Expected word count** (< 1.5K, 1.5-2.5K, > 2.5K)

Based on responses, the skill routes users to one of two established paradigms:
- **Sociology Research Paradigm** (定量/理论/质性路径)
- **Management World Case Study Paradigm** (案例研究范式)

### 2. **Seven-Element Paper Structure**
Guides users through 7 mandatory components:
1. **Title + Abstract + Keywords** (G1-G4, A1-A5): Distill paper essence for indexing
2. **Introduction** (I1-I7): Establish research legitimacy
3. **Literature Review** (L1-L6): Position within knowledge context
4. **Methods & Materials** (M1-M5): Narrate research process
5. **Empirical Analysis** (E1-E5): Present findings through logical organization
6. **Theoretical Dialogue** (T1-T5): Contribute to knowledge base
7. **Conclusion & Discussion** (C1-C6): Synthesize and extend

### 3. **Writing Standards & Hard Constraints**
- **Hard Constraints** (write_constraints):
  - Prohibit embedding complete paper titles in body text (use author-year citations)
  - Prohibit non-academic colloquialisms ("一文中", "该文")
  - Prohibit "negation + assertion" sentence structure ("不是...而是...")
  - Prohibit em-dashes (——) in body text
  - Prohibit mechanical punctuation replacement scripts
  - Require justified quotation marks
  - Mandate Chinese quotation marks ("") throughout

- **Structural Standards**:
  - Ideal proportions: Empirical analysis 30-40%; other elements balanced
  - Introduction: 10-15% of total
  - Literature review: 15-20%
  - Methods: 8-12%
  - Theory dialogue: 10-15%
  - Conclusion: 10-15%

### 4. **Four-Stage Quality Control Checklist**
Users follow a structured validation workflow:
1. **Structural Completeness** - 7 elements present, proportion audits
2. **Argumentation Rigor** - Logical progression, transitions, evidence density
3. **Materials & Citations** - Citation diversity (≥3 forms), analytical depth per citation
4. **Language Normalization** - Academic register, terminology consistency, formatting

### 5. **Writing Scanner Tool**
Automated Python script (`writing_scanner.py`) detects and flags:
- Prohibited patterns (19 rules across 4 categories)
- Provides actionable rewriting instructions
- Supports iterative refinement cycle: scan → instruct → rewrite → re-scan

---

## Knowledge Structure

### Chapter-Based Standards (`/chapters`)
- **ch01-form-logic.md** - Logical form selection for papers
- **ch02-topic-material.md** - Topic design, title generation, abstract/keywords
- **ch03-genesis-question.md** - Problem formulation and introduction structure
- **ch04-lit-review.md** - Literature review framework and architecture
- **ch05-lit-technique.md** - Citation techniques and integration strategies
- **ch06-material-method.md** - Methods section writing standards
- **ch07-organizing-materials.md** - Empirical material organization principles
- **ch08-theory-dialogue.md** - Theoretical contribution and positioning
- **ch09-conclusion.md** - Conclusion and discussion conventions
- **ch10-submission-ethics.md** - Reference formatting and submission ethics

### Exemplars & Prompt Templates (`/examples`)
- **intro_example.md** - 3 introduction models (sociology quantitative/qualitative + management case study)
- **lit_review_example.md** - Framework-based and hypothesis-driven literature review models
- **framework_example.md** - 4 analytical framework types (dimensional, dialogical, mechanistic, matrix)
- **findings_example.md** - 3 findings presentation models with annotation
- **conclusion_example.md** - 2 conclusion models per paradigm with anti-patterns

### Resource Materials (`/resources`)
- **paradigm_selector.md** - Detailed paradigm comparison, decision trees, conversion guides
- **cheatsheet.md** - Quick reference tables (paper elements, decision matrices, checklists)
- **glossary.md** - Key terminology with definitions
- **patterns.md** - Writing techniques, trigger conditions, anti-patterns (15.2 KB of applied craft knowledge)

---

## Interaction Protocol

### Usage Flow

1. **Initial Orientation**
   - User provides writing task
   - Skill uses `AskUserQuestion` to diagnose paradigm (3 questions)
   - Skill confirms selected paradigm and explains section-specific requirements

2. **Section-Specific Writing**
   - User requests work on specific section
   - Skill reads applicable `chapter/ch_X.md` file
   - Skill reads corresponding `examples/X_example.md` file
   - Skill applies standards from chapters + templates from examples
   - Outputs writing guidance or revised text

3. **Revision Workflow**
   - User submits draft text
   - Skill invokes `writing_scanner.py --instructions` to generate repair instructions
   - AI reads instructions and performs natural sentence rewriting
   - Skill runs `writing_scanner.py --scan` to verify
   - Cycle repeats until critical issues (`🔴高危`) = 0

4. **Quality Assurance**
   - Before submission, user runs full 4-stage checklist
   - Skill cross-references each item against hardcoded standards
   - Provides itemized remediation plan

### Tools & Methods
- **Read:** Access chapter standards, exemplars, resources
- **Write:** Generate outlines, revise sections, produce full drafts
- **Edit:** Iterative refinement using structured feedback
- **Bash:** Execute `writing_scanner.py` for automated analysis
- **Grep:** Search across chapters and examples for pattern references

### Argument Hint
```
[文本路径] 后加 [润色/扫描/检查/改写]
[Text path] followed by [polish/scan/check/rewrite]
```

Accepted commands:
- `润色` (Polish) - Copy-edit for language normalization
- `扫描` (Scan) - Run automated writing scanner
- `检查` (Check) - Run 4-stage quality checklist
- `改写` (Rewrite) - Structural or content regeneration

---

## Key Features & Differentiators

### 1. Evidence-Based Standards
All 19 hard standards are derived from published papers in tier-1 Chinese journals, not prescriptive theory. This ensures advice is publication-tested.

### 2. Paradigm Flexibility
Recognizes that sociology and management publishing have distinct conventions (structure, evidence presentation, theory dialogue style). System auto-routes without requiring user expertise in field-specific norms.

### 3. Granular Citation Guidance
Beyond "use citations," the system specifies:
- Citation density per section (引文前后密度均衡)
- Analytical depth requirements (引文后有思考痕迹)
- Form diversity (引文呈现形式多样化 ≥ 3 种)

### 4. Mechanical Pattern Detection
The `writing_scanner.py` tool flags prohibited patterns algorithmically, reducing manual review burden and enabling iterative refinement loops.

### 5. Annotation-Based Learning
All exemplars are annotated with bracketed standard codes (e.g., [I1], [E3]), enabling cross-referencing between example text, standard documentation, and user outputs.

---

## Forbidden Patterns & Constraints

### Prohibited Constructions
| Pattern | Reason | Example |
|---------|--------|---------|
| "不是...而是..." | Negation-assertion structure; use direct statement | ❌ 并非能力不足，而是基础设施缺失 → ✅ 根源在于基础设施缺失 |
| Em-dashes (——) | Suggests prose narrative, incompatible with formal register | ❌ 劳动可见性——关键因素 → ✅ 劳动可见性的关键决定因素是组织定义 |
| Paper title in body | Standard citation format requires author-year; allows reader lookup in references | ❌ 《劳动市场如何分割》一文说... → ✅ 张三（2020）分析了劳动市场分割... |
| Colloquial meta-language | Signals non-academic register | ❌ 一文中提出... / 该文指出... → ✅ 该研究发现... / 直接陈述内容 |

### Script Replacement Prohibition
The skill explicitly forbids mechanical punctuation replacement. All edits must involve natural sentence rewriting by AI, not regex substitution.

---

## Quality Assurance Workflow

### Writing Cycle: Scan → Instruct → Rewrite → Re-Scan

1. **Scan Phase**
   ```bash
   python writing_scanner.py --instructions < draft.md > repair_instructions.md
   ```
   Generates diagnostic output for human/AI review

2. **Instruct Phase**
   AI reads repair instructions and identifies patterns to rewrite

3. **Rewrite Phase**
   AI performs natural sentence rewriting (not mechanical substitution)

4. **Re-scan Phase**
   ```bash
   python writing_scanner.py --scan < revised.md
   ```
   Verifies compliance; cycles until `🔴高危` count = 0

---

## Integration Points

### With External Tools
- Academic citation managers (Zotero, Mendeley) for reference formatting
- Word/Google Docs for collaborative drafting (exported to .md for scanning)
- ArXiv/journal submission systems for final formatting

### With Other Skills
- **Grammar skill**: Handles syntax issues not covered by pattern detection
- **Citation formatting skill**: Specific journal citation styles (GBK/APA/Chicago)
- **Plagiarism detection skill**: Upstream integrity checks

---

## Limitations & Scope Boundaries

### In Scope
- ✅ Chinese academic paper writing guidance (social sciences primary)
- ✅ Structural and substantive advice (argumentation, framework logic)
- ✅ Language register normalization and pattern correction
- ✅ Cross-paradigm routing and section-specific coaching

### Out of Scope
- ❌ Non-academic writing (journalism, creative writing, technical documentation)
- ❌ Non-Chinese publications (English, European journals have different conventions)
- ❌ Disciplinary fields outside social sciences (STEM, medicine, law)
- ❌ Research ethics review or plagiarism detection (upstream tasks)
- ❌ Statistical analysis or data visualization guidance (downstream task)

---

## Repository Structure Summary

```
paper-write-4ss/
├── README.md                          # User-facing overview
├── SKILL.md                           # Full skill specification (236 lines)
├── SKILL_SPECIFICATION.md             # This document
├── paper-write-4ss/
│   ├── SKILL.md                       # Master reference document
│   ├── chapters/                      # 10 chapter-based standard documents
│   │   ├── ch01-form-logic.md
│   │   ├── ch02-topic-material.md
│   │   ├── ch03-genesis-question.md
│   │   ├── ch04-lit-review.md
│   │   ├── ch05-lit-technique.md
│   │   ├── ch06-material-method.md
│   │   ├── ch07-organizing-materials.md
│   │   ├── ch08-theory-dialogue.md
│   │   ├── ch09-conclusion.md
│   │   └── ch10-submission-ethics.md
│   ├── examples/                      # 5 exemplar documents with templates
│   │   ├── intro_example.md
│   │   ├── lit_review_example.md
│   │   ├── framework_example.md
│   │   ├── findings_example.md
│   │   └── conclusion_example.md
│   ├── resources/                     # Supporting reference materials
│   │   ├── paradigm_selector.md       # Paradigm decision tree
│   │   ├── cheatsheet.md              # Quick reference tables
│   │   ├── glossary.md                # Terminology definitions
│   │   └── patterns.md                # Writing techniques & anti-patterns
│   └── scripts/                       # Automation tools
│       └── writing_scanner.py         # Pattern detection & repair script
```

---

## Version & Maintenance

**Skill Version:** 1.0 (Initial Release)

**Last Updated:** 2026-05-29

**Maintenance Notes:**
- All standards traceable to published papers in tier-1 journals
- Update cycle: Quarterly review of new publications in reference journals
- Anti-pattern library: Living document; new prohibited patterns added as edge cases discovered in user feedback

---

## Getting Started for Users

### For First-Time Users
1. Load the skill and answer 3 diagnostic questions about your research paradigm
2. Navigate to `examples/` → read the exemplar for your paper section
3. Copy the corresponding prompt template and adapt for your paper
4. Generate or revise text using the prompt
5. When draft complete, run: `python scripts/writing_scanner.py --scan <your_file>`

### For Frequent Users
1. Bookmark `resources/cheatsheet.md` for fast lookups
2. Use `chapters/chX-X.md` as reference during writing
3. Integrate `writing_scanner.py` into your editor workflow
4. Follow the scan → instruct → rewrite → re-scan cycle

---

## Support & Contributing

**Documentation Issues:** File issues on the repository if a standard is unclear or an exemplar needs clarification.

**New Paradigms:** If your research domain isn't covered (e.g., law review writing), create a new paradigm document following the structure of `paradigm_selector.md`.

**Pattern Contributions:** Submit edge cases of poor writing patterns for potential addition to `writing_scanner.py` and `patterns.md`.
