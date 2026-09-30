---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-30"
date: 2026-09-30 09:00:00 +0800
description: "本期关注 World SLAM Model、森林 VIO 实测、3DGS 实时碰撞规划、自适应 MPC 与安全过滤、多机器人扩散规划、GPT-6.1 Sol，以及 MCP 错误信息对 Agent 恢复能力的影响。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-09-30

## 摘要

截至 2026-09-30 早间（Asia/Shanghai），arXiv Robotics 最新常规公开批次为 **2026-09-29，共 243 条**，Software Engineering 同日也刷新了最新批次。本期先检查最近 24 小时公开与更新内容，再从最近 7 天补足高价值且尚未进入覆盖索引的工作；所有候选均按规范化标题、arXiv ID、DOI、GitHub 仓库与项目页和历史索引做强制去重。

今天 SLAM 方向有两件事尤其值得关注。**World SLAM Model** 不再把 SLAM 只当成给导航提供 pose / map 的前置模块，而把“增量状态更新、持久记忆、后端纠错”本身放进世界模型，让未来视觉预测、相机运动、稠密几何和动作生成共享同一个持续更新的 world state。**ForVis** 则给了一个很务实的反例提醒：森林 VIO 里，换一颗相机带来的误差变化，可能比换七套算法之间的差异还大。它用 D435i 和 OAK-D Pro Wide 同步采集 12 次真实 UAV 飞行，七套开源 VI-SLAM 共跑 504 次，所有算法在 OAK-D Pro 上的 median error 都更低。

规划侧，**CollisionSplatting** 直接在标准 3DGS 上构造 GPU 加速、可调保守度的碰撞距离度量，再同时接入 MPPI 和 RRT。这个方向很关键，因为 3DGS 如果只能“看起来逼真”，却还要另外维护 ESDF / mesh 才能规划，地图栈仍然是分裂的。

控制侧今天呈现出一个共同趋势：**算力和安全余量都开始按需分配。** Fast-TD-MPC 在快速 policy execution 和昂贵 test-time planning 之间动态路由，103 个连续控制任务中最高获得约 4× 推理加速，受到外部扰动时再回退到规划。Adaptive RACF 则冻结原 ACC policy，只根据已完成 transition 的 residual 做 conformal calibration，把 residual quantile 变成 action projection 的安全 margin。

多机器人方面，**Denoising Multi-Robot Trajectories / D4orm** 把 diffusion denoising 当作采样优化器，而不是生成一个“看起来像轨迹”的模型。论文展示 10 架真机 quadrotor、100 个仿真机器人和 6 台完全 onboard 的地面机器人长期运行。官方代码当前已经发布 D4orm-D，可直接和 MPPI / CEM 做同环境对照。

AI Coding 今天有两条非常实际。第一，OpenAI 于 9 月 29 日发布 **GPT-6.1 Sol**：API 仍是 Sol 价格区间——每百万输入 token 2 美元、缓存输入 0.10 美元、输出 10 美元——但官方报告它在 DeepSWE、AutomationBench 和 computer-use 上显著接近 Astra。第二，最新修订的 MCP error-message 研究指出：很多 MCP server 把“给人类开发者看的修复步骤”原样喂给只能调用工具的 Agent，反而会误导更强模型。真正有效的修复方式是让错误信息明确指出 Agent 可以调用的恢复工具。

[arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)

## 1. World SLAM Model：让世界模型本身按 SLAM 的方式维护状态

**时间回补：v1 提交于 2026-09-26 13:44 UTC。**

### 为什么重要

很多机器人基础模型的长期记忆仍然更像“把过去若干帧、token 或 latent 塞进 context”。经典 SLAM 则会持续加入新观测，并在后端发现回环或累计误差后反过来修正旧状态。World SLAM Model（WSM）的核心价值，是把这种增量状态、持久记忆和后端修正机制真正拿进 world model，而不只是把 SLAM 生成的 pose / depth 当外部条件。

### 算法模块

