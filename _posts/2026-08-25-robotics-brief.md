---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-25"
date: 2026-08-25 09:00:00 +0800
description: "8月24日最新公开批次中，NeSAM、SRL-MPC、Neural-Primitive、Logic-VLA 与测量鲁棒 CBF 展示了物理先验、学习规划、形式化约束和状态估计误差安全过滤的融合趋势，AI Coding 则继续向可编译工作流演进。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-25

## 摘要

截至 2026-08-25 09:59（Asia/Shanghai），arXiv Robotics 最新公开批次为 2026-08-24，共 37 条；Software Engineering 同日批次共 30 条。本轮开始时已读取 `robotics-brief-covered-items.md`；索引已经包含今日 8 条主动态与 1 条经典论文回顾，共 415 条。本次对同日候选继续使用规范化标题、arXiv ID、论文页与项目页做幂等复核，没有重复追加相同记录。由于这些工作的 arXiv v1 原始提交时间主要为 8 月 20–21 日，虽然进入 8 月 24 日最新公开批次，本期仍统一标注“时间回补”，不把它们包装成 8 月 25 日新投稿。（[arXiv Robotics](https://arxiv.org/list/cs.RO/recent)，[arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)）

今天最值得关注的技术主线有四条。第一，机器人控制正在从“纯模型”和“纯学习”两端向结构化融合收敛：NeSAM 用可微 Bekker-Wong 土壤力学提供可解释的轮土作用，再用 Transformer residual 补模型缺口；SRL-MPC 则让 RL 只负责在线调 MPC 参数，真正执行的控制仍来自显式 HOCBF-MPC。第二，学习式局部规划开始直接输出控制器可执行轨迹，而不是神经网络后面再挂一个昂贵优化器：Neural-Primitive 在 MID360 + Jetson Orin NX 实机上平均规划仅 3.68 ms，模型占用约 1.38 MiB。

第三，安全层开始明确承认“状态估计会错”。Measurement-Robust CBF 不再假设安全过滤器拿到真实状态：它把估计误差集合直接纳入 CBF，学习版 NMR-CBF 在 12D 四旋翼数值实验中每步约 0.57 ms，并在 Unitree Go2 上面对最高约 18% 的里程计距离低估和额外 15 cm 偏置仍保持 10/10 安全通过。第四，VLA 和 Coding Agent 都在把自然语言的模糊性压缩到结构化约束：Logic-VLA 用 Signal Temporal Logic 在推理时指定时空安全要求；Artic 则把自然语言工作流“编译”为显式读写 artifact、约束 gate 和控制转移的可执行工作流。

大模型官方发布方面，本次核验到 OpenAI 于 8 月 24 日发布 GPT-5.6 在 Kiro 中可用的生态集成更新；由于 GPT-5.6 模型本身已在历史索引中覆盖，这不是新的基础模型发布，因此不作为完整主动态重复报道。（[OpenAI 官方](https://openai.com/index/gpt-5-6-in-kiro/)）

## 1. NeSAM：把可微土壤力学和 Transformer residual 放进同一个越野动力学预测器

**时间回补：arXiv v1 提交于 2026-08-21 17:37 UTC，进入 8 月 24 日 Robotics 最新公开批次。此前未进入去重索引。**

NeSAM（Neuro-Symbolic Kinodynamics with Soil Adaptation for Off-Road Mobility）针对越野机器人最难处理的一类模型失配：同一辆车在草地、砂土、松软地面上会出现完全不同的下陷、滑移和牵引力，固定平面运动学模型无法解释，而纯神经网络又往往需要覆盖大量土壤条件才能泛化。NeSAM 把二者拆开：用可微 Bekker-Wong terramechanics 计算物理可解释的轮土作用力，用 Transformer 建模近期车辆—地形交互历史，再用 learned residual 修正解析模型没有覆盖的轮胎、悬架与整车效应。（[论文](https://arxiv.org/abs/2608.21330)，[HTML 全文](https://arxiv.org/html/2608.21330)）

### 为什么重要

真正的价值不是“physics-informed”这个标签，而是**在线适配变量变成了可解释的土壤参数**。纯 latent adaptation 常能改善预测，但现场工程师很难判断 latent 到底代表湿度、松软度还是模型错误；NeSAM 使用 EKF 根据实际运动和预测运动的偏差在线修正土壤参数，同时冻结已经训练好的神经组件。这比在线重训整个 dynamics network 更容易限制变化范围，也更方便与风险规划器耦合。

### 算法模块

系统输入车辆状态、控制量、车体对齐的 elevation patch 与 semantic terrain patch。两个 U-Net encoder 分别编码高程与语义；soil predictor 输出六维名义土壤参数；因果 Transformer 使用最近 32 个 interaction token，对应 10 Hz 下约 3.2 s 历史。网络同时预测轮端 sinkage 和 12 维整车 residual。sinkage 与轮速、土壤参数进入可微 Bekker-Wong 模型，得到轮土力，再通过 Newton-Euler dynamics 生成物理状态增量，最后叠加 learned residual。部署时由 buffered EKF 更新 soil correction，神经网络本身不在线改权重。

### 传感器与动力学假设

论文的 terrain observation 是 128×128 elevation 与 RGB semantic patch，因此实际机器人需要可靠的局部地形几何和语义来源；状态与控制也必须同步到 10 Hz。可微 terramechanics 假设轮土接触仍能被 Bekker-Wong/相关剪切模型合理描述，遇到碎石、植被缠绕、积水或轮胎严重变形时可能出现结构性模型误差。

### 实时性与实体结果

训练数据包括 Chrono/Verti-Bench 中 500 条约 25 s 轨迹，共约 3.5 h，以及 Verti-4-Wheeler 实体平台 50 条约 30 s 轨迹，共约 25 min；采样均为 10 Hz。论文报告相对最强基线，长时域预测精度最高提升约 30%（仿真）和 29%（真实数据）；闭环在线土壤适配将相对参考轨迹的 Hausdorff distance 降低 69.4%。

### 鲁棒性、可复现性与风险

当前 arXiv 页面未给出稳定官方代码仓库。实机数据量仍较小，且物理测试场是缩比 Verti-Arena。更重要的是，EKF 只在模型定义的土壤参数空间里适配；如果真正错误来自轮胎漏气、传动故障、传感器外参漂移，系统可能把它错误解释为“土壤变了”。

### 适合谁关注

适合越野机器人、矿区车辆、巡检底盘、行星 rover，以及正在使用 MPPI/MPC 但发现动力学模型在不同地面条件下漂移很大的团队。

### 工程落地启发

不必第一步就复现完整 NeSAM。更实用的路径是：保留现有刚体/轮式动力学，在其后加入一个小 residual model；同时只开放少量有物理意义的在线参数，例如纵向/侧向滑移系数、等效摩擦或轮地刚度。先用创新量或 tracking residual 判断什么时候允许在线更新，避免把所有异常都归因给地面。

## 2. SRL-MPC：RL 不直接控制机器人，只在线调 HOCBF-MPC 的参数

**时间回补：arXiv v1 提交于 2026-08-21 14:46 UTC，进入 8 月 24 日 Robotics 最新批次。此前未进入去重索引。**

SRL-MPC（Shape-Aware Reinforcement Learned Model Predictive Control）面向异构机器人密集导航。很多 crowd navigation 方法把所有机器人都近似成圆，这在带机械臂的移动机器人、长矩形 AMR 或不同 footprint 混行时会产生过度保守或直接漏碰撞。SRL-MPC 通过 support-function transformation 构造 geometric separation features（GSF），再形成二阶 HOCBF 约束；RL policy 读取邻居的 shape-aware GSF，只在线更新 MPC 的路径跟踪、控制努力与安全距离等参数，真正执行的动作仍由显式 MPC 求解。（[论文](https://arxiv.org/abs/2608.21175)，[项目页](https://hanruihua.github.io/srl_mpc_project/)）

### 为什么重要

这是一个很典型、也很值得产品化参考的“学习器只负责调参”架构。RL 擅长从复杂邻居几何中快速判断当前应该更激进还是更保守；MPC/HOCBF 则保留动力学约束、控制边界和可解释安全结构。相比让网络直接输出速度命令，它更容易做离线审计、故障回退和上线 A/B。

### 算法模块

系统先计算机器人与邻居真实凸几何之间的 GSF，利用 support function 构建无需圆形简化的分离特征；HOCBF 将几何分离写入 MPC 约束。为提高数值可解性，论文将 HOCBF residual 以软惩罚方式进入局部 MPC。RL adapter 根据局部 crowd geometry 动态输出 MPC 参数，而不是输出控制量。训练在 15 台机器人随机凸多边形场景中完成，部署时不重训直接扩展到 20、25 台机器人和多种 OOD 几何。

### 实时性与结果

项目页报告 25 台机器人时每机器人平均 controller time 约 10.34 ms；25 机器人高密度场景中成功率约 86.7%±0.6%，而文中最强外部基线 SARL 约 21%。在 0.5 s 的 RL 参数更新延迟下，成功率仍保持 100%；但感知噪声或动作延迟增大时碰撞迅速上升，说明 RL 参数层可以低频，但状态估计和执行层不能慢。

### 鲁棒性、可复现性与风险

项目页存在，但代码仍标注 Coming Soon。真实平台演示目前还是受控室内验证，论文也明确把 uncertainty-aware neighbor prediction 与更复杂非凸几何留给未来工作。尤其要注意：shape-aware 不等于 uncertainty-aware，定位误差、通信延迟、邻居预测误差仍需要额外安全裕量。

### 适合谁关注

适合多机器人巡检、仓储 AMR、移动操作机器人、异构 fleet 和希望把 RL 接入现有 MPC 而不放弃安全结构的团队。

### 工程落地启发

对已有导航系统，最值得复制的是接口边界：RL 只输出代价权重、预测时域、安全余量或采样温度，MPC/MPPI 继续输出最终命令。然后为 RL adapter 设置硬范围和失效默认值；即使网络超时或 OOD，也能回到一组人工验证过的保守参数。

## 3. FF-MPCC：把编队保持写进 Model Predictive Contouring Control，高速时不再死追时间戳

**时间回补：arXiv v1 提交于 2026-08-21 12:56 UTC，进入 8 月 24 日最新批次。此前未进入索引。**

FF-MPCC（High-speed Agile Formation Flight with Model Predictive Contouring Control）针对多无人机高速编队中一个常见矛盾：如果每架机都跟踪固定时间参数轨迹，只要某一架因动力学限制或扰动稍微落后，其他无人机仍按时间表向前冲，编队几何就会迅速拉散。FF-MPCC 把“沿路径前进多少”作为优化变量，让每台无人机围绕路径几何而不是绝对时间进行 MPCC，同时通过重新参数化和同步动态编队形状维持相对构型。（[论文](https://arxiv.org/abs/2608.21056)，[HTML 全文](https://arxiv.org/html/2608.21056)）

### 为什么重要

它体现了 contouring control 相比传统 trajectory tracking 的核心优势：**任务目标是沿几何路径快速前进，而不是在某个绝对时刻必须出现在某个点**。对高速无人机尤其重要，因为推力饱和、风扰或邻机通信延迟都可能让严格时间跟踪变得不可行。

### 算法模块

每架无人机独立运行 MPCC，约束自身四旋翼动力学和推力边界；formation geometry 被重新参数化到公共路径进度变量；去中心化协调器根据邻机进度计算目标相对位置，从而允许编队整体在复杂路径上自动“等一等”或“赶一赶”。编队形状还可在飞行中从三角形切换为直线等动态构型。

### 实时性与实体结果

真实实验中三架 UAV 的邻居位置通过标准 Wi-Fi 以 10 Hz 共享，平均通信延迟约 15 ms。论文报告最高约 21 m/s 的高速飞行，相比时间参数化轨迹跟踪，编队保持性能提升约 65%，到达时间仍相近。

### 鲁棒性、可复现性与风险

当前未发现官方代码。论文验证的是路径已知条件下的高速编队控制，不包含未知环境中感知、避障和重新规划的全部复杂性。10 Hz 邻机状态广播在受控飞行足够，但在遮挡、多径或链路丢包时，需要显式预测邻居状态和超时降级策略。

### 适合谁关注

适合无人机编队、协同巡检、多机狭窄空间飞行，以及希望把单机 MPC 扩展为分布式 fleet coordination 的团队。

### 工程落地启发

如果当前多机系统使用“中心规划器生成所有带时间戳轨迹”，可以尝试只下发几何路径、编队关系和速度上限，让每台机本地 MPCC 决定进度。中心端只负责低频任务层，同步失败时单机仍可以减速或退出编队，而不会因为追时间戳直接打满控制量。

## 4. Neural-Primitive：MID360 + Jetson Orin NX 上 3.68 ms 的直接轨迹生成

**时间回补：arXiv v1 提交于 2026-08-21 10:13 UTC，进入 8 月 24 日最新批次；论文已被 IEEE Transactions on Industrial Informatics 接收。此前未进入索引。**

Neural-Primitive 的目标非常明确：学习式无人机局部规划不能只把后端优化换成另一个慢模型。作者先离线用 motion primitive 生成大量满足 minimum-jerk 与动力学约束的高质量专家轨迹，再训练一个极小网络直接从机载感知输入输出多项式轨迹系数。网络输出本身就是低层控制器可执行的连续轨迹，不需要再做在线搜索、投影或非线性优化。（[论文](https://arxiv.org/abs/2608.20948)，[项目页](https://zhitaoliu.github.io/neural-primitive/)）

### 为什么重要

这篇工作与“端到端控制”最大的区别是，它没有让网络直接吐 thrust 或 velocity，而是输出**带高阶连续性的轨迹参数**。训练数据来自经典 primitive planner，因此网络学到的是一个高质量规划器的近似映射；部署时把搜索成本前移到离线阶段，在线只做一次轻量推理。

### 算法模块

离线 expert 通过 free-space sampling、碰撞剔除和 constrained minimum-jerk QP 生成 primitive library，并选择面向目标的近优轨迹；网络训练后直接预测 polynomial coefficients。为减小 sim-to-real 感知差异，输入点云经过针对障碍密度的预处理和 domain randomization。部署采用 event-triggered receding horizon：飞行 0.5 m、执行时间达到上限或检测到潜在碰撞时触发重新规划。

### 传感器与平台

真实平台使用 Livox MID-360、NVIDIA Jetson Orin NX 和 PX4。Jetson 负责 end-to-end planner 与 SE(3) geometric tracking controller，PX4 负责低层姿态控制。这个平台组合对使用 MID360 的小型无人机很有参考意义。

### 实时性与实机结果

论文报告桌面计算低于 1 ms，真实机载飞行平均规划时间 3.68±0.77 ms，中位数 3.43 ms，范围约 2.71–5.94 ms；模型占用约 1.38 MiB。真实测试包括浓密植被和狭窄空间，最窄通道低于 0.8 m，而机体直径约 0.3 m，并实现零微调 sim-to-real 部署。

### 鲁棒性、可复现性与风险

当前项目页公开视频但未给出代码仓库。最大风险是“empirically collision-free”不是形式化安全保证：网络可能在训练分布之外生成穿障轨迹；另外 primitive teacher 的能力上限会固化进学生。更合理的产品化做法是保留一个极轻量的最后碰撞/动力学检查，而不是完全无验证执行网络输出。

### 适合谁关注

特别适合资源受限无人机、MID360 局部避障、狭窄通道飞行和正在比较传统 MINCO/ESDF 与学习局部规划器的团队。

### 工程落地启发

可以先把现有 planner 生成的成功轨迹当 teacher，不必自己设计新数据集。学生网络只输出 1–2 s 多项式轨迹，然后使用现有 ESDF/点云碰撞器做 0.5–1 ms 级 final gate。这样能获得神经推理速度，同时保留当前规划系统最重要的安全检查。

## 5. IMU-Free Scene Flow State Estimation：没有 IMU，也尝试从双目与电机推力恢复机体系速度和角速度

**时间回补：arXiv v1 提交于 2026-08-21 09:11 UTC，进入 8 月 24 日最新批次。此前未进入索引。**

《IMU-Free Body-Frame State Estimation with Sparse Scene Flow for Quadcopters》研究一个反常规问题：四旋翼如果完全没有 IMU，仅靠同步双目图像和电机推力命令，能否在 body frame 中估计 pose、速度、角速度、重力和 disturbance。系统使用连续—离散 manifold EKF，把静态场景特征当作隐式惯性参考；四视图 bundle adjustment（前后两个时刻、左右双目）联合估计三维点位置和速度，并输出带联合协方差的稀疏 scene flow。（[论文](https://arxiv.org/abs/2608.20891)，[HTML 全文](https://arxiv.org/html/2608.20891)）

### 为什么重要

这并不是建议无人机删掉 IMU。更有价值的理解是：**视觉本身可以形成一个与惯性链路相对独立的速度/角速度观测源**。如果 IMU 饱和、强振动、时间同步异常或 bias 突变，独立 vision-derived body-frame motion 可以作为故障检测与冗余测量，而不是让同一个 VIO 滤波器内部的视觉和 IMU 一起失效后无法判断原因。

### 算法模块

FAST/Shi-Tomasi 检测特征，SSD/Lucas-Kanade 做时间跟踪，NCC 做左右目匹配；EKF 根据当前 pose 与点不确定度预测搜索区域，并通过 normalized innovation 的 chi-squared gating 只接收被判断为静态的特征。四视图 BA 不直接把 EKF 中的 feature state 送进求解，而是通过相对 pose prior 传递信息，输出 sparse 3D point cloud、per-point velocity 与 joint covariance。

### 传感器与动力学假设

只需要同步 stereo 与 motor thrust command，但依赖准确的双目标定、相机—机体外参、推力模型和足够静态纹理。当前验证使用 VID 数据集，序列主要是无载荷、无风、hover 为主，属于第一阶段验证，不是高动态飞行证据。

### 实验结果与风险

79 s、4733 帧完整序列中，translation RMSE 约 1.104 m、rotation RMSE 约 7.55°，但中位数分别只有 0.229 m 和 2.58°；误差主要由起降瞬态尤其落地后的灾难性发散拉高。73–75 s 时间窗内，translation error 可从约 0.32 m 增至 3.4 m，rotation 从约 2.2°升到 20°。这恰恰说明该系统目前更适合作为研究型冗余观测，而不是替代 IMU 的主飞控状态估计。

### 可复现性

论文声称 Python 实现，并在正文中引用 calibration 配置，但当前 arXiv 页面未提供可直接核验的稳定官方仓库链接。本期因此不给出猜测代码地址。

### 适合谁关注

适合 UAV 状态估计、传感器故障诊断、视觉 scene flow，以及希望为 VIO/LIO 增加独立健康监测通道的团队。

### 工程落地启发

可以把它降维成更实用的“视觉角速度/机体系速度健康监测器”：不参与主滤波，只与 IMU/飞控估计做一致性检查。当视觉与 IMU 长时间显著分歧时，再触发传感器降权、重新标定检查或安全模式。

## 6. Logic-VLA：让 VLA 在推理时接收 Signal Temporal Logic，而不是只听自然语言“注意安全”

**时间回补：arXiv v1 提交于 2026-08-20 20:35 UTC，作为 cross-list 进入 8 月 24 日 Robotics 批次。此前未进入索引。**

Logic-VLA 解决 VLA 在安全关键任务中的一个根本问题：自然语言可以说“绕开红区并在最后到达 B”，但这类要求很难精确定义“始终、最终、先后、时间窗”。Logic-VLA 在普通自然语言任务之外增加 Signal Temporal Logic（STL）输入，并用 syntax-graph encoder 表示逻辑公式，使同一个策略可以在推理时根据不同 STL 约束改变行为，而不必为每一种安全规则训练一套新 policy。（[论文](https://arxiv.org/abs/2608.20556)，[HTML 全文](https://arxiv.org/html/2608.20556)）

### 为什么重要

机器人安全要求最怕停留在 prompt。STL 的价值是可计算：例如“未来 5 秒始终距离障碍超过 d”“在 10 秒内进入目标区域，但进入 B 之前必须先访问 A”。只要最终轨迹可以计算 robustness score，就能形成训练和验收信号，而不是靠语言模型自己解释“我认为我遵守了规则”。

### 算法模块

STL syntax graph encoder 先用 trajectory-formula pair 和 robust semantics 预训练；VLA 后训练分两阶段：先在满足 STL 的 demonstrations 上做 STL-conditioned supervised fine-tuning，再对 matched satisfying/violating rollout pair 做 trajectory-level preference optimization，使用 flow-matching surrogate 实现类似 Identity Preference Optimization 的更新。

### 实验范围与结果

实验在 NVIDIA Isaac Sim 5.1 中使用 DJI Mavic 2 Pro 模型，包含 10 个随机化 photorealistic warehouse 环境、6 个自然语言导航任务和约 3000 条无碰撞动态可行参考轨迹。相对 STL-blind base policy，Logic-VLA 将 STL satisfaction rate 提高 24.8–40.7 个百分点，而自然语言主任务成功率最多下降 1.8 个百分点，并测试了未见 STL 公式的泛化。

### 鲁棒性、可复现性与风险

当前结果全部是仿真，并且动作执行采用 Isaac Sim API 的位置更新，距离真实无人机动力学、感知延迟和安全认证还有明显距离。更关键的是，STL 条件提高“策略倾向于满足规则”的概率，不代表形式化运行时保证；VLA 仍可能输出违反约束的轨迹。

### 适合谁关注

适合 VLA、安全机器人、无人机任务规划、行为约束和希望把形式化规格接到学习策略上的团队。

### 工程落地启发

短期不必把 STL 编进 VLA。可以先让 VLA/LLM 负责把用户任务转成 STL/LTLf，再由传统 trajectory monitor 或 CBF/MPC 在运行时硬检查。只有当规格生成、监控和回退流程成熟后，才考虑把逻辑条件继续下沉到 policy training。

## 7. Measurement-Robust CBF：安全过滤器开始把“定位误差集合”当作一等输入

**时间回补：arXiv v1 提交于 2026-08-20 18:00 UTC，作为 Systems and Control cross-list 进入 8 月 24 日 Robotics 批次。此前未进入索引。**

《Learning-Based Measurement-Robust Control Barrier Functions for Obstacle Avoidance under State Estimation Error》针对标准 CBF 一个常被工程实现忽略的前提：CBF 通常默认拿到的状态就是真实状态，但真实机器人只有带 bias、漂移和延迟的估计。作者提出 DMR-CBF 与 NMR-CBF：前者在 CBF 条件内部针对 drift dynamics 的最坏测量误差做优化，后者用学习项近似这个昂贵 inner optimization，再通过可微 trajectory rollout 微调。（[论文](https://arxiv.org/abs/2608.20467)，[HTML 全文](https://arxiv.org/html/2608.20467)）

### 为什么重要

传统“障碍物膨胀”只能处理一部分几何不确定性。当定位误差具有方向性、随时间累积，或者 robot state estimate 与真实位置之间存在系统偏置时，固定膨胀不是很高效：太小会撞，太大则无法通过狭窄区域。Measurement-Robust CBF 直接把估计误差界纳入 safety condition，让安全余量跟当前状态不确定性变化。

### 算法模块

DMR-CBF 在每次安全过滤时对允许的 measurement/drift uncertainty 求 worst-case 条件；NMR-CBF 先用 DMR-CBF 监督预训练，再通过 differentiable rollout 优化，使小网络学习鲁棒项，避免在线重复求 inner optimization。最终仍以安全 QP/filter 形式修正名义控制器输出。

### 实时性

数值实验中，标准 CBF 对 planar double integrator / 12D quadrotor 每步约 0.26/0.47 ms；NMR-CBF 为约 0.31/0.57 ms；DMR-CBF 为 0.61/2.27 ms；另一种 Duality CBF 在 12D quadrotor 上约 45.28 ms。学习版的意义因此很明确：把鲁棒优化的主要成本离线蒸馏掉。

### Unitree Go2 实机

作者在 Unitree Go2 EDU + Jetson Orin Nano 8GB 上测试。机器人自身 odometry 在试验前测得沿程距离最多低估约 18%，实验又额外注入了 -15 cm 的横向位置 bias。10 次硬件 trial 中，标准 CBF 出现 3 次碰撞，安全率 7/10；NMR-CBF 为 0 次碰撞、10/10 安全通过。

### 风险

这里的误差界仍需用户设定。如果真实状态误差超出训练/配置的 envelope，NMR-CBF 同样可能失效；如果把界设置得过大，则会重新变成极度保守的障碍膨胀。它也不处理动态障碍预测错误、地图错误或控制执行器故障。

### 适合谁关注

非常适合轮足机器人、无人机、移动机器人，以及已经有 CBF/MPC safety filter 但定位在长走廊、弱特征或 RTK 切换时会明显漂移的系统。

### 工程落地启发

先把定位系统输出的协方差真正接进安全层，而不是只用于日志显示。第一版甚至可以不用神经 CBF：将位置 3σ、延迟对应的运动距离和控制跟踪误差组合成方向性 margin；确认收益后再考虑学习式 robust term。

## 8. Artic：把自然语言 Agent 工作流“编译”为有类型读写边界的 artifact workflow

**时间回补：arXiv v1 提交于 2026-08-21 17:47 UTC，进入 8 月 24 日 Software Engineering 最新批次。此前未进入索引。**

《Natural-Language Workflows Are Not Software Yet: Artifact-Driven Compilation for Reliable Agent Execution》指出自然语言 skill/SOP 最大的问题不是模型看不懂，而是**数据依赖和控制流没有被机器明确表示**。一段人类可读流程经常写“根据上一步结果继续检查”，却没声明究竟读取哪个结果、写出什么新状态、什么条件下进入哪个分支。Artic 因此把自然语言 workflow 编译为 artifact-driven representation：每一步显式声明 reads/writes，输出 artifact 有 constraint gate，分支由显式 control transfer 管理。（[论文](https://arxiv.org/abs/2608.21341)，[HTML 全文](https://arxiv.org/html/2608.21341)）

### 为什么重要

这和真实 Coding Agent/Work Agent 的长期可靠性直接相关。很多所谓 Agent framework 仍把整个 SOP 塞进 context，让模型自己记住步骤、前置条件和中间结果；任务一长、出现重试或分支，模型就很容易读错旧状态或跳步骤。Artic 的思路更像传统编译器：让模型只负责把模糊流程翻译成结构，运行时执行器只消费明确 artifact contract。

### 算法模块

编译器将源工作流分解为显式 artifact dependency；对步骤的 read/write、输出约束和 control transfer 建模；再通过 constrained optimization 识别“需要记太多上下文”或控制逻辑过重的步骤并进一步拆分。因为自然语言没有严格形式语义，Artic 不声称可以像 C 编译器那样证明等价，而是把 faithfulness validation 拆成局部 obligation，并用 scenario-based dry run 检查编译后的区域是否仍符合原流程。

### 工程结果

论文在 11 个真实领域共 488 个实例上测试，使用 GPT-5.4、Sonnet-4.6、GLM-5 等模型做 workflow compiler，并以多个大小不同的 executor 执行。相比原始文本工作流，Artic 的 task resolve rate 提升 28 个百分点；跨模型一致性提升 32 个百分点，重复执行一致性提升 56 个百分点。移除 correctness validation 的版本比完整系统低 16 个百分点，说明“编译出来”之后仍必须独立验收。

### 是否适合真实研发流程

非常适合长期 Coding Agent、文档处理 Agent 和机器人任务编排，但建议把它理解成**工作流 IR / 编译层**，而不是另一个大模型代理。read/write artifact 应具有 schema、版本、provenance 与权限；执行器必须拒绝缺失依赖或类型不符的数据，不能在运行时继续让 LLM 猜。

### 风险与可复现性

当前论文未在 arXiv 页面公开稳定代码仓库。自然语言到 workflow IR 的编译仍由 LLM 完成，因此源流程歧义、遗漏和错误仍可能被结构化地固化；scenario dry run 也只能覆盖抽样路径，而非所有分支。

### 工程落地启发

对内部 Agent，可以先实现一个非常小的 artifact contract：每步只允许声明 `inputs / outputs / preconditions / postconditions / next`。中间产物写入持久化对象而不是聊天历史；任何写 GitHub、部署、发消息等不可逆操作必须消费显式、已验证的 artifact。这样比继续把 SOP 写得更长更稳定。

## 经典论文回顾

### MPPI：从“求一条最优轨迹”转向“并行采样很多未来，再用指数权重更新控制序列”

**发表时间与历史位置：** Grady Williams、Paul Drews、Brian Goldfain、James M. Rehg 与 Evangelos A. Theodorou 在 ICRA 2016 的《Aggressive Driving with Model Predictive Path Integral Control》中展示了 MPPI 在高速自动驾驶上的代表性应用；随后 2017 年的《Information Theoretic Model Predictive Control: Theory and Applications to Autonomous Driving》系统化了其信息论推导。MPPI 后来成为无人车、无人机、移动机器人和高维连续控制中最常见的 sampling-based MPC 之一。（[ICRA 2016 DOI](https://doi.org/10.1109/ICRA.2016.7487277)，[信息论 MPPI 论文](https://arxiv.org/abs/1707.02342)，[MPPI-Generic](https://github.com/ACDSLab/MPPI-Generic)）

### 核心问题

传统非线性 MPC 每个控制周期都需要求解一个约束优化问题，复杂非凸代价、不可微碰撞项和高维动力学会让求解器依赖初值、梯度质量和实时预算。MPPI 的核心思路是避免对 value function 求梯度：从当前 nominal control sequence 周围采样大量扰动，前向 rollout 动力学，根据每条轨迹的累计代价给样本赋指数权重，再用加权扰动更新控制序列。

### 关键数学思想

MPPI 可以从 path integral / KL divergence / importance sampling 的随机最优控制视角推导。实践上，一个典型循环是：

1. 保留长度为 T 的 nominal control sequence；
2. 采样 K 组控制噪声；
3. 并行前向 rollout K 条状态轨迹；
4. 计算运行代价、终端代价与控制修正项；
5. 用 `exp(-cost / lambda)` 形成软最优权重；
6. 对采样噪声做加权平均，更新每个时刻的控制；
7. 执行第一个控制，控制序列整体左移，进入下一周期。

这使复杂障碍代价、非线性动力学和非凸目标可以直接写进 rollout cost，而不必保证每一项可微。

### 动力学与传感器假设

MPPI 本身不是感知算法，它假设有一个能够快速前向预测的动力学模型，以及当前状态估计和局部环境代价。模型可以是解析动力学、学习模型或混合模型；地图可以是 costmap、ESDF、terrain cost 或 learned value。真正决定实机效果的往往不是 MPPI 公式，而是动力学预测速度、状态延迟、采样分布与 cost shaping。

### 当年为什么重要

MPPI 非常适合 GPU：成百上千条 rollout 几乎天然并行。ICRA 2016 的 aggressive driving 让它证明 sampling-based MPC 不只是低速玩具，而能在强非线性、接近车辆动力学极限的场景实时工作。今天的 CUDA 实现进一步把这一优势工程化。

### 今天仍然有效的思想

- 用大量并行 rollout 替代单一路径局部梯度搜索；
- cost 可以高度非凸甚至不可微；
- nominal sequence 天然提供 receding-horizon warm start；
- 可以把 learned dynamics / learned cost 放进去而不改变控制框架；
- 采样分布本身是重要设计变量，可使用 colored noise、低频噪声或混合分布；
- 高级安全模块可以先过滤 rollout 或给危险轨迹极高代价。

### 已被后续扩展的部分

Vanilla MPPI 对模型误差、采样效率和硬约束处理并不完美。后续出现 Tube-MPPI、Robust MPPI、Smooth-MPPI、低频采样、风险感知 MPPI、distributionally robust 版本等；移动机器人 Nav2 也发展出 CPU 可实时运行的 MPPI Controller。高维系统中，学习 proposal、value warm-start 和多模态采样开始替代单一高斯噪声。

### 公开代码与可复现性

ACDSLab 的 [MPPI-Generic](https://github.com/ACDSLab/MPPI-Generic) 是当前很实用的 C++/CUDA 实现，支持 MPPI、Tube-MPPI、RMPPI、多种采样分布和可插拔 dynamics/cost；仓库采用 BSD-2-Clause。它比复刻 2016 年实验代码更适合作为现代工程基线。

### 对当前工程项目的重新解读

对 LiDAR 导航、机器狗或无人机，MPPI 最值得重新强调的是**采样空间必须与真实可达动作一致**。如果直接在 `vx/vy/vw` 上撒白噪声，而底层飞控或轮足控制器根本无法跟随这些快速变化，rollout 再多也只是在优化虚假的动力学。

更合理的结构是：

```text
状态估计 + 局部点云/ESDF
        ↓
系统辨识后的短时动力学模型
        ↓
结构化采样（低频/colored/mode-aware）
        ↓
并行 rollout + 碰撞/跟踪/风险代价
        ↓
可达性 / CBF 最终安全过滤
        ↓
底层飞控或运动控制器
```

对于窄通道无人机，可以把真实制动距离、估计协方差和控制延迟显式写进 rollout，而不是只把障碍物统一膨胀；对于机器狗，可以让采样变量变成高层 body velocity / gait parameter，而不是直接采样关节动作。这样 MPPI 才真正成为系统级预测控制器，而不只是随机轨迹打分器。

## 今日结论

8 月 24 日公开批次里最明确的趋势是：**学习模块正在从“替代整个控制器”退回到更合适的结构位置。** NeSAM 让神经网络补足土壤力学模型，SRL-MPC 让 RL 调节显式 MPC，NMR-CBF 用网络近似昂贵 worst-case 鲁棒项，Neural-Primitive 则把经典 motion primitive teacher 的求解成本蒸馏成极轻网络。它们的共同点不是端到端，而是尽量让网络只负责最难建模或最贵计算的部分。

对状态估计与安全层来说，Measurement-Robust CBF 是今天最有直接工程价值的一条：定位协方差不应该只显示在 RViz 或日志里，而应该真实改变局部安全边界。标准 CBF 在 Go2 上面对漂移和 bias 会撞，显式建模估计误差后可以恢复安全，这比单纯再调一个固定 obstacle inflation 更有说服力。

无人机方向值得重点看 Neural-Primitive 与 FF-MPCC。前者说明 MID360 + Orin NX 的局部规划完全可以进入个位毫秒，并且输出的是多项式轨迹而不是速度命令；后者则证明高速编队不应该死追统一时间表，而应让每台机围绕路径进度协同。两者都在改变“上层给低层什么接口”这个核心设计问题。

VLA 与 Coding Agent 也呈现相同结构化趋势。Logic-VLA 用 STL 把模糊安全要求变成可计算逻辑条件；Artic 把自然语言 SOP 编译成显式 artifact 依赖。对于真实工程，真正可靠的方向越来越不是“给模型更多自由”，而是把可验证边界变得更明确。

## 最值得深入研究或尝试复现的方向

1. **MID360 无人机做 Neural-Primitive 风格 planner distillation**  
   保留当前局部规划器作为 teacher，离线收集 `point cloud + state → polynomial trajectory`，训练小网络直接预测轨迹系数。在线仍保留一个极轻碰撞 gate。验收重点是平均/P99 规划延迟、最小净空、动态可行率和窄通道成功率，而不是只看 imitation loss。

2. **把定位不确定度真正接进安全控制层**  
   先不训练 NMR-CBF，直接用当前 ESKF/LIO 输出的 position covariance、时间同步误差和控制跟踪误差构造方向性安全 margin，对比固定膨胀。确认能在弱特征、RTK 跳变和轮速打滑下减少碰撞且不过度保守，再研究 DMR/NMR-CBF。

3. **给内部 Agent 增加 artifact-driven workflow IR**  
   把长 SOP 从 prompt 中拆出，每一步显式声明输入、输出、前置条件、后置条件和下一状态；GitHub 写入、部署、发消息等不可逆动作只允许消费已验证 artifact。用同一批任务比较纯文本 SOP 与结构化 workflow 的重复执行一致性和跨模型迁移稳定性。

## 参考资料

1. **NeSAM: Neuro-Symbolic Kinodynamics with Soil Adaptation for Off-Road Mobility**  
   - [论文](https://arxiv.org/abs/2608.21330)  
   - [HTML 全文](https://arxiv.org/html/2608.21330)

2. **SRL-MPC: Shape-Aware Reinforcement Learned Model Predictive Control**  
   - [论文](https://arxiv.org/abs/2608.21175)  
   - [项目页](https://hanruihua.github.io/srl_mpc_project/)

3. **FF-MPCC: High-speed Agile Formation Flight with Model Predictive Contouring Control**  
   - [论文](https://arxiv.org/abs/2608.21056)  
   - [HTML 全文](https://arxiv.org/html/2608.21056)

4. **Neural-Primitive: An Efficient End-to-end Local Planner with Primitive-based Imitation Learning for Autonomous Flight**  
   - [论文](https://arxiv.org/abs/2608.20948)  
   - [项目页](https://zhitaoliu.github.io/neural-primitive/)

5. **IMU-Free Body-Frame State Estimation with Sparse Scene Flow for Quadcopters**  
   - [论文](https://arxiv.org/abs/2608.20891)  
   - [HTML 全文](https://arxiv.org/html/2608.20891)

6. **Logic-VLA: A Temporal Logic Conditioned Vision-Language-Action Model**  
   - [论文](https://arxiv.org/abs/2608.20556)  
   - [HTML 全文](https://arxiv.org/html/2608.20556)

7. **Learning-Based Measurement-Robust Control Barrier Functions for Obstacle Avoidance under State Estimation Error**  
   - [论文](https://arxiv.org/abs/2608.20467)  
   - [HTML 全文](https://arxiv.org/html/2608.20467)

8. **Natural-Language Workflows Are Not Software Yet: Artifact-Driven Compilation for Reliable Agent Execution**  
   - [论文](https://arxiv.org/abs/2608.21341)  
   - [HTML 全文](https://arxiv.org/html/2608.21341)

9. **MPPI 经典工作与现代实现**  
   - [Aggressive Driving with Model Predictive Path Integral Control / ICRA 2016 DOI](https://doi.org/10.1109/ICRA.2016.7487277)  
   - [Information Theoretic Model Predictive Control](https://arxiv.org/abs/1707.02342)  
   - [MPPI-Generic](https://github.com/ACDSLab/MPPI-Generic)

10. **最新公开列表与官方模型更新**  
    - [arXiv Robotics](https://arxiv.org/list/cs.RO/recent)  
    - [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)  
    - [OpenAI: GPT-5.6 in Kiro](https://openai.com/index/gpt-5-6-in-kiro/)
