---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-18"
date: 2026-11-18 09:00:00 +0800
description: "EasyNav共享导航状态、Polygraph多会话优化、OrthoMark轻量回环、GHySSeg无GPU地面分割、多机器人瓶颈协调、选择性传感器、ForceHarness与DynLimit；附Linglong Agent、Codex检索及sccache实践。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-18

## 摘要

**日期：2026-11-18（Asia/Shanghai，周三；上午约09:04开始检索）。** [arXiv Robotics 原始最新列表](https://arxiv.org/list/cs.RO/new)显示最近常规公开批次为 **2026-11-17**，总计217条，其中New submissions **110条**；[Software Engineering原始最新列表](https://arxiv.org/list/cs.SE/new)总计109条，其中新提交 **55条**。总数包含Cross-list和替换版本，不可直接当作首次投稿数。

本轮先检查最近24小时，再扩展到七天。入选八项工作的原始v1分布在**11月13—16日 UTC**，因此明确标为**时间回补**，不能用“11月17日进入/new列表”冒充首发时间。选题前已读取仓库master上的任务规范与**1,382条**历史覆盖记录，按题名、arXiv ID、DOI、官方代码仓库和项目页联合核查，没有重复旧的Polaris、SAG2、SemMap、QVS-LIVO、LEASH、PolyMop等。

本期主线分为三部分。**SLAM/地图：** Polygraph研究不建统一3D地图的在线多会话轨迹图，OrthoMark用约1.9 KB的BEV频谱检索键与高度列核验回环，GHySSeg不依赖GPU做新型混合固态雷达地面分割。**导航/控制：** EasyNav用明确的共享NavState约束模块时序，多机器人窄通道协调将软全局计划交给在线MPPI，选择性位置识别避免每次都调用昂贵传感器；ForceHarness把高速力闭环放在模型之外，DynLimit区分任务要求、真实执行和验收结果。**AI工程：** Linglong Agent Service已公开多环境工具执行服务，Codex实践关注“先生成代码标识符再Grep”和通过sccache缩短重复C++编译。

**优先复现：** [EasyNav](https://github.com/EasyNavigation/EasyNavigation)、[ForceHarness](https://github.com/showlab/ForceHarness)与[DynLimit](https://github.com/Yang2581/dynlimit)都有公开代码、可定位的使用说明和相对独立的冒烟验证入口；下面的命令已核实来自官方文档，**本次没有实际下载、构建、训练、调用Codex或使用付费模型API**。GHySSeg公开了数据集DOI，但本轮Zenodo跳转不可访问，不能把数据可下载视为已独立证实。

---

## 1. EasyNav：让建图、定位、规划和控制只通过共享导航状态交互

**时间回补｜v1：2026-11-15 09:17 UTC｜arXiv:2611.19894**

### 为什么重要

传统ROS2导航栈把地图、定位、规划和控制连接在特定Topic、TF和插件时序上，扩展到多楼层、混合点云/栅格/高程图时，开发者很难判断某个控制命令使用的是哪一版感知与定位状态。EasyNav将共享**NavState**变成模块间的显式接口，并为地图、定位、规划、控制定义相容性与时序契约。算法可以替换，但不能绕过共同状态任意读取过时数据。

### 算法模块、传感器假设

~~~text
LiDAR / GPS / 里程计 / TF
               ↓
地图管理 + 定位插件 → 共享 NavState（类型、时间、版本）
               ↓
规划插件（2D Costmap / GridMap / NavMap / Octomap）
               ↓
控制与恢复插件 → 速度命令 → 底盘
~~~

它不是新LiDAR里程计，而是导航软件架构。2D/3D地图支持取决于加载的插件，ROS2消息、TF、时间同步和定位质量仍由各自组件负责。“同一个NavState”不意味着所有模块自动满足实时性，也不解决弱纹理或长走廊的物理可观测性。

### 实验指标与真实性

作者在可比条件下报告室内激光导航的**反应延迟377→33 ms**，室外GPS+3D LiDAR多层级路线的**71→8 ms**，同时报告CPU/内存开销降低。这是论文定义的导航反应时延，不是某个控制器的硬实时P99，也不能视为所有Nav2配置都慢于EasyNav。

### 源码与最小复现

[EasyNavigation主仓库](https://github.com/EasyNavigation/EasyNavigation)为Apache-2.0，官方还提供[插件集](https://github.com/EasyNavigation/easynav_plugins)、[NavMap](https://github.com/EasyNavigation/NavMap)与[Playground](https://github.com/EasyNavigation/easynav_playgrounds)。官方[安装文档](https://easynavigation.github.io/build_install/)覆盖Humble/Jazzy/Kilted/Lyrical/Rolling；各发行版APT包版本可能不同，不能混用rolling文档和旧二进制。

可以先在隔离的ROS2 Jazzy容器中克隆对应分支、安装rosdep依赖，并运行插件集自带的Kobuki或Summit仿真；同地图、同障碍、同目标点比较Nav2与EasyNav的反应时延、TF过期率、导航成功和CPU P95。**源码公开不等于本轮已完成本地构建。**

### 适合谁关注与工程落地启发

适合跨楼层巡检、三LiDAR系统和需要不同地图表达的轮式/轮足机器人。建议保持现有FAST-LIO/高精度重定位不变，仅在独立测试栈验证共享状态与模块替换，避免一次性重构稳定的整套导航。

来源：[原论文](https://arxiv.org/abs/2611.19894) · [源码](https://github.com/EasyNavigation/EasyNavigation) · [安装文档](https://easynavigation.github.io/build_install/)。

---

## 2. Polygraph：多次巡检轨迹无需先合并点云，也能在线建立跨会话一致性

**时间回补｜v1：2026-11-16 14:27 UTC｜arXiv:2611.21163**

### 为什么重要

一个机器人多次巡检同一配电室，不同时间产生的视觉/惯性轨迹都有漂移，彼此也没有共同世界坐标。多数多会话地图融合需要将所有轨迹先收齐、建立统一稠密地图再全局优化。Polygraph先将关键帧分组为局部Cluster，Cluster结束后用学习式图像检索寻找其他会话，再用稀疏匹配、公制单目深度与鲁棒位姿估计验证，最终只维护共享**Pose Graph**，不强制建统一3D地图。

### 算法模块

~~~text
会话A/B/C的视觉或VIO关键帧
               ↓
局部Cluster形成 → 跨会话图像检索
               ↓
局部特征匹配 + 深度 + 鲁棒位姿
               ↓
两级独立证据共识门
      ├─证据不足：拒绝跨会话边
      └─证据成立：添加图约束
               ↓
增量优化 + 周期性鲁棒Batch剔除错边
~~~

### 假设、实验、实时性

依赖可重复观察的视觉特征和能够提供跨帧几何的一致相机标定/深度。遮挡、极端光照和重复走廊可能导致相似检索候选；两级共识门是必要但非绝对充分的防护。作者测试了立体户外驾驶、HoloLens/iPad室内轨迹、Spot机器人及大尺度重复行走路线，报告在所比较的GPU条件下较先前方法更快、接受更少不可靠闭环边，并保持或改善轨迹精度。摘要没有统一ATE/P95数字，本期不补造。

### 工程验证

本轮未确认完整可构建的官方仓库。可以固定已有的多天巡检Pose序列及图像关键帧，先实现“候选检索→几何核验→双证据准入→GTSAM增量因子图”四段原型；**不需要把三个激光雷达的全部原始点云拼成一张巨大地图**。测试指标是错误跨会话边率、闭环召回、图优化增量耗时及最终多次经过同一位置的误差。

适合多楼层长期SLAM、重复建图与多机器人地图共享。其核心价值是**把何时相信一条跨会话约束当成显式决策**。

来源：[Polygraph论文](https://arxiv.org/abs/2611.21163)。

---

## 3. OrthoMark：用约1.9 KB的重力对齐LiDAR描述子筛选回环

**时间回补｜v1：2026-11-16 UTC｜arXiv:2611.20570**

### 为什么重要

大型点云地图的回环和重定位不能每次对每个候选执行完整3D配准。OrthoMark利用重力对齐后从上向下看的正射BEV特性：同一场景经平移/航向旋转，极坐标频谱适合进行候选检索；高度结构不适合作为全局检索键，却适合在候选对齐后核验局部对应区域。

### 算法模块

~~~text
重力对齐3D LiDAR
        ↓
BEV极坐标频谱 → 旋转/平移鲁棒检索键（约1.9 KB/帧）
        ↓
召回Top-K历史帧
        ↓
相位相关估计平面相对位姿
        ↓
每栅格16-bit高度占用掩码 + 预期观测范围重叠
        ↓
接纳或拒绝候选回环
        ↓
只有接受后才运行必要的细配准和图优化
~~~

### 实验、传感器假设与风险

论文在KITTI与多机器人序列上，报告在无需3D注册的训练无关方法中取得领先的AP，并报告相对RING++约**1/350描述子体积**、多机器人回环性能不低于比较对象。这里“1/350”比较的是特定描述子存储，**不是整张地图压缩350倍**，也不是最终定位误差减少350倍。

方法依赖重力方向、BEV栅格尺寸和高度掩码的有效性。楼层高度混叠、走廊重复结构、可见高度随距离变化，仍可能导致误匹配；相位相关初值不等于6DoF位姿已经确定。

### 最小复现与工程价值

本轮检索到一个同名图像水印项目，但**与本论文不是同一工作**，不能误引用其GitHub作为LiDAR源码；当前没有核实到这篇LiDAR OrthoMark的官方代码。

最小实验可先按论文思路做固定分辨率BEV频谱与局部高度掩码，和Scan Context、RING++对照：候选召回率、误回环、Top-K查询P95、每关键帧字节数、全局找回成功率。

适合16线/96线多LiDAR、长期重复定位及地图内存优化；应先作为**回环候选检索层**，不直接替代当前已达厘米级精度的局部点云精配准。

来源：[OrthoMark论文](https://arxiv.org/abs/2611.20570)。

---

## 4. GHySSeg：不依赖GPU，对无Ring的混合固态LiDAR进行地面分割

**时间回补｜v1：2026-11-16 UTC｜arXiv:2611.21507**

### 为什么重要

传统机械旋转雷达地面分割常按Ring、列号或固定扫描线组织数据；混合固态雷达可能没有机械式360° Ring，点云主要聚集在前向视场。如果直接照搬机械雷达的扫描线分割，许多算法在输入结构上就失效。

GHySSeg直接沿混合固态传感器的实际扫描曲线，使用**相邻高度阶跃**和**距离回折**两个几何信号推断地面/可行驶道路，不需要训练模型或GPU。

### 算法与性能

~~~text
混合固态雷达点云
      ↓
恢复/跟踪实际扫描曲线
      ↓
高度阶跃 + 距离回折特征
      ↓
候选地面和道路区域
      ↓
几何连续性校验与输出
~~~

作者发布HySoLiD-Drive基准，含**100帧人工标注、7,000帧未标注**真实驾驶记录。报告道路IoU **0.907**、地面IoU **0.896**，Precision超过0.96，**单CPU核心约22 ms/帧**。这些是指定混合固态雷达与道路数据上的结果，不等于RoboSense Helios或iRay 96线的直接性能。

### 可复现性、风险与工程落地

[论文](https://arxiv.org/abs/2611.21507)给出[HySoLiD-Drive数据集DOI](https://doi.org/10.5281/zenodo.21705196)，但**本轮Zenodo DOI跳转无法通过网页工具访问**；不能声称已下载数据。完整算法源码同样未独立确认。

若用于多LiDAR平台，必须先检查点云消息是否保留扫描曲线顺序和必要采样元数据。无曲线顺序的拼接点云不能保证直接适用。验证时对比Patchwork++/RANSAC地面分割，统计斜坡误检、低矮障碍误剔除、CPU耗时与不同视场覆盖；**不要把误分割的“地面”直接作为最终通行保证**。

适合前向固态LiDAR、CPU边缘设备与地形语义前端。

来源：[原论文](https://arxiv.org/abs/2611.21507) · [数据集DOI](https://doi.org/10.5281/zenodo.21705196)。

---

## 5. Passage-Focused Soft Coordination：5—30台机器人会车，以瓶颈通道为协调单位

**时间回补｜v1：2026-11-13 19:31 UTC｜arXiv:2611.18877**

### 为什么重要

多机器人在门洞、单车道和狭窄走廊之间移动时，硬性预留每个时间槽会被实际执行偏差破坏；完全独立的局部避障又容易两车相互礼让形成死锁。

该框架把地图分解为一组凸区域形成的通道图，先按通道使用方向与优先级进行软全局协调；再沿选定通道执行连续时空规划，使用MPPI做在线避碰；当真实执行偏离参考时局部调节，必要时选择性重规划，不要求严格执行整条预先预约的轨迹。

### 算法模块

~~~text
地图几何 → Convex Set Passage Graph
                  ↓
       线路方向/优先级软协调
                  ↓
       时间冲突代价 + 参考轨迹
                  ↓
      在线 MPPI + 可调时间/几何容差
                  ↓
       仅局部冲突时重新规划
~~~

### 实验与边界

作者在四种环境、**1,200个实例、每组5—30台机器人**的仿真中报告接近全成功，并在**8台真机**实验中完成所有所测试次且未发生碰撞。论文没有提供足够信息支持“在任意现场100%不碰撞”的说法。

MPPI局部控制仍需要正确的机器人尺寸、动力学、位置通信和冲突检测；优先级机制不等于物理急停。完整复现代码尚未独立确认。

### 最小复现与适合谁关注

优先在二维双走廊/单门洞地图搭建5台差速机器人，比较独立MPPI、全局刚性预约和软通道协调。统计通行总耗时、Flowtime、死锁次数、机器人间最小净空、规划P95与执行时差。多台楼宇巡检机器人共享电梯口、配电室门洞时，优先在任务层设置通道资源，并让局部控制保留必要的实时灵活性。

来源：[原论文](https://arxiv.org/abs/2611.18877)。

---

## 6. Selective Sensor Acquisition：次要传感器仅在位置识别确有需要时启动

**时间回补｜v1：2026-11-16 08:36 UTC｜arXiv:2611.20730**

### 为什么重要

多模态Place Recognition的常见做法是每次定位查询都计算摄像头、LiDAR、语义等全部描述子。但当主要传感器已经足够可靠时，额外计算不一定带来更多正确信息，还会占用CPU/GPU、带宽和能耗。

该研究把次级传感器获取率作为**可控制的目标**，根据主传感器当前匹配分数，在线调节触发阈值，优先把第二传感器的预算花在最不可靠的查询上。

### 算法模块

~~~text
主传感器Place Recognition匹配分数
             ↓
在线估计当前PR可靠性
             ↓
按目标预算更新触发阈值
   ├─可靠：使用主传感器结果
   └─不可靠：获取/计算次级传感器
             ↓
融合候选匹配并验证回环
~~~

### 数字与适用边界

作者在不同数据、描述子和传感器组合上报告：**次级传感器调用25%**时可恢复全部可用融合增益的**55%**；调用50%时恢复**81%**。这里“55%/81%”是原本全部融合能带来的**PR性能增益比例**，不是直接宣称总体识别正确率55%或81%。

它假设主PR输出具有可用于排序的分数；若主传感器在陌生环境持续过度自信，门控也可能放弃真正有价值的次级观测。论文尚未确认完整可运行源码。

### 最小复现与工程启发

在相同多雷达/相机数据上，模拟调用全部传感器、只调用主LiDAR、按分数阈值25%和50%预算调用次级雷达。测Recall@1/Top-K、错误回环接受率、描述子计算P95、GPU占用和新地点失败率。**三雷达融合不一定要三路点云永远全量参与每一次定位更新**；可以先把选择门控用于全局重定位候选评估。

来源：[原论文](https://arxiv.org/abs/2611.20730)。

---

## 7. ForceHarness：把高频接触力闭环放到模型之外，再把物理量作为Tool Result返回

**时间回补｜v1：2026-11-16 UTC｜arXiv:2611.21099**

### 为什么重要

前沿多模态模型不可能以电机控制频率持续判断每一帧力传感器，也不擅长直接读取成百上千个原始力采样点。ForceHarness让冻结模型只决定“按压、推拉、插入、搜索接触”等高级动作；下面的确定性控制器自动调节接触力，并在达到接触、停止或阻力突变等事件时自行结束。上报模型的是质量、摩擦、刚度、接触高度等**有单位、有不确定性**的物理判断，而非原始波形。

### 算法模块与传感器假设

~~~text
冻结LLM/VLM → 高层力技能请求
              ↓
局部力闭环：阻抗/导纳 + 自终止事件
              ↓
腕部力传感器，或通过关节外力矩与Jacobian估计
              ↓
偏置校准、物理量估计、误差范围
              ↓
Tool Result：重量/摩擦/刚度/卡滞状态
              ↓
下一次高层模型判断
~~~

无腕部六轴力传感器并不等于每台机械臂都能精确估力；仍取决于可用外力矩接口、摩擦补偿、关节模型和姿态激励。

### 实验与重要限定

在真实Franka FR3、无腕部独立力传感器、六种任务每项10次的实验中，使用相同模型和安全限制，作者报告**无力接口2/60（3.3%）→ ForceHarness 54/60（90.0%）**。HiddenPhys含七个MuJoCo任务；项目页区分了开发时使用过的随机种子与独立留出种子，不能把所有平均值当成盲测。力闭环成功不等于生产机械臂的功能安全证明。

### 已有开源与真实最小复现

[showlab/ForceHarness](https://github.com/showlab/ForceHarness)为MIT，公开核心、HiddenPhys模拟器、离线测试、监控与[Codex可阅读的配置Skill](https://github.com/showlab/ForceHarness/blob/main/skills/forceharness-setup/SKILL.md)。作者README提供以下**完全不调用付费模型**的首步：

~~~bash
git clone https://github.com/showlab/ForceHarness.git
cd ForceHarness
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install -e ".[sim]"
python -m forceharness.doctor
python -m pytest -q
python scripts/run_episode.py --task weight_sort --agent scripted --backend fake
~~~

后续接入前沿模型或真机需要API凭据、额外依赖、独立安全审查及人类授权。本轮**没有启动模拟器、没有API调用、没有动真机**。

### 工程落地启发

适合力控机械臂、VLA工具接口、接触失败恢复以及SIP/机器人状态机的“事件驱动而非等时轮询”思想。对于只暴露速度控制/登梯模式的厂商SDK，不要假定可直接执行其全部底层力控制技能。

来源：[论文](https://arxiv.org/abs/2611.21099) · [项目页](https://showlab.github.io/ForceHarness/) · [源码](https://github.com/showlab/ForceHarness)。

---

## 8. DynLimit：驾驶/运动控制的三个问题必须分别验收——要求、执行、任务是否完成

**时间回补｜v1：2026-11-15 04:23 UTC｜arXiv:2611.19785**

### 为什么重要

对极限工况运动控制，轨迹规划器提出“穿过狭窄障碍”只是一个要求；控制系统实际可能因轮胎打滑、控制饱和或参考修正而执行另一条轨迹；最后是否达到任务终点又是第三件事。只看最终碰撞率或侧偏角峰值，不能判断失败具体发生在哪一层。

DynLimit将道路、摩擦、障碍、参考目标组成任务场景，提供统一计划/控制/车辆动力学接口，并在日志中分别记录要求、真实执行和任务规则的结果。

### 模块与实证

~~~text
场景定义 + 摩擦条件 + 任务约束
                 ↓
规划器/控制器 → 统一车辆接口
                 ↓
Mock四轮模型或可选的商业CarSim
                 ↓
同步记录参考/实际轨迹/事件
                 ↓
任务准则、重放与诊断报告
~~~

作者在8类任务、3种摩擦环境和3组参考控制链上执行**450次**实验（360次名义、18次局部细化、72次初始偏差）。这不是450次真机实验。论文强调两个方法有相同的“通过总数”也可能通过完全不同的工况单元。

### 源码和最小工程入口

[Yang2581/dynlimit](https://github.com/Yang2581/dynlimit)提供Python后端、Vite前端和无CarSim许可也能运行的Mock植物模型。项目README当前的快速启动示例主要以Windows PowerShell写成，Linux移植需要独立验证，不能谎称已在Arch跑通。按当前官方snapshot对应目录进入后：

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
dynlimit-api

# 第二终端进入frontend目录
npm install
npm run dev
~~~

HTTP服务默认127.0.0.1:8000，Web开发页面通常5173。CarSim不是必需，但高保真工况需要用户自备许可证与模型。不要将Mock仿真结果当作高保真动力学或硬件安全认证。

### 工程启发

适合轮式底盘高加速度避障、MPC和模型失配回归。可以把它的**期望动作—实际动作—任务是否完成**三段审计思路迁移到现有机器人验证：控制器与路径规划器分别记录约束违反、跟踪偏差和到达状态，而不是只看“任务完成”。

来源：[DynLimit论文](https://arxiv.org/abs/2611.19785) · [官方代码](https://github.com/Yang2581/dynlimit)。

---

## AI / LLM 附属框架与开源工程组件

### 组件 1｜Linglong Agent Service：推理集中、工具执行留在各台机器的轻量运行时

**时间回补｜v1：2026-11-16 UTC｜[论文](https://arxiv.org/abs/2611.21129) · [MIT源码](https://github.com/mz24cn/agents)**

#### 它解决什么问题

一个Coding Agent如果同时管理Linux开发机、Windows测试机和远程ARM设备，不宜把所有文件系统与Shell工具都转发到中心服务执行。Linglong在母端管理推理、会话、模型和工具描述；每次推理选择一个子环境，文件、Shell、终端、MCP等工具在选定子端执行，支持直连HTTP与子端主动WebSocket隧道。还有客户端工具应答、断点会话、在线调试的设计。

~~~text
中心：模型 / 对话历史 / 工具声明
                ↓
会话选择目标执行环境
    ├─Linux开发机：源码与编译
    ├─Windows：软件/GUI测试
    └─ARM板：只读诊断与测试
                ↓
工具结果返回母端，继续推理
~~~

#### 最低运行入口与工程边界

仓库README说明核心Python运行时主要基于标准库，完整Web/MCP相关功能要求Python 3.10+。首先仅在环回地址启动并阅读源码和示例：

~~~bash
git clone https://github.com/mz24cn/agents.git
cd agents
python app.py 127.0.0.1:7988
# 再阅读 docs/introduce-remote-execution.md 和 examples/
~~~

**不要仅凭“零第三方依赖”便认为已有隔离沙盒、默认鉴权或者可安全开放公网。** 远程子环境权限应由操作系统用户、网络ACL、容器和独立审批控制。论文明确说现有证据证明的是**执行契约与回归测试**，并不证明比Codex/T3 Code更快、更可靠或具备生产级故障恢复。部分运行时补丁能力尚未实现。

#### 对Codex/T3 Code的用途和A/B

这不是Codex的直接替代品。可把其“模型留在中心、工具留在设备”的协议和状态恢复思路用于多机器研发。选三个只读任务：读取ARM板传感器信息、Windows侧查看测试结果、Linux侧检查编译错误。测失败边界、会话恢复与权限审计。确认收益后再考虑写工具；**不默认授权远程任意Shell**。

来源：[Linglong论文](https://arxiv.org/abs/2611.21129) · [作者源码](https://github.com/mz24cn/agents) · [远程执行说明](https://github.com/mz24cn/agents/blob/main/docs/introduce-remote-execution.md)。

---

## AI Coding 实战技巧精选

### 技巧 1｜Codex先生成可能的代码标识符，再用rg验证，不要立即引入向量数据库

- **来源**：Xue等，2026-11-16，[Embeddings vs. Grep原论文](https://arxiv.org/abs/2611.20455)；[ripgrep官方仓库](https://github.com/BurntSushi/ripgrep)。
- **一句话结论**：描述故障的自然语言往往不包含仓库实际函数名。先让Codex生成**需要验证的候选术语**，再用确定性文本工具查询真实源码；结果为空时再考虑LSP、AST或语义检索。
- **具体怎么做**：
  1. 给Codex一条真实Bug描述，要求先只输出10个以内可能的函数名、结构体、错误枚举、Topic或API关键字，不允许编造文件路径为事实。
  2. 对候选执行只读搜索，例如：

~~~bash
rg -n -i '(register|catalog|subscribe|timeout|retry)' src/ include/ --glob '*.{cpp,h,hpp,cc}'
~~~

  3. 根据搜索结果再查真实定义/调用者、检查相应CMake目标；不要把猜出的标识符当作已证实的符号。
  4. 与直接一句自然语言要求读仓库、纯rg和现有索引MCP做对照：比较**首次正确文件命中、查找耗时、读入Token与误定位**。
- **适合什么场景**：Codex、ROS2 C++、GB28181/SIP大型源码、历史Bug定位和大仓库。
- **注意**：论文构建Repo-Premium真实代码搜索基准，在若干Python检索池里“生成标识符再Grep”的词项检索可以追上Dense检索；**不能外推为所有语言和查询都优于向量检索**。本轮没有运行Codex。

### 技巧 2｜用sccache缓存Codex反复触发的C++编译，按实际命中率A/B

- **来源**：[Mozilla sccache官方源码及说明](https://github.com/mozilla/sccache)；[CMake编译启动器文档](https://cmake.org/cmake/help/latest/variable/CMAKE_CXX_COMPILER_LAUNCHER.html)。
- **一句话结论**：对于反复调试同一ROS2/C++仓库的Codex会话，相比一味精简日志，先避免重复编译未变化的翻译单元可能更直接。
- **具体怎么做**：
  1. 在开发机安装并运行受信任的sccache二进制；先确认sccache、CMake和编译器版本。
  2. 在新的**隔离Build目录**启用编译启动器：

~~~bash
cmake -S . -B build-cached -G Ninja   -DCMAKE_BUILD_TYPE=RelWithDebInfo   -DCMAKE_C_COMPILER_LAUNCHER=sccache   -DCMAKE_CXX_COMPILER_LAUNCHER=sccache
cmake --build build-cached -j 8
sccache --show-stats
~~~

  3. 对同一个模块进行一次真实的小改动，让Codex只运行相关目标编译；同时保留一个未缓存Build目录做对照。
  4. 记录**编译耗时、缓存命中率、失败率和测试通过**，比较工作树路径变化、头文件修改和编译参数变动时的效果。
- **适合什么场景**：Arch Linux、CLion、ROS2、C++/CUDA项目和T3 Code多Worktree工作流。
- **注意**：不同编译选项、绝对路径或生成代码会降低命中；不建议为每个小任务建立复杂分布式缓存基础设施。sccache**不替代编译检查**，也不会让代码自动正确。

---

## 经典论文回顾

### Shortest Paths in Graphs of Convex Sets — Marcucci、Umenberger、Parrilo、Tedrake

**历史位置：** [初稿2021-01-27](https://arxiv.org/abs/2101.11565)，2024年发表于 *SIAM Journal on Optimization* 34(1):507–532；[正式DOI](https://doi.org/10.1137/22M1523790)。

### 核心问题与数学思想

普通Dijkstra最短路把每个节点视作一个离散位置；机器人运动规划中的一个“通道节点”却可以是一整块**凸可行区域**，进入与离开该区域的位置都需要优化。Graph of Convex Sets（GCS）将每个图节点关联一个凸集、每条边关联凸代价与耦合条件，同时优化**走哪些区域**与**在区域内从哪里通过**。

~~~text
非凸自由空间
      ↓
多块凸区域 + 允许穿行的连接边
      ↓
图上的离散路线选择 + 连续通行变量
      ↓
透视函数与混合整数凸优化
      ↓
候选全局路径 / 代价界与可行性证明
~~~

原问题一般是NP-hard。凸松弛能提供有用下界、也可能构造高质量路径，但**不能说所有GCS实例都能在多项式时间找到全局最优**。其价值是将组合选择与连续轨迹优化联系起来，并让求解器提供可比较的界。

### 当年重要性、传感器与动力学假设

这是一篇规划/优化理论论文，本身不依赖特定LiDAR，也不解决机器人在地图中的定位。使用GCS前需要上游提供可靠的障碍模型和凸区域分解；动态障碍、多机器人时序、非完整约束及接触模式通常需要新增表示和近似。

现代Drake及多机器人通道规划延伸了这条路线。今天Passage-Focused Soft Coordination把瓶颈通道表示为凸区域图，再用在线MPPI应对执行偏差；它并不自动继承任意GCS求解的所有理论保证。

### 开源复现与仍在使用的思想

可参考[Drake的GCS规划文档](https://drake.mit.edu/)、[原论文](https://arxiv.org/abs/2101.11565)，先在二维有两个绕障通道的地图中构造凸集图，和网格A*、采样式RRT比较路径代价、耗时和局部障碍净空，再加入两个机器人共用瓶颈通道的时间冲突。Drake是现代工程库，不是原始论文的独立逐行复刻。

**对轮式巡检的重新解读：** 地图建得越细不一定越好。重要的是从几何地图抽取真实瓶颈、可通行区域和动作能力，把连续轨迹优化集中到少数物理上关键的通道，而不是让每个点云点都成为规划状态。

---

## 今日结论

本期最值得投入验证的三个对象是：

**EasyNav**：已经公开ROS2导航核心、插件和Playground，适合在不动原有FAST-LIO的前提下，与Nav2对比多楼层路线的数据契约和响应延迟。

**ForceHarness**：提供完整开源的离线假后端和MuJoCo验证，不调用任何付费模型就能检查高频力控制技能与事件式返回。模型只负责高层判断、底层决定实际连续执行的思想，也可以帮助改进其他机器人Agent状态机。

**OrthoMark与选择性传感器**：分别从**回环描述子字节数**与**是否需要调用第二传感器**两个角度控制多雷达定位的计算开销。对已经具有高精度局部匹配的系统，先做辅助候选检索与门控A/B，比全量替换地图与优化后端更稳妥。

在Codex工作流中，先通过“生成候选标识符→rg核实”减少无关读文件，再用sccache缓存反复编译；评估的是实际Bug定位、测试和交付质量，而不是仅看消耗Token下降。没有需要为另一家Coding CLI发布修复公告来充数的理由。

---

## 最值得深入研究或尝试复现的方向

| 优先级 | 方向 | 最小验收 |
|---|---|---|
| P0 | EasyNav与Nav2 | 相同Gazebo路线的反应延迟、TF过期、CPU与P95 |
| P0 | ForceHarness | fake后台、离线pytest、力技能退出条件和无付费API执行 |
| P0 | Codex + sccache | 重复构建命中率、相关模块真实编译时间及回归测试 |
| P1 | OrthoMark | 1.9KB候选描述子、Top-K回环召回、误接受及检索P95 |
| P1 | Polygraph | 多会话错闭环拒绝率、图更新成本和独立证据准入 |
| P1 | 选择性多传感器 | 次级传感器25%/50%预算下的定位候选质量 |
| P1 | 多机器人软通道协调 | 狭窄门洞死锁、Flowtime、最小净空和实际时差 |
| P1 | GHySSeg | 可用数据与扫描曲线元数据、CPU 22ms对照、地面误剔除 |
| P1 | DynLimit | Mock模型450次任务思路：要求/执行/结果三类独立报告 |
| P1 | Linglong Agent | 远程工具最小权限、隧道重连、会话边界和操作审计 |
| P2 | GCS经典算法 | 凸集分区质量、混合离散连续规划与动态避障 |

## 参考资料

**最新列表：** [arXiv Robotics](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/new)。

**SLAM与地图：** [EasyNav论文](https://arxiv.org/abs/2611.19894) · [EasyNav源码](https://github.com/EasyNavigation/EasyNavigation) · [Polygraph](https://arxiv.org/abs/2611.21163) · [OrthoMark](https://arxiv.org/abs/2611.20570) · [GHySSeg](https://arxiv.org/abs/2611.21507) · [选择性传感器](https://arxiv.org/abs/2611.20730)。

**规划控制与Bench：** [多机器人软通道协调](https://arxiv.org/abs/2611.18877) · [ForceHarness](https://arxiv.org/abs/2611.21099) · [ForceHarness代码](https://github.com/showlab/ForceHarness) · [DynLimit](https://arxiv.org/abs/2611.19785) · [DynLimit代码](https://github.com/Yang2581/dynlimit)。

**LLM与Codex：** [Linglong Agent论文](https://arxiv.org/abs/2611.21129) · [Linglong源码](https://github.com/mz24cn/agents) · [Embeddings vs. Grep](https://arxiv.org/abs/2611.20455) · [ripgrep](https://github.com/BurntSushi/ripgrep) · [sccache](https://github.com/mozilla/sccache)。

**经典论文：** [Shortest Paths in Graphs of Convex Sets](https://arxiv.org/abs/2101.11565) · [SIAM DOI](https://doi.org/10.1137/22M1523790)。

