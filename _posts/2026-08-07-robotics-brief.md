---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-07"
date: 2026-08-07 09:00:00 +0800
description: "最新批次重点关注人形机器人四模态鲁棒里程计、足式学习本体里程计、原始点云安全走廊、多机器人联合强化学习、全身世界动作模型、Isaac Sim 模糊测试以及 Coding Agent 检索与技能供应链安全。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-07

## 摘要

arXiv Robotics 在 2026 年 8 月 7 日最新公开批次中列出 42 条记录。本期已先读取 `helywin/daily` 的 `robotics-brief-covered-items.md`，与截至 8 月 6 日的 239 条历史记录进行标题、arXiv ID、项目页和代码仓库联合查重，最终选择 8 条此前未完整报道的主动态。今天不需要用 7 天或更早窗口凑数，8 条主动态均来自 8 月 7 日最新公开列表或同日 Software Engineering 最新批次。

本期最值得关注的四条技术主线是：

1. **状态估计开始把“高频本体约束 + 低频外感知 + 模态故障切换”做成统一框架。** KILVO 在人形机器人上将编码器、IMU、LiDAR、相机统一进异步—顺序混合 ESIKF，并在外感知失效后继续退化运行；TRACE 则走另一条路线，只依赖 IMU 与关节历史，用学习式注意力隐式处理接触不可靠问题。
2. **实时规划继续向原始传感器数据靠近。** PathCover 直接从原始点云沿参考路径生成凸安全走廊，减少 ESDF/体素预处理和优化式区域膨胀的成本，对高频 LiDAR 局部规划很有现实价值。
3. **机器人学习正在把传统搜索、控制器和世界模型重新组合。** SJRL 将 RL 与单步冲突搜索、Dijkstra 全局引导结合；ω-0 则不预测昂贵未来视频，而是预测紧凑视觉 latent，并输出控制器可执行的全身动作 latent。
4. **AI Coding 的工程瓶颈从“能不能写代码”进一步转向检索效率与供应链安全。** CodeGrep 表明高精度、可训练的只读检索 Agent 可以显著减少下游 Agent 的轮次和 token；恶意 Skill 文件研究则说明，未经验证的 Agent skill 本质上就是可执行供应链依赖，不能按普通提示词处理。

本次核验的 OpenAI、Anthropic、Google DeepMind 和 Meta AI 官方发布源中，没有发现 8 月 7 日新发布且技术重要性足以挤进本期前 8 条的通用大模型或代码基础模型，因此本期不使用旧模型发布补位。

## 1. KILVO：1 kHz 人形机器人运动学—惯性—LiDAR—视觉统一里程计，并支持传感器故障退化

**公开时间：2026-08-07 最新 Robotics 批次；论文 v1 提交于 2026-08-06。**

