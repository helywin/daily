---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-29"
date: 2026-10-29 09:00:00 +0800
description: "RESPLE2 连续时间多传感器里程计与开源 ROS2 工程、SG²SLAM 几何原生 3DGS、G1 低矮空间爬行、Go2 多步态 CPG、GPU 多机械臂规划、事件相机微型无人机、三维世界动作模型、工具副作用型 Coding Agent；另附三项可执行技巧与经典连续时间估计论文。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-29

## 摘要

**检索基准：2026-10-29 09:03（Asia/Shanghai），星期四。**

arXiv 的最近常规公开批次为 **2026-10-28**：Robotics（cs.RO）共 125 个列表条目，其中 76 个新提交；Software Engineering（cs.SE）共 65 个列表条目，其中 33 个新提交。列表总数包含交叉收录和版本更新，并不等于全部为首次投稿。[Robotics 原始列表](https://arxiv.org/list/cs.RO/new) · [Software Engineering 原始列表](https://arxiv.org/list/cs.SE/new)。

先检查最近 24 小时，再向最近七天扩展，选题与仓库此前 **1,147 条覆盖记录**按标题、arXiv ID、DOI、项目页及代码仓库联合去重。今天选择的八篇主动态 v1 实际提交于 **2026-10-26—27 UTC**，均超过最近 24 小时，正文统一标注“时间回补”；这不等于论文不新，而是区分提交时间和 arXiv 列表公开时间。

**本期 8 条主动态：** 两项 SLAM/状态估计（RESPLE2、SG²SLAM）、三项机器人控制与规划（REACH、CPG-ENN、cuArms）、一项微型无人机事件视觉训练与端侧部署、一项 3D 世界动作模型（E0.5）、一项 Coding Agent 工具副作用训练（EffectWorld）。另有 3 条官方原始发布对应的 AI Coding 实战技巧和一篇 2012 年连续时间估计经典论文。

本期最值得直接复现的是 **RESPLE2**：官方仓库已经有 ROS2 Humble/Jazzy 工程、多个数据集启动配置及全球样条回环选项，适合与现有 FAST-LIO / LIO-SAM 在同一录制数据上做实测 A/B。最值得注意的控制突破是 **REACH** 把三维 LiDAR 规划与 G1 站立—低姿态—爬行双向模式切换结合，而不再局限于仅调节站立高度。**事件相机无人机**则报告了从解析事件仿真、INT8 策略到 56 g 机载闭环的完整路径。所有结果仅代表论文指定条件，尚不能推广为任何特定工业平台的保证。

---

## 1. RESPLE2：非均匀 B 样条把异步多传感器观测真正统一在连续时间轨迹上

**时间回补：2026-10-27 17:33 UTC 首次提交。**

### 为什么重要

LiDAR、IMU、相机和足端运动学的数据频率、采集时刻不一致。传统离散时间滤波器如果把所有观测硬塞到最近状态时刻，可能在快速转动、高加速度和不同雷达扫描时刻引入时间近似误差。

RESPLE2 使用**非均匀 B 样条**表示连续六自由度轨迹，将 IMU 驱动的样条控制点预测嵌入迭代 EKF，并允许 LiDAR、视觉和运动学观测在各自原始时间戳处更新。非均匀节点还可以根据运动与观测密度调整，不要求所有场景采用固定时间采样。

### 算法模块、观测与理论边界

```text
IMU 高频运动信息
         ↓
非均匀 B 样条控制点预测（knot clamping）
         ↓
Iterated EKF + 控制点延拓后的状态重置
         ↑
LiDAR / Camera / Leg Kinematics
         ↓
按原始时间戳生成连续时间残差
         ↓
高频 6-DoF 里程计与轨迹
         ↓
可选 LiDAR-Visual 回环约束
         ↓
全局样条控制点修正
```

其关键不是把所有传感器变为同一 ROS Topic 频率，而是为任意时间戳建立同一条可求值、可求导的连续轨迹。前提仍包括时间戳可靠、外参正确、运动及噪声模型合理。采用 IKF/EKF 不会自动消除弱特征走廊中的不可观测方向。

### 实验结果、实时性与可复现性

作者在手持、履带、腿足、空地混合平台，以及包含强加速度和激烈机动的数据上测试，报告对应传感器配置下与先进多传感器里程计相当或更好的精度、鲁棒性，并保持实时执行。**没有一个可以直接外推到所有平台的统一 FPS 或 ATE 降幅**，应在统一 Bag 上重新测量。

官方仓库目前已经可访问，不只是论文宣称“即将开源”。支持 **ROS2 Humble（Ubuntu 22.04）和 Jazzy（Ubuntu 24.04）**，包括 LIO、LVIO、LKIO、LKVIO 配置、多个数据集示例，以及 `if_loop_closure: true` 的可选全局修正。工程依赖 Pinocchio 3.9.0，仓库采用 **GPLv3**；商业集成必须核查许可证义务，作者在 README 提到可联系讨论其他许可。

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone --recursive https://github.com/ASIG-X/RESPLE2.git
cd ~/ros2_ws
colcon build --symlink-install --packages-select resple2
source install/setup.bash
# 按仓库 README 选择 GrandTour / JEPLO / HOPPER 等数据集启动文件
```

运行前还应按 README 安装 ROS、Ceres、Pinocchio 等依赖，不能仅凭上面几行认为构建已完整满足前提。

### 鲁棒性、工程风险与适合谁关注

主要风险是样条重置与观测延迟一致性、异常时间戳、回环后局部轨迹的平滑修正，以及激烈运动时的 IMU 饱和。推荐把同一 Bag 的 LiDAR/IMU/图像输入 RESPLE2、FAST-LIO2、LIO-SAM，测量 ATE/RPE、运动畸变、退化方向 NEES、P95/P99 前端耗时和回环前后轨迹连续性。

**适合：** 双 LiDAR、轮足融合、ROS2 SLAM、异步相机/IMU 和强机动定位。对于前后两台不同扫描模式雷达，先完成各自驱动的统一时钟、坐标外参，再决定是否融合到同一估计器。

**来源：** [原论文](https://arxiv.org/abs/2610.37602) · [官方 ROS2 代码](https://github.com/ASIG-X/RESPLE2) · [项目页](https://asig-x.github.io/resple2_web/)。

---

## 2. SG²SLAM：用流式空间几何约束单目 3DGS，减少跟踪误差污染地图

**时间回补：2026-10-26 21:34 UTC 首次提交。**

### 为什么重要

很多 3D Gaussian Splatting SLAM 在当前帧估计位姿后再更新地图。如果单目尺度或跟踪错误被吸收到地图参数中，后续渲染会看起来越来越自洽，却可能对应错误几何；单独优化追踪和高斯地图也会产生不一致。

SG²SLAM（Spatial Geometry-Informed 3D Gaussian Splatting SLAM）通过**分块级流式度量空间几何先验**同时监督跟踪与映射，还为高斯原语加入对观测射线方向敏感的表示，以应对不同单目视角的信息变化。

### 算法模块与传感器假设

```text
单目连续图像
     ↓
Streaming Spatial Geometry（chunk-level metric prior）
     ├── 位姿约束
     └── 地图几何约束
     ↓
Ray-conditioned Gaussian Primitives
     ↓
联合优化相机轨迹与 3DGS
     ↓
稠密几何 / 渲染地图 → 下游几何导航
```

作者在 KITTI 和 Waymo Open 上比较了逐帧二维到三维关联基线，报告单目室外导航中较好的轨迹与地图表现。摘要没有足够的跨序列数值用于断言具体厘米级定位性能，也没有可验证的嵌入式实时 FPS。

**注意：** 所谓“度量先验”需要检查其获得方式，以及在不具备真实尺度锚点时是否引入数据集偏置。动态汽车、夜间光照和大面积低纹理路面会同时影响空间几何和高斯优化。高渲染质量并不等于导航可通行精度。

### 可复现性、风险与工程落地启发

作者明确表示**代码将在接收后公开**，所以目前不宜声称已有官方可运行实现。可以先固定相同 KITTI 序列，对比视觉位姿固定后构图、追踪映射交替优化、联合优化三个思想的轨迹漂移、地图几何残差、重渲染误差与 GPU 显存。

**适合：** 3DGS SLAM、单目视觉定位、室外导航。建议继续保留 LiDAR 的几何安全地图，先将 3DGS 用作稠密重建与语义查询，不要直接以高斯外观地图替代 ESDF/Costmap。

**来源：** [原论文](https://arxiv.org/abs/2610.36312)。

---

## 3. REACH：G1 用 LiDAR 规划高度，再实现站立与低矮爬行双向切换

**时间回补：2026-10-27 02:59 UTC 首次提交；Humanoids 2026。**

### 为什么重要

很多人形高度可调策略只能“蹲低走路”，但真正的低矮通道可能需要机器人从双足站立切换为四肢支撑的爬行模式。切换过程涉及接触点和支撑多边形突变，不能只把目标机身高度连续减小。

REACH 采用分层强化学习：可变高度双足策略、低姿态爬行策略、双向过渡策略，加上点云驱动的三维规划器，构成完整的低净高通行链路。

### 算法模块、动力学与观测假设

```text
LiDAR 点云 → 三维可通行路径与净高估计
                 ↓
       目标高度 + 行进速度 + 模式
                 ↓
  双足高度策略  ↔  双向模式过渡  ↔  爬行策略
                 ↓
   关节命令 / 本体感觉历史潜变量
                 ↓
            Unitree G1
```

作者报告双足模式机身高度范围为 **1.27—0.50 m**，爬行模式为 **0.50—0.20 m**。通过本体感觉历史潜变量刻画接触和地形状态，并使用双向过渡连接不同接触模式。

### 实验、实时性与可复现性

项目页展示 G1 真机的变高行走、爬行、站立恢复和连续低净高障碍穿越。其公开摘要没有给出普适的成功率、控制频率、可通过最大坡度等数值，不能凭演示推断出机器人一定能在任意楼梯/狭窄空间安全通行。

**开源核验：** 论文称代码视频可从项目页获取，但核查项目页发现代码栏目前仍标记 **“To be released”**，视频可看、完整代码未确认开放。应以项目实际文件为准，而非以论文一句“code available”直接认定可复现。

### 鲁棒性、工程风险与适合谁关注

LiDAR 给出的净高要考虑机体姿态、背部/四肢包络、定位误差和控制跟踪误差。模式切换失败后必须能停留在稳定支撑状态；只看机身中心高度会导致肩部、肘部或腿部碰撞。

**适合：** 人形跨狭窄空间、跨层三维导航、任务级运动模式规划。若现有机器狗平台只开放登梯/速度 SDK，不应直接移植 G1 的关节策略，但可以借鉴“路径输出速度、净高与运动模式”三个命令维度。

**来源：** [原论文](https://arxiv.org/abs/2610.36546) · [官方项目与真机视频](https://aislab-sustech.github.io/REACH/)。

---

## 4. CPG-ENN：用可解释六参数调节 Go2 五种步态，不为每个步态训练独立控制器

**时间回补：2026-10-27 02:49 UTC 首次提交。**

### 为什么重要

机器狗从慢走、快跑到腾跃时，采用每个步态一套独立策略，往往会在策略切换时引起动作突变，并增加训练和维护成本。

CPG-ENN 将显式神经节律和学习式关节动作执行分开。一个具有对称结构的八神经元中央模式发生器（CPG）生成节律，四条腿共享的 Execution Neural Network 将轨迹/节律参数映射为关节角参考，在线无需重新运行逆运动学；上层单一反馈策略只调节 **6 个具有物理解释的轨迹变量**。

### 算法模块、动力学与鲁棒性

```text
vx / vy / yaw-rate
        ↓
六个可解释步态/轨迹参数
        ↓
八神经元 CPG 生成协同节律
        ↓
腿共享 ENN → 关节角参考
        ↓
底层关节执行与姿态反馈
```

覆盖 walk、trot、pace、bound、pronk 五种步态。作者在模拟中对 20 种有向步态切换、速度集合 {0.5,1.0,1.5,2.0} m/s 的源—目标组合，报告 **99.39% 切换成功率**；并在 Unitree Go2 上验证五种步态及切换。

这属于所选仿真工况的切换成功率，不代表任意室外地形/载荷下也能达到 99.39%。关节角控制接口、腿部机械参数、足地摩擦和姿态估计误差都影响真机迁移。

### 实时性、可复现性与工程落地启发

摘要没有提供完整闭环 P99 和公开权重；目前未确认可直接运行的官方仓库。推荐先在 MuJoCo 固定 Go2 机器人参数，比较一个统一 CPG-ENN 与五套单独步态策略的切换瞬间躯干角速度、足端滑移、平均速度误差和对侧向扰动的恢复。

**适合：** Go2、低层步态控制、强化学习控制架构。现阶段如果只通过厂家 SDK 速度/登梯模式调度，应学习它的“统一反馈参数化”思路，避免未经授权直接替换底层关节控制。

**来源：** [原论文](https://arxiv.org/abs/2610.36537)。

---

## 5. cuArms：GPU 冲突搜索把多机械臂任务分配、时序和运动规划接在一起

**时间回补：2026-10-26 20:31 UTC 首次提交。**

### 为什么重要

多机械臂共享工位不仅要避免机器人互撞，还要解决谁抓哪个物体、先后时序、交接时刻以及可用抓取姿态。若直接求解全部机械臂的联合配置空间，搜索往往迅速膨胀。

cuArms 在每个机械臂的可复用多模态 Roadmap 上构造候选动作，再利用 GPU 批量冲突表与 Lazy Conflict-Based Search 排除碰撞和死锁。高层 ScheduleStream 或 Coding Agent 只提供任务分配、抓取/放置及时间安排的候选骨架，cuArms 负责判断其可执行性并持续优化。

### 算法模块、关键技术和实时性

```text
目标/物体/机械臂定义 + 技能采样器
                ↓
高层调度器（或受控 Coding Agent）
                ↓
Task Assignment / Schedule Skeleton
                ↓
每台机械臂的多模态 Roadmap
                ↓
GPU Batch Conflict Tables
                ↓
Lazy Conflict Search + Anytime Refinement
                ↓
联合无冲突轨迹 + 独立执行检查
```

论文和官方项目展示多臂焊接、双臂搬运、桌面装配、长期 LEGO 任务等。作者报告**可以实时获得初始解，随后通过 Anytime 搜索改进**，但没有可跨机器直接复用的统一毫秒数；官方页面还明确指出一些对照实验的计时不含 Roadmap 构建，不能只比较演示中的核心搜索时间。

项目专门展示 Coding Agent 作为调度器：Agent 通过 API 反复提出方案，真实碰撞和任务结果仍由运动规划器及独立校验判定。这比让 LLM 直接生成一长串关节位置更容易控制工程风险。

### 可复现性、假设和工程风险

官方项目和演示可访问，但当前没有确认作者发布了完整可构建的 cuArms 源码。规划仍然依赖可靠的机器人碰撞几何、夹具标定、抓取 IK 与动作时间假设，实际协同控制不能绕过手臂急停和运动控制器限幅。

**适合：** 多机械臂共享工位、协作装配和机器人 Coding Agent Harness。可用现有 MoveIt/OMPL 两机械臂场景对照集中式联合规划与“调度骨架＋逐臂规划＋冲突修复”，统计总任务完成时间、冲突次数、规划 P95 与可复现失败原因。

**来源：** [原论文](https://arxiv.org/abs/2610.36250) · [官方实验与多臂视频](https://cuarms.github.io/)。

---

## 6. Rendering-Free Event Navigation：事件视觉微型无人机实现仿真到 56 g 真机的端侧闭环

**时间回补：2026-10-27 16:56 UTC 首次提交。**

### 为什么重要

使用事件相机训练高速无人机避障时，很多模拟器先生成真实感 RGB，再把相邻图像的亮度变化转换成事件流。这个昂贵的渲染过程与事件相机实际需要的“运动对比边缘”并不完全对齐，也会严重限制强化学习采样速度。

新工作直接从**场景几何与自运动**解析生成事件观测，绕开完整 RGB 渲染，再训练小型端侧避障策略。

### 算法模块

```text
3D Geometry + UAV Ego-motion
               ↓
解析运动边缘事件模型（不渲染 RGB）
               ↓
64×64 Event Observations
               ↓
GPU 并行 RL 训练
               ↓
INT8 量化策略（约 1.2 MB）
               ↓
GenX320 事件相机 + OpenMV N6
               ↓
56 g Crazyflie 机载自主避障
```

### 实验、实时性与数据边界

作者报告在指定 GPU 上生成一帧 64×64 事件观测约 **17 μs**，相比所选传统渲染管线超过 **400 倍**速度；训练在 30 分钟内收敛。这里是**仿真观测生成吞吐**，绝不能解释成真实无人机以几十千赫运行完整飞控。

未见拥挤赛道的仿真成功率约 **83%**，平均目标速度 2.4 m/s；高纹理室内模拟环境约 70%。量化后在 56 g Crazyflie 上使用 Prophesee GenX320 和 OpenMV N6，三个真实障碍课程的成功次数分别为 **5/5、5/6、4/6**，共 **14/17**，作者概述为约 82%。样本规模仍小，且三组实验的复杂度不同。

### 可复现性、鲁棒性与适合谁关注

官方源代码仓库已发布：[tudelft/rendering-free-event-nav](https://github.com/tudelft/rendering-free-event-nav)。先检查其 README、仿真依赖、网络权重和硬件驱动说明，再决定哪部分可直接复现。

主要风险是现实背景纹理、事件阈值差异、振动、低光纹理缺失与场景物体材质。训练时未提供全局定位，真机也不应被误认为获得了长期 SLAM 或绝对地图。

**适合：** 室内小无人机、事件相机、低功耗推理、Sim2Real。工程建议按“解析事件仿真 → 仿真策略 → INT8 量化 → 上板事件链路 → 系留/保护网内测试”递进，并记录事件有效率、控制 P95、量化前后成功率与真机碰撞距离。

**来源：** [原论文](https://arxiv.org/abs/2610.37543) · [作者代码](https://github.com/tudelft/rendering-free-event-nav)。

---

## 7. E0.5：用 3D 基础模型直接预测未来几何与动作，而不只预测未来视频

**时间回补：2026-10-26 UTC 首次提交。**

### 为什么重要

World Action Model 往往沿用视频生成模型或 VLM 主干，将三维几何当作额外输入或辅助监督。对机械臂而言，物体接触和空间结构变化可能比未来 RGB 纹理更重要。

E0.5 直接采用 **3D Foundation Model 作为主干**，联合预测未来三维状态与机器人动作，使几何变化成为核心预测对象。

### 算法模块与训练假设

```text
当前多视角 / 3D 场景表征 + 任务条件
                 ↓
          3D Foundation Backbone
                 ↓
       Future 3D State + Actions
                 ↓
         Robot Action Execution
```

作者首先在 RoboTwin 2.0 上评估未经具身轨迹预训练的版本，报告 Clean **89.90%**、Randomized **50.09%** 成功率；随后在超过 **16 万条 AgiBotWorld-Beta 机器人轨迹**上联合预训练，在 AgileX Piper 与 Zerith H1 真机上，平均任务成功率分别提高约 **15、7 个百分点**。

不同场景和训练条件不能直接比较。该模型也不能因为输出几何而天然具备真实时空可观测性、可靠接触摩擦或可证明的碰撞安全。

### 实时性、开源与工程风险

当前未确认完整可运行的官方训练代码/权重，论文摘要也没有可推广到嵌入式设备的延迟与显存数字。多视角标定、动作时间戳和未来几何监督质量，会显著影响模型在分布外物体上的可靠性。

**适合：** 3D 世界动作模型、VLA、复杂操作数据集。建议在冻结原始模型和同一实验集条件下，对比“仅动作”“未来视频＋动作”“未来 3D 几何＋动作”三类训练目标，并分离记录几何预测、任务成功率与推理成本。让模型负责候选动作，真实空间净空与执行限幅仍由外部模块检查。

**来源：** [原论文](https://arxiv.org/abs/2610.36011)。

---

## 8. EffectWorld：让小 Coding Agent 明确工具的副作用、幂等性和资源访问范围

**时间回补：2026-10-26 10:28 UTC 首次提交。**

### 为什么重要

很多小模型虽然会调用工具，却不知道某次调用是否会写文件、删除数据、可否安全重试，以及多个调用能不能合并。于是可能发生重复写入、重复读取同一状态、危险命令没有确认，或者一轮只能做一个无用操作。

《Small agents should know what their tools do》提出 EffectWorld：让每个工具声明**效果类型、幂等性、读写资源集合**，由可执行验证器检查工具轨迹是否遵守契约，并将低效轨迹优化成训练数据。

### 算法模块与工程价值

```text
Tool Contract: read / write / delete / idempotent / resources
                          ↓
Agent Tool Trace → Replay Verifier
                          ↓
安全性与副作用检查
                          ↓
Compiler-style Trace Optimization
                          ↓
验证过的高质量 SFT 示例
                          ↓
轻量模型适配训练
```

例如 read_file 可以重复读取但成本高；create_issue 需要明确可重复性；delete_file 必须检查资源所有权和批准条件。可由运行时执行器根据类型组织多个有依赖的工具调用，而不是让模型把所有操作混成不可检查的一条自然语言命令。

### 实验结果、泛化边界

作者在 Qwen3-4B 上报告：分布内任务成功率由 **53% 提升至 99%**；未见任务与干扰工具条件由 **52% 提升至 81%**；未见领域由 **74% 提升至 83%**，同时输出 Token 约降到三分之一。在 BFCL 多轮工具调用上从 **21.9 提升至 26.6**。

**这些是作者可执行工具世界及对应基准中的结果，不能解释为任何真实企业仓库修复率从 53% 变为 99%。**

论文还发现一些训练语料中的“拒绝模板”会让小模型学会不调用工具，导致 BFCL 非实时准确率从 88.0 掉到 31.4，过滤后回到 84.8。说明“更多拒绝样本”不一定提升真正的工具调用能力。

### 权限、安全、可复现性与适合谁关注

当前未确认完整独立的官方代码仓库。可以不训练模型，先在现有 Agent Harness 为关键工具附上类似结构：

```json
{
  "name": "update_file",
  "effect": "write",
  "idempotent": false,
  "reads": ["repo/path"],
  "writes": ["repo/path"],
  "requires_approval": true
}
```

再以相同任务比较重复写、无效读、错误重试、真实通过率与每成功任务 Token。工具声明本身不是操作系统权限机制，执行器仍须真正约束写入和远程副作用。

**适合：** Codex 类 Harness、小型 Qwen/DeepSeek Agent、MCP 工具与跨会话开发。工程启发是用少量明确的工具行为契约代替大量流水账式防御文档。

**来源：** [原论文](https://arxiv.org/abs/2610.35981)。

---

## AI Coding 实战技巧精选

### 技巧 1｜GitHub Agentic Workflows GA：把 Markdown Agent 工作流编译为受控 Actions

**来源：** GitHub 官方，2026-10-28：[GA 原始公告](https://github.blog/changelog/2026-10-28-github-agentic-workflows-generally-available/) · [官方 Quickstart](https://github.github.com/gh-aw/setup/quick-start/)。

**一句话结论：** 如需在 GitHub Actions 中运行周期性 Issue/CI 分析，可以把 Markdown 工作流编译成标准 Actions YAML，默认 Agent 只读并通过 Safe Outputs 控制写入，不必维护额外的 Agent 服务。

**具体怎么做：**

1. 在自己有权限的**测试仓库**安装扩展：`gh extension install github/gh-aw`。
2. 在仓库根目录运行 `gh aw add-wizard githubnext/agentics/repo-status`；按提示选择 Copilot、Codex 或其他支持的引擎并配置认证。
3. 审查生成的 `.github/workflows/repo-status.md` 和 `.lock.yml`，特别是权限、Secret、触发器和 Safe Outputs；修改后运行 `gh aw compile`。
4. 经过仓库审批后提交两份文件，可通过 `gh aw run repo-status` 测试，并用 `gh aw status` 检查结果。

**适合什么场景：** 既有 GitHub Actions 的 CI 故障分析、代码扫描报告、只读仓库汇总。**注意：** 默认 Copilot 引擎可能需要有效 Copilot 授权，使用 Codex API 引擎应按文档配置 API Key；不能把个人 ChatGPT 订阅令牌当作 API Key。不要在未审查的 PR 上使用高权限 `pull_request_target` 执行提交代码。

### 技巧 2｜在 Linux Copilot CLI 中试本地模型自动路由，但不要误认离线运行

**来源：** GitHub 官方，2026-10-28：[本地模型路由公告](https://github.blog/changelog/2026-10-28-github-copilot-fusion-now-supports-selection-of-local-models/) · [CLI 自定义模型文档](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-llm-models)。

**一句话结论：** Copilot Fusion 实验预览支持通过 CLI 在符合条件的**本地 OpenAI-compatible 模型**与云模型间智能选择，Linux 需要手工提供本地服务；不是所有 BYOK 模型自动可用于路由。

**具体怎么做：**

1. 在测试机器启动官方支持的本地模型推理服务器，核实 API、可用模型和剩余显存；按照文档在 Copilot CLI 注册为 Local Provider。
2. 在 Copilot CLI 开启 Experimental/local routing，打开 `/model`，确认本地模型出现在可选候选里。
3. 选择 Copilot Fusion **Standard**，用同一批只读任务分别测试 Local-only、Cloud-only、Fusion，记录请求路由、时间、成功率与成本。
4. 检查模型类型与硬件内存约束；若本地模型不被 Fusion 支持，直接手动选择，而不是假定 BYOK 自动进入路由。

**适合什么场景：** Linux 本地编码模型、Qwen 小模型、低成本 AI Coding。**注意：** 官方说明即使推理在本地，Fusion 的路由决策仍在云端，不能视为离线或完全不上传上下文；Copilot App 的智能本地路由当前主要支持托管 Windows ML 模型。

### 技巧 3｜让 GitHub AI Scan 扫全仓后手工确认真实安全缺陷，再重新扫描关闭告警

**来源：** GitHub 官方，2026-10-28：[AI Scan 仓库扫描公告](https://github.blog/changelog/2026-10-28-ai-scan-for-repositories-in-public-preview/)。

**一句话结论：** AI Scan 已从 PR 变更扩展到整个仓库，能与 CodeQL 告警共同进入 Code Scanning，但修复后不能仅凭 PR 合并认为告警自动关闭。

**具体怎么做：**

1. 在受支持的 GitHub 仓库中由管理员开启 AI Scan for repositories，确认与现有 PR 扫描配置是两项独立开关。
2. 具有相应权限的人员进入 **Security → Code scanning → AI Scan**，对默认分支最新 Commit 发起一次完整扫描。
3. 对候选安全告警查看对应证据，独立复现、确认误报或用 PR 修复，避免 Agent 自动批准自己的修复。
4. 修复合并后重新运行 AI Scan，确认旧告警确已被复检关闭；对扫描预算、数据权限和重复告警做一次记录。

**适合什么场景：** 企业大型代码库与未被 CodeQL 完整覆盖的语言。**注意：** 公开预览的支持范围和计费条件不同；组织私有仓库要求相应 Code Security 权限，扫描消耗 Code Security AI credits。扫描报告是候选证据，不是安全认证。

---

## 经典论文回顾

### Continuous-Time Batch Estimation Using Temporal Basis Functions（ICRA 2012）

**作者：** Paul Furgale、Timothy D. Barfoot、Gabe Sibley。**发表：** ICRA 2012，第 2088—2095 页，DOI 10.1109/ICRA.2012.6225005。后续扩展的 IJRR 2015 期刊版本为 *Continuous-time batch trajectory estimation using temporal basis functions*，两篇不能混淆发表年份。

### 核心问题与算法思想

离散状态估计通常为每个关键时刻维护一个 Pose。如果使用高频 IMU、滚动快门相机、旋转 LiDAR，每一个测量采样时刻都新增状态将显著放大优化规模。连续时间估计改为求一个可在任意时刻评估的轨迹函数：

```text
相机 / 旋转 LiDAR / IMU 异步观测
                 ↓
连续时间运动模型与时间基函数
                 ↓
少量待优化的基函数系数
                 ↓
每条残差在测量真实时间戳求值
                 ↓
Batch MLE / MAP 轨迹与不确定性
```

可以写作 `T(t) = f(t; c_1, c_2, ...)`，其中 `c_i` 是轨迹的有限数量控制参数；时间基函数可以是 B 样条或其他有效参数化方式。估计的自由度数量取决于所选基函数、节点密度和实际运动带宽，而不是直接等于 IMU 样本数。

### 当年为何重要

它把“每个传感器需要统一采样时间”的直觉转化为“运动状态可以在任何时间戳查询”的估计设计。该思路对点云去畸变、滚动快门、IMU/Camera 联合标定、复杂机载旋转扫描具有持久价值。

但**连续时间参数化不等于拥有真实时间同步**。如果相机驱动产生了错误时间戳，样条只会在错误时间插值。节点太稀可能抹掉急转弯，太密则增大计算开销并导致弱观测方向不稳定。

### 今天仍然使用的思想与已被扩展的部分

现代连续时间 LiDAR/视觉/IMU 系统沿用时间基函数、在原始观测时间求值、联合估计。今天的 RESPLE2 与 2012 年经典方法形成清晰对照：

- 经典路线侧重 **Batch Continuous-Time Estimation**；
- RESPLE2 重点是 **非均匀样条＋递归 IKF 预测/更新＋可选全局样条修正**。

这使得新方法更直接面向在线多传感器状态估计，但不会自动消除数据关联、外参和可观测性问题。

### 传感器假设、复现路径与工程重新解读

经典工作需要有足够连续性且可观测的运动、合理噪声假设、正确传感器模型。原论文并非一套现成可部署的 ROS2 SLAM 系统，不应把后来社区代码当作其唯一官方工业实现。

在一个具有 IMU 与 LiDAR Point Time 的 Bag 中，按时间跨度抽取 10—30 秒高速运动数据，固定外参与真值，比较：

1. 最近时间戳离散 Pose；
2. 均匀时间 B 样条；
3. 非均匀时间 B 样条；

测量点云去畸变、轨迹 ATE/RPE、运动突变处插值误差、控制点数量和计算延迟。

**工程启发：** 先保证采样时间与外参准确，然后才谈连续时间模型复杂度。对前后两台 LiDAR 或 IMU 与 LiDAR 距离很远的机器人尤其如此。

**来源：** [ICRA 2012 原论文 DOI](https://doi.org/10.1109/ICRA.2012.6225005) · [IJRR 2015 扩展版](https://doi.org/10.1177/0278364915585860)。

---

## 今日结论

本期最值得立即采取行动的项目是 **RESPLE2：有真实 ROS2 代码、可运行数据集说明和多传感器配置**。它与现成 LIO 的 A/B 价值高于只看新的论文排行榜。特别需要关注它如何在高速运动下处理不同传感器原始时间戳、非均匀样条控制点和回环修正。

REACH 与 CPG-ENN 则展示两种不同的机器人控制分层：一个解决**任务净高决定运动模式**，一个解决**多步态之间共享可解释参数**。cuArms 进一步说明“Coding Agent 负责高层调度、经典规划器负责可行性”的分工比语言模型直接输出关节轨迹更可审查。

事件相机无人机研究通过不渲染 RGB 的模拟方法显著提高训练采样，再将 INT8 策略真正装上微型平台，建立了难得完整的训练—部署证据链；但 14/17 的真机飞行结果远不足以视为复杂环境的安全证明。

E0.5 提醒我们三维世界模型的价值在于描述**未来几何变化**，不能用画面质量代替动作安全。EffectWorld 提醒小型 Coding Agent 首先需要明白工具是什么、副作用是什么，避免越权和重复操作。

**总判断：控制、定位和 Agent 工程的高价值改进，应优先来自准确时间戳、可解释状态、真实工具契约和独立行为验收，而不是无条件增加模型层数、并行 Agent 或报告文档。**

---

## 最值得深入研究或尝试复现的方向

1. **RESPLE2 对 FAST-LIO/LIO-SAM：** 相同 ROS2 Bag、统一时间戳和坐标系，比较高动态 ATE、回环修正后连续性、P95 与代码集成成本。
2. **SG²SLAM：** 固定相机序列，检查联合地图优化是否真的减少几何漂移，避免仅以图像渲染指标论证 SLAM。
3. **REACH：** 仿真中增加通道净高约束，分别测试低姿态双足、爬行、双向过渡与中途失效恢复。
4. **CPG-ENN：** 在 Go2/MuJoCo 比较统一六参数策略和独立步态策略的切换冲击、侧向速度误差与地形泛化。
5. **cuArms：** 以双机械臂共享工位比较联合规划、先调度再规划、惰性冲突搜索，并记录总 Makespan 和求解 P99。
6. **事件相机无人机：** 使用作者官方仓库先复现渲染无关事件仿真，再独立测量量化前后网络延迟和真实事件统计。
7. **E0.5：** 对相同具身任务比较未来 RGB 与未来 3D 几何预测的真实物体交互收益与计算代价。
8. **EffectWorld：** 给现有 Agent Harness 的读、写、删除及 GitHub 工具声明幂等性与权限，统计重复副作用、误重试和每成功任务 Token。
9. **AI Coding 实操：** 小测试仓库试 `gh aw add-wizard`、Linux Copilot Fusion 本地路由、AI Scan 全仓复检，分别核查权限、流量与额外成本。

---

## 参考资料

**最新公开批次：** [arXiv Robotics](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/new)。

**SLAM / 状态估计：** [RESPLE2](https://arxiv.org/abs/2610.37602) · [RESPLE2 官方代码](https://github.com/ASIG-X/RESPLE2) · [SG²SLAM](https://arxiv.org/abs/2610.36312)。

**机器人控制与规划：** [REACH](https://arxiv.org/abs/2610.36546) · [REACH 项目](https://aislab-sustech.github.io/REACH/) · [CPG-ENN](https://arxiv.org/abs/2610.36537) · [cuArms](https://arxiv.org/abs/2610.36250) · [cuArms 项目](https://cuarms.github.io/)。

**无人机和具身模型：** [Rendering-Free Event Navigation](https://arxiv.org/abs/2610.37543) · [其官方代码](https://github.com/tudelft/rendering-free-event-nav) · [E0.5](https://arxiv.org/abs/2610.36011)。

**AI Coding：** [EffectWorld](https://arxiv.org/abs/2610.35981) · [GitHub Agentic Workflows GA](https://github.blog/changelog/2026-10-28-github-agentic-workflows-generally-available/) · [Copilot Fusion 本地模型](https://github.blog/changelog/2026-10-28-github-copilot-fusion-now-supports-selection-of-local-models/) · [GitHub AI Scan 全仓扫描](https://github.blog/changelog/2026-10-28-ai-scan-for-repositories-in-public-preview/)。

**经典论文：** [Furgale 等，ICRA 2012](https://doi.org/10.1109/ICRA.2012.6225005) · [IJRR 2015 扩展版](https://doi.org/10.1177/0278364915585860)。
