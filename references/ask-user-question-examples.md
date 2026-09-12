# ask_user 示例模块规范

本文档定义 `paper-master-4ss` 内所有用户提问、确认和阻断门槛的示例写法。`ask_user` 是各宿主通用能力名；Claude Code 与 ZCode 可映射为 AskUserQuestion，OMP 映射为 `ask` 工具，OpenCode/Codex 映射为各自的提问能力或直接提问。各模块可以保留局部业务选项，但字段结构应统一为 `question`、`header`、`options`。

## 一、标准字段

```text
question: "面向用户的一句话问题。"
header: "12字以内短标题"
options: [
  {label: "推荐选项", description: "说明选择后的执行影响"},
  {label: "备选选项", description: "说明适用条件或代价"}
]
```

- `question` 必须能被用户直接理解，避免内部术语堆叠。
- `header` 应短而稳定，用于界面标题或日志摘要。
- `options` 通常提供 2-4 个互斥选项；每项必须包含 `label` 与 `description`。
- 推荐项放在首位，`description` 说明为什么推荐，而不是只写“推荐”。

## 二、自由输入型

当问题无法预设选项，或需要用户给出路径、主题、期刊名、数据名时，使用空选项并明确允许自由输入。

```text
question: "请提供你的研究主题、数据路径或目标期刊。"
header: "自由补充"
options: []
```

执行规则：自由输入型不应伪造默认答案。用户未回答时，记录为 `未确认` 或转入最小可行路径。

## 三、推荐/不确定型

当用户可能无法判断，应保留“不确定，请推荐”或“按推荐执行”。

```text
question: "下一步按哪个方向推进？"
header: "方向确认"
options: [
  {label: "按推荐执行", description: "采用当前证据最充分、风险最低的路径"},
  {label: "收窄范围", description: "用户指定理论、机制、人群、时期或材料边界"},
  {label: "不确定，请推荐", description: "由 Skill 根据已读材料给出主方案和备选方案"}
]
```

执行规则：选择“不确定，请推荐”时，必须说明推荐依据，并在过程日志中记录这是推断推荐而非用户主动指定。

## 四、阻断确认型

涉及 Team 创建、CNKI 验证码、写文件权限、外部工具不可用、关键输入缺失等情况时，使用阻断确认型。

```text
question: "当前步骤被阻断。请选择如何处理。"
header: "阻断确认"
options: [
  {label: "已处理，继续", description: "用户已完成验证码、登录、授权或补充必要材料"},
  {label: "稍后再试", description: "暂停当前步骤，等待用户处理后再继续"},
  {label: "放弃本步骤", description: "记录为用户明确放弃或网络不可达，转入允许的回退路径"}
]
```

执行规则：未确认前不得继续执行被阻断步骤；不得用猜测替代用户选择。

## 五、选择固化规则

以下选择一旦稳定，应按 `project_memory` 写入当前宿主项目规则；Claude Code 可写入项目级 `CLAUDE.md` 的 paper-master 标记块，ZCode 写入工作区 `AGENTS.md` 的 paper-master 标记块，OpenCode/Codex 缺少宿主规则文件时写入 `paper-workspace/_index/project-rules.md`：

- 模块模式、研究范式、学理化风格、输出路径等长期偏好。
- Team 五项选择。
- 文献检索来源启用/暂缓策略。
- 用户明确指定的目标期刊、论文类型、学历层次和字数范围。

临时任务说明、隐私材料细节、一次性验证码状态不得固化。
