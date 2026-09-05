---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-05"
date: 2026-09-05 09:00:00 +0800
description: "TRaIL-Odom 用方向级雷达 Doppler 补偿 LiDAR 退化，CP-Cert 为鲁棒位姿配准增加快速最优性认证；本期同时关注软体机械臂 Koopman-MPC、VLA 世界模型后训练、Real-to-Sim 评测、Coding Agent 需求漂移，以及 Claude 驱动的大规模 Lean 形式化。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-05

## 摘要

截至 2026-09-05 09:00（Asia/Shanghai），arXiv Robotics 最新公开列表为 2026-09-04，共 75 条，其中 36 条为 new submissions；Software Engineering 同日共 31 条，其中 14 条为 new submissions。严格最近 24 小时内，高质量、可完整核验且未进入历史覆盖索引的机器人 / SLAM / 控制主动态不足 5 条，因此本期按任务规范扩展到最近 7 天。大部分论文的 v1 提交于 9 月 2–3 日 UTC，均明确标记为“时间回补”；Anthropic 的 Fermat 最后定理形式化则是 9 月 4 日官方研究更新。

今天 SLAM / 状态估计方向最值得优先看的工作是 **TRaIL-Odom**。它没有把 mmWave radar 当成“全天候备胎”简单固定加权，而是先从 LiDAR 几何中识别弱平移方向，再让每个 radar Doppler 约束按照自己与弱子空间的对齐程度获得不同权重；扫描级别还会根据 LiDAR 几何各向异性整体提高或降低 radar 增益。在三段几何退化序列的消融里，两层自适应机制相对固定 radar 权重将 RMSE ATE 与 RTE 分别降低 86.0% 和 78.5%。官方 ROS 2 代码和数据已经公开，数据平台包含 ANYmal、Livox Mid-360、Honeywell HG4930 IMU 与 D3 Embedded mmWave radar。

与之互补的是 **CP-Cert**。它处理的不是“怎样再做一次局部配准”，而是“局部求解器已经给出一个 pose 后，能否快速证明这个解就是全局最优”。传统 SDP certifier 在某些机器人配准问题上会因 relaxation degeneracy 变得很慢；CP-Cert 从候选解出发寻找 central path 上更容易获得证书的区域，并利用稀疏线性代数、并行与间接求解，将部分模拟问题的认证速度提升到相对直接 SDP solver 最多三个数量级。它对 loop-closure / global registration 的启发很直接：召回、求解、认证可以是三个独立层。

控制侧，**Koopman 多段软体机械臂 MPC** 把“只控制末端点”升级成“控制整条连续体形状”。作者同时设计 global 与 local observables，避免段间耦合、重力载荷和惯性效应全部被一个全局 shape error 吞掉；数值实验扩展到 10 段，实体 3 段和 5 段软臂在末端最高约 0.6 m/s 下实现实时形状跟踪，并在不重新训练的情况下承受 400 g 末端载荷和 7 N 横向扰动。这类 Koopman + MPC 结构很适合“解析模型太复杂、纯黑盒控制又缺乏结构”的柔性机器人。

安全运行时方面，**Predictive Zonotope Reduction** 关注一个很容易被忽略的细节：不确定性 monitor 持续融合传感器后，zonotope 阶数会不断增长，必须做 over-approximation reduction；但固定 reduction 方法在不同状态下会产生不同程度的保守性。作者把“下一步选哪一种 reducer”本身变成一个 beam-search MPC，再把策略蒸馏成小网络，在 Raspberry Pi 5 上运行，减少了因过度保守引起的 false positive。它说明 runtime verification 的性能瓶颈不只在逻辑规则，也在不确定性集合怎样被压缩。

机器人策略评测方面，**R2S-Eval** 很适合现场交付团队研究。它并不要求构建一个完美照片级数字孪生，只校准真正影响策略行为的 robot geometry、kinematics、joint limits、control interface、task objects、camera viewpoints 与 initialization，然后在 Isaac Sim 中重放闭环策略。再由 VLM 对成对 rollout 视频比较 task progress、continuity、control quality 与 completion，并用 Bradley–Terry 模型聚合成 policy ranking。七个 Real-to-Sim 校准任务中，八个 VLM judge 的排序与真机 success ordering 的平均 Spearman 相关达到 0.957，和人工 pairwise preference 的一致率达到 91.9%。

VLA 后训练方面，**WISE** 的核心不是“世界模型越多 rollout 越好”，而是只在真正值得想象的交互阶段调用 world model。它选择 interaction-relevant state，限制 multi-view imagination horizon，用 progress / completion 信号比较候选未来，再把相对结果用于修正真实交互上下文中的动作。π0 与 π0.5 上都获得稳定提升，同时相对全程 imagination 将 GPU computation time 降低约 80%。这很符合实际部署：世界模型最适合成为昂贵、按需调用的评估器，而不是每个控制周期都生成未来视频。

