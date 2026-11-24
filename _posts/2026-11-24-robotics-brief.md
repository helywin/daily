---
layout: post
title: "机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-24"
date: 2026-11-24 09:00:00 +0800
description: "Instant-LIVO 紧凑多传感器里程计、声呐公制 SLAM、ROS2 确定性仿真、延迟补偿控制与 Agent 执行证据。"
categories: [机器人技术简报]
tags: [SLAM, 机器人控制, AI-Coding, 大模型]
---

# 机器人 / SLAM / 控制 / AI Coding 技术深度简报｜2026-11-24

## 摘要

今日核验 arXiv 2026-11-23 公开批次：cs.RO 共125项、首次提交69项；cs.SE 共43项、首次提交14项。公开列表日期与原始 v1 提交日期不同。本轮先检查24小时，再按规范回补7天；以下八项 v1 为11月19—20日 UTC，标记时间回补。与原有1454条覆盖记录按标题、标识及项目地址查重；经典 DWA 已覆盖，明确作不同角度复盘。

本期重点不是增加模型参数，而是控制资源、观测可信度和执行时间。Instant-LIVO 对 ARM 端尤为值得关注，let_ros 则可让 ROS2 测试与调度噪声解耦。FORTH 的仓库自审推翻了若干原始优势，尤其值得从科研复现角度审读，而不是照搬摘要。以下建议均为待执行实验，未在本地编译或运行模型。

## 1. Instant-LIVO：紧凑 OctVox 与单参考帧视觉地图

