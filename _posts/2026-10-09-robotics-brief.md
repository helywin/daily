---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-09"
date: 2026-10-09 09:00:00 +0800
description: "雷达—激光—相机无靶标联合标定、连续时间事件相机 VO、LLA-MPPI、风险触发重规划、Belief Space、机器人动作重定时、长上下文 WAM 与多子 Agent 并发实证。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-09

## 摘要

**检索基准：2026-10-09 09:00（Asia/Shanghai）。** arXiv Robotics 最新常规公开批次为 **2026-10-08，共 121 条**，Software Engineering 同日 **33 条**。先核查最近 24 小时的公开批次与开发工具更新，再扩展至最近 7 天；与截至 10 月 8 日的覆盖索引（927 条）按规范标题、arXiv ID、DOI、项目页和代码仓库联合去重。今天八条主动态均为未在索引出现的工作。其中多篇在 10 月 7 日 UTC 提交，但 10 月 8 日才进入常规列表；凡超过严格 24 小时的条目都标注**时间回补**。论文数字为作者报告，不视作跨平台可保证指标。

**SLAM 与标定。** 三传感器联合标定工作把雷达稀疏、虚警多的问题用距离相关噪声过滤和跨帧对应累积处理，且不再依赖两两标定结果简单相乘。事件相机立体 VO 则用连续时间 WNOA 高斯过程，在真实事件时间戳计算残差，优化变量只放在少量 keytime；MVSEC / DSEC 论文报告 22 / 6 Hz。它们分别给出了“多模态一致性”和“异步观测不用重采样成视频帧”的工程路线。

**控制与规划。** LLA-MPPI 在 GPU 上并行试运行候选接触动力学，在线根据过去窗口选择模型，Unitree Go2 展示了运行中加负载、腿部失效、推箱重量变化。CERT-Replan 不再把 CBF 当成无限纠偏器，而用 conformal 残差与尾部风险发现“当前规划模式本身已不安全”时主动换速度、走廊或绕行拓扑。Belief-Space Planning 则说明：估计器在自身信息条件下无偏，不代表对掌握更多信息的规划器仍无偏；只传协方差可能严重低估未来任务误差。

**机器人模型与执行。** RoboPace 不改 VLA/action-chunk 轨迹几何，只依据接触可能性和机器人动态极限在线改变执行速度。Long-WAM 则发现**历史长度不等于历史利用能力**：经自回归视频预训练的模型从 0 增加到 19.2 秒上下文时，在 RoboCasa GR-1 的成功率从 63.3% 升到 78.7%；但双向预训练初始化几乎没有收益。它在 RTX 5090 上每个包含未来视频 latent 预测的 action chunk 报告 107.4 ms。

**AI Coding。** 2,124 条执行轨迹的并发子 Agent 研究表明，动态并发是需要单独测试的执行策略：它带来并行收益，也产生上下文漂移、重复工作、冲突合并等新的失败类型。AI Coding 技巧今天选取 GitHub 10 月 8 日的 Draft PR 限额，以及 Claude Code 2.1.290 的权限 Hook 静态校验，均是可以直接实践的一手变化。

最新列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

## 1. 三传感器在线无靶标标定：不要把雷达—LiDAR—相机当成三组互不相关的两两标定

**时间回补：2026-10-03 14:35 UTC 首次提交；ICCAS 2026 接收。**

### 为什么重要

毫米波雷达在烟雾、弱光和粉尘下很有价值，但其点稀疏、存在多径与虚假回波。常规流程分别标定 Camera–LiDAR、Radar–LiDAR，再组合外参；然而三对外参的组合可能不一致，并且稀疏雷达对应导致标定抖动。这项工作直接联合优化 Radar、LiDAR、Camera 的外参，避免把两个单独看起来不错但整体不一致的结果接入融合系统。

