---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-18"
date: 2026-09-18 09:00:00 +0800
description: "最新机器人公开批次继续向可执行系统靠拢：VLA 推理缓存、级联软碰撞规划、多机器人 TAMP、动态环境 kinodynamic planning、语言驱动无人机 MPPI 与人形全身控制成为重点，同时 AI Coding 暴露插件供应链与多 Agent 协作成本问题。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-18

## 摘要

截至 2026-09-18 早间，arXiv `cs.RO/recent` 的最新公开批次仍是 **2026-09-17**，该批次共有 113 条 Robotics entries。昨天的简报已经覆盖了 SEAM、SOL-SLAM、地下 VIO 退化评测、ElastiQP、Adaptive-MHE、VLA-ULAP 等条目，所以今天不重复，而是继续从同一最新批次中向下筛选此前未覆盖、且工程价值较高的工作。本文 7 条主动态的 `v1` 都提交于 2026-09-16，因此统一标为“时间回补”，不伪装成 9 月 18 日新论文。（[arXiv Robotics Recent](https://arxiv.org/list/cs.RO/recent)）

今天最明显的趋势不是某个单点模型参数变大，而是**系统接口越来越重要**：rMuscle 从跨执行相似性里做 VLA 缓存；CaSCo 把“碰到什么、会连锁撞到什么”写进规划状态；多机器人 TAMP 重新审视不同任务转移对应不同维度配置空间的理论覆盖；VLM-MPPI 和 KINO 都把慢速语义推理与高速控制之间放入一个有限、可验证的中间接口；PASSAGE 则证明人形感知运动能力仍然强烈受高质量、场景对齐数据规模影响。

对现有 SLAM/导航工程尤其值得注意的是：最新批次中的 SEAM、SOL-SLAM、VIO failure benchmark 已在昨天展开，今天没有重复报道。与其为了“每天必须有一篇 SLAM”而重复旧工作，本期把重点放到**地图之后如何规划、控制与执行**，这更符合强制去重规则。

## 1. rMuscle：VLA 推理优化开始利用“机器人重复劳动”本身，而不是只做通用模型压缩

**时间回补；v1 提交于 2026-09-16，进入 9 月 17 日最新公开批次。**（[论文](https://arxiv.org/abs/2609.19104)）

### 为什么重要

工厂和固定工位是具身模型最现实的早期落地场景之一，而这类任务恰恰高度重复。传统 VLA 加速常见路线是量化、蒸馏、减少视觉 token、降低 diffusion step 或更换轻量 backbone，但这些方法基本把每一次执行都当成全新的输入。rMuscle 的出发点不同：**机器人反复完成相似任务时，不只图像和动作相似，模型内部状态也会重复。**

这使“缓存”从 LLM 的 prefix cache 类比进入 VLA：系统不是单纯缓存输入，而是针对 VLA 两个不同瓶颈分别重用计算结果。

### 算法模块

rMuscle 使用双阶段缓存：

```text
Repeated robot executions
        ↓
Context Cache
  复用视觉 token 的中间输出
        ↓
Action-generation stage
        ↓
Action Cache
  复用神经元激活模式，减少权重访问
        ↓
Action output
```

为了避免缓存本身变成大内存和高检索开销，论文还加入在线 cache recomputation、滑动窗口检索，以及在连续去噪步骤之间共享 mask。

### 实时性、鲁棒性与可复现性

论文报告在 RTX 4090 与 Jetson Thor 上、跨 LIBERO、RoboTwin 和真实操作任务取得 **1.29–1.42×** 推理加速，并声称真实机器人成功率保持原水平。这个结果的价值在于它包含桌面 GPU 和边缘平台，而不是只在服务器卡上测 kernel throughput。

但需要注意，缓存收益天然依赖**跨执行相似性**。固定工位装配、分拣、上下料很合适；开放家庭环境、移动机器人持续换视角和换目标时，命中率可能明显下降。因此工程评测不应只看平均延迟，还要同时记录 cache hit ratio、误复用率、P95 latency 和任务成功率。

### 工程风险

缓存对具身系统最大的风险不是“缓存没命中”，而是**过期状态被错误复用**。如果物体位置变化很小但足以影响接触，视觉特征仍然相似，缓存可能让模型错过关键差异。安全实现最好保留置信门槛，并对接触前、目标切换、异常检测等阶段强制刷新。

### 适合谁关注

工业操作机器人、Jetson/边缘 VLA 部署、固定工位具身模型、需要降低动作延迟和显存带宽压力的团队。

### 工程落地启发

即使不复现整套 rMuscle，也值得在自己的 VLA pipeline 中先做一件事：**记录连续任务之间各层特征相似度与动作相似度**。如果固定工位上很多层长期高度相似，再决定缓存哪一层，比一开始就盲目做模型剪枝更有针对性。

## 2. CaSCo：碰撞规划不再只有“撞 / 不撞”，而是开始计算物体语义风险与级联后果

**时间回补；v1 提交于 2026-09-16。**（[论文](https://arxiv.org/abs/2609.18910)）

### 为什么重要

传统 motion planning 往往把碰撞建模成硬约束，但现实里机器人轻擦纸箱和碰到玻璃杯的后果完全不同，更麻烦的是机器人推倒 A 之后，A 可能继续撞倒 B。CaSCo 把这个问题称为 **cascade-aware soft collision**：规划代价不仅取决于机器人直接碰到谁，还取决于碰撞后场景如何演化。

### 算法模块

系统首先利用 VLM 或语言模型为场景物体赋予语义风险，然后用物理模拟器预测候选动作造成的直接与间接位移。规划状态不再只有机器人 configuration，而是扩展为：

```text
(robot state,
 predicted object arrangement,
 set of already-incurred risky objects)
```

目标函数统计被直接或级联移动的**唯一物体**的总风险，避免同一物体被重复计费。作者进一步构造了具有 admissible / consistent 性质的 cascade-relaxed heuristic，并通过缓存和剪枝降低搜索开销。

### 假设与鲁棒性

这个方法隐含两个强假设：物体语义风险能被合理标定，以及物理模拟对“轻推之后会发生什么”足够可信。前者可以人工规则兜底，后者更难，因为摩擦、质心、支撑关系、软物体和包装材料都会带来 sim-real gap。

因此真正落地时，最适合把 CaSCo 当成**风险排序器**，而不是把模拟结果视为严格安全保证。对玻璃、化学品、电气设备等高风险对象仍应保留硬禁碰区域。

### 实时性与可复现性

论文在 cluttered manipulation 场景并包含真实机器人实验。相比普通几何 roadmap，它需要额外 physics rollout，因此搜索成本更高；但缓存 object arrangement 与风险集合正是在避免重复物理计算。

### 工程风险

如果 VLM 把一个“看起来普通但实际昂贵”的工件判低风险，规划器会主动利用软碰撞穿过去。生产系统最好把风险来源拆成：资产数据库硬标签、规则层、视觉语义估计三层，VLM 只能补充未知对象，不能覆盖硬规则。

### 适合谁关注

仓储拣选、杂乱桌面操作、家庭机器人、工业柔性上下料，以及需要在“完全无碰撞”和“可接受轻接触”之间做权衡的系统。

### 工程落地启发

现有 MoveIt / sampling planner 可以先做简化版：给 collision object 增加风险等级，把低风险物体从 hard constraint 改为高代价 soft constraint，再逐步加入被推物体的二次碰撞预测。这样能先验证“语义软碰撞”是否真的改善任务成功率，再投入复杂物理模拟。

## 3. Asymptotically Optimal Multi-Robot TAMP：多机器人最优性难点不只是维度高，而是每种任务转移的“参与机器人集合”不同

**时间回补；v1 提交于 2026-09-16。**（[论文](https://arxiv.org/abs/2609.18813)）

### 为什么重要

多机器人 Task and Motion Planning 同时面对离散任务顺序和连续碰撞自由运动。简单做法是把所有机器人状态拼成一个巨大 composite configuration space，但当某个任务转移只涉及机器人 A，另一个转移涉及 A+B+C 时，不同 transition 实际落在不同维度的约束集合上。

这篇工作的重要点在于它从理论上指出：要得到全局渐近最优，不能只保证每个 mode 内的 motion planner 越来越好，还必须保证**相关任务转移持续获得足够采样覆盖**。

### 算法结构

作者给出全局渐近最优的充分条件，并据此设计 planner：

```text
Individual robot roadmaps 持续增长
            ↓
Implicit tensor-product search
            ↓
Task-mode / transition reasoning
            ↓
Conditional transition sampling
            ↓
Lazy collision checking
            ↓
Mode-level + solution-level guidance
```

关键是避免显式构造巨大的联合 roadmap，而是保留单机器人 roadmap，在需要时通过隐式 tensor product 组合。

### 假设、实时性与鲁棒性

这里讨论的是 asymptotic guarantee，不等于有限时间内一定快。工程上真正决定速度的仍然是 transition sampler、碰撞检测、任务模式数量与机器人间耦合程度。对于紧耦合搬运、交接、双机器人协同装配，低维独立规划无法完全替代联合空间搜索。

### 工程风险

多机器人规划最容易出现“理论上完备、线上超时”。如果系统最终只给 planner 200 ms 或 2 s，渐近性质并不能救场。因此应把 anytime 行为、首次可行解时间、最优性 gap 和冲突重规划次数列为主要指标。

### 适合谁关注

多机械臂、移动操作机器人协同、仓储 AMR + 机械臂、实验室自动化、多机器人装配。

### 工程落地启发

如果现有系统使用 centralized TAMP，可以先检查任务图中的 transition 到底涉及哪些机器人。很多 transition 实际只需要 1–2 台机器人，把所有机器人一直绑在一个高维状态里是浪费。按 transition 的参与集合动态构造联合搜索空间，往往比先上更复杂的学习 planner 更直接。

## 4. DynoFluxBench：动态障碍中的 kinodynamic planning 终于开始有专门 benchmark，而不是各论文各自画一套场景

**时间回补；v1 提交于 2026-09-16。**（[论文](https://arxiv.org/abs/2609.18549)，[项目页](https://dynofluxbench.github.io/)）

### 为什么重要

静态路径规划 benchmark 很成熟，但机器人一旦同时受到动力学约束和移动障碍约束，就会进入 space-time kinodynamic planning。不同论文常用不同障碍轨迹、到达时限和动力学模型，很难判断算法到底强在哪里。

DynoFluxBench 专门针对**已知动态环境 + kinodynamic feasibility + 不限制到达时间**建立统一评测，并提供三种新的 baseline：ST-Db-RRT、ST-GBRRT 和 KIST。

### 算法对比

三种 planner 覆盖不同搜索范式：ST-Db-RRT 使用 trajectory optimization 产生 discontinuity-bounded motion primitive；KIST 与 ST-GBRRT 则维护 kinodynamically feasible tree，但采用不同的 heuristic guidance。

作者还分析了这些方法在动态环境下的 probabilistic completeness。实验中，ST-Db-RRT 的首次解在部分场景可快到 **32×**，而当 trajectory optimization 脆弱时，KIST / ST-GBRRT 仍有价值。

### 为什么这个 benchmark 对工程更有价值

动态环境 planner 最容易被“平均路径长度”掩盖问题。真实系统至少要同时看：

```text
first-solution latency
success rate under moving obstacles
trajectory dynamic feasibility
minimum clearance over time
control effort
replanning sensitivity
```

而且必须区分“规划器没找到解”和“低层控制跟不上规划轨迹”。

### 工程风险

论文假设动态环境已知，这与真实机器人在线预测行人 / 车辆未来轨迹仍有距离。把 benchmark 成绩直接外推到 perception uncertainty 场景并不合理。下一步工程验证应人为加入 obstacle prediction error 与 tracking delay。

### 适合谁关注

无人机动态避障、高速移动机器人、自动驾驶局部规划、kinodynamic RRT / sampling planner 研究者。

### 工程落地启发

如果正在比较 MPPI、RRT 系和轨迹优化，本质上也需要一个类似 DynoFluxBench 的内部 harness：固定场景生成器、动态障碍脚本、动力学模型和同一组评价指标。先把 benchmark 建起来，往往比继续调一个 planner 的参数更有长期价值。

## 5. VLM-MPPI：让 VLM 只选“行为模式”，高速轨迹仍交给 20 Hz MPPI

**时间回补；v1 提交于 2026-09-16。**（[论文](https://arxiv.org/abs/2609.18451)）

### 为什么重要

对于室内无人机，直接让大 VLM 输出连续控制量既慢又难做动力学安全约束。VLM-MPPI 采用更工程化的分层：同时运行 6 个带不同行为偏置的 MPPI，让 VLM 只在这些**已经动态可行的候选轨迹**之间做语义选择。

例如“从柜子左侧绕过”“保持离人更远”“从狭窄开口穿过”等自然语言意图，不需要让语言模型理解推力与角速度，而是让它选择一个行为模式。

### 算法模块

```text
LiDAR / state estimate
        ↓
6× behavior-conditioned MPPI
  各自使用不同 guiding cost / sampling bias
        ↓
6 条有意区分的 3D trajectory candidates
        ↓
投影到机载第一视角 RGB
        ↓
VLM + natural-language prompt
        ↓
选择 candidate index（异步）
        ↓
20 Hz MPPI replanning
        ↓
PID low-level tracking
```

这比“对同一个 MPPI 多采样几次”更关键，因为不同 planner 被设计成收敛到不同的 behavioral mean，候选具有明确语义差异。

### 传感器与实时性

真实四旋翼使用 LiDAR + RGB；MPPI 以 20 Hz 重规划，低层由 PID 跟踪，而 VLM 异步运行，因此慢模型不会直接阻塞控制环。论文在 Isaac Sim 和真机场景中报告评测任务 100% 成功，但这个数字应严格理解为作者所测场景，不代表开放环境泛化率。

### 鲁棒性与风险

最大的系统风险是**候选集缺失**：如果 6 个 MPPI 都没有生成真正满足语言意图或安全要求的轨迹，VLM 再聪明也只能在坏选项里挑一个。因此 VLM 输出必须允许 `none-of-the-above`，并把低层安全约束与急停独立于语言层。

另一个风险是视觉投影可能把 3D clearance 表达得不够清楚。对于狭窄空间，无人机自身尺寸、桨叶安全半径最好直接叠加到可视化候选上。

### 适合谁关注

室内无人机、语义导航、VLM + 传统规划混合系统、需要把自然语言接入现有 PX4 / MPC / MPPI 栈的团队。

### 工程落地启发

这是一种很值得复制的接口设计：**VLM 不产生控制，VLM 选择受约束的行为。** 对已有无人机系统，可以先保留定位、避障和控制全部不变，只增加 3–5 套 cost profile，再让语义层选择 profile / trajectory ID，风险远低于端到端替换控制器。

## 6. KINO：人形机器人把 VLM 与 Whole-Body RL 连接起来的关键，不一定是更多 token，而是“动作关键帧接口”

**时间回补；v1 提交于 2026-09-16。**（[论文](https://arxiv.org/abs/2609.18869)）

### 为什么重要

高层 VLM 适合做任务与场景推理，低层 Whole-Body Policy 适合做高频运动控制，但两者之间经常缺少稳定接口。若高层直接输出关节动作，语义模型负担太重；若只输出“抓取箱子”这样的符号技能，低层又缺少足够几何约束。

KINO 把 **motion keyframe** 作为中间语言：一个 keyframe 指定目标全身 pose，必要时还包含 object pose。

### 算法模块

VLM 根据语言指令、场景观测和执行反馈，从预定义 keyframe library 中选择下一关键帧；系统根据当前物体位置和尺寸对 keyframe retarget；随后 keyframe-conditioned whole-body RL policy 产生关节动作。

论文还提出 saliency-based keyframe sampling，用于低层 policy 训练。在稀疏 VLM keyframe 条件下，作者报告端到端成功率由 **44% 提升到 92%**。

### 模型假设与泛化

KINO 的代价是需要预定义 keyframe library，因此不是“任意新任务零先验”。但这恰恰带来工程可控性：高层搜索空间有限，中间状态可视化，失败可以定位到“选错关键帧、retarget 错、还是低层执行失败”。

论文在仿真和 Unitree G1 上验证 pickup、transport、placement，包括单手与双手操作，并展示超出训练参考位置的 placement 泛化。

### 实时性与鲁棒性

低层控制不依赖 VLM 高频输出，因此更适合真实人形。真正部署时建议给每个 keyframe 配置 entry condition、completion detector、timeout 和 recovery policy；否则高层选对了关键帧，低层因接触失败卡住，系统仍无法闭环。

### 工程风险

keyframe library 会逐渐膨胀，若没有语义分类和版本管理，最终会变成不可维护的 motion template 仓库。此外 retarget 只处理几何变化并不自动解决动力学变化，例如重物、摩擦、手部接触不稳定。

### 适合谁关注

人形机器人、移动操作、VLM planner、Whole-Body RL、需要可解释高低层接口的工业具身系统。

### 工程落地启发

对已有机器人，完全可以把“关键帧”推广成统一 task-space contract：`base pose + end-effector pose + object relation + tolerance + completion condition`。高层模型只负责生成 / 选择 contract，低层 MPC、QP 或 RL 去满足它。这比让 VLM 直接输出底层 action 更容易验证。

## 7. PASSAGE：人形穿越复杂障碍的瓶颈仍然很“朴素”——场景对齐运动数据规模直接决定行为覆盖

**时间回补；v1 提交于 2026-09-16。**（[论文](https://arxiv.org/abs/2609.18732)）

### 为什么重要

人形机器人可以跨、侧身、下蹲穿越障碍，但很多方法为每种行为单独设计 RL objective 或人工 motion library。PASSAGE 尝试用一个 perception-conditioned planner + tracker 统一选择和组合这些动作，而且把重点放在**scene-aligned human motion data scaling**。

### 数据与模型结构

作者通过 VR 和惯性动作捕捉，收集 **100 小时、1,500 个 cluttered scenes** 的场景对齐人体运动。系统由两层组成：

```text
motion history
+ local destination
+ robot-centric multi-layer elevation map
        ↓
conditional flow-matching planner
        ↓
short-horizon motion references @ 6.25 Hz
        ↓
perceptive whole-body tracker @ 50 Hz
        ↓
robot joints
```

real-time chunking 用于提高 chunk 间一致性，planner 还在冻结 tracker 后进行 RL post-training。

### 数据规模结果

论文在三个独立训练 seed 上报告：场景对齐数据由 6 h 扩到 100 h 后，held-out scene 的平均 contact-free success 从 **48.1% 提升到 68.9%**；再加入验证过的 scene augmentation 后达到 **70.3%**。

这组结果比单纯“更大模型更好”更有启发：对复杂运动，**行为覆盖和场景分布覆盖**仍是最直接的性能杠杆。

### 传感器、实时性与真机

完整系统使用机载 3D LiDAR、在线 occupancy mapping、Jetson AGX Orin，规划 6.25 Hz、控制 50 Hz；作者在 50 个未见真实布局中测试，不依赖预建地图或 offboard computation。

这类配置很接近可部署的人形导航系统：局部几何地图仍然是安全与可解释的感知接口，生成式 planner 负责行为组合，而高频 tracker 负责动力学执行。

### 工程风险

100 小时 scene-aligned motion 的采集成本并不低，而且人体动作到机器人本体仍存在 retarget / feasibility gap。论文的成功不意味着“再录更多 mocap 就能无限增长”，数据分布、障碍几何覆盖和 tracker 能力都会成为上限。

### 适合谁关注

人形导航、感知运动控制、LiDAR + whole-body policy、sim-to-real、数据驱动 traversal。

### 工程落地启发

对轮足 / 四足机器人也有同样启发：不要只记录“地形标签”，而要把**场景几何 + 实际成功运动轨迹**绑定存储。后续无论训练 diffusion / flow planner 还是做 retrieval-based policy，都比纯动作数据更有价值。

## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### A. Plugin4Shell：把 Agent 插件 / Skill 当作“有开发者权限的可执行供应链”，不能只靠 SHA pinning

AIR Security 在 2026-09-17 公布 Plugin4Shell，研究者报告同一类插件版本解析问题影响 Claude Code、Codex、GitHub Copilot 与 Gemini CLI 等 coding agent。核心问题不是提示词注入，而是插件安装 / 更新链路：客户端请求 checkout 被 pin 的 commit 后，没有再验证工作区最终 `HEAD` 是否真的等于该 commit，攻击者可利用 ref 名称解析歧义绕过 pinning。研究文章还给出了厂商披露与修复状态。（[原始研究](https://www.air.security/blog-posts/plugin4shell)）

**今天可做的技巧：**把 `skills/plugins/MCP` 纳入软件供应链清单；禁止自动信任新插件；升级已修复的 Agent 版本；对自研插件管理器在 checkout 后增加“解析实际 HEAD 并与期望 SHA 精确比较”的断言；高权限 Agent 使用 allowlist 和最小权限工作目录。

**为什么值得学：**Agent 插件不是普通编辑器主题，它可能继承 shell、仓库、凭据与内部服务权限。一旦插件更新链被攻破，攻击者拿到的是 Agent 已经拥有的权限。

**风险 / 边界：**这是一家安全厂商发布的研究，涉及具体产品受影响版本与修复状态，团队应结合自己当前安装版本再次查看对应厂商公告。供应链扫描也不能替代运行时权限隔离。

### B. 多 Agent 不是越多越好：把“协调税”当成显式成本，独立子任务完成后一次性回报

2026-09-17 的一篇开发者报道汇总了 Codex 开发者 Eric Provencher 对 Agent swarm 的实践观察：并行子 Agent 太多时，常出现重复检索、重复验证、彼此不信任又重新检查的情况，token 消耗快速上升，而质量没有同比提升；他把这称为 **coordination tax**。报道中提到“超过两个往往开始浪费”应理解为个人工程经验，而不是受控 benchmark。（[报道](https://the-decoder.com/ai-agent-swarms-are-a-massive-waste-of-tokens-with-zero-quality-gain-says-openai-codex-developer/)）

**今天可做的技巧：**默认主 Agent + 1–2 个真正独立的子任务；每个子 Agent 在启动时拿到明确输入、输出格式和验收条件；运行期间不轮询彼此状态，完成后一次性把结果和证据交回主 Agent；只有当任务能清晰分区、工具资源互不冲突时才继续扩并发。

**适用场景：**大型仓库分析、并行测试 / 文档 / 安全审查、研究资料搜集、多个互不依赖模块的实现。

**风险 / 边界：**并发数不是固定魔法数字。对于真正独立的 20 个数据分片，更多 Agent 可能很合理；问题在于把强依赖、共享上下文的推理任务机械拆成 swarm。应该记录每个子任务的 token、工具调用、重复文件读取和最终被采用的产出比例，再决定是否加并发。

## 经典论文回顾

### A Unified Approach for Motion and Force Control of Robot Manipulators: The Operational Space Formulation（Oussama Khatib，1987）

**发表位置：**IEEE Journal on Robotics and Automation, Vol. RA-3, No. 1, 43–53, February 1987。（[Stanford Robotics Lab](https://khatib.stanford.edu/publications.html)，[论文 PDF](https://khatib.stanford.edu/publications/pdfs/Khatib_1987_RA.pdf)，[DOI](https://doi.org/10.1109/JRA.1987.1087068)）

### 核心问题

传统关节空间控制直接围绕 `q, q_dot, tau` 工作，但机器人任务通常表达为“末端到哪里、沿哪个方向施多大力、冗余关节怎么安排”。Operational Space Formulation 的关键转变是：**直接在任务空间描述末端的动力学，并构造与机器人真实惯量一致的任务空间控制。**

### 数学直觉

关节空间动力学可写为：

```text
M(q) q_ddot + h(q, q_dot) = tau
```

末端速度满足 `x_dot = J(q) q_dot`。Operational Space 将动力学投影到任务空间，得到任务空间等效惯量：

```text
Lambda(q) = (J M^-1 J^T)^-1
```

并构造 dynamically consistent generalized inverse：

```text
J_bar = M^-1 J^T Lambda
```

由此可以把主任务控制在 task space 中，同时利用 null space 处理冗余自由度。现代写法常用：

```text
tau = J^T F_task + N^T tau_null
```

其中 `N` 用于隔离不会破坏主任务的冗余动作。核心思想不是记住某个公式，而是**任务空间优先级必须考虑机器人动力学，而不是只做普通 Moore-Penrose 伪逆。**

### 当年为什么重要

这篇工作把 motion control、force control、冗余机器人和奇异位形处理放进统一动力学框架。对于机械臂而言，这意味着“控制末端行为”不再只是把笛卡尔误差通过 Jacobian 变成关节误差，而是可以显式描述末端惯量、力与约束方向。

### 今天仍在使用的思想

今天 humanoid whole-body control、mobile manipulation、operational-space QP、task hierarchy、null-space posture control 仍然大量继承这些抽象。KINO 这类高层关键帧接口最终也需要某种 task-space / whole-body execution 层；PASSAGE 的 tracker 即使由 RL 学得，其工程接口依旧经常落到 base、足端、手端、质心等 task-space quantity 上。

### 哪些部分已被后续方法增强

经典 Operational Space Control 并不直接解决现代人形机器人的多接触切换、摩擦锥、关节 / 力矩 / 接触力不等式、碰撞约束与状态估计不确定性。今天更常见的是 Whole-Body QP / HQP、inverse dynamics optimization、MPC、CBF、安全过滤器以及学习策略与模型控制混合。

换句话说，现代方法不是抛弃 operational space，而是把它的 task-space 结构塞进更强的约束优化框架。

### 可复现性与现在怎么做

最容易的复现不是从人形开始，而是 7-DoF Franka：

1. 用 Pinocchio / MuJoCo / Drake 得到 `M(q)` 与 `J(q)`；
2. 实现 task-space inertia `Lambda` 与 dynamically consistent inverse；
3. 主任务设末端 6D pose，null-space 任务设关节姿态；
4. 与普通 Jacobian pseudoinverse controller 对比；
5. 特别测试接近奇异位形、负载变化和快速方向切换时的关节力矩与 task error。

真正理解这篇经典论文之后，再看今天的 Whole-Body MPC / QP / RL，会更容易分辨“哪些只是优化器换了，哪些真的改变了任务接口”。

## 今日结论

今天最重要的共同线索可以概括成一句话：**复杂机器人系统正在把不确定的大模型能力压缩到更小、更稳定、更可验证的接口里。**

rMuscle 利用重复执行构造可控缓存；VLM-MPPI 让 VLM 只选轨迹候选；KINO 让 VLM 只选关键帧；PASSAGE 把生成式 planner 与 50 Hz tracker 分层；多机器人 TAMP 则把联合空间按 task transition 的参与机器人集合重新结构化。它们都不是“一个模型端到端全做”，而是在计算预算、动力学与可验证性之间重新划边界。

另一条同样重要的工程信号来自 AI Coding：Plugin4Shell 说明 Agent 的插件生态已经是软件供应链问题，而多 Agent coordination tax 则提醒团队，Agent 数量本身不是产能指标。**权限边界、验证证据、重复工作率与单位有效产出的 token 成本**，正在成为和模型能力同样重要的系统指标。

## 最值得深入研究或尝试复现的方向

**第一优先：复现 VLM-MPPI 的“语义选择受约束候选”架构。** 对已有无人机平台风险最低：保留 LiDAR 定位 / 避障与低层控制，先并行生成 3–6 条具有明确行为差异的轨迹，再让 VLM 只选择 ID。特别适合室内配电室、走廊这类语义要求明确但安全边界严格的场景。

**第二优先：给 VLA / 重复工位任务做 feature-cache profiling。** 不必立刻实现 rMuscle，只需记录不同执行之间各层 activation similarity、命中率、延迟和动作误差，就能判断固定工位是否值得做跨执行缓存。

**第三优先：建立动态障碍 kinodynamic planner 内部 benchmark。** 参考 DynoFluxBench，把 MPPI、RRT/kinodynamic tree、trajectory optimization 放到同一组动态障碍脚本和动力学模型下，统一记录首次解延迟、成功率、最小时空 clearance 和低层可跟踪性。

**第四优先：Coding Agent 插件链做一次供应链审计。** 列出实际安装的 skills/plugins/MCP、来源 repo、权限、自动更新行为与 pinning 验证方式；对 checkout 后没有验证实际 commit 的链路补硬断言，并尽量把高权限工具放进 sandbox。

## 参考资料

- [arXiv Robotics Recent](https://arxiv.org/list/cs.RO/recent)
- [rMuscle: Robotic Muscle Memory for Efficient Vision-Language-Action Model Inference](https://arxiv.org/abs/2609.19104)
- [CaSCo: Cascade-Aware Soft-Collision Motion Planning](https://arxiv.org/abs/2609.18910)
- [Asymptotically Optimal Multi-Robot Task and Motion Planning](https://arxiv.org/abs/2609.18813)
- [DynoFluxBench: Benchmarking Kinodynamic Space-Time Planners in Dynamic Environments](https://arxiv.org/abs/2609.18549)
- [DynoFluxBench Project](https://dynofluxbench.github.io/)
- [VLM-MPPI: Grounding Natural Language in Behaviorally Diverse Trajectories for Aerial Navigation](https://arxiv.org/abs/2609.18451)
- [KINO: A Keyframe Interface for VLM Planning and Whole-Body Control in Humanoid Loco-Manipulation](https://arxiv.org/abs/2609.18869)
- [PASSAGE: Scaling Scene-Aligned Motion Learning for Perceptive Humanoid Traversal in Cluttered Environments](https://arxiv.org/abs/2609.18732)
- [AIR Security: Plugin4Shell](https://www.air.security/blog-posts/plugin4shell)
- [The Decoder: AI agent swarms and coordination tax](https://the-decoder.com/ai-agent-swarms-are-a-massive-waste-of-tokens-with-zero-quality-gain-says-openai-codex-developer/)
- [Stanford Robotics Lab: Oussama Khatib Publications](https://khatib.stanford.edu/publications.html)
- [Khatib 1987 Operational Space Formulation PDF](https://khatib.stanford.edu/publications/pdfs/Khatib_1987_RA.pdf)
- [DOI: 10.1109/JRA.1987.1087068](https://doi.org/10.1109/JRA.1987.1087068)
