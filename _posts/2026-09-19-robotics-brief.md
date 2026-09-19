---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-19"
date: 2026-09-19 09:00:00 +0800
description: "周末回补 9 月 18 日最新公开批次：无标定单目 Gaussian SLAM、RAW HDR SLAM、农业语义 SLAM、未知环境可移动障碍规划、视频想象双模态导航、SafeHarness、UniExo 与屋面人形控制。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-19

## 摘要

截至 9 月 19 日早间检索，最新高质量 Robotics 候选仍主要来自 9 月 18 日公开批次，论文 v1 多提交于 9 月 17 日 UTC。今天因此不虚构“9 月 19 日新批次”，而是在完整读取 `robotics-brief-covered-items.md` 后，从上一批次继续强制去重回补。昨天已经覆盖 AMB3R-SLAM、Dynamic-LIVO、DR-MPC、SGPS、Workspace Models 等，因此本期换到此前未覆盖、但工程价值较高的 8 项工作。

今天最值得关注的是三个趋势。第一，SLAM 正在同时向两个方向扩展：一端是 **VGGT-GS SLAM** 这种把 feed-forward 几何先验、在线相机标定、Gaussian map 和 Sim(3) 全局一致性放进同一系统；另一端是 **RawSLAM**，开始正面处理 RAW/HDR 输入而不是默认 ISP 后的 8-bit 图像。第二，语义地图与任务规划正在更紧地耦合：农业语义 SLAM把植物类别、尺寸、健康状态作为概率地图属性；NAMO 则把“绕过去还是搬开障碍”本身变成在线规划决策。第三，机器人 Agent 的安全瓶颈越来越清楚：不是模型没看到约束，而是自然语言约束没有被编译为几何可验证的执行结构，SafeHarness 对这个问题给出了很直接的答案。

如果只选一个方向自己动手复现，我会优先做 **RawSLAM 的 HDR photometric front-end 改造** 或 **SafeHarness 的几何执行层**。前者可以直接验证现有视觉 SLAM 在强明暗差、曝光切换场景中的真实收益；后者不需要重新训练大模型，适合把 Coding Agent / VLM 的高层计划接到现有 MoveIt、Nav2 或自研局部规划器前做硬约束落地。

## 1. VGGT-GS SLAM：无标定单目 Gaussian SLAM，把“相机模型不可信”也纳入在线优化

**时间回补；v1 提交于 2026-09-17，进入 9 月 18 日公开批次。**

### 为什么重要

很多单目 Gaussian Splatting SLAM 默认内参、畸变已经可靠标定，但真实产品最常见的问题恰恰是：换镜头、电子防抖、裁剪缩放、低成本模组装配误差都会让固定标定失效。VGGT-GS SLAM 的价值在于，它不把相机标定看成离线前置条件，而是把相机位姿、Gaussian map、共享内参和径向/切向畸变一起优化。

