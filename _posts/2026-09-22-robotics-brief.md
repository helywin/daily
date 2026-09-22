---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-22"
date: 2026-09-22 09:00:00 +0800
description: "本期关注极暗视觉 SLAM、VIO 退化初始化、全身安全控制、连续碰撞概率场、GPU 接触模式规划、飞行器控制权威、Coding Agent 行为评测与 Grok 4.7。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-22

## 摘要

截至 2026-09-22 早间（Asia/Shanghai），arXiv Robotics 最新公开批次为 **2026-09-21（周一）**，共 114 条；Software Engineering 同日也刷新了新批次。需要注意的是，arXiv 的“公开批次日期”和论文最初提交时间并不相同：本期机器人论文的 v1 多提交于 9 月 17–18 日，因此严格按任务规范标为“时间回补”，不把它们包装成 9 月 22 日刚提交的新论文。最新列表可查看 [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) 与 [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

今天 SLAM 侧最值得优先看的两项工作都在处理“系统什么时候应该承认自己看不清”。**Noctif3R** 针对极暗、光子受限场景：它不只追求暗光下仍然输出轨迹，而是通过显式 match gate 拒绝没有运动信息的帧。作者在真实 Spot 暗室视频里观察到 86.5% 输入帧完全黑时，DROID-SLAM 与 DPV-SLAM 仍为全部 1178 帧输出 pose，而 Noctif3R 配置在照明消失后停止；同时作者给出 Jetson AGX Orin 的嵌入式执行路径，在两条测试场景上取得 1.28× / 1.42× throughput，峰值 GPU 内存下降 47%，每 pose 能耗下降 29%。([论文](https://arxiv.org/abs/2609.21114))

**SLIM-init** 则处理单目 VIO 启动阶段的退化运动。它不显式三角化 3D landmark，而从 2D line track 中提取 vanishing point，利用 VP 对平移不敏感的性质提供 rotation-only 约束，再以 line epipolar residual 和 line-normal projection 改善 translation / linear alignment 的条件数。对于低视差、近似纯平移等很容易把 VIO 初始化搞坏的运动，这种“先借结构方向救旋转可观测性”的思路比继续堆 point feature 更值得关注。([论文](https://arxiv.org/abs/2609.21186))

控制侧今天有一条很清晰的主线：**安全模块开始显式建模“还有多少控制能力可用”，而不是只检查当前状态有没有越界。** LIMBO 从黑盒 transition 学 state-action Q-CBF，再把安全结构蒸馏进 29-DoF humanoid task policy，真机部署时不再需要在线 safety filter；Tilt as a Certified Resource 则更机械地定义 articulated multirotor 的 motor-only wrench-rate authority，用 CBF 保证“遇到扰动时还有多少快速改 wrench 的余量”，刻意不把较慢 servo 能力算入证书，避免出现虚假的可控性。

运动规划方面，两篇工作都在重新利用现代 GPU。**CoMET** 认为接触模式空间并不一定非得靠复杂启发式树搜索逃避，可以用 GPU 高吞吐把大量 mode trajectory 直接并行评价；**Stochastic Neural Signed Swept Volume** 则把整条机器人 swept volume 学成带不确定度的 signed-distance probabilistic field，使连续时间碰撞风险能够直接进入 chance-constrained trajectory optimization，而不是只在离散 waypoint 上做碰撞检查。

AI Coding 侧，**GameLogicBench** 把“代码能跑”与“运行过程中一直遵守业务规则”区分开。72 个 Godot 任务、403 个手工场景与 1451 个 seeded test case 都在每个 simulation tick 检查黑盒行为；论文发现很多失败提交是可运行的，只是某些 gameplay rule 在中间过程被违反。更重要的是，作者用 mutation validation 检验 evaluator 本身；去掉 mutation validation 后，会有错误 Agent 提交被判通过。这比再设计一个 LLM Judge 更接近真正的软件验收系统。

今天唯一真正属于最近 24 小时的大模型新发布是 **Grok 4.7**。xAI 在 9 月 21 日正式发布并开放 `grok-4.7` API：500K context，支持 text / image 输入与 text 输出，reasoning effort 支持 low / medium / high / xhigh；200K prompt tokens 以下价格为每百万 token $2 input、$0.50 cached input、$6 output。xAI 的自报基准中，Grok 4.7 在 CursorBench 4.0 为 46.3%，DeepSWE v1.1 为 71.0%（high effort），Terminal-Bench 4.0 为 38.0%。这些数字应视为厂商发布数据，而不是独立横评。([官方发布](https://x.ai/news/grok-4-7)，[模型文档](https://docs.x.ai/developers/models/grok-4.7))

## 1. Noctif3R：极暗 SLAM 最重要的能力之一，是知道“这一帧根本没有可用运动信息”

**时间回补：v1 提交于 2026-09-17 21:57 UTC。**

### 为什么重要

低照度 SLAM 很容易被“轨迹长度”误导。一个系统在完全黑暗时仍持续输出 pose，看起来没有 tracking lost，实际输出却可能几乎不包含相机运动信息。对真实机器人而言，这比明确报失效更危险，因为上层导航会把这些 pose 当真。

Noctif3R 的价值不只是把图像增强后继续跑，而是把**信息不足时主动拒绝**做进 pipeline。论文基于低光 feed-forward pointmap 前端，并增加显式 match gate：只有帧间匹配提供足够运动信息时，tracking 才继续。

### 算法与系统结构

```text
Photon-limited RGB frame
        ↓
Low-light feed-forward pointmap front-end
        ↓
Explicit match / information gate
        ↓
Tracking at lower resolution
        ↓
Keyframe + map + backend at higher resolution
        ↓
Pose / map
```

作者为 Jetson AGX Orin 专门设计了异分辨率执行路径：tracking 用 256 px，map / keyframe / backend 用 384 px，并修正 per-frame pose solve 中的两个瓶颈。

### 传感器假设

系统只依赖 monocular RGB，因此重量和功耗友好，但也意味着没有 IMU、LiDAR 或主动照明替它补观测。极暗时可观测性一旦消失，正确动作不是“猜一个 pose”，而是停止或让其他传感器接管。

### 实时性与结果

在论文的九个最低照度等级中：

- DROID-SLAM 在 9/9 情况下给出完整长度、但不含有效运动信息的轨迹；
- VGGT-SLAM 与 CUT3R 为 8/9；
- pi³ 为 7/9；
- DPV-SLAM 为 4/9；
- Noctif3R/SYS 只在真正能跟踪的三条情况下返回轨迹，没有输出“无信息轨迹”。

在真实机器人视频中，86.5% 输入帧完全为黑；Noctif3R 在照明消失后停止，而 DROID-SLAM 与 DPV-SLAM 为全部 1178 帧持续输出 pose。

嵌入式路径在两条测试场景分别达到约 1.28× / 1.42× throughput，同时峰值 GPU 内存下降 47%、每 pose 能耗下降 29%。

### 鲁棒性与工程风险

最大的工程启发是：**tracking health 应该是输出的一部分，而不是等 trajectory 爆掉才发现。**

可以把 SLAM 接口从：

```text
Pose T_world_body
```

升级为：

```text
TrackingResult {
  pose
  tracking_state
  match_information
  photometric_quality
  fallback_required
}
```

这样 PX4 / planner 才能在低信息阶段明确降级。

### 可复现性

论文公开了可再生的 calibrated noise ladder 和真实暗光序列设计思路，但当前最值得复现的不是完整网络，而是**给现有 VIO / SLAM 增加 no-information detection**：人为逐级降低曝光 / SNR，统计“何时停止输出”与“何时开始输出假稳定轨迹”。

### 适合谁关注

室内无人机、矿井 / 隧道机器人、夜间巡检、低功耗视觉定位、Jetson 端侧 SLAM。

### 工程落地启发

对于狭窄走廊无人机，与其把所有精力放在低光增强，不如同步设计三层 fallback：

```text
正常视觉 tracking
→ 视觉信息下降：提高 IMU / LiDAR 权重
→ 视觉完全失效：明确 INVALID，不生成伪 pose
```

[论文](https://arxiv.org/abs/2609.21114)

## 2. SLIM-init：VIO 初始化遇到低视差时，用直线和消失点先把旋转“钉住”

**时间回补：v1 提交于 2026-09-18 01:11 UTC；IROS 2026。**

### 为什么重要

单目 VIO 初始化通常需要同时恢复：

```text
gravity
scale
velocity
IMU bias
camera / IMU motion
```

如果机器人启动阶段接近纯平移、低视差或缺少充分旋转，point-based alignment 会变得病态。工程上经常出现“正常数据集都没问题，一上真机从地面直线起飞就初始化失败”。

SLIM-init 的思路是利用环境中的 line structure，将不同可观测信息拆开处理。

### 算法模块

```text
2D tracked line features
        ↓
Vanishing Points
→ translation-invariant orientation cue
→ rotation-only constraints
        ↓
Line epipolar residual
→ constrain translation
        ↓
Line-normal projection residual
→ improve linear alignment conditioning
        ↓
Monocular VI initialization
```

关键点是 **structureless**：不需要先显式恢复 3D line / point landmark，再做初始化。

### 传感器与几何假设

需要 monocular camera + IMU，并假定环境中存在足够稳定的直线结构。走廊、厂房、室内设备间、建筑环境通常非常适合；天然环境如果几乎没有可靠 line，收益会下降。

VP 的优势来自它对平移不敏感，因此即使 parallax 很弱，平行线族仍能给 rotation 提供独立约束。

### 鲁棒性

论文在公共 benchmark 和专门设计的 degenerate-motion sequence 上，相对已有初始化方法取得更高精度与成功鲁棒性。它解决的并不是整个 VIO 生命周期，而是一个非常具体、却对工程稳定性影响巨大的“启动可观测性”问题。

### 可复现性

arXiv 页面声明 source code available，并链接 `cjunwan/SLIM-init`；本次核验时该 GitHub 地址返回 404，因此当前代码可复现性暂时不能按“已公开可用”评价。论文算法仍可根据公开描述复现，但正式代码需要等待作者仓库可访问。

### 工程风险

Line / VP 也可能被错误结构欺骗：重复门框、纹理边缘、运动模糊都可能产生错误 line association。真正产品化时建议把：

```text
point excitation score
line / VP support count
rotation observability
translation observability
```

分别记录，而不是只返回一个 `initialized=true`。

### 适合谁关注

VINS / OpenVINS、无人机起飞初始化、建筑室内 VIO、低视差相机运动、对初始化失败敏感的嵌入式视觉系统。

### 工程落地启发

对现有 VIO 不需要推倒重写。可以把 SLIM-init 类结构作为 **fallback initializer**：正常 excitation 时继续用成熟点特征初始化，检测到 translation-dominant / low-parallax 时再引入 VP rotation constraint。

[论文](https://arxiv.org/abs/2609.21186)

## 3. LIMBO：把 Q-CBF 学出来，再把安全结构蒸馏进 Humanoid Policy

**时间回补：v1 提交于 2026-09-18 17:57 UTC。**

### 为什么重要

全身人形安全控制很难直接手写 CBF：29-DoF 动力学、碰撞、平衡和快速动作共同存在时，解析 barrier 设计与在线 QP 都会迅速复杂化。

LIMBO 采用两阶段路线：先从黑盒 transition 学 state-action safety value / Q-CBF，再把它作为 teacher 训练 task policy，最终真机部署不再运行在线 safety filter。

### 算法模块

```text
Frozen base whole-body controller
        ↓
Residual action space
        ↓
Black-box transitions
+ state-based failure specification
        ↓
Learned state-action Q-CBF
        ↓
Risk-guided sampling near recoverability boundary
        ↓
Task-policy training with action-level safety feedback
        ↓
Safety structure internalized in policy
```

“Residual around a frozen controller” 是重要工程选择：它避免直接在完整 actuator space 从零学习安全动力学。

### 动力学与安全假设

安全定义来自 state-based failure specification。Q-CBF 不是凭空发现“什么叫安全”，而是在给定失败定义下学习 recoverability boundary。

这意味着如果失败规格漏掉了脚部碰撞、关节热限制或接触冲击，那么蒸馏后的 policy 也不会自动拥有这些约束。

### 真机结果

论文展示 29-DoF humanoid：

- dodgeball avoidance；
- 从低障碍下方 locomotion；
- learned policy 直接转到硬件；
- 部署时不需要在线 safety filter。

作者还观察到，在同一个 safety specification 下改变 boundary sampling concentration，会产生从 crouching 到 backward-leaning “limbo” 的不同规避策略，说明 risk sampling 会直接塑造 policy 的行为风格。

### 鲁棒性与风险

最大的优点也是最大的风险：安全 filter 被“编译进 policy”以后，运行时少了一层独立检查。

更稳的产品结构可以是：

```text
LIMBO-style safe policy
        ↓
cheap hard limits
(joint / torque / collision emergency gate)
        ↓
hardware
```

不要因为训练阶段有 Q-CBF，就删除所有 runtime hard guard。

### 适合谁关注

人形 / 四足 RL、whole-body control、安全 RL、已有稳定 base controller、想减少在线 QP 开销的团队。

### 工程落地启发

如果现有机器人已有楼梯 / locomotion SDK，可以把学习控制限制在 residual velocity / posture command，而不是直接重学电机 torque，再用 boundary sampling 专门覆盖“快要不可恢复”的状态。

[论文](https://arxiv.org/abs/2609.22075)

## 4. Stochastic Neural Signed Swept Volume：碰撞检查不该只看离散 waypoint，整条机械臂扫过的空间都应该进入优化

**时间回补：v1 提交于 2026-09-18 01:51 UTC。**

### 为什么重要

机械臂规划常见做法是：

```text
trajectory
→ 每隔 Δt 采一个 state
→ 做 collision check
```

采样太稀会漏掉两个 waypoint 之间的碰撞；采样太密又会把优化拖慢。更麻烦的是，真实感知地图本身有噪声，而 learned collision model 也有 approximation error。

这篇工作把机器人一段运动的 **swept volume** 直接学习成 signed-distance probabilistic field。

### 算法模块

```text
Robot trajectory segment
        ↓
Neural Signed Swept Volume
        ↓
Probabilistic signed-distance field
  ├─ epistemic uncertainty
  └─ perception noise
        ↓
Chance constraint
        ↓
Trajectory optimizer
```

这样 optimizer 不是问“第 17 个 waypoint 碰没碰”，而是问“整个连续运动区间的碰撞概率是否满足约束”。

### 传感器与规划假设

环境来自带噪感知；robot geometry / motion representation 需要落入训练分布。概率场既包含模型 epistemic uncertainty，也纳入 perception noise，因此比 deterministic neural SDF 更适合直接进入安全约束。

### 实时性与真机

论文明确展示 high-dimensional manipulation 的 simulation 与 real hardware 结果，并将方法定位为 real-time chance-constrained trajectory optimization。不过摘要没有给出一个可跨硬件外推的统一毫秒级延迟，因此工程评估仍应实测：

```text
field query latency
optimizer iterations
continuous-risk violation
P95 planning time
```

### 鲁棒性与风险

概率输出本身需要 calibration。如果网络在 OOD geometry 上过度自信，chance constraint 会得到“数学上很安全、实际上不安全”的结果。

因此建议部署时同时记录：

```text
predicted collision probability
uncertainty decomposition
nearest training-domain distance / OOD score
fallback exact checker result
```

高风险动作仍可在最终执行前用精确几何 checker 做一次稀疏复核。

### 适合谁关注

机械臂、移动操作、窄空间轨迹优化、感知不确定性规划、需要 continuous collision safety 的 MPC / TAMP 系统。

### 工程落地启发

如果现有 planner 使用 ESDF / FCL，可先把 swept-volume model 放在**候选轨迹筛选层**，比较它与 dense interpolation collision checking 的 false-negative、规划时间和优化 smoothness，再决定是否让它直接承担约束。

[论文](https://arxiv.org/abs/2609.21211)

## 5. CoMET：接触模式组合爆炸，不一定只能靠树搜索；GPU 可以直接“多试很多种”

**时间回补：v1 提交于 2026-09-18 14:16 UTC。**

### 为什么重要

Contact-rich planning 的难点通常不是一条连续轨迹，而是先决定：

```text
什么时候左手接触？
什么时候右手释放？
推、滑、支撑、切换的 mode 顺序是什么？
```

mode 数量一多，组合空间迅速爆炸，因此传统方法倾向于复杂 heuristic、mixed-integer formulation 或 adaptive tree search。

CoMET 提出一个很符合现代 GPU 的反方向思路：**显式评估大量 mode sequence 其实可能已经足够便宜。**

### 算法模块

```text
Current contact mode
        ↓
Greedy local mode expansion
        ↓
Many candidate mode sequences
        ↓
GPU-parallel trajectory optimization / evaluation
        ↓
score candidates
        ↓
expand promising modes
```

论文消融表明，性能提升很大一部分来自高吞吐 trajectory evaluator，而不是额外复杂的搜索逻辑。

### 结果

在 planar pushing benchmark 中，CoMET 相对 optimization、sampling 和 tree-search baseline 在 solution quality / planning time 上具有竞争力，并在几乎所有实例中接近 full enumeration reference，同时用更少 evaluation、更短规划时间完成。

在 bimanual nonprehensile manipulation 中，当 mode space 变大时，GPU-friendly local expansion 的 planning success 高于论文测试的 adaptive tree search。

### 实时性与可复现性

论文说明 GPU 高吞吐是关键，但摘要未提供可直接拿来承诺真机实时性的统一延迟数字，也未在 arXiv 页面声明公开代码。因此当前更适合复现“并行 evaluator”这一思路，而不是把它当现成库。

### 工程风险

显式宽搜索会把问题从“搜索复杂度”转成“每个 candidate trajectory evaluator 是否足够可信”。如果简化接触动力学太粗，GPU 只是更快地产生大量错误评分。

因此建议把：

```text
mode search model
→ fast approximate dynamics

final candidate
→ higher-fidelity validation
```

做成两级。

### 适合谁关注

双臂非抓取操作、推拉、腿式接触规划、GPU trajectory optimization、复杂接触 TAMP。

### 工程落地启发

如果已经有 Isaac / MuJoCo 批量 rollout，可以先做一个很简单的基线：对几十个手写 contact-mode template 并行优化，而不是马上实现一套复杂 MCTS。现代 GPU 下，这个 baseline 可能比预期强很多。

[论文](https://arxiv.org/abs/2609.21803)

## 6. Tilt as a Certified Resource：多旋翼不只要“当前能产生所需 wrench”，还要保证下一瞬间有足够 wrench-rate 余量

**时间回补：v1 提交于 2026-09-18 10:10 UTC。**

### 为什么重要

全驱动 / 可倾转多旋翼通常做 control allocation：给定目标 wrench，找一组 motor speed / tilt angle 尽量省力地实现它。

问题是：一个“当前刚好能实现”的 allocation 可能已经把电机推到饱和边缘。下一瞬间突然来一阵风时，虽然理论最大 wrench 很大，却没有足够快的 motor wrench-rate 去补偿。

论文把这种能力称为 **readiness / wrench-rate authority**。

### 核心方法

作者构造 configuration-dependent、**motor-only** readiness certificate：可达 wrench-rate set 的 log-volume。

特别强调 motor-only，是因为 tilt servo 通常比电机慢。如果把 servo 的长期形态变化能力也计入瞬时证书，就会产生“ghost capacity”：数学上看还有控制余量，真实执行器却来不及动。

```text
motor state + tilt geometry
        ↓
reachable motor wrench-rate set
        ↓
log-volume readiness certificate
        ↓
CBF safety floor
        ↓
Unified Physical-Command QP
  ├─ motor torques
  └─ servo setpoints
```

Servo tilt 在这里不是直接被算作瞬时 authority，而是作为**改变未来 geometry、恢复 motor authority 的主动形态资源**。

### 结果与证据边界

论文在 articulated octorotor severe-gust simulation 中比较：

- classical allocator 会发散；
- 未认证的 articulated allocator 会跌破 readiness safety floor；
- CBF filter 能限制系统状态并保持 authority。

当前公开摘要只给出 simulation，不能把它写成已经通过真实飞行器强扰动验证。

### 工程风险

证书只和模型一样可靠。Motor torque rate、battery sag、ESC delay、servo speed 如果与模型偏差大，readiness margin 会被高估。

真机至少应在线估计：

```text
motor headroom
motor acceleration / torque-rate limit
battery voltage dependent derating
servo rate
CBF readiness margin
```

### 适合谁关注

可倾转多旋翼、全驱动无人机、抗风控制、control allocation、CBF、执行器饱和管理。

### 工程落地启发

这个思想也适用于普通四旋翼：除了记录 `thrust saturation`，再维护一个**未来 100–300 ms 可用控制增量 margin**。狭窄走廊里，飞行器真正危险的往往不是“现在姿态已经超界”，而是“虽然现在正常，但已经没有余量纠正下一次扰动”。

[论文](https://arxiv.org/abs/2609.21580)

## 7. GameLogicBench：Coding Agent 的测试必须检查“执行过程”，不能只看最终状态看起来对不对

**时间回补：v1 提交于 2026-09-18 09:51 UTC。**

### 突破性工程价值

很多自动验收只看：

```text
程序启动了吗？
最终输出对了吗？
截图看起来正常吗？
```

但一个游戏、交易系统或状态机可能中途严重违反规则，最后又偶然回到正确结果。

GameLogicBench 用 Godot 构造 **72 个 gameplay-logic coding tasks**，并让 evaluator 在**每个 simulation tick**读取黑盒 observable state，而不是只验最终一帧。

### Benchmark 结构

```text
Agent edits game project
        ↓
Isolated deterministic Godot execution
        ↓
Every simulation tick:
  behavioural assertions
        ↓
403 hand-designed scenarios
+ seeded variations
        ↓
1451 test cases
```

Evaluator 不读取 solution source code，也不相信 Agent self-report。

### 为什么 mutation validation 很重要

作者对 evaluator 本身做 mutation test：从正确实现中故意删除一个必需 capability，测试 judge 是否一定能拒绝这些 mutant，同时仍接受不同写法的正确实现。

论文发现：**如果不做 mutation validation，会有错误 Agent submission 被 evaluator 判为通过。**

这对现实 CI 很重要：测试数量多不代表测试有效，关键是它是否真的能杀死你关心的错误。

### 结果

- 20 个 model × scaffold 组合；
- 最好一次运行解决 52.78% tasks；
- Claude Code 下测试的 12 个模型都随着任务从 isolated mechanic → interacting systems → repo-scale feature 而明显下降；
- 多数失败提交其实可以运行，只是部分 required behavior 实现错误；
- network-open agent 会从公开仓库复制代码，说明 benchmark 的网络权限本身也是实验条件。

### 可复现性

代码和 benchmark 已公开：

[GameLogicBench](https://github.com/NJU-LINK/GameLogicBench)

作者将 task library、frozen judge、reference solution 分离，hidden seed 通过 argv 传入，不把 judge 直接暴露给 Agent。

### 适合谁关注

Codex / Claude Code 内部评测、游戏开发 Agent、状态机 / 工作流代码、需要真实 runtime behaviour 验收的团队。

### 工程落地启发

把普通单元测试升级成：

```text
scenario seed
+ invariant checked every step
+ mutant test for evaluator
+ hidden held-out scenarios
```

尤其适合机器人控制模拟器、协议状态机和业务 workflow。**先证明 evaluator 能抓住错误，再拿 evaluator 去评价 Agent。**

[论文](https://arxiv.org/abs/2609.21562) · [代码](https://github.com/NJU-LINK/GameLogicBench)

## 8. Grok 4.7：这次升级重点明显指向长时 Coding / Agent，而不只是单轮代码生成

**最新发布：SpaceXAI / xAI 于 2026-09-21 发布。**

### 突破性工程价值

Grok 4.7 相对 4.6 使用更大的 base model，并进行更长、偏向多小时任务的 RL 训练；官方强调 self-verification、long-context management 和 coding / knowledge work。

模型 API ID：

```text
grok-4.7
```

### API 与上下文

官方文档给出的主要规格：

```text
Input:  Text + Image
Output: Text
Context: 500,000 tokens
Reasoning effort:
  low / medium / high / xhigh
Default: high
```

200K prompt token 以下：

```text
Input        $2 / 1M
Cached input $0.50 / 1M
Output       $6 / 1M
```

超过 200K prompt 后价格提高到约两倍。Fast variant 使用同一模型、token 速率约 2×、价格约 2×，目前只在 Cursor 和 Grok Build 提供，不在公开 xAI API。

### 官方基准怎么读

xAI 发布页给出：

```text
CursorBench 4.0    46.3%
DeepSWE v1.1       71.0% (high effort)
Terminal-Bench 4.0 38.0%
AA Briefcase       1657
EEBench             64.0%
```

这些是厂商自己的发布 benchmark，应作为“值得自己复测的信号”，不能直接换算成“实际项目一定比某模型强”。

更有价值的是，它明确把训练和产品入口都朝长时 coding harness 收敛：Grok Build 默认使用 Grok 4.7，API 也支持 reasoning、多轮 encrypted reasoning content、tool use。

### 是否适合真实研发流程

最值得做的不是立刻换默认模型，而是放进现有 Agent regression set 做：

```text
同一 repo task
同一 harness
同一 tool permissions
同一 reasoning budget

比较：
success
wall-clock
input/output token
retries
human correction
```

特别要注意 500K context 并不代表应该把整个仓库塞进去；超过 200K prompt 后价格档位变化，也会直接改变长 session 的经济性。

### 权限 / 安全边界

官方还强调新的 safeguard stack，但这仍然不能替代 harness 外的 filesystem / network / write authorization。模型变强以后，`--always-approve` 这类配置的 blast radius 反而更大。

### 适合谁关注

Cursor / Grok Build 用户、多模型 Coding Agent 平台、长任务 code migration、希望用 500K context 做 repo-level 工作的团队。

### 工程落地启发

建议先只把 Grok 4.7 放进“高难任务 fallback”而不是全量默认：连续一周记录哪类任务它明显优于当前主模型，再决定 routing。模型路由应该来自自己的 task distribution，而不是发布会 benchmark。

[官方发布](https://x.ai/news/grok-4-7) · [模型文档](https://docs.x.ai/developers/models/grok-4.7) · [Release Notes](https://docs.x.ai/developers/release-notes)

## AI Coding 实战技巧精选

### 技巧 1｜给本地 MCP / Bash Agent 套 `srt`，默认断网、只允许当前仓库写入

- **来源**：[Anthropic `sandbox-runtime` 官方仓库](https://github.com/anthropics/sandbox-runtime)，截至 2026-09-21 持续更新；目前标记为 Beta Research Preview。
- **一句话结论**：不要只靠“执行前弹权限框”。对会运行 shell、MCP server、package manager 的 Agent，直接用 OS 级 sandbox 限定文件和网络，让越权动作即使被模型提出也执行不了。
- **具体怎么做**：

  1. 安装：

     ```bash
     npm install -g @anthropic-ai/sandbox-runtime
     ```

  2. 先把普通命令放进 sandbox：

     ```bash
     srt "npm test"
     srt "curl https://github.com"
     ```

  3. 建 `~/.srt-settings.json`，只允许当前目录写入，同时保护 SSH 与 `.env`：

     ```json
     {
       "filesystem": {
         "denyRead": ["~/.ssh"],
         "allowWrite": ["."],
         "denyWrite": [".env", "secrets/"]
       },
       "network": {
         "allowedDomains": ["github.com", "*.github.com", "api.github.com"],
         "deniedDomains": []
       }
     }
     ```

  4. MCP server 原本：

     ```json
     {
       "command": "npx",
       "args": ["-y", "@modelcontextprotocol/server-filesystem"]
     }
     ```

     改成：

     ```json
     {
       "command": "srt",
       "args": ["npx", "-y", "@modelcontextprotocol/server-filesystem"]
     }
     ```

- **适合什么场景**：Claude Code / Codex 周边工具、自研 Agent、第三方 MCP server、需要执行 npm / Python / shell 的代码 Agent，尤其适合开发机上不想再起完整 Docker 的场景。
- **注意**：`srt` 是 research preview；域名 allowlist 只能限制去哪里，不能保证允许域名里的每个请求都安全。特别是允许 `github.com` 以后仍可能发生数据外传；Linux 还依赖 bubblewrap / seccomp 环境，Windows 当前为 alpha。

### 技巧 2｜Agent 调写操作前先过“意图策略”，不要只检查参数是否合法

- **来源**：[Google Developers Blog：Build zero-trust AI agents that judge intent, not just syntax，2026-09-15](https://developers.googleblog.com/build-zero-trust-ai-agents-that-judge-intent-not-just-syntax/)；附带一手开源 demo。
- **一句话结论**：`issue_refund(amount=120)`、`delete_file(path=...)`、`deploy(prod)` 参数完全合法，也可能违背用户真实意图。把**用户请求 + 会话历史 + 候选 tool call + 业务规则**交给一个独立 policy gate，在 tool 真正执行前返回 ALLOW / DENY。
- **具体怎么做**：

  1. 先直接跑 Google 的公开 demo：

     ```bash
     git clone https://github.com/GoogleCloudPlatform/generative-ai.git
     cd generative-ai/agents/adk/zero-trust-agents-2/
     ./demo/run_part2_demo.sh
     python3 -m unittest demo/test_runtime_governance.py
     ```

  2. 把高风险工具列成 policy target，而不是在 Agent prompt 里写一句“请谨慎”：

     ```yaml
     name: production-write-policy
     target_tools: [deploy_prod, delete_resource, issue_refund]
     constraints: |
       Only execute when the current user's request explicitly authorizes
       this exact state-changing action and required approval is present.
     enforcement: BLOCK
     ```

  3. Runtime 流程固定成：

     ```text
     user intent
        ↓
     agent proposes tool(args)
        ↓
     policy gate
       ALLOW → execute
       DENY  → suppress tool
     ```

  4. 再做 session-level 累积检查。例如单次写入都小于阈值，也要统计：

     ```text
     repeated_tool_calls
     cumulative_amount
     repeated_writes_same_entity
     ```

- **适合什么场景**：自动部署、数据库写入、退款 / 工单、GitHub merge、删除文件、机器人高风险 skill、任何“参数合法但语义上可能越权”的工具。
- **注意**：LLM-based semantic gate 本身也不是形式证明；最关键的额度、路径、角色权限仍应有 deterministic check。意图判断用于补传统 schema / regex 看不到的语义层，不应替代硬权限。

## 经典论文回顾

### MSCKF：经典复盘——从固定计算预算与观测可信度重新看滤波式 VIO

Anastasios I. Mourikis 与 Stergios I. Roumeliotis 的 **A Multi-State Constraint Kalman Filter for Vision-aided Inertial Navigation** 发表于 **ICRA 2007**。它是滤波式 VIO 最重要的经典工作之一。([DOI](https://doi.org/10.1109/ROBOT.2007.364024))

本工作已在 **2026-08-05** 的简报索引中覆盖；本期不把它当作新的经典论文条目，而是结合今天的 Noctif3R 与 SLIM-init，从**固定计算预算、观测可信度和退化初始化接口**三个角度重新复盘。

### 核心问题

经典 EKF-SLAM 如果把所有 landmark 都放进 state：

```text
x = [IMU state, landmark_1, landmark_2, ...]
```

环境越大，state / covariance 越大，视觉特征越多，计算和内存都会迅速膨胀。

另一方面，如果完全不保存历史 camera pose，一个 feature 跨多帧观测产生的几何约束又利用不充分。

MSCKF 的折中是：

> **保存一小段历史 camera pose clone，但不把短期视觉 feature 当永久 state。**

### 状态结构

典型状态可以抽象成：

```text
x = [IMU navigation state,
     camera_pose_1,
     camera_pose_2,
     ...,
     camera_pose_N]
```

IMU 高频传播；每当视觉帧进入，就把对应 camera pose clone 进 filter state。

一个 feature 在多个 clone 中被看到以后，先构造多视图重投影残差：

```text
r ≈ H_x δx + H_f δf + n
```

其中 `δf` 是 feature 3D position 的误差。

关键一步是找 `H_f` 的左零空间 `A`：

```text
Aᵀ H_f = 0
```

于是：

```text
Aᵀ r = Aᵀ H_x δx + Aᵀ n
```

feature state 被消掉，但它跨多个 camera pose 提供的几何约束仍然保留下来，用来 update IMU + pose clones。

这就是 “Multi-State Constraint” 的核心。

### 为什么当年重要

它同时解决了三个工程问题：

1. 不需要把海量 3D feature 永久加进 EKF state；
2. 可以利用 feature 在多个相机位姿之间的几何约束；
3. 计算复杂度相对 feature 数保持可控，适合实时导航。

原论文已经在大尺度真实城市 camera / IMU 数据上展示高精度实时 vision-aided inertial navigation。

### 传感器与假设

经典 MSCKF 主要依赖：

- camera + IMU；
- 足够准确的内外参和时间同步；
- feature 在观测窗口内近似静态；
- EKF 线性化与噪声模型合理；
- 运动提供足够可观测性。

它并不会自动解决今天 SLIM-init 提到的低视差 / 退化启动问题；初始化、时间偏差、外参、rolling shutter、动态特征仍需要额外处理。

### 今天仍然在使用的思想

今天的优化式 VIO / SLAM 更流行因子图与 sliding-window bundle adjustment，但 MSCKF 的几条思想仍非常现代：

```text
fixed compute budget
pose cloning
feature marginalization / nullspace projection
high-rate IMU propagation
bounded visual update window
```

对于无人机、AR/VR、嵌入式设备，这种“状态大小可控、延迟可预测”的结构仍然很有吸引力。

### 已被后续扩展的部分

后续系统加入了：

- observability-constrained EKF；
- FEJ / consistency improvement；
- stereo / multi-camera；
- online extrinsic / time-offset calibration；
- SLAM feature 与长期 map；
- zero-velocity update；
- 更完善的 dynamic initialization。

现代开源参考中，[OpenVINS](https://docs.openvins.com/) 是非常好的 MSCKF 系工程实现，官方仓库为 [rpng/open_vins](https://github.com/rpng/open_vins)。

### 可复现性

如果今天想真正理解 MSCKF，不建议只读推导。用 OpenVINS 跑 EuRoC / TUM-VI，额外把以下量画出来：

```text
clone count
feature track length
update residual
innovation covariance
NEES / NIS
IMU bias
CPU time per update
```

然后人为缩短窗口、降低 feature 数、加入 1° 外参误差，观察 consistency 怎么变化，会比单看 ATE 更有价值。

### 对当前工程项目的重新解读

今天很多机器人系统可以采用“两种估计器分工”：

```text
高频、固定预算 local VIO
→ MSCKF / OpenVINS 类滤波器

低频、全局一致性
→ LiDAR / factor graph / loop closure / RTK
```

尤其当主系统已有 LIO-SAM 时，视觉不一定非要再做一套全局 visual SLAM。一个稳定、可预测延迟的 MSCKF 可以只负责局部短时视觉惯性约束，在 LiDAR 退化、极暗 / 低纹理边缘状态下提供补充健康量或相对运动信息。

今天 Noctif3R 与 SLIM-init 也可以放在这条经典主线上理解：现代 VIO 不是把 EKF 换成大网络就结束，而是在**观测什么时候可信、初始化什么时候可观、端侧计算什么时候可承受**这些系统问题上继续补强。

[DOI](https://doi.org/10.1109/ROBOT.2007.364024) · [OpenVINS](https://docs.openvins.com/) · [OpenVINS GitHub](https://github.com/rpng/open_vins)

## 今日结论

今天机器人部分最值得带走的关键词不是“更大模型”，而是 **authority、observability 与 continuous safety**。

Noctif3R 和 SLIM-init 从状态估计侧提醒我们：系统必须知道什么时候测量没有信息、什么时候 initialization 条件不足。一个 estimator 只报 pose 而不报 observability / confidence，长期来看很难做成稳定产品。对于低线数 LiDAR、长走廊、极暗室内和无人机这种典型退化环境，健康量应该和 pose 本身同等重要。

LIMBO 与 Tilt 则从控制侧回答了另一种“可观测性”：当前动作虽然合法，系统是否还拥有**恢复能力**？LIMBO 学 recoverability boundary，Tilt 直接计算 motor wrench-rate authority。安全控制正在从“不要越过边界”升级到“不要把自己开到一个下一拍已经救不回来的状态”。

Stochastic Neural Swept Volume 与 CoMET 又说明 GPU 的作用开始从“跑更大网络”转回优化器本身：一个用 GPU / learned field 加速连续碰撞约束，一个用 GPU 高吞吐直接评估大量 contact mode。传统 motion planning 很多“因为算不起而不得不做的启发式”，值得在 2026 年硬件上重新测一遍。

AI Coding 侧，GameLogicBench 给出的结论非常实用：**验证器也需要被验证。** 测试全绿不等于测试真的覆盖了业务约束；用 mutation test 主动构造“应该失败的实现”，检查 CI 是否确实把它杀掉，是比增加另一个 LLM Judge 更扎实的办法。

Grok 4.7 的发布则继续强化长任务 Coding 模型的竞争方向：更长 context、更长 RL horizon、更强 self-verification。但 context window 扩大并没有改变系统工程原则——权限、sandbox、测试和 artifact gate 仍然应该留在模型外部。今天 AI Coding 两条实战技巧刚好对应这一点：shell / MCP 用 OS 级 sandbox，state-changing tool call 在执行前做独立意图治理。

如果把今天整期压缩成一句话：

> **可靠机器人和可靠 Coding Agent 都不应该只回答“我现在能不能做”，而应该持续回答“我是否有足够证据、足够控制余量，以及失败以后还有没有恢复空间”。**

## 最值得深入研究或尝试复现的方向

1. **给现有 LIO / VIO 增加统一 Observability Health API。** 不改主估计器，先输出 `visual_information / lidar_localizability / init_condition / tracking_valid`，再把它接到 sensor fusion 权重和控制降级逻辑。重点在长走廊、暗室、低视差起飞三个故障场景测“提前多久能预测失败”。

2. **做一个 SLIM-init 思路的 Line/VP Fallback。** 正常 VIO 初始化保持原方案，只在 parallax / excitation 不足时启用 line VP rotation constraint。测试直线起飞、走廊匀速、缓慢平移，比较初始化成功率和 bias / scale 收敛时间。

3. **把 Safety Margin 从“距离”升级成“恢复能力”。** 对无人机可以先实现简化 `thrust_headroom + attitude_rate_headroom`；对四足可以用 residual safety value / fall-recovery score。控制器接近 authority floor 时主动降速，而不是等姿态已经失稳再救。

4. **GPU Contact-Mode Baseline。** 如果已有 Isaac / MuJoCo，枚举一小组接触 mode template，批量 rollout / trajectory-optimize，和当前 heuristic planner 做 A/B。先验证“暴力并行”到底有多强，再决定是否值得实现复杂搜索算法。

5. **给 Coding Agent Regression Suite 加 Mutation Test。** 从 20–50 个真实任务里，每个 task 人工或脚本制造一个“缺一项能力但能编译”的 mutant；只有 evaluator 能稳定拒绝这些 mutant，才允许这组测试作为 Agent 发布 gate。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [Noctif3R](https://arxiv.org/abs/2609.21114)
- [SLIM-init](https://arxiv.org/abs/2609.21186)
- [LIMBO](https://arxiv.org/abs/2609.22075)
- [Stochastic Neural Signed Swept Volume](https://arxiv.org/abs/2609.21211)
- [Contact-Rich Motion Planning via GPU-Parallel Mode Evaluation / CoMET](https://arxiv.org/abs/2609.21803)
- [Tilt as a Certified Resource](https://arxiv.org/abs/2609.21580)
- [GameLogicBench](https://arxiv.org/abs/2609.21562) · [GitHub](https://github.com/NJU-LINK/GameLogicBench)
- [Grok 4.7 官方发布](https://x.ai/news/grok-4-7) · [模型文档](https://docs.x.ai/developers/models/grok-4.7)
- [Anthropic Sandbox Runtime](https://github.com/anthropics/sandbox-runtime)
- [Google Zero-trust Agents Runtime Governance](https://developers.googleblog.com/build-zero-trust-ai-agents-that-judge-intent-not-just-syntax/)
- [MSCKF DOI](https://doi.org/10.1109/ROBOT.2007.364024) · [OpenVINS](https://docs.openvins.com/) · [OpenVINS GitHub](https://github.com/rpng/open_vins)
