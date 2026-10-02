---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-02"
date: 2026-10-02 09:00:00 +0800
description: "聚焦声纳回环、平面图先验 SLAM、多机视觉状态估计、GPU 信息增益探索、概率安全 NMPC、VLA 多链路防护、机器人执行 Harness 与 Coding Agent 预执行哨兵。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-02

## 摘要

截至 2026-10-02 早间，arXiv Robotics 最新常规公开批次为 2026-10-01，共 144 条；Software Engineering 同日为 24 条。本期先检查最近 24 小时公开内容，再从最新批次筛选高价值工作，并按规范化标题、arXiv ID、DOI、GitHub 仓库和项目主页与历史覆盖索引强制去重。今天入选论文的 v1 均实际提交于 9 月 30 日 UTC，距离本次生成已超过 24 小时，因此统一标为“时间回补”，不把 arXiv 公开批次日期包装成论文原始提交日期。

SLAM 侧今天最值得看的两条路线，分别解决“感知本身高度歧义时怎样防止错误回环毁图”和“已有建筑平面图时怎样让在线 VIO 获得长期全局约束”。BatSLAM 2.0 面向仿生双耳声纳，把 loop candidate 的时间序列一致性验证放在 place recognition 与 pose graph 之间，避免长走廊中几乎相同的 echo train 直接形成灾难性闭环。MVP-SLAM 则使用前后相反方向的两颗鱼眼相机做在线 VIO，并把自己检测到的墙与 floorplan 进行 drift-aware 匹配，再把可靠匹配逐步变成持续校正。在 Hilti-Trimble SLAM Challenge 2026 多层施工场景中，它的 Localization mean RMSE 为 0.29 m、SLAM 为 0.24 m。

状态估计与控制之间，今天有一条非常值得 UAV 团队注意的结果：多机视觉估计如果只看邻机位置，再由位移差分估速度/加速度，会产生近似固定的结构性延迟。Towards Agile Vision-Based Multi-UAV Flight 直接把视觉检测到的机体倾角作为额外观测，给推力方向提供物理约束；在 3–21 m/s² 的敏捷运动测试中，pose-aware estimator 相对 position-only estimator 平均速度误差降低 40%、加速度误差降低 57%，后者还出现约 300 ms 的恒定 acceleration-step delay。

自主探索方面，GPU-Accelerated Path-Dependent Marginal Information Gain 解决了“候选视点的信息量被重复计算”的老问题。它用 depth buffer 表示祖先节点已经覆盖的未知体素，再把后续 candidate ray 投影回这些 buffer，剔除路径上已经“预期见过”的区域；结果与精确 voxel-hash marginal gain 只差约 5–10%，但桌面 GPU 最高快 118×，Jetson Orin NX 最高快 28×。

安全控制侧，本期两项工作都不是简单再加一个碰撞 penalty。RL-Guided PAC-NMPC 将 RL 学到的 actor-critic 与 sensor prediction model 放进 sampling-based NMPC，并用 PAC 风格硬约束给碰撞概率与 value improvement 提供有限样本统计保证；Multi-Link Safety Filtering for VLA Policies 则给机械臂的 gripper、wrist、forearm 建五个椭球安全包络，在 CPU 上用 barrier program 对移动危险体做实时修正，真机 SO-101 的 16 次任务中，hazard contact 从未加 shield 的 11/16 降到 3/16。

机器人 Agent / VLA runtime 方面，DynaHarness 很值得认真看。它把 slow semantic brain 与 fast physical brain 分离，所有高层能力调用必须通过共享 execution contract；fast brain 可以拒绝无法落地的符号参数、替换 capability、触发 replanning，并把失败证据写回 capability revision。项目页给出的实现里，控制 20 Hz、安全 50 Hz、fast brain 2 Hz，而 slow brain 仅按需调用，真正的执行权始终留在快速物理层。

AI Coding 主动态 HiSentinel 则把同一种思想搬到 Coding Agent：不要等错误 tool action 执行完再补救，而是在执行前判断“放行、自动改道、还是暂停求人”。它用 privileged teacher 读取历史轨迹的真实后果，再蒸馏成只看 pre-action context 与 proposed action 的 0.6B / 1.7B causal sentinel；在 SWE-bench Verified Mini 与 Ask-or-Assume 上分别最高提升约 14% 与 10%，token 使用保持相近。

近期通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic、Google 与 xAI 的公开发布入口，没有发现 10 月 1 日需要新增覆盖的通用旗舰正式发布；近期 GPT-6.1 Sol、Gemini 4 Argon 与 Claude Sonnet 5.5 已在前几期覆盖，因此本期不重复填充。

最新公开列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

## 1. BatSLAM 2.0：声纳回环不能只看“像不像”，还必须看“是不是连续地像”

**时间回补：v1 提交于 2026-09-30 16:29 UTC。**

### 为什么重要

声纳 place recognition 的根本问题是高歧义。长走廊、规则房间、重复墙面会产生非常相似的 echo train。单帧 descriptor 即使给出很高相似度，也可能只是感知 aliasing；一旦错误 loop closure 被写入图优化，整张拓扑地图可能被强行折叠。

