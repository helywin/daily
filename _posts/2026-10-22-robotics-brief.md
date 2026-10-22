---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-22"
date: 2026-10-22 09:00:00 +0800
description: "MAPLE 无训练室内探索、雷达卫星地图定位、RILC 与自适应 Koopman MPC、SuperMimic、机器人规划器强化学习、视觉触觉世界模型及 Agent 业务规则测试。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-22

## 摘要

**检索基准：2026-10-22 09:00（Asia/Shanghai），星期四。** arXiv Robotics（cs.RO）最近常规公开批次为 **10 月 21 日，88 条列表条目**；Software Engineering（cs.SE）同日 **39 条**。这里是列表条目数，不能直接视为全部首次投稿。先查最近 24 小时的一手消息，再查看最近七天；本期论文首次提交于 10 月 19—20 日 UTC，故均注明**时间回补**。与 GitHub master 截至 10 月 21 日的 **1,065 条索引**按标题、arXiv ID、DOI、项目主页和仓库交叉去重，以下八项均未覆盖。

今天的关键进展不是单纯换一个更大的视觉或控制模型，而是重新分配**地图假设、观测模型、控制迭代、真实接触与软件验收**各自的职责。MAPLE 将多种可能的未知室内几何用于信息增益估计，无需离线学习；RadGeoLoc 在 GNSS 不可靠时用地面雷达、卫星影像和粒子滤波建立跨模态绝对位置证据。RILC 将高精度迭代学习控制和跨轨迹泛化策略耦合，DA-KCF 则保持名义 Koopman 模型不变、在线只学习风扰残差。SuperMimic 在可微世界模型上大幅降低人形动作跟踪训练成本；AgenticRoboRL 将 Coding Agent 的多轮后训练方式迁入机器人规划器；PhysCanvas 以视觉、触觉、状态一致性提高想象 Rollout 的决策相关性。软件侧的 AgenTest 则证明仅检查最终任务完成状态会漏掉大量业务规则违例。

AI Coding 实操精选 GitHub CLI 可自动刷新的短期 OAuth 凭据、Claude Code 新增的安全决策遥测事件，以及 Copilot 企业模型策略 REST API。经典回顾选择 2006 年的 Iterative Learning Control 综述，连接今天 RILC 的理论边界。

原始公开列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。本文定量结果均为作者特定实验报告，不自动等于 RK3588、Jetson、Go2 或其他硬件的可复现性能。

## 1. MAPLE：未知室内空间不只猜一张地图，而是维护多种可能的可见性

**时间回补：v1 提交于 2026-10-20 17:25 UTC。**

### 为什么重要

机器人探索陌生建筑时，经典 Frontier Exploration 只根据当前已知自由空间及未知边界选择目标。墙后是否有长走廊、岔路还是房间，会影响下一次移动究竟能够新增多少观测。学习型地图补全能提供先验，但往往要求特定楼层数据训练及推理算力。MAPLE 以 Mondrian 随机空间分割为基础，把观察到的墙体和房间几何条件化成**多个可能的未知地图假设**，不用神经网络离线训练。

### 算法模块、传感器和假设

~~~text
局部占据地图 / 观测墙面
          ↓
Mondrian 结构先验
          ↓
生成多个可能的未观测地图
          ↓
逐假设估计候选 Frontier 的可见区域
          ↓
聚合信息增益与行动成本
          ↓
局部规划器执行并更新真实地图
~~~

输入仍依赖有足够可信度的 LiDAR/深度图、里程计和局部占据地图。生成的房间边界只是假设，不能标记为已确认自由空间。尤其在临时隔断、开放大厅、不规则墙面中，Mondrian 结构先验可能失配。

### 实时性、鲁棒性与可复现性

作者在 KTH 楼层平面图及来自真实 SLAM 的环境中，跨多个传感器量程比较无预测探索和学习型预测探索。MAPLE 通常优于无预测基线，与学习型方案有竞争力。摘要没有给统一探索成功率、FPS 或硬件延迟。一个很重要的负面结论是：**地图补全像素越准确，不必然使探索效率越高**；因为 Frontier 价值取决于可见性差异，而不只是图像相似度。目前未确认完整官方代码公开。

### 适合谁关注与工程落地启发

