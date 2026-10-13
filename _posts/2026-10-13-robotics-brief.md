---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-13"
date: 2026-10-13 09:00:00 +0800
description: "聚焦烟尘中LiDAR-Radar可靠性切换、无地图ESDF避障、物理时间VLA、GPU约束规划、端侧机器人Agent和Coding Agent审查及Skill供应链安全。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-13

## 摘要

**检索基准：2026-10-13 09:00（Asia/Shanghai），星期二。** 最新常规公开批次为 **2026-10-12**：arXiv Robotics **87 条**，Software Engineering **28 条**。本轮先检查最近 24 小时，再复核最近 7 天候选，与 `master` 截至 10 月 11 日的 961 条覆盖索引及 **10 月 12 日已生成、但尚未归档的 11 条待补录记录**联合去重。下列 8 项主动态均为新的工作，不将昨天因 GitHub 写入失败而未入库的研究重新包装为今天首发。

由于本期 8 篇论文的 arXiv v1 均在 **2026-10-09 UTC** 提交，而周末后于 10 月 12 日进入常规公开列表，它们均标记为**时间回补**。正文所有性能数字均是作者在指定硬件/测试集上报告的结果，不能自动外推到 RK3588、Jetson、Go2 或具体产品环境。

**SLAM 与无人机感知**今天最值得关注的是两种完全不同的计算分层。*When LiDAR Fades, Radar Takes Over* 让一个只从健康数据训练的时序异常检测器持续评估 LiDAR 是否还能信任，烟尘恶化时将定位权交给 Radar-Inertial Odometry；*Low-Latency Mapless ESDF Queries* 直接对带位姿的深度图做 GPU 距离查询，避免每个短预测周期都为数百次查询构建完整体素图。在森林仿真中，后者最高 9 m/s 的实验碰撞率为 **0.4%**，对比最佳体素方案为 **5.9%**。

**控制与规划**方面，*Chronos Policy* 认为 VLA 最大的隐藏假设是“第几个 token 就对应第几个固定控制时刻”，因此将传感器采集时刻与动作预期执行时刻直接放进 Transformer 的 time-aware RoPE；*PATACON* 则在有显式运动学约束的机械臂、人形任务中，沿约束流形的局部切空间开展 GPU 双向 RRT 搜索，报告最高 **11.25 倍**规划加速。这两篇分别针对真实时间与配置空间几何，都是非常值得迁入成熟系统的基础表示问题。

**端侧机器人 AI**，*BT-Agent* 在四足机器人上用 9B 模型与预定义行为树技能组合，在低层直接拦截不安全动作，避免等待下一轮 LLM 推理；其 161 任务多保真测试中，文本层评测吞吐为仿真的 **10.9 倍**。*SmolWAM* 则将 2B Cosmos Policy 压缩成约 0.88B 的 latent world-action 模型，作者报告在 LIBERO 400 回合测试中成功率 **95.5%**，生成一个 16-action chunk 用时约 **57 ms**、GPU 内存约 **2.4 GiB**。这仍是 GPU 结果，不等于 RK3588 NPU 已经可以直接部署。

**AI Coding** 两项工作特别有现实警示意义。CRBugBench 以真实历史引入的 Bug 为目标评估 AI Code Reviewer：公开/内部合计 1,800 个审查任务中，最好的受测组合只在前五条评论内找出约 **71.9%** 的已核实 Bug。SkillRelayBench 发现恶意内容还能通过不同会话持久化文件、配置与缓存“接力传播”，不是只在当前 Prompt 出现；270 个攻击案例中，多种 Agent 的攻击成功率达到 **46.7%–77.4%**。因此不能将通过 AI Review 或成功运行 Skill 等同于安全验收。

今日实操关注 GitHub **10 月 12 日**推出的提交真实推送者身份归属（目前为 Enterprise 限量预览），以及 **10 月 6 日**确认的 Copilot IDE 代理使用指标漏记修复。经典回顾选择 **Voxblox（IROS 2017）**，与今天“无地图 ESDF”形成直接工程对照。

原始列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

## 1. When LiDAR Fades, Radar Takes Over：烟尘环境中根据传感器健康度切换 LIO / RIO

**时间回补：arXiv v1 提交于 2026-10-09 16:04 UTC。**

### 为什么重要