~~~text
RGB observation + navigation goal
        ↓
generation expert
→ goal-conditioned future visual states
        ↓
SLAM expert
→ camera motion
→ dense geometry
→ persistent spatial world state
        ↓
incremental update + backend refinement
        ↓
action generation / closed-loop navigation
~~~

真实观测帧与 dreamed future 都进入同一空间状态估计过程，模型维护的是持续演化的 world state，而不是每个 planning step 都重新从上下文猜地图。

### 传感器、实时性与鲁棒性

项目目前强调 RGB-only start-goal navigation。它同时预测相机运动与稠密几何，但这不等于已经替代真实机器人上的 IMU / LiDAR metric estimator。项目页在 InternVLA-N1 benchmark 上报告较高的 SR / SPL，同时保留 SLAM 能力；当前没有适合直接外推到嵌入式机器人的统一控制频率。

### 可复现性与风险

项目页已提供论文与代码入口。真正值得复现的是架构原则：长期 world state 应该是显式、可被后续观测修正的对象。

后端修旧状态后，上层历史 action / semantic memory 如何重绑定是关键风险。建议 world-state element 至少保存 state_id、pose_revision、observation_sources、confidence、last_refined_at、semantic_links。

### 适合谁关注

视觉 SLAM、语义导航、VLA / world model、长期机器人记忆，以及希望把建图和规划从松耦合接口推进到联合模型的团队。

### 工程落地启发

已有 FAST-LIO / LIO-SAM 不必立即更换。更实际的是让 learned world-model memory node 绑定稳定 map/submap ID，并允许 pose graph 更新时重新投影 memory，先实现 SLAM-style persistent memory。

