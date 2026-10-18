---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-18"
date: 2026-10-18 09:00:00 +0800
description: "周末技术回补：Go2 拓扑导航、天空偏振绝对航向、BubbleCBF、安全自适应 MPC、移动参考系 MPCC、VLA 持续记忆与因果剪枝、Coding Agent 完整文件上下文。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-18

## 摘要

**检索基准：2026-10-18 09:00（Asia/Shanghai），星期日。**

最新常规 arXiv 批次是 **10 月 16 日（星期五）**：Robotics（cs.RO）共有 149 个列表条目，其中 89 条新提交；Software Engineering（cs.SE）49 个条目，其中 18 条新提交。最近 24 小时内没有新的常规论文批次。按规范逐级检查最近 24 小时、再扩展近 7 天；本期八篇主动态的 arXiv v1 均提交于 **2026-10-14 至 10-15 UTC**，因此全部明确标记为**时间回补**。性能数字均指作者特定设置，不能外推为任意机器人平台保证。

选题前读取了 GitHub master 的任务规范及 **1,018 条覆盖索引**，按规范化标题、arXiv ID、DOI、项目页和代码地址联合去重，没有重复报道 LIN-SLAM、FastVLA、T2-z 或最近发布的 WEAVE 等研究。

**今日核心：** AVALON 不要求机器人预先完成建筑全局 SLAM，利用人类提供的楼层拓扑和现场证据进行首次导航；天空偏振则在 GNSS/磁航向受干扰时补充绝对航向。BubbleCBF 把真实刹车能力纳入二阶动态安全集合，A-SLS 在 MPC 中预测未来能学到的动力学，MR-MPCC 把跟踪进度与参考路径的固定时间解绑。机器人基础模型 REKI 以极少 register token 保留近期动作记忆，VLA 因果分析通过少数关键注意力层减低 FLOPs。AI Coding 工作 CQ2-CARE 发现，在相同 Token 预算下，提供少数完整待修改源文件比对大量片段做复杂压缩更有帮助。

**AI Coding 实操**选三条可以马上操作的措施：10 月 19 日前检查 GitHub Copilot 即将退役的模型配置；仅按需要启用 OpenTelemetry 的身份或内容采集；在 Slack/Teams 中通过 @GitHub 跨多个仓库定位问题。**经典论文**回顾 Liniger 等人的 2015 年 MPCC 赛车系统，以对照今天机械臂移动参考坐标系跟踪。

