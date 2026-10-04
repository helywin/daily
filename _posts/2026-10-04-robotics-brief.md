---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-04"
date: 2026-10-04 09:00:00 +0800
description: "周末最新批次聚焦长序列三维重建闭环、隐私保护多机器人3DGS视点规划、训练免Diffusion规划、四足多目标控制、多机吊运、人形多接触恢复、轻量WAM与Coding Agent可落地审计。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-04

## 摘要

今天是周日。截至 2026-10-04 早间，arXiv Robotics 与 Software Engineering 的最新常规公开批次仍是 2026-10-02，分别有 107 条和 31 条。周末没有新的常规 arXiv 批次，因此本期继续从最近 7 天范围筛选未覆盖工作，并按规范化标题、arXiv ID、DOI、GitHub 仓库和项目主页与历史覆盖索引强制去重。本期入选论文的 v1 实际提交于 9 月 30 日至 10 月 1 日 UTC，均已超过 24 小时，因此统一标为“时间回补”。

今天 SLAM / 三维重建最值得看的工作是 CLoSeR。它把 loop closure 重新带回 streaming reconstruction foundation model：用全局描述子找回环，构造 loop-conditioned window 估计相对位姿，并利用 backbone 全局尺度一致这一性质，直接在 SE(3) 上联合优化 sequential 与 loop constraints。作者将目标推进到 kilometer-scale reconstruction，并已公开代码。

多机器人地图方面，TRACE 提出协同 next-best-view 不必交换完整 3DGS 地图。它将跨机器人 EIG 耦合压缩成沿射线的 transmittance 与 radiance aggregates，消息大小不随地图规模增长。100 次 Habitat-Sim 决策中，83.3% 的 heading 与集中式方案相差不超过 15°，并达到集中式 EIG 的 97.9%。

规划方向，Training-Free Diffusion Planning with Analytical Local Scores 不再学习全局 trajectory score，而把障碍、平滑、速度、机器人间约束直接写成解析局部 score，让 denoising 只承担迭代优化。论文报告 300+ agents、100+ obstacles 的场景可在 GPU 上 6 秒内求解。

四足控制侧，PROMO 将命令跟踪、稳定性和能耗等冲突目标从固定 reward weight 变成运行时 preference。100 个偏好设置中得到 67 个 Pareto 非支配行为，平均 preference-objective correlation 为 0.843；同一策略 zero-shot 到 Unitree Go2 后，仅改变 preference 就能在不同设置下显著改变能耗、跟踪和姿态稳定性。

AFD-CAMLs 关注多 UAV 缆绳吊运里“轨迹可行但张力分配病态”的问题：全局层在 tension-to-wrench allocation 的 null space 中生成 payload trajectory 与 cable-force reference，局部层联合规划各 UAV，再用 onboard cable-tension estimate 经过 admittance filter 做闭环修正。4 到 10 架 UAV 的仿真和实验都显示更均衡的张力。

人形方向，Reactive Humanoid Multi-Contact Using Learned Stability Models 在线选择手应该扶哪个区域、哪个点。它通过 centroidal dynamics rollout 跨过 pre-impact、impact、post-impact，并用学习得到的 post-impact CoP region 快速评估候选。仿真中 impulse resilience 相对不使用手接触提高 89%，真机 standing push test 的稳定时间相对朴素手扶策略缩短 43%。

SkeleWAM 给出一个反“大视频世界模型”的思路：操作真正需要的未来状态可能不是下一帧像素，而是机器人关节、物体中心和 interaction point 组成的稀疏 3D skeleton。它从 RGB-D 与 proprioception 在线构建 skeleton，训练时联合预测未来 skeleton，部署时直接从当前 skeleton + language 生成动作。LIBERO-Plus 上，57.1M 参数模型整体成功率为 85.9%，项目页还报告真实 ARX R5 五任务平均成功率 89%。

AI Coding 主动态 Groundability, Not Scale Alone 回答“弱模型能否审计强 Coding Agent”。结论是关键不在 reviewer 尺寸，而在有没有可以独立执行的 grounded evidence。结构化但未验证的 evidence 会同时提高 defect catch 与 over-rejection；真正的 execution evidence 才能让较弱 reviewer 稳定做对判断。

