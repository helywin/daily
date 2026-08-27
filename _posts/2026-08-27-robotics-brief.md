---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-27"
date: 2026-08-27 09:00:00 +0800
description: "本期聚焦 STL-MPPI、欠驱动可信动作集、四足动力学残差适应、VLA 推理延迟、事件相机高速运动估计、机器人世界模型动作一致性与仓库级 Coding Agent。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-27

## 摘要

截至 2026-08-27 09:00（Asia/Shanghai），arXiv Robotics 的最新公开列表已经刷新到 2026-08-26：`new` 页面共有 77 个条目，其中 32 个为 Robotics 新投稿；`recent` 页面中 8 月 26 日共有 42 个 Robotics 相关条目。Software Engineering 的 8 月 26 日 `new` 页面共有 62 个条目，其中 33 个为新投稿。本期先检查严格最近 24 小时，再结合已覆盖索引进行标题、arXiv ID、代码仓库和项目主页联合查重；严格 24 小时内能够完整核验、足够高质量且未报道的主动态不足 5 条，因此按规范扩大到最近 7 天。

本期最值得优先看的是两个控制 / 规划方向。第一，**Safety-aware STL-MPPI** 尝试把 Signal Temporal Logic 从“任务说明”真正变成 sampling MPC 的运行约束：离散时间 STL 被递归编译成 time-varying Control Barrier Function，再嵌进 MPPI。它的意义并不是声称 sampling controller 从此拥有无条件形式保证，而是让“始终避开危险区域、在时间窗内到达、先做 A 再做 B”这类时序任务第一次更自然地进入大规模并行 rollout。第二，**Trusted Polytopic Action Sets** 不再把欠驱动规划的一个 tree node 理解成一个状态，而是局部构造一整块可信的凸动作族；碰撞和控制边界在线性动作坐标中处理，非线性动力学误差则通过 trust region 截掉，最终长时域规划可以在“可复用的动作多面体”之间扩展。论文在拥挤平面场景中报告几十毫秒求解，并比 kinodynamic RRT 快 14–78 倍。

四足控制方面，**CARO** 是本期很值得工程尝试的工作。它没有继续训练一个黑盒 history encoder 去猜 payload、摩擦和接触，而是把一个刻意简化的 fixed-base Euler–Lagrange 模型放进 RL loop，通过 momentum/disturbance observer 形成 joint-level residual。这个 residual 不要求 F/T sensor、显式接触识别，也不要求浮动基座线速度，而是作为“动力学和接触分布正在偏离名义模型”的结构化反馈交给 policy。DeepRobotics Lite3 真机上，CARO 在无硬件微调条件下完成 unseen terrain、偏心载荷、8.5 kg 负载以及 0.2 m 平台落地测试。

VLA 侧，**Learning to Act While Waiting** 把推理延迟从“部署工程问题”提升为 RL 的状态定义问题。大型 VLA 一次生成常常需要明显时间；如果机器人一边执行旧 action chunk、一边等待新动作，环境已经继续演化，标准 RL 却仍把 observation/action 当作同步 Markov transition，训练会系统性失真。ARLI 通过把 committed actions 和 inference 中途的新观测加入状态，恢复近似 Markov 结构；论文 v2 在 8 月 26 日刚刚修订，因此本期按“最近 24 小时修订”处理。

感知 / SLAM 前端方面，**ODF Motion Estimation** 值得事件相机方向关注。它不是完整 VIO/SLAM，而是一个极低延迟运动原语：用预计算 oriented distance field，把常见的迭代运动优化改成一次向量平均，再配合自适应事件数量和无参数 trail filter。论文报告运动估计达到 per-event 亚微秒级延迟，并展示了实时去模糊与低功耗眼动追踪。它的真正价值是说明 event sensor 的微秒级时间分辨率不应该被一个毫秒级迭代优化器重新吃掉。

机器人世界模型方面，**WorldEcho / WorldSync** 给出一个很重要的负面结论：世界模型在专家 action 上“视频看起来对”并不代表它真的服从动作。作者扩大 action query 到 off-expert 区域，用视觉完整性和 SE(3) 末端轨迹共同检查，发现现有模型常常直接忽略输入动作，或者生成视觉崩坏结果。WorldSync 从动作分布覆盖、Action-Forcing representation grounding 和 intervention-effect alignment 三方面增强动作一致性；RoboTwin 策略迭代从约 51–52% 提升到 65%，真实叠杯从 48% 提升到 68%，显著高于 CtrlWorld 的 56%。

AI Coding 侧，本期两条工作都值得真实研发平台参考。**DeepRepoQA** 将仓库理解从“一次 semantic search + 回答”变成 MCTS 式多跳探索，搜索树中的路径保留跨文件证据；扩展版 SWE-QA 含 15 个仓库、720 对 QA，最大提升相对 SWE-agent 达 7.08 分。**SWE Refactor Bench** 则专门打击“测试通过但根本没完成迁移”的假成功：20 个整仓迁移任务使用 Migration Audit、固定行为测试和 6 个独立 Agent 的对抗验证三级验收；520 次运行只有 28 次，也就是 5.4%，通过全部阶段。这对长期自动化重构比普通 bug-fix benchmark 更接近真实工程难度。

