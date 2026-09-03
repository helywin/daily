---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-03"
date: 2026-09-03 09:00:00 +0800
description: "多机器人连续时间相对定位、无对应点云 BA、MPC 与 RL 融合、ProxPI、Facet-0、VLA 自适应动作块、HarnessDev 与 Gemini 3.8 Flash。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-03

## 摘要

截至 2026-09-03 09:00（Asia/Shanghai），arXiv Robotics 最新公开批次为 2026-09-02，共 73 条，其中 39 条为 new submissions；Software Engineering 同日共 55 条，其中 29 条为 new submissions。本期首先检查最近 24 小时：真正满足高质量、可完整核验、未进入历史索引并且与 SLAM / 控制高度相关的新增条目不足 5 条，因此按任务规范继续扩展到最近 7 天。CT-RIO 的 v4 于 2026-09-02 更新，Gemini 3.8 Flash 也于 2026-09-02 正式发布；其余论文的 v1 主要提交于 9 月 1 日，均明确标记为“时间回补”。（[arXiv Robotics](https://arxiv.org/list/cs.RO/new)，[arXiv Software Engineering](https://arxiv.org/list/cs.SE/new)）

今天 SLAM / 状态估计方向最值得优先看的是 **CT-RIO**。它不是普通“多机器人 EKF”，而是把异步观测、跨机器人时钟偏差、连续时间状态和大规模并行优化统一到一套 reference-centric 相对定位框架中。最新 v4 明确使用 Clamped Non-Uniform B-splines 消除普通未钳位 B-spline 的查询延迟，再通过 closed-form extension / shrinkage 和 knot-keyknot 策略兼顾高频状态输出与稀疏优化变量；实验中可从最大 264 ms 时钟偏移在 3 s 内收敛到亚毫秒，并达到 0.046 m / 1.8° RMSE。对多机器人、前后多 LiDAR、无线测距和异步视觉系统，这类“时间本身也是状态”的设计比事后硬对齐时间戳更值得关注。（[论文](https://arxiv.org/abs/2602.22006)）

点云地图侧，**Adaptive Depth-Map-Guided Bundle Adjustment** 提出一个很有意思的“无显式对应”多视图点云 BA：把工业场景压到全局 2.5D 网格，每个 cell 在需要时维护多个深度假设，再同时优化传感器 pose 与 layered depth。它绕开重复钢材、弱纹理和部分重叠场景中最容易出错的 feature / correspondence；21 帧、每帧原始约 130 万点的测试中，完整流程 24.4 s，明显低于论文所测的 TEASER+ICP、TEASER+PGO、TEASER+BA 和 3D occupancy 方案。它不是高频 SLAM 前端，但很适合工业扫描、离线地图精修和多视角测量。（[论文](https://arxiv.org/abs/2609.01089)，[代码](https://github.com/YiranZhou-Robotics/ADM-BA)）

控制侧本期两项工作都在重新安排“学习器应该插在哪里”。**SG-RL** 不让 RL 直接控制赛车，而是让 PPO 在线调 NMPC 的 7 个 cost weight；真实闭环回报仍是优化目标，MPC solver sensitivity 只作为有界辅助梯度。两个高保真全尺寸赛车仿真平台上，最强变体达到 PPO 最佳回报所需样本最多减少 70.6%。需要严格区分：论文的 NMPC 架构已经在真实 AV-24 / EAV-24 赛车上验证，但本文学习出来的权重策略仍在高保真仿真中训练和评测，作者没有声称这些 learned policy 已经上真车。（[论文](https://arxiv.org/abs/2609.01061)）

**ProxPI** 则指出 policy-guided MPPI 一个结构性坑：如果每个 replanning cycle 都把采样中心重新搬到 learned prior，prior 一旦 OOD，优化器上一周期已经学到的 correction 会被反复清零。ProxPI 保持 MPPI sampling center 在自己的 nominal sequence 上，只把 learned prior 作为 soft proximal cost。结果是 unseen obstacle、Go2 rearing、G1 squat 等 prior mismatch 下仍能接近 vanilla MPPI；真实 Franka FR3 中，行为克隆 prior 只学过一个目标，目标切换后 warm-start 停留在旧位置，而 ProxPI 可以脱离 prior 并到达新目标。（[论文](https://arxiv.org/abs/2609.00941)）

机器人基础模型侧，**Facet-0** 把“制造业精密装配缺的是接触数据”直接做成系统。ManuFacet-1K 目标规模为 1,000 小时 force-synchronized 精密装配数据，覆盖 UR7e、xArm、Franka 等本体；模型把 vision-language / kinematics 与因果 wrench history 结合，联合生成 action chunk 和未来 wrist-wrench profile，再用 Action-Wrench Critic 对接触结果做分布式价值判断。项目页给出的运行分层非常工程化：语义规划约 5–10 Hz、force residual 闭环约 20 Hz、底层 precision control 约 200 Hz。相比让一个大 VLA 直接输出所有高频控制，这种多速率接口更接近工业机器人。（[论文](https://arxiv.org/abs/2609.01596)，[项目页](https://pine-lab-ntu.github.io/facet-0/)）

VLA runtime 方面，**Knowing When to Stop** 研究固定 action chunk 长度的根本矛盾：短 chunk 反应快但频繁重推理，长 chunk 平滑却会在任务语义变化后继续执行过期动作。作者发现 cross-attention dispersion entropy 在预测 horizon 拉长时会进入高熵平台，并据此做 training-free 截断。RoboTwin、LIBERO 与真实双臂任务中均有改善；真实三任务平均成功率从最佳固定 chunk 的 47.5% 提升到 61.7%，单次推理延迟只从约 0.266 s 增至 0.273 s。对 VLA 部署来说，这比单纯继续调固定 8/16/32 步 chunk 更值得做成 runtime policy。（[论文](https://arxiv.org/abs/2609.00908)）

AI Coding 侧，**HarnessDev** 把评测单位从“Agent 最终答对没有”改成“它自己构建的 harness 到底是不是一个可运行、可泛化的软件系统”。Creation 阶段从最小 seed 构建完整执行系统，Evolution 阶段再根据 downstream feedback 修改自己的 harness。最值得警惕的结果是：可见反馈上的 improvement 只有 34/64 次版本切换与 held-out 方向一致，9 个最终版本里只有 2 个真正在 held-out 上最优。也就是说，“Agent 自己跑 benchmark 发现自己变好了”远不足以批准生产 harness 升级。（[论文](https://arxiv.org/abs/2609.01437)，[项目页](https://self-developing-agents.github.io/)）

大模型方面，Google DeepMind 于 **2026-09-02 正式发布 Gemini 3.8 Flash**。它基于 Gemini 3.7 Flash，继续支持可调 effort level，以质量 / 成本 / 延迟之间的平衡为主要产品接口；支持文本、图像、音频、视频输入，context window 最高 1M token、输出最高 64K token，并明确针对 software engineering、long-horizon knowledge work 和 agentic execution 优化。Google 同时在 model card 中提醒模型仍会 hallucinate、部分请求存在响应变慢或超时，并且高 effort 会消耗更多 token。因此真实 Coding Agent 不应该“版本一更新全量切换”，而应按 Scout / Worker / Reviewer 等角色做独立 A/B 与回归。（[模型卡](https://deepmind.google/models/model-cards/gemini-3-8-flash/)，[模型页](https://deepmind.google/models/gemini/flash/)）

## 1. CT-RIO：连续时间多机器人定位开始真正处理“异步 + 时钟偏差 + 高频输出”

**最近 24 小时实质更新：v1 于 2026-02-25 提交，v4 于 2026-09-02 07:28 UTC 更新。本期首次覆盖。** [论文](https://arxiv.org/abs/2602.22006)

### 为什么重要

多机器人协同定位里，最常被简化掉的两件事恰好很难简化：

1. 不同机器人传感器观测不是同一时刻到达；
2. 各机器人本地时钟本身可能存在固定 offset。

如果先把数据插值到同一 timestamp，再交给普通离散时间滤波器，相当于把时间误差提前变成了空间误差。高速运动、长 lever arm 和低延迟协同任务里，几十毫秒时间差足够产生明显相对位姿偏差。

CT-RIO 的核心思路是：不要把异步问题“预处理掉”，而是把机器人状态直接建模成可在任意时刻查询的连续时间函数，并让时间 offset 与相对运动一起进入优化。

### 算法模块

系统可以拆成四层：

```text
IMU / Inter-Robot Measurements
            ↓
Clamped Non-Uniform B-Splines
            ↓
Closed-form Extension / Shrinkage
            ↓
Knot-Keyknot Online State Management
            ↓
Reference-Centric Sliding Window
            ↓
Robot-wise Subproblems
            ↓
Asynchronous Block Coordinate Descent
```

作者用 **Clamped Non-Uniform B-splines（C-NUBS）** 取代常见未钳位 spline，主要目的是消除连续时间轨迹在“最新时刻附近无法立即可靠查询”的尾部延迟。随后增加 closed-form extension / shrinkage，使在线系统可以添加、删除 knot，同时保持已有 spline shape 不被破坏。

`knot-keyknot` 则解决另一个工程矛盾：如果所有高频状态都进入优化，变量会迅速膨胀；如果 knot 太稀，又无法提供高频 relative pose。CT-RIO 允许高频扩展 spline，但只保留更稀疏的 keyknot 承担核心优化。

### 传感器与可观测性假设

框架是 reference-centric relative-inertial odometry，依赖 IMU 和 inter-robot relative constraints。它并不等价于“任何机器人之间只要通信就能定位”。

如果机器人长时间没有相对观测、运动缺乏激励或 relative measurement 自身存在严重 outlier，时间 offset 与运动状态仍可能弱可观。无线测距、视觉相对位姿、UWB、LiDAR 相对约束的噪声模型也需要分别设计。

### 实时性与结果

论文报告：

- 最大约 **264 ms** 初始时钟偏差，可在 **3 s 内收敛到亚毫秒**；
- 相对定位 RMSE 约 **0.046 m / 1.8°**；
- 高速运动场景相对已评测公开方法最高改善约 **60%**。

这类结果真正重要的地方是同时满足“online time-offset estimation”和“高频相对状态”，而不是离线把整段轨迹重新对齐。

### 鲁棒性、可复现性与风险

当前论文是 v4、仍投稿 T-RO，公开页面没有给出稳定官方代码仓库，因此可复现性目前只能评为中等。

生产系统应特别区分：

```text
clock offset
clock drift
network delay
queue jitter
packet reorder
```

CT-RIO 主要针对可估的时钟 offset / 异步观测，并不意味着这些通信问题可以全部被一个 offset state 吸收。

### 适合谁关注

多机器人 SLAM、无人机编队、UWB / 视觉相对定位、多机协同建图、多个计算节点之间存在不同硬件时钟的系统。

### 工程落地启发

对多 LiDAR / 多计算机机器人，建议把 sensor / robot timestamp 从日志字段升级成正式状态：

```text
source_clock
estimated_offset
uncertainty
last_sync_time
jitter
excitation_score
```

先做 shadow estimator，不急着自动修改所有时间戳。只有在激励充分、innovation 一致时才允许更新 offset；低激励时冻结，这比让时间参数在直线匀速阶段自由漂更可靠。

## 2. Adaptive Depth-Map BA：把工业多视图点云从“找对应”改成“共同解释一张分层深度地图”

**时间回补：v1 提交于 2026-09-01 11:28 UTC。** [论文](https://arxiv.org/abs/2609.01089) · [代码](https://github.com/YiranZhou-Robotics/ADM-BA)

### 为什么重要

工业废钢、钢坯、焊接件和大型设备扫描里，经典 multi-view registration 最容易坏在 correspondence：

- 表面重复；
- 金属反光、弱纹理；
- 视角间 overlap 小；
- 局部边缘非常相似；
- 上下层结构在投影中重叠。

一旦 pairwise correspondence 错了，后面的 pose graph / BA 再强，也是在优化错误约束。

这项工作的思路是取消显式点对点匹配，让所有观测共同去解释一张全局结构化 depth map。

### 算法模块

```text
Multi-view Depth / Point Clouds
          ↓
Global 2.5D Grid
          ↓
Adaptive Multi-Depth Hypotheses per Cell
          ↓
Softmax Layer Assignment
          ↓
Joint Pose + Depth Optimization
          ↓
Metric Industrial Reconstruction
```

普通 height / depth map 每个 `(x,y)` 只有一个深度，会把对象侧面、支撑面和遮挡层硬平均。这里每个 cell 在深度结构简单时仍保持单层；检测到冲突时才增加多个 depth hypothesis，既保留 2.5D 紧凑性，又允许同一投影格内存在多个表面。

### 传感器与几何假设

方法更适合**主要从上方观察**的工业测量任务，例如 LiDAR、structured-light、RGB-D 多视角扫描。它不是通用任意拓扑 3D occupancy 表示：如果场景存在大量垂直洞穴、完全封闭的多层结构，单一全局投影方向会成为限制。

另外，它取消的是**显式 feature correspondence**，不是取消几何可观测性。所有视角几乎没有重叠时，BA 仍然没有足够信息恢复正确相对 pose。

### 实时性

论文在一个 21 帧序列上测试，每帧原始约 **130 万点**，0.015 m voxel 下采样后约 **2.8 万点**：

- 本方法完整流程：**24.4 s**；
- BALM2：35 s；
- T+BA：245 s；
- T+ICP：500 s；
- T+PGO：691 s；
- 3D occupancy：1750.5 s。

这些数字包含加载、预处理、地图初始化和优化，因此更像**批量多视图重建**，不能误写成 24 Hz 或实时 SLAM。

### 鲁棒性与可复现性

官方代码已经公开，可复现性较好。论文也展示了固定单层 depth map 的消融：多深度假设对于物体边界和重叠区域确实是核心，不只是换了优化器。

风险主要是网格分辨率和投影方向。0.025 m 级全局网格适合大件工业测量，但如果要做毫米级装配，representation 本身就需要重设。

### 适合谁关注

工业 3D 扫描、大型工件测量、机器人切割/打磨前建模、多视图 LiDAR / structured-light registration。

### 工程落地启发

这篇工作和经典 Bundle Adjustment 放在一起看很有意义：**BA 的核心不是“相机专属”，而是联合优化共享潜在结构与传感器状态。**

如果已有多 LiDAR / 多视角地图，除了继续做 pairwise GICP，也可以尝试：

```text
各视角局部点云
      ↓
共同 Voxel / Surfel / Layered Depth Latent Map
      ↓
Pose + Map Statistics 联合优化
```

减少“错误 correspondence 被当成硬事实”进入后端的机会。

## 3. SG-RL：让 RL 学 MPC 的权重，而不是替代 MPC

**时间回补：v1 提交于 2026-09-01 10:55 UTC。** [论文](https://arxiv.org/abs/2609.01061)

### 为什么重要

MPC 的 cost weight 往往是工程师最痛苦的参数之一：

```text
tracking
speed
jerk
steering rate
lateral acceleration
```

权重固定时，很难同时覆盖直道、急弯、不同抓地条件和模型误差。

让 RL 在线调权重很自然，但普通 PPO 完全依赖环境采样，样本效率低；直接对 differentiable MPC 做 solver gradient 又容易因为 prediction model 与真实 plant 不一致而优化错目标。

SG-RL 的折中非常合理：**真实闭环 return 仍由 RL 决定方向，solver gradient 只提供“局部应该往哪里试”的辅助信息。**

### 算法模块

策略动作不是方向盘，而是 7 个 NMPC cost weight：

```text
q_lateral
q_heading
q_velocity
q_longitudinal_accel
q_lateral_accel
r_jerk
r_steering_rate
```

NMPC 仍负责：

- steering / jerk 硬约束；
- steering range；
- powertrain envelope；
- longitudinal / lateral friction ellipse；
- receding-horizon trajectory optimization。

作者构造四种 PPO 变体，把 solver sensitivity 分别用于 actor update scaling、policy loss、advantage 和 value learning。

### 动力学假设

最关键的实验设计是**故意让 NMPC prediction model 比 plant simulator 简化**，包括轮胎、负载转移、空气动力和 actuator dynamics，从而测试 solver gradient 在 model mismatch 下是否仍有价值。

因此它并不是在一个“优化器模型和环境完全相同”的理想条件下证明自己。

### 实时性与结果

在 AV-24 / Monza 上，SG-SCA 比 PPO 提前约 60% 样本达到 PPO 最佳平均回报；EAV-24 / Yas Marina 上，最强结果约 **70.6% fewer samples**。

单 seed 预算实验里，SG-SCA / SG-LOS 用 810K samples，而 PPO 需要 1.94M；训练本身在普通 Apple M2 / M4 机器上完成，说明这里昂贵的不是超大深度网络。

### 必须准确理解的真机边界

论文使用的是**全尺寸赛车高保真仿真**；NMPC prediction / simulation model 来自真实赛车数据，且同一 Weights-varying NMPC 架构已经在 2025 年 Yas Marina 与 Modena 的实体赛车中验证。

但作者明确说明：**learned weight policy 仍留在仿真训练和评测，因为实体赛车极限探索风险和成本太高。**

因此不能把论文写成“RL 策略已在真车达到 70.6% 提升”。

### 适合谁关注

已有成熟 MPC / NMPC，但希望在线适配 cost、模型误差和环境变化的无人机、车辆、四足和机械臂团队。

### 工程落地启发

很适合采用下面的权限边界：

```text
RL / Small Network
      ↓
bounded MPC parameters
      ↓
MPC constraints
      ↓
actuator command
```

学习器不直接拥有最终 actuator authority，而且权重动作本身有上下界；这比直接学习控制量更容易做回归和故障降级。

## 4. ProxPI：Learned Prior 应该是“软建议”，不应该每周期重置 MPPI 的搜索中心

**时间回补：v1 提交于 2026-09-01 09:03 UTC。** [论文](https://arxiv.org/abs/2609.00941)

### 为什么重要

Policy-guided MPPI 很诱人：让 RL / BC / Flow policy 给一个好初值，MPPI 只做少量 refinement。

问题在于最常见的 warm-start 结构会做：

```text
每个控制周期
learned prior → sampling center
```

一旦 prior 因新障碍、新目标或新动作语义进入 OOD，MPPI 上个周期辛苦找到的 correction 会在下一周期被 prior 再次覆盖。

作者把这个现象称为结构性的 reset effect，而不是简单“样本数量不够”。

### 算法模块

ProxPI 不改变 MPPI 核心 sampling center：

```text
Nominal MPPI Sequence
        ↓
Sampling / Rollout
        ↓
Task Cost
+
Soft Proximity Cost to Learned Prior
        ↓
MPPI Update
```

prior 变成一项 proximal regularizer，而不是整个探索分布的中心。

因此：

- prior 对时，可以帮助；
- prior 错时，task cost 仍能把 nominal 拉走；
- 上周期 correction 会自然传到下一周期。

### 动力学与先验假设

论文跨五类平台验证 environment mismatch 与 behavior mismatch：2D navigation、2D reaching、Franka FR3、Go2、G1。

真实 FR3 使用 ACT 行为克隆 prior，只观察关节位置和速度，预测 40-step joint-position chunk，而且训练时只见过一个 end-effector target。

这非常刻意：作者就是要制造“prior 对旧任务很好，但对新 command 明显错”的情况。

### 实时性与结果

仿真 OOD 中，policy-centered warm-start 在 FR3 / Go2 / G1 任务上接近失败，而 ProxPI 的 normalized progress 分别约 **0.953 / 0.895 / 0.952**，基本回到 vanilla MPPI 水平。

真实 FR3 中，两种 controller 先在约 8 s 到达训练目标；8.3 s 将 command 切换到未见位置后，ProxPI 约在 14.3 s 到达新目标，而 warm-start 仍停留在训练目标附近。

更关键的是：**单纯增加 rollout K 或 sampling variance 并不能稳定救回 warm-start。** 这说明问题不是“再多采一点”就能解决。

### 鲁棒性、可复现性与风险

当前未见稳定官方代码入口，因此复现成本主要在 MPPI 与 learned prior 接口。

ProxPI 也不是永远优于不使用 prior：proximal weight `α` 太大时，它同样会被错误 prior 限制。工程上必须给 `α` 做可解释范围和 OOD fallback。

### 适合谁关注

已有 RL / VLA / BC policy，又希望用 MPPI 做在线约束和修正的机器人团队。

### 工程落地启发

推荐把 learned policy 的职责改成：

```text
proposal / reference / soft cost
```

而不是：

```text
每周期覆盖 optimizer internal state
```

这和“Foundation Model 不应该拥有最终 safety authority”是同一种系统原则。

## 5. Facet-0：精密装配的真正 Scaling 变量可能是 Force-Synchronized Data

**时间回补：v1 提交于 2026-09-01 17:58 UTC。** [论文](https://arxiv.org/abs/2609.01596) · [项目页](https://pine-lab-ntu.github.io/facet-0/)

### 为什么重要

通用 VLA 在抓取、搬运和粗放置上越来越强，但电脑 RAM、CPU、GPU、连接器插装这类任务的失败往往发生在最后几毫米：

- 插槽位置基本对了，但方向差一点；
- 已经接触，但法向力太大；
- 卡住以后应该退还是继续压；
- 视觉几乎不再能区分“插进 0.5 mm”还是“刚好顶住”。

这时继续堆普通 RGB-action trajectory 不一定能解决问题，因为真正缺的是 contact outcome。

### 数据与模型模块

Facet-0 围绕 **ManuFacet-1K** 构建训练资产，目标是 1,000 小时 force-synchronized precision assembly 数据，并统一不同机器人本体的 action schema。

项目页当前公开状态显示已经有数百小时可训练数据、25k 级 curated episodes；每帧都有 wrist F/T，同一时钟下记录约 160 Hz state 与 15 Hz vision，同时保留 failure + recovery 段。

模型端并不只预测 action：

```text
Vision / Language / Kinematics
        +
Causal Wrench History
        ↓
Action + Future Wrench Proposal
        ↓
Action-Wrench Critic
        ↓
Bounded Adaptation
        ↓
Contact-Safe Execution
```

### 多时间尺度控制

项目页给出的运行分层很值得工程团队参考：

- 语义 planning：约 **5–10 Hz**；
- force residual closed loop：约 **20 Hz**；
- precision control：约 **200 Hz**。

这比让一个 Transformer 用同一频率同时承担语义、接触判断和伺服更符合真实工业控制结构。

### 传感器与动力学假设

Facet-0 显式需要 wrist F/T、相机与机器人运动学。F/T 传感器的 bias、温漂、安装方向和结构柔顺都会影响 contact state；不同夹具与零件材料也会改变力学分布。

因此跨工位迁移不应该只检查视觉域变化，还必须重新验证 wrench normalization 与 safety envelope。

### 结果与边界

论文摘要报告 bounded adapted system 在 5 个亚毫米级电脑装配任务上平均成功率约 **82%**，最强对照约 15%，并报告约 0.5 mm placement accuracy 和 50 ms command latency。

项目页还展示了 RAM / CPU / GPU / disk 的完整真实 workstation 任务。

但这是新发布系统，数据集仍在持续扩展；大规模跨工厂、跨零件批次和长周期传感器漂移仍需更多验证。

### 适合谁关注

工业装配、连接器插拔、精密机械臂、F/T 传感器、VLA + force control、sim-to-real 接触操作。

### 工程落地启发

如果内部要做精密操作数据平台，建议从一开始就把：

```text
RGB-D
joint / EE
commanded action
measured wrench
contact phase
failure type
recovery action
calibration version
```

锁在同一时间基准里。

对接触任务来说，“失败并恢复”的数据往往比再收一遍完美成功轨迹更有信息量。

## 6. Knowing When to Stop：VLA Action Chunk 应该根据内部注意力状态动态截断

**时间回补：v1 提交于 2026-09-01 08:38 UTC。** [论文](https://arxiv.org/abs/2609.00908)

### 为什么重要

固定 action chunk 是 VLA 部署里一个非常实际的工程参数。

短 chunk：

- 反应快；
- 频繁重推理；
- 容易动作抖动。

长 chunk：

- 流畅；
- 推理摊销好；
- 一旦世界变化，会继续执行陈旧动作。

以往通常只能靠 grid search 找 8 / 16 / 32 步这种固定值。

### 算法模块

作者观察到 cross-attention 随 horizon 增长会出现一个很稳定的信号：当模型逐渐“不知道后面应该关注什么”时，attention distribution 变得分散，dispersion entropy 上升并进入持续高熵 plateau。

因此 runtime 可以直接使用已经算出来的 attention：

```text
Action Chunk Prediction
        ↓
Cross-Attention Entropy
        ↓
Sustained High-Entropy Plateau?
        ↓
Yes → truncate
No  → continue
```

不需要增加额外网络，也不需要重新训练 VLA。

### 传感器与控制接口

真实实验采用双臂 ARX R5 follower，ARX X5 leader 用于遥操作采集；腕部鱼眼相机 + 头部 RGB，图像约 20 Hz，低层控制约 60 Hz。

这说明 adaptive chunking 处在中间 policy runtime 层，而不是替代低层 servo。

### 结果与实时性

论文报告：

- LIBERO 平均约 **97.25%**，高于固定 chunk 最佳约 94.88%；
- LIBERO-Long 为 **94.5%**，提升约 4.5 个百分点；
- 真实三任务平均成功率：最佳固定 chunk **47.5%**，本文 **61.7%**；
- 单次推理延迟约从 **0.2661 s → 0.2725 s**。

也就是说，收益不是来自显著增加推理预算，而是更合理地决定“这一次预测到底执行多少”。

### 鲁棒性与风险

Attention entropy 仍然只是模型内部启发式，不是动作安全或任务完成概率。

一个模型即使非常自信，也可能自信地错。因此 adaptive chunk 应与：

```text
action age
collision / force monitor
new observation interrupt
high-priority preemption
```

组合使用。

### 适合谁关注

π0 / π0.5、flow-matching VLA、双臂操作、长时任务和已经遇到 chunk-length tradeoff 的团队。

### 工程落地启发

建议 VLA runtime 不再只有 `chunk_size=16`，而是暴露：

```text
predicted_horizon
executed_horizon
truncation_reason
attention_entropy
observation_age
```

这样以后才能做真正的 closed-loop action-freshness 回归。

## 7. HarnessDev：让 Agent 自己改 Harness 容易，让“改完真的更好”很难

**时间回补：v1 提交于 2026-09-01 15:45 UTC。** [论文](https://arxiv.org/abs/2609.01437) · [项目页](https://self-developing-agents.github.io/)

### 突破性工程价值

现在 Coding Agent 的效果越来越由 harness 决定：

- tool schema；
- workspace；
- memory；
- search；
- verifier；
- context management；
- retry / repair loop。

如果 Agent 能自己写和修改 harness，理论上就可以把一次项目经验固化成下一次可复用能力。

HarnessDev 专门评测这件事，而不是只看最后一个 Issue 修没修好。

### 两阶段设计

**Creation**：

从极小 seed 和少量案例出发，让模型创建一个完整、可以真实执行的 agent harness。

**Evolution**：

让它继续观察 downstream execution feedback，并修改自己的 harness，希望提高后续任务表现。

评估同时看：

```text
held-out task success
execution-token cost
cross-executor portability
```

Creation 覆盖 6 个 creator LLM、4 个领域、5 个 downstream benchmark，共 2,207 个 unique downstream instances。

### 最关键的负结果

“看见反馈以后改得更好”并不可靠：

- 64 次可比较版本切换中，visible feedback 与 held-out improvement 方向一致只有 **34 次（53.1%）**；
- 9 个 Agent 自己声明的 final version，只有 **2 个**是 held-out 上真正最好的版本；
- 固定 Gemini executor 的多条 evolution 运行里，只有一条 creator lineage 在 held-out 上最终改善，其余出现退化。

这几乎就是生产自进化系统最需要的警告：**局部 benchmark gain 不能直接 merge 到全局 harness。**

### 另一个很现实的问题：Dead Mechanisms

项目分析中，模型生成的 18 个 Code harness 都可以运行，但有些代码里声明的 state / memory 机制在正式 execution 中根本没有真正触发。

也就是说：

> “代码里有 Memory 类”不等于 Agent 运行时真的使用了 Memory。

### 权限、安全与可验证性风险

生产 harness 不应该允许 Agent 自己同时拥有：

```text
proposal
implementation
benchmark selection
acceptance
production rollout
```

否则就是自改规则、自出考题、自判通过。

至少要分成：

```text
Agent Proposal
      ↓
Sandbox Harness Version
      ↓
Frozen Held-Out Regression
      ↓
Independent Acceptance Gate
      ↓
Canary / Rollback
```

### 适合谁关注

企业 Coding Agent、自建 Codex/Claude Code 平台、长期项目记忆、Agentic RL、Skill / Harness 自动演化。

### 工程落地启发

最值得复制的是**Harness-as-Artifact**：

```text
harness_version
base_model
executor_version
tool_schema
memory_schema
visible_eval
heldout_eval
runtime_trace
rollback_target
```

Agent 可以生成下一版，但生产环境只部署通过冻结回归的版本。

## 8. Gemini 3.8 Flash：Flash 级模型继续向“长时 Coding Agent 主力 Worker”移动

**2026-09-02 官方正式发布。** [模型卡](https://deepmind.google/models/model-cards/gemini-3-8-flash/) · [模型页](https://deepmind.google/models/gemini/flash/)

### 突破性工程价值

Google 对 Gemini 3.8 Flash 的定位已经非常明确：

> 不是“便宜一点的聊天模型”，而是面向 software engineering、long-horizon knowledge work 和 agentic execution 的高吞吐工作模型。

它基于 Gemini 3.7 Flash，同时继续提供可调 `effort`，让应用按任务动态控制质量、成本和延迟。

### 上下文与多模态

官方 model card 给出的接口能力包括：

- 文本、图像、音频、视频输入；
- 最高 **1M token context**；
- 最高 **64K token text output**；
- 面向软件工程、Agent 工作流和多模态任务；
- 已进入 Gemini、Gemini Enterprise Agent Platform、Google AI Studio、Gemini API、AI Mode 和 Antigravity 等产品入口。

### 为什么适合 Coding Agent

对真实 Coding Agent 来说，Flash 系模型最重要的不是单次 benchmark 峰值，而是：

```text
每次工具循环成本
平均响应时间
长任务稳定性
上下文吞吐
并发 Worker 数
```

如果它能够用更低成本长期承担 Scout、Fixer 或普通 Worker，就可以把更昂贵模型留给深度 review、复杂故障和高风险决策。

### 安全、权限与可验证性风险

官方 model card 同样明确列出：

- 仍然可能 hallucinate；
- 某些请求可能更慢或超时；
- higher effort 会使用更多 token；
- safety evaluation 并非所有指标都相对上一版单调改善。

因此升级模型时不能只看 coding benchmark。

生产 Agent 至少应该保存：

```text
requested_model
actual_model
model_version
effort
prompt_version
tool_policy
latency
tokens
validator_result
```

### 是否适合真实研发流程

很适合作为高并发 Coding Worker、仓库 Scout、知识工作 Agent 和多模态工具 Agent 的候选默认模型，但不建议无 A/B 全量替换已有模型。

### 工程落地启发

更合理的模型路由可能是：

```text
Fast / Cheap Scout
        ↓
Gemini 3.8 Flash-class Worker
        ↓
Deep Reviewer / Hard Fixer
        ↓
Deterministic Validator
```

把最强模型当成每一步唯一模型，往往既贵，也让回归定位更困难。

## 经典论文回顾

### Bundle Adjustment — A Modern Synthesis：为什么 BA 的核心不是“调相机”，而是利用稀疏结构联合解释所有观测

Bill Triggs、Philip McLauchlan、Richard Hartley 与 Andrew Fitzgibbon 的 **Bundle Adjustment — A Modern Synthesis** 收录于 *Vision Algorithms: Theory and Practice*，Springer LNCS 1883，正式出版于 **2000 年**；Workshop 版本来自 1999 年。它几乎定义了现代计算机视觉社区理解 BA 的标准框架：不是把每个相机 pose 独立修一下，而是**联合优化相机参数与三维结构，使全部观测在同一几何模型下最一致**。（[DOI](https://doi.org/10.1007/3-540-44480-7_21)，[Ceres BA 教程](https://ceres-solver.readthedocs.io/latest/nnls_tutorial.html#bundle-adjustment)）

### 核心问题

经典视觉 BA 的形式可以写成：

```text
Camera Parameters + 3D Points
            ↓
        Projection
            ↓
Observed Image Measurements
            ↓
Robust Reprojection Residual
            ↓
Joint Nonlinear Optimization
```

如果相机 pose 有一点误差、三维点也有一点误差，只固定其中一边优化另一边，误差很容易互相污染。BA 直接把两边一起当变量。

### 关键数学思想

真正让 BA 能扩展到大问题的不是“用了 Gauss-Newton”这么简单，而是它特殊的 block sparsity。

一个视觉 observation 通常只连接：

```text
一个 Camera Block
        ↕
一个 3D Point Block
```

线性化后 Hessian 具有明显的 camera / point block structure。使用 **Schur Complement** 可以先消掉大量 point variables，把问题降成更小的 camera system，再回代恢复三维点更新。

这也是 Ceres 为什么专门提供 `DENSE_SCHUR / SPARSE_SCHUR / ITERATIVE_SCHUR` 等 BA solver。

### Gauge Freedom：优化器收敛不等于问题唯一

单目 reconstruction 中，全局平移、旋转和尺度可能并不由 reprojection error 决定。

这类 gauge freedom 如果没有 anchor / prior / proper parameterization，会使 Hessian 存在 null space。数值优化器即使返回“成功”，covariance 与解的物理意义也可能有问题。

这和今天 LiDAR registration 的 degeneracy 本质非常接近：

> **不是 solver 能不能算，而是观测到底约束了哪些自由度。**

### 传感器与假设

原论文重点面向多视图视觉与 photogrammetry，但 BA 的抽象远超 Camera：

```text
共享潜在状态
+
不同观测模型
+
稀疏因子连接
→ 联合优化
```

所以后来：

- Visual SLAM；
- Visual-Inertial BA；
- LiDAR BA；
- multi-sensor calibration；
- object-level mapping；

都在复用同一类思想。

### 当年为什么重要

它把几十年 photogrammetry 的成熟经验系统整理给了 computer vision，包括：

- robust cost；
- sparse Newton / Schur；
- gauge invariance；
- quality control；
- covariance / uncertainty；
- 参数化与数值稳定性。

BA 从此不再只是“最后跑一个非线性 least squares”，而是一套完整估计理论与软件结构。

### 今天仍然在使用的思想

**1. 联合优化优于逐阶段永久冻结。**

当多个状态强耦合时，先估 A、永远固定，再估 B 很容易把 A 的误差锁死。

**2. 稀疏结构比 solver 名字更重要。**

Factor graph / BA 性能很大程度取决于变量和 residual 怎么连接。

**3. Gauge / observability 必须显式处理。**

优化器给出一个数字，不等于这个数字被数据真正约束。

**4. Robust loss 只能压 outlier，不能创造 information。**

长走廊没有纵向几何约束时，换 Huber / Cauchy 不会凭空解决可观测性。

### 已被后续扩展的部分

现代 SLAM 已大量加入：

- IMU preintegration；
- incremental smoothing；
- sliding-window marginalization；
- continuous-time trajectory；
- learned correspondence / depth；
- LiDAR voxel / surfel statistics；
- GPU linear algebra。

但这些没有取代 BA，反而是在改变 residual、状态和稀疏结构。

### 公开代码与可复现性

原论文主要是理论与综述，不对应单一官方实现。今天最适合工程复现的是 **Ceres Solver**：其官方教程直接提供 bundle adjustment 例子，并解释了 Schur-based solver 如何利用 BA 稀疏结构。

### 对当前工程项目的重新解读

今天的 Adaptive Depth-Map BA 正好说明：BA 不一定非要优化经典 image keypoint。

对 16 线 / 多 LiDAR 系统，可以重新思考：

```text
Pose_i
  +
Local Map Statistics
  +
Extrinsic
  +
Time Offset
        ↓
统一 Residual Graph
        ↓
Observability / Gauge Analysis
        ↓
Joint Optimization
```

真正值得避免的是“先拼点云 → 再 ICP → 再把结果当绝对真值塞进后端”的层层硬冻结。

如果外参、时间和 map statistics 本来互相耦合，就应该至少在离线 calibration / map refinement 阶段允许它们共同被重新解释。

## 今日结论

今天最明显的 SLAM 信号是：**时间与地图表示都正在从预处理细节升级成估计器的一等状态。** CT-RIO 不再假设机器人之间拥有同一个时钟；Adaptive Depth-Map BA 不再假设多视图之间必须先得到可信离散 correspondence。两者都在减少“先做一个脆弱前处理，再把结果当真值”的系统风险。

控制侧也呈现高度一致的趋势：**学习器越来越少直接接管最终控制，更多是在优化器周围提供参数、先验或搜索建议。** SG-RL 让 RL 调 NMPC cost weight；ProxPI 让 learned policy 只成为 soft prior，而不是重置 MPPI optimizer state。对于需要真实安全边界的机器人，这比“RL vs MPC 二选一”更容易走向产品。

Facet-0 和 adaptive action chunking 则共同指向多时间尺度 VLA：语义、接触、轨迹和 servo 本来就不应该共享一个控制频率。对真实机器人，模型能力继续提高以后，**动作新鲜度、接触反馈、低层抢占和安全 envelope** 会比单一离线 benchmark 更能决定落地效果。

AI Coding 侧，HarnessDev 和 Gemini 3.8 Flash 放在同一天看很有意义：模型越来越适合长时 Agent，但 harness 自动演化本身仍然很不稳定。越是允许 Agent 工作数小时甚至数天，越需要：

```text
Harness Version
Held-Out Regression
Tool Permission
Runtime Trace
Rollback
```

模型更强不会让这些传统软件工程结构消失，反而会放大它们的重要性。

## 最值得深入研究或尝试复现的方向

1. **多机器人 / 多计算节点 Time-State Prototype。** 给每个传感器与机器人维护独立 `clock_id / offset / uncertainty / jitter / excitation`，人为注入 10–300 ms offset，比较“先硬同步”与连续时间联合估计的相对定位误差和恢复时间。

2. **ProxPI 风格 Learned-Prior MPC A/B。** 在已有 MPPI 上同时实现 policy-centered warm-start 与 nominal-centered + soft prior cost；人为加入新障碍、目标切换和动作语义变化，观察 prior OOD 时 optimizer correction 是否被反复重置。

3. **VLA Adaptive Chunk Runtime。** 不改模型权重，直接记录 cross-attention entropy、预测 horizon、实际执行 horizon、action age 与 preemption；比较固定 8/16/32 步和动态截断在真实任务中的成功率与 P95/P99 反应时间。

4. **Harness Evolution 必须走软件发布流程。** Agent 可以自动生成 harness vNext，但只允许进入 sandbox；冻结 model / executor / hidden regression 后再决定是否升级，任何可见 benchmark gain 都不能直接触发生产替换。

## 参考资料

1. [CT-RIO / Parallel Reference-Centric Continuous-Time Relative Localization](https://arxiv.org/abs/2602.22006)
2. [Adaptive Depth-Map-Guided Bundle Adjustment](https://arxiv.org/abs/2609.01089) · [代码](https://github.com/YiranZhou-Robotics/ADM-BA)
3. [Solver-Gradient Guided RL for Weights-varying MPC](https://arxiv.org/abs/2609.01061)
4. [ProxPI](https://arxiv.org/abs/2609.00941)
5. [Facet-0](https://arxiv.org/abs/2609.01596) · [项目页](https://pine-lab-ntu.github.io/facet-0/)
6. [Knowing When to Stop / Adaptive Action Chunking](https://arxiv.org/abs/2609.00908)
7. [HarnessDev](https://arxiv.org/abs/2609.01437) · [Self-Developing Agents](https://self-developing-agents.github.io/)
8. [Gemini 3.8 Flash Model Card](https://deepmind.google/models/model-cards/gemini-3-8-flash/) · [模型页](https://deepmind.google/models/gemini/flash/)
9. [Bundle Adjustment — A Modern Synthesis](https://doi.org/10.1007/3-540-44480-7_21) · [Ceres Solver BA 教程](https://ceres-solver.readthedocs.io/latest/nnls_tutorial.html#bundle-adjustment)
10. [arXiv Robotics](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/new)
