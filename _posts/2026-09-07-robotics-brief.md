---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-07"
date: 2026-09-07 09:00:00 +0800
description: "本期关注 SLAM 点云与 IMU 在线学习地形振动代价、商业移动平台定位精度实测、6DoF 无人机局部规划、机器人失败判定与轻量策略，以及 AI Coding 的不可满足任务拒绝和最小代码编辑。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-07

## 摘要

今天是周一，但截至本期检索时，arXiv Robotics 与 Software Engineering 的最新常规公开批次仍停留在 2026-09-04。严格最近 24 小时内不足 5 条高质量、未重复且能够完整核验的主动态，因此按任务规范扩展到最近 7 天。本期 8 条主动态的 v1 均提交于 2026-09-03 UTC，全部明确作为“时间回补”。近期 GPT-6 Astra、Gemini 3.8 Flash、Claude Fable 5.1 等旗舰模型已经在前几期覆盖，因此今天不重复用模型发布凑数。

今天与 SLAM / 自主导航最相关的信号，不是又一套里程计，而是两项更偏“产品指标”的工作。**RoughSense** 将 SLAM 点云中的局部几何粗糙度与 IMU 实际振动闭环起来：先用 RANSAC 平面残差得到地形振动代理，再用在线 Recursive Least Squares 根据机器人真实经过后的振动修正预测。它把“可通行”从几何碰撞进一步扩展到机械冲击、振动和设备寿命代价，尤其适合月面、矿井、碎石路等低速巡检场景。

另一篇移动机器人 NDE 定位基准则用约 6 μm 精度的激光跟踪仪，对 KUKA KMP-1500、KUKA KMR、MiR250、Boston Dynamics Spot 和 Clearpath Husky 做统一外部真值评测。静态定位中位误差从 8.2 mm 到 63.5 mm，动态 cross-track error 从 6.9 mm 到 112.1 mm；仅依赖轮速里程计的 Husky 在该协议下甚至无法完成可用标定。更重要的是，所有平台都无法仅靠底盘定位满足航空 NDE 常见的 0.2–1.0 mm 级要求。这说明“机器人导航定位够用”和“机器人能把测头准确送到计量位置”是完全不同的系统指标。

控制侧，**6D-DWA Omnicopter** 将经典 Dynamic Window Approach 扩展到六自由度速度搜索，通过局部地图 voxelization、球体机身近似和自适应 6D velocity sampling，把全向多旋翼局部规划稳定压进 0.2 s 控制循环。它还引入 Agile Mode，在未知障碍突然出现时动态改变 goal progress、clearance、heading/facing 权重。不过 centered obstacle 只有 41.4% 成功率，论文没有隐藏紧约束几何中的明显失败边界，这对工程选型反而很有价值。

机器人基础模型方面，本期更值得看的不是参数继续变大，而是两个“反 Scaling”结果。**MINERVA** 只用 0.54M 参数就在标准 LIBERO 四套任务上达到 95.1%，离报告的 LeRobot π0.5 只差 2.4 个百分点，却少约 7,700 倍参数；0.54M 模型在普通笔记本 CPU 上每个 action chunk 仅需 5–9 ms。更关键的是，一旦改变 task-ID 映射，标准 LIBERO 成功率几乎掉到随机水平；到了 LIBERO-Plus 视觉扰动，成功率也下降到 46–56%。这说明标准 LIBERO 的高分很大程度测到了任务记忆与固定视觉分布，而不完全是开放指令理解。

**GIFT** 则从另一个角度解释为什么大 VLM / World Model 的视觉表示不一定适合控制：表示可能“信息很多”，却保留了大量与动作无关的细节，同时遗漏真正决定可执行性的 geometry、affordance 和 goal region。GIFT 不改变 VLA/WAM 的动作头，而是在训练期对中间表示增加几何对齐、可供性预测和目标区域重建。它在 LIBERO-Plus 与 RoboCasa 上对多种不同动作建模架构都带来稳定提升，更值得把它理解成一种“让表示对控制任务负责”的训练原则。

AI Coding 侧，两篇工作都直接挑战“模型只要继续写代码就行”。**Refusing the Impossible** 构造 270 个故意不可满足的编程请求和 91 个匹配可解对照，12 个开源代码/推理模型在不可满足请求中约 60% 仍会生成没有现实依据的代码，仅 27% 会拒绝，而对可解对照的错误拒绝率却是 0%。真正需要补的可能不是更多修复能力，而是在写代码之前增加 package/API/约束是否真实可满足的 grounding gate。