本轮同时检查了 OpenAI 等主流模型厂商的近期官方入口。OpenAI 8 月 26 日主要更新集中在安全事件、教育和产品内容，8 月 25 日是 Jalapeño 推理芯片实测与基础设施更新；没有出现需要挤掉上述机器人 / 控制条目的全新旗舰基础模型正式发布，因此本期不使用旧模型新闻补位。

## 1. Safety-aware STL-MPPI：把“始终 / 最终 / 时间窗”从文字要求编译进采样 MPC

**时间回补：论文 v1 提交于 2026-08-25 02:00:50 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.23972)，[项目页](https://zhaoy37.github.io/safety-aware-stl-mppi/)）

### 为什么重要

MPPI 很擅长处理非凸 cost、复杂动力学和 GPU 并行，但传统 cost shaping 很难清楚表达时序任务：比如“未来 8 秒内必须到目标，同时全过程不能进入危险区”“必须先完成观测再经过区域 B”。常见做法是不断叠 penalty，最后 reward/cost 参数很难解释，也很难知道某个 rollout 到底是“稍微差一点”还是已经违反硬任务规格。

这项工作把离散时间 Signal Temporal Logic（STL）递归转换成候选 time-varying CBF，再交给 MPPI 的 rollout / weighting 机制使用。它让时序逻辑不再只存在于高层 planner，而能直接影响 receding-horizon 控制。

### 算法模块

系统仍保留标准 MPPI 的基本骨架：名义控制序列周围并行采样大量 perturbation，前向 rollout 动力学、计算 cost、用指数权重更新控制序列。新增部分是：

- 将离散 STL 公式分解成时变谓词和组合算子；
- 为候选公式构造 time-varying barrier；
- 用 CBF 条件把 STL 约束转化成 rollout 的安全 / 任务可行性评价；
- 对时变 horizon 进行 receding-horizon 重算；
- 对 Mars Rover 任务和 Isaac Lab 四旋翼进行验证。

### 动力学与传感器假设

论文的理论构造建立在离散动态系统上，并重点讨论 control-affine dynamics 与 box input constraints。真实机器人仍然需要可靠的状态估计和障碍 / 任务谓词；如果 perception 错误地把危险区域判断为安全，STL/CBF 只会严格执行一个错误世界模型。

另一个要准确理解的点是：论文给出了基于 CBF 的 STL 安全构造，但名义实时实现为了计算效率使用近似；因此不能把“带 CBF”直接包装成所有条件下的形式安全证书。更严谨的做法仍是保留独立 runtime monitor 与超时 / 不可行回退。

### 实时性、鲁棒性与可复现性

作者强调 MPPI 的并行计算优势，并在多个 Mars Rover 场景中相对 MPPI baseline 获得更好的安全与效率，同时展示 Isaac Lab 四旋翼规划。项目页已公开，适合复现 STL 到 MPPI 的接口。

真正落地时应该分别测：P50/P95/P99 rollout latency、STL satisfaction、CBF 近似造成的保守性，以及当任务公式突然变化时 nominal sequence 能否及时重置。

### 风险

复杂 STL 会使 barrier 变得更保守或带来长 horizon；而 MPPI 仍然是 sample-based planner，有限采样预算下没有“必然找到可行解”的保证。若当前状态已经离开可恢复域，系统必须明确进入 stop / safe fallback，而不是继续靠增大 sample 数“赌一个解”。

### 适合谁关注

无人机、移动机器人、行星 rover、安全强化学习 / MPC、需要把自然语言任务进一步编译成机器可验证时序约束的团队。

### 工程落地启发

可以先从非常小的规格集开始：`always obstacle_distance > d`、`eventually goal_reached within T`、`A before B`。让上层 LLM 只能生成受限 STL schema，经过独立 parser / validator 后再进入 MPPI，避免直接让语言模型控制 cost 函数。

## 2. Trusted Polytopic Action Sets：欠驱动规划的 Tree Node 不再是一条轨迹，而是一整族可信可达动作

**时间回补：论文 v1 提交于 2026-08-25 03:18 UTC，已被 IEEE Control Systems Letters 接收；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.24019)，[代码](https://github.com/akshay5312/paamp_underactuated)）

### 为什么重要

欠驱动系统的可行运动并不是状态空间中一块简单的凸区域，而是受动力学约束的一条薄而弯曲的 trajectory manifold。传统 RRT 每扩展一次只得到一条 trajectory；GCS / IRIS 等凸方法虽然能高效处理几何自由空间，却很难直接保证非线性动力学一致性。

PAS 的核心转变是：围绕一条 nominal feasible trajectory 建立局部 action coordinate，把一整个邻域的“完整短时轨迹”表示成一个低维参数向量。这样 tree 每个节点携带的不是一个末端状态，而是一块可重复查询、可组合的 reachable family。

### 算法模块

- 在 nominal trajectory 周围做 LTV 近似；
- 用有限维 action coordinate `γ` 参数化完整附近轨迹；
- 碰撞半空间和 actuator limit 在 `γ` 中变成线性约束；
- 用 dynamics-violation metric 评价线性近似偏离真实非线性动力学的程度；
- 使用 IRIS-inspired zeroth-order inflation 在 action space 中提取可信 convex inner approximation；
- 多个 PAS 可以继续组合成更长的凸 reachable family；
- PAS-RRT 用 LP 做 goal containment / target projection，再扩展新的可信动作集。

官方实现采用 C++/CUDA、HiGHS / OSQP，并支持 cartpole、acrobot、Dubins 等内置动力学，仓库采用 MIT License。

### 动力学与规划假设

PAS 的可信性建立在 nominal 轨迹附近。非线性非常剧烈、接触模式突变或 nominal 本身离可行流形很远时，local affine map 和 dynamics trust region 可能迅速缩小。

因此它很适合“局部可行族 + 全局树搜索”，但并不是把任意接触丰富系统自动凸化。腿式落脚切换、碰撞冲击和离散模式仍可能需要单独 hybrid model。

### 实时性与结果

论文报告 cluttered planar scene 中几十毫秒求解，速度比 kinodynamic RRT baseline 快 **14–78 倍**；在 nonlinear underactuated benchmark 上 terminal error 相对 sampling / NLP baseline 降低 **26–86%**。这组结果说明“把局部动态可行区域保存成可复用集合”比每次只保留一条 rollout 更有长期规划价值。

### 鲁棒性、可复现性与风险

代码已经公开且包含 C++/CUDA、Python binding 和测试，复现条件相对好。风险在于 trust tolerance 如何设置：太小会把可达集压得很保守，太大则会让 nominal linearization 与真实非线性系统偏差增大。

### 适合谁关注

欠驱动无人机 / 航空器、cartpole / acrobot 类系统、kinodynamic planning、希望把凸优化和 RRT 结合的团队。

### 工程落地启发

如果已有 sampling planner，可以考虑不再缓存“最好的一条轨迹”，而是缓存局部 action family：当前状态附近哪些短时控制在碰撞、输入和动力学误差上都可信。后续 goal / obstacle 改变时，可以直接 LP 查询已有 family，而不是从头 rollout。

## 3. CARO：用简化刚体模型的残差给四足 RL 一个结构化“动力学异常感知”通道

**时间回补：论文 v1 提交于 2026-08-25 08:23:24 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.24217)）

