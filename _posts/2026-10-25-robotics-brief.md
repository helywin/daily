---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-25"
date: 2026-10-25 09:00:00 +0800
description: "稀疏跨会话拓扑度量地图、OASIS 动态语义锚点、WarpWeaver 分布式协同规划、九种人形的统一奖励、无示范驾驶、自适应多视角 VLA、云端与本地接管，以及 Coding Agent 旧指令冲突实证。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-25

## 摘要

**检索基准：2026-10-25 09:00（Asia/Shanghai，星期日）。** arXiv 的最新常规 Robotics（cs.RO）与 Software Engineering（cs.SE）列表均为 **2026-10-23（星期五）**，分别有 **107 条／63 条新提交**和 **51 条／25 条新提交**；总量包括交叉列表和替换版本。周末最近 24 小时没有新的常规论文批次，所以按照任务规范扩展到最近七天。本期研究的原始 v1 日期为 2026-10-21 至 22 日 UTC，均明确标注**时间回补**，不能把列表的公开日期误当首次提交日。

选题与 GitHub 历史覆盖索引截至 10 月 24 日的 **1,101 条**记录进行规范化标题、arXiv ID、DOI、项目主页与仓库地址联合去重。最终选择 **8 条主动态、3 条 AI Coding 实战技巧与 1 篇经典论文**；本期不重报昨天的 Joint-CI、ProTrav、GlobMP、OpenTac 或单步 Flow 工作。

今天的主线是**把地图、控制和 Agent 的信任边界放到正确层级**。稀疏 Topometric Graph 尝试用极低地图内存完成跨会话室内导航；OASIS 通过稳定语义锚点检索动态场景中的物体。WarpWeaver 使用异步分布式搜索近似联合多机器人规划；MPBRS 在九种人形本体间复用潜势奖励配置。TerraTransfer++ 将高速自博弈与视觉学生策略分开，FocusVLA 根据未来交互阶段动态选择相机视角。CARE 让本地具身 Agent 在风险上升时才请求云端接管。Coding Agent 的最新对照研究则发现，过期指令文件可能迫使模型违背当前代码事实。

