---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-16"
date: 2026-09-16 09:00:00 +0800
description: "9 月 16 日刷新版聚焦 LiDAR 退化检测、语义回环、纳米无人机 ToF-IMU 里程计、在线几何变化检测、混合系统 HJ 安全、多接触腿式稳定控制、多模态世界动作模型与动态仓库上下文。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-16

## 摘要

今天早间归档时，arXiv Robotics / Software Engineering 最新公开列表仍停留在 9 月 15 日，因此首版使用了最新可见的 9 月 14 日提交工作。随后 **2026-09-16** 新公开批次已经刷新：Robotics 当天共有 77 条，Software Engineering 当天共有 26 条。本版重新从最新批次检索并对 `robotics-brief-covered-items.md` 做强制查重，以下 8 条主动态均未在早间索引中出现。最新列表可直接查看 [arXiv Robotics](https://arxiv.org/list/cs.RO/recent) 与 [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

今天 SLAM / 定位侧最值得优先看的工作是 **LiLi**。它直接针对长走廊、隧道、平坦场地这类 LiDAR scan alignment 退化场景，并指出经典 Hessian / eigenvalue 方法的一个根本弱点：它通常在固定对应关系和当前线性化附近判断可观测性，却没有充分考虑点对应重新关联后是否仍存在一整族等价 SE(3) 解。LiLi 用 `se(3)` 生成元系统地构造扰动，重新优化并比较结果，从而识别完整的退化变换集合。论文在合成数据上相对 Hessian-based detector 将 alignment error 降低约 50%，并在 430 m 往返隧道轨迹上成功完成 LiDAR odometry，而参考退化检测方案失败。([论文](https://arxiv.org/abs/2609.17145))

视觉 SLAM 侧，**HuMemSLAM** 把“人类记忆式”的 bottom-up perceptual evidence 与 top-down contextual reasoning 用于视觉地点识别，再作为 ORB-SLAM3 的 place-recognition 前端。HuMem-VPR 在真实图像 benchmark 上获得最高 aggregate retrieval accuracy，同时延迟约为所比较 SOTA VPR 的 1/2–1/3；集成到 ORB-SLAM3 后，提高 Recall@1，并减少送入几何后端的无效候选。它的工程启发不是“用语义替代几何”，而是让高层上下文先减少候选，再由几何验证最终闭环。([论文](https://arxiv.org/abs/2609.17168))

无人机状态估计方面，**TIO-Former** 很有硬件味道：六个正交 8×8 ToF 阵列总载荷约 15 g，每帧只有 384 个距离值，再与 IMU 融合完成 mapless 6-DoF odometry。它使用 IMU-guided cross-attention 和 Streaming Causal Transformer，并将短期 KV 与压缩 Chunk-FIFO memory 分开，使推理成本和内存不随飞行时长无限增长。真实飞行中，相比 nano-UAV optical flow，open-loop position error 降低 54.4%；部署在 RISC-V companion computer 上 P95 延迟 **10.466 ms**、峰值驻留内存 **6.324 MiB**。([论文](https://arxiv.org/abs/2609.17198)，[官方仓库](https://github.com/Ly041021/TIO-Former))

长期地图侧，**Online Geometric Change Detection via Scene Decomposition（CDSD）** 不再每次把两个完整全局地图做昂贵差分，而是把环境分解成可唯一识别的 scene，并为每个 scene 维护 dense local submap；机器人在线重访时只对相关 submap 做视场差异鲁棒的几何比较，再把变化回写地图。对长期巡检而言，这比简单的“新 scan 覆盖旧 map”更合理，因为 fallen tree、开门、设备移动等变化应该成为带位置和证据的地图事件。([论文](https://arxiv.org/abs/2609.17302)，[代码](https://github.com/vectr-ucla/geometric_change_detection))

控制侧，**Hamilton-Jacobi Reachability for Hybrid Systems** 将经典 HJ reachability 从纯连续动力学扩展到“连续状态 + 离散模式”的 hybrid system。它不仅计算 hybrid safe set，还提出 hybrid least-restrictive safety filter，以及同时保证避险和到达目标的 hybrid backward reach-avoid tube；最终可以同时调整连续控制和离散 mode transition。论文包含四足机器人真机实验。这对接触丰富机器人很关键，因为“左脚支撑 / 双脚支撑 / 抓住扶手”等模式切换本身就是控制的一部分。([论文](https://arxiv.org/abs/2609.17430)，[IJRR DOI](https://doi.org/10.1177/02783649261477777))

另一篇腿式控制工作 **Optimized Wrench Polytope Analysis** 把 arbitrary multi-contact 下的 full actuatable wrench polytope 优化到可以进入常规控制环，论文报告能够以 **49 Hz** 计算关节力矩，并已部署到真实 walking robot。它特别适合斜坡、洞穴、脚手架和多点支撑：与只看 COM 是否落在支撑多边形里相比，wrench polytope 会把关节力矩能力、接触方向和真实可施加六维力矩都纳入“当前姿态到底稳不稳”。([论文](https://arxiv.org/abs/2609.17405))

机器人世界模型侧，**ModAR（Modality-Autoregressive World-Action Models）** 给出了一个很值得记住的负结果：WAM 不一定需要花大量算力去预测未来 RGB。作者让模型按 `point tracks → DINO features → depth → RGB → action` 顺序逐模态去噪，后一个模态显式条件于前一个。实验显示 tracks、DINO、depth 都稳定帮助动作，额外预测 future RGB 却没有一致收益；ModAR 从零训练，在相同数据上平均成功率 75%，略高于视频模型初始化的 Flex-π 的 72%，但训练 FLOPs 约少 20×、参数规模约小 200×。([论文](https://arxiv.org/abs/2609.17524)，[项目页](https://adamhung60.github.io/ModAR/))

AI Coding 侧，**RepoAtlas** 正好击中超长 session 的一个核心问题：代码 Agent 需要 repository graph，但一次性把整张图喂进去太密；只生成一次局部视图又会随着 Agent 探索而过期。RepoAtlas 使用 `select → project → refresh`：根据 issue 与当前探索状态，在固定预算里选相关 graph region，同时投影成文本与视觉表示，并在上下文陈旧时刷新。SWE-bench Verified 上，相对论文中最强 multimodal graph baseline，resolve rate 提高 2.4 个百分点，同时 input token 和 model call 分别平均减少 5.8% 与 7.8%。([论文](https://arxiv.org/abs/2609.16936))

近期通用旗舰模型方面，本轮重新核验 OpenAI、Google DeepMind 与 Anthropic 的官方入口，没有发现 9 月 16 日需要作为新旗舰模型报道的正式发布；9 月 15 日的 Gemini 3.8 Audio 已在昨天简报覆盖，因此今天不重复。

## 1. LiLi：退化不只是 Hessian 小特征值，而是一整族“重新关联后仍然等价”的 SE(3) 运动

**最新公开批次；v1 提交于 2026-09-15 13:10 UTC。**

### 为什么重要

长直走廊、隧道、平坦田野对 LiDAR scan matching 的本质问题不是“点太少”，而是某些方向上的运动无法由当前几何唯一确定。例如长隧道中沿隧道轴平移，很多点仍然可以找到几乎同样好的对应。

经典工程实现常做：

```text
ICP / Scan-to-map optimization
        ↓
Gauss-Newton Hessian
        ↓
eigenvalue / condition number
        ↓
Degenerate? yes / no
```

但这种判断通常围绕当前对应关系和局部二次近似。如果把位姿沿某方向稍微推开，重新建立 correspondences 后仍然能得到同样好的最优解，真正的退化空间可能比当前 Hessian 显示得更复杂。

### 算法模块

LiLi 利用刚体群 `SE(3)` 和李代数 `se(3)`：

```text
optimized scan alignment T*
        ↓
沿 se(3) generators 施加系统扰动
        ↓
重新执行 alignment / association
        ↓
比较 re-optimized pose
        ↓
哪些方向存在等价最优解？
        ↓
构造 degenerate transformation set
```

这样得到的不只是一个“退化分数”，而是对完整退化变换方向的描述。

### 结果与工程边界

论文在合成退化数据上，相比 Hessian-based 方法将 alignment error 降低约 **50%**，噪声越大改善越明显。

真实退化数据中，集成 LiDAR odometry 后，在 260 m 轨迹上优于参考方案；430 m 往返隧道中，参考退化检测方案失败，而 LiLi 成功完成定位。

论文当前没有给出适合直接外推到现有 LIO 前端的统一每帧额外耗时，因此工程复现必须重点测“为检测退化增加的重复优化次数”是否能够放进 10–20 Hz LiDAR pipeline。

### 传感器假设与风险

LiLi 解决的是 scan alignment 的几何退化，不会凭空产生缺失观测。

如果隧道轴向真的不可观，正确行为仍应是：

```text
LiDAR：承认该方向弱约束
IMU / Wheel / RTK / Reflector：补该方向
```

而不是让 LiDAR 自己“算出”不存在的信息。

另一个风险是，动态物体或错误关联也可能制造多个局部最优；实际系统需要把“几何不可观”和“数据关联错误”区分开。

### 适合谁关注

低线数 LiDAR、LIO-SAM、FAST-LIO2、隧道 / 长走廊 / 矿井定位，以及正在做方向级退化融合的团队。

### 工程落地启发

不要只输出一个 `is_degenerate`。

更适合后端的接口是：

```text
Localizability {
  observable_se3_directions
  degenerate_se3_directions
  confidence
  support_geometry
}
```

因子图 / ESKF 再按方向改变 LiDAR 信息矩阵，并让轮速、IMU、RTK 或反光标志在真正需要的方向上承担更多权重。

[论文](https://arxiv.org/abs/2609.17145)

## 2. HuMemSLAM：Place Recognition 应该先用上下文理解减少候选，再让几何后端做最终裁决

**最新公开批次；v1 提交于 2026-09-15 13:32 UTC。**

### 为什么重要

视觉 SLAM 的回环 / 重定位一直同时受两类问题影响：

```text
Perceptual aliasing
→ 不同地点看起来太像

Perceptual variation
→ 同一地点因为光照、视角、季节看起来太不同
```

ORB-SLAM3 这类几何系统的最终验证很强，但如果前端 retrieval 给出大量错误候选，几何后端会浪费计算；如果 retrieval 根本没召回真实地点，几何后端也无能为力。

HuMemSLAM 将 semantic / contextual VPR 用作候选生成器，而不是直接取代几何验证。

### 算法模块

HuMem-VPR 借鉴“bottom-up 感知 + top-down 上下文”的双向关系：

```text
visual observation
      ↓
bottom-up perceptual evidence
      ↕
top-down contextual reasoning
      ↓
high-level place representation
      ↓
VPR candidates
      ↓
ORB-SLAM3 geometric backend
      ↓
loop / relocalization decision
```

这样 semantic reasoning 负责“像哪个地方”，几何 backend 仍负责“是否真的是同一地点”。

### 结果与实时性

论文报告 HuMem-VPR 在真实图像 benchmark 上得到最高 aggregate retrieval accuracy，在 CARLA benchmark 上也具有竞争力，并且延迟约比所比较的 SOTA VPR 方法低 **2–3×**。

集成到 ORB-SLAM3 后，HuMemSLAM 提高 integrated Recall@1，同时减少送进 geometric backend 的 proposal 数量。

### 风险

语义上下文也可能产生新的 aliasing。例如两个楼层都有“白墙 + 消防栓 + 电梯”，高层语义可能比局部几何更像。

因此 semantic VPR 最适合承担：

```text
candidate ranking / pruning
```

而不是直接写 loop factor。

最终 loop 仍应通过 feature geometry、PnP / Sim3、局部地图一致性等独立证据验证。

### 适合谁关注

视觉 SLAM、ORB-SLAM3、跨光照 VPR、长期巡检、视觉回环检测。

### 工程落地启发

现有 ORB-SLAM3 不需要重构。可以先把 HuMem 一类 learned VPR 放成 sidecar：只改变候选排序，不改变后端验证逻辑，然后统计：

```text
Recall@K
false candidate rate
geometric verification calls / frame
loop latency
false loop count
```

如果候选明显减少、最终 false loop 不增加，才逐步提高语义前端权限。

[论文](https://arxiv.org/abs/2609.17168)

## 3. TIO-Former：六个 8×8 ToF + IMU，也可以做 6-DoF 纳米无人机里程计

**最新公开批次；v1 提交于 2026-09-15 13:54 UTC。**

### 为什么重要

nano-UAV 的 SWaP-C 约束非常极端：LiDAR / 双目可能太重，单目 optical flow 在低纹理表面又容易失效，纯 IMU 则快速漂移。

TIO-Former 使用六个正交方向的 8×8 multi-zone ToF，总共每帧只有 **384 个 range**，整个传感器载荷约 **15 g**，再和 IMU 联合估计 6-DoF ego-motion。

### 算法模块

```text
6 × orthogonal 8×8 ToF grids
          +
         IMU
          ↓
Bilateral Gated Difference
→ 相邻 range grid 的变化特征
          ↓
IMU-guided Cross Attention
→ 根据运动状态路由不同方向几何信息
          ↓
Streaming Causal Transformer
  ├─ Local uncompressed KV cache
  └─ compressed Chunk-FIFO memory
          ↓
6-DoF odometry
```

最重要的系统设计是 memory 不随飞行时长线性增长；长时历史被压缩进 Chunk-FIFO，而近期信息保留高精度 KV。

### 实时性与真机结果

真实飞行实验中：

```text
vs nano-UAV optical flow：open-loop position error -54.4%
vs learned inertial baselines：-66.4% ~ -89.1%
```

部署在 edge RISC-V companion computer 上：

```text
P95 latency       10.466 ms
Peak resident RAM 6.324 MiB
```

对于几十到上百 Hz 的小型无人机状态估计，这已经是真正具有端侧意义的数据。

### 传感器假设与风险

multi-zone ToF 在强阳光、低反射率、玻璃 / 镜面和超出量程时会产生 invalid return；六方向布置也意味着外参和机体遮挡非常关键。

Transformer 可以学习缺失模式，但它不能把持续没有 range 的方向变成可靠几何观测。

因此生产系统应持续记录每方向：

```text
valid_range_ratio
range_age
saturation / max-range ratio
innovation vs IMU
```

并在大面积失效时降低 ToF 约束权重。

### 可复现性

作者已经建立官方 GitHub 仓库，但目前明确写着 **code、pretrained models、dataset coming soon**，因此现在只能复现结构，暂时不能把它评价为“完整开源可复现”。

### 适合谁关注

nano-UAV、狭窄空间无人机、无纹理环境、小型 RISC-V / MCU companion computer、低成本 range-inertial odometry。

### 工程落地启发

这项工作的真正启发是：几何锚点不一定需要完整 3D LiDAR。

如果无人机的主要问题是狭窄走廊的漂移，可以先用前 / 后 / 左 / 右 / 上 / 下的低分辨率 range array 给 VIO / IMU estimator 增加方向级几何约束，未必需要马上上更重的雷达。

[论文](https://arxiv.org/abs/2609.17198) · [官方仓库](https://github.com/Ly041021/TIO-Former)

## 4. CDSD：长期地图需要知道“环境真的变了”，而不是把变化都当成 SLAM 噪声

**最新公开批次；v1 提交于 2026-09-15 15:10 UTC。**

### 为什么重要

长期巡检机器人经常看到：

```text
昨天门是关的，今天打开了
树倒在道路上
设备被移动
货架结构变化
```

如果地图系统只有“当前 scan 和旧 map 是否对齐”，这些真实变化很容易被 robust loss 当作 outlier 丢掉；另一极端是每次都重新构建完整地图，失去长期历史。

CDSD 的目标是把 **change** 本身变成地图一等对象。

### 算法模块

```text
global dense map / online mapping
          ↓
scene decomposition
→ 环境划分成具有唯一性的 scene
          ↓
dense representative submap per scene
          ↓
revisit scene
          ↓
submap-to-submap comparison
处理不同 FoV
          ↓
change detection / post-process
          ↓
real-time map reconstruction
```

它避免每次全局 map-vs-map 比较，只处理当前相关 local scene。

### 传感器与地图假设

论文支持 **LiDAR 或 RGB-D**。

它依赖 SLAM 本身能够产生足够紧密的局部地图对齐；如果两次 session 的 pose graph 仍存在明显系统偏差，CDSD 可能把 registration error 误认为环境变化。

另一个挑战是不同视角和 FoV：第一次只看到桌子正面，第二次看到侧面，并不代表桌子形状变化。论文将 differing field of view 明确作为核心问题之一处理。

### 实时性与可复现性

论文在美国 Army Research Laboratory Graces Quarters 自采数据，以及公开 multi-session change-detection 数据上验证。

作者团队已公开 `vectr-ucla/geometric_change_detection` 仓库，可用于进一步核验实现。

### 工程风险

变化不应该立即覆盖历史地图。

更稳的产品数据模型是：

```text
MapChangeEvent {
  scene_id
  geometry_delta
  evidence_submaps
  first_seen
  last_confirmed
  confidence
  status: candidate | confirmed | reverted
}
```

只有多次确认后才修改长期 static layer。

### 适合谁关注

长期巡检、多 session SLAM、园区机器人、矿井、仓储、变化检测与数字孪生维护。

### 工程落地启发

现有 LIO-SAM 不必修改前端。可以把每 10–30 m 或关键房间切成 submap，跨 session 对同一 submap 做变化检测，先只生成 change report，不立刻改导航地图。

这比拿整张几 GB 点云每晚做一次全局 diff 更容易扩展。

[论文](https://arxiv.org/abs/2609.17302) · [代码](https://github.com/vectr-ucla/geometric_change_detection)

## 5. Hybrid HJ Reachability：接触模式切换也应该进入安全证明，而不只是连续控制量

**最新公开批次；v1 提交于 2026-09-15 16:42 UTC；IJRR 2026。**

### 为什么重要

四足、人形、抓取和接触丰富机器人天然是 hybrid system：

```text
continuous state
→ q, dq, pose, force ...

+

discrete mode
→ left support / right support / double support / contact / no-contact
```

经典 HJ reachability 主要针对连续时间非线性系统。如果只在单一 mode 下证明安全，再把 mode transition 留给外部逻辑，很容易在切换瞬间破坏保证。

### 方法

作者将 HJ value function 扩展到：

```text
V(mode, continuous_state)
```

同时考虑 control constraint 和 model uncertainty，并提供数值计算方法。

在此基础上有两种运行方式：

```text
1. Hybrid Least-Restrictive Safety Filter
nominal hybrid controller
       ↓
只有将进入 unsafe set 时
同时干预 continuous action + discrete mode

2. Hybrid Backward Reach-Avoid Tube
同时寻找：
能避开危险 + 最终到达目标 的 hybrid policy
```

第二点特别重要，因为传统 safety filter 只保证“别出事”，不保证“最终还能完成任务”。

### 真机与适用性

论文包含 simulation 和四足机器人 real-world experiments，展示 hybrid mode planning 和 safety-critical control。

它对楼梯、跨障碍、接触切换很有概念价值：安全集合不应该只依赖当前连续状态，还应该知道机器人处在哪种 contact mode，以及哪些 mode transition 仍然可用。

### 工程风险

HJ reachability 最大问题仍是维数灾难。

真实全身机器人状态几十维，不可能直接在完整状态空间网格上求值函数。工程部署往往需要：

```text
降阶 safety model
局部 / 分层 safe set
offline precompute
online interpolation / filter
```

模型误差和未建模 contact 也必须被 uncertainty set 包住，否则 formal guarantee 不成立。

### 适合谁关注

四足 / 人形接触规划、safe locomotion、混合系统控制、CBF / reachability safety layer。

### 工程落地启发

对于楼梯机器狗，可以先把完整系统压成少量 mode：

```text
flat
ascending
turning-on-landing
descending
recovery
```

再给 mode transition 显式定义安全入口 / 出口集合，而不是只靠一个连续速度控制器承担所有异常切换。

[论文](https://arxiv.org/abs/2609.17430) · [IJRR DOI](https://doi.org/10.1177/02783649261477777)

## 6. Optimized Wrench Polytope：多接触腿式机器人“稳不稳”，应该看真实可施加 wrench，而不只是支撑多边形

**最新公开批次；v1 提交于 2026-09-15 16:35 UTC。**

### 为什么重要

静态 ZMP / support polygon 很直观，但面对复杂接触时会越来越不够：

```text
脚踩斜面
身体靠墙
多个接触法向不同
某些关节接近力矩极限
```

COM 落在支撑区域里，并不代表执行器真的能够产生保持该姿态所需的 6D force / torque。

Wrench polytope 直接描述在当前关节力矩和接触限制下，机器人真正可实现的合力 / 合力矩集合。

### 算法模块

```text
robot kinematics / dynamics
      +
contact configuration
      +
friction / contact constraints
      +
joint torque limits
          ↓
full actuatable wrench polytope
          ↓
stability / feasible wrench query
          ↓
required joint torques
          ↓
pose control
```

论文的关键贡献是把 full wrench-polytope analysis 加速到能进入常规控制回路，而不是只做离线分析。

### 实时性与真机

作者报告关节力矩计算可以达到 **49 Hz**，并在真实 walking robot hardware 上部署。

论文声称控制器在非常复杂的多接触场景中保持稳定，目标应用包括 slope、cave、scaffolding 等困难地形。

### 假设与风险

稳定性强依赖：

```text
friction coefficient
contact normal
contact point
joint torque limit
```

如果脚底实际打滑、地面软化或力矩热降额没有被模型捕获，wrench polytope 会过度乐观。

因此实时系统最好让 friction / actuator capability 本身带 uncertainty margin，而不是始终使用标称值。

### 适合谁关注

四足、人形、轮足机器人、多接触控制、楼梯 / 脚手架 / 斜坡稳定性。

### 工程落地启发

即使不实现完整 polytope controller，也值得把一个简化的 **wrench feasibility margin** 暴露给上层 planner：

```text
margin high
→ 正常走

margin falling
→ 降速 / 调姿态

margin near zero
→ 禁止继续进入该 contact configuration
```

这比只依赖 IMU 倾角超过阈值后再救机器人更主动。

[论文](https://arxiv.org/abs/2609.17405)

## 7. ModAR：世界模型不一定需要预测 RGB，先预测 motion / semantics / geometry 可能更有效

**最新公开批次；v1 提交于 2026-09-15 17:56 UTC。**

### 为什么重要

World-Action Model 常见思路是：

```text
当前 RGB + action
      ↓
预测 future RGB
      ↓
从未来画面帮助动作
```

但 RGB 包含大量与控制无关的信息：纹理、光照、背景细节。

ModAR 问了一个更基础的问题：**机器人真正需要预测的 future modality 到底是什么？**

### 模态自回归结构

作者不是一次性并行生成所有 future，而是按结构从紧凑到复杂依次生成：

```text
Point Tracks
→ motion
    ↓
DINO Features
→ semantics
    ↓
Depth
→ geometry
    ↓
RGB
→ appearance
    ↓
Action
```

每个后续模态都 condition on 已经生成的前序模态，最后动作可以显式依赖预测出的运动、语义和几何结构。

### 一个很有价值的负结果

消融显示：

- 预测 point tracks 有帮助；
- DINO feature 有帮助；
- depth 有帮助；
- **再预测 future RGB 没有稳定额外收益**。

这意味着 WAM 的训练算力不一定应该默认花在高保真 video generation 上。

### 结果与计算量

在相同 RoboTwin 数据条件下，ModAR 从零训练平均成功率 **75%**，视频模型初始化的 Flex-π 为 **72%**。

项目页给出的模型规模与训练量对比：

```text
ModAR       30.1M parameters
Flex-π      ~6B parameters

ModAR       1× training FLOPs
Flex-π      ~20×
```

也就是约 **200× 更小参数规模、20× 更少训练 FLOPs**，且不需要 video pretraining。

三项真实双臂任务中 ModAR 也优于基线，并能从 human videos 获益。

### 风险与边界

自回归模态存在 error propagation：track 预测错了，会污染后面的 DINO / depth / action。

项目页的消融也指出，需要在训练中给前序预测加入 context noise，才能让后续模块适应不完美预测。

另外官方项目页目前写明 **Code coming soon**，可复现性暂时不是完整状态。

### 适合谁关注

VLA / WAM、机器人 world model、低算力动作模型、human-video robot learning。

### 工程落地启发

如果正在做机器人 world model，不要默认“预测高清未来视频”是第一目标。

可以先做：

```text
future point tracks
future depth / occupancy
future object relation
```

然后测这些结构性目标是否已经足够提升 action policy。只有明确出现收益，再加入 RGB generation。

[论文](https://arxiv.org/abs/2609.17524) · [项目页](https://adamhung60.github.io/ModAR/)

## 8. RepoAtlas：长任务 Coding Agent 需要的是“会更新的仓库地图”，不是越来越长的聊天历史

**最新 Software Engineering 公开批次；v1 提交于 2026-09-15 10:11 UTC。**

### 突破性工程价值

repository-level coding 最大的问题之一，是任务所需上下文不是固定的。

刚开始修 bug 时可能只需要：

```text
issue
→ controller
→ service
```

调查到一半才发现真正原因在：

```text
shared library
→ generated client
→ config schema
```

如果一开始把全仓库 graph 全塞进 context，会过密、过贵；如果只在开始生成一次局部图，随着探索深入又会变 stale。

RepoAtlas 的核心因此不是“再做一个 repo RAG”，而是**让仓库视图本身跟 Agent 的探索状态一起演化**。

### Select → Project → Refresh

```text
Issue Evidence
      +
Agent Exploration State
      ↓
SELECT
固定预算选择 task-relevant code graph region
      ↓
PROJECT
同时形成 visual + textual repository view
      ↓
Agent 继续探索
      ↓
REFRESH
当前视图过时时重新选择与投影
```

它是 training-free module，可以挂在现有 Coding Agent 外部。

### 结果

SWE-bench Verified 中，相对论文最强 multimodal graph baseline：

```text
resolve rate       +2.4 points
input tokens       -5.8%
model calls        -7.8%
```

而且在三个不同 family / scale 的模型上都有一致收益。

这说明“上下文更少”与“成功率更高”并不矛盾；关键是当前 context 是否覆盖了正确的结构区域。

### 是否适合真实研发流程

非常适合大型单仓 / 多模块项目，特别是 Agent session 会持续数小时甚至多轮交接的情况。

真正持久化的对象可以从：

```text
chat summary
```

升级成：

```text
RepositoryView {
  task_id
  graph_revision
  selected_symbols
  selected_paths
  unresolved_dependencies
  evidence
  refresh_reason
}
```

新 session 可以从这份 artifact 重建上下文，而不是重放所有历史对话。

### 风险

静态 code graph 对 reflection、runtime dependency、代码生成、动态语言并不完整；visual representation 也可能给模型制造“图里没画就是不存在”的错误确定性。

因此 RepoAtlas 仍然需要 grep / build / runtime trace 等工具不断纠正 graph。

### 工程落地启发

如果不想实现论文完整方法，也可以先做一个轻量版本：每个任务维护 `relevant_files.md + dependency_edges.json + unresolved_symbols.md`，当 Agent 新发现跨文件依赖时更新，而不是一直往 prompt 追加源码。

[论文](https://arxiv.org/abs/2609.16936)

## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### A. 敏感动作的审批状态不要放在 Agent 能删除的文件里

9 月 15 日的一条 Claude 工作流社区分享讨论了一个非常现实的权限问题：如果“允许 merge / deploy”的 marker file 位于 Agent 可写目录，那么 Agent 可能通过删除或修改 marker 绕过软性审批。分享者建议把授权状态放到 Agent 权限边界之外，并在 `PreToolUse` 一类 hook 中使用明确的拒绝退出状态，而不是只返回自然语言提示。（[Reddit 原始讨论](https://www.reddit.com/r/ClaudeWorkflows/comments/1wglhhm/workflow_securing_claude_code_agents_preventing/)）

这属于**社区工程经验**，不是安全认证结论，但思路非常值得照搬：安全状态不能和被约束主体共享同一个可写控制面。

**今天怎么用：**把 `merge_allowed`、生产部署批准、密钥解锁等状态移到只读环境变量、外部审批服务或 Agent 无写权限的目录；hook 只读这些状态。拒绝路径必须 fail-closed，工具执行失败时默认不放行。

**风险 / 边界：**hook 本身也属于安全边界。若 Agent 可以修改 hook 配置、启动参数或执行器代码，外置 marker 仍然不够，需要 OS/container 权限进一步隔离。

### B. Claude Code 与 Codex CLI 混用时，先明确谁拥有 orchestration loop

一篇在 9 月 15 日更新的工程文章系统整理了 Claude Code 与 Codex CLI 的双向 MCP 连接方式。最有价值的不是“两个工具可以互相调用”，而是明确了三种角色分工：Claude 做规划、Codex 做明确子任务执行；Codex 做测试 / 执行外循环、Claude 做复杂诊断；或者用阶段 gate 串联多个专业 Agent。（[原文](https://codex.danielvaughan.com/2026/03/26/claude-code-codex-bidirectional-mcp/)）

**今天怎么用：**不要让两个 Agent 同时认为自己是总控。为一次任务固定一个 owner：

```text
orchestrator
  ↓ produces explicit artifact
verification gate
  ↓
worker agent
  ↓ produces patch / test result
verification gate
  ↓
next phase
```

对于 Codex 子任务，用 workspace sandbox；对于 Claude 暴露给外部 orchestrator 的工具，优先 allowlist `Read/Grep/Glob`，只有确实需要时再开放 Bash / Write。

**风险 / 边界：**MCP 层并不会自动转发下层 MCP 工具；此外 headless 权限、`approval-policy: never` 和共享配置文件都会扩大攻击面。跨 Agent 编排首先是权限工程，其次才是 prompt engineering。

### C. Flaky test 重试不能把 Agent 回归“洗绿”

9 月 15 日的 Coding Agent Guide 新增了一条针对 flaky tests 的实践：采用**有限重试 + 每次尝试保留证据 + 有过期时间的 quarantine**，而不是“失败就重跑，最后一次过了就算绿”。（[指南入口](https://codingagentguide.com/)）

这对于 Coding Agent 特别重要，因为 Agent 很容易把已有 flaky test 当成自己改动无关的噪声；反过来，无限重试又可能把真实回归隐藏掉。

**今天怎么用：**CI 中给 flaky candidate 固定最多 2–3 次重试，保存每次日志、seed、环境和失败签名；如果首次失败、后续通过，状态应标记为 `FLAKY/UNSTABLE` 而不是普通 PASS。quarantine 必须有 owner 和 expiry date。

**风险 / 边界：**不要让 Agent 自己决定把一个新失败加入永久 quarantine。新增 quarantine 应经过独立 review，否则它会成为最简单的“通过测试”捷径。

## 经典论文回顾

### On Degeneracy of Optimization-based State Estimation Problems：今天 LiDAR 退化检测方法仍在回答它提出的问题

Ji Zhang、Michael Kaess、Sanjiv Singh 的 **On Degeneracy of Optimization-based State Estimation Problems** 发表于 **ICRA 2016**。它是现代 LiDAR / Vision 退化检测中非常重要的经典工作之一，也是今天 LiLi 直接对比和改进的代表性基线。（[CMU 论文页](https://publications.ri.cmu.edu/on-degeneracy-of-optimization-based-state-estimation-problems)，[IEEE DOI](https://doi.org/10.1109/ICRA.2016.7487211)）

### 核心问题

优化式定位默认存在一个隐含条件：测量约束在所有需要估计的自由度上都提供足够信息。

但真实环境会出现：

```text
Camera：弱纹理 / 重复纹理
LiDAR：长走廊 / 隧道 / 大平面
```

此时某些状态方向几乎没有独立约束，优化问题变成 ill-conditioned，最终表现为漂移、抖动甚至完全发散。

### 关键数学思想

在当前线性化点附近，非线性最小二乘可以写成：

```text
min || J δx - r ||²
```

对应的信息 / Hessian 近似为：

```text
H = JᵀJ
```

如果 `H` 某些特征值很小，相应 eigenvector 就对应弱约束 / 退化方向。

经典方法据此把状态空间拆成：

```text
well-conditioned directions
→ 正常接受优化更新

degenerate directions
→ 抑制 / 投影掉不可靠更新
```

也就是不要求“整个位姿都可信或都不可信”，而是按方向处理。

### 当年为什么重要

在此之前，很多 SLAM 系统只在 estimator 发散以后才知道场景退化。

这篇工作将退化变成一个可在线检测的数值属性，并用 camera + LiDAR ego-motion 实验说明：在不增加新传感器的情况下，只要拒绝 ill-conditioned direction 中的虚假更新，就可以显著提高定位鲁棒性。

### 今天仍然在使用的思想

它留下的几个原则今天仍然非常重要：

- 可观测性 / localizability 应该是**方向级**而不是单个布尔值；
- Hessian / Fisher information 的谱可以作为 estimator health signal；
- 弱约束方向应该由其他传感器补，而不是让 scan matching 强行输出；
- 退化检测结果应进入后端信息矩阵和控制层 telemetry。

今天大量 LIO 工作仍然从 eigenvalue、condition number、局部几何贡献等角度扩展这条路线。

### 今天已经暴露出的局限

LiLi 今天提出的核心批评正好揭示经典 Hessian 方法的局限：

> 当前 `JᵀJ` 描述的是当前线性化与对应关系附近的信息结构，但真实 point-cloud registration 在位姿变化后会重新关联数据点。

因此 Hessian 看起来“有约束”，并不一定意味着全局上没有另一族等价解；噪声和复杂几何也会让固定阈值敏感。

现代方法开始加入：

```text
raw measurement localizability
correspondence-level contribution
reassociation-aware perturbation
learning-based risk prediction
multi-sensor directional fusion
```

### 公开代码与可复现性

经典论文有公开 PDF 和完整算法描述，但没有今天这种一键式官方独立仓库。复现本身并不困难：大多数点云优化器已经能输出 Jacobian / approximate Hessian，核心工作是谱分解、方向投影和正确处理旋转 / 平移尺度。

### 对当前工程项目的重新解读

对 16 线 LiDAR 或 MID360 系统，最值得保留的不是某个固定 eigenvalue threshold，而是一个统一接口：

```text
EstimatorObservability {
  rotation_xyz_score
  translation_xyz_score
  source: lidar | vision | imu | wheel | rtk
  timestamp
}
```

后端融合再按方向分配信息权重。

例如长走廊中：

```text
LiDAR 横向 / yaw 可能很强
LiDAR 走廊轴向很弱
Wheel 轴向短期较强
RTK / Reflector 提供长期绝对约束
```

这种方向级融合比“LiDAR 退化了就整体降权”更符合真实可观测性结构。

[CMU 论文页](https://publications.ri.cmu.edu/on-degeneracy-of-optimization-based-state-estimation-problems) · [IEEE DOI](https://doi.org/10.1109/ICRA.2016.7487211)

## 今日结论

今天最新批次里，对 SLAM 工程最有价值的两句话是：

> **退化应该输出“哪些方向不可信”，而不是只输出“当前帧坏了”。**

> **长期地图应该保存“哪里发生了变化”，而不是让新观测悄悄覆盖旧世界。**

LiLi 把退化检测从当前 Hessian 的局部谱进一步推向重新关联后的 SE(3) 等价变换；CDSD 则把地图变化做成 scene/submap 层面的独立问题。对正在使用 LIO-SAM / FAST-LIO2 的系统，这两项都可以作为 sidecar 加进去，而不必替换主前端。

HuMemSLAM 展示的 place-recognition 分层同样值得保留：learned semantic / contextual model 最适合缩小候选集，几何后端继续承担最终裁决。这样神经网络出错时，系统还有第二种独立失败模式可以把错误挡住。

TIO-Former 的信号则很有硬件意义：几何里程计不等于必须有完整激光点云。六方向稀疏 ToF 只要和 IMU、时间模型结合得足够好，也能成为低 SWaP-C 平台的 metric anchor。更重要的是它认真处理了 long-running transformer 的 memory complexity，而不是只报短序列精度。

控制侧今天可以归纳成：

```text
Contact / Mode
必须进入安全状态

Actuator Capability
必须进入稳定性状态
```

Hybrid HJ 让离散接触 mode 成为 reachability state 的一部分；Wrench Polytope 则让“关节到底还能产生多少稳定力矩”成为实时控制变量。对于腿式机器人，单纯用姿态角 / COM / support polygon 做稳定性判断会越来越不够。

ModAR 的结果非常值得机器人基础模型团队冷静看待：预测未来 RGB 并不是世界模型的最终目的。motion、semantics、geometry 这些更结构化、与动作强相关的中间模态，可能以更低计算成本带来更稳定收益。

AI Coding 侧，RepoAtlas 与本期社区精选实际上在回答同一问题：

```text
长期 Agent 真正应该持续增长的是 Artifact，
不是 Conversation。
```

代码依赖图、当前 relevant files、unresolved symbols、验证证据、审批状态和 flaky-test history 都应该位于模型上下文之外，并允许新 session 重新加载。这样即使模型和聊天被重启，项目状态也不会被“总结压缩”成越来越模糊的自然语言。

## 最值得深入研究或尝试复现的方向

1. **LiLi 式 Directional Degeneracy Sidecar。** 在现有 ICP / LIO-SAM 中保留 Hessian baseline，再对疑似退化帧沿 `se(3)` 六个生成方向做小扰动 + 重新配准，统计哪些方向存在等价解。先 shadow 输出 6DoF localizability，不直接改变 estimator，再比较长走廊和坡地中的 failure lead time。

2. **16 线 / MID360 的多源方向级融合。** 给 LiDAR、IMU、轮速、RTK / 反光标志分别维护 `rotation_xyz / translation_xyz` information score，让因子图按方向调信息矩阵，而不是整传感器统一乘一个权重。重点复现“走廊轴向弱、横向强”的真实曲线。

3. **Submap Change Journal。** 在现有长期地图上把房间 / 10–30 m 路段切成 scene submap；跨 session 只生成 `candidate change event`，连续两次确认以后再更新 static navigation layer。统计 false change、missed change 和 map rewrite 对定位的影响。

4. **Hybrid Skill Safety Envelope。** 对楼梯 / 转弯任务明确 `flat / ascending / landing-turn / descending / recovery` 五种 mode，每个 mode 定义允许进入和退出的状态集合；控制接口仍使用现有 `vx/vy/vw`，但 mode transition 由独立 safety gate 决定。

5. **Repository View Artifact。** 给 Coding Agent 增加 `relevant_files.md + dependency_edges.json + unresolved_symbols.md + validation_receipts/`。每次发现新的跨文件关系就刷新 view；新 session 只加载当前 view 和任务 spec，比较与“连续几天一个大 session”在 token、定位错误与返工次数上的差异。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [LiLi: Lie Theory Based 3D LiDAR Scan Alignment Degeneracy Detection](https://arxiv.org/abs/2609.17145)
- [HuMemSLAM: Efficient Human-Inspired Semantic Place Recognition for Robust Visual SLAM](https://arxiv.org/abs/2609.17168)
- [TIO-Former](https://arxiv.org/abs/2609.17198) · [官方仓库](https://github.com/Ly041021/TIO-Former)
- [Online Geometric Change Detection via Scene Decomposition](https://arxiv.org/abs/2609.17302) · [代码](https://github.com/vectr-ucla/geometric_change_detection)
- [Hamilton-Jacobi Reachability for Hybrid Systems](https://arxiv.org/abs/2609.17430) · [IJRR DOI](https://doi.org/10.1177/02783649261477777)
- [Optimized Wrench Polytope Analysis](https://arxiv.org/abs/2609.17405)
- [Modality-Autoregressive World-Action Models / ModAR](https://arxiv.org/abs/2609.17524) · [项目页](https://adamhung60.github.io/ModAR/)
- [RepoAtlas](https://arxiv.org/abs/2609.16936)
- [社区经验：Agent 敏感动作审批状态外置](https://www.reddit.com/r/ClaudeWorkflows/comments/1wglhhm/workflow_securing_claude_code_agents_preventing/)
- [Claude Code ↔ Codex CLI 双向 MCP 工程文章](https://codex.danielvaughan.com/2026/03/26/claude-code-codex-bidirectional-mcp/)
- [Coding Agent Guide](https://codingagentguide.com/)
- [On Degeneracy of Optimization-based State Estimation Problems](https://publications.ri.cmu.edu/on-degeneracy-of-optimization-based-state-estimation-problems) · [IEEE DOI](https://doi.org/10.1109/ICRA.2016.7487211)