AI Coding 侧，本期有两条特别值得工程团队记住。第一，**Requirements After the First Edit** 对 3,553 个真实 SWE-chat session 做了需求后到达分析：用户在 Agent 已经开始改代码以后才补充的新需求，其后续造成的既有 Agent 代码删除 / 替换量大约是匹配的非需求编辑的两倍，而且这个负担没有随着 session 进行明显下降。换句话说，Coding Agent 的“需求”不是一次性 Prompt，而是一个会持续演化、必须版本化和显式触发 replan 的状态。

第二，Anthropic 9 月 4 日公布了 **Fermat 最后定理的首个完整 computer-checked Lean 形式化**。Claude 在约 11 天内以多 Agent 方式生成约 1,300 万行 Lean，最终证明使用约 29,500 个中间定理；整个过程最初也因 Agent 丢失项目状态和协作失效而失败，转折点是引入 Prove2Me 的 theorem DAG、声明/证明分离、搜索复用和 Claude Code 多 Agent harness。最终证明不仅由 Lean kernel 编译检查，还经过 comparator 与独立 Rust Lean kernel nanoda 再验证。对 AI Coding 的真正启发不是数学本身，而是：超长任务需要显式依赖图、可机器验证的最终产物和独立 verifier，而不是无限延长聊天上下文。

## 1. TRaIL-Odom：让 Radar 专门补 LiDAR 当前真正缺信息的方向

