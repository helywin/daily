from pathlib import Path

p = Path('robotics-brief-covered-items.md')
s = p.read_text(encoding='utf-8')

old = '> 2026-09-16 新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 648 条。'
new = '> 2026-09-16 早间首版新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 648 条；随后因 arXiv 9 月 16 日最新公开批次刷新，更新同日文章并追加 8 条主动态与 1 条经典论文回顾，累计共 657 条。早间首版条目保留为历史覆盖记录。'

rows = '''| 2026-09-16 | LiLi: Lie Theory Based 3D LiDAR Scan Alignment Degeneracy Detection | [论文](https://arxiv.org/abs/2609.17145) | 最新公开批次；v1 2026-09-15；Lie-theory / se(3) 重新关联感知退化检测；430 m 隧道 odometry。 |
| 2026-09-16 | HuMemSLAM: Efficient Human-Inspired Semantic Place Recognition for Robust Visual SLAM | [论文](https://arxiv.org/abs/2609.17168) | 最新公开批次；v1 2026-09-15；semantic/context VPR + ORB-SLAM3 几何验证。 |
| 2026-09-16 | TIO-Former: Ultra-Lightweight 6-Directional ToF-Inertial Odometry for Nano-UAVs via a Streaming Causal Transformer | [论文](https://arxiv.org/abs/2609.17198) · [仓库](https://github.com/Ly041021/TIO-Former) | 最新公开批次；v1 2026-09-15；6×8×8 ToF + IMU；RISC-V P95 10.466 ms；代码待发布。 |
| 2026-09-16 | Online Geometric Change Detection via Scene Decomposition | [论文](https://arxiv.org/abs/2609.17302) · [代码](https://github.com/vectr-ucla/geometric_change_detection) | 最新公开批次；v1 2026-09-15；LiDAR/RGB-D scene/submap 在线长期地图变化检测。 |
| 2026-09-16 | Hamilton-Jacobi Reachability for Hybrid Systems: Unified Goal-Driven Control with Safety Guarantees | [论文](https://arxiv.org/abs/2609.17430) · [DOI](https://doi.org/10.1177/02783649261477777) | 最新公开批次；v1 2026-09-15；hybrid safety filter + backward reach-avoid；四足真机。 |
| 2026-09-16 | Optimized Wrench Polytope Analysis for Real-Time Stability Control of Legged Robots in Complex Multi-Contact Configurations | [论文](https://arxiv.org/abs/2609.17405) | 最新公开批次；v1 2026-09-15；full actuatable wrench polytope；49 Hz；真实 walking robot。 |
| 2026-09-16 | Modality-Autoregressive World-Action Models / ModAR | [论文](https://arxiv.org/abs/2609.17524) · [项目页](https://adamhung60.github.io/ModAR/) | 最新公开批次；v1 2026-09-15；tracks→DINO→depth→RGB→action；future RGB 无稳定增益。 |
| 2026-09-16 | RepoAtlas: Guiding Coding Agents via Evolving Multimodal Repository Views | [论文](https://arxiv.org/abs/2609.16936) | 最新 Software Engineering 批次；v1 2026-09-15；select-project-refresh 动态代码图上下文；SWE-bench Verified。 |
| 2026-09-16 | On Degeneracy of Optimization-based State Estimation Problems | [CMU](https://publications.ri.cmu.edu/on-degeneracy-of-optimization-based-state-estimation-problems) · [DOI](https://doi.org/10.1109/ICRA.2016.7487211) | 经典论文回顾；ICRA 2016；Hessian/eigen 方向级退化检测与良态方向部分求解。 |
'''

if '2609.17145' in s:
    raise SystemExit('refresh entries already present; refusing duplicate update')
if old not in s:
    raise RuntimeError('expected 2026-09-16 header summary not found')
marker = '\n## 维护检查表'
if marker not in s:
    raise RuntimeError('maintenance checklist marker not found')

s = s.replace(old, new, 1)
s = s.replace(marker, '\n' + rows + marker, 1)
p.write_text(s, encoding='utf-8')
