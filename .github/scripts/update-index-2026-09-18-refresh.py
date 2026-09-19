from pathlib import Path

p = Path('robotics-brief-covered-items.md')
s = p.read_text(encoding='utf-8')

old = '> 2026-09-18 新增 7 条主动态、1 条经典论文回顾与 2 条社区精选，共 690 条。'
new = '> 2026-09-18 早间首版新增 7 条主动态、1 条经典论文回顾与 2 条社区精选，共 690 条；随后因 9 月 18 日新公开批次刷新，更新同日文章并追加 8 条主动态、1 条经典论文回顾与 3 条社区精选，累计共 702 条。早间首版条目保留为历史覆盖记录。'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise RuntimeError('2026-09-18 summary line not found')

rows = '''| 2026-09-18 | AMB3R-SLAM: Kilometer-scale SLAM with Hierarchical Backend | [论文](https://arxiv.org/abs/2609.19518) · [项目页](https://hengyiwang.github.io/projects/amber-slam) · [代码](https://github.com/HengyiWang/amb3r-slam) | 9 月 18 日新公开批次；v1 2026-09-17；分层 local/mid/global 后端，公里级实时单目 SLAM，可扩展 stereo/RGB-D/LiDAR。 |
| 2026-09-18 | Dynamic-LIVO: A Dynamic-Aware LiDAR-Inertial-Visual Odometry System Using Spatio-Temporal Normals | [论文](https://arxiv.org/abs/2609.19336) | 9 月 18 日新公开批次；v1 2026-09-16；S-T normal 动态点检测跨 LiDAR/visual update 传播，证据不足时延迟分类。 |
| 2026-09-18 | Equivariant Filter Design for Acoustic and Depth Aided Inertial Navigation Systems | [论文](https://arxiv.org/abs/2609.19742) | 9 月 18 日新公开批次；v1 2026-09-17；Tangent-Group symmetry 将 IMU bias 纳入几何状态，DVL+pressure AUV EqF。 |
| 2026-09-18 | DR-MPC: Fast and Feasible Dynamics-Relaxed Model-Predictive Control for Legged Locomotion | [论文](https://arxiv.org/abs/2609.20035) | 9 月 18 日新公开批次；v1 2026-09-17；dynamics-relaxed box-QP + 专用 IPM；Go1 onboard median 4.4 ms。 |
| 2026-09-18 | Winning a Won Game: Strict Reach-Avoid-Stay Control Barrier Functions for High-Dimensional Black-Box Systems | [论文](https://arxiv.org/abs/2609.19449) | 9 月 18 日新公开批次；v1 2026-09-16；black-box sRAS Q-CBF；四足 gap-jump 真机与 F1TENTH。 |
| 2026-09-18 | Accelerating Visual Policy Learning with Sampling-Based Model Predictive Control / SGPS | [论文](https://arxiv.org/abs/2609.20575) | 9 月 18 日新公开批次；v1 2026-09-17；sampling MPC 周期性修正 FoPG visual policy；Go2 真机零样本部署。 |
| 2026-09-18 | Workspace Models: Lightweight Robotic Memory via Saliency-Driven Supervision | [论文](https://arxiv.org/abs/2609.20820) | 9 月 18 日新公开批次；v1 2026-09-17；CoRL 2026；训练时 VLM saliency 蒸馏为 deployment workspace token。 |
| 2026-09-18 | An Empirical Study of Harness Design for Coding Agents | [论文](https://arxiv.org/abs/2609.20804) | 9 月 18 日新公开批次；v1 2026-09-17；176 matched settings，消融 planning/action-space/context-management。 |
| 2026-09-18 | Parallel Tracking and Mapping for Small AR Workspaces / PTAM | [论文页](https://www.robots.ox.ac.uk/~lav/Papers/klein_murray_ismar2007/) · [DOI](https://doi.org/10.1109/ISMAR.2007.4538852) · [代码](https://github.com/Oxford-PTAM/PTAM-GPL) | 经典论文回顾；ISMAR 2007；Tracking / Mapping 并行化、关键帧与后台 BA 的视觉 SLAM 架构里程碑。 |
| 2026-09-18 | 社区精选：Claude Code per-command allowed_domains | [官方 Release](https://github.com/anthropics/claude-code/releases) | 社区精选；2026-09-18；sandbox 网络权限按单条 Bash/PowerShell/Monitor 命令临时放行域名。 |
| 2026-09-18 | 社区精选：Plugin install/update exact command SHA-256 approval | [官方 Release](https://github.com/anthropics/claude-code/releases) | 社区精选；2026-09-18；--accept-command <sha256> 将安装/更新批准绑定到确切命令 payload。 |
| 2026-09-18 | 社区精选：Code Review Finding Lifecycle | [GitHub Changelog](https://github.blog/changelog/2026-09-18-copilot-code-review-an-improved-review-experience/) | 社区精选；2026-09-18；review finding 跨 revision 维护 NEW/OPEN/RESOLVED 生命周期并重新验证。 |
'''

if 'AMB3R-SLAM: Kilometer-scale SLAM with Hierarchical Backend' not in s:
    marker = '\n## 维护检查表'
    if marker not in s:
        raise RuntimeError('maintenance checklist marker not found')
    s = s.replace(marker, '\n' + rows + marker, 1)

p.write_text(s, encoding='utf-8')