### 为什么重要

四足策略遇到 payload、CoM 偏移、地形变化、滑移或落地冲击时，最常见方案是依赖更大 domain randomization 或 history encoder，让网络自己从历史中隐式推断“环境变了”。这类 latent adaptation 有效，但结构上很难知道网络到底在感知什么。

CARO 采取非常工程化的折中：在 policy 外并行放一个 fixed-base Euler–Lagrange internal model。这个模型明知不完整——真实四足当然是 floating-base、还有接触力——但恰恰利用“模型不完整后产生的 joint-space residual”作为 deployment-time adaptation signal。

### 算法模块

policy 输出关节位置增量，经低层 PD 形成 torque command。CARO 用固定基座刚体模型计算名义 joint dynamics，再通过 momentum-based disturbance observer 估计 residual，不需要显式数值微分关节加速度。

这个 residual 混合了：

- joint contact loading；
- payload / external disturbance；
- floating-base coupling mismatch；
- motor tracking error；
- nominal dynamics error。

CARO 并不试图把这些因素逐一物理辨识，而是把 residual 直接附加到 policy observation，让 RL 自己学习“这种残差模式下应该怎么走”。

### 传感器与动力学假设

CARO observer 本身只需要关节位置、关节速度和 torque command，不要求 F/T sensor、contact state、floating-base position 或 base linear velocity。真机 actor 同样不依赖不可直接测量的 base linear velocity。

但 residual 是“lumped mismatch”，不能拿来做精确接触力控制或故障诊断。高速运动中，固定基座近似误差可能反而主导 residual。

### 实时性与实体结果

同等训练条件下，CARO 在 25 个 payload-terrain 组合上平均成功率 **88.6%**；在 3 倍 nominal base mass 下仍有 **64.5%**，RMA 为 36.4%，RL2AC 为 0.2%，Vanilla 为 0%。

实体 DeepRobotics Lite3 不做 hardware-specific policy fine-tuning，只增加最近 5 帧 observation history 以降低实机振动。CARO 可在 2.5 kg 负载下穿越四种未见地形，偏心负载下保持航向，最大稳定前进负载达到 **8.5 kg**；Vanilla 在 6.5 kg 已无法完成测试。0.2 m 平台落地 CARO **3/3** 成功，Vanilla **3/3** 跌倒。

