---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-25"
date: 2026-09-25 09:00:00 +0800
description: "关注 DAVIO 稠密单目惯性 SLAM、超大范围城市 UAV 几何定位、LEAP-CBF 鲁棒安全、丢包下分布式 Koopman-MPC、Spike-MPPI、LiMA/PointCast 与 SWE-Flux。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-25

## 摘要

截至 2026-09-25 早间（Asia/Shanghai），arXiv Robotics 最新公开批次为 2026-09-24，共 103 条；Software Engineering 同日共 35 条。本期首先从该批次中筛选，再与 robotics-brief-covered-items.md 按标题、arXiv ID、DOI、项目页和仓库地址强制去重。由于本期入选论文的 v1 均提交于 9 月 23 日 UTC，距离本次生成已超过 24 小时，因此统一明确标为“时间回补”，不把公开批次日期包装成原始提交日期。最新列表见 [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) 与 [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

今天 SLAM / 定位侧最值得看的两项工作，一项在解决“VIO 为什么非得等视差足够才能启动”，另一项在解决“没有 GNSS、视觉外观又不可靠时，城市 UAV 怎么在数百平方公里范围内做全局定位”。DAVIO 使用同一个多视图深度模型同时服务启动和稠密建图：五帧图像与预积分 IMU 构成 feature-free 线性初始化，再由真实 VIO pose 对 feed-forward depth 进行 metric conditioning。Large-Scale Geometric Map-Based Localization 则绕开卫星图像外观检索，以向下相机检测到的建筑布局和 footprint 数据库做几何匹配，在约 452 km²、最多 27.7 万栋建筑的搜索空间里仍取得 71.4% Recall@1。

控制侧今天的共同主题是“安全余量要能量化，而不是只看有没有违反约束”。LEAP-CBF 用 Least-Effort Adversarial Potential 表示“扰动至少要付出多少累计努力才会把系统推向失败”，再由此构造鲁棒 safety filter；Safety-Filtered Distributed Koopman-MPC 则把邻居通信与硬安全解耦：通信轨迹只用于 Koopman 预测，本地传感器和货架几何独立构造最终 hard-constrained QP，因此 packet loss 不会顺带把 collision constraint 一起丢掉。在 8 机器人仓库仿真中，完整方法 20/20 trial 无碰撞，而缺少最终安全投影的 predictive Koopman-MPC 只有 1/20 无碰撞。

MPPI 方面，Spike-MPPI 给了一个很值得实践的提醒：有限 rollout 预算下，真正决定搜索效率的不只是 sample 数量，还有 proposal distribution 的时间结构。作者用简化 motoneuron dynamics 产生时序相关扰动；结果显示控制平滑性明显改善，而一部分收益可以由 spectrum-matched Gaussian 复现，另一部分来自更高阶统计结构。这意味着调 MPPI 时，不应只盯温度、噪声方差和 rollout 数，还应该把“噪声在时间轴上长什么样”当成一等参数。

机器人世界模型侧，LiMA 与 PointCast 分别从时间尺度和状态表示上降低世界模型落地成本。LiMA 把稀疏长时 intent generation 与高频 motion refinement 异步解耦，相比 Cosmos-Policy 报告 45.8% latency reduction；PointCast 则用 3D point-set 作为统一状态表示，同一 19.8M diffusion-transformer 架构覆盖刚体、布料、绳索和多关节柜体，并可冻结后放进 sampling-based MPC。

AI Coding 侧，SWE-Flux 很值得进入自己的 Agent regression suite。它不是再做“给仓库提问、由另一个 LLM 判答案”，而是从真实 Python 仓库的 instrumented test execution 自动采集 gold answer，构造 480 个 repository-level runtime reasoning 问题。五个模型中最好只有 37% accuracy，尤其容易在 dataflow、inter-procedural execution、精确程序状态和 test-suite aggregation 上失败。它再次说明：Coding Agent 真正薄弱的地方，经常不是读懂一段函数，而是跟踪真实程序执行过程中状态到底如何流动。

最近 24 小时没有发现需要新增报道的 OpenAI、Anthropic、Google DeepMind 或 xAI 通用旗舰正式发布；9 月 22 日的 GPT-6 Sol / Luna、Claude Opus 5.5 与 9 月 21 日的 Grok 4.7 均已进入历史覆盖索引，因此今天不重复填充模型栏目。

## 1. DAVIO：用同一个 Feed-Forward Depth 模型同时解决 VIO 启动和稠密建图

**时间回补：v1 提交于 2026-09-23 11:21 UTC。**

### 为什么重要

传统单目 VIO 的启动通常要等运动产生足够视差，先通过 feature geometry 建立尺度、重力、速度和 bias 的可观条件，再进入正常滤波或优化。对“拿起来就走”、狭窄空间起飞、低纹理室内等场景，这段等待本身就是产品问题。

与此同时，VIO 一旦启动，经典系统往往只保留 sparse landmarks；如果再额外接一个 feed-forward dense geometry model，又容易出现另一个问题：网络输出的几何尺度与 VIO 的 metric scale / gravity 不一致。

DAVIO 的思路很统一：一个多视图 Depth Anything 3 模型既参与启动，又参与后续稠密 map construction，而 metric authority 始终由 IMU + VIO 提供。

### 算法模块

启动阶段：

    five-image window
    + preintegrated IMU
            ↓
    feed-forward multi-view geometry
            ↓
    feature-free linear system
            ↓
    condition / robustness check
            ↓
    VIO bootstrap
            ↓
    buffered replay

跟踪 / 建图阶段：

    metric VIO poses
            ↓
    condition Depth Anything 3
            ↓
    dense depth
            ↓
    ray-only residual scale correction
            ↓
    preserve metric camera baselines
            ↓
    gravity-preserving submap graph
    + drift-gated revisits

“只沿 viewing ray 修正 residual scale”很关键，因为这样不会随意破坏相机 baseline 的 metric geometry。

### 传感器与假设

最低配置仍然只是 monocular camera + IMU。系统把 feed-forward geometry 当作强 prior，但没有让网络直接拥有 metric truth；尺度和重力仍由惯性约束负责。

这意味着 DAVIO 的真正价值不是“用深度网络替代 VIO”，而是用 dense prior 改善 VIO 最脆弱的启动与地图表示阶段。

### 实时性、鲁棒性与风险

论文在 EuRoC 上报告更早启动、更低定位误差，并在相同 pose 条件下得到更好的 dense mapping；在 building-scale ORI 序列中，使用真实 odometry 替代 GT pose 后，其地图质量退化也小于对比方法。作者将系统定位为 real-time dense metric SLAM，并声明代码已发布。

最大风险是 feed-forward geometry 的 domain shift。如果深度模型在镜面、低光、重复纹理或极端视角下系统性出错，而初始化器又把这个 prior 当作高置信几何，就可能比“初始化失败”更危险。工程接口最好显式保留 init_condition_score、inertial_excitation、depth_prior_consistency、bootstrap_residual 与 map_scale_consistency，不要只返回 initialized=true。

### 适合谁关注

单目 VIO、轻量无人机、移动机器人、希望 camera+IMU 同时获得 metric trajectory 和 dense map 的团队。

### 工程落地启发

不需要一开始替换现有 OpenVINS / VINS-Fusion。可以先把 feed-forward multi-view geometry 作为“初始化 sidecar”，只在原 initializer 判定低视差或启动过慢时启用，然后比较首个可信 pose 的时间、bias 收敛和错误初始化率。

[论文](https://arxiv.org/abs/2609.27702)

## 2. 超大范围 UAV 几何定位：不用卫星图像外观检索，只匹配城市建筑布局

**时间回补：v1 提交于 2026-09-23 14:53 UTC；IROS 2026。**

### 为什么重要

GNSS-denied UAV 的全局定位经常走 aerial-image retrieval：将机载图像和卫星 / 航拍底图库做视觉匹配。问题是季节、阴影、建筑翻新、相机波段、拍摄时间和视角变化都会影响 appearance，而且搜索区域越大，视觉描述子的混淆越严重。

这篇工作把“城市本身的几何布局”当成全局指纹：向下相机只负责检测建筑，再把局部建筑 arrangement 与已有 building-footprint database 做匹配。

### 算法模块

    downward camera
          ↓
    building detection
          ↓
    multi-frame accumulation
          ↓
    local building arrangement
          ↓
    triangle structure
    + per-building shape
          ↓
    reference footprint database
          ↓
    global location candidate

描述子不依赖建筑纹理，而依赖附近建筑之间的相对空间关系和单栋 footprint 形状。

### 传感器与地图假设

需要向下相机与可查询的建筑 footprint 数据库。对于 OpenStreetMap / 城市 GIS 较完善区域，这个假设现实可行；对郊野、森林、建筑稀疏工业区则未必适用。它解决的是 global localization / place retrieval，而不是完整高频 odometry，所以实际飞行仍应与 VIO / LIO / IMU 组合。

### 结果与风险

七次飞行、四个 municipality 的实验中，约 113 km² 与约 254 km² 搜索区 Recall@1 均为 100%；约 452 km²、最多约 277,000 栋建筑时 Recall@1 为 71.4%。论文中的视觉基线在 254 km² 与 452 km² 搜索范围下降到 0% Recall@1。

几何方法不怕光照，但会怕地图陈旧、建筑 footprint 错误、临时建筑、视场内建筑过少，以及大量规则街区产生相似 topology。因此应返回 top-K hypothesis 与 geometric margin，而不是一个不可质疑的单点定位。

### 适合谁关注

GNSS-denied UAV、城市巡检、跨城区重定位、希望减少卫星影像依赖的视觉导航团队。

### 工程落地启发

对无人机全局定位，可以明确分层：local metric tracking 用 VIO / LIO，global hypothesis generation 用 building geometry retrieval，最终再做 local geometry / inertial consistency verification。比让一个 global image descriptor 同时承担召回和最终定位更容易控制错误模式。

[论文](https://arxiv.org/abs/2609.28225)

## 3. LEAP-CBF：安全余量改成“扰动还要付出多少努力才能把我推坏”

**时间回补：v1 提交于 2026-09-23 16:36 UTC。**

### 为什么重要

经典 robust CBF 最大的难点之一，是需要给 disturbance 一个明确的瞬时 bound；bound 设太小不安全，设太大又会极度保守。高维机器人、输入受限系统中，这种 worst-case envelope 很难手工构造。

LEAP-CBF 换了一种安全坐标：不是只问“当前位置离 unsafe set 多远”，而是问一个对手至少需要累积多少 disturbance effort，才能把当前状态推到失败。这个量就是 Least-Effort Adversarial Potential。

### 算法模块

    state
      ↓
    adversarial disturbance process
      ↓
    minimum cumulative effort to failure
      ↓
    LEAP value
      ↓
    CBF / robust safety filter

作者用 on-policy deep RL 学 LEAP，而不是要求手工解析求解高维 HJ / robust barrier。

### 动力学假设、真机与风险

保证依赖“扰动累计 effort 有上界”这一建模。它和“每一拍 disturbance 都有同一个 box bound”不同，因此很适合冲击、阵风、推搡等时间上不均匀的扰动，但前提是 effort metric 和真实风险匹配。

论文先在多智能体仿真验证，再在 quadruped 与 quadrotor 硬件实验中展示真实扰动 / 不确定性下的结果。工程上值得记录 leap_margin、estimated_disturbance_effort、cumulative_effort_budget 与 filter_intervention。

学习到的 LEAP 仍然只是近似 certificate；OOD state、训练中没覆盖的接触模式、错误 disturbance metric 都可能让 margin 过度乐观。生产系统仍应保留 joint / tilt / thrust / workspace 等 deterministic hard bounds。

### 适合谁关注

安全 RL、CBF、四足 / 无人机抗扰控制、无法轻易写解析 robust CBF 的高维系统。

### 工程落地启发

现有 safety filter 可以先不替换，额外训练一个“recoverability / adversarial effort” critic 做 shadow telemetry。先看它能否在传统 barrier 还没越界前提前预警，再决定是否进入正式 filter。

[论文](https://arxiv.org/abs/2609.28364)

## 4. Safety-Filtered Distributed Koopman-MPC：通信丢包不能顺便把安全约束也丢掉

**时间回补：v1 提交于 2026-09-23 07:28 UTC。**

### 为什么重要

分布式 MPC 常见做法是从邻居发来的未来 trajectory 同时构造邻居预测和 collision avoidance constraint。这样一旦 packet loss，性能信息和安全约束会一起消失。这篇工作将“性能预测”和“硬安全”彻底拆开。

### 算法模块

性能层：

    received neighbor trajectory
            ↓
    Koopman prediction
            ↓
    distributed MPC command

执行前 safety layer：

    local sensing
    + shelf geometry
    + bounded snapshot / direction error
            ↓
    hard constrained QP projection
            ↓
    applied input

有限 zero-order-hold 周期内保持 supporting-plane clearance 的约束是 hard row，不允许 safety slack；更高阶 anticipatory rows 才允许为了性能而放松。

### 结果

8 机器人仓库匹配仿真、120 ms 控制周期并注入 packet dropout、nonlinear drift、bounded input/speed 与货架约束时：

- 完整方法 20/20 trials 无碰撞；
- 达到 160/160 robot goals；
- predictive Koopman-MPC 没有最终 projection 时只有 1/20 无碰撞；
- 38,400 组 hard-row 在线 feasibility test 全部通过。

fleet sweep 中一直到 16 robots 都保持 collision-free / hard-row feasible；20 robots 出现边界失败前，online feasibility margin 已先变负。

### 动力学假设与风险

目前证据仍是 simulation，不是真仓库机器人群。证明依赖 snapshot error、directional plant error、hold interval 等上界。但它给了一个非常好的工程原则：网络只应该影响性能预测，不应该成为安全约束唯一的数据来源。

### 适合谁关注

多机器人仓储、分布式 MPC、网络不稳定机器人群、AGV / AMR fleet。

### 工程落地启发

如果现在 collision constraint 完全来自其他机器人广播 trajectory，可以增加 independent local safety path：remote plan 只改善 prediction；local LiDAR / UWB / geometry 负责 last-mile hard safety。这样 packet loss 最差只是“走慢一点”，而不是“突然失去避碰”。

[论文](https://arxiv.org/abs/2609.27463)

## 5. Spike-MPPI：有限 Rollout 下，噪声的“时间形状”本身就是控制器设计变量

**时间回补：v1 提交于 2026-09-23 16:03 UTC。**

### 为什么重要

MPPI 常见调参集中在 rollout 数 K、horizon、temperature λ 和 noise covariance Σ，但通常默认 control perturbation 是独立或简单相关的 Gaussian noise。

有限计算预算下，这个 proposal 决定了采样到底在搜索什么样的控制序列。如果 proposal 大量产生高频抖动，而真实机器人可执行动作本来就是低频、平滑的，大量 rollout 从一开始就是浪费。

### 方法

Spike-MPPI 用简化 motoneuron dynamics 产生时序结构化 perturbation，再进入标准 MPPI rollout 与指数 cost weighting。论文同时加入 spectrum-matched Gaussian baseline，用来区分仅仅因为频谱更合理得到的收益，以及 Spike proposal 更高阶统计结构额外带来的收益。

### 结果与边界

MuJoCo Ant 的 torque-actuated 与 antagonistically actuated 两种设置中，structured sampling 明显改善 executed-control smoothness；任务 performance 的收益则依 rollout 条件和 actuation 而变。Spectrum-matched Gaussian 能复现相当一部分行为，但不能解释全部差异，说明 proposal 的高阶结构也有作用。

### 为什么工程上重要

这个结论比“Spike 一定优于 Gaussian”更有价值：先把 MPPI noise 的 temporal spectrum 调到与 actuator / task 匹配，可能就能获得很大一部分收益，然后再考虑更复杂的 non-Gaussian proposal。

### 风险

目前只有 MuJoCo Ant 仿真，不能直接推到无人机、轮足或机械臂真机。不同 actuator bandwidth 对最佳 proposal 可能完全不同。

### 适合谁关注

MPPI、sampling MPC、无人机 / 四足控制、正在受 rollout 数限制的实时优化团队。

### 工程落地启发

在现有 MPPI 中增加 white Gaussian、low-pass / spectrum-shaped Gaussian、learned / structured proposal 三组 A/B；固定 K、horizon 和 dynamics，然后比较 task cost、control jerk、saturation rate、effective sample weight entropy 与 wall-clock。

[论文](https://arxiv.org/abs/2609.28325)

## 6. LiMA：长时想象与高频接触控制不要强迫同一个生成循环同步运行

**时间回补：v1 提交于 2026-09-23 17:31 UTC。**

### 为什么重要

灵巧操作同时需要两个完全不同的时间尺度：几秒到几十秒的长时任务意图，以及数十毫秒级的接触变化响应。VLA 长于语义和长时规划，但物理细节弱；World-Action Model 能预测未来，但 iterative generation latency 又很高。

让同一个大模型每一个高频动作都重新完成完整长时想象，会形成明显 temporal mismatch。

### 算法结构

LiMA 明确做成 asynchronous dual system：slow system 负责 sparse long-horizon spatiotemporal intent；Latent Schrödinger Bridge Coupling 用 entropy-regularized probabilistic transport 对齐稀疏 intent 与 dense trajectory；fast system 负责 dense high-frequency motion refinement。

### 结果

六项 bimanual dexterous manipulation task 中，LiMA 相比 Cosmos-Policy inference latency 下降 45.8%，overall success 70.8%，average subtask success 78.9%，并在 unseen scenario 中保持可用表现。

### 鲁棒性与风险

异步系统最大问题是 intent staleness：高层计划生成期间，物体可能已经被碰动，旧 intent 可能不再成立。产品里必须记录 intent_timestamp、intent_validity_region、fast_policy_deviation 与 force_replan_condition，不能只因为 slow model 终于返回结果，就无条件覆盖最新执行状态。

### 适合谁关注

双臂操作、VLA / WAM、端云分层推理、希望降低生成式策略 latency 的团队。

### 工程落地启发

这个结构可以迁移到更传统的机器人栈：1–2 Hz semantic / task planner + 20–100 Hz learned local policy + 200–1000 Hz deterministic controller。关键不是所有层“模型统一”，而是每层只负责自己能赶得上的时间尺度。

[论文](https://arxiv.org/abs/2609.28431) · [项目页](https://ccdcs.github.io/LiMA_repo/)

## 7. PointCast：用 Point Set 统一刚体、柜门、绳索和布料的世界模型

**时间回补：v1 提交于 2026-09-23 17:02 UTC。**

### 为什么重要

世界模型很容易陷入 representation fragmentation：刚体用 pose，柜门用 joint angle，绳索 / 布用 mesh / particles，机械臂用 end-effector pose。每种对象写一套状态定义，就很难训练一个统一 planner / model。

PointCast 选择一个很直接的公共语言：3D point set。

### 算法模块

状态由 object 3D points + end-effector 3D points 组成。每个 point 保留 identity，并监督自己的 trajectory，而不仅是监督最终点云形状。

模型是 19.8M 参数 diffusion transformer：recent point history 与 commanded EE motion 输入后，经 local/global alternating attention 与 EE cross-attention，预测未来 point trajectories。同一架构 / training recipe 覆盖 rigid、cloth、rope、multi-joint cabinet，但不同 regime 训练独立 checkpoint。

### 结果

随机仿真数据对四个 baseline 的同指标比较中，四种 regime 里三项第一、刚体第二。真实 teleoperation dataset 上，六个类别里四项 mean error 最低，另两项第二，并优于该数据集自己的模型。

冻结进 sampling-based MPC 时，每个 planning window 只做一次 network evaluation；四项仿真任务共 64 episodes，表现与 baseline 相当或更好。

### 假设与风险

Point identity 对训练很重要，但真实 perception 中 point correspondence / occlusion 不会天然完美。真实系统如果每一帧 point identity 都漂移，模型在训练中学到的 trajectory identity 优势可能缩水，因此 perception frontend 仍然是部署关键。

### 适合谁关注

机器人 world model、柔性物操作、双臂操作、sampling MPC、希望统一 rigid / articulated / deformable state representation 的团队。

### 工程落地启发

如果不想直接做 diffusion world model，也可以先把 planner 的状态接口统一成稳定 point entity，带 stable_id、xyz、confidence、object_id 和 timestamp，看 rigid / rope / cloth 是否能共享 downstream cost 和 tracking 工具，再决定是否训练统一 dynamics。

[论文](https://arxiv.org/abs/2609.28393) · [项目页](https://pointcast-wm.github.io/)

## 8. SWE-Flux：Coding Agent 真正难的是追踪“程序跑起来以后状态怎么流动”

**时间回补：v1 提交于 2026-09-23 17:46 UTC。**

### 突破性工程价值

很多代码 benchmark 仍然测试静态阅读、写 patch、最终 unit test 是否通过，或由另一个 LLM 判断回答是否合理。但真实排障经常需要回答：这组测试按顺序运行后哪个对象被修改了？异常在哪一层被捕获？某个 global state 在下一个 test 前到底是什么？这属于 repository-level dynamic execution reasoning。

### Benchmark 如何构造

SWE-Flux 从 12 个真实 Python repository 中构造 480 个 execution-grounded instance。最关键的是 gold answer 不是人工写，也不是 LLM judge，而是 instrument tests → execute real repository → harvest runtime oracle → generate question / answer instance。

覆盖 control flow、loops、program state、dataflow、exceptions、invariants，以及 single-test / multi-test aggregation。

### 结果

五个模型中，最好只有 37% accuracy。模型对 localized behavior 相对更好，例如 intra-procedural control flow、exception、简单 loop 和 local invariant；明显更弱的是 dataflow、inter-procedural execution、precise state reasoning 和 test-suite aggregation。

作者还通过 input perturbation 自动生成 fresh variant，接近 90% 选中实例能够产生有效新变体，而且对模型更难。

### 为什么适合真实研发流程

这很适合变成 Coding Agent 的“读代码 / 调 bug”回归集，因为答案来自真实执行，不需要相信 Agent 自述，也不需要另一个 LLM 当裁判。

### 风险与边界

它主要是 Python repository + tests 的执行推理，不等价于完整 SWE patch benchmark。但对公司内部仓库而言，构造类似动态 oracle 往往比手写上百道 QA 更便宜，而且可以随着代码变化自动更新。

### 工程落地启发

可以从现有 test suite 自动采集 function call trace、state snapshots、thrown / caught exceptions、DB mock mutations 和 fixture lifetime，然后让 Agent 在看不到 trace 的情况下回答，最后由 runtime oracle 自动评分。这能专门测出“Agent 看起来很懂代码，但实际上没跟上执行状态”的失败模式。

[论文](https://arxiv.org/abs/2609.28449)

## AI Coding 实战技巧精选

### 技巧 1｜C++ 大仓库先等 Whole Codebase Indexing 建好，再让 Agent 做跨文件重构

- **来源**：[GitHub 官方 Changelog，2026-09-22](https://github.blog/changelog/2026-09-22-faster-c-code-intelligence-with-whole-codebase-indexing/)。
- **一句话结论**：大型 C++ 仓库里，Agent 反复 grep / 重新解析 header 会浪费大量时间。GitHub Copilot CLI 现在默认建立持久 Whole Codebase Index（WCI），让 C++ language server 复用全仓符号、类型、include 和引用关系。
- **具体怎么做**：
  1. 第一次打开大型 C++ repo 后先让 WCI 完成，不要立刻给 Agent 下跨模块重构任务。
  2. 用 /lsp logs 查看 language server / indexing 进度。
  3. 确保项目有准确的 compilation information，例如正确生成 compile_commands.json；否则全仓索引解析出的 include / macro / type 关系也会失真。
  4. 如果刚修改 WCI 设置，重启 Copilot session，让新的索引策略生效。
- **适合什么场景**：ROS2、SLAM、CMake 大仓库、上百万行 C++、跨几十个 header 的重构 / API 迁移。
- **注意**：首次建索引会额外消耗时间和内存，真正收益来自后续复用。WCI 也不是编译器真值，最终仍要以真实 build / test 为准。

### 技巧 2｜给 Copilot / Coding Agent 接 OpenTelemetry，先定位“慢在模型还是慢在工具”

- **来源**：[GitHub Copilot OpenTelemetry 官方更新，2026-09-22](https://github.blog/changelog/2026-09-22-opentelemetry-in-the-github-copilot-app/)；[GitHub Docs](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference)。
- **一句话结论**：长 Agent session 不要只保存 final answer。把 LLM call、tool execution、token usage 和 session span 发到 OTel collector，出现“同一个任务今天突然慢 3 倍”时，才能区分模型延迟、工具卡顿还是调用次数膨胀。
- **具体怎么做**：
  1. 本地 Copilot CLI 可设置 COPILOT_OTEL_ENABLED=true，并设置 OTEL_EXPORTER_OTLP_ENDPOINT 指向自己的 collector。
  2. 企业环境在 managed-settings.json 的 telemetry 中统一指定 enabled、endpoint、protocol 和 serviceName；默认保持 captureContent=false。
  3. Dashboard 至少拆出 agent session wall-clock、LLM call count / duration、tool call count / duration、token usage、error / retry count。
  4. 给每次 regression run 写入 repo SHA、model、agent/harness version，避免不同版本的 trace 混在一起比较。
- **适合什么场景**：Copilot CLI / app、公司内部 Coding Agent、长任务、多个 MCP / connector、需要做成本与延迟 SLO 的团队。
- **注意**：Prompt / response 内容默认不采集是好事。只有在明确完成隐私审查后才考虑 captureContent；观测系统不应该为了 debug 把源代码、密钥或客户数据全部复制进 telemetry backend。

## 经典论文回顾

### Information-Theoretic Model Predictive Control：今天 Spike-MPPI 讨论“采样分布怎么设计”的理论起点之一

Grady Williams、Paul Drews、Brian Goldfain、James M. Rehg 与 Evangelos A. Theodorou 的 **Information-Theoretic Model Predictive Control: Theory and Applications to Autonomous Driving**，arXiv v1 于 2017 年发布，后发表于 IEEE Transactions on Robotics 2018。

### 核心问题

传统 gradient-based optimal control 需要可微 dynamics / cost，并可能在强非线性、非凸约束、复杂 learned dynamics 下难以实时求解。IT-MPC 选择直接在控制序列分布上做优化：对当前 nominal control sequence 加扰动并并行 rollout，计算 trajectory cost，通过 exponential / information-theoretic weighting 更新控制序列，执行第一拍后滚动 horizon。

### 关键数学思想

核心连接是 stochastic optimal control 与 relative entropy / information-theoretic optimization。直觉上，低 cost rollout 获得 exponentially larger weight，高 cost rollout 的贡献快速衰减；控制更新不是只保留一个“当前最好 sample”，而是利用整个 sampled distribution 的 cost-weighted information。

### 动力学与传感器假设

MPPI 本身不决定状态估计器。原工作将算法应用到 aggressive autonomous driving，真正运行仍需要可靠 state estimate 和可 rollout 的 vehicle dynamics model。它对 dynamics 的要求比许多基于 analytic derivative 的方法宽松，因此特别适合 learned dynamics、非线性车辆和 GPU batch rollout。

### 当年为什么重要

它把 stochastic optimal control 的信息论形式与一个高度可并行的 sampling controller 结合起来，并在 aggressive dirt-track driving 上做真实系统验证。更重要的是，它让大批量采样真正变成 GPU 友好的控制计算。

### 今天仍在使用的思想

现代 MPPI 仍然围绕 proposal distribution、number of rollouts、horizon、temperature、cost shaping、dynamics accuracy 与 warm start 工作。今天 Spike-MPPI 的意义正是在提醒：经典实现把 proposal 常常简化成 Gaussian perturbation，但理论框架本身并没有要求忽略 proposal 的时序结构。

### 已被后续扩展的部分

现代 MPPI 已经大量加入 covariance adaptation、colored / low-pass noise、learned proposal、risk-sensitive / robust cost、multi-modal sampling、neural / ensemble dynamics、安全 filter，以及 CUDA / Isaac / JAX 大规模并行。

因此经典论文最值得复盘的不是“照抄 2018 参数”，而是理解 cost-weighted sampling 为什么有效，以及 proposal mismatch 为什么会浪费 rollout budget。

### 公开代码 / 数据与可复现性

论文可直接从 [arXiv](https://arxiv.org/abs/1707.02342) 获取，正式出版 DOI 为 [10.1109/TRO.2018.2865891](https://doi.org/10.1109/TRO.2018.2865891)。

今天复现实验不必重做 AutoRally。用现有 MuJoCo / Isaac / 自己的 MPPI 控制器，固定 dynamics、cost 和 K，只改变 proposal spectrum，就能直接观察这一经典框架最核心的行为。

### 对当前工程项目的重新解读

对无人机 / 四足 MPPI，建议将 sampler 从“实现细节”提升为显式模块，并记录 temporal spectrum、covariance、higher-order structure、actuator bandwidth match，以及 effective sample size / weight entropy。

如果大部分权重长期集中在极少数 rollout 上，很可能不是“再加 4096 个 sample”就能解决，而是 proposal 根本没有在有效控制空间里采样。

[arXiv](https://arxiv.org/abs/1707.02342) · [DOI](https://doi.org/10.1109/TRO.2018.2865891)

## 今日结论

今天最明显的机器人系统趋势，是“学习模块开始主动服从系统时间尺度和安全边界”，而不是让一个大模型拥有全部职责。

DAVIO 让 feed-forward geometry 服务于 VIO 的启动和 dense mapping，但 metric scale / gravity 仍由惯性系统掌权；LiMA 把长时 intent 和高频 reaction 拆开；PointCast 学 world dynamics 后也只是作为 MPC 的预测器。它们共同说明：learned model 最有价值的落点，经常是某个困难中间模块，而不是一口气替换完整机器人栈。

安全控制侧也在进一步从“当前是否违反约束”转向“还有多少可恢复余量”。LEAP-CBF 用 adversarial effort 表示 recoverability，Distributed Koopman-MPC 则用独立 local projection 保证即便通信掉线也仍有 last-mile safety。对于真实机器人，能够明确知道 safety margin 正在变差，比失败后才触发 emergency stop 更重要。

Spike-MPPI 和经典 IT-MPC 放在一起看，则给 sampling control 一个非常实际的结论：Rollout budget 是有限的，因此 sampler 必须尽量产生“机器人真的可能执行的控制”。时序白噪声只是方便，不一定是最合适的 proposal。对于 actuator bandwidth 很有限的无人机、腿式和机械臂，先匹配控制频谱，再增加 sample 数，很可能更划算。

SLAM / 全局定位方面，建筑几何定位展示了另一种值得保留的思路：当 appearance 容易漂移时，优先寻找在时间上更稳定的 structural invariant。对城市 UAV 是 building footprints；对工业机器人可能是管线拓扑、立柱 / 门洞布局、反光标志结构。

AI Coding 侧，SWE-Flux 和今天两条实战技巧可以组合成一个完整工程闭环：runtime-grounded regression + persistent code intelligence + model/tool OpenTelemetry。Agent 不只是“写代码并说自己完成”，而是在可观测、由真实执行 oracle 验收的研发环境里工作。

如果把今天压缩成一句话：

> **真正可落地的智能系统，不仅要学会预测和生成，还要明确自己的时间预算、安全余量、运行证据和失败边界。**

## 最值得深入研究或尝试复现的方向

1. **DAVIO 式 Feed-Forward Init Sidecar**：保留当前 VIO，不改正常 initializer；只在低视差 / 启动超时场景调用多视图深度 prior，比较 first-valid-pose 时间、错误初始化率和 bias 收敛。
2. **MPPI Proposal A/B**：固定当前 MPPI 的 rollout 数和 cost，只比较 white Gaussian、low-pass Gaussian、与 actuator bandwidth 匹配的 colored noise。先看 smoothness / weight entropy / success，再考虑 Spike / learned proposal。
3. **Robot Safety Recovery Margin**：在现有 CBF / safety QP 旁增加 recoverability critic，记录“离不可恢复状态还有多少 disturbance budget”，先 shadow mode，不直接接管控制。
4. **多机器人 Safety 与通信解耦**：把 remote trajectory 只用于性能预测；本地 LiDAR / geometry 单独负责最后一层 hard safety。主动注入 packet dropout 测 collision rate 和 feasibility margin。
5. **SWE-Flux 式内部动态评测**：从公司真实 unit/integration tests 自动 harvest runtime oracle，生成 state / exception / dataflow 问题，用来回归 Codex / Claude / 自研 Agent，而不是只测 patch 是否编译。
6. **C++ Agent 工具链观测**：大型 C++ 项目先让 whole-codebase index 稳定，再通过 OTel 记录 LLM / tool latency；把“Agent 慢”拆成 indexing、model、tool、build/test 四类真实成本。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [DAVIO](https://arxiv.org/abs/2609.27702)
- [Large-Scale Geometric Map-Based Localization of UAVs](https://arxiv.org/abs/2609.28225)
- [LEAP-CBF](https://arxiv.org/abs/2609.28364)
- [Safety-Filtered Distributed Koopman-MPC](https://arxiv.org/abs/2609.27463)
- [Motoneuron-Inspired Sampling for MPPI](https://arxiv.org/abs/2609.28325)
- [LiMA](https://arxiv.org/abs/2609.28431) · [项目页](https://ccdcs.github.io/LiMA_repo/)
- [PointCast](https://arxiv.org/abs/2609.28393) · [项目页](https://pointcast-wm.github.io/)
- [SWE-Flux](https://arxiv.org/abs/2609.28449)
- [GitHub C++ Whole Codebase Indexing](https://github.blog/changelog/2026-09-22-faster-c-code-intelligence-with-whole-codebase-indexing/)
- [GitHub Copilot OpenTelemetry](https://github.blog/changelog/2026-09-22-opentelemetry-in-the-github-copilot-app/) · [GitHub Docs](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference)
- [Information-Theoretic Model Predictive Control](https://arxiv.org/abs/1707.02342) · [DOI](https://doi.org/10.1109/TRO.2018.2865891)
