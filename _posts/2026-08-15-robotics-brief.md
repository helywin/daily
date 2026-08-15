---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-15"
date: 2026-08-15 09:00:00 +0800
description: "本期关注跨楼层持久语义导航、LiDAR 自监督表示、自动干预、近传感器触觉、VLA 自适应推理、物理提示注入、Agent 技能运行时保障与多机航空协调。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-08-15

## 摘要

截至 2026-08-15（Asia/Shanghai）早间，本轮检索遇到一个数据源时效性问题：arXiv `recent` 页面在当前检索通道中的缓存仍停留在较早批次，且无法稳定完整核验 8 月 14 日可能新增的 Robotics / Software Engineering 批次。为避免把未核验条目包装成“今日新发布”，本期严格按任务规范扩大到最近 7 天窗口，并只收录能够从 arXiv 原始页面、官方项目页或官方代码仓库完整核验、且未出现在 `robotics-brief-covered-items.md` 中的工作。所有主动态均明确标注原始提交日期。

本期共选择 8 条主动态。导航与地图方向最值得看的是 LifelongCrossNav：它把单次 ObjectNav 变成跨楼层、连续多目标任务，并在整个 episode 中维护可长期复用的稀疏 3D 语义体素记忆；Vernata 则从 LiDAR 表征层解决户外点云标注昂贵和点密度变化的问题，通过多教师自监督、稀疏视图增强与跨模态蒸馏提升下游语义能力。

机器人控制与部署侧，AutoIntervene 直面 action-chunking policy 的一个危险失效模式：策略即使已经偏离演示分布，仍可能继续输出非常平滑但与当前状态不一致的动作块。它用成功轨迹构建 visual-action support memory，自动决定何时把控制权交给人、何时还给策略，并把成功人工干预片段反过来作为纠正数据。近传感器视觉触觉工作则把 Poisson 深度重建直接搬到 FPGA/ASIC 流水线，128×128 深度首值固定延迟约 0.211 ms，完整保护反射动作从主机方案约 170 ms 降到约 28 ms，说明机器人安全反射越来越适合做成独立于主 GPU 的本地确定性通道。

VLA 部署方面，Environment-aware Model Selection 不再强耦合“大模型慢思考”和“小模型快控制”，而是让两套完全解耦的策略由环境感知切换器按需调用，在 LIBERO 上保持接近大模型的成功率同时把有效动作频率提升到 93.4 Hz。机器人基础模型安全方面，Physical Prompt Injection 研究证明一张写有恶意文字的纸就可能诱导 VLM 规划器偏离原任务，且成功攻击在推理轨迹中几乎都被模型“看见并承认”；这意味着物理环境中的文字必须像网络输入一样进入安全边界。

AI Coding 侧，本期最值得关注的是 SkillSentry。它不重新训练 Coding Agent，而是把 skill 文档和历史成功/失败轨迹编译成运行时指导 DSL，包裹在现有 Agent 循环外监控每一步技能执行；在 Claude Code 与 Codex、多种底模的 15 个技能上，平均任务成功率提高 24.1%，同时降低重复运行波动。最后，Plan-and-Avoid 从多机航空协同给出一种很实用的“优先轨迹 + 周边单边避让”范式：当一架飞机因应急或任务约束不能轻易改轨时，不强迫所有参与者一起重规划，而是自动向周边飞机发出满足机动约束的避让建议。

本轮同时检查了主流模型厂商的近期官方发布入口，没有发现需要挤掉上述机器人/控制条目的、可完整核验的过去 24 小时全新通用大模型或代码基础模型正式发布，因此本期不使用旧模型新闻补位。

## 1. LifelongCrossNav：把 ObjectNav 从一次性找目标升级成跨楼层、可积累经验的持久 3D 语义导航

**时间回补：arXiv v1 提交于 2026-08-07 10:31 UTC。此前未进入去重索引。**

