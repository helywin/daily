---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-08"
date: 2026-09-08 09:00:00 +0800
description: "本期关注3DGS导航基准、AoI约束协同感知、采样规划理论边界、动态人机接触、零推理成本VLA语义脚手架、机器人奖励鲁棒性，以及AI Coding执行反馈与推理缓存复现性。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-08

## 摘要

截至本期检索时，arXiv Robotics 与 Software Engineering 最新公开批次均为 **2026-09-07**。Robotics 共 65 条，其中 32 条为 new submissions；Software Engineering 共 44 条，其中 30 条为 new submissions。严格最近 24 小时内，可完整核验、与本简报方向高度相关且尚未进入覆盖索引的高质量工作不足 5 条，因此按任务规范扩展到最近 7 天。今天入选的 8 条主动态 v1 均提交于 9 月 3–4 日 UTC，全部明确标为“时间回补”。

今天最值得从地图与导航系统角度看的工作是 **NavArena**。过去两年 3D Gaussian Splatting 很容易产出“看起来像数字孪生”的场景，但漂亮的新视角渲染并不等于机器人真的能在里面做闭环导航。NavArena 把冻结的 3DGS 转成导航基准：从 Gaussian density 与高度统计生成 occupancy costmap，从多视角开放词汇分割提升出语义目标，再使用同一环境做 RGB-D 渲染、碰撞/可达性查询和闭环策略评测。作者在 2,000 多个场景中生成 2,220 万条 expert trajectory。这类工具最有价值的地方，是把已有 3D 扫描资产转成可反复跑策略回归的导航资产，而不是再单独手工搭一套仿真场景。

协同感知方面，**Conductor** 把一个很现实的变量提升为系统一等约束：**Age of Information（AoI）**。路侧边缘节点可以融合多辆车和 RSU 的观测、预测未来轨迹，但如果结果送到车辆时已经过期，融合精度再高也没有意义。Conductor 通过 occlusion-aware selector 优先选真正补充 RSU 盲区的车辆，同时用 runtime controller 动态调节每周期融合多少辆车、预测多少条轨迹，使系统在最多 31 辆 CAV 的模拟中维持 AoI 上界。这一思想可以直接迁移到多机器人 SLAM、远端地图融合和云端 VLM：远程信息必须携带“多老了”，而不能只有“置信度多高”。

运动规划理论方面，**Achieving Asymptotic Near-Optimality Without δ-Similarity** 很值得认真读。大量 kinodynamic sampling planner 的近最优证明依赖“最终几乎必然采到接近最优轨迹的 δ-similar 片段”，但论文指出其中隐含了一个很容易被忽略的 retention assumption：采到以后这些片段还得真的被树保留下来。实际 pruning / sparsification 可能出现“crowding out”，让局部低代价路径把通往全局更优解的近似片段排挤掉。论文并不是否定渐近近最优，而是重新给出不依赖完整 δ-similar solution trajectory 的论证。这对工程实现非常重要：采样器、传播器和 cost 都没问题，也不代表节点保留策略不会破坏理论前提。

人机接触控制方面，**Dressing in Motion** 处理的是比静态穿衣更真实的问题：人在穿衣过程中会主动移动手臂，衣物又有复杂遮挡和柔性接触。作者从静态专家示范出发，用基于部分观测点云的 diffusion policy 学穿衣动作，再用 PDE diffusion 构造手臂轴向的 object-centric representation，并对连续观测中的运动相关区域做注册，近似估计手臂运动后实时调整轨迹。真实研究包含 9 名参与者、3 种衣物和 6 类手臂运动模式。这类系统提醒我们：辅助机器人不能把人当静态障碍；人的运动本身就是需要进入策略状态的动态变量。

VLA 侧，**Latent Semantic Scaffolding（LSS）** 提出一条很适合端侧机器人的路线：把“物理推理”放到训练期，而不是每次推理都生成 reasoning token。训练时用一个小 projection head，把 VLA action-token representation 对齐到物理推理 rationale 的文本 embedding；部署时 projection head 直接丢掉，因此基础策略结构和推理成本都不变。真正关键的消融是：按 manipulation phase 为每个动作 token 对齐局部 rationale 的 Dense LSS，比整段任务只对齐一个 pooled rationale 泛化更好，内部表示的 phase separability 约提高到两倍。这说明训练数据如果已经有接触阶段、操作阶段和因果说明，完全可以把它们当作“训练脚手架”，而不要求真机运行时继续支付大模型推理成本。

