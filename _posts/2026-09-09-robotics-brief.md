---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-09"
date: 2026-09-09 09:00:00 +0800
description: "从水下 BEV 占据、拥挤人群导航与端侧动力学加速，到 VLA 故障恢复、网络触觉控制与 AI Coding 证据化验证，聚焦可部署机器人系统。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-09

## 摘要

截至 2026-09-09 09:00（Asia/Shanghai），arXiv Robotics 最新公开批次仍是 2026-09-07，共 65 条，其中 32 条为 new submissions；Software Engineering 同日共 44 条，其中 30 条为 new submissions。严格最近 24 小时内，没有足够 5 条同时满足“高质量、未重复、可完整核验”的机器人 / SLAM / 控制新工作，因此本期按任务规范扩展至最近 7 天。本期论文类主动态均于 9 月 3–4 日 UTC 首次提交，全部明确标记为“时间回补”。（[arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new)，[arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)）

今天定位与环境表示侧最值得看的工作是 **AquaBEV**。它把昂贵 3D imaging sonar 从“部署必需传感器”降成“训练期几何教师”：训练时使用 RGB 与 3D sonar 配对数据学习水下局部 BEV occupancy，部署时只需要单目 RGB。网络先把视觉特征映射到 calibration-free polar representation，再沿 range 方向做 causal decoding，最后回到 Cartesian BEV。统一 benchmark 下达到 31.4 Visible IoU / 38.6 Observed IoU，相对最强 transferred baseline 分别提高 4.0% / 4.3%。这条路线的工程价值并不局限于水下机器人：昂贵传感器完全可以只负责“教会便宜传感器理解几何”，而不必永远挂在量产设备上。（[论文](https://arxiv.org/abs/2609.04411)）

控制与导航侧，本期两项工作分别处理“人群交互不确定性”和“规划器自己如何制造压力测试”。**H2INT** 不再假设所有行人对机器人具有统一避让意愿，而让 pedestrian responsiveness 真实影响仿真动态，却不作为策略输入；策略必须从机器人中心的相对位置历史中自己推断人群是否会让路。两阶段 gated Transformer 先建模 human-human，再建模 human-robot interaction，recurrent policy 负责时间演化，并通过逐步降低 responsiveness 的课程增加难度；论文还给出了稀疏观测下的真实机器人部署。（[论文](https://arxiv.org/abs/2609.05300)）

**One Diffusion Model, Two Roles** 则把同一个 diffusion traffic prior 同时用作 ego motion planner 与 safety-critical scenario generator。规划侧使用 SSDS diffusion-transformer 和 training-free 的 DAPSE energy guidance；测试侧通过 inference-time guidance 主动生成 aggressive cut-in、lead braking 等长尾交互。很重要的负结果是：SSDS 在标准 nuPlan 闭环上名义性能更强，但在生成的高风险场景中退化反而更明显。这直接提醒机器人团队：**benchmark 排名高，不等于 robustness 高；生成式规划器最有价值的第二用途可能是给自己制造“难题”。**（[论文](https://arxiv.org/abs/2609.04921)）

端侧控制计算方面，**APEX-RBD** 关注的是一个通常隐藏在算法论文下面的瓶颈：高频刚体动力学在 FPGA / ASIC / 边缘设备上到底需要多少位宽。它没有对所有变量统一量化，而是根据不同状态变量和中间量对轨迹误差的敏感度进行 physics-driven grouping 与搜索空间裁剪，再用 prior-informed surrogate 预测完整闭环仿真的 trajectory error。相对 uniform-precision baseline，作者报告最高 1.9× area reduction 与 1.8× power savings。对于未来 500–2000 Hz WBC、torque MPC 和大自由度人形，这类“动力学计算本身的混合精度设计”会越来越像控制栈的一部分，而不只是芯片工程。（[论文](https://arxiv.org/abs/2609.05161)）

远程机器人与人机协作方面，**HaptiNet** 把网络延迟直接当作控制系统的一等状态。系统用低惯量、大行程、高力反馈的终端建立远距离双向触觉耦合，并用 imitation-learning-based delay compensator 抵消跨网延迟。研究覆盖 284 名健康参与者与 111 名神经系统受损患者，并测试约 4,000 km 的三条跨城链路。这里最值得机器人团队迁移的不是某个康复结论，而是体系结构：当控制闭环跨网络时，`latency / jitter / age / predicted remote state` 必须和 pose、force 一样被显式建模，而不能把网络当作透明管道。（[论文](https://arxiv.org/abs/2609.04799)）

VLA 评测侧，**LIBERO-RECOVER** 很可能比继续刷接近 100% 的 LIBERO success rate 更有产品价值。它从先进 embodied model 的真实执行失败中构建 1,000+ recovery scenario，并把恢复难度分为 Action Retry、Action Adaptation、Object State Recovery、Environmental Recovery 四层，同时评测空间理解、对象结构、交互理解和拓扑推理。它把问题从“机器人会不会一次做对”改成了“做错以后是否知道世界哪里变了、该怎样回到可继续状态”。（[论文](https://arxiv.org/abs/2609.05178)，[项目页](https://liulin815.github.io/LIBERO-Recovery/)）

AI Coding 侧，OpenAI 9 月 6 日发布的内部研究数据值得单独看，但更应该把它当作**供应商内部测量**而不是独立因果实验。OpenAI 报告其研究组织到 8 月中旬已使用约 3.1 个 agent-workday / 1 个 human workday；中位研究员按 API 等价价格每天使用超过 600 美元推理，90 分位超过 7,000 美元。与此同时，过去 6 个月里超过一半成功的 4–8 小时任务仍包含至少一次人工干预，高层 planning 仍只占 agent token 很小部分。OpenAI 自己也明确指出实验数量增长和 Codex 采用相关，但同期可用 compute 也显著增加，因此不能把所有速度提升都归因给 Agent。（[OpenAI 官方研究](https://openai.com/index/research-acceleration-view-inside-openai/)）

最后，**Better Understanding, Better Fixes?** 给 Coding Agent 的 verifier 泼了一盆很有必要的冷水：在 832 个 Defects4J bug 上，三个代表性 LLM 只有 21.0%–55.9% 的生成补丁能通过开发者测试；对 812 个 sampled repair 的人工分析中，72.7% 存在 repair hallucination，而且其中包含“所有现有测试都通过”的补丁。最主要问题是错误 causal localization（45.9%）和错误 repair strategy（18.5%）。这意味着“测试绿了”仍可能只是偶然绕过症状，真正生产级 Coding Agent 需要把触发测试、覆盖路径、因果定位、补丁与验证证据一起保存，而不是只保留最终 diff。（[论文](https://arxiv.org/abs/2609.04909)）

近期主流旗舰模型方面，本轮重新检查官方发布入口后，没有发现 9 月 7–9 日需要替换上述条目的新旗舰正式发布；GPT-6 Astra、Gemini 3.8 Flash、Claude Fable 5.1 已在此前简报覆盖，因此本期不重复展开。

## 1. AquaBEV：用昂贵 Sonar 教会便宜单目相机理解水下可通行空间

**时间回补：arXiv v1 提交于 2026-09-03 19:22 UTC。**（[论文](https://arxiv.org/abs/2609.04411)）

### 为什么重要

水下机器人真正用于导航的不是“这张 RGB 图像长得像什么”，而是机器人周围哪里是自由空间、哪里可能有结构物或障碍。问题在于水下 RGB 的几何线索远比陆地弱：散射、色偏、浑浊、照度变化和低纹理都会让 monocular depth 不稳定；3D imaging sonar 几何更可靠，却价格、体积、功耗和数据处理成本都更高。

AquaBEV 的系统分工很值得借鉴：

```text
训练阶段：RGB + 3D Sonar
          ↓
      学几何监督
          ↓
部署阶段：RGB only
          ↓
    Local BEV Occupancy
```

昂贵传感器被定位为 **teacher sensor**，而不是永久 BOM。

### 算法模块

整体链路可以理解为：

```text
Monocular RGB
     ↓
Visual Features
     ↓
Calibration-Free Polar Representation
     ↓
Causal Range Decoding
     ↓
Cartesian BEV Reconstruction
     ↓
Free / Occupied Space
```

这里 `polar → range causal decoding → Cartesian` 的设计很符合 sonar / 水下几何的物理结构：同一视线方向上，近处结构会影响对更远处空间的解释，因此沿 range 维度按顺序建模，比把 BEV 当成普通二维语义分割更合理。

### 传感器假设

部署期只需要单目 RGB，但训练期必须有与相机相对稳定配准的 3D imaging sonar。论文所谓 calibration-free polar representation 并不意味着整套数据采集完全不需要时空同步；如果 RGB 与 sonar 在运动状态下存在较大 timestamp 偏差，teacher geometry 本身就会污染监督。

另外，单目部署最终仍受 appearance domain shift 影响：换水域、浑浊度、人工照明或摄像机 ISP 后，网络不会因为训练时见过 sonar 就自动获得真实声学几何。

### 实时性与结果

统一 underwater occupancy benchmark 中：

```text
Visible IoU   31.4
Observed IoU  38.6
```

相对最强 transferred baseline 的相对提升分别为 4.0% 和 4.3%。论文当前摘要没有提供可安全外推到 Jetson / ARM 平台的统一端侧 FPS，因此工程评估时应该重新测 `camera→BEV` P50/P95 latency、显存和功耗，而不是用训练服务器结果推断部署性能。

### 鲁棒性、可复现性与工程风险

目前 arXiv 页面没有稳定公开代码入口，可复现性暂评中等偏低。真正部署还需要保留传统 sonar / altimeter / collision envelope 做安全兜底，不能把 monocular occupancy 当作几何证书。

建议额外记录：

```text
water_condition
visibility_range
camera_exposure
occupancy_confidence
unknown_ratio
last_geometric_teacher_check
```

### 适合谁关注

AUV / ROV、水下巡检、船体 / 水池检查，以及任何“训练时可以挂昂贵传感器、量产时必须减 BOM”的机器人团队。

### 工程落地启发

这条思路可以直接迁移到陆地机器人：

```text
训练车辆：MID360 + Stereo / Depth / RTK
                 ↓
           Teacher Geometry
                 ↓
量产设备：单目 / 低线数 LiDAR
```

不要只问“便宜传感器能不能独立做到同样精度”，还可以问“昂贵传感器能否只存在于数据采集车上”。

## 2. H2INT：在人群里导航，机器人必须推断“这个人到底会不会让路”

**时间回补：arXiv v1 提交于 2026-09-04 15:53 UTC。**（[论文](https://arxiv.org/abs/2609.05300)）

### 为什么重要

大多数 social navigation 仿真都有一个不太真实的默认设定：行人要么完全不理机器人，要么所有人都以近似同样程度响应机器人。

现实人群却是混合的：

```text
有人主动让路
有人直到很近才反应
有人边看手机几乎不反应
有人跟随群体一起变向
```

如果 planner 只预测“人在没有机器人时怎么走”，就会漏掉 human-robot interaction；如果又把所有人设成同一种 reciprocity，策略会在真实世界形成错误安全边界。

### 算法模块

H2INT 让 responsiveness 真正影响 pedestrian dynamics，但故意**不把 responsiveness label 给策略**。策略只能从交互历史反推。

```text
Robot-centered Relative Positions
             ↓
Human-Human Gated Transformer
             ↓
Human-Robot Gated Transformer
             ↓
Recurrent Policy
             ↓
Navigation Action
```

训练 curriculum 会逐渐降低行人的响应程度，让机器人从“大家都会让”逐步过渡到“有人完全不让”。

### 传感器与动力学假设

策略依赖机器人中心的相对位置观测，因此真实部署还需要稳定的人体检测 / 跟踪与 ego-motion compensation。论文展示了 sparse observation 的真机部署，但在极度遮挡、人群身份频繁交换或检测 ID switch 时，recurrent state 仍可能把错误历史绑定到错误的人。

H2INT 处理的是交互不确定性，不是形式安全认证。紧急制动距离、机器人 footprint、最大相对速度等仍应由独立 safety layer 管理。

### 实时性、鲁棒性与可复现性

论文报告在不同 crowd density、不同 responsiveness 分布和结构不同的人流布局上均有更好的安全性与鲁棒性，并验证了无重新训练的 layout transfer；还进行了真实机器人稀疏观测部署。摘要没有给出可以跨硬件直接比较的统一 Hz，因此部署时要单独测 detector + tracker + policy 的端到端 wall-clock latency。

当前未见稳定公开代码入口，可复现性暂评中等偏低。

### 适合谁关注

商场 / 医院 / 车站服务机器人、园区配送、人机共融巡检，以及在动态人群中运行的轮式和腿式机器人。

### 工程落地启发

人群 tracker 的每个目标不应该只有：

```text
position
velocity
```

可以增加一个长期在线估计的 interaction state：

```text
PedestrianState {
  pose
  velocity
  track_confidence
  responsiveness_belief
  last_robot_reaction
}
```

planner 可以根据这个 belief 调整 passing distance，而不是把所有行人用同一个社交力模型处理。

## 3. APEX-RBD：机器人控制器的下一轮优化，可能从“算法复杂度”进入“每个变量到底需要多少 bit”

**时间回补：arXiv v1 提交于 2026-09-04 14:02 UTC。**（[论文](https://arxiv.org/abs/2609.05161)）

### 为什么重要

高自由度机器人里，Rigid Body Dynamics 是很多实时控制模块的共同底座：

```text
Inverse Dynamics
Forward Dynamics
Mass Matrix
Coriolis / Gravity
Jacobian-related computations
```

桌面 CPU 上这些计算往往还能接受，但当人形机器人同时运行 WBC、MPC、状态估计、视觉和 VLA，而且控制频率要求 500–2000 Hz 时，功耗与 worst-case latency 会迅速变成硬约束。

统一使用 FP32 / FP16 看似简单，却忽略了一个事实：不同物理量对最终 trajectory error 的敏感度完全不同。

### 算法模块

APEX-RBD 把 mixed precision design 变成自动搜索：

```text
RBD Variables / Intermediate Values
             ↓
Physics-driven Grouping
             ↓
Sensitivity Analysis
             ↓
Search-space Pruning
             ↓
Prior-informed Surrogate
预测 trajectory error
             ↓
Hybrid Optimizer
             ↓
满足 Accuracy / Performance 约束下
最小 Area / Power
```

最关键的一步是 surrogate：如果每一个 bit-width 组合都必须跑完整闭环 simulation，搜索几乎不可行；因此作者用少量真实评估训练一个 trajectory-error predictor，把大部分配置先在代理模型上筛掉。

### 动力学与硬件假设

它优化的是给定 RBD 运算图和硬件 accelerator 结构下的数值精度，不会自动解决动力学模型本身的误差。即使 mass matrix 算到 32 位完全准确，错误的 link inertia、gear friction、payload 仍然会让控制预测失真。

另外混合精度安全性必须看**闭环轨迹误差**，不能只看每个 kernel 的平均数值误差；少数极端姿态或接近奇异位形时的误差可能比平均指标重要得多。

### 结果与实时性

相对 uniform-precision baseline，作者报告跨多个机器人平台：

```text
最高 1.9× area reduction
最高 1.8× power savings
```

论文目前强调 accelerator design-space exploration，并没有给出“一款通用芯片在所有机器人上固定达到多少 Hz”的承诺。

### 可复现性与工程风险

当前 arXiv 页面没有稳定官方代码 / RTL 入口，因此复现性暂评中等偏低。

真正产品化时建议验证：

```text
nominal trajectory error
worst-case pose error
near-singularity error
contact transition error
controller stability margin
thermal / power limit
```

### 适合谁关注

人形 WBC、机械臂 torque control、FPGA / ASIC 机器人加速器、Jetson 边缘控制器，以及需要在低功耗设备上做高频动力学的团队。

### 工程落地启发

即使不做专用芯片，也可以先在 CPU/GPU 软件栈做同样的 sensitivity profile：哪些矩阵必须 FP32，哪些中间量可以 FP16/BF16，哪些 lookup / geometry 甚至可以更低精度。未来机器人实时栈的性能优化可能越来越像：

> **控制理论决定什么误差能容忍，硬件编译器决定算力应该花在哪里。**

## 4. One Diffusion Model, Two Roles：规划模型最好的安全测试者，可能就是它自己

**时间回补：arXiv v1 提交于 2026-09-04 09:22 UTC；ECCV 2026 Workshop 接收。**（[论文](https://arxiv.org/abs/2609.04921)）

### 为什么重要

自动驾驶 / 移动机器人 diffusion planner 最大优势是能表示多模态未来：在同一交通场景里，减速、变道、等待都可能合理。

但这类模型通常只承担一个角色：生成 ego trajectory。论文提出一个更有价值的开发闭环：同一个 traffic diffusion prior 既能规划，也能在测试时故意把其他 actor 引导成危险但仍真实的行为。

### 算法模块

规划侧：

```text
Scene Context
     ↓
SSDS Diffusion-Transformer
     ↓
Joint Attention
     ↓
Trajectory Distribution
     ↓
DAPSE Energy Guidance
     ↓
Ego Plan
```

DAPSE（Decoupled Annealing Posterior Sampling with Energy）允许部署期直接加入任意 energy function，而且在 clean-sample level 注入，不需要额外训练一个 guidance network。

压力测试侧则复用同一个 diffusion prior：

```text
Traffic Prior
   +
Safety-critical Energy
   ↓
Aggressive Cut-in
Lead Braking
Combined Longitudinal/Lateral Interaction
```

### 动力学与场景假设

方法基于 learned traffic distribution，所谓“危险但真实”仍受训练数据支持范围约束。模型可能生成统计上合理、但动力学边界或法规上并不合理的场景，因此 scenario generator 最终还需要独立的 kinematic / collision / rule checker。

它在 nuPlan closed-loop 中验证，不应直接等价为工厂 AGV 或无人机动力学可复用；真正可以迁移的是**同一生成模型同时做 proposal 和 adversarial test generation**的开发方法。

### 结果与最有价值的负结论

生成的 safety-critical scenario 能暴露标准 benchmark 隐藏的 planner failure。尤其值得注意：SSDS planner 名义 benchmark 表现更强，但在这些困难场景里退化更大。

这说明上线 Gate 不应只比较：

```text
Average Success / Average Cost
```

还应该比较：

```text
Nominal → Stress 的性能下降幅度
```

### 可复现性与工程风险

当前论文公开方法细节，但 arXiv 页面未给出稳定官方代码入口。生产系统不能让 planner 自己既生成考试题又自己判分：stress scenario 可以由模型生成，最终 collision、rule violation、tracking feasibility 必须由独立 simulator / checker 判定。

### 适合谁关注

无人车、无人机、移动机器人 diffusion planner、sim-to-real 回归和自动场景生成团队。

### 工程落地启发

内部 CI 可以增加：

```text
Planner Checkpoint
      ↓
Nominal Benchmark
      +
Learned Adversarial Scenario Generator
      ↓
Deterministic Safety Metrics
      ↓
Regression Gate
```

如果某版本平均分更高，但 stress degradation 明显更大，就不应该自动替换生产版本。

## 5. HaptiNet：一旦控制环跨越公网，网络延迟就不再是 IT 指标，而是机器人状态

**时间回补：arXiv v1 提交于 2026-09-04 06:54 UTC。**（[论文](https://arxiv.org/abs/2609.04799)）

### 为什么重要

普通远程机器人主要传视频和指令，100–200 ms 延迟可能只是“操作有点迟钝”。双向触觉不同：用户 A 的力必须通过机器人和网络影响用户 B，B 的响应又返回 A，延迟直接进入闭环，轻则感觉失真，重则发生振荡。

HaptiNet 的价值是把 networked haptics 当作完整控制系统设计，而不是在现有机械臂上再加一层 WebRTC。

### 系统模块

```text
User A ↔ Haptic Terminal A
          ↓
   Network Transport
          ↓
Delay Compensation
          ↓
Haptic Terminal B ↔ User B
```

每个终端强调 low inertia、long stroke 和 high force-feedback capacity；中间通过 imitation-learning-based delay compensator 对跨网络交互做预测补偿。

### 网络 / 动力学假设

这类系统的真实状态至少包括：

```text
round-trip latency
jitter
packet loss
remote velocity
remote force
prediction age
```

如果 compensator 只适应训练时常见的延迟分布，遇到突发拥塞、路由切换或长时间 packet burst loss，预测补偿可能变成错误的主动驱动。因此任何 learned compensator 都应被 passivity / force / energy envelope 包在里面。

### 实时性与真实验证

研究覆盖 284 名健康参与者与 111 名神经系统受损患者，并逐步从实验室扩展到跨城和临床场景。论文报告相较单人训练和仅视觉协作，触觉协作的任务表现分别提高 24% 和 22%；三条跨城链路合计约 4,000 km。

这些数字属于论文特定康复实验，不应外推成通用医疗效果结论；对机器人系统而言，更重要的是跨广域网络仍能维持稳定双向力交互的工程验证。

### 鲁棒性、可复现性与风险

人体直接参与力反馈，风险边界必须比普通 teleoperation 更严格：机械限位、最大力、最大能量注入、通信 watchdog 和网络断开时的安全降级都不能交给 learned model。

### 适合谁关注

远程操作、双机协作、远程维护、触觉教学、跨城机器人控制，以及未来远端人机协同系统。

### 工程落地启发

所有远端控制数据建议统一成：

```text
RemoteState<T> {
  value
  source_time
  age
  latency_estimate
  jitter
  confidence
  valid_until
}
```

网络不再是透明传输层；**信息的新鲜度和可预测性就是控制质量的一部分。**

## 6. LIBERO-RECOVER：VLA 的下一项核心指标应该是“失败后还能不能继续”

**时间回补：arXiv v1 提交于 2026-09-04 14:15 UTC。**（[论文](https://arxiv.org/abs/2609.05178)，[项目页](https://liulin815.github.io/LIBERO-Recovery/)）

### 为什么重要

LIBERO 上接近 100% 的成功率很容易制造一种错觉：Manipulation VLA 已经基本解决。

真实部署里的 episode 却不是每次都从干净初始状态开始。第一次 grasp miss 后物体位置变了；碰撞后容器被推歪；拿错对象后原任务步骤的前置条件已经失效。真正的长时机器人必须回答：

> **当前世界已经偏离 demonstration manifold，我能否识别偏差并把它恢复到可继续状态？**

### Benchmark 分层

LIBERO-Recover 从先进 embodied model 的真实 execution failure 出发构建 1,000+ scenario，并分成四个恢复等级：

```text
Level 1  Action Retry
Level 2  Action Adaptation
Level 3  Object State Recovery
Level 4  Environmental Recovery
```

越往后，问题越不是“再抓一次”，而是需要真正理解世界状态变化。

同时评测四类能力：

```text
Spatial Understanding
Object Structure Reasoning
Interaction Understanding
Topological Reasoning
```

### 传感器与系统假设

这是 benchmark / evaluation 工作，不是一个特定控制器。它的重要性在于强迫模型面对**失败后的非标准初始状态**。

不过恢复任务本身也需要明确安全边界。例如物体掉到人附近、工具卡住或玻璃碎裂时，不应该让 VLA 无限尝试“恢复”，而要进入 unrecoverable / human intervention 状态。

### 实时性与可复现性

Benchmark 建立在 LIBERO 上，项目页已给出公开计划。具体模型的 recovery policy 仍需要各团队自行实现，因此它更像未来 VLA CI 的一套 test contract，而不是可直接部署的 runtime。

### 工程风险

最大的评测误区是只记录最终是否完成任务，却不记录 recovery cost。产品至少应该统计：

```text
failure_detect_latency
recovery_attempts
extra_time
extra_distance
new_damage / disturbance
human_intervention
```

一个“最终能完成但每次失败后胡乱试 20 次”的机器人并不可靠。

### 适合谁关注

VLA、双臂长时操作、工业装配、移动操作，以及已经从 demo 阶段进入客户现场的团队。

### 工程落地启发

建议正式建立执行状态机：

```text
RUNNING
   ↓
FAILURE_DETECTED
   ↓
RETRY / ADAPT / RESET
   ↓
RECOVERED → RUNNING
   ↓
UNRECOVERABLE → STOP / HUMAN
```

VLA 不应该只有 `action()` API，还应有 `failure_state / recovery_state`。

## 7. OpenAI Research Acceleration：长时 Coding Agent 已经变成“并行计算资源”，但人类高层决策仍是瓶颈

**时间回补：OpenAI 于 2026-09-06 发布内部研究数据。**（[官方研究](https://openai.com/index/research-acceleration-view-inside-openai/)）

### 突破性工程价值

这份数据值得关注，不是因为它证明了某个 benchmark，而是因为它展示了一个真正高强度研发组织如何消费 Coding Agent。

OpenAI 报告截至 8 月中旬：

```text
中位研究员：> $600 / day API 等价推理
90 分位：   > $7,000 / day
整个研究组织：
3.1 agent-workdays / 1 human-workday
```

研究员普遍同时运行多个 Agent，Agent 总 runtime 已超过人类劳动时间。

这意味着 AI Coding 基础设施开始更像 compute cluster，而不是“一个更聪明的 IDE 自动补全”。

### 什么工作真的被 Agent 吃掉了

OpenAI 将研发过程分为 Decide、Design、Build、Run、Analyze、Communicate 六类。2026 年各类 Agent 使用都增长，但最明显的仍是代码 / 基础设施、技术帮助、运行监控等；**高层 planning 仍只占很小一部分 token**。

这和生产软件研发很一致：Agent 最先替代的往往不是“决定公司下一季度做什么”，而是：

```text
查仓库
写实验脚本
修基础设施
跑评测
看日志
做重复分析
```

### 长任务仍需要人工 Steering

官方数据还显示，过去六个月中，成功的 4–8 小时 Agent 任务里，**超过一半至少需要一次人工干预**。

所以“Agent 可以连续工作数小时”不应被翻译成“人可以完全不管数小时”。更准确的产品形态是：

```text
Human sets direction
      ↓
Parallel Agents execute
      ↓
Evidence / anomalies surface
      ↓
Human intervenes at high-value decision points
```

### 不能过度解读因果关系

OpenAI 明确提醒，实验数增长和 Codex adoption 相关，但同期可用 compute 也大幅增长；AI 研究本身还有数据、训练算力、评测和组织协作等多个瓶颈。

因此这些数据说明“Agent 使用和研发吞吐一起增长”，不等价于严格证明“3.1 个 Agent 工作日 = 3.1 倍科研速度”。

### 权限、安全与可验证性风险

官方还披露，在 Hugging Face 安全事件后曾暂停面向部署的新模型 RL 训练，进一步加固、红队测试研究环境与监控，部分 workload 在加强控制后恢复。这说明当 Agent 真正进入模型研发基础设施时，权限和环境隔离本身就是 capability scaling 的一部分。

生产研发平台至少应区分：

```text
Read-only analysis
Experiment launch
Code write
Training control
Secret access
Deployment authority
```

Agent 使用量越大，默认权限越不能一起放大。

### 适合谁关注

正在公司内部大规模部署 Codex / Claude Code / OpenHands 类 Agent、运行多个并行 Worker、构建 AI 研发平台的团队。

### 工程落地启发

不要只统计“每天调用多少 token”。更值得看：

```text
agent-work-hours / human-hour
successful task duration
human interventions / task
experiment throughput
verification failures
rollback rate
cost per accepted change
```

只有把“并行算力”与“被验收的工程产物”绑定起来，才能判断 Agent 是否真的加速研发。

## 8. Better Understanding, Better Fixes?：测试通过的 Patch 也可能完全没有理解 Bug

**时间回补：arXiv v1 提交于 2026-09-04 09:11 UTC。**（[论文](https://arxiv.org/abs/2609.04909)）

### 突破性工程价值

自动修复系统通常只看最终结果：

```text
Patch → Tests pass ? → Accepted
```

这篇工作把 LLM 修复过程拆开，研究中间理解是否真的 grounded。它检查三种 intermediate artifact：

```text
Triggering Testcase Identification
Line Coverage Prediction
Additional Testcase Generation
```

如果 Agent 连“哪个测试真正触发 bug、哪条路径会执行、还缺什么边界测试”都理解错了，那么最后 patch 即使绿灯，也可能只是碰巧屏蔽症状。

### 数据与结果

研究在 **832 个 Defects4J bug** 上评估三个代表性 LLM。

不同模型 / 设置下，只有 **21.0%–55.9%** 的补丁通过开发者测试套件。

更关键的是，对 **812 个 sampled repair** 的人工分析发现：

```text
72.7% 存在 repair hallucination
其中主要类型：
45.9% incorrect causal localization
18.5% incorrect repair strategy
```

而 hallucinated repair 中包含“通过全部可用测试”的 patch。

### 为什么“补更多测试”仍不够

论文还发现模型会：

- 识别错真正 triggering testcase；
- 在有 branch 的控制流里预测错 coverage；
- 生成漏掉 bug-triggering condition 的新测试；
- 写出错误 expected behavior。

因此让同一个 Agent：

```text
写 Patch
→ 自己补 Test
→ 自己宣布 Test 通过
```

并没有真正建立独立验证。

### 是否适合真实研发流程

非常适合 repository-level Coding Agent。建议 handoff 不只保存 diff，还保存：

```text
BugEvidence {
  triggering_test
  suspected_symbols
  causal_path
  failing_invariant
  patch_rationale
  validation_receipts
  repo_sha
}
```

Reviewer 可以直接判断“Patch 修改的位置是否真的在证据链上”。

### 权限、安全与可验证性风险

生成 Agent 不应拥有随意删除失败测试、修改验收脚本或降低 coverage threshold 的权限。

最终 Acceptance 至少需要：

```text
Original regression tests
Independent generated tests
Static / dynamic analysis
Patch-diff review
Post-condition / invariant checks
```

安全关键代码还应再加入 fuzz、sanitizer 或形式化约束。

### 工程落地启发

以后 Coding Agent 的“成功轨迹”最好不要定义成：

```text
CI green
```

而是：

```text
CI green
+ causal evidence coherent
+ independent verifier accepts
+ patch minimal enough
+ no constraint regression
```

## 经典论文回顾

### CHOMP：为什么现代轨迹优化仍然在重复 2009 年提出的“把整条轨迹当成一个函数来优化”

**历史位置：** Nathan Ratliff、Matthew Zucker、J. Andrew Bagnell 与 Siddhartha Srinivasa 在 ICRA 2009 发表 **CHOMP: Gradient Optimization Techniques for Efficient Motion Planning**；2013 年的 IJRR 扩展版系统化为 **Covariant Hamiltonian Optimization for Motion Planning**。它是现代机器人 trajectory optimization 最重要的奠基工作之一。（[CMU ICRA 2009 页面](https://publications.ri.cmu.edu/chomp-gradient-optimization-techniques-for-efficient-motion-planning)，[IJRR DOI](https://doi.org/10.1177/0278364913488805)，[MoveIt CHOMP 实现](https://github.com/moveit/moveit/tree/master/moveit_planners/chomp)）

### 核心问题

传统 sampling planner 常产生一串几何上可行但并不漂亮的 waypoint：

```text
RRT / PRM
   ↓
碰撞自由 Path
   ↓
很多折线 / 抖动
   ↓
再做 Smoothing
```

CHOMP 的核心观点是：**轨迹本身就是优化变量。** 不必把“找路”和“轨迹变顺”完全割裂，可以直接优化一个轨迹泛函，使 smoothness 与 obstacle avoidance 同时下降。

### 关键数学思想

可以将目标粗略写成：

```text
J[ξ] = J_smooth[ξ] + λ J_obs[ξ]
```

其中 `ξ(t)` 是整条连续轨迹。

普通欧氏梯度直接在离散 waypoint 坐标上下降会严重依赖轨迹参数化：同一条几何曲线只因采样点密度不同，就可能得到不同更新方向。

CHOMP 使用 **covariant functional gradient**，用与轨迹 smoothness 相关的度量对梯度进行预条件，使更新更接近“改变曲线形状”而不是“拖某几个离散点”。这也是为什么它能同时产生较平滑、空间相关性更强的整条轨迹更新。

2013 年扩展工作进一步引入 Hamiltonian Monte Carlo 来缓解高成本局部极小值，并支持 trajectory-wide hard constraints。

### 障碍代价与地图假设

CHOMP 典型障碍项依赖 robot body points 到障碍的距离及梯度，因此非常适合：

```text
Signed Distance Field / Distance Transform
             ↓
距离 + 空间梯度
             ↓
Trajectory Obstacle Cost
```

这条接口今天仍然非常现代：ESDF、SDF、Neural SDF、Gaussian / voxel distance field 最终都可以给轨迹优化器提供类似梯度。

但它也意味着地图必须能给出**连续且足够稳定的距离梯度**。若 16 线 LiDAR 直接产生稀疏、破碎障碍边界，梯度噪声就会让优化器沿错误方向移动。

### 动力学假设

经典 CHOMP 更偏 configuration-space / trajectory-shape optimization，并不是完整的 torque-level dynamics optimizer。速度、加速度或更高阶 smoothness 可以进入代价，但复杂非线性动力学、接触切换和 actuator saturation 并不是其原始强项。

因此今天高动态无人机 / 人形通常会选择：

```text
CHOMP-like geometric trajectory optimization
                ↓
MPC / DDP / Whole-Body Controller
```

或者直接使用带动力学约束的现代轨迹优化器。

### 当年为什么重要

它把 motion planning 的关注点从“如何在高维空间随机找到一条路”推向另一个方向：

> **如果已经有一个大概的初始轨迹，能否利用可微环境结构高效把整条轨迹变好？**

对于机械臂、腿式等高维系统，这在很多场景比从零开始构造庞大搜索树更直接。

### 今天仍然在使用的思想

今天大量优化式规划器仍然保留 CHOMP 的核心结构：

1. 轨迹作为整体优化变量，而不是彼此独立的 waypoint；
2. smoothness / obstacle / task cost 共同优化；
3. 使用距离场提供连续碰撞梯度；
4. 用预条件 / metric-aware update 改善轨迹空间的数值条件；
5. warm-start 极其重要，上一周期轨迹可以直接成为下一周期初值。

这些思想在 TrajOpt、STOMP、GPMP2、现代 differentiable planner 乃至一些 diffusion-guided trajectory refinement 中都能看到影子。

### 已被后续替代的部分

经典 CHOMP 最明显的边界是 local minimum：

```text
初值在障碍左边
→ 往往继续优化左边 homotopy
```

很难仅凭局部梯度突然穿过高代价区域找到完全不同拓扑的右侧路线。

现代系统因此经常结合：

```text
Global / Topological Planner
         ↓
产生多个初值 / Corridor
         ↓
CHOMP / TrajOpt / MPC Refine
```

另外动态障碍、接触、强动力学约束、chance constraint 和实时 uncertainty 都需要更现代的扩展。

### 公开代码与可复现性

CHOMP 已进入 ROS / MoveIt 生态，MoveIt 仓库仍包含 `moveit_planners/chomp`，因此经典算法的工程复现成本远低于很多新论文。需要注意的是，具体 MoveIt 版本、collision model 和 distance-field implementation 会明显影响实际效果。

### 对当前工程项目的重新解读

对 16 线 LiDAR / 移动机器人，现在更值得重用的不是“直接把 CHOMP 搬来替代所有 local planner”，而是它的接口思想：

```text
LIO / Local Map
      ↓
稳定 Voxel / ESDF
      ↓
Global / Topological Candidate
      ↓
Covariant Trajectory Refinement
      ↓
MPC / Controller
```

如果地图稀疏，可以先对 occupancy / surfel 形成 conservative ESDF；如果存在多个明显 homotopy，则由上层生成多个初值，再分别优化，而不要指望单条局部梯度轨迹自己发现所有通路。

今天的 diffusion planner 和 CHOMP 放在一起看，还有一个很有意思的组合：

```text
Diffusion
→ 负责生成多样初值 / homotopy

CHOMP-like Optimizer
→ 负责确定性地满足局部几何与平滑约束
```

生成模型擅长“想出不同办法”，经典优化器擅长“把一个办法修得更干净”。这比让任意一方独占整个规划链更符合生产机器人。

## 今日结论

今天最清晰的机器人系统信号是：**昂贵能力正在从“永久在线组件”变成“按需教师、评估器或加速器”。** AquaBEV 用 3D sonar 只做训练期几何监督，部署只保留单目；diffusion traffic model 一份权重既可规划，也可在测试阶段生成危险场景；LIBERO-Recover 更进一步，把失败本身变成新的测试资产。

控制侧也越来越强调以前经常被隐藏的中间状态。H2INT 显式面对 pedestrian responsiveness 的不确定性，HaptiNet 把网络 delay 当成控制系统的一部分，APEX-RBD 甚至把每一类动力学变量的数值精度都变成设计状态。机器人软件从“模块串起来就行”逐渐走向：

```text
Geometry Quality
Interaction Belief
Information Age
Numerical Precision
Failure State
```

这些都需要被显式表示、记录和验收。

规划方面，本期 diffusion planner 与 CHOMP 经典工作形成了很好的互补。生成模型擅长多模态 proposal 和长尾 scenario；局部优化擅长把明确的几何 / 平滑约束压进一条连续轨迹。未来更稳妥的架构很可能是：

```text
Learned Multi-modal Proposal
           ↓
Deterministic / Optimization Refinement
           ↓
Independent Safety Checker
           ↓
Controller
```

而不是让一个模型同时负责“想方案、证明方案、执行方案”。

AI Coding 侧的结论同样明显。OpenAI 的内部数据说明 Agent 已经可以被当成大规模并行研发算力，但成功的数小时任务仍经常需要人工 steering；APR hallucination 研究则说明即使最终测试通过，Agent 也可能根本没有正确理解 bug。真正能长期扩展的研发平台需要把：

```text
Requirements
Execution Evidence
Causal Diagnosis
Patch
Independent Validation
Runtime Provenance
```

做成持久 Artifact，而不只是把对话窗口做得更长。

## 最值得深入研究或尝试复现的方向

1. **Teacher-Sensor Distillation for Mapping。** 在已有 MID360 / 高质量深度相机的数据采集平台上训练一个更便宜的单目或 16 线 LiDAR local traversability / occupancy 网络，部署时移除 teacher sensor，重点验证跨场景 domain shift，而不是只看同数据集 IoU。

2. **Crowd Responsiveness Belief。** 在现有人体 tracker 后增加一个简单的在线 `responsiveness_score`：机器人轻微调整轨迹后，观察行人是否同步响应，用时序统计而非 end-to-end 网络先验证这个变量是否能减少过近会车和不必要停顿。

3. **Generative Planner Stress CI。** 不管当前使用 MPPI、MPC 还是 learned planner，都增加一个生成式场景层，主动产生 cut-in、突然停止、窄通道等“名义分数高但可能脆弱”的场景，并统计 `nominal→stress degradation` 作为正式发布指标。

4. **Coding Agent Evidence Gate。** 对每个自动修复强制生成 `triggering_test / causal_symbol / failing_invariant / validation_receipt / repo_sha`；如果 patch 测试通过但证据链自相矛盾，进入人工 Review，而不是自动合并。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)
- [AquaBEV](https://arxiv.org/abs/2609.04411)
- [H2INT](https://arxiv.org/abs/2609.05300)
- [APEX-RBD](https://arxiv.org/abs/2609.05161)
- [One Diffusion Model, Two Roles](https://arxiv.org/abs/2609.04921)
- [HaptiNet](https://arxiv.org/abs/2609.04799)
- [LIBERO-RECOVER](https://arxiv.org/abs/2609.05178)
- [OpenAI Research Acceleration](https://openai.com/index/research-acceleration-view-inside-openai/)
- [Better Understanding, Better Fixes?](https://arxiv.org/abs/2609.04909)
- [CHOMP ICRA 2009](https://publications.ri.cmu.edu/chomp-gradient-optimization-techniques-for-efficient-motion-planning)
- [CHOMP IJRR 2013 DOI](https://doi.org/10.1177/0278364913488805)
- [MoveIt CHOMP](https://github.com/moveit/moveit/tree/master/moveit_planners/chomp)
