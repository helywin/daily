---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-23"
date: 2026-10-23 09:00:00 +0800
description: "VeriCalib外参校准验证、GGraph空间图、RangeNav轻量激光导航、Flow-MPC、HyperDrone、触觉动作编辑、人形遥操作与VerifierBench。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-23

## 摘要

**检索基准：2026-10-23 09:00（Asia/Shanghai），星期五。** 首先检查最近24小时的新论文和一手正式发布，再扩展到最近7天。arXiv可核查的最新常规公开批次为**2026-10-22**：Robotics（cs.RO）120项，其中69项属于New submissions；Software Engineering（cs.SE）59项，其中34项为New submissions。其余包含交叉收录和版本更新，不能都称为新论文。

本期与GitHub仓库 `helywin/daily` 的 `master` 分支截至10月22日**1,077条**历史覆盖记录，按规范标题、arXiv ID、DOI、项目主页和GitHub仓库联合去重。最终收录**8条未覆盖的主动态、3条一手AI Coding实操、1篇经典论文**。由于八篇论文的v1均提交于10月19—21日UTC，均明确标注为**时间回补**，不混淆arXiv上榜日期与首发时间。

**SLAM与感知**关注VeriCalib对外参拟合误差的进一步质疑：RMSE小不代表所有方向都可观、也不代表物理误差不被不同参数互相吸收。GGraph则使空间拓扑图能够在ROS2在线维护和GPU多环境训练中复用。RangeNav使用仅18.3万参数的360° LiDAR距离图编码器，把语义和BEV监督引入导航表征学习。

**规划控制**中的Flow Matching + MPC把生成式多模态路径提议与受约束执行隔离，HyperDrone则通过GPU原生仿真提高大规模视觉策略训练吞吐，但“每秒数百万渲染帧”不是单架真机的控制带宽。T-WLA用缓存视觉记忆和触觉更新修订尚未执行的动作块；HuMiT压缩G1人形遥操作输入，报告约20毫秒通信至推理延迟、65毫秒中位可见端到端延迟，二者指标口径不同。

**AI Coding**方面VerifierBench警示：如果自动生成的验收器拒绝所有答案，它看起来会非常严格，却完全不能验收合法替代实现。实操选择GitHub 10月22日的Copilot Skill/MCP用量统计、Copilot全局功能默认策略，以及Anthropic Claude Code同日2.1.309的沙盒权限修复。经典回顾TrajOpt（IJRR 2014），与今天学习路径生成和MPC形成工程对照。

数据和性能均为作者在限定条件下的报告，不得直接外推到RK3588、Jetson、Go2或实际交付机器人。[arXiv Robotics](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/new)。

---

## 1. VeriCalib：校准RMSE很小，不代表外参真的可置信

**时间回补：arXiv v1于2026-10-20 UTC提交。**

### 为什么重要

相机—LiDAR外参标定常用标定板采样，再通过视觉重投影/点云匹配残差RMSE决定是否验收。但同一批数据参与拟合和验收，可能掩盖两个层面的补偿：外参与单帧板位姿误差互相吸收；外参内部旋转和平移也可能补偿。得到的SE(3)矩阵整体拟合优良，但某个旋转轴或平移方向仍缺少有效观测。下游多传感器SLAM一旦更换测量距离或方向，可能出现系统性地图错位。

### 算法模块、传感器假设与数学思想

```text
Camera / LiDAR Board Features
             ↓
已知板几何 + 特征噪声模型
             ↓
结构化协方差联合传播
             ↓
Rotation / Translation 可观测性分析
             ↓
逐方向精度、最小可检测偏差
             ↓
同视图及跨视图一致性检验
             ↓
重提特征 / 增加新角度采集 / 接受校准
```

VeriCalib的重点是将**校准质量**提升为正式系统状态，包括逐方向不确定性和采样内部一致性，而不是只返回矩阵。方法仍需要正确相机内参、LiDAR距离模型、板几何、特征关联和时间同步。若板尺寸制造误差或相机畸变建模不正确，协方差也可能低估真实误差。

