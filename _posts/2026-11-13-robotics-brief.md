---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-13"
date: 2026-11-13 09:00:00 +0800
description: "单目安全深度、FAME-QP GPU MPC、SIGMO交互规划、Koopman RL、ExRL动作块、LEASH/Jev安全门、VLA记忆失效、百任务VLA，以及AST监控与RAG回放工具。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-13

## 摘要

**北京时间 2026-11-13（星期五），Asia/Shanghai。** 在本次检索时，arXiv cs.RO 和 cs.SE 的 /new 页面最新可核实常规公开批次均为 **2026-11-11**，而非擅自推断的 11 月 12 日或 13 日批次。cs.RO 列出 111 条（其中 57 条 New submissions），cs.SE 列出 47 条（其中 23 条 New submissions）；列表总量包含交叉收录和版本更新。先核查最近 24 小时，再扩至 7 天；入选八篇论文的 v1 均在 **2026-11-09 至 11-10 UTC** 提交，因此统一标为“时间回补”。原始入口：[arXiv cs.RO](https://arxiv.org/list/cs.RO/new) · [arXiv cs.SE](https://arxiv.org/list/cs.SE/new) · [cs.RO recent](https://arxiv.org/list/cs.RO/recent)。

选题前对照 GitHub 已覆盖的 **1,321 条**历史工作，使用标题、arXiv ID、DOI、代码仓库及项目主页联合去重。今天优先推荐三个真正值得动手的工程对象：

- **FAME-QP**：MIT 开源、可用 pip 安装的 GPU 二次规划求解器，作者公开 CUDA Graph/Triton 实现和复现案例；不要把指定 RTX 3080 Laptop 的测试结果套到全部 GPU。
- **LEASH / RoboRisk**：作者公开 MIT 代码、105 个仿真/真机任务和安全 Harness，使用 Jev 或其他决策服务建立 Task / Action / Commit 三级门禁；模型审批不替代硬件限幅。
- **RAG/Agent 监测**：AST 监测“有动作但没获得新信息”的停滞，retrieval-lens 记录检索命中与顺序，分别适合长任务监控和 SAG 类检索系统 A/B。

同日还重点关注：冻结 Depth Anything V2 的低成本安全深度校正、交互让行规划 SIGMO、Koopman 一步传播 RL、动作块执行长度自适应 ExRL、VLA 的“虚假进度”记忆漏洞，以及带代码与权重的百任务 VLA。所有性能数字均注明原始设备/任务条件；未安装运行的项目明确标注。

---

## 1. From Depth to Safe Depth：让单目深度的“不确定性”直接作用于 Nav2 避障

**时间回补｜v1 2026-11-10 09:07 UTC｜arXiv:2611.13769**

### 为什么重要

将 Depth Anything V2 的 Metric Depth 直接转为局部 Costmap 看似可以用单摄像头替代深度硬件，但模型**高估近距离真实距离**时，机器人会错误认为前方仍可通行。作者在 120 个室内 Nav2 仿真 Episode 中，未校正深度导致 **63% 碰撞**。

新方法在冻结的深度模型上附加仅 **0.58M 参数**的预测头，为每个像素输出对数深度偏移 μ 与不确定度 σ，并采用保守单侧边界：

    d_safe = d_pred × exp(μ - kσ)

其中 k 在独立留出环境中做 Conformal 校准；不确定性还影响哪些像素允许当作地面。它不只是对所有障碍设置相同的固定膨胀半径。

### 算法模块、传感器与假设

RGB → 冻结 Depth Anything V2 → 小型校正头输出 (μ,σ) → 保守深度与地面掩码 → Nav2 Costmap → 路径与局部控制。需要相机内参、真实障碍距离的训练/校准数据、足够可靠的相机时序。对镜面、深色和无纹理墙面提供了针对性评估，但没证明全部未知环境下的安全覆盖率。

### 实验、实时性和工程风险

| 指标 | 未校正深度 | Safe Depth |
|---|---:|---:|
| AbsRel | 0.262 | 0.134 |
| 近距离高估率 | 59.8% | 12.0% |
| 导航成功率 | 37% | 70% |
| 碰撞率 | 63% | 3% |

同等像素覆盖下的固定安全边距仅有 30% 导航成功率，说明保守不应简单等同于“让机器人停下”。这些数字**来自指定仿真测试，不是真机认证**。论文摘要未给出可独立核实的端到端 Jetson/RK3588 P99，当前未核实完整官方工程。

### 可复现性、适合谁关注与落地启发

先用固定 ROS2/Nav2 仿真地图对比 RGB Metric Depth、恒定安全边距、Safe Depth 三种 Costmap 输入，记录近障高估、碰撞、误停车、CPU/GPU P95。适合低成本轮式机器人、单目无人机、视觉辅助导航；已有激光雷达时优先做融合辅助层，不能用“预测安全深度”覆盖真实 LiDAR 量测。

原始来源：[论文](https://arxiv.org/abs/2611.13769)。

---

## 2. FAME-QP：CUDA Graph + 融合 ADMM 的 GPU MPC 求解器，已公开可执行代码

**时间回补｜v1 2026-11-10 09:06 UTC｜arXiv:2611.13766**

### 为什么重要

线性 MPC 往往在每个控制周期求解凸二次规划。对中等规模问题，传统 GPU 实现容易因每轮 Kernel Launch、数据搬运和矩阵变化重新预处理而丢掉并行收益。FAME-QP 使用约束结构识别、单/双 Kernel 融合 ADMM、CUDA Graph Replay、惩罚参数 Operator Bank 与按设备选择执行模式。

### 算法模块和动力学假设

线性化动力学与约束 → Condensed QP → 区分 Box、Split、Dense 约束 → 自动选 Kernel/精度与预热 → ADMM 迭代 → 原始/对偶残差停止 → Warm Start 下一周期。它解决**凸 QP 求解**，不是任意非线性 MPC 的直接替代；线性化、模型误差和接触模式仍由上游负责。

### 作者公开的性能

RTX **3080 Laptop GPU、float64** 指定实验：随机线性 MPC 问题单步 **0.66–4.2 ms**；所测 G1 抗推 MPC 在 2 ms 控制周期下可支持 N=20，而比较的 ReLU-QP 支持至 N=10。Skydio X2 动态更新 QP 矩阵的例子为 **12.5 ms 对 59.2 ms**，其 P99 为 **17.6 ms**，未超过 20 ms 周期。注意这些不是 RTX 5070 或完整真实机器人全链路数字，也不包含每种情况下所有外部调度延迟。

### 开源与最小复现

官方 [santoshrajkumar/fame-qp](https://github.com/santoshrajkumar/fame-qp) 为 MIT，包含 fame_qp、examples、tests、实验和 PyPI 包。要求 Linux、Python 3.9+、CUDA PyTorch、兼容 Triton 的 NVIDIA GPU。首次在新设备校准会有额外开销。

~~~bash
python -m venv .venv && source .venv/bin/activate
# CUDA 版本的 torch 请先按 PyTorch 官方说明安装
pip install fame-qp
git clone https://github.com/santoshrajkumar/fame-qp.git
cd fame-qp
python examples/usage.py
~~~

也可从仓库 editable 安装，参考 README 中的 QP.create / Solver / LinearMPC API。上方命令是作者给出的可用入口组合，本次未实际运行。建议对同一问题形状比较 OSQP、qpOASES、FAME-QP，在严格一致的原始/对偶容差下记录首次 Setup、Warm Start、矩阵更新、P50/P95/P99、实际控制可行性。

### 适合谁关注与工程落地启发

适合 CUDA MPC、四旋翼、轮足/人形的线性化约束优化及大批量控制仿真。对现有 NVIDIA 开发机，最有价值的是先测自己的 QP 规模，而不是仅根据论文加速倍数换控制器。

来源：[论文](https://arxiv.org/abs/2611.13766) · [源码](https://github.com/santoshrajkumar/fame-qp) · [示例](https://github.com/santoshrajkumar/fame-qp/tree/main/examples)。

---

## 3. SIGMO：拥挤走廊不只预测碰撞，还估计对方“是否会让行”

**时间回补｜v1 2026-11-10 17:53 UTC｜arXiv:2611.14414**

### 为什么重要

多个移动机器人在狭窄走廊相遇时，仅依据预测碰撞选择减速可能使双方都停住。SIGMO 使用几何和速度等物理交互特征构造**多项式 Sigmoid 让行分数**，再放入滚动时域规划器，对候选轨迹同时评价安全性与主动通行能力。

### 算法模块、假设与实时性

感知邻近智能体位置/速度 → 预测其轨迹 → 计算 Interaction Features 与 Yield Score → 对候选自车轨迹打分 → Receding-Horizon 执行与重规划。该方法需要合理的他车行为预测，不意味着能够在对方不遵守避让规则时自动保证安全。

论文提供交互密集的仿真和硬件演示，描述其规划计算轻量，但公开摘要未给出统一可复核的毫秒时延与可靠成功率，完整官方代码未独立确认。

### 可复现性、适合谁关注与落地启发

先在双机器人单车道会车场景对比“均避让停止”、DWA/MPPI 只考虑碰撞与 SIGMO 式显式优先权分数，记录死锁率、最小净空、通行时间和错误让行率。适合轮式巡检、狭窄走廊、多机器人协同；不能把主动通行优先级凌驾于硬件紧急停止。

来源：[原论文](https://arxiv.org/abs/2611.14414)。

---

## 4. Koopman Model-Based RL：一步模型传播加 Critic，避免长时域预测误差爆炸

**时间回补｜v1 2026-11-10 UTC｜arXiv:2611.14186**

### 为什么重要

未知非线性动力学的模型式 RL 要么靠长时域模型 Rollout 产生误差累积，要么需要大量在线优化。K-MBRL 学习 Koopman 算子，将非线性状态映射到更接近线性演化的特征表示，并只做**一步模型预测**；未来长期收益则由 Critic 估计。

### 算法模块与理论假设

机器人观测 → Koopman 特征/随机动力学模型 → 一步预测状态 → 即时代价 + Critic 未来代价 → 近似策略梯度更新 → 推理期前馈策略输出。一步传播减少模型误差积累，但并不自动使 Koopman 特征完全线性；其收敛保证依赖所述随机逼近假设。

### 实验与硬件

作者在 HalfCheetah、四足运动、Pendulum Swing-up 评价样本效率及梯度近似，另外在真实四足机器人展示后足站立、双足移动并重新安全落地的完整序列。摘要未提供可直接推广的统一成功率和嵌入式 P99，官方完整训练工程尚未核实。

### 最小复现与适用场景

在 MuJoCo 相同动作数据上比较 Koopman 一步预测、普通 MLP 多步模型和无模型 PPO/SAC，统一记录短期预测、真实 Rollout 回报、环境样本数与控制时延。对已拥有稳定厂商 SDK 的机器狗，先在仿真研究状态和策略表达，不直接改变真实底层步态。

来源：[论文](https://arxiv.org/abs/2611.14186)。

---

## 5. ExRL：不重新训练整段动作，让策略学习“这一段执行到第几步”

**时间回补｜v1 2026-11-10 02:44 UTC｜arXiv:2611.13482**

### 为什么重要

VLA、Diffusion Policy、Flow Policy 通常一次产生几十个连续动作。越长的 Chunk，直接通过强化学习调整整个动作张量越贵；但**把全部 Chunk 一次执行完**也可能因场景变化、抓取失败而过期。

ExRL 冻结原策略，将在线适配变量从高维动作向量降为“当前 Chunk 实际执行长度”，由小型 Off-Policy RL 适配器依据观测决定何时重新规划。

### 算法模块

输入观察 → 原策略输出长 Chunk → 长度适配器输出执行步数 L → 仅执行前 L 步 → 新观察与奖励 → Off-Policy 更新长度适配器。它等价于在更低维的决策空间优化时间尺度，而不是重新学习每个末端动作。

### 实验、鲁棒性与工程风险

论文在多个仿真及真实操作任务报告提高样本效率，特别针对长 Chunk 策略；摘要没有一个对所有任务都有效的数值，不应凭空写成“统一加速 X 倍”。作者项目页已公开，但本次未独立确认可构建训练代码。

执行长度受推理、相机、通信及电机时延约束。动态障碍和抓取异常仍需要独立即时取消机制，不能等到预测 L 到期才检查。

### 最小复现与工程落地启发

固定同一 VLA/Chunk Checkpoint，在两个任务测试固定长度（5/10/20）、基于误差的启发式提前停止、ExRL 学习长度；记录成功率、每次任务模型调用次数、动作年龄、P99 和接触失败。适合语音机器人非流式动作块、机械臂 VLA、带动作预取的轮足导航。

来源：[论文](https://arxiv.org/abs/2611.13482) · [作者项目](https://exrl-project.github.io/)。

---

## 6. LEASH + RoboRisk：Jev 类决策模型给机器人加任务、动作与不可逆提交三道门

**时间回补｜v1 2026-11-10 UTC；官方代码/数据于 11 月 11—12 日发布｜arXiv:2611.14115**

### 为什么重要

LLM 能正确理解“移动水杯”，不代表当前路径安全。机器人朝相同坐标移动，如果抓着湿海绵可能没有问题，抓着满杯水跨过带电设备则有风险。**仅检查工具参数文字不足以判断是否安全，必须结合当前相机与执行状态。**

LEASH 使用三个 Safety Gate：

1. **Task Gate**：收到任务先检查拒绝边界；
2. **Action Gate**：每个动作或复合 Skill 执行前结合当前 RGB-D 场景检查；
3. **Commit Gate**：夹爪打开、倒液体等不可逆步骤前再次审批。

三道门与 Planner 共用一份安全策略，并按动作/任务发放短期许可，不让主 Agent 持有永久动作权限。作者使用 Jev 或其他决策 API 作为低延迟审查器；**这并不代表 jevos 开源权重与 TypeSafe Jev 直接兼容**。

### 实验结果及边界

RoboRisk 包含 **92 个仿真 + 13 个真机任务**，覆盖拒绝、计划修复、执行危险、提示注入及跨回合记忆。以作者所测 GPT-6 Astra 规划器为例：仿真 Harm Rate 从 **11.23% → 0%**，Safe Success Rate 从 **78.99% → 80.80%**；真实机器人实验中四种规划器各自观察到零次伤害，但每种仅 13 个真实任务，不能得出普适的零事故保证。所测仿真总体时间额外开销约 **1.66%**，门禁调用费用约 **$0.005/次任务**。

### 开源与最低复现

[LEASH 官方仓库](https://github.com/zhuqinfeng1999/LEASH) 为 MIT，包含 benchmark、research、Dobot 适配、测试数据；[RoboRisk 数据集](https://huggingface.co/datasets/zhuqinfeng/RoboRisk) 可公开获取。作者 README 提供 Python 3.11、特定 CUDA Torch、准备仿真运行时和启动单场景的详细步骤。最低先执行仓库文档中的 **P3-01 单任务仿真重置和 Benchmark**，不要先接真机或填真实密钥。模型门禁需要实际服务凭据，不能把 Harness 源码公开理解为完全无云端依赖。

### 风险、适用场景与工程启发

语义门禁不能代替机械臂动力学碰撞检查、急停、PLC/驱动器保护；视觉盲区和模型误判会漏检。适合机器人 VLA Skill 层，也值得借鉴到 Codex/MCP：给删除、部署、推送和修改生产库等操作设置**确定性权限门 + 语义复核**，但终极执行授权仍由实际系统控制。

来源：[论文](https://arxiv.org/abs/2611.14115) · [项目页](https://zhuqinfeng1999.github.io/LEASH/) · [源码](https://github.com/zhuqinfeng1999/LEASH) · [数据](https://huggingface.co/datasets/zhuqinfeng/RoboRisk)。

---

## 7. Is Your Robot's Memory Just a Clock?：无意义等待也会让 VLA 误判“任务已完成”

**时间回补｜v1 2026-11-10 18:47 UTC｜arXiv:2611.14488**

### 为什么重要

长任务机器人常按固定时间间隔抽取历史帧，附带时间戳并压缩到 Context。问题是训练演示动作大多连续进行，于是**时间本身成了任务进度的捷径**。在执行时故意插入几秒静止或轻微摆腕，虽然物体没有变化，记忆策略却可能认为任务正在正常推进并过早停止。

### 实验证据

在 RoboMME 两个计数任务中，作者只插入“Null Event”就让成功数分别从 **47/50 → 16/50**、**44/50 → 10/50**。若不将这些无效帧写入记忆，表现恢复；只删掉时间位置编码仍不能彻底修复，因为无效帧仍会占据固定采样记忆槽。

### 算法与理论边界

故障链为：固定时钟采样 → 无变化的观测占据记忆槽 → 时间与状态变化的虚假相关 → 模型认为进度已完成。作者发现**按真实事件建立记忆索引**能恢复一半或更多性能损失，而仅向训练加入暂停干扰未解决问题并可能伤害计数表现。

这说明以固定周期压缩历史并非普遍错误，但在需要精确计数或阶段判断的任务中，应该独立维护真实事件、成功回执与物体状态，避免由时间戳推断完成。

### 可复现性、适用场景与启发

目前主要核实论文和方法，完整独立重现实验代码尚未确认。可以用现有机器人动作/对话状态机测试三种情形：不动等待 5 秒、重复无效动作、真正完成动作；分别使用时间采样记忆与事件记忆，测完成状态误报、Token 占用与恢复次数。

**这对 SIP 语音 Agent、Codex 长任务和机器人操作 Agent 都很有价值：成功应来自已核实的事件，而不是工作过了多少秒。**

来源：[论文](https://arxiv.org/abs/2611.14488)。

---

## 8. One Policy for 100 Household Tasks：公开 VLA Checkpoint，也公开 Agent 工具协作边界

**时间回补｜v1 2026-11-10 UTC｜arXiv:2611.14432**

### 为什么重要

BEHAVIOR Challenge 2026 把长任务扩展到 100 项，既考查动作策略能否完成具体操作，也考查长任务的阶段、恢复和任务切换。

独立团队提交一套基于 π0.5 的**单一 2.9B VLA Checkpoint**，使用 21 维动作空间、语义阶段标签、多个 Flow Sample 的方差降低策略和约 **200K 训练步**；数据约 2.11 亿帧。为高难度 14 个任务，团队还尝试由工具调用 Agent 进行观察和动作执行。

### 实验结果及重要区别

| 指标 | 作者结果 |
|---|---:|
| 纯学习策略、100 任务 Q | **0.392** |
| 公榜综合提交 Q | **0.446** |
| 公榜完整任务成功率 | **27.3%** |
| 14 项 Agent 路线自身 Q | **0.639** |
| 同 14 项原学习策略 Q | **0.108** |

这是**不同协议或任务子集**的结果，不应混合成统一的成功率。论文明确表示 14 个 Agent 任务的真实训练实践会话未全部公开，因此不能仅凭仓库重现完整 Agent 路线。

### 源码、权重与复现入口

[Robot-Learning-Collective/behavior-1k-solution-2026](https://github.com/Robot-Learning-Collective/behavior-1k-solution-2026) 为 Apache-2.0，包含 agent、configs、scripts、模型服务和复现说明，权重在 [IliaLarchenko/BEHAVIOR2026VLA](https://huggingface.co/IliaLarchenko/BEHAVIOR2026VLA)。

~~~bash
git clone --recurse-submodules   https://github.com/Robot-Learning-Collective/behavior-1k-solution-2026.git
cd behavior-1k-solution-2026
# 依赖 Isaac Sim、BEHAVIOR-1K，环境准备成本较高
bash setup_remote.sh
~~~

作者公开的评测会使用六个仿真 Worker 同时推进，并记录可恢复的模拟器状态。建议先读复现实验文档，跑最小任务而不是一开始下载所有数据并启动百任务评测。

### 适合谁关注与工程落地启发

适合 VLA 长任务、Agent 调度、统一动作表征、仿真评测基础设施。最值得借鉴的其实是**基于任务阶段的动作接口、失败后的恢复状态快照、独立的训练与评测记录**；无需为了学习这套架构直接复现整个大模型训练。

来源：[论文](https://arxiv.org/abs/2611.14432) · [代码](https://github.com/Robot-Learning-Collective/behavior-1k-solution-2026) · [权重](https://huggingface.co/IliaLarchenko/BEHAVIOR2026VLA)。

---

## AI / LLM 附属框架与开源工程组件

### 组件 1｜Acquisition-State Telemetry：不看 Token 和动作数量，而监控“证据是否真的有进展”

**时间回补｜2026-11-10 UTC｜[原始论文](https://arxiv.org/abs/2611.14111) · [作者源码](https://github.com/dimipan/ast-telemetry)**

**痛点**：长时间 Agent 可以不断搜索、调用工具、写工作日志，却一直没有完成任务需要的证据。AST（Acquisition-State Telemetry）让应用将声明的任务要求转换成若干“是否已解决”的坐标，再用固定监控器输出 **Progress** 与 **Information Friction（信息摩擦）** 两个信号。重复读取几乎相同的证据而没有推进任务时，Friction 应上升；已完成任务后的合理静止不应被误报为停滞。

**接口和可运行性**：它不依赖主模型类型，输入是应用自己的 Task Binding、归一化比较数据与证据分数；作者在对话、MiniGrid、Crafter、MetaWorld 等八类任务上测试。代码仓库的真实 Python 工程位于子目录 ast_telemetry_anonymous_repo/ast-telemetry；要求 Python 3.10+，测试与复现使用 CPU，并提供已缓存的部分模型评分，无需每次发起新的 LLM API 请求。

~~~bash
git clone https://github.com/dimipan/ast-telemetry.git
cd ast-telemetry/ast_telemetry_anonymous_repo/ast-telemetry
python -m venv .venv && source .venv/bin/activate
pip install -e ".[envs,rl,test]"
# 按 README 准备所需的公开数据及 AST_DATA 路径
pytest
./reproduce.sh studies
~~~

**适合 Codex / T3 Code 的用法**：不是立即让模型读更多日志，而是先定义“定位故障=找到出错模块/复现证据/有效补丁/测试通过”四个 Task Condition，再把新的工具结果转换成已满足条件。若多次读取相同文件而证据毫无变化，可提示中止重复调查或更换搜索策略。

**工程风险与 A/B**：Task Binding 仍需人为设计，自动赋分不一定正确；它不保证停滞判断总是正确，也不是通用监控 SaaS。选 20 个已知问题，对比仅统计工具次数和 AST Progress/Friction 的停滞识别准确率、误报与额外执行开销。**源码和复现命令已核验；本次未本地运行。**

### 组件 2｜retrieval-lens：给 SAG/RAG 检索增加可回放、可比较的证据日志

**工程补充回顾，非 11 月 13 日首发｜[作者开源仓库](https://github.com/Vbj1808/retrieval-lens)**

**痛点**：SAG2、BM25、向量检索返回错误回答时，需要先知道错在**检索没有找到正确片段**，还是**模型拿到正确片段却解释错误**。retrieval-lens 是 TypeScript/MCP 的轻量“检索飞行记录仪”，提供 retrieval_observe、retrieval_query、retrieval_diff、retrieval_stats 四个工具，记录每次查询、Chunk、评分、来源及顺序，并可比较变更前后的证据排名。

~~~bash
# 验证包的实际启动入口
npx -y retrieval-lens
# 在 Codex 环境中按需接入（先核查 Codex MCP 配置）
codex mcp add retrieval-lens -- npx -y retrieval-lens
codex mcp list
~~~

**重要限制**：它不自动拦截所有 MCP 工具的返回值；需要你的检索管道**明确调用 retrieval_observe** 上报结果。仅安装服务并不能完成 SAG2 全链路观测。作者 README 已确认 MIT 许可证与运行入口，本轮未核实实际 RAG 回放的完整兼容性测试。

**A/B 建议**：固定 30 个跨文档问题，分别保存 BM25、SAG2+Jev、本地 Reranker 的检索结果；在相同问题和 Index 版本下调用 retrieval_diff，检查真正证据是否进入 Top-5、排名变化和平均查询耗时。对私有代码库应避免把整段源码、Token 或秘密信息直接写进无访问控制的检索记录。

---

## AI Coding 实战技巧精选

### 技巧 1｜用 rr 给 Codex 一条可以反复回放的 C++ 崩溃执行轨迹

- **来源**：[rr-debugger/rr 官方仓库](https://github.com/rr-debugger/rr) · [rr 安装与系统要求](https://github.com/rr-debugger/rr/wiki/Building-And-Installing)。
- **一句话结论**：间歇性的 SIGSEGV、线程竞态或初始化崩溃，不应反复让 Codex 猜测；先通过 rr 记录一次真实失败，再用 GDB 反向回放找到错误发生前的上下文。
- **具体怎么做**：在支持 rr 的 Linux x86-64 机器上准备含 Debug Symbol 的**CPU 测试程序**，先运行 rr 的系统兼容检查，然后记录、复现：

~~~bash
rr check
rr record ./your-test-program
rr replay
# 进入 gdb 后：bt / reverse-continue / watch 等
~~~

- **适合什么场景**：C++/ROS2、难复现的内存与线程错误，以及需要把真实 Backtrace/变量演变交给 Codex 分析的任务。
- **注意**：rr 依赖 Linux perf/CPU、Kernel 配置，某些 GPU、实时、容器和多进程负载不受支持；不要直接用 rr 包住整套 CUDA/驱动器或高负载真机控制。先在最小 CPU 复现程序验证平台兼容。录制内容可能包含敏感输入。

### 技巧 2｜Codex 修补丁并 Rebase 后，用 git range-diff 证明补丁语义没漂移

- **来源**：[Git 官方 range-diff 手册](https://git-scm.com/docs/git-range-diff)。
- **一句话结论**：普通 git diff 展示两个文件树的差异，range-diff 则比较**两组提交补丁**，非常适合 Codex 在独立 Worktree 修复、Rebase 或重写提交之后检查有没有漏掉原本修好的内容。
- **具体怎么做**：

~~~bash
# 假设 base、feature-before、feature-after 都是本地已知的引用
git range-diff base..feature-before base..feature-after
git diff --check feature-after
git log --oneline base..feature-after
~~~

- **适合什么场景**：T3 Code 的多个 Worktree、Codex 多轮补丁、大仓库的 PR Rebase/Cherry-pick。
- **注意**：range-diff 输出适合人阅读而非当作稳定的机器接口；如果两组提交的基准不同或有 Merge Commit，需要按 Git 官方说明调整比较范围。比较通过也不能替代编译与回归测试。

---

## 经典论文回顾

### iSAM2: Incremental Smoothing and Mapping Using the Bayes Tree

**作者**：Michael Kaess、Hordur Johannsson、Richard Roberts、Viorela Ila、John J. Leonard、Frank Dellaert。**2011-12-20 首次在线发表，2012 年 2 月刊于 IJRR 31(2):216–235。** [原始 DOI](https://doi.org/10.1177/0278364911430419) · [CMU 作者记录](https://www.cs.cmu.edu/~kaess/pub/Kaess12ijrr.html) · [GTSAM](https://github.com/borglab/gtsam)。

### 核心问题、数学思想与历史位置

SLAM 中位姿图不断新增 IMU、里程计、回环因子。每来一个观测就重新求解整个稀疏非线性最小二乘问题，在长走廊或跨楼层地图中会造成不必要的计算。

iSAM2 使用 **Bayes Tree** 表达稀疏因子图的条件概率和平方根信息矩阵，使新因子只影响局部相关 Clique；同时增量重线性化和变量重排序，避免周期性完整 Batch 计算。简化工作流：

    新激光/里程计/回环因子
              ↓
       更新受影响 Bayes Clique
              ↓
        局部重线性化与变量消元
              ↓
           增量状态更新
              ↓
        查询当前地图位姿估计

### 观测假设、仍有效的思想与后续限制

iSAM2 不自动判断回环是否错误，也不负责前端特征提取。里程计退化、错误数据关联和动态物体必须由可靠前端、鲁棒核或 Switchable Constraints 等机制处理。

它今天仍是多传感器因子图、回环优化和持续融合定位的重要基础。但对于海量 LiDAR 点级残差，如果未经选择全部塞进优化后端，Bayes Tree 同样会变得庞大。

### 现代代码与最小复现

GTSAM 中有 ISAM2。可以构造 1000 个位姿链，在第 500 个节点后追加一条强回环因子；比较每次 Batch 优化与 iSAM2 的每次更新耗时、重线性化变量数、最终地图残差和错误回环后的恢复。再分别测试一个、两个和三个 LiDAR 提供的候选约束。

**对已有三雷达平台的重新解读**：前端不必对三个雷达的每个点都建因子。高质量主里程计维持实时性，其他雷达主要在不同方向几何退化时补充关键位姿约束；iSAM2 负责增量后端一致性。这样比简单拼接全部点云更有机会提高精度/算力比。

---

## 今日结论

今天的共同主题是：**不要把模型预测等同于可执行的物理事实，也不要把 Agent 持续活动等同于任务进展。**

Safe Depth 把预测不确定性转成对导航真正有影响的安全距离，FAME-QP 让带约束求解进入更严格的 GPU 控制预算，SIGMO 解决会车中的互动让行，ExRL 决定何时结束一段预生成动作。LEASH 将 Jev 这类轻量判断器真正插在机器人执行路径中，而不是只做事后安全文字总结；VLA 记忆研究进一步提醒我们，事件比“经过了多久”更适合标记任务阶段。AST 与 retrieval-lens 则为 Codex/LLM 工作流提供可诊断的信息获取证据。

**当日首选验证：FAME-QP 的真实 RTX 控制 P99、LEASH 仿真 Task/Action/Commit 门禁、以及 Codex 的 rr/range-diff 工程回归。** 后两项尤其适合通过最小实验直接判断是否省时间，而不需要扩建一套新 Agent 基础设施。

## 最值得深入研究或尝试复现的方向

| 优先级 | 方向 | 最小可核实指标 |
|---|---|---|
| P0 | FAME-QP | 相同 QP 容差下 Setup/Warm Start/矩阵更新 P99 |
| P0 | LEASH | RoboRisk 单场景门禁阻断率、误拒绝与执行开销 |
| P0 | rr + Codex | 一个真实 C++ 问题的可重放轨迹及最小修复 |
| P1 | Safe Depth | Nav2 误停车、近障高估、碰撞/到达率 |
| P1 | SIGMO | 双机器人走廊死锁率、最小净空和通行耗时 |
| P1 | ExRL | 动作块有效期、模型调用数、抓取成功率 |
| P1 | AST | 多次重复无信息调用时的检测率、误报 |
| P1 | retrieval-lens | SAG 与 BM25 证据排名/召回的可回放比较 |
| P2 | Koopman RL | 一步误差、环境样本效率、真实控制延迟 |
| P2 | VLA Clock Memory | 插入等待后计数完成误报与恢复率 |
| P2 | 百任务 VLA | 固定 Checkpoint 的单任务评测和恢复状态 |
| P2 | iSAM2 | 回环后局部更新成本、错误回环处置 |

## 参考资料

**检索列表**：[arXiv Robotics 新论文](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering 新论文](https://arxiv.org/list/cs.SE/new) · [Robotics 最近批次](https://arxiv.org/list/cs.RO/recent)。

**感知与规划**：[Safe Depth](https://arxiv.org/abs/2611.13769) · [FAME-QP](https://arxiv.org/abs/2611.13766) · [FAME-QP 官方实现](https://github.com/santoshrajkumar/fame-qp) · [SIGMO](https://arxiv.org/abs/2611.14414) · [Koopman MBRL](https://arxiv.org/abs/2611.14186) · [ExRL](https://arxiv.org/abs/2611.13482)。

**机器人安全与 VLA**：[LEASH 论文](https://arxiv.org/abs/2611.14115) · [LEASH 源码](https://github.com/zhuqinfeng1999/LEASH) · [RoboRisk 数据](https://huggingface.co/datasets/zhuqinfeng/RoboRisk) · [Memory Temporal Shortcut](https://arxiv.org/abs/2611.14488) · [BEHAVIOR 100 任务论文](https://arxiv.org/abs/2611.14432) · [Checkpoint 与代码](https://github.com/Robot-Learning-Collective/behavior-1k-solution-2026)。

**AI 附属组件与 Codex**：[AST 论文](https://arxiv.org/abs/2611.14111) · [AST 代码](https://github.com/dimipan/ast-telemetry) · [retrieval-lens](https://github.com/Vbj1808/retrieval-lens) · [rr](https://github.com/rr-debugger/rr) · [Git range-diff](https://git-scm.com/docs/git-range-diff)。

**经典论文**：[iSAM2 DOI](https://doi.org/10.1177/0278364911430419) · [作者记录](https://www.cs.cmu.edu/~kaess/pub/Kaess12ijrr.html) · [GTSAM](https://github.com/borglab/gtsam)。