BatSLAM 2.0 的关键不是单独设计一个更强 descriptor，而是在 acoustic front-end 和 pose graph 之间加入 sequence verifier：闭环候选必须在连续时间上积累证据，才能真正变成图约束。

### 算法模块

    binaural sonar echoes
            ↓
    updated acoustic front-end
            ↓
    place-recognition candidates
            ↓
    sequence tracking / verification
            ↓
    accepted loop closures
            ↓
    factor-graph pose graph
            ↓
    robust topological map

这和视觉 / LiDAR 回环中的 temporal consistency 很像：单次相似度只负责“提出候选”，连续观测负责“建立可信度”。

### 传感器与状态假设

系统依赖仿生双耳声纳，而不是 LiDAR / camera。声纳对低光、烟尘和弱纹理环境有天然优势，但 range/angular resolution 和多径特性决定了它更容易出现 perceptual aliasing。

因此它特别适合把定位状态理解成多层证据，而不是让一个 place score 直接控制 pose graph。

### 实时性、鲁棒性与结果

论文在仿真与真实声纳录制数据上评估，重点展示 sequence verification 对 false loop closure 的抑制，以及在地图规模增加时仍能维持更稳定的 topological mapping。公开摘要没有给出一个可直接迁移到任意平台的统一 Hz / latency 数字，因此现阶段不应把它包装成固定实时指标。

### 可复现性

当前 arXiv 页面没有稳定公开的完整代码仓库入口，复现条件暂时一般。最容易先复现的不是声纳前端，而是 sequence gate：将现有 place-recognition top-K 候选缓存成短窗口，只允许持续多帧满足时间 / 拓扑一致性的候选进入 pose graph。

### 工程风险

sequence verification 会降低误闭环，但也可能推迟真正闭环，尤其在机器人快速穿过重复区域时。建议输出：

    candidate_score
    sequence_support
    temporal_consistency
    geometric_consistency
    loop_age
    accepted_or_rejected_reason

这样能区分“前端没认出来”和“后端主动拒绝”。

### 适合谁关注

声纳 SLAM、矿井 / 隧道、烟尘环境、低纹理地下空间，以及任何存在强重复结构的视觉 / LiDAR 回环系统。

### 工程落地启发

对 16 线 LiDAR 长走廊同样适用：Scan Context / UpDown-SC 只做候选召回，连续若干 keyframe 对同一闭环假设形成一致支持后，再进入 GICP / pose graph。不要让一个漂亮的单帧相似度直接改变全局图。