[论文](https://arxiv.org/abs/2609.19628)

### 算法模块

系统可以概括为：

```text
Uncalibrated monocular video
          ↓
VGGT feed-forward priors
  ├─ pose prior
  └─ depth prior
          ↓
Submap differentiable bundle adjustment
  ├─ camera poses
  ├─ 3D Gaussian map
  ├─ shared intrinsics
  └─ radial-tangential distortion
          ↓
Gaussian-Native Alignment (GNA)
  ├─ sequential submap scale refinement
  └─ loop candidate verification
          ↓
Global Sim(3) pose graph
```

其中值得注意的是 analytic calibration Jacobian。相机参数如果只靠数值差分或完全交给自动微分，在线 BA 中容易带来额外开销和病态尺度；显式 Jacobian 让“标定变量也参与 SLAM”更像传统几何优化，而不是只靠网络先验兜底。

### 传感器与模型假设

输入是单目 RGB，依赖 VGGT 提供初始 pose / depth prior。单目系统仍然存在尺度与运动退化问题，所以作者在子图之间额外做 camera-anchored scale refinement，并最终用 Sim(3) 图优化处理全局尺度一致性。

需要特别注意：在线估计焦距和畸变并不意味着任意运动都可观。如果相机长期纯旋转、视差很弱、视野内结构单一，内参与深度/位姿仍可能互相补偿。

### 实时性与可复现性

论文在标准室内 benchmark 上报告了更好的定位与渲染结果，但其后端明显比纯 feature / direct odometry 更重。工程复现时不要只记录 ATE，建议额外记录：

```text
tracking latency P50/P95
submap BA time
peak VRAM
intrinsics drift
loop alignment failure rate
Sim(3) correction magnitude
```

如果系统在长序列中不断靠相机参数吸收位姿误差，短期 ATE 可能很好，但标定值会逐渐变得不物理。

### 鲁棒性与工程风险

最大风险是 **多组变量之间的可观性耦合**。Gaussian geometry、camera pose、focal length、distortion、submap scale 都能解释部分重投影误差，因此必须监控 Hessian 条件、标定变化率和参数先验。

另一个风险来自 feed-forward prior：先验很好时优化容易收敛，先验在反光、弱纹理、运动模糊下系统性偏差时，后端可能进入错误 basin。

### 适合谁关注

神经 SLAM、3DGS SLAM、无标定视觉设备、消费级相机长期建图、需要在线相机自校准的移动机器人。

### 工程落地启发

对已有 ORB-SLAM3 / VINS / Gaussian mapping 系统，不必一次性全换。更现实的验证路线是先把焦距、主点和畸变作为低频 calibration state，只在关键帧窗口条件数足够好时更新；条件退化时冻结参数。这样能先验证“在线标定到底解决了多少现场问题”。

## 2. RawSLAM：视觉 SLAM 不应默认 ISP 已经替你解决了光照问题

**时间回补；v1 提交于 2026-09-17。**

### 为什么重要

传统视觉 SLAM 的 photometric residual 常建立在 8-bit sRGB 图像上，但这已经经过曝光、白平衡、tone mapping、gamma、降噪和锐化。尤其在室内外切换、窗边逆光、矿井灯光、仓库高反差等场景，ISP 的非线性会破坏“同一点亮度应该一致”这个假设。

RawSLAM 直接面向单曝光 16-bit 线性 HDR 图像，核心问题不是做更漂亮的 HDR，而是让跟踪和 Gaussian map 在大动态范围下保持更稳定的光度关系。

[论文](https://arxiv.org/abs/2609.20589)

### 算法模块

作者提出 architecture-agnostic HDR Gaussian module，主要包括：

```text
16-bit linear RAW/HDR
        ↓
MLP-free logarithmic Gaussian color parameterization
        ↓
Reinhard range-compressed photometric objective
        ↓
structure-guided spatial gradient weighting
        ↓
tracking + Gaussian reconstruction
```

“MLP-free”很重要：它避免为了拟合 HDR response 再引入一个小网络，把额外自由度塞进已经很复杂的 SLAM 优化中。

### 传感器与假设

这条路线要求相机能输出稳定 RAW 或接近线性的高位深数据。实际部署时还要区分：

- 真正 sensor-linear RAW；
- 厂商所谓 10/12/16-bit 但已经经过部分 ISP 的数据；
- rolling shutter 与曝光时间变化；
- 黑电平、坏点、镜头阴影、温漂。

论文提供 10 个真实室内序列，包含 16-bit RAW、对齐深度、IMU 与 OptiTrack 真值，适合做曝光/动态范围相关的消融。

### 结果与可复现性

摘要报告该模块在直接 HDR 化 MonoGS 的基线之上改善轨迹与重建，并可迁移到 SplaTAM、Gaussian SLAM、DROID-W；在 8-bit 输入上同一 formulation 也有收益。不过截至当前，代码和数据仍标注将公开，因此今天只能核验方法与论文结果，不能把它当成已可一键复现的开源方案。

### 工程风险

RAW 最大的问题不是算法，而是数据链。CameraX、V4L2、MIPI ISP、厂商 HAL 往往会在你以为拿到“原始图”之前已经做处理。移动端和嵌入式端还要考虑 16-bit 带宽与缓存压力。

此外，HDR residual 更稳定不代表几何可观性增强；弱纹理、快速运动、重复结构仍是原问题。

### 适合谁关注

工业视觉 SLAM、强明暗差场景、煤矿/隧道/仓库、相机 ISP 可控的自研硬件、Gaussian SLAM。

### 工程落地启发

如果现有 SLAM 在灯光切换时经常炸，先别急着换大模型。可以先做一个低成本实验：同一相机同时保存 RAW 与 ISP 输出，固定轨迹跑 photometric residual 分布、inlier ratio、tracking loss 和曝光跃迁前后 ATE。如果 RAW 明显更稳定，再决定是否值得改造完整 front-end。

## 3. 农业语义 SLAM：把植物类别、尺寸、健康状态当作“概率地图属性”而不是检测结果截图

**时间回补；v1 提交于 2026-09-17。**

### 为什么重要

语义 SLAM 常见做法是把 detector label 直接贴到点云或对象节点上，但真实农业场景会反复观察同一植株，检测类别、尺寸和健康状态都有噪声。论文把这些 semantic attributes 放入 Bayesian update，并与 g2o 图优化结合，形成可持续修正的对象级世界模型。

[论文](https://arxiv.org/abs/2609.20604)

### 算法模块

```text
Depth camera observations
        ↓
YOLOv8n object / semantic extraction
        ↓
Object association
        ↓
Bayesian semantic attribute update
  ├─ plant type
  ├─ size
  └─ health
        ↓
g2o graph-based SLAM
        ↓
probabilistic semantic field map
```

它的工程价值不在于 YOLOv8n，而在于“同一个对象的新观测应该更新 belief，而不是覆盖旧值”。

### 传感器、实时性与结果

系统在 Gazebo 和室内人工植株场地中用 Boston Dynamics Spot 验证，论文报告可实时映射至少 400 株植物。定位不只依赖 GPS，这对温室、棚内和遮挡严重区域有意义。

### 鲁棒性与风险

农业语义地图真正困难的是 data association。两株相近植物长得很像，如果机器人轨迹漂移或行间距规则重复，很容易把观测更新到错误对象。一旦 association 错，Bayesian update 会“非常自信地累计错误证据”。

所以工程实现应同时维护：

```text
object identity confidence
pose uncertainty
semantic posterior
association residual
last-seen timestamp
```

不能只保存最终 label。

### 适合谁关注

农业机器人、对象级 SLAM、长期语义地图、巡检资产管理、需要把语义状态持续更新而非一次性检测的系统。

### 工程落地启发

这套思路很容易迁移到工业巡检：把“仪表正常/异常、阀门开/关、设备热状态”等作为对象属性，用多次观测更新 posterior，同时让对象节点绑定 SLAM keyframe/submap identity，而不是只存绝对坐标。

## 4. Navigate or Relocate?：未知环境里，“绕路”与“搬障碍”应该是同一个在线规划问题

**时间回补；v1 提交于 2026-09-17。**

### 为什么重要

传统导航遇到障碍通常只有两个极端：局部规划绕过去，或者任务失败等待人工。对于带机械臂、推杆、可搬动物体能力的移动机器人，真正的问题是：

```text
现在看到的障碍后面有没有更短的未知通路？
还是应该花操作代价把障碍移开？
如果要移开，先移哪个？移到哪里？
```

论文把这类 NAMO（Navigation Among Movable Obstacles）问题放到未知环境中在线求解。

[论文](https://arxiv.org/abs/2609.19541)

### 算法思路

一个很实用的判断框架是同时维护两类最短路：

```text
Path A: 把已发现可移动物体当作不可穿越障碍
Path B: 允许移除这些物体
```

两者代价差异决定是否值得启动 relocation search。真正执行搬移时，再用 sampling-based search 搜索相互依赖的搬移序列；LLM 只负责 bias sampling，而不是替代可行性验证。

### 假设与实时性

系统需要知道哪些障碍“可移动”，并且有某种移动/操作代价模型。摘要目前主要报告 numerical experiments，因此对真实机器人来说，物体质量、摩擦、抓取/推挤可达性和动态稳定性仍是大空缺。

### 鲁棒性与工程风险

最大的风险是把 LLM 的语义常识误当成物理可执行性。模型可能认为纸箱“能搬”，但不知道箱子被固定、太重、后面连着电缆。

因此 LLM 最合理的位置是：

```text
proposal prior / sample bias
          ↓
geometry + dynamics + manipulation feasibility checker
          ↓
verified relocation action
```

而不是直接输出执行动作。

### 适合谁关注

移动操作、仓库/家庭机器人、狭窄空间巡检、具备推/拉/搬能力的轮足平台。

### 工程落地启发

现有 Nav2 / MoveIt 系统可以先做一个简化版：把可移动障碍节点加入任务图，定义 `detour_cost`、`manipulation_cost`、`uncertainty_cost`，只有预期收益超过阈值才进入操作规划。这样比直接训练端到端 NAMO 策略更容易验证安全边界。

## 5. TADreamer：让视频生成模型“想象路线”，但真正执行仍回到可测量几何

**时间回补；v1 提交于 2026-09-17。**

### 为什么重要

地面-空中双模态机器人不仅要决定去哪里，还要决定什么时候滚/走、什么时候飞。语言指令和场景语义很适合 VLM 处理，而连续 3D 几何与执行安全又更适合传统规划器。TADreamer 的有趣之处，是用生成视频承担“行为想象”，再把想象结果校准回真实几何。

[论文](https://arxiv.org/abs/2609.19824)

### 算法模块

```text
Onboard observation + language instruction
                ↓
VLM prompt / candidate selection / feedback
                ↓
Video generator imagines navigation sequence
                ↓
3D reconstruction
  ├─ waypoints
  └─ terrestrial / aerial mode labels
                ↓
Two-stage metric calibration
  1. FOV constraints initialize scale
  2. axis-wise scale + R + t registration
                ↓
Measured-geometry planner executes
```

这套结构最值得借鉴的是：**生成模型输出不是直接控制命令，而是一个需要重新落到传感器几何坐标系的高层候选。**

### 结果与实时性

论文在 7 个室内外真实场景上验证；每轮生成 5 个候选，7 个场景都能在两轮内得到可用视频。对于 calibration observations，相比 NavDreamer，深度 MAE 和相对深度误差分别大幅下降。

但生成视频本身很难进入 20–100 Hz 控制环，所以它天然是低频 planning layer。真正高频执行仍依赖测量几何和传统控制器。

### 工程风险

风险包括视频生成随机性、3D 重建尺度/轴向畸变、动态障碍未进入 imagined plan，以及生成延迟。尤其当想象路线穿过传感器未覆盖区域时，必须把它当“建议”，而不是自由空间证明。

### 适合谁关注

地空两栖机器人、语义导航、VLM + 传统规划混合架构、需要低频任务推理和高频安全控制分层的系统。

### 工程落地启发

对无人机来说，可以把生成模型输出限制为 `topological route + behavior mode + coarse waypoint`，再由 ESDF/voxel map + MPC 做最后 10–20 m 的连续轨迹。这样能把语义能力和几何安全清晰隔离。

## 6. SafeHarness：机器人 Coding Agent 的安全失败，往往不是“没理解约束”，而是约束没有进入执行结构

**时间回补；v1 提交于 2026-09-17。**

### 为什么重要

这篇论文的负结果非常值得重视：Agent 的 trace 里会谈论障碍，prompt 也明确禁止碰撞，但机器人仍经常撞上障碍。也就是说，问题不是 perception 没看到，也不是 instruction 不清楚，而是自然语言安全约束没有被转化成规划器里的 priority / geometry constraint。

[论文](https://arxiv.org/abs/2609.20822)

### 两个 Harness

作者把操作拆成 route phase 和 contact-rich moment，并分别增加结构化 harness：

```text
1. Obstacle-aware route planning
   object bounding boxes
        ↓
   candidate waypoint routes
        ↓
   plan → verify → replan → execute

2. Obstacle-aware contact execution
   choose contact position
        ↓
   verify contact itself respects obstacle constraint
```

这比“再写一条 system prompt 强调安全”强得多，因为安全约束进入了工具接口和执行流程。

### 结果

论文报告 SafeHarness 达到 71.9% task success、87.5% collision avoidance；相对前一 SOTA 分别提升 6.5 和 27.0 个百分点，并显著高于同一 Agent 不带 harness 的结果。

### 实时性、可复现性与风险

Harness 本身不要求重新训练基础模型，理论上很适合复用到现有 Coding Agent。真正风险在几何抽象：bounding box 只是近似，细长物、凹物体、旋转物体和机械臂 swept volume 都可能让 box-based verifier 误判。

真实系统最好把验证层继续下沉到：

```text
signed distance / collision checker
joint limits
self collision
velocity / acceleration bounds
contact wrench limits
runtime emergency stop
```

### 适合谁关注

LLM/Coding Agent 控制机器人、VLM 任务规划、自动生成 ROS/MoveIt controller、工业机器人 Agent 安全。

### 工程落地启发

这篇论文对软件 Agent 同样适用：`“不要删生产数据”` 只是文本约束；真正可靠的是让工具层没有这项 capability，或要求独立 verifier / approval token。安全需求必须从 prompt 编译到 **可执行权限与可验证结构**。

## 7. UniExo：外骨骼不再靠手工切换走/跑/转身模式，而是学习连续技能 latent

**时间回补；v1 提交于 2026-09-17。**

### 为什么重要

传统外骨骼辅助往往按步态状态机设计：walking、running、turning、backward 各有一套控制器，再写切换逻辑。真正使用时，人不会提前告诉设备“下一秒我要从走路切成转身”。UniExo 试图把这些技能压入一个连续 skill latent，再让人和外骨骼共同适应。

[论文](https://arxiv.org/abs/2609.19690)

### 方法结构

```text
Human motion demonstrations
     ↓
4 single-skill imitation experts
  ├─ walk
  ├─ turn
  ├─ run
  └─ backward
     ↓
distill into unified skill-latent human policy
     ↓
RL fine-tuning for transitions
     ↓
hip-moment prediction initializes exoskeleton controller
     ↓
multi-agent RL co-adaptation
  ├─ human policy
  └─ exoskeleton policy
```

这相当于把“模式切换器”从手工 FSM 改成 learned latent dynamics。

### 结果与假设

论文报告统一 human policy 在未见动作片段上达到 94.7% tracking success。硬件实验使用自研 hip exoskeleton，在多位参与者的不同 treadmill speed 下测试，并展示了无需显式技能标签的连续多技能路线。

### 工程风险

外骨骼是典型 safety-critical human-in-the-loop 系统。当前结果不能被解释成“可直接替换产品状态机”：参与者数量有限，连续复杂路线的验证尤其需要更大样本；不同体型、疲劳、步态病理和误触发都可能造成分布外状态。

部署时必须保留 torque/angle/rate limit、机械限位和可解释的 fallback controller。

### 适合谁关注

可穿戴机器人、人机协同控制、multi-agent RL、连续技能切换、康复与助力设备。

### 工程落地启发

更一般的机器人也可以借鉴“连续 skill latent”：例如轮足狗的平地、斜坡、楼梯、跨障不一定要靠硬阈值 FSM 切换，可以用 latent manager 平滑选择控制策略，但低层安全和可行域仍由确定性控制器约束。

## 8. 屋面施工人形机器人：把人类动作、屋面几何和执行误差一起放进训练闭环

**时间回补；v1 提交于 2026-09-17。**

### 为什么重要

屋面施工是一个比“实验室平地人形行走”苛刻得多的任务：地面有持续坡度，操作会改变重心，工具与屋面需要保持相对位置，还要同时满足足底支撑与手部工作空间约束。

这项工作以 Unitree G1 为平台，把 human demonstration、metric roof scene、trajectory optimization 和 execution-aware RL 串在一起。

[论文](https://arxiv.org/abs/2609.20558)

### 算法模块

```text
Human demonstrations
       ↓
motion tracking + retargeting
       ↓
metric roof scene model
       ↓
trajectory-level optimization
  ├─ support contacts grounded to roof
  └─ work relations grounded to scene
       ↓
execution-aware RL
  └─ tolerate tracking/model errors
       ↓
whole-body execution on G1
```

这个流程的亮点是没有把示范轨迹直接当 reference，而是先让轨迹对真实屋面几何重新“落地”。

### 结果

论文覆盖不同 roof pitch，并做 nailgun、hammering、pushing 等消融；报告 work-clearance 误差在毫米到厘米以内，且真实 G1 展示了上坡行走、钉枪、锤击和弯身动作。

### 鲁棒性与工程风险

论文验证仍远不足以代表真实建筑工地安全。真实屋面有湿滑、松动材料、未知承载、风、绳索和人体共域等复杂因素。训练中的 metric roof model 如果与真实结构偏差过大，动作“看起来对”但接触力可能完全错误。

工程上至少需要独立的：

```text
terrain friction estimation
support polygon / wrench margin
slip detection
fall protection
tool reaction-force monitoring
human exclusion zone
```

### 适合谁关注

人形机器人、斜坡全身控制、施工机器人、动作重定向、场景约束 RL。

### 工程落地启发

对楼梯/坡面轮足机器人也有直接启发：不要只把 terrain height 当 observation，而要把**任务相关接触关系**显式投影回场景几何，比如足端支撑面、机身 clearance、工具工作面和下一落脚区域。

## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### A. Agent 技能、MCP、插件也应该有“使用率遥测”，否则只是在不断堆工具

GitHub 9 月 17 日把 Copilot CLI 的 skill、custom agent、MCP server、slash command 和 plugin 使用情况加入 Usage Metrics API，包括 top items 的 `interaction_count` 和不同项目的 distinct-use count。值得注意：MCP 的 interaction count 统计连接/重连尝试，不是每次工具调用；plugin skill 同时会进入 skill 统计，因此不能简单相加。

[GitHub Changelog](https://github.blog/changelog/2026-09-17-agentic-cli-customizations-now-in-the-usage-metrics-api/)

**今天就能用：**自研 Agent 平台也给每个 skill/MCP/tool 记录 `invocation_count`、`success_rate`、`p95_latency`、`token_delta`、`human_override_rate`，每周淘汰长期没人用或失败率高的工具。

**为什么值得学：**Agent 工具越多不一定越强。工具描述会占 context，路由空间也会扩大。没有 telemetry，就不知道“这个 MCP 是真的提高了完成率，还是只让 prompt 更长”。

**适用场景：**公司内部 Agent、Codex/Claude/Copilot 多工具开发环境、长期维护的 skill 库。

**风险 / 边界：**使用次数不等于价值。低频但关键的生产恢复工具不能因为调用少就删除；要和任务成功、风险等级联合看。

### B. Agent 生成的 CI/CD 不能只审 YAML：对“谁能触发、什么事件能触发”再加一层执行保护

GitHub Actions 的 workflow execution protections 已在 9 月 17 日 GA，可以按 actor、event 和具体 workflow file 设 allowlist，并支持 evaluate/shadow mode。GitHub 还明确提醒 `pull_request_target` 在公开仓库中具有 secrets 暴露风险，并计划对未配置相应策略的公开仓库逐步采用更安全的默认保护。

[GitHub Changelog](https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/)

**今天就能用：**对于允许 Coding Agent 修改 `.github/workflows/` 的仓库，把 `deploy.yml`、release、签名、生产迁移等 workflow 单独收紧；先用 evaluate mode 观察一周，再强制 enforce。把 `pull_request_target` 当成高风险触发器单独审查。

**为什么值得学：**Agent 可以写出语法正确、测试也通过的 workflow，但它未必理解组织级 secrets 边界。最可靠的防线不是“要求 Agent 小心”，而是让平台拒绝不符合 actor/event policy 的执行。

**风险 / 边界：**策略过紧会阻断合法自动化，因此先 shadow/evaluate，再逐步 enforcement；同时要防止出现“为了过策略而把高权限动作迁到另一个未受保护 workflow”。

### C. 给 LLM Gateway 增加请求分类与工具耗时提示，定位“慢是模型慢，还是工具链慢”

Claude Code v2.1.273 增加了可选的 `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1`，向 LLM gateway 发送 request class、agent type、previous tool durations、compaction 与 context-compacted 等提示头。这类信息非常适合做企业内部 Agent 的网关级 SLO 分析。

[Claude Code Releases](https://github.com/anthropics/claude-code/releases)

**今天就能用：**如果公司自建 LLM gateway，把一次 Agent turn 拆成：模型排队时间、模型首 token、工具调用耗时、compaction 发生次数、上下文大小、最终任务状态。对长任务至少看 P50/P95，不要只看平均响应时间。

**为什么值得学：**很多“模型最近变慢”的问题其实来自 MCP 连接、测试命令、上下文压缩或某个远程工具。网关如果只记录模型 latency，很难做根因分析。

**风险 / 边界：**不要把敏感 prompt、文件路径、客户标识直接塞进 telemetry 标签；request-class / agent-type 应采用枚举和聚合，工具参数保持脱敏。

## 经典论文回顾

### FAB-MAP：Probabilistic Localization and Mapping in the Space of Appearance（2008）

Mark Cummins 与 Paul Newman，The International Journal of Robotics Research，2008。论文首次在线发表于 2008 年 6 月。([Oxford Research Archive](https://ora.ox.ac.uk/objects/uuid%3A917f6474-bc02-4d6d-8f51-c8bd90b2bbb8)，[DOI](https://doi.org/10.1177/0278364908090961))

### 它解决的核心问题

视觉 place recognition 最危险的不是“没认出来”，而是 **perceptual aliasing**：两个完全不同的地方，因为都有门、窗、走廊、树等高频视觉词，看起来很像。

如果回环检测只做 descriptor similarity：

```text
similarity > threshold → loop closure
```

那么重复环境很容易产生灾难性假回环。FAB-MAP 把问题改写成概率推断：当前 observation 到底来自已有 place，还是一个从没见过的新 place？

### 核心数学思想

它使用 bag-of-visual-words 表示图像，但没有假设所有视觉词彼此独立，而是用 Chow-Liu tree 近似视觉词之间的联合分布。直觉是：

```text
P(z_1, z_2, ..., z_n)
≈ P(z_root) ∏ P(z_i | z_parent(i))
```

这样“窗 + 墙 + 门”这种经常共同出现的词不会被错误地当成三份独立证据重复加权。

对于每个候选 place，系统计算 observation likelihood，同时保留一个“new place”假设。只有已有地点的后验概率真正压过新地点假设，才应接受 place match。

### 为什么当年重要

在深度学习全局描述子出现之前，FAB-MAP 让大规模视觉回环从“最近邻匹配 + 手工阈值”升级为一个明确处理 perceptual aliasing 的概率模型。原论文强调算法复杂度随地图地点数线性增长，并能在线新增 place，非常适合移动机器人长期定位。

### 今天仍然在使用的思想

现代 VPR 已经从 SURF/BoW 换到 NetVLAD、CosPlace、MixVPR、DINO/SALAD 等 learned global descriptor，但 FAB-MAP 的几个系统思想仍然非常现代：

1. **Loop closure 是概率决策，不是相似度排序。**
2. **必须保留“这是新地方”的假设。**
3. **高频共现特征不应被重复计证据。**
4. **回环候选需要结合先验和后验，而不是只看 top-1 score。**

### 已被后续方法替代的部分

传统 visual word quantization、Chow-Liu tree 和手工局部特征今天大多已不是最强配置。现代系统通常使用神经全局描述子召回，再用 SuperPoint/LightGlue、PnP-RANSAC、ICP/GICP 或局部几何一致性做 verification。

但很多系统反而退回了一个简单的 cosine threshold。这个时候重新读 FAB-MAP 会发现：**descriptor 变强并没有消灭 false loop 的决策问题。**

### 传感器与假设

FAB-MAP 本质上只需要视觉 appearance，不要求连续里程计才能做 place recognition，因此能作为 SLAM 的独立 loop detector。它假设训练数据足以学习视觉词的统计共现关系；如果部署域和训练域差异过大，生成模型同样会失效。

### 现在怎么复现

现代复现不一定照搬原始 BoW，可以做一个“FAB-MAP 思想版”实验：

```text
DINO/SALAD global descriptor
        ↓
Top-K retrieval
        ↓
calibrated probability / new-place hypothesis
        ↓
local feature or LiDAR geometric verification
        ↓
pose graph loop factor
```

然后在重复走廊、停车场、厂房等强 aliasing 数据上比较：

- 固定 cosine threshold；
- top-K + geometric verification；
- 带 new-place prior 的概率 gating；
- false-positive rate、precision-recall、最终 ATE 和 catastrophic loop 次数。

### 对当前工程的重新解读

如果使用 Scan Context、learned LiDAR descriptor 或视觉 VPR，最值得借鉴 FAB-MAP 的不是旧特征，而是 **不要让候选召回器直接拥有“写入 pose graph”的权力**。召回、概率门控、几何验证、图优化应该是不同责任层；尤其 16 线 LiDAR、长走廊和重复工业环境中，这比换一个更大的 descriptor 网络更重要。

## 今日结论

今天的 8 条工作看起来跨度很大，但可以归到一个共同方向：**把过去隐含在系统外部的条件，显式纳入可优化、可验证的状态或接口。**

VGGT-GS SLAM 把相机内参与畸变纳入 SLAM；RawSLAM 把 ISP 前的线性亮度重新纳入光度模型；农业语义 SLAM 把多次观测下的语义不确定性纳入地图；NAMO 把“是否值得搬障碍”纳入导航代价；TADreamer 把生成式想象重新锚定到实测几何；SafeHarness 则把自然语言安全约束编译成 waypoint 与 contact verifier。

对真实机器人而言，这比单纯追求更大的模型更有意义。很多现场失败不是 backbone 不够强，而是关键约束只存在于人的脑子、prompt 或配置注释里，没有进入系统的 state、cost、constraint、verification 或 permission layer。

## 最值得深入研究或尝试复现的方向

**首选：RawSLAM 风格的 RAW/HDR 前端 A/B。** 如果手里有可输出 RAW 的相机，录同一条强光照变化轨迹，比较 8-bit ISP 图和 12/16-bit linear 输入的跟踪 inlier、photometric residual 和 ATE。这个实验成本低，却能直接回答“现场视觉退化到底来自几何还是 ISP”。

**第二：SafeHarness 风格的 Agent 执行协议。** 对现有机器人 Agent 定义一个 `plan → verify → execute → monitor` typed interface，禁止模型直接把自由文本变成运动命令。几何 verifier 独立于模型，并记录每次 rejected plan 的原因。

**第三：VGGT-GS SLAM 的在线标定可观性门控。** 不必先复现完整 3DGS，先在滑窗 VIO/BA 中加入 focal/distortion state，基于 Hessian condition / Fisher information 决定什么时候允许更新。这个思路对长期换温、震动、变焦相机很实用。

**第四：把 FAB-MAP 的“new-place hypothesis”带回现代 VPR。** 现有 Scan Context / DINO / learned descriptor 先负责召回，但不直接加 loop factor；再加概率门控与几何验证，重点测 catastrophic false loop，而不是只测 Recall@1。

## 参考资料

- [VGGT-GS SLAM: Uncalibrated Monocular Gaussian Splatting SLAM with Feed-Forward Priors](https://arxiv.org/abs/2609.19628)
- [RawSLAM](https://arxiv.org/abs/2609.20589)
- [Semantic SLAM in Precision Agriculture using Bayesian Inference](https://arxiv.org/abs/2609.20604)
- [Navigate or Relocate? Planning Among Movable Obstacles in Unknown Environments](https://arxiv.org/abs/2609.19541)
- [TADreamer: Zero-Shot Language-Guided 3D Navigation for Terrestrial-Aerial Bimodal Robots via Video Imagination](https://arxiv.org/abs/2609.19824)
- [Coding Agents with an Obstacle-Aware Harness for Safe Robot Manipulation](https://arxiv.org/abs/2609.20822)
- [UniExo](https://arxiv.org/abs/2609.19690)
- [Learning Slope-Adaptive Whole-Body Locomotion for Humanoid Robots in Roofing Construction](https://arxiv.org/abs/2609.20558)
- [GitHub: Agentic CLI customizations now in the usage metrics API](https://github.blog/changelog/2026-09-17-agentic-cli-customizations-now-in-the-usage-metrics-api/)
- [GitHub: Workflow execution protections in GitHub Actions generally available](https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/)
- [Claude Code Releases](https://github.com/anthropics/claude-code/releases)
- [Oxford Research Archive: FAB-MAP](https://ora.ox.ac.uk/objects/uuid%3A917f6474-bc02-4d6d-8f51-c8bd90b2bbb8)
- [FAB-MAP DOI](https://doi.org/10.1177/0278364908090961)
