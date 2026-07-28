---
layout: page
title: 日报归档
permalink: /archive/
---

共收录 **{{ site.posts | size }}** 期技术深度简报。

{% assign posts_by_month = site.posts | group_by_exp: "post", "post.date | date: '%Y 年 %m 月'" %}
{% for month in posts_by_month %}
## {{ month.name }}

{% for post in month.items %}
- `{{ post.date | date: "%m-%d" }}` [{{ post.title }}]({{ post.url | relative_url }})
{% endfor %}
{% endfor %}
