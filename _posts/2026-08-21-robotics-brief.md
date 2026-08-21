---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-21"
date: 2026-08-21 09:00:00 +0800
description: "本期关注长期场景记忆、候选轨迹世界模型、腿式机器人约束 DDP、无人机吊载抑摆、人形全身行为世界模型、灵巧操作预训练，以及 Coding Agent 与 PLC Agent 的项目级技能和运行时验证。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-21

## 摘要

截至 2026-08-21 09:00（Asia/Shanghai），arXiv Robotics 最新公开批次为 2026-08-20，共 38 条；Software Engineering 同日共 22 条。本期先核验最近 24 小时：高质量、可完整核验且未进入历史索引的候选不足 5 条，因此按任务规范扩展到最近 7 天。DA-WAM 的 v2 于 2026-08-20 06:46 UTC 修订，仍属于最近 24 小时窗口；其余主动态的 v1 主要提交于 8 月 18–19 日，均明确标为“时间回补”，不把 arXiv 列表日期误写为论文首次发布时间。（[arXiv Robotics](https://arxiv.org/list/cs.RO/recent?show=2000)，[arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent?show=2000)）

今天最值得关注的 SLAM / 长期自主方向是 LT-Mem。它没有把长期语义地图理解成“不断覆盖旧状态”，而是把多 session SLAM、跨 session 物体身份、对象波动性和事件历史统一起来，通过 Live / Delta / Meta 三层记忆保留“现在是什么、发生过什么、这个对象平时有多容易变化”。对于长期巡检机器人，这比只维护最新 3D 地图更接近真正需要的世界状态。

控制侧出现两个很强的工程信号。Real-Time Control-Constrained DDP 用 APG 替代反复 KKT 求解，把控制约束直接放进 DDP / multiple-shooting，仿真中在强欠驱动四足动作上实现 25–50 Hz MPC；Payload Swing Estimation 则展示一个完全不同的轻量路线，只用机载 IMU 与 throttle command 在线估计吊载摆频，不要求提前知道绳长和载荷质量，并通过姿态修正实现实机主动抑摆。

人形与灵巧操作方向也在从“单纯 imitation”向“可复用先验 + 在线可行性判断”移动。GigaBrain-WBC-0.5 让同一个 causal Transformer 同时预测动作、下一本体状态和下一行为命令分布，并把这个分布反过来作为运行时 OOD / best-effort 约束；ADEPT 则先用通用 object reposing 做 dexterity pre-training，再用保守 post-training 将已有灵巧先验迁移到插装、摆放等下游任务，并证明触觉在真实长时域操作中显著减少“已经抓住却又松开”的失败。

世界模型侧，DA-WAM 的重要点不是“更会预测未来”，而是让每条候选轨迹拥有自己的 counterfactual future latent，并强制 scorer 用该候选自己的未来表示做排序。这实际上回答了一个长期问题：如果世界模型预测的未来不能改变最终动作选择，那么再漂亮的未来表示也只是辅助特征。

AI Coding 侧，本期两个条目都进一步证明模型外工程的重要性。SkillForge 不等待仓库历史里恰好出现足够多相似 issue，而是主动从 test-covered core functionality 合成项目特定问题，再把解决轨迹蒸馏成 repository-specific skills；SemaPLC 则把“生成完成”的定义从模型自评或编译通过，提升为规格检查、项目集成编译和 live PLC runtime trace 全部通过。对工业软件 Agent，这类 verification-gated harness 比单纯换更强模型更接近生产可靠性。

本轮同时检查 OpenAI、Anthropic、Google DeepMind 与 Meta AI 的官方发布入口。过去 24 小时内没有发现足以挤入本期前 8 条的全新通用模型、代码模型或机器人基础模型正式发布；因此本期不使用较旧模型新闻补位。

## 1. DA-WAM：世界模型真正有用的前提，是每条候选轨迹都对应自己的未来

**最近 24 小时修订：v1 提交于 2026-08-19 16:33 UTC，v2 于 2026-08-20 06:46 UTC 修订。本期首次覆盖。**（[论文](https://arxiv.org/abs/2608.19085)，[代码](https://github.com/LeapWM/da-wam)）

DA-WAM（Decision-Aligned Future Latents for Driving World Models）针对自动驾驶世界模型里一个很容易被忽略的问题：很多方法虽然预测未来，但所有候选轨迹最终共享同一个 future feature，或者未来预测只在预训练阶段使用。这样 scorer 仍可能主要依赖当前几何，而不是“如果走这条轨迹，未来会发生什么”。

### 为什么重要

候选 A 和 B 在当前位置可能几何上非常接近，但 A 会在 0.5 秒后进入碰撞趋势，B 不会。若两条候选共享同一个未来表示，世界模型无法把这种 action-specific consequence 真正传给 trajectory scorer。

DA-WAM 强制建立一一对应关系：每条候选轨迹先与当前 scene latent 交互，产生自己的 future latent，再由 scorer 同时读取当前场景、候选动作和该候选对应的未来表示。它把 world model 从“预测辅助器”变成候选排序的一部分。

### 算法模块

- V-JEPA 2.1 作为视觉表征基础；
- online encoder 加 LoRA，继续随规划目标适配；
- EMA target encoder 只在训练时提供稳定未来监督；
- 每个 trajectory candidate 独立产生 action-conditioned future latent；
- scorer 输出 NC、DAC、EP、TTC、Comfort 等可解释 planning factors 和最终 utility；
- 只对 expert-matched candidate 使用真实未来做 latent supervision，避免把执行过的未来错误分配给未执行候选；
- 增加 expert-proximate safety-critical hard negatives，逼迫 scorer 学习“几何相近但后果不同”的边界。

### 传感器与系统假设

当前方法主要是 camera-only driving planner，未来 latent 是学习表示，不是 occupancy / reachability certificate。离线日志只包含实际执行轨迹的真实未来，其余 counterfactual candidate 的未来没有 ground truth，因此只能通过规划 factor、utility 和 ranking 间接训练。

这意味着它非常适合候选规划排序，但不能因为模型预测“安全”就取消几何碰撞检查或规则安全层。

### 实时性与结果

NAVSIM-v1 上 DA-WAM 达到 93.7 PDMS，NAVSIM-v2 达到 87.7 EPDMS；在 v2 中 TTC 和 Lane Keeping 分别达到 97.9 和 97.6。推理阶段不需要 target encoder、真实未来或 hard-negative retrieval，只保留 online encoder、future predictor 和 scorer。

### 鲁棒性、可复现性与风险

代码已公开，可复现性较好。但当前结果主要是离线 driving benchmark；候选未来预测是否能在真实闭环中抵抗传感器延迟、动态目标误检和 distribution shift，还需要进一步验证。

另一个风险是“latent 很好用但不可解释”：若未来表示错误，factor head 仍可能以很高置信度输出安全分数，因此真实系统最好继续保留 TTC、ESDF、交通规则等独立检查。

### 适合谁关注

适合 World Action Model、候选轨迹规划、自动驾驶、无人机局部路径评分，以及正在研究“世界模型到底怎样进入控制决策”的团队。

### 工程落地启发

如果现有机器人已经有 10–100 条候选轨迹，不必先训练大视频世界模型。可以先为每条 candidate 预测一个轻量 future state / collision latent，再让 scorer 必须读取该 candidate 的预测结果；然后做消融：去掉 future latent 后最终候选是否真的改变。若几乎不变，说明世界模型尚未真正进入决策链。

## 2. LT-Mem：长期 SLAM 不应只保存“最新地图”，还要保存对象历史和变化规律

**时间回补：v1 提交于 2026-08-19 15:56 UTC；IROS 2026 接收。本期首次覆盖。**（[论文](https://arxiv.org/abs/2608.19059)，[项目页](https://lt-mem.github.io/)）

LT-Mem（Volatility-Aware Spatio-Temporal Memory for Lifelong Scene Understanding）针对长期机器人一个非常实际的问题：地图每次更新都覆盖旧对象状态，机器人最终只知道“椅子现在在哪”，却回答不了“这把椅子过去几周移动过几次、通常出现在哪、这次变化是不是异常”。

### 为什么重要

巡检机器人真正需要的长期世界模型往往包含两种事实：稳定结构和会变化的对象。对稳定设备，频繁多假设会浪费存储；对推车、椅子、工具箱，一旦简单 overwrite，又会丢掉有价值的事件历史。

LT-Mem 的关键是给对象维护 volatility，并让不同对象采用不同记忆更新策略。

### 算法模块

- multi-session SLAM 先将不同 session 的对象观测对齐到统一空间；
- 跨 session object re-identification 使用空间、时间、视觉和运动一致性等确定性证据；
- volatility-aware policy 在 overwrite / hold / multi-hypothesis 之间选择；
- Tri-Memory 分成 Live、Delta、Meta：分别保存当前状态、事件变化和长期统计；
- 当 session 对齐结构出现较大异常时，进入 hold，避免错误全局配准污染长期记忆；
- LT-VQA 用多 session persistent identity 和 temporal QA 测试机器人能否回答长期事件问题。

### 传感器与 SLAM 假设

它建立在 multi-session SLAM 已能获得足够可靠的 Sim(3) / 跨 session 对齐之上。若底层回环错误，object identity 很容易被错误合并或拆分。

因此 LT-Mem 不是 LIO / VIO 的替代品，而更像长期 SLAM 上层的对象记忆后端。对工业场景尤其应让结构地图、对象状态和事件历史分层维护，而不是全塞进一张语义点云。

### 实时性与资源

论文与项目结果显示，结构化记忆相对把历史 session 大批量重新喂给 VLM，可以把 token 消耗降低一个数量级，同时提高 temporal QA / event reasoning。项目已公开数据入口，但代码当前仍标记为待发布，因此完整复现性尚不如已有开源 SLAM 系统。

### 鲁棒性与风险

核心风险有三类：跨 session 对齐错、同类物体 re-ID 错、动态对象长期状态被错误固化。工程上每个长期对象都应该保留来源 session、时间戳、置信度、最近观测和可回滚的历史，而不是只保存一个“当前真值”。

### 适合谁关注

适合长期巡检、多 session SLAM、语义地图、数字孪生、仓库/工厂变化检测和机器人长期记忆团队。

### 工程落地启发

可以在现有 LIO-SAM / FAST-LIO 地图上先建立一个独立对象层：`object_id / pose / covariance / first_seen / last_seen / volatility / observation_history / state_hypotheses`。只有低波动对象才进入稳定地图，高波动对象保留事件历史。这样不需要改前端 LIO，也能先获得“长期地图不是每次全覆盖”的能力。

## 3. Real-Time Control-Constrained DDP：腿式 MPC 的控制约束不必每次都靠重型 QP/KKT 求解

**时间回补：v1 提交于 2026-08-19 05:21 UTC；IEEE RA-L 2026 接收。本期首次覆盖。**（[论文](https://arxiv.org/abs/2608.18552)，[DOI](https://doi.org/10.1109/LRA.2026.3723262)）

这项工作提出 ABC-DDP（Accelerated Projected Gradient based Control-Constrained DDP），目标是在强欠驱动腿式机器人上，把控制上下限真正放进 DDP，同时保持可以用于短 horizon real-time MPC 的求解速度。

### 为什么重要

传统 DDP / iLQR 的优势是能充分利用时序动力学结构，但一旦加入严格 control constraints，常见做法会进入 QP / KKT 子问题，活动集变化时需要反复矩阵求解，实时性明显恶化。

ABC-DDP 使用 accelerated projected gradient 在 box / control constraints 下识别 active set，避免每轮都做重型 KKT inversion；同时用 virtual constraint 将控制限制纳入 feasibility-driven multiple shooting，使动态上不可行的初始轨迹也能逐步收敛。

### 算法模块

- DDP / multiple-shooting 主体；
- APG 求局部 control-constrained step；
- active-set identification；
- virtual constraint 维持控制可行性；
- short-horizon receding MPC；
- 同一求解器覆盖双腿静止平衡、catwalk、直立行走和高速跑动。

### 动力学假设

论文使用约 37.5 kg 四足动力学模型，强依赖刚体、接触和摩擦模型。控制约束被严格处理，不代表 contact model 就是真实的；实际足底柔顺、摩擦突变和执行器延迟都可能让离线/仿真可行轨迹在真机上变得不可行。

### 实时性

论文在短 horizon MPC 仿真中报告 25–50 Hz 更新：不同任务的平均求解时间约 1–6 ms，最坏时刻仍落在几十毫秒以内。作者同时比较 APG 与 QP 路线，APG 在离线长 horizon 求解中明显减少总时间，主要收益来自避免反复 KKT inversion。

### 鲁棒性、可复现性与风险

目前公开结果是 real-time simulation，并非真实四足硬件闭环。因此应把它看成值得复现的优化器结构，而不是已经证明可直接上机器人。

真实落地需要重点检查 contact switch、摩擦系数估计、state estimation latency、motor torque tracking 和 warm start。MPC 即使数学上实时，如果观测与执行链存在 20–50 ms 延迟，也可能失去预期稳定裕量。

### 适合谁关注

适合四足/人形 whole-body MPC、DDP/iLQR、强约束最优控制以及希望减少通用 QP 求解开销的团队。

### 工程落地启发

若现有 MPC 的主要瓶颈在每步 QP，不一定先换强化学习。可以先把控制约束划分成简单 box / active-set 可处理部分与复杂接触约束部分，让 DDP 内部直接解决前者；同时记录 P50/P95/P99 solve time，而不是只看平均优化时间。

## 4. 无载荷参数吊载抑摆：只用 IMU + 油门在线估计摆频，再给姿态环加阻尼

**时间回补：v1 提交于 2026-08-19 07:19 UTC。本期首次覆盖。**（[论文](https://arxiv.org/abs/2608.18625)）

《Payload Swing Estimation and Damping Without Payload Parameters for Multirotor UAVs》针对吊载无人机部署中一个很烦人的问题：绳长和负载质量经常变化，而很多 anti-swing controller 需要提前知道这些参数或额外安装视觉/摆角传感器。

### 为什么重要

实际运输任务中，现场人员更换绳子、挂载不同工具或载荷后，重新做系统辨识非常不现实。如果能够从无人机自身 IMU 与 throttle 中分离周期扰动，并把摆频作为状态在线估计，就能把 anti-swing 做成更接近 plug-and-play 的模块。

### 算法模块

- 只读取 onboard IMU 与 throttle command；
- EKF 把周期扰动和未知 pendulum frequency 一起作为状态估计；
- 不显式输入 cable length 或 payload mass；
- active damping 根据估计摆动生成 correction angle；
- correction angle 注入已有 attitude setpoint / attitude loop，不需要重写飞控内部控制器。

### 传感器与动力学假设

方法仍然假设主导扰动近似单摆型周期运动。非常短的绳长、强空气动力、双绳/多点悬挂或载荷大幅旋转可能破坏这一近似。

另外“不需要载荷参数”不等于完全不需要飞行器模型：基础姿态控制、推力映射和 IMU 状态仍必须可靠。

### 实时性与实机结果

系统以 100 Hz 级嵌入式周期运行。论文在不同绳长和不同载荷质量上完成飞行实验；增益扫描中 `k_c=0.3` 时摆动衰减时间常数约 2.23 s，相对被动基线 6.43 s 缩短 65.3%。当增益过大时抑摆反而恶化，说明这不是“越强阻尼越好”。

### 鲁棒性与风险

短绳场景下摆动信号幅值变小，频率估计更容易被噪声淹没。真实产品应增加 estimator confidence；低置信度时退出主动抑摆，而不是继续注入高增益姿态修正。

还需要给姿态 correction 设置严格幅值和速度限制，确保 anti-swing 不会与避障、定位恢复或主任务姿态产生冲突。

### 适合谁关注

适合吊载无人机、消防/喷洒工具吊挂、绳索载荷运输和希望在 PX4/ArduPilot 外层增加轻量抑摆模块的团队。

### 工程落地启发

可先把它做成 companion-computer 外环：订阅 IMU / throttle，输出有限幅的 roll/pitch correction。这样不修改飞控核心，容易 A/B；同时记录估计摆频、confidence、damping ratio 和姿态修正量，现场换载荷后无需人工录入绳长/质量。

## 5. GigaBrain-WBC-0.5：让全身控制器同时预测“下一步会发生什么”，并用预测分布拒绝不可能命令

**时间回补：v1 提交于 2026-08-18 18:21 UTC。本期首次覆盖。**（[论文](https://arxiv.org/abs/2608.18234)，[项目页](https://shepherd1226.github.io/gigabrain-wbc-0.5/)）

GigaBrain-WBC-0.5 将自己定义为 Behavior World Model：同一个 causal Transformer 不只输出 humanoid 的下一动作，还预测下一 proprioceptive state，以及下一 latent behavior command 的分布。

### 为什么重要

普通 motion tracker 的目标是“尽量追 reference”。但当 reference 本身物理上不可执行，例如脚下支撑不存在、动作穿模、环境位置变化时，一个只会追踪的 policy 往往会继续执行直到摔倒。

GigaBrain 的思路是让控制器本身学到“在当前环境和自身状态下，什么行为仍属于训练分布”。部署时如果外部命令偏离模型认为可行的区域，就把它 retract 到最近的 learned behavior，以 best-effort 方式执行，而不是盲目追踪。

### 算法模块

- causal Transformer 联合预测 action、next proprio state 和 next-command distribution；
- 自动 terrain annotation 从 retargeted motion 中恢复实际接触过的 3D 支撑几何；
- 用环境接触训练坐、踩台阶、倚靠等 whole-body interaction；
- 运行时用 predicted command distribution 做 OOD filtering / projection；
- 同一 policy 同时承担普通 tracking、环境交互、fall recovery，不单独切换 recovery controller；
- Unitree G1 checkpoint 可进一步微调到 Maker L01。

### 动力学与控制假设

部署控制约 50 Hz，输出关节 PD target，上游参考由实时 command 提供。训练引入摩擦、质量、质心和扰动随机化，但模型仍依赖已有动作和接触数据覆盖。

所谓“world model”主要建模行为/本体未来，并不是完整 3D 环境预测器。其 OOD filter 判断的是“像不像训练过的可行行为”，不等于直接计算真实物理风险。

### 结果与硬件验证

论文在 sim-to-sim benchmark 中报告 terrain interaction 成功率 81.3%，相对最强对比约 4.3 倍；面对物理不可行命令时成功保持稳定的比例为 83.1%，fall recovery 达到 99.3%。论文同时提供硬件环境交互、缺失支撑和外部扰动实验。

### 鲁棒性、可复现性与风险

作者明确指出更完整的真实机器人 latency 与组件消融仍待补充，代码也尚未完整开放。运行时安全半径需要针对 checkpoint / platform 重新标定，因此目前不应把该 filter 当作形式化安全层。

### 适合谁关注

适合人形 whole-body control、大规模 motion tracking、环境接触、fall recovery 和希望给动作生成器增加可行性过滤的团队。

### 工程落地启发

这个思想可以比人形更通用：任何生成式控制器都可以额外训练一个 `p(feasible_behavior | state, command)`，在命令进入低层前做投影或降级。对于机器狗楼梯/狭窄环境，也比“reference 不可执行时仍强追”更安全。

## 6. ADEPT：先学通用灵巧 reposing，再用保守 RL post-training 迁移到真实插装任务

**时间回补：v1 提交于 2026-08-19 17:55 UTC。本期首次覆盖。**（[论文](https://arxiv.org/abs/2608.19182)，[项目页](https://adept-dexterity.github.io/)）

ADEPT（Accelerating Dexterity via Pre-Training and Post-Training using Reinforcement Learning）试图回答灵巧操作里最现实的问题：每一个插孔、摆盘、抓取任务都从零训练 billions of simulation steps，成本太高，而且不同任务反复重新学抓稳、提起、手内重定向等基础能力。

### 为什么重要

ADEPT 先训练一个任务无关的 object reposing prior，然后在具体下游任务中继续 RL，而不是重置 policy。真正关键的是它发现“直接 PPO fine-tune”很容易摧毁先验，因此设计了更保守的 post-training recipe。

### 算法模块

- 通用 object reposing RL pre-training；
- 下游任务先用 behavior cloning / distillation 继承 prior；
- fresh critic warm-up，避免初始 value 错误拖坏 actor；
- 低 actor learning rate、小 clip 的 conservative PPO；
- Joint-space Geometric Fabric 放在 policy 与机器人之间，负责 joint limits、collision 和几何可行性；
- 视觉或视觉+触觉 student 将仿真 teacher 零样本迁到真实机器人。

### 本体与传感器

论文覆盖 KUKA + Allegro Hand 以及 Flexiv + Sharpa 灵巧手。前者主要视觉，后者还使用 fingertip vision-based tactile。策略层约 60 Hz，底层机械臂/手控制使用更高频率执行。

这说明灵巧 RL 最合理的结构不是把神经 policy 直接接电机，而是 `policy → geometric fabric / constraints → high-rate servo`。

### 真机结果

KUKA-Allegro 在 FMB star 插装达到 5/10，square/round 3/10，dish placement 6/10；Flexiv-Sharpa 在 square/round 上加入触觉后达到 8/10，而纯视觉只有 3/10。论文特别指出纯视觉策略经常已经抓住物体，却因为无法确认接触而再次张手，导致后续整段任务失败。

完整动作约 5–10 s，论文对比的传统分阶段人类示范流程约 20–70 s，显示连续手内重定向可以显著缩短任务链。

### 鲁棒性、可复现性与风险

ADEPT 仍需要非常大的仿真训练预算，且作者明确把 perception 列为主要瓶颈，特别是遮挡下非对称 peg 姿态。触觉改善了 grasp confidence，但不同指尖、材质和相机配置仍需重新适配。

### 适合谁关注

适合灵巧手、接触密集装配、RL pretrain/post-train、sim-to-real 和希望构建可复用 manipulation prior 的团队。

### 工程落地启发

对工业操作机器人，可以先把“抓稳、提起、重定向、接触保持”训练成基础 prior，再给具体工位只做小规模 post-training。更重要的是，必须防止下游 RL 把基础能力洗掉：旧任务 replay、actor 小学习率、独立 critic warm-up 和硬几何约束都应该成为标准发布流程。

## 7. SkillForge：仓库经验不够时，Agent 可以主动制造项目特定问题来锻造 skills

**时间回补：v1 提交于 2026-08-19 14:01 UTC。本期首次覆盖。**（[论文](https://arxiv.org/abs/2608.18933)，[代码与数据](https://github.com/cslsolow/SkillForge)）

SkillForge 解决 Coding Agent 的一个长期限制：项目历史里真正高质量、能揭示仓库内部约束的 issue 数量有限，而且很多 bug 类型从未出现过。仅从历史修复记录提炼 memory，覆盖面天然受限。

### 为什么重要

SkillForge 不等待真实 bug 出现，而是从 tests 已覆盖的核心 repository functionality 出发，主动修改多个协同函数/代码段，生成 project-specific synthetic issues；Agent 解决这些问题后，再把成功与失败轨迹蒸馏成 entity-grounded diagnostic / intervention skills。

它更像“让 Agent 在仓库副本里先做专项训练”，而不是上线后边犯错边积累经验。

### 算法与工作流

- 从 core tests 识别项目真实功能路径；
- 在严格 temporal isolation 下合成 issue，避免未来 gold patch 泄漏；
- 使用 Mini-SWE-Agent 风格执行器解决 synthetic issues；
- 从解决轨迹抽取 repository-level diagnostic skills 与 entity-level intervention skills；
- 用 BM25 检索与当前真实 issue 相关的少量 skills；
- skills 与具体仓库 entity 绑定，而不是只保留泛化自然语言总结。

### 结果与成本

SWE-bench Verified 上，DeepSeek-V3.2 从 66.4% 提升到 72.2%，GPT-5-mini 从 55.0% 提升到 60.6%；SWE-bench Pro 上分别提升 5.8 和 4.1 个百分点。

它不是免费的：离线 issue synthesis / resolution 增加了预计算成本。论文把这部分摊销到每个真实 issue 的平均成本中；工程上应把它看成“为一个长期仓库提前买知识”，而不是单次任务最低成本方案。

### 权限、安全与可验证性风险

Synthetic issue 必须始终在隔离 revision / worktree 中生成，绝不能污染真实分支。skill 也必须绑定 repository commit / version；项目结构变化后，旧 intervention skill 可能从经验变成错误指令。

另一个重要结果是 skills 对底模存在明显依赖：某模型自己蒸馏的 skill 给另一个模型使用，收益会下降。因此不能把 Agent skill 当成天然跨模型通用知识。

### 适合谁关注

适合长期维护大型仓库、Codex/Claude Code/OpenHands 类 Agent、企业内部 coding skill 平台，以及已有高测试覆盖率代码库的团队。

### 工程落地启发

可以在 nightly CI 的仓库副本中自动生成“可恢复 synthetic bugs”，让便宜模型尝试定位/修复，再把高价值失败轨迹变成项目 skill。真正进入生产前，每条 skill 都应带 `source_revision / affected_entities / evidence / expiry / regression_test`，而不是只有一段 Markdown 建议。

## 8. SemaPLC：工业 Coding Agent 的“完成”必须经过真实运行时验证，而不是编译通过就结束

**时间回补：v1 提交于 2026-08-19 05:44 UTC。本期首次覆盖。**（[论文](https://arxiv.org/abs/2608.18565)，[代码](https://github.com/midea-ai/SemaPLC)）

SemaPLC（A Project-Grounded, Verification-Gated Agent Harness for PLC Code Generation）非常适合工业软件团队关注。它不把 PLC code generation 当成普通文本生成，而是把项目上下文、规范、编译、部署和 live runtime trace 组成一个外部验证闭环。

### 为什么重要

PLC 代码“能编译”远远不等于“现场逻辑正确”。一个状态机可能编译正常，却在特定输入序列下遗漏 interlock；timer / latch / edge trigger 的语义也很难仅靠静态文本判断。

SemaPLC 的核心原则是：模型没有权力宣布任务完成。只有外部 verifier 留下可审计证据后，harness 才允许结束。

### Agent / Harness 模块

- project-grounded context：读取真实工程符号、依赖和 POU 结构；
- specification check：验证生成逻辑与要求是否一致；
- integrated compilation：候选必须放回真实项目中编译；
- static behavior checks；
- dynamic runtime verification：把候选和 reference 部署到 live PLC runtime，在多个场景下比较 output traces；
- compile、deploy、timeout 或缺失 trace 均直接计为失败；
- hidden reference / scoring artifact 不暴露给生成模型，减少 reward hacking。

### 结果

117 个独立 POU 任务、7 个 backbone 上，完整 SemaPLC harness 的 strict verified pass rate 平均 72.6%，高于 bare 同底模的 55.3% 和最强基线平均 63.9%。

65 个 project-context 任务中，平均 integrated compilation 达 89.4，dynamic behavior 达 52.2，而最佳对比的动态分数为 31.4。这个差异说明静态/编译指标相近时，真实运行时行为仍可能完全不同。

### 权限、安全与工程风险

最大的风险恰恰来自“真实运行”。Agent 生成的 PLC 逻辑绝不能直接部署生产设备。live runtime 必须是仿真 PLC、数字孪生、测试架或具有物理隔离的 staging controller；I/O 要通过安全 proxy，禁止真实危险输出。

此外，动态测试只覆盖有限 scenario。通过当前隐藏测试并不是形式化安全证明，功能安全逻辑仍需要独立审计、SIL/PL 流程和人工批准。

### 适合谁关注

适合 PLC / IEC 61131-3、工业自动化、机器人安全状态机、自动代码生成和需要强验证门禁的 Coding Agent 团队。

### 工程落地启发

SemaPLC 的模式可以直接迁移到机器人软件：Agent 修改控制/任务逻辑后，流程必须是 `compile → static checks → deterministic simulator → recorded-bag replay → hardware staging → human approval`。主 Agent 只能生成，最终“是否完成”由独立验证器决定。

## 经典论文回顾

### ikd-Tree：为什么 FAST-LIO2 时代的关键创新之一，其实是一棵会增量维护、区域删除和自我重平衡的 k-d tree

**发表时间与历史位置：** ikd-Tree《An Incremental K-D Tree for Robotic Applications》于 2021 年 2 月公开。它诞生在 FAST-LIO / FAST-LIO2 这类高频 LiDAR-inertial odometry 开始需要持续更新局部点云地图的阶段。传统静态 k-d tree 很适合建完后反复查，但机器人地图每一帧都在插入新点、删除远区、下采样；反复整树重建会迅速成为瓶颈。（[论文](https://arxiv.org/abs/2102.10808)，[官方代码](https://github.com/hku-mars/ikd-Tree)）

### 核心问题

在线 LIO 的地图数据结构同时需要：

- kNN / nearest-neighbor search 足够快；
- 每帧增量插点；
- 地图滑窗时按 box 批量删除；
- 在线 downsampling；
- 长期插入/删除后树不能越来越偏；
- 更新不能长期阻塞高频 scan-to-map。

普通静态 k-d tree 只解决第一项，ikd-Tree 则把“动态地图生命周期”也作为数据结构的一部分。

### 算法模块与关键思想

- incremental point insertion / re-insertion / deletion；
- point-wise 和 box-wise 操作；
- nearest-neighbor、box search、radius search；
- tree 内直接支持 downsampling；
- 持续监控树结构，在局部失衡时做 partial rebalancing；
- 多线程设计，尽量将重建与在线查询解耦；
- 删除可以先标记，再在合适的 rebuild 阶段真正清理。

原论文在随机数据和真实 LiDAR-inertial mapping 测试中报告，ikd-Tree 的运行时间约为静态 k-d tree 方案的 4%，说明收益主要来自避免“每帧地图变化都重建整棵树”。

### 传感器与地图假设

ikd-Tree 本身不关心 LiDAR 是 16 线、64 线还是固态扫描，它只管理 3D 点；因此它不会解决时间同步、运动畸变、几何退化和错误 correspondence。

它也不是地图表达本身。若局部地图需要 surfel、Gaussian、voxel occupancy、语义标签或 GPU 并行，k-d tree 未必是最佳载体。

### 当年为什么重要

FAST-LIO2 将 raw-point scan-to-map 与高频增量地图结合后，空间索引不再只是一个“库函数”，而直接决定前端能否实时运行。ikd-Tree 把增量更新、区域删除和下采样放进统一结构，使局部地图可以持续滑动而不用周期性停顿重建。

### 今天仍然有效的思想

1. **地图数据结构必须匹配更新模式。** 高频增量地图不应该使用只擅长静态构建的数据结构。
2. **删除和插入与查询同等重要。** 对机器人局部地图，生命周期管理本身就是实时算法。
3. **重建应局部化、异步化。** 不需要因为一个子树失衡就暂停整个定位线程。
4. **downsampling 最好与数据结构更新合并。** 避免先生成巨大点云再单独复制过滤。
5. **基准不只看 kNN 延迟，还应测长时间运行后的更新尾延迟和内存。**

### 已被后续扩展或替代的部分

现代 LIO 也大量采用 voxel hash、hierarchical voxel、surfel / Gaussian map、GPU spatial hash 等结构。对于稠密点云、GPU pipeline 或需要局部统计面的算法，voxel representation 往往比 exact dynamic k-d tree 更自然。

因此今天不应把 ikd-Tree 当作唯一正确答案，而应把它当成一个基准：如果新的 voxel/hash map 声称更好，应同时比较 nearest search、insert/delete、滑窗清理、长期内存和 P99 update latency。

### 公开代码、许可与可复现性

官方 `hku-mars/ikd-Tree` 仓库公开了 Build、Add/Delete Points、Delete Point Boxes、Nearest/Box/Radius Search 等接口，并被 FAST-LIO2 使用。仓库采用 GPLv2，并明确提示商业用途需联系作者，因此闭源商业产品需要单独评估许可风险。

### 对当前工程项目的重新解读

对多 LiDAR / 16 线雷达系统，最值得借鉴的不是“必须继续用 ikd-Tree”，而是把**地图数据结构和传感器职责分开设计**：

```text
每个 LiDAR 独立去畸变 / 质量检查
        ↓
融合后的局部几何更新
        ↓
动态地图结构：ikd-Tree / voxel hash / surfel
        ↓
按机器人移动做 box/voxel 区域淘汰
        ↓
退化检测决定哪些传感器约束应降权
```

16 线 LiDAR 点少并不代表数据结构不重要：如果每帧仍反复重建全局索引，有限算力会被地图维护吃掉；但如果真正问题是长走廊几何退化，换 ikd-Tree 又不会产生新的可观测方向。应把“地图维护性能”和“几何可观测性”作为两个独立问题测量。

## 今日结论

今天最明显的趋势是：**机器人系统正在从“一个模型完成全部任务”重新走向结构化分工。** DA-WAM 给每条候选轨迹配自己的未来表示；LT-Mem 把当前对象状态、变化事件和长期统计分层；GigaBrain 把生成命令与行为可行性预测合到同一控制器里；ADEPT 则把通用 dexterity prior、几何约束和高频 servo 分开。它们的共同点都是先明确中间表示和职责边界，再让学习模型工作。

控制方面也越来越强调“少改核心、可在线退化”。ABC-DDP 试图直接在最优控制结构内部更高效地处理约束；吊载抑摆则只在姿态 setpoint 上增加一个可旁路修正，不需要重写底层飞控。对工业/航空机器人，这种可回退、可限幅的增量式架构通常比一次性替换整套 controller 更容易真正部署。

AI Coding 的 SkillForge 和 SemaPLC 则把同样的工程原则带到软件 Agent：前者把项目经验变成有来源、有实体绑定的 skill，后者把“完成权”交给外部 verifier。下一阶段可靠 Agent 的核心竞争力，很可能不是让模型更自信地说“做完了”，而是让系统能证明它做过什么、依据什么、在哪个 revision 上通过了哪些真实检查。

## 最值得深入研究或尝试复现的方向

1. **给长期巡检地图增加 LT-Mem-lite 对象生命周期层。** 不改 LIO 前端，只给稳定对象和高波动对象建立不同更新策略；至少保存对象 `current / event history / volatility / source session / confidence`，验证多次巡检后是否能可靠回答“发生了什么变化”。

2. **把“候选轨迹 → 候选未来 → 候选评分”接入现有局部规划器。** 先不用视频 world model，用轻量网络预测每条候选的碰撞/可通行 latent，做 DA-WAM 式一一对应；对比共享 future feature 与 per-candidate future 是否真的减少危险候选被选中。

3. **给工业 Coding Agent 建独立 Verification Gate。** Agent 可以写代码，但不能决定完成。至少强制 `revision check → compile → unit/integration test → simulator/replay → diff audit`；对 PLC/机器人控制逻辑再增加 live staging runtime，并让测试证据独立保存。

## 参考资料

1. [DA-WAM: Decision-Aligned Future Latents for Driving World Models](https://arxiv.org/abs/2608.19085) · [代码](https://github.com/LeapWM/da-wam)
2. [LT-Mem: Volatility-Aware Spatio-Temporal Memory for Lifelong Scene Understanding](https://arxiv.org/abs/2608.19059) · [项目页](https://lt-mem.github.io/)
3. [Real-Time Control-Constrained DDP for Underactuated Balancing of Legged Robots](https://arxiv.org/abs/2608.18552) · [DOI](https://doi.org/10.1109/LRA.2026.3723262)
4. [Payload Swing Estimation and Damping Without Payload Parameters for Multirotor UAVs](https://arxiv.org/abs/2608.18625)
5. [GigaBrain-WBC-0.5](https://arxiv.org/abs/2608.18234) · [项目页](https://shepherd1226.github.io/gigabrain-wbc-0.5/)
6. [ADEPT: Accelerating Dexterity via Pre-Training and Post-Training using Reinforcement Learning](https://arxiv.org/abs/2608.19182) · [项目页](https://adept-dexterity.github.io/)
7. [SkillForge: Self-Distilling Agents for Project-Specific Issue Resolution](https://arxiv.org/abs/2608.18933) · [代码与数据](https://github.com/cslsolow/SkillForge)
8. [SemaPLC: A Project-Grounded, Verification-Gated Agent Harness for PLC Code Generation](https://arxiv.org/abs/2608.18565) · [代码](https://github.com/midea-ai/SemaPLC)
9. [ikd-Tree: An Incremental K-D Tree for Robotic Applications](https://arxiv.org/abs/2102.10808) · [官方代码](https://github.com/hku-mars/ikd-Tree)
10. [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent?show=2000) · [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent?show=2000)
11. [OpenAI News](https://openai.com/news/) · [Anthropic News](https://www.anthropic.com/news) · [Google DeepMind](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/) · [Meta AI](https://ai.meta.com/blog/)
