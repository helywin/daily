from pathlib import Path

p = Path('robotics-brief-covered-items.md')
s = p.read_text(encoding='utf-8')

summary_19 = '> 2026-09-19 新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 714 条。'
summary_20 = '> 2026-09-20 新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 726 条。'
marker = '\n## 维护检查表'

if '2026-09-20 | PerSeM:' not in s:
    if '> 最后更新：2026-09-19（Asia/Shanghai）' not in s:
        raise RuntimeError('last-updated marker not found')
    if summary_19 not in s:
        raise RuntimeError('2026-09-19 summary marker not found')
    if marker not in s:
        raise RuntimeError('maintenance checklist marker not found')

    s = s.replace('> 最后更新：2026-09-19（Asia/Shanghai）', '> 最后更新：2026-09-20（Asia/Shanghai）', 1)
    s = s.replace(summary_19, summary_19 + '\n>\n' + summary_20, 1)

    rows = '''
| 2026-09-20 | PerSeM: Persistent Semantic Memory for Long-Horizon Open-Vocabulary UAV Mapping | [论文](https://arxiv.org/abs/2609.19542) | 时间回补；v1 2026-09-17；开放词汇 UAV 持久 voxel 语义记忆、多视角稳定与选择性 refinement。 |
| 2026-09-20 | EliGSiR: Continual RGB-D Mapping with Gaussian Splatting under Bounded Compute | [论文](https://arxiv.org/abs/2609.20348) | 时间回补；v1 2026-09-17；view scheduling + adaptive fidelity + targeted geometry growth。 |
| 2026-09-20 | Learning Safe Humanoid Navigation from Reduced Order Models | [论文](https://arxiv.org/abs/2609.19272) · [项目页](https://wdc3iii.github.io/rom-nav/) | 时间回补；v1 2026-09-16；RoM→G1 迁移 + frozen locomotion + Poisson safety filter。 |
| 2026-09-20 | Feasibility and Singularity in High-Order Safety-Critical Control for Quadrotor UAVs | [论文](https://arxiv.org/abs/2609.19362) | 时间回补；v1 2026-09-16；pairwise effectiveness + aggregate feasibility + torque-aware fourth-order HOCBF。 |
| 2026-09-20 | StageGuard: Distilling Agentic Reasoning into Lightweight Stage Transition Monitors for Long-Horizon Robot Tasks | [论文](https://arxiv.org/abs/2609.20791) | 时间回补；v1 2026-09-17；agentic distillation 的阶段完成监控；BEHAVIOR-1K 与 UR5e/Piper 真机。 |
| 2026-09-20 | GeoAAC: Geometry-Aware Adaptive Action Chunking for Flow-Matching Vision-Language-Action Policies | [论文](https://arxiv.org/abs/2609.20776) | 时间回补；v1 2026-09-17；Flow denoising geometry 驱动 training-free adaptive action chunk。 |
| 2026-09-20 | MoWAM: Motion-centric World-Action Models for Efficient Robot Manipulation | [论文](https://arxiv.org/abs/2609.20709) | 时间回补；v1 2026-09-17；部署期 explicit future motion 替代完整 future-video generation，并支持 candidate verification。 |
| 2026-09-20 | DeltaSelect: Cost-Bounded Representative Task Selection for Coding-Agent A/B Evaluation | [论文](https://arxiv.org/abs/2609.19607) | 时间回补；v1 2026-09-17；从历史 benchmark trials 选择低成本、可校准的 Coding Agent regression set。 |
| 2026-09-20 | SemanticFusion: Dense 3D Semantic Mapping with Convolutional Neural Networks | [论文](https://arxiv.org/abs/1609.05130) · [DOI](https://doi.org/10.1109/ICRA.2017.7989538) · [项目页](https://www.imperial.ac.uk/dyson-robotics-lab/downloads/semanticfusion/) | 经典论文回顾；ICRA 2017；ElasticFusion + CNN，多视角概率式 dense semantic mapping。 |
| 2026-09-20 | 社区精选：Claude Code 原生 AGENTS.md 支持与 Canonical Instruction Source | [Claude Code Releases](https://github.com/anthropics/claude-code/releases) | 社区精选；v2.1.277；跨 Claude/Codex 项目减少重复 instruction drift。 |
| 2026-09-20 | 社区精选：AGENTS.md / CLAUDE.md 过期引用的 Pre-commit 机械校验 | [Reddit](https://www.reddit.com/r/ClaudeCode/comments/1wk018t/your_claudemd_can_reference_code_that_no_longer/) | 社区精选；社区经验；2026-09-19；stale instruction reference validation。 |
| 2026-09-20 | 社区精选：Auto Mode Server-Side Classifier 与 Runtime Telemetry | [Claude Code Releases](https://github.com/anthropics/claude-code/releases) | 社区精选；v2.1.278；记录 classifier location、fallback 与 policy revision。 |
'''
    s = s.replace(marker, '\n' + rows + marker, 1)
    p.write_text(s, encoding='utf-8')
else:
    print('index already contains 2026-09-20 rows; no-op')
