---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-03"
date: 2026-10-03 09:00:00 +0800
description: "周末最新公开批次聚焦玻璃可导航建图、信念空间规划、策略感知 MPC、执行接口 Sim2Real、安全人形恢复、多机器人探索与选择性澄清 Coding Agent。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-03

## 摘要

今天是周六。截至 2026-10-03 早间，arXiv Robotics 最新常规公开批次为 2026-10-02，共 107 条；Software Engineering 同日为 31 条。由于周五公开批次中的 v1 实际都在 10 月 1 日 UTC 提交，今天入选的论文统一标为“时间回补”，不把 arXiv 的公开批次日期包装成论文原始提交日期。[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

今天 SLAM / 导航最值得关注的是 GlassGuard 和 BLT*。GlassGuard 直接针对机器人导航里最棘手、又很容易被常规 LiDAR 地图“看漏”的玻璃：视觉基础模型负责给出玻璃掩码，结构化 3D 线索生成可度量平面，再用不依赖深度的投影几何做多视角验证，并将玻璃作为可修订的全局地图假设长期维护。BLT* 则把 Informed RRT* 的“只在可能改进当前解的区域里搜索”推广到 belief space，让数字孪生中的点云定位不确定性真正进入路径规划，而不是先规划几何路径、再被动承受定位漂移。

控制侧今天有两条非常接近真实产品问题。ReCo 不试图重新辨识一套精确的四足全身动力学，而是先把 RL locomotion policy 的命令响应训练得更一致，再学习“命令到真实闭环响应”的简化模型交给 MPC；EIDA 则更进一步，把 Sim2Real 的焦点从机器人底层动力学挪到 execution interface：只学习目标平台收到速度命令后，机体到底怎么位移、策略最终又会看到什么速度反馈。对于只能使用 vx / vy / wz 或厂商 gait mode 的第三方机器人，这两条路线都比重做底层控制器现实得多。

无人机方向，LiDARFlow 用经典势流 / panel formulation 构造局部无碰引导场，结合在线 LiDAR 障碍表示做完全 onboard 的实时避障；OpenSpace Lab 的 IROS 2026 探索方案则强调全局预算：单机用地图补全预测优先探索高价值未知区域，并随剩余时间显式考虑返航约束，多机再通过共享地图与意图减少重复搜索。它们分别代表“低成本局部反应”和“有资源预算的全局探索”两层规划。

安全控制方面，VAPS 给动态人形动作增加 Continue / Abort / Fall 三层策略，不再假设 nominal tracking policy 一旦偏离参考还能自己救回来。每个控制周期先估计继续动作和主动中止是否仍然可行，再按“尽量完成动作、做不到就安全终止、再不行则尽量保护关键部位”的顺序降级。这种显式安全降级链，比把所有安全行为蒸馏进一个黑盒策略更容易验证和回滚。

AI Coding 主动态 CONTRA 解决的不是“代码写得够不够强”，而是需求本身存在多种合理解释时，Agent 到底什么时候应该问。它只保留会真正改变程序行为的问题：对一个候选问题分别假设两种 plausible answer 生成程序，再在共享输入上执行，如果稳定产生不同外部行为，才认为这个问题值得打断开发者。ClarifyCodeBench 上它相对最佳基线 macro-F1 提高 13.88 个百分点，并已经提供 Claude Code 插件。

最近通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic、Google 与 xAI 的官方公开入口，没有发现 10 月 2 日需要新增覆盖的通用旗舰正式发布；GPT-6.1 Sol、Gemini 4 Argon、Claude Sonnet 5.5 已在前几期覆盖，因此今天不重复旧发布凑数。

## 1. GlassGuard：导航地图不能把透明玻璃当作“自由空间”

**时间回补：v1 提交于 2026-10-01 17:31 UTC。**

### 为什么重要

透明和强反光玻璃是 LiDAR 导航非常危险的一类失败模式。激光可能直接穿透玻璃，地图里于是出现本不该存在的自由空间；也可能产生离散、错误回波，使几何后端拟合出完全错误的墙面。对导航系统而言，“没看见障碍”和“在错误位置造出障碍”都会造成真实碰撞风险。

GlassGuard 的重要性在于，它没有把玻璃处理做成一次性的语义 mask，而是把玻璃平面作为具有几何位置、朝向、置信度和生命周期的地图实体。

### 算法模块

流程可以概括为：

~~~text
camera image
    ↓
foundation vision glass mask
    ↓
structural 3D cues
    ↓
metric glass-plane hypotheses
    ↓
depth-free 2D projective geometry checks
    ↓
multi-view consolidation
    ↓
revisable global glass map
    ↓
navigation / collision map
~~~

视觉负责回答“哪里像玻璃”，结构几何负责回答“它在 3D 中到底是哪一个平面”，后续多视角观测再不断验证或推翻已有假设。

### 传感器与地图假设

官方 ROS 2 实现需要注册后的 LiDAR 点云、状态估计和相机图像，实验中使用 TARE autonomy stack，但接口并不绑定某一种 SLAM。也就是说，FAST-LIO、LIO-SAM 或其他能提供稳定位姿与 registered scan 的系统都可以作为底层几何来源。

关键假设是相机能给玻璃足够的视觉证据，而且位姿误差不能大到让跨视角投影验证失效。

### 实时性与结果

论文在 9 个 building-scale 场景、超过 1 小时和 2.1 km 的机器人行程中评估。全景设置的玻璃覆盖率达到 85%；在相同 pinhole 输入下达到 82%，而对比方法不高于 61%；错误体素数量每帧减少约 5–17 倍。

项目页给出的完整系统显存约 1.5 GB，单帧端到端处理约 0.74 s，并通过 perception / mapping 两进程重叠执行。因此它更适合低频“语义几何地图修正”，而不是把玻璃网络塞进 20–100 Hz 的主 LIO 前端。

### 鲁棒性与工程风险

最值得借鉴的是“玻璃平面允许被以后观测推翻”。真实建筑里窗户、玻璃门和镜面很容易被局部视觉误判，如果一帧检测结果永久写死到 occupancy map，同样会造成假障碍。

工程上建议把玻璃作为独立 layer，至少保存：

~~~text
plane_id
pose / normal
visual_confidence
geometric_support
observation_count
last_seen
map_revision
~~~

规划层可以把高置信玻璃当硬障碍，中置信玻璃当高代价区域；低置信假设继续等待新视角验证。

### 可复现性

官方项目页和 ROS 2 代码已经公开，接口也相对清楚，是今天最适合直接动手的 SLAM / 导航项目之一。

### 适合谁关注

室内巡检、商场 / 写字楼 / 车站机器人、玻璃隔断密集环境、LiDAR SLAM、希望给现有 occupancy / ESDF 增加透明障碍语义层的团队。

### 工程落地启发

对现有机器人不必改 SLAM 主链。先把 GlassGuard 做成 sidecar：订阅相机、位姿和 registered cloud，单独输出 glass planes，再由 costmap 插件进行膨胀和风险分级。这样即使玻璃模块失败，也不会污染原始几何地图。

[论文](https://arxiv.org/abs/2610.02110) · [项目页](https://glassguardproject.github.io/) · [代码](https://github.com/glassguardproject/GlassGuard)

## 2. BLT*：把 Informed RRT* 从几何空间推进到“定位不确定性空间”

**时间回补：v1 提交于 2026-10-01 16:21 UTC。**

### 为什么重要

传统路径规划默认机器人知道自己在哪。真实数字孪生定位却经常存在不确定性：有些路线几何上更短，却经过重复走廊、少特征区域或视角不好的位置，最终定位 covariance 会快速放大。

BLT*（Informed Belief Localization Trees*）直接在 belief space 中搜索，让路径长度、碰撞风险和“走到这里以后还能不能可靠定位”成为同一个规划问题。

### 算法模块

BLT* 从 RRT* / Informed RRT* 出发，但节点不再只是位置 x，而是位置分布。论文使用高斯 belief，并用 2-Wasserstein 距离衡量两个 belief state 的接近程度。

~~~text
digital twin + localization information
          ↓
sample Gaussian belief states
          ↓
belief-space steering
          ↓
probabilistic collision constraints
          ↓
W2 nearest / rewiring
          ↓
informed subset after first solution
          ↓
lower-cost localization-aware path
~~~

一个重要的工程优化是预计算测量信息，使 steering / rewiring 不需要每次重新模拟完整观测序列。

### 传感器与地图假设

论文场景基于 semantic digital twin 和 point-cloud localization。核心规划假设之一是 isotropic Gaussian belief，因此目前更适合单峰、不确定性可以用一个尺度近似的情况。

如果真实定位是强各向异性——例如长走廊沿轴向几乎不可观，而横向约束很强——或者已经出现多峰重定位假设，一个 isotropic Gaussian 会丢掉非常关键的结构。

### 实时性与鲁棒性

实验显示，在多数地图上 BLT* 更快找到初始可行解，并保持有竞争力的 cost convergence。它真正解决的是大尺度 belief-space sampling 的搜索效率，而不是替代高频局部避障。

### 可复现性

当前 arXiv 页面没有给出成熟开源代码入口。复现时可以先不做完整 BLT*：给现有 RRT* / Informed RRT* 的 state 加一个离线 localizability scalar 或 covariance surrogate，比较“最短路径”和“定位友好路径”在真实 SLAM 回放中的漂移。

### 工程风险

最大的风险是规划器相信的 localization model 与真机不一致。digital twin 中“这里应该有很多可定位结构”，不代表现场仍然一样。

规划状态最好额外保留：

~~~text
belief_covariance
measurement_information_age
map_revision
predicted_localizability
actual_estimator_residual
~~~

在线发现模型长期高估定位质量时，应重新学习或直接放大 belief margin。

### 适合谁关注

数字孪生导航、BIM / 工厂地图、GNSS-denied 长距离机器人、希望把 SLAM 可观测性真正放进路径规划的团队。

### 工程落地启发

对于长走廊 / 楼梯机器人，最有价值的第一步不是完整 belief-space planner，而是把 LIO 的 Hessian / covariance / localizability 变成 planner cost。一条稍长但能经过墙角、立柱、反光标志的路径，往往比纯几何最短路径更可靠。

[论文](https://arxiv.org/abs/2610.01972)

## 3. ReCo：不要让 MPC 去猜一个“响应不稳定”的 RL 步态控制器

**时间回补：v1 提交于 2026-10-01 12:51 UTC。**

### 为什么重要

四足 + 机械臂做连续操作时，上层 MPC 往往把底盘当成一个可预测的运动系统。但实际 RL locomotion policy 对同一个 vx / vy / wz 指令的响应会随步态相位、接触状态、载荷和随机化参数改变。

如果底层 command-response 本身每次都不一样，再强的 MPC 也只能在一个不断变化的模型上补误差。

ReCo 的核心思路是先做 response shaping：训练 locomotion policy 时就要求它对高层命令产生更一致、可重复的闭环响应，然后再辨识这个响应模型交给 MPC。

### 算法模块

~~~text
randomized dynamics
      ↓
RL locomotion policy
+ response-shaping objective
      ↓
more repeatable command response
      ↓
identify closed-loop response model
      ↓
MPC
  ├─ locomotion command
  └─ arm motion
      ↓
coordinated legged manipulation
~~~

这比“把四足完整动力学学到极准”更现实。MPC 只需要预测已经部署的 locomotion controller 收到命令后会怎么动。

### 动力学假设

方法假设底层策略在 response shaping 后可以由一个紧凑的 closed-loop model 近似，而且高层 MPC 的时间尺度低于底层足式控制。

接触突变、滑移、超出训练分布的重载仍可能让这个模型失效。

### 结果与真机

论文在仿真中相对最佳对比方法将位置 RMSE 降低 28.7%、姿态 RMSE 降低 27.4%，并在真实机器人上展示 onboard、连续的腿式操作，通过底盘与机械臂协同扩大可操作范围。

### 鲁棒性与工程风险

response shaping 的副作用是可能为了“更可预测”牺牲一部分极限敏捷性。对于产品，这是可以接受甚至很值得的交换，但应该显式测：

~~~text
command tracking error
response variance
phase dependence
payload dependence
MPC model residual
task success
~~~

不要只看最终 manipulation success，否则很难知道收益来自步态更稳还是 MPC 更聪明。

### 可复现性

当前没有稳定的完整代码入口，复现门槛中等。最小实验非常清楚：固定现有厂商 / RL gait controller，采集命令和真实速度响应，比较不同 phase / payload 下同一命令的方差，再决定是否值得做 response shaping。

### 适合谁关注

四足 + 机械臂、轮足操作、第三方 locomotion controller、策略感知 MPC、sim-to-real。

### 工程落地启发

只有 vx / vy / vw 的机器人狗尤其适合这个思想。上层不需要知道腿部每个关节，只需学习：

~~~text
recent state + command history
→ achieved vx / vy / wz / pose increment
~~~

然后让导航 / 操作 MPC 在这个真实闭环模型上规划。

[论文](https://arxiv.org/abs/2610.01612)

## 4. EIDA：Sim2Real 不一定要重建底层动力学，先把“执行接口”学准

**时间回补：v1 提交于 2026-10-01 07:24 UTC。**

### 为什么重要

移动机器人导航策略在仿真中常假设：

~~~text
command vx, wz
→ simulator 立刻按指定速度运动
→ policy 下一帧也读到这个速度
~~~

真实 Jackal、Go2 或厂商 SDK 却会受到滤波、延迟、限幅、步态、接触和内部控制器影响。于是即使视觉 / LiDAR 感知完全一样，策略面对的闭环接口也已经变了。

EIDA（Execution-Interface Dynamics Adaptation）明确把这个差异当作独立的 Sim2Real 问题。

### 算法模块

它不重建电机、轮胎或腿部动力学，而是分别学习两件事：

~~~text
command + recent execution history
      ↓
model A: body-frame pose increment
      ↓
update simulator geometry

command + recent feedback history
      ↓
model B: policy-facing velocity feedback
      ↓
what policy observes next
~~~

策略输入还加入短时间速度反馈历史，让策略看到真实 execution interface 的动态特征。

### 传感器与动力学假设

EIDA 只需要目标平台上的命令、位姿 / 运动结果和反馈速度数据，不需要访问底层 actuator state。这对封闭厂商控制器非常关键。

但如果部署差异来自极端地形、脚端接触、传感器时延或高层感知，而不是 execution interface，本方法不会自动解决。

### 实时性与结果

作者用 Jackal 与 Unitree Go2 真实数据验证 learned interface model，相比预定义仿真运动模型能更准确预测位置与 yaw 响应。

在独立 physics simulator 的 100 个导航环境中，使用 EIDA 训练的策略取得对比方法中最高的成功率 / 导航分数。真实 Unitree Go2 的静态场景测试里，EIDA 策略达到 20/20 成功，而基线为 4/20。

### 鲁棒性与工程风险

execution model 应该版本化并绑定硬件 / 固件：

~~~text
robot_model
firmware_version
gait_mode
payload
command_rate
model_version
residual_distribution
~~~

厂商升级固件以后，如果底层速度滤波或 gait response 变了，旧 interface model 也应该视为可能失效。

### 可复现性

当前论文没有给出成熟开源仓库入口，但数据采集要求很低，因此非常适合自研。只需要一套 scripted command sequence 和真实 pose / velocity log，就能训练第一版 execution model。

### 适合谁关注

Unitree Go2 / Go1、第三方机器狗 SDK、AGV、轮式底盘、只开放速度命令接口的机器人平台。

### 工程落地启发

如果现有导航在真机上总有“慢半拍、转弯不足、坡地速度打折”，不要第一时间重训完整 policy。先测清楚 simulator 的 command-response 和真机到底差多少，再决定是在训练时注入 EIDA，还是部署时做 reference adapter。

[论文](https://arxiv.org/abs/2610.01219)

## 5. LiDARFlow：用势流式局部引导场做轻量无人机实时避障

**时间回补：v1 提交于 2026-10-01 12:33 UTC；论文 journal-ref 为 IMAV 2026。**

### 为什么重要

很多无人机局部规划器需要构建 ESDF、采样大量候选轨迹或做较重的优化。对于小型 MAV，算力、功耗和控制延迟都很紧。

LiDARFlow 借用了空气动力学 potential-flow / panel method 的思想：把障碍边界转成会“绕流”的局部向量场，再和原本指向目标的 guiding vector field 合成。机器人不需要先求一条完整离散路径，也能获得连续、平滑的避障方向。

### 算法模块

~~~text
LiDAR point cloud
      ↓
online local obstacle representation
      ↓
panel / potential-flow field
      ↓
collision-avoiding guidance vector
      +
nominal goal / directional vector field
      ↓
final guidance command
~~~

### 传感器与动力学假设

它依赖 onboard LiDAR 与局部注册后的点云，适合未知、杂乱环境。论文重点是 guidance layer，而不是完整全局定位和全局拓扑规划。

局部势场类方法仍可能遇到狭窄通道、局部平衡点或“必须先远离目标才能绕开”的几何，因此需要全局 planner 或 recovery state machine 兜底。

### 实时性与真机

论文在室内 MAV 上完成 waypoint 与 directional guidance 的真机实验，所有障碍都由 onboard LiDAR 在线感知并实时避开。作者强调算法计算较轻，实际主要负担来自点云处理，而不是 guidance field 本身。

### 鲁棒性与工程风险

最重要的风险是把“局部无碰引导”误当成“全局可达规划”。工程上应明确：

~~~text
local_flow_valid
goal_progress
stuck_detector
minimum_clearance
pointcloud_age
global_recovery_request
~~~

如果连续数秒没有目标进展，应切换探索 / 全局重规划，而不是继续沿一个稳定但无进展的局部流场打转。

### 可复现性

当前没有稳定公开代码入口。方法模块边界清晰，可先在现有点云仿真中实现 vector-field sidecar，与 VFH / APF / MPPI 做 CPU 时间、最小间距和卡死率对比。

### 适合谁关注

小型无人机、Jetson / ARM 端侧规划、狭窄室内飞行、需要非常低延迟 local avoidance 的团队。

### 工程落地启发

可以把 LiDARFlow 放在高层 planner 和 PX4 / 厂商飞控之间，只修正短时目标速度方向；全局路径、定位和姿态控制保持原系统不动。这样失败范围小，也容易 A/B。

[论文](https://arxiv.org/abs/2610.01573)

## 6. VAPS：人形安全不应只有“继续成功”与“彻底摔倒”两种状态

**时间回补：v1 提交于 2026-10-01 10:02 UTC。**

### 为什么重要

人形做翻转、跳跃等动态动作时，nominal tracking policy 一旦偏离 reference，继续硬跟踪可能已经物理不可行。传统“安全策略”常把所有恢复行为塞进一个网络，却没有显式说明什么时候该放弃任务、什么时候只能保护头部和手部。

VAPS 把安全做成策略层级：

~~~text
Continue
→ 尽量完成原动作

Abort
→ 原动作不可行时主动终止并争取站稳 / 双脚落地

Fall
→ 连安全中止也不可行时，采用保护性摔倒
~~~

### 算法模块

训练阶段分别获得 nominal behavior、protective fall policy 与可随时中止动作的 abort policy。

运行时每个控制周期，learned viability predictor 分别估计“继续动作”和“现在中止”在短 horizon 内是否仍可行，再按照 least-sacrificial hierarchy 选择最有任务价值且仍被认为可行的策略。

### 动力学与传感器假设

方法面向高动态 humanoid，需要可靠的 proprioception，并假设 viability predictor 对当前机器人、动作类型和动力学分布有足够覆盖。

它没有消除模型误差：如果 predictor 对 OOD 状态过度乐观，系统可能继续一个实际上已经无法救回的动作。

### 仿真与真机

论文在 Unitree G1 与 LimX Oli 仿真中评估，并在真实 LimX Oli 上验证 side-flip 场景中的 viability predictor 与完整 VAPS。相对单网络安全基线，VAPS 在任务成功和头部冲击等指标上形成更好的 Pareto trade-off。

### 鲁棒性与工程风险

产品里 viability 不应只输出 bool，最好记录：

~~~text
nominal_viability
abort_viability
prediction_horizon
minimum_support_margin
head / hand impact risk
policy_switch_reason
~~~

并对“频繁 Continue↔Abort 抖动”设置 dwell time / hysteresis。

### 可复现性

当前未发现完整开源代码入口。最容易迁移的思想是策略分层本身：对已有动作增加 Abort / Protective policy，再用最初可解释的阈值规则决定切换，之后再考虑 learned viability predictor。

### 适合谁关注

人形动态控制、四足跳跃 / 楼梯、强化学习安全、任何存在“任务失败但仍可安全退出”状态的机器人系统。

### 工程落地启发

机器人产品的安全状态机不要只有 RUN / E-STOP。更实用的是：

~~~text
RUN
→ CONTROLLED_ABORT
→ SAFE_RECOVERY
→ PROTECTIVE_STOP
~~~

模型可以决定何时降级，但降级路径本身应该可单独测试。

[论文](https://arxiv.org/abs/2610.01397)

## 7. OpenSpace Lab IROS 2026 探索方案：把返航时间也当成探索预算

**时间回补：v1 提交于 2026-10-01 11:43 UTC。**

### 为什么重要

自主探索算法很容易只优化“下一步哪里信息最多”，最后才发现机器人离起点太远、剩余时间不足，或者多机器人在不同方向上重复覆盖同一片未知区域。

OpenSpace Lab 总结了其 IROS 2026 Autonomous Exploration Challenge 方案：单机重点做地图补全预测 + 剩余时间约束，多机重点做 utility-driven target assignment + intent sharing。

### 单机模块

~~~text
partial map
      ↓
pretrained map-completion predictor
      ↓
global unexplored-area priority
      ↓
candidate target
      ↓
travel / gain / remaining-time / homing constraint
      ↓
exploration action
~~~

接近任务结束时，planner 会显式提高返航权重，而不是继续追逐最后一点边际覆盖率。

### 多机器人模块

多机使用共享地图与机器人意图，将 observation gain、移动成本和 budget 一起写入 target utility。共享“我准备去哪”非常关键，否则即使大家看到同一张地图，也可能同时选择同一个高收益 frontier。

### 结果

团队在 IROS 2026 挑战中获得 Single-Robot Public Track 第 1，以及 Single / Multi-Robot Private Track 第 3。论文报告覆盖率分别为 61.04%、39.53% 和 39.91%。

### 传感器与系统假设

这是一套探索系统方案，不是单一 planner。地图补全 prior 会受到训练场景分布影响；比赛中的时间 / 返航规则也未必等于真实巡检任务。

但“把剩余任务时间、返航成本、其他机器人意图作为正式规划状态”的思想非常通用。

### 可复现性

论文 comments 表示代码计划在完整 manuscript acceptance 后公开，目前不能按已开放源码评价。

### 工程风险

map completion 很容易“把没见过的地方想当然”。建议预测地图只用于 target ranking，不要直接写进 collision map。应区分：

~~~text
observed_free
observed_occupied
predicted_structure
unknown
~~~

规划安全约束只信观测层，预测层只影响探索优先级。

### 适合谁关注

无人机 / 机器人狗自主探索、FAR planner、矿井 / 工业巡检、多机器人搜索、必须保证按时返航的任务。

### 工程落地启发

现有 frontier planner 可以先只增加两个量：time_to_home 和 teammate_intent。哪怕不引入神经 map completion，也通常能减少“最后回不来”和多机器人重复搜索。

[论文](https://arxiv.org/abs/2610.01505)

## 8. CONTRA：Coding Agent 只问那些“答案不同会让程序行为真的不同”的问题

**时间回补：v1 提交于 2026-10-01 14:26 UTC。**

### 突破性工程价值

Coding Agent 面对欠规范需求时通常有两个极端：要么擅自补全假设，代码表面正确但实现了用户从未要求的行为；要么为了避免猜测不停追问，开发体验变得很差。

CONTRA 试图把“是否值得问”变成可执行判断，而不是靠语言模型自评一句“这个问题重要吗”。

### 算法模块

~~~text
underspecified requirement
        ↓
broad candidate-question discovery
        ↓
semantic filtering
- remove irrelevant questions
- remove already-resolved questions
        ↓
for each candidate:
  plausible answer A → generate program A
  plausible answer B → generate program B
        ↓
execute on shared inputs
        ↓
stable behavioral difference?
        ↓
yes → qualified clarification
no  → don't interrupt user
~~~

交互历史还会用于决定下一条问题或何时停止继续问。

### 结果

在 ClarifyCodeBench 上，CONTRA 与四种 coding agent 组合都获得最高 F1，相对最佳 baseline 的 macro-average F1 高 13.88 个百分点。在相同 LLM 与评估协议下，也比 Claude Code 和 OpenHands 的原生澄清行为获得更高 clarification recall / F1。

### 是否适合真实研发流程

非常适合 API 行为、边界条件、排序 / 并发语义、错误处理等“两个答案会产生可执行差异”的需求。

它不适合所有产品决策。UI 审美、业务优先级、法律 / 合规偏好并不一定能通过程序 A/B 执行自动判定。

### 权限 / 安全 / 可验证性风险

CONTRA 会为不同假设生成并执行候选程序，所以 qualification 应在 sandbox 中运行，而且不能继承生产凭据。

建议把澄清问题记录成：

~~~text
question
answer_hypotheses
behavioral_counterexample
tests_used
user_answer
resulting_requirement
~~~

这样后续 Agent 不会在几小时后又重新猜一遍。

### 可复现性

作者已经公开代码，并提供 Claude Code plugin，属于今天 AI Coding 论文里非常适合直接尝试的一项。

### 适合谁关注

Claude Code、Codex、自研 Coding Agent、需求经常只有一两句自然语言的大仓库开发流程。

### 工程落地启发

即使不用完整 CONTRA，也可以给 Agent 增加一个很实用的规则：只有当两个合理解释能产生不同测试结果 / API 行为时才升级为用户澄清；只是实现细节差异则由 Agent 自己选择并记录。

[论文](https://arxiv.org/abs/2610.01769) · [代码 / Claude Code 插件](https://github.com/fangz-cs/Contra)

## AI Coding 实战技巧精选

### 技巧 1｜把 Copilot Code Review 接进自己的 CI，并按阶段调 Review Effort

- **来源**：GitHub 官方 Changelog，2026-10-02：[Copilot code review: API support and new default effort level](https://github.blog/changelog/2026-10-02-copilot-code-review-api-support-and-new-default-effort-level/)。
- **一句话结论**：Copilot Code Review 现在可以从 REST / GraphQL API 发起，并且每次请求都能指定 review effort；不要再把 AI Review 只能绑在 GitHub UI 点击上。
- **具体怎么做**：
  1. 在现有 PR pipeline 中，把“测试通过”之后增加一个请求 Copilot review 的 API step，而不是每次 push 都人工点 reviewer。
  2. 高频开发阶段使用较低 review effort；准备合并或大范围重构时，把该次请求提升到 Balanced。GitHub 现在默认使用 Balanced，之前显式选择 Lite 的设置仍会保留。
  3. 企业 / 组织 / 仓库可以分别在 AI controls 或 Copilot → Code review 中设默认值，低层级设置可以覆盖上层默认。
  4. 把 review 结论与 build、unit test、CodeQL 分开记录；AI review 不作为唯一 merge gate。
- **适合什么场景**：GitHub Copilot、大量 PR、Agent 高频提交、多仓库统一代码审查流程。
- **注意**：Review effort 越高不代表一定更正确，只代表投入更多审查预算。真正应比较的是每个 PR 的有效 finding、误报和人工修正量。

### 技巧 2｜Claude Code 深审前用 --max-findings 控制一次 Code Review 的问题数量

- **来源**：Anthropic Claude Code v2.1.288，2026-10-02：[官方 Release](https://github.com/anthropics/claude-code/releases/tag/v2.1.288)。
- **一句话结论**：v2.1.288 给 /code-review 增加 --max-findings <n>|all；日常迭代限制 finding 数，发布前再放开全量，比每次都生成一长串低优先级问题更可控。
- **具体怎么做**：
  1. 普通迭代先运行 /code-review --max-findings 5，让模型集中报告最值得处理的一小批问题。
  2. release candidate、复杂迁移或安全敏感 PR 再运行 /code-review --max-findings all。
  3. 该选择会在后续 review 中复用；想回到工具默认限制时使用 /code-review --max-findings default。
  4. 把“finding 数量”与实际修复率一起记录，找到团队最合适的上限，而不是追求报告越长越好。
- **适合什么场景**：Claude Code、大 PR、重构、长期 Agent 任务、希望控制 review token / 人工注意力成本的团队。
- **注意**：all 很容易把低价值 finding 也一起放大。正式合并仍要依赖真实 build、test、static analysis 和人工 review。

## 经典论文回顾

### Informed RRT*：找到第一条路以后，不要再把算力浪费在“不可能改进当前解”的区域

Jonathan D. Gammell、Siddhartha S. Srinivasa 与 Timothy D. Barfoot 的 **Informed RRT*: Optimal Sampling-based Path Planning Focused via Direct Sampling of an Admissible Ellipsoidal Heuristic** 发表于 IROS 2014。它是 asymptotically optimal sampling-based planning 中最经典的“把采样预算集中到可改进区域”工作之一，也直接构成今天 BLT* 的思想起点。

### 核心问题

RRT* 找到第一条可行路径以后，仍会继续在整个状态空间里采样。对于单起点、单终点问题，大量样本显然不可能产生比当前 c_best 更短的路径，却仍然要做 nearest、collision checking 和 rewiring。

Informed RRT* 问了一个非常直接的问题：

> 已经知道当前最好路径长度 c_best 后，哪些状态还可能出现在一条更短的路径上？

### 关键数学思想

在 Euclidean 最短路径问题里，如果某个状态 x 有可能改进当前解，就必须满足：

~~~text
distance(start, x) + distance(x, goal) < c_best
~~~

满足这个不等式的所有点组成一个以 start / goal 为焦点的 prolate hyperspheroid。

因此算法分为两阶段：

~~~text
还没有解
→ 像 RRT* 一样全局探索

已有当前最好解 c_best
→ 只在 informed hyperspheroid 内直接均匀采样
→ 继续 rewiring
→ 新解更短后 hyperspheroid 继续收缩
~~~

关键在“直接采样椭球”，而不是先在整个空间采样再做 rejection。随着维度升高，后者命中 informed set 的概率会急剧下降。

### 传感器 / 动力学假设

原始 Informed RRT* 主要讨论连续 Euclidean 配置空间中的几何最短路径，状态被视为确定值；它本身不建模 SLAM covariance、动态障碍、复杂 kinodynamic constraint 或感知可观测性。

这正是今天 BLT* 值得看的原因：BLT* 把节点变成 Gaussian belief，用 Wasserstein 距离和定位信息扩展“哪些区域值得继续搜索”的概念。

### 当年为什么重要

Informed RRT* 保留 RRT* 的 probabilistic completeness 与 asymptotic optimality，同时显著改善已有初始解后的收敛效率。原论文在抽象规划和 HERB 双臂机器人上展示了更快的 cost 改进。

它改变了一个很重要的工程直觉：采样式规划的性能不只取决于“采多少点”，更取决于“把点采到哪里”。

### 今天仍在使用的思想

今天许多 planner 都在重复同一原则：

~~~text
先找到可行解
→ 根据当前 upper bound 推导可改进区域
→ 把后续计算集中在那里
~~~

BIT*、AIT*、EIT*、各种 learned sampler 和今天的 belief-space BLT* 都是在不同问题结构上扩展 informed search。

### 已被后续替代 / 扩展的部分

原始椭球 informed set 对 Euclidean path length 非常漂亮，但一旦引入非完整约束、复杂动力学、风险、定位 covariance、多模态 belief，通常就没有这么简单的解析椭球。

现代 planner 会使用启发式 cost-to-go、批量随机几何图、MCMC、learned proposal 或问题特定的 belief metric 来近似“可改进区域”。

因此不要把 Informed RRT* 理解成“永远采一个椭球”，而应理解成一个更广义的计算预算原则：

> **已经有 incumbent solution 后，任何不可能击败它的候选都不值得继续花昂贵计算。**

### 公开代码与可复现性

论文有公开 arXiv 版本，算法也已被 OMPL 等现代 planning library 广泛实现。最小复现实验很简单：固定 collision checker 和随机种子，对 RRT* 与 Informed RRT* 记录第一条可行路径出现后的：

~~~text
best_cost vs time
collision_checks
samples
rewires
dimension scaling
~~~

真正应该比较的是“找到第一条路以后谁更快变好”，而不是只比较 first-solution latency。

### 对当前工程项目的重新解读

对无人机、机器狗或机械臂，今天最值得借鉴的是“上界驱动的预算收缩”。

例如已经有一条安全可行路线后，可以让：

~~~text
当前最好时间 / 距离 / 风险
        ↓
推导还能击败它的候选范围
        ↓
只对这些候选运行昂贵的
collision / dynamics / SLAM-localizability evaluation
~~~

BLT* 再向前走一步：如果定位不确定性本身决定路径是否可靠，那么 informed set 也应该在 belief space 里定义，而不是只按欧氏几何距离收缩。

[论文 arXiv](https://arxiv.org/abs/1404.2334) · [DOI](https://doi.org/10.1109/IROS.2014.6942976) · [作者项目页](https://robotic-esp.com/papers/gammell_iros14)

## 今日结论

今天八项工作虽然横跨 SLAM、规划、四足、人形、无人机和 Coding Agent，但共同主题非常清楚：**真正成熟的系统会把“不确定性、接口误差和失败后的降级路径”都变成显式对象。**

GlassGuard 不再把玻璃检测结果直接烙死进地图，而维护可以被后续观测推翻的几何假设；BLT* 不再假设机器人始终知道自己的精确位置，而让 belief 成为规划 state；ReCo 与 EIDA 也都承认底层控制器 / 硬件接口本身是系统的一部分，上层 planner 必须知道“命令最后会变成什么真实响应”。

LiDARFlow 和 OpenSpace Lab 则展示了不同时间尺度上的规划分工。局部层应该足够轻，能在 onboard 算力下快速绕开眼前障碍；全局层则需要考虑时间预算、返航和多机器人重复劳动。把这两类职责强行塞进同一个 planner，往往既慢又难调。

VAPS 对安全控制最有启发：失败不是一个二值事件。继续任务、主动中止、保护性跌倒分别对应不同剩余可控性。机器人在高风险状态下最重要的能力，可能不是“仍然把任务做完”，而是正确判断从什么时候开始不再值得冒险。

CONTRA 又把同一原则映射到 Coding Agent：澄清也不应该二值化成“永远猜”和“永远问”。只有当不同答案会稳定改变程序外部行为时，问题才真正值得打断用户。

今天两条 AI Coding 实战技巧同样是在做预算分配。Copilot review 可以按阶段设置 effort，Claude Code 可以限制 finding 数量。更强 Agent 的下一步并不是每次都开最大推理 / 最大 review，而是根据任务风险和阶段动态投入计算和人工注意力。

如果把今天整期压成一句话：

> **可靠机器人和可靠 Coding Agent，都应该把计算预算花在“可能改变结果”的地方，并把无法继续、需要澄清或必须降级的时刻显式建模出来。**

## 最值得深入研究或尝试复现的方向

1. **玻璃地图 Sidecar。** 在现有 LIO / costmap 外增加独立 glass-plane layer，只订阅相机、registered cloud 和 pose；先统计玻璃漏检、假平面和真实碰撞风险，不直接污染 SLAM 主图。
2. **Localizability-aware Informed Planning。** 给 Informed RRT* 的 cost 增加 LIO covariance / Hessian localizability 项，比较长走廊中最短路径与定位友好路径。
3. **机器人狗 Execution-Interface Model。** 采集 vx / vy / wz、gait mode、真实 pose increment 和 feedback velocity，先学一个 EIDA-style 模型，再用于导航训练或上层 reference correction。
4. **Policy-aware MPC A/B。** 不重建四足完整动力学，只比较“理想速度积分模型”和“从真实 controller log 学到的 closed-loop response model”对 MPC 预测误差的影响。
5. **无人机局部流场 Sidecar。** 保留 PX4 / 全局 planner，只让 LiDARFlow 类模块修正短时速度方向，专门比较 MPPI / APF / flow field 的 P95 latency、最小间距与卡死率。
6. **Continue / Abort / Recovery 状态机。** 在楼梯、跳跃或高风险操作里先用规则实现三层降级，再收集真实切换数据训练 viability predictor。
7. **探索加入 time-to-home 与 teammate intent。** 即使没有 map completion 网络，仅增加返航剩余时间和队友目标广播，也能验证预算感知探索是否减少重复与超时。
8. **Coding Agent Behavior-Changing Clarification。** 对现有需求集自动生成两个 plausible interpretation，只有当测试结果不同才询问用户；把用户答案写成持久 requirement artifact。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [GlassGuard](https://arxiv.org/abs/2610.02110) · [项目页](https://glassguardproject.github.io/) · [代码](https://github.com/glassguardproject/GlassGuard)
- [BLT*](https://arxiv.org/abs/2610.01972)
- [ReCo](https://arxiv.org/abs/2610.01612)
- [EIDA](https://arxiv.org/abs/2610.01219)
- [LiDARFlow](https://arxiv.org/abs/2610.01573)
- [VAPS](https://arxiv.org/abs/2610.01397)
- [OpenSpace Lab IROS 2026 Exploration Solution](https://arxiv.org/abs/2610.01505)
- [CONTRA](https://arxiv.org/abs/2610.01769) · [代码 / 插件](https://github.com/fangz-cs/Contra)
- [GitHub Copilot Code Review API / Effort](https://github.blog/changelog/2026-10-02-copilot-code-review-api-support-and-new-default-effort-level/)
- [Claude Code v2.1.288](https://github.com/anthropics/claude-code/releases/tag/v2.1.288)
- [Informed RRT*](https://arxiv.org/abs/1404.2334) · [DOI](https://doi.org/10.1109/IROS.2014.6942976) · [作者项目页](https://robotic-esp.com/papers/gammell_iros14)
