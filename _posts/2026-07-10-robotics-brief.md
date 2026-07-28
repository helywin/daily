---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-07-10"
date: 2026-07-10 09:00:00 +0800
description: "今天值得重点关注的是三条主线：一是 SLAM 里的 3DGS 正在从“漂亮渲染”转向“几何可用、实时可用、可压缩”；二是控制方向继续把 MPC / MPPI / Safe RL 往“真实机器人约束、安全滤波、模型误差自适应”推进；三是 AI coding agent 和大模型更新明显进入工程化阶段，重点不再只是写代码，而是浏览器验证、企业管控、可观测性、成本与多模型路由。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

## 摘要

今天值得重点关注的是三条主线：一是 SLAM 里的 3DGS 正在从“漂亮渲染”转向“几何可用、实时可用、可压缩”；二是控制方向继续把 MPC / MPPI / Safe RL 往“真实机器人约束、安全滤波、模型误差自适应”推进；三是 AI coding agent 和大模型更新明显进入工程化阶段，重点不再只是写代码，而是浏览器验证、企业管控、可观测性、成本与多模型路由。

## 1. GeoGS-SLAM：3DGS SLAM 不一定要做外观，几何才是机器人最需要的

GeoGS-SLAM 提出 Geometry-Only Gaussian Splatting，用只保留空间几何参数的 Gaussian 表示做稠密单目 SLAM。论文称相比常规 3DGS，GeoGS 每个 primitive 的参数量减少超过 80%，并更关注导航、避障、重建所需的几何一致性，而不是 novel view synthesis 的照片级外观。论文于 2026-07-08 提交。(arxiv.org)

### 为什么重要
这很符合机器人实际需求。大多数移动机器人并不需要“好看的 NeRF/3DGS 渲染图”，而是需要可用于定位、避障、路径规划的几何地图。GeoGS-SLAM 的方向说明 3DGS SLAM 正在摆脱“渲染优先”的研究惯性。

### 适合关注
视觉 SLAM、3DGS 建图、室内机器人、低成本单目/鱼眼建图、地图压缩。

### 工程启发
如果你做机器人建图，可以考虑把 3DGS 用作“几何地图后端”：前端仍用 VIO / LIO 保证实时轨迹，后端用 geometry-only Gaussian 做稠密几何精修。落地风险主要是单目尺度、动态物体污染、回环一致性和在线算力。

## 2. PLED-VINS：事件相机 + 点线特征，用可靠性权重处理动态环境

PLED-VINS 是一个 monocular event camera-based VINS，针对动态物体和快速运动导致的视觉 SLAM 退化。它同时使用点特征和线特征，并构建 entropy-recency score map 来估计特征的时间可靠性，再结合几何可靠性做 point-line robust bundle adjustment 和自适应加权。论文已接收 IROS 2026。(arxiv.org)

### 为什么重要
事件相机天然适合高速运动、高动态范围场景，但很多 event SLAM 仍默认静态环境。PLED-VINS 把“特征是否可信”显式建模，这比简单 RANSAC 剔除动态点更细。

### 适合关注
动态环境 VIO、无人机高速飞行、机器狗快速运动、低光/强光变化场景、事件相机 SLAM。

### 工程启发
即使不用事件相机，也可以借鉴它的“时间可靠性 + 几何可靠性”思想：给 LiDAR / 视觉 / 反光板 / RTK 因子都加健康度，而不是直接塞进后端。对动态环境，后端优化要能区分“长期稳定结构”和“短时可疑观测”。

## 3. Real-Time LiDAR Gaussian Splatting SLAM：LiDAR 版 3DGS 开始逼近实时工程形态

Real-Time LiDAR Gaussian Splatting SLAM 把 fast G-ICP registration 和 spherical rasterization-based dense mapping 结合起来，用 LiDAR 几何初始化 Gaussian，包括 range-aware scale、surface normal 和局部 covariance。论文称在 Newer College 数据集上用在线轨迹达到 >20 FPS，并获得 86.78% F-score。(arxiv.org)

### 为什么重要
这条线比纯视觉 3DGS 更接近移动机器人落地。LiDAR 的几何精度、尺度稳定性和抗光照能力更适合做长期定位地图；如果能实时跑，后续可以替代一部分传统 voxel / surfel mapping。

### 适合关注
LiDAR SLAM、LIO 后端、稠密点云地图压缩、室外巡检、长距离建图。

