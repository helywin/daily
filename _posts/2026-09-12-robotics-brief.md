---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-12"
date: 2026-09-12 09:00:00 +0800
description: "9 月 11 日最新公开批次聚焦 RIDE 定位几何复用、ActSafeGuard 硬约束 VLA、接触感知空中 MPC、CAP 人形感知退化鲁棒控制、约束流形规划、IMLE-VLA 单步动作头，以及 Ecdysis 与 ChurnBench 的 Agent 工程启示。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-12

## 摘要

今天是周六，arXiv 没有新的周末常规批次。最新公开批次仍是 2026-09-11：Robotics 共 44 条，Software Engineering 共 38 条。严格按最近 24 小时计算，可核验且未覆盖的高质量主动态不足 5 条，因此按任务规范扩展到最近 7 天，但本期仍优先选择 9 月 11 日最新公开批次中的工作。除一篇约束流形规划论文 v1 提交于 9 月 9 日 UTC 外，其余主动态均于 9 月 10 日 UTC 提交，均标记为“时间回补”。（[Robotics recent](https://arxiv.org/list/cs.RO/recent)，[Software Engineering recent](https://arxiv.org/list/cs.SE/recent)）

今天 SLAM / 定位侧最值得看的工作是 **RIDE**。它把传统 relocalization 流程里本来只用于 PnP 求姿态的 2D-3D inlier correspondence 再利用起来，为单目 RGB 提供稀疏的 metric depth 锚点，再用预训练 video-depth prior 补成稠密深度。这个思路很适合已经拥有 3DGS 地图和视觉重定位的机器人：同一套地图不只给 pose，还可以给 metric perception 提供尺度和局部几何约束。（[论文](https://arxiv.org/abs/2609.11079)）

控制侧有两项工作很值得关注。**ActSafeGuard** 针对 flow-matching VLA/WAM 的动作安全问题，不再只在推理结束后做 projection，而是把解析的 ray-scaling 可行域算子放进训练路径，让 hard action feasibility 与策略学习对齐；在 π0.5 与 Fast-WAM 等 backbone 上报告 100% step safety，同时保持或提高任务成功率。（[论文](https://arxiv.org/abs/2609.11697)）**Contact-Aware Incremental MPC** 则把 NMPC 的末端位置/法向力跟踪与 whole-body INDI 结合，在欠驱动四旋翼 + 单关节刚性机械臂上实现真实接触书写，不依赖专用腕部 F/T 传感器，并覆盖倾斜表面、不同摩擦和风扰动。（[论文](https://arxiv.org/abs/2609.11661)）

人形控制方面，**CAP** 处理比“有视觉 / 没视觉”二选一更真实的问题：深度传感器往往只是部分退化。它用感知 world-model encoder 把被遮挡、带噪或出现室外 artifact 的深度恢复成更干净的潜变量，同时用 proprioceptive variational encoder 提供不依赖深度的身体状态；再通过 depth-noise curriculum 与 latent dropout 让同一策略覆盖从正常感知到近乎失明的连续退化区间。Unitree G1 上已经做了室内外和真实传感器退化实验。（[论文](https://arxiv.org/abs/2609.11553)）

运动规划方面，**Planning along Differentiable Charts of Constraint Manifolds** 解决一个长期工程痛点：大量工业 IK 是 IKFast 这类自动 meta-solver 生成的解析函数，但不是为可微优化设计的。作者利用 inverse function theorem，从普通 forward-kinematics Jacobian 恢复解析 IK 参数化的梯度，并增加可微的 reachability 描述，使梯度在工作空间边界外仍然存在，最终可直接接入轨迹优化；真实 RB-Y1 上完成搬箱演示。（[论文](https://arxiv.org/abs/2609.10905)）

VLA runtime 方面，**IMLE-VLA** 很可能比“继续优化 10 步 flow-matching kernel”更值得工程团队尝试。它直接把 π0.5 的迭代动作头替换为 conditional IMLE 单步生成器，在保留多模态动作覆盖的同时消除多步采样。项目页报告 NVIDIA L40S 上推理频率从 15 Hz 提升到 55 Hz，LIBERO 40 任务平均成功率 98.0%；真实 Franka Panda 四任务中，动作 jerk 降低 2.2–3.0 倍，VLA 推理墙钟时间降低 3.9–6.6 倍。（[论文](https://arxiv.org/abs/2609.10915)，[项目页](https://kianhk6.github.io/IMLE-VLA/)）

AI Coding 侧，本期两项工作都把“Agent 基础设施状态”提升为正式工程对象。**Ecdysis** 认为 harness evolution 最危险的失败是把某个模型偶发犯错误判成 harness 系统性缺陷，然后不断为单例过拟合。它改用跨任务 failure aggregation 与多角色诊断，只对重复出现的 harness-level failure pattern 做修改，报告 harness 训练最高 1.84 倍加速，并将最终 harness 的 reasoning accuracy 提高 18.56%。（[论文](https://arxiv.org/abs/2609.11677)）

**ChurnBench** 则把企业 Agent 的“上下文过期”从静态 RAG 问题变成时间轴问题：所有底层数据变化进入 append-only ground-truth ledger，评测时可以区分 reasoning error 与 freshness error。它最有意思的结论是“cache age 本身不是关键变量，refresh schedule / TTL 才是”：28 天窗口里，开启 tiered refresh 时 freshness error 为 4，关闭后升到 45。（[论文](https://arxiv.org/abs/2609.11515)，[代码与数据](https://github.com/vsingh45/churnbench)）

## 1. RIDE：让重定位的几何对应同时服务稠密深度

**时间回补：v1 提交于 2026-09-10 04:36 UTC。**

### 为什么重要

视觉重定位常见流程是：从 query image 与地图建立 2D-3D correspondence，经 PnP-RANSAC 恢复相机位姿。成功以后，这些 inlier correspondence 往往就被丢掉了。

RIDE 的核心观察是：这些 correspondence 本身已经提供了**稀疏、带 metric scale 的深度锚点**。如果机器人已经拥有经过尺度标定的 3D Gaussian Splatting 地图，那么一次成功 relocalization 同时给了：

```text
Query RGB
   +
3DGS Map
   ↓
Render / Match
   ↓
PnP-RANSAC Inliers
   ↓
Sparse Metric Depth
   +
Pretrained Video-Depth Prior
   ↓
Dense Metric Depth
```

作者进一步加入 global / local depth correction 与 temporal memory，使短时间 correspondence 缺失时仍能维持尺度和时间一致性。（[论文](https://arxiv.org/abs/2609.11079)）

### 算法模块

系统可理解成三层：

1. **定位层**：3DGS render-match-PnP，得到 pose 与可信 2D-3D inlier；
2. **尺度校正层**：从 inlier 提取稀疏 metric depth，对 pretrained video-depth 的尺度/局部结构进行修正；
3. **时间记忆层**：在观测分布不均、短时无法获得稀疏锚点时延续最近可靠的 metric correction。

这里最重要的工程点不是“又一个 monocular depth 网络”，而是把 localization geometry 变成可复用的 perception signal。

### 传感器与地图假设

RIDE 依赖**metrically scaled 3DGS** 和足够可靠的 relocalization correspondence。如果 3DGS 本身尺度错误、地图发生大变化，或 PnP inlier 被重复纹理误导，那么错误尺度会直接传给 depth。

它因此更适合已有稳定地图与回定位模块的机器人，而不是完全 map-free 的单目系统。

### 实时性、鲁棒性与可复现性

论文在公共 RGB-D 视频上训练，并在机器人序列上零微调测试，报告相较仅做 scale calibration 的方法具有更好的深度精度与 temporal consistency。公开摘要没有给出可安全外推到 Jetson / ARM 的统一 FPS，因此实际部署应单独测 render-match、PnP 与 depth backbone 三部分的 P95 latency。

目前 arXiv 页面未给出稳定官方代码入口，可复现性暂评中等。

### 工程风险

最危险的错误链是：

```text
错误重定位 correspondence
        ↓
错误 metric depth anchor
        ↓
整帧 dense depth 被拉到错误尺度
```

因此 depth head 不应只接受一个“PnP 成功/失败”布尔值，最好同时输入或记录 `inlier_count / reprojection_error / spatial_coverage / pose_covariance`，并在 geometry support 太弱时主动回退到纯视觉 relative depth。

### 适合谁关注

视觉 SLAM、3DGS 地图、机器人重定位、单目深度、低成本视觉机器人。

### 工程落地启发

已有 3DGS / SfM / visual map 的系统可以先不训练新网络，只做一个简单实验：把 PnP inlier 转成 sparse metric-depth supervision，比较它对当前 monocular depth scale drift 的改善。若收益明显，再考虑 temporal memory 与学习式融合。

## 2. ActSafeGuard：把硬动作约束放进 Flow-Matching 的训练路径

**时间回补：v1 提交于 2026-09-10 15:21 UTC。**

### 为什么重要

VLA 与 World-Action Model 常用 diffusion / flow matching 生成连续动作。问题是概率模型天然回答“什么动作像训练数据”，却不天然回答：

```text
关节速度是否超限？
动作是否越过可行域？
某一维 command 是否违反硬约束？
```

传统做法通常是在 inference 后投影/裁剪。但这样训练时模型学的是 unconstrained action distribution，部署时执行的是经过外部修正的 distribution，存在明显 train-execution mismatch。

ActSafeGuard 的目标就是让约束不再只是末端补丁。（[论文](https://arxiv.org/abs/2609.11697)）

### 算法模块

核心是解析的 **ray-scaling operator**：沿当前动作方向把样本缩放到可行边界内，同时保持该算子可微。

```text
Flow-Matching Action
        ↓
Analytical Ray Scaling
        ↓
Feasible Action
        ↓
Boundary-Aware Gradient
        ↓
反向影响 Policy Learning
```

因此模型会逐渐学到 constrained manifold 本身，而不是每次都先走出边界再被修回来。

### 约束与动力学假设

论文强调 hard action feasibility，但这里的“hard”是相对于**已经写进 safeguard 的动作约束集合**。如果真实安全条件依赖碰撞几何、接触动力学、热限制或时序约束，而这些没有被编码，100% step safety 并不等价于整机 100% 安全。

### 实时性、鲁棒性与结果

在 π0.5 和 Fast-WAM 等 backbone、多个任务上，作者报告 **100% step safety rate**，且任务成功率完全保持或有所提高。方法只增加薄的解析约束层，理论上比每步再跑一个重优化器更容易插入高频 VLA runtime。

当前未见稳定官方代码仓库，复现性暂评中等。

### 工程风险

约束层越可靠，团队越容易产生“上层模型现在安全了”的错觉。真实系统仍应保留 collision monitor、joint/torque limit、watchdog 与 emergency stop。

更合理的分层是：

```text
VLA / WAM
   ↓
Training-Aligned Action Feasibility
   ↓
Geometric / Dynamic Safety Gate
   ↓
Controller / Hardware Protection
```

### 适合谁关注

Flow-matching VLA、机器人基础模型、动作安全层、需要将大模型接入真实机械臂的团队。

### 工程落地启发

先统计现有 VLA 的“最终动作被 clip / projection 的比例”。如果比例长期不低，说明训练分布与部署可行域已经脱节，值得把约束逐步前移到训练目标中。

## 3. Contact-Aware Incremental MPC：欠驱动四旋翼也能做真实接触力跟踪

**时间回补：v1 提交于 2026-09-10 15:03 UTC。**

### 为什么重要

空中机械臂做写字、擦拭、检测时，难点不是飞到墙边，而是同时满足：

- 末端沿表面精确运动；
- 法向接触力稳定；
- 机体仍保持可控；
- 摩擦和风扰动不把整个系统推离轨迹。

完全驱动飞行器或复杂多关节机械臂能降低问题难度，但成本、重量和控制复杂度都更高。这项工作证明标准欠驱动 quadrotor + 简单 1-DoF 刚性臂也能完成这类任务。（[论文](https://arxiv.org/abs/2609.11661)）

### 算法模块

作者将两种控制器职责拆开：

```text
NMPC
→ 末端位置 + 法向力跟踪
→ 小 penetration reference 下优化接触

Whole-body INDI
→ 快速抑制模型误差、摩擦与气动扰动
```

这是一种很实用的“预测优化 + 增量鲁棒控制”组合：MPC 负责未来和约束，INDI 负责把模型没解释好的高频扰动吃掉。

### 传感器与动力学假设

论文特别指出不需要 dedicated force/torque sensor。接触力跟踪因此依赖模型、状态和控制残差推断出的接触信息。

优点是硬件简单；风险是摩擦、气动、结构柔性和真实接触力会在 residual 中耦合，不能把估计量当成实验室六维力传感器的等价物。

### 实时性、鲁棒性与真机结果

真实实验覆盖垂直与倾斜表面、多个 reference force、不同摩擦条件和风扰动，并实现同时五自由度末端 pose + contact-force tracking。公开摘要没有给出统一控制频率，因此不人为补数字。

### 工程风险

接触任务最重要的 fallback 不是“继续优化”，而是**失稳时能主动脱离表面**。上线建议至少增加：contact-force envelope、max penetration、attitude margin、solver timeout、wind/disturbance monitor 与 contact-abort trajectory。

### 适合谁关注

空中操作、无人机擦洗/喷涂/检测、接触式巡检、NMPC + INDI 控制栈。

### 工程落地启发

对已有 PX4 / 自研飞控系统，可以先把外部接触看成一种有界 residual disturbance，做 INDI / disturbance-observer 层，再把真正的 contact-force objective 慢慢引入 NMPC；不要一开始就让单一 NMPC 同时承担全部鲁棒性责任。

## 4. CAP：人形感知不是“开/关”，而是一条连续退化曲线

**时间回补：v1 提交于 2026-09-10 13:45 UTC；CoRL 2026 接收。**

### 为什么重要

复杂地形行走需要 depth / heightmap 做前瞻感知，但真实传感器最常见的故障不是完全黑屏，而是：

```text
部分遮挡
边缘破碎
室外红外失效
局部噪声变大
若干帧间歇性错误
```

传统 perceptive policy 默认输入一直可信；“视觉策略 + blind policy 路由器”又把世界粗暴分成两种状态。CAP 认为部分可用的信息不应该因为质量下降就全部丢弃。（[论文](https://arxiv.org/abs/2609.11553)）

### 算法模块

```text
Corrupted Depth
      ↓
Perceptive World-Model Encoder
      ↓
Learned Denoising / Clean-depth Latent
      ↓
                 ┐
Proprioception → Co-active Variational Encoder
                 ┘
      ↓
Single Locomotion Policy
```

训练时配合两个 curriculum：对 depth input 逐渐增加噪声；对 policy-facing world-model feature 做 dropout，让策略从“视觉完全可靠”一路见到“几乎只能靠 proprioception”的状态。

### 传感器与动力学假设

CAP 不是无视觉策略，它仍希望能利用残留的 exteroceptive signal。若深度出现系统性错误且模型无法识别，例如稳定但错误的镜面/透明物体深度，denoiser 可能把错误信息修得更加“自信”。

### 鲁棒性与真机结果

仿真中，在 depth 仍有信息时 CAP 达到或超过纯 perceptive baseline；随着感知恶化，其性能比 binary-switching baseline 更平滑。Unitree G1 上覆盖间歇遮挡、真实 sensor corruption 与室外深度 artifact。（[论文](https://arxiv.org/abs/2609.11553)）

### 工程风险

感知 denoiser 本身不应拥有最终几何解释权。对于台阶边缘、悬崖、玻璃等安全关键区域，还需要 conservative obstacle / drop monitor。

建议 runtime 记录：

```text
raw_depth_quality
reconstruction_residual
feature_dropout_proxy
proprioception_only_score
policy_confidence
```

这样才能知道某次摔倒到底来自控制失败还是感知恢复错误。

### 适合谁关注

Unitree G1 / H1、人形复杂地形、四足 perception-aware locomotion、室内外深度传感器切换。

### 工程落地启发

现有感知行走策略可以先做最简单的训练增强：随机遮挡、旧帧、深度局部 dropout、量化噪声与整帧缺失，并绘制 success rate 对“输入质量”的连续曲线。比只测试 clean / blind 两个点更接近真实产品。

## 5. Differentiable Constraint Charts：不用重写 IKFast，也能把解析 IK 放进轨迹优化

**时间回补：v1 提交于 2026-09-09 23:22 UTC。**

### 为什么重要

机械臂在端着杯子、保持工具法向、沿表面移动时，满足的是 equality constraint：可行 configuration 只占整个 C-space 中一个 measure-zero manifold。

一种高效办法是直接用解析 IK 将这个 manifold 参数化，但工业机器人常用的解析 IK 来自 IKFast / meta-solver 自动生成，很难手工改成 differentiable code。

这篇工作利用 **inverse function theorem**，从普通 forward kinematic Jacobian 恢复解析 IK parameterization 所需要的梯度，从而让现成 IK solver 也能成为 gradient-based trajectory optimization 的可微 chart。（[论文](https://arxiv.org/abs/2609.10905)）

### 关键数学思想

如果约束可以局部写成 `F(q, y)=0`，其中 `y` 是自由参数，满足适当非奇异条件时：

```text
dq/dy = - (∂F/∂q)^(-1) (∂F/∂y)
```

工程上不需要对 IKFast 生成的每一行分支代码做自动微分，而是利用 robot forward kinematics 已经可计算的 Jacobian，在当前解附近恢复局部 chart derivative。

作者还增加 least-squares domain extension 与 optimization-friendly reachability constraint，使目标暂时落在工作空间外时仍保留可用梯度，而不是优化器直接进入“无解、无梯度”。

### 传感器与动力学假设

这是 kinematic equality-constrained planning，核心约束来自机器人几何与 IK；它不自动处理 torque、接触动力学、执行器延迟等更高层物理限制。

### 实时性、可复现性与真机结果

论文给出数值实验，并在 RB-Y1 上完成拿起箱子并放到桌面的硬件演示。方法最大工程优势是能够复用现有 general-purpose analytic IK，而不是为每一种机器人手写新的 differentiable solver。

### 工程风险

inverse-function 局部 chart 在 singularity 附近会变差。真正系统需要显式监控 Jacobian conditioning，并准备 chart switching、regularization 或回退到数值 IK。

### 适合谁关注

机械臂轨迹优化、受约束操作、MoveIt/Tesseract、工业 IKFast 用户。

### 工程落地启发

如果现有轨迹优化器因为“解析 IK 不可微”而只能反复调用数值 IK，可以先做一个 Jacobian-based local derivative wrapper，不改 IKFast 代码本身，就能快速验证 chart-based optimization 是否值得投入。

## 6. IMLE-VLA：把十步动作采样缩成一步，机器人不再“等模型想完再动”

**时间回补：v1 提交于 2026-09-10 00:00 UTC；IROS 2026 接收。**

### 为什么重要

π0.5 一类 VLA 的 action expert 常通过多步 flow matching 生成连续 action chunk。其多模态性很好，但一个实际副作用是：动作头需要串行执行多次，机器人呈现明显的 `观测 → 等待 → 执行 → 再等待`。

IMLE-VLA 选择不继续优化这条十步链，而是直接换掉生成范式。（[论文](https://arxiv.org/abs/2609.10915)，[项目页](https://kianhk6.github.io/IMLE-VLA/)）

### 算法模块

```text
Frozen / Pretrained VLM Backbone
          ↓
Conditional IMLE Action Head
          ↓
Single Forward Pass
          ↓
Multimodal Action Chunk
```

普通 L1/L2 regression 容易把多种合理动作平均成一个“中间动作”；conditional IMLE 则通过样本匹配目标保留多模态 coverage，又避免 iterative denoising。

### 实时性与结果

项目页给出的核心数据：

- π0.5：15 Hz；IMLE-VLA：55 Hz，约 **3.67×**；
- LIBERO 40 任务平均成功率：**98.0%**；
- 真实 Franka Panda 四任务：jerk 降低 **2.2–3.0×**；
- 每个真实任务的 VLA 推理墙钟时间降低 **3.9–6.6×**；
- 动态 moving-plate 任务中，更高频重规划能显著减少 stale observation 导致的追踪失败。

这些频率来自 NVIDIA L40S / A6000 级硬件，不应直接外推到 Jetson，但“去掉串行 10-step head”的算法收益是硬件无关的。（[项目页](https://kianhk6.github.io/IMLE-VLA/)）

### 鲁棒性与风险

单步生成最大的风险是 mode coverage 不足；作者用 cIMLE 专门针对这一点。LIBERO-Plus 中，它在背景、初始状态、语言和布局扰动下基本保持 π0.5 的鲁棒性。

但更高动作频率也意味着系统更快地消耗新观测和下发命令，必须同时保证相机 timestamp、动作队列和机器人控制接口不会成为新的瓶颈。

### 适合谁关注

VLA runtime、Jetson/边缘部署、需要动态反应的机械臂、π0/π0.5 系策略。

### 工程落地启发

在做 TensorRT/Triton kernel 优化前，先问一个更基础的问题：**迭代采样本身是否是必要的？** 如果单步多模态生成器能保留策略质量，算法级减少串行步骤通常比底层 kernel 再抠 20% 更值。

## 7. Ecdysis：Harness 不应该为每一个 Agent 偶发错误打补丁

**时间回补：v1 提交于 2026-09-10 15:09 UTC。**

### 突破性工程价值

Agent harness 现在越来越复杂：context 管理、工具协议、memory、retry、validator、sub-agent orchestration 都会影响最终能力。让 Agent 自己修改 harness 很自然，但失败原因有两类：

```text
Model-Specific Failure
→ 某次模型自己推理错了

Harness-Systematic Failure
→ 多个任务重复暴露同一基础设施缺陷
```

如果看到一次失败就修改 harness，系统很容易为某个模型、某个任务过拟合，最后 unseen task 反而更差。

Ecdysis 的核心就是先做 failure diagnosis，再决定 harness 是否值得改。（[论文](https://arxiv.org/abs/2609.11677)）

### 方法

```text
Batch of Agent Runs
        ↓
Cross-Instance Failure Aggregation
        ↓
Recurring Failure Pattern
        ↓
Multi-Role Failure Diagnosis
        ↓
Harness-Level Modification Spec
        ↓
Refine Harness
```

只有跨任务重复出现的模式才更可能是真正 harness deficiency。作者把这一流程称为 Failure-Driven Collaborative Refinement。

### 结果

论文报告相对已有 harness evolution 方法：

- harness training 最高 **1.84× speedup**；
- 生成 harness 的 reasoning accuracy 提高 **18.56%**。

这说明“少改一点、但只改系统性问题”可能同时降低成本和提高泛化。

### 是否适合真实研发流程

非常适合内部 Coding Agent 平台。真正生产化时，每次 harness change 都应该绑定：

```text
failure_cluster_id
affected_tasks
model_versions
change_spec
heldout_regression
rollback_target
```

这样才能区分“修基础设施”与“针对某模型打补丁”。

### 权限、安全与可验证性风险

Harness 本身定义工具权限与 verifier，因此不能让同一个 Agent 同时拥有：发现失败、修改 harness、选择回归集、批准上线四种权力。

建议把自动演化限制在 sandbox branch，必须经过固定 held-out regression 与独立 acceptance gate。

### 工程落地启发

先把你现有 Agent 失败日志做聚类。只有连续多个 repo、多个任务重复出现的失败模式，才进入 harness backlog；单次失败优先归因于 task/model，而不是立即改框架。

## 8. ChurnBench：Agent 的“知识新鲜度”由 Refresh Schedule 决定，而不是文件有多旧

**时间回补：v1 提交于 2026-09-10 13:19 UTC。**

### 突破性工程价值

企业 Agent 读取的信息来自多个系统：SQL、NoSQL、SaaS API、文档、缓存和长期 memory。传统 RAG benchmark 把数据冻结成 snapshot，只能评“找没找到正确 passage”，却无法回答：

> Agent 找到的东西在回答这一刻还是真的吗？

ChurnBench 把 benchmark 从 snapshot 改成 timeline。所有 mutation 写入 append-only ledger，因此可以在**检索时间**和**评测时间**分别恢复 ground truth，明确区分 freshness error 与 reasoning error。（[论文](https://arxiv.org/abs/2609.11515)，[代码](https://github.com/vsingh45/churnbench)）

### 核心结果

作者比较 1、14、28 天 cache age，开启 tiered refresh 时 freshness error 分别为 **7、4、4**，没有随着 cache 年龄单调恶化。

真正改变结果的是 refresh scheduler：在 28 天窗口里关闭 tiered refresh 后，freshness error 从 **4 增加到 45**。这说明评测 Agent memory / cache 时，应该扫的是：

```text
Entity Drift Rate
×
TTL
×
Refresh Schedule
```

而不是只问“缓存 28 天是不是比 1 天更旧”。

### 是否适合真实研发流程

非常适合共享 Coding Agent / 知识库。比如：

- API 文档变化慢，可长 TTL；
- 当前 branch / PR 状态变化快，应短 TTL 或 event-driven refresh；
- dependency lockfile 一旦 commit 变化应立即 invalidation；
- 人员权限、部署状态、服务健康度应接近实时。

一个统一的“记忆 7 天刷新一次”通常没有工程意义。

### 权限、安全与可验证性风险

过期权限和过期业务数据的风险不同。对 authorization、secret scope、production state 等安全关键上下文，应优先使用 source-of-truth 实时读取，不能仅靠 Agent memory TTL。

### 工程落地启发

为 Agent context 增加正式元数据：

```text
source
retrieved_at
valid_until
refresh_policy
entity_version
invalidation_event
```

长期 Agent 的 context 不应该只有“内容”，还应该知道**什么时候必须重新确认**。

## 经典论文回顾

### Task Space Regions / CBiRRT：为什么受约束操作不能只把终点写成一个 6D Pose

Dmitry Berenson、Siddhartha Srinivasa、James Kuffner 等人在 2009 年 ICRA 提出 **Manipulation Planning on Constraint Manifolds / CBiRRT**，随后在 2011 年 IJRR 的 **Task Space Regions: A Framework for Pose-Constrained Manipulation Planning** 中系统化 TSR 表示与 CBiRRT2。它是现代受约束机械臂规划非常重要的一条技术源头。（[ICRA 2009](https://publications.ri.cmu.edu/manipulation-planning-on-constraint-manifolds)，[IJRR 2011](https://doi.org/10.1177/0278364910396389)）

### 核心问题

普通 RRT 在完整 configuration space 里采样，但很多真实操作只能活在低维 constraint manifold 上：

```text
端着杯子 → 杯口必须近似竖直
开门 → 末端必须沿门把手圆弧运动
擦桌子 → 工具法向受约束
双臂搬物 → 两只手与刚体形成闭链
```

这些可行状态在完整 C-space 中是 measure-zero。随机采样几乎不可能自然落在上面。

### TSR 表示

Task Space Region 不把目标定义为一个离散 pose，而是定义为一个允许的 pose 区域：

```text
T_world^TSR
+
T_TSR^ee
+
6D bounds Bw
```

它可以表达“这个轴可以自由转”“这个方向可以滑动几厘米”“只要末端落在某一工作空间体积内都算成功”。多个 TSR 还能串联或相交，用来描述更复杂的 articulated-object 和 pose-uncertainty 任务。（[IJRR 2011](https://doi.org/10.1177/0278364910396389)）

### CBiRRT 的规划思想

CBiRRT 在双向 RRT 的基础上增加 constraint projection：

```text
Sample / Extend
      ↓
Project toward Constraint Manifold
      ↓
Reject if projection fails
      ↓
Grow constrained trees
      ↓
Bridge feasible regions
```

相比“先规划再修轨迹”，它从搜索阶段就尊重约束，并证明了相关 probabilistic completeness 性质。

### 传感器与动力学假设

经典 TSR/CBiRRT 主要处理 kinematic pose constraints。动力学、接触力、执行器带宽、感知误差并不是它的强项。

因此今天更合理的组合是：

```text
TSR / Constraint Manifold
      ↓
Feasible Geometric Motion
      ↓
Trajectory Optimization / MPC
      ↓
Force / Dynamic Safety
```

### 当年为什么重要

它让“任务允许一组解，而不是一个精确终点”成为规划器的一等概念。抓杯子时不必提前决定唯一 wrist pose，开门时也不必把整条圆弧离散成大量硬 waypoint。

### 今天仍然在使用的思想

今天 MoveIt / Tesseract / Drake 里大量 pose constraint、goal region、manifold planning 都延续了同一原则：**先表达任务真正允许的自由度，再让规划器利用这些自由度。**

本期新的 differentiable-chart 工作其实是在回答一个现代版本的问题：既然 analytic IK 已经能把 constraint manifold 参数化，怎样不重写 IK solver 就获得可微 chart，让 gradient-based optimizer 也能高效沿 manifold 运动。

### 已被后续扩展的部分

现代方法增加了：

- projection-based constrained sampling；
- Atlas / tangent-space manifold planning；
- differentiable IK；
- trajectory optimization；
- contact / dynamics constraints；
- learned proposal 与 neural implicit constraints。

经典 CBiRRT 的采样效率和高维扩展性已不一定是最强，但 TSR 的“任务空间允许区域”思想仍非常有工程价值。

### 公开代码 / 可复现性

原始 OpenRAVE 时代实现生态已经老化，但算法定义和公开论文完整，社区仍有 CBiRRT 复现；现代系统更容易直接在 MoveIt/Drake/Tesseract 中重建同类约束规划实验。

### 对当前工程项目的重新解读

如果正在做机械臂或移动操作，不要把所有 skill API 都设计成：

```text
go_to_exact_pose(x, y, z, roll, pitch, yaw)
```

更通用的接口应该支持：

```text
GoalRegion {
  nominal_frame
  allowed_translation
  allowed_rotation
  task_constraints
}
```

这样 planner 可以主动利用任务冗余，避障和 IK 成功率都会明显更容易提高。

## 今日结论

今天最清晰的 SLAM / 感知信号是：**地图中的几何约束正在被重复利用，而不是只服务一次定位。** RIDE 让 PnP correspondence 从“求完 pose 就丢掉”变成 dense metric perception 的尺度锚点。这与过去几期 3DGS 导航、公共地图纠漂的方向一致：地图资产的价值正在从“保存环境”扩展为“持续给多个模块提供结构性约束”。

控制侧则出现两种互补思路。ActSafeGuard 将 action feasibility 前移到策略训练，让生成模型本身更贴近可行域；Contact-Aware MPC 则保留明确的 model-based optimizer 和 INDI 鲁棒层。在真实机器人上，更成熟的架构往往不是端到端或模型控制二选一，而是：

```text
Learned Proposal / Policy
        ↓
Feasibility Shaping
        ↓
Model-Based Control
        ↓
Independent Safety / Hardware Limits
```

CAP 又提醒我们，真实传感器状态通常不是 healthy / dead 二值，而是一条连续质量曲线。机器人控制策略如果只在 clean sensor 上训练，再用一个 blind fallback 补洞，中间的大量“部分可用”状态就会被浪费。以后 sensor quality 很可能会像速度、姿态一样成为策略显式或隐式的连续状态。

IMLE-VLA 的工程启发尤其直接：**如果系统慢是因为算法必须串行执行 10 次，继续优化 kernel 不一定是最优路线。** 单步多模态 action generator 证明，先改变计算图的算法结构，可能比底层系统优化带来更大收益。

AI Coding 侧，两篇工作共同说明长期 Agent 的基础设施必须时间化、版本化。Ecdysis 要求 harness 修改建立在跨任务重复证据上，而不是单次失败；ChurnBench 则要求 context / cache 显式维护 refresh policy。一个真正可运行几天的 Coding Agent，需要的不只是 1M context，还需要：

```text
Context Source
Freshness / TTL
Harness Version
Failure Cluster
Validation Receipt
Rollback Target
```

这些传统软件工程式的外部状态。

## 最值得深入研究或尝试复现的方向

1. **RIDE-lite：重定位 inlier 直接校准单目深度。** 不训练完整新系统，只把现有 visual relocalization 的 PnP inlier 转成 sparse metric-depth anchor，给现有 Depth Anything / video-depth 做 scale + local correction，重点测短时失去 inlier 时尺度能维持多久。

2. **VLA Constraint Violation Telemetry。** 在现有 π0/flow policy 后增加统一 action-feasibility logger，统计每维 command 被 clip / project 的比例、幅度和任务阶段；如果长期存在系统性越界，再把类似 ActSafeGuard 的约束前移到训练。

3. **感知质量连续退化回归。** 对人形/四足 depth 输入建立从 clean → 轻噪 → 遮挡 → stale frame → 大面积 dropout → 全盲的连续梯度，画成功率和摔倒率曲线，而不是只测试 vision on/off。

4. **Agent Context TTL 分层 + Harness Failure 聚类。** 将 repo revision、dependency docs、PR state、CI result、组织知识分别配置不同 refresh policy；同时对 Agent failure 做跨任务聚类，只有重复出现的 failure cluster 才允许进入 harness 自动修改流程。

## 参考资料

- [arXiv Robotics recent](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering recent](https://arxiv.org/list/cs.SE/recent)
- [RIDE](https://arxiv.org/abs/2609.11079)
- [ActSafeGuard](https://arxiv.org/abs/2609.11697)
- [Contact-Aware Incremental MPC](https://arxiv.org/abs/2609.11661)
- [CAP](https://arxiv.org/abs/2609.11553)
- [Planning along Differentiable Charts of Constraint Manifolds](https://arxiv.org/abs/2609.10905)
- [IMLE-VLA](https://arxiv.org/abs/2609.10915)
- [IMLE-VLA 项目页](https://kianhk6.github.io/IMLE-VLA/)
- [Ecdysis](https://arxiv.org/abs/2609.11677)
- [ChurnBench](https://arxiv.org/abs/2609.11515)
- [ChurnBench 代码与数据](https://github.com/vsingh45/churnbench)
- [Manipulation Planning on Constraint Manifolds](https://publications.ri.cmu.edu/manipulation-planning-on-constraint-manifolds)
- [Task Space Regions](https://doi.org/10.1177/0278364910396389)
