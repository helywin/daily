---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-07"
date: 2026-09-07 09:00:00 +0800
description: "本期关注矿井多模态退化自适应定位、风险规则簿控制、户外 3D 场景图、VLA 在线强化学习与失效检测、触觉实时纠偏、现场持续学习，以及 LSP + 形式验证的 AI Coding。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, VLA, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-07

## 摘要

截至本期重新检索时，arXiv Robotics 已刷新到 **2026-09-07** 最新公开批次，共 65 条，其中 **32 条 new submissions**；Software Engineering 最新常规批次仍为 **2026-09-04**，共 31 条，其中 14 条 new submissions。今天恰逢周一，Robotics 的最新批次集中释放了周末前提交的论文，因此本期优先改用这一批新公开工作，而不是继续沿用早间检索时的 9 月 3 日候选。入选 Robotics 论文的 v1 实际提交时间主要为 9 月 3–4 日 UTC，按任务规范仍明确标记为“时间回补”。

今天 SLAM / 状态估计方向最值得优先看的工作是 **FIRE-LIVWO**。它面向大型地下煤矿最难处理的两类退化：烟尘让视觉和 LiDAR 同时丢信息，长而自相似的巷道又让几何约束沿特定方向消失。系统不是简单把 Radar、LiDAR、Camera、Wheel 全部固定加权，而是在 IESKF 内用统一 VoxelMap、LiDAR-Radar point-to-plane、稀疏视觉光度残差、Radar Doppler 与轮速非完整约束共同工作，并显式分析几何与视觉可观测性，在不同 failure boundary 上切换融合模型。对正在做 16 线 / MID360、长走廊、矿井或多传感器 LIO 的团队，这类“先判断缺什么信息，再决定谁来补”的结构比继续寻找一个永不退化的单一 LIO 更值得研究。

控制侧，**Risk-Aware Optimal Control with Rulebooks** 把安全规则从一个加权总 cost 拆成带优先级的 rulebook：碰撞、后车急刹、车距、舒适性可以使用不同风险度量和阈值，而且高优先级规则不能因为低优先级收益更大而被换掉。算法将问题做成 excess-risk 的字典序优化，并用 anytime filtering + Lipschitz branch-and-bound 在任意有限计算预算下同时返回当前策略和可证明的最优性 gap。它目前主要是合成实验与高速公路并线仿真，但架构上非常适合机器人任务规划和 MPC 前的安全候选筛选。

长期语义地图方面，**Open-Set 3D Scene Graphs for Field Robotics** 给出了少见的户外负结果。五个户外数据集上，VLM 点级 embedding 并没有像室内 demo 那样稳定：约 30% 的点出现超过 0.1 的 outlier ratio；基于场景图的目标检索导航可以接近 70% 成功率，但平均路径效率仍约有 66% 的次优程度，region-level 理解平均 F1 只有约 0.359。另一方面，多公里轨迹的语义图仍能压在 600 MB 以内。这说明 3D Scene Graph 很有长期地图价值，但真正产品化必须把 traversability、语义多峰和重复巡检一致性一起放进图里，不能只把 CLIP/VLM 特征平均后当作“语义真值”。

VLA 侧今天有三条互补路线。**VLA-Precision** 用真实机器人在线 RL 解决高精度化学操作的重复性问题：早期由人工 intervention 引导行为改进，后期再用全局 return 与局部 preference 逐步校准 value，配合 reference-bounded policy update 避免策略漂移；ACoB-Stream 又把经验采集和大 VLA 更新解耦，最高获得 10.9× throughput / compute efficiency。九项高精度化学任务、四种机器人本体上，平均成功率达到 98.3%，每项约 45.8 分钟在线学习。

**FailureSpot** 解决“失败到底从哪一帧开始”的问题。它不把整条失败轨迹从第一帧起都错误标成 failure，而是利用 VLA action chunk 之间的不一致、冻结、无意义大动作等信号做弱监督预训练，再只挑 detector 最不确定的少数轨迹做 timestamp-level 标注。主实验使用 60% 轨迹做弱监督预训练、15% 轨迹做精细标注；在 π0 上轻量 MLP 的 timestamp-level AUROC 平均达到 92.9，而且报警可以早于平均 ground-truth failure onset。这更适合作为 VLA runtime 的 proactive watchdog，而不是等机器人已经把物体推倒后再让视觉模型判定“任务失败”。

**TacPAC** 则处理接触已经发生之后的实时纠偏。World-Action Model 先生成 action chunk 与预期接触，执行过程中新的触觉图像不是重新触发整块动作生成，而是与“原计划本来预期看到什么接触”进行比较，只修改尚未执行的动作。单次纠偏比重新生成 action chunk 便宜 20.7×；五个真实机器人接触任务中，平均成功率从 vision-only base model 的 22% 提高到 64%。它把 world-model prediction 从离线评分器变成真正的闭环 reference。

