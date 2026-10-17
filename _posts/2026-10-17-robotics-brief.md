---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-17"
date: 2026-10-17 09:00:00 +0800
description: "新一批机器人论文：LIN-SLAM与线特征cuVSLAM、亚毫秒反射、倾转旋翼CBF、世界模型执行适配与环境潜变量、FastVLA动态压缩和WEAVE长任务评测。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-17

## 摘要

**检索基准：2026-10-17（Asia/Shanghai，星期六）早间。** arXiv Robotics 最近常规公开批次是**10 月 16 日，102 条**；Software Engineering 同日 **25 条**。以上是公开列表的条目数，包含交叉列表，不能全部算作初次投稿。周六尚无新常规批次。本期先检查过去 24 小时的一手来源，再扩展最近七天，按标题、arXiv ID、DOI、仓库和项目主页，与 GitHub 已登记 **1007 条**覆盖记录联合去重。

本期 8 条主动态的 v1 均在**10 月 14—15 日 UTC** 提交，已经超过严格的最近 24 小时，因而各项明确标注**时间回补**。其中两项直接解决 SLAM 工程：LIN-SLAM 将几何 LIO 与神经隐式后端分层，在 **Go2 + Orin NX + 16 线 LiDAR** 上完成长距离实时实验；Line-Augmented cuVSLAM 将直线几何真正纳入高频位姿求解和滑窗 BA，缓解货架和白墙环境点特征不足。

控制侧，亚毫秒 ROS 2 反射引擎把危险动作切换留在本地实时环；倾转旋翼 CBF 控制分配明确考虑舵机滞后与实际推力可行性。机器人世界模型方面，ExecutionBridge 区分规划参考轨迹和控制器实际执行轨迹；T2-z 在测试时从少量交互优化新环境的隐变量。FastVLA 则不重训 VLA，就按任务重要性动态压缩视觉 Token，真实 Franka 上端到端延迟降低 20%。AI Coding 研究 WEAVE 把多 PR 软件演进组合成可执行依赖 DAG，让长任务中间进度获得可验证评价。

实战技巧来自 GitHub 一手记录：**10 月 16 日开源许可证合规合并门禁 GA**，以及**10 月 15 日 Copilot 固定模型退役迁移提醒**。经典回顾为 PL-SLAM（2017 首版、2019 T-RO），与今天的低纹理线特征 VIO 互相对照。论文性能数字均为作者指定硬件和数据集下的报告，不是跨平台保证。

原始列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)。

## 1. LIN-SLAM：让高频几何LIO与神经隐式地图在边缘设备上分工

**时间回补：arXiv v1 于 2026-10-15 03:58 UTC 提交，投稿 RA-L。**

### 为什么重要

传统 LiDAR–Inertial Odometry（LIO）能稳定提供高频位置与姿态，但点云或体素地图不天然具备连续空间表示。神经隐式 SLAM 方便持续优化地图，代价是显著的 GPU 计算负担。如果把高频状态估计与复杂地图表示绑在一个神经网络里，控制环往往先被建图延迟拖垮。LIN-SLAM 将两者分开：几何 LIO 保证实时估计，神经后端承担连续地图、跟踪补充与全局细化。

### 算法模块与传感器假设

~~~text
LiDAR + IMU → 高频几何 LIO → 低延迟状态
                    ↓
            神经隐式Tracking/Mapping
                    ↓
               Global refinement
~~~

神经地图只是补充几何与长期优化，不能代替 LiDAR/IMU 的同步标定，也无法凭空恢复重复走廊的退化自由度。

### 实时性、结果与风险

作者在三种数据集的 **12 条序列**、32/64/128 线配置上比较，报告整体平均轨迹误差为受测方法中最低。真机使用 **Unitree Go2、Jetson Orin NX、16 线 LiDAR**，在 **1.47 km 室内轨迹**上同时在线定位和神经建图，最终端点闭合误差 **0.141 m**。这是端点误差，不是所有位置的 ATE。作者明确写明**代码将在论文接收后公布**，目前不能称为完整开源。

### 适合谁关注与工程落地启发

适合 16线/MID360-LIO、地下走廊、轻量边缘 GPU。若现有 FAST-LIO 已稳定，先旁路部署低优先级隐式地图，独立记录 GPU P95、里程计延迟、地图更新速率、回环修订与位姿跳变；神经地图负载上升时不能阻塞控制输出。关键指标不是渲染多漂亮，而是长距离几何轨迹是否真正改善。

