---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-22"
date: 2026-11-22 09:00:00 +0800
description: "聚焦立体视觉里程计几何深度校正、GeoDiff终端停车认证、物理世界模型MoRE、机器人规划停滞诊断Unstick及WAMotor推理加速，附Skill跨系统审核与Codex实操。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-22

> **时间范围：** 2026-11-22，Asia/Shanghai，周日。首先核查最近24小时，再回补最近7天。arXiv cs.RO/cs.SE 最新常规新稿列表为 **11月20日（周五）**，cs.RO 总140条、其中首次提交79条；cs.SE 总39条、其中首次提交20条。下面八项主动态的原始 v1 均为11月18—19日 UTC，属于**时间回补**，不是11月22日首发。已按标题、arXiv ID、DOI、项目页和代码仓库同历史索引去重。

## 摘要

今天最值得关注的不是进一步增加传感器数据量，而是三个工程问题：**能否用少数可信几何约束校正深度预测；规划器既然能到达目标，是否真的能在目标区域安全停下；世界模型预测看似前进，实际执行为什么会原地卡住。**

- **定位和安全规划：** Stereo SVO+GFM 利用优化后的稀疏三维地标校正稠密预测深度；GeoDiff 将“走到附近”和“以非圆形车体在目标内完成停车”分开认证；移动机器人气源定位则把在线风场重建与主动探测路径相结合。
- **机器人控制：** Close&Safe 只改写被新障碍阻断的操作轨迹片段；Unstick 将 JEPA 规划失败中的固定点停滞与世界模型分布偏移区分；MoRE 以刚体、软体和抓持交互专家预测三维点云。
- **多智能体与性能：** MAWAM 联合预测多机械臂的未来视图和动作，WAMotor 在不重训专门草稿模型的前提下复用扩散流速度，并按时间步执行误差校验。
- **Codex 工作流：** SkillBridge 检查 Skill 在 Linux/macOS/Windows 的隐含环境契约；Git `rebase --exec` 把每个历史补丁交给真实测试，Ninja 解释无谓的 C++ 重编译。