现场持续学习方面，**CFAM** 采取非常不同的路线：慢学习部分冻结，Sensor / Reasoning / Action 三个模块负责通用能力；现场新经验则写入快速的 Capsule Field，以 one-shot、gradient-free 的 Competence Capsule 形式积累。五种本体实验中，CFAM 用约 40% 的 prior-training 数据达到标准 full-data policy 的 operating point，部署时自动捕获并验证 near-OOD case 后，action success 再提高 13.9 个百分点；顺序学习模拟中的 backward transfer 为 -0.5 pp，而 LoRA 为 -11.4 pp。项目方还报告 Jetson Orin 上约 23.4 ms/cycle。需要强调的是，其 open-world novelty 明确不在当前范围内，因此它更像“有边界的现场经验增长”，不是机器人遇到任何未知事物都能自己学会。

AI Coding 侧，本期选择 **Large Language Models and Language Server Protocol: a match made in context**。它把 LSP 当作模型与真实工程语义之间的稳定接口：语言服务器天然知道符号、类型、项目结构与静态验证器，LLM 负责生成代码和规格，但每次结果都交给 verifier 检查，不通过就修正、拒绝或继续 retry。Eiffel-tools 在两个公开数据集、三个模型上的 bug-fixing 成功率为 76%–95%。真正值得迁移的不是 Eiffel 本身，而是“IDE/LSP 提供结构化上下文，LLM 提候选，确定性 verifier 决定是否接受”的 Coding Agent 架构。

近期 GPT-6 Astra、Gemini 3.8 Flash、Claude Fable 5.1 等旗舰模型已经在前几期覆盖；本轮没有发现 9 月 5–7 日需要挤掉上述最新 Robotics 工作的新旗舰基础模型正式发布，因此不重复用模型新闻凑数。

## 1. FIRE-LIVWO：矿井定位不应固定相信所有传感器，而应根据 failure boundary 切换融合模型

