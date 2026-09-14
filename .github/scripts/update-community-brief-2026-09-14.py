from pathlib import Path

heading = '## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选'

spec_section = '''## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

主动态之后、经典论文回顾之前固定增加该章节，不计入 5–8 条主动态。每期精选 **2–3 条**最新且高信号的 Vibe Coding / AI 编程实战技巧、工作流经验或工具实践。

来源**不限于 X 和 Reddit**，也包括 Hacker News、Lobsters、GitHub Discussions / Issues、开发者博客、技术论坛、Newsletter，以及工具 / 框架作者和一线工程师公开分享。

- 优先最近 24 小时；不足 2 条时扩展到最近 7 天，再不足可扩展到最近 30 天；不得为了凑数收录低价值内容。
- 优先具体工作流、命令、配置、上下文管理、Agent 协作、代码审查、验证、测试、成本控制、长期任务管理与权限治理。
- 不收录纯情绪、泛泛观点或营销软文；社区个人经验必须明确标注为经验，不得包装成 benchmark 结论。
- 每条至少说明：技巧是什么、为什么值得学、适用场景、今天如何使用、风险 / 边界、原始链接。
- 按 URL、标题和核心技巧主题联合去重；当天入选条目追加到 `robotics-brief-covered-items.md`，备注为“社区精选”。

'''

community = '''## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### 1. 双 Agent 不要“同题双跑”：Maker / Reviewer 分工，Reviewer 必须看原始需求

**来源：2026-09-11 开发者实战文章。**

一篇近期 Claude Code + Codex 联合工作流文章给出的高价值经验是：不要让两个 Agent 都完整做一遍同一任务，而是让一方执行、一方用 fresh context 独立审查。Reviewer 不应只读执行 Agent 的总结，而要同时读取**原始需求、实际改动和检查结果**，否则很容易继承执行者自己的 framing。

并行时按真实文件路径划分 ownership；不同 worktree 只能隔离工作区，不能自动避免两个 Agent 同时改同一文件后的覆盖或冲突。共享文件应采用“先写、后审”的串行流程。

**今天可以直接用：** handoff 固定为 `Goal / Decisions / Do not change / Files changed / Checks run / Still open`，并把原始 brief 一起交给 Reviewer。

**边界：** 这是个人开发者工作流经验，不是严格 benchmark；第二个 Agent 会增加 token / 额度消耗，只有真正承担独立验证职责时才值得。

[原文：Claude Code and Codex Together: How to Split the Work](https://have-been.com/en/posts/claude-code-codex-together)

### 2. Front-load：Research → Plan → Task → Implementation，聊天可丢，Artifact 不能丢

**来源：2026-09-06，2026-09-10 更新的 Codex 工作流文章。**

这篇文章最值得借鉴的原则是：上游研究和架构假设一旦错了，Agent 会在后续实现中把错误不断放大，因此人工注意力应前置，而不是等几小时代码生成后再靠 patch 补救。

推荐把流程固定成 `Research（只读探索）→ Plan（持久架构文档）→ Task（Goal / Dependencies / Paths / Acceptance / Validation）→ Implementation（Fresh Session）`。真正持久的状态是 **Task Registry + Append-only Activity Log + Git State**，不是聊天历史；`AGENTS.md / CLAUDE.md` 也更适合只保留经过真实失败证明必要的短规则。

**今天可以直接用：** 建 `research.md`、`plan.md`、`tasks/TASK-xxx.md` 和 `activity.log`；每个 Task 必须带验收命令，新任务尽量从 fresh session 开始。

**边界：** 具体 CLI 命令会随版本变化；应复用的是“前置验证 + Artifact 化 + Fresh Session”的结构。

[原文：Front-Load or Fail — The Four-Phase Coding Agent Workflow](https://codex.danielvaughan.com/2026/09/06/front-load-human-review-phased-coding-agent-workflow-codex-cli/)

### 3. 社区高赞经验：架构、边界和 Edge Cases 先由人想清楚，再把 Implementation 交给 Agent

**来源：2026-09-07 Reddit 高热度讨论；属于社区经验。**

讨论中最值得保留的一条实践是 **Human-owned Design Checkpoint**：在 Agent 获得写权限前，先由人把 architecture、关键接口、edge cases、trade-offs 和 definition of done 想清楚。之后可以高强度让 Agent 写代码，但 review 要回到原始需求和设计 artifact，而不是只问“测试是不是绿了”。

**今天可以直接用：** 在写权限前确认一份很短的 `DESIGN.md`，至少包含 `Goal / Non-goals / Architecture / Key interfaces / Edge cases / Trade-offs / Definition of done`。

**边界：** 这是社区个人经验，不是控制变量实验；更适合作为保持系统理解和审查能力的工作习惯。

[Reddit 讨论：I am done with the everyday’s work using just claude/codex](https://www.reddit.com/r/developersIndia/comments/1w9w2jh/i_am_done_with_the_everydays_work_using_just/)

'''

