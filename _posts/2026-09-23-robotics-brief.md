---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-23"
date: 2026-09-23 09:00:00 +0800
description: "本期关注可分离稀疏 SLAM 优化、AUV 距离辅助初始化、G1 机载预测动作扩散、统一可行性距离场、图像直达 SE(3) 规划、VLA 低比特量化、Coding Agent 记忆实证，以及 GPT-6 Sol/Luna 与 Claude Opus 5.5。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-23

## 摘要

截至 2026-09-23 早间（Asia/Shanghai），arXiv Robotics 最新公开批次是 **2026-09-22（周二）**，当天 Robotics 列表有 210 条，Software Engineering 也在同日刷新。本期先对 `robotics-brief-covered-items.md` 做强制查重，再从最新批次和最近 7 天中筛选尚未覆盖的工作。由于下面多数论文的 v1 实际提交于 9 月 20–21 日 UTC，距离本期生成时间已经超过 24 小时，因此统一按规范标为“时间回补”，不把 arXiv 的公开批次日期误写成论文首次提交日期。

今天 SLAM / 状态估计侧最值得关注的是两种“先利用结构，再做非线性优化”的路线。**SPARSER** 重新把 Variable Projection 带回大型机器人感知问题：当 landmark、transponder 等变量在固定 pose 后线性可解时，不必把所有变量一起交给通用 NLS；它用 matrix-free Schur operator 同时利用可分离结构与稀疏性，并专门处理 SLAM 常见的 gauge symmetry。论文在 SLAM、SfM、sensor-network localization 上平均获得 5–7× CPU/GPU 加速，个别数据集超过 40×。另一篇 **Range-Aided SLAM Initialization** 则利用 AUV 上通常很准的航向信息，把距离辅助 SLAM 的初始化拆成 GTRS + 线性最小二乘两步；它的价值不是替代完整后端，而是给非线性 RA-SLAM 一个更可靠的起点。

控制与规划侧今天同样强调“把隐含结构显式化”。**PredActor** 用 joint state-action diffusion 在内部同时预测未来状态与动作，但部署时只执行动作，不需要单独 motion-reference tracker；经过 rolling denoising 和延迟补偿后，Unitree G1 + Jetson Orin NX 的完整 callback median 16.790 ms、p95 19.383 ms，进入 50 Hz 机载控制预算。**Feasibility Distance Fields** 则试图把碰撞、关节限位、dexterity、compliance、payload torque、dynamic manipulability 等异构约束都转成同一个 joint-space metric 下“离不可行集合还有多远”的量，从而让不同安全裕度真正可比较。

规划方面，**SE(3) Neural Potential Fields** 不在部署时显式重建完整 3D 场景，而从 posed RGB 学一个六自由度势场；训练时用由图像恢复的 free-space geodesic navigation function 监督，从根本上减少传统人工势场的梯度抵消、贴障与停滞问题。UR10 两个桌面场景中，所有测试起点都能收敛到抓取位姿 3 cm 内，规划约 2 s，而基于重建的 RRT* 为 67–133 s；但作者也明确指出，主要部署优势来自省掉稠密重建后的碰撞检查，而不是证明“神经规划器本身比 RRT* 算法复杂度低几十倍”。

机器人基础模型工程侧，**FoldQuantVLA** 给了非常实用的端侧量化数据：W4A4 在 Jetson AGX Orin 上相对浮点 TensorRT 获得 1.20–1.33× 加速；完全统一 W4A4 会明显损害真实机器人动作质量，而把 language attention-output 与 FFN down projection 保留成 W8A8，GR00T N1.7 四项真机任务成功率从 80.0% 恢复到 92.5%，代价只有约 1 ms Orin 延迟。它说明 VLA 量化不能只看 perplexity 或离线 action error，最终要用真实 episode 成功率决定哪些层必须保精度。

AI Coding 侧，**VibeMemBench** 是今天最值得读的负结果之一。111 个真实 repository target、90 个 SWE-rebench V2 仓库和 3,634 条历史 trajectory 显示：如果直接把已经验证“确实有用”的历史经验注入 Agent，4/5 held-out solver 的 task resolution 可提高 1.1–4.5 个百分点，并减少所有 solver 的步骤；但让四个现有 memory system 自己从同样历史构建和检索记忆时，12 个 solver×memory 组合里有 11 个没有超过 matched memory-off baseline。结论不是“记忆没用”，而是“有用经验存在”和“现有检索系统能把它送到正确任务”是两件完全不同的事。

模型侧 9 月 22 日有两条真正的新发布：OpenAI 发布 **GPT-6 Sol / Luna**，Anthropic 发布 **Claude Opus 5.5**。两家公司都把重点放到了 coding / agentic work 的单位成本与长任务效率。厂商 benchmark 适合用来决定“值得不值得纳入自己的回归集”，不应直接当成自己仓库里的模型排名。本期后面给出更适合工程团队的选型方式。