### 工程启发
可尝试“LIO 前端 + LiDAR Gaussian map 后端”：FAST-LIO / LIO-SAM 提供实时轨迹，Gaussian map 用于局部几何重建、地图压缩和可视化。风险是动态点、雨雾粉尘、多雷达融合，以及地图更新/裁剪策略。

## 4. RC-MPPI + Safe RL with MPC：安全控制正在从固定惩罚走向“模型误差自适应”

RC-MPPI 针对 MPPI 在模型-真实系统不匹配时安全边界不稳定的问题，用 prediction-execution residual 在线调节约束收紧、安全代价和采样温度。模型越不准，控制器越保守，避免过度相信 rollout 的低 cost 结果。(arxiv.org)

另一篇 Safe Reinforcement Learning using Ideas from MPC 则用离线 MPC 计算安全可行状态-动作空间，并在训练和部署时把 RL 动作投影到该可行集，作为安全滤波器。论文在非线性 1-DoF 物理平台上验证了安全探索和稳定收敛。(arxiv.org)

### 为什么重要
真实机器人里，模型误差不是例外，而是常态。固定碰撞惩罚、固定 safety margin、固定 RL reward 很容易在高速、载荷变化、轮胎/脚端打滑、气流扰动时失效。

### 适合关注
MPC、MPPI、Safe RL、无人机绕障、机械臂避障、机器狗运动控制。

### 工程启发
做 MID360 无人机或机器狗局部规划时，可以把“预测轨迹 vs 实际执行轨迹残差”作为安全调节量：残差增大时缩短 horizon、提高障碍物安全距离、降低速度上限、增大采样温度或切到保守控制器。

## 5. PSDF-MPC：局部规划瓶颈越来越像“几何约束计算问题”

GPU-Accelerated Polygonal Signed Distance Functions for Real-Time Collision Avoidance 提出 PSDF：机器人 footprint 用凸多边形，障碍物用边界边表示，GPU 批量计算距离和梯度，CPU 解稀疏 QP。论文称在密集多边形环境中仍能保持实时避障。(arxiv.org)

### 为什么重要
很多机器人局部规划失败，不是 MPC 理论不行，而是碰撞约束太慢、footprint 过度简化。圆形膨胀 costmap 对长条形机器人、四足机器人、带机械臂平台都太粗。

### 适合关注
MPC 局部规划、狭窄通道避障、AMR、机器狗、非圆形 footprint 机器人。

### 工程启发
如果你的机器人不是圆形底盘，应尽量从“圆形安全半径”升级到“多边形 footprint + 可微距离约束”。工程风险是 GPU/CPU 同步延迟、障碍边界提取质量，以及动态障碍预测不稳定。

## 6. VLA-Corrector / LingBot-VLA 2.0：VLA 落地重点转向 action horizon、预测和全身动作空间

VLA-Corrector 针对 action chunk 策略的开环盲区：VLA 一次预测多个未来动作后，如果真实视觉变化偏离预测，就会累积错误。它不改 backbone，而是用 Latent-space Vision Monitor 检测预测视觉特征与实际视觉特征的偏差，一旦持续偏离，就截断剩余动作并触发重新规划。(arxiv.org)

LingBot-VLA 2.0 则强调真实应用中的 VLA 工程化：约 60,000 小时预训练数据，其中 50,000 小时机器人轨迹覆盖 20 种机器人配置，另有 10,000 小时 egocentric human video；动作空间扩展到头、腰、移动底盘和灵巧手，并加入未来预测作为 temporal reasoning 的 proxy task。(arxiv.org)

### 为什么重要
VLA 真接机器人时，问题不是“能不能生成动作”，而是动作 chunk 多久执行一次、什么时候中断、偏差怎么检测、如何接底层控制器。

### 适合关注
机器人基础模型、VLA、diffusion policy、flow matching policy、机械臂/双臂/移动操作。

### 工程启发
部署 VLA 时建议默认加三层安全壳：视觉/状态偏差监测、action chunk 动态截断、传统 MPC/WBC/PID 执行层。不要让 VLA 直接长期闭眼执行，尤其是接触丰富或近障任务。

## 7. GPT-5.6 / Grok 4.5 / Copilot：AI coding agent 进入“多模型 + 企业治理 + 浏览器验证”阶段

OpenAI 于 2026-07-09 发布 GPT-5.6，分为 Sol、Terra、Luna 三档：Sol 是旗舰，Terra 偏低成本高性能，Luna 偏最快和最便宜。OpenAI 表示 GPT-5.6 已开始在 ChatGPT、Codex 和 API 中逐步可用，并给出 API 价格：Sol $5/M input、$30/M output；Terra $2.5/M input、$15/M output；Luna $1/M input、$6/M output。(openai.com)

