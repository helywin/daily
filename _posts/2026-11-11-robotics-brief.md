---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-11"
date: 2026-11-11 09:00:00 +0800
description: "时空联合标定、DASH-SLAM、GPU 可微 MPC、跨本体迁移和人形安全规划；NINJA、Ninada 与 Codex 工具复现。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-11

## 摘要

**日期：2026-11-11（Asia/Shanghai，星期三）。** 本期首先从 GitHub master 读取任务规范与 **1,297 条历史索引**，再检索论文、作者网页和官方源码。按规范化标题、arXiv ID、DOI、官方项目/仓库联合查重；本期入选的研究工作未作为同一条目登记过。

**arXiv 最新可核实常规公开批次为 2026 年 11 月 10 日：** Robotics（cs.RO）共 241 条，其中 New submissions 128；Software Engineering（cs.SE）共 100 条，其中 New submissions 44。列表总数包含交叉收录和更新稿，不能全部算作首次提交（[cs.RO](https://arxiv.org/list/cs.RO/new)、[cs.SE](https://arxiv.org/list/cs.SE/new)）。

本期优先最近 24 小时，再扩展 7 天；有确切源码的工程项目允许回补较早研究。**注意首次提交时间**：Galilean 联合标定 11 月 9 日；DASH-SLAM、UniLatent、统一惯性编码器、Capturability MPC 均为 11 月 6 日；SmoothedTurboMPC 的论文虽然出现在当前批次，但 arXiv v1 实际记录为 **10 月 13 日**，属于历史回补。绝不把列表日期当成全部论文的首次发布日期。

本期工程主线：

- **SLAM 与标定：** 不再把传感器时间偏移与空间外参割裂；单目基础模型的米制尺度也需要跨片段持续约束。
- **控制：** GPU 可微 MPC 与一阶强化学习的训练流程已经有官方代码；双足足步不仅要避障，还必须保留可停稳状态。
- **具身学习：** 通过潜变量对齐实现不同机械臂之间的视觉策略迁移；人类惯性数据还能帮助 G1 学习速度状态。
- **LLM 附属工程：** 有完整训练/评测仓库的 NINJA 适合大代码库故障定位；有可运行代码的 Ninada 值得用于研究分块流式 TTS；Codex 实战重点转为 ast-grep 和可安装的 NVIDIA Skills。

本期的“源码公开”只表示已核验仓库和构建文档，并不表示已经本机下载、构建或跑出论文指标。没有执行任何 Codex 任务。

---

## 1. Galilean Robots / Aristotelian Sensors：统一描述时空外参与机器人运动

**时间回补｜原始 v1：2026-11-09 15:01 UTC｜[论文](https://arxiv.org/abs/2611.12526)**

### 为什么重要

相机、LiDAR、IMU 和测距设备的空间外参常表示为 SE(3)，时间偏移则作为额外标量。空间变换可以直接与位姿复合，但考虑时间偏移时必须到轨迹的“另一时刻”取值，常需要插值或独立的连续时间参数化。这增加了多传感器后端建模复杂性，并可能掩盖时间误差和运动状态之间的耦合。

Abhishek Goudar、Jonathan Kelly、Timothy D. Barfoot 提出使用特殊 **Galilean 群**描述机器人轨迹，并使用其 **Aristotelian 子群**描述传感器时空外参，使时间与空间耦合通过群结构直接体现。作者给出 Twist 和 IMU 驱动的运动先验，可处理理想与非理想时钟，并组合相机、位置及距离观测。

### 算法模块与假设

~~~text
机器人运动：Galilean 群状态
              +
传感器外参：Aristotelian 子群
              ↓
时移与空间变换统一复合
              ↓
Twist / IMU 运动先验
              +
相机、位置与测距因子
              ↓
轨迹、时钟、时空外参联合估计
~~~

**并非无需同步。** 如果设备出现时钟漂移、跳变、延迟缓存、扫描点内不同时刻等问题，仍需可靠时间戳和适当的时钟模型。纯匀速或缺少旋转/平移激励的运动也可能让某些外参不可观测。群表示能让问题更整洁，不会凭空增加观测信息。

### 实验、鲁棒性与工程风险

论文在仿真和真实多传感器数据上报告与已有方法相当的轨迹与标定表现。摘要未给出可核实的统一 ATE、P95、CPU 占用，本期不补造具体数字。**目前未独立确认完整可构建的官方 ROS2 工程。**

复现步骤：固定同一相机—IMU Bag，注入 0/5/20/50 ms 偏移及不同的时钟漂移；分别估计 SE(3)+偏移和新群结构，检查旋转/平移外参误差、归一化残差、可观测性及 P99 计算开销。最后将方案作为双雷达系统的只读旁路，而不是直接改生产 TF。

### 适合谁关注与工程落地启发

适合 LiDAR–IMU–Camera、双 MID360、跨板卡同步和机器人多传感器联合估计。最大工程收益是减少时空校准模型的割裂，不是取代硬件同步、时间戳管理或完整标定验收。

来源：[原论文](https://arxiv.org/abs/2611.12526)。

---

## 2. DASH-SLAM：借助 Depth Anything 3 在单目子地图之间传播真实尺度

**时间回补｜原始 v1：2026-11-06 21:24 UTC｜[论文](https://arxiv.org/abs/2611.10239)**

### 为什么重要

前馈几何基础模型可以从单目序列估计密集结构，但多个分段重建的相对尺度可能不一致。即使 Sim(3) 对齐后的 ATE 很低，机器人也不一定具有真实“米”的尺度。对多楼层重定位和地图复用，这个差异比漂亮的 3D 渲染更重要。

DASH-SLAM 引入预训练 **Depth Anything 3** 的公制深度，在共享关键帧的位姿图上，利用共同锚定图像的深度比例逐段估计尺度。阻尼因子限制尺度校正的作用强度，并同步调整里程计平移、回环约束和地图几何；不要求专门微调基础模型。

### 算法模块与传感器假设

~~~text
单目 RGB → Depth Anything 3 几何预测
                    ↓
连续局部重建 / 共享关键帧
                    ↓
共同锚点的深度比例
                    ↓
尺度校正 + 阻尼传播
                    ↓
位姿图平移、回环及地图同步修正
~~~

基础模型给出的公制深度并不等于 LiDAR 真值。玻璃、镜面、严重烟雾、极端室内布局会产生系统误差；若共享关键帧重叠不足，尺度比也可能不稳。

### 实验、实时性与可复现性

作者在 TUM、Replica、7-Scenes 以及 Unified Autonomy Stack 的隧道、浓雾、冰湖等四条感知退化序列评价，报告优于对照的基础模型 SLAM，并在部分经典 SLAM 失跟踪时继续运行。论文刻意同时报告刚体对齐 SE(3) 和相似变换 Sim(3) 结果，以区分尺度恢复与仅仅形状对齐。

当前没有已独立核实的官方完整构建入口和跨硬件 FPS，不承诺在 RK3588 上实时。最小 A/B 是固定视频、相同前端和后端，关闭与打开尺度锚定及阻尼，对比米制平移误差、回环错误、GPU 显存与 P95。

### 适合谁关注与工程落地启发

适合单目机器人、视觉地图、弱特征环境定位。对于已经具有 LiDAR 真尺度的生产系统，建议作为视觉 Sidecar，而不是把学习深度直接覆盖激光尺度。

来源：[原论文](https://arxiv.org/abs/2611.10239)。

---

## 3. SmoothedTurboMPC：GPU 平滑 ADMM + 一阶 RL，源码与测试入口已经开放

**时间回补｜arXiv 原始 v1：2026-10-13 20:29 UTC｜[研究](https://arxiv.org/abs/2611.09937) · [官方代码](https://github.com/ToyotaResearchInstitute/turbompc)**

### 为什么重要

把 MPC 作为可微策略层，可保留优化问题的结构、约束和动力学先验，但两件事阻碍训练：active-set 切换处导数不光滑，以及每次策略评估都重新求解优化问题的高计算开销。

SmoothedTurboMPC 将 GPU 并行 SQP 外层与 Log-Barrier 平滑 ADMM 内层结合，在收敛条件下获得可用的敏感度；再通过 Short-Horizon Actor-Critic（SHAC）复用 rollout 的 MPC 解，减少一阶 RL 中重复的策略求解成本。

### 核心模块

~~~text
状态 / 动力学 / 约束 / 学习型代价
                 ↓
GPU SQP
                 ↓
Log-Barrier Smoothed ADMM
                 ↓
最优动作 + 梯度信息
                 ↓
SHAC 使用已求解的 MPC rollout
                 ↓
策略参数更新与域随机化
~~~

### 实验结果与边界

作者报告相对于所选最先进求解器，端到端训练吞吐最高 **4.4×**；在指定赛车任务与 MPC PPO 对照时，训练速度提高 **46×**，用 **330 万条 transition、约 7 分钟**完成该实验，并在真实全尺寸赛车上验证。这里的 46× 是**训练比较**，不是每个机器人控制周期都加速 46 倍。MPC 求解成功也不等于模型失配、执行器延迟和外部碰撞都被证明安全。

### 最小可执行复现

官方仓库包含 Python 3.10+、CPU 安装、CUDA 12 构建、诊断工具、无人机/赛车 Notebook 和 pytest，仓库说明主要在 Ubuntu 22.04 测试。Arch Linux 建议用单独虚拟环境。

~~~bash
git clone https://github.com/ToyotaResearchInstitute/turbompc.git
cd turbompc
python -m venv .venv
source .venv/bin/activate
pip install -e .
turbompc-check
# CUDA 12 的独立 GPU 环境：
# pip install -e ".[cuda12]"
# turbompc-check
~~~

可先运行 CPU 端冒烟与 pytest，再测试官方 examples/rl 下的 Drone/Quadrotor/Racing 训练例。固定 Horizon、随机种子、硬件、约束、batch、成功率指标，报告 solve P50/P95/P99、训练 GPU-hours、显存与最终真实闭环性能。

### 适合谁关注与工程落地启发

适合无人机 MPC、学习控制与 GPU 批量规划；若希望避免过度工程化，先从仓库现有示例起跑，不必立刻重写底盘控制器。本轮只核实公开代码和命令，未实际运行训练。

来源：[论文](https://arxiv.org/abs/2611.09937) · [作者页](https://brianplancher.com/publication/smoothedturbompc/) · [官方仓库](https://github.com/ToyotaResearchInstitute/turbompc)。

---

## 4. UniLatent：先对齐本体间的潜特征，不必逐帧重画目标机器人

**时间回补｜arXiv 原始 v1：2026-11-06 07:35 UTC｜CoRL 2026｜[论文](https://arxiv.org/abs/2611.10061) · [项目页](https://selina2023.github.io/unilatent/)**

### 为什么重要

Franka 上训练的视觉操作策略切换到 xArm 或 Sawyer 后，图像中的机械臂外形、遮挡和抓持区域发生变化。使用扩散模型逐帧把源机器人改画为目标机器人，容易扭曲手指及接触点，而且推理/预处理成本高。

UniLatent 采取**仿真成对图像**：固定相机与工具中心位姿，在同一随机场景中渲染源和目标本体。目标视觉编码器 E_T 冻结；训练源编码器 E_S 将源图像映射到 E_T 的目标特征。之后使用对齐的源演示训练 Flow-Matching 动作策略，部署时仅对目标图像做 E_T 编码，**无须在线图像翻译**。

### 算法模块与假设

~~~text
源/目标机器人：相同 TCP、相同背景的配对渲染
                           ↓
目标 DINOv2 编码器冻结 E_T
                           ↓
训练 E_S 对齐 CLS/Patch 特征
                           ↓
源演示潜特征 → Flow-Matching 动作块
                           ↓
目标图像 → E_T → 共享动作策略
~~~

需要兼容的末端动作接口与任务语义；潜特征一致不代表关节限位、夹爪动作、力矩和时序也一致。

### 实验与实时性

三种模拟操作任务、两个目标本体的六种零样本迁移条件下，作者报告平均成功率 **76.0%**，受控像素翻译对照 **44.5%**；某个测试单元最高 **93%**。真实 xArm → Franka，在每个任务仅增补 10 条目标机器人示范后，三任务 **27/30** 成功，像素翻译对照 **23/30**。这不是纯真机零样本迁移；必须注明用了目标本体少量微调。

作者项目具有详细配对渲染、消融和真机失败分析，尚未独立确认完整训练代码/权重可以一键构建。最小复现可先在 MuJoCo 中采集共享 TCP 姿态的配对 RGB，比较直接迁移、像素翻译和潜特征对齐，并单独统计抓取时接触点错位。

### 适合谁关注与工程落地启发

适合跨机械臂示教共享、多本体 VLA。真正减少的可能是视觉域迁移成本，并非消除机械/控制差异；正式使用仍需关节与碰撞约束。

来源：[原论文](https://arxiv.org/abs/2611.10061) · [官方项目](https://selina2023.github.io/unilatent/)。

---

## 5. Unified Inertial Encoder：借助人类运动记录，零样本迁移到 G1 速度估计

**时间回补｜arXiv v1：2026-11-06 19:03 UTC｜[论文](https://arxiv.org/abs/2611.10137)**

### 为什么重要

纯机器人惯性状态估计训练数据受已执行动作集合限制；人类运动覆盖更多动作，但人体结构、传感器安放位置及动力学均与 G1 不同。作者将人体与人形运动映射到**对应身体位置的运动学合成 IMU**，在统一惯性输入空间同时训练速度估计和动作—文本对齐。训练包含连续时间编码、传感器随机化和动作随机化，减少本体间差距。

### 算法模块

~~~text
人类动作数据 + 重定向人形动作数据
                    ↓
对应身体部位的运动学 IMU 合成
                    ↓
共享惯性编码器
           ├─ 速度估计目标
           └─ 语言—动作对齐
                    ↓
真实 Unitree G1 IMU 输入
~~~

### 实验、鲁棒性与边界

作者报告**无需真实 G1 训练轨迹、物理仿真或目标微调**，直接零样本部署到 G1；在五个测试数据集上取得所比较方法最低的速度误差，真实 G1 报告 **0.099 m/s**。这不是 ATE，也不是累计位置漂移；单靠 IMU 不会凭空获得全局 Yaw，足底滑移与加速度偏置仍可造成长期不稳定。

当前尚未核实公开完整训练源码及权重，也没有跨设备 P99。工程比较应固定动作和 IMU 位置、对比传统惯性/足底估计及学习 Encoder 的速度 RMSE、稳定时间和姿态依赖，并对楼梯、推箱和失稳工况进行分布外测试。

### 适合谁关注与工程落地启发

适合 G1、人形与轮足机器人本体速度辅助估计。不要仅因为单帧速度低误差，就用它替换已有 ESKF/足底/激光联合定位；先做只读旁路。

来源：[原论文](https://arxiv.org/abs/2611.10137)。

---

## 6. Capturability-Aware Footstep MPC：落脚要避开障碍，也必须保留停稳能力

**时间回补｜arXiv v1：2026-11-06 19:46 UTC｜Humanoids 2026｜[论文](https://arxiv.org/abs/2611.10169)**

### 为什么重要

普通足步规划可以找到不碰撞的下一落脚点，但下一步是否还能稳定停止并不确定。作者在 Linear Inverted Pendulum（LIP）模型中，同时考虑**捕获/停稳能力（Capturability）**和**安全走廊几何约束**，将障碍地图分为相互重叠的轴对齐矩形走廊，通过 Sequential MPC 规划可行足步。

### 算法模块与动力学假设

~~~text
局部障碍地图
      ↓
重叠矩形安全走廊
      ↓
LIP 质心动力学
      +
Capturability 约束
      ↓
Sequential MPC 足步优化
      ↓
可继续运动 / 原地保持稳定
~~~

作者强调递归可行性：例如事先预计打开的门在执行时关闭，系统能退回原地步行，而不是强制穿越。证明属于 LIP 规划层，需要正确摩擦、落脚面积、质心高度等假设；它并非对完整关节动力学的全场景安全认证。

### 实验、实时性与可复现性

在 Digit 高保真仿真中测试狭窄障碍与路线阻塞，作者报告较高成功率、性能对时域长度依赖较弱。摘要没有可靠的统一真机成功率、P99 求解数字；本次未确认官方完整可运行仓库。

最小工程试验是固定走廊、突然关闭的门、可停稳安全区域，对比普通足步 MPC 和 Capturability-Aware MPC 的站稳成功率、最小净空、无可行步时的行为及控制超时恢复。

### 适合谁关注与工程落地启发

适合人形足步与狭窄通道规划。对于仅开放运动/登梯模式的轮足 SDK，应借鉴“高层必须保留安全退路”而不是直接移植 Digit 的足步控制器。

来源：[原论文](https://arxiv.org/abs/2611.10169)。

---

## 7. DPGS-SLAM：异步扩散补全动态背景，但地图要记录每个几何来源

**时间回补｜2026-11-10 arXiv 当前公开列表；原始 v1 UTC 时间本轮未独立读取｜[arXiv 2611.12038](https://arxiv.org/abs/2611.12038)**

### 为什么重要

动态 SLAM 的两难是：允许移动的人和物体进入地图会污染估计；全部剔除动态区域，又可能长期缺失遮挡后的静态背景。DPGS-SLAM 使用单目 RGB，异步扩散生成背景候选，再在 3D Gaussian Splatting 地图中保留**来源（Provenance）标记**，区分真实观测支持和临时预测内容。

### 算法模块与假设

~~~text
单目 RGB + 相机跟踪
             ↓
动态区域隔离
      ├─ 可靠静态观测 → 高置信 Gaussian
      └─ 遮挡区域 → 异步扩散补全
                           ↓
                   暂定 Gaussian
             ↓
来源标记与后续真实回访验证
             ↓
渲染与稠密地图更新
~~~

扩散补全可以让画面完整，但不能当作真实的碰撞地图或规划障碍。动态分割错误、相机漂移及补全置信度失控都可能制造“看起来很好”的错误墙体。

### 实验、实时性与资料限制

根据当日 [cs.RO 一手列表](https://arxiv.org/list/cs.RO/new) 摘要，作者报告 TUM RGB-D 和 BONN RGB-D 上平均 ATE RMSE 分别为 **1.2 cm**、**2.7 cm**，StaDy4D 上相对 WildGS-SLAM 的平均 PSNR 提升 **4.60 dB**。ATE 与 PSNR 不能相互替代，也不能推广到任意动态仓库。**本次独立论文页面暂时无法打开，完整代码/发布时间细节未独立确认**，因此不声称已经复现。

### 可复现性与工程启发

先在一个含行人的室内视频中对比：仅剔除动态点、无来源标记补全、带来源标记补全。评价后来实际看到被遮挡墙面时，临时 Gaussian 是否会撤销/修正，此外记录定位 ATE、渲染 PSNR、显存和异步线程 P95。

适合动态视觉地图和数字孪生，不建议将生成式背景直接用于真实机器人的安全 Costmap。

来源：[论文入口](https://arxiv.org/abs/2611.12038) · [arXiv 当日列表](https://arxiv.org/list/cs.RO/new)。

---

## AI / LLM 附属框架与开源工程组件

### 组件 1｜NINJA：仓库级 Navigator + 函数级 Inspector 的分层代码定位

**时间回补｜arXiv v1：2026-11-05 UTC｜[论文](https://arxiv.org/abs/2611.10027) · [官方仓库](https://github.com/wantbook-book/NINJA)**

**真正解决的痛点：** Coding Agent 搜索大型仓库时，文件级查找和函数级深入分析往往混在同一上下文，导致无关代码与调用轨迹挤占预算。NINJA 将两种过程分离：Navigator 管理候选文件和全局搜索状态，每个 Inspector 在独立上下文分析分派的函数/调用图，并只返回怀疑位置和理由。

~~~text
问题描述 → Navigator 文件级搜索
                  ↓
      Inspectors 独立函数上下文
                  ↓
  返回疑似文件、函数和关联调用证据
                  ↓
 Navigator 继续查找或输出定位结果
~~~

**真实开源程度：** 已核验官方仓库包含 RepoSearch、LocAgent、verl、数据构建、SFT/RL、评测及可视化目录，并给出脚本示例；属于完整**研究训练栈**，不是安装后就自动提升 Codex 的零配置插件。训练需满足 CUDA、vLLM/SGLang、FlashAttention 和指定数据条件，实际部署成本不低。

**最小工程尝试：** 先不训练任何模型。从真实 C++/ROS2 Bug 的已知文件出发，让 Codex 第一步只使用文件名/符号查找返回最多五个候选入口，再对每个入口做单独函数级只读检查，最后统一汇总为 file:function:reason；与单一长上下文进行比较。测首个正确函数排名、总 Token、误定位率和人工定位时间。

**安全与局限：** 多 Agent 不一定更快；如果无关任务切得太碎，协调开销可能抵消收益。不要直接照搬论文其他模型的 Benchmark 分数到当前 Codex。可先把流程写成一个轻量 Skill，不动底层模型。

来源：[NINJA 论文](https://arxiv.org/abs/2611.10027) · [官方训练/评测代码](https://github.com/wantbook-book/NINJA)。

### 组件 2｜Ninada：可部署的分块语音合成，支持浏览器、Node.js 与 Python

**时间回补｜arXiv v1：2026-11-05 UTC｜[论文](https://arxiv.org/abs/2611.10035) · [官方源码](https://github.com/hemanth/ninada)**

**真正解决的痛点：** 语音 Agent 等待整句合成后再播放，导致 Time-To-First-Audio 过长；而手机/浏览器对模型大小、ONNX 推理和音频缓冲的要求不同。Ninada 按文本子句拆分推理，在桌面与移动端采用不同的 VITS/Vocoder ONNX 实现，持续输出 24 kHz PCM，另提供 Python、Node 和浏览器入口。

**开源与量化：** 官方仓库包含 JS、Python、训练、测试和模型调用代码，MIT 许可证，支持英语、古典梵语和十种印度语言。作者报告 Desktop/WebGPU 首个可听音频约 **89–155 ms**，Pixel 10 Pro XL 移动端约 **538–649 ms**；单个桌面 ONNX 约 **27.9 MB**、移动版约 **21.7 MB**。数字与硬件、预热、语言和加载状态有关，不可当成通用 SLA。

~~~bash
npm install ninada webml-kit
npx ninada "Welcome to Ninada studio voice synthesis." -l en -v female -o english.wav

# 另一种使用入口
pip install ninada
~~~

**与语音机器人的工程关系：** 可直接学习分块 PCM、边生成边播放、手机 CPU/WASM 回退与能力路由；**当前官方语言列表不含普通话**，不能直接宣称取代中文 TTS。对 SIP Bot 应评价 TTFA、RTF、每分块延迟、打断后的缓冲残留和音质，不是只看模型大小。

**许可证/依赖边界：** 仓库 MIT，不等于所有权重和训练数据没有各自许可证；使用前分别核对下载模型和语料授权。本文未实际安装运行。

来源：[原论文](https://arxiv.org/abs/2611.10035) · [官方仓库](https://github.com/hemanth/ninada)。

---

## AI Coding 实战技巧精选

本栏仅针对 Codex 及其实际开发工作流，不使用其他 Coding CLI 的版本公告。本期两个技巧均有直接可运行的操作入口。

### 技巧 1｜为 Codex 配 ast-grep：按 C++ AST 结构定位调用，少读无关文件

- **来源：** [ast-grep 官方代码](https://github.com/ast-grep/ast-grep) · [CLI 文档](https://ast-grep.github.io/reference/cli)。
- **一句话结论：** 对复杂 C++/ROS2 仓库，先用语法树模式找到真正的函数调用，再把候选行交给 Codex；相比无差别读全文或正则替换，更有利于控制搜索范围。
- **具体怎么做：**
  1. 先安装：npm install --global @ast-grep/cli；在 Linux 使用完整命令 ast-grep，避免与系统 sg(setgroups) 重名。
  2. 在临时工作树只读搜索结构，例如下面的两种有效 C++ 模式：

     ~~~bash
     ast-grep run -l cpp -p 'foo($ARG)' src/
     ast-grep run -l cpp -p '$OBJ.publish($MSG)' src/
     ~~~

  3. 用真实 API 名替换示例，要求 Codex 先给出文件、行号与关联函数，确认候选后才能修改；最终执行相关编译和测试。
  4. 用已知的十条 Bug 对照 rg 与 ast-grep，记录首个正确位置、无关文件阅读数量、总 Token 和无关 Diff。
- **适合什么场景：** Codex、C++、ROS2、函数迁移、跨模块定位。
- **注意：** AST 结构搜索不是完整语义分析；宏、模板、动态分派可能需要编译数据库与静态分析补充。未经审查不要全局运行 rewrite。

### 技巧 2｜Codex 按需安装 NVIDIA 官方 Skills：只用对工作有益的专业能力

- **来源：** [NVIDIA Agent Skills 官方仓库](https://github.com/NVIDIA/skills) · [Agent Skills 规范](https://agentskills.io/)。
- **一句话结论：** NVIDIA 的可迁移 Skills 覆盖 Physical AI、机器人仿真、CUDA、RAG 和 cuOpt；按需安装到 Codex，比把完整 SDK 教程常驻 AGENTS.md 更轻量。
- **具体怎么做：**
  1. 只查询可用列表，不批量安装：

     ~~~bash
     npx skills@latest add nvidia/skills --list
     ~~~

  2. 若要实验 cuOpt 数值优化接口，可安装一项到 Codex：

     ~~~bash
     npx skills@latest add nvidia/skills \
       --skill cuopt-numerical-optimization-api --agent codex
     ~~~

  3. 开新 Codex 会话，确认 Skill 被发现，选择一个具有可计算标准答案的小型优化问题进行只读/沙盒测试。
  4. 与不使用 Skill 的同一任务对照，统计 API 错误、测试通过率、Token 和人工复核成本；无收益即不保留。
- **适合什么场景：** Codex、GPU 工具、机械臂规划、仿真与真实 C++/Python 工程。
- **注意：** Skill 是使用指南，不会安装所需 NVIDIA SDK，也不提供任何机器人安全认证。安装前应审查实际 SKILL.md 和许可证，不要授权外部脚本任意访问私有仓库。

---

## 经典论文回顾

### Closed-form Solution of Absolute Orientation Using Unit Quaternions（Horn，1987）

**作者：** Berthold K. P. Horn。**发表：** 1987 年 4 月，Journal of the Optical Society of America A，4(4):629–642。**原始来源：** [论文 DOI](https://doi.org/10.1364/JOSAA.4.000629)。

### 核心问题、算法与数学思想

当两个不同传感器/坐标系观测到一组具有确定对应关系的三维点，如何估计最合适的旋转 R、平移 t，以及需要时的统一尺度 s？Horn 把点集做质心中心化，再用对应点的交叉相关构建四元数特征值问题，求得最优的单位四元数。随后由质心计算平移；在相似变换情况下还可计算统一尺度。

~~~text
已对应的点集 P、Q
        ↓
中心化与相关矩阵
        ↓
单位四元数特征值问题
        ↓
旋转 R
        ↓
平移 t 与可选尺度 s
        ↓
地图/传感器坐标初始对齐
~~~

它和 Kabsch SVD、Umeyama 的目标密切相关，但不是相同的推导实现；不要不加区分地把所有 SVD 配准都称为 Horn 四元数算法。

### 传感器假设与理论边界

方法假设点对应正确、几何结构非退化。如果点几乎共线、存在大量错误匹配，或两台设备不同步导致对应的物理点位置发生变化，解析最优解也会对错误数据给出“最优拟合”。它不会自动处理离群点、时间偏移或真实传感器内参错误。

### 当年为何重要、今天如何使用

1987 年它使 3D 绝对定向/坐标对齐能够以简洁解析形式求解。今天仍广泛作为手眼/外参初始化、不同点云子地图对齐、视觉回环几何验证中的底层工具。离群点鲁棒性通常交给 RANSAC/稳健优化；后端时间同步与状态估计交给现代因子图等方法。

对本期的 Galilean 联合标定尤其要注意：Horn 可以先求**同步、对应关系可靠条件下的空间初值**，不能代替时空联合标定中的时钟状态。对 DASH-SLAM 则必须区分依靠 Sim(3) 对齐评价的 ATE 与实际恢复米制尺度的能力。

### 最小可复现性与工程重读

用 100 对真实或仿真三维点，施加已知 R/t/s，逐步注入 0%、10%、30% 错误对应和随机噪声；比较 Horn、SVD 及 RANSAC+后端优化的旋转/平移/尺度误差。再把采集时间偏差引入运动点对应，观察纯空间解如何失效。经典方法的用途是**可靠的初始化和对照**，不应被误认为完整 SLAM。

来源：[Horn 1987 DOI](https://doi.org/10.1364/JOSAA.4.000629)。

---

## 今日结论

本期七项主动态与两项 AI 附属组件指向三个共同原则。

**几何观测必须明确时间和尺度。** Galilean/Aristotelian 时空标定和 DASH-SLAM 的尺度锚定解决不同层面的不一致；DPGS-SLAM 则提醒我们，预测背景只能是带来源标记的暂定信息，不能被当作实测地图。

**规划器需要尊重动力学和执行成本。** SmoothedTurboMPC 有代码可用于学习型优化，但论文的 46 倍是指定 RL 训练比较，不是机器人通用在线加速；Capturability 足步规划的可行性保证也只属于相应 LIP 模型。视觉和惯性策略迁移需要真实接触/姿态工况复核。

**Agent 的提升来自工具链，不是模型公告。** NINJA 用全局导航和局部函数调查分离代码定位；Ninada 用真实的 PCM 流式输出解决音频时效。Codex 可从 ast-grep 和经过审核的 NVIDIA Skills 中获得可测量的工作效率提升，但是否值得长期启用，应以真实项目的 A/B 为准。

---

## 最值得深入研究或尝试复现的方向

1. **Galilean 标定：** 双传感器 Bag 注入时差、漂移、运动退化，测外参误差和优化时延。
2. **DASH-SLAM：** 用 TUM/7-Scenes 比较有无尺度锚点，并分开报告 SE(3)/Sim(3) ATE。
3. **TurboMPC：** 从官方 CPU 诊断开始，再在隔离 CUDA 12 环境验证 GPU 批量求解与无人机示例。
4. **UniLatent：** 生成成对本体 RGB，在相同 TCP 空间下评估潜特征对齐与接触失败。
5. **统一惯性编码：** 在 G1/人形动作中测速度 RMSE、Yaw 退化和长期位移积分错误。
6. **Capturability MPC：** 仿真突然关门、窄通道与超时，检验停稳退路是否保持。
7. **DPGS-SLAM：** 分离真实观测与扩散补全的 Gaussian，回访后验证补全是否能撤销。
8. **NINJA：** 用已知 C++ Bug 对比单 Agent 长上下文与 Navigator/Inspector 分层定位。
9. **Ninada：** 测真实设备的 TTFA、RTF、打断缓冲；不要当普通话现成 TTS。
10. **Codex：** AST 查询与 NVIDIA Skill 分别做 10 次真实任务 A/B，统计无关改动和人工复核成本。

---

## 参考资料

**原始批次：** [Robotics cs.RO](https://arxiv.org/list/cs.RO/new) · [Software Engineering cs.SE](https://arxiv.org/list/cs.SE/new)。

**SLAM/标定：** [Galilean 联合标定](https://arxiv.org/abs/2611.12526) · [DASH-SLAM](https://arxiv.org/abs/2611.10239) · [DPGS-SLAM](https://arxiv.org/abs/2611.12038)。

**规划/控制/具身：** [SmoothedTurboMPC](https://arxiv.org/abs/2611.09937) · [TurboMPC 源码](https://github.com/ToyotaResearchInstitute/turbompc) · [UniLatent](https://arxiv.org/abs/2611.10061) · [UniLatent 项目](https://selina2023.github.io/unilatent/) · [统一惯性编码](https://arxiv.org/abs/2611.10137) · [Capturability MPC](https://arxiv.org/abs/2611.10169)。

**AI 附属框架：** [NINJA 论文](https://arxiv.org/abs/2611.10027) · [NINJA 源码](https://github.com/wantbook-book/NINJA) · [Ninada 论文](https://arxiv.org/abs/2611.10035) · [Ninada 源码](https://github.com/hemanth/ninada)。

**Codex 工程：** [ast-grep](https://github.com/ast-grep/ast-grep) · [ast-grep CLI](https://ast-grep.github.io/reference/cli) · [NVIDIA Skills](https://github.com/NVIDIA/skills) · [Agent Skills 规范](https://agentskills.io/)。

**经典论文：** [Horn 1987](https://doi.org/10.1364/JOSAA.4.000629)。
