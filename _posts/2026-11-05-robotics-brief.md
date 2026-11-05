---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-05"
date: 2026-11-05 09:00:00 +0800
description: "CoReMatch连续坐标匹配、机载Hamilton–Jacobi可达性、G1 iLQR-MPC、具身导航安全架构、WayTrace城市导航、VLA量化实测、RoboScope评测并行化和Agent Skills演化研究。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-05

## 摘要

**检索基准：2026-11-05 08:59（Asia/Shanghai，星期四）。** arXiv 可核查的最新常规公开列表为 **2026-11-04（星期三）**，其中 cs.RO 列表合计 **125** 项、首次新提交 **56** 项；cs.SE 合计 **43** 项、首次新提交 **17** 项。总数包括交叉收录与替换版本，不能全部视为新论文。首先检查最近 24 小时，再扩展至最近七天，选取 8 项经过标题、arXiv ID、DOI、项目主页和仓库地址联合查重的工作；与本仓库此前 1,227 条记录均不重复。入选论文的 arXiv v1 实际于 **11 月 2—3 日 UTC** 提交，均标记“时间回补”，不把本日简报时间误写成论文首次发表时间。

**今天的优先结论：** 机器人闭环的可靠性需要四个独立的预算：观测匹配的像素精度与延迟、规划器的安全可恢复集合、动作在真实底盘上的有效期、以及模型评测的真实吞吐与量化速度。仅仅提高视觉模型得分、把动作模型量化成 INT4 或让高层 VLA 看见一张更好的地图，都不能替代这些预算。

**建议立即研究：** CoReMatch 对现有 VIO/SLAM 特征前端的计算收益；在线 HJ 可达性求解的维度与 GPU 边界；WayTrace 把地图指令变成像素路径的导航架构；LoopQ 对“4-bit 必定更快”的反例；RoboScope Kit 已公开的评测工程。AI Coding 方面，工具行为契约与 Skill 回归验证比不断堆叠冗余提示词更值得投入。

资料入口：[arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)。

---

## 1. CoReMatch：连续坐标迭代匹配，把视觉 SLAM 的亚像素精化从高分辨率网格中解耦

**时间回补：arXiv v1 2026-11-02 20:36 UTC；CoRL 2026 接收。**

### 为什么重要

视觉里程计、回环验证和重定位，都依赖图像间具有几何一致性的对应点。LoFTR 类半稠密网络通过在固定离散网格上预测匹配置信度取得较好鲁棒性，但精细定位往往需要更大网格、显存与计算开销。CoReMatch 不直接输出越来越高分辨率的置信图，而是在**连续二维坐标空间**循环改进已有对应点。

### 算法模块与传感器假设

模块链为：图像对 → 低分辨率初始特征 → Deep Aggregated Transformer 提供全局几何上下文 → 循环更新连续匹配坐标 → 轻量回归头局部亚像素精化 → 置信匹配集合 → RANSAC/PnP/三角化等下游视觉几何。

连续坐标并不意味着天然具备高精度深度。其稳定性依赖摄像头内参、图像间重叠率、真实视差、光照和纹理。低纹理、动态人车与重复廊道依然可能造成错误匹配，进入图优化前仍需几何外点检查。

### 实验、实时性与鲁棒性

作者报告在室内、室外匹配基准中精度高于 Efficient LoFTR，并在其测试的**边缘硬件**上获得超过 **10 倍**的运行速度优势。该数字属于特定输入尺寸、实现与设备组合，不能直接宣称 RK3588 或 RTX 5070 上必然快十倍，更不是完整 VIO 的端到端 FPS。

### 可复现性、风险与适合谁关注

公开论文已核实；本轮未独立确认官方完整源码或经过部署验证的 ONNX/RKNN。优先用相同数据对比 Efficient LoFTR、CoReMatch、传统 SuperPoint+LightGlue：测正确匹配率、匹配坐标残差、匹配耗时、内存占用和 PnP/VO ATE。除匹配精度外，还要统计 RANSAC 后内点比例、弱纹理走廊和强背光下的恢复能力。

