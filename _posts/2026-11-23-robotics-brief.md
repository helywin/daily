---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-23"
date: 2026-11-23 09:00:00 +0800
description: "本期关注ScaRF-SLAM稠密视觉地图、EAGLE显式定位信念、水下全身MPC、通信感知无人机协同及VLA验证；精选本地RAG、Codex Skill评测和两条可直接使用的C++工程技巧。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-23

## 摘要

**日期：2026-11-23，星期一，Asia/Shanghai。**

本期首先按[仓库任务规范](https://github.com/helywin/daily/blob/master/robotics-brief-task-spec.md)读取[覆盖索引](https://github.com/helywin/daily/blob/master/robotics-brief-covered-items.md)，与原有 **1,441 条**记录联合去重，优先检查最近 24 小时，再扩展到七天及具备工程价值的历史代码。可核实的 [arXiv cs.RO 最新常规公开列表](https://arxiv.org/list/cs.RO/new)与[cs.SE](https://arxiv.org/list/cs.SE/new)均为**2026-11-20（星期五）**，分别有 140 条总条目／79 条新提交、39 条总条目／20 条新提交。由于周末没有新的常规公开批次，本期不把旧论文冒充为 11 月 23 日首发。

**工程优先级：**
- **SLAM：ScaRF-SLAM** 把成熟 VIO/视觉定位与神经稠密重建解耦，公开完整代码和 LiDAR 真值数据，但 GPL-3.0 商用受限；
- **定位与规划：EAGLE、ST-RCP** 分别以显式空间信念代替长序列隐式定位状态、联合预测无人机通信盲区与临时中继；
- **控制：可微水动力 MPC** 将 CFD 学到的力场压缩为可解析求导的控制模型；
- **VLA：VG-Steer、WEVO、Verify2Act、RoC** 分别对应冻结策略测试时纠偏、视频世界模型后训练、执行前验证、按事件触发高层推理；
- **AI 组件：agent-skill-eval、mcp-local-rag** 分别验证 SKILL.md 是否真正提高 Codex 完成率、为本地文档提供混合检索；
- **Codex 实操：CTest 反复检测间歇性失败；Git sparse-checkout 缩小大型工作树。**

本期八项主动态中，**七项为 2026-11-18 至 19 UTC 首次提交的“时间回补”**；ScaRF-SLAM 为 **2026-05-29 原始预印本的“工程补充回顾”**，因为其真实开源实现和多会话几何一致性对 SLAM 开发更有直接价值。主动态的机器人性能均按作者特定任务、设备、数据及评测协议描述，未将模型延迟误称为闭环控制实时性。

## 1. ScaRF-SLAM：成熟视觉定位负责跟踪，几何基础模型只负责稠密重建

**时间性质：工程补充回顾。原始预印本 2026-05-29；IEEE RA-L 2026，非今日首次发布。**

### 为什么重要

把 Depth Anything 等几何基础模型的预测深度直接加入定位残差，容易使深度尺度不准或视角变化产生的几何错误污染相机位姿。ScaRF-SLAM 不让几何基础模型主导 Tracking：传统视觉 SLAM/VIO 输出低延迟相机位姿，GFM 只为关键帧提供深度／稠密表面，随后通过关键帧尺度与子地图尺度优化提高一致性。这与“先保证可定位，再扩展稠密语义地图”的机器人产品架构相符。

### 算法模块与传感器假设

1. 单目、双目或多相机视觉 SLAM（可附 IMU）提供已估计的关键帧位姿；
2. 将选中的图像视图输入几何基础模型预测深度，关键帧形成局部子地图；
3. 通过帧内及子地图间尺度优化对齐几何，并投影融合深度点；
4. 回环或 VIO 后端更新位姿后，重算相关子地图几何，而非让错误深度反推主定位。

论文使用 LiDAR 高精度真值评测，但**算法本身是视觉稠密建图而不是 LiDAR LIO 前端**。仍需要良好的相机内外参、几何重叠、光照与位姿质量；薄玻璃、动态物体和纹理差会破坏神经深度／视觉轨迹。关键帧尺度被约束，不等于所有绝对尺度错误自动消失。

### 实验、实时性与风险

作者报告建筑级室内数据中每 10 m 子地图约 2 cm 重建误差，室外每 30 m 区块约 10 cm，相比所选基线改善约 10–20% 的重建精度。这些是指定真值／对照，**不是机器人的长期重定位精度或控制 P99**。大模型深度推理和在线子地图融合会增加 GPU 占用，需要分别量化 Tracking P95、Mapping 队列延迟和内存增长。

### 复现状态、适合谁关注与落地启发

**已核实官方代码及说明，未实际编译。** [ori-drs/ScaRF-SLAM](https://github.com/ori-drs/ScaRF-SLAM) 提供 GPL-3.0 实现、[部署 Wiki](https://github.com/ori-drs/ScaRF-SLAM/wiki)、[多会话使用说明](https://github.com/ori-drs/ScaRF-SLAM/wiki/5.-%F0%9F%94%80-Multi%E2%80%90Session-Mapping)及 [ScaRF 传感器数据](https://github.com/ori-drs/ScaRF-SLAM/wiki/1.-%F0%9F%93%A5-Dataset)。先从官方 Wiki 环境搭建与离线重建实验开始：

    git clone https://github.com/ori-drs/ScaRF-SLAM.git
    cd ScaRF-SLAM
    # 按 Wiki 配置 Python/CUDA/GFM 权重及数据集
    # 先执行离线重建，再接入现有视觉 SLAM

适合 ROS2 上层三维重建、多相机地图、历史地图迭代。先做一份场景的姿态冻结与可更新两组 A/B，记录重建 Chamfer、相机 ATE、显存与回环重建耗时。**GPL-3.0 及第三方权重许可需单独审查，不能直接复制到闭源商业固件。**

来源：[原论文](https://arxiv.org/abs/2606.00307)、[IEEE RA-L DOI](https://doi.org/10.1109/LRA.2026.3732836)、[官方仓库](https://github.com/ori-drs/ScaRF-SLAM)。

## 2. EAGLE：从历史视觉序列改为显式空间信念的主动地理定位

**时间回补：v1 2026-11-19 UTC，arXiv:2611.25866。**

### 为什么重要

无人机在局部区域内寻找由航拍图、地面照片或自然语言描述的目标时，大 Transformer 可以从完整历史序列隐式推断位置，但序列增长、定位不确定性及执行时对大 VLM 的依赖会增加成本。EAGLE 将空间信息变成**可解释的栅格级信念张量**，而非只用长 Token 序列“记住走过哪里”。

### 算法模块、观测与可观测性

训练时，冻结 Qwen2.5-VL-7B 提供全场景上下文，Teacher Swin 分支结合它学习全局信息；Student Swin 只根据随机遮挡的局部航拍拼图、未知格子预测及不确定性监督学习。离线知识蒸馏后，丢弃大 VLM、Teacher 与上下文缓存。部署时由学生估计每个栅格的航空特征与不确定性，结合目标跨模态特征与访问掩码交给小 CNN actor-critic/PPO 选择移动。

**关键假设：**搜索区域可以合理离散为栅格，局部视图、运动/访问记录可用于更新空间信念。若基础地图粗糙、位置记忆漂移、视角极端变化，信念会偏差；它不是 GPS 或 LiDAR 实时六自由度定位替代。

### 实验与风险

作者报告 MASA、xBD 零样本迁移、MM-GAG 未见航拍目标三组平均成功率分别为 **78.1%、76.4%、76.8%**，部署阶段不需调用原大 VLM；这是指定 AGL 任务成功率，并非飞行控制器性能。论文写明源码“将公开”，本次没有核实可构建官方仓库，不提供虚构安装步骤。

### 最小验证、适合谁关注与工程启发

先在二维网格仿真中把访问历史、目标相似度、未知区域与预测不确定性明确保存为四个图层，对比“仅历史序列”“仅当前视图”“空间信念+访问掩码”的目标到达率、重复覆盖、推理时延。适合室内无人机找物、主动探索、建筑级语义搜索；可以借鉴显式状态表达，并将已有 SLAM 估计与其融合。

来源：[EAGLE 原论文](https://arxiv.org/abs/2611.25866)、[arXiv 公开列表](https://arxiv.org/list/cs.RO/new)。

## 3. ST-RCP：通信盲区预测与无人机临时中继共同决定飞行路径

**时间回补：v1 2026-11-19 UTC，arXiv:2611.25558。**

### 为什么重要

城市低空无人机飞行时，最短无障碍航线可能穿过基站覆盖盲区。给每台无人机永久配置中继机昂贵，也不能利用同区域已有航线的交会机会。ST-RCP 将配送无人机视为**可按任务空隙临时支援的通信中继**，共同优化路线、时间和通信持续性。

### 核心模块与系统边界

1. 基于有限未来时域预测任务无人机的通信丢链事件；
2. 为潜在支援机与盲区事件建立“可支援—时间冲突—能耗”兼容图；
3. 联合选择中继伙伴、调整其轨迹并调度服务顺序；
4. 对路径进行障碍、任务完成和能源预算检查，重新预测覆盖。

它强调**移动中继与任务调度**，不等同于从零创建蜂窝覆盖，不改变无人机空域法规及无线传播物理。它与此前覆盖的 CommDreamer“自身 LiDAR+SINR 世界模型规划”不同：此处重点是**多机协同临时支援**。

### 实验、适用场景与工程风险

作者在真实交通场景驱动的仿真里，在最高负荷场景报告下降阶段通信覆盖相对只用基站提升 **29.93%**；相对 1/2/3 台固定任务中继机配置分别提高 **27.38%、22.02%、15.20%**。这些不是实际空中链路测量，也不说明飞行距离与能源消耗必然更低。必须独立处理碰撞、避让、通信加密、无人机脱网自主返航与中继角色授权。

### 最小可复现与落地启发

没有核实可直接运行的官方代码。可先在二维城市地图和离散时间中，为 3–5 台无人机配置已知盲区，建立可支援时间窗与冲突边。比较“不协调”“一台固定中继”“动态中继”三种方案的断链总时长、任务延误、额外路径长度和调度 CPU P95。适合 4G/5G 联网无人机、多机巡检和紧急通信研究。

来源：[ST-RCP 原论文](https://arxiv.org/abs/2611.25558)。

## 4. 可微水动力全身 MPC：把 CFD 力场变成能在线求导的控制模型

**时间回补：v1 2026-11-19 UTC，arXiv:2611.25373。**

### 为什么重要

水下机器人如果同时拥有推进器和机械臂，将机械臂动作交给独立控制器、载体只维持姿态，会丧失它们之间的动力学协同。然而每个 MPC 时域步都实时调用高保真 CFD 基本不可行。该研究将水动力项压缩为**平滑球谐力/力矩场与耦合附加惯量**，在优化时提供解析 Jacobian。

### 算法模块与假设

离线使用 CFD 构建随方向和速度变化的水动力响应，拟合球谐系数及附加惯量；在线结合自由漂浮的“载体+机械臂”整体动力学，优化推进器力和关节扭矩。相比数值差分，这类解析梯度避免步长敏感，适于梯度型 MPC 和轨迹优化。

水流和压力条件、载体几何、机器人质量及流体动力假设变化时，拟合精度会衰减。推进器饱和、接触物体、海流扰动与模型失配必须额外考虑；**解析可微不代表具有真机稳定性证明。**

### 实验与复现

论文在独立的 Stonefish 水下仿真中做闭环全身 MPC，并用独立 CFD 测试动力学预测；摘要没有可泛化的控制频率／统一成功率，完整官方代码目前未独立核实。最低验证可先以六自由度载体和二维机械臂简化模型实现解析/有限差分梯度对比，再检查梯度误差、QP/NLP 迭代次数、MPC P95 与执行器饱和。适合可微模型控制、双层平台协调、CFD 参数辨识；对陆地轮足机器人可借鉴**离线复杂物理模型、在线轻量解析控制**的设计，而非照搬水动力公式。

来源：[原论文](https://arxiv.org/abs/2611.25373)。

## 5. VG-Steer：冻结 VLA，通过成功轨迹里的物体相对距离做测试时纠偏

**时间回补：v1 2026-11-18 UTC，arXiv:2611.25199。**

### 为什么重要

抓取动作策略在训练分布内成功，但物体稍微换一个位置或目标名称变化就可能失效。全面后训练代价大，也可能损害原有技能。VG-Steer 不修改 π0.5 或 GR00T 的参数：从一次成功的参考轨迹提取“夹爪—物体—目标容器”的**随时间变化的相对距离和投影方向**，在 Flow Matching 去噪过程中加入可微引导，使新场景尽量复现有用的物体关系，而不是机械复制绝对坐标。

### 算法、感知和实际硬件

先用 DINOv2/CLIP 检索相似的成功 Episode，VLM 选择关键实体对及需要保持的几何轴/平面；再利用图像分割、RGB-D 投影和机器人正运动学恢复实时三维关系，将其转化为去噪阶段的方向梯度。真实实验使用 UR5/Robotiq 夹爪和 RealSense，部署侧仍需要 VLM/分割服务以及足够准确的相机—机械臂外参。

### 实验与成本

[作者项目](https://arthurfenderbucker.github.io/VG-Steer/)报告在 LIBERO-Pro 上 π0.5 提升 **14.5 个百分点**，真实机械臂在训练位置外一格的放置任务成功率约 **2.1 倍**；未见目标类别场景物体混淆从 **45.8%** 降为 **4.2%**，总推理开销约 **1.2 倍**。这些是指定任务，且视觉检测与几何误差可能对梯度引导产生错误方向；**它不是硬件碰撞安全约束**。

### 已核实代码、最小实验与商业边界

**已独立核实 GitHub README 和安装命令，未本地运行。** [arthurfenderbucker/VG-Steer](https://github.com/arthurfenderbucker/VG-Steer)公开仓库给出：

    git clone https://github.com/arthurfenderbucker/VG-Steer.git policy_abstraction
    cd policy_abstraction
    cp .env.example .env
    # 配置 OPENAI_API_KEY 或 OPENROUTER_API_KEY
    uv sync
    uv run pytest -m "not slow"
    # 按 docs/SETUP.md 安装 LIBERO-PRO / 策略服务后：
    uv run python scripts/evaluate.py --env.task-suite-name libero_spatial

以上测试不保证第三方 CUDA／策略服务不需额外配置。推荐同一固定模型比较不开启、开启引导两组，记录任务成功、误抓、外参扰动、额外推理时间、人工审核动作。适合 VLA/Flow Policy 研究；闭源 VLM API 与开源本地策略**不能混称全离线**。许可证与模型权重授权需分别核查。

来源：[论文](https://arxiv.org/abs/2611.25199)、[代码](https://github.com/arthurfenderbucker/VG-Steer)、[项目与真实回放](https://arthurfenderbucker.github.io/VG-Steer/)。

## 6. WEVO：用真实部署对齐的视频世界模型，替代危险的人形真机 RL 探索

**时间回补：v1 2026-11-18 UTC，arXiv:2611.25251。**

### 为什么重要

在真实人形机器人上直接做强化学习探索，可能碰撞、跌倒或伤及设备；纯模拟训练又容易被 Sim-to-Real 差异误导。WEVO 先使用仿真中的操作和行走 Play Data 学习条件视频预测，再以少量自主真机轨迹校准世界模型，使后续强化学习主要在视频世界模型内进行。

### 模块、观测与控制假设

- 上层 VLA 产生全身任务动作；
- WBC 将动作转换为可执行的全身控制；
- Action-conditioned Video World Model 预测下一个视觉状态及任务进展；
- 使用经过部署观察修正的世界模型建立 RL 闭环，更新 VLA；
- 在真机回放进行实际任务验证。

作者每任务采集约 **20 条自主真实 Rollout**用于部署对齐，而不是全部靠从零遥操作示教。仍需依赖已存在的机器人安全控制器和重置条件。模型能生成逼真的视频，**不等于能够准确模拟接触力与失稳**。

### 作者结果与局限

在三个真实操作任务中，视频世界模型内 RL 的平均成功率由 **23.3% 提升至 75.0%**，作者所比较的真机 RL 方案为 **48.3%**。这些是相应机器人、任务、样本预算下的结果，不能推断所有人形机器人用 20 条示例均能达到相同成功率。项目页已公开，但本期没有核实完整训练仓库和权重。

### 最小对照与适用对象

先选择既有的 MuJoCo/G1 任务，留出 20 段真实或高保真状态轨迹，只评估世界模型的接触和动作响应偏差；再比较纯 Sim RL、视频 WM RL 和小规模真实闭环修正。测任务成功率、世界模型预测误差、接触失败率、GPU-hours 与安全停止次数。适合人形机器人 VLA、移动操作及 Sim2Real 研究。商业研发中应先在数字孪生上验证模型局限，不能将视频 Rollout 当成物理安全证据。

来源：[WEVO 论文](https://arxiv.org/abs/2611.25251)、[作者项目页](https://qianzhong-chen.github.io/wevo.github.io/)。

## 7. Verify2Act：VLM 先提出操作计划，潜空间世界模型与 Critic 在执行前验证

**时间回补：v1 2026-11-18 UTC，arXiv:2611.25243。**

### 为什么重要

让 VLM 直接为机械臂生成“抓、移动、放”的动作序列，语言逻辑可能正确，但物理后果却错误。逐候选生成像素级未来视频成本很高，且长时域误差容易累积。Verify2Act 在**冻结 DINOv2 特征空间**中用动作条件的世界模型预测候选计划，训练同时评价时间一致性和最终目标达成度的双头 Critic，形成执行前准入层。

### 算法与验证边界

VLM 根据观察和任务列出候选计划；V2A-WM 用 Flow Matching、动作 Cross-Attention 及因果历史窗口对每个候选在潜空间 Rollout；Critic 检查计划时序与目标满足程度，通过后才交给真实抓取/放置控制器。潜空间评估只对模型训练分布内的物理误差有效，不能推断对抗障碍、未知刚度或真实夹爪力控制必然安全。

### 量化实验

在六项语言条件操作中，作者的系统成功率 **83.3%**，相对于未加入相应结构改进的潜空间世界模型为 **61.7%**、单独 VLM **53.3%**、像素扩散模型 **46.7%**。在 CALVIN 长任务上，相对像素扩散验证约减少 **30 倍反思式 VLM 调用**。这不是全流程耗时缩短 30 倍，也没有证明真实操作零事故。论文表示实际实验失败更多由低层夹取／放置滑移造成，说明高层计划验收不能代替执行器反馈。

### 可复现性、适合谁关注与工程启发

未核实完整公开代码。可以用已有机器人 Skill 库建立最小独立验证器：每个 Skill 写出前置条件、期望后置观测和硬件失败条件；只用虚拟场景测试 VLM 方案在错误顺序、目标遮挡、抓取失败下的拒绝率。关注机械臂 VLA、可验证工具调用及多步骤 Agent；推荐“语言推理提出候选、确定性验证约束、独立物理反馈执行”的分层方案。

来源：[Verify2Act 论文](https://arxiv.org/abs/2611.25243)。

## 8. RoC / Reasoning on Call：仅在进展异常或阶段变化时调用高层推理

**时间回补：v1 2026-11-19 UTC，arXiv:2611.26341。**

### 为什么重要

频繁询问大模型“下一步做什么”，可能耗尽 Token 和网络时延；只让底层策略一口气跑完，又难以发现子任务失败。RoC 通过在线任务状态监视器，结合短期视觉序列和有序交互记忆判断当前子任务进展、下一任务阶段，并在**事件触发**时调用高层推理器。

### 技术模块

底层操作策略持续执行；状态监视器估计进展和异常，遇到任务边界、操作失败、结果不符合预期才调高层 Agent 讨论应修正动作执行还是任务计划；只有**被验证的结果**才允许推进记忆和任务状态。这与前期覆盖的 CHAC（导航 Action Chunk 重规划）主题接近，但 RoC 针对操作任务的阶段级监视与代理介入，研究对象并不相同。

### 实验、边界及适用性

RMBench 上，RoC 相比作者最强 Agent 基线成功率提升 **24.0 个百分点**、Token 消耗下降 **65.3%**；相较最强纯策略基线成功率提高 **15.1 个百分点**，并展示三项真实长时操作。均为指定任务；监视器假阴性可能导致错误动作持续执行，不能承担紧急停止。完整官方代码和离线模型方案尚未核实。

### 最小 A/B 和工程启发

以三阶段抓取—搬运—放置或 ROS2 导航—停靠—登梯流程，先写明确的“阶段完成证据”和“异常回退条件”；比较固定每 1 秒询问大模型、每 Action Chunk 询问和事件触发，记录 Token、额外延迟、失败恢复次数、真实任务完成率。适合机器人状态机、SIP 语音 Agent、长时 AI Coding；建议**先用确定性事件与状态机建立准入，不盲目增加大模型频率**。

来源：[RoC 论文](https://arxiv.org/abs/2611.26341)。

## AI / LLM 附属框架与开源工程组件

### 组件 1｜agent-skill-eval：真正跑 Codex，比对 SKILL.md 对任务完成率的净提升

**工程补充回顾；本期首次覆盖。来源：[tardigrde/agent-skill-eval](https://github.com/tardigrde/agent-skill-eval)。**

**解决的痛点：**“写了一份很长的 SKILL.md”不等于 Codex 会触发该 Skill，更不代表真实修复率上升。该 Python 工具执行含 Skill / 不含 Skill 的同一组用例，记录实际 CLI 过程，支持确定性文件状态差分、负控制（不该触发 Skill 时是否乱触发）、重复 Run 的 pass@k/pass^k、耗时与 Token、外部验证和隔离。

**模块与开源情况：**开源仓库已核实，可通过 PyPI 安装，支持 Codex CLI 实际 Harness 与隔离的 Harbor/Docker 运行后端。标准 API 模型调用并不与 Codex 订阅额度等价；真实运行 Codex 也会消耗用户的 Codex 资源。工具自带 Rubric Judge 选项可需要额外 API Key。Native Runner 并非强隔离环境，可能读到测试答案或其他工作树，正式 A/B 应选择 Harbor，避免把测试答案泄漏给 Agent。

**最低不消耗 Codex 的入口核查：**

    python3 -m venv .venv
    source .venv/bin/activate
    pip install agent-skill-eval
    agent-skill-eval --version
    agent-skill-eval list
    agent-skill-eval validate examples/write-release-notes/evals/evals.json

其中最后的 examples 路径存在于**源码检出**时；仅 PyPI 安装不应假定带有相同相对路径，需要先下载官方示例。可独立运行的最短安全探测是版本与帮助命令。**本期没有实际启动任何 agent-skill-eval 测试、没有调用 Codex。**

**对 Codex / T3 Code 的价值：**先用一个真实的 C++ 工程修复用例定义“修复前失败、修复后通过且无无关修改”，为 Skill 增加正例和负例。若获准运行 Codex，再以固定相同模型/effort/预算比较无 Skill 与有 Skill 三次以上的成功率、成本、误触发和总耗时，而不是用 LLM 打分代替真实编译。复杂度较高，适合固定复用的自研 Skill，不必为每个临时 Prompt 搭建评测系统。

来源：[README 与运行契约](https://github.com/tardigrde/agent-skill-eval)、[源代码与示例](https://github.com/tardigrde/agent-skill-eval/tree/main/examples)。

### 组件 2｜mcp-local-rag：文档混合检索本地运行，Codex 不必反复全文读文件

**工程补充回顾；本期首次覆盖。来源：[shinpr/mcp-local-rag](https://github.com/shinpr/mcp-local-rag)。**

**具体痛点：**C++/ROS2 仓库的大量架构文档、API 手册、设备说明有不同术语；纯 grep 找不到同义表达，整段文件加载又浪费上下文。该工具通过本地 Embedding 与关键字检索结合，并返回带源文件、标题、页码／行号的证据块。主要支持 PDF、DOCX、Markdown、TXT，**不是默认 C++ AST 代码索引器，也不会自动生成答案**。

**模块、许可证与依赖：**MIT 开源；Node.js **22.20+**，npm 安装和首次本地模型下载需要网络，之后可无云 API 离线文本检索。MCP 提供 sync、查询、相邻证据块读取等工具；默认嵌入模型约 90 MB，持久索引需要本地空间。多目录根与缓存路径需要主动配置，避免把私人凭据加入索引。

**最小 CLI 入口（不调用任何云模型）：**

    mkdir -p /tmp/rag-demo/docs
    printf '# SIP state\nINVITE accepted then ACK\n' > /tmp/rag-demo/docs/sip.md
    cd /tmp/rag-demo
    npx mcp-local-rag ingest ./docs
    npx mcp-local-rag query "SIP ACK confirmation"

Codex 可以在项目的 ~/.codex/config.toml 配置 Stdio MCP，明确 document root，例如：

    [mcp_servers.local-rag]
    command = "npx"
    args = ["-y", "mcp-local-rag"]
    [mcp_servers.local-rag.env]
    BASE_DIR = "/absolute/path/to/docs"

**已核实命令与源码，未实际安装或执行。** 不能把“Local RAG 检索召回更好”写成 Codex 修复成功率提高。推荐在 30 个已有答案的项目文档问题上对照 rg+read、mcp-local-rag、已覆盖的 Polaris，统计 Top-5 证据召回、正确引用率、总 Token、P95 和索引维护时间。若命中的证据带有恶意指令，Codex 仍必须把它当数据，不自动执行。

来源：[官方 README](https://github.com/shinpr/mcp-local-rag)、[Codex 接入说明](https://github.com/shinpr/mcp-local-rag#quick-start)。

## AI Coding 实战技巧精选

### 技巧 1｜用 CTest --repeat until-fail:20 捕获“偶尔失败”的 C++ 回归

- **来源**：CMake 项目维护者，[CTest --repeat 官方手册](https://cmake.org/cmake/help/latest/manual/ctest.1.html)；长期稳定功能，工程补充回顾。
- **一句话结论**：单次通过不能证明线程竞争或非确定性状态机已被修好；让 Codex 先运行 20 次相同测试，再凭真实失败轨迹改动代码。
- **具体怎么做**：
  1. 先构建并确认真实存在的 CTest 名称（例如 sip_state_machine_test）。
  2. 在稳定环境运行以下命令，保留日志与退出码：

        ctest --test-dir build -N
        ctest --test-dir build -R '^sip_state_machine_test$' \
          --repeat until-fail:20 --output-on-failure

  3. 如发生失败，交给 Codex 失败时的完整日志、输入 Seed、时间戳和测试源码，由它定位最小修改。
  4. 修复后再次跑重复测试及完整回归，核对实际退出码。
- **适合什么场景**：Codex、T3 Code、Linux、ROS2、C++、SIP 状态机、随机地图配准测试。
- **注意**：重复 20 次仍不能证明永不失败；测试必须能独立重置，不能让并行运行写入相同设备、日志或端口。该技巧与此前只重跑失败用例的 --rerun-failed **目标不同**。

### 技巧 2｜用 Git sparse-checkout 让 Codex 只看到当前需要的 Monorepo 子树

- **来源**：Git 项目维护者，[git-sparse-checkout 官方手册](https://git-scm.com/docs/git-sparse-checkout)；工程补充回顾。
- **一句话结论**：在超大 C++/ROS2 仓库中，只把本次任务涉及的目录放到独立工作树，减少无关文件干扰和扫描成本。
- **具体怎么做**：
  1. 首先检查主工作区无未提交更改；建议在独立克隆或 Worktree 使用，不修改生产工作区；
  2. 在完整 Git 元数据的仓库中建立 cone 模式：

        git sparse-checkout set src/localization include/localization tests/localization
        git sparse-checkout list
        git status --short

  3. 让 Codex 在该工作树运行限定任务，并确认 CMake/colcon 的外部依赖目录没有被漏掉；
  4. 若需要完整工程恢复，执行 git sparse-checkout disable，并做全量编译回归。
- **适合什么场景**：Codex、T3 Code、多 Worktree、C++ Monorepo、分层 ROS2 代码维护。
- **注意**：sparse-checkout 只控制本地显示哪些跟踪文件，**不是安全沙盒、不是权限隔离**，也不自动降低模型 Token。仓库包含子模块、生成代码和跨目录依赖时可能导致构建失败；只有与原基线相比的实际文件读取量／构建时间才算收益。

## 经典论文回顾

### Kimera：Real-Time Metric-Semantic Localization and Mapping（Rosinol 等，2019/2020）

**发表时间与历史位置**：[arXiv v1](https://arxiv.org/abs/1910.02490)于 **2019-10-06** 公开，2020-03-04 发布 v3；属于把实时 VIO、位姿图、网格和语义建图分层的早期系统化开源工作。论文标题为 *Kimera: an Open-Source Library for Real-Time Metric-Semantic Localization and Mapping*。

**核心问题**：只有稀疏位姿和点特征的 SLAM 很难直接为机器人规划、场景理解或重建提供带语义的三维表面。Kimera 希望在可控 CPU 计算预算下，让机器人同时保持即时位姿估计、全局一致性、3D Mesh 和语义标注。

**算法模块**：Kimera-VIO 处理视觉惯性状态估计；鲁棒位姿图后端优化长期一致性；轻量 Mesher 构建三角网格；密集几何模块通过语义图像生成带类别的三维表面。四部分可以独立运行，因而不是“一个黑盒大网络端到端解决 SLAM”。

**传感器与理论假设**：依赖标定的视觉／惯性传感器、合理的特征跟踪、同步和语义标签。大规模动态人群、光照变化及尺度误差并不会因 Mesh 存在自动消除。长时间地图维护仍需回环、状态管理与内存限制。语义预测错误可能污染地图分类，但主定位不应该无条件依赖语义类别。

**当年的工程价值**：模块化分层让“几何估计”和“语义地图”可以各自优化，不必因增加分类网络而重新实现整个 VIO 后端。这与今天 ScaRF-SLAM 的“定位保持成熟系统，神经网络服务稠密地图”形成直接对比。

**现代替代与局限**：新式 GFM/3DGS/语义基础模型提供更丰富几何与类别，但也需要额外 GPU；Kimera 侧重已标定几何与明确的优化模块，而非大规模预训练。它不是完整三路 LiDAR LIO，不能直接作为车身三雷达定位的现成替换。

**可复现性**：[论文](https://arxiv.org/abs/1910.02490)、[MIT-SPARK/Kimera-VIO](https://github.com/MIT-SPARK/Kimera-VIO)、[Kimera-Semantics](https://github.com/MIT-SPARK/Kimera-Semantics)。历史仓库依赖有自身 ROS/Ubuntu 兼容要求；本次未本地编译。最小实验：固定相同带 IMU 的相机数据，分别量化 VIO ATE/RPE、关键帧优化、Mesh 重建延迟和语义误判；再为外部已有 LiDAR 地图只增加 Mesh/语义 Sidecar，验证业务地图收益。

**对今天工程的解读**：需要独立维护“主位姿真值来源—稠密地图—语义风险图”的可信度层级。三雷达定位主线最好使用已验证的物理几何，前沿网络提供可回滚的辅助图层，不让预测地图错误反过来破坏主定位。

## 今日结论

**对 SLAM**：ScaRF-SLAM 和经典 Kimera 的共同收益不是“更多网络”，而是明确把定位、几何重建和语义层拆开，独立测量 ATE/RPE、表面误差、地图更新延迟。EAGLE 则提醒主动搜寻必须保存显式的目标概率、未访问区域和不确定性。

**对控制与规划**：ST-RCP 的通讯盲区不仅是路径成本，也是多机协同资源约束；可微水动力 MPC 说明复杂动力学可以先在离线学习、在线使用具有解析梯度的轻模型。两者都需要明确执行器／网络断连的独立安全退化。

**对机器人 Agent**：VG-Steer 是较完整的可运行开源工程，可优先研究冻结模型的测试时纠偏；WEVO、Verify2Act 与 RoC 分别改进训练环境、执行前验证和触发推理时机，但**尚未全部核实生产级代码**，不能混成一套零配置平台。

**对 Codex**：先用低成本的本地命令检查稳定性和工作树范围；当确实需要验证 Skill 是否有效时，再考虑隔离式 A/B，而不是无授权消耗 Codex 额度。mcp-local-rag 可以与 rg、Polaris 在真实文档问题上比较，不应把更多 MCP 当成最终目标。

## 最值得深入研究或尝试复现的方向

| 优先级 | 方向 | 最小验收指标 | 开源状态 |
|---|---|---|---|
| P0 | ScaRF-SLAM | 同数据 Tracking ATE、Mesh Chamfer、GPU/CPU P95 | 已核实 GPL-3.0 仓库和 Wiki |
| P0 | VG-Steer | LIBERO 原模型/引导成功率、误抓、推理开销 | 已核实运行入口，需外部模型服务 |
| P0 | CTest 反复失败检查 | 20 次失败概率、第一次失败日志、完整回归 | Git/CMake 原生工具 |
| P1 | mcp-local-rag | Top-5 证据召回、Token、端到端耗时 | 已核实 MIT、无云 API 必需 |
| P1 | EAGLE | 网格信念、重复覆盖、目标发现、推理 P95 | 论文，代码承诺将公开 |
| P1 | ST-RCP | 通信断链时长、任务延迟、额外路径/能耗 | 论文，未核实官方代码 |
| P1 | Hydrodynamic MPC | 解析 Jacobian 误差、QP/控制时延、饱和 | 论文，未核实官方代码 |
| P1 | Verify2Act | 错误任务顺序拒绝率、物理失效漏判 | 论文，未核实官方代码 |
| P1 | WEVO | 20 条真实轨迹校准、WM 误差、真机失败 | 论文/项目页，完整代码未核实 |
| P1 | RoC | 高层触发次数、Token、任务成功、恢复 | 论文，完整代码未核实 |
| P1 | agent-skill-eval | Codex 有无 Skill 的真实成功率、误触发及成本 | 已核实 Harness；需授权后运行 |
| P2 | Git sparse-checkout | 工作区文件减少量、实际构建与扫描耗时 | Git 原生命令 |
| P2 | Kimera | VIO、位姿图、Mesh 及语义分层性能 | 历史公开工程 |

## 参考资料

**检索列表**：[arXiv Robotics 2026-11-20](https://arxiv.org/list/cs.RO/new)、[arXiv Software Engineering 2026-11-20](https://arxiv.org/list/cs.SE/new)。

**SLAM 与主动定位**：[ScaRF-SLAM](https://arxiv.org/abs/2606.00307)、[源码](https://github.com/ori-drs/ScaRF-SLAM)、[EAGLE](https://arxiv.org/abs/2611.25866)。

**运动规划与控制**：[ST-RCP](https://arxiv.org/abs/2611.25558)、[Differentiable Hydrodynamics](https://arxiv.org/abs/2611.25373)。

**VLA 与机器人世界模型**：[VG-Steer](https://arxiv.org/abs/2611.25199)、[源码](https://github.com/arthurfenderbucker/VG-Steer)、[WEVO](https://arxiv.org/abs/2611.25251)、[Verify2Act](https://arxiv.org/abs/2611.25243)、[RoC](https://arxiv.org/abs/2611.26341)。

**AI 组件 / Codex**：[agent-skill-eval](https://github.com/tardigrde/agent-skill-eval)、[mcp-local-rag](https://github.com/shinpr/mcp-local-rag)、[CTest](https://cmake.org/cmake/help/latest/manual/ctest.1.html)、[Git sparse-checkout](https://git-scm.com/docs/git-sparse-checkout)。

**经典论文**：[Kimera](https://arxiv.org/abs/1910.02490)、[Kimera-VIO](https://github.com/MIT-SPARK/Kimera-VIO)、[Kimera-Semantics](https://github.com/MIT-SPARK/Kimera-Semantics)。

**核验说明**：来源为原始论文、作者项目或维护者文档；已核实 GitHub 仓库与列出的最低入口，但**没有在本次研究中实际编译、执行测试、训练大模型或调用 Codex**。