[arXiv Robotics 原始列表](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering 原始列表](https://arxiv.org/list/cs.SE/new)。

---

## 1. AVALON：首次进入陌生楼宇，利用人类熟悉的拓扑代替预先全局建图

**时间回补：arXiv v1 于 2026-10-15 09:33 UTC 提交。**

### 为什么重要

机器人第一次进入建筑时没有自建全局地图，但楼层平面图、房间名称、门禁条件和通道关系往往早已为人类所知。AVALON 针对“人类熟悉、机器人陌生”的场景，把楼层拓扑与现场验证结合；不要求入场前机器人遍历整栋楼或做场景专用训练。

### 算法模块、传感器与假设

~~~text
楼层图 + 人类场所/权限线索
          ↓
分层 Topological Memory
          ↓
节点目标选择
          ↓
深度视觉 Point-Goal Navigation
          ↓
节点到达的物理证据验证
          ↓
局部重锚定 + 有门槛的记忆更新
~~~

机器人仍需要当前里程计、初始拓扑—里程计对齐和局部深度感知。人类可以提供不能由视觉直接判断的权限，却不能仅凭描述就证明通道物理可通行；门被堵住、临时施工等变化必须经现场观察验证。拓扑不等于占据栅格，两个地图产品应独立维护版本。

### 实验、实时性、鲁棒性与复现

在 Unitree Go2 的 12.81 m 任务中，AVALON + X-NavDP **5/5** 成功，耗时 46.4 s；比较的 DimOS-Go2 **4/5**、78.5 s；仅运行 X-NavDP 则五次全部超时。测试规模小、场景受限，不代表任意楼宇都可靠。作者没有提供跨设备统一 FPS；主要开销来自局部导航与节点确认。

重点风险是初始坐标对齐误差、对称走廊节点混淆、楼层转移和人类描述与现实矛盾。建议记录 node_id、arrival_evidence、odometry_revision、human_rule_revision、edge_validated_at。

### 适合谁关注与工程落地启发

适合 Go2、楼宇/矿井巡检、已有 CAD 平面图却缺少机器人全局 SLAM 的系统。最小方案是用语义拓扑指导全局目标，沿途以当前 LiDAR/深度图维护局部防碰和可达性，节点无法确认时主动请求新观测。

[论文](https://arxiv.org/abs/2610.21586)。

---

## 2. 天空偏振航向：通过 Rayleigh 模型获取 GNSS 与磁场之外的绝对 Yaw 证据

**时间回补：arXiv v1 于 2026-10-14 18:41 UTC 提交。**

### 为什么重要

IMU/LIO/VIO 的短时相对姿态可能很稳定，但长距离缺少回环时偏航仍会慢慢漂移。磁罗盘受金属和电机干扰，双天线 GNSS 也可能被遮挡。该工作使用屋顶偏振相机观测天空偏振方向分布，将其与太阳位置和 Rayleigh 单次散射模型拟合，提供独立的绝对航向。

### 算法模块、传感器假设

~~~text
偏振相机图像 + 位置/时间/太阳方位
          ↓
每像素偏振角 AoP、偏振度 DoP
          ↓
Rayleigh 模型预测偏振角分布
          ↓
偏振度加权全图误差
          ↓
全局搜索绝对 Yaw
          ↓
与 INS/VIO/LIO 的航向因子融合
~~~

低 DoP 的云层、建筑遮挡和树木区域应降权。模型依赖相机标定、天时地理和足够天空视野，因此不适合长期无天窗的矿井深处。与普通里程计不同，这类观测是绝对航向约束，而非直接输出连续 6DoF 位姿。

### 实验、风险和复现

三条城市道路真实数据以双天线 GNSS/INS 作参考，Yaw RMS 为 **0.718°–0.889°**，相对选定对照方法最多改善 **87%**。缺少可迁移的统一端侧 FPS。偏振角具有对称性，严重阴云和模型失配会令优化产生异常候选。

建议独立运行偏振定位 Sidecar，仅对高可信输出执行 gated heading update，记录 sky_valid_fraction、DoP_distribution、yaw_innovation、solar_model_residual；避免直接硬重置飞控姿态。

### 适合谁关注与工程落地启发

适合室外巡检车辆、GNSS 间歇失锁无人机和长时偏航漂移诊断。它能增加航向观测类型，但不能代替局部几何避障。

[论文](https://arxiv.org/abs/2610.20797)。

---

## 3. BubbleCBF：安全不仅是“离障碍够远”，还必须“来得及刹住”

**时间回补：arXiv v1 于 2026-10-14 20:24 UTC 提交。**

### 为什么重要

二阶动力学机器人可能在离障碍仍有空隙时，就已因速度过高、刹车能力有限而无法避免后续碰撞。简单的位置 SDF 约束不能自动保证“下一秒能停住”。BubbleCBF 针对二阶 control-affine 系统，从局部障碍几何构造**依赖位置和速度**的安全集合。

### 算法模块与理论边界

~~~text
SDF / 自由空间
       ↓
无碰撞球 Bubble 及其几何重叠
       ↓
二阶位置—速度联合安全条件
       ↓
Union-of-Intersections Safe Set
       ↓
QP Action Safety Filter
~~~

利用自由球二次几何，作者在指定的动力学、重叠和参数假设下证明过滤器连续、前向不变，并给出**有界输入可行性**的充分条件。保证并不覆盖地图过期、传感器严重延迟或动力学越出模型范围等情况。

### 实验、实时性和工程风险

论文在差速机器人未知环境自主导航中验证；摘要不提供跨平台通用碰撞率或耗时，因此不能据此宣称固定 100 Hz。最小复现实验可在二维 double-integrator 上固定障碍距离、改变当前速度，对比仅位置 CBF、高阶 CBF 与 BubbleCBF。除了是否碰撞，应统计 QP 不可行次数、制动裕量、P99 求解时间与最小净空。

风险包括错误连通的 Bubble、局部 SDF 变化与车体实际减速能力变化。动态障碍依旧需要运动预测和独立紧急制动层。

### 适合谁关注与工程落地启发

适合窄廊移动机器人、差速底盘与带加速度约束的无人车。核心启发：**安全集合必须随着速度和制动能力变化，而不是只做固定半径的障碍膨胀。**

[论文](https://arxiv.org/abs/2610.20895) · [作者项目与视频](https://existentialrobotics.org/bubblecbf/)。

---

## 4. A-SLS：GPU 鲁棒 MPC 把未来的系统辨识收益也纳入规划

**时间回补：arXiv v1 于 2026-10-14 20:55 UTC 提交。**

### 为什么重要

传统鲁棒 MPC 往往假定未知质量、摩擦或推力参数会在整个预测窗口内保持当前最坏不确定性，因此控制极为保守；但系统运动本身会带来信息。A-SLS 基于 System-Level Synthesis，将**未来可保证的参数学习**纳入鲁棒可达集传播，并在 GPU 上实时优化。

### 算法模块、动力学假设

~~~text
当前状态 + 参数不确定集
        ↓
候选控制与未来信息增益
        ↓
传播过程扰动/参数误差/估计更新相关性
        ↓
预测不确定集收缩
        ↓
鲁棒 Reachable Tube
        ↓
GPU SLS 优化与安全执行
~~~

关键是保留过程噪声、参数误差和估计器更新之间的相关结构，而非简单假定各量独立。结果仍依赖系统可辨识性、动力学模型和观测可靠性；系统若处于不可辨识工作点，不能提前把“未来必然学习到参数”记成已经获得的安全裕量。

### 结果、鲁棒性与可复现性

作者报告鲁棒管更紧且求解可实时运行，并展示四足控制规模：**61 个状态、8 个不确定参数、12 个控制输入**。真实 Crazyflie 通过在线识别一个未知动力学参数实现飞行稳定；摘要未给通用 P95 时延，不能直接外推 RK3588/Jetson。

最小 A/B 从双积分器或小 UAV 的质量、阻尼参数开始，比较固定最坏参数集和学习感知可达管，记录 tube_width、constraint_margin、parameter_posterior、deadline_miss。硬件上必须限制辨识激励，不能为获得信息而越过安全区域。

### 适合谁关注与工程落地启发

适合在线动力学辨识、PX4 及足式机器人的鲁棒预测控制。建议先验证“未来学得更快是否确实值得在当前承担少量探索代价”。

[论文](https://arxiv.org/abs/2610.20925)。

---

## 5. MR-MPCC：机械臂跟踪移动工件时，路径进度不应绑定死板的时钟

**时间回补：arXiv v1 于 2026-10-15 05:38 UTC；IROS 2026 接收。**

### 为什么重要

加工、打磨和探头跟踪的真正目标是贴近工件上的几何路径，不是无论工件是否移动，都必须在某一秒到达某一个绝对世界坐标。时间索引 MPC 遇到参考系突然运动、图像感知延迟或动作进度滞后时，容易增加轮廓误差。MR-MPCC 为机械臂引入**移动参考系的模型预测轮廓控制**。

### 算法模块和运动学接口

~~~text
移动参考框架内的 6DoF 路径
             ↓
参考框架位姿观测
             ↓
MPCC：路径进度 + 轮廓/姿态误差
             ↓
末端 Cartesian Twist
             ↓
受关节限位与安全约束的 RMRC
             ↓
UR5e 关节速度控制
~~~

路径参数 θ 可随真实执行进度调整；下层 constrained Resolved Motion Rate Control 使用关节 Jacobian 将末端 Twist 投射为可行关节速度。该分层并不允许任意速度执行，仍应检查速度、加速度、奇异性与碰撞。

### 实验与工程风险

作者使用 ROS2–MuJoCo 和 UR5e，借助电磁传感器测量并扰动参考坐标系；相较 PI 与 time-indexed tracking MPC，移动参照情形下轮廓与路径框架误差更小。摘要没有统一 FPS/收益数字，不把赛车 MPCC 的 50 Hz 当作本系统指标。

先固定相同路径，注入不同参考系平移、旋转及测量延迟，对比控制误差、进度跳跃、joint saturation、frame_age 和 P95 求解时间。路径坐标系的跳变也应具有显式 Version，以免旧参考动作误执行。

### 适合谁关注与工程落地启发

适合 UR5e/Franka、移动工件加工、移动坐标系下的精确操作。核心是将**几何进度**与**期望时间**分开。

[论文](https://arxiv.org/abs/2610.21292)。

---

## 6. REKI：2.4B VLA 用少量 Register Token 低成本记住上几个控制周期

**时间回补：arXiv v1 于 2026-10-15 16:34 UTC。**

### 为什么重要

许多 VLA 在每个动作块开始时只读取新图像与任务指令，忘记刚才是靠近、抓取还是撤离，容易在相邻姿态间震荡。完整历史视频上下文显存高、推理慢。REKI 将近期信息压缩到 Action Expert 的几枚持续 Register Token，而不是反复重跑整个历史。

### 模型架构和数据

~~~text
当前视觉 + 语言
       ↓
VLM 编码器
       ↓
Flow-Matching Action Expert
       ├─ 输出下一个动作块
       └─ 更新 Persistent Register Tokens
                    ↓
             下个控制周期复用
~~~

约 **2.4B 参数**，训练使用公开机器人、人类第一视角及视觉语言数据。Register 是短期工作记忆，不能替代具备对象 ID、位置版本和跨会话检索的长期地图。

### 结果、实时性与可复现性

作者报告在 LIBERO-Plus、RoboTwin Clean2Rand 与 RoboCasa365 表现有竞争力，Register 使姿态间来回震荡**约减少四倍**。完整公开数据整理、训练、推理、评测、部署代码与预训练/微调权重，因此可复现性明显优于只有项目预告的论文。模型规模不等于 RK3588 已经可跑，必须检查算子、量化、内存和真实端到端 P95。

**风险：** 急停、模式切换、定位重置后继续使用旧记忆会导致错误动作。应以 episode_id、observation_timestamp、action_chunk_id 管理缓存生命周期，关键模式切换时清空。

### 适合谁关注与工程落地启发

适合端侧 VLA、长动作块操作、减少短时重复决策。固定相同数据比较“无状态”“简单滑窗”“Register”三组，测成功率、震荡次数和整个推理链成本。

[论文](https://arxiv.org/abs/2610.22178) · [官方代码及权重](https://github.com/kyutai-labs/reki)。

---

## 7. VLA 因果分析：36 层跨注意力里只有少数层真正传递动作条件

**时间回补：arXiv v1 于 2026-10-14 18:06 UTC。**

### 为什么重要

以往模型加速常随机剪 Token 或层，未确认剪掉的连接是否真正影响任务动作。该研究用 Activation Patching 分析 π0.5、MolmoAct2、MolmoBot：从图像与语言进入 Action Expert 的因果信息集中在一段较窄的中后层跨注意力接口中。

### 方法、结果与限制

~~~text
视觉 / 指令 Token
        ↓
逐层 Activation Patching
        ↓
测量不同层对 Action Expert 的因果贡献
        ↓
保留重要 Action-Conditioning Interface
        ↓
减少跨注意力计算量
~~~

较早—中层的目标名词表示决定“选哪个物体”，较中—后层的空间信息改变动作方向；不同架构可能把空间条件放在文本或图像 Token 上。作者在 MolmoBot 只保留 **36 层中的 3 层**作为动作条件输入，推理 FLOPs **最多减少 33%**；3,000 次回合成功率为 **46.7% 对 46.9%**，并在真实机器人 π0.5 上检验迁移思想。

这不是完整系统延迟降低 33%，因为相机、视觉主干和执行仍占时间。结构性剪枝必须重新测未知任务、突发改指令与换目标时的失败模式，不能跨模型复制固定层号。

### 适合谁关注与工程落地启发

适合 VLA 高效推理与 Jetson 部署。先对固定模型运行逐层消融并测任务成功率，再与 Token 裁剪、量化和 KV Cache 联合比较，评估实际 P95 和输出动作质量。

[论文](https://arxiv.org/abs/2610.20750)。

---

## 8. Skip the Compressor / CQ2-CARE：复杂 Coding Agent 先选对源文件，再原样交给执行模型

**时间回补：arXiv v1 于 2026-10-15 01:21 UTC。**

### 为什么重要

大型仓库远超上下文长度。用摘要压缩源文件能省 Token，却可能改变或遗漏修复所需的完整条件分支、类型定义与源代码边界。检索相似代码片段也不一定能找准真正应修改的文件。CQ2-CARE 证明：相同 Token 预算下，**挑出少量待改文件并提供完整原文**，可能比复杂压缩更可靠。

### 方法与数据

~~~text
Issue / 错误描述
       ↓
选择 Must-Edit 候选文件
       ↓
完整源文件（无语义压缩）
       ↓
Coding Agent 编辑
       ↓
原仓库测试验收
~~~

在 **300 个 SWE-rebench** Issue、固定每题预算上，GPT-5.6 和 Claude Opus 5 使用完整文件选择的解决率为 **43.7% 与 46.7%**，两模型各比最佳压缩策略高 **6.3 个百分点**，较最佳检索策略分别高 **9.3 和 12.7 个百分点**。这是作者指定任务集与模型组合的结果，并不意味着全文读入越多越好。

### 工程与可验证性

根本区别是：检索先帮 Agent 判断哪些文件值得查看，执行时必须使用**与真实工作树一致**的代码，才能可靠生成 Patch。对于超长文件，可按精确行范围拆分并保留原始位置，不能把不完整摘要冒充源码。

最小 A/B 使用相同 C++/Java/ROS2 Issue、相同 Token 预算，分别比较片段检索、LLM 压缩、完整文件选择，记录 must-edit-file recall、Patch 应用率、最终测试成功率及每成功任务成本。不要为了这项方法再添加庞大文档或验收证据流水线。

### 适合谁关注与工程落地启发

适合 Codex、Claude Code、大仓重构和追求更低上下文管理复杂度的团队。**把精力用在正确文件定位，比把所有文件摘要得越来越漂亮更有价值。**

[论文](https://arxiv.org/abs/2610.21073)。

---

## AI Coding 实战技巧精选

### 技巧 1｜现在检查 Copilot 固定模型名，避免 10 月 19 日退役造成任务失败

- **来源：** [GitHub 官方退役公告](https://github.blog/changelog/2026-09-18-upcoming-deprecation-of-selected-github-copilot-models-in-mid-october/)，2026-09-18；本期为临期实操回补，不是当日发布。
- **一句话结论：** Copilot 将于 **2026-10-19** 退役 Gemini 3.7 Flash、GPT-5.5、GPT-5.4/mini、GPT-5 mini、Grok 4.5，固定模型路由应今天迁移。
- **具体怎么做：** ① 在实际配置目录运行 <code>rg -n 'Gemini 3\.7 Flash|GPT-5\.5|GPT-5\.4|GPT-5 mini|Grok 4\.5' .github .</code>；② 根据 GitHub 公告选择 Gemini 3.8 Flash、GPT-5.6 Sol/Luna、Grok 4.6 等替代；③ 管理员核对 Copilot Model Policy；④ 用固定任务检查正确性、延迟及费用。
- **适合什么场景：** Copilot CLI、IDE、企业工作流、硬编码模型的多 Agent。
- **注意：** 这是 GitHub Copilot 的日期，不能外推为其他 API 下线；历史文档不需要机械替换。

### 技巧 2｜用 Copilot OpenTelemetry 最小化采集，避免为监控而复制源码和密钥

- **来源：** [GitHub 客户端遥测官方更新](https://github.blog/changelog/2026-10-12-client-telemetry-user-attribution-and-configurable-capture/)，2026-10-12。
- **一句话结论：** 企业托管设置可分别管理 <code>telemetry.capture.identity</code> 和 prompts、responses、toolArguments、toolOutput、policyDetail 五类内容采集，默认关闭。
- **具体怎么做：** ① 检查受支持客户端 Managed Settings 中的 telemetry 配置；② 仅为了使用者归属时按官方 Schema 开 identity，不同时启用全文采集；③ 在测试会话确认 OTel 字段仅包含审批通过的用户与进程信息；④ 为允许的内容类指定受控收集端点与保留期限。
- **适合什么场景：** Copilot CLI、Copilot App、VS Code Agent Host、企业成本统计。
- **注意：** Tool Arguments 和 Tool Output 可包含源代码、用户路径或密钥；管理级配置优先于本地覆盖。

### 技巧 3｜多仓前后端问题直接在 Slack/Teams 同一线程交给 @GitHub 调查

- **来源：** [GitHub 官方跨仓支持](https://github.blog/changelog/2026-10-15-copilot-in-slack-and-teams-adds-model-and-repository-updates/)，2026-10-15。
- **一句话结论：** @GitHub 允许一条聊天跨多个已授权仓库创建 Issue、调查问题及跟踪 PR。
- **具体怎么做：** ① 确认 GitHub App 对前端与后端测试仓库均有授权；② 在 Slack/Teams 同一线程提出“@GitHub Investigate this issue using the code in our frontend and backend repositories”；③ 要求逐仓列出受影响文件与候选补丁；④ 每仓测试后再按依赖顺序合入。
- **适合什么场景：** 多仓 API、前后端契约变更、跨微服务排错。
- **注意：** 聊天上下文不等于跨仓原子操作，部署依赖和权限必须单独验收。

---

## 经典论文回顾

### Liniger / Domahidi / Morari（2015）：MPCC 让“沿路径前进”与“固定时刻跟踪参考点”分开

**历史位置：** *Optimization-based autonomous racing of 1:43 scale RC cars*，2014 年在线发表、2015 年刊于 *Optimal Control Applications and Methods* 36(5):628–647，DOI [10.1002/oca.2123](https://doi.org/10.1002/oca.2123)。2017 年 arXiv 公开稿并非首次发表日期。

### 核心问题与数学思想

传统定时追踪要求车辆在 t 秒处于参考轨迹的固定位置，稍一滞后就可能切弯。MPCC 把路径进度 θ 当成一个优化状态，主要惩罚 lateral contouring error 和 longitudinal lag error，并在动力学/道路边界下最大化前进进度：

~~~text
固定几何路径
     ↓
路径参数 θ + Contouring / Lag Error
     ↓
预测车辆动力学 / 轮胎模型
     ↓
线性化时变 QP
     ↓
求解控制命令和路径进度
     ↓
执行前缀 → 再优化
~~~

### 传感器、动力学、当年价值

原论文使用非线性车辆/轮胎模型及赛道、转向和驱动约束，在 **1:43 模型车**上实现 **50 Hz**，速度超过 **3 m/s**，包含漂移和避让。这证明了轮廓控制与路径进度联合优化可在嵌入式系统实时运行。**该频率不等于今天 UR5e 的 MR-MPCC 实测频率。**

### 今天仍在使用的思想与局限

将路径几何与时间进度分离，已影响高速车辆、无人机和机器人末端控制。今天 MR-MPCC 在此基础上进一步处理**路径参考系本身在移动**。经典方案仍依赖足够准确的动态模型，不自动解决 GNSS/SLAM 失效、动态障碍错预测、机器人关节奇异或分布外摩擦，因此后续增加了鲁棒 MPC、在线动力学学习和独立安全过滤。

### 开源、复现与工程重新解读

作者的 [alexliniger/MPCC](https://github.com/alexliniger/MPCC) 提供 C++ 和 MATLAB 实现。先对固定路径测 θ、contouring/lag error；再施加参考系旋转和运动，对照新 MR-MPCC。对于第三方仅有 vx/vy/vw 的机器人，应以真实闭环速度响应预测执行结果，不能把控制指令瞬间等价为真实机体速度。

[期刊论文](https://doi.org/10.1002/oca.2123) · [公开预印本](https://arxiv.org/abs/1711.07300) · [官方源码](https://github.com/alexliniger/MPCC)。

---

## 今日结论

AVALON 让人工拓扑帮助机器人第一次进入陌生建筑，但仍要求现场验证；偏振绝对航向从另一种物理信息源补强长时方向估计。BubbleCBF 把刹车能力加入安全条件，A-SLS 在 MPC 中显式计算未来知识的收益，MR-MPCC 则拒绝将实际路径进度死绑在时间线上。

REKI 在动作专家中以少量 Token 保存必要的近期历史；VLA 因果实验发现真正传递关键动作条件的层很少；CQ2-CARE 则展示了**某些不可压缩的信息（源代码原文）必须保持精确**。

这三类研究共同指向一条工程原则：**应该选择性地保存真实约束与必要信息，而不是任意提高模型复杂度，或为了省 Token 删除可能改变行为的证据。**

今天最紧迫的 AI Coding 操作是检查明天的 Copilot 模型退役配置，其后才是压缩遥测采集、保持多仓任务的权限和验收边界。技术能力与实际执行契约，始终需要独立验证。

## 最值得深入研究或尝试复现的方向

1. **Go2 拓扑优先导航**：用楼层图、节点确认和局部避障，测初始对齐偏差及对称走廊混淆。
2. **天空偏振独立航向 Sidecar**：在户外 VIO/LIO 旁记录可用偏振比例和 yaw innovation。
3. **BubbleCBF 刹车压力测试**：控制相同距离但不同速度，检查安全过滤与输入饱和条件。
4. **A-SLS 参数学习管**：未知质量/阻尼下比较固定最坏集合与学习感知可达管。
5. **移动参考系 MR-MPCC**：固定机器臂路径并注入工件位姿变化，对比几何误差和求解超时。
6. **REKI Register 生命周期**：急停、定位重置和任务切换必须使旧记忆失效。
7. **VLA Action-Conditioning 因果消融**：在不变权重与数据集下评估层重要性和真实 P95。
8. **CQ2-CARE 完整文件检索**：同 Token 预算比较压缩、片段、整文件的 Patch 成功率。
9. **Copilot 工作流维护**：清查明日退役模型、最小遥测、跨仓 @GitHub 授权。

## 参考资料

**最新列表：** [Robotics](https://arxiv.org/list/cs.RO/new) · [Software Engineering](https://arxiv.org/list/cs.SE/new)。

**导航与控制：** [AVALON](https://arxiv.org/abs/2610.21586) · [天空偏振航向](https://arxiv.org/abs/2610.20797) · [BubbleCBF](https://arxiv.org/abs/2610.20895) · [A-SLS](https://arxiv.org/abs/2610.20925) · [MR-MPCC](https://arxiv.org/abs/2610.21292)。

**机器人与 Coding Agent：** [REKI](https://arxiv.org/abs/2610.22178) · [REKI 代码](https://github.com/kyutai-labs/reki) · [VLA 因果分析](https://arxiv.org/abs/2610.20750) · [CQ2-CARE](https://arxiv.org/abs/2610.21073)。

**AI Coding 一手实操：** [Copilot 2026-10-19 退役](https://github.blog/changelog/2026-09-18-upcoming-deprecation-of-selected-github-copilot-models-in-mid-october/) · [Copilot Telemetry](https://github.blog/changelog/2026-10-12-client-telemetry-user-attribution-and-configurable-capture/) · [Slack/Teams 跨仓 @GitHub](https://github.blog/changelog/2026-10-15-copilot-in-slack-and-teams-adds-model-and-repository-updates/)。

**经典论文：** [MPCC 2015](https://doi.org/10.1002/oca.2123) · [作者代码](https://github.com/alexliniger/MPCC)。
