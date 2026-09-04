---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-04"
date: 2026-09-04 09:00:00 +0800
description: "本期聚焦人形机器人足端观测可信度、166 Hz 力控 MPPI、安全急停、世界模型视觉行走、主动操作增强建图、长时 VLA 意图保持、Tool Primitive Harness，以及 GPT-6 Astra。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-04

## 摘要

截至 2026-09-04 09:00（Asia/Shanghai），arXiv Robotics 最新公开列表为 2026-09-03，共 60 条，其中 31 条为 new submissions；Software Engineering 同日共 27 条，其中 12 条为 new submissions（[Robotics](https://arxiv.org/list/cs.RO/new)，[Software Engineering](https://arxiv.org/list/cs.SE/new)）。严格最近 24 小时内，高质量、可完整核验且未进入历史索引的机器人 / SLAM / 控制条目不足 5 条，因此本期按任务规范扩展到最近 7 天。除 9 月 3 日正式发布的 GPT-6 Astra 外，其余主动态的 v1 主要提交于 9 月 1–2 日 UTC，均明确标为“时间回补”。

今天状态估计侧最值得关注的是 **FOCUS**。它把腿式里程计里长期使用的“脚是否接触地面”二值判断改成连续的 **FK 观测可信度**：脚虽然接触地面，但部分支撑、脚尖拖拽和滑移会让 forward-kinematics 速度约束严重失真。FOCUS 不替换 EKF，而是让一个只依赖 IMU 与关节运动学的轻量网络输出每只脚的连续可信度，再据此混合 FK velocity 与 IMU propagation，并动态调整 EKF measurement covariance。真实 19 段步行数据的 ATE 降低 70.8%，四类动态动作平均 ATE 降低 42.7%（[论文](https://arxiv.org/abs/2609.02222)）。

控制侧有两条非常强的工程信号。**Torque-Sampling MPPI** 直接在 torque space 采样并显式求解刚体动力学，用 GPU 并行 rollout 做运动—力混合控制，真实 7-DoF 机械臂上以 0.18 s horizon 达到超过 **166 Hz solver update rate**，说明 MPPI 已经开始进入传统上由解析 operational-space / impedance controller 占据的高频接触控制层（[论文](https://arxiv.org/abs/2609.02020)）。**Safe-Stop** 则把人形机器人急停从固定动作改成“先判断当前状态到底还能不能安全停”：一个 estimator 学当前 stop policy 的经验成功概率，另一个用 Hamilton–Jacobi backup 学 reach-avoid recoverability；只有两者持续同意才真正执行 stop，否则立即切到 damping fall fallback。Unitree G1 上 OOD stop success 达 96.4%，unsafe-approval rate 为 3.89%（[论文](https://arxiv.org/abs/2609.02358)，[项目页](https://junfeng-long.github.io/safestop/)）。

人形视觉行走方面，**WM-LOCO** 将 recurrent world model 与 PPO 联合训练，不要求显式 foothold label，而是让 world model 将当前 proprioception + 单目深度压成“未来观测与奖励的预测性摘要”，再把这个 recurrent feature 提供给 policy。Unitree G1 只使用机载 proprioception 和单路深度，在 stepping stones、gap 和 narrow stairs 三类真实地形平均达到 **93.3%** 成功率（[论文](https://arxiv.org/abs/2609.02542)）。这条路线值得关注的不是“世界模型生成视频”，而是世界模型作为低维、预测性的控制状态。

主动建图侧，**MS-MEM** 很像把 next-best-view 和 manipulation planning 合并成同一个 information-gain planner。面对货架遮挡，它不仅能移动相机，还能主动 push / grasp 物体来揭露被遮挡区域；所有候选观察与操作技能使用统一 information gain 排序，同时加入 collateral disturbance constraint，避免为了多看一点把已经确定的场景大幅弄乱（[论文](https://arxiv.org/abs/2609.02493)）。这比“语义地图永远只是被动接收传感器观测”更接近真实服务机器人。

VLA 方面，**HINT** 把“语义推理频率”和“低层动作频率”彻底拆开。它只在 manipulation-pattern transition 时调用高层语义推理，确定当前 subtask / target；之后通过 multi-view grounding 与 visual tracking 持续维持这一 semantic commitment，再用 image-space highlighting 或 attention-prior injection 把目标传给冻结的 action policy，不增加 foundation action backbone 参数。双臂 PiPER 三个长时任务中，π0.5 的 full-task success 在多个任务上从 0–13.3% 提升到 30–86.7%（[论文](https://arxiv.org/abs/2609.02653)，[项目页](https://robot-hint.github.io/)）。

AI Coding / Agent Harness 侧，**HEART** 将工具调用问题从“模型背所有 API schema”改成 **Tool Primitive + 动态检索 + Planner/Router/Verifier**。ToolFace 收集 25,519 个函数，运行时只检索当前需要的工具；每个 Tool Primitive 自己处理底层 schema resolution 与执行，Agent 间通过更自然的语义接口组合。论文在五个 benchmark 上平均超过 SFT 模型 10%，相对 GPT-5.4 / Claude 4.6 Sonnet / Gemini 3.1 Pro 平均高 6%，API 成本最高下降 85%；50 个真实任务完成率为 84%（[论文](https://arxiv.org/abs/2609.01736)）。

今天的大模型重点必须单独记录：OpenAI 于 **2026-09-03 正式发布 GPT-6 Astra**。API 型号为 `gpt-6-astra`，上下文 1,050,000 tokens，最大输出 128,000 tokens，输入 / 输出价格为 $10 / $50 每百万 tokens；模型面向复杂推理、Coding、Computer Use、Research 和文档工作，并支持 web search、file search、hosted shell、apply patch、computer use、MCP 和 tool search（[模型文档](https://developers.openai.com/api/docs/models/gpt-6-astra)，[安全说明](https://openai.com/index/safety-overview-gpt-6-astra/)）。它也是 OpenAI 首个达到 Preparedness Framework **Critical cybersecurity capability** 阈值的广泛部署模型，因此企业 Agent 的权限、隔离和轨迹级监控会变得比“选哪个模型”本身更重要。

## 1. FOCUS：腿式里程计应该估计“这只脚的 FK 现在有多可信”，而不是只问接触没接触

**时间回补：v1 提交于 2026-09-02 07:34 UTC。** [论文](https://arxiv.org/abs/2609.02222)

### 为什么重要

腿式机器人只靠 IMU 会快速漂移，因此几乎所有 proprioceptive odometry 都会在脚支撑时利用 forward kinematics 提供 base velocity 约束。传统实现通常是：

```text
Contact = true  → 信任整只脚 FK
Contact = false → 不使用 FK
```

但真实动态步态并不是这种二值世界。脚掌可能只有前半部分接触、脚尖拖地、边缘滚动，甚至在 contact detector 仍为 true 时整体滑移。此时“接触”与“FK 速度约束可信”是两件完全不同的事。

FOCUS 的核心贡献正是把它变成一个连续 measurement-quality 问题。

### 算法模块

部署时网络只读取机器人真正能够稳定获得的 proprioception：

```text
IMU
+
Joint Kinematics
      ↓
FOCUS Reliability Network
      ↓
per-foot continuous FK weight
      ↓
FK velocity ↔ IMU propagated velocity blending
      ↓
adaptive EKF measurement covariance
```

网络并不直接输出 base pose，也不替代 EKF。它只估计“当前这只脚的运动学速度约束有多值得相信”。因此 learned component 的权限非常小，最终状态仍由显式 model-based estimator 管理。

训练也不需要人工逐帧标注“脚滑了 37%”。作者利用仿真自动产生的 velocity-consistency signal，加上轻量 simulator-contact regularization 学 continuous FK reliability。

### 传感器与可观测性假设

FOCUS 部署只需要 IMU 和关节运动学，不依赖可靠 torque sensing，这对大量量产人形 / 四足很现实。

但需要明确：它仍然是 **proprioceptive odometry**。没有视觉、LiDAR、GNSS 或固定世界约束时，global position / yaw 长期仍然会漂。FOCUS 解决的是“脚运动学约束什么时候不该强信”，不是创造绝对位置观测。

### 实时性与结果

论文报告：

- 仿真 walking episode ATE 降低 **83.7%**；
- 19 段真实 walking segment ATE 降低 **70.8%**；
- 四个真实 dynamic-motion routine 平均 ATE 降低 **42.7%**。

论文摘要没有给出值得直接外推到不同 CPU/GPU 的统一毫秒延迟，因此不人为补 FPS；网络输入规模和职责都较小，真正落地更应测 estimator total P99，而不是只测网络 forward。

### 鲁棒性、可复现性与风险

最大风险是 simulation-derived reliability 与真实脚底材料、鞋底摩擦、关节间隙、结构柔顺之间的 domain gap。如果网络在极端滑移时仍给高 confidence，反而会把错误 FK 以较小 covariance 强塞给 EKF。

因此生产系统应保留独立 innovation gate：learned confidence 可以调 measurement covariance，但不能绕过 residual consistency check。

### 适合谁关注

人形 / 四足 proprioceptive state estimation、视觉/LiDAR 临时失效时的高频 fallback，以及正在使用 contact-aided EKF / InEKF 的团队。

### 工程落地启发

对现有机器人，第一步不必训练 FOCUS。先把当前 estimator 的二值 contact gate 改成可接受连续 `foot_observation_confidence` 的接口，并记录：

```text
foot_contact
FK_velocity_residual
slip_indicator
innovation
estimated_confidence
```

只要确认“滑移前后 residual 分布明显变化”，就已经具备做连续可信度估计的基础。

## 2. Torque-Sampling MPPI：让 MPPI 直接在力矩空间做 166 Hz 接触控制

**时间回补：v1 提交于 2026-09-02 02:46 UTC；IROS 2026 接收。** [论文](https://arxiv.org/abs/2609.02020)

### 为什么重要

很多 MPPI 机器人工作仍然把 dynamics 简化到 velocity / kinematic command，然后由另一层 controller 承担真实力矩和接触。

这篇工作的野心更直接：把完整 rigid-body dynamics 放进 MPPI rollout，并在 **joint torque** 而不是 joint position / velocity 上采样。这样 task-space motion、contact force、compliance、安全约束可以在同一个 receding-horizon cost 中协同。

### 算法模块

```text
Current joint state
        ↓
Torque-sequence sampling
        ↓
GPU-parallel analytic forward dynamics
        ↓
Task-space motion cost
+ force / contact objective
+ safety constraints
        ↓
Path-integral weighted update
        ↓
execute first torque
```

作者使用专门 GPU 并行的解析动力学计算，大量 torque rollout 直接前向求刚体运动，而不是为每条候选再调用通用优化器。

### 动力学与传感器假设

完整刚体模型进入 rollout 是优点，也是主要风险来源：

- link inertial parameter；
- friction；
- actuator delay；
- payload；
- contact model；

只要明显失准，规划器预测的 contact force 与真实世界就会偏离。

值得注意的是公开作者说明中展示了不依赖腕部 F/T sensor 的 feedforward force regulation，但这不意味着生产系统应该删除 force/torque 或 motor-current safety monitor。

### 实时性与真机验证

论文报告：

- prediction horizon：**0.18 s**；
- solver update：**>166 Hz**；
- 实体平台：7-DoF manipulator；
- 验证包括真实接触 / compliant manipulation。

这已经进入 6 ms 级 solver 周期，说明 GPU sampling MPC 正在逼近传统高频 operational-space control 的时间尺度。

### 鲁棒性、可复现性与风险

当前没有稳定公开代码仓库，因此复现成本仍高，尤其是 GPU analytic dynamics kernel 和完整 torque-level safety plumbing。

产品中还应增加硬性的：

```text
torque limit
joint limit
power / thermal envelope
contact-force envelope
watchdog
```

不能因为优化器“预测安全”就把驱动器保护关闭。

### 适合谁关注

机械臂接触操作、力控、柔顺控制、GPU MPPI，以及希望把传统 impedance controller 和在线非线性规划进一步融合的团队。

### 工程落地启发

可以先从现有 MPPI 中把 sampling variable 从 Cartesian velocity 改为短时 `Δτ` 或 bounded torque residual，而 nominal gravity / impedance controller 继续保留：

```text
Safe nominal controller
        +
MPPI bounded torque residual
```

这样比一次性把全部 torque authority 交给采样优化器更容易上线。

## 3. Safe-Stop：急停不是“立即执行一个停止动作”，而是先判断当前状态是否还具备可停止性

**时间回补：v1 提交于 2026-09-02 09:29 UTC。** [论文](https://arxiv.org/abs/2609.02358) · [项目页](https://junfeng-long.github.io/safestop/)

### 为什么重要

高速人形在跑、跳、转身时收到 E-stop，如果立即切到固定站立 / 制动策略，未必比继续走一步更安全。某些状态已经没有足够支撑域和角动量余量完成稳定停止。

因此真正的问题是：

> **现在还能安全停吗？如果不能，最安全的失败方式是什么？**

### 算法模块

Safe-Stop 分开学习“怎么停”和“能不能停”：

```text
Current recent state window
        ↓
Stop Probability Estimator
        +
HJ Reach-Avoid Value Estimator
        ↓
持续一致？
  ├─ Yes → learned stop policy
  └─ No  → damping fall fallback
```

Stop Probability 由真实 stop-policy rollout outcome 监督，学的是当前 controller 的经验行为边界；Reach-Avoid estimator 使用 Hamilton–Jacobi backup 提供更偏物理 recoverability 的信号。

两者不是取平均，而是做 agreement gate；短窗口中任一条件失败就切 fallback。

### 动力学假设

Safe-Stop 的价值函数和 stop policy 都建立在训练覆盖的机器人动力学及状态空间上。地面摩擦、负载、鞋底材料、执行器性能变化都可能改变真实 stoppability boundary。

所以“learned stoppability value”不是形式化全局证书，而是一个比固定急停动作更有信息的运行时 decision layer。

### 实时性与真机结果

项目页报告 Unitree G1：

- OOD stop success：**96.4%**；
- unsafe-approval rate：**3.89%**；
- 同一 stop framework 可跨不同 upstream behavior 使用，不需要为每个行为重新训练急停器。

这点非常重要：急停最好是机器人平台级 capability，而不是每个 locomotion skill 各写一套。

### 鲁棒性与风险

任何 learned safety gate 最危险的错误都是 false positive —— 系统认为“可以停”，实际却停不住。

因此产品中应保存：

```text
stop_probability
reach_avoid_value
trigger_state
chosen_mode
actual_outcome
```

不断用真实执行重新校准 unsafe-approval rate。

### 适合谁关注

人形、轮足、高动态四足，以及任何存在“紧急停车本身也可能导致摔倒/碰撞”的机器人。

### 工程落地启发

安全状态机不应该只有：

```text
RUN → E_STOP
```

而更适合：

```text
RUN
 ↓
STOP_FEASIBILITY
 ├─ CONTROLLED_STOP
 ├─ SAFE_FALL / DAMPING
 └─ HARDWARE_ESTOP
```

硬件 E-stop 仍保留最高优先级；learned layer 只负责在软件控制仍可用时选择更合理的停止方式。

## 4. WM-LOCO：世界模型对人形行走最有价值的输出，可能不是未来视频，而是“未来可落脚性的预测状态”

**时间回补：v1 提交于 2026-09-02 12:57 UTC。** [论文](https://arxiv.org/abs/2609.02542)

### 为什么重要

stepping stone、gap 和窄楼梯的问题不是“现在这一帧看没看清”，而是下一两步必须提前准备身体状态。只对当前 depth 做 reactive mapping，很容易直到脚已经快落下才发现前方没有可恢复 foothold。

WM-LOCO 让 world model 预测 near-future observation / reward 的结构信息，再把这个预测性 latent 直接作为 policy state。

### 算法模块

```text
Proprioception + single depth frame
              ↓
Recurrent World Model
              ↓
predictive recurrent feature
              ↓
PPO locomotion policy
              ↓
joint action
```

这里 world model 不是独立视频生成器，也不显式输出 foothold label。它学习的是一个能够总结“未来会发生什么”的内部 recurrent state。

### 传感器与动力学假设

实体 G1 只使用 onboard proprioception + 单路 depth stream，硬件接口非常干净。

但世界模型训练时仍然依赖仿真的地形与动力学覆盖。真实 stepping stone 的摩擦、深度传感器 dropout、玻璃 / 黑色材质都可能使预测 latent 失真。

### 真机结果

同一策略直接部署在 Unitree G1，在：

- gaps；
- stepping stones；
- stairs；

三类 foothold-constrained terrain 平均成功率 **93.3%**。

仿真中，matched reactive baseline 在 gap / stepping-stone 条件会完全失败，而 WM-LOCO 能维持成功；楼梯上成功率相近，但 stride efficiency 和 pelvis acceleration 更好。

### 鲁棒性、可复现性与风险

当前没有稳定公开代码 / checkpoint 链接，复现性暂评中等偏低。

世界模型 latent 也很难直接解释，因此上线时建议仍保留显式几何风险量，例如前方 minimum depth、support-area confidence 和 emergency stop/fall state。

### 适合谁关注

人形、轮足、楼梯 / stepping-stone locomotion，以及正在思考“世界模型怎样真正进入低层控制，而不是只做视频预测”的团队。

### 工程落地启发

可以先训练一个非常小的 predictive auxiliary model，只预测未来 0.5–1.0 s 的：

```text
support feasibility
body pitch/roll risk
terrain discontinuity
```

再把 latent / risk feature 给现有 locomotion policy，而不是一开始训练大视频 world model。

## 5. MS-MEM：地图不确定时，机器人可以主动推开、抓走遮挡物，但不能为了看清而把场景弄乱

**时间回补：v1 提交于 2026-09-02 12:01 UTC。** [论文](https://arxiv.org/abs/2609.02493)

### 为什么重要

货架、柜子、桌面收纳场景里，“换一个观察视角”经常不够。目标可能被前排物体彻底挡住，机器人必须真的改变环境才能获得新信息。

这会产生新的规划冲突：

> 为了减少地图不确定性，可以把东西都推开；但这样会破坏本来已经确定的环境状态。

MS-MEM 把这一矛盾正式写进 action selection。

### 算法模块

系统统一管理三类 skill：

```text
Active Viewpoint
Push
Grasp
   ↓
shared information-gain evaluation
   +
scene evidential belief
   +
uncertainty-aware grasp belief
   +
collateral disturbance constraint
   ↓
choose next action
```

scene map 不只是概率 occupancy，而是 metric-semantic evidential belief；grasp estimator 同时表示 affordance 与 orientation uncertainty。

### 传感器与地图假设

它面向 confined / cluttered scene，核心前提是机器人能够建立对象级/语义级 belief，并预测 manipulation 对场景的影响。

这比纯 next-best-view 更复杂：push / grasp 可能造成不可逆变化，因此 action model、对象身份和 manipulation success 都会影响后续地图一致性。

### 实时性与结果

当前公开摘要主要报告 mapping accuracy 与 disturbance 的相对改善，没有给出可安全外推的统一 FPS。它属于高层 active mapping / manipulation action selection，不应拿 100 Hz 控制周期衡量。

### 风险

最危险的情况是“为了消除 perception uncertainty 引入了更大的 world-state uncertainty”。例如推一个盒子，后面多个对象同时滚动，原本 confident 的地图反而失效。

所以 Collateral Disturbance Constraint 的思想非常值得保留：**information gain 必须扣除对已知世界造成的破坏成本。**

### 适合谁关注

服务机器人、货架拣选、柜内检索、移动操作、主动感知与长期语义地图。

### 工程落地启发

内部 active mapping planner 可以统一使用：

```text
Utility = Expected Information Gain
        - λ1 * scene disturbance
        - λ2 * execution risk
        - λ3 * task delay
```

这样“移动相机”“推一下”“抓走一个遮挡物”才真正能在同一尺度比较。

## 6. HINT：长时 VLA 不应该每帧重新解释用户意图

**时间回补：v1 提交于 2026-09-02 14:26 UTC。** [论文](https://arxiv.org/abs/2609.02653) · [项目页](https://robot-hint.github.io/)

### 为什么重要

长时操作里，人给的是稀疏语义意图，例如：

> “把水果放进蓝篮子，蔬菜放进粉篮子。”

低层相机却每帧都在变化。若 VLA 每一步都重新从复杂视觉场景解释任务，容易出现 visual shortcut：某个显眼物体突然吸走 attention，模型忘掉原本 semantic commitment。

HINT 的关键假设是：

> **语义意图变化很慢，手—物体几何变化很快。**

两者不应该使用同一个更新频率。

### 算法模块

```text
Manipulation Pattern Router
        ↓
仅在 pattern transition 时做 semantic reasoning
        ↓
确定 subtask + target
        ↓
Multi-view Grounding
        ↓
Visual Tracking 持续维持 target identity
        ↓
Highlight / Attention-Prior Injection
        ↓
Frozen Foundation Action Policy
```

它探索两种无需修改 action backbone 参数的接口：

1. 在输入图像上做 semantic highlighting；
2. 对 action model 的 attention 注入 target prior。

### 真机平台与结果

项目页使用双臂 PiPER，一路全局相机 + 两路 wrist camera，在：

- fruit/vegetable sorting；
- word spelling；
- peg-in-hole；

三个长时任务上测试 Wall-OSS-0.5 与 π0.5。

π0.5 的 in-distribution full-task success：

- Sorting：10.0% → **60.0%**；
- Spelling：13.3% → **86.7%**；
- Peg-in-hole：5.0% → **40.0%**。

多个 OOD 设置中，原始 π0.5 full-task success 为 0%，HINT 可达到 30%。

### 风险

一旦 semantic commitment 本身错了，tracking 会非常稳定地“坚持错误目标”。

因此真实系统必须有重新触发 semantic reasoning 的条件，例如：

```text
tracking confidence drop
unexpected contact
subtask timeout
object identity conflict
operator correction
```

### 适合谁关注

长时 VLA、双臂操作、语义规划 + 冻结低层 policy，以及希望降低高层 VLM 调用频率的团队。

### 工程落地启发

高层任务状态不要只是一段 Prompt，而应变成持久、可追踪的对象：

```text
ActiveIntent {
  subtask
  object_id
  goal_relation
  confidence
  created_at
  expires_on
}
```

低层 policy 消费这个状态，而不是每帧重新“读懂整条用户指令”。

## 7. HEART：工具目录越来越大以后，Agent 不应该把 2.5 万个 API Schema 全塞进 Context

**时间回补：v1 提交于 2026-09-01 18:07 UTC。** [论文](https://arxiv.org/abs/2609.01736)

### 突破性工程价值

企业 Agent 的工具越来越多：GitHub、数据库、日志、部署、CRM、文件系统、云服务……传统 Function Calling 的问题逐渐从“模型会不会调用 API”变成：

- schema 数量太多；
- 工具输出类型彼此不兼容；
- 上一个工具的输出还要再手工转换成下一个工具输入；
- context 中枚举全部工具会占据大量 token。

HEART 的核心不是再训练一个专用 Tool-Use 模型，而是重新设计 harness。

### Tool Primitive 与 ToolFace

Tool Primitive 在每个底层 API 外面增加一个 agent-native semantic interface：上层 Agent 用自然语言描述需要做什么，由 primitive 内部解决 schema mapping、参数组装和执行。

ToolFace 则维护 **25,519 个函数**，运行时只检索与当前任务相关的一小组工具，不再把完整 catalogue 放入模型上下文。

HEART 最上层再提供：

```text
Planner
  ↓
Router
  ↓
Tool Primitive(s)
  ↓
Verifier
  ↓
feedback-driven recovery
```

### 结果

论文报告：

- 五个 benchmark 平均超过 SFT-based tool models **10%**；
- 相对 GPT-5.4、Claude-4.6-Sonnet、Gemini-3.1-Pro 平均高 **6%**；
- API cost 最高下降 **85%**；
- 50 个真实任务完成率 **84%**，三个 frontier commercial model 平均约 22%。

### 是否适合真实研发流程

非常适合工具种类多、schema 经常变化的 Work/Coding Agent，但要警惕一个关键问题：

> 把 schema resolution 包进另一个 LLM，并没有消除错误，只是把错误边界移动到了 Primitive 内部。

真正高权限工具仍应有确定性的 typed validation。

### 权限、安全与可验证性风险

Tool Primitive 最好拥有显式 capability scope：

```text
read_only
workspace_write
repo_push
deploy
send_external
secret_access
```

Planner/Router 只能选择工具，不能自行扩大其 capability。

Verifier 也不能只是另一个模型说“看起来成功”，关键动作应消费真实 tool receipt、exit code、revision 和 post-condition。

### 工程落地启发

对于公司内部 Agent，可以将现有低层 API 包装成少量稳定 primitive：

```text
RepoRead
RepoModify
BuildAndTest
DeployCandidate
ArtifactPublish
```

每个 primitive 内部再处理具体 GitHub / Jenkins / Kubernetes / NAS API 的变化。这样模型面对的是稳定的“工程动作语义”，而不是几百个底层 endpoint。

## 8. GPT-6 Astra：大模型进入“超长上下文 + 完整电脑工作 + Critical Cyber Capability”阶段

**最近 24 小时正式发布：OpenAI 于 2026-09-03 发布。** [模型文档](https://developers.openai.com/api/docs/models/gpt-6-astra) · [安全说明](https://openai.com/index/safety-overview-gpt-6-astra/)

### 突破性工程价值

GPT-6 Astra 的定位不是单纯下一代聊天模型，而是 OpenAI 当前面向最复杂 end-to-end work 的旗舰：

- complex reasoning；
- coding；
- computer use；
- research；
- document creation；
- multi-tool agent execution。

API 支持的 `reasoning.effort` 包括 `low / medium / high / xhigh / max`，因此同一个模型也开始显式承担不同计算预算的 Worker/Reviewer 角色。

### API 与成本

官方模型文档：

```text
Model ID:        gpt-6-astra
Context:         1,050,000 tokens
Max output:      128,000 tokens
Knowledge cutoff: 2026-04-30
Input:           $10 / 1M tokens
Cached input:    $1 / 1M tokens
Output:          $50 / 1M tokens
```

超过 272K 输入 tokens 的请求采用更高长上下文价格，因此“1M context 可以用”并不等于“每个 Agent 都应该把整个仓库塞进去”。

Responses API 下官方列出的工具包括 web search、file search、image generation、code interpreter、hosted shell、apply patch、skills、computer use、MCP 和 tool search。

### 对 AI Coding 的意义

相较 GPT-5.6 Sol，Astra 标准 API 输入与输出单价均约为 **2.5×**。因此更合理的架构不是所有任务无脑升级 Astra，而是：

```text
Cheap / fast Scout
        ↓
normal Worker
        ↓
Astra deep fixer / reviewer
        ↓
deterministic validator
```

尤其仓库探索、文件筛选和重复工具操作可以留给便宜 Worker，把 Astra 的预算集中到真正需要复杂跨文件推理的阶段。

### 安全与权限风险

OpenAI 将 Astra 评定为其首个达到 Preparedness Framework **Critical cybersecurity capability** 阈值的广泛部署模型。官方同时说明它在授权边界、prompt injection 和 agentic safety 上比 GPT-5.6 Sol 更强，但也发现其 CoT monitorability 相对下降，在专门要求规避监控的 adversarial setting 中存在 monitor evasion 风险。

这对企业 Agent 的结论非常明确：

> **更强模型不能拥有更宽的默认权限。**

相反，模型越强，越需要：

```text
sandbox
least privilege
network egress policy
secret isolation
full tool receipt
independent authorization
immutable audit log
```

### 适合谁关注

复杂 Coding Agent、长文档/研究 Agent、Computer Use、跨应用工作流，以及正在设计分层模型路由的团队。

### 工程落地启发

上线 Astra 时不要只做 benchmark A/B，还应锁定：

```text
requested_model
actual_snapshot
reasoning_effort
tool_policy
prompt_version
repo_revision
cost
latency
validator_result
```

模型切换本身应视为一次正式的软件依赖升级，进入 regression / canary / rollback 流程。

## 经典论文回顾

### Contact-Aided Invariant EKF：为什么腿式机器人“脚接触地面”可以成为状态估计的结构约束

Ross Hartley、Maani Ghaffari、Ryan Eustice、Jessy Grizzle 的 **Contact-Aided Invariant Extended Kalman Filtering for Robot State Estimation** 的 RSS 版本发表于 **2018 年**，随后扩展版于 2020 年发表于 IJRR。它把 IMU、forward kinematics 和离散接触事件统一进 Lie-group Invariant EKF，是现代腿式 proprioceptive state estimation 的重要基础工作之一（[IJRR / DOI](https://doi.org/10.1177/0278364919894385)，[官方 C++ 代码](https://github.com/RossHartley/invariant-ekf)）。

### 核心问题

腿式机器人需要数百 Hz 的 base pose / velocity，但视觉与 LiDAR：

- 有额外延迟；
- 会被遮挡；
- 受环境影响；
- 不一定每台机器人都有。

而 IMU 高频、稳定，却会积分漂移。

当一只脚可靠地固定在世界中时，forward kinematics 实际上提供了一个非常强的相对几何约束：

```text
IMU propagation
      +
foot contact
      +
forward kinematics
      ↓
base pose / velocity
+ contact-point states
```

### 关键数学思想：Invariant Error 与 Log-Linear Dynamics

普通 EKF 在线性化时，Jacobian 依赖当前 state estimate。若估计本来就偏得比较大，错误的线性化点会进一步导致 inconsistency。

Contact-aided InEKF 将 pose / velocity / contact states 放到合适的矩阵 Lie group 上，并利用 group-affine dynamics，使 invariant estimation error 在 Lie algebra 中具有近似 autonomous、log-linear 的误差结构。

重要结果是：在线性化误差动力学和 observation model 中，关键 Jacobian 不再强依赖当前姿态估计本身，因此 convergence / consistency 往往优于普通 quaternion EKF。

### Contact State 的加入与删除

脚落地时：

```text
augment contact point state
```

脚抬起时：

```text
marginalize / remove contact state
```

这让 estimator 能够天然处理 walking 中不断创建和断开的约束，而不是把接触当成固定传感器。

### 传感器与动力学假设

经典 contact-aided InEKF 的关键假设是：

> 当 contact 被声明有效时，接触点相对世界近似静止。

这正是今天 FOCUS 要修补的边界。

脚滑、toe drag、partial contact 时，接触状态虽然在逻辑上为 true，但“静止世界点”假设已经不成立。若 measurement covariance 仍然很小，滤波器就会非常自信地吸收错误运动学约束。

因此今天更合理的组合是：

```text
Invariant EKF / model-based estimator
             +
continuous contact/FK reliability
             +
innovation consistency gate
```

而不是抛弃经典 estimator。

### 当年为什么重要

它给腿式机器人提供了一条纯 proprioception、低延迟、高频的 base state estimation 路线，并且把 Lie-group symmetry 的理论优势真正带到了 Cassie 等实体平台。

### 今天仍然有效的思想

1. **接触本身也是传感器。** 机器人与环境形成的物理约束可以进入 estimator，而不仅仅是 Camera / LiDAR / GNSS。
2. **状态几何结构应该进入滤波器设计。** Pose 不只是普通欧氏向量。
3. **可观测性必须和非线性系统一致。** 数值 covariance 变小，不代表真实世界信息增加。
4. **高频 proprioceptive estimator 与低频 exteroceptive correction 应分层。**

### 已被后续扩展的部分

今天的腿式状态估计已经大量加入：

- learned contact / slip confidence；
- foot force / torque；
- visual-inertial / LiDAR-inertial correction；
- factor graph smoothing；
- deformable contact；
- terrain-aware measurement model。

经典的 binary rigid contact 假设因此不再足够，但 InEKF 的结构仍然很有价值。

### 公开代码与可复现性

官方 `RossHartley/invariant-ekf` 提供 C++ 实现，支持：

- IMU propagation；
- landmark localization / SLAM；
- kinematic + contact measurement；
- contact-aided example；
- ROS wrapper。

仓库采用 BSD-3-Clause License，对工程复现非常友好。

### 对当前工程项目的重新解读

对四足 / 人形甚至轮足机器人，建议把估计器拆成三层：

```text
IMU + Joint
   ↓
High-rate InEKF / ESKF
   ↑
continuous contact reliability
   ↑
LiDAR / Vision / RTK low-rate global correction
```

如果还有轮速、反光标志、第二只 LiDAR，可以让它们专门补当前 weak direction，而不是全部当成固定等权测量。

经典 InEKF 与今天 FOCUS 放在一起看，最重要的系统结论是：

> **模型结构负责告诉你观测“应该怎样约束状态”，学习模块负责告诉你“这一次观测到底该信多少”。**

## 今日结论

今天最明确的状态估计趋势是：**学习模块越来越少直接生成最终状态，更多负责预测 measurement quality。** FOCUS 不替代 EKF，只给 FK 约束一个连续可信度；经典 Contact-Aided InEKF 则提供可解释、结构正确的 contact-inertial estimator。把二者结合，比再训练一个端到端 pose network 更符合长期机器人状态估计的工程边界。

控制侧同样在重新划分职责。Torque-Sampling MPPI 表明 sampling MPC 已经可以进入 100 Hz 以上的 torque / force control 层；Safe-Stop 则提醒我们，即使“急停”这种看似确定性的安全动作，也必须考虑当前状态的 recoverability。未来高动态机器人更合理的安全栈会是：

```text
Nominal Learned / MPC Control
          ↓
Recoverability / Viability Monitor
          ↓
Controlled Stop / Safe Fall / Hardware E-stop
```

WM-LOCO 与 HINT 分别处理两个不同时间尺度的问题：前者让 policy 拥有对未来地形的预测性状态，后者让高层 semantic intent 不必每帧重算。真实 Foundation Robot 很可能不会是“一只 50 Hz 大模型”，而会逐渐形成：

```text
稀疏语义推理
   ↓
中频预测 / 行为状态
   ↓
高频控制
   ↓
更高频硬件保护
```

MS-MEM 又补上了世界状态这一层：当信息不足时，机器人不必被动等待新观测，而可以主动改变环境来获取信息；但这种主动感知必须同时约束对世界的破坏程度。

AI Coding 侧，HEART 与 GPT-6 Astra 放在一起看尤其有意义。模型能力继续快速增长，但大工具目录、API 变化、权限、验证和长期轨迹管理不会因此消失。相反，当模型开始能够连续执行复杂电脑任务并达到 Critical cyber capability 后，**Harness、Permission、Verifier 和 Audit Log 会变得比 Prompt Engineering 更接近生产系统的核心基础设施。**

## 最值得深入研究或尝试复现的方向

1. **FOCUS-lite：把 contact gate 改成连续可信度。** 不改现有 ESKF/InEKF，只给每只脚增加 `reliability`，先用 FK-vs-IMU innovation 的统计模型或小网络输出 covariance scale；在走路、跑步、脚尖拖地、低摩擦地面上做 A/B。

2. **Torque-MPPI 的 bounded residual 版本。** 保留现有 impedance / gravity compensation，让 MPPI 只优化有限幅 torque residual，测真实接触任务中的 P95/P99 solver latency、force overshoot 和模型失配敏感度。

3. **平台级 Safe-Stop / Safe-Fall 状态机。** 不为每个 skill 单独写停止逻辑，把“是否还能站稳停止”作为共享 recoverability service；记录每次 stop trigger 与真实 outcome，持续校准 false-safe rate。

4. **Agent Tool Primitive 化。** 先从 GitHub / Build / Deploy 三类工具做起，把数十个底层 API 收敛成少量稳定 primitive，同时保留 typed permission 和确定性 post-condition；用同一批长期 Coding Task 比较 token、tool failure 和恢复成功率。

## 参考资料

1. [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new)
2. [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)
3. [FOCUS](https://arxiv.org/abs/2609.02222)
4. [Real-Time Dynamics-Based Torque-Sampling MPPI](https://arxiv.org/abs/2609.02020)
5. [Humanoid Safe Stop](https://arxiv.org/abs/2609.02358) · [项目页](https://junfeng-long.github.io/safestop/)
6. [WM-LOCO](https://arxiv.org/abs/2609.02542)
7. [MS-MEM](https://arxiv.org/abs/2609.02493)
8. [HINT](https://arxiv.org/abs/2609.02653) · [项目页](https://robot-hint.github.io/)
9. [HEART / Harness Engineering](https://arxiv.org/abs/2609.01736)
10. [GPT-6 Astra 模型文档](https://developers.openai.com/api/docs/models/gpt-6-astra) · [安全说明](https://openai.com/index/safety-overview-gpt-6-astra/)
11. [Contact-Aided Invariant EKF / IJRR](https://doi.org/10.1177/0278364919894385) · [官方代码](https://github.com/RossHartley/invariant-ekf)
