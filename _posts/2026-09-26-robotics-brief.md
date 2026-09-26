---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-26"
date: 2026-09-26 09:00:00 +0800
description: "本期关注室内 LiDAR 回环、动态障碍不确定性导航、向量化约束规划、全手接触力调节、支撑接触选择、遮挡感知 MPPI、Rolling-WAM 与 Agent Skill 可验证评测。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-26

## 摘要

今天是周六，arXiv Robotics 与 Software Engineering 最新公开批次仍是 **2026-09-25（周五）**，分别有 101 条和 52 条。本期先从最新公开批次筛选，再按规范化标题、arXiv ID、DOI、GitHub 仓库和项目页与历史覆盖索引强制去重。由于入选工作的 v1 实际提交于 9 月 23–24 日 UTC，距今天 09:00（Asia/Shanghai）均超过 24 小时，所以全部标为“时间回补”。最新列表见 [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) 与 [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

今天 SLAM / 定位侧最值得看的，是 **UpDown-SC**。经典 Scan Context 使用 polar cell 最大高度，室内大面积天花板会压掉下半部分更有区分度的结构。UpDown-SC 先做重力方向归一化，再同时保留下层/中层结构的上包络与顶部结构的下包络；它 training-free、CPU 轻量，并保留 Scan Context shortlist 和 yaw 对齐流程。([论文](https://arxiv.org/abs/2609.29118)，[代码](https://github.com/jiejie567/updown-sc))

动态导航方面，**UCON** 同时处理目标 ID 丢失和 uncertainty 无法进入 planner 两个问题：历史点云片段用于 point-level re-association，Kalman filter 输出各向异性的状态与 covariance，再转换成可微的 uncertainty sector 写入 trajectory optimization。([论文](https://arxiv.org/abs/2609.29419))

运动规划侧，**ReVAMP** 用 analytic IK 重新参数化受约束 planning space，让末端约束天然成立，再针对这种表示重新设计向量化和并行计算。论文在最高 20 维、复杂约束下报告微秒到毫秒级规划，相对当前对比方法最高约 10× 加速。([论文](https://arxiv.org/abs/2609.30213))

控制侧有两项很“硬件味”的工作。**Real-Time Force Regulation for Whole-Hand Dexterous Grasping** 持续估计整只手各 link 上的接触并重算力分配，27-DoF 真机展示扰动下抓持维持和 regrasp。([论文](https://arxiv.org/abs/2609.30082)，[项目页](https://sangminkim-99.github.io/reactive-grasp-whole-hand/)) **Contact as a Decision Variable** 则把“靠墙、撑桌、借扶手”本身变成决策变量，用 residual wrench、末端可达性和 base mobility 衡量支撑收益，Unitree Go2 + AgileX NERO 实验中相对逐候选精确求解约 3× 加速。([论文](https://arxiv.org/abs/2609.30140))

无人机控制方面，**OA-MPPI** 把“遮挡区域中可能突然出现的动态体”直接写进 MPC。每个规划周期从在线 occupancy map 提取 3D occlusion boundary，对隐藏 agent 的 reachable region 进行 horizon 传播，并在 MPPI rollout 中惩罚进入这些区域的轨迹；完整 pipeline 已做 onboard real-time 真机验证。([论文](https://arxiv.org/abs/2609.28709))

机器人世界模型侧，**Rolling-WAM** 不再每次 replanning 都从纯噪声重新生成完整 future video + action，而维护处于不同 noise level 的 video-action chunks。临近执行 chunk 完全去噪，更远 future 只做部分 refinement；下一周期继续利用保留的未来 chunk。LIBERO、RoboTwin 与 Unitree G1 上，论文报告 **4.5× steady-state replanning speedup**。([论文](https://arxiv.org/abs/2609.30247)，[项目页](https://rolling-wam.github.io/))

AI Coding 主动态里，**Evaluating Agent Skills for Version-Specific Plugin Migration** 很值得和 Skill 热潮一起看。加入真实 plugin-upgrade skill 后，mean reward 从 93.83 升到 98.75，但深入追踪 328 个 criterion decision 后发现 evaluator 本身存在评分错误；真正的 executable probe 能抓出“文字上看似满足、实际违反目标版本 contract”的答案。([论文](https://arxiv.org/abs/2609.30120)，[代码与评测](https://github.com/oh-my-dsh/dsh-plugin-upgrade-skill))

近期通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic、Google DeepMind 与 xAI 的官方发布入口，没有发现 9 月 25–26 日需要新增报道的通用旗舰正式发布；GPT-6 Sol / Luna、Claude Opus 5.5、Grok 4.7 已在前几期覆盖，因此今天不重复填充。

## 1. UpDown-SC：室内 Scan Context 不应该让天花板盖住真正有辨识度的结构

**时间回补：v1 提交于 2026-09-24 06:54 UTC。**

### 为什么重要

Scan Context 默认在每个 polar cell 存最大高度。室内同一格子常同时含天花板、门框、桌椅与设备，最大高度几乎总被天花板占据，相邻房间和长走廊真正有差异的中低层结构因此被弱化，传感器安装高度变化还会进一步放大问题。

### 算法模块与假设

UpDown-SC 先按重力方向 canonicalize 点云，再根据地图高度分布一次性估计上下结构的物理 split。描述子同时保留下层/中层结构的 upper envelope 和顶部结构的 lower envelope；mask-aware 双通道距离区分“未观测”与“真实低高度”。最后仍沿用 Scan Context shortlist 与 circular yaw alignment，可直接接现有 geometric verification。

方法依赖 3D LiDAR 和可信重力方向，可由 IMU 或稳定姿态估计提供。

### 实时性、鲁棒性与可复现性

方法无需训练网络，保留轻量 CPU front end。重复室内 session、安装高度变化、室内外混合与 outdoor transfer 实验中，室内第一候选更可靠，F1max / AUPR 处于最佳或第二梯队；continuous replay 也验证候选可用于 metric prior-map localization。代码和评测已经公开。

### 工程风险、适合谁关注与落地启发

它缓解垂直结构表达，但不会消除长走廊 aliasing。两个走廊上下包络都很像时，仍需 GICP / ICP、时间连续性、反光标志或语义信息裁决。适合 LIO-SAM、FAST-LIO2、室内回环和低线数 LiDAR 团队。

最便宜的 A/B 是保持 pose graph 和 registration 不变，同时计算原始 Scan Context 与 UpDown-SC，比较 Recall@1、false loop、GICP verification pass rate 与 CPU time。特别建议回放“同一路线 LiDAR 高度上下移动 20–50 cm”。

[论文](https://arxiv.org/abs/2609.29118) · [代码](https://github.com/jiejie567/updown-sc)

## 2. UCON：动态障碍导航里，目标身份和 covariance 都应该真正进入 Planner

**时间回补：v1 提交于 2026-09-24 11:41 UTC；IROS 2026。**

### 为什么重要与算法

动态导航常见两个接口断层：tracker 丢 ID / ID switch，但 planner 仍把轨迹当连续可信；tracker 明明维护 covariance，planner 却只读 mean trajectory。UCON 用 historical point-cloud fragments 做 point-level re-association，恢复短暂丢失目标；随后用 Kalman filter 得到各向异性的 motion state 与 covariance，再转换成 uncertainty sector，以 differentiable cost 直接进入 trajectory optimization。

### 实时性、鲁棒性与风险

论文包含 simulation 与 real-world experiments，并强调在较高计算效率下提高 perception stability 与动态导航鲁棒性。代码目前仍写的是 will be open-sourced，尚不能按完整开源项目评价。

工程风险是 covariance calibration：process noise 设得过小，planner 会收到虚假窄的不确定域。建议同时输出 track age、reassociation count、innovation、covariance 与 time since last observation。

### 适合谁关注与工程落地启发

适合 AMR / AGV、人群动态避障、LiDAR tracking、TEB / MPC / trajectory optimization。即使不复现整套算法，也可以先把动态障碍接口从 id/x/y/vx/vy 升级为 state mean、state covariance、track age、reassociation state，再让安全距离随 covariance 扩张。

[论文](https://arxiv.org/abs/2609.29419)

## 3. ReVAMP：约束规划不一定要采样后再投影，可以先换坐标系让约束天然成立

**时间回补：v1 提交于 2026-09-24 17:45 UTC。**

### 为什么重要与方法

托盘保持水平、焊枪保持固定姿态、门把手沿转轴运动等约束，会把可行 configuration space 压到 measure-zero manifold。普通 sampler 随机采点几乎必然不可行，只能不断 projection。ReVAMP 用 analytic IK 重参数化 planning space，使末端约束 by construction 成立，再对这一表示做 vectorized feasibility / collision evaluation 与并行 planning。

### 实时性与风险

论文报告最高约 20 维、复杂约束系统中，规划达到微秒到毫秒量级，相对当前 state-of-the-art 最高约 10× 加速。优势依赖可用 analytic IK 或高效参数化；运动学约束天然满足不等于碰撞、动力学、力矩和接触约束也满足，接近 IK branch singularity 时参数空间也可能失真。

### 适合谁关注与工程落地启发

适合机械臂轨迹规划、焊接/打磨、双臂协作、受约束 TAMP。对现有 constrained planner 可做 sample→project 与 reduced parameter→analytic IK 双实现，保持 collision checker 和 cost 相同，只测 valid-sample ratio、P50/P95 latency 与 singularity failure。

[论文](https://arxiv.org/abs/2609.30213)

## 4. Whole-Hand Force Regulation：接触力分配应该跟着接触变化实时重算

**时间回补：v1 提交于 2026-09-24 16:31 UTC。**

### 为什么重要与算法

whole-hand grasp 中，掌心、指节、手指侧面会随物体运动形成或失去接触，一次预计算 fingertip force allocation 很快与真实接触脱节。系统用 tracked object model + hand proprioception 几何估计各 link 接触，并持续重算满足 friction constraints、actuator limits 与 actuation-consistency constraint 的 contact-force distribution，再与 reactive reaching 联动，实现 grasp acquisition、disturbance rejection 与 regrasp。

### 真机、风险与可复现性

仿真相对 fixed-allocation 与 fingertip-only execution 提高 grasp retention；真实 27-DoF arm-hand 中展示了外部扰动下维持与恢复。最大风险是“几何接触”不等于“真实法向力已建立”，产品里最好结合 motor current / tactile / force residual 形成 contact confidence。项目页已公开，便于对照实现结构。

### 适合谁关注与工程落地启发

适合灵巧手、whole-hand grasp、接触丰富控制。先不改 force optimizer，只把静态 contact array 改成带 link_id、point、normal、confidence、age 的实时集合，仅在 contact set 变化时触发 reallocation，观察扰动下 grasp failure 是否下降。

[论文](https://arxiv.org/abs/2609.30082) · [项目页](https://sangminkim-99.github.io/reactive-grasp-whole-hand/)

## 5. Contact as a Decision Variable：腿式操作机器人应该主动选择靠哪里更值

**时间回补：v1 提交于 2026-09-24 17:08 UTC。**

### 为什么重要与方法

机器狗/人形在远距离或大推力操作中经常借墙、桌面、扶手支撑，但 contact 不是越多越好：它能增加 residual wrench，也会限制 base mobility 或末端 reach。论文用 residual wrench、end-effector reach、base mobility 三种任务后剩余能力衡量候选 contact，再与 acquisition cost 权衡。

CTCS 先做 contact/task feasibility screening，再按 surface 聚类，对少量 anchor 精确求值，用 local sensitivity 预测相似候选，选择性 exact check，最终只对 shortlist 精确 rerank。

### 结果、风险与工程落地

Unitree Go2 + AgileX NERO arm 的仿真和硬件实验覆盖 392 个 task condition、9 个 support surface。相对 ground-only / fixed-contact 能选到更合适支撑；相对 exact-every-candidate 约 3× 加速。真实部署仍需考虑 surface friction、compliance、结构稳定性和 semantic permission。

适合机器狗 + 机械臂、人形 loco-manipulation、多接触全身控制。即使暂时不自动选择 contact，也值得实时输出 residual wrench、reach、base mobility 三类 margin，让任务层知道当前是“刚好能完成”还是“完成后仍有恢复余量”。

[论文](https://arxiv.org/abs/2609.30140)

## 6. OA-MPPI：UAV 不只要躲看见的障碍，还要躲可能从遮挡后出来的东西

**时间回补：v1 提交于 2026-09-23 18:46 UTC。**

### 为什么重要与算法

unknown 当 free 太激进，unknown 当 occupied 又太保守。OA-MPPI 每个 planning step 从 online occupancy map 提取 3D occlusion boundary，对潜在 hidden agent 沿 horizon 传播 reachable region，并在 MPPI rollout 中惩罚进入这些扩张区域的轨迹。rollout 使用非线性 quadrotor dynamics，并考虑 individual rotor thrust limits。

### 真机、实时性与风险

论文完成 simulation + hardware flight，完整 pipeline onboard real-time。相对 baseline MPPI 增加了离 occlusion boundary 的 clearance；仿真中还能避开从遮挡区突然出现的 agent。

主要风险是 hidden-agent reachable set 的速度/加速度假设：过大则所有拐角都过度减速，过小则形成虚假安全；occupancy map 的遮挡边界也受定位误差和 resolution 影响。

### 适合谁关注与工程落地启发

适合室内无人机、仓库/走廊 UAV、MPPI、动态避障。已有 MPPI 可以先只增加 hidden-reachable risk cost，不动其他 dynamics/cost，专门测试“人从门后/货架拐角出现”，比较 minimum distance、任务时间和 false conservative rate。

[论文](https://arxiv.org/abs/2609.28709)

## 7. Rolling-WAM：未来视频和动作不必每个控制周期都从头想一遍

**时间回补：v1 提交于 2026-09-24 17:58 UTC。**

### 为什么重要与方法

WAM 每次 replanning 如果都重新联合生成完整 future video + action，iterative denoising 会拖慢闭环。Rolling-WAM 维护 sliding window，不同 video-action chunk 处于不同 noise level：临近执行 chunk 当前周期 fully denoise，更远 future 只 partial refine；新 observation 到来后窗口滚动，保留 future chunk 继续去噪。这与 receding-horizon MPC 的滚动修正很相似。

### 结果与风险

LIBERO、RoboTwin 与真实 Unitree G1 上，论文报告相对 standard joint WAM **4.5× steady-state replanning speedup**。风险是 stale imagination：物体被移动、抓取失败或意外接触后，旧 future 可能立即失效，因此应监控 observation-prediction error，在 mismatch 过大时 reset rolling state。

### 适合谁关注与工程落地启发

适合 VLA / WAM、Unitree G1、生成式机器人策略。即使不用 WAM，也可检查现有生成式 policy 是否每帧全重算；高成本视觉编码、轨迹 latent 与 world prediction 可以 warm-start，但必须有明确 invalidation trigger。

[论文](https://arxiv.org/abs/2609.30247) · [项目页](https://rolling-wam.github.io/)

## 8. Agent Skill 评测：平均分涨了，不代表 Skill 真满足目标版本 Contract

**时间回补：v1 提交于 2026-09-24 16:56 UTC。**

### 突破性工程价值

研究对象是一个真实发布的 plugin-upgrade skill。加入 Skill 后 mean recorded reward 从 93.83 提升到 98.75，但收益集中在一个任务，八组 task pair 已在 ceiling。作者把 328 个 criterion decision 追溯到 target-version contract，发现 evaluator 本身存在正反两类评分错误。

### 为什么 executable probe 很重要

典型案例是 containment predicate 错误接受 parent directory，却仍给满分。自然语言评分很难发现，真正 executable probe 会立即暴露 contract violation；另一方面，也存在有效 teardown repair 因 rubric 过窄而被错误排除。

修正复查发现的 decision 后，Skill 效果点估计仍为正，但区间移动到或跨过 0；换两个其他模型家族重判时，agreement 分别为 91.8% 和 95.7%，估计增益也明显变化。

### 真实研发含义、可复现性与落地

Skill evaluation 至少应有 aggregate task score、contract-level evidence、executable probe / real migration test 三层。论文代码、Skill、数据和评测证据均公开，仓库还包含跨 Claude Code、Codex、Gemini、Cursor 的安装方式。

适合 Skill / MCP 插件迁移 / Agent harness。重要 Skill 至少维护 SKILL.md、fixtures、contract.md、tests、known_failures 与 eval receipts，并先制造 contract-violating mutant，确认 evaluator 会拒绝。

[论文](https://arxiv.org/abs/2609.30120) · [代码与评测](https://github.com/oh-my-dsh/dsh-plugin-upgrade-skill)

## AI Coding 实战技巧精选

### 技巧 1｜批量交给 Agentic Autofix 前，先检查 Copilot Memory 里有没有过时的修复惯例

- **来源**：[GitHub 官方 Changelog，2026-09-25](https://github.blog/changelog/2026-09-25-agentic-autofix-now-uses-copilot-memory/) · [Copilot Memory 官方文档](https://docs.github.com/en/copilot/concepts/agents/copilot-memory)。
- **一句话结论**：Agentic Autofix 现在会在修告警前读取 Copilot Memory，并把成功修复模式写回 Memory。框架大升级或策略变化后，先检查旧 Memory。
- **具体怎么做**：
  1. 确认组织/企业允许 Copilot Memory，用户侧也已启用。
  2. 开始批量自动修复前，先检查与仓库框架、测试命令、依赖版本相关的 Memory。
  3. 大版本迁移、目录重构或规则变化后，清理明显过时记忆。
  4. 自动修复后仍跑原始分析、build、test；Memory 只是经验提示，不是 acceptance gate。
- **适合什么场景**：同一大仓库持续处理相似代码告警，希望 Agent 复用以前修复模式。
- **注意**：长期未使用的 fact / preference 会在约 28 天后自动删除，但版本化规范和测试仍应是 source of truth。

### 技巧 2｜企业先设置“未来 Copilot 新功能”的默认策略，避免新能力上线后各仓库状态失控

- **来源**：[GitHub 官方 Changelog，2026-09-24](https://github.blog/changelog/2026-09-24-default-enablement-of-copilot-features-for-copilot-business-and-enterprise/)。
- **一句话结论**：GitHub 新增企业/组织级 **Default policy for new features**。如果团队不希望每次新 Copilot 能力发布后再逐仓库追着收口，现在就先设统一默认，再对需要的功能做显式 override。
- **具体怎么做**：
  1. 进入 Enterprise / Organization 的 **AI Controls → Copilot**。
  2. 在 **Default policy for new features** 选择符合团队流程的默认值。
  3. 再检查 **Features & clients**、Copilot Code Review 和 MCP servers 这几类策略，因为新默认会作用到这些 eligible feature。
  4. 对确实需要提前试用的仓库或团队做显式 override，并把 override 原因写进内部变更记录。
- **适合什么场景**：Copilot Business / Enterprise、多个组织和仓库、希望统一管理 Agent/Review/MCP 能力启用节奏的团队。
- **注意**：GitHub 给出了约 28 天配置窗口，之后 eligible 且未配置的新功能会逐步按这一默认策略处理。它是治理默认值，不是对每个具体功能风险的替代评审。

## 经典论文回顾

### SegMatch：在局部特征和全局描述子之间，引入 3D Segment 这个中间尺度

Renaud Dubé、Daniel Dugas、Elena Stumm、Juan Nieto、Roland Siegwart、Cesar Cadena 的 **SegMatch: Segment based place recognition in 3D point clouds** 最初于 2016 年公开，发表于 **ICRA 2017**。它是 3D LiDAR place recognition 从局部特征 / 整帧全局描述向结构级匹配发展的代表工作。

### 核心问题、算法与假设

local feature 对 partial observation 更友好，但局部几何容易歧义；global descriptor 区分度高，却更受 viewpoint 影响。SegMatch 用 segment 作为中间层。系统由 point-cloud segmentation、segment feature extraction、segment matching 与 geometric verification 构成。它不要求 segment 必须对应语义对象，只要求跨 session 能稳定重复观察。

### 当年为什么重要

论文在 KITTI 最大 odometry sequence 上展示约 **1 Hz** localization，并能够在线实时检测和关闭 loop。它证明 place recognition 的基本单元不一定只能是点或整帧，中尺度结构可以同时获得局部和全局方法的部分优势。

### 今天仍在使用的思想与已被替代的部分

segments、objects、planes、rooms、submaps、scene graphs 都延续同一思想：原始点太细，整帧又太粗。原始 SegMatch 的手工 descriptor、传统分类器与 ROS Indigo 实现今天已不先进；团队后来发展出 SegMap，用 data-driven descriptor 做 segment localization 与 map compression，现代系统还会用 sparse convolution、Point Transformer、MinkLoc 等。

### 公开代码与可复现性

代码后来演进到 ETH ASL 的 [segmap](https://github.com/ethz-asl/segmap) 仓库，BSD 许可，但依赖环境较老。

[arXiv](https://arxiv.org/abs/1609.07720) · [ICRA DOI](https://doi.org/10.1109/ICRA.2017.7989618) · [代码](https://github.com/ethz-asl/segmap)

### 对当前工程项目的重新解读

已有 Scan Context 回环时不必替换前端，更值得做三层验证：UpDown-SC / Scan Context 快速出 Top-K；segment / plane / reflector structure 做解释性几何验证；GICP / pose-graph consistency 最终决定是否加入 loop factor。对 16 线 LiDAR 和长走廊特别适合。

## 今日结论

今天八项工作有一条一致主线：**把中间状态显式化。** UpDown-SC 重写室内垂直结构表达；UCON 把目标身份和 covariance 传进 planner；ReVAMP 用新的参数空间让约束天然成立；Whole-Hand Force Regulation 把 contact set 从静态假设变成在线状态；CTCS 把支撑接触本身变成决策变量；OA-MPPI 把遮挡区潜在动态风险变成 horizon 内显式 cost。

Rolling-WAM 说明生成式机器人策略最终也会重新遇到经典 MPC 熟悉的问题：未来计划不应每一拍全部作废，应滚动修正；旧未来也不能永远相信，必须有 mismatch 与 reset trigger。

AI Coding 侧同样如此：Skill 总分必须回到 contract 和 executable probe；Copilot Memory 可以存经验，但不能替代测试；企业级 Copilot 新能力也应该先进入统一、可审计的策略默认值，而不是上线后再被动追配置。

如果把今天压成一句话：

> **可靠系统不是让模型多想一点，而是把地点、身份、不确定性、接触、遮挡、未来计划和权限边界变成可观察、可验证、可失效的显式状态。**

## 最值得深入研究或尝试复现的方向

1. **UpDown-SC 替换 Scan Context descriptor 做 A/B。** 不改 pose graph / registration，比较长走廊、安装高度变化、上下楼后的 Recall@1、false loop 与 verification pass rate。
2. **动态目标接口增加 covariance + reassociation state。** tracker 不换，先让 planner 看到 uncertainty；专测目标丢失 0.5–2 秒后重新出现。
3. **OA-MPPI Occlusion Cost Sidecar。** 从 occupancy map 生成门口/货架拐角隐藏 agent 可达域，保持其他 MPPI cost 不变，比较 minimum distance 与不必要减速。
4. **Whole-hand Contact Set 动态化。** contact 改成带 confidence / age 的实时集合，统计 contact turnover 与 grasp failure 的相关性。
5. **Agent Skill Contract Regression。** 每个 Skill 维护 5–20 个 executable probe；先制造 contract-violating mutant，验证 evaluator 能拒绝。
6. **Rolling Inference State。** 对 diffusion / VLA 保留上轮未来 latent，仅在 observation mismatch 足够大时 reset，记录 replanning latency、失败恢复时间和 stale-plan 事故率。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [UpDown-SC](https://arxiv.org/abs/2609.29118) · [代码](https://github.com/jiejie567/updown-sc)
- [UCON](https://arxiv.org/abs/2609.29419)
- [ReVAMP](https://arxiv.org/abs/2609.30213)
- [Real-Time Force Regulation](https://arxiv.org/abs/2609.30082) · [项目页](https://sangminkim-99.github.io/reactive-grasp-whole-hand/)
- [Contact as a Decision Variable](https://arxiv.org/abs/2609.30140)
- [OA-MPPI](https://arxiv.org/abs/2609.28709)
- [Rolling-WAM](https://arxiv.org/abs/2609.30247) · [项目页](https://rolling-wam.github.io/)
- [Evaluating Agent Skills for Version-Specific Plugin Migration](https://arxiv.org/abs/2609.30120) · [代码与评测](https://github.com/oh-my-dsh/dsh-plugin-upgrade-skill)
- [Agentic Autofix now uses Copilot Memory](https://github.blog/changelog/2026-09-25-agentic-autofix-now-uses-copilot-memory/) · [Copilot Memory](https://docs.github.com/en/copilot/concepts/agents/copilot-memory)
- [Default Enablement of Copilot features](https://github.blog/changelog/2026-09-24-default-enablement-of-copilot-features-for-copilot-business-and-enterprise/)
- [SegMatch](https://arxiv.org/abs/1609.07720) · [DOI](https://doi.org/10.1109/ICRA.2017.7989618) · [代码](https://github.com/ethz-asl/segmap)
