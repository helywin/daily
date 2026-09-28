---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-28"
date: 2026-09-28 09:00:00 +0800
description: "本期关注 Doppler LiDAR 无运动初始化、LiDAR 语言空间定位、多机器人受力装配、身体状态驱动重规划、Residual HIL、抗深度噪声四足、VLA 三轴早退，以及 Coding Agent 自动合成广义 TAMP 程序。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-28

## 摘要

截至 2026-09-28 09:00（Asia/Shanghai），arXiv Robotics 与 Software Engineering 的 recent 页面最新常规公开批次仍为 **2026-09-25（周五）**，分别为 101 条与 52 条；本次检索时尚未出现新的周一批次。因此今天不把周末期间的旧条目包装成“9 月 28 日新论文”，而是继续从最新公开批次和最近 7 天窗口中筛选此前索引未覆盖的高价值工作，并按标题、arXiv ID、DOI、项目页和 GitHub 仓库做强制去重。

今天 SLAM / 状态估计最值得关注的是 **Free-Init**。它其实是 IEEE RA-L 2024 已发表工作，只是 2026-09-24 才补登 arXiv，因此本期明确作为“补充回顾”。它利用 FMCW Doppler LiDAR 的逐点径向速度和 IMU，绕开传统 LIO 初始化对 scan undistortion、激励运动和地图 correspondence 的依赖；内嵌 Doppler-inertial velocimeter 输出超过 10 kHz，并能覆盖静止、一般动态甚至剧烈启动。对于长期在长走廊、狭窄空间和退化几何里工作的 LIO 系统，这类“速度观测直接进入初始化”的意义比单纯提高点云匹配精度更大。

另一项与 LiDAR 直接相关的工作 **Retrieve-to-Localize** 把 LLM 的关系推理能力和 LiDAR 的精确几何绑定起来。它不是让语言模型直接“说出一个坐标”，而是先用语言条件检索位置相关 proposal，再回到局部点云细化目标坐标。这种结构很适合未来做“找到第二个柜子右侧靠墙的灭火器”之类需要多步空间关系的机器人指令：语言负责组合关系，几何负责最终 metric grounding。

规划与控制方面，本期重点看三条。**WRAP** 将多机器人装配中的支撑力、抓取和装配顺序一起考虑，通过线性规划检查哪些抓取能承受装配 wrench，再将廉价 backward heuristic 与更昂贵 forward search 结合，最后分成自由空间运动和 contact-rich assembly skills 执行。**Body-Grounded Replanning** 则把关节负载、移动受限、近期执行统计这些“机器人身体状态”提升到高层策略层：任务目标和低层 controller 不变，只在身体状态事件触发时重新选择执行策略。**Res-HIL** 更直接：冻结 imitation policy，只让人类在线纠正 residual，并把每次 intervention 同时变成 residual supervision 和前序 autonomous behavior 的 reward shaping；20 条初始示范、10 分钟在线训练即可超过更多示范训练出的 imitation policy。

四足方向，**DAWN** 针对一个非常现实的问题：深度相机在室外阳光、夜间和强 IR 干扰下的噪声分布很难手工滤波。它让 world model 编码器直接吃 noisy depth、解码器重建 clean depth，再用 contrastive loss 对齐 noisy / clean latent；部署时所有训练辅助模块移除，因此相对原有 world-model policy 没有额外 inference overhead。Unitree Go1 + RealSense D435i 真机无需手工滤波即可完成 18 cm 楼梯、70 cm gap 与 45 cm step。

VLA 侧，**Decoupled Early Exits** 把计算预算拆成三条轴：VLM backbone 深度 V、action expert 深度 A、denoising step D。通过中间 Exit Transformer 与 KV cache synthesis，action expert 可以比 backbone 走得更深；在 SmolVLA 和 π0.5 上，联合配置将 latency 降低 79.2%、FLOPs 降低 31.8%，mean success 反而提升 5.6%。这比统一“少跑几层”更适合真实机器人，因为不同任务真正吃算力的部分并不一样。

AI Coding 与机器人交叉方向，**Coding Agents for Generalized Task and Motion Planning Problems** 很值得认真看。Claude Code 与 Codex 并不是在线一步一步当 planner，而是在给定 simulator 和固定 synthesis budget 的情况下，先像软件工程师一样反复探测环境、写程序、测 edge case、修程序；程序随后被冻结，再在 unseen instances 上评估。28 个 KinDER / PDDLStream 环境、980 个生成程序、98,000 次评估中，三种 agent 配置平均成功率 56%–95%，在有手工 planner 的 16 个环境里高于 planner 的 47%，并在物体数增长时保持更好的扩展性。