近期通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic、Google 与 xAI 的官方公开入口，没有发现 10 月 2–4 日需要新增覆盖的通用旗舰正式发布。近期 GPT-6.1 Sol、Gemini 4 Argon、Claude Sonnet 5.5 与 Grok 4.7 已在前几期覆盖，因此今天不重复旧发布凑数。

最新公开列表：[arXiv Robotics](https://arxiv.org/list/cs.RO/recent) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/recent)

## 1. CLoSeR：给 Streaming Reconstruction Foundation Model 重新装上回环后端

**时间回补：v1 提交于 2026-10-01 15:59 UTC。**

### 为什么重要

Feed-forward 3D reconstruction foundation model 在短窗口里很强，但长序列的微小姿态误差仍会累计。进入数百米、公里级 streaming reconstruction 后，系统依旧需要“发现自己回到旧地方，并用新证据修正过去状态”的机制。CLoSeR 的价值就是把传统 SLAM 最成熟的 loop closure 思想接回 learned reconstruction。

### 算法模块

    streaming reconstruction backbone
            ↓
    global descriptor retrieval
            ↓
    loop-conditioned window
            ↓
    relative pose between looped frames
            ↓
    sequential + loop constraints
            ↓
    joint SE(3) pose optimization

作者观察到所采用的 backbone 会保持 globally consistent scale，因此后端不必为 scale drift 再引入 Sim(3)，可以直接在 SE(3) 上优化。

### 传感器、实时性与鲁棒性

它面向视觉 streaming reconstruction，前提是 backbone 的尺度一致性足够好。如果换成存在明显 scale drift 的单目模型，“只用 SE(3)”未必成立。global descriptor 仍会受到重复建筑、长走廊和外观变化影响，foundation model 并没有消除 perceptual aliasing。

论文重点展示 kilometer-scale 长序列漂移下降，没有给出可直接外推到任意 GPU 的统一 FPS。工程上应分别统计 backbone、descriptor retrieval、loop-window reconstruction 和 global optimization 的延迟。

### 可复现性、风险与工程落地

作者已公开代码。真正风险仍然是错误回环，因此建议保留 descriptor recall → temporal consistency → loop-window relative pose → geometry residual → robust global optimization 的多层验证。

适合学习式 SLAM、DUSt3R / MASt3R 类 reconstruction、长距离视觉建图团队。已经有 learned reconstruction 时，下一步往往不是更大 backbone，而是把累计 drift、loop candidate quality 和 relative-pose consistency 做成正式 telemetry。

[论文](https://arxiv.org/abs/2610.01927) · [代码](https://github.com/MoyangLi00/CLoSeR)

## 2. TRACE：多机器人 3DGS 协同探索可以共享“射线统计”，不共享整张地图

**时间回补：v1 提交于 2026-09-30 23:32 UTC。**

### 为什么重要

多机器人 next-best-view 若要计算团队整体信息增益，最直接的方法是汇总完整地图。但 3DGS splat map 会随环境规模增长，通信成本、隐私和地图外泄都会成为问题。TRACE 追问：为了算一个候选视点的 EIG，是否真的需要拿到别人的每个 Gaussian？

### 算法模块

    local private 3DGS map
            ↓
    candidate rays
            ↓
    per-depth-bin aggregates
       ├─ transmittance in front
       └─ radiance behind
            +
    pose derivatives
            ↓
    compact message exchange
            ↓
    local pooled EIG / SO(3) gradient

每台机器人保留自己的 splats，只交换信息增益计算真正需要的统计量。

### 假设、结果与风险

TRACE 假设各机器人有自己的 3DGS map，并存在公共坐标关系。这里的 privacy 是“不交换完整 splats”，并不等价于密码学隐私。

消息大小不随地图规模增长。100 次 Habitat-Sim NBV 决策中，83.3% 的 heading 与 centralized solution 相差不超过 15°，达到 centralized EIG 的 97.9%。

真实系统还要处理 map alignment error、pose latency、packet loss、stale aggregates 和 dynamic objects。消息应带 map_revision、pose_timestamp 与 candidate_view_id。

### 可复现性与工程落地

当前未给出成熟代码入口。最小复现可以比较 full-map centralized EIG 与 ray aggregate 的决策偏差和网络流量。

适合多 UAV / 多机器人探索、3DGS、带宽受限协作。工程上值得借鉴的是：协同接口不一定以“同步地图”为中心，先问 planner 真正需要哪些 sufficient statistics。

[论文](https://arxiv.org/abs/2610.00822)

## 3. Training-Free Diffusion Planning：Cost 能解析写出来时，不一定还要学一个全局 Score

**时间回补：v1 提交于 2026-10-01 16:15 UTC。**

### 为什么重要

Diffusion planner 的常见代价是训练数据和分布绑定。环境尺寸、障碍数量、agent 数一变，learned global trajectory score 可能需要重新训练。

这项工作把 diffusion 重新解释成 iterative trajectory refinement：真正决定方向的 score 不来自网络，而来自局部解析约束。

### 算法模块

    noisy candidate trajectories
            ↓
    analytical local scores
       ├─ obstacle avoidance
       ├─ smoothness
       ├─ velocity / dynamics constraints
       └─ inter-agent feasibility
            ↓
    denoising / iterative refinement
            ↓
    feasible trajectories

### 动力学假设、实时性与风险

方法依赖任务约束能被分解为局部、可计算 score。长时语义目标、复杂接触和离散逻辑仍可能需要额外层。

论文报告 300+ agents、100+ obstacles 的场景 GPU 求解时间低于 6 秒。它不是 50 Hz 控制器，但对大规模批量轨迹规划很有参考价值。

解析 score 的优势也是风险：漏掉执行器饱和、地图不确定性或硬动力学限制，planner 不会自动补上。建议 hard feasibility 与 soft objective 分离。

### 可复现性与工程落地

当前未发现成熟代码入口。可以固定同一 cost，比较 analytical diffusion、MPPI、CEM 的 GPU time、constraint violation 与规模扩展。

适合多机器人规划、GPU trajectory optimization、MPPI / diffusion planning。引入 learned planner 前，先统计有多少 cost 本来就是已知的；已知结构通常值得保留。

[论文](https://arxiv.org/abs/2610.01959)

## 4. PROMO：四足机器人的“节能 / 跟踪 / 稳定”权衡变成运行时输入

**时间回补：v1 提交于 2026-10-01 07:52 UTC。**

### 为什么重要

四足 RL 的 reward 往往是几十项 weighted sum，训练后这些权重就固化进策略。现场如果更看重续航、精确跟踪或机体稳定，常常只能换策略或重新训练。

PROMO 把这些目标之间的 preference 显式作为 policy input，让同一套 locomotion policy 在部署时连续改变 trade-off。

### 算法模块与假设

    command + robot state
            +
    semantic objective preference
            ↓
    preference-conditioned policy
            ↓
    locomotion action

关键是把 deployment-facing preference 与维持 gait 可行所必需的 embodiment-specific locomotion prior 分离。用户调的是业务权衡，不是随意改变所有 reward term。

### 结果与真机

100 个采样偏好中，67 个行为是 Pareto 非支配解，平均 preference-objective correlation 为 0.843。

同一策略 zero-shot 到 Unitree Go2 后，相对 balanced preference，仅改变偏好可在不同设置下将 specific energy 最多降低 30.4%、位置误差最多降低 38.7%、peak body-attitude deviation 最多降低 59.0%。这些最大值来自不同偏好设置。

### 风险、可复现性与工程落地

运行时 preference 本身是新控制接口，应加 allowed range、rate limit、task preset 与 balanced fallback，不能让上层任意输出极端权衡。

作者声明提供项目页、代码和视频。适合 Unitree Go2、多目标 locomotion、需要同一 gait 支持不同业务模式的团队。相比训练多套 gait，受限 preference interface 更像真正的软件 API。

[论文](https://arxiv.org/abs/2610.01260) · [项目页](https://amrmousa.com/promo/)

## 5. AFD-CAMLs：多机吊运不只要跟轨迹，还要防止某几根缆绳长期吃掉大部分载荷

**时间回补：v1 提交于 2026-10-01 07:01 UTC。**

### 为什么重要

多 UAV 悬索吊运的 payload wrench 往往可由多组 cable tension 实现。当 tension-to-wrench allocation 冗余或接近病态时，payload 轨迹即使几何可行，也可能让少数缆绳张力过大、另一些接近松弛。

### 算法模块

    desired payload motion
            ↓
    global planner explores allocation null space
            ↓
    payload trajectory + cable-force references
            ↓
    centralized local planner for all UAVs
            ↓
    onboard cable-tension estimates
            ↓
    admittance filter
            ↓
    corrected kinematic references

global planner 决定健康的力分配，local planner 决定每架 UAV 怎样运动，admittance layer 用真实 tension 把模型误差闭环回来。

### 动力学假设、结果与风险

系统需要 cable geometry、payload dynamics 和在线 tension estimate。论文在 4 到 10 架 UAV 的仿真和实验中展示，在 hover 与敏捷运动下都获得更均衡的 tension distribution，同时不明显牺牲 agility 或 payload tracking。

建议显式监控 cable_tension、tension_margin、allocation_condition_number、slack_risk 和 payload tracking error。很多故障不是 controller 突然坏了，而是当前几何构型已让力分配接近不可控。

### 可复现性与工程落地

当前未提供成熟公开代码入口。适合多无人机吊运、冗余执行器协同。高层规划不应只看位姿可达，把 force margin 和 allocation conditioning 带进 planner，通常比低层饱和后再补救更稳。

[论文](https://arxiv.org/abs/2610.01185)

## 6. Reactive Humanoid Multi-Contact：人形被推时，在线决定“手应该扶哪里”

**时间回补：v1 提交于 2026-09-30 23:33 UTC。**

### 为什么重要

足底支撑不足时，人类会自然扶墙、撑桌、抓扶手。难点不是“允许用手”，而是受扰后快速从周边很多可达表面中选出真正能恢复稳定的接触。

### 算法模块

    disturbance / low-stability state
            ↓
    sample reachable contact candidates
            ↓
    centroidal dynamics rollout
    pre-impact → impact → post-impact
            ↓
    learned post-impact CoP region
            ↓
    score CoP control authority
            ↓
    select bracing region → select contact point

网络只替代昂贵的 post-impact stability evaluation，而不是替代整个物理规划结构。

### 动力学假设与结果

方法基于 centroidal dynamics 和接触后的 CoP control authority，要求环境表面可达、能承受支撑，并且 friction / contact geometry 没有严重误判。

仿真中 impulse resilience 相对不用手提高 89%，相对“最近可达区域”策略提高 17%。真机 standing push test 中，平均 stabilization time 相对朴素 hand placement 缩短 43%；walking 场景相对不用手 baseline 缩短 18%。

### 风险、可复现性与工程落地

真正产品化要分开 geometric reachability、structural supportability、friction confidence、semantic permission 与 predicted stability gain。玻璃、移动家具和人体即使几何可达，也不应自动成为支撑候选。

当前无成熟代码入口。适合人形、腿式操作、推搡恢复、多接触规划。可以先用离线优化生成 contact stability label，再训练轻量 surrogate 做实时 shortlist。

[论文](https://arxiv.org/abs/2610.00823)

## 7. SkeleWAM：世界模型不一定预测视频，稀疏 3D Skeleton 可能更接近控制需要的状态

**时间回补：v1 提交于 2026-10-01 17:35 UTC。**

### 为什么重要

许多 World Action Model 预测未来视频或高维视觉 latent，会把纹理、光照和背景等控制无关信息带进世界模型。SkeleWAM 把 manipulation scene 表示成机器人关节、对象中心和 interaction point 的稀疏 3D skeleton。

### 算法模块

    RGB-D + proprioception
            ↓
    sparse 3D skeleton
            ↓
    joint training:
       action generation
       + future skeleton prediction
            ↓
    inference keeps action branch
            ↓
    Medoid Action Consensus
            ↓
    execute prefix and replan

future-skeleton branch 用于训练监督，部署时无需生成未来视频。

### 传感器、结果与风险

输入是 RGB-D + proprioception，前提是能稳定抽取对象 landmarks / interaction points，并从 forward kinematics 获得机器人关节几何。

LIBERO-Plus 10,030 个 variant 上整体成功率 85.9%，模型 57.1M 参数；future-skeleton supervision 将 success 从 80.1% 提升到 85.9%。项目页报告真实 ARX R5 五项任务平均成功率 89%。

边界也很明确：layout change 成功率 66.6%，说明稀疏几何能过滤外观噪声，却不会自动解决大尺度布局泛化。perception error 也会直接变成控制 state error，因此 skeleton 中每个 landmark 应有 confidence、age 和 association。

### 可复现性与工程落地

项目页公开详细方法和实验，当前未见完整代码仓库。适合 WAM / VLA、RGB-D 桌面操作与边缘部署。即使不复现全模型，也可先比较 pixel latent 与 object-centric 3D keypoints 哪个更适合作为当前 policy state。

[论文](https://arxiv.org/abs/2610.02120) · [项目页](https://skelewam-project.github.io/)

## 8. Groundability：弱 Reviewer 也能审强 Agent，前提是证据能独立执行验证

**时间回补：v1 提交于 2026-10-01 04:10 UTC。**

### 突破性工程价值

Coding Agent 常给出“看起来合理”的 patch 和自信总结，但遗漏要求。单纯再叫另一个 LLM 看 diff，容易被相同的表面合理性骗过。论文认为 review 质量关键不只是 reviewer scale，而是争议能不能被独立检查，也就是 groundability。

### 实验结构与结果

作者分析 411 条 execution-labeled agent traces 和 101 个 controlled cases，并区分 agent testimony、structured but unchecked evidence、grounded evidence。

在 154 条 GPT-5.4 traces 上，结构化但未经检查的 evidence 同时提高 defect catch 和 over-rejection。提供官方 execution evidence 作为上限后，固定 evidence format 的 held-out 测试中，6 个 reviewer 有 5 个同时改善两项指标，2 个全部判对。

现实部署没有 official tests，因此作者构造 frozen cascade：

    reject empty patch
    → reject patch-caused static errors
    → generated tests must first fail on base repo
    → unresolved cases enter reviewer

在 held-out GPT-5.4 / Gemini traces 上，coverage 分别为 0.89 / 0.86，catch 为 0.76 / 0.80，但 over-rejection 仍为 0.66 / 0.67。真正瓶颈是怎样自动产生可靠 decisive checks。

### 真实研发价值与风险

工程结论不是“换小 reviewer 省钱”，而是 build result 应高于 agent summary、failing-on-base regression 应高于 generated explanation、patch-caused static error 应高于 vague code smell。

生成测试必须先在未修改仓库失败，否则 Agent 容易生成 patch 前后都通过的自证测试。静态检查也只应把 patch 新引入的问题归因给当前 patch。

### 可复现性与工程落地

论文未提供成熟代码入口，但 pipeline 很适合内部 Agent CI。适合 Codex / Claude Code 自动 PR、AI Code Review、多模型 router。

把 completion receipt 从“我完成了 A/B/C”改成“每项需求对应哪个可执行证据”。Verifier 第一目标不是读懂整条推理轨迹，而是确认外部行为真的发生。

[论文](https://arxiv.org/abs/2610.01023)

## AI Coding 实战技巧精选

### 技巧 1｜用 Claude Code Mod 在高风险 Bash 执行前显示 Blast Radius

- **来源**：Anthropic claude.dev，2026-10-01：[Claude Code Mods](https://claude.dev/mods/) · [Getting started with Claude Code mods](https://claude.dev/blog/getting-started-with-claude-code-mods/)。
- **一句话结论**：对于高影响文件删除、历史重写、发布或数据库迁移类 shell 操作，不要只依赖 Prompt 提醒。用 tool.call hook 在执行前暂停命令，先展示影响范围，再由人选择继续或取消。
- **具体怎么做**：
  1. 使用 Claude Code 2.1.287 或更新版本；Mods 默认启用。
  2. 在插件中通过 hooks/hooks.json 加载 JS/TS module；模块导出 register(on, options)。
  3. 对 Bash 注册 tool.call hook；普通命令直接放行，高风险命令计算影响范围并显示确认 UI。
  4. 可参考官方 Blast Radius 示例；自定义时以 Claude Code 写入 .claude-plugin/types/ 的当前版本类型声明为准。
- **适合什么场景**：Claude Code、本地大仓库、数据库迁移、自动 Git 操作、给 Agent 较高 shell 权限的环境。
- **注意**：Mod 与 Claude Code 在同一台机器上运行，只安装可信来源。它不替代 OS sandbox、protected branch 或数据库权限。

### 技巧 2｜把团队 Skills 和 MCP 配置封装成 Codex Plugin，而不是每个 Session 手工接工具

- **来源**：OpenAI Developers 官方文档：[Plugins](https://developers.openai.com/api/docs/guides/agents-api/tools/plugins)。
- **一句话结论**：一套 Coding Agent 工作流若需要固定 Skills + Docs / Jira / 内部 MCP，不要在每个项目手工复制 Prompt 和 MCP JSON；把它们放进同一个 .codex-plugin 包并版本化。
- **具体怎么做**：
  1. 建立插件目录，包含 .codex-plugin/plugin.json、.mcp.json 和 skills/docs-search/SKILL.md。
  2. 在 plugin.json 中分别声明 skills 与 mcpServers；路径从插件根开始、使用 ./，且不能通过 .. 跳出插件目录。
  3. 无凭据 Skill / MCP 可统一打包；秘密凭据继续由运行环境注入，不写进插件仓库。
  4. Skill / MCP contract 更新时升级插件版本，让不同项目能复现自己使用的工具包版本。
- **适合什么场景**：Codex、Agents API、自研 Coding Agent、多仓库共享文档检索 / CI / issue workflow。
- **注意**：Plugin 是打包边界，不是安全边界。MCP 仍需单独做网络、凭据和写权限最小化；插件升级也应跑 regression。

## 经典论文回顾

### Capture Point：把“被推后还能不能救回来”变成一个可计算的落脚区域

Jerry Pratt、John Carff、Sergey Drakunov 与 Ambarish Goswami 的 **Capture Point: A Step toward Humanoid Push Recovery** 发表于 2006 IEEE-RAS International Conference on Humanoid Robots。它把 humanoid push recovery 从经验策略推进为“何时必须迈步、一步要落到哪里”的可计算问题，后来成为 capturability、DCM、步态恢复和现代 humanoid balance control 的重要基础。

### 核心问题与数学思想

传统静态指标只告诉你当前 ZMP / CoM 是否还在支撑范围附近，却不直接回答：现在还能不迈步停住吗？如果必须迈步，脚至少要落到哪里？如果一步已经不够，什么时候应该承认需要多步恢复？

论文从简化倒立摆模型出发，并引入 flywheel 表示机体角动量。给定当前 CoM 状态与系统动力学，可以求出 capture region：脚落在该区域内，机器人就有机会消散当前运动并最终停住。

如果 capture point / region 与当前 base of support 有交集，机器人不一定需要迈步；没有交集就必须改变支撑位置；capture region 完全落在 swing foot 可达域外时，一步恢复也已经不可行。

### 传感器 / 动力学假设

经典推导依赖 Linear Inverted Pendulum 等简化动力学及 flywheel 对角动量的近似。它不是完整 whole-body dynamics，也不直接处理复杂地形、接触摩擦和手部支撑，因此更适合作为快速 recoverability 指标。

### 当年为何重要、今天仍在使用什么

它清楚给出 when to step、where to step、when one step is no longer enough 三个 push recovery 核心问题，并展示可控角动量会扩大 capture region。

现代 humanoid control 已大量使用 MPC、whole-body QP、RL 和 learned viability model，但核心思想没有过时：stability 是未来可达性问题，不只是当前静态 margin。

今天的 Reactive Humanoid Multi-Contact 可以视为自然扩展：经典 Capture Point 问“脚落哪里”，新工作进一步问“脚已不够时，手在哪里建立新接触才能重新获得 CoP control authority”。

### 后续扩展、可复现性与工程重读

后续 capturability 研究扩展到 N-step、有限步长和时间、角动量、非平地与更完整动力学；DCM 也把相关思想用于在线步态控制。learned viability predictor 能处理更复杂模型，但 certificate 和可解释性更弱。

最小复现实验甚至不需要 humanoid simulator：实现 LIPM + flywheel，画出不同 CoM velocity、支撑区和角动量限制下的 capture region，再比较无迈步 / 单步 / 多步恢复边界。

对于人形或轮足狗，真正值得借鉴的是把“安全恢复能力”做成连续 margin：current support margin、one-step recoverability、reachable support set、contact alternatives、abort / fall fallback。让上层动作在进入不可恢复区域前就降级。

[Honda Research Institute 页面](https://usa.honda-ri.com/w/capture-point-a-step-toward-humanoid-push-recovery) · [IEEE DOI](https://doi.org/10.1109/ICHR.2006.321385)

## 今日结论

今天八项工作共同主题很明确：**不要把系统里已有的结构丢掉，再期待一个更大的网络重新学回来。**

CLoSeR 的 streaming foundation model 最终仍需要经典 loop closure；Training-Free Diffusion Planning 保留解析 obstacle / smoothness / multi-agent constraints；AFD-CAMLs 把力分配 null-space structure 写进规划；人形多接触恢复也只让 learned model 加速昂贵的稳定性评估，而不是端到端替代物理结构。

TRACE 与 SkeleWAM 从“信息应该传多少”给出类似答案。多机器人协同不必传完整 3DGS，只传 EIG 需要的射线统计；世界模型也不必预测完整视频，只预测控制需要的稀疏几何状态。对边缘机器人而言，“只保留 sufficient state”往往比单纯压模型更有效。

PROMO 展示了一个值得产品化的控制接口：将多目标 trade-off 从训练配置变成运行时 preference。底层策略保证步态可行，上层任务动态表达“更省电”或“更重视跟踪”，比任务层直接调几十个 reward coefficient 更接近稳定 API。

Groundability 对 Coding Agent 的结论与机器人系统一致：模型自己的叙述不是证据。可靠 reviewer 依赖可以独立执行的检查，正如机器人安全依赖真实张力、CoP margin 和几何残差，而不是 policy 的自信度。

两条实战技巧也延续同一思路：Claude Code Mod 将高风险命令的 blast radius 放到执行前可视化；Codex Plugin 将 Skill 与 MCP contract 做成可版本化包。过去散落在 Prompt 里的“习惯”，应该逐步变成正式软件组件。

如果把今天整期压缩成一句话：

> **机器人与 Coding Agent 越强，越应该保留几何、动力学、约束、验证和权限这些可计算结构，只让学习模型负责真正难以显式建模的部分。**

## 最值得深入研究或尝试复现的方向

1. **给 Learned Reconstruction 补回环。** 对现有 DUSt3R / MASt3R / 视频重建管线记录长距离 drift，增加 global retrieval + loop-window relative pose + SE(3) graph，先测 500 m 以上序列。
2. **多机器人共享决策统计而非完整地图。** 对 3DGS / voxel exploration 统计 NBV 真正需要的信息，比较 full-map sync 与 aggregate protocol 的带宽、延迟和决策损失。
3. **Analytical-Score Diffusion vs MPPI。** 固定 cost，比较 analytical diffusion、MPPI、CEM 的 GPU time、sample efficiency、constraint violation 与扩展到 100+ agent 的趋势。
4. **Go2 Preference API。** 定义 energy / tracking / stability 三个可观测指标和受限 preference preset，再决定是否训练 PROMO 类统一策略。
5. **Cable / Actuator Allocation Health。** 将 allocation condition number、force margin 和 saturation risk 提升成 planner telemetry。
6. **人形 / 轮足 Recoverability Margin。** 从 Capture Point 解析基线开始，再增加 hand contact candidate 与 learned stability surrogate。
7. **SkeleWAM 式任务充分状态。** 对当前 VLA / WAM 做 object center + interaction point + robot joint 稀疏输入 baseline，确认是否真的需要完整 visual latent。
8. **Coding Agent Evidence Gate。** 每条自动 PR 至少绑定一个会在 base revision 失败、在 patch revision 通过的 behavioral test；Reviewer 优先审证据而不是 completion summary。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [CLoSeR](https://arxiv.org/abs/2610.01927) · [代码](https://github.com/MoyangLi00/CLoSeR)
- [TRACE](https://arxiv.org/abs/2610.00822)
- [Training-Free Diffusion Planning with Analytical Local Scores](https://arxiv.org/abs/2610.01959)
- [PROMO](https://arxiv.org/abs/2610.01260) · [项目页](https://amrmousa.com/promo/)
- [AFD-CAMLs](https://arxiv.org/abs/2610.01185)
- [Reactive Humanoid Multi-Contact Using Learned Stability Models](https://arxiv.org/abs/2610.00823)
- [SkeleWAM](https://arxiv.org/abs/2610.02120) · [项目页](https://skelewam-project.github.io/)
- [Groundability, Not Scale Alone](https://arxiv.org/abs/2610.01023)
- [Claude Code Mods](https://claude.dev/mods/) · [Mods 入门](https://claude.dev/blog/getting-started-with-claude-code-mods/)
- [OpenAI Plugins 指南](https://developers.openai.com/api/docs/guides/agents-api/tools/plugins)
- [Capture Point - Honda Research Institute](https://usa.honda-ri.com/w/capture-point-a-step-toward-humanoid-push-recovery)
- [Capture Point DOI](https://doi.org/10.1109/ICHR.2006.321385)
