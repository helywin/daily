---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-20"
date: 2026-11-20 09:00:00 +0800
description: "Facet-SLAM实时Triangle Splatting、足接触地图校正SBEE、雷达Doppler安全CBF、毫米级LiDAR视觉对接、转向约束多机规划、城市无线无人机、生成式世界模型规划加速及torchtest2实战。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-20

## 摘要

**检索日期：2026-11-20（Asia/Shanghai，星期五；核实时间约 09:02）。** arXiv Robotics（cs.RO）最新常规公开列表为 **2026-11-19**，总计 **140** 项（其中 **85** 项 New submissions）；Software Engineering（cs.SE）总计 **110** 项（其中 **77** 项 New submissions）。总数含交叉收录和更新稿，并不全部代表新论文。原始列表：[cs.RO](https://arxiv.org/list/cs.RO/new)、[cs.SE](https://arxiv.org/list/cs.SE/new)。

本期优先审查最近 24 小时，再按任务规范考虑最近七天。八项主动态均来自 11 月 19 日发布列表，其原始 v1 提交于 **11 月 18 日 UTC**，已超过核验时的滚动 24 小时，因此明确标记为**时间回补**；不是把论文出现在列表的日期误写为首次提交时间。选题前读取仓库已覆盖索引 **1,406 条**，按 arXiv ID、规范化标题、项目主页和代码地址查重，所选八项均未出现。

**本期主线：** 用几何约束让三角面元 SLAM 真正达到传感器帧率；将足部触地历史当作可重复利用的高程地标；用 FMCW Radar 原生 Doppler 而不是差分距离估计危险相对速度；通过 LiDAR 墙线与 AprilTag 实现毫米级终端对接；把转向执行时间纳入多机器人路径协调；无人机同时估计碰撞几何和蜂窝信号盲区；以及避免世界模型重复对大量相近动作候选做完整前向预测。

**优先动手：** [Facet-SLAM](https://github.com/edward62740/Facet-SLAM) 有真实安装脚本和 TUM/Replica 示例，但整体研究用途许可应单独审查；[PIBTT2](https://github.com/tzy82065/PIBTT2) 有 CMake 编译及可运行的转向约束多机规划测试；[AeroCity-RT](https://github.com/ppppyq/AeroCity-RT) 能独立生成可复现的城市和蜂窝覆盖场景。AI 工程方面，公开的 [torchtest2](https://github.com/Hrehory/torchtest2) 可在模型正式训练前检查静默错误。本次仅核实原始论文和仓库文件，**没有实际编译、运行训练或使用 Codex 额度**。

---

## 1. Facet-SLAM：RGB-D 三角面元地图同时服务 GICP 跟踪和实时网格渲染

**时间回补｜v1 2026-11-18 06:23 UTC｜[arXiv:2611.23935](https://arxiv.org/abs/2611.23935)**

### 为什么重要

Gaussian Splatting 地图擅长新视角渲染，但直接获得可用于碰撞分析的网格还需要额外处理。Triangle Splatting 的三角面元天生含表面结构，问题是三角形位置如果在渲染优化中不断移动，就不能当作可靠的 GICP 配准目标。Facet-SLAM 将跟踪和渲染优化需要的几何分开处理：**从融合的 RGB-D 深度确定面元质心，GICP 只对可信质心做几何配准；渲染端更新形状和外观时，限制三角形发生平移。**

### 算法模块、传感器假设

~~~text
同步 RGB-D 帧 → 深度融合并构建 Triangle Facets
                       ├─ 固定质心 → GICP 几何跟踪
                       └─ 非平移参数优化 → 外观和表面更新
                         ↓
                    位姿 + 可三角化网格
~~~

仅基于 RGB-D，相机标定与深度有效性仍是关键；不能把它等同于可直接处理原始三路 LiDAR 的框架。动态物体、反射深度和无效像素需要额外鲁棒处理。

### 实验、实时性与风险

作者报告桌面 GPU **约 100 FPS**，Jetson AGX Orin 可以达到传感器帧率；相对所比较光度三角面元跟踪方案提速 **超过 20 倍**。Replica 的 Delaunay 网格 Chamfer Distance 从对照的 **1.55 cm** 降至 **0.86 cm**。帧率并不包含任意真机 ROS2 导航全链路，也不代表在所有场景下达到硬实时 P99。

### 源码与最小复现

[edward62740/Facet-SLAM](https://github.com/edward62740/Facet-SLAM) 已公开安装脚本、TUM、Replica、Ceres 窗口优化、GICP 扩展及单元自测。作者说明依赖 CUDA 12.x、PCL、Eigen、uv 等，需下载约 2GB 的 PyTorch 并构建多项扩展：

~~~bash
git clone --recursive https://github.com/edward62740/Facet-SLAM.git facet-slam
cd facet-slam
sudo apt install -y libeigen3-dev libpcl-dev
bash install.sh --no-live

source .venv/bin/activate
python main.py --dataset fr1_desk --max_fps 30 --eval
python main.py --dataset room0 --eval
~~~

Linux/NVIDIA 环境先按文档检查编译器、CUDA Toolkit 和依赖版本。**仓库虽然可见 MIT 标记，但 README 明确说明组合代码总体上只能做非商业研究；各上游三方组件许可证要逐项核验，不可仅凭单个 LICENSE 认定可商业集成。**

### 适合谁关注与工程落地启发

适合 D455/RGB-D、视觉稠密 SLAM、表面 Mesh 与数字孪生研发。可固定相同 TUM/Replica 序列对比 GICP ATE/RPE、网格 Chamfer、GPU 内存与处理 P95。对已有成熟 LiDAR 定位的机器人，先验证它作为**视觉网格侧车模块**的价值，而不是替换主定位。

来源：[论文](https://arxiv.org/abs/2611.23935) · [代码](https://github.com/edward62740/Facet-SLAM) · [作者项目页](https://edward62740.github.io/facetslam/)。

---

## 2. SBEE：足部接触本身成为高程地图地标，校正无外部感知时的垂直漂移

**时间回补｜v1 2026-11-18 12:19 UTC｜[arXiv:2611.24310](https://arxiv.org/abs/2611.24310)**

### 为什么重要

足式机器人在灰尘、黑暗、遮挡或激光暂时失效时，只剩 IMU、关节编码器与接触信息。其全局位置和航向一般不可观测，尤其垂直漂移会破坏摆腿高度参考。SBEE 将**曾经踩过的地形高度**保存在概率地图里：新稳定接触写入带不确定性的高程，再次走到已见位置时，用该地形反馈修正底座高度，类似只利用本体感觉做垂直回环。

### 算法模块、传感器与假设

~~~text
IMU + 关节位置/速度 + 足底接触置信度
                   ↓
     左不变 EKF (LI-EKF)：姿态、速度、位置、Bias
                   ↓
             接触点高程采样
                   ↓
      环形索引局部 Elevation Grid
                   ↓
          地图高程与方差反馈
                   ↓
       只修正可信的底座垂直分量
~~~

地图采用环形（Toroidal）索引，窗口重新居中不必整体复制全部地图。系统使用运动学速度量测而不是对每条腿都增广完整接触状态，滤波状态维度不随腿数增加。利用地图做垂直伪量测时采用局部、不确定度加权更新，以免旧地图反向污染速度、姿态和 Bias 等可观测状态。若足底滑移、错误接触判定或新旧地形发生变化，垂直约束同样会失真。

### 实验、实时性、可复现性

作者在四足/双足 MuJoCo 仿真及 ANYmal-D GrandTour 约 **296 m** 行走数据上，报告 ATE **1.062 m**，相比三种本体估计对照中最强者改善 **22.1%**；Raspberry Pi 5 的平均估计周期耗时 **0.162 ms**（论文指定条件）。这个 ATE 不能改写成厘米级定位，也不能说它解决了全局 XY 和 Yaw 漂移。

**开源状态必须特别说明：** 论文摘要将方法称为 open-source framework，但正文明确写着 **“will be released as open-source upon acceptance”**。本轮没有发现可核实的正式 SBEE 实现，不能提供杜撰的 git clone 安装命令。

### 适合谁关注与工程落地启发

适合 G1、四足/轮足登梯、纯本体状态估计与已知坡地接触重复性研究。先用 MuJoCo 保存足底接触位置与高程方差，在每次重复踏地时测垂直误差、滑移诱发的错误校正、地图长度与估计 P95，再考虑接入已有 SDK 状态估计。

来源：[论文](https://arxiv.org/abs/2611.24310) · [HTML 方法与数据](https://arxiv.org/html/2611.24310v1)。

---

## 3. Radar-Native CBF：直接把毫米波 FMCW Doppler 当作安全约束导数

**时间回补｜v1 2026-11-18 00:19 UTC｜[arXiv:2611.23654](https://arxiv.org/abs/2611.23654)**

### 为什么重要

对移动机器人迎面来的动态障碍，仅知道当前距离不够，还需要知道**相对接近速度**。如果用相邻距离做数值差分或依赖 Kalman 目标跟踪，障碍突然改变速度时可能因滤波滞后而太晚制动。FMCW Radar 可以直接通过 Doppler 测到径向距离变化率。论文将它作为以机器人为中心的距离 CBF 导数，得到封闭形式的纵向速度限制，并将距离、Doppler、机器人速度、方位测量的不确定度编入安全裕量。

### 算法模块与物理假设

~~~text
FMCW Radar：距离 r、径向速度 dr/dt、方位
                    ↓
         传感器误差界与安全缓冲
                    ↓
           纵向 Range CBF
                    ↓
      对名义前进速度进行闭式裁剪
                    ↓
         底盘速度控制 / 制动执行
~~~

它保护的是**纵向距离通道**，需要持续检测和有界测量误差，并要求底盘在给定后退/制动能力内。没有检测到障碍、错误关联、极端侧向切入和实际底盘制动超限时，不能简单沿用证明。不是完整二维/三维避障器。

### 实际结果、工程风险

在满足平台撤退能力的 **508 次配对相遇**中，直接 Doppler 方案发生 **2 次**安全缓冲侵入；使用常加速度、常速度 Kalman 估计分别为 **15 次、25 次**。Unitree Go1 上，实测停车距离 **0.777 ± 0.015 m**，对照预测 **0.758 m**。这并不是零风险保证，而且缓冲侵入与实际碰撞并非同一个指标。

### 最小复现与适合对象

以录制的 Radar Range/Doppler、LiDAR 距离和差速底盘速度作为离线输入；对照“距离差分＋低通”“Kalman 估计相对速度”“直接 Doppler”三种纵向裁剪，统计缓冲侵入、过度停车、控制 P95 与丢检测情况下的退化行为。适合具备 FMCW Radar 的轮式机器人、行人动态接近保护及雷达与 LiDAR 冗余安全层。完整原作者源码尚未独立核实。

来源：[论文](https://arxiv.org/abs/2611.23654)。

---

## 4. 毫米级停靠：LiDAR 柜门直线 + AprilTag，分别测横向、法向和航向

**时间回补｜v1 2026-11-18 10:28 UTC｜[arXiv:2611.24191](https://arxiv.org/abs/2611.24191)**

### 为什么重要

巡检机器人可以在房间中完成厘米级导航，但停靠充电触点、柜体接口和精密操作台时，**终端姿态误差**比长路径的全局 ATE 更重要。差速底盘不能直接横移，短距离内校正侧向位置需要旋转和平移联合控制。论文使用 LiDAR 在柜门平面拟合直线，获取法向距离与朝向；AprilTag 识别具体工作站，将 Tag 中心光线和 LiDAR 所测平面相交以确定切向位置。

### 算法模块

~~~text
全局导航 → 停靠区域
      ↓
LiDAR 柜前直线：法向距离 + 偏航
      +
AprilTag 图像：工作站 ID + 中心射线
      ↓
射线与 LiDAR 平面交点：切向位置
      ↓
教示参考位姿 / 固定误差抵消
      ↓
侧向预校正 + 连续视觉伺服 + 预测停车
~~~

教示观测有助于抵消**在相同安装和几何条件下**的可重复系统偏差，但若相机/雷达固定位置改变，旧偏差不能直接继续使用。

### 实验结果与限制

同一套导航/停靠代码在 Robot 2 的五个工位、两次测试中，**111/111 完成**，其中 **101/111 一次成功**；相对于教示观测的车载纵向、横向和航向 RMS 分别为 **1.51 mm、5.93 mm、0.238°**。允许位置各轴 ±10 mm、航向 ±1° 时，联合接受率 **107/111（96.4%）**。**这是相对教示和车载观测的残差，不等于外部测量仪校准过的绝对毫米级精度。**

### 最小复现、工程启发

为已有差速底盘设置“LiDAR 柜门平面 + AprilTag”，与“仅 AprilTag”或“仅 LiDAR 线段”对照。每个工位重复 20 次，记录位置误差三轴、单次成功率、速度下限、停止过冲、不同光照和安装变化。适合配电室巡检停靠、近场充电、机械接口对接。完整官方实现未独立确认，论文方法可先离线验证。

来源：[论文](https://arxiv.org/abs/2611.24191)。

---

## 5. PIBT*_T：一千台机器人也要算转向和让路，而不能只按网格跳跃

**时间回补｜v1 2026-11-18 06:01 UTC｜[arXiv:2611.23911](https://arxiv.org/abs/2611.23911)**

### 为什么重要

传统 MAPF 将相邻栅格的移动当作同样的一个离散动作。但差速底盘必须先转向才能进入部分相邻栅格，转向会占用时间和通道。如果规划器按“上一台机器人下一步立即腾空该节点”协调，就可能在真实执行时阻塞甚至死锁。PIBT*_T 扩展优先级继承和回溯的迭代 MAPF，显式处理转向占用、局部死锁、Livelock 与不必要的重复推让。

### 算法、动力学假设

~~~text
格点位置 + 朝向 + 离散转向时间
                ↓
   Priority Inheritance with Backtracking
                ↓
  转向依赖 / 节点占用 / 死锁解除
                ↓
     每个迭代时步规划动作
                ↓
   Action Dependency Graph 执行模拟
~~~

系统仍需要独立满足真实底盘加减速、体积、定位误差和通信延迟，抽象转向时间不等于真实运动轨迹一定不碰撞。

### 实验与工程入口

论文在标准 MAPF Benchmark 上报告可在数秒内处理**最多 1,000 个 Agent** 的指定实例，使用 ADG 执行仿真和制造系统案例比较实际任务完工时间，并通过 TurtleBot4 实验展示基本可行性。**不是 1,000 台真机实时控制实验。**

官方 [tzy82065/PIBTT2](https://github.com/tzy82065/PIBTT2) 采用 C++、CMake 3.16+，包含示例与实验脚本：

~~~bash
git clone --recursive https://github.com/tzy82065/PIBTT2.git
cd PIBTT2
mkdir -p build && cd build
cmake ..
cmake --build . -j

./mapf -i ../instances/mapf/sample.txt -s PIBT -o result.txt -v
~~~

源码基于之前的 PIBT 公共实现，商业使用前需核实各依赖授权。

### 适合谁关注与复现

适合多台室内巡检机器人、仓储搬运与共享窄门。用同一仓库地图，对照普通 PIBT、PIBT*_T 和真实差速底盘执行仿真，统计冲突数、转向占用、任务 Makespan、规划 P95 和重规划。**比只比较图上最短距离，更贴近工程执行。**

来源：[论文](https://arxiv.org/abs/2611.23911) · [C++ 仓库](https://github.com/tzy82065/PIBTT2)。

---

## 6. Control-Aware Hyperplanes：CBF 不仅选安全分离面，还让速度命令改动最小

**时间回补｜v1 2026-11-18 05:19 UTC｜[arXiv:2611.23867](https://arxiv.org/abs/2611.23867)**

### 为什么重要

CBF 避障常依赖机器人和多边形障碍之间的分离超平面。若只根据几何选取方向，可能得到过于保守、偏离名义速度命令很大的控制结果。将所有超平面方向和控制量放进一般非凸优化又会带来初始化敏感和不可预测求解延迟。论文利用**机器人与障碍的 Minkowski Difference Polygon**，把问题转换成有限组可闭式检查的候选控制调整，在满足条件时直接选最小范数的可行修改，无需在每一步运行一般非线性 Solver。

### 算法与动力学假设

~~~text
机器人多边形 + 障碍多边形 + 名义速度
                     ↓
         Minkowski Difference
                     ↓
          有限候选分离方向
                     ↓
        闭式安全与可行性检查
                     ↓
           最小控制修正量
~~~

结论只覆盖论文设定的二维平面、多边形和具体控制模型。无法直接外推到三维轮足复杂接触，也不能在地图错误或无可行控制时继续保证安全。

### 实验与可复现性

在 **250 个仿真导航场景**中，作者报告与局部非线性求解器相比，累计干预代价的中位数下降 **3.6%**、第 90 百分位下降 **27.3%**；16 个同时障碍的扩展测试每步约 **6.1 倍**加速。要注意“全局最优”限定在论文**可行且满足模型假设的联合子问题**，不是无条件最优导航路径。完整官方代码尚未核实。

### 工程落地

在差速底盘周围构造矩形/多边形障碍，将现有 CBF-QP 的超平面选择改为有限候选法，对照最低障碍净空、无可行解率、原指令偏移、CPU P99、制动距离。适合无 GPU、CPU 时间敏感的安全层。

来源：[论文](https://arxiv.org/abs/2611.23867)。

---

## 7. CommDreamer：3D LiDAR 与蜂窝 SINR 联合世界模型，让无人机提前绕过通信盲区

**时间回补｜v1 2026-11-18 11:22 UTC｜[arXiv:2611.24244](https://arxiv.org/abs/2611.24244)**

### 为什么重要

低空城市峡谷里，无人机不仅要避开建筑，还要保持蜂窝控制链路。未必能提前获得可靠的三维城市模型和全频段信道地图。CommDreamer 将机载 **3D LiDAR、多个小区的蜂窝测量与相对运动**写入循环潜变量模型，联合预测空间净空与不同方向 SINR；轻量策略在潜状态里想象多步结果，再决定飞行方向。

### 技术模块

~~~text
3D LiDAR 扫描 + 多基站测量 + 相对位姿
                       ↓
          Categorical Recurrent State-Space Model
                       ↓
             几何 / SINR 潜在信念
                       ↓
           潜空间 Rollout 与策略训练
                       ↓
       同时避障与维持无线链路的航线
~~~

### 实验与风险

作者在未见过的仿真城市形态中，报告在 **150 Episode** 内收敛，而比较的无模型 RL 无法完成任务；在所选测试中达到 **100% 任务成功、零碰撞**，中位路线 SINR 为 **8.02 dB**，有效通信中断率相比两种无线盲规划基线降低超过一半。**全部属于仿真，不是城市真机零碰撞保证。** 现场蜂窝网络会有变化的干扰、切站、天线和通信运营商策略，必须独立验证。

### 代码与最小复现

作者公开的 [ppppyq/AeroCity-RT](https://github.com/ppppyq/AeroCity-RT) 是**城市生成与 Sionna RT 无线仿真器**，不应误标为完整 CommDreamer 世界模型权重。其 Python 3.10+ 环境可在 Linux 使用，纯城市几何不要求 GPU；无线射线追踪通常需要相容的 NVIDIA/CUDA/OptiX：

~~~bash
git clone https://github.com/ppppyq/AeroCity-RT.git
cd AeroCity-RT
python -m venv .venv
source .venv/bin/activate
pip install -e .
wireless-city generate --config configs/city_only.yaml

# 无线计算需另外安装并配置支持的 Sionna RT 环境
# pip install -e ".[rt]"
# wireless-city generate --config configs/city_radio_smoke.yaml
~~~

最小实验固定同一三维城市场景和种子，比较最短路径、仅 LiDAR 避障和附加 SINR 预测的路径，统计实际碰撞、信号跌落时长、切站次数和执行成本。

### 适合谁关注

适合室外 4G/5G 无人机、网络覆盖辅助航线和城市低空导航。室内短程自主无人机可以借鉴无线/几何联合约束，但仿真蜂窝指标不可直接代替真实控制链路验收。

来源：[论文](https://arxiv.org/abs/2611.24244) · [作者仿真器](https://github.com/ppppyq/AeroCity-RT)。

---

## 8. ProbeShare：世界模型规划时只向少数候选“探针”完整推理，其余候选共享局部响应

**时间回补｜v1 2026-11-18 11:05 UTC｜[arXiv:2611.24229](https://arxiv.org/abs/2611.24229)**

### 为什么重要

视觉世界模型的 CEM/MPC 可以生成大量候选动作，然后用较大的前向预测模型评估每个候选到目标图像的距离。然而大量相近动作共享当前观察与相似局部物理影响。每条都重复调用十亿参数级世界模型会让闭环规划成本过高。ProbeShare 对代表性动作执行少量完整预测，学习或估计**动作—潜特征局部响应**，再用场景几何权重重建邻近候选的未来特征；当搜索走到未覆盖区域时补充新探针。

### 算法模块与假设

~~~text
当前观察 + 目标图像 + CEM 候选动作
                   ↓
      少量代表性 Action Probes
                   ↓
         大世界模型完整前向
                   ↓
       局部 Action-to-Feature 响应
                   ↓
重建多数候选潜特征、计算目标接近度
                   ↓
对外推不可靠区域追加 Probe 并重打分
~~~

关键假设是相邻候选的未来特征响应可以被足够平滑地近似。出现接触模式突变、硬碰撞、遮挡或多个动作引起完全不同结果时，不能盲目依赖共享推断。

### 实验结果和复现边界

作者在四项 RoboCasa 仿真操作任务中，报告相对逐候选密集 RoboJEPA 的 **Episode 规划加速 43.8–128.9 倍**，相对于其他所比较方法至少 **14.2 倍**；固定规划时间下取得更好的平均目标进度。**这是规划时世界模型 Rollout 计算的实验，不是整套真机控制器达到 128 倍 FPS。**

目前未独立核实完整官方代码或权重，不提供臆造的训练命令。

### 适合谁关注和工程实验

适合世界模型驱动的机械臂、视觉预测控制、动作候选重排。先在小型 PushT/抓取预测器中缓存邻近候选的预测结果，对比全部评估、简单线性近似和按误差触发新 Probe，记录候选排序一致性、成功率、GPU 推理调用数与真实闭环 P99。

来源：[ProbeShare 论文](https://arxiv.org/abs/2611.24229)。

---

## AI / LLM 附属框架与开源工程组件

### 组件 1｜torchtest2：训练前用一个 Batch 检测 PyTorch 模型里的“静默错误”

**工程补充回顾｜论文原始 v1 2026-10-16，非当日首发**；本期首次进入索引。来源：[torchtest2 论文](https://arxiv.org/abs/2611.23273) · [Hrehory/torchtest2 源码](https://github.com/Hrehory/torchtest2)。

**解决的痛点：** 模型可以跑、Loss 也在下降，但未调用某层、优化器遗漏新加的头、批次维度错误、Attention Mask 被忽略，训练几天后才发现。torchtest2 是 Apache-2.0 的轻量 Python 库，提供 **18 项单 Batch 检查**，支持 MLP/CNN/RNN/Transformer 和部分插件化的特殊模型训练接口；不需要云端 API Key 或另一个大模型。论文在 191 个未见过的模型架构测试里，对注入的静默错误检测率 **78%**（95% CI 75–80），原 torchtest 约 **40%**。作者还报告检查耗时中位数约 **1.0 秒**，但对真实缺陷的检出范围有限，不能声称捕捉全部训练 Bug。

**最小运行（Python ≥3.10、PyTorch ≥2.1）：**

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install torch torchtest2
~~~

在一份**本来就有模型和训练 Batch 的工程**中执行：

~~~python
import torchtest2

report = torchtest2.check_model(
    model, inputs, targets,
    loss_fn=loss_fn,
    optimizer=optimizer
)
print(report)
~~~

**核心接口：** 输入 model、一个真实 Batch、Loss、Optimizer，输出可审查的诊断报告。作者声称会恢复参数、Buffer、Optimizer 状态、梯度、训练标志以及常用 RNG 状态；但**无法自动恢复用户 forward 自己修改的任意 Python 普通属性**，所以首次应在隔离环境检查状态副作用。

**Codex/T3 Code 实战：** 让 Codex 先生成最小可重现 Batch，针对一个已知错误模型对照测试：原始训练是否能正常前向、torchtest2 是否实际检测、修复后警报是否消失；不要让 Agent 通过删除检查项来“修复”。对自己的视觉/RKNN 转换前 PyTorch 模型特别有帮助，但它**只检查 PyTorch 训练逻辑**，不能证明 ONNX、RKNN 数值转换、端侧量化正确。

**A/B 验收：** 选择 10 个带有不同静默错误的模型，分别使用仅 Forward Smoke、一个 Batch 过拟合、torchtest2；记录误报、漏报、执行时间与最终训练质量。论文来源：[论文原文](https://arxiv.org/html/2611.23273v1) · [PyPI 与项目 README](https://github.com/Hrehory/torchtest2)。

---

## AI Coding 实战技巧精选

### 技巧 1｜Codex 修改 PyTorch 网络后先用 torchtest2 检查静默训练错误

- **来源**：torchtest2 原作者 Grzegorz Gwardys，[官方 README](https://github.com/Hrehory/torchtest2)；论文原始 v1 2026-10-16。
- **一句话结论**：模型能正常调用、Loss 能下降仍可能存在没有使用的层和错误 Mask；Codex 完成修改后，只拿一批真实数据跑一次独立模型检查。
- **具体怎么做**：
  1. 为当前修改准备一个真实输入 Batch 和训练目标，核对输入 Shape、Device 和 Optimizer 是否覆盖所有可训练参数。
  2. 安装 torchtest2，调用 check_model(model, inputs, targets, loss_fn=..., optimizer=...)；保留诊断报告。
  3. 让 Codex 仅解释并修复明确发现的真实缺陷，再运行相同检查及最小训练回归；与单次 Forward Smoke 对照。
- **适合什么场景**：Codex + PyTorch、视觉语义网络、训练前模型重构、RKNN 转换前的训练实现。
- **注意**：不能把模型检查通过误当成训练精度、ONNX 导出或端侧 INT8 量化已经验证。与上方 torchtest2 为**同一项目**，索引只登记一次。

### 技巧 2｜用 Git Pickaxe 追溯某个 C++ 接口何时被改坏

- **来源**：[Git 官方 git-log 手册](https://git-scm.com/docs/git-log)；工程技巧回补，不伪装为当日新品。
- **一句话结论**：找到可能出错的函数后，不要只搜索当前仓库，还要查它在历史提交中的增删和实际 Diff，定位引入回归的最早改动。
- **具体怎么做**：
  1. 确定一个**真实存在**的函数名或配置字段，限定相关目录。
  2. 使用 Pickaxe 按字符串出现次数变化搜索，或者按补丁中的正则搜索：

~~~bash
git log -S'updateMap' --all --oneline -- src/
git log -G'updateMap|scanToMap' -p -- src/
git blame -L '/updateMap/,+25' -- src/localization.cpp
~~~

  3. 把找到的历史差异、Bug 复现条件交给 Codex；先做只读根因判断，再在独立 Worktree 中修复并跑最小测试。
- **适合什么场景**：Codex、ROS2/C++、长期维护、SIP 状态机、跨多次 Rebase 的回归定位。
- **注意**：-S 和 -G 语义不同；历史中函数改名或文件移动可能漏掉结果，最终必须由构建和测试验证，不应靠 Git 搜索结果直接下结论。

---

## 经典论文回顾

### Priority Inheritance with Backtracking for Iterative Multi-agent Path Finding（PIBT，Okumura 等，IJCAI 2019）

**发表时间与历史位置：** Keisuke Okumura、Manao Machida、Xavier Défago、Yasumasa Tamura，2019 年 IJCAI，后续扩展发表于 *Artificial Intelligence* 2022。来源：[IJCAI 2019 DOI](https://doi.org/10.24963/ijcai.2019/76) · [2022 扩展论文 DOI](https://doi.org/10.1016/j.artint.2022.103752)。

### 核心问题和算法思想

多个机器人共享图节点时，低优先级机器人占据高优先级机器人希望进入的位置，就需要**临时继承更高优先级**，请求前方机器人先移动；若当前局部移动序列找不到可行出口，再执行回溯。相比一次求出长时域最优多机器人路径，PIBT 使用短时迭代协调减少每轮计算，适合大量机器人与持续到来的任务。

~~~text
机器人当前占位 + 目标 / 优先级
                 ↓
         当前迭代选择下一节点
                 ↓
       阻挡时优先级向前传递
                 ↓
      可让路 → 提交局部动作
      不可让路 → 回溯并改选
                 ↓
       进入下一迭代时步
~~~

### 当年为何重要、今天仍在用什么

它把复杂全局 MAPF 的部分协调压力变成了局部优先级继承和回溯，后来成为可扩展 MAPF 的重要基础之一。今天仓储、车队和多机器人走廊协调中的临时让路思想仍然直接相关。**不能将经典 PIBT 的网格同步时间模型直接等同于真实差速底盘的转向、制动与执行时延。**

### 已被后续补充的部分和可复现性

今天的 PIBT*_T 特别补上了转向动作和转向依赖问题，这恰好说明经典 PIBT 的节点释放假设在真机上可能失真。作者新代码 [PIBTT2](https://github.com/tzy82065/PIBTT2) 含继承的原始 PIBT 与转向约束实现，能够用于同一 Benchmark 的直接对照；完整旧版源码与对应历史版本应按作者引用核对。

### 对实际工程的重新解读

在二维走廊、单门和充电工位的协调层，分别记录“图上规划时步”“机器人实际转向时间”“等待时长”“局部重规划”和“死锁次数”，比只看最终无碰撞更能解释系统瓶颈。真实底盘安全仍交给低层制动和障碍检测。

---

## 今日结论

**本期最优先动手：Facet-SLAM、PIBTT2 与 torchtest2。** Facet-SLAM 提供从 RGB-D 几何到 Triangle Splatting 网格的真实源码，但组合许可证限制非商业使用；PIBTT2 的代码和编译方法更适合立即检验多个差速底盘经过窄门时的转向依赖；torchtest2 可在不使用任何付费模型的情况下，先减少新 PyTorch 模型训练里的静默错误。

对定位研究，SBEE 的真正启发是**将足底历史接触作为具有方差的地图地标**，而不是说仅靠 IMU/关节编码器就解决了全部全局定位。毫米级终端停靠研究则把“全局导航”与“对接局部重复精度”清晰分开，值得在配电柜/充电触点场景中单独验收。

安全与规划方面，Doppler-CBF 对动态接近速度提供直接量测，但仍只有纵向通道保证；Control-Aware Hyperplane 降低过度干预，仍须遵守建模假设。世界模型加速研究需要比较实际闭环延迟和任务成功率，不能把规划内推理速度倍数搬到整机控制。

---

## 最值得深入研究或尝试复现的方向

1. **Facet-SLAM**：用 TUM/Replica 固定种子，比较几何跟踪 ATE、网格表面误差、CUDA 显存和 Jetson P95；使用前审查非商业许可证。
2. **SBEE**：对 MuJoCo 腿式机器人加入接触高程记忆，对比 LI-EKF 与地图反馈的垂直漂移；论文代码仍待发布。
3. **Radar-Native CBF**：同一组动态障碍相遇记录比较 Doppler 与 Kalman 相对速度估计的缓冲侵入和制动距离。
4. **终端精密对接**：LiDAR 柜门直线 + AprilTag；重复 20 次以上，分开报告车载残差和外部精度真值。
5. **PIBT*_T**：同一地图运行经典 PIBT 与转向约束 PIBT，重点测真机风格转向占用、Makespan 和死锁。
6. **Control-Aware Hyperplanes**：16 个多边形障碍时的安全可行率、名义控制偏移和 CPU P99。
7. **AeroCity-RT / CommDreamer**：先单独验证城市几何与 Sionna RT，再对照通信可靠性与安全路径；未确认完整世界模型开源。
8. **ProbeShare**：测世界模型调用数、候选近似排序错误和闭环 P95；不混淆 Episode 规划加速与电机控制时延。
9. **Codex + torchtest2**：已知静默错误模型的检查覆盖、误报、数据副作用与训练回归。
10. **Codex + Git Pickaxe**：十条真实历史 Bug，对比字符串搜索与 -S/-G 找到首次引入代码的时间。

---

## 参考资料

**公开批次与时间：** [arXiv cs.RO 2026-11-19 列表](https://arxiv.org/list/cs.RO/new) · [arXiv cs.SE 2026-11-19 列表](https://arxiv.org/list/cs.SE/new)。

**SLAM、状态估计和终端定位：** [Facet-SLAM](https://arxiv.org/abs/2611.23935) · [Facet-SLAM 源码](https://github.com/edward62740/Facet-SLAM) · [SBEE](https://arxiv.org/abs/2611.24310) · [毫米级 LiDAR/AprilTag 对接](https://arxiv.org/abs/2611.24191)。

**安全与多机器人：** [FMCW Doppler-CBF](https://arxiv.org/abs/2611.23654) · [PIBT*_T](https://arxiv.org/abs/2611.23911) · [PIBTT2 源码](https://github.com/tzy82065/PIBTT2) · [Control-Aware Hyperplanes](https://arxiv.org/abs/2611.23867)。

**无人机与世界模型：** [CommDreamer](https://arxiv.org/abs/2611.24244) · [AeroCity-RT](https://github.com/ppppyq/AeroCity-RT) · [ProbeShare](https://arxiv.org/abs/2611.24229)。

**AI Coding / 工程框架：** [torchtest2 论文](https://arxiv.org/abs/2611.23273) · [torchtest2 源码](https://github.com/Hrehory/torchtest2) · [Git log 官方手册](https://git-scm.com/docs/git-log)。

**经典论文：** [PIBT IJCAI 2019](https://doi.org/10.24963/ijcai.2019/76) · [PIBT AI 2022](https://doi.org/10.1016/j.artint.2022.103752)。
