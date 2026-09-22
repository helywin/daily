from pathlib import Path

p = Path('robotics-brief-covered-items.md')
s = p.read_text(encoding='utf-8')
s = s.replace(
    '> 2026-09-22 新增 8 条主动态、2 条 AI Coding 实战技巧精选，并经典复盘 MSCKF 1 条，共 749 条。',
    '> 2026-09-22 新增 8 条主动态、2 条 AI Coding 实战技巧精选，并经典复盘 MSCKF 1 条，共 748 条。',
    1,
)
dup = '| 2026-09-22 | A Multi-State Constraint Kalman Filter for Vision-aided Inertial Navigation / MSCKF | [DOI](https://doi.org/10.1109/ROBOT.2007.364024) | 经典论文回顾；ICRA 2007；从固定计算预算、structureless feature constraints 与观测可信度角度复盘滤波式 VIO。 |\n\n'
if dup in s:
    s = s.replace(dup, '', 1)
elif '| 2026-09-22 | A Multi-State Constraint Kalman Filter for Vision-aided Inertial Navigation / MSCKF |' in s:
    s = s.replace('| 2026-09-22 | A Multi-State Constraint Kalman Filter for Vision-aided Inertial Navigation / MSCKF | [DOI](https://doi.org/10.1109/ROBOT.2007.364024) | 经典论文回顾；ICRA 2007；从固定计算预算、structureless feature constraints 与观测可信度角度复盘滤波式 VIO。 |\n', '', 1)
# The canonical existing classic-revisit row must remain.
needle = '| 2026-09-22 | MSCKF | [DOI](https://doi.org/10.1109/ROBOT.2007.364024) · [OpenVINS](https://docs.openvins.com/) | 经典复盘；原始覆盖 2026-08-05；本期从固定计算预算、观测可信度与退化初始化接口重新解读。 |'
if needle not in s:
    raise SystemExit('canonical MSCKF revisit row missing')
p.write_text(s, encoding='utf-8')
