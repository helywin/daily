---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-16"
date: 2026-09-16 09:00:00 +0800
description: "9 月 16 日聚焦 SLAM 轨迹评测、CBF 可行性认证、采样 MPC 灵巧手、多机器人曲率约束、人形跨本体控制、LiDAR 土壤状态估计、挖掘世界模型与机器人长期记忆。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-16

## 摘要

截至 2026-09-16 早间，arXiv Robotics 的最新公开批次仍以 9 月 15 日公布、9 月 14 日提交的工作为主，因此本期不虚构“9 月 16 日新论文”，而是从最新批次中继续做强制去重后的高价值回补。昨天的覆盖索引已经包含 P-POSEMEM、JEPLO、ResSafe、Volumetric Harmonic Field Navigation、GNSS 退化无人机、MPC 脚手架真机强化学习等工作，今天选择的 8 条主动态均未在索引中出现，并统一标注为时间回补。

今天值得特别关注四个信号。第一，SLAM 工程正在把“评测协议”本身当作算法组件：轨迹的时钟、采样、外参处理如果不标准化，ATE/RPE 的小数点并不可信。第二，安全控制从“QP 能不能解”进一步进入“为什么不可行、谁负责、如何重新分配约束”的可诊断阶段。第三，世界模型开始从预测展示走向真正的闭环 action ranking——挖掘任务已经能在 Jetson 上把多候选预测放进真实重型机械决策循环。第四，长期机器人系统越来越重视持久记忆与环境状态，而不是每次任务都从当前帧重新理解世界。

如果今天只选一个最适合现有机器人团队快速复现的方向，我会优先做 **轨迹评测协议标准化**：它不要求替换任何 SLAM 前端，却能直接发现时间同步、外参和采样对结论的污染；对于正在比较 LIO-SAM、FAST-LIO2、不同 16 线 / MID360 配置的工程团队，收益非常直接。

## 1. Comparing Trajectories from Positions Alone：SLAM 的 ATE/RPE 之前，先把时间、采样与外参说清楚

**时间回补；v1 提交于 2026-09-14。**

### 为什么重要

机器人定位评测经常看起来非常标准：导出估计轨迹和真值轨迹，跑 evo 或自研脚本，得到 ATE、RPE，然后比较谁更小。但这篇工作指出一个长期被低估的问题：如果时间同步、采样点配对和传感器外参没有被显式统一，最终误差会混入评测管线本身的误差，甚至改变算法排名。

