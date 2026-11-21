---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-21"
date: 2026-11-21 09:00:00 +0800
description: "多机器人LiDAR初始配准、异构传感器时空标定、轮足登梯入口记忆、ROAM野外导航、CHAC按需推理、约束MPC蒸馏和LocoMuJoCo；附可核验证据组件与Codex C++实操。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-21

## 摘要

**日期：2026-11-21，Asia/Shanghai。** 截至本次检索，arXiv `cs.RO/new` 与 `cs.SE/new` 的最新常规公开批次均为 **2026-11-20（星期五）**，分别有 **140 项 / 79 项新提交**与 **39 项 / 20 项新提交**。列表总量包含交叉收录、修订论文，不能将它们都视作首次发表。原始列表：[Robotics](https://arxiv.org/list/cs.RO/new)、[Software Engineering](https://arxiv.org/list/cs.SE/new)。

先检查最新 24 小时，再核对最近 7 天及项目源码。与 GitHub 既有 **1,417 条**索引按标题、arXiv ID、DOI、仓库和主页联合去重，以下 **8 项主动态均为首次覆盖**。论文 v1 实际主要提交于 **11 月 18—19 日 UTC**，因此按规范标注**时间回补**，不把 11 月 20 日 arXiv 公布日混同于原始提交日。

**今天三个最有价值的结论：**

1. **定位成功与几何正确不是同一件事。** TU Darmstadt 的多机器人 LiDAR 初始配准在 KISS-Matcher/GICP 后再做实体互相可见性检查；复杂走廊中的假匹配应被拒绝，而不是总要生成一条看似精确的 TF。
2. **跨楼层/登梯的入口姿态是导航状态的一部分。** Passage-Conditioned Navigation 只利用一次成功示教的入口位置和朝向，就能在每次局部重规划后守住登梯技能的启动条件，不需要改动厂商步态。
3. **大模型、RL 与确定性控制应按责任分层。** ROAM 用 VLM 解释语义风险、RL 执行运动；DiffMPC 蒸馏把自博弈策略放进显式约束；CHAC 在允许的条件下减少多模态推理请求，省下的时间不能以失去可恢复性为代价。

**优先动手：** [I See You](https://github.com/tu-darmstadt-ros-pkg/i-see-you-registration)、[LocoMuJoCo](https://github.com/robfiras/loco-mujoco)、[CHAC](https://github.com/phare111/chac)。本次核验了官方 README 与运行入口，但未实际安装、训练或运行真机，也未调用 Codex。

## 1. I See You：单帧多机器人 LiDAR 配准后，用“互相看得见”否决假位姿

**时间回补：arXiv v1 2026-11-19 15:40 UTC；SSRR 2026。**

### 为什么重要

多台机器人在同一个集结区启动时，常没有共享 RTK、全局地图或足够长的共同轨迹。单帧 LiDAR 全局配准在重复走廊、对称空间容易把错误假设拟合出很低的点云残差；若直接发布到 `/tf_static`，后续的多机地图和路径规划就可能整体错位。

这项研究不只优化点云，而是将**可证伪的物理关系**用于约束。任意一对机器人先用 KISS-Matcher 粗配准、GICP 精配准，再检查两车几何包围盒是否重叠，以及机器人 A 如果声称位于机器人 B 的扫描可见区域，B 的测量中是否确实出现对应实体。通过的候选边组成最大生成树，再作位姿图优化。无法可靠配准的机器人宁可暂不发布 TF。

### 算法、传感器与鲁棒性

```
静止机器人 A/B/C/D：各一帧重力对齐 LiDAR
             ↓
全部机器人对：KISS-Matcher → GICP
             ↓
车体包围盒检查 + 双向观测/视场检查
             ↓
拒绝不可能的配准边
             ↓
最大生成树 + Pose Graph
             ↓
人工确认，发布跨机器人静态 TF
```

需要每台机器人一帧稳定点云、车体尺寸估计、准确传感器视场和重力对齐。**接受检查不等于证明配准正确**；遮挡、视场估错、低线数稀疏点云仍可能让错误位姿漏过。这个算法是**多机器人启动时的坐标系对齐**，不是同一底盘三雷达逐帧建图的直接替代品。

### 实验、源码与最小复现

作者用四台同步机器人、七类真实场景及真值验证：物理检查拒绝超过三分之一的错误配准，对正确配准的误拒绝率低于 1%，包含错误机器人位姿的团队注册结果减少 **38%**；这里的百分数不是配准 ATE 下降幅度。

官方 [MIT 源码](https://github.com/tu-darmstadt-ros-pkg/i-see-you-registration) 已核实，面向 **Ubuntu 24.04 + ROS2 Jazzy**，有 [四机器人数据](https://tudatalib.ulb.tu-darmstadt.de/items/20fc6be7-d17c-4aee-8b3b-cd77c7400795) 和已接受/被拒绝两组示例。最低起点：

```bash
sudo apt install ros-jazzy-gtsam libpcl-dev libflann-dev liblz4-dev libtbb-dev libyaml-cpp-dev
cd ~/ros2_ws/src
git clone https://github.com/tu-darmstadt-ros-pkg/i-see-you-registration.git
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select multi_robot_lidar_registration
# 无可选图形依赖时启动使用 gui:=false
```

随后对照作者 README 的 `lab/2026-05-21_10-45-56` 与 `walkway/2026-05-21_10-52-54` 快照，比较打开/关闭 `mutual_observation_check` 的错误接受率、漏配准率和 P95。源码构建期间还会下载 KISS-Matcher 和 small_gicp。

### 适合谁关注与工程落地启发

适合多机器人巡检、救援与多 LiDAR 地图初始对齐。已有精确局部定位时，可以把“配准必须可物理证伪”的思想应用到**多雷达外参验收和跨楼层回环准入**，避免仅凭 GICP Score 接受错误约束。

来源：[论文](https://arxiv.org/abs/2611.26276) · [项目](https://tu-darmstadt-ros-pkg.github.io/i-see-you-registration/) · [源码](https://github.com/tu-darmstadt-ros-pkg/i-see-you-registration)。

## 2. Reference-Twist Calibration：不匹配跨传感器特征，也能联合估计 Radar/Event/IMU 时空外参

**时间回补：arXiv v1 2026-11-19 13:24 UTC。**

### 为什么重要

毫米波雷达观测 Doppler 速度、事件相机观测法向光流，IMU 观测加速度和角速度；这些传感器很难直接找到统一的几何特征点。作者把它们共同响应的**刚体运动速度 Twist**作为中间表示，使用一个可信参考 Twist 条件化地估计两台 Radar、一台事件相机和两台 IMU 的旋转、杠杆臂、时间偏移以及各自偏置/尺度。

### 算法、可观测性和实时性

```
外部可信的机体 Twist(t)
         ↓
Radar Doppler / Event Normal Flow / IMU
         ↓
参考速度条件化的多模态残差
         ↓
旋转、Lever Arm、Δt、Bias/Scale 联合估计
         ↓
条件可辨识性/CRLB 界与残差检查
```

论文显式比较联合与参考条件化求解，给出参数可辨识性及 Cramér–Rao 下界层面的分析，并在室内、森林和分轴激励数据上评价退化、时差及参考错误敏感性。摘要没有通用可引用的外参角度误差或实时 CPU P99，本期不编造数字。

**重要边界：参考 Twist 不会凭空增加物理可观测性。** 如果仅作直线匀速运动，部分 Lever Arm 与时间偏移不可辨识；如果参考里程计本身有系统偏差，估计也将被偏置。它不意味着无需可靠时间戳。

### 可复现性与工程启发

论文指向一个匿名代码镜像，但此次访问仅得到占位页面，**无法确认完整仓库、许可证及可执行命令**。建议先用离线 Bag 进行小型验证：给真实 Twist 与各传感器时间戳人为增加 0/5/20/50 ms 偏移，设置分轴与混合激励段，比较外参稳定性、残差一致性和条件数，再考虑接入完整在线系统。

适合毫米波 Radar、事件相机、IMU 及多传感器联合标定。对三 LiDAR 平台主要价值是**把时差/外参与运动激励一起验收**，不建议未经验证就替换现有标定链路。

来源：[论文](https://arxiv.org/abs/2611.26083) · [作者提供的代码镜像入口（状态待核实）](https://anonymous.4open.science/r/xxxx)。

## 3. Collision-Free Is Not Enough：轮足登梯不只需无碰撞路径，还必须记住每级台阶的入口姿态

**时间回补：arXiv v1 2026-11-19 09:17 UTC。**

### 为什么重要

路径从当前点绕过障碍后，仍可能以错误的朝向或横向偏移抵达台阶；即使有厂商成熟的登梯 Skill，入口姿态不匹配也可能导致卡住或摔倒。

作者不训练新步态，也不要求取得厂商动力学模型，而是将**一次成功登梯的入口**记为可重复使用的事件约束。每次局部路径重规划后，在关键台阶前设置 Entry Gate：位置偏差大于 **10 cm** 或航向差大于 **10°**，就转向、后退、重新接近，不允许硬闯。

### 模块与实验

```
路线示教：每个楼梯/台阶的成功入口 Pose
                ↓
路径图 + 关键地形转换事件
                ↓
局部规划/避障（可以重新规划）
                ↓
到达事件入口前检查 Δxy、Δyaw
  ├─ 合格 → 调用厂商固定登梯模式
  └─ 超界 → 退回、校正、再进入
                ↓
通过地形后解除 Gate
```

作者报告一次 **27 分钟**现场示教，在有定位扰动时合格入口比例由 **24.1% 提升至 88.6%**。接触仿真 180 次登梯中，引入入口记忆后的跌落为 0，对照为 9；现场竞赛轮足机器人在 **271 m、累计高程 7.0 m** 路线完成六次自主运行。这些都是特定运动 Skill、地图和赛道的结果，不能推断任意机器人已经保证不会摔倒。

### 可复现性、风险及落地

本轮未找到可独立核验的作者源码/运行入口。最小实现并不复杂：把成功入口保存为带地图帧 ID、方向、容差、Skill ID 的路标，在 Nav2/自研状态机中添加不满足则拒绝进入 Skill 的前置检查。验证逐步增加定位误差、台阶重规划和障碍绕行，记录入口达标率、回退次数、错入率、总任务时间。

**尤其适合只有 `vx/vy/wz` 与“登梯模式”SDK 的轮足机器人。** 关键风险是参考地图和局部定位错误会把 Entry Gate 带偏；失败时应停在安全区，不得无限后退或强制运行。

来源：[论文](https://arxiv.org/abs/2611.25788)。

## 4. CHAC：冻结导航策略，根据环境变化决定何时更新 Action Chunk

**时间回补：arXiv v1 2026-11-19 06:31 UTC。**

### 为什么重要

多模态导航模型每走一小步就重新推理，会产生大量重复计算；一次执行完缓存的多个 Waypoint 又可能错过新障碍、已到达目标或执行偏差。

Cognitive-Horizon Action Chunking（CHAC）为冻结的 OmniNav Flow 策略添加**无需重新训练**的执行层：从旧视觉上下文、Waypoint 到达预测和控制反馈中判断何时应该刷新导航推理，并在 STOP 时根据局部访问历史允许一次有界补救移动。

### 实验和可运行性

在 HM3D-OVON，作者报告 VLM 调用量下降 **33.4%**，成功率下降 **0.63 个百分点**；在 R2R-CE 调用量下降 **64.7%**，成功率下降 **10.82 个百分点**，不能只宣传省调用而隐藏成功率代价。四项真实导航任务、每方法 40 次实验中，CHAC **18/40** 成功、原生执行 **14/40**，调用次数减少 **54.9%**，GPU 推理时间减少 **49.7%**。

[CHAC MIT 仓库](https://github.com/phare111/chac) 已核实，需 Python 3.10+、OmniNav 的 CUDA/Transformers 分支、Habitat 0.2.3、单独下载模型权重与场景数据。最低入口：

```bash
git clone https://github.com/phare111/chac.git
cd chac
python -m pip install --no-deps -e .
# 按官方README设置 OMNINAV / FLOW_MODEL / OVON_DATA / SCENES
python -m chac --benchmark ovon --split val_seen \
  --omninav "$OMNINAV" --model "$FLOW_MODEL" \
  --dataset "$OVON_DATA" --scenes "$SCENES" \
  --scene 5cdEh9F2hJL --episode-id 1756 --seed 20261021 \
  --output outputs/ovon-1756
```

实际会生成 `result.json`、`steps.jsonl`、`execution.json`；本次未实际运行。不要在机器人失联或前方障碍出现时继续使用缓存动作；应将安全停止与失效回退放在高于 CHAC 的独立控制层。

### 适合谁关注与工程启发

适合 VLM/VLA 导航、异步动作块和高推理成本边缘模型。对于室内巡检、SIP Agent 的阶段式任务，同样可借鉴“**事件触发重新决策，而不是按固定周期重复问模型**”，但应量化成功率与时延的共同变化。

来源：[论文](https://arxiv.org/abs/2611.25587) · [MIT 代码](https://github.com/phare111/chac) · [OmniNav](https://github.com/amap-cvlab/OmniNav)。

## 5. LocoMuJoCo：MuJoCo、MJX、MjWarp 同一训练接口，覆盖 G1 和多种全身控制

**时间回补：论文 v1 2026-11-19 15:48 UTC；此前已存在 LocoMuJoCo 软件，本期报道的是完整新论文及公开工程状态，并非声称项目 11 月 21 日首发。**

### 为什么重要

足式动作训练经常因为 CPU MuJoCo、GPU MJX/MjWarp、人体动作重定向和真机控制接口不同而难以进行公平 A/B。LocoMuJoCo 将这些后端放在统一环境与模仿学习 API 下，可交换观察、奖励、运动控制模式、地形、随机化和训练算法。

论文列出 **9 类人形、3 类（肌肉骨骼）人体和 4 类四足**模型；当前仓库说明及扩展模型清单可能与论文统计口径不同，不应混为统一模型数量。它支持 AMASS/LAFAN1 运动重定向，官方还提供 [loco-mujoco-real](https://github.com/robfiras/loco-mujoco-real) 的 G1/AgiBot X2 Ultra Sim2Real 工具与参考训练配置。

### 架构、动力学和工程风险

```
动作捕获 / 关节轨迹
       ↓
SMPL→机器人 / 机器人→机器人 Retarget
       ↓
统一 Observation / Reward / Termination API
       ├─ MuJoCo CPU 调试
       └─ MJX / MjWarp GPU 并行
       ↓
PPO / AMP / GAIL / DeepMimic / SuperMimic
       ↓
导出与仿真回放 → 受控真机测试
```

GPU 加速不代表运动学、碰撞、接触和底盘惯性参数自动匹配真实设备。不同机器人 URDF/模型与关节限位、摩擦、质量、控制周期必须单独标定；部署需硬件急停。论文不是统一成功率 Benchmark，不在这里编造新硬件实验数字。

### 最小复现

官方 [MIT 源码](https://github.com/robfiras/loco-mujoco) 与 PyPI 安装入口已核实：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install loco-mujoco
# Python 中可先 import loco_mujoco，按官方教程建立一个 UnitreeG1 仿真
```

仓库特别提醒 JAX 的 CUDA 依赖兼容，当前推荐版本形如 `pip install "jax[cuda12]<=0.10.1,!=0.10.0"`；具体以当前安装环境与 README 核对。机器人模型初次创建通常下载约 200 MB；AMASS 与部分人体模型另受许可约束。先跑一个 CPU 仿真，再在 GPU 对相同地形与动作参考比较 Success、接触稳定性、训练耗时和显存，最后再考虑真机。

### 适合谁关注与工程落地启发

适合 G1、四足/轮足底盘动作学习与 Sim2Real。值得研究的是**数据、动作、物理模型和训练后端统一**，不意味着厂商登梯 SDK 可以直接被新策略取代。

来源：[论文](https://arxiv.org/abs/2611.26293) · [官方代码](https://github.com/robfiras/loco-mujoco) · [部署配套](https://github.com/robfiras/loco-mujoco-real)。

## 6. DiffMPC + DAgger：将自博弈 RL 的驾驶能力蒸馏到有显式约束的学生控制器

**时间回补：arXiv v1 2026-11-18 21:17 UTC。**

### 为什么重要

自博弈 PPO 可以学到有效驾驶行为，但纯策略输出的几何约束不易检查。Differentiable MPC 能在解算时处理道路边界、周围车辆与动力学限制，却通常需要昂贵的在线 RL 或大量预先标注的教师轨迹。

作者保留 PPO 教师的特征主干，将动作输出层替换为 **DiffMPC**，用 DAgger 在原自博弈模拟器里反复收集学生会到达的状态，从而训练受约束学生。

### 算法与实验

```
已经训练好的 PPO 教师主干
             ↓
DiffMPC 学生动作头
  道路半平面 / 他车椭圆障碍
             ↓
在教师自博弈环境中运行学生
             ↓
DAgger 收集偏离后的状态
             ↓
蒸馏、约束检查、闭环评测
```

在 9 个随机种子下，较小教师的学生在 nuPlan 与教师相当，在 CARLA 和 Waymo OOD 场景优于教师；更强教师的学生在 nuPlan、Waymo 失败更少，CARLA 持平。蒸馏训练时间不超过教师训练时间的 **30%**。这里指作者对照的**再训练成本**，不是在线 MPC 推理加速倍数。

### 理论、鲁棒性及可复现性

半平面与椭圆约束对车辆外形和预测不确定性是近似。即使 QP 可行，也不能保证模型误差、动态障碍或闭环延时下无碰撞。论文没有明确可独立核验的完整官方源码，本期不提供猜测的 GitHub 命令。

可用一个二维非完整底盘或自车仿真先做最小实验：固定策略 Encoder，将输出由 MLP 改为有速度/障碍约束的局部 QP/MPC，再用 DAgger 收集约束诱发的分布变化。比较动作差异、碰撞、约束超限、P95 与再训练样本数。

### 适合谁关注与工程落地启发

适合 MPC/RL 混合控制、高速底盘及具备既有教师策略的项目。建议从**冻结策略 + 确定性约束层**的 A/B 起步，不要为了蒸馏而重做全部强化学习基础设施。

来源：[原论文](https://arxiv.org/abs/2611.25197)。

## 7. ROAM：VLM 理解野外通行语义，开放词汇风险图与 RL 局部控制各司其职

**时间回补：arXiv v1 2026-11-18 UTC；Science Robotics 2026 作者版本。**

### 为什么重要

足式机器人能凭几何识别坡度，却不容易仅用高度图判断“禁止通行标识”“湿滑地面”“道路是否封闭”等具有语义的风险。

ROAM（Robust Open-world Autonomous Mobility）让 VLM 在较低频率解释图像和标识，生成语义标签及对应通行成本；开放词汇分割把标签稠密投影为实时风险图；两个经过仿真强化学习训练的策略负责局部导航和运动执行。

### 架构、感知与实验

```
现场 RGB → VLM 场景/标识解释
                 ↓
语义类别、场景风险及通行成本
                 ↓
开放词汇分割 → 稠密 Risk Map
                 ↓
仿真训练的局部 Navigation RL
                 ↓
仿真训练的 Locomotion RL
                 ↓
腿足控制与状态反馈
```

作者报告在真实阿尔卑斯及城市复杂地形开展**公里级**野外自主徒步，能够识别标识、判断风险并选择可落脚地形。这是指定真实演示，不应推成全地形无干预保证。VLM 的语义推断可能错误，分割也可能在新场景失效，底层必须保留独立障碍与稳定性保护。

### 开源与最小验证

[公开论文](https://arxiv.org/abs/2611.25215)及[项目页](https://roam-hiking.github.io/)已经核实，但本轮未证实可一键部署的完整 ROS2 源码、权重和训练配方。适合先复现**语义成本图 Sidecar**：将 VLM 输出限制为人工审查过的地形/标识类别，在固定相机图像和已知 LiDAR 高程图上生成语义权重，比较是否减少误通行，同时统计类别误判和全链路延迟。

### 适合谁关注与工程落地启发

适合轮足野外巡检、越野语义导航及 VLA 导航分层。对已有三雷达系统，先把语义信息放在**规划成本**层，不能覆盖 IMU/LiDAR 主定位或紧急停止。

来源：[论文](https://arxiv.org/abs/2611.25215) · [作者项目](https://roam-hiking.github.io/)。

## 8. Old-School Planners：16 种传统路径与轨迹组合，部分闭环场景反而胜过学习式规划

**时间回补：arXiv v1 2026-11-18 20:18 UTC。**

### 为什么重要

越来越多自动驾驶/机器人论文只替换一个端到端策略，却常把感知、数据量与规划器同时变化。这样即使最终指标提升，也难判断收益究竟来自哪里。

作者固定感知输入，将四种路径来源（参考线、A*、Hybrid A*、RRT*）与四种轨迹方法（Frenet lattice、非线性优化、s-t 搜索、Dynamic Window）组合为 **16 种传统规划器**，在 nuScenes、nuPlan 和 HUGSIM 对照。

### 关键结果与边界

在 HUGSIM 中，传统规划器只替换 UniAD 的规划层，使用同一个冻结感知；其中 **9/16** 种高于学习规划器。最佳组合为 **Hybrid A* + 非线性轨迹优化**，HD-Score **32.0→41.8**。在 UniAD 规划发生碰撞的 182 次运行中，有 **31 次**最佳传统规划器能在同样感知下完成路线，说明部分失败可归因于规划层。但面对主动驶向自车的对手时没有明显收益。

另在作者指定 nuScenes 开环实验中，传统方案 L2 **0.735 m** 对 UniAD **0.947 m**；nuPlan Test14-hard 的指定分数 **79.3** 对 PDM-Closed **76.1**。这些分数来自不同基准，不能直接相加或推广为全部驾驶场景传统方法更好。

### 可复现性与落地

论文未给出本轮可独立核实的完整十六规划器官方仓库。可在已有 ROS2/仿真中**冻结感知和场景**，用同一组点云/障碍目标对比 A* + MPC、Hybrid A* + MPC、采样式 MPPI 及学习式轨迹头，记录通过率、碰撞、控制 P99 和退化路径。重点让“Planner 更好”与“Sensor 更好”可分辨。

适合机器人局部规划、自动驾驶/越野路径优化和学习式端到端方案的工程验收。

来源：[原论文](https://arxiv.org/abs/2611.25138)。

## AI / LLM 附属框架与开源工程组件

### Filing-Evidence：给小模型答案附上机器可验的原文证据，但还要检查单位与时间列

**时间回补：论文 v1 2026-11-18；首次覆盖。** 论文：[Show Your Work](https://arxiv.org/abs/2611.24990)，代码：[pramana-research/filing-evidence](https://github.com/pramana-research/filing-evidence)，数据：[Hugging Face](https://huggingface.co/datasets/pramana-research/filing-evidence)。

**痛点。** RAG/Agent 给出正确段落并不代表最终抽取值正确；尤其数字含单位、时间区间与表格列时，错误也可能附着在真正存在的证据后。Filing-Evidence 建立 **1,000 个问题、90 份 SEC 文件、45 家公司**的证据基准，答案以 XBRL 标签为真值，模型必须给数值、页码和原文引句。

**关键模块与 Benchmark。** 运行链路是 `EDGAR/iXBRL → 冻结数据集 → 本地 vLLM 模型输出 → 页面/引句/值校验器 → 错误类型和报告`。作者在一张 RTX 4090 上评估十个 7–21B 开放模型；最佳方案 Qwen3.5-9B 达到 **84.5%** 的有证据答案正确率。仍有每千题 **16–167** 个错误数值通过自动检查：部分错误把量纲或千/百万比例搞错，部分取了相邻年份列。**证据存在 ≠ 事实正确，更不等于代码修改正确。**

**开源/许可/最低入口。** GitHub 提供 Apache-2.0 代码、预注册 Protocol、完整回答结果以及重评分脚本；数据采用 CC BY 4.0，模型权重各有独立许可。无需 GPU 即可重新评分已有答案：

```bash
git clone https://github.com/pramana-research/filing-evidence.git
cd filing-evidence
uv sync --all-extras
uv run python hf_data.py pull
uv run pytest
uv run python runner.py qwen3.5-9b C1 --regrade
```

重新推理需相应模型、RTX 4090 量级 GPU/vLLM；部分受限模型还需要 Hugging Face Token。上述命令已从官方 README 核对，但本次未实际安装/执行。

**对 Codex/T3 Code 的价值和 A/B。** 不应拿 SEC 领域 Benchmark 当 C++ 代码检索准确率。可仿照其独立 Checker 做一个项目事实核查器：每个回答必须给文件路径、行号、原文、所声称的参数值，再由脚本校验数字单位、版本和数据来源。准备 20 个带过期配置/错误版本的问答，比较无证据回答、引用检查和语义/数值双重检查的误报率与总耗时。

**风险。** 自动脚本也无法证明所有复杂解释正确；检索库中的不可信文本不能当作指令。项目是研究基准与工具集，**不是能直接替换 SAG2 的通用 RAG MCP**，也不是零成本模型。

## AI Coding 实战技巧精选

### 技巧 1｜Codex 修改 ROS2/C++ 后，优先重跑失败 CTest，而不是全仓重复测试

- **来源**：CMake 作者官方 [CTest 命令文档](https://cmake.org/cmake/help/latest/manual/ctest.1.html)，工程补充回顾，非当日新版本。
- **一句话结论**：让 Codex 每次小修复先执行之前失败的用例，最终再跑完整回归；量化缩短的反馈周期，而不是只减少日志。
- **具体怎么做**：

```bash
cmake -S . -B build -G Ninja -DBUILD_TESTING=ON
cmake --build build -j
ctest --test-dir build --output-on-failure
# Codex 修复后，先重跑上轮失败列表
ctest --test-dir build --rerun-failed --output-on-failure
# 确认修复后执行完整回归
ctest --test-dir build --output-on-failure
```

- **适合什么场景**：Codex、T3 Code Worktree、C++/ROS2 多模块编译测试。A/B 统计首次故障反馈时间、总回归时间和漏测。
- **注意**：`--rerun-failed` 复用上轮失败清单，**不能替代最终全量测试**；项目需实际启用 CTest 测试发现。

### 技巧 2｜为改动文件执行 clangd --check，提前发现丢失头文件与编译数据库错误

- **来源**：LLVM clangd 官方 [System Headers 指南](https://clangd.llvm.org/guides/system-headers)、[Compile Commands](https://clangd.llvm.org/design/compile-commands)，工程补充回顾。
- **一句话结论**：Codex 更改 C++ 接口后，先用真实编译命令解析本次源文件；比让模型猜测缺失的 Include 路径更可验证。
- **具体怎么做**：

```bash
cmake -S . -B build -G Ninja \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
clangd --check=src/localization.cpp \
  --compile-commands-dir=build
# 之后仍编译真实目标
cmake --build build --target your_target
```

- **适合什么场景**：Arch Linux、CLion、Codex、ROS2/C++ 大仓库，尤其 Header 与编译参数差异造成的假阳性。
- **注意**：clangd 出现 `Generic fallback command` 常说明未正确找到编译数据库；该静态诊断**不等于编译、链接与运行时测试**。跨编译或 CUDA 源文件更需核对编译器兼容。

## 经典论文回顾

### Fast Global Registration — Zhou、Park、Koltun，ECCV 2016

**历史位置。** Qian-Yi Zhou、Jaesik Park、Vladlen Koltun，ECCV 2016，页 766–782。原论文：[DOI](https://doi.org/10.1007/978-3-319-46475-6_47)，作者[论文页](https://vladlen.info/publications/fast-global-registration/)，[原始 C++ 实现](https://github.com/isl-org/FastGlobalRegistration)。

**核心问题。** 两片部分重叠点云的初始相对位置未知，局部 ICP 容易落入错误极小值；候选匹配中又有大量错误。FGR 从特征匹配出发，把几何位姿和异常对应权重放入同一个鲁棒目标进行联合优化，不在内部循环反复做最近点搜索。

**关键思想。**

```
两片点云 → 特征/初始对应
             ↓
匹配几何残差 + 鲁棒非凸代价
             ↓
从平滑目标逐步提高离群点惩罚区分度
             ↓
联合求刚体 R、t 与对应可靠权重
             ↓
局部精配准 / 多点云共同注册
```

论文报告在其指定数据和对照中，精度与当时领先的全局配准管线相当或更优，速度快一个数量级以上；**不能把 2016 年实验的倍数直接当作当前 KISS-Matcher/TEASER++ 的基准。**

**传感器与假设。** FGR 不要求某种 LiDAR 型号，但依赖足够正确且有分布的初始特征对应、部分场景重叠和非退化几何。对完全相似的走廊或缺乏重叠的两片点云，低残差不代表真位姿。它不是完整 LIO、没有自动处理多雷达时间偏移和去畸变。

**当年为什么重要、今天如何使用。** 它把“全局粗配准只靠随机几何采样”的思路推进到快速鲁棒联合优化。现在可将 FGR、KISS-Matcher、RANSAC 等作为**候选位姿产生器**，再通过真实可见性、机器人几何关系、局部 GICP 和因子图一致性验收；这正是本期 I See You 的方法论关联。原始 Intel 相关仓库 **已停止维护**，虽采用 MIT 源码许可，不应默认原仓库适配最新编译器或具有生产维护保障。

**最小复现。** 从同一对 LiDAR PCD 生成正确/错误匹配，注入 10%、30%、60% Outlier 和重叠率变化，对比 FGR、RANSAC 粗配准、KISS-Matcher；统一比较旋转/平移误差、错误接受率、CPU P95、最终 GICP 精度。增加平行墙/对称建筑，验证“算法给出变换”和“物理可证伪”两类验收的区别。

**工程结论：** 对跨机器人的初始 TF 和三雷达外参，**不能把匹配得分或几何配准收敛当作可信度的全部依据**。

## 今日结论

**今日最值得动手的不是堆更多传感器点数，而是给每个环节增加明确的准入、拒绝与验收条件。**

多机器人 LiDAR 配准应该先有粗配准，再用实体关系否决错误几何；跨楼层轮足导航除了路径点，还应保存登梯入口姿态和失败退回策略；雷达、事件相机和 IMU 需要联合验证时间偏移与运动激励。ROAM、DiffMPC、CHAC 说明模型推理可以减少、规划能力可以蒸馏、语义推断可以丰富地图，但执行与安全必须仍由可监测的低层系统负责。

AI Coding 方面，Filing-Evidence 的一手实验证明“模型附上原文证据”仍可能产生数字、单位和时间列错误；对 Codex 修改，应该用真实测试、编译诊断、文件与项目状态来验收，而不是根据模型的完成宣告判断成功。

## 最值得深入研究或尝试复现的方向

| 优先级 | 方向 | 最小验收指标 |
|---|---|---|
| P0 | I See You 多机器人 LiDAR 对齐 | 成功/拒绝数据示例、错误边接受率、静态 TF 与重力对齐 |
| P0 | Passage-Conditioned 登梯入口守门 | 入口位置与航向误差、回退次数、真实 Skill 成功率 |
| P0 | LocoMuJoCo G1/四足统一仿真 | CPU/GPU 环境一致性、接触稳定性、显存与训练时长 |
| P1 | Radar/Event/IMU 时空联合标定 | 注入 0/5/20/50 ms 偏移、可观测性和残差 |
| P1 | CHAC 动作段刷新门控 | 推理调用数、任务成功率、障碍出现后的停止延迟 |
| P1 | DiffMPC + DAgger | 约束超限、控制 P95、教师调用与再训练成本 |
| P1 | ROAM 语义风险 Sidecar | 语义错误率、误通行率、规划延迟 |
| P1 | 传统 Planner 与学习 Planner A/B | 固定相同感知的通过率、碰撞、P99 |
| P1 | Filing-Evidence 式证据校验 | 数值/版本/单位错引检测率和检索成本 |
| P1 | Codex CTest/clangd 快速验证 | 首次失败定位时间、最终回归与误诊断 |
| P2 | FGR 经典全局配准 | Outlier/重叠率变化下的误配准和 CPU 开销 |

## 参考资料

**公开原始列表：** [arXiv Robotics 2026-11-20](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering 2026-11-20](https://arxiv.org/list/cs.SE/new)。

**几何、标定、跨楼层导航：** [I See You](https://arxiv.org/abs/2611.26276) · [代码](https://github.com/tu-darmstadt-ros-pkg/i-see-you-registration) · [时空校准](https://arxiv.org/abs/2611.26083) · [Passage-Conditioned](https://arxiv.org/abs/2611.25788)。

**导航/控制与仿真：** [CHAC](https://arxiv.org/abs/2611.25587) · [CHAC 代码](https://github.com/phare111/chac) · [LocoMuJoCo](https://arxiv.org/abs/2611.26293) · [代码](https://github.com/robfiras/loco-mujoco) · [DiffMPC+DAgger](https://arxiv.org/abs/2611.25197) · [ROAM](https://arxiv.org/abs/2611.25215) · [Old-School Planners](https://arxiv.org/abs/2611.25138)。

**AI 工程组件、实战：** [Filing-Evidence 论文](https://arxiv.org/abs/2611.24990) · [Apache-2.0 源码](https://github.com/pramana-research/filing-evidence) · [CTest 官方文档](https://cmake.org/cmake/help/latest/manual/ctest.1.html) · [clangd 文档](https://clangd.llvm.org/guides/system-headers)。

**经典论文：** [Fast Global Registration，ECCV 2016](https://doi.org/10.1007/978-3-319-46475-6_47) · [历史源码](https://github.com/isl-org/FastGlobalRegistration)。