### 算法模块、传感器假设

    Radar detections + LiDAR cloud + Camera
               ↓
    Radar 距离相关噪声边界过滤
               ↓
    多帧雷达对应积累
               ↓
    三对传感器联合残差
               ↓
    Joint nonlinear optimization
               ↓
    统一一致的外参集合

它不需要专门标定板，但需要有足够稳定的跨模态几何对应、合理的初始外参和动态物体处理；“无靶标”不等于零初始化或零运动要求。论文在自建城市道路雷达—激光—相机数据上报告三对传感器标定误差均有下降，摘要没有提供可统一推广的实时频率，不应夸大为开箱即用在线自动标定。

### 鲁棒性、可复现性与风险

距离越远，雷达量测散布与误关联的风险可能越高，因此作者采用 range-dependent margin；但这种 margin 仍受设备波束宽度、目标反射和多径影响。项目暂无可靠的成熟代码入口。工程验证应先标记每个约束的 inlier ratio、radar-range bins、pairwise transform cycle error、优化 Hessian 条件数和校准外参漂移速度。动态标定结果不能未经门控直接覆盖在线 SLAM 外参。

### 适合谁关注 / 工程落地启发

适合毫米波雷达 + MID360 / 多线雷达 + 相机平台、恶劣环境定位与无人机传感器冗余。产品中应存一份带版本号的传感器外参图，只有在跨帧几何一致性和闭环转换误差都达标后，才允许切换新外参。