**When Models Edit Too Much** 则说明“修对了”和“改得好”是两个指标。400 个 BigCodeBench 控制腐化任务拥有已知最小补丁，即使 GPT-5.5 级强模型也普遍 over-edit。仅增加 preservation instruction，就能将 excess Levenshtein 从 0.195 降到 0.131、额外 cognitive complexity 降低 26.6%，同时 Pass@1 还提高 2.3 个百分点。对真实 Coding Agent 来说，diff size、触达符号数量、无关重构和 reviewability 都应该成为独立 Gate，而不是测试通过以后就全部接受。

## 1. RoughSense：把 SLAM 地图从“能不能走”升级成“走过去会不会把机器人震坏”

**时间回补：arXiv v1 提交于 2026-09-03 11:54 UTC。**（[论文](https://arxiv.org/abs/2609.03720)）

### 为什么重要

传统 traversability map 大多聚焦坡度、台阶高度、障碍占据和地面法向。但对月面车、矿井巡检车、带精密传感器的移动平台来说，一条几何上完全可通过的碎石路，也可能因为持续振动造成定位退化、测量失真、机械件疲劳或任务中断。

RoughSense 的价值在于把“地形几何”和“机器人真实受到的机械响应”闭环起来：地图不再假设某种粗糙度对所有机器人都具有固定代价，而是让机器人在实际经过地形后在线校正自己对振动风险的理解。

### 算法模块

系统首先从 SLAM 输出的点云中切出局部 patch，并对每个 patch 使用 RANSAC 拟合局部平面。点到平面的残差分布被压缩成一个轻量 geometry-based vibration proxy：表面越难被单平面解释，潜在粗糙和激振越明显。

与此同时，IMU 持续测量机器人真正经历的振动。系统使用 Recursive Least Squares 在线更新“点云几何代理 → 实际振动”的映射，再将修正传播回 traversability cost map：

```text
SLAM Point Cloud
      ↓
Local Patch + RANSAC Plane
      ↓
Geometry Roughness Proxy
      ↓
Predicted Vibration
      ↑
Online RLS Correction ← IMU Measured Vibration
      ↓
Vibration-Aware Cost Map
```

这种设计很轻：几何部分只需要局部平面拟合，适应部分只是递归最小二乘，不依赖大网络，也无需把整个历史数据送回云端训练。

### 传感器与假设

主要输入只有 LiDAR/SLAM 点云与 IMU。它假设局部点云粗糙度和车辆振动之间存在可以在线校正的稳定关系，因此非常适合同一台机器人长期工作；但换轮胎、悬架、载荷、速度或传感器安装位置后，这个映射很可能发生变化。

更重要的是，振动并不只由地面决定。车速、转向、主动悬架、轮胎压力、轮地滑移都会影响 IMU 频谱。所以产品版本最好把速度与载荷也纳入状态，否则同一 patch 在 0.3 m/s 和 2 m/s 下会被错误地视为同一种风险。

### 实时性、鲁棒性与可复现性

论文明确以资源受限实时导航为目标，并在月面模拟环境 Lunalab、湖岸户外场地和地下矿井三个差异明显的场景评测。当前公开材料没有一个可以跨平台直接复用的统一 CPU 毫秒数，因此工程复现时更应该记录每秒 patch 数、RANSAC 预算、RLS 更新频率和 cost-map 刷新时间。

该方法最明显的优点是能够随机器人真实体验持续自适应；风险则是 IMU 测到的结构共振或驱动振动也可能被错误归因给地面。应保留异常频带过滤与机械故障诊断，避免把“车自身坏了”学成“这块地更颠”。

### 适合谁关注

月面/火星车、矿井、煤场、碎石路巡检、长距离轮式机器人，以及搭载精密测量设备、不只关心碰撞而还关心平台振动的系统。

### 工程落地启发

现有 16 线 / MID360 建图系统完全可以先做一个 RoughSense-lite：对 voxel/surfel 地图增加 `roughness / support_count / observed_vibration / speed_bin`，局部规划的代价从：

```text
obstacle + slope
```

升级成：

```text
obstacle + slope + slip risk + vibration cost + localization health
```

对于工业巡检，这比单纯追求最短路径更接近真实设备寿命和测量质量。

## 2. 移动平台精密 NDE 基准：导航“定位准”不代表计量任务“位置准”

**时间回补：arXiv v1 提交于 2026-09-03 13:02 UTC。**（[论文](https://arxiv.org/abs/2609.03794)）

### 为什么重要

很多工业移动机器人项目在导航阶段看到厘米级地图轨迹，就自然推断“机械臂或 NDE 探头也能到厘米级甚至毫米级”。这篇工作用统一外部基准说明，这个推断非常危险。

作者用约 6 μm 级激光跟踪仪作为 ground truth，对五种商业移动平台进行同一协议下的静态定位与分段轨迹测试：KUKA KMP-1500、KUKA KMR、MiR250、Boston Dynamics Spot 和 Clearpath Husky。

### 评测与标定模块

为了避免“每台机器人各用一套自家坐标系，最终数字不可比”，论文设计 coupled multi-corner calibration，同时估计 laser-to-robot transformation 与 reflector offsets。主要估计用全部姿态上的 ordinary least squares，robust estimation 只作为 gross blunder 检查。

这套协议把问题拆成三个层次：

```text
机器人内部 Localization
        ↓
外部坐标系 Calibration
        ↓
Static Position Accuracy
        +
Dynamic Cross-Track Error
```

这样可以区分“系统本身漂”“外参没标好”和“底盘跟踪误差”。

### 结果

静态定位中位误差从 KMP-1500 的 **8.2 mm** 到 Spot 的 **63.5 mm**；只依赖 wheel odometry 的 Husky 在该协议下无法获得可用标定。动态路径 cross-track error 从 **6.9 mm** 到 **112.1 mm**。

作者还观察到，accuracy 与 calibratability 整体跟随平台所使用的 localization capability：从较新的 LiDAR SLAM 到 map-free visual odometry / wheel odometry，表现明显分层。

最关键的结论是：**没有一个底盘仅靠自身定位就达到 0.2–1.0 mm 的航空 NDE 位置容差。** 最好的平台仍需要大约一个数量级的附加 sensing 改善，最差接近两个数量级。

### 传感器假设与工程风险

这不是在给五个品牌做绝对排名。平台配置、地图质量、地面条件、软件版本和运动速度都会影响结果。Spot 的优势本来也不是静态 XY 高精度定位，而是通过复杂地形；KMP 的场景定位也不同。

真正可迁移的结论是：对精密任务必须建立**任务端独立真值链**，不能用 SLAM ATE 或厂商导航指标代替末端测量误差。

### 适合谁关注

航空 NDE、移动机械臂测量、打磨/喷涂、机器人巡检取证、需要重复回到同一个物理测点的项目。

### 工程落地启发

如果任务要求毫米甚至亚毫米，建议将系统拆成：

```text
SLAM / AMR Localization
        ↓
厘米级到位
        ↓
Local Metrology Layer
视觉靶标 / 激光跟踪 / 结构光 / 反光标志
        ↓
机械臂局部精定位
```

这也解释了为什么很多现场项目用 RTK、反光标志或固定工装不是“技术落后”，而是在给全局 SLAM 无法承担的计量任务补一个局部高精度坐标系。

## 3. 6D-DWA Omnicopter：经典 Dynamic Window 也能扩展到全向六自由度飞行

**时间回补：arXiv v1 提交于 2026-09-03 10:25 UTC；ICUAS 2026 接收。**（[论文](https://arxiv.org/abs/2609.03630)）

### 为什么重要

全向多旋翼与普通 quadrotor 的差别是，机体不必通过倾斜才能产生横向力，因此“移动方向”和“朝向”可以更自由地解耦。传统 2D DWA 只搜索平面线速度与 yaw rate，无法充分利用这种 6DoF actuation。

这项工作把 DWA 直接扩展到 6D local velocity search，同时通过一系列工程近似把计算量压到在线可用范围。

### 算法模块

实时性主要来自三点：局部障碍地图先 voxelization；机体几何用紧凑球体近似；6D velocity space 不做均匀暴力网格，而采用 adaptive velocity sampling。

对每组短时速度候选，系统 rollout 未来运动并综合评价：

```text
Goal Progress
+ Obstacle Clearance
+ Path / Waypoint Tracking
+ Heading / Facing
+ Feasibility
```

论文还增加 **Agile Mode**：当未知障碍突然进入局部地图时，动态调整 progress、clearance 和 heading/facing 权重，让飞行器优先完成躲避，而不是死守原来的朝向要求。

### 动力学与几何假设

为了在 0.2 s 内完成循环，机身几何被简化成球体，局部 rollout 也不是完整高保真 aerodynamics。这适合“快速局部可行性筛选”，但复杂细长机身、外挂机械臂或靠墙操作时，球体 envelope 会过度保守或漏掉局部碰撞风险。

6D-DWA 本质仍是局部方法。它需要上游 global path / waypoint，并可能陷入局部几何困境。

### 实时性与结果

论文报告 planner 稳定运行在 **0.2 s control loop** 内；密集 waypoint global path 的平均 cross-track error 小于 **0.1 m**，平均 heading error 约 **13°**。

未知障碍实验非常值得看：off-centre obstacle 成功率 **79.3%**，但 centred obstacle 只有 **41.4%**。这表明 adaptive weighting 能提高反应性，但在高度受限的正面死局中，局部速度搜索仍然缺少更强的拓扑/长期预测能力。

### 鲁棒性、可复现性与风险

当前主要是仿真结果，并非长期真机飞行证明。上真实 UAV 前还需要加入 sensor latency、state-estimation covariance、minimum braking distance、thrust reserve 和安全 abort 机制。

### 适合谁关注

全向多旋翼、室内无人机、狭窄空间飞行、需要同时控制位置与朝向的 aerial manipulation。

### 工程落地启发

对于现有 UAV 软件栈，最值得复制的是职责分层：

```text
Global / Topological Planner
        ↓
6D Local Velocity Search
        ↓
Trajectory / Dynamics Safety Gate
        ↓
Flight Controller
```

不要让 DWA 同时承担全局逃逸和动力学安全认证。

## 4. FailBench：VLM 当机器人任务“裁判”，接触任务里仍接近抛硬币

**时间回补：arXiv v1 提交于 2026-09-03 09:58 UTC。**（[论文](https://arxiv.org/abs/2609.03611)）

### 为什么重要

机器人 RL、自动数据清洗和长期 autonomous recovery 越来越依赖一个关键组件：自动判断“这次到底成功没有”。很多系统默认用 VLM 看最后几帧视频当 reward / evaluator，但如果 judge 本身经常错，后面的 RL、DAgger、数据筛选都会被系统性污染。

FailBench 专门把 failure detection 从主策略里拆出来评测。

### 数据与评测

benchmark 收集 **2,197 个 manipulation attempts**，来自 14 个公开来源，其中 12 个真实机器人、2 个仿真；75% 的失败是数据里自然发生的，而不是为了 benchmark 人工制造。作者评测 13 个 VLM-based detector。

最佳模型的 mean balanced accuracy 也只有 **0.77**。当成功与否能够通过明显 object motion 判断时，模型接近饱和；但在插接、装配等依赖细微接触证据的任务中，balanced accuracy 会跌到 **0.60 以下**，接近随机水平。

更值得警惕的是：在视觉证据模糊时，模型系统性偏向回答“成功”。单纯提高 reasoning effort 并不能消除这种偏差。

### 一个低成本有效改进

不重新训练模型，只先定位 outcome-relevant region 并裁剪输入，就能让最强 detector 提高 **2.4 个百分点**。

这说明 failure judge 的瓶颈不一定是“大模型还不够聪明”，而可能是原始多相机画面中真正关键的接触区域占比太小。

### 鲁棒性与工程风险

VLM evaluator 不是传感器真值。尤其接触任务中，应该结合：

```text
Vision Outcome
+ Gripper / Joint State
+ Force / Torque / Current
+ Task-State Predicate
+ Retry Observation
```

再形成成功判定。

如果 evaluator 用于自动 RL reward，更应该保存 uncertainty；模糊样本宁可进入人工复核，也不要把高置信错误奖励灌入策略。

### 适合谁关注

VLA 自动评测、robot data engine、DAgger、在线 RL、自动失败恢复和 Real-to-Sim 策略回归。

### 工程落地启发

将 robot outcome evaluator 从“一次 VLM Yes/No”升级成 typed evidence：

```text
OutcomeEvidence {
  visual_state
  contact_state
  object_pose_change
  task_predicates
  confidence
  evidence_timestamp
}
```

失败判定本身也应该有 regression suite。

## 5. MINERVA：0.54M 参数已经能把标准 LIBERO 做到 95.1%，这说明了什么？

**时间回补：arXiv v1 提交于 2026-09-03 11:51 UTC。**（[论文](https://arxiv.org/abs/2609.03715)）

### 为什么重要

标准 LIBERO 已经被大量十亿参数 VLA 当成核心 benchmark。如果一个只有几十万参数的视觉动作策略也能接近这些大模型，那么“LIBERO 高分”究竟在测试通用机器人智能，还是在测试一组相对固定的任务分布，就必须重新审视。

MINERVA 的定位非常明确：不是追求通用 VLA，而是测 **LIBERO 的 task-specific capacity floor**。

### 模型与结果

一个只有 **0.54M 参数**的策略，在四套标准 LIBERO、2,000 个 rollout 上达到 **95.1%** 平均成功率，只比报告的 LeRobot π0.5 低 2.4 个百分点，却少约 **7,700× 参数**。

作者发现性能在约 1M 参数附近已经饱和，低于 0.25M 才明显崩塌。大量架构、训练和推理 sweep 中，只有 **action-chunk length** 与 **vision capacity** 稳定超过约 ±1-point 的随机种子波动。

Flow Matching 在三个种子下相对直接 L1 regression 没有可检测优势，后者 GPU 推理最高快 **3.8×**。

### Benchmark 暴露出的更大问题

最有价值的实验是 task-ID permutation：只改变 task-ID 与任务之间的对应关系，成功率就接近随机。这意味着标准 LIBERO 的语言条件很大程度在充当“选择已记忆任务”的索引，而不是模型真的需要对自然语言进行强组合推理。

同一 recipe 在 LIBERO-90 还能达到 **94.6%**；但到了 LIBERO-Plus 的环境扰动，只有 **46–56%**，对 photometric shift 几乎没有鲁棒性。

### 实时性

0.54M 模型在普通 laptop CPU 上每个 action chunk 仅需 **5–9 ms**，每个 control step 都可以重新规划；作者报告相对 SmolVLA 快 113×、相对 π0.5 快约 1,400×，无需 GPU。

### 工程风险与适合谁关注

它不是在证明“大 VLA 没用”。开放词汇、跨任务迁移、复杂语言、长时推理和跨 embodiment 仍需要更大模型。它证明的是：**不要用标准 LIBERO 单独为大模型的复杂度买单。**

特别适合做边缘机器人策略、蒸馏、小模型控制器和 benchmark 设计的团队关注。

### 工程落地启发

真实产品最好同时跑两套指标：

```text
ID Task Success / Latency
          +
OOD Visual / Geometry / Language Robustness
```

如果小模型在你的固定交付任务上已经 95%，就把大模型放在低频语义规划和异常处理层，而不是每 20 ms 都调用它。

## 6. GIFT：视觉表示“懂得很多”，不等于它知道什么对动作真正重要

**时间回补：arXiv v1 提交于 2026-09-03 17:59 UTC。**（[论文](https://arxiv.org/abs/2609.04193)，[项目页](https://openphoenix-team.github.io/GIFT-pages)）

### 为什么重要

VLM 预训练和 World Model 确实能产生很丰富的视觉特征，但丰富不等于可控。表示可能保留纹理、背景和语义细节，却没有把“哪里能动、怎么动、目标区域在哪里”编码成对 action head 足够直接的结构。

作者把这个问题称为 **action-sufficiency gap**。

### 算法模块

GIFT 不强行统一所有 VLA/WAM 的动作形式，而是在训练期约束中间表示必须保留三类控制相关结构：

```text
Geometry Alignment
→ 保留运动可行性与空间结构

Affordance Prediction
→ 保留指令相关实体与可交互性

Goal-Region Reconstruction
→ 将语言目标绑定到任务相关区域
```

同一训练原则分别实例化到 VLA、direct-action WAM 和 inverse-dynamics WAM，原来的 action formulation 不需要重写。

### 结果

LIBERO-Plus 零样本迁移中，GIFT-VLA / GIFT-WAM-Fast / GIFT-WAM-IDM 分别达到 **79.6% / 72.6% / 87.8%**，比对应 baseline 提高 **4.6 / 12.6 / 5.2 个百分点**。

RoboCasa 中分别达到 **61.4% / 83.6% / 82.3%**，对应提升 **12.6 / 9.0 / 8.4 个百分点**。增益在 articulated-object 与高精度真实操作中尤其明显。

### 传感器、可复现性与风险

GIFT 的优势是训练期结构监督可以被移除，部署时不需要额外大模块。但训练时必须获得或构造 geometry、affordance 和 goal-region supervision；如果这些辅助标签质量差，同样可能把错误结构固化进表示。

### 适合谁关注

正在预训练 VLA/WAM backbone、希望增强 OOD robustness，却不想继续单纯扩大参数或数据量的团队。

### 工程落地启发

内部 representation benchmark 不要只做 linear probe 的 object/category accuracy。更应该增加：

```text
reachability probe
contact / affordance probe
goal-region localization
action recoverability
```

如果一个视觉 backbone 对这些控制相关变量不可解码，那么它即使语义能力很强，也未必是好的机器人 action backbone。

## 7. Refusing the Impossible：Coding Agent 在写代码之前需要先判断“这个任务是否可能”

**时间回补：arXiv v1 提交于 2026-09-03 01:50 UTC。**（[论文](https://arxiv.org/abs/2609.03267)）

### 突破性工程价值

代码模型常见的失败并不是语法 bug，而是非常流畅地实现一个现实中根本不存在的东西：导入不存在的包、调用伪造 API，甚至宣称实现数学上被证明不可能的算法。

这篇论文把这种情况定义为 **ungrounded generation**，并和“在真实可行任务上写错代码”的普通 bug 分开。

### Benchmark 与结果

作者建立三维 taxonomy：groundedness（普适不可能 vs 生态/事实伪造）、manifestation level（syntactic / semantic / factual）以及行为严重度。

对抗集合包含 **270 个故意不可满足请求**，覆盖 6 种语言、24 个子类；另外配对 **91 个可解对照**。12 个开源 code/reasoning model 共得到 4,332 个评审响应。

结果很直接：

- 不可满足请求中约 **60%** 仍产生无依据代码；
- 只有 **27%** 会正确拒绝；
- 对匹配可解请求的错误拒绝率为 **0%**。

这说明模型不是“太爱拒绝”，恰恰相反：它明显过度倾向于给出一个看起来完成任务的实现。

### 是否适合真实研发流程

非常适合。Coding Agent 在进入写文件阶段前，应增加一个 grounding / feasibility preflight：

```text
Requirement
   ↓
Package / API Existence
Version Compatibility
Constraint Satisfiability
Platform Capability
   ↓
Feasible → Plan / Code
Impossible / Ambiguous → Refuse or Escalate
```

### 权限、安全与可验证性风险

在有 shell / network 权限的 Agent 中，幻觉不存在的依赖并不只是浪费时间。模型可能为了“让任务成立”去安装可疑同名包、搜索未知二进制或修改系统环境。

因此 package install、外部下载和新增 registry source 都应该受独立 policy 管理，不能由“任务看起来需要它”自动获得授权。

### 工程落地启发

把“找不到 API”从普通 retry loop 中移出来。连续两三次无法在官方文档、代码库或 package registry 中证明某个依赖存在时，Agent 应进入 `GROUNDING_FAILED` 状态，而不是继续编造下一种拼写。

## 8. When Models Edit Too Much：最小改动应该成为 Coding Agent 的正式质量指标

**时间回补：arXiv v1 提交于 2026-09-03 16:36 UTC；EMNLP 2026 Main。**（[论文](https://arxiv.org/abs/2609.04061)）

### 突破性工程价值

真实软件维护中，一个能通过测试但顺手重写半个函数的 Patch，通常比只改两行的 Patch 更难 review、更难回滚，也更容易引入隐藏回归。

论文专门研究 **over-editing**：模型修改超过修复 bug 所必需的范围。

### 评测设计

作者从 BigCodeBench 选取 400 个问题，在 reference solution 上注入可控 AST-level corruption，因此每个任务都拥有一个已知最小修复。

这样可以同时测：

```text
Correctness
+ Excess Edit Distance
+ Structural Preservation
+ Added Cognitive Complexity
```

而不是只有 Pass@1。

### 结果

即使强模型也普遍出现过度编辑。简单增加 preservation instruction 后：

- average excess Levenshtein：**0.195 → 0.131**；
- added cognitive complexity：降低 **26.6%**；
- Pass@1：反而提高 **2.3 个百分点**。

更大的 reasoning budget 或模型尺寸并不会自动带来更小的 patch。

后训练方面，SFT 容易过拟合已经见过的 corruption pattern，而 RL 在 OOD edit-fidelity 与性能保持之间表现出更好的折中。

### 是否适合真实研发流程

非常适合任何自动修 bug / PR Agent。建议在 CI 中加入独立的 Patch Fidelity Gate：

```text
changed_files
changed_symbols
AST edit count
unrelated formatting
complexity delta
public API delta
```

如果功能测试全过，但触达范围远超 issue 预期，就转人工 review 或要求 Agent 重新最小化补丁。

### 权限与风险

最小 patch 也不是绝对目标。安全漏洞、架构迁移或 API 设计错误可能必须做更大的改动。因此 diff budget 应由任务类型决定，不能变成“越少越好”的机械奖励。

### 工程落地启发

Agent 最终 verifier 可以明确分成：

```text
Functional Correctness
        ↓
Constraint / Security Gate
        ↓
Minimality / Reviewability
        ↓
Merge Candidate
```

这能显著降低“测试绿了，但 reviewer 还要花半小时弄清模型为什么顺手改了其他代码”的维护成本。

## 经典论文回顾

### Timed Elastic Band：为什么今天 ROS 移动机器人局部规划仍然离不开“路径 + 时间”联合优化

Christoph Rösmann、Wendelin Feiten、Thomas Wösch、Frank Hoffmann 和 Torsten Bertram 的 **Trajectory modification considering dynamic constraints of autonomous robots** 发表于 **ROBOTIK 2012**。它形成了后来广泛使用的 Timed Elastic Band（TEB）局部规划思想，并发展成 ROS `teb_local_planner`。（[TU Dortmund 项目页](https://rst.etit.tu-dortmund.de/en/research/robotics/online-trajectory-optimization-based-on-timed-elastic-ban/)，[代码](https://github.com/rst-tu-dortmund/teb_local_planner)）

### 核心问题

经典 Elastic Band 可以把全局规划器给出的离散路径像橡皮筋一样推离障碍，但它本质还是几何路径，没有显式回答：

```text
这一段什么时候到？
速度是不是过快？
加速度是否超过底盘能力？
拐弯曲率能不能实现？
```

TEB 的关键变化是在相邻 pose 之间同时加入时间间隔，让局部路径直接变成时空轨迹：

```text
Pose_0 -- Δt_0 --> Pose_1 -- Δt_1 --> Pose_2 ...
```

于是速度与加速度约束可以由 `Pose difference / Δt` 自然构造出来。

### 算法模块与关键数学思想

TEB 从 global planner 提供的初始 waypoint path 出发，将 pose 与 time interval 作为优化变量，通过 scalarized multi-objective optimization 同时考虑：

```text
Trajectory Execution Time
+ Obstacle Clearance
+ Intermediate Waypoints
+ Velocity Limits
+ Acceleration Limits
+ Kinematic / Geometric Constraints
```

绝大多数目标只连接少量相邻状态，因此问题天然形成稀疏图结构。后续实现使用 g2o/hypergraph 组织这些局部约束，使在线非线性优化能够在移动机器人控制循环中工作。

### 传感器与动力学假设

TEB 自身不是感知器，它消费 costmap / obstacle model 和 global path。官方 ROS 实现支持 differential drive 与 Ackermann / car-like kinematics。

它对 obstacle state、robot footprint 和 localization 的质量高度敏感。地图里一个错误障碍会直接扭曲轨迹；定位突然跳变也会让整条 band 在局部重新寻找极小值。

### 当年为什么重要

它把“局部路径规划”和“速度规划”从两个相对割裂的步骤统一成一个时空优化问题，同时保持足够稀疏，能在线求解。对于 ROS 经典导航栈，这使底盘约束能够真正进入 local planner，而不是先生成几何曲线，再由 controller 尽力跟踪。

### 今天仍然在使用的思想

TEB 最值得保留的不是某套 g2o 参数，而是三点：

1. **时间必须是一等优化变量。** 一条空间上短的路径可能因为曲率和制动要求而执行得更慢。
2. **全局拓扑与局部动力学应该分层。** 全局 planner 决定从哪边绕，TEB 负责在当前拓扑内把轨迹变成可执行形状。
3. **局部约束构成的稀疏图非常适合在线非线性优化。** 这个思想今天仍出现在 factor graph、MPC 和 trajectory optimization 中。

### 已被后续替代的部分

经典 TEB 对未来动态障碍的预测能力有限，代价权重也高度依赖工程调参；它仍是局部非凸优化器，可能被局部极小值困住。后来的 TEB 扩展增加多拓扑候选，现代系统则大量使用 MPC、MPPI、ESDF、可达性、安全 CBF 和学习式局部规划。

但这些方法并没有让 TEB 的“space-time joint optimization”过时。

### 公开代码与可复现性

`rst-tu-dortmund/teb_local_planner` 仍是非常完整的经典实现，BSD-3-Clause License，ROS 生态中有大量配置与案例。其 README 明确说明在线优化目标包括执行时间、避障和 kinodynamic constraints。

### 对当前工程项目的重新解读

对于现有 LIO-SAM + 局部导航，TEB 很适合作为一个“基准线”而不是最终答案：

```text
LIO / Local Cost Map
       ↓
Global Path / Topology
       ↓
TEB / MPC / MPPI A-B Test
       ↓
Independent Safety Gate
       ↓
Controller
```

尤其在楼梯前、狭窄走廊和转弯平台，建议将 TEB 的 `Δt`、速度约束和 footprint 几何显式保留。真正需要现代化的部分，则是给它增加 localization uncertainty、动态障碍预测、弱方向定位健康度和可恢复性约束。

## 今日结论

今天没有新的“某某 LIO SOTA”值得为了数量强行报道，但两项导航相关工作反而更接近真实产品问题。RoughSense 说明地图代价不能只看空间几何；移动平台 NDE 基准则说明 SLAM 的厘米级定位指标无法直接替代任务端的毫米级计量要求。一个成熟机器人系统应该同时拥有：

```text
Localization Accuracy
Traversability / Vibration Cost
Task-End Metrology Accuracy
```

三套不同指标。

6D-DWA 和经典 TEB 放在一起看也很有意思。DWA 是“在当前可达速度窗口中快速搜动作”，TEB 是“对一条带时间的局部轨迹做稀疏非线性优化”。今天的 MPPI / MPC / diffusion planner 技术更复杂，但产品层仍然绕不开同一个职责划分：全局拓扑、局部动力学、轨迹安全和低层控制不应该由一个算法同时承担。

机器人学习侧最清晰的信号是：**Benchmark 高分和真正的部署能力必须拆开。** MINERVA 用 0.54M 参数做出 95.1% LIBERO，说明标准任务存在非常低的 task-specific capacity floor；GIFT 又从表示层说明，真正决定 OOD 控制性能的是 geometry / affordance / goal 等 action-oriented structure，而不只是 backbone 参数量。

FailBench 补充了另一层：即使策略本身很强，自动判断“任务是否真的成功”仍然非常困难，尤其接触装配场景中 VLM judge 接近随机。如果未来机器人系统依赖自动 RL、自动采集和自动恢复，那么 Outcome Verification 会和 Policy 本身一样重要。

AI Coding 方向同样在从“生成能力”转向“生成之前与生成之后的 Gate”。不可满足任务需要在编码前被识别；可满足任务修完以后，不仅要测试通过，还要控制 diff、复杂度和无关改动。更合理的生产链会逐渐变成：

```text
Requirement Grounding
        ↓
Feasibility Gate
        ↓
Plan / Code
        ↓
Functional + Constraint Tests
        ↓
Minimality / Reviewability Gate
        ↓
Merge
```

## 最值得深入研究或尝试复现的方向

1. **给现有点云地图增加“振动代价层”。** 从 16 线 / MID360 的局部点云提取平面残差、roughness 与 support count，同时按速度分桶记录 IMU 振动；先离线验证几何粗糙度和实际机械振动的相关性，再决定是否进入 local planner cost。

2. **建立机器人“导航精度 vs 任务精度”双真值体系。** 对需要重复到达固定设备的巡检点，额外布置 AprilTag、反光标志或局部精密定位基准，统计 SLAM pose error、底盘 cross-track error 和最终测头/相机 position error，避免只看地图轨迹。

3. **做一个 MINERVA-style 小策略基线。** 对固定的公司内部操作任务，用 0.5M–5M 参数小模型先跑成功率与 CPU latency，再与大型 VLA 比较 OOD 扰动和长时语义任务。只有大模型确实带来可测泛化收益时，才让它进入高频执行链。

4. **Coding Agent 增加 Grounding + Minimal Patch 两个 Gate。** 开始写代码前验证依赖/API/约束是否真实存在；代码完成后检查 changed symbols、AST diff、复杂度变化和无关格式化。两层都由 Agent 之外的 verifier 产生证据。

## 参考资料

- [RoughSense](https://arxiv.org/abs/2609.03720)
- [移动机器人精密 NDE 定位精度对比](https://arxiv.org/abs/2609.03794)
- [Local Path Planning and Obstacle Avoidance for an Omnicopter Platform](https://arxiv.org/abs/2609.03630)
- [FailBench](https://arxiv.org/abs/2609.03611)
- [MINERVA](https://arxiv.org/abs/2609.03715)
- [GIFT](https://arxiv.org/abs/2609.04193)
- [GIFT 项目页](https://openphoenix-team.github.io/GIFT-pages)
- [Refusing the Impossible](https://arxiv.org/abs/2609.03267)
- [When Models Edit Too Much](https://arxiv.org/abs/2609.04061)
- [TEB 官方项目说明](https://rst.etit.tu-dortmund.de/en/research/robotics/online-trajectory-optimization-based-on-timed-elastic-ban/)
- [teb_local_planner](https://github.com/rst-tu-dortmund/teb_local_planner)