论文提出一套面向状态估计、定位与 SLAM 的标准化轨迹评测协议，核心包含两部分：基于轨迹曲率信号的时间对齐，以及按行驶距离归一化的漂移误差。作者还把 temporal synchronization、sampling alignment、extrinsic calibration 的影响单独做敏感性分析。（[论文](https://arxiv.org/abs/2609.14936)）

### 算法模块

可以把流程理解成：

```text
estimated positions ─┐
                     ├─ curvature signal → temporal alignment
reference positions ─┘
                              ↓
                     sampling alignment
                              ↓
                     extrinsic calibration
                              ↓
              distance-normalized drift metric
                              ↓
                     sensitivity analysis
```

曲率是一个很实用的选择：它从“轨迹形状变化”中寻找时间对应关系，而不是要求两条轨迹预先拥有完全可信的同步时间戳。对只有 position ground truth、没有完整姿态真值的野外机器人数据，这一点尤其有价值。

### 传感器与评测假设

它不是新的 SLAM 前端，因此不限定相机、LiDAR 或 IMU。真正的假设是两条轨迹共享足够的运动结构，使曲率信号能够形成可辨识的时间特征。如果机器人长时间直线匀速、几乎没有转弯，曲率本身的时间辨识能力就会下降。

另外，按距离归一漂移更适合回答“每走一定距离积累多少误差”，但不能替代所有任务指标。对于短程高精度机械臂、原地旋转、纯姿态定位等任务，仍需要单独的 orientation / task-space 指标。

### 实时性、鲁棒性与可复现性

这是离线评测协议，不进入实时状态估计回路，计算负担不是核心问题。真正的价值在于**可复现性**：建议每个 SLAM benchmark 报告至少保存以下元数据：

```text
clock source / offset
trajectory sampling rate
interpolation method
estimated↔reference frame extrinsic
alignment method
alignment interval
drift normalization distance
```

这样才能区分“算法改好了”与“评测脚本换了对齐方式”。

### 工程风险

最大的风险是团队把一个新的对齐算法当作“自动修复所有数据问题”的工具。时间对齐只能处理可观察的时移，不能补救随机时钟抖动、严重丢帧、真值传感器自身漂移或错误外参。对齐自由度太大还可能反过来把算法误差吸收到评测变换里。

### 适合谁关注

LiDAR SLAM / VIO / LIO 算法团队、无人机状态估计、长期定位、机器人 benchmark 与回归测试维护者。

### 工程落地启发

如果你现在已经有多套 LIO 算法，不要先继续换前端。先做一个统一的 `trajectory_eval` 工具：原始时间戳不可覆盖、外参显式版本化、对齐过程输出诊断图、同时给出 ATE/RPE 与 distance-normalized drift。然后用同一套 bag 重跑所有算法，很可能会先发现评测层面的差异。

## 2. Multi-Robot CBF Feasibility Certification：安全 QP 失败时，系统应该知道“为什么失败”

**时间回补；v1 提交于 2026-09-14。**

### 为什么重要

Control Barrier Function 常被部署成 nominal controller 外的一层安全过滤器：把原始控制指令投影到满足安全约束的可行集合。但多机器人场景中，多个避碰约束、执行器上限和异构动力学会同时挤压控制空间，QP 最终可能无解。

传统系统通常只能得到一个“solver infeasible”。这篇工作进一步提出精确可行性证书，把安全约束带来的 demand 与执行器能够提供的 supply 分开，给出可行性余量，并定位到底是哪个 agent / interaction 导致冲突。（[论文](https://arxiv.org/abs/2609.14935)）

### 算法模块

核心逻辑可以抽象成：

```text
heterogeneous control-affine dynamics
              +
convex actuator input sets
              +
multi-agent CBF constraints
              ↓
exact feasibility certificate
   ├─ safety demand
   ├─ actuator supply
   └─ feasibility reserve
              ↓
identify responsible interactions
              ↓
optimal shared-constraint allocation
              ↓
polyhedral inputs → linear program
```

这比简单增大 CBF gain 更有意义，因为证书能判断：当前冲突是“调 gain 还有救”，还是“物理执行能力根本不够”。

### 结果与控制假设

论文面向 heterogeneous control-affine systems 与 convex input sets。对于 polyhedral 输入约束，共享安全责任的优化可以落成线性规划。作者在 320 组配对闭环仿真中报告，新的责任分配将不可行控制步从约 50% 降到 6.2%，安全违规运行从 118/160 降到 24/160；52 次不可行事件中，证书在 94% 情况下定位到一个放松后可恢复可行性的交互。

这些数字是仿真结果，不应直接等同于真机安全保证，但它们说明“可诊断安全过滤器”比单纯 QP 成功/失败二值状态更有工程价值。

### 实时性、鲁棒性与可复现性

如果输入集合是多面体，新增优化可以保持在 LP 级别，适合作为 CBF-QP 周边的诊断 / 分配层。真正部署时应把以下量打进 telemetry：

```text
feasibility reserve
active safety constraints
responsible pair / group
actuator saturation margin
allocation result
QP/LP solve time
```

这样事故前后的“安全空间被谁吃掉了”才可追踪。

### 工程风险

证书建立在动力学和输入约束可信的前提下。若轮胎侧滑、推力衰减、电池低压、执行器迟滞没有进入模型，所谓 supply 会被高估。另一个风险是为了恢复数学可行性而错误放松本不该让步的安全规则，所以生产系统需要区分硬约束与可协商约束。

### 适合谁关注

多无人机、多移动机器人、CBF 安全过滤、异构机器人协作、安全 MPC / RL 系统。

### 工程落地启发

现有系统如果已经用 CBF-QP，可以先不改变 nominal controller，只增加一层 `feasibility_monitor`。一旦余量接近零，提前降低速度、扩大机器人间距或改变任务分配，而不是等 QP 真正 infeasible 后再做紧急停止。

## 3. Primitive-Informed Sampling-Based MPC：灵巧手高维采样，不是“多撒点样本”就能解决

**时间回补；v1 提交于 2026-09-14。**

### 为什么重要

采样式 MPC 很适合接触丰富操作，因为不要求对复杂接触动力学求解析梯度；但多指灵巧手的关节空间维度高，直接在 joint space 中随机探索会把大量预算浪费在不协调动作上。

这篇工作采用低维 manipulation primitives 去偏置采样，同时保留 joint-level residual，让控制器既继承“手指应该怎么协同”的先验，又能根据当前 hand-object 状态做局部适配。（[论文](https://arxiv.org/abs/2609.14868)）

### 算法模块

```text
low-dimensional manipulation primitive
                 ↓
        biased action sampling
                 +
        joint-level residual
                 ↓
      forward dynamics rollout
                 ↓
 task-related rollout constraints
      reject infeasible samples
                 ↓
      sampling-based MPC update
                 ↓
          execute / replan
```

它与“扩大 sample count”最大的区别是：先改变采样分布的结构，再增加计算量。论文消融明确显示，primitive 和 residual 都是可靠连续手内旋转所必需，仅提高采样预算不能恢复同样的协调性。

### 动力学与传感器假设

实验使用物理 Allegro Hand 与同步 MuJoCo digital twin。也就是说，方法仍需要一个足够有用的 rollout model，但不要求模型完美：作者报告从单个物体提取的 primitive 在不同物体尺寸和模型失配下仍然有效。

框架还扩展到抓取、物体重定向，以及机械臂 + 手的 reach-grasp-transport；primitive 可以来自仿真训练策略，也可以来自人手运动数据。

### 实时性、鲁棒性与可复现性

采样 MPC 的实时性依赖并行 rollout。工程上最值得借鉴的是把预算分成三层：

```text
coordination prior → 决定“往哪里采”
residual          → 决定“如何局部适配”
rollout constraint→ 决定“哪些样本立即丢弃”
```

这比盲目加 GPU sample count 更容易稳定扩展。

### 工程风险

primitive 质量会决定搜索偏置。如果 primitive 与新任务的接触模式差异太大，强偏置反而可能错过真正可行区域。因此建议保留一定比例的 broad exploration samples，并监控 primitive-guided 与 residual-only 两类候选的有效率。

### 适合谁关注

灵巧手、接触丰富 manipulation、MPPI / sampling MPC、数字孪生控制、Sim2Real。

### 工程落地启发

对于高维机器人控制，不妨把 learned policy 当作 proposal prior，而不是最终 controller。策略负责提供低维动作结构，MPC 负责结合当前模型与约束做短时闭环修正，这通常比“纯 RL”或“纯随机 MPC”都更容易解释和调试。

## 4. Distributed Safe Cooperative Vector Field：多机器人避障必须尊重真实转弯能力

**时间回补；v1 提交于 2026-09-14。**

### 为什么重要

很多多机器人路径跟踪方法默认机器人可以立即产生任意方向速度。但差速底盘、车辆和固定翼 / 非完整约束平台都有曲率限制：即使几何避障向量看起来安全，机器人也可能根本转不过去。

这项工作提出面向 trajectory-curvature-constrained multi-robot systems 的分布式安全协同向量场，把协同路径跟随和碰撞避免一起设计，并使用可自适应调整的 reactive boundary 使避碰动作保持运动学可实现。（[论文](https://arxiv.org/abs/2609.15266)）

### 算法模块

```text
desired path / cooperative objective
              ↓
     cooperative vector field
              +
 safety collision-avoidance vector field
              ↓
adaptive reactive boundary
              ↓
curvature-feasible local command
```

通信方面，每个邻居只需要共享一个 virtual variable，用于实现协同运动，同时处理障碍物与机器人之间的碰撞避免。

### 动力学假设与验证

方法明确把 trajectory curvature 作为约束，因此比“点机器人 + 任意速度向量”模型更接近轮式平台。作者同时进行了仿真和真实多机器人平台实验，并说明该工作获得 CCSICC 2025 Best Student Paper。

### 实时性与鲁棒性

向量场控制本身通常比在线非线性优化轻量，非常适合高频本地控制。分布式结构也避免了中心协调器成为单点瓶颈。

鲁棒性问题主要来自邻居状态延迟与局部感知误差。工程部署时最好为 virtual variable 附带时间戳，并对 stale neighbor 采用更保守的 collision envelope。

### 工程风险

曲率约束只是可执行性的一部分：高速平台还会受制动距离、轮胎侧向力、加速度 / jerk 限制影响。如果速度升高，只控制曲率而没有动力学安全余量，仍可能在理论上“能转”但实际停不住。

### 适合谁关注

AMR 编队、无人车、多机器人巡检、低带宽协作、非完整约束机器人。

### 工程落地启发

已有 ORCA / 人工势场 / vector-field 系统可以先加入一个 curvature feasibility layer，而不必立刻换成完整 DMPC。先过滤那些底盘不可能执行的瞬时避碰方向，通常就能显著减少“规划说安全，控制跟不上”的问题。

## 5. X-WBC：人形机器人控制开始把“人体动作语义”与“具体本体执行”拆开

**时间回补；v1 提交于 2026-09-14；已接收 CoRL 2026。**

### 为什么重要

当前很多 humanoid whole-body control 策略仍是一台机器人训练一套 policy。这样 Unitree G1、不同尺寸人形或自研本体上的运动经验无法共享，导致每换硬件都要重新采数据、重做 reward 和重新训练。

X-WBC 的核心思路是把相对共享的 human motion semantics 与 embodiment-specific physical execution 解耦，让不同本体共同贡献训练经验。（[论文](https://arxiv.org/abs/2609.15213)）

### 模型结构

```text
full human motion
robot reference motion
sparse VR observations
       ↓
human-centered command tokens
       ↓
shared causal Transformer
       ↓
reusable temporal motion representation
       ↓
robot-specific lightweight modules
       ↓
proprioception / action for each embodiment
```

这里最值得关注的是 command interface。它没有强迫所有机器人共享完全相同的关节空间，而是在更高层的人体动作语义中对齐，再把最后一段映射交给本体特定模块。

### 数据、传感器与结果

论文在 9 个仿真本体、外部动作数据和 4 台真实机器人上评估。作者报告联合训练改善 tracking，并让同一表示在 full motion、robot reference 与 sparse VR 等不同 command source 下保持一致控制能力；策略在训练动作之外仍保持竞争力。

### 实时性、鲁棒性与可复现性

因果 Transformer 可以在线运行，但真实频率仍取决于模型规模、硬件和低层控制接口。论文摘要没有把端到端控制周期作为核心结论，因此工程上不应假定它能直接替换高频关节控制器。

更务实的部署是：foundation policy 产生中频动作参考，底层 PD / WBC / torque loop 继续负责高频稳定与硬件保护。

### 工程风险

跨本体共享表示最怕“语义相似但动力学不可达”。例如相同人体动作在不同腿长、关节限位和扭矩密度下可能对应完全不同的可行域。共享模型必须与本体能力边界一起训练，否则迁移会在极端动作上失真。

### 适合谁关注

人形机器人、动作重定向、VR 遥操作、whole-body control、跨本体 robot foundation model。

### 工程落地启发

如果公司有多个轮足 / 四足 / 人形 SKU，数据层最好尽早区分“任务 / 动作语义”与“底层关节命令”。把本体相关映射压到 adapter，不但利于 foundation policy，也让后续仿真数据和人类动作数据更容易复用。

## 6. Tracking the Ground：LiDAR 地图不只描述地面，地面本身也可以成为在线状态

**时间回补；v1 提交于 2026-09-14。**

### 为什么重要

传统移动机器人通常把地面当作静态几何背景：建一个 elevation map 或 point cloud，然后基于坡度和粗糙度规划。但农业、松软土壤、矿区等环境里，机器人自己的轮胎会持续改变地形。

这篇工作提出从 LiDAR 观测在线量化 traffic-induced soil deformation，并用低阶参数模型表示土壤行为，从而把 soil state 变成持续可观测、可更新的机器人状态。（[论文](https://arxiv.org/abs/2609.15667)）

### 算法模块

```text
LiDAR ground observations
          ↓
local ground / deformation extraction
          ↓
reduced-order parametric soil model
          ↓
physically interpretable parameters
          ↓
continuously updated soil state
          ↓
future soil-aware planning / behavior adaptation
```

它的价值不在于再做一个稠密地形重建，而是把“机器人经过后地面发生了什么”从地图残差提升为系统状态。

### 传感器与环境假设

核心传感器是 LiDAR。模型需要在不同观测时刻建立足够稳定的地面对应关系，因此定位误差、车体姿态误差和点云遮挡都会直接污染“形变”估计。

论文在不同土壤条件下做实验，证明方法能捕捉机器人造成的地面变化。摘要没有宣称它已经闭环优化车辆路径，因此更准确的理解是：它建立了 soil-aware control / planning 所需的可观测状态接口。

### 实时性、鲁棒性与可复现性

低阶参数模型比直接维护高维连续介质状态更适合在线运行，而且参数具有物理解释性，便于做异常检测和跨地块比较。

工程上应把 localization uncertainty 与 soil-state uncertainty 一起维护，否则地图轻微漂移很容易被误判为土壤沉降。

### 工程风险

湿度、土壤类型、轮载、轮胎花纹、行驶速度都会影响形变。低阶模型如果只在窄分布土壤上标定，跨地块泛化可能很差。此外，LiDAR 只能看到表面形变，不等价于完整的土壤压实状态。

### 适合谁关注

农业机器人、矿山 / 土方机器人、越野 UGV、可变地形建图、terrain-aware planning。

### 工程落地启发

对于轮足机器人或无人车，可以把地图从单层 elevation map 扩成：

```text
geometry layer
traversability layer
robot-induced change layer
confidence / observation-age layer
```

这样规划器就能避免反复碾压已经明显变形的区域，或主动选择更稳定的地面。

## 7. World-Model-Guided Excavation：世界模型真正有用的地方，是在闭环里替你“挑动作”

**时间回补；v1 提交于 2026-09-14。**

### 为什么重要

挖掘不是单次动作任务：每一铲都会改变下一铲面对的地形。一个世界模型如果只能生成“看起来合理的未来”，对控制帮助有限；它必须能在有限时间内比较多个候选动作，并把预测结果变成下一步决策。

这篇工作提出 World-Action Model（WAM），对多个候选 scoop 做几何过滤，预测 signed terrain change 和 loaded volume，再执行预测载荷最大的候选，重新观测后继续规划。（[论文](https://arxiv.org/abs/2609.15382)）

### 闭环结构

```text
current terrain observation
          ↓
propose multiple scoops
          ↓
geometric admissibility filter
          ↓
world-action prediction
   ├─ signed terrain change
   └─ loaded volume
          ↓
rank candidates
          ↓
execute best scoop
          ↓
re-observe terrain → replan
```

这是比“预测视频”更接近机器人世界模型最终价值的形式：prediction 是 decision 的内部模块，而不是最终产品。

### 结果与实时性

在 32 个 geometry-disjoint MinSlope 测试 episode 上，加入 world-model ranking 后，平均 scoop 数从 651.8 降到 540.6，减少 17.1%，同时保持 32/32 完成，并且每个配对 episode 都改善。完整系统比较中，WAM 完成 32/32，独立训练的 SAC 为 29/32。

更关键的工程指标是：ROS 2 + TensorRT 实现在 Jetson AGX Orin 上处理 5 个候选耗时 72.4 ms，并且完整 perception → proposal → prediction → selection → execution 流程已经部署到全尺寸装载机，作者将真实实验表述为闭环可行性验证。

### 模型与感知假设

系统依赖可用的地形观测和候选 scoop proposal。世界模型并不直接解决所有动作搜索问题，而是把候选空间控制在少量可实时评估的动作上。

这种结构本质上是 learned value/model 与 model-predictive selection 的混合：生成器保证候选多样性，几何规则做硬过滤，学习模型负责排序。

### 鲁棒性与工程风险

最大的风险是模型 ranking error。若世界模型在分布外地形上高估某一动作，系统会主动选择错误动作。因此实际设备应该保留硬几何约束、执行中止条件、载荷 / 液压异常监控，并记录 prediction-vs-realized terrain delta 做在线校准。

### 适合谁关注

工程机械、矿山自动化、世界模型、接触丰富规划、Jetson 边缘推理、机器人闭环 action selection。

### 工程落地启发

世界模型不必一次替换 controller。一个低风险路径是先把它作为 **candidate ranker** 接到现有规则 / MPC 规划器之后：旧系统仍负责产生可行轨迹，世界模型只对 5–20 个候选打分。这样更容易验证，也更适合逐步上真机。

## 8. MessyMem：机器人长期记忆应该记录“我做过什么、结果怎样”，而不只是保存地图和视频

**时间回补；v1 提交于 2026-09-14；已接收 CoRL 2026。**

### 为什么重要

移动操作机器人今天的常见矛盾是：地图很紧凑但忘掉交互经验，视频很完整但几乎不可查询，VLM planner 每次任务又要从当前输入重新推理。

MessyMem 试图把这三者连起来：维护空间对齐的 3D scene graph，给对象 / 位置增加由真实交互学到的 property 与 outcome，再链接关键视觉观测供细粒度回忆。（[论文](https://arxiv.org/abs/2609.15976)，[项目页](https://messymem.github.io/)）

### 记忆结构

```text
3D scene graph
  ├─ objects
  ├─ locations
  └─ spatial relations
        +
interaction-derived properties / outcomes
        +
linked visual observations
        ↓
queryable persistent memory
        ↓
future mobile-manipulation planning
```

例如“柜门打不开”“某物体上次在这个抽屉”“这个位置操作失败过”不应该只存在历史视频里，而应该变成下一次规划能直接消费的结构化知识。

### 结果与适用假设

论文同时在仿真和真实移动操作平台评估。在一个持续 3 小时以上、25 个连续任务的仿真中，MessyMem 达到 80.0% task progress，比最强消融高 14.8 个百分点，比最强外部 baseline 高 28.9 个百分点；它能从数千个 keyframe 和一小时前的历史中取回与当前任务相关的证据。

这些结果强调的是跨任务经验复用，而不是一次性任务成功率。

### 实时性、鲁棒性与可复现性

长期系统最大的瓶颈通常不是一次查询速度，而是 memory growth、错误写入和 stale knowledge。工程实现至少要给每条记忆附上：

```text
source observation
pose / map version
timestamp
confidence
interaction outcome
last verification time
```

如果 SLAM pose graph 后续发生大幅修正，空间记忆还必须跟随地图坐标重写，否则“记得越多，错得越系统”。

### 工程风险

长期记忆最大的风险是错误的持久化。一次误识别“柜门锁着”如果被当成永久事实，可能让机器人未来永远不再尝试。记忆系统需要区分事实、一次观测、可变属性和失败经验，并支持遗忘 / 重新验证。

隐私和存储也是实际问题：长期保存视觉 keyframe 可能包含人员与敏感环境信息，应支持权限、脱敏和生命周期管理。

### 适合谁关注

长期巡检、家庭机器人、移动操作、语义导航、scene graph、Embodied Agent memory。

### 工程落地启发

对于已有 SLAM + 任务规划系统，第一步无需上复杂 memory model。可以先给 scene graph 节点增加一个 append-only interaction journal：`action / result / timestamp / evidence / confidence`，再做按对象和房间的检索。只要能让任务失败经验跨 session 被复用，就已经开始获得长期记忆的价值。

## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### A. 敏感动作的审批状态不要放在 Agent 能删除的文件里

9 月 15 日的一条 Claude 工作流社区分享讨论了一个非常现实的权限问题：如果“允许 merge / deploy”的 marker file 位于 Agent 可写目录，那么 Agent 可能通过删除或修改 marker 绕过软性审批。分享者建议把授权状态放到 Agent 权限边界之外，并在 `PreToolUse` 一类 hook 中使用明确的拒绝退出状态，而不是只返回自然语言提示。（[Reddit 原始讨论](https://www.reddit.com/r/ClaudeWorkflows/comments/1wglhhm/workflow_securing_claude_code_agents_preventing/)）

这属于**社区工程经验**，不是安全认证结论，但思路非常值得照搬：安全状态不能和被约束主体共享同一个可写控制面。

**今天怎么用：**把 `merge_allowed`、生产部署批准、密钥解锁等状态移到只读环境变量、外部审批服务或 Agent 无写权限的目录；hook 只读这些状态。拒绝路径必须 fail-closed，工具执行失败时默认不放行。

**风险 / 边界：**hook 本身也属于安全边界。若 Agent 可以修改 hook 配置、启动参数或执行器代码，外置 marker 仍然不够，需要 OS/container 权限进一步隔离。

### B. Claude Code 与 Codex CLI 混用时，先明确谁拥有 orchestration loop

一篇在 9 月 15 日更新的工程文章系统整理了 Claude Code 与 Codex CLI 的双向 MCP 连接方式。最有价值的不是“两个工具可以互相调用”，而是明确了三种角色分工：Claude 做规划、Codex 做明确子任务执行；Codex 做测试 / 执行外循环、Claude 做复杂诊断；或者用阶段 gate 串联多个专业 Agent。（[原文](https://codex.danielvaughan.com/2026/03/26/claude-code-codex-bidirectional-mcp/)）

**今天怎么用：**不要让两个 Agent 同时认为自己是总控。为一次任务固定一个 owner：

```text
orchestrator
  ↓ produces explicit artifact
verification gate
  ↓
worker agent
  ↓ produces patch / test result
verification gate
  ↓
next phase
```

对于 Codex 子任务，用 workspace sandbox；对于 Claude 暴露给外部 orchestrator 的工具，优先 allowlist `Read/Grep/Glob`，只有确实需要时再开放 Bash / Write。

**风险 / 边界：**文章也提醒 MCP 层并不会自动转发下层 MCP 工具；此外 headless 权限、`approval-policy: never` 和共享配置文件都会扩大攻击面。跨 Agent 编排首先是权限工程，其次才是 prompt engineering。

### C. Flaky test 重试不能把 Agent 回归“洗绿”

9 月 15 日的 Coding Agent Guide 新增了一条针对 flaky tests 的实践：采用**有限重试 + 每次尝试保留证据 + 有过期时间的 quarantine**，而不是“失败就重跑，最后一次过了就算绿”。（[指南入口](https://codingagentguide.com/)）

这对于 Coding Agent 特别重要，因为 Agent 很容易把已有 flaky test 当成自己改动无关的噪声；反过来，无限重试又可能把真实回归隐藏掉。

**今天怎么用：**CI 中给 flaky candidate 固定最多 2–3 次重试，保存每次日志、seed、环境和失败签名；如果首次失败、后续通过，状态应标记为 `FLAKY/UNSTABLE` 而不是普通 PASS。quarantine 必须有 owner 和 expiry date。

**风险 / 边界：**不要让 Agent 自己决定把一个新失败加入永久 quarantine。新增 quarantine 应经过独立 review，否则它会成为最简单的“通过测试”捷径。

## 经典论文回顾

### ORB-SLAM3：An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM

Carlos Campos、Richard Elvira、Juan J. Gómez Rodríguez、José M. M. Montiel、Juan D. Tardós。论文 2020 年首次公开，2021 年修订并发表于 IEEE Transactions on Robotics。（[论文](https://arxiv.org/abs/2007.11898)，[DOI](https://doi.org/10.1109/TRO.2021.3075644)，[官方代码](https://github.com/UZ-SLAMLab/ORB_SLAM3)）

### 它解决的核心问题

ORB-SLAM2 已经把单目、双目和 RGB-D 特征 SLAM 做成非常成功的统一系统，但对现代机器人而言仍有两个明显缺口：一是视觉惯性需要真正统一的 MAP 优化与可靠 IMU 初始化；二是长期运行中机器人会丢失、重定位、建立多个局部地图，系统不能假定永远只维护一张连续 map。

ORB-SLAM3 因此把系统提升成：

```text
camera / camera+IMU
        ↓
feature tracking + keyframes
        ↓
visual / visual-inertial MAP estimation
        ↓
local mapping
        ↓
place recognition
        ↓
Atlas: multiple maps
  ├─ start new map after tracking loss
  ├─ relocalize
  └─ merge maps after revisiting
```

它支持 monocular、stereo、RGB-D，相机模型包括 pinhole 与 fisheye，并把 visual、visual-inertial、multi-map SLAM 放进同一套系统。

### 关键数学思想：IMU 初始化也放在 MAP 框架里

很多 VIO 系统会把初始化视为一个与后端割裂的特殊阶段。ORB-SLAM3 的重要思想之一，是视觉惯性状态估计包括初始化阶段都依赖最大后验估计框架。

抽象看，系统优化的是：

```text
X* = arg min_X (
    visual reprojection residuals
  + IMU preintegration residuals
  + prior / marginalization terms
)
```

状态中不仅有相机 / IMU 位姿，也包含速度、IMU bias、尺度与重力相关变量。初始化质量决定了后续整个 VIO 是否落在正确 basin，因此它不是一个可以随便“先猜一下再说”的前处理。

### Multi-Map / Atlas 为什么重要

ORB-SLAM3 的另一个长期影响是把 tracking failure 从“系统结束”改造成“地图生命周期事件”。当视觉信息长期恶化时，可以新建 map；当重新进入已知区域时，通过 place recognition 把新旧地图合并。

这对长期机器人非常关键，因为真实系统必然会经历：

```text
强曝光 / 黑暗
纯旋转或低视差
动态遮挡
镜头暂时被挡
重启 / 多次巡检
跨 session 重访
```

Atlas 的思想告诉工程团队：**丢定位不是异常分支，而应该是一等状态。**

### 当年为什么重要

论文报告其 stereo-inertial 配置在 EuRoC 上平均精度达到厘米级，并在 TUM-VI 快速手持场景达到毫米到厘米量级；更重要的是，它把成熟 feature-based SLAM、IMU 紧耦合与多地图生命周期做成一个可用的开源系统，成为很多研究和工程对比中的强基线。

### 今天仍然在使用的思想

即使 2026 年已经有大量 neural SLAM、3DGS SLAM 和 foundation-model mapping，ORB-SLAM3 的几个系统原则仍然非常现代：

- 前端跟踪、局部地图与全局地图分频运行；
- IMU initialization 是可观测性问题，不只是参数调节；
- place recognition 不只是“加一个 loop closure”，还决定 map merge；
- 允许多张地图长期共存，再按证据合并；
- 所有历史共视 keyframe 都可以在需要时重新进入优化，而不是只看最后几秒。

### 哪些部分今天已被增强或替代

经典 ORB 特征在弱纹理、重复纹理、强照明变化下仍有局限；现代 learned feature / global descriptor 可以提高匹配和回环鲁棒性。大规模长期地图也越来越倾向 submap / hierarchical graph / map compression，而不是无限增长的 keyframe graph。

对于高速、高动态或强退化平台，事件相机、LiDAR、轮速、GNSS / RTK、Radar 等多模态融合会比纯视觉惯性更稳。语义地图和可查询 scene graph 也不是 ORB-SLAM3 的设计重点。

### 公开代码、数据与可复现性

官方仓库长期公开，常用 EuRoC、TUM-VI、KITTI 等数据集可以直接复现。真正工程复现时最值得严格记录的是 camera-IMU time offset、内外参、IMU noise / random walk 与相机曝光；这些参数对 VIO 初始化和稳定性影响远大于很多表面上的 feature threshold。

### 对今天工程项目的重新解读

ORB-SLAM3 最值得重新学习的并不是 ORB descriptor，而是 **Atlas + failure recovery**。如果今天设计 LiDAR / multi-sensor 长期定位，也可以照搬这个状态机：

```text
active local map
      ↓ tracking confidence drops
start isolated submap
      ↓ place evidence appears
cross-map registration
      ↓ geometric verification
factor-graph merge
```

对于矿区、长走廊、跨楼层巡检和多 session 建图，这比强迫定位器“永不丢失”更现实。

## 今日结论

今天这批工作呈现出一个很清晰的工程趋势：机器人算法正在从“单模块分数更高”转向**系统可诊断、可持续运行、可闭环验证**。

SLAM 方面，新的轨迹评测工作提醒我们，误差指标的可信度取决于完整评测协议；经典 ORB-SLAM3 则再次说明 tracking loss 与 map merge 应该进入系统设计本身。控制方面，CBF 可行性证书和曲率约束协同控制都在把“理论安全”推进到“物理可执行且能解释失败原因”。采样 MPC 与世界模型的共同思路，则是把 learned prior / prediction 放在受约束的候选选择器中，而不是让学习模型独占最终控制权。

长期自主性也出现两个很值得关注的状态变量：一个是会被机器人本身改变的**环境状态**，如土壤形变；另一个是跨任务积累的**经验状态**，如 MessyMem 的交互结果记忆。机器人真正长期运行时，这两者都不能继续被当作静态背景。

AI Coding 侧的三条实践实际上与机器人安全非常相似：授权状态应位于执行 Agent 权限之外；多 Agent 编排要有唯一 orchestration owner 和可验证 handoff；测试重试必须保留失败证据，不能把异常“重跑成绿色”。本质上都是把系统从“会做事”升级成“知道自己凭什么可以继续做下一步”。

## 最值得深入研究或尝试复现的方向

**首选：统一轨迹评测管线。** 把现有 LIO-SAM、FAST-LIO2、KISS-ICP 或 VIO 的输出统一进入同一个时间同步 / 外参 / 插值 / drift-normalized pipeline。用人为加入 10 ms、20 ms、50 ms 时间偏移和毫米到厘米级外参误差做 sensitivity sweep，你会非常直观地看到评测协议本身能制造多大“算法差距”。

**第二：给 CBF / MPC 增加 feasibility telemetry。** 不只记录 solver success，而是记录 active constraints、输入余量、最紧张的机器人对和 saturation margin。哪怕暂时不复现完整 certificate，也能先把“为什么差点无解”变成可观测数据。

**第三：把 learned model 当 candidate ranker。** 无论是无人机规划、机械臂还是工程机械，都可以让现有规则 / 优化器产生少量安全候选，让世界模型只负责预测后果和排序。这个架构比端到端动作输出更容易做 A/B、fallback 和真机上线。

**第四：为长期地图增加 interaction journal。** 在 object / room / landmark 节点上保存动作结果、置信度、时间和证据；配合 pose-graph 版本管理，让语义 / 经验记忆能够随地图重写。这是从传统 SLAM 走向长期 embodied memory 的低风险起点。

## 参考资料

- [arXiv Robotics Recent](https://arxiv.org/list/cs.RO/recent)
- [Comparing Trajectories from Positions Alone: Curvature-Based Time Alignment and Drift Error Metric](https://arxiv.org/abs/2609.14936)
- [Exact Feasibility Certification and Optimal Responsibility Allocation for Multi-Robot CBF Safety Filters](https://arxiv.org/abs/2609.14935)
- [Primitive-Informed Sampling-Based MPC for Multi-Fingered Dexterous Manipulation](https://arxiv.org/abs/2609.14868)
- [Distributed Safe Cooperative Vector Field for Trajectory Curvature Constrained Multi-Robot Systems](https://arxiv.org/abs/2609.15266)
- [X-WBC: A Cross-Embodiment Foundation Model for Humanoid Whole-Body Control](https://arxiv.org/abs/2609.15213)
- [Tracking the Ground: Online Lidar Identification of Robot-Induced Soil Deformation in Agricultural Environments](https://arxiv.org/abs/2609.15667)
- [From Prediction to Decision: World-Model-Guided Action Selection for Continuous Pile Excavation](https://arxiv.org/abs/2609.15382)
- [MessyMem: Learning-from-Doing Memory for Mobile Manipulation](https://arxiv.org/abs/2609.15976)
- [MessyMem Project Page](https://messymem.github.io/)
- [社区讨论：Securing Claude Code Agents](https://www.reddit.com/r/ClaudeWorkflows/comments/1wglhhm/workflow_securing_claude_code_agents_preventing/)
- [Claude Code ↔ Codex CLI: Bidirectional MCP Integration](https://codex.danielvaughan.com/2026/03/26/claude-code-codex-bidirectional-mcp/)
- [Coding Agent Guide](https://codingagentguide.com/)
- [ORB-SLAM3 Paper](https://arxiv.org/abs/2007.11898)
- [ORB-SLAM3 DOI](https://doi.org/10.1109/TRO.2021.3075644)
- [ORB-SLAM3 Official Repository](https://github.com/UZ-SLAMLab/ORB_SLAM3)