[论文：Online Target-less Radar-LiDAR-Camera Extrinsic Calibration](https://arxiv.org/abs/2610.04552)

## 2. Event Stereo VO：连续时间估计不应把微秒事件硬压成图像帧

**时间回补：2026-10-01 23:55 UTC 首次提交；投稿 ICRA 2027。**

### 为什么重要

事件相机对高速飞行、强明暗交界的鲁棒性有潜力，但其真正优势是异步、微秒量级观测。先把事件堆成固定时间窗口的伪图像，等于提前抛弃了部分时间信息。逐个事件引入独立姿态又会把状态维数撑到无法实时求解。这篇工作用连续时间高斯过程回避两难。

### 算法模块、传感器与假设

    Stereo event stream（异步时间戳）
              ↓
    少量 Keytime Pose States
              ↓
    WNOA（white-noise-on-acceleration）轨迹先验
              ↓
    在每个事件原始时间戳做 GP 插值
              ↓
    事件立体几何观测残差
              ↓
    稀疏连续时间 VO

关键不是无限提高状态更新率，而是让状态数量跟 keytime 数量相关，观测却保持原始时间分辨率。WNOA 本身是运动平滑先验，对强碰撞、猛烈瞬态加速度和失真事件时间戳仍有建模偏差。

### 实时性、鲁棒性与结果

在 MVSEC 和 DSEC 上论文报告约 **22 Hz / 6 Hz** 实时更新，跨有效序列的 RMS 相对误差为 **0.46 cm** 与 **0.038°**；相对 ES-PTAM 对应误差约改善 11 倍和 15 倍，除一条测试序列外表现更好。数字来自指定 benchmark，不能理解为任意高速狭窄无人机都有厘米级全局定位。

### 可复现性与工程风险

目前论文提供视频和方法，但未看到明确完整源码。优先测试时间戳 jitter、事件噪声、低纹理静态区和相机同步偏差；实现时将 GP 插值开销与立体匹配开销分开 profile。与 FAST-LIO 的互补方向是把事件 VO 作为局部光学速度 / 相对运动证据，而非无条件替换 metric LIO。

### 适合谁关注 / 工程落地启发

适合高速无人机、强动态范围视觉定位、连续时间融合。最小实验是用同一事件数据比较固定窗口伪帧 VO 与 keytime-GP VO，控制相同运动先验和计算预算，明确收益究竟来自高时间分辨率还是额外平滑。

[论文：Real-time Event-camera Stereo Visual Odometry via Keytime GP Regression](https://arxiv.org/abs/2610.02601)

## 3. LLA-MPPI：GPU 模型库把整机四足控制变成在线物理假设选择

**时间回补：2026-10-07 17:30 UTC 首次提交。**

### 为什么重要

传统四足 Whole-Body Controller 依赖固定质量、摩擦、接触参数；突然携带重物、失去一条腿的有效支撑或推箱载荷变化，固定模型容易瞬间失效。LLA-MPPI 将“重新辨识未知模型”转成 GPU 上的多个接触仿真器并行评分，再让 MPPI 使用最新最佳解释模型继续优化。它与此前报道的 F1TENTH **LLA-MPC**、多模型安全滤波 **LBA-CBF** 属于同一研究路线，但本次是真正面向**接触丰富的全身控制**的新方法与新真机验证。

### 算法模块与动力学假设

    Recent states / controls
             ↓
    GPU batched contact simulators
    （不同质量、摩擦、接触 / 结构）
             ↓
    Look-back prediction residual
             ↓
    选择当前最可信模型
             ↓
    Look-ahead whole-body MPPI
             ↓
    Joint / whole-body commands

关键假设是候选库能够覆盖真实变化，模型选择窗口对动态变化足够敏感。与网络式 model identification 不同，选中的物理或结构假设仍可解释。

### 结果、实时性与鲁棒性

四个仿真任务中，论文报告 **97.5%** 成功率，最强对比方法 **74%**，知道真实模型的 oracle 为 **98.5%**。Go2 真机展示了**行走过程中临时增加负载、单腿失效后行走、推箱过程中箱体质量变化**。摘要未公开可普适移植的控制 Hz、显存与端到端 worst-case latency，不能据此直接断言 Jetson / RK3588 可等效运行。

### 可复现性与工程风险

作者提供代码和项目材料入口，但部署必须重视 GPU 仿真耗时、候选模型覆盖、contact solver 与真机摩擦失配。记录 model-ID 变化频率、look-back residual gap、foot slip、joint torque saturation、每周期最差 MPPI 时间。若所有候选残差都明显升高，应进入降速/保护状态，而不是让选出来的“相对最好模型”获得无限控制权。

### 适合谁关注 / 工程落地启发

适合有低层控制权的 Go2/自研四足。对只开放 vx/vy/wz 的第三方机器狗，可先把 model bank 降阶成“命令→机体速度 / 位移响应”并比较与纯 learned interface model 的预测误差；不要错误地照搬 whole-body controller 接管厂商关节控制。

[论文：LLA-MPPI](https://arxiv.org/abs/2610.10465) · [团队项目入口](https://lla-control.github.io/)

## 4. CERT-Replan：CBF 不应永远抢救一条已经不安全的规划路线

**时间回补：2026-10-07 02:02 UTC 首次提交。**

### 为什么重要

动态障碍预测在拥挤环境中会随时间漂移。最常见架构是固定 MPC 路径加 CBF，每次靠 Safety Filter 修正即将撞上的控制；但如果整条走廊或绕行类别已不可行，连续小动作投影只会让机器人反复停停走走、越修越被动。CERT-Replan 让规划器主动承认“当前规划模式失效”。

### 算法模块、概率假设与触发器

    动态障碍历史预测误差
             ↓
    在线 conformal calibration（按 horizon）
             ↓
    动态障碍安全 margin / Barrier loss
             ↓
    MPC rollout 上尾部 CVaR 风险
             ↓
    风险 > 配额：换速度 / 走廊 / homotopy class
             ↓
    下一控制仍经 one-step Safety Filter

它将“当前一步安全”和“未来一段时间内这条计划是否仍划算”分开。Conformal 误差半径依赖历史残差对当前非平稳环境仍有代表性；CVaR 风险预算的统计解释必须和在线校准条件一起看。

### 实验与工程风险

在论文非平稳 benchmark 上，相对仅安全过滤基线碰撞减少 **83.3%**，相对简单重规划触发减少 **77.8%**，Safety Filter 平均干预减少 **32.4%**。接入 Trajectron++ 后报告 **96%** 无碰撞运行，并有硬件实验和 onboard profiling；这些不等于形式化绝对不撞保证。

### 可复现性 / 工程落地启发

无需一开始重写 MPC。先给现有路径规划器增加 horizon-risk telemetry 和 plan-mode switch：观察未来障碍预测的高分位损失，在超过预算时主动改走廊或停车。记录 CVaR、预测误差分位、trigger reason、plan-switch count、最小障碍距离与实际 CBF 介入次数。

### 适合谁关注

动态障碍导航、UAV 窄走廊、MPPI/MPC、风险感知探索与机器人安全层。

[论文：Adaptive Risk-Certified Event-Triggered Replanning](https://arxiv.org/abs/2610.09302)

## 5. Planner-conditioned Estimator Error：SLAM 协方差未必是规划器真正面对的定位风险

**时间回补：2026-10-06 23:08 UTC 首次提交。**

### 为什么重要

常见 belief-space planner 从 EKF 读取状态均值和 covariance，然后假设误差零均值。问题是规划器知道**计划中的动作、场景、任务阶段**，而现成估计器未必能观测这些信息。估计器即使对自己的信息集无偏，对规划器已知的条件变量也可能产生系统性偏置。间歇观测被接收/拒绝时，两种情形的条件均值不同，进一步引入容易被普通 covariance propagation 漏掉的校正事件不确定性。

### 算法模块、估计假设

    Planner information + EKF / sensor mode
                ↓
    仿射估计误差状态动态
                ↓
    Correction accepted / rejected 条件均值
                ↓
    误差均值 + 协方差矩递推
                ↓
    Task-weighted quadratic risk
                ↓
    Receding-horizon belief-space action selection

论文采用明确的操作模式区间（regimes），不主张一个模型统管所有环境。

### 结果与边界

在倾转旋翼 VTOL 舰面降落仿真中，加入规划器条件信息后，command-blind EKF 的误差预测 loss 降低 **13.4%**。16 组匹配闭环实验里，终端 task gauge 中位数从 **1.60 降至 0.99**；超过 2 秒的估计误差预测在 **1.3 倍**内，而单靠协方差的规划低估达 **5.7 倍**。样本规模仍小，且尚无真实舰载飞行验证。

### 可复现性、鲁棒性与工程落地启发

最值得先做的是在自有 SLAM 回放上记录“规划器看来应该发生什么”和“估计器实际接受了哪些观测”的差异。建立按楼梯/长走廊/遮挡分区的条件误差均值和协方差，再比较只用 Hessian covariance 与条件风险规划。注意评测目标必须是未来真实估计误差，不要把 estimator 自己报告的 covariance 当作 ground truth。

### 适合谁关注

VIO/LIO 与规划紧耦合、无人机降落、GNSS 断续、雷达退化定位、risk-aware MPC。

[论文：Belief-Space Planning with Planner-Conditioned Estimator Error](https://arxiv.org/abs/2610.09207)

## 6. RoboPace：VLA 的几何动作可保留，但接触阶段不能直接继承人类示范的速度

**时间回补：2026-10-07 08:55 UTC 首次提交。**

### 为什么重要

UMI / 人类双手演示数据正在降低机器人模仿学习门槛，但人的软组织和柔顺手指能快速撞上物体，机器人关节跟踪延迟和刚性接触却不允许同样速度；反过来机器人空载移动又完全可以比人类更快。若将一个 action chunk 简单整体加速，会在接触附近失败；始终整体减速又极大浪费时间。

### 算法模块与动力学假设

    VLA / UMI 预测的几何动作路径
              ↓
    预测路径上的接触阶段
              ↓
    Contact-dependent speed limits
    + 机器人运动学 / 动力学限制
              ↓
    在线 time-optimal retiming
              ↓
    不改路径，只改沿路径的时间参数

这不需要重训 base policy。它假设既有几何路径本身可行，接触预测足够可靠；若几何路径穿模或目标物已移动，仅重定时无法救回来。

### 结果、实时性与风险

三项接触丰富的双臂任务中，统一高速和仅考虑物理极限的重定时普遍失败；RoboPace 则在保持慢速执行可靠性的同时，**五种指令中的四种用大约一半时间完成**，整体成功表现高于统一慢速方案。作者报告实时运行，未在摘要给出统一 Hz。

应记录 contact_prediction_confidence、near-contact slowdown、trajectory tracking error、joint saturation 和触碰力度。如果接触判别错误，重定时器可能在真正接触前未及时减速。

### 可复现性 / 适合谁关注 / 工程落地启发

适合 UMI、双臂 VLA、机器人操作和任何已有 action chunk 的执行器。先对同一策略尝试 uniform slow、uniform fast、contact-aware retiming 三种执行模式；固定硬件与轨迹几何，比较 success、完成时间和最大接触力。

[论文：RoboPace](https://arxiv.org/abs/2610.09696) · [项目页](https://robopace.airoa.io/)

## 7. Long-WAM：长上下文有效的前提，是视频基础模型预训练时真正学会了因果时间

**时间回补：2026-10-07 17:58 UTC 首次提交。**

### 为什么重要

World-Action Model 很容易被视频帧历史带来的 token 和时延拖垮；然而粗暴减少历史会让动态任务缺少速度、进度和对象状态线索。Long-WAM 比较的不是“长上下文有没有用”，而是**什么视频预训练机制允许后续动作模型真正利用更长历史**。

### 算法模块、部署结构与假设

    Robot / Egocentric 视频（可无 action 标签）
                  ↓
    自回归 AR 未来视频预训练
                  ↓
    Causal World-Action Adaptation
                  ↓
    Streaming Observation Encoding
    + Asynchronous Action Execution
    + Hardware-Specific Acceleration
                  ↓
    Future-video latent + Action chunk

模型保留历史→未来因果结构；仅扩大一个双向预训练模型的输入窗口，不必然换来更好的动作。

### 实验结果与实时性

RoboCasa GR-1 上历史从 **0 秒扩到 19.2 秒**，成功率 **63.3%→78.7%**；双向预训练初始化没有对应净收益。作者在 LIBERO-Long、RoboTwin 2.0、DOMINO 报告领先的对比结果；RTX 5090 上包含 future video latent 预测的每个 action chunk **107.4 ms**，并展示 DGX Spark / Jetson AGX Thor 部署。G1 与 YAM 真实动态操作中，dynamic cup stacking 达 **95%**，对比的两种策略在 20 次测试中均无成功。

### 鲁棒性、可复现性与工程风险

长历史对 camera/robot embodiment 变化、历史状态版本和视频缓存 age 非常敏感。需要记录有效可见历史秒数、token 缓存命中、observation-to-action latency、async command age 与 rollout 安全回退。项目主要以原论文和演示为依据，不把模型权重/全套训练流程认定为已经全部开源。

### 适合谁关注 / 工程落地启发

适合 WAM、VLA、G1/YAM、Jetson/RTX 边缘推理和长操作任务。一个可执行的 A/B 是固定主模型参数和 action space，比较 AR 与 bidirectional pretraining 的 0/4/8/19.2s 上下文曲线；单独 profile 流式编码和动作推理，避免“实验里看了 20 秒”实际只重复利用旧帧。

[论文：Long-WAM](https://arxiv.org/abs/2610.10528)

## 8. 多子 Agent 动态并发：不是启动越多 Agent 越快，调度策略本身决定成功率

**时间回补：2026-10-07 15:35 UTC 首次提交。**

### 突破性工程价值

长时间 Coding Agent 会在任务中动态分派搜索、重构、测试、审查等子 Agent，看起来天然可以并发提速。但每个 agent 的文件状态、工作树、测试环境、输入上下文和终止条件都可能变得不同。固定多 Agent 组织与运行时由模型随时 spawn 的并发策略，其失败机理不同。

### 实验设计与结果

研究使用 Codex、Claude Code、Kimi Code 的匹配执行，比较 dynamic concurrency **启用与禁用**，覆盖 **354 个任务、2,124 条执行轨迹**。作者整理出 **13 种并发特有失败模式**及 **28 种可观察行为模式**，系统分析不同任务规模和执行长度下，何时并发带来优势。摘要没有提供跨模型统一“快 N 倍”或“成功率 +N%”的可靠总数字，因此不能把动态并发包装成必然收益。

### 实际 Harness 怎么改

    Main agent
      ├─ Read-only search agent
      ├─ Isolated worktree implementer
      └─ Test/review agent
             ↓
    Explicit ownership / join barrier
             ↓
    Integration test
             ↓
    Final receipt

每个子 Agent 要有明确文件所有权、最大预算、输入 SHA、完成证据和 join barrier；整合前检查工作树版本以及是否重复修改同一文件。对于共享数据库、生成代码、测试 fixture，尽量只允许一个 writer。

### 安全、可验证性与工程风险

并发产生的危险不只是不小心覆盖源码，还包括工具权限被子 Agent 扩散、重复执行外部副作用、错误摘要污染主 Agent 判断。必须将每个子任务的 token、wall-clock、文件冲突数、无意义重复读和最终真实测试记录成独立 telemetry。

### 适合谁关注 / 工程落地启发

适合 Codex / Claude Code 大仓库、多代理自动重构、复杂 C++/Java/ROS2 项目。推荐先做静态二 Agent 与动态并发同任务 A/B，而不是在生产大仓库立刻无上限并发。

[论文：When Sub-Agents Work in Parallel](https://arxiv.org/abs/2610.10263)

## AI Coding 实战技巧精选

### 技巧 1｜让 GitHub 的 Draft PR 也计入限额，限制 Agent 批量堆积草稿

- **来源**：GitHub 官方 Changelog，2026-10-08，[Draft pull requests count toward pull request limits](https://github.blog/changelog/2026-10-08-draft-pull-requests-count-toward-pull-request-limits/)。
- **一句话结论**：如果已经给仓库设定每位贡献者的 PR 数量限制，现在可以把 draft 一起计入，防止 Coding Agent 用无限草稿绕开限额。
- **具体怎么做**：
  1. 在仓库现有 Pull Request 限额配置中启用“Draft PR 计入限额”（具体设置入口以仓库当前界面为准）。
  2. 用测试账号依次创建普通 PR 和 Draft PR，检查二者是否合计占用同一用户额度。
  3. 配合 Agent 自身的“每任务一 PR、失败时复用同一 Draft”策略；超额不应自动换账号绕过治理。
- **适合什么场景**：GitHub、Copilot Cloud Agent、Codex / Claude 自动提 PR 的企业仓库。
- **注意**：这只是仓库贡献入口限流，不能取代分支保护或防止既有 Draft 内的危险代码变更。

### 技巧 2｜用 Claude Code 2.1.290 的 gatingHooks 报告检查高权限 Hook 是否具备异常处理

- **来源**：Anthropic [Claude Code v2.1.290 Release](https://github.com/anthropics/claude-code/releases/tag/v2.1.290)，2026-10-05。
- **一句话结论**：Claude Code 的 Mod/Plugin Hook 可能卡在权限检查、工具审批等 gating site。新版本在 JSON 校验结果中列出相关 Hook 是否带 .catch；将它纳入插件上线前检查。
- **具体怎么做**：
  1. 升级到 v2.1.290 或更新版本，在插件工程中运行 **claude plugin validate** 并启用该命令的 JSON 输出模式。
  2. 从返回 JSON 的 **gatingHooks** 读取每个 gating Hook 是否包含 .catch；对缺失的 Hook 补上失败处理并执行模拟超时/拒绝测试。
  3. 如果是企业插件，再用普通 Agent 与 subagent 分别触发审批；新版 tool.check 的 **agentId** 与 **ceiling** 可用于区分执行者和组织审批上限。
- **适合什么场景**：Claude Code Mods、MCP、企业权限 Hook、带 Shell 权限的长期 Agent。
- **注意**：检测到 .catch 不等于逻辑安全；还需检查出错时是 fail-open 还是 fail-closed，并用真实 sandbox/权限规则回归。

## 经典论文回顾

### Exactly Sparse Continuous-Time GP：在任意测量时刻估计状态，而不为每次观测新开状态节点

2014 年 RSS 的 **Batch Continuous-Time Trajectory Estimation as Exactly Sparse Gaussian Process Regression**（Barfoot、Tong、Särkkä）是连续时间轨迹估计的重要奠基工作；随后 Anderson、Barfoot、Tong、Särkkä 的扩展预印本 **Batch Nonlinear Continuous-Time Trajectory Estimation as Exactly Sparse Gaussian Process Regression** 于 2014-12-01 提交 arXiv。不要将这两篇标题和作者顺序混为一谈。

### 当年的核心问题

异步相机、LiDAR、IMU 和事件数据每个传感器都有自己的测量时刻。若把连续轨迹强行等频离散成节点，频率高则状态巨大，频率低又让异步测量需要粗糙插值。

作者改从随机微分方程驱动的**连续时间高斯过程**表达轨迹，在少量 support state 上优化，并可以向任意观测时间戳插值。

### 数学与算法结构

    Continuous-time stochastic dynamics
      └─ 白噪声驱动 GP prior
             ↓
    Sparse support states / Markov structure
             ↓
    Exactly sparse inverse kernel
    （block tridiagonal）
             ↓
    Measurement at arbitrary timestamp
             ↓
    GP interpolation + batch smoothing

对于所述线性时变 SDE 类先验，逆核矩阵是精确稀疏的，不必构造稠密核再硬截断。线性先验和线性测量模型下，它与经典离散平滑在测量点处等价；存在非线性时执行迭代优化。

### 当年为何重要、今天哪里仍然有效

这让连续时间估计不再必然意味着“每个异步观测都新增独立姿态变量”。今天滚动快门、事件相机 VO、运动畸变 LiDAR 去畸变、时空传感器标定仍然需要同一思想。今天的 Keytime GP Event Stereo VO 正是沿着“压缩 keytime 状态数但保留观测真实时间”的方向继续改进。

### 传感器、假设与局限

它是状态估计数学表示，不限定传感器。真正依赖的是运动先验、噪声模型与可观测性；强接触碰撞、不连续运动或传感器时戳漂移会破坏平滑先验。后来出现更多 Lie-group GP、spline-based continuous-time LIO、局部增量平滑等方案，连续时间 GP 也不能替代全局回环和鲁棒数据关联。

### 公开资料与可复现性 / 项目重新解读

先搭一条已知解析轨迹，采样不等频 IMU / 相机 / LiDAR 事件，比较离散线性插值、keytime GP 和高密度节点的误差、CPU、状态维数与时间戳扰动敏感性。再接入真实多雷达平台，比较同步后点云 deskew 与 continuous-time 观测建模的残差。重点看 **时间戳、外参和噪声模型的正确性**，不是单纯追求更密集的时间节点。

[RSS 2014 原始会议论文](https://www.roboticsproceedings.org/rss10/p01.html) · [2014 扩展预印本](https://arxiv.org/abs/1412.0630) · [RSS DOI](https://doi.org/10.15607/RSS.2014.X.001)

## 今日结论

今天最有价值的系统趋势是：**让多传感器误差、模型不确定性、接触风险和多 Agent 并发代价真正进入系统状态，不让某个主模型靠“更自信”吞掉它们。**

雷达—LiDAR—相机联合标定与连续时间事件 VO，分别强调空间一致性和时间一致性；若两者做错，再强的后端 SLAM 也只是在优化错误观测。Belief-space 规划则指出，估计器对自己的误差描述并不天然满足规划的条件信息要求，因此长走廊、间歇 RTK 或室内 UAV 可以考虑学习“任务条件下的真实定位误差”。

控制侧，LLA-MPPI 允许物理模型假设随着真实接触变化而切换；CERT-Replan 允许规划路线本身被拒绝；RoboPace 只改动作执行的时间轴，不随意修改已经学到的几何意图。这三种做法分别把模型、路线和速度变成能够被独立验证的可替换层。

Long-WAM 告诉我们，长历史有用的前提是模型已经学会因果利用历史；而并发 Coding Agent 的研究告诉我们，更多工作者不等于更高产出，最终要看共享状态是否一致、隔离是否合理、结果是否真正验证。

**工程上应优先把“不可信的中间状态”显式化，让系统有机会降权、重标定、重规划或停止，而不是等错误积累到最后才让大模型补救。**

## 最值得深入研究或尝试复现的方向

1. **Radar–LiDAR–Camera 三角一致性审计**：记录雷达距离 bins 与 pairwise cycle residual，先在离线 bag 上测试多帧对应累积，再允许更新真机外参。
2. **连续时间事件 / LiDAR 时间建模基线**：按原生 timestamp 插值状态，用相同时间预算与伪帧或固定频率 VO 对比。
3. **Go2 模型库适配分层**：若仅有 vx/vy/vw，用速度响应模型替代接触全身模型；若有 WBC 执行权，再研究 LLA-MPPI 全结构。
4. **MPC 风险触发换路**：保留 one-step CBF，增加 horizon CVaR 和 conformal 残差记录，专门测连续介入但不换路的失败案例。
5. **Planner-conditioned SLAM 误差校准**：按长走廊、转角和观测丢失状态，拟合条件偏差和误差方差，与只使用 covariance 的规划比较真实越界率。
6. **Action-Chunk 在线重定时**：固定 VLA 输出的几何动作，分别测 uniform slow / fast / contact-aware 的执行成功率与接触冲击。
7. **WAM 历史真正利用率**：保持推理预算固定，做不同预训练与历史长度的消融，并记录数据缓存带来的真实延迟。
8. **多 Agent 并发治理**：对子任务设置 owner、worktree、join、独立测试与外部副作用权限，再对 10 个真实工程任务比较串行和动态 spawn。
9. **高权限 Claude Hook 回归**：在插件发布前解析 gatingHooks，跑拒绝、超时和缺失依赖场景，确认 fail-closed。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [Radar–LiDAR–Camera Online Target-less Calibration](https://arxiv.org/abs/2610.04552)
- [Event Stereo VO via Keytime GP](https://arxiv.org/abs/2610.02601)
- [LLA-MPPI](https://arxiv.org/abs/2610.10465)
- [CERT-Replan](https://arxiv.org/abs/2610.09302)
- [Planner-conditioned Belief-Space Planning](https://arxiv.org/abs/2610.09207)
- [RoboPace](https://arxiv.org/abs/2610.09696)
- [Long-WAM](https://arxiv.org/abs/2610.10528)
- [When Sub-Agents Work in Parallel](https://arxiv.org/abs/2610.10263)
- [GitHub Draft PR Limits](https://github.blog/changelog/2026-10-08-draft-pull-requests-count-toward-pull-request-limits/)
- [Claude Code v2.1.290](https://github.com/anthropics/claude-code/releases/tag/v2.1.290)
- [RSS 2014 Continuous-Time GP](https://www.roboticsproceedings.org/rss10/p01.html)
- [Expanded Sparse Continuous-Time GP](https://arxiv.org/abs/1412.0630)