适合未知楼层、矿井支巷和仅能使用 CPU 的巡检机器人。先保留现有 Frontier Planner，只增加并行假设生成和预计信息增益评分。记录 frontier_id、hypothesis_variance、predicted_visible_area、actual_new_area 和探索里程；遇到未知空间时，独立碰撞检查只能依赖真实感知。关键 A/B 是**相同里程和算力预算下实际新发现的自由空间**。

来源：[MAPLE 论文](https://arxiv.org/abs/2610.28566)。

## 2. RadGeoLoc：地面旋转雷达和卫星 RGB 地图跨模态匹配的 GNSS 失锁定位

**时间回补：v1 提交于 2026-10-19 21:30 UTC。**

### 为什么重要

在城市峡谷、林地和越野场景中，GNSS 精度不足可能使长时间行驶里程计出现累计全球位置误差。卫星 RGB 影像通常已有地理坐标，但地面旋转雷达看到的是回波结构，不是俯视 RGB。RadGeoLoc 使用预训练雷达表示与卫星图像特征构建学习式测量似然，再让粒子滤波器维护**多个可能的地理位置假设**。

### 算法模块与传感器假设

~~~text
Spinning Ground Radar → Radar Odometry → 粒子运动预测
            ↓
Masked Reconstruction 预训练 Radar Encoder
            ↓
Satellite RGB Feature Map（地理配准）
            ↓
跨模态 Observation Likelihood
            ↓
粒子重加权 / 重采样 → Global Pose Belief
~~~

它需要地面旋转雷达、粗略初始区域先验和已地理配准的卫星图；不能凭空消除卫星地图不新鲜、树冠遮挡或雷达重复结构导致的多模态定位歧义。粗先验范围扩大还会增加粒子数需求。

### 结果、实时性和工程风险

作者在 **8 个数据集的 31 条城市/越野路线**评估，并对同一路线相隔 **13 个月** 的不同天气重访考察鲁棒性。摘要没有给统一米级定位 RMSE、更新 Hz 或端侧硬件指标，不能推断可直接替代 FAST-LIO。当前未确认完整官方代码。真机需保留粒子有效样本量、观测似然峰度、地图年代、重定位创新量和多峰假设数量；低置信时不能把最大权重粒子当作唯一正确全球位姿。

### 适合谁关注与工程落地启发

适合 GNSS 受限户外地面机器人、矿区露天车和雷达地图匹配。建议保持 LIO 负责高频连续位姿，用 RadGeoLoc 作为低频绝对定位约束；只在后验足够集中、空间变换连续且通过独立验证时修正全局地图坐标。跨模态检索质量、重定位可靠性和局部避障属于三个不同验收项。

来源：[RadGeoLoc 论文](https://arxiv.org/abs/2610.27310)。

## 3. RILC：让迭代学习控制保留收敛优势，同时用 RL 泛化到新轨迹

**时间回补：v1 提交于 2026-10-20；已接收 Control Engineering Practice，2026 年第 176 卷。**

### 为什么重要

传统 Iterative Learning Control（ILC）适合重复执行同一轨迹：上一轮的跟踪误差可用于修正下一轮馈前控制，精度通常很好。但每条新轨迹都要重新学习。RL 策略能跨轨迹泛化，但往往训练数据需求高，且首次执行精度未必可靠。RILC 将两者并行耦合，ILC 提供经过重复试验改进的高质量控制样本，RL 在不同轨迹之间学习通用补偿。

### 算法模块与动力学假设

~~~text
目标轨迹 + 当前跟踪误差
           ↓
稳定的 ILC 更新律 ──→ 重复执行精度提升
           ↕
跨轨迹 RL 通用补偿策略
           ↓
组合控制输入
           ↓
弹性关节机械臂 / 下一轮回放
~~~

弹性关节系统包含电机侧与负载侧运动、柔顺传动及模型失配。论文给出的稳定和误差界结论有明确的系统、更新律和耦合条件；不能概括为“接上任意 RL 网络后 ILC 总会稳定”。

### 实验、实时性与鲁棒性

作者在**欠驱动四自由度串联弹性机器人**上进行了仿真和硬件实验，覆盖不同轨迹及模型不准确情形。作者称方法能减轻传统 ILC 的首次执行误差与适应速度问题，并证明在特定条件下 RL 部分不破坏 ILC 稳定性、还能改善渐近误差界。摘要没有通用 Hz 或误差改善百分比。当前未确认完整代码。需避免把训练阶段高质量的 ILC 轨迹直接当成全新负载或碰撞环境的安全证明。

### 适合谁关注与工程落地启发

适合重复装配、柔性传动机械臂、高精度轨迹跟踪。最小复现可以先在固定轨迹记录 trial_index、tracking_RMSE、first_trial_error、feedforward_update 和电机饱和，然后引入独立训练的跨轨迹策略；保持原 ILC 控制环作为主稳定路径。它适用于**重复任务学习**，并非替代所有在线 MPC。

来源：[RILC 论文](https://arxiv.org/abs/2610.28329) · [期刊 DOI](https://doi.org/10.1016/j.conengprac.2026.107166)。

## 4. DA-KCF：四旋翼名义 Koopman 模型保持不动，在线只补偿空间变化的风扰

**时间回补：v1 提交于 2026-10-20 00:09 UTC。**

### 为什么重要

真实无人机在建筑尾流、局部阵风和旋翼气动干扰下，动力学与离线仿真模型会偏离。重新在线训练完整动力学网络容易过拟合短时扰动，并损坏在无风条件下已经学好的行为。论文提出 Disturbance-Aware Koopman Control Family（DA-KCF）：**名义模型固定，轻量残差集成在线学习风扰修正**。

### 算法模块及假设

~~~text
离线模拟数据 → Reference-dependent Koopman Control Family
                            ↓ 少量真机校准
                         固定名义模型
真机 (state, command, next state)
                            ↓
                   在线轻量残差集成
                            ↓
          预测窗口逐步叠加风扰修正
                            ↓
                 MPC 输出位置 / Yaw 参考
                            ↓
                   机载稳定控制器
~~~

MPC 不是直接绕过飞控给电机任意指令；低层稳定控制器仍承担姿态稳定。残差更新依赖时序正确的因果状态—指令—后继状态样本，未见的快速突变、状态估计漂移或执行器故障可能超出残差模型分布。

### 实时性、鲁棒性与复现

作者在**纳米四旋翼真机**的均匀风和空间变化尾流场景中，报告在线适应改善多步预测与轨迹跟踪，并满足其硬件实时要求。摘要未提供通用 MPC 周期和改善比例，不应补造。当前未确认完整代码。应记录 nominal_prediction_error、residual_norm、ensemble_disagreement、MPC_deadline、tracking_error；残差与不确定性突增时回退稳定名义控制，并保持飞控 Failsafe 独立。

### 适合谁关注与工程落地启发

适合 PX4/无人机风扰补偿、学习动力学加经典 MPC。先离线固定名义控制器，用同一组风场日志比较无修正、全模型在线重训及固定名义模型+残差；再测试扰动切换、时延、旧状态和模型恢复过程。**在线适配应修正已知残差，不能偷偷改变系统安全边界。**

来源：[DA-KCF 论文](https://arxiv.org/abs/2610.27414)。

## 5. SuperMimic：一个可微世界模型显著降低人形全身动作跟踪训练成本

**时间回补：v1 提交于 2026-10-20 16:29 UTC；CoRL 2026 Oral。**

### 为什么重要

人形机器人要模仿成千上万段人类动作，传统 Model-Free RL 往往需要大量并行仿真，或先训练专门策略再蒸馏。SuperMimic 从刚体仿真器日志拟合**一个共享动力学的可微世界模型**，随后用短窗口想象 Rollout 的反向传播直接训练动作跟踪策略，减少反复调用大型物理仿真器的预算。

### 算法模块与动力学假设

~~~text
刚体仿真器状态转移数据
             ↓
统一可微世界模型
             ↕ 联合训练
人形参考动作 → Tracking Policy
             ↓
短时想象 Rollout + BPTT 梯度
             ↓
动作跟踪损失更新
             ↓
真机 Unitree G1 执行与验证
~~~

依赖模型在短时运动和接触动力学附近足够准确。短窗口梯度有效，并不等于任意长期碰撞、复杂物体交互都被精确建模。最后仍需真实机器人关节扭矩、接触和自碰撞控制。

### 实验、实时性与可复现性

作者报告：**一张 GPU 训练约 3 小时**超过一个**128 GPU、7 天**的对照跟踪器回报；按作者比较口径 GPU-hours 需求减少超过 **1000 倍**。在 **129,514 段**测试动作中，训练阶段某模型仅失败 **25 段**，对照 **179 段**；两张 GPU 训练 **9.8 小时**后在该测试集报告零失败。并展示 Unitree G1 真机迁移。对照 GPU 型号和计算任务并不完全相同，训练算力节省不等于真机推理提升千倍。项目页已公开；需核查正式代码、权重与训练数据可获取性。

### 适合谁关注与工程落地启发

适合 G1、人形动作 Retargeting、Whole-Body RL。可先使用相同动作库与约束定义，对比传统 Isaac/MuJoCo Model-Free RL 与可微模型短 Rollout：记录 simulator_transitions、world_model_error、GPU_hours、tracking_success、foot_slip 与真机安全过滤次数。不要用仿真“零失败”宣传真机安全认证。

来源：[SuperMimic 论文](https://arxiv.org/abs/2610.28480) · [官方项目](https://supermimic.github.io/)。

## 6. AgenticRoboRL：将 Coding Agent 的 SFT＋多轮 RL 后训练迁移到机器人规划器

**时间回补：v1 提交于 2026-10-20 17:41 UTC。**

### 为什么重要

机器人 Agent 的性能常通过更好的 Prompt、技能库和长期记忆提升，但始终使用同一个未经专项训练的通用规划模型。AgenticRoboRL 借鉴 Coding Agent 的工具调用轨迹后训练：将任务级成功反馈回传规划模型，针对不同 Robot Harness 进行统一的 SFT 和多轮 RL。

### 算法模块与执行接口

~~~text
VLA Skill Harness / 控制代码生成 Harness
                 ↓
       各自的 Adapter
                 ↓
 Planner 多轮调用轨迹 + 任务结果
                 ↓
           SFT → Multi-turn RL
                 ↓
          更新 9B 规划器
                 ↓
      原有执行 Harness 保持不变
~~~

它优化的是**规划层选择工具及处理错误的能力**，不是直接提升电机闭环带宽或隐式修改物理控制器。不同 Harness 的安全权限和成功测试仍需要独立运行。

### 结果、复现性与工程风险

作者在 LIBERO-PRO 报告：9B 规划器不使用外部记忆时成功率由 **18.1% 提高到 71.0%**；使用外部记忆的 Codex（论文中的 GPT-5.5）对照约为 **72.1%**。这属于论文的任务集合与 Harness 条件，不应推广为所有机器人都能使用 9B 达到 71%。作者表示**将公开**框架和权重，目前不能声称完整开源。真实控制代码生成需隔离运行，策略训练必须避免学习到绕过失败测试或安全检查的投机路径。

### 适合谁关注与工程落地启发

适合具身 Coding Agent、已有稳定技能 API 的机器人系统。设计清晰的 read_state、navigate、grasp、stop 等工具；把 task_success、failure_reason、safety_violation、tool_trace 作为训练轨迹，而不让奖励仅取决于 Agent 最后一条“已完成”文字。可先对同一测试集比较 Prompt-only、外部记忆和规划器后训练三组。

来源：[AgenticRoboRL 论文](https://arxiv.org/abs/2610.28589)。

## 7. PhysCanvas：视觉、触觉和任务状态同时一致的世界模型，才更适合评估操作策略

**时间回补：v1 提交于 2026-10-20。**

### 为什么重要

只根据未来视频判断机器人抓取是否会成功，可能完全错过摩擦、滑动、指尖触觉变化等决定性信息。视觉上合理的物体运动不一定代表真实接触力学正确。PhysCanvas 将多视角 RGB、触觉图像、Marker 位移、任务状态与动作统一映射到视频潜空间，并引入独立奖励模型约束不同信息之间的一致性。

### 算法模块和传感器假设

~~~text
多视角 RGB + 光学触觉 + Marker 位移 + 状态 + 动作
                          ↓
               共享 Video VAE / 生成主干
                          ↓
    基于正运动学与相机投影的动作空间条件
                          ↓
               未来视觉 + 触觉生成
                          ↓
     Scene / Modality / State Reward Models
                          ↓
             一致性后训练的世界模型
                          ↓
             Policy Rollout / GRPO 更新
~~~

依赖摄像头、触觉表面、机器人几何及时间同步。生成器可能把观察合理性误当物理正确性，尤其是新材料、未知摩擦和接触模式。

### 结果、实时性与可复现性

四项真实操作任务上，世界模型预测的任务成功率与真实成功率的**任务级 Pearson 相关系数平均从 0.602 提升到 0.885**；通过一致性模型想象 Rollout 训练后，π0.5 真实平均成功率从 **59.1% 提升到 70.8%**。相关性提升不等于逐步物理误差同等下降。该方法包含视频生成，作者没有声称能在低功耗平台每个控制周期实时运行；目前项目页明确标注 **Code / Model Coming Soon**。

### 适合谁关注与工程落地启发

适合机械臂接触操作、视觉触觉世界模型和训练期数据扩增。先用现有真实操作日志比较“只预测图像”和“联合预测触觉/状态”的离线候选动作排序；检查成功率相关性、触觉误差、状态违例和真实部署表现。世界模型可以帮助评估，但不能取代真实夹爪力限幅与独立接触安全控制。

来源：[PhysCanvas 论文](https://arxiv.org/abs/2610.28613) · [项目页](https://zebinx.github.io/PhysCanvas_HomePage/)。

## 8. AgenTest：业务规则不在最终状态里，Agent 测试必须检查整个工具调用过程

**时间回补：v1 提交于 2026-10-20。**

### 为什么重要

会操作订单、客户信息或账务数据的 LLM Agent，即使最终任务完成，也可能在过程中错误读取他人信息、违反审批前置条件或越权修改资源。传统 Benchmark 的最终状态断言可能根本发现不了这类问题。AgenTest 从 System Prompt、工具定义和领域知识提取业务规则，把规则整理成可执行的 Given–When–Then，再构造多轮用户与环境状态测试。

### 测试流程与权限边界

~~~text
系统规则 + Tool Schema + 领域要求
                ↓
        业务规则抽取 / 精炼
                ↓
        Given–When–Then 规格
                ↓
    构造测试用户 + 环境初始状态
                ↓
       多轮 Agent 工具交互
                ↓
检查消息 / 工具调用 / 数据状态的混合 Oracle
                ↓
            最小失败案例
~~~

规则提取本身可能遗漏业务限制或产生错误断言，故需要抽检合法正例。测试必须运行在隔离数据库与假账户中，不能为了找越权 Bug 访问真实客户数据。

### 实验结果与可复现性

作者在 tau2-bench 的航空、零售与电信 Agent 上生成 **551 条精炼规格**。使用两种模型时，分别发现 **89 和 121 条**不同规则被违反，对应为全部基线合计发现量的 **3.4 倍与 2.5 倍**。约 **60%** 可触发 Bug 的运行，仅看最终状态无法识别；只有其方法发现了不当访问或修改其他用户数据的问题。论文未确认成熟源码入口，结果属于具体模型与业务场景。

### 适合谁关注与工程落地启发

适合企业业务 Agent、MCP 工具和具备副作用的 Coding Agent。最小试验可以选 5 条真实约束，例如“用户 A 不得读取 B 的订单”“未审批不得调用发布工具”，并记录 tool_name、actor_id、resource_owner、precondition、effect。将测试 Oracle 放在独立进程，不允许被测 Agent 修改规则。**任务完成率与业务规则遵守率必须分别验收。**

来源：[AgenTest 论文](https://arxiv.org/abs/2610.28116)。

## AI Coding 实战技巧精选

### 技巧 1｜给 GitHub CLI 切换可刷新的短期 OAuth 凭据

- **来源**：GitHub 官方，2026-10-21：[原始公告](https://github.blog/changelog/2026-10-21-github-cli-opt-in-to-expiring-auto-refreshing-oauth-tokens/)。
- **一句话结论**：从 gh **v2.103.0** 起可选择短期访问 Token 和自动旋转 Refresh Token，减少长期泄漏 Token 的风险。
- **具体怎么做**：① 在测试终端确认 gh --version；② 新登录执行 gh auth login --expiring，或为之后登录执行 gh config set expiring_credentials enabled；③ Git HTTPS 操作运行 gh auth setup-git，建议 Git 2.46+；④ 执行 gh auth status 检查有效期并用测试仓库验证拉取。
- **适合什么场景**：本地 Codex/Claude Code、Worktree、长期运行开发机的 GitHub CLI 身份管理。
- **注意**：它是**可选预览**；将 gh auth token 输出缓存到脚本的做法可能在几小时后失效。该令牌与 GitHub Actions 使用的 GITHUB_TOKEN 不是同一种配置。

### 技巧 2｜用 Claude Code v2.1.307 审计工具被阻止的原因与 MCP 副作用重试

- **来源**：Anthropic，2026-10-21：[官方 Release](https://github.com/anthropics/claude-code/releases/tag/v2.1.307)。
- **一句话结论**：新版本增加 claude_code.safety_event OpenTelemetry 事件，同时调整 HTTP MCP 网络中断后的重试，只自动重试只读或幂等工具。
- **具体怎么做**：① 通过 claude --version 核实至少 v2.1.307；② 在测试环境使用现有受控 OTLP 收集器开启官方支持的遥测输出；③ 分别制造无害的权限拒绝、Hook 拒绝和 Sandbox 拒绝，核对 safety_event 是否记录；④ 对 MCP 写操作注入断连，检查是否避免重复创建 Issue、重复部署或重复扣费。
- **适合什么场景**：Claude Code、企业 Agent、HTTP MCP、有副作用的工具编排。
- **注意**：遥测字段可能泄露内部路径或工具上下文，应限定收集范围。网络层“未自动重试”不等于业务层天然幂等，服务端仍需请求幂等键。

### 技巧 3｜用 Copilot Model Policy API 清点并冻结组织 Agent 可用模型

- **来源**：GitHub 官方，2026-10-19（时间回补）：[原始公告](https://github.blog/changelog/2026-10-19-copilot-model-policy-api-for-enterprise-orgs-and-teams/)。
- **一句话结论**：新增正式 GA 的 GET/PATCH 模型策略 REST API，适合在组织统一控制 Copilot Agent 的模型名单。
- **具体怎么做**：① 先用拥有相应组织权限的管理员测试身份执行 gh api /orgs/ORG/copilot/model-policies（替换 ORG）；② 企业级可读取 /enterprises/ENT/copilot/model-policies，团队和 Agent App 也有独立层级；③ 将当前 JSON 保存到内部审计系统，仅在评审后使用 PATCH；④ 选择测试团队确认禁用模型真的不可选，并验证保留的替代模型可用。
- **适合什么场景**：GitHub Copilot Business/Enterprise、多个 Agent App、模型退役迁移、成本与权限管理。
- **注意**：GET 是只读，PATCH 是组织策略写操作；不得让 Coding Agent 在没有管理员批准的情况下自行改变组织模型政策。具体权限与 API JSON Schema 以官方文档为准。

## 经典论文回顾

### Bristow、Tharayil、Alleyne：《A Survey of Iterative Learning Control》（IEEE Control Systems Magazine，2006）

**发表时间与历史位置**：论文发表于 2006 年 IEEE Control Systems Magazine 第 26 卷第 3 期，96—114 页，是连接早期工业重复控制与现代学习控制的重要综述。[IEEE 论文](https://doi.org/10.1109/MCS.2006.1636313) · [大学作者记录](https://experts.umn.edu/en/publications/survey-of-iterative-learning-control-a-learning-based-method-for-/)。

### 核心问题与数学思想

普通反馈控制在重复任务中，每次都从近似相同的策略开始纠正误差。ILC 额外利用上一轮相同时间位置的误差来更新下一轮控制输入。典型形式为：

~~~text
u_(k+1)(t) = u_k(t) + L[e_k](t)
~~~

其中 k 是重复任务编号、t 是一次执行内的时间、L 是学习算子。理想条件下，沿试验编号的误差能够收敛。这里**沿迭代收敛**不同于常规闭环系统在单次执行时间内的稳定性：即使某条任务重复后精度很高，也不代表新轨迹第一次执行同样准确。

### 传感器、动力学假设与当年价值

经典 ILC 强依赖任务可重复性、时间对齐、误差测量、初始条件以及输入/输出映射。机械臂编码器、末端位置测量和已知时间参考都可提供反馈。2006 年综述系统梳理稳定性、单调收敛、瞬态学习和鲁棒设计，说明学习器不是单纯把上次误差乘一个巨大系数。模型失配、非重复扰动、输入饱和和错误的初始状态都会影响性能。

### 今天仍有效的思想和被后来扩展的部分

精密重复制造、轨迹型机器人仍可用 ILC 构造高质量 Feedforward。后续 Model-based ILC、优化 ILC、深度学习与 RL 等方法帮助处理更复杂动态或跨轨迹转移。今天的 RILC 试图解决其经典短板：保留同一轨迹重复学习的理论控制结构，同时让 RL 给新轨迹提供更好的首次尝试。它不是“RL 从此获得 ILC 的全部收敛保证”，条件仍必须重新检查。

### 复现路径与今天的工程解读

在 ROS2/MuJoCo 的四关节机械臂上准备 3 条不同速度和曲率的轨迹。以相同反馈控制为底座，对比纯反馈、固定轨迹 ILC、跨轨迹共享补偿、RILC 风格耦合。分别统计首次跟踪 RMSE、经过 5/10 次后的误差、最大电机扭矩、学习过程是否振荡，以及不同负载的恢复能力。**一个控制器训练后的平均精度不应掩盖首次执行风险与试验间收敛条件。**

## 今日结论

今天八项工作共同强调：机器人和 Agent 的高可靠性来自**对“还不知道什么”的显式管理**。MAPLE 保留多个未知地图解释，RadGeoLoc 保留全球位置多峰假设；RILC 区分重复任务学到的高精度与跨轨迹泛化，DA-KCF 将名义动力学和实时风扰残差分开；SuperMimic 借助可微模型降低大量运动学习的仿真成本，但仍需真机验证；AgenticRoboRL 改变任务规划器而不侵入执行 Harness；PhysCanvas 指出视觉上合理的未来视频不能代替真实触觉一致性；AgenTest 则证明工具调用过程中的业务规则必须被独立检查。

工程上可以概括为：**观测假设、动力学修正、执行权限和验收 Oracle 都应该有明确接口；模型更强，不代表这些约束自动成立。**

## 最值得深入研究或尝试复现的方向

1. **MAPLE CPU 探索**：固定楼层 Occupancy Bag，比无预测、单地图补全和多假设可见性评分的新增自由空间/里程比。
2. **Radar+卫星地图全球定位**：保留 LIO 高频位姿，用地面 Radar/Geoimage 粒子滤波尝试低频全球重定位，记录多峰置信度。
3. **RILC 首次执行与重复学习**：同一弹性机械臂比较新轨迹首轮误差和 10 次学习后的误差，检查输入饱和。
4. **DA-KCF 风场变化**：固定名义无人机模型，只允许残差更新，测试突然尾流和恢复原无风模型。
5. **SuperMimic 训练预算复现**：比较模拟器 RL 与短期可微 Rollout 的 GPU-hours、足端滑移和真机安全过滤频次。
6. **Robot Harness 规划器后训练**：用统一工具行为契约评估 Prompt、外部记忆及 SFT/RL 后训练的真实多轮任务成功率。
7. **视觉触觉世界模型**：同一真实数据上比较只看视频与联合触觉/状态预测的候选动作排序。
8. **AgenTest 业务逻辑审计**：对真实业务工具抽取 Given–When–Then，在隔离数据库测试全调用轨迹，重点查跨用户权限。
9. **AI Coding 工具回归**：在测试工作树验证短期 gh 凭据刷新、Claude Code 工具拒绝遥测和企业 Copilot 模型策略读取。

## 参考资料

**最新论文列表**：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

**SLAM / 定位 / 探索**：[MAPLE](https://arxiv.org/abs/2610.28566) · [RadGeoLoc](https://arxiv.org/abs/2610.27310)。

**控制与人形机器人**：[RILC](https://arxiv.org/abs/2610.28329) · [DA-KCF](https://arxiv.org/abs/2610.27414) · [SuperMimic](https://arxiv.org/abs/2610.28480) · [SuperMimic 官方项目](https://supermimic.github.io/)。

**世界模型、具身 Agent、AI Coding**：[AgenticRoboRL](https://arxiv.org/abs/2610.28589) · [PhysCanvas](https://arxiv.org/abs/2610.28613) · [PhysCanvas 项目](https://zebinx.github.io/PhysCanvas_HomePage/) · [AgenTest](https://arxiv.org/abs/2610.28116)。

**AI Coding 一手实操**：[GitHub CLI 短期 OAuth](https://github.blog/changelog/2026-10-21-github-cli-opt-in-to-expiring-auto-refreshing-oauth-tokens/) · [Claude Code v2.1.307](https://github.com/anthropics/claude-code/releases/tag/v2.1.307) · [Copilot Model Policy API](https://github.blog/changelog/2026-10-19-copilot-model-policy-api-for-enterprise-orgs-and-teams/)。

**经典论文**：[A Survey of Iterative Learning Control（2006）](https://doi.org/10.1109/MCS.2006.1636313)。