### 实时性、结果、鲁棒性与复现

这是标定和验收方法，不是实时6DoF里程计。论文摘要不提供统一SLAM FPS或可跨数据迁移的标定误差降低倍数，不能补造。可分别采集“只在正前方同距离”和“跨距离、俯仰、多方向”的板面样本，比较独立验证集重投影残差、旋转轴协方差、平移方向不确定性以及点云上色后误差。当前未确认完整官方代码，不能误把同名工具当论文作者实现。

### 适合谁关注与工程落地启发

适合多雷达、多相机、手工重复装调的边缘机器人。建议把`calibration_revision`、`covariance_directional`和`independent_validation_residual`写入传感器诊断接口；质量不合格的外参不应因为总体RMSE漂亮而自动上线。

来源：[VeriCalib原论文](https://arxiv.org/abs/2610.28791)。

---

## 2. GGraph：同一套空间图支撑ROS2部署和GPU并行机器人训练

**时间回补：arXiv v1于2026-10-20 UTC提交。**

### 为什么重要

机器人的稀疏空间图同时服务于拓扑探索、空间记忆、回环以及路径规划。单台机器人通常可以在CPU维护节点和边，但当强化学习一次运行数百个模拟环境时，反复增删节点、关联局部占据和刷新拓扑就成了训练瓶颈。GGraph提出把GPU批量图维护与真实机器人在线图维护贯通，不必用两套语义不同的状态表示。

### 算法模块与前提

```text
LiDAR / Depth / Odometry / Semantic Features
                     ↓
             Sparse Spatial Graph
          Nodes / Edges / Attributes
                     ↓
 ROS2实时节点边更新  ←→  GPU批量环境构图
                     ↓
    Exploration / Graph Policy / Routing
                     ↓
  Loop-Closure & Graph Revision Tracking
```

前提是各节点真实坐标、时间戳、地图修订号和边可通行条件明确。异步回环可能导致旧节点坐标失效；动态障碍也不能永久沉淀为静态图上的“可通行”边。

### 实验、实时性与工程风险

论文报告单机器人图更新达到毫秒级、并行训练覆盖数百机器人、相对对照训练墙钟时间下降约一个数量级。这里的加速是图构造与训练吞吐，不是路径长度/SLAM精度提高10倍。实际部署应分别测图维护P95和从传感器到安全控制的完整延迟。论文称有开源实现，但本轮未核实准确的官方GitHub仓库URL，所以仅链接原论文。

### 可复现性与适合谁关注

适合机器狗拓扑导航、海量环境训练和ROS2图记忆。复现应固定同一个SLAM结果，比较CPU与GPU图维护的节点/边数量、回环更新一致性、显存及每环境吞吐。空间图可以辅助全局路由，但不能替代最新Costmap的实时安全检查。

来源：[GGraph原论文](https://arxiv.org/abs/2610.28953)。

---

## 3. RangeNav：18.3万参数的360° LiDAR导航特征

**时间回补：arXiv v1于2026-10-21 UTC提交，10月22日更新v2。**

### 为什么重要

全景LiDAR在黑暗和遮挡环境中比窄视场相机拥有更完整的几何感知，但传统高维点云编码器在多环境RL训练中开销较高。RangeNav将360°扫描转成Range Image，通过仅**183k参数**的紧凑编码器学习导航相关特征，再将编码器冻结供策略复用。

### 模块、传感器假设与结构

```text
360° LiDAR Scans
        ↓
Circular Range Image
        ↓
Anisotropic Convolution + Circular Padding
        ↓
Range Reconstruction + Segmentation + BEV
        ↓
Frozen Compact Encoder (183k)
        ↓
RL Navigation Policy
```

各向异性卷积适应宽而矮的距离图，Circular Padding处理0°/360°接缝。冻结编码器避免每种新策略都重训感知，但输入仍依赖真实雷达扫描线排列、方位起点、异常回波处理和训练数据域匹配。

### 结果、鲁棒性和风险

与只做距离重建预训练的对照相比，联合语义/BEV任务在作者程序化训练环境中使成功率平均提高**32.03个百分点**，在分布外仿真环境中提高**23.73个百分点**。还展示了Unitree B2-W在弱光、施工、人群环境中的零样本部署。论文没有报告能直接替换为M10前后两台96线LiDAR后的FPS或安全保证；源码权重尚标记计划发布。不同线束数、雷达回波选择和地面法向分布变化都可能带来域偏移。

### 适合谁关注与工程落地启发

适合96线LiDAR机器狗导航和低功耗感知。先冻结同一批ROS bag，比较原始Range、重建预训练和语义+BEV特征的导航表现及P95编码成本。动作下发仍走独立速度/碰撞安全层；更高的平均RL成功率不能替代硬件急停。

来源：[RangeNav论文](https://arxiv.org/abs/2610.29845) · [作者项目页](https://rangenav.github.io/)。

---

## 4. Flow Matching + MPC：路径生成负责提出方案，约束控制负责执行

**时间回补：arXiv v1于2026-10-21 UTC提交。**

### 为什么重要

Flow Matching擅长学习路径的多模态分布：同一障碍可以从左侧或右侧绕行。可是生成的路径不保证满足当前速度、加速度、障碍间距或执行器限制；若把生成轨迹直接发给机器人，实际上是把概率模型输出当成了运动安全证明。

### 算法模块与动力学约束

```text
Goal / Scene / Demonstrations
             ↓
Flow-Matching Multi-Modal Path Proposals
             ↓
MPC Tracking
  ├─ System Dynamics
  ├─ State / Input Bounds
  └─ Dynamic Obstacle Constraints
             ↓
Execute Safe Prefix
             ↓
Observation Update & Event Replanning
             ↺
```

本文还将MPC的规划执行反馈给后续生成模块，而非每个周期从头猜一条新轨迹。真正的风险在于MPC模型失准、障碍观测过期，以及QP/NLP本身没有可行解。必要的保守停车和失败退出不能交给生成模型自行决定。

### 结果、实时性、鲁棒性与复现

论文展示杂乱环境仿真中的导航，但公开摘要没有足够统一的碰撞率或P95求解时间，不能声称所有场景“形式化安全”。目前未确认成熟的官方代码。对已有MPC系统最小改动是保持动力学/求解器不变，只替换全局路径候选，在同一任务中比较A*路径、Flow路径、Flow+MPC的成功率、净空、求解器不可行次数与P99响应。

### 适合谁关注与工程落地启发

适合狭窄走廊机器人、动态绕障和基于MPPI/MPC的控制栈。路径的地图修订号、生成完成时间以及控制执行时间必须一致，已过期的生成前缀应直接丢弃。

来源：[Flow Matching + MPC论文](https://arxiv.org/abs/2610.29377)。

---

## 5. HyperDrone：GPU批量视觉无人机仿真加速不等于真机控制频率

**时间回补：arXiv v1于2026-10-20 UTC提交，CoRL 2026接收。**

### 为什么重要

视觉无人机RL需要大量运动和渲染样本，而CPU动力学与GPU渲染、跨设备拷贝可能限制吞吐。HyperDrone集成多旋翼GPU原生批量动力学与HyperLux视觉渲染，支持RGB、深度、分割、法向和光流，并提供可配置照明、材质、运动模糊。

### 算法模块、渲染后端与假设

```text
Vectorized Quadrotor Physics
            ↓
HyperLux GPU Rendering
(RGB / Depth / Seg / Normal / Optical Flow)
            ↓
RL Batch Rollouts
            ↓
Vision Control Policy
            ↓
Sim-to-Real Tests on Camera Crazyflie
```

后端包括OptiX、Vulkan、Metal和WebGPU。作者报告在所选对照下批量模拟吞吐**超过20倍**，消费级GPU上可达到每秒**数百万次渲染帧**，即在大量环境中累积的离线仿真帧数，并不是单架无人机的实时camera FPS或飞控Hz。还展示了纯视觉偏航策略在真实Crazyflie完全机载运行。

### 风险、可复现性与适合谁关注

重点是训练仿真中的光照/模糊与真实相机的域差异、简化动力学与推力模型的差异。当前未确认完整官方源码。建议相同GPU及视觉分辨率与现有模拟器对比samples/s、显存、训练墙钟时间、物理轨迹误差和真实闭环表现；不要以高模拟FPS替代系统级延迟验证。

来源：[HyperDrone论文](https://arxiv.org/abs/2610.28950)。

---

## 6. T-WLA：用高速触觉修订尚未执行的视觉动作块

**时间回补：arXiv v1于2026-10-20 UTC提交。**

### 为什么重要

抓握、插入和物体滑移发生得往往比视觉主干刷新更快。如果每次触觉异常都重新运行VLA视觉编码器，会增加动作响应时间；若只用固定力阈值，又可能忽略当前任务意图。T-WLA在视觉推理时构建可缓存的任务感知记忆，再由触觉小网络用这份缓存对**未执行动作**预测残差修正。

### 算法模块与传感器假设

```text
Image / Language / History
            ↓
Visual Memory + Base Action Chunk
            ↓
Fast Incoming Tactile Observation
            ↓
Task-Aware Residual Editor
            ↓
Only Unexecuted Chunk Segment
            ↓
Independent Contact / Motor Safety
```

未来视觉和触觉预测作为训练期辅助监督，部署时无需每次触觉反馈重跑大视觉主干。关键工程前提是触觉数据和动作块真实执行时刻一致，不能改写已经执行的历史命令。

### 结果、实时性与风险

在EgoTouch和Tachin评估中作者报告关节位置MPJPE相对最佳对照减少约**30%**，四项真实灵巧操作任务的平均成功率约**50%**。这离可靠工业装配仍有距离，也没有提供对所有触觉设备有效的固定实时毫秒数。作者项目页有实验视频及代码入口，但具体权重的完整可用性需再核实。

### 适合谁关注与工程落地启发

适合灵巧手、视觉—力觉融合及动作块控制。比较触觉阈值、全量重新推理、触觉残差编辑三组，在相同接触任务上记录P95事件至动作修正延迟、接触峰值、任务成功率和过期动作拒绝率。底层力限幅不能由VLA替代。

来源：[T-WLA论文](https://arxiv.org/abs/2610.28814)。

---

## 7. HuMiT：四个稀疏姿态加根部状态实现G1低延迟遥操作

**时间回补：arXiv v1于2026-10-21 UTC提交。**

### 为什么重要

复杂人形遥操作流程可能要求把人类动作重定向成机器人全身关节轨迹，或依赖未来帧优化。这样增加计算和网络延迟，机器人在快速运动中会落后于操作者。HuMiT采用简化的本体参考：根部高度、根部速度和四个当前帧关键点的SE(3)姿态，由统一策略补全全身动作。

### 模块与动力学假设

```text
VR / Human Observation
          ↓
Root Height + Root Velocity + Four SE(3) Keys
          ↓
Unified Tracking Policy
          ↓
G1 Whole-Body Execution
          ↓
Low-level Balance / Contact / Joint Limits
```

依赖当前帧而非未来帧，降低重定向链路复杂度；但压缩参考不等于不可见的足底、关节和身体姿态已经满足安全约束，仍需低层独立控制。

### 实验结果与风险

作者报告头显输入到策略输出通信与推理约**20 ms**，视觉光流测得中位可见端到端延迟约**65 ms**，不能把前者当作机器人执行反应总延迟。展示了G1接球和移动操作。高速遥操作仍需要操作者失联、网络抖动和旧动作队列的保护；中位延迟应辅以P99和最大连续丢包分析。

### 可复现性、适合谁关注与工程落地启发

适合G1、远程全身控制与低带宽遥操作。暂未确认完整官方代码模型。建议为头显采集、报文到达、策略输入、执行器指令与电机反馈分别打时间戳，验证四关键点方案和密集姿态重定向的跟踪误差及全链路延迟，先完成失联回退状态机再扩大动作范围。

来源：[HuMiT论文](https://arxiv.org/abs/2610.29903)。

---

## 8. VerifierBench：只会拒绝的自动测试器，并不是优秀的Agent验收器

**时间回补：arXiv v1于2026-10-19 UTC提交，10月22日列入cs.SE公开批次。**

### 为什么重要

Coding Agent可以自动写测试和验证器，但若把“错误答案是否被拒绝”当唯一指标，最容易作弊的实现就是拒绝所有输出。许多正确但代码结构不同的方案也会被错误判失败。VerifierBench显式区分**合法方案的接受能力**和**非法方案的拒绝能力**。

### Benchmark、实验与工程价值

```text
Task Spec + Environment
           ↓
Agent-Generated Executable Verifier
           ↓
Independent Hidden Cases
 ├─ Valid Alternative Implementations
 └─ Invalid or Adversarial Outcomes
           ↓
Balanced Accuracy / Failure Diagnosis
```

基准有**222个任务**，来自6个基准，拥有**4,993条隐藏测试用例**；作者利用Verifier4Verifier（V4V）进行源验证器和测试集质量审查，并在统一Harness上测19种模型。归一化平衡准确度在**10.6—62.1**间。一个关键结论是：正确接受合法替代方案比拒绝明显非法结果更难。此处报告的指标并不是通用软件修复成功率。

### 权限、可复现性与落地启发

与普通单测不同，验证器本身属于必须测试的软件。应从过去已经正确合入的PR中生成至少两种语义等价合法实现，另构造一个确实违反行为契约的版本。验证器必须接受两种合法实现，拒绝违法版本；对全部拒绝的“严格检查”直接判为失败。模型生成的验收代码必须在隔离沙盒运行，不能拥有发布或生产数据库权限。

适合Codex、Claude Code、Spring Boot跨模块和ROS2 C++自动验收。本轮未确认完整官方代码，引用原始论文。最小A/B：人工维护测试器、Agent自动生成验证器、带双向合法性回归的验证器，比较false reject、false accept以及真实每成功任务成本。

来源：[VerifierBench论文](https://arxiv.org/abs/2610.28679)。

---

## AI Coding 实战技巧精选

### 技巧 1｜用Copilot指标API直接核对团队实际使用的Skill与MCP

- **来源**：GitHub官方，2026-10-22；[原始公告](https://github.blog/changelog/2026-10-22-custom-skills-agents-and-mcp-servers-in-usage-metrics-api/)。
- **一句话结论**：Copilot用量指标新增自定义Skill、Agent、MCP、斜杠命令和Plugin的**具体名称**，不必将一切归入other。
- **具体怎么做**：① 确认有View Copilot Metrics权限及组织Usage Metrics Policy；② 获取组织已有的1-day/28-day usage报告；③ 分析`totals_by_skill`、`totals_by_custom_agent`、`totals_by_mcp`、`totals_by_slash_cmd`、`totals_by_plugin`；④ 与任务成功率和人工修正成本合并分析，淘汰只调用却没有实际收益的Skill。
- **适合什么场景**：Copilot CLI、企业Skill/MCP治理、多Agent成本优化。
- **注意**：每类最多25条，余项归入other，客户端需Copilot CLI 1.0.97+或相应SDK；旧数据不回填，遥测指标不能直接当精确费用或成功率。

### 技巧 2｜审计Copilot全局默认策略，避免新MCP权限被无意默认开启

- **来源**：GitHub官方，2026-10-22；[原始公告](https://github.blog/changelog/2026-10-22-global-default-for-copilot-features-generally-available/)。
- **一句话结论**：10月22—26日开始将部分未显式配置的GA Copilot功能按全局默认值处理，企业需要明确设置工具权限。
- **具体怎么做**：① 企业管理员打开`AI Controls → Copilot → Default policy for new features`；② 检查`Features & clients`、`MCP servers in Copilot`尚处于Unconfigured的条目；③ 对具有写仓库、执行Shell或外部MCP访问的功能显式设置符合内控的策略；④ 以低权限测试账户和组织策略API只读核验。
- **适合什么场景**：GitHub Copilot Business/Enterprise、企业MCP权限、长期Agent。
- **注意**：已显式设置的不受本轮默认迁移覆盖；改全局默认不会自动追溯更改所有旧的单项设置。

### 技巧 3｜升级Claude Code并回归符号链接拒写、子Agent权限继承

- **来源**：Anthropic，2026-10-22；[官方Claude Code v2.1.309 Release](https://github.com/anthropics/claude-code/releases/tag/v2.1.309)。
- **一句话结论**：该版本修复符号链接绕过拒写、组合Shell命令权限误判、MCP配置变更、子Agent未继承工具拒绝等问题。
- **具体怎么做**：① 在隔离测试机通过`claude --version`核验修复版本，升级到2.1.309或更新的稳定版本；② 在临时测试文件夹配置denyWrite，检查符号链接指向拒写路径时能否成功阻止写入；③ 用无害组合Shell命令核查目录变更后的写权限判断；④ 启动无害子Agent，确认上层deny规则正确继承且MCP配置文件未发生不应有的变化。
- **适合什么场景**：Claude Code CLI、Worktree、Managed Agents、多MCP自动编码。
- **注意**：不要在生产密钥、系统目录或真实部署仓库尝试越权复现；升级CLI不能替代OS权限和独立审批。

---

## 经典论文回顾

### TrajOpt：基于序列凸优化的连续碰撞检查（IJRR 2014）

**发表时间与历史位置**：John Schulman等《Motion Planning with Sequential Convex Optimization and Convex Collision Checking》2014年6月11日在线发表于*International Journal of Robotics Research*，33卷9期；2013年RSS已经有相关前期路线。原文：[期刊DOI](https://doi.org/10.1177/0278364914528132)，[历史源码](https://github.com/joschu/trajopt)。

### 核心问题与算法思想

传统离散路径点碰撞检测容易漏掉两点之间扫掠轨迹的障碍碰撞。高自由度机械臂既有自碰撞、环境碰撞和末端目标，又受到关节限制，直接求非凸全局最优通常太昂贵。TrajOpt在当前轨迹附近将非凸目标和约束近似为一系列凸子问题，通过Trust Region和逐步提升的罚函数求局部可行轨迹，并强调**连续时间扫掠碰撞检查**。

```text
初始轨迹
  ↓
距离/碰撞代价及约束线性化
  ↓
Sequential Convex Subproblem
  ↓
Trust Region + L1 Penalty
  ↓
连续路径段扫掠碰撞复核
  ↓
更新轨迹或重新初始化
  ↓
独立动态与执行器检查
```

### 传感器/动力学假设与历史贡献

TrajOpt依赖可靠机器人几何、关节限位、环境障碍和目标约束。它并不是独立的SLAM/感知器；若输入地图错了，优化仍可能给出错误的局部最优。论文验证7自由度机械臂、PR2和Atlas类型的高维规划，在特定配置下报道约100—200ms级轨迹规划；它不是保证每10ms能解完整轨迹，也不自动包含真实电机动力学。

### 后续发展、局限、代码与可复现性

该路线影响了后续优化式路径规划与机器人软件栈，与CHOMP/STOMP、OMPL RRTConnect、GPMP2在求解机制上各有优缺点。序列凸化对初值敏感，窄通道中可能收敛至不可行的局部盆地，因此用采样规划先生成多条拓扑不同的候选往往更稳妥。历史源码依赖较旧，应先在可重现容器中进行离线对照。

最小A/B：固定相同碰撞地图、机械臂及末端目标，比较RRTConnect+平滑、CHOMP与TrajOpt，统计时间、碰撞漏检、最大约束违例及P95；尤其检查**轨迹点之间**的碰撞。今天的Flow Matching可以作为新的全局初始化生成器，但无论路径来自采样还是神经模型，都应再经过TrajOpt式碰撞检查和实时MPC的动态约束。

---

## 今日结论

本期的共同思路是显式管理**观测可信度、训练与执行预算，以及验证器自身的正确性**。VeriCalib不以漂亮的RMSE代替外参可辨识度；GGraph用统一图语义连接训练与部署；RangeNav证明轻量距离图编码器也能支持真实复杂导航；Flow-MPC与TrajOpt将路径“提出方案”和“可执行”明确分层。HyperDrone追求仿真批量吞吐，但不把它误认成真机控制频率；T-WLA关注毫秒级触觉状态，HuMiT压缩上游遥操作参考。VerifierBench说明Coding Agent生产的验收器也必须通过合法和非法双向用例，不能因“拒绝率高”便误判成功。

三个AI Coding技巧则提醒实际研发：Skill/MCP使用量不等于收益；默认启用策略可能改变工具权限；工具拒绝规则应在符号链接、组合命令与子Agent上保持一致。

**一句话：把哪些数据可信、哪个动作已经过期、哪项约束真正可行，以及什么样的实现必须通过验收，都设计成可测的正式系统状态。**

---

## 最值得深入研究或尝试复现的方向

1. **相机—LiDAR标定质量**：对相同板面数据做弱方向和独立验证样本，比较总体RMSE与逐方向外参协方差。
2. **GGraph多环境空间拓扑**：固定前后双雷达ROS2 bag，检验图更新P95、回环版本一致性和GPU训练内存。
3. **RangeNav多线束迁移**：测试16/96/128线的Range Image循环拼接、编码成本及低纹理环境导航。
4. **Flow Path + MPC**：固定动力学、障碍和规划预算，对比候选质量、控制不可行率和实际净空。
5. **HyperDrone批量仿真**：在固定GPU及图像分辨率下比较训练样本吞吐与真实Crazyflie策略质量。
6. **T-WLA触觉动作块编辑**：保证触觉修正只作用于未执行片段，检查接触峰值、时序和P95延迟。
7. **HuMiT远程参考压缩**：分开记录头显采集、传输、推理、命令执行时间，验证断联安全回退。
8. **VerifierBench双向验收**：让生成的测试器接受两种合法实现并拒绝至少一种确定违约实现。
9. **Coding Agent权限和收益**：核对Copilot Skill/MCP指标、企业新功能默认策略及Claude Code sandbox deny规则。

---

## 参考资料

**最新公开列表**：[arXiv Robotics](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/new)。

**SLAM/导航**：[VeriCalib](https://arxiv.org/abs/2610.28791) · [GGraph](https://arxiv.org/abs/2610.28953) · [RangeNav](https://arxiv.org/abs/2610.29845) · [RangeNav项目](https://rangenav.github.io/)。

**控制/仿真/人形**：[Flow-MPC](https://arxiv.org/abs/2610.29377) · [HyperDrone](https://arxiv.org/abs/2610.28950) · [T-WLA](https://arxiv.org/abs/2610.28814) · [HuMiT](https://arxiv.org/abs/2610.29903)。

**AI Coding**：[VerifierBench](https://arxiv.org/abs/2610.28679) · [Copilot Usage Metrics](https://github.blog/changelog/2026-10-22-custom-skills-agents-and-mcp-servers-in-usage-metrics-api/) · [Copilot企业策略](https://github.blog/changelog/2026-10-22-global-default-for-copilot-features-generally-available/) · [Claude Code 2.1.309](https://github.com/anthropics/claude-code/releases/tag/v2.1.309)。

**经典**：[TrajOpt期刊论文](https://doi.org/10.1177/0278364914528132) · [TrajOpt源码](https://github.com/joschu/trajopt)。