GitHub 同日宣布 GPT-5.6 Sol/Terra/Luna 正在进入 GitHub Copilot；Sol 面向大代码库复杂推理和长时间 agentic work，Terra 作为日常 agentic coding 平衡默认，Luna 面向快速低成本任务。企业/Business 管理员需要显式开启相关策略。(github.blog)

xAI 也在 2026-07-08 发布 Grok 4.5，定位 coding、agentic tasks 和 knowledge work，官方页面强调较高 token efficiency、80 TPS 服务速度，并给出 $2/M input、$6/M output 价格。(x.ai)

同时，GitHub Copilot in VS Code 的 6 月更新把 agentic browser tools GA：agent 可导航页面、读取内容、截图并验证 Web App；Agents window 支持并行 session 和多 chat。(github.blog) GitHub 还发布了 MDM / 文件配置的企业托管 Copilot 设置，以及企业托管 OpenTelemetry export，方便组织统一管控 Copilot CLI / VS Code agent 的策略与审计数据。(github.blog) (github.blog)

### 为什么重要
AI coding agent 正从“IDE 里补代码”变成“能看网页、跑验证、并行处理任务、进入企业治理系统”的研发执行层。模型竞争点也从 benchmark 扩展到上下文、工具调用、缓存、推理速度、审计和成本。

### 适合关注
vibe coding、Codex / Copilot / Cursor、研发平台、DevSecOps、企业 AI 治理。

### 工程启发
真实研发流程建议采用：一个任务一个隔离 worktree；agent 可读但默认不可写生产系统；浏览器域名白名单；MCP server 白名单；所有命令、文件修改、测试、token 成本、工具调用都进日志；PR 前必须跑 lint、test、secret scan、依赖审计和人工 review。

## 结论

今天最值得跟进的是：SLAM 地图表示正在向“轻量几何 3DGS + 实时 LiDAR Gaussian map”靠拢；控制方向正在把 MPPI/MPC/RL 的安全性从固定规则升级为残差自适应和安全可行集；VLA 正在补真实机器人部署最关键的 action horizon 和偏差修正；AI coding agent 则正式进入工程治理和组织级管控阶段。

## 建议深入研究 / 复现的 3 个方向
LIO + LiDAR Gaussian map 最小闭环
用 FAST-LIO2 / LIO-SAM 作为实时前端，离线或半在线构建 Gaussian 几何地图，比较 voxel map、surfel map、Gaussian map 在地图大小、重定位精度、动态点残留上的差异。
MPPI 残差自适应安全层
给现有 MPPI / MPC 增加 prediction-execution residual 监控：残差大时缩短 horizon、降低速度、提高安全距离、切换保守模式，优先用于无人机绕障或机器狗高速避障。
VLA action chunk 安全执行器
不急着重训 VLA，先在推理层加入视觉偏差检测、chunk 截断、jerk 限制和传统控制器兜底。这个方向对真实机械臂、机器狗、无人机端到端控制都更实用。

## 参考资料

- [GeoGS-SLAM](https://arxiv.org/search/?query=GeoGS-SLAM&searchtype=all)
- [PLED-VINS](https://arxiv.org/search/?query=PLED-VINS&searchtype=all)
- [Real-Time LiDAR Gaussian Splatting SLAM](https://arxiv.org/search/?query=Real-Time%20LiDAR%20Gaussian%20Splatting%20SLAM&searchtype=all)
- [RC-MPPI + Safe RL with MPC](https://arxiv.org/search/?query=RC-MPPI%20%2B%20Safe%20RL%20with%20MPC&searchtype=all)
- [PSDF-MPC](https://arxiv.org/search/?query=PSDF-MPC&searchtype=all)
- [VLA-Corrector / LingBot-VLA 2.0](https://arxiv.org/search/?query=VLA-Corrector%20/%20LingBot-VLA%202.0&searchtype=all)
- [GPT-5.6 / Grok 4.5 / Copilot](https://github.com/search?q=GPT-5.6%20/%20Grok%204.5%20/%20Copilot&type=repositories)

> 说明：历史聊天导出文本没有保留原始超链接，上述链接为按论文或项目名称生成的官方站点/学术检索入口；后续日报将直接保存原始论文、GitHub 与官方发布链接。