[论文](https://arxiv.org/abs/2609.40085)

## 2. MVP-SLAM：施工现场已经有 Floorplan，就让在线 VIO 把它变成长期漂移约束

**时间回补：v1 提交于 2026-09-30 12:19 UTC。**

### 为什么重要

施工现场是 VIO 很难受的一类环境：低纹理墙面、重复走廊、楼层结构相似、临时遮挡和持续改造都会让纯视觉惯性系统长期漂移。

但这类场景通常又有一个被传统 SLAM 流程浪费的先验：建筑 floorplan。

MVP-SLAM 并不是把 floorplan 当“初始化一次的地图”，而是持续从在线 SLAM 地图中检测 wall，再以 drift-aware 策略与平面图匹配，只有可靠关系才逐步转成持久 correction。

### 算法模块

    opposite-facing fisheye cameras
              +
             IMU
              ↓
    online visual-inertial SLAM
              ↓
    wall extraction from local map
              ↓
    drift-aware wall ↔ floorplan matching
              ↓
    multi-stage consistency checking
              ↓
    persistent floorplan correction
              ↓
    globally stabilized trajectory

两颗相反方向的鱼眼相机有助于扩大视场，减少施工通道中“只看一面墙”的局部退化。

### 传感器与地图假设

需要双鱼眼 + IMU，以及与当前建筑相对应的 floorplan。最大的隐含假设是“设计图和现场已经足够一致”。

真实施工环境里，临时隔墙、未完工区域、门洞变化、堆料和局部结构修改都可能让 floorplan 变成错误先验。

### 结果与实时性

在 Hilti-Trimble SLAM Challenge 2026 多层施工数据上，论文报告 Localization 项在 22 支队伍中排名第 2，mean RMSE 0.29 m；SLAM 项在 62 支队伍中排名第 5，mean RMSE 0.24 m，并强调其属于在线运行、真正把 floorplan 集成进定位流程的方法。

公开材料没有给出一个适合直接外推到所有硬件的端到端 FPS，因此工程上仍需自行统计 front-end、wall matching、correction update 的 P95 latency。

### 鲁棒性与工程风险

floorplan prior 最大风险是“非常自信地纠错到错误地方”。建议匹配接口不要只输出一个 transform，而要保留：

    wall_pair_support
    floorplan_revision
    local_map_consistency
    correction_magnitude
    persistence_count
    reject_reason

如果 correction 一次就能把地图拉几十厘米甚至数米，应该先进入 shadow / delayed confirmation，而不是立即施加。

### 可复现性

当前没有稳定定位到成熟公开仓库。最实用的复现方式是保留现有 VIO，仅增加 floorplan wall factor sidecar，比较 pure VIO 与 floorplan-aided 后端的长期 drift。

### 适合谁关注

施工机器人、BIM / Revit 场景、室内无人机、仓储 / 楼宇巡检，以及已有建筑图纸但又不想完全依赖预建点云地图的团队。

### 工程落地启发

如果已经有 CAD / BIM，地图先验不必一上来做复杂 3D semantic matching。墙、走廊方向、门洞等稳定结构就足以构造低频 global correction，而且比把 floorplan 全部硬塞进 estimator 更容易排错。

[论文](https://arxiv.org/abs/2609.39596)

## 3. 多机视觉状态估计：位置看得再准，也补不回 300 ms 的结构性加速度延迟

**时间回补：v1 提交于 2026-09-30 12:29 UTC；IROS 2026。**

### 为什么重要

多无人机 leader-follower、编队和相互避障经常依赖视觉估计邻机位置，再通过状态滤波推速度和加速度。

问题在于：如果视觉 measurement 本身只包含 position，突然 acceleration 发生以后，estimator 必须等待位置轨迹“弯出来”才知道对方改变了运动。这不是滤波参数没调好，而是 observability 带来的结构性延迟。

论文的解决方式很简单但有效：从视觉检测器中同时提取邻机 tilt。对于共面 multirotor，倾角直接提供推力方向信息，因此对 acceleration 是更即时的物理观测。

### 算法与估计结构

    image detector
       ├─ relative position
       └─ body tilt / pose cue
              ↓
    pose-aware estimator
              ↓
    thrust-direction constraint
              ↓
    neighbor velocity / acceleration
              ↓
    NMPC leader-follower control

作者比较了 4 种 position-only 与 5 种 pose-aware estimator，并包含一个新的 linear thrust-constraining Kalman filter。

### 传感器与动力学假设

关键假设是邻机属于 multirotor，姿态倾斜和水平推力 / 加速度存在明确物理联系。对于固定翼或地面机器人，这个 tilt cue 不再具有同样含义。

此外，结果依赖视觉 detector 能稳定输出 tilt；严重遮挡、motion blur、机体对称外观都会影响 pose cue。

### 结果与实时性

在两组真实数据和一组 photorealistic simulation 中，运动强度覆盖约 3–21 m/s²。pose-aware estimator 平均速度误差降低 40%、加速度误差降低 57%。position-only estimator 对 acceleration step 出现约 300 ms 的近似恒定延迟，而且这个延迟并不会随着运动强度降低而消失。

闭环 leader-follower NMPC 里，position-only leader estimate 无法保持稳定 hover；加入 tilt constraint 后可以支持超过 2g 的 lateral maneuver。

### 工程风险

姿态 cue 是强观测，但 detector 偶尔翻转 180° 或发生错误姿态解时，也可能把错误 acceleration 直接送进控制器。

建议把：

    pose_confidence
    position_innovation
    tilt_innovation
    estimated_acceleration
    vision_timestamp

独立保留，避免把所有信息混成一个不可诊断的 state vector。

### 可复现性

论文更适合做 estimator-level 复现：用同一套视觉位置数据，比较 position-only KF 与增加 tilt measurement 的 filter，不必一开始就重做完整 multi-UAV 系统。

### 适合谁关注

多 UAV 编队、视觉跟随、动态目标状态估计、狭窄空间协同飞行。

### 工程落地启发

当系统“总是慢半拍”时，先问是不是观测本身缺少对目标变化率的直接信息，而不是立刻调更激进的 Q/R。更强的 measurement 往往比更复杂的 filter 更有效。

[论文](https://arxiv.org/abs/2609.39611)

## 4. GPU 路径相关信息增益：自主探索不要把同一块未知区域反复算成“新信息”

**时间回补：v1 提交于 2026-09-30 17:50 UTC；投稿 ICRA 2027。**

### 为什么重要

sampling-based exploration planner 常给每个 candidate viewpoint 算“能看到多少未知 voxel”，再用 information gain / travel cost 选目标。

最常见的近似是假设每个 viewpoint 相互独立。于是同一条候选路径上，前一个节点已经预计会看见的未知区域，后一个节点又会重复计分。规划器因此可能喜欢“连续看同一片区域”的路径，而不是覆盖真正的新空间。

### 算法模块

    exploration tree
          ↓
    ancestor observations
          ↓
    depth buffers
    representing already-covered unknown voxels
          ↓
    candidate ray projection into ancestor buffers
          ↓
    remove overlap
          ↓
    path-dependent marginal information gain
          ↓
    GPU parallel evaluation per tree level

论文还联合优化 yaw，并让同一层的 candidate node / ray 在 GPU 上并行。

### 结果与实时性

相对精确 voxel-hash marginal gain，这种 depth-buffer 近似误差约 5–10%；但吞吐大幅提高，桌面 GPU 最高达到 118×，Jetson Orin NX 最高 28×。

集成到两类 sampling planner、三个仿真环境后，6 个 planner-environment 组合中有 5 个缩短达到 95% coverage 的时间；真实实验中，达到 95% coverage 的时间缩短约 30%，也能更早判断“继续探索收益已经很低”。

### 传感器 / 地图假设

算法假设当前 occupancy / unknown map 能提供 raycasting，且相机 / LiDAR FOV 可被 depth buffer 近似表达。

如果地图快速变化、动态物体很多，祖先节点“预计已经看到”的区域不一定仍然有效；长期 exploration 仍需 map revision 机制。

### 鲁棒性与工程风险

信息增益算得再精确，也只是在优化当前 map belief。定位漂移或地图错误可能让“新信息”判断本身失真。

建议 planner telemetry 同时保存：

    raw_viewpoint_gain
    marginal_gain
    overlap_ratio
    travel_cost
    localization_uncertainty
    expected_coverage_after_path

### 可复现性

当前没有稳定公开代码入口，但算法适合在已有 frontier / RRT exploration 上做局部替换：先保留原 planner，只把 independent information gain 改成 ancestor-aware marginal gain。

### 适合谁关注

无人机自主探索、FAR planner 类系统、3D occupancy exploration、Jetson GPU 平台。

### 工程落地启发

如果探索器总喜欢在一个房间反复转向不同 viewpoint，可以先统计 candidate gain 的 overlap ratio。很多时候不是路径搜索不够聪明，而是 reward 把重复观测当成了新收益。

[论文](https://arxiv.org/abs/2609.40297)

## 5. RL-Guided PAC-NMPC：让 RL 提供长期偏好，让 NMPC 保留有限样本概率安全约束

**时间回补：v1 提交于 2026-09-30 14:43 UTC。**

### 为什么重要

未知环境感知导航有一个长期矛盾：RL 很擅长从复杂传感器输入里学习长期行为，但安全难证明；NMPC 可以显式写 dynamics 和 constraint，却很难把高维视觉 / 感知 uncertainty 全部手工建模。

这项工作试图把两者职责拆开：RL 学 actor-critic 与 sensor prediction，sampling-based NMPC 负责在当前 horizon 内搜索动作，并通过 PAC 风格约束控制碰撞概率和 value improvement。

### 算法模块

    sensor observation
          ↓
    learned probabilistic actor-critic
    + learned sensor prediction model
          ↓
    sampling-based nonlinear MPC
          ↓
    finite-sample PAC constraints
       ├─ collision probability
       └─ expected value improvement
          ↓
    applied control

核心思想不是让 RL action 直接执行，而是把 learned policy / value 变成 proposal 和长时目标，再由 MPC 进行局部安全过滤。

### 动力学与概率假设

所谓 PAC safety 是相对于论文给定的 sampling、prediction model 和 confidence construction 的有限样本统计保证，并不等于真实世界“绝对不会撞”。

模型 misspecification、传感器 OOD、极端动态体都可能落在保证范围之外。

### 结果与真机

论文在多个高维系统和 nonlinear dynamics 仿真中评估，并在固定翼敏捷飞行平台上做 perception-based navigation 硬件验证。结果表明，它可以利用 RL 的长期 value，同时保留显式碰撞概率约束。

### 鲁棒性与工程风险

最重要的 runtime state 不是一个“safe=true”，而应该把保证本身显式输出：

    confidence_level
    sampled_collision_probability
    value_improvement_bound
    model_uncertainty
    sample_count
    constraint_feasible

如果 sample budget 太小或 model uncertainty 太高，系统应降速 / 停止，而不是继续沿用旧 certificate。

### 可复现性

当前没有稳定定位到完整开源仓库。最小复现可以在现有 MPPI/NMPC 上增加 learned terminal value + stochastic obstacle model，再对 sample count 与 empirical collision rate 做 calibration。

### 适合谁关注

安全 RL、无人机 MPC、感知导航、希望让 learned policy 与 hard runtime controller 共存的团队。

### 工程落地启发

对现有飞行系统，先不要让 RL 直接控 actuator。可以让 RL 只输出 reference / terminal value / action proposal，再用 NMPC 或 CBF 作为最后的执行层，failure domain 更清晰。

[论文](https://arxiv.org/abs/2609.39854)

## 6. Multi-Link VLA Safety Filter：只保护夹爪远远不够，手腕和前臂同样会撞

**时间回补：v1 提交于 2026-09-30 15:49 UTC。**

### 为什么重要

不少 VLA safety demo 只把 end-effector 当一个点或小球。真实机械臂却经常是手腕、前臂或 elbow 先撞到移动的人 / 物体。

这项工作用五个椭球覆盖 gripper、wrist、forearm，并在不重新训练 π0.5 的情况下，用 barrier program 对 nominal action 做在线修正。

### 算法模块

    RGB-D reset observation
          ↓
    detect / fit moving hazard ellipsoid
          ↓
    sparse optical flow tracking
          ↓
    robot five-ellipsoid body model
          ↓
    barrier safety program on CPU
          ↓
    corrected VLA action

它没有每帧都重新做昂贵 detector / 3D fit，而是初始化后用 sparse optical flow 跟踪 hazard center，尽量保持控制 loop 轻量。

### 实时性

项目页公开的 profiling 很值得看：

- 五椭球 barrier filter CPU P99 latency 约 2.2 ms；
- 通过缩短 vision-language prefix、减少 flow-matching step，π0.5 在 integrated GPU 上从约 343 ms 降到 177.3 ms；
- detector / policy 跑 iGPU，filter 和 optical flow 跑 CPU；
- 作者测试 NPU 后发现约慢 2.5×，因此没有使用。

这说明真正的机器人 edge optimization 往往不是“有 NPU 就一定上 NPU”，而是按 operator profile 决定放在哪里。

### 真机结果

仿真 6 类 hazard condition 中，collision 从 65.62% 降到 27.27%，safe-success 从 29.35% 提升到 50.43%。

SO-101 真机 4 个任务 × 4 次，共 16 episode：加 shield 后 hazard contact 为 3/16，未加 shield 为 11/16。项目页使用 RealSense D455 + wrist camera 和 Intel Core Ultra X7 358H。

### 传感器与风险

最大风险来自 hazard representation：移动危险体被近似成椭球，而且初始检测 / 拟合之后主要靠 optical flow 更新中心。持续遮挡、目标形变、深度错误都会让安全几何逐渐漂移。

因此更稳的产品结构应增加：

    hazard_track_confidence
    last_depth_update
    optical_flow_residual
    shield_intervention_rate
    minimum_link_clearance

并在 track confidence 低时切到更保守速度限制。

### 可复现性

项目页已公开实现细节与实验，代码目前仍标注 coming soon，因此还不能按完整开源项目评价。

### 适合谁关注

VLA、低成本桌面机械臂、动态人机共域、希望给已有 policy 外挂 safety shield 的团队。

### 工程落地启发

安全几何至少要覆盖真正可能碰撞的 link，而不是只包围 TCP。对于机器人狗水炮、机械臂、轮足操作，同样应该把机体 / 臂杆 / 末端分成多个安全几何体。

[论文](https://arxiv.org/abs/2609.40007) · [项目页](https://yathag.github.io/multilink-safety-filter/)

## 7. DynaHarness：让慢速 Agent 提建议，让快速物理层掌握真正执行权

**时间回补：v1 提交于 2026-09-30 17:52 UTC。**

### 为什么重要

机器人 Agent 最危险的一种架构是：

    VLM/LLM
      ↓
    skill call
      ↓
    robot executes

中间没有真正理解 capability precondition、动作可落地性、失败证据和 runtime correction 的执行层。

DynaHarness 把机器人 runtime 做成“动态物理 Harness”：slow brain 只负责提出 capability 和符号参数，fast brain 负责 grounding、monitoring、拒绝、替换 capability 和请求 replanning；所有接受的命令都通过共享 execution contract。

### 架构模块

    slow semantic brain
    → propose capability + symbolic arguments
                 ↓
          execution contract
                 ↓
    fast physical brain
       ├─ ground arguments
       ├─ validate capability
       ├─ monitor execution
       ├─ reject / substitute
       └─ request replan
                 ↓
            robot control

失败后并不是简单“再问一次 LLM”，而是 failure attribution 先定位具体 capability / grounding fault，再把修订通过 paired regression checks 后才写回能力库。

### 实时性

项目页给出的系统频率非常有参考意义：

- control：20 Hz；
- safety：50 Hz；
- fast brain：2 Hz；
- slow brain：按需调用；
- Qwen3-VL-4B slow brain 单次约 913 ms；
- fast brain median 约 0.046 ms；
- 实验累计 47,199 次 fast decision、3,090 次 planner call。

它最关键的系统原则是：slow model 再慢，也不直接获得高频 physical authority。

### 结果

LIBERO-Pro 上 800 个新 initial state，论文报告完整系统成功率 75.2%，frozen policy 为 17.5%。使用同一 capability library 时，dynamic execution 为 74.0%，而 nominal one-step replanning 为 63.9%。项目页还提供真实机器人实验。

### 权限 / 安全 / 可验证性风险

execution contract 本身必须是 deterministic / inspectable 的，否则只是把黑盒从 policy 移到了 harness。

建议 capability 统一保存：

    preconditions
    argument_schema
    body_state_requirements
    runtime_monitor
    success_evidence
    failure_codes
    rollback
    regression_tests

### 可复现性

项目页公开了大量架构、评测与运行数据，但其 GitHub 代码链接在本次核验时返回 404，因此当前不能把它评价为“代码已可直接复现”。

### 适合谁关注

机器人 Agent、VLA + skill library、多层控制系统、需要让 LLM 参与任务但不希望它直接拥有物理执行权的团队。

### 工程落地启发

已有 vendor SDK 的系统尤其适合这种架构：LLM 只生成 skill plan，fast harness 负责把 vx/vy/vw、stair mode、arm command 等真正映射到当前机器人，并随时拒绝违反物理 / 安全条件的调用。

[论文](https://arxiv.org/abs/2609.40306) · [项目页](https://denghaoyuan123.github.io/Dynaharness_page/)

## 8. HiSentinel：Coding Agent 的关键动作应该在执行前被“放行、改道或暂停”

**时间回补：v1 提交于 2026-09-30 15:26 UTC。**

### 突破性工程价值

Coding Agent 的错误通常不是单次 command 本身很严重，而是一个错误工具动作把后续 context 全部带偏：改错文件、错误假设测试环境、在不确定状态继续 destructive write，最后 Agent 可能花几十个 tool call 在错误分支上自洽。

HiSentinel 不做 post-hoc critic，而是在每次动作执行之前决定：

    allow
    autonomously redirect
    pause for human assistance

### 如何训练

直接训练这种 gate 很难，因为“当时不做这一步会怎样”缺少标签。

论文使用 hindsight distillation：

    recorded agent trajectory
             ↓
    privileged teacher sees future outcome
             ↓
    label whether earlier action should be
    allowed / redirected / escalated
             ↓
    distill into causal small sentinel
             ↓
    runtime sees only pre-action context
    + proposed action

作者训练了 0.6B 和 1.7B 两个 sentinel，并构建 SWE-Intervene 数据来描述 intervention 类型和反馈。

### 结果

在 SWE-bench Verified Mini 与 Ask-or-Assume 上，论文报告 completion 分别最高提升约 14% 和 10%，同时 token 使用保持在相近量级。

这说明“小模型 gate”不是单纯增加审批开销；如果能提前阻止高代价错误路径，可能反而让整体 trajectory 更短。

### 是否适合真实研发流程

非常适合高权限 Agent，但 intervention policy 必须和工具风险分级结合：

    read-only
    → 通常自动放行

    reversible write
    → sentinel + idempotency / diff review

    destructive / production action
    → deterministic policy + human approval

不要让 sentinel 代替权限系统。

### 权限 / 安全 / 可验证性风险

sentinel 最大风险是 false positive 太多，最终把 Agent 变成“每两步就问人”；false negative 则会放过真正危险动作。

产品中应持续记录：

    proposed_action
    sentinel_decision
    redirect_action
    human_override
    downstream_success
    false_intervention_rate

这样 gate 自身也能被回归测试。

### 可复现性

当前公开论文可以复现方法思路，但本次未找到稳定的官方代码仓库入口，因此暂时不能评价为成熟开源实现。

### 适合谁关注

Codex / Claude Code 企业部署、自研 Agent、自动 PR / CI / deploy、tool 权限治理。

### 工程落地启发

Agent runtime 可以先不用训练 sentinel，直接实现三态 gate API：

    ALLOW
    REDIRECT(tool/action)
    ESCALATE(reason)

然后把真正高成本的历史失败做成 regression set，再决定是否训练小模型自动判定。

[论文](https://arxiv.org/abs/2609.39957)

## AI Coding 实战技巧精选

### 技巧 1｜Copilot 需要操作桌面 GUI 时，按 App 单独授权，不要直接全局 Always Allow

- **来源**：GitHub 官方 Changelog，2026-10-01：[GitHub Copilot can now interact with desktop apps with computer use](https://github.blog/changelog/2026-10-01-github-copilot-can-now-interact-with-desktop-apps/)。
- **一句话结论**：Copilot CLI / App 现在可以点击、输入、滚动和拖拽桌面应用。把它用在“只能通过 GUI 完成”的遗留流程，但按应用逐个授权，不要把密码管理器、生产管理台等高风险应用设成永久放行。
- **具体怎么做**：
  1. Copilot CLI 更新到支持版本后执行 /computer on；需要查看状态时用 /computer show，完成后用 /computer off。
  2. Copilot App 可在 Settings → Computer Use → Enable Computer Use 打开，也可以使用 /computer on。
  3. 第一次控制某个应用时只授权当前明确需要的 App；完成任务后检查并重置不必要的 always-allow 项。
  4. 企业环境用 managed settings 对 Computer Use 做统一禁用 / 放行策略，不让个人默认权限覆盖组织边界。
- **适合什么场景**：没有 API 的内部工具、桌面测试软件、遗留配置工具、需要跨 IDE 与本地 GUI 完成步骤的 Coding Agent。
- **注意**：GUI 自动化比 API 更难保证幂等和可验证。涉及付款、生产权限、密码、发布等高影响动作，仍应要求显式真人确认。

### 技巧 2｜把重复的 Agent 流程写成 Dynamic Workflow，不要继续堆在一个超长 Prompt 里

- **来源**：GitHub 官方 Changelog，2026-10-01：[Dynamic workflows in Copilot CLI and the Copilot app](https://github.blog/changelog/2026-10-01-dynamic-workflows-in-copilot-cli-and-the-copilot-app/)。
- **一句话结论**：如果一个 Agent 任务有固定阶段、并行子任务、验证和人工 checkpoint，直接做 code-defined workflow；普通一次性任务继续用 chat。
- **具体怎么做**：
  1. 更新 Copilot CLI，用 --experimental 启动，或在会话中执行 /experimental on。
  2. 把稳定流程拆成明确 step：检索 / 修改 / 测试 / review / 汇总；需要并行的子任务并发运行，统一返回 structured result。
  3. 在发布、merge、昂贵测试前插入 checkpoint，让 workflow pause → review → resume，而不是靠模型“记住等我确认”。
  4. 可直接询问 Copilot “What dynamic workflows are available?” 检查当前扩展提供的 workflow，再把高频 Prompt 工作流逐个迁移。
- **适合什么场景**：长任务、大仓库、多 Agent、固定回归流程、需要阶段性人工审批的 CI / 发布准备。
- **注意**：workflow 把 orchestration 固化后也会形成新的代码资产；版本升级时要给 workflow 本身做 regression，不要认为“写成代码就不会漂”。

## 经典论文回顾

### Switchable Constraints：与其假设所有回环都是真的，不如把“这条边是否可信”也交给优化器

Niko Sünderhauf 与 Peter Protzel 的 **Switchable Constraints for Robust Pose Graph SLAM** 发表于 **IROS 2012**。它是 robust pose-graph optimization 非常经典的一步：不是只在 residual 外面套一个 robust kernel，而是给可疑 loop closure 引入显式 switch variable，使“这条约束是否参与图优化”本身成为状态估计问题的一部分。

### 核心问题

传统 pose graph 的结构通常是预先固定的：

    odometry edges
    + accepted loop closures
            ↓
    nonlinear least squares

一旦前端接受了错误闭环，后端往往默认这条边是真的，只能在互相冲突的约束中找一个折中。强错误闭环尤其可能把整张地图拉坏。

Switchable Constraints 把图结构也部分变成可优化对象：

    loop closure residual
           ×
    switch variable s
           ↓
    pose graph objective

如果某条闭环与其余图高度冲突，优化器可以把对应 s 压到接近 0，相当于自动关闭这条边。

### 关键数学思想

每个候选闭环增加一个 switch state，并给 switch 本身加 prior，避免所有边都被随意关掉。

直觉上：

    consistent loop
    → 保持 s ≈ 1
    → 正常参与优化

    gross outlier
    → residual 太大
    → 优化更愿意把 s → 0
    → 弱化 / 关闭该边

这让数据关联和状态估计不再完全串行：“前端一票定终身”变成后端还能根据全局几何一致性重新评价约束。

### 传感器 / 动力学假设

方法本身是后端鲁棒优化，不限定 camera / LiDAR / sonar，也不解决前端候选生成。

它默认 odometry / 大部分图约束整体仍然足够好，错误主要集中在一部分 loop closure。如果图里大多数边都错误，switch 变量也无法凭空恢复真实世界。

### 当年为什么重要

作者展示了即使加入多达约 1000 条 false-positive loop closure，Switchable Constraints 仍能比普通 pose graph 更稳，并提供了 Vertigo 扩展用于 g2o / GTSAM 体系。

它的重要历史位置在于：SLAM 社区开始更系统地承认“错误数据关联不是异常事件，而是后端必须主动建模的变量”。

### 今天仍在使用的思想

今天常见的 Dynamic Covariance Scaling、max-mixtures、Graduated Non-Convexity、Pairwise Consistent Measurement 等方法虽然形式不同，但都延续同一个思想：

> 约束的可信度不能只由前端一次打分决定，后端应该具有拒绝全局不一致测量的能力。

今天的 BatSLAM 2.0 恰好是一个非常好的对应案例。声纳环境 aliasing 很强，所以前端增加 sequence verifier；而 Switchable Constraints 提醒我们，即使 sequence verifier 偶尔仍出错，pose graph 也最好有自己的第二道鲁棒性。

### 已被后续替代 / 扩展的部分

显式 switch state 会增加变量数，也需要合理 prior；现代系统会选择更便宜的 DCS、GNC、robust kernel，或在进入图前做 PCM / geometric consistency pruning。

因此今天不一定要机械地把每条 loop 都加 switch variable，而是应该保持“前端验证 + 图前一致性筛选 + 后端鲁棒估计”的多层结构。

### 公开代码与可复现性

作者项目页仍保留论文和 Vertigo 代码说明，历史实现依赖较老的 g2o / GTSAM 2.0 与 OpenSLAM SVN，直接编译体验不再现代。

但算法很容易在今天的 factor-graph 中重现：给 loop factor 增加 scalar switch，再给 switch 添加偏向 1 的 prior，即可观察错误闭环如何被自动关闭。

### 对当前工程项目的重新解读

对于 LIO-SAM + Scan Context / UpDown-SC，更合理的回环流水线不是单层阈值：

    global descriptor
    → Top-K recall

    temporal / sequence consistency
    → suppress perceptual aliasing

    GICP / local geometry
    → SE(3) verification

    robust pose graph
    → final safety net

长走廊、楼梯和重复厂房里，真正可靠的回环来自多层相互独立的证据，而不是把某一个 descriptor 阈值调得越来越苛刻。

[项目页](https://nikosuenderhauf.github.io/projects/switchableConstraints/) · [论文 PDF](https://nikosuenderhauf.github.io/assets/papers/IROS12-switchableConstraints.pdf) · [DOI](https://doi.org/10.1109/IROS.2012.6385590)

## 今日结论

今天最明显的一条主线是：**可靠系统正在把“是否相信这条信息”从一个隐含判断，变成显式的状态和可验证流程。**

BatSLAM 2.0 不让单次声纳相似度直接成为闭环，而要求 sequence-level support；MVP-SLAM 不让 floorplan 一次匹配就拉地图，而通过多阶段匹配逐步形成 persistent correction；经典 Switchable Constraints 更进一步，让后端自己拥有关闭可疑 loop factor 的能力。

多机视觉状态估计说明另一个重要事实：滤波器复杂度不能补偿观测缺失。position-only pipeline 的 300 ms 结构性 delay 不会因为调更大的 process noise 就消失；真正有价值的是增加与动力学直接相关的 tilt measurement。

探索和控制侧也在重新分配计算预算。路径相关 marginal information gain 把 GPU 花在“真正新增的信息”上，而不是重复计算重叠视场；PAC-NMPC 把 RL 用在长期 value 和感知预测，把最后执行留给带概率约束的 NMPC。

VLA safety 与 DynaHarness 则说明，大模型 / VLA 不应直接拥有无限物理 authority。一个可部署系统需要 link-level geometry、fast safety loop、capability contract、failure evidence 与 rollback / replan 路径。HiSentinel 把完全相同的思想应用到 Coding Agent：危险 tool action 应该在执行前被 gate，而不是事故发生后才让模型解释自己为什么做错。

今天两个 Copilot 实战技巧也可以放在同一个框架理解。Computer Use 扩大了 Agent 的可执行表面，因此权限必须细化到 App；Dynamic Workflow 把原本藏在长 Prompt 里的流程变成 code-defined orchestration，因此验证、checkpoint 和 rollback 都更容易成为显式机制。

如果把今天整期压成一句话：

> **可靠机器人和可靠 Agent 的核心，不是让单个模型更自信，而是让每条观测、闭环、先验、动作和工具调用都拥有独立的证据、权限边界与拒绝机制。**

## 最值得深入研究或尝试复现的方向

1. **长走廊回环四层 Gate。** 用现有 Scan Context / UpDown-SC 做召回，增加 3–5 keyframe temporal support，再做 GICP，最后在 pose graph 使用 DCS / switchable constraint。专门回放对称走廊和上下楼数据统计 false loop。
2. **Floorplan Sidecar。** 不改现有 VIO / LIO 前端，只从局部地图提 wall line，与 CAD / Revit floorplan 做低频匹配，把 correction 作为可拒绝的 factor 注入后端。
3. **多机视觉直接观测“运动变化率”。** 除位置外尝试估 tilt / heading / apparent scale rate，比较 estimator latency，而不是只比较 RMSE。
4. **探索 Reward 去重。** 给 FAR / sampling exploration planner 增加 ancestor-overlap ratio；固定路径搜索器，只对比 independent gain 与 path-dependent marginal gain。
5. **VLA Multi-Link Shield。** 不重训 policy，给末端、腕部、前臂分别建立安全几何，先在 shadow mode 统计真正的 link collision 分布，再决定 barrier margin。
6. **Robot Harness Contract。** 将 vendor SDK 的 stair / vx-vy-vw / arm skill 统一补齐 precondition、parameter schema、runtime monitor、failure code、verification 和 rollback。
7. **Coding Agent 三态 Pre-Action Gate。** 先用 deterministic policy 实现 ALLOW / REDIRECT / ESCALATE，再从真实错误轨迹构建 regression；不要一开始就训练一个无法解释的 judge。
8. **Copilot Computer Use 最小授权实验。** 只允许一个低风险 GUI 应用，用完整录像 /操作日志检查重试、重复点击和不可逆副作用，再考虑扩大应用范围。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [BatSLAM 2.0](https://arxiv.org/abs/2609.40085)
- [MVP-SLAM](https://arxiv.org/abs/2609.39596)
- [Towards Agile Vision-Based Multi-UAV Flight: Revisiting State Estimation](https://arxiv.org/abs/2609.39611)
- [GPU-Accelerated Path-Dependent Marginal Information Gain](https://arxiv.org/abs/2609.40297)
- [RL-Guided PAC-NMPC](https://arxiv.org/abs/2609.39854)
- [Multi-Link Safety Filtering for VLA Policies Around Moving Hazards](https://arxiv.org/abs/2609.40007)
- [Multi-Link Safety Filter 项目页](https://yathag.github.io/multilink-safety-filter/)
- [DynaHarness](https://arxiv.org/abs/2609.40306)
- [DynaHarness 项目页](https://denghaoyuan123.github.io/Dynaharness_page/)
- [Learning When and How to Intervene / HiSentinel](https://arxiv.org/abs/2609.39957)
- [GitHub Copilot Computer Use](https://github.blog/changelog/2026-10-01-github-copilot-can-now-interact-with-desktop-apps/)
- [GitHub Copilot Dynamic Workflows](https://github.blog/changelog/2026-10-01-dynamic-workflows-in-copilot-cli-and-the-copilot-app/)
- [Switchable Constraints 项目页](https://nikosuenderhauf.github.io/projects/switchableConstraints/)
- [Switchable Constraints DOI](https://doi.org/10.1109/IROS.2012.6385590)