矿井、消防烟雾、施工粉尘会改变 LiDAR 回波的数量、强度与空间分布，甚至产生大量近场悬浮颗粒点。传统 LiDAR-Inertial Odometry 即使仍能输出姿态，也可能已经从“真实墙面配准”退化成“对雾团和噪声点的配准”。问题不只是某个单帧质量指标变差，而是系统**何时应停止相信这条定位链**。

这篇论文没有要求算法先识别“烟”“尘”或具体故障类别，而是在正常观测上训练单类时序模型，检测 LiDAR 感知状态的异常偏离。这样可以覆盖难以预先穷举或标注的多种退化现象。

### 算法模块与传感器假设

~~~text
LiDAR/IMU + Radar/IMU
        ↓
空间、跨模态、几何/运动、强度、观测新鲜度特征
        ↓
短时滑窗 LSTM Autoencoder（仅在健康数据训练）
        ↓
LiDAR Reliability / Anomaly Score
        ├─ 可信：LIO 继续负责定位
        └─ 退化：将定位权交给 RIO
        ↓
连续定位输出 + 状态机记录
~~~

Radar 的优势是受烟尘影响较小，但在稀疏散射、镜面多径或可观方向有限的场景中也可能退化；因此“切 Radar”不是“获得绝对可靠的定位”。实现时必须处理 LIO 与 RIO 坐标系、速度偏差、时间戳以及切换瞬间的状态连续性。

### 实时性、鲁棒性与可复现性

论文使用 GNSS-denied 地下隧道真实地面机器人数据，包含正常和浓烟工况，展示了退化检测、定位权切换以及在严重 LiDAR 退化下持续输出里程计。特征族消融反而发现：**较少、但更相关的异常特征**在所测浓烟场景中可能优于盲目叠加所有特征。

摘要没有提供可移植到其他平台的统一切换延迟、ATE 或输出 Hz，不能将“保持输出”误认为“定位误差不增长”。论文说明代码**计划公开**，当前应按未完全开源处理。

### 工程风险、适合谁关注与落地启发

适合消防/矿井机器人、LiDAR + 毫米波雷达的地面或飞行平台。最小 A/B 不必先重写 SLAM：在现有 FAST-LIO/LIO-SAM 旁运行 detector，记录 `point_valid_ratio`、`intensity_distribution`、`cross_modal_velocity_residual`、`sensor_age`、`health_score` 和 `mode_switch_reason`。先只报警，确认低误报后再允许自动切换；切换时保留滞回、最短停留时间和恢复条件，避免烟尘边缘持续 LIO↔RIO 抖动。

