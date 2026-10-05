---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-05"
date: 2026-10-05 09:00:00 +0800
description: "周末最新批次聚焦人形测试时奖励程序演化、机器人基础模型单步动作生成、显式概念记忆、VLA全身安全、多机安全路径跟随、VLA推理可行动性，以及Coding Agent模型-框架匹配与Harness自动课程优化。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-10-05

## 摘要

今天是周一。截至 2026-10-05 早间，arXiv Robotics 与 Software Engineering 最新常规公开批次仍为 2026-10-02；Robotics 该批次共 107 条。周末没有新的常规 arXiv 批次，因此本期严格从最近 7 天窗口继续筛选此前未覆盖的高价值工作，并与已验证的 2026-10-04 覆盖索引一起按规范化标题、arXiv ID、DOI、GitHub 仓库与项目页强制去重。

经过去重后，周末批次里没有一条新的 SLAM 工作能比 10 月 4 日已经覆盖的 CLoSeR、TRACE 等工作更值得重复报道，因此今天不为了维持栏目比例硬塞重复 SLAM。主动态重点转向控制、机器人基础模型、VLA runtime 与 AI Coding harness。

今天机器人控制最值得看的工作是 InterEvolve。它不在新任务出现时重新训练 humanoid controller，而是把任务写成可执行的 staged reward program：大模型修改程序结构，数值优化器调常数，每个候选都在并行仿真里验证，再把通过验证的程序加入 skill library。作者的核心思路可以概括成一句话：evolve the task, not the controller。最终演化出的技能可从机载第一视角感知直接运行在 Unitree G1 真机上。

机器人基础模型推理效率方面，Kinematic MeanFlow 针对多步 flow-matching action head 的延迟，分析出 robotic foundation model 的 velocity field 在去噪后段存在局部加速度突增和样本幅值分散问题，再通过中间点将时间导数拆成两个子区间项，实现真正的一步动作生成。GR00T-N1.6 的 action-head latency 在 L40 与 Jetson Orin 上下降 67.5%–74.4%，端到端延迟下降 30.3%–54.9%。

长期机器人记忆方面，ECoMEM 不再把历史全部塞进更长 context，也不指望 action supervision 自己学会“该记住什么”。它把 memory maintenance 和 action learning 分离：Writer 根据证据更新 Entity/Spatial、State/Relation、Event/Progress、Temporal/Procedure 等显式概念记录，Reader 再把这些记录编码成 VLA memory token。16 个 RoboMME 任务中领先 15 项，两个新真机任务中达到 86.1% 成功率，而无记忆 VLA 只有 8.6%。

VLA 安全方面，WBAG 从“只保护末端”推进到“保护整机和抓在手上的物体”。系统显式建模 articulated whole-body 和 grasp-dependent attached geometry，将随抓取状态变化的几何转换成可微 CBF 约束，在原生 6D operational-space action 上做最小修正。SafeLIBERO 上 aggregate Scene Safety 为 97.38%，Safe Success 为 59.38%。

多无人机控制方面，Decentralized Safe Path Following 给出了一个非常清楚的安全分层原则：发生冲突时只放松沿路径速度，不放松路径本身和 heading。控制器将 transverse feedback linearization 写成带 4 个等式约束的 QP，在满足论文假设和可接受初始条件时，可证明多机收敛到指定路径、避免碰撞并避开姿态奇异。项目页还给出了 400 Hz 控制、非平面交叉路径和毫米级收敛后路径误差的实验。

VLA 推理监控方面，When Reasoning Helps Action 很重要的一点不是“CoT 可以被纠正”，而是它证明了“推理更正确”并不自动意味着“机器人表现更好”。TRUST 可以把 Alpamayo 1.5 的推理正确率从 75.9% 提升到 90.0%，并降低困难驾驶子集的碰撞；但在 DeepThinkVLA 上，虽然 grasp-state 和 action-choice reasoning 都显著变准，LIBERO-Plus 闭环表现却基本不变。部署 VLA 时，必须把 correctability 和 actionability 分开验证。

AI Coding 主动态有两项值得放在一起看。Finding the Right Fit 测试 66 个 model-harness configuration，发现同一个模型换 harness 后排名可以直接翻转；Terminal-Bench 4 中 Claude 在 OpenHands 里领先 GPT 7.94 分，却在 PI 中落后 30.16 分。ActiveSaddler 则继续向前一步：不仅自动优化 harness 的 prompt、tool interface 和 control logic，还用非平稳 bandit 自动决定“下一批应该训练哪些失败场景”，在相同 rollout budget 下将 GAIA2 Pass@1 提高 4.4 个百分点、Terminal-Bench 2.0 提高 7.5 个百分点。

