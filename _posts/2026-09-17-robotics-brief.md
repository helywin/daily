---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-17"
date: 2026-09-17 09:00:00 +0800
description: "本期关注长期 LiDAR 地图证据重投影、声呐直配准、地下 VIO 失效基准、永远可行 QP、在线系统辨识 MPC、端云 VLA、交互式 SWE 评测与真实 Agent 维护质量。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-17

## 摘要

今天早间首版生成时，arXiv Robotics / Software Engineering 最新公开列表仍停留在 9 月 16 日；随后 **2026-09-17** 新批次已经刷新。Robotics 当天共有 113 条，Software Engineering 当天共有 21 条，因此本版重新检索并与 `robotics-brief-covered-items.md` 做强制去重。早间首版的 8 条主动态、1 条经典论文和 3 条社区精选保留在覆盖索引中作为历史记录，以下正文改用今天新批次中更值得长期跟踪的工作。最新列表见 [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) 与 [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

今天 SLAM / 长期地图侧最值得优先看的工作是 **SEAM**。它没有把动态物体剔除和变化检测永久绑定在某一版全局轨迹上，而是把证据锚定在 submap 上；后续新 session 触发回环、全局轨迹被重新优化时，只需要重投影 submap 级证据，不必从原始点云重新跑完整处理链。它还用 DOP-based confidence 抑制几何条件差的跨 session loop edge，并用 directional voxel evidence 区分“动态物体”和“环境真的发生变化”。这非常贴近长期巡检地图维护真正会遇到的问题。([论文](https://arxiv.org/abs/2609.18819))

水下 SLAM 方面，**SOL-SLAM** 反而非常“朴素”：只使用 Forward-Looking Sonar，不依赖 DVL / IMU 的多模态融合，通过 dense direct registration 将整幅 acoustic intensity scan 对齐到递归更新的 local map，并用 Inverse Compositional Gauss-Newton 降低每次优化成本。论文报告在 feature-rich 环境中达到与 FLS+DVL+IMU pipeline 可比的 odometry，同时已经在资源受限的 AUV 嵌入式计算机上跑完整 local SLAM。([论文](https://arxiv.org/abs/2609.18893))

视觉惯性侧，今天更值得看的不是又一个 VIO，而是 **地下环境 VIO Failure Benchmark**。它基于 CERBERUS 数据集，对 filtering、optimization、learning 三类四种代表方法施加九类实际扰动，包括 IMU bias / noise、相机内外参漂移和动态遮挡；除了 ATE，还统计 coverage ratio 与 failure threshold。真正有价值的是，它开始回答“什么时候会彻底坏掉”，而不只是正常条件下谁的平均误差更小。([论文](https://arxiv.org/abs/2609.18628))

控制侧，**ElastiQP** 解决 QP 控制器最烦人的工程状态：约束临时冲突时，solver 返回 `infeasible`，而机器人这一拍仍然必须执行点什么。它保持动力学 equality 为硬约束，却给每一个 inequality 独立的精确 L1 elastic penalty，并把 slack 解析消元，因此 condensed system 大小不随 inequality 数量增长。论文报告 microsecond-level 性能；在 infeasible case 中，最多比最佳替代 solver 快 40× 返回可执行结果，并把违反限制在真正冲突的 inequality。代码已作为 header-only C++ 库开源，并提供 Python / JAX 接口。([论文](https://arxiv.org/abs/2609.19080)，[代码](https://github.com/StanfordASL/elastiqp))

腿式控制方面，**Adaptive-MHE** 值得作为“时间回补”关注。它把 sampling-based system identification 从离线搬到 online moving-horizon estimation，用大量并行 rollout 直接拟合真实轨迹，在线估计物体质量、地面摩擦等接触参数，然后把估计结果送进 sampling-based MPC。它的关键点是：不要求 contact-rich dynamics 可微，也不要求 sim-to-real 参数在部署前一次性标定完。仿真和真机实验中，性能接近拥有 ground-truth 参数的 controller。([论文](https://arxiv.org/abs/2609.17832))

VLA 工程侧，**VLA-ULAP** 很像真正会进入产品的端云分层。远端大 VLA 仍负责困难状态，但中间大量连续动作由约 7.4M 参数的 Ultra-Lightweight Local Action Predictor 在边缘端补齐。ULAP 只读取当前视图、proprioception 和已执行 action history，不需要访问 VLA hidden state，也不需要服务器在线验证。在 Jetson Orin Nano 上单次 19.9 ms、0.183 J；不同基准中可以移除 48.8–76.7% 的 VLA calls，同时保持 95.0–97.5% 的 baseline success。物理 SO-101 上同样保持 95.2–100% baseline success，并显著减少推理时间与设备能耗。([论文](https://arxiv.org/abs/2609.18663))

AI Coding 侧，**ProgramDistill** 把“照着现有产品把功能做回来”变成可验证 benchmark。Agent 不再只读 issue，而需要实际操作一个完整 reference web app，发现其行为，再把这些行为实现进 incomplete app。自动化 `mine-craft-patch` pipeline 从 26 个 app 挖出 1,975 个 replay-verified behaviors，自动构造 4,063 个任务；随着 restoration depth 从 1 增到 8，成功率明显下降。这非常接近真实重构、竞品复刻、旧系统迁移中“需求没有完整文档，只能从正在工作的系统反推”的场景。([论文](https://arxiv.org/abs/2609.18805))

最后，**Not All Agents Are Equal** 虽然是 9 月 12 日论文，按规范作为“时间回补”，但对真实研发流程很有价值。作者分析 2,807 个 GitHub 仓库里的 37,623 个 provenance-labeled PR，覆盖 Codex、Devin、GitHub Copilot、Cursor、Claude Code，并用 58,792 份缓存 GitHub API response 分析安全 smell、结构可维护性、merge 后 churn、revert 和人工 review。结果显示差异明显是 vendor-specific，而不是简单的“Agent 代码统一优于/劣于人类”；例如 Codex PR 的观察到的 revert rate 为 6.1%，human baseline 为 11.5%，而 Devin 为 14.5%。但这是历史观察研究，不是随机对照 bakeoff，不能把这些比例直接当作当前模型能力排行榜。([论文](https://arxiv.org/abs/2609.17598))

近期通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic 与 Google DeepMind 的官方入口，没有发现 9 月 17 日需要新增报道的通用旗舰正式发布；今天 Anthropic 的新公开内容主要是科研应用与治理/度量，不是新的 Claude 主模型。因此本期不为了“模型栏目”强行重复昨天已经覆盖的发布。

## 1. SEAM：长期 LiDAR 地图的证据应该跟着 Submap 走，而不是跟某一版全局轨迹绑死

**最新公开批次；v1 提交于 2026-09-16 15:27 UTC。**

### 为什么重要

长期多 session SLAM 有一个经常被低估的数据生命周期问题：

```text
Session A 建图
   ↓
做动态物体剔除 / change detection
   ↓
把结果写进全局坐标
   ↓
Session B 新增跨会话回环
   ↓
历史轨迹整体变形
```

如果动态证据和变化证据已经被“烘焙”进旧的 global pose，那么后端一旦重新优化，之前计算的 evidence 就与新地图不再严格一致。最粗暴的办法是从原始 scan 全量重算，但长期运行后代价会越来越高。

SEAM 的核心是把 evidence 生命周期和 submap 生命周期对齐。

### 算法模块

```text
LiDAR sessions
    ↓
Submap-level trajectory anchors
    ↓
Dynamic-object removal + change evidence
    ↓
Directional voxel-wise evidence
    ↓
新 session 加入 / trajectory deformation
    ↓
Submap-level reprojection
    ↓
复用既有 evidence，而非全量重算
```

跨 session loop 还会先经过 **DOP-based confidence**。几何分布不可靠的 loop edge 被压低或拒绝，避免后端为了“闭环”强行把两段实际上不可可靠对齐的轨迹拉到一起。

### 传感器与地图假设

SEAM 假设各 submap 内部已经有足够好的局部几何，并且历史 raw / local evidence 与 submap anchor 的关系仍可追踪。

它不会自动解决所有长期变化。例如建筑施工现场可能出现结构被拆除、重新搭建；如果整个 submap 的稳定背景都已经大幅变化，旧 submap anchor 本身就可能失去意义。

### 鲁棒性与工程风险

方向化 voxel evidence 很值得关注。一个 voxel 是否被“占据”，不仅取决于有没有点，还取决于观测射线方向。如果一个物体只从某些方向反复出现，而另一些方向穿透为空，更可能是动态目标或遮挡现象，而不一定是永久环境变化。

产品化时建议给长期地图对象保留：

```text
submap_id
anchor_revision
evidence_direction
evidence_timestamp
source_session
change_confidence
reprojection_revision
```

否则后续很难审计一个 voxel 为什么被判成“新墙”或“动态车辆”。

### 实时性与可复现性

论文在真实施工场景和长期 multi-session 数据上报告更高精度和更快处理，但当前 arXiv 页面没有公开可直接核验的官方代码仓库，因此现阶段可复现性只能评为中等。

### 适合谁关注

LIO-SAM / FAST-LIO2 长期地图、多班次巡检、工厂数字孪生、施工场景、跨天机器人地图维护。

### 工程落地启发

现有 LIO 前端不用换。最小改造是：把动态点剔除、变化检测和语义标签全部从 `global_xyz` 改成 `submap_id + local evidence`，全局坐标只作为当前派生结果。这样后端 loop closure 重写历史时，上层资产可以重新投影，而不是悄悄失真。

[论文](https://arxiv.org/abs/2609.18819)

## 2. SOL-SLAM：信息已经很稀疏的声呐，不要再先丢成几个 Keypoint

**最新公开批次；v1 提交于 2026-09-16。**

### 为什么重要

Forward-Looking Sonar 的 acoustic image 本来就比相机 / LiDAR 稀疏、噪声大。如果再走经典：

```text
acoustic image
   ↓
keypoint detection
   ↓
descriptor matching
   ↓
pose
```

等于主动丢掉大量本来就不多的强度信息。

SOL-SLAM 选择 dense direct registration，直接利用完整声呐强度场。

### 算法模块

```text
FLS acoustic intensity scan
        ↓
递归 Local Acoustic Map
        ↓
Dense Direct Registration
        ↓
Inverse Compositional Gauss-Newton
        ↓
Local Pose / Map Update
```

Inverse Compositional 的好处是将部分 Jacobian / Hessian 相关计算从每次迭代中移出或复用，在 direct alignment 中减少在线计算。

### 传感器假设

它只需要 FLS，但“sonar-only”并不意味着任何水下环境都同样好用。论文明确指出其与 FLS+DVL+IMU pipeline 可比的结果来自 **feature-rich environments**。

大面积平滑海床、开阔水体、强多径或声学阴影仍会削弱可观测性；声速变化、姿态变化造成的投影差异也需要进入更完整模型。

### 结果与实时性

论文报告 dense 方法相对 sparse keypoint baseline 明显降低 translation error，并在较大 scan displacement 下仍维持稳定的 sub-meter tracking。

更重要的是，它已经在 AUV field trial 中把完整 local SLAM 跑在 resource-constrained embedded computer 上，而不是只在桌面 GPU 离线回放。

### 风险与工程边界

这仍然是 **local SLAM**。它解决短中程局部一致性，并不等价于大范围全球闭环 / 绝对定位。

水下产品栈更合理的结构仍然是：

```text
FLS Direct Local SLAM
        +
低频 DVL / USBL / Depth / IMU / Loop
        ↓
Global Navigation
```

而不是因为 local sonar odometry 很好就删除所有其他传感器。

### 适合谁关注

AUV、ROV、低成本水下机器人、FLS-only 平台、边缘端声呐定位。

### 工程落地启发

同样的思路可以迁移到其他“原始观测本身信息就少”的传感器：不要为了使用标准 feature pipeline，先把连续测量压成很少的 feature。先比较 direct likelihood / dense correlation 是否能够保留更多弱信息。

[论文](https://arxiv.org/abs/2609.18893)

## 3. 地下 VIO Failure Benchmark：最重要的不是正常情况下 ATE 多小，而是“从哪里开始坏”

**最新公开批次；v1 提交于 2026-09-16。**

### 为什么重要

地下、矿井、隧道里的 VIO 通常不是在“正常数据集精度榜”上输，而是在几类真实退化叠加后突然失效：

```text
IMU bias / noise 漂移
camera intrinsic 改变
camera-IMU extrinsic 松动
人员 / 设备遮挡视野
```

如果 benchmark 只报 nominal ATE，两个方法可能看起来只差 10%，但其中一个在少量外参漂移后直接丢轨，另一个仍然能完成 90% 路线。

### Benchmark 设计

论文基于 **CERBERUS** 地下机器人数据，选择四种代表性 VIO，覆盖 filtering、optimization 和 learning-based paradigms。

然后系统注入九类扰动，包括：

```text
IMU bias / noise variation
camera intrinsic drift
camera extrinsic drift
dynamic scene occlusion
```

评价不只看 trajectory error，还看：

```text
coverage ratio
failure threshold
breakdown behavior
```

也就是从“误差指标”转向“部署生存曲线”。

### 结果的真正价值

论文发现不同 paradigm 的脆弱点不同：有的更怕 inertial degradation，有的更怕 geometric miscalibration，有的更容易受动态干扰。

这比宣布“某方法总分第一”更有工程价值，因为选型可以按照现场最容易发生的故障来做。

例如相机与 IMU 安装在振动大的机体两端，真正需要优先看的可能就是 **extrinsic drift sensitivity**，而不是 EuRoC 上的最好 ATE。

### 可复现性

作者表示会公开完整 benchmark scripts 和 evaluation pipeline，但当前原始 arXiv 页面使用的是 “will release”，因此不能把它写成已经完整开源。

### 工程风险

人工注入 perturbation 仍然是现实故障的近似。真实外参松动可能同时伴随 rolling vibration、timestamp jitter 和 blur，而不是只改变一个静态 transform。

所以 benchmark 最好作为 failure taxonomy 的起点，而不是替代真实故障注入。

### 适合谁关注

地下机器人、矿井无人机、视觉惯性定位、传感器安装 / 标定设计、机器人可靠性测试。

### 工程落地启发

对现有 VIO / LIO 项目，建议把回归测试从“数据集跑一次 ATE”升级成参数化 fault matrix：

```text
IMU bias × {0, 1σ, 2σ, 4σ}
extrinsic rot × {0°, 0.5°, 1°, 2°}
latency × {...}
occlusion × {...}
```

最终输出 failure boundary，而不是只输出一个平均分。

[论文](https://arxiv.org/abs/2609.18628)

## 4. ElastiQP：实时控制器最怕的不是 QP 解得慢，而是这一拍“无解”

**最新公开批次；v1 提交于 2026-09-16。**

### 为什么重要

机器人 QP controller 经常同时塞入：

```text
动力学 equality
接触约束
关节限位
摩擦锥
碰撞约束
速度 / 力矩限制
任务 tracking
```

正常时一切很好，但传感器噪声、接触切换或多个 safety constraint 短暂冲突时，标准 solver 可能只返回：

```text
INFEASIBLE
```

对离线优化这很合理，对 500 Hz 控制 loop 却非常尴尬：机器人这一拍仍然要输出命令。

### 算法模块

ElastiQP 保持：

```text
A x = b
```

这类 dynamics equality 为硬约束。

对每个 inequality：

```text
Gx <= h
```

增加独立的 L1 elastic slack penalty。关键是 slack 不直接扩进最终 condensed linear system，而是解析消元，所以系统维数仍由原 decision variable 决定，不随 inequality 数量同步膨胀。

### 为什么这种设计适合机器人

现实中，动力学 equality 通常应该是“不可商量”的，而碰撞 margin、tracking bound、某些 soft joint margin 在极端瞬间可以以最小代价被轻微破坏。

ElastiQP 让每类 inequality 有不同 penalty，相当于把“谁最不能违反”写进 solver：

```text
hard dynamics
    > high-cost safety inequalities
    > lower-cost task / comfort inequalities
```

### 实时性与结果

论文报告 microsecond-level benchmark；在 infeasible 问题中，最多比最佳替代 solver **40× 更快**返回可用解，并且只放松真正冲突的 inequality。

官方仓库给出的 humanoid-scale whole-body-control 示例在 Intel i7 laptop 上约 **50 μs**。

### 可复现性

代码已公开：[StanfordASL/elastiqp](https://github.com/StanfordASL/elastiqp)。

当前实现包括：

- C++ / Eigen header-only core；
- Python bindings；
- JAX FFI；
- 示例和 tests。

仓库也明确标注 differentiability 仍处于 beta，不要把它当成已经成熟的默认 differentiable-QP 层。

### 工程风险

“always feasible”不是“always safe”。如果所有 safety inequalities 同时被赋予可放松权限，那么极端情况下 solver 仍会返回一个**违反安全约束但数值可执行**的动作。

所以 penalty hierarchy 和真正不可突破的 hardware guard 必须非常明确。

建议输出：

```text
solver_status
relaxed_constraints
slack_magnitude
weighted_violation_cost
```

只要安全类 slack 非零，就进入降级 / safe stop telemetry，而不能把 `solver succeeded` 当成一切正常。

### 适合谁关注

Whole-body QP、人形 / 四足控制、CBF-QP、机械臂约束控制、实时 MPC 内层 QP。

### 工程落地启发

现有 qpOASES / OSQP / ProxQP pipeline 不用立即替换。先离线收集历史 infeasible frame，把相同 QP 丢给 ElastiQP，比较它实际选择放松了哪些 constraint，是否符合工程师对优先级的直觉，再决定是否进入真机 shadow mode。

[论文](https://arxiv.org/abs/2609.19080) · [代码](https://github.com/StanfordASL/elastiqp)

## 5. Adaptive-MHE：让 MPC 在执行过程中持续辨识“这个箱子到底多重、地面到底多滑”

**时间回补：v1 提交于 2026-09-15 20:49 UTC。**

### 为什么重要

腿式 loco-manipulation 的 sim-to-real gap 很多时候不是 policy 不够大，而是几项物理参数错了：

```text
object mass
contact friction
terrain property
```

这些参数还会在一次任务中改变——推不同箱子、从干燥地面走到湿滑区域，部署前一次性 system-ID 根本不够。

### 方法结构

Adaptive-MHE 把 sampling-based Sys-ID 做成 moving horizon：

```text
最近一段真实 state / action trajectory
              ↓
Massively Parallel Simulation Rollouts
              ↓
寻找最能解释真实轨迹的参数
(mass / friction / ...)
              ↓
Moving-Horizon Parameter Estimate
              ↓
Sampling-based MPC
              ↓
新动作 + 新数据
              ↺
```

它不依赖 dynamics 的解析梯度，所以特别适合包含接触切换、摩擦和非光滑碰撞的系统。

### 为什么比离线 Sys-ID 更适合接触任务

经典 offline ID 会得到：

```text
robot nominal model
```

Adaptive-MHE 更像持续维护：

```text
environment-conditioned model belief
```

机器人推一个轻箱子时学到的参数，不会被假定永久适用于下一件重物。

### 结果与工程边界

论文在 simulation + hardware experiment 中持续优于基线，并达到接近“controller 已经知道 ground-truth physical parameters”的性能。

当前摘要没有披露统一控制频率、并行 rollout 数量和具体硬件算力，因此还不能据此判断它是否能直接塞进所有嵌入式腿式平台。

### 风险

系统辨识存在非常典型的可辨识性问题：

```text
动作不够激励
→ mass 和 friction 的效果可能混在一起
→ 参数看似收敛，但不唯一
```

更危险的是“错误参数 + MPC 自己补偿”可能短期仍表现正常。

因此建议同步保存 parameter covariance / ensemble spread，而不只输出单点 `mass=...`。

### 适合谁关注

四足 / 人形 loco-manipulation、MPPI / sampling MPC、在线 system-ID、Sim2Real。

### 工程落地启发

可以先从一个参数开始：例如只在线估计被推物体质量或地面 friction scale。先验证真实轨迹 residual 是否确实随该参数变化，再逐步增加维度；不要一开始就让在线 estimator 同时自由调整几十个物理参数。

[论文](https://arxiv.org/abs/2609.17832)

## 6. VLA-ULAP：大 VLA 不需要每一拍都被调用，边缘端可以补上“肌肉记忆”

**最新公开批次；v1 提交于 2026-09-16。**

### 为什么重要

云端 / 远端 VLA 有两个天然问题：

```text
GPU power 很高
network latency 不稳定
```

但机器人动作序列里又有大量连续局部阶段，例如抓取接近后继续闭合、已经对准以后持续插入。这些阶段不一定值得每 100–300 ms 再调用一次 billion-parameter model。

VLA-ULAP 在大模型调用之间插入一个很小的 local predictor。

### 算法模块

```text
Remote / Cloud VLA
      ↓
关键 Action Chunk
      ↓
Robot executes
      ↓
current views
proprioception
executed action history
      ↓
ULAP (~7.4M params incl. frozen vision encoder)
      ↓
Local Action Chunk
      ↓
必要时重新调用 VLA
```

最关键的是 ULAP **独立训练**，不依赖远端 VLA hidden states，也不需要每一拍向服务器请求 verifier。

所以它不是“压缩大模型内部某一层”，而是一个可以替换不同 base VLA 的外部 sidecar。

### 延迟与能耗

论文报告：

```text
ULAP / Jetson Orin Nano
19.9 ms
0.183 J / inference
```

论文同时给出 GR00T / RTX A6000 的 284.3 ms、50.55 J 数据，但这是**不同模型 + 不同硬件**，不能简单宣传成同硬件加速多少倍。

更有参考价值的是 episode-level 结果：在三个 simulation base-policy / benchmark 配对中，可以移除 **48.8–76.7%** VLA calls，同时保留 **95.0–97.5%** baseline success。

实体 SO-101 上保留 **95.2–100%** baseline success，同时估算 inference time 降低 47.9–58.0%，inference-device energy 降低 52.1–62.5%。

### 鲁棒性与风险

最大风险是“什么时候该相信小模型”。论文展示的 operating point 是离线选出来的；生产系统最好有明确的 fallback trigger：

```text
OOD / uncertainty high
unexpected contact
scene changed
local prediction disagreement
elapsed local steps too many
        ↓
force remote VLA refresh
```

否则 ULAP 会把一个小误差连续滚成大偏差。

### 适合谁关注

端云 VLA、Jetson Orin、远程 robot inference、低功耗机械臂、移动网络条件下的机器人基础模型。

### 工程落地启发

这套架构也适用于非 VLA：大模型只负责低频决策，轻量 policy 负责高频闭环。真正值得优化的指标不是“单次模型 FPS”，而是：

```text
每个成功 episode 的远端调用次数
P95 action latency
总推理能耗
失败时重新观察的恢复速度
```

[论文](https://arxiv.org/abs/2609.18663)

## 7. ProgramDistill：真实软件需求经常不在 Issue 里，而藏在“那个旧系统实际怎么工作”

**最新 Software Engineering 批次；v1 提交于 2026-09-16。**

### 突破性工程价值

现有 Coding Agent benchmark 通常给出：

```text
Issue / Task Description
        ↓
Repo
        ↓
Patch
```

但真实重构、系统迁移和竞品兼容经常是另一种任务：

> 这里有一个正在工作的 reference app，你自己操作它，搞清楚行为，然后把缺失功能做出来。

ProgramDistill 正式把这种 **behavior discovery → implementation** 做成 benchmark。

### Benchmark 如何生成

作者把完整应用拆成不同粒度的 feature，并使用 `mine-craft-patch` pipeline：

```text
Functional Reference App
        ↓
自动探索 / 挖掘 Behavior
        ↓
Replay 验证 behavior 是否稳定
        ↓
关联 Gold Patch
        ↓
构造 Incomplete App Task
```

最终从 **26 个应用**中得到：

```text
1,975 replay-verified behaviors
4,063 tasks
```

且任务构建无需人工逐条写 issue。

### 结果告诉了什么

九个 frontier coding agents 中，论文报告 GPT-6 Astra 和 Claude Opus 5 在 full-app cumulative workflow 上分别为 **49.2% / 28.8%**。

Partial reconstruction 中，当 restoration depth 从 1 增加到 8，两个示例设置的成功率分别从 100%→64.0%、96%→32%。

这说明单个 UI 行为复刻不一定难，困难在于越来越长的依赖链和行为组合。

### 是否适合真实研发流程

很适合：

- 老系统重写；
- 前端 / App 行为兼容；
- 无完整文档的内部工具迁移；
- 自动生成回归测试；
- Coding Agent curriculum。

它还提示一个非常实际的 Agent workflow：**先让 Agent 写行为测试，再写实现。**

如果 reference app 的 behavior 没有被 replay 固化，后续实现成功与否就无法稳定验证。

### 风险与边界

行为等价不等于内部实现等价。一个 clone 可以通过可见 replay，却在 accessibility、性能、安全、隐藏边界条件上完全不同。

所以“reference-guided”适合建立功能契约，但不应替代代码级和非功能需求 review。

### 工程落地启发

公司内部遗留系统可以先做：

```text
reference app
→ 自动浏览 / API trace
→ behavior artifact
→ deterministic replay
→ agent implementation
→ differential verification
```

需求文档从“人努力写全”变成“文档 + 可执行行为规范”。

[论文](https://arxiv.org/abs/2609.18805)

## 8. Not All Agents Are Equal：Agent 代码质量不能只看第一次 PR 能不能过测试，还要看 Merge 之后发生什么

**时间回补：v1 提交于 2026-09-12 19:51 UTC。**

### 突破性工程价值

Coding Agent benchmark 最常测：

```text
patch accepted?
tests pass?
```

但公司真正付成本的地方还包括：

```text
一周后被 revert 吗？
后续 churn 高吗？
有没有 security smell？
需要多少人 review？
```

这篇研究直接把观察窗口拉到 merge 之后。

### 数据规模

作者分析：

```text
37,623 provenance-labeled PRs
2,807 GitHub repositories
5 commercial coding agents
+ matched human baseline
Dec 2024 – Jul 2025
```

并结合 **58,792** 个缓存 GitHub API response，分析 security smell、structural maintainability、post-merge churn、revert rate 和 human review。

覆盖的 Agent 包括：

- OpenAI Codex；
- Devin；
- GitHub Copilot；
- Cursor；
- Claude Code。

### 值得记住的结果

观察数据中：

```text
Codex PR revert        6.1%
matched human          11.5%
Devin                   14.5%
```

Pooled agent code 的 security-smell odds 比 human 更低（OR 0.63），主要由更少 hardcoded credentials / eval-style constructs 驱动。

人类 review 负担也不均匀：Copilot PR 收到最多 review / change request；Claude Code PR 到第一次人工 review 的 median 最长，为 **12.6 h**。

### 最重要的边界：这不是 Agent 排名赛

这是**历史 observational study**，不是随机把同一批任务分配给五个 Agent。

不同工具的：

```text
用户群
任务类型
仓库规模
使用时间段
自动化程度
```

都可能不同。因此不能从 6.1% vs 14.5% 直接得出“Codex 比 Devin 强多少”的因果结论。

真正可靠的结论是：**不同 Agent 的 post-merge failure profile 确实不同，组织应该测自己的长期指标。**

### 工程落地启发

内部 Agent dashboard 不要只放：

```text
PR acceptance rate
```

建议增加：

```text
7d / 30d revert rate
post-merge fix commits
review comments / PR
security findings
churn after merge
human review latency
```

这样才能判断“AI 把 PR 做快了”是否真的等于“研发吞吐提高了”。

[论文](https://arxiv.org/abs/2609.17598)

## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### A. Headless Coding Agent 的 MCP 启动必须有 Deadline：可选依赖不能拖死第一回合

**来源：Claude Code v2.1.274，2026-09-17 官方 release。**

Claude Code 今天新增 `CLAUDE_CODE_MCP_STARTUP_WAIT_MS`，用于限制**第一个非交互回合**等待 MCP server 连接的最长时间；设为 `0` 可以完全不等待。

这个小功能背后的工程原则很重要：

> Agent 的工具依赖必须区分 required 与 optional，而且每个外部依赖都应该有明确启动 deadline。

如果 CI / scheduled agent 同时配置了 GitHub、数据库、浏览器、内部文档等多个 MCP，只要其中一个坏掉，默认无限等或等待很久，就会让整个自动任务看起来像“模型卡死”。

**今天可以直接用：**给 headless agent 做依赖分级：

```text
Required MCP
→ 启动失败：任务 FAILED，不继续

Optional MCP
→ 有 startup timeout
→ 超时：记录 DEGRADED，继续剩余任务
```

再把 `MCP connected / timed out / unavailable` 写进最终 receipt。

**边界：**不要为了追求启动速度对关键 source-of-truth 设置 `0`。如果任务必须读取某个数据库 / 工单系统才能安全执行，MCP 没连上时应该 fail closed，而不是让模型凭记忆继续。

[Claude Code Releases](https://github.com/anthropics/claude-code/releases)

### B. Plugin / Skill 也应该像代码一样有 Regression Eval，而不是“改完 Prompt 手感不错”

**来源：Claude Code v2.1.269，2026-09-11 官方 release；最近 7 天补充。**

Claude Code 新增 `claude plugin eval`：可以运行插件自己的 eval suite，并生成 scored、可复现的 JSON + HTML 报告。

这条功能非常适合 Vibe Coding 工作流，因为很多团队已经开始长期维护：

```text
AGENTS.md / CLAUDE.md
skills
custom commands
subagents
MCP-based plugins
```

但修改这些“Agent 基础设施”时仍然常靠主观体验：跑两次感觉变好了，就直接上线。

**今天可以直接用：**给关键 skill 建一组固定案例：

```text
case_id
input repo / fixture
user request
required artifacts
forbidden changes
validation command
expected evidence
```

每次改 system prompt / skill / plugin 都先跑同一套 suite，再比较成功率、token、工具调用次数和错误类型。

这与普通单元测试的区别是：Agent 输出可能不是 bitwise deterministic，所以更应该保存**评分标准和执行证据**，而不是只看最终文字。

**边界：**eval suite 很容易被过拟合。不要让 Agent 只针对一小组公开 case 优化；保留 hidden / held-out regression，并定期加入真实生产失败案例。

[Claude Code Releases](https://github.com/anthropics/claude-code/releases)

## 经典论文回顾

### The Normal Distributions Transform：NDT 为什么二十多年后仍是点云定位的重要基线

Peter Biber 与 Wolfgang Straßer 的 **The Normal Distributions Transform: A New Approach to Laser Scan Matching** 发表于 **IROS 2003**。原始论文是 2D laser scan matching，但它提出的核心表示后来扩展到 3D NDT、自动驾驶定位、矿山车辆、Radar odometry 和长期地图。

[原论文 DOI](https://doi.org/10.1109/IROS.2003.1249285)

### 核心问题

ICP 类方法通常需要显式建立：

```text
source point
   ↕ correspondence
map point / plane
```

对应关系本身就是计算成本和失败来源，尤其在扫描稀疏、初值较差或局部几何重复时。

NDT 的思路是先把地图变成**连续概率密度近似**。

### 原始 2D NDT 表示

将平面划分成 cells，对每个 cell 内的点估计：

```text
mean μ
covariance Σ
```

于是一个 cell 不再只是一堆离散点，而是一个局部 Gaussian：

```text
p(x) ∝ exp(-1/2 (x-μ)^T Σ^-1 (x-μ))
```

整个地图变成 piecewise continuous、可微的 probability density。

另一帧 scan 经过候选刚体变换以后，直接评价每个 transformed point 在该密度上的 likelihood，然后用 Newton-style optimization 找最大匹配概率。

关键点是：**不需要显式 point-to-point / point-to-line correspondence。**

### 当年为什么重要

它把 scan matching 从：

```text
找对应 → 最小化距离
```

转换成：

```text
建立局部统计地图 → 最大化概率密度匹配
```

这种表示天然把局部表面方向和点分布编码进 covariance，同时大幅压缩原始点云。

### 3D 扩展为什么影响很大

后来 3D-NDT 将同样思想扩展到 voxel：

```text
3D voxel
→ Gaussian distribution
→ scan-to-distribution / distribution-to-distribution registration
```

它长期被用于：

- 自动驾驶 LiDAR map localization；
- mining vehicle registration；
- 3D SLAM；
- NDT occupancy maps；
- Radar odometry；
- place recognition representation。

今天 Autoware 仍然有 NDT scan matcher，PCL 也保留 `NormalDistributionsTransform` 实现。

### 传感器与几何假设

NDT 不是“无需 correspondence 所以永不退化”。

它仍然依赖：

- 初始 pose 足够接近正确 basin；
- voxel 中有足够点估 covariance；
- 环境几何在目标自由度上提供信息；
- resolution 与 sensor density 匹配。

长走廊、大平面、重复结构同样可能产生弱约束方向。

因此 NDT 与昨天讨论的 LiLi / 经典 degeneracy analysis 本质上并不冲突：**一个是 registration objective，一个是判断 objective 在哪些方向上真的可信。**

### 实时性与现代替代

现代系统中，NDT 的位置已经更加多样：

```text
NDT
ICP / GICP / VGICP
surfel registration
feature-based LIO
implicit / neural map registration
```

GPU NDT、VGICP 等方法在很多硬件上已经更快；FAST-LIO2 一类紧耦合 LIO 也不依赖传统 NDT 作为高频 odometry 前端。

但在**已有先验地图的全局定位 / scan-to-map registration**中，NDT 的统计网格表示仍然非常有吸引力。

### 可复现性

原始论文年代较早，没有现代官方 GitHub，但今天非常容易复现：

- [PCL NDT Tutorial](https://pointclouds.org/documentation/tutorials/normal_distributions_transform.html)
- [Autoware NDT Scan Matcher](https://autowarefoundation.github.io/autoware_core/latest/localization/autoware_ndt_scan_matcher/)
- [fast_gicp / CUDA NDT](https://github.com/koide3/fast_gicp)

### 对当前工程项目的重新解读

对于低线数 16 线 LiDAR，NDT 的关键不是“是否比某个新 LIO 更强”，而是**地图分辨率与局部统计是否稳定**。

点太少时，如果 voxel 太小：

```text
每格样本不足
→ covariance 不可靠
```

voxel 太大又会：

```text
不同表面被混进同一 Gaussian
→ 几何被过度平滑
```

因此低线数雷达用 NDT 更应该监控：

```text
points / voxel
covariance condition
active voxel count
Hessian / localizability spectrum
registration basin
```

不要只调一个固定 resolution。

而对已有 LIO-SAM 的系统，NDT 更适合成为：

```text
低频 scan/submap → prior map localization
```

而不是为了使用 NDT 把已经稳定的高频 LIO 前端全部推倒重做。

[原论文 DOI](https://doi.org/10.1109/IROS.2003.1249285) · [PCL NDT](https://pointclouds.org/documentation/tutorials/normal_distributions_transform.html) · [Autoware NDT](https://autowarefoundation.github.io/autoware_core/latest/localization/autoware_ndt_scan_matcher/)

## 今日结论

今天 SLAM / 状态估计里最值得带走的不是“哪篇 ATE 最低”，而是**长期资产与失败边界开始成为一等设计对象**。

SEAM 说明：地图里动态物体、变化检测、语义等高层 evidence 不应该绑死在某一版 global trajectory 上；后端可以重写历史，上层证据也必须能够随 submap / anchor revision 重投影。地下 VIO benchmark 则从另一侧提醒：一个 estimator 的产品质量不能只由 nominal ATE 定义，而应该由 `failure boundary × coverage × calibration sensitivity` 共同定义。

SOL-SLAM 又给了一个很经典但常被忘记的信号：传感器本来就信息稀缺时，先抽 feature 不一定是最优选择。Direct method 在相机时代讨论过很多次，在声呐这种 sparse-information modality 上仍然成立。

控制侧今天的两个方向可以浓缩成：

```text
优化器必须有降级语义
模型必须能在线修正
```

ElastiQP 不允许实时 loop 在约束冲突时只返回“无解”，而是明确告诉你必须违反哪几个 inequality 才能继续；Adaptive-MHE 则不再假设 deployment dynamics 永久固定，而是持续从最新 trajectory 反推 mass / friction。二者都在把传统控制器从“理想模型的一次性求解”推向“现实世界持续不完美时仍能解释自己正在做什么”。

VLA-ULAP 的产品信号也很清楚：未来 VLA 并不一定等于每一控制拍都跑同一个十亿参数模型。更现实的系统会逐渐形成：

```text
低频大模型语义 / 纠偏
        +
高频小模型动作延拓
        +
确定性 Safety / Controller
```

这和机器人经典 hierarchical control 其实是同一套思想，只是上层模型换成了 VLA。

AI Coding 侧，ProgramDistill 与 post-merge Agent 研究都把评测从“静态题目答对了吗”推进到真实软件生命周期：需求可能需要从 reference behavior 反推，而代码 merge 后还要观察 revert、churn、安全 smell 和人工 review。对于真正长期使用 Codex / Claude Code 的团队，比单次 benchmark 分数更值得建设的是**自己的行为回归库和 merge 后 telemetry**。

社区精选也给了两个很朴素但重要的基础设施原则：MCP / 外部工具必须有 deadline；Prompt、Skill、Plugin 也必须有可复现 regression suite。随着 Agent 变强，最影响生产稳定性的越来越不是“再写一段更聪明的系统提示”，而是模型之外的 timeout、evidence、eval、rollback 和 failure state。

## 最值得深入研究或尝试复现的方向

1. **Submap-Anchored Long-Term Evidence。** 在现有 LIO-SAM / GTSAM 上给动态点、反光标志、变化事件和语义对象统一改成 `submap_id + local evidence`，每次 pose-graph optimization 后只做重投影。专门构造跨 session 大回环，比较“旧 global_xyz”与“submap reprojection”在地图重写后的误差。

2. **VIO Failure Surface。** 不再只跑一次 EuRoC / CERBERUS ATE。对相机外参、IMU bias、timestamp、遮挡分别做参数 sweep，画出 `perturbation → coverage / failure rate` 曲线。用它决定硬件安装和标定优先级，而不是只决定算法排名。

3. **QP Constraint-Conflict Replay。** 从四足 / 机械臂控制日志中保存历史 `infeasible` QP，离线用 ElastiQP 重放，检查它自动放松的 inequality 是否符合安全优先级；再设计 `safety slack > 0 → degrade / stop` 的 runtime policy。

4. **Online One-Parameter MHE。** 在 sampling MPC 中先只在线估一个最敏感参数，例如 object mass 或 ground friction scale，记录 parameter belief、trajectory residual 与 MPC performance。确认具有真实可辨识性后再扩多参数，不要一开始构造高维在线 Sys-ID。

5. **Agent Behavior Regression + Post-Merge Telemetry。** 选 20–50 个真实项目行为做 deterministic replay，要求 Coding Agent 每次修改都通过；同时统计 7/30 天 revert、fix-after-merge、review comments、security finding。把 Plugin / Skill 更新也纳入同一套 eval，而不是只根据一次 session 的“手感”决定上线。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [SEAM: Submap-Anchored Evidence for Lifelong LiDAR Mapping under Trajectory Deformation](https://arxiv.org/abs/2609.18819)
- [SOL-SLAM](https://arxiv.org/abs/2609.18893)
- [Benchmarking VIO in Subterranean Environments](https://arxiv.org/abs/2609.18628)
- [ElastiQP](https://arxiv.org/abs/2609.19080) · [GitHub](https://github.com/StanfordASL/elastiqp)
- [Adaptive-MHE](https://arxiv.org/abs/2609.17832)
- [VLA-ULAP](https://arxiv.org/abs/2609.18663)
- [ProgramDistill](https://arxiv.org/abs/2609.18805)
- [Not All Agents Are Equal](https://arxiv.org/abs/2609.17598)
- [Claude Code Releases](https://github.com/anthropics/claude-code/releases)
- [The Normal Distributions Transform](https://doi.org/10.1109/IROS.2003.1249285)
- [PCL NDT Tutorial](https://pointclouds.org/documentation/tutorials/normal_distributions_transform.html)
- [Autoware NDT Scan Matcher](https://autowarefoundation.github.io/autoware_core/latest/localization/autoware_ndt_scan_matcher/)
