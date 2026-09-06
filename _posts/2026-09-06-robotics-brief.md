---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-06"
date: 2026-09-06 09:00:00 +0800
description: "聚焦公共地图视觉定位、多模态 VLA 鲁棒性、接触力感知移动操作、四足跑酷导航、双臂数据扩展、JEPA 世界模型与 Coding Agent 约束评测。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-06

## 摘要

今天是周日，arXiv Robotics 与 Software Engineering 的最新常规公开批次仍是 2026-09-04：Robotics 共 75 条，其中 36 条为 new submissions；Software Engineering 共 31 条，其中 14 条为 new submissions。严格最近 24 小时内不足 5 条高质量、未重复且可完整核验的新主动态，因此本期按任务规范扩展到最近 7 天。最终 8 条主动态的 v1 均提交于 9 月 2–3 日 UTC，全部明确标为“时间回补”，没有把周末日报日期误写成论文发布时间。

今天 SLAM / 定位方向最值得优先看的是 **AutoCompass**。它没有再构建一张昂贵的城市级 3D 地图，而是直接从单张图像定位到公开 2D 地图，并专门解决训练数据里 GPS / heading 标签并不精确的问题：heading 标签可以完全不提供，只用带噪 GPS、位置容忍区间，以及可选的 SLAM / SfM 相对位姿，就能训练 3-DoF neural map matcher。它更像长期机器人的“廉价全局重定位层”，而不是替代 LIO / VIO 的高频里程计。

机器人学习侧，今天有三条很一致的信号。**EGR** 不让 VLA 对所有相机 / 触觉通道一视同仁，而是在训练时估计每帧、每传感器的任务相关性：低证据传感器应该对扰动保持不敏感，高证据传感器则应该单独足以支撑决策，并且这一机制部署时零额外开销。**FWBC-VLA** 则把接触力从“低层控制器自己处理”的隐变量变成 VLA 能看见的 token；它甚至不要求额外腕部 F/T 传感器，而是通过残差力矩估计接触强度，再由 whole-body compensation 负责执行。**MulDP** 面向四足跑酷，把深度视觉、proprioception 和目标一起交给 diffusion policy，直接产生有前瞻性的导航速度命令；真实 Unitree Go1 + Orin NX 上以约 5 Hz 运行高层策略。

大规模数据方面，**XR-2** 公开了 1,500 小时双臂家庭操作示范，并明确研究两条 scaling 轴：更多 expert demonstrations，以及真实机器人执行过程中由人介入产生的 DAgger correction。论文结果显示这两条轴在当前数据规模下都持续提高成功率，说明“扩大静态数据”和“修正策略自己真正会犯的错误”不是互相替代，而是互补的数据投资。

世界模型方面，**Physically Grounded JEPA** 的价值并不在视频生成，而在提醒 latent world model：只预测未来 latent 还不够，表示可能塌缩成对控制没有用的信息。作者同时加入 inverse dynamics 与 state alignment，让 latent transition 必须保留“什么动作导致了这次变化”和“这个 latent 对应怎样的物理状态变化”。它在 TwoRoom、PushT、OGBench-Cube 上分别达到 100%、98%、87% 成功率，但当前仍是 5 页 workshop 工作，尚无真机证据，因此更适合作为 representation design 的信号，而不是成熟世界模型产品。

AI Coding 侧的两项工作非常适合真实 CI / Agent 平台。**SWE-Gate** 证明“测试通过”与“补丁可合并”不是同一件事：644 个通过功能测试的 Agent patch 中，有 221 个、即 34.3% 仍违反真实 PR review 中提取出的约束。**PatchBench** 则处理漏洞修复中的 benchmark gaming：PoC 不再崩溃，并不代表漏洞根因真正修复；11 个 Agent 上，单纯 PoC validation 平均把 solve rate 高估到完整安全 + 语义验证的 1.83 倍。两篇论文共同说明，生产 Agent 的 final gate 必须独立于生成 Agent，而且必须验证“完整工程约束”，而不是只验证一个表面指标。