机器人奖励模型方面，**ROBORMBENCH** 暴露了一个非常危险的漏洞：同一条真实机器人轨迹，只把语义等价的任务指令换一种说法，VLM reward 就可能从“成功”翻成“失败”，或者给出明显不同的 progress score。基准包含 2,390 条真实机器人轨迹、ground-truth progress label 和 21,673 条经过验证的同义改写，覆盖词汇、句法以及 action-goal rewrite。作者发现这种不稳定性在开源和闭源 VLM 中都很普遍，而且模型变大、显式 reasoning 也不能可靠消除。若 VLM reward 被用于 RL 或自动评测，paraphrase invariance 应该成为正式的 metamorphic regression，而不是默认假设。

AI Coding 侧，本期两条工作共同指向“真实执行状态必须进入 Agent 基础设施”。**Dynamic Adaptation of the LLM Context for Generating Routines with Coupled Semantics** 研究文本描述无法静态决定正确性的程序：一个 routine 的正确含义要看另一个 routine 实际运行后发生什么。它让 validation agent 从 execution trace 抽取结构化诊断，再动态写入 generation context，同时用知识图谱维持语义约束、用 simulated annealing 避免候选搜索过早塌缩。在 8 个问题上，300 与 600 次 evaluation 预算下有 7 个优于 zero-shot、Reflexion 与 OpenEvolve。工程含义非常直接：Coding Agent 的上下文不应该只来自仓库检索，也应该来自“刚才实际执行出了什么问题”。

另一篇 **Same Request, Different Answer** 则把 serving infrastructure 本身拉进 Agent 可复现性问题。作者固定模型、seed、请求顺序与 batch size，只改变 prefix cache 与权重量化，80 个多轮工具调用 episode 中，打开 cache 后 16-bit 有 36.2% 的轨迹发生变化，4-bit 上升到 75.0%；关闭 cache 后 800 次重复执行没有出现 divergence。结果不能简单外推到所有引擎，但它足以说明：对长时 Coding Agent，`model + prompt + seed` 已经不够描述一次实验，cache 配置、量化格式乃至 cache state 都应该进入 provenance。

近期 GPT-6 Astra、Gemini 3.8 Flash、Claude Fable 5.1 等旗舰模型已经在前几期覆盖；截至本期检索，没有发现 9 月 7–8 日需要挤掉上述机器人 / 控制 / AI Coding 工作的新旗舰基础模型正式发布，因此不重复用模型新闻凑数。

## 1. NavArena：把 3DGS 从“漂亮重建”变成可闭环评测的导航资产