**工程优先级：** 先使用 [Unstick开源评测](https://github.com/jhlee0619/unstick) 和 [MoRE源码、权重与数据](https://github.com/AlwaySleepy/MoRE-WM) 建立可重复的小实验；GPU 充足时再评估 [WAMotor](https://github.com/Overdue-Lin/WAMotor)。本期核实代码与官方入口，不等于本地编译或训练已经成功。

## 1. Stereo Visual Odometry + GFM：几何稀疏点校正稠密深度的尺度与偏移

**时间回补｜原始 v1：2026-11-19 03:24 UTC｜arXiv:2611.25445**

### 为什么重要
神经网络输出的高密度单目深度视觉效果好，但在不同关键帧之间可能出现尺度和整体偏移不一致。直接将这些预测当公制点云融入地图，会形成“看起来密，几何却不稳定”的结构。本研究将立体视觉和多视角优化的**可靠稀疏公制地标**作为校准锚点，保持几何 VO 的可靠定位，再从 GFM 补齐稠密结构。

### 算法模块
```text
Stereo RGB / 相机内外参
  → 滑动窗口因子图：相机位姿与稀疏三维地标
  → 每个局部子地图共享的深度 Scale/Shift 校准
  → 选择性关键帧运行几何前馈模型，生成密集深度
  → 子地图内 SE(3) GICP 配准
  → 相邻子地图 Sim(3) 对齐
  → 全局因子图：轨迹 + 公制稠密重建
```

### 假设、实时性与鲁棒性
要求立体相机标定与同步、足够视差和多视角特征，子地图尺度/偏移校正依赖真实可用的稀疏地标。只在关键帧生成密集深度以平衡算力。作者在公开及自采数据上报告与几何/学习基线相当的定位精度及更可靠的稠密几何，但摘要没有统一可核查的嵌入式 FPS、ATE 或 P99，不应自行填数。

### 可复现性、风险与工程启发
本次未独立确认完整官方源码与安装入口。最小验证是固定双目序列，对比“原始 GFM 深度”“逐帧独立缩放”“局部子地图共享 Scale/Shift”的跨帧深度误差、点云平面残差、轨迹 RPE、GPU 内存和建图耗时。不要允许错误深度覆盖可靠 LiDAR 观测。**适合关注：** 多相机 BEV/稠密地图、Stereo VO、移动机器人数字孪生。对已有三雷达系统，推荐将此法作为视觉几何附加层，而非立即替换主 LIO。

来源：[原论文](https://arxiv.org/abs/2611.25445)。

## 2. GeoDiff：不是抵达目标点，而是证明非圆形底盘能在目标内停下

**时间回补｜原始 v1：2026-11-19 14:19 UTC｜arXiv:2611.26167**

### 为什么重要
狭窄门洞、充电工位、贴柜停靠的任务中，规划器找到一条避障路径，并不证明机器人的多边形车体在制动后能完整处于目标容差内。GeoDiff 将**原目标的安全停止集合、终端修复与可复用的认证条件**组成独立规划接口。

### 算法模块
```text
带非圆形 Footprint 的自由空间 + 原始目标与容差
  → 候选运动程序与可达停车集合
  → 确认停止后的车体是否完整落在原目标区域
  → 失败时由证据 Witness 引导修改终端段
  → 将几何与制动约束分解成可复用认证子问题
  → 同时返回：原路线可用性 / 目标停车证书
```

### 结果、假设与风险
作者在楼层平面图任务的指定15秒预算内，5 cm 停靠容差的认证数量由基线44/139提高至61/139；在由公开 BARN 地图派生的Jackal形状任务中为202/270，对照3/270。最值得关注的区别是：外部适配器可从119条原生候选路线中只认证13条，**路径存在不等于满足认证条件**。这些是论文的几何/规划证明协议，不是现实机器人已经通过安全认证；定位误差、制动模型失配和动态障碍仍可能使证明条件失效。

### 可复现性与工程启发
尚未核实官方完整代码，不能提供虚构的构建命令。建议以真实差速巡检底盘 Footprint、柜体入口和±5/10 cm目标容差构造离线测试，比较A*/Hybrid A*“到达”与完整 Footprint 终端停稳的成功数、认证时间及制动裕量。**适合关注：** 配电室巡检贴柜停靠、差速车充电、狭窄工位和需要明确安全停稳判据的系统。

来源：[GeoDiff论文](https://arxiv.org/abs/2611.26167)。

## 3. Mapping the Wind：室内气体源定位，移动测风、物理扩散和主动搜索联合闭环

**时间回补｜原始 v1：2026-11-18 19:11 UTC｜arXiv:2611.25067**

### 为什么重要
化学/燃气泄漏巡检并不等价于查找浓度最高的点。气流会把气体带离源头，机器人自身运动影响传感器读数，建筑内风场又会随位置改变。该研究在线重建不均匀风场、模拟候选源的气体分散，再按概率地图选择下一观测位置。

### 算法模块
```text
机器人定位 + 风速/风向传感器 + 气体浓度
  → 增量重建空间变化的风场与不确定性
  → 候选泄漏源位置逐个进行轻量扩散预测
  → 实际气体观测更新源位置后验概率
  → 考虑风场预测可靠性的主动路径规划
  → 继续取样、更新 belief，直到定位置信度足够
```

### 传感器、实时性、鲁棒性
依赖风和气体传感器的时间同步、采样滞后标定与机器人准确位姿；强湍流、突然开门和传感器饱和都可能让简单扩散模型失效。作者使用高保真仿真与室内实物实验验证，在空间变化气流中优于缺少物理先验的搜索，但当前摘要未提供可统一引用的精确相对改善及端侧 P99。

### 可复现性与工程启发
尚未独立核实完整官方源码。可以先固定 Gazebo/CFD 生成的浓度+风场，在同一移动预算内比较“沿最大浓度爬坡”“不考虑风场的贝叶斯搜索”“风场约束的主动搜索”，记录首次源头发现时间、后验置信度、移动距离和模型误差。**适合关注：** 工业移动巡检、危险环境传感器布置、主动采样。危险泄漏现场的作业安全不能由该概率模型单独承担。

来源：[原论文](https://arxiv.org/abs/2611.25067)。

## 4. Close&Safe：机械臂擦拭轨迹遇到障碍，只修被阻断的一小段

**时间回补｜原始 v1：2026-11-19 12:39 UTC｜arXiv:2611.26031**

### 为什么重要
擦拭、喷涂、打磨等任务定义的是持续的末端轨迹，而不是只到达终点。传统重规划可能为了避障而大幅改写整段轨迹，使本来可执行的任务表面也无法覆盖。Close&Safe 保留所有仍可执行的原轨迹，仅在碰障区间沿配置空间障碍边界搜索短绕行，并尽快回到原轨迹。

### 算法模块
```text
示教末端轨迹 + 冗余机械臂模型 + 新增障碍
  → 识别发生冲突的最短时间区间
  → 在原轨迹附近构建 C-space 边界样本与 Roadmap
  → 寻找最小偏离、最早重新接入的绕行
  → 其他区间严格跟踪原参考轨迹
  → 真机碰撞检查和约束验收
```

### 结果、假设与风险
论文在仿真与Franka真机实验中报告，能在无碰撞前提下恢复52.4%—78%（具体依赖场景和指标）的被保留任务路径部分；不能把该范围解释成通用任务成功率。方法依赖机器人正运动学、关节限幅、障碍模型和可用冗余自由度；动态障碍与错误深度感知会破坏输入假设。

### 可复现性与工程启发
未确认完整官方代码。可用MoveIt/MuJoCo建立一条平面擦拭轨迹，在中间插入新障碍，比较整段重新规划、局部约束避障和边界绕行的“原轨迹保留比例”、碰撞次数、末端位置/接触误差、规划P95。**适合关注：** 机械臂巡检、表面接触操作、移动操作。关键不是“避障成功”一个指标，而是“原任务保留多少”。

来源：[原论文](https://arxiv.org/abs/2611.26031)。

## 5. Unstick：JEPA 规划看似每轮有进展，现实中却原地不动

**时间回补｜原始 v1：2026-11-19 02:57 UTC｜arXiv:2611.25415**

### 为什么重要
以JEPA/DINO特征为潜空间的世界模型，会预测推物体动作的未来状态。遇到失败时，研究者常认为是世界模型分布偏移、应当在当前Episode重新训练。但作者回放真实闭环后发现，在多数指定条件下**至少96%的失败属于 Stall**：物体没移动，模型却预测在前进，暖启动的梯度规划器重复提交几乎相同的无效动作。

### 算法模块
```text
当前观察、动作与JEPA预测
  → 记录预测进展和真实进展残差
  → 检测 Stall / 重复同一候选计划
  → Unstick-Mem：保留本Episode预测误差记忆
     或 Unstick-ReInit：每次重规划重新初始化
  → 固定世界模型权重继续优化动作候选
```

### 实验与鲁棒性
作者在形状、视觉和动力学转移的推物体及迷宫任务中，说明重新初始化在形状变化下有帮助，但对于视觉变化明显弱于有界残差记忆。它没有证明所有世界模型失效都源自规划固定点；模型本身严重错误时仍要处理分布偏移。

### 已核实工程入口
[MIT代码](https://github.com/jhlee0619/unstick) 已公开，含多任务配置、`scripts/run_eval.py`、`scripts/finetune.py` 和 [预训练/微调权重](https://huggingface.co/jhlee0619/unstick)。作者环境要求Conda及旧版MuJoCo 2.1/D4RL，建议隔离：
```bash
git clone https://github.com/jhlee0619/unstick.git
cd unstick
conda env create -f environment.yml
conda activate unstick-eval
# 另按 README 准备 D4RL、MuJoCo 2.1、DATA 与 CKPT
hf download jhlee0619/unstick --local-dir FT
python scripts/run_eval.py --help
```
`--help` 是低风险的参数探测，不能代替作者按具体路径指定的完整Eval脚本。

### 适合谁关注与工程启发
适合JEPA世界模型、PushT、生成式规划、机器人长任务状态机，也能启发Codex：不能用“工具调用次数”“自述进度”来证明实际任务推进。最小A/B：固定同一Checkpoint和Episode，比较无记忆、误差记忆、每轮重启三种方案的实际物体位移、连续停滞次数、成功率和模型调用数。不要使用无界随机重试绕过底层安全限制。

来源：[论文](https://arxiv.org/abs/2611.25415) · [源码](https://github.com/jhlee0619/unstick) · [权重](https://huggingface.co/jhlee0619/unstick)。

## 6. MoRE：三维世界模型按刚体、软体和抓取接触分配专门运动专家

**时间回补｜原始 v1：2026-11-19 01:24 UTC｜CoRL 2026｜arXiv:2611.25336**

### 为什么重要
同一机械臂推动塑料盒、拖动布料、抓取玩具时，物理运动规律明显不同。把所有接触混到一个统一的点云运动预测器里，会使模型难以兼顾三种动态。MoRE以刚体非抓持、软体非抓持、软体抓持专家分别学习局部运动，使用短交互历史判断当前物理模式。

### 算法模块
```text
历史点云 + 末端执行器动作点云
  → 接触/材质模式推断
  → 刚体 / 可变形非抓持 / 可变形抓持专家
  → 预测未来点云与3D Flow
  → MPC采样候选推动动作
  → Chamfer目标误差打分、执行、重新观察
```

### 速度与结果
项目作者展示的3D点云预测约20 FPS，并提供真实机器人和仿真的MPC Rollout。在CoRL 2026的指定刚体/软体任务中，预测和真实闭环规划优于所比世界模型；但不要将20 FPS当作所有候选Rollout在端侧的完整MPC频率。接触模式切换、遮挡、多物体重叠及点云分割错误都可能使专家路由失效。

### 源码与最小运行
[官方开源仓库](https://github.com/AlwaySleepy/MoRE-WM)、[项目页](https://alwaysleepy.github.io/MoRE-WM-site/)、[数据](https://huggingface.co/datasets/MoRE-WM/MoRE-Data)、[权重](https://huggingface.co/MoRE-WM/MoRE-Model)已核实。仓库含CUDA/PointNet2依赖与 `rollout/rollout.py`，可以先做环境和单段预测验证：
```bash
git clone https://github.com/AlwaySleepy/MoRE-WM.git
cd MoRE-WM
conda env create -f environment.yml
conda activate morewm
pip install -r requirements.txt
# 另按 README 安装 PointNet2 CUDA 扩展与 Uni3D 权重
# 并下载公开模型/数据、设置 MOREWM_MODEL_DIR 等路径
python rollout/rollout.py --help
```

### 适合谁关注与工程启发
适合点云世界模型、机械臂接触操作、物理MPC和Sim2Real。先验证单步预测的Chamfer误差与路由混淆，再考虑复杂多步MPC；建议真实/仿真场景分开统计，不因预测视频看着合理就断言动力学准确。大型权重与CUDA扩展的显存及许可证条件需要实际检查。

来源：[论文](https://arxiv.org/abs/2611.25336) · [项目](https://alwaysleepy.github.io/MoRE-WM-site/) · [官方源码](https://github.com/AlwaySleepy/MoRE-WM)。

## 7. MAWAM：多机械臂联合预测彼此动作后的世界，而不是独立执行各自VLA

**时间回补｜原始 v1：2026-11-18 19:39 UTC｜arXiv:2611.25105**

### 为什么重要
两个机械臂叠放衣物、交接雨伞时，一方动作会立即改变另一方要面对的几何。独立规划的单臂模型不一定理解共同接触与交接的时序。MAWAM在单机器人世界动作模型主干上加入跨机器人注意力，使多臂的动作Token与未来视图Token联合去噪，但仍保留每个机器人的单独执行接口。

### 算法模块
```text
多台机械臂的当前视图、本体状态与联合目标
  → 各机器人动作/未来图像Token
  → Cross-Agent Attention共同去噪
  → 各自可执行的Action Chunk + 联合未来视图
  → 分机器人执行、同步观察与重规划
```

### 实验与适用边界
在三个真机任务（收集洗衣袋、折浴巾、雨伞交接）上作者报告平均成功率**67.8%**，比同演示与相机设置下的MA-VLA高**18.9个百分点**。仿真八项最多四机械臂任务平均**90.3%**；移除跨臂注意力时，四臂传递任务的成功率由95%降至39%。这些是特定任务与控制器的成功率，不能自动推广为多台移动机器人组队导航。

### 可复现性、风险与工程启发
本轮未核实完整官方可构建训练/推理仓库，不提供未经证实的命令。可以先在双机械臂MuJoCo中构建异步抓取/交接，比较独立单臂预测和联合状态预测，测相互碰撞、交接超时、失败恢复和计算P95。**适合关注：** 双机械臂搬运、多人形协同操作、多机器人世界模型。必须保留执行层互斥、急停与实际状态确认。

来源：[MAWAM论文](https://arxiv.org/abs/2611.25105)。

## 8. WAMotor：按扩散时间步修正投机推理的误差预算，而非一律复用速度

**时间回补｜原始 v1：2026-11-19 UTC｜arXiv:2611.25413**

### 为什么重要
世界动作模型的Flow Matching一般需要多次去噪网络调用。直接把上一步速度复用于接下来若干步，看似可省推理，却遇到两个问题：不同时间段速度变化并不均匀；非均匀时间间隔会放大部分残差。WAMotor延后投机起点选择可靠速度锚点，并按积分步长缩放每次候选的可接受误差。

### 算法模块
```text
World Action Model去噪速度轨迹
  → 检测可复用的Anchor Time Steps
  → 跨步Velocity Draft
  → 按 Δt 的误差容差验证候选
  → 通过则跳过完整网络调用，失败则计算真实速度
  → 完成Action Chunk并执行
```

### 实验结果
作者在Joint-WAM/Fast-WAM/Faster-WAM及LIBERO、RoboTwin2.0、LIBERO-Plus的指定实验里报告**端到端加速2.86—4.28倍**，保持相近任务成功率。需注意这不是机器人运动控制环实际提频4倍，准确性与加速收益都依赖模型、验证阈值、时间步采样和硬件。

### 源码与最低入口
[官方代码](https://github.com/Overdue-Lin/WAMotor) 已核实包含 `src/wamotor/models/wan22/speculative/`、三套评测环境、Latency脚本与配置。作者要求Python3.10、PyTorch2.7.1与CUDA12.8，并单独下载WAM Checkpoint：
```bash
git clone https://github.com/Overdue-Lin/WAMotor.git
cd WAMotor
bash scripts/setup/install_core.sh
source .venv/bin/activate
mkdir -p checkpoints
export DIFFSYNTH_MODEL_BASE_PATH="$(pwd)/checkpoints"
# 准备作者README列出的模型权重与归一化统计后：
# bash scripts/setup/install_libero.sh
# bash experiments/latency/run_latency.sh --speculative
```

### 适合谁关注与工程风险
适合需要GPU的VLA/WAM推理优化。先比较相同任务、相同模型的基线与投机推理Latency、成功率、跳步接受率、GPU峰值和失败重试；不要在低算力嵌入式平台上仅凭论文倍数承诺部署。此项不会直接改善非Flow模型。

来源：[论文](https://arxiv.org/abs/2611.25413) · [官方源码与评测脚本](https://github.com/Overdue-Lin/WAMotor)。

## AI / LLM 附属框架与开源工程组件

### SkillBridge：跨Linux/macOS/Windows的Agent Skill契约静态检查、动态复现与修复

**时间回补｜v1 2026-11-19 UTC｜ICSE 2027录用研究**

**具体痛点：** 一个Skill在作者Mac上可用，移到Linux容器却因为`brew`、PowerShell、路径分隔符、可执行权限、缺少二进制或工具声明与安装步骤冲突而失败。盲目在所有OS运行全部Skill不仅慢，还会产生工具开销、模型Token和潜在安全风险。

**关键模块和接口：** SkillBridge先提取Skill描述/元数据/脚本/包管理/执行入口的系统依赖，静态筛查隐含契约；然后对高可疑组合执行动态任务、保留日志和根因证据；最后修改引发问题的契约字段并回放验证。

作者分析**1,090个Skill × 3系统 = 3,270个组合**，优先筛选后用185次动态验证确认38个OS问题，均匀随机采样按作者估计需要约865次；在受控测试中，审查员评估的目标任务通过率由30.6%增至38.4%（+7.8个百分点）。这不是“所有Skill的可靠性自动提高7.8%”。

**真实开源程度：** [论文](https://arxiv.org/abs/2611.26256)、[作者仓库](https://github.com/TankTechnology/SkillBridge) 已核实。公开仓库的`code/`包含实验分析与复现管道、`code/tests/`测试及`requirements.txt`，但原始Skill包、私有数据库、凭据和部分执行归档没有随Git公开；它不是已发布为`pip install skillbridge`的成熟Codex插件。未核实完整跨OS实验可一键运行，许可证也不能据此自行认定。

**最小本地验证入口：**
```bash
git clone https://github.com/TankTechnology/SkillBridge.git
cd SkillBridge
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q code/tests
```
这是基于作者`code/README.md`目录结构的轻量测试尝试，**并未本地执行**；如因环境或依赖缺失失败，应按子模块实际入口排查，不能声称已跑通全量实验。

**Codex/T3 Code/Linux工程价值与A/B：** 对自己已有的五个自研Skill，逐项核对`SKILL.md`中的平台声明、CLI命令、路径、权限与依赖，并在Arch Linux和Ubuntu Distrobox隔离运行只读任务。比较修复前后的首次成功率、失败定位时间、Token、外部网络和文件写入副作用。静态分析只能缩小候选集合；权限隔离、来源信任和真实执行仍需独立检查。

## AI Coding 实战技巧精选

### 技巧 1｜让Codex Rebase的每一笔Commit经过可执行测试

- **来源：** Git维护者，[git-rebase官方文档](https://git-scm.com/docs/git-rebase)；工程补充回顾，非当天软件更新。
- **一句话结论：** 用`git rebase --exec`在重放每个补丁后执行真实测试。这样比最终才发现五个Commit里的第三个已经破坏API，更容易定位因果。
- **具体怎么做：**
  1. 在独立Worktree与短分支上确认`git status --short`为空，先建立快速且稳定的相关测试命令；
  2. 执行以下示例（将`BASE`替换为真实上游引用）：
```bash
git rebase --exec 'cmake --build build -j4 && ctest --test-dir build --output-on-failure' BASE
# 如果某一笔提交检查失败，修复并审查后再执行
git rebase --continue
```
  3. 记录第一个失败的Commit，完成Rebase后仍运行最终全量回归、`git range-diff`和`git diff --check`。
- **适合：** Codex/T3 Code多Worktree、C++/ROS2、长期维护多提交补丁。
- **注意：** 历史中某些Commit本身不支持独立编译时该策略需改为分段检查；不能在共享已发布分支上随意改写历史。此技巧需要实际测试命令，不是只写一句“请检查”。

### 技巧 2｜Codex构建突然变慢时，让Ninja先解释为什么重编译

- **来源：** Ninja作者维护的[官方构建手册](https://ninja-build.org/manual.html)和其`-d`调试命令；工程补充回顾。
- **一句话结论：** 没有必要先要求Codex重构整个CMake工程；应先找到究竟是头文件时间戳、生成步骤、编译命令变化还是依赖图使大量目标被认为过期。
- **具体怎么做：**
```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
ninja -C build -d explain your_target 2>&1 | tee /tmp/ninja-why.txt
ninja -C build -t stats
```
  然后让Codex对照解释日志与`build.ninja`或`compile_commands.json`定位重复构建的根因，最小修改后连续运行两次同一构建，记录首次及热构建时间、触发目标数和编译输出是否一致。
- **适合：** Arch Linux、CLion、C++/ROS2大型工程、频繁切换Codex工作树。
- **注意：** `ninja -t stats`不同版本可能只在实际构建中报告统计；不能因为缓存命中就跳过最终链接/运行时测试。只比较相同构建目标和配置。

## 经典论文回顾

### On-Manifold Preintegration for Real-Time Visual-Inertial Odometry — Forster 等，2015/2017

**历史位置：** Christian Forster、Luca Carlone、Frank Dellaert、Davide Scaramuzza；2015-12-08公开预印本；正式发表在 *IEEE Transactions on Robotics* 2017年33(1):1—21（DOI:10.1109/TRO.2016.2597321）。

**核心问题：** IMU频率可能达到数百Hz，如果每个角速度/加速度采样都在大因子图中显式建状态，关键帧之间的非线性优化会变得昂贵。简单把旋转当三维向量加法积分又忽略SO(3)的流形结构，影响噪声传播与偏置更新。

**关键数学与算法：**
```text
两视觉关键帧之间连续IMU测量
  → 在SO(3)上预积分相对旋转 ΔR
  → 同时累积 Δv、Δp 与协方差
  → 用Jacobian修正IMU Bias小变化
  → 一个预积分因子连接相邻关键帧姿态、速度、Bias
  → 与视觉/激光/回环因子构成增量平滑因子图
```

旋转更新不是普通向量求和，而是类似`ΔR ← ΔR · Exp((ω-b_g)Δt)`的群上累积；完整噪声传播、重力处理和雅可比应以原论文实现为准。

**当年为何重要：** 它给出了IMU采样与关键帧非线性优化解耦的系统推导，让Bias修正、协方差传播和GTSAM等增量优化器易于组合。现代VIO、LIO和多传感器图优化仍大量借鉴这种思想。

**假设与局限：** 依赖正确的IMU时间戳、外参、噪声密度与随机游走模型；预积分并不修复漏测、时间偏移、LiDAR运动去畸变或几何退化。Bias变化太大时，线性修正不能无限复用，需要重新积分。现代连续时间融合和直接原始IMU因子在某些运动模式下提供不同权衡。

**公开代码与最小复现：** [arXiv原文](https://arxiv.org/abs/1512.02363)、[正式DOI](https://doi.org/10.1109/TRO.2016.2597321)、[GTSAM](https://github.com/borglab/gtsam)。选取一段EuRoC/自采IMU+Stereo或LiDAR数据，分别运行原始离散IMU残差与预积分因子，比较每关键帧更新时间、Bias收敛、RPE、时间偏移敏感性和CPU占用。

**对三雷达平台的重新解读：** 两台iRay若各有IMU，不应只因为数量多就把所有高频IMU约束重复加权。应先确认统一时钟、各IMU到机体外参及噪声相关性，并在明确的主惯性参考框架下选择信息互补的因子，而不是通过重复约束制造虚假置信度。

## 今日结论

本期有两条相互呼应的技术原则。

第一是**可信观测与受约束执行分层**：Stereo SVO用可靠地标校正密集深度，GeoDiff要求证实真实停车条件，Close&Safe尽量保留任务原有可执行段，工业巡检的气源搜索则要将风场与传感器不确定性显式进入路径决策。

第二是**世界模型的预测进展不能当作实际进展**：Unstick发现了循环规划固定点；MoRE区分不同接触动力学；MAWAM联合多个机械臂未来；WAMotor减少重复推理但依旧必须检查时步误差。上述论文的仿真成功率、模型查询速度与真机闭环安全不能混同。

对于C++和ROS2研发，SkillBridge、`git rebase --exec`与Ninja诊断都强调可验证证据和最小改动：任何工具若不能降低真实Bug、构建开销或人工复核量，就不值得继续增加系统复杂度。

## 最值得深入研究或尝试复现的方向

| 优先级 | 方向 | 最小验收指标 |
|---|---|---|
| P0 | GeoDiff非圆形机器人终端停车 | Footprint完整进入目标、制动可行性、P95认证时间 |
| P0 | Unstick世界模型规划停滞 | 实际位移与预测差、固定点次数、成功率 |
| P0 | MoRE点云多物理世界模型 | 刚体/软体路由、Chamfer、20FPS条件、MPC耗时 |
| P0 | Codex rebase --exec | 第一个坏Commit定位率、回归通过、执行成本 |
| P1 | Stereo SVO+GFM | 深度Scale/Shift漂移、稀疏地标RPE、显存 |
| P1 | Close&Safe | 原轨迹保留率、局部障碍净空、控制P95 |
| P1 | WAMotor | 同模型同GPU延迟/成功率、跳步接受率 |
| P1 | SkillBridge | Arch/Ubuntu跨OS Skill通过率、权限与依赖问题 |
| P1 | 室内风场主动气源搜索 | 首次定位时间、风场误差、真实路径长度 |
| P2 | MAWAM | 跨机械臂联合预测与交接完成率 |
| P2 | Ninja编译解释 | 无必要重编译次数、两次Build耗时 |
| P2 | Forster IMU预积分 | Bias修正、RPE、关键帧优化成本 |

## 参考资料

**最新列表：** [arXiv Robotics 2026-11-20](https://arxiv.org/list/cs.RO/new) · [arXiv Software Engineering 2026-11-20](https://arxiv.org/list/cs.SE/new)。

**定位/规划：** [Stereo SVO+GFM](https://arxiv.org/abs/2611.25445) · [GeoDiff](https://arxiv.org/abs/2611.26167) · [移动气源定位](https://arxiv.org/abs/2611.25067) · [Close&Safe](https://arxiv.org/abs/2611.26031)。

**控制/世界模型：** [Unstick](https://arxiv.org/abs/2611.25415) · [Unstick代码](https://github.com/jhlee0619/unstick) · [MoRE](https://arxiv.org/abs/2611.25336) · [MoRE源码](https://github.com/AlwaySleepy/MoRE-WM) · [MAWAM](https://arxiv.org/abs/2611.25105) · [WAMotor](https://arxiv.org/abs/2611.25413) · [WAMotor源码](https://github.com/Overdue-Lin/WAMotor)。

**AI Coding：** [SkillBridge论文](https://arxiv.org/abs/2611.26256) · [SkillBridge开源实验仓库](https://github.com/TankTechnology/SkillBridge) · [Git rebase原始文档](https://git-scm.com/docs/git-rebase) · [Ninja官方手册](https://ninja-build.org/manual.html)。

**经典论文：** [Forster等预积分论文](https://arxiv.org/abs/1512.02363) · [IEEE TRO DOI](https://doi.org/10.1109/TRO.2016.2597321) · [GTSAM](https://github.com/borglab/gtsam)。