**来源：** [论文](https://arxiv.org/abs/2610.13788)。

## 2. Mapless ESDF：短时无人机避障不必每次先构建完整体素地图

**时间回补：arXiv v1 提交于 2026-10-09 07:48 UTC。**

### 为什么重要

在 10–30 ms 的局部反应窗口内，如果规划器只需要对眼前的一小批轨迹点计算障碍距离，先把最新深度图融合成 TSDF/ESDF 体素地图可能“预处理比查询还贵”。地图在大范围探索和数百万次复用查询时有价值，近场避障的成本结构却不同。

作者选择直接从**已知相机位姿的深度图**建立 GPU 距离查询，按 image pooling 调整分辨率，避开固定 3D voxel size 对细枝和狭缝造成的量化损失。

### 算法模块与假设

~~~text
Depth Image + Camera Pose
           ↓
图像域 pooling / GPU query structure
           ↓
Query points from local MPC trajectories
           ↓
Signed Distance / Clearance + gradients
           ↓
MPC obstacle cost and feasible control
           ↓
execute → get next depth image
~~~

这里“Mapless”只是**不构建持久体素 ESDF**，并不是不依赖相机外参、位姿和深度质量。单帧视野之外、被遮挡的区域仍可能是未知；不能直接把没有深度回波的区域视为无障碍。

### 实时性与结果

作者在嵌入式 GPU 上，对比 2–20 cm 分辨率体素方案，报告更低的包含预处理在内的总延迟、更高的距离查询精度，以及在相当分辨率下**低 1–2 个数量级**的内存消耗。与 MPC 组合的激光扫描森林仿真在最高 9 m/s 时，报告碰撞率 **0.4%**，最佳体素方案 **5.9%**、最佳同分辨率无地图基线 **5.5%**。还在两个真实森林点进行机载飞行，指令速度最高 4 m/s。

这些数字来自指定 GPU 和森林实验，不是所有场景都能实现的安全概率保证。当前论文原页没有成熟源码入口。

### 鲁棒性、适合谁关注与落地启发

适合小型 MAV、Jetson、短时 MPC、需要追踪细枝/缆线的无人机。建议直接统计**每次新观测到每次有效避障控制输出**的端到端延迟，而不只看 `distance_query_us`。固定同一深度图、同一 MPC 样本数，比较体素 ESDF、直接点云距离与 mapless 深度图 ESDF，评估 P95 延迟、最大内存、最小净空、未知区域风险。全局任务依旧需要独立定位与持久地图。

**来源：** [论文](https://arxiv.org/abs/2610.13158)。

## 3. Chronos Policy：将真实物理时间放进 VLA 的注意力，而不只按 token 顺序排动作

**时间回补：arXiv v1 提交于 2026-10-09 UTC。**

### 为什么重要

很多 VLA/Diffusion Policy 把视觉帧、力反馈、关节状态和动作块排列成固定长度序列，隐含“连续两个 token 间总是固定毫秒数”。真机上却经常有相机掉帧、控制线程抢占、GPU 推理抖动、网络摄像头延迟、力传感器与关节总线不同频率。序列位置相同，并不说明物理上的时间间隔相同。

Chronos Policy 在预测时显式使用**观测真实采集时刻**和**动作目标执行时刻**；比较向 token 特征加时间 embedding 与把真实时间用于 RoPE，作者发现后一种更稳健。

### 算法模块与传感器假设

~~~text
Vision / Proprioception / Force tokens
           + capture_timestamp
           ↓
Time-aware Rotary Positional Encoding
           ↓
Diffusion Transformer
           + requested_action_execution_timestamp
           ↓
Action chunk indexed by physical time
~~~

训练时对观察采样频率、交付时延及动作块开始时刻进行随机化，让同一段示范经历多组传感时序。这样多速率传感器不必强行重采样到一个固定的伪时间网格。

### 实时性、实验与局限

作者在 Dynamic Cup、Conveyor、Peg Insertion、Pivoting 等动态/多传感任务中改变观测频率、延迟与推理耗时，报告比固定时序基线更稳健；在六项 DexMimicGen 准静态任务上保持大体相当的标准表现，并在时间条件变化时获得更高平均成功率。项目页给出时间编码与随机化消融，但当前代码仍标记 **Coming soon**，不能说可直接运行。

这不是一种补偿任意时间错误的魔法：如果传感器时间戳在采集端已错误，或者机器人控制器不保证在指定时间执行动作，模型会被喂入错误的时间条件。

### 适合谁关注与工程落地启发

非常适合多速率传感、远端 VLA、GPU 队列抖动和机器人 Action Chunk。迁入已有系统的第一步不是重训：先为每个 observation 保存 `capture_time`、`received_time`、`inference_begin/end`、`planned_execution_time`、`actual_execution_time`，统计 P95 时延与时钟偏移。再在相同数据上比较固定位置编码、额外时间 embedding 和 time-aware RoPE。安全控制与动作队列仍要独立检查实际执行超时。

**来源：** [论文](https://arxiv.org/abs/2610.13929) · [官方项目与消融](https://changhaowang.github.io/chronospolicy/)。

## 4. PATACON：约束机械臂与人形运动规划在切空间搜索而非反复投影

**时间回补：arXiv v1 提交于 2026-10-09 08:13 UTC。**

### 为什么重要

双臂闭链搬运、手握固定物体、人形双脚支撑等任务存在显式等式约束。传统 RRT-Connect 往往先在高维关节配置空间采样，再把候选投影回约束流形；维度越高、约束越多，投影和碰撞检测浪费越严重。

PATACON 使用约束函数在当前配置下的局部 Jacobian，计算可行运动的切空间，把 GPU 并行搜索更多地限制在**符合局部流形几何的方向**。它保留双向 RRT-Connect 的探索能力，但减少了候选频繁偏离约束流形的问题。

### 算法模块与动力学假设

~~~text
q_start / q_goal + equality constraints c(q)=0
                 ↓
Jacobian and local tangent basis
                 ↓
GPU-parallel bidirectional RRT-Connect
                 ↓
Tangent-space steering + correction
                 ↓
Constraint / collision validation
                 ↓
feasible high-DOF path
~~~

该方法依赖已知、可计算局部导数的约束函数，以及可信的关节限位与碰撞几何。局部切空间只近似当前流形，长步长、流形奇异位置、接触模式跳变仍需做可行性复核。它主要解决**运动学约束规划**，不自动保证执行时的动力学、抓持力或电机扭矩满足限制。

### 结果、可复现性与风险

论文在双臂闭链以及人形全身约束规划任务中，对比 GPU 并行采样方法，随着配置维度和约束余维增长，报告最高 **11.25 倍**的加速。它没有证明任何任务都能达到同样速度，也没有提供能直接推断实际控制频率的统一数字；当前 arXiv 页面没有成熟官方代码入口。

### 适合谁关注与工程落地启发

适合 MoveIt/OMPL、双臂搬运、全身 IK、足式机器人的连续支撑控制。复现时先用现有 RRT-Connect + projection 建基线，固定相同约束 Jacobian、碰撞检测和随机种子，记录 sample accept ratio、constraint correction iterations、wall-clock、失败率和路径执行可行性。对于高频 whole-body controller，该 Planner 更适合提供**慢速可行几何路径**，再由 MPC/WBC 做时间参数化与硬动态约束。

**来源：** [论文](https://arxiv.org/abs/2610.13195)。

## 5. BT-Agent：端侧 9B LLM 负责调度，行为树负责即时拦截和可恢复执行

**时间回补：arXiv v1 提交于 2026-10-09 17:08 UTC。**

### 为什么重要

机器人 Agent 常见的危险接口是：“大模型决定动作 → 等动作运行 → 失败时再问模型下一步”。如果底盘已经进入危险区域、导航目标突然丢失或操作者下达急停，等待完整 LLM 推理再处理显然不符合机器人控制要求。

BT-Agent 将语言决策与**预定义行为树技能**组合。行为树节点拥有前置条件、执行条件、运行期监测与结构化错误反馈；LLM 只选择技能和解析错误，低层可以不经 LLM 立即终止不再满足条件的动作。

### 系统模块与实际部署

~~~text
Onboard 9B LLM
     ↓ structured tool/skill request
Behavior Tree: conditions + actions + local monitors
     ↓
Robot navigation / manipulation skills
     ↓
Structured success/failure reason
     ↓
LLM retries, chooses another skill, or reports constraints
~~~

作者在四足机器人上使用 9B 模型完成五类任务。161 个任务的多保真基准先使用文本环境评测所有任务，再在 Habitat 中测试 39 项；文本评测吞吐约为仿真的 **10.9 倍**，但仿真能够揭露单纯文本环境发现不了的感知与运动故障。在最有价值的 4B 与 9B 对比中，相比最强 Act/ReAct 基线分别约提升 **10** 和 **5 个百分点**。消融显示结构化工具调用与有用的失败反馈最重要。

### 实时性、鲁棒性与工程风险

“9B 完全 onboard”并不等于 LLM 能 100 Hz 控制机器人。它用于任务层，低级安全反应由行为树和控制节点本地完成。行为树自身仍要经过故障注入：传感器过期、取消命令、导航控制失联、同一技能重复调用、错误返回码误分类等。论文原页未给出可直接复现的成熟代码链接。

### 适合谁关注与工程落地启发

适合 Go2/巡检狗、机器人语音助手、端侧 LLM 任务规划，以及要避免 LLM 直接控制关节的系统。最小落地可把 `GoTo`, `Inspect`, `Speak`, `ReturnHome` 设计成有 `preconditions / running_checks / timeout / abort / error_code` 的明确 API。错误信息应直接反馈 *localization_lost*、*path_blocked*、*battery_low*，而不是模糊的“动作失败”。

**来源：** [论文](https://arxiv.org/abs/2610.13862)。

## 6. SmolWAM：将世界动作模型压到约 0.88B，保留未来状态预测但省掉生成整段视频

**时间回补：arXiv v1 提交于 2026-10-09 15:34 UTC；NeurIPS 2026 相关 Workshop。**

### 为什么重要

世界动作模型同时预测“该做什么”和“做了之后场景会怎样”，但完整视频 diffusion transformer 的显存、计算和多步采样时间很难用于端侧实时操作。SmolWAM 不是从零训练小型模型，而是从 2B 参数 Cosmos Policy 继承预训练主干，再把推理接口改成单帧 latent、缓存文本特征和一次 rectified-flow 读取动作及未来视觉 latent。

### 算法模块与规模

作者保留原模型 28 层中的 **12 层 Transformer**，约 **1,008 个 token**，形成约 **0.88B 参数**的模型。缓存文本特征时保留预训练主干依赖的 attention sink，而不是粗暴移除。动作与未来场景 latent 在同一模型流程中得到预测。

~~~text
Current image latent + cached text features
                 ↓
12-layer compact Transformer trunk
                 ↓
Single rectified-flow inference
        ├─ 16-action chunk
        └─ future visual latent
~~~

### 实时性、结果与可复现性

论文报告 **3.6 GPU-hours** 训练，LIBERO 400 个 episode 的成功率 **95.5%**。一个 16-action chunk 的推理耗时 **57 ms**，约 **2.3 TFLOP**、显存 **2.4 GiB**；相对其 teacher 约 **11 倍**速度、**18.5 倍**更低 FLOPs、**3.2 倍**更低内存。作者已公开 [GitHub 仓库](https://github.com/iitimii/SmolWAM) 与项目页；仓库存在不等于目标 RKNN 权重、RK3588 编译器支持和量化算子都已验证。

### 鲁棒性、适合谁关注与工程落地启发

适合 Jetson/本地机器人、WAM、流式操作推理以及小型 GPU。压缩层数可能牺牲多步状态推理与分布外表现；需同时测视觉预测误差、动作成功率、控制队列抖动和世界状态不一致。对于 RK3588，先检查模型算子是否可导出 ONNX、是否涉及不支持的 attention/flow 算子，再测 INT8 量化精度和 NPU 内存占用，**不能把 57 ms 的 GPU 成绩当成 RK3588 NPU 成绩**。

**来源：** [论文](https://arxiv.org/abs/2610.13740) · [代码](https://github.com/iitimii/SmolWAM) · [项目页](https://smolwam.vercel.app/)。

## 7. CRBugBench：AI Code Review 检出率还不足以让软件工厂“关灯”

**时间回补：arXiv v1 提交于 2026-10-09 14:37 UTC。**

### 突破性工程价值

生成代码越来越快，人类审查成为瓶颈，但“Agent 审过就能合并”需要更强的证据。CRBugBench 不使用模型凭空生成的虚构缺陷，而是从版本历史中找到**已被人类确认的真实 bug**，再恢复其引入 PR，要求审查器在当时可见的 diff 和仓库上下文下检出缺陷。

### 基准与结果

包含公开 GitHub **98 个仓库的 1,000 个 PR 审查任务**，以及大型企业内部仓库的 **800 个任务**。受测最佳组合（Claude Opus 5 + Copilot CLI）在**前五条审查意见**中检出 **71.9%** 的已知 bug；五个月前的 Opus 4.6 对应指标为 **47.7%**。复杂变更、跨文件依赖、多模块非局部推理，特别是需要私有项目知识的企业代码，表现下降明显。

作者还发现，扩大审查计算预算不如恰当引导探索来得稳定：鼓励检查上下游影响的 Prompt 在约 **10%** 额外成本下最高增加 **5.8%** 的检出表现。这并不是任何 Prompt 都能稳定提升 5.8%，也不能把 top-5 recall 误写成 review precision。

### 真实研发、权限和可验证性风险

AI Review 是查缺陷的补充层，不应独自决定 Merge Gate。它不知道业务上为什么允许某项破例，也不能从少量文件推断隐藏服务契约。应按 `small/local / medium / cross-module / safety-critical` 划分 PR，分别设置 review effort 与必要的人工参与；记录 reviewer 模型版本、输入 SHA、测试凭据来源、真正修复的 finding 和人工误报。

### 适合谁关注与工程落地启发

适合 Copilot Code Review、Codex/Claude 自动 PR、大仓库治理。立即可做：取最近 30 个真实引入 bug 的 PR，恢复 bug-introducing SHA，盲测当前 reviewer 并记录 top-5 recall、precision、时间/费用。再单独给跨模块 PR 增加明确的调用关系和目录指导，与“直接让审查模型读 diff”做 A/B。

**来源：** [论文](https://arxiv.org/abs/2610.13668)。

## 8. SkillRelayBench：跨会话文件与缓存可把恶意 Skill 指令传到下一次正常任务

**时间回补：arXiv v1 提交于 2026-10-09 08:45 UTC。**

### 突破性工程价值

传统 Prompt Injection 研究常假设恶意文字与危险调用处在同一次会话。真实 Coding Agent 却会保留缓存、编辑过的配置、文档摘要、测试日志和工作文件；下一次会话中另一项合法 Skill 把这些持久化内容当作上下文读入，就可能触发**跨会话接力攻击**。

论文将机制分成：Instruction Propagation（指令传播）、Data Boundary Violation（数据边界跨越）、Evidence Poisoning（证据污染）。这与昨天报道的同类 Skill 竞争不同：昨天重点是**加载错哪个 Skill**；今天重点是**上一轮落盘产物污染下一轮可信输入**，属于另一种安全边界。

### 基准、结果与防御

SkillRelayBench 包含 **10 个领域、30 个跨会话场景、270 个攻击案例**；在 Codex CLI、Gemini CLI 与 Claude Code 的七种模型组合上，攻击成功率 **46.7%–77.4%**，完整接力链成功率 **35.6%–61.1%**。作者的 SkillRelayGuard 在读入持久 artifact 时恢复来源上下文，并在执行之前提供风险审查建议；在受测三组设置中，将总体攻击成功率从 **69.5% 降到 10.9%**，接力链成功率从 **54.8% 降到 10.0%**，正常任务完成率由 **79.6% 提至 87.5%**。

这些都是论文 benchmark 内的结果，不意味着所有未知攻击均能防御。其防御让 Agent 做最终决定，故不是真正不可绕过的权限边界。

### 真实研发流程、权限与可验证性风险

产品化建议每个持久文件保存 `creator_tool / originating_skill / session_id / content_hash / trust_level / read_policy`，下一次读取时将外部生成内容作为**数据**，而不是自动提升为命令；对写入 `.github/workflows`、`AGENTS.md`、`.mcp.json`、Skill 配置及部署脚本设置独立审批和拒绝规则。缓存清理与 Git Diff 审计同样关键。

### 适合谁关注与工程落地启发

适合长期 Agent、Skill 市场、自动编码 CI、带跨会话 memory 的桌面 Agent。可先做一个安全回归：Session A 使用低信任 Skill 写入测试说明，Session B 读取它但必须拒绝其中要求修改权限配置的文字，只将其作为待审查数据。不能只靠“请忽略恶意提示”的系统 Prompt。

**来源：** [论文](https://arxiv.org/abs/2610.13227)。

## AI Coding 实战技巧精选

### 技巧 1｜审计 AI 生成提交时，分清 Git author、committer 和真实 pusher

- **来源**：GitHub 官方 Changelog，**2026-10-12**；[Push attribution for commits in limited public preview](https://github.blog/changelog/2026-10-12-push-attribution-public-preview/)。
- **一句话结论**：Commit author/committer 字段可以由提交端填写，不应把它们当作已认证推送身份。GitHub 现有 Enterprise **限量公开预览**新增持久化 pusher identity 和规则 **Committer must match pusher**。
- **具体怎么做**：① 若组织为 Enterprise，先联系 GitHub account team 确认是否进入预览，**不要假设普通仓库已有该规则**；② 可用时在仓库/组织 Push Ruleset 中启用 `Committer must match pusher`；③ 用专门的测试仓库分别推送 metadata 匹配与不匹配的无害测试提交，核对 UI/API 中认证 pusher 与 author/committer 的差别；④ Agent 的发布凭据使用独立机器人身份，并将执行任务 ID 与提交 SHA 一起纳入审计。
- **适合什么场景**：企业 GitHub、自动提交的 Codex/Claude、机器人账号和高权限 CI。
- **注意**：限量预览不是全面 GA；真实执行者认证与 PR 审查、签名提交、最小权限是不同防线。

### 技巧 2｜Copilot Agent 指标突然下滑时，先检查 IDE 遥测版本再评价生产率

- **来源**：GitHub 官方 Changelog，**2026-10-06**；[Update your IDE to restore agent activity in Copilot usage metrics](https://github.blog/changelog/2026-10-06-update-your-ide-to-restore-agent-activity-in-copilot-usage-metrics/)。
- **一句话结论**：部分 Copilot SDK IDE 客户端没带正确 IDE 身份，导致 Agent 活动与增删行指标漏记、部分误归到 CLI；这**不是** Agent 实际效率突然下降。
- **具体怎么做**：① 收集团队 per-user metrics 的 `totals_by_ide.last_known_ide_version` 和 `last_known_plugin_version`；② VS Code 升到 **1.139.0+**，其余 IDE 在官方指定修复版发布后再升级，不要把尚未发布的版本写成已可用；③ 核查代理/防火墙没有阻断 Copilot telemetry，再对比 1-day 与 28-day `agent_edit`、`loc_added_sum`、`loc_deleted_sum`；④ 在分析报表中标记修复前的不可回填区间，避免把数据缺口误认成 ROI 下降。
- **适合什么场景**：Copilot 团队指标、IDE Agent 评估、企业工程效率度量。
- **注意**：GitHub 明确说旧缺失数据**不能回填**，计费不受此问题影响；工具报告不应替代任务成功率和人工修复成本。

## 经典论文回顾

### Voxblox（IROS 2017）：ESDF 为什么曾需要地图，而今天短视野避障又开始绕开地图

**历史位置。** Helen Oleynikova、Zachary Taylor、Marius Fehr、Juan Nieto 与 Roland Siegwart 的 *Voxblox: Incremental 3D Euclidean Signed Distance Fields for On-Board MAV Planning* 首版于 **2016-11-11** 发布，更新稿 **2017-04-21**，正式发表于 **IROS 2017**。它是无人机局部规划中 TSDF→ESDF 增量计算的标志性工作，也提供了广泛引用的开源工程实现。

**核心问题与数学思想。** 无人机需要快速获得障碍距离及其梯度，使轨迹优化器能询问“这里离最近障碍多远、该往哪边让”。TSDF 适合利用多帧深度观测得到平滑表面表示，但 TSDF 截断距离本身并不提供全空间的真正欧氏距离。Voxblox 在已融合的 TSDF 上增量维护 ESDF，通过 Raise/Lower Wavefront 传播距离变化，避免每一帧从头重建整个距离场。

~~~text
Depth / Point Cloud + Robot Pose
              ↓
TSDF fusion (integrated geometry)
              ↓
Incremental ESDF update
   ├─ raise wavefront: invalidate stale distance
   └─ lower wavefront: propagate improved distance
              ↓
ESDF value / gradient query
              ↓
Trajectory optimization + onboard MAV
~~~

**传感器、动力学与历史价值。** Voxblox 不绑定某一种相机或 LiDAR，但依赖标定可靠、位姿正确的深度/点云；其 ESDF 为路径优化提供几何代价，**不直接保证四旋翼动力学或未知区域安全**。原作者报告在单核 CPU 上实时构建地图，并完成无人机机载轨迹优化，证明了从感知到实时局部规划的完整工程链。

**今天仍在使用的思想。** 许多 TSDF/ESDF 地图、机器人轨迹优化器、可查询梯度的 Costmap 都延续了此思想：表面重建与安全距离查询是**两个不同的数据产品**，应拥有各自的更新频率、误差与版本。Voxblox 让 ESDF 的增量维护成本合理化；今天的 Mapless ESDF 研究进一步问：**如果只在几十毫秒中做几百次近场查询，连地图维护成本是否都应该省掉？**

**局限与后续。** 在快速运动、短 horizon、动态障碍和地图不断重建的情况下，TSDF/ESDF 的融合延迟与体素分辨率会成为新瓶颈。后续多分辨率地图、ESDF 局部增量更新、直接深度图查询都在修正不同使用场景的成本结构。不能因此认为 mapless 在全局探索、长期遮挡处理和大量复用查询中一定优于有地图方法。

**开源、可复现性与工程重读。** 原仓库 [ethz-asl/voxblox](https://github.com/ethz-asl/voxblox) 公开算法与 [ESDF 传播说明](https://github.com/ethz-asl/voxblox/blob/master/docs/pages/How-Does-ESDF-Generation-Work.rst)。最有价值的现代 A/B：固定同一批带位姿深度图，比较 Voxblox 增量 ESDF、仅当前深度图的 mapless query 和简单点云最近邻；统计每帧更新/预处理开销、每 100/1000/10000 次查询成本、误差、内存以及真实障碍漏检。哪个方案最好取决于**查询复用量和更新频率**，而不只取决于单次 query latency。

**来源：** [arXiv](https://arxiv.org/abs/1611.03631) · [IROS DOI](https://doi.org/10.1109/IROS.2017.8202315) · [官方代码](https://github.com/ethz-asl/voxblox)。

## 今日结论

今天的核心不是哪一种 SLAM 或神经模型更大，而是**系统能否显式管理物理时间、传感器健康、几何约束、技能执行与软件信任边界**。

LiDAR-Radar 切换承认“一个传感器持续输出并不意味着可以信赖”；mapless ESDF 承认“重建一张完整地图与眼前避障的查询预算不相同”。Chronos 把真实时间纳入注意力，PATACON 把约束流形几何纳入搜索。两者都证明，真实系统里已知的物理结构不应在进入模型前被无意丢弃。

BT-Agent 让 LLM 做慢速任务调度、行为树负责即时条件判断；SmolWAM 尝试在有限 GPU 内保留动作与未来状态联合预测。两者都表明部署可行性取决于能力切分，不只是主模型大小。

CRBugBench 说明审查智能体还不足以替代人类与确定性测试，SkillRelayBench 则说明持久缓存和文档可能把恶意影响带进下一轮无辜会话。自动化软件工厂不能只检查最终回答，必须维护提交身份、文件来源、工具权限和独立验证证据。

**一句话：把“能否信任、何时执行、是否可行、由谁推动、依据何种证据”都变成正式系统状态，可靠性才能被持续验证。**

## 最值得深入研究或尝试复现的方向

1. **烟尘 LiDAR 健康 Sidecar**：对 FAST-LIO + radar 同步日志建立健康特征和异常分数，先报警，再增加滞回切换及坐标系连续性测试。
2. **Mapless vs Voxblox 成本交叉点**：在相同嵌入式 GPU 上扫查询数量和感知频率，找出构建持久 ESDF 什么时候才真正划算。
3. **Chronos 实时时戳采集**：给 VLA 逐模态记录 capture/receive/execute 四类时间，再做固定 token、时间 embedding、time-aware RoPE A/B。
4. **Tangent-Space RRT 基线**：对闭链双臂约束，比较 RRT-Connect + IK Projection 与切空间导向搜索的 correction iterations、失败率与 P95 时间。
5. **Go2 行为树技能执行器**：定义 precondition、cancel、timeout、failure code，让任务层 LLM 永远不能越过高频保护和控制状态机。
6. **SmolWAM 端侧可移植性审计**：先核实 ONNX 导出、Attention 算子和量化误差，再考虑 RKNN；不要先承诺 RK3588 FPS。
7. **盲测 AI Reviewer**：在有真实回归 Bug 的旧 PR 上恢复引入提交，按 PR 复杂度切片比较 top-5 recall、precision 与人工纠错量。
8. **跨会话 SkillRelay 安全回归**：跨会话读取低信任 artifact 时保持来源和 trust label，不允许文件文字无审核升级成可执行权限配置。
9. **提交身份与 Agent 指标治理**：Enterprise 预览先核 pusher identity，Copilot 指标先核客户端版本/遥测完整性，再进行 ROI 计算。

## 参考资料

**最新公开批次：** [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

**定位、规划与控制：** [LiDAR/Radar 可靠性](https://arxiv.org/abs/2610.13788) · [Mapless ESDF](https://arxiv.org/abs/2610.13158) · [Chronos Policy](https://arxiv.org/abs/2610.13929) · [Chronos 官方项目](https://changhaowang.github.io/chronospolicy/) · [PATACON](https://arxiv.org/abs/2610.13195)。

**机器人 Agent 与端侧模型：** [BT-Agent](https://arxiv.org/abs/2610.13862) · [SmolWAM](https://arxiv.org/abs/2610.13740) · [SmolWAM 代码](https://github.com/iitimii/SmolWAM)。

**AI Coding：** [CRBugBench](https://arxiv.org/abs/2610.13668) · [SkillRelayBench](https://arxiv.org/abs/2610.13227) · [GitHub Commit Pusher 归属](https://github.blog/changelog/2026-10-12-push-attribution-public-preview/) · [GitHub Copilot IDE 指标修复](https://github.blog/changelog/2026-10-06-update-your-ide-to-restore-agent-activity-in-copilot-usage-metrics/)。

**经典论文：** [Voxblox](https://arxiv.org/abs/1611.03631) · [IROS DOI](https://doi.org/10.1109/IROS.2017.8202315) · [官方代码](https://github.com/ethz-asl/voxblox)。