---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-07"
date: 2026-10-07 09:00:00 +0800
description: "本期聚焦地面约束 LIO、Floorplan 在线定位、自适应安全 CBF、Reachability+MPPI、持久扩散规划、人形数据飞轮、端侧多模态 Embedding 与 Coding Agent 仓库治理。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-07

## 摘要

截至 2026-10-07 早间，arXiv Robotics 最新常规公开批次为 2026-10-06，共 174 条；Software Engineering 同日为 58 条。今天先检查最近 24 小时，再向最近 7 天扩展，并与覆盖索引按规范化标题、arXiv ID、DOI、GitHub 仓库和项目主页联合去重。除 Google 10 月 6 日刚发布的 EmbeddingGemma 2 外，本期入选论文的 v1 均已超过 24 小时，因此统一标为“时间回补”。

SLAM 侧今天两项工作都在利用机器人原本已经拥有、却经常没有进入定位后端的先验。GR-LIO 将局部地面平面和 body-to-ground 高度直接纳入滤波状态，用地面点到平面约束和 planar-motion update 压制垂直漂移；FreeLoc 则不再把 floorplan 离线离散成庞大 pose database，而是在线查询二维平面图几何，用 diffusion refinement 将粗候选连续化，再送入 histogram filter 做时序融合。

安全控制侧，Neural Barriers 试图解决经典 CBF 对模型精度过度敏感的问题：Neural ODE 在线学习未知扰动，conformal prediction 给学习残差估计不确定性；不确定性高时保守，数据积累后再逐步释放控制性能。ReSQ-MPPI 则把 Hamilton-Jacobi reachability、MPPI 与 SQP 分工：低维 HJ value function 负责把采样推向更安全的区域，MPPI 负责非凸长视野搜索，最后由少量 SQP 在全阶模型上落实硬约束。

生成式规划方面，P3 不再每个控制周期把 diffusion population 全部丢掉重采，而把上一个周期仍然有价值的候选轨迹作为“持久粒子”带到下一次 replanning，部分 re-noise、重新加权和 resample。对存在窄通道、稀有安全路线的任务，这比每次从零重新发现路径更符合 receding-horizon 控制真正的时序结构。

人形数据方面，InterMimicGen 将人类-物体交互数据做 contact-preserving retargeting，训练一个 physics-based generalist tracker，再让每轮成功执行的机器人轨迹继续衍生新的物体位置、身体实现和 embodiment 变化，只保留仿真中真正能完成任务的变体，形成“示范 → 可执行机器人动作 → 新训练数据”的闭环飞轮。

模型动态方面，Google 10 月 6 日正式发布 EmbeddingGemma 2：740M 总参数，把文本、代码、图像、视频和音频映射到统一 768 维空间；模块化加载时 text-only 约 270M 参数，量化后 Pixel 11 Pro 上 full multimodal active RAM 可低至约 567 MB。它不是生成式大模型，但对本地代码检索、机器人多模态记忆和离线 RAG 更直接：MTEB Code 从上一代 68.76 提升到 78.68，并支持 768→512/256/128 维 Matryoshka 截断。

AI Coding 主动态 SWE-CC 则指出，Coding Agent “测试通过”仍远离“可以合并”。12 个开源仓库的贡献文档被转换成 823 条机器可检查政策，500 个 SWE-bench Verified 扩展任务中，即使补丁功能正确，现代 Agent 仍违反 43.1% 的适用仓库政策，而且接近一半违规发生在中间执行步骤，而不是最终 diff。这意味着 AGENTS.md / CONTRIBUTING.md / CI 规范不能只作为 Prompt 背景，应该逐步编译成运行时和提交时都能执行的检查。

最新公开列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

## 1. GR-LIO：把“地面”从分割结果提升为 LIO 的正式状态约束

**时间回补：v1 提交于 2026-10-04 21:18 UTC。**

### 为什么重要

地面移动机器人长期拥有一个很强的几何事实：机器人通常围绕局部地面运动，机体到地面的高度也不会毫无规律地跳变。但许多 LIO 只是把地面点和其他点一样送进 scan matching，最多在地图层把地面分出来，并没有把这种稳定结构正式写进 estimator。

GR-LIO 将 local ground plane 用机器人姿态和 body-to-ground（B-G）height 参数化，并让这套几何在状态估计过程中持续传播。这样地面既能帮助更快、更稳定地分割，也能反过来约束状态。

### 算法模块

    LiDAR + IMU
        ↓
    filter propagation
        ↓
    propagated local ground plane
        ├─ orientation
        └─ B-G height
        ↓
    efficient ground segmentation
        ↓
    ground point-to-plane update
        +
    planar-motion update
        ↓
    state estimate

B-G height 初始未知时，作者先做初始化，再在线持续标定。相比每帧重新独立拟合一张地面，传播式 local plane 能让 ground segmentation 和 estimator 共享同一个几何状态。

### 传感器与运动假设

方法面向 LiDAR + IMU 的 ground-based mobile robot。核心假设是机器人当前附近确实存在可描述的局部地面，而且机器人运动与地面之间具有稳定关系。

