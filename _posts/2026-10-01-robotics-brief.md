---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-01"
date: 2026-10-01 09:00:00 +0800
description: "关注 Pow3R-SLAM、可认证 IMU 预积分、RGB-only CBF、安全无人机 MPCC、材料在线辨识、Rho VLA、Gemini 4 Argon 与 Agent Harness Bug 自动复现。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-01

## 摘要

截至 2026-10-01 早间（Asia/Shanghai），arXiv Robotics 最新常规公开批次为 **2026-09-30，共 134 条**，Software Engineering 同日为 **47 条**。本期先核验最近 24 小时的模型与工程发布，再从最新批次中筛选高价值工作，并按规范化标题、arXiv ID、DOI、GitHub 仓库和项目主页与历史覆盖索引强制去重。入选论文的 v1 均实际提交于 9 月 29 日 UTC，因此统一标为“时间回补”；Gemini 4 Argon 是 Google 于 9 月 30 日正式发布的最新模型动态。

今天 SLAM 最值得看的两条路线分别是“学习式 RGB-D 几何前端”和“可认证惯性后端”。**Pow3R-SLAM** 让真实 depth 直接条件化两视图 pointmap 网络，而不是最后才做几何融合；Hybrid 版本达到 25.3 FPS。**QCQP-Representable IMU Pre-Integration** 用 Cayley map 与冗余约束把惯性因子纳入 QCQP/SDP 框架，使 GNSS-IMU smoothing 可以给出全局最优性证书。

控制侧，一项工作把 privileged CBF teacher 蒸馏成只读 RGB 历史、速度与 nominal action 的轻量 safety filter；另一项 **DQ-MPCC** 用 dual quaternion 统一四旋翼 pose/twist 误差表示，在八门赛道真机 100 Hz 运行，最短圈速相对传统 MPCC 降低 10.5%。

机器人操作方面，**FORM** 从一次交互中的材料运动和接触力直接恢复显式 material law，2–5 秒完成材料参数辨识；**Rho** 则发布开放权重双臂 VLA，并用轻量 latent adapter 修正冻结的 flow-matching action expert，论文报告约 15 个 corrected episodes 即可完成一类在线适配。

最新模型方面，Google 于 **2026-09-30** 发布 **Gemini 4 Argon**，定位长时软件工程、企业知识工作和防御性安全，单次输出上限提升到 1M token；当前通过 Fairwind Program 分阶段开放，并非普通 API 用户全面可用。

AI Coding 侧，**AgentBug-Smith** 专门自动发现和复现 Agent harness bug，构建 200 个可执行实例的 Live-Harness-Bench，并把历史修复蒸馏成 reusable repair skills。它提醒我们：模型之外的 session、tooling、permission、MCP 与 sandbox runtime 也必须有自己的 regression suite。

最新公开列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

## 1. Pow3R-SLAM：把 RGB-D 深度当成学习式几何的条件先验

**时间回补：v1 提交于 2026-09-29 17:22 UTC。**

### 为什么重要

实际 RGB-D 深度常有空洞、稀疏和局部噪声。传统系统把这些 depth 直接送进 TSDF/点云融合，只能保留“测到了什么”；Pow3R-SLAM 则先让 depth 条件化两视图 pointmap 网络，利用 RGB、内参与跨帧几何把缺失区域补起来，再进入 metric SLAM。

### 算法模块

~~~text
RGB frame + keyframe + intrinsics + sensor depth
        ↓
depth-conditioned Pow3R
        ↓
pointmaps + confidence
        ↓
metric scaling / Sim(3) tracking
        ↓
keyframes + loop closure + relocalization
        ↓
depth-anchored global optimization
        ↓
dense metric map
~~~

Hybrid 版本让普通帧用 ICP 跟踪、关键帧仍用 Pow3R，从而在几何质量与吞吐之间折中。

### 传感器、实时性与结果

