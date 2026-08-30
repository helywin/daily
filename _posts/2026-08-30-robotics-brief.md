---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-30"
date: 2026-08-30 09:00:00 +0800
description: "周末无新 arXiv 常规批次，本期回补 8 月 27 日高价值工作：多智能体 3DGS SLAM、30Hz+ 流式 VLA、安全对比强化学习、在线 VLA 适配、世界动作模型、失败恢复，以及 Coding Agent 训练数据筛选与工具授权治理。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-30

## 摘要

今天是周日。公开检索确认 arXiv Robotics 与 Software Engineering 的最新常规公开批次仍停留在 2026-08-28；严格最近 24 小时内没有足够 5 条高质量、未重复且可完整核验的新主动态，因此本期按任务规范扩大到最近 7 天。最终 8 条主动态的 v1 均提交于 2026-08-27 UTC，全部明确按“时间回补”处理，不把日报日期包装成论文首次发布日期。（[arXiv Robotics recent](https://arxiv.org/list/cs.RO/recent?show=2000)，[arXiv Software Engineering recent](https://arxiv.org/list/cs.SE/recent?show=2000)）

今天最值得看的 SLAM 工作是 **CGS-SLAM**。它面向多智能体协同 3D Gaussian Splatting SLAM，但没有要求每台设备都拥有 RGB-D，而是只使用 RGB 与惯性数据：各 Agent 本地以 IMU 预积分作为运动先验，利用 metric monocular depth 建立有尺度的本地 3DGS 地图，只交换关键帧编码；服务器再使用跨视图模型对齐子图。这个设计真正值得关注的不是 3DGS 渲染，而是“本地连续跟踪 + 低带宽表征交换 + 中心全局对齐”的协同 SLAM 分工。（[论文](https://arxiv.org/abs/2608.26868)）

控制侧，**Arrive and Survive / Safe-CRL** 针对 goal-conditioned contrastive RL 中一个很隐蔽的安全偏差：发生失败终止后，传统正样本构造会忽略“已经因为失败而消失的未来占用概率质量”，从而让接近灾难的短轨迹被错误强化。作者只增加 survival-mass weighting 与一个 goal-independent survival score，就能只凭一位 failure termination 信号进行安全目标学习，覆盖 12 个机器人导航与 locomotion 任务。（[论文](https://arxiv.org/abs/2608.26571)，[代码](https://github.com/RomainLITUD/safe-crl)）

VLA 侧今天有四条互补路线。**FlashVLA** 不是简单减少 denoising step，而是维护处于不同噪声阶段的 action-chunk streaming buffer，每次 forward 同时推进所有 chunk 一步，并通过 chunk-wise causal attention 保持跨块连续性；官方摘要报告单 GPU 可达到至少 30 Hz，并在真实机器人上异步执行。（[论文](https://arxiv.org/abs/2608.27384)）**GRAFT** 关注少量真机交互下的在线适配，用 region-level supervision 学习 view-specific visual anchors，同时用单步动作生成与视觉语言前缀缓存降低在线更新成本；四项生物医学精细操作任务中，在相同适配预算下成功率提高 25 个百分点。（[论文](https://arxiv.org/abs/2608.27079)）

**Riemann-1.0** 则把 policy 与 world model 合成一个 fully causal autoregressive World Action Model：同一套权重既根据真实观察输出机器人动作，也可以在给定动作后继续生成视觉未来。它基于 20 万小时以上 embodied interaction data 做分阶段预训练，RoboTwin2.0 / LIBERO / RoboCasa-365 分别报告 94.3% / 99.0% / 62.6% 成功率，真实长时任务平均 SR 为 85.0%。但当前世界模拟器部分主要是定性展示，还不能把“能生成未来视频”直接等价为可用于安全规划的精确动力学模型。（[论文](https://arxiv.org/abs/2608.27033)）

**FLARE** 的价值则在失败恢复。它把恢复拆成两层：轻微执行偏差通过 Retry 处理；对象掉落、环境状态被破坏等 OOD failure 则由离线 MLLM 分析执行视频，建立少量 object-centric Reset skill，线上 monitor 决定何时暂停主任务并调用恢复技能。它更像在 VLA 外增加一个故障恢复状态机，而不是期待同一策略在所有坏状态下“自己想办法”。（[论文](https://arxiv.org/abs/2608.26645)）

AI Coding 侧，两项工作都很适合生产 Agent。**SWE-Prime** 发现“成功轨迹”仍包含大量冗余、无效甚至危险步骤，因此先在 trajectory level 按过程质量、结果质量与代表性筛选，再在 segment level 按贡献、可学习性和风险选择真正参与 loss 的片段；只使用选出的 10% 轨迹，仍能在 SWE-Bench Pro / Verified 上超过使用全部 resolved trajectories 的训练，最高相对提升 12.2% / 24.2%。（[论文](https://arxiv.org/abs/2608.27449)）

**SARA** 则从权限边界解决 tool-output prompt injection：工具返回值可以诱导模型提出某个动作，但“诱导出动作”不应该自动获得执行授权。系统将 Action Probe 与 Runtime Authorization 分开，并持续记录 action provenance；真正 tool call 必须能被用户目标和已经审计通过的执行证据支撑，同时通过 No-History-Promotion 防止恶意文本因为多次出现就被洗成可信指令。AgentDojo 与 AgentDyn 的四个主要设置中，攻击成功率被压到不高于 0.63%。（[论文](https://arxiv.org/abs/2608.27146)）

本轮也检查了近期主流模型厂商官方入口。8 月 28 日 OpenAI 的公开更新是 Cursor 合同与模型供应相关声明，并非新的基础模型发布；Google 近期机器人主模型仍是 7 月 30 日的 Gemini Robotics ER 2，因此本期没有用旧模型新闻挤占更有工程价值的机器人、SLAM 与控制工作。（[OpenAI 8 月 28 日更新](https://openai.com/index/our-decision-on-cursor-following-its-acquisition-by-spacex/)，[Gemini Robotics ER 2](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/gemini-robotics-er-2/)）

## 1. CGS-SLAM：多手机协同 3DGS SLAM，不把所有原始数据都上传服务器

**时间回补：arXiv v1 提交于 2026-08-27 09:31 UTC；此前未进入去重索引。** [论文](https://arxiv.org/abs/2608.26868)

### 为什么重要

多机器人 / 多手机协同建图通常有两个极端：要么每台设备独立建图，最后很难稳定合并；要么把原始图像和点云持续上传服务器，通信量、隐私和在线鲁棒性都很差。

CGS-SLAM 采用混合去中心化 / 中心化架构。每个 Agent 自己完成连续 tracking 和 local 3DGS reconstruction，只在关键位置交换紧凑的 keyframe encoding；服务器利用多 Agent 的重叠区域做 submap alignment 与全局融合。对于 GNSS-denied 室内扫描，这种结构比“服务器实时控制所有客户端”更符合真实部署。

### 算法模块

系统大致分为：

```text
RGB + IMU
   ↓
Local inertial motion prior
   ↓
Metric monocular depth
   ↓
Local 3D Gaussian map
   ↓
Keyframe encoding exchange
   ↓
Overlap-aware dynamic keyframing
   ↓
Server-side cross-view submap alignment
   ↓
Global collaborative reconstruction
```

其中 metric depth 用于让单目 3DGS 获得尺度；服务器使用跨视图基础模型进行不同 Agent 子图对齐。

### 传感器与系统假设

它只要求 RGB + IMU，适合普通手机或低成本终端，但“metric monocular depth”本质仍是学习先验，不是物理深度传感器。玻璃、强反射、极端尺度和训练分布外环境都可能出现系统性尺度偏差。

服务器跨视图对齐也依赖不同 Agent 之间存在足够可辨识重叠。如果多个楼层或长走廊外观高度重复，foundation feature 并不会自动提供形式化正确的回环约束。

### 实时性与通信

论文强调通过 keyframe encoding 而非持续交换原始高带宽观测降低通信成本，但当前公开摘要没有给出一个可跨平台直接搬用的统一端侧 FPS / Mbps 数字。因此工程复现应重点测：客户端 tracking P95、3DGS update P95、每分钟上传字节数以及服务器合并延迟。

### 鲁棒性、可复现性与风险

目前公开证据主要来自多数据集实验，尚不能视为已经验证的大规模真实多机器人长期系统。最大风险有三个：learned metric depth 的尺度偏置、子图对齐误闭环、以及中心融合结果与本地实时轨迹之间的版本一致性。

### 适合谁关注

适合多机器人协同扫描、手机 3D 重建、GNSS-denied 数字孪生、多人协作现场采集，以及希望降低中心服务器带宽压力的团队。

### 工程落地启发

最值得先复制的是**分层通信接口**，而不是 3DGS 本身：

```text
本地高频：Pose / Tracking / Safety
中频共享：Keyframe + Compact Descriptor
低频中心：Submap Alignment / Loop / Global Map
```

这样即使网络中断，机器人本地状态估计仍然继续运行；服务器只负责最终一致性，不成为实时控制单点故障。

## 2. FlashVLA：把多步动作去噪改成持续流，而不是每帧重新从噪声开始

**时间回补：arXiv v1 提交于 2026-08-27 17:19 UTC。** [论文](https://arxiv.org/abs/2608.27384)

### 为什么重要

Flow-matching VLA 常见问题不是模型“不会做”，而是每次 observation 到来后都要重新执行多轮 action denoising。同步执行会让机器人停顿，异步执行又会产生 observation-action age：动作算完时，机器人已经离开了生成动作时的状态。

FlashVLA 将多轮去噪摊到时间轴上：同时维护多个处于不同噪声阶段的 action chunk，每一次 forward 只推进它们一步，同时弹出最成熟的一块去执行。这样每一块最终仍经过多步 refinement，但每个控制周期不再承担完整多步 decoding 成本。

### 算法模块

核心是 streaming action buffer 与 chunk-wise causal attention：较晚、噪声更高的 chunk 可以看到前面更成熟的动作意图，从而维持跨 action chunk 的连续性；新 chunk 在队尾初始化，成熟 chunk 在队首执行。

这一结构等于把 action decoder 从“一个 observation → 完整求解一次”改成持续运行的 pipeline。

### 控制频率与实时性

官方摘要给出的关键数字是：单 GPU 可达到 **至少 30 Hz** 控制频率，并完成真实机器人异步执行。论文同时在 LIBERO、RoboTwin 2.0 与真实任务中评估。

真正应该关注的指标不只有平均 Hz，还包括：Time-to-First-Action、Time-to-React、动作从 observation 生成到真正执行时的 age，以及 action chunk 被新观察打断或重规划的能力。

### 动力学与控制假设

Streaming buffer 隐式保留短期动作历史，但它不是机器人动力学模型。遇到突然碰撞、物体滑落或人进入工作区时，缓冲区里尚未执行的动作可能立刻过期。

因此高优先级接触 / 碰撞 / 急停通道必须能够抢占 action buffer，不能因为“流式连续性”而让旧动作继续不可中断地执行。

### 可复现性与风险

论文展示的是对 flow-matching VLA 的结构化改造，工程价值高，但实际收益取决于 backbone、action chunk 长度、buffer 深度和 GPU。不能把单卡 30 Hz 直接外推到 Jetson 或同时运行 detector / depth / SLAM 的共享 GPU 环境。

### 适合谁关注

适合 π0.5 类 flow-matching VLA、动态抓取、长时序操作，以及真机已经出现“模型离线成功但实时动作断断续续”的团队。

### 工程落地启发

VLA runtime 最好显式维护：

```text
observation_timestamp
action_generated_at
action_start_at
action_age
buffer_slot
valid_until
preemptible
```

以后优化 VLA 不能只比较 token/s，应直接比较 P95/P99 action age 与任务成功率。

## 3. Arrive and Survive：失败终止会让对比强化学习错误高估“快要撞死”的轨迹

**时间回补：arXiv v1 提交于 2026-08-27 03:24 UTC。** [论文](https://arxiv.org/abs/2608.26571) · [代码](https://github.com/RomainLITUD/safe-crl)

### 为什么重要

Goal-conditioned contrastive RL 会把轨迹中未来真正访问到的状态作为正样本，学习“当前状态 / 动作到某个目标的可达性”。但在 failure-terminated MDP 中，轨迹一旦碰撞或失败，后面的未来直接消失。

如果训练仍把失败前剩下的几个 future state 当作正常正样本，却不考虑“本来应该存在但被失败终止切掉的概率质量”，就会产生系统性高估：越靠近灾难，存活的短未来反而可能获得过强监督，形成 catastrophic failure bootstrapping。

### 算法模块

Safe-CRL 做了两个相对克制的修正：

- **mass-weighted InfoNCE**：critic 学习时按剩余 survival mass 修正正样本权重；
- **log-survival-mass score**：policy optimization 显式补回目标无关的生存概率质量。

系统只需要环境已经提供的“一位 failure termination”信号，不要求每种危险都有精细 reward shaping。

### 传感器与动力学假设

这是一种目标条件 RL 理论修正，并不依赖特定 LiDAR / Camera。真正的前提是 failure termination 本身可靠：如果碰撞检测漏掉危险，或把普通 episode timeout 误当安全失败，survival signal 会被污染。

### 结果、鲁棒性与可复现性

论文在 12 个 failure-prone robot navigation / locomotion 任务中报告一致的生存性和目标到达提升，并公开 JAX/Brax 实现。

需要注意，它仍然是**统计学习意义上的安全改善**，不是 CBF / reachability 那类可认证安全层；未见环境、sim-to-real 动力学误差和传感器漏检仍需独立处理。

### 适合谁关注

适合 goal-conditioned navigation、四足 locomotion、自动 curriculum / self-play，以及已经使用 contrastive RL、HER 类目标学习却发现策略会“为了够到目标反复撞”的团队。

### 工程落地启发

真实机器人安全学习可以明确分层：

```text
Hard safety termination
        ↓
Survival-aware learning objective
        ↓
Goal-reaching policy
        ↓
Runtime CBF / Collision / Limit Gate
```

不要让 reward 中一个巨大碰撞惩罚同时承担“学习信号”和“最后安全防线”两个职责。

## 4. GRAFT：少量真机在线适配时，先告诉 VLA“到底应该看哪里”

**时间回补：arXiv v1 提交于 2026-08-27 13:04 UTC。** [论文](https://arxiv.org/abs/2608.27079)

### 为什么重要

精密生物医学操作的成功与失败可能只差一个很小的视觉细节，例如针尖、组织边缘、容器开口或某个器械相对位姿。Task-level reward 只告诉策略最后成功没有，却几乎无法解释“当前画面里哪一块区域决定成败”。

如果直接用少量真机交互在线强化整个大 VLA，不仅 sample inefficient，反向更新与 replay 的计算成本也很高。

### 算法模块

GRAFT 使用 region-level supervision 学习 **view-specific visual anchors**，训练时告诉模型任务相关局部线索在哪里；部署阶段不再需要额外运行 region proposal pipeline。

计算侧采用单步 action generation 和 cached visual-language prefix reuse，尽量避免每次在线更新都重新计算大段不变的视觉语言上下文。

### 结果与实时性

论文覆盖 4 个 biomedical fine-grained manipulation task，在相同在线适配预算下，成功率相对基线提高 **25 个百分点**，同时降低在线 policy update 的计算负担。

公开摘要没有给出可安全外推的固定控制 Hz，因此不应仅凭“single-step”就宣称它已经是高频控制器。

### 传感器与任务假设

GRAFT 的优势依赖任务真正存在稳定的局部视觉 anchor。对于透明、强反光、组织形变或严重遮挡场景，区域监督本身可能变化；如果关键反馈主要来自力觉而不是视觉，纯 visual grounding 的上限也会很明显。

### 风险与可复现性

在线 RL 真机探索必须有动作限幅、碰撞监控和可恢复 workspace。区域级监督也会增加数据标注 / 生成成本，产品化需要比较“多标一点视觉区域”与“多采一些完整示范”哪个更划算。

### 适合谁关注

适合精密装配、医疗 / 生物实验自动化、插接、微小对象操作，以及希望对通用 VLA 做现场少量 adaptation 的团队。

### 工程落地启发

如果任务失败集中在某一局部视觉区域，不要第一反应就扩大 backbone。可以先给现有策略增加：

```text
task-relevant region
region confidence
region-specific feature cache
```

让在线学习只围绕真正决定任务结果的区域更新。

## 5. Riemann-1.0：一套因果序列同时做 Policy 和 Visual World Simulator

**时间回补：arXiv v1 提交于 2026-08-27 12:21 UTC。** [论文](https://arxiv.org/abs/2608.27033)

### 为什么重要

传统 VLA 与世界模型通常是两个系统：Policy 从 observation 输出 action；World Model 接收 action 预测未来。Riemann-1.0 试图用同一套 fully causal autoregressive sequence 统一二者，把多视角 observation、robot state 和 embodiment-specific action 按真实因果顺序串起来。

当下一帧 observation 来自真实相机时，它是在线 Policy；当下一帧由模型继续生成时，同一模型就成为 action-conditioned visual simulator。

### 数据与训练结构

作者采用 progressive embodied pretraining，把第一人称人类视频、handheld-gripper demonstration 和异构机器人轨迹统一进一个 World Action Modeling objective，总体建立在 20 万小时以上 embodied interaction data 上。

这里的关键不是强行把不同机器人压成同一种 action space，而是保留 embodiment-specific action，同时共享世界演化 backbone。

### 结果

论文报告：

- RoboTwin2.0：**94.3%**；
- LIBERO：**99.0%**；
- RoboCasa-365：**62.6%**；
- 真实长时操作平均 SR：**85.0%**；
- 真实长时任务 Progress Success Rate：**94.4%**。

长时真实任务 SR 相比论文中的最强开源基线高 15 个百分点。

### 传感器与控制假设

统一 world-action token sequence 很优雅，但它不自动解决 low-level contact safety。机器人 proprioception、夹爪状态、相机时延和执行器反馈仍必须准确进入模型。

更重要的是，论文对“world simulator”部分主要提供定性生成结果，目前没有足够证据把它当作可替代真实动力学模拟的 planning oracle。视频看起来合理，不等于接触力、摩擦、碰撞和动作后果数值正确。

### 实时性、可复现性与风险

公开摘要没有给出可以直接用于边缘部署预算的参数量、统一推理延迟或显存数字。20 万小时以上训练数据也意味着从零复现门槛极高。

因此中小团队更适合研究其**因果接口和数据组织方式**，而不是复制训练规模。

### 适合谁关注

适合通用 manipulation foundation model、世界模型、跨本体训练、长时任务和希望统一 policy / simulation 表征的团队。

### 工程落地启发

内部机器人数据可以按因果记录统一成：

```text
Observation_t
RobotState_t
Action_t
Observation_{t+1}
RobotState_{t+1}
Outcome / Contact
```

即使以后不训练 Riemann 类大模型，这种数据顺序也比散落的图像、joint log 和任务标签更容易支撑 world model、policy 和故障分析。

## 6. FLARE：不要要求主 VLA 在严重失败状态里继续硬撑，先把环境 Reset 回可执行域

**时间回补：arXiv v1 提交于 2026-08-27 05:58 UTC；CVPR 2026 接收。** [论文](https://arxiv.org/abs/2608.26645)

### 为什么重要

大多数 demonstration 都是单调成功轨迹：抓住、移动、放下。真实执行却会出现 missed grasp、掉落、意外碰撞。轻微偏差还可能通过闭环观察自己修正，但一旦对象掉到错误位置，当前环境已经离开训练分布，继续让原 task policy 输出动作通常只会越做越错。

FLARE 明确把“正常任务策略”和“环境恢复策略”拆开。

### 算法模块

**Retry**：在 demonstration 中注入扰动与 bridging segment，让策略学会从轻微 pose deviation 回到主轨迹。

**Reset**：对会破坏任务状态的严重 OOD failure，先由离线 MLLM 分析执行视频，识别典型失败状态；随后只针对这些状态采集小型 object-centric reset skill library。

线上再由一个 MLLM monitor 判断继续主任务还是调用 Reset。

### 传感器与策略假设

在线 monitor 本身也可能误判。特别是“看起来失败”与“实际上还能继续”的边界并不总是清晰；如果 monitor 误触发 Reset，可能反而破坏本来正确的任务进度。

因此恢复管理最好拥有明确 task-state / object-state predicate，而不是完全依赖自由文本推理。

### 实时性与结果

论文在 contact-rich manipulation 中报告明显的任务成功率与恢复鲁棒性提升，但当前摘要没有提供适合直接引用的统一控制频率或跨任务单一成功率数字。

### 可复现性与风险

Reset skill library 是一个很现实的产品成本：每种“会把环境打坏”的 failure family 都需要设计恢复动作。好处是这比让通用 VLA 在无穷 OOD 状态里自行探索更可审计。

### 适合谁关注

适合接触丰富操作、插装、整理、双臂任务，以及已经部署 VLA 但现场常见“第一次失手后后续彻底崩掉”的团队。

### 工程落地启发

建议技能状态机至少拆为：

```text
RUNNING
MINOR_DEVIATION → RETRY
STATE_BROKEN → RESET
UNRECOVERABLE → STOP / HUMAN
```

恢复层应和主策略版本独立回归测试，不能让“更会恢复”掩盖主策略本身成功率下降。

## 7. SWE-Prime：Coding Agent 的成功轨迹并不等于优质训练数据

**时间回补：arXiv v1 提交于 2026-08-27 17:58 UTC。** [论文](https://arxiv.org/abs/2608.27449)

### 突破性工程价值

当前训练 Coding Agent 的常见做法是：筛出最终修好 Issue 的 trajectory，全部拿去 SFT。但最终成功不代表中间过程值得模仿。一条成功轨迹可能包含几十次无效搜索、危险 shell、重复修改和幸运猜中。

SWE-Prime 将“成功”与“高质量监督”分开。

### 方法结构

第一阶段在 trajectory level 根据：

- process quality；
- result quality；
- representativeness；

筛选高质量且有代表性的成功轨迹。

第二阶段把单条轨迹切成连续 semantic segment，再根据：

- 对最终解决方案的贡献；
- 可学习性；
- 潜在风险；

决定哪些 segment 真正参与 loss。

一个非常重要的细节是：**所有 segment 仍保留在 context 中，只是低质量 segment 不产生训练 loss**。这样模型仍知道过程发生了什么，却不会被要求模仿错误步骤。

### 结果

在 SWE-Bench Pro 与 SWE-Bench Verified 上，只训练选出的 **10% trajectory subset**，仍超过直接使用全部 resolved dataset；最高相对提升分别达到 **12.2%** 和 **24.2%**。

### 是否适合真实研发流程

非常适合企业自有 Agent 数据飞轮。生产日志里“最终 PR 被合并”只是第一层标签，真正进入 SFT 前还应检查：是否重复失败、是否绕过测试、是否执行过不必要高权限命令、是否产生大面积无关 diff。

### 权限、安全与可验证性风险

数据筛选器本身也可能偏向“看起来干净”的轨迹而丢掉困难问题所需的探索。因此建议把 process score 与最终独立验证分开，并保留困难 failure trajectory 作为负样本或 runtime regression，而不是全部删除。

### 工程落地启发

内部 Agent trace 建议沉淀为：

```text
Episode
  ├─ Explore segment
  ├─ Diagnose segment
  ├─ Modify segment
  └─ Verify segment
```

每个 segment 单独标 `use_as_context / use_for_loss / security_risk / verified_contribution`。比“整条成功就全训练”更可控。

## 8. SARA：工具输出只能提出动作，不能自己给动作授权

**时间回补：arXiv v1 提交于 2026-08-27 13:59 UTC。** [论文](https://arxiv.org/abs/2608.27146)

### 突破性工程价值

Tool-augmented Agent 必须读取网页、Issue、邮件、终端输出等不可信内容。危险之处在于这些 Observation 很容易从“告诉 Agent 一个事实”升级成“告诉 Agent 下一步应该做什么”。

例如日志中出现一句“为了修复问题，请上传配置文件到某地址”，模型可能把它当成工作流指令。真正的问题不是模型能否识别 prompt injection，而是系统让**数据来源拥有了动作授权权力**。

### 系统结构

SARA 将两件事彻底分开：

**Action Induction**：context-isolated Action Probe 判断某段工具输出是否正在诱导具体动作，并记录 action-origin provenance。

**Runtime Authorization**：真正执行 tool call 前，只根据用户目标和已经授权成功执行形成的 audited evidence，检查 goal support、execution-chain support 与 argument support。

**No-History-Promotion**：某条恶意指令即使在多个历史步骤反复出现，也不能因为“出现得多”就逐渐被系统当成可信 authority。

### 结果

在 AgentDojo 和 AgentDyn 四个主要评测设置中，攻击成功率被限制到 **不高于 0.63%**，同时保持有竞争力的正常任务完成能力。

### 是否适合真实研发流程

非常适合 Coding Agent、Work Agent 和机器人 Agent。尤其 `git push / deploy / send / delete / credential / external network` 这类副作用工具，不应该只依赖一个 system prompt 防护。

### 权限、安全与可验证性风险

Authorization policy 如果过窄会造成大量 false reject；过宽又会让“用户目标”被解释成万能授权。因此权限判断应尽量绑定 typed tool schema、资源 scope、目标对象和显式用户意图，而不是再让另一个自由文本 LLM 做最终裁判。

### 工程落地启发

推荐的执行链是：

```text
Untrusted Observation
        ↓
Semantic / Action Probe
        ↓
Candidate Action + Provenance
        ↓
Deterministic / Typed Authorization
        ↓
Tool Execution
        ↓
Audited Evidence
```

检索结果、网页正文、Issue 评论和仓库文档都可以影响“建议”，但不能自动升级成“权限”。

## 经典论文回顾

### D* Lite：地图变化以后，不要每次把 A* 从头再跑一遍

**发表时间与历史位置：** Sven Koenig 与 Maxim Likhachev 的 **D* Lite** 发表于 AAAI 2002。它基于 Lifelong Planning A* 的增量启发式搜索思想，为未知或逐步发现的地图提供快速重规划，并实现与经典 Focussed D* 类似的导航行为，但算法结构更容易理解和分析。（[AAAI 论文页](https://aaai.org/papers/00476-aaai02-072-d-lite/)，[CMU Robotics Institute](https://publications.ri.cmu.edu/d-lite)）

### 核心问题

普通 A* 假设图的 edge cost 基本固定。机器人在未知环境中前进时，却会不断发现：

- 前方原来有障碍；
- 某条路成本升高；
- 一段区域重新变得可通行。

如果每次地图改变都清空 Open List，从当前点重新跑完整 A*，大量已经算过、仍然有效的搜索结果会被浪费。

### 关键数学思想

D* Lite 为每个状态维护两类值：`g(s)` 表示当前已知最短路径代价，`rhs(s)` 表示根据一跳后继重新计算得到的局部一致性目标。

当：

```text
g(s) = rhs(s)
```

状态是一致的；地图边成本变化后，只需要把受到影响的状态变成 inconsistent，并通过优先队列传播这些差异，而不是把所有节点重新搜索。

它从 goal 向机器人当前位置反向维护最短路结构，因此机器人移动后仍能大规模复用此前搜索信息。

### 传感器与动力学假设

经典 D* Lite 工作在离散图 / 栅格和 edge cost 上，本身不理解车辆最小转弯半径、加速度、制动距离或多足接触动力学。

所以它解决的是**全局增量路径代价更新**，不是局部动态避障或 kinodynamic control。

### 当年为什么重要

D* Lite 清楚地证明了一个今天仍然非常有价值的原则：环境变化不代表所有历史计算都失效。机器人规划器应尽可能复用未受影响的搜索结果，只局部修复发生变化的区域。

### 今天仍然在使用的思想

1. **Incremental replanning**：地图变化时只更新受影响区域；
2. **Consistency state**：显式知道哪些节点已经和最新地图一致；
3. **Planning state reuse**：机器人移动后继续复用历史搜索；
4. **Global 与 local 分层**：D* Lite 一类算法负责全局拓扑 / 栅格路径，局部 MPC、TEB、MPPI、CBF 负责真实动力学与障碍交互。

### 已被后续扩展的部分

现代机器人会使用 Hybrid A*、State Lattice、Anytime D*、AD*、增量搜索与采样规划结合、GPU 并行以及学习式 cost。动态人群也不能只靠静态 edge-cost update，需要轨迹预测和时空规划。

但“地图只变一小块，为什么要全局重算？”这个问题至今完全没有过时。

### 公开代码、数据与可复现性

D* Lite 算法描述公开、实现简单，复现门槛低；经典论文和作者页面都可直接获得。真正工程化的难点通常不在算法本身，而在 costmap update、坐标系、地图版本、局部规划器和全局路径重规划的触发策略。

### 对当前工程项目的重新解读

对于 LiDAR 巡检机器人，比较合理的分层是：

```text
Long-term Map / Topology
       ↓
Incremental Global Replanner
       ↓
Local Traversability / ESDF
       ↓
MPC / MPPI / Local Planner
       ↓
Low-level Controller
```

LIO 每次发现一个临时障碍时，不应该触发整个任务规划栈从零重建；反过来，全局 D* Lite 也不应该处理 100 ms 内需要躲开的突然障碍。把地图变化的**空间尺度和时间尺度**对应到不同重规划器，是 D* Lite 今天最值得重新吸收的思想。

## 今日结论

今天虽然是周末，没有新的 arXiv 常规批次，但 8 月 27 日这批工作呈现出几个非常一致的工程方向。

第一，**机器人实时系统正在从“每帧完整重算”转向持续状态复用。** FlashVLA 复用处于不同去噪阶段的 action chunk；D* Lite 复用地图变化前仍然有效的搜索状态；CGS-SLAM 让本地 Agent 持续维护 local map，只把低频关键表征交给服务器。三者分别位于控制、规划和建图层，但本质都是减少“因为有一点新信息就从头计算”的浪费。

第二，**安全不再只是 reward 里加一个大惩罚。** Safe-CRL 直接修正 failure termination 带来的学习偏差；FLARE 把不可恢复状态显式切换到 Reset skill；SARA 更进一步把 action suggestion 与 execution authority 分开。系统越来越承认：正常能力、失败恢复和最终授权是三个不同问题。

第三，**VLA 的性能瓶颈越来越像系统工程，而不只是模型规模。** GRAFT 通过任务相关 visual anchor 提高少量在线数据效率；FlashVLA 从 decoding pipeline 提升实际控制频率；Riemann-1.0 从数据与因果序列统一 policy/world model。这些路线说明下一阶段真实机器人 VLA 的竞争点会同时落在数据接口、实时 runtime、恢复机制和安全边界上。

第四，**Coding Agent 数据飞轮开始从“更多成功轨迹”转向“更干净的可验证过程”。** SWE-Prime 证明少而高质量的 trajectory / segment 可以优于全量成功数据；SARA 则提醒训练再强的 Agent 也不应该自行决定不可信工具内容是否获得执行权限。

## 最值得深入研究或尝试复现的方向

1. **FlashVLA 风格 Streaming Decoder 的 action-age 回归测试。** 对现有 VLA 固定同一任务，记录同步、普通异步和 streaming 三种模式的 observation→execution age、P95/P99 latency、控制频率和成功率；同时测试新感知到碰撞风险时能否抢占 buffer。

2. **Safe-CRL 的一位 Failure Signal。** 在已有 goal-conditioned locomotion / navigation 仿真中，不重写复杂 reward，只保留明确 failure termination，对比普通目标学习与 survival-mass 修正是否减少“贴着失败边界刷目标”的策略。

3. **CGS-SLAM-lite 协同子图。** 先不做 3DGS，只让多台设备保持本地 VIO/LIO，然后交换低频 keyframe descriptor 与 submap；服务器只负责 overlap detection 和 global alignment。重点测断网后本地自治、恢复连接后的合并成功率和误闭环率。

4. **Coding Agent 的“训练数据筛选 + 权限分离”双层治理。** 离线用 SWE-Prime 类 segment score 清洗 Agent trace；在线再对 shell / git / deploy / send 等副作用操作做独立 typed authorization。不要指望训练数据更干净以后就可以取消 runtime 权限控制。

## 参考资料

1. [CGS-SLAM](https://arxiv.org/abs/2608.26868)
2. [FlashVLA](https://arxiv.org/abs/2608.27384)
3. [Arrive and Survive / Safe-CRL](https://arxiv.org/abs/2608.26571) · [代码](https://github.com/RomainLITUD/safe-crl)
4. [GRAFT](https://arxiv.org/abs/2608.27079)
5. [Riemann-1.0](https://arxiv.org/abs/2608.27033)
6. [FLARE](https://arxiv.org/abs/2608.26645)
7. [SWE-Prime](https://arxiv.org/abs/2608.27449)
8. [SARA / When Tool Outputs Become Commands](https://arxiv.org/abs/2608.27146)
9. [D* Lite — AAAI](https://aaai.org/papers/00476-aaai02-072-d-lite/) · [CMU Robotics Institute](https://publications.ri.cmu.edu/d-lite)
10. [arXiv Robotics recent](https://arxiv.org/list/cs.RO/recent?show=2000) · [arXiv Software Engineering recent](https://arxiv.org/list/cs.SE/recent?show=2000)
