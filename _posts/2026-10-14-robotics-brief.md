---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-14"
date: 2026-10-14 09:00:00 +0800
description: "视觉与Wi-Fi融合源目标导航、杂乱场景最小障碍移除、世界模型动力学采样规划、人形接触优先级和身体接触示教、航空操作Coding Agent主动诊断、LeWAM及Agent修改部署配置的治理。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-14

## 摘要

**检索基准：2026-10-14 09:00（Asia/Shanghai）。** 本次重新核验的 arXiv 页面显示，Robotics 的最新可见 new 列表为 **2026-10-12 批次，共 132 条（72 条新投稿）**；Software Engineering 为同日 **41 条（18 条新投稿）**。先核查最近 24 小时的一手技术公告，再扩展到最近七天论文；与 GitHub 截至 2026-10-13 的 **983 条覆盖索引**以规范标题、arXiv ID、DOI、项目主页和 GitHub 地址联合去重。本期八项研究均未被收录过。论文首次提交于 2026-10-08 或 10-09 UTC，因此全部标为**时间回补**，不把 10 月 12 日的公开批次误认为初次提交日。[Robotics 最新列表](https://arxiv.org/list/cs.RO/new) · [Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)。

**定位与导航**：ViFiNav 在不接入目标设备网络、不改现场基础设施的情况下，被动监听 Wi-Fi 包，使用机器人运动累积信号源方向观测，再与深度图融合导航。这不是用 RSSI 替代 SLAM，而是把“信号源在哪里”的概率估计交给上层目标搜索。最新批次里没有足以压过已经覆盖论文的全新 LiDAR-SLAM 架构，本期不为凑数重复旧 LIO。

**规划与控制**：Minimum Constraint Removal 不再把被箱子堵死的通道简单判为无解，而计算最少需移走哪些障碍；Sampling-based Kinodynamic Planning with World Models 把 RRT/KPIECE 的非局部探索引入世界模型潜空间，在作者实验中较 CEM/MPPI 最多快 13.8 倍，真机推块任务成功率提高约 20%。

**人形技能**：PriMoRetarget 用显式优先级保证足底和操作接触不被姿态模仿的低优先级目标破坏；PanTact 利用人类身体接触贴片记录接触时空目标，在无需为 Unitree G1 额外安装身体接触传感器的情况下实现身体支撑、推动与载荷分担。

**机器人基础模型与 Coding Agent**：Fly-by-Code 让 Agent 生成 View/Probe 诊断程序，从仿真中主动收集先前看不到的故障证据；六个空中操作任务的成功率由 31.7% 提升至 75%。LeWAM 把 JEPA 潜状态预测与动作 Flow Matching 联合训练，作者报告接触丰富任务成功率由 28.6% 至 89.7%，规划加速 32.3 倍。

**研发治理**：一项研究分析 26,999 个 PR，发现同时改动业务代码和部署基础设施的 AI Agent PR 虽仅约 4.5%，却出现审核拖延与缺少人工审核两极结果。实战技巧关注 GitHub 2026-10-13 发布的 Copilot 企业策略刷新、Code Quality finding 审计和 GitHub App 权限最小化。经典回顾选择 ICRA 2000 的 RRT-Connect，分析双向搜索与今天世界模型树规划的联系。

## 1. ViFiNav：Wi-Fi 定位信号源，深度相机判断真实可通行性

**时间回补：v1 2026-10-08 21:28 UTC。**

### 为什么重要

寻找打印机、路由器、无线标签和智能设备时，目标可能被遮挡、难以视觉区分。无线信号有助于回答“设备大致在哪个方向”，但建筑多径会让单次方向观测产生偏差。ViFiNav 将机器人自身运动变成消歧工具：在多个位姿上积累目标 Wi-Fi 方向信息，形成带置信度的源位置估计，并让深度相机提供可通行几何条件。（[论文](https://arxiv.org/abs/2610.12733)）

### 算法模块与传感器假设

    Wi-Fi packets + 机载天线阵列
                    ↓
        Bearing / multipath observations
                    ↓
           多位姿源位置估计
                    +
                Depth camera
                    ↓
             ViFiNav policy
                    ↓
          Move → observe → update

作者提供 WiFiSpaces，将在线射线追踪 Wi-Fi 感知整合到 Habitat，使训练时的观测能随机器人连续位姿改变。真实机器人使用普通路由器改造的 Wi-Fi 传感器，不需要加入目标无线网络。该方法需要稳定的机器人自身位姿、天线阵列标定和信号源身份关联；多设备共信道、强反射和源移动仍可能造成多个位置假设。

### 实时性、鲁棒性、可复现性

作者报告零样本迁移到未见场景数据，并在真实机器人上无需真实数据训练地完成部署；论文摘要没有可普遍迁移的 Hz 或绝对位置 RMSE。源定位并不等于连续 odometry，不能取代 FAST-LIO/VIO 的高频里程计。

目前没有确认可直接复现的完整官方代码。可先在现有 LiDAR 位姿上做多方位 Wi-Fi Bearing 融合，分析不同运动基线、穿墙、多径下的位置协方差，再接上层搜索规划。

### 工程风险、适合谁与落地启发

适合室内巡检与联网设备查找。建议输出 source_id、bearing_confidence、source_covariance、packet_age、pose_revision；只将 Wi-Fi 信念作为搜索先验，碰撞安全仍由真实 LiDAR/Depth 和局部控制器负责，并遵守无线监听的法律与隐私要求。

[原论文](https://arxiv.org/abs/2610.12733)

## 2. Minimum Constraint Removal：没路时先计算最少要搬走哪些障碍

**时间回补：v1 2026-10-08 18:30 UTC。**

### 为什么重要

仓库、医院和居家机器人遇到箱子或椅子堵路时，传统路径规划通常返回 infeasible；若允许移走少量物体，任务可能重新可达。寻找最少需移除障碍的集合是 NP-hard 的 Minimum Constraint Removal（MCR）问题。本论文将双向可行集合生成、简化 MCR 图与定长搜索组合，避免直接枚举全部障碍子集。（[论文](https://arxiv.org/abs/2610.12609)）

### 算法模块与动力学假设

    Start/Goal + 静态与可移动障碍
                    ↓
           双向可行集合生成
                    ↓
            Reduced MCR Graph
                    ↓
                定长搜索
                    ↓
         待移除对象 + 可行几何路径
                    ↓
          任务规划器验证移除动作

只有知道物体可被移动还不够：其重量、抓取面、移动权限、落点和碰撞空间都可能使理论上的“最小移除集合”物理上不可执行。该方法主要提供几何/组合搜索，不能单独证明操作机器人能够移除目标。

### 结果、鲁棒性与可复现性

六组 benchmark 中，三组匹配精确最优；其余最多多移除 31.25% 的障碍，求解较精确基线快 3.4–33.7 倍。一个杂乱操作场景由移除七个障碍改成两个，使 MCR+IK+规划总时间由 84.72 秒降至 30.59 秒。该结果属于任务级搜索，不代表低层控制频率。当前未见可确认的官方完整源码。

### 工程落地启发与适合谁

适合仓库 AMR、整理环境的移动机械臂、人形通行。最小产品化方案：为对象增加 movable、graspable、mass_estimate、permission、last_verified 字段，仅在常规全局规划无解时启用 MCR；规划输出移除集后必须再次经过 manipulation feasibility gate。

[原论文](https://arxiv.org/abs/2610.12609)

## 3. World-Model Kinodynamic Planning：RRT/KPIECE 帮世界模型跨越局部奖励陷阱

**时间回补：v1 2026-10-09 03:01 UTC；论文注明投稿 ICRA 2027。**

### 为什么重要

视觉世界模型可以预测动作后果，但用 CEM/MPPI 逐轮优化轨迹时，短期评分可能不奖励“先绕到箱子背后、再把箱子推向目标”这种必要的阶段。论文采用 RRT 和 KPIECE 在世界模型潜空间开展树搜索，利用模型作为 latent state propagator，使规划器能探索暂时距离目标更远、最终却更有效的中间状态。（[论文](https://arxiv.org/abs/2610.12910)）

### 算法模块和动力学假设

    Current image → DINO-WM latent
                    ↓
        RRT nearest-neighbor / KPIECE
                    ↓
           GPU batched expansion
                    ↓
          Predicted latent successor
                    ↓
       Goal test → action sequence

RRT 更偏向最近节点的空间扩展，KPIECE 借投影空间覆盖控制探索；两者都要求潜空间中距离与覆盖度有一定规划意义。世界模型 rollout 越长，预测误差越会积累，不能把“模型预测可达”当作现实中的安全可达。

### 实验、实时性、可复现性与风险

作者在四个仿真任务和真实推块实验使用现成 DINO-WM，报告成功率匹配或超过 CEM/MPPI，仿真规划耗时最多减少 13.8 倍，真实推块成功率提高约 20%。数值是指定模型与算力上的结果，不意味着所有长时任务都能同等加速。当前未确认完整官方代码入口。

### 适合谁关注与工程落地启发

适合视觉操作、移动操作和 WAM 规划。固定同一 world-model predictor、GPU 预算与安全约束，A/B 比较 CEM/MPPI、latent RRT、KPIECE，重点记录实际轨迹可行性、latent prediction drift、sample utilization 和最坏规划延迟。**预测器和搜索器应分开进行归因评测。**

[原论文](https://arxiv.org/abs/2610.12910)

## 4. PriMoRetarget：接触优先级应是硬层级，而非任意可交换奖励

**时间回补：v1 2026-10-08 19:03 UTC。**

### 为什么重要

人形动作重定向必须同时匹配脚底位置、抓持接触、对象关系、身体姿态及机器人关节范围。常见加权损失存在隐性风险：姿态权重足够大时，优化器可以为“动作像人”而损失真正决定任务成功的接触。

PriMoRetarget 采用显式优先级：先满足关键的落足与交互接触，再在不破坏高优先级条件的可行自由度上优化下一级姿态目标。（[论文](https://arxiv.org/abs/2610.12642)）

### 算法模块与假设

    Human + Object + Contact reference
                    ↓
          High-priority constraints
          foot placement / contacts
                    ↓
         Lower-priority pose objectives
                    ↓
             Retargeted motion
                    ↓
                Tracker / WBC

优先级并不意味着不存在冲突。如果两个接触目标在当前机器人本体上无法同时实现，优化器需要明确报告 infeasible，而非悄悄把误差传给低层控制器。机器人真实关节限制、接触力和摩擦仍需后续物理校验。

### 结果、鲁棒性与可复现性

作者在单人、人—物、人—人互动的四个数据集报告更好的任务关键接触保持和参考轨迹可追踪性；摘要没有给出统一真机控制 Hz 或具体可部署的代码入口。当前不能声称完整开源。

### 适合谁关注与工程落地启发

适合 G1、人形技能迁移、复杂接触数据生成。将 contact_set、priority_level、constraint_residual、tracking_feasibility 作为训练轨迹元数据；数据导出前先检查高优先级接触，不要只以平均 joint error 筛选“好轨迹”。

[原论文](https://arxiv.org/abs/2610.12642)

## 5. PanTact：用人体接触贴片教会机器人非手部操作

**时间回补：v1 2026-10-08 18:00 UTC。**

### 为什么重要

人类搬重物会使用肘、肩、躯干、身体重量支撑物体，而很多机器人模仿学习数据只记录手和夹爪，缺失全身接触的时空信息。PanTact 使用可穿戴身体接触贴片、第一视角视觉和双手 UMI 装置，在不需要真实机器人参与示范的情况下采集接触事件；上层策略预测接触目标，低层全身控制器决定如何由机器人身体表面实现。（[论文](https://arxiv.org/abs/2610.12558)，[项目页](https://pantact.github.io/)）

### 算法模块与传感器假设

    Ego video + Hand UMI + Body contact patches
                    ↓
            Whole-body contact goals
                    ↓
             Visuomotor policy
                    ↓
           Contact-aware Whole-Body Control
                    ↓
               Unitree G1

论文在没有为 G1 额外安装身体接触传感器的条件下演示支撑、推动、扫移和分担载荷；这不意味着无需身体几何、机器人力矩反馈或碰撞建模。采集端的人体接触贴片与部署端的机器人配置是两个不同问题。

### 实时性、鲁棒性与可复现性

作者摘要强调真机可行性演示，未给出可跨平台的统一 FPS/成功率；项目页存在，代码/数据开放完整性尚待核验。接触迁移依赖对象刚性、摩擦、承压表面、人与机器人尺寸差异，不能直接将人体胸部支撑轨迹复读到机器人执行器。

### 适合谁关注与工程落地启发

适合人形全身操作、搬运数据工厂和接触技能训练。建议使用 contact_surface_id、object_id、start/end_time、force_limit、friction_confidence、human_clearance 明确记录接触与限制，外部安全层限制肩、头、躯干可能产生的危险碰撞。

[原论文](https://arxiv.org/abs/2610.12558) · [项目页](https://pantact.github.io/)

## 6. Fly-by-Code：Coding Agent 无法诊断失败时，主动生成新的物理证据

**时间回补：v1 2026-10-08 18:00 UTC。**

### 突破性工程价值

Agent 根据自然语言生成机器人任务程序后，经常只看执行终端状态与现有相机画面继续改代码。但无人机载荷限制导致关键位置不在视野内，操作动力学耦合又可能让不同故障有相同表面征象。仅让模型重复阅读相同日志无法恢复从未采集的证据。

Fly-by-Code 为此设计 Active Feedback：当结果或故障原因仍不确定，Agent 在**仿真中**生成诊断程序。View 选择有信息量的新视角检查未知结果，Probe 执行有针对性的模拟物理交互，区分互相竞争的失败假设。（[论文](https://arxiv.org/abs/2610.12549)，[项目页](https://fly-by-code.github.io/)）

### 算法模块

    Task program → execution feedback
                    ↓
           unresolved question?
                 /         \
             View          Probe
                 \         /
          diagnostic simulation
                    ↓
           evidence-backed revision
                    ↓
             verify completion

### 结果、可复现性与安全风险

在六个模拟空中操作任务、每条件 60 次试验中，错误宣布完成数从 25 下降到 5，任务成功率从 31.7% 提高到 75%。作者用共享机器人 API 将仿真修订程序部署到真实空中操作机器人完成多阶段操作，无需更改任务程序源代码。项目页可用，但不能凭页面判定完整源代码/硬件配置已一键开放。

真实机器人上的 Probe 可能造成物理风险，必须限制在仿真或明确授权的低风险测试内。建议将 diagnostic_question、missing_evidence、diagnostic_program_sha、simulation_outcome、completion_receipt 做成独立工件；任何“任务已完成”都要有独立可验证条件，而不是只取 Agent 自述。

### 适合谁关注与工程落地启发

适合无人机操作、机器人自动程序生成、长任务 Agent。软件开发也能复用同样思路：当 CI 日志无法定位 Bug 时，先生成能区分多种假设的最小测试，再修改代码，而非反复盲猜。

[原论文](https://arxiv.org/abs/2610.12549) · [项目页](https://fly-by-code.github.io/)

## 7. LeWAM：让 JEPA 同时为未来预测与真实动作决策优化

**时间回补：v1 2026-10-08 23:58 UTC。**

### 为什么重要

视觉 JEPA 可以学习紧凑未来潜状态，但常见流程先做 representation，再训练 dynamics，最后再配 policy，容易产生对视觉相似性有用、却对接触与控制不充分的表征。

LeWAM 采用一个联合目标训练 next-latent prediction 与 action flow matching，并对 latent state 加 isotropic Gaussian 约束，形成同一模型既输出动作，也通过潜状态转移给候选动作评分的结构。（[论文](https://arxiv.org/abs/2610.12818)，[项目页](https://le-wam.github.io/)）

### 算法模块与动力学假设

    Observation latent + task
                    ↓
        Joint JEPA + Action Flow Training
                    ↓
         Gaussian-constrained latent
                    ↓
      Direct policy / sampled action planner

潜空间预测避免昂贵的逐帧视频重建，但它并不自动学习真实接触力、摩擦系数，也可能遗漏对安全有意义的局部视觉细节。Gaussian 正则项是训练与规划的表示约束，不等于真实动作后验始终高斯。

### 结果、实时性和可复现性

作者报告，相较已有视觉规划 JEPA，接触丰富任务成功率由 28.6% 至 89.7%，长时任务由 10.9% 至 46.2%，规划加速 32.3 倍；行为克隆实验还覆盖仿真和真实机器人。这些对比来自特定 benchmark，不能直接视为统一的端侧毫秒数。项目页已经发布，未确认全部训练及权重入口。

### 适合谁关注与工程落地启发

适合 VLA/WAM、机械臂世界模型和端侧规划。建议固定视觉编码器、训练数据与算力，比较 staged JEPA+policy 与 joint JEPA+flow；将 world_prediction_error、action_success、planning_walltime、safety_filter_intervention 分别记录，避免用更好看的 latent 代替真实动作验收。

[原论文](https://arxiv.org/abs/2610.12818) · [项目页](https://le-wam.github.io/)

## 8. Agent 同时改业务代码与部署配置：四点五个百分点的小类别，隐藏不同级别的审查风险

**时间回补：v1 2026-10-09 01:16 UTC。**

### 突破性工程价值

Coding Agent 常在本地沙盒和同步单测上被评估，而实际发布需要 CI、Docker、Kubernetes、Terraform、数据库迁移与环境变量协同。修改应用代码与部署基础设施的 dual-scope PR 有异步发布副作用，测试代码通过不能直接证明部署安全。

研究使用 AIDev v5 与 MOSAIC-3M 的 **26,999 个 PR**，覆盖六类 Agent 架构及匹配人类基线，通过文件分类和条件匹配来比较双范围 PR 的集成后果。（[论文](https://arxiv.org/abs/2610.12849)）

### 关键结果与局限

Dual-scope 只占 Agent PR 的 **4.48%–4.55%**，但出现明显两种情况：明确进入人工审核的 PR 中位额外等待 **13.13 小时**，time-to-merge 为 **3.24 倍**；另一种路径中，**43.1%–56.2%** 的 dual-scope PR 未经过人工检查便合入，中位不到 31 分钟。

这是指定样本和匹配方法下的观察，不代表任何团队都有同等比例，也不能把匹配分析视为完全消除所有混杂的随机试验。

### 真实流程、权限、安全与可验证性

应按文件范围分类 PR：application_only、workflow_change、deployment_change、database_migration、secret_surface。默认只授权 Coding Agent 修改应用目录；当 PR 触及 .github/workflows、helm、infra 或数据库迁移时，强制对应 CODEOWNERS、CI dry-run 和发布环境审核。

验证应冻结 input SHA、记录工具轨迹与变更文件，分别审查 App 和 IaC，完成部署验证后才允许合并。不要让 Agent 自己修改它需要通过的 GitHub Actions 验证逻辑。

### 适合谁关注与工程落地启发

适合 Codex、Claude Code、Copilot 自动 PR、公司 monorepo 和复杂 CI/CD。建议抽取最近 100 个 Agent PR，按 dual-scope 分组比较人工审核率、merge 延迟、部署失败与回滚成本。论文给出详细实证方法，当前未核实完整官方代码数据仓库。

[原论文](https://arxiv.org/abs/2610.12849)

## AI Coding 实战技巧精选

### 技巧 1｜让 Copilot 启动时强制刷新托管策略，阻断旧权限缓存

- **来源**：GitHub 官方，2026-10-13，[公告](https://github.blog/changelog/2026-10-13-enterprise-managed-settings-enforcement-updates/)。
- **一句话结论**：Copilot CLI、VS Code 与 Copilot App 支持在企业托管设置中添加 forceRemoteSettingsRefresh: true，确保启动时从受管端确认策略，无法确认则 fail-closed。
- **具体怎么做**：①管理员在受支持的 server-managed、MDM 或 file-based managed settings 中设置 forceRemoteSettingsRefresh 为 true；②重启客户端确认拉取新策略，而不只依赖旧缓存；③模拟策略端不可达，验证客户端拒绝在未知策略状态下继续运行；④配置 sandbox 管控项的团队核对最低支持客户端版本，防止旧版绕开策略。
- **适合什么场景**：企业 Copilot、多 Agent 高权限 shell、统一沙盒治理。
- **注意**：server-managed 值需先被客户端成功接收，才会在之后启动强制刷新；强制刷新可能牺牲离线启动可用性。

### 技巧 2｜审计 Code Quality 告警的 dismiss 和 reopen，别让质量问题被悄悄清零

- **来源**：GitHub 官方，2026-10-13，[公告](https://github.blog/changelog/2026-10-13-audit-github-code-quality-finding-dismissals-and-reopenings/)。
- **一句话结论**：组织和企业审计日志新增 repo.code_quality_findings_dismissed 与 repo.code_quality_findings_reopened 两种事件，可以追踪谁关闭/恢复了质量告警。
- **具体怎么做**：①进入组织或企业 Audit Log；②按上述两个 action 过滤；③检查 actor、repo、rule、finding identifiers、count 和时间，重点核对 Agent PR 之后集中的驳回行为；④使用 Enterprise Cloud 审计 API 将这些事件加入例行治理报告。
- **适合什么场景**：自动 PR、GitHub Code Quality、AI Reviewer 管控。
- **注意**：适用于已经启用 Code Quality 的仓库；此次特性在 GitHub Team 与 Enterprise Cloud GA，GitHub Enterprise Server 不支持。

### 技巧 3｜缩小 Agent GitHub App 的仓库创建与安装管理权限

- **来源**：GitHub 官方，2026-10-13，[公告](https://github.blog/changelog/2026-10-13-github-app-improvements-for-least-privilege-and-management/)。
- **一句话结论**：创建仓库可以只申请 repository_creation:write；管理安装仓库列表另用 installation_repositories:write，不必为单纯创建仓库持有宽泛的 repository_administration:write。
- **具体怎么做**：①盘点已有 Agent App / fine-grained PAT 是否因创建仓库而持有管理权限；②在测试环境改成 repository_creation:write 并执行仓库创建 API 回归；③仅对确需调整 App 安装范围的身份增加 installation_repositories:write；④验证无法删除或转移无关仓库，记录安装范围变更。
- **适合什么场景**：自研 Coding Agent、企业 GitHub App、自动创建项目仓库与 CI。
- **注意**：创建仓库的 App 仍需组织管理员安装授权；细粒度权限并不等于没有组织治理责任。

## 经典论文回顾

### RRT-Connect（Kuffner & LaValle，ICRA 2000）：双向探索为何仍是高维规划的实用基线

**历史位置**：James J. Kuffner 与 Steven M. LaValle 的 *RRT-Connect: An Efficient Approach to Single-Query Path Planning* 发表于 **ICRA 2000（995–1001 页）**。历史索引已有 1998 年基础 RRT，但 RRT-Connect 的双向贪心算法此前未作独立经典回顾。它正适合对照今天 world-model latent RRT 的搜索结构。（[IEEE DOI](https://doi.org/10.1109/ROBOT.2000.844730)，[作者研究页](https://www.kuffner.org/james/plan/)）

### 核心问题、算法与数学思想

单棵 RRT 从起点探索高维配置空间，只有逐步接近目标才形成完整路径。RRT-Connect 同时从起点和终点建立两棵树：一棵朝随机样本 EXTEND 得到新节点，另一棵采用 CONNECT 贪心策略尽量沿局部路径朝该节点延伸；两树相遇便组合成从起点到终点的路径。

    Start Tree ── EXTEND(q_rand)
                       ↓
              new configuration
                       ↓
    Goal Tree  ── CONNECT(new configuration)
                       ↓
           reached? stitch or swap trees

该方法结合 RRT 的 Voronoi 探索偏置与双向搜索效率，特别适合无预处理的单次高维几何路径规划。原论文展示了刚体与机械臂路径，并包括 6 自由度 PUMA 等示例。

### 动力学假设、当年为何重要、今天仍使用的思想

RRT-Connect 主要在配置空间运行，要求能进行局部几何延伸和碰撞检查。它不直接给出执行时的速度、加速度或扭矩安全保证；对不可逆动力学、非完整约束或复杂接触切换，目标树“从目标向后走”的假设不一定对应现实可执行动作。

当年重要的贡献是几乎不用环境预处理，却能高效完成高维 single-query motion planning。今天 OMPL 仍有成熟 RRTConnect，后续 constrained/atlas RRT、RRT*、kinodynamic RRT 和 GPU 批处理在可行性、质量与计算上分别延展了这条路线。

### 已被后续扩展的部分、开源与可复现性

经典方法不追求全局最短路径，缺乏动力学约束与复杂障碍风险预测；现代系统通常在找到几何路径后再进行优化、时间参数化与独立安全检查。

可使用 [OMPL RRTConnect](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1RRTConnect.html) 复现，与基础单向 RRT、constrained RRT 和 latent-world-model RRT 在相同随机种子、碰撞检查预算下比较成功率、P95 时间、平滑后可执行率。**几何找得到路与机器人真实走得过去是不同的验收目标。**

### 对当前工程项目的重新解读

今天 Sampling-based Kinodynamic Planning with World Models 把双向/采样探索的基本思想迁入 learned latent state，不应因此跳过低层物理验证。规划器需要明确输出世界模型不确定性与候选路径，安全执行仍由真实距离场、机器人动力学与控制周期约束决定。

[ICRA 2000 DOI](https://doi.org/10.1109/ROBOT.2000.844730) · [作者主页](https://www.kuffner.org/james/plan/) · [OMPL](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1RRTConnect.html)

## 今日结论

今天的研究共同强调**任务抽象与物理可执行性必须分层**。Wi-Fi 帮助寻找目标，视觉/深度仍负责几何导航；MCR 将“无路”转为可移动约束组合问题，但动作可执行还得靠操作规划器；世界模型树规划把探索交给 RRT/KPIECE，不将潜空间的高分动作直接当作真实安全动作。

PriMoRetarget 让真正关键的接触优先于姿态相似性；PanTact 先把全身接触从人类示范中正确采集，再让 WBC 判断机器人能否实现。Fly-by-Code 则将“我不知道为什么失败”变成生成一个新的诊断实验，而不是让大模型重复猜测；LeWAM 将世界预测与动作生成在训练目标里直接结合，但仍需要外部独立验证。

AI Coding 的教训同样清晰：Agent 修改部署配置需要有别于普通代码的合并门槛，工具权限需最小化，安全策略必须是当前版本，告警驳回必须可追踪。模型越强，越不能把真实执行、审计和安全边界交给模型自述。

**一句话：不要把预测、接触、权限和安全藏在黑盒里；每个关键假设都应有明确状态、验证方法和降级路径。**

## 最值得深入研究或尝试复现的方向

1. **Wi-Fi/视觉定位 Sidecar**：记录 Wi-Fi bearing 与 LIO/VIO 位姿，在不同移动基线下拟合源位置协方差。
2. **可移动障碍的任务规划**：占据图增加可移动对象语义与权限，标准导航失败后再求 MCR。
3. **World Model + RRT/KPIECE**：固定 DINO-WM/算力预算，比较 CEM/MPPI 与潜状态树搜索，测真实可执行率。
4. **优先级接触重定向**：用脚步与抓持接触高优先级、外观姿态低优先级，记录 infeasible。
5. **身体接触示范数据**：为接触面、持续时间、物体关系和力限制建立结构化标签。
6. **具身 Agent View/Probe**：失败原因不明时，只在受控仿真中先生成诊断程序并要求验证证据。
7. **联合 JEPA/Flow 基线**：固定训练数据比较先世界模型后策略与联合训练的闭环回报。
8. **Agent PR 审批分级**：对 CI、Docker、Terraform、Kubernetes、数据库迁移单独设 CODEOWNERS。
9. **企业 Copilot / GitHub App 治理**：托管策略强制刷新、审计质量告警驳回、拆分仓库创建与管理权限。

## 参考资料

[arXiv Robotics new](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering new](https://arxiv.org/list/cs.SE/new)。

[ViFiNav](https://arxiv.org/abs/2610.12733) · [Minimum Constraint Removal](https://arxiv.org/abs/2610.12609) · [World-Model Kinodynamic Planning](https://arxiv.org/abs/2610.12910) · [PriMoRetarget](https://arxiv.org/abs/2610.12642) · [PanTact](https://arxiv.org/abs/2610.12558) · [Fly-by-Code](https://arxiv.org/abs/2610.12549) · [LeWAM](https://arxiv.org/abs/2610.12818) · [Agent Dual-Scope PR](https://arxiv.org/abs/2610.12849)。

[Managed Settings Refresh](https://github.blog/changelog/2026-10-13-enterprise-managed-settings-enforcement-updates/) · [Code Quality Audit](https://github.blog/changelog/2026-10-13-audit-github-code-quality-finding-dismissals-and-reopenings/) · [GitHub App Fine-Grained Permissions](https://github.blog/changelog/2026-10-13-github-app-improvements-for-least-privilege-and-management/)。

[RRT-Connect IEEE DOI](https://doi.org/10.1109/ROBOT.2000.844730) · [Kuffner 原作者研究页](https://www.kuffner.org/james/plan/) · [OMPL RRTConnect](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1RRTConnect.html)。
