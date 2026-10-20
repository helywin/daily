---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-20"
date: 2026-10-20 09:00:00 +0800
description: "聚焦三维声呐 SLAM、微纹理定位、越野动力学学习、四足失败驱动训练、RAX 具身 Coding Agent、VLA 记忆与 Mamba 动作专家，以及 AI Coding 实操。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-20

## 摘要

**检索基准：2026-10-20 08:55（Asia/Shanghai）。** arXiv 最新常规公开列表为 **2026-10-19**：Robotics（cs.RO）121 条（61 条新提交），Software Engineering（cs.SE）37 条（17 条新提交）。列表总量包含交叉收录和更新版本，不能全部算作新论文。

本期先检索最近 24 小时的一手来源，再扩展最近 7 天，与截至 10 月 19 日的 **1,041 条**历史覆盖索引按标题、arXiv ID、DOI、官方项目/仓库联合去重。八项主动态的 v1 实际提交于 **10 月 15–16 日 UTC**，统一标记为**时间回补**。特别注意：10 月 15 日已报道的 RTISSLAM 是二维平面声学 SLAM；今天的 RTISSLAM-3D 新增三维声束建模、6-DoF 状态、三维注册回环与森林真机数据，作为**实质性技术更新**而不是重复旧研究。

**今日最值得关注的路线：** 状态估计需要尊重声呐物理和微纹理尺度；越野控制需要在预测轨迹将到达的位置查询地形特征；四足 RL 训练应围绕真实失败而不是随机堆场景；VLA 应选择何时记住历史和在哪里节省去噪计算；机器人 Coding Agent 的技能复用必须携带执行证据；C++ AI 审计不能只依赖语言模型对静态报警的直觉解释。性能数字均是原作者在相应条件下的报告，不能直接推广到任意 RK3588、Jetson 或机器狗。

最新列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/new)。

---

## 1. RTISSLAM-3D：从二维声呐导航扩展到真实起伏地形的六自由度定位

**时间回补：v1 2026-10-15 18:47 UTC；相对 10 月 15 日旧文的实质更新。**

### 为什么重要

此前的 RTISSLAM 主要处理平面室内声学建图；林地坡面和起伏地形需要真实的 z、roll、pitch 估计。RTISSLAM-3D 将空气三维成像声呐、IMU 与轮式里程计融合，使用**声束的实际角域特性**而不是把稀疏声学峰值机械当成 LiDAR 三维点。

### 算法模块与传感器假设

    3D imaging sonar + IMU + wheel encoders
       → 球面 CFAR 提取稀疏 3D 检测
       → 声束形状感知的声学里程计
       → 极坐标子地图的场所识别
       → 3D 注册验证回环
       → 姿态因子 + 6-DoF pose graph
       → 三维声呐地图

强多径、镜面反射、声速变化、稀疏回波和低信息量的地形仍然会影响关联；IMU 和轮编码器提供的惯性/运动先验也依赖标定、时间一致性。

### 实验、实时性与可复现性

在 **545 m 森林行驶**中，以 3D LiDAR SLAM 作为参考，回环令水平误差 **1.74 m→0.28 m**，高度误差约 **0.12 m**；**94.6%** 的声呐三维地图位于参考 LiDAR 地图 **0.3 m** 以内。这些指标并不是跨场景 6-DoF ATE 保证。原论文摘要没有可迁移的整机 P95 计算耗时或成熟完整开源入口。

### 风险、适合谁关注与落地启发

适合消防、烟尘巡检、矿井和林地机器人。建议先把声呐独立跑成声学 odometry sidecar，与 LIO 同步记录检测数量、速度创新量、回环支持度和位姿误差。不能因为输出格式都是 PointCloud2，就用相同 LiDAR 点面误差模型直接配准声学回波。