LifelongCrossNav 面向未知多楼层室内环境中的 sequential multi-object ObjectNav：机器人不是每收到一个目标就重新探索，而是在整个 episode 中持续维护共享的稀疏 3D 语义体素记忆。记忆同时累积几何结构、可通行状态和 vision-language features，使后续目标可以直接利用前面任务已经获得的场景知识；跨楼层部分则加入 support-aware 3D traversability、楼梯专用感知和方向感知的楼梯穿越。（[论文](https://arxiv.org/abs/2608.07079)，[项目页](https://flageval-baai.github.io/LifelongCrossNavPage)）

### 为什么重要

很多语义导航系统在单个目标上表现不错，但任务一结束就相当于“失忆”。工业巡检、服务机器人或长期自主系统更接近 LifelongCrossNav 的设定：一天内连续找多个对象、跨楼层移动，而且前一个任务建立的地图理应成为下一个任务的资产。

更关键的是它把楼梯从“特殊动作”提升为 3D traversability 的一部分。传统 2D semantic map 很容易在楼梯、电梯、夹层等垂直连接结构上失去拓扑语义，而持久 3D memory 能在全局层直接保存这些跨层连接。

### 算法模块

- 以 sparse 3D semantic voxel memory 作为长期环境状态；
- 持续融合几何、可通行状态和 vision-language features；
- 对当前帧提取 live point-of-interest，同时可从历史记忆检索 historical POI；
- 使用 same-floor frontier exploration 处理当前楼层未知区域；
- 用 support-aware 3D traversability 判定可站立/可移动区域；
- 对楼梯建立专用感知和 direction-aware traversal；
- 统一策略在 frontier、历史 POI、楼梯、目标搜索与最终接近之间切换；
- 提出 HM3D-MFMON，用于 sequential Multi-Floor Multi-Object Navigation。

### 传感器与系统假设

它属于语义导航/记忆层，不是替代 SLAM 的位姿估计器。系统仍假设底层几何投影和机器人运动足以把多次观测稳定写入共享 3D 体素坐标系；如果底层位姿长期漂移，持久语义记忆同样会被污染。

此外，vision-language feature 适合做开放词汇检索，却不能直接作为碰撞安全依据。真实机器人仍应把几何占用、坡度/台阶可通行性与语义目标分开维护。

### 实时性、鲁棒性与可复现性

论文摘要没有给出可直接外推到实体机器人的统一端到端控制频率，因此本期不人为补一个 FPS。实验在作者提出的 HM3D-MFMON 上相对代表性的平面持久语义地图基线取得持续优势，说明 3D 持久记忆和跨楼层建模确有价值，但最终实机效果仍取决于底层定位、楼梯检测和真实动态环境变化。

当前 arXiv 页面提供项目页，但没有在摘要页直接列出稳定代码仓库，完整复现性暂评中等。

### 风险

- 长期 voxel memory 需要生命周期管理，否则动态物体会被写成长期事实；
- 跨楼层后坐标漂移会造成历史 POI 错位；
- 楼梯可通行不仅是几何问题，还依赖具体机器人能力；
- VLM feature 对相似物体和外观变化可能产生语义误检；
- 多目标任务中的“记忆越多越好”并不成立，需要压缩、淘汰和置信度衰减。

### 适合谁关注

适合长期巡检、服务机器人、多楼层语义导航、场景图和 persistent memory 团队。

### 工程落地启发

现有 LiDAR 导航系统不必直接换成端到端 ObjectNav。更现实的路线是保留高频 LIO + 局部占用地图，在其上增加稀疏的“楼层—区域—POI”长期层：几何地图负责能不能走，持久语义层负责以前在哪里见过什么。这样跨楼层和多任务经验能够积累，又不会让语义错误直接进入碰撞控制。

## 2. Vernata：用多教师自监督预训练 LiDAR 表征，专门处理户外点云标注贵和点密度变化

**时间回补：arXiv v1 提交于 2026-08-07 07:51 UTC；IROS 2026。官方实现已公开，此前未进入去重索引。**

Vernata 建立在 Sonata 架构上，针对户外 LiDAR 表征学习增加三项关键机制：sparse view augmentation 用于模拟不同传感器/距离造成的点密度变化；memory bank 稳定资源受限条件下的训练；cross-modal distillation 则从高分辨率 2D 图像教师向稀疏点云传递更细粒度语义。（[论文](https://arxiv.org/abs/2608.06919)，[代码](https://github.com/rai-opensource/vernata)）

### 为什么重要

LiDAR 学习算法一个长期现实障碍是 3D 标注昂贵，而且同一模型从 64 线数据迁到 16 线、固态非重复扫描或远距离稀疏区域时，点分布变化非常大。单纯在一个点密度固定的数据集上监督训练，很容易把“传感器采样模式”学成特征。

Vernata 的思路更接近基础表征：先用大量无标签点云学习对密度、模态缺失和传感器变化更稳定的 point representation，再把它交给 traversability、语义分割、障碍理解等下游任务。

### 算法模块

- 以 Sonata 为基础的自监督 LiDAR encoder；
- sparse-view augmentation 主动降低/改变点密度；
- memory bank 在受限 batch / 显存下保持更稳定的对比/蒸馏目标；
- 多教师结构融合不同监督信号；
- cross-modal distillation 从稠密 2D image features 向 3D 点传递语义；
- 对缺少 color 或 normals 的 reduced-modality 输入单独评估鲁棒性。

### 传感器假设

训练阶段可以使用图像教师，但论文同时验证了减少模态后的 LiDAR 表现，因此部署端不必永久依赖相机。需要注意的是，跨模态蒸馏会把视觉教师的类别偏差一起写入 LiDAR 表征；夜间、逆光、雨雪或视觉教师错分时，教师并非绝对真值。

### 结果、实时性与鲁棒性

论文在 GrandTour、TartanGround、Waymo 和自采机器人数据上评估。TartanGround mIoU 达 54.7，相对 Sonata baseline 提升 5.9 个百分点；Waymo 达 57.1，提升 7.3 个百分点。缺少 color 或 normals 的 reduced-modality 设置仍达到 49.4 和 50.2 mIoU，说明表征并未完全依赖完整输入模态。（[论文](https://arxiv.org/abs/2608.06919)）

论文重点是预训练表征质量，摘要没有给出特定下游模型的 Jetson 实时帧率，因此不能把 mIoU 提升直接等价为“可实时导航”。好处是官方实现已经公开，可直接做内部数据预训练和下游线性探测实验。

### 风险

- 视觉教师错误可能被蒸馏到 LiDAR；
- 自监督预训练的下游收益依赖数据域是否匹配；
- 语义 mIoU 提升不代表 SLAM 几何残差更稳定；
- 大规模预训练仍需要显著 GPU 资源；
- 不同 LiDAR 的时间/扫描模式问题不能靠 representation learning 修复。

### 适合谁关注

适合 LiDAR 语义理解、非结构化地形 traversability、多型号 LiDAR 统一感知和低标注成本训练团队。

### 工程落地启发

最值得做的不是把学习网络塞进 LIO 主前端，而是先用大量自有无标签点云做 Vernata 类预训练，再测三个独立任务：地面/障碍分类、动态点识别、退化场景几何区域评分。如果同一 encoder 能在 16 线和 MID360 类数据上保持稳定，再考虑把它用于自适应权重或语义地图。

## 3. AutoIntervene：策略动作看起来很平滑，也可能已经错了；用 visual-action support 自动决定何时让人接管

**时间回补：arXiv v1 提交于 2026-08-07 10:14 UTC。此前未进入索引。**

Action-chunking policy 一次预测未来若干步动作，能减少抖动、提高时间一致性，但也带来一个特殊危险：当感知错误或执行偏差把机器人推离演示分布后，策略仍可能继续输出非常平滑的动作块，让系统“看起来很稳定地做错事”。AutoIntervene 用成功任务轨迹构建 visual-action support memory，在部署时同时比较当前视觉状态和策略提出的 action chunk 是否仍被历史成功经验支持。（[论文](https://arxiv.org/abs/2608.07065)，[项目页](https://aus.bot/research/autointervene/)）

### 为什么重要

人工遥操作接管通常靠操作者盯视频主动判断，既占人又不一致；仅靠视觉 OOD score 又可能误报，因为同一视觉状态下动作方向是否合理同样重要。AutoIntervene 把“是否需要人”定义为**当前状态—动作联合是否落在成功支持集内**，更贴近真实策略失效。

### 算法模块

- 从成功执行建立 visual-action support memory；
- visual similarity 判断当前状态是否接近历史支持区域；
- proposed/reference action consistency 判断当前 action chunk 是否与成功行为一致；
- phase-local support 决定 policy → operator 的接管；
- global support 决定 operator → policy 的控制权返还；
- 两个方向使用不同切换阈值；
- 阈值由 held-out expert demonstrations 的经验分位数校准，而不是人工拍脑袋；
- 成功 rollout 中的人工接管片段被保留，形成下一轮纠正监督数据。

### 传感器与控制假设

系统主要围绕视觉动作策略，前提是已有任务 phase、成功演示和人工遥操作通道。它不是形式化安全证明，也不能发现“历史成功轨迹本身包含危险行为”的问题。

另外，visual-action support 是数据驱动的；遇到真正新颖但安全的策略动作时也可能频繁请求接管，因此 support threshold 与任务探索性之间存在明显权衡。

### 实时性、鲁棒性与可复现性

论文在真实双臂操作任务上报告，相比纯手动干预策略，AutoIntervene 在后续适配后获得更高任务成功率和更低 operator-control time。摘要没有给出统一毫秒级 support 查询延迟，因此真实部署仍需测视觉 embedding、memory search 和切换判定的 P99 延迟。

当前有公开项目页，但未在 arXiv 摘要中列出稳定代码仓库，完整复现性暂评中等。

### 风险

- 支持记忆覆盖不足会产生过度接管；
- phase 错判会使局部阈值失效；
- 人工接管动作如果质量不稳定，会污染后续纠正训练；
- 控制权切换本身要防止速度/力矩不连续；
- 仅凭经验支持不能替代碰撞、力限位和急停。

### 适合谁关注

适合 action-chunking imitation policy、VLA 部署、遥操作辅助学习和工业机器人数据闭环团队。

### 工程落地启发

这非常适合做成“人只处理策略真正不确定的 5%–20% 时间”的数据飞轮：策略正常时自主执行，超出 visual-action support 时自动暂停/降速并请求接管，接管成功后把这段数据自动标成高价值纠正样本。比全天候人工遥控收数据更高效。

## 4. Near-sensor Visuotactile：把深度重建放到传感器旁边，机器人保护反射从约 170 ms 降到约 28 ms

**时间回补：arXiv v1 提交于 2026-08-06 08:08 UTC。此前未进入索引。**

《Near-sensor Computing for Rapid Visuotactile Perception》把视觉触觉传感器常见的梯度场到深度图 Poisson 重建，映射成固定调度的流式硬件管线，而不是把原始图像送到主机 CPU/GPU 后迭代求解。128×128 输入下，FPGA 逻辑以 166 MHz 运行，从第一输入像素到第一深度值固定为 35,107 个周期，即约 0.211 ms；计算逻辑功耗估计约 347 mW。（[论文](https://arxiv.org/abs/2608.05725)，[HTML 全文](https://arxiv.org/html/2608.05725)）

### 为什么重要

机器人真正的安全反射不应该依赖主 GPU 当前是否正在跑 VLA、SLAM 或视频模型。触觉接触属于高优先级、本地、时间确定性的事件；把感知重建和阈值决策下沉到 near-sensor FPGA/ASIC，可以让保护链路拥有独立算力与固定时延。

这与工业控制中的安全 PLC 思路很像：主智能系统负责复杂任务，局部硬实时通道负责“马上松手/退让/停机”。

### 算法与硬件模块

- 视觉触觉成像阵列获得软弹性体形变；
- structured illumination / photometric stereo 得到局部表面梯度；
- 将 Poisson 方程改写为 spectral direct formulation；
- 全流水硬件执行固定调度，无数据依赖分支和迭代收敛；
- 每帧产生 calibrated depth，而不是只输出原始像素；
- 本地阈值/决策直接触发执行器保护动作；
- 主机仍可异步读取深度用于精细力估计或触觉建图。

### 实时性与精度

在 15 种接触几何上，重建深度与 double-precision reference 的差异约为峰值接触深度的 0.17%。完整 contact-to-motion 保护反射延迟为 28.3±4.9 ms，而同一执行器、经主机处理的等价链路约 169.9±27.8 ms，约降低 6 倍；其中近传感器方案的大部分剩余时间实际来自舵机自身响应。（[HTML 全文](https://arxiv.org/html/2608.05725)）

### 传感器假设与风险

论文针对特定视觉触觉成像结构和 Poisson 重建，不意味着任意 GelSight 类传感器都能直接复制。真实产品还要处理弹性体老化、光源变化、污染、温漂和标定变化。

硬件流水线的优势是确定性，但固定算法也意味着灵活性较低。如果接触模型升级为复杂神经网络，功耗和确定延迟优势可能迅速缩小。

### 可复现性

论文给出了详细硬件结构和性能指标，但是否提供完整可综合 RTL/板级工程需要在正式 artifact 中继续核验；当前本期未找到稳定官方代码仓库地址，因此不虚构链接。

### 适合谁关注

适合机器人触觉、末端执行器安全、灵巧手、夹爪力控、FPGA near-sensor computing 和高可靠保护系统团队。

### 工程落地启发

即使没有视觉触觉传感器，也值得复制其架构：碰撞电流、六维力、触觉阵列、急停边沿等安全信号建立独立 1–10 kHz 本地处理链；主 VLA/规划器只接收“当前安全状态”和高级触觉特征，不让复杂 AI 推理成为保护动作的串行依赖。

## 5. Environment-aware Model Selection：完全解耦快/慢两套 VLA，用环境状态决定什么时候才调用大模型

**时间回补：arXiv v1 提交于 2026-08-06 06:32 UTC。此前未进入索引。**

《Fast and Accurate: An Adaptive VLA Inference Framework through Environment-aware Model Selection》针对 dual-system VLA 的部署难题：很多“慢思考 + 快控制”架构让轻量控制器依赖大模型内部中间表征，因此模型必须联合训练，慢模型一换版本，快模型也要重做。作者提出 EMS，让 large deliberative system 与 lightweight reactive system 完全解耦，再由 RL switching policy 根据实时环境反馈选择当前该调用哪一个。（[论文](https://arxiv.org/abs/2608.06434)）

### 为什么重要

机器人部署中最难接受的是“为了保持 20–50 Hz 控制，每一帧都必须跑一个大 VLM/VLA”。实际上，大多数稳定阶段只需要轻量闭环策略，真正需要大模型的是任务阶段变化、遮挡、失败恢复和复杂语义决策。

如果快慢系统完全解耦，就可以独立替换底模、量化或部署在不同算力节点上。这比从大模型内部抽 hidden state 给小模型更适合长期产品维护。

### 算法模块

- large-scale deliberative policy 负责全局一致、长时域规划；
- lightweight reactive policy 负责高频闭环动作；
- 两个系统使用独立模型，不要求共享中间特征；
- RL-based switching policy 读取环境反馈；
- 根据当前场景复杂度/不确定性决定调用快模型还是慢模型；
- 慢模型只稀疏调用，降低总体推理成本；
- 架构支持 plug-and-play model replacement。

### 实时性与结果

论文在 LIBERO 上报告成功率接近 large-scale baseline，同时有效动作频率提升到 93.4 Hz；真实双臂操作实验也展示了在保持任务表现的同时缩短执行时间。（[论文](https://arxiv.org/abs/2608.06434)）

需要注意，“93.4 Hz 有效动作频率”是论文系统定义下的综合结果，不等于任意大模型+小模型组合都可以达到该频率。真实 P99 latency 仍取决于切换器、网络通信、慢模型并发和 action chunk 缓存。

### 风险

- switching policy 本身可能误判复杂场景；
- 快模型在未知状态继续执行可能放大错误；
- 慢模型触发时要处理异步结果过期；
- 两套策略输出需要统一坐标系、动作尺度和安全限制；
- 如果大/小模型行为分布差异过大，切换瞬间可能出现动作不连续。

### 可复现性

当前 arXiv 页面未列出稳定官方代码仓库，完整复现性暂评中等偏低。

### 适合谁关注

适合 VLA 部署、端侧机器人、双臂/移动操作、模型服务架构和需要兼顾高频控制与复杂推理的团队。

### 工程落地启发

可以把当前机器人分成三条时钟：100–1000 Hz 传统底层控制，10–50 Hz 小策略闭环，0.5–5 Hz 大模型任务/恢复决策。大模型永远不直接阻塞底层周期；切换器只负责更新高层 action target 或 skill，而不是直接输出电机指令。

## 6. 一张纸就能劫持机器人：VLM 物理 Prompt Injection 应进入机器人安全威胁模型

**时间回补：arXiv v1 提交于 2026-08-06 07:52 UTC。此前未进入索引。**

《Hijacking Robots with a Piece of Paper》系统研究了 VLM 控制机器人面对“场景中的人类可读恶意文字”时的 prompt injection 风险。作者设计 20 种攻击、3 种物理布局、3 种指令表达，共完成 5,670 次试验；GPT-4o、Gemini 2.5 Flash、Qwen3-VL-32B 的总体攻击成功率分别为 27.0%、29.4% 和 5.0%。（[论文](https://arxiv.org/abs/2608.05715)，[HTML 全文](https://arxiv.org/html/2608.05715)）

### 为什么重要

网络 Agent 的 prompt injection 通常来自网页、邮件或文档；机器人 VLM 的攻击面更直接——只要摄像头能看到文字，墙上的纸条、箱子标签、显示屏甚至恶意二维码旁边的说明文字，都可能变成“隐形 system prompt”。

更值得警惕的是，成功攻击并非模型完全没意识到文字存在。论文对 1,105 个成功攻击轨迹分析发现，99.9% 的 reasoning trace 明确提到被注入的文字：模型是“看见了，而且选择服从”。这意味着仅靠提升 OCR/视觉理解精度并不能解决问题。

### 攻击与防御结构

- 攻击分 indirect signage、task redefinition、authority impersonation、conflict injection；
- 测试不同场景布局和不同规则明确度的主任务指令；
- prompt-based defense 通过上层指令提醒忽略场景文字；
- two-stage verification 在执行前增加独立验证；
- text masking 在视觉预处理阶段去除场景文本；
- 防御效果在论文 benchmark 中分别约 75–100%、85–100% 和 100%。

### 风险解释

Text masking 在该 benchmark 中最有效，但不能简单推广为产品默认方案，因为机器人真实任务往往需要读仪表、设备编号、危险标识和箱体标签。彻底抹掉文字会损失正常能力。

更合理的是区分**环境事实文本**与**控制指令权限**：视觉文字可以作为对象属性或信息证据，但不能直接提升为高权限动作指令。真正改变任务目标、禁用安全规则、切换控制模式的命令必须来自受认证通道。

### 可复现性与工程边界

论文的实验对象是 VLM-controlled sorting，不能直接把攻击率外推到所有机器人/VLA。不同 system prompt、工具限制和动作空间都会显著影响结果。但 5,670 次物理场景实验已经足以证明这是系统性攻击面，而不是偶然 jailbreak。

### 适合谁关注

适合 VLA/VLM 机器人、仓储分拣、服务机器人、巡检读表、机器人 Agent 安全和功能安全团队。

### 工程落地启发

建议给 VLM 感知输出增加 provenance：`文本内容 / 来源=相机 / 位置 / OCR置信度 / 是否经过认证`。视觉文本默认只能进入低权限 context；任何改变任务、速度、安全区域或工具权限的指令都必须来自签名任务系统、HMI 或后台调度器。执行前再由独立规则层检查动作是否违反任务 contract。

## 7. SkillSentry：不重训 Codex/Claude Code，在 Agent 外面加“技能运行时保障层”就能提高稳定性

**时间回补：arXiv v1 提交于 2026-08-10 08:13 UTC。此前未进入索引。**

SkillSentry 针对一个很真实的 Coding Agent 问题：即使 Agent 已经“会”某个 skill，也可能在相似任务或重复运行中偏离既定步骤、遗漏关键校验或错误执行某一步。它提出 skill-oriented runtime assurance framework，用专门 DSL 表达技能执行过程中的运行时指导，并把 skill 文档与历史成功/失败 trace 共同编译成可执行保障逻辑。（[论文](https://arxiv.org/abs/2608.09253)）

### 为什么重要

当前大量 Agent skill 只是 Markdown：告诉模型“先搜索、再修改、再测试”。但真正执行时，模型可能跳步、重复、提前结束，或者工具返回错误后仍继续。SkillSentry 把 skill 从“提示词知识”升级成**运行时可监控过程**，这与传统软件中的 runtime verification 很接近。

### 算法与系统结构

- 从 skill document 抽取显式步骤与约束；
- 从历史成功/失败 execution trace 挖掘实际经验；
- 将两者合成 runtime-guidance DSL；
- wrapper 包裹现有 Agent execution loop；
- 监控当前执行是否偏离 skill guidance；
- 必要时向 Agent 注入纠偏指导；
- 新执行 trace 继续反馈到 guidance refinement；
- 不要求修改基础模型权重。

### 结果

作者在 15 个 skills 上评估两类 Coding Agent：Claude Code 搭配 Claude Haiku 4.5 / Claude Opus 4.6，以及 Codex 搭配 GPT-5.2 / GPT-5.4。SkillSentry 跨技能平均任务成功率提高 24.1%，同时降低重复运行的结果波动。（[论文](https://arxiv.org/abs/2608.09253)）

### 突破性工程价值

这条路线比无限增加 system prompt 更可维护。团队可以把“必须先读测试规范”“修改后必须运行哪些检查”“禁止在错误 branch 上提交”等规则做成 runtime contract，而模型依然可以自由完成语义推理。

它也可以与 skill 安全扫描形成互补：静态阶段检查 skill 是否包含危险命令，运行时阶段检查 Agent 是否按批准过程执行。

### 风险与可复现性

当前本轮检索没有稳定确认到与该论文对应的官方代码仓库，因此只保留 arXiv 原文链接，不引用名称相同但无关的 SkillSentry 项目。

DSL 规则过细会把 Agent 变成脆弱工作流；过松又无法真正保证执行。历史失败 trace 也可能只覆盖已知错误模式，因此 runtime assurance 不是形式化证明。

### 适合谁关注

适合 Codex、Claude Code、OpenHands、自建 Coding Agent、团队级 skills 以及自动化软件研发平台。

### 工程落地启发

内部 skills 建议逐步从 Markdown 升级成 `spec + runtime contract + regression cases`。例如“修复 GitHub Issue”技能不只是写步骤，而要声明：必须确认当前 revision、必须在补丁前复现失败、必须在补丁后运行指定测试、写操作失败不能声称完成。Agent 负责创造性修复，保障层负责过程真实性。

## 8. Plan-and-Avoid：当一架飞机不能改轨时，让周边交通单边避让，而不是让所有 Agent 一起重规划

**时间回补：arXiv v1 提交于 2026-08-06 23:29 UTC。此前未进入索引。**

Plan-and-Avoid（PAA）针对多机协同中的“priority trajectory”问题：某架飞机可能因为应急着陆、机动能力受限或任务优先级而必须尽量保持既定轨迹。框架先预测该轨迹与周边交通之间、考虑不确定性的 well-clear separation violation；若优先飞机自身无法保持间隔，就向附近飞机生成满足各自机动约束的 unilateral avoidance advisories。（[论文](https://arxiv.org/abs/2608.06648)）

### 为什么重要

多机器人规划经常默认所有机器人都可自由改轨，但工业现场并不是这样：吊运机器人、载重 AGV、执行紧急任务的机器人、已进入狭窄通道的机器人可能拥有不同的“改计划成本”。把优先级显式写进协调算法，比所有 Agent 对称重规划更符合真实调度。

PAA 的思想也适合多机器人系统：保护一条高优先级任务轨迹，其他低优先级机器人局部让行，而不是每次冲突都触发全局联合优化。

### 算法模块

- 输入一条 declared priority trajectory；
- 预测周边多机交通与优先轨迹的未来 separation；
- 把状态/轨迹不确定性带入 well-clear violation 检测；
- 若冲突，针对周边飞机生成 unilateral advisory；
- advisory 满足相应 vehicle constraints；
- 论文中的 Plan 组件使用 contingency landing planner 产生应急候选优先轨迹；
- Avoid 组件修改周边飞机轨迹，同时保持优先飞机计划。

### 实时性与结果

论文使用 Washington, D.C. 真实 ADS-B 交通，覆盖 900 多个 forced-landing cases、累计超过 140 小时模拟飞行；框架对全部 575 个 unique conflict encounters 都生成了可行 cooperative advisory。个人电脑上的最坏端到端响应时间为 5.7 s，其中包括优先轨迹规划、避让建议生成以及 1 s 双向数据链延迟；93.5% 建议满足 35 s 的 RTCA DO-365 Detect-and-Avoid 时间阈值。（[论文](https://arxiv.org/abs/2608.06648)）

### 传感器与系统假设

这是航空交通协调框架，不是近距离无人机避障器。它假设参与者具备共享/广播状态和执行 advisory 的合作能力，并使用 well-clear 而非厘米级碰撞距离作为安全目标。

因此不能直接拿 5.7 s 指标指导室内无人机；真正可迁移的是优先级建模和单边协调结构。

### 风险与可复现性

论文当前未给出稳定官方代码仓库。未来工作还需量化 advisory 给普通交通带来的绕行和延误。若通信延迟、状态广播错误或参与者不合作，集中生成的 advisory 也可能失效。

### 适合谁关注

适合多无人机调度、多机器人交通管理、应急轨迹保护和大型园区 fleet orchestration 团队。

### 工程落地启发

多机器人调度器应给任务和轨迹定义“可让行等级”。例如载重搬运、危险区退出、消防任务属于高优先级，空载巡检车属于低优先级；冲突解决先尝试只调整低优先级机器人。这样比每次都让所有机器人重新规划更稳定，也更容易解释和审计。

## 经典论文回顾

### R3LIVE：把 LiDAR-IMU 几何骨架与相机光度纹理解耦，再在同一状态估计系统中紧耦合

**发表时间与历史位置：** R3LIVE 的 arXiv v1 于 2021 年 9 月 10 日公开，后被 ICRA 2022 接收。它建立在 R2LIVE、FAST-LIO 和 ikd-Tree 的工程基础之上，目标不是只提升 VIO/LIO benchmark，而是同时输出可靠状态估计与实时高密度 RGB 彩色三维地图。（[论文](https://arxiv.org/abs/2109.07982)，[官方代码](https://github.com/hku-mars/r3live)）

### 解决的核心问题

LiDAR 对尺度和几何非常稳定，但在长走廊、大平面、稀疏结构下也会退化；相机有丰富纹理，却受光照、曝光和低纹理影响。R3LIVE 没有简单把所有残差塞进一个巨大统一优化器，而是设计两个职责清晰、彼此耦合的子系统：LIO 使用 LiDAR+IMU 建立全局地图的几何结构，VIO 使用视觉+惯性观测直接最小化 frame-to-map photometric error，并给已有 3D 点渲染/更新颜色纹理。

### 算法模块与关键数学思想

- LIO 子系统基于 FAST-LIO，用 LiDAR + IMU 提供高频、尺度稳定的几何状态；
- LiDAR 点增量写入全局三维地图；
- VIO 子系统读取视觉观测和已有几何地图；
- 将 3D 地图点投影到当前图像；
- 直接最小化 frame-to-map photometric error，而不是只依赖稀疏视觉角点；
- 视觉更新同时修正状态并为三维点赋颜色；
- 两个子系统共享/传递状态，使视觉在 LiDAR 退化时补充约束、LiDAR 在视觉弱纹理时保持几何稳定；
- 提供离线 mesh reconstruction 与 texturing 工具，把 SLAM 输出继续用于三维应用。

### 传感器与标定假设

系统需要 3D LiDAR、IMU 与相机，三者之间的时间同步和外参非常关键。相机的 photometric residual 还受曝光、白平衡、运动模糊影响；LiDAR 几何正确也不能自动修复严重 camera-LiDAR 外参误差。

R3LIVE 官方生态还提供 targetless LiDAR-camera calibration 工具，这本身说明多模态系统真正的工程门槛往往在同步与标定，而不只是估计公式。

### 当年为什么重要

2021–2022 年很多 LIO 已经能提供很强的几何轨迹，但“实时高精度彩色地图”仍常需要离线 SfM/纹理处理。R3LIVE 把几何状态、光度更新、实时 RGB map 和后处理工具放到一个公开系统中，并证明 LiDAR 与视觉可以按各自优势分工，而不是让一种传感器成为另一种的附属。

### 今天仍然有效的思想

- 传感器应按物理优势分工，而不是简单等权拼接；
- LiDAR/IMU 适合承担高频几何骨架；
- 相机可以作为中低频纹理/光度约束，而不必主导每一帧状态；
- 高密度地图表达与高频定位状态可以解耦；
- 多模态退化要允许另一模态临时接管主要约束；
- 标定、时间同步和数据质量监控必须是一等公民。

### 已被后续方法替代或扩展的部分

现代系统开始使用 3D Gaussian Splatting、neural implicit map 和 feed-forward 3D foundation model 做更高质量的稠密表达；学习式全局描述子和语义层也增强了长期回环与场景理解。FAST-LIO2、现代 voxel/hash map 和多传感器因子图让局部几何状态更高效；相机 photometric model 也可由更鲁棒的 learned feature 替代。

但这些更新并没有推翻 R3LIVE 的核心架构：**几何高频状态和丰富视觉地图应分层，而昂贵视觉表示不应该阻塞机器人控制链。**

### 公开代码、数据与可复现性

官方 `hku-mars/r3live` 仓库仍公开，并提供 R3LIVE dataset、离线 mesh/texturing utility 和采集硬件机械设计。仓库页面标明源码基于 GPLv2，但同时明确写有“personal and academic usage free，commercial use 联系作者另行协商”的附加说明，因此闭源商业产品不能只看到 GPL 标签就直接集成，必须单独核对作者许可条款。（[官方代码](https://github.com/hku-mars/r3live)）

### 对当前工程项目的重新解读

今天做多 LiDAR + IMU + 相机/RTK 的机器人，不必把 R3LIVE 理解成“再加一个相机就会更准”。更值得复制的是分层职责：

```text
IMU 高频传播
    ↓
LiDAR 几何状态 / 局部地图
    ↓
视觉或其他模态中频校正与语义/纹理增强
    ↓
RTK、反光标志、回环等低频全局约束
```

每个模态都应该有独立健康度。当 LiDAR Hessian 退化时提高其他约束；相机曝光或低纹理时降低视觉权重；RTK 跳变时拒绝全局因子。不要把“多传感器融合”做成简单把所有残差永远同时打开。

## 今日结论

本期因为最新 arXiv 批次在当前检索通道中无法稳定完整核验，因此严格采用时间回补，而没有制造“8 月 15 日新论文”标签。这本身也说明日报工作流需要继续把“来源是否真正刷新”与“搜索结果看起来新不新”分开，否则非常容易把缓存日期误当成真实最新批次。

技术上，今天最明显的趋势是**机器人系统开始从一次性模型能力转向长期运行能力**。LifelongCrossNav 让语义地图跨多个目标和楼层持续积累；AutoIntervene 把人工接管从被动遥操作变成可自动触发、可回灌训练的数据闭环；SkillSentry 则在 Coding Agent 里做同样的事——不假设模型一次学会后就永远稳定，而是在运行时持续检查其是否按技能过程执行。

第二个趋势是**硬实时安全与大模型智能继续分层**。Near-sensor tactile 把保护反射下沉到传感器旁，EMS 只在复杂环境才调用大 VLA；这两条路线都说明未来机器人不会让所有决策统一跑在一个巨大网络里。毫秒级碰撞/触觉响应、几十赫兹动作控制、低频语义推理应该由不同计算路径负责。

第三个趋势是**多模态和大模型系统的攻击面正在从网络世界延伸到物理世界**。场景文字可以成为 prompt injection；LiDAR 自监督表征会继承视觉教师偏差；持久语义记忆会长期保存错误事实。未来机器人安全不仅需要碰撞和急停，还需要数据 provenance、任务权限、记忆生命周期和运行时验证。

## 最值得深入研究或尝试复现的方向

1. **做一个 AutoIntervene 风格的“策略健康度 + 人工接管数据飞轮”**：对现有机器人技能记录成功轨迹的视觉/状态 embedding 与动作分布，部署时计算 support score；低于阈值先降速/暂停再请求接管。统计一周内人工真正接管时间、误报率和接管片段对下一轮策略成功率的提升。

2. **把安全反射从主计算机拆出去**：选择一个现有可用信号，如关节电流、六维力或触觉阵列，在 MCU/FPGA/实时线程上实现确定时延保护，主 AI 栈只读取状态。验收指标只看 P99 contact-to-command、P99 contact-to-motion 和主 GPU 满载时延是否仍稳定。

3. **建立多传感器健康度分层，复盘 R3LIVE 的职责分工**：对每个 LiDAR、IMU、相机/RTK 独立计算同步质量、几何可观测性和残差一致性，再决定当前权重。目标不是再加一种传感器，而是让某一模态退化时系统能明确知道“谁应该接管”。

## 参考资料

1. [LifelongCrossNav: Persistent 3D Semantic Memory for Cross-Floor Multi-Object Navigation](https://arxiv.org/abs/2608.07079) · [项目页](https://flageval-baai.github.io/LifelongCrossNavPage)
2. [Vernata: Self-Supervised Learning of LiDAR Point Representations](https://arxiv.org/abs/2608.06919) · [代码](https://github.com/rai-opensource/vernata)
3. [AutoIntervene: Calibrated Intervention for Action-Chunking Imitation Learning Policies](https://arxiv.org/abs/2608.07065) · [项目页](https://aus.bot/research/autointervene/)
4. [Near-sensor Computing for Rapid Visuotactile Perception](https://arxiv.org/abs/2608.05725)
5. [Fast and Accurate: An Adaptive VLA Inference Framework through Environment-aware Model Selection](https://arxiv.org/abs/2608.06434)
6. [Hijacking Robots with a Piece of Paper: A Systematic Study of Physical Prompt Injection in VLM-Controlled Robots](https://arxiv.org/abs/2608.05715)
7. [SkillSentry: Reliable Skill Execution for LLM Agents via Runtime Assurance](https://arxiv.org/abs/2608.09253)
8. [Plan-and-Avoid: Real-Time Aircraft Trajectory Coordination in a Multi-Agent Environment](https://arxiv.org/abs/2608.06648)
9. [R3LIVE: A Robust, Real-time, RGB-colored, LiDAR-Inertial-Visual tightly-coupled state Estimation and mapping package](https://arxiv.org/abs/2109.07982) · [官方代码](https://github.com/hku-mars/r3live)
