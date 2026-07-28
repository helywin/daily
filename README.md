# 机器人技术日报 · GitHub Pages

基于 Jekyll 构建的中文技术日报归档网站，内容覆盖 SLAM、机器人控制、强化学习、VLA 与 AI Coding Agent。

## 在线地址

启用 GitHub Pages 后访问：

`https://helywin.github.io/daily/`

## 内容结构

```text
_posts/                 # 每日技术简报
_config.yml             # Jekyll 配置
index.md                # 网站首页
archive.md              # 按时间归档
about.md                # 网站说明
assets/main.scss        # 自定义样式
.github/workflows/      # GitHub Pages 自动部署
```

## 本地预览

```bash
bundle install
bundle exec jekyll serve
```

浏览器打开 `http://127.0.0.1:4000/daily/`。

历史日报由聊天导出的 Markdown 自动拆分，并根据日期、章节编号和固定栏目恢复标题、列表和层级。后续日报可直接保存为 `_posts/YYYY-MM-DD-robotics-brief.md`。
