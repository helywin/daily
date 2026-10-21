---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-21"
date: 2026-10-21 09:00:00 +0800
description: "动态视觉SLAM、退化轮足激光惯性定位、协作风险导航、500Hz推力辅助MPC、GPU运动学、异步无人机VLA与Coding Agent接手及PRD完整交付。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-21

## 摘要

**检索基准：2026-10-21 08:58（Asia/Shanghai）。** 2026-10-20 的 arXiv Robotics 最新公开批次有 **160 个列表条目**，Software Engineering 有 **42 个列表条目**；条目数包含交叉收录和更新版本，不等于新投稿总数。优先检查最近 24 小时，再扩展 7 天；与截至 10 月 20 日的 **1,053 条已覆盖记录**进行 arXiv ID、标题、项目页、代码仓库联合去重。以下有 **8 条此前未收录的主动态**、3 条一手 AI Coding 实操、1 篇经典论文回顾。10 月 18 日提交的两项工作标注为**时间回补**。

**今日技术主线是可信约束的分层。** CAOS-SLAM 通过按需识别、跟踪未知动态物体改善视觉定位；轮足 LiDAR–Inertial 方法学习不同车轮和运动方向的协方差，结合激光退化投影，在严重走廊退化实验中将终点误差从 7.531 m 降到 0.198 m。CoopUQ 将多机器人预测的未来占据和不确定性一起交给导航；Harpy 的 QP-MPC 以 500 Hz 联合控制推力与地面反作用力。CusADi2 让 GPU 同时利用批间、批内并行降低运动学/Jacobian/Hessian 的在线延迟。AeroDASH 通过连续 B-spline 拼接解决 UAV VLA 推理期间的运动连续性。

**AI Coding 的两项一手研究**提醒开发者：SWE-Residual 发现 Agent 接手前人留下的错误半成品时成功率显著下降；PACE 则指出修完单个组件并不意味着完整交付包含集成条件的 PRD。今日可直接尝试的工具侧技巧包括 GitHub npm Package Firewall 预览、Dependabot 告警版本字段和 Branch Protection 批量迁移 Rulesets。经典回顾选 **IJRR 2010 的 OC-EKF/FEJ 一致性论文**，与退化方向的虚假信息增益问题形成呼应。

性能数据均为论文作者在特定实验条件下的结果，不能直接外推到 RK3588、Jetson 或特定机器狗；“软件项目仓库存在”与“所有权重和数据完整可复现”亦须区分。

原始入口：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

## 1. CAOS-SLAM：让未知动态物体进入对象级跟踪，而不只是靠语义黑名单

**公开时间：arXiv v1 2026-10-19 16:00 UTC（最近 24 小时）。**

### 为什么重要

传统动态视觉 SLAM 经常预设“人、车”等类别，或者每帧运行昂贵的语义分割。但机器人会遇到未知移动物体，例如搬运推车、机械设备和临时遮挡物。其特征如果进入 ORB-SLAM3 估计器，可能污染相机位姿和静态地图。CAOS-SLAM 将目标**发现、跨帧关联、运动判断和特征过滤**分层，且不是所有帧都运行重型分割。

### 算法模块与传感器假设

~~~text
RGB-D + ORB-SLAM3
    ↓
按需 Panoptic Segmentation → 已知对象
    + 深度聚类 → 未分类对象候选
    ↓
轻量检测 / 世界系 Kalman 预测 / 深度一致性 / 外观关联
    ↓
对象轨迹与运动估计
    ↓
只剔除确实动态的特征
    ↓
静态几何定位与地图
~~~

它依赖 RGB-D 几何、可靠的对象关联和位姿变换。语义类别不是动态性的证明；未知静止物体不应一概删除，已知类别的临时静止对象也需按运动证据判断。遮挡和身份交换是主要风险。

### 实时性、鲁棒性与可复现性

作者报告：在未知动态物体场景，定位误差**最高降低 59%**；重遮挡场景**最高降低 88%**；笔记本上中位处理率 **30 FPS**。这两项百分比是各自场景下的最大改善，非统一保证。论文称代码与数据**待接收后发布**，不能标记为完整开源。

