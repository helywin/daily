---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-15"
date: 2026-11-15 09:00:00 +0800
description: "多无人机地形概率搜索、HeadIO惯性里程计、GP信息路径规划、SPARC开放救援导航、BlinkMimic、NSDL、HDH；Robo-SWE及Coccinelle语义补丁；Codex差分回归测试。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-15

## 摘要

**日期：2026-11-15（星期日，Asia/Shanghai），早间检索。** arXiv Robotics（cs.RO）及 Software Engineering（cs.SE）的 `/new` 页面最新常规批次均为 **2026-11-13（星期五）**：cs.RO 总计 164 条、新投稿 91 条；cs.SE 总计 86 条、新投稿 39 条。总数包括交叉收录及更新版，不能都当成首次投稿（[cs.RO 当日列表](https://arxiv.org/list/cs.RO/new)、[cs.SE 当日列表](https://arxiv.org/list/cs.SE/new)）。

检索先查最近 24 小时；由于周日没有新的常规 arXiv 批次，扩展至最近 7 天，对照 GitHub 现有 **1,345 条**历史索引，以规范化标题、arXiv ID、DOI、官方代码仓库、主页联合排重。下述七项技术原始 v1 均于 **11 月 10—12 日 UTC** 提交，全部按规范标为**时间回补**，不把今天的简报日期当作论文首发日期。

**本期技术主线**：① 多无人机探索不应只按几何覆盖率，还要考虑地形先验和遮挡可见性；② 惯性里程计要区分绕竖直轴旋转与头部倾斜；③ GP 信息路径规划用后验方差直接评价采样价值，而不是盲目最大化看似高级的熵指标；④ SPARC 真正提供了双 LiDAR/IMU、ROS2、Zenoh 的救援机器人数据和源码；⑤ G1 全身动作跟踪的训练过程可以通过优化失败重置和 CUDA Graph 显著缩短；⑥ 多机器人任务规划将视觉状态判断交给小 VLM，将调度约束交给确定性求解器；⑦ 冻结 VLA 也能用轻量 Action Verifier 筛选候选动作。

**工程优先级**：首选 [NSDL](https://github.com/Xincheng-Tan/NSDL) 的无 GPU 规划器单测和 [SPARC](https://github.com/STAR-Explorer-Robotics/Robocup_system) 双 LiDAR Bag；有 NVIDIA GPU 的环境再验证 [BlinkMimic](https://github.com/fuyichen0725/blinkmimic)。AI Coding 部分选 [Robo-SWE](https://huggingface.co/datasets/vharatian/Robo-SWE) 的机器人专用可执行评测，以及可生成 Coccinelle 语义补丁的开源研究，避免无收益的 Coding CLI 版本公告。所有本文中的示例命令来自官方资料，本轮**未实际运行训练，也未调用 Codex**。

---

## 1. 地形感知 Thompson Sampling：多无人机搜索不再对每个栅格一视同仁

**时间回补｜v1 2026-11-10 19:45 UTC｜arXiv:2611.14685**

### 为什么重要

无人机灾后搜索的目标不是最大化相机拍摄过的面积，而是在有限飞行时间内尽早发现目标。地形高度、路径、流域、历史失踪人员移动规律都能提供候选区域的先验概率；树林遮挡则意味着“飞过这块区域”与“这块区域确实被可靠观察”不是一回事。

该研究把地形信息写进目标出现概率的先验，将各网格的观测更新做成局部 Gaussian 后验，再利用 Thompson Sampling 在高概率区搜索与高不确定区探索之间动态取舍。各无人机可以分布式决策，而不需要每一轮都由中心节点分配完整路径。

### 算法模块、传感器与理论假设

~~~text
地形/失踪者历史先验 → 栅格出现概率分布
                             ↓
各无人机：抽样 Thompson 后验 → 选择区域
                             ↓
航拍观测 + 林冠遮挡比例 → 观测置信度
                             ↓
每格 Bayesian 更新 → 下一轮搜索
~~~

其观察模型以分数林冠覆盖估计漏检概率；不是一个能直接处理所有视频检测偏差的通用感知模型。无人机速度、无人机之间通信和持续感知覆盖都需要按真实载体重新检验。

### 实验结果、实时性与风险

作者基于 YOSAR 真实搜索救援记录构造 1.5 km²、3.8 km² 场景，采用 5、10、15、20 台无人机、名义速度 50 km/h。小场景报告约 **87% 成功率**，完成搜索时间 60—247 秒；大场景成功率约 **75—91%**，耗时 161—466 秒。不同数字来自不同机器人数量和场景，不能把 87% 当成单台小无人机通用成功率。

算法主要验证于仿真；未核实官方完整部署仓库、通信 P99 和飞控实机成功率。空域冲突、禁飞区、电池、天气和多机防撞仍需单独安全约束。

### 最小复现、适合谁关注与落地启发

在已有 2D/3D 占据地图生成 100 个目标先验样本，先只比较固定割草覆盖、Frontier 信息增益、Thompson Sampling 三种策略；注入 0/30/60% 视野遮挡，统计首次发现时间、目标召回率、实际飞行距离和无人机任务冲突。适合激光无人机自主探索、搜救多机编队、主动感知；不能直接拿搜索效率代替避障安全证明。

**来源**：[原论文](https://arxiv.org/abs/2611.14685)。

---

## 2. HeadIO：利用机身/头部坐标系的重力分解，降低纯 IMU 里程计开销

**时间回补｜v1 2026-11-11 UTC｜arXiv:2611.14895（cs.CV，交叉收录 cs.RO）**

### 为什么重要

在相机暂时不可用的 VR/AR、头戴传感器或机器人局部惯性运动估计里，纯 IMU 神经里程计仍受到方向表示影响。直接把 IMU 变换到重力对齐的全局坐标，绕竖直轴的旋转会改变表示；使用原始 body-frame 又会把身体倾斜导致的重力投影变化与真实水平加速度混合。

HeadIO 只依赖姿态的倾斜（tilt）分量，将重力与水平运动信息在 body-frame 中分离，再用双向 Mamba 时序网络估计短时间位移；无需把完整的 yaw 作为表示前提。

### 算法模块、可观测性与边界

~~~text
IMU 加速度 + 角速度 + tilt 估计
                ↓
重力/水平分量分解（弱化 yaw 依赖）
                ↓
双向 Mamba 序列编码
                ↓
短时相对位移
                ↓
可选稀疏外部 yaw 修正
~~~

该设计针对头戴设备的姿态和运动统计，并不是替代 LiDAR-IMU ESKF 的通用状态估计器。双向时间编码还需要检查离线窗口与在线因果部署的延迟差异。纯 IMU 仍然面临偏置、漂移和绝对航向不可观测问题。

### 实验结果与可复现性

Nymeria 数据集的 **5 秒相对平移误差 RTE-5s**：所比较的 learned-equivariant 世界坐标方法 0.260 m，HeadIO 为 **0.239 m**（改善 8.1%），论文报告近 **3 倍更低 FLOPs** 和 **8 倍更少参数**。作者还报告 Nymeria 上简单陀螺仪 yaw 系数校正可降低约 11.6% 的 yaw 误差；每 30 秒提供稀疏外部 yaw 更新可进一步改善 RTE-5s。不同指标不能混为全局定位精度。

尚未核实完整开源训练代码及在普通 ROS2 传感器上的 FPS。最小复现应固定一个头戴 IMU 数据集，在同一 train/test 划分比较 world-frame、body-frame、tilt decomposition 的 RTE-5s、yaw 变化敏感性、参数量和实际端侧推理耗时。

### 适合谁关注与工程启发

适合 IMU-only 短期运动跟踪、穿戴式导航及需要方向不变性的小模型；对机器人多 IMU 系统，可借鉴坐标表达和 tilt/yaw 分离做特征前端，不能直接推断换成 HeadIO 后 LiDAR 精度会提高。

**来源**：[原论文](https://arxiv.org/abs/2611.14895)。

---

## 3. GP Informative Path Planning：信息路径应该优先降低未知区域的后验方差

**时间回补｜v1 2026-11-12 14:41 UTC｜arXiv:2611.16877**

### 为什么重要

巡检、环境采样和自主探索常用“信息增益”选择下一站，但最大化熵、互信息、GP 方差等不同指标并不总对应相同的物理测量误差。很多信息路径工作把采样点选择与路线成本混在一个经验权重里，难以解释终端地图误差真正受到什么约束。

这篇工作对 Gaussian Process（GP）下的预测误差上下界进行分析，指出**预测方差**是针对均方估计误差更直接的优化量，再研究 GreedyCover 对离散、离线、具有误差界约束的 IPP 的近似性质。

### 算法模块、假设与复杂度

~~~text
已测样本 + GP Kernel / 噪声模型
                ↓
查询区域后验均值与方差
                ↓
选择最有助于降低剩余不确定性的采样点
                ↓
GreedyCover / 路径长度与预算约束
                ↓
生成机器人访问路线
                ↓
采样后重新计算方差
~~~

理论分析假设 GP 的 Kernel、超参数或其适用条件已知，主要覆盖**离线、离散候选点**的规划问题；它不自动解决移动机器人实时重规划、动态障碍和未知传感器噪声。所谓近似保证也必须满足论文所给目标函数和约束，不能套用到任意多机器人 VRP。

### 实验与工程复现

作者在环境监测数据集与不同目标函数上比较预测方差、信息论目标和 GreedyCover，报告更好的估计误差与计算效率，但摘要没有可统一外推的百分比，本期不编造加速倍数；未确认完整官方一键工程。

建议用已有三维点云地图构造二维温度/信号强度标量场，随机放置 30—100 个候选观测位，统一 GP Kernel 与路径预算，比较均匀覆盖、最大熵、方差 GreedyCover 的留出区域 RMSE、最大方差和路径耗时。注意 GP 本身的 O(n³) 朴素核矩阵计算和超参数漂移。

### 适合谁关注与工程启发

适合无人机采样巡检、多机器人主动探索、室内信号图/温度图采集；与 Frontier 信息增益不同，这里更强调**有限传感器观测能把连续物理量重建到什么误差**。

**来源**：[原论文](https://arxiv.org/abs/2611.16877) · [论文 HTML 理论和实验](https://arxiv.org/html/2611.16877v1)。

---

## 4. SPARC：真实双 LiDAR、IMU 与救援场景 Bag，已公开 ROS2 导航源代码

**时间回补｜v1 2026-11-11 13:15 UTC｜arXiv:2611.15443**

### 为什么重要

单独的 SLAM 测试通常没有机器人整套系统的真实性：传感器时间戳、前后激光视场、控制 SDK、地形规划、任务接口和网内通信分布在不同模块。SPARC 试图以 Unitree A2-W 轮足平台和 RoboCup Rescue 标准障碍环境提供可比较的真实场景基线。

论文公开了 ICRA Legged Robot Challenge 与 RoboCup Rescue 的 Bag、点云场景，以及以 ROS2 为基础的导航系统。数据包括前后 LiDAR、Microstrain IMU、关节状态、厂商运动状态，这一点比只给一段成功演示视频更值得使用。

### 架构、数据、模块

~~~text
前/后 LiDAR + IMU / 运动状态
                ↓
定位 / 建图（SuperOdom、SuperLoc 相关实现）
                ↓
地形处理 / 可通行区 / 边界
                ↓
TRG 地形图 → 路线生成 → 跟踪
                ↓
Unitree SDK2 接口 / 运动控制
                +
ROS2 + Zenoh 分布式数据通道
~~~

公开 Bag 包含：2026 LRC 两条斜坡序列约 **392 s/12.5 GB**、**429 s/13.7 GB**，以及 RoboCup 约 **614 s/21.2 GB** 的真实记录；还有 0.07 GB、0.2 GB 的赛场点云。不同序列包含的具体 Topic 不完全相同，不能把全部传感器都视为同时存在。

### 代码与工程风险

- [SPARC 论文](https://arxiv.org/abs/2611.15443)
- [STAR-Explorer-Robotics/Robocup_system](https://github.com/STAR-Explorer-Robotics/Robocup_system)
- [LRC 数据](https://doi.org/10.5281/zenodo.23002951)
- [RoboCup Rescue 数据](https://dx.doi.org/10.21227/e01k-mf43)

已核实仓库包含 `localization`、`terrain_processing`、`terrain_planning`、`path_following`、`robot_interface`、`mission_control`、`perception` 等目录。

**作者 README 明确声明这次发布是“源码组织版”，重组后的树尚未验证为完整可运行部署。** 不应写成“git clone 就能一键启动 A2-W 自主巡检”。厂商速度接口、地形运动学、安全急停也不可脱离机器本体直接复用。

### 最小复现、适合谁关注

先下载一段最小 Bag，核实 `ros2 bag info`、TF、前/后雷达时间戳和 PointCloud2 字段，再在独立分支里把两个雷达送进已有的融合/定位框架。固定同一参考地图比较单前雷达、单后雷达和两雷达的退化指标、可观测方向、注册耗时及地图存储。

尤其适合已经具有多 LiDAR 和轮足 SDK 的机器人研发，不必为了使用数据购买同型号硬件。

---

## 5. BlinkMimic：G1 全身动作跟踪，40 段动作在单 RTX 4090 上数分钟完成训练

**时间回补｜v1 2026-11-12 07:31 UTC｜arXiv:2611.16422**

### 为什么重要

传统运动模仿 RL 需要大量模拟环境步骤。SuperMimic 和 InstantTrack 已展示世界模型可微 rollout 带来的训练加速，BlinkMimic 在此基础上继续调整优化过程、采样重置分布和 GPU 图捕获，减少每轮训练成本与完成所有困难动作的迭代次数。

### 算法模块与关键假设

~~~text
40 段 LAFAN1 参考动作
            ↓
mjlab / MuJoCo Warp 并行世界模型
            ↓
可微动作跟踪 + residual policy
            ↓
分阶段学习率 + 失败导向 reset
            ↓
CUDA Graph 捕获训练迭代
            ↓
稳定部署策略 / 全片段评测
~~~

它针对**模拟 Unitree G1**，不是证明真机动作跟踪的安全控制器。先明确真实机器人质量、关节限位、接触和 SDK 接口，再讨论 sim-to-real。

### 实验结果

作者使用 RTX 4090、CUDA 12.8、PyTorch 2.9、40 条 LAFAN1（2.45 h 动作）按三随机种子测试。达到归一化 Return ≥ 0.82 的平均训练时间约 **2.94 min**；达到“连续 3 个 Checkpoint Return ≥0.82 且 40 段无失败”的严格条件约 **3.38 min**；InstantTrack v1.2 对照严格条件为约 **7.36 min**。

注意 3.38 分钟是作者定义的训练阶段时长，包含编译、图捕获和检查点，排除进程启动及数据加载；不是 40 段动作在真实 G1 上播放的时间，也不是任何 GPU 都能做到的通用速度。

### 已核实官方源码与运行

[论文](https://arxiv.org/abs/2611.16422) · [fuyichen0725/blinkmimic（MIT）](https://github.com/fuyichen0725/blinkmimic)。

~~~bash
git clone https://github.com/fuyichen0725/blinkmimic.git
cd blinkmimic
uv sync
uv run python tools/test_env.py
bash scripts/train.sh logs/run_s0 --seed 0
uv run python tools/eval_batch.py --run_dir logs/run_s0 --group 18 --reps 4
~~~

需要 CUDA、MuJoCo Warp 和对应驱动支持；本次只核实 README 与命令，**没有执行训练或占用 Codex 额度**。

### 适合谁关注与工程落地

适合 G1 运动跟踪、GPU 加速 RL、Sim2Real 训练工具链。最小 A/B 是固定同一任务和训练预算，对比开启/关闭失败重置、学习率策略与 CUDA Graph 的训练时长、平均回报、失败动作数、GPU 显存和接触穿透，而不是只报告最终一条成功视频。

---

## 6. NSDL：视觉小模型只负责判断“现在是什么状态”，约束调度交给确定性求解器

**时间回补｜v1 2026-11-12 11:47 UTC｜arXiv:2611.16671**

### 为什么重要

多机器人长任务通常涉及两种本质不同的决策：机器人是否已经到达、箱子是否已搬走、哪台设备可用，这些需要视觉与语义判断；某项动作必须在另一动作之后执行、何时交接、是否资源冲突，则属于可由确定性求解器检查的结构性问题。

NSDL 不让 VLM 直接生成最终动作时间表。它将小型 VLM 输出约束在带有 `[GOAL]`、`[ASSIGN]`、`[SKETCH]` 的计划草图里，再让 Planner 生成正式联合执行计划；还提供 `detect` 和 `schedule` 两个工具，训练时可以将 Solver 纳入工具循环。

### 算法模块

~~~text
场景图像 + 自然语言指令
              ↓
3B / 7B / 8B VLM：状态判断与任务分配
              ↓
Plan Sketch（GOAL、ASSIGN、SKETCH）
              ↓
确定性 Solver：先决条件、资源冲突、交接、排序
              ↓
联合多机器人执行计划
              ↓
回读新观测，重新检查任务状态
~~~

### 实验和理论边界

论文在 VIKI-L2 与作者新建的 LOCUS-Bench 评测，7B 版本在 VIKI-L2 的 OOD 准确率报告 **97.0%**。这个结果是指定的计划正确性协议，不是物理多机器人在未知复杂场地中有 97% 的真机成功率。

Solver 能够显著降低排序/调度错误，但**它无法纠正模型没识别到的目标**：计划草图漏掉的任务不一定会被调度器自动补出来。执行时，还需要底层导航、避障和资源锁。

### 官方工程及最小可执行验证

[论文](https://arxiv.org/abs/2611.16671) · [Xincheng-Tan/NSDL 官方代码](https://github.com/Xincheng-Tan/NSDL)。

已核实项目包含：`nsdl/tool_runtime.py`、`planning_tool.py`、`micro_planner.py`、`macro_graph.py`、`validator.py`、数据构建脚本、训练配置、LOCUS-Bench，以及 Hugging Face 3B/7B/8B 权重。项目还给出**无需 GPU、无需下载权重的离线规划器单测**，建议优先执行项目的 `tests/`，再决定是否下载模型。

完整训练/RL 依赖 Conda、verl、视觉检测权重和较大 GPU 资源，不能把“工具层可测”误写成“全量 7B 模型低成本本地可跑”。

### 工程启发

对 SIP/GB28181 平台、巡检机器人调度、跨楼层任务，可借鉴“Agent 只判断状态，确定性模块负责号码/资源映射、先后顺序与互斥约束”的分工；先在静态 JSON 输入上测试 planner 是否拒绝不可能的任务，再让 VLM 接真实世界。

---

## 7. HDH：冻结 VLA 时，先用历史执行结果训练一个低延迟候选动作验收器

**时间回补｜v1 2026-11-10 23:32 UTC｜arXiv:2611.14834**

### 为什么重要

VLA 一次生成的 Action Chunk 可能无效，但每一步都用另一个大型 VLM 检查候选动作会增加控制延迟。HDH（Hindsight-based Action Verification）利用冻结策略自身执行过的轨迹训练小型成功率打分器，候选动作可在执行之前经过快速排序。

### 算法模块

~~~text
冻结 VLA 自主 Rollout + 成败结果
                ↓
训练紧凑候选动作评分器
                ↓
同一观测由冻结 VLA 采样多条 Action Chunk
                ↓
评分候选的任务成功可能性
                ↓
选择相对高分候选并执行
                ↓
重新观察，继续验证
~~~

### 实验结果和风险

作者在四个 LIBERO-10 任务中报告平均 **82.3%** 成功率；三个真实机械臂任务中，相对冻结的原始 VLA 平均成功率提高 **22.6%**（以论文原文指标为准，不自行换算为百分点）。摘要未给出所有模型统一的评分器 P99、独立端侧 GPU 和真实接触安全指标；完整训练仓库尚未核实。

评分高不代表轨迹没有碰撞。候选动作若全部不可行，排序器仍可能选出一个“最不坏”的方案；应加入确定性安全过滤器与允许全部拒绝的逻辑。

### 最小复现与适合谁关注

使用原有冻结动作策略产生 100—300 组带标签的失败/成功 Chunk，训练小型二分类/回归评分器，对比原策略首选、随机选候选、学习评分器选候选的成功率、误报和额外 P95。适合 VLA 后训练、动态操作与“先动作验收再执行”的工具架构，不应直接控制真实夹爪的不可逆动作。

**来源**：[原论文](https://arxiv.org/abs/2611.14834)。

---

## AI / LLM 附属框架与开源工程组件

### 组件 1｜Robo-SWE：用真正可执行的 ROS2 / 机器人项目 Issue 评测 Codex，而不是只看通用 SWE-bench

**时间回补｜v1 2026-11-11 23:51 UTC｜arXiv:2611.16116**

**来源：** [原论文](https://arxiv.org/abs/2611.16116) · [公开数据集](https://huggingface.co/datasets/vharatian/Robo-SWE)。

**具体解决的痛点。** 通用 Coding Agent 基准未必覆盖 ROS2 包的构建、Gazebo/MuJoCo 环境、C++ 编译器、传感器时间与底层接口。Robo-SWE 从 **28 个机器人开源仓库**、**1,567 个候选 PR** 中筛出 **236 个可执行修复任务**，每项包含原 Issue、修复前版本、容器环境、开发者 Patch 和可靠的 Fail-to-Pass 测试。任务覆盖 ROS2、仿真物理、机器人算法和机器人学习。

作者还发布 3,540 次已评分尝试及 3,529 条可用轨迹。在此特定数据与执行协议下，GPT-6.1 Sol 最高思考配置的修复率约 **54.1%**，中等配置约 **52.5%**；这些是作者的特定实验，不是保证你本地项目达到同一完成率。基准目前未完成完整人工公平性评审。

**开源与最低应用步骤。** Hugging Face 提供 Parquet 格式和任务描述，可先挑 3 个与你的 ROS2 构建相近的任务，核对任务的 commit、镜像依赖和对应测试命令；使用任务自带的隔离容器重建修复前失败、再验证官方补丁可通过。此过程可先在不运行 Codex 的情况下进行。实际比较 Codex 前先确定实验预算与是否允许消耗额度。

~~~bash
# 只下载数据结构，先阅读卡片与文件布局；无需下载全部镜像
python -m pip install -U huggingface_hub
hf repo-files vharatian/Robo-SWE --repo-type dataset
# 按数据集卡片选定小范围任务及镜像后再运行
~~~

**工程价值与风险。** 用于识别 Coding Agent 在不同 ROS2/C++ 项目上的真实弱点，并将通过率、构建耗时、错误修改率和 Token 成本放进同一统计。避免直接把未审查的公开补丁自动并入生产仓库；容器应隔离网络及真实凭据。本次未实际下载数据或运行模型。

### 组件 2｜本地小模型 + Coccinelle：从已成功迁移的“兄弟代码”生成可审核的 C/C++ API 语义补丁

**时间回补｜v1 2026-11-12 03:08 UTC｜arXiv:2611.16215**

**来源：** [研究论文](https://arxiv.org/abs/2611.16215) · [MohannedAhmed67/kernel-sibling-migrations 官方研究代码](https://github.com/MohannedAhmed67/kernel-sibling-migrations)。

**痛点与模块。** C/C++ API 升级经常需要在几十上百个驱动/模块中做同类改动。让模型对每个文件分别重写容易产生无关变化。该方法先从 Git 历史里抽取已经被维护者审核的相邻模块迁移，按模式分组，让本地模型输出 Coccinelle SmPL 规则；确定性语法/变量修正器规范化规则，最后以**编译结果**作为硬验收。

~~~text
Git 历史中先发生的成功迁移
              ↓
按 API 变化分组 / 模式树
              ↓
本地 Qwen2.5-Coder 7B 生成 SmPL
              ↓
Coccinelle 规则运行 + 语法修正
              ↓
候选补丁 → 编译/匹配已有人工修复 → 接受或拒绝
~~~

在论文选择的 **7 类新 API 迁移、122 个留出驱动**上，Qwen2.5-Coder 7B 经框架引导，三随机种子平均解决 **35.3** 个目标；直接提示模型仅约 1.0 个；其他对照 Spinfer 41、强模型 Agent 66。这里“解决”要求既符合人工修复又能编译，不能当成任意 kernel 版本的普遍自动迁移率。

**真实代码状态与部署。** 作者的 MIT 仓库包含 Dockerfile、Makefile、规则、数据和脚本，工具链固定 Ubuntu 22.04、GCC 11.4、Coccinelle 1.1.1；README 明确 H1/H2 已完成，H3 并未运行，且原 DRIVEBENCH 工件不全公开。最低环境验证：

~~~bash
git clone https://github.com/MohannedAhmed67/kernel-sibling-migrations.git
cd kernel-sibling-migrations
docker compose build
docker compose run --rm dev make env
~~~

完整 Linux 内核数据抓取可能涉及 GB 级磁盘/网络，切忌把上面命令理解为已复现全部论文指标。

**适用场景。** Codex 辅助 C++ SDK 改造、ROS2 消息字段迁移、C 接口更名、大型跨模块一致性修改。先让 Codex 生成一条 SmPL/AST 改写规则，应用到**只读副本/隔离 Worktree**，再编译通过才允许合并。小范围手工变更不要为了“自动化”部署整套 LLM 训练框架。此代码研究使用了开源本地模型，但与 Codex 没有内置直接集成关系。

---

## AI Coding 实战技巧精选

### 技巧 1｜Codex 写回归测试必须做“两版本 Fail-to-Pass”，不能只看当前分支全绿

- **来源：** Vahid Haratian 等，2026-11-11，[ADAPT 论文](https://arxiv.org/abs/2611.16114)；[Git Worktree 官方文档](https://git-scm.com/docs/git-worktree)。
- **一句话结论：** 对已知 Bug 修复，理想回归用例应在修复前版本失败、修复后版本通过。仅在修复后通过的测试，很可能根本没验证目标错误。
- **具体怎么做：**
  1. 在独立目录准备修复前 Commit 与当前补丁，使用 `git worktree add --detach ../pre-fix <GOOD_OR_BAD_SHA>` 创建**修复前**工作树。注意这里指定的是已知存在 Bug 的 SHA。
  2. 要求 Codex 只根据需求、Diff 和具体 Bug 生成**最小相关测试**，不要自动修改生产源代码或自作主张扩大验收集。
  3. 在修复前工作树运行新测试必须失败，在修复后运行必须通过；测试需要能映射到变更行为。若始终通过，应让 Codex重新设计有区分能力的断言。
  4. 仅对改动模块跑相关编译/测试，报告 F2P 结果及未覆盖的真正修改逻辑，不要生成大量“漂亮但无效”的脚本。
- **适合什么场景：** Codex + C++/ROS2、SIP 状态机、回归 Bug、独立 Worktree。
- **注意：** 新功能与旧功能行为兼容时不一定存在有意义的 F2P 用例；不应强制把所有 PR 都塑造成失败测试。上述是可用于 Codex 的方法，不是 ADAPT 官方 Codex 插件。

### 技巧 2｜只分析改动行：clang-tidy-diff.py + Codex 做精确代码审查

- **来源：** LLVM 项目官方 [clang-tidy-diff.py 源码](https://github.com/llvm/llvm-project/blob/main/clang-tools-extra/clang-tidy/tool/clang-tidy-diff.py) · [clang-tidy 官方说明](https://clang.llvm.org/extra/clang-tidy/)。
- **一句话结论：** 在大型 C++ 仓库，只让 clang-tidy 产生此次 Diff 相关的诊断，再让 Codex修复真实问题，减少全仓历史告警污染上下文。
- **具体怎么做：**
  1. 用 CMake/colcon 生成正确的 `compile_commands.json`，确保 clang-tidy 与源码版本匹配。
  2. 取得 LLVM 官方随版本打包的 `clang-tidy-diff.py`。针对目标基线生成上下文 Diff，然后输入差分分析器：

~~~bash
git diff -U0 BASE_COMMIT...HEAD -- '*.cpp' '*.cc' '*.h' \
  | python3 clang-tidy-diff.py -p1 -path build
~~~

  3. 将确切诊断位置交给 Codex，要求先给出最小补丁与诊断原因；修复后 `git diff --check`、相关编译和最小回归必须通过。
  4. 与直接全仓库运行 clang-tidy 对比诊断条数、真实新缺陷数、检查时间和无关修改数量。
- **适合什么场景：** Codex、ROS2/C++、庞大仓库、旧代码历史告警较多的模块。
- **注意：** `-p1` 和 `-path build` 必须按工作树、编译数据库实际位置调整；差分过滤只抑制其他行的诊断呈现，不意味着分析器只读取了改动行，也不能发现所有跨文件动态故障。

---

## 经典论文回顾

### An Analysis of Approximations for Maximizing Submodular Set Functions—I（Nemhauser、Wolsey、Fisher，1978）

**发表时间及历史位置：** 1978 年发表于 *Mathematical Programming* 14(1):265—294。原始来源：[论文 DOI](https://doi.org/10.1007/BF01588971) · [DBLP 书目记录](https://dblp.org/rec/journals/mp/NemhauserWF78.html)。

### 核心问题

当机器人每次只能挑选 K 个候选观测位置，怎样避免花费指数级时间遍历所有观测组合？如果每加入一个观测点的新增收益会随着已观测位置增多而降低，就形成**边际收益递减（submodularity，次模性）**。直觉是：两台相邻摄像机拍摄大量重叠区域时，第二台新增的信息远少于第一台。

对于集合函数 `F`，如果 A 是 B 的子集，新增位置 x 的边际收益满足：

\[
F(A\cup\{x\})-F(A)\ \ge\ F(B\cup\{x\})-F(B).
\]

在**非负、单调、次模、基数约束**等充分条件下，经典贪心选择可达到最优值的 `1-1/e`（约 63.2%）常数因子保证。不能把这个结论机械移植到有任意路径代价、时间窗、机器人动力学和通信限制的规划问题里。

### 算法与当年价值

~~~text
候选传感器 / 观测点集合
           ↓
每个候选当前的边际信息收益
           ↓
选择增益最大的候选
           ↓
更新已选集合和收益
           ↓
直到 K 个或预算用尽
~~~

这一思想为后来的传感器部署、主动视觉、信息驱动探索和近似路径规划提供了理论基础。与本期 GP Informative Path Planning 结合看，先验证目标是否具备次模结构，再谈近似最优的收益比，远比“这个启发式看上去较新”更有依据。

### 假设、现代局限及代码复现

原论文不是机器人 SLAM 端到端代码，也不需要假装存在官方 ROS2 包。真实连续场 GP Kernel 的数值变化、相关噪声和路径执行代价可能改变目标性质。现代在线主动 SLAM、连续空间优化、巡检车路径规划还要考虑碰撞、能耗、轮式运动学和信息延迟。

最小复现：在二维地图上生成 20 个相机/测量候选，设 K=5，枚举所有组合求最优（小规模），比较贪心、随机、距离均匀策略的方差降低量和路程。先独立验证目标是否单调/次模，再加入路径约束，展示理论保证在哪一步不再适用。

**工程重新解读：** 低成本传感器选型、三雷达关键帧选择、前沿候选筛选可以先做“有效边际信息”评估，不是数据越多越好。

---

## 今日结论

**SLAM/导航方面：** HeadIO 的 body-frame 分解告诉我们，选择正确的状态表示常比堆更复杂 Backbone 更有用；GP 信息路径规划强调预测方差的可解释收益；SPARC 的双雷达真实 Bag 直接适合验证多传感器几何互补和弱特征环境。地形 Thompson Sampling 则可用于无人机搜索中的多区域优先级分配，但仍需另建实际避障控制链路。

**机器人控制方面：** BlinkMimic 的公开代码是今天最适合 GPU 工程复现的工作；NSDL 更适合作为“Agent + 确定性求解器”的高层任务调度参考，先验证小规划器、后上视觉模型。HDH 展示轻量筛选 VLA 候选动作的可能性，尚不能替代确定性碰撞检查。

**AI Coding 方面：** 今天不推荐另一套 Coding CLI。优先利用 Robo-SWE 中真实的 ROS2 修复任务评估 Codex，配合改动前后 F2P 断言；需要大量重复 C/C++ API 迁移时才考虑 Coccinelle 规则生成，并坚持编译验收。对日常小改动，`clang-tidy-diff.py` 比额外部署一套复杂 Agent Framework 更实际。

---

## 最值得深入研究或尝试复现的方向

| 优先级 | 实验 | 最小验收 |
|---|---|---|
| P0 | SPARC 前后 LiDAR ROS2 Bag | 时间戳/TF、单雷达与双雷达 ATE/RPE、退化方向、地图大小 |
| P0 | NSDL 无 GPU 任务 Solver | 目标遗漏、顺序/资源约束错误、离线单测、规划时延 |
| P0 | BlinkMimic | 环境自检、三种优化消融、失败片段数、GPU-hours |
| P0 | Codex 两版本回归测试 | Bug 修复前失败、修复后通过，无无关代码修改 |
| P1 | GP Informative Path Planning | 方差、留出 RMSE、路径长度、算法耗时 |
| P1 | HeadIO | RTE-5s、yaw/tilt 扰动、参数与端侧时延 |
| P1 | Multi-drone Thompson Sampling | 发现时间、遮挡漏检、覆盖与能耗 |
| P1 | Robo-SWE | 三个可执行 ROS2 任务、环境复现率、真实 F2P |
| P1 | Coccinelle + 本地小模型 | 最小 API 迁移、规则误改率、编译通过 |
| P2 | HDH VLA 候选验收 | 失败率、误报、候选筛选时延及无法安全执行时弃答 |
| P2 | 贪心次模观测选择 | 小规模枚举最优、贪心比率、路径约束影响 |

## 参考资料

**最新原始批次：** [arXiv cs.RO](https://arxiv.org/list/cs.RO/new) · [arXiv cs.SE](https://arxiv.org/list/cs.SE/new)。

**SLAM / 感知 / 信息路径：** [Terrain-Aware Thompson Sampling](https://arxiv.org/abs/2611.14685) · [HeadIO](https://arxiv.org/abs/2611.14895) · [GP Informative Path Planning](https://arxiv.org/abs/2611.16877) · [SPARC](https://arxiv.org/abs/2611.15443) · [SPARC 官方源码](https://github.com/STAR-Explorer-Robotics/Robocup_system)。

**控制与多机任务：** [BlinkMimic](https://arxiv.org/abs/2611.16422) · [BlinkMimic 开源实现](https://github.com/fuyichen0725/blinkmimic) · [NSDL](https://arxiv.org/abs/2611.16671) · [NSDL 完整工程](https://github.com/Xincheng-Tan/NSDL) · [HDH](https://arxiv.org/abs/2611.14834)。

**AI / Codex 工程：** [Robo-SWE](https://arxiv.org/abs/2611.16116) · [Robo-SWE 数据](https://huggingface.co/datasets/vharatian/Robo-SWE) · [Coccinelle 小模型论文](https://arxiv.org/abs/2611.16215) · [代码](https://github.com/MohannedAhmed67/kernel-sibling-migrations) · [ADAPT](https://arxiv.org/abs/2611.16114) · [LLVM clang-tidy-diff](https://github.com/llvm/llvm-project/blob/main/clang-tools-extra/clang-tidy/tool/clang-tidy-diff.py)。

**经典论文：** [Nemhauser 等 1978](https://doi.org/10.1007/BF01588971)。