近期通用旗舰模型方面，本轮重新核验 OpenAI、Anthropic、Google 与 xAI 的官方公开入口，没有发现 10 月 3–5 日新的通用旗舰正式发布。近期 GPT-6.1 Sol、Gemini 4 Argon、Claude Sonnet 5.5 与 Grok 4.7 已在前几期覆盖，因此今天不重复旧发布。

## 1. InterEvolve：新任务来了，不重新训练人形控制器，而是演化 Reward Program

**时间回补：v1 提交于 2026-10-01 17:59 UTC。**

### 为什么重要

人形 loco-manipulation 的现实问题不是“训练一次就覆盖所有任务”，而是现场总会出现训练集之外的新物体、新接触顺序和新任务组合。如果每次任务变化都重新做 RL 或 imitation learning，部署周期会被训练、调 reward 和 sim-to-real 重新验证拖得很长。

InterEvolve 的思路是固定一个已经具备较宽运动能力的控制基础模型，把变化压缩到控制器上方的任务接口：reward program。

任务不是一句自然语言直接进入低层策略，而是被表示为多个阶段的 reward、完成条件和可调常数。LLM 只修改这个程序的结构，数值优化器负责调连续参数，而每个候选程序必须经过并行仿真验证。

### 算法模块

    新任务与场景
        ↓
    staged reward program
        ↓
    LLM 修改程序结构
        +
    numerical optimizer 调常数
        ↓
    object-aware FB behavioral foundation model
        ↓
    parallel simulation verification
        ↓
    通过验证的 reward program
        ↓
    skill library
        ↓
    Unitree G1 真机执行

其中 object-aware forward-backward behavioral foundation model 在 frozen body prior 上增加 object residual，使针对身体或物体的新 reward 可以直接诱导出已有运动能力的重新组合。

### 动力学假设、实时性与鲁棒性

这条路线假设 frozen controller 本身已经拥有足够丰富的运动先验，新任务更多是“怎样组合已有能力”，而不是要求机器人突然掌握完全不存在的底层运动技能。

测试时演化不是高频控制回路。真正高频执行仍由冻结 controller 负责；LLM 和 numerical optimizer 运行在更慢的任务适配层。

最大的风险是 reward hacking：reward program 形式上满足 verifier，但产生工程上不希望的取巧动作。因此 verifier 必须独立于 LLM，并且 reward program 最好限制在受控 DSL，而不是允许任意代码直接访问机器人执行接口。

### 可复现性

作者已公开项目页，展示 task evolution、simulation verification 与 Unitree G1 真机案例。对已有 RL locomotion / humanoid controller 的团队，最值得复现的是“控制器冻结 + 程序化任务目标 + 固定 verifier”这一系统边界，而不是先重做完整 behavioral foundation model。

### 适合谁关注

Unitree G1、人形 loco-manipulation、已有强底层策略但现场任务不断变化的团队，以及希望让 LLM 参与控制但不让它直接生成关节动作的系统。

### 工程落地启发

可以把机器人任务接口明确拆成：

    controller
    → 冻结、经过大量真机验证

    task program
    → 可修改、版本化、可回滚

    verifier
    → 独立判断完成、安全和违规

这样 Agent 真正演化的是“任务程序”，而不是在现场悄悄改变底层控制器权重。

