from pathlib import Path

p = Path('robotics-brief-covered-items.md')
s = p.read_text(encoding='utf-8')
old = '> 2026-09-22 新增 8 条主动态、2 条 AI Coding 实战技巧精选，并经典复盘 MSCKF 1 条，共 748 条。'
new = '> 2026-09-22 新增 8 条主动态、2 条 AI Coding 实战技巧精选，并经典复盘 MSCKF 1 条，共 749 条。'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('2026-09-22 summary line not found')
row = '| 2026-09-22 | A Multi-State Constraint Kalman Filter for Vision-aided Inertial Navigation / MSCKF | [DOI](https://doi.org/10.1109/ROBOT.2007.364024) | 经典论文回顾；ICRA 2007；从固定计算预算、structureless feature constraints 与观测可信度角度复盘滤波式 VIO。 |\n'
if row.strip() not in s:
    marker = '\n## 维护检查表\n'
    if marker not in s:
        raise SystemExit('maintenance checklist marker not found')
    s = s.replace(marker, '\n' + row + marker, 1)
p.write_text(s, encoding='utf-8')