最新公开列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

## 1. SPARSER：SLAM 后端不一定要把所有变量一起优化，可分离变量应该先被消掉

**时间回补：v1 提交于 2026-09-21 14:52 UTC。**

### 为什么重要

机器人感知中的非线性最小二乘经常同时包含两类变量：

```text
非线性变量：camera / LiDAR / robot poses
线性或条件线性变量：landmarks、某些网络节点、部分 calibration variables
```

传统 BA / factor graph 会利用 Jacobian 稀疏性，但仍然把这两类变量都放进同一个大问题。Variable Projection（VarPro）更进一步：如果固定 pose 后某组变量可以解析或线性求解，就先把它们消掉，只优化真正的非线性自由度。

问题在于，标准 VarPro 在 SLAM 中会遇到 gauge symmetry：整个地图一起平移 / 旋转，代价并不变；再叠加稀疏大规模结构后，直接套经典 VarPro 很难高效实现。

### 算法模块

SPARSER 的关键结构可以概括为：

```text
Separable robotic NLS
        ↓
identify conditionally-linear variables
        ↓
analytical / linear elimination
        ↓
Matrix-free Schur Complement Operator
  ├─ reduced cost
  ├─ reduced gradient
  └─ Hessian-vector product
        ↓
iterative nonlinear solver
```

它不显式形成一个巨大的 dense reduced Hessian，而是提供 matrix-free operator，因此能同时保留 sparsity 与 separability 的收益。论文还分析了 IRLS robust loss，说明常用鲁棒代价并不会完全破坏可利用结构。

### 实时性与结果

论文覆盖 synthetic / real SLAM、sensor-network localization 和 SfM：

- CPU / GPU 平均约 **5–7×** 加速；
- 个别数据集超过 **40×**；
- outlier-corrupted multi-robot SLAM 中，robust 版本相对论文采用的 GNC 基线约 **2–16×** 更快。

作者声明开源 C++ 实现和数据集，但当前最稳定的一手入口仍是论文页；工程评估时应以实际仓库 release 状态为准。

### 传感器 / 模型假设

SPARSER 不是一个新的 LiDAR 前端或视觉 feature，它要求问题本身存在**条件可分离结构**。如果所有状态都以强非线性方式耦合，VarPro 没有变量可以便宜地消掉，收益自然会下降。

### 鲁棒性与工程风险

最大的工程风险不是数值精度，而是错误地判断“哪些变量真的线性”。另外 gauge handling、robust weighting 和 marginalization 之间的交互要认真测试；一个离线 benchmark 上非常快的 reduced solver，如果和现有 incremental backend 生命周期不匹配，也不一定值得直接替换 iSAM2 / Ceres。

### 适合谁关注

GTSAM / Ceres 后端、视觉 BA、多机器人 SLAM、大规模传感网络定位，以及正在遇到“前端够快但后端越来越贵”的团队。

### 工程落地启发

最现实的尝试不是立刻重写 LIO-SAM，而是先审查自己的优化变量：

```text
哪些变量在固定 pose 后可以线性求？
哪些变量只是因为历史代码习惯才被一起塞进 NLS？
```

先在离线 replay 上做 full-NLS vs reduced-NLS A/B，记录 wall-clock、迭代数、最终 cost 与数值稳定性，再决定是否进入在线后端。

