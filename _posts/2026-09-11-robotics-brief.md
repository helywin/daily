---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-11"
date: 2026-09-11 09:00:00 +0800
description: "本期聚焦 OSM 车道几何漂移校正、千赫兹 FPGA MPC、执行器动力学课程、机器人世界模型因果拆分、低延迟 JEPA Policy、学习规划对称性，以及跨仓库检索和自动修复停止条件。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-11

## 摘要

截至 2026-09-11 早间，arXiv Robotics 最新公开批次为 2026-09-10，共 82 条，其中 42 条为 new submissions；Software Engineering 同日共 36 条，其中 18 条为 new submissions。严格最近 24 小时内，高质量、可完整核验且未进入历史覆盖索引的机器人 / SLAM / 控制工作不足 5 条，因此本期依照任务规范扩展到最近 7 天。本期主动态的 v1 主要提交于 9 月 8–9 日 UTC，另有一篇世界模型工作提交于 9 月 6 日，均明确标记为“时间回补”。（[Robotics 最新列表](https://arxiv.org/list/cs.RO/new)，[Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)）

今天 SLAM / 定位侧最值得优先看的工作是 **Odometer-Agnostic Drift Correction Using OpenStreetMap Lane Geometry**。它没有要求重新设计一个新的 LiDAR / Visual odometry，而是在任何已有里程计后面增加一个很薄的地图约束层：把最近一小段轨迹直接对齐到 OpenStreetMap 车道中心线。作者的实现平均约 19.5 ms/pose，约等于 51 Hz；在 KITTI-360 上，LiODOM 的平均 2D APE 从 334.33 m 降到 19.24 m，KISS-ICP 从 82.73 m 降到 12.17 m。对于没有回环、又不想维护高精 3D 先验地图的地面机器人，这种“局部高频里程计 + 稀疏公共地图低频纠漂”很有工程价值。（[论文](https://arxiv.org/abs/2609.10336)，[代码](https://github.com/Joaquinecc/icp_trajectory_alignment_osm)）

控制侧最强的硬件工程信号来自 **AccelMPC**。作者不是继续把 MPC 算法扔给一颗更大的 CPU，而是联合设计 ADMM 求解器、数值表示、FPGA 映射和物理载板，在 35 g Crazyflie 上增加约 6 g FPGA PCB，做到真正机载的 **1 kHz constrained MPC**，还能处理动态障碍；相对嵌入式 MCU 求解器，最高达到 15.6 倍求解加速和 195.4 倍 energy-delay product 改善。这说明对小型无人机而言，MPC 的下一轮竞争不只在算法，也在“算法—数值—硬件”共同设计。（[论文](https://arxiv.org/abs/2609.09380)，[FPGA Deck](https://github.com/A2R-Lab/Crazyflie_FPGA_Deck)，[ADMM FPGA](https://github.com/A2R-Lab/ADMM_FPGA)）

强化学习控制方面，**Actuator Dynamics Curricula** 研究了一类很现实、却经常被误判成“奖励没调好”的失败：任务的可行状态集合太窄，随机探索在产生有用梯度前就终止。作者训练初期人为提高关节刚度，并按临界阻尼选择 damping，让系统暂时拥有更大的 viability kernel；随着策略成功率上升，再把刚度逐渐退火到真实系统辨识值。Boston Dynamics Spot 的四足到倒立转换中，固定真实刚度训练会停在永远无法完成动作的局部平台，而 curriculum 在 10 个随机种子中都能完成，并零样本转到真机。这里值得带走的是：**sim-to-real curriculum 不一定只能改变地形或奖励，也可以暂时改变执行器动力学，再严格退火回真实系统。**（[论文](https://arxiv.org/abs/2609.09492)）

机器人世界模型方面，**Identifying Habit, Physics, and Nuisance in Robot World Models** 试图把遥操作数据里的多模态来源真正拆开：operator habit 决定“人喜欢怎样选动作”，physics 决定“动作执行后世界怎样变化”，camera / appearance nuisance 决定“同一物理状态看起来怎样”。论文用结构因果模型明确区分三者，并建议迁移时冻结共享 physics readout，只适配很薄的 interface，而不是让新用户习惯或新相机外观重写整个 dynamics model。对机器人数据平台，这比“所有 domain shift 都丢给大模型继续微调”更合理。（[论文](https://arxiv.org/abs/2609.09210)）

VLA / 模仿学习方面，**JEPA Policy** 给出了一个很有端侧价值的替代路线：不做迭代 diffusion sampling，而是在训练时把 action chunk 和真实发生的 future representation 成对监督。共享 Transformer 同时学习“我要做什么”和“做完以后表示应该走向哪里”，未来预测直接塑造动作表征。九个仿真任务和五个真实任务中都保持同样的排名优势；模型平均延迟约 13.2 ms、P95 约 14.5 ms，而论文评测配置中的 100-step Diffusion Policy 约 439.5 ms。未来表征因此可以作为训练信号，而不必把视频生成或多步 denoising 永久带进部署路径。（[论文](https://arxiv.org/abs/2609.09630)，[代码](https://github.com/jiejie567/JEPA-Policy)，[项目页](https://jiejie567.github.io/JEPA-Policy/)）

学习式运动规划方面，**What Symmetry Buys a Learned Motion Planner** 的结论很“反架构崇拜”：仅仅把起点和终点变换到一个规范坐标系，原点取二者中点、主轴沿 `goal-start`，就能一次消掉 SE(3) 中 3 个平移和 2 个旋转自由度。保持模型、数据与预算不变，held-out collision-free rate 从 14.60% 提高到 51.10%；而为剩余绕起终连线的旋转再加入更复杂 equivariant mechanism，只带来不到 1 个百分点的最终收益。它提醒我们，在训练等变网络以前，应该先问：**问题本身是否已经提供了一个几乎免费的 canonical frame？**（[论文](https://arxiv.org/abs/2609.10033)）

AI Coding 侧，本期两条工作非常适合真实开发平台。**CrossCoder** 将 target repository 和外部依赖库一起构造成统一知识图谱，通过 planner + semantic retrieval 找关键节点，再选择性展开多跳邻居；它还新增 VersionExec，专门评测 dependency version 改变后的代码兼容性。论文报告 pass@1 最高提高 6.3%，并能把 RepoExec 平均候选节点规模从约 9,914 压到 23.5，同时保持依赖召回；代价是检索推理耗时和输入 token 也明显增加。对企业私有仓库而言，真正的仓库上下文边界很少停在单 Repo，版本化依赖必须进入 Agent 的 retrieval graph。（[论文](https://arxiv.org/abs/2609.09987)）

另一篇 **If It’s Not Buggy, Don’t Fix It** 则说明“让 Agent 再找一轮 bug”可能本身就是有害操作。模型会在完全正确的程序里持续声称找到缺陷，且对正确程序造成破坏的概率可能高于真正修复 buggy program 的概率；长时迭代甚至会进入 pseudo-bug-fixing cycle：同一修改被加上、撤回、再加上。论文还找到与“代码有 bug”内部表征相关的 steering direction。生产 Coding Agent 因此需要显式的 **abstention / stopping rule**：没有失败测试、静态分析证据、运行时异常或明确需求变化时，不应该因为“还能继续优化”就自动继续改代码。（[论文](https://arxiv.org/abs/2609.10123)）

近期旗舰模型方面，本轮重新检查主要官方入口，没有发现 9 月 10–11 日需要挤掉上述机器人 / 控制 / AI Coding 条目的全新旗舰模型正式发布；GPT-6 Astra、Gemini 3.8 Flash、Claude Fable 5.1 已在此前简报覆盖，本期不重复。

## 1. OSM Lane Geometry Drift Correction：不换里程计，只给它一条稀疏公共地图“校准绳”

**时间回补：arXiv v1 提交于 2026-09-09 15:33 UTC；IEEE RA-L 2026 接收。**

### 为什么重要

长期地面机器人经常处在一个尴尬区间：LiDAR / Visual odometry 在几十秒内很好，但几公里没有回环以后一定漂；高精 3D 先验地图又贵、更新慢、难跨城市维护。

这篇工作的切入点很克制：不碰前端里程计，只利用 OpenStreetMap 里最稳定、最廉价的一层几何——**道路 / 车道中心线**。

```text
LiDAR / Visual Odometry
          ↓
Recent Trajectory Window
          ↓
OSM Lane Centerlines
          ↓
Direction-Aware Correspondence
          ↓
Trimmed SE(2) ICP
          ↓
Corrected Ground-Plane Pose
```

因此 KISS-ICP、LiODOM、Basalt、ORB-SLAM3 之类都可以保留原样，地图校正只是后置层。

### 算法模块

作者先把 OSM lane geometry 转到本地 UTM / Lanelet2 坐标系，并沿中心线稀疏采样。最近一段 odometry trajectory 经过当前全局变换后，与 lane KD-tree 建 correspondence；但它不是普通 nearest-neighbor ICP，而是加入**轨迹方向与道路方向一致性**，尽量避免在平行车道、十字路口中匹配到几何上近、语义上错的 lane。

随后在地面 SE(2) 上做 trimmed ICP，并根据有效 correspondence 比例与 residual 决定是否接受更新。匹配失败时系统可以保留原 odometry，等待后续轨迹积累出更有辨识度的形状以后重试。

### 传感器与几何假设

它不是 6-DoF SLAM 后端，而是面向道路车辆 / 地面机器人的平面纠漂。核心前提包括：

- 最近一段 odometry 虽然整体漂移，但局部轨迹形状仍大体可信；
- OSM lane geometry 在当前位置足够完整；
- 运动方向和道路拓扑能提供辨识度；
- 当前全局初值没有错到完全匹配到另一条远处道路。

因此它不是任意位置的 global place recognition，也不能替代 GNSS / visual place recognition 做大范围冷启动。

### 实时性与结果

论文报告平均约 **19.5 ms/pose，约 51 Hz**；主要时间花在 lane matching，trimmed ICP 本身只有亚毫秒量级，整体可兼容常见 10 Hz LiDAR odometry 与 10–30 Hz camera odometry。

KITTI-360 的结果很直观：LiODOM 平均 2D APE 从约 **334.33 m → 19.24 m**，KISS-ICP 从 **82.73 m → 12.17 m**；视觉后端同样获得改善。这里最重要的不是某一个绝对数字，而是 correction layer 对多种 odometer 都能工作。

### 鲁棒性、可复现性与风险

代码已经公开，可复现性很好。真正的风险来自地图本身：OSM 可能道路缺失、车道中心线偏移、施工后拓扑过期；大型路口、平行道路也会产生局部几何歧义。

因此生产系统不要让 OSM alignment 直接覆盖主状态，而应输出：

```text
MapCorrection {
  delta_pose
  residual
  correspondence_ratio
  lane_ids
  confidence
  map_age
}
```

再由 factor graph / EKF 或一致性 Gate 决定是否吸收。

### 适合谁关注

园区巡检车、无人配送、道路机器人、没有闭环的大范围巡航，以及想降低高精地图维护成本的团队。

### 工程落地启发

对于已有 LIO-SAM / KISS-ICP 系统，最小可行验证甚至只需要：每 1–2 秒取一段最近轨迹，在后台对 OSM / 自建稀疏道路中心线做 SE(2) alignment；先作为 shadow global correction 记录，不直接回写状态。统计几周以后再决定是否变成正式 pose factor。

[论文](https://arxiv.org/abs/2609.10336) · [代码](https://github.com/Joaquinecc/icp_trajectory_alignment_osm)

## 2. AccelMPC：1 kHz MPC 开始成为 35 g 微型无人机上的机载控制器

**时间回补：arXiv v1 提交于 2026-09-08 19:27 UTC。**

### 为什么重要

小型无人机动力学快，但算力、功耗、载荷都极其有限。传统 MPC 的矛盾是：越想增加约束、障碍、预测长度，优化问题越大；为了跑在 MCU 上又不得不降低控制率，最后 MPC 的“预测能力”被计算延迟抵消。

AccelMPC 不把这看成纯 solver 问题，而是端到端共同设计：

```text
MPC Formulation
     ↓
ADMM Solver Structure
     ↓
Numerical Representation
     ↓
FPGA Data Path
     ↓
Custom 6 g PCB
     ↓
35 g Crazyflie Platform
```

这和服务器上“换一个优化库”完全不同。

### 算法与硬件模块

求解器基于结构化 ADMM，并针对 FPGA 做固定的数据流和并行映射。硬件是 AMD Xilinx Artix-7 系 FPGA 的 Crazyflie 扩展板；官方同时公开 PCB、FPGA accelerator 和 Crazyflie firmware integration。

作者在飞行器上真正闭环运行 constrained MPC，而不是仅仅 FPGA 离线 benchmark。

### 动力学与系统假设

MPC 依然依赖合理的线性 / 局部模型、状态估计和约束定义。FPGA 只是让优化更快，并不会消除：

- aerodynamic mismatch；
- 电池电压变化；
- thrust model 误差；
- 状态估计延迟；
- 极端接触 / 撞击后的模型失效。

因此“1 kHz 求解”不应被误读成“1 kHz 就自动更安全”。

### 实时性与结果

硬件实验达到 **1 kHz onboard constrained MPC**，并包含动态障碍；相对嵌入式 MCU 方案，最高报告 **15.6× solve-time speedup** 与 **195.4× energy-delay product improvement**。求解器还能扩展到超过 **20,000 个优化变量**和数量相当的约束。

对于微型无人机，1 kHz 意味着求解器预算进入约 1 ms 级别，MPC 已经可以和高频姿态 / 轨迹控制竞争同一个实时层。

### 鲁棒性、可复现性与风险

可复现性很高：PCB、固件和 FPGA solver 都公开。主要工程风险反而是硬件工具链、定点 / 混合精度、bitstream 和实时 I/O 验证；一旦 solver 数值路径被硬化到 FPGA，修改模型和约束的灵活性也比 CPU 版本低。

产品化时建议同时保留：

```text
FPGA MPC
  ↓
health / timeout / infeasible flag
  ↓
MCU deterministic fallback controller
```

FPGA 故障或 infeasible 不应该把飞行器一起带走。

### 适合谁关注

微型无人机、高速无人机、低功耗边缘控制、FPGA/SDR 背景团队，以及正在研究“算法如何真正落在机器人硬件上”的控制工程师。

### 工程落地启发

如果暂时不做 FPGA，也建议把控制软件 profiling 拆成：模型更新、矩阵构造、线性代数、ADMM iteration、I/O 五部分。只有确认瓶颈稳定、矩阵结构固定以后，硬件化才真正有价值。

[论文](https://arxiv.org/abs/2609.09380) · [FPGA Deck](https://github.com/A2R-Lab/Crazyflie_FPGA_Deck) · [ADMM FPGA](https://github.com/A2R-Lab/ADMM_FPGA) · [Crazyflie Firmware](https://github.com/A2R-Lab/crazyflie_fpga_firmware)

## 3. Actuator Dynamics Curriculum：有些 RL 任务不是奖励太稀疏，而是探索轨迹根本活不到获得奖励

**时间回补：arXiv v1 提交于 2026-09-08 22:14 UTC；CoRL 2026 接收。**

### 为什么重要

高动态腿式任务经常出现：reward 看起来合理、PPO 也稳定，但训练永远停在一个“不错却完成不了任务”的策略。

论文将其中一类问题解释为 **narrow viability**：真实执行器动力学下，大量随机初始动作会非常快地进入不可恢复状态，episode 在策略获得有效探索信号前就结束。

### 算法模块

作者没有改 reward，而是暂时改 simulator actuator dynamics：

```text
System-Identified Joint Dynamics
           ↓
训练初期提高 Stiffness
Damping 设为接近 Critical Damping
           ↓
扩大可行 / 可恢复区域
           ↓
Policy 开始学会任务结构
           ↓
根据 Episode Length / Success
逐渐 Anneal Stiffness
           ↓
最终回到真实辨识参数
```

Cart-pole 分析用于说明更高 closed-loop natural frequency 在临界阻尼附近可以扩大 viability kernel；腿式实验则在 Boston Dynamics Spot 上验证这一 curriculum。

### 动力学假设

这里有一条非常重要的边界：**curriculum 最后必须真正退回真实执行器。**

如果训练结束仍保留虚假的高刚度，策略学到的是一台不存在的机器人；sim-to-real 反而会更差。它也不保证所有“训练难”都可以通过 actuator curriculum 解决——有些任务确实是 reward、observation 或 policy representation 有问题。

### 实时性与真机结果

Spot 的 quadruped-to-handstand transition 中，固定系统辨识刚度的 baseline 会在约 400 step 的局部平台停住，即使持续训练也无法完成；curriculum 在 10 个随机种子中都完成任务，并将策略零样本部署到真机。

公开实验的硬件部分主要证明“能转移并完成动作”，并不是大规模统计型真机成功率 benchmark，因此不应把仿真 10-seed 结果直接当成硬件可靠性数字。

### 鲁棒性与工程风险

Actuator curriculum 相当于人为改变训练 MDP。任何这类方法都需要记录：

```text
training_dynamics_version
current_stiffness_scale
current_damping
anneal_progress
real_identified_parameter
```

否则 checkpoint 很容易在团队中被误用到与训练阶段不一致的 dynamics。

### 适合谁关注

四足、人形、动态翻滚/倒立、窄支撑域技能，以及“PPO 能学会走路，却始终学不会某个极端技能”的团队。

### 工程落地启发

在 Isaac Lab / MuJoCo 中可以先做一个最简单的 A/B：只改变 PD stiffness/damping curriculum，不改奖励；检查成功率、episode survival time 和策略最终回到真实参数时是否仍稳定。如果只有“软硬件不真实时”才能成功，这个 curriculum 就没有真正解决问题。

[论文](https://arxiv.org/abs/2609.09492)

## 4. Habit / Physics / Nuisance：世界模型迁移时，不应该为了新用户习惯重写物理

**时间回补：arXiv v1 提交于 2026-09-06 00:20 UTC。**

### 为什么重要

遥操作机器人数据天然多模态。同一个杯子可以从左抓、从右抓、快抓、慢抓；不同用户也有不同动作习惯。但在给定真实执行动作以后，下一时刻物理状态往往比“动作选择”本身确定得多。

如果 world model 直接学习：

```text
Observation + Command
→ Next Observation
```

它很容易把三种因素缠在一起：

```text
Habit      → 人为什么选这个动作
Physics    → 这个动作真正让世界怎样变化
Nuisance   → 相机 / 外观让世界看起来怎样
```

### 关键数学结构

作者明确写成结构因果形式：

```text
a = g(h, z, u)
z' = f(z, a)
o = r(z, c)
```

其中 `h` 是 operator habit，`z` 是物理状态，`u` 是任务 / 命令，`c` 是 camera / appearance nuisance。

然后使用干预做诊断：在同一状态下打乱 / 替换 action，真正的 physics predictor 应明显变差；仅改变外观和 camera，则物理 transition 不应该被大幅破坏。

### 迁移策略

论文主张迁移时：

```text
Shared Physics Readout
        → Freeze

Thin Interface / Habit Layer
        → Adapt
```

而不是遇到新操作者、新相机或少量 corrupted adaptation data 就 full finetune 整个 world model。

在 StackCube、DROID、RH20T 上，作者报告这种做法在 low-shot transfer 中优于 scratch，同时对 corrupted adaptation data 更不容易污染共享 dynamics。

### 传感器与模型假设

“physics”与“habit”不是天然可观的标签。数据必须包含足够的动作变化、用户变化或多视角变化，才能通过干预与泛化行为验证分解是否真的成立。

论文也明确没有把 latent action 简单等价为 operator habit，这一点很重要：latent action 可能同时吸收控制器、时延和未观测状态。

### 鲁棒性与风险

错误的 modularization 同样有风险。如果所谓“薄 interface”实际上不足以表达新 embodiment 或新接触模式，强行冻结 physics 会把真实动力学变化误当成用户习惯。

因此至少要有：

```text
physics_residual
habit_shift_score
appearance_shift_score
OOD / model-error test
```

来决定是只适配 interface，还是必须升级共享 dynamics。

### 适合谁关注

机器人世界模型、多用户遥操作数据、跨相机 / 跨操作者迁移，以及想做长期机器人数据平台的团队。

### 工程落地启发

训练数据的 metadata 不要只保存 `observation/action`，最好同时保存 `operator_id / embodiment_id / camera_id / calibration_version / task_id`。这些字段以后是判断 world model 到底在适配“谁”还是适配“物理”的关键证据。

[论文](https://arxiv.org/abs/2609.09210)

## 5. JEPA Policy：把未来当训练监督，而不是部署时必须生成的东西

**时间回补：arXiv v1 提交于 2026-09-09 02:42 UTC。**

### 为什么重要

Diffusion Policy 的多模态动作能力很强，但迭代 denoising 对端侧和高频控制并不友好。另一条路线是直接 action chunk prediction，但如果只监督 action，本体表征可能并没有被迫理解“这段动作会把世界带到哪里”。

JEPA Policy 把两者之间缺失的一环补上：

```text
Current Visual State
        ↓
Shared Transformer
       ↙ ↘
Action Chunk   Future Representation
       ↘ ↙
paired supervision
```

训练时既预测动作，也预测与该动作真实对应的 future representation；未来分支不是独立装饰 head，而是通过共享 token interaction 反过来塑造用于动作生成的表示。

### 算法模块

论文使用 action tokens 与 future-representation tokens 共用 Transformer，并进行两次 forward refinement；通过 dual-branch 与 gradient-routing 消融，作者试图证明收益来自共享拓扑，而不是简单“再加一个 auxiliary loss”。

这条路线最大的产品优势是：**部署时不需要迭代生成未来视频，也不需要几十 / 上百步 denoising。**

### 实时性与真机结果

九个仿真任务上，JEPA Policy 平均成功率高于 action-only MIP baseline，并在论文配置中超过 Diffusion Policy。额外模型延迟相对 MIP 只有约 **0.29 ms**。

完整模型平均约 **13.2 ms**、P95 约 **14.5 ms**，约可支撑 76 Hz 模型调用；对照的 100-step Diffusion Policy 在同一评测配置下约 **439.5 ms / 2.3 Hz**。

真机使用双臂 ARX-5、RTX 3090、三路 128×128 RGB；5 个任务总计 630 个 episode，整体 ranking 与仿真一致。

### 传感器与假设

future representation 的质量仍取决于数据覆盖。如果 demonstration 从未进入恢复状态，未来预测同样不会自动学会 recovery。

论文还发现 future-prediction error 含有 task-conditioned failure-ranking signal，这很有潜力，但它还不等于可校准的安全置信度。

### 鲁棒性、可复现性与风险

代码与项目页已经公开，可复现性较好。

工程上不要直接把 future error 当成“安全概率”，而应该先做 calibration：失败前是否稳定升高？不同物体、光照、相机域是否还能比较？

### 适合谁关注

需要 10–50 Hz 甚至更高 VLA / imitation policy、Jetson / 单 GPU 机器人，以及认为 diffusion latency 太高、又不想回到纯 action-only behavior cloning 的团队。

### 工程落地启发

现有 Action Chunking Policy 可以先不换架构，只增加一个训练期 future-latent head；部署时删掉或仅作为低频 health head 使用。先验证这个辅助监督是否能提高 OOD 与恢复能力，再决定是否迁移到完整 JEPA-style shared token 结构。

[论文](https://arxiv.org/abs/2609.09630) · [代码](https://github.com/jiejie567/JEPA-Policy) · [项目页](https://jiejie567.github.io/JEPA-Policy/)

## 6. What Symmetry Buys：先做坐标规范化，再考虑昂贵等变网络

**时间回补：arXiv v1 提交于 2026-09-09 11:05 UTC。**

### 为什么重要

学习式运动规划在 world frame 中训练时，会被迫反复学习本质完全相同的问题：

```text
同一障碍关系
只是在世界里平移 / 旋转了
```

最常见的解决方式是 data augmentation、equivariant network 或 inference-time group averaging。论文问了一个更基础的问题：start 与 goal 本身已经给出两个特殊点，能不能先用它们定义坐标系？

### Canonical Frame

构造极其简单：

```text
Origin = (start + goal) / 2
Primary Axis = normalize(goal - start)
```

再用一个叉积补齐坐标基，就能消除：

```text
3 个平移自由度
+
2 个旋转自由度
```

只剩绕 start-goal axis 的一个连续旋转无法用全局连续规则唯一固定。

### 结果为什么值得重视

保持模型、数据和训练预算不变：

```text
World-frame learned planner: 14.60% collision-free
Canonical frame:             51.10%
Straight-line baseline:      15.6%
```

也就是说，不做规范化的 learned planner 甚至没有真正超过直线基线。

而对剩余 1DoF 旋转尝试 data augmentation、inference operator、equivariant backbone 等机制，最终收益都不足 1 个百分点；equivariant backbone 的主要优势是更快达到同一水平，大约 2–3× sample-efficiency，而不是最终分数大幅上升。

更进一步，local geometry representation 的影响达到约 +40 points，比 symmetry frame 本身还大。

### 传感器与动力学假设

这项研究是 cluttered 3D motion planning benchmark，不是完整机器人闭环系统。它主要改变问题表征，并没有给出碰撞安全或动力学可执行性证书。

经典 TrajOpt / CHOMP / RRT-Connect 的 collision-free rate 在作者同一 benchmark 上仍显著更高，因此这篇论文不应被理解成“learning 已经替代 classical planning”。

### 鲁棒性与工程风险

Canonical frame 在 `start≈goal`、方向退化或某些对称环境中需要特殊处理；如果状态还包含 gravity、非完整约束、传感器视角等，不能盲目把所有坐标都旋转后认为任务完全等价。

### 适合谁关注

Neural motion planner、trajectory diffusion、VLA trajectory head、3D local planner，以及任何使用世界坐标训练轨迹网络的团队。

### 工程落地启发

训练新网络以前，先建立一张“对称性清单”：哪些自由度可以通过解析坐标变换完全消掉，哪些必须由网络学习，哪些因为重力 / 动力学根本不是对称的。**先把可解析的不变性从学习问题里删掉，通常比给网络增加复杂结构更划算。**

[论文](https://arxiv.org/abs/2609.10033)

## 7. CrossCoder：真实代码上下文的边界通常不在当前仓库

**时间回补：arXiv v1 提交于 2026-09-09 10:14 UTC；EMNLP Findings 2026 接收。**

### 突破性工程价值

仓库级 Coding Agent 很多失败并不是不懂目标 Repo，而是不懂**目标 Repo 当前锁定版本的外部 API**。

例如代码里使用某个旧版 ROS / npm / Python dependency，模型预训练知识记住的是最新版；只检索当前仓库根本找不到真实函数签名和行为。

CrossCoder 因此把 context graph 扩到仓库边界之外：

```text
Target Repository
       +
Dependency Libraries
       ↓
Unified Code Knowledge Graph
       ↓
Planning + Semantic Retrieval
       ↓
Important Nodes
       ↓
Selective Multi-hop Expansion
       ↓
Generation Context
```

它还建立 VersionExec，专门测试同一代码需求在不同 dependency version 下是否仍能生成正确实现。

### 结果与成本

论文报告 RepoExec、DevEval、VersionExec 都有改善，功能正确性最高提高约 **6.3% pass@1**。

更值得工程关注的是检索压缩：RepoExec 中平均候选节点从约 **9,914 → 23.5**，DevEval 从约 **7,020 → 26.5**，同时保持依赖召回。

但这种多跳图检索不是免费的。论文实验里 CrossCoder 的在线推理约 **21.56 s**，对照 Hydra 约 **14.28 s**；输入 / 输出 token 也更高。因此它更像“困难任务的深检索模式”，而不是所有补丁都默认开启。

### 是否适合真实研发流程

非常适合：

- monorepo + 多内部库；
- C++ / Java / TypeScript 大项目；
- 多版本 SDK；
- ROS / CUDA / Qt / Android API；
- 企业私有 package registry。

真正部署时，dependency graph 应来自 lockfile、build graph、package manager 和实际 checkout revision，而不是模型凭文本猜。

### 权限、安全与可验证性风险

跨仓库检索会扩大供应链攻击面。Agent 看到依赖库源码，不代表它有权修改依赖；看到 README 示例，也不代表示例适合当前版本。

建议 retrieval artifact 始终携带：

```text
repository
revision / version
license
source_path
symbol
retrieval_reason
```

生成器只消费 context，写权限仍由 capability system 独立控制。

### 工程落地启发

对于多机使用 Codex / Coding Agent 的团队，一个很实用的共享基础设施不是再建一个“大知识库”，而是建立**版本化代码图服务**：索引当前主仓 + lockfile 对应依赖 + 内部 SDK，并允许 Agent 按 symbol / call graph / dependency edge 检索。知识来源和 repo SHA 必须可追踪。

[论文](https://arxiv.org/abs/2609.09987)

## 8. If It’s Not Buggy, Don’t Fix It：自动修复系统必须拥有“停止修改”的能力

**时间回补：arXiv v1 提交于 2026-09-09 13:00 UTC。**

### 突破性工程价值

Coding Agent 最危险的循环之一不是“第一次修错”，而是：

```text
请继续检查还有没有 bug
        ↓
模型总能找到一个可疑点
        ↓
继续修改
        ↓
新的修改又制造新的可疑点
        ↓
继续修改……
```

论文专门研究 blind iterative bug-fixing，并发现模型会在**完全正确程序**上持续声称存在缺陷。

### Repair 与 Damage 必须同时统计

作者定义两类转移：

```text
α = P(next correct | current incorrect)
β = P(next incorrect | current correct)
```

也就是：

- `α`：真正修复错误程序的概率；
- `β`：把正确程序改坏的概率。

在多个设置中，`β` 明显高于 `α`。例如部分 Gemini Flash-Lite / structured repair 设置里，repair 只有个位数百分点，而 damage 可接近三成甚至更高；Qwen 的一些设置 damage 更严重。

这说明“多迭代几次总会更好”完全不成立。

### Pseudo-Bug-Fixing Cycle

长时间运行后，系统经常进入循环：

```text
Correct State
→ 模型误判 Bug
→ Patch A
→ Incorrect State
→ 下一轮认为 Patch A 有问题
→ 撤销 A
→ Correct State
→ 再次认为原代码有 Bug
```

同一修改反复出现、撤回，Agent 在工具层看起来非常忙，却没有产生任何净进展。

论文的 mechanistic probing 还找到一个与内部“buggy code”表示相关的 steering direction，提示 edit propensity 可能因为提示或上下文而被错误激活。

### 是否适合真实研发流程

这项结果直接支持一个原则：**自动修复必须 evidence-driven，而不是 activity-driven。**

允许修改代码的触发条件至少应该来自：

```text
Failing Test
Static Analyzer Finding
Runtime Exception / Trace
Explicit Requirement Change
Independent Reviewer Finding
```

如果没有新的失败证据，默认动作应该是 `ABSTAIN / STOP`，而不是“再优化一轮”。

### 权限、安全与可验证性风险

尤其不要让同一个 Agent 同时：

```text
决定代码有 Bug
修改代码
修改测试
宣布已经修好
```

生产 Harness 应记录每次编辑的 `evidence_id`。没有证据来源的 patch 应自动降级成人工 review，而不是自动 merge。

### 工程落地启发

长期 Coding Agent 可以增加一个极简单、却很有效的状态机：

```text
EVIDENCE_PRESENT
      ↓
PATCH
      ↓
VERIFY
   ├─ PASS + no new evidence → STOP
   └─ FAIL → new evidence required
```

并设置修改预算、同一区域反复 diff 检测和 cycle detector。**会拒绝继续改，是自治能力的一部分。**

[论文](https://arxiv.org/abs/2609.10123)

## 经典论文回顾

### LQR-Trees：把“可执行轨迹”升级成“带反馈吸引域的运动技能”

Russ Tedrake、Ian R. Manchester、Mark Tobenkin 与 John W. Roberts 的 **LQR-Trees: Feedback Motion Planning via Sums-of-Squares Verification** 于 2010 年发表于 *The International Journal of Robotics Research*。它是 feedback motion planning 的经典工作之一：规划结果不再只是一条开环曲线，而是“一条 nominal trajectory + 周围经过验证、能够被反馈控制收进来的状态漏斗”。（[论文 DOI](https://doi.org/10.1177/0278364910369189)）

### 核心问题

传统 kinodynamic planning 经常返回：

```text
x*(t), u*(t)
```

但真实机器人永远不会精确待在 `x*(t)` 上。状态估计误差、扰动和模型偏差会让它偏离轨迹。

如果规划器只回答“这条曲线理论上可行”，控制器再独立追踪，两者之间存在明显缝隙。

LQR-Trees 更关注：

> **哪些初始状态可以在反馈控制下被可靠吸入这条轨迹，并最终到达目标？**

### 算法模块

对于一条 nominal trajectory，先在其周围构造 time-varying LQR：

```text
Nominal Trajectory
       ↓
Linearize Dynamics Along Trajectory
       ↓
Time-Varying LQR
       ↓
Candidate Lyapunov Function
       ↓
Sum-of-Squares Verification
       ↓
Verified Region of Attraction
       ↓
Funnel
```

然后不断在尚未被现有 funnel 覆盖的状态中采样，生成新的轨迹与 funnel，最终形成一棵稀疏的“反馈轨迹树”。

在线运行时，机器人不必精确命中某条预计算轨迹起点；只要当前状态落入某个 verified funnel，就可以切换到对应反馈 controller。

### 关键数学思想

LQR 给出局部二次价值函数 / Lyapunov candidate，但只靠线性化不能保证非线性系统的真实吸引域。

原始 LQR-Trees 利用 **Sum-of-Squares（SOS）优化**对多项式系统和 Lyapunov 条件进行验证，寻找一个能够保证状态沿闭环动力学朝目标收敛的区域。

因此它不是：

```text
Trajectory Library
```

而是：

```text
Trajectory + Controller + Verified Funnel Library
```

### 动力学假设

经典 SOS 版本更适合能够用平滑 / 多项式形式表达或近似的低维非线性系统。状态维数增加以后，SOS / SDP 很快变得昂贵；强接触、离散模式切换和复杂障碍也会显著增加验证难度。

这正是后来 2016 年 **Simulation-based LQR-Trees** 尝试用仿真与 falsification 近似 funnel computation 的原因：牺牲一部分形式化严格性，换取更广泛的动力学与约束可用性。（[后续论文](https://doi.org/10.1177/0278364916647192)）

### 当年为什么重要

它把 Planning 与 Feedback Control 真正统一起来。

普通 motion planning 问：

```text
有没有一条路？
```

LQR-Trees 问：

```text
从这一片状态区域出发，
有没有一套反馈策略能把机器人可靠带到目标？
```

对欠驱动系统、快速动态系统而言，后一个问题明显更接近真实部署。

### 今天仍然在使用的思想

虽然今天不一定真的运行 SOS-LQR Trees，但它留下的几个思想非常现代：

1. **轨迹应该附带有效域。** 一个 controller / skill 不只输出动作，还应知道自己在哪些状态下可信。
2. **Recovery region 是规划资产。** Planner 不应该只储存 nominal path，还可以存“哪些偏差仍可恢复”。
3. **离线昂贵计算可以换在线极快决策。** 预计算 funnel / skill graph，运行时只做 membership 与切换。
4. **控制器的闭环性质应该进入 Planner，而不是规划后才考虑。**

### 已被后续替代的部分

今天的高维人形、四足和接触操作，很少直接使用原始 SOS funnel 全状态验证。现代替代 / 扩展包括：

```text
Reachability
Control Barrier Functions
Viability Kernel
MPC Terminal Set
Learned Safety Critic
Tube MPC
Simulation / Falsification
```

但这些工作本质上都在回答类似问题：**当前状态是否位于某个可安全恢复 / 可完成任务的集合中？**

### 可复现性

原始论文的核心依赖 SOS / SDP 工具，今天可以使用 Drake、SumOfSquares / SDP solver 或课程级实现重建小系统示例；同时 2016 年 simulation-based LQR-Trees 更容易在一般仿真器中实现。

需要注意，公开社区仓库更多是教学 / 复现项目，而不是一个可以直接塞进 ROS 2 的官方“LQR-Trees package”。因此它更适合作为控制架构思想复现，而不是直接依赖的产品库。

### 对当前机器人系统的重新解读

对于已有多个技能的四足 / 人形，可以把 LQR-Trees 的 Funnel 思想改写成：

```text
Skill {
  policy
  valid_state_region
  recoverable_region
  exit_condition
  fallback
}
```

例如楼梯模式、平地模式、转弯模式、跌倒恢复，不应该只由一个 `mode_id` 表示；还应该有“当前状态还在不在这个技能的可恢复区域”。

这和近期 Safe-Stop、Reachability Gate、Viability MPC 的趋势完全一致：**机器人真正需要的不只是动作生成器，而是对自身动作有效域的持续估计。**

[原始论文 DOI](https://doi.org/10.1177/0278364910369189) · [Simulation-based LQR-Trees](https://doi.org/10.1177/0278364916647192)

## 今日结论

今天最明确的 SLAM / 定位信号是：**全局纠漂不一定需要另一套重型 SLAM。** OSM lane correction 说明，只要局部 odometry 形状仍可信，一个非常稀疏、维护成本极低的公共几何先验就能承担长期 drift correction。对于大园区 / 城市级地面机器人，未来地图栈可以更清楚地分层：

```text
高频：LiDAR / Visual / Inertial Local Odometry
              ↓
低频：Sparse Public / Semantic Geometry
              ↓
全局一致性因子
```

而不是所有信息都压进一张永久维护的高精 3D 地图。

控制侧今天两条工作放在一起尤其有意思。AccelMPC 通过算法—数值—硬件共同设计把 MPC 推到 1 kHz；Actuator Curriculum 则说明训练阶段连“机器人动力学本身”都可以成为 curriculum 轴，但最终必须回到真实硬件参数。一个负责**让模型控制真正跑得足够快**，另一个负责**让策略在窄可行域里有机会学出来**。

机器人基础模型今天也出现相同的“职责拆分”。Habit/Physics/Nuisance 工作不希望 world model 用同一套权重吸收用户习惯、真实动力学和视觉外观；JEPA Policy 则把 future prediction 用作训练期结构监督，却不要求部署时持续运行昂贵生成过程。越来越多系统开始主动区分：

```text
什么应该成为共享长期知识？
什么只应该是轻量适配层？
什么只在训练期存在？
什么必须在运行时高频执行？
```

这比“把所有能力放进一个更大的模型”更接近机器人产品化。

学习式规划方面，symmetry 论文给出的教训非常值得长期保留：**先消除问题里免费的自由度，再让网络学习剩下的部分。** 在 canonical frame 都没做好以前，投入大量工程实现复杂 SE(3)-equivariant architecture，可能是在让网络解决本可解析消掉的问题。

AI Coding 侧的两条工作则共同改变 Agent 基础设施的边界。CrossCoder 说明正确代码上下文天然跨 repository / dependency version；Iterative Bug-fixing 工作说明修改行为本身也需要“可停止性”。长期 Coding Agent 因此应该同时拥有：

```text
Versioned Cross-Repo Context
Evidence-Grounded Edit Trigger
Independent Validation
Abstention / Stop Condition
```

一个真正成熟的 Agent 不是“永远还能继续做点什么”，而是知道什么时候该去查依赖、什么时候该改、什么时候证据不足应该停。

## 最值得深入研究或尝试复现的方向

1. **LIO + Sparse Map Drift Correction。** 保留现有 LIO-SAM / KISS-ICP，增加一个 1–2 Hz 的轨迹窗口对齐模块。先用 OSM 或自己画的走廊 / 道路中心线做 shadow correction，统计长距离 RPE、误匹配率、地图过期影响和 correction confidence，再决定是否写入因子图。

2. **执行器动力学 Curriculum A/B。** 在 Isaac Lab 四足 / 人形极限技能中，仅增加 stiffness+damping curriculum，不改 reward。强制最后 20–30% 训练完全回到真实辨识参数，比较 episode survival、任务成功率和真机 zero-shot，而不是只看训练峰值。

3. **JEPA Future Head for VLA。** 给现有 action-chunk policy 增加训练期 future-latent 预测，部署保持原 action path；同时记录 future-prediction error 是否能够提前区分失败 / OOD。若可以，再把它做成 runtime health signal，而不是先上完整视频 world model。

4. **Coding Agent 的“跨仓检索 + 停止修改”双 Gate。** Retrieval 层按 lockfile / build graph 索引真实版本依赖；Edit 层要求每个 patch 绑定 failing test、runtime trace、static finding 或明确 requirement。没有新 evidence 时 Agent 必须停止，且自动检测重复 diff / revert cycle。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)
- [Odometer-Agnostic Drift Correction Using OpenStreetMap Lane Geometry](https://arxiv.org/abs/2609.10336)
- [OSM Drift Correction 代码](https://github.com/Joaquinecc/icp_trajectory_alignment_osm)
- [AccelMPC](https://arxiv.org/abs/2609.09380)
- [Crazyflie FPGA Deck](https://github.com/A2R-Lab/Crazyflie_FPGA_Deck)
- [ADMM FPGA](https://github.com/A2R-Lab/ADMM_FPGA)
- [Actuator Dynamics Curricula for Narrow-Viability Tasks in Legged Robot Learning](https://arxiv.org/abs/2609.09492)
- [Identifying Habit, Physics, and Nuisance in Robot World Models](https://arxiv.org/abs/2609.09210)
- [JEPA Policy](https://arxiv.org/abs/2609.09630)
- [JEPA Policy 代码](https://github.com/jiejie567/JEPA-Policy)
- [What Symmetry Buys a Learned Motion Planner](https://arxiv.org/abs/2609.10033)
- [Beyond Repository Boundaries / CrossCoder](https://arxiv.org/abs/2609.09987)
- [If It’s Not Buggy, Don’t Fix It](https://arxiv.org/abs/2609.10123)
- [LQR-Trees](https://doi.org/10.1177/0278364910369189)
- [Simulation-based LQR-Trees](https://doi.org/10.1177/0278364916647192)