输入是 RGB-D + 相机内参，不依赖 IMU。24 条 TUM、7-Scenes、Replica 序列中，相比 MASt3R-SLAM，论文报告 wall time 快 1.6×、mean trajectory error 低 15%、unscaled error 低 3.1×、Chamfer distance 低 30%；Hybrid 相比 MASt3R-SLAM 快 2.1×并达到 **25.3 FPS**。

### 鲁棒性与工程风险

深度缺失可以由网络补，但“密集且错误的深度”会把网络往错误方向拉。玻璃、强反光、日照干扰、远距离噪声都可能造成这种情况。工程上应同时输出 valid-depth ratio、sensor-vs-network residual、network confidence 与 tracking condition，在冲突过大时主动降低 depth 权重。

### 可复现性、适合谁关注与工程落地

项目页已公开方法、交互地图与深度消融，但代码当前仍标注 review 后开放，因此不能当作已一键复现。适合 RGB-D SLAM、RealSense/D455 室内建图、MASt3R/DUSt3R 系学习式 SLAM 团队。现有系统可以先做三组 A/B：直接深度融合、depth-conditioned learned pointmap、RGB-only learned pointmap。

[论文](https://arxiv.org/abs/2609.38054) · [项目页](https://chriskolios.github.io/Pow3R-SLAM/)

## 2. QCQP IMU Pre-Integration：把惯性因子推进可认证全局估计

**时间回补：v1 提交于 2026-09-29 17:19 UTC；投稿 ICRA 2027。**

### 为什么重要

常见 VIO/LIO/GNSS-IMU 后端依赖 Gauss-Newton 或 LM，工程上很强，但本质只保证局部收敛。若初始化或数据关联很差，求解器仍可能“正常收敛”到错误局部极小值。可认证估计希望进一步回答：当前解是否真的是所建模型下的全局最优。

### 算法模块

~~~text
exponential-map preintegration
        ↓ replace
Cayley-map IMU preintegration
        ↓
QCQP representation
        ↓
lifting variables + redundant constraints
        ↓
tight SDP relaxation
        ↓
certifiable GNSS-IMU smoothing
~~~

传统指数映射难直接进入 polynomial/QCQP 结构，新工作通过 Cayley map 建立可表示的 IMU pre-integration factor，并用额外冗余约束收紧 relaxation。

### 假设、实时性与风险

它改变的是惯性因子的代数表示，不是新的 IMU 传感器模型。论文重点是 relaxation tightness 与 global-optimality certificate，并未声称适合每个 100–400 Hz VIO 更新周期。更现实的应用是低频 batch smoothing、初始化验收或对可疑窗口做影子验证。

“可认证全局最优”只证明数学目标被求对，不会自动修复错误 GNSS association、时间同步、外参或不正确的 bias model。

### 可复现性、适合谁关注与工程落地

当前没有明确公开代码入口。适合 VIO/LIO 因子图、GNSS-IMU、状态估计后端团队。工程上可以让在线局部因子图继续提供实时 pose，再把可疑窗口送到 certifiable backend；若 local solution 与 certificate 明显冲突，再触发重定位或离线诊断。

[论文](https://arxiv.org/abs/2609.38048)

## 3. RGB-only CBF Safety Filter：训练时用特权状态，部署时只留相机

**时间回补：v1 提交于 2026-09-29 02:12 UTC。**

### 为什么重要

RGB-only navigation policy 硬件简单，但传统 CBF 需要显式状态和障碍几何；若部署时再做完整 3D 重建、渲染和安全优化，延迟与算力很快变成瓶颈。

### 算法模块

~~~text
Training:
dynamic Gaussian-Splatting simulation
+ ground-truth robot / obstacle states
        ↓
privileged CBF teacher
        ↓
safe-action supervision
        ↓
RGB-only student

Deployment:
short RGB history + robot velocity + nominal action
        ↓
student safety filter
        ↓
safe action
~~~

Teacher 只为学生 RGB 历史中可观察到的障碍建立约束，并显式考虑 obstacle-velocity uncertainty，避免 teacher 依赖学生永远看不到的信息。

### 实时性、鲁棒性与风险

项目页展示了 sim-to-real 真机导航、braking 和 steering intervention。部署不需要显式在线 3D reconstruction/rendering，但公开材料没有统一毫秒级 P95 latency，因此仍需在目标硬件实测。

需要强调：蒸馏后的 student 是 learned safety filter，并不等于运行时形式化 CBF 证书。OOD 光照、外观和动态模式仍可能误判。

### 可复现性、适合谁关注与工程落地

当前未见完整官方代码发布。适合 RGB-only UAV/UGV、安全策略蒸馏与小算力机器人。产品里建议保留 hard speed/acceleration limit 和 LiDAR/ToF emergency stop，形成 learned filter + deterministic last gate 的双层结构。

[论文](https://arxiv.org/abs/2609.36520) · [项目页](https://syeon-yoo.github.io/distill-cbf-site/)

## 4. DQ-MPCC：用 Dual Quaternion 统一高速无人机的位姿误差表达

**时间回补：v1 提交于 2026-09-29 01:42 UTC。**

### 为什么重要

传统 quadrotor MPCC 常把位置/速度写在 inertial frame，姿态误差又放在 body frame。高速赛道中位置、姿态、progress 强耦合，多坐标系误差表达会放大 sim-to-real tuning。

DQ-MPCC 用 unit dual quaternion 表示 pose，并把 contouring/lag error 投影到 dual-quaternion manifold 的 tangent space，在 desired body frame 里统一 pose-twist 误差。

### 真机结果

作者在 **8 gate、11 × 4.5 × 3.65 m** 赛道做 Monte Carlo SIL 与真机 racing。论文报告：

- 所有完成的 DQ-MPCC 飞行都满足 gate geometric margin；
- baseline 的 median worst-gate offset 从 sim 到 real 增长 71.5%，DQ-MPCC 则下降 10.1%；
- 满足全部 margin 的配置里，最短圈速 simulation 降低 6.7%、真机降低 10.5%；
- **onboard 100 Hz** 运行。

### 动力学假设与工程风险

方法没有消除电机推力误差、气动、风和延迟，而是减少表示本身带来的 tuning mismatch。真机应继续记录 predicted-vs-actual twist、gate margin、solver time、input saturation 与 attitude error。

### 可复现性、适合谁关注与工程落地

当前没有公开代码仓库。适合高速 UAV、MPCC、SE(3)/dual-quaternion control。已有窄走廊 MPC 团队可以固定 dynamics、cost、constraint，只替换 pose/error representation，直接比较 sim→real margin 漂移。

[论文](https://arxiv.org/abs/2609.36482)

## 5. FORM：一次探测，2–5 秒恢复可用于规划的材料参数

**时间回补：v1 提交于 2026-09-29 17:46 UTC。**

### 为什么重要

软物体、弹塑性材料和液体操作中，同一动作对不同材料会产生完全不同结果。纯 model-free policy 要覆盖庞大的材料分布，传统在线 system identification 又可能需要对 differentiable simulator 反复迭代十几分钟。

FORM 从 weak-form momentum balance 出发，把未知 material parameters 整理成线性方程，一次交互后直接做 least squares，不需要通过 simulator 反向传播。

### 算法模块

~~~text
one probing interaction
        ↓
material motion + contact forces
        ↓
weak-form momentum balance
        ↓
same MPM discretization as forward simulator
        ↓
linear least squares
        ↓
explicit material law
        ↓
plan next action
~~~

### 结果、实时性与风险

四类材料中，辨识从迭代 baseline 的约 **10–25 分钟**降到 **2–5 秒**。论文还展示 elastic rod insertion、elastic club putting、elastoplastic shaping 与 target-volume pouring；报告弹性参数误差在 3.4% 内、弹塑性参数 2% 内，pouring 的 mean error 为 3.8 mL。

风险是材料必须能被所选择的 constitutive law / MPM 模型合理描述。破裂、强粘附、泡沫、多相流等未建模现象不会被线性求解自动解释。

### 可复现性、适合谁关注与工程落地

项目页与官方代码均已公开。适合柔性物、工业材料处理、倒液体、软体操作。可以把“主动探测”正式做成 skill：probe → identify_parameters → validate_model → plan → execute；只在 residual 变大时重新辨识。

[论文](https://arxiv.org/abs/2609.38105) · [项目页](https://form-robots.github.io/) · [代码](https://github.com/form-robots/FORM)

## 6. Rho：开放权重双臂 VLA，用轻量 Latent Policy 做现场纠错

**时间回补：v1 提交于 2026-09-29 17:59 UTC。**

### 为什么重要

VLA 产品化后，最贵的往往不是第一次预训练，而是换一个 embodiment、gripper、工作台或现场后又要重采大量 demonstration、重新 finetune 整个 action model。

Rho 把通用动作能力和现场纠错拆开：flow-matching action expert 冻结，小型 latent policy 根据 observation 选择 noise input，从而修正动作。

### 模型与结果

Rho 面向 YAM Box、UR AI Trainer、FR3 Duo 三种双臂平台，并研究 embodiment midtraining 对 data-light adaptation 的影响。论文报告 embodiment-specific variants 在其任务上匹配或超过多种 open-weight VLA；在线适配时，**约 15 个 corrected episodes** 即可处理离线 finetuning 分布边缘的一类情况。

### 可复现性与风险

论文宣布发布 base Rho 与 embodiment-specific checkpoints。15 个 episodes 是论文场景结果，不应外推成固定规律；相机、控制频率、关节空间或 gripper dynamics 变化过大时，小 adapter 可能根本不够。

### 适合谁关注与工程落地

适合双臂、VLA、工业现场小样本适配。更可维护的路线是 freeze base policy → train small residual/latent adapter → held-out regression gate → versioned deployment；只有 adapter 明确不够时才开放整个 action expert finetune。

[论文](https://arxiv.org/abs/2609.38164)

## 7. Gemini 4 Argon：1M 输出 Token 的长时 Agent 模型，但目前分阶段开放

**最新模型动态：Google 于 2026-09-30 正式发布。**

### 突破性工程价值

Google 将 Gemini 4 Argon 定位为复杂、长时的软件工程、企业知识工作与防御性 cybersecurity 模型，单次输出上限提升到 **1M token**。Google 还公布了内部迁移案例，包括大型 C/C++→Rust 工作，以及 libgav1 Rust port 的 profile-guided 优化。

### 官方 benchmark 与价格

Google 官方公布 DeepSWE v1.1 77.9%、AutomationBench 51.3%、CWE-bench v1 68%、LVBench 91.7%。这些是厂商数据，只适合作为“应进入内部 A/B”的信号。

介绍期 API 价格为：

~~~text
Input:        $2 / 1M tokens
Cached input: 输入价的 5%
Output:       $10 / 1M tokens
~~~

官方计划介绍期后调整到 $4 / $20。

### 可用性与安全边界

Argon 当前并未全面公开给普通 API 用户，而是先通过 Fairwind Program 向 trusted cyber defenders 分阶段开放，后续再扩展到更多 paid API customers 和 Google AI Ultra 用户。

Google 同时强调 misuse safeguards、indirect prompt-injection resistance、reasoning/action monitoring、hardened sandbox isolation。这也说明 trajectory 越长，模型外 runtime governance 越重要。

### 适合谁关注与工程落地

适合大型 C++/Rust 迁移、超长 Coding Agent、多文件调查、企业知识工作。未来拿到 API 后，应固定同一 repo/task/tools/timeout，比较 success、wall-clock、total tokens、tool calls、human correction、rollback frequency 和 cost per successful task，而不是单纯把 1M output 打满。

[Google 官方发布](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/)

## 8. AgentBug-Smith：把 Agent Harness 故障自动变成可执行 Regression

**时间回补：v1 提交于 2026-09-29 15:46 UTC。**

### 突破性工程价值

Coding Agent 的线上故障越来越多来自 harness：tool result 没回传、resume 丢历史、permission state 错乱、parallel calls 触发边界问题、MCP 或 sandbox 状态与 Agent 预期不一致。这类问题很难被普通 SWE benchmark 覆盖。

AgentBug-Smith 自动发现、复现开源 Agent 系统中的真实 harness bug，并把它们变成 executable regression instance。

### 结果

相对通用软件 bug reproduction 方法，AgentBug-Smith 在不同 backbone LLM 下把 harness-bug reproduction success 提高 **10.67–27.56 个百分点**；构建的 **Live-Harness-Bench** 当前包含 **200 个**可复现实例。作者进一步从历史修复蒸馏 reusable repair skills，使现有 software agents 的 harness-bug repair rate 再提高 **6.32%**。

### 真实研发价值与风险

内部 Agent 平台每次“resume 失效”“MCP 重连丢工具”“权限 prompt 卡死”都应该产出 fixture、reproducer、expected state、failing trace、fixed trace 和 regression test，而不是只留一条 issue 描述。

Harness regression 往往会触发 shell、文件、网络和认证路径，因此必须在 disposable sandbox、fake credential 或 mock service 中复现，不要为了“真实”而把生产权限带进测试。

### 可复现性、适合谁关注与工程落地

论文声明代码与数据公开，但本次检索未稳定获得对应仓库直链，因此这里只保留 arXiv 原始入口。适合自研 Coding Agent、Claude Code/Codex 周边平台、MCP runtime、权限系统和长期 session。建议建立固定流程：incident → minimal executable reproducer → harness regression suite → fix → replay old failures。

[论文](https://arxiv.org/abs/2609.37864)

## AI Coding 实战技巧精选

### 技巧 1｜在 Claude Code 建一个名为 verify 的 Skill，让提交前自动跑验证

- **来源**：[Anthropic Claude Code v2.1.286，2026-09-30](https://github.com/anthropics/claude-code/releases/tag/v2.1.286)。
- **一句话结论**：如果项目或用户 Skills 中存在名为 **verify** 的 Skill，Claude Code v2.1.286 会在准备 commit 前提醒模型运行它；docs-only 和 tests-only commit 例外。把 build/test/lint/static check 集中到这个 Skill，比每次 Prompt 里写“记得测试”稳定。
- **具体怎么做**：
  1. 使用现有 Skill 机制创建名为 verify 的项目 Skill。
  2. Skill 只放机械验证，例如 unit test → lint/typecheck → build；失败立即停止。
  3. C++/ROS2 可以放目标 package build + test；Node 项目则放 npm test / lint / typecheck。
  4. 升级 v2.1.286 后用普通代码改动实测触发，并继续保留 CI 作为最终 gate。
- **适合什么场景**：Claude Code、大仓库、AI 自动 commit、团队统一提交前验收。
- **注意**：verify Skill 不替代 GitHub Actions / protected branch；依赖秘密凭据的验证仍应在 sandbox 或 CI 运行。

### 技巧 2｜长 Agent 把稳定前缀显式 Cache，动态日志放到 Breakpoint 后面

- **来源**：[OpenAI Prompt Caching 官方指南](https://developers.openai.com/api/docs/guides/prompt-caching) · [官方更新](https://openai.com/index/better-prompt-caching-for-gpt-6/)。
- **一句话结论**：缓存命中最怕把时间戳、用户输入和不断变化的 tool output 混进稳定前缀。GPT-5.6 及更新模型可以显式设置 cache mode / breakpoint，只缓存稳定 instructions、tool schema 与项目规则。
- **具体怎么做**：
  1. 固定 system/developer 规则、tool schema、repo conventions 放在前面；当前任务和动态日志放后面。
  2. 设置：
     ~~~json
     {"prompt_cache_options":{"mode":"explicit"}}
     ~~~
  3. 在稳定 developer content 末尾添加：
     ~~~json
     {"prompt_cache_breakpoint":{"mode":"explicit"}}
     ~~~
  4. 上线前比较 cached_tokens、cache_write_tokens、latency 和总成本；异常 miss 时用 Prompt Cache Diagnostics 查 model、tools、settings 或 prefix 是否变化。
- **适合什么场景**：Codex / Agents API、自研长时 Coding Agent、多 session fork、tool 定义很多的系统。
- **注意**：显式 cache write 本身有成本，只有 prefix 会复用才值得写；不要为了 cache hit 把权限或用户上下文错误固定在稳定区。

## 经典论文回顾

### SE-Sync：把“SLAM 后端收敛了”推进到“我能证明这个解是全局最优”

David M. Rosen、Luca Carlone、Afonso S. Bandeira、John J. Leonard 的 **SE-Sync: A Certifiably Correct Algorithm for Synchronization over the Special Euclidean Group** 是机器人可认证状态估计的代表性经典工作，完整期刊版发表于 **IJRR 2019**。

### 核心问题与数学思想

Pose-graph SLAM 在 SE(d) 上根据 noisy relative-pose measurement 估计全局 poses，常规 Gauss-Newton/LM 只能说明数值优化收敛，不能证明得到 global optimum。

SE-Sync 为 SE(d) synchronization 构造 semidefinite relaxation，并利用问题的低秩和图结构做高效 Riemannian optimization。在一类实际噪声条件下 relaxation 是 exact 的，系统不仅给出 pose，还能提供 a-posteriori certificate，证明当前结果是原问题的 global optimum。

~~~text
nonconvex pose-graph MLE
        ↓
semidefinite relaxation
        ↓
low-rank geometric structure
        ↓
Riemannian optimization
        ↓
rounding
        ↓
pose estimate + certificate
~~~

### 当年为什么重要、今天仍在使用的思想

它把“找到一个解”和“证明这个解全局最优”明确分开。今天越来越多状态估计系统希望同时输出 pose、covariance、consistency、relaxation gap 与 certificate，而不是只给 trajectory。

今天的 QCQP IMU pre-integration 正好沿着这条路线继续推进：SE-Sync 更偏 relative-pose synchronization，新工作则尝试把惯性 pre-integration 也变成 certifiable framework 能接受的代数形式。

### 已被后续扩展的部分

后续研究继续扩展到 robust/outlier-resistant certifiable estimation、rotation/pose averaging、range/bearing localization、GNSS-IMU smoothing、stronger sparse relaxations 与 certifiable initialization。高频在线 LIO/VIO 仍通常采用高效局部优化，因为每帧跑全局 certificate 并不划算。

### 公开代码与可复现性

官方实现仍公开：[SE-Sync GitHub](https://github.com/david-m-rosen/SE-Sync)。

最有价值的复现实验是给同一 pose graph 多组差初值，比较 Gauss-Newton final cost、SE-Sync certified optimum、relative gap、runtime 与 certificate 成功率。

### 对当前工程项目的重新解读

LIO-SAM / 多雷达系统不需要把 SE-Sync 塞进高频 tracking。更实际的架构是：

~~~text
high-rate local estimator
→ ESKF / factor graph

low-rate global backend
→ loop closure / GNSS / reflector

suspicious optimization window
→ certifiable checker
~~~

当回环很多、走廊退化或 RTK 突然拉动整图时，用 certificate 做低频验收，比让同一个 local solver“自己证明自己”更可靠。

[论文页](https://david-m-rosen.github.io/publication/sesync-ijrr/) · [DOI](https://doi.org/10.1177/0278364918784361) · [arXiv](https://arxiv.org/abs/1612.07386) · [代码](https://github.com/david-m-rosen/SE-Sync)

## 今日结论

今天最明显的共同趋势，是把“模型会做”进一步变成“系统知道什么时候能信、能改、能证明”。

Pow3R-SLAM 让真实深度直接改变 learned geometry prediction；QCQP IMU 与 SE-Sync 则把后端从“收敛”推进到“可认证”。学习前端和数学后端并不冲突：一个负责提供更强观测，另一个负责给结果加可解释的约束与可信度。

RGB-only CBF distillation 说明复杂安全计算可以在训练时使用特权信息、部署时压成轻量 filter；DQ-MPCC 说明并非所有 sim-to-real 问题都要靠更大网络，状态和误差表示的几何一致性本身就可能减少真机漂移。

FORM 与 Rho 都在降低现场适配成本，但一个恢复显式材料参数，一个冻结大模型只训练小 adapter。二者共同指向一种更可维护的在线学习方式：让可变参数空间小、版本可回滚、失败域可定位。

Gemini 4 Argon 把单次输出推到 1M token，同时 Google 仍把 sandbox、prompt injection 和 action monitoring 单独作为安全层；这说明 trajectory 越长，模型外 runtime contract 越重要。

如果把今天压成一句话：

> **机器人与 Coding Agent 的下一步，不只是提高生成能力，而是让观测、状态估计、安全、现场适配和执行 Harness 都变成可验证、可回滚、可持续测试的系统组件。**

## 最值得深入研究或尝试复现的方向

1. **Pow3R-SLAM Depth-as-Prior A/B**：固定 backend，对比直接深度融合、depth-conditioned pointmap、RGB-only pointmap，专测洞区质量和错误深度敏感性。
2. **Certifiable Backend Shadow Mode**：实时 LIO/GNSS 因子图不变，定期把可疑窗口送入 certifiable solver，比 local solution cost、certificate 与异常段。
3. **RGB Safety Distillation Sidecar**：privileged CBF 离线自动产 correction label，部署只留小 safety filter，并保留 LiDAR/ToF emergency gate。
4. **Dual-Quaternion MPCC 对照**：dynamics/cost/constraints 不变，只替换 pose/error representation，测 sim→real gate-margin 漂移。
5. **FORM Probe-Identify-Plan Skill**：设计低风险探测动作，显式估参数并保存 residual，再决定是否继续规划。
6. **VLA 小适配层优先**：冻结 base expert，用 10–30 条现场 correction 训练 residual/latent adapter，过不了 regression 才开放全模型 finetune。
7. **Harness Bug Regression 化**：Agent runtime 每个真实事故都必须产出 executable reproducer，进入固定 regression。
8. **Prompt Cache 工程化**：拆稳定 rules/tool schema 与动态日志，用 explicit breakpoint 后持续监控 cache-hit、write token 与每成功任务成本。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [Pow3R-SLAM](https://arxiv.org/abs/2609.38054) · [项目页](https://chriskolios.github.io/Pow3R-SLAM/)
- [A QCQP-Representable IMU Pre-Integration Factor for Certifiable State Estimation](https://arxiv.org/abs/2609.38048)
- [Distilling Privileged Control Barrier Functions into RGB-Only Safety Filters](https://arxiv.org/abs/2609.36520) · [项目页](https://syeon-yoo.github.io/distill-cbf-site/)
- [DQ-MPCC](https://arxiv.org/abs/2609.36482)
- [FORM](https://arxiv.org/abs/2609.38105) · [项目页](https://form-robots.github.io/) · [代码](https://github.com/form-robots/FORM)
- [Rho](https://arxiv.org/abs/2609.38164)
- [Gemini 4 Argon 官方发布](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/)
- [AgentBug-Smith](https://arxiv.org/abs/2609.37864)
- [Claude Code v2.1.286](https://github.com/anthropics/claude-code/releases/tag/v2.1.286)
- [OpenAI Prompt Caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [SE-Sync](https://david-m-rosen.github.io/publication/sesync-ijrr/) · [DOI](https://doi.org/10.1177/0278364918784361) · [代码](https://github.com/david-m-rosen/SE-Sync)
