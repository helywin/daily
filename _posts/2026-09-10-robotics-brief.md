---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-10"
date: 2026-09-10 09:00:00 +0800
description: "本期聚焦 Functional-SLAM 在线功能场景图、学习占据图的观测门控、在线可达集安全规划、人形地形感知追踪与全身 VLA，以及 AI Coding 的能力域授权与独立测试。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-10

## 摘要

截至今天早间，arXiv Robotics 最新正式公开批次为 2026-09-09。按严格最近 24 小时窗口，没有足够 5 条同时满足高质量、未重复且可完整核验条件的新工作，因此依照任务规范扩展到最近 7 天。本期主动态主要来自 9 月 8 日提交、9 月 9 日公开的论文；Functional-SLAM 的 v1 为 9 月 7 日提交，均明确标为“时间回补”。近期 GPT-6 Astra、Gemini 3.8 Flash、Claude Fable 5.1 已在前几期覆盖，本轮复查主要厂商官方入口后没有发现需要挤掉这些机器人 / SLAM / 控制 / AI Coding 工作的全新旗舰模型正式发布。

今天 SLAM 最值得优先看的工作是 **Functional-SLAM**。它没有把功能关系当成 SLAM 完成后的离线语义后处理，而是把“对象—可操作部件—功能关系”作为随位姿优化持续更新的在线地图状态。小把手、旋钮、按钮这类交互元素容易受前端漂移、遮挡和单帧歧义影响，因此系统将节点几何绑定到 anchor keyframe 的局部坐标系，并用多帧关系后验延迟提交稳定功能边。更有意思的是，功能拓扑不仅服务操作规划，还反过来补充视觉回环候选，在重复纹理或弱纹理环境中帮助位姿估计。这代表地图从“几何 + 语义标签”进一步走向“可操作结构”。

主动建图侧，**Rethinking Learned Occupancy** 给出一个很重要的负结果：学习式 occupancy completion 的精度更高，并不保证闭环主动建图最终覆盖率单调变好，因为同一张预测地图往往同时承担“哪里值得去看”和“哪里允许通过”两个职责。错误补全既可能诱导错误信息增益，也可能制造虚假障碍。论文据此提出 observation-gated filter：在尚未充分观察的区域保留 completion，但当同一区域被多次相机视锥覆盖、却始终没有邻近 RGB-D 几何支持时逐渐抑制预测。工程上最值得带走的结论是：**学习预测可以参与探索，但不能天然获得与实测几何相同的安全权限。**

控制 / 规划方面，**Online Reachability-Aware Sampling-Based Motion Planning** 把过去常见于离线预计算的可达集安全约束搬进 sampling MPC 在线循环。它使用快速 interval-based pipeline 在线计算 guaranteed reachable-set over-approximation，不需要昂贵的全局离线预计算；赛车仿真中安全违规减少超过 99%，并在模型赛车真机实验中无碰撞运行。这条路线很适合 MPPI / sampling MPC 产品化：学习或采样模块继续负责快速找低代价动作，而安全层明确维护“这一批候选未来真正可能到哪里”的外包络。

人形控制方面，**PGMT** 解决“参考动作本身不知道地形”的矛盾。传统 general motion tracker 即使能很好追踪跑、跳、挥手等参考，在台阶、箱体或复杂地形上也会因为原始参考足部轨迹物理不可行而失败。PGMT 先学习通用 tracking / recovery prior，再通过 motion-conditioned terrain glimpses 只编码当前动作真正相关的地形区域，并允许 terrain-aware tracking relaxation 在必要时偏离参考，同时保持动作意图。Unitree G1 零样本部署能处理最高约 37 cm 障碍，并统一支持遥操作、动态动作追踪和跌倒恢复。

VLA 侧本期有两条不同路线。**Proxy Policy Steering（PPS）** 不修改大基础策略，而是训练两个轻量 proxy：reference proxy 近似冻结基础策略在目标任务观测上的行为，task proxy 学少量示范带来的行为变化，两者在 velocity space 的差值作为 residual，在每个 denoising step 引导冻结 base sampler。8 个真实任务和 4 个仿真任务上，PPS 让 π0.5 平均绝对成功率提高 53 个百分点，同时保留基础策略原有的恢复能力。它很适合“基础 VLA 很大、权重不可得或不想破坏通用能力”的部署场景。

另一条是 **TANGO**：它不再把人形导航简化成 2D 路径 + 独立行走控制，而是直接把自然语言和第一视角 RGB 映射为 29-DoF 全身关节动作。训练数据全部来自仿真，通过全局路径、运动学生成、障碍感知动作编辑和 RL tracking 组合得到动态可执行监督；最后零样本部署到 Unitree G1 的真实杂乱环境中。真正值得关注的并不是“VLA 替代 Nav2”，而是狭窄三维空间里手臂摆放、躯干偏转和步态本来就是导航可行性的一部分，2D footprint 在人形上越来越不够。

