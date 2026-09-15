from pathlib import Path

p = Path('robotics-brief-covered-items.md')
s = p.read_text(encoding='utf-8')
old = '> 2026-09-14 新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 606 条。'
new = '> 2026-09-14 早间首版新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 606 条；随后因 arXiv 9 月 14 日最新公开批次刷新，更新同日文章并追加 8 条主动态与 1 条经典论文回顾，累计共 615 条。早间首版条目保留为历史覆盖记录。'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise RuntimeError('2026-09-14 summary line not found')

rows = '''| 2026-09-14 | Chain-SLAM: An Online Multi-Session LiDAR SLAM System with Chained Loop Closure | [论文](https://arxiv.org/abs/2609.12221) · [项目页](https://ai4ce.github.io/Chain-SLAM/) · [代码](https://github.com/ai4ce/Chain-SLAM) | 最新公开批次；v1 2026-09-10；IROS 2026；跨会话 chained loop、ICP 验证与统一 factor graph。 |
| 2026-09-14 | Parameter Sensitivity Analysis for Aerial LiDAR-Inertial Odometries in Low-Altitude Flights | [论文](https://arxiv.org/abs/2609.12837) | 最新公开批次；v1 2026-09-11；FAST-LIO2 / Cartographer 参数敏感性与简化调参建议。 |
| 2026-09-14 | VertexCBF: Improving Neural Control Barrier Functions via Vertex-Restricted Control Search | [论文](https://arxiv.org/abs/2609.12831) | 最新公开批次；v1 2026-09-11；convex-polytope 顶点搜索、neural CBF 与真实移动机器人避障。 |
| 2026-09-14 | ASTRIL-MPC: Autonomous Traversal Framework of Articulated Tracked Robots with Language-Guided Neural-Kinematic MPC | [论文](https://arxiv.org/abs/2609.13083) | 最新公开批次；v1 2026-09-11；learned kinematics + NMPC + 安全受限 LLM 参数适配；周期 <100 ms。 |
| 2026-09-14 | Breaking the Vision-Action Shortcut: Latent Interface Training for Generalizable Vision-Language-Action Models / LIT | [论文](https://arxiv.org/abs/2609.12641) · [项目页](https://magiclab-nus.github.io/LIT/) · [代码](https://github.com/MAGICLAB-NUS/LIT) | 最新公开批次；v1 2026-09-11；pose-supervised latent interface 切断视觉动作捷径。 |
| 2026-09-14 | DWMP: Leveraging Dual World Models for Humanoid Obstacle Traversal | [论文](https://arxiv.org/abs/2609.12347) | 最新公开批次；v1 2026-09-11；Koopman proprioceptive world model + RSSM depth world model；Unitree G1。 |
| 2026-09-14 | GraphAHA: Graph-Based Adaptive Search with Heterogeneous Actions for Test-Time Code Generation | [论文](https://arxiv.org/abs/2609.12757) | 最新公开批次；v1 2026-09-11；typed DAG 复用候选代码与层级 Thompson sampling。 |
| 2026-09-14 | Reality Is the Final Verifier: On Two Key Gaps in Agentic Software Engineering | [论文](https://arxiv.org/abs/2609.12039) | 最新公开批次；v1 2026-09-10；Requirement Gap / Model Gap 与 deployment-evidence assurance loop。 |
| 2026-09-14 | Control Barrier Function Based Quadratic Programs for Safety Critical Systems | [DOI](https://doi.org/10.1109/TAC.2016.2638961) · [arXiv](https://arxiv.org/abs/1609.06408) · [CBFKit](https://github.com/bardhh/cbfkit) | 经典论文回顾；IEEE TAC 2017；CBF/CLF-QP、forward invariance 与运行时 safety filter。 |
'''

if '2609.12221' not in s:
    marker = '\n## 维护检查表'
    if marker not in s:
        raise RuntimeError('maintenance checklist marker not found')
    s = s.replace(marker, '\n' + rows + marker, 1)

p.write_text(s, encoding='utf-8')