**时间回补：arXiv v1 提交于 2026-09-03 09:00 UTC；论文已于 2026-08-23 被 IEEE RA-L 接收。** [论文](https://arxiv.org/abs/2609.03561) · [官方代码与数据](https://github.com/ChiyunNoh/TRaIL-Odom)

### 为什么重要

Radar-LiDAR fusion 最常见的做法，是给 Doppler residual 一个固定权重，然后和 LiDAR / IMU 一起优化。但“雷达是否有用”并不是一帧一个布尔值：长走廊中 LiDAR 可能只在走廊轴向弱可观，而横向、垂向仍然非常稳定；某一个 radar point 的 radial velocity 对这个弱轴贡献可能很大，也可能几乎没有。

TRaIL-Odom 把这个问题拆成两个尺度：

```text
LiDAR geometry
      ↓
weak translational subspace
      ↓
per-radar-point Doppler alignment
      ↓
point-wise reweighting

LiDAR scan anisotropy
      ↓
scan-wise radar gain scheduling
```

第一层回答“哪一个 Doppler 测量真正补得到弱方向”，第二层回答“这一整帧到底需要多依赖 radar”。

### 算法模块

系统本体是 tightly coupled continuous-time Radar-IMU-LiDAR odometry，用 B-spline 表示连续运动，直接融合异步 IMU、LiDAR 与 radar 约束。

几何退化检测从当前 LiDAR scan 的方向性信息中提取弱平移子空间。每个 radar Doppler measurement 具有自己的 line-of-sight 方向，因此可以计算它对弱子空间的投影；越能观测弱方向的 radar point，权重越高。随后 scan-wise gain 又根据 LiDAR geometric anisotropy 做整体调度：LiDAR 自身约束充分时降低 radar 影响，几何严重退化时提升 radar 贡献。

这比“雷达永远权重大”更稳，因为 radar 多径、静态 clutter 与 Doppler outlier 同样可能污染状态估计。

### 传感器与几何假设

官方公开数据平台为 ANYmal + Boxi，传感器包含：

- Livox Mid-360；
- Honeywell HG4930 IMU；
- D3 Embedded RS-1843AOPU mmWave radar；
- Leica MS60 + 360° prism ground truth。

六条公开序列覆盖 BikeTunnel、Park 与 Airfield 三类几何场景。

Radar Doppler 主要提供 radial velocity，因此单个点天然只约束一个方向；真正有效的是多 radar return 与运动 / 几何共同形成的方向覆盖。另一方面，若环境存在大量运动目标或严重多径，Doppler 本身也需要 outlier rejection，不能因为 LiDAR 退化就无条件放大所有 radar measurement。

### 实时性与结果

作者在 13 条评测序列上报告整体 SOTA；在三条几何退化消融序列中，相比固定 radar 权重：

- RMSE ATE 降低 **86.0%**；
- RTE 降低 **78.5%**。

公开仓库提供 Ubuntu 22.04、ROS 2 Humble、C++17、Ceres 2.2、PCL 1.13 和 Zenoh RMW 的完整启动配置。

### 鲁棒性、可复现性与风险

可复现性高：代码、数据、Docker / launch / config 都已经公开，MIT License。

真正值得工程关注的风险不是“Radar 能不能替代 LiDAR”，而是方向级 observability estimate 是否稳定。低线数 LiDAR 的弱方向如果因为局部 normal / covariance 噪声频繁跳变，就会让 radar gain 抖动。生产系统应对 weak-axis 加时间滤波 / hysteresis，并同时记录 Doppler innovation。

### 适合谁关注

长走廊、隧道、矿井、机场停机坪、工业厂房，以及 16 线 / 非重复扫描 LiDAR 容易出现几何退化的多传感器定位系统。

### 工程落地启发

最值得直接迁移到现有 LIO-SAM / ESKF 的不是整套 continuous-time estimator，而是接口：

```text
LiDAR frontend
   ↓
weak_axis / information_matrix
   ↓
Radar / Wheel / RTK / Reflector
按“能否补弱方向”动态加权
```

轮速、RTK、第二只 LiDAR 和反光标志都可以使用同样逻辑：不是“这个传感器整体好不好”，而是“它现在能否补当前缺失的状态方向”。

## 2. CP-Cert：全局配准不只要给出解，还要快速回答“这个解能不能被证明”

**时间回补：arXiv v1 提交于 2026-09-02 23:39 UTC。** [论文](https://arxiv.org/abs/2609.03222)

### 为什么重要

回环、跨 session 地图对齐、object registration 常见流程是：descriptor 召回候选，TEASER++ / RANSAC / GNC / local solver 求一个 SE(3) pose，然后根据 residual 或 inlier 数决定是否接受。

问题是 residual 小不等于全局正确。重复结构里，一个错误 basin 也可能拥有漂亮的局部 residual。

Certifiable optimization 希望进一步回答：

> 当前候选是不是原非凸问题的全局最优解？

### 算法模块

很多高性能 certifier 使用“local solve → certificate”的路线，借助 SDP relaxation 的 dual structure 做快速认证。但某些 pose-registration relaxation 本身存在 degeneracy，使快速证书无法直接构造，最终只能退回昂贵的直接 SDP solve。

CP-Cert 从局部 candidate 出发，不直接死磕退化点，而是沿 feasible set 寻找一个邻近的 **central path** 区域，在那里有效 certificate 更容易构造；随后利用：

- indirect linear algebra；
- problem sparsity；
- parallelism；

降低证书计算成本。

论文同时将这一思路用于 matrix-weighted pose registration，并提出 point-cloud data association 的新 SDP relaxation。

### 传感器与几何假设

它不绑定特定 LiDAR，而依赖你已经拥有 pose-registration / correspondence problem。

“可认证”也不是“输入 correspondence 全部可以随便错”。若前端根本没有形成足够真实几何关系，优化问题自己的最优解可能就不是你真正想要的物理对应。

### 实时性与结果

模拟实验中，CP-Cert 在部分问题上相对 state-of-the-art direct SDP solver 达到**最多三个数量级**的速度提升，并最终组成了一个 certifiable outlier-robust pose-estimation pipeline，在真实数据上测试。

公开材料目前没有稳定官方代码入口，因此工程复现性暂评中等偏低。

### 鲁棒性、可复现性与风险

认证只证明“你写下的优化问题”的性质，不证明模型本身正确。错误的 noise bound、对应关系定义、动态物体或对称环境，都可能使一个 mathematically certified optimum 仍不是想要的机器人位姿。

因此认证层应该是**几何验收的最后一层**，不是感知与 data association 的替代品。

### 适合谁关注

回环验证、跨 session global registration、跨传感器地图对齐、高误匹配率点云配准，以及需要严格限制误闭环的工业定位系统。

### 工程落地启发

可以把回环链正式拆成：

```text
Place Retrieval
      ↓
Robust Global Registration
      ↓
Local GICP / VGICP Refinement
      ↓
Optimality / Consistency Certificate
      ↓
通过后才加入 Pose Graph
```

相比仅用 fitness threshold，这更容易将“候选召回错误”“局部优化失败”“全局几何不可信”三类故障分开统计。

## 3. Koopman 多段软臂 MPC：真正要控制的是整条连续体形状，不只是末端点

**时间回补：arXiv v1 提交于 2026-09-02 21:36 UTC；T-RO 投稿。** [论文](https://arxiv.org/abs/2609.03175)

### 为什么重要

连续体 / 软体机械臂在狭窄空间内真正危险的往往不是末端偏差，而是中间某一段身体鼓出去撞到环境。传统 tip tracking 即使末端完全正确，也可能得到一个不可接受的整机 shape。

另一方面，直接从材料力学建立高维 nonlinear continuum model 又很难实时放进 MPC。

### 算法模块

作者使用 Koopman operator 将非线性动态提升到更容易预测的 observable space，并刻意同时设计两类观测：

```text
Global observables
→ 整体 shape 相对世界目标

Local observables
→ 每一段相对相邻段的局部形变 / 耦合
```

只用 global shape error 时，多段软臂的 segment coupling、gravity loading 和 inertia 很容易被平均掉；加入 local observable 后，MPC 能更直接感知每段形状是否局部失真。

### 动力学与传感器假设

Koopman 模型依赖训练 / system identification 数据覆盖足够的形变和动态范围。对软体机器人而言，材料老化、温度、负载、压力系统滞后都可能改变真实 dynamics。

因此“无需 retraining 承受 400 g payload / 7 N disturbance”是很有价值的鲁棒性证据，但不能外推到任意软材料与更大接触力。

### 实时性与实体结果

数值实验展示到 **10 个 independently actuated segments**。

实体实验：

- 3 段、5 段软体机械臂；
- tip speed 最高约 **0.6 m/s**；
- 不重训承受末端 **400 g** payload；
- 可从 **7 N** 横向扰动恢复；
- 展示 confined-space inspection 场景。

论文明确以 real-time shape control 为目标，但公开 abstract 没有给出一个适合跨硬件比较的统一 solver ms，本期不人为补 FPS。

### 鲁棒性、可复现性与风险

当前未见稳定官方代码，复现需要自己完成 shape sensing、Koopman identification 和 MPC integration。

最关键的安全风险是 learned lifted dynamics 在强接触 / 材料状态变化下 OOD。真正部署时应保留压力、驱动器和几何的硬限制。

### 适合谁关注

管道巡检、狭窄空间探测、柔性机械臂、软体抓取与 continuum robot 控制。

### 工程落地启发

这套思路也能迁移到刚柔耦合机构：不要只用一个 global end-effector error 控制整机，可以把关键结构中间状态做成 local observable，再由 MPC 同时约束“任务结果”和“机体形状”。

## 4. Predictive Zonotope Reduction：安全 Monitor 的不确定性表示也需要在线调度

**时间回补：arXiv v1 提交于 2026-09-03 11:36 UTC。** [论文](https://arxiv.org/abs/2609.03699)

### 为什么重要

Runtime monitor 若要在传感器存在误差时判断安全规格，不能只使用一个点估计，而应维护真实状态可能所在的集合。

Zonotope 很适合表示这类集合，但连续加入新的测量和不确定性以后，generator 数量不断增加，计算会失控，因此必须定期做 reduction。Reduction 又是 over-approximation：压得越狠，集合越大，monitor 越容易误报 unsafe。

### 算法模块

传统系统通常固定使用一种 reduction 方法。PZR 的观察是：

> 不同 state / geometry 下，最合适的 reducer 不一样。

于是作者把 reducer selection 变成一个小型最优控制问题，用 beam-search MPC 预测未来几步不同 reduction 决策对集合精度与计算成本的影响，再选择当前 action。

为了在资源受限端侧运行，又把这个 MPC policy distill 成一个小 neural policy。

### 传感器与系统假设

方法要求初始 uncertainty model 是 sound 的；论文在 MuJoCo 5-DoF arm 中按照 ISO 5725 建模 sensor uncertainty。

如果真实噪声存在未建模 bias、heavy-tail 或时间相关性，再精确的 zonotope reduction 也只能正确处理错误的 uncertainty envelope。

### 实时性与结果

实现集成到 RLola runtime monitoring framework，并在 **Raspberry Pi 5** 上测试。动态 reduction 相比静态 reducer 明显降低 false-positive rate；policy distillation 比在线 beam-search MPC 快得多，同时保留主要精度收益。

### 鲁棒性、可复现性与风险

当前验证仍以模拟机械臂为主。它的核心价值不是某个具体 reducer，而是把“verification representation quality”也看作运行时资源调度问题。

### 适合谁关注

安全机器人、CBF / reachability 外的独立 runtime verification、资源受限边缘控制器，以及需要对不确定性做 sound over-approximation 的系统。

### 工程落地启发

很多机器人 safety monitor 目前还是：

```text
state estimate
→ 加固定 margin
→ 判断
```

更成熟的做法应让 uncertainty representation 本身具备 health / precision / compute budget 指标，避免安全层因为过度保守而频繁误停，最后被现场工程师“临时关掉”。

## 5. R2S-Eval：Real-to-Sim 不只用于训练，也可以先用于减少真机评测成本

**时间回补：arXiv v1 提交于 2026-09-03 02:08 UTC。** [论文](https://arxiv.org/abs/2609.03276) · [项目页](https://r2s-eval.github.io/)

### 为什么重要

机器人策略评测的真实成本很高：

- 每轮都要人工 reset；
- 真机磨损；
- 初始状态难完全一致；
- 同一策略重复评测会产生不同 ranking；
- binary success 看不出“虽然都成功，但哪个动作更平滑、更稳”。

R2S-Eval 的目标不是替代全部真机实验，而是把大部分重复 comparison 移到一个**行为相关的校准仿真**里。

### Real-to-Sim Calibration

系统并不追求 photo-realistic digital twin，而是优先校准真正改变 policy behavior 的因素：

```text
robot geometry
kinematics
joint limits
control interface
task objects
camera viewpoints
initialization distribution
```

项目页展示七个 tabletop task，将真实 teleoperation 轨迹以 joint-angle action replay 的方式放到 NVIDIA Isaac Sim 校准环境中，比较真实和仿真行为。

### VLM Preference

对候选策略的成对 rollout，VLM 先描述：

- task progress；
- action continuity；
- control quality；
- final completion；

再产生 pairwise preference，最后通过 Bradley–Terry model 聚合成 policy score / ranking。

### 实时性与结果

评测覆盖 40 个 LIBERO task、七个校准真实任务、六种候选 VLA 和八个 VLM judge。

LIBERO：

- 平均 Spearman(policy ranking vs success ordering)：**0.823**；
- preference score 与 success rate Pearson：**0.924**；
- 与人工 pairwise annotation 一致率：**82.9%**。

Real-to-Sim 七任务：

- 与硬件 success ordering 的平均 Spearman：**0.957**；
- Pearson：**0.978**；
- 与人工 pairwise annotation 一致率：**91.9%**。

### 鲁棒性、可复现性与风险

真正的风险是“模拟器把错误排序稳定地重复很多次”。因此 R2S-Eval 自己也强调 validation protocol，而不是看到仿真排名就直接发布结论。

尤其接触丰富任务里，视觉 rollout 无法完整表达真实 force / friction / jamming，VLM 的视频 preference 也不应替代力觉和硬件安全指标。

### 适合谁关注

批量机器人交付、VLA 版本回归、Real-to-Sim / Sim-to-Real、需要每天比较多个 checkpoint 的机器人团队。

### 工程落地启发

可以将交付评测预算分层：

```text
大量每日回归
→ calibrated sim

少量关键版本
→ 真机 paired validation

安全 / 接触 / 极限边界
→ 必须真机或硬件在环
```

这样 Digital Twin 的商业价值不只在“训练策略”，还在“降低验证与回归成本”。

## 6. WISE：World Model 不应每一步都想象，应该只在真正有决策价值的时刻想象

**时间回补：arXiv v1 提交于 2026-09-03 11:17 UTC。** [论文](https://arxiv.org/abs/2609.03681)

### 为什么重要

用 world model 给 VLA 后训练很诱人：不用真机探索，生成大量未来，再从中选择更好的动作。

但 world model 最大的问题也是 rollout：越滚越远，预测误差越大；每个时间点都生成 multi-view future 又非常贵。

WISE 的关键不是做更大的 world model，而是建立 **Imagination Scheduler**。

### 算法模块

```text
real interaction state
        ↓
interaction relevance
        ↓
值得想象？
  ├─ No → 继续真实策略
  └─ Yes
       ↓
 bounded multi-view rollout
       ↓
 progress / completion scoring
       ↓
 relative candidate outcome
       ↓
 refine VLA action
```

它只在 manipulation 中 interaction-relevant state 调用 imagination，并严格限制 rollout horizon，不让世界模型在自己越来越不可信的远未来制造监督。

### 传感器与模型假设

世界模型需要在当前 observation/action 分布附近足够准确。OOD 对象、接触和遮挡仍会让 imagined future 失真。

因此“调度 imagination”本质上也是一种模型可信区间管理。

### 实时性与结果

论文在 π0 和 π0.5 上验证，多个 manipulation task 都有稳定提升；相比 full imagination，GPU computation time 减少约 **80%**，并在真实机器人 distribution shift 条件下展示鲁棒性与泛化收益。

### 鲁棒性、可复现性与风险

当前 arXiv 页面未给出稳定代码入口，可复现性暂评中等偏低。

最主要风险是 scheduler 与 world model 一起错：恰好在最关键的接触阶段误判“不需要想象”，或者在 world model 最不可靠的 OOD 状态持续生成未来。

### 适合谁关注

π0 / π0.5 后训练、World Action Model、真实机器人策略优化，以及希望降低 world-model rollout 成本的团队。

### 工程落地启发

世界模型最合理的产品接口可能不是：

```text
每帧生成未来
```

而是：

```text
Policy / Monitor 发现高风险或高价值决策点
          ↓
World Model On-Demand Evaluation
          ↓
返回候选排序 / risk
```

这和慢速 VLM 高层规划一样，属于稀疏调用的昂贵认知模块。

## 7. Requirements After the First Edit：Coding Agent 的需求不是 Prompt，而是会持续变化的版本化状态

**时间回补：arXiv v1 提交于 2026-09-02 18:02 UTC。** [论文](https://arxiv.org/abs/2609.03028)

### 突破性工程价值

很多 Coding Agent benchmark 假设 issue 一开始就已经写完整，Agent 只需要理解并实现。

真实开发不是这样。用户经常看到第一版界面 / diff 后才意识到：

- 原来还需要兼容旧格式；
- 这里不能改 API；
- 这个按钮应该放另一个页面；
- 还要支持一个此前没想到的边界条件。

研究对 **3,553 个 eligible SWE-chat sessions** 进行分析，专门标注“Agent 已经开始改代码以后，新需求才出现”的情况，并在可 replay repository state 上估算这些 late requirement 对此前 Agent-authored lines 的 invalidation。

### 结果

新需求到达后的代码 deletion / replacement 约为匹配非需求 edit 的 **2 倍**。这一 rework burden 在 session 后期没有明显下降，也没有观察到随着 operation type 变化而消失。

控制实验还显示：仅提前提醒“后面可能还有需求”并不能明显减少最终 overwriting；真正延迟披露需求，只是把实现工作推迟到 reveal 之后。

这说明问题不是让 Agent“更谨慎一点”就能解决，而是任务状态真的发生了变化。

### 是否适合真实研发流程

非常适合任何 Codex / Claude Code / OpenHands 长任务。

需求应该从聊天历史里抽出来，成为有版本的 artifact：

```text
Requirement v1
   ↓
Implementation
   ↓
Requirement v2 arrives
   ↓
impact analysis
   ↓
replan affected modules
   ↓
regression
```

### 权限、安全与可验证性风险

如果 Agent 每次收到一句用户补充就全仓重写，会放大 rework；如果又过度坚持旧计划，则会实现已经过期的需求。

因此新需求到达后，需要独立的 impact analysis：哪些文件 / 接口 / 测试已被 invalidated，哪些已有 artifact 仍可复用。

### 工程落地启发

长期 Agent 不应该只有 `task.md`，而应维护：

```text
requirements_version
accepted_constraints
superseded_constraints
affected_symbols
implementation_revision
validation_revision
```

每一次 requirement change 都触发一个显式 replan gate，而不是让模型在上下文里悄悄“改变主意”。

## 8. Claude 形式化 Fermat 最后定理：长时 AI Coding 的真正突破来自 DAG + Compiler + Independent Verifier

**2026-09-04 官方研究更新。** [Anthropic 研究说明](https://www.anthropic.com/research/formalizing-fermats-last-theorem) · [完整 Lean 证明](https://github.com/anthropics/fermats-last-theorem)

### 突破性工程价值

Anthropic 公布首个完整、computer-checked 的 Fermat's Last Theorem Lean 形式化。Claude 在约 **11 天**内大规模协作完成：

- 约 **1,300 万行 Lean**；
- 总计约 **30,300** 个 machine-verifiable theorem proof；
- 最终证明使用约 **29,500** 个中间定理；
- 多个 Claude agent 并行工作；
- 总输出 token 约 **60 亿**。

这不是普通代码生成 benchmark，而是一项极端长时、巨型依赖图、必须最终由编译器 / kernel 全量验证的工程任务。

### 最有价值的负结果

Anthropic 明确记录：最初的多 Agent 尝试并不顺利。Agent 很快开始丢失项目全局状态，协作效率下降。

真正的转折点是切换到 **Prove2Me**：

```text
Theorem DAG
   ↓
Agent 选择未证明节点
   ↓
独立文件保存 statement / proof
   ↓
Lean 编译
   ↓
可复用 theorem search
   ↓
更高层 theorem 解锁
```

DAG 缓解 memory degradation，让不同 Agent 可以无冲突并行；statement 与 proof 分离又减少重复编译成本。

### 可验证性为什么关键

最终成果不是“Claude 说证明完成了”。仓库提供多层独立检查：

1. Lean 4.33.1 从头 `lake build`，所有 declaration 由 kernel 检查；
2. `FinalCheck.lean` 明确检查最终 theorem 只依赖 Lean 的三项标准 axioms，并禁止 `sorry` 等绕过；
3. comparator 将证明 statement 与 Mathlib 中的 FLT statement 做一致性检查；
4. 独立 Rust Lean kernel **nanoda** 再检查导出的 environment，验证 1,052,234 个 declaration 无错误。

### 是否适合真实研发流程

数学形式化比普通软件更容易拥有“绝对 verifier”，但系统思想完全可以迁移：

```text
大任务
 ↓
显式依赖图
 ↓
多 Agent 分片实现
 ↓
机器可检查 Artifact
 ↓
独立 Verifier
 ↓
只有通过才解锁上层节点
```

这比让一个 Manager 在自然语言里不断汇总“大家做到哪了”可靠得多。

### 权限、安全与风险

即使最终 proof 可验证，Agent 仍可能浪费极其巨大的计算预算。60 亿输出 token 提醒我们：可验证不等于成本可控。

生产 Coding Agent 还需要 budget、branch / workspace isolation、tool permission 与 artifact provenance。

### 工程落地启发

对复杂软件项目，可以把 requirement / module / test / migration step 组织成 DAG，每个节点拥有：

```text
inputs
dependencies
artifact
validator
status
owner_agent
revision
```

Verifier 不通过时，节点不能被上层任务当作“完成”。这可能比继续扩展单 Agent 上下文窗口更接近真正可扩展的长期 AI Coding。

## 经典论文回顾

### Chen–Medioni Point-to-Plane Registration：为什么点到平面的误差在三十多年后仍是 LiDAR 配准的核心残差

**历史位置：** Yang Chen 与 Gérard Medioni 在 ICRA 1991 提出 `Object Modeling by Registration of Multiple Range Images`，扩展版发表于 1992 年 *Image and Vision Computing*。它和 Besl–McKay ICP 同时代，却走出了一条影响极深的不同路线：不要求严格 point-to-point correspondence，而是让 source point 去最小化到 target local tangent plane 的距离。[ICRA 论文](https://graphics.stanford.edu/~smr/ICP/comparison/chen-medioni-align-rob91.pdf) · [1992 期刊 DOI](https://doi.org/10.1016/0262-8856(92)90066-C)

### 核心问题

如果两个 range scan 已经大致对齐，希望继续精配准，最直接的 point-to-point objective 是：

```text
min Σ || Rp_i + t - q_i ||²
```

但在一片平面上，source point 真正应该匹配 target 平面的哪个离散 sample 并不重要。强行追一个最近点会引入与点云采样密度有关的切向误差。

Chen–Medioni 改成：

```text
min Σ [ n_iᵀ (Rp_i + t - q_i) ]²
```

只惩罚沿 target normal 的误差；在切平面内滑动不会被无意义地强罚。

### 关键数学思想

小位姿增量下，旋转可以局部线性化，point-to-plane residual 对 6DoF twist 形成近似线性 least-squares system。

这也是今天大量 LiDAR odometry / scan-to-map 方法的基础：

```text
point
   ↓
找到 local plane / normal
   ↓
构造 signed distance residual
   ↓
Gauss-Newton / LM
   ↓
迭代更新 Pose
```

LOAM 的 planar feature、surfel SLAM、VGICP 中的平面统计，都可以看到这种几何思想的延续。

### 传感器与几何假设

Point-to-plane 需要可靠 normal。Normal 来源若只有极少点、边缘点、动态物体或低线数 LiDAR 的稀疏邻域，平面残差可能比 point-to-point 更糟。

它同样是**局部配准**：初值太差时，normal 再好也会匹配到错误表面。

### 当年为什么重要

它将 registration 从“离散点是否一一对应”转向“局部表面几何是否一致”。对密度不同、采样相位不同的 range image，这更符合真实几何。

### 今天仍然在使用的思想

1. **Residual 应与局部表面结构一致。** 平面上用法向误差比三个坐标等权更合理。
2. **Correspondence 与 geometry 是两件事。** 最近邻只是找到 local surface 的一种方式。
3. **Normal / covariance 应成为地图属性。** 如果每次优化都需要，最好在 voxel / surfel map 中维护。
4. **Hessian 的弱方向直接来自场景几何。** 长走廊轴向缺少 normal coverage 时，point-to-plane 自己不会创造信息。

### 已被后续替代或扩展的部分

现代系统增加了：

- robust kernel / trimmed correspondence；
- GICP / VGICP covariance；
- voxel / surfel map；
- continuous-time deskew；
- IMU propagation；
- degeneracy-aware weighting；
- GPU parallelism。

这些不是推翻 point-to-plane，而是解决它的 correspondence、normal quality、动态、初值和可观测性边界。

### 公开代码、数据与可复现性

原始论文属于早期 range-image 时代，没有现代官方仓库。但 point-to-plane 已经成为 PCL、Open3D 等库的标准配准基线，复现成本极低。

### 对当前低线数 LiDAR 工程的重新解读

16 线 LiDAR 最常见的问题不是“point-to-plane 太老”，而是：

```text
局部点太少
  ↓
normal 不稳定
  ↓
平面 residual 变成噪声
```

因此现代低线数系统更应该：

```text
短时 Deskewed Submap
        ↓
Voxel / Surfel
normal + covariance + support count
        ↓
根据 geometry quality
自适应选择 point-to-plane / point-to-point
        ↓
输出 weak direction
        ↓
Radar / IMU / Wheel / RTK 补约束
```

把今天 TRaIL-Odom 的方向级 Doppler reweighting 放在这条经典几何链后面，系统逻辑非常自然：**Point-to-plane 告诉你 LiDAR 哪个方向有信息，其他传感器只补真正缺的方向。**

## 今日结论

今天最清晰的 SLAM 信号是：**多传感器融合正在从“传感器级权重”走向“状态方向级权重”。** TRaIL-Odom 不再问“Radar 应不应该信”，而是问“这个 Doppler 能不能补 LiDAR 当前的 weak subspace”。这与低线数 LiDAR 的真实退化问题高度吻合。

CP-Cert 则继续把定位系统的职责拆细：召回候选、优化 pose、判断 residual、证明最优性，不应该由同一个分数承担。对于误闭环代价很高的长期地图，独立 certifier 是很值得关注的一层。

控制侧，Koopman 软臂 MPC 与 PZR 都体现了一个共同趋势：模型学习并不一定替代控制或安全结构。前者用可学习线性提升模型服务 MPC，后者把昂贵在线决策蒸馏为轻量 policy，但最终安全集合仍然有明确数学语义。

机器人基础模型开始面对另一个现实：**世界模型和 VLM 都很贵，也都不是任何时间都值得调用。** WISE 通过 scheduling 将 imagination GPU 时间降低约 80%；R2S-Eval 则把昂贵真机回归迁移到经过行为校准的 simulator，再只用关键硬件结果验证 ranking。它们本质上都在做“昂贵认知 / 实验资源调度”。

AI Coding 侧的两项结果把长期 Agent 的工程边界说得非常清楚。真实需求会在实现过程中继续变化，因此计划必须可版本化、可失效；而真正超长任务一旦扩展到上千万行形式化代码，单纯聊天上下文和自然语言 Manager 都会失效，必须依赖 DAG、持久 artifact、编译器和独立 verifier。

## 最值得深入研究或尝试复现的方向

1. **16 线 LiDAR + Radar / Wheel 的方向级融合 A/B。** 保留现有 LIO，只输出 LiDAR translation information matrix / weak axis，再让 radar Doppler 或轮速按照与 weak axis 的投影动态加权；重点测长走廊轴向 RPE、误差出现前的 health lead-time 与权重抖动。

2. **给回环增加独立 Certificate 层。** 先不改变 Scan Context / descriptor 召回，只在 robust global registration + GICP 后增加更严格的几何一致性 / certifier，专门统计误闭环被哪一层拒绝。

3. **R2S-Eval-lite 交付回归。** 选 3–5 个真实固定任务，只校准机器人几何、相机、控制接口和对象初始分布；日常 checkpoint 在 simulator 批量跑，只有排名变化明显时再做真机复核，测一个月实际节省的人工 reset 时间。

4. **Coding Agent Requirement DAG。** 把“需求版本—实现模块—测试—验证证据”做成显式依赖图；用户新增约束时先做 impact analysis，只 invalidates 真正受影响节点，再让 Agent 重规划。最终合并仍由独立 CI / verifier 决定。

## 参考资料

1. [TRaIL-Odom 论文](https://arxiv.org/abs/2609.03561) · [官方代码与数据](https://github.com/ChiyunNoh/TRaIL-Odom)
2. [Following a Unique Path / CP-Cert](https://arxiv.org/abs/2609.03222)
3. [Koopman 多段软体机械臂 MPC](https://arxiv.org/abs/2609.03175)
4. [Predictive Zonotope Reduction](https://arxiv.org/abs/2609.03699)
5. [R2S-Eval 论文](https://arxiv.org/abs/2609.03276) · [项目页](https://r2s-eval.github.io/)
6. [WISE](https://arxiv.org/abs/2609.03681)
7. [Requirements After the First Edit](https://arxiv.org/abs/2609.03028)
8. [Anthropic：Formalizing Fermat's Last Theorem](https://www.anthropic.com/research/formalizing-fermats-last-theorem) · [完整 Lean 证明](https://github.com/anthropics/fermats-last-theorem)
9. [Chen–Medioni ICRA 1991](https://graphics.stanford.edu/~smr/ICP/comparison/chen-medioni-align-rob91.pdf) · [1992 期刊 DOI](https://doi.org/10.1016/0262-8856(92)90066-C)
10. [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)