这对轮式车、AGV 很自然；对四足、楼梯、跳跃或跨台阶任务则需要更谨慎。机器狗在步态中机体高度会周期性变化，楼梯还会出现多层局部支撑面，不能把“平面运动约束”机械照搬。

### 实时性、鲁棒性与结果

论文在多个公开 benchmark 和自采真实数据上评估，并报告在定位精度和计算效率两方面持续优于代表性 LIO。当前摘要没有给出统一 Hz 或具体平台延迟，因此工程上更值得关注的是它减少了无效地面匹配、同时增加了显式垂直约束这一结构。

对于长平面、仓库、道路等环境，它尤其有机会缓解 z 方向慢漂和 ground points 占比过高导致的计算浪费。

### 可复现性与工程风险

当前 arXiv 页面没有给出成熟官方代码入口。复现时可以先不改整个 LIO，只做两件事：记录现有 estimator 的地面 point-to-plane residual；再增加独立 B-G height / local-plane state，观察 z drift、roll/pitch 和 CPU 时间变化。

产品化需要额外记录：

    B-G height
    ground-plane confidence
    ground inlier ratio
    planar-update residual
    terrain slope
    current locomotion mode

一旦进入楼梯、跨障或机体明显起伏状态，应该允许关闭或降权 planar constraint。

### 适合谁关注

FAST-LIO / LIO-SAM 改造、轮式机器人、AGV、户外地面平台，以及正在处理长走廊、平地 z 漂移或地面点过多问题的团队。

### 工程落地启发

对现有 LIO 最值得先做的不是复制整篇论文，而是把“地面是否可信”做成 estimator telemetry。如果 local ground 足够稳定，就将它升级为独立 measurement；如果不稳定，就只保留普通 LiDAR constraint，不要让一个强先验在错误地形上反过来拉坏状态。