**时间回补：arXiv v1 提交于 2026-09-04 16:19 UTC；IROS 2026 接收。**（[论文](https://arxiv.org/abs/2609.05325) · [项目页](https://kj-falloutlast.github.io/) · [代码](https://github.com/KJ-Falloutlast/FIRE-LIVWO)）

### 为什么重要

地下煤矿同时存在两种非常不同的退化：

```text
烟尘 / 粉尘
→ Camera 纹理与 LiDAR 回波质量下降

长直、自相似巷道
→ LiDAR 几何 Hessian 出现弱方向
```

把这些情况统一处理成 `lidar_good = false` 并不够。烟尘时 4D mmWave Radar 仍然能提供 Doppler 与几何信息；长走廊时轮速对前向速度往往反而很强。FIRE-LIVWO 的价值是把“哪个模态此刻能补哪一种退化”直接写进状态估计器。

### 算法模块

主体是 iterated error-state Kalman filter（IESKF）：

```text
IMU Propagation
      ↓
Unified VoxelMap
      ↓
LiDAR-Radar point-to-plane
+ sparse visual photometric residual
+ Radar point-wise Doppler velocity
+ Wheel NHC
      ↓
Geometric / Visual Observability
      ↓
Failure Detection
      ↓
Adaptive Fusion Model Switching
```

Radar 与 LiDAR 并不是两条完全分离的里程计再做 pose-level fusion，而是共同进入 VoxelMap 几何约束。烟尘严重时，Radar Doppler 负责维持速度可观测性；长走廊中则引入 wheel odometry 的 non-holonomic constraint，并在线补偿 wheel 与机体之间的 lever arm。

### 传感器与可观测性假设

方案同时依赖 IMU、LiDAR、4D mmWave Radar、Camera 与轮速。硬件多的好处是 failure diversity，代价则是标定、时钟和故障诊断都更复杂。

尤其 Radar 并不是天然“不会失败”：多径、动态目标和错误 Doppler association 仍可能污染 estimator；轮速在泥、水、煤尘和打滑路面也会失效。因此 adaptive switching 最重要的输入不是传感器名称，而应该是可观测性、innovation 和物理一致性。

### 实时性、鲁棒性与结果

论文在真实大型地下煤矿中测试，并报告平均 localization error 为 5.677 m，同时强调在烟尘和几何退化边界上的相对鲁棒性优于基线。这个数值本身并不是“厘米级高精度”的证据，更适合放在大尺度极端环境下理解；真正值得关注的是系统能够在线识别 failure boundary 并改变融合结构。

官方代码已经公开，因此可复现性优于只给论文的多模态 SLAM 工作。

### 工程风险

五种传感器全部进入紧耦合 estimator 后，最危险的是 failure detector 自己判断错。某个模态已经异常但仍被高权重使用，错误会比松耦合系统更快传播。

生产版本建议每个模态都独立维护：

```text
observability
innovation consistency
time-sync health
calibration health
staleness
failure reason
```

### 适合谁关注

矿井、长走廊、隧道、地下空间、煤场，以及 16 线 / MID360 + IMU + 轮速 + Radar 的多传感器定位系统。

### 工程落地启发

不必一开始复现整套 FIRE-LIVWO。对现有 LIO-SAM / FAST-LIO，先输出当前 Hessian / information matrix 的 weak direction，再让轮速、Radar、RTK 或第二只 LiDAR按“是否能补弱方向”动态加权，就已经能复制最重要的系统思想。

## 2. Risk-Aware Optimal Control with Rulebooks：安全规则不要压成一个总 Cost

**时间回补：arXiv v1 提交于 2026-09-04 14:32 UTC。**（[论文](https://arxiv.org/abs/2609.05199)）

### 为什么重要

很多机器人 planner / MPC 把所有目标写成：

```text
J = w_collision * collision
  + w_progress * progress
  + w_clearance * clearance
  + w_comfort * comfort
```

这有一个结构性问题：只要权重选择不当，足够大的低优先级收益可以“买掉”高优先级安全规则。

Rulebook 的思想是显式规定：

```text
Rule 1: Collision risk      最高优先级
Rule 2: Rear braking risk
Rule 3: Headway
Rule 4: Comfort             低优先级
```

不同规则甚至可以使用不同风险度量与阈值。

### 算法模块

每条 rule 先得到一个 risk-evaluation function，再计算超过可接受 threshold 的 excess risk；多个规则按照 priority 做 lexicographic optimization。

算法不是要求先把第一条规则精确全局优化完才能进入第二条，而是维护 candidate policy 的 box collection、可证明 lower/upper bound 与 incumbents，使用 filtering + Lipschitz branch-and-bound 持续收缩：

```text
Policy Search Space
      ↓
Rule 1 Bound / Filter
      ↓
Certified admissible set
      ↓
Rule 2 Bound / Filter
      ↓
...
      ↓
Current Policy + Optimality Gaps
```

任何有限计算预算下都能返回一组有效 gap；预算增加时，在论文假设下 gap 继续收敛。

### 动力学与风险假设

一个很实用的特点是 risk evaluation 可以当 black box，不要求可微、凸或拥有显式解析式。但理论需要 Lipschitz 连续性及相应常数或界，这在复杂学习式 simulator 中可能相当保守。

论文高速公路并线实验使用 CVaR 表达 collision、rear braking、headway 与 comfort 风险。

### 实时性与结果边界

当前验证是已知最优的 synthetic benchmark 和 realistic highway-merging simulation，没有实体机器人或统一毫秒级实时结果。因此它现阶段更适合作为高层 policy / trajectory candidate 的 certified anytime optimizer，而不是直接替换 100 Hz local controller。

### 工程风险

Rulebook 只会忠实执行已经定义的规则。漏写一条真正重要的安全条件，优化器不会自动发现。

因此 rule 应带 provenance：

```text
rule_id
priority
risk_measure
threshold
source / regulation
version
```

### 适合谁关注

安全 MPC、多目标局部规划、无人车 / 无人机、高风险工业机器人，以及希望把 SOP / 安全要求从 Prompt 变成可执行控制约束的团队。

### 工程落地启发

即使不用论文算法，也建议先把现有加权 cost 分成“不可交易的高优先级规则”和“可优化的低优先级性能目标”。这一步本身就能减少大量靠调权重解决的安全歧义。

## 3. Open-Set 3D Scene Graphs：户外语义地图最大的问题不是内存，而是语义多峰与可通行性

**时间回补：arXiv v1 提交于 2026-09-04 01:14 UTC；IEEE Transactions of Field Robotics 接收。**（[论文](https://arxiv.org/abs/2609.04607)）

### 为什么重要

3D Scene Graph 很适合长期机器人地图，因为它可以把：

```text
Points / Objects / Places / Regions
```

放到同一层级结构里，再让 VLM / LLM 查询“工具箱在哪里”“哪条路通往设备区”。但绝大多数漂亮 demo 都来自室内。

这篇 field report 的价值是把 open-set 3DSG 放进五个真实户外数据集，专门测它在哪些地方不可靠。

### 评测模块

作者以 Terra 3DSG 为案例，分别分析：

- 点级 VLM semantic embedding；
- place-node graph navigation；
- region-level understanding；
- repeated traversal consistency；
- 多公里地图内存。

并新增一致性指标，检查同一区域重复经过以后 semantic / structural graph 是否稳定。

### 关键结果

多个结果很适合产品团队直接记住：

```text
约 30% points:
outlier ratio > 0.1

Object-retrieval navigation:
成功率接近 70%

Path efficiency:
平均约 66% suboptimal

Region understanding:
平均 F1 ≈ 0.359

Memory:
多公里轨迹 < 600 MB
```

也就是说，**存储并不是目前最严重的问题**；真正难的是 VLM embedding 多峰、区域概念不稳定，以及 scene graph 与 traversability graph 没有充分统一。

### 传感器与地图假设

户外地图会遇到植被、重复地貌、季节变化、坡度与不可通行区域。一个 place node 在几何上相邻，不代表真实机器人一定能直接通过。

所以 Scene Graph 不能只保存 semantic relation，还需要保留：

```text
traversability
path cost
observation support
semantic modes
last seen
cross-session consistency
```

### 实时性、鲁棒性与可复现性

这是一份 field study，不是新的实时 SLAM 前端。论文证明 3DSG 具有长期压缩潜力，但也明确暴露当前 open-set semantic layer 仍不稳定。

### 适合谁关注

园区 / 矿区巡检、语义导航、长期地图、VLM + SLAM、跨 session object retrieval。

### 工程落地启发

现有 LIO-SAM 地图完全可以保留几何主地图，再增加低频 3DSG 层：几何层负责“能否走”，场景图负责“为什么去、找什么、区域是什么”。不要让 VLM semantic embedding 直接覆盖几何可通行性。

## 4. VLA-Precision：真实在线 RL 的重点不是多试几次，而是控制 Value 漂移与系统吞吐

**时间回补：arXiv v1 提交于 2026-09-03 18:19 UTC。**（[论文](https://arxiv.org/abs/2609.04355) · [项目页](https://vla-precision.github.io/)）

### 为什么重要

通用 VLA 可以完成“拿起、放下、移动”这类粗操作，但实验室化学任务要求插入、移液、刷管、装架等高度可重复的毫米级动作。

继续采 demonstration 有上限；真实在线 RL 能从失败中继续改善，但大 VLA 又面临两个问题：

```text
Value 估计不可靠
→ Policy drift

模型太大
→ 真机等待推理/更新
→ 单位时间获得的有效经验太少
```

### ACoB：不同阶段使用不同学习信号

早期 policy 很差时，作者使用 intervention-guided behavioral learning 快速把行为拉进可用区域，同时让后续采集到的 autonomous experience 更有价值。

随着真实经验积累，再逐步使用 global return propagation + local preference ranking 校准 value，并通过 relative action advantage + reference-bounded update 限制策略偏离已有可靠行为。

这是一种明显的“先把系统救活，再做自主优化”的两阶段逻辑。

### ACoB-Stream：把经验循环和大模型更新解耦

ACoB-Stream 强调 invariant-state decoupling 与 on-demand streaming，避免机器人每获得一次新经验都停下来等待整个大 VLA 完整更新。

论文报告最高 **10.9× throughput / computational efficiency** 改善。

### 真机结果

九项高精度 chemistry manipulation、四类任务、四种 robot embodiment：

```text
Mean success rate: 98.3%
Online training:    45.8 min/task
Episode duration:   27.6 s
```

并相对 VLA / RL baseline 分别以约 1.2× / 1.8× 速度运行 episode。

### 风险

真实在线 RL 最大风险不是训练不收敛，而是探索真的会撞设备、打翻试剂或损坏器材。

论文使用 intervention 与 reference-bounded improvement 缩小风险，但生产系统仍需要：

```text
action bound
workspace bound
force / collision gate
recovery skill
human takeover
version rollback
```

### 适合谁关注

精密装配、实验室自动化、插接、机器人现场 post-training，以及有少量真机持续运行预算但没有上千小时 demonstration 的团队。

### 工程落地启发

不要把“在线学习”实现成一个常驻训练线程直接改生产 policy。更合理的是：采集真实 correction → 沙箱更新 candidate → 小流量验证 → 通过后切换版本，并永远保留 reference policy。

## 5. FailureSpot：VLA Watchdog 应该定位失败开始的 Timestamp，而不只给整条轨迹打标签

**时间回补：arXiv v1 提交于 2026-09-03 00:04 UTC。**（[论文](https://arxiv.org/abs/2609.04277)）

### 为什么重要

如果一条 40 秒轨迹最后 3 秒抓取失败，把前 37 秒全部标成 `failure` 会给 detector 引入严重 label noise。

真正部署需要回答的是：

> **哪一帧开始，机器人已经不再朝任务目标有意义地进展？**

而且最好在错误动作真正造成不可逆后果之前报警。

### 算法模块

FailureSpot 使用 VLA 在动作执行前已经拥有的 internal representation，接一个非常轻的 MLP 或 LSTM detector。

第一阶段不需要人工逐帧标注，而从 action chunk 本身构造 weak signal：

```text
相邻 chunk 不一致
动作长期冻结 / idle
异常大的随机动作
chunk magnitude 异常
```

第二阶段根据 detector uncertainty，只挑最不确定的轨迹做 timestamp-level annotation，再 fine-tune。

### 标注效率与结果

主实验配置为：

```text
60% trajectories:
弱监督预训练

15% trajectories:
timestamp-level 精细标注
```

π0 上 FailureSpot-MLP 的 timestamp-level AUROC：

```text
Seen   95.3
Unseen 90.5
Avg.   92.9
```

π0-FAST 的平均为 83.5；OpenVLA 更低，说明 detector 可迁移性仍依赖 base policy representation。

论文还显示最佳阈值下报警时间早于平均 ground-truth failure onset，因此具备 proactive intervention 的可能。

### 风险

Action abnormality 不一定等于任务失败。某些动态任务本来就需要大动作；某些失败则可能动作看起来平滑，却抓错了对象。

所以 runtime 更合理的组合是：

```text
VLA internal failure detector
+
object/task-state verifier
+
collision / force safety
```

而不是让一个 failure score 拥有全部停机权。

### 适合谁关注

长时 VLA、无人值守机械臂、双臂操作、希望在失败后自动 Retry / Reset 的系统。

### 工程落地启发

每次策略执行至少记录：

```text
policy_hidden_state / compact feature
action_chunk
detector_score
failure_onset
recovery_action
final outcome
```

这样长期运行数据才能真正训练“什么时候应该接管”。

## 6. TacPAC：触觉反馈最有价值的方式不是重新生成动作，而是纠正尚未执行的动作

**时间回补：arXiv v1 提交于 2026-09-04 15:24 UTC。**（[论文](https://arxiv.org/abs/2609.05266) · [代码](https://github.com/LogosRoboticsGroup/TacPAC)）

### 为什么重要

World-Action Model 可以预测未来视觉，但接触任务里真正决定成败的信号往往是：

```text
插入方向是否卡住
夹持是不是开始滑
脆弱物体受力是否异常
旋转是否真正发生
```

这些信息只会在动作执行过程中出现。

如果每收到一帧 tactile 都重新运行整个大模型生成新的 action chunk，闭环延迟和算力开销都会太高。

### 算法模块

TacPAC 在规划时缓存：

```text
Predicted Contact
+
Plan Representation
+
Unexecuted Action Chunk
```

执行过程中，新触觉图像由 tactile expert 读取，并与“原计划预期发生的接触”比较，然后只更新还没有执行的那一段动作。

这非常像控制里的 tracking residual：不是孤立地解释当前触觉，而是判断实际 contact 与 predicted contact 之间出现了什么偏差。

### 实时性与真机结果

单次 action correction 只对缓存做一次前向，比重新生成完整 chunk **便宜 20.7×**。

五个真实机器人任务覆盖 precision insertion、fragile-object handling、object reorientation 与 long-horizon manipulation：

```text
Vision-only base: 22%
TacPAC:           64%
```

并且官方代码已经公开。

### 风险

缓存的 predicted contact 也可能已经过期。如果物体被碰到后发生大幅位姿变化，继续围绕旧计划做“小纠偏”可能反而更危险。

因此需要一个 residual magnitude / novelty gate：

```text
小偏差 → TacPAC correction
大偏差 → invalidate chunk → replan
```

### 适合谁关注

插接、旋拧、脆弱物抓取、双臂接触任务、视觉 + GelSight / tactile 的 VLA 系统。

### 工程落地启发

真实机器人 Foundation Model 很可能需要两种闭环：慢速模型重新规划；快速 tactile / force expert 只做 bounded correction。两者不应该都使用同一个频率和同一算力预算。

## 7. CFAM：部署后持续学习可以不改主模型参数，而把新经验写入快速能力场

**时间回补：arXiv v1 提交于 2026-09-03 23:15 UTC。**（[论文](https://arxiv.org/abs/2609.04552) · [技术说明](https://skylarklabs.ai/use-cases/cfam-stack-overview.html)）

### 为什么重要

传统机器人产品基本都是：

```text
收集失败日志
→ 上传服务器
→ 重新训练
→ 新版本 OTA
```

但矿井、灾害、无人机、野外机器人经常没有持续网络，也没有时间等待下一轮集中训练。

CFAM 研究的是更严格的 field-learning regime：算力和内存固定、监督稀疏、连接可能不存在，而且新的 action 必须在下一个控制周期继续产生。

### 架构

慢学习部分冻结，包含三类 cortex：

```text
Sensor
→ 多模态输入映射到 3D-grounded geometry

Reasoning
→ 任务分解、结果判断、缺失能力选择

Action
→ 执行 geometric skills
```

快速学习部分是 **Capsule Field**。新的经过验证的现场经验被写成 Competence Capsule，不通过 gradient update 修改共享主模型参数。

这让“学会一个新局部修正”和“破坏以前全部能力”在架构上被分开。

### 结果

论文覆盖 manipulator、quadruped、humanoid、quadrotor、off-road vehicle 五种 embodiment。

- 约 **40%** prior-training 数据即可达到 full-data 标准 policy 的 operating point，相当于 2.5× 更少轨迹；
- 自动捕获并验证 near-OOD case 后，action success **+13.9 pp**；
- sequential simulation backward transfer 为 **-0.5 pp**，LoRA 为 **-11.4 pp**。

项目方技术说明还报告 Jetson Orin 上 **23.4 ms/cycle、30 Hz** 的 edge loop。这个数字来自作者/公司项目页，仍应在自己的目标硬件上重新基准。

### 边界与风险

作者明确指出 open-world novelty 不在当前范围内。CFAM 处理的是 bounded novelty / near-OOD growth，不是机器人第一次看到任意工具就能完全自主学会。

另一个风险是 Capsule Field 越积越多以后：

```text
谁决定新 capsule 真的有效？
旧 capsule 何时过期？
冲突 capsule 谁优先？
内存如何压缩？
```

这些都需要版本与 provenance。

### 适合谁关注

野外机器人、矿井、无人机、多地点部署、弱网络、希望把现场经验变成可复用技能而又担心 catastrophic forgetting 的团队。

### 工程落地启发

即使不实现 CFAM，也可以把在线学习资产从“模型权重”改成：

```text
Skill / Correction Artifact {
  trigger
  local context
  action correction
  verification evidence
  version
  rollback
}
```

先让现场经验可审计，再决定是否真正合并进主模型。

## 8. LLM + LSP + Static Verifier：Coding Agent 的上下文接口应该来自语言服务器，而不是让模型自己 grep 一切

**时间回补：arXiv v1 提交于 2026-09-02 18:59 UTC；VERIFAI-2026。**（[论文](https://arxiv.org/abs/2609.03086) · [Eiffel-tools](https://github.com/alschena/eiffel-tools)）

### 突破性工程价值

IDE 里的 Language Server 本来就已经知道：

```text
symbol
type
definition
reference
project structure
diagnostics
```

Coding Agent 如果完全绕开这些结构，每次都通过全文搜索重新“猜仓库语义”，既浪费 token，也容易遗漏编译器已经知道的事实。

Eiffel-tools 把 LSP 直接变成 LLM 的工程上下文层。

### Generate → Verify → Repair

系统使用语言与项目特定知识构造 programmatic prompt，LLM 可以生成：

- 代码；
- specification；
- bug fix。

但模型输出不会直接被接受，而是进入静态 verifier：

```text
LSP Context
    ↓
LLM Candidate
    ↓
Static Verifier
  ├─ Pass → Accept
  └─ Fail → Correct / Reject / Retry
```

验证失败的具体结果又成为下一轮修复输入，形成确定性 feedback loop。

### 结果

两个公开 bug dataset、三个模型上，LLM + verifier 能修复 **76%–95%** 的 bug；成功率随允许的修复尝试次数提高，也带来更多调用成本。

### 为什么比“Agent 自己反思”更重要

Verifier 的关键价值是**判定权不在生成模型手里**。

模型可以说“我认为现在没问题”，但最终是否满足 specification 由静态工具决定。这和普通 Coding Agent 的：

```text
build
unit test
static analysis
symbolic verifier
```

本质上属于同一类独立证据。

### 局限与风险

Eiffel 的 Design by Contract 与静态验证生态使这条路线特别自然。迁移到 C++ / Java / Rust 后，能够验证到什么程度取决于类型系统、annotation、static analyzer 和项目本身的 specification 质量。

因此不能从 76%–95% 直接推出“任意仓库都能达到类似自动修复率”。

### 适合谁关注

Codex / Claude Code 类企业 Agent、IDE Agent、强类型代码库、静态分析 / 形式验证流水线。

### 工程落地启发

比给 Agent 再加一套自定义 grep 工具更值得优先做的是统一：

```text
LSP / AST → 稳定 Read API
Compiler / Verifier → Evidence API
Agent → 只负责提出 Patch
```

模型升级以后，这些确定性接口仍然可以保持不变。

## 经典论文回顾

### Timed Elastic Band（TEB）：为什么一条“路径”还不是机器人真正能执行的“轨迹”

Christoph Rösmann、Wendelin Feiten、Thomas Wösch、Frank Hoffmann、Torsten Bertram 在 **ROBOTIK 2012** 的《Trajectory modification considering dynamic constraints of autonomous robots》中提出 Timed Elastic Band。后续 `teb_local_planner` 将它做成 ROS Navigation Stack 最经典的局部轨迹优化器之一。（[原始论文](https://files.davidqiu.com/research/papers/2012_rosmann_TEB%20Planner%20Trajectory%20modification%20considering%20dynamic%20constraints%20of%20autonomous%20robots%20%5BROBOTIK%202012%5D.pdf) · [TU Dortmund 介绍](https://rst.etit.tu-dortmund.de/en/research/robotics/online-trajectory-optimization-based-on-timed-elastic-ban/) · [代码](https://github.com/rst-tu-dortmund/teb_local_planner)）

### 核心问题

全局 A* / Dijkstra 给出的通常只是：

```text
p0 → p1 → p2 → ... → pN
```

它没有回答：

```text
每一段什么时候到？
速度多大？
加速度是否超限？
机器人转得过来吗？
绕障碍的时间代价是多少？
```

经典 Elastic Band 只在空间中把 path 当成一条可以被障碍物“推开”的弹性带；TEB 的关键升级是给相邻 pose 增加时间间隔 `ΔT`。

于是优化变量从单纯空间 waypoint 变成：

```text
Pose_i + ΔT_i
```

一条 Path 正式变成了带时间参数的 Trajectory。

### 优化结构

TEB 使用加权多目标优化，典型项包括：

```text
最短执行时间
障碍物距离
最大线速度 / 角速度
最大加速度
非完整运动学
路径跟随
```

绝大部分 objective 只连接相邻的少数 pose / time interval，所以整个问题形成稀疏图结构，可以使用 g2o 一类 sparse nonlinear least-squares solver 高效迭代。

这也是它能在移动机器人上在线运行的关键：不是每次求一个巨大的 dense trajectory optimization。

### 为什么今天仍然重要

TEB 把“几何规划”和“动力学可执行性”之间的边界做得非常清楚：

```text
Global Planner
→ 给拓扑和长距离方向

TEB
→ 把局部路径变成受速度/加速度/障碍约束的时间轨迹

Controller
→ 真正跟踪
```

这套分层今天仍然适用于 MPPI、MPC、学习式 planner。

### Homotopy / 多拓扑扩展

后续 `teb_local_planner` 还会并行维护不同 homotopy class，例如从障碍左边绕和右边绕，避免只在一个局部最优 basin 中调轨迹。

这和今天 diffusion planner “保留多模态候选”在思想上其实非常接近：先保留多个拓扑不同的候选，再在各自局部空间优化。

### 传感器与动力学假设

TEB 主要使用 2D costmap / obstacle representation，默认环境在短预测窗口内足够可预测。它支持差速与 Ackermann 等运动学约束，但并不是完整车辆轮胎动力学、四足接触动力学或无人机 6DoF 动力学优化器。

动态障碍、非常窄的空间和错误 footprint 都可能让局部优化陷入失败。

### 今天已经过时的部分

经典 ROS1 `teb_local_planner` 的工程栈已经比较老，今天可以选择 Nav2 Controller、MPPI、MPC 或自研 GPU planner。

但 TEB 最值得保留的不是某个 ROS plugin，而是三个原则：

1. **Path 必须显式变成 time-parameterized trajectory；**
2. **障碍、安全与 kinodynamic constraint 应在同一局部优化中考虑；**
3. **局部优化要保留不同拓扑候选，不能只修一个初始路径。**

### 对当前机器狗 / 轮式机器人项目的重新解读

如果机器人已经有 SDK 提供楼梯 / parkour gait，而上层只需输出 `vx / vy / yaw-rate`，TEB 思想仍然可以迁移，但优化变量不一定是底盘真实关节轨迹：

```text
Global Route
      ↓
Terrain / Mode Topology
      ↓
Timed Local Command Sequence
(vx, vy, yaw, mode, ΔT)
      ↓
SDK Locomotion Skill
```

也就是说，“时间弹性带”可以升级为**带 locomotion mode 的高层 command band**，而不是强行让通用 2D TEB 直接理解楼梯接触动力学。

## 今日结论

今天最清晰的 SLAM 信号是：**鲁棒融合正在从“传感器数量更多”走向“先识别 failure boundary，再决定哪个传感器在当前状态方向上有价值”。** FIRE-LIVWO 把烟尘、视觉退化、几何走廊退化和轮速约束分开处理，这比固定五传感器权重更接近真实矿井系统。

Open-Set 3D Scene Graph 的户外实测又提醒我们，长期地图不能只追求语义丰富。VLM embedding 存在明显多峰 / outlier，place graph 如果不带 traversability，语义导航会走出几何上很低效甚至不可通行的路径。更合理的地图栈是：

```text
Metric / Traversability Map
        ↓
Topological / Place Graph
        ↓
Open-set Semantic Graph
        ↓
Task Memory
```

各层互相约束，但不能让最不稳定的语义层反过来覆盖底层几何事实。

控制侧的 Rulebook 与经典 TEB 放在一起看，也呈现出同一个长期趋势：**机器人规划不应该把所有东西压成一个不透明标量。** TEB 明确区分时间、障碍、速度和运动学；Risk-Aware Rulebooks 更进一步明确了规则之间的不可交易优先级和风险阈值。对于安全任务，这比不断调一个总 cost 的权重更可审计。

VLA 侧今天的三项工作分别补齐真实部署的三个阶段：

```text
VLA-Precision
→ 运行后怎样继续安全变好

FailureSpot
→ 什么时候应该认为主策略已经开始失败

TacPAC
→ 接触偏差还可恢复时怎样低延迟纠偏
```

再加上 CFAM 的“现场经验不直接改主模型权重”，可以看到机器人基础模型正在从单一 policy 变成一套拥有 watchdog、fast correction、slow adaptation 和版本边界的运行时系统。

AI Coding 也是同样的结构化趋势。LSP + verifier 的价值并不依赖某个模型版本：Agent 负责生成候选，Language Server 提供结构化项目事实，静态验证器拥有最终判定权。模型越强，这种**独立证据链**反而越重要。

## 最值得深入研究或尝试复现的方向

1. **FIRE-LIVWO-lite 退化路由器。** 不动现有 LIO 主体，先输出 LiDAR geometry eigenvalue / visual track health / wheel slip / Radar Doppler innovation，做一个独立 mode selector；在长走廊、烟尘和遮挡数据上记录它能提前多久识别 failure boundary。

2. **VLA FailureSpot + Recovery 状态机。** 给现有 π0 / π0.5 rollout 加轻量 hidden-state detector，先只做 `RUNNING → DEGRADED → RETRY/RESET → HUMAN`，测 timestamp-level lead time 和 false-stop rate，不让 detector 直接拥有危险动作权限。

3. **TacPAC 风格 Fast Residual Loop。** 即使没有完整 World-Action Model，也可以把 action chunk 的“预期接触”缓存下来，让 tactile / force expert 只修尚未执行的 100–300 ms 命令；大偏差再触发完整 replan。

4. **Coding Agent 接入 LSP / Static Verifier。** 将 Repo Search 从自由文本 grep 升级为 typed symbol/reference/diagnostic API；Agent 生成 Patch 后由 compiler、linter、static verifier 和测试给出独立 receipt，再决定是否进入下一轮。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)
- [FIRE-LIVWO](https://arxiv.org/abs/2609.05325) · [代码](https://github.com/KJ-Falloutlast/FIRE-LIVWO)
- [Risk-Aware Optimal Control with Rulebooks](https://arxiv.org/abs/2609.05199)
- [Open-Set 3D Scene Graphs for Field Robotics](https://arxiv.org/abs/2609.04607)
- [VLA-Precision](https://arxiv.org/abs/2609.04355) · [项目页](https://vla-precision.github.io/)
- [FailureSpot](https://arxiv.org/abs/2609.04277)
- [TacPAC](https://arxiv.org/abs/2609.05266) · [代码](https://github.com/LogosRoboticsGroup/TacPAC)
- [CFAM](https://arxiv.org/abs/2609.04552) · [技术说明](https://skylarklabs.ai/use-cases/cfam-stack-overview.html)
- [Large Language Models and Language Server Protocol](https://arxiv.org/abs/2609.03086) · [Eiffel-tools](https://github.com/alschena/eiffel-tools)
- [Timed Elastic Band 原始论文](https://files.davidqiu.com/research/papers/2012_rosmann_TEB%20Planner%20Trajectory%20modification%20considering%20dynamic%20constraints%20of%20autonomous%20robots%20%5BROBOTIK%202012%5D.pdf) · [teb_local_planner](https://github.com/rst-tu-dortmund/teb_local_planner)
