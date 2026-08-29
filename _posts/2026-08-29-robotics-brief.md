---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-29"
date: 2026-08-29 09:00:00 +0800
description: "周末最新公开批次聚焦在线 LiDAR 外参与转向标定、接触辅助因子图定位、可证明前向树搜索、长时域人形感知行走、分钟级真机在线学习、实时零样本导航，以及 AI Coding 的动态子规划与紧凑行为测试。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-29

## 摘要

截至 2026-08-29 09:01（Asia/Shanghai），arXiv Robotics 最新公开批次仍是 2026-08-28，包含 35 条 new submissions、69 条总条目；Software Engineering 同日包含 27 条 new submissions、65 条总条目。今天是周六，严格最近 24 小时内高质量、可完整核验且未进入历史覆盖索引的主动态不足 5 条，因此按任务规范扩大到最近 7 天。本期最终 8 条主动态的 v1 提交于 8 月 26–27 日 UTC，全部明确标记为“时间回补”，没有把日报日期或 arXiv 列表日期写成论文首次提交日期。（[arXiv Robotics](https://arxiv.org/list/cs.RO/new)，[arXiv Software Engineering](https://arxiv.org/list/cs.SE/new)）

今天最值得优先看的是两条状态估计工作。第一条面向仓储轮式机器人，直接把 steering zero offset 与 planar LiDAR extrinsic 一起作为 EKF 状态在线估计，不需要外部定位基站或专用标定路线；作者使用 Ouster 32 线雷达、100 Hz 轮速/转角输入和 10 Hz LiDAR，在自然运动中同时收敛转向偏置和 `x/y/yaw` 外参，并进一步验证转向偏置修正对闭环 cross-track error 的改善。它的价值不是“又一个标定算法”，而是把会因维护、装配和机械磨损缓慢变化的标定量升级成了长期状态估计问题。（[论文](https://arxiv.org/abs/2608.26789)）

第二条来自水下采样：Contact-Aided Factor-Graph Localization 把机械臂吸附接触视为高置信几何因子，在低纹理、近似平面的海床上用实际物理交互创造结构约束。系统将自适应视觉里程计、learned object detection、DVL/机载传感器和 suction contact event 一起放进 smoothing factor graph；视觉弱时根据 inlier statistics 降权，接触则形成类似 implicit loop closure 的约束，不依赖外观式 place recognition。它提醒一个很重要的机器人估计原则：当纯感知退化时，机器人本体的接触、关节运动、轮地约束也可以成为定位观测，而不是只在控制层使用。（[论文](https://arxiv.org/abs/2608.26932)）

规划控制侧，DFT*（Dispersive Forward Tree Search）尝试把 forward-propagation kinodynamic planning 从“经验上好用”推进到带确定性有限样本 near-optimality 保证的算法。它为 differential-flat nonlinear systems 构造 locally dispersive control commands，并使用 cost-conditioned dominance pruning 把原本随 horizon 指数增长的树压到多项式规模；breadth-first expansion 又天然适合 GPU 并行。作者以 8 个 SM 模拟 Jetson Orin Nano 计算层，在 unicycle、trailer car 和 quadrotor 上与主流 kinodynamic planner 比较，并实现了 dynamic environment 的 receding-horizon WWDFT*。静态特化版本可在相同解质量下最高降低约 44 倍规划 wall time，而从 Orin 级并行资源扩到 RTX 4090 时 wall time 最高再缩短约 15 倍。（[论文](https://arxiv.org/abs/2608.26314)，[代码](https://github.com/croshank/DFTSearch)）

人形控制方面，SOLO 的亮点不是更大的 height-map 网络，而是对“地形重建为什么会把 stepping stone、台阶边缘等动作关键结构抹平”给出针对性设计。Query Reconstructor 使用 Fourier cell query 从 depth-proprio tokens 中按位置检索局部证据，Trajectory-Aware MSE 又把 teacher/student 下一状态差异写入 PPO reward，通过 GAE 将未来误差回传到更早动作。Omni 人形只使用胸部 RealSense D455 与 proprioception，50 Hz 输出 25 维 joint target offset；Jetson AGX Thor 上完整 observation-build + inference + action post-processing 平均约 1.15 ms。作者报告零样本完成一次连续 1.5 km 室外路线、超过 100 级楼梯，无外部定位或地图输入。（[论文](https://arxiv.org/abs/2608.26583)，[项目页](https://sunpihai-up.github.io/solo/)）

真机在线学习方面，Robot Juggling 展示了一条比“先把 sim2real 做得很准再上线”更实用的路线：保留一个即使不准确也有全局结构的 prior model，只利用不断积累的真实经验学习局部 correction；同时用预计算 Mutually Reachable Set 将 successive skill transition 约束在既可到达、又能保证下一步仍可继续的状态区域。AthenaZero 双臂三指手使用 30 Hz 同步相机，场景采集到 3DoF 球位置约 0.1 s 延迟；系统能在不足 5 分钟真实交互中学习 cascade、tennis、half-shower、shower、box 五种三球模式。这里最值得迁移的不是杂耍，而是“真实在线学习 + 可达/可存活集合硬约束”的组合。（[论文](https://arxiv.org/abs/2608.26800)）

语义导航方面，RTNav 的贡献很像一次对 Foundation Model 导航评测范式的纠偏：传统 Habitat benchmark 里，20 ms 和 2 s 推理被视为同一个 action cost，环境会等 Agent；真实机器人却不会暂停世界。RTNav 让 perception、mapping、planning、navigation 按各自频率异步并行，真实时间继续流逝。它在 HM3D-v1、HM3D-v2、HM3D-OVON 的 real-time 版本上将 SR 最高提高 11 个百分点、SCT 最高提高 5.1 点，同时将 idle time 相对所有对比方法降低 14% 以上，并获得超过 20 倍的 unique detection frames/s。项目还公开了 Stretch 3 + Jetson AGX Thor 的实机仓库。（[论文](https://arxiv.org/abs/2608.26496)，[项目页](https://generalroboticslab.com/RTNav)，[代码](https://github.com/generalroboticslab/RTNav)，[实机代码](https://github.com/generalroboticslab/RTNav-RealWorld)）

AI Coding 侧，本期两项工作都在解决“测试和计划必须跟着真实执行状态走”。DeepRepro 将 paper-to-code 从一次性的 upfront plan 改为 execution-state-aware subplanning：repository skeleton 只是初始 blueprint，之后每一轮根据已经生成的文件、依赖、运行反馈和失败状态重新生成细粒度 implementation subplan，并配合 bounded repair、memory compression 与过程可视化。PaperBench Code-Dev 五论文子集上，`deepplan+ref` 平均 84.28，高于 fast 路径的 82.07；论文还报告在共享子集上超过 PaperBench Best@3 human baseline。（[论文](https://arxiv.org/abs/2608.26557)，[代码](https://github.com/ruyisy/DeepRepro)）

FaultLens 则针对 AI 生成的 operational program：几条手写例子太弱，穷举所有场景又太贵。它先完整执行一次 rich probe domain，将“哪个 probe 能杀死哪个 fault”缓存为稀疏证据，再从历史程序代际学习 probe ordering；一部分预算贪心利用已知 fault-kill 结构，另一部分保留 mutation-independent diversity 来覆盖未知故障族。32 个 probe 只使用穷举域的约 1.2–2.0%，却覆盖未来程序中 576/582、即 99.0% 的动态可杀故障；完整 fault family 被留出时，diversity 将 macro coverage 从 84.6% 提高到 94.9%。它明确不是 correctness proof，但很适合作为 Agent 生成工作流、规则、调度器和控制逻辑的低成本发布前 behavioral gate。（[论文](https://arxiv.org/abs/2608.26746)）

本轮同时检查了近期模型厂商公开入口，没有发现 8 月 28–29 日需要挤掉上述机器人 / SLAM / 控制工作的全新旗舰基础模型正式发布。OpenAI 当前旗舰 GPT‑5.6 页面最近一次公开价格更新仍是 8 月 21 日，因此本期不重复报道已进入覆盖索引的模型条目。（[GPT‑5.6 官方页](https://openai.com/index/gpt-5-6/)）

## 1. 在线联合标定：把转向零偏和 LiDAR 外参当作“会慢慢漂的状态”

**时间回补：arXiv v1 提交于 2026-08-27 08:19 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.26789)）

### 为什么重要

仓储 WMR / AGV 的路径“蛇形”和 cross-track error 很多时候不是 controller 本身调得差，而是 steering encoder 的机械零位和 LiDAR-to-body 外参发生了系统偏差。传统工程往往依赖 CAD、卷尺或者人工用遥控器把轮子“看起来摆正”，维修拆装之后也未必重新严格标定。

这篇工作的价值在于把四个慢变量直接并入 estimator：`x_off / y_off / theta_off / steering_offset`。它们不是每天离线重新跑一次 calibration job，而是和车辆姿态一起被 EKF 持续估计，并允许通过小 random walk 追踪装配、载荷和机械磨损带来的缓慢变化。

### 算法模块

系统保留完整 bicycle kinematics，而不是把转向输入简化成直接可测的 yaw rate。真实转角写成：

```text
steering_true = steering_measured - steering_offset
```

这样 steering bias 会直接改变预测曲率，因此保持可观测耦合。EKF state 除 `x/y/yaw` 外，增加 planar LiDAR extrinsic 和 steering bias。

LiDAR 侧先把 Ouster 32-channel 点云滤除动态物体、地面和顶棚，再压成 2D scan；scan-to-map 使用局部离散 grid search 产生 LiDAR relative motion。Estimator 随后使用经典 motion-based calibration constraint：body frame 和 LiDAR frame 的相对运动必须通过同一个 rigid extrinsic 相容，在 `SE(2)` 中形成 EKF measurement residual。

### 传感器与动力学假设

真实平台的 encoder longitudinal velocity 与 steering angle 为 100 Hz，LiDAR 为 10 Hz。核心假设是 bicycle model 在小侧滑条件下成立，而且自然运动里必须存在足够 excitation。论文明确指出不需要预编程标定轨迹，但“自然运动”并不等于任何运动都可观：长期直行几乎不提供外参和 steering offset 分离所需的曲率信息。

另一个边界是系统使用 LiDAR odometry 自身作为几何参考，而实验没有外部高精度 ground truth；作者只说明评估区域中 onboard LiDAR odometry 经验精度约 10 cm。因此当前结果更适合证明在线收敛和控制收益，而不是宣称达到毫米级绝对外参真值。

### 实时性、鲁棒性与结果

作者在 Tugger 和 Nano 两套 WMR 上跨多天测试，其中 Tugger 包含空载和 500 kg 负载。参考 `x_off` 约 0.434 m 时，收敛结果约为 0.43–0.44 m；`y_off` 约 5 mm，yaw offset 约 0.72–0.73°，steering offset 约 0.91–0.92°。即使所有 calibration state 从 0 初始化、只放大初始 covariance，也能收敛到接近的稳态区域。

更重要的是论文把 calibration 结果重新应用到闭环路径跟踪，直接量化了 steering offset correction 对 CTE 的改善。这是比只展示外参数值更有工程意义的闭环验证。

### 可复现性与风险

当前没有稳定公开代码仓库。工程上线时尤其不能让 estimator 在低 excitation、轮胎严重打滑或 LiDAR localization 已经失败时继续“自信地改外参”。应该给 calibration state 增加 observability、innovation consistency 和 update gate。

### 适合谁关注

仓储 AGV、牵引车、Ackermann / bicycle-model WMR、长期运营移动机器人，以及拆装维护后容易发生传感器与转向标定漂移的团队。

### 工程落地启发

生产系统可以把静态 TF 升级成：

```text
nominal_extrinsic
online_delta
covariance
excitation_score
last_verified
update_enabled
```

只有在转弯激励充分、LiDAR odometry 健康、innovation 统计正常时允许在线更新；其他时候只监控，不写回生产配置。这样“标定漂了”会变成可观测故障，而不是地图开始扭曲后才人工猜原因。

## 2. Contact-Aided Factor Graph：当海床没有纹理，就让机器人“碰一下”创造定位约束

**时间回补：arXiv v1 提交于 2026-08-27 10:34 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.26932)）

### 为什么重要

低空水下采样特别容易同时遇到视觉和惯性导航的结构性弱点：朝下相机看近似平面、低纹理海床时会出现尺度歧义、横向退化和不稳定 feature tracking；IMU + DVL 虽能稳定短时速度，却没有天然机制把累积漂移重新拉回某个历史几何位置。

论文最有意思的地方是把“机械臂吸附到采样点”从任务动作变成 localization primitive。机器人本来就需要触碰目标，既然接触表示末端与某个世界对象发生了强物理关系，就可以把它写成高置信几何因子。

### 算法模块

整体是 smoothing-based factor graph。视觉里程计提供 relative-pose factor；learned object detector 提供目标的 bearing/range landmark factor；DVL 和其他 onboard sensor 保持连续运动约束；suction contact event 则形成高置信 contact factor。

视觉部分不是固定权重：系统根据 inlier statistics 调整 VO relative-pose 和 landmark factor 的不确定度，避免一帧低纹理图像把整个图强行拖歪。

真正关键的是 contact factor：当机器人再次与同一个采样对象建立接触，系统相当于获得了“我此刻又到达这个实体”的物理证据，从而产生类似 loop closure 的长期约束，而且不要求图像外观足够独特。

### 传感器与系统假设

这种方法依赖 contact identity 足够可靠。吸盘确实接触到了哪个对象、对象是否在任务期间移动、末端执行器到机体的运动学是否准确，都会直接影响约束质量。

它也不是“用接触替代视觉”。没有接触发生的长航段仍然依赖 VO、DVL 和惯性链路；contact 更像稀疏但非常强的结构锚点。

### 实时性、鲁棒性与结果

论文支持运动中完整在线初始化，并在水池、港口和仿真环境测试。摘要报告 contact-induced constraints 相对 filtering-based navigation 与无 contact 的 graph formulation 都显著降低轨迹漂移，并改善 object revisit accuracy。

公开材料没有给出一个适合安全引用的统一 solver Hz，因此本期不把它包装成“某个固定频率的实时 SLAM”。更重要的是 graph 中不同 factor 的质量管理方式：弱视觉自动降权，真实接触作为强证据进入 smoothing。

### 可复现性与风险

当前未见稳定官方代码。高置信 contact 如果身份匹配错误，反而会形成比普通视觉误匹配更危险的强假回环，因此必须保留 object identity confidence、contact force/attachment validity 与因子撤销能力。

### 适合谁关注

水下机器人、采样机器人、移动操作、巡检开关/阀门/插接任务，以及任何“机器人会反复触碰已知设施”的长期定位系统。

### 工程落地启发

这套思想很容易迁移到工业巡检：反光标志、充电桩对接、机械插销、按钮、门把手、轮子接触约束都可以成为低频高置信 factor。状态估计不必永远只消费 LiDAR / camera / IMU；任务动作本身也可以产生几何观测。

## 3. DFT*：前向传播式动力学规划，也开始拥有确定性有限样本近最优保证

**时间回补：arXiv v1 提交于 2026-08-26 18:46 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.26314)，[官方代码](https://github.com/croshank/DFTSearch)）

### 为什么重要

很多 kinodynamic planner 依赖 steering function：给定两个状态，求一条满足非线性动力学的边值轨迹。但真实 quadrotor、trailer car 或复杂非线性系统未必有稳定、便宜的 state-to-state steering solver。

另一类 propagation planner 直接枚举控制输入向前 rollout，避免边值求解，却经常面临两个问题：需要多少 sample 才够没有明确结论；树随 horizon 爆炸，工程性能也差。

DFT* 尝试同时解决理论和实现问题。

### 算法模块

对 differential-flat nonlinear systems，作者在 control space 构造 locally dispersive command sets，保证有限大小的 forward tree 中包含一条接近最优的轨迹。

若不考虑 cost，覆盖认证轨迹族需要随 horizon 指数增长的树；DFT* 引入 cost-conditioned dominance pruning，只保留状态空间 cell 中对未来仍有价值的代表节点，从而把树规模压到 horizon 的多项式级。

搜索采用 breadth-first expansion，每一层大量 rollout 可以并行映射到 GPU。静态场景还能使用更激进的 static dominance pruning 与 A* beam ordering。

### 动力学假设

理论覆盖依赖 differential flatness 和作者构造 dispersive control set 的条件。对于强接触、人形混合动力学、不可微碰撞模式，不能直接把当前证明照搬。

另一方面，forward propagation 的优势是低层只需要前向动力学，不需要精确的 boundary-value steering。对于无人机、汽车、拖车等连续系统，这一点很有工程吸引力。

### 实时性与结果

作者用 GPU SM 数量模拟不同 onboard 级别：8 SM 对应 Jetson Orin Nano、16 SM 对应 AGX Orin、RTX 4090 使用完整 128 SM。静态 Dynobench 问题中，特化搜索最高可在相同解 cost 下减少约 44 倍 planning wall time；同一计算扩大到桌面 GPU 时 wall time 最高进一步缩短约 15 倍。

在线版本 WWDFT* 在动态环境做 receding-horizon replanning。论文的动态实验中，三类任务上的 WWDFT* 都达到 100% 成功；部分对比方法虽然规划出路径，但执行轨迹会穿过动态障碍或违反微分约束。

### 鲁棒性、可复现性与风险

代码已经公开，可复现性较高。需要注意论文的“embedded-tier”是通过限制桌面 GPU kernel 使用的 SM 数量来模拟，不完全等价于真实 Orin 的内存、带宽、功耗和调度环境，所以真正上 Jetson 仍应重测 P50/P95/P99 wall time。

### 适合谁关注

无人机局部规划、拖车/车辆 kinodynamic planning、GPU sampling planner、需要实时 receding-horizon 搜索但不希望依赖非线性 steering solver 的团队。

### 工程落地启发

它提供了一条 RRT/MPPI 之外的路线：先为自己的真实控制接口设计“低 dispersion、物理可执行”的有限 command library，再做并行 forward tree。对于无人机，这通常比直接在每个时间步对 `vx/vy/vz/yaw` 独立白噪声采样更接近真实可执行动作空间。

## 4. SOLO：把地形重建从“稠密输出”改成“按控制需要查询”

**时间回补：arXiv v1 提交于 2026-08-27 03:49 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.26583)，[项目页](https://sunpihai-up.github.io/solo/)）

### 为什么重要

人形 perceptive locomotion 常见做法是把 depth 压成 dense height map，再给 locomotion policy。但稠密 reconstruction 的平滑 inductive bias 会把窄踏板、台阶锐边、stepping stone 之间的断裂变得“视觉上更连续”，恰好抹掉控制最需要的结构。

SOLO 的 Query Reconstructor 不要求一次重建一张尽可能平滑的完整地形，而是针对固定 spatial cell 发送 Fourier-encoded query，从 depth-proprio token 中检索该位置真正相关的局部证据。

### 算法模块

QR 负责空间查询式地形重建；teacher/student distillation 侧，Trajectory-Aware MSE 不只比较当前动作，还将下一状态的 teacher-student disagreement 加进 PPO reward，再利用 GAE 把未来状态差异的影响向前传播。

部署阶段 teacher、critic、AMP discriminator 和 privileged label 全部移除，只保留 chest depth、proprioception、QR 与 student policy。

### 传感器与控制接口

真实 Omni 人形只使用一只胸部 RealSense D455 和 proprioception，不需要 motion capture、外部 odometry 或外部地图。Raw depth 为 640×480@60 Hz，网络内部缩小并维护短 temporal history；policy 50 Hz 输出 25 维默认关节位置 offset，由低层控制器跟踪。

这种感知方案很适合长期 terrain locomotion，但它不是全局导航定位：机器人依然不知道自己在建筑的绝对位置，SOLO 解决的是本体附近“下一步踩哪里”的局部感知控制。

### 实时性与真机结果

Jetson AGX Thor MAXN 上，1000 次 batch-1 TensorRT inference 平均 1.03±0.21 ms，p95 1.59 ms；完整 observation-build、inference、action post-processing 平均 1.15±0.23 ms，落在 50 Hz 控制的 20 ms 周期内，TensorRT engine 约 7.56 MB。

仿真中 QR 将 height-map L1 error 降低约 3.3–4.0 倍；stress terrain 平均通过率 97.5%，stepping stone 96%。实机使用同一感知/策略栈完成一次不中断 1.5 km 室外路线、超过 100 级楼梯，并展示超过 10 层楼梯上行。

### 鲁棒性、可复现性与风险

项目页已公开，但需要继续核验代码/权重开放程度。真实 1.5 km 是很有价值的 endurance evidence，但不能自动外推到雨雪、镜面、强阳光、湿滑地面或 D455 深度完全失效场景。

### 适合谁关注

人形/轮足 perceptive locomotion、楼梯、非结构化地形、端侧深度感知，以及希望减轻 full terrain reconstruction 计算和过度平滑问题的团队。

### 工程落地启发

对机器狗或楼梯巡检，不一定要维护高分辨率全局 3D 地形图。可以将高分辨率几何限制在 robot-centric footprint 周围，并按未来 foothold / wheel-contact query 只提取真正影响下一步控制的局部高度和边缘证据。

## 5. Robot Juggling：不完美模型也有价值，关键是只在真实经验附近学习修正

**时间回补：arXiv v1 提交于 2026-08-27 08:39 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.26800)）

### 为什么重要

很多 sim2real 项目陷入一个误区：如果模型不够准，就继续堆参数辨识，直到仿真几乎复制现实，再允许真机学习。这篇工作证明另一条路线：一个明显不够准、甚至无法连续完成一轮任务的 prior model，仍然可以为探索提供正确的全局趋势；真实机器人只需要在自己真正访问到的局部区域学习 correction。

### 算法模块

Regularized memory-based learner 保存每次真实 `(state, command, outcome)`，局部区域优先使用真实经验拟合 correction，而在经验稀疏处继续靠 global prior 外推，避免每次学习新东西都把原有结构推翻。

Task-level planner 将目标落点等命令转换为关节位置/速度/加速度的 transition state；真正的安全核心是离线构造的 Mutually Reachable Set。它通过 B-spline 参数化的 forward reachable 与 backward reachable 集合取交，形成凸多面体：任何保留状态都既能从共同区域到达，也能再安全进入后续动作。

在线 planner 直接把这个 polytope 写成线性约束，因此 learner 即使提出激进的新目标，也不能把机械臂送进“这一步能到、下一步已经无解”或“以后可行、但这一步根本到不了”的状态。

### 传感器与系统接口

AthenaZero 是低惯量双臂平台，每只手三根欠驱动手指。同步相机 30 Hz，从场景采集到计算出球的 3DoF tracked position 延迟约 0.1 s；perception、learning、task planning 和低层 motion generation 采用异步多速率结构。

### 真机学习速度与结果

系统在少于 5 分钟真实交互内组合出 cascade、tennis、half-shower、shower、box 五种三球模式。五次完全从头实验中，cascade 都在第 8 次尝试前学会，并连续成功重复三次；统计的约 5 分钟 wall-clock 包含人工 reset。

论文还显示，如果去掉 MRS，绝大多数 task-level candidate 会落到预计算安全内集之外，其中存在既不可达又不可持续的状态。这说明真机在线学习的关键不是“探索慢一点”，而是先定义哪些状态允许被探索。

### 鲁棒性、可复现性与风险

当前安全集主要考虑 joint/actuator kinodynamic limit，使用的是轻量球；作者也明确指出，重物或大接触力任务需要进一步把环境接触后果纳入 safety constraint。

### 适合谁关注

动态操作、抛接、双臂协同、真机 continual learning、希望减少 sim2real 模型精度依赖的团队。

### 工程落地启发

对工业技能在线校正，可以采用：

```text
global prior model
+ local real residual memory
+ hard reachable/viable envelope
```

网络或 learner 只在 envelope 内优化效率，安全状态集合由动力学、限位、碰撞和力约束单独维护。这样真机数据可以快速改善技能，而不会让“在线学习”获得越过硬件边界的权限。

## 6. RTNav：Foundation Model 导航必须用真实墙钟时间评测

**时间回补：arXiv v1 提交于 2026-08-27 00:35 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.26496)，[项目页](https://generalroboticslab.com/RTNav)，[代码](https://github.com/generalroboticslab/RTNav)，[实机代码](https://github.com/generalroboticslab/RTNav-RealWorld)）

### 为什么重要

传统 Habitat ObjectNav 是 step-based：Agent 算多久，世界都会等它。因此一个 20 ms detector 和一个 2 s VLM，在 benchmark 里可能完全等价。现实里机器人在这 2 秒里可能继续行驶、错过目标、发生碰撞，或者只是原地停着浪费任务预算。

RTNav 的贡献首先是把 wall-clock 重新纳入 benchmark，然后再设计能够适应真实时间流逝的架构。

### 算法模块

perception、mapping、high-level reasoning/planning、local navigation 不再顺序串联，而是各自按 native frequency 异步执行。高成本 Foundation Model 查询不会冻结低层控制；高频 detector 也不必等待 VLM 完成一轮推理才处理下一帧。

系统维护 object memory 与 verification，使用 semantic frontier 选择探索方向；只有真正需要语义验证时才调用昂贵模块。

### 传感器与真实部署

仿真 evaluator 让 Habitat 固定 30 Hz 继续推进，Agent 单独容器通过 ROS 2 与环境交互，因此 baseline 的计算耗时真实计入 wall-clock。

真实系统使用 Hello Robot Stretch 3，RGB-D 来自头部 RealSense D435i，底盘原生 2D LiDAR 运行 HectorSLAM 获得全局 pose；SLAM occupancy 与 RGB-D 3D obstacles 再融合生成导航图。全部 RTNav 模块跑在一台 Jetson AGX Thor 上，通过 Wi-Fi 与机器人通信。

### 实时性与结果

在 HM3D-v1/v2/OVON 实时版本上，RTNav 相比先前方法 SR 最高提升 11 个百分点，SCT 最高提升 5.1 点。异步架构使 idle time 至少减少 14%，unique detection frames/s 相比同步基线超过 20 倍，并明显缩短 detection blind gap。

代码仓库还提供同步/异步统一 evaluator，支持多种 baseline，方便直接在目标硬件上公平复测。

### 鲁棒性、可复现性与风险

作者当前主要考虑静态环境。动态人群、移动障碍与异步 stale-state 问题仍需要更严格的 timestamp / freshness 管理。实际系统也仍依赖传统 SLAM 和局部导航，Foundation Model 并没有取代底层几何栈。

### 适合谁关注

语义导航、VLM/VLA 移动机器人、Foundation Model + ROS 2、多速率 Agent，以及现在只在同步仿真里评估高层模型的团队。

### 工程落地启发

以后所有大模型机器人任务建议把日志从“每步耗时”升级成事件时间线：

```text
observation_time
perception_ready
reasoning_ready
command_generated
command_executed
command_age
```

模型升级以后不只比较 success rate，还必须比较 wall-clock completion、idle ratio、stale action ratio 与 P95/P99 blind gap。

## 7. DeepRepro：Paper-to-Code 不是先列计划，再照计划写完 50 个文件

**时间回补：arXiv v1 提交于 2026-08-27 02:54 UTC；CIKM 2026 Demo Track 已接收；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.26557)，[代码](https://github.com/ruyisy/DeepRepro)）

### 为什么重要

复现论文是最典型的长时域 Coding Agent 任务之一。最开始读 paper 时，Agent 根本不知道真正实现到第 20 个文件以后会出现什么接口冲突、依赖问题或数值错误。一次性 upfront plan 写得再详细，也很快会与真实 repository state 脱节。

DeepRepro 因此把 repository construction 当成不断变化的状态机，而不是静态 checklist。

### 系统结构

Blueprint planning 先从论文提炼 repository skeleton：模块、数据流、依赖、evaluation protocol。

之后 repository-aware orchestration 进入 round-level loop。每轮 planner 都读取已经存在的文件、当前依赖、运行反馈、失败和未完成目标，再生成细粒度 subplan。实现过程中还配合 asynchronous memory compression、bounded repair，避免长任务中 context 无限增长或一次失败触发无边界改写。

过程 UI 则显式展示当前阶段、中间失败和 repository state，降低“Agent 运行几个小时以后没人知道它到底在干什么”的不可观测性。

### 结果与突破性工程价值

PaperBench Code-Dev 基于 20 篇 ICML 2024 Spotlight/Oral 论文。五论文固定子集上，`deepplan+ref` 平均 84.28，`deepplan` 84.22，`fast+ref` 82.11，`fast` 82.07。论文还报告 DeepRepro 在共享子集上超过 PaperBench Best@3 human baseline。

更值得关注的是，系统收益来自“根据真实仓库状态持续重规划”，而不是换一个更强底模。这和长期企业 Issue/重构任务非常接近。

### 是否适合真实研发流程

适合，但每次 replanning 都必须绑定固定 git revision 和执行证据。否则 Agent 可能根据已过期的 test result 或旧文件状态继续规划。

最好将阶段 handoff 保存为 artifact，而不是自然语言聊天历史，例如：

```text
repo_sha
implemented_modules
failing_commands
unresolved_interfaces
next_subplan
validation_evidence
```

### 权限、安全与可验证性风险

Paper reproduction 往往需要安装依赖、下载数据、运行外部脚本。真实企业环境应该将 shell/network 权限与 repository write 权限分层，不让“为了复现论文”自动升级到任意网络执行权限。

### 适合谁关注

科研代码复现、复杂原型生成、长时间 Coding Agent、从论文自动实现算法，以及内部希望自动复现 SLAM / 控制论文的团队。

### 工程落地启发

如果想构建“论文→可运行 ROS 包”的 Agent，不要直接让一个模型从 PDF 写完整仓库。更合理的是：Blueprint → first runnable skeleton → benchmark smoke test → state-aware subplan → bounded repair → 独立 validator。每一次状态改变都重新规划剩余工作。

## 8. FaultLens：AI 生成运行逻辑不必每次穷举测试，但必须保留可审计的行为证据

**时间回补：arXiv v1 提交于 2026-08-27 07:37 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.26746)）

### 为什么重要

Agent 生成 operational program，例如资源调度、策略规则、workflow 或控制逻辑时，最危险的 bug 往往只在少数环境组合、时间窗口或边界值触发。只运行几条“典型例子”很容易漏掉；每个版本都跑完整 exhaust domain 又可能成本过高。

FaultLens 的目标不是让模型预测“哪些测试可能有用”，而是先执行真实测试建立 evidence，再学习如何以较小预算重放最有杀伤力的一组 probe。

### 算法模块

系统对 rich probe domain 做一次完整执行，保存 sparse fault-probe kill cache。后续 program generation 只使用前几代程序的已执行证据来构造 probe ordering。

Active greedy 优先选择历史上能杀掉最多未覆盖 fault 的 probe；diversity component 不依赖 mutation outcome，而是覆盖 scenario、case、template、temporal bin 等结构维度。Hybrid 交替使用两者，避免系统只会检查历史上已经见过的故障族。

### 结果

评估覆盖 20 个 generated operational policy、4 种环境、10 个 execution seed、2160 个受控 program transformation，共执行 4,120,200 个 program-probe pair。

32-probe hybrid 在未来 generation 中覆盖 576/582、即 99.0% 的 dynamically killable faults，只使用完整 domain 的约 1.2–2.0%。当一个完整 fault family 从 ordering construction 中留出，diversity 将 scenario-family macro coverage 从 84.6% 提高到 94.9%。部署研究中的 conservative admission rule 还将 severe tail regression 从 15/20 program-environment group 降到 0/20。

### 突破性工程价值

最值得借鉴的是“测试优先级本身也必须有 provenance”。FaultLens 的 cache 保留 stable probe ID、program hash、seed、fault transformation 和具体 killing evidence，因此一个 probe 被放在前面不是因为 LLM 说它重要，而是因为历史执行真的证明它能抓到某类错。

### 权限、安全与可验证性风险

论文明确指出 FaultLens 是 prioritized evidence mechanism，不是 correctness proof。未被 probe 覆盖的逻辑仍可能失败；历史故障分布突然变化也会降低 greedy ordering 的价值。

所以 compact suite 适合做快速 admission gate，完整 regression / formal verification 仍应保留在高风险发布链路中。

### 适合谁关注

Coding Agent 生成 workflow、PLC/状态机、机器人任务逻辑、云端调度器，以及每个版本都需要在大量离散场景中做回归的系统。

### 工程落地启发

可以从现有机器人 regression bag / scenario 开始维护 `scenario → failure signature` 稀疏矩阵。PR 阶段先跑 20–50 个高价值 scenario，nightly 再跑全量。这样测试预算可以根据真实历史故障自适应，而不是永远固定一组“祖传 smoke test”。

## 经典论文回顾

### Kalibr / Unified Temporal and Spatial Calibration：为什么多传感器融合里“时间偏移”不能只靠改时间戳

**发表时间与历史位置：** Paul Furgale、Joern Rehder、Roland Siegwart 的《Unified Temporal and Spatial Calibration for Multi-Sensor Systems》发表于 2013 IEEE/RSJ IROS，页码 1280–1286，DOI `10.1109/IROS.2013.6696514`。它和 Furgale 等人在 ICRA 2012 的 continuous-time batch estimation 工作一起，构成后来 Kalibr 工具链最关键的数学基础之一。（[IEEE DOI](https://doi.org/10.1109/IROS.2013.6696514)，[ETH 记录](https://www.research-collection.ethz.ch/items/487b06bb-dcbe-411d-ab46-8580147273ac)，[Kalibr 官方代码](https://github.com/ethz-asl/kalibr)）

### 核心问题

相机 20–30 Hz、IMU 100–1000 Hz，两个传感器的采样时刻本来就不同；更糟的是，驱动、硬件时钟和系统调度还可能带来未知 offset。如果先把时间差“拍脑袋修到差不多”，再单独估外参，时间误差会被几何外参、速度和 IMU bias 吸收，最后得到一组在某段数据能用、运动一快就暴露问题的参数。

2013 论文的关键突破是**把空间外参和时间 offset 放进同一个 maximum-likelihood batch estimation**，而不是先时间后空间两阶段分开处理。

### 关键数学思想

离散关键帧方法很难对任意 sensor timestamp 直接求状态。连续时间 trajectory 则用 temporal basis / spline 表示整条运动轨迹：

```text
continuous trajectory x(t)
        ↓
任意 camera / IMU timestamp
        ↓
直接求 pose / derivative
        ↓
同时优化 extrinsic + temporal offset
```

因为轨迹可以在任意时间查询，时间偏移参数只需要改变“这条 measurement 应该落到轨迹的哪个 t 上”，就能自然进入同一个 likelihood / residual framework。

这也是今天 rolling-shutter、事件相机、异步 LiDAR、continuous-time LIO 中大量方法的基础思想之一。

### 传感器与可观测性假设

联合估计并不意味着任何数据都能标定。运动必须同时激励需要估计的 rotation / translation / temporal offset；如果设备长期静止或只做单轴运动，一些参数仍然不可观。

时间偏移和外参之间也高度相关：高速角运动能让毫秒级偏移产生明显几何误差，从而帮助估计；低动态数据则可能让完全不同的参数组合拥有近似 residual。

### 当年为什么重要

它把“硬件同步不完美”从工程上的预处理问题，变成 estimator 中可以严谨建模的系统参数。对于消费级相机、IMU 与复杂 ROS/驱动链，这极大降低了必须先拥有完美硬件同步的门槛。

Kalibr 后续发展成视觉惯性标定事实上的经典工具之一，官方仓库后来继续支持 multi-camera、camera-IMU spatial/temporal calibration、multi-IMU extrinsics / intrinsics 和 rolling-shutter camera calibration。仓库初始公开发布于 2014 年 6 月，并采用 BSD 类许可证。

### 今天仍在使用的思想

第一，**时间同步是一等状态，不是日志后处理细节。**

第二，**异步传感器最好在共同连续时间轨迹上建模，而不是强行插值到某个主传感器时刻。**

第三，**标定必须讨论可观测性。** 优化器给出数字不代表数据真正约束了该参数。

第四，**外参和时间偏移应该一起验证。** 一套外参在低速数据上很好，高角速度时地图抖动，很可能实际是时间偏移被外参吸收。

### 已被后续扩展的部分

原始 Kalibr 主要围绕 camera/IMU；今天的机器人系统还需要 LiDAR-IMU、multi-LiDAR、GNSS lever arm、wheel scale、rolling shutter、事件相机和在线漂移监测。很多现代方法还加入 analytic observability、online calibration state、sliding window 与 hardware timestamp correction。

而且生产系统未必适合永久在线自由修改所有 calibration parameter。在线 estimator 可以监测 drift，但生产 TF 是否真的更新，应经过 excitation、covariance、重复性和回归验证。

### 公开代码与可复现性

官方 `ethz-asl/kalibr` 仓库仍公开，引用页面明确列出 2013 IROS 联合时空标定论文、2012 continuous-time batch estimation，以及后续 multi-IMU / rolling-shutter 扩展。代码较老，依赖环境可能需要容器化，但数学和工程参考价值仍很高。

### 对当前工程项目的重新解读

对于多 LiDAR、远置 IMU、轮速和 RTK 系统，建议把“标定文件”升级成一个有证据链的资产：

```text
sensor pair
extrinsic mean + covariance
time offset + covariance
excitation / observability score
source dataset
software version
last verified
regression result
```

尤其 IMU 与 LiDAR 物理距离较大时，角速度会通过 lever arm 放大动态误差；几毫秒 timestamp mismatch 也会在急转弯时直接表现成点云去畸变错误。地图抖动时，第一件事不应总是换 ICP/LIO，而应先验证时间与外参是否仍在可信区间。

## 今日结论

今天最明确的状态估计趋势是：**机器人开始把“非视觉、非 LiDAR 的物理结构”正式写进 estimator。** WMR 在线联合标定使用 bicycle kinematics 让 steering bias 与 LiDAR extrinsic 可被持续观测；水下 Contact-Aided Factor Graph 更进一步，把真实接触事件当成定位约束。结合 Kalibr 的经典时空联合估计来看，一个成熟状态估计系统不应该只有 pose，它还应该显式维护 calibration、time offset、sensor health 和任务产生的结构因子。

控制规划侧的共同信号是：**在线计算预算要花在“真正有价值的可达空间”里。** DFT* 用 dispersive command 与 dominance pruning 避免无意义地扩展 forward tree；Robot Juggling 用 MRS 把真机学习限制在既能到达、又能继续下一步的状态区域。二者一个偏全局规划，一个偏动态技能学习，但都在减少“先生成大量物理上没价值的候选，再靠代价函数淘汰”的浪费。

SOLO 与 RTNav 则从两个时间尺度强调系统结构。SOLO 把局部地形表示改成 control-query-driven reconstruction，不再执着于一张视觉上平滑的完整 height map；RTNav 则让感知、语义推理与导航按各自频率异步运行，不再让最慢 Foundation Model 决定整个机器人控制周期。真正的机器人 AI 系统越来越像多速率实时系统，而不是一个同步 Transformer pipeline。

AI Coding 方向同样在回归软件工程本质。DeepRepro 说明计划必须持续对齐真实 repository state；FaultLens 则说明测试优先级必须来自真实执行证据，而不能只依赖模型直觉。对于长期 Agent，最值得积累的不是更长聊天历史，而是可版本化的状态、证据、失败轨迹和 regression artifact。

## 最值得深入研究或尝试复现的方向

1. **在线标定健康度模块。** 在现有 WMR / 机器人底盘中先只把 steering offset、wheel scale、LiDAR planar extrinsic 作为 shadow state 估计，不自动写回 TF；同时记录 excitation、covariance 和 CTE。确认不同载荷、轮胎磨损、拆装以后确实能稳定发现偏差，再逐步开放自动更新。

2. **把任务接触变成定位因子。** 对充电桩、门把手、阀门、按钮或反光定位标志，建立 `object_id + contact_pose + confidence` 因子；比较纯 LIO、LIO+视觉回环、LIO+物理接触锚点在长走廊/重复结构里的长期漂移与 revisit error。

3. **Jetson 上复现 DFT* / structured forward sampling。** 不必先追论文全部理论，先把现有无人机可执行 motion primitive 变成有限 command library，并比较随机 MPPI、普通 kinodynamic tree、dispersive forward tree 的 P95/P99 规划时间、碰撞率与轨迹成本。

4. **AI Coding 的“状态化规划 + 证据化回归”组合。** Scout/Planner 每轮必须读取当前 repo SHA、失败测试和 diff，再生成下一 subplan；Validator 则根据历史 fault-probe matrix 优先跑小型高价值 suite，nightly 再跑完整回归。这样长任务不会一直按过期计划执行，PR 阶段也不会被全量测试成本拖死。

## 参考资料

1. [Online Joint Calibration of Steering Offset and Planar LiDAR Extrinsics for Wheeled Mobile Robots](https://arxiv.org/abs/2608.26789)
2. [Contact-Aided Factor-Graph Localization for Underwater Sampling](https://arxiv.org/abs/2608.26932)
3. [Dispersive Forward Tree Search for Optimal Control](https://arxiv.org/abs/2608.26314) · [代码](https://github.com/croshank/DFTSearch)
4. [SOLO: Stable Omni-terrain Long-Horizon Perceptive Humanoid Locomotion](https://arxiv.org/abs/2608.26583) · [项目页](https://sunpihai-up.github.io/solo/)
5. [Rapid On-Robot Learning for Dynamic Manipulation Skills: Robot Juggling](https://arxiv.org/abs/2608.26800)
6. [RTNav: Towards Real-Time Zero-Shot Object Navigation](https://arxiv.org/abs/2608.26496) · [项目页](https://generalroboticslab.com/RTNav) · [代码](https://github.com/generalroboticslab/RTNav) · [实机代码](https://github.com/generalroboticslab/RTNav-RealWorld)
7. [DeepRepro](https://arxiv.org/abs/2608.26557) · [代码](https://github.com/ruyisy/DeepRepro)
8. [FaultLens](https://arxiv.org/abs/2608.26746)
9. [Unified Temporal and Spatial Calibration for Multi-Sensor Systems](https://doi.org/10.1109/IROS.2013.6696514) · [Kalibr](https://github.com/ethz-asl/kalibr)
10. [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)
