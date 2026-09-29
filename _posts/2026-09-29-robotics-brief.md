---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-29"
date: 2026-09-29 09:00:00 +0800
description: "本期关注建筑 Mesh 上的 LiDAR 全局重定位、语义鲁棒 RTK-VIO、风场预览 MPC、低成本 ToF 四足感知、刚性接触可微仿真、20K 小时 World Action Model、Claude Sonnet 5.5 与 Coding Agent 成本治理。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-29

## 摘要

截至 2026-09-29 09:00（Asia/Shanghai），arXiv Robotics 与 Software Engineering 的最新常规公开批次均为 2026-09-28（周一），分别包含 84 条 Robotics 与 24 条 Software Engineering 条目。今天先检查最近 24 小时的新发布，再从最近 7 天范围补足高价值且未覆盖的工作，并与覆盖索引按规范化标题、arXiv ID、DOI、项目页和 GitHub 地址强制去重。由于本期入选的论文 v1 均实际提交于 9 月 25 日 UTC，已超过 24 小时，所以统一标为“时间回补”；Claude Sonnet 5.5 则是 9 月 28 日正式发布的最新模型动态。

今天定位方向最值得看的是两项“把不确定性真正放进系统”的工作。Transformer-based Monte Carlo Localization in Construction Meshes 用纯合成 LiDAR 扫描训练 PointNet++ + place-recognition decoder，再把网络输出当作 MCL 的 learned observation model；uncertainty-aware decoder 会缩放位置 likelihood，resampling 还主动注入 model hypothesis，避免粒子耗尽，真实数据上保持 18 ms 单次推理。SeA-RVINS 则针对深城市 RTK-VIO：视觉端在 landmark 持久化之前先做 semantic-aware track rejection，GNSS 端对 double-difference 做保留 shared-pivot correlation 的 robust DCS，并设计 ambiguity continuation，约 20 km TEX-CUP 路线中达到 100% availability。

控制侧今天有两条特别适合工程化。Wind-Preview MPC 不是等阵风已经打到机体以后再估 disturbance，而把低成本 pitot-static sensor 放到前伸 boom 上，提前量测即将到来的风并写进 nonlinear MPC；室外实验沿风方向误差相对 baseline 减少 54%。另一项 ANYmal 工作则走反方向：不是再堆高端 LiDAR / depth camera，而是在机器人周身布置低成本 ToF，用近场分布式覆盖补足传统传感器 blind spot，仍能达到厘米级局部建图并支持 footstep planning。

机器人学习里，Bundled Contact Gradients 解决 differentiable simulator 的经典矛盾：软接触梯度平滑但物理不真，刚性接触更真实却让梯度对微小状态扰动极敏感。BCG 只在 stiff contact 附近做一小簇 randomized perturbation rollout，再聚合 gradient，从而保留硬接触 fidelity，同时压低 gradient variance，最终实现 Unitree G1 动态动作零样本迁移真机。

世界模型方向，InternW0-Δ 把视觉动力学、VLM 语义、4D 几何/运动先验与 action generation 放到一个 Mixture-of-Transformers WAM 中。它的数据规模超过 20K 小时，尤其值得注意的是 Causal Imprint：训练时利用 future supervision 学 action-relevant future change，但推理时不需要真的生成 future video，再把这些 predictive representation 直接给 action expert。项目页已公布多项 simulation / real-robot 结果，并承诺开放训练代码、模型权重、基础设施与可许可的数据处理产物。

最新模型方面，Anthropic 在 9 月 28 日发布 Claude Sonnet 5.5。官方定位非常明确：Opus 5.5 继续面向复杂开放式任务，Sonnet 5.5 面向范围清晰的日常工作、代码修复和文档产出；API 价格仍是每百万输入 token 2 美元、输出 token 10 美元，但官方称输出速度快 30% 以上、典型任务成本最多降低约 30%。Terminal-Bench 4.0 官方结果为 70.6%，但这类厂商 benchmark 更适合用作“值得加入自己的 regression set”的信号，而不是直接替代真实仓库 A/B。

AI Coding 论文里，Analyzing and Mitigating Cost-Inefficient Behaviors in Coding Agents 非常适合长期使用 Claude Code / Codex 的团队。作者先分析 1,200 条 SWE-bench Verified trajectory，发现 subsumed retrieval、similar script generation、test re-execution 三类浪费影响 79%–98% 的任务，最高占 22.75% task cost；更大规模 10K+ trajectory 验证中，结构感知 retrieval 甚至可能把成本提高 28.14%，而开发者设计的高层、trace-agnostic Skill 最多降低 41.73% 成本，约是 Agent 自己生成 Skill 的两倍收益。

最新公开列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

## 1. Transformer MCL：从建筑 Mesh 直接训练 LiDAR 全局重定位，而不是先采一套真实地图

**时间回补：v1 提交于 2026-09-25 14:54 UTC。**

### 为什么重要