### 鲁棒性、可复现性与风险

作者明确指出：residual observer 的误差 boundedness 并不等于整个 learned closed-loop system 已经被证明稳定。observer gain 越高响应越快，但也更放大关节测量噪声。

当前没有稳定公开代码入口，可复现性主要依赖固定基座模型、observer gain 与和 policy observation 的集成细节。

### 适合谁关注

四足、轮足机器人、载荷变化大的巡检机器人、希望把传统 disturbance observer 与 RL policy 结合的团队。

### 工程落地启发

这个思想可以先作为“健康度通道”而不是直接改 policy：计算 `model-predicted joint response - actual joint response`，在 rosbag 中观察它是否能更早识别载荷、滑移、台阶冲击和机构异常。确认 residual 具有区分度后，再把它接入 RL / MPC 参数调整。

## 4. ARLI：VLA 的推理延迟不是简单卡顿，而是在改变 RL 看到的动力学

**最近 24 小时修订：v1 提交于 2026-08-24 21:19:50 UTC，v2 于 2026-08-26 14:32:04 UTC 修订；本期首次覆盖。**（[论文](https://arxiv.org/abs/2608.23831)，[项目页](https://async-rl-intermediate-information.github.io/)）

### 为什么重要

大型 VLA 在机器人端常见两种策略：同步等待——生成动作时机器人暂停；异步执行——一边执行上一段 action chunk，一边后台生成下一段。后者看起来更流畅，但对 RL 来说会产生一个根本问题：当新的 observation 被送入模型时，机器人接下来一段时间还会继续执行旧动作；等新 action 返回时，世界已经变化。标准 MDP 中的 `s_t, a_t, s_{t+1}` 因此不再对齐。

论文指出这会破坏 Markov assumption，使标准在线 RL 在有明显 inference delay 的 generalist policy 上直接失效。

### 算法模块

ARLI（Asynchronous RL with Intermediate Information）仍使用异步 inference，但扩充低延迟 RL state：

- 显式加入已经 committed、在模型计算期间仍会继续执行的动作；
- 在 inference window 中途获取一次新 observation；
- 用这些信息恢复近似 Markov state；
- policy 更新针对“真正执行时机器人已经到哪里”学习，而不是假设 action generation 瞬时完成。

### 传感器与控制假设

ARLI 依赖能够在模型 inference 中途继续采集 observation，并且底层执行器能够安全执行 committed action。对接触丰富任务，如果旧 chunk 已经在错误方向持续执行，单纯更聪明地处理 latency 也不能代替 contact watchdog、碰撞限位和 action freshness 检查。

### 实时性与真实机器人

论文在仿真和真实 manipulation 中评估，结论是：存在推理延迟时，标准 RL 可以完全失效，而 ARLI 能继续有效 post-training，甚至达到或超过理想化无延迟标准 RL 的表现。

工程上更重要的是它提出了一个测试原则：VLA benchmark 不应只报告模型 forward latency，还应报告 observation timestamp、generation completion timestamp、action start timestamp 与 action age。

### 鲁棒性、可复现性与风险

v2 在 8 月 26 日刚修订，论文和项目页可访问。风险主要是异步控制中的 stale action：如果感知突然变化，例如有人进入工作区或物体滑落，已 committed 的 action 必须能够被更高优先级安全通道打断。

### 适合谁关注

VLA 在线 RL、action chunking、移动操作、双臂策略，以及当前遇到“离线会做、真机一加模型延迟就抖 / 停 / 失败”的团队。

### 工程落地启发

建议把每个 action chunk 都带上 `generated_from_observation_time / valid_from / valid_until / preemptible`。底层 controller 不应只接收数值动作，还要知道动作有多旧；超过 freshness threshold 直接降速、重观测或停止。

## 5. ODF Motion Estimation：事件相机的运动估计不应该用迭代优化把微秒优势重新吃掉

**时间回补：论文 v1 提交于 2026-08-25 08:27:42 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.24223)）

### 为什么重要

Event Camera 的价值是微秒级时间分辨率和高速动态范围，但很多 event-motion 方法仍要反复 warping、假设比较或非线性优化。最后 sensor 很快，算法却在毫秒级才给出结果。

ODF Motion Estimation 的核心是把当前 event 与模板边缘之间的运动信息预计算成 oriented distance vector field。新事件进来后不再重新求一个大优化问题，而是从 field 查向量并做一次聚合；自适应 event-count selection 决定当前需要多少事件，无参数 trail filter 抑制事件拖尾。

### 算法模块

- 从参考边缘构建 oriented distance field；
- 对流入 event 读取方向距离向量；
- 单次 averaging 得到 motion estimate；
- 根据运动 / event rate 自适应选择 event 数；
- 使用 parameter-free trail filter；
- 将估计轨迹直接转为 blur kernel；
- 同一个 field 也用于低功耗 pupil / glint directional filtering。

### 传感器与运动假设

