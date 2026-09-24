---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-24"
date: 2026-09-24 09:00:00 +0800
description: "本期关注热成像在线自适应定位、Radar-LiDAR SE(3)直接配准、果园语义3DGS、空地双模控制、Koopman MPC、VLA风险回滚、里程计不确定性评测与长时Coding Agent上下文压缩。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-24

## 摘要

截至 2026-09-24 早间（Asia/Shanghai），arXiv Robotics 最新公开批次为 **2026-09-23**，该批次包含 112 条 Robotics 条目；Software Engineering 同日有 39 条。由于本期入选论文的 v1 大多实际提交于 9 月 22 日 UTC，距离本次生成时间已超过 24 小时，因此均按规范标为“时间回补”，不包装成“今天刚提交”的论文。最新列表可查看 [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) 与 [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

今天 SLAM / 定位方向最值得关注的是三条非常不同、但可以放到同一个工程框架里理解的工作。**TM-APR** 解决热成像地点识别 / 绝对位姿回归在环境变化下在线适配太慢的问题：不走反向传播，而把 Analytic Class-Incremental Learning 与 Unscented、GMM、H∞ 等控制 / 估计思想结合，保持闭式 O(1) 更新，使在线适配延迟严格低于传感器采样间隔。**Dr-LiSA** 则第一次把 2D 旋转雷达强度图直接和 3D LiDAR 地图在 SE(3) 中做直接配准，通过 learned forward model 将候选 LiDAR submap “渲染”为雷达观测，再做光度对齐。**ArborSplat** 更进一步说明：3DGS 进入真实农业机器人后，不能只追求 photometric fidelity，而要主动为树干、棚架、果实这类“小但重要”的语义结构保留 Gaussian capacity。

控制侧今天也非常有工程味。**Learning Air-Ground Motion Control** 用历史单点 ToF、机器人状态和未来参考信息学习空中 / 地面模式切换，再用 RL 处理多地形地面跟踪；真机完成 101 m 空地混合轨迹，位置 RMSE 0.08 m。**Wheel-loader V-Cycle Automation with Deep Koopman MPC** 则把高保真仿真学到的前进 / 后退双 Koopman 模型放进 MPC，以 50 ms 控制周期完成铰接式装载机 V-cycle。两者共同说明，复杂机器人控制未必需要把完整非线性动力学实时求到极致：只要中间表示对控制足够好，学习模型可以服务于确定性规划和 MPC，而不是取代它们。

VLA 安全侧，**SafeLoop** 非常值得落地团队关注。它不修改基础 VLA 参数，而在外层增加一个轻量风险预测器，提前估计 body collision / object failure 的概率和 time-to-hazard，再在 `noop / record / rollback` 三个动作中选择。危险时机器人退回最近的安全 waypoint，再让基础策略从那里重新生成动作。在 24 个 LIBERO 任务和三项真机任务中，hazard case 大约减少 70%，同时保持基础策略控制频率和任务成功率。它比“等失败发生后再 reset episode”更接近真实机器人需要的可恢复运行时。

状态估计评测侧，**You Should Be Properly Scoring Your Odometry** 可能是今天最应该进入现有 SLAM 工程流程的一篇。作者指出 ATE / RMSE 只评价点估计，却完全无视滤波器和 smoother 本来就会输出的 covariance；一个“厘米级自信、公里级真实误差”的 estimator，普通 ATE 只告诉你它错了，却不会告诉你它错得有多自信。论文引入 strictly proper scoring rules，并提供开源 `smfeval`；四个 ground LiDAR-inertial filter 的案例里都观察到 overconfidence。

AI Coding 侧，**CliffCompaction** 直接针对百万 token 长任务。它最反直觉的设计是：压缩时**绝不重写 / 改写历史内容，只允许截断或丢弃原始内容**；下一次 compaction 仍然从原始历史重新做，而不是“压缩上一次的压缩结果”。这样可以减少 summary drift。论文报告在 bounded context 下成本最高下降 50%，同时保持或提升 Terminal-Bench 表现，并公开与 Claude Code、Codex 等 harness 无关的 API-proxy 实现。

近期通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic、Google DeepMind 与 xAI 的官方发布入口，没有发现 9 月 23–24 日需要新增报道的通用旗舰正式发布。9 月 22 日已经覆盖 GPT-6 Sol / Luna 与 Claude Opus 5.5，因此今天不重复旧发布凑数。

## 1. TM-APR：热成像定位的在线适配，不一定要靠反向传播

**时间回补：v1 提交于 2026-09-22 17:46 UTC。**

### 为什么重要

热成像对夜间、烟尘、弱可见光环境很有价值，但它的 domain shift 也很严重：季节、地表热惯性、天气、设备温升甚至一天中的时间变化，都可能显著改变视觉外观。

传统做法通常是：

```text
thermal image
   ↓
VPR / APR network
   ↓
domain changes
   ↓
再 fine-tune
```

问题是在线 fine-tune 既需要反向传播，又可能出现更新延迟大于 sensor interval 的情况。此时机器人前端继续收到新帧，模型却还在适配旧分布，很容易产生 temporal discontinuity。

TM-APR 把问题换了个角度：如果目标只是让表示 / 回归头快速适应新分布，能不能用**解析式、闭式矩阵更新**，而不是每次都做 gradient descent？

### 算法模块

论文从 Analytic Class-Incremental Learning（ACIL）出发：

```text
Thermal observation
      ↓
domain-invariant feature
      ↓
Analytic incremental update
      ↓
metric pose / place estimate
```

作者进一步指出标准 ACIL 的线性假设在极端非线性温度变化下不够，因此将三类结构嵌入更新：

```text
U-ACIL
→ Unscented propagation
→ 处理非线性传播

GMM-ACIL
→ Gaussian Mixture partition
→ 把复杂分布拆成局部模式

H∞-ACIL
→ minimax / worst-case optimization
→ 对强扰动更保守
```

核心约束是整个在线学习过程仍然维持闭式矩阵更新，而不是重新引入 backprop。

### 传感器 / 状态假设

TM-APR 面向 thermal VPR / absolute pose regression，需要已有 mapped environment 与可建立监督 / 对应关系的在线数据流。它不是完整 SLAM 后端，也不会替代 IMU、LiDAR 或因子图；更合理的定位是一个**热视觉全局重定位 / metric prior sidecar**。

### 实时性

论文给出的核心理论目标是更新复杂度 O(1)，并使 `Δt_learn < Δt_acquire`，即在线适配在下一次传感器采样之前完成。

这个约束本身非常值得工程系统学习：很多 online learning 论文只报告平均训练耗时，却不把“更新是否赶得上数据流”写成一等系统条件。

### 鲁棒性与风险

解析更新快，并不代表分布一定建模正确。GMM component 数量、Unscented 参数和 H∞ 鲁棒边界仍然会影响更新质量。

此外，绝对视觉定位最危险的情况不是“没结果”，而是**稳定地匹配到错误位置**。因此产品化时至少应输出：

```text
pose_candidate
place_confidence
domain_shift_score
adaptation_state
last_update_timestamp
```

并让后端通过 IMU / LiDAR / map consistency 验证，而不是直接把 APR pose 当真值。

### 可复现性

当前 arXiv 页面没有给出明确官方代码仓库，因此现阶段可复现性只能评为中等。最值得先复现的是它的系统约束：对现有 thermal descriptor / VPR 头，用 closed-form ridge / recursive least-squares 类更新做 baseline，测在线更新 wall-clock 是否真正低于 sensor period。

### 适合谁关注

夜间无人机、消防 / 搜救机器人、隧道与矿井定位、thermal VPR、需要在线 domain adaptation 但算力受限的边缘设备。

### 工程落地启发

在线适配模块的接口最好明确包含：

```text
update_budget_ms
sensor_period_ms
update_completed_before_next_frame
```

如果适配赶不上实时数据流，就应该跳过或降级，而不是让模型在历史数据上“越追越慢”。

[论文](https://arxiv.org/abs/2609.26766)

## 2. Dr-LiSA：让 2D Radar 直接对齐 3D LiDAR 地图，跨模态定位开始进入 SE(3)

**时间回补：v1 提交于 2026-09-22 13:50 UTC。**

### 为什么重要

雷达和 LiDAR 在长期机器人系统里天然互补：

```text
LiDAR
→ 几何精细
→ 建图质量高
→ 雨雪 / 雾 / 水滴环境受影响

Radar
→ 几何稀疏、强度难解释
→ 恶劣天气更稳
```

工程上一个很自然的目标是：天气好时用 LiDAR 建高质量地图，天气差时用 Radar 在已有 LiDAR map 上定位。

难点在于两种传感器看见的“世界”根本不同。此前 radar-to-lidar 方法往往局限在地面车辆的 SE(2)。Dr-LiSA 试图把这个问题推进到完整 SE(3)。

### 算法模块

核心不是把 radar point 与 LiDAR point 强行找对应，而是训练一个 forward model：

```text
LiDAR submap
+ candidate SE(3) pose
        ↓
Learned forward model
        ↓
Predicted radar intensity scan
        ↓
Observed radar intensity scan
        ↓
Direct photometric alignment
        ↓
SE(3) pose update
```

也就是说，先把 LiDAR 地图“翻译”到 Radar measurement space，再做直接法优化。

这和视觉 direct method 的思想非常相似：不依赖显式 feature correspondence，而优化观测空间里的整体 residual。

### 传感器与地图假设

需要：

- 已有 3D LiDAR map / submap；
- 2D spinning radar intensity measurement；
- 足够好的初始 pose，使 direct alignment 落在合理 basin；
- forward model 在当前环境 / radar 类型上有足够泛化。

它特别适合“先建图、后定位”的重复路线，而不是完全未知环境下的 radar-only SLAM。

### 结果与鲁棒性

论文在超过 90 km 公路数据上评估：相对既有 radar-lidar SE(2) 方法精度更高，同时 planar accuracy 可以和当前 radar-radar 定位竞争。

真正的工程价值在于：LiDAR map 不需要重新采 radar map，就能成为恶劣天气的定位先验。

### 实时性与风险

Direct alignment 最大风险仍然是：

```text
initial guess 太差
forward model domain shift
重复结构
radar multipath
```

都可能造成错误 basin。

因此更适合与 IMU / wheel odometry / GNSS 联合使用，将 Dr-LiSA 作为 map factor，而不是每帧独立全局搜索。

### 可复现性

当前 arXiv 页面没有提供明确官方代码，因此现阶段重点应先复现数据接口：选择一小段 LiDAR map + radar 数据，验证 forward model 的 radar prediction 是否在几何结构变化时保持可微、可优化。

### 适合谁关注

自动驾驶、矿区车辆、恶劣天气定位、Radar-LiDAR 多模态地图、希望在 LiDAR 地图上增加全天候 localization 的团队。

### 工程落地启发

长期系统的 map 不一定等于“传感器原始观测格式”。更合理的架构是：

```text
canonical geometric map
        ↓
sensor-specific forward model
        ↓
Camera / Radar / LiDAR measurement likelihood
```

这样可以把不同传感器统一到“给定地图和 pose，应该看见什么？”这个接口上。

[论文](https://arxiv.org/abs/2609.26423)

## 3. ArborSplat：3DGS 语义地图不能只优化“看起来像”，还要为细小但重要的结构保留容量

**时间回补：v1 提交于 2026-09-22 12:25 UTC。**

### 为什么重要

果园场景非常适合暴露 3DGS semantic mapping 的弱点。树干、枝条、棚架线、果实在图像中占像素很少，但对机器人却非常重要：导航 clearance、机械采摘、树体统计都依赖它们。

Appearance-driven 3DGS 容易把表示能力花在大面积叶片、背景、天空上；细结构即使语义重要，也可能因为面积太小而被 representation budget 吞掉。

### 算法模块

ArborSplat 采用 LiDAR odometry 做 tracking，然后在 Gaussian map 上直接优化语义：

```text
LiDAR odometry
      ↓
Keyframe stereo point cloud
      ↓
fit local ground plane
      ↓
class-specific height bands
      ↓
semantic evidence filtering
  ├─ reject ground-inconsistent labels
  └─ reject monocular-depth inconsistent labels
      ↓
Gaussian semantic optimization
      ↓
class-constrained refinement
      ↓
reserve Gaussian capacity for thin / underrepresented classes
```

它最值得关注的地方不是“又一个 semantic 3DGS”，而是把**representation budget 分配**和语义类别重要性绑定起来。

### 传感器假设

系统依赖 LiDAR odometry、stereo keyframe point cloud 和图像语义。地面拟合以及 class-specific height prior 对规则果园很合适，但迁移到工厂、仓库等环境时需要换成新的结构先验。

### 结果

论文在苹果、梨园的休眠、开花、采收阶段测试；12 条完整路线 ATE 都小于 0.5 m。

在共享 301 帧片段上，相对 SGS-SLAM / GS3LAM，training-view mIoU 提高 0.23–0.50，held-out mIoU 提高 0.15–0.36，同时运行快 1.7–7.5×；SemGauss-SLAM 在六组对比里都出现 GPU OOM。

### 实时性与工程风险

农业环境存在重复树行、季节变化、风吹枝叶、果实增减。即使 semantic map 更好，长期地图仍需要处理：

```text
static trunk / trellis
semi-static fruit
highly dynamic leaves / branches
```

建议不要让所有 semantic Gaussian 具有同样生命周期。

### 可复现性

当前 arXiv 页面未列出明确官方代码。复现时可以先在已有 Gaussian mapper 上做一个很小的实验：给 `trunk / cable / pipe` 等细结构设置独立 densification quota，比较在相同 Gaussian 数量预算下的召回率和 GPU 占用。

### 适合谁关注

农业机器人、语义 3DGS、细结构建图、巡检机器人、希望控制 Gaussian map 规模的团队。

### 工程落地启发

对工业场景同样适用：

```text
大墙面
→ 不需要无限 densify

细电缆 / 管线 / 阀门 / 扶手
→ 面积小但任务重要
→ 应保留 representation quota
```

地图容量应该按任务价值分配，而不是只按 photometric residual 分配。

[论文](https://arxiv.org/abs/2609.26315)

## 4. Learning Air-Ground Motion Control：单点 ToF 也可以参与空地模式切换，关键在时间上下文

**时间回补：v1 提交于 2026-09-22 15:16 UTC。**

### 为什么重要

被动轮式空地两栖飞行器很有吸引力：平地用轮子省电，障碍 / 台阶 / 断层时起飞。但如果没有复杂 3D 感知，什么时候该从 ground 切 air、什么时候落地，很容易依赖脆弱阈值规则。

这篇工作给了一个非常实用的答案：**有限感知不代表只能用瞬时阈值，时间历史本身就是感知。**

### 算法模块

模式选择器读取：

```text
single-point ToF history
+ robot state history
+ future reference
        ↓
learned temporal mode selector
        ↓
air / ground
```

地面模式则使用 RL policy：

```text
proprioception
+ future reference
        ↓
RL tracking policy
        ↓
wheel / ground command
```

通过 multi-terrain training 与 dynamics randomization，提高跨地形鲁棒性。

### 传感器与动力学假设

模式判断只使用历史单点 ToF + robot state + reference，并没有假设机载 dense depth / LiDAR。这使得系统硬件很轻，但也意味着对狭窄侧向障碍、悬空物等复杂几何仍然无法完整感知。

### 真机结果

论文报告 learned mode selector 在困难切换中优于 rule-based selector；ground controller 在所有测试条件下 position RMSE 低于 PID，并在 NMPC 失败的部分场景仍保持可用跟踪。

集成系统完成 101 m 空地混合轨迹，多次自主 mode transition，位置 RMSE 为 0.08 m。

### 鲁棒性与工程风险

最危险的是 mode switching 形成隐式状态机但没有显式迟滞：

```text
ground ↔ air
```

如果边界附近频繁抖动，会带来执行器和姿态风险。

工程上建议学习 selector 外再保留：

```text
minimum_dwell_time
mode_transition_guard
emergency_airborne_override
```

确保网络不会直接拥有无限制的模式切换权限。

### 可复现性

论文没有在 arXiv 页面给出明确代码；最简单的复现是把现有阈值 selector 替换成一个短历史 TCN / GRU，并保持底层控制器不动，专门比较 transition false-positive / false-negative，而不是一开始训练整个控制栈。

### 适合谁关注

空地双模无人机、轮式飞行器、轻量机载感知、模式切换控制、希望减少 3D LiDAR 依赖的团队。

### 工程落地启发

“传感器少”时不要只堆规则，优先把时间窗口利用起来：

```text
instant measurement
→ 容易被噪声骗

measurement history + state history
→ 可以识别趋势和阶段
```

这对楼梯计步、接触判断、狭窄走廊状态切换同样适用。

[论文](https://arxiv.org/abs/2609.26564)

## 5. Wheel-loader Deep Koopman MPC：把难建模的重型机械动力学压进可供 MPC 使用的双线性空间

**时间回补：v1 提交于 2026-09-22 15:27 UTC。**

### 为什么重要

装载机 V-cycle 是典型的 forward → reverse → forward 反复切换任务。铰接转向、轮胎-地面相互作用、载荷变化让完整动力学很难实时优化。

纯 RL 可以绕过显式模型，但调试和约束能力弱；高保真 nonlinear MPC 又可能算不动。

Deep Koopman MPC 提供了一条中间路线：从高保真仿真中学习一个对 MPC 友好的动态表示。

### 算法模块

规划层：

```text
reduced-order articulated kinematics
        ↓
forward trajectory
+ reverse trajectory
        ↓
joint optimization through shared intermediate state
```

控制层：

```text
Algoryx high-fidelity simulation data
        ↓
Deep bilinear Koopman model (forward)
Deep bilinear Koopman model (reverse)
        ↓
MPC
        ↓
trajectory tracking
```

把前进和倒车拆成两个 Koopman dynamics 非常合理，因为两种模式下轮胎和铰接动力学分布并不完全对称。

### 实时性

论文报告 MPC 在 **50 ms execution loop** 中运行，即约 20 Hz。

对重型机械而言，这已经是很实际的控制频率；不过当前证据来自高保真仿真，而不是真实装载机。

### 动力学假设与风险

最大的 Sim2Real 风险来自：

```text
soil / gravel interaction
payload mass
hydraulic delay
wheel slip
```

如果这些在 Algoryx 数据里覆盖不足，Koopman latent 即使数学上很适合线性 / 双线性预测，也可能在真实工地上出现系统偏差。

### 可复现性

当前没有明确开源代码。对已有车辆 MPC 项目，最有价值的实验是：保持 planner、constraint、cost 完全不变，只替换 prediction model，比较 physics model / neural dynamics / Koopman model 在同一 MPC horizon 下的误差与 solve time。

### 适合谁关注

工程机械、轮式机器人、铰接车辆、Koopman control、MPC + learned dynamics、Sim2Real。

### 工程落地启发

学习动力学最适合先替换：

```text
prediction model
```

而不是一次性替换：

```text
planner + constraint + controller
```

这样模型错时仍然可以从 MPC residual、constraint violation、prediction error 中诊断原因。

[论文](https://arxiv.org/abs/2609.26580)

## 6. SafeLoop：VLA 不是只能“成功或失败”，中间还应该有可回滚的安全检查点

**时间回补：v1 提交于 2026-09-22 12:22 UTC；IROS 2026。**

### 为什么重要

长时程 manipulation 中，一次小误差会累积成不可恢复失败：

```text
手臂逐渐贴近桌边
→ 碰撞

物体抓持变差
→ 继续动作
→ 掉落
```

传统 episode-level recovery 通常是在失败后 reset；但真实机器人 reset 很贵，甚至无法自动恢复。

SafeLoop 把“安全检查点 + 回滚”引入 VLA 执行层。

### 算法模块

风险预测器读取 vision + proprioception，并输出四个量：

```text
body collision probability
body time-to-hazard
object failure probability
object time-to-hazard
```

然后 controller 在三种动作中选择：

```text
noop
→ 正常继续

record
→ 当前状态足够安全，记为 rollback anchor

rollback
→ 沿 joint space 返回最近安全 waypoint
→ 重新 query base policy
```

Base VLA 完全不需要改参数，因此它是一个真正的 external wrapper。

### 结果与真机

在 24 个 LIBERO tasks、每任务 16 个 seed，以及 3 个真实机器人任务、每任务 25 次 rollout 中，SafeLoop 相对替代方法获得更好的 safety-success trade-off，hazard case 大约减少 70%，同时保持任务成功率和基础策略控制频率。

代码、训练数据与权重已经公开：仓库提供完整 rollout 收集、Qwen2.5-VL multitask predictor、三动作 decision head 与 24-task evaluation recipe。

### 鲁棒性与风险

Rollback 并不是时间机器。真实世界里：

```text
物体已经滑走
门已经打开
液体已经倾倒
```

joint-space 返回旧姿态，也不能恢复环境状态。

因此 checkpoint 最好附带：

```text
robot_state
scene_state_digest
object_pose_confidence
reversibility_class
```

只有可逆操作才允许自动 rollback；不可逆操作应改为 safe stop / human intervention。

### 实时性

论文强调保持 base-policy control rate，但预测器本身依赖视觉模型。部署时要重点记录 P95 predictor latency 和错误 hazard prediction 对控制频率的影响。

### 适合谁关注

VLA、长时机器人操作、工业机器人、机器人 Agent、希望给现有策略增加 safety wrapper 而不重训 base model 的团队。

### 工程落地启发

可以先不训练完整 SafeLoop，把 skill runtime 统一增加：

```text
checkpoint()
rollback_to(checkpoint_id)
is_reversible()
```

先把恢复机制做成基础设施，再逐步让 learned risk predictor 决定什么时候调用。

[论文](https://arxiv.org/abs/2609.26313) · [代码](https://github.com/Loule0-0/SafeLoop/tree/release/safeloop)

## 7. You Should Be Properly Scoring Your Odometry：ATE 只告诉你“错多少”，却不告诉你 estimator 是否知道自己错了

**时间回补：v1 提交于 2026-09-22 09:03 UTC。**

### 为什么重要

SLAM / odometry 评测最常见的是：

```text
ATE
RPE
RMSE
```

但 EKF、smoother、factor graph 往往同时输出 covariance。

如果一个 estimator 输出：

```text
error = 5 m
σ = 10 m
```

它虽然不准，但至少知道自己不确定。

另一个 estimator：

```text
error = 5 m
σ = 1 cm
```

则是严重 overconfidence。对控制和导航而言，第二种通常更危险，因为系统不会触发降级 / relocalization。

普通 ATE 对这两者几乎没有区分能力。

### 核心方法

论文建议使用 **strictly proper scoring rules**，把预测均值与预测分布一起评分：

```text
estimated pose
+ covariance
+ ground truth
        ↓
proper score
```

如果 estimator 不报告 covariance，这类 score 仍可以退化回 point metric；如果报告 covariance，就能同时评价准确性与 uncertainty calibration。

作者还提出 one-sided pairwise test：即使没有 ground truth，也能比较两个 estimator，并暴露至少一个系统存在 overconfidence 的情况。

### 结果

作者用开源 `smfeval` 检查四个 ground-based LiDAR-inertial odometry filter，全部观察到 overconfidence。

最极端案例出现：**报告厘米级 certainty，但实际产生公里级 error**。

进一步分析将一类 overconfidence 追溯到滤波器把 LiDAR measurement 当成比实际包含更多“新信息”的观测，也就是重复 / 相关信息被过度计入。

### 为什么对 LIO 特别重要

这和退化环境非常相关。长走廊中 LiDAR 横向可能很强、轴向很弱；如果 estimator 仍然给出各向同性的小 covariance，控制器根本无法知道“这个方向其实已经漂了”。

因此未来 SLAM benchmark 更合理的是同时画：

```text
trajectory error
covariance / information
NEES / NIS
proper score
localizability direction
```

### 可复现性

论文明确提供开源 `smfeval` 框架。即使不换 estimator，也非常值得把现有 LIO-SAM / ESKF 日志中的 pose covariance 导出来重新评分。

### 适合谁关注

LIO / VIO、ESKF、因子图、定位 benchmark、希望把 estimator health 接到控制器的团队。

### 工程落地启发

不要让上层只订阅：

```text
pose
```

而应该订阅：

```text
pose
covariance
consistency_score
localizability
health_state
```

然后明确规定 overconfidence / inconsistency 时的降级动作。

[论文](https://arxiv.org/abs/2609.25900)

## 8. CliffCompaction：长时 Coding Agent 压缩上下文时，最危险的是“摘要再摘要”造成语义漂移

**时间回补：v1 提交于 2026-09-22 17:55 UTC。**

### 突破性工程价值

长任务 Coding Agent 会很快积累：

```text
源码
build log
test output
工具返回
失败尝试
计划
子 Agent 报告
```

超过 context window 后必须压缩。

常见做法是：

```text
history
→ LLM summary A
→ 继续工作
→ summary A + new history
→ LLM summary B
→ ...
```

问题是每一轮 summary 都可能轻微改写事实；几轮后，小偏差会累积成 context drift。

### CliffCompaction 的关键设计

它使用一个非常保守的原则：

> **压缩只能 truncate 或 drop 原始内容，绝不 rephrase / rewrite。**

而且下一次 compaction 不会压缩上一次的压缩结果：

```text
original history
→ compaction A

original history + new original content
→ compaction B
```

旧 compaction 直接丢弃。

这样就避免：

```text
summary(summary(summary(...)))
```

造成累计失真。

### 结果

论文报告在 bounded context 下，单 rollout 成本最高可下降 **50%**，同时在 Terminal-Bench 保持或提升表现。

因为单次 rollout 更便宜，同样预算可以做更多 test-time scaling；论文报告在 Terminal-Bench 上，用低于两次 full-context run 的成本获得超过 10 个百分点的提升。

KernelBench 的持续任务超过百万 token；CliffCompaction 在 200 / 400 steps 后分别达到 2.23× / 3.58× CUDA kernel speedup。

### 为什么适合真实研发

真实代码任务最不能丢的是：

```text
原始需求
明确约束
失败证据
测试结果
用户决定
```

而很多临时 Bash 输出、重复日志、已重建文件内容其实可以直接 drop。

这与“写一个越来越长的自然语言总结”相比更符合软件工程：**宁可删掉可重建的数据，也不要改写 source-of-truth。**

### 风险

纯删除式 compaction 也可能删掉低频但关键事实。

因此最稳妥的组合是：

```text
immutable artifacts / task spec
        +
lossy context compaction
```

关键决策永远写到仓库 / artifact；上下文只负责工作记忆。

### 可复现性

作者公开了 scaffold-agnostic API-proxy，可用于 Claude Code、Codex 等不同 harness。对于自研 Agent，也可以先做最小版：对 tool log 只保留最近 N 行、失败签名和 artifact path，不做自然语言重写。

### 适合谁关注

Codex / Claude Code 长任务、大仓库迁移、多 Agent、数小时到数天的自动开发任务、自研 Agent memory / compaction。

### 工程落地启发

建议将上下文分成三种生命周期：

```text
Permanent
→ spec / decisions / acceptance criteria

Recoverable
→ source files / test artifacts / git history

Ephemeral
→ command logs / repeated tool output / temporary reasoning traces
```

压缩优先删除 `Ephemeral`，其次删除可以按路径重新读取的 `Recoverable`，不要反复摘要 `Permanent`。

[论文](https://arxiv.org/abs/2609.26779)

## AI Coding 实战技巧精选

### 技巧 1｜Copilot 本地 Agent 开新 Session 时默认启用 Sandbox，不要只靠工具审批弹窗

- **来源**：[GitHub 官方 Changelog，2026-09-23](https://github.blog/changelog/2026-09-23-local-sandboxing-in-the-github-copilot-app/)。
- **一句话结论**：本地 Coding Agent 的文件、网络和凭据权限最好由 OS 级 sandbox 先限制，再让模型做工具调用；即使模型错误执行命令，也无法越过 sandbox policy。
- **具体怎么做**：
  1. 在 GitHub Copilot app 打开项目设置 → `Sandbox`，开启 **Sandbox new sessions**。
  2. 文件系统只增加任务真正需要的 read/write 目录，把 `~/.ssh`、密钥目录、其他项目设为 denied / 不授权。
  3. Network 默认关闭或只开放当前任务需要的 outbound；Git credentials 与 GitHub CLI credentials 分别按需授权。
  4. 已经运行的本地 session 可以直接输入：
     ```text
     /sandbox on
     ```
     立即切入 sandbox；项目默认值只对新 session 生效。
- **适合什么场景**：Copilot app 本地仓库 session、让 Agent 跑构建 / 测试 / shell、需要真实 Git 操作但不希望它读取整台开发机的场景。
- **注意**：当前功能为 public preview；Copilot app 与 Copilot CLI 的 sandbox 配置是分开的。更重要的是，如果操作系统无法真正 enforce 请求的 policy，GitHub 的实现会让 sandbox shell **直接失败**，而不是静默退化成无 sandbox 执行——自研 Agent 也应该采用同样的 fail-closed 原则。

### 技巧 2｜把自动 Code Review 分成“每次 Push 的 Lite”与“准备合并前的 Balanced”

- **来源**：[GitHub 官方 Changelog，2026-09-23](https://github.blog/changelog/2026-09-23-copilot-code-review-more-ways-to-request-and-configure-reviews/)。
- **一句话结论**：Code Review 不应该每次都用同一强度。频繁 push 阶段用低成本 review 捕获明显问题，准备合并时再提升 effort，能减少无价值重复审查。
- **具体怎么做**：
  1. 打开个人 `Copilot settings → Code review`。
  2. 打开 automatic review，并根据工作流决定是否同时打开 **new pushes** 和 **draft pull requests** 的自动 review。
  3. 日常默认 review effort 设为 **Lite**，用于每次 push 的快速回归检查。
  4. PR 准备合并时，在 `Reviewers` 中手动请求 Copilot，并将本次 effort 改为 **Balanced**；企业管理员还可以给 organization-owned repository 设统一默认 effort，再允许仓库级 override。
- **适合什么场景**：Agent 高频产出 commit / PR、大型仓库、同一 PR 会连续十几次 push、希望控制 review token / 时间成本的团队。
- **注意**：Lite / Balanced 是成本与深度的 trade-off，不是安全等级。合并前仍应依赖真正的 build、test、static analysis、security scan 和人工审查；不要把 AI review 当 merge gate 的唯一证据。

## 经典论文回顾

### Hector SLAM：没有轮速里程计，也可以直接让 Laser Scan 对 Occupancy Grid 做梯度优化

Stefan Kohlbrecher、Johannes Meyer、Oskar von Stryk 与 Uwe Klingauf 的 **A Flexible and Scalable SLAM System with Full 3D Motion Estimation** 发表于 **IEEE SSRR 2011**，其 ROS 实现 `hector_slam / hector_mapping` 是早期 2D 激光实时 SLAM 中非常有代表性的系统。

### 核心问题

传统 2D 激光 SLAM 往往依赖：

```text
wheel odometry
→ 提供 scan matching 初值
```

但搜索救援机器人、手持建图设备、小型 UAV 并不总有可靠轮速。

Hector SLAM 的目标是利用高频、精确 2D LiDAR，让 scan-to-map matching 本身提供足够高频的平面 pose 更新。

### 算法模块

核心 2D 前端不是 ICP 式 point-to-point correspondence，而是把 beam endpoint 直接对齐当前 occupancy grid：

```text
Laser scan endpoints
        ↓
current occupancy probability map
        ↓
interpolated map value / gradient
        ↓
Gauss-Newton pose optimization
        ↓
SE(2) pose
```

地图采用 multi-resolution representation：

```text
coarse grid
→ 先获得大 basin 粗对齐
        ↓
finer grid
→ 逐层细化 pose
```

这种 coarse-to-fine 结构降低了纯梯度方法掉进局部最小的风险。

完整系统再将 2D SLAM 的 x/y/yaw 与 IMU 姿态信息结合，形成 full 3D platform state，用于 UAV / USAR 等有 roll / pitch 的平台。

### 传感器与假设

Hector Mapping 可以在**没有 wheel odometry**时工作，这也是它当年最吸引人的地方。

但它非常依赖：

```text
较高扫描频率
scan-to-scan 运动不能过大
环境有足够二维几何梯度
```

长直走廊、大片空旷区域、只有一个大平面等场景仍会发生退化。

### 当年为什么重要

2011 年在有限 CPU 上，Hector SLAM 能用 occupancy-grid gradient + Gauss-Newton 实现实时 scan matching，而且不需要显式 point correspondence / exhaustive pose search。

ROS 包说明中，Hokuyo UTM-30LX 可以按约 40 Hz scan rate 输出 2D pose；系统被用于 UGV、USV、handheld mapping 和 quadrotor logged data。

### 今天仍在使用的思想

Hector SLAM 留下的几个思想今天仍然非常常见：

- scan-to-map 通常比纯 scan-to-scan 更稳；
- multi-resolution / pyramid 可以扩大直接优化 basin；
- 不一定需要显式 correspondence 才能做激光配准；
- 高频局部前端可以独立于全局后端存在。

今天的 Dr-LiSA 与它有一个很有意思的呼应：Hector 将 **LiDAR endpoint 对 occupancy field** 做直接优化；Dr-LiSA 则将 **Radar intensity 对由 LiDAR map 预测出的 radar field** 做直接优化。传感器完全不同，但都是把显式对应问题改写成连续场上的优化问题。

### 已被后续替代的部分

Hector SLAM 原始系统没有现代成熟的 loop closure / pose-graph backend；3D 环境中的完整几何也远不如今天的 LIO / 3D LiDAR 系统。

今天更常见的是：

```text
FAST-LIO2 / LIO-SAM
Cartographer
KISS-ICP / VGICP
现代 2D graph-SLAM
```

因此它更适合作为**理解 direct scan-to-map 优化的经典教材**，而不是直接作为新产品默认底座。

### 公开代码与可复现性

官方代码仍可访问：

[tu-darmstadt-ros-pkg/hector_slam](https://github.com/tu-darmstadt-ros-pkg/hector_slam)

ROS Index 当前仍列出 `hector_mapping` noetic-devel 分支，BSD 许可。经典实现非常适合拿一个 2D 激光 bag 做参数与退化实验。

### 对当前工程项目的重新解读

如果正在做低线数 LiDAR / 长走廊定位，Hector SLAM 最值得重新看的不是“2D 能不能替代 3D”，而是它的**优化目标与退化可观测性之间的关系**。

建议在 occupancy gradient matching 中额外统计：

```text
Gauss-Newton Hessian spectrum
x/y/yaw condition
active beam distribution
map gradient direction histogram
```

这样可以直观看到：为什么某些墙角很好定位，而长平行走廊沿轴向几乎没有约束。

这与最近连续出现的 LiLi、proper scoring / covariance consistency 其实是一条主线：

> **定位系统不仅要给 pose，还要给“这个 pose 在哪些方向上值得信”。**

[论文 DOI](https://doi.org/10.1109/SSRR.2011.6106777) · [官方代码](https://github.com/tu-darmstadt-ros-pkg/hector_slam) · [ROS Index](https://index.ros.org/p/hector_mapping/)

## 今日结论

今天 SLAM / 定位部分最值得带走的不是某一种新网络，而是**measurement space 与 uncertainty 的重新设计**。

TM-APR 说明在线 domain adaptation 未必一定是慢速反向传播；Dr-LiSA 说明跨模态配准可以先把地图投影成目标传感器的 measurement，再做 direct optimization；ArborSplat 则说明地图表示能力应该按任务语义价值分配，而不是按像素面积平均消耗。

这三条合在一起其实是在改变地图和定位的接口：

```text
Map
不只是 point cloud / voxel

它还应该支持：
- sensor-specific prediction
- semantic priority
- uncertainty / adaptation state
```

控制侧今天的两篇工作也值得放在一起看。空地双模控制用 learned mode selector 处理离散 locomotion mode，再用 RL policy 处理连续 tracking；Deep Koopman MPC 则让 learned latent dynamics 进入 MPC，而不丢掉优化器的约束结构。这比“用一个端到端策略替换所有模块”更接近可维护产品。

SafeLoop 则把机器人 Agent 里经常缺失的一层补了回来：**恢复能力本身应该成为 runtime primitive。** 我们已经很习惯软件系统有 transaction / checkpoint / rollback，但 VLA 往往仍然是单向向前执行。一旦任务中存在可逆动作，记录安全 checkpoint 并在风险上升时回退，可能比持续提高 base policy 的一次成功率更有产品价值。

而 proper odometry scoring 对 SLAM 工程的意义尤其直接：以后只报 ATE 不够。一个 estimator 是否“知道自己正在丢失定位”，决定了 fusion、planner 和 safety controller 有没有机会做正确降级。

AI Coding 侧，CliffCompaction 和今天两条实战技巧共同强调模型之外的 harness：

```text
上下文会丢信息
→ Permanent 决策写 artifact
→ compaction 只处理工作记忆

Agent 会执行错误命令
→ sandbox fail-closed

Agent 会频繁产生 PR 变化
→ review effort 分层
```

这类系统工程往往比再加一段“请认真检查” Prompt 更有效。

如果把今天压缩成一句话：

> **机器人和 Coding Agent 都在从“模型做出一个答案”转向“系统维护可适配的状态、可信的不确定性、可恢复的执行过程和受限制的权限”。**

## 最值得深入研究或尝试复现的方向

1. **给 LIO / VIO 增加 Proper-Scoring 回归测试。** 现有数据集不换算法，同时输出 covariance，用 ATE + NEES/NIS + strictly proper score 比较；专门找“误差开始变大但 covariance 还很小”的场景，将它定义成 estimator-health regression。

2. **做一个 Radar→LiDAR Map Localization 小样。** 不必先完整复现 Dr-LiSA，先在固定 LiDAR submap 上训练一个 `map + pose → radar intensity` forward model，检查 predicted radar 对 pose 的梯度是否在 x/y/z/roll/pitch/yaw 六个方向都有足够信息。

3. **把 VLA Skill Runtime 加上 Checkpoint / Rollback API。** 先人工规则决定 checkpoint，不训练风险网络；记录哪些 manipulation step 真正可逆、哪些一旦发生必须人工恢复。以后再接 SafeLoop 类 predictor。

4. **给 Mode-switching Controller 加三态接口。** 不只 `air/ground`，增加 `transition/uncertain`，并加 minimum dwell time。对楼梯、轮足、空地机器人都比二值瞬时切换更容易调试。

5. **Coding Agent Context 分类。** 把 task spec / decisions 标成 Permanent，把源码和测试报告标成 Recoverable，把长工具输出标成 Ephemeral；只对后两者做自动 compaction，并测 4h+ session 的 token、失败率与“遗忘已决定约束”的次数。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [TM-APR](https://arxiv.org/abs/2609.26766)
- [Dr-LiSA](https://arxiv.org/abs/2609.26423)
- [ArborSplat](https://arxiv.org/abs/2609.26315)
- [Learning Air-Ground Motion Control](https://arxiv.org/abs/2609.26564)
- [Wheel-loader V-Cycle Automation with Deep Koopman MPC](https://arxiv.org/abs/2609.26580)
- [SafeLoop](https://arxiv.org/abs/2609.26313) · [GitHub](https://github.com/Loule0-0/SafeLoop/tree/release/safeloop)
- [You Should Be Properly Scoring Your Odometry](https://arxiv.org/abs/2609.25900)
- [CliffCompaction](https://arxiv.org/abs/2609.26779)
- [GitHub Copilot app Local Sandboxing](https://github.blog/changelog/2026-09-23-local-sandboxing-in-the-github-copilot-app/)
- [GitHub Copilot Code Review Configuration](https://github.blog/changelog/2026-09-23-copilot-code-review-more-ways-to-request-and-configure-reviews/)
- [Hector SLAM DOI](https://doi.org/10.1109/SSRR.2011.6106777) · [GitHub](https://github.com/tu-darmstadt-ros-pkg/hector_slam) · [ROS Index](https://index.ros.org/p/hector_mapping/)
