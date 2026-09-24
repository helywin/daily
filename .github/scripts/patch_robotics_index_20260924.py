from pathlib import Path

p = Path('robotics-brief-covered-items.md')
s = p.read_text(encoding='utf-8')

old_date = '> 最后更新：2026-09-23（Asia/Shanghai）'
new_date = '> 最后更新：2026-09-24（Asia/Shanghai）'
assert old_date in s, 'expected last-update header not found'
s = s.replace(old_date, new_date, 1)

prev = '> 2026-09-23 新增 7 条论文/技术主动态、同一模型动态栏目覆盖 2 个官方模型发布、2 条 AI Coding 实战技巧精选与 1 条经典论文回顾，共 760 条。'
new_hist = '> 2026-09-24 新增 8 条主动态、2 条 AI Coding 实战技巧精选与 1 条经典论文回顾，共 771 条。'
assert prev in s, '2026-09-23 history line not found'
assert new_hist not in s, '2026-09-24 history already exists'
s = s.replace(prev, prev + '\n>\n' + new_hist, 1)

rows = '''
| 2026-09-24 | TM-APR: Thermal Temporal-Memory Localization via Analytic Online Adaptation | [论文](https://arxiv.org/abs/2609.26766) | 时间回补；v1 2026-09-22；ACIL + Unscented/GMM/H∞ 解析在线适配；闭式 O(1) 更新。 |
| 2026-09-24 | Dr-LiSA: Direct Radar-Lidar Scan Alignment for SE(3) Localization | [论文](https://arxiv.org/abs/2609.26423) | 时间回补；v1 2026-09-22；2D spinning radar 对 3D LiDAR map 的 learned-forward-model direct SE(3) alignment；>90 km 道路数据。 |
| 2026-09-24 | ArborSplat: Online Semantic Gaussian Splatting SLAM for Orchards | [论文](https://arxiv.org/abs/2609.26315) | 时间回补；v1 2026-09-22；LiDAR odometry + semantic 3DGS；class-constrained refinement 保留细结构表示容量。 |
| 2026-09-24 | Learning Air-Ground Motion Control with Temporal Mode Switching and Cross-Terrain Tracking | [论文](https://arxiv.org/abs/2609.26564) | 时间回补；v1 2026-09-22；历史单点 ToF + state/reference 模式选择器；RL 地面跟踪；101 m 真机空地轨迹。 |
| 2026-09-24 | Wheel-loader V-Cycle Automation with Deep Koopman MPC | [论文](https://arxiv.org/abs/2609.26580) | 时间回补；v1 2026-09-22；前进/后退双 deep bilinear Koopman model + MPC；50 ms 仿真控制循环。 |
| 2026-09-24 | SafeLoop: Risk-Aware Rollback for Vision-Language-Action Manipulation | [论文](https://arxiv.org/abs/2609.26313) · [代码](https://github.com/Loule0-0/SafeLoop/tree/release/safeloop) | 时间回补；v1 2026-09-22；model-agnostic VLA risk prediction + safe waypoint rollback；LIBERO/真机。 |
| 2026-09-24 | You Should Be Properly Scoring Your Odometry | [论文](https://arxiv.org/abs/2609.25900) | 时间回补；v1 2026-09-22；strictly proper scoring rules + smfeval；同时评估 pose error 与 covariance consistency。 |
| 2026-09-24 | CliffCompaction: Cost-Efficient Compaction for Long-Horizon Coding Agents | [论文](https://arxiv.org/abs/2609.26779) | 时间回补；v1 2026-09-22；truncation-only / original-context compaction，避免 summary drift；长时 Coding Agent。 |
| 2026-09-24 | AI Coding 实战技巧精选：Copilot app Local Sandboxing 默认沙箱新 Session | [GitHub 官方 Changelog](https://github.blog/changelog/2026-09-23-local-sandboxing-in-the-github-copilot-app/) | AI Coding 实战技巧精选；2026-09-23；filesystem/network/credentials 项目级 sandbox + `/sandbox on`；无法 enforce 时 fail-closed。 |
| 2026-09-24 | AI Coding 实战技巧精选：Copilot Code Review 分层使用 Lite / Balanced Effort | [GitHub 官方 Changelog](https://github.blog/changelog/2026-09-23-copilot-code-review-more-ways-to-request-and-configure-reviews/) | AI Coding 实战技巧精选；2026-09-23；push/draft 自动 review 与个人/企业默认 effort 配置。 |
| 2026-09-24 | A Flexible and Scalable SLAM System with Full 3D Motion Estimation / Hector SLAM | [DOI](https://doi.org/10.1109/SSRR.2011.6106777) · [代码](https://github.com/tu-darmstadt-ros-pkg/hector_slam) · [ROS Index](https://index.ros.org/p/hector_mapping/) | 经典论文回顾；SSRR 2011；无轮速 scan-to-occupancy-grid gradient Gauss-Newton + multi-resolution mapping。 |
'''.strip() + '\n'

for aid in ['2609.26766','2609.26423','2609.26315','2609.26564','2609.26580','2609.26313','2609.25900','2609.26779']:
    assert aid not in s, f'duplicate arXiv id already in index: {aid}'
assert '2026-09-24 | AI Coding 实战技巧精选：Copilot app Local Sandboxing' not in s
assert 'A Flexible and Scalable SLAM System with Full 3D Motion Estimation / Hector SLAM' not in s

marker = '\n## 维护检查表\n'
assert marker in s, 'maintenance checklist marker not found'
s = s.replace(marker, '\n' + rows + marker, 1)

p.write_text(s, encoding='utf-8')
print('patched index for 2026-09-24')