时间回补｜v1 2026-11-20 UTC｜[论文](https://arxiv.org/abs/2611.27633)｜[官方实现](https://github.com/Faker-0714/Instant-LIVO)

### 为什么重要与算法模块

基于 FAST-LIVO2 的紧耦合系统。几何地图以空间哈希组织，每个块最多保留八个子体素代表点；缓存辅助分阶段 KNN 根据距离界提前结束搜索，按需拟合局部平面。视觉只维护一个有界参考帧地图，按照跟踪质量切换参考帧，并使用 Schmidt 型更新考虑参考位姿不确定性与当前状态的相关性。

IMU传播 → LiDAR几何修正 → 图像光度修正 → 参考帧选择与地图更新。

减少重复地图数据和邻域访问，而不是仅降低点云输入频率。单参考帧不意味着整个几何地图恒定大小，更不等于完整全局回环 SLAM。

### 实验、假设与风险

作者在32个公开及自采数据序列/基准上评估，报告 x86/ARM 平均处理速度分别提升约2.3倍/2.1倍，峰值内存分别约为比较基线的1/20、1/13。不能将其直接外推为 RK3588 的实测速度或全栈内存比例。需有准确内外参、时间同步、点云去畸变；强光、弱纹理、几何退化可能同时影响两种观测。体素容量需按设备实际内存配置。

### 可复现性与工程落地

已通过 GitHub 读取真实 README，支持 Ubuntu 20.04、ROS Noetic、C++17、PCL、Eigen、OpenCV、Sophus；有 MID360、Hesai、Ouster、RoboSense 的配置，不能理解为三路同步融合已完成。许可证及第三方依赖商用义务仍需核对。

~~~bash
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src
git clone https://github.com/Faker-0714/Instant-LIVO.git
cd ~/catkin_ws
source /opt/ros/noetic/setup.bash
mkdir -p src/Instant-LIVO/Log/{result,pcd,image,Colmap/sparse/0}
catkin_make
source devel/setup.bash
roslaunch instant_livo mapping_mid_360.launch
~~~

另一个终端播放已标定的 ROS1 bag；先安装 README 指定依赖。不要在生产机器人上直接启动未经适配的配置。

### 适合谁关注

多雷达、ARM 边缘计算及 LIVO 工程。建议先用相同 MID360 数据比较 FAST-LIVO2 与 Instant-LIVO 的 ATE/RPE、每帧耗时 P95、RSS 峰值及每米地图增长，再测试固定采样预算的前后雷达融合。对现有三雷达方案，优先借鉴地图后端而非一次性替换状态估计。

## 2. BRINA：用海床提供声呐里程计的公制尺度

时间回补｜v1 2026-11-20 UTC｜[论文](https://arxiv.org/abs/2611.27817)｜[全文](https://arxiv.org/html/2611.27817v1)

### 为什么重要与算法模块

前视声呐每个回波的仰角不可直接观测，单纯匹配图像特征存在尺度歧义。BRINA 利用波束首个海床回波估计离底高度，结合 IMU 姿态和声呐几何，把匹配的 AKAZE 特征投影到局部海床平面。惯性、声呐相对运动及回环共同形成增量因子图；回环利用强度拼图和深度子图，并做一致性验证。

### 实验与边界

作者在水下机器人仿真和无人水面艇十次现场任务中验证两款声呐。任务 B 航程804米，加入回环后相对 FAST-LIO2 参考的平均误差5.55米降至3.35米，终点误差10.0米降至6.3米，100米位移误差4.1%降至2.9%。参考不是独立绝对真值；任务 A 平均误差改善仅0.05米。海床倾角和坡度变化会破坏局部投影，低纹理和多径仍是风险。

### 可复现性与工程落地

尚未核实完整公开源码。最小实验先生成可控坡度的二维声呐几何，比较平面假设下的尺度误差和加入 IMU 约束后的漂移，再对真实数据验证闭环。适合水下巡检、声呐与惯性融合；陆地机器人可借鉴利用独立物理尺度约束解决弱观测，而非直接移植算法。

## 3. LiDAR 仿真密度校验：光束数量相同不等于点云相同

时间回补｜v1 2026-11-20 UTC｜[论文](https://arxiv.org/abs/2611.27379)

### 为什么重要与方法

将仿真雷达配置直接照抄厂家线数、频率与视场并不能保证物体点密度接近真机。研究仅使用3D包围盒和点云，把目标距离分箱，统计目标点数随距离的变化，再由 MAPE 构造有界 Density Similarity Score（DSS）。不需要网络或语义模型。

### 实验、假设与风险

作者在三种 CARLA 配置中发现，采用非均匀垂直光束角的定制方案效果最好，DSS 为0.559–0.709；仍非完全一致。该指标只覆盖距离相关密度，不评价强度、多回波、时间戳、运动畸变、遮挡噪声或定位精度。比较时需保持物体尺寸、视角及统计分箱一致，不能将近距离箱的点数差异全部归因于雷达模型。

### 可复现性与工程落地

未核实作者代码；可独立复现距离分箱和点数统计。对 Helios 16P、iRay 96线或 MID360，分别录制同一组不同距离的静态标定目标，再与对应仿真做密度曲线、空箱比例和局部法向分布对照。最后运行同一个 LIO 评估 RPE、退化频次及 CPU 耗时。适合多雷达仿真、Sim2Real 和传感器选型。

## 4. 群体延迟补偿：优先补偿 CBF 使用的邻居状态

时间回补｜v1 2026-11-20 UTC｜[论文](https://arxiv.org/abs/2611.27540)｜[全文](https://arxiv.org/html/2611.27540v1)

### 为什么重要与算法模块

多机通过共享 TDMA 链路交换距离、方位，机群规模越大，每台机器人获得的邻居状态越陈旧。研究把平均场博弈路由与独立 CBF 安全过滤器分层，在仿真中发现路由相对不敏感，安全过滤却受到明显影响。比较将预测补偿放在路由或安全过滤器的不同方式，包括基于速度估计与学习预测。

### 实验与风险

100个 Agent 的指定仿真中，无补偿无碰撞极限约125ms；速度预测约250ms、学习预测约350–400ms的设置仍有少量碰撞，不能称为安全保证。保持测量噪声时，两种预测器在100机条件下约175ms，说明噪声模型对结果很重要。简单增大间距在瓶颈场景还可能加重拥堵与约束松弛。

### 可复现性与工程启发

尚未核实完整源码。先用二维机器人仿真对比无补偿、路由补偿、安全层补偿、两层补偿；统一延迟注入、控制频率和噪声，统计碰撞、最小净空、QP不可行率、通过量及预测误差。真实机器人需独立急停及有效状态超时处理。适合多机器人走廊调度、无人机控制和延迟敏感的局部避障。

## 5. Many Plans at Once：预算内生成真正不同的可行轨迹

时间回补｜v1 2026-11-20 UTC｜[论文](https://arxiv.org/abs/2611.27012)

### 为什么重要与算法模块

只生成一条最优轨迹，在临时障碍出现或下游需求改变后往往只能从头规划。MPAO 将低代价与轨迹间差异同时纳入连续时间规划：采样天然满足边界条件的神经轨迹参数化，训练共享修正，保存已通过验证的候选，根据已有解改变后续采样方向。Anytime 形式使规划时间增加时能够继续扩充候选集。

### 实验、假设与风险

作者在四类领域40个实例与五种基线比较，在相同预算下仅 MPAO 完成全部实例；接触操作的部分任务可获得更多近最优候选。不能从40个实例推导普适完备性。轨迹距离的定义会影响多样性，连续碰撞约束及动力学可行性仍依赖验证器；密集时间采样也可能遗漏中间越界。

### 可复现性与工程落地

尚未核实完整源码。建议在双通道环境中生成多个 B-spline 候选，以同伦类别、空间距离和时间代价分组，随后封闭首选通道，比较单轨迹重规划与候选切换的耗时、可行率和内存。适合狭窄通道、跨楼层导航、接触规划与 MPC 热启动。

## 6. let_ros：让 ROS2 回调并行执行但保持逻辑行为一致

时间回补｜v1 2026-11-19 UTC｜[论文](https://arxiv.org/abs/2611.26676)｜[源码](https://github.com/ChengziHuang/let_ros)

### 为什么重要与算法模块

同一份 ROS2 输入，在不同线程调度下可能因消息到达顺序不同而产生不同控制输出，难以复现偶发回归。let_ros 引入 Logical Execution Time：节点在预定逻辑时刻读取消息、按照计算与传输延时发布消息，运行时根据已知依赖关系把独立回调分配到多个线程，允许真实计算乱序但逻辑通信不乱序。

### 实验与边界

作者在工业场景报告相对同步并行仿真最高2.6倍加速，与异步并行仿真比较的消息内存开销低约一个数量级。这是仿真器结果，不是生产 DDS 的真实实时性保证。外部 IO、随机数、共享可变状态、未纳入模型的线程行为仍需受控；配置逻辑时延不能代替真实测量。

### 可复现性

已核实 Apache-2.0 README、ROS2 Jazzy、Ubuntu24.04、C++20 和五节点驾驶示例。依赖安装后：

~~~bash
mkdir -p ~/let_ros_ws/src
cd ~/let_ros_ws
git clone https://github.com/ChengziHuang/let_ros.git src/let_ros
source /opt/ros/jazzy/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -y
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
graphs="$(ros2 pkg prefix let_ros_examples)/share/let_ros_examples/graphs"
ros2 run let_ros let_ros_run --nodes "$graphs/pipeline.txt" --engine ooo --workers 4 --horizon 10s --computation-delays "$graphs/pipeline_computation_delays.txt" --transition-delays "$graphs/pipeline_transition_delays.txt" --results results.jsonl --record-topic /cmd
~~~

### 适合谁关注与工程落地

ROS2 C++ 导航、控制状态机及 Codex 回归工作流。将同一输入分别运行单线程和四线程，对照逻辑时间及输出字段，而非只看日志顺序；测吞吐、峰值内存、重复执行一致性。真实系统仍应单独评估硬件时延与 DDS QoS。

## 7. SMC 潜空间规划：让候选动作群体逐步演化

时间回补｜v1 2026-11-19 UTC｜[论文](https://arxiv.org/abs/2611.26706)｜[全文](https://arxiv.org/html/2611.26706v1)

### 为什么重要与方法

基于世界模型的长时域规划可能因梯度局部最优或每轮重新采样而浪费既有搜索成果。该研究使用序贯蒙特卡洛（SMC）让动作序列群体在一系列中间目标分布中演化，通过重要性加权、重采样、群体更新与梯度优化推进搜索，并利用 PDE 推导的潜空间 cost-to-go 引导候选接近目标。

### 实验与风险

作者在视觉和本体感觉世界模型的导航、操作任务中报告相对部分梯度法平均成功率改善29、50个百分点，相对采样法35个百分点，相对 MPPI 7个百分点。不同对照条件不能合并成统一收益；迭代次数也不等于墙钟延迟。潜空间距离、世界模型预测偏差及重采样退化可能导致错误计划。尚未核实完整官方代码。

### 适合谁关注与工程落地

世界模型 MPC、动作采样及长时任务。最小实验用固定二维动力学或 PushT 模型，对照 MPPI、梯度优化与 SMC；以相同模型前向调用预算统计成功率、候选多样性、实际任务进度、P95 和峰值显存。不要以模型预测成功代替真实碰撞检查。

## 8. FORTH：触觉力控的开放组件与作者自我纠错

时间回补｜v1 2026-11-19 UTC｜[论文](https://arxiv.org/abs/2611.26744)｜[代码与审计](https://github.com/Jordanlllll/FORTH)

### 为什么重要与算法模块

研究将触觉空间表示、无反传更新和滑移反馈力控拆为三部分：局部前向触觉编码、低秩更新适配器、SlipGuard 力控；另有滑移统计、传感器误差模拟和形变指标。真正值得关注的是仓库明确说明三模块联动优势在复查中被否定，多次发现仿真装置或对照缺陷并撤回结果。

### 实验结果与证据冲突

摘要宣称29倍峰值抓力差距，但仓库表明该数字来自 MuJoCo impratio=1 的旧档案；纠正为10后为22.8741 N 对1.5895 N，约14.39倍。该对比仅为特定纸盒模型和控制器，不能推广到真机抓取或 LIBERO 全任务。README 还明确没有完整 VLA 栈、仿真器、数据集与训练权重，因此不能把论文所称开放模型理解为当前仓库全部可下载。作者自审不是独立复现。

### 可复现性与工程落地

MIT、Python>=3.9、NumPy>=1.24，公开核心算法及纸盒历史轨迹回放，不需 GPU：

~~~bash
git clone https://github.com/Jordanlllll/FORTH.git
cd FORTH
python -m pip install -e .
python examples/box_crush/run_compare.py
~~~

适合机械臂触觉、力闭环与研究复现。先运行轨迹审计，再检查传感器延迟、摩擦和基线的预载条件是否匹配。明确区分历史轨迹再分析与重新运行物理仿真。不要将离线控制器直接用于真实夹爪。

## AI / LLM 附属框架与开源工程组件

### Epistemic Guard：用执行回执约束 Agent 的完成声明

时间回补｜v1 2026-11-20 UTC｜[论文](https://arxiv.org/abs/2611.27095)｜[全文](https://arxiv.org/html/2611.27095v1)｜[MIT源码](https://github.com/AlienatedAliens/epistemic-guard)

痛点是 Agent 宣称已写文件、提交代码或删除记录，实际工具可能失败或根本未执行。组件在独立进程代理 MCP 调用，产生签名回执与 Merkle 审计链；轻量 INT8 分类器核验最终文字声明，另有 SQLite 记忆来源门控及转载来源去重。签名证明记录完整性，不证明业务结果正确，仍须独立读取文件或数据库状态。

作者在250条冻结样本报告93.2%准确率、CPU中位17.9ms、P95 35.83ms（Windows11/Core Ultra9 275HX工作站）；60条真实 MCP 代理测试准确率76.67%，危险声明召回96.15%，误报38.24%。实际场景误报明显，不能只引用冻结集成绩。来源去重也无法可靠识别大幅改写。

### 最低接入与 A/B

当前 README 提供 pip、可选约227MB OpenVINO INT8 权重、离线 demo 和 Codex hooks。先在隔离虚拟环境使用 demo，不装全局 hook，不调用 Codex，不访问生产路径：

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install epistemic-guard
epistemic-guard download-models
epistemic-guard demo
~~~

模型初次下载需联网，之后本地判断不需要付费 LLM API。论文固定 v0.5.2；实际安装时核对版本与模型哈希。当前 README 另有 install-hooks 入口，但安装会修改客户端配置，应单独审查并先用观察模式。对 Codex/T3 Code，建议构造20条已知成功、失败、部分成功和目标错误的工具轨迹，比较裸回执、规则检查、分类器+回执与实际文件读回；指标为虚假完成检出率、误报、P95、附加重试与数据泄露风险。独立状态读回仍然是最终依据。

## AI Coding 实战技巧精选

### 技巧 1｜用 CMake --fresh 区分缓存错误与源码错误

**来源：** CMake 官方[命令手册](https://cmake.org/cmake/help/latest/manual/cmake.1.html#cmdoption-cmake-fresh)，3.24引入，工程补充回顾。

**一句话结论：** 更换工具链、SDK或依赖后，不要让 Codex 根据陈旧 CMakeCache 猜测代码错误。

**具体怎么做：** 先保存旧缓存及配置参数，在独立诊断目录或可重建目录重新配置；保留相同生成器及真实工具链参数，然后构建、测试并比较错误。

~~~bash
cmake --fresh -S . -B build-diagnostic -G Ninja -DBUILD_TESTING=ON -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build-diagnostic
ctest --test-dir build-diagnostic --output-on-failure
~~~

**适合：** C++、CLion、ROS2、Distrobox、交叉编译。**注意：** fresh 会移除指定目录的 CMakeCache.txt 和 CMakeFiles，不能对不可恢复生产构建目录随意执行；旧于3.24的环境改用新目录。

### 技巧 2｜保护临时离线的 Codex 工作树元数据

**来源：** Git [worktree 官方手册](https://git-scm.com/docs/git-worktree)，工程补充回顾。

**一句话结论：** 将长期任务工作树放在可移动 SSD 或间歇挂载路径时，先防止 Git 自动清理其元数据。

**具体怎么做：** 在主仓库核对目标工作树；对确需保留且已存在的工作树加锁，检查 prune 的 dry-run 结果。挂载恢复后检查 Git 状态，任务结束再解锁。

~~~bash
git worktree list --porcelain
git worktree lock --reason "offline development workspace" /mnt/ssd/robot-worktree
git worktree prune --dry-run --verbose
# 工作完成且数据盘恢复后
git worktree unlock /mnt/ssd/robot-worktree
~~~

**适合：** T3 Code 多工作树、移动 SSD、间歇连接的开发目录。**注意：** lock 保护 Git 管理元数据，不是文件备份、权限沙盒或并行写互斥锁；不要用 force 绕过仍在执行的任务。

## 经典论文回顾

### Dynamic Window Approach（DWA，1997）：从延迟与停车距离角度经典复盘

Dieter Fox、Wolfram Burgard、Sebastian Thrun，IEEE Robotics & Automation Magazine 4(1)，1997年3月，23–33页。[DOI](https://doi.org/10.1109/100.580977)｜[作者摘要](https://www.cs.cmu.edu/~dfox/abstracts/colli-ieee.abstract.html)。历史索引已于2026-08-09覆盖，本次复盘角度是时延预算与实际制动，不再作为首次报道。

核心思想是在速度空间搜索，而不是直接在所有几何曲线上搜索：速度极限与短周期加速度形成可达窗口，进一步排除不能在障碍前停止的速度，剩余候选以朝向、速度、净空评分。作者在 RHINO 上报告最高0.95m/s的动态环境实验。

现代系统依旧借鉴可达控制集合与制动约束。原始模型面向特定移动底盘，并非任意非圆形轮足和动态障碍的通用安全证明；现代 DWB、MPPI、MPC 可使用更多动态约束和代价。现代参考工程：[Nav2](https://github.com/ros-navigation/navigation2)，并非原作者历史代码。

本期延迟补偿研究提醒：若估计与执行之间存在总延迟 tau，简化一维静态障碍情形的制动预算可写作 d = v*tau + v²/(2*a)，其中 a 为可保证的减速度。还必须额外考虑车体外形、观测误差与障碍自身运动。示例：0.8m/s、0.8m/s²、150ms延迟时预算为0.52m，忽略延迟则仅0.4m。它只是工程估算，不是原论文公式或完整安全认证。

最小实验在仿真中注入0/100/200ms状态延迟，记录实际停车余量、过度停止与控制 P99；再由独立安全层在受控场地验证底盘减速度。对于狭窄走廊和多雷达巡检，定位精度、状态年龄、制动能力应分别验收。

## 今日结论

最值得先做的是 Instant-LIVO 的内存/精度对照、let_ros 的重复性实验以及 Epistemic Guard 的离线回执测试。FORTH 特别提醒论文摘要和最新代码审计可能不一致，必须按真实公开资产和修订后条件评价可复现性。多机延迟补偿应验证低层安全过滤使用的状态是否足够新，而不是盲目增加规划复杂度。所有论文性能均为作者报告，未执行本地构建、训练或 Codex 模型调用。

## 最值得深入研究或尝试复现的方向

| 优先级 | 项目 | 最小验收 |
|---|---|---|
| P0 | Instant-LIVO | 相同数据 RPE、RSS、P95、地图增长 |
| P0 | let_ros | 单/多线程消息结果一致性、模拟吞吐 |
| P0 | Epistemic Guard | 真实回执与状态读回、误报、漏报 |
| P1 | LiDAR 仿真校验 | 点密度曲线、扫描特征、LIO差异 |
| P1 | 群体延迟补偿 | 状态年龄、净空、约束可行与通过量 |
| P1 | MPAO | 候选差异、切换时间、碰撞约束 |
| P1 | FORTH | 历史轨迹回放与修正参数审计 |
| P1 | SMC规划 | 固定模型调用预算下成功率及耗时 |
| P2 | BRINA | 海床坡度、尺度误差、回环 |
| P2 | CMake fresh / worktree lock | 配置差异与离线工作树状态 |
| P2 | DWA经典复盘 | 延迟、实际停车余量与 P99 |

## 参考资料

- [arXiv Robotics](https://arxiv.org/list/cs.RO/new)；[Software Engineering](https://arxiv.org/list/cs.SE/new)。
- [Instant-LIVO](https://arxiv.org/abs/2611.27633)；[BRINA](https://arxiv.org/abs/2611.27817)；[LiDAR密度](https://arxiv.org/abs/2611.27379)。
- [延迟补偿](https://arxiv.org/abs/2611.27540)；[MPAO](https://arxiv.org/abs/2611.27012)；[let_ros](https://arxiv.org/abs/2611.26676)；[SMC](https://arxiv.org/abs/2611.26706)；[FORTH](https://arxiv.org/abs/2611.26744)。
- [Epistemic Guard](https://arxiv.org/abs/2611.27095)；[CMake](https://cmake.org/cmake/help/latest/manual/cmake.1.html#cmdoption-cmake-fresh)；[Git worktree](https://git-scm.com/docs/git-worktree)；[DWA](https://doi.org/10.1109/100.580977)。
