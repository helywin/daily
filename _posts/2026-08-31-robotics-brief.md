---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-31"
date: 2026-08-31 09:00:00 +0800
description: "本期聚焦具身场景重排、软体夹爪长期力控、受限仓库多机器人调度、VLM 规划与高频控制解耦、VLA 安全、去中心化异构机器人协作，以及 Coding Agent 的状态持久化与跨迭代安全。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-31

## 摘要

截至 2026-08-31 早间，能够通过当前公开检索稳定核验的最新高质量候选仍主要集中在 8 月 27–28 日公开的论文。严格最近 24 小时内没有足够 5 条高质量、未重复且可完整核验的主动态，因此本期按任务规范扩大到最近 7 天。最终 8 条主动态均未出现在截至 8 月 30 日共 460 条的覆盖索引中，且均明确标记为“时间回补”。本期没有为了凑数量而再次展开已经覆盖的最新 SLAM/LIO 工作；SLAM 方向放在经典论文回顾中，从地图表示和闭环一致性的角度重读 ElasticFusion。

机器人方向今天最值得关注的第一条主线是：**规划系统正在被迫面对真实机器人看不全、等不起、不能无限回退的约束。** ESRP 把场景重排从“拥有完整世界状态的几何搬运”改成只给第一视角观测和俯视目标布局，加入物体互相遮挡与长期任务规划；Instruct-to-Act 则把慢速 VLM 规划器与高频 world-model controller 明确解耦，使文本只承担稀疏高层指导，而不是直接进入每个低层动作周期。

第二条主线是：**机器人控制正在更多利用结构化物理状态，而不是只增加模型容量。** Relaxation-Aware Soft Gripper 直接把软材料的温度、黏弹松弛与持续抓持力放进同一感知—学习—控制框架，在 280 秒持续抓持中把平均绝对力误差压到 0.066 N。它说明软体机器人真正困难的不是一次抓住，而是材料状态会随时间演化，控制器必须显式处理“力会自己掉下来”的慢动态。

多机器人侧的两项工作也很有现实工程价值。A-sharp 面向单机器人宽度通道和死胡同仓库，通过动态 Haven 选择和 pending-release 规则减少机器人被固定等待点拖远的问题，并在 72,000 次运行中保持完整任务交付；Pass the Bucket 则研究另一种极端——机器人几乎没有中央通信，只凭邻居局部相遇就自组织形成与各自速度成比例的任务分区。前者适合正式仓储调度，后者更适合研究极简局部协作规则与系统自恢复。

VLA 安全方面，TrapVLA 给出一个需要严肃对待的供应链风险：模型在正常输入下表现可以几乎不变，但特定文本条件可能把动作推向预配置失败模式。其价值不在于攻击技巧本身，而在于提醒机器人团队：**VLA checkpoint、训练数据、prompt、动作输出与低层安全门禁必须分别拥有可信边界**，不能因为 clean benchmark 高就默认策略没有隐藏故障行为。

AI Coding 侧，本期两项工作都在强调“状态不能只活在当前 prompt 里”。Zero-Shot Self-Orchestration 用 manager-worker + 共享文件 ledger，在不训练、不针对 benchmark 调参的前提下让部分模型显著提高 LiveCodeBench 成绩，但收益依赖模型且 token 成本明显增加；Safety Does Not Compose 则从安全理论上指出，如果 Agent 每轮重新初始化监控状态，那么跨多次迭代分散证据的攻击在单轮 monitor 中可能根本不可区分。长期自主 Agent 需要**不随会话衰减的安全状态和独立的不可逆动作授权层**。

## 1. ESRP：真实场景重排不是“已知地图上的搬箱子”，而是边看边理解、边移动边消除遮挡