**时间回补：arXiv v1 提交于 2026-09-04。**（[论文](https://arxiv.org/abs/2609.04602)）

### 为什么重要

3D Gaussian Splatting 已经非常适合快速重建工厂、园区和室内现场，但固定 3DGS 本质上只回答：

```text
给定一个相机位姿
→ 能渲染出什么画面？
```

机器人导航还需要另外三类东西：

```text
这里能不能走？
哪里会碰撞？
哪些位置算有效目标？
```

如果每次都重新手工建 occupancy、语义目标和 episode，3DGS 与导航栈之间仍然存在很大的工程断层。NavArena 的目标就是自动补上这一层。

### 算法模块

整体结构可以理解为：

```text
Frozen 3DGS Reconstruction
          ↓
Egocentric RGB-D Rendering
          +
Gaussian Density / Height Statistics
          ↓
Occupancy Costmap
          +
Multi-view Open-Vocabulary Masks
          ↓
Semantic Goal Candidates
          ↓
Episode / Expert Trajectory Generation
          ↓
Unified Closed-loop Navigation Evaluation
```

作者不要求重新训练 3DGS，而是把已经存在的 Gaussian scene 解析成“可以被导航算法消费”的表示。公开摘要报告覆盖超过 2,000 个场景，并自动生成 **2,220 万条 expert trajectories**。

### 传感器与地图假设

这里最关键的假设是：Gaussian density、高度结构和渲染深度足以近似真实几何可达性。

这在常规室内表面上可能很好用，但对玻璃、薄结构、楼梯边缘、悬空物、窄门和动态物体，视觉重建质量与真实碰撞几何可能不是一回事。3DGS“看起来连续”甚至可能把几何空洞渲染得很漂亮。

因此 NavArena 更适合作为**导航策略回归与数据生成环境**，而不是直接把 derived costmap 当成安全认证地图。

### 实时性、鲁棒性与可复现性

它主要解决 benchmark construction，不是一个在线 20 Hz local planner，因此不应该用在线规划 FPS 衡量。

更值得测试的是：

```text
3DGS-derived collision vs 实际几何
可达区域 precision / recall
语义目标正确率
仿真策略 ranking 与真机 ranking 的相关性
```

论文摘要说明 benchmark-generation tools、evaluation protocols 与 derived assets 将公开；在正式资源完全发布前，可复现性仍应标为“公开计划明确，但需等待完整资产”。

### 工程风险

最大的风险是形成一种新的“simulator confidence illusion”：策略在高保真渲染里表现很好，看起来也非常真实，但失败来自 derived geometry 与真实世界不一致。

因此任何从 3DGS 自动生成的地图最好保存：

```text
geometry_source
support_density
uncertainty
last_real_validation
known_bad_regions
```

### 适合谁关注

3DGS 扫描、数字孪生、机器人交付回归、室内导航、Real-to-Sim 评测团队。

### 工程落地启发

如果已经有现场 3DGS / Gaussian map，可以先做一个 NavArena-lite：

```text
3DGS
→ 2D / 2.5D costmap
→ 随机生成 1,000 个 start-goal pair
→ 跑现有 Nav2 / local planner
→ 抽样真机验证失败区域
```

这样同一份扫描资产就能同时服务展示、回归和导航算法测试。

## 2. Conductor：协同感知的核心约束不是“融合多少”，而是“信息到达时还新不新”

**时间回补：arXiv v1 提交于 2026-09-03。**（[论文](https://arxiv.org/abs/2609.04364)）

### 为什么重要

多车 / 多机器人协同感知容易把目标写成“收集越多观测，世界模型越准确”。但远端融合天然存在：

```text
上行网络
→ 边缘计算
→ 轨迹预测
→ 下行网络
```

等结果回到机器人时，世界已经继续运动。一个 98% 准确、但 500 ms 前的动态目标位置，可能比 90% 准确、但只有 30 ms 的本地观测更危险。

Conductor 因此把 **Age of Information（AoI）** 直接设为运行时预算。

### 算法模块

```text
CAV / RSU Detections
        ↓
Fixed-anchor Edge World Model
        ↓
Occlusion-aware Vehicle Selector
        ↓
只优先接入真正补 RSU 盲区的 CAV
        ↓
Runtime Controller
        ↓
动态调节：
- 本周期融合多少辆车
- 预测多少条未来轨迹
        ↓
在 AoI deadline 内返回
```

这不是简单“边缘服务器算快一点”，而是允许系统主动减少输入量和预测负载，换取信息新鲜度。

### 传感器与系统假设

方法依赖不同车辆 / RSU 观测能被变换到共同 frame，也依赖网络与计算延迟能够被测量和在线调度。

真实部署还会遇到：

```text
packet loss
乱序
时钟偏差
带宽突降
edge node overload
```

因此 AoI 只是一条核心指标，并不能替代 time-sync 与 networking health。

### 实时性与结果

作者在 CAV simulation infrastructure 中评估最多 **31 辆 CAV**。联合 selector-controller 能在多种 traffic scenario 下满足设定的 AoI 安全上界，同时 fusion fidelity 接近 Oracle，并明显优于相同 AoI 约束下的随机 vehicle selector。

目前主要证据来自模拟，而不是城市道路真实大规模 CAV 网络，因此还不能把结果直接外推到蜂窝网络抖动和真实 RSU 部署。

### 鲁棒性与风险

边缘融合的最大风险是 stale data 被当成高质量 observation 使用。每个远端 observation 最好同时带：

```text
source_timestamp
arrival_timestamp
age
predicted_valid_until
source_pose_uncertainty
calibration_version
```

一旦 age 超过控制任务容忍上限，宁可丢弃，也不要让“高置信旧信息”污染 planner。

### 适合谁关注

多机器人协同地图、CAV、路侧感知、云端视觉 / VLM、远程多机任务系统。

### 工程落地启发

多机器人系统里建议把所有远端状态统一成：

```text
RemoteObservation<T> {
  value
  confidence
  source_time
  age
  deadline
}
```

不要只传一个 pose / detection + confidence。**新鲜度本身就是观测质量的一部分。**

## 3. Achieving Asymptotic Near-Optimality Without δ-Similarity：采到了好轨迹，不代表树会把它留下来

**时间回补：arXiv v1 提交于 2026-09-03；已提交 IEEE RA-L。**（[论文](https://arxiv.org/abs/2609.04464)）

### 为什么重要

很多 kinodynamic sampling planner 的证明逻辑可以粗略理解为：

```text
不断随机采样 + forward propagation
        ↓
最终几乎必然采到
接近 optimal trajectory 的片段
        ↓
逐步拼出 near-optimal solution
```

论文指出这里存在一个经常未被显式写出的条件：

> **这些接近最优轨迹的片段，采到以后还必须被 planner 的节点保留 / pruning 机制留下。**

实际稀疏树为了控制规模，会淘汰“看起来局部不够好”的节点。于是可能出现 **crowding out**：某条局部代价更低的路径占据区域后，让真正通往全局最优路径的 δ-similar segment 无法进入树。

### 关键理论结构

论文并不是简单说“原来的 planner 都错了”，而是区分：

```text
Sampling guarantee
≠
Retention guarantee
≠
最终 solution guarantee
```

作者构造了一个系统 / 环境例子，在那里通过归纳方式持续保留 δ-similar solution trajectory 是不可能的；随后又证明，只要把 crowding-out 情况正确纳入分析，仍可以得到 asymptotic near-optimality，而不必要求整条解始终由 δ-similar segment 组成。

### 动力学与规划假设

论文面向使用 forward dynamics propagation 的 kinodynamic sampling planning。它关注的是理论保证，不是一个新的实时局部 planner，因此没有“多少 Hz”的部署指标。

它最重要的工程接口反而是 planner 内部数据结构：

```text
node selection
pruning
witness / sparse representation
dominance rule
local cost
```

这些机制不只是性能优化，也可能改变理论性质。

### 鲁棒性、可复现性与风险

理论 counterexample 很有价值，但不能自动证明某个具体 OMPL planner 在你的机器人上一定会 crowd out。真正值得做的是构造 regression：记录哪些节点因为 pruning 被删、哪些区域长期由低成本节点“占坑”，以及最终解质量随样本数是否真的稳定逼近。

### 适合谁关注

无人机、车辆、欠驱动机器人、kinodynamic RRT / SST / forward-propagation planner，以及正在为 sampling planner 做 GPU / sparse-tree 优化的团队。

### 工程落地启发

以后改 planner 的 pruning rule 时，不应该只看：

```text
节点更少了吗？
规划更快了吗？
```

还应该看：

```text
长期 best cost 是否继续下降？
关键 homotopy 是否被过早消失？
被删节点是否具有独特可达后继？
```

**树的保留策略本身就是规划算法的一部分，而不是无害的内存优化。**

## 4. Dressing in Motion：辅助机器人必须把“人正在动”当作策略状态，而不是外部扰动

**时间回补：arXiv v1 提交于 2026-09-04。**（[论文](https://arxiv.org/abs/2609.04759)）

### 为什么重要

机器人辅助穿衣是一个典型的 contact-rich human-in-the-loop task。多数实验让人保持固定姿势，但真实用户会主动抬手、弯肘、调整肩部；衣物又会遮挡人体，并产生强柔性接触。

如果策略只根据当前一帧点云做动作，容易把人的主动运动当成 perception noise，导致机器人继续沿旧轨迹拉衣物。

### 算法模块

作者从**静态 expert demonstration** 学习基础穿衣动作，再增加对动态用户运动的表征：

```text
Partially Observed Point Cloud
          ↓
Diffusion Policy
          +
PDE-diffusion Object-centric Arm Representation
          ↓
Motion-relevant Region Sampling
          ↓
跨连续观测做 Region Registration
          ↓
近似 Arm Motion
          ↓
Reactive Trajectory Adaptation
```

PDE diffusion 的目的不是求机械臂动力学，而是把手臂的轴向几何组织成更稳定的 object-centric representation，减少局部遮挡造成的表示跳变。

### 传感器与动力学假设

方法依赖部分观测点云能够持续捕获足够的人体几何。衣物本身的非刚体动力学、摩擦以及拉扯力并没有因为 diffusion policy 自动消失。

公开摘要没有表明系统使用独立力觉作为主要闭环信号，因此真实辅助机器人仍应保留接触力、关节力矩、速度和人体安全空间的独立监控。

### 实时性与真实实验

作者在仿真和真人实验中验证，真实研究包含：

- 9 名参与者；
- 3 种 garment；
- 6 类 arm-motion pattern。

论文报告在 dressing progress、freedom of movement 与 user comfort 上优于基线，但摘要没有提供适合直接引用的统一控制频率或全部绝对数值，因此本期不人为补充。

### 鲁棒性与工程风险

human motion estimation 一旦错误，机器人可能“积极地追着错误运动补偿”。辅助类机器人应至少有：

```text
human-motion confidence
contact-force envelope
trajectory preemption
user stop / override
maximum relative velocity
```

生成策略只负责提出动作，不应独占最终安全权限。

### 适合谁关注

辅助穿衣、康复、护理机器人、人与机器人共享接触空间、柔性物体操作。

### 工程落地启发

对任何 human-in-the-loop manipulator，可以把目标接口从：

```text
HumanPose_t
```

升级成：

```text
HumanState {
  pose
  velocity
  confidence
  predicted_short_horizon_motion
}
```

“人在动”不应只通过下一帧误差被动体现，而应进入 planner / policy 的明确状态。

## 5. Latent Semantic Scaffolding：让 VLA 在训练时学“为什么”，部署时不再支付推理成本

**时间回补：arXiv v1 提交于 2026-09-04。**（[论文](https://arxiv.org/abs/2609.04893)）

### 为什么重要

给 VLA 增加 reasoning 通常有两种成本很高的办法：

```text
每个动作前生成 reasoning tokens
或
每一步 rollout future / world model
```

长任务中，这些额外推理会不断累积 latency。LSS 问了一个很实际的问题：

> 能不能只在训练阶段让动作表示学习物理推理，部署时把辅助模块整个扔掉？

### 算法模块

训练阶段增加一个小 projection head：

```text
VLA Action-token Representation
          ↓
Projection Head
          ↓
对齐 Text Embedding of Physical Rationale
```

训练结束后：

```text
Projection Head → 删除
Base VLA → 原样部署
```

因此 inference graph 不新增 reasoning module。

论文比较两种 granularity：

**Pooled LSS**：整条 episode 使用一个总 rationale。

**Dense LSS**：每个 manipulation phase 的 action token，只对齐自己阶段的 rationale。

Dense LSS 在 in-distribution 和 held-out transfer 上都更好，且表示探针显示 backbone 的 per-phase separability 约提升到两倍；Pooled 反而更容易对训练任务过拟合。

### 传感器与策略假设

LSS 不改变部署时的传感器要求，它改变的是 pretraining supervision。真正的成本转移到训练数据：你需要合理的 physical rationale / phase 描述。

如果 rationale 本身来自错误自动标注，模型也可能被稳定地推向错误语义。因此 rationale 应保留来源与置信度，而不是把 LLM 生成的解释直接当真值。

### 实时性、鲁棒性与可复现性

最大的实时性优势就是**零新增 inference module**。这对 Jetson / 双臂实时策略比“再挂一个在线 reasoning model”更容易落地。

当前摘要没有给出足够完整的官方代码 / checkpoint 入口，因此可复现性仍取决于后续资源公开情况。

### 工程风险

更可分的 latent 并不等于动作更安全。LSS 只能帮助表示保留 phase-level 物理语义，碰撞、接触力、关节限位和动作新鲜度仍需独立 runtime gate。

### 适合谁关注

端侧 VLA、π0 / diffusion / autoregressive action policy、机器人数据平台，以及希望利用 reasoning supervision 又不愿增加真机推理延迟的团队。

### 工程落地启发

机器人数据仓库可以开始额外保存：

```text
manipulation_phase
contact_state
object_relation
physical_rationale
```

这些信息不一定部署时使用，但可以成为训练期的“语义脚手架”。这是比单纯继续扩 action-demo 数量更便宜的一条 representation scaling 轴。

## 6. ROBORMBENCH：同一句任务换个说法，VLM Reward 不应该把同一轨迹从成功翻成失败

**时间回补：arXiv v1 提交于 2026-09-04。**（[论文](https://arxiv.org/abs/2609.05401)）

### 为什么重要

VLM 越来越常被拿来做：

```text
机器人任务自动打分
RL Reward
Preference Label
Checkpoint Ranking
Failure Detection
```

这些用途有一个最低要求：**语义等价的目标描述，应该对同一条 trajectory 给出一致评价。**

ROBORMBENCH 证明，当前许多 VLM 并没有满足这一点。

### Benchmark 结构

数据包括：

- **2,390 条真实机器人 trajectory**；
- ground-truth progress labels；
- **21,673 条经过验证的 paraphrase**；
- lexical、syntactic、action-goal rewrite 等不同改写类型。

只改变 instruction wording，不改变机器人行为本身，然后重新让 reward model 打分。

### 结果与鲁棒性

作者发现 paraphrase-induced instability 在开源和闭源 VLM 中都普遍存在，改写越大，问题通常越严重；简单扩大模型规模或要求显式 reasoning 也不能可靠解决。

更专门、使用 trajectory-grounded supervision 训练的 reward model 明显更稳定。

这里最危险的不是分数浮动几个百分点，而是**相同 trajectory 的 success / failure 判定发生翻转**。一旦这种 reward 被用于 RL，策略优化方向本身就可能被 prompt wording 改写。

### 传感器与假设

这是一项 reward-model evaluation，不直接提出新的机器人控制器。Ground-truth progress label 与 paraphrase verification 本身是 benchmark 的关键资产。

不同真实生产任务的语义可能更复杂，因此 21,673 条 paraphrase 仍不能证明覆盖所有 instruction variation；它提供的是一种应该进入测试体系的方法论。

### 工程风险

不要把 VLM reward 当成“自然语言版本的确定性传感器”。至少要同时监控：

```text
prompt sensitivity
paraphrase consistency
trajectory-grounded score
human calibration subset
```

### 适合谁关注

VLA RL、机器人自动评测、Preference Learning、VLM-as-a-Judge、无人值守 checkpoint 回归。

### 工程落地启发

给 reward / judge 增加**metamorphic test**：

```text
同一条 trajectory
× 10–20 条语义等价 instruction
        ↓
检查 score variance
检查 success-label flip rate
```

如果模型连这个测试都过不了，就不应该让它单独决定策略上线或 RL reward。

## 7. Dynamic Context Adaptation：Coding Agent 的上下文应该由真实执行结果不断改写

**时间回补：arXiv v1 提交于 2026-09-03；ICANN 2026 接收。**（[论文](https://arxiv.org/abs/2609.04570)）

### 突破性工程价值

普通 Coding Agent 假设“正确做法可以从需求 + 仓库文本中读出来”。但有一类问题只有运行以后才能知道正确与否：

```text
Routine A 的输出
决定 Routine B 应该怎样行为
而 B 的结果又反过来约束 A
```

作者称这种问题为 **static binding** 的失败：文本上下文无法预先完全解析 execution-dependent coupling。

### 算法模块

```text
Problem Description
      ↓
Knowledge Graph
→ 提供稳定 semantic constraints

Generated Candidates
      ↓
Real Execution / Validation
      ↓
Validation Agent
      ↓
Structured Diagnostics
      ↓
Dynamic Context Update
      ↓
Generation Agent
      ↓
Multiple Candidates
      ↓
Simulated Annealing Selection
```

其中 structured execution diagnostics 类似“梯度方向”：它不是只告诉模型 pass / fail，而是说明哪种 joint behavior 出了问题。

### 结果

论文在 8 个问题上评估。在 **300 与 600 次 evaluation budget** 下，方法有 **7/8 个问题**优于 zero-shot、Reflexion 与 OpenEvolve，统计结果报告 `p < 0.01`；在主要 cross-coupled optimization 问题上，1000 次 evaluation 时仍取得最佳结果。消融显示 structured execution feedback 是主要收益来源。

### 是否适合真实研发流程

非常适合数值算法、优化器、编译 / 性能问题、协议实现和任何“单元函数看起来对，但组合起来错”的任务。

真实工程里，validation agent 最好不要输出任意自然语言长文，而应输出结构化 artifact：

```text
failing_case
observed_output
expected_invariant
coupled_symbols
runtime_metric
repo_sha
```

这样下一轮 context 是可审计的，不是不断增长的聊天摘要。

### 权限、安全与可验证性风险

执行反馈越强，越需要 sandbox。Agent 为了“看运行结果”不应该自动获得生产数据库、外网或部署权限。

另外 validator 自己也可能诊断错，所以最终 acceptance 仍应由确定性测试 / benchmark 决定，而不是 generation agent 与 validation agent 相互说服。

### 工程落地启发

Coding Agent 的上下文建议分成：

```text
Static Context
→ 需求、接口、架构约束

Dynamic Context
→ 最新测试、profiling、trace、失败案例

Verified State
→ CI / compiler / benchmark 的确定性结果
```

这比把所有历史终端输出原样塞进 1M context 更容易长期扩展。

## 8. Same Request, Different Answer：Prefix Cache 与低比特量化会进入 Agent 的复现性边界

**时间回补：arXiv v1 提交于 2026-09-04；已提交 IEEE Access。**（[论文](https://arxiv.org/abs/2609.04748)）

### 突破性工程价值

我们通常认为一次 LLM 实验只要固定：

```text
model
prompt
seed
decoding parameters
```

就足以复现。

这篇工作显示，在长时 Agent serving 中，**prefix cache state 也可能成为隐藏输入**，而低比特量化会放大这种差异。

### 实验结构

作者构造 80 个 multi-turn agentic tool-use episode，在两个 serving engine、四种 weight format 上重复运行，并固定：

- 模型；
- decoding parameters；
- seed；
- request order；
- serial batch size = 1。

唯一系统性改变的是 cache 开 / 关及相关 serving 状态。

### 结果

打开 prefix cache 后：

```text
16-bit：36.2% episode 的 Agent trajectory 发生变化
4-bit： 75.0% episode 的 Agent trajectory 发生变化
```

关闭 cache 后，重复执行在 **0 / 800 episode** 中出现 divergence，也就是全部 bit-identical；作者据此把其他 nondeterminism 的影响上界限制在约 0.5%。

论文还显示，改变一个 server-level prompt-cache setting 可以让 run-to-run divergence 相差 **37.5 个百分点**。当 cache state 被恢复后，cached path 与 recompute path 又各自能够稳定复现，说明问题不是“模型随机坏掉”，而是 cache state 实际进入了计算路径。

### 是否适合真实研发流程

这个结果尤其适合：

- Coding Agent benchmark；
- 长时 tool-use regression；
- 本地 vLLM / SGLang 类部署；
- 4-bit / 8-bit 端侧模型；
- A/B 模型路由。

它不意味着所有 prefix cache 实现都会有相同比例的 divergence，论文只测试了有限引擎与 workload，因此不能过度外推。

### 权限、安全与可验证性风险

如果 Agent 运行结果影响部署、代码合并或安全判断，复现日志至少应保存：

```text
model snapshot
quantization format
serving engine version
cache enabled / disabled
cache configuration
cache provenance / reset policy
seed
request order
```

真正高风险 verifier 甚至可以选择关闭 cache，换取更清晰的复现边界。

### 工程落地启发

以后做 Agent regression 不要只写：

```text
GPT-X / temperature=0 / seed=42
```

而应该保存一个 **Serving Provenance Manifest**。模型能力越来越强以后，推理引擎的“透明优化”也会变成软件依赖的一部分。

## 经典论文回顾

### Stable Sparse-RRT / SST：没有两点边值求解器，也能做具有渐近性质的 Kinodynamic Planning

Yanbo Li、Zakary Littlefield 与 Kostas E. Bekris 的 **Asymptotically Optimal Sampling-based Kinodynamic Planning** 最早于 2014 年公开，正式工作发表于 **IJRR 2016**。论文提出 Stable Sparse-RRT（SST）与 SST*：SST 在适当条件下具有 asymptotic near-optimality，SST* 进一步得到 asymptotic optimality，同时只保留稀疏状态样本。([论文](https://arxiv.org/abs/1407.2896) · [DOI](https://doi.org/10.1177/0278364915614386) · [OMPL SST](https://ompl.kavrakilab.org/core/classompl_1_1control_1_1SST.html))

### 核心问题

RRT* 一类几何规划器可以依赖“从状态 A 精确连接到状态 B”的 steering / local connection。

对真实动力学系统：

```text
quadrotor
car + trailer
underactuated robot
high-dimensional dynamics
```

两点边界值问题往往没有便宜、稳定的求解器。

但 forward simulation 很容易：

```text
给当前 state
+ 一段 control
→ 得到 next state
```

SST 解决的核心问题就是：**只依赖随机 control propagation，不要求 BVP solver，能否仍然获得有理论保证的高质量解？**

### 算法模块与关键数学思想

SST 属于 control-based incremental tree planner：

```text
State / Control Sampling
        ↓
Forward Propagation
        ↓
Select promising local node
        ↓
Sparse representation / witness logic
        ↓
只保留有竞争力的 trajectory node
        ↓
持续改善 best solution
```

关键并不是“采更多点”，而是同时解决两个矛盾：

1. 树必须足够丰富，不能把未来可能通往优解的状态全删掉；
2. 树又不能像普通随机传播那样无限密集，否则最近邻和传播成本会不断膨胀。

SST 用稀疏化与 dominance / witness 思想控制树规模；SST* 再通过逐步收紧相关参数恢复渐近最优性质。

### 动力学假设

它要求可以进行 forward state propagation，并满足论文理论中的动力学、cost 与可达性条件。

不需要 steering function 是它最大的实用价值，但这并不代表所有控制系统都天然满足理论假设。接触切换、强不连续动力学和错误的数值积分都会影响实际行为。

### 当年为什么重要

它给 kinodynamic planning 一个非常清楚的答案：

> **没有 two-point boundary-value solver，并不意味着只能接受“没有最优性讨论的随机 rollout”。**

这也是为什么 OMPL 至今仍提供 `control::SST`：对于只能 forward propagate dynamics 的系统，它是一条非常实用的基准路线。

### 今天仍然在使用的思想

今天大量 GPU forward planner、motion primitive tree、sampling MPC 与 learning-guided planner 都延续同一个结构：

```text
结构化 / 随机 control proposal
        ↓
Forward Dynamics
        ↓
Cost / feasibility
        ↓
保留少量真正有价值的 state
```

尤其对无人机和车辆，真正决定计算效率的往往不是“采样次数”本身，而是**哪些历史 rollout 值得留下继续展开**。

### 已被后续扩展和重新审视的部分

现代系统已经加入：

- learned control proposal；
- GPU batch propagation；
- differential-flat command library；
- barrier / reachability safety；
- dynamic obstacle；
- model predictive replanning。

而今天主动态中的《Achieving Asymptotic Near-Optimality Without δ-Similarity》又提醒了一个关键理论边界：采样到接近最优路径的片段，不等于 pruning 后这些片段还存在。换句话说，SST 类算法最值得重新审视的恰恰是**sparsification / retention logic**，而不能只引用“asymptotically near-optimal”这几个字。

### 公开代码与可复现性

OMPL 仍提供 SST 的标准 control planner 实现，适合用 Dubins-like、车辆、无人机简化模型做基准。经典论文、DOI 和 OMPL 文档都可以直接获取。

### 对当前工程项目的重新解读

如果已经拥有无人机 / 轮式机器人动力学 rollout，可以做一个非常实用的三层 planner：

```text
有限控制 / Learned Proposal
          ↓
Forward Dynamics Batch
          ↓
SST-style Sparse Retention
          ↓
短时可执行 trajectory
```

真正需要重点调试的不只是 propagation dt 和 sampling distribution，还应记录：

```text
node 被谁淘汰
为什么淘汰
当前区域 witness 是谁
被删节点的未来可达性是否独特
best-cost 随时间是否继续改善
```

今天的新理论工作与 SST 放在一起看，最重要的工程结论是：

> **Sampling planner 的“内存管理规则”本身会决定你最终还能不能找到好路径。**

## 今日结论

今天的几项工作表面上跨度很大，但共同指向一个非常工程化的趋势：**系统质量越来越取决于那些过去被视作“附属实现细节”的中间状态。**

NavArena 说明 3DGS 是否能进入导航，不取决于渲染有多漂亮，而取决于能否显式产生 traversability、goal 与闭环 protocol；Conductor 说明远程世界模型不能只讨论 accuracy，还必须显式维护 AoI；新的 sampling-planning 理论则说明即使采样正确，retention / pruning 仍可能改变长期性质。

机器人学习同样在发生这种转变。Dressing in Motion 把人的运动状态显式纳入策略；LSS 把 manipulation phase 与 physical rationale 注入训练表示；ROBORMBENCH 则把“指令换个说法是否仍给相同 reward”升级成可量化的系统属性。VLA 产品化正在从“多模态输入 + 大模型输出动作”走向更明确的**状态、阶段、证据与一致性管理**。

AI Coding 侧更加直接：Dynamic Context Adaptation 说明真实 execution trace 应当持续更新 Agent context；cache-divergence 工作则说明 serving engine 自身也会改变长期 Agent 轨迹。以后一个可复现 Coding Agent 实验的最小描述，很可能需要同时包含：

```text
repo revision
requirements version
model snapshot
serving engine
quantization
cache state
runtime evidence
validator result
```

模型上下文变得更长，并不会让这些工程状态消失。

## 最值得深入研究或尝试复现的方向

1. **NavArena-lite：把现有 3DGS 扫描变成导航回归环境。** 从 Gaussian density / depth 提取 2D 或 2.5D costmap，随机生成 1,000 个 start-goal episode，用现有 Nav2 / local planner 跑批量回归，再抽样真机验证 costmap 的 false-free / false-occupied 区域。

2. **SST / Forward Planner 的 crowding-out 回归。** 在 OMPL SST 或自研 kinodynamic tree 中记录 witness、pruned node、best-cost 曲线，专门构造“局部低代价但全局错误”的场景，比较不同 pruning radius / retention rule 是否让潜在好 homotopy 永久消失。

3. **VLA 的 Paraphrase + Latent Scaffold A/B。** 给现有 reward / VLM judge 建 10–20 条语义等价 instruction 的 metamorphic test；训练侧增加 phase-level rationale / contact-state 辅助监督，验证能否在不增加部署推理成本的情况下同时提高泛化和 reward consistency。

4. **Coding Agent Reproducibility Matrix。** 固定一批仓库任务，组合测试 `16-bit / 8-bit / 4-bit × cache on/off × engine snapshot`，保存完整 Serving Provenance Manifest，统计最终 patch、tool trajectory 与 validator result 的 divergence，而不只比较文本回答。

## 参考资料

- [NavArena: Automated Construction of Goal-Oriented Navigation Benchmarks from 3D Gaussian Splatting Reconstructions](https://arxiv.org/abs/2609.04602)
- [Scalable Edge-assisted Fusion and Path Prediction for Connected Autonomous Vehicles / Conductor](https://arxiv.org/abs/2609.04364)
- [Achieving Asymptotic Near-Optimality Without δ-Similarity](https://arxiv.org/abs/2609.04464)
- [Dressing in Motion: A Human Motion-Aware Diffusion Policy for Robot-Assisted Dressing](https://arxiv.org/abs/2609.04759)
- [Reasoning Without Inference Cost: Latent Semantic Scaffolding for Robot VLA Policies](https://arxiv.org/abs/2609.04893)
- [Same Trajectory, Contradictory Rewards (ROBORMBENCH): Paraphrase Fragility in Vision Language Reward Models](https://arxiv.org/abs/2609.05401)
- [Dynamic Adaptation of the LLM Context for Generating Routines with Coupled Semantics](https://arxiv.org/abs/2609.04570)
- [Same Request, Different Answer: Quantization Amplifies Cache-Induced Divergence in LLM Serving](https://arxiv.org/abs/2609.04748)
- [Asymptotically Optimal Sampling-based Kinodynamic Planning / SST](https://arxiv.org/abs/1407.2896)
- [SST in OMPL](https://ompl.kavrakilab.org/core/classompl_1_1control_1_1SST.html)
