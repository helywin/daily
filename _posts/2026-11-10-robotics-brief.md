---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-10"
date: 2026-11-10 09:00:00 +0800
description: "BIM-LIO、Frontier 重排、CS-Pi、G1 推车、MR0 与 Agent 安全；增补 SAG2、开源 jevos、SAG 知识库，以及 T3 Code + Codex MCP / Skill 工程实操。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-10

## 摘要

**检索日期：2026-11-10（Asia/Shanghai，星期二）；检索基准约北京时间 08:58。** 已核验的 arXiv Robotics（cs.RO）最新常规公开批次为 **2026-11-09**，总计 103 条，其中 New submissions 54 条；Software Engineering（cs.SE）总计 44 条，其中 New submissions 19 条。列表总数含交叉收录、更新稿，不能全部作为首次提交计算（[cs.RO 原始列表](https://arxiv.org/list/cs.RO/new)，[cs.SE 原始列表](https://arxiv.org/list/cs.SE/new)）。

本轮首先检索最近 24 小时，主动态候选不足以覆盖全部高价值方向时，按规范扩展到最近 7 天。入选的八项工作原始 v1 提交于 **11 月 5—6 日 UTC**，均标为**时间回补**。已与仓库截至 11 月 9 日的 **1,282 条**历史覆盖条目，按论文标题、arXiv ID、DOI、项目主页与代码仓库联合核对，八项均为首次覆盖。没有将论文、项目页和仓库重复记作多条。

**今日主线：** 让地图更新先回答“观测能否区分定位误差与真实施工偏差”；让规划器按可达路径而非直线距离选择 Frontier；让生成式动作同时满足约束和原模型的高概率行为；在人形推车中把接触力与平衡统一处理；把人工接管作为带偏差的学习信号；让 VLA 长任务和工具调用保留状态与时效；对 Agent 权限验证不能只看插件是否仍显示启用。

**优先复现：** [CS-Pi](https://github.com/Sumo048/CS-Pi) 已公布核心采样器、YAML 实验和对照实现；[Meituan-Robotics-0](https://github.com/Meituan-Robotics/Meituan-Robotics-0) 已公开训练、评测、部署目录及多个模型入口。两者均不能因此被宣称已在本次运行中实际编译或训练。对现有 3D LiDAR 机器人，最值得先开展的轻量实验是 BIM-LIO 假匹配归因和 Frontier 路径代价重排。

**11 月 10 日 AI 栏目修订：** 增补三项可工程化 LLM 附属技术：SAG2 多跳证据检索、jevos-v5 本地决策模型、SAG/SAG-Wiki 知识库与 Codex MCP。实战栏目仅保留 Codex/T3 Code/Skill，提供实际接入、验收与许可证/云端依赖边界，不再引用其他 Coding CLI 的版本公告。

---

## 1. BIM-LIO：扫描与 BIM 墙体不一致，先证明能否区分定位漂移和施工偏差

**时间回补｜v1 2026-11-06 06:20 UTC｜arXiv:2611.09045**

### 为什么重要

在已知建筑 CAD/IFC/BIM 的配电室或多层楼宇巡检中，BIM 提供全局地图锚点。但激光扫描与图纸墙面错开时，原因可能是机器人定位偏移、墙面实际施工偏移、墙前新放置设备，或者整间房坐标发生变化。直接把残差解释成“地图错了”并更新 BIM，会污染长期地图；直接强拉机器人位姿到 BIM，又可能制造错误定位。

《When to Trust the BIM》把此问题建模为**故障归因可辨识性**，区分三类解释，并推导哪些观测几何能唯一判别。当观测只能证明“有异常”但不能确定原因时，系统保留候选解释，暂不沿歧义方向修改 BIM 或施加定位校正，等待更多独立参考再恢复。

### 算法模块、传感器与假设

~~~
LiDAR + IMU → LIO局部位姿
                 +
IFC/BIM设计墙面/房间结构
                 ↓
扫描—图纸残差和对应关系
                 ↓
位姿故障 / 墙面偏差 / 房间整体偏差
                 ↓
几何可辨识性判定
      ├─ 唯一可归因 → 有条件修正
      └─ 多解歧义 → 保留假设、暂停危险更新
                 ↓
新的独立参照进入 → 重新归因
~~~

这不是一个“RANSAC 阈值再大一点”的问题：有些平行墙、对称房间本就让不同故障具有同样观测。方法依赖 BIM 坐标注册、激光—惯性标定、场景静态结构及正确的数据关联。动态遮挡、错位地标、老旧图纸不能靠模型自行消失。

### 实验结果、鲁棒性与实时性

在预注册二维研究中，对**可检测但不可唯一归因**的情况，方法条件错误率 **0.83%**，相同回答率下的“不确定性弃答”基线为 **31.67%**。在 5,600 个可归因情况里，5,574 次给出唯一归因，且没有错误归因。实验室 IFC 地图的 168 个注入条件、SLABIM 三层数据 1,302 个条件中，均未报告误指向其他故障的归因。**这些是论文特定故障注入和归因指标，不是实际定位 ATE 或零失效证明。** 摘要未提供统一 ARM 端到端 P99。

### 可复现性、工程风险、适合谁关注

适合已有建筑图纸的轮式巡检、跨楼层 3D LiDAR 地图、施工变化检测。先固定 FAST-LIO 地图与 BIM 坐标，独立注入“机器人整体平移”“单面墙偏移”“房间整体偏移”，只读分析哪些数据不足以唯一判断。要求系统输出 UNKNOWN/AMBIGUOUS，不能强制输出唯一故障。重点测误归因、错误 TF 更新、局部可观测性和新增参考后的恢复率。**在归因可辨识前，不要自动把激光测量写成图纸修正。**

来源：[原始论文](https://arxiv.org/abs/2611.09045)。

---

## 2. 无人机 Frontier 重排：用带时间预算的 RRT* 估计真实路径，而不是相信欧氏距离

**时间回补｜v1 2026-11-06 15:03 UTC｜arXiv:2611.09561**

### 为什么重要

三维探索通常先生成许多 Frontier，再按未知信息收益和“到目标的距离”选择下一个目标。厂房货架、门洞、立柱与狭窄通道下，直线距离近的 Frontier 可能需要很长的绕行路线。对续航有限的无人机，这种错误排序很昂贵。

《Lightweight Path-Aware Frontier Re-ranking》采用**先便宜筛选、后有限预算精排**：先用轻量效用挑少数 Top-N 候选，再对候选用限时 RRT* 估算实际无碰撞路径成本，按路径长度重排，并复用选中 Frontier 的规划路径，避免再完整规划一次。

### 算法模块与传感器假设

~~~
3D LiDAR → OctoMap / 已知与未知体素
                     ↓
                 Frontier候选
                     ↓
        信息增益 + 粗代价选Top-N
                     ↓
           限时RRT*路径可行性
                     ↓
            重排并复用赢家路径
                     ↓
               本地轨迹跟踪
~~~

依赖 LiDAR 体素图正确反映障碍、机器人三维外廓、必要的膨胀和动力学可行性。RRT* 在时间受限时给出的是当前搜索到的可行路线，不是已证明的全局最短路；候选被粗筛掉也可能丢失真正最好的目标。

### 实验、实时性与工程风险

三种仓储式环境中，作者报告相对所选 Frontier 基线行驶路径**最多缩短 14.1%**；其中两个环境探索时间**最多下降 9.5%**，第三个环境仍有竞争力；地图细节与 OctoMap 基线接近。这些属于仿真中的相对指标，不是任意无人机的保证，也未提供可外推的机载 P99。

### 最小复现与适合谁关注

适合 LiDAR-only 无人机、主动探索、室内狭窄通道。可以不动当前 SLAM：固定相同 3D 地图、候选 Frontier 和 RRT* 随机种子，对比欧氏排序、A* 真实路径排序、Top-N 限时 RRT* 排序。报告总航程、覆盖率、候选评估 P95、失败规划次数及地图更新后的路径复用失效率。对自主探索而言，“减少重复全局规划”可能比换更复杂的网络模型更实用。

来源：[原论文](https://arxiv.org/abs/2611.09561)。

---

## 3. CS-Pi：冻结 Flow Policy，用“采样—投影—再加噪”处理训练时没见过的障碍

**时间回补｜v1 2026-11-05 20:01 UTC｜CoRL 2026｜arXiv:2611.08654**

### 为什么重要

生成式机器人策略能产生看似自然的动作，但临时新增一个障碍后，原策略可能直接穿过它。只在推理阶段用约束优化做投影，虽然几何上更安全，却可能把高概率动作改成原策略完全不擅长的动作；无条件拒绝采样又会在安全动作稀少时极慢。

CS-Pi（Constraint-Satisfying Flow Policy Sampling）结合投影的效率和拒绝采样的行为合理性。核心循环为 **Draw → Project → Renoise → 重新通过原 Flow Policy 去噪**，只修改采样器，不重训权重，也不要求约束函数可微。

### 算法模块

~~~
冻结Flow Policy → 生成完整动作x
                    ↓
               约束检测
          ├─ 满足 → 输出
          └─ 不满足
                ↓
          投影到可行集合g
                ↓
    按投影距离选择回滚噪声深度
                ↓
          部分再加噪+重新去噪
                ↓
       循环至安全或达到预算
~~~

作者源码中主要实现位于 cspi/core/algorithm.py，并提供 FlowPolicy、约束投影、同协议基线和 YAML 实验配置，核心调用如：

~~~python
from cspi import FlowPolicy, cspi
policy = FlowPolicy(my_velocity_fn, horizon=16, action_dim=2, normalizer=my_norm).condition(obs)
x, info = cspi(policy, my_constraint(policy), k=20.0, k_max=5, tau=0.01)
~~~

### 实验与风险

作者在七自由度机械臂货架取放中报告安全且完成任务的比例 **81.3%**，投影基线 **55.3%**；真实 Franka 为 **55% 对 40%**。两者不是形式化的现实零碰撞保证。源码存在达到最大迭代数后的最终投影回退，可能使动作较不符合原模型分布。推理总延迟还取决于重试次数、投影代价、IK、连续轨迹检查与执行器约束。

### 开源与工程落地

[官方源码](https://github.com/Sumo048/CS-Pi)、[交互项目页](https://sumo048.github.io/CS-pi_site/)均已核实。先运行二维避障示例，再把只读约束包装到自己的动作生成器：比较纯 Flow、仅投影、CS-Pi 的安全完成率、动作似然、迭代次数、P95/P99、轨迹内部碰撞，而非只验收离散终点。适合 Flow VLA、机械臂动作生成和动态障碍插入。

来源：[论文](https://arxiv.org/abs/2611.08654) · [官方仓库](https://github.com/Sumo048/CS-Pi)。

---

## 4. ForPC：不用额外力传感器，让 G1 在变载荷下更准确地推车

**时间回补｜v1 2026-11-05 20:21 UTC｜arXiv:2611.08664**

### 为什么重要

人形机器人双手推车后，双臂—推车形成受力耦合环。推动小车所需的手部接触力也在扰动机器人平衡，负载增加又会改变系统动态。只把期望底盘速度交给普通行走策略，很可能出现推车速度跟不上、左右手相互抵抗、抓持滑移与关节饱和。

ForPC 采用两阶段 RL：先训练在不同手部负载与上半身姿态下维持平衡的行走先验，再从本体传感估计**力潜变量和状态潜变量**，由残差控制器有界地协调手臂、腰和腿，调整推车速度。训练奖励同时惩罚左右手内部对抗、抓持滑移及执行器饱和。

### 算法模块与假设

~~~
目标推车速度 + G1本体状态
                ↓
        行走先验（负载鲁棒）
                +
       力潜变量 / 状态潜变量
                ↓
     Residual Whole-Body Policy
                ↓
       手臂、腰、腿协同修正
                ↓
        推车速度/平衡反馈
~~~

“无需外部力传感器”不等于知道真实接触力；潜变量估计依赖训练时的动力学随机化、机体传感质量和抓持条件。被动推车转向、地面摩擦和载荷分布都可能造成分布外失败。

### 实验、可复现性与工程落地

在作者仿真里，相比仅用行走先验，推车速度 RMSE 最多减少 **68.2%**，多弯路线横向误差最多减少 **74.2%**。完全仿真训练后，策略无需针对特定载荷调参就在真实 Unitree G1 上推动**载荷至 30 kg 的小车，以 0.5 m/s 行进**。这些不代表任意路面、任意小车或长期稳定成功率。项目页已公开，完整训练权重与可构建源码仍需按作者发布状态核实。

建议在仿真中固定推车几何、轮地摩擦、载荷位置，比较普通步行先验与残差力控；真机先从轻载、限速、失去抓持自动停止开始。适合人形物流和受控接触搬运。

来源：[论文](https://arxiv.org/abs/2611.08664) · [项目及演示](https://roboforpc.github.io/)。

---

## 5. Q-OIL：人的接管并不总是最优动作，但可以作为强化学习的探索线索

**时间回补｜v1 2026-11-05 18:44 UTC｜CoRL 2026｜arXiv:2611.08576**

### 为什么重要

真实机器人在卡住时由人短暂接管，是最现实的改进信号之一。然而，常见仿真会把人类接管建模成即时且最优的专家纠正；作者研究的真实用户常常在**进度停滞之后**才介入，动作还可能并非最优。

Q-OIL 不将每次人类纠正都当成标准答案，而是对接管迁移施加**乐观探索奖励**，引导机器人更愿意尝试被人纠正过的状态邻域。使用解耦 Critic 防止乐观奖励错误回传到接管前状态而破坏学习稳定性。

### 算法模块

~~~
环境运行 → 识别停滞/人接管
                   ↓
           接管前后Transition
                   ↓
      乐观Bonus仅作用于干预迁移
                   ↓
       解耦Critic估值并限制传播
                   ↓
           策略优化与再次探索
~~~

### 实验和局限

作者在仿真与真实机器人上报告比竞争基线**相对高 10%–50% 的任务成功表现**，并在两项双手 VLA 后训练中展示收益；项目页称人工工作量约减少三成。不同任务口径不可合并为统一百分点收益。乐观奖励若过大，可能引导机器人反复靠近危险接触；现实接管也需要明确的权限和紧急停止通路。

### 可复现性、适合谁关注

[官方项目](https://weirdlabuw.github.io/qoil/)含交互演示，但标明完整代码 **coming soon**。目前可先把自己记录的人工接管时间戳、机器人此前进度、纠正片段与之后结果结构化，离线比较“全部当专家演示”与“按接管位置探索”的数据效率。适合机器人在线学习、VLA Post-training、人工辅助恢复；不能把探索奖励直接接入无安全隔离的真机动作层。

来源：[论文](https://arxiv.org/abs/2611.08576) · [项目页](https://weirdlabuw.github.io/qoil/)。

---

## 6. 美团 Meituan-Robotics-0：跨 12 种本体的桌面 VLA，配合 Rollback 和持久事件记忆

**时间回补｜v1 2026-11-05｜arXiv:2611.08577**

### 为什么重要

大规模 VLA 不只是视觉语言预训练，更需要将不同机器人本体的动作统一到可执行接口，并处理推理延迟、失败纠正、长期任务暂停与恢复。

Meituan-Robotics-0（MR0）面向**固定底座的桌面操作**。数据包含 **1.47 亿视觉语言样本、15,060 小时机器人轨迹、12 种本体**。三阶段训练是：离散 FAST 动作 Token 与视觉语言联合预训练 → MMDiT 连续 Flow Matching 中期训练 → 真实任务上的演示和人工纠正后训练。

### 算法模块

~~~
视觉+语言+动作数据
        ↓
FAST离散动作Token预训练
        ↓
MMDiT连续动作块 Flow Matching
        ↓
SFT / DAgger类真实任务后训练
        ↓
统一末端执行器动作接口
        +
异步Action Chunk融合
        +
事件Monitor → Memory Manager → Planner
        ↓
执行回执与条件变化时再规划
~~~

**Rollback** 将被人替换掉的失败策略片段与相应纠正片段配对，供 CFG-DAgger 同时利用正负反馈，无需为这些片段额外学习价值函数。事件驱动 Agent 在目标暂时不可用时保留待办条件，条件恢复后再继续任务，这一点尤其适合长序列操作。

### 实验指标和边界

| 评测 | MR0 作者报告 |
|---|---:|
| RoboTwin 2.0 综合成功率 | **93.6%** |
| RoboTwin 专门仓库模型 clean/randomized | **93.22% / 93.88%** |
| RoboDojo 平均成功率 | **14.63%** |
| Ethernet 插线，CFG-DAgger Rollback 后 | **70%** |
| 三个真机任务、配对 HG-DAgger 后均值成功率 | **78%**，对照 π0.5 为 **69%** |

这些属于不同数据协议，不应将 93.6% 宣传成所有机器人操作的通用能力。尤其 RoboDojo 14.63% 表明跨分布泛化仍十分有限。其训练数据包含授权来源和仿真，不能假定全部数据可自由商业再分发。

### 开源、实时性与工程风险

[Meituan-Robotics-0 官方 GitHub](https://github.com/Meituan-Robotics/Meituan-Robotics-0) 当前已公开 mr0、train_scripts、eval_scripts、deployment、tests、GETTING_STARTED.md 以及 Hugging Face 模型入口；[官方项目页](https://meituan-robotics.github.io/Meituan-Robotics-0/)也可访问。尚未在本轮实际下载权重、训练或验证具体 GPU P99。

适合跨本体动作模型、桌面机械臂、受限 Agent 任务管理；不应直接用于轮式导航或机器狗登梯。建议先运行仓库提供的 RoboTwin 评测，并单独测异步动作块的采样时间戳、过期丢弃、延迟与任务恢复。

来源：[论文](https://arxiv.org/abs/2611.08577) · [官方代码](https://github.com/Meituan-Robotics/Meituan-Robotics-0)。

---

## 7. 连续体机器人接触估计：只有驱动腱测量时，为什么几何约束比更复杂 EKF 更有效

**时间回补｜v1 2026-11-06 18:53 UTC｜arXiv:2611.09877**

### 为什么重要

腱驱连续体机器人可进入弯曲狭窄区域，但接触可能发生在任意柔性段位置，电机侧只读得到腱张力/长度。研究证明，**不限制接触支撑位置时，接触力到腱测量的映射至少存在七维零空间**，因此没有估计器能仅凭相同信息唯一定位接触点。这是结构性不可辨识，而不是 EKF 增益没调好。

如果外部墙体几何已知，可以用不可穿透和接触互补条件收缩可行接触集合。作者提出约束 Moving Horizon Estimation（MHE），每个采样周期解一个 QP，并给出接触模式内的局部稳健稳定性分析。

### 算法模块

~~~
腱长 / 腱张力 / 驱动状态
           +
已知障碍几何、不可穿透约束
           ↓
接触互补与局部可观测性
           ↓
滑动窗口Constrained MHE
           ↓
接触位置、接触力与状态
~~~

### 实验、实时性与边界

在两节连续体机器人抵住并沿墙滑动的**有限元仿真基准**中，接触定位误差 **0.9 mm**，接触力误差 **0.22 N**；调优的带状态投影 EKF 分别是 **65 mm** 与 **0.72 N**。40 次随机模型失配实验中，MHE 在接触力和位置误差上均优于对照。无接触时并无优势。文中“每样本一个 QP”不等于任何 ARM 硬件都满足实时截止时间；结果尚非完整实体医疗/工业连续体机器人验证。

### 可复现性、工程风险与适合谁关注

适合柔性机械臂、导管式设备、狭窄通道检测以及接触状态估计研究。先用已知墙面/未知墙面的成对测试，比较 EKF 和 MHE，再注入障碍几何误差、摩擦失配、腱迟滞。只有约束本身可信时，估计才会真正受益。工程启发与 BIM-LIO 相同：**当测量本身无法区分多种物理解释时，不能靠更激进的滤波器强行输出唯一答案。**

来源：[原论文](https://arxiv.org/abs/2611.09877)。

---

## 8. Agent Harness 安全：插件仍在运行，不代表权限检查仍按正确顺序执行

**时间回补｜v1 2026-11-06 07:19 UTC｜arXiv:2611.09088**

### 为什么重要

AI Coding Agent 的安全规则分散在宿主程序、配置、插件、Hooks 和 MCP 中。某个“禁止编辑文件”的插件显示为 Enabled，不代表所有编辑请求都一定经过它。

研究《When Routine Operations Break Architectural Pattern Relationships in LLM Agent Harnesses》分析了五个已发布 Harness、十四个独立插件，以及 Guardrail Enforcement Point、Autonomy Controller、Blackboard 相关的五类架构关系。某些情况下，仅重新应用插件或保存允许规则，就改变了执行顺序或状态生命周期；**插件仍显示启用，但禁止的编辑实际执行成功**。

### 技术机制

~~~
请求 → 工具路由 → Guardrail → 工具执行
          ↓（重配或插件重载）
实际顺序可能变化 / 拦截状态丢失
          ↓
表面规则仍启用，实际违规写入成功
~~~

研究重点不是再增加一份抽象政策，而是验证**运行时决策路径和历史状态变化**是否始终保持约定。不同部署的正确实现可能需要不同顺序和状态保持策略，不存在一个适合所有 Harness 的插件排列口诀。

### 实验、权限与可验证性

论文对受支持的重配置操作和部署路径进行系统测试，并给出实际禁止编辑被执行的案例；它不是对所有 Coding Agent 产生同一漏洞概率的统计，也不意味着只要有插件就一定会越权。

### 复现与工程落地

适合 Codex/Claude Code、MCP、Subagent 多级委托、自研 C++ Agent Harness。使用无害临时仓库：启用只允许读取、禁止编辑受保护文件的 Hook/插件；分别在**首次启动、修改 Allow 规则、插件重载、会话恢复、Worktree 切换**后执行同一拒绝用例，检查文件哈希是否变化。测试应由**独立于 Agent 的外部脚本**记录，不允许 Agent 同时编辑保护规则和验收器。这里应验证“拒绝确实生效”，而不是只检查配置页面显示 Enabled。

来源：[原论文](https://arxiv.org/abs/2611.09088)。

---

## AI / LLM 附属框架与开源工程组件

**本栏为 11 月 10 日增补的工程专题，不将已有项目当成今日首次开源。** 只选择能查到真实仓库、模型或部署入口的技术，并区分“已核实仓库/命令”和“已实际运行”。以下示例均为按作者文档整理的复现步骤，本次没有替读者运行模型或消耗 Codex 额度。

### 组件 1｜SAG2：不用 Embedding 建索引，用 BM25 + Jev 进行多跳证据检索

**项目与代码：** [SAG2 论文](https://arxiv.org/abs/2610.22588) · [SAG-Benchmark/sag2 官方实现](https://github.com/Zleap-AI/SAG-Benchmark/tree/main/sag2) · [完整复现 README](https://github.com/Zleap-AI/SAG-Benchmark/blob/main/sag2/README.md)。

**它解决什么问题？** Agent 查技术文档、跨文件故障链、长报告时，只返回语义相似的一段文字往往不够；真正的答案可能需要先找到一个实体，再通过该实体关联到第二、第三份证据。SAG2 的路线是“问题 → 证据段落 → 扩展词 → 新证据”，不在索引时调用 LLM，也不构建 Embedding 向量库。

~~~text
原始文档 → SQLite FTS5 / BM25 索引（无 LLM 调用）
                        ↓
问题检索 Top 候选 → Jev 对原始问题的证据贡献打分
                        ↓
提取扩展词 → 继续 BM25 检索 → 去重与重新打分
                        ↓
返回可追溯的原文片段（不是直接编造答案）
~~~

作者在各 1,000 道题的测试里报告 MuSiQue、2WikiMultiHopQA、HotpotQA 的 **R@10 分别为 86.62%、97.43%、99.00%**；EnterpriseRAG-Bench 的 470 个标注问题、511,962 份文档上，文档 R@10 为 **81.10%**。这里 R@10 是原始证据召回率，**不是最终问答正确率**；MuSiQue 也是方法开发集，不能把它当完全独立的盲测。

**最小可执行步骤（Linux，Python 3.11+、uv、C 编译器）：**

~~~bash
git clone https://github.com/Zleap-AI/SAG-Benchmark.git
cd SAG-Benchmark/sag2
uv sync --frozen
# 下载固定 Benchmark 数据并建索引：不调用模型
uv run python scripts/run_sag2_benchmark.py --download --index-only --dataset musique
~~~

默认高分路线在**查询时依赖 Jev API**。官方示例使用 OpenRouter 的 `typesafe/jev-1.13`，需要单独配置 API Key；不能把“零模型索引成本”误写为“端到端完全本地”。

项目还提供 `--mode local --reranker qwen` 的本地 Qwen3-Reranker-0.6B 路线，权重需提前下载。作者在对应 MuSiQue 消融中报告本地 Qwen 两轮扩展 R@10 **74.18%**，低于 Jev 对照约 **86.6%**；不要暗示替换后完全复现云端分数。

**适合什么场景？** 用于 Codex 对技术规范、历史故障、设计资料做跨文档证据检索，尤其适合“先检索后引用原文”的开发研究流程。先取自己掌握答案的 30 个跨文档问题，对比 `rg/BM25`、SAG2+Jev 与本地 reranker，量化证据 Recall@5、全证据命中、一次查询费用与 P95。

**工程风险：** SAG2 Benchmark 是可复现算法/检索实验入口，并非自动可插入所有 Coding IDE 的成熟知识库；需要作为工具或 MCP 包装后才能参与 Codex 工作流。

### 组件 2｜jevos-v5：开源 Jev 类小型判断模型，本地 CPU 提供 yes/no、选项与分数

**项目与权重：** [feder-cr/jev 源码](https://github.com/feder-cr/jev) · [jevos-v5 Release](https://github.com/feder-cr/jev/releases/tag/jevos-v5) · [Hugging Face 权重](https://huggingface.co/feder-cr/jev)。

首先区分两个名字：**TypeSafe Jev 是单独提供的云端决策模型；jevos 是第三方开源替代实现，不是 Jev 官方开源权重。** jevos 将一句文本/结构化状态和若干判断规则转换为 `noul`（yes 概率）、`choice`（分类）或 `score`（刻度）结果，避免为简单分流调用一次大型生成模型。

作者发布了 MIT 许可证源码、OpenVINO INT8 权重、GGUF、Linux/Windows/macOS 预编译服务。以 Core Ultra 7 255H 16 线程测试为例，报告单次决策延迟约 **28–130 ms**；v5 版本说明报告 yes/no 主要评测分数 **78.9%**、Agent 指令数据约 **74.0%**。这些是作者选定的测试集及设备结果，不代表对任意未知规则达到相同准确率，也不应和不同任务上的 Jev 分数直接混用。

**Linux 最小运行方式：** 从上述 Release 下载 Linux x64 压缩包及 `jevos-v5-openvino-int8.zip` 后：

~~~bash
tar -xzf jev-linux-x64.tar.gz
cd jev
unzip ../jevos-v5-openvino-int8.zip
./jev serve
~~~

默认本地地址为 `127.0.0.1:8017`，适合 CPU 常驻；Linux x64 预编译包要求对应系统库（Release 指明 glibc 2.35+），约 1 GB 内存起步。验证独立 API：

~~~bash
curl -s http://127.0.0.1:8017/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{"model":"jev-latest","state":"日志显示机器人定位模块连续三次丢帧",
       "questions":{"needs_review":{"type":"noul",
       "instructions":"是否存在值得人工复核的定位异常证据？"}}}'
~~~

**适合什么场景？** Codex 工具调用前的低成本任务分类、日志分流、证据相关性初筛和失败告警；可将分数附带来源后传给主 Agent。强制安全权限仍由确定性代码控制，不能仅用模型概率放行高风险操作。

**与 SAG2 的真实兼容边界：** jevos 暴露 `POST /v1/systemone`，SAG2 官方云端示例使用 `/api/alpha/decisions`。两者协议及返回结构未被证明完全相同；**本次没有验证 SAG2 直接将 BASE_URL 改为 jevos 就能工作**。要集成应开发并测试薄适配器，并在同一证据集合重做 Recall@K、延迟和成本 A/B。不能把 API 风格相似宣传为“本地无损替换 Jev”。

### 组件 3｜SAG 与 SAG-Wiki：为 Codex 配一个能追溯原文的知识检索层

**两个项目不是同一套索引实现：** [Zleap-AI/SAG](https://github.com/Zleap-AI/SAG) 是事件—实体关系及查询期动态关系扩展的知识库应用，索引时需要 Embedding/事件抽取模型；[SAG-Wiki](https://github.com/Zleap-AI/SAG-Wiki) 使用 SAG2 的 SQLite FTS5/BM25 检索路线，建索引本身无需 LLM 和 Embedding。不要因为名字相近，就将 SAG2 测试分数直接算作原始 SAG 产品实测。

**最适合 Linux + Codex 的已核实链路：SAG Docker + 官方 CLI + MCP + Skill。** SAG 本地服务启动不要求先填模型密钥，但要执行 Embedding 索引、关系抽取和回答，需要配置实际模型服务。

~~~bash
git clone https://github.com/Zleap-AI/SAG.git
cd SAG
docker compose up -d --build
# Web: http://localhost:3000  API: http://localhost:8000/docs
~~~

建立知识源并完成索引后，在同一 Linux 主机安装官方 CLI，再接入 Codex（Node.js ≥ 20.19）：

~~~bash
npm install --global @zleap-ai/sag-cli
sag mcp test
sag agent connect codex
sag agent status
codex mcp list
~~~

原仓库还提供随 CLI 附带的知识检索 Skill，可参考 [SAG MCP 指南](https://github.com/Zleap-AI/SAG#MCP-guide) 安装。Codex 当前通用个人 Skill 目录为 `~/.agents/skills`，仓库级为 `.agents/skills`；请按当前 Codex 环境检查 Skill 是否实际被发现。

**SAG-Wiki 另一条路线：** 项目提供 Rust/Tauri 桌面、独立 CLI 和 [Codex Skill](https://github.com/Zleap-AI/SAG-Wiki/blob/main/cli/skills/sag/SKILL.md)，支持 `sag add` / `sag check` / `sag "问题" . -m 5`；但其 README 当前列出的 npm CLI 预编译发行平台主要是 macOS Apple Silicon 与 Windows x64。**Arch Linux 不应假定直接安装即可获得可用二进制**，先检查发行版支持或自行构建。

**如何判断值不值得集成？** 拿 30 个真实工程问题做对照：Codex 直接 `rg`、SAG 事件—实体索引、SAG2 多跳检索。要求每条回答都能打开原始文件及对应片段，统计错误引用、跨文档证据召回、索引更新成本和平均查询时延。不要为仅有几十个源码文件的简单项目额外部署完整知识库。

**安全边界：** MCP 只暴露需要的知识源；不要把整个 HOME、SSH 私钥或生产密钥目录加入索引；远程服务需鉴权，并按实际权限范围限制文档访问。

---

## AI Coding 实战技巧精选

本栏改为 **仅面向 Codex 的效率工具、可复用 Skill 和实际工作流**；不再使用其他 Coding CLI 的版本修复公告凑数。

### 技巧 1｜T3 Code 管理本机 Codex：手机继续任务，独立 Worktree 避免互相污染

- **来源**：[pingdotgg/t3code 官方仓库](https://github.com/pingdotgg/t3code) · [安装说明](https://github.com/pingdotgg/t3code/blob/main/README.md) · [远程访问指南](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md) · [Worktree 设置](https://github.com/pingdotgg/t3code/blob/main/docs/user/project-settings.md)。
- **一句话结论**：T3 Code 是 Codex 的跨设备操作界面，不需要再装一套“新的编码模型”；把不同任务安排到不同 Worktree，手机查看进度和审批，不要让两个任务改同一工作树。
- **具体怎么做**：
  1. 主机上已有 Codex CLI 时先检查 `codex --version` 和登录状态。Arch 可安装 `yay -S t3code-bin`，或直接用 `npx t3@latest` 试运行。
  2. 在 T3 Code 中为同一仓库创建两个独立 Worktree/线程，例如“定位模块修复”和“只读代码审查”，确认两者 `git status --short` 互不影响；检查项目 Worktrees 设置中的路径和子模块策略。
  3. 如需手机操作，按照文档使用 `t3 up` 配置 T3 Connect 或仅在受控局域网/Tailscale 访问；在手机选择自己的主机环境，不要直接暴露未鉴权的本地服务到公网。
  4. 完成任务后先审查 Diff 和必要测试，再人工合并；比较单工作树串行与双 Worktree 的冲突次数、人工切换成本和真实完成时间。
- **适合什么场景**：Codex + Arch Linux、手机/电脑跨设备、多 C++/ROS2 工程、多个独立任务。
- **注意**：并行线程仍然会消耗相应 Codex 使用额度，T3 Code 不会凭空增加订阅限额；远程主机需要保持可访问。文中没有替你运行任何 Codex 任务。

### 技巧 2｜把 SAG 接到 Codex 的 MCP，再用原文证据回答跨文档问题

- **来源**：[SAG 官方 MCP / Codex 指南](https://github.com/Zleap-AI/SAG#MCP-guide) · [Codex MCP 命令说明](https://learn.chatgpt.com/docs/cli/reference)。
- **一句话结论**：相比让 Codex 反复通读一堆 PDF、设计文档或历史说明，先通过检索工具返回可追溯片段，再让 Agent 查对应源码与执行测试。
- **具体怎么做**：
  1. 按上方 SAG 组件步骤启动容器，添加一个**小范围**知识源并完成索引，不要一次导入整个主目录。
  2. 使用 `sag mcp test`、`sag agent connect codex`、`codex mcp list` 确认工具确实出现在当前 Codex 配置里。
  3. 给 Codex 一个跨两份文档才能回答的问题，要求“先返回两个原始文件的证据位置，再判断结论”；同时运行 `rg` 基线。
  4. 检查证据是否真实存在、查询时延和新增文件被重新索引后能否检索到，再决定是否长期启用。
- **适合什么场景**：GB28181/ROS2 技术规格、长项目设计文件、历史 Bug 分析、Codex 研究型任务。
- **注意**：工具能检索到相关文本不代表它是当前版本的正确实现；必须结合 Git 当前分支、运行配置与必要测试判断。

### 技巧 3｜为 Codex 建一个十行级 Skill：改动后验证，不再靠长篇 AGENTS.md 堆规则

- **来源**：[Codex Skills 官方说明](https://learn.chatgpt.com/docs/customization/overview) · [Codex Skill 构建文档](https://learn.chatgpt.com/docs/build-skills)。
- **一句话结论**：把常用的“限定修改范围 → 运行最小相关测试 → 查看 Diff”打包为 Skill，只有需要时再加载，避免每轮 Prompt 重复铺满项目规范。
- **具体怎么做**：
  1. 在仓库创建 `.agents/skills/verify-change/SKILL.md`。
  2. 填入下面这份最小 Skill：

~~~markdown
---
name: verify-change
description: When code changes are complete, verify the smallest relevant build/test and inspect the diff.
---

1. Inspect git diff --check and git diff --stat first.
2. Run only the build/test commands relevant to changed modules.
3. Check that existing public APIs and error semantics still pass.
4. Report changed files, test result, and remaining failures.
5. Do not modify tests to conceal failures; do not auto-commit or push.
~~~

  3. 在新 Codex 会话中用 `$verify-change` 显式触发，选择一个小改动，检查 Skill 是否被加载及真正运行了相应测试。
  4. 与每次都粘贴长提示词的方式对照，比较上下文占用、无关文件修改和验收遗漏；确认有效后再推广给其他仓库。
- **适合什么场景**：Codex CLI、C++/ROS2、多模块工程、长期任务和共用 Skill。
- **注意**：Skill 是操作指导而不是权限沙盒；复杂 CI、安全发布和跨仓库写操作仍须有独立执行权限。不要因为本例出现 Skill，就额外生成大批无价值日志与验收脚本。

---

## 经典论文回顾

### Random Sample Consensus（RANSAC）：Fischler & Bolles，Communications of the ACM，1981

**原始发表**：Martin A. Fischler、Robert C. Bolles，1981 年 6 月，*Communications of the ACM* 24(6):381–395，[论文 DOI](https://doi.org/10.1145/358669.358692)；[作者机构原始发表记录](https://www.sri.com/publication/artificial-intelligence-pubs/random-sample-consensus-a-paradigm-for-model-fitting-with-applications-to-image-analysis-and-automated-cartography-2/)。

### 核心问题与关键思想

几何模型拟合时，部分特征匹配完全错误。使用全部观测做最小二乘，即使大部分点正确也可能被少量离群点严重拉偏。RANSAC 假设存在一定比例的内点，从随机最小样本构建模型，用全体观测的一致性计数筛选，再用内点重新估计模型。

~~~
特征对应 / 点云观测
          ↓
随机最小样本 → 候选变换 / 直线 / 单应
          ↓
残差阈值 → 内点集
          ↓
对多次候选按一致性评分
          ↓
内点精化 / 几何复核
~~~

给定内点概率 w、每个最小样本需要 s 个点、希望至少一次全内点采样的概率 p，理想独立采样下所需迭代数近似为：

n ≥ log(1-p) / log(1-w^s)。

这个公式对样本独立性、内点率估计和模型退化非常敏感，不能当作实际运行时间保证。

### 历史位置与今日价值

RANSAC 将“在大量错误观测下仍可形成模型假设”变成计算机视觉、PnP、基础矩阵、LiDAR 位姿配准的基础工具。它支持强离群点环境，但不理解观测是否真的**能够区分两种物理原因**：例如 BIM 墙体错开究竟是机器人位姿偏了还是墙真的建歪了。RANSAC 可能选出内点最多的错误解释。因此本期 BIM-LIO 的贡献不是替代 RANSAC，而是补充其没有解决的故障可辨识性。

### 假设、已被扩展的部分和可复现性

传统硬阈值 RANSAC 对噪声尺度敏感，极低内点率时采样开销巨大；平面或共线几何可能导致退化。后续 PROSAC、LO-RANSAC、MAGSAC++、USAC 等方法在采样、局部优化和阈值稳健性上继续发展。

[OpenCV calib3d](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html) 提供现代几何估计工具；[MAGSAC 作者代码](https://github.com/danini/magsac) 可供对照，它们不是 1981 年原始软件的直接复刻。

建议在同一组视觉回环配对上控制 10%、30%、60% 的错误匹配，比较最小二乘、普通 RANSAC 和 MAGSAC++ 的相对位姿误差、错误内点、运行 P95。进一步构造平行墙 BIM 歧义，即使 RANSAC 一致性很高，也检查能否正确输出“不能唯一归因”。

### 工程重新解读

**一致性强不代表模型解释唯一，残差小也不代表全局姿态可信。** 现代 SLAM 应将鲁棒配准、几何可辨识性和全局图约束作为三类不同问题。

---

## 今日结论

今天新公开工作中，工程意义最强的并不是“某模型成功率更高”，而是清晰界定了系统何时应该相信一个结果。BIM-LIO 对多解几何选择弃答而非强行地图更新；Frontier 重排让候选的路径成本接受真实可行性检查；CS-Pi 要求动作同时满足外部约束与原策略的行为分布；ForPC 把推车力与平衡联系起来；Q-OIL 承认人类接管带有延迟和次优性；连续体机器人接触估计证明部分观测问题本身无唯一解；Agent Harness 研究则提醒开发者，只看“安全插件已启用”远远不够。

**今日最值得动手：** 先用 [CS-Pi 仓库](https://github.com/Sumo048/CS-Pi) 跑二维约束采样与纯投影对照，再用一套现有 3D LiDAR 地图做 BIM/走廊歧义实验，最后检查 Coding Agent 在插件重载、路径切换后的拒绝规则是否仍然有效。对于 MR0，先复现实验 Benchmark 和工具时序，再讨论真实机器人部署。

**AI 工程技术补充：** SAG2 解决跨文档证据扩展，jevos 提供可本地化的轻量判断，但必须明确 TypeSafe Jev 云端服务与独立开源替代的性能差别。SAG 可通过 MCP 向 Codex 提供可溯源知识，T3 Code 用于跨设备控制与隔离 Worktree；最小 Skill 则将关键回归动作按需加载。推荐先针对 30 个真实问题和一个具体仓库做 A/B，不要为了“最新技术”给简单工程叠加不必要的框架。

---

## 最值得深入研究或尝试复现的方向

1. **BIM-LIO 归因可辨识性**：在有 IFC/CAD 的楼层注入位姿偏差、墙面偏差和房间整体偏差，测是否在歧义时正确拒绝更新地图。
2. **Frontier 路径代价重排**：固定同一张 3D 障碍图，比较直线距离与限时 RRT* 真实绕障代价，报告探索总路程和 P95。
3. **CS-Pi**：使用公开代码对比无保护、投影、重采样与 CS-Pi，重点看约束满足、策略似然和最坏延迟。
4. **ForPC 推车力控**：在 MuJoCo G1 上逐步增加推车负载，分析双手内部力、足底滑移和速度跟踪。
5. **Q-OIL 人工干预学习**：采集干预前停滞、干预动作与恢复结果；离线验证乐观奖励是否错误回传到危险状态。
6. **MR0 桌面 VLA**：固定 RoboTwin 评测协议，观察异步动作块时效、Rollback 正负监督与事件驱动任务恢复。
7. **连续体机器人 MHE**：用已知与未知墙面几何分别测试接触位置可辨识性，再比较 EKF 与约束 MHE。
8. **Agent Harness 失效回归**：对插件重新加载、允许规则更新和 Worktree 切换建立独立拒绝测试，检查实际文件哈希。
9. **SAG2 多跳检索**：以自己掌握证据的 30 个跨文档问题，对比 BM25、SAG2+Jev 与本地 Qwen 重排的 Recall@K、成本和查询 P95。
10. **jevos-v5 本地判断**：在 Linux CPU 上运行 `/v1/systemone`，分别测真假判断、误报率、冷启动与 P95；不用模型分数直接决定高权限动作。
11. **T3 Code + Codex + Skill**：为两个独立任务创建 Worktree，通过 T3 Code 管理会话，配置只读检索 MCP 与 `verify-change`，测实际完成时间、无关改动和测试遗漏。

---

## 参考资料

**最新原始批次：** [arXiv Robotics 2026-11-09 列表](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering 2026-11-09 列表](https://arxiv.org/list/cs.SE/new)。

**SLAM、探索与接触状态估计：** [BIM-LIO 可辨识性](https://arxiv.org/abs/2611.09045) · [LiDAR UAV Frontier 重排](https://arxiv.org/abs/2611.09561) · [连续体机器人约束 MHE](https://arxiv.org/abs/2611.09877)。

**动作生成、控制和机器人学习：** [CS-Pi](https://arxiv.org/abs/2611.08654) · [CS-Pi 源码](https://github.com/Sumo048/CS-Pi) · [ForPC](https://arxiv.org/abs/2611.08664) · [ForPC 项目](https://roboforpc.github.io/) · [Q-OIL](https://arxiv.org/abs/2611.08576) · [Q-OIL 项目](https://weirdlabuw.github.io/qoil/)。

**具身 VLA 与 Coding Agent：** [MR0 论文](https://arxiv.org/abs/2611.08577) · [MR0 源码与模型](https://github.com/Meituan-Robotics/Meituan-Robotics-0) · [Agent Harness 架构失效](https://arxiv.org/abs/2611.09088)。

**AI / LLM 附属框架：** [SAG2 论文](https://arxiv.org/abs/2610.22588) · [SAG2 代码与评测](https://github.com/Zleap-AI/SAG-Benchmark) · [jevos 开源模型](https://github.com/feder-cr/jev) · [jevos-v5 权重](https://huggingface.co/feder-cr/jev) · [SAG](https://github.com/Zleap-AI/SAG) · [SAG-Wiki](https://github.com/Zleap-AI/SAG-Wiki)。

**Codex 工程实操：** [T3 Code](https://github.com/pingdotgg/t3code) · [T3 Code 远程连接](https://github.com/pingdotgg/t3code/blob/main/docs/user/remote-access.md) · [SAG 官方 MCP 接入](https://github.com/Zleap-AI/SAG#MCP-guide) · [Codex Skills](https://learn.chatgpt.com/docs/customization/overview)。

**经典论文：** [Fischler & Bolles 1981 RANSAC DOI](https://doi.org/10.1145/358669.358692) · [SRI 机构发表记录](https://www.sri.com/publication/artificial-intelligence-pubs/random-sample-consensus-a-paradigm-for-model-fitting-with-applications-to-image-analysis-and-automated-cartography-2/)。
