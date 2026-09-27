---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-27"
date: 2026-09-27 09:00:00 +0800
description: "本期关注 OREN-X 多模态八叉树地图、FMCW Doppler LIO、跨本体安全过滤、闭环 Sim2Real 适配、实时 Koopman 扩散控制、Training-free Behavior Cloning、RAPID 机器人编程，以及 Agent 写操作的 Exactly-Once 工程契约。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-27

## 摘要

今天是周日。arXiv Robotics 与 Software Engineering 最新常规公开批次仍为 **2026-09-25（周五）**，分别有 101 条和 52 条；周末没有新的常规 arXiv 批次。因此本期严格从最近 7 天继续筛选，并按规范化标题、arXiv ID、DOI、GitHub 仓库和项目页与覆盖索引去重。今天入选的 2026 年工作 v1 都提交于 9 月 24 日 UTC，距本次生成已超过 24 小时，统一标记为“时间回补”；FMCW-LIO 则是 **IEEE RA-L 2024 已发表工作在 2026-09-24 补登 arXiv**，因此明确标为“补充回顾”，不把旧论文包装成新研究。

今天 SLAM / 长期地图最值得看的工作是 **OREN-X**。它没有为 SDF、occupancy、radiance、vision-language feature 各维护一套地图，而是让一个 3D octree 成为多模态场的共同索引和存储骨架。Replica 上，SDF 单模态映射达到 80+ fps，四种模态同时维护仍达到 30+ fps；在线字典学习把视觉语言特征压到完整逐顶点存储的约 1/3.7，同时开放词汇 3D mIoU 和几何精度反而进一步提升。这个方向很贴近长期机器人真正需要的“地图既服务定位，也服务规划、渲染、语义查询”。

另一条和 LiDAR 退化直接相关的是 **FMCW-LIO**。传统 LIO 基本只能从点的位置推运动，而 FMCW LiDAR 自带瞬时 Doppler velocity。论文将 Doppler 写进 on-manifold 状态估计，同时用 Doppler criterion 清除动态点，因此在结构退化环境中获得比纯几何 LIO 更稳定的观测。它真正值得关注的不是又一个 LIO 名字，而是新传感器正在把“速度测量”直接带进点云前端。

控制侧今天有三个很清晰的工程方向。**CrossSafe** 尝试让 Hamilton-Jacobi safety filter 跨不同机器人本体复用：安全概念共享，但 morphology / kinematics 决定同一抽象动作在具体机器人上是否安全。**OSRAM** 不改已有策略，而把“机器人 + 已部署 policy”视为一个闭环系统，在线学习 command→response，再反向修正未来参考命令；这特别适合已经稳定但存在残余 Sim2Real 偏差的商业控制栈。**BK-MBD** 则把 model-based diffusion 的昂贵 rollout 换成 bilinear Koopman lifted dynamics，在仿真中把单次 planning update 控制在 14.7 ms 以内，并在真机机械臂上同时满足移动目标跟踪和控制 deadline。

机器人学习侧，**Behavior Predictive Control（BPC）** 很值得和大 VLA 对照看：它不做端到端训练，而根据最近 observation-action history 从 demonstration bank 检索并混合未来动作，再用闭式 residual correction 修正。论文报告 consumer GPU 上从“小时级训练”缩到“秒级 fitting”，Jetson Orin Nano 闭环超过 75 Hz，而且每次动作仍可以追溯到支撑它的 demonstration window。**RAPID** 则把 Coding Agent 的 generate→execute→verify→repair 循环搬进机器人程序生成：只给一段人类视觉示范，就自动推导 task spec、action primitives 和可交互验证环境，再生成 object-centric relational program，最终在真实 Franka 上跑完八类非抓取操作。

AI Coding 主动态 **Where Does Exactly-Once Live?** 则直接触及 Agent 真正上线后的事故类型：一次写操作 timeout 并不代表它没执行，盲目 retry 会产生重复副作用。25,930 个 episode 的结论很明确：当结果能立即 read-back 时，强模型可以做得很好；但在 in-flight / transport redelivery 这类模型根本无法观察真实提交状态的故障里，同样的强模型仍大量重复写。把 idempotency key 变成 tool contract 的一部分，duplicate rate 从 28% 降到 4%。这说明 Exactly-Once 首先是接口与系统设计问题，不是 Prompt 技巧。

近期通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic、Google DeepMind 与 xAI 的官方公开入口，没有发现 9 月 26–27 日需要新增报道的通用旗舰正式发布；Claude Opus 5.5、GPT-6 系列与 Grok 4.7 已在前几期覆盖，因此本期不重复填充。

最新公开列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

## 1. OREN-X：把几何、颜色与开放词汇语义放进同一棵 Octree

**时间回补：v1 提交于 2026-09-24 07:33 UTC。**

### 为什么重要