KILVO（Kinematic-Inertial-LiDAR-Visual Odometry）面向人形机器人，把关节编码器、IMU、LiDAR 和相机放进一个异步—顺序混合 Error-State Iterated Kalman Filter。IMU 负责预测；腿部运动学以高频异步方式更新；LiDAR 先通过 point-to-plane 几何残差更新；视觉随后通过 frame-to-map photometric error 再更新一次。系统还加入数据健康检查和 modality switcher，使某一传感器中断时可以重组估计链，而不是让整个紧耦合系统直接崩溃。（[论文](https://arxiv.org/abs/2608.05647)，[代码与数据](https://github.com/JixinGao/KILVO)，[IEEE DOI](https://doi.org/10.1109/TMECH.2026.3721778)）

### 为什么重要

很多多模态状态估计论文的“鲁棒”主要是给异常残差降权，但真实机器人更棘手的是**数据流直接消失**：相机线缆松动、LiDAR 因碰撞重启、编码器短时丢帧。KILVO 的价值在于把“测量退化”和“模态中断”都当作系统设计的一部分。

对人形和四足平台尤其重要，因为腿部运动学可以提供非常高频的短时约束，但它会受触地、打滑、关节间隙和结构柔性影响；LiDAR/视觉能抑制长期漂移，却频率更低、计算更重。异步融合比强行把所有数据同步到同一频率更贴合真实硬件。

### 算法模块

- IMU 高速状态传播；
- 1 kHz 腿部运动学异步 ESIKF 更新；
- 接触脚速度、位置和高度多重残差；
- 基于 impact deviation 的运动学协方差自适应；
- 10 Hz LiDAR point-to-plane 顺序更新；
- 稀疏视觉 frame-to-map photometric update；
- 统一 hash-indexed voxel map；
- 利用冲击偏差与地面 patch 的无额外传感器接触估计；
- 数据健康检测、模态切换和状态缓存。

### 传感器假设

论文假设各传感器刚性安装且外参预先标定，IMU 坐标系与机器人 body frame 重合。真实 G1 数据使用 Livox MID360 10 Hz、其内置 IMU 200 Hz、Unitree 编码器 1 kHz，以及 10 Hz Hikvision 或 RealSense D455 相机。

这种设计降低了严格全局同步要求，但“无需统一时间对齐”不等于时间戳可以随意漂移；高速人形运动中，设备时钟偏移、相机曝光时间和扫描去畸变仍必须工程上受控。

### 实时性

论文报告完整四模态流程平均处理时间约 14 ms，同时维持 1 kHz 状态输出；单次运动学处理通常低于 0.2 ms，LiDAR 部分一般低于 10 ms，视觉部分约 5 ms。高频输出来自异步运动学更新，并不意味着完整 LiDAR+视觉优化每 1 ms 执行一次。

### 鲁棒性

在一个超过 9 分钟的故障注入实验中，相机在 350 s 后永久失效，系统从 KILV 退化到 KIL；500 s 后 LiDAR 也永久失效，继续以 Kinematic-Inertial 模式运行到结束。完整模态端到端平移误差约 0.0130 m，而长期失去外感知后的误差增至约 0.3338 m，说明“不断线”与“长期无漂移”仍是两回事。

编码器短时失效时，系统还能继续依靠 LiDAR/视觉定位，但输出率会从 1 kHz 降到约 10 Hz，编码器恢复后再重新加入运动学约束。

### 可复现性与风险

代码和数据集已经公开，可复现性较高。主要风险包括：

- 仍属于 odometry，没有真正解决长期回环和全局图优化；
- 视觉直接法受曝光、反光、低纹理影响；
- 腿部运动学误差可能来自结构柔性而非简单高斯噪声；
- 接触估计依赖地图地面 patch，在极端不平整或松软地面上可能失效；
- 外感知长时间中断后，系统虽可运行但会积累明显漂移；
- 多模态重入时必须关注状态协方差是否与真实误差一致。

### 适合谁关注

适合人形、四足、轮足机器人状态估计，以及正在融合 MID360、IMU、编码器、相机且希望实现传感器故障降级的团队。

### 工程落地启发

比起直接照搬 KILVO，更值得复制的是它的**不同频率、不同可信度、可失效的模态管理方式**：

1. IMU/轮速或运动学负责高频传播；
2. LiDAR 负责主几何约束；
3. 视觉只在有明显增益时参与；
4. 每种模态都有 health state，而不是只有 residual weight；
5. 故障后明确切换 estimator mode；
6. 恢复时先做创新量和协方差一致性检查，再重新紧耦合；
7. RTK、反光标志和回环仍放在更低频全局因子图中。

## 2. TRACE：只靠 IMU 与关节编码器，用足端注意力学习“不可靠接触”下的高速本体里程计

**公开时间：2026-08-07 最新 Robotics 批次；论文 v1 提交于 2026-08-06。**

TRACE（Tokenized Robust Attention for Contact-Aware Estimation）是一套端到端学习式 proprioceptive odometry。它不依赖相机、LiDAR 或显式足底力阈值，而是从最近一段 IMU 和关节测量历史中直接预测相对位移、相对旋转和 body-frame velocity。核心结构是 foot-aware cross-attention：各腿的运动学 token 与 IMU token 动态加权，由网络自己判断当前哪条腿的信息可信。（[论文](https://arxiv.org/abs/2608.05975)）

### 为什么重要

经典腿式状态估计的困难并不在于写出正运动学，而在于“脚是否真的可以当作静止世界锚点”。草地、碎石、软垫、侧滑、快速跑动都会让二值 contact/slip threshold 变得脆弱。

TRACE 的思路是把**接触可信度从手工门限变成时序表示学习问题**。这不是替代 LiDAR/VIO 的全局定位，而是很适合作为外感知短时失效时的高频 backup odometry，或者给 LIO/VIO/FGO 提供独立本体约束。

### 算法模块

- IMU 与关节历史窗口编码；
- leg-wise kinematic token；
- foot-aware cross-attention；
- 相对位置、相对旋转和 body velocity 联合输出；
- 直接监督损失；
- 运动学一致性和状态传播一致性的 physics-inspired auxiliary loss；
- policy randomization 降低对单一 gait controller 的过拟合；
- sim pretraining 后只微调部分时序编码器和预测头。

### 传感器假设

部署只需要机载 IMU、关节编码器和机器人运动学模型，不需要 LiDAR 或相机。论文在 Raibo2 上记录 500 Hz IMU 与关节状态。

但模型仍隐式假设训练数据覆盖足够多的步态、接触模式和结构动力学。更换机器人尺寸、减速器、足端材料或控制器后，token 分布会发生明显变化。

### 实时性

在 Intel Core Ultra 7 255H CPU 上，batch size 1 连续运行 10,000 个样本，平均单步推理延迟为约 `0.2774 ± 0.0188 ms`，理论上足以支撑 500 Hz 在线运行。模型规模约 0.2M 参数，明显小于文中 1.4M 参数的 Legolas 对比模型。

### 鲁棒性

真实室内测试覆盖平地、粗糙、湿滑和软地面；室外覆盖草地、硬地、楼梯和长路线。完整室外路线中，TRACE 相对最强基线将 10 s position relative error 的 mean 和 P90 分别降低约 37.4% 与 30.7%。

需要特别注意：室外参考轨迹来自 FAST-LIO2，而且实机微调也使用了 6 段 FAST-LIO2 参考日志。因此它的真实数据阶段仍存在“外感知 teacher”依赖，不能理解为完全不需要外部高质量轨迹来构建训练集。

### 可复现性与风险

当前 arXiv 页面没有给出公开代码仓库，复现性中等。主要风险是：

- 当前没有显式输出可信度/协方差；
- 没有显式 IMU bias estimator；
- 部分真实微调可能把 FAST-LIO2 的系统误差带入模型；
- 新机器人、新足端和新控制策略仍可能需要重新适配；
- 学习模型出现 OOD 时不如滤波器容易诊断。

### 适合谁关注

适合机器狗、人形、轮足机器人，以及需要 500 Hz 级低算力本体里程计或外感知故障备份的团队。

### 工程落地启发

生产系统不建议让 TRACE 类网络单独承担全球定位。更合理的接口是输出：

- 高频 relative pose increment；
- body velocity；
- 每腿 attention/可信度；
- 最好额外训练 uncertainty head。

然后把这些量作为 LIO/VIO/因子图中的一个可降权因子。这样既利用它对滑移的非线性建模，又保留传统状态估计的可检查性。

## 3. PathCover：不建 ESDF，直接从原始点云生成 MPC 可用凸安全走廊

**公开时间：2026-08-07 最新 Robotics 批次；论文 v1 提交于 2026-08-06。**

PathCover 的核心算法 RISP（Randomized Iterative Space Partitioning）直接在原始障碍点云上构造凸多面体，并沿一条无碰撞参考路径生成连续重叠的 safe corridor。作者证明在一个温和的概率消除条件下其期望复杂度近似线性，并给出有限步终止与沿参考路径持续推进的保证。（[论文](https://arxiv.org/abs/2608.05586)，[代码](https://github.com/kunalnk123690/PathCover)）

### 为什么重要

很多无人机和机器狗规划栈是：

`点云 → voxel/ESDF → 路径 → 区域膨胀 → 多项式/MPC`

其中安全走廊膨胀常常成为高密点云下的延迟尖峰。PathCover 把 corridor generation 直接放到 point cloud 上，避免为“生成凸区域”这一步先构造完整距离场。

更重要的是，它生成的凸多面体可以直接作为 MPC、MINCO、Bezier 或其他轨迹优化器的线性空间约束，因此是一个很清晰的可插拔模块。

### 算法模块

- 输入原始 2D/3D 障碍点云与无碰撞 reference path；
- 沿路径选取 seed；
- 随机迭代空间分割，持续排除障碍点；
- 用 half-space 构造凸 polytope；
- 连续生成相互重叠 corridor；
- 减少不必要 polytope 数量；
- downstream planner 在 corridor 内做动力学轨迹优化。

### 传感器假设

输入可以来自 LiDAR 或深度传感器，本身不依赖特定定位算法。但它假设：

- 点云已经位于一致局部坐标系；
- reference path 本身无碰撞；
- 机器人 footprint/安全半径已被正确考虑；
- 传感器漏检区域不能被误当成自由空间。

因此，RISP 的几何安全性不能替代未知空间管理和定位不确定性膨胀。

### 实时性

作者在 i7-9750H 2.6 GHz、16 GB RAM 的 CPU 上完成全部测试。单多面体 dense 3D stress test 中，RISP 平均约 96.37 ms，而 Decomp、FIRI、IRIS 分别约 279.32 ms、656.26 ms、35.6 s。

更有工程意义的是闭环实体机器狗实验：在约 2.6 万到 15 万点的实时点云上，路径规划加 corridor generation 平均约 2.93 ms，最慢约 7.08 ms，并且仿真到真实硬件没有修改核心算法。

### 鲁棒性

PathCover 的速度来自更直接的随机几何切分，因此生成区域通常比 FIRI 更保守。保守并不一定是坏事：对高频重规划而言，略小但稳定、便宜的 corridor 往往比巨大但需要几十到几百毫秒优化的区域更有价值。

真正风险是传感器噪声、稀疏远距离点和动态障碍。如果点云中没有障碍点，算法不会凭空知道那里是否安全。

### 可复现性与风险

完整 C/C++ 代码已公开，可复现性较高。落地风险包括：

- 仍依赖上游 reference path；
- 动态障碍需要预测后进行时空膨胀；
- 点云 outlier 会切碎 corridor；
- 漏检会导致错误放大自由空间；
- 定位协方差、控制跟踪误差和机器人真实体积需要显式加入安全余量；
- 对飞行器还必须叠加速度、加速度、jerk 和制动距离限制。

### 适合谁关注

特别适合 MID360 无人机、机器狗和 AGV 的局部规划，以及当前已经发现 FIRI/IRIS/ESDF corridor generation 占用明显 CPU 时间的系统。

### 工程落地启发

可以直接尝试：

`MID360 去畸变点云 → 局部 JPS/A* 路径 → PathCover → MINCO/MPC → 飞控/底盘`

并把安全半径写成：

`机器人几何半径 + 定位 3σ + 控制跟踪误差 + 动态障碍预测误差`

这样比固定膨胀一个经验值更容易解释。

## 4. SJRL：RL 不再单独“学会避碰”，而是和 Causal PIBT、Dijkstra 联合解决仓储多机器人长期调度

**公开时间：2026-08-07 最新 Robotics 批次；论文 v1 提交于 2026-08-06。**

这项工作研究更贴近真实仓库的 Lifelong Multi-Agent Path Finding with Rotations（LMAPF-R2）：机器人不仅不能碰撞，还要考虑 in-place rotation 和更严格的 robust safety constraint。SJRL（Search-Aided Joint Reinforcement Learning）没有让神经网络从零学习所有协调规则，而是用 Causal PIBT 做单步冲突搜索，再让 RL 同时学习 agent policy 与 environment policy；后者学习图边 cost，并通过 backward Dijkstra 提供全局引导。（[论文](https://arxiv.org/abs/2608.05588)）

### 为什么重要

多机器人规划中，纯搜索在高密度、持续重新派单时容易计算爆炸；纯 RL 又容易出现“平均上有效、边界情况下撞车或死锁”。SJRL 更值得关注的不是某个 PPO trick，而是**把硬结构留给搜索，把长期交通组织交给学习**。

这是一个很通用的机器人控制设计原则：让学习优化启发式和代价，而不是让学习模型替代所有安全与组合约束。

### 算法模块

- LMAPF-R2 图模型；
- 神经 agent policy；
- Causal PIBT 单步搜索处理局部冲突与意图传播；
- robust safety constraint 在动作选择阶段强制检查；
- environment policy 学习图 edge cost；
- backward Dijkstra 生成全局方向引导；
- PPO 进行 agent/environment 联合训练；
- expert edge-cost initialization 可作为训练先验。

### 动力学与环境假设

系统主要在离散图上规划，机器人执行层需要把离散 move/rotate/wait 转成真实轨迹。真实实验借助 OptiTrack 定位，并使用 P3GASUS 处理执行扰动和控制误差。

因此它尚不是“仅靠机载定位的完整仓库系统”；真实部署还需要 AMR 自定位、局部避障、通信超时和紧急停车层。

### 实时性

训练服务器使用 64 vCPU、4 张 RTX 4090D 24 GB；每张地图 warm-up 训练约 3 小时，联合训练约 6 小时。论文报告平均每 timestep 推理时间低于 0.05 s。

### 鲁棒性与实体结果

混合现实仓库使用 8 台实体机器人和 248 台虚拟机器人。论文报告 throughput：NORL 约 0.72、SERL 0.84、SARL 0.87、SJRL 1.01。

不过，论文也发现 expert guidance graph 初始化能显著改善训练，从零训练的 SJRL 仍可能陷入 PPO 的局部最优。这意味着环境 cost 学习并没有完全消除人工交通规则的价值。

### 可复现性与风险

论文给出较完整训练细节，但主页面没有直接列出稳定公开仓库链接，可复现性中等。主要风险是：

- 图离散化可能忽略连续动力学；
- mocap 实验不能直接代表自主定位仓库；
- PPO 对初始 edge-cost 和地图分布敏感；
- 通信丢包和执行延迟需要另做鲁棒化；
- 高密度系统必须保留独立碰撞安全层。

### 适合谁关注

适合仓储 AMR、机器人车队、持续任务分配和多机器人路径规划团队。

### 工程落地启发

对真实项目，更值得采用“学习代价图”而不是“学习直接速度”：

- 传统规划器继续保证基本可行性和碰撞约束；
- RL 学习某条巷道此时应该更贵还是更便宜；
- 交通方向、拥堵、充电区和任务优先级都可以进入 edge cost；
- 这样学习模块失效时，可以退回默认固定代价图。

## 5. ω-0：不预测未来视频，预测未来视觉 latent，让一个模型完成 11 类人形机器人边走边操作任务

**公开时间：2026-08-07 最新 Robotics 批次；论文 v1 提交于 2026-08-06。**

ω-0 是面向人形机器人 concurrent loco-manipulation 的 latent predictive world-action model。输入语言指令、当前视觉和本体状态，输出 controller-compatible whole-body action latent。与视频世界模型不同，它不要求重建完整未来 RGB，而是预测紧凑的 future observation embedding，再用 diffusion 生成全身动作 latent。（[论文](https://arxiv.org/abs/2608.06375)，[项目页](https://gentlefress.github.io/OMEGA-0_page/)）

### 为什么重要

人形“边走边操作”真正困难的是 locomotion、躯干、双臂、手和视角变化之间强耦合。把走路交给一个 controller、抓取交给另一个 policy，再用状态机拼起来，很容易在移动操作边界上失效。

ω-0 的工程上有价值之处有两个：

1. **动作接口不是原始电机力矩，而是控制器可执行的 whole-body latent**，仍保留底层稳定控制；
2. **世界预测在 latent 空间完成**，部署时不用渲染未来视频，明显减轻闭环推理负担。

### 算法模块

- FAST whole-body action tokenizer；
- Qwen3-VL-2B-Instruct 作为 action-aware VLM；
- V-JEPA 提取视觉 latent；
- T5 语言编码；
- future-aware query 预测未来视觉表示；
- diffusion transformer 生成 whole-body action latent；
- SONIC controller 将 latent 转成真实全身控制命令；
- receding-horizon action chunk 与 RTC-style warm start。

### 传感器与数据假设

支持 egocentric RGB、exocentric RGB 和 exocentric depth，以及 robot proprioception。作者收集的 ω-HOME 包含 40.3 小时、4,827 个 episode、24 类任务、30 Hz 同步多视角与机器人状态数据。

这类方法仍高度依赖视觉质量、机器人硬件一致性和 controller action latent 的定义，不是换一台人形机器人就能零成本迁移。

### 实时性

真实机器人部署时单次 forward 约 0.14 s，即略高于 7 Hz。模型一次预测长度 `H=25` 的 action chunk，但只执行前 `K=8` 步便重新获取图像并规划，因此属于 receding-horizon 策略而非一次性开环执行整段动作。

### 鲁棒性与真实结果

11 类真实家庭任务中，统一模型 ω-0 Omni 报告约 81.8% success rate、90.3% task progress；加入额外 ω-HOME pretraining 后 success rate 进一步到约 82.4%。同一评测下，论文中的 π0.5、InternVLA-M1、GR00T-N1.7 等基线明显较低。

但这些结果全部是在作者的数据、机器人、控制器和任务协议内比较，不能直接外推为通用人形基础模型能力。

### 可复现性与风险

项目页已公开，但完整训练依赖 8 张 H100，且需要大量真实人形数据、动作 tokenizer 与底层 SONIC controller，复现门槛高。

主要风险：

- 7 Hz 高层策略仍需要可靠低层控制器兜底；
- 没有形式化碰撞或稳定性保证；
- 相机遮挡、强光和长时任务误差会积累；
- action latent 与硬件绑定较强；
- 任务成功率高不代表异常情况下会安全失败。

### 适合谁关注

适合 VLA、世界模型、人形全身控制和 loco-manipulation 团队。

### 工程落地启发

目前最值得复制的不是完整模型，而是它的接口设计：

`语言/视觉 → 中低频全身动作 chunk → 传统全身控制器 → 关节闭环`

学习策略不直接取代 500 Hz–1 kHz 的低层控制，这比端到端直接输出电机命令更适合真实设备。

## 6. IcFuzz：第一次系统性对 Isaac Sim 做语义引导模糊测试，4 个月找到 11 个 Bug

**公开时间：2026-08-07 最新 Robotics / Software Engineering 批次；论文 v1 提交于 2026-08-06，已被 ASE 2026 接收。**

IcFuzz 针对 Isaac Sim 的复杂 Python/Omniverse API 做 fuzzing。普通随机参数变异很容易生成大量语义无效的仿真程序，因此它先用 LLM 把 seed script 分成有语义的仿真阶段，再按对象、API 和参数层级做 context-aware mutation，最后用 multi-armed bandit 根据反馈动态选择更有效的 mutation operator。（[论文](https://arxiv.org/abs/2608.06088)，[ACM DOI](https://doi.org/10.1145/3832783.3837550)）

### 为什么重要

sim-to-real 经常把“仿真器”默认为可信基础设施，但 Isaac Sim 本身也是一个巨大的软件系统。如果 physics API、sensor API、生命周期或 USD object 状态存在 bug，RL/VLA 训练结果可能建立在错误世界之上。

因此机器人 CI 不应该只测试自己的 policy 和 ROS 节点，还应该测试**仿真环境本身在当前版本、扩展组合和场景脚本下是否稳定**。

### 算法模块

- 收集 Isaac Sim seed scripts；
- LLM semantic stage segmentation；
- 根据阶段上下文选择合法对象；
- object/method/argument 等多层 mutation；
- coverage/crash 反馈；
- multi-armed bandit 自适应调度 mutation operator；
- crash 去重与 bug triage。

### 实时性与结果

在三轮、每轮 12 小时的测试中，IcFuzz 的 code coverage 达到基线约 190%–205%，平均发现约 3.7 个 unique crash，而基线没有发现 crash。作者约 4 个月共找到 11 个 bug，其中 9 个被开发者确认或修复。

这是离线软件测试工具，不是机器人控制环算法，因此“实时性”指标应理解为 fuzz throughput、coverage 和 crash yield，而不是毫秒级推理延迟。

### 鲁棒性、可复现性与风险

论文声明提供 replication package，但 arXiv HTML 中的 artifact 引用当前显示不够清晰，因此现阶段可复现性为中等，而不是仅凭“released”就判定很高。

主要风险：

- LLM 分段本身可能漏掉语义结构；
- fuzzing 找到 crash 不等于发现物理模型数值错误；
- Isaac Sim 闭源底层组件限制根因分析；
- 每次大版本升级都可能改变 API 和 mutation space；
- 长时间 GPU fuzzing 需要独立机器，不能和正常训练抢资源。

### 适合谁关注

适合 Isaac Sim / Isaac Lab、机器人仿真基础设施、sim-to-real 和测试平台团队。

### 工程落地启发

对于正在大量使用 Isaac Lab 的项目，可以建立两层 CI：

- 每次提交：跑固定的 deterministic smoke scenarios；
- 每晚：对自己实际使用的 sensor、robot、USD 和 reset/step API 做 2–8 小时定向 fuzz；
- Isaac Sim 升级前后比较 crash signature、sensor shape、physics invariant 和 deterministic replay；
- 对训练关键 API 做白名单版本锁定。

## 7. CodeGrep：把“在仓库里找对文件”单独训练成 14B RL Agent，下游 Coding Agent 少 15% 轮次、19% token

**公开时间：2026-08-07 最新 Software Engineering 批次；论文 v1 提交于 2026-08-06。**

CodeGrep 把 repository retrieval 从 Coding Agent 的隐式能力拆成一个独立的、只读的检索 Agent。模型基于 Qwen3-14B-Instruct，工具只有 `grep`、`glob` 和 `read`；每轮最多并行发出 8 个调用，最多 3 轮探索加 1 轮回答。训练采用 GRPO，并从约 67K 条公开 OpenHands 轨迹中自动挖掘“哪些文件最终真的有用”的监督信号。（[论文](https://arxiv.org/abs/2608.05886)）

### 为什么重要

真实 Coding Agent 很多 token 并不是花在写代码，而是浪费在：

- 反复 grep；
- 打开错误文件；
- 顺着错误调用链阅读；
- 把无关上下文塞给主模型；
- 修改后才发现根因在别处。

CodeGrep 证明“检索”值得成为独立可训练角色，而不是让最贵的 coding model 一边规划、一边搜索、一边写代码。

### 算法模块

- Qwen3-14B 检索策略；
- read-only `grep/glob/read` tools；
- 每轮并行 tool calls；
- CATM 从历史 Agent trajectory 挖 relevance labels；
- Git bare clone + worktree 构建轻量 rollout sandbox；
- GRPO 训练检索策略；
- 输出候选文件列表后注入冻结的 OpenHands coding agent。

### 工程结果

在 SWE-Bench Verified 500 个任务上，冻结下游 Agent 的 baseline resolve rate 为 25.8%，CodeGrep 提升到 27.0%，绝对提升 1.2 个百分点；更重要的是，在已解决任务上平均轮次减少约 15%，token 减少约 19%。

论文还观察到明显的“检索精度阈值”：BM25 file precision 约 0.375 时反而拖累 Agent；Jina 约 0.445 基本中性；CodeGrep 约 0.677 后才开始稳定换来下游效率。这说明**给 Agent 更多上下文不一定更好，错误上下文本身就是成本和噪声**。

### 是否适合接入真实研发流程

适合，而且最安全的部署方式正是论文这种“只读前置 Agent”：

1. retriever 只有 read 权限；
2. 输出固定 schema 的候选文件；
3. 主 Coding Agent 再决定是否修改；
4. retriever 与 editor 使用不同权限和上下文；
5. 用真实内部历史 PR/Issue 训练或评估 repository relevance。

这比直接给一个大 Agent 全仓库 shell 权限更容易治理。

### 可复现性与风险

论文声明将模型、CATM、RL 环境和评测 harness 全部开放，但当前 arXiv 页面没有稳定暴露独立项目仓库链接，因此实际复现前仍需确认 artifact。

工程风险包括：

- 14B retriever 对小仓库可能成本过高；
- SWE-Bench 的 issue 分布不等于企业内部 monorepo；
- 只返回文件列表仍可能漏掉配置、生成代码和跨仓库依赖；
- 低 precision retriever 会比不检索更差；
- 必须用 end-to-end bug fix 成功率验证，而不能只看 retrieval recall。

### 适合谁关注

适合 Codex/Claude Code/OpenHands 类工作流、自建 Coding Agent、超大 monorepo 和多 Agent 软件研发平台。

### 工程落地启发

即使不训练 14B 模型，也可以立刻复制其系统边界：

`Issue → 只读检索 Agent → 5~20 个候选文件 → Coding Agent → 测试/验证`

再记录“最终补丁实际修改/引用了哪些文件”，形成自己的 trajectory relevance 数据，为后续训练轻量 retriever 做准备。

## 8. 恶意 Skill 文件：Coding Agent 的 skills 不能再被当作普通 Markdown，实质上是可执行供应链依赖

**公开时间：进入 2026-08-07 Software Engineering 最新批次；论文 v1 提交于 2026-08-05。**

《Towards a Risk Assessment of Malicious Skill Files in Coding Agents》研究 Agent skill/interface 带来的供应链风险：攻击者可以把危险 shell command 包装成看似正常的“环境初始化”“preflight”“依赖检查”等自然语言说明，让 Agent 在加载 skill 后主动执行。（[论文](https://arxiv.org/abs/2608.05223)，[代码与数据](https://github.com/awsm-research/AgentJailbreak)）

### 为什么重要

Coding Agent 越来越依赖：

- `SKILL.md` / rules；
- MCP 配置；
- repo-local instructions；
- 自动 setup scripts；
- marketplace skill；
- 第三方 Agent 模板。

过去大家主要防 prompt injection，但 skill 文件通常被赋予更高信任级别。如果 skill 同时能引导 Agent 调 shell、网络和凭据，它就已经不是“提示词”，而是类似 npm package、CI action 或 IDE extension 的供应链组件。

### 实验设计与结果

作者从 471 个真实 shell command 构造 2,826 个伪装 skill，覆盖 11 类 MITRE ATT&CK tactic，并在 5,629 次完整 Agent run 上评估。

在论文特定的 **auto-approved execution mode** 下，Gemini CLI 的 exploitability 约 95.5%–96.1%，Qwen Code 约 71.6%–74.0%；明确识别安全风险的 run 只有约 1.99%。

这些数字非常醒目，但不能直接理解为“所有默认 Coding Agent 都有 95% 被攻破概率”。实验刻意使用自动批准执行模式来测量 skill-interface 的最坏风险面；开启逐命令确认、沙盒、权限隔离后结果会不同。

### 突破性工程价值

最重要的结论不是某个模型谁更安全，而是**信任边界必须从模型提示词扩展到 Agent 配置供应链**。

真实研发流程应该把 skill 当代码处理：

- 来源和 commit 固定；
- code review；
- hash/signature；
- 静态分析 shell/API 调用；
- 默认 deny network/secret；
- 写文件、执行程序、访问云资源分权限；
- 不允许 skill 自己提高权限；
- 新 skill 首次运行必须人工审批；
- 执行 provenance 和命令日志长期保存。

### 可复现性与风险

作者已经公开 AgentJailbreak replication package，包含攻击样本、Qwen/Gemini runner 和评估脚本，可复现性较高。

研究本身的边界包括：

- 当前只覆盖两个 CLI Agent；
- auto-approved 模式偏向暴露最大风险；
- benchmark 主要围绕 Linux shell command；
- 企业实际风险还取决于 sandbox、网络、secret scope 和审批策略。

### 适合谁关注

所有准备把 Coding Agent 接到真实源码、GitHub、云平台、数据库、部署系统或 MCP 的团队都应关注。

### 工程落地启发

建议把 Agent skill 引入流程改成类似依赖供应链：

```text
外部 Skill
   ↓
来源/commit/hash 验证
   ↓
静态权限扫描
   ↓
隔离 sandbox dry-run
   ↓
人工批准能力清单
   ↓
只读默认运行
   ↓
按任务临时提升最小权限
```

尤其不要让仓库里一个新出现的 Markdown/skill 文件自动获得 shell + 网络 + secret 三项能力。

## 经典论文回顾

### State Estimation for Legged Robots：把接触脚位置纳入滤波状态，奠定现代腿式本体状态估计

**发表时间与历史位置：** Michael Bloesch、Marco Hutter 等人的《State Estimation for Legged Robots - Consistent Fusion of Leg Kinematics and IMU》发表于 Robotics: Science and Systems 2012，DOI 为 `10.15607/RSS.2012.VIII.003`。它是现代 legged proprioceptive state estimation 的重要奠基工作之一，在视觉/LiDAR 尚无法稳定提供高频腿式控制状态时，系统地回答了“只用 IMU 与关节运动学，如何一致地估计浮动基座状态”。（[RSS 论文页](https://www.roboticsproceedings.org/rss08/p03.html)，[DOI](https://doi.org/10.15607/RSS.2012.VIII.003)，[ETH 开放页面](https://www.research-collection.ethz.ch/handle/20.500.11850/62169)）

### 解决的核心问题

腿式机器人没有固定底盘坐标系。每一步都会经历：

- 某只脚落地成为临时约束；
- 另一只脚抬起失去约束；
- IMU 高频但会积分漂移；
- 编码器给出相对腿部几何，却不知道世界绝对位姿。

论文的关键做法是把**各接触脚在世界坐标系中的位置也作为滤波状态**，这样接触期间可以把“脚基本不动”表达成一个带不确定性的观测，而不是硬编码零速度约束。

### 关键数学思想与算法模块

- IMU 驱动浮动基座姿态、位置和速度传播；
- 关节编码器通过 forward kinematics 给出 body-to-foot 相对几何；
- 世界系 foothold position 进入 EKF state；
- 新触地点动态加入状态；
- 失去接触后对应约束被移除；
- 将接触与运动学误差作为随机变量建模；
- 使用 Observability-Constrained EKF 处理线性化一致性；
- 明确保留非线性系统本来不可观的自由度，而不是让错误线性化产生“虚假信息”。

### 传感器与动力学假设

只需要 IMU、关节编码器、机器人运动学模型和接触状态。它不依赖外部地图，也不假设地面必须是严格水平面。

但它仍假定接触脚在支撑阶段可用一个相对稳定的世界点表示。如果脚在泥地、碎石、草地或高速转向中持续滑动，约束就会系统性错误。

### 当年为什么重要

这项工作把两个后来一直影响腿式机器人估计的思想放在了一起：

1. **接触不是简单的布尔零速度条件，而应进入随机状态估计模型；**
2. **滤波器的一致性与可观测性和数值精度同样重要。**

今天 KILVO 仍然让 contact foot position 进入状态，并通过运动学残差高频更新；TRACE 虽然换成学习式 attention，本质上也仍在解决“当前哪个足端约束值得信任”这一问题。

### 今天仍然有效的思想

- IMU 高频 propagation + 运动学高频 correction；
- 接触脚作为短期世界锚点；
- 显式维护 contact uncertainty；
- 不把不可观的 global position/yaw 错当成可观量；
- 控制需要高频局部状态，而全局定位可以更低频；
- 触地与离地会改变测量模型，估计器必须显式处理 mode change。

### 已经被后续方法替代或扩展的部分

- Contact-aided Invariant EKF 通过 Lie group 结构改善一致性和线性化性质；
- factor graph / invariant smoother 更适合长窗口、异步多传感器和离线重优化；
- 现代方法对 contact covariance、slip probability 进行在线估计或学习；
- LiDAR/VIO/GNSS 被加入以约束长期 position/yaw drift；
- 人形机器人还需要处理结构柔性、双足切换、全身碰撞和更剧烈冲击；
- KILVO 类系统进一步加入多模态故障切换和地图约束。

### 公开代码、数据和可复现性

原论文有公开论文与完整数学推导，但没有发现作者维护的、可直接一键复现原始 RSS 2012 算法的官方代码仓库。因此代码层面的直接可复现性不如现代项目。

工程复现可以使用公开腿式数据集自行实现核心 EKF，也可参考后续开源 state estimator 的工程组织。例如 Pronto 提供 IMU+运动学等多源 EKF 状态估计框架，但它并不是原论文代码的逐行实现。（[Pronto](https://github.com/ori-drs/pronto-distro)）

真正需要验证的不是“轨迹看起来顺”，而是：

- NEES/NIS 是否一致；
- global yaw/position 不可观方向是否被错误收紧；
- contact transition 时协方差是否连续合理；
- 足端滑移后滤波器是否迅速降低运动学权重；
- IMU bias 与速度是否发生不可恢复耦合。

### 对当前工程项目的重新解读

今天重新看这篇论文，最重要的不是复刻 2012 年 EKF，而是把**传感器职责分层**：

```text
IMU：最高频连续传播
  ↓
轮速/腿运动学：高频短时约束
  ↓
LiDAR/VIO：中频局部无漂移约束
  ↓
RTK/反光标志/回环：低频全局约束
```

对于远置 IMU、多 LiDAR、轮速和 RTK 系统，应避免所有传感器统一当作“同等可信的位置来源”。更合理的是让每一层只纠正它真正可观、真正稳定的状态，并把异常观测通过协方差、健康状态和模式切换隔离开。

## 今日结论

今天最有工程价值的变化集中在三个方向。

第一，**腿式/人形状态估计正在出现两条互补路线**：KILVO 代表结构化多传感器滤波，把传感器频率、残差和失效模式显式建模；TRACE 代表学习式本体估计，让网络从历史运动中隐式判断接触可信度。近期最值得做的不是二选一，而是把学习式本体里程计作为传统 LIO/ESIKF 的独立辅助因子和故障备份。

第二，**规划与控制越来越强调“少做中间表示”**。PathCover 直接从点云生成凸安全区域，ω-0 不解码未来视频而只预测 latent；两者背后的共同工程原则都是：如果中间表示不是下游控制真正需要的，就不要为它付出完整计算成本。

第三，**AI Coding 正进入基础设施治理阶段**。CodeGrep 把仓库检索拆成只读、可训练的独立 Agent，说明角色拆分可以同时降成本和减权限；恶意 Skill 文件研究进一步表明，skills、MCP、repo instructions 和 setup script 都必须纳入软件供应链安全，而不能因为它们以 Markdown 形式存在就默认可信。

本期没有值得强行加入的全新通用大模型发布。相比换模型，今天更值得真实研发团队立即做的是：建立只读检索层、skill 权限门禁、仿真器版本测试和传感器故障降级策略。

## 最值得深入研究或尝试复现的方向

1. **KILVO 式多模态故障注入测试**

   在现有 LIO/轮速/RTK 或机器狗状态估计栈中，主动注入 `LiDAR 断流、IMU 延迟、编码器丢帧、RTK 跳点`，把“能不能自动降级并恢复”作为独立指标，而不只看正常数据集 ATE。记录每种 mode 下输出频率、协方差、恢复瞬态和最终漂移。

2. **MID360 点云直接接 PathCover，再交给现有 MPC/MINCO**

   不替换当前 SLAM，只替换局部 corridor generator。对比 ESDF/FIRI/PathCover 的平均延迟、P99 延迟、polytope 数量、最小净空和规划成功率，尤其测试狭窄通道和点云由 2 万增长到 20 万以上时的退化情况。

3. **Coding Agent 的“只读检索 + Skill 供应链门禁”**

   将 Agent 权限拆成 retriever/read-only 与 editor/write 两层；所有第三方 skill 在进入主 Agent 前做 commit pin、静态命令扫描、sandbox dry-run 和 capability manifest。用真实内部 Issue 统计检索 precision、最终修改文件 recall、token 成本，以及 skill 被拒绝/提权的原因。

## 参考资料

1. **KILVO**  
   - [论文](https://arxiv.org/abs/2608.05647)  
   - [代码与数据](https://github.com/JixinGao/KILVO)  
   - [IEEE DOI](https://doi.org/10.1109/TMECH.2026.3721778)

2. **TRACE**  
   - [论文](https://arxiv.org/abs/2608.05975)

3. **PathCover**  
   - [论文](https://arxiv.org/abs/2608.05586)  
   - [代码](https://github.com/kunalnk123690/PathCover)

4. **Search-Aided Joint Agent-Environment Reinforcement Learning / SJRL**  
   - [论文](https://arxiv.org/abs/2608.05588)

5. **ω-0**  
   - [论文](https://arxiv.org/abs/2608.06375)  
   - [项目页](https://gentlefress.github.io/OMEGA-0_page/)

6. **IcFuzz**  
   - [论文](https://arxiv.org/abs/2608.06088)  
   - [ACM DOI](https://doi.org/10.1145/3832783.3837550)

7. **CodeGrep**  
   - [论文](https://arxiv.org/abs/2608.05886)

8. **Towards a Risk Assessment of Malicious Skill Files in Coding Agents**  
   - [论文](https://arxiv.org/abs/2608.05223)  
   - [AgentJailbreak 代码与数据](https://github.com/awsm-research/AgentJailbreak)

9. **State Estimation for Legged Robots - Consistent Fusion of Leg Kinematics and IMU**  
   - [RSS 论文页](https://www.roboticsproceedings.org/rss08/p03.html)  
   - [DOI](https://doi.org/10.15607/RSS.2012.VIII.003)  
   - [ETH 开放页面](https://www.research-collection.ethz.ch/handle/20.500.11850/62169)  
   - [Pronto 状态估计框架](https://github.com/ori-drs/pronto-distro)

10. **最新公开列表**  
   - [arXiv Robotics](https://arxiv.org/list/cs.RO/recent)  
   - [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

11. **大模型官方发布源（本期核验但未选入主动态）**  
   - [OpenAI News](https://openai.com/news/)  
   - [Anthropic News](https://www.anthropic.com/news)  
   - [Google DeepMind](https://blog.google/technology/google-deepmind/)  
   - [Meta AI](https://ai.meta.com/blog/)