**来源：** [论文](https://arxiv.org/abs/2610.22552)。

## 2. Micro-Localization：用地面微纹理做到特定平面任务的几十微米定位

**时间回补：v1 2026-10-15 19:04 UTC。**

### 为什么重要

传统移动平台依赖 SLAM 获得厘米到毫米级位姿；高精度工位对接和测量任务可能需要更精细、可重复的局部定位。论文利用显微镜头读取天然地面纹理，通过高倍率相机模型、对焦质量与特征/光度匹配解决精密二维位置查询。

### 模块、测量假设与结果

    地面显微图像 + 预建纹理参考地图
       → 高倍率镜头标定/对焦控制
       → 特征检索与独立光度配准
       → 已知平面上的绝对平移估计
       → 位置误差与观测质量输出

作者在多种表面、**每种 1,007 次**保留查询中全部定位成功，平移 RMSE **28–73 μm**；独立光度配准与特征解相差约 **9 μm RMSE**。还在低成本移动机器人上使用精密平台建立的地面纹理地图，并观察到温度导致的微小位移。

### 实时性、鲁棒性和复现

这些指标针对**受标定且平整的局部表面**，不是普通室内机器人的六自由度 SLAM 精度。显微镜头小视野导致失焦、灰尘、光照变化、地面磨损、温度变化尤其关键。摘要没有可推广 FPS，亦未核验完整部署代码。

### 适合谁关注与工程启发

适合高精度对接、精密物流平台与自动装配。保留 LIO/VIO 作粗定位，仅在进入固定工位后切换微纹理精定位；对比 AprilTag、机械导向、显微纹理的重复位置误差以及维护代价。输出必须包含 map_revision、focus_score 与定位协方差，防止错误的高精度数字使下游过度自信。

**来源：** [论文](https://arxiv.org/abs/2610.22563)。

## 3. SpatialBEV：越野动力学预测应查询未来轮地接触处的地形

**时间回补：v1 2026-10-16 04:02 UTC；CoRL 2026。**

### 为什么重要

越野车辆进入斜坡、软土和沟壑时，真实动力学依赖**未来具体接触区域**。如果只给模型整张图的全局 embedding，未来多步 rollout 很容易漏掉某段局部坡度或材质变化。SpatialBEV 使用几何/语义 BEV 特征，沿着预测状态位置逐步查询相应空间特征，再预测下一步运动。

### 模块、物理假设与指标

    Local BEV (geometry + semantics)
       + current state / command
       → 预测下一运动状态
       → 在预测位置重新查询 BEV 特征
       → 动力学多步 rollout
       → MPC / 跟踪器评价控制序列

跨季节数据上，作者报告预测误差降低 **17.1%**；真实高于或等于 **10 m/s** 的越野路线中最大横向跟踪误差降低 **25.3%**。后者是最大 cross-track error，而非平均定位误差。方法依赖 BEV 几何配准、车辆状态、运动响应与当前地形的分布一致性；材质变化及时间错位会直接影响结果。

### 实时性、风险与复现

端侧执行需把 BEV 编码、逐步采样、MPC 求解全计入 P95 决策耗时；论文摘要没有统一平台 FPS。项目页有方法和实验展示，未以项目页存在代替权重可用性判断。先固定同一批轮式机器人 bag，比较纯运动学、整图 embedding 和按预测位置查询三组，以最大横向误差、摩擦突变时的模型残差与回退率评价。

### 适合谁关注与工程启发

适合越野车、坡地机器人与学习增强 MPC。只暴露 vx/vy/wz 的封闭底盘可先建立闭环速度响应模型，用地形特征修正高层预测，不必把学习模块改写为低层力矩控制。

**来源：** [论文](https://arxiv.org/abs/2610.22900) · [项目](https://theairlab.org/spatial-bev-dynamics/)。

## 4. FCTS：从机器狗失败地点生成下一批最有价值的训练地形

**时间回补：v1 2026-10-15 20:22 UTC。**

### 为什么重要

随机增加坡道、阶梯、障碍并不能保证学会真实工地上的组合困难。FCTS 根据机器人在验证路线中的**失败位置、跌落/终止模式、运动状态和附近地形**生成训练新场景，然后通过 Monte Carlo Tree Search 在固定训练预算中探索可能的课程分支。

### 算法、动力学与结果

    固定验证路线 → 定位失败片段
      → 局部失败状态 + 地形裁片
      → 条件地形生成
      → MCTS/PUCT 选课程分支
      → RL 更新并回归保留测试路线

基于扫描工地几何重建的测试中，中难路线成功率 **28.4%→85.8%**，高难路线 **14.9%→44.7%**。项目页还展示真实四足平台 **Jetson AGX Orin / 50 Hz** 深度与本体反馈控制；约 24 小时内并行完成 25 次课程扩展，约为顺序速度 **5.3 倍**。50 Hz 是真机控制频率，不代表地形生成或整个训练循环实时。

### 鲁棒性、可复现性与风险

如果跌倒原因其实是感知时延、里程计跳变或 IMU 外参错误，基于错误诊断生成地形会浪费训练。应在固定隐藏路线与真实硬件限幅条件下做验证，确认新课程没有让旧技能遗忘。现有项目页发布视频和流程，完整训练权重/脚本需按实际链接单独核验。

### 适合谁关注与工程落地

适合 Go2、楼梯、工地救援和复杂地形四足 RL。初步做法是在失败 bag 加注 failure_pose、termination_reason、foot_contact、terrain_crop，优先训练“当前能力边缘”的难度，而不是只追求更多并行环境。

**来源：** [论文](https://arxiv.org/abs/2610.22619) · [项目](https://narayananpp.github.io/fcts/)。

## 5. RAX：Coding Agent 用真实探索编译机器人技能，而不是每项任务重训策略

**时间回补：v1 2026-10-15 18:00 UTC。**

### 为什么重要

RAX（Robot Agent eXploration）把具身学习的结果做成可执行程序：Coding Agent 通过机器人感知和运动 API，逐步写程序、观察运行结果、修正错误，完成之后将流程保存为具有前置条件与检查逻辑的可复用技能，不要求先收集该任务的遥操作演示数据。

### 模块、实验与开源

    任务目标 → Coding Agent
       → 调用受控 robot API / 生成动作程序
       → 仿真或经过授权的真机探索
       → 观测/错误与任务验收
       → 修订代码、验证完成
       → 技能库：前置条件 + 执行 + 失败恢复

论文横跨单臂、双臂、灵巧手、移动机器人和人形；在仿真保留环境上，作者报告相较所选先进基线平均 **+37.4%**。项目站展示通过探索生成程序后，某空气炸锅任务从 Agent 探索约 **72 分钟**变为程序复用约 **18 秒**；这是探索与复用执行的任务生命周期差异，不是普遍推理速度提升。官方 [RAX 仓库](https://github.com/robot-agent-exploration/rax) 中 main 是说明索引，具体仿真和真机 Harness 在独立分支；项目页还有原始会话日志和技能库。

### 权限、安全和可验证性

让模型生成机器人运动代码有直接的物理风险。真机动作接口必须有硬限速、允许范围、停止条件与授权。探索脚本不能修改底层安全门禁；技能复用时检查机器人类型、工装和状态版本。最终成功必须由独立的状态/视觉验收决定，不能仅凭 Agent 的自然语言完成报告。

### 适合谁关注与工程启发

适合自研 Robot Harness、Franka、Go2、仿真技能学习。先在隔离模拟器暴露只读状态、safe_move 和 stop 三个简单接口，让 Agent 只生成高层动作流程，再通过可重放日志评估它是否真正学会可靠任务。

**来源：** [论文](https://arxiv.org/abs/2610.22496) · [项目](https://robot-agent-exploration.com/) · [源码](https://github.com/robot-agent-exploration/rax)。

## 6. RePlanMem-VLA：相邻动作预测出现分歧时才保存视觉关键帧

**时间回补：v1 2026-10-15 18:49 UTC。**

### 为什么重要

多阶段 VLA 会用到早先已经不在当前相机视野的目标状态，但永久缓存全部视频显存与检索成本很高。RePlanMem-VLA 使用不同控制周期 Action Chunk 对**同一未来动作位置**的重叠预测；预测修订异常增大时，将其视为“重要事件”，触发有界视觉记忆写入，随后通过机器人掩码减少重复帧。

### 算法与结果

    Action chunk at t / t+1
      → 对齐重叠时间段
      → 测两次动作预测差异
      → 事件阈值决定是否写入 Keyframe
      → robot-mask 去冗余
      → 后续阶段按需检索

论文比较 **35 种**分歧指标，在受测模型/任务下事件检测 ROC-AUC **0.981–0.997**；特定视觉记忆保留实验中，重要帧 **100%** 留存到后续决策点；有真实机器人 replay 的事件选择验证。切勿将“记忆保留 100%”误写成“真机完成率 100%”。

### 实时性、鲁棒性与风险

策略合法多模态、时间戳误差和执行器滞后都能造成伪分歧。存储帧必须绑定 episode、capture_time、action_chunk_id、位姿版本，任务切换与急停后需要旧帧降权。论文摘要没有统一 VLA 真机端到端 FPS，也不能由 AUC 直接推断闭环任务增益。

### 适合谁关注与工程启发

适合 VLA 流式动作块、长时机器人操作、观测带宽受限系统。先离线比较固定间隔抽帧、视觉 embedding 新颖度触发及重叠动作分歧触发的帧命中率与缓存成本，之后再接入在线执行。

**来源：** [论文](https://arxiv.org/abs/2610.22556) · [项目](https://vika787.github.io/RePlanMem/)。

## 7. MambaAct：把 VLA 最耗时的 Action Expert 换成更小的 Mamba 序列模型

**时间回补：v1 2026-10-16 05:20 UTC。**

### 为什么重要

π0.5 一类 Flow-Matching VLA 每块动作需要反复运行去噪网络。MambaAct 保留预训练的视觉语言前缀编码器，使用紧凑的 Mamba 动作专家建模连续 noisy action 序列，并通过 Context Compressor 将视觉语言 Tokens 汇总为 gating/modulation 条件，减少高成本 token-level cross-attention。

### 架构与作者结果

    Vision-language prefix (保留)
       → Context Compressor
       → Mamba Action Expert + Flow denoising
       → Continuous Action Chunk
       → 原控制执行接口

作者报告 Action Expert 规模约小 **10 倍**；LIBERO 去噪延迟降低 **64.8%**，真机去噪部分延迟降低 **58.8%**；三次独立微调种子下 LIBERO 成功率平均增加 **1.08 个百分点**，并在 LIBERO-Plus 和真实操作中保持表现。应特别区分**去噪子模块时延**与相机采集、视觉主干、控制回路的端到端时延。

### 传感器与工程风险

端侧迁移要验证 Mamba selective scan、缓存状态、Context Compressor 的导出与量化算子；不能把 RTX 平台的结果直接当成 RK3588 RKNN 结果。官方仓库声明开放代码与权重，建议先在相同视觉编码器/数据上重放动作并比较模型大小、P95 去噪耗时、端到端耗时、动作平滑和分布外成功率。

### 适合谁关注与工程启发

适合 Jetson 上的实时 VLA、动作专家压缩和边缘计算。若真机瓶颈在视觉前缀而非动作专家，Mamba 替换不会提供对应比例的整机加速。

**来源：** [论文](https://arxiv.org/abs/2610.22951) · [官方代码/权重](https://github.com/giakhuyendihoc/MambaAct)。

## 8. VulnSAGE：让 Coding Agent 对 C/C++ SAST 告警的判断可由程序分析验证

**时间回补：v1 2026-10-16 07:12 UTC。**

### 为什么重要

静态分析在复杂 C/C++ 大仓库中会产生大量上下文依赖型告警。LLM 只看到报错行可能编造调用关系；简单扩大上下文又花 Token。VulnSAGE 使用报告中心程序切片找出真正影响报警操作的调用、对象和数据关系，再通过 CLAIM 中间表示要求模型写出**可以被程序图验证的判断前提**，最后对静态支持的真缺陷构造隔离 PoC。

### 算法和评测

    SAST alert → 程序依赖图与上下文切片
      → LLM 解释 + CLAIM 结构化前提
      → 检查前提引用的程序关系
      → 验证真阳性并生成 PoC
      → 沙盒复现及开发者确认

在 187 条标注报告中，作者拒绝 **89/97** 条误报，保留 **85/90** 条真缺陷；同一 PoC 验证流程下复现 **25** 个正例，对照系统为 **3**。对 GitHub 200 个高 Star C/C++ 项目的 **45,440** 条扫描告警，复现 **104** 个缺陷；维护者对已回应的 26 个报告确认了 24 个，其中有 10 个此前未知缺陷，9 个已修复。不能把 24/26 的确认率推广为全部 104 个缺陷均已核实。

### 权限、可验证性与风险

PoC 构造与执行必须在隔离容器中进行，不能访问生产凭据和部署网络；审计报告需包含 commit SHA、告警 ID、必要代码片段、判断依赖与重放结果。对于权限或程序结构不足以判断的案例，必须允许 uncertain，而不能为了自动化强行打“安全/危险”标签。

### 适合谁关注与工程启发

适合 C++、ROS2、嵌入式和服务器安全告警治理。可先使用已经人工确认的旧告警，固定扫描报告与源码 SHA，对照裸 LLM、相关文件检索和 VulnSAGE 式依赖切片的漏报、误报与复现成本。当前没有核实完整的一键公开实现。

**来源：** [论文](https://arxiv.org/abs/2610.23035)。

---

## AI Coding 实战技巧精选

### 技巧 1｜对 Copilot CLI 单次 -p 会话显式设置受信任工作目录

**来源：** GitHub Copilot CLI 官方 [v1.0.100](https://github.com/github/copilot-cli/releases/tag/v1.0.100)，2026-10-19。

**一句话结论：** 新版增加 --trust-folder，可在一次 -p 或 stdin 驱动的 Prompt 会话中显式信任已经审核的目录，避免无交互任务遇到目录信任提示。

**具体怎么做：** ①运行 copilot --version 确认 1.0.100+。②进入自己控制的测试仓库，运行 copilot -p "只读 README 并说明构建步骤" --trust-folder。③用未经信任的新目录作反向测试，确认信任行为不会无意扩大。④检查 Shell/文件写入权限另行要求审批。

**适合什么场景：** Copilot CLI、一次性自动脚本、独立 Worktree。

**注意：** 目录信任不是安全沙盒；不要给来自外部且未经审查的仓库直接开启。

### 技巧 2｜Claude Code 只读审计 Managed Agents 权限配置

**来源：** Anthropic [Claude Code v2.1.304](https://github.com/anthropics/claude-code/releases/tag/v2.1.304)，2026-10-19。

**一句话结论：** /claude-api managed-agents-secure 对比现有 Managed Agents 设置和 Anthropic 安全指南，本身不修改设置。

**具体怎么做：** ①升级到 v2.1.304+。②进入已配置 Managed Agents 的测试环境执行 /claude-api managed-agents-secure。③审阅权限、工具和安全建议差异，将必要变更交由管理员批准。④在隔离环境回归工具准入后再更新生产策略。

**适合什么场景：** Claude Code、Managed Agents、企业 Agent Harness。

**注意：** 仅审计配置，并不提供代码或机器人真机安全保证；并非所有个人本地 Agent 场景都适用。

### 技巧 3｜Codex 0.163.0 用 /config 对账，并在测试任务里验证中断语义

**来源：** OpenAI [Codex 0.163.0 Release](https://github.com/openai/codex/releases/tag/rust-v0.163.0)，2026-10-15，时间回补。

**一句话结论：** /config 支持跨类别搜索与可立即变更的设置；Turn 进行时可提交 follow-up，取消 Turn 会同时停止活跃 Code Mode Cell 与嵌套工具。

**具体怎么做：** ①codex --version 核对版本。②运行 /config 核查权限、网络和需要重启的设置。③对只读、无害的长任务在执行中发送 follow-up，再测试取消。④执行 git status --short 检查是否仍有未完成的文件修改，并跑独立回归。

**适合什么场景：** Codex CLI、长期任务、Code Mode、多工具调度。

**注意：** 取消不能回滚已经发生的文件、数据库或远程副作用，仍需隔离工作树与权限门禁。

---

## 经典论文回顾

### LOAM：2014 年的高频里程计—低频建图分层为何仍然重要

Ji Zhang 与 Sanjiv Singh 的 [LOAM: Lidar Odometry and Mapping in Real-time](https://roboticsproceedings.org/rss10/p07.html) 发表在 **RSS 2014**，DOI **10.15607/RSS.2014.X.007**。此前索引已有 LeGO-LOAM、LIO-SAM 和 FAST-LIO2，但尚未独立回顾**原始 LOAM**。

**核心问题：** 机械扫描三维 LiDAR 的点不是同一时刻采样，机器人运动会使一帧点云扭曲。直接扫描匹配成本高且对运动初值敏感。LOAM 将复杂的 SLAM 拆成频率不同的两部分：

    点云时戳 / 边缘和平面特征
        → 高频、相对粗的 LiDAR odometry
        → 扫描间运动估计与去畸变
        → 低频、更精确的 scan-to-map 配准
        → 低漂移实时三维地图

**关键数学与物理思想：** 根据局部几何提取角点与平面特征，构造点到线、点到局部面残差；高频线程解决及时运动估计，低频线程把更多地图信息用于慢速精细校正。原论文展示不依赖高精度 IMU 的实时里程计与地图融合，在 KITTI 等实验中达到接近当时离线批处理方案的精度。

**传感器假设与局限：** 需要足够可靠的扫描时序、外参和几何结构；平行走廊、重复墙面、动态遮挡会导致退化。原始 LOAM 并不自带今日典型的完整 IMU 紧耦合、鲁棒回环和长期地图生命周期管理，不能替代现代 LIO 方案。

**今天的遗产与后续替代：** LeGO-LOAM 将地面约束带进计算预算，LIO-SAM 加入紧耦合因子图，FAST-LIO/FAST-LIO2 使用更直接的高频滤波与点云关联；但高低频职责分离、激光运动补偿和几何退化审计仍具有工程价值。

**公开代码与复现：** [RSS 原论文](https://roboticsproceedings.org/rss10/p07.html)、[CMU 原作者记录](https://publications.ri.cmu.edu/loam-lidar-odometry-and-mapping-in-real-time) 是一手文献；[loam_velodyne](https://github.com/laboshinl/loam_velodyne) 属于历史社区 ROS 实现，**不是原作者维护的官方工业实现**。可用同一个 16 线 bag 对比禁用去畸变、禁用地图细化和完整流程，分别看 ATE/RPE、Hessian 退化、回环误差与 P95 耗时。

**对当前工程的重新解读：** 长走廊 16 线 LIO-SAM 抖动时，先排查点时间、IMU 与雷达外参、退化方向和图优化约束，而不是为了尝试神经地图而撤掉已经可靠的高频里程计。

---

## 今日结论

今天八项研究的共同点是：**可靠性不来自单一模型做得更多，而来自每一层明确知道自己拥有什么证据。** RTISSLAM-3D 明确声束物理，Micro-Localization 明确定位尺度与表面条件，SpatialBEV 在正确的位置读取地形特征，FCTS 使失败真正驱动课程学习，RAX 把探索结果编译成有前提条件和可验证证据的技能，RePlanMem 让关键事件而非固定时钟驱动记忆写入，MambaAct 把加速集中在确实昂贵的 Action Expert，VulnSAGE 让 AI 安全审计判断能够回到实际程序结构。

**一句话：先做好观测模型、失败归因、动作生命周期与验证契约，再追求更大的模型和更多计算预算。**

## 最值得深入研究或尝试复现的方向

1. **三维声呐 SLAM sidecar：** 在起伏地形比较声呐与 LIO 里程计、三维回环和错误对应。
2. **工位显微地面定位：** 分别测试灰尘、离焦、照明和温度漂移下的重复定位。
3. **SpatialBEV 命令响应：** 在预测移动位置查询局部 BEV 特征，与全局 embedding 的越野控制误差 A/B。
4. **FCTS 机器狗失败课程：** 保存失败位置、状态、地形裁片，锁定保留测试场地避免过拟合。
5. **RAX 机器人 Harness：** 先在仿真提供 read_state/safe_move/stop，技能保存前置条件和可重放成功证据。
6. **RePlanMem 记忆触发：** 与固定抽帧、视觉新颖度比较关键帧保留收益及缓存预算。
7. **MambaAct 端侧审计：** 单独测视觉编码/动作专家 P95，确认 ONNX/RKNN selective-scan 算子可用性。
8. **VulnSAGE C++ 告警：** 以真实历史 SAST 缺陷验证依赖切片、误报裁减与隔离 PoC。
9. **Agent 权限回归：** 比较 Copilot 信任目录、Claude 只读 Managed Agent 配置检查及 Codex Turn 取消后的工作区状态。

## 参考资料

**最新公开：** [arXiv Robotics](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/new)。

**SLAM/状态估计：** [RTISSLAM-3D](https://arxiv.org/abs/2610.22552) · [Micro-Localization](https://arxiv.org/abs/2610.22563)。

**控制/强化学习：** [SpatialBEV](https://arxiv.org/abs/2610.22900) · [SpatialBEV 项目](https://theairlab.org/spatial-bev-dynamics/) · [FCTS](https://arxiv.org/abs/2610.22619) · [FCTS 项目](https://narayananpp.github.io/fcts/)。

**机器人 Agent/VLA：** [RAX](https://arxiv.org/abs/2610.22496) · [RAX 源码](https://github.com/robot-agent-exploration/rax) · [RePlanMem](https://arxiv.org/abs/2610.22556) · [MambaAct](https://arxiv.org/abs/2610.22951) · [MambaAct 代码](https://github.com/giakhuyendihoc/MambaAct)。

**AI Coding：** [VulnSAGE](https://arxiv.org/abs/2610.23035) · [Copilot CLI v1.0.100](https://github.com/github/copilot-cli/releases/tag/v1.0.100) · [Claude Code v2.1.304](https://github.com/anthropics/claude-code/releases/tag/v2.1.304) · [Codex 0.163.0](https://github.com/openai/codex/releases/tag/rust-v0.163.0)。

**经典论文：** [LOAM RSS 2014](https://roboticsproceedings.org/rss10/p07.html) · [CMU 作者页](https://publications.ri.cmu.edu/loam-lidar-odometry-and-mapping-in-real-time) · [社区代码](https://github.com/laboshinl/loam_velodyne)。