# Spec
p = Path('robotics-brief-task-spec.md')
s = p.read_text(encoding='utf-8')
if heading not in s:
    s = s.replace('## 经典论文回顾\n', spec_section + '## 经典论文回顾\n', 1)
    s = s.replace('主动态之后固定增加独立章节：', '主动态与社区精选之后固定增加独立章节：', 1)
    s = s.replace('- `## 经典论文回顾`\n', '- `## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选`\n- `## 经典论文回顾`\n', 1)
    s = s.replace('确认：日期正确、正文未截断、包含 `## 经典论文回顾` 和 `## 参考资料`、无聊天内部引用标记。', '确认：日期正确、正文未截断、包含 `## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选`、`## 经典论文回顾` 和 `## 参考资料`、无聊天内部引用标记。')
    s = s.replace('- 追加当天首次覆盖的论文/项目；\n', '- 追加当天首次覆盖的论文/项目；\n- 追加当天社区精选条目，并在备注中标记“社区精选”；\n', 1)
    p.write_text(s, encoding='utf-8')

# Article
p = Path('_posts/2026-09-14-robotics-brief.md')
a = p.read_text(encoding='utf-8')
if heading not in a:
    a = a.replace('\n## 经典论文回顾\n', '\n' + community + '## 经典论文回顾\n', 1)
    a = a.replace('description: "本期关注恶劣视觉条件下雷达稠密深度、实时雅可比灵巧手控制、安全技能适配、端到端控制形式验证、VLA 记忆与世界模型、企业代码检索可信度和 Agent 生产变更沙箱。"', 'description: "本期关注恶劣视觉条件下雷达稠密深度、实时雅可比灵巧手控制、安全技能适配、VLA 记忆与世界模型、AI Coding 社区实战技巧和 Agent 生产变更沙箱。"')
    p.write_text(a, encoding='utf-8')

# Coverage index
p = Path('robotics-brief-covered-items.md')
idx = p.read_text(encoding='utf-8')
if '社区精选：双 Agent Maker/Reviewer' not in idx:
    idx = idx.replace('> 2026-09-14 新增 8 条主动态与 1 条经典论文回顾，共 603 条。', '> 2026-09-14 新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 606 条。')
    rows = '''| 2026-09-14 | 社区精选：双 Agent Maker/Reviewer + 原始需求独立审查 | [文章](https://have-been.com/en/posts/claude-code-codex-together) | 社区精选；开发者实战文章；2026-09-11 |
| 2026-09-14 | 社区精选：Front-Load 四阶段 AI Coding Workflow | [文章](https://codex.danielvaughan.com/2026/09/06/front-load-human-review-phased-coding-agent-workflow-codex-cli/) | 社区精选；2026-09-06，2026-09-10 更新 |
| 2026-09-14 | 社区精选：Human-owned Design Checkpoint 后再交给 Agent 实现 | [Reddit](https://www.reddit.com/r/developersIndia/comments/1w9w2jh/i_am_done_with_the_everydays_work_using_just/) | 社区精选；社区经验；2026-09-07 |
'''
    marker = '\n## 维护检查表'
    if marker not in idx:
        raise RuntimeError('maintenance checklist marker not found')
    idx = idx.replace(marker, '\n' + rows + marker, 1)
    p.write_text(idx, encoding='utf-8')
