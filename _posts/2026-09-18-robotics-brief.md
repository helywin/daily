---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-18"
date: 2026-09-18 09:00:00 +0800
description: "9 月 18 日新公开批次聚焦公里级分层 SLAM、动态场景 LIVO、等变水下惯导、可行腿式 MPC、黑盒 Reach-Avoid-Stay 安全、MPC 引导视觉策略学习、轻量机器人记忆与 Coding Agent harness 实证。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-18

## 摘要

今天早间首版生成时，arXiv Robotics 的最新公开批次仍停留在 9 月 17 日，因此首版从上一批次向下补充了 rMuscle、CaSCo、Multi-Robot TAMP、DynoFluxBench、VLM-MPPI、KINO、PASSAGE 等未覆盖工作。随后 **2026-09-18 新公开批次已经刷新**：Robotics 当天有 133 条，Software Engineering 当天有 24 条。本版重新检索并与 `robotics-brief-covered-items.md` 做强制去重；早间首版条目保留在覆盖索引中作为历史记录，但正文换成新批次中优先级更高的 8 条工作。最新列表见 [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) 与 [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent?show=2000&skip=0)。

今天 SLAM 侧最值得优先看的工作是 **AMB3R-SLAM**。它针对当前神经/学习式单目 SLAM 很难同时满足“大场景、动态环境、实时后端”的问题，将低延迟 tracking 与分层 backend 解耦，用 span-2、long-context 和 loop-closure edges 逐级建立局部、中程和全局一致性，避免依赖静态世界假设的 bundle adjustment。论文在单张消费级 GPU 上处理 10k+ 帧、公里级轨迹，并在 9 个数据集上验证；VBR 和 Oxford Spires 上相对此前 SOTA 的 ATE 降低超过 70%，额外输入 LiDAR 时在 KITTI/VBR 上进入亚米级。([论文](https://arxiv.org/abs/2609.19518)，[项目页](https://hengyiwang.github.io/projects/amber-slam)，[代码仓库](https://github.com/HengyiWang/amb3r-slam))

另一条和实际巡检环境更直接相关的是 **Dynamic-LIVO**。它使用 Spatio-Temporal Normal 识别动态 LiDAR 点，并把同一动态分类传播到 LiDAR-inertial 与 visual-inertial update，避免动态点及其关联图像观测同时污染状态估计和彩色地图。对新区域或稀疏区域，作者不急于立刻二分类，而是使用 time-delayed S-T normal estimation，等后续观测补足后再决定，这个“证据不足就延迟裁决”的设计比一帧式动态剔除更适合长期建图。([论文](https://arxiv.org/abs/2609.19336))

状态估计侧，**Equivariant Filter Design for Acoustic and Depth Aided INS** 很值得水下和多传感器滤波团队读。现有 IEKF 常把 IMU bias 当 Euclidean appendage，破坏原本期望的 group-affine 误差结构；这篇工作使用 Tangent-Group symmetry 把 bias 一起纳入几何状态，导航状态保留零线性化误差、bias 只留下二阶误差，并为 DVL 构造等变输出模型。Monte Carlo 中，姿态、速度、位置误差相对 Two-Frame-Group IEKF 和 MEKF 均降低 18–25%，ANEES 更接近 1；AUV 实测数据离线分析也显示更低位置漂移。([论文](https://arxiv.org/abs/2609.19742))

控制侧，**DR-MPC** 的目标不是再做一个更复杂的腿式动力学优化，而是把在线“可求解性”做进问题结构：将 dynamics equality 和 affine input constraints 转成 quadratic penalties，仅保留永远非空的 box constraints，再利用 block-arrow Hessian 和 Schur complement 做结构化消元。相同 DR-MPC formulation 下，专用 solver 相对 HPIPM / OSQP 的 median end-to-end speedup 为 16.0× / 4.4×，Unitree Go1 机载 median MPC 时间 4.4 ms。([论文](https://arxiv.org/abs/2609.20035))

安全控制方面，**Winning a Won Game** 把经典“reach-avoid”进一步扩展为 **strict Reach-Avoid-Stay（sRAS）**：机器人不仅要安全到达目标，还要在第一次到达以后永久维持目标集合内安全。作者将 stay value 与 reach-avoid value 组合成 robust discrete-time CBF，再提升到 state-action Q function；合成和部署都不要求已知动力学、affine structure、value derivatives 或人工 barrier。近似值函数通过 reachability-based adversarial RL 从 black-box interaction 学习，并在四足 gap jumping 真机和 F1TENTH 超车/守位中验证。([论文](https://arxiv.org/abs/2609.19449))

机器人学习侧，**Sampling-Guided Policy Search（SGPS）** 把 sampling-based MPC 当作训练过程里的“反复修正器”，而不是一次 imitation teacher。先用 MPC sampled action 做 BC 初始化，然后在 perturbed initial states 和 randomized dynamics 下交替进行 sampling refinement 与 short-horizon first-order policy-gradient update；视觉训练时把 rendering 从微分图里拆出去，因此可以直接从 depth 学，而不需要额外 state-policy teacher。单 GPU 训练覆盖 Go2 / G1 的 locomotion、越障、推箱和双臂搬运，最终策略 zero-shot 部署到真实 Go2，用机载 depth 完成 trot、crawl、跨栏和行为切换。([论文](https://arxiv.org/abs/2609.20575))

长期机器人记忆方面，**Workspace Models** 给出了一条很实用的“训练时用大模型，部署时删掉大模型”路线。训练阶段让 VLM 判断当前与历史中真正和任务有关的信息，再把这些 salient elements 蒸馏进一个轻量 **workspace token**；部署时 policy 直接查询这个 token，不需要 VLM in-the-loop。论文在仿真和硬件上都显示，这个 token 不只是更便宜，在记忆密集任务中还可以比直接条件于完整历史得到更好的 policy performance。([论文](https://arxiv.org/abs/2609.20820))

AI Coding 侧今天最值得看的不是单一 Agent 新分数，而是 **An Empirical Study of Harness Design for Coding Agents**。作者固定 Agent execution loop，只改变 planning、action space、context management，在 4 个模型、SWE-Bench Verified 与 Terminal-Bench 2.1 上形成 176 个 matched settings。结论很具体：context window 越紧，context management 越重要，主要收益来自防止 overflow；“先规则删除、再 LLM 总结”是整体效率最好的上下文策略；把被删除内容做成可恢复机制增加了复杂度但没有带来 accuracy gain；planning 对弱模型更多是准确率 scaffold，对强模型更多是 cost saver；而 bash 能力强的模型可以用 bash-only interface 以更低成本完成命令行型任务。([论文](https://arxiv.org/abs/2609.20804))

近期通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic、Google DeepMind 的官方发布入口，没有发现 9 月 18 日需要新增报道的通用旗舰正式发布；Claude Fable 5.1、Gemini 3.8 Audio、GPT-6 Astra 等近期重要更新均已在前几期覆盖，因此今天不重复。

## 1. AMB3R-SLAM：公里级实时 SLAM 的关键不只是前端更强，而是后端要有“层级时间尺度”

**最新 9 月 18 日公开批次；v1 提交于 2026-09-17 00:11 UTC。**

### 为什么重要

很多现代单目 SLAM 系统在短序列上效果很好，但轨迹拉到公里级以后会同时遇到三个压力：

```text
高频 tracking 必须低延迟
        +
中程漂移需要不断校正
        +
全局 loop closure / consistency 需要看很长历史
```

如果所有优化都放进同一个全局 BA，计算会随关键帧不断增长；如果只做局部窗口，长程一致性又很难维持。动态场景还会进一步破坏依赖 static-world residual 的全局优化。

AMB3R-SLAM 的核心不是“再加一个更大的网络”，而是把后端拆成不同跨度的图约束。

### 算法模块

官方项目页给出的结构可以概括为：

```text
Input images
    ↓
Lightweight Front-end
低延迟 camera tracking
    ↓
Hierarchical Backend
  ├─ span-2 edges
  │   维持局部连续一致性
  ├─ long-context edges
  │   修正中长程漂移
  └─ loop-closure edges
      建立全局一致性
    ↓
Pose Graph Optimization
```

这里最值得注意的是：**全局一致性不是通过“越来越大的静态世界 BA”实现，而是通过不同时间尺度的 pose-graph relations 逐级建立。**

这种结构天然更接近长期机器人系统：高频层必须稳定、低延迟；低频层可以更昂贵，但不能阻塞 tracking。

### 传感器与地图假设

基础系统是 monocular，但论文同时展示了 stereo、RGB-D、LiDAR 作为额外输入的扩展。

单目模式仍然面对尺度、弱纹理、曝光、motion blur 等经典问题。论文“dynamic scenes out of the box”的前提是其 backend 避免静态世界 BA 依赖，并不意味着任何大规模运动目标都不会影响 front-end matching / pose relation。

### 实时性与结果

论文报告：

- 单张 consumer-grade GPU；
- 超过 10k 帧；
- kilometer-scale trajectory；
- 9 个数据集；
- VBR 与 Oxford Spires 上相对此前 SOTA ATE 降低超过 70%；
- 加 LiDAR 输入后，KITTI 与 VBR 达到 sub-meter ATE。

这些结果说明层级 backend 的 scaling 思路有价值，但工程复现还应该额外记录：

```text
front-end P50 / P95 latency
local-edge queue depth
long-context update latency
loop-closure optimization pause
GPU memory vs trajectory length
```

因为“平均实时”不代表长 loop closure 到来时没有 latency spike。

### 鲁棒性与可复现性

项目页与 GitHub 仓库已经公开，但截至今天仓库仍非常早期，主要是 README / 项目入口；因此应把它理解为**官方代码入口已存在**，而不是已经可以一键完整复现全部论文结果。

### 工程风险

层级 backend 会产生一个新的系统问题：不同层级可能对同一历史 pose 给出不同版本。

如果上层语义地图、任务点、导航路径直接缓存某一版 global pose，就会重现前几天 P-POSEMEM / SEAM 暴露的问题。

因此建议所有上层数据绑定稳定 identity / submap / keyframe reference，而不是永久复制 `map_xyz`。

### 适合谁关注

大尺度视觉 SLAM、长期巡检、神经 SLAM、多模态 SLAM、需要把局部实时和全局一致性分层的系统。

### 工程落地启发

即使继续使用 ORB-SLAM3 / LIO-SAM，也可以直接借鉴“层级后端”思想：

```text
高频：local odometry
中频：local/submap optimization
低频：long-range loop / global graph
```

每层都定义独立预算与异步队列，不要让全局闭环偶发计算峰值反向拖死实时 tracking。

[论文](https://arxiv.org/abs/2609.19518) · [项目页](https://hengyiwang.github.io/projects/amber-slam) · [代码仓库](https://github.com/HengyiWang/amb3r-slam)

## 2. Dynamic-LIVO：动态点“证据不够”时，先延迟判断，而不是急着删

**最新 9 月 18 日公开批次；v1 提交于 2026-09-16 19:04 UTC。**

### 为什么重要

动态环境中的 LIVO 很容易出现一种跨模态污染：

```text
移动的人 / 车
   ↓
LiDAR 点进入 scan-to-map residual
   +
图像 feature 也落在同一动态物体
   ↓
LiDAR update 与 visual update
同时把错误信息写进状态
   ↓
地图出现拖影 / 状态估计偏移
```

很多方法只在 LiDAR 端做 dynamic filtering，却仍允许相关视觉 feature 进入后续优化。

Dynamic-LIVO 的设计更完整：一个动态判断同时约束 LiDAR 和视觉两个更新通道。

### 算法模块

```text
LiDAR temporal observations
        ↓
Spatio-Temporal Normal Analysis
        ↓
static / dynamic evidence
        ↓
┌─────────────────────────────┐
│ LiDAR-inertial update       │
│ Visual-inertial update      │
│ Colored map construction    │
└─────────────────────────────┘
```

对“刚看见的区域”或“点太稀”的情况，S-T normal 本身不可靠。

论文因此增加：

```text
insufficient observations
        ↓
defer classification
        ↓
collect later observations
        ↓
re-evaluate S-T normal
        ↓
then decide static / dynamic
```

这点很重要：**unknown ≠ dynamic**。

### 传感器与假设

系统依赖 LiDAR + IMU + camera，并利用时空重复观测判断几何是否持续稳定。

如果机器人速度很快，一个动态目标只短暂进入视场，或者扫描稀疏到根本没有足够 temporal support，delay strategy 可能需要在“等待更多证据”和“不要让可疑观测污染 estimator”之间做权衡。

### 鲁棒性与结果

论文在公共与自采数据、不同 sensor configurations 上验证，报告更高定位精度和更干净的 static colored map。

但当前 source code 和自采 dataset 明确写的是 **upon acceptance release**，所以现阶段不可把它评价为已经完整开源。

### 工程风险

时间延迟分类会引入“暂存观测”的数据生命周期问题。

建议每个点 / feature 至少有：

```text
classification_state:
  static | dynamic | pending

support_count
temporal_span
normal_confidence
associated_visual_features
```

`pending` 状态不应直接进入永久地图，也不应简单当作 dynamic 删除。

### 适合谁关注

城市 / 工厂动态 LIVO、彩色点云建图、巡检机器人、多传感器动态剔除。

### 工程落地启发

即使不复现 S-T normal，也可以先把现有动态剔除器从二元接口：

```text
static / dynamic
```

升级为：

```text
static / dynamic / uncertain
```

让 `uncertain` 进入短期缓存，后续观测足够以后再决定是否写入长期地图。这通常比提高一次性动态分割网络准确率更容易带来地图稳定性收益。

[论文](https://arxiv.org/abs/2609.19336)

## 3. Tangent-Group EqF：IMU Bias 不应该只是“挂在 Lie Group 旁边的欧氏变量”

**最新 9 月 18 日公开批次；v1 提交于 2026-09-17 06:09 UTC；投稿 ICRA 2027。**

### 为什么重要

IEKF 的核心优势来自几何误差结构：当系统具有合适 group-affine structure 时，误差动力学对 estimate 的依赖可以大幅减少，线性化更一致。

但真实 inertial navigation 还必须估计：

```text
gyro bias
accelerometer bias
```

常见做法是把 bias 作为一个 Euclidean block 直接 append 到 Lie-group state 后面。这样实现方便，却会破坏严格的 group-affine 结构，也会让 covariance consistency 逐渐变差。

### 数学结构

这篇工作使用 **Tangent-Group (TG) symmetry**，把 bias 一起纳入状态空间几何。

结果是：

```text
navigation states
→ zero linearization error

bias states
→ only second-order error
```

同时，作者为 DVL velocity 构造 equivariant output model，其 update 只有 third-order linearization error；pressure depth 则使用直接输出。

最终融合链可以写成：

```text
IMU propagation
      ↓
TG-Equivariant State
      ↓
DVL equivariant velocity update
      +
pressure depth update
      ↓
consistent navigation posterior
```

### 传感器与假设

场景是 GPS-denied AUV，主要传感器：

- IMU；
- acoustic DVL；
- pressure-derived depth。

它并不处理 DVL 全面失锁、海流模型错误、声速异常等所有水下问题，但给出了一个更一致的滤波底座。

### 结果

Monte Carlo 中，相对 Two-Frame-Group IEKF 与 Multiplicative EKF：

```text
attitude / velocity / position error
↓ 18–25%
```

更值得关注的是 ANEES：TG-EqF 更接近理想值 1，意味着 reported covariance 和实际误差更一致。

AUV field data 的 offline analysis 也显示 position drift 降低。

### 实时性与工程风险

论文是 filter，而不是大规模 batch optimizer，理论上非常适合嵌入式在线状态估计。

但当前 field evidence 是**离线重放实测数据**，不是已经证明在 AUV 主控上长期实时运行。工程部署仍需测：

```text
update latency
numerical conditioning
DVL dropout recovery
bias convergence
ANEES / NIS over long missions
```

### 适合谁关注

水下 AUV、Invariant EKF、Lie-group state estimation、多传感器惯性融合。

### 工程落地启发

更普遍的启示是：如果状态里有“辅助变量”长期影响主状态，不要默认它们放在欧氏尾巴里就没有代价。

在轮式/腿式融合中，外参、bias、scale、time offset 等变量是否破坏原本的 invariant structure，值得在估计器设计阶段明确检查。

[论文](https://arxiv.org/abs/2609.19742)

## 4. DR-MPC：实时 MPC 的第一目标有时不是“模型更精确”，而是“每一拍都能快速给出可用解”

**最新 9 月 18 日公开批次；v1 提交于 2026-09-17 10:38 UTC。**

### 为什么重要

腿式 MPC 常见难点是同时存在：

```text
nonlinear / linearized dynamics
contact switching
swing force = 0
friction / input constraints
high control frequency
```

传统做法将大量约束作为 equality / inequality 硬塞进 QP，接触模式一变，问题结构和可行域也跟着变化。

DR-MPC 选择主动放松部分模型约束，使最终在线问题只留下**天然非空的 box constraints**。

### 算法模块

论文将：

```text
dynamics equality
affine input constraints
```

移入 quadratic penalty，而不是继续作为 hard constraints。

然后利用 contact-aware input parameterization，把 swing-force elimination 和 contact-aligned move blocking 写入结构。

最终 QP 的 Hessian 呈 block-arrow 结构：

```text
states / affine outputs
        ↓ Schur complement elimination
reduced control system
        ↓ factorization
control solution
```

### 实时性

相同 DR-MPC formulation 下：

- 相对 HPIPM median end-to-end speedup：**16.0×**；
- 相对 OSQP：**4.4×**；
- Unitree Go1 onboard median MPC end-to-end：**4.4 ms**；
- locomotion performance 在仿真中保持可比；
- 有真实 Go1 验证。

这是今天最明确的“可以放进高频腿式控制 loop”的数字之一。

### 动力学假设与风险

这里要非常准确地区分：

> **优化问题可行**，不等于**机器人真实动力学约束一定被严格满足**。

因为 dynamics equality 已进入 penalty，如果 penalty 权重、线性化误差或 model mismatch 处理不当，solver 可以用一定 dynamics residual 换取更低总 cost。

因此上线时应把：

```text
dynamics_residual
affine_constraint_residual
contact_force_margin
box_constraint_margin
```

作为 runtime telemetry，而不能只看 solver status。

### 可复现性

论文写明开源代码将在 publication 后提供，因此今天暂时不能按“已有代码”评分。

### 适合谁关注

四足 / 人形 MPC、whole-body QP、接触切换控制、需要 100–200 Hz 以上在线优化的团队。

### 工程落地启发

现有 MPC 可以先做离线实验：逐渐将最容易导致 infeasible / expensive factorization 的约束从 hard equality 转成高权重 penalty，画出：

```text
solve time
vs
constraint residual
vs
tracking performance
```

找到真正的工程 Pareto，而不是默认“所有模型等式都必须作为硬约束”。

[论文](https://arxiv.org/abs/2609.20035)

## 5. Strict Reach-Avoid-Stay CBF：安全不是“到达目标前别出事”，到达以后也必须守得住

**最新 9 月 18 日公开批次；v1 提交于 2026-09-16 21:32 UTC。**

### 为什么重要

很多 reach-avoid formulation 关注：

```text
安全地到达 Goal
```

但机器人真实任务常常要求：

```text
安全到达
+
到达以后持续留在安全目标集合
```

例如：

- 四足跳过缝隙以后必须稳定落地，不是“脚碰到对岸”就算成功；
- 赛车超车以后必须保持领先和赛道安全；
- 机械臂到达插入位置以后必须保持接触稳定。

这篇工作将这种要求 formalize 为 **strict Reach-Avoid-Stay (sRAS)**。

### 算法模块

作者构造两个 value：

```text
Stay Value
→ 哪些目标状态可以永久安全停留

Reach-Avoid Value
→ 哪些状态可以安全到达
   那些“可永久停留”的目标子集
```

二者组合成 robust discrete-time CBF，再提升成 state-action **Q-CBF**：

```text
Black-box State
     ↓
Nominal Action
     ↓
sRAS Q-CBF
     ↓
safe / intervene
     ↓
Executed Action
```

### 最特别的地方：不要求已知动力学

合成 / 部署均不需要：

- known dynamics；
- control-affine structure；
- value derivatives；
- hand-designed barrier。

作者使用 reachability-based adversarial RL，仅通过 black-box interactions 近似 value。

### 理论保证与现实边界

对**精确 value**，在论文的 measure-zero condition 下，filter 对几乎所有 winnable initial states 保留 sRAS feasibility，并对所有允许的不确定性保持目标内安全。

但真机部署使用的是**近似 value**。

这意味着工程系统不能把理论 exact-value guarantee 无条件复制到神经近似上。应该额外测：

```text
value approximation error
OOD state coverage
intervention frequency
post-target invariant violations
```

### 真机

论文包含 quadruped gap jumping hardware：

```text
jump
→ cross gap
→ land
→ remain safe
```

同时在 simulated F1TENTH 上展示安全超车与 lead retention。

### 适合谁关注

Safe RL、CBF safety filter、四足跳跃、目标集合保持、black-box dynamics。

### 工程落地启发

对机器人任务定义，不要只保存：

```text
success_condition
```

更完整的是：

```text
reach_condition
avoid_condition
stay_condition
```

尤其是楼梯落平台、无人机停靠、机械接触这些任务，`stay_condition` 往往才决定系统是不是真的完成任务。

[论文](https://arxiv.org/abs/2609.19449)

## 6. SGPS：Sampling MPC 不只是 Teacher，它可以在训练过程中不断纠正 Policy 的接触模式

**最新 9 月 18 日公开批次；v1 提交于 2026-09-17 15:33 UTC。**

### 为什么重要

可微仿真 + first-order policy gradient 的优势是 GPU 训练成本低，但局部梯度很容易收敛到“数学上能降低 loss、物理上却很别扭”的接触模式。

例如越障时，policy 可能找到一种局部可行但脆弱的蹭障碍方式。

Sampling MPC 的优势正相反：不依赖局部梯度，可以通过 rollout 跳出当前局部 basin，但单独长期在线跑又比较昂贵。

SGPS 将二者交替使用。

### 训练流程

```text
Sampling MPC
→ 找更好的 action target
        ↓
Behavior Cloning initialization
        ↓
First-order Policy Gradient
        ↓
Perturbed initial states
+ randomized dynamics
        ↓
再次 Sampling MPC refinement
        ↓
短 horizon FoPG
        ↺
```

也就是说，MPC 不是只在 dataset 初始化阶段出现一次，而是周期性纠正 policy 的训练目标。

### 视觉训练

视觉 policy 使用 depth observation。

作者特别把 rendering 从 differentiable computation graph 中解耦，因此不需要让 renderer 本身参与梯度传播，也不需要额外训练一个 state-policy teacher。

这降低了视觉 policy training 的 GPU memory / computation pressure。

### 结果与真机

单 GPU 训练覆盖：

- Unitree Go2 locomotion；
- obstacle traversal；
- crate pushing；
- G1 bimanual carrying。

最终 policy zero-shot 到真实 Go2，用 onboard depth 完成：

```text
trot
crawl
clear hurdles
switch behaviors
```

### 风险

Sampling MPC 的 proposal quality 依赖 model / simulator。

如果 MPC 在仿真里偏好一种真实硬件上不可执行的 contact mode，后续 policy 反而会把错误 teacher target 学得很稳定。

因此应同时进行：

```text
MPC target quality check
sim randomization
hardware constraint audit
policy-only rollout
```

### 适合谁关注

Isaac Lab / 可微仿真、四足 / 人形训练、MPC + RL、希望减少大规模 end-to-end RL trial 的团队。

### 工程落地启发

如果已经有一个“能跑但不够灵活”的 sampling MPC，不必只拿它生成一次 offline demonstration。

可以把它改成**周期性 policy repair source**：当训练 loss plateau、失败模式集中或 curriculum 升级时，再调用 MPC 生成更好的局部 action target。

[论文](https://arxiv.org/abs/2609.20575)

## 7. Workspace Models：长时记忆可以在训练时请 VLM 做“老师”，部署时只留下一个小 Token

**最新 9 月 18 日公开批次；v1 提交于 2026-09-17 17:59 UTC；CoRL 2026。**

### 为什么重要

长时机器人任务需要记住过去：

```text
哪个抽屉已经打开？
工具之前放在哪里？
哪一步已经完成？
刚刚哪个物体被移动？
```

最直接的方法是把完整 history 都喂给 policy。

问题是：

```text
history 越长
→ compute 越高
→ spurious correlation 越多
→ policy 反而可能变差
```

另一条路线是在运行时反复问 VLM：“历史里现在真正重要的是什么？”但这会把延迟和成本永久放进控制 loop。

Workspace Models 选择在训练时完成这件事。

### 训练结构

```text
Current + Historical Observations
            ↓
Training-time VLM
识别 task-salient information
            ↓
Set-Reconstruction Supervision
            ↓
Workspace Token
轻量 latent memory
            ↓
Policy
```

训练完成后：

```text
部署：
Observation + Workspace Token
        ↓
Policy

不再需要 VLM in-the-loop
```

### 为什么值得关注

这和“蒸馏一个 VLM”并不完全一样。

蒸馏目标不是复刻 VLM 的所有语言/视觉能力，而是只保留：

> **当前任务真正需要从历史中取出的信息集合。**

因此 memory capacity 是 task-shaped 的。

### 结果

论文在 simulation 与 hardware 中验证，workspace token 可以作为 observation 的 drop-in memory representation，支持 memory-intensive task。

作者还观察到：它不仅更 lightweight，而且 policy performance 反而更好，说明完整 history 中的多余信息确实可能伤害决策。

### 风险

训练时 VLM 的 saliency judgment 会变成 memory supervision。

如果 VLM 系统性忽略某类低频但关键事件，例如：

```text
一次短暂碰撞
一个只出现一帧的工具
某个安全状态改变
```

workspace token 也可能永远学不会保留它。

安全关键 memory 不应完全交给 learned saliency，应保留 deterministic state / event log。

### 适合谁关注

长时操作、机器人 memory、VLA orchestration、边缘端 policy、希望把大模型移出实时 loop 的团队。

### 工程落地启发

可以把机器人 memory 拆成两层：

```text
Hard Memory
→ task phase / safety / irreversible event
→ deterministic

Soft Workspace Memory
→ scene details / object history / contextual cues
→ learned latent
```

这样既降低长 history 成本，又不让不可丢失的信息依赖一个隐式 token。

[论文](https://arxiv.org/abs/2609.20820)

## 8. Coding Agent Harness 实证：先删无价值上下文，再总结；强模型未必需要一堆专用 Tools

**最新 9 月 18 日 Software Engineering 批次；v1 提交于 2026-09-17 17:58 UTC。**

### 突破性工程价值

Coding Agent 的表现越来越取决于 harness：

```text
Planning
Context Management
Action / Tool Space
Execution Loop
```

问题是大家常把 harness 当整体比较：

```text
Claude Code vs Codex vs 自研 Agent
```

这样很难知道到底是模型、Prompt、上下文策略还是 Tools 起作用。

这篇论文固定 execution loop，只改变三个可控组件：

- planning；
- action space；
- context management。

因此更接近真正的工程消融。

### 实验规模

作者在：

- 4 个模型；
- SWE-Bench Verified；
- Terminal-Bench 2.1；
- 176 个 matched settings；
- 5 种 context-management strategies；
- 4 种 context-window budgets；

上做对照。

### 结论 1：上下文管理首先是在防止“爆窗”

论文发现，context window 越紧，context management 越重要；它主要的收益不是让 Agent “思路突然更聪明”，而是：

> **让 trajectory 不因为 context overflow 提前死亡。**

这解释了为什么长任务里“能继续工作”本身就是一项重要 harness 能力。

### 结论 2：Rule-based Elision → LLM Summary 更划算

总体最有效率的策略是：

```text
先机械删除
明确无价值 / 可重建内容
        ↓
再让 LLM 总结
真正需要压缩的内容
```

而不是所有历史都先交给 LLM summarizer。

更有意思的是，“把已经 elide 的内容做成可恢复机制”增加了 machinery，但模型很少主动使用，最终没有 accuracy gain。

这对复杂 memory system 是一个很好的反过度工程提醒。

### 结论 3：Planning 对不同模型的作用不同

弱一些的模型：

```text
Planning
→ accuracy scaffold
```

强模型：

```text
Planning
→ 主要减少成本 / 早停错误路径
→ accuracy 改变不大
```

因此没有必要把“必须先输出长 Plan”当成所有模型永久不变的最佳实践。

### 结论 4：Tool 越多不一定越强

论文观察到：

- bash 能力较弱的模型受益于 predefined tools；
- bash-capable model 用 bash-only interface 也能很好工作；
- 在 command-line-centric tasks 上，bash-only 往往明显更便宜。

这意味着 Tool 设计应该**model-aware**，不是工具数量竞赛。

### 是否适合真实研发流程

非常适合。

我会把它转成一个实际 harness policy：

```text
Context:
  deterministic elision first
  summarization second

Planning:
  根据模型 / 任务动态启用
  不强制超长 plan

Tools:
  bash-capable model
  → 默认少而通用

  weak shell model
  → 提供 typed tools
```

### 风险与可验证性

SWE-Bench / Terminal-Bench 仍然不能代表所有大型企业仓库。

而且 bash-only 对权限治理要求更高：模型能力越强、工具越通用，capability boundary 越要在模型外部做 sandbox、network、filesystem policy。

### 工程落地启发

如果正在自研 Coding Agent，不要一上来做复杂 memory / tool ecosystem。

先固定模型与 task，做三个最小 A/B：

```text
1. 无压缩 vs rule-elision vs elision+summary
2. planning on / off
3. typed tools vs restricted bash
```

记录：

```text
success
token
wall-clock
tool calls
overflow rate
human intervention
```

再决定哪些 harness 组件值得长期维护。

[论文](https://arxiv.org/abs/2609.20804)

## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### 1. 网络权限不要按 Session 开：按“这一条命令”临时放行域名

**来源：Claude Code v2.1.276，2026-09-18 官方 release。**

Claude Code 最新版本给 sandbox auto mode 的 Bash / PowerShell / Monitor 增加了 **per-command `allowed_domains`**：一条命令需要访问哪些 host，就随该命令一起审核和临时开放；其他 host 仍然拒绝。

这个功能背后的原则比具体产品更重要：

> **Coding Agent 的网络权限最好绑定到一次工具调用，而不是整个 Session。**

传统做法往往是：

```text
这个 Agent 需要 npm / GitHub / docs
→ 整个容器长期允许外网
```

更安全的是：

```text
npm install
→ 只允许 registry.npmjs.org

git fetch
→ 只允许 github.com

访问内部 API
→ 只允许指定内部 host
```

命令结束后权限随之消失。

**今天怎么用：**即使你不是 Claude Code，也可以在自己的 Agent sandbox 里让每次 network tool call 返回：

```text
command
allowed_hosts
ttl
reason
```

然后由执行器而不是模型 enforce。

**边界：**域名 allowlist 不等于内容安全。一个被允许的 GitHub / package registry 仍然可能承载恶意内容；它解决的是网络最小权限，不是供应链验证。

[Claude Code Releases](https://github.com/anthropics/claude-code/releases)

### 2. 安装 Plugin 时不要批准“下一条命令”：批准它的 SHA-256

**来源：Claude Code v2.1.276，2026-09-18 官方 release。**

同一版本新增：

```text
claude plugin install --accept-command <sha256>
claude plugin update  --accept-command <sha256>
```

它允许先用 JSON 模式看到**确切将被执行的安装命令**，再用该命令的 hash 做授权，而不是简单 `-y` 接受“现在 whatever command”。

这个模式非常适合所有 Agent 自动化：

```text
Plan
→ 生成具体 destructive / install command
→ hash exact payload
→ Human / policy approves hash
→ Execute only if hash unchanged
```

如果 Agent 在审批之后又修改了参数，hash 就不匹配，必须重新批准。

**为什么值得学：**它直接缩小了经典 TOCTOU：

```text
批准的是 A
真正执行时偷偷变成 A'
```

的问题。

**今天怎么用：**对 `npm install`、数据库 migration、远程部署、机器人软件升级这类高风险动作，保存：

```text
normalized_command
payload_hash
approved_by
approved_at
expires_at
```

执行器只接受 exact hash。

**边界：**hash 只能证明“执行的是已批准字节”，不能证明命令本身是安全的。批准前仍需 sandbox / dependency / blast-radius 检查。

[Claude Code Releases](https://github.com/anthropics/claude-code/releases)

### 3. Code Review Findings 应该有生命周期：NEW → OPEN → RESOLVED，而不是一堆静态评论

**来源：GitHub Copilot Code Review，2026-09-18 官方更新。**

GitHub 今天更新 Copilot code review：overview 会区分：

```text
Open
Resolved since last review
```

新 commit 引入的 finding 还会标记 `new`；系统会重新验证此前建议是否已经被修复，并在批量接受建议时生成更有意义的 commit message。

这里真正值得复制的是：

> **Agent Review 的输出应该是有状态的 defect ledger，而不是每次 review 重新生成一堆独立评论。**

**今天怎么用：**自研 Reviewer 可以把 finding 固化为：

```text
finding_id
introduced_revision
severity
evidence
status: NEW | OPEN | RESOLVED | REGRESSED
last_verified_revision
```

每个新 commit 只增量验证受影响 finding。

这样可以避免两个常见问题：

- Agent 反复评论已经修好的问题；
- 新改动把旧 bug 重新引入，但历史 review 没有状态关联。

**边界：**auto-resolve 仍然必须基于实际新 revision 的证据。不要因为开发者“回复已修复”就直接改成 RESOLVED。

[GitHub Changelog](https://github.blog/changelog/2026-09-18-copilot-code-review-an-improved-review-experience/)

## 经典论文回顾

### PTAM：现代 SLAM 的“快前端 + 慢后端”架构，2007 年就已经把关键原则说清楚了

Georg Klein 与 David Murray 的 **Parallel Tracking and Mapping for Small AR Workspaces（PTAM）** 发表于 **ISMAR 2007**，并获得 Best Paper Award。它最初是为小型 AR workspace 的手持单目相机设计，但对后续 Keyframe-based Visual SLAM 的系统架构影响极大。([Oxford 论文页](https://www.robots.ox.ac.uk/~lav/Papers/klein_murray_ismar2007/)，[DOI](https://doi.org/10.1109/ISMAR.2007.4538852))

### 核心问题

在 PTAM 之前，实时单目 SLAM 常把：

```text
相机定位
地图更新
```

放在同一个逐帧估计循环里。

这带来天然冲突：

```text
Tracking
→ 每帧必须快

Mapping / Optimization
→ 希望看更多关键帧
→ 希望做更昂贵的优化
```

PTAM 的核心突破不是新的 feature descriptor，而是把这两个时间尺度拆开。

### 系统架构

```text
Camera Frames
     ↓
Tracking Thread
→ 使用当前地图快速估计 pose
→ frame-rate
     ↓
挑选 Keyframe
     ↓
Mapping Thread
→ 三角化新点
→ 地图维护
→ Bundle Adjustment
```

两个线程并行运行。

于是 mapping 可以做当时看起来很“奢侈”的 batch optimization，而 tracking 不必等待它完成。

### 关键技术思想

PTAM 同时强化了几个后来几乎成为视觉 SLAM 常识的结构：

- **Keyframe-based mapping**：不是每帧都进入长期优化；
- **Tracking against a map**：前端利用地图，而不是只做 frame-to-frame VO；
- **Parallel tracking / mapping**：不同时间预算的任务拆开；
- **Bundle Adjustment as map refinement**：更重的几何优化放到后台；
- **Relocalization**：tracking 丢失后允许从地图恢复。

### 当年为什么重要

它证明了一件非常关键的事情：

> **“复杂后端优化”和“实时前端”并不矛盾，只要系统架构把它们解耦。**

2007 年还是 dual-core desktop 的时代，这种线程拆分就已经足够让数千 landmark 的地图与 frame-rate tracking 共存。

### 今天仍在使用的思想

现代 ORB-SLAM、VINS、很多 neural SLAM 虽然算法细节完全不同，但仍经常可以看到：

```text
Fast Tracking / Odometry
        ↓
Keyframes
        ↓
Local Mapping / Optimization
        ↓
Loop / Global Optimization
```

今天 AMB3R-SLAM 进一步将 backend 从“一个 mapping thread”细分成：

```text
local
mid-level
global
```

本质上是 PTAM 时间尺度解耦思想在公里级场景上的继续扩展。

### 已经被后续替代的部分

PTAM 原始系统针对 small AR workspace：

- 没有今天成熟的全局 loop-closure architecture；
- 单目初始化和尺度仍有局限；
- feature / matching / BA 实现属于 2007 年时代；
- 不具备现代 VIO、多地图 Atlas、稠密 / 语义地图能力。

今天更常使用 ORB-SLAM3、VINS、DSO、neural SLAM 等成熟系统。

### 公开代码与可复现性

原始 PTAM 后来以 GPLv3 重新发布：

[Oxford-PTAM/PTAM-GPL](https://github.com/Oxford-PTAM/PTAM-GPL)

但它依赖老式 C++ / 图像库生态，今天不适合直接作为新产品底座。

真正值得复现的是**架构思想**，而不是把 2007 代码重新移植进现代项目。

### 对当前工程项目的重新解读

机器人系统经常犯的错误是：

```text
所有模块都要求“实时”
```

更合理的是明确不同 deadline：

```text
100–500 Hz  State / Control
10–30 Hz    Tracking / Local Perception
1–10 Hz     Local Mapping / Planning
0.1–1 Hz    Global Optimization / Semantic Reasoning
event-driven Loop Closure / Rebuild
```

然后用 queue、revision 和 stable ID 协调不同层级。

PTAM 给今天最大的启示仍然非常现代：

> **算法能不能跑实时，很多时候取决于你有没有把不同时间尺度的问题错误地绑在同一个同步循环里。**

[Oxford 论文页](https://www.robots.ox.ac.uk/~lav/Papers/klein_murray_ismar2007/) · [DOI](https://doi.org/10.1109/ISMAR.2007.4538852) · [PTAM-GPL](https://github.com/Oxford-PTAM/PTAM-GPL)

## 今日结论

今天新批次里，SLAM / 状态估计最值得带走的不是一个单独 benchmark，而是**“分层 + 延迟裁决 + 几何一致性”**三个系统原则。

AMB3R-SLAM 将 local / mid-level / global consistency 分成不同 backend 时间尺度；Dynamic-LIVO 在时空证据不足时不急着把点删除，而是保留 `pending` 等待更多观测；Tangent-Group EqF 则进一步提醒我们，bias 这样的“辅助状态”怎样被放进状态空间，会直接改变线性化误差和 covariance consistency。

这三者共同说明：

```text
真实系统的可靠性
不只来自更准的单次预测
还来自状态在时间上的正确生命周期
```

控制侧也是同样的趋势。DR-MPC 主动放松一部分严格模型约束换取稳定高频求解；sRAS CBF 则把“到达以后还能安全留住”写进 safety definition；SGPS 让 sampling MPC 周期性纠正 gradient policy 的局部接触错误。传统优化、形式安全与学习策略并不是三选一，而正在形成更清晰的职责分工。

机器人学习侧，Workspace Models 很值得和之前的 2AM、P-POSEMEM、长期 scene memory 放在一起看。长期记忆不应该等价为“把所有历史不断塞进 context”。更合理的体系很可能是：

```text
不可丢的结构化事件 / 状态
        +
任务相关的轻量 latent workspace
        +
按需访问的原始历史
```

AI Coding 今天的 harness 实证则给了一个非常实用的反过度工程结论：

```text
先机械删除确定无价值的上下文
再让模型总结真正需要压缩的部分
```

并不是所有被删内容都必须建一个复杂可恢复 memory；也不是每个强模型都需要几十个专用 tool。Harness 应该根据**模型能力、任务类型和预算**配置，而不是追求组件数量。

社区最新工具变化也进一步强调模型外部的工程边界：网络权限应尽量 command-scoped；高风险命令批准应绑定 exact payload hash；Code Review finding 应有跨 revision 的生命周期。

如果把今天整期压缩成一句话：

> **无论机器人还是 Coding Agent，成熟系统都在从“一个聪明模型做所有事”转向“不同时间尺度、不同权限和不同可信度的模块通过可验证接口协作”。**

## 最值得深入研究或尝试复现的方向

1. **Hierarchical SLAM Backend Sidecar。** 不替换现有 LIO-SAM / ORB-SLAM3 前端，先把历史 keyframe graph 按 local / submap / global 三层组织；给每层独立更新频率、最大 latency 和 revision，观察大 loop closure 到来时是否能避免阻塞高频 tracking。

2. **三态 Dynamic Evidence。** 将动态过滤从 `static/dynamic` 改成 `static/dynamic/pending`；对 pending 点保留短期时空 support，1–3 秒后重判。重点比较地图完整度、ghost points、定位 ATE 与内存成本，而不是只看单帧 segmentation accuracy。

3. **MPC Hard-vs-Soft Constraint Pareto。** 在当前四足 / 无人机 MPC 上挑 1–2 组最容易造成求解困难的 equality / affine constraint，逐渐转换成高权重 penalty；同时记录 solve time、residual、tracking 和实际硬件 margin，找真正的高频控制 Pareto。

4. **Sampling MPC 作为 Policy Repair。** 现有 RL policy 不重新从零训练；只在失败 cluster、curriculum 升级或 uncertainty 高时调用 sampling MPC 生成局部 action targets，再做短 horizon policy update。比较与纯 BC / 纯 PPO 的真实失败次数和 GPU 时间。

5. **Coding Harness 三组最小 A/B。** 在同一个真实仓库任务集上只比较：`no compression vs rule-elision vs elision+summary`、`planning on/off`、`typed tools vs restricted bash`。统一记录成功率、token、wall-clock、overflow、human intervention；不要先投入复杂长期 memory，等数据说明需要再做。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent?show=2000&skip=0)
- [AMB3R-SLAM](https://arxiv.org/abs/2609.19518) · [项目页](https://hengyiwang.github.io/projects/amber-slam) · [代码仓库](https://github.com/HengyiWang/amb3r-slam)
- [Dynamic-LIVO](https://arxiv.org/abs/2609.19336)
- [Equivariant Filter Design for Acoustic and Depth Aided Inertial Navigation Systems](https://arxiv.org/abs/2609.19742)
- [DR-MPC](https://arxiv.org/abs/2609.20035)
- [Winning a Won Game: Strict Reach-Avoid-Stay CBF](https://arxiv.org/abs/2609.19449)
- [Accelerating Visual Policy Learning with Sampling-Based MPC](https://arxiv.org/abs/2609.20575)
- [Workspace Models](https://arxiv.org/abs/2609.20820)
- [An Empirical Study of Harness Design for Coding Agents](https://arxiv.org/abs/2609.20804)
- [Claude Code Releases](https://github.com/anthropics/claude-code/releases)
- [GitHub Copilot Code Review — Improved Review Experience](https://github.blog/changelog/2026-09-18-copilot-code-review-an-improved-review-experience/)
- [PTAM — Parallel Tracking and Mapping for Small AR Workspaces](https://www.robots.ox.ac.uk/~lav/Papers/klein_murray_ismar2007/)
- [PTAM DOI](https://doi.org/10.1109/ISMAR.2007.4538852)
- [PTAM-GPL](https://github.com/Oxford-PTAM/PTAM-GPL)