AI Coding 侧，**CapScope / Authority Is Not a String** 把间接 Prompt Injection 的问题重新定义为授权问题，而不是文本分类问题。系统在读取仓库和工具输出这些不可信内容之前，就从可信任务输入推导 task-wide authority ceiling；每个子 Agent 获得独立 typed capability，并把权限状态保存在模型上下文之外。300 次实验中，ambient-authority / global-policy 基线的注入效果成功 33–47/75 次，而 CapScope 降到 3/75，同时修复完成率保持 68/75。对于拥有 shell、Git、部署、文件写入能力的 Coding Agent，这比“请忽略恶意提示”更接近真正的安全边界。

**ExecCritic** 则证明了另一个常被忽视的问题：测试并不天然是好反馈。如果 Test Agent 写出的测试本身理解错需求，执行反馈反而会把 Repair Agent 带离正确答案；论文中固定 base Repair Agent 时，基础 Test Agent 的测试让 SWE-bench Verified 解决率从不加测试的 61.2% 降到 57.3%，而 GPT-5.6-sol 生成的测试能提高到 65.3%。因此框架显式分离 Test 和 Repair，测试先经 fail-closed harness 验证并冻结，Repair Agent 无权修改；分别后训练两个 Qwen-3.5-35B-A3B 角色后，组合解决率达到 72.6%。这非常适合真实 Coding Agent：**Verifier 的质量和权限结构，和 Worker 本身同样重要。**

## 1. Functional-SLAM：功能关系开始成为 SLAM 在线状态，而不是建图后的离线标签

