# 机器人技术日报 · GitHub Pages

基于 Jekyll 构建的中文技术日报归档网站，内容覆盖 SLAM、机器人控制、强化学习、VLA 与 AI Coding Agent。

## 在线地址

- 自定义域名：`https://daily.helywin.com/`
- GitHub Pages 默认地址：`https://helywin.github.io/daily/`

## 内容结构

- `_posts/`：每日技术简报
- `_layouts/`：Jekyll 页面模板
- `assets/css/`：网站样式
- `.github/workflows/pages.yml`：GitHub Pages 自动部署
- `CNAME`：自定义域名声明

历史日报由聊天导出的 Markdown 自动拆分并恢复标题、列表和章节层级。后续日报直接保存为 `_posts/YYYY-MM-DD-robotics-brief.md`。

## 本地预览

```bash
bundle install
bundle exec jekyll serve
```

浏览器打开 `http://127.0.0.1:4000/`。
