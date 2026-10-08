---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-08"
date: 2026-10-08 09:00:00 +0800
description: "关注单片机级雷达惯导、3DGS 场景图、高速无人机规划、模型库安全控制、Flow RL、开放世界动作模型、Coding Agent Harness 与 Claude Haiku 5.5。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-08

## 摘要

截至 2026-10-08 09:00（Asia/Shanghai），arXiv Robotics 最近的常规公开批次是 **2026-10-07，共 133 条**，Software Engineering 同日 **26 条**。本期先检查最近 24 小时内的官方模型与工具发布，再读取最新论文批次，向最近 7 天扩展以寻找定位 / 建图高价值工作。选题已与覆盖索引按规范化标题、arXiv ID、DOI、项目页、代码地址联合去重。注意：最新 arXiv 公开批次中的多篇 v1 实际提交于 **10 月 6 日 UTC**，早于本次生成 24 小时，下面明确标为“时间回补”，而不冒称今天首发。

今天与 SLAM 最直接相关的是 **Embedded Bare-Metal Radar-Inertial Odometry**：不依赖 Linux、ROS 或 GPU，FMCW 雷达、IMU 驱动和惯性估计全部运行在单核微控制器上，飞行实验平移 APE 为 0.51–0.82 m、相对位姿误差低于 3%，还能直接闭环接入未修改的 PX4。固件与 PCB 设计均已公开。它不是要与高精度多线 LiDAR-LIO 正面竞争，而是给弱光、粉尘和极低功耗平台提供一种完全不同的状态估计基线。[论文](https://arxiv.org/abs/2610.07278)

**OpenSplatGraph** 将在线 3DGS 开放词汇语义地图，升级为可长期维护的对象和关系图。它保存语义观测可靠性、按查询抽取实例，再将对象关联到持久节点。这样“在上一次巡检时，那个阀门旁边的仪表是什么状态”一类查询，终于可以落到可修订实体，而不只是 dense feature field。[论文](https://arxiv.org/abs/2610.07569)

控制方向两项工作值得并列。**NMPP** 把真实感知障碍写成非线性预测规划的**硬几何约束**，把全状态轨迹交给 SE(3) 跟踪器；真机在未知杂乱环境中达到 5.5 m/s，仿真激进速度设置下成功率 86%，对比规划器仅 26%。**LBA-CBF** 则只靠最近控制记录，在最多 25 万个候选动力学模型中筛选解释当前状态的模型集，再对该集合同时施加安全约束；已有 Crazyflie 和 F1TENTH 实验。这一对工作分别把“碰撞约束”和“模型不确定性”拉回正式优化接口。[NMPP](https://arxiv.org/abs/2610.08695) · [LBA-CBF](https://arxiv.org/abs/2610.08765)

机器人学习侧，**QF3** 在 flow matching 的策略训练中加入由 critic 导出的 Q 梯度，并只在接近 replay action 的可信动作维度上使用梯度。论文报告从零训练人形 locomotion / tracking 并零样本落地真机；与 on-policy FPO++ 相比，训练 wall-clock 速度提高 10 倍。**OpenWAM** 则给世界动作模型提供统一、可组合的架构，将视频预测与动作生成不同交互顺序置于同一实验框架，开放了代码，用于回答“世界模型究竟何时值得插在 action expert 前面”。[QF3](https://arxiv.org/abs/2610.08789) · [OpenWAM](https://arxiv.org/abs/2610.07922)

**HERMES / Dev-Primitives** 是今天 AI Coding 最有系统价值的研究：将仓库组件变成拥有局部上下文与依赖视图的可执行开发原语，按需激活、把失败证据定位回真正应修改的组件。四项软件工程评测相对匹配 Harness 基线平均提升 12.4%。它强调：长任务不是简单加大 Context，而是要设计可复用的“仓库内执行接口”。[论文](https://arxiv.org/abs/2610.07832)

模型动态方面，Anthropic **10 月 7 日正式发布 Claude Haiku 5.5**，模型 ID 为 claude-haiku-5-5。低于或等于 100K 输入窗口时 API 标价为每百万输入 0.10 美元、输出 0.50 美元；定位高频、短时、可委托的子 Agent 工作。它已同时进入 GitHub Copilot 的多个客户端，适合建立“大模型判断 + 小模型检索 / 分类 / 摘要”的路由，而不是盲目用它承包复杂自主开发。[Anthropic 官方发布](https://www.anthropic.com/claude-haiku-5-5)

最新公开列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

## 1. Embedded Bare-Metal Radar-Inertial Odometry：单核 MCU 跑完整雷达惯导

**时间回补：arXiv v1 提交于 2026-10-05 19:16 UTC。**

### 为什么重要

惯性里程计往往默认需要 x86、ARM Linux、ROS2 或专用加速器。对于微型 UAV、极小轮式平台、煤尘和烟雾环境，计算机体积、功耗与视觉失效风险可能比绝对轨迹精度更难解决。该工作直接采用 FMCW 雷达径向速度观测与 IMU，试图把导航估计压到单核 MCU，而不是在已有 LiDAR / VIO 方案上继续减几帧点云。

### 算法模块、传感器与假设

整体结构是“FMCW Radar + IMU → 雷达数据处理 / 速度测量 → aided inertial navigation → 估计姿态、速度、位置 → PX4 接口”。雷达能提供 Doppler 速度信息，对光照、低纹理不敏感；但它并不天然具备 LiDAR 那样稠密的几何轮廓。输出质量依赖雷达可用静态散射体、安装外参、时间同步，以及雷达回波中的动态干扰剔除。

### 实时性、结果与可复现性

作者把所有传感器驱动、前处理和状态估计放在**同一个单核微控制器**执行。动捕对照飞行中平移绝对位姿误差 **0.51–0.82 m**，RPE **小于 3%**，并完成未修改 PX4 上的闭环飞行。论文给的是该测试条件下的结果，不等于任意纹理贫乏或强多径环境都有同等精度。固件和 PCB 都已公开，因而不仅可以读算法，还能检查完整接口、电源和硬件实现。

### 工程风险与落地启发

若将其用于狭窄走廊无人机，必须先确认误差余量是否满足安全距离：0.5 m 级 APE 对 30 cm 小飞机在半米过道中显然不能直接当唯一定位源。更务实的用途是低功耗备份速度 / 健康观测，或者将 MCU RIO 与 LiDAR-LIO 做异构失效保护。建议记录雷达速度有效率、散射点分布、姿态创新、时间偏移与 PX4 EKF innovations。**适合**：FMCW 雷达、极低功耗嵌入式、强光 / 烟尘无人机、多传感器冗余设计。

[论文](https://arxiv.org/abs/2610.07278) · [固件](https://github.com/ntnu-arl/embedded_rio) · [PCB](https://github.com/ntnu-arl/embedded_rio-pcb)

## 2. OpenSplatGraph：让 3DGS 地图成为可持久查询的对象关系图

**时间回补：arXiv v1 提交于 2026-10-06 00:58 UTC；ACCV 2026。**

### 为什么重要

3D Gaussian Splatting 近年来已经能把场景的颜色、几何甚至语义特征存进密集地图，但“所有 splats 的 feature 很像阀门”不等于“地图知道这是一台阀门、它属于哪套设备、与隔壁仪表什么关系”。机器人长时巡检需要稳定的对象 ID、历史查询和增量属性更新。

### 算法模块

OpenSplatGraph 从**在线 Gaussian open-vocabulary semantic map**出发，增加可靠性感知 semantic field，为观测维护轻量统计。查询时根据语义置信度提取对象实例；随后进行跨观察 / 跨查询实例关联，把它们转成 persistent graph nodes，再维护属性和对象间关系。地图仍然保留原来的稠密几何，并没有为了场景图放弃可渲染表示。

### 传感器 / 地图假设、实时性与鲁棒性

它假设已有可在线更新的 3DGS 语义地图，且相机姿态、对象掩码和跨帧关系具有足够一致性。作者在 3D scene understanding benchmark 和真实机器人中验证下游任务，但论文摘要没有给出可以直接推广到 RK3588 的统一 FPS；工程上应独立测 Gaussian 更新、实例抽取、graph association 三种延迟。最大的风险是对象切分和地图版本错位：同一阀门跨视角被拆成多个节点，或者移动设备位置更新后 graph edge 未同步改写。

### 可复现性与工程落地启发

项目页已公开，代码的完整可用性仍需以仓库实际发布状态为准。建议在现有点云 / 3DGS 地图旁先建立对象 Sidecar：持久保存 object_id、submap_id、pose_revision、semantic_evidence、graph_edges 与 last_verified，避免把所有语义压成一次 embedding 查询。**适合**：3DGS / 语义 SLAM、工厂巡检、自然语言目标定位和长期机器人记忆。

[论文](https://arxiv.org/abs/2610.07569) · [项目页](https://csiro-robotics.github.io/OpenSplatGraph/)

## 3. NMPP：杂乱环境高速无人机，用硬障碍约束取代“撞了扣分”

**时间回补：arXiv v1 提交于 2026-10-06 17:10 UTC。**

### 为什么重要

小无人机在杂乱空间中敏捷飞行时，需要的不是一条视觉上平滑的几何线，而是可被姿态控制器真实追踪、遵守推力和姿态边界、又不会与障碍物发生冲突的**全状态轨迹**。多项式轨迹方法常将航迹锁在凸安全走廊内；很多优化方法则将障碍写成 soft penalty，允许用性能收益去交换碰撞。

### 算法模块与动力学假设

NMPP 构造非线性 quadrotor model predictive planning：状态 / 推进器约束参与优化，感知障碍以**硬几何约束**进入；规划输出完整 state reference，再由不直接感知障碍的 SE(3) tracker 跟踪。设计分工非常明确：planner 负责决策和可行域，tracker 只负责高带宽动态执行。它依赖障碍几何、状态估计和推力模型足够及时准确；硬约束也不会自动补偿定位漂移。

### 实时性与真机

作者报告位置 RMSE 比线性 MPC 轨迹规划低 **58%–67%**，比多项式轨迹规划低 **41%–70%**。森林飞行在最高 **9.5 m/s** 情况下全部无碰撞；更激进速度分布下成功率 **86%**，对比规划器 **26%**；未知杂乱真机环境最高 **5.5 m/s**。这些结果是作者报告的特定试验，不应直接解释成任意室内狭窄走廊都能安全飞行同样速度。

### 工程风险、复现与落地启发

真正要测的不只是解是否可行，还包括 P95 solve time、上周期轨迹执行进度、地图 age、tracking residual 和不可行时退让策略。对于 PX4 现有系统，优先在外层做 NMPP 仿真：固定同一 obstacle cloud 和动力学、将 soft-penalty planner 与 hard-constrained planner A/B，再做低速真机 shadow test。**适合**：高速 UAV、PX4 外部轨迹控制、狭窄 / 灌木 / 林地规划。

[论文](https://arxiv.org/abs/2610.08695)

## 4. LBA-CBF：25 万候选动力学模型，在线筛选仍安全的控制输入

**时间回补：arXiv v1 提交于 2026-10-06 17:51 UTC。**

### 为什么重要

10 月 6 日报道的 LLA-MPC 关注“哪个模型最能解释当前机器人”，而 LBA-CBF 进一步回答“如果当前模型仍然不确定，如何避免使用单一 best-fit 模型给出过度自信的安全证书”。它是不同工作，不是重新报道同一篇论文。

### 算法模块

系统记录短时间 look-back 状态与动作，平行计算有限 candidate dynamics bank 的近期 prediction errors。保留误差不超过最佳分数某个容差的模型集合，对集合中**每一个候选模型**施加 high-order CBF 条件，再求解尽量接近 nominal action 的安全输入。通过容差大小，可以从单一 best-fit 适配平滑切到 full-bank robust filtering，不需要显式切换模型或连续参数辨识器。

### 假设、结果与可复现性

论文的条件性保证是：**如果保留集合包含一个对真实安全动态具有代表性的候选，而且 QP 可行，那么过滤控制满足真实 CBF 条件**。这不是“25 万个模型总有一个是真的”的无条件保证。仿真在风向突变和未知载荷的四旋翼任务中，从随机初始状态全部安全抵达目标，对比 adaptive / robust baseline 取得 0%–88% 的不同成功率；实现能在控制环中评估最高 **250,000 个模型**。Crazyflie 2.1 与 F1TENTH 做了风、载荷释放和轮胎摩擦变化实验。

### 风险与工程落地启发

模型库覆盖范围、状态估计误差与容差是三大风险源。应记录 bank score distribution、retained set size、CBF infeasibility、solve time 与 emergency fallback。如果真实动力学落在 bank 之外，须先降速 / 停机而不是继续信任形式化标签。代码 / 视频入口已提供，但当前项目主页仍显示 coming soon，不能声称可一键复现。**适合**：高变化载荷、风扰车辆 / 四旋翼、CBF safety shield、在线模型适配。

[论文](https://arxiv.org/abs/2610.08765) · [项目入口](https://lla-control.github.io/)

## 5. QF3：把 Flow RL 的 Q 梯度限制在可信动作邻域内

**时间回补：arXiv v1 提交于 2026-10-06 17:59 UTC。**

### 为什么重要

flow-matching action policy 适合从示范学习多模态动作，但真正面对任务失败时，仍然需要 RL 改善策略。off-policy actor 更新如果直接沿 critic 的动作梯度优化，会遭遇 Q extrapolation error：critic 在 replay data 以外看似很自信，却可能把策略推向没有真实回报支撑的动作。

### 算法模块

QF3 在 flow matching loss 外增加 critic 提供的 Q-gradient。算法通过**对 flow 输出的一步预测**建立可微链，将 Q 的动作梯度传回 flow policy；关键的 filtered Q-gradient 只对留在 replay action 附近的动作维度施加更新。这样可以利用 off-policy replay，却避免整条动作向量被 critic 的分布外梯度肆意牵引。

### 动力学假设、效率与结果

作者称 QF3 是首次能从零训练 humanoid locomotion flow policy、并零样本迁移硬件的 off-policy flow RL 方法；在他们的训练设置下，humanoid locomotion / motion tracking 的 wall-clock 相比 FPO++ 快 **10 倍**。还对 ABC-Sim 和 Robomimic 的预训练 manipulation flow policy 做 finetuning。此处速度比较受硬件并行、环境吞吐和数据复用影响，并不等同于算法每次 gradient step 天然快十倍。

### 可复现性与工程风险

已有官方项目页。部署前建议与 SAC / PPO / 其他 flow RL 按同一环境步数、wall-clock 和真实 rollout 比较，同时记录 critic ensemble disagreement、Q-gradient clipping ratio、policy action distance to replay 与真实 collision / failure。**适合**：flow-matching VLA、双臂操作、仿真强化学习、人形 locomotion、已有示范但缺少在线改进机制的团队。

[论文](https://arxiv.org/abs/2610.08789) · [项目页](https://qf3-rl.github.io/)

## 6. OpenWAM：把视频世界模型与动作专家的耦合方式变成可控实验变量

**时间回补：arXiv v1 提交于 2026-10-06 08:02 UTC；项目页与代码已于 2026-06-04 发布，本期是论文补充。**

### 为什么重要

“世界模型帮助机器人控制”已经很容易变成一句没法验证的口号：不同研究同时改变视频 backbone、action expert、交互顺序和训练数据，最后成功率变化无法归因。OpenWAM 的贡献是搭一套**可配置的共同基座**，专门隔离这些选择。

### 算法模块

以 Wan2.2-5B 为基础，在 **10,000+ 小时机器人视频**上进行 causal video pretraining，然后通过共享 Mixture-of-Transformers 接入 action expert。同一框架可在 joint、video-then-action、action-then-video、decoupled 四种交互机制间切换。还支持 inverse / forward dynamics 模块，以反事实状态转移训练模型，不依赖全部来自成功示范的轨迹。

### 结果、假设与鲁棒性

作者报告 causal-adapted video-to-action 路线在 LIBERO-Long 从 **68.4% 提高到 97.8%**。仅适配视频预测器、冻结局部逆动力学模块后，在四个 holdout LIBERO-90 任务上均值成功率 **84.0%**，对比 full-context inverse model 47.0%、仅示范训练的 local-context model 21.5%。反事实监督还使 RGB future-prediction error 减少 **34.5%**，16 个相同初态结局识别从 21.1% 提升到 71.3%。

### 工程风险与可复现性

这些是作者实验集上的结果，不意味着视频模型能推导出真实质量、摩擦与因果动力学。WAM 仍需外接可靠 metric state、接触感知及安全执行层。项目和代码已经开放，适合固定数据 / 动作空间，仅切换四种 interaction pattern 做 A/B。**适合**：VLA / world-action model、机器人未来预测、Sim2Real、需要明确训练变量与公平基线的研究团队。

[论文](https://arxiv.org/abs/2610.07922) · [项目页](https://openwam.stanford.edu/)

## 7. HERMES / Dev-Primitives：长时 Coding Agent 不应不停重读整个仓库

**时间回补：arXiv v1 提交于 2026-10-06 06:32 UTC。**

### 为什么重要

Coding Agent 运行几个小时后，失败不一定来自模型不会写代码，而是上下文被反复读取、组件边界不清、错误信息无法反馈到应修改的源文件。不断增加 context window 只会把依赖和状态塞得更杂。

### 算法模块与实质创新

HERMES 把仓库源码、配置、测试等 artifact 包装成 **Dev-Primitive**：每个原语带有局部实现 / 依赖信息和常驻小模型，可通过自然语言执行组件级分析、与其他原语交流并允许局部修改。总 Harness 负责 dependency-aware dynamic activation，只唤醒与当前任务有关的原语；运行失败时通过 bug diagnosis 把证据送回需要修复的组件。

### 实验结果与边界

四个软件工程 benchmark 中，HERMES 相比匹配的原有 Harness 平均提高 **12.4%**。当路由 / 诊断层使用较强模型、组件原语仅用 Qwen3-8B 时，相比全部 GPT-5.6 Sol 的均质配置，在四项测试上的差距保持在 **4.5% 以内**；Terminal-Bench 4.0 推理成本下降 **26.2%**。这说明成功率不只是 model weights 的函数，也是“谁在何时读取哪段代码”的函数。

### 真实研发与安全风险

每个仓库文件都配一个 LLM 可能造成进程 / 显存放大、依赖图陈旧、并发编辑冲突。产品化应从**逻辑原语**开始而不是物理一文件一模型：例如 ROS package、NestJS module、Spring Boot service、FreeSWITCH integration adapter。所有编辑仍应经过沙盒、版本控制、单一合并者和独立 CI；局部 Agent 不应凭自己分析直接拥有全仓写权限。论文尚未给出可确认的成熟代码入口。**适合**：超大 C++/Java 仓库、多 Agent 长时任务、复杂依赖定位与 Harness 研究。

[论文](https://arxiv.org/abs/2610.07832)

## 8. Claude Haiku 5.5：高频子 Agent 的单任务成本出现新拐点

**最新发布：Anthropic，2026-10-07。**

### 突破性工程价值

Claude Haiku 5.5 的价值并不是让更小模型直接取代所有复杂 Coding Agent，而是让大量过去“不值得调用大模型”的任务变得经济：搜索结果归类、代码文件筛选、工具结果压缩、日志摘要、路由、重复表格提取以及简单补丁建议。

### 定价、能力和可用性

官方模型 ID **claude-haiku-5-5**。对于不超过 100K tokens 的请求，每百万输入 **$0.10**、输出 **$0.50**、cache read **$0.01**；超过 100K 的请求输入 / 输出分别为 **$0.50 / $2.50**。支持 adjustable effort。Anthropic 自报 Terminal-Bench 4.0 **39.2%**（Sonnet 5.5 为 70.6%），因此复杂开放式开发仍明显更适合更强模型。GitHub 10 月 7 日宣布它进入 Copilot 的 IDE、CLI、Web、cloud agent 等入口，具体展示会渐进开放。

### 研发选型、安全与工程落地启发

建议按三层路由做回归：Haiku 负责文件筛选、日志归纳、简单子任务；Sonnet / Opus 或 GPT-6 处理跨模块设计、长时修复；最终由测试、静态分析和确定性权限系统验收。固定 30–50 条真实仓库任务比较每成功任务成本、P95 latency、无效工具调用、误删和人工修正，不能只比较单 token 价格。**适合**：多 Agent Harness、IDE Agent、海量短查询、LLM Router 和构建成本敏感型自研 Coding 平台。

[Anthropic 官方发布](https://www.anthropic.com/claude-haiku-5-5) · [GitHub Copilot 官方公告](https://github.blog/changelog/2026-10-07-claude-haiku-5-5-in-github-copilot/)

## AI Coding 实战技巧精选

### 技巧 1｜给 Copilot 本地执行开启 Sandbox，再逐项收窄文件 / 网络权限

- **来源**：GitHub，2026-10-07，[Local sandboxing for GitHub Copilot now generally available](https://github.blog/changelog/2026-10-07-local-sandboxing-for-github-copilot-now-generally-available/)。
- **一句话结论**：将 Agent 运行工具与模型推理分开授权。Copilot CLI / App 与 VS Code Agent Host 已支持基于 Microsoft eXecution Container（MXC）的本地沙盒，支持 Windows、macOS、Linux。
- **具体怎么做**：① 在支持版本的 Copilot CLI 或 App 中启用本地 sandbox，按[官方 Sandbox 文档](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/sandboxing)配置；② 仅允许项目工作目录读写，默认阻断私人目录、SSH 私钥和云凭据；③ 仅放行必需网络域名，并单独检查 local MCP、Git 与 GitHub CLI 凭据授权；④ 用读禁止文件、访问未许可网络、普通 build 三类回归确认 deny 生效、正常开发未损坏。
- **适合什么场景**：Copilot 自主编辑、内部源码、大型 Agent 工作流、多仓库本地开发。
- **注意**：沙盒隔离的是工具执行，不等于模型本身安全，也不替代生产端最小权限、分支保护和人工发布审批。

### 技巧 2｜Copilot CLI 用 /model 发现 Ollama 本地模型，先验工具调用能力再接入工作流

- **来源**：GitHub，2026-10-07，[Discover local models in GitHub Copilot CLI](https://github.blog/changelog/2026-10-07-discover-local-models-in-github-copilot-cli/)。
- **一句话结论**：Copilot CLI **1.0.94-0 起**支持从已经运行的 Ollama 实例发现本地模型。可以保留云模型负责难题，让本地模型承担低敏感 / 高频子任务。
- **具体怎么做**：① 在本机安装并运行 Ollama、拉取一个支持 tool calling 和 streaming 的模型；② 升级 Copilot CLI 至 1.0.94-0 或更新版本，在会话运行 **/model**；③ 选择发现的本地模型，检查 provider 和 endpoint，确认 Add and use for this session 或 Add without switching；④ 用文件搜索、调用工具与断网三项小任务检查实际路径、延迟与退化方式。
- **适合什么场景**：本地 Coding Agent、隐私敏感文件检索、多模型路由、ARM/x86 开发机实验。
- **注意**：发现模型并不会自动安装 Ollama 或下载权重；**本地模型 ≠ 自动离线**。离线模式还需显式设置 **COPILOT_OFFLINE=true**，并审计远端 provider 是否会发送源码上下文。

## 经典论文回顾

### Tassa / Erez / Todorov 2012：在线轨迹优化是现代 MPC 与 iLQR 的一条工程源流

Yuval Tassa、Tom Erez、Emanuel Todorov 的 **Synthesis and Stabilization of Complex Behaviors Through Online Trajectory Optimization** 发表于 **IROS 2012**，DOI 为 **10.1109/IROS.2012.6386025**。该工作把复杂的人形起身、受扰恢复等动作纳入可在线反复求解的轨迹优化框架，展示了非线性动力学优化并不只是离线运动合成工具。

### 核心问题与算法

目标是在每个控制窗口寻找控制序列，使动力学、跟踪目标、姿态限制和控制代价取得更优折中。其代表性的局部轨迹优化结构是**前向动力学 rollout → 对当前轨迹做二次近似 → backward pass 得到局部反馈与前馈更新 → forward line search → 重复并执行前缀**。这构成 iterative LQG / iLQR 类方法的核心工程直觉：用状态反馈局部地改进整条控制轨迹，而非逐时刻手工设定 PID 增益。

### 假设与历史位置

这类方法依赖足够准确、可微或可近似微分的动力学，以及可接受的初始轨迹。它是**局部优化**，不会自动解决多峰非凸环境全局选路、未知障碍或长时数据关联。原论文 2012 年在标准 PC 上实现人形复杂动作约实时的 7 倍运行耗时，简单任务可实时，表明当时计算能力已经开始允许 online nonlinear trajectory optimization。

### 今天仍在使用的思想和后续扩展

今天的 MPPI、DDP/iLQR、非线性 MPC、全身控制规划虽有不同算法形态，但很多系统仍沿用“模型预测 + 优化当前动作序列 + 执行前缀 + 下一周期重算”的闭环机制。相对传统 iLQR，GPU 采样式 MPPI 更易搜多峰候选；SQP / constrained MPC 更适合强硬约束；学习策略则提供更好的初值。今天 NMPP 的硬碰撞约束、LBA-CBF 的模型库安全过滤，本质上都是在继续补强这种优化控制的现实假设。

### 代码 / 可复现性与重新解读

可用公开 [anassinator/ilqr](https://github.com/anassinator/ilqr) 阅读 iLQR 教学实现，不过该项目依赖 Theano，属于历史研究代码，不宜直接作为生产依赖。建议用现有 CasADi / JAX 或 C++ 自动微分写一个 double-integrator / unicycle iLQR baseline，测试四项：初始化差、强障碍约束、模型参数突变、控制截止时间，然后与 MPPI / NMPP 做公平对比。对目前仅开放 vx/vy/wz 接口的机器人，上层 iLQR 最好使用**真实闭环命令响应模型**，不要假定厂商控制器立即实现理想速度。

[IEEE 论文](https://ieeexplore.ieee.org/document/6386025/) · [DOI](https://doi.org/10.1109/IROS.2012.6386025) · [教学代码](https://github.com/anassinator/ilqr)

## 今日结论

今天的研究再次说明，**可靠的机器人控制和 AI Coding 系统并不是通过堆叠越来越大的单体模型实现，而是通过清晰的观测、可行域、计算预算和验证边界实现**。

单核 MCU 上的 RIO 说明状态估计可以作为独立低功耗硬件能力存在，不必和 SLAM 的每个高密度地图模块捆在一起；OpenSplatGraph 则把“好看的三维地图”向“可更新实体与关系”推进。对于长期巡检机器人，二者分别解决物理运动估计和持续环境记忆，两者不能互相替代。

NMPP 与 LBA-CBF 从不同层面加强安全：前者对轨迹几何施加硬约束，后者对未知动力学保留多假设。QF3 也应用了相同的谨慎原则：critic 只有在 replay action 邻域内的建议才值得影响 flow policy。它们共同反对“模型给了个高分，就可以忽略真实可行域”。

OpenWAM 反过来提醒世界模型研究，必须有可以隔离变量的同一测试基座；HERMES 也在软件工程中把仓库组件及其执行证据变成 Harness 的基本对象。Claude Haiku 5.5 的低成本让这类分层 Agent 更现实，但最终成功仍取决于是否有独立测试、权限分离与可回滚的 artifact。

今天的两条实战技巧进一步落到具体操作：先用沙盒限制 Agent 能碰什么，再用可选择的本地模型降低某些任务的成本。**模型选择与安全隔离是两件不同的事**，不能因本地推理就默认所有工具调用无风险。

## 最值得深入研究或尝试复现的方向

1. **MCU Radar-Inertial 备份里程计**：先复现实验板、时间同步和 PX4 EKF innovation，比较雷达 RIO、IMU-only 和 MID360-LIO 失效场景。
2. **3DGS / Point-Cloud Persistent Scene Graph**：为阀门、仪表和设备建立稳定 object ID，把 pose graph revision 与对象关系同步更新。
3. **UAV Hard-Constraint Planner A/B**：固定同一 SE(3) tracker，比较 soft-obstacle penalty 与 NMPP 风格 hard geometry constraints 的成功率和求解时间。
4. **Model-Bank CBF 安全层**：对风、载荷和响应延迟分别设计 5–50 个候选模型，先看是否足够，再考虑十万级 GPU 并行。
5. **QF3 Replay-Neighborhood 消融**：同一 flow policy 对比纯 flow matching、未筛选 Q-gradient、filtered Q-gradient 的回报和 OOD 动作率。
6. **OpenWAM 四种视频-动作交互顺序**：不换数据与模型参数预算，只改变 joint / video-first / action-first / decoupled 结构，测真实动作而非仅视频质量。
7. **Dev-Primitive Harness Prototype**：先以 ROS2 package / Java module / NestJS service 为单位实现激活、上下文摘要、局部诊断、回归验证，避免盲目一文件一 Agent。
8. **Haiku 5.5 子 Agent / 本地 Ollama 路由基线**：按简单分类、仓库搜索、复杂修复分层，记录成本、回退率、P95 时间和权限违规。

## 参考资料

- [arXiv Robotics 最新公开列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新公开列表](https://arxiv.org/list/cs.SE/recent)
- [Embedded Bare-Metal Radar-Inertial Odometry](https://arxiv.org/abs/2610.07278)
- [embedded_rio 固件](https://github.com/ntnu-arl/embedded_rio)
- [OpenSplatGraph](https://arxiv.org/abs/2610.07569)
- [NMPP](https://arxiv.org/abs/2610.08695)
- [LBA-CBF](https://arxiv.org/abs/2610.08765)
- [QF3](https://arxiv.org/abs/2610.08789)
- [OpenWAM](https://arxiv.org/abs/2610.07922)
- [HERMES / Dev-Primitives](https://arxiv.org/abs/2610.07832)
- [Anthropic Claude Haiku 5.5](https://www.anthropic.com/claude-haiku-5-5)
- [GitHub Copilot Sandbox GA](https://github.blog/changelog/2026-10-07-local-sandboxing-for-github-copilot-now-generally-available/)
- [GitHub Copilot 本地模型发现](https://github.blog/changelog/2026-10-07-discover-local-models-in-github-copilot-cli/)
- [Tassa / Erez / Todorov 2012](https://doi.org/10.1109/IROS.2012.6386025)