这不是完整 6DoF SLAM。论文当前主要假设 globally consistent motion，且下游两个应用使用 **2-DoF translation**。模板如果被单一方向边缘主导、事件过稀或场景存在多个独立运动体，估计会退化。

因此它更适合作为高速视觉前端原语、gimbal/PTZ motion、图像去模糊或事件跟踪模块，而不是直接替代 VIO/LIO。

### 实时性与结果

论文报告 motion estimation 达到 **per-event 亚微秒级延迟**，并在公开与自采数据上取得 sub-pixel accuracy。去模糊分支使用不足 1M 参数的轻量迭代展开网络；一个 0.6M 参数配置在真实数据上取得有竞争力的 PSNR / SSIM。

### 鲁棒性、可复现性与风险

算法没有复杂在线优化器，计算路径清晰；但对 reference template、edge orientation diversity 和事件质量敏感。目前论文页面未稳定给出官方代码仓库，因此复现需要自行实现 field construction 与 event filtering。

### 适合谁关注

高速无人机视觉、事件 VIO 前端、gimbal、快速转台、视觉去模糊和超低延迟边缘计算团队。

### 工程落地启发

在高速机器人上可以把 event frontend 独立成一个高频 motion monitor，不一定直接参与主滤波：持续输出 image-plane motion / angular-rate proxy，与 IMU / VIO 预测比较。一旦出现持续不一致，就触发 motion blur、IMU saturation、timestamp error 等健康检查。

## 6. WorldEcho / WorldSync：机器人世界模型“会生成未来”之前，先证明它真的服从输入动作

**时间回补：论文 v1 提交于 2026-08-25 17:59:49 UTC，并进入 8 月 26 日 Robotics 最新公开批次；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.24885)）

### 为什么重要

World Action Model 越来越被当成训练和评测机器人的“便宜模拟器”。但这里有一个容易被视频质量指标掩盖的前提：你给模型 action A，它生成的未来必须真的对应 A。

过去 benchmark 通常使用 expert demonstrations；模型只要在训练分布附近生成看起来合理的视频，就容易拿到好分。一旦 policy post-training 开始探索 off-expert action，世界模型可能出现两类问题：忽略动作，继续生成更“常见”的专家行为；或者动作跟了，但视频整体崩坏。

### WorldEcho：先测动作服从性

WorldEcho 不只看 PSNR / 视频视觉质量，而把 query 扩展到更宽的 numerical action distribution，并同时检查：

- visual integrity；
- 生成视频中恢复的末端 SE(3) trajectory；
- 与 simulator replay 同一 action 后的真实轨迹对齐。

这样可以直接区分“视频合理但动作没执行”和“动作执行了但画面失真”。

### WorldSync：从三个方向修复

- **Expanded Action Coverage**：扩大训练时动作后果覆盖；
- **Action-Forcing Expert**：让中间表示更强地 grounding 到 action-induced robot dynamics；
- **Intervention-Effect Alignment**：比较动作干预前后真实未来的变化，强制模型学习“动作改变会造成什么变化”。

### 结果与真实机器人

RoboTwin 策略改进实验从相近的 51–52% 初始成功率出发，两轮后 WorldSync 达到 **65%**；CtrlWorld 只达到 56–57%。

真实叠杯任务两组都从 **48%** 出发，两轮后 WorldSync 达到 **68%**，CtrlWorld 为 **56%**。消融显示 intervention-effect supervision 是 trajectory alignment 的主要驱动因素，而 Action-Forcing Expert 更像在动作一致性与视觉有效性之间平衡。

### 风险与工程边界

世界模型即使更忠实地跟动作，也仍然不是安全 simulator。真实摩擦、接触力、传感器偏差和长尾物理可能没被视频 latent 捕获。

产品中应把 world model rollout 理解为**候选评估证据之一**，继续由几何碰撞、动力学约束、真实安全监控做最终 gate。

### 适合谁关注

WAM/VLA、离线 policy improvement、世界模型模拟器、机器人数据生成和 sim replacement 团队。

### 工程落地启发

内部评估世界模型时至少增加一项 `action replay audit`：随机采样 expert 附近和明显 off-expert 的可执行 action，拿真实 / 高保真 simulator replay 得到 ground truth trajectory，再对 world model rollout 做 SE(3) trajectory alignment。只看 FVD / 视频质量已经不够。

## 7. DeepRepoQA：仓库问答从一次检索升级成 MCTS 多跳“侦察树”