机器人长期运行后，地图往往会碎成几套互不一致的表示：几何用 occupancy / SDF，颜色用 radiance map，VLM / segmentation 又单独维护 semantic feature map。它们各自做 voxelization、索引、压缩和查询，不只重复消耗内存，也让“同一空间位置的几何、颜色、语义是否一致”变得难以利用。

OREN-X 的核心不是单纯压缩地图，而是把 **octree 作为多模态 field 的共同空间骨架**。

### 算法模块

```text
Online observations
      ↓
Shared 3D Octree
      ├─ occupancy
      ├─ SDF
      ├─ radiance
      └─ vision-language feature
      ↓
explicit / implicit queries
      ↓
GPU ray-octree traversal
+ online dictionary compression
```

不同模态还不是完全独立更新。论文利用 cross-modality synergy：occupancy 与 radiance 会帮助 sharpen SDF；视觉语言 feature 则使用在线 dictionary learning 压缩，而不是给每个 vertex 永久保存完整高维向量。

### 实时性与结果

Replica 上，论文报告 SDF 映射 **80+ fps**，四种模态一起维护 **30+ fps**；vision-language feature 相对完整逐顶点存储压缩 **3.7×**；near-surface SDF accuracy 相对单模态 baseline 提升 **33%**；相对最佳先前方法，mean open-vocabulary 3D mIoU 提升 **71%**、mean accuracy 提升 **61%**。

### 传感器 / 系统假设

OREN-X 主要解决 online map representation，而不是重新发明一套前端 tracking。工程上仍需要可靠的位姿来源，把多模态观测投进一致坐标系。如果 pose graph 后续发生大闭环，多模态证据如何随 map revision 更新，仍然需要和 submap-anchored evidence 一起设计。

### 鲁棒性与工程风险

多模态共享也会带来“错误互相强化”的风险。例如错误 pose 可能同时污染 SDF、颜色和语义。长期地图建议每类 field 都保留独立的 `observation_count / last_seen / source_pose_revision / confidence / update_source`。共享空间索引，不等于共享同一个置信度。

### 可复现性

当前最值得复现的是 representation / query throughput。可以用现有点云地图抽一小段区域，同时维护 occupancy、TSDF/SDF、RGB 与 CLIP/VLM feature，对比“四棵独立 voxel map”与“共享 octree + per-node fields”的内存、query latency 和更新成本。

### 适合谁关注

长期 LiDAR / RGB-D 地图、语义导航、开放词汇 3D 地图、数字孪生、希望控制地图内存增长的机器人团队。

### 工程落地启发

地图接口可以从多个互不关联的 `query_geometry / query_semantic / query_color`，升级为先获得统一 spatial handle，再访问 `geometry / radiance / semantic_feature / confidence`。这样 planner、relocalizer 与 VLM 访问同一份空间 identity。