[论文](https://arxiv.org/abs/2609.24708)

## 2. Range-Aided SLAM Initialization：AUV 航向已经很准时，不要让 SLAM 再从最困难的全非线性状态起步

**时间回补：v1 提交于 2026-09-21 16:24 UTC；已接收 OCEANS 2026。**

### 为什么重要

水下 AUV 很常见的一种传感器组合是：INS 能给出很准的 heading，但绝对位置仍依赖 LBL / acoustic range。此时一般 RA-SLAM 如果仍把 heading、robot positions、transponder positions 全部从差初值交给非线性优化，容易把一个本来具有额外结构的问题做得过于困难。

这篇工作的核心是承认一个事实：**已知 heading 后，SLAM 的一大部分位置关系变成条件线性。**

### 算法模块

```text
accurate INS heading
+ nonlinear LBL range measurements
        ↓
Step 1: GTRS
estimate transponder positions relative to AUV
        ↓
Step 2: Linear Least Squares
relative transponders + known heading
→ global transponder / AUV positions
        ↓
initial state for nonlinear RA-SLAM
```

第一步用 Generalized Trust Region Subproblem 处理非线性 range geometry，第二步则退化成线性 least squares。

### 传感器假设

这项方法有非常明确的适用前提：**heading 足够准。** 论文场景是 AUV + LBL ranges + INS heading。它不是通用“无条件 SLAM 初始化器”；如果 heading 本身有明显 bias，整个线性化结构会把偏差直接带进位置初值。

### 实时性与鲁棒性

初始化算法只在启动 / 重初始化阶段执行，不是每帧高频里程计，所以工程重点不是微秒级 latency，而是：

```text
initial position error
nonlinear solver convergence rate
heading bias sensitivity
range outlier sensitivity
```

论文在真实 AUV 数据上验证了方法有效性。

### 可复现性与风险

对于已有 LBL + INS 系统，复现成本不高；真正需要补的是对声学 range outlier、声速误差和 heading bias 的故障注入。否则在“干净航向 + 干净测距”上初始化很好，进入真实海试后仍可能给后端一个偏得很稳定的起点。

### 适合谁关注

水下 AUV、声学定位、range-only / range-aided SLAM、已拥有高质量 INS 的平台。

### 工程落地启发

这篇论文也给普通机器人一个通用原则：

> 如果某个自由度已经由另一传感器高置信确定，就不要为了算法“统一”而强迫后端重新从零联合猜所有自由度。

把可观测性强的状态先固定 / 强先验化，再求弱状态，往往比一开始就做全量黑盒 NLS 更稳。

[论文](https://arxiv.org/abs/2609.24846)

## 3. PredActor：人形扩散控制开始把“未来状态”留在模型内部，而不是再外接一套 motion tracker

**时间回补：v1 提交于 2026-09-21 16:20 UTC。**

### 为什么重要

人形生成式控制常有两种极端：

```text
Motion Generator
→ 生成参考运动
→ 独立 Tracker 执行
```

或者：

```text
Action Diffusion
→ 直接输出动作
→ 但缺少可用于 test-time steering 的未来状态
```

PredActor 试图把两者合并：联合预测 future state + action，但 future state 只作为模型内部的可指导 representation，真机只执行 action，因此不再需要一个外部 full-body motion-reference tracker。

### 算法模块

```text
proprioceptive history
+ optional task context
        ↓
joint state-action diffusion
        ↓
internal future-state trajectory
  ├─ classifier guidance：test-time objective
  └─ classifier-free guidance：强化 task condition
        ↓
selected action
        ↓
direct robot execution
```

训练还采用自动 task label、perturbed teacher rollout 和 learner-state aggregation；部署侧加入 rolling denoising、precomputed mask / schedule 与 delay compensation。

### 实时性

在 Jetson Orin NX 的 zero-actuation benchmark 中：

- complete callback median **16.790 ms**；
- p95 **19.383 ms**；
- 600 次 callback 中 593 次进入 20 ms period。

这支撑 50 Hz 的实测可行性，但不是硬实时保证。项目页也明确将这一点表述为“measured 50 Hz feasibility”。

### 真机与鲁棒性

Unitree G1 上展示了：

- text-conditioned motion；
- joystick steering；
- disturbance response；
- behavior transition / semantic interpolation。

模拟中 15 个 destination target 全部到达，text retrieval score 0.580，对比 conditional action diffusion 的 0.373。

### 工程风险

内部 future state 是用于 guidance 的预测表示，不等于真实 state estimator。不能因为模型“预测未来姿态很合理”，就拿它替代 IMU / joint state / safety monitor。

另一个现实问题是 p95 已经贴近 20 ms 周期，所以 thermal throttling、CUDA contention、日志线程和其他 Jetson workload 都可能把少量 callback 推出预算。

### 适合谁关注

Unitree G1、人形全身控制、扩散策略、生成式 locomotion、希望把 language / joystick / objective steering 合并成一个控制接口的团队。

### 工程落地启发

如果已有成熟 locomotion policy，可以先复现“**内部预测用于 steering，但只输出动作**”这个接口，不必立即端到端重训整个人形。真正上线前至少记录：

```text
inference p50 / p95 / p99
control deadline miss
predicted-state disagreement
fallback activation
```

[论文](https://arxiv.org/abs/2609.24840) · [项目页](https://masteryip.github.io/predactor.github.io/)

## 4. Feasibility Distance Fields：把碰撞、力矩、dexterity 等异构约束统一成“离不可行还有多少关节空间距离”

**时间回补：v1 提交于 2026-09-21 14:13 UTC。**

### 为什么重要

机械臂控制器里经常同时存在：

```text
collision distance       → 米
joint limit margin       → 弧度
dexterity                → 无量纲
torque margin            → N·m
compliance               → 另一套指标
```

这些指标数值范围和梯度尺度完全不同，很难回答一个简单问题：**机器人当前到底离“不可行”还有多少余量？**

FDF 给出统一定义：在一个固定正定 joint-space metric 下，计算当前 configuration 到所有 infeasible configuration sets 并集的距离。

### 算法模块

论文为以下约束构造 admissible set：

- external / self collision；
- joint limits；
- dexterity；
- Cartesian / task-projected compliance；
- payload 下 joint torque；
- dynamic manipulability。

由于所有 field 使用同一个 metric，不同约束可以直接 pointwise minimum：

```text
FDF_total(q) = min(FDF_collision,
                   FDF_joint,
                   FDF_torque,
                   ...)
```

多机器人约束还会产生 block-sparse gradient，可以直接指出“哪台机器人该先让”。

### 理论性质与结果

基于 distance-to-set 理论，FDF 具有 1-Lipschitz 连续性；最近投影唯一处几乎处处可微，dual-gradient norm 为 1。作者进一步用 projection label + distance loss + Eikonal penalty 学 neural approximation。

UR5e / 双臂仿真中覆盖 7 类 field；8,000 个 configuration 上 mean learned gradient norm 约 0.994–0.998。24 条随机障碍路径中，external / composed collision fields 在 3 cm 内的成功率为 90.4% / 91.6%，sign error 低于 2%。

### 工程风险

统一 metric 是优点，也是设计责任：joint metric 选得不好，1 cm 末端运动和某个关节 0.1 rad 的“风险距离”可能被不合理比较。

神经近似的错误集中在 medial axis 和稀疏 boundary 附近，而这恰恰可能是 planner 最关心的狭窄区域，所以不能只看平均误差。

### 适合谁关注

机械臂轨迹优化、whole-body control、双臂协作、安全约束融合、需要统一 risk margin 的 MPC / policy safety layer。

### 工程落地启发

可以先从最简单的两类开始：

```text
collision infeasible set
+
joint-limit infeasible set
```

统一到同一个 joint metric，比较 `min-distance margin` 与当前多个手工阈值的行为差异。若统一 margin 对规划 / 降速 / stop policy 更稳定，再逐步加入 torque / manipulability。

[论文](https://arxiv.org/abs/2609.24632)

## 5. SE(3) Neural Potential Fields：从 RGB 直接学六自由度“该往哪里走”，部署时不必先做稠密 3D 重建

**时间回补：v1 提交于 2026-09-21 16:35 UTC。**

### 为什么重要

图像到机械臂轨迹通常是：

```text
RGB / RGB-D
→ 3D reconstruction
→ collision geometry
→ motion planner
```

重建误差与稠密碰撞检查都可能成为延迟来源。另一条路线是直接从图像学 potential field，但经典 artificial potential field 会遇到 attractive / repulsive gradient 抵消，导致贴障、局部停滞。

这篇工作把 potential 定义到 **SE(3)**，并用 free-space geodesic navigation function 监督，而不是仅靠“离目标欧氏距离”。

### 算法模块

```text
posed RGB images
        ↓
training-time free-space recovery
        ↓
geodesic distance to grasp
        ↓
SE(3) neural potential field
        ↓
descent in position + orientation
        ↓
6-DoF trajectory
```

部署时优化直接查询 learned field，不需要先构造完整稠密 3D reconstruction 再做每一步碰撞查询。

### 真机结果

UR10 的两个 tabletop scene：

- 所有测试起点均收敛到 grasp pose **3 cm** 内；
- 对 ground-truth geometry，执行路径全部 collision-free；
- image-supervision-only baseline 分别只有 25% / 0%；
- mean clearance 从不足 1 cm 提升到约 **8.6–8.8 cm**；
- arm-link contact 占执行 configuration 的比例从 20.6–50.4% 降至 2.7–5.5%；
- 两个场景 grasp success 为 90% / 40%，剩余失败来自 Cartesian executor refusal。

规划约 **2 s**，重建后 RRT* 为 **67–133 s**。

### 一个必须保留的边界

作者明确说明：在共同 offline harness 下两者计算更接近；部署时巨大差距主要来自 reconstruction-based pipeline 还需要稠密 collision checking。因此不能把 2 s vs 133 s 简化成“神经势场算法本身比 RRT* 快 60 倍”。

### 工程风险

learned potential 对 OOD geometry 的安全性依赖训练 coverage。即使 field 产生平滑梯度，也不等价于完整几何 collision certificate。

### 适合谁关注

视觉机械臂、抓取轨迹规划、NeRF / 3DGS 前端、想减少 reconstruction→planning handoff 的团队。

### 工程落地启发

可以先把 neural field 当 **proposal generator**：快速给出一条 SE(3) path，最后仍由 FCL / ESDF 做一次连续 collision validation。这样先吃到速度收益，又不把 safety 全压到 learned field 上。

[论文](https://arxiv.org/abs/2609.24864)

## 6. FoldQuantVLA：VLA 做 W4A4 时，真正决定可用性的不是平均误差，而是哪几层绝不能降到 4 bit

**时间回补：v1 提交于 2026-09-21 11:28 UTC。**

### 为什么重要

VLA 上 Jetson 的痛点不是模型能不能跑，而是 observation-to-action latency、显存和功耗。低比特 PTQ 很诱人，但机器人 policy 和语言模型不同：某几层只有很小数值误差，也可能在长 episode 中积累成抓取失败。

FoldQuantVLA 的核心是让 calibration、weight rounding 与 native integer execution 使用一致 activation representation，并结合：

- channel scaling；
- block Hadamard transform；
- dynamic per-token quantization；
- TensorRT W4A4 custom plugin。

不需要重新训练 policy。

### 实时性

跨三个 GR00T checkpoint 与 π0.5：

```text
Jetson AGX Orin: 1.20–1.33×
desktop Ada:     1.25–1.52×
```

相对浮点 TensorRT。

### 最有价值的真机消融

统一 W4A4 并不是最终最优。作者发现 language attention-output 和 feed-forward down projection 保留 W8A8，可以稳定改善四个 checkpoint 的 held-out action fidelity。

GR00T N1.7 四项真实机器人任务、每配置 80 trials：

```text
uniform W4A4       80.0%
mixed W4A4/W8A8    92.5%
```

代价仅约 **+1 ms Orin latency**。

### 工程风险

这类结论高度 model-family dependent。不要把“这两类 projection 保 8 bit”直接抄成所有 VLA 的永久规则。

量化 acceptance gate 至少要同时看：

```text
offline action error
closed-loop episode success
rare-state recovery
P95 latency
thermal steady-state
```

### 可复现性

论文说明了代码仓库地址，但本轮核验时该公开仓库链接仍返回 404，因此当前不把它标成“代码已可直接复现”。

### 适合谁关注

Jetson Orin、GR00T / π0.5、端侧 VLA、机器人模型压缩与 TensorRT 团队。

### 工程落地启发

真正产品化时，建议逐 block 做 sensitivity sweep：

```text
W4A4 baseline
→ 每次只把一组 block 恢复到 W8A8
→ 跑固定真机 regression tasks
→ 计算 success_gain / latency_cost
```

用真实 episode 选择 mixed precision，而不是凭语言模型量化经验猜。

[论文](https://arxiv.org/abs/2609.24433)

## 7. VibeMemBench：Coding Agent “历史经验确实有用”，但现有 Memory System 大多没能把对的经验取出来

**时间回补：v1 提交于 2026-09-20 11:44 UTC。**

### 突破性工程价值

给 Coding Agent 加“长期记忆”很容易变成一个看起来合理但无法验证的功能：检索到了一段旧总结，模型也说“有帮助”，可最终 patch 并没有更好。

VibeMemBench 强制把 memory 的价值落到**可执行 repository task**上：

- 111 个 coding target；
- 90 个 SWE-rebench V2 repository；
- 3,634 条历史 trajectory；
- bug fix、feature、interface change、configuration work；
- 最终仍由 executable tests 判断任务是否解决。

更严格的一点是：一个 target 只有在 reference setting 中证明“注入某段历史经验确实改善可执行结果”后才被保留。因此 benchmark 先确认**仓库历史里真的存在可用经验**，再测 memory system 能不能找到它。

### 结果

把 frozen、已验证有用的 experience 直接给 5 个 held-out solver：

- 4/5 solver 的 resolution 提升 **1.1–4.5 个百分点**；
- 5/5 solver 的 agent steps 都下降。

但让四个现有 memory system 自己从相同 history 建库和检索：

> 12 个 solver × memory-system 组合中，**11 个没有超过 matched memory-off baseline**。

### 这意味着什么

问题不是“Memory 没用”，而是：

```text
有价值的经验存在
≠
能正确抽取
≠
能在正确任务检索
≠
检索内容能被当前 Agent 正确利用
```

这四个阶段需要分别测。

### 权限 / 可验证性风险

长期 memory 还会产生 stale instruction、过期 API、错误 workaround 和权限信息污染。Memory item 应至少保存：

```text
source_repo_sha
source_task
created_at
validation_receipt
applicable_paths
expiry / invalidation rule
```

否则过去一次“当时有效”的修复会变成未来的隐形 prompt injection。

### 适合谁关注

Codex / Claude Code 长任务、企业代码知识库、跨 session Agent、自研 repository memory / RAG。

### 工程落地启发

先不要做复杂向量库。最好的第一版实验是三组 A/B：

```text
A: no memory
B: oracle / manually selected useful memory
C: your retrieval system
```

如果 B 明显优于 A、C 却没有，问题就在 extraction / retrieval；如果 B 都不优于 A，就不该继续堆 memory infrastructure。

[论文](https://arxiv.org/abs/2609.23570)

## 8. 9 月 22 日模型更新：GPT-6 Sol / Luna 与 Claude Opus 5.5 都在争“长任务单位成本”

**最新官方发布：均发布于 2026-09-22。**

### GPT-6 Sol / Luna

OpenAI 发布 GPT-6 Sol 与 Luna，并明确保留 GPT-6 Astra 作为最高能力档。API 价格（每百万 token）：

```text
GPT-6 Sol   input $2.00   output $10.00
GPT-6 Luna  input $0.10   output $0.50
```

官方称相对 GPT-5.6 的促销定价，两者整体价格下降约 50%。

对 Coding Agent 更值得看的不是单点榜单，而是成本曲线。OpenAI 自报 DeepSWE 1.1 中：Sol max 68.8%；Luna max 66.6%。这些数字必须视为**厂商 benchmark**，真正部署应该在自己的 harness、权限和 reasoning budget 下复测。

[OpenAI 官方发布](https://openai.com/index/introducing-gpt-6-sol-and-luna/)

### Claude Opus 5.5

Anthropic 同日发布 Opus 5.5，API ID 为 `claude-opus-5-5`：

```text
input       $4 / 1M
output     $20 / 1M
cache read $0.20 / 1M
```

Anthropic 表示典型 workload 相对 Opus 5 运行成本约低 40%，输出速度提高 30% 以上；Claude Code / API 还提供最高约 2.5× 的 fast mode，但价格为 $8 / $40 每百万 input/output token。

Anthropic 同样给出了 Terminal-Bench 4.0、FrontierCode、CursorBench 等厂商数据。更重要的是，它自己也在发布页提醒：这些高能力区间里 benchmark margin 已经越来越难代表真实工作差异。

[Anthropic 官方发布](https://www.anthropic.com/claude-opus-5-5)

### 工程上怎么选

不要根据两家公司各自图表直接指定“赢家”。更稳的 routing 方法是拿 20–50 个自己的固定任务，统一：

```text
same repository snapshot
same task brief
same tool permissions
same time limit
same verification gate
```

然后记录：

```text
resolved / not resolved
wall-clock
input/output/cached tokens
tool calls
retry count
human correction
7-day revert / fix-after-merge
```

成本已经低到可以按任务类型路由，而不是强迫所有 coding job 使用一个默认模型。

### 适合谁关注

Codex / Claude Code 重度用户、多模型 Coding Agent router、企业内部研发 Agent、需要控制长 session 成本的团队。

## AI Coding 实战技巧精选

### 技巧 1｜JetBrains 里的 Agent：先审批 Plan，再把 MCP 权限缩到“每个 Tool”

- **来源**：[GitHub Copilot for JetBrains 1.18.0 官方 Changelog，2026-09-22](https://github.blog/changelog/2026-09-22-new-features-and-improvements-in-copilot-for-jetbrains/)。
- **一句话结论**：大改动不要让 Agent 一上来就写代码；先让 Codex Agent 进入 Plan mode，审查实施路径，再只给当前任务需要的 MCP tool 持久权限。低风险调用可以 assisted approval，高风险动作继续人工确认。
- **具体怎么做**：
  1. 更新 GitHub Copilot for JetBrains 到 1.18.0；大型 refactor / 多文件功能优先用 Codex 的 **Plan mode**，在实现前 review / refine / approve 计划。
  2. 检查内置 GitHub MCP Server 是否真的需要；新版可以单独开关，不影响手工配置的其他 MCP server。
  3. 对 MCP 使用 **persistent per-tool controls**：只开放本任务真正需要的 read/search/write tool，不要按整个 server 一次性全放开。
  4. Assisted approvals 只用于低风险调用；merge、删除、发布、生产写入继续保留明确人工 gate。
- **适合什么场景**：IntelliJ / Android Studio / PyCharm 大仓库、多文件重构、Codex Agent + GitHub MCP、需要降低频繁权限弹窗但又不希望 Agent 获得全权限的团队。
- **注意**：Plan approval 只是实现前的人类检查，不是安全证明；真正的写权限仍应由 IDE / MCP / GitHub 权限层限制。

### 技巧 2｜GPT-6 长任务保持 Tool Schema 顺序稳定；要禁用工具用 `allowed_tools`，别把定义从 Prompt 里删掉

- **来源**：[OpenAI《Better prompt caching for GPT-6》，2026-09-22](https://openai.com/index/better-prompt-caching-for-gpt-6/)。
- **一句话结论**：长时间 Coding Agent 的 system prompt、project rules、tool definitions 应尽量成为稳定 prefix。工具暂时不用时，不要删除 / 重排 schema；用 `allowed_tools` 或 `tool_choice=none` 控制调用，这样更容易继续命中 prompt cache。
- **具体怎么做**：
  1. Prompt 排序固定为：`system → project rules → stable tool schemas → reference context → dynamic task/tool output`，高频变化内容尽量放后面。
  2. 不要每轮根据任务重新生成不同顺序的 tool list；需要收紧权限时保留 definitions，只改变 `allowed_tools`。
  3. GPT-6 上要临时提高 / 降低 reasoning，可追加 `configuration_update`，避免不必要地破坏可复用 prefix。
  4. 用 Prompt Caching Dashboard / diagnostics 检查 miss；若出现 `reason: tools_changed`，先对比 tool schema 和 ordering，而不是盲目缩短上下文。
- **适合什么场景**：运行数小时的 Coding Agent、多 MCP 工具、自研 Agent gateway、同一 repository context 被多个子任务复用的系统。
- **注意**：缓存只优化重复计算，不替代 context hygiene。过期的大段 repo 文本即使命中缓存，也仍然可能让模型依据陈旧状态做错事。

## 经典论文回顾

### Golub & Pereyra 1973：Variable Projection 为什么五十多年后又重新出现在 SLAM 后端

**G. H. Golub 与 V. Pereyra，SIAM Journal on Numerical Analysis，1973。**

[原论文 DOI](https://doi.org/10.1137/0710036)

### 核心问题

很多 nonlinear least-squares 模型其实是“部分非线性”：

```text
y ≈ Φ(α) a
```

其中 `α` 非线性，`a` 在线性意义下出现。

朴素做法是一起优化：

```text
min_{α,a} || y - Φ(α)a ||²
```

Variable Projection 的关键是：固定 `α` 后，`a` 有线性最小二乘最优解：

```text
a*(α) = Φ(α)^† y
```

于是可以把问题缩成只对 `α` 优化：

```text
min_α || (I - Φ(α)Φ(α)^†) y ||²
```

优化结束后再恢复 `a*`。

### 当年为什么重要

它不是简单的“少几个变量”。消掉线性参数以后，非线性优化器不再浪费迭代去学习一个本可直接求解的方向，问题的 conditioning 和计算结构都可能明显改善。

原论文还推导了 pseudoinverse 与相关 orthogonal projector 的导数，为 reduced objective 的正确梯度提供了基础。

### 和今天 SPARSER 的关系

1973 年的 formulation 面向一般 separable nonlinear least squares，没有今天机器人系统的几个麻烦：

```text
千万级 sparse Jacobian
SLAM gauge symmetry
robust M-estimation / IRLS
multi-robot graphs
GPU iterative solver
```

SPARSER 的意义就在这里：不是“重新发明 VarPro”，而是把 VarPro 改造成能与现代稀疏机器人感知后端共存的 matrix-free reduced operator，并处理 gauge-symmetric problem。

### 传感器 / 动力学假设

Variable Projection 本身与相机或 LiDAR 无关。唯一真正重要的结构假设是：存在一组变量，在另一组变量固定后可以可靠地线性 / 解析消元。

在 BA 中常见的是 landmark；在 range network 中可能是节点位置的某些块；在机器人系统辨识里也可能是线性动力学系数。

### 今天仍在使用的思想

这篇经典论文最值得保留的一句工程原则是：

> **不要把所有未知量都因为“统一接口方便”而交给同一个通用非线性优化器。**

先问哪些自由度能被解析消掉，通常比先换一个更强的 solver 更重要。

### 已被后续扩展的部分

现代系统更关注：

- sparse Schur / factor graph；
- gauge 与 observability；
- robust loss；
- automatic differentiation；
- matrix-free Hessian-vector product；
- incremental / sliding-window 生命周期；
- GPU 并行。

因此 1973 原算法不是今天直接拿来替代 GTSAM 的软件库，而是一个优化建模思想。

### 可复现性

最容易做的复现是选一个小 BA / calibration 问题，做两版：

```text
A: full nonlinear variables
B: conditionally-linear variables eliminated
```

统一 stopping criterion，比较：

```text
iterations
wall-clock
peak memory
final residual
sensitivity to initialization
```

再逐渐加 robust loss 与 gauge-free parameterization，就能直接理解为什么今天 SPARSER 仍然能从这条老路线获得数量级收益。

### 对当前工程项目的重新解读

对于 LIO / VIO 后端，不要只问“Ceres、GTSAM、g2o 哪个更快”。更前一层的问题应该是：

```text
这个优化问题是否被建模得比实际需要更大？
```

如果可以先消掉 calibration block、landmark block 或其他条件线性状态，再讨论 solver 选型，往往比换库更有收益。

## 今日结论

今天的论文其实围绕同一条系统思想：**先识别问题结构，再花计算。**

SPARSER 利用可分离变量，Range-Aided SLAM 利用高置信 heading，Feasibility Distance Fields 利用统一 configuration metric；它们都不是简单增加网络或算力，而是把原本藏在问题里的结构拿出来，让优化器少做无效工作。

PredActor 与 FoldQuantVLA 则把这个思想推到端侧学习控制。PredActor 不再让一个 motion generator 和 tracker 互相传递难以执行的 reference，而把 future state 留在 diffusion policy 内部；FoldQuantVLA 也不追求“所有层一律 4 bit”的形式统一，而是承认少数层值得多花 1 ms 去保留闭环动作质量。真正的机器人系统往往不是结构越统一越好，而是不同模块有不同误差成本。

SE(3) Neural Potential Fields 展示了另一个越来越值得观察的方向：视觉到规划的中间表示可能从“完整 3D reconstruction”逐步变成“只为当前任务保留的可微几何场”。这不会消灭传统地图，但可能让很多高频局部操作不再为构造一个通用世界模型付出完整成本。

VibeMemBench 对 Coding Agent 的提醒尤其重要。过去几个月很多系统都在加 memory，但这篇结果说明，**Memory architecture 的第一 KPI 应该是下游 executable task improvement，而不是召回率、总结质量或“模型觉得有帮助”。** 一段经验如果不能提高真实 repo task 的解决率，就不应该因为它在向量检索里很相似而被长期保存。

GPT-6 Sol / Luna 与 Claude Opus 5.5 的发布则继续把竞争从“最高榜单分数”推向“长任务单位成本”。对真正每天跑 Coding Agent 的团队，这反而是好事：未来更适合根据任务难度动态路由模型，而不是全员固定使用最昂贵的一档。

如果把今天整期压缩成一句话：

> **高效机器人和高效 Coding Agent 的共同方向，不是给所有问题更多算力，而是尽早判断哪些状态、约束、上下文和模型能力真正值得算。**

## 最值得深入研究或尝试复现的方向

1. **SPARSER 式后端结构审计。** 从现有 LIO-SAM / Ceres 项目里挑一个离线 graph，标出 pose、landmark、calibration、auxiliary state，检查哪些变量条件线性；先做 full vs reduced solver replay，不动在线前端。
2. **统一 Feasibility Margin。** 对机械臂先只做 `collision + joint limits` 两个 infeasible set，用同一 joint-space metric 输出一个统一 margin，再把它接到降速 / stop policy，看是否比多套手工阈值更容易调。
3. **PredActor 机载 deadline audit。** 对任何 Jetson 上的生成式 policy，都记录 30 分钟 thermal steady-state 的 p50/p95/p99 和 deadline miss，而不是只测 600 次冷机 callback。
4. **VLA Mixed-Precision 真机 A/B。** 量化后不要只跑离线 action error；固定 4–6 个代表任务，逐 block 恢复 W8A8，画 `成功率收益 / 额外毫秒` 曲线，直接找自己的敏感层。
5. **Coding Agent Memory Oracle Test。** 在实现向量库前，人工挑 20 条历史经验做 oracle memory。若 oracle 能提升任务、自动 retrieval 不能，再投入 retrieval；如果 oracle 本身无收益，就停止堆 memory。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [SPARSER](https://arxiv.org/abs/2609.24708)
- [Range-Aided SLAM Initialization](https://arxiv.org/abs/2609.24846)
- [PredActor](https://arxiv.org/abs/2609.24840) · [项目页](https://masteryip.github.io/predactor.github.io/)
- [Feasibility Distance Fields](https://arxiv.org/abs/2609.24632)
- [SE(3) Neural Potential Fields](https://arxiv.org/abs/2609.24864)
- [FoldQuantVLA](https://arxiv.org/abs/2609.24433)
- [VibeMemBench](https://arxiv.org/abs/2609.23570)
- [GPT-6 Sol / Luna 官方发布](https://openai.com/index/introducing-gpt-6-sol-and-luna/)
- [Claude Opus 5.5 官方发布](https://www.anthropic.com/claude-opus-5-5)
- [GitHub Copilot for JetBrains 1.18.0](https://github.blog/changelog/2026-09-22-new-features-and-improvements-in-copilot-for-jetbrains/)
- [OpenAI：Better prompt caching for GPT-6](https://openai.com/index/better-prompt-caching-for-gpt-6/)
- [Golub & Pereyra 1973 Variable Projection](https://doi.org/10.1137/0710036)
