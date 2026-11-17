---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-17"
date: 2026-11-17 09:00:00 +0800
description: "RK3588 NPU GNSS捕获、ERA可修正深度地图、PoliMop策略在环规划、虚拟关节跨本体控制、X-Nav、Agentic-Teacher，以及ProdPilot、Agent轨迹分析和Codex Skills工程实战。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-17

## 摘要

**日期：2026-11-17（Asia/Shanghai，星期二）。** 本次首先读取 [GitHub 任务规范](https://github.com/helywin/daily/blob/master/robotics-brief-task-spec.md) 和 [历史覆盖索引](https://github.com/helywin/daily/blob/master/robotics-brief-covered-items.md)，历史已有 **1,369 条**。再核查 arXiv 原始列表：目前可见的 cs.RO 最新常规列表为 **2026-11-16（周一）61 条、首次提交 37 条**；cs.SE 为 **44 条、首次提交 10 条**。列表总数包含交叉收录及更新稿（[cs.RO](https://arxiv.org/list/cs.RO/new)、[cs.SE](https://arxiv.org/list/cs.SE/new)）。

先检索最近 24 小时，随后扩大到最近 7 天。八篇主动态的 v1 实际提交于 **11 月 12—13 日 UTC**，均标为**时间回补**，不将 11 月 16 日列表日期误写成首发日期。按标题、arXiv ID、项目页、仓库及 DOI 与全部历史条目去重，没有重复报道此前已覆盖的 SAG2、Polaris、SemMap、SPARC、NSDL、LARBRID 等项目。

**今日关注：** ① 真实可运行的 **PocketSDR-NPU** 将 GNSS 码捕获映射到 RK3588 NPU，提供 CPU/NPU 逐信号对照；② **ERA** 让预测深度造成的错误占据可撤销，避免“无 Frontier 即任务结束”；③ **PoliMop** 让真实底层运动策略参与三维路径可达性判断；④ **虚拟关节接口、X-Nav 与 Agentic-Teacher** 分别解决跨本体训练、跨室内外目标导航和失败数据生成；⑤ **ProdPilot / 轨迹分析器 / Skills MCP** 以确定性验证、可观测轨迹和按需工具强化 Codex。

**优先尝试：** [PocketSDR-NPU](https://github.com/taroz/PocketSDR-NPU)（真实 RK3588 模型与评测脚本）、[ProdPilot](https://github.com/prodpilotai/ProdPilot)（仅在受支持的 Node/React 项目做离线审计）、[trajectory-analyzer](https://github.com/SWE-rebench/trajectory-analyzer)（不用模型分析 Agent 工具执行轨迹）。本次核实了原始代码与文档，没有在用户设备上实际构建或调用 Codex。

---

## 1. NPU-Accelerated GNSS：不用神经网络，也能利用 RK3588 NPU 加速 GNSS 相关运算

**时间回补｜v1 2026-11-13 13:56 UTC｜arXiv:2611.18186**

### 为什么重要

RK3588 的 NPU 通常用于 RKNN 检测模型，但 GNSS 信号捕获也包含大量可并行乘加。论文将 FFT/DFT 的并行码相位搜索拆分为四步 DFT、小矩阵乘法、1×1 卷积、逐元素操作和张量转置，交给 NPU 执行；信号跟踪仍由 CPU 处理。**这不是用 YOLO 模型“识别卫星”，而是用 NPU 加速传统数值信号处理。**

### 算法模块、硬件与实时性

~~~text
GNSS 射频前端 → IF 采样 → Doppler/码相位搜索
                           ↓
                     four-step DFT
                           ↓
              1×1 conv / 矩阵乘法 / 相关峰
                           ↓
              NPU 相关结果 → CPU 跟踪 / 导航
~~~

作者分别针对共享 DDR 的 RK3588 和经 PCIe 连接且具有独立内存的 AX8850 设计数据流。**不能把 AX8850 的 3.0–3.8 倍加速算在 RK3588 头上。** 在 ROCK 5C（RK3588）上，L1CA 8 MHz 的 A76 基线为 52 ms、NPU 为 45 ms（约 1.1 倍）；L2CM 为 2,918 ms 对 1,231 ms（约 2.4 倍）；以 A55 为 CPU 基线时，NPU 相对加速明显更大。作者报告的整机跟踪通道 175→230 主要是 **Raspberry Pi 5 + AX8850** 评测，不能写成 RK3588 整机实测。

### 开源与最小复现

[论文](https://arxiv.org/abs/2611.18186) · [全文与硬件分解](https://arxiv.org/html/2611.18186v1) · [taroz/PocketSDR-NPU 官方源码](https://github.com/taroz/PocketSDR-NPU) · [Release 模型包](https://github.com/taroz/PocketSDR-NPU/releases)。

作者提供 BSD-2-Clause 源码、RK3588 INT8 RKNN 模型、模型生成与测试脚本、300 秒 / 14.4 GB IF 原始记录。Linux ARM64、FFTW3、RKNN Runtime 2.3 是 RK3588 路线的主要依赖。根据 README 的构建方式：

~~~bash
git clone https://github.com/taroz/PocketSDR-NPU.git
cd PocketSDR-NPU
# 先安装 FFTW3、匹配驱动的 RKNN Runtime，并解压对应模型 Release
cd lib/build
make USE_SOAPY=0 USE_FFTW=1 USE_RKNN=1
make USE_SOAPY=0 USE_FFTW=1 USE_RKNN=1 install
# 按 README 在 app/pocket_trk 中编译，然后用 -acc cpu / -acc rknn 对照
~~~

评测目录含 \`test/eval\` 与 \`test/utest\`。先跑合成 IF 与单个短码搜索，检查相关峰位置、灵敏度、内存和温度，再下载超大原始数据。

### 假设、风险、适合谁关注

NPU 在部分短码场景不一定比优化后的 A76/FFTW 快很多；模型与采样率、RKNN runtime 和 NPU 驱动绑定，不能把不同 BSP 的性能混用。GNSS 捕获速度也不是定位精度；实际 RTK、多路径误差和时钟仍需独立处理。

**适合 RK3588、Rock 5C、Orange Pi 5 Plus、RTK/GNSS、SDR 和边缘计算研发**。可以先验证“非 AI 模型的 NPU 运算加速”这条技术路线，再决定是否适用于其他卷积可表达的信号处理。

---

## 2. ERA：深度估计错了可以修地图，不应让虚假的“无 Frontier”结束导航

**时间回补｜v1 2026-11-13 04:20 UTC｜arXiv:2611.17730**

### 为什么重要

单目 RGB 推断的深度会随视角变化。如果把每次深度预测直接写为永久障碍，错误会累积：原本可通行的区域被封死，Frontier 被虚假占据抹去，系统认为没有未知空间而停止探索。ERA 用 **可撤销占据更新（Revisable Occupancy）** 和 **可达视点探索** 替代“首次预测就是地图真值”，目标还要经过多视角复核才允许宣告发现。

### 算法模块与假设

~~~text
RGB + 已知/估计相机位姿 → 预测深度
                    ↓
             可撤销占据图
                    ↓
Frontier 是否仍存在？
  ├─ 有：普通探索
  └─ 无：从可达视点重新观察可疑区域
                    ↓
       新证据推翻旧深度/占据假设
                    ↓
         跨视角目标确认
~~~

作者在三个 Benchmark 中报告不使用真实深度传感器的 training-free 对照优势；把 ERA 地图/探索组件接入 VLFM 时，**同一预测深度条件下的成功率从 10.8% 提升至 61.7%**。论文也报告真实机器人部署。这里不是定位 ATE 或碰撞认证。

### 可复现性、鲁棒性与工程落地

[原论文](https://arxiv.org/abs/2611.17730)。本轮未核实完整官方构建源码，不能标记为可一键部署。

最小实验：在统一 RGB、相机位姿与深度预测下，比较永久占据图、带观测证据的可撤销占据图、额外加入“无 Frontier 时检查可达视点”的方案。记录误封死格子比例、真实未知区域覆盖率、过早停止次数、计算 P95 与目标误报率。对玻璃、反光和视觉退化场景，**不可靠的生成几何不能覆盖激光雷达的可信避障测量**。

**适合单目无人机、低成本对象搜索和长期语义地图**。对多雷达定位平台，重要启发是为低置信地图增量保留证据来源与可撤销性，而非把它直接合入主地图。

---

## 3. PoliMop：把运动策略放进 RRT 搜索环，真正判断机器人“能不能过”

**时间回补｜v1 2026-11-13 12:35 UTC｜arXiv:2611.18110**

### 为什么重要

静态几何地图对不同机器人并不提供相同的可达性：轮式底盘不能走的台阶，四足策略可能越过；同一个四足底盘换一种运动策略后也可能失去跳跃能力。PoliMop 不是先生成几何路径、再祈祷控制器能够跟踪，而是把**机器人动力学仿真与当前控制策略 Rollout** 放到 kinodynamic RRT 的树扩展步骤。

### 算法模块与实验

~~~text
当前三维场景 + 底盘模型 + 运动策略
                   ↓
       质点模型先找粗略目标路线
                   ↓
     在降维状态空间采样 (xyz/v/yaw)
                   ↓
     物理仿真执行当前策略并扩展 RRT
                   ↓
          获得策略实际可行轨迹
~~~

论文在轮式、四足、人形的仿真中验证不同平台共享规划主架构，粗路径引导采样在指定对照中使规划时间**最多减少 63%**。放置木板连接断口后，可通行集合随环境变化扩展，但这不等于系统已经能自主判断如何安全架桥。

### 开源状态与工程风险

[论文](https://arxiv.org/abs/2611.18110) · [ETH 作者项目与视频](https://ariael21.github.io/polimop.html)。**项目页当前明确写着“Code coming soon”**；arXiv 元信息中的“videos and code”不能代替实际代码核验。

可先以 MuJoCo 中相同地图、同一控制策略复现：几何 RRT、质点引导 RRT、策略在环 RRT。用成功率、物理穿透、足底滑移、规划时长和硬件控制延迟验收。在线执行仍需要独立障碍检查，策略模拟误差和 Sim2Real 落差无法忽略。

**适合跨楼层 3D 规划、机器狗/轮足 SDK、不同底盘共用规划框架。** 对只有 vx/vy/wz 或登梯模式的 SDK，先将厂商模式作为有限技能集在仿真中验证，不能宣称已有控制策略就能泛化所有楼梯。

---

## 4. Body-Aligned Virtual Joints：不改底层驱动，让不同人形机器人复用同一训练配方

**时间回补｜v1 2026-11-13 10:29 UTC｜arXiv:2611.18003**

### 为什么重要

同一套模仿或 RL 奖励配方放到不同人形机器人上，关节局部轴方向、角度正负、限位和传动关系可能不同。策略若直接输出各平台原生关节坐标，训练优化器实际上在不同坐标系中工作。

研究在策略与原生运动控制之间加一层**以人体方向约定表示的虚拟关节空间**，用确定性运动学映射回各机器人 native target，不动原有 transmission 与低层控制栈。

### 模块、实验与边界

~~~text
同一策略网络 / 动作尺度 / 奖励配方
                  ↓
           Body-Aligned Virtual Joints
                  ↓
          确定性虚拟→原生关节映射
                  ↓
             原有执行器与控制器
~~~

在三个腿部关节轴布局不同的人形平台上，作者报告同一未经修改的训练配方能够稳定训练；真实 Unitree G1 实验中航向漂移约降低近六倍。**这个量化结果属于指定 G1 实验，不是所有行走任务训练加速六倍。**

### 复现、风险与适用

[原论文](https://arxiv.org/abs/2611.18003)。本轮未核实完整官方训练代码与权重。

在 MuJoCo 做最小验证：使用两台腿部关节轴定义不同的模型，保持同一前进动作、奖励与 PD 参数，只比较直接输出 native joint 与虚拟关节映射。测足部朝向、关节限幅、航向漂移、训练方差及实际控制延迟。映射错误会形成新的系统性危险，不可跳过 FK/雅可比和限位检查。

**适合 G1/多型号人形、机器人控制 SDK 封装及跨本体训练。** 更广义的启发是把“策略动作接口”与“设备驱动私有坐标”解耦。

---

## 5. Agentic-Teacher：Coding Agent 从失败状态生成演示，数据筛选比成功 Rollout 更重要

**时间回补｜v1 2026-11-12 15:43 UTC｜arXiv:2611.17394**

### 为什么重要

预训练 VLA 的薄弱点往往藏在少数状态：抓取偏移、物体遮挡、错过目标或控制偏离。直接采集越来越多成功演示，未必覆盖这些失败分布。Agentic-Teacher 让 Coding Agent 检查失败 Rollout，选择干预状态，编写闭环代码策略，经过环境执行验证后将其复用为演示生成器。

### 训练链路与实验

~~~text
冻结 VLA → 发现失败状态
               ↓
Coding Agent 借助仿真工具开发局部闭环修复策略
               ↓
环境执行验证 → 产生成功续接演示
               ↓
加入时间相关动作扰动，去除无效停顿但保留夹爪转换
               ↓
按冻结原策略 Flow-Matching Loss 筛选数据
               ↓
VLA 后训练 → 部署时不再需要 Coding Agent
~~~

在作者所设仿真中，π0 在 LIBERO-10 从 **79.4%→87.8%**、MetaWorld-10 从 **80.4%→90.6%**，三个 RoboCasa 任务的平均成功由 0% 提至 30.0%。这些是作者指定的模型、任务与数据，不能代表所有 VLA 或真机成功率。

### 工程边界与适合人群

[原论文](https://arxiv.org/abs/2611.17394)。目前未确认可运行的完整官方代码，不提供虚构安装命令。

最小可复现思想：在一个固定 RoboTwin/MuJoCo 操作任务，保存失败起始状态；让确定性代码策略从该状态完成任务；只对有效续接采样做离线训练对照，比较原策略、加所有修复数据、加筛选修复数据的任务成功率与分布外误差。

适合 **VLA 后训练、生成式动作策略、机器人失败恢复**。真正的工程价值是“失败定位→局部修复→数据质量验证”的流水线，不能让 Coding Agent 直接控制未经安全限制的真机。

---

## 6. Racing the Clock：带剩余时间预算的 VLN，应学会信息不足下的探索，而非模仿全知最优路线

**时间回补｜v1 2026-11-12 19:13 UTC｜arXiv:2611.17442**

### 为什么重要

同样是“找楼里的灭火器”，给机器人 30 秒和 10 分钟时，策略应不同：前者尽快访问最可能区域，后者应更广泛探索。传统 VLN 常有固定 Episode 上限，但策略并不知道剩余预算。研究比较两种专家：已知真实物体位置的 TSP 全知专家，以及只有房间级语义先验、最大化期望收益的 Bellman 专家。

### 模块、指标与假设

~~~text
目标类别 + 剩余动作预算 + 当前观察
                  ↓
      房间级候选 / 目标出现先验
                  ↓
       不完全信息下的 Bellman 决策
                  ↓
          下一观察目标 / 访问房间
~~~

在未见过的 HM3D 测试场景，2,000 步（约 500 m）预算下，Bellman 监督策略找到 **71.4%** 的可达目标实例，TSP 全知专家监督策略为 **65.5%**，原 VLN 为 **44.8%**。**这是目标发现召回，不是导航无碰撞率；全知专家自身性能更高，却未提供最适合学习探索的监督。**

### 可复现性与应用

[原论文](https://arxiv.org/abs/2611.17442)。目前未核实训练脚本完整公开。

可在已有语义地图中设置 30、100、500 个离散决策步预算，对比固定 Frontier、贪心最高概率房间和显式预算策略，统计预算内首次发现时间、目标召回和绕行成本。要记录真实移动速度与停靠耗时，避免仿真步数直接等价真实秒数。

**适合无人机巡检、楼宇搜寻、消防/应急找物以及短续航任务。**

---

## 7. X-Nav：从办公楼走到室外商店的人形长任务，视觉模型并未取代 LiDAR 控制链

**时间回补｜v1 2026-11-12 23:38 UTC｜arXiv:2611.17598**

### 为什么重要

语义导航 Benchmark 常评估从当前位置走到短程目标，而真实巡检任务需要跨房间、门、楼外道路、动态障碍及不同导航模式。X-Nav 建立数据引擎（仿真、现场数字孪生、真机）、MELIOR 视觉导航策略和 X-Navarch 任务编排，把一句长期指令拆成可以逐段执行的子任务。

### 真实系统结构

~~~text
用户长指令
   ↓
X-Navarch: 分解室内/门/室外子目标
   ↓
MELIOR-A: RGB→动作  或  MELIOR-N: RGB→目标点
   ↓
显式目标导航 + 障碍避让 + 底层执行
   ↓
LiDAR / 里程计用于目标接近与低层控制
~~~

作者在 Lingxi X2 上报告约百米的办公室大厅→室外相邻建筑商店演示，并以现场数字孪生数据调整导航模型。**“MELIOR 使用内置 RGB”不等于整套机器人是纯相机零 LiDAR 导航。**

### 复现与工程风险

[原技术报告](https://arxiv.org/abs/2611.17598)。未核实完整训练、模型权重及导航代码可下载，不能作为现成 ROS2 组件直接集成。

先构建可验证的“房间→门→室外→具体设备”分层状态机：每个任务阶段具有目标证据、成功判据、超时和失败回退；底层仍用现有 LiDAR 规划控制。比较一次性生成全路线与分阶段可重试导航的最终成功率、错误目标切换与人工接管次数。

**适合跨楼层巡检、语义导航、长期 Agent 与现场数字孪生适配。**

---

## 8. Objectives as Policies：让 VLM 写可编辑代价程序，MPC 执行物理动作

**时间回补｜v1 2026-11-13 UTC｜arXiv:2611.18298**

### 为什么重要

VLM 能理解“将物体移入盒中”，但直接让它生成连续关节轨迹缺乏确定的物理约束。Objectives as Policies（OaP）要求 VLM 生成的是一个**可编辑的任务目标程序**：分阶段定义 running cost、terminal cost 和完成条件，再由共享采样式 MPC 在仿真中执行。

### 模块、实验与边界

~~~text
自然语言 + 场景观察 → VLM
                    ↓
       代价项 / 阶段边界 / 完成条件
                    ↓
           真实场景→仿真数字孪生
                    ↓
          采样式 MPC 执行与回放
                    ↓
           VLM 修改代价程序
                    ↓
          经过验证后部署实际动作
~~~

作者在四项桌面接触操作的仿真和真实机器人中报告优于对照的方法表现。摘要没有统一、可直接外推的成功率或实时 P99，本期不造数。

[原论文](https://arxiv.org/abs/2611.18298)。项目展示已被作者声明，但**完整官方运行代码没有独立确认**。

最小实验可让 LLM 仅生成固定 schema 的目标代价 JSON，包括每一阶段的终止条件；由已有 MPC/仿真器执行，独立校验代价值域、状态机转换、碰撞和最大动作时间。不得把 LLM 的“任务完成”文字当成真实关节与接触的验收证据。

**适合机械臂接触操作、VLM 任务分解、规划与控制解耦。**

---

## AI / LLM 附属框架与开源工程组件

### 组件 1｜ProdPilot：50 条确定性生产检查 + 有界修复 MCP

**项目：** [ProdPilot 论文](https://arxiv.org/abs/2611.17381) · [MIT 官方代码](https://github.com/prodpilotai/ProdPilot)。

**痛点：** Coding Agent 生成的 Node/React 项目能本地运行，却可能缺少健康检查、容器、密钥隔离和部署条件。ProdPilot 采用 50 条规则，其中 28 条固定模板、16 条提取项目数据填充、只有 6 条允许 Agent 自由生成；**每次修复必须重新经过原始检查器验证**，而不是相信 Agent 宣称成功。作者在 23 个样本项目的完整流水线中，独立验证拒绝 237 个“自称已应用”的补丁中的 25 个。

~~~text
代码 → 50 条只读检查 → 失败规则
                           ↓
模板 / 项目提取修复 / 有界模型修复
                           ↓
重新执行独立规则验证
                           ↓
生产就绪 Gate → 可选部署
~~~

**运行与依赖：** PyPI 提供 Python 3.11–3.14 工具，README 当前版本 1.1.0。项目仅覆盖 **Express/Node.js API 和 React/Vite**，默认部署后端仅 **Render**；发布部署需要 GitHub/Render 凭据，不适用于 C++/ROS2/SIP 原生工程。

**先做只读实验，不部署：**

~~~bash
uv tool install prodpilot
prodpilot --help
prodpilot audit ./your-node-project --ci
prodpilot report --format md --out /tmp/prodpilot-audit.md ./your-node-project
prodpilot fix --dry-run ./your-node-project
~~~

README 已明确提供 \`audit\`、\`report\` 和 \`fix --dry-run\`；调用 \`deploy\` 会影响真实 GitHub/Render 资源，不能把安全审计默认升级为部署操作。与 Codex 的 \`prodpilot serve\` Stdio MCP 属于**手工连接的可行方案**，项目提供的自动 connect 子命令没有声明原生 Codex 支持。

**A/B：** 在固定的 Node 项目中制造 10 个受控故障，比较 Codex 自行审查、ProdPilot 报告、报告+Codex 有界修复的实际规则通过数、误修复、构建成功率。只记录实际结果；不根据项目论文的部署评分推断所有生产环境可上线。

---

### 组件 2｜trajectory-analyzer：用确定性解析器看 Codex 究竟在搜索、修改还是验证

**项目：** [Interpreting Coding Agents 论文](https://arxiv.org/abs/2611.17440) · [MIT 开源解析器](https://github.com/SWE-rebench/trajectory-analyzer)。

**痛点：** 两次 Agent 任务都失败，可能原因完全不同：一轮在读错文件，另一轮过早修改，没有运行任何测试。只看 Token 和最终成功/失败不足以指导优化。作者对 143,209 条多模型执行轨迹研究，将工具日志归一化为**搜索、文件编辑、测试**等行为，再比较执行阶段结构。

已核实的仓库提供 Python 3.10+ 确定性解析器、合成单测、统计分析与说明：

~~~bash
git clone https://github.com/SWE-rebench/trajectory-analyzer.git
cd trajectory-analyzer
python3 -m unittest discover -s tests -v
python3 parser.py /path/to/trajectory.json --schema auto --include-metrics
python3 extract_metrics.py /path/to/trajectory.json --output metrics.json
~~~

**真实开放边界：** 当前公开仓库并不包含原论文全部轨迹与共识标注；部分上游 Hugging Face 数据集已变为私有，原始全量分析不能从当前检出直接一键重跑；解析器对部分 \`file_change\` 事件的统计也存在明示限制。

**Codex 工程应用：** 在不泄漏密钥和真实源码的情况下，对个人导出的、已脱敏的 Agent 执行轨迹统计“定位用时、无关文件阅读、首次修改前的证据数量、运行测试比例、重复搜索比例”。比较新 Skill/MCP 接入前后这些指标和真实任务结果，不要假设“工具调用次数更少”总是更好。**未经核实的 Codex 私有轨迹格式需要先适配，不能宣称直接支持每一种 Codex 日志。**

---

### 组件 3｜skills-mcp：让 Codex 搜索 Skill 目录，但必须先人工审查再安装

**项目：** [gengirish/skills-mcp](https://github.com/gengirish/skills-mcp)（MIT）。

**痛点：** 各种 \`SKILL.md\` 散落在不同仓库，手工找、复制和更新成本高。该 MCP 用本地构建的技能目录提供 \`search_skills\`、\`get_skill\`、\`recommend_skills\`、\`install_skill\` 等工具。作者 README 标称 9,000+ 条 Skill；**这是目录规模，不是经过安全审计或真实任务有效性认证的数量**。

**本地与 Codex：** Node/npm，可直接在 Linux 启动 Stdio 服务。全局安装避免每次 npx 重新解析包导致握手超时。

~~~bash
npm install -g @gengirish/skills-mcp
codex mcp add skills -- skills-mcp
codex mcp list
~~~

随后先在 Codex 只使用 \`search_skills\` 与 \`get_skill\` 研究候选，不自动调用 \`install_skill\`。审查 Skill 是否包含 Shell、网络、上传、跨工作树文件读写、危险 Hooks，再将经过批准的单个 Skill 加入目标仓库。作者索引来自第三方 GitHub，安装时还会获取远端当前内容，因此适合**固定 commit/版本后再复用**，不要盲目批量引入。

**A/B：** 对 5 个重复的 C++/ROS2 任务，测无 Skill、简短仓库自定义 Skill、外部候选 Skill 的任务成功率、额外上下文、错误命令数及人工复核时间。不是安装技能越多越好。

---

## AI Coding 实战技巧精选

### 技巧 1｜Codex 改完 Node/React 服务，先跑 ProdPilot 只读规则审计

- **来源：** [ProdPilot 官方 README 与 CLI](https://github.com/prodpilotai/ProdPilot)，工程工具（非当天首发）。
- **一句话结论：** 不让 Codex 自评“可以部署”；先输出检查报告，再针对少数失败规则修改，修复后重新跑原检查器。
- **具体怎么做：** ① 用 \`uv tool install prodpilot\` 安装；② 在独立测试项目运行 \`prodpilot audit . --ci\`，保存失败规则；③ \`prodpilot fix --dry-run .\` 查看会产生什么变化；④ 将检查器的报告交给 Codex 做最小改动，之后重复只读审计并运行真实测试。
- **适合什么场景：** Codex + NestJS 外围的 Express 服务、React/Vite 小项目与实际部署前回归。**不适用 FreeSwitch/ROS2 核心 C++ 直接扫描。**
- **注意：** 不默认执行 \`prodpilot deploy\`，它可能推送代码、创建外部服务并触发持续部署。和上方组件属同一项目，去重索引只记一次。

### 技巧 2｜T3 Code 多 Worktree 反复 Rebase，用 git rerere 记住已经人工解决的冲突

- **来源：** [Git 官方 git-rerere 文档](https://git-scm.com/docs/git-rerere)，成熟 Git 方法回顾。
- **一句话结论：** 两个独立 Worktree 的相同补丁反复出现相同冲突时，Git 可以记住一次被人工确认的冲突解决方案，减少重复处理。
- **具体怎么做：** ① 在需要的仓库里运行 \`git config rerere.enabled true\`；② 第一次 Merge/Rebase 冲突时人工检查、解决并继续；③ 下次出现相同冲突后用 \`git rerere status\`、\`git rerere diff\` 审查复用结果；④ 始终检查 \`git diff --check\`、目标文件语义并运行相关测试。
- **适合什么场景：** T3 Code + Codex 并行工作树、C++ 分支集成、多次 Cherry-pick/Rebase。
- **注意：** rerere 复用旧解决方案并不保证它仍符合新代码语义；保持人工审查，不应自动提交或自动推送。

---

## 经典论文回顾

### LSD-SLAM: Large-Scale Direct Monocular SLAM — Engel、Schöps、Cremers，ECCV 2014

[原始出版信息及 DOI](https://doi.org/10.1007/978-3-319-10605-2_54) · [论文记录](https://mlanthology.org/eccv/2014/engel2014eccv-lsd/) · [原始 GPLv3 代码](https://github.com/tum-vision/lsd_slam)。

**历史位置与核心问题：** 当年很多单目直接法仍停留在局部 VO，长距离尺度漂移与一致地图困难。LSD-SLAM 不依赖稀疏角点检测来驱动前端，而是使用图像光度残差直接对齐；每个关键帧维护半稠密逆深度及不确定度，再构成关键帧位姿图，并在 Sim(3) 上处理单目尺度漂移。

~~~text
单目图像
   ↓
高梯度像素的直接光度对齐
   ↓
逆深度滤波与不确定度更新
   ↓
关键帧半稠密深度地图
   ↓
Sim(3) 关键帧位姿图 / 回环
   ↓
可修正尺度漂移的全局地图
~~~

**关键数学思想：** 直接法优化像素亮度或对比变换后的残差，依赖相机模型、光度一致性和足够纹理；逆深度估计需要多视角基线，单目原生不具绝对尺度。Sim(3) 同时表达旋转、平移与尺度，比单纯 SE(3) 更符合单目全局地图中的尺度漂移现象。

**当年为什么重要、今天仍在用的思想：** 半稠密深度与不确定性、直接光度跟踪、关键帧全局约束仍是后续视觉 SLAM 与神经地图的重要基础。

**已被改进或替代的部分：** 当前 DSO、ORB-SLAM 系列、学习式深度与视觉惯性方法在鲁棒性、光度标定、绝对尺度和跨环境可部署性方面提供不同改进。LSD-SLAM 的老仓库与早期 ROS 环境不等于最新 ROS2 成熟实现；也不能仅凭直接法实时性推断它能在无纹理或强光场景稳定运行。

**最小复现：** 在 TUM RGB-D 选取亮度变化、弱纹理和尺度变化序列，比较直接图像跟踪的失败点、深度方差、关键帧尺度与回环后位姿变化。重现原仓库时需准备适配的旧依赖环境，避免把现代开发机不兼容归因为论文算法错误。

**对当前平台的重新解读：** 今天 ERA 的“可撤销占据”、BIM-LIO 的“归因可辨识性”与经典 LSD-SLAM 的“深度不确定性和尺度修正”共同说明：地图不是简单的最新测量堆积。对于现有多 LiDAR 系统，应保留几何证据、信任度与何时允许修改全局地图的规则。

---

## 今日结论

**最值得立即验证的不是新模型参数量，而是三个更明确的工程问题。**

第一，**RK3588 NPU 不只用于神经网络。** PocketSDR-NPU 已提供源码、模型及 CPU/NPU 对照，特别适合验证共享 DDR、INT8 RKNN 和数据搬运对实际加速的限制。要按相同 CPU 核心和同一信号逐项比较，不要挪用其他 NPU 的性能倍数。

第二，**三维导航的可达性和地图可信度必须分开处理。** ERA 允许新观测修复旧占据，PoliMop 让当前底盘策略决定路径是否真的能执行；而 X-Nav 把长期语义任务与 LiDAR/里程计底层控制区分开来。这些思想可先在离线图、仿真或 Sidecar 中验证，不必破坏成熟 SLAM 主线。

第三，**LLM Agent 的工程优化应该有外部证据。** ProdPilot 要求修复后重新过规则，轨迹分析器解释 Agent 的搜索/修改/测试分布，skills-mcp 用目录检索减少找 Skill 的成本。建议按“真实任务成功率、错误修改、可复现命令、上下文开销”验证，而不是只看模型声称完成。

---

## 最值得深入研究或尝试复现的方向

| 优先级 | 方向 | 最小验收 |
|---|---|---|
| P0 | PocketSDR-NPU / RK3588 | CPU A76 vs NPU 同码捕获耗时、相关峰和 RKNN 版本 |
| P0 | ERA 可撤销地图 | 误封死格、Frontier 恢复、过早结束比例 |
| P0 | ProdPilot | Express/React 规则准确性、修复复核、无部署副作用 |
| P1 | PoliMop | 几何路径 vs 策略在环可执行率、规划 P95 |
| P1 | Body-Aligned Virtual Joints | 相同 RL 配方跨平台航向漂移、限位 |
| P1 | Budget-conditioned VLN | 不同搜索预算下目标发现率 |
| P1 | Agentic-Teacher | 从失败状态续接数据、筛选消融与新任务成功率 |
| P1 | X-Nav | 跨室内外导航状态机、目标验证与恢复 |
| P1 | trajectory-analyzer | 搜索/编辑/测试阶段分布与真实修复成功率 |
| P2 | skills-mcp | 候选 Skill 供应链审查与五任务 A/B |
| P2 | Objectives as Policies | VLM 目标代价 schema、MPC 闭环完成验证 |
| P2 | LSD-SLAM | 半稠密逆深度可信度、尺度漂移与回环修正 |

---

## 参考资料

**公开列表：** [arXiv Robotics 2026-11-16](https://arxiv.org/list/cs.RO/new) · [Software Engineering 2026-11-16](https://arxiv.org/list/cs.SE/new)。

**SLAM、信号与规划：** [GNSS NPU 论文](https://arxiv.org/abs/2611.18186) · [PocketSDR-NPU](https://github.com/taroz/PocketSDR-NPU) · [ERA](https://arxiv.org/abs/2611.17730) · [PoliMop](https://arxiv.org/abs/2611.18110) · [PoliMop 项目](https://ariael21.github.io/polimop.html) · [虚拟关节](https://arxiv.org/abs/2611.18003)。

**VLA 与控制：** [Agentic-Teacher](https://arxiv.org/abs/2611.17394) · [Budget VLN](https://arxiv.org/abs/2611.17442) · [X-Nav](https://arxiv.org/abs/2611.17598) · [Objectives as Policies](https://arxiv.org/abs/2611.18298)。

**AI 组件与 Codex：** [ProdPilot 论文](https://arxiv.org/abs/2611.17381) · [ProdPilot 代码](https://github.com/prodpilotai/ProdPilot) · [行为轨迹论文](https://arxiv.org/abs/2611.17440) · [解析器代码](https://github.com/SWE-rebench/trajectory-analyzer) · [skills-mcp](https://github.com/gengirish/skills-mcp) · [git rerere](https://git-scm.com/docs/git-rerere)。

**经典论文：** [LSD-SLAM ECCV 2014 DOI](https://doi.org/10.1007/978-3-319-10605-2_54) · [原始源码](https://github.com/tum-vision/lsd_slam)。