[论文](https://arxiv.org/abs/2609.29157)

## 2. FMCW-LIO：当 LiDAR 自己能测速度，LIO 的退化结构就变了

**补充回顾：论文已发表于 IEEE RA-L 2024；2026-09-24 才补登 arXiv。**

### 为什么重要

传统机械式 / ToF LiDAR 的单点观测主要是 range + direction，因此 LIO 要从连续扫描几何变化间接估计速度。长走廊、大平面、重复结构一旦让几何 Hessian 退化，某些运动方向就几乎没有约束。

FMCW Doppler LiDAR 多了一个非常关键的原生量：**instantaneous radial Doppler velocity**。这等于给每个合适的回波增加一个与机器人运动直接相关的速度观测。

### 算法模块

```text
FMCW LiDAR range + Doppler
        +
IMU
        ↓
motion compensation
        ↓
Doppler-aided observation model
        ↓
on-manifold state estimation
        ↓
Doppler dynamic-point rejection
        ↓
static geometric map
```

Doppler 不只用于估速度，还可以帮助判断某个点是否真的属于静态世界。

### 传感器与动力学假设

它依赖真正能够输出 point-wise Doppler velocity 的 FMCW LiDAR，不是普通 MID360 / Velodyne 软件升级就能得到。因此它对现有 ToF LiDAR 项目的意义更多是“重新理解可观测性”：未来若更换 Doppler LiDAR，状态估计不应该只把它当更抗干扰的 range sensor，而要把速度通道写进 estimator。

### 鲁棒性

论文报告在多种场景下相对其他算法提升 accuracy / robustness，并特别强调 structure-degenerated environments。Doppler 观测与几何观测的退化方向并不完全相同，因此可以提供真正互补的信息。

### 工程风险

Doppler 本身也不是完美速度真值。运动补偿、时间同步、目标自身运动和 return quality 都会影响观测。产品化应至少记录 `doppler_residual / doppler_inlier_ratio / geometric_localizability / dynamic_point_ratio / imu_consistency`。

### 可复现性

官方 GitHub 仓库目前已经存在，但 README 仍标注 **Coming soon**，还没有可直接复现实验的完整实现。因此现阶段只能评价为“官方代码入口已建，代码尚未真正发布”。

### 适合谁关注

LIO、退化走廊 / 隧道、动态环境定位、FMCW LiDAR、新型 4D LiDAR 传感器选型。

### 工程落地启发

现有 LIO-SAM / FAST-LIO2 可以先在点测量接口中预留 `radial_velocity / radial_velocity_variance`，将来换 Doppler LiDAR 时不用重写整个数据流，只扩 estimator residual。

[论文](https://arxiv.org/abs/2609.29374) · [DOI](https://doi.org/10.1109/LRA.2024.3396636) · [官方仓库](https://github.com/IMRL/FMCW-LIO)

## 3. CrossSafe：同一个“避障”概念可以共享；同一个动作是否安全，必须看机器人本体

**时间回补：v1 提交于 2026-09-24 03:55 UTC。**

### 为什么重要

跨本体 VLA 往往希望多个机器人共享同一个 end-effector action space，但安全过滤很难跟着共享。同样一个末端位移，对一台手臂较短的机器人可能安全，对另一台肩更宽、肘部包络更大的机器人却可能造成 whole-body collision。

CrossSafe 的核心假设是：**“什么叫危险”可以跨本体共享，但“怎样实现安全动作”必须显式条件化 morphology / kinematics。**

### 算法模块

```text
robot morphology + environment
        ↓
morphology-aware latent state
        ↓
Hamilton-Jacobi reachability
in latent space
        ↓
shared safety value function
+ safety-maximizing policy
        ↓
embodiment-conditioned safe action
```

### 实验与鲁棒性

论文覆盖 **5 种双臂机器人本体 × 5 个 manipulation task**，安全约束是 whole-body collision avoidance。联合在 4 个 embodiment 上训练后，对第 5 个 held-out embodiment 做 zero-shot，能降低 nominal policy 的碰撞率；增加训练 embodiment 数量还会改善泛化。

### 风险

latent-space HJ 仍然依赖 representation 是否保留真正与碰撞可达性相关的信息。若编码器把关键几何差异压掉，形式上计算出的 safety value 可能失真。部署时应同时记录 embodiment id、morphology embedding version、safety value、filter intervention 与真实 collision margin。

### 可复现性

当前摘要未给出成熟开源实现入口，现阶段更适合先复现“共享安全表征 + morphology conditioning”这个实验问题，而不是直接替换现有硬 safety layer。

### 适合谁关注

多款机械臂共用 VLA、跨本体机器人基础模型、whole-body collision avoidance、安全 RL / HJ reachability。

### 工程落地启发

如果公司里不同机械臂 / 机器人共享上层 action schema，安全层 API 不应只是 `filter(action)`，而应显式接收 `embodiment_model + current_state + scene + action`。安全永远是“动作 × 当前状态 × 本体”的关系。

[论文](https://arxiv.org/abs/2609.28984)

## 4. OSRAM：Sim2Real 偏了，不一定要重训 Policy；先把参考命令“预失真”

**时间回补：v1 提交于 2026-09-24 00:54 UTC。**

### 为什么重要

很多真实机器人控制器上线后并不是完全失效，而是存在持续的小偏差：命令速度长期偏低、转弯有 phase lag、载荷变化后轨迹出现固定残差。这种 residual dynamics mismatch 如果重新做 system identification 或重训整个 policy，成本很高。

OSRAM 选择不碰已有 controller，而是在它之前加一个自适应 reference layer。

### 算法模块

```text
simulation randomized dynamics
        ↓
meta-train closed-loop model
(robot + deployed policy)
        ↓
real deployment
        ↓
limited tracking observations
        ↓
rapid model finetuning
        ↓
optimize future references
        ↓
existing policy unchanged
```

它学习的不是裸 robot dynamics，而是 robot + controller 对 reference 的 closed-loop command-response。

### 真机与鲁棒性

论文在 biped velocity tracking 与 loco-manipulation 上做 simulation + hardware evaluation。结果显示 closed-loop model 在 unseen dynamics 下提高 prediction / tracking accuracy，在线 reference adaptation 可以继续压低残余 Sim2Real tracking error。

### 为什么适合已有机器人产品

很多商业机器人底层控制器根本不能改，只给 `vx / vy / wz / pose target`。OSRAM 的思路特别适合这种接口：不去重训第三方 gait controller，只在 command side 学一个“应该给它什么参考，它最后才会得到你真正想要的运动”。

### 风险

reference pre-compensation 有可能把命令推向 actuator / stability boundary。因此 adaptive layer 之外必须保留 reference clamp、rate limit、safety envelope、model uncertainty 与 fallback-to-nominal-command。

### 可复现性

作者提供项目入口。最小复现可以先对现有机器人做 step / chirp command，学习 `desired vx → achieved vx` 的短时闭环模型，再让 optimizer 只修正 reference，不改底层控制器。

### 适合谁关注

第三方机器狗 SDK、人形 locomotion、Sim2Real、已有稳定 RL / MPC controller 但真机有系统偏差的团队。

### 工程落地启发

如果控制接口只有 `vx / vy / vw`，可以尝试 `navigation command → OSRAM-style reference adapter → vendor stair / locomotion controller`。这样可以改善速度、转向和坡地 tracking，又不需要接管底层腿控。

[论文](https://arxiv.org/abs/2609.28878) · [项目页](http://generalroboticslab.com/OSRAM)

## 5. BK-MBD：让 Diffusion Trajectory Optimization 真正赶上控制周期

**时间回补：v1 提交于 2026-09-24 02:03 UTC。**

### 为什么重要

Model-Based Diffusion（MBD）很适合非凸 trajectory optimization，但每轮 diffusion 都需要大量 dynamics rollout。真实控制里，planner 再聪明，如果 50 ms deadline 里算不完，也没有意义。

BK-MBD 用 Koopman lifted dynamics 把 rollout 最昂贵的部分变成批量 matrix-vector computation。

### 算法模块

```text
current robot state
        ↓
lift once to Koopman space
        ↓
many candidate trajectories
        ↓
bilinear lifted dynamics
(matrix-vector propagation)
        ↓
diffusion / noise annealing
        ↓
best control sequence
        ↓
execute first action
```

和普通 linear Koopman 不同，它使用 **bilinear input gain**，使控制输入的作用随 configuration 改变。

### 实时性

仿真中每次 planning update **不超过 14.7 ms**，控制周期为 50 ms，且每个 trial 都到达目标。论文还有一个很有价值的消融：在 learned rollout 下，annealed noise schedule 比固定 noise 更准确；换成 exact rollout 后，两种 schedule 都能成功，说明 annealing 的一部分作用是在对抗 surrogate-model error。

### 真机

物理机械臂追踪一个起初未知的移动目标时，BK-MBD 是论文比较方法中唯一同时满足 tracking task 和 control deadline 的方法。

### 风险

Koopman lift 把速度问题解决后，主要风险变成 model bias。如果 lifted dynamics 在接触、饱和、强非线性区域失真，GPU 只会更快地 rollout 错误未来。因此建议实时监控 one-step / multi-step model residual、optimizer cost、deadline miss 与 fallback rate。

### 可复现性

项目页已经公开。对已有 MPPI / sampling MPC 项目，最公平的 A/B 是保持 cost / horizon / control limits 相同，只替换 rollout model，比较 exact dynamics、MLP dynamics、linear Koopman 与 bilinear Koopman 的 P50/P95 planning latency 和闭环误差。

### 适合谁关注

机械臂 MPC、sampling control、Koopman dynamics、diffusion policy / diffusion planning、边缘 GPU 实时优化。

### 工程落地启发

学习模型最适合先加速 rollout engine，而不是立即替换 cost + constraints + planner + controller。这样即便模型错了，仍然能从 optimization telemetry 追查问题。

[论文](https://arxiv.org/abs/2609.28920) · [项目页](https://rcilab.khu.ac.kr/bkmbd/)

## 6. Training-free Behavior Cloning：示范数据不一定非要先压成一套大网络

**时间回补：v1 提交于 2026-09-24 17:05 UTC。**

### 为什么重要

经典 Behavior Cloning 会把 demonstrations 压进 network weights。好处是推理快，但也让动作难追溯、新增示范往往要重训、坏行为也难精确删除。

Behavior Predictive Control（BPC）把 demonstration bank 保留在部署系统里，直接从历史数据合成控制。

### 算法模块

```text
recent runtime
observation-action history
        ↓
action-aware retrieval
        ↓
matching demonstration windows
        ↓
Hankel action-continuation prior
        ↓
blend future actions
        ↓
closed-form one-step residual correction
        ↓
control
```

它不是最近邻照抄一段轨迹，而是寻找能够重构当前 runtime history 的多个 observation-action window，再根据系数预测未来。

### 结果与实时性

论文在 simulation + real robot 上报告：表现可与学习式 policy（包括 π0.5）竞争，部分设置中超过它；policy fitting 从小时级降到 consumer GPU 上的秒级；Jetson Orin Nano 上闭环控制 **超过 75 Hz**。此外，retrieved windows 与 blending coefficients 天然给出“当前像示范里的哪个阶段”。

### 鲁棒性与风险

最大的限制是 demonstration bank 必须覆盖当前行为附近。如果机器人进入完全没有相似历史的 OOD 状态，retrieval 仍可能强行找到“最不坏”的示范，但那不等于安全。产品接口最好输出 retrieval distance、support window ids、coefficient entropy、residual magnitude 与 OOD state。

### 可复现性

这是今天很适合动手的方向，因为不需要重新训练大模型。现有遥操作数据只要保留 observation-action sequence，就可以先实现一个最简单 action-aware retrieval + linear correction baseline。

### 适合谁关注

小样本机器人学习、Jetson 边缘控制、需要快速增删示范的工业机器人、希望策略动作可追溯的团队。

### 工程落地启发

示范库可以直接版本化为 `success / edge_cases / recovery / deprecated`。行为改变时不是重新训练黑盒，而是明确增加 / 删除 demonstration，再做固定 regression。

[论文](https://arxiv.org/abs/2609.30134)

## 7. RAPID：给 Coding Agent 一段人类示范，让它自己生成、运行和修机器人程序

**时间回补：v1 提交于 2026-09-24 17:58 UTC。**

### 为什么重要

“让 LLM 写机器人代码”最大的问题并不是生成第一版代码，而是怎么自动回答：任务到底完成了吗、动作原语是什么、代码在哪运行验证、失败后怎么改。

RAPID 把 Coding Agent 最成熟的 generate→execute→test→repair 循环真正搬进机器人任务。

### 算法模块

只输入一段视觉人类示范，系统自动推导三样东西：testable task specification、robot action primitives、interactive execution / verification environment。之后进入：

```text
generate program
      ↓
execute
      ↓
verify against task spec
      ↓
repair program
      ↺
```

为了让程序不只是复刻示范里的绝对轨迹，RAPID 使用 **object-centric relational program**。Action primitive 由 trajectory optimization 实现对象级 motion effect；不同 primitive 再通过 relational constraints 组合，让程序在运行时适配新的物体位置和场景几何。

### 结果

系统在 simulation 中评估 8 个 contact-rich nonprehensile manipulation task，并测试 LIBERO-Pro 的常规抓取操作。真机使用 Franka arm，八个非抓取任务全部进行了实际部署评估，并展示对 object pose、shape、material 和 environment 变化的泛化。

### 为什么比“VLM 直接输出动作”值得关注

它保留了一个非常重要的软件工程层：Program 可以读、可以执行、可以检查、可以修。当机器人任务需要长期维护、客户现场变化、工程师还要介入调试时，这比所有行为永久封装在一个 policy weight 里更容易管理。

### 风险

自动生成的 verification environment 可能和真实世界存在 specification gap。如果 Agent 自己同时定义“什么叫成功”和“我是否成功”，就容易产生自证循环。生产系统应把关键安全 / 完成条件留在独立 geometric / sensor verifier。

### 可复现性

官方项目页已经公开。即使不复现自动 action-primitive discovery，也可以先从已有 skill library 开始，让 Coding Agent 只负责编排、执行、读错误码和修 program。

### 适合谁关注

机器人 Agent、机械臂编程、VLA + skill library、非抓取操作、希望让自然语言 / 示范最终落成可审计程序的团队。

### 工程落地启发

每个机器人 skill 最好统一成 `preconditions / parameters / effects / failure_codes / verification / rollback`，这样 Agent 写的不是“随便调用 SDK 的脚本”，而是组合有 contract 的机器人 primitive。

[论文](https://arxiv.org/abs/2609.30249) · [项目页](https://yuyaoliu.me/projects/rapid)

## 8. Exactly-Once：Agent 写操作的可靠性，首先是 Tool Contract，不是 Prompt

**时间回补：v1 提交于 2026-09-24 06:24 UTC。**

### 突破性工程价值

Agent 调只读工具失败，通常最多是少拿到信息；写操作 timeout 则完全不同：请求可能根本没到，也可能已经提交但 response 丢了，还可能仍在 flight。Agent 看不到真实状态时，retry 可能产生重复副作用，不 retry 又可能漏掉必须完成的动作。

### LIMBO 如何测

论文构造 deterministic LIMBO sandbox：6 类 service、optional idempotency key、eventually-consistent / missing read path、12 类 fault mode（包括 late commit、redelivery、partial batch），每个 episode 都用 committed-effect ledger 评分。总计 **25,930 个 episode**，覆盖 9 个近期模型、3 个 production agent harness、2 种 contract 与 15 种 recovery condition。

### 最值得记住的结果

如果写请求只是 ack 丢失，但 Agent 可以立即 read-back，强模型在明确 Exactly-Once 指令下重复率只有 **0.5%**。但如果请求仍在 flight，或者 transport 自己 redeliver，duplicate 分别达到 **56%** 和 **74%**。

更关键的是，无 universal idempotency key 时 duplicate 约 **28%**；每个 write 都提供 idempotency key 后下降到 **4%**。而且 **90% 已经产生重复副作用的 episode，Agent 最终仍然报告成功。**

### 工程结论

所有高风险 Agent write tool 都应该原生支持 `idempotency_key / operation_id / effect_ledger / status(operation_id)`，而不是让 Agent 自己拿自然语言记住“我刚才可能做过一次”。

### 权限 / 安全 / 可验证性风险

论文还证明：如果 late commit 没有已知最大 in-flight 时间，仅靠“等待一会再 read-back”的 verification policy 无法保证 Exactly-Once。因此这不是“让模型更谨慎”能完全解决的问题。

### 适合谁关注

自动部署、消息发送、创建工单、数据库 mutation、GitHub merge、机器人不可逆动作、自研 MCP / Agent tool。

### 工程落地启发

给内部工具分三类：READ 可安全重试；IDEMPOTENT WRITE 带 operation key 后可安全重试；NON-IDEMPOTENT WRITE 不裸暴露给 Agent，先包装成带 idempotency contract 的服务。这比 Prompt 里写“不要重复操作”可靠得多。

[论文](https://arxiv.org/abs/2609.29095)

## AI Coding 实战技巧精选

### 技巧 1｜升级模型后先跑 `/doctor prompt-audit`，清理旧时代留下的 Agent 指令

- **来源**：[Anthropic Claude Code v2.1.283 官方 Release，2026-09-25](https://github.com/anthropics/claude-code/releases/tag/v2.1.283)。
- **一句话结论**：模型升级后，不要默认旧 `CLAUDE.md`、Skill、Agent 和 command 仍然合理。Claude Code 现在有专门的 prompt audit，会优先指出 stale path、stale command 和互相矛盾的 instruction。
- **具体怎么做**：
  1. 在仓库根目录运行 `/doctor prompt-audit`，也可以使用 `/checkup prompt-audit`。
  2. 先处理报告顶部的 stale path / stale command / conflicting instruction files，不要一上来继续“优化 Prompt 文风”。
  3. 每次升级主模型、目录大重构、Skill 大改以后都重新跑一次，把结果当成 Agent 配置的 lint。
  4. 修完后用固定 regression task 再确认成功率，不要只因为 audit 清零就认为行为一定更好。
- **适合什么场景**：长期维护 `CLAUDE.md` / `AGENTS.md`、大量 Skills / custom commands、模型频繁升级的大仓库。
- **注意**：prompt-audit 只能发现配置层问题，不能替代 build / tests。稳定的业务 invariant 应继续保留。

### 技巧 2｜企业环境把模型白名单改成 Exact，再用 `deniedModels` 做显式封锁

- **来源**：[Anthropic Claude Code v2.1.283 官方 Release，2026-09-25](https://github.com/anthropics/claude-code/releases/tag/v2.1.283)。
- **一句话结论**：如果生产 Agent 需要模型版本可审计，不要让 `availableModels` 在新版本发布时自动放宽。使用 `availableModelsMatch: "exact"`，新模型必须明确加入才允许使用；个别模型再用 `deniedModels` 强制封锁。
- **具体怎么做**：
  1. 企业 managed settings 中把 `availableModelsMatch` 设为 `exact`。
  2. `availableModels` 只列经过内部 regression 的具体 model id。
  3. 对即使被宽规则命中也绝不允许使用的版本放进 `deniedModels`。
  4. 把最终实际 model id 写进每次 Agent run receipt，避免配置与实际 fallback 不一致。
- **适合什么场景**：Claude Code 企业部署、受监管研发、自动 PR / 部署 Agent、需要可复现模型版本的 CI。
- **注意**：具体 model id 应以当前组织实际可用列表为准。白名单解决的是“谁能运行”，并不自动解决 Prompt / Tool 权限风险。

### 技巧 3｜让 Agent 自动写 Fuzz Harness，但一定放进 disposable Codespace / VM

- **来源**：[GitHub Security Lab：AI-powered fuzzing with the Taskflow Agent，2026-09-24](https://github.blog/security/application-security/ai-powered-fuzzing-with-the-github-security-lab-taskflow-agent/)；[官方代码](https://github.com/GitHubSecurityLab/seclab-taskflows-fuzzing)。
- **一句话结论**：C/C++ 项目可以让 Agent 自动找入口、写 AFL++ harness、读 coverage 再迭代补 harness；但这个官方实现会执行 Agent 选择的 clang / AFL / build 命令，必须在 disposable 环境里跑。
- **具体怎么做**：
  1. 最安全的起点是直接打开官方仓库 Codespace，不要先在开发主机执行。
  2. 运行 `./scripts/fuzzing/run_fuzzing.sh owner/repo`；小项目可先用 `./scripts/fuzzing/run_fuzzing.sh DaveGamble/cJSON` smoke test。
  3. Pipeline 会为每个 harness 同时构建 AFL binary 与 coverage binary；AFL queue 再由 coverage binary replay，Agent 根据真实 uncovered branches 决定加 seed、改 harness、扩 dictionary 或跳过低价值分支。
  4. 官方默认 fuzz budget 按 30s → 60s → 120s → 240s → 480s → 960s 增长；连续两轮绝对 line coverage 增益都低于约 1% 时停止，避免 Agent 无限烧算力。
- **适合什么场景**：C/C++、解析器、网络协议、文件格式库、希望让 Coding Agent 真正连接 sanitizer / coverage / fuzzing evidence 的项目。
- **注意**：官方明确警告当前 Taskflow 会在 host 上直接执行 `afl-fuzz`、`clang` 和 LLM 选择的任意 build command，**没有额外容器隔离**。只应在无高权限、无生产凭据的 Codespace 或 throwaway VM 中使用。

## 经典论文回顾

### STOMP：不需要代价函数梯度，也能靠随机轨迹把机器人从局部最小里“抖出来”

Mrinal Kalakrishnan、Sachin Chitta、Evangelos Theodorou、Peter Pastor 与 Stefan Schaal 的 **STOMP: Stochastic Trajectory Optimization for Motion Planning** 发表于 **ICRA 2011**。它是 sampling-based trajectory optimization 的经典路线，也非常适合和今天 BK-MBD / diffusion trajectory optimization 一起重读。

### 核心问题

CHOMP 一类 gradient-based trajectory optimizer 非常高效，但前提是 cost 对轨迹有可用梯度。现实机器人经常想同时优化 collision、smoothness、motor torque、joint constraint 和 task-specific black-box score，其中不少 cost 难以写出稳定解析梯度，而且 gradient optimizer 容易陷进局部最小。

STOMP 的答案是：**不求 cost gradient，直接在整条轨迹附近随机采样。**

### 算法思想

```text
nominal trajectory
        ↓
sample correlated noisy trajectories
        ↓
evaluate trajectory costs
        ↓
convert costs into weights
        ↓
weighted trajectory update
        ↓
smooth / respect endpoint structure
        ↺
```

噪声不是独立 waypoint 白噪声，而会经过平滑结构，使 sample 更像真实可执行轨迹。因此它探索的是“轨迹形状”，不是随机把每个关节位置打散。

### 传感器 / 动力学假设

STOMP 本身主要是 motion planner / trajectory optimizer，不规定感知系统。它要求能够给轨迹计算 cost、对 collision / constraint 做评价、给定初始 trajectory，并在固定时间离散上更新控制点。原论文在 simulation 与双臂移动操作系统上验证 unconstrained / constrained task。

### 当年为什么重要

最大的意义是把“没有梯度的 cost”纳入实用 trajectory optimization。论文实验显示，STOMP 的 stochastic exploration 能逃出 CHOMP 可能卡住的局部最小。这对接触代价、离散惩罚、复杂 collision checker 很有吸引力。

### 今天仍在使用的思想

现代 sampling MPC、MPPI、diffusion planning 虽然数学形式不同，但很多工程直觉和 STOMP 一脉相承：不要只沿一个局部梯度走；candidate 的采样分布会决定有限预算下能探索什么；cost 可以是 black-box，只要能评估，不一定必须可微。今天 BK-MBD 的目标，本质上也是解决这类“候选很多、rollout 很贵”的现代版本问题。

### 已被后续替代 / 扩展的部分

原始 STOMP 的固定 horizon、Gaussian trajectory perturbation 和经典 CPU 实现已经不是今天的性能上限。后续系统加入 GPU parallel rollout、learned / colored proposal、chance constraint、model-predictive receding horizon、differentiable collision field 与 diffusion / path-integral weighting。

### 公开代码与可复现性

原始实验 ROS package 仍可访问，ROS-Industrial 也有后续 STOMP 实现。最适合做的复现实验不是追老 benchmark，而是固定同一个机械臂 scene，对 CHOMP / STOMP / 现代 sampling optimizer 使用同一 collision field，记录 success rate、P50/P95 planning time、initialization sensitivity、collision-check count、final smoothness 与 local-minimum failures。

### 对当前工程项目的重新解读

STOMP 对今天最有价值的提醒是：**Sampler 不是优化器里的随机数发生器，而是计算预算分配策略。**

如果现代 GPU 可以一次并行上千条 trajectory，那么需要重新审视的是：哪些时间相关结构值得采、哪些控制频谱是真实 actuator 能执行的、哪些候选应该在 cheap model 上先筛。这和前两天 Spike-MPPI、今天 BK-MBD 的问题完全相连。

[MPI-IS 论文页](https://is.mpg.de/publications/kalakrishnan_raiic_2011) · [DOI](https://doi.org/10.1109/ICRA.2011.5980280) · [原始复现仓库](https://github.com/kalakris/stomp_motion_planner_icra2011) · [ROS-Industrial STOMP](https://github.com/ros-industrial/stomp)

## 今日结论

今天最清晰的主线是：**机器人正在把过去隐含在“模型能力”里的东西重新拆回显式系统接口。**

OREN-X 让几何、颜色与语义共享空间 identity，但仍保留各自 field；FMCW-LIO 把 Doppler velocity 从“新传感器附赠信息”提升成 estimator 的正式 residual；CrossSafe 明确把安全拆成“可共享的安全概念”和“本体相关的动作可行性”。

控制侧更明显。OSRAM 不改已有 controller，而是把 closed-loop command-response 单独建模；BK-MBD 只替换最昂贵的 rollout dynamics，却保留优化器结构；BPC 甚至不把 demonstration 全部压进权重，而让支撑当前动作的历史窗口继续可追踪。

RAPID 又进一步把机器人任务变回一种可验证的软件系统：spec → program → execute → evidence → repair。这和 AI Coding 的 Exactly-Once 结论实际上是一回事：真正成熟的 Agent 不能只“看起来知道该怎么做”，必须依赖模型之外的 contract、execution state 和 verifier。

今天 Exactly-Once 的数据尤其值得记住。模型可以解决“我能观察到结果以后该不该重试”，但解决不了“真实世界发生了什么，而系统又不给我观察渠道”。这种情况下继续改 Prompt 没有意义，应该改 Tool API。

AI Coding 实战部分也指向同一方向：prompt-audit 负责清理 Agent 配置债务；exact model allowlist 让运行版本可审计；Security Lab fuzzing taskflow 则把 Agent 生成 harness 的能力放到真正的 AFL、coverage、sanitizer feedback loop 里，同时用 disposable environment 限制 blast radius。

如果把今天压成一句话：

> **更可靠的机器人和 Coding Agent，不是让一个模型承担更多隐式责任，而是把地图、速度、安全、本体差异、闭环误差、示范证据和写操作语义都变成明确、可观测、可验证的系统状态。**

## 最值得深入研究或尝试复现的方向

1. **OREN-X 式共享空间索引实验。** 在现有 LiDAR map 上增加 RGB / semantic feature field，比较独立 voxel map 与共享 octree 的内存、query latency 和 pose-revision 成本。
2. **LIO 退化诊断 + Doppler 接口预留。** 现有 MID360 / 16 线系统先把 geometric localizability 做成 telemetry；数据接口预留 radial velocity channel，为未来 FMCW / 4D LiDAR 做准备。
3. **OSRAM 式 Command Adapter。** 不改第三方狗的 stair / locomotion controller，只学习 `desired vx/vy/vw → achieved motion`，在外层优化 reference correction。
4. **Koopman Rollout Engine A/B。** 固定 sampling planner 和 cost，仅替换 rollout dynamics，比较 exact / MLP / linear Koopman / bilinear Koopman 的 planning deadline 和 model residual。
5. **Training-free Demonstration Policy。** 从已有遥操作 / 示教数据构建一个 BPC-like retrieval baseline，先验证 20–75 Hz 是否能稳定闭环，再与小 BC network 比较 OOD、更新成本和可解释性。
6. **Exactly-Once Tool Contract。** 对所有 Agent 写工具加 `operation_id + idempotency_key + status()`，故意注入 timeout / late response / duplicate delivery，验证同一动作无论重试多少次都只产生一次副作用。
7. **机器人 Skill Contract。** 参考 RAPID，把现有 `vx/vy/vw`、机械臂 primitive、stair mode 等接口统一补上 precondition、effect、failure code、verifier 与 rollback，再让 Agent 负责编排。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [OREN-X](https://arxiv.org/abs/2609.29157)
- [FMCW-LIO](https://arxiv.org/abs/2609.29374) · [DOI](https://doi.org/10.1109/LRA.2024.3396636) · [GitHub](https://github.com/IMRL/FMCW-LIO)
- [CrossSafe](https://arxiv.org/abs/2609.28984)
- [OSRAM](https://arxiv.org/abs/2609.28878) · [项目页](http://generalroboticslab.com/OSRAM)
- [BK-MBD](https://arxiv.org/abs/2609.28920) · [项目页](https://rcilab.khu.ac.kr/bkmbd/)
- [Training-free Behavior Cloning](https://arxiv.org/abs/2609.30134)
- [RAPID](https://arxiv.org/abs/2609.30249) · [项目页](https://yuyaoliu.me/projects/rapid)
- [Where Does Exactly-Once Live?](https://arxiv.org/abs/2609.29095)
- [Claude Code v2.1.283](https://github.com/anthropics/claude-code/releases/tag/v2.1.283)
- [GitHub Security Lab Fuzzing Taskflow](https://github.blog/security/application-security/ai-powered-fuzzing-with-the-github-security-lab-taskflow-agent/) · [GitHub](https://github.com/GitHubSecurityLab/seclab-taskflows-fuzzing)
- [STOMP](https://is.mpg.de/publications/kalakrishnan_raiic_2011) · [DOI](https://doi.org/10.1109/ICRA.2011.5980280) · [原始代码](https://github.com/kalakris/stomp_motion_planner_icra2011)