**时间回补：arXiv v1 提交于 2026-09-07 13:46 UTC。**  
[论文](https://arxiv.org/abs/2609.07497) · [官方代码](https://github.com/Hbelief1998/Functional-SLAM-CoRL_2026)

### 为什么重要

传统几何 SLAM 回答的是“我在哪里、表面在哪里”；语义 SLAM 再回答“这里是什么对象”。真正执行精细操作时，机器人还需要知道：

```text
水壶
 ├─ 把手：用于抓持
 └─ 壶盖：用于打开

柜门
 └─ 把手：作用于柜门开合
```

这类“对象—交互元素—功能关系”如果只在完成整段扫描后离线生成，就无法支持机器人边探索边操作。Functional-SLAM 的关键变化，是把 functional scene graph 提升为和几何地图一样需要在线维护、会随位姿优化变化的 SLAM 状态。

### 算法模块

系统以 MASt3R-SLAM 作为几何 tracking backbone，同时生成开放词汇功能观测：

```text
RGB Stream
   ↓
MASt3R-SLAM Tracking / Keyframes
   +
Open-Vocabulary Functional Perception
   ↓
Object / Interaction-Element Observations
   ↓
Anchor-Keyframe Geometry
   +
Functional-Context Association
   ↓
Persistent Functional Nodes
   ↓
Temporal Relation Posterior
   ↓
Stable Functional Edges
   ↓
Functional-Topology-Assisted Loop Closure
```

其中最值得工程团队借鉴的是 **anchor-keyframe local coordinates**。小型把手、旋钮、按钮如果直接写成固定 world coordinate，后端回环一旦修正历史 keyframe pose，这些小节点就会和最新几何脱节。论文把节点 canonical geometry 绑定到 anchor keyframe，需要世界坐标时再用最新优化位姿恢复，使语义资产和后端优化保持同步。

关系边也不是单帧一检测到就永久写入。系统积累多帧 relation support，只有在历史支持和近期最优归属都稳定后才 commit，降低遮挡和相邻物体局部重叠造成的错误关联。

### 传感器与系统假设

当前框架主要依赖连续 RGB 与 MASt3R 类 dense geometry / matching，并使用开放词汇视觉模型获得对象和交互元素。它的功能节点质量最终仍依赖视觉检测、分割和当前几何质量。

所以“功能拓扑帮助回环”不能变成无条件强约束。若早期把一个柜门把手错误关联到另一个柜体，错误 topology 也可能制造坏回环。论文仍把功能拓扑作为候选补充，并继续经过几何验证，这个权限边界很重要。

### 实时性、鲁棒性与可复现性

论文报告在线 functional graph construction 相比过去依赖离线重建的方案显著更快，并保持有竞争力的图构建精度；功能拓扑补充回环后还能改善位姿估计。当前官方代码已经公开，可复现性在本期新工作里属于较高水平。

真正部署时应重点测的不是一张漂亮 scene graph，而是：

```text
node identity switch rate
functional-edge false commit rate
loop candidate precision
后端位姿修正后的节点一致性
单帧 VLM / segmentation latency
```

### 工程风险

最大的系统风险是语义 / 功能错误进入几何后端后形成正反馈。因此推荐保留三级状态：

```text
Observed
Candidate
Committed
```

只有经过多帧和几何验证的 `Committed` 功能关系才允许参与回环；`Observed` 与 `Candidate` 只能服务当前感知与探索。

### 适合谁关注

语义 SLAM、室内移动操作、服务机器人、开放词汇地图、需要机器人理解按钮 / 把手 / 开关等可操作部件的团队。

### 工程落地启发

现有 LIO / VIO 或视觉 SLAM 不必马上换前端。可以先给地图数据库增加：

```text
FunctionalNode {
  object_id
  part_id
  role
  anchor_keyframe
  local_geometry
  confidence
  state
}

FunctionalEdge {
  source
  target
  relation
  temporal_support
  committed
}
```

先解决“地图资产如何跟随后端位姿修正”，再考虑让功能拓扑真正参与回环或任务规划。

## 2. Rethinking Learned Occupancy：更准的补全地图，不一定让主动建图走得更好

**时间回补：arXiv v1 提交于 2026-09-08 17:23 UTC；IROS 2026 Space Robotics Workshop Oral。**  
[论文](https://arxiv.org/abs/2609.09069)

### 为什么重要

主动建图里，learned occupancy completion 常被同时拿来做两件事：

```text
预测未知区域结构
   ↓
A. 计算哪里 Information Gain 高
B. 判断候选路径哪里会碰撞
```

这两个角色的风险完全不同。A 预测错了，最多浪费探索步骤；B 预测错了，可能直接把真正可走区域封死，或者把虚假 free space 当成安全通道。

论文固定主动建图其他所有模块，只替换 planner-facing occupancy，在 observation-only、learned、oracle-corrected 与 ground-truth 条件下比较闭环结果。一个很反直觉的发现是：occupancy accuracy 提升并不会单调提升最终 coverage。

### 算法模块

作者没有重新训练更大的 completion network，而是加一层 observation-gated filter：

```text
Learned Completion
       ↓
当前区域是否仍缺乏直接观测？
  ├─ Yes → 保留预测，帮助探索
  └─ No
       ↓
多次视锥覆盖后是否仍没有邻近 RGB-D 支持？
  ├─ Yes → 抑制该预测
  └─ No  → 保留
```

也就是说，模型的 prior 会随着真实观测不断到达而失去权限，而不是永远与实测 geometry 平起平坐。

### 传感器与假设

当前 benchmark 使用 RGB-D，并假设位姿足够准确。论文自己也明确指出，行星环境传感条件以及累计 localization drift 仍未覆盖。

这很关键：如果 pose 本身漂移，“反复观察却没有几何支持”也可能是配准错误造成的，而不一定说明 completion 是错的。

### 实时性与结果

25 个起点实验中，ground-truth occupancy 达到 learned baseline 最终 coverage 的 70% 时，平均能提前 **12.7 个 planning step**；但最终 coverage 只增加 **0.031**。这很好地说明“更早找到结构”和“最终能不能探索完”不是同一个指标。

Observation-gated filter 在论文针对的 failure-prone starts 上无需重训、无需 ground truth 就能改善闭环表现。

### 鲁棒性、可复现性与风险

工程上最危险的是把 neural occupancy 直接写进唯一的 collision map。更合理的是拆成两张地图：

```text
Measured Safety Map
→ 只由真实传感器与保守融合更新

Predicted Exploration Map
→ 允许 learned completion
→ 带 age / confidence / observation support
```

规划器可以用第二张图排序 NBV / frontier，但真正轨迹下发前仍回到第一张地图做 collision gate。

### 适合谁关注

自主探索、火星 / 月面机器人、3D active mapping、Neural Occupancy、Next-Best-View，以及正在让学习地图进入规划闭环的团队。

### 工程落地启发

地图单元建议不再只有 occupancy probability，而同时保存：

```text
source = measured / predicted
observation_count
last_observed
prediction_age
confidence
safety_authority
```

“预测很自信”不应自动等价于“允许承担安全约束”。

## 3. Online Reachability-Aware Sampling-Based Motion Planning：给 Sampling MPC 加一层在线可达集安全外包络

**时间回补：arXiv v1 提交于 2026-09-08 17:27 UTC。**  
[论文](https://arxiv.org/abs/2609.09073)

### 为什么重要

MPPI、sampling MPC 的工程优势很明显：非线性、非凸 cost 容易写，GPU 并行也友好。但传统 sampling controller 通常只能说“采到的这些 rollout 没撞”，不能证明真实系统在模型误差和有限控制更新之间不会进入障碍。

这篇工作将 reachability 直接嵌入在线 sampling planning，通过 interval-based pipeline 在每次 replanning 时计算 guaranteed reachable-set over-approximation。

### 算法模块

可以抽象为：

```text
Current State + Uncertainty
          ↓
Sampling-Based MPC
          ↓
Candidate Controls
          ↓
Fast Interval Reachability
          ↓
Guaranteed State Tube Overapproximation
          ↓
Obstacle / Safety Constraint Check
          ↓
只保留可认证 Candidate
```

与需要为整片状态空间提前计算 viability / reachability table 的方法不同，这条路线只围绕当前在线候选和短时 horizon 求外包络，因此避免昂贵预计算，也能扩展到此前不适合完整离线 reachability 的系统。

### 动力学与安全假设

“hard safety guarantee”成立的前提必须严格理解：真实动力学、扰动和状态不确定性需要被所采用的 interval / reachable-set 模型正确包住。

如果轮胎摩擦、执行器延迟、传感器 bias 超出假设范围，再漂亮的可达集证书也只是对错误模型的证书。因此产品中必须版本化：

```text
model_version
uncertainty_bound
state_estimator_bound
reachable_set_horizon
certificate_result
```

### 实时性与真机结果

论文报告赛车仿真中安全违规减少 **超过 99%**，并在模型赛车真实硬件上完成无碰撞控制；同时性能接近所比较的先进 reachability planner，却不需要其昂贵预计算。

公开摘要没有给出可跨硬件直接引用的统一 solver 毫秒数，因此实际复现应测 P50 / P95 / P99 的完整 `sample + reachability + selection` 墙钟延迟，而不是只测 reachability kernel。

### 鲁棒性、可复现性与风险

当前公开信息以论文为主，代码成熟度尚不能按稳定生产库评价。另一个典型风险是过度保守：reachable tube 太大时，安全层会把大量实际可行候选全部拒绝，最后机器人频繁停死。

因此要同时记录：

```text
safety_violation
false_rejection
no-feasible-candidate rate
minimum clearance
solve latency
```

### 适合谁关注

MPPI、sampling MPC、自动驾驶、赛车、无人机高速避障以及需要把“概率上表现不错”进一步升级为可审计安全边界的团队。

### 工程落地启发

现有 MPPI 不一定要大改。可以把 reachability checker 做成完全独立的 final gate：

```text
MPPI / Learned Planner
        ↓
Top-K Control Sequences
        ↓
Reachability Certificate
        ↓
通过 → 执行
失败 → Safe Backup
```

这样 proposal 与 safety authority 可以继续解耦。

## 4. PGMT：人形机器人追踪动作时，参考轨迹必须允许为真实地形“让步”

**时间回补：arXiv v1 提交于 2026-09-08 09:57 UTC。**  
[论文](https://arxiv.org/abs/2609.08511)

### 为什么重要

General motion tracking 的目标通常是尽可能逼近参考动作。平地上这很合理，但复杂地形会出现根本矛盾：参考视频里脚应该落在某个世界位置，现实那里却刚好是台阶边缘、箱体或凹槽。

如果 tracker 仍把 reference error 当最高优先级，就会为了“动作像”牺牲“动作能做”。PGMT 的关键设计是允许策略在地形要求时偏离参考，但尽量保留原始运动意图。

### 算法模块

训练过程可以理解成两阶段：

```text
大量通用 Motion Reference
        ↓
General Tracking + Recovery Prior
        ↓
加入 Terrain Perception
        ↓
Motion-Conditioned Terrain Glimpses
        ↓
Terrain-Aware Tracking Relaxation
        ↓
Unified Whole-Body Policy
```

Motion-conditioned terrain glimpse 只选择与当前动作真正相关的局部地形，而不是每一帧都编码整张高分辨率高度图。这样既降低输入复杂度，也让网络把注意力集中在即将踩踏 / 穿越的位置。

### 传感器与动力学假设

PGMT 需要能够获取前方 / 足下地形信息以及完整 proprioception。论文重点在 terrain-aware tracking policy，而不是全局导航或语义理解。

其 sim-to-real 仍依赖动力学随机化和真实传感器分布覆盖。37 cm 障碍能够通过，不代表任意 37 cm 台阶、任意摩擦和任意动作参考都安全。

### 实时性、鲁棒性与真机结果

论文在 Unitree G1 上零样本部署，展示复杂真实地形上最高约 **37 cm** 障碍的适应，同时支持 teleoperation、dynamic motion tracking 与 fall recovery。

公开摘要没有给出可用于跨平台比较的统一策略 Hz，因此不能把真机成功直接等价为所有端侧计算平台都满足相同实时预算。

### 可复现性与风险

当前论文公开，但没有把它视作已经有成熟通用 checkpoint / SDK 的产品。最大的工程风险是 tracking relaxation 的权限过大：如果允许偏离 reference 太多，策略可能“安全地完成另一个动作”。

所以部署指标应同时看：

```text
tracking intent retention
terrain clearance
fall rate
recovery rate
reference deviation
```

### 适合谁关注

Unitree G1、人形动作模仿、遥操作、复杂地形 locomotion，以及希望统一“动作库 + 环境适应”的团队。

### 工程落地启发

现有运动控制栈可以把 reference 分成不同硬度：

```text
Hard:
关节限位 / 接触安全 / 身体碰撞

Soft:
手臂风格 / 躯干姿态 / 足端精确落点

Terrain-Conditioned:
当前必须改变的脚步和身体路径
```

不是所有 reference dimension 都应该在所有环境中等权追踪。

## 5. Proxy Policy Steering：不改基础 VLA，也能用两个轻量 Proxy 在推理时把它“拉向”新任务

**时间回补：arXiv v1 提交于 2026-09-08 17:59 UTC。**  
[论文](https://arxiv.org/abs/2609.09148)

### 为什么重要

部署大 VLA 时经常遇到一个非常现实的问题：基础策略拥有广泛通用能力，但新现场只有少量示范；直接 LoRA / fine-tune 可能过拟合并破坏基础策略已经具备的 recovery、避障或通用 manipulation prior。

PPS 选择完全不修改 base policy。

### 算法模块

```text
Frozen Base Policy
       │
       ├─────────────┐
       ↓             ↓
Reference Proxy   Task Proxy
拟合 Base 行为      学任务变化
       └──────┬──────┘
              ↓
Velocity-Space Difference
              ↓
Calibrated Residual
              ↓
每个 Denoising Step
Steer Frozen Base Sampler
```

Reference proxy 首先学习基础策略在目标任务观测分布上的行为；task proxy 从 reference 初始化，再通过少量 task supervision 学“应该改变什么”。两者差值因而更接近任务带来的行为变化，而不是从零重新学习一个 specialist。

### 模型与部署假设

论文一个非常实用的点是：PPS 只需要基础策略的 forward velocity prediction，不一定要求访问 base 参数。这对托管模型、只暴露推理接口的大策略或不希望修改原 checkpoint 的产品很有吸引力。

但 residual steering 仍依赖 proxy 训练数据覆盖真正的新任务状态。如果示范太窄，proxy 在异常状态上也可能给出错误 steering。

### 实时性与结果

论文在 **8 个真实任务 + 4 个仿真任务**上评测，PPS 相对 π0.5 基础策略平均提升 **53 个百分点的绝对成功率**，并在 base 从未成功的任务上得到 zero-to-one 改善；同时优于 LoRA、从零 specialist、residual policy 等基线。

因为每个 denoising step 还需要额外 proxy forward，产品复现应重点测完整 action query latency，而不能只看参数量很小就假设延迟可忽略。

### 鲁棒性、可复现性与风险

最大的优点也是权限结构：base 永久冻结，因此出问题时可以立即将 steering residual 设为零，回到原始策略。

推荐将上线接口设计成：

```text
base_action
proxy_residual
residual_norm
proxy_confidence
steering_enabled
```

并对 residual amplitude 做硬上限。

### 适合谁关注

π0.5 / diffusion / flow-matching VLA、少样本现场适配、无法访问 foundation policy 权重、希望保留基础恢复能力的机器人团队。

### 工程落地启发

对于产品线，适配资产可以从“大量 LoRA checkpoint”转成：

```text
一个稳定 Base
+
每个任务很小的 Proxy Package
+
明确可关闭的 Steering Gate
```

这样回滚、A/B 和版本治理都会简单很多。

## 6. TANGO：人形机器人在窄空间里，“导航动作”本来就是全身动作

**时间回补：arXiv v1 提交于 2026-09-08 17:59 UTC。**  
[论文](https://arxiv.org/abs/2609.09158)

### 为什么重要

对轮式机器人，2D footprint + local planner 通常足够表达“能不能通过”。人形机器人不一样：

```text
门洞略窄
→ 侧身可以过

障碍与手臂高度冲突
→ 收臂 / 抬臂可以过

桌边接近躯干
→ 改变 torso + gait 才可行
```

把这些全部压成固定圆形 footprint，会把大量真实可行路径错误判成不可通行，也无法表达连续的 body-shape adaptation。

### 算法模块

TANGO 输入自然语言任务与 egocentric RGB，直接预测 **29-DoF joint-space action** 给下游 whole-body control。训练完全在仿真中完成，监督数据流水线为：

```text
Global Path Planning
        ↓
Kinematic Whole-Body Motion Generation
        ↓
Obstacle-Aware Motion Editing
        ↓
RL-Based Tracking
        ↓
Dynamically Feasible Supervision
        ↓
Whole-Body VLA
```

也就是说，它不是让大模型凭空学会动力学，而是先用传统规划 / 运动学 / RL pipeline 构造大量可执行全身导航行为，再蒸馏成语言条件 VLA。

### 传感器与动力学假设

部署端依赖第一视角 RGB 与本体状态，下游仍需要能够稳定追踪关节动作的 whole-body controller。

它解决的是局部、几何相关的全身穿越，不代表已经替代大尺度定位、地图管理或安全碰撞系统。长走廊全局导航仍可以由传统 topological / metric planner 提供目标，TANGO 只处理最困难的近场 whole-body traversal。

### 实时性、鲁棒性与真机结果

论文报告仿真中优于强 modular baseline，并将策略 **zero-shot 部署到 Unitree G1** 的真实杂乱场景，不使用真实导航数据训练。

公开摘要没有给出足够完整的统一端到端 Hz，因此目前更适合作为架构信号，而不是直接据此承诺某计算平台的实时性。

### 可复现性与风险

主要风险是 sim geometry 与真实碰撞模型之间的细小差异。人形在狭窄环境中，手臂、肘、肩与环境之间几厘米误差就可能决定碰撞与否。

因此生产系统仍建议保留：

```text
3D body collision monitor
self-collision constraints
joint / torque limits
perception age
emergency preemption
```

VLA 提供全身动作候选，不应该独占最终安全权。

### 适合谁关注

人形导航、Unitree G1、狭窄空间巡检、VLA + whole-body control、希望从 2D Nav 走向全身几何规划的团队。

### 工程落地启发

很实际的一种分层是：

```text
全局 SLAM / Topological Planner
          ↓
给出局部目标 / 语义目标
          ↓
Whole-Body Traversal Policy
          ↓
WBC / Safety Monitor
```

不要强迫同一个模型同时做公里级地图导航和 1 米范围内的肩、肘、足端避障。

## 7. CapScope：Prompt Injection 最终是“谁有权做什么”，而不是“模型能不能识别坏文字”

**时间回补：arXiv v1 提交于 2026-09-08 07:37 UTC。**  
[论文](https://arxiv.org/abs/2609.08371)

### 突破性工程价值

Coding Agent 会读取 README、Issue、代码注释、测试日志、网页和工具输出。只要这些不可信内容能通过自然语言影响模型，而模型又拥有 shell / Git / 网络 / secret 等 ambient authority，间接 Prompt Injection 就能变成真实动作。

CapScope 的核心判断是：

> 不要求模型先正确判断哪段文字恶意，而是在模型之外限制它即使被诱导也做不了超出授权范围的动作。

### Harness 结构

```text
Trusted User Task
       ↓
在读取 Repo / Tool Output 前
推导 Task-Wide Authority Ceiling
       ↓
每个 Agent 分配独立 Typed Capabilities
       ↓
Capability State 存在模型上下文之外
       ↓
所有 Tool Call 进入 Trusted Gate
       ↓
允许 / 拒绝
```

对子 Agent 的能力也不是自动继承。Manager 有权限，并不意味着它新创建的 Worker 立即拥有相同权限。

### 实验结果

作者在 Pi coding agent 上构造 5 个 Python repair task × 5 种 injection surface × 4 种 authorization condition × 3 次重复，共 **300 次运行**。

注入效果执行成功：

```text
Ambient / Global-Policy Baseline: 33–47 / 75
CapScope:                       3 / 75
```

正常 repair completion：

```text
CapScope: 68 / 75
Baselines: 68–72 / 75
```

说明把权限收紧到 Agent / Capability 层并没有把正常任务能力一起摧毁。

### 是否适合真实研发流程

非常适合。尤其适用于：

- Coding Agent 读取第三方仓库；
- Agent 浏览 Web / Issue；
- 多 Agent Manager-Worker；
- 能执行 shell、发送消息、部署或访问 secret 的工作流。

### 权限、安全与可验证性风险

真正困难的是 authority ceiling 的生成必须来自可信输入，而不能等 Agent 读完仓库后再“自己决定需要什么权限”。否则恶意文件可以先影响授权推理。

Capability 也应该落到具体资源和动作：

```text
repo:read
workspace:write
repo:push(branch=x)
network:domain-list
secret:name
artifact:publish
production:deploy
```

而不是一个模糊的 `admin=true`。

### 工程落地启发

企业 Agent 最值得先做的不是复杂 Prompt Firewall，而是把工具边界改成：

```text
Tool Request
   ↓
Agent Identity
   ↓
Capability Check
   ↓
Resource Scope Check
   ↓
Audit Receipt
   ↓
Execution
```

即使模型被注入，也只能提出一个最终会被拒绝的请求。

## 8. ExecCritic：错误测试会让 Coding Agent 比“不测试”更差

**时间回补：arXiv v1 提交于 2026-09-08 17:53 UTC。**  
[论文](https://arxiv.org/abs/2609.09133) · [官方代码](https://github.com/MSR-Orchard/execcritic)

### 突破性工程价值

“让 Agent 先写测试，再根据测试修代码”听起来几乎一定更可靠，但 ExecCritic 给了一个非常重要的反例：测试如果错误地编码了需求，执行反馈会变成高置信错误监督。

固定同一个 base Repair Agent：

```text
No Test Feedback:       61.2%
Base Test Agent Tests:  57.3%
GPT-5.6-sol Tests:      65.3%
```

也就是说，弱 Test Agent 的测试真的会让结果低于完全不测试。

### Test–Verify–Revise Scaffold

ExecCritic 将职责硬拆开：

```text
Issue / Repository
      ↓
Test Agent
      ↓
Candidate Tests
      ↓
Fail-Closed Harness Qualification
      ↓
Freeze Tests
      ↓
Repair Agent
      ↓
Source Patch
      ↓
Execution Feedback
      ↓
Revise Source Only
```

Repair Agent **没有修改测试的权限**。这是比“Prompt 里告诉它不要改测试”更强的系统边界。

### 后训练方式与结果

Test 与 Repair 两个角色都使用 Qwen-3.5-35B-A3B，但分别训练。

Learn to Test 阶段让 Test Agent 学会生成能够区分正确 / 错误 patch 的行为测试；Test to Improve 阶段则让 Repair Agent 同时学习直接修复与利用执行反馈进行 revision。

后训练后，Qwen Test Agent 的 Base-to-Gold test success 从 **22.2% 提升到 62.2%**；两个后训练角色组合后在 SWE-bench Verified 达到 **72.6% resolved**，相较原 no-test baseline 提高 **11.4 个百分点**，评测时不需要更强模型或 Oracle feedback。

### 是否适合真实研发流程

非常适合仓库级 Coding Agent，但 Test Agent 仍不应该是唯一 verifier。真实工程至少还存在：

```text
Project Invariants
Security Rules
Performance Regression
Backward Compatibility
Deployment Smoke Test
```

这些约束未必能从当前 Issue 自动推导出来。

### 权限、安全与可验证性风险

Test / Repair 分离只有在**权限真的分离**时才有意义：

```text
Test Agent:
可写独立 test workspace
不可改 production source

Repair Agent:
可改 source
只读 frozen tests
不可改 CI / validator
```

最终 test artifact 还必须绑定 repo SHA，否则 Agent 修了一轮代码以后测试针对的仓库状态可能已经过期。

### 工程落地启发

长期 Coding Agent 最好至少有三种独立 Artifact：

```text
Requirement Artifact
Test Artifact
Patch Artifact
```

三者分别版本化，由 CI 产生不可伪造的 execution receipt。测试不是聊天上下文中的几段代码，而应该是有来源、版本和权限边界的正式验收资产。

## 经典论文回顾

### OctoMap：为什么“未知空间”必须和“已知空闲空间”严格区分

Armin Hornung、Kai M. Wurm、Maren Bennewitz、Cyrill Stachniss 与 Wolfram Burgard 的 **OctoMap: An Efficient Probabilistic 3D Mapping Framework Based on Octrees** 最终发表于 *Autonomous Robots* **2013**，其工作可追溯到更早的机器人三维占据建图研究。它是现代 3D occupancy mapping 最重要的经典基础之一。  
[官方项目页](https://octomap.github.io/) · [官方代码](https://github.com/OctoMap/octomap) · [DOI](https://doi.org/10.1007/s10514-012-9321-0)

### 核心问题

直接保存一整块高分辨率三维 voxel grid 会迅速爆炸：空间边长扩大一倍，体素数量近似变成八倍。但机器人导航又不能只保存“障碍表面点”，因为 planner 必须区分：

```text
Occupied
→ 真的看到这里有东西

Free
→ 传感器射线已经穿过这里

Unknown
→ 根本还没有足够观测
```

最后一项尤其重要。没有点不等于 free；把 unknown 当成 free，是自主探索和安全规划中非常危险的错误。

### 关键数学与数据结构

OctoMap 使用八叉树表示三维空间：

```text
World Volume
   ↓
Octree
   ↓
需要细节的区域继续 8 分
   ↓
均匀区域保持粗层级
```

每个叶节点保存概率 occupancy belief。传感器射线命中末端体素时提供 occupied evidence，射线经过的空间提供 free evidence；多次测量使用概率 / log-odds 风格更新累积，而不是一次命中就永久写死。

当八个子节点具有相同 / 可合并状态时，树可以压缩为更高层节点，因此地图天然支持多分辨率和稀疏存储。

### 传感器与估计假设

OctoMap 自己不是 SLAM。它通常假设每帧深度 / LiDAR 数据已经有足够好的传感器位姿，再将 ray 投入全局地图。

这意味着上游 pose drift 会直接写进 occupancy：

```text
错误 Pose
→ 错误 Ray Origin / Endpoint
→ 障碍变厚、重复墙面、虚假 Free Space
```

如果后端随后发生大回环修正，经典 OctoMap 也不会自动像现代可重积分地图那样重新解释所有历史观测。

### 当年为什么重要

官方设计目标直到今天仍然非常现代：完整 3D；同时表示 occupied / free，并隐式保留 unknown；可随时增加新观测并概率更新；地图范围可动态扩展；支持多分辨率；在内存与磁盘中足够紧凑。

它让 3D occupancy 从“科研点云展示”变成真正可以被导航、探索和碰撞检查系统消费的数据结构。

### 今天仍在使用的思想

第一，**Unknown 是一等地图状态**。今天 Neural Occupancy、3DGS、TSDF、BEV completion 都仍然需要回答“这里是预测为空，还是实测为空”。

第二，**地图更新必须保存观测证据，而不是只存最终标签**。多次观测可以提高 confidence，也允许后续传感器纠正早期噪声。

第三，**地图分辨率应该随空间结构与任务需求变化**。大面积 free space 没必要和障碍边缘保持同样体素密度。

第四，**地图是 Planner API，不是可视化副产品**。它必须明确给出 free / occupied / unknown 语义。

### 已被后续替代或扩展的部分

现代系统已经大量加入：

- TSDF / ESDF，提供更连续的表面或距离查询；
- Voxel hashing / GPU mapping，提高大规模实时更新效率；
- Dynamic occupancy / temporal decay，处理运动物体；
- Semantic / object / scene graph，增加任务语义；
- Neural / Gaussian representation，提供补全与外观表示；
- 可重积分 / submap 架构，在回环修正后更新地图一致性。

OctoMap 的经典概率八叉树不是所有场景的最快表示，但它关于“观测、未知、空间层级”的抽象仍然非常难被替代。

### 公开代码、数据与可复现性

官方 C++ 库持续公开维护；核心 `octomap` 库采用 New BSD License，官方仓库还包含 `octovis` 与 `dynamicEDT3D`。项目页提供示例地图和 API 文档，属于经典 SLAM / Mapping 工作中最容易直接复现和集成的一类。

### 对当前工程项目的重新解读

今天本期的 learned occupancy 工作与 OctoMap 放在一起看，最重要的结论恰好是：

> **Prediction 不能悄悄抹掉 Unknown。**

现代地图可以扩成：

```text
Cell / Voxel {
  measured_occupancy
  predicted_occupancy
  observation_count
  last_observed
  support_sensor
  uncertainty
}
```

Planner 再按任务选择权限：

```text
探索排序
→ 可以读取 predicted occupancy

安全碰撞
→ 主要读取 measured occupancy
→ unknown 保持保守语义
```

对 16 线 LiDAR、多 LiDAR 或长期巡检尤其如此。短时间没有点，不应自动代表 free；而神经网络补出来一个墙面，也不应该未经实测验证就拥有永久安全地图权限。

## 今日结论

今天最明显的 SLAM 趋势，是地图正在从“几何结果”进一步升级为**带来源、关系和权限的在线状态**。Functional-SLAM 让功能节点与后端位姿共同演化；learned occupancy 的负结果又提醒我们，预测出来的几何和真实观测不能享受完全相同的规划权限。把两者与 OctoMap 的经典 `occupied / free / unknown` 思想放在一起，现代机器人地图更合理的最小状态已经越来越像：

```text
geometry
semantics / function
observation support
prediction source
confidence
age
safety authority
```

而不是一张单一概率栅格。

控制与规划侧的两条路线也很一致。Online Reachability-Aware planner 不试图取代 sampling MPC，而是给候选轨迹增加独立可达集安全证书；PGMT 也没有简单让网络死追 reference，而是允许真实 terrain 对动作追踪产生有结构的 relaxation。成熟机器人系统的关键越来越不是“某个算法一统所有模块”，而是**谁负责 proposal、谁能修正、谁拥有最终否决权**。

VLA 侧 PPS 和 TANGO 代表两个不同方向。PPS 说明大基础策略可以保持冻结，把现场适配变成可关闭的小 residual package；TANGO 则说明人形机器人狭窄空间导航的 action space 终究会从 `vx / vy / yaw` 走向全身几何动作。二者共同说明 Foundation Policy 的产品化不一定意味着取消分层，而可能意味着重新定义每层接口。

AI Coding 今天的结论最直接。CapScope 说明授权状态必须存在模型上下文之外，不能依靠模型读完不可信文本以后再决定自己能做什么；ExecCritic 则说明验证器本身也会错，弱测试甚至会让 Agent 比无测试更差。因此长期 Coding Agent 真正需要固化的是：

```text
Trusted Task
→ Capability Ceiling
→ Worker / Test / Repair Role Isolation
→ Frozen Verification Artifact
→ Tool Receipt
→ Independent Acceptance
```

模型继续变强、上下文继续变长，也不会让这些权限和验证结构失去价值。

## 最值得深入研究或尝试复现的方向

1. **给现有 SLAM 增加 Functional Map Sidecar。** 不改几何前端，给 keyframe 绑定 object / handle / button 等功能节点，保存 anchor-frame geometry 与多帧 relation support；第一阶段只做查询，不参与回环，待统计功能节点稳定性后再 A/B topology-assisted loop closure。

2. **把 Learned Occupancy 从 Safety Map 中拆出去。** 保留一张 measured occupancy / ESDF 作为最终碰撞依据，单独维护 prediction layer 服务 frontier 与 NBV；增加 observation-gated decay，专门统计 predicted obstacle 的 false-blocking rate 和 predicted free-space 的危险率。

3. **给 MPPI 增加 Top-K Reachability Gate。** 不必把所有 rollout 都做昂贵认证；先按普通 cost 选 Top-K，再对少量候选计算 bounded reachable tube，并设计无可认证候选时的 deterministic safe backup，重点测 P99 延迟与 false rejection。

4. **Coding Agent 同时实现 Capability Gate + Frozen Test Gate。** 每个子 Agent 使用独立能力集合；Test Agent 产生测试后由 harness 冻结，Repair Agent 只能读和运行，不能修改。用含恶意 README / tool output 的仓库与真实 repair task 一起做回归，统计 unauthorized action、修复成功率和 validator false confidence。

## 参考资料

- [Functional-SLAM: Interaction-Aware Mapping with Online Functional Scene Graphs](https://arxiv.org/abs/2609.07497) · [代码](https://github.com/Hbelief1998/Functional-SLAM-CoRL_2026)
- [Rethinking Learned Occupancy in Autonomous Active Mapping with Observation-Gated Filtering](https://arxiv.org/abs/2609.09069)
- [Online, Reachability-Aware, Sampling-Based Motion Planning](https://arxiv.org/abs/2609.09073)
- [PGMT: Perceptive General Motion Tracking for Humanoid Robots](https://arxiv.org/abs/2609.08511)
- [Proxy Policy Steering](https://arxiv.org/abs/2609.09148)
- [TANGO: Humanoid Navigation in Cluttered Environments with a Whole-Body Vision-Language-Action Model](https://arxiv.org/abs/2609.09158)
- [Authority Is Not a String: A Capability-Scoped Harness for Prompt-Injection-Resistant Coding Agents](https://arxiv.org/abs/2609.08371)
- [ExecCritic: Learn to Test, Test to Improve for Coding Agents](https://arxiv.org/abs/2609.09133) · [代码](https://github.com/MSR-Orchard/execcritic)
- [OctoMap 官方项目页](https://octomap.github.io/) · [官方代码](https://github.com/OctoMap/octomap) · [DOI](https://doi.org/10.1007/s10514-012-9321-0)
- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new)