[论文](https://arxiv.org/abs/2609.32626) · [项目页](https://tsinghua-mars-lab.github.io/WorldSLAMModel/)

## 2. ForVis：森林 VIO 中，传感器选择可能比算法选择更影响误差

**时间回补：v1 提交于 2026-09-28 15:57 UTC。**

### 为什么重要

真实森林 UAV 会面对重复枝叶纹理、大动态范围、飞行振动、高速姿态变化、近距离植被遮挡，以及草地、冠层上方、林下三种差异明显的视觉条件。ForVis 同时安装两套常见视觉惯性设备，让算法误差和硬件误差能被分开观察。

### 数据与评测

~~~text
12 flights
563.8 s
1096.8 m trajectory

Sensors simultaneously:
- Intel RealSense D435i
- OAK-D Pro Wide
- IMU
- flight-controller data
~~~

作者对七套开源 VI-SLAM 系统执行 **504 次**完整评测。最值得记住的结果不是哪套算法第一，而是所有七种方法在 OAK-D Pro 上的 median trajectory error 都低于 D435i；传感器选择造成的影响，大于算法之间的整体 spread。

### 传感器假设、实时性与风险

这说明 VIO 选型前应先确认 exposure control、motion blur、FOV、rolling/global shutter、IMU noise、camera-IMU time sync、振动安装是否已经成为更大的误差源。某一相机在该 benchmark 更好也不能直接外推到所有机器人；镜头、曝光、IR、飞行高度和森林类型都会改变结果。

### 可复现性

论文给出了真实 UAV 数据与七套开源 VI-SLAM 的系统化对照。当前 arXiv 页面未稳定提供官方数据主页，因此本期只引用原论文。

### 适合谁关注

室外 UAV、森林巡检、单目 / 双目 VIO、相机与 IMU 硬件选型、狭窄环境高速视觉定位。

### 工程落地启发

固定同一轨迹同步录多套 sensor，然后做两组实验：algorithm fixed, sensor changes；sensor fixed, algorithm changes。先拆分硬件和算法的真实贡献，再决定优化投入。

[论文](https://arxiv.org/abs/2609.35482)

## 3. CollisionSplatting：3DGS 开始直接承担实时碰撞查询

**时间回补：v1 提交于 2026-09-28 16:57 UTC。**

### 为什么重要

3DGS 很适合做高保真地图，但规划器真正需要的是 collision、distance-to-obstacle、gradient / cost。如果 3DGS 最后还必须转换成 mesh / voxel / ESDF，系统仍然需要第二套几何地图和额外显存。

CollisionSplatting 直接在标准 3DGS scene 上构造 GPU 加速、probability-inspired 的距离度量，并允许显式调节 conservatism。

### 算法模块

~~~text
standard 3D Gaussian scene
        ↓
probability-inspired collision distance
        ↓
tunable conservatism
        ↓
geometric collision + image-conditioned objectives
        ↓
GPU MPPI / RRT
~~~

### 传感器假设与结果

方法假设已经得到质量足够的 3DGS map。论文报告 collision classification 达到或超过代表性 baseline，同时显著提高 collision-checking throughput、降低 VRAM，并集成 GPU MPPI 与 RRT，展示真实视觉引导导航和操作任务。

### 鲁棒性与工程风险

定位误差、Gaussian 尺寸错误和动态物体都会直接进入 collision metric，因此“渲染逼真”不等于“几何安全”。可调 conservatism 很有工程价值，但下一步最好让 localization covariance、map age 和 Gaussian uncertainty 共同决定 margin。

### 可复现性

当前论文没有稳定公开正式代码地址。最容易做的工程复现是把现有 3DGS 与 ESDF / mesh ground truth 做 collision-query benchmark，比较 throughput、VRAM、false-safe 与 false-block。

### 适合谁关注

3DGS SLAM、视觉导航、机械臂规划、MPPI、RRT，以及希望减少渲染地图和规划地图双份存储的团队。

### 工程落地启发

3DGS 产品除了 PSNR / SSIM，至少还应 benchmark collision query throughput、false-safe rate、false-block rate、VRAM、map update latency 和 localization-error sensitivity。

[论文](https://arxiv.org/abs/2609.35619)

## 4. Fast-TD-MPC：不是每个控制周期都值得启动完整 Planner

**时间回补：v1 提交于 2026-09-26 13:10 UTC。**

### 为什么重要

Data-driven MPC 每一步都 rollout 大量 trajectory 会拖慢控制频率；纯 policy inference 虽快，却在 disturbance / OOD state 下缺少在线修正。Fast-TD-MPC 把问题改成：当前这个状态是否值得支付一次完整 test-time planning 的算力成本。

### 算法模块

~~~text
current state
     ↓
adaptive router
  ┌──┴───────────────┐
  ↓                  ↓
fast policy       planner
execution         deliberation
  └──────┬───────────┘
         ↓
       action
~~~

正常、熟悉状态走快速 policy；需要更强 deliberation 时才调用规划。

### 结果与实时性

论文在 **103 个 continuous-control task** 上保持竞争力表现，同时 inference 最高约 **4× 更快**。受到外部 disturbance 时，系统会选择性回退到 planning，鲁棒性接近原始每步规划器。

### 动力学假设与工程风险

真正危险的是 router false negative：本应 planning 却走 fast policy。因此实际机器人上 router 不应只读取 policy confidence，还应输入 constraint margin、model residual、tracking error、contact event。

部署建议记录 planning_trigger_rate、P50/P95 latency、planner_burst_duration、deadline_miss 和 disturbance_recovery_time。

### 可复现性

当前没有稳定代码入口。已有 TD-MPC / sampling MPC 的系统可以先做 rule-based baseline：tracking residual 或 safety margin 越界才触发 planner，其余时刻走 policy，先验证选择性规划能省多少算力。

### 适合谁关注

学习式 MPC、MPPI、四足 / 无人机高频控制、端侧算力有限但希望保留在线 planning robustness 的团队。

### 工程落地启发

easy corridor 可以走 local policy / velocity controller；uncertainty 上升、constraint margin 下降或出现 unexpected obstacle 时再触发 expensive planner。算力应该跟任务难度动态分配。

[论文](https://arxiv.org/abs/2609.32591)

## 5. Adaptive RACF：冻结 ACC Policy，只在线校准“模型到底错了多少”

**时间回补：v1 提交于 2026-09-28 15:29 UTC。**

### 为什么重要

真实部署后，轮胎、载荷、延迟和环境都会变化。重新训练 policy 成本高，固定 worst-case margin 又容易过度保守。Residual-Aware Conformal Filtering（RACF）不改 policy 和 nominal predictor，只用真实 transition residual 估计当前误差分布，再把 conformal quantile 转成 action projection margin。

### 算法模块

~~~text
frozen policy
      ↓
candidate action
      ↓
fixed nominal predictor
      ↓
finite-model action projection
      ↑
conformal residual quantile
      ↑
completed real transitions
~~~

### 结果与权衡

在 **2,400 个 controller-trial unit** 的注册对比中，Adaptive RACF：

- episode safety 为 94.3%；
- 相对评测中的 nominal CBF-QP 提高 19.9 个百分点；
- projection frequency 从 8.11% 降到 6.63%。

单独控制实验中 residual-margin injection 带来 4.54 个百分点提升。

硬件 matched evaluation 也显示重要 trade-off：相对 Robust CBF-QP，平均 amortized rollout time 降低 21.2%，安全 episode 是 161/180，而对方是 170/180。计算更省不等于所有安全指标都更好。

### 鲁棒性与工程风险

Conformal coverage 依赖 residual 分布和 calibration 条件；严重 regime shift 后，过去 residual quantile 可能不再代表当前风险。应监控 residual_quantile、calibration_window_age、coverage_violation、projection_rate 与 policy_action_vs_applied_action，离群时进入 hard fallback。

### 可复现性

论文目前未公开成熟代码入口。最小实验是在现有 CBF / action shield 上增加滚动 residual quantile，与 fixed margin 做同任务 A/B。

### 适合谁关注

安全 MPC / CBF、RL safety filter、车辆控制、希望不重训已有 policy 就适应 Sim2Real / deployment drift 的团队。

### 工程落地启发

如果已有稳定策略，优先让 safety margin 在线适配，而不是重新打开整个 policy 继续训练，failure domain 更容易定位和回滚。

[论文](https://arxiv.org/abs/2609.35415)

## 6. Denoising Multi-Robot Trajectories：把 Diffusion 变成多机器人在线轨迹优化器

**时间回补：v1 提交于 2026-09-28 17:18 UTC；已接受 IEEE Transactions on Robotics。**

### 为什么重要

多机器人 trajectory planning 同时高维、非凸、多模态并带动力学约束。D4orm 不把 diffusion 当作离线生成模型，而把 diffusion-style denoising 本身当成采样优化过程，持续 deformation 候选 control trajectory。

### 算法模块

~~~text
D4orm
→ massively parallel samples
→ denoise / deform control trajectories
→ kinodynamic feasibility
→ conflict-free trajectories

variants:
1. decoupled planner
2. online receding-horizon + feedback
3. distributed planner
~~~

### 实时性与扩展性

论文覆盖 differential-drive、holonomic、2D / 3D 环境，并与 MPPI 和 learned diffusion planner 对比。规模验证包括：

- 10 架真实 quadrotor 零样本部署；
- 100 个仿真机器人 deconfliction；
- 6 台地面机器人完全 onboard、distributed、lifelong operation。

### 可复现性

官方仓库已开放，当前 release 包含 D4orm-D：

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .

d4orm --method d4orm-d --env-name multi2dholo --num-agents 16 --save-images
~~~

仓库也提供 MPPI 和 CEM 便于同环境比较。README 说明其他 D4orm variant 会逐步开放，因此目前不能把论文所有 planner 都当成已完整发布。

### 工程风险

采样并行不等于通信和感知问题消失。真实 distributed 系统仍需处理邻居 state latency、packet loss、localization error 和独立 emergency collision layer。

### 适合谁关注

多 UAV、多 AGV、仓储 fleet、多机器人 MPC / trajectory optimization，以及希望利用 GPU 做大规模并行候选搜索的团队。

### 工程落地启发

先用 D4orm-D 做 4 / 8 / 16 / 32 robot shadow benchmark，记录 planning time、success、minimum separation、control smoothness、GPU memory，再决定是否接入在线系统。

[论文](https://arxiv.org/abs/2609.35651) · [官方代码](https://github.com/proroklab/d4orm)

## 7. GPT-6.1 Sol：更值得关注的是“同预算可以跑更多 Agent 任务”

**最新发布：OpenAI 于 2026-09-29 正式发布。**

### 突破性工程价值

GPT-6.1 Sol 是 GPT-6 Sol 的升级，官方定位集中在 agentic coding、computer use 和 professional work，同时保持 Sol 级 API 定价：

~~~text
Input         $2 / 1M tokens
Cached input  $0.10 / 1M tokens
Output        $10 / 1M tokens
~~~

API model id 为 gpt-6.1-sol。

### 官方结果怎么读

OpenAI 报告 DeepSWE v1.1 表现接近 / 匹配 Astra，成本约其五分之一，并比 GPT-6 Sol 最佳结果高 6.4 个百分点；AutomationBench 在 medium reasoning 下比 Opus 5.5 高 2.2 个百分点，约三分之一成本；OSWorld 2.0 在最大 reasoning 下比 GPT-6 Sol 高 7 个百分点；Terminal-Bench Science 提升明显，但最难科学任务 Astra 仍更强。

这些属于厂商评测，应视为“值得进入内部 regression set”的信号，而不是直接替换所有模型的依据。

### 是否适合真实研发流程

固定 same task、same repo SHA、same tools、same timeout、same reasoning budget，然后比较 success、wall-clock、input/output token、tool-call count、test reruns 和 human correction。真正优化的是每个成功任务成本。

### 权限 / 安全 / 可验证性

官方安全评估报告 GPT-6.1 Sol 在 broken-tool transparency、显式限制遵循和 unauthorized outcomes 等方面比 GPT-6 Sol 更好，但模型更强不应该自动获得更高权限。A/B 必须保持 same sandbox、network policy、write approvals、merge/release gate 和 idempotency contract。

### 可用性

发布时已进入 API、ChatGPT Work 和 Codex；GitHub 于 9 月 29 日宣布开始在 Copilot 各客户端滚动开放。

### 适合谁关注

Codex、GitHub Copilot、多模型 Coding Agent router、长任务自动化、大规模 API Agent 工作负载。

### 工程落地启发

routine code task 可以优先试 6.1 Sol；hard unresolved task 再 fallback 到 Astra；critical release 则坚持 model + independent verifier。不要默认“最强模型永远常驻”。

[OpenAI 官方发布](https://openai.com/index/introducing-gpt-6-1-sol/) · [GitHub Copilot 上线说明](https://github.blog/changelog/2026-09-29-gpt-6-1-sol-in-github-copilot/)

## 8. MCP Error Messages：给人看的“修复提示”，可能恰恰是 Agent 的毒药

**最新更新：v2 于 2026-09-29 03:56 UTC 修订。**

### 突破性工程价值

MCP server 经常把传统 Web API 的错误提示直接返回给 Agent，例如 Run this CLI command、Edit your config、Open this page、Wait and retry。对人类有用，但 tool-only Agent 可能根本没有 terminal、browser 或 config-edit 权限。

论文检查 **150 个常用 MCP server**，3,001 条 error message 中有 949 条明确告诉 caller 下一步做什么，而其中约一半步骤依赖 server 无法知道的 caller capability。

### 结果

credential error 中，62/67 个步骤要求 terminal command、配置修改或网页；rate-limit error 中 20/30 只说等待重试，却没有指出应重试哪个 tool call。

在 BFCL-style tool-only 测试中，expired credential 场景保留终端指令后只有 **45%** recovery；影响从 GPT-5.5 的 18 个百分点扩大到 GPT-6 Astra 的 69 个百分点。GitHub 风格的 “Wait before retrying.” 在对应 rate-limit 实验中只剩 **6%** recovery。

### 真正有效的修复

错误信息直接命名 server 可调用的 login tool 后，credential recovery 到 84%；明确指出应重复的 call 后，rate-limit recovery 到 88%。如果暂时无法改 server，Agent-side compatibility layer 删除不可执行的人类步骤并换成 capability-aware 提示，expired credential recovery 到 82%。

### 权限与安全风险

解决方案不是给 Agent 更多权限。更合理的 error contract 应包含：

~~~text
error_code
retryable
recovery_tool
retry_after
required_capability
operation_id
~~~

Agent 只在已经授权的能力内恢复。

### 可复现性

代码和数据已公开，复现分析可运行：

~~~bash
python survey/make_tables.py
python experiment/code/analyze.py
python experiment/code/plot_figures.py
~~~

### 适合谁关注

自研 MCP server、Coding Agent tool runtime、企业 connector，以及需要自动恢复 credential / permission / rate-limit 故障的 Agent 平台。

### 工程落地启发

内部 MCP error lint 可以立刻要求：如果错误文字包含 shell / browser / config / wait 指令，就必须同时声明 recovery_tool、required_capability、retryable 与 operation_id；没有 Agent 可执行恢复路径时，明确返回 human_action_required。

[论文](https://arxiv.org/abs/2609.35381) · [代码与数据](https://github.com/WenJing95/tool-error-text)

## AI Coding 实战技巧精选

### 技巧 1｜给 Coding Agent 安装 OpenAI 官方 Developers Plugin / Docs MCP

- **来源**：[OpenAI Developers 官方文档](https://developers.openai.com/learn/developers-codex-plugin)。
- **一句话结论**：不要让 Coding Agent 只靠训练记忆猜最新 API、model ID 和 Agents SDK 用法；让它直接查询官方当前文档。
- **具体怎么做**：
  1. Codex CLI 中启动 codex，执行 /plugins，搜索 **OpenAI Developers** 并安装。
  2. Claude Code 中执行：
     ~~~text
     /plugin marketplace add openai/openai-developers-for-claude
     /plugin install openai-developers@openai-developers
     ~~~
  3. 安装后新开 session，再处理 OpenAI API、Agents SDK、model migration 或错误排查。
  4. 对关键 API 调用要求 Agent 明确最终使用的 model ID / API surface。
- **适合什么场景**：Codex、Claude Code、Cursor 中开发 OpenAI API / Agents SDK / MCP / plugin 项目。
- **注意**：官方 Docs MCP 能降低记忆过期，但不能替代 integration test，也不代表当前账号已经拥有相应 model / feature 权限。

### 技巧 2｜自托管 Coding Agent 时，把业务 API Key 留在 Sandbox 外

- **来源**：[OpenAI Agents API 官方文档](https://developers.openai.com/api/docs/guides/agents-api/environments/self-hosted)。
- **一句话结论**：不要把主 OPENAI_API_KEY、云凭据和其他 workload 文件一起塞进 Agent 容器；每个用户 / workload 独立环境，sandbox 内只放受限 executor key。
- **具体怎么做**：
  1. 每个用户或 workload 建独立 workspace；共享环境意味着 Agent 可以访问同一批文件、凭据和资源。
  2. sandbox 内安装 Codex：
     ~~~bash
     mkdir -p /workspace
     npm install -g @openai/codex@alpha
     ~~~
  3. 创建单独 environment key，把其他权限全部设为 None；业务 OPENAI_API_KEY 留在 sandbox 外，只把 environment key 作为 CODEX_API_KEY 传入。
  4. 启动 executor：
     ~~~bash
     codex exec-server \
       --remote "<session.environment.remote_url>" \
       --environment-id "<session.environment.id>"
     ~~~
- **适合什么场景**：公司内部 Coding Agent、GPU / ARM 自托管 runner、需要访问私有仓库或本地构建链的 Agents API worker。
- **注意**：Agent 生成的代码仍能读取 environment key，所以它必须只能连接 environment，不能拥有普通 API / 数据权限；也不要写进 image、源码或日志。

## 经典论文回顾

### GPMP2：把连续时间运动规划改写成因子图上的概率推断

Mustafa Mukadam、Jing Dong、Xinyan Yan、Frank Dellaert 与 Byron Boots 的 **Continuous-Time Gaussian Process Motion Planning via Probabilistic Inference** 是 GPMP / GPMP2 路线的代表工作：GPMP2 论文发表于 RSS 2016，完整连续时间版本发表于 IJRR 2018。

### 核心问题

传统 trajectory optimization 往往在固定离散时间点保存大量状态。如果时间分辨率低，两个 knot 之间可能撞障碍；如果分辨率高，变量数量和优化成本迅速膨胀。GPMP2 把整条连续轨迹视为 Gaussian Process，只优化少量 support states，任意中间时刻通过 GP interpolation 高效恢复。

### 关键数学思想

运动规划被写成 MAP inference：

~~~text
trajectory prior
→ GP smoothness factors

obstacles
→ obstacle likelihood factors

start / goal
→ boundary factors

joint limits / task constraints
→ constraint factors

all factors
        ↓
factor graph optimization
        ↓
continuous-time trajectory
~~~

这样可以直接利用 GTSAM 的稀疏结构和数值优化。

### 当年为什么重要

它把 SLAM 社区成熟的 factor-graph machinery 带进 motion planning，并给出统一连续时间视角：trajectory smoothness 是 GP prior，collision 是 likelihood，planning 是 posterior inference。

### 今天仍在使用的思想

最没有过时的三点是：

1. **连续时间轨迹不等于必须高密度离散化。**
2. **规划约束可以像 SLAM factor 一样模块化组合。**
3. **只在少量 support state 优化，中间状态按需插值。**

今天 CollisionSplatting 正好可以和它组合理解：3DGS 提供新的 collision distance query，GPMP2 提供 continuous-time factor-graph trajectory representation。

### 已被后续扩展的部分

现代 GPU sampling MPC、MPPI、diffusion planning 更善于并行探索多模态 / 非凸候选；GPMP2 属于局部 gradient-based optimization，初始化不好仍可能陷入局部最优。后续还有 iGPMP2、Lie-group GP trajectory、differentiable GPMP2、学习式 cost factor 等路线。

### 传感器 / 动力学假设

GPMP2 本身不是定位算法，不决定传感器；它需要 planner 能查询机器人状态、平滑/动力学先验和障碍代价。环境地图可以来自 occupancy / SDF，也可以是今天的 3DGS collision field。

### 公开代码与可复现性

官方仓库为 borglab/gpmp2，核心 C++，提供 Python / MATLAB toolbox，依赖 GTSAM。

~~~bash
git clone https://github.com/borglab/gtsam.git
# build / install GTSAM

git clone https://github.com/borglab/gpmp2.git
cd gpmp2
mkdir build && cd build
cmake ..
make -j4 check
sudo make install
~~~

### 对当前工程项目的重新解读

真正值得借鉴的是“轨迹表示”和“地图查询”解耦：

~~~text
trajectory representation
→ GP / spline / controls

collision backend
→ ESDF / point cloud / 3DGS

state estimation
→ LIO / VIO

optimizer
→ factor graph / MPPI / diffusion
~~~

这样未来更换 CollisionSplatting、ESDF 或新地图表示时，不需要同时重写整个 planner。

[GPMP2 官方代码](https://github.com/borglab/gpmp2) · [arXiv](https://arxiv.org/abs/1707.07383) · [DOI](https://doi.org/10.1177/0278364918790369)

## 今日结论

今天最清晰的趋势不是“所有模块都被一个大模型吞掉”，反而是 **状态、算力、安全和工具能力正在被显式化**。

World SLAM Model 把 persistent state 与 backend refinement 拉进世界模型；ForVis 提醒我们，真实状态估计里 sensor 本身仍可能比算法名字更重要。CollisionSplatting 让视觉地图开始拥有规划接口，说明未来地图会越来越像“可查询的统一世界状态”。

控制侧，Fast-TD-MPC 和 Adaptive RACF 可以放在一起看：一个动态分配 **计算预算**，另一个动态估计 **安全预算**。前者只在值得的时候付规划成本；后者根据真实 residual 扩张或收缩 action margin。

D4orm 展示 GPU 时代另一条路线：过去因为组合爆炸而必须强剪枝的问题，可以重新问——如果一次并行生成 / 修正上千条候选，能否用更简单的统一采样优化解决？

AI Coding 侧同样如此。GPT-6.1 Sol 说明更强模型继续降低单位任务成本；MCP error-message 研究则说明，模型越强，**错误的接口语义也可能被执行得越认真**。Agent 工程不能只升级模型，tool contract 必须同步升级。

> **可靠智能系统的竞争点，越来越不是“模型知道多少”，而是系统能否明确维护世界状态、分配计算预算、量化安全余量，并给 Agent 提供真正可执行的接口。**

## 最值得深入研究或尝试复现的方向

1. **SLAM-style World Memory Sidecar**：保留现有 LIO / VIO，为 world-model memory node 增加稳定 map ID 与 pose revision。
2. **双相机同轨迹 A/B**：复制 ForVis 思路，同一机器人同步录两套传感器，算法完全固定，先测硬件贡献。
3. **3DGS Collision Benchmark**：同一 scene 比较 3DGS direct collision、ESDF 与 mesh/FCL 的吞吐、显存和 false-safe rate。
4. **Selective Planning Router**：现有 MPPI / MPC 不动，先增加 rule-based planner trigger，再与 learned router 比较。
5. **Residual-Calibrated Safety Margin**：在 CBF / action projection 外加滚动 residual quantile，先 shadow mode。
6. **D4orm-D vs MPPI**：固定 4/8/16/32 robot 场景比较 latency、success、minimum separation 与 GPU memory。
7. **MCP Error Contract Lint**：凡错误信息出现 shell / browser / config / wait 指令，就要求 recovery_tool、required_capability、retryable、operation_id。
8. **GPT-6.1 Sol 固定任务回归**：固定 repo、工具和预算，记录每成功任务成本和 tool steps，再决定 router。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [World SLAM Model](https://arxiv.org/abs/2609.32626) · [项目页](https://tsinghua-mars-lab.github.io/WorldSLAMModel/)
- [ForVis](https://arxiv.org/abs/2609.35482)
- [CollisionSplatting](https://arxiv.org/abs/2609.35619)
- [Fast-TD-MPC](https://arxiv.org/abs/2609.32591)
- [Adaptive Safety Filtering / RACF](https://arxiv.org/abs/2609.35415)
- [Denoising Multi-Robot Trajectories](https://arxiv.org/abs/2609.35651) · [D4orm 官方代码](https://github.com/proroklab/d4orm)
- [GPT-6.1 Sol 官方发布](https://openai.com/index/introducing-gpt-6-1-sol/)
- [GPT-6.1 Sol in GitHub Copilot](https://github.blog/changelog/2026-09-29-gpt-6-1-sol-in-github-copilot/)
- [MCP Error Messages Written for Developers Hurt the Most Capable Agents Most](https://arxiv.org/abs/2609.35381) · [代码与数据](https://github.com/WenJing95/tool-error-text)
- [OpenAI Developers plugin](https://developers.openai.com/learn/developers-codex-plugin)
- [OpenAI Agents API Self-hosted sandboxes](https://developers.openai.com/api/docs/guides/agents-api/environments/self-hosted)
- [GPMP2](https://github.com/borglab/gpmp2) · [arXiv](https://arxiv.org/abs/1707.07383) · [DOI](https://doi.org/10.1177/0278364918790369)
