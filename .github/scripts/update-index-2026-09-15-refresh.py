from pathlib import Path

p = Path('robotics-brief-covered-items.md')
s = p.read_text(encoding='utf-8')

old = '> 2026-09-15 新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 627 条。'
new = '> 2026-09-15 早间首版新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 627 条；随后因 arXiv 9 月 15 日最新公开批次刷新，更新同日文章并追加 8 条主动态与 1 条经典论文回顾，累计共 636 条。早间首版条目保留为历史覆盖记录。'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise RuntimeError('2026-09-15 header line not found')

sentinel = '| 2026-09-15 | P-POSEMEM: Projective Semantic Memory for Consistent Language Grounding under Pose-Graph Rewrites |'
rows = '''
| 2026-09-15 | P-POSEMEM: Projective Semantic Memory for Consistent Language Grounding under Pose-Graph Rewrites | [论文](https://arxiv.org/abs/2609.15475) | 9 月 15 日最新公开批次；v1 2026-09-14；pose-graph rewrite / marginalization 下保持语言目标语义一致性。 |
| 2026-09-15 | JEPLO: Joint-Embedding Predictive Learning for LiDAR-Based Legged Locomotion | [论文](https://arxiv.org/abs/2609.15770) · [代码](https://github.com/ASIG-X/JEPLO) | 9 月 15 日最新公开批次；v1 2026-09-14；MID360 + proprioception、mapping-free JEPA 感知运动、Go2 sim-to-real。 |
| 2026-09-15 | ResSafe: Learning Safety Filtering with Residual Reinforcement Learning for Humanoids | [论文](https://arxiv.org/abs/2609.15988) | 9 月 15 日最新公开批次；v1 2026-09-14；nominal performance policy + residual safety policy。 |
| 2026-09-15 | Volumetric Harmonic Field Navigation for Quadrotors | [论文](https://arxiv.org/abs/2609.15680) | 9 月 15 日最新公开批次；v1 2026-09-14；3D harmonic global field + constrained predictive planner；Crazyflie 真机。 |
| 2026-09-15 | Belief-Adaptive Online Autonomy for Quadrotor UAV Navigation under GNSS Degradation in Urban Environments | [论文](https://arxiv.org/abs/2609.14806) | 9 月 15 日最新公开批次；v1 2026-09-13；EKF + explicit GNSS trust latent + latency-aware OOSM；当前为仿真验证。 |
| 2026-09-15 | Real-World Reinforcement Learning with MPC Scaffolding for Dexterous Manipulation | [论文](https://arxiv.org/abs/2609.14878) | 9 月 15 日最新公开批次；v1 2026-09-14；sampling MPC 作为 SAC 真机学习脚手架；Allegro 16-DoF。 |
| 2026-09-15 | Fabrication After Tool Failure: Tool-Augmented Agents Assert Values Their Tools Did Not Return | [论文](https://arxiv.org/abs/2609.14758) | 9 月 15 日最新 Software Engineering 批次；tool semantic failure、显式 retrieval_status 与运行时诚实性。 |
| 2026-09-15 | Gemini 3.8 Audio (Live, Live Extended Thinking) | [官方模型卡](https://deepmind.google/models/model-cards/gemini-3-8-audio/) | Google DeepMind 2026-09-15 发布；native multimodal realtime audio；128K context、audio/text output。 |
| 2026-09-15 | g²o: A General Framework for Graph Optimization | [DOI](https://doi.org/10.1109/ICRA.2011.5979949) · [官方代码](https://github.com/RainerKuemmerle/g2o) | 经典论文回顾；ICRA 2011；通用 graph nonlinear least-squares、SLAM / BA 稀疏图优化。 |
'''

if sentinel not in s:
    marker = '\n## 维护检查表'
    if marker not in s:
        raise RuntimeError('maintenance checklist marker not found')
    s = s.replace(marker, '\n' + rows + marker, 1)

p.write_text(s, encoding='utf-8')
