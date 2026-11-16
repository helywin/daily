---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-16"
date: 2026-11-16 09:00:00 +0800
description: "SemMap 越野语义地图、DroneDiffusion 感知可靠性规划、APG-Planner 高速飞行、DIVAL 非完整约束、耦合 CBF、任务主动感知、神经 MPC 及 BWM-Forge；另附 Polaris 本地检索与 Codex 工具实践。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-16

## 摘要

**日期：2026-11-16（Asia/Shanghai，星期一）；检索基准约北京时间 09:00。** arXiv cs.RO 和 cs.SE 的最新可核查常规公开批次均为 **2026-11-13（星期五）**：cs.RO 总计 164 条，其中新提交 91 条；cs.SE 总计 86 条，其中新提交 39 条。总数包括交叉收录与替换版本，并不全部是首次投稿（[cs.RO](https://arxiv.org/list/cs.RO/new)；[cs.SE](https://arxiv.org/list/cs.SE/new)；[cs.RO recent](https://arxiv.org/list/cs.RO/recent)）。

首先检查最近 24 小时；由于周末没有新的常规 arXiv 批次，扩展至 7 天。八篇主动态原始 v1 均在 **2026-11-11—12 UTC**，全部明确标记为**时间回补**。选题前已读取仓库 master 最新规范与既有 **1,357 条**覆盖索引，按照标题、arXiv ID、DOI、仓库及项目主页联合去重；下列八项均未在既有索引登记。

**今天的判断：** 对机器人最有落地价值的，不只是模型变强，而是语义可通行性真正接入地图、视觉失效被纳入规划成本、非完整约束下保持初始航向连续、交互避障能同时处理安全与死锁、长任务主动补拍被遮挡的物体。对 AI 工作流，优先选择本地检索、确定性写入边界检查、真实源代码变更验证，而不是其他 Coding CLI 版本通知。

**复现优先级：** ① [SemMap ROS2 源码](https://github.com/rai-opensource/sem_map)（须注意仅限非商业研究许可），② [Polaris 本地 MCP](https://github.com/girard-g/polaris)，③ [BWM-Forge](https://github.com/Lcixs/BWM-Forge)（有代码，但依赖 Blender、模型 API 与视频生成服务）。本次只核实原始资料与公开运行入口，**没有替用户下载模型、实际训练或调用 Codex**。

---

## 1. Autonomous Trail Racing + SemMap：DINOv3 轻量解码器融合 LiDAR，实时构建越野可通行地图

**时间回补｜v1 2026-11-11 UTC｜arXiv:2611.15280**

### 为什么重要

对于在复杂地形上移动的机器人，单纯的几何高程地图无法完全区分“能开过去的泥土”“危险碎石”“合法的林间小径”；但把语义网络直接作为全身运动控制器，也会降低可解释性。RAI Institute/ETH 的越野自行车机器人将语义地形作为导航与运动控制共同使用的表示，真实自行车机器人完成了约 **959 m** 的无先验山地赛道，平均 **3.26 m/s**、峰值超过 **5 m/s**。论文强调训练与部署的共同接口是地形语义，而不是单独一条速度指令（[论文](https://arxiv.org/abs/2611.15280)；[项目](https://pages.rai-inst.com/autonomous-trail-racing/)）。

### 算法模块、传感器与实时性

~~~text
前向 RGB → 冻结 DINOv3 特征
              ↓
约 10 万参数双头 Decoder
    ├─ 像素语义与可通行分数
    └─ 特征重建相似度（置信度）
              ↓
LiDAR 点云 + 位姿 + 相机标定
              ↓
2.5D 高程图 + 语义/置信度融合
              ↓
运动策略读取局部可通行地形
~~~

官方独立开源 **SemMap** 模块，带 ROS2 C++ 节点、Python 推理、TensorRT 模型导出和 GrandTour 公开数据示例。仓库介绍其在特定配置下 Jetson AGX Orin 可达到约 **90 Hz** 的模型运行速率；论文描述的完整机载语义地图约 **30 Hz**，两个频率不是同一条完整处理链（[SemMap 源码](https://github.com/rai-opensource/sem_map)）。

### 代码、依赖与可复现性

作者文档指定 x86_64 NVIDIA GPU 或 Jetson AGX Orin、Ubuntu 22.04/ROS2 Humble 容器与 NVIDIA Container Toolkit。入口为：

~~~bash
git clone https://github.com/rai-opensource/sem_map.git
cd sem_map
docker compose --profile desktop build
docker compose --profile desktop up -d
docker compose --profile desktop exec sem_map-desktop bash
source scripts/setup_env.sh
./scripts/verify.sh
colcon build
source install/setup.bash
~~~

需要图形桌面时先按 README 配置 X11/RViz 权限，不能无条件复制宽松的 xhost 设置到生产主机。之后按官方 \`scripts/artifacts/download.sh\` 获取模型，并用与设备匹配的 TensorRT 版本导出。

**关键许可限制：SemMap 代码采用 RAI Institute Research License，仅允许非商业研究使用。** 它不是可直接集成进商业产品的 Apache/MIT 项目。公开仓库也未包含作者内部机器人配置及完整论文评测代码。

### 鲁棒性、风险与工程启发

置信度来自特征重建相似度，不能直接当作障碍的标定概率。模型在极端光照、陌生地表及反光地面上可能低估风险；离线地图回环和相机外参漂移也会影响语义投影。最小实验应选一段含陡坡、碎石与草地的 ROS Bag，对比纯 2.5D 地图、语义地图与置信度门控地图，测运行 P95/P99、地面误判与地图更新速度。

**适合：** Jetson、轮足/轮式越野导航、语义成本地图。对于多 LiDAR 系统，可以只引入 SemMap 的语义与可靠性 Sidecar，不必改变已有稳定的 LIO 主定位。

来源：[原论文](https://arxiv.org/abs/2611.15280) · [官方演示](https://pages.rai-inst.com/autonomous-trail-racing/) · [SemMap](https://github.com/rai-opensource/sem_map)。

---

## 2. DroneDiffusion：把耀斑、过曝和反射造成的感知失效区纳入 UAV 轨迹生成

**时间回补｜v1 2026-11-11 10:08 UTC｜arXiv:2611.15277**

### 为什么重要

三维环境里几何上看似可通行的区域，不代表视觉传感器能够可靠地感知它。耀斑、玻璃反射和过曝可能使无人机在自由空间估计上出错。DroneDiffusion 将 VLM/视觉感知可靠性地图与 RGB、目标和初速度共同输入条件 DDPM，生成候选局部三维路径，最后使用基于 ESDF 的 CHOMP 式引导修正障碍代价。训练在仿真中完成，作者报告了零样本实机飞行（[论文](https://arxiv.org/abs/2611.15277)）。

### 算法、假设和实验

~~~text
前向 RGB → AnyTraverse 感知可靠性
           ↓
像素风险图 + 目标 + 初速度
           ↓
条件 DDPM / 1D U-Net → 轨迹候选
           ↓
ESDF + CHOMP 式引导（无需重训）
           ↓
可执行局部轨迹 → 控制器
~~~

在指定实验中，轨迹沿线平均感知可靠性由几何基线 **0.63** 提升至 **0.71**；CHOMP 引导使学习先验的碰撞率由 **14.7% 降至 7.8%**。这不是现实飞行零碰撞保证。

论文提供 RTX 4070 Super（12 GB）的完整耗时分解：ESDF **18.38 ms**、AnyTraverse **122.14 ms**、Scene Encoder **5.23 ms**、11 步生成与引导 **35.61 ms**，完整 warm-start 均值 **181.36 ms**，约 **5.51 Hz**；可见主要瓶颈是感知可靠性推理，而不是扩散生成本身（[HTML 论文与耗时表](https://arxiv.org/html/2611.15277v1)）。

### 复现、风险与适用对象

未核实同名论文的完整官方训练代码；网上另有较早的 JAX **DroneDiffusion 动力学辨识**仓库，两者**不是同一个项目**，不能借用代码冒充此次规划器实现。可以先在 PX4 SITL/ROS2 中用人工构造的过曝/反射风险区域与 ESDF，比较只考虑几何距离、增加感知风险成本、增加轨迹引导三组。记录碰撞、风险区域停留、规划 P95 和控制动作年龄。

**适合：** 室内无人机、狭窄通道、强光/玻璃场景。涉及实际飞行时仍需独立的物理避障与失联制动逻辑。

来源：[论文](https://arxiv.org/abs/2611.15277) · [HTML 与运行时数据](https://arxiv.org/html/2611.15277v1)。

---

## 3. APG-Planner：解析策略梯度训练高速 UAV 轨迹，真机报告最高 11 m/s

**时间回补｜v1 2026-11-11 10:28 UTC｜arXiv:2611.15296**

### 为什么重要

无人机高速轨迹学习通常依赖专家轨迹模仿或模型自由 RL。前者被示教质量限制，后者从离散回报估计策略梯度，方差高、训练昂贵。APG-Planner 利用差分平坦性（Differential Flatness），从规划的多项式轨迹解析重建状态，使整段轨迹的代价与策略参数保持可微，直接对 Episode Loss 反向传播（[原论文](https://arxiv.org/abs/2611.15296)）。

### 方法、实验与理论限制

~~~text
深度图 / 视觉观测 + 目标
           ↓
策略网络输出轨迹参数
           ↓
差分平坦性 → 位置、速度、姿态与输入
           ↓
可微轨迹级状态传播与障碍损失
           ↓
解析梯度更新策略
           ↓
真实无人机采用低层跟踪器执行
~~~

作者报告单 GPU 约 **30 分钟**训练，在仿真中达到与强基线相当或更好的表现，真实飞行最高约 **11 m/s**；方法还在差动/滑移转向地面机器人上做了扩展。但 **11 m/s 是指定实验所达峰值，不是任意环境的安全工作速度**。

差分平坦性依赖所用载体动力学和控制约束。轨迹生成“可微”不等于实际电机、推力、电池、控制延迟和接触全部被正确建模。公开论文未核实可直接构建的一键训练仓库，本期不虚构安装命令。

### 最小工程验证

在 Python/JAX/PyTorch 仿真中先为二维双积分模型建立多项式轨迹参数化，并验证有限差分与解析梯度一致，再加入四旋翼微分平坦状态重建。比较 APG、PPO 和专家模仿在相同 GPU-hours 下的有效路径率、碰撞率、最大加速度/jerk、训练成本及真实控制 P99。

**适合：** 视觉高速无人机、解析梯度控制学习、从轨迹直接回传损失的规划器；对于只使用 LiDAR 的飞行平台，不能直接照搬它的视觉前端。

来源：[APG-Planner 论文](https://arxiv.org/abs/2611.15296) · [HTML 方法细节](https://arxiv.org/html/2611.15296v1)。

---

## 4. DIVAL：非完整约束机器人启动时，先修正向量场与航向不一致的问题

**时间回补｜v1 2026-11-11 UTC｜arXiv:2611.14918**

### 为什么重要

轮式非完整约束机器人不能瞬间沿任意二维方向运动。即使规划器设计了无碰撞的名义向量场，如果初始航向恰好与其方向严重不一致，机器人在旋转对齐期间可能撞上障碍，或产生速度/角速度突变。DIVAL 对工作空间应用局部微分同胚变换，使**初始位置的向量场方向**与机器人当前航向对齐，同时在变形区域外保留原向量场（[DIVAL 论文](https://arxiv.org/abs/2611.14918)）。

### 算法模块与假设

~~~text
名义安全向量场 + 当前 (x,y,θ)
                  ↓
局部工作空间微分同胚变形
                  ↓
初始场方向与 θ 对齐
                  ↓
非完整约束速度/角速度控制律
                  ↓
连续跟踪并保持名义场相关性质
~~~

论文给出与特定数学条件相联系的安全、目标收敛和平滑性推导，并在数值仿真与地面车硬件实验演示不同初始条件下无碰撞收敛。**不能将论文中的全部试验通过理解为随机动态障碍和任意车体动力学都被保证安全。**

### 工程风险与可复现性

该方法需要当前位姿、可用的名义场、机器人几何及速度/角速度上限。局部变形必须可逆，且不能偷偷引入新的不可行区。未核实完整的官方源码，可先在 2D 差动底盘模拟器中建立初始航向相反、障碍靠近起点的十类工况，比较原向量场、先原地转向与 DIVAL。统计起步最近障碍距离、轨迹曲率、控制抖动、收敛率和 P95。

**适合：** 室内轮式巡检、非完整约束底盘和局部场规划；不是可直接替代 Nav2 全局拓扑规划的算法。

来源：[论文](https://arxiv.org/abs/2611.14918) · [HTML 公式与硬件实验](https://arxiv.org/html/2611.14918v1)。

---

## 5. Coupled-CBF：多机器人避免碰撞的同时，显式排除部分死锁状态

**时间回补｜v1 2026-11-12 03:09 UTC｜arXiv:2611.16218**

### 为什么重要

两台机器人在单通道互相礼让、双方都停在狭窄区域，即使没有碰撞也不能完成任务。只优化“离障碍越远越好”或让两台车独立运行同一套 CBF-QP，可能产生互相阻塞。论文引入**耦合 CBF + Yielding Matrix**，编码双方影响与礼让偏好，并推导在特定条件下排除死锁状态的充分条件（[论文](https://arxiv.org/abs/2611.16218)）。

### 关键控制结构

~~~text
多机器人位置/速度 + 输入约束
                  ↓
可控减速度与相互作用约束
                  ↓
耦合 Control Barrier Functions
                  +
Yielding Matrix（礼让结构）
                  ↓
QP 最小修改名义控制
                  ↓
持续安全、冲突消解与重新规划
~~~

论文还指出：**有限最大减速度导致的松弛项并不能靠无限增大罚系数消除**；需要通过充分的安全边距处理。这对高速会车十分关键。

### 实验与工程边界

作者给出数学充分条件和多机器人仿真实验，包含礼让偏好变化与部分机器人故障。摘要没有统一的真实机器人碰撞率或 P99，也未核实完整官方代码。

可以创建两车会车与四车十字路口场景，对比固定优先级、普通独立 CBF、耦合 CBF；验证死锁时间、最小净空、QP 可行率、最大减速度超限、动作平滑与故障恢复。只有当假设满足时才能讨论论文的数学保证；不能把它当成所有现实交通情形的安全认证。

**适合：** 多台轮式机器人共享走廊、楼层任务协作、低带宽车队局部调度。

来源：[原论文](https://arxiv.org/abs/2611.16218)。

---

## 6. Visibility-Aware TAMP：先决定该去看什么，再决定如何挪动物体

**时间回补｜v1 2026-11-12 03:07 UTC｜arXiv:2611.16213**

### 为什么重要

长时段桌面整理任务不只缺少路径，还常缺少观测证据：物体部分被遮挡，抓取前并不知道它的确切形状与可用空间。只依赖当前帧，一旦遮挡物被移走就容易丢失之前知道的几何；只依赖一个静态全局计划，则会在隐蔽物体被发现后过期。

这篇工作把主动观察动作插入传统 Task-and-Motion Planning（TAMP）骨架，利用**持久物体记忆**融合跨视角观测，维护对象 Mesh 假设与已经真实观察过的占据区域（[论文](https://arxiv.org/abs/2611.16213)）。

### 模块、观测假设与工程风险

~~~text
部分可见桌面图像 + 初始任务
                   ↓
传统 TAMP 生成任务骨架
                   ↓
判定当前关键对象是否具有足够证据
       ├─ 足够：继续移动/抓取
       └─ 不足：加入主动感知视角
                   ↓
对象级持久 Mesh/占据记忆更新
                   ↓
重新验证后续任务动作可行性
~~~

作者在真实桌面重排、重遮挡和部分可见设置中报告优于无主动感知/无持久记忆基线，但公开摘要未提供统一的百分比或实际控制时延。没有独立核实可构建的完整源码。

### 最小复现与适用对象

用 MuJoCo 两个箱子互相遮挡的桌面任务，构造只用当前图像、持久对象记忆和持久记忆+主动观察三组。测任务成功率、无谓重新搜索次数、观察动作数量、规划时延、错误抓取和 Mesh 与真实点云冲突。

**适合：** 移动操作、机器人长期任务、语义地图和需要明确“未知/已确认”的 Agent。生成的假设几何不能未经验证就变成安全避障的真实地图。

来源：[原论文](https://arxiv.org/abs/2611.16213)。

---

## 7. Neural TOMPC Imitation：长时域非凸 MPC 当专家，部署用 1 kHz 学习控制器

**时间回补｜v1 2026-11-12 16:04 UTC｜arXiv:2611.17005**

### 为什么重要

非线性 Time-Optimal MPC 能处理终端约束和复杂动态，但在线求解很慢；单纯把 MPC 大量 Rollout 当作模仿数据，又会因为专家查询昂贵而难以覆盖边界状态。论文提出 **Self-Informed Sampling（SIFS）**，用学习到的剩余时间/偏差线索优先查询专家，使有限的专家预算集中在策略可能偏离时间最优行为的状态（[论文](https://arxiv.org/abs/2611.17005)）。

### 算法、实测与边界

~~~text
非凸 Time-Optimal MPC 专家
                ↓
初步收集数据训练近似策略
                ↓
SIFS：筛选最需要专家标签的状态
                ↓
补充专家数据 + 训练 + 状态分布修正
                ↓
部署时使用低成本前馈控制网络
                ↓
终端约束与独立安全策略验收
~~~

作者报告相对标准数据聚合，在**约三分之一训练时间、不到一半训练数据**下达到相近的策略表现。指定系统从原专家约 **1.4 Hz** 求解提升到学习控制器 **1 kHz**；硬件实验在 **Furuta 倒立摆**上完成摆起与稳定。

这是 **Furuta 系统的控制率对比**，不是说通用机器人 MPC 都可无条件提升数百倍。学习策略并不天然继承所有 MPC 硬约束的严格保证，模型失配和状态分布外时仍须安全过滤。完整源码未独立确认。

### 工程复现

在 MuJoCo/Furuta Pendulum 上生成一批时间最优 MPC 示例，然后比较随机专家采样、DAgger 和 SIFS。统一计量专家求解次数、数据量、训练时间、策略成功率、实际推理 P99 及真实状态边界约束违反率。

**适合：** 高频控制、嵌入式边缘控制器、从重型 NMPC 蒸馏可执行策略。

来源：[论文](https://arxiv.org/abs/2611.17005)。

---

## 8. BWM-Forge：让 Coding Agent 先写可编辑 Blender 世界程序，再做机器人视频生成

**时间回补｜v1 2026-11-12 03:14 UTC｜arXiv:2611.16221**

### 为什么重要

直接生成机器人视频很难保持相同动作在多个镜头、多个场景外观间的几何一致性。BWM-Forge 让 Coding Agent 先生成 Blender Scene、机器人模型、运动和相机的显式程序，渲染结构正确的 Proxy Video，再由视频模型补足外观。这样的中间层天然可编辑，便于复用机械臂/机器狗动作与摄像机机位（[论文](https://arxiv.org/abs/2611.16221)；[源码](https://github.com/Lcixs/BWM-Forge)）。

### 框架与已公开内容

~~~text
输入图片 / 动作先验 / 演示视频
                    ↓
Input Agent → Blender Building Agent
                    ↓
场景脚本 + URDF/Robot + Camera
                    ↓
Blender Proxy Video
                    ↓
Video Generation + Rendering/Review
                    ↓
Review 反馈 → Experience Repository
~~~

论文在五类机器人、15 个任务上比较生成视频的审美、成像、运动与指令匹配等指标。这些 **VBench / RoboJudge 指标并不证明仿真物理可靠，更不代表 Sim2Real 控制策略已验证**。

官方 GitHub 仓库有 Apache-2.0 源码、GUI、Blender 与模型配置，真实入口为 Python 3.11+、独立安装 Blender：

~~~bash
git clone https://github.com/Lcixs/BWM-Forge.git
cd BWM-Forge
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 按 config.py 配置本地 Blender 路径和模型/视频服务凭据
python -m gui.app
~~~

项目 README 明确目前主要面向 **Windows 本地桌面**；在 Arch Linux 上不能假定上述启动未经修改即可正常运行。模型调用与最终视频生成依赖外部服务，虽然 Harness 开源，**并非完整纯离线方案**。不应让 Codex 自动读取真实 Key；配置文件和日志须排除凭据。

### 对工程的实际价值

先跳过大型视频生成，只运行一个 Blender Proxy 测试：导入一台机械臂 URDF，指定两组相机位姿和简单重复动作，检查每一帧关节、末端位置和场景物体是否一致，再考虑引入生成模型美化。检查脚本复用率、渲染耗时和物理错误数。

**适合：** 机器人演示视频、训练数据合成、Sim2Real 可复现素材；不适合把生成视频直接当作物理真值。

来源：[原论文](https://arxiv.org/abs/2611.16221) · [官方仓库](https://github.com/Lcixs/BWM-Forge) · [官方项目](https://bwm-forge.github.io/)。

---

## AI / LLM 附属框架与开源工程组件

### 组件 1｜Polaris：纯本地文档检索 MCP，SQLite BM25 + ONNX 向量检索

**工程补充回顾｜本期首次覆盖；不是 2026-11-16 首发。**

**源码：** [girard-g/polaris](https://github.com/girard-g/polaris)，MIT 许可证，Rust 单文件可执行分发。

**痛点与模块：** Codex 经常为回答“项目某个设计约束写在哪里”而 \`rg\`、打开多份 Markdown。Polaris 使用本地 ONNX Embedding、SQLite FTS5/BM25 和 sqlite-vec KNN 检索，再以 RRF 融合与 MMR 去重，将有限的相关原文段落通过 MCP 返回给 Codex。不用云端 Key；索引与向量计算在本机。它不是 SAG2 的多跳 Jev 评分框架，也不会无损复现 SAG2 Benchmark。

**最小运行：**

~~~bash
# 请先审阅安装脚本，确认发行版本和平台
curl -fsSL https://raw.githubusercontent.com/girard-g/polaris/main/install.sh -o /tmp/polaris-install.sh
bash /tmp/polaris-install.sh
polaris index ./docs
polaris watch ./docs     # Codex 场景，持续增量索引
~~~

运行 \`polaris serve\` 可作为 stdio MCP Server；Codex 手动注册方式见下文。作者的 token 节省指标来源于其项目文档的特定检索测试，**不是 Codex 端到端完成率 Benchmark**，不应直接宣传任意项目都能省 10–40 倍 Token。

**A/B 验收：** 从现有 C++/ROS2 项目文档挑 30 个有标准答案的问题，比较 \`rg\` + 阅读文档与 Polaris 的证据 Top-5 命中率、错误引用、首次准备时间、文件更新后的索引新鲜度、返回 Token 与查询 P95。只索引需要的 Markdown，不向共享 MCP 暴露私钥文件或整个 HOME。

**风险：** 项目处于积极开发期，README 所述能力需自行测试；当前主要面向 Markdown 文档，并非完整 C++ 跨函数依赖图，也不等于 Agent 记忆系统。未实际本机运行。

### 组件 2｜Agent Commit-Boundary Evaluator：用确定性写入事实校验 LLM Judge

**时间回补｜v1 2026-11-10 UTC｜arXiv:2611.14581。**

**来源：** [论文](https://arxiv.org/abs/2611.14581) · [作者复现包 DOI](https://doi.org/10.5281/zenodo.23683806)。

**它解决什么？** Agent 的输出文字可以合理、连贯，LLM Judge 也可以重复给出相似评分，但实际数据库写入、权限状态等副作用与文字评价可能不一致。作者对 tau2-bench 航空及零售场景的 **2,160 个 Episode**记录每次数据库写入，对比原生 Gold-state、带/不带策略文档的 LLM Judge，以及最简单的 Commit-Boundary 检查。

**结果：** LLM Judge 重复裁决一致性 **98.2%**，却与 Native 评分只一致 **56.2%**。在 11 个已知禁止写入 Episode 中，普通 Judge 放过约 10–11 个；简单的无模型写入边界检查发现了全部 11 个。**这是所测情境的事实，不能推断任意应用中边界规则总比模型全面**。

**落地形式：**

~~~text
Codex 提议工具动作
        ↓
独立程序检查：权限、工作目录、目标对象、提交边界
        ↓
执行工具 / 记录实际写入与退出码
        ↓
独立事实验收（不是 Agent 自述）
        ↓
Codex 只对失败根因作解释与修复建议
~~~

**可执行最小试验：** 在无害 Git Worktree 中用固定脚本检查一个禁止修改的文件或模拟配置，记录操作前后 SHA256、目标路径和退出码；比较“让 Agent 自述通过”与“外部脚本检查真实文件”能否检测被禁止的副作用。对于已有 CLI/CI 测试，不必部署另一套大模型 Judge。

**可复现性与边界：** 论文给出可下载的追踪数据与复现 DOI，但本次通过网页访问 DOI 发生跳转错误，未独立验证复现包内容和许可证；不能宣称代码已本地安装执行，也不能把实验里的简易检查当作通用权限沙盒。

---

## AI Coding 实战技巧精选

### 技巧 1｜Codex 配 Polaris MCP：先查证据，再读源码

- **来源**：[Polaris 原始 README](https://github.com/girard-g/polaris)。
- **一句话结论**：当任务需要阅读大量 Markdown 技术规范时，将本地索引作为只读检索工具，避免每次全文送进上下文。
- **具体怎么做**：
  1. 按组件说明安装 Polaris，对项目文档运行 \`polaris index ./docs\`；用 \`polaris watch ./docs\` 保持索引更新。
  2. 使用当前 Codex CLI 的 MCP 子命令注册本地程序，**不需要云端 API Key**：
  
     ~~~bash
     codex mcp add polaris -- polaris serve
     codex mcp list
     ~~~

  3. 新开 Codex 会话，要求“先返回有关参数 X 的文档原句和文件位置，再读对应源码，不要凭推测回答”。
  4. 与相同问题下直接 \`rg\` 的方案比较原文命中、错误引用、上下文大小和端到端耗时。
- **适合什么场景**：Codex/T3 Code、长技术文档、ROS2/SIP 多文件规范。
- **注意**：Codex MCP 配置是否被当前 T3 Code 会话继承必须实际检查；Polaris 主要索引 Markdown，不替代 clangd/LSP 符号检索。与上方 Polaris 组件属于同一项目，**去重索引只登记一次**。

### 技巧 2｜用 oasdiff 验证 Codex 改接口是否破坏兼容性

- **来源**：[oasdiff 官方仓库](https://github.com/oasdiff/oasdiff) · [CLI Getting Started](https://www.oasdiff.com/docs/getting-started)。
- **一句话结论**：修改 NestJS/HTTP API 后，不要只让 Codex 自述“保持兼容”；用确定性 OpenAPI 差分检查接口有无破坏性变化。
- **具体怎么做**：
  1. 将 API 变更前后的 OpenAPI 定义保存为 \`base.yaml\` 与 \`revision.yaml\`。
  2. 用容器直接运行，不需要在宿主机安装 Go：
  
     ~~~bash
     docker run --rm -v "$PWD:/specs:ro" tufin/oasdiff \
       breaking /specs/base.yaml /specs/revision.yaml
     # 如需完整变更：将 breaking 改为 changelog
     ~~~

  3. 将实际 Breaking Report 交给 Codex，只允许针对明确的兼容性问题修改 API 或补充迁移策略。
  4. 对修改结果重新导出 OpenAPI 运行同一检查，再配合真实客户端契约测试。
- **适合什么场景**：Codex、NestJS/HTTP、跨平台 API、客户现场升级。
- **注意**：OpenAPI 差分只能覆盖规范中描述的 HTTP 行为；SIP/RTP/Kafka 等未纳入 OpenAPI 的协议语义不会自动得到保障。作者的仓库是 Apache-2.0，并非 11 月 16 日刚发布的新工具，属于高价值工程回顾。

---

## 经典论文回顾

### Brockett (1983)：Asymptotic Stability and Feedback Stabilization

**作者：** Roger W. Brockett。**历史位置：** 1983 年，收录于 *Differential Geometric Control Theory*，Progress in Mathematics 27，181–191 页（[原始论文存档](https://www.hrl.harvard.edu/publications/brockett83asymptotic.pdf)；[书目信息](https://cir.nii.ac.jp/crid/1572824499073211520)）。

### 核心问题与关键数学思想

为什么一个差速轮式机器人“可控”，却不等于存在一个对所有邻近状态都平滑、时间不变且能渐近稳定到指定姿态的状态反馈律？Brockett 在一般非线性系统 \(\dot{x}=f(x,u)\) 中给出连续/光滑静态反馈可稳定性的必要拓扑条件。对经典非完整约束车体，这构成了不能随意假定所有停车/目标姿态都可通过单一平滑静态反馈稳定的理论基础。

~~~text
非线性运动学 + 可用控制输入
              ↓
检查系统映射/拓扑可稳定性条件
              ↓
不满足 → 不能要求某类平滑静态反馈完成任务
              ↓
选用时间变化、混合/非光滑、轨迹跟踪
或分层规划 + 局部控制
~~~

### 当年重要性与今天仍然有效的部分

这项结果把“控制系统可到达”与“存在特定类型稳定反馈”严格区分，对非完整约束规划、轨迹跟踪、停车控制及移动机器人局部反馈设计影响深远。

**重要边界：** Brockett 条件是相应数学设置下的必要条件，不是说差速车无法停车或任何非完整约束系统都不能稳定。实际工程可以设计时间变化反馈、混合切换、轨迹跟踪或有条件的停车模式。

### 被后续扩展的部分和复现

后续非完整约束控制、CLF/CBF、轨迹优化和 DIVAL 等方法从不同角度处理航向、障碍和反馈结构。但 DIVAL 的局部向量场变形不能被简单宣传为“推翻 Brockett 定理”。

无所谓“官方 ROS2 原始源码”；原始研究是理论论文。可以在差动底盘二维模拟器构造目标姿态、起步方向相反和窄通道三组任务，对比静态平滑位置场、独立旋转—平移阶段控制、跟踪时间参数轨迹，以及 DIVAL 风格的初始航向对齐。

**对现有工程的重新解读：** 即便高精度 LiDAR 地图和 1 cm 重定位已具备，控制器也必须尊重非完整运动学；地图准确不自动保证姿态可即时跟踪或无碰撞靠近目标。

来源：[原始存档](https://www.hrl.harvard.edu/publications/brockett83asymptotic.pdf) · [1983 年书目](https://cir.nii.ac.jp/crid/1572824499073211520)。

---

## 今日结论

本期最直接能落地的是 SemMap 的**语义可通行性/置信度与 LiDAR 地图融合**；它有 ROS2、模型导出与公开数据示例，但需要特别遵守**非商业研究许可证**。对商业产品，先做功能与性能评估，不宜将其代码直接嵌入交付版本。

无人机部分，APG-Planner 的高速飞行展示学习式轨迹优化潜力，DroneDiffusion 则提醒我们必须把**感知可靠性和完整推理延迟**放进规划评测；前者不是 LiDAR-only 方法，后者 181 ms 完整管线也不适合在缺少独立安全层时直接承担高速控制。

对轮式机器人，DIVAL 解决初始航向与向量场不一致，耦合 CBF 则明确处理多机器人死锁；两者应分别以几何/动态约束仿真验收。Brockett 经典论文说明为什么这些控制问题不能靠“给出一条几何路径”就彻底解决。

对 Codex，优先试小范围本地 Markdown 检索和 OpenAPI Breaking Check；**能测出证据质量、减少无关文件读取和避免兼容性破坏的工具，比再加一层 Agent 框架更有价值。**

---

## 最值得深入研究或尝试复现的方向

| 优先级 | 方向 | 最小验收 |
|---|---|---|
| P0 | SemMap | Docker/ROS2 编译、GrandTour 演示、语义误判、TensorRT P95、许可证 |
| P0 | Codex + Polaris | 30 条真实文档问答、Top-5 证据召回、上下文/时间 |
| P0 | oasdiff | 一次 HTTP API 破坏性变更被阻止、真实客户端回归 |
| P1 | DroneDiffusion | 风险地图与 ESDF 消融、完整 181 ms 管线细分、SITL 避障 |
| P1 | APG-Planner | 可微平坦轨迹验证、训练成本、动态约束与飞行 P99 |
| P1 | DIVAL | 初始航向相反时的净空、角速度、收敛率 |
| P1 | Coupled-CBF | 双车会车/多车交叉口死锁率、最大减速度 |
| P1 | Visibility TAMP | 主动观察数量、长期物体记忆正确性、抓取率 |
| P2 | Neural TOMPC | 专家标签样本效率与控制 1 kHz 验证 |
| P2 | BWM-Forge | Blender 场景复用、几何一致性、外部服务依赖 |
| P2 | Commit-Boundary | 无害文件写入禁止测试、实际副作用日志 |
| P2 | Brockett | 不同反馈结构在非完整约束下的适用范围 |

## 参考资料

**最新公开批次：** [arXiv Robotics](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering](https://arxiv.org/list/cs.SE/new)。

**语义/无人机：** [越野自行车](https://arxiv.org/abs/2611.15280) · [SemMap](https://github.com/rai-opensource/sem_map) · [DroneDiffusion](https://arxiv.org/abs/2611.15277) · [APG-Planner](https://arxiv.org/abs/2611.15296)。

**规划/控制：** [DIVAL](https://arxiv.org/abs/2611.14918) · [Coupled-CBF](https://arxiv.org/abs/2611.16218) · [Visibility-Aware TAMP](https://arxiv.org/abs/2611.16213) · [Neural TOMPC](https://arxiv.org/abs/2611.17005)。

**世界建模/AI：** [BWM-Forge 论文](https://arxiv.org/abs/2611.16221) · [BWM-Forge 源码](https://github.com/Lcixs/BWM-Forge) · [Polaris](https://github.com/girard-g/polaris) · [Agent Judge 研究](https://arxiv.org/abs/2611.14581) · [oasdiff](https://github.com/oasdiff/oasdiff)。

**经典论文：** [Brockett 原论文](https://www.hrl.harvard.edu/publications/brockett83asymptotic.pdf) · [1983 书目](https://cir.nii.ac.jp/crid/1572824499073211520)。
