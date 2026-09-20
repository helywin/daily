---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-20"
date: 2026-09-20 09:00:00 +0800
description: "本期关注长期开放词汇语义记忆、受限算力持续 3DGS 建图、人形多楼层安全导航、高阶无人机安全控制、长任务阶段切换、VLA 自适应动作块、轻量未来运动世界模型与 Coding Agent 低成本 A/B 测试。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-20

## 摘要

今天是周日。arXiv Robotics 与 Software Engineering 最近公开批次仍为 **2026-09-18（周五）**，分别有 133 条和 24 条；周末没有新的常规 arXiv 批次。因此本期严格按任务规范从最近 7 天范围内继续筛选，并与覆盖索引逐项按规范标题、arXiv ID、DOI、项目页和仓库地址去重。以下 8 条主动态均为此前索引中尚未覆盖的工作，原始 v1 提交时间集中在 9 月 16–17 日，统一标为“时间回补”。最新列表可查看 [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) 与 [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

今天 SLAM / 长期地图方向最值得看的两篇工作，恰好都在讨论“地图不是一次性产物”。**PerSeM** 将开放词汇分割结果从逐帧预测升级为持久的世界坐标 voxel memory：反复观测先用 majority memory 建稳定基线，只对不确定区域再做 history-preserving refinement、trust-aware replay 和 context-guided verification。它不增加新的神经推理，也不需要重新训练，在 UAVScenes 五条序列上同时改善语义正确率、mIoU 与 temporal flicker。([论文](https://arxiv.org/abs/2609.19542))

**EliGSiR** 则直接处理持续运行的 3D Gaussian Splatting：不是假设全部图像已经离线收齐，再跑一大轮优化，而是在固定算力预算下动态决定“哪些 view 值得优化、当前 supervision 用多高分辨率、哪里真的需要新增 Gaussian”。在 TUM RGB-D 的 tracked-pose 对比中，EliGSiR 使用实时 ORB-SLAM3 pose，在 155.5 s 内达到 23.02 dB；CaRtGS 使用自身 tracker 为 20.10 dB / 230.9 s。([论文](https://arxiv.org/abs/2609.20348))

控制侧，**Learning Safe Humanoid Navigation from Reduced Order Models** 很适合认真研究多楼层机器人的团队。作者先在 reduced-order dynamics 上学习带完整 3D LiDAR 观测的导航，再用 KL + PPO 把导航知识迁移到完整 Unitree G1，底层 locomotion policy 保持冻结。导航策略 5 Hz 输出平面速度，底层 locomotion 50 Hz 执行；再叠加一个直接从 occupancy 构造的 Poisson safety filter。真机完成超过 10 m 垂直变化和 100 m 路径，多组 OOD / adversarial obstacles 中 safety filter 将碰撞从 2/10、4/10 降到 0/10，同时不降低任务成功率。([论文](https://arxiv.org/abs/2609.19272)，[项目页](https://wdc3iii.github.io/rom-nav/))

另一篇 **Feasibility and Singularity in High-Order Safety-Critical Control for Quadrotor UAVs** 则补上了很多 CBF 工程里被一句“QP feasible”带过的问题：单个 pairwise barrier 有控制作用，不代表多条 barrier 在共享、受限的 thrust 下能同时满足；更麻烦的是，当相对位移与可用推力方向正交时，距离 barrier 甚至会瞬间失去 thrust effectiveness。论文分别定义 pairwise effectiveness 与 aggregate feasibility margin，并通过 torque-aware fourth-order dynamic extension 把 attitude torque 显式带进 barrier，再用 GP 学 HOCBF residual 的 robust margin。([论文](https://arxiv.org/abs/2609.19362))

长任务机器人方面，**StageGuard** 把“什么时候结束当前 skill、切到下一阶段”从手写 completion checker 变成可蒸馏的在线监控器。Teacher model 结合示范轨迹产生结构化的阶段完成解释，轻量 student VLM 再学习这种 decision pattern。BEHAVIOR-1K 中，完整 StageGuard 将 hierarchical system success 从 end-to-end policy 的 0.30 提高到 0.53，接近 GT-transition oracle 的 0.63；UR5e 和 Piper 真机分别达到 18/20 与 16/20，monitor 约 2.2 Hz 并行运行。([论文](https://arxiv.org/abs/2609.20791))

VLA 执行层，**GeoAAC** 给了一个很实用的结论：action chunk 不应该永远固定长度。Flow Matching 在一次 denoising 过程中已经暴露了 action prefix 的几何变化，而这种变化和预测可靠性相关；GeoAAC 从单次生成的 denoising trajectory 直接构造 horizon-wise geometric profile，自适应决定这一拍究竟执行多长 action chunk，不需要额外训练。真实三项操作任务中，仅改变执行 horizon，就把平均成功率从固定 50-step 的 53.3% 提到 74.4%。([论文](https://arxiv.org/abs/2609.20776))

世界模型侧，**MoWAM** 继续强化最近非常明显的趋势：机器人未必需要在推理时生成完整 future video。它训练阶段仍学习视觉未来，但部署时只显式预测结构化 future robot motion，并与 action 联合生成；再通过 motion-aware task-progress verifier 在多个 motion-action candidate 之间选择。Franka 三项真机任务平均成功率达到 80%，相对 Fast-WAM 提高 35 个百分点，同时只增加约 33.4 ms action-generation latency；相对 Motus，latency 从 1621.9 ms 降到 293.5 ms。([论文](https://arxiv.org/abs/2609.20709))

AI Coding 侧，**DeltaSelect** 很适合真正长期迭代 Codex / Claude skills、prompt 与 harness 的团队。完整 SWE benchmark 太贵，一两次随机抽题又很不稳定；DeltaSelect 从历史 benchmark trials 中筛选“一次运行结果仍能稳定跟踪全 benchmark”的任务，并在给定美元预算内固定一组 A/B regression set。论文自己的 gpt-5.6-luna low-reasoning case study 做了 13 次 evaluation，总记录成本 27.86 美元；最终采用配置相对初始配置成本下降 58.1%，calibrated score 从 36.46% 观察到 42.36%，但作者也明确说明分数提升在其方差模型下没有统计显著性。这个“把不确定性写出来”比单纯宣称 prompt 提升更值得学。([论文](https://arxiv.org/abs/2609.19607))

近期通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic 与 Google DeepMind 的公开发布入口，没有发现 9 月 19–20 日需要新增报道的通用旗舰正式发布；Claude Code 在 9 月 19 日有新的运行时 / Agent 工程更新，放在后面的社区精选中讨论，不把 CLI 更新混写成“新基础模型”。

## 1. PerSeM：开放词汇语义地图最先需要解决的，不是类别更多，而是“同一个地方别每天换标签”

**时间回补：v1 提交于 2026-09-17 01:07 UTC。**

### 为什么重要

开放词汇分割已经能让无人机输出非常丰富的逐帧语义，但逐帧结果天然会抖：

```text
同一栋建筑
这一帧 → building
下一帧 → structure
再下一帧 → warehouse
```

视角、尺度、遮挡和模型置信度变化都会让标签在时间上漂移。如果直接把每帧标签投进地图，长期地图虽然“词汇开放”，却没有稳定记忆。

PerSeM 的核心判断很务实：

> 先让重复世界观测形成一个稳定的 3D majority memory，再只处理剩下真正不确定的少数区域。

### 算法模块

```text
Frame-wise Open-Vocabulary Segmentation
              ↓
World-space Voxel Association
              ↓
Persistent Majority Memory
              ↓
仅针对 Uncertain Memory State：
  ├─ History-preserving Spatial Refinement
  ├─ Trust-aware Replay
  └─ Context-guided Verification
              ↓
Persistent Semantic Map
```

这里最值得注意的是“conservative refinement”。系统不会因为最近一帧看起来很自信，就粗暴覆盖已经由多次历史观测建立的稳定标签。

### 结果与工程边界

在 Forest 与 UAVScenes 上，真正占最大收益的是“持久 3D aggregation”本身。以 UAVScenes 五条序列的宏平均为例：

```text
Raw2D:
PA       77.50
mIoU     36.32
Flicker  13.73

Raw3D Majority:
PA       81.21
mIoU     41.50
Flicker   7.27

PerSeM:
PA       81.41
mIoU     41.90
Flicker   6.90
```

这说明第二阶段 refinement 是锦上添花，而第一原则其实更朴素：

> **机器人已经多次看见过同一个地方，就不要每一帧重新从零决定“这里是什么”。**

### 实时性与资源

PerSeM 不增加额外 open-vocabulary neural inference，也不需要 retraining。

论文未优化研究实现中，Forest 约 19.4K voxel、峰值内存 0.93 GB；UAVScenes 约 291.8K voxel、峰值内存 3.17 GB。PerSeM-specific refinement 分别约 2.82 s 和 39.10 s，而大头之一是为了 benchmark 输出 dense image-space prediction 的 reprojection，并非维护 voxel memory 的必要开销。

### 风险

当前方法还没有显式建模 pose uncertainty 和动态场景。

如果 UAV 的 map pose 本身漂了 1–2 m，错误的 world-space voxel association 会把不同物理区域混成“持久记忆”，此时语义越稳定，反而可能越稳定地错。

所以产品里至少需要：

```text
voxel_semantic_state
observation_count
pose_uncertainty_at_observation
last_seen
source_view_diversity
```

而不是只有一个最终 label。

### 适合谁关注

开放词汇地图、无人机巡检、语义导航、长期场景记忆、3D scene graph。

### 工程落地启发

如果现有系统已经有 LIO-SAM / ORB-SLAM3 / 3DGS，不需要先做 PerSeM 全套。第一步只要把 semantic observation 从：

```text
map_xyz + label
```

升级成：

```text
stable voxel / object id
+ label histogram
+ observation history
```

就能先吃到最主要的“多视角稳定化”收益。

[论文](https://arxiv.org/abs/2609.19542)

## 2. EliGSiR：持续 3DGS 的核心不是“永远多优化几步”，而是把有限算力花在最值得的地方

**时间回补：v1 提交于 2026-09-17 13:12 UTC。**

### 为什么重要

传统 3D Gaussian Splatting 的默认世界是：

```text
所有图像已经收齐
        ↓
离线优化很久
        ↓
得到最终模型
```

机器人在线 mapping 恰好相反：

```text
新 RGB-D 不断到来
旧区域不能忘
算力预算固定
地图还要随时可用
```

因此真正的问题不是“最终 PSNR 能有多高”，而是：

> 在第 30 秒、第 60 秒、第 5 分钟，机器人手里那张**正在使用的地图**质量怎么样？

### 三个核心预算控制器

EliGSiR 从三个维度分配固定 mapping budget：

```text
1. Map-Guided View Scheduling
   → 新帧太冗余就不优化
   → 旧帧是否值得 replay 由当前地图状态决定

2. Load-Adaptive Fidelity
   → mapping load 高时降低 supervision resolution
   → 空闲时再用高分辨率补细节

3. Targeted Geometry Growth
   → depth supervision ≠ 一看见 depth 就创建新 Gaussian
   → 只有重复 RGB-D 证据说明几何缺失 / 错位时才扩 representation
```

这本质上把“地图增长”也变成一个需要预算审批的动作。

### 结果

TUM RGB-D `fr3/long_office_household`：

```text
GT mapping poses:
SplaTAM   19.42 dB / 1382.6 s
EliGSiR   21.52 dB /  176.1 s

Tracked poses:
CaRtGS    20.10 dB / 230.9 s
EliGSiR + live ORB-SLAM3
          23.02 dB / 155.5 s
```

这里最有意义的不是单个 PSNR，而是它证明“限预算调度”不一定要牺牲地图质量。

### 传感器与假设

它是 RGB-D continual mapping，依赖外部 tracking 或 live ORB-SLAM3 pose。

因此 EliGSiR 并不是新的完整 SLAM 前端；tracking 漂移、回环大幅改写 pose 时，Gaussian representation 与历史 keyframe supervision 的一致性仍然需要系统层处理。

### 工程风险

长期运行最大的风险是“旧地图债务”：

```text
早期低分辨率 supervision
+ 当时 pose 不准
+ 后面一直没被重新 schedule
→ 形成永久低质量区域
```

产品最好给 map region 保存：

```text
last_optimized
view_support
pose_revision
geometry_residual
fidelity_level
```

这样后台才能知道哪里值得补算力。

### 适合谁关注

RGB-D 机器人、3DGS SLAM、持续扫描、数字孪生、边缘 GPU 上的在线重建。

### 工程落地启发

如果正在做 3DGS mapping，先别急着上更大 GPU。可以先把每个 optimization step 都问一句：

```text
这一步是在修真正有证据的地图缺陷，
还是只是因为“新帧来了所以照例优化”？
```

调度策略往往比盲目增加 iteration 更容易把在线系统做稳。

[论文](https://arxiv.org/abs/2609.20348)

## 3. RoM-Nav：多楼层人形导航可以先在“简化身体”里学去哪，再交给完整 G1 学怎么走

**时间回补：v1 提交于 2026-09-16 18:00 UTC。**

### 为什么重要

单阶段 humanoid navigation RL 需要同时学：

```text
去哪
+
楼梯 / 坡道是否可通行
+
完整全身动力学如何执行
+
别摔
```

问题会非常难，尤其是跨楼层任务。论文实验也显示，Single-Stage PPO 的主要差距恰好出现在 cross-level goal，而不是普通同层移动。

RoM-Nav 把问题拆成两个难度层级。

### 训练与运行结构

第一阶段在 reduced-order model 上学习导航：

```text
3D LiDAR / Depth
      ↓
Navigation Policy on RoM
      ↓
planar velocity
```

其动力学被简化成带 heading 的 single integrator；撞 occupancy boundary 时只把穿入分量投影掉，允许 policy 迅速学会“从哪里走”。

第二阶段再把这份导航知识迁移给完整 humanoid：

```text
RoM Policy
   ↓ KL guidance
Full Humanoid Navigation Policy
   ↓ 5 Hz planar command
Frozen Locomotion Policy
   ↓ 50 Hz
Unitree G1
```

KL 权重从早期强约束逐步衰减，让 full-order policy 先沿用 RoM 的路线知识，再适应真正的人形动力学。

### 传感器与真机

部署配置：

- Unitree G1；
- MID360；
- 向下 ZED Mini depth；
- navigation 5 Hz；
- frozen locomotion 50 Hz。

真机包含：

- 7 m 两层楼梯；
- 10 m 垂直爬升；
- 最长约 100 m path；
- mapless policy。

### Poisson Safety Filter

更值得工程化的是安全层。LiDAR point cloud 被投成 0.05 m occupancy grid，去地面并按机器人半径膨胀，然后解 Poisson equation 直接从 occupancy 生成 barrier function。

最后只做一个最小修改：

```text
desired velocity
       ↓
Poisson CBF-QP
       ↓
closest safe velocity
```

真机共享初始条件实验中：

```text
OOD obstacles:
无 CBF   2/10 collision
CBF      0/10 collision

Adversarial hanging obstacles:
无 CBF   4/10 collision
CBF      0/10 collision
```

成功率保持 10/10，但到达时间有所增加。

### 风险与边界

它仍然依赖准确 body-frame goal，而且 LiDAR 对玻璃等透明障碍不足；论文甚至在一个场景里用纸板遮住玻璃门 / 窗以避免错误穿越。

这恰好说明安全 filter 的保证永远只覆盖**进入 occupancy 的障碍证据**。

### 适合谁关注

Unitree G1、多楼层导航、机器狗 / 人形楼梯、mapless navigation、安全导航层。

### 工程落地启发

对已有第三方 locomotion SDK 的机器人特别合适：

> 不要让导航 RL 重新学 gait。

让底层 gait 保持冻结，只学习 5–10 Hz 的 `vx / vy / wz` 导航，再在这层输出上加独立安全 filter，工程复杂度会低很多。

[论文](https://arxiv.org/abs/2609.19272) · [项目页](https://wdc3iii.github.io/rom-nav/)

## 4. 高阶 Quadrotor CBF：每一条避碰约束“各自可行”，不代表它们一起可行

**时间回补：v1 提交于 2026-09-16 19:34 UTC。**

### 为什么重要

多无人机 CBF-QP 经常写成：

```text
每一对 UAV：
h_ij >= 0

把所有 barrier inequality
一起塞进 QP
```

然后一句：

> assuming QP remains feasible.

但真实 bounded actuator 下，至少有两种完全不同的失败：

```text
A. Pairwise singularity
   → 这一对 UAV 当前几何下
     thrust 根本无法立刻改变 barrier

B. Aggregate infeasibility
   → 每一条 constraint 单看都能满足
   → 但同一组受限 thrust
     不可能同时满足所有 pair
```

这篇论文把两者拆开量化。

### Pairwise Effectiveness

距离 barrier：

```text
h_ij = ||p_i - p_j||² - d_min²
```

二阶 HOCBF 中，thrust 影响项由相对位置和两个机体 thrust direction 决定。

当相对位移同时与两个可用 thrust 方向正交时，输入系数变为零：

```text
γ_ij^th = ||B_ij||

γ → 0
→ thrust 对这一条 barrier
  瞬时失去作用
```

所以“距离还很远”并不自动等于“现在还有避让 authority”。

### Aggregate Feasibility

作者进一步定义一个 scalar margin：

```text
Γ_th^rob
=
在所有合法 thrust 中
选择一组输入，
让最差那条 HOCBF inequality
还能剩多少共同 margin
```

于是：

```text
Γ > 0  → 有严格余量
Γ = 0  → 临界
Γ < 0  → 在当前 input bounds 下联合无解
```

它比只看 solver 最后报 infeasible 更早暴露“安全约束正在互相挤压”。

### 为什么需要 Torque-Aware Fourth-Order Extension

Quadrotor translational thrust 只能沿 body z 轴。

论文进一步做 dynamic extension，让 thrust rate 在三阶出现、attitude torque 在四阶 barrier 中显式出现，从而允许 torque 改变未来 thrust direction，避免二阶 thrust channel 在某些几何位置彻底消失。

再用 GP 直接学习 fourth-order HOCBF residual，为未知扰动提供 robust margin，而不是反复对未知 perturbation 求导。

### 当前证据边界

论文主要是理论分析 + simulation，没有真实机群实验，因此不能把它写成“已经真机证明的多无人机安全方案”。

它最大的工程价值，是提供两个运行时健康量：

```text
pairwise_effectiveness
aggregate_feasibility_margin
```

### 适合谁关注

无人机群、CBF、受限推力控制、MPC safety layer、狭窄空间多机避碰。

### 工程落地启发

即使不实现四阶 HOCBF，也建议让现有 safety QP 输出：

```text
constraint_effectiveness
feasibility_margin
active_constraints
input_headroom
```

安全系统不应该等到 `solver = infeasible` 才第一次知道自己快没路了。

[论文](https://arxiv.org/abs/2609.19362)

## 5. StageGuard：长任务真正容易坏的地方，经常不是 Skill 本身，而是“什么时候切下一个 Skill”

**时间回补：v1 提交于 2026-09-17 17:53 UTC。**

### 为什么重要

Hierarchical robot system 常有：

```text
OpenDrawer
→ PickPlate
→ PlacePlate
→ CloseDrawer
```

每个 skill 单独都可能做得不错，但执行链必须不断判断：

```text
当前 skill 真的完成了吗？
现在切换会不会太早？
继续执行会不会已经过头？
```

手写 completion checker 对 learned policy 很难维护；直接让大 VLM 每一拍在线推理又太慢，而且 VLM 的“看起来已经完成”并不天然等价于真正 task completion。

### Agentic Distillation

StageGuard 将大模型留在训练 / 蒸馏侧：

```text
Teacher VLM / Agent
+ Demonstration Trajectory
+ Task Requirement
        ↓
Structured Completion Explanation
        ↓
Lightweight Student VLM
        ↓
Compact Self-Explanation
        ↓
Stage Complete?
yes / no
```

重点不是只蒸馏一个二分类标签，而是先让 teacher 解释“哪些观察证据对应哪些任务条件”，再让 student 学这种 decision pattern。

### 系统结果

BEHAVIOR-1K：

```text
End-to-end policy
Success       0.30
Progress      0.43

Hierarchical + GT transition oracle
Success       0.63
Progress      0.88

StageGuard
Success       0.53
Progress      0.76
```

这说明 hierarchical planning 的上限很高，但如果 transition monitor 不准，收益会大量丢失。

### 真机

50 条 demonstration trajectory 用于训练，之后：

```text
UR5e:
18 / 20 success

Piper:
16 / 20 success
```

Piper 四次失败全部来自薄板抓取失败，不是 StageGuard transition error。

StageGuard 大约 **2.2 Hz** 并行运行，没有观察到阻塞本地 VLA control loop。

### 风险

Stage transition 仍然是部分可观测问题。

例如“物体是否已经完全进入抽屉内部”可能从某个 camera 角度看不清；论文 UR5e 的一个失败就是 plate placement → drawer closing 的 transition miss 与 partial observability 有关。

所以 monitor 最好能输出：

```text
COMPLETE
INCOMPLETE
UNCERTAIN
```

而不是永远强迫二选一。

### 适合谁关注

长时操作、Skill orchestration、VLA + classic skill 混合系统、机器人 Agent。

### 工程落地启发

如果做机器人 Agent，真正值得标准化的不只有：

```text
Skill.execute()
```

还应该有：

```text
SkillCompletionEvidence {
  observable_conditions
  satisfied_conditions
  uncertain_conditions
  confidence
}
```

高层 Agent 决定下一步，StageGuard 这类模块负责把视觉状态编译成可检查的 transition evidence。

[论文](https://arxiv.org/abs/2609.20791)

## 6. GeoAAC：VLA 的 Action Chunk 应该跟着“当前预测可靠性”变长变短

**时间回补：v1 提交于 2026-09-17 17:48 UTC。**

### 为什么重要

固定 action chunk 有一个很明显的矛盾：

```text
自由空间长距离移动
→ 希望 chunk 长
→ 少调用模型、更流畅

接近物体 / 对孔 / 拧盖
→ 希望 chunk 短
→ 更频繁看新图像、闭环修正
```

但很多 VLA 仍然使用固定 horizon。

GeoAAC 的有趣之处在于：它没有再训练一个 uncertainty model，而是直接利用 Flow Matching 本来就会产生的 **denoising trajectory geometry**。

### 核心观察

在一次 flow-based action generation 内，可以观察不同 action prefix 随 denoising 如何变化。

论文发现：

> prefix 的 geometric variation 与 predictive uncertainty 正相关。

于是可以构造：

```text
Flow Denoising Trajectory
        ↓
每个 Action Prefix 的变化几何
        ↓
Horizon-wise Geometric Profile
        ↓
决定当前实际执行到第几步
```

整个过程只需要**一次 action generation**，不需要额外模型和重新训练。

### 结果

模拟中，相对最佳 fixed horizon：

- RoboCasa365：最高 +8.7 个百分点；
- LIBERO-Pro：最高 +5.3 个百分点。

三项真机任务、每项 30 次：

```text
Fixed-50:
Extinguish   16.7
Disconnect   76.7
Uncap        66.7
Avg          53.3

GeoAAC:
Extinguish   36.7
Disconnect  100.0
Uncap        86.7
Avg          74.4
```

模型权重和训练数据相同，变化只来自执行 horizon。

### 为什么这比“根据动作速度调 chunk”更合理

关键不是动作本身快慢，而是：

```text
现在预测的未来 action
到底有多稳定？
```

接近高精度操作阶段时，Flow trajectory 自己开始出现更明显 prefix variation，系统就主动缩短执行段，尽快获取新 observation。

### 风险

这种 reliability signal 是模型内部生成过程的 proxy，不是形式 uncertainty。

如果 Flow model 在 OOD 场景里非常“稳定地自信犯错”，几何 profile 也可能判断 chunk 很长。

所以产品里应该再设置硬上限：

```text
max_chunk_by_task_phase
max_chunk_by_speed
max_chunk_by_safety_distance
```

不要让 learned confidence 独占控制频率。

### 适合谁关注

π0.5、GR00T、Flow Matching VLA、端侧 VLA latency 优化、精密操作。

### 工程落地启发

如果现在 VLA 每次固定执行 20 / 50 个 action，先别急着换模型。

**action horizon 本身就是一个非常便宜的控制变量。**

先把 horizon 做成 runtime policy，往往可以在不动训练集的情况下同时改善成功率与推理成本。

[论文](https://arxiv.org/abs/2609.20776)

## 7. MoWAM：World Model 的未来不一定是一张 RGB 图，可能只需要回答“机器人会怎么动”

**时间回补：v1 提交于 2026-09-17 17:07 UTC。**

### 为什么重要

传统 WAM 很自然地想到：

```text
current observation
      ↓
generate future video
      ↓
action
```

但 future RGB 包含很多对控制没有价值的信息：

```text
纹理
背景
阴影
光照细节
```

推理成本却很高。

MoWAM 保留“显式未来”这个思想，但把 future representation 换成 **structured robot motion**。

### 训练与推理

训练时 Mixture-of-Transformer 同时学习：

```text
future visual dynamics
future motion
action
```

但部署时删掉完整 future video generation：

```text
Current Scene
      ↓
Future Robot Motion
      +
Action
```

未来仍然是显式的，只是变成更紧凑、与执行直接相关的 motion abstraction。

### Inference-Time Scaling

motion representation 还可以做一个非常自然的 test-time search：

```text
sample N × (motion, action)
          ↓
motion-aware task-progress verifier
          ↓
选择最值得执行的一组
```

例如 Pick Banana 中，candidate 数：

```text
1 → 65%
4 → 75%
8 → 80%
```

说明显式 motion 不只是 auxiliary loss，还可以成为候选评价证据。

### 真机

Franka Research 3：

- Pick Banana；
- Stack Bowls；
- Close Drawer。

MoWAM 平均成功率 **80%**。

相对 Fast-WAM：

```text
平均成功率 +35 个百分点
额外 action latency 约 +33.4 ms
```

相对 Motus：

```text
1621.9 ms
→
293.5 ms
```

同时平均成功率更高。

### 重要边界

论文自己给了一个很有价值的负结果：在部分 OOD 条件下，motion-only future 仍然低于最好的 visual-future WAM。

所以结论不是：

> RGB future 没用了。

而是：

> **如果目标是部署效率，future motion 是一个很强的低成本中间表示；复杂视觉分布变化下，完整视觉未来仍可能提供额外信息。**

### 适合谁关注

World Action Model、VLA、机器人 world model、推理时搜索、边缘端操作策略。

### 工程落地启发

做 world model 时可以把 future prediction 分级：

```text
Level 1: robot motion
Level 2: object / contact motion
Level 3: depth / geometry
Level 4: full RGB video
```

只有下一级确实不能解释当前失败时，再承担更昂贵的未来生成成本。

[论文](https://arxiv.org/abs/2609.20709)

## 8. DeltaSelect：调 Coding Agent 不需要每次重跑整个 Benchmark，但“小测试集”必须证明自己真的能代表整体

**时间回补：v1 提交于 2026-09-17 02:42 UTC。**

### 突破性工程价值

日常改 Coding Agent 往往只是：

```text
改一条 AGENTS.md
换一个 Skill
换 context policy
改 tool description
```

如果每次都跑完整 SWE-bench：

```text
贵
慢
不适合高频 iteration
```

但随便抽 10 道题也不可靠。

DeltaSelect 问的是：

> 哪些 benchmark task 的**单次结果**，在历史试验中仍然稳定跟踪 full benchmark 的变化？

### 方法

先用已有多次 benchmark trial 做 resampling：

```text
Full Benchmark Historical Trials
          ↓
每个 Task 的 one-run result
与 overall performance 做 correlation
          ↓
筛高稳定性 Task
          ↓
Fractional verifier score
用 linear regression 校准到共同尺度
          ↓
在固定 Dollar Budget 下
选一个固定 A/B Set
```

论文分析 DeepSWE published trials 时，113 个任务里只有 **22 个（19.5%）** 的 fifth-percentile Pearson correlation 至少达到 0.50。

也就是说，大多数“随便抽来的便宜题”其实不适合做日常回归代理。

### Case Study

作者用 gpt-5.6-luna low-reasoning 调 custom skills / instructions：

- 13 次 evaluation；
- 总记录成本 27.86 美元；
- 初始配置：4.18 美元 / calibrated 36.46%；
- 最终采用配置：1.75 美元 / calibrated 42.36%。

成本下降 **58.1%**。

但论文也明确指出：

> observed score +5.90 pp 在 transferred-variance model 下 p=0.326，不能证明总体性能显著提升。

这点非常重要：**别把一次小 A/B 的方向性改善包装成 benchmark 胜利。**

### 是否适合真实研发流程

非常适合维护自己的 Agent regression suite。

但最好不要直接复制论文筛出的公开 task，而应该用公司自己的历史失败数据重新选：

```text
哪些任务对 harness change 最敏感？
哪些任务重复运行方差较小？
哪些 task 能代表真实 workload？
```

### 风险

固定小集合最终也会被过拟合。

所以合理结构应该是：

```text
Daily / PR:
Delta regression set

Weekly:
larger held-out set

Major release:
full benchmark + production shadow
```

### 工程落地启发

Vibe Coding 真正需要的不是“每次感觉这版好像更聪明”，而是一个**便宜到愿意天天跑、但又经过代表性校准的 Agent unit test**。

[论文](https://arxiv.org/abs/2609.19607)

## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### 1. Claude Code 原生支持 AGENTS.md：跨 Claude / Codex 项目最好选一个 Canonical Instruction Source

**来源：Claude Code v2.1.277，2026-09-18 官方 release。**

Claude Code 现在原生支持 `AGENTS.md`：项目没有 `CLAUDE.md` 时，会读取 `AGENTS.md`，并可以在 `/config` 的 Project instructions 中调整。这个变化很适合同时使用 Claude Code、Codex 和其他 Coding Agent 的仓库，因为 `AGENTS.md` 正在成为更通用的项目级 Agent instruction 载体。([官方 Release](https://github.com/anthropics/claude-code/releases))

**技巧是什么：**

不要维护两套互相复制的长规则：

```text
CLAUDE.md
AGENTS.md
```

然后希望它们永远同步。

更合理的是定义一份 canonical source：

```text
AGENTS.md
→ 跨 Agent 的稳定项目约束

工具专属文件
→ 只保留该工具独有行为
→ 或明确引用 canonical docs
```

**今天可以直接用：**

把跨工具规则收敛为：

```text
Build / Test commands
Architecture invariants
Do-not-touch paths
Generated-code rules
Definition of done
```

而 Claude / Codex 独有配置放在各自工具层，不复制业务架构说明。

**边界：**

Claude 当前的 AGENTS.md 支持仍有平台差异；官方 release 明确写着当时尚未覆盖 Bedrock、Vertex、Foundry。多 Agent 仓库仍应在 CI 中验证每个实际运行环境加载的 instruction source，而不是只因为文件存在就默认已经生效。

### 2. Instruction File 也会“代码腐烂”：给 AGENTS.md / CLAUDE.md 加机械式 Pre-commit 校验

**来源：2026-09-19 Reddit r/ClaudeCode 社区实践；属于社区经验。**

近期一个很实用的社区案例指出：很多看起来像“Agent hallucination”的问题，其实是 `CLAUDE.md` / `AGENTS.md` 还在引用已经删除的文件、组件或旧 API。作者做了一个只有 39 行 shell 的 pre-commit 检查，用来验证：

- referenced paths 仍存在；
- 已删除名字没有残留在 instruction；
- instruction 的修改已经 staged。

([Reddit 原讨论](https://www.reddit.com/r/ClaudeCode/comments/1wk018t/your_claudemd_can_reference_code_that_no_longer/))

**为什么值得学：**

Agent instruction 已经是代码库的一部分依赖关系。

如果写着：

```text
修改 API 时同步更新 src/legacy/client.ts
```

但这个文件三周前已经删了，模型严格遵守 instruction 反而会被误判成“又在胡说”。

**今天可以直接用：**

CI / pre-commit 至少做：

```text
path existence
command existence
documented API symbol grep
instruction file staged check
```

并把动态架构说明移到 versioned docs，只让 AGENTS.md 保留真正稳定的 invariant。

**边界：**

机械检查只能发现“引用不存在”，不能判断 instruction 在语义上是否过时。关键架构规则仍需要 review；但这种 0-token guardrail 非常适合先挡住最常见的 stale-context 错误。

### 3. Auto Mode 的分类器跑在哪也应该进入 Telemetry：不要只观察“Agent 最后有没有成功”

**来源：Claude Code v2.1.278，2026-09-19 官方 release。**

Claude Code 最新版将 Claude API / Enterprise，以及 Bedrock、Vertex、Foundry、gateway 场景的 Auto Mode 默认改为 **server-side classifier**；`/status` 新增 `Auto mode server`，用于显示当前 session 的 classifier 是否在服务端运行，并对可能产生额外计费的 fallback 给出警告。([官方 Release](https://github.com/anthropics/claude-code/releases))

这背后的通用技巧是：

> **Agent 的 routing / permission / classifier 到底运行在哪一层，也属于运行时配置，必须能被观测。**

同一个 prompt / model，如果 classifier 从本地换成 server、gateway fallback 或企业策略层，延迟、成本和允许的行为都可能变化。

**今天可以直接用：**

自研 Agent receipt 增加：

```text
model
reasoning_effort
router_version
classifier_location
fallback_used
policy_revision
```

遇到“今天同样命令为什么突然慢 / 贵 / 被拒绝”时，先比较 runtime receipt，而不是马上改 prompt。

**边界：**

这是工具运行时工程经验，不是模型能力提升。Classifier 放服务端不代表输出更聪明；它主要影响权限判断、成本可见性和运维一致性。

## 经典论文回顾

### SemanticFusion：机器人为什么应该“融合多次语义观测”，而不是把每帧 CNN 标签直接贴到地图上

John McCormac、Ankur Handa、Andrew Davison 与 Stefan Leutenegger 的 **SemanticFusion: Dense 3D Semantic Mapping with Convolutional Neural Networks** 发表于 **ICRA 2017**。它将 ElasticFusion 的实时 RGB-D dense SLAM 与 CNN semantic segmentation 结合，是现代 3D semantic mapping 非常经典的一条起点。([DOI](https://doi.org/10.1109/ICRA.2017.7989538)，[项目页](https://www.imperial.ac.uk/dyson-robotics-lab/downloads/semanticfusion/))

### 核心问题

单帧语义分割有噪声：

```text
View A → chair 0.70
View B → sofa  0.55
View C → chair 0.82
```

但 SLAM 已经知道 A/B/C 看到的是**同一个三维表面**。

既然几何系统提供了跨帧 correspondence，就没有理由让语义层每帧重新投票、互相独立。

### 系统结构

```text
RGB-D Frame
   ├─ ElasticFusion
   │   → camera pose
   │   → dense surfel map
   │   → long-term correspondence
   │
   └─ CNN semantic prediction
       → per-pixel class probability
              ↓
将 2D prediction 投到可见 surfel
              ↓
每个 surfel 保存 class distribution
              ↓
Recursive Bayesian Fusion
              ↓
Dense 3D Semantic Map
```

核心不是“给地图染一个最终颜色标签”，而是**每个 3D 元素维护一个随观测更新的语义概率分布**。

### 当年为什么重要

SemanticFusion 展示了一个非常关键的事实：

> 多视角融合不仅让 3D semantic map 更稳定，甚至可以反过来改善单帧 2D labeling。

因为同一个物理表面在不同视角下积累的证据，可以抑制某一帧 CNN 的偶发错误。

系统当年已经能做到约 **25 Hz** interactive use，这让 semantic mapping 从离线 post-processing 进入真正实时机器人管线。

### 传感器与假设

原系统强依赖：

- RGB-D；
- 室内场景；
- ElasticFusion 的稳定 surfel correspondence；
- closed-set CNN semantic classes。

它的“持久语义”依然建立在 geometry correspondence 正确的前提上。

错误 loop / pose drift 会把错误语义融合到一起；动态物体也会破坏“一个 surfel 对应长期稳定物理表面”的假设。

### 今天仍然在使用的思想

现代 open-vocabulary / 3DGS / foundation-model semantic mapping 已经完全换了网络，但几个原则没有变：

```text
1. 语义应该绑定稳定的 3D identity
2. 多帧 evidence 应累积，不应逐帧覆盖
3. uncertainty / probability 比单标签更重要
4. geometry correspondence 是 semantic memory 的地基
```

今天的 PerSeM 本质上继续回答同一个问题，只是从 closed-set indoor RGB-D 扩展到 open-vocabulary UAV 长时地图，并进一步处理 history / trust / context。

### 已被后续替代的部分

今天通常会用：

- open-vocabulary segmentation / VLM；
- object-level / voxel-level semantic memory；
- 3D Gaussian / neural implicit map；
- instance identity 与 scene graph；
- dynamic-scene filtering；
- uncertainty-aware fusion。

所以不建议为了“经典”去移植 SemanticFusion 老代码作为新项目底座。

真正值得保留的是**概率式、多视角、持久语义融合的系统思想**。

### 公开代码与可复现性

Imperial College 仍提供 SemanticFusion 软件和说明。需要注意其项目页列出的软件许可条件，并不是“随便拿来商用”的无条件开放许可。

论文与项目：

- [arXiv:1609.05130](https://arxiv.org/abs/1609.05130)
- [ICRA DOI](https://doi.org/10.1109/ICRA.2017.7989538)
- [Imperial SemanticFusion](https://www.imperial.ac.uk/dyson-robotics-lab/downloads/semanticfusion/)

### 对当前工程项目的重新解读

今天做 LiDAR / RGB-D 语义地图，最常见的错误仍然是：

```text
segmentation result
→ 直接覆盖 map label
```

更合理的是：

```text
Stable Map Element
  ├─ geometry
  ├─ semantic evidence history
  ├─ current posterior
  ├─ source pose / revision
  └─ confidence / freshness
```

如果以后接入开放词汇模型，模型只是新的 **measurement source**，不应该自动成为地图真值。

这也正是 SemanticFusion 到 PerSeM 近十年仍然共通的思想：

> **神经网络负责提出语义观测，地图负责把观测变成记忆。**

## 今日结论

今天没有新的周末 arXiv 批次，但 9 月 18 日的 133 条 Robotics / 24 条 Software Engineering 中，仍然有一批此前未覆盖且工程价值很高的工作。最清晰的一条主线是：**系统正在从“每帧做一次聪明预测”转向“长期维护可信状态”。**

PerSeM 与 SemanticFusion 前后呼应。2017 年的 SemanticFusion 已经证明多视角语义证据应该绑定到稳定 3D map element 并持续融合；PerSeM 则把这个思想推到 open-vocabulary、长时 UAV mapping，并进一步把“已经稳定的记忆”和“真正不确定、值得重新判断的区域”区分开。

EliGSiR 解决的是同一个长期问题的算力版本：持续地图不能无限优化，系统必须知道哪些 view、哪些 region、哪些 fidelity 现在值得消耗预算。长期建图未来越来越像一个资源调度器，而不是“每来一帧就完整处理一遍”的流水线。

控制侧的两项工作也共同强调**分层**。RoM-Nav 让 reduced-order model 先学导航，再让完整 G1 学真实身体执行；同时用独立 Poisson safety filter 约束最终速度。高阶 Quadrotor CBF 则进一步提醒：Safety layer 不能只问“barrier 公式写出来了吗”，还要实时知道 control effectiveness 和多约束联合 feasibility 是否正在消失。

机器人策略侧，StageGuard、GeoAAC、MoWAM 分别在三个不同时间尺度上做“不要固定死”：

```text
StageGuard
→ 什么时候切 skill

GeoAAC
→ 这一拍 action chunk 执行多长

MoWAM
→ 未来信息到底用什么表示
```

它们都没有简单把模型做得更大，而是让系统根据当前证据改变执行粒度。

AI Coding 侧，DeltaSelect 与今天三条社区技巧可以放到同一张图里理解：

```text
AGENTS.md / CLAUDE.md
→ 需要稳定、可校验

Runtime classifier / router
→ 需要有 telemetry

Agent prompt / skill change
→ 需要便宜但经过校准的 regression set
```

成熟 Vibe Coding 的下一步不是继续堆规则，而是把 **instruction、runtime policy、evaluation** 都当成可版本化、可观测、可回归的软件资产。

如果把今天整期压缩成一句话：

> **无论 SLAM、控制、VLA 还是 Coding Agent，可靠系统的关键越来越不是单次输出有多聪明，而是它有没有可持续更新的记忆、预算、可信度和验证闭环。**

## 最值得深入研究或尝试复现的方向

1. **Semantic Memory Sidecar。** 在现有 LIO-SAM / ORB-SLAM3 上不给主前端加负担，只增加 `stable_element_id + semantic_histogram + last_seen + pose_revision`。先比较逐帧覆盖与多视角 persistent vote 对长期语义 flicker 的影响，再决定是否引入更复杂的 trust/context refinement。

2. **3DGS Mapping Budget Scheduler。** 给现有 Gaussian mapper 增加三项 telemetry：`view_redundancy / region_geometry_residual / last_optimized`，固定每秒 optimization budget，比较“平均分配”与“证据驱动分配”在持续扫描 10–30 分钟后的地图质量和 GPU 使用。

3. **Reduced-Order Navigation + Frozen Locomotion。** 对第三方机器狗 / 人形 SDK，不碰 gait，先在简化 2D/2.5D dynamics 上训练 5–10 Hz `vx/vy/wz` navigation policy，再迁移到真实机器人；安全层独立做 occupancy / CBF filter。重点统计跨楼层、楼梯和 OOD obstacle，而不是只测平地成功率。

4. **Action-Horizon Runtime Controller。** 对现有 VLA 固定模型和权重不变，只把 action chunk length 变成动态变量。即使暂时没有 GeoAAC 的 Flow geometry，也可以先用 contact proximity、policy variance、task phase 做简单 baseline，测成功率、VLA calls / episode 与 P95 control latency。

5. **Agent Daily Regression Set。** 从自己过去真实的 Coding Agent 失败里筛 10–30 个低方差、能代表主要 workload 的任务，每次改 AGENTS.md、Skill、context policy 都固定 A/B；同时每周跑更大的 held-out set。把单次“感觉这版更好”彻底替换成可重复的成本 / 成功率曲线。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [PerSeM](https://arxiv.org/abs/2609.19542)
- [EliGSiR](https://arxiv.org/abs/2609.20348)
- [Learning Safe Humanoid Navigation from Reduced Order Models](https://arxiv.org/abs/2609.19272) · [项目页](https://wdc3iii.github.io/rom-nav/)
- [Feasibility and Singularity in High-Order Safety-Critical Control for Quadrotor UAVs](https://arxiv.org/abs/2609.19362)
- [StageGuard](https://arxiv.org/abs/2609.20791)
- [GeoAAC](https://arxiv.org/abs/2609.20776)
- [MoWAM](https://arxiv.org/abs/2609.20709)
- [DeltaSelect](https://arxiv.org/abs/2609.19607)
- [Claude Code Releases](https://github.com/anthropics/claude-code/releases)
- [社区实践：检查 CLAUDE.md / AGENTS.md 过期引用](https://www.reddit.com/r/ClaudeCode/comments/1wk018t/your_claudemd_can_reference_code_that_no_longer/)
- [SemanticFusion](https://arxiv.org/abs/1609.05130) · [DOI](https://doi.org/10.1109/ICRA.2017.7989538) · [项目页](https://www.imperial.ac.uk/dyson-robotics-lab/downloads/semanticfusion/)
