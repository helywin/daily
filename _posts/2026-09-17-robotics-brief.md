---
layout: default
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-17"
permalink: /reports/2026/09/17/
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-17

## 摘要

截至今天早间，arXiv `cs.RO/recent` 的最新公开批次仍是 **2026-09-16**，因此本期不把尚未出现的“9 月 17 日论文”硬凑成新动态，而是继续从 9 月 16 日批次中做去重回补。昨天的索引已经覆盖 LiLi、HuMemSLAM、TIO-Former、Online Geometric Change Detection、Hybrid HJ Reachability、Wrench Polytope、ModAR、RepoAtlas 等条目；今天选择的 8 个方向均未出现在覆盖索引中，并优先挑选对真实机器人系统设计有直接启发的工作。[arXiv Robotics Recent](https://arxiv.org/list/cs.RO/recent)

今天最值得关注的几个工程信号是：**安全控制开始从“当前位置是否安全”转向“执行器在有限时间内是否还有逃逸能力”**；**多机器人主动感知开始显式修正共享先验造成的信息重复计算**；**地形感知与控制策略都越来越强调部署后的持续适应，而不是一次性离线训练**；同时，VLA 工程也开始出现试图把数据、训练、仿真、远程推理和真机操作统一起来的平台化工具。

如果只选一个今天最适合深入复现的方向，我会优先看 **Escape-Aware Control Barrier Functions**。它击中了传统 CBF 在无人机高速逼近障碍物时一个很现实的漏洞：数学上“当前位置仍在安全集”，并不代表受限于机体角速度、推力方向变化速度的飞行器仍然来得及转向逃离。这个问题和实际 PX4 / MPC 中的姿态内环、推力矢量、控制饱和是直接相连的。

## 1. Escape-Aware CBF：安全不是“现在没撞”，而是“在机体角速度限制下仍然来得及逃”

**时间回补；arXiv:2609.17292，2026-09-15 提交，进入 9 月 16 日公开批次。**

### 为什么重要

常见 obstacle CBF 会根据位置、速度或停止距离构造安全约束。例如一维直觉上可以写成：

```text
h(x) = distance - stopping_distance(v)
```

但四旋翼并不能瞬时把总推力转到任意方向。即使推力大小足够，真正的加速度方向仍依赖机体姿态，而姿态改变又受到 body-rate 上限约束。因此会出现一种“认证缺口”：传统 state-only barrier 认为当前状态安全，但飞行器实际上已经没有足够时间把推力向量转到逃逸方向。

论文明确指出，这个缺口的宽度随 closing speed 增大而扩大，并随可用 body-rate 增大而缩小。[论文](https://arxiv.org/abs/2609.17292)

### 方法结构

作者把 barrier 从只看当前 state，扩展为同时考虑：

```text
current state
    +
previously applied input
    ↓
one-step reachable thrust cap
    ↓
escape authority
    ↓
escape-aware barrier
```

这里的核心不是再加一个经验安全 margin，而是计算：在下一个离散控制周期里，受 body-rate 限制后，推力向量最多能转到哪里；这个有限的“逃逸权威”再进入 barrier 判定。

论文还给出闭式形式以及最大可认证 closing speed 的解析逆关系。工程上这很有价值，因为它意味着安全边界可以直接转化为“当前速度还能不能刹/转得过来”的可解释量，而不只是 QP 是否可行。

### 实验与实时性

作者在 13-state quadrotor 上做了 550 对闭环 episode。摘要报告中，escape-aware 方法在测试中全部完成，而 stopping-distance barrier 在 gap 类场景中出现约 15% / 25% 的失败；相对在线 backup-CBF 基线，论文还报告了更大的方向裕量与净空。当前公开结果主要是闭环仿真/实验设置，不能直接等同于复杂真机环境的安全认证。

它的优势是无需为安全层额外增加状态维数很高的在线 rollout；作者强调可以嵌入 predictive controller，而不引入额外 state cost。

### 工程风险与失败边界

真正落地时最容易踩的坑有四个：

- body-rate 上限不能只填飞控标称值，还要考虑负载、电池、姿态内环带宽与 rate saturation；
- one-step reachable thrust 依赖控制周期，planner / MPC / attitude loop 的时间戳不一致会破坏认证含义；
- 风扰、模型误差与推力估计偏差会让理论 escape authority 偏乐观；
- barrier 层只能保证所建模约束，不能替代感知延迟与障碍物预测误差处理。

### 适合谁关注

高速无人机、狭窄空间飞行、MPC/CBF 安全层、PX4 外环控制、自主避障系统。

### 工程落地启发

如果已有无人机 MPC，不必立刻重写成论文完整算法。可以先做一个 `escape_margin` telemetry：根据当前相对障碍 closing speed、最大可用 body-rate、当前推力方向和控制周期，估算最小可逃逸距离。把它和传统 stopping distance 同时记录，先找出二者分歧最大的真实飞行片段，再决定是否升级 safety filter。

## 2. Exact Fusion and Coordinated Exploration：多机器人融合里，最隐蔽的错误可能是“把同一个先验算了 n 次”

**时间回补；arXiv:2609.17384。**

### 为什么重要

多机器人探索很容易写成：每个机器人独立维护 posterior，通信后把各自 posterior 融合；规划时，每个机器人都在当前 belief 上计算 expected information gain。问题是，如果所有机器人从同一个 prior 出发，那么简单把局部 posterior 相乘会重复计算公共先验；而规划时所有机器人都针对同一份 belief 选“最有信息”的位置，又会集体冲向同一未知区域。

这篇工作把两个问题统一成 **evidence increment**：不要融合 posterior 本身，而是融合每个机器人相对于共享 prior 新增了多少证据。[论文](https://arxiv.org/abs/2609.17384)

### 数学直觉

对指数族 / Gaussian belief，可以把 belief 写在 natural parameter 空间里：

```text
shared natural parameter η0
        +
robot 1 evidence Δη1
        +
robot 2 evidence Δη2
        + ...
```

融合时只叠加已实现的 evidence increment；规划时，则把已经承诺执行的队友未来观测视为 expected increment，再计算下一个机器人的 conditional gain。

这比简单做：

```text
argmax_a I(x; z | a)
```

更接近：

```text
argmax_a I(x; z_i | 已承诺的队友观测)
```

因此后加入的机器人会自动避开已经被前面机器人“解释掉”的信息区域。

### 理论与结果

摘要中给出的关键结论是：校正后的增益之和可以与 joint gain 对齐，去除的冗余可由计划观测流之间的 total correlation 描述；顺序承诺策略仍保留 1/2 greedy guarantee。对于 Gaussian beliefs + 固定 sampling path 可以做到精确；Dirichlet belief 使用 novelty approximation；有限 hypothesis class 则可以直接枚举。

作者在 cooperative RockSample、foraging、field monitoring 上验证，说明 anticipated evidence 能减少多机器人重复探索，并以线性随机器人数量增长的协调成本恢复大部分 centralized joint planning 的收益。

### 工程风险

理论成立高度依赖“共享先验”和观测模型的一致性。真实系统里更麻烦的是：

- 不同机器人地图坐标系尚未完全对齐；
- 传感器噪声模型和标定不一致；
- 通信延迟使所谓 shared belief 实际上已经过期；
- 队友承诺的路径可能因局部避障而改变。

因此部署时应该给 evidence increment 加版本号 / belief timestamp，而不是只传播一个匿名增量。

### 适合谁关注

多无人机探索、多四足巡检、主动建图、弱通信搜索、协同信息采集。

### 工程落地启发

已有 frontier exploration 系统可以先实现一个简化版：每个 frontier 除了本地 gain，再维护 `claimed_gain` 或 `expected_coverage`。机器人发布未来 3–5 秒的 intended sensing footprint，其他机器人计算 frontier reward 时减去重叠区域。先用几何 coverage 做 evidence proxy，就能验证是否减少扎堆，再逐步升级到真正 belief-space information gain。

## 3. Continual Traversability：地形可通行性模型开始把“部署后的新地面”当成一等问题

**时间回补；arXiv:2609.17141。**

### 为什么重要

学习式 traversability predictor 的常见 demo 往往是：采一批草地、砂石、泥地数据，训练一次，然后上线。但野外机器人真正遇到的问题是地表分布不断变化：湿土、落叶、雪、煤灰、碎石粒径变化都会让原模型失效。如果每次新地形都全量再训练，代价高；如果只用新数据微调，又容易 catastrophic forgetting。

这篇工作把 traversability 做成 continual learning，并使用 **generative experience recall** 在不保存全部历史原始数据的情况下回放旧经验，同时把生成样本的不确定性纳入适应过程。[论文](https://arxiv.org/abs/2609.17141)

### 方法直觉

```text
old experience
     ↓
generative recall ─────┐
                       ├─ uncertainty-aware adaptation → updated predictor
new terrain samples ───┘
```

重点不只是 replay，而是对生成出来的历史样本“有多可信”显式建模。因为生成模型本身也会漂移，如果把低质量 replay 当真实旧数据，continual learning 会变成另一种遗忘。

### 传感器与系统假设

摘要没有把方法绑死在单一激光或相机前端上；它更像 traversability prediction 后端。作者在 skid-steering robot 的多种真实环境中验证，这至少比纯仿真地形分类更接近移动机器人部署问题。

实际接入时，输入可能来自 LiDAR height map、视觉语义、IMU/轮滑反馈或它们的融合；最重要的是“可通行性标签”如何在线获得。如果没有真实 slip / sink / pitch response 等自监督反馈，持续学习仍可能只是在持续拟合感知外观。

### 工程风险

- uncertainty 高不等于 terrain 危险，它也可能只是模型没见过；
- generator 的 replay quality 需要单独监控，否则会逐渐产生虚假旧知识；
- 在线学习不能直接覆盖 safety fallback；
- skid-steer 上学到的 slip pattern 不能无条件迁移到轮足或四足平台。

### 适合谁关注

户外 UGV、矿山/煤场机器人、轮足机器人、越野导航、长期运行巡检机器人。

### 工程落地启发

如果当前已经用 LIO-SAM + elevation map 做通行性，可以先不在线更新主模型，而是做“两层输出”：`traversability_score` + `epistemic_uncertainty`。当 uncertainty 连续超过阈值时，把对应地图片段、轮速/IMU/slip telemetry 自动归档，离线形成下一轮增量训练集。这一步本身就能把“新地形失败”从偶发 bug 变成可观测的数据闭环。

## 4. RRT + Hit-and-Run：把“从哪个节点扩展”和“往哪个方向扩展”解耦

**时间回补；arXiv:2609.16810。**

### 为什么重要

经典 RRT 的高效来自 Voronoi bias，但在高维、窄通道、小 clearance 场景里，nearest-node + random-sample direction 的耦合并不总是理想。Hit-and-Run（HAR）则更擅长在高维可行区域里做随机游走，但它并不是传统意义上的单查询 motion planner。

这篇论文提出一个很漂亮的统一视角：**选择“哪个点被扩展”的偏置，与选择“扩展方向”的偏置，本来就可以分开设计。** RRT 和 HAR 都只是这个更一般框架的特例。[论文](https://arxiv.org/abs/2609.16810)

### 算法结构

可以把一步扩展写成两个独立决策：

```text
1. choose expansion point q
2. choose extension direction d
3. collision-limited move along d
```

RRT 更强地偏置第 1 步；HAR 更强调随机方向。作者将二者混合，并加入 sparse move：多机器人 / 多刚体问题中，每一步只移动一定比例 `p_r` 的对象，而不是所有对象同时变化。

### 为什么 sparse move 有效

如果状态空间是：

```text
SE(3)^N
```

一次同时改变 N 个刚体会让碰撞约束迅速变得苛刻。只移动少数对象，相当于在高维空间里优先搜索低维子空间，使狭窄局部约束更容易满足。

论文在 3D piano mover 与分子系统映射的多刚体问题上测试，最高到 64 个 robot / 384 DoF；摘要报告标准笔记本上可在秒级处理部分大规模实例，并在复杂多机器人问题上相对经典“全部一起动”的 RRT 获得显著加速。

### 工程风险

这类 benchmark 的“64 robots”不能直接等价成 64 台真实移动机器人：真实多机器人还要处理动力学、通信、任务冲突、连续时间碰撞与时间参数化。论文更主要说明高维几何规划中的采样策略，而不是完整 fleet planner。

### 适合谁关注

机械臂、高自由度规划、多刚体装配、多机器人 configuration-space planner、OMPL 算法研究。

### 工程落地启发

如果你的 RRTConnect 在高自由度机械臂 narrow passage 上经常卡死，不妨先做一个比“换整个 planner”更小的实验：记录每次扩展失败原因，并允许采样器只扰动一组 joint block。对 7 DoF 手臂可以比较 `all-joint sample`、`2-joint sparse sample`、`adaptive block sample` 的成功率与 collision-check 数量。

## 5. Residual Fault Adaptation：机械手故障时，不切换“故障策略”，而让循环残差从命令响应历史里自己推断

**时间回补；arXiv:2609.17404。**

### 为什么重要

灵巧手一旦某个关节出现 command attenuation、卡滞或响应异常，健康策略通常立刻退化。传统做法要么做 fault diagnosis → policy switching，要么在训练阶段把所有故障模式直接 domain randomization 到一个大 policy 里。

这篇工作采用 teacher-anchored residual fault adaptation：健康 teacher 冻结并持续给 nominal action，另一个 recurrent residual policy 从 proprioception 与 command-response history 中推断修正量，不需要部署时提供 fault label 或显式 switching signal。[论文](https://arxiv.org/abs/2609.17404)

### 控制结构

```text
observation ──→ frozen healthy teacher ──→ nominal action ──┐
                                                           ├─→ final command
history + proprioception ─→ recurrent residual policy ─→ Δu ┘
```

训练时 fault-injection domain randomization 随机改变故障模式、关节、严重度与 onset；同时 adaptive sampling 会增加近期表现差的故障类型。论文还使用 Direct FIDR policy 作为训练分布参考，但部署时并不需要 fault label。

### 为什么 recurrent history 很关键

单帧 proprioception 很难区分“当前姿态刚好如此”和“执行器没有按命令响应”。而命令 `u_t` 与随后的 joint response 之间的时间序列偏差本身就是故障观测器。用 recurrent residual，相当于把一部分系统辨识隐式塞进策略。

### 实验边界

摘要报告仿真 mixed faults 下的提升，并在真实机器人上做了软件注入故障的 zero-shot 部署。这里要严格区分：**真机 + 软件注入故障** 并不等于真实电机、齿轮、线缆物理故障已经被覆盖。真实硬件故障可能伴随温升、回差、摩擦突变、传感器异常甚至结构损伤。

### 适合谁关注

灵巧手、冗余执行器、容错控制、RL residual policy、工业机器人降级运行。

### 工程落地启发

类似思想完全可以迁移到轮足/四足：保留一个验证过的 nominal controller，再训练低幅度 residual 只在命令-响应残差长期异常时介入。关键是给 residual 设置严格 action envelope，并把 `commanded vs measured response` 的异常统计作为独立 safety monitor，而不是让 residual 获得无限补偿权。

## 6. IL-ACT：30 吨挖掘机的模仿学习，不让神经策略独自承担液压延迟与轨迹误差

**时间回补；arXiv:2609.16696。**

### 为什么重要

工程机械控制非常适合展示“学习策略 + 经典闭环”的价值。大挖机具有强耦合运动学、液压执行延迟、载荷变化与模型不确定性，单纯行为克隆输出动作很容易产生累积误差。

IL-ACT 的做法不是继续堆大模型，而是让 imitation policy 给 nominal joint-rate，再由 adaptive Cartesian tracking feedback 修正，并用 stopping-distance governor 约束 joint reference generation。[论文](https://arxiv.org/abs/2609.16696)

### 架构

```text
operator demonstrations
        ↓
14-input imitation policy
        ↓
nominal joint rates
        ↓
adaptive Cartesian feedback
  ├─ gain estimation
  └─ bias estimation
        ↓
stopping-distance governor
        ↓
reference / actuator command
```

这种分层的价值在于：学习部分负责“像人一样给出合理动作趋势”，经典闭环负责把真正的末端误差、液压滞后和扰动吸收掉。

### 结果与边界

作者在 Simscape 中做 100 个 sequential goals，以及 spiral、figure-eight、rounded-raster 等轨迹，共 88 次多条件运行。摘要报告 telemetry-initialized IL-ACT 在 figure-eight / rounded-raster 的 24 个 seed 对比中均降低 RMSE；额外载荷的 spiral 平均 RMSE 改善约 29%；共享传感器噪声条件下相对 Teacher+ACT 平均降低约 27.67%。

必须注意，这些是 **Simscape 评估**，不是 30 吨挖机现场已经连续生产运行的证据。

### 工程风险

- 模仿策略的 nominal command 如果超出 governor 可行域，会让后端一直裁剪；
- adaptive gain/bias 若缺少边界，很容易在模型失配时漂移；
- 液压阀 dead-zone 与真实负载变化可能比仿真更复杂；
- stopping-distance governor 只能约束所建模的 reference admissibility。

### 适合谁关注

工程机械、矿山机器人、重型机械自动化、learning + control 混合架构。

### 工程落地启发

这类架构比端到端策略更适合产品化：把 policy 输出限定成可解释的 nominal velocity / target，再让已有 PID/MPC/自适应控制守住最后闭环。对巡检操作机器人也同样适用：学习“做什么”，经典控制保证“精确做到”。

## 7. CorrRisk-WM：风险预测必须以“我的候选轨迹”为条件，而不是只预测别人会怎么走

**时间回补；arXiv:2609.16724。**

### 为什么重要

很多 world model / motion prediction 系统会先预测周围 agent 的未来轨迹，再由 planner 判断碰撞。但同一个周围车辆动作，对不同 ego candidate 来说风险完全不同：你走左侧 corridor 可能安全，走右侧则刚好侵入。

CorrRisk-WM 因此不只预测 environment evolution，而是让每条候选 ego trajectory 用自己的 corridor 去查询动态环境，直接预测 intrusion 与 near-miss risk。[论文](https://arxiv.org/abs/2609.16724)

### 模型结构

```text
dynamic agents + map
        ↓
latent environment evolution
        ↓
for each ego candidate trajectory
        ↓
trajectory corridor / footprint query
        ↓
recurrent risk module
        ↓
slice hazard
        ↓
survival aggregation
        ↓
first-entry probability + horizon event probability
```

这里的关键是 **candidate-conditioned risk**。world model 不再只回答“未来世界长什么样”，而开始回答“如果我执行这条动作序列，这个未来对我意味着什么”。

### 数据与结果

作者使用 100 个 Waymo validation shards 中的 29,176 个 scenario。摘要报告 intrusion AP 0.8567、1 m near-miss first-entry AP 0.8671；规划评估中最低观察到的 open-loop collision rate 为 4.88%，route progress 为 15.35 m。消融中，移除动态环境建模或候选几何交互都会显著降低 intrusion AP。

这些结果是数据集 / open-loop 评估，不等于闭环自动驾驶安全证明，更不应被直接外推到无人机或室内机器人。

### 工程风险

- corridor 宽度选得太窄会漏风险，太宽会造成假阳性；
- motion predictor 的 multimodality 若被压成单一路径，risk head 再准确也没用；
- survival aggregation 对时间相关性有建模假设；
- open-loop 指标不能替代 closed-loop intervention / recovery 测试。

### 适合谁关注

自动驾驶、移动机器人局部规划、动态障碍预测、world model + planner、风险敏感 MPC。

### 工程落地启发

在机器人局部规划里不必先训练完整 world model。DWA / MPPI / trajectory rollout 已经有 candidate set，可以先把每条 trajectory 膨胀成 footprint corridor，再从 predicted obstacle occupancy 中计算 `first_intrusion_time`、`min_clearance_distribution` 和 `near_miss_prob`，把这些作为风险代价输入现有 planner。

## 8. FluxVLA Engine：VLA 的下一个工程瓶颈，可能不是新 policy，而是数据—训练—评测—真机之间没有统一接口

**时间回补；arXiv:2609.17210；代码已公开。**

### 为什么重要

机器人 VLA 生态当前最大的问题之一是碎片化：一个仓库负责数据转换，一个仓库训练 Pi0，另一个做仿真，真机又写一套 ZMQ server 和轨迹后处理。实验室能跑通，但模型一换、机器人一换，整条链路几乎重写。

FluxVLA Engine 的定位就是工程平台，而不是提出一个新的 VLA policy。[论文](https://arxiv.org/abs/2609.17210) / [代码](https://github.com/FluxVLA/FluxVLA)

### 平台覆盖范围

论文与仓库目前公开的模块包括：

```text
datasets
   ↓
VLM / vision encoder / world model
   ↓
action head
   ↓
SFT / reward- or advantage-weighted learning
   ↓
distributed training
   ↓
simulation evaluation
   ↓
optimized / remote inference
   ↓
trajectory post-processing
   ↓
robot operator
```

仓库列出的模型/组件包括 OpenVLA、LlavaVLA、GR00T、Pi0、Pi0.5、FastWAM、DiT4DiT，以及 PaliGemma/Qwen-VL、DINOv2/SigLIP 等；训练侧支持 FSDP、DDP、LoRA 与 LeRobot 数据格式，推理侧有 ZMQ remote inference、RTC trajectory continuity、Triton/CUDA Graph/custom op 等优化路径。

### 真正值得看的工程点

我更关注三件事，而不是“支持多少模型”：

1. **model-decoupled human-in-the-loop**：rollout、takeover、correction、reward annotation 不绑死单一模型；
2. **remote GPU serving**：允许机器人端只保留轻量控制/通信，重模型放 GPU server；
3. **trajectory continuity**：VLA action chunk 并不是生成完就结束，实际执行还要处理推理延迟、chunk 拼接与轨迹平滑。

这几个接口往往比换一个 backbone 更决定真机是否稳定。

### 工程风险

平台化也有典型陷阱：抽象层越统一，越容易把 embodiment-specific 的细节藏掉。不同机器人 action 的单位、频率、坐标系、归一化、gripper semantics、safety envelope 完全可能不同。如果这些契约只写在 YAML 而没有 schema / version / runtime validation，平台会制造“配置正确但语义错”的隐蔽问题。

### 适合谁关注

VLA 研发团队、机器人 foundation model、双臂/人形、仿真到真机流水线、远程 GPU 推理。

### 工程落地启发

如果已有自己的机器人栈，不建议立刻把全部代码迁过去。先把 FluxVLA 当“接口规范参考”：检查自己的系统是否明确拆出了 `dataset adapter`、`model adapter`、`action schema`、`inference transport`、`trajectory adapter`、`robot safety wrapper`。能把这六层独立测试，比盲目引入一个大平台更重要。

## 社区 / 社交平台 · Vibe Coding / AI 编程技巧精选

### A. 用 session fork 做“高风险试验分支”，不要在一个长上下文里反复撤销方向

Claude Code 最近的 release notes 增加了一个实用能力：由 `claude --remote-control` 或 `/remote-control` 启动的 session，可以从 Claude App 直接 fork，fork 后的会话在本机以 background session 运行。[Claude Code Releases](https://github.com/anthropics/claude-code/releases)

**今天就能用的技巧：**当主 session 已经完成大量代码探索，不要为了尝试“换框架 / 大重构 / 改数据库 schema”直接污染主线。先 fork：

```text
main session
  ├─ branch A: 最小修复
  └─ branch B: 激进重构
```

要求两个 fork 最终都输出相同格式的 handoff：改了哪些文件、测试结果、未解决风险、建议保留的 commit。人只比较最终证据，再把选中的实现合回正式工作树。

**适用场景：**大重构、依赖升级、替代方案 A/B、远程控制本地 Coding Agent。

**风险 / 边界：**fork 只是上下文与执行分支，不自动解决 Git 冲突，也不代表不同分支的结论会自动合并。必须把真正要保留的知识落到 commit、测试、文档或 handoff artifact 里，而不是依赖某个 session 自己“记得”。

### B. 长任务恢复时只加载“可验证 handoff + Git 状态”，不要重新灌入整段聊天

今天 r/ClaudeWorkflows 的一个实践总结建议，把子 Agent 或上一 session 的结论写成短小 durable handoff 文件，新 session 先用 Git 验证当前仓库状态，再继续任务，而不是把几十万 token 的历史对话重新放回上下文。[社区原帖](https://www.reddit.com/r/ClaudeWorkflows/comments/1wi35ri/workflow_efficient_session_resumption_for_claude/)

这是**社区经验，不是模型厂商保证**，但它符合一个很可靠的软件工程原则：状态以仓库和可执行证据为准，对话只是推导过程。

**今天就能用的技巧：**给 `HANDOFF.md` 固定成下面几个字段：

```text
Goal
Current commit / branch
Files changed
Decisions / invariants
Commands already run + results
Known failures
Next 3 actions
```

新 Agent 的第一步不是相信 handoff，而是执行：

```text
git status
git log -1
git diff --stat
关键测试 / build
```

验证一致后再继续。这样能把“压缩上下文后模型误记状态”变成一个可检查的问题。

**适用场景：**一个任务跨多天、多个 Agent 接力、上下文频繁 compact、远程/本地混合 Coding。

**风险 / 边界：**handoff 不能只写“已完成”。必须写可复验命令与 commit；如果工作区有未提交修改，也要明确记录，否则新 session 很容易把旧改动当成自己生成的安全基线。

### C. Build / test 必须等到退出码回来再结束 Agent 回合，后台任务不能算“已验证”

另一条当天的 Claude Code 社区实践专门针对一个常见坑：Agent 把 build 放到后台，然后在进程真正失败之前就结束回合，最后给用户一个看似“完成”的总结。[社区原帖](https://www.reddit.com/r/ClaudeWorkflows/comments/1whj598/workflow_claude_code_forcing_foreground_builds_to/)

**今天就能用的技巧：**在项目规则或 skill 里明确：

```text
Verification commands must run in the foreground.
Do not claim success until exit code and final output are observed.
If a command must be backgrounded, poll it and collect its exit status/log before finishing.
```

同时把 build/test 看成任务状态机的一部分，而不是一句自然语言承诺：

```text
EDITED → BUILD_RUNNING → BUILD_EXITED → TESTED → READY
```

没有从 `BUILD_RUNNING` 走到 `BUILD_EXITED`，就不能输出“构建通过”。

**适用场景：**C++/Android/Gradle、大型前端 build、CI wrapper、会启动子进程的测试。

**风险 / 边界：**前台运行不等于无限等待。需要为 build/test 配置合理 timeout；超时应该输出 `TIMEOUT/UNKNOWN`，而不是 PASS，也不能简单 kill 后假装已验证。

## 经典论文回顾

### Rapidly-exploring Random Trees: A New Tool for Path Planning（RRT，1998）——真正的核心不是“随机”，而是 Voronoi bias

Steven M. LaValle 在 1998 年的技术报告 **Rapidly-exploring Random Trees: A New Tool for Path Planning** 中提出 RRT。今天几乎所有机器人 motion planning 工程师都知道“采随机点、找最近节点、向它扩展”，但最值得重新理解的是：RRT 的高效探索不是因为随机本身，而是随机采样隐式产生了 **Voronoi bias**。[LaValle RRT 页面](https://lavalle.pl/rrtpubs.html) / [OMPL planners](https://ompl.kavrakilab.org/planners.html)

### 它解决的核心问题

在高维 configuration space 中，规则网格搜索会遭遇维数灾难。RRT 不试图显式离散整个空间，而是维护一棵从起点生长的树：

```text
q_rand ~ Sample(C)
q_near = Nearest(T, q_rand)
q_new  = Steer(q_near, q_rand)
if CollisionFree(q_near, q_new):
    T.add(q_new)
```

如果均匀随机采样一个 `q_rand`，树上某个节点被选为 `q_near` 的概率，与它在空间中的 Voronoi region 大小相关。位于“尚未探索的大空白区域”边缘的节点通常拥有更大的 Voronoi region，因此更容易被再次选中。

这就是 RRT 会快速向未知空间伸出长枝的原因。

### 为什么它当年很重要

早期 motion planning 很多方法要么依赖精细 configuration-space 构造，要么在高维下计算成本迅速爆炸。RRT 把问题转成增量式 sampling + local propagation，对 holonomic、nonholonomic、kinodynamic 系统都可以使用；LaValle 本人的回顾也指出，RRT 后来被广泛用于自动驾驶、UAV、人形、行星机器人等系统。

它还是典型 **single-query planner**：不需要像 PRM 那样先建立可复用 roadmap，给定 start-goal 后可以立即把计算预算花到当前问题上。

### RRT 的数学直觉

令树节点集合为 `V`，随机点 `q_rand` 服从空间采样分布。节点 `v_i` 被 nearest-neighbor 选中的概率近似等于其 Voronoi cell 的测度：

```text
P(q_near = v_i) ∝ μ(Voronoi(v_i))
```

因此最稀疏、最未探索区域的节点天然获得更高 expansion probability，而不需要显式计算 exploration frontier。

这也是今天 RRT-HAR 论文重新拆解“选哪个节点扩展”和“往哪个方向扩展”的理论入口：经典 RRT 把这两种偏置通过 `q_rand` 与 nearest-neighbor 耦合在一起，而新工作尝试把它们解耦。

### 哪些思想今天仍然在用

现代 OMPL 里的大量 planner 仍保留 RRT 的核心骨架：

- state sampler；
- nearest-neighbor data structure；
- steering / propagation；
- collision checking；
- tree expansion；
- goal bias。

RRTConnect 通过双向树通常能更快找到第一条可行路径；RRT* 加入 rewiring 获得渐近最优；SST 面向动力学系统保持稀疏代表；BIT* / AIT* / EIT* 则进一步引入启发式与隐式随机几何图。

### 哪些部分已经显得不足

经典 RRT 最大的几个问题今天仍然存在：

1. **窄通道低概率。** 均匀采样很难命中关键小体积区域；
2. **只追求可行，不追求路径质量。** 第一条 path 往往曲折；
3. **高维最近邻与碰撞检查昂贵。** 维度升高后，tree growth 本身并不免费；
4. **动力学 steering function 可能很难。** 对复杂系统，简单直线插值没有物理意义；
5. **环境变化时复用有限。** 原始算法并不天然处理动态 obstacle 与在线 repair。

这也是为什么今天的研究会继续做 informed sampling、learned sampling、sparse action、parallel collision checking、kinodynamic propagation 与 trajectory optimization hybrid。

### 现在怎么复现最有价值

不要只跑一次二维迷宫。更有意义的是用 OMPL 做一个“失败机制实验”：

1. 7 DoF 机械臂，设置一个明显 narrow passage；
2. 比较 RRT、RRTConnect、RRT*；
3. 再给 RRT 增加 joint-block sparse sampler；
4. 记录 first-solution latency、collision-check 次数、nearest-neighbor 时间、path length；
5. 把 narrow passage 宽度逐渐缩小，看成功率何时崩掉。

这样会非常直观地看到：RRT 的真正瓶颈不是“随机算法不够聪明”，而是 **采样 measure、扩展偏置与局部连接可行域之间的关系**。

### 2026 年重新看 RRT 的价值

今天很多神经 motion planner 会学习 sampler、cost-to-go 或 latent dynamics，但只要系统仍然需要安全 collision check，经典 RRT 的结构就没有消失：学习模块通常只是替换“在哪里采样、往哪里扩展、哪个节点更值得展开”。

因此读懂 RRT 的 Voronoi bias，比背下某个最新 neural planner 的网络结构更能帮助判断一个新方法到底改进了什么。

## 今日结论

今天的 8 条动态虽然来自 9 月 16 日最新公开批次的继续去重回补，但共同指向几个非常清晰的系统趋势：

1. **安全约束从几何状态走向真实执行能力。** Escape-aware CBF 直接把 body-rate / reachable thrust 拉进认证条件；仅仅“障碍距离大于停止距离”已不够描述高速无人机安全。
2. **协同系统开始修正信息论层面的重复，而不只优化通信。** 多机器人主动探索不仅要共享地图，还要避免共享先验和未来观测被重复计价。
3. **部署后适应正在成为常态。** Traversability continual learning 与 dexterous fault residual 都在回答“上线后环境/执行器变了怎么办”。
4. **学习策略更愿意承认经典控制的价值。** IL-ACT 用 imitation policy 提供 nominal 行为，把精确跟踪、偏差估计与 reference safety 交还给闭环控制器。
5. **VLA 工程竞争开始从模型扩展到平台。** FluxVLA 的意义不一定是它会成为统一标准，而是它暴露了当前真机 VLA 流水线最缺少的接口层：数据契约、动作 schema、远程推理、轨迹连续性与 human takeover。
6. **Coding Agent 也在走相同路线：把状态与验证外置。** session fork、handoff artifact、前台 build/test 都是在减少“模型说完成了”和“系统真的完成了”之间的差距。

## 最值得深入研究或尝试复现的方向

**首选：Escape-Aware CBF + 现有 PX4 / MPC 日志离线回放。** 不必第一天就做飞行实验。先从 rosbag / ulog 中提取位置、速度、姿态、body-rate、推力指令和最近障碍距离，对每帧同时计算 stopping-distance margin 与 escape-aware 近似 margin，找出传统 barrier 会判安全、但姿态转向已经来不及的片段。这能快速判断论文问题在自己的飞行平台上是否真实存在。

**第二：给多机器人 frontier planner 加 expected sensing footprint 去重。** 先不用完整 active inference，把每台机器人的未来视场/激光覆盖投影到 occupancy grid，其他机器人在 frontier score 中扣掉队友已承诺覆盖的部分。若探索完成时间和路径重复明显下降，再引入真正 belief increment。

**第三：在现有地形分割后加 uncertainty 与持续学习数据闭环。** 对 MID360 / 16 线雷达的 elevation/traversability map，先标出模型不确定区域，再关联轮速、IMU、足端/机体响应，自动生成“新地形候选样本”。这比直接在线训练主网络更安全，也更容易验证。

**第四：用 OMPL 复现 RRT-HAR 的核心思想，而不是直接复刻整篇论文。** 在高 DoF 机械臂上实现 joint-block sparse perturbation 和 direction sampler 分离，量化 collision-check 数量与窄通道成功率。若简单版本已经有收益，再考虑完整 HAR hybrid。

**第五：给 Coding Agent 的 Definition of Done 增加机器可检查状态。** 强制要求最终输出附带 commit / diff、build exit code、test summary 与 remaining failures；handoff 只传这些持久证据。这样即使换模型、compact 上下文或 fork session，也不依赖聊天历史来判断工程状态。

## 参考资料

- [arXiv Robotics Recent](https://arxiv.org/list/cs.RO/recent)
- [Escape-Aware Control Barrier Functions for Quadrotor Safety under Body-Rate Limits](https://arxiv.org/abs/2609.17292)
- [Exact Fusion and Coordinated Exploration in Multi-Robot Active Inference](https://arxiv.org/abs/2609.17384)
- [Continual Learning for Traversability Prediction with Uncertainty-Aware Adaptation](https://arxiv.org/abs/2609.17141)
- [Motion planning in high dimensional spaces hybridizing RRT and HAR via position-direction decoupling](https://arxiv.org/abs/2609.16810)
- [Residual Fault Adaptation for Dexterous In-Hand Manipulation Under Runtime Joint Faults](https://arxiv.org/abs/2609.17404)
- [IL-ACT: Imitation Learning with Adaptive Cartesian Tracking Control for a 30-ton Excavator](https://arxiv.org/abs/2609.16696)
- [CorrRisk-WM: Corridor-Conditioned Risk World Modeling for Safety-Critical Trajectory Planning](https://arxiv.org/abs/2609.16724)
- [FluxVLA Engine: A One-Stop VLA Engineering Platform for Embodied Intelligence](https://arxiv.org/abs/2609.17210)
- [FluxVLA Engine GitHub](https://github.com/FluxVLA/FluxVLA)
- [Claude Code Releases](https://github.com/anthropics/claude-code/releases)
- [Reddit: Efficient Session Resumption for Claude Code Agents using External Handoffs and Git Verification](https://www.reddit.com/r/ClaudeWorkflows/comments/1wi35ri/workflow_efficient_session_resumption_for_claude/)
- [Reddit: Claude Code — Forcing Foreground Builds to Prevent Silent Failures](https://www.reddit.com/r/ClaudeWorkflows/comments/1whj598/workflow_claude_code_forcing_foreground_builds_to/)
- [Steven M. LaValle: Rapidly-exploring Random Trees](https://lavalle.pl/rrtpubs.html)
- [OMPL Available Planners](https://ompl.kavrakilab.org/planners.html)