施工现场、厂房和建筑内部经常已经有 BIM / triangle mesh，却没有机器人真正走过一遍采集的 LiDAR localization map。经典做法通常需要先把机器人带进现场建图，再做 Scan Context / place recognition / registration；但对施工周期频繁变化的环境，这相当于一直追着现场重新采地图。

这篇工作的关键是：把“建筑 mesh 就是全球参考地图”当成前提，直接在 mesh 中模拟 LiDAR scan 训练全局观测模型，然后把 learned likelihood 放回 Monte Carlo Localization，而不是让神经网络直接输出最终 pose。

### 算法模块

    Building triangle mesh
            ↓
    synthetic LiDAR simulation
            ↓
    PointNet++ encoder
            ↓
    place-recognition decoder
            ↓
    learned position likelihood
            ↓
    Monte Carlo Localization
       ├─ uncertainty-aware likelihood scaling
       └─ model-hypothesis injection during resampling
            ↓
    global pose belief

这里真正值得保留的是“网络只负责 observation model，粒子滤波继续负责 multi-hypothesis belief”。重复房间和低纹理环境中，单个网络 pose 容易过早选错；MCL 可以同时保留多个位置假设，再通过后续 scan 逐步淘汰。

### 传感器与地图假设

需要 3D LiDAR 与质量足够的建筑 mesh，并假设 mesh 与真实场地整体拓扑没有严重偏差。训练只使用由 mesh 模拟的 synthetic LiDAR，因此部署前不要求真实 scan label，这是它最大的工程优势。

但施工现场临时脚手架、堆料、门状态和移动设备都可能与设计 mesh 不一致，因此 learned observation model 必须允许较宽 uncertainty，而不是把 synthetic-to-real gap 当成测量噪声为零。

### 实时性与鲁棒性

论文在真实数据上相对 diffusion-based 和 ScanContext++ baseline 获得更好全局重定位表现，单次模型调用约 18 ms。uncertainty-aware decoder 会根据模型的不确定性缩放 positional likelihood；resampling 中主动注入 model hypothesis，则用于缓解 particle depletion。

### 可复现性与工程风险

当前 arXiv 页面没有明确成熟开源仓库入口，因此可复现性暂时弱于已经开放代码的项目。最值得先复现的不是整个 Transformer，而是“mesh → synthetic scan → particle-filter observation likelihood”这条数据链。

最大风险是 mesh revision。建议地图层明确保存：

    mesh_version
    localization_model_version
    synthetic_scan_profile
    real_scan_domain_shift_score

当 BIM 更新时，不能只替换 mesh，却继续使用旧模型。

### 适合谁关注

BIM / 建筑机器人、室内巡检、已拥有 CAD / mesh 但缺少现场 LiDAR map 的团队，以及希望保留多假设全局定位而不是单点回归的系统。

### 工程落地启发

可以把现有局部 FAST-LIO / LIO-SAM 与这一类全局模块分层：

    local tracking
    → LIO / VIO

    global belief
    → mesh-based MCL

    global correction
    → 只有 posterior 足够集中时才注入 pose graph

这样“全局认错房间”不会直接瞬间拉坏局部里程计。

