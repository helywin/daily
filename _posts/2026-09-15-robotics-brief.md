---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-15"
date: 2026-09-15 09:00:00 +0800
description: "arXiv 9 月 15 日早间尚未刷新新批次，本期从最新公开列表补齐语义地图、规划控制、无人机能量规划、多机器人探索、VLA 与 ROS 2 工程优化，并跟进 Copilot 模型路由。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-15

## 摘要

截至今天早间，`cs.RO/recent` 的最新公开批次仍停留在 **2026-09-14**，因此本期不虚构“9 月 15 日新论文”，而是按规范向最近 7 天回补、并与覆盖索引去重。最新列表可见 9 月 14 日批次共有 59 条 Robotics entries；昨天已经覆盖 Chain-SLAM、Aerial LIO 参数敏感性、VertexCBF、ASTRIL-MPC、LIT、DWMP 等工作，所以今天继续从同批次中挑选此前未覆盖、且更贴近 SLAM / 规划 / 控制 / 工程落地的 7 篇论文，再加入 1 条 9 月 14 日 GitHub 官方 AI Coding 更新。([arXiv Robotics Recent](https://arxiv.org/list/cs.RO/recent))

今天最值得关注的三个信号是：第一，**地图正在从纯几何走向可查询的层级语义结构**，ProClosure 直接解决“一个对象到底属于哪个房间”；第二，**规划控制越来越强调执行器、能量与环境约束进入同一个闭环**，从多模型 Pure Pursuit 到 battery-aware multirotor planning 都在弱化“先规划一条几何路径，再让控制器尽量跟”的传统分层假设；第三，**机器人与 Coding Agent 都在显式管理计算预算**——ROS 2 的 Costmap 配置会影响真实能源消耗，Copilot 则把 Auto 路由进一步暴露为 efficiency / balance / intelligence 三档。

如果只选一个今天最值得自己复现的方向，我会选 **ProClosure**：它不要求重做一个 SLAM 前端，而是可以直接接在现有 RGB/SLAM 轨迹和开放词汇检测结果之后，作为 room-level scene graph 的结构恢复层；这类“地图后处理 + 语义层级”很适合现有巡检、语义导航和长期地图系统渐进加入。

## 1. ProClosure：单目视频的语义地图，关键不是“识别到了什么”，而是“它属于哪个房间”

**时间回补；v1 提交于 2026-09-11。**

### 为什么重要

很多语义 SLAM / 3D Scene Graph 系统已经能检测 chair、door、cabinet，但在真正做任务规划时，机器人更常问的是：

```text
“去厨房找灭火器”
“检查 2 号配电间里的仪表”
“到会议室拿杯子”
```

如果对象被错误挂到相邻房间，即使对象检测和 3D 坐标都正确，层级查询仍会失败。ProClosure 关注的正是 **room-object assignment**，而不是再做一个新的视觉里程计。([论文](https://arxiv.org/abs/2609.12614))

### 算法模块

它假设上游已经有：

```text
Monocular RGB Video
        ↓
SLAM front end
        ├─ Camera trajectory
        └─ Structural point cloud
        ↓
Open-vocabulary segmentation / tracking
        └─ Object tracks
        ↓
Top-down rasterization
        ↓
Progressive Boundary Closure
        ↓
Room regions
        ↓
Object → room assignment
```

核心观察很实用：在不完整点云里，“真正的门”和“因为没拍到而缺了一段墙”都表现为边界缺口。与其先可靠区分两者，不如先承认：**它们都不应该让一个房间无限扩张到另一个房间。**

ProClosure 因此逐步向内加厚边界；一个自由空间区域一旦闭合，就被冻结为房间。不同大小的缺口会在不同尺度下自行闭合，不需要提前选一个统一 morphology radius。相机轨迹本身又被用作 seed，减少随机采样带来的不确定性。

### 结果与适用假设

论文在 HM3D-Semantics 的 6 个场景、10 层楼上比较 HOV-SG：其输出 74 个房间，对应 72 个标注区域，而 HOV-SG 为 44 个；room F1 在 IoU 0.25 下由 0.741 提升到 0.890，object-to-room ARI 从 0.488 提升到 0.696。

这些数字说明它擅长修复“相邻房间被漏墙合并”的问题，但也要注意它仍依赖：

- 上游 SLAM 的尺度和位姿基本正确；
- top-down 投影对楼层结构是有意义的；
- 室内空间存在相对明确的墙体边界；
- 语义对象轨迹没有严重跨房间漂移。

### 实时性、鲁棒性与可复现性

它更像一个 **地图结构化后端**，不必运行在高频状态估计环里，因此可以与现有 ORB-SLAM3、VINS、LIO+相机语义前端松耦合。arXiv 页面已给出关联 GitHub 链接，适合直接拿现有录制数据验证。([论文页面](https://arxiv.org/abs/2609.12614))

### 工程风险

最大的风险不是计算量，而是**拓扑错误很难靠后续导航局部修正**。如果一堵墙因为建图漂移被错误闭合，可能把本来连通的区域切成两个 room；反过来，如果走廊和大厅没有清晰结构边界，也可能出现不稳定分区。

工程上最好同时保存：

```text
room polygon
closure scale
supporting wall points
camera seed poses
object-room confidence
```

这样后续回环或地图优化发生后，可以重算 room layer，而不是把第一次分区永久写死。

### 适合谁关注

语义导航、长期巡检、机器人问答、开放词汇地图、scene graph、家庭 / 工业室内移动机器人。

### 工程落地启发

如果已经有一套 LIO-SAM / FAST-LIO2 地图，再叠加 RGB 相机，完全可以不改定位前端：先把关键帧、墙面点云和对象 track 导出，再独立做一个 `room_graph_builder`。这比直接上完整神经语义 SLAM 风险更低，也更容易逐模块验收。

## 2. Global Path Planner with Multi-Model Switching：同一条全局路径，不应该假设机器人始终只有一种运动学

**时间回补；v1 提交于 2026-09-11。**

### 为什么重要

传统导航栈经常把路径规划与跟踪简化为：

```text
A* / Dijkstra → path → Pure Pursuit / MPC
```

但四足、轮足、全向平台甚至无人机，在不同地形、不同速度和不同运动模式下，真正可实现的运动学约束会变化。如果全程用同一个模型，路径在几何上可行，却可能在执行时出现大转角、侧滑、能耗上升或跟踪误差放大。

这篇工作把 **模型切换** 直接放到路径跟踪层。([论文](https://arxiv.org/abs/2609.13015))

### 算法模块

论文的主线是：

```text
Terrain / Map
    ↓
Traversability Graph
    ↓
Heading-Aware A*
    ↓
Geometrically feasible global path
    ↓
Multi-model Pure Pursuit
    ↓
根据 terrain feature + robot state
实时选择不同 kinematic model
```

这里最值得借鉴的不是 Pure Pursuit 本身，而是把“机器人当前应该按哪类运动学来解释”作为运行时状态，而不是配置文件里的一项固定参数。

### 传感器与模型假设

系统需要能够从地图或感知中获得 traversability / terrain feature，并且已经为各候选运动模式准备可用的 kinematic model。它不是在运行时凭空辨识完整动力学。

论文在 Artaban 四足机器人和 X3 quadrotor 仿真平台上验证，因此跨平台结果更像“架构可迁移性”证据，而不是已经证明所有地形下真机都鲁棒。

### 实时性与鲁棒性

Heading-Aware A* 仍属于可解释的图搜索，全局路径不需要神经网络；模型切换发生在跟踪器侧，理论上比每周期重新求解高维动力学优化更轻量。

真正工程化时应该重点记录：

```text
active_model_id
switch_reason
tracking_error_before_after_switch
energy / effort estimate
switch hysteresis
```

否则模型在临界地形频繁抖动切换，会把“自适应”变成新的控制不连续源。

### 工程风险

模型切换必须有 **滞回、最小驻留时间或连续 blending**。如果仅按一个地形阈值硬切，例如坡度 10° 用模型 A、11° 用模型 B，噪声会让控制器不断跳变。

此外，多模型系统最容易被忽略的是标定成本：模型越多，不代表越强；每个模型都要有明确适用域，否则只是增加维护复杂度。

### 适合谁关注

轮足机器人、四足导航、越野 UGV、多模态运动平台、复杂地形无人机路径跟踪。

### 工程落地启发

现有导航栈不必重构成学习系统。一个务实方案是保留全局 A* / Hybrid A*，在 local controller 前增加 `motion_mode_manager`：根据坡度、地面粗糙度、速度、曲率和足端状态输出一个 model profile，再让 Pure Pursuit / MPC 读取 profile。

## 3. Battery-Aware Multirotor Planning：无人机规划开始把“剩余电压能不能完成这个动作”纳入路径选择

**时间回补；v1 提交于 2026-09-10。**

### 为什么重要

无人机规划中常见的能量代价只是：

```text
path length
flight time
control effort
```

但真实电池不是一个无限电压源。相同轨迹在低 SOC、强风扰动和高控制需求下，可能触发 terminal-voltage 限制，使电机可用推力下降。因此“路径短”并不等于“安全可执行”。

这篇工作把 vehicle、motor、battery 三层闭环传播一起放进候选轨迹评估。([论文](https://arxiv.org/abs/2609.12188))

### 核心框架

```text
Candidate trajectories
       ↓
Disturbance model / spatial disturbance zones
       ↓
Closed-loop propagation
  ├─ vehicle dynamics
  ├─ controller demand
  ├─ motor response
  └─ battery evolution
       ↓
Energy + tracking + terminal-voltage-dependent actuator capability
       ↓
Trajectory selection
```

它的重要变化是：**规划器评价的不是一条开放环参考轨迹，而是“这条参考轨迹在真实闭环控制器 + 电机 + 电池下会发生什么”。**

### 一个需要特别谨慎的细节

arXiv 当前摘要把若干具体 benchmark 数字写在 `%` 注释后的文本里，包括电池模型误差和任务能耗变化。因此今天不把这些数字当成摘要已正式声明的核心结论；更稳妥的工程信息是论文明确提出了 battery-aware closed-loop predictive planning 框架，并让 terminal voltage 影响执行器能力评估。

### 传感器与状态要求

落地至少需要：

- SOC / 电压或可观测的 battery state；
- 电机 / 推力映射；
- 控制器结构与饱和约束；
- 外部扰动估计或空间扰动先验。

如果电池模型和电机模型误差很大，规划器会出现“精确地优化错误模型”的问题。

### 实时性与风险

相比纯几何规划，这种闭环 rollout 明显更重。工程实现可以采用两级策略：先用几何 / 动力学约束快速筛候选，再只对 Top-K 做完整 vehicle–motor–battery propagation。

更值得警惕的是 battery state uncertainty。低温、老化、电芯不一致都会让同一个 SOC 对应不同的可用功率。因此部署时应该给 voltage / power constraint 留 margin，而不是把预测值当精确边界。

### 适合谁关注

长航时无人机、强风场飞行、带载无人机、狭窄空间高动态飞行、低电量返航策略、工业巡检。

### 工程落地启发

如果现有 PX4 / 自研 MPC 已经能预测姿态和推力，不必马上加入完整 electrochemical model。第一步可以只加入一个简化 Thevenin / equivalent-circuit battery state，并把 `predicted_min_voltage` 与 `predicted_peak_thrust_margin` 作为 trajectory score 的硬门槛。

## 4. Size Doesn't Matter：把“土壤状态”作为策略状态，500 g 桌面机器人和 11.5 吨挖机可以共享同一套权重

**时间回补；v1 提交于 2026-09-11。**

### 为什么重要

挖掘、回填、筑堤这类任务不是普通刚体 manipulation。土壤会堆积、压实、塌落，工具和材料之间的接触状态决定下一步动作是否有效。只学习“铲斗轨迹 → reward”，很容易把材料状态隐含在某台机器、某个场景里。

这篇工作将材料的形状和 compactness 显式作为 policy condition，并在 GPU 并行 Material Point Method 仿真里训练。([论文](https://arxiv.org/abs/2609.12677))

### 方法结构

```text
GPU-parallel Material Point Method simulation
              ↓
Material state
  ├─ shape
  └─ compactness
              ↓
RL policy
              ↓
Normalized end-effector action space
              ↓
Calibrated machine interface
              ↓
不同尺度 / 不同执行机构
```

跨机器迁移的关键不是 domain randomization 一句话带过，而是把策略输出放在 **normalized end-effector space**，再用每台机器的 calibrated interface 去执行。

### 实验信号

论文报告同一套 learned weights 被部署在 11.5 吨液压挖掘机和约 500 g 桌面机器人上；全尺寸设备自主构建 42 m 长、2.1 m 高的筑堤，用时 45 分钟，完成 201 次 policy stroke，没有失败、重试或人工介入；作者还报告其推进速度与专家相当，成形结果更一致。

### 实时性、鲁棒性与可复现性

训练端 MPM 仿真成本高，但部署端是 policy inference + machine interface。真正 sim-to-real 的敏感点会集中在：

```text
soil parameter mismatch
bucket / tool geometry
hydraulic delay
joint backlash
material-state observation accuracy
```

论文最值得借鉴的是“材料状态 + 归一化末端空间 + 机器标定层”的分层设计，而不是把 11.5t 的成功直接理解为策略天然 scale invariant。

### 工程风险

土壤是典型的难建模对象。同一“compactness”指标未必能覆盖含水率、颗粒分布、黏性等变化。若环境超出训练材料分布，策略可能保持动作连贯，却持续做低效率甚至危险的推土动作。

部署时建议增加材料状态 OOD / action progress monitor，尤其要检测“连续多次 stroke 但地形目标几乎不改善”的情况。

### 适合谁关注

工程机械、矿山自动化、土方机器人、颗粒物操作、Sim2Real、接触丰富强化学习。

### 工程落地启发

这篇论文对一般机器人也有启发：跨本体迁移不一定先做复杂 representation learning，很多时候先把 **策略空间与硬件空间解耦**，再把 machine-specific 部分压到一个可标定接口，收益更确定。

## 5. MACE：多机器人探索里，通信不是“有信号就同步”，而是一个需要主动规划的任务

**时间回补；v1 提交于 2026-09-11。**

### 为什么重要

多机器人探索的理论加速来自并行，但如果通信间歇，团队会面对两个坏极端：

- 完全 opportunistic：只有偶遇通信时才同步，信息太陈旧；
- 固定 rendezvous：频繁为了会合绕路，探索效率反而下降。

MACE 把“值不值得为了通信偏离当前探索”显式做成规划问题。([论文](https://arxiv.org/abs/2609.12502))

### 算法模块

```text
Decentralized exploration
        ↓
Scheduled communication window
        ↓
Known / predicted communication locations
        ↓
Estimate travel cost to communicate
        ↓
Vehicle Orienteering Problem variant
        ├─ communication value
        ├─ travel detour
        └─ exploration reward along route
        ↓
communicate or keep exploring
```

这个建模方式比“每 N 秒去 rendezvous”更贴近实际，因为机器人去通信点的路上仍然可以探索，不必把通信成本简单看成纯损失。

### 结果与假设

论文在不同尺寸和几何的仿真环境中，相比已有通信约束探索策略，将总探索时间最多降低 23%。

但它隐含几个前提：

- 通信窗口可计划；
- 机器人知道或能估计哪些位置更可能建立链路；
- 局部地图与任务状态可以在连接后有效融合；
- 机器人之间没有严重定位框架不一致。

### 实时性与鲁棒性

MACE 是 decentralized framework，不依赖持续中心服务器；这对地下空间、灾害搜救、矿井和大厂区更现实。

实际部署最先暴露的通常不是 orienteering solver，而是**通信质量预测**：RSSI / SNR 与空间位置并不是确定映射，人体、设备、门、姿态都会造成快速变化。因此 communication location 应该带概率与历史统计，而不是二值“这里能连”。

### 工程风险

如果每个机器人都高估“我稍后能再连上”，团队可能长时间分裂；反过来，过于保守则会退化成频繁 rendezvous。

建议给系统加一个独立的 `information_age` 指标，例如：

```text
map_age
peer_pose_age
frontier_assignment_age
mission_state_age
```

通信决策不只看链路强度，也看“当前不同步到底有多危险”。

### 适合谁关注

多无人机、多四足、地下机器人、矿井 / 隧道探索、灾害搜救、弱网园区巡检。

### 工程落地启发

如果已有 frontier exploration，不必重写整个系统。可以先把 rendezvous 变成一种特殊 frontier：其 reward 由信息陈旧度和预期通信价值决定，再与普通探索 frontier 统一进入任务分配器。

## 6. ROS 2 Nav2 Costmap 调参：导航“能跑通”不代表能耗和算力配置合理

**时间回补；v1 提交于 2026-09-11；论文标注 ICRA 2026。**

### 为什么重要

机器人产品里，软件参数经常只用成功率和路径长度调：

```text
inflation_radius
resolution
update_frequency
publish_frequency
obstacle layer settings
```

但更高地图更新频率、更密 costmap 或更激进的 obstacle processing，会持续占用 CPU，并间接改变机器人停车、绕行和加减速行为。最终影响的是整机电量，而不是只有“导航好不好看”。

这篇论文专门研究 Nav2 Costmap 2D 配置对能耗和导航性能的影响。([论文](https://arxiv.org/abs/2609.12971))

### 实验设计

作者在两个 warehouse-like 场景中改变障碍布局和 Costmap 2D 配置，多次重复运行，同时测量：

```text
energy usage
power profile
CPU load
memory consumption
navigation performance
```

结论不是找到一套万能参数，而是发现配置对能耗和导航表现都有实质影响，并且“好参数”与环境相关。

### 为什么对工程团队比 benchmark 更有价值

很多团队会在台式机 / 工控机上把 Nav2 调好，再把同一套 YAML 复制到低功耗 ARM 平台。这样做的问题是，地图分辨率、更新频率和传感器层负载可能在新硬件上形成不同瓶颈。

因此导航调参最好由：

```text
成功率 + 轨迹质量 + CPU/GPU + 平均/峰值功率 + 单任务 Wh
```

共同驱动，而不是只盯 planner/controller 的局部指标。

### 实时性与可复现性

这项工作没有引入新神经模型，复现门槛反而较低。只要已有 ROS 2 Nav2 机器人，就可以设计 A/B 参数组，用功率计 / 电池 BMS + rosbag 记录做自己的 Pareto front。

### 工程风险

最大误区是把软件功耗与机器人总功耗混在一起。移动底盘的电机功率常常远大于 CPU；但软件配置又会改变路径、停走和加速度，所以不能简单用 `CPU watts` 代替任务总能耗。

### 适合谁关注

ROS 2 / Nav2 移动机器人、仓储 AMR、低功耗 ARM 主控、长续航巡检平台。

### 工程落地启发

建议在 CI / HIL 中增加一套“导航能源回归测试”：固定地图、固定起终点和障碍脚本，记录任务完成时间、路径长度、CPU 占用与 Wh。软件 PR 如果让成功率相同但 Wh 上升 15%，就不应该被当成无影响的参数改动。

## 7. Dynin-Robotics：把动作、未来观测、目标状态放进同一个 masked-diffusion 轨迹模型

**时间回补；v1 提交于 2026-09-11。**

### 为什么重要

当前 VLA 常见的做法是：视觉语言 backbone 输出表征，action head 生成动作；如果还需要 world model，就再加一套未来预测器。问题是不同模块的 latent 未必对齐，test-time planning 也难共享计算。

Dynin-Robotics 试图用一个共享 trajectory model 统一：

```text
language
visual observations
visual goals
actions
```

并用 masked diffusion 的不同 conditioning / target spans，完成多个方向的预测。([论文](https://arxiv.org/abs/2609.13053))

### 模型接口

同一模型可以学习：

```text
observation + language → action
observation + action → next observation
observation + language → terminal goal state
trajectory → instruction
```

因此测试时可以做 goal prediction、action candidate evaluation，以及 action / future-state joint refinement，而不是每种功能都起一个独立网络。

### 数据与结果

作者持续预训练约 **133 万条 trajectory，来自 48 个 Open X-Embodiment 数据集**，再对下游 domain 分别适配。论文报告在 LIBERO、zero-shot LIBERO-Plus 上具有竞争力，并在 Franka Research 3 的四种 manipulation condition 上得到 78.4% 平均成功率。

另一个很工程化的点是 block-parallel action decoding：在论文报告的 profiling setup 下，模型侧动作解码最多加速 29.2 倍。

### 假设、实时性与鲁棒性

它依赖统一离散 token 表示来容纳视觉、语言和动作；这给“同一模型多方向预测”带来接口整洁性，但也意味着 tokenization / quantization 本身会成为控制精度的上限之一。

真实机器人控制还必须考虑：

- inference latency；
- action chunk 执行期间的环境变化；
- future prediction error 是否会误导 action ranking；
- 大规模 heterogeneous embodiment 数据是否真的覆盖目标机器人的动力学。

### 工程风险

“world prediction 能生成合理未来”不等于“这个未来在控制上可信”。如果未来图像看起来合理，但接触状态、力或几何误差被视觉生成掩盖，candidate ranking 仍可能选错。

因此把它用于真实工业操作时，最好仍保留低层安全控制与独立状态约束，而不是让生成式未来成为唯一 verifier。

### 适合谁关注

VLA、world-action model、机器人 foundation model、跨本体预训练、低延迟 generative policy。

### 工程落地启发

更值得复用的是“**统一预测接口**”思想：即使不用大模型，也可以在同一个 latent dynamics 模块里同时训练 action prediction、next-state prediction 和 goal prediction，让控制器在部署时根据预算选择只调用其中一部分。

## 8. GitHub Copilot Auto：模型选择从“自动”进一步变成可配置的成本—质量策略

**2026-09-14 官方更新，属于最近 24 小时动态。**

### 发生了什么

GitHub Copilot 的 Auto model selection 新增三档：

```text
Efficiency   → 优先成本与速度
Balance      → 成本 / 质量 / 延迟折中
Intelligence → 优先复杂任务质量
```

三档使用的是同一可用模型池，Auto 仍会逐 prompt 判断应该路由到哪个模型；即使选 Intelligence，一个简单 docstring 任务仍可能被路由到小模型。该能力正在 VS Code、Copilot CLI 和 GitHub Copilot app 中滚动上线。([GitHub Changelog](https://github.blog/changelog/2026-09-14-configure-cost-and-quality-in-copilot-auto-model-selection/))

### 为什么这比“多了三个按钮”更重要

Coding Agent 的模型路由正在从：

```text
用户手选模型
```

转向：

```text
用户定义优化偏好
        ↓
系统按 prompt 难度 / 成本 / 延迟动态选模型
```

这和机器人里的 hierarchical controller 很像：不再让人每次决定“调用哪个控制器”，而是给一个 policy，让 runtime 自己做选择。

### 对重度 Coding 工作流的实际意义

如果日常任务混合了：

- 改变量名 / 写单测 / 补注释；
- 跨文件重构；
- 很长的 bug root-cause；
- 大仓库 architecture change；

那么固定使用最贵模型很浪费，固定小模型又会在复杂任务上反复返工。三档 Auto 的价值在于把“成本偏好”放到会话 / 用户策略层，而不是每个 prompt 都手工切模型。

GitHub 说明无论选哪一档，实际使用仍按 Auto 最终选中的模型计费；付费用户通过 Auto 的用量继续享受 10% 折扣。

### 风险与边界

Auto 最大的问题是**可重复性**。同一类任务如果不同时期被路由到不同模型，长期 benchmark、成本回归和输出风格会漂。

团队环境最好记录：

```text
requested_tier
effective_model
input/output/cache usage
wall time
task result
```

否则只能知道“Auto 今天变贵 / 变慢了”，却不知道是模型选择还是任务复杂度变化。

### 适合谁关注

Copilot CLI / VS Code 重度用户、多模型 Coding Agent、企业 AI 成本治理、自动模型路由系统设计者。

### 工程落地启发

自研 Agent 也可以抄这个模式：不要只有 `model=small/large`，而是把路由暴露成 `cost_priority / balanced / quality_priority`，再由 runtime 按任务风险、工具数量、代码影响范围和失败重试次数升级模型。

## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### A. 代码审查 Agent 不要只读 diff：让 reviewer 真正运行 build / test / targeted script

GitHub 9 月 11 日的 Copilot code review 更新提供了一个很明确的工程信号：Review Agent 现在会使用更完整的 shell 工具，在 agent firewall 后运行构建、测试、定向脚本和可用 API；Lite review 也改为多个 agent 的 ensemble，再把发现合并成一次 review。GitHub 自己的实验中，ensemble 后被实际处理的高严重度评论平均增加 47%、中等增加 31%、低严重度增加 11%，review cost 约下降 8%。([GitHub Changelog](https://github.blog/changelog/2026-09-11-auto-resolution-and-analysis-updates-in-copilot-code-review/))

**今天就能用的技巧：**把 Reviewer 的 system instruction 从“检查代码”改成“先建立最小验证计划，再运行与变更相关的 build/test/lint/script；无法执行时必须注明缺失证据”。对于高风险 PR，再并行起两个不同 reviewer：一个查 correctness，一个查 regression / security，最后由汇总 Agent 去重。

**适用场景：**Codex / Claude Code / Copilot 做 PR review、自动合并门禁、大型 C++ / TypeScript / Android 仓库。

**风险 / 边界：**shell 权限必须在 sandbox；reviewer 运行测试并不等于测试覆盖足够。Agent 的“测试通过”只能算一类证据，不能自动获得 merge authority。

### B. Prompt cache 是长会话 Agent 的成本基础设施，不要在一个 session 里随意改变 cached prefix

今天 r/ClaudeCode 的一篇社区问题总结了近期 Claude Code 的多项 prompt-cache 修复：包括 tool-call 后上下文未正确缓存、会话中切换 effort 造成 cache invalidation、subagent 恢复后 tool list / system prefix 变化导致 cache miss 等。作者还引用了官方 changelog 和 issue tracker，强调多 subagent + hooks + skills + 大上下文时，cache miss 可能把原本应复用的前缀反复作为 uncached input 处理。([Reddit 讨论](https://www.reddit.com/r/ClaudeCode/comments/1wbclml/claude_code_promptcache_bugs_who_pays_for_the/))

这属于**社区经验**，不能把帖子里的消费量直接当成所有人的普遍结果；但工程结论很有价值：缓存命中率应该像数据库 hit ratio 一样被监控。

**今天就能用的技巧：**长任务中尽量固定 system prompt、tool set、hooks 和 effort 档位；升级 Agent CLI 后，先用一个固定仓库 / 固定任务跑 3 次基线，记录 cached / uncached input、wall time 和总成本，再决定是否大规模切换版本。

**适用场景：**多 Agent 编排、长 context Coding、工作流里有大量 MCP / skills / hooks 的项目。

**风险 / 边界：**不要为了 cache hit 锁死所有工具。任务需要新能力时仍应允许改变工具集，只是要把 cache invalidation 当成可观测成本，而不是隐形副作用。

### C. 把 Context 当“树”而不是日志：探索完一条支线后，用 `/rewind` 保留代码、丢掉调试噪声

今天 r/ClaudeAI 有一篇社区工作流分享，核心顺序是：`/rewind → /compact → /clear`。作者特别推荐 `/rewind` 的“恢复对话、保留代码”模式：让 Agent 花大量上下文探索一个 bug，得出修复后把那段高噪声探索从 conversation history 切掉，但保留工作区里已经修改好的代码；复杂探索也可以交给 subagent，最后只保留一个结构化 handoff block。([Reddit 原帖](https://www.reddit.com/r/ClaudeAI/comments/1wgh4my/stop_writing_handoff_docs_rewind_is_the_tool_90/))

这同样是**社区经验**。帖子里诸如“80k tokens 是 tripwire”“成熟 spec map 可恢复 80% 代码库”都是作者经验，不应当作模型厂商保证。

**今天就能用的技巧：**把 feature knowledge 写成小型 `specs/<feature>.md`：只保留 `What / Where / How / Invariants / Tests`；对一次性调试、搜索和试错，让 subagent 做完后压成 10–30 行结论，再把原探索从主上下文移除。

**适用场景：**一个 session 用几天、跨文件重构、反复调 bug、上下文很容易膨胀的 Codex / Claude Code 工作流。

**风险 / 边界：**不要删掉关键决策理由。真正应该保留的是 invariant、接口契约、失败原因和验证结果，而不是“为了省 token 把所有历史都清掉”。

## 经典论文回顾

### Probabilistic Roadmaps for Path Planning in High-Dimensional Configuration Spaces（PRM，1996）

Lydia E. Kavraki、Petr Švestka、Jean-Claude Latombe、Mark H. Overmars，IEEE Transactions on Robotics and Automation，1996。([Kavraki Lab](https://kavrakilab.rice.edu/publications/kavraki-svestka1996probabilistic-roadmaps-for.html)，[DOI](https://doi.org/10.1109/70.508439)，[OMPL PRM](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1PRM.html))

### 它解决的核心问题

高维机械臂配置空间里，显式构造完整 free space 极其昂贵。PRM 的关键转变是：**不要把整个自由空间表示出来，只随机采一些可行 configuration，再用局部规划器把能连的点连接成图。**

算法被清晰拆成两阶段：

```text
Learning phase
  sample collision-free milestones
          ↓
  local planner connects nearby milestones
          ↓
  reusable roadmap graph G(V,E)

Query phase
  start / goal connect to roadmap
          ↓
  graph search
          ↓
  collision-free path
```

原论文的真正创新不是“随机点”，而是把昂贵的连续空间规划转化成 **可复用的离线连通性学习 + 在线离散图搜索**。

### 数学 / 算法直觉

定义 configuration space `C`，障碍区域 `C_obs`，自由空间：

```text
C_free = C \ C_obs
```

PRM 从 `C_free` 采样 milestone `q_i`。对于近邻 `q_j`，调用 local planner 判断是否存在一条简单连接 `L(q_i, q_j)` 完全位于 `C_free`。若成立就在 roadmap 中加边：

```text
(q_i, q_j) ∈ E
```

查询阶段只需把 `q_start`、`q_goal` 接入图，然后做 Dijkstra / A*。

在现代实现中，采样策略、连接半径 / k-nearest、碰撞检测器和 local planner 都可以替换；PRM* 进一步引入渐近最优连接策略。

### 为什么它在 1996 年很重要

当时 deterministic high-DOF planner 很容易被 configuration-space 复杂度拖垮。PRM 接受“随机化 + 概率完备”这条路线，用足够多样本去近似 free-space connectivity，让多自由度机械臂规划第一次获得非常实用的工程扩展性。

论文还天然提出了 multi-query 思想：同一静态场景里，roadmap 建一次，后续不同 start / goal 可以重复查询。OMPL 今天的 PRM 实现仍保留 `clearQuery()` 与复用 roadmap 的能力。

### 哪些思想今天仍然在用

今天的 sampling-based motion planning、roadmap、experience-based planning、multi-query manipulator planning，仍保留 PRM 的几个核心抽象：

```text
State sampler
Validity / collision checker
Nearest-neighbor structure
Local connector
Graph search
```

即使换成 learned sampler、neural distance field、GPU collision checking，系统骨架通常还是这五件事。

### 哪些部分已经被后续方法替代或增强

经典 PRM 的弱点包括：

- 窄通道很难靠均匀随机采样覆盖；
- 连边时 collision checking 成本很高；
- 默认更适合静态环境和 holonomic planning；
- roadmap 密度增加后近邻查询与边数会膨胀；
- 原始 PRM 只关心找到路径，并不保证代价渐近最优。

后续的 PRM*、RRT*、SST、BIT*、informed sampling、learned sampler、GPU collision checking，以及 trajectory optimization / MPC 都在补这些缺口。

### 2026 年再看 PRM，最值得重新理解的点

PRM 的思想其实非常适合今天的机器人系统：**把昂贵但可复用的结构预计算出来，把在线阶段压缩成小搜索问题。**

这和很多现代系统本质相同：

- 语义导航预建 scene graph；
- 多会话 SLAM 预建 keyframe / place graph；
- VLA 预计算 skill / latent graph；
- Coding Agent 预建 code graph / dependency graph。

所以今天复盘 PRM，不只是为了学一个机械臂 planner，而是为了理解“continuous problem → sparse reusable graph → cheap online query”这个非常长寿的系统设计模式。

### 现在怎么复现

最直接的是用 OMPL：

1. 选一个 6–7 DoF manipulator state space；
2. 实现 collision checker；
3. 跑 PRM、PRM*、RRTConnect 三组；
4. 固定场景，重复 100 个 start-goal query；
5. 比较首次建图时间、后续 query latency、成功率、roadmap 大小和路径长度。

真正有意思的实验不是“谁单次最快”，而是看 **query 数量增加以后 PRM 的预计算成本何时被摊薄**。

## 今日结论

今天没有硬凑 9 月 15 日尚未出现的 arXiv 新批次，而是利用 9 月 14 日最新公开列表继续去重回补。真正值得记住的不是 8 个标题，而是四个工程趋势：

1. **SLAM 后端继续结构化。** 几何位姿正确只是第一层，room / object / topology 正在变成导航系统真正消费的地图接口。
2. **规划与控制的边界继续变薄。** 多模型运动学、闭环 energy propagation、材料状态 RL 都在把“执行后果”提前放进决策。
3. **系统优化从单指标转向 Pareto。** ROS 2 参数不只影响导航质量，也影响 CPU 与任务能耗；Coding Agent 模型选择也显式暴露成本—质量—延迟偏好。
4. **长时 Agent 的可靠性越来越像传统系统工程。** 测试证据、缓存命中、权限边界、上下文生命周期、模型路由都需要可观测与可回归，而不是只靠 prompt 技巧。

## 最值得深入研究或尝试复现的方向

**首选：ProClosure + 现有 SLAM 的 room-level semantic graph。** 原因是它最容易在已有机器人系统中增量验证：不替换 LIO/VIO，不碰高频控制，只在后端增加 top-down structural map、progressive closure 与 object-room assignment。可以直接拿办公楼 / 走廊 rosbag 做 A/B：比较固定 morphology、connected-components、ProClosure 三种方法在 room count、object-room ARI、导航查询成功率上的差异。

**第二：给 Nav2 增加“任务能耗回归测试”。** 这是非常产品化的工作：把 Costmap 参数、CPU 占用、任务 Wh、完成时间放进一张 Pareto 表，比继续凭经验调 YAML 更容易形成不同硬件 SKU 的默认配置。

**第三：在无人机 planner 里增加简化 battery feasibility gate。** 不需要一开始复现整篇论文；先用 BMS 电压 + 简化电池模型预测候选轨迹最低电压 / 推力余量，就能验证“低 SOC 时几何最短路径是否仍是最优路径”。

**第四：给 Coding Agent 增加路由与上下文 telemetry。** 至少记录 effective model、cache hit / uncached input、tool set hash、验证命令和最终任务结果。这样以后比较 Codex / Copilot / Claude Code 或不同 Agent 架构时，不再只靠“感觉这版更费 token”。

## 参考资料

- [arXiv Robotics Recent](https://arxiv.org/list/cs.RO/recent)
- [ProClosure: Hierarchical Room-Object Assignment using Progressive Boundary Closure from Monocular Video](https://arxiv.org/abs/2609.12614)
- [Global Path Planner with Multi-Model Switching](https://arxiv.org/abs/2609.13015)
- [Battery-Aware Predictive Trajectory Planning and Control for Multirotors Under Disturbances](https://arxiv.org/abs/2609.12188)
- [Size Doesn't Matter: Material-State Reinforcement Learning for Excavator Transferable Soil Manipulation](https://arxiv.org/abs/2609.12677)
- [Communication-Constrained Multi-Robot Exploration With Adaptive Communication Windows](https://arxiv.org/abs/2609.12502)
- [Tuning ROS 2 for Energy-Efficient Navigation: Empirical Insights from Costmap 2D Configurations](https://arxiv.org/abs/2609.12971)
- [Dynin-Robotics: Omnimodal Unified Diffusion Vision-Language-Action Model](https://arxiv.org/abs/2609.13053)
- [GitHub: Configure cost and quality in Copilot auto model selection](https://github.blog/changelog/2026-09-14-configure-cost-and-quality-in-copilot-auto-model-selection/)
- [GitHub: Auto-resolution and analysis updates in Copilot code review](https://github.blog/changelog/2026-09-11-auto-resolution-and-analysis-updates-in-copilot-code-review/)
- [Reddit: Claude Code prompt-cache bugs](https://www.reddit.com/r/ClaudeCode/comments/1wbclml/claude_code_promptcache_bugs_who_pays_for_the/)
- [Reddit: Stop writing handoff docs. /rewind is the tool 90% of Claude Code users have never opened](https://www.reddit.com/r/ClaudeAI/comments/1wgh4my/stop_writing_handoff_docs_rewind_is_the_tool_90/)
- [Kavraki Lab: Probabilistic Roadmaps for Path Planning in High Dimensional Configuration Spaces](https://kavrakilab.rice.edu/publications/kavraki-svestka1996probabilistic-roadmaps-for.html)
- [PRM DOI: 10.1109/70.508439](https://doi.org/10.1109/70.508439)
- [OMPL: PRM Class Reference](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1PRM.html)
