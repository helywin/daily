---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-14"
date: 2026-11-14 09:00:00 +0800
description: "QVS-LIVO多相机自适应融合、CT-SGAL-LIO连续时间平滑、EMS-Nav巡检语义导航、VINE外置相机、GenGenIK、FORGE力控、Alloy多材料仿真和人群MPC；Memory-TCG、Codex测试与MCP工程实践。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-14

## 摘要

**日期：2026-11-14，Asia/Shanghai，星期六；检索基准：约 08:55。**

arXiv 最新可核实的常规公开批次为 **2026-11-13（星期五）**：[cs.RO 新论文](https://arxiv.org/list/cs.RO/new) 共 164 条，**新提交 91 条**；[cs.SE 新论文](https://arxiv.org/list/cs.SE/new) 共 86 条，**新提交 39 条**。总数还包含 cross-list 与 replacement，不能全部当作第一次投稿。主动态优先检查最近 24 小时，并扩展至最近 7 天；8 篇的原始 v1 分别于 11 月 11—12 日 UTC 提交，均是**时间回补**，不能把今天当首发日。

正式选题前读取了 [任务规范](https://github.com/helywin/daily/blob/master/robotics-brief-task-spec.md) 与 [历史覆盖索引](https://github.com/helywin/daily/blob/master/robotics-brief-covered-items.md)，针对规范标题、arXiv ID、DOI、GitHub 和项目主页联合去重。原索引有 **1,334 条**；下文主动态和组件均未以同一原始工作在历史索引中登记。

**今日最值得投入：** ① QVS-LIVO 是已经有 ROS2 Humble/C++ 实际代码与四路相机选择逻辑的多传感器工程；② CT-SGAL-LIO 通过固定滞后插值平滑离散 LIO 位姿，对控制器需要的速度连续性很有针对性；③ Alloy 提供 Python 可运行的多材料物理引擎，并将仿真操作以 MCP 暴露给 Codex；④ Memory-TCG 的真实开源脚本可检验长期 Agent 在压缩记忆时是否丢失当前决策。

本期区分**论文作者指标、已核实项目源代码与未实际运行的工程入口**。所有量化结果不得直接外推到既有 RK3588、RTX 5070、ROS2 Humble 或真机硬件。

---

## 1. QVS-LIVO RiskMap：多相机不必全部参与滤波，选择真正有信息增益的一路

**时间回补｜v1 2026-11-12 02:51 UTC｜arXiv:2611.16205**

### 为什么重要

FAST-LIO 或 FAST-LIVO 在几何退化的长走廊、越野路段上，可能需要视觉提供额外约束，但摄像头也会遇到曝光、模糊、失帧与时间戳偏差。将所有相机的光度残差无条件加入同一个状态更新，既增加计算又可能污染已经比较可靠的 LIO 后验。QVS-LIVO 的原则是**全相机只读预跟踪、状态更新只放行至多一路、语义建图另行利用全部可用视角**。

### 算法模块与传感器假设

~~~text
LiDAR + IMU → 共享 LIO 后验
                    │
四相机 → 分通道只读跟踪、健康分数、几何互补性
                    ↓
              健康记忆 + 迟滞选择
                    ↓
        至多一个视觉通道进行光度校正
                    ↓
       校正不可靠 → 保留原 LIO 后验
各相机语义结果 → 局部 BEV / 全局 2.5D 风险地图（论文完整系统）
~~~

需要正确的相机内外参、传感器真实时间戳、已知雷达点格式。该方法不是自动时钟校准：随附相机 Gate 保留原始时间戳，不会修正硬件时钟漂移。

### 论文结果、实时性和鲁棒性

作者在两条越野实测序列报告水平位置 RMSE 为 **0.910 m、1.664 m**；几何退化长路线比 FAST-LIO2 误差降低 **43.3%**。12 种相机故障配置包含黑帧、丢帧、60 ms 时间偏移，仍保持完整轨迹，误差范围 1.54–2.23 m。Jetson AGX Orin 上局部地图 9.94 Hz、全局地图 2.00 Hz，局部地图延迟中位数 32.4 ms。这些是论文指定硬件与任务，不能等同于厘米级定位或整个控制系统的 P99。

### 已发布源码与最小复现

**[zihanPan-HIT/QVS-LIVO 官方源码](https://github.com/zihanPan-HIT/QVS-LIVO)** 已核实含 C++17、ROS2 Humble、定位主线、四路相机选择、接口和测试；遵循 GPLv2/第三方组件各自许可。作者明确写明**语义分割、2.5D 风险地图、网页地图、RViz 配置与实验数据不在本次公开仓库中**，不能将论文的完整 RiskMap 视为已经全部开源。

~~~bash
git clone https://github.com/zihanPan-HIT/QVS-LIVO.git
cd QVS-LIVO
source /opt/ros/humble/setup.bash
colcon build --parallel-workers 2 --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DLIVO_BUILD_EXPERIMENTAL_SHADOWS=OFF
source install/setup.bash
colcon test --packages-select livo_core
colcon test-result --verbose
~~~

运行前应修改仓库提供的 YAML 标定，别照搬 96 线 AIRY/四相机默认数据。Distrobox Ubuntu Humble 可用于隔离依赖，但没有实测确认该工程能在所有容器环境中成功构建。

### 适合谁关注 / 落地启发

适合多激光+多相机长走廊与室外巡检。已有 FAST-LIO、三雷达融合系统可先把“相机健康评估和是否允许更新”作为 Sidecar，在当前位姿上做 Shadow Mode，测 ATE/RPE、误校正接受率、相机故障恢复时间和 CPU P95，而不是一上来替换现有 LIO。

来源：[论文](https://arxiv.org/abs/2611.16205) · [完整 GitHub README](https://github.com/zihanPan-HIT/QVS-LIVO)。

---

## 2. CT-SGAL-LIO：不替换现有 LIO，在输出端以因果固定滞后减少位姿跳变

**时间回补｜v1 2026-11-12 15:07 UTC｜arXiv:2611.16918**

### 为什么重要

离散滤波式 LIO 在 IMU 高频传播和雷达观测校正之间反复切换，长期 ATE 可能很好，但位姿流的速度、短时相对运动可能出现小幅突变。对轮式/轮足控制、视觉融合和跟随规划而言，**局部位姿连续性**与全球轨迹一致性是两种不同指标。

CT-SGAL-LIO 并不重新优化全部原始点云或 IMU，而是直接在已有 SGal(3) 估计器后验投影位姿上拟合短窗口三次轨迹，以很小的固定延时查询已观测区间：**做插值，而不是向未来外推**。

### 算法模块和假设

~~~text
离散 LIO 的高频 posterior pose
             ↓
滑动窗口：最近若干姿态
             ↓
有界三次连续时间轨迹拟合
             ↓
以固定 lag 查询时刻 t-δ 的位姿
             ↓
下游运动估计、图优化或控制观测
~~~

该模块的代价是**额外固有延时**。如果控制器需要最新实时状态，必须区分延后高质量轨迹与当前时刻 IMU 外推姿态，不能把 t-δ 的输出误当作 t 时刻状态。

### 作者结果

17 条 GRAND-TOUR、MCD、GEODE 序列上，作者报告相对运动误差 RTE 在 GRAND-TOUR 最高减少约 70%，GEODE 七条序列减少 **9.9–51.1%**。19.5 分钟 R-Campus 上，后验跳变降低 **85.4%**，轨迹首尾间隙只变化 4.7 mm。以上不是全数据集 ATE 同步下降 70% 的承诺。

### 可复现性、风险与工程建议

作者明确称**计划发布源码**，截至本次核验没有将其标记为可直接拉取工程。可先自行实现 SGal(3)/SE(3) 输出位姿短窗口 spline 对照，在同一 Bag 上统计局部 RTE、旋转速度抖动、轨迹闭合误差、固定 lag 与 P99。最好与现有 LIO 的点云传播和控制回路分开评估。

适合已有 LIO-SAM/FAST-LIO、三雷达定位、下游足步/速度控制器的系统。优先**不动稳定滤波内核，只处理后验轨迹**。

来源：[CT-SGAL-LIO 原论文](https://arxiv.org/abs/2611.16918)。

---

## 3. EMS-Nav：面向配电室的对象、房间、区域、实例多尺度语义导航

**时间回补｜v1 2026-11-11 15:09 UTC｜arXiv:2611.15589**

### 为什么重要

“去配电室二号柜前面”和“到走廊尽头的消防器材”不是同一粒度的导航目标：前者可能指一个设备实例，后者是目标类别加空间关系。把全部设备节点和关系都塞入巨大开放词汇 3D 地图，会带来存储与语言推理成本。

EMS-Nav 将**区域作为组织基础**，按区域—房间—设备—具体实例的层级进行环境理解、检索和路径执行，让端侧只处理与当前任务相关的小块上下文。

### 算法模块、假设和可复现性

~~~text
RGB / 深度 / 里程计
         ↓
局部空间分区与区域级关系
         ↓
房间、对象、实例语义层级
         ↓
语言目标解析至对应粒度
         ↓
区域级导航 → 局部设备级定位
~~~

作者报告四类目标（对象、房间、区域、实例）全部取得较高成功率，整体首次尝试成功率相对最强对照提高 **9.39 个百分点**，同时减少地图开销与 LLM 输入长度；还展示真实室内本地部署。

但论文摘要没有足够明确的嵌入式统一显存、响应 P95，也未独立核实完整可安装仓库，不能把“端侧运行”直接当作 RK3588 已可一键部署。

### 最小 A/B 与适合谁关注

用已有 3D 点云和手工区域标签先构建轻量“楼层 → 区域 → 柜体实例”索引，不需要训练全部深度网络。创建 30 条文本导航任务，对比直接全图语义检索与分区层级检索的目标命中、错柜次数、上下文 Token、P95 及无图探索失败恢复。

适合工业巡检和语义导航。建议让语义目标输出在已知地图中的**可验证候选位姿**，最终路由与避障仍交给 Nav2/实际 3D Planner。

来源：[EMS-Nav 原论文](https://arxiv.org/abs/2611.15589)。

---

## 4. VINE：利用固定在场地里的相机导航，而不是强行学习外置视角到运动指令

**时间回补｜v1 2026-11-12 04:32 UTC｜arXiv:2611.16282**

### 为什么重要

工厂已有的固定摄像头可以看到机器人看不到的障碍，但是它们的坐标视角与机器人机载相机不同。论文发现，直接让 PPO 从随机位置的外置相机图像端到端输出 egocentric 控制，在指定仿真设置里学习失败。

VINE 先训练**视角不变的占据/障碍地图估计器**，输入外置图片、粗相机位姿、机器人位姿和房间尺寸；之后把这个地图交给普通 PPO 或 A*。这样分离“坐标视角转换”和“路径决策”。

### 关键架构、假设与结果

~~~text
Exocentric RGB + 摄像头粗位姿
                ↓
        学习全局障碍地图
                ↓
Robot pose → 机器人局部地图
                ↓
        A* / PPO 导航控制
~~~

作者在随机摄像头位姿仿真中，对相机平移轴各 **30 cm 标准差**、平均约 **20° 旋转误差**的近似外参仍有鲁棒性，并展示双摄像头部分覆盖条件；部分设置下成功率超过机载相机 PPO。

这不意味着外部视觉地图已实现生产级 30 cm 误差容忍或障碍厘米级定位。真实部署还面临网络延迟、相机覆盖盲区、外置到机器人世界坐标注册与数据隐私。

### 最小工程复现 / 适合谁关注

在 Gazebo/Isaac Sim 固定两台高位相机与一个底盘，先用真值外参构建占据地图，再逐步增加外参误差和掉线；比较外置相机直接 PPO、VINE 式地图→A* 与原始 LiDAR-only 控制，重点测遮挡误检、局部重规划和急停安全。

官方完整训练源码未独立确认。适合配电室固定摄像机与巡检机器人辅助融合，但外置传感器不可成为唯一安全避障依据。

来源：[VINE 论文](https://arxiv.org/abs/2611.16282)。

---

## 5. GenGenIK：条件 Flow 同时处理双手、移动底座、环境和偏好，而不只是单个目标位姿

**时间回补｜v1 2026-11-11 14:48 UTC｜arXiv:2611.15565**

### 为什么重要

传统数值 IK 常解决“此时手腕能否到达目标”，而移动操作、双臂抓取更需要一组**分布合理、后续可达、碰撞风险可控**的关节候选。GenGenIK 以条件生成建模这些多解，支持移动底座、双手目标、场景信息和“更偏好某类姿态”等任务条件。

### 算法模块

~~~text
目标末端位姿 / 场景 / 底盘与关节约束
                 ↓
        Conditional Flow 采样
                 ↓
    多组候选机器人配置 q₁...qₙ
                 ↓
FK 残差 / 碰撞 / 关节限位与后续规划验证
                 ↓
        可执行动作候选
~~~

论文报告双臂抬举、翻转等任务的求解成功率和耗时优于所比较方法，并可在部分场景观测下工作；摘要未统一提供实际设备 P99 或所有任务精确胜率，因此此处不额外填数字。

### 传感器、动力学和工程风险

这是 IK 候选生成，不是接触动力学或完整运动轨迹证明。生成动作仍需 FK 终点误差检验、全程碰撞检查、抓持力及底盘可达性约束。

本轮核实了[官方项目页](https://icra-2027-gengenik.github.io/)，但没有确认完整可复现源码/权重。可在同一个 MuJoCo 机械臂环境下对比随机多初值 IK、TRAC-IK 和 Flow 候选，统计 Top-K 可达、总求解时延、关节边界、下游规划完成率。

适合双臂/移动操作与多解逆运动学。生成结果不应在未验证前直接作用于关节电机。

来源：[GenGenIK 论文](https://arxiv.org/abs/2611.15565) · [项目页](https://icra-2027-gengenik.github.io/)。

---

## 6. FORGE：少量手腕目标与可选力命令，就能协调人形行走和接触操作

**时间回补｜v1 2026-11-12 17:30 UTC｜arXiv:2611.17142**

### 为什么重要

人形搬运、推箱等任务需要行走平衡、两手动作及接触力协调，但长期收集全身关节轨迹成本高。FORGE 的上层只需左右手腕相对骨盆位姿、粗速度/足步目标和可选期望力；底层通过冻结行走先验和残差动作保持稳定。

### 算法模块与动力学边界

~~~text
速度导航 / 足部目标 / 双手腕位姿 / 可选目标力
                       ↓
             多粒度 Whole-body Policy
                       ↓
       冻结行走 Prior + Asymmetric Residual
                       ↓
             G1 关节目标与运动
                       ↑
          本体感觉 + PD 扭矩重建
                       ↓
        Momentum Observer + 学习式力修正
                       ↓
           准静态虚拟手腕目标回路
~~~

它可以在**无手腕六维力传感器**的条件下估计低频等效接触力，但估计器不等于绝对可靠的硬件测力计。快速碰撞、摩擦变化与驱动器饱和需要独立保护。

### 实验与复现

作者评估统一控制的稳定性、腕部轨迹跟踪、持续挤压刚性箱体的接触力以及不同负载下的下蹲—抬举扩散策略动作。公开摘要没有统一可迁移的成功率或真机安全指标，不补造。

项目页[FORGE 官方展示](https://bb0928.github.io/forge/)已核实存在；完整训练权重和可运行代码未独立确认。建议在仿真中对比“仅手腕位置跟踪”“带虚拟目标力”与“带反馈残差”的接触力误差、足底滑移、腰部姿态和控制 P99。

### 适合谁关注 / 工程启发

适合 G1、双臂接触操作以及只拥有稀疏手部演示数据的机器人系统。对厂家 SDK 只提供速度和登梯模式的平台，可以借鉴**高层稀疏命令→稳定模式→状态反馈**，而不应声称能直接移植下肢控制权重。

来源：[FORGE 论文](https://arxiv.org/abs/2611.17142) · [项目](https://bb0928.github.io/forge/)。

---

## 7. Alloy：可 pip 安装的多材料物理引擎，还给 Codex 提供原生 MCP 接口

**时间回补｜v1 2026-11-12 05:14 UTC｜arXiv:2611.16312**

### 为什么重要

机械臂操作的布料、线缆、液体、沙粒往往需要不同求解器，训练系统因此被迫维护多套模拟器和数据桥接。Alloy 在同一个场景里用不同的材质 Solver，并在统一 Control Step 耦合：刚体采用 MuJoCo Warp，布料/软体使用 Newton VBD，颗粒材料使用 MPM，液体使用 DFSPH。

更特别的是作者**从设计之初为 Agent 提供文档和 MCP 工具**；Codex 可以以工具形式创建场景、运行物理步、读取状态和健康度，而不是通过猜测代码 API 来操作仿真。

### 算法模块

~~~text
场景对象卡片（形状、质量、摩擦、材质）
                 ↓
         Solver Router
  ├─ 刚体/关节 → MuJoCo Warp
  ├─ 布料/软体 → Newton VBD
  ├─ 沙粒       → MPM
  └─ 液体       → DFSPH
                 ↓
每一步材质间耦合 / 接触 / 多并行世界
                 ↓
状态、可视化与 World Health Grade
                 ↓
             RL / IL / Agent
~~~

### 已核实代码与最小启动

[官方 GitHub](https://github.com/argonrobotics-ai/alloy) 已公开，Apache-2.0；支持 Linux x86-64、Python 3.11/3.12、CPU 或兼容 NVIDIA GPU。仓库 README 给出：

~~~bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install alloy-engine
python -c "import alloy; print(alloy.__version__)"
python -m alloy.docs agents
~~~

验证一个落箱实验可参考[官方 Quick Start](https://github.com/argonrobotics-ai/alloy#quick-start)：定义 0.8×0.8×0.7 m 的桌子，在 z=0.9 m 放置 8 cm 方盒，运行 1.5 s，检查最终 z 约 0.74 m 和 `sim.check()['ok']`。该项目还提供 `alloy mcp` 的 stdio 工具服务。

论文和仓库报告并行世界数从自由刚体的数千，到机械臂约 512–4,096，布/液体通常只有数十至数百；**性能强烈依赖材质、接触精度和 GPU**。不能将它等同于几千个复杂布料世界都能实时运行。

### 鲁棒性与工程风险

Alloy 是初期 0.x 公开版本，API 可能变化；已知间隙与 workaround 被列于[官方限制页](https://alloy.argonrobotics.ai/docs/keep-in-mind/)。大规模训练时要区分物理失稳与策略失败，不能只看平均 Reward。

### 适合谁关注 / 落地启发

适合线缆、软体、倒水、人形接触和 Sim2Real。建议先在 CPU 做落箱/布料简例，再比较 GPU 并行数量、内存、接触误差和模型健康状态。它也是今日最适合直接实验的 **Codex + MCP 机器人附属工具**；具体接入见后文实战技巧。

来源：[Alloy 论文](https://arxiv.org/abs/2611.16312) · [作者源码](https://github.com/argonrobotics-ai/alloy) · [MCP 实现](https://github.com/argonrobotics-ai/alloy/tree/main/alloy/mcp)。

---

## 8. Prediction-Error-Tightened MPC：给人群导航添加模型预测误差的安全余量

**时间回补｜v1 2026-11-11 17:56 UTC｜arXiv:2611.15781**

### 为什么重要

机器人在人员密集走廊导航时，不仅预测行人轨迹，还应估计**自己的预测有多不可靠**。这篇方法将 Koopman 预测与在线残差估计接入 MPC 的碰撞约束，针对误差为避障距离增加边界。同时用语义区分行人与普通障碍，并合并附近障碍以降低优化约束数量。

### 算法模块

~~~text
行人与障碍感知
       ↓
Koopman 行人轨迹预测
       ↓
在线预测误差统计 / Markov Residual Tightening
       ↓
对行人调整人际安全距离
       ↓
附近障碍聚合，减少 MPC 约束
       ↓
滚动优化 / 控制执行
~~~

### 量化结果与边界

作者在配对 **300 个随机种子**的移动障碍闭环仿真中，将物理接触比例从 **10.0% 降至 1.33%**，平均额外行驶时间约 **0.68 s**。另一项人群语义消融，机器人占用区域和行人个人空间重叠时长比例从 **22.84% 降为 2.11%**。

两组指标来自**不同实验**，不能直接组成一个统一的机器人避碰成功率。论文没有报告真实人群道路的事故证明或可直接移植的代码；预测误差估计如果分布漂移，同样可能失效。

### 最小复现 / 适用场景

在 ROS2 Gazebo 的双人交叉走廊中，对比普通 MPC、固定障碍膨胀、在线误差收紧 MPC，分别测接触、个人空间侵入、死锁、过于保守停车和求解 P99。动态保护应由独立的物理紧急停止维持。

适合轮式巡检、多机器人共用走廊与人与机器人近距离共处。

来源：[Prediction-Error-Tightened MPC 原论文](https://arxiv.org/abs/2611.15781)。

---

## AI / LLM 附属框架与开源工程组件

### 组件 1｜Memory-TCG / RRR：长期 Agent 记忆最该保留的是“当前有效决策”

**时间回补｜v1 2026-11-11 15:55 UTC｜arXiv:2611.15644**

**论文和源码：** [Memory-TCG 论文](https://arxiv.org/abs/2611.15644) · [elzobrito/conversation-esaa-rrr-artifacts](https://github.com/elzobrito/conversation-esaa-rrr-artifacts)。

**痛点：** Agent 跑了一周，历史聊天里可能反复出现“采用方案 A → 放弃 A → 改 B”，一旦按时间截断或盲目摘要，可能把旧方案当作当前有效要求。

Memory-TCG 的 RRR Consolidation 通过当前有效决策、权限/来源、冲突证据和 Token 预算决定保留哪些记录。它与“把所有日志长期存储”不是一回事。

~~~text
历史事实、旧决策、冲突与来源
              ↓
保留当前权威决策 + 去重归并
              ↓
不同 Token Budget 选择上下文
              ↓
输出 Decision / Provenance / Conflict
              ↓
下一个 Agent 会话执行
~~~

**作者实验：** 480 条事实、1,024 Token 限额下，完整 RRR 当前决策召回为 **0.44**，按时间截断仅 **0.06**，理论表示上界 **0.58**；4,096 Token 下当前决策被全部召回。但作者也发现简单的 Authority-aware 基线 B' 与完整 RRR 在决策召回上可以打平，说明真正起作用的不一定是复杂“共振”机制。

此外有限预算下冲突项可能被挤掉；在 480 事实/1,024 Token 条件给冲突预留 20% 预算可提高 Conflict F1，但会降低部分决策召回。这是**合成数据工程实验**，不是独立证实的生产 Agent 优越性。

**可运行代码：** 仓库采用 MIT，包含冻结源码、实验数据和验证脚本；需 Node 18+、Python3、tiktoken 0.12.0。示例：

~~~bash
git clone https://github.com/elzobrito/conversation-esaa-rrr-artifacts.git
cd conversation-esaa-rrr-artifacts
python -m venv .venv
.venv/bin/pip install -r tests/memory/requirements-evaluation.txt
.venv/bin/python tests/memory/v13-evaluation.py /tmp/rrr-v13.json
python tests/memory/test-v13-result.py
node --test tests/memory/authority-baseline.test.js
~~~

**Codex/T3 Code 的直接用途：** 把项目决策记忆从流水账改为一条条“当前决策+仓库位置+对应验收命令+被替代的旧决策”，每次开启新任务只取有效决策。建议用二十个跨周历史 Issue 比较只读最新 AGENTS.md、最近日志截断和 Authority-aware 决策索引，测需求遗漏、重复调查、Token 和错误决策引用。不要把合成分数直接当 Codex 真实增益。

**局限：** 该仓库是研究实验快照，不是可安装的 Codex 生产插件，也不是 Mem0。尚未证明任意文档都能自动正确判定“当前权威”。

---

## AI Coding 实战技巧精选

### 技巧 1｜Codex 先从需求提炼不变量，再读实现生成回归测试

- **来源**：[Spec-Driven PBT 作者论文](https://arxiv.org/abs/2611.15920)，2026-11-11 UTC；工程方法。论文针对 25 个 ViBench 应用，规格驱动测试比代码驱动少生成 **2.4×** Property Tests，并发现后者漏掉的业务流程 Bug；169 个 Bug 中接近 60% 仅由其中一种方法检出。这不是任何 Codex 版本的直接 Benchmark。
- **一句话结论**：先让 Codex 依据需求输出必要的外部行为，再查看具体实现生成测试，避免“代码已经这么写了，所以测试也认可它”的循环验证。
- **具体怎么做**：
  1. 选一个有明确输入输出契约的函数/协议流程，例如 SIP 会话重试、设备报警状态机。先只提供规则文档，要求列出不超过 5 条可执行不变量及 2 个反例。
  2. 复核不变量正确后，再提供当前仓库实现，要求根据语言选用已有 Catch2/GoogleTest 或 Hypothesis，把不变量变成实际回归测试。
  3. 对比代码驱动测试，检查独立需求是否被覆盖；修复前应至少有一个针对真实问题的失败用例，修复后通过。
  4. 不自动补大量无价值测试；记录有效新 Bug、无关修改数和验证总时间。
- **适合**：Codex、C++/ROS2/SIP、状态机、协议和多阶段工作流。
- **注意**：作者完整 Agent Harness 的公开构建状态未独立核验，这里提供的是基于原研究的可直接落地流程，而不是声称官方提供了 Codex Skill。独立的测试执行器和原始需求不能让 Agent 随意改写。

### 技巧 2｜把 Alloy 仿真作为 Codex 的 MCP 工具，先验证物理再讨论 RL

- **来源**：[Alloy 原始仓库 MCP 说明](https://github.com/argonrobotics-ai/alloy#MCP-server)，2026-11-12 论文对应的已核实实现。
- **一句话结论**：在真实机器人上验证之前，让 Codex 调用仿真服务的 build、step、state、check，直接获取结构化物理结果，而不是猜测模拟器源码或写一堆中间脚本。
- **具体怎么做**：
  1. 在 Linux Python3.11/3.12 虚拟环境执行 `pip install alloy-engine`，先用 README 落箱案例确认 `sim.check()['ok']`。
  2. 在同一个虚拟环境中通过 Codex CLI 添加 MCP：`codex mcp add alloy -- /absolute/path/to/venv/bin/alloy mcp`。
  3. `codex mcp list` 核实服务配置存在；新的 Codex 会话里先只允许创建箱子与桌子场景，执行低风险小步数仿真。
  4. 比较工具式调用和临时生成 Python 脚本的失败次数、场景搭建耗时、状态检查是否可靠，再决定是否扩大到布料/液体任务。
- **适合**：Codex CLI、T3 Code 的 Codex 后端、GPU 机器人仿真、柔性物体任务。
- **注意**：MCP 配置不保证服务在所有环境成功启动；`alloy mcp` 的 Tools 也不等于物理正确性或真实机器人安全。项目仍是早期 0.x 工程。本任务**未启动 Codex 或消耗额度**。

---

## 经典论文回顾

### Graduated Non-Convexity for Robust Spatial Perception: From Non-Minimal Solvers to Global Outlier Rejection

**作者：** Heng Yang、Pasquale Antonante、Vasileios Tzoumas、Luca Carlone。原始预印本 **2019-09-18**，后续期刊工作发表于 2020 年。

**原始资料：** [论文 arXiv](https://arxiv.org/abs/1909.08605) · [MIT SPARK Lab](https://web.mit.edu/sparklab/2020/11/10/Graduated_Non-Convexity_for_Robust_Spatial_Perception__From_Non-Minimal_Solvers_to_Global_Outlier_Rejection.html) · [GTSAM](https://github.com/borglab/gtsam)。

### 核心问题与数学思想

三雷达地图匹配或跨机器人回环可能存在很多错误对应。对所有观测直接最小二乘，少数错误约束就会把地图拉偏；RANSAC 虽然鲁棒，但在高维几何配准和高外点率时样本需求大。

Graduated Non-Convexity（GNC）从容易求解的近似稳健代价出发，逐步调整非凸性，让优化器渐进降低离群点权重。研究将 Black–Rangarajan 双重性与非最小样本求解器结合，处理点云、网格配准、位姿图和物体位姿估计。

~~~text
原始点云 / 回环对应
           ↓
  较容易的平滑鲁棒代价
           ↓
      优化状态 x
           ↓
  根据残差更新观测权重
           ↓
逐步提高非凸性并反复优化
           ↓
   鲁棒 SE(3) / 位姿图结果
~~~

### 历史价值、效果与边界

作者在指定实验展示对 **70–80% 错误观测**的经验鲁棒性，并在若干任务中优于 RANSAC 等对照。但**GNC 不保证任意非凸问题全局最优，也不意味着所有退化走廊都能自动找出唯一正确回环**。

鲁棒权重解决外点影响，可辨识性解决“是否有足够独立几何证据”，两者不是同一个问题。

### 传感器/动力学假设与现代实现

该方法处理观测残差，对传感器本身没有直接生成新信息的能力；需要足够正确的内点、恰当的尺度估计、对应关系和残差模型。现代 GTSAM 已有 GNC 优化相关实现，可以作为学习范例，但本次没有核验其与原论文所有实验配置完全一致。

### 可复现性 / 对工程项目的重新解读

在同一组 3D 回环对齐问题中注入 0%、20%、50%、70% 错误对应，比较最小二乘、RANSAC、GNC 的旋转和平移误差、运行 P95、错误回环接受率，再在平行墙/对称房间中增加退化测试。建议将 GNC 与 Switchable Constraints 放在离线图优化 A/B，而不是无条件替换已稳定的实时 LIO 前端。

**结论：** 鲁棒核优化是保护地图的一层，但不应取代回环几何验真和失败可恢复机制。

---

## 今日结论

**最值得实际复现的是 QVS-LIVO 与 Alloy。** 前者给出真正可构建的 ROS2 多相机健康选择估计器，后者既提供物理引擎也提供 Codex 可调用的 MCP 工具。两者对多传感器定位与机器人 Agent 仿真都能产生可检验的结果，而不是只有论文图表。

CT-SGAL-LIO 值得以独立固定滞后 spline 做小实验：如果不破坏现有厘米级地图定位精度，却能减少短时姿态跳变，收益可能大于继续合并更多雷达点。EMS-Nav 则适合优先在真实配电室数据上验证区域级语义索引，避免过早引入很重的全局图结构。

对于 Codex，不再靠普通版本更新凑内容。Memory-TCG 的启发是**压缩项目历史时保留当前有效决策与冲突**；Spec-Driven PBT 的启发是**先从用户需求定义可执行不变量，再让 Agent 看实现**。两者都应通过自己的真实仓库 A/B 验证，不能将论文数据当作实际节约成本。

---

## 最值得深入研究或尝试复现的方向

| 优先级 | 研究方向 | 最小验收指标 |
|---|---|---|
| P0 | QVS-LIVO | ROS2 Humble 构建、四相机失帧/偏移、拒绝错误校正 |
| P0 | Alloy | CPU 落箱物理验收、MCP 工具返回与 GPU 并行性能 |
| P0 | CT-SGAL-LIO | RTE、位姿跳变、引入固定延时、闭环误差 |
| P1 | EMS-Nav | 真实设备查询、语义导航首次成功率、Token |
| P1 | Memory-TCG | 当前决策召回、冲突保留率、上下文大小 |
| P1 | Spec-Driven PBT | 独立需求不变量、真实新 Bug、修改范围 |
| P1 | Crowd MPC | 行人接触率、个人空间侵入和求解 P99 |
| P2 | VINE | 外置相机错位/遮挡与可达地图 |
| P2 | GenGenIK | Top-K 关节配置有效率、碰撞与规划完成率 |
| P2 | FORGE | 接触力估计、足底滑移、控制限幅 |
| P2 | GNC 经典实验 | 高外点率配准、误闭环与对称几何退化 |

---

## 参考资料

**最新公开批次：** [arXiv cs.RO](https://arxiv.org/list/cs.RO/new) · [arXiv cs.SE](https://arxiv.org/list/cs.SE/new)。

**SLAM / 语义导航：** [QVS-LIVO](https://arxiv.org/abs/2611.16205) · [QVS-LIVO ROS2 代码](https://github.com/zihanPan-HIT/QVS-LIVO) · [CT-SGAL-LIO](https://arxiv.org/abs/2611.16918) · [EMS-Nav](https://arxiv.org/abs/2611.15589) · [VINE](https://arxiv.org/abs/2611.16282)。

**规划、控制和物理：** [GenGenIK](https://arxiv.org/abs/2611.15565) · [FORGE](https://arxiv.org/abs/2611.17142) · [Alloy](https://arxiv.org/abs/2611.16312) · [Alloy GitHub](https://github.com/argonrobotics-ai/alloy) · [Prediction-Error-Tightened MPC](https://arxiv.org/abs/2611.15781)。

**AI 附属组件及 Codex：** [Memory-TCG 论文](https://arxiv.org/abs/2611.15644) · [开源实验](https://github.com/elzobrito/conversation-esaa-rrr-artifacts) · [Spec-Driven PBT](https://arxiv.org/abs/2611.15920) · [Alloy MCP](https://github.com/argonrobotics-ai/alloy#MCP-server)。

**经典论文：** [GNC Robust Spatial Perception](https://arxiv.org/abs/1909.08605) · [MIT SPARK Lab](https://web.mit.edu/sparklab/2020/11/10/Graduated_Non-Convexity_for_Robust_Spatial_Perception__From_Non-Minimal_Solvers_to_Global_Outlier_Rejection.html)。