### 适合谁关注与工程落地启发

适合 RGB-D 巡检、室内人机共域导航、ORB-SLAM3。固定一组含人和移动推车的 bag，比较无过滤、语义过滤和跨帧运动过滤的静态有效点数、动态漏删率、误删率、ATE 与跟踪完整性。特别防止低纹理环境因为误删而无法继续定位。对象轨迹可共享给规划器，但要保留独立置信度。

来源：[CAOS-SLAM 论文](https://arxiv.org/abs/2610.26633)。

## 2. 学习车轮运动不确定性的退化感知 LIO：不要给每个轮速相同权重

**公开时间：arXiv v1 2026-10-19 15:12 UTC（最近 24 小时）。**

### 为什么重要

长走廊等场景中 LiDAR 缺少某些方向的几何约束，轮足机器人可以借助轮运动学；然而轮胎打滑、失去接触和滚动方向变化，使轮观测不能使用固定协方差。该方法保留**解析滚动预测**，只让网络估计逐轮、逐方向的过程协方差，再利用 Degeneracy-Aware Projection（DAP）抑制激光弱可观测方向的不可靠约束。

### 算法模块与动力学假设

~~~text
LiDAR + IMU + Wheel Joints / Contact History
         ↓
解析车轮滚动模型 + Moving Wheel-Center States
         +
CovNet：逐轮、逐方向协方差
         ↓
紧耦合状态滤波
         ↑
LiDAR 几何退化方向分析 + DAP
         ↓
位姿 / 速度 / 协方差
~~~

CovNet 用仿真速度监督和可微滤波训练，无需真机微调。网络不直接替代物理里程计，而是评估运动学测量可信度。轮半径、外参、时间同步、关节状态等前提仍须成立。

### 实验、实时性、鲁棒性

在退化比例最高的 6 条室内房间序列上，相对 FAST-LIO2 平均位置 RMSE **降低 66.2%**，相比固定协方差版本 **降低 31.0%**；严重退化走廊终点误差 **0.198 m**，FAST-LIO2 为 **7.531 m**。终点误差不能等同全程 ATE。论文尚未报告可外推到任意平台的统一实时频率，代码与数据处于计划公开状态。

### 适合谁关注与工程落地启发

适合轮足底盘、双 MID360、多雷达退化走廊。首轮不要立即修改滤波器：将 CovNet 作为只读旁路，记录每轮协方差、轮速创新量、LiDAR 信息矩阵弱方向、真实打滑证据，确认网络在地面打滑时降低轮测量信任，而不是让弱约束过度自信。

来源：[原论文](https://arxiv.org/abs/2610.26550) · [作者项目页](https://weihairuo.github.io/)。

## 3. CoopUQ：多机器人交换未来占据的不确定性，而不是只交换目标框

**公开时间：arXiv v1 2026-10-19 17:59 UTC（最近 24 小时）；CoRL 2026。**

### 为什么重要

在人群遮挡场景，一台机器人看不到的人可能出现在另一台机器人视野内。即使共享当前检测框，未来几秒的人群运动也可能多解。CoopUQ 从跨机器人时空特征融合中预测未来占据栅格及其不确定性，用约束多智能体强化学习让机器人同时规避**预计被占据**和**预测高度不确定**的区域。

### 算法模块与假设

~~~text
各机器人局部历史观测 / 相对位姿
             ↓
跨机器人时空特征融合
             ↓
未来 Occupancy Grid + Uncertainty
             ↓
Constrained Multi-Agent RL
             ↓
风险敏感的局部决策与执行
~~~

必须检查时钟同步、坐标对齐、消息年龄和定位协方差。预测网络的“不确定性”不是经过认证的碰撞概率；分布外人群突然奔跑时，独立近场避障仍须拥有更高优先级。

### 实验结果与可复现性

作者在 Unity3D 的多种布局、人群密度、遮挡与分布外奔跑行为中，相对代表性基线报告更好的预测和安全表现，并展示真机实验。摘要没有足以跨平台复用的统一 FPS 和碰撞率，不能补造。项目页已公布代码和视频入口，真正复现仍需要核验具体数据、训练和模型依赖。

### 适合谁关注与工程落地启发

适合多台巡检机器人在狭窄公共区域协作。建议先共享带时间戳的未来占据栅格与不确定性，固定当前局部规划器，对比单机感知与协作感知的最小障碍间距、过期消息率和预测校准误差，再决定是否训练 MARL。

来源：[CoopUQ](https://arxiv.org/abs/2610.26852) · [官方项目](https://coopuq.github.io/)。

## 4. Harpy：500 Hz QP-MPC 同时优化地面反作用力和主动推力

**公开时间：arXiv v1 2026-10-19 17:50 UTC（最近 24 小时）；IROS 2026。**

### 为什么重要

双足行走的可行力依赖足底摩擦和接触模式。Harpy 通过额外推力器调节载荷与身体动力学。该工作不是把推力作为随意的补偿项，而是将地面反作用力（GRF）和推力矢量一起放进可实时计算的压缩 QP-MPC。

### 算法模块、动力学假设

~~~text
速度与步态参考
      ↓
Thrust-assisted Spring-Loaded Inverted Pendulum
      ↓
Sagittal Condensed QP-MPC：GRF / 摩擦锥 / 推力分配
      +
Frontal Cascade Orientation Stabilization
      ↓
Harpy 机身、足端与推力器
~~~

论文在 Harpy 硬件上以 **500 Hz** 控制，QP 求解时间约 **0.18 ms**，低于 2 ms 周期预算。静止和 0.1 m/s 的参考速度下，均值速度能够跟踪参考，腿部轨迹误差在约 **1°** 内。注意 0.18 ms 是 QP 求解时长，不是传感器到执行器的总响应时间；推力迟滞、输入饱和和摩擦锥模型偏差均可能产生失效。

### 可复现性、工程风险与适合谁

未确认完整可直接运行的官方软件工程。适合多模态运动、足式+飞行混合机器人和力分配 MPC。建议在仿真中固定步态，对比无推力、固定推力与联合 QP 的 GRF 约束违例、能耗、输入饱和、完整闭环 P99；真机须额外验证推力失效和电机故障回退。

来源：[Harpy QP-MPC](https://arxiv.org/abs/2610.26810)。

## 5. CusADi2：在线 GPU MPC 更需要低延迟的成批 Jacobian/Hessian，而不只是最高吞吐

**时间回补：arXiv v1 2026-10-18 19:03 UTC。**

### 为什么重要

MPPI 或二阶轨迹优化每轮需要计算大量前向运动学、Jacobian、Hessian。传统 GPU 方法主要让不同候选批次并行；在线控制真正关心一个小批次的**墙钟完成时间**。CusADi2 在每个批次实例内部进一步并行，优化控制器常见的中小批量求值。

### 算法模块与计算假设

~~~text
Robot Model
    ↓
64–4096 Candidate States / Time Steps
    ↓
GPU Batch Parallel + Within-instance Parallel
    ↓
FK / Jacobian / Hessian
    ↓
Sampling MPC or Gradient-based Optimization
~~~

作者对 MuJoCo Menagerie 的 **67 个机器人**评估，比较 MuJoCo XLA、MuJoCo Warp、frax、CusADi、CasADi 等，报告在 batch 64–4096 时延迟优于所选全部基线，大批量时接近。这不是“所有硬件固定快几倍”，论文摘要也没有给出这样可普适的数字。

### 开源、鲁棒性和落地

[官方代码](https://github.com/johnviljoen/cusadi2) 已公开。复现时应报告 CPU-GPU 传输、Kernel Launch、实际求值和整个 MPC 求解 P50/P95/P99；同时对比浮点精度与数值梯度校验。该实现以 GPU 为目标，不能直接假设 RK3588 RKNN NPU 支持相同计算路径。

### 适合谁关注

适合 GPU MPPI、全身 IK、非线性轨迹优化、需要连续批量几何导数的控制器。工程上建议先替换计算后端而不改变求解器，从而区分数学收益和硬件实现收益。

来源：[CusADi2 论文](https://arxiv.org/abs/2610.25476) · [官方 GitHub](https://github.com/johnviljoen/cusadi2)。

## 6. AeroDASH：无人机 VLA 要丢弃过期预测并连续拼接新轨迹

**时间回补：arXiv v1 2026-10-18 17:05 UTC。**

### 为什么重要

VLA 推理时无人机仍持续移动。如果根据几百毫秒前画面生成的整个动作块直接执行，起始部分可能已经过期。直接拼接 Waypoints 又会引起速度和加速度不连续。AeroDASH 使用**B-spline 位置/yaw 轨迹**，新推理完成后丢弃已过期前缀，在导数连续与变形限制下融合剩余轨迹。

### 模块、动力学与时间语义

~~~text
Vision + Language → VLA B-spline Reference
                ↓
Current Time / Active Trajectory
                ↓
Discard Expired Prefix
                ↓
Derivative-continuous Trajectory Fusion
                ↓
High-frequency Flight Control
                ↑
Execution-aware GRPO 训练
~~~

作者通过执行感知 GRPO 降低异步预测与实际控制偏差。它不是让语言模型替代姿态控制器。实现须显式记录相机采集、模型开始和结束、轨迹目标执行时刻；若预测全部过期，应拒绝并进入独立悬停/保守模式。

### 结果、风险与复现

UAV-Flow 测试成功率 **76.56%**，较 OpenVLA-UAV 与无 GRPO 的 AeroDASH 分别高 **38.1、20.1 个百分点**。执行实验中推理期间持续飞行，且加速度、jerk、速度波动优于异步 waypoint 跟踪。作者称代码将在接收后公开，现阶段不能认定为完整可运行实现。

### 适合谁关注与工程落地启发

适合 PX4、走廊 UAV、异步 Action Chunk。建议先独立实现 Trajectory Manager：新轨迹版本、过期区间删除、连续拼接、安全净空复核，保持底层飞控不变；然后再决定是否接入 VLA。

来源：[AeroDASH 论文](https://arxiv.org/abs/2610.25407)。

## 7. SWE-Residual：Agent 接手“已修改但没修好”的工作树时会产生接受偏差

**公开时间：arXiv v1 2026-10-19 UTC（最近 24 小时）。**

### 突破性工程价值

传统 Coding Agent Benchmark 通常从干净仓库开始。真实开发却常常接手人类或另一 Agent 声称“已完成”的工作树，但隐藏行为仍错误。SWE-Residual 只改变 Agent 的**起始状态**，其余任务描述与隐藏验收保持不变，测量是否仍能独立理解原需求。

### 实验设计、结果与解释

Benchmark 包含 **111 个任务的 198 个 Residual State**，来自 DeepSWE 和 Terminal-Bench，前任 Agent 已提交其认为完成的修改，但实际隐藏测试没有全过。接手模型看不到前任轨迹，也不知道该状态是失败产物。

五个前沿 Agent 的成功率相对 Clean Start：DeepSWE 下降 **20.6–53.5 个百分点**；Terminal-Bench 下降 **20.6–34.9 个百分点**。在 DeepSWE 失败的接手实验中，**58.9%–88.2%** 保留了与接手时完全相同的失败测试。作者称之为 Acceptance Bias：模型将已有实现当作事实，而不是重新核对需求。

### 研发流程、权限与验证风险

“拒绝相信已有代码”不等于允许 Agent 自动丢弃开发者工作。应当保留当前 Diff，在隔离 Worktree 中独立运行测试、审视需求和行为不变量，再决定最小修改。不要让接手者修改其自身验收规则。多 Agent 并行需要清楚的文件所有权和集成步骤。

### 适合谁关注与工程落地启发

适合 Codex/Claude Code 长任务、跨会话恢复、大仓 Agent 接力。一个直接可用的 A/B 是为同一 Issue 构造 Clean Start 和部分错误补丁起点，保持预算一致，测量真实修复率、错误前提保留次数及每成功任务成本。

来源：[SWE-Residual 论文](https://arxiv.org/abs/2610.25899)。

## 8. PACE：单文件修复分数高，不意味着真实 PRD 已完整交付

**公开时间：arXiv v1 2026-10-19 13:39 UTC（最近 24 小时）。**

### 突破性工程价值

PRD 驱动开发经常跨 API、数据库、UI、权限、配置和部署。Agent 写出了接口与类，并不代表这些模块协同工作。PACE 使用经过专家审核的**需求 Code Points** 和行为证据来评价完整交付，而非仅看一个 Patch 能否通过局部测试。

### 评测规模和主要结果

研究覆盖 **43 项成熟企业仓库任务、750 个专家审阅 Code Point、11 种模型—Harness 组合**。多数评分在 **52.1–78.1**，最佳受测配置的**完整交付率只有 14.0%**；评分与专家共识一致率 **95.2%**。最典型的失败是各组件分别存在，但集成遗漏或不符合完整需求。在同一模型和任务集上，定向调整 Harness 后，平均得分从 **59.4** 到 **63.0**。

这些是作者定义的任务和评分体系，不能直接外推为所有软件项目的真实完成率。

### 真实研发、权限和落地

适合 Spring Boot 多模块、ROS2、C++ 和 Web 管理端。最小落地不是增加大量验收文档，而是从 PRD 提取 8–15 条真正可执行的行为契约：正向流程、错误分支、跨服务接口、配置生效、权限边界。Agent 可以写代码，但不能任意降低独立测试条件；最终报告应列出尚未验证的集成点。

### 可复现性

[官方 PACE-Bench 仓库](https://github.com/TianqiLiu1/PACE-Bench) 已公开。可以选一个已有三模块业务需求，独立复核“单测都通过”与“真实需求完全可用”之间的落差。

来源：[PACE 论文](https://arxiv.org/abs/2610.26394) · [开源项目](https://github.com/TianqiLiu1/PACE-Bench)。

## AI Coding 实战技巧精选

### 技巧 1｜让 Agent 的 npm 安装先走 Package Firewall

**来源：** GitHub，2026-10-20，[正式公告](https://github.blog/changelog/2026-10-20-github-package-firewall-in-public-preview/) 与 [官方配置文档](https://docs.github.com/en/enterprise-cloud@latest/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/protecting-endpoints-with-package-firewall)。

**一句话结论：** 企业预览版可在 Agent/CI 安装 npm 依赖前检查恶意软件、已知漏洞、新增安装脚本、Attestation 降级和最小包龄期。

**具体怎么做：**
1. Enterprise Cloud 管理员打开 **Policies → Package firewall**，在沙盒环境设置规则；官方默认包龄期为 1 天。
2. 为隔离的测试 Runner 配置用户级 npmrc：
   ~~~ini
   registry=https://package-firewall.githubapp.com/npm/enterprises/ENTERPRISE
   //package-firewall.githubapp.com/npm/enterprises/ENTERPRISE/:_authToken=YOUR_TOKEN_FROM_ENV
   ~~~
   将 ENTERPRISE 替换为企业标识，实际访问令牌由 CI Secret/环境变量注入，**不可提交到 Git**。
3. 执行 npm ci，验证安装、拦截和例外审批，同时检查是否存在绕过防火墙直连公共 registry 的路径。

**适合什么场景：** 企业 Coding Agent、Actions Runner、npm 自动安装。**注意：** 当前仅支持 npm、Enterprise Cloud **公开预览**；预览期免费、正式版可能按用量收费。不是所有个人仓库均可用。

### 技巧 2｜Dependabot Alert 直接传入已记录的依赖版本

**来源：** GitHub，2026-10-20，[原始公告](https://github.blog/changelog/2026-10-20-dependabot-alerts-rest-api-now-includes-dependency-versions/)。

**一句话结论：** REST 告警中的 dependency.version_requirement 让修复 Agent 无需重复解析锁文件，就能获得 GitHub 最后记录的依赖版本或版本范围。

**具体怎么做：**
1. 对已有权限的测试仓库执行：
   ~~~bash
   gh api repos/OWNER/REPO/dependabot/alerts \
     --jq '.[] | {number, name: .dependency.package.name, version: .dependency.version_requirement, state}'
   ~~~
2. 将 version_requirement 与 Advisory 的 vulnerable version range 分开交给修复 Agent；让 Agent 明确升级的目标约束。
3. 如果字段为 null、长约束被截断或一条告警覆盖多个版本，回退到锁文件和实际构建解析结果，不能凭该字段声称所有依赖已修复。

**适合什么场景：** Dependabot 自动修复、Agent 安全升级与报告。**注意：** 无 Lockfile 时可能只有 manifest 声明约束，并不代表唯一实际安装版本。

### 技巧 3｜GitHub 分支保护迁移 Rulesets 时先 Evaluate，不要直接删旧规则

**来源：** GitHub，2026-10-20，[原始公告](https://github.blog/changelog/2026-10-20-bulk-migrate-branch-protections-to-rulesets-for-a-repository/)。

**一句话结论：** 可以批量迁移经典 Branch Protection，但应先回归测试 Agent Bot 的权限和必需 CI 检查。

**具体怎么做：**
1. 仓库进入 **Settings → Rulesets → Import branch protection rules**。
2. 预览旧规则如何展开成新 Rulesets，核对 Required Reviews、Required Status Checks、分支匹配模式和 Bot Bypass。
3. 先选择 **Evaluate** 验证匹配逻辑，再经管理员批准切换 **Active**；测试通过前保留旧分支保护。
4. 在无害 PR 上分别模拟人类与 Agent Bot 的合并流程，确认双方权限满足预期。

**适合什么场景：** Copilot/Codex 自动 PR、企业多分支治理。**注意：** Rulesets 不是给 Agent 取消审查的工具，误配 Bypass 可能直接削弱 Merge Gate。

## 经典论文回顾

### Observability-based Rules for Designing Consistent EKF SLAM Estimators（IJRR 2010）

**发表时间与历史位置：** Guoquan P. Huang、Anastasios I. Mourikis 与 Stergios I. Roumeliotis 的论文于 **2009-12-11** 首次在线发布，**2010 年**发表于 International Journal of Robotics Research 29(5):502–528。它奠定了后续 EKF-SLAM、VIO 关于**可观测性一致性**的重要理论基础。

**核心问题。** 真实 SLAM 在缺乏全局参考时存在不可观测的坐标规范自由度。标准 EKF 每个周期都使用最新估计重新线性化状态和观测模型，可能让线性化误差系统拥有**比真实非线性系统更多的可观测方向**。滤波器因此在没有新增信息的方向上缩小协方差，错误地表现得越来越自信。

**算法模块和数学思想：**

~~~text
运动模型 + 测量模型
        ↓
分析非线性系统不可观测子空间
        ↓
选择不会引入虚假可观测性的线性化点
        ├─ OC-EKF：在可观测性约束下优化线性化点
        └─ FEJ-EKF：使用变量首次可用估计计算 Jacobian
        ↓
更一致的误差状态与协方差
~~~

**传感器/动力学假设。** 模型依赖正确的数据关联、观测噪声和运动方程。OC-EKF 解决的是不当线性化造成的信息虚增，并不能修复轮胎实际打滑、LiDAR 时钟失配或错误回环。

**当年为何重要。** 作者以理论、仿真和实验说明，估计器的低 RMSE 不一定意味着它的协方差可信；维护正确的不可观测子空间，是稳定融合传感器的重要基础。

**今天仍使用的思想。** 今天的 LIO/VIO 退化方向分析、FEJ、不变滤波和 Gauge Freedom 处理都延续了类似原则：没有物理观测支持的自由度，不应因为数值优化收敛就获得虚假置信度。本期轮足 LIO 通过 DAP 与方向相关轮观测协方差，属于在不同估计架构下处理这一原则的当代实践。

**后来被替代/扩展的部分。** 因子图平滑、滑窗 BA 和不变滤波在大规模问题中更具灵活性，但它们同样需要正确处理不可观测方向；单纯使用更强优化器不会凭空增加可观测性。

**公开资料与可复现性：** [IJRR 原论文 DOI](https://doi.org/10.1177/0278364909353640) · [2008 年 FEJ 前序工作](https://doi.org/10.1109/ROBOT.2008.4543252)。原论文不是一键运行的现代 ROS2 工程。可在二维 EKF-SLAM 仿真中固定地图和噪声，对比标准 EKF 与 FEJ；主要指标为 RMSE、NEES、置信覆盖率、不可观测方向协方差和定位重置后的行为。

**对当前工程的解读：** 长走廊中间歇丢失横向或偏航观测时，先识别**究竟缺少哪个方向的几何约束**，再决定轮速、IMU、UWB 或主动运动如何补充，而不是无条件增加某个测量权重。

## 今日结论

今天多项研究都在处理**不要对弱证据过度自信**的问题。

CAOS-SLAM 让对象运动决定视觉特征的可信度；轮足 LIO 将激光退化和逐轮打滑纳入协方差；CoopUQ 使多机器人预报带有不确定性。Harpy 与 CusADi2 区分数学上可行的控制与在有限算力下能否及时求解。AeroDASH 区分**生成时刻**和**真正执行时刻**，拒绝让过期轨迹参与运动。

SWE-Residual 和 PACE 则把相同原则带进 Coding Agent：已有代码不意味着真实需求已经满足，局部测试通过也不意味着跨模块交付成功。Agent 应当使用独立可执行的验收证据，而不是大量无效过程文档。

**本期结论：SLAM 要维护可观测性，控制要维护动力学和时间可行性，Coding Agent 要维护独立验证边界。**

## 最值得深入研究或尝试复现的方向

1. **动态 ORB-SLAM3 对照。** 比较无过滤、语义过滤、跨帧对象运动过滤，统计静态点误删与跟踪失败。
2. **轮足退化信息 Sidecar。** 保存逐轮方向协方差、轮速创新量与 LiDAR 信息矩阵弱特征值；先 Shadow Mode 后进入正式估计。
3. **多机器人预测栅格。** 带时间戳、位姿协方差共享未来占据，比较协作/单机模式的风险校准与最小净空。
4. **500 Hz QP 控制预算。** 先比较核心 Solver 与完整感知—计算—执行链的 P99，再测试推力失效。
5. **CusADi2 批量计算 A/B。** 对同一个机器人测 64/256/1024/4096 batch 的 Jacobian/Hessian 延迟、GPU 同步及数值误差。
6. **异步 UAV 轨迹管理。** 先实现旧前缀丢弃、连续拼接、超时降级，再接入 VLA。
7. **Agent 残留工作树评测。** 同一需求比较 Clean Start 与已有错误半成品，测不完整修复率。
8. **PRD 完整验收。** 用少量跨模块真实测试取代“生成代码即完成”的评分。
9. **Agent 依赖与权限。** 在支持的企业环境试用 npm Firewall，结合 Dependabot 版本字段和 Rulesets Evaluate 验证。

## 参考资料

**最新批次：** [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

**SLAM / 导航：** [CAOS-SLAM](https://arxiv.org/abs/2610.26633) · [Wheel Covariance LIO](https://arxiv.org/abs/2610.26550) · [CoopUQ](https://arxiv.org/abs/2610.26852) · [CoopUQ 项目](https://coopuq.github.io/)。

**控制 / 端侧：** [Harpy QP-MPC](https://arxiv.org/abs/2610.26810) · [CusADi2](https://arxiv.org/abs/2610.25476) · [CusADi2 GitHub](https://github.com/johnviljoen/cusadi2) · [AeroDASH](https://arxiv.org/abs/2610.25407)。

**AI Coding：** [SWE-Residual](https://arxiv.org/abs/2610.25899) · [PACE](https://arxiv.org/abs/2610.26394) · [PACE GitHub](https://github.com/TianqiLiu1/PACE-Bench) · [Package Firewall](https://github.blog/changelog/2026-10-20-github-package-firewall-in-public-preview/) · [Dependabot API](https://github.blog/changelog/2026-10-20-dependabot-alerts-rest-api-now-includes-dependency-versions/) · [Rulesets Migration](https://github.blog/changelog/2026-10-20-bulk-migrate-branch-protections-to-rulesets-for-a-repository/)。

**经典论文：** [Observability-based Rules for Designing Consistent EKF SLAM Estimators](https://doi.org/10.1177/0278364909353640)。