所有定量指标均来自作者指定实验条件；尚未验证的开源、真机性能、端侧推理延迟不做保证。原始列表：[Robotics](https://arxiv.org/list/cs.RO/new) · [Software Engineering](https://arxiv.org/list/cs.SE/new)。

## 1. Sparse Topometric Graph：用拓扑连通性与局部三维几何跨会话重定位

**时间回补：2026-10-22 UTC 首次提交。**

### 为什么重要

跨天巡检时，参考地图与当前相机、LiDAR 的视觉细节、照明甚至传感器类型可能都不同。密集点级地图需要大量内存；逐点细匹配又容易在相似走廊和房间内发生混淆。《A Sparse Topometric Graph for Scalable Cross-Session Indoor Navigation》将**局部 3D 几何节点**与**表示可通行关系及距离的边**组合成稀疏图，跨会话通过节点描述子和邻域连通结构联合匹配。这更适合“先前地图中指定一个目标，第二次进入时不知道初始位置”的导航任务。

### 算法模块、传感器与假设

~~~text
Reference Session: Local 3D Geometry → Topometric Nodes → Distance-weighted Edges
New Session: Local Observations → Local Subgraph
                           ↓
          Learned Subgraph Matching
                           ↓
        Cross-session Graph Alignment
                           ↓
          Point-goal Global Guidance
                           ↓
       Current Local Obstacle Avoidance
~~~

图匹配利用邻域关系降低单个局部几何描述子的歧义；但拓扑本身仍然可能因封门、施工和新隔断而改变。该研究**不是新的高频六自由度 LiDAR–IMU 里程计**，必须有可靠的局部运动估计和传感器坐标标定。图中边的历史可通行性也不等于当下没有障碍。

### 实验、实时性、鲁棒性与复现

作者报告，跨会话目标导航在 Gibson 的成功率为 **77.1%**，在存在场景变化的 3D-FRONT 条件下为 **40.0%**；相对点级地图表示，内存减少**超过两个数量级**。两组成功率属于不同场景，不能混为统一定位成功率。公开摘要没有可外推到 RK3588 的端到端 FPS，也未确认完整、一键运行的官方工程仓库。

最小复现可以冻结同一批局部几何，比较点级全局匹配、仅节点描述子和节点＋邻域拓扑匹配。记录跨会话目标到达率、错误图对应、内存、地图加载时间及地图版本跳变。

### 适合谁关注与工程落地启发

适合多楼层巡检、长走廊、跨会话建图和低内存机器狗。可以将稀疏图作为跨会话导航层，仍由 FAST-LIO/VIO 承担局部位姿、由最新 3D Costmap 负责碰撞检查。**图的“边存在”仅说明历史上可通行，不是实时安全证明。**

**原始来源：** [论文](https://arxiv.org/abs/2610.31432)。

## 2. OASIS：通过稳定语义锚点维护动态环境中的对象位置

**时间回补：2026-10-22 UTC 首次提交；ACM MM 2026 Oral。**

### 为什么重要

长期运行的机器人常常知道“工具柜”或“工作台”在哪里，却发现柜上的工具已被移走。将所有历史 RGB-D 观测一直加到稠密语言地图中，不仅内存上涨，也会产生过期对象位置。OASIS（Online Anchor-centric Scene Inference System）将室内场景组织为相对稳定的**语义锚点节点**，每个锚点保存文字描述、视觉特征与几何状态，按需检索和提取证据，并利用导航途中获得的新观测重新定位移位对象。

### 算法模块、观测假设与风险

~~~text
RGB(-D) / Odometry / Scene Observations
                    ↓
         Stable Anchor Nodes
      ├─ Semantic Description
      ├─ Visual Appearance
      └─ Geometric State
                    ↓
       Hierarchical Retrieval
                    ↓
  Verification / On-demand Evidence
                    ↓
  Object Relocation from New Observations
                    ↓
     Semantic Goal → Local Planner
~~~

稳定锚点不代表对象永远不动。重复设备、相似房间和遮挡会影响实例身份；里程计漂移会影响地图中的对象坐标。更新对象位置之前应验证实例一致性、观测时间和所依赖的地图版本。语义查询层不能取代实体几何规划。

### 实验、实时性与可复现性

论文展示了仿真和真实环境中的开放词汇检索、导航以及场景变化后的物体重定位。官方摘要**未报告可通用的统一检索准确率、FPS 或存储削减百分比**，因此不编造指标。也尚未确认完整公开训练权重与一键部署仓库。

复现建议先在同一 RGB-D 序列中移动一个目标：比较不断追加对象记录、全量重建和锚点式增量重定位；评价旧位置误报、对象 ID 连续性、更新延迟与地图内存。

### 适合谁关注与工程落地启发

适合工厂巡检、仓储、语言目标搜索。推荐将对象状态拆成“历史最后位置、当前已确认位置、最后证据时间”，并在目标行动前使用最新局部感知确认。**语言地图的作用是选目标，不是代替障碍可通行性检查。**

**原始来源：** [论文](https://arxiv.org/abs/2610.30589) · [ACM 关联 DOI](https://doi.org/10.1145/3767308.3835228)。

## 3. WarpWeaver：异步分布式多机器人规划接近联合最优解

**时间回补：2026-10-22 UTC 首次提交；投稿 IEEE T-RO。**

### 为什么重要

集中式联合轨迹优化在机器人增加时容易遇到计算、通信瓶颈；完全分布式避碰则未必优化全队总行程。论文《Dispersive Tree Agreements for Multi-Robot Coordination》提出 WarpWeaver：机器人各自从可微平坦系统的控制指令前向传播生成候选树，再通过**分布式列生成与共享空间价格协商**协调路径。规划器是 Anytime 的：即使实时 Deadline 中断协商，也可以保留已经取得的可用结果。

### 算法模块、动力学假设与理论边界

~~~text
Robot A/B/... Forward-propagated Control Trees
                     ↓
     Locally Encoded Coupling Constraints
                     ↓
      Decentralized Column Generation
                     ↓
    Shared-space Price / Rent Negotiation
                     ↓
  Agreement Candidate → Execute Prefix
                     ↓
       Receding-horizon Replanning
~~~

作者讨论了满足条件时的近最优一致性以及协商达到静止状态后的证书。但**协商被 Deadline 提前截断，不等于已经获得完整的近最优证书**。推导依赖特定动力学类别、局部耦合约束构造以及及时交换的信息；严重通信丢包或另一台机器人没有遵守计划时，还需独立的局部避碰保护。

### 实验、实时性、鲁棒性与复现

在指定仿真中，WarpWeaver 相比集中式离线规划器将总行程时间最多减少 **22%**，相比所选分布式实时基线最多减少 **37%**；六台机器人在硬件上实现了机载规划。两个改善属于不同对照，不能相加。论文摘要未给出通用 P99 规划时延和全失联安全保证。

最小复现从双机器人交叉路口开始，固定总搜索预算，比较集中式 MPC、局部 RVO/ORCA 和 WarpWeaver 风格的协商。额外注入消息过期，记录最小机器人间距、协商次数、当前解质量与 Deadline Miss。

### 适合谁关注与工程落地启发

适合多机仓库、狭窄共享通道和无人机机群。建议先在任务层协商目标通道和时间窗，真实本地控制仍独立检查当期障碍、可执行性与急停。**分布式“可以随时输出方案”，不意味着中途所有输出都具有相同的最优性保证。**

**原始来源：** [论文](https://arxiv.org/abs/2610.31540)。

## 4. MPBRS：九种人形机器人的潜势奖励统一配置

**时间回补：2026-10-21 UTC 首次提交。**

### 为什么重要

四足和人形 RL 经常将速度跟踪、躯干姿态、能耗、脚部接触等奖励项手工加权；换一台机器人就要重新调一次。论文《MPBRS: Multi-Potential-Based Reward Shaping for Unified Reward Configuration in Humanoid Locomotion》研究利用多个潜势函数构成 Reward Shaping，使同一奖励结构与权重在**九种人形机器人**上复用，只需修改机器人关节、链接映射和默认姿态等元数据。

### 算法模块与理论前提

常见潜势奖励可以写为 F(s,a,s') = γΦ(s') − Φ(s)，多个潜势可组合。满足经典 PBRS 假设时，塑形奖励改善学习导向而不改变原任务的最优策略集合。工程上依然要核对折扣因子、终止状态处理、潜势是否依赖动作以及权重的跨本体尺度一致性；如果随意增加未满足形式的奖励，策略不变性结论就不成立。

~~~text
Shared Task Objective
       +
Potential Functions (posture / velocity / contact ...)
       +
Robot-specific Joint / Link Metadata
                 ↓
         Reward Shaping
                 ↓
       Common PPO/RL Pipeline
                 ↓
  Cross-embodiment Regression Evaluation
~~~

### 实验、实时性、鲁棒性与复现

作者在九种人形上报告，相比普通塑形方式，其学习表现随配置变化更加一致，对权重调节更不敏感。公开摘要**没有能够跨机器人泛化的单一成功率或统一加速比**，也未确认完整官方代码。此研究主要是**训练奖励设计**，不能理解为新的人形实时控制器。

可在现有 Isaac/MuJoCo 强化学习框架中使用相同训练预算、不同机器人元数据，比较人工逐机奖励、完全共享普通奖励、共享 MPBRS；报告收敛速度、站立/行走成功率、速度误差、功耗和接触违规。

### 适合谁关注与工程落地启发

适合 Unitree G1 和多本体 Locomotion 平台。先实现可版本化的 reward 配方，把“本体元数据”和“任务本身要求”分开；独立动力学限制、跌倒保护不可因潜势理论而删除。

**原始来源：** [论文](https://arxiv.org/abs/2610.30334)。

## 5. TerraTransfer++：不依赖人工驾驶示范的自博弈训练与视觉策略蒸馏

**时间回补：2026-10-21 UTC 首次提交。**

### 为什么重要

视觉端到端驾驶通常需要大量真实驾驶日志，或在高保真模拟器里不断运行昂贵的视觉主干。TerraTransfer++ 把“学会决策”与“学会看图像”拆开：先在高吞吐向量化模拟器中自博弈训练基于场景状态的策略，再蒸馏出 Flow-Matching 轨迹教师，最后用冻结的视觉主干和轻量适配器，将配对的**图像／场景状态**映射到已有教师的表示与决策。它不是完全不需要数据，而是不需要人工驾驶轨迹作为模仿标签。

### 算法模块、传感器与动力学假设

~~~text
Vectorized Self-play with Scene State
                ↓
         Reactive Policy
                ↓
 Flow-matching Trajectory Teacher
                ↓
 Paired Image / Scene-state Frames
                ↓
Frozen Visual Backbone + Lightweight Adapters
                ↓
 Vision-conditioned Policy / Planner
                ↓
 Closed-loop Driving Benchmark
~~~

训练用的场景状态与真实车辆传感器必须具有相同或可对齐的语义；模拟器交通规则、动力学与图像分布偏差都可能导致 Sim2Real 失败。驾驶系统还需要独立的障碍和执行器约束，不能仅凭 NAVSIM 分数认证道路安全。

### 实验、实时性与鲁棒性

作者报告，无人工示范的 Planner 在 **NAVSIM navhard 达到 59.4 EPDMS**，超过论文比较的 DriveZero-Scale **57.1**；在 navtest 达到 **95.5 PDMS**，并在 HUGSim 闭环测试中取得有竞争力的表现。navhard 与 navtest 的度量和场景不同，不能直接对比为同一指标。高速自博弈的“百万步/秒”是仿真总体样本吞吐，并非真实车控频率。完整可直接运行的训练代码与权重尚未核实。

### 可复现性与工程落地启发

适合自博弈路径规划、无人车与策略蒸馏。建议固定同一驾驶场景与视觉 Backbone，分别测试人工模仿、状态教师蒸馏和轻量视觉适配，比较闭环冲突/碰撞、干预次数、延迟及跨区域泛化。**自博弈的价值在于补充长尾状态分布，不应被等同于省略真实世界闭环验证。**

**原始来源：** [论文](https://arxiv.org/abs/2610.30319)。

## 6. FocusVLA：根据未来交互意图动态调度腕部与全局相机

**时间回补：2026-10-22 UTC 首次提交；CoRL 2026。**

### 为什么重要

多相机机械臂 VLA 有固定的全局视角和腕部视角，但模型可能长期偏信腕部图像：靠近物体时局部细节有用，搬运和最终放置时，全局场景几何又更重要。FocusVLA 利用历史动作预测即将发生的交互阶段，再动态调节不同视角对 Action Expert 的贡献，避免固定视角权重。

### 算法模块与传感器假设

~~~text
Global Camera + Wrist Camera
              +
History of Action Chunks
                 ↓
    Future Interaction Intent
                 ↓
      Dynamic View Routing
                 ↓
      Original VLA Backbone
                 ↓
          Action Chunk
~~~

它对模型核心架构的修改较小，但依赖正确的跨相机时间同步、标定和动作历史。预测的阶段可能错误；如接触阶段突然变化或腕部摄像头被遮挡，视角路由应具备降级和恢复策略。

### 实验、实时性、鲁棒性与复现

作者报告 RoboTwin 2.0 相比最强 π0.5 对照的平均成功率提高 **10.10 个百分点**；真实机器人成功率从 **71.7% 提升到 85.0%**，即 **13.3 个百分点**（不应误写成 13.3% 的相对增长）。摘要没有完整硬件端到端 P95；官方一键运行源码状态尚待核实。

可在现有双摄 VLA 上固定基础模型和动作数据，比较腕部独占、双摄固定融合、阶段感知路由；统计任务成功率、相机失效后恢复和动作突变。

### 适合谁关注与工程落地启发

适合双臂、Franka、插接/放置、多视角 VLA。**不要默认“多给模型一张图”就能获得多视角互补，应该测试模型是否在正确的任务阶段使用正确的视角。**

**原始来源：** [论文](https://arxiv.org/abs/2610.31423)。

## 7. CARE：端侧具身 Agent 何时该把控制升级给云端大模型

**时间回补：2026-10-22 UTC 首次提交。**

### 为什么重要

云端强模型进行每步规划会因网络和推理使机器人停顿；全程使用端侧小模型则容易在复杂状态下失败。CARE（Critic-guided Adaptive Execution）引入轻量评判器，在本地执行可靠性下降时升级到云端模型，并在恢复之前保持接管状态，避免每一步来回路由。两个执行者通过共享 Handoff Memory 继承任务进度。

### 算法模块、时序与安全边界

~~~text
On-device Executor + Robot State
                 ↓
         Reliability Critic
                 ↓
           Escalation?
       ├─ No → Local Fast Path
       └─ Yes → Cloud Executor
                      ↓
             Shared Handoff Memory
                      ↓
          Recovery Verification
                      ↓
               Local Resume
~~~

共享状态应包括当前任务、最后已执行动作、观测时间与工具权限；未执行动作不能因为切换执行者就被重复执行。网络超时应进入本地稳定的保守控制，而不是无限等待云端。如果云端和本地对当前世界状态存在分歧，必须重新观测，而不是强行拼接旧动作块。

### 实验、实时性、鲁棒性与可复现性

作者报告，CARE 相对所选最强协作基线的任务成功率提高 **6.3–18.3 个百分点**；相对 Cloud-only 的中位动作间隔延迟降低 **28.8%–82.6%**，在部分任务中达到接近或超过云端专用方案的成功率。范围跨不同任务，不能当成任意网络状况下的固定收益。摘要没有断联安全认证或全部工具链 P99 数据，完整官方仓库尚未核实。

### 适合谁关注与工程落地启发

适合边缘计算平台、ROS2 工具式机器人、混合云/本地 Agent。先在仿真里做“只记录升级建议”的 Shadow Mode，再加入延迟、失败接管、持续云端不可达等故障。**模型路由与物理控制权不是一回事：任何规划模型都不能获得绕开本地安全控制器的权限。**

**原始来源：** [论文](https://arxiv.org/abs/2610.30587)。

## 8. Stale Instruction Files：一条规则降低 Coding Agent 被过期项目指令带偏的概率

**时间回补：2026-10-22 UTC 首次提交。**

### 为什么重要

AI Coding Agent 需要阅读 AGENTS.md 或 CLAUDE.md 中的项目规则。但是规则可能多年未更新，与当前源码约定相矛盾。例如文档要求统一采用某种日志工具，而主分支仍使用另一种接口。Coding Agent 可能看到冲突后仍按旧规则修改，甚至主动大范围重写当前正确代码。论文《Stale Instruction Files Override the Code in Coding Agents: A One-Sentence Fix》用可控项目检验这个问题。

### 实验与工程流程价值

研究构造 **40 个 Python 项目、320 次运行**，让 Claude Code 与 Codex CLI 在项目指令和真实代码冲突时添加功能。没有特殊修正时，**90.1%** 的选择遵循过期文件；一个关于“冲突时以当前代码为准”的用户级指令，使遵循代码的比例从 **4.2% 提高到 91.4%**，测试通过率从 **89.4% 到 100%**。这些是作者的小型受控实验，不能直接外推到所有真实大型仓库。

作者还报告，Claude Code 在 80 次中的 79 次指出冲突却仍按旧文件操作；Codex CLI 在 80 次中有 20 次为迎合指令重写原代码，其中 17 次导致原测试失败。表明**发现冲突不等于能够正确处理冲突**。

### 可复现性、权限与工程风险

可将下列简短规则放进用户级 Agent 指令，与项目文件形成明确仲裁原则：

> 当项目说明与当前代码及通过的测试不一致时，先核实代码的现行行为；不要为遵循可能过期的说明而批量重写现有代码，遇到真正的需求冲突先列出差异。

这不是说代码永远高于明确的安全约束或用户新需求。安全、权限与本次明确指定的行为契约仍应优先；当前代码可能本身就有 Bug。

### 适合谁关注与工程落地启发

适合大型 C++/Java/ROS2 仓库、跨会话接力和 Code Agent 过度工程化治理。选择两三个真实冲突文件，在独立 Worktree 中比较有无该规则时的修改范围、测试结果与新增文档数量。不要因此额外建复杂的“说明文件真实性评估平台”；**一个明确的冲突裁决规则加当前源码与独立测试已足以检验收益。**

**原始来源：** [论文](https://arxiv.org/abs/2610.30571) · [作者数据与代码](https://github.com/WenJing95/stale-docs-data)。

## AI Coding 实战技巧精选

### 技巧 1｜用 Codex 0.164.0 的 /presets 固定常用权限与模型配置

- **来源：** OpenAI，2026-10-23，[Codex 0.164.0 官方 Release](https://github.com/openai/codex/releases/tag/rust-v0.164.0)。
- **一句话结论：** 新版本可保存十个编号的可复用 Prompt/斜杠命令 Preset，并可在 /model、/permissions 中直接设置模型、推理档位、速度与权限配置。
- **具体怎么做：** ① 执行“codex --version”确认版本；② 在测试 Worktree 的交互式 Codex 里打开“/presets”，将“只读排查”“普通实现”“代码审查”分成不同槽位；③ 使用“/model”和“/permissions”检查每个工作模式的真实授权，再在同一组测试任务上比较切换开销和误授权次数；④ 对需要高风险写操作的任务继续要求显式审批。
- **适合什么场景：** Codex CLI、多项目、需要频繁切换模型与权限档位的编码任务。
- **注意：** Preset 是方便复用指令，不是安全沙盒；权限边界应以实际配置和工具提示为准。

### 技巧 2｜回归 Claude Code 2.1.310 的符号链接真实路径提示与 Hook 拦截

- **来源：** Anthropic，2026-10-23，[Claude Code v2.1.310 官方 Release](https://github.com/anthropics/claude-code/releases/tag/v2.1.310)。
- **一句话结论：** 新版本修复文件读取权限请求不显示符号链接真实指向，以及 Windows 缺少 Git Bash 时某些 Hook 命令未正确拦截的问题。
- **具体怎么做：** ① 用“claude --version”确认版本；② 在隔离临时目录中创建指向另一测试目录的符号链接，检查读取审批能否显示真实目标；③ Windows 环境用无害的测试 Hook 覆盖 Git Bash 缺失场景，确认拒绝规则仍有效；④ 对比升级前后结果，检查工作树没有越界修改。
- **适合什么场景：** Claude Code、本地开发机、Worktree、复杂项目路径与自动 Hook。
- **注意：** 不要拿真实凭据或系统敏感目录试验；CLI 的权限修复不等于替代 OS 级目录访问控制。

### 技巧 3｜把企业自动化的长期 PAT 逐步迁移到按权限安装的 GitHub App

- **来源：** GitHub，2026-10-23，[Enterprise GitHub Apps GA 官方公告](https://github.blog/changelog/2026-10-23-enterprise-installations-for-github-apps-generally-available/)。
- **一句话结论：** GitHub Apps 的企业级安装正式 GA，规则集、策略、审计等 API 覆盖增加。符合条件的企业可减少长期 Classic PAT 在 Agent/CI 中的使用。
- **具体怎么做：** ① 列出当前自动化使用的 PAT 权限及调用的 GitHub API；② 在企业 App 设置中申请具体所需的只读或读写权限，先从审计/读操作迁移；③ 为独立测试工作流使用安装令牌，验证调用结果、令牌过期和拒绝行为；④ 管理员审核后才迁移规则集、成员或权限等写操作。
- **适合什么场景：** GitHub Enterprise Cloud、内部 Coding Agent、组织 CI 和企业治理自动化。
- **注意：** 企业级安装不自动等于每个仓库都授权；需要组织/仓库数据的 App 仍需对应安装与权限，迁移前应验证每个 API 的权限模型。

## 经典论文回顾

### ORCA / Reciprocal n-Body Collision Avoidance（2011）：让多机器人相互承担避碰责任

**发表时间与历史位置。** Jur van den Berg、Stephen J. Guy、Ming Lin 和 Dinesh Manocha 的《Reciprocal n-Body Collision Avoidance》发表于 2011 年 *Springer Tracts in Advanced Robotics*，第 3–19 页，DOI：[10.1007/978-3-642-19457-3_1](https://doi.org/10.1007/978-3-642-19457-3_1)。它继承 Velocity Obstacles 和 RVO 思想，发展为广泛使用的 ORCA。

**核心问题。** 多台移动机器人互相避让，如果每台都认定“对方负责避碰”，就会碰撞；若每台都采取完整避碰动作，又可能造成过度保守和振荡。ORCA 在相对速度空间构造避碰约束，让双方各承担一部分责任，使单台机器人选择新的安全速度可以转化为低维线性规划。

~~~text
Preferred Velocity + Neighbor Position / Velocity
                    ↓
       Relative Velocity Obstacles
                    ↓
       Reciprocal Half-plane Constraints
                    ↓
            Small Linear Program
                    ↓
        Collision-avoiding Velocity
                    ↓
       Differential-drive / MPC Adapter
~~~

**关键数学思想与假设。** 对每个邻机计算给定时间窗内的碰撞速度区域，再生成线性半平面约束，从最接近期望速度的可行点中选择命令。经典结论依赖邻居位置、速度和尺寸足够准确、相互配合且速度能够被执行；当存在加速度/转弯半径限制、通信失联或高度非合作行为时，需要专门扩展或保守降级。ORCA 并不是带全局任务最优证书的多机器人 MPC。

**当年为何重要。** 它把多智能体实时避让变成每个智能体都能计算的低维优化，便于扩展到大量个体。RVO2 库将该方法实现为可用于仿真与机器人开发的 C++ 工具。

**今天仍使用的思想。** 多机器人协作必须明确“共享空间责任”与速度可执行性。今天 WarpWeaver 从局部避碰进一步追求带协商的团队整体路径质量。ORCA 可以是分布式实时基线，但不能用它替代任务层通行顺序、拥堵解决和全局目标规划。

**后续发展与局限。** 现代方法引入加速度约束、非完整运动学、通信不确定性、风险概率与预测控制；经典 ORCA 的瞬时速度选择在狭窄死胡同中可能出现局部停滞。它的避碰保证也不覆盖未观测的真实障碍。

**源码与可复现性。** 可使用作者相关的 [RVO2 C++ 代码](https://github.com/snape/RVO2)，先在二维对向通道里测试 2、6、20 台机器人，记录最小间距、死锁、路径偏差和 CPU 耗时；再将选出的速度交给有加速度约束的底盘控制器，比较输入是否真实可执行。

**对当前工程的重新解读。** 多机器人系统至少分三层：全局通路分配、局部对邻机避让、底盘物理限制。将这些责任清楚分层，远比把所有机器人速度简单送给一个“神奇全局优化器”更便于调试和验证。

**原始资料：** [论文 DOI](https://doi.org/10.1007/978-3-642-19457-3_1) · [RVO2 实现](https://github.com/snape/RVO2) · [ORCA 原作者项目](https://gamma.cs.unc.edu/ORCA/)。

## 今日结论

今天最有工程价值的不是“更大的神经网络”，而是**每个模块只相信它真正拥有证据的部分**。

Sparse Topometric Graph 用局部几何加可通行结构抗跨会话变化；OASIS 用稳定锚点更新动态对象，而不把一次识别当成永远正确。WarpWeaver 通过多机协商改善团队路径，但 Deadline 之前的中间解仍需独立安全保护。MPBRS 用潜势奖励降低跨本体人工调参，却不越过真实动力学边界。

TerraTransfer++ 说明昂贵的视觉模仿可被高吞吐自博弈与轻量视觉适配部分替代；FocusVLA 说明多视角信息需要按动作阶段使用；CARE 说明云端模型应该在本地不可靠时再接管，而不是阻塞每一个控制周期。

Coding Agent 的过期指令实验则提醒：写在仓库里的说明未必比当前源码和独立测试更可靠。面对不一致，最有效的改进可能就是**一条明确的冲突规则**，而不是更多计划书、报告和证据文件。

本期核心结论：**让地图保存版本与证据、规划保存可行性与期限、Agent 保存真实行为契约。先验证信任边界，再讨论模型规模和并行数量。**

## 最值得深入研究或尝试复现的方向

1. **跨会话稀疏地图：** 在同一室内数据上比较点云全匹配、局部描述子和 Topometric 子图匹配；重点检查重复走廊中的误对应。
2. **OASIS 动态锚点：** 在已建立地图中移动工具，验证对象重定位、过期证据淘汰和实时局部障碍一致性。
3. **WarpWeaver 对 ORCA：** 用双机器人与六机器人共享通道比较总时间、P99 规划耗时、碰撞净空及中间方案可行性。
4. **MPBRS 统一 Reward：** 在两种以上人形本体保持相同潜势权重，仅替换关节映射和初始姿态，做收敛与性能消融。
5. **TerraTransfer++ 自博弈蒸馏：** 固定视觉主干和仿真场景，比较是否依赖真人示范、长尾冲突和闭环失效。
6. **FocusVLA 摄像头路由：** 记录腕部/全局视角权重随抓取、搬运和放置阶段的变化；注入遮挡并观察恢复。
7. **CARE 本地—云接管：** 先做 Shadow Mode，对网络超时、任务失败和历史动作过期设计显式状态机。
8. **过期 AGENTS.md/CLAUDE.md：** 选择真实冲突样例，在相同测试条件下比较有无“优先核对当前代码”的规则。
9. **AI Coding 工具链：** 在无害 Worktree 中验证 Codex Preset、Claude Code 符号链接审批以及 GitHub App 最小权限迁移。

## 参考资料

**arXiv 最新批次：** [Robotics](https://arxiv.org/list/cs.RO/new) · [Software Engineering](https://arxiv.org/list/cs.SE/new)。

**SLAM、空间记忆与协作：** [Sparse Topometric Graph](https://arxiv.org/abs/2610.31432) · [OASIS](https://arxiv.org/abs/2610.30589) · [WarpWeaver](https://arxiv.org/abs/2610.31540)。

**控制与具身模型：** [MPBRS](https://arxiv.org/abs/2610.30334) · [TerraTransfer++](https://arxiv.org/abs/2610.30319) · [FocusVLA](https://arxiv.org/abs/2610.31423) · [CARE](https://arxiv.org/abs/2610.30587)。

**AI Coding 研究与工具：** [Stale Instruction Files](https://arxiv.org/abs/2610.30571) · [实验证据仓库](https://github.com/WenJing95/stale-docs-data) · [Codex 0.164.0](https://github.com/openai/codex/releases/tag/rust-v0.164.0) · [Claude Code v2.1.310](https://github.com/anthropics/claude-code/releases/tag/v2.1.310) · [GitHub Enterprise Apps GA](https://github.blog/changelog/2026-10-23-enterprise-installations-for-github-apps-generally-available/)。

**经典论文：** [ORCA 2011](https://doi.org/10.1007/978-3-642-19457-3_1) · [RVO2](https://github.com/snape/RVO2)。