[论文](https://arxiv.org/abs/2609.31357)

## 2. SeA-RVINS：深城市 RTK-VIO 的难点不是多加传感器，而是别让坏观测长期留在图里

**时间回补：v1 提交于 2026-09-25 04:49 UTC。**

### 为什么重要

城市峡谷里，RTK GNSS 会被 multipath / NLOS 污染；VIO 则可能因为车辆、玻璃、重复纹理和错误 temporal association 把坏 landmark 写进因子图。紧耦合系统最危险的不是偶尔有一个 outlier，而是错误观测一旦被“持久化”，会在多个时刻持续拉扯状态。

SeA-RVINS 的思路很系统：视觉错误尽量在进入 persistent landmark graph 之前淘汰；GNSS 则不能为了 robustification 随便把 double-difference 之间原本共享 pivot 的相关结构抹掉。

### 算法模块

    stereo images + IMU
          ↓
    semantic-aware learned stereo frontend
          ↓
    reject unreliable tracks
          ↓
    persistent landmarks
          ┐
          ├→ fixed-lag factor graph
          │
    RTK GNSS double differences
          ↓
    Dynamic Covariance Scaling
      ├─ batch
      ├─ scalar
      └─ latent-pivot formulation
          ↓
    ambiguity continuation
      ├─ one ambiguity state within verified short arc
      └─ random-walk links across arcs

### 传感器与估计假设

系统依赖 stereo camera、IMU 和 RTK GNSS。GNSS double-difference 的 shared-pivot correlation 是数学结构的一部分，因此 robust loss 不能把每个 residual 完全当独立标量随便降权。

视觉端使用 semantic-aware learned frontend，这有利于拒绝动态/不可靠 track，但也增加了 learned perception 的 domain shift 风险。

### 结果

在约 20 km 的 TEX-CUP 路线中，大约一半属于 deep-urban 场景。论文报告 latent-pivot 配置达到 100% availability，最大水平误差 1.6 m；96.16% epoch 小于 1.0 m，99.90% 小于 1.5 m。

### 鲁棒性与工程风险

这个工作最值得借鉴的是“坏数据要尽量在生命周期早期处理”。对视觉：

    detection / semantics
    → track quality
    → landmark admission
    → factor graph

不要等错误 landmark 已跨几十帧存在后再靠一个 robust kernel 补救。

对 RTK 则建议保存：

    ambiguity_arc_id
    pivot_satellite
    correlation_model
    DCS_weight
    fix_status
    multipath_indicator

否则后续排查“为什么 RTK 看似 fix 但轨迹突然跳”会非常困难。

### 可复现性

论文明确声明 implementation released as open-source software，但本轮公开检索没有稳定定位到作者给出的官方仓库地址，因此归档仅链接原论文，不猜测 GitHub 地址。

### 适合谁关注

RTK + VIO、城市无人车、室外机器人、希望将外置 RTK 与视觉惯导做真正紧耦合而不是简单 pose blending 的团队。

### 工程落地启发

对现有因子图系统，可以先增加“factor admission gate”：一个观测进入长期图之前，必须有独立的 semantic / geometric / temporal quality check。长期图的鲁棒性往往来自“不把垃圾写进去”，而不是把 robust loss 调得越来越重。

[论文](https://arxiv.org/abs/2609.30814)

## 3. Wind-Preview MPC：无人机抗阵风可以从“扰动观测”升级成“扰动预览”

**时间回补：v1 提交于 2026-09-25 12:16 UTC；投稿 ICRA 2027。**

### 为什么重要

常见抗风方法都是 reactive：要么从机体加速度、姿态误差反推出 disturbance，要么在机体附近测风。但无论哪一种，风已经作用到无人机以后控制器才知道。

这篇工作把一个轻量 pitot-static sensor 安装在机体前方 boom 上。无人机向风场方向飞行 / 悬停时，传感器在风真正打到机体之前先测到它，相当于给 MPC 一个短时间 preview horizon。

### 算法模块

    pitot-static sensor on forward boom
              ↓
    upcoming wind measurement
              ↓
    wind preview over short horizon
              ↓
    nonlinear MPC
       ├─ vehicle dynamics
       ├─ rotor / state constraints
       └─ previewed disturbance
              ↓
    anticipatory control command

### 一个很有工程价值的结论：Boom 不是越长越好

更长的 boom 提供更多预览时间，但同时增加惯量、改变平台动态。仿真表明最优 preview distance 不是平台固定常数，而会随着风速和无人机响应速度移动。

这比“装个更长传感器杆就行”更符合真实系统。

### 真机结果

室内硬件实验相对 PX4 baseline 和完全相同但没有 wind preview 的 MPC 明显改善 hover；室外实验中，沿风方向误差相对 baseline 降低约 54%。

### 传感器与动力学假设

当前方案使用单个 wind-aligned sensor，因此最适合已知主要风方向或能让传感器朝向有效来流的场景。复杂 3D 湍流、旋翼下洗和机体姿态变化都会影响 pitot-static 测量。

### 工程风险

把 preview sensor 当安全关键输入时，要有明确 fallback：

    wind_preview_valid
    pitot_quality
    boom_vibration
    current_wind_estimate
    preview_age

当 preview 失效时，MPC 应退化成 wind-unaware / disturbance-observer 模式，而不是继续使用陈旧风值。

### 适合谁关注

户外无人机、狭窄走廊出口 / 风口飞行、抗风悬停、MPC、希望用低成本传感器改善控制而不是堆更大模型的团队。

### 工程落地启发

对走廊飞行特别有启发：靠近门口 / 洞口时，气流变化往往早于机体受扰。未来可以把 wind preview 与 LiDAR 的空间预览放到同一 MPC horizon 中：几何告诉你“将到哪里”，风传感器告诉你“那里即将有什么扰动”。

[论文](https://arxiv.org/abs/2609.31185)

## 4. ANYmal 分布式 ToF：近场避障不一定非得再加一台深度相机

**时间回补：v1 提交于 2026-09-25 08:52 UTC；IEEE RA-L 2026。**

### 为什么重要

四足机器人通常已经装了 LiDAR / depth camera，但这些传感器在机身近处仍然常有 blind spot：脚边的小台阶、机器人侧后方凸起、贴近身体的障碍，可能恰好位于主传感器视场外。

传统解法是再加更多深度相机，但价格、功耗、数据带宽和标定复杂度都会上升。

这篇工作尝试更朴素的方案：把低成本、低分辨率 ToF 分布在 ANYmal 周身，只负责近场几何。

### 系统结构

    distributed ToF sensors
       around robot body
            ↓
    synchronized range measurements
            ↓
    local terrain reconstruction
            ↓
    near-field obstacle map
            ↓
    obstacle avoidance
    + footstep planning

传感器分布本身就是系统设计的一部分：不是追求单个传感器高分辨率，而是用多个低成本测距点消除覆盖盲区。

### 结果

论文报告即使 ToF 分辨率更低、噪声更高，也能实现厘米级 local mapping，并提供足够几何信息支持可靠 perceptual locomotion、near-field obstacle avoidance 和 footstep planning；成本、能耗和系统复杂度明显低于多深度相机方案。

### 传感器假设与鲁棒性

ToF 很适合近距离，但玻璃、黑色低反射表面、斜入射以及阳光 IR 干扰仍可能带来 invalid / biased range。系统不能只融合“有数值的点”，还应该维护每个 sensor 的：

    valid_ratio
    saturation
    incidence_geometry
    last_valid_time
    noise_estimate

### 可复现性

Oxford Dynamic Robot Systems Group 已提供官方项目页；论文接受 IEEE RA-L 2026。项目目前最适合作为传感器布局和近场融合参考，而不是假设有一个即插即用 ROS package。

### 适合谁关注

机器狗楼梯、近场避障、ANYmal / Go2 / 自研四足、低功耗平台，以及希望补足 MID360 / 深度相机盲区的团队。

### 工程落地启发

对于前后 MID360 + 水平 16 线的机器狗，ToF 最合理的位置不是替换 LiDAR，而是补在：

    脚前下方
    腹部边缘
    机身侧后方
    楼梯踏步盲区

然后只用于 0–1.5 m near-field safety / footstep veto。这样不会把低分辨率 ToF 强行承担全局建图任务。

[论文](https://arxiv.org/abs/2609.31008) · [Oxford 项目页](https://dynamic.robots.ox.ac.uk/projects/time-of-flight-anymal/)

## 5. Bundled Contact Gradients：硬接触更真实，但梯度太抖；只在接触附近做局部随机平滑

**时间回补：v1 提交于 2026-09-25 08:02 UTC。**

### 为什么重要

可微物理的一个长期矛盾是：

    soft contact
    → gradient 平滑
    → 容易优化
    → 但接触不够真实

    stiff contact
    → dynamics 更真实
    → 但一点点 state perturbation
       就可能改变 contact mode
    → gradient variance 爆炸

对 humanoid 动态动作，这个矛盾尤其严重，因为 sim-to-real 恰恰依赖真实接触冲击。

### BCG 的关键做法

Bundled Contact Gradients 不对所有状态一直做昂贵随机平滑，而是在检测到 stiff contact 后，只围绕当前接触 configuration 生成一小簇 randomized perturbation rollout，再聚合这些 rollout 的 gradient。

    nominal rollout
          ↓
    detect stiff contact
          ↓
    local bundle of perturbed states
          ↓
    differentiable rollouts
          ↓
    aggregate gradients
          ↓
    lower-variance policy gradient

它本质上把计算预算集中在“梯度最不可靠的 contact neighborhood”。

### 真机意义

作者展示了 dynamic motion 在 differentiable simulator 中训练后，zero-shot 迁移到真实 Unitree G1。这说明 contact smoothing 不只是让 loss 更好看，而是在“保持硬接触物理 fidelity”和“让一阶优化还可用”之间找到更好的折中。

### 动力学假设与风险

局部 bundle 的扰动尺度非常关键。太小无法跨过 contact-mode discontinuity；太大又会把不相关 dynamics 混进 gradient。

建议训练 telemetry 中保留：

    contact_stiffness
    bundle_radius
    gradient_variance
    contact_mode_switch_rate
    sim-real contact residual

否则很难判断 policy 不稳定究竟来自控制目标，还是 gradient estimator 本身。

### 可复现性

作者提供公开项目页和视频 / supplementary info。即使暂时不使用同一 simulator，也可以复用“只在 contact instability 区域增加 randomized gradient estimate”的思想。

### 适合谁关注

Unitree G1、人形动态控制、可微仿真、接触丰富 RL、sim-to-real、希望用 first-order optimization 但又不想把 contact 软化得太假的团队。

### 工程落地启发

对楼梯 / 跳跃任务，真正值得随机化的不一定是整条 rollout，而是脚落地、离地、碰撞切换前后的短窗口。把计算集中在 hybrid transition 附近，比全程均匀增加 sample 更划算。

[论文](https://arxiv.org/abs/2609.30951) · [项目页](https://bundledcontactgradients.github.io/)

## 6. InternW0-Δ：20K+ 小时开放数据，把“未来变化”蒸馏给 Action Expert，而不是在线生成完整未来视频

**时间回补：v1 提交于 2026-09-25 15:24 UTC。**

### 为什么重要

World Action Model 的问题一直不是“未来视频有没有用”，而是如何把视觉未来真的转成动作收益，同时又不让部署 latency 被 video generation 吃掉。

InternW0-Δ 采用 Mixture-of-Transformers，把 video expert 和 action expert 放进同一个系统，但保留独立参数和 masked interaction；冻结 VLM 提供 task-conditioned scene semantics，4D foundation model 则在训练阶段提供 geometry / motion prior。

### 架构重点

    current / recent observations
          ↓
    video expert
       +
    frozen VLM semantics
       +
    action expert
          ↓
    directed attention
          ↓
    action generation

训练阶段另外加入：

    future visual supervision
          ↓
    Causal Imprint queries
          ↓
    future-relevant scene-change representation
          ↓
    action expert

关键是推理时不需要真正 rollout future video，Causal Imprint 已经把“哪些未来变化对动作有用”压进可直接消费的 representation。

### 数据规模

作者将 robot demonstrations、UMI、egocentric human demonstrations 与 Ego2Robot 数据对齐到共同 state-action representation，形成超过 20K 小时的 processed corpus，并称这是同类最大的开放数据语料之一。

### 结果

项目页公开的结果包括 LIBERO-Plus 92.8%、RoboTwin Clean2Random 71.9%、RoboTwin Clean2Clean 90.0%、RoboDojo 23.9% 等；这些数字来自作者项目，应视为论文 / 项目自报结果，真正选型仍需在自己的 embodiment 和控制频率上验证。

### 可复现性

项目页已提供 Paper / Code / Models 入口，并声明将开放 training code、weights、infrastructure、data-processing pipeline，以及许可允许范围内的 processed data。

### 工程风险

20K 小时 heterogeneous data 的核心风险不是“数据不够”，而是不同 embodiment、action convention、camera setup 和 state frequency 的对齐误差。

如果以后做自有多平台预训练，建议所有 sample 显式保存：

    embodiment_id
    action_frame
    control_rate
    proprio_schema
    camera_calibration_version
    action_mask_reason

### 适合谁关注

VLA / WAM、机器人基础模型、多 embodiment 预训练、希望把 future prediction 的收益带进 action policy 但不愿承担在线视频生成成本的团队。

### 工程落地启发

对小团队最值得抄的不是 20K 小时规模，而是 Causal Imprint 这个训练 / 推理解耦思路：训练可以使用昂贵 future supervision，部署只保留一个便宜 predictive latent。

[论文](https://arxiv.org/abs/2609.31394) · [项目页](https://internrobotics.github.io/InternW0-Delta/)

## 7. Claude Sonnet 5.5：真正值得测试的是“同样任务完成得更快、更少步骤”，而不是只看新 Benchmark

**最新发布：Anthropic 于 2026-09-28 正式发布。**

### 突破性工程价值

Sonnet 5.5 的定位不是取代 Opus 5.5，而是把大量 well-scoped coding / document / everyday agent work 放到更快、更低成本的模型上。

官方信息：

- 模型 ID：claude-sonnet-5-5
- 输入：2 美元 / 百万 token
- 输出：10 美元 / 百万 token
- cache read：0.20 美元 / 百万 token
- 官方称输出速度比 Sonnet 5 快 30% 以上
- 官方称多数任务单任务成本最多低约 30%
- 支持 adaptive thinking 与 low / medium / high / xhigh / max effort

价格与 Sonnet 5 相同，所以所谓“更便宜”主要来自更少 token / tool step，而不是单 token 降价。

### 官方 Coding Benchmark 怎么看

Anthropic 报告 Terminal-Bench 4.0 为 70.6%，CursorBench 4.0 为 55.5%，并给出 FrontierCode 等结果。

这些数字可以说明模型值得试，但不能直接回答“是否应该替换自己的默认 Coding Agent”。真正有意义的是固定：

    same repo
    same task
    same tool permissions
    same harness
    same max cost / timeout

然后记录：

    task success
    wall-clock
    output tokens
    tool calls
    test retries
    human corrections

### 是否适合真实研发流程

对于范围明确的 bug fix、文档修改、简单重构，可以优先测试 Sonnet 5.5 Medium / High；复杂架构、长时间开放式任务仍应和 Opus 5.5 / GPT-6 现有路线一起 A/B，而不是按单个公开 benchmark 做全局切换。

### 权限 / 安全风险

模型更快意味着高权限 agent 也可能更快地产生大量副作用。模型升级不应该自动改变：

    filesystem sandbox
    network allowlist
    write approvals
    idempotency policy
    merge / release gate

### 工程落地启发

模型升级时把“质量”和“单位任务成本”拆开测。一个模型即使单 token 价格没变，只要少 30% 无用 retrieval / test retry / tool call，真实 CI 成本就可能显著下降。

[Anthropic 官方发布](https://www.anthropic.com/claude-sonnet-5-5) · [迁移指南](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) · [GitHub Copilot 上线说明](https://github.blog/changelog/2026-09-28-claude-sonnet-5-5-in-github-copilot/)

## 8. Coding Agent 成本画像：Agent 自己生成 Skill，往往不如开发者写一个高层 Skill

**时间回补：v1 提交于 2026-09-25 02:54 UTC。**

### 突破性工程价值

Coding Agent 的成本浪费很难从 token 总数看出根因。作者对 Claude Code 和 Mini-SWE-Agent 的 1,200 条 SWE-bench Verified trajectory 做行为分析，把最常见浪费拆成三类：

1. subsumed retrieval：后一次检索包含了前一次检索信息，前面的读取基本白做；
2. similar script generation：重复生成结构非常相似的一次性脚本；
3. test re-execution：没有新证据的情况下重复跑相同或近似测试。

这三类行为出现在 79%–98% 的任务中，最高占到 22.75% task cost。

### 三种缓解策略的结果很反直觉

作者在 10K+ held-out SWE-bench Verified / Pro trajectory 上比较：

    structure-aware retrieval
    agent-synthesized skills
    developer-designed skills

结果并不是“更智能的 retrieval 一定省钱”。结构感知 retrieval 会增加自身开销、改变 Agent delegation，最差情况下成本反而提高 28.14%。

Agent 自己总结的 Skill 往往偏低层、trace-specific，例如“先跑这个命令，再 grep 那个文件”，很容易过拟合某条历史轨迹。

真正有效的是开发者设计的高层、trace-agnostic Skill，例如：

    先建立失败最小复现
    修改后只跑受影响测试
    扩大到完整 regression 前先验证局部假设
    已读取的静态配置不要重复读取

这类 Skill 最多降低 41.73% 成本，约为 Agent 自己生成 Skill 最大收益的两倍。

### 为什么对 Vibe Coding 很实用

这说明 Skill 不应该成为“把过去 session 总结成更长 prompt”的仓库。真正高价值 Skill 更像工程策略：

    invariant
    decision rule
    stop condition
    escalation rule

而不是历史命令流水账。

### 风险与边界

这些结果来自 SWE-bench 类任务，具体百分比不能直接外推到大型 C++、Android 或 ROS2 仓库。但三类浪费非常容易用自己的 telemetry 验证。

### 工程落地启发

建议给 Agent trace 加三个简单指标：

    duplicate_read_bytes
    similar_generated_script_count
    repeated_test_without_code_change

每周挑最贵的十条任务，不让 Agent 自动写 Skill，而由工程师把真正稳定的决策原则提炼成 5–20 行 Skill，再做固定 A/B。

[论文](https://arxiv.org/abs/2609.30725)

## AI Coding 实战技巧精选

### 技巧 1｜升级 Sonnet 5.5 不要手工全仓替换，直接让 Claude Code 跑官方迁移 Skill

- **来源**：Anthropic Claude Platform 官方迁移指南，2026-09-28：[Migrating to Claude Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide)。
- **一句话结论**：如果项目里散落了 Claude API model ID、thinking 参数、prefill 和 effort 配置，先跑官方迁移 Skill，让它改完可机械修改的部分，再人工检查 checklist。
- **具体怎么做**：
  1. 在项目根目录打开 Claude Code。
  2. 运行：

        /claude-api migrate this project to claude-sonnet-5-5

  3. 按提示确认迁移范围：整个 working directory、子目录或指定文件。
  4. 让 Skill 完成 model ID swap、breaking parameter changes、prefill replacement 与 effort calibration，再逐项处理它输出的人工验证清单。
- **适合什么场景**：Node/Python Claude API 项目、Bedrock / Claude Platform on AWS、多个文件共享 model 配置的 Agent 后端。
- **注意**：自动迁移只负责代码层兼容，不代表性能等价。迁移后仍要重新跑自己的 regression，并重新扫 low / medium / high effort；不要直接继承旧 Sonnet 的成本 / 延迟阈值。

### 技巧 2｜今天就检查 GitHub Self-hosted Runner 版本，避免 Agent CI 突然不接 Job

- **来源**：GitHub 官方 Changelog，2026-09-28：[Self-hosted runner version enforcement date has moved](https://github.blog/changelog/2026-09-28-self-hosted-runner-version-enforcement-date-has-moved/)。
- **一句话结论**：GitHub Enterprise Cloud 从 2026-09-29 开始全面执行 runner 最低版本规则；低版本 runner 即使昨天还能跑，今天也可能停止接 workflow job。
- **具体怎么做**：
  1. 先在 runner fleet 中盘点版本；低于 2.329.0 的 runner 连注册 / 重新注册都不允许。
  2. 不要只满足注册最低版本：GitHub 对“执行 workflow job”还有更高的 runtime minimum，现有已注册 runner 也会被停止调度。
  3. 升级 runner 后，跑一条真实 Agent / build / test workflow 验证标签、权限、缓存和容器挂载都正常。
  4. 企业 fleet 可以接 GitHub 新的 runner-version deprecation REST API，自动提前告警 registration / runtime deprecation date。
- **适合什么场景**：Codex / Copilot / Claude 生成 PR 后由 GitHub Actions 自动 build、测试、CodeQL、仿真或部署，且使用 self-hosted GPU / ARM / 内网 runner。
- **注意**：这次 enforcement 影响 GitHub Enterprise Cloud；GitHub Enterprise Server 不在本次变更范围内。不要等 Agent PR 堆积后才发现 runner 全部 offline。

## 经典论文回顾

### KLD-Sampling：粒子数应该跟着 belief 的复杂度变，而不是永远固定 500 / 2000 / 10000

Dieter Fox 的 **KLD-Sampling: Adaptive Particle Filters** 发表于 NIPS 2001，后续完整版本以 **Adapting the Sample Size in Particle Filters Through KLD-Sampling** 发表于 IJRR 2003。它是自适应粒子滤波中最经典的工作之一，也非常适合和今天的 Transformer-MCL 一起重读。

### 核心问题

粒子滤波的固定 sample count 天生很浪费：

    已经高度确定的单峰 posterior
    → 仍然保留几千粒子
    → 浪费 CPU

    kidnapped robot / 对称环境 / 多峰 posterior
    → 仍然只有几百粒子
    → 很容易把正确 hypothesis 采没

KLD-Sampling 的核心不是“按照 likelihood 高低调粒子数”，而是直接约束粒子近似 posterior 的分布误差。

### 关键数学思想

将 posterior 近似成离散 histogram / occupied bins，要求以概率 1−δ，使 sample-based approximation 与真实 posterior 的 KL distance 不超过 ε。

因此所需样本数主要随：

    occupied belief bins
    error bound ε
    confidence δ

变化。

belief 越集中，occupied bins 越少，所需粒子自动下降；belief 越分散、多峰越强，粒子数自动增大。

### 为什么 likelihood-based 自适应还不够

一个对称环境里可能有四个几乎同样可信的位置 hypothesis。平均 measurement likelihood 可以和单峰状态差不多，但表示四峰明显需要更多粒子。

KLD-Sampling关注的是 belief 的空间复杂度，而不是只看“传感器看起来匹配得好不好”。

### 当年为什么重要

原论文指出实现和计算 overhead 都很小，但在 mobile robot localization 实验里相对固定粒子数以及此前的 adaptive 方法能显著提高效率。

这使 MCL 从“工程师手调 particle count”进一步变成“根据当前不确定性自动分配计算预算”。

### 今天仍在使用的思想

现代系统即使换成 learned observation model，这个原则完全没有过时：

    observation model
    → 可以是 LiDAR likelihood
    → 也可以是 Transformer / neural descriptor

    belief complexity
    → 仍然决定需要多少 hypothesis

今天的 construction-mesh MCL 用 uncertainty-aware decoder 与 model-hypothesis injection 解决 ambiguity / particle depletion；KLD-Sampling 则从另一个维度回答“当前到底要保留多少粒子”。

### 已被后续扩展的部分

今天的粒子系统还会使用 adaptive resampling、proposal learning、mixture model、GPU batch likelihood、multi-resolution state space，以及和 factor graph / scan registration 的 hybrid localization。

KLD 的固定 histogram discretization 在高维 SE(3) 中也会面临 bin 设计与维数问题，所以不能机械地把 2D AMCL 参数原样搬到 6DoF。

### 可复现性

不需要任何神经网络就能复现。拿 ROS2 Nav2 AMCL 或自己的 MCL，对三种场景做测试：

    1. 已收敛单峰
    2. 重复长走廊多峰
    3. kidnapped robot

固定粒子数与 KLD adaptive 分别记录：

    particles_per_update
    CPU time
    relocalization latency
    posterior multimodality
    false convergence

### 对当前工程项目的重新解读

真正值得借鉴的是“估计器也要做 compute scheduling”。

如果以后把 Transformer observation model 放到 3D LiDAR 全局重定位中，可以让：

    model uncertainty
    + occupied belief volume
    + relocalization mode

共同决定粒子预算。

tracking 状态可能只需少量粒子；失锁 / 长走廊 ambiguity 时再把预算拉高。比永久把 GPU / CPU 跑满更适合嵌入式机器人。

[NeurIPS 2001 论文页](https://papers.nips.cc/paper_files/paper/2001/hash/c5b2cebf15b205503560c4e8e6d1ea78-Abstract.html) · [IJRR 2003 完整版 PDF](https://rse-lab.cs.washington.edu/papers/adaptive-ijrr-2003.pdf) · [DOI](https://doi.org/10.1177/0278364903022012001)

## 今日结论

今天最值得带走的系统思想，是**“学习模型负责提供更好的信息，但不应该吞掉估计、控制和工程约束本身。”**

建筑 Mesh 重定位没有让 Transformer 直接替代 localization，而是把它变成 MCL 的 observation model；SeA-RVINS 没有指望一个万能 robust kernel 修所有错误，而是把 semantic track rejection、GNSS correlation 和 ambiguity lifecycle 分别处理；Wind-Preview MPC 也没有用网络猜风，而是引入真实 preview measurement，让控制器在扰动发生之前就拥有证据。

四足 ToF 工作同样提醒我们，传感器选型不应只看“谁点最多、精度最高”。近场 footstep safety 的关键可能是 coverage、blind spot、功耗和 latency，而不是再增加一颗高端 3D 传感器。

BCG 和 InternW0-Δ 则代表两种不同的训练 / 部署解耦。BCG 把额外计算集中到训练中的 stiff-contact gradient estimation，换取真机部署时更可靠的 policy；InternW0-Δ 在训练时使用 future video 和 4D teacher，部署时把未来信息压成 Causal Imprint latent，不要求在线生成完整未来。

AI Coding 侧也出现相同规律。Sonnet 5.5 的价值如果真实存在，应该表现为更少 tool step、更短 wall-clock 和更低每任务成本，而不是“模型名更新了”。Coding Agent 成本研究进一步说明，Agent 自己总结出来的低层 Skill 未必是好资产；最有价值的是工程师写出的稳定 decision rule。

今天的 KLD-Sampling 经典回顾把这些方向串起来：算力应该随着不确定性和问题复杂度分配。定位如此，MPC rollout 如此，VLA inference 如此，Coding Agent reasoning / test budget 也如此。

如果把整期压成一句话：

> **成熟的智能系统不是一直把模型和算力开到最大，而是让传感器证据、不确定性、任务阶段和工程约束共同决定“现在该算什么、算多少、什么时候不该相信”。**

## 最值得深入研究或尝试复现的方向

1. **Mesh → Synthetic LiDAR → MCL 小样。** 从现有 Revit / BIM 导出的 mesh 里模拟 MID360 scan，先不训练大模型，只验证 synthetic-to-real point distribution 与多房间 ambiguity，再接 learned observation model。
2. **LIO / RTK-VIO Factor Admission Gate。** 给视觉 landmark 和 RTK factor 增加进入长期图之前的质量门控，记录 rejected observation 的原因，比较“早拒绝”与“全写入 + robust kernel”谁更稳。
3. **无人机 Wind Preview。** 用廉价风速 / 压差传感器先做 time-lag correlation，确认“前置多少厘米能获得多少毫秒 preview”，再决定是否值得进 MPC，不要一开始就做复杂控制器。
4. **机器狗近场 ToF Ring。** 在脚前下方、腹部边缘和机身侧后方增加小型 ToF，只做 0–1.5 m safety layer，与现有 MID360 / 16 线地图独立，专测楼梯踏步和近身障碍漏检。
5. **Contact-Localized Gradient Smoothing。** 对可微仿真只在 foot touchdown / liftoff / impact 周围启用 perturbation bundle，测 gradient variance 和 sim-to-real，而不是全轨迹均匀加随机化。
6. **Coding Agent Cost Telemetry。** 在 Claude Code / Codex trace 中记录重复读取字节、无代码变化的重复测试、一次性脚本相似度；先用数据找前三个浪费点，再由工程师写高层 Skill。
7. **模型升级固定 A/B。** Sonnet 5.5 与现有模型用同一仓库、同一任务、同一 permission、同一 timeout 比 success / wall-clock / token / tool-call / human correction，不直接使用公开 benchmark 做路由结论。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [Transformer-based Monte Carlo Localization in Construction Meshes](https://arxiv.org/abs/2609.31357)
- [SeA-RVINS](https://arxiv.org/abs/2609.30814)
- [Onboard Wind-Preview MPC](https://arxiv.org/abs/2609.31185)
- [Quadruped Obstacle Avoidance and Footstep Planning with Distributed ToF](https://arxiv.org/abs/2609.31008)
- [Oxford ANYmal ToF 项目页](https://dynamic.robots.ox.ac.uk/projects/time-of-flight-anymal/)
- [Bundled Contact Gradients](https://arxiv.org/abs/2609.30951)
- [BCG 项目页](https://bundledcontactgradients.github.io/)
- [InternW0-Δ](https://arxiv.org/abs/2609.31394)
- [InternW0-Δ 项目页](https://internrobotics.github.io/InternW0-Delta/)
- [Claude Sonnet 5.5 官方发布](https://www.anthropic.com/claude-sonnet-5-5)
- [Claude Sonnet 5.5 迁移指南](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide)
- [Analyzing and Mitigating Cost-Inefficient Behaviors in Coding Agents](https://arxiv.org/abs/2609.30725)
- [GitHub Self-hosted Runner 版本执行规则](https://github.blog/changelog/2026-09-28-self-hosted-runner-version-enforcement-date-has-moved/)
- [KLD-Sampling: Adaptive Particle Filters](https://papers.nips.cc/paper_files/paper/2001/hash/c5b2cebf15b205503560c4e8e6d1ea78-Abstract.html)
- [Adapting the Sample Size in Particle Filters Through KLD-Sampling](https://rse-lab.cs.washington.edu/papers/adaptive-ijrr-2003.pdf)