**时间回补：arXiv v1 提交于 2026-08-27 17:08 UTC；RA-L 2026 工作。** [论文](https://arxiv.org/abs/2608.27371) · [项目页](https://pie-lab.cn/ESRP/) · [代码](https://github.com/BIT-PIE/ESRP) · [数据集](https://huggingface.co/datasets/serendipity800/ESRP-PD)

### 为什么重要

很多场景重排 benchmark 给机器人完整对象位姿、无遮挡的目标状态甚至全局 occupancy map。真实移动操作不是这样：机器人只能从当前第一视角看到局部空间，家具会彼此遮挡，而且目标往往只是一张全局布局图。

ESRP（Embodied Scene Rearrangement Planning）把任务定义为：机器人只使用 egocentric observation 与目标 top-down layout，在 3D 环境中通过移动和物体操作，把当前场景重排成目标场景。ESRP-Bench 基于 OmniGibson，包含超过 5,400 对场景和 8,200 个对象，并提供 TAMP、VLM、IL、RL 四类基线。

### 算法模块

最合理的系统拆分并不是让一个大模型端到端输出全部动作，而是：

```text
局部视觉 / 深度观测
        ↓
对象身份 + 部分可观世界状态
        ↓
Belief / Scene Memory
        ↓
高层重排顺序规划
        ↓
移动 / 抓取 / 放置 TAMP
        ↓
执行后重新观测并更新世界状态
```

ESRP 中一个很关键的基线差异是：强 TAMP 可以在 privileged setting 下使用完整 occupancy 和精确对象状态，而真正 embodied setting 必须自己通过观测逐步建立这些信息。这恰好暴露了很多“规划算法很好，但默认 perception 已经把世界完全解释完”的研究断层。

### 传感器与系统假设

当前 benchmark 主要在 OmniGibson 中验证，尚不能直接等价为真实移动操作系统。现实里还会增加对象检测误差、抓取失败、动态人类、相机遮挡、底盘定位误差和物体实际接触动力学。

如果最终目标是工业巡检操作机器人，更应该把对象世界状态设计成带来源和置信度的 belief，而不是单一真值：

```text
object_id / pose / covariance / visibility / last_seen /
movable / graspable / task_role / target_region
```

### 实时性、鲁棒性与可复现性

ESRP 更偏长时域任务规划，而不是毫秒级控制 benchmark。官方已经公开代码和数据入口，可复现性比只给论文的工作更好。工程上最需要关注的是规划过程中 perception 与 memory 的错误是否会累积，以及失败后能否重新观察并修正错误世界状态。

### 适合谁关注

移动操作、客户现场家具/设备整理、仓储重排、长期任务规划、VLM/VLA 与 TAMP 融合团队。

### 工程落地启发

不要让高层任务规划直接依赖“最新一帧检测结果”。更可靠的是维护一个显式 object belief layer，并允许 planner 主动产生“先去看清楚”这一类 information-gathering action。真正的场景重排首先是部分可观测问题，其次才是几何规划问题。

## 2. Relaxation-Aware Soft Gripper：软体夹爪真正难的是 280 秒以后还能保持同样的力

**时间回补：arXiv v1 提交于 2026-08-27 05:19 UTC；RSS 2026 工作。** [论文](https://arxiv.org/abs/2608.26622)

### 为什么重要

软体夹爪的柔顺性使它适合脆弱物体和不确定接触，但软聚合物具有明显黏弹性：即使开度保持不变，内部应力也会随时间松弛，抓持力持续下降。

这意味着一个“刚刚抓住物体时很稳定”的控制器，不代表 30 秒、3 分钟以后仍然稳定。对于长时间搬运、工具保持、医疗或食品操作，这比瞬时抓取成功率更接近真实产品指标。

### 算法模块

该工作采用 structure-perception-learning 联合设计：

- 可变刚度软夹爪提供物理层调节能力；
- onboard vision 跟踪结构形变；
- IR thermography 跟踪温度场；
- temperature-coupled viscoelastic force representation 显式描述温度与材料松弛；
- physics-informed learning model 估计持续抓持中的力趋势；
- 力补偿控制根据预测结果逐步抵消 relaxation。

关键思想是：学习模型不是替代机械结构和物理控制，而是专门补解析模型难以准确覆盖的黏弹动态。

### 传感器与动力学假设

系统依赖视觉和红外温度场能够稳定反映材料形变/热状态。环境温度、材料老化、表面污染和夹爪制造差异都可能改变训练时建立的关系。

同时，红外与热致刚度变化属于慢动态，不能承担接触瞬间的硬实时保护。真正的产品仍需要电机电流、限力、速度限制或其他更直接的低层安全通道。

### 实时性与结果

在 280 秒力控制抓持任务中，论文报告平均绝对力误差为 **0.066 N**，相对固定开度基线改善约 80%，相对只使用瞬时状态的基线改善约 95%。

这里最值得关注的不是单个误差数字，而是评测时间尺度已经从“抓起一次”延长到数分钟持续保持。

### 鲁棒性、可复现性与风险

当前没有稳定公开的完整代码/硬件仓库，复现需要自制可变刚度软夹爪和红外视觉链，因此工程门槛不低。产品化还应额外评估不同材料批次、温湿度、对象热传导和连续循环老化。

### 适合谁关注

软体机器人、灵巧夹爪、食品/医疗操作、长时间抓持、柔顺工具操作团队。

### 工程落地启发

对任何存在柔性材料、皮带、弹性夹具或软指尖的系统，都应该把“材料状态”纳入控制状态，而不是只用瞬时位置映射力。建议长期日志至少记录 `command / deformation / temperature / estimated force / hold_time`，再观察 force drift 是否具有可预测结构。

## 3. A-sharp：受限仓库里，等待点本身也是一种必须被预约的资源

**时间回补：arXiv v1 提交于 2026-08-27 10:40 UTC。** [论文](https://arxiv.org/abs/2608.26939)

### 为什么重要

很多 MAPF/MAPD benchmark 使用宽阔网格，但真实高密度仓库为了提高货位利用率，会出现单机器人宽度通道、死胡同工位和很少的会车空间。

在这种拓扑里，“机器人任务完成以后去哪里等”并不是无关紧要的细节。等待位置选择不当，会让机器人堵死关键通道，甚至使后续任务无法被安全释放。

### 算法模块

此前 SHARP 为每台机器人分配固定 Haven，并要求任务路径最后能够安全退回自己的 Haven。A-sharp（Adaptive SHARP）允许在任务分配时动态更换 Haven，但增加两个关键规则：

- **availability test**：候选 Haven 必须真的可供当前机器人使用；
- **pending-release rule**：旧 Haven 在机器人真正离开以前仍保持保护，避免两个机器人瞬间同时依赖同一等待资源。

底层建立在 Safe Interval Path Planning（SIPP）和显式 Haven 结构假设上，并给出 invariant preservation 与 finite-release completeness 分析。

### 动力学与系统假设

当前抽象主要是离散仓储图，并不直接建模真实 AGV 的制动距离、转弯半径、通信丢包和定位误差。实际部署时 Haven 应该扩展成带 footprint、时间区间和安全缓冲的物理资源，而不是单一 cell。

### 结果与实时性

论文进行了 72,000 次运行、覆盖四张地图和 14,400 个配对测试案例。对于“可用 Haven 数多于机器人”的 138 种配置，A-sharp 在 107 种上显著优于 SHARP，且没有显著更差的配置；树状地图上的 makespan 中位数降低约 16.7%。

### 鲁棒性、可复现性与风险

算法的完备性结论依赖论文明确列出的 Haven 和 SIPP 假设。如果真实仓库有人、叉车或临时货物占据等待点，系统必须将 Haven availability 与实际感知/调度状态联动。

### 适合谁关注

AMR/AGV 调度、窄通道仓库、多机器人巡检、持续任务分配系统。

### 工程落地启发

把等待点、充电点、会车点、避让点都当成**带占用生命周期的调度资源**。多机器人系统不要只规划“从 A 到 B”，还要显式规划任务结束后的安全驻留状态，否则死锁很容易发生在任务看似已经完成以后。

## 4. Instruct-to-Act：慢 VLM 做稀疏规划，高频 world-model controller 自己连续控制

**时间回补：arXiv v1 提交于 2026-08-27 08:17 UTC；COLM 2026。** [论文](https://arxiv.org/abs/2608.26788) · [项目页](https://zinengtang.github.io/instruct-to-act/)

### 为什么重要

VLM 很适合解释开放式任务，但并不适合以高频率持续输出精细动作。反过来，学习式 world-model controller 可以做快速 observation-to-action control，却通常缺少开放式任务语言能力。

Instruct-to-Act 不要求二者互相替代，而是把它们放到不同时间尺度：VLM planner 偶尔生成高层文本 instruction，controller 在两次指令之间自主高频行动。

### 算法模块

训练时，作者把 controller rollout 自动切成行为片段，并为这些片段合成文本 instruction，再把 language-conditioned behavior cloning 与原有 reward/world-model objective 联合优化。

部署时结构变成：

```text
低频 VLM Planner
      ↓ 稀疏文本指令
World-Model Controller
      ↓ 高频动作
环境持续变化
      ↓
必要时重新请求规划
```

这一结构让上层 VLM 可以替换，而不必重新训练底层 controller。

### 传感器与控制假设

文本指令会出现 staleness：VLM 生成指令以后，环境可能已经改变。生产系统应该给 instruction 附带 `created_at / task_phase / valid_until / precondition`，而不是把自然语言字符串永久视为有效控制目标。

低层 controller 也必须拥有独立碰撞/限位/接触保护。上层语言计划正确，不代表每个低层动作都安全。

### 实时性与结果

论文在 7 个 embodied environment（其中 3 个多智能体环境）中评估，结果持续优于 controller-only 与直接 VLM action generation 变体，并在 7 个任务中的 6 个保持与强 VLA/MARL baseline 有竞争力的表现。

真正值得复制的不是某个统一 Hz，而是**规划和控制完全解耦**：慢推理不会冻结机器人低层闭环。

### 鲁棒性、可复现性与风险

系统需要大量 controller rollout 再做 instruction relabeling；如果合成 instruction 与真实动作语义对应不准，语言接口可能学成脆弱捷径。真实部署还要测试 planner 延迟、指令过期、错误指令和高层 planner 超时。

### 适合谁关注

VLM/VLA、语义导航、多机器人协调、移动操作，以及已经有可靠低层策略但希望增加开放语言任务能力的团队。

### 工程落地启发

高层模型接口最好是受限、结构化的 intent，而不是直接控制量：

```text
Intent {
  skill;
  target;
  precondition;
  timeout;
  priority;
}
```

语言模型负责“做什么”，高频 controller 负责“现在这一毫秒具体怎么做”。

## 5. TrapVLA：Clean benchmark 很高，不代表 VLA 没有隐藏的失败行为

**时间回补：arXiv v1 提交于 2026-08-27 03:44 UTC。** [论文](https://arxiv.org/abs/2608.26578) · [项目页](https://john-liua.github.io/TrapVLA/)

### 为什么重要

机器人基础模型正在越来越多地通过第三方 checkpoint、混合训练数据和现场 prompt 部署。传统模型供应链安全通常关注“模型会不会整体变差”，但更危险的情况是：模型在正常评测上几乎不掉点，只在某类特殊输入条件下稳定进入指定失败模式。

TrapVLA 构建了 Trap-LIBERO 与 Trap-RoboTwin，用 configured failure trapping 测试这类风险，并在仿真和真实机械臂上验证隐藏失败行为可以与 clean performance 同时存在。

### 安全含义

这里不应把重点放在如何实现攻击，而应关注防御结论：

1. **clean success rate 不足以做 checkpoint 验收**；
2. 文本输入属于控制面，应做 schema、来源和权限限制；
3. action 输出仍需要独立几何/力/安全 gate；
4. checkpoint、训练数据与微调数据都需要 provenance；
5. 上线前应加入 trigger-robust regression、异常动作模式和 prompt perturbation 测试。

### 传感器与实体实验

论文真实实验使用 ROKAE 6-DoF 机械臂、外部 RealSense D435 和 wrist RealSense D405，在 pick/place 类任务中测试 clean 与触发条件。这说明问题并不只存在于纯文本 Agent，而会直接进入视觉—语言—动作控制链。

### 鲁棒性、可复现性与风险

这是安全研究，不应把其结果直接解释成“所有 VLA 都已被攻破”。具体风险取决于模型来源、训练流程、prompt authority 和底层控制架构。

真正工程风险是：如果机器人把 VLA action 当成最高权限命令，任何隐藏行为都会直接转化为物理风险。相反，如果 VLA 只产生候选轨迹，后面还有 reachability、collision、force 和 task-state 验证，攻击面会显著缩小。

### 适合谁关注

VLA 产品团队、机器人模型供应链、安全评测、第三方 checkpoint 部署团队。

### 工程落地启发

将 VLA 部署验收拆成至少三层：

```text
Model / Data Provenance
        ↓
Prompt / Context Authority
        ↓
Action Safety & Task-State Gate
```

不要让“模型在 100 个正常任务里成功 95 次”成为唯一上线证据。

## 6. Pass the Bucket：没有中心调度，也能靠局部相遇形成异构机器人任务分区

**时间回补：arXiv v1 提交于 2026-08-27 13:09 UTC。** [论文](https://arxiv.org/abs/2608.27085)

### 为什么重要

很多多机器人系统依赖中心服务器持续计算任务分配和路径。如果网络中断、机器人数量变化或能力差异很大，中心调度可能成为瓶颈。

Pass the Bucket 研究一个极简问题：一群速度不同的机器人在一维受限空间合作运输，只能感知邻居/墙体的局部相遇，不共享全局时钟，也不依赖中心控制，是否仍能自动形成合理负载分区？

### 算法模块

基本 bucket-brigade 机制会因为异构速度和局部交互产生持续振荡。论文增加一个极简 token：机器人发生边界相遇后暂时减速，从而消除长期振荡，并使任务区间逐渐收敛到与各机器人速度近似成比例的分区。

系统只需要极少局部状态，理论与 event-driven simulation 都集中在“如何靠局部交互形成全局稳定负载平衡”。

### 动力学与系统假设

论文是受限一维任务模型，真实仓库二维/三维交通、交叉口、动态障碍和复杂避碰都不在当前结论范围内。

同时，“碰撞感知”在实际工业机器人中不能直接理解为允许物理碰撞。更安全的实现应把 collision event 替换成近距离 encounter、虚拟边界或局部通信事件。

### 鲁棒性与结果

事件驱动模拟显示，在机器人删除、位置抖动、速度扰动等条件下，系统能够重新收敛。其价值在于证明一类极简 local policy 可以拥有较强的自恢复特性。

### 可复现性与风险

目前主要是理论和仿真结果，没有真实多机器人实验。对一般仓储系统不能直接替代 MAPF/MAPD 调度器，但非常适合做局部负载分配、管道/长走廊接力或中心通信故障后的降级策略原型。

### 适合谁关注

异构 swarm、多机器人运输、长走廊/管道巡检、弱通信协同。

### 工程落地启发

多机器人系统可以同时拥有两层：正常情况下由中心调度优化全局效率；中心失联时，机器人切换到只依赖局部 peer observation 的低性能但可持续运行模式。**降级模式不必最优，但应该能自恢复。**

## 7. Zero-Shot Self-Orchestration：共享 Ledger 对部分 Coding Model 很有效，但并不是“多 Agent 必胜”

**时间回补：arXiv v1 提交于 2026-08-27 00:11 UTC。** [论文](https://arxiv.org/abs/2608.26480)

### 为什么重要

多 Agent Coding 的实验经常把模型、token budget、tool 调用、prompt 和角色数量一起改变，最后即使成绩提高，也很难知道究竟什么因素有效。

这项工作固定底模，只增加一个 manager-worker scaffold 与共享文件 workspace，在 9 个模型、LiveCodeBench 最新 100 个 hard problem 上比较 zero-shot self-orchestration 的真实收益。

### 系统结构

核心不是“多开几个聊天”，而是让任务状态落入共享持久文件：manager 负责分解、派工和汇总，worker 使用较短上下文解决子问题，结果通过 ledger/workspace 回写。

论文的 transcript analysis 指出两个反复出现的收益来源：

- context management：短 worker call + 共享 notes 降低长上下文截断；
- problem decomposition：将复杂问题拆成更容易验证的子任务。

### 结果与成本

结果高度依赖模型：Qwen3.8-27B 提升 **23.4 个百分点**，GPT-5.6-Luna 提升 **10.6 个百分点**，GPT-5.6-Terra 提升 **8.0 个百分点**；但某些模型收益接近 0，甚至为负。Manager 大约会把 token bill 放大到约 3 倍。

这说明“多 Agent”不是通用免费增益，必须按模型和任务实际 A/B。

### 是否适合真实研发流程

很适合长时 Coding 任务，但生产系统不应该把 ledger 只做成几份自由格式 Markdown。至少应绑定：

```text
repo_sha
current_plan
completed_tasks
failed_commands
evidence
owner
validation_status
```

并让真正的 verifier 使用仓库测试/CI，而不是只相信 worker 自己写的结论。

### 权限、安全与可验证性风险

Manager 和 worker 都应该默认在 sandbox 中运行；共享 ledger 是状态接口，不是权限提升接口。任何 worker 都不应该因为向 ledger 写入一句“已验证”就自动获得 deploy、push 或外部网络权限。

### 工程落地启发

如果已经有单 Agent Coding 流程，第一步不必复杂多 Agent 编排。先把长期状态从 prompt 迁到有 schema 的 artifact ledger，再比较是否真的减少重复搜索、上下文溢出和无效修复。

## 8. Safety Does Not Compose：Agent 每轮都“重新安全检查”仍然可能在长期循环里失效

**时间回补：v1 提交于 2026-08-27 13:52 UTC，v2 于 2026-08-28 08:52 UTC 更新。** [论文](https://arxiv.org/abs/2608.27141)

### 为什么重要

长期自主 Agent 已经不是一次 prompt → 一次 answer，而是循环执行：发现工作、规划、调工具、验证、保存状态，然后进入下一轮。

如果安全 monitor 每个 trajectory 开始时都清零，那么攻击或错误证据可以被分散到多个迭代里。每一轮单独看都很“正常”，组合起来却可能逐步越过原本不应越过的权限边界。

### 核心思想

论文给出一个重要分离结果：对于决定性证据被拆散在多个 iteration 的攻击，任何只看单 trajectory 的 monitor 都可能无法比随机判别更好；简单携带一个几何衰减的 risk score 也不够，因为耐心等待固定 cooldown 后风险会自动被“洗掉”。

作者提出 LoopHarness：在整个 autonomous loop 层维护**持久、非衰减的安全状态**，并让不可逆 commit 经过独立仲裁。论文还给出在特定检测与仲裁假设下，对 unauthorized irreversible action 数量的 horizon-independent 上界分析。

### 是否适合真实 Coding Agent

非常适合长期 Codex/Claude Code/OpenHands 类系统。真正需要跨轮持久的安全状态包括：

```text
已请求过的敏感资源
失败/拒绝历史
外部目标地址
写权限升级
secret access
删除 / deploy / send 等不可逆动作历史
```

这些状态不能因为任务重新规划、context compact 或新 session 就自动归零。

### 权限、安全与可验证性风险

LoopHarness 是安全架构研究，不是一个可以直接替代企业 IAM 的完整产品。真实系统仍然需要 OS/container 权限、secret manager、网络策略和人工确认。

最关键的架构要求是：**审计状态和授权器不能由同一个被审计 Agent 任意修改。** 否则“持久状态”只会变成另一个可被模型覆盖的文本文件。

### 工程落地启发

长期 Agent 建议明确分成三种状态：

```text
Task State       —— 可被 Agent 更新
Evidence State   —— 由工具结果产生，可审计
Safety State     —— 由独立 runtime 维护，Agent 只读
```

跨迭代安全从“每次都提醒模型要谨慎”升级为真正的系统状态机。

## 经典论文回顾

### ElasticFusion：2015 年就证明“地图本身”可以承担全局一致性，而不一定先维护一张 Pose Graph

**发表时间与历史位置：** Thomas Whelan、Stefan Leutenegger、Renato Salas Moreno、Ben Glocker、Andrew Davison 的《ElasticFusion: Dense SLAM Without A Pose Graph》发表于 **RSS 2015**。它是 dense RGB-D SLAM 的代表工作之一，也是 surfel map、frame-to-model tracking 与 deformation-based loop closure 路线的重要里程碑。[RSS 论文页](https://www.roboticsproceedings.org/rss11/p01.html) · [DOI](https://doi.org/10.15607/RSS.2015.XI.001) · [官方代码](https://github.com/mp3guy/ElasticFusion)

### 核心问题

很多 SLAM 系统将全局一致性理解为：关键帧形成 pose graph，检测回环以后优化相机位姿，再根据新位姿重建地图。

ElasticFusion 选择另一条路线：维护一个长期活动的 dense surfel model，当前 RGB-D frame 直接对地图做 frame-to-model tracking，新深度不断融合进 surfel；发现局部/全局回环以后，不先显式优化整张 pose graph，而是通过 **non-rigid map deformation** 直接把表面地图拉回一致状态。

### 算法模块与关键思想

经典管线可以概括为：

```text
RGB-D Frame
    ↓
Dense Frame-to-Model Tracking
    ↓
Active Surfel Map
    ↓
Windowed Surfel Fusion
    ↓
Local Model-to-Model Loop Closure
    ↓
Global Appearance Loop Closure
    ↓
Deformation Graph
    ↓
Non-Rigid Map Correction
```

Surfel 不只是一个 3D 点，而是局部表面元素，通常包含位置、法向、颜色、置信度、时间等属性。这使 tracking、fusion 和可视化共享同一个结构化地图表示。

### 传感器与动力学假设

原始系统针对室内 RGB-D camera，依赖足够稳定的 projective data association。快速运动、motion blur、RGB/Depth 不同步和 rolling shutter 都会直接破坏 dense tracking。

因此 ElasticFusion 的地图更新机制不能直接照搬到 MID360/16 线 LiDAR，但“地图是带局部几何统计和生命周期的主动状态”这一思想完全可以迁移。

### 当年为什么重要

它证明实时 dense SLAM 不一定只能是“稀疏轨迹 + 离线 dense reconstruction”。地图本身可以在线更新、用于跟踪，并在回环后通过 deformation 保持全局一致。

### 今天仍然有效的思想

1. **Frame-to-model 通常比 frame-to-frame 更稳定。** 当前观测应该对一个经过累积、去噪的局部地图配准，而不是只对上一帧。
2. **地图元素应该有生命周期。** 活跃/非活跃 surfel、置信度和更新时间比无限保存所有原始点更有工程价值。
3. **回环不仅要改 pose，也必须传播到地图表示。** 如果轨迹优化了而 dense map/semantic map 没同步纠正，系统仍然不一致。
4. **地图表示应该直接服务 tracking。** 地图不是最后的可视化副产品。

### 已被后续替代的部分

原始 RGB-D projective tracking、OpenGL/CUDA 工程栈和 fern-based place recognition 已明显老化。现代系统通常会加入 IMU、学习特征、submap/voxel hash、Gaussian/surfel statistics、显式 factor graph 和更强的 place recognition。

当前官方仓库也明确要求较旧式 GPU/OpenGL/OpenNI 依赖，并采用**仅限非商业使用**的授权，闭源产品不能直接把代码拿来商用。

### 公开代码、数据与可复现性

官方代码仍可获取，也提供示例数据；作为理解 dense surfel SLAM 很有价值。但如果目标是现代产品实现，更建议复现其“active map + loop-induced map correction”思想，而不是复刻整套旧 GPU pipeline。

### 对当前 SLAM 工程的重新解读

对 LiDAR / 多 LiDAR 系统，可以把 ElasticFusion 的思想转成：

```text
去畸变后的 LiDAR
       ↓
Voxel / Surfel Local Map
position + normal + covariance + age + support
       ↓
Frame-to-Map Registration
       ↓
Loop / RTK / Global Factor Correction
       ↓
Submap / Map Element Correction
       ↓
同步更新 Semantic / Traversability Layer
```

尤其当系统同时维护几何地图、语义对象、可通行地图和长期变化历史时，必须明确规定**全局位姿修正如何传播到每一层地图**。这正是 ElasticFusion 在 2015 年已经逼迫 dense SLAM 面对的问题，也是今天 3DGS、Gaussian map 和长期语义地图仍然必须解决的问题。

## 今日结论

今天没有强行从最近列表里找一个新的 LIO 名字凑 SLAM 条目，因为此前几天已经连续覆盖了 LF-GICP、Super Odometry 2.0、多 LiDAR 标定与协同 SLAM。本期真正新的工程信号更多集中在**部分可观测规划、控制时间尺度分层、多机器人资源状态和长期 Agent 安全状态**。

第一，ESRP 与 Instruct-to-Act 实际上都在说明：**高层智能不应该假装自己拥有完整、实时的世界。** ESRP 要求机器人主动建立被遮挡的场景状态；Instruct-to-Act 则接受 VLM 本来就慢，让快速 controller 在两次高层指令之间保持闭环。将“看不全”和“算不快”当成架构约束，比假装 Foundation Model 可以同步解决一切更接近真实部署。

第二，软体夹爪与多机器人调度都在强调**隐藏状态的生命周期**。软材料的内部状态随温度和时间变化；仓库 Haven 从“空闲”变成“正在释放”也不是一个瞬时布尔值。机器人系统越复杂，越需要把这种跨时间状态建模为一等对象。

第三，TrapVLA 与 Safety Does Not Compose 把安全问题从模型输出提升到了系统边界。VLA 的正常成功率无法证明没有隐藏失败模式；Coding Agent 的单轮安全 monitor 也无法保证多轮组合以后仍然安全。真实产品需要 provenance、持久安全状态和独立 execution gate，而不是把全部希望押在“模型会自觉遵守规则”。

第四，Zero-Shot Self-Orchestration 与 Pass the Bucket 从两个完全不同的系统给出相似经验：**共享状态/局部规则有时比继续扩大中央控制器更有效，但收益必须实测。** 前者对不同 coding model 的收益差异很大，后者目前仍主要是仿真。不要把漂亮的系统范式提前当成普适规律。

## 最值得深入研究或尝试复现的方向

1. **移动操作的 ESRP-lite belief layer。** 在现有地图上只加对象级 `pose / covariance / visibility / target / last_seen`，让 planner 在对象状态不确定时可以主动请求“去某个视角重新观察”，先验证主动感知是否能降低长任务中 world-state 错误。

2. **VLM Planner → 高频 Controller 的多速率接口。** 给高层指令增加 `precondition / valid_until / priority / skill_id`，测 VLM 延迟从 100 ms 增加到数秒时，低层任务成功率和 stale-instruction 率如何变化；低层保持独立安全控制。

3. **VLA 上线增加隐藏失败回归集。** 不研究攻击实现，只把 prompt 变体、checkpoint 版本、异常 action residual、几何/力约束违规加入 release gate；任何模型升级都同时跑 clean success 与 adversarial robustness regression。

4. **Coding Agent 建立不可衰减安全 Ledger。** Task ledger 可以由 Agent 写，但 Safety ledger 由 runtime 独立维护；`push / deploy / delete / send / secret access` 等不可逆动作必须读取跨迭代安全历史再授权，不能因为 session 重置自动清零。

## 参考资料

1. [ESRP: Embodied Scene Rearrangement Planning](https://arxiv.org/abs/2608.27371) · [项目页](https://pie-lab.cn/ESRP/) · [代码](https://github.com/BIT-PIE/ESRP)
2. [Relaxation-Aware Multimodal Sensing of Soft Gripper](https://arxiv.org/abs/2608.26622)
3. [Dynamic Haven Selection / A-sharp](https://arxiv.org/abs/2608.26939)
4. [Decoupling Planning and Control for Instructable Agents](https://arxiv.org/abs/2608.26788) · [项目页](https://zinengtang.github.io/instruct-to-act/)
5. [TrapVLA](https://arxiv.org/abs/2608.26578) · [项目页](https://john-liua.github.io/TrapVLA/)
6. [Pass the Bucket](https://arxiv.org/abs/2608.27085)
7. [Zero-Shot Self-Orchestration with Ledger-Based Control](https://arxiv.org/abs/2608.26480)
8. [Safety Does Not Compose / LoopHarness](https://arxiv.org/abs/2608.27141)
9. [ElasticFusion: Dense SLAM Without A Pose Graph](https://www.roboticsproceedings.org/rss11/p01.html) · [官方代码](https://github.com/mp3guy/ElasticFusion) · [DOI](https://doi.org/10.15607/RSS.2015.XI.001)