**时间回补：论文 v1 提交于 2026-08-25 08:26:31 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.24221)，[代码](https://github.com/peng-weihan/DeepRepoQA)）

### 为什么重要

很多 Coding Agent 的 repository QA 本质上仍是：向量检索几个文件，把片段塞进 prompt，再让模型回答。遇到“这个状态是从哪里写入、经过哪些 wrapper、最终为什么在另一个模块失效”这种跨 5–10 个文件的问题，一次检索很难拿全证据。

DeepRepoQA 把 repository navigation 变成搜索问题：每个 action 是打开文件、跟踪 symbol、继续搜索或验证假设；MCTS 平衡 exploration / exploitation，LLM feedback 给搜索分支提供 prior/value，避免 Agent 在一个看起来相关但实际错误的模块里一路深入。

### 系统模块

- code indexing / semantic search；
- MCTS search tree；
- Perception Agent 组织当前仓库观察；
- Evaluation Agent 对当前假设 / 答案打分；
- structured memory path 保存跨文件证据；
- 最终答案从已验证的 search path 综合，而不是只依赖一次 context window。

### 结果

扩展 SWE-QA 包含 **15 个仓库、720 对 QA**。DeepRepoQA 在 Kimi K2、GLM-4.6、Qwen3-Coder-480B、GPT-5.1 上都相对 ReAct-style agent 获得提升；最大提升是在 Qwen3-Coder 上相对 SWE-agent **+7.08 分**。消融显示 MCTS 是最关键组件，semantic search、Evaluation Agent 和 Perception Agent 进一步改善稳定性。

代码仓库已经公开，采用 Apache-2.0 / MIT 相关开源声明，包含单仓库 / 批量示例以及 SWE-agent、Cursor-Agent、OpenHands 风格对照脚本。

### 突破性工程价值

它说明“更深仓库理解”不一定需要无限加 context，而可以通过**结构化搜索预算**获得。对于企业代码库，Scout 阶段甚至可以使用较便宜模型，通过树搜索把关键 evidence package 交给后续强模型。

### 权限、安全与可验证性风险

MCTS 会显著增加 tool call 和 token 数；如果搜索工具具有写权限，树搜索会放大误操作风险。因此 repository QA 阶段应默认 read-only，并固定 git revision。

LLM-as-a-Judge 也不能替代真实代码证据。最终答案最好附 symbol path、文件行、commit SHA，而不是只输出自然语言结论。

### 适合谁关注

企业代码搜索、Coding Agent Scout、架构问答、长期 monorepo、需要跨文件 root-cause 分析的团队。

### 工程落地启发

可以先不用完整 MCTS，实现一个 bounded evidence tree：每个问题最多 20 次搜索 / 打开动作，每个节点必须写 `hypothesis / evidence / next query`，最终答案必须能回溯到具体文件与 revision。这样就已经比“向量搜 10 段”更可审计。

## 8. SWE Refactor Bench：整仓迁移最危险的假成功，是“什么都没迁但测试全绿”

**时间回补：论文 v1 提交于 2026-08-24 17:59:04 UTC；此前未进入覆盖索引。**（[论文](https://arxiv.org/abs/2608.23564)，[代码与评测](https://github.com/Einsia/SWE-Refactor-Bench)）

### 为什么重要

Bug-fix benchmark 里“测试通过”通常比较合理；但 stack migration 不一样。一个 C→Rust、Python→Go、旧构建系统→新工具链的任务，在 Agent 开始之前原程序本来就是正确的。Agent 最简单的作弊方式就是保留原实现，只在外面套一点新文件，行为测试依然全过。

SWE Refactor Bench 将这种问题称为 **Blindness**：行为正确性无法证明迁移真的发生了。

### 三级验证结构

**1. Migration Audit**

检查新实现是否真正进入 default path，旧 source/dependency/release closure 是否已经离开；这一阶段不运行项目本身，避免 Agent 通过兼容 wrapper 伪装迁移。

**2. Behavioural Tests**

在新旧环境中构建并比较 artifacts、endpoint、installed layout 和 upstream tests，要求 drop-in compatibility。

**3. Agentic Verification**

6 个独立 Coding Agent 获得两套构建好的树，各自尝试构造“原版本通过、新版本失败”的反例；反例要重复三次才计入。

### 结果

Benchmark 包含 **20 个整仓迁移任务、4 类技术债**。8 个 frontier model、26 组 model-effort 配置共 **520 次运行**，只有 **28/520（5.4%）**通过全部三阶段；20 个任务里 **13 个没有任何一个 accepted solution**。最佳模型 Claude Opus 5 得分 **47.0/100**。

340 个通过 Migration Audit 的运行中，58% 可以通过 99% 固定检查，但只有 26% 达到 100%。Build toolchain rewrite 得分 31.4，而 language rewrite 只有 5.6，说明长时域迁移仍明显超出现有 Agent 的稳定能力。

### 突破性工程价值

这套 benchmark 最值得复制的是“迁移完整性”和“行为正确性”分开。企业内部做 Qt5→Qt6、ROS1→ROS2、Java/Spring 大版本、CMake/Bazel 或数据库框架迁移时，CI 不应该只问“旧测试还过吗”，还要验证旧依赖、旧入口和过渡 shim 是否真的退出生产路径。

### 权限、安全与可验证性风险

整仓迁移会修改构建链、依赖与发布产物，Agent 应在隔离 branch/worktree 中运行；Stage 1 / 2 / 3 最好使用不同容器环境，防止旧工具链偷偷留在测试镜像里让迁移“看似成功”。

### 适合谁关注

Codex / Claude Code / OpenHands、自建代码迁移平台、大规模 legacy modernization、企业 monorepo。

### 工程落地启发

内部自动迁移任务至少建立三张清单：`必须消失的旧技术证据`、`必须保持的行为 contract`、`独立生成的反例测试`。Agent 只有同时满足三张清单才能宣布完成。

## 经典论文回顾

### RRT*：为什么“能找到路径”和“采样越来越多后趋近最优”是两件完全不同的事

**发表时间与历史位置：** Sertac Karaman 与 Emilio Frazzoli 的 RRT*/PRM* 理论工作最早在 RSS 2010 形成代表性版本，系统长文《Sampling-based Algorithms for Optimal Motion Planning》于 2011 年公开并发表于 IJRR。它把 sampling-based planning 从“概率完备”推进到“渐近最优”的理论阶段。（[论文](https://arxiv.org/abs/1105.1186)，[RSS 2010](https://roboticsproceedings.org/rss06/p34.html)，[OMPL RRT*](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1RRTstar.html)）

### 核心问题

经典 RRT 的优势是快速探索高维空间，并且在存在可行路径时，采样数增加后找到路径的概率趋近 1，也就是 probabilistic completeness。但这并不意味着树越长，路径 cost 就越接近最优。

Karaman/Frazzoli 的关键负面结果是：在温和条件下，普通 RRT 返回路径的 cost 几乎必然收敛到一个**非最优值**。因此“找到一条可行解”和“随着计算继续进行不断改善到最优”是两个不同性质。

### RRT* 的关键数学思想

RRT* 仍然随机采样自由空间，但新节点插入时不只连接最近节点，而会检查一个随样本数量变化的 near-neighbor 邻域：

1. 在邻域中选择能够产生最低 cost-to-come 的 parent；
2. 插入新节点；
3. 再检查邻域已有节点，如果通过新节点能降低其 cost，就执行 **rewiring**；
4. 随着样本数增加，邻域尺度按照 random geometric graph 理论缩放。

这个小小的 rewiring 让树从“只扩张覆盖”变成“边探索边改良已有拓扑”。论文证明 PRM* 和 RRT* 在相应条件下具有 asymptotic optimality，而且计算复杂度仍与原 probabilistically-complete 对应算法处于常数因子量级。

### 动力学与传感器假设

经典 RRT* 更自然地工作在 configuration/state space 中，假设能够：

- 从样本中生成状态；
- 计算 local connection / steering；
- 检查碰撞；
- 定义可加的 path cost。

对于强欠驱动、非完整或接触系统，“两点之间连一条直线”并不是真实可执行轨迹，因此需要 kinodynamic RRT*、trajectory rollout、motion primitive 或今天 PAS 这类局部动作集作为 steering mechanism。

它本身也不处理感知误差：地图错误、状态估计漂移和动态障碍都需要外层系统解决。

### 当年为什么重要

它第一次非常清楚地告诉机器人社区：sampling-based planner 的理论评价不能只停留在“最终能否找到解”。如果机器人愿意继续花计算时间，算法是否具有 **anytime improvement** 和最终 cost 质量同样重要。

论文还把机器人规划与 random geometric graph 理论连接起来，为后来的 RRT#、Informed RRT*、BIT*、FMT* 等大量算法提供理论基础。

### 今天仍然使用的思想

- 先快速得到可行解，再持续改良；
- 邻域连接与 rewiring；
- 搜索半径 / k-nearest 数量应该随样本规模变化；
- global exploration 与 local connection 明确分工；
- planner 的质量不能只看 success rate，还要看 cost 随预算的收敛曲线。

### 已被后续方法替代或扩展的部分

现代系统经常使用 Informed RRT* 在已有解之后只采样可能改善解的椭球区域；BIT* 将启发式图搜索与采样结合；机器人实时规划还大量采用 kinodynamic RRT、motion primitive、MPC、MPPI、trajectory optimization 和 learned proposal。

因此 RRT* 不一定是今天每个机器人最好的在线 planner，但仍然是衡量“全局探索、渐近最优、任何时预算”最重要的基线之一。

### 公开代码与可复现性

OMPL 至今提供成熟 RRT* 实现，可配置 range、rewiring factor、k-nearest / radius、informed sampling、tree pruning 等参数。复现成本很低，非常适合作为新规划器的 independent baseline。

### 对当前工程项目的重新解读

今天把 RRT* 与本期 Trusted PAS 放在一起看尤其有意思：RRT* 的 tree node 是状态，PAS-RRT 的 node 可以是一整块 reachable family。可以把现代学习 / 优化器的角色理解成**提升 local connection 质量**，而 RRT* 式全局搜索仍负责避免局部最优。

对无人机或机器狗，比较合理的混合结构是：

```text
全局拓扑 / Sampling Tree
        ↓
学习或模型引导的局部 Proposal
        ↓
动力学 Rollout / Trusted Action Set
        ↓
Collision / Reachability Gate
        ↓
Rewire / Cost Improvement
```

不要让“神经网络一次给一条看起来不错的轨迹”直接替代 global search，也不要让 RRT* 用物理上不可执行的直线 steering 假装自己在做 kinodynamic planning。

## 今日结论

今天最明显的控制趋势是：**形式规格、模型结构和学习策略开始真正进入同一个闭环，而不是各自写一篇论文。** STL-MPPI 把时序逻辑转换成 MPPI 可以消费的 barrier；PAS 把非线性可行轨迹局部转换成可复用凸动作集；CARO 用经典刚体模型残差增强 RL 对真实动力学变化的感知。这三项工作的共同点都是：没有要求神经网络或采样器独自解决全部问题，而是把“哪一部分适合解析结构、哪一部分适合学习 / 采样”拆得更清楚。

VLA 侧则暴露出一个越来越无法回避的工程事实：**模型速度会改变控制问题本身。** ARLI 表明 inference latency 会改变有效环境动力学和 RL 的 Markov 结构；这意味着未来 benchmark 不能只写“模型平均 8 Hz”，而应把 observation-to-action age、异步 action overlap、preemption 和 P99 delay 全部纳入控制指标。

WorldEcho / WorldSync 同样在修正一个长期评测偏差：视觉上合理的未来并不等于动作后果正确。只要 world model 被用于 policy improvement，就应该证明 off-expert action 仍然被忠实执行。否则 policy 很可能是在优化 simulator 的“习惯动作”，而不是现实世界。

AI Coding 的两条工作则再次指向**结构化搜索与独立验证**。DeepRepoQA 用树搜索让仓库理解可以显式探索和回溯；SWE Refactor Bench 证明整仓迁移中“测试全绿”甚至可能说明 Agent 根本没做要求的迁移。生产 Agent 必须把 evidence、migration audit、behaviour validation 和 independent adversarial test 分成不同责任层。

## 最值得深入研究或尝试复现的方向

1. **CARO-lite：给现有四足控制加入 joint residual health channel。** 不先改 policy，只根据关节状态、PD torque command 和简化刚体模型运行 residual observer；记录 payload、坡道、打滑、落地冲击下 residual 的可分性。若健康度稳定，再将其作为 RL / MPC adaptive input。

2. **给 MPPI 增加一小套 STL / CBF 任务契约。** 从 `always clearance>d`、`eventually reach goal before T` 开始，不让语言模型直接改 cost；高层只生成经过 schema 验证的 STL，再由确定性编译器进入 rollout。重点测 safety satisfaction 与 P99 planning latency 的权衡。

3. **为 VLA 建立 Latency-in-the-Loop 回归。** 人为加入 25/50/100/200/400 ms 推理延迟，同时记录 committed action、mid-inference observation 和 action age；比较同步、普通异步与 ARLI 风格状态增强，找出真实任务的“最晚有效动作时间”。

4. **Coding Agent 增加迁移完整性门禁。** 对一次真实技术栈升级建立 `旧技术必须消失` 的结构检查，行为测试只作为第二阶段，第三阶段再让独立 Agent 自动生成差分测试。只有三层都通过才允许合并。

## 参考资料

1. [Safety-aware Model Predictive Path Integral Control with Signal Temporal Logic](https://arxiv.org/abs/2608.23972) · [项目页](https://zhaoy37.github.io/safety-aware-stl-mppi/)
2. [Trusted Polytopic Action Sets for Fast Planning in Underactuated Systems](https://arxiv.org/abs/2608.24019) · [代码](https://github.com/akshay5312/paamp_underactuated)
3. [CARO: Contact-Agnostic Residual Observation for Zero-Shot Robust Quadruped Locomotion](https://arxiv.org/abs/2608.24217)
4. [Learning to Act While Waiting: RL Finetuning of Generalist Robot Policies Under Inference Latency](https://arxiv.org/abs/2608.23831) · [项目页](https://async-rl-intermediate-information.github.io/)
5. [Event-Based Motion Estimation via Oriented Distance Fields](https://arxiv.org/abs/2608.24223)
6. [Do Robotic World Models Really Follow Actions? Diagnosing and Aligning Action-Conditioned Generation for Policy Learning](https://arxiv.org/abs/2608.24885)
7. [DeepRepoQA](https://arxiv.org/abs/2608.24221) · [代码](https://github.com/peng-weihan/DeepRepoQA)
8. [SWE Refactor Bench](https://arxiv.org/abs/2608.23564) · [代码与评测](https://github.com/Einsia/SWE-Refactor-Bench)
9. [Sampling-based Algorithms for Optimal Motion Planning / RRT*](https://arxiv.org/abs/1105.1186) · [RSS 2010](https://roboticsproceedings.org/rss06/p34.html) · [OMPL RRT*](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1RRTstar.html)
10. [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/new)