**适合：** VIO、视觉重定位、单目/双目 SLAM、边缘视觉前端。**工程落地启发：** 不要仅凭特征匹配网络 Benchmark 更好便改动整个 SLAM；先把它作为可切换的前端，保持相同后端和点选择策略做 A/B 测试。

原始来源：[CoReMatch 论文](https://arxiv.org/abs/2611.03932)。

---

## 2. Online HJ Reachability：Hamilton–Jacobi 安全集从离线计算进入 GPU 在线控制循环

**时间回补：arXiv v1 2026-11-03 00:11 UTC。**

### 为什么重要

对黑箱 VLA、强化学习导航或传统 MPC，碰撞预测往往受模型概率和局部线性化影响。Hamilton–Jacobi（HJ）可达性把受控动力学和有界扰动形成的可达集合写为 Hamilton–Jacobi–Isaacs 偏微分方程，通过求解后向可达管（BRT），确定哪些状态在指定时域内可能进入危险集合。

历史难点是网格维度灾难：状态维数每增加一维，离散网格的存储和计算代价都会快速增长。新研究使用 CUDA 实现 WENO5 空间离散、TVD-RK3 时间积分和 Lax–Friedrichs 数值通量，使**2D/3D/4D 低维动力学**的 BRT 可以在线刷新。

### 算法模块与理论假设

动力学模型 + 控制/扰动边界 → 风险终端集合 → HJI 方程数值迭代 → 在线 BRT/安全值函数 → 策略命令过滤或避让控制。多智能体示例增加 GPU 内标签传播，一次求解生成多个追逐者的捕获域划分。

可达性保证受模型、边界、网格和数值误差限制；把 3D 平面相对运动的结果写成完整 12 状态四旋翼保证，是不成立的。实际风场超出扰动集合、执行延迟大于设计值或碰撞几何建模错误，均会让保证失效。

### 定量结果

| 指标 | 作者指定配置 |
|---|---:|
| RTX 4000 Ada，FP32，3D Air3D BRT | **112 Hz** |
| 同卡，FP32，4D 追逐—逃逸 | **61 Hz** |
| Jetson AGX Thor，Air3D，N=41 | **66 Hz** |
| Jetson AGX Thor，2D 漂流模型 | **54 Hz** |
| 六架四旋翼野火响应模拟中的多智能体核计算 | **4.0 ms/tick** |

对同精度 JAX 参考求解器，所选任务的工作站加速在 **5.9–17.5 倍**范围内。作者还在 FP64 中检查了多个经典数值测试，与 Mitchell Air3D 参考解的栅格计数差在 0.04% 以内。**注意：4.0 ms 是所述核计算，不等于所有传感、图构建与电机命令的端到端控制周期。**

### 可复现性、工程风险与适合谁关注

本轮确认了论文和公开数值指标，尚未独立核验完整作者代码仓库。可先复现二维双车碰撞和三维 Air3D，用相同网格、边界和 FP32/FP64 精度比较 JAX 与 CUDA，并验证 BRT 边界、最大扰动和数值一致性。下一步在轮式机器人中只对相对位姿/速度等低维状态使用 HJ 安全层，保留急停冗余。

**适合：** 轮式机器人局部避障、无人机风险控制、多机器人交叉会车和 VLA 安全包装。**工程启发：** 在明确维度和模型假设时，形式化可达性有机会变成在线安全工具；但不能用局部安全层代替全局可通行性与死锁处理。

原始来源：[在线 HJ 可达性原论文](https://arxiv.org/abs/2611.04096)。

---

## 3. Online iLQR-MPC + WBC：G1 以 100 Hz 同时调整足步与接触力

**时间回补：arXiv v1 2026-11-03 02:42 UTC。**

### 为什么重要

人形机器人受到推搡后，单独修改步点再由另一控制器解决接触力，可能产生两个模块之间的动态不一致。该研究将**落脚位置与接触力**放进同一个滚动时域优化，通过单刚体模型保持机身姿态和完整接触力矩信息。

### 算法模块与动力学假设

状态与接触时序 → Single Rigid Body Dynamics → iLQR-MPC 联合优化足步/接触力 → 增广拉格朗日与松弛 Barrier 处理约束 → 全身控制器映射关节力矩 → 执行反馈 → 下一次 MPC 更新。

系统并不需要重新训练平台专用 RL 策略，但依赖准确的质量惯量、接触切换、摩擦锥、足底支撑区域和执行器限幅。单刚体近似对大幅摆臂、负载变化和强烈碰撞的描述有限。WBC 的 500 Hz 也不能自动提高上游 100 Hz 的计划更新频率。

### 实验结果

MuJoCo 中，iLQR-MPC **100 Hz** 重规划、平均求解时间 **8.9 ms**；WBC **500 Hz**。Unitree G1 仿真在平稳行走之外还能从 **245 N 前向推力和 175 N 横向推力**的脉冲扰动中恢复。该数字没有给出真实 G1 的可靠恢复概率、P99 求解时间或对不同地面的稳定性认证。

### 可复现性、风险与适合谁关注

当前未独立核实完整开源工程。建议以公开 MuJoCo G1 模型在相同接触脚本下比较固定落脚点 MPC、独立 Footstep Planner + MPC 和联合 iLQR；记录失败率、足端滑移、求解 P95/P99、瞬时接触力及关节力矩饱和。

**适合：** G1、人形步态 MPC、模型式 WBC。**工程启发：** 与其不断叠加动作后处理，不如把真实需要协同变化的足步和接触力放进同一优化，但必须对最坏周期而非均值 8.9 ms 做实时设计。

原始来源：[iLQR-MPC 原论文](https://arxiv.org/abs/2611.04204)。

---

## 4. Caging Legged-VLN：让 VLA 决定去哪里，让 SDF、MPPI 与 Barrier 决定能否安全去

**时间回补：arXiv v1 2026-11-03 14:29 UTC。**

### 为什么重要

VLM/VLA 擅长解释“进入门厅后左转”，但不具备可靠的地形净空、制动距离或三维碰撞约束。直接把语言模型输出的路径当作速度命令，会把语义推理失误传给机器人的底层执行。

这项研究采用**高层语言规划 + 低层物理约束导航**的分层结构。高层保持可替换，低层对真实机器人状态和现场三维几何负责。

### 算法模块与传感器假设

语言/图像 → VLA 生成语义目标或粗路线 → 状态估计与现场三维点云 → SDF 距离场 → 低维 Bézier 参数化 MPPI 候选 → Discrete Exponential Barrier Function（dEBF）约束 → 可执行轨迹 → 底盘控制器。

SDF 是当前建图范围内的几何距离表示，不会自动表达不可见障碍、人群意图或楼梯中机器狗完整的多接触安全。dEBF 碰撞保证要求距离场、动态模型、观测延迟和约束参数满足相应条件，不能把它解释为任意环境下的安全认证。

### 实验与实时性

作者报告在真实人形和四足机器人上进行了广泛实验，展示语言引导导航与障碍约束的一体化；可核查的摘要中没有统一 P99、碰撞率或跨平台任务成功率数字，因此不补造。尚未独立确认成熟官方开源源码。

### 工程复现路线

对已有 FAST-LIO + 3D 地图的机器狗，先在 Shadow Mode 保留厂商底盘控制：高层 VLA 只提交局部目标，SDF/MPPI 计算安全轨迹，底层 SDK 根据速度、净空与急停策略裁剪。比较无障碍过滤、普通 ESDF MPPI 和 dEBF 安全层的最小净空、不可行率、滞后命令丢弃率与规划 P99。涉及台阶时必须增加完整机身包络与接触模式限制。

**适合：** 四足/轮足自然语言导航、人形移动任务、3D 局部绕障。**工程启发：** 不必让大模型理解所有动力学；让高层负责语义，让实时局部层负责可验证的几何安全。

原始来源：[Caging Vision-Language Navigation 原论文](https://arxiv.org/abs/2611.04972)。

---

## 5. WayTrace：把在线地图指引转成视觉路径轨迹，轮足机器人完成 1.37 km 城市任务

**时间回补：arXiv v1 2026-11-03 16:13 UTC；论文处于评审中。**

### 为什么重要

城市机器人跨区域巡检的路线往往首先来自 Web 地图和步行指引，但“前方路口过马路”不是能直接交给底盘的轨迹。只用 GNSS 点目标也容易在高楼、树荫或密集道路附近偏离人行道。

WayTrace 采用三级抽象：Web 地图指引 → 一条当前可执行的原子语言指令 → 图像上的路径 Trace → 低层 RL 跟踪。VLM 不直接输出电机命令，语义与几何中间层明确可检查。

### 算法模块与观测假设

卫星地图、逐向导航文字、最近的机载图像 → VLM Orchestrator 生成“在左侧人行横道过马路”等原子命令 → 在超过百万条街景自动标注样本上训练的视觉 Trace Predictor → 图像中的路径曲线 → RL 跟踪控制器 → 机体运动与新观测。

Trace 需要正确的相机安装、姿态、道路分割与路径时序，像素上的一条线不直接约束轮足机器人在楼梯上的摩擦、全身姿态或动态行人安全；城市交通还需要额外法规和人工许可约束。

### 实验结果

在较长距离仿真任务中，作者报告对 GNSS 噪声更有鲁棒性，离开人行道/斑马线的违规次数相对 Point-goal 对照少约一个数量级。真实轮足机器人已完成**最长 1.37 km、约 1.1 m/s**的城市中心、大学园区和乡间路线，包含人行横道、楼梯及施工区域。

该里程是特定路线的成功案例，不构成任意城市可自动通行的安全保证；也没有在摘要中给出统一行驶成功率或机载 P99。

### 可复现性、风险与适合谁关注

作者公开了[WayTrace 项目页](https://way-trace.github.io/)；本轮未独立确认端到端可构建仓库及策略权重。可先在录制视频上让 VLM 输出原子目标，比较 GNSS Waypoint、自然语言目标和视觉 Trace 对人行道中心偏差的影响。再由传统几何规划器监督 Trace 的可执行性。

**适合：** 轮足长距离跨区导航、户外巡检、视觉语言导航。**工程启发：** “地图指引→语义原子动作→几何 Trace→底盘”是比让 VLM 直接输出速度更清晰的跨层接口；这对跨楼层巡检同样具有架构参考意义。

原始来源：[WayTrace 原论文](https://arxiv.org/abs/2611.05129) · [官方项目](https://way-trace.github.io/)。

---

## 6. LoopQ：INT4 的 VLA 显存少了，但 H100 和 Jetson 未必变快

**时间回补：arXiv v1 2026-11-03 15:51 UTC。**

### 为什么重要

端侧 VLA 量化经常把“模型变小”直接等同于“闭环更快”。实际上推理时间还与量化内核、主干与 Action Expert 的计算比例、Batch Size、框架有关。

LoopQ 将 RTN、AWQ、GPTQ、ActQuant、QuantVLA 放在**相同 Checkpoint、量化层、执行引擎和闭环任务**下比较，覆盖四种 VLA、超过 **180,000** 个 LIBERO/LIBERO-plus 回合，并在 H100、L4、Jetson AGX Thor 上评测。

### 模块与测试假设

原始模型 → 固定同一组需量化的层 → 切换 PTQ 方法和内核 → 检查实际低比特存储 → 统一视觉/动作推理引擎 → 同一闭环扰动任务 → 测量任务成功、端到端延迟与显存。不要将仅改变量化层或不同版本的 CUDA Runtime 的结果放在同一排行榜中比较。

### 关键实验结果

| 作者报告 | 结果 |
|---|---|
| 真实低比特模型内存降低 | **2–3 倍** |
| 4-bit 通用 RTN/AWQ/GPTQ | 成功率可达到或超过受测 VLA 专用方法 |
| LIBERO-plus 扰动下的隐性退化 | **1.5–4.3 个百分点** |
| H100 Batch=1，受测量化 π0.5 / OpenVLA-OFT | 比 16-bit **慢 1.06–1.58 倍** |
| L4 使用特定 INT8 Kernel | **快 4–14%** |
| Thor 受测 4-bit 组合 | **均变慢** |
| 仅切换执行引擎造成的延迟差异 | **2.1 倍** |

作者还指出，π0.5 的 Action Expert 占 63% 的 GPU 时间、但只占 13% 参数，而且在受测方案中仍以 16-bit 运行。仅量化大主干当然不保证整体明显提速。

### 实时性、可复现性与风险

论文对一些已有公开 VLA 量化实现进行了复现检查，但本轮未确认 LoopQ 自身完整官方源码和所有模型权重，不能称为开箱即用。真实部署至少测端到端摄像头→动作块的 P50/P95/P99，并在动态扰动任务中重新评价成功率；不要只看静态 LIBERO。

**适合：** Jetson、端侧 VLA、Flow Action Expert、量化工程。**工程启发：** 如果目标是吞吐或闭环时延，应先 Profile，再选对瓶颈算子有真实加速内核的量化方法。

原始来源：[LoopQ 原论文](https://arxiv.org/abs/2611.05093)。

---

## 7. RoboScope Kit：独立调度仿真 Worker 与策略副本，保持评测语义而提高 GPU 利用率

**时间回补：arXiv v1 2026-11-02 19:20 UTC。**

### 为什么重要

机器人 VLA Benchmark 一次运行数百回合，耗时并不全部来自 GPU 推理。很多模拟器执行占用 CPU，策略 GPU 却处于等待状态。作者 Profile StarVLA 官方评测时，观察到 GPU 平均利用率只有 **14.3%**。

RoboScope Kit 为每个策略封装一次 Policy 接口，为每个 Benchmark 封装单独 Adapter，保持原评测规则与评分定义不变。运行时将仿真 Worker 和 Policy Replica 分为两个资源池，用短时间 Probe 自动选择并发组合，同时跳过 Action Chunk 策略不读取的中间图像渲染。

### 算法/系统模块

基准适配器 → 数据观测格式校验 → CPU Simulator Workers → Policy Replica GPU 池 → 批量调度与结果回传 → 每回合独立记录 → 与官方终止条件一致性检查。可选 CUDA MPS 允许多个副本的 GPU Kernel 并行执行。

### 量化结果

| 场景 | 作者报告 |
|---|---|
| LIBERO-Long，RTX 4090 48 GiB，12 Worker / 3 Replica | **4.45 倍**于 StarVLA 官方评测 |
| 同场景，启用 CUDA MPS，16 Worker / 4 Replica | **6.16 倍** |
| RoboTwin Easy，四 GPU，500 回合 | **14.4 分钟** |
| 相对指定 RoboTwin 单 GPU 对照 | **25.04 倍** |

作者报告在这些对照中成功结果和终止步数一致。**这不是 VLA 实际在线控制频率提高 25 倍**，更不能把四 GPU 加速全部归因为模型推理优化。

### 开源与工程落地

**已核验官方仓库：** [MINT-SJTU/RoboScope-Kit](https://github.com/MINT-SJTU/RoboScope-Kit)；[项目页](https://roboscope.pages.dev/)。

可先在相同模型、数据集、GPU 上保留官方评测脚本作为 Ground Truth，逐步启用不同 Worker/Replica 组合，再比较成功率、实际 Episode 步数、显存峰值、CPU 利用率与分钟/500 Episodes。对多模型实验，尤其要固定随机种子和仿真版本。

**适合：** VLA Benchmark、大规模机器人 RL 评测、多 GPU CI。**工程启发：** 不必先更换更大 GPU，先把仿真和推理并发资源配置正确，通常更容易提升实验吞吐。

原始来源：[RoboScope Kit 论文](https://arxiv.org/abs/2611.03850) · [官方代码](https://github.com/MINT-SJTU/RoboScope-Kit)。

---

## 8. 84,200 个 Agent Skills 的演化研究：Skill 的问题不只是写得少，而是缺少执行契约与回归

**时间回补：arXiv v1 2026-11-03 07:46 UTC。**

### 为什么重要

Codex、Claude Code 和自研 Coding Agent 越来越依赖跨模型共用的 Skill。Skill 内容一旦与仓库 API、命令参数或工具权限脱节，模型可能在看似正确的流程中执行错误操作。许多 Skills 又在重复讲述同样的通用工作原则，增加上下文成本。

研究《How Agent Skills Evolve》分析 GitHub 上 **84,200 个 Skills、750,898 次 Commit**，建立 Skill 组成、变更类型和动机分类。

### 核心发现

研究指出五种趋势：可靠性验证和恢复机制在 Skill 设计中相对被忽略；项目耦合的 Skill 更容易随代码变化；多数修改属于小步补充或完善；冗余内容是真实维护问题；仅以“安全修订”为名的文本变化不一定显著降低风险。

这是一项仓库生态实证研究，不是比较不同 Skill 写法在 SWE-bench 上的成功率实验，不能从数量直接推断某种设计一定让模型提高多少百分点。

### 对 AI Coding Harness 的工程价值

对长期 C++/ROS2 项目，可以将 Skill 拆成最小三层：**何时使用**、**可执行的仓库/工具约定**、**独立验收和失败恢复**。例如 ROS2 移植 Skill 不应只写“遵守最佳实践”，而要明确如何构建、启动节点、检测 Topic/Service 兼容性以及失败时怎样回滚。

对于高风险的 GitHub 写入、部署和数据删除，Skill 文本不是权限边界；实际执行器需要最小权限及独立确认。

### 可复现性与风险

论文及数据规模已核实，尚未确认可直接运行的官方 Skill 分析工具。最小内部实验是从 10 个常用 Skills 中抽取实际任务，移除重复说明，添加一条可执行验收；用同一模型和仓库 Commit 做 A/B，比较通过率、无关文件改动、Token 和误操作。

**适合：** Codex/Claude Code 共享 Skills、多项目 Monorepo、长任务 Agent。**工程启发：** Skill 不需要成为小型需求管理体系；重要的是与当前仓库同步、可执行、能回归。

原始来源：[How Agent Skills Evolve 论文](https://arxiv.org/abs/2611.04456)。

---

## AI Coding 实战技巧精选

### 技巧 1｜更新 Copilot CLI 预发布，保护损坏的 settings.json 不被单项设置覆盖

- **来源**：GitHub Copilot CLI 团队，2026-11-03 23:34 UTC（北京时间 11 月 4 日 07:34），[v1.0.106-7 官方 Release](https://github.com/github/copilot-cli/releases/tag/v1.0.106-7)。
- **一句话结论**：新版在设置文件无法读取或无效 JSON 时，修改单项设置将**拒绝写入并保留原文件**，而不是用一个设置覆盖整个配置；同时过滤插件名称、命令输出中的终端控制字符。
- **具体怎么做**：
  1. 在临时 HOME 或隔离容器安装预发布并确认版本：npm install -g @github/copilot@prerelease；copilot --version。
  2. 备份测试用 settings.json，故意写入无效 JSON（只使用虚构数据）。
  3. 在 Copilot CLI 的 /settings 中改变一个无害选项；确认显示错误，且原 settings.json 的 Hash 与内容不变。
  4. 复原合法配置，使用 copilot config 核查 Fusion tier 选项；在独立 Test Repo 验证插件名称无法借控制字符改变终端显示。
- **适合什么场景**：Linux Copilot CLI、多个 Skill/MCP 插件、自动化配置管理。
- **注意**：这是预发布版本；“拒绝覆盖损坏配置”不是完整的权限沙盒，不能消除 Shell/MCP 的外部副作用。

### 技巧 2｜Gemini CLI ACP 会话恢复与 Rootless Podman 沙盒做成最小回归

- **来源**：Google Gemini CLI 官方 Nightly，2026-11-04 01:20 UTC，[v0.67.0-nightly.20261104.g89e9d25d6](https://github.com/google-gemini/gemini-cli/releases/tag/v0.67.0-nightly.20261104.g89e9d25d6)。
- **一句话结论**：更新修复 ACP session/load 在历史 Replay 未完成前响应的问题，并为 Rootless Podman 沙盒传入 --userns=keep-id；Hook 还支持 SubagentStop 映射。
- **具体怎么做**：
  1. 在隔离测试机确认 Nightly 版本，备份现有 Gemini 配置；不要在生产 Agent 自动升级到 Nightly。
  2. 构造一个包含多条工具回执的无害 ACP 会话，保存后 session/load，再立刻查询之前产生的结果；核对历史回放完成后才恢复下一步操作。
  3. 在 Rootless Podman 测试容器中使用原用户 ID 创建一个临时文件，验证容器内外文件权限一致；记录 --userns=keep-id 是否生效。
  4. 为测试子 Agent 配置仅写入临时日志的 SubagentStop Hook，验证只执行一次。
- **适合什么场景**：Gemini CLI、ACP IDE 集成、Podman 开发容器、子 Agent Hook。
- **注意**：这不是对所有 Rootless 存储驱动或文件挂载的保证；必须另行限制宿主目录挂载与外部 API 权限。

---

## 经典论文回顾

### Mitchell、Bayen、Tomlin（2005）：A Time-Dependent Hamilton-Jacobi Formulation of Reachable Sets for Continuous Dynamic Games

**发表时间与历史位置：** *IEEE Transactions on Automatic Control*，2005 年 7 月，第 50 卷第 7 期，947–957 页；DOI：[10.1109/TAC.2005.851439](https://doi.org/10.1109/TAC.2005.851439)。[加州大学伯克利作者/机构记录](https://its.berkeley.edu/publications/time-dependent-hamilton-jacobi-formulation-reachable-sets-continuous-dynamic-games)。

### 核心问题与数学思想

给定机器人动力学、可用控制输入和可能的外部扰动，哪些初始状态会在指定时间内不可避免地进入危险集合？论文证明，在适当连续动态博弈假设下，后向可达集合可以表示为一个时间依赖 Hamilton–Jacobi–Isaacs 方程的**黏性解的零下水平集**。

它把安全问题从“规划轨迹上有没有碰撞”提升为“给定最坏扰动和最优控制，哪些状态仍然无法避免危险”。由于值函数在状态空间连续，可以使用 Level Set 数值方法求解与跟踪危险区域边界。

### 算法结构

危险目标集合 → 选择终端隐式值函数 → 根据机器人/扰动动力学构造 Hamiltonian → 向后积分 HJI 方程 → 读取零下水平集形成 BRT → 将当前状态投影到安全与危险区域 → 选择保证避险的控制。

其经典示例是两车/两飞行器相对运动的三维 Air3D 碰撞规避，与可解析参考解做数值验证。

### 理论与工程假设

系统需要明确控制有界、扰动有界、动力学准确、碰撞集合准确；数值网格近似仍有误差。形式化保证只对模型及其边界成立，不能自动覆盖传感器失联、执行延迟、未知摩擦与不服从协作规则的邻机。

计算瓶颈是状态维数爆炸，因此真实完整机器人通常不能直接为全部关节状态建立高维 HJI 网格，需要低维相对运动模型、分解或在线滤波控制接口。

### 为什么当年重要，今天仍在用什么

这项工作奠定了现代 Reachability-Based Safety Filter、动态博弈避碰、风险控制和部分 CBF 设计的理论参照。今天的在线 GPU HJ 论文没有改变安全定义，而是改变其在低维系统中的**计算可行性**。

较新的方法包括 GPU 并行求解、神经近似值函数、CBF 二次规划和学习安全过滤，但它们不自动具有与精确 HJI 值函数相同的保证。使用 CBF 时必须另行证明不变性；使用神经近似还需验证近似误差。

### 公开代码、数据与复现路径

原研究公开了数值实现思路与可复验的 Air3D 示例。今天可以使用 [hj_reachability](https://github.com/StanfordASL/hj_reachability) 作为后续社区开源参考；它不是 2005 年作者原始工程的等价复刻。

先建立两机器人二维交汇模型，再扩展到 Air3D，在同一终端集合、网格分辨率和动态边界下复核 BRT；比较 FP32、FP64 与数值解析参考的差异，最后才接入实时控制层。

### 对当前工程的重新解读

对于轮式机器人，**让 VLA/MPPI 提供效率，让低维可达性层提供独立的最坏情形防护**，比直接用概率预测成功率宣称“安全”更有解释力。它也说明，计算频率足够高之后，安全证书是否可信仍取决于真实传感器和动力学契约。

---

## 今日结论

今天技术最值得重视的不是单个榜单冠军，而是**从感知到动作的接口是否能够独立校验**。

CoReMatch 将视觉特征匹配精化从离散高分辨率网格迁移到连续坐标；在线 HJ 将低维最坏情形安全集合推进控制周期；G1 iLQR 联合优化步点与接触力；Caging VLN 将语言意图和有保证的几何执行分层；WayTrace 让地图语义成为逐帧可检查的路径 Trace。

同时，LoopQ 证明 4-bit 未必比 16-bit 快，RoboScope 证明很多评测时间耗在 CPU 仿真等待而不是模型推理，Agent Skill 生态研究显示大量提示文档也不能替代执行契约和回归。

**本期工程结论：先实测传感器、求解器、推理引擎、执行器的独立时延与失败边界，再决定使用学习式感知、MPC、形式化安全或 Agent 自动化中的哪一层解决问题。**

## 最值得深入研究或尝试复现的方向

1. **CoReMatch**：固定相同图像和 VO 后端，比较匹配内点、弱纹理鲁棒性、P95 和 ATE。
2. **在线 HJ 安全层**：从二维相对状态和 Air3D 起步，验证 GPU 时延、BRT 数值一致性和模型外扰动。
3. **G1 iLQR-MPC**：在相同 MuJoCo 扰动下测落脚点、接触力、WBC 500 Hz 与规划 P99。
4. **Caging VLN**：将高层语言意图、SDF 地图、Bézier-MPPI、dEBF 过滤解耦，保留急停和执行器约束。
5. **WayTrace**：先用公开视频离线比较 Map Waypoint、语言原子动作和 Trace 的人行道/楼梯几何偏差。
6. **LoopQ**：在真实目标 GPU 上 Profile Action Expert/视觉主干，验证 INT8/INT4 Kernel 是否实际改善闭环 P95。
7. **RoboScope Kit**：统一 500 回合和随机种子，优化 CPU Worker/GPU Replica 比率，独立核对成功率与终止步。
8. **Agent Skills**：从项目最常用的 10 个 Skill 开始消除重复文本，增加仅需一两条的执行与回滚验收。
9. **Coding Agent 实操**：在隔离环境对照 Copilot 配置损坏保护和 Gemini ACP/Podman 会话恢复。

## 参考资料

**原始批次：** [arXiv Robotics（2026-11-04）](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering（2026-11-04）](https://arxiv.org/list/cs.SE/new)。

**视觉、SLAM 与控制：** [CoReMatch](https://arxiv.org/abs/2611.03932) · [Online HJ Reachability](https://arxiv.org/abs/2611.04096) · [Online iLQR-MPC](https://arxiv.org/abs/2611.04204) · [Caging Legged-VLN](https://arxiv.org/abs/2611.04972) · [WayTrace](https://arxiv.org/abs/2611.05129) · [WayTrace 项目](https://way-trace.github.io/)。

**端侧模型与评测：** [LoopQ](https://arxiv.org/abs/2611.05093) · [RoboScope Kit](https://arxiv.org/abs/2611.03850) · [RoboScope Kit 源码](https://github.com/MINT-SJTU/RoboScope-Kit)。

**AI Coding：** [How Agent Skills Evolve](https://arxiv.org/abs/2611.04456) · [Copilot CLI v1.0.106-7](https://github.com/github/copilot-cli/releases/tag/v1.0.106-7) · [Gemini CLI Nightly](https://github.com/google-gemini/gemini-cli/releases/tag/v0.67.0-nightly.20261104.g89e9d25d6)。

**经典论文：** [Mitchell 等，IEEE TAC 2005](https://doi.org/10.1109/TAC.2005.851439) · [伯克利机构记录](https://its.berkeley.edu/publications/time-dependent-hamilton-jacobi-formulation-reachable-sets-continuous-dynamic-games) · [后续开源 HJ 工具](https://github.com/StanfordASL/hj_reachability)。