近期通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic、Google DeepMind 与 xAI 的官方公开入口，没有发现 9 月 27–28 日需要新增报道的通用旗舰正式发布；近期已经覆盖的 GPT-6、Claude Opus 5.5 / Fable 5.1、Grok 4.7 本期不重复填充。

最新公开列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

## 1. Free-Init：Doppler LiDAR 初始化可以不等“运动激励”和地图对应

**补充回顾：IEEE RA-L 2024 已发表；2026-09-24 补登 arXiv，v2 于 2026-09-25 更新。**

### 为什么重要

传统 LiDAR-inertial 初始化通常需要先处理 scan motion distortion，再通过足够的平移 / 旋转激励和点云对应关系恢复速度、重力与 IMU 状态。问题是机器人真正启动时并不会总配合算法：它可能静止很久，也可能上电后立刻快速移动，甚至在传感器刚稳定时已经发生剧烈运动。

FMCW LiDAR 多出的逐点 Doppler velocity，等于给初始化阶段加入了一类几乎瞬时的运动观测。Free-Init 将 point-wise Doppler 与 IMU 在 non-inertial kinematics 下联合起来，不依赖 scan matching 就能得到高频 Doppler-inertial velocity。

### 算法模块

~~~text
FMCW LiDAR
  ├─ range / direction
  └─ point-wise Doppler velocity
            +
           IMU
            ↓
Doppler-Inertial Velocimeter
            ↓
gravity / velocity / inertial-state initialization
            ↓
plug into conventional LIO
~~~

论文强调三项 free：scan-free 不依赖完整 scan undistortion；motion-free 不要求人为做特定 excitation motion；correspondence-free 不需要先建立 map / scan correspondence。

### 传感器与动力学假设

它依赖真正能够输出 Doppler radial velocity 的 FMCW LiDAR，普通 ToF LiDAR 无法软件模拟得到这一观测。状态模型仍然依赖准确的 IMU 时间同步和外参。Doppler 也会受到动态物体、自身旋转、回波质量的影响，因此需要合理的 measurement noise 与 outlier treatment。

### 实时性与鲁棒性

论文报告内嵌 Doppler-inertial velocimeter 输出频率 **超过 10 kHz**，并验证 stationary、dynamic 与 violent initialization。它最重要的系统价值不是最终 ATE 多一点少一点，而是把“初始化必须等待合适运动”这个脆弱前提去掉。

### 可复现性

官方代码仓库已经公开，仓库名为 IMRL/Free-Init，对应 RA-L 2024 工作。对于计划评估 FMCW / 4D LiDAR 的团队，它是比完整 FMCW-LIO 更适合先读的入口，因为初始化模块边界更清楚。

### 工程风险

Doppler channel 进入 estimator 后，必须把它当正式传感器健康量，而不是附加字段。建议至少记录 doppler_inlier_ratio、doppler_velocity_variance、imu_consistency、initialization_condition 与 time_to_valid_state。

### 适合谁关注

FMCW / 4D LiDAR、FAST-LIO / LIO-SAM 扩展、矿井/走廊退化环境、高动态平台、希望缩短上电定位等待时间的机器人。

### 工程落地启发

即使当前仍用 MID360 / 16 线 ToF LiDAR，也可以先把 driver 与 estimator measurement interface 预留 radial_velocity 与 radial_velocity_variance 字段。以后换 Doppler LiDAR 时，不必重写整条感知数据链。