[论文](https://arxiv.org/abs/2610.02196) · [项目页](https://sirui-xu.github.io/InterEvolve/)

## 2. Kinematic MeanFlow：把机器人 Flow-Matching Action Head 压到一步生成

**时间回补：v1 提交于 2026-10-01 00:31 UTC。**

### 为什么重要

许多 VLA / robotic foundation model 使用 flow matching 或 diffusion action head。视觉语言 backbone 即使已经足够快，action expert 仍可能因为 8、16 甚至更多 denoising step 成为闭环延迟瓶颈。

直接套普通 MeanFlow 做一步生成又会出现性能崩塌。Kinematic MeanFlow 的价值在于，它不是简单蒸馏“多步变一步”，而是先分析机器人 action velocity field 为什么不适合普通 MeanFlow。

### 关键发现与算法

作者观察到两种特殊动力学：

1. local acceleration 在去噪早期比较稳定，但接近结束时突然增大；
2. 不同样本的 acceleration magnitude spread 会随着 denoising 推进明显变宽。

K-MF 使用一个中间点，将 MeanFlow 里的时间导数拆成两个子区间项，使两部分分别拟合早期与后期 dynamics，降低后段误差被一步积分放大的问题。

    多步 flow-matching teacher
        ↓
    分析 velocity-field kinematics
        ↓
    中间点拆分时间导数
        ↓
    early-stage term + late-stage term
        ↓
    one-step action generation

### 实时性

在 GR00T-N1.6 上，作者报告：

- action-head latency 在 L40 与 Jetson Orin、eager / compiled mode 下下降 67.5%–74.4%；
- end-to-end latency 下降 30.3%–54.9%。

这类数字比只报告 FLOPs 更有工程意义，因为真正决定机器人控制频率的是完整 observation→action wall-clock。

### 鲁棒性与工程风险

一步生成意味着错误没有后续迭代修正机会。部署时不能只比平均任务成功率，还要统计：

    P50 / P95 inference latency
    action jerk
    saturation rate
    closed-loop recovery
    OOD scene failure
    safety-filter intervention

此外，论文标注的代码地址目前仍未能正常访问，因此当前可复现性要保守评价，不能把“作者说将开放”当成已经开源。

### 适合谁关注

GR00T、π 系列、flow-matching VLA、Jetson Orin 边缘部署，以及控制频率被 action denoising 拖住的团队。

### 工程落地启发

先 profile 再优化。若 60% 延迟其实在视觉 backbone，一步 action head 收益会有限；只有当 action generation 已经是主要瓶颈时，K-MF 类方法才真正值钱。

[论文](https://arxiv.org/abs/2610.00864)

## 3. ECoMEM：机器人记忆应该是可更新的概念记录，而不是无限变长的 Context

**时间回补：v1 提交于 2026-09-30 22:54 UTC。**

### 为什么重要

长任务中，机器人经常必须利用当前视野里已经不存在的信息：

- 刚才把工具放在了哪个抽屉；
- 人类之前演示的是哪个顺序；
- 当前多阶段任务已经完成到哪一步；
- 某个对象之前和另一个对象是什么关系。

仅仅延长 observation history 会把大量无关图像和动作一起塞进 context；依靠 action supervision 学 implicit memory，则没有直接告诉模型“什么事实应该长期保存、什么时候该更新或删除”。

ECoMEM 因此把 memory maintenance 和 action learning 明确分开。

### 算法模块

    当前观察 + 过去证据
            ↓
    evidence-based Writer
            ↓
    显式 Concept Records
       ├─ Entity / Spatial
       ├─ State / Relation
       ├─ Event / Progress
       └─ Temporal / Procedure
            ↓
    learned Reader
            ↓
    memory tokens
            ↓
    VLA action policy

Writer 管理事实，Reader 决定当前动作需要怎样读取这些事实。

### 结果

论文报告：

- 16 个 RoboMME memory-dependent task 中领先 15 项；
- 两个新真机任务中，同一 memory library 可直接迁移或只增加一个新 concept；
- pooled real-robot success 为 86.1%，no-memory VLA 为 8.6%。

项目页还展示 concept record 的更新过程，说明 memory 不只是静态 retrieval，而是可以随新证据改变状态。

### 鲁棒性与工程风险

显式 memory 最大风险不是“忘记”，而是“错误事实长期存活”。

产品接口至少应该让每条记录保存：

    concept_id
    evidence_source
    confidence
    created_at
    last_verified
    invalidation_condition
    supersedes

如果新的视觉证据和旧记忆冲突，应该触发 revision，而不是把两个互相矛盾的事实都塞给 VLA。

### 可复现性

项目页已经公开，代码当前仍标记 coming soon。即使不复现模型，也可以先在机器人 Agent 上实现结构化 concept store，再比较“无限历史上下文”和“明确状态记录”在长任务中的 token、错误累积和恢复能力。

### 适合谁关注

长时机器人 Agent、VLA、巡检操作、需要记任务进度和对象状态的系统。

### 工程落地启发

机器人 memory 最好像数据库，而不是聊天记录。真正应该持久化的是可以被验证、修改和失效的事实，而不是整段原始历史。

[论文](https://arxiv.org/abs/2610.00801) · [项目页](https://ecomem.github.io/)

## 4. WBAG：VLA Safety 不能只包住 TCP，还要保护前臂和抓在手里的物体

**时间回补：v1 提交于 2026-10-01 05:26 UTC。**

### 为什么重要

很多 inference-time VLA safety method 把机器人近似成末端附近的点或球。真实操作里，最先撞到障碍的却可能是 elbow、forearm、wrist，或者刚刚抓起的长物体。

尤其是 grasp 发生后，机器人的有效碰撞几何已经发生变化。如果 safety shield 不知道“手里多了一根杆”，它即使保证夹爪本身安全，也可能让杆子扫到环境。

### 算法模块

    VLA native 6D operational-space action
            ↓
    whole-body articulated geometry
            +
    grasp-dependent attached-object geometry
            ↓
    grasp-conditioned safe set
            ↓
    differentiable CBF constraints
            ↓
    minimal action correction
            ↓
    safe operational-space action

关键是 protected geometry 会随着 grasp state 动态更新。

### 结果

在 SafeLIBERO 上，作者报告：

- aggregate Scene Safety：97.38%；
- Safe Success：59.38%；
- 在论文评估的方法里取得最佳整体安全与安全任务成功表现。

### 动力学假设与工程风险

CBF 约束的可信度依赖 robot geometry、attached-object geometry、环境感知和动作模型。

最危险的一类错误是“抓取状态已经变化，但 collision model 还没更新”。因此产品里最好让 grasp event、object pose、geometry revision 与 safety constraint 更新成为原子流程。

建议记录：

    protected_link_set
    attached_object_id
    geometry_revision
    minimum_distance
    barrier_margin
    action_correction_norm

### 可复现性

当前没有稳定的官方代码入口，因此更适合作为系统设计参考。对于已有 MoveIt / Pinocchio / FCL 几何模型的团队，先做 whole-body + attached-object collision shield，就已经能验证核心收益。

### 适合谁关注

VLA 操作、桌面机械臂、人机共域、长物体搬运，以及已有 VLA 不想重新训练但希望增加运行时安全层的团队。

### 工程落地启发

安全层的几何对象应该和 planner 使用同一套 scene graph / attached-object 状态。否则“规划器知道手里抓了东西，安全过滤器不知道”会形成非常隐蔽的接口漏洞。

[论文](https://arxiv.org/abs/2610.01083)

## 5. 多无人机 Safe Path Following：冲突时只放慢，不偏离预定路径

**时间回补：v1 提交于 2026-09-20 23:12 UTC。**

### 为什么重要

多机在走廊、固定空域、检查线或轨道附近运行时，路径本身往往就是安全边界。常见 nominal controller + safety filter 在发生冲突时会修改整个 velocity vector，虽然避免了碰撞，却可能把飞机推离允许航路。

这篇工作把“什么可以牺牲、什么不能牺牲”写得非常明确：

> 只放松 along-path speed；path adherence 和 heading 保持硬约束。

### 算法模块

作者将 transverse feedback linearization 写成 constrained QP，并使用四个等式约束：

    2 × 路径收敛 / 严格跟随
    1 × desired speed
    1 × heading

安全冲突发生时，QP 允许调整沿路径速度，而路径和 heading 等式保持不动。

### 理论保证与实时性

在论文假设和 admissible initial conditions 下，作者证明：

- 所有 agent 收敛并保持在指定路径上；
- 避免相互碰撞；
- 避免 attitude singularity。

项目页给出的实验包括：

- 400 Hz controller；
- 四架 quadrotor 的非平面交叉圆轨迹；
- 两机 sinusoid crossing，保持约 0.8 m separation；
- 收敛后的 worst path error 约 0.5 mm；
- heading error 小于 1e-3 degree；
- QP equality residual 约 1.1e-13，未出现 feasibility-test failure。

### 鲁棒性与工程风险

理论保证总是相对于模型、感知和通信假设成立。真实系统还需要考虑：

    state-estimation latency
    clock skew
    packet loss
    actuator saturation
    wind disturbance

尤其是如果其他飞机的位置已经滞后，QP 可能在“数学上安全的旧世界状态”上求解。

### 可复现性

作者提供项目页、代码和额外结果，是本期控制项目里可复现性较好的一项。

### 适合谁关注

多 UAV 编队、固定航路交叉、仓库空中物流、希望有明确安全保证又不能让安全层随意偏离路径的系统。

### 工程落地启发

这是一个很通用的 safety-filter 设计原则：

    hard constraints
    → 绝不能破坏的几何 / 法规 / 接触要求

    soft performance
    → 速度、进度、效率

安全层应该优先牺牲性能，而不是牺牲任务的物理边界。

[论文](https://arxiv.org/abs/2610.00208) · [项目页](https://gradslab.github.io/safe_multiquad_pf/)

## 6. When Reasoning Helps Action：CoT 变正确，不代表机器人真的会做得更对

**时间回补：v1 提交于 2026-09-30 19:04 UTC。**

### 为什么重要

Reasoning-enabled VLA 开始输出可读 CoT，这看起来给 safety monitor 提供了一个诱人的接口：

    reasoning 有问题
    → 检测出来
    → 修正 reasoning
    → 动作就会更安全

但最后一步并不天然成立。

这篇论文专门把这件事拆成两个不同指标：

- correctability：错误推理能否在生成过程中被发现并改正；
- actionability：推理修正以后，机器人行为是否真的按预期改变。

### TRUST

作者训练 Token-level Reward for Utility-Steered Chain-of-Thought（TRUST），从 partial reasoning prefix 预测最终 reasoning 是否正确，再对冻结 VLA 的推理生成进行选择性 steering。

它并不直接修改 VLA 权重，而是在 inference time 影响 reasoning trajectory。

### 结果

Alpamayo 1.5：

- reasoning correctness：75.9% → 90.0%；
- monitor correctness：88.9%；
- 困难 AlpaSim 子集 collision rate 相对 unsteered 降低 30.4%；
- maximum trajectory error 降低 11.5%；
- 优于 compute-matched Best-of-4。

DeepThinkVLA：

- grasp-state correctness：69.3% → 90.2%；
- action-choice correctness：68.8% → 85.9%；
- 但 LIBERO-Plus closed-loop task performance 基本没有明显提升。

### 工程风险

这个结果非常重要：**CoT 不是控制系统的 safety certificate。**

一个 reasoning monitor 可能成功让文本解释变得更正确，但 action expert 对这些 token 不敏感，或者视觉 / 动力学瓶颈根本不在 reasoning。

因此部署 CoT steering 时至少要同时测：

    reasoning correctness
    action delta
    trajectory delta
    task success
    safety event rate

如果只有前两个指标变好，不应该声称机器人更安全。

### 可复现性与适合谁关注

目前论文是研究性方案，适合 reasoning VLA、自动驾驶 VLA、希望把语言推理接入 runtime monitoring 的团队。

### 工程落地启发

在机器人里，任何“中间解释更合理”的改进都必须最后落到可执行行为指标。对于 safety，真正的最终证据仍然是 geometry、constraint、trajectory 和实际闭环结果。

[论文](https://arxiv.org/abs/2610.00601)

## 7. Finding the Right Fit：Coding Agent 选型不是 Model 排行榜，而是 Model × Harness × Task

**时间回补：v1 提交于 2026-10-01 01:49 UTC。**

### 突破性工程价值

企业选 Coding Agent 时经常先问“哪个模型最强”。但真正执行任务的不是模型单体，而是：

    model
    + prompt scaffold
    + tool schema
    + retry strategy
    + failure feedback
    + context management

也就是完整 harness。

Finding the Right Fit 系统测试了 66 个 configuration：

- 4 个可配置 harness：OpenHands、DeepSeek Harness、PI、openJiuwen；
- 5 个模型；
- TUA-Bench、ALE-CLI、Terminal-Bench 4；
- 另外加入 native Codex-GPT 与 Claude Code-Claude pairing。

### 最重要的结果

model ranking 会随 harness 翻转。

Terminal-Bench 4 中：

- Claude 在 OpenHands 里比 GPT 高 7.94 分；
- 换到 PI 后，Claude 反而比 GPT 低 30.16 分。

5 个模型中有 4 个，其最佳 harness 会随 benchmark 改变。

openJiuwen 则让 Kimi 在三个 benchmark 上都达到自己的最好成绩，提升 5.61–11.11 分。

论文还发现 vendor 自家 harness 并不稳定地是最佳选择，高成本也不保证更高分；Terminal-Bench 4 上，GPT 在 PI 中比 DSH 分数更高，但 cost per task 不到后者四分之一。

### 为什么 Harness Fit 会这么重要

作者对 matched trajectories 的解释很值得工程团队关注：大部分修复是模型主动开始的，真正的差异在于 harness 能否把失败以“模型可以利用的形式”反馈回来。

GPT 更适合 PI 的 lean scaffold；Kimi 容易生成 malformed tool call，因此在 openJiuwen 的额外结构下更强。

### 可复现性

作者公开 harness adapters、evaluation code 和 6,204 条 scored trajectories，适合直接拿来做内部模型路由实验。

### 权限与工程风险

不要因为某个 harness benchmark 高就直接迁移生产权限配置。A/B 时必须保持：

    same repository snapshot
    same task set
    same sandbox
    same tool permissions
    same timeout
    same cost accounting

否则测到的不是 harness fit，而是权限和预算差异。

### 适合谁关注

Codex、Claude Code、OpenHands、自研 Agent runtime、多模型 router，以及已经发现“同一个模型换工具后表现完全不同”的团队。

### 工程落地启发

内部 leaderboard 最好把行从“模型名”升级成：

    model × harness_version × task_family

再记录：

    success
    wall-clock
    cost
    tool errors
    test reruns
    human correction

模型升级和 harness 升级都需要独立版本号。

[论文](https://arxiv.org/abs/2610.00917) · [代码](https://github.com/liyix/finding-the-right-fit)

## 8. ActiveSaddler：Harness 优化下一步是自动选择“最值得继续练的失败模式”

**时间回补：v1 提交于 2026-10-01 01:36 UTC。**

### 突破性工程价值

自动 harness optimization 已经可以根据 rollout feedback 修改 prompt、tool interface 和 control logic，但多数方法仍按固定 scenario 顺序训练。

问题是 harness 变强以后，原本最有价值的失败案例可能已经解决；继续重复这些 scenario 只是在浪费 rollout budget。

ActiveSaddler 把“接下来训练什么”也变成优化问题。

### 算法模块

    execution trajectories
        ↓
    提取 recurring failure patterns
        ↓
    动态创建 failure-pattern arms
        ↓
    non-stationary bandit
        ├─ exploit 当前最有学习价值的已知失败
        └─ explore 新 scenario 发现新失败
        ↓
    选择下一批优化任务
        ↓
    harness optimizer
        ↓
    prompt / tool / control logic 更新
        ↺

随着 harness 改变，每种 failure pattern 的学习价值也会重新估计。

### 结果

在相同 rollout budget 和相同模型设置下：

- GAIA2 Pass@1 提高 4.4 个百分点；
- Terminal-Bench 2.0 提高 7.5 个百分点。

项目页还报告达到开发目标的实验成本：

- GAIA2：约 1360 美元 → 298 美元，约 4.6× 降低；
- Terminal-Bench 2.0：约 220 美元 → 128 美元，约 1.7× 降低。

这里最值得关注的不是绝对美元数，而是把 expensive rollout budget 从“平均撒给所有任务”改成“集中到仍然暴露系统弱点的任务”。

### 可复现性与风险

作者公开项目页和实现。最大的风险是 curriculum 过拟合当前 benchmark：如果 failure-pattern extractor 只会围绕历史错误打补丁，可能损害未知任务泛化。

因此内部使用时最好保留：

    fixed holdout suite
    adversarial unseen suite
    failure-pattern coverage
    regression count
    cost-to-target

每轮优化都必须经过独立 holdout，而不是只看 active curriculum 上的分数。

### 适合谁关注

自研 Coding Agent、Agent harness 自动优化、长期 regression suite、大量 rollout 成本敏感的团队。

### 工程落地启发

即使暂时不自动改 harness，也可以先自动做“测试选择”：每天从过去一周真实失败中聚类 failure pattern，优先跑最可能产生新信息的一小组 regression，而不是每次都把几千条测试全跑一遍。

[论文](https://arxiv.org/abs/2610.00906) · [项目页](https://autosaddler-projectpage.github.io/activesaddler/)

## AI Coding 实战技巧精选

### 技巧 1｜Claude Code 依赖 Bash deny / ask 规则时，先升级到 v2.1.289 再给 Agent 高权限

- **来源**：Anthropic / 2026-10-03 / [Claude Code v2.1.289](https://github.com/anthropics/claude-code/releases/tag/v2.1.289)。
- **一句话结论**：v2.1.289 修复了多类 permission-rule 绕过边角，包括复合 shell 命令的嵌套部分、环境变量前缀命令、sandbox auto-allow，以及 symlink 场景下 Read deny 未生效。只要团队把 deny / ask 当成安全边界，就应该先升级再继续扩大自动执行权限。
- **具体怎么做**：
  1. 将开发机、CI runner 和远程 Agent 环境统一升级到 v2.1.289 或更新版本。
  2. 建一个 permission regression：至少覆盖 compound command、变量前缀命令和 symlink read，例如让被禁止命令出现在 && / ; 后，或以环境变量赋值开头。
  3. 在升级前后跑同一组 regression，确认禁止项全部进入 deny / ask，而不是被 sandbox auto-allow。
  4. 只有 regression 通过后，再允许 background agent、plugin / mod 或更宽的 shell 自动执行。
- **适合什么场景**：Claude Code、企业 managed settings、高权限 shell、插件 / Mods、自动 CI 修复。
- **注意**：版本修复不是 OS sandbox 的替代品。生产凭据、发布权限和危险文件系统操作仍应由系统权限隔离。

### 技巧 2｜把 Codex Cloud 环境先“准备并发布”，再让多个任务复用同一套依赖和网络权限

- **来源**：OpenAI / 2026-09-29 起正式公开 / [Codex Cloud 官方文档](https://learn.chatgpt.com/docs/cloud)。
- **一句话结论**：不要让每个 Cloud task 自己临时猜依赖、安装工具和申请网络。先创建一个经过测试的 environment，把 repository、install script、tools、network allowlist 和 secrets 配好并发布，后续任务各自使用独立 workspace 但复用同一环境定义。
- **具体怎么做**：
  1. 在 Work in → Cloud 中创建 environment，选择需要的 GitHub repositories，让 Codex 自动检查依赖和工具。
  2. 审查 install / setup 结果，补齐必要的环境信息和权限，跑通项目测试后再 Publish。
  3. 在 environment 设置中只开放必要的 package registry / API domain；需要凭据时使用 network secrets，不把业务密钥写进仓库。
  4. 后续任务直接从已发布 environment 启动；项目依赖、工具或权限变化时更新 environment 并重新验证，而不是让每个任务自己漂移。
- **适合什么场景**：Codex Cloud、大仓库、多个并行 Agent、需要私有包源 / API 的团队、从手机或远程设备启动任务。
- **注意**：environment 是可复用配置，不代表任务之间共享 working tree；每个 task 仍有独立 workspace。网络权限和 secrets 也要按最小权限配置。

## 经典论文回顾

### Dynamical Movement Primitives：用稳定吸引子承载可学习的运动形状

Auke Ijspeert、Jun Nakanishi、Heiko Hoffmann、Peter Pastor 与 Stefan Schaal 的 **Dynamical Movement Primitives: Learning Attractor Models for Motor Behaviors** 发表于 Neural Computation 2013，是 DMP 路线的系统化代表论文；其基本思想可追溯到 Schaal 团队 2002 年 ICRA 的 humanoid movement imitation 工作。

### 核心问题

如果直接存一条时间序列轨迹，机器人可以重放，却很难自然地：

- 换起点；
- 换终点；
- 改执行速度；
- 在保持稳定性的同时调整运动形状；
- 在示范基础上继续优化。

DMP 的核心是把“稳定到达目标”和“复杂轨迹形状”拆开。

### 关键数学思想

最常见的离散 DMP 使用二阶 spring-damper attractor：

    τ v_dot = K(g - x) - Dv - K(g - x0)s + K f(s)
    τ x_dot = v

再用 canonical system：

    τ s_dot = -α s

让 phase variable s 单调衰减。

其中稳定 spring-damper 保证系统趋向目标 g；非线性 forcing term f(s) 使用一组 basis function 表达示范轨迹的形状。

这使“学运动”变成“学 forcing-term weights”，而不是重新学习整个控制动力学。

### 传感器 / 动力学假设

经典 DMP 本身不解决机器人完整动力学与碰撞，它生成的是 desired motion / trajectory representation。

真正部署时仍需要：

    tracking controller
    inverse dynamics / operational-space control
    joint / torque limits
    collision avoidance
    contact handling

因此 DMP 更像一个稳定、可调的 skill representation，而不是完整 whole-body controller。

### 当年为什么重要

DMP 给机器人学习提供了一个非常实用的折中：

- 比直接 trajectory playback 更能泛化起终点和时间尺度；
- 比完全 black-box policy 更容易解释；
- 吸引子结构带来明确的稳定性；
- 参数空间适合 imitation learning、RL 和 black-box optimization。

这也是后来大量 Learning from Demonstration、skill library、trajectory adaptation 工作的基础之一。

### 今天仍在使用的思想

即使今天 VLA、diffusion policy 和 humanoid foundation model 已经非常强，DMP 留下的三个思想仍然重要：

1. **低层运动先验和高层任务变化要解耦。**
2. **可学习部分最好放在受稳定结构约束的参数空间里。**
3. **skill 应该能被重定向、组合和参数化，而不是只能复读训练轨迹。**

今天 InterEvolve 其实延续了相同系统哲学，只是可编辑接口从 DMP forcing weights 升级成了 staged reward program：底层 controller 已经很强，现场适配尽量发生在更小、更可验证的任务参数空间。

### 已被后续替代 / 扩展的部分

经典 DMP 对复杂接触、多峰行为和高维场景语义表达能力有限。

现代系统扩展出了：

- Cartesian / quaternion DMP；
- coupling terms 与 obstacle avoidance；
- probabilistic movement primitives；
- 双臂 / 多臂耦合；
- DMP + CBF；
- diffusion / VLA skill generation；
- foundation-policy 上的 task adapter。

所以今天不应该把 DMP 当作“比神经策略更先进的替代品”，而应把它当作一个重要设计原则：**把学习放进一个稳定、可控制、可复用的行为接口里。**

### 公开代码与可复现性

目前有多套成熟开源实现。DFKI 的 movement_primitives 提供 DMP、ProMP、Cartesian / Dual Cartesian DMP，并支持 coupling term；dmpbbo 则包含 Python/C++ 实现和 black-box optimization 示例。

最值得做的复现实验不是简单重画论文曲线，而是拿一条现有机械臂示教轨迹，测试：

    改起点
    改终点
    改时间尺度
    加障碍 coupling
    加控制约束

再与直接 spline playback 和 learned action policy 比较失败边界。

### 对当前工程项目的重新解读

对于机器人 Agent / 操作系统，可以把 skill 分三层：

    task intent
    → reward / symbolic program

    reusable motion primitive
    → DMP / trajectory prior / learned skill

    physical execution
    → MPC / WBC / vendor controller

越往下越稳定、越少在线修改；越往上越允许 Agent 组合和适配。这比让 LLM 直接生成底层控制更容易验证，也与今天 InterEvolve 的设计非常一致。

[论文 DOI](https://doi.org/10.1162/NECO_a_00393) · [movement_primitives](https://github.com/dfki-ric/movement_primitives) · [dmpbbo](https://github.com/stulp/dmpbbo)

## 今日结论

今天最清楚的一条主线，是**机器人和 Coding Agent 都在把“可变化的部分”从核心系统里拆出来，放到更小、更容易验证的接口上。**

InterEvolve 不在线重训 humanoid controller，而是演化 reward program；ECoMEM 不把所有历史塞进模型，而把应该长期存在的信息变成显式概念；WBAG 不重训 VLA，而是在 action 落地前增加 whole-body + attached-geometry safety shield；多机 safe path following 则只放松速度，不允许安全层破坏路径和 heading 这些硬边界。

Kinematic MeanFlow 说明另一个很实际的问题：机器人 foundation model 的推理架构最终必须面对控制周期。模型平均成功率再高，如果 action head 让闭环频率掉到不可用，也很难进入真正的边缘机器人。未来 VLA 的竞争会越来越同时包含 intelligence、latency、jitter 和 safety-filter compatibility。

When Reasoning Helps Action 又给 reasoning VLA 一个很重要的刹车：推理文字变正确，只能证明 reasoning interface 更干净，不能证明物理行为更可靠。机器人系统最后必须回到 trajectory、constraint、collision 和任务成功这些可执行证据。

AI Coding 两项主动态则把“模型强弱”重新定义成系统问题。Finding the Right Fit 表明 model 和 harness 是不可分割的配置；ActiveSaddler 进一步表明 harness 训练数据也不能固定不变，应该把有限 rollout budget 花在当前仍然暴露系统缺陷的 failure pattern 上。

今天两个实战技巧也指向同一方向：高权限 shell 的安全不能只靠 Prompt，要升级并回归测试 permission engine；远程 Agent 的环境不能每次临时重建，要先发布一份经过验证、最小权限的 cloud environment。

如果把今天整期压缩成一句话：

> **成熟的机器人和 Coding Agent，不是让核心模型在线随意改变一切，而是把任务、记忆、偏好、验证、权限和适配拆成有明确契约、可回归、可回滚的小接口。**

## 最值得深入研究或尝试复现的方向

1. **Humanoid Reward Program Sandbox**：保留现有 locomotion / whole-body policy，定义一个受限 staged-reward DSL，让 Agent 只能改任务阶段、目标和权重，每个候选必须经过固定仿真 verifier。
2. **VLA Action-Head Latency A/B**：在 Jetson Orin 上把视觉 backbone 和 action head 分别 profile，只有确认多步 flow matching 是主要瓶颈后，再测试 K-MF / early-exit / distillation。
3. **Explicit Robot Memory Store**：给长期任务建立 Entity / State / Event / Procedure 四类结构化记录，保存 evidence 和 invalidation condition，与纯长 context 做失败率和 token A/B。
4. **Attached-Object Safety Geometry**：机械臂每次 grasp / release 时原子更新 attached geometry，并让 planner、collision checker 与 runtime shield 读取同一 revision。
5. **多机 Safety QP 的硬软约束分层**：固定 path / heading 为 hard constraint，只允许 speed 退让，故意注入定位延迟和 packet loss 测理论假设被破坏后的真实 margin。
6. **CoT Actionability Regression**：reasoning monitor 每次改写推理后，都记录 action delta 和闭环 task delta；没有行为改善的 reasoning gain 不进入安全 KPI。
7. **Model × Harness × Task Leaderboard**：内部评测不再只登记 model name，而是绑定 harness version、tool schema、权限和 task family。
8. **Failure-Pattern Curriculum**：把最近一个月 Agent 真实事故聚类，只对仍频繁出现且修复后最可能提高成功率的 failure pattern 分配昂贵 regression / rollout budget。

## 参考资料

- [arXiv Robotics 最新列表](https://arxiv.org/list/cs.RO/recent)
- [arXiv Software Engineering 最新列表](https://arxiv.org/list/cs.SE/recent)
- [InterEvolve](https://arxiv.org/abs/2610.02196)
- [InterEvolve 项目页](https://sirui-xu.github.io/InterEvolve/)
- [Kinematic MeanFlow](https://arxiv.org/abs/2610.00864)
- [ECoMEM](https://arxiv.org/abs/2610.00801)
- [ECoMEM 项目页](https://ecomem.github.io/)
- [WBAG](https://arxiv.org/abs/2610.01083)
- [Decentralized Safe Path Following](https://arxiv.org/abs/2610.00208)
- [Safe Multi-Quadrotor Path Following 项目页](https://gradslab.github.io/safe_multiquad_pf/)
- [When Reasoning Helps Action](https://arxiv.org/abs/2610.00601)
- [Finding the Right Fit](https://arxiv.org/abs/2610.00917)
- [Finding the Right Fit 代码](https://github.com/liyix/finding-the-right-fit)
- [ActiveSaddler](https://arxiv.org/abs/2610.00906)
- [ActiveSaddler 项目页](https://autosaddler-projectpage.github.io/activesaddler/)
- [Claude Code v2.1.289](https://github.com/anthropics/claude-code/releases/tag/v2.1.289)
- [Codex Cloud 官方文档](https://learn.chatgpt.com/docs/cloud)
- [Dynamical Movement Primitives DOI](https://doi.org/10.1162/NECO_a_00393)
- [DFKI movement_primitives](https://github.com/dfki-ric/movement_primitives)
- [dmpbbo](https://github.com/stulp/dmpbbo)
