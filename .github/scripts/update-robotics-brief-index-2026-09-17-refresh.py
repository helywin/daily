from pathlib import Path

path = Path('robotics-brief-covered-items.md')
text = path.read_text(encoding='utf-8')

old_summary = '> 2026-09-17 新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 669 条。'
new_summary = '> 2026-09-17 早间首版新增 8 条主动态、1 条经典论文回顾与 3 条社区精选，共 669 条；随后因 arXiv 9 月 17 日最新公开批次刷新，更新同日文章并追加 8 条主动态、1 条经典论文回顾与 2 条社区精选，累计共 680 条。早间首版条目保留为历史覆盖记录。'

if old_summary in text:
    text = text.replace(old_summary, new_summary, 1)
elif new_summary not in text:
    raise RuntimeError('2026-09-17 summary marker not found')

rows = '''| 2026-09-17 | SEAM: Submap-Anchored Evidence for Lifelong LiDAR Mapping under Trajectory Deformation | [论文](https://arxiv.org/abs/2609.18819) | 最新公开批次；v1 2026-09-16；submap-anchored evidence、DOP 跨 session 回环置信度、directional voxel change evidence |\n| 2026-09-17 | SOL-SLAM: Inverse Compositional Gauss-Newton Direct Registration for Fast Sonar-Only Local SLAM | [论文](https://arxiv.org/abs/2609.18893) | 最新公开批次；v1 2026-09-16；FLS-only dense direct registration、IC-GN、AUV 嵌入式 local SLAM |\n| 2026-09-17 | Benchmarking Visual-Inertial Odometry in Subterranean Environments Under Sensor Degradation, Miscalibration, and Dynamic Occlusion | [论文](https://arxiv.org/abs/2609.18628) | 最新公开批次；v1 2026-09-16；CERBERUS failure-centric VIO benchmark、9 类退化、coverage/failure threshold |\n| 2026-09-17 | ElastiQP: An Always-Feasible QP Solver for Constrained Robot Control | [论文](https://arxiv.org/abs/2609.19080) · [代码](https://github.com/StanfordASL/elastiqp) | 最新公开批次；v1 2026-09-16；hard equality + per-inequality L1 elasticity；header-only C++ / Python / JAX |\n| 2026-09-17 | Adaptive-MHE: A Sampling-Based Adaptive MPC for Legged Loco-Manipulation via Moving Horizon Estimation | [论文](https://arxiv.org/abs/2609.17832) | 时间回补；v1 2026-09-15；online sampling Sys-ID / MHE 估计 mass、friction 并耦合 sampling MPC |\n| 2026-09-17 | VLA-ULAP: Interleaving Cloud VLA Calls with Ultra-Lightweight Local Action Prediction at the Edge | [论文](https://arxiv.org/abs/2609.18663) | 最新公开批次；v1 2026-09-16；约 7.4M edge action predictor、端云 VLA 分层、减少远端调用 |\n| 2026-09-17 | ProgramDistill: From Interactive Web Apps to Verifiable Reference-Guided SWE Tasks | [论文](https://arxiv.org/abs/2609.18805) | 最新 Software Engineering 批次；v1 2026-09-16；reference-app behavior discovery、1,975 replay behaviors、4,063 tasks |\n| 2026-09-17 | Not All Agents Are Equal: Code Quality and Post-Merge Maintenance Across Five Autonomous Coding Agents in the Wild | [论文](https://arxiv.org/abs/2609.17598) | 时间回补；v1 2026-09-12；37,623 PR / 2,807 repos 的 post-merge observational study；非随机对照排名 |\n| 2026-09-17 | The Normal Distributions Transform: A New Approach to Laser Scan Matching | [DOI](https://doi.org/10.1109/IROS.2003.1249285) | 经典论文回顾；Biber & Straßer，IROS 2003；cell-wise Gaussian scan registration、无显式 correspondence |\n| 2026-09-17 | 社区精选：为 Headless Coding Agent 的 MCP 启动设置 Deadline | [Claude Code Releases](https://github.com/anthropics/claude-code/releases) | 社区精选；官方工具作者发布；v2.1.274，2026-09-17；CLAUDE_CODE_MCP_STARTUP_WAIT_MS |\n| 2026-09-17 | 社区精选：Plugin / Skill 使用可复现 Regression Eval | [Claude Code Releases](https://github.com/anthropics/claude-code/releases) | 社区精选；官方工具作者发布；v2.1.269，2026-09-11；claude plugin eval JSON/HTML scored report |\n'''

if 'SEAM: Submap-Anchored Evidence for Lifelong LiDAR Mapping under Trajectory Deformation' not in text:
    marker = '\n## 维护检查表'
    if marker not in text:
        raise RuntimeError('maintenance checklist marker not found')
    text = text.replace(marker, '\n' + rows + marker, 1)

path.write_text(text, encoding='utf-8')
