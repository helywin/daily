---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-14"
date: 2026-09-14 09:00:00 +0800
description: "arXiv 周一新批次：多会话 LiDAR SLAM、LIO 参数敏感性、神经 CBF、人形越障、VLA 去视觉捷径、双世界模型与 AI Coding 图搜索；附 3 条社区实战技巧。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-14

## 摘要

今天早些时候归档时，arXiv 周末后的新批次尚未刷新；随后 **2026-09-14（周一）** 的公开列表已经出现，因此本版按最新批次重新检索和去重。当前 [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) 显示 59 条 recent entries，[arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent) 显示 30 条。以下 8 条主动态均未出现在此前覆盖索引中，其中多数 v1 实际提交于 9 月 10–11 日 UTC，但属于今天进入最新公开批次的工作。

SLAM 侧今天最值得优先看的工作是 **Chain-SLAM**。它专门处理多次任务、多台平台累积出来的 LiDAR 地图如何在线连成一个一致后端，而不是再做一个单次任务里程计。系统先用 GNSS proximity 做粗对齐，再利用 session adjacency graph 传播跨会话候选，通过 ICP 验证 chained loop closure，最后把可靠约束统一放进 factor graph。它的工程价值在于：长期机器人地图维护开始从“每次任务重建”转向“会话之间持续建立可追踪关系”。([论文](https://arxiv.org/abs/2609.12221)，[项目页](https://ai4ce.github.io/Chain-SLAM/)，[代码](https://github.com/ai4ce/Chain-SLAM))

另一篇 **Parameter Sensitivity Analysis for Aerial LiDAR-Inertial Odometries** 很适合已经在调 FAST-LIO2 / Cartographer 的团队。作者没有继续提出一个新 LIO，而是用 exhaustive grid、Pearson correlation 与 random-forest permutation importance 系统分析低空飞行参数敏感性，再给出简化调参建议；论文报告推荐配置在 94% 的分析案例中，ATE 与完整网格搜索最优值相差不超过 5 cm。它回答的是很现实的问题：哪些参数真的值得工程师花时间调，哪些参数并没有想象中敏感。([论文](https://arxiv.org/abs/2609.12837))

安全控制侧，**VertexCBF** 把 neural CBF 与控制集合的几何结构结合起来。对 control-affine dynamics 和凸多面体控制集，Hamiltonian 的最大值一定出现在顶点，因此不需要在完整连续控制空间中盲目搜索；作者据此构建 GPU 并行的 vertex-restricted tree search，并用 residual architecture 保证 learned CBF 不会高于指定 constraint function。工作覆盖 15 个系统，并在移动机器人行人避障上做了硬件验证。([论文](https://arxiv.org/abs/2609.12831))

搜索救援机器人方面，**ASTRIL-MPC** 把 learned kinematics、NMPC 与受限 LLM adaptation 放在同一个控制闭环里。神经模型从高度序列和近期轨迹预测 task-state increment，NMPC 保持显式可行性；LLM 只能通过经过 range clipping、rate limiting 和 consistency check 的接口，修改少数权重和边界，而不能直接生成履带动作。编译后的 predictor + MPC 完整周期控制在 100 ms 内；论文报告相对非自适应 NMPC 的综合穿越质量最高提高 71%，并消除下降阶段可测的碰撞冲击。([论文](https://arxiv.org/abs/2609.13083))

VLA 侧，**Latent Interface Training（LIT）** 直接针对“视觉—动作捷径”。Stage 1 先在没有图像的条件下，让 Action Expert 只依赖语言、机器人状态和终端 SE(3) pose 学会动作；Stage 2 再让视觉信息只能通过 pose-supervised latent interface 进入动作模型。这样迫使视觉先被压缩成与几何目标相关的中间表示，而不是让策略记住背景、相机视角和纹理。论文在 π0.5、MolmoAct2、FAST-WAM、ImageWAM 上都观察到明显 OOD 增益。([论文](https://arxiv.org/abs/2609.12641)，[项目页](https://magiclab-nus.github.io/LIT/)，[代码](https://github.com/MAGICLAB-NUS/LIT))

人形控制方面，**DWMP** 不用一个 world model 同时解释身体动力学和视觉深度，而是显式拆成两个模型：Koopman latent 负责 proprioceptive dynamics，RSSM 负责视觉 / depth 的时序预测，最后将两种 latent 融合给 student policy。作者在仿真和 Unitree G1 上测试随机障碍布局。这里更重要的信号不是“又一个世界模型”，而是不同传感模态可以采用不同的预测结构和时间归纳偏置，而不必强行共享一个统一 latent dynamics。([论文](https://arxiv.org/abs/2609.12347))

AI Coding 侧，**GraphAHA** 把 test-time code search 从“不断采样新的独立候选”变成一个可复用的有向无环图。等价程序会合并成同一 code node，下游统计可以被多个路径共享；层级 Thompson sampling 再决定是探索新 successor、复用已有 successor，还是选择 sampling / reasoning / implementation / repair 等不同动作。LiveCodeBench 与 CodeContests 上，论文在 20 个设置中 18 个取得最佳结果，并在可见测试条件下相对最强基线平均提高 4.1 个百分点 Pass@1。([论文](https://arxiv.org/abs/2609.12757))

最后一篇 **Reality Is the Final Verifier** 不提供新的 SWE-bench 数字，而提出一个很值得工程系统长期保留的“两种差距”框架：Requirement Gap 是文本需求与真实 stakeholder intent 的差距，Model Gap 是测试 / 仿真 / evaluator 与真实部署环境的差距。Agent 的 reward hacking 会利用这两种 gap，hallucination 则可能放大它们。因此验证不应该在“测试全绿”时结束，而应形成 deployment evidence → requirement / model / evaluator revision 的 assurance loop。([论文](https://arxiv.org/abs/2609.12039))

## 1. Chain-SLAM：长期多会话地图，不应该只是多个独立点云文件

**今日 arXiv 公开批次；v1 提交于 2026-09-10 21:29 UTC；IROS 2026。**

### 为什么重要

多数 LiDAR SLAM 论文默认任务从一个干净起点开始，跑完一次以后得到一张地图。但真正长期运行的机器人往往是：

```text
Day 1 / Robot A
Day 2 / Robot A
Day 7 / Robot B
维护后重新上电
局部区域重新扫描
```

如果每个 session 只是保存成独立轨迹和点云，后续全局地图维护、跨会话定位和变化分析会越来越困难。

Chain-SLAM 试图直接构建一个**跨 session 的在线后端**。

### 算法模块

整体可以概括为：

```text
Session-level Odometry / Keyframes
            ↓
GNSS Proximity Initial Alignment
            ↓
Session Adjacency Graph
            ↓
沿图传播 Chained Loop Candidates
            ↓
ICP Verification
            ↓
Verified Inter-session Constraints
            ↓
Unified Factor Graph Optimization
```

项目页进一步说明，系统会在 pose graph 上通过 BFS 收集相连 keyframe，再用 ICP 判断传播出来的闭环是否真的成立。([项目页](https://ai4ce.github.io/Chain-SLAM/))

### 传感器与地图假设

方法依赖各 session 内部的局部里程计已经足够可用，并使用 GNSS proximity 进行粗粒度 session 初始化，因此它并不是完全无全局信息的任意跨会话定位。

论文也明确没有把动态物体剔除作为核心模块。停车场、道路、工厂如果长期结构变化很大，ICP 的几何一致性仍可能把“历史存在、现在消失”的结构当成匹配证据。

### 实时性、鲁棒性与可复现性

论文强调 online multi-session backend 和 cross-platform robustness，并已经公开代码。([代码](https://github.com/ai4ce/Chain-SLAM))

真正复现时我会重点测四项，而不是只看最终 ATE：

```text
session 数量增长后的后端 P95 时间
错误 chained loop 的拒绝率
跨平台 LiDAR / 外参变化敏感性
地图长期变化后的约束老化
```

### 工程风险

跨会话系统最危险的是错误约束具有长期传播性。一条错误 loop 不只是破坏当前轨迹，还可能污染后续多个 session。

因此每个 inter-session factor 最好保存：

```text
source_session
target_session
initial_alignment_source
ICP fitness
support_keyframes
creation_time
last_revalidated
```

并允许后续失效 / 降权，而不是永久写死。

### 适合谁关注

长期巡检、园区机器人、多机器人共享地图、跨天 LiDAR mapping、车队地图维护。

### 工程落地启发

如果现有系统已经有 LIO-SAM / FAST-LIO2，不一定要换前端。可以先把每次任务的 keyframe graph 作为 session artifact 保存，再单独做一个“跨 session constraint service”。

这比直接把所有历史点云重新 ICP 到一张超大地图，更容易调试、回滚和审计。

## 2. Aerial LIO 参数敏感性：比“再找一个更强 LIO”更实用的，是先知道哪些参数真正重要

**今日 arXiv 公开批次；v1 提交于 2026-09-11 13:31 UTC。**

### 为什么重要

FAST-LIO2、Cartographer 这类成熟系统在真实无人机上经常不是“完全不能跑”，而是：

```text
某些场景很稳
某些高度 / 速度开始漂
换雷达以后突然变差
参数很多，不知道先调哪个
```

工程师很容易陷入经验式手调，最后无法判断提升来自哪个参数，也很难迁移到下一台机器人。

这篇工作把参数调优本身当作研究对象，而不是提出新前端。

### 方法

作者对低空飞行数据进行 exhaustive grid evaluation，并同时使用：

```text
Pearson correlation
→ 观察近似线性敏感关系

Random-Forest Permutation Importance
→ 捕获非线性和参数交互影响
```

分析 FAST-LIO2 与 Cartographer 中不同配置对轨迹误差的影响，再压缩成更少的推荐调参规则。([论文](https://arxiv.org/abs/2609.12837))

### 结果

论文报告，简化后的推荐配置在 **94% 的分析案例中，ATE 与 exhaustive-grid 最优值相差不超过 5 cm**。

这个结果的工程意义不是“存在一套万能参数”，而是说明大量搜索维度可以通过敏感性分析提前排除。

### 传感器与场景假设

结论针对论文覆盖的低空航测 / 无人机数据和这两类算法。参数 importance 会随：

```text
LiDAR 线数 / FoV
IMU 噪声
飞行速度
地面高度变化
点云结构
时间同步
```

改变。

因此不要把论文的具体参数值直接抄成所有平台默认值。

### 工程落地启发

对自己的 16 线 LiDAR / MID360 系统，我更推荐复现它的方法，而不是复现它的最终参数：

1. 定义 5–10 个真正怀疑的参数；
2. 在代表性走廊 / 坡地 / 空旷区做小规模 grid；
3. 用 sensitivity ranking 找 Top-3；
4. 以后只对 Top-3 做现场自适应或自动标定。

这会比长期靠“感觉调参数”更容易形成可维护产品。

## 3. VertexCBF：利用控制集合几何，把 Neural CBF 的安全搜索压到顶点

**今日 arXiv 公开批次；v1 提交于 2026-09-11 13:24 UTC。**

### 为什么重要

Control Barrier Function 的核心价值，是把安全写成一个运行时可检查的不等式；但复杂高维系统中，真正计算安全值函数或 Hamiltonian 仍然很贵。

VertexCBF 抓住 control-affine system 的一个结构：

```text
x_dot = f(x) + g(x)u
```

当控制集合 `U` 是 convex polytope 时，对 `u` 为线性的 Hamiltonian 最大值出现在多面体顶点。

所以与其在连续控制空间里搜索：

```text
max over all u ∈ U
```

可以转化成：

```text
max over vertices(U)
```

### 算法模块

```text
Safety Constraint Function
       ↓
Residual Neural CBF
       ↓
Physics-informed Training + Sparse Supervision
       ↓
Vertex-Restricted Control Search
       ↓
GPU Parallel Tree Search
       ↓
Safe Control / Avoidance
```

作者还通过 residual architecture 约束 learned CBF 不超过给定 constraint function，避免网络产生“比原始几何约束更乐观”的安全区域。([论文](https://arxiv.org/abs/2609.12831))

### 结果与硬件

工作评估 15 个不同系统，并包含移动机器人与行人的真实避障实验。

这比单纯在低维 double-integrator 上验证更有说服力，但依然要正确理解“安全保证”的边界：保证依赖动力学、控制集合和状态估计误差模型是正确的。

### 工程风险

真实机器人常见问题是：

```text
state estimate 有 bias
actuator saturation 比模型更严格
delay / rate limit 没进 dynamics
障碍物未来运动估计错误
```

如果这些没被 barrier 模型覆盖，数学上满足 CBF 不等于物理世界一定安全。

### 适合谁关注

安全 MPC、RL safety shield、无人机 / 四足避障、learned local planner、端到端控制的独立安全层。

### 工程落地启发

很适合形成一个统一接口：

```text
Policy / MPC Proposal
        ↓
CBF Safety Filter
        ↓
Actuator Command
```

学习策略负责效率，CBF 层负责定义清楚的安全边界。今天的新工作与经典 CBF-QP 放在一起读尤其合适，后面的经典论文回顾会专门展开这一点。

## 4. ASTRIL-MPC：LLM 可以调控制器，但不应该直接越过 MPC 生成履带动作

**今日 arXiv 公开批次；v1 提交于 2026-09-11 17:17 UTC。**

### 为什么重要

履带式搜索救援机器人面对台阶、斜坡、碎石和高度突变时，固定权重 NMPC 很难覆盖所有地形；但完全用 RL / LLM 端到端输出控制，又很难保证可行性和碰撞约束。

ASTRIL-MPC 给出了一个比较合理的折中：

```text
Terrain Height Sequence
+ Recent Robot Trajectory
        ↓
Learned Kinematics Predictor
        ↓
NMPC
→ 负责显式约束与可行性
        ↑
Bounded LLM Adaptation
→ 只修改少数 Weight / Bound
```

### LLM 的权限边界

最值得关注的是接口设计。LLM 的更新必须经过：

```text
range clipping
rate limiting
consistency checks
```

也就是说，它可以提出“地形危险时更重视稳定性”一类高层参数调整，但没有权绕开 NMPC 直接输出履带速度。

这比“让大模型直接控制机器人”更接近真实产品架构。

### 实时性与结果

论文报告编译后的神经 predictor + MPC 完整 control cycle **小于 100 ms**。

实验中，相对 non-adaptive NMPC，aggregate traversal quality 最高提高约 **71%**；相对 PPO 最高提高约 **67%**，并消除了下降阶段可测的碰撞冲击。([论文](https://arxiv.org/abs/2609.13083))

### 动力学与工程风险

learned kinematics 仍然是系统辨识模型。如果机器人换履带、负载、摩擦条件或地形材质明显变化，模型误差可能直接进入 MPC prediction。

另外，LLM 只要能改 cost / bound，就仍然拥有“软权限”。建议所有 adaptive update 都保存：

```text
old_value
new_value
reason
allowed_range
rate_limit
validation_result
rollback_value
```

### 适合谁关注

履带救援机器人、复杂地形移动机器人、MPC + learned model、想把 LLM 放入机器人但又不想让它触碰实时控制底层的团队。

### 工程落地启发

Agent 与控制器之间最合理的接口往往不是：

```text
set_velocity(vx, vy, wz)
```

而是：

```text
request_controller_profile(
  risk_weight,
  speed_limit,
  clearance_margin
)
```

底层依旧由确定性控制器决定怎样执行。

## 5. LIT：VLA 想提高 OOD 泛化，先切断“看见背景就直接猜动作”的捷径

**今日 arXiv 公开批次；v1 提交于 2026-09-11 09:42 UTC。**

### 为什么重要

大量 VLA 在训练环境里成功率很高，但换相机、换背景、换灯光就明显掉点。一个原因是模型可以走视觉捷径：

```text
某种背景 / 纹理 / 相机视角
        ↓
直接关联某段训练动作
```

它并没有真正学到“视觉告诉我目标几何在哪里，然后据此控制”。

LIT 通过两阶段训练人为切断这条 shortcut。

### 训练结构

**Stage 1：动作先脱离视觉学会。**

Action Expert 不看图像，只读取：

```text
Language
Robot State
Terminal SE(3) Pose
```

学习从任务目标几何到动作的映射。

**Stage 2：视觉只能通过 Latent Interface 进入。**

```text
Image / Semantic Feature
        ↓
Pose-Supervised Latent Interface
        ↓
Action Expert
```

因此视觉信息必须先形成与目标 pose / geometry 更一致的中间表示，不能直接连到 action head。([论文](https://arxiv.org/abs/2609.12641))

### 结果

项目页报告，在 π0.5、MolmoAct2、FAST-WAM、ImageWAM 上，LIBERO-Plus overall 提升约 **3.87–10.70 个百分点**；真实机器人未见 camera / lighting / distractor 条件下提升约 **13.3–16.7 个百分点**。([项目页](https://magiclab-nus.github.io/LIT/))

### 工程风险

LIT 假设 terminal SE(3) pose 是一个足够好的“动作语义瓶颈”。对强接触、柔性物体、旋拧、插拔等任务，单个终端 pose 未必包含足够的 force / contact-state 信息。

因此更通用的 latent interface 未来可能需要：

```text
pose
contact state
force intent
object relation
phase
```

### 适合谁关注

VLA、Diffusion / Flow action policy、相机域变化、机器人 OOD 泛化。

### 工程落地启发

与其无限增加视觉 augmentation，不如先检查策略结构里有没有“视觉直接到动作”的短路。可以尝试让视觉先预测 task-space waypoint / pose / relation，再让动作模型消费这个结构化中间量。

[代码](https://github.com/MAGICLAB-NUS/LIT)

## 6. DWMP：身体动力学和视觉世界，不一定应该由同一个 World Model 学

**今日 arXiv 公开批次；v1 提交于 2026-09-11 02:13 UTC。**

### 为什么重要

人形越障需要同时预测两类完全不同的信息：

```text
Proprioception
→ 关节 / 速度 / 身体动力学如何演化

Depth / Vision
→ 障碍几何和未来可见环境怎样变化
```

如果强行把两类模态塞进同一个黑盒 latent dynamics，它们不同的时间结构和可预测性可能互相干扰。

DWMP 使用 **Dual World Models**。

### 算法模块

```text
Proprioceptive History
        ↓
Koopman-based Latent Dynamics
→ 尽量让时间演化接近线性

Depth Observation
        ↓
RSSM Visual World Model
→ 学视觉 / 几何时序状态

两种 Latent
        ↓
Fusion
        ↓
Student Locomotion Policy
```

([论文](https://arxiv.org/abs/2609.12347))

### 传感器与动力学假设

Koopman latent 并不是说真实人形动力学线性，而是寻找一个更适合近似线性演化的隐藏表示。

视觉 world model 则依赖 depth 对障碍结构的持续观测。透明 / 镜面、强遮挡或深度失效仍可能破坏环境预测。

### 真机与鲁棒性

作者进行了随机障碍布局仿真，并部署到 **Unitree G1** 实机。

值得注意的是，这种结构天然允许未来分别诊断：

```text
proprioceptive model error
visual model error
fusion error
```

比一个统一 latent 出错以后完全不知道是哪种模态造成的，更适合产品调试。

### 适合谁关注

人形越障、四足 locomotion、world-model policy、多模态预测控制。

### 工程落地启发

多传感器系统不一定总应该做“越早融合越好”。如果不同模态的动力学规律完全不同，可以先各自形成可解释的 predictive state，再在 policy 层融合。

这与传统状态估计中的“每种传感器有自己的 measurement model”其实是一脉相承的。

## 7. GraphAHA：Coding Agent 的 Test-Time Compute 应该复用搜索历史，而不是不断从零采样

**今日 arXiv 公开批次；v1 提交于 2026-09-11 12:08 UTC。**

### 突破性工程价值

给 Coding Agent 更多 test-time compute，最简单的方法是：

```text
生成 N 个候选
运行测试
挑最好的
```

但很多候选实际上只在局部不同，大量推理和验证被重复浪费。

GraphAHA 将搜索状态组织成 typed DAG：

```text
Code Node
   ↓
Sampling / Reasoning / Implementation / Repair Action
   ↓
New Code Node
```

语义 / 行为等价的程序可以合并为同一个节点，下游成功 / 失败统计也能复用，而不是每条 trajectory 都当成完全独立经验。([论文](https://arxiv.org/abs/2609.12757))

### 搜索策略

作者使用 hierarchical Thompson sampling：

1. 先决定探索新的 successor，还是利用已有 successor；
2. 再在 heterogeneous action 中选择下一步，例如 reasoning、repair 或 implementation。

这比固定“每轮都 repair”更灵活。

### 结果

在 LiveCodeBench 和 CodeContests、Qwen2.5-Coder 与 DeepSeek-Coder 组合下，GraphAHA 在 **20 个设置中 18 个最佳**；在 visible-test 设定下，相对最强基线平均提高约 **4.1 个百分点 Pass@1**。

### 是否适合真实研发流程

概念非常适合，但生产仓库需要解决“两个 patch 是否等价”的问题。测试等价不代表真实行为完全等价，尤其涉及：

```text
并发
数据库副作用
性能
日志 / telemetry
权限
```

所以 DAG node merge 必须谨慎。

### 工程落地启发

长任务 Agent 可以保存：

```text
Patch Graph
├─ parent patch
├─ validator result
├─ failure signature
├─ reasoning artifact
└─ next actions
```

这样一个失败 patch 不是“聊天历史里的废文本”，而是后续搜索可复用的结构化负样本。

## 8. Reality Is the Final Verifier：CI 全绿，只能证明你通过了当前模型化的世界

**今日 arXiv 公开批次；v1 提交于 2026-09-10 17:58 UTC。**

### 突破性工程价值

这篇文章没有提出新 Agent，而是给 Agentic Software Engineering 一个非常有用的系统框架。

作者指出自动软件工程至少有两个永远无法完全消除的 gap：

```text
Requirement Gap
真实 stakeholder intent
≠
写下来的 issue / spec

Model Gap
真实部署环境
≠
测试 / benchmark / simulator / evaluator
```

([论文](https://arxiv.org/abs/2609.12039))

### 为什么对 Coding Agent 很关键

Agent 越擅长优化 evaluator，就越容易找到 evaluator 的盲区。

例如：

```text
所有单元测试通过
但性能退化 10×

SWE-bench 测试通过
但破坏未覆盖 API

sandbox 正常
但生产数据库规模不同
```

这不是单纯“模型 hallucination”，而是 evaluator 对现实世界本来就只是近似。

### 建议的 Assurance Loop

更合理的生命周期是：

```text
Requirement
    ↓
Agent Implementation
    ↓
Test / Simulation / Evaluation
    ↓
Deployment Evidence
    ↓
发现 Requirement Gap / Model Gap
    ↓
更新 Requirement / Model / Evaluator
    ↓
下一轮
```

部署不是验证链终点，而是下一轮规范更新的数据来源。

### 权限、安全与可验证性风险

这并不意味着“测试不重要”。相反，测试仍然是最便宜的 verifier，只是不能被误认为现实本身。

高风险 Agent 应明确记录：

```text
what_was_verified
what_was_not_verified
assumptions
production evidence
rollback criteria
```

### 适合谁关注

Coding Agent 平台、自动修复、自动部署、长期 Agent、机器人软件远程升级。

### 工程落地启发

对 Vibe Coding 最实用的一条原则是：**Definition of Done 不能只写“tests pass”。**

应该至少再问：

```text
真实用户路径是什么？
真实数据规模是什么？
有哪些环境差异没有进入测试？
上线后哪个 telemetry 会证明我们错了？
```

## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### 1. 双 Agent 不要“同题双跑”：Maker / Reviewer 分工，Reviewer 必须看原始需求

**来源：2026-09-11 开发者实战文章。**

一篇近期 Claude Code + Codex 联合工作流文章给出的高价值经验是：不要让两个 Agent 都完整做一遍同一任务，而是让一方执行、一方用 fresh context 独立审查。Reviewer 不应只读执行 Agent 的总结，而要同时读取**原始需求、实际改动和检查结果**，否则很容易继承执行者自己的 framing。

并行时按真实文件路径划分 ownership；不同 worktree 只能隔离工作区，不能自动避免两个 Agent 同时改同一文件后的覆盖或冲突。共享文件应采用“先写、后审”的串行流程。

**今天可以直接用：** handoff 固定为 `Goal / Decisions / Do not change / Files changed / Checks run / Still open`，并把原始 brief 一起交给 Reviewer。

**边界：** 这是个人开发者工作流经验，不是严格 benchmark；第二个 Agent 会增加 token / 额度消耗，只有真正承担独立验证职责时才值得。

[原文：Claude Code and Codex Together: How to Split the Work](https://have-been.com/en/posts/claude-code-codex-together)

### 2. Front-load：Research → Plan → Task → Implementation，聊天可丢，Artifact 不能丢

**来源：2026-09-06，2026-09-10 更新的 Codex 工作流文章。**

这篇文章最值得借鉴的原则是：上游研究和架构假设一旦错了，Agent 会在后续实现中把错误不断放大，因此人工注意力应前置，而不是等几小时代码生成后再靠 patch 补救。

推荐把流程固定成：

```text
Research（只读探索）
→ Plan（持久架构文档）
→ Task（Goal / Dependencies / Paths / Acceptance / Validation）
→ Implementation（Fresh Session）
```

真正持久的状态是 **Task Registry + Append-only Activity Log + Git State**，不是聊天历史；`AGENTS.md / CLAUDE.md` 也更适合只保留经过真实失败证明必要的短规则。

**今天可以直接用：** 建 `research.md`、`plan.md`、`tasks/TASK-xxx.md` 和 `activity.log`；每个 Task 必须带验收命令，新任务尽量从 fresh session 开始。

**边界：** 具体 CLI 命令会随版本变化；应复用的是“前置验证 + Artifact 化 + Fresh Session”的结构。

[原文：Front-Load or Fail — The Four-Phase Coding Agent Workflow](https://codex.danielvaughan.com/2026/09/06/front-load-human-review-phased-coding-agent-workflow-codex-cli/)

### 3. 社区经验：架构、边界和 Edge Cases 先由人想清楚，再把 Implementation 交给 Agent

**来源：2026-09-07 Reddit 讨论；属于社区经验，不作为 benchmark 结论。**

这条实践可以概括为 **Human-owned Design Checkpoint**：在 Agent 获得写权限前，先由人把 architecture、关键接口、edge cases、trade-offs 和 definition of done 想清楚。之后可以高强度让 Agent 写代码，但 review 要回到原始需求和设计 artifact，而不是只问“测试是不是绿了”。

**今天可以直接用：** 在写权限前确认一份短 `DESIGN.md`，至少包含：

```text
Goal
Non-goals
Architecture
Key interfaces
Edge cases
Trade-offs
Definition of done
```

**边界：** 这是社区个人经验，不是控制变量实验；更适合作为保持系统理解和审查能力的工作习惯。

[Reddit 讨论：I am done with the everyday’s work using just claude/codex](https://www.reddit.com/r/developersIndia/comments/1w9w2jh/i_am_done_with_the_everydays_work_using_just/)

## 经典论文回顾

### Control Barrier Function Based Quadratic Programs for Safety Critical Systems：把“安全”变成控制器每一拍都必须满足的约束

Aaron D. Ames、Xiangru Xu、Jessy W. Grizzle 与 Paulo Tabuada 的 **Control Barrier Function Based Quadratic Programs for Safety Critical Systems** 于 2016 年在线发表、2017 年刊于 IEEE Transactions on Automatic Control。它是现代 CBF Safety Filter、Safe RL shield 与许多安全 MPC 工作的重要基础之一。([DOI](https://doi.org/10.1109/TAC.2016.2638961)，[arXiv](https://arxiv.org/abs/1609.06408))

### 核心问题

传统稳定控制常问：

```text
系统能不能收敛到目标？
```

安全控制还必须先回答：

```text
在去目标的过程中，状态会不会进入危险集合？
```

论文使用 barrier function 定义安全集合，例如：

```text
C = { x | h(x) >= 0 }
```

并通过对 `h(x)` 的导数施加条件，保证闭环系统不会穿过安全边界，即获得 forward invariance。

### CBF-QP 的关键结构

对 control-affine system：

```text
x_dot = f(x) + g(x)u
```

CBF 条件可以转化为对 `u` 的线性不等式。

于是每一个控制周期都可以解一个很小的 QP：

```text
minimize    ||u - u_nominal||²

subject to  CBF safety constraints
            actuator limits
```

如果同时加入 Control Lyapunov Function，还可以把“朝目标收敛”作为 performance objective / soft constraint：

```text
Nominal Controller / Planner
          ↓
CLF-CBF-QP
          ↓
尽量保持原动作
同时强制 Safety
```

### 动力学与传感器假设

经典 CBF 的安全保证依赖几个关键条件：

- 动力学模型足够准确；
- `h(x)` 确实表达了真实危险边界；
- 状态估计误差没有超出建模范围；
- 求解频率、执行器 delay 和 saturation 没有破坏连续时间假设。

所以 CBF 不是“写一个不等式就自动绝对安全”。

### 当年为什么重要

它把安全从 planner 的隐含 cost 变成了**运行时显式约束**。

这让系统可以采用非常激进甚至学习式的 nominal controller，只要最后一层安全滤波器能够确保动作仍处于可接受集合。

### 今天仍然在使用的思想

今天大量系统都仍然沿用：

```text
Policy / RL / MPC / Human Command
            ↓
Safety Filter
            ↓
Actuator
```

尤其是：

```text
Safe RL
Learning-based CBF
Robust / Measurement-aware CBF
Multi-agent collision avoidance
VLA action safety
```

今天的 VertexCBF 就是在解决经典 CBF 面对高维、复杂 value function 时的计算问题。

### 已被后续扩展的部分

现代研究已经加入：

```text
High-Order CBF
Robust CBF
Stochastic CBF
Measurement-Robust CBF
Learned / Neural CBF
Reachability + CBF
Differentiable Safety Layer
```

并开始更加认真地处理模型误差和感知不确定性。

### 公开代码与可复现性

现代开源工具中可以参考 [CBFKit](https://github.com/bardhh/cbfkit)，它提供 JAX / Python 的 CBF / CLF 组件和 ROS 2 相关接口，适合快速搭建实验。

### 对当前工程项目的重新解读

对无人机、机器狗和 VLA，我更推荐把 CBF 理解成一种**权限边界**，而不是主控制器：

```text
上层算法可以自由提出动作
但只有满足可证明安全条件的动作
才允许真正进入执行器
```

它与 Coding Agent 的 capability gate 很像：模型可以“建议”，但最终执行权必须经过独立、可检查的约束。

对低线数 LiDAR / SLAM 系统，还要特别注意安全边界应考虑地图和定位误差；如果障碍位置本身有 ±20 cm uncertainty，那么 `h(x)` 里的障碍几何也必须相应膨胀，而不是拿点估计直接做形式安全声明。

## 今日结论

今天 SLAM 最值得带走的不是某个新前端，而是两个更贴近长期工程的问题：**跨会话地图如何持续积累**，以及**成熟 LIO 到底哪些参数真正值得调**。Chain-SLAM 把 session 变成图中的长期对象；参数敏感性工作则提醒我们，在换算法以前，先把现有算法的敏感维度测清楚。对于已经能跑起来的 LIO-SAM / FAST-LIO2 系统，这两项往往比继续追逐“最新前端”更容易产生真实产品收益。

控制侧今天形成一条非常清楚的分层：

```text
Learned / LLM Proposal
        ↓
Model-based Optimization
        ↓
CBF / Reachability Safety Gate
        ↓
Low-level Controller
        ↓
Hardware Protection
```

ASTRIL-MPC 说明 LLM 可以调 controller profile，但不应直接输出底层动作；VertexCBF 与经典 CBF-QP 则进一步说明，Safety Gate 最好具有与上层生成模型不同的数学结构和失败模式。

VLA 侧的 LIT 与 DWMP 都在反对“所有信息全部丢进一个大网络自然就会学好”。LIT 强制视觉先经过几何语义接口；DWMP 则让 proprioception 与 depth 使用不同 world model。未来机器人基础模型很可能继续变大，但真正稳定的产品栈会同时变得**更模块化、更可诊断**。

AI Coding 侧今天最有价值的共同主题是：**搜索历史与现实证据都应该成为持久资产。** GraphAHA 不再把每次候选代码当成孤立 rollout，而是构成可复用的 patch graph；Reality Is the Final Verifier 则提醒我们，测试通过只是当前 evaluator 下的证据，真正的部署结果还要反向更新 requirement 和 verifier。

这也和社区精选里的三个实践高度一致：

```text
原始需求要保留
设计 Artifact 要保留
Patch / Test / Failure 要保留
聊天上下文可以随时重开
```

真正适合长期 Vibe Coding 的不是一个永不结束的超长 session，而是一套可以被新 Agent 重建状态的持久 Artifact。

## 最值得深入研究或尝试复现的方向

1. **Multi-session LIO Sidecar。** 保留现有 LIO 前端不动，把每次任务保存成 session keyframe graph；后台单独做 GNSS / coarse prior + ICP verified inter-session factor。先 shadow 运行，不立即改正式地图，重点统计错误约束和地图变化导致的 factor 老化。

2. **自己的 LIO 参数敏感性矩阵。** 对 16 线 LiDAR / MID360 分别在长走廊、坡地、空旷区做小型参数 grid，再用 permutation importance 排 Top-3。以后优化只围绕真正敏感的参数，而不是全量手调。

3. **Policy → CBF Safety Filter。** 选一个二维 / 低维移动机器人任务，用现有 local planner 或 RL 产生 nominal action，CBF-QP 做最后安全过滤；同时人为加入定位 bias 和 actuator delay，测“理论 safe”与“真实 safe”之间差多少。

4. **VLA Latent Interface A/B。** 不立刻重训大 VLA，只在视觉和 action head 中间加入 waypoint / terminal pose / object relation 监督，测试换相机、换背景、换光照后的性能是否比纯 augmentation 更稳定。

5. **Coding Agent Patch Graph。** 每次 Agent 尝试保存 parent patch、failure signature、validator result、reasoning artifact 和下一步动作；遇到重复失败不再从零开始，而是让新的 Agent 先遍历历史 patch graph。同时把线上 telemetry 作为 evaluator 更新的正式输入。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [Chain-SLAM](https://arxiv.org/abs/2609.12221) · [项目页](https://ai4ce.github.io/Chain-SLAM/) · [代码](https://github.com/ai4ce/Chain-SLAM)
- [Parameter Sensitivity Analysis for Aerial LiDAR-Inertial Odometries](https://arxiv.org/abs/2609.12837)
- [VertexCBF](https://arxiv.org/abs/2609.12831)
- [ASTRIL-MPC](https://arxiv.org/abs/2609.13083)
- [Latent Interface Training](https://arxiv.org/abs/2609.12641) · [项目页](https://magiclab-nus.github.io/LIT/) · [代码](https://github.com/MAGICLAB-NUS/LIT)
- [DWMP](https://arxiv.org/abs/2609.12347)
- [GraphAHA](https://arxiv.org/abs/2609.12757)
- [Reality Is the Final Verifier](https://arxiv.org/abs/2609.12039)
- [Claude Code and Codex Together: How to Split the Work](https://have-been.com/en/posts/claude-code-codex-together)
- [Front-Load or Fail — The Four-Phase Coding Agent Workflow](https://codex.danielvaughan.com/2026/09/06/front-load-human-review-phased-coding-agent-workflow-codex-cli/)
- [Reddit：I am done with the everyday’s work using just claude/codex](https://www.reddit.com/r/developersIndia/comments/1w9w2jh/i_am_done_with_the_everydays_work_using_just/)
- [Control Barrier Function Based Quadratic Programs for Safety Critical Systems](https://doi.org/10.1109/TAC.2016.2638961) · [arXiv](https://arxiv.org/abs/1609.06408) · [CBFKit](https://github.com/bardhh/cbfkit)
