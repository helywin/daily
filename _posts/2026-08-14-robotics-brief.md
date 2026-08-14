---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-14"
date: 2026-08-14 09:00:00 +0800
description: "本期更新至8月13日最新公开批次，重点覆盖SMPC示教到稀疏RL、接触隐式轨迹优化、统一自回归VLA、单示教适配、无视频Rollout世界模型和Coding Agent工具架构。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-14

## 摘要

截至 2026-08-14 09:32（Asia/Shanghai），arXiv Robotics 与 Software Engineering 的最新公开批次均已更新到 **2026-08-13**：Robotics 当日 28 条，Software Engineering 当日 18 条。本期在早间首版基础上重新执行检索和去重，因为新批次中出现了比首版候选更近、更具工程价值的机器人控制、VLA 与 AI Coding 工作。选题前已重新读取 `robotics-brief-covered-items.md`，当前历史索引共 307 条；本次新选条目均未在索引中作为完整条目报道。（[arXiv Robotics](https://arxiv.org/list/cs.RO/recent?show=2000)，[arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent?show=2000)）

严格按 24 小时窗口看，RIFT 在 2026-08-13 02:41 UTC 发布了 v2 修订，仍位于本期检索时点之前约 23 小时；其余高价值工作主要于 8 月 11–12 日提交，因此统一标记为“时间回补”，不把 8 月 13 日 arXiv 列表日期误写成论文首次发布时间。本期最终选择 8 条主动态，优先级为控制/规划、机器人策略与 AI Coding 工程架构。

今天最值得关注的控制趋势，是**传统优化器正在变成学习系统的数据发动机，而学习策略也开始反过来超越优化器教师**。`Learning Loco-Manipulation From SMPC Demonstrations` 用 Sample-based MPC 在仿真中自动生成大规模高质量示范，解决 RL 最昂贵的探索问题，再用纯 sparse task reward 做 offline-to-online RL；最终策略不仅跨 Spot+机械臂和 G1 人形实现 sim-to-real，还能在真实任务目标上超过原始 optimal-control teacher。ContactIPM 则从另一端强化传统优化器本身：针对 contact-implicit trajectory optimization 的 complementarity degeneracy，使用结构化 primal-dual interior-point + Riccati recursion，在多项接触 benchmark 上相对 CRISP 获得 2.17–8.87 倍速度提升。

机器人基础模型侧出现三条很鲜明的路线。G0.5 不再用“VLM + 单独 flow-matching action expert”，而是让同一个 autoregressive decoder 交错生成 reasoning token 与 action token，并通过跨本体 action tokenizer 把不同机器人的动作映射到共享词表；StellaVLA 不要求为了新场景重新微调，而是把单条人类/机器人/XR 轨迹离线转换成结构化任务计划、子目标和 3D 运动描述，在测试时作为 in-context demonstration；RIFT 则证明世界模型真正需要保留的可能不是逐帧未来视频，而是供动作头读取的 future K/V representation——用 anticipation tokens 一次构造未来 cache 后，LIBERO 保持 98.8% 成功率，同时将 action-chunk latency 降低 68.2–89.1%。

少数据适配方面，MiDAS 进一步把“一个演示 + 几小时自主在线交互”做成可验证路线：先用单/few demonstration 对预训练 VLA 做行为克隆锚定，再让 residual policy 通过 value-based online RL 自主提高成功率。更偏 Agent 系统的一条路线 SHAPER 则完全冻结模型权重，只通过目标环境 rollout 进化 reusable skills 与 context-code harness，说明机器人 Agent 的能力边界和 Coding Agent 一样，越来越取决于模型外部的技能、上下文和执行脚手架。

AI Coding 侧，今天最有工程价值的是《The Devil Is in the Interface》。作者在 3 类 actor、6 种工具架构、11,700 条 repository-level issue-fixing trajectory 上做受控实验：底层能力几乎不变，仅改变工具如何组织和暴露，重复尝试的一致性就可提高 4.7 倍；Python CodeAct 风格接口能以相近任务表现减少 41.6% 步数和 56.3% token。这与最近几期关于 skill、harness、独立验证和 chaos testing 的结果高度一致：Coding Agent 的产品性能已经不能简单归因于底模大小。

## 1. SMPC 示教 + 稀疏 Offline-to-Online RL：让优化器负责探索，RL 负责把真实任务目标做到更好

**时间回补：论文 v1 提交于 2026-08-12 13:48:56 UTC，并进入 8 月 13 日 Robotics 最新批次。此前未进入去重索引。**

《Learning Loco-Manipulation From SMPC Demonstrations With Sparse Offline-to-Online RL》针对移动操作 RL 一个非常实际的瓶颈：任务越复杂，dense reward shaping 越慢，而且奖励一旦写得不好，策略会把工程师设计的代理指标优化得很好，却未必真正完成任务。作者没有直接让 RL 在仿真里盲目探索，而是先用 Sample-based Model Predictive Control（SMPC）作为自动化 expert，在仿真中快速调参并生成大规模离线轨迹，再让 off-policy RL 使用**纯稀疏任务奖励**学习。（[论文](https://arxiv.org/abs/2608.12063)）

### 为什么重要

优化控制和 RL 往往被讨论成替代关系：要么用 MPC，要么用 learning policy。这项工作的价值是把它们放到更合理的流水线里。SMPC 擅长在已知仿真动力学中生成“至少能做成”的行为，因此非常适合解决 early exploration；RL 则擅长从大量数据中压缩策略、吸收模型误差，并直接围绕最终 sparse objective 优化。

更值得注意的是，论文摘要明确报告最终 learned policy 能够**超过原始 optimal-control teacher**。这说明示范学习不一定意味着策略永远受限于专家上界：教师只负责把状态分布带到正确区域，在线/离线 RL 仍可以针对真实任务目标继续改进。

### 算法模块

- 在高保真仿真中建立 loco-manipulation 任务与机器人模型；
- 使用 Sample-based MPC 作为自动 expert，快速生成大量成功轨迹；
- 将 SMPC 轨迹写入 offline replay buffer，解决稀疏奖励下的探索冷启动；
- off-policy RL 只使用 sparse task reward，不依赖人为密集 shaping；
- 高层学习策略输出任务相关的移动/操作动作；
- 低层 dynamic stability controller 负责保持本体稳定与执行可行性；
- offline policy 继续通过 online interaction 改进，减少 expert bias；
- 同一思路跨 morphology 迁移到 arm-equipped Spot 和 Unitree G1。

### 动力学与传感器假设

该框架仍依赖质量足够高的仿真模型，否则 SMPC 产生的数据会把错误动力学结构写入初始策略。不过与纯 imitation learning 不同，后续 RL 可以在真实任务奖励下继续修正，因此对模型偏差的容忍度更高。

论文摘要没有把具体视觉/力觉栈作为核心贡献，因此不能把它理解为完整 VLA 感知系统；其重点是**控制学习与数据生成机制**。真正接到巡检操作机器人时，感知、SLAM、碰撞地图和技能状态机仍需要独立解决。

### 实时性、鲁棒性与可复现性

SMPC 的主要计算成本发生在数据生成阶段，部署阶段使用的是学到的 policy + 低层稳定控制器，因此不需要把高成本采样 MPC 保留在每个真实控制周期。论文已经给出不同 morphology 的 sim-to-real 验证，这是相较“只在 Isaac Gym 跑 reward 曲线”的工作更值得关注的地方。

当前 arXiv 页面没有稳定公开代码仓库，因此复现难点主要是 SMPC expert 的任务建模、数据规模、off-policy RL 配方以及 Spot/G1 的低层接口。

### 风险

SMPC 数据如果只覆盖少数成功模式，RL 仍可能学到狭窄行为；online fine-tuning 也会重新引入真实硬件探索风险。产品化时应限制在线残差幅度、使用碰撞/力矩/速度硬约束，并明确哪些 task reward 可以在真实机器人上安全自动计算。

### 适合谁关注

适合四足+机械臂、轮式移动操作、人形 loco-manipulation、offline-to-online RL，以及已经有成熟 MPC/轨迹优化器但觉得“手工写新任务太慢”的团队。

### 工程落地启发

非常适合从现有传统控制栈渐进升级：先把当前 MPC/规划器跑出来的成功任务轨迹自动沉淀成数据集，再让小型 residual/action policy 学“如何在同一任务上更快、更稳、更少保守”。这样传统算法不是被废弃，而是成为机器人数据飞轮的第一代教师。

## 2. ContactIPM：把 Contact-Implicit Trajectory Optimization 从通用 MPCC 难题拉回可利用最优控制结构的求解器

**时间回补：论文 v1 提交于 2026-08-12 07:11:58 UTC，并进入 8 月 13 日 Robotics 最新批次。此前未报道。**

Contact-implicit trajectory optimization 的吸引力是无需提前指定“第几步哪只脚/哪一面物体接触”，优化器自己寻找接触时机和接触力；代价是会形成 Mathematical Program with Complementarity Constraints（MPCC），而 complementarity 在接触切换处具有严重退化，普通 SQP / primal-dual solver 往往收敛困难。ContactIPM 的目标就是同时保留 contact-specific robustness 和 optimal-control stagewise structure。（[论文](https://arxiv.org/abs/2608.11731)）

### 为什么重要

对于腿式机器人、推箱、双臂接触、whole-body manipulation，手工指定 contact schedule 会迅速成为 combinatorial burden。Contact-implicit optimization 能自动发现接触序列，但如果一个问题需要几秒甚至几十秒、且对 initialization 极端敏感，就很难进入 MPC 或大规模数据生成。

ContactIPM 最值得关注的是它没有只换一个 penalty，而是从线性代数结构上降低每次 Newton solve 的代价，并且把“是否真的满足物理 complementarity”放到终止条件里，避免优化器仅仅在 relaxed problem 上看起来收敛。

### 算法模块

- 自动识别 complementary inequality pairs；
- 使用 barrier-coupled elastic interior relaxation 处理 MPCC 退化；
- stagewise 消去 slack 和 dual variables；
- 将 reduced Newton system 重新暴露为最优控制的时序结构；
- 使用 Riccati recursion 求解 reduced system；
- 固定 multi-phase MPCC recovery schedule 提供 4 次 continuation/restart 机会；
- 最终 termination 由未松弛的 physical complementarity residual 把关；
- 对不同接触任务使用统一 post-solve acceptance criteria 与基线比较。

### 实时性与结果

在 4 个固定 CRISP benchmark 上，ContactIPM 在每个案例 20 次 paired timing 中比 CRISP 快 **2.17–8.87 倍**，并在 Push Box 与 Push-T robustness suite 上具有更高成功率。与 IMPACT 相比，它在 Push T 上约快 2.96 倍、Cart Transport 约快 4.91 倍，但在 Push Box 上反而慢 4.46 倍。这个结果很有价值，因为它没有把“新求解器”包装成所有任务都更快，而是暴露了结构依赖。（[论文](https://arxiv.org/abs/2608.11731)）

### 动力学假设

ContactIPM 的上限仍由接触模型决定。刚性接触、摩擦锥、离散时间动力学如果和真实软接触、轮胎/足底弹性、机械间隙差距太大，求解器再精确也只是更快地解错模型。

### 鲁棒性与可复现性

论文还进行了 Push Box 在模型失配、噪声、pose error 和 state reset 下的闭环测试，说明作者并未只停留在离线 open-loop trajectory。当前没有稳定公开代码入口，可复现性暂评中等。

### 风险

Interior-point + continuation 仍可能在非常复杂的接触拓扑或糟糕 warm start 下失败；Riccati structure 也要求问题保持适合时序分解的形式。工程上不能因为 solver 变快就取消 fallback contact schedule 或 safety monitor。

### 适合谁关注

适合人形/四足全身控制、contact-implicit MPC、推拉操作、移动操作，以及希望用 trajectory optimizer 自动产生 RL demonstration 的团队。

### 工程落地启发

这项工作与上一条非常适合组合：ContactIPM/SMPC 一类优化器可以做“困难技能数据生成器”，策略网络做高频执行器。未来真正值得做的不是争论 MPC 和 RL 谁取代谁，而是把优化器输出、求解状态、失败原因全部结构化记录，直接进入策略训练与安全标签。

## 3. G0.5：把 reasoning 与 action 放进同一个自回归 Token Stream，而不是让 VLM 只当上下文编码器

**时间回补：论文 v1 提交于 2026-08-12 07:26:47 UTC，并进入 8 月 13 日 Robotics 最新批次。此前未进入索引。**

G0.5 针对当前 VLA 的主流架构提出了非常直接的反例：典型做法是预训练 VLM 负责视觉语言理解，再外挂一个单独训练的 flow-matching / diffusion action expert。这样 VLM 本质上只是 context encoder，真正的动作决策发生在另一套参数中。G0.5 则用**单个 autoregressive transformer decoder** 在同一目标下交错输出 reasoning token 和 action token。（[论文](https://arxiv.org/abs/2608.11739)）

### 为什么重要

这条路线如果成立，意义不只是“又一种 VLA”。它把语言模型原生的 instruction following、长上下文推理、prompt steerability 和动作生成放进同一权重空间，理论上可以减少“VLM 理解正确，但 action expert 没吃到这个语义”的接口损失。

另一方面，它也与最近几期“控制链不要生成过长自由文本”形成有意思的张力：统一自回归流可能提升 reasoning/action alignment，但自回归 action token 的延迟、错误累积和 tokenization 精度也会成为新的系统约束。

### 模型结构

- learnable cross-embodiment action tokenizer 将不同机器人动作映射到共享 vocabulary；
- 单一 transformer decoder 同时产生语言推理和动作 token；
- native CoT stream 交错表达 task decomposition、object grounding、action hints 与真实 action token；
- visual memory 通过 vision encoder 注入数秒历史，而不是只看当前帧；
- reasoning/action 共用权重与训练目标；
- prompt 可以直接改变动作粒度、任务 horizon 和 OOD 场景处理方式；
- 预训练同时使用大规模机器人轨迹与 VQA 数据。

### 结果

论文报告在 R1lite/R1pro 真实机器人微调上成功率 **76.7%**，对比 π0.5 的 53.3% 与 GR00T-N1.7 的 24.4%；BEHAVIOR Challenge 的 50 个长时域家庭移动操作任务中达到 31.4%，高于 π0.5 的 26.3% 和当年 challenge winner 的 26.1%。此外还报告 DROID post-training 后未见环境/物体 zero-shot 82.5%、LIBERO 98.9%、RoboTwin 2.0 93.3%、SimplerEnv-Bridge 87.3%。（[论文](https://arxiv.org/abs/2608.11739)）

### 实时性与工程风险

当前摘要没有给出端到端 action frequency，因此不能因为“统一 decoder”就假设它比 flow expert 更快。自回归生成天然存在 token-by-token latency；如果一段动作需要较多 token，可能反而不适合 20–50 Hz 高频控制。

更大的风险是 tokenization error：不同 embodiment 动作压缩到统一离散 vocabulary 后，精细力控、关节限位和时序平滑度如何保持，需要单独验证。长 CoT 也不能进入硬实时低层环。

### 可复现性

当前 arXiv 页面未稳定暴露代码/权重仓库，完整复现门槛较高。

### 适合谁关注

适合 VLA、跨本体动作建模、长时域移动操作，以及正在评估“统一 autoregressive policy”与“VLM + action expert”两种基础模型架构的团队。

### 工程落地启发

中小团队无需复制 foundation pretraining，可以先研究 action tokenizer：把轮式底盘、单臂、双臂、升降机构的动作映射成共享的高层 token，而低层仍由各自控制器执行。若统一 token 能表达“接近、对准、伸臂、抓取、退让”等跨本体技能，就已经能降低技能库按硬件重复开发的问题。

## 4. StellaVLA：测试时只给一条结构化示范，不重新微调模型，也能做 OOD 适配

**时间回补：论文 v1 提交于 2026-08-12 05:30:53 UTC。此前未报道。**

StellaVLA 研究一个对机器人产品非常现实的问题：同一个任务换物体、换相机视角、换桌面布局后，VLA 往往性能快速下降；传统做法是继续收数据、fine-tune。StellaVLA 选择把一条已有 raw trajectory 离线转换成**结构化 demonstration**，内容包括 task plan、sub-goal description 和 verbalized 3D motion，在测试时作为 in-context guidance 注入，而无需为新场景再次更新权重。（[论文](https://arxiv.org/abs/2608.11671)）

### 为什么重要

真正部署机器人时，“每个客户现场都重新训练”很难规模化。示范却很容易获得：工程师遥操作做一遍，或者人直接演示一遍。如果系统能把这一次演示抽象成任务结构，而不是死记像素轨迹，就更接近现场快速配置。

尤其值得注意的是 StellaVLA 允许 real-robot、human-hand 和 XR demonstration 作为上下文来源。这意味着数据采集不必全部发生在目标机器人上。

### 算法模块

- 离线读取 raw trajectory；
- 自动生成 task plan；
- 提取 sub-goal descriptions；
- 将连续 3D motion verbalize/结构化；
- 整个转换过程不需要人工逐帧标注；
- 检索与当前任务相关的一条 demonstration；
- 在训练期用 joint action-and-language objective internalize reasoning；
- 推理时只保留 action expert，不额外运行语言 reasoning branch；
- 同一 structured demo 可以跨 robot/human/XR embodiment 使用。

### 实时性与结果

论文特别强调推理阶段只使用 action expert，因此结构化 reasoning 不增加在线控制 latency。VLA-Arena 2026-08-01 leaderboard 上，StellaVLA overall score 为 **0.63**，对比 π0.5 的 0.44 和 LingBot-VLA 的 0.22；LIBERO 平均成功率 98.8%，LIBERO-Plus 85.1%。作者还提供真实机器人 OOD benchmark，验证人类、机器人和 XR demo 都可以作为结构化上下文来源。（[论文](https://arxiv.org/abs/2608.11671)）

### 风险

“单 demo”并不意味着没有检索问题：示范选错、task plan 自动抽取错、3D motion 描述丢失关键接触细节，都可能让策略得到错误 guidance。结构化语言也更适合描述阶段与几何关系，不适合代替毫秒级力觉变化。

### 可复现性

当前未见稳定公开代码入口。算法复现门槛主要集中在 structured demonstration generation 与 base VLA 训练。

### 适合谁关注

适合工业移动操作、遥操作数据复用、客户现场快速适配、VLA 以及希望利用人类/XR 演示减少真机数据成本的团队。

### 工程落地启发

即使不使用 StellaVLA，也值得把每次遥操作任务保存成**技能包**：目标语义、关键子目标、关键位姿、允许误差、失败恢复点和原始轨迹。将来更换 VLA 或底盘/机械臂后，结构化技能资产仍能复用，而不是只剩一堆难以解释的 rosbag/video。

## 5. RIFT：世界模型可以保留“未来表示”，但把逐帧视频 Rollout 从部署链里删掉

**最近 24 小时修订：论文 v1 提交于 2026-08-12 00:17:30 UTC，v2 于 2026-08-13 02:41:24 UTC 修订；本期检索时 v2 距当前约 23 小时。此前未进入索引。**

RIFT（Rollout-free Imagination via Future Tokens）针对 World Action Model 最明显的产品瓶颈：许多方法让视频生成模型迭代预测未来，再把未来帧/中间特征提供给 action policy。未来想象有用，但逐步 denoising/video rollout 太慢。作者首先做 paired intervention，问了一个非常关键的问题：动作头真正需要的是“未来视频生成过程”，还是最终形成的 future representation？（[论文](https://arxiv.org/abs/2608.11521)）

### 核心发现

在 4 种 WAM、LIBERO 40 个任务中，作者发现修改 future-cache value 会明显改变执行，说明“未来信息”确实重要；但对于 Joint 与 Cosmos-2，只要把最终 clean future 的 K/V cache 固定下来反复 replay，策略行为几乎保持不变：末端平均位移误差约 1.7–1.9 cm，成功率仍有 97.9–98.2%。

这说明 cache **消费**和 cache **生成**可以拆开：动作头需要 future K/V，但不一定需要在线逐步生成未来视频。

### 模型结构

- 保留原 WAM action branch 读取 future-cache 的接口；
- 引入 learnable anticipation tokens；
- 单次 backbone forward 直接构造完整 future K/V cache；
- 不执行 iterative video rollout；
- action branch 仍像原模型一样读取“未来表示”；
- 因此可以最大程度复用已有 WAM 结构，而不是重新训练完全不同的 reactive policy。

### 实时性与结果

RIFT 在 LIBERO 达到 **98.8%** 成功率，与 rollout-based Joint、IDM、LingBot-VA 的 98.4–98.6% 接近，但 action-chunk latency 降低 **68.2–89.1%**。RoboTwin 2.0 上 clean/randomized 分别达到 92.9% / 92.6%，是论文评测方法中的最高结果。（[论文](https://arxiv.org/abs/2608.11521)）

### 为什么重要

这比“把视频模型量化到 INT8”更根本：它质疑部署时为什么要生成用户根本不会看的未来 RGB。机器人真正需要的可能只是经过世界模型训练后形成的未来 state/cache。

### 风险与可复现性

未来 cache 仍是 learned representation，并没有物理可解释性；如果 anticipation token 在 OOD 接触或动态障碍下猜错，action policy 可能以很高置信度消费错误未来。当前没有稳定公开代码链接。

### 适合谁关注

适合 WAM/VLA、边缘部署、视频世界模型和希望降低 action latency 的团队。

### 工程落地启发

如果现有策略已经有昂贵的预测分支，可以做一次类似实验：离线缓存“完整模型算出来的最终未来 latent”，然后在闭环 replay 中固定或替换这些 latent，测 action sensitivity。若策略只依赖最终 latent，就应该优先蒸馏/预测这个 latent，而不是继续优化整个视频生成链。

## 6. MiDAS：一条示范先把 VLA 锚定到任务，再用约 6 小时在线交互把脆弱策略练稳

**时间回补：论文 v1 提交于 2026-08-11 19:15:26 UTC。此前未报道。**

《Adaptation of Generalist Robot Policies with Minimal Data》把研究问题定义得很明确：一个已经预训练好的 generalist policy，到新任务现场后只允许拿到 **1 条 demonstration**，随后主要依靠机器人自己在线交互，能不能真正学会？作者提出 MiDAS：先对单/few demonstration 做 behavior cloning，将策略锚定到任务附近，再使用 value-based online RL 优化 residual policy。（[论文](https://arxiv.org/abs/2608.11363)）

### 为什么重要

完全 zero-shot 在线 RL 很难，因为 sparse reward 下机器人很可能一次成功都碰不到；大量示范又太贵。MiDAS 选择最小人工引导：只需要让人“正确做一遍”，先把探索分布推到成功附近，然后让 residual learning 自主扩大鲁棒区域。

这特别适合工业现场的新工位、新夹具、新设备按钮等小变化：基础策略已经会移动和操作，只缺现场最后 10–20% 的适配。

### 算法模块

- 预训练 generalist VLA 作为基础策略；
- 单条或少量 demonstration 进行 behavior cloning anchor；
- 不直接大幅修改基础 policy；
- 使用 residual policy parameterization 约束在线更新；
- value-based online RL 从真实交互中改进 residual；
- sparse task success 提供主要学习信号；
- offline demo 与 online replay 共同维持任务锚定。

### 结果

LIBERO 和 RoboCasa 上，MiDAS 从 1 条示范即可恢复强任务表现并超越对比基线。真实 bimanual YAM 平台上，从单示范得到的低成功率脆弱策略出发，约 **6 小时在线交互**后能够提高鲁棒性并学出示范中没有的成功行为。作者将其描述为从单任务示范可靠适配机器人策略的首次实证之一。（[论文](https://arxiv.org/abs/2608.11363)）

### 实时性与安全边界

论文重点是学习效率，不是推理速度。真正产品化的瓶颈是 6 小时在线探索如何安全进行：机械臂碰撞、夹具卡死、掉件、人员进入工作区，都不能只靠 reward 事后惩罚。

### 风险

Residual policy 如果权限过大，在线 RL 仍可能破坏基础策略；如果 reward 可以被投机，也会学出“高分但错误”的动作。应给 residual 严格动作范围、力矩/速度上限和 rollback checkpoint，并把真实安全 constraint 独立于 reward。

### 适合谁关注

适合工业机械臂、轮式操作机器人、VLA post-training、现场快速工艺适配，以及希望降低真机 demonstration 数量的团队。

### 工程落地启发

可把客户现场调试流程重构为：`工程师示范1–5次 → 自动生成初始技能 → 夜间安全工位自主练习 → 次日验收 → 固化版本`。这比“每个客户工位都回总部重新训练大模型”更接近可规模化产品。

## 7. SHAPER：冻结基础模型，通过 Skill + Context-Code Harness 自我进化机器人 Agent

**时间回补：论文 v1 提交于 2026-08-11 18:55:58 UTC。此前未进入索引。**

SHAPER（Self-Evolving Embodied Agents via Skill-Harness Evolution）延续了最近 Coding Agent 中非常明显的趋势：系统性能不仅由模型参数决定，还由 skills、context、action interface 与 execution harness 共同决定。作者把这一观点迁移到 embodied agent，并且刻意**不做任何模型权重更新**，只通过目标环境中的 rollout 迭代外部技能和 context-code harness。（[论文](https://arxiv.org/abs/2608.11350)）

### 为什么重要

真实机器人基础模型很难频繁 fine-tune：训练资源贵、回归风险大、权重发布慢，而且有时使用的是无法修改的闭源模型。反过来，skill library、prompt/context、tool schema、恢复逻辑和动作 API 都可以快速版本化。

这意味着机器人产品的“持续学习”不一定首先发生在权重里，也可能发生在**模型外部的可审计资产**中。

### 算法模块

- foundation model 参数全程冻结；
- 同一模型既作为任务 planner，也作为外部系统 optimizer；
- 从 target-environment rollout 中观察成功/失败轨迹；
- 生成、修改 reusable skills；
- 同时优化 context-code harness；
- skill 与 harness 共同适配不同 low-level action interface；
- 无需额外 SFT/RL training run；
- 在 VLABench 和 ESI-Bench 与 pure execution、SFT 和 test-time scaling 基线对比。

### 突破性工程价值

它把“技能”从一句 prompt 升级成可演化的系统组件。对于同一模型，如果某机器人只能调用固定 `move/grasp/open` API，而另一机器人提供更细的 Cartesian/impedance primitive，适配对象可以是 harness 与 skill，不一定重新训练整套 VLA。

### 风险与安全

外部 skill/harness 本质上也是可执行供应链。系统如果允许模型自动修改 context-code，必须具备版本控制、静态权限扫描、沙箱回放、历史任务 regression 和一键 rollback。最近关于恶意 skill 和 AgentChaos 的研究已经说明，模型外系统越有权限，治理越重要。

### 可复现性

当前 arXiv 页面没有稳定公开仓库入口。方法本身对 base model、action interface 和评测环境依赖明显。

### 适合谁关注

适合机器人 Agent、技能平台、VLA orchestration、多型号机器人共享能力，以及不希望频繁重新训练基础模型的团队。

### 工程落地启发

这条路线与工业机器人“技能包”非常契合。建议把技能拆成：`precondition / perception query / action graph / safety constraints / recovery / success check / supported embodiments / version`。模型可以提出技能修改，但只有经过仿真和历史真机日志回放后才能进入生产版本。

## 8. The Devil Is in the Interface：Coding Agent 能力相同，工具接口组织方式不同，行为就能差几倍

**时间回补：论文 v1 提交于 2026-08-11 19:50:56 UTC，并进入 8 月 13 日 Software Engineering 最新批次。此前未报道。**

这项工作研究的是一个极其容易被忽略的变量：**tool architecture**。很多 Coding Agent benchmark 把性能差异归因于模型、prompt 或 planning，但如果两个 Agent 能读取相同文件、执行相同行为，只是一个给 `bash`，另一个给结构化文件 API / 搜索 API / Python CodeAct，模型会不会表现完全不同？作者在 repository-level issue fixing 中对 6 种工具架构、3 种 actor、总计 **11,700 条 trajectory**做了受控实验。（[论文](https://arxiv.org/abs/2608.11386)）

### 为什么重要

这对真实研发 Agent 比再做一个 prompt engineering 技巧更重要。工具接口决定模型每一步能看到什么、错误如何反馈、动作是否结构化、输出长度是否可控；因此同一个底模放进 Codex、Claude Code、自建 shell loop 或结构化 IDE API，行为差异可能来自 harness，而非智力差异。

### 核心结果

- 相比只提供 bash 的基础架构，结构化 low-level interface 在重复尝试中的一致性最高提升约 **4.7 倍**；
- natural-language search 扩大仓库探索范围，访问 relevant file 的比例提升超过 **11%**；
- Python CodeAct 风格接口在相近任务表现下减少 **41.6% steps**；
- 同时减少约 **56.3% token usage**；
- 让 Agent 记录中间 reasoning 的轻量文本 cognitive-scaffolding tool，对行为的影响反而有限。

### 突破性工程价值

结论非常明确：不要把“给 Agent 一个无限 bash”当成最通用、最强的设计。结构化工具不仅更安全，也可能更稳定、更省 token。相反，增加一个 `notes` / `scratchpad` 工具并不一定显著提高软件工程能力。

### 是否适合真实研发流程

非常适合。内部 Coding Agent 应该把工具层当成独立可测产品：文件读取、符号搜索、文本搜索、diff、测试、Git 操作分别定义 schema、最大输出、超时与错误类型，而不是把所有能力塞到 shell 后期待模型自己管理。

### 安全与可验证性风险

结构化 API 也会限制能力上限：接口漏掉某个关键操作时，Agent 可能完全无法完成任务。因此工具设计需要 escape hatch，但高风险通用 shell 应运行在隔离 worktree/sandbox，并对网络、secret 和宿主机路径默认拒绝。

### 可复现性

论文公开了实验规模和 6 类工具架构，但当前 arXiv 页面未显示稳定代码仓库。最值得团队自己复现的是**同底模、同任务、只换工具协议**的内部 A/B，而不是照搬其 benchmark 数字。

### 适合谁关注

适合 Codex/Claude Code/OpenHands 类内部平台、IDE Agent、MCP 工具层、vibe coding 系统，以及需要降低 Agent token 成本与重复运行方差的团队。

### 工程落地启发

建议内部 benchmark 增加第三个维度：`model × task × tool architecture`。如果同一个模型在结构化文件 API 下稳定、在 bash-only 下波动巨大，就应该优先修 harness，而不是直接升级更贵的模型。

## 经典论文回顾

### LeGO-LOAM：为什么“先识别地面、再分两阶段求 6DoF”曾经让 16 线 LiDAR 真正跑上低算力 UGV

**发表时间与历史位置：** Tixiao Shan 与 Brendan Englot 的《LeGO-LOAM: Lightweight and Ground-Optimized Lidar Odometry and Mapping on Variable Terrain》发表于 IROS 2018，页 4758–4765，DOI 为 `10.1109/IROS.2018.8594299`。它处于 LOAM 已经证明 feature-based LiDAR odometry 可行、但低线数雷达和地面车辆仍需要更低计算量方案的阶段。官方仓库明确面向 ROS-compatible UGV、水平安装 Velodyne VLP-16，并支持可选 IMU，目标是在低功耗计算平台实时输出 6DoF pose。（[论文信息](https://researchwith.stevens.edu/en/publications/lego-loam-lightweight-and-ground-optimized-lidar-odometry-and-map/)，[官方代码](https://github.com/RobustFieldAutonomyLab/LeGO-LOAM)，[DOI](https://doi.org/10.1109/IROS.2018.8594299)）

### 核心问题

原始 LOAM 对三维 edge/plane feature 做匹配，精度很好，但在 UGV 场景存在两个可利用的强先验：机器人长期贴地运动，而且地面点数量很多。如果仍把所有点一视同仁做特征和六自由度联合优化，会浪费计算；低线数 VLP-16 的垂直分辨率又限制了可提取的稳定特征数量。

LeGO-LOAM 的核心目标就是：**利用 ground structure 减少无效计算，并把 6DoF 求解拆成几何上更容易的两个阶段。**

### 算法模块与关键数学思想

- 将 LiDAR 点云投影成 range image；
- 利用相邻扫描线几何快速识别 ground points；
- 对非地面点做 segmentation，过滤小簇噪声；
- 从分割后的点云中提取 edge 与 planar features；
- 第一阶段主要利用 ground planar feature 估计与地面相关的姿态/高度分量；
- 第二阶段利用 edge feature 继续求剩余平移与 yaw 分量；
- 两阶段 Levenberg-Marquardt 避免一次性解完整大问题；
- mapping 线程将特征与局部地图继续匹配；
- 后续 SLAM 框架可使用 GTSAM / loop closure 消除长期漂移。

官方论文信息页总结其核心为 point cloud segmentation、planar/edge feature extraction 和 two-step Levenberg-Marquardt optimization，并报告相对 LOAM 在 variable-terrain UGV 数据上获得相当或更好的精度，同时降低计算量。

### 传感器假设

官方代码最典型配置是**水平安装 VLP-16**，并给出非常具体的 range-image 参数：16 beams，水平角分辨率约 0.2°、垂直约 2°，`groundScanInd=7`。这说明 LeGO-LOAM 的高效率并不是“任何点云都天然适用”，而是明显利用了扫描线结构和地面可见性。（[官方代码](https://github.com/RobustFieldAutonomyLab/LeGO-LOAM)）

换 HDL-32E 等传感器需要重新配置 scan geometry；对于 MID360 这种非重复固态扫描，直接照搬 range-image / fixed-ring ground extraction 就不是自然选择。

### 当年为什么重要

它证明了低线数 LiDAR 不一定要依赖更强 CPU 才能完成 6DoF mapping。只要把场景先验和优化结构设计好，16 线雷达也能在 UGV 上实时工作。对 2018 年的机器人硬件来说，这种“算法顺着传感器结构设计”比单纯提高算力更实际。

### 今天仍然有效的思想

1. 不要把所有点赋予相同计算预算；
2. ground / dominant plane 是地面机器人的强先验，可以直接提升姿态约束和降采样效率；
3. 如果状态变量对不同特征具有不同可观测性，可以分阶段或分块求解；
4. range image/scan structure 能把邻域搜索从 3D kNN 降成规则图上的局部操作；
5. 前端低延迟与后端全局回环应该解耦。

### 已被后续方法替代的部分

FAST-LIO2、Point-LIO、LIO-SAM 等现代 LIO 使用 IMU propagation、点级 deskew、直接 point-to-plane residual、ESKF/因子图和增量空间索引，不再要求显式 edge/plane 分类；对 Livox/MID360 这类非重复扫描，也不适合依赖固定 ring curvature pipeline。

另一方面，LeGO-LOAM 的“利用地面先验”并没有过时。现代系统仍可以把 ground normal、wheel odometry、零侧滑/非完整约束作为额外 factor 或退化时的强观测。

### 公开代码、数据与可复现性

官方 `RobustFieldAutonomyLab/LeGO-LOAM` 仓库仍公开，BSD-3-Clause，README 给出 ROS Indigo/Kinetic/Melodic、GTSAM 4.0.0-alpha2、VLP-16/HDL-32E 配置和编译步骤。依赖明显偏老，但算法结构清晰，作为 16 线 LiDAR baseline 仍然非常适合复现。（[官方代码](https://github.com/RobustFieldAutonomyLab/LeGO-LOAM)）

### 对当前工程项目的重新解读

今天重新看 LeGO-LOAM，最值得吸收的并不是把现有 LIO 换回 feature LOAM，而是**给不同 LiDAR 建立传感器特定的几何职责**。

对于“前后 MID360 + 水平 16 线雷达”一类多 LiDAR 系统，16 线雷达可以专门负责稳定地面/立面/走廊横截面约束，而不是简单和 MID360 全量拼点。系统可以为每个雷达分别计算 ground support、平面法向覆盖、退化方向和时间同步健康度，再把这些信息转成 measurement weight。这样保留 LeGO-LOAM 的结构先验，同时用现代 ESKF/因子图处理异步 IMU、多雷达和 RTK。

## 今日结论

今天最新批次最清楚的趋势是：**机器人学习开始主动吸收成熟优化与系统工程，而不是试图用一个大网络替代所有层。** SMPC 为 RL 生成成功分布，ContactIPM 把接触优化器做得更适合大规模求解；StellaVLA 把示范抽象成结构化技能上下文；MiDAS 把一条真机示范变成在线自主学习的起点。传统规划、控制和示范数据正在成为学习系统的数据与约束基础设施。

第二个趋势是，机器人基础模型正在重新思考“什么必须在线算”。G0.5 选择统一 reasoning/action token stream，追求语义与动作共享权重；RIFT 则相反，证明世界模型昂贵的逐帧 rollout 可以删掉，只保留 future cache 的作用。这两条路线并不矛盾：真正的目标都是让**在线控制路径只保留对动作有直接价值的计算**。

第三个趋势来自机器人 Agent 与 Coding Agent 的共同收敛：SHAPER 把机器人能力提升放到 skill + harness，Coding Agent 工具架构实验则证明接口组织本身可以显著改变稳定性、探索范围和 token 成本。模型外系统已经变成一等研究对象。未来机器人技能平台真正的壁垒，很可能不仅是 VLA 权重，而是技能数据结构、工具/动作接口、仿真验证、版本回滚和真实任务持续回灌。

## 最值得深入研究或尝试复现的方向

1. **用现有 MPC/规划器自动生产 RL 技能数据**

   选一个移动操作任务，例如“导航到设备前 → 机械臂对准 → 按按钮/拉把手”。先让现有规划器/MPC 在仿真中生成 1–5 万条成功与失败轨迹，RL 只用 sparse task success 学 residual。比较纯 MPC、behavior cloning、offline RL、offline-to-online RL 的成功率、动作平滑度和真机调参时间。

2. **做一次 World-Model Deployment Ablation：未来视频是否真的必须生成**

   如果当前在研究 WAM/VLA，分别测试完整 rollout、固定 final latent/cache、单步预测 future latent 三种部署方式。重点记录 action success、P95/P99 latency、显存和 OOD 动态障碍表现。若固定 latent 已能保留主要收益，就应优先蒸馏未来表示，而不是继续优化视频解码速度。

3. **把 Agent/机器人策略接口当成正式产品层做 A/B**

   对 Coding Agent 比较 bash-only、结构化 file/search/test API；对机器人 Agent 比较底层 `vx/vy/vw + joint`、技能 primitive、结构化 task API。底模保持不变，测成功率、重复运行方差、token、危险动作和恢复能力。这样可以直接知道下一轮研发应该投模型，还是投 harness。

## 参考资料

1. **Learning Loco-Manipulation From SMPC Demonstrations With Sparse Offline-to-Online RL**  
   - [论文](https://arxiv.org/abs/2608.12063)

2. **ContactIPM: A Structure-Exploiting Interior-Point Solver for Contact-Implicit Trajectory Optimization**  
   - [论文](https://arxiv.org/abs/2608.11731)

3. **G0.5: One Autoregressive Stream for Robot Reasoning and Action**  
   - [论文](https://arxiv.org/abs/2608.11739)

4. **StellaVLA: In-Context Structured Demonstration for Generalizable Vision-Language-Action Models**  
   - [论文](https://arxiv.org/abs/2608.11671)

5. **Keep the Future, Drop the Rollout: RIFT for World Action Models**  
   - [论文](https://arxiv.org/abs/2608.11521)

6. **Adaptation of Generalist Robot Policies with Minimal Data / MiDAS**  
   - [论文](https://arxiv.org/abs/2608.11363)

7. **Self-Evolving Embodied Agents via Skill-Harness Evolution / SHAPER**  
   - [论文](https://arxiv.org/abs/2608.11350)

8. **The Devil Is in the Interface: Evaluating How Tool Architecture Shapes Coding Agent Behavior**  
   - [论文](https://arxiv.org/abs/2608.11386)

9. **LeGO-LOAM: Lightweight and Ground-Optimized Lidar Odometry and Mapping on Variable Terrain**  
   - [论文信息](https://researchwith.stevens.edu/en/publications/lego-loam-lightweight-and-ground-optimized-lidar-odometry-and-map/)  
   - [官方代码](https://github.com/RobustFieldAutonomyLab/LeGO-LOAM)  
   - [DOI](https://doi.org/10.1109/IROS.2018.8594299)

10. **最新公开列表**  
    - [arXiv Robotics](https://arxiv.org/list/cs.RO/recent?show=2000)  
    - [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent?show=2000)