[论文](https://arxiv.org/abs/2610.05546)

## 2. FreeLoc：Floorplan 不再离散成百万候选位姿，而是在线查询后连续细化

**时间回补：v1 提交于 2026-10-04 07:09 UTC；CoRL 2026。**

### 为什么重要

建筑 floorplan 很轻、很常见，但高精度 floorplan localization 往往先把平面图离散成密集的 pose grid，再为大量采样位姿建立离线视觉 / 几何数据库。分辨率越高，存储与预处理越重；换一张建筑图还要重新离线生成。

FreeLoc 把 floorplan 重新当作“可直接在线查询的几何地图”，避免把连续 SE(2) / pose space 预先穷举成数据库。

### 算法模块

    RGB observation
        ↓
    on-the-fly floorplan ray querying
        ↓
    coarse plausible pose anchors
        ↓
    diffusion-aided pose refinement
        ↓
    continuous pose hypotheses
        ↓
    online likelihood construction
        ↓
    histogram-filter temporal fusion

单帧阶段先从平面图几何中找粗 anchor，再用 diffusion refinement 连续化；时序阶段把 coarse candidates 与 refined hypotheses 共同转成 likelihood，因此不需要为 histogram filter 事先建密集数据库。

### 传感器与地图假设

核心输入是 RGB + floorplan。它不是 VIO 或 SLAM 的替代品，更像全局 floorplan localization / relocalization layer。

系统依赖实际建筑结构和 floorplan 足够一致。如果现场增加了临时隔断、封门、施工围挡或家具遮挡，在线查询虽然避免数据库陈旧，但地图先验本身仍可能错误。

### 实时性与鲁棒性

论文报告 real-time online inference，并在 single-frame 和 sequential localization 上达到 SOTA 级表现，同时通过真实室内机器人结果验证部署可行性。

它真正有价值的系统属性是：精度不再被预先离散 pose grid 的分辨率直接锁死，地图也不再携带巨大的 scene-specific descriptor database。

### 可复现性与工程风险

目前 arXiv 页面没有稳定公开代码入口。最小复现可以先实现 floorplan ray query + coarse pose likelihood，再用普通 local optimizer 替代 diffusion refinement，先测数据库方案与 online-query 方案的内存和换图成本。

产品化建议保留：

    floorplan_revision
    coarse-anchor entropy
    refined-pose spread
    temporal posterior entropy
    map-vs-observation consistency

当 floorplan 与现实长期冲突时，应降低全局 prior 权重，而不是强行把局部 VIO 拉回“设计图上的正确位置”。

### 适合谁关注

BIM / Revit 场景、室内巡检、施工机器人、已有 floorplan 但不想采完整 LiDAR 地图的团队，以及需要轻量全局重定位的视觉机器人。

### 工程落地启发

很适合与现有 VIO / LIO 分层：局部 estimator 高频连续运行，FreeLoc 类模块低频维护 floorplan posterior；只有 posterior 足够集中且连续多帧一致时，才把全局 correction 写入 pose graph。

[论文](https://arxiv.org/abs/2610.05011)

## 3. Neural Barriers：让 CBF 在线学习模型误差，同时把“学得有多不确定”也纳入安全边界

**时间回补：v1 提交于 2026-10-04 21:13 UTC。**

### 为什么重要

经典 Control Barrier Function 最大的工程痛点之一是：数学保证建立在动力学模型上，而真机的载荷、风、摩擦和执行器变化会持续破坏模型。

如果安全控制器一直按错误模型算 barrier derivative，“形式上有 CBF”并不意味着现实中仍安全；但如果一看到模型不确定就永久使用巨大 robust bound，又会让机器人极端保守。

Neural Barriers 将在线学习与不确定性校准都纳入 barrier controller。

### 算法模块

    nominal dynamics
        +
    streaming state/action observations
        ↓
    Neural ODE learns time-varying disturbance
        ↓
    conformal prediction
        ↓
    adaptation uncertainty bound
        ↓
    robust adaptive high-order CBF
        ↓
    safe control

数据少、预测不确定性高时，barrier 使用更保守的 margin；随着新数据到来、扰动模型变得可信，再逐步减小不必要的保守度。

### 动力学假设与理论边界

论文给出在适当 Lipschitz smoothness 假设下、带概率界的安全保证。这里必须强调：这不是“神经网络学到什么都能保证安全”。

保证仍依赖系统与轨迹满足论文假设、conformal uncertainty 对当前数据有效、barrier function 与相对阶建模正确。遇到传感器故障、模式切换或完全未建模动力学时，应该进入更硬的 fallback。

### 实时性、鲁棒性与工程风险

摘要重点是 certifiable online adaptation，没有给出一个可以直接外推到任意机器人平台的控制频率。工程上真正需要 profile 的是 Neural ODE update、conformal calibration 和高阶 CBF 求解是否都能在目标控制周期内完成。

建议在线记录：

    disturbance prediction
    conformal radius
    barrier margin
    CBF intervention
    model residual
    coverage violation
    fallback count

如果 conformal radius 持续扩大，系统应该理解为“正在失去模型信心”，而不是让控制器无限堆 margin。

### 可复现性

当前未发现成熟官方代码入口。最值得先做的是把已有 CBF 的 fixed disturbance bound 替换成 rolling calibrated residual bound，再比较固定 robust margin 与自适应 margin 的安全率、任务效率和 intervention frequency。

### 适合谁关注

无人机抗风、载荷变化机器人、安全 RL、CBF / HOCBF、希望保留形式化安全结构又需要适应真机模型漂移的团队。

### 工程落地启发

学习模块不应直接拥有“取消安全约束”的权力。它更适合提供一个经过校准的 uncertainty budget，再由 CBF 把这个 budget 转成安全裕量。这样学习错了，失败边界仍比端到端 neural safety policy 清晰。

[论文](https://arxiv.org/abs/2610.05542)

## 4. ReSQ-MPPI：用 Reachability 指路、MPPI 探索、SQP 最后把硬约束落实

**时间回补：v1 提交于 2026-10-03 09:51 UTC。**

### 为什么重要

MPPI 很适合非线性、非凸环境，但有限样本和 weighted-average update 可能输出违反硬约束的控制；全阶 nonlinear MPC 能写硬约束，却高度依赖 warm start 和局部收敛；Hamilton-Jacobi reachability 有强安全含义，但高维 value function 又算不起。

ReSQ-MPPI 没有要求其中一种方法解决全部问题，而是明确做 generation → refinement 分工。

### 算法模块

    reduced-order model
        ↓
    offline HJ reachability value
        ↓
    online safe-biased sampling
        ↓
    MPPI candidate / warm start
        ↓
    few SQP iterations
    on full-order constrained MPC
        ↓
    executable control

论文还有一个很有意思的观察：标准 MPPI inference step 可以理解成 unconstrained weighted least-squares。ReSQ-MPPI 将它替换为 constrained MPC refinement；当 MPPI 更新本身可行时尽量保留，只有冲突时才最小修改。

### 动力学假设

HJ 使用 reduced-order model，而最后 SQP 使用 full-order model。这里的关键工程问题是：低维安全 value 能否保留真正决定危险的状态。

如果降阶模型没有包含高速侧滑、执行器延迟或接触模式，那么 HJ 只能提供“对那个简化模型安全”的采样偏置。

### 实时性、鲁棒性与结果

论文在 cluttered navigation 与 autonomous racing simulation 中，相对单独 MPPI、MPC 和 reachability-filtered sampling baseline 改善了安全与性能。

当前没有真机结果，也没有摘要级统一控制频率，因此它更适合作为架构方向，而不是直接声明已经解决实机实时安全 MPC。

### 可复现性与工程风险

当前没有稳定代码入口。最容易做的 A/B 是保持现有 MPPI cost / dynamics 不变，只增加一个廉价 reachability / viability score 做 proposal bias，然后再给最终控制序列跑少量 constrained SQP。

建议记录：

    MPPI best cost
    HJ value
    pre-refine violation
    SQP correction norm
    SQP iteration count
    solve deadline miss

如果 SQP 每个周期都进行很大修正，说明上游采样并没有真正学会把候选放在可行区域。

### 适合谁关注

MPPI、无人机 / 赛车控制、安全 MPC、非凸路径规划，以及希望把形式化安全和 GPU sampling controller 结合的团队。

### 工程落地启发

把不同方法放在它们最擅长的计算尺度：离线安全集合负责大方向，在线 sampling 负责探索，全阶优化只负责最后几步硬约束。比让一个大优化器每帧从零解决全部问题更容易满足实时性。

[论文](https://arxiv.org/abs/2610.04406)

## 5. P3：Diffusion Planner 每个周期不再“失忆”，把稀有好路线作为持久粒子带到下一次规划

**时间回补：v1 提交于 2026-10-05 08:56 UTC；ICLR 2027 under review。**

### 为什么重要

Diffusion trajectory prior 能生成多模态候选，但 receding-horizon 控制中常见做法是每个周期重新采一批轨迹。结果是：上一周期好不容易找到的一条窄通道 / 稀有安全绕行路线，下一周期可能因为随机采样又消失，规划器反复换路。

P3 把跨时间的 trajectory population 当成 sequential Monte Carlo particle system，而不是一组一次性样本。

### 算法模块

    previous weighted plan population
        ↓
    shift with executed action
        ↓
    partial re-noising
        ↓
    denoise under newest observation
        ↓
    constraint-aware weighting
        ↓
    ESS-based resampling
        ↓
    next persistent population

它保留多个 continuation，而不是只保留上一周期唯一 best plan。

### 理论与工程意义

论文分析表明 re-noising depth 决定已有路线能保留多强；而对于稀有、彼此分离的路线，保留一条已经找到的粒子，需要的候选数远少于每周期从零重新发现它。

实验中 population reuse 减少 route switching、提高成功率且没有引入 constraint violation；由于只需要部分 re-noise，也减少了每次 replanning 的 denoising iterations。

### 可复现性

作者已经公开代码与 pretrained models，复现包甚至包含 Table 1 的完整 inference weights。官方 README 给出的基本命令是：

    python -m pip install -e '.[benchmarks]'
    python scripts/run_table1_p3.py --device cuda:0 --output table1_p3.json
    python -m pytest -q tests

仓库使用 Git LFS 保存 16 组推理权重，并支持 smoke test、断点 resume 和多机 seed shard。

### 动力学假设与工程风险

P3 仍依赖 diffusion prior 能覆盖有价值路线。如果训练 prior 完全不知道某类动作，particle persistence 只能记住已有候选，不能凭空创造能力。

另一个风险是“过度坚持旧路线”：环境突然变化时，re-noising 太浅可能让 population 被旧假设绑住。因此 persistent planner 必须监控 observation mismatch 和 effective sample size，必要时注入 fresh particles 或彻底 reset。

### 适合谁关注

Diffusion planning、机器人 receding-horizon control、存在窄通道 / 多模态绕行路线的导航，以及已经发现生成式 planner 经常左右摇摆或每帧换路线的团队。

### 工程落地启发

这套思想不局限 diffusion。MPPI / CEM 也可以问同样的问题：为什么每个周期都重新随机采样？把上一周期高质量 trajectory population shift 后复用，再少量注入新样本，通常更符合真实控制的时间连续性。

[论文](https://arxiv.org/abs/2610.06002) · [代码与预训练模型](https://github.com/p3-username/p3-anon)

## 6. InterMimicGen：把每一次可执行的人形动作继续变成下一轮训练数据

**时间回补：v1 提交于 2026-10-05 17:59 UTC。**

### 为什么重要

人类-物体交互 mocap / 视频很丰富，但直接迁移到 humanoid 会遇到 embodiment gap、手型不同、物体位置不同，以及“人能做到、机器人动力学做不到”的问题。

传统 imitation pipeline 往往是一次性：人类示范 → retarget → 训练 tracker。InterMimicGen 增加了一个真正的数据 flywheel：只有机器人在物理仿真里实际完成任务的变体，才有资格成为下一轮数据种子。

### 算法模块

    heterogeneous human-object interaction data
        ↓
    contact-preserving retargeting
        ↓
    humanoid reference library
        ↓
    physics-based generalist tracker
        ↓
    simulated execution
        ↓
    task-preserving local edits
       ├─ interaction location
       ├─ body realization
       └─ embodiment / object variation
        ↓
    keep successful executable variants
        ↓
    next augmentation round

随着轮次增加，小范围修改逐渐把原始稀疏示范周围扩成更大的可执行动作区域。

### 动力学与数据假设

核心质量门是 physics-based execution，但最终仍然受 simulator fidelity 影响。仿真里接触成功不等于真机抓持、摩擦和柔顺完全可靠。

另一个风险是 self-evolution 逐轮偏离原任务语义。作者用 task-preserving edit 和“执行必须完成任务”做过滤，但产品系统最好额外保留语义 verifier 与 motion-quality gate。

### 结果与可复现性

论文展示跨对象、跨机器人配置的 contact-preserving retargeting；一个 generalist tracker 覆盖大规模 whole-body loco-manipulation；多轮 augmentation 后可执行动作覆盖持续扩大，并展示到真实机器人上的迁移。

项目页已公开 Unitree G1 + Inspire hands、Dexmate Vega、Unitree G1 rubber hands、Booster K1 等多种部署演示，但当前公开重点是研究展示，并非一套即插即用训练仓库。

### 适合谁关注

Unitree G1、人形 loco-manipulation、MimicGen / InterMimic 路线、希望把少量人类示范扩成大规模物理可执行数据的团队。

### 工程落地启发

数据增强最好由“视觉看起来像”升级成“机器人真实或高保真物理执行过”。以后做人形数据工厂时，每条数据都可以带：

    source_demo_id
    retarget_version
    simulator_version
    task_success
    contact_quality
    real_robot_validation

数据集不是静态文件夹，而是一条能追溯每个动作为什么被接受的生产线。

[论文](https://arxiv.org/abs/2610.06850) · [项目页](https://sirui-xu.github.io/InterMimicGen/)

## 7. EmbeddingGemma 2：740M 多模态 Embedding，把本地代码检索和机器人记忆压进约 567 MB RAM

**最新发布：Google 于 2026-10-06 正式发布。**

### 突破性工程价值

EmbeddingGemma 2 不是新的聊天模型，而是专门做 representation / retrieval 的开放多模态 embedding model。它将文本、代码、图像、视频和音频映射到同一 768 维空间。

这类模型对机器人和 Coding Agent 的价值往往比“再加一个小生成模型”更直接：本地代码语义搜索、设备端多模态历史检索、视觉-语音跨模态查找都可以在不把原始数据上传云端的情况下完成。

### 模型结构与端侧规模

Google 公布的总规模为 740M 参数：

- text 模块约 270M；
- vision encoder 约 170M；
- audio encoder 约 300M；
- 不需要的 modality encoder 可以不加载。

模型支持 8K context；完整 768 维 embedding 还可以通过 Matryoshka Representation Learning 截断为 512、256 或 128 维。Google 表示这最多可以带来约 6× 的向量存储缩减。

在量化配置下，Google Pixel 11 Pro 上 text-only active RAM 可低至约 191 MB，full multimodal 约 567 MB。

### 代码检索表现

官方模型卡给出的 MTEB Code 结果从 EmbeddingGemma 1 的 68.76 提升到 **78.68**，提高 9.92 分。官方还专门给出 CodeRetrieval task prefix：

    task: code retrieval | query: {query}

而 corpus code 可以使用：

    title: {filename} | text: {code}

这使它非常适合在本地为 Codex / Claude Code / 自研 Agent 构建一个不依赖云 embedding API 的 repo index。

### 机器人侧怎么用

机器人上最适合的不是让它直接输出动作，而是作为多模态 memory / retrieval sidecar。例如把巡检历史的图像、声音、短视频、故障文本统一嵌入，任务 Agent 可以用一句自然语言查“上一次这个阀门附近出现高频噪声时的画面和记录”。

对于 ARM / Android / 本地服务器，同一模型在 text-only 与 full multimodal 之间可按需要加载，内存预算更容易管理。

### 风险与边界

Embedding 相似并不等于几何或因果正确。机器人 safety-critical 查询不能因为“向量最近”就直接触发动作；代码检索也不能把高相似文件当作真正 dependency graph。

此外，Google 的 benchmark 是官方报告，选型仍需在自己的中文代码库、ROS / C++ 项目和多模态数据上 A/B。

### 可复现性

模型权重已经开放，可通过 Hugging Face、Kaggle、LiteRT、Transformers、sentence-transformers、MLX、vLLM、llama.cpp、Ollama 等使用。

最简单的 text/code 测试可以从：

    pip install -U sentence-transformers transformers

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("google/embeddinggemma-2")

开始，再固定自己的 repo query set 比较 Recall@K、索引体积和端侧 latency。

### 适合谁关注

本地 Coding Agent、离线代码语义搜索、Android / ARM 边缘 RAG、机器人长期多模态记忆，以及希望降低 embedding API 依赖和数据外发的团队。

### 工程落地启发

Embedding model 最适合做“可替换的检索层”。把 chunking、metadata、vector dimension、index version 明确版本化，不要让 Agent memory 永久绑定某一个 embedding 模型；以后升级时才能重建索引并做固定 recall regression。

[Google 官方发布](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/) · [官方模型权重](https://huggingface.co/google/embeddinggemma-2) · [Developer Guide](https://developers.googleblog.com/en/embeddinggemma-2-the-developer-guide/)

## 8. SWE-CC：代码功能正确，也可能完全不符合仓库“可合并”的贡献规则

**时间回补：v1 提交于 2026-10-05 12:08 UTC。**

### 突破性工程价值

现有 Coding Agent benchmark 主要看 unit tests 能不能过，但成熟仓库的真实合并要求还包括格式、目录规则、生成文件、测试命令、Git 约束、文档更新和 workflow 规范。

SWE-CC 将 12 个开源仓库贡献文档中的规则半自动转成 **823 条 machine-checkable atomic policies**，并同时审计 Agent 的中间执行行为与最终提交物。

### 实验结果

作者在 500 个从 SWE-bench Verified 扩展出的 end-to-end contribution task 上评估 4 个 LLM × 2 种 agent scaffold。

最值得记住的数据是：即使补丁已经 functionally correct，Agent 仍违反 **43.1%** 的适用 project policies；而接近一半违规发生在 intermediate execution steps。

这意味着只审最终 diff 不够。例如 Agent 可能在过程中运行了仓库明确禁止的脚本、修改了不该碰的生成文件、跳过指定测试入口，最后又把表面结果整理得很干净。

### Benchmark 的设计价值

SWE-CC 的关键不是再加一个语言 judge，而是把政策转换成 lightweight deterministic checker。

理想的仓库治理接口应该更像：

    policy_id
    scope
    deterministic_check
    runtime_or_final
    violation_evidence
    remediation

而不是把 CONTRIBUTING.md 全部塞进 Prompt，希望模型永远记得。

### 是否适合真实研发流程

非常适合大仓库、开源项目和企业 monorepo。最现实的落地不是完整复制 benchmark，而是先挑本仓库最容易被 Agent 违反的 10–30 条规则做机器检查，比如：

- 不允许直接编辑 generated files；
- 必须通过指定 wrapper 跑测试；
- 修改某模块时必须同步文档 / schema；
- 禁止某类 Git 操作；
- 某目录只能由特定 build step 生成。

这些检查可以同时挂在 pre-tool hook、pre-commit 和 CI，而不是只存在于 AGENTS.md。

### 权限 / 安全 / 可验证性风险

如果 policy checker 只看最终 tree，仍会漏掉中间危险行为；如果只做 runtime blocking，又可能漏掉最终 artifact 不完整。

因此 Agent governance 应至少分成：

    execution policy
    artifact policy
    merge policy

并把违规事件写入长期可审计日志。

### 可复现性

作者已经公开 benchmark 和 source code。可以直接使用其 policy / checker 思路做内部仓库扩展。

### 适合谁关注

Codex、Claude Code、Copilot Coding Agent、自研 Agent harness、企业 monorepo、自动 PR 与合规研发流程。

### 工程落地启发

未来的 AGENTS.md 最好不是“长篇自然语言说明书”，而是一个 human-readable index，真正可判定的规则链接到 checker。Agent 看规则，人也看规则，但最终由可执行检查决定是否满足，而不是由 Agent 自己解释“我已经遵守”。

[论文](https://arxiv.org/abs/2610.06193) · [代码与 Benchmark](https://github.com/dangtruong01/swe-cc-arxiv)

## AI Coding 实战技巧精选

### 技巧 1｜Claude Code v2.1.292 给不同子 Agent 分配不同 effort，不要全员开同一推理档位

- **来源**：Anthropic，2026-10-06，[Claude Code v2.1.292](https://github.com/anthropics/claude-code/releases/tag/v2.1.292)。
- **一句话结论**：v2.1.292 给 Agent tool 新增 effort 参数。把“仓库搜索 / 文件分类”这类机械子任务设为较低 effort，把“架构判断 / 安全审查 / 根因分析”留给较高 effort，可以把预算从平均分配改成按任务难度分配。
- **具体怎么做**：
  1. 先升级到 v2.1.292 或更高版本，并确认团队环境版本一致。
  2. 在会触发 sub-agent 的 Skill / workflow 中，明确要求 Claude 调 Agent tool 时为不同角色设置对应 effort；不要让所有子 Agent 无条件继承主 Agent 的最高推理预算。
  3. 固定一组真实任务，对比 success、wall-clock、token / usage、tool-call 次数和人工修正量，再确定团队默认分档。
  4. 对安全 review、release gate 这类高风险任务保持独立验证，不能因为 effort 更高就跳过测试。
- **适合什么场景**：Claude Code 多 Agent、大仓库探索、并行 review、长任务成本控制。
- **注意**：effort 是计算预算，不是权限边界。低 effort Agent 和高 effort Agent 应使用同样的 filesystem / network / write policy。

### 技巧 2｜Agent 做大型重构时改用 GitHub Stacked PR，把一大坨 Diff 拆成可独立验证的层

- **来源**：GitHub，2026-10-06，[Stacked pull requests generally available](https://github.blog/changelog/2026-10-06-stacked-pull-requests-generally-available/)；[官方 gh-stack](https://github.com/github/gh-stack)。
- **一句话结论**：不要让 Coding Agent 一次生成一个上千行 PR。GitHub Stacked PR 已 GA，gh stack 也支持 Git worktree；可以让不同 Agent / 子任务各自负责一层依赖明确的小 PR。
- **具体怎么做**：
  1. 安装官方扩展：gh extension install github/gh-stack。
  2. 在主干上运行 gh stack init BRANCH-NAME，完成第一层并提交；下一逻辑单元用 gh stack add NEXT-BRANCH 叠在上一层。
  3. 每层只放一个可独立 build / test / review 的行为变化；Agent 并行开发时使用独立 worktree，避免互相污染 working tree。
  4. 用 gh stack submit 创建 / 更新整组 PR；底层修改后统一 rebase stack，再让每层 CI 和 reviewer 独立验收。
- **适合什么场景**：Codex / Claude Code 大型重构、API 迁移、跨模块功能、多 Agent 并发开发。
- **注意**：stack 解决 review granularity，不解决逻辑耦合。每一层仍应有明确 regression；跨 fork stack 当前不支持。

## 经典论文回顾

### Control Barrier Function Based Quadratic Programs：把“安全”从 penalty 变成实时优化里的硬不等式

Aaron D. Ames、Xiangru Xu、Jessy W. Grizzle 与 Paulo Tabuada 的 **Control Barrier Function Based Quadratic Programs for Safety Critical Systems** 完整期刊版本发表于 **IEEE Transactions on Automatic Control 2017**（论文 2016 年先行公开）。它是现代 CBF-QP 安全控制路线最基础的工作之一，也正好解释今天 Neural Barriers 与大量 VLA / MPC safety shield 为什么会采用“nominal controller + barrier projection”的结构。

### 核心问题

机器人控制经常同时存在两类目标：

    performance
    → 跟踪、速度、稳定、效率

    safety
    → 绝不能进入危险集合

如果把安全只写成 cost penalty，优化器在任务收益足够大时仍可能选择“少量违规”。经典 CBF 的关键变化是：安全不再只是偏好，而是要求 safe set 在闭环下保持 forward invariant。

### 关键数学思想

定义安全集合：

    C = { x | h(x) >= 0 }

对相对阶为 1 的系统，典型 CBF 条件可以写成：

    Lf h(x) + Lg h(x) u + alpha(h(x)) >= 0

只要控制输入持续满足这个不等式，就可以在相应条件下保证状态不离开安全集合。

论文进一步把 CBF 与 Control Lyapunov Function（CLF）放进同一个 Quadratic Program：

    minimize
        nominal-control deviation
        + CLF slack penalty

    subject to
        CBF safety constraint
        CLF performance constraint
        actuator bounds

安全约束通常保持硬约束，performance 则可以通过 slack 在冲突时退让。

### 传感器 / 动力学假设

CBF 本身不规定 LiDAR、相机还是 IMU；它假设你能构造与安全集合相关的状态 h(x)，并且系统动力学足够准确，可以计算 Lie derivatives。

这也是经典方法到真实机器人时最容易出问题的地方：障碍位置错、速度估计延迟、动力学偏差或 actuator saturation 都会让“数学上的 barrier margin”和“现实安全距离”不再一致。

### 当年为什么重要

这项工作把 safety 与 performance 的冲突转成一个可以高频实时求解的 QP，而不是预先设计复杂状态机。

对于 adaptive cruise control 和 lane keeping 这类任务，控制器不必放弃原有 nominal objective，只需要在动作即将违反 safety set 时做最小修改。

这套接口后来非常适合与 RL、MPC、VLA 和 learned policy 组合：学习策略负责“想怎么做”，CBF 负责“这一步最多允许做到哪里”。

### 今天仍在使用的思想

今天最常见的 runtime shield 仍然延续三个原则：

1. nominal policy 与 safety layer 解耦；
2. 安全写成可验证 constraint，而不是一个模糊 reward；
3. safety filter 尽量做最小动作修正，避免永久破坏 nominal behavior。

今天的 Neural Barriers 是这条路线非常自然的现代扩展：经典 CBF 假设模型足够准，新工作则给 model disturbance 增加 Neural ODE online adaptation，再用 conformal uncertainty 决定 robust margin。

### 已被后续扩展的部分

经典 CBF-QP 对 relative degree、model mismatch 和 uncertainty 的处理较理想化。后续已经出现：

- High-Order CBF：处理约束对控制输入不是一阶显式出现的系统；
- Robust / Adaptive CBF：处理有界或可估计模型误差；
- Stochastic / chance-constrained CBF：处理概率不确定性；
- learning-enhanced CBF：学习未知动力学、barrier 或 residual；
- feasibility-aware / backup-set 方法：解决多个 CBF 与输入约束冲突导致 QP infeasible。

所以今天不能把“加一个 CBF-QP”理解成自动获得绝对安全，它仍依赖 sensing、model、solver deadline 和 fallback architecture。

### 公开资料与可复现性

原论文有开放 arXiv 版本和 Caltech 归档页面。最小复现不需要大型仿真器：一个 double-integrator 或 unicycle，加一个 circular obstacle，就能实现 nominal controller + QP projection，再观察 barrier margin 与 action correction。

更值得做的工程实验是故意加入：

    model bias
    sensor delay
    moving obstacle error
    actuator saturation

然后测经典固定 CBF 从什么时候开始失效，再与 robust / adaptive margin 比较。

### 对当前工程项目的重新解读

对机器狗、无人机或 VLA 操作，CBF-QP 最值得保留的是**接口边界**：

    planner / RL / VLA
        ↓
    nominal action
        ↓
    independent safety state
        ↓
    CBF / constrained projection
        ↓
    applied action

学习模型不需要自己证明安全，安全层也不需要理解全部任务语义。两边只通过明确动作与安全状态交互。

但如果底层厂商机器人只开放 vx / vy / wz，这反而更容易：CBF 可以直接在速度命令层做投影，不必接管腿控。对无人机则可在 body-rate / thrust 或 velocity reference 层加入 barrier，保留 PX4 内环。

[arXiv](https://arxiv.org/abs/1609.06408) · [IEEE DOI](https://doi.org/10.1109/TAC.2016.2638961) · [CaltechAUTHORS](https://authors.library.caltech.edu/records/jnhr0-1ww05)

## 今日结论

今天最清楚的一条主线，是机器人系统正在把过去“隐含在算法里”的先验与风险，重新变成显式、可估计、可持续更新的状态。

GR-LIO 让地面几何真正进入 estimator，而不是只作为点云分类标签；FreeLoc 让 floorplan 直接成为在线可查询地图，而不是先膨胀成离线数据库。它们共同说明：已有结构先验如果足够稳定，应该以 measurement / prior 的形式正式进入系统，而不是让神经网络重新猜一遍。

Neural Barriers 与 ReSQ-MPPI 则从安全控制的两端给出类似答案。安全保证不应该只停留在 nominal model；真实系统必须知道模型误差有多大。与此同时，形式化 reachability 也不需要承担所有在线计算，可以作为低维 guide，把昂贵全阶 constrained optimization 留给最后几步。

P3 的持久粒子又把这种“状态连续性”带进生成式规划。机器人下一帧和这一帧高度相关，规划器却每帧完全失忆，本身就是一种计算浪费。未来 diffusion / flow / sampling planner 很可能越来越像 Bayesian filter：不仅输出 trajectory，还维护跨周期的候选分布。

InterMimicGen 则把数据集从静态资源变成生产系统。人类示范只是起点，真正有价值的是机器人执行过、物理可行、能继续衍生的数据。对于人形规模化训练，数据 provenance、simulator revision、执行成功证据会越来越像传统软件的测试与构建日志。

EmbeddingGemma 2 对边缘机器人和 Coding Agent 的意义也很明确：并不是所有智能都要靠生成模型完成。一个 740M、可模块化加载、可压缩向量维度的本地 embedding model，可以承担代码检索、多模态记忆和离线 RAG，将高价值上下文先筛出来，再交给更昂贵模型推理。

SWE-CC 和今天两个实战技巧最终把相同原则落到软件工程：Agent 不能只“完成功能”，还必须遵守仓库运行规则；复杂改动也不应全部塞进一个巨大 PR，而要拆成可单独验证的层。模型越强，越需要把 policy、evidence、review unit 和权限边界写成系统结构。

如果把今天整期压成一句话：

> **可靠机器人和可靠 Coding Agent 的共同方向，是把先验、不确定性、候选轨迹、数据来源和工程政策都变成显式状态，让每一步都能被验证、更新和拒绝，而不是让一个更大的模型隐式承担全部责任。**

## 最值得深入研究或尝试复现的方向

1. **LIO Ground Constraint Sidecar**：先在现有 FAST-LIO / LIO-SAM 上记录 local ground plane、B-G height 与 z drift，不改主算法；确认相关性后再把 point-to-plane / planar update 写进 estimator。
2. **Floorplan Global Posterior**：保留现有 VIO/LIO，只增加低频 floorplan ray-query posterior；先测施工现场图纸变化对 false localization 的影响。
3. **Adaptive CBF Margin**：将现有固定 robust bound 改成 rolling residual + conformal calibration，重点记录 coverage failure 和 intervention frequency。
4. **MPPI + Final SQP A/B**：固定 MPPI 采样器，只对最终序列做 1–3 次 constrained SQP，测安全提升、correction norm 和 deadline miss。
5. **Persistent Sampling Population**：MPPI/CEM/diffusion 都尝试复用上一周期 elite population，统计 route switching、sample 数和 GPU time。
6. **Humanoid Data Provenance**：每条 retarget / augmented motion 都保存 source demo、接触约束、simulator version、执行成功证据与真机验证状态。
7. **本地 EmbeddingGemma 2 代码索引**：在 C++ / ROS2 / Android 三类仓库各建固定 query set，比较 768/256 维的 Recall@K、索引体积和 ARM / GPU latency。
8. **把 CONTRIBUTING 规则编译成 Checker**：先从 20 条最容易被 Agent 违反的规则开始，同时挂到 runtime hook、pre-commit 和 CI，比较自然语言提示与 deterministic enforcement 的差异。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [GR-LIO](https://arxiv.org/abs/2610.05546)
- [FreeLoc](https://arxiv.org/abs/2610.05011)
- [Neural Barriers](https://arxiv.org/abs/2610.05542)
- [ReSQ-MPPI](https://arxiv.org/abs/2610.04406)
- [P3](https://arxiv.org/abs/2610.06002)
- [P3 代码与权重](https://github.com/p3-username/p3-anon)
- [InterMimicGen](https://arxiv.org/abs/2610.06850)
- [InterMimicGen 项目页](https://sirui-xu.github.io/InterMimicGen/)
- [EmbeddingGemma 2 官方发布](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/)
- [EmbeddingGemma 2 模型](https://huggingface.co/google/embeddinggemma-2)
- [SWE-CC](https://arxiv.org/abs/2610.06193)
- [SWE-CC 代码与 Benchmark](https://github.com/dangtruong01/swe-cc-arxiv)
- [Claude Code v2.1.292](https://github.com/anthropics/claude-code/releases/tag/v2.1.292)
- [GitHub Stacked Pull Requests GA](https://github.blog/changelog/2026-10-06-stacked-pull-requests-generally-available/)
- [gh-stack](https://github.com/github/gh-stack)
- [Control Barrier Function Based Quadratic Programs](https://arxiv.org/abs/1609.06408)
- [CBF-QP DOI](https://doi.org/10.1109/TAC.2016.2638961)