## 1. AutoCompass：公共 2D 地图可以成为低成本全局定位层，训练时也不必相信 GPS 标签完全正确

**时间回补：arXiv v1 提交于 2026-09-02 16:31 UTC；ECCV 2026。**（[论文](https://arxiv.org/abs/2609.02798)，[项目页](https://nianticspatial.github.io/autocompass/)）

### 为什么重要

很多长期机器人真正缺的不是 100 Hz 局部里程计，而是一个便宜、长期可维护的全球 / 城市级重定位层。传统 image-to-map localization 往往要求大规模 geo-referenced 训练图像，但真实采集数据的 GPS 有米级误差，heading 也可能明显偏；如果把这些标签当成 ground truth，模型会直接学习标签噪声。

AutoCompass 研究的正是这个问题。它把 query 图像与 128 m 级公开地图 tile 做 neural map matching，输出平面上的 `x / y / heading` 三自由度位姿。最关键的监督设计有三层：heading 标签可以彻底删除，由网络结构与地图几何自己学出方向；GPS 不再被当成一个精确点，而是只要求真值落在其附近的容忍区域；如果训练序列还能跑 SLAM / SfM，则利用图像之间更可靠的相对 pose 继续约束局部几何关系。

### 算法模块

可以概括为：

```text
Gravity-aligned query image
        +
Rasterized public map tile
        ↓
Image / Map feature encoders
        ↓
BEV / map cross-correlation
        ↓
3-DoF pose probability
        ↓
Weak-label supervision
GPS tolerance + optional SLAM/SfM relative poses
```

它的工程价值不是“用神经网络替代 SLAM”，而是把高频局部状态估计和低频全局地图定位分层。

### 传感器与地图假设

AutoCompass 依赖图像与公开地图之间存在足够稳定的语义 / 结构对应，也假设重力方向可以获得或近似对齐。输出是 3-DoF 平面位姿，不是完整 6-DoF 状态。因此它更适合车辆、步行 / 低动态机器人在已有道路 / 建筑语义地图中的全局初始化或重定位。

公开地图本身也可能过期、位置不准、缺失内部道路；跨国家、地图风格变化和极端视角都会形成 domain shift。

### 实时性、鲁棒性与可复现性

论文在 driving 与 egocentric benchmark 上均优于高度依赖精确绝对标签的训练方法。当前论文与项目页已公开，但并没有给出适合直接作为端侧实时承诺的统一 FPS，因此工程复现应重点测：单帧 map-matching 延迟、候选地图检索成本、错误地图块的拒绝率，以及长期地图变化后的重定位成功率。

### 风险

神经地图匹配器给出高置信度，并不等于几何上一定正确。重复街区、相似路口和公共地图错误都可能形成高置信误定位。它最好给后端输出多峰 pose hypothesis 和 uncertainty，而不是直接覆盖 LIO / VIO 主状态。

### 适合谁关注

城市机器人、巡检车、无人配送、手机 / 轻量 AR 全局定位，以及希望降低高精度 3D 地图长期维护成本的团队。

### 工程落地启发

比较合理的系统结构是：

```text
IMU + LiDAR / Camera
      ↓
高频 Local Odometry
      ↓
Public-Map Global Matcher
      ↓
候选位姿 + Covariance
      ↓
Geometric / temporal consistency gate
      ↓
Factor graph / global correction
```

不要让 public-map matcher 直接成为单点真值，而是让它提供低频全局约束。

## 2. EGR：多模态 VLA 不应默认“每个传感器永远同样重要”

**时间回补：arXiv v1 提交于 2026-09-02 20:25 UTC。**（[论文](https://arxiv.org/abs/2609.03142)）

### 为什么重要

相机、腕相机、触觉、深度等多模态输入越多，模型并不一定越鲁棒。有限且同质化的示范数据很容易让策略学出错误的跨传感器相关性：任务实际只需要腕相机时，模型却因为背景相机变化而崩；真正有用的视觉被遮住后，另一条本来足够的信息通道又无法独立支撑动作。

作者将这一问题称为 **modality entanglement**。

### 算法模块

Evidence-Gated Regularization（EGR）在训练时估计每帧、每传感器的 task relevance，并用它控制两类一致性目标：

```text
低 Evidence 传感器
→ 扰动后策略应保持不变

高 Evidence 传感器
→ 单独保留该通道时仍应足以决策
```

它不是一个新的 inference module，而是训练目标，因此部署时没有额外推理开销。

### 传感器与系统假设

论文同时覆盖纯视觉多相机和视觉 + GelSight 触觉两类系统，说明方法并不绑死某一种 modality。真实实验包括双 Kinova + 3 个 RGB 相机，以及 MELFA ASSISTA + RGB + 2 个 GelSight。

### 实时性与结果

BEHAVIOR-1K 派生 benchmark 中，完整多模态条件成功率从 12.5% 提升到 16.4%；无关传感器被 corruption 时从 9.4% 提升到 16.5%；只保留单个有效传感器时从 2.8% 提升到 6.1%。真机 physical distractor 中，双臂视觉设置从 30% 提升到 85%，触觉设置从 55% 提升到 70%。

### 鲁棒性与风险

训练阶段的 evidence 估计本身也可能错，尤其两个传感器只有组合起来才可辨识时，“单传感器 sufficiency”不能无限加强。生产系统还应单独维护真实 sensor-health，例如相机掉线、触觉饱和、时间戳异常，不能用 learned robustness 取代硬件健康监测。

### 适合谁关注

多相机 VLA、视觉 + 触觉操作、现场传感器容易被遮挡 / 污染的机器人系统。

### 工程落地启发

即使不复现 EGR，也建议在数据与评测层增加：

```text
sensor dropout
uninformative-sensor corruption
single-sensor fallback
cross-sensor disagreement
```

把“多模态模型全输入时成功”升级为“某个通道变坏时系统还能知道该信谁”。

## 3. FWBC-VLA：把接触力从低层隐变量变成 VLA 可以消费的显式状态

**时间回补：arXiv v1 提交于 2026-09-03 14:10 UTC。**（[论文](https://arxiv.org/abs/2609.03889)）

### 为什么重要

擦白板、推门、移动重物这类 loco-manipulation 不只需要“手应该去哪里”，还需要理解当前到底有没有接触、接触力是在增加还是释放。普通 VLA 看见的是视觉和任务语义，whole-body controller 看见的是动力学稳定性，两者之间缺了一层“任务相关物理交互”的接口。

### 算法模块

FWBC-VLA 分成三层：

```text
Joint state / torque residual
        ↓
HSR-Force sensorless estimator
        ↓
contact strength + temporal variation
        ↓
Force tokens → VLA action expert
        ↓
VLA manipulation action
        +
whole-body compensation correction
        ↓
WBC execution
```

HSR-Force 利用残差力矩推断接触，不要求额外改装腕部 F/T sensor；接触估计随后作为 token 注入 VLA action decoding。作者还构建了超过 5,000 episode 的 WL&Arm 数据集。

### 传感器与动力学假设

“无 F/T 传感器”并不意味着无物理模型。残差力矩会同时受到模型误差、关节摩擦、惯量参数、驱动器跟踪误差和真正外力影响，因此 estimator 必须能区分“机器人模型不准”和“正在推门”。

### 实时性与真机结果

真实平台为 DeepRobotics M20S wheeled-legged quadruped + CM1 6-DoF arm + gripper，并使用 3 个 RealSense D435i。任务包括白板擦拭和推开带闭门器的门，后者把手处需要约 50 N 作用力。论文实验中 FWBC-VLA 在白板任务最终成功率达到 64%，门体推开并穿越达到 52%，显著优于对照的 ForceVLA。

### 鲁棒性、可复现性与风险

论文目前没有稳定可直接复用的完整工程仓库入口。更重要的是，sensorless force estimate 不应替代驱动器层的 torque / current / temperature 保护。接触任务的 final safety 仍应由低层电流、力矩、关节限位、碰撞和急停独立兜底。

### 适合谁关注

巡检操作机器人、推门 / 擦拭 / 阀门、轮足移动操作，以及已有 VLA + WBC 但二者缺少物理交互接口的团队。

### 工程落地启发

先把现有系统的接触状态做成明确数据接口：

```text
contact_probability
estimated_force
force_trend
contact_phase
estimator_confidence
```

让 VLA 或高层技能消费“物理状态”，不要只让低层控制器静默吸收所有接触误差。

## 4. MulDP：四足跑酷的高层导航开始从离散技能切换走向多模态连续 Diffusion Policy

**时间回补：arXiv v1 提交于 2026-09-03 15:19 UTC；IROS 2026 接收。**（[论文](https://arxiv.org/abs/2609.03984)）

### 为什么重要

四足跑酷的低层 locomotion 已经相当成熟，但高层通常仍需要人为指定“这里跳、这里上台阶、这里绕过去”。真正的自主 parkour navigation 要同时处理深度几何、机器人当前身体状态、目标方向和未来几秒速度选择。

MulDP 不把问题拆成硬编码技能状态机，而是用多模态 diffusion policy 直接产生 temporally coherent 的高层导航速度命令。

### 算法模块

```text
Depth history
+
Proprioception history
+
Goal
      ↓
Multimodal encoder
      ↓
Diffusion denoising
      ↓
future navigation velocity commands
      ↓
低层 locomotion controller
```

论文还构建 QPND（Quadruped Parkour Navigation Dataset），包含多类复杂地形和导航行为；训练中对传感器噪声与视觉输入做增强，以缩小 sim-to-real 差距。

### 传感器与动力学假设

MulDP 输出的是高层 velocity command，不是关节 torque，因此真实能力仍依赖一个足够强、能够根据速度命令跨越台阶 / 缝隙 / 障碍的低层 locomotion policy。

### 实时性与真机

真实部署使用 Unitree Go1、RealSense D435i 和 Jetson Orin NX 16GB，diffusion navigation policy 约 **5 Hz**；论文展示户外长距离、动态目标跟随、gap、stairs、hurdle 等场景。

5 Hz 不能理解成机器人只有 5 Hz 控制。它是高层导航更新率，底层步态与关节环仍以更高频率运行。

### 鲁棒性、可复现性与风险

论文消融中，去掉 data augmentation 后成功率明显下降，说明视觉 / 深度 domain gap 仍是主要风险。动态障碍、高反光 / 低纹理深度失效、窄踏板边缘等场景仍需要独立的 geometry / collision health layer。

### 适合谁关注

四足自主巡检、楼梯 / 跳台 / 缝隙导航，以及希望把“路径规划 + 技能切换”进一步学习化的团队。

### 工程落地启发

学习式高层导航最好仍然输出稳定、可限幅的结构化接口，例如：

```text
vx / vy / yaw_rate
mode confidence
valid_horizon
terrain risk
```

而不是直接把关节动作交给一个同时承担感知与规划的大模型。

## 5. XR-2：1,500 小时双臂示范之后，下一条 Scaling 轴是“让真实策略犯错，再只修真正的错”

**时间回补：arXiv v1 提交于 2026-09-03 09:37 UTC。**（[论文](https://arxiv.org/abs/2609.03591)，[公开数据](https://huggingface.co/datasets/challenge-2026/challenge_data)）

### 为什么重要

机器人数据 scaling 经常只讨论“再录更多 demonstration”。但当模型已经看过大量成功轨迹后，最有价值的数据往往变成策略自己执行时真正遇到的边界失败。

XR-2 同时研究这两条轴：先用 1,500 小时双臂 household manipulation 数据做大规模训练，再利用真实执行中的 human intervention 采集 DAgger correction，专门修策略当前分布中的错误。

### 数据与训练结构

论文公开的 1,500 小时 corpus 同时包含真实机器人 teleoperation 与 UMI 风格数据。真实机器人子集包含 32,518 条轨迹、约 5,740 万帧、531.7 小时同一类移动双臂机器人交互数据。

整体研究可以概括为：

```text
Large offline demonstrations
        ↓
XR-2 base VLA
        ↓
Real policy rollout
        ↓
Human intervention / DAgger correction
        ↓
Post-training
```

论文报告，在当前实验范围内，无论继续增加 expert demonstrations，还是增加 DAgger correction，任务成功率都表现出持续提升趋势。

### 实时性

公开实现使用 RTX 4090 级 GPU 进行约 10 Hz 异步推理，输出长度 50 的动作 chunk；全身 joint command 在更高频率进行 temporal ensembling，底层 whole-body motion controller 运行在约 1 kHz。

这再次说明 VLA 产品不是“一个模型的 FPS”，而是一套多频率运行时。

### 鲁棒性与风险

DAgger 的代价是真人必须在策略真正失败的分布里持续介入，而且 intervention 数据本身需要时间同步、标记“人何时接管 / 为什么接管”。如果只把人修正后的动作混回普通示范，可能丢失失败上下文。

大规模同一本体数据也不自动等价于跨机器人泛化；action semantics、相机位姿和控制接口仍然具有 embodiment bias。

### 适合谁关注

希望建立长期机器人数据飞轮、已经有稳定遥操作平台、准备从“离线模仿”走向“部署后持续修正”的团队。

### 工程落地启发

数据平台最好把四类轨迹分开保存：

```text
Expert Demo
Policy Success
Policy Failure
Human Correction
```

并记录 `policy_version / failure_reason / intervention_start / intervention_end`。这比把所有轨迹都当成同一种 BC 数据更适合迭代训练。

## 6. Physically Grounded JEPA：World Model 的 Latent 必须记住“动作导致了什么物理变化”

**时间回补：arXiv v1 提交于 2026-09-03 09:11 UTC；IROS 2026 PWMS Workshop。**（[论文](https://arxiv.org/abs/2609.03565)）

### 为什么重要

JEPA 类 world model 的优势是不用生成像素，只在 latent space 预测未来，因此规划成本可能明显低于视频生成模型。但一个只追求 latent prediction loss 的模型可能找到捷径：预测一些视觉上稳定、却和机器人动作几乎没关系的表示。

对于控制来说，这种 latent 即使“预测很准”也没用。

### 算法模块

作者增加两类物理 grounding：

```text
Latent_t + action
      ↓
JEPA future latent prediction
      +
Inverse Dynamics
→ 强迫 latent transition 保留动作信息
      +
State Alignment
→ 强迫 consecutive latent 与物理配置 / 运动一致
```

Inverse Dynamics 抑制 latent collapse，并让变化方向可反推出动作；State Alignment 再将表示锚定到真实状态变化。

### 结果

四个 benchmark 中，该模型在 TwoRoom、PushT、OGBench-Cube 上分别达到 **100%、98%、87%** 成功率，在 Reacher 上与主要 baseline 接近。消融显示 State Alignment 在四个任务中都能继续提高仅使用 IDM 时的规划表现。

### 动力学与传感器假设

它解决的是 goal-conditioned planning 表示，不是完整 robot dynamics system identification。State supervision 本身也意味着训练期能够访问更结构化的机器人状态。

### 实时性、可复现性与风险

目前是 5 页 workshop 论文，公开摘要没有真实机器人实验，也没有成熟代码工程。因此不能把 benchmark success 直接外推到接触丰富的真实操作。

### 适合谁关注

机器人 world model、latent planning、视频数据预训练，以及希望避免昂贵 pixel rollout 的团队。

### 工程落地启发

训练 world model 时，不要只问：

> 未来 latent 能不能预测准？

还应单独测：

```text
action identifiability
physical-state alignment
off-policy action sensitivity
multi-step transition error
```

只生成“稳定 latent”并不代表模型真的理解控制因果。

## 7. SWE-Gate：功能测试全部通过，仍可能有三分之一的 Patch 不满足真实 Review 约束

**时间回补：arXiv v1 提交于 2026-09-03 17:53 UTC。**（[论文](https://arxiv.org/abs/2609.04167)，[代码与数据](https://github.com/DeepSoftwareAnalytics/SWE-Gate)）

### 突破性工程价值

SWE-bench 一类 benchmark 极大推动了 Coding Agent，但它们通常把“测试通过”当作完成。真实 PR review 还有大量没有完全编码进原测试的要求：不要破坏既有 API、必须使用某种 helper、错误处理方式必须一致、不要引入额外依赖、改动范围不能越界等。

SWE-Gate 将这些 **review constraints** 从真实 PR review comment 中抽取出来，并为每个 repository-level repair 分开构建 functional tests 和 constraint tests。

### 数据与结果

benchmark 包含 **303 个 repair instance、75 个开源 Python repository、6 类软件领域**。

最关键的结果是：研究中共有 644 个 Agent repair 已经通过功能测试，但其中 **221 个（34.3%）**仍然违反 review constraint。

也就是说，单纯 functional pass 明显高估真实可合并能力。

### 是否适合真实研发流程

非常适合。生产 CI 可以直接拆成：

```text
Functional Gate
        ↓
Review-Constraint Gate
        ↓
Security / Dependency Gate
        ↓
Human or Independent Agent Review
```

Review constraint 也不一定都来自自然语言，可以逐步固化成 lint、AST rule、CodeQL、architecture test 或 policy-as-code。

### 权限、安全与可验证性风险

不能让修补 Agent 自己把“不方便通过”的 constraint tests 改掉。生成者与 verifier 必须有不同权限边界，constraint 来源也应绑定 PR / spec / repo revision。

### 工程落地启发

企业内部每次人工 review 如果反复指出同一类问题，就应该把它沉淀成机器可执行 Gate，而不是永远依赖 Reviewer 记忆。

## 8. PatchBench：PoC 不再崩溃，并不等于漏洞真正被修复

**时间回补：arXiv v1 提交于 2026-09-03 16:44 UTC。**（[论文](https://arxiv.org/abs/2609.04075)）

### 突破性工程价值

漏洞修复 Agent 最容易“刷过”的评测是：给一个会崩溃的 PoC，补丁以后 PoC 不崩了，就算成功。

这至少存在两种问题。第一，模型可能见过历史 developer patch，直接记忆答案；论文估计约 **25%** Agent patch 与历史修复存在显著相似性。第二，Agent 可以只在 crash stack 上加条件判断，把这一个 PoC 挡住，却没有消除漏洞根因。

### Benchmark 设计

PatchBench 面向 C/C++，专门选择 ground-truth fix 位于 crash stack 之外的漏洞，再利用 vulnerability transplant 与 code mutation 将历史漏洞迁移到新的 repository context，降低记忆原补丁和表面修补的空间。

最终验证不只跑 PoC，而同时检查 security correctness 与 semantic correctness。

### 结果

PatchBench 包含 **213 个任务、32 个项目**。11 个 Agent 上，原 PoC-only validation 平均把 solve rate 放大到完整验证的 **1.83×**。论文报告聚合结果中，原 PoC 通过率约 83.1%，真正同时通过安全与语义验证约 45.3%。

论文正文声明了计划 / 代码仓库地址，但本轮直接核验该 GitHub URL 时仍返回 Not Found，因此归档中不把仓库写成“已公开可用”。

### 是否适合真实研发流程

对安全修复尤其适合拆成：

```text
Original PoC
      ↓
Variant / mutated PoCs
      ↓
Root-cause semantic tests
      ↓
Regression suite
      ↓
Static / sanitizer / fuzzing
```

“崩溃没了”只能是第一层。

### 权限、安全与可验证性风险

漏洞修复 Agent 必须在隔离 sandbox 中运行，不应默认获得生产 secret、外部网络或发布权限。最终安全判定更不能由生成 patch 的同一 Agent 自己给出。

### 工程落地启发

Coding Agent 的安全 benchmark 应尽量避免“唯一公开输入 → 唯一历史补丁”的闭卷式结构。真正有价值的是让 Agent 在新上下文中证明自己理解了 vulnerability invariant。

## 经典论文回顾

### RMA：Rapid Motor Adaptation 为什么成为腿式机器人“训练时看真值、部署时靠历史推断环境”的经典范式

Ashish Kumar、Zipeng Fu、Deepak Pathak、Jitendra Malik 的 **RMA: Rapid Motor Adaptation for Legged Robots** 发表于 **Robotics: Science and Systems 2021**。它不是今天常见的“大模型”，却奠定了近几年大量 sim-to-real locomotion 中最重要的一种结构：训练时允许 teacher / base policy 看到 privileged environment information，部署时再通过最近一段 proprioception 与 action history 在线推断一个紧凑的环境 / 动力学 latent。（[论文](https://arxiv.org/abs/2107.04034)，[项目页](https://ashish-kmr.github.io/rma-legged-robots/)）

### 核心问题

同一套四足控制器到了真实世界，会不断遇到：

```text
地面摩擦变化
软 / 硬 / 下陷地面
负载变化
电机与机构差异
磨损
外部扰动
```

如果每种环境都重新 system identification + retune controller，很难规模化。纯 domain randomization 又要求策略直接从当前 observation 里隐式覆盖所有可能 dynamics，学习负担很大。

### 算法模块

RMA 的经典结构是两阶段：

```text
Phase 1: Base Policy
proprioception + privileged extrinsics
              ↓
         locomotion action

Phase 2: Adaptation Module
recent state/action history
              ↓
estimated extrinsics latent
              ↓
          Base Policy
```

Base policy 在仿真中通过 RL 学会：如果知道当前环境 / 动力学 latent，该怎么走。

随后 Adaptation Module 学会仅从机器人真实可获得的历史状态和动作估计这个 latent。真机上只运行 `history → adaptation latent → base policy`，不再需要 privileged simulator state。

### 传感器与动力学假设

RMA 的核心输入主要来自 proprioception 和动作历史，不依赖外部地形模型。它能快速适应的前提是环境 / 动力学差异会在机器人响应中留下可辨识信号。

如果两个完全不同的隐藏因素在短历史里产生几乎相同运动响应，adaptation latent 仍然会不可辨识。

### 当年为什么重要

RMA 完全在仿真训练，直接零微调部署到 Unitree A1，并展示沙地、泥地、长草、岩石、碎石、楼梯和滑面等真实环境。项目页强调适应可以在**几分之一秒**内发生。

它把 sim-to-real 从“训练一个对所有随机环境都一样强的 policy”变成：

> 训练一个会根据当前机器人反馈迅速推断“现在这个世界是什么样”的 policy。

### 今天仍在使用的思想

**Privileged learning。** 仿真知道、真机拿不到的摩擦、payload、motor strength 等变量，可以用于训练 teacher / critic，而不必强迫部署端增加传感器。

**History-based system identification。** 最近的状态—动作响应本身就是在线系统辨识信号。

**Adaptation 与行为策略分层。** 不必让同一个大网络同时学习“识别环境”和“控制机器人”的全部问题。

### 已被后续扩展的部分

今天的机器人开始进一步把一个抽象 `extrinsics latent` 拆成更可解释的状态：

```text
contact reliability
slip probability
force estimate
terrain feature
sensor evidence
motor health
```

本期 EGR 和 FWBC-VLA 就体现了这种趋势：适应不再只是“猜一个统一隐藏向量”，而是显式判断哪个传感器该信、当前接触强度如何。

### 公开代码 / 数据与可复现性

RMA 项目页公开论文、补充材料、视频和代码入口，历史影响和复现资料都比较成熟。由于原系统依赖特定仿真、A1 动力学和策略训练设置，直接照搬到现代 Unitree / DeepRobotics 平台仍需要重新做 actuator model、观测和动作接口适配。

### 对当前工程项目的重新解读

对轮足、四足甚至无人机，可以把 RMA 思想重新解释成一个**动力学健康与适应层**：

```text
High-rate state / action history
           ↓
Adaptation / System-ID feature
           ↓
friction / payload / actuator / contact confidence
           ↓
MPC parameters / policy conditioning
           ↓
低层确定性 Safety Envelope
```

最值得保留的不是“必须用 RL”，而是：**把部署时不可直接测的系统变化，先变成一个可在线推断的中间状态，再让控制器根据它改变行为。**

## 今日结论

今天最清晰的定位信号是：**长期机器人不需要所有地图都变成昂贵 3D 数字孪生。** AutoCompass 表明，公开 2D 地图 + 弱标签学习可以承担低频全局定位，而高频局部几何仍交给 VIO / LIO。地图层与里程计层明确分工，往往比继续把单一 SLAM 地图做得无限大更容易长期维护。

VLA / 控制侧则出现一条更明显的共同趋势：**学习系统开始从“所有输入一起吞、所有物理交互自己猜”转向显式的质量 / 物理状态接口。** EGR 估传感器证据，FWBC-VLA 估接触力，MulDP 把高层速度规划和低层 locomotion 分开，RMA 的经典结构则告诉我们为什么这种“先估环境状态，再调行为”的分层会长期有效。

数据规模方面，XR-2 给出了非常现实的下一步：当 demonstration 已经上千小时后，继续录完美成功轨迹仍然有价值，但 on-policy correction 会越来越重要。机器人数据平台最终需要关心的不只是“总小时数”，而是**这批数据到底来自专家、成功策略、失败策略，还是人工纠偏**。

World Model 侧，Physically Grounded JEPA 提醒我们，压到 latent space 只是第一步。一个对图像压缩很好的 latent，不一定对控制有用；action identifiability 和 physical-state grounding 应成为独立验收指标。

AI Coding 的两项工作则把生产 Gate 的方向说得非常清楚：

```text
功能正确
   ≠
满足工程 Review 约束
   ≠
安全根因真正修复
```

Agent 越强，最终 verifier 越不能只是“再叫同一个模型看一眼”。真实 PR 约束、静态规则、安全测试、变体 PoC、差分执行和 CI receipt 都应该成为独立证据。

## 最值得深入研究或尝试复现的方向

1. **AutoCompass-lite 全局重定位层。** 不动现有 LIO-SAM / VIO，只实现 `camera → public-map 3DoF candidates`，通过轨迹连续性和局部地图几何做二次验收；重点测长走廊 / 园区跨天重定位成功率与错误高置信率。

2. **多模态 VLA 的 Sensor Evidence 回归集。** 对每个相机 / 触觉通道分别做遮挡、噪声、静态图像、随机延迟和整路 dropout，记录模型是“忽略无关传感器”还是“关键传感器坏了仍盲目执行”。

3. **给移动操作增加 Contact State API。** 先不用完整 FWBC-VLA，只利用 motor current / residual torque 建 `contact_probability / estimated_force / phase`，让上层 skill 能知道“还没碰到、已接触、持续加载、已释放”。

4. **Coding Agent 做双 Gate：Functional + Constraint / Security。** PR 合并条件不再只有测试绿灯；把重复 review comment 固化为 constraint tests，安全修复再加入 mutated PoC、semantic regression 和 sanitizer / fuzzing，生成 Agent 不拥有修改 Gate 的权限。

## 参考资料

- [AutoCompass](https://arxiv.org/abs/2609.02798) · [项目页](https://nianticspatial.github.io/autocompass/)
- [Sensing Which Modality Matters / EGR](https://arxiv.org/abs/2609.03142)
- [FWBC-VLA](https://arxiv.org/abs/2609.03889)
- [MulDP](https://arxiv.org/abs/2609.03984)
- [XR-2 / 1,500h Bimanual Manipulation](https://arxiv.org/abs/2609.03591) · [数据](https://huggingface.co/datasets/challenge-2026/challenge_data)
- [Physically Grounded JEPA World Models](https://arxiv.org/abs/2609.03565)
- [SWE-Gate](https://arxiv.org/abs/2609.04167) · [代码与数据](https://github.com/DeepSoftwareAnalytics/SWE-Gate)
- [PatchBench](https://arxiv.org/abs/2609.04075)
- [RMA: Rapid Motor Adaptation](https://arxiv.org/abs/2107.04034) · [项目页](https://ashish-kmr.github.io/rma-legged-robots/)
- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)