来源：[LIN-SLAM](https://arxiv.org/abs/2610.21199)。

## 2. Line-Augmented cuVSLAM：线段在低纹理环境补的是几何约束，不只是更多特征

**时间回补：v1 2026-10-14 21:29 UTC。**

### 为什么重要

仓储货架、墙角和门框缺乏稳定角点，却具有大量直线。只检测线段并不等于增强定位，必须让线段状态、观测残差和优化 Jacobian 正式进入 VIO。该工作为 CUDA 视觉 SLAM 系统 cuVSLAM 增加线观测，不再并列运行另一个估计器。

### 算法模块与观测模型

~~~text
RGB-D → 点特征 + 线段
                ↓
线：Plücker坐标 / 4-DoF最小正交表示
                ↓
Cauchy鲁棒点到线残差 + 解析Jacobian
                ↓
逐帧Gauss-Newton位姿
                ↓
Schur补滑窗BA联合更新
~~~

当点特征稀少时，自适应信息权重提升线的贡献；禁用线观测就退回原来的点特征管线。线段沿自身方向通常弱约束，重复货架里的平行线也容易错误匹配，因此不能简单把线数当作定位信心。

### 实时性、结果与风险

在 RGB-D、SE(3) Umeyama 对齐且**不进行尺度修正**的对照中，TUM RGB-D Freiburg3 **22 条序列**平均 ATE 下降 **38.5%**，Replica **8 条**下降 **30.1%**；Replica 中位平移/旋转误差分别下降 **38.9%/66.4%**。摘要没有可直接推广的统一端到端 FPS，未确认完整修改版代码公开。

### 适合谁关注与工程落地启发

适合白墙长走廊、厂房、仓库和弱纹理 VIO。可固定同一数据集比较 point-only、固定点线权重、动态点线权重，记录点/线数量、线的方向分布、Hessian 最小奇异值、假匹配和掉跟踪次数。对于点云 LIO 的长廊退化，也可参考它的思路，优先审计哪种几何方向真正有约束。

来源：[Line-Augmented cuVSLAM](https://arxiv.org/abs/2610.20958)。

## 3. 亚毫秒反射引擎：接触危险时不要等待ROS 2控制器停启

**时间回补：v1 2026-10-15 14:00 UTC。**

### 为什么重要

常规 ros2_control 控制器切换可能需要停止并重新配置，适合普通任务模式切换，却难以处理突然碰触、关节触限与人机物理互动。论文通过 ROS 2 兼容的多模态控制器，让保护子控制器在实时路径中**无锁切换**，无需等待中间件重新配置。

### 算法模块与动力学假设

~~~text
Franka 1 kHz状态 / 接触力 / 关节限制
          ↓
    本地实时危险检测
          ↓
NORMAL → REFLEX → WAIT_FOR_RECOVERY
                         ↓
                 RECOVERY → NORMAL
          ↓
 Stop / Zero-G / 导纳 / 关节撤退 / 笛卡尔撤退
~~~

这是实时执行架构，而不是让上层 LLM 决定每次接触如何处理。作者仓库包含 reflex_engine、reflex_controllers、reflex_mc_impl 和 MuJoCo/真机配置示例。

### 实时性、鲁棒性与结果

论文在 Franka 机械臂报告控制器**切换时延小于 0.1 ms**，相比传统 ros2_control 对照快四个数量级以上；多阶段操作任务时间缩短 **3.5%**，峰值 jerk 降低超过三倍。0.1 ms 仅指切换本身，**不是**传感器识别、外力检测、控制输出和硬件动作全部结束所需的总时间。触碰阈值、误检率、执行器饱和及恢复行为仍需真机标定。

### 适合谁关注与工程落地启发

适合 Franka、ROS 2、双臂操作与人机协作。源代码 [franka_reflex_engine](https://github.com/RoboRef/franka_reflex_engine) 已公开，README 包含 MuJoCo Figure-8 和恢复例子。先在仿真中注入接触事件，测“接触→实际保护输出”的 P99，并验证恢复后不会重放陈旧动作。只提供 vx/vy/vw 的机器人不能直接复刻 Franka 的关节反射控制。

来源：[论文](https://arxiv.org/abs/2610.21913) · [代码](https://github.com/RoboRef/franka_reflex_engine)。

## 4. 倾转旋翼CBF分配器：上层期望Wrench未必是实际电机能生成的Wrench

**时间回补：v1 2026-10-15 UTC。**

### 为什么重要

全向倾转旋翼可生成六维力/力矩，但舵机有物理响应时间。当舵机实际倾角滞后于规划值时，名义推力分配矩阵得出的期望 wrench 可能根本不可实现。仅对上层轨迹加 CBF，并不能保证下层分配不超过电机能力。

### 算法模块与条件保证

~~~text
期望6D Wrench + 实际舵机角
        ↓
名义/实际配置失配与储备估计
        ↓
12个推力裕量约束
        ↓
6变量 Servo-rate CBF-QP
        ↓
差分推力分配与执行
~~~

文章在六通道分配映射非奇异时，将鲁棒 Wrench 可行性转成紧化的推力裕量，并给出条件性前向不变性：实际失配在储备覆盖内、初始状态可行且QP有合法输入。它不能证明任意未建模舵机卡死时仍然安全。

### 实验结果与可复现性

在 MuJoCo 圆周和 cartwheel 机动里，作者报告更低位置误差；**有扰动 cartwheel** 的 **1751 个记录样本**均满足期望 wrench 可行性，对照方案的违例率为 **60.8%—100%**。这些是仿真离散记录样本，并非真实飞行绝对安全证明。作者也特别指出，完整验证名义轨迹证书还需要名义状态与储备覆盖记录。尚未确认官方完整源码。

### 适合谁关注与工程落地启发

适合全向旋翼、安全 MPC、执行器控制分配。建议将 requested_wrench、measured_servo_angle、reserve_margin、thrust_saturation、QP_status、allocation_condition_number 同时记入遥测。与普通 quadrotor 的速度级 CBF 不同，这里保护的是**动力执行能力本身**。

来源：[原论文](https://arxiv.org/abs/2610.22057)。

## 5. ExecutionBridge：计划轨迹不是执行轨迹，世界模型不能直接混用两种语义

**时间回补：v1 2026-10-15 15:13 UTC。**

### 为什么重要

世界模型通常用参考轨迹生成未来，但真机控制器可能有延迟、限幅、平滑和打滑，同一计划在新控制器上会执行成不同运动。直接将模型输入的计划轨迹替换成预计执行轨迹并不一定有用：**计划描述下游控制参考；执行轨迹描述控制后的实际结果**，两者不是可互换的训练条件。

### 算法模块

~~~text
历史 Plan / Execution 成对轨迹
                  ↓
Controller-specific 执行特性
                  ↓
ExecutionBridge 调整Ego Latent Rollout
                  ↓
Planner、World Model与Reward Head保持冻结
                  ↓
用校正后的未来评价原始候选计划
~~~

作者并未简单要求重训整个世界模型，这对已有昂贵模型权重的工程系统很重要。

### 结果、假设与风险

在 NAVSIM 的 **10 个未见控制器配置**上，把计划直接替换成执行轨迹仅提高 **0.048 PDMS**，远不及 ExecutionBridge；后者在困难驾驶场景和多个冻结规划器上持续改善规划。当前论文未给出通用机器人闭环 FPS，也没有确认完整代码。控制器切换后仍需采集足够的计划—执行配对，若配对受定位误差污染，则校正潜变量也可能偏置。

### 适合谁关注与落地启发

适合世界模型、MPPI/轨迹规划、厂商仅开放 vx/vy/wz 的地面机器人。建议先建立命令响应侧路：保存计划、实际位移、实际速度、延迟与饱和状态；保持上层“参考轨迹”语义稳定，只在预测执行后果时修正，而不是直接把输出和目标混成一个状态变量。

来源：[ExecutionBridge 论文](https://arxiv.org/abs/2610.22041)。

## 6. T2-z：无需标签，用一次新环境交互调整世界模型的摩擦/质量隐变量

**时间回补：v1 2026-10-15 17:59 UTC。**

### 为什么重要

相同推块动作在橡胶/金属表面效果不同；相同机械臂动作面对不同物体质量也不同。这类因素有时不可直接从图像识别，也很难为训练数据逐个标注。T2-z 给世界模型加入可学习的环境 latent，在训练与部署中用**预测误差**来调整它。

### 算法模块和假设

~~~text
训练A：固定环境latent，优化世界模型
训练B：冻结世界模型，优化各环境latent
部署：冻结世界模型，初始化新latent
      收集一条或多条安全交互
      只优化新latent → 预测候选动作后果
~~~

隐变量可能混合编码摩擦、质量和人定义的环境约束，不能强行解释为物理仪表读数。新环境适配需要交互，意味着不是零风险且不总是零成本。

### 结果、鲁棒性与复现

作者在 **7 组仿真、4 项真机机器人任务**里，物体预测误差指标由 **15.20 降至 7.00**，动作成功率由 **33.73% 提高到 72.96%**；消融显示有时只需一次测试时交互。结果不能推广到所有材质或所有机器人。尚未确认完整官方权重和训练代码，不能给出一键复现命令。

### 适合谁关注与落地启发

适合操作世界模型、Sim2Real、可变载荷和未知摩擦。最小实验固定同一个预测器，分别使用 0/1/3 次受控交互估计环境 latent，记录预测误差下降与实际执行收益。试探动作必须先经过碰撞/力控安全层，不能让世界模型为“摸清环境”而自行执行高风险动作。

来源：[T2-z 原论文](https://arxiv.org/abs/2610.22364)。

## 7. FastVLA：按任务与时间动态裁剪视觉Token，真实机器人端到端延迟降低20%

**时间回补：v1 2026-10-15 16:17 UTC，WACV 2027 接收。**

### 为什么重要

VLA 在每次推理处理高分辨率多视角图像，视觉 Token 数量会主导 Transformer 成本。通用显著性不等于当前任务重要性，固定剪枝比例又会在简单阶段浪费计算、复杂阶段误删关键目标。FastVLA 提供**无需重训的、任务感知的动态视觉压缩**。

### 算法模块

~~~text
图像Token + 任务指令
       ↓
Task-to-Vision Attention分布
       ↓
Inverse-Simpson重要性均匀度
       ↓
在线滑窗校准Token预算
       ↓
压缩视觉上下文 → 原VLA Action Expert
~~~

它不是把视觉图像永久压低分辨率，而是依当前任务和控制时刻调整保留哪些 Token。

### 结果、风险和可复现性

作者在 OpenVLA、OpenVLA-OFT 和 CogACT 的 LIBERO/SIMPLER 任务上报告 backbone FLOPs 减少 **35%–59%**、Action Latency 降低 **9%–32%**，保持相近成功率。真实 Franka Research 3 上端到端推理延迟下降 **20%（1.25×）**。官方代码已公开：[jiuyixu25/FastVLA](https://github.com/jiuyixu25/FastVLA)。部署时必须计入 Attention 打分开销，以及关键物体被漏裁剪的风险；GPU 结果不能直接外推到 RK3588 NPU。

### 适合谁关注与工程落地启发

适合本地VLA、视觉频率较高的双臂任务和边缘GPU。固定同一批视觉数据与任务，比较全Token、固定比例裁剪、FastVLA动态预算的 P95 延迟、动作平滑度和成功率。观测或任务突然改变时要让旧 Token 重要性失效。

来源：[FastVLA 论文](https://arxiv.org/abs/2610.22146) · [源码](https://github.com/jiuyixu25/FastVLA)。

## 8. WEAVE：长时Coding Agent的验收单位不该永远只有单个PR

**时间回补：v1 2026-10-15 15:12 UTC。**

### 为什么重要

真正的大型软件变更通常先动基础接口、再迁移调用方、最后修改测试/部署，多 PR 之间存在前后依赖。把整个项目拆成独立 Issue 且只用最终 Pass/Fail 评分，会失去任务中间进展，也可能奖励错误顺序的“局部成功”。

### 算法模块与关键贡献

WEAVE 从**历史真实已验证 PR**提取 typed change loci，推断变化的依赖，将相关 PR 组装成有界可执行 DAG，再用**Graph Credit** 按测试和依赖一致性衡量部分进展。

~~~text
已验证PR历史 → 变更位置/类型提取
              ↓
       Dependency DAG 任务
              ↓
       Agent分层改动与测试
              ↓
   Graph Credit验证中间有效进展
~~~

作者在任务构造、Agent 评测、监督训练和强化学习实验中报告这比平坦评分更能衡量进度与提供训练信号；摘要未提供可跨模型泛化的统一绝对成功率，不能编造。

### 权限、安全与工程风险

依赖图自动推断可能漏掉数据库迁移、共享 CI、协议版本和跨仓调用。Graph Credit 也不能替代真实端到端回归；如果 DAG 的先后关系错，模型可能学到“测试通过但发布不可行”的顺序。当前未确认成熟的官方完整仓库。

### 适合谁关注与工程落地启发

适合 Codex、Claude Code 长时重构、ROS2 package 和 Spring Boot 多模块项目。选一个真实的三层改动：数据契约 → API/服务 → UI/调用方，要求每层有一个确定性的测试，而非重复生成长篇执行日志；独立节点可并发，最终必须统一工作树验收。

来源：[WEAVE 原论文](https://arxiv.org/abs/2610.22039)。

## AI Coding 实战技巧精选

### 技巧 1｜把Agent新增依赖的许可证检查加入PR合并规则

- **来源**：GitHub，2026-10-16，[Open source license compliance GA](https://github.blog/changelog/2026-10-16-open-source-license-compliance-generally-available/)。
- **一句话结论**：Agent 新增包不应只看能否编译；如果许可证不符合组织策略，应在合并前自动拒绝。
- **具体怎么做**：
  1. 在满足条件的 **GitHub Enterprise Cloud + Code Security** 仓库中设定企业 License Policy。
  2. 新建/修改 Ruleset，启用 **Require license compliance results before merging**。
  3. 通过一个引入不同许可证依赖的测试 PR 验证是否产生阻断与注释；确需例外时交由 **Enterprise Open-Source License Manager** 审批。
  4. 自研 Agent 推荐新包时，优先查询官方包许可证合规 API，再生成修改。
- **适合什么场景**：Codex/Claude 自动加依赖、企业 C++/Java 仓库、代码供应链。
- **注意**：GA 受 GitHub 计划及 Code Security 启用条件限制；结果不替代具体业务的法律判断。

### 技巧 2｜提前迁移Copilot工作流中将在11月退役的模型

- **来源**：GitHub，2026-10-15，[Copilot 模型退役官方公告](https://github.blog/changelog/2026-10-15-upcoming-deprecation-of-selected-github-copilot-models-in-mid-november/)。
- **一句话结论**：Copilot 计划于 **2026-11-16** 退役 Claude Opus 5、GPT-5.6 Terra 等模型；写死模型名的 Agent 路由需要提前验证替代模型。
- **具体怎么做**：
  1. 在自身项目执行示例搜索：~~~bash
     rg -n 'Claude Opus 4\.8|Claude Opus 5\b|GPT-5\.6 Terra' .github . 2>/dev/null
     ~~~
  2. 对匹配的实际配置做单独清点，不要对所有文本搜索结果机械替换；测试迁至 **Claude Opus 5.5** 或 **GPT-6.1 Sol / GPT-6 Luna**。
  3. 组织管理员核对 Model Policy 是否启用替代型号；以同一组真实任务比较成功率、费用和延迟后调整默认路由。
- **适合什么场景**：GitHub Copilot、固定模型的多 Agent、企业长时任务。
- **注意**：公告列有年度个人订阅的 Opus 4.8 例外；仅适用于 Copilot 的退役安排，不能外推到其他平台 API。

## 经典论文回顾

### PL-SLAM：点线融合为什么是低纹理仓库定位的长期有效思路

Ruben Gomez-Ojeda、David Zuñiga-Noël、Francisco-Angel Moreno、Davide Scaramuzza 和 Javier Gonzalez-Jimenez 的 **PL-SLAM: a Stereo SLAM System through the Combination of Points and Line Segments**，2017-05-26 首版公开、2019 年发表于 **IEEE Transactions on Robotics**，是结构化视觉 SLAM 的经典代表。

### 历史问题与数学/算法思想

早期立体视觉 SLAM 以角点和点描述子为主。白墙、仓库货架的角点不足时，系统容易失去可跟踪约束，而门框和墙线仍有丰富可重复观测。PL-SLAM 不只把线段加入前端，而是贯通里程计、关键帧、点线 Bundle Adjustment 与混合词袋回环：

~~~text
Stereo
 ├─ 点检测/匹配
 └─ 线段检测/匹配
         ↓
    Joint odometry
         ↓
   Point-Line BA
         ↓
   Point-Line BoW Loop
         ↓
    Map Correction
~~~

点与线不是同一观测：线段端点在图像边缘经常不稳定，沿线方向又可能缺乏约束。因此线残差与信息权重必须符合几何结构，不能仅根据“有多少线”推断可观测性。

### 当年意义、今天的延续和局限

作者在 KITTI、EuRoC 等数据集报告了低纹理环境更稳健的运行表现，同时保持实时。今天 Line-Augmented cuVSLAM 在这一思想上进一步使用 Plücker 几何、最小线表示、解析 Jacobian 和自适应信息权重，使线约束直接进入 CUDA 滑窗。后续的线/点/平面/IMU 联合优化继续扩展可观测约束，但重复货架、错误关联、运动模糊和回环假阳性仍然存在。

### 公开代码与复现

作者的 [PL-SLAM 源码](https://github.com/rubengooj/pl-slam) 使用 C++ 并附 KITTI 配置，许可证 **GPLv3**；仓库明确说明这是研究社区版，未包括论文的所有优化功能。最小对照：同一立体序列跑点-only、点线联合、禁用回环三组配置，对比 ATE/RPE、掉跟踪、CPU、误匹配、线方向分布。若现有 16线 LIO 在长廊退化，优先问“缺少哪些状态方向的观测”，再决定加视觉线、回环或主动视角变化，而不是无条件换算法。

来源：[2017 原始论文](https://arxiv.org/abs/1705.09479) · [作者开源代码](https://github.com/rubengooj/pl-slam) · [IEEE DOI](https://doi.org/10.1109/TRO.2019.2899783)。

## 今日结论

本期共同主题是**状态语义和物理约束比堆算力更基础**。LIN-SLAM 区分高频位姿与高成本神经地图；Line-cuVSLAM 把真正可观的线几何加到已有优化器。亚毫秒反射引擎把紧急切换留给本地实时层，CBF Tiltrotor 则证明上层期望控制与实际可分配推力并非一回事。

ExecutionBridge 区分计划与执行，T2-z 区分当前画面可见状态与未知环境物理条件，FastVLA 区分视觉显著性与任务相关性。这些不是增加更大模型就会自然解决的错误。WEAVE 同样提醒 Coding Agent：只有依赖正确且有确定性测试支撑的进展才应计入有效完成，冗长自述并不是证据。

**一句话：先把实时层、观测约束、执行器能力、环境不确定性和代码验收契约建对，再提高模型、采样和Agent并行规模。**

## 最值得深入研究或尝试复现的方向

1. **LIN-SLAM地图旁路**：16线LIO保持主控制输出，测试低频神经地图的Orin GPU P95与闭环误差，避免等待尚未公开的源码。
2. **点线VIO对照**：白墙/货架场景比较点、点线固定权重和动态权重，特别记录线平行时的几何退化。
3. **Franka实时反射**：按官方MuJoCo示例注入接触，测端到端保护P99与恢复状态机，验证不会重复执行旧动作。
4. **倾转旋翼CBF储备**：分别记录期望力矩、实际舵角和推力可行集；检查QP无解时的Fallback。
5. **计划—执行模型**：在只开放vx/vy/vw接口的机器人上学习命令延迟与实际响应，保持上层参考语义稳定。
6. **T2-z低风险适配**：用受控单次交互校准未知摩擦的预测器，比较0/1/3次更新，禁止高风险自由试探。
7. **FastVLA剪枝A/B**：任务条件Token预算与固定比例裁剪比较Latency P95、VRAM和真实成功率。
8. **WEAVE DAG验收**：将真实跨模块重构拆成有依赖的3–6个节点，每节点只保存必要测试结果与代码变更。
9. **GitHub许可证/模型治理**：新增依赖先查License Policy；Copilot固定模型配置在11月16日前完成替代版本验证。

## 参考资料

**最新论文列表**：[cs.RO](https://arxiv.org/list/cs.RO/recent) · [cs.SE](https://arxiv.org/list/cs.SE/recent)。

**定位与控制**：[LIN-SLAM](https://arxiv.org/abs/2610.21199) · [Line-Augmented cuVSLAM](https://arxiv.org/abs/2610.20958) · [Reflex Engine 论文](https://arxiv.org/abs/2610.21913) · [Reflex源码](https://github.com/RoboRef/franka_reflex_engine) · [Tiltrotor CBF](https://arxiv.org/abs/2610.22057)。

**机器人世界模型/端侧**：[ExecutionBridge](https://arxiv.org/abs/2610.22041) · [T2-z](https://arxiv.org/abs/2610.22364) · [FastVLA](https://arxiv.org/abs/2610.22146) · [FastVLA源码](https://github.com/jiuyixu25/FastVLA)。

**AI Coding与经典论文**：[WEAVE](https://arxiv.org/abs/2610.22039) · [GitHub License Compliance](https://github.blog/changelog/2026-10-16-open-source-license-compliance-generally-available/) · [Copilot模型退役](https://github.blog/changelog/2026-10-15-upcoming-deprecation-of-selected-github-copilot-models-in-mid-november/) · [PL-SLAM](https://arxiv.org/abs/1705.09479) · [代码](https://github.com/rubengooj/pl-slam)。