[论文](https://arxiv.org/abs/2609.29375) · [DOI](https://doi.org/10.1109/LRA.2024.3490395) · [代码](https://github.com/IMRL/Free-Init)

## 2. Retrieve-to-Localize：让 LLM 负责关系推理，让 LiDAR 负责最后一米的坐标

**时间回补：v1 提交于 2026-09-24。**

### 为什么重要

传统 3D detection 能回答“这里有一辆车”，但复杂机器人指令经常包含多步空间关系，例如“找到左边第二辆车后面、离护栏最近的那个目标”。纯 LLM 很擅长语言组合，却不擅长精确 metric coordinate；纯 LiDAR 网络几何很准，却很难理解长关系链。

### 算法模块

~~~text
natural-language spatial query
          ↓
LLM-aligned LiDAR representation
          ↓
language-conditioned position-aware proposal retrieval
          ↓
local point refinement
          ↓
metric target coordinate
~~~

关键点是最终坐标直接来自 local LiDAR geometry，不经自然语言 token 解码。作者同时构建 SpatialLiDAR-QA，包含单步 / 多步 relational grounding 以及辅助 spatial understanding task。

### 传感器假设

核心输入是 LiDAR point feature + language query。它更像 semantic spatial grounding module，不是 SLAM / odometry 本身；机器人仍需要可靠的局部坐标系和 map / point cloud。

### 鲁棒性与结果

论文报告在精确 coordinate prediction 上明显优于代表性 LiDAR-language model 与 multi-camera VLM。当前摘要未给出部署控制频率，因此不应直接假设它可以进入几十 Hz 的安全环。

### 可复现性

论文写明 dataset 与 training code **will be publicly released**，当前不能按“已经一键复现”评价。

### 工程风险

语言关系若涉及地图中不存在或感知漏检对象，系统仍可能强制返回一个坐标。产品接口应该允许 grounded / ambiguous / not_found，而不是永远输出 xyz。

### 适合谁关注

语义导航、LiDAR + LLM、户外巡检、机器人自然语言空间查询、希望避免 VLM 直接输出 metric action 的团队。

### 工程落地启发

把 LLM 限制在“关系解析 + 候选选择”，最终空间坐标交给 geometric module，是一个很值得复用的边界：language 负责 semantic relation，geometry 负责 metric truth。

[论文](https://arxiv.org/abs/2609.29835)

## 3. WRAP：多机器人装配不能只排顺序，还要问“谁来承受这个力”

**时间回补：v1 提交于 2026-09-24。**

### 为什么重要

fixtureless assembly 的难点不只是哪个零件先装、哪个机器人抓哪个零件。真正装配时会出现 wrench：插入、压紧、支撑、托住都会对零件产生力矩。如果规划器只看几何可达性，可能给出“路径上可行、受力时却根本托不住”的计划。

### 算法模块

~~~text
part meshes + initial poses + ordering dependencies
        ↓
candidate grasp / support configuration
        ↓
linear program: wrench feasibility
        ↓
cheap backward search heuristic
        ↓
expensive forward search
        ↓
multi-robot multi-goal motion planning
        ↓
free-space motions + contact-rich assembly skills
~~~

### 动力学 / 接触假设

它需要已知零件几何、装配依赖以及用于受力判定的接触 / 抓取模型。LP 可以高效检查 static wrench feasibility，但真实摩擦、柔顺和装配公差仍然可能与模型不同。

### 实时性与结果

论文在多种 multi-part assembly 和不同尺寸 / kinematics 的机器人组合上 benchmark，并在 physics simulation 与真实机器人中验证。核心收益是减少对专用 fixture 和固定 top-down strategy 的依赖。

### 可复现性

作者项目页提供视频和代码入口，属于本期工程可复现性较好的工作之一。

### 工程风险

能承受静态 wrench 并不代表动态插入过程一定稳定。真实系统仍应记录 support_force_margin、estimated_friction_margin、contact_loss 与 assembly_force_residual，并允许 contact-rich skill 在执行中触发重新规划。

### 适合谁关注

多机械臂、工业装配、fixtureless assembly、TAMP、多接触规划。

### 工程落地启发

现有装配 planner 可以先不改搜索结构，只给每个 candidate grasp 增加一个 wrench_feasible gate。单独这一层就能淘汰很多“几何看着能做、受力做不了”的方案。

[论文](https://arxiv.org/abs/2609.29407) · [项目页](https://www.vhartmann.com/wrap)

## 4. Body-Grounded Replanning：高层 Planner 也应该知道“机器人身体已经很吃力了”

**时间回补：v1 提交于 2026-09-24。**

### 为什么重要

机器人任务规划通常只看外部世界：目标在哪里、障碍在哪里、物体有没有抓住。但同一个几何可行方案，在机器人自身状态变化后可能已经非常不合适，例如某个关节负载持续升高、一侧运动受限，或者某个姿态长期逼近机械极限。传统系统往往只让低层 controller 默默承受这些问题。

### 算法模块

~~~text
joint-level physical state
+ recent execution statistics
+ execution history
        ↓
body-state event detector
        ↓
high-level replanning trigger
        ↓
LLM interprets body condition
        ↓
select alternative strategy
        ↓
task objective unchanged
low-level controller unchanged
~~~

它的关键不是让 LLM 进入高频控制，而是让身体状态成为“是否换策略”的上层信息。

### 结果

论文在受控 load 与 asymmetric mobility restriction 的 reaching task 中做 simulation + real robot 验证，并用额外 contact-rich manipulation 展示相同接口的可迁移性；结果显示在保持较高成功率的同时，physical effort 下降、策略适配更快。

### 工程风险

joint load / mobility condition 如果直接转成自然语言再让 LLM 自由解释，容易引入不稳定决策。更可靠的产品结构是 deterministic body-state classifier 输出 structured event，再让 LLM 只在允许的 strategy set 中选择。

### 可复现性

当前没有成熟代码入口，最适合先从系统接口复现：让上层 task manager 订阅 joint_load_margin / workspace_margin / mobility_state，不改低层控制器，只在 margin 低时切换预定义策略。

### 适合谁关注

人形 / 机器狗操作、机械臂长期任务、第三方底层 controller、机器人 Agent 编排。

### 工程落地启发

可以把 skill contract 从 precondition / effect 升级为 precondition / effect / body_cost / body_margin_required / fallback_strategy，让 planner 明确知道某个 skill 在当前身体状态下是否仍值得执行。

[论文](https://arxiv.org/abs/2609.30024)

## 5. Res-HIL：冻结已有模仿策略，人类只教“怎么纠正”

**时间回补：v1 提交于 2026-09-24。**

### 为什么重要

已有 imitation policy 往往已经能完成大部分任务，真正难的是最后那一批接触、精确对齐和 OOD 情况。为了修这些边角，再收五倍 demonstrations 或重新训练 full policy，成本很高。

Res-HIL 的思路是：base policy 保持冻结，人类只在错误即将发生时提供 correction，学习一个 residual policy。

### 算法模块

~~~text
frozen imitation policy
        ↓
nominal action
        +
human intervention
        ↓
residual target
        ↓
residual policy

human intervention
→ reward shaping
→ 修正 intervention 发生前的自主行为
~~~

residual policy 使用 zero initialization，避免训练一开始就破坏原有策略。

### 结果

五项 contact-rich manipulation task 中，只用 **20 条初始 demonstration**，经过 **10 分钟 online training**，Res-HIL 在每项任务上都超过 full-policy HIL RL 和没有 human guidance 的 residual fine-tuning；还优于使用五倍 demonstrations 训练的 imitation policy。

消融显示 direct residual supervision 是主要性能来源，intervention-aware reward shaping 则明显提高样本效率。

### 风险

人类 intervention 的延迟与质量会直接进入学习。如果 operator 晚半拍，residual 可能学到“如何从更差状态救回来”，而不是“如何提前避免”。建议记录 intervention_timestamp、reaction_delay、residual_magnitude、state_at_intervention 与 recovery_success。

### 可复现性

论文没有给出明显成熟代码入口，但算法结构非常适合从现有 BC / VLA policy 上做小规模 sidecar 试验。

### 适合谁关注

灵巧手、接触丰富操作、已有 imitation policy 的产品团队、人类在线校正、少样本强化学习。

### 工程落地启发

如果已有稳定基础策略，优先训练 residual，不要轻易把整个 policy 打开继续 RL。训练失败时 residual = 0 就能回退原策略，比 full-policy online fine-tuning 更容易做安全回滚。

[论文](https://arxiv.org/abs/2609.30023)

## 6. DAWN：深度噪声不要靠部署现场“手调滤波器”

**时间回补：v1 提交于 2026-09-24；IROS 2026 Best Paper Award Finalist。**

### 为什么重要

RealSense / structured-light depth 在室外阳光、强 IR、暗光环境下的噪声分布差异非常大。很多四足视觉 locomotion 论文训练时吃 clean depth，部署时再依赖一组没有公开或难迁移的 post-processing filter。这使得同一个 policy 从室内移到室外时，真正需要重新调的往往不是 locomotion，而是 perception preprocessing。

### 算法模块

DAWN 不改变 world-model architecture，只改训练信号：noisy depth 进入 encoder，clean depth 作为 reconstruction target，同时用 contrastive loss 对齐 noisy / clean latent。部署时 clean depth、decoder 辅助和 contrastive branch 都不需要，因此没有额外 inference overhead。

### 真机结果

Unitree Go1 + Intel RealSense D435i 直接读取 raw depth：

- 最高 18 cm 楼梯；
- 最高 70 cm gap；
- 最高 45 cm step；
- 室内、阴影、直射阳光、夜间均无需环境特定重新标定。

### 可复现性

官方代码已经公开，基于 Isaac Lab / Isaac Sim。README 给出完整安装、训练和 checkpoint replay；默认训练 4,096 environments，作者使用 RTX 5090。

### 工程风险

DAWN 是 learned robustness，不是 sensor health guarantee。强反射、全黑 / invalid depth、大面积透明材质仍可能产生模型训练时没见过的失效。运行时最好仍保留 valid_depth_ratio、depth_dropout_pattern、latent_ood_score 与 fallback_speed_limit。

### 适合谁关注

四足楼梯 / 越障、RealSense 深度、Isaac Lab、Sim2Real、户外视觉 locomotion。

### 工程落地启发

如果已有 stair mode / locomotion policy，先不要改 controller。用真实传感器采集不同光照下 raw depth noise，训练一个 noise-robust latent，再让原 policy 读取这个 latent。感知鲁棒和控制鲁棒可以分开迭代。

[论文](https://arxiv.org/abs/2609.29092) · [项目页](https://dawn-parkour.github.io/) · [代码](https://github.com/DocyNoah/dawn-parkour)

## 7. Decoupled Early Exits：VLA 的 Backbone、Action Expert、Denoising 不该统一砍深度

**时间回补：v1 提交于 2026-09-24。**

### 为什么重要

Flow-matching VLA 通常有两大模型部分：VLM backbone 看懂视觉 / 指令，action expert 产生连续动作，然后还有多步 denoising。常见加速方式只做 backbone early exit 或减少 denoising steps，但不同任务真正需要的计算并不一样。

### 三轴计算预算

论文定义 V = backbone depth、A = action-expert depth、D = denoising steps。在 backbone 与 action expert 中间都加 lightweight Exit Transformer，蒸馏最终 policy layer；另外使用 **KV Cache synthesis** 补齐被跳过 backbone layer 的 key/value，使 action expert 可以继续走得比 backbone 更深，而不被二者强制绑定。

### 结果

在 SmolVLA、π0.5 × LIBERO、Meta-World 上，joint (V,A,D) configuration latency 下降 **79.2%**，FLOPs 下降 **31.8%**，mean success rate **提高 5.6%**；每个 exit 只增加约 2.1%（SmolVLA）/ 4.1%（π0.5）参数。

论文观察到 backbone depth 更直接影响 FLOPs，action-expert depth 更直接影响 latency，而 denoising step 同时影响两者。

### 实时性与工程风险

最大的价值是把 compute budget 做成 task-dependent runtime policy。但 early exit 的置信度并不天然等于任务风险。高速 free-space motion 可以少算，精细插入 / 接触阶段则应该主动增加计算。建议至少同时考虑 task_phase、contact_proximity、policy_uncertainty 与 latency_budget。

### 可复现性

方法不需要从头训练 base VLA，只训练附加 exit module，因此比蒸馏一个全新小 VLA 更容易在现有模型上试。

### 适合谁关注

π0.5、SmolVLA、flow-matching policy、Jetson / 边缘机器人、希望降低控制延迟的 VLA 团队。

### 工程落地启发

把模型推理接口改成可接受 backbone_depth、action_depth、denoise_steps 的 compute_budget，然后让任务状态机控制预算，而不是所有任务永久固定同一推理深度。

[论文](https://arxiv.org/abs/2609.29382)

## 8. Coding Agent 合成 TAMP 程序：Agent 先“开发 Planner”，部署时再跑冻结程序

**时间回补：v1 提交于 2026-09-24。**

### 突破性工程价值

这篇工作没有让大模型在线充当每一步 planner，而是把 Coding Agent 当成规划算法开发者：

~~~text
task description
+ simulator access
        ↓
coding agent
  ├─ probe environment
  ├─ calibrate physics
  ├─ test edge cases
  ├─ write planning program
  └─ debug / refine
        ↓
freeze program
        ↓
evaluate unseen instances
~~~

也就是说，昂贵 LLM 只发生在 synthesis 阶段；正式任务执行时跑的是生成出来的程序。

### 实验规模

作者测试 Claude Code（Opus 5）、Codex（GPT-5.6 Sol）、Codex（GPT-6 Astra），覆盖 28 个 KinDER / PDDLStream simulated environment、980 个 generated program；每个程序在 100 个 held-out instance 上评估，总计 **98,000 evaluation episodes**。

在有传统 planner 可用的 16 个环境上，hand-engineered planner mean success 为 47%，三种 Coding Agent 配置为 **56%–95%**。随着 object count 增加，Agent 生成的程序仍保持更高 success，同时平均每个 instance 计算量低约一个数量级。

### 为什么这个范式值得关注

它把机器人 agent 从 “LLM → 每一步动作” 改成 “LLM → 生成可执行策略程序；程序 → 高频执行”。这样程序本身可以 review、version control、unit test、fuzz、benchmark，并固定后在真实机器人上审计。

### 权限 / 安全 / 可验证性

风险也非常像 Coding Agent：simulator 中学出的启发式可能利用 benchmark bug、遗漏真实物理 constraint，或者对 unseen real hardware 失效。因此 deployment 前应该经过 program freeze、hidden simulation regression、constraint checker、hardware shadow run 与 limited rollout，而不是 simulator success 高就直接上真机。

### 可复现性

作者公开全部代码和完整 Agent prompts，可直接重放 synthesis / evaluation 流程。

### 适合谁关注

机器人 Agent、TAMP、自研 skill library、希望让 Codex / Claude 自动产出规划程序而不是在线直接控机器人的团队。

### 工程落地启发

已有机器人 API 如果只有 vx/vy/vw 或若干 skill，完全可以把 Coding Agent 的输出限定成一个小 DSL / Python policy，并规定 allowed APIs、state inputs、resource limits、tests 与 safety checker，然后“生成一次、验证很多次、部署冻结版本”。

[论文](https://arxiv.org/abs/2609.30233) · [代码](https://github.com/tomsilver/robocode) · [项目页](https://agenticgentamp.github.io/)

## AI Coding 实战技巧精选

### 技巧 1｜Agent 改 C/C++ 后，让 CodeQL 2.27.1 专门再扫一次比较结果赋值与新数据流模型

- **来源**：[GitHub 官方 Changelog，2026-09-25](https://github.blog/changelog/2026-09-25-codeql-2-27-1-adds-c-and-c-query-and-kotlin-2-4-20-support/)。
- **一句话结论**：Coding Agent 做大规模 C/C++ 重构后，不要只跑编译和单测。CodeQL 2.27.1 新增 cpp/ambiguous-assignment-of-comparison，并补强 Boost.Asio、Protobuf 等数据流模型，适合做 Agent patch 的第二层机器验收。
- **具体怎么做**：
  1. 确认 GitHub code scanning 使用 CodeQL 2.27.1 或更新版本。
  2. Agent 改动网络 / Protobuf 代码时，把 CodeQL 扫描作为 PR 必跑项。
  3. 对 C/C++ 特别关注 cpp/ambiguous-assignment-of-comparison，它会找出把比较结果赋值后又作为 truth value 使用的易错表达式。
  4. 将 CodeQL finding 和编译 / unit test 一起写进 Agent completion receipt，不能因为 tests 通过就忽略静态数据流告警。
- **适合什么场景**：ROS2、SLAM、CMake/C++ 服务、Boost.Asio 网络代码、Protobuf RPC、Agent 大规模 API 重构。
- **注意**：静态分析不是最终真值；新模型可能增加 finding，也可能改变 false-positive 分布。先在已有仓库做一次 baseline，再把新增告警作为 gate。

### 技巧 2｜高影响 GitHub 操作要求“人在场”，不要让长期 Token 直接等于最终授权

- **来源**：[GitHub 官方 Changelog，2026-09-24](https://github.blog/changelog/2026-09-24-require-proof-of-presence-for-high-impact-actions/)。
- **一句话结论**：Agent 即使拿到了合法 session / token，也不应该天然拥有高影响操作的最终权限。GitHub Enterprise Cloud 现在可以对高影响动作要求交互式重新认证 / MFA，思路非常适合 Agent 发布、合并和权限变更。
- **具体怎么做**：
  1. 对生产发布、敏感权限变更、关键仓库管理动作定义 high-impact 集合。
  2. 普通 Agent credential 允许准备 change，但最终动作要求 proof-of-presence。
  3. 在身份提供商侧配置重新认证 / MFA policy，而不是让 Agent 自己弹一句“请确认”后继续。
  4. 日志中同时记录 agent_request_id 与 human_presence_event，形成可审计链。
- **适合什么场景**：自动 merge / release、Copilot / Codex 企业部署、供应链敏感仓库、具有管理员能力的 Agent。
- **注意**：GitHub 当前该预览功能有企业身份环境限制；即使不用 GitHub，也可以复制原则：**token 证明身份，presence 证明此刻有真人授权**。

### 技巧 3｜把 Copilot Managed Settings 当代码：提交后看 JSON Path Validator，不要假设配置已生效

- **来源**：[GitHub 官方 Changelog，2026-09-25](https://github.blog/changelog/2026-09-25-enterprise-managed-settings-in-product-validator/)。
- **一句话结论**：AI Agent 的企业安全策略如果 JSON 写错、team mapping 不存在，最危险的不是报错，而是你以为策略已生效。GitHub 现在会直接指出文件与 JSON Path。
- **具体怎么做**：
  1. 将 copilot/managed-settings.json、copilot/team-mappings.json 放在 .github-private 中版本管理。
  2. 每次修改后 commit 到 default branch。
  3. 打开 Enterprise AI Controls 的 **Copilot settings validation**，逐项修复 malformed JSON、unsupported config、invalid team mapping。
  4. reload Agents 页面，确认 validator 清零后再把策略变更视为完成。
- **适合什么场景**：Copilot Business / Enterprise、多个团队使用不同 sandbox / MCP / agent policy 的组织。
- **注意**：validator 只能证明配置结构与引用有效，不能证明策略设计本身安全。仍要有 policy regression 和最小权限 review。

## 经典论文回顾

### Velocity Obstacles：把“会不会撞”从位置空间改写成速度空间

Paolo Fiorini 与 Zvi Shiller 的 **Motion Planning in Dynamic Environments Using Velocity Obstacles** 发表于 **The International Journal of Robotics Research，1998 年 7 月**。它是动态障碍规划里最经典的思想之一，也是后来 Reciprocal Velocity Obstacles、ORCA 以及大量局部避障方法的重要基础。

### 核心问题

静态路径规划只需要避开固定 obstacle；动态环境还必须考虑障碍现在在哪里、障碍以什么速度移动、机器人接下来选择什么速度。如果直接在 position × time 空间搜索，问题会快速膨胀。

Velocity Obstacle（VO）的关键转换是：哪些机器人速度一旦选择，在未来某个时间必然会与给定移动障碍发生碰撞？

### 关键几何思想

对一个以已知速度运动的障碍，构造速度空间中的 collision cone。机器人 candidate velocity 转成 relative velocity 后，只需要判断未来轨迹是否进入 Minkowski-expanded obstacle；进入 VO 表示存在未来碰撞，VO 外则在当前一阶预测模型下安全。最终从 VO 外与机器人动力学允许速度集合的交集中选择动作。

### 动力学假设

经典 VO 是一阶模型，主要使用位置与速度，不显式积分完整高阶动力学。障碍未来运动通常按当前速度预测，因此它特别适合作为 fast local collision primitive，而不是完整长期行为预测器。

### 当年为什么重要

它把动态避障从昂贵的 state-time trajectory search 转成一个非常直观的 velocity-space exclusion problem，使实时局部规划器能在每个控制周期快速判断“这个速度未来会不会撞”。

### 今天仍在使用的思想

现代系统虽然会加入概率轨迹、学习预测、MPC、social navigation，但基本结构仍经常是 predict other agent motion → transform into forbidden control / velocity set → choose safe control。UCON 这类 covariance-aware planner 可以理解为同一思想的概率升级：不再只有一条确定速度，而是把状态 covariance 转成更大的时空风险区域。

### 已被后续替代 / 扩展的部分

经典 VO 无法自然解决两个自主机器人“你躲我、我也躲你”造成的 reciprocal oscillation。RVO / ORCA 后来进一步把 avoidance responsibility 在多个 agent 之间分摊。另外，现代车辆 / UAV 的 acceleration、nonholonomic constraint、occlusion uncertainty 和 multi-modal prediction 都超出了经典一阶 VO 的原始假设。

### 公开代码 / 数据与可复现性

VO 本身非常容易复现。用二维圆盘机器人，只需输入 robot_position、robot_radius、robot_velocity、obstacle_position、obstacle_radius、obstacle_velocity 即可画出 velocity obstacle cone。

真正值得做的实验是把动态障碍的 velocity covariance 逐渐增大，观察固定 VO、inflated VO 与 MPC / probabilistic planner 的保守程度差异。

### 对当前工程项目的重新解读

对于机器人狗 / UAV，只给 vx / vy / wz 接口时，Velocity Obstacle 的思想仍然非常合适做一层极便宜的安全 pre-filter：

~~~text
planner desired velocity
        ↓
dynamic-obstacle VO check
        ↓
safe velocity candidate
        ↓
vendor controller
~~~

它不需要接管底层 gait / attitude controller，却可以在上层速度命令进入第三方 SDK 前先排除明显会撞的动作。

[论文 DOI](https://doi.org/10.1177/027836499801700706)

## 今日结论

今天最明显的主线是：**把隐藏在模型里的能力拆成可检查、可回滚、可独立升级的系统模块。**

Free-Init 不依赖几何 scan correspondence 去猜启动运动，而把 Doppler velocity 明确作为一类新测量；Retrieve-to-Localize 不让 LLM 直接生成 metric coordinate，而把关系推理和局部 LiDAR 几何拆开；WRAP 也不是只做离散任务排序，而是在每个装配步骤显式检查 wrench feasibility。

控制和学习侧也是一样。Body-Grounded Replanning 把 joint load / mobility state 提升成 planner 可以看到的结构化事件；Res-HIL 把人类纠错限制为 residual，而不是让在线 RL 把已有 base policy 全部重写；DAWN 只在训练阶段学习 depth-noise invariance，部署时不增加额外 branch；VLA early exit 则把 V、A、D 三类计算预算分别暴露出来。

Coding Agent for TAMP 更值得把这个趋势延伸到软件工程：模型不一定要永远在线。更稳的模式可能是 Agent 负责探索、写代码、测试与修复，之后 freeze artifact；Runtime 只运行经过验证的程序。

这和今天 AI Coding 三条技巧其实是一套完整治理方式：生成以后用 CodeQL 验证 patch；高影响动作要求 proof-of-presence；策略配置用 validator 确认真的生效。

如果把今天整期压缩成一句话：

> **机器人和 Coding Agent 的成熟方向，不是让一个更大的模型一直掌控更多事情，而是把感知、运动、身体状态、算力、权限和验收拆成有明确接口的可验证组件。**

## 最值得深入研究或尝试复现的方向

1. **Doppler-LIO Measurement Interface**：即使当前硬件不是 FMCW，也先让 estimator API 支持 radial velocity + variance，并把 initialization health 独立输出；未来更换 4D/FMCW LiDAR 时减少系统改造。
2. **LiDAR Semantic Grounding Sidecar**：LLM 只解析左/右/最近/第二个等关系，候选目标和 xyz 必须由 point-cloud module 决定。先做离线 spatial query benchmark，再接导航。
3. **Body-State-Aware Skill Scheduler**：给现有 skill 增加 joint_load_margin / workspace_margin / mobility_state，只在超过阈值时切换预定义策略，不让 LLM 进入高频控制。
4. **Residual Human Correction**：已有 BC/VLA policy 保持冻结，记录 10–20 分钟人工 intervention，训练小 residual；重点比较新增示范与 residual HIL 谁更快修复长尾失败。
5. **Depth Noise Regression Set**：对 RealSense 在室内、阳光、阴影、夜间采集同路线，固定 locomotion policy，只比较手工 filter、noise augmentation、DAWN-style latent denoising。
6. **VLA Compute Budget Controller**：将 backbone depth / action depth / denoise step 暴露给 task runtime，让 free-space 阶段少算、接触 / 精密阶段多算，并记录 success、P95 latency 与 energy。
7. **Coding-Agent-to-Robot Program Freeze**：让 Codex/Claude 只生成受限 DSL/Python planning program；通过 simulator regression、隐藏测试、静态权限检查后冻结版本，再上真实机器人。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [Free-Init](https://arxiv.org/abs/2609.29375) · [DOI](https://doi.org/10.1109/LRA.2024.3490395) · [GitHub](https://github.com/IMRL/Free-Init)
- [Retrieve-to-Localize](https://arxiv.org/abs/2609.29835)
- [WRAP](https://arxiv.org/abs/2609.29407) · [项目页](https://www.vhartmann.com/wrap)
- [Body-Grounded Replanning](https://arxiv.org/abs/2609.30024)
- [Res-HIL](https://arxiv.org/abs/2609.30023)
- [DAWN](https://arxiv.org/abs/2609.29092) · [项目页](https://dawn-parkour.github.io/) · [代码](https://github.com/DocyNoah/dawn-parkour)
- [Decoupled Early Exits for Flow-Matching VLAs](https://arxiv.org/abs/2609.29382)
- [Coding Agents for Generalized TAMP](https://arxiv.org/abs/2609.30233) · [代码](https://github.com/tomsilver/robocode) · [项目页](https://agenticgentamp.github.io/)
- [CodeQL 2.27.1](https://github.blog/changelog/2026-09-25-codeql-2-27-1-adds-c-and-c-query-and-kotlin-2-4-20-support/)
- [Require proof of presence for high-impact actions](https://github.blog/changelog/2026-09-24-require-proof-of-presence-for-high-impact-actions/)
- [Enterprise managed settings validator](https://github.blog/changelog/2026-09-25-enterprise-managed-settings-in-product-validator/)
- [Velocity Obstacles DOI](https://doi.org/10.1177/027836499801700706)
