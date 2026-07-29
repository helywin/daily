(() => {
  const form = document.querySelector('.search-page-form');
  const input = document.getElementById('search-input');
  const summary = document.getElementById('search-summary');
  const results = document.getElementById('search-results');
  if (!form || !input || !summary || !results) return;

  let indexPromise;

  const normalize = (value) => String(value || '')
    .normalize('NFKC')
    .toLocaleLowerCase()
    .replace(/\s+/g, ' ')
    .trim();

  const decodeEntities = (value) => {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = value;
    return textarea.value;
  };

  const escapeHtml = (value) => String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');

  const highlight = (text, terms) => {
    if (!terms.length) return escapeHtml(text);
    const escapedTerms = terms
      .map((term) => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
      .sort((a, b) => b.length - a.length);
    const pattern = new RegExp(`(${escapedTerms.join('|')})`, 'giu');
    let cursor = 0;
    let output = '';
    for (const match of text.matchAll(pattern)) {
      output += escapeHtml(text.slice(cursor, match.index));
      output += `<mark>${escapeHtml(match[0])}</mark>`;
      cursor = match.index + match[0].length;
    }
    return output + escapeHtml(text.slice(cursor));
  };

  const countMatches = (text, term) => {
    let count = 0;
    let offset = 0;
    while ((offset = text.indexOf(term, offset)) !== -1 && count < 8) {
      count += 1;
      offset += Math.max(term.length, 1);
    }
    return count;
  };

  const makeExcerpt = (post, terms) => {
    const description = decodeEntities(post.description);
    const content = decodeEntities(post.content);
    const searchableContent = content.normalize('NFKC').toLocaleLowerCase();
    const positions = terms
      .map((term) => searchableContent.indexOf(term))
      .filter((position) => position >= 0);

    if (!positions.length) {
      const fallback = description || content;
      return fallback.length > 210 ? `${fallback.slice(0, 210)}…` : fallback;
    }

    const position = Math.min(...positions);
    const start = Math.max(0, position - 70);
    const end = Math.min(content.length, position + 180);
    return `${start > 0 ? '…' : ''}${content.slice(start, end).trim()}${end < content.length ? '…' : ''}`;
  };

  const preparePost = (post) => {
    const title = decodeEntities(post.title);
    const description = decodeEntities(post.description);
    const tags = decodeEntities(post.tags);
    const content = decodeEntities(post.content);
    return {
      ...post,
      title,
      description,
      tags,
      content,
      fields: {
        title: normalize(title),
        description: normalize(description),
        tags: normalize(tags),
        content: normalize(content)
      }
    };
  };

  const loadIndex = () => {
    if (!indexPromise) {
      const indexUrl = new URL('../search.json', window.location.href);
      indexPromise = fetch(indexUrl)
        .then((response) => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.json();
        })
        .then((posts) => posts.map(preparePost));
    }
    return indexPromise;
  };

  const search = (posts, terms) => posts
    .map((post) => {
      const allText = Object.values(post.fields).join(' ');
      if (!terms.every((term) => allText.includes(term))) return null;

      const score = terms.reduce((total, term) => (
        total
        + countMatches(post.fields.title, term) * 20
        + countMatches(post.fields.tags, term) * 10
        + countMatches(post.fields.description, term) * 6
        + countMatches(post.fields.content, term)
      ), 0);

      return { post, score };
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score || b.post.date.localeCompare(a.post.date));

  const render = (matches, terms, query) => {
    summary.textContent = matches.length
      ? `找到 ${matches.length} 篇包含“${query}”的文章`
      : `没有找到包含“${query}”的文章`;

    results.replaceChildren();
    matches.forEach(({ post }) => {
      const article = document.createElement('article');
      article.className = 'search-result';
      const excerpt = makeExcerpt(post, terms);
      const tags = post.tags
        ? `<span class="search-result-tags">${highlight(post.tags, terms)}</span>`
        : '';
      article.innerHTML = `
        <div class="search-result-meta">
          <time datetime="${escapeHtml(post.date)}">${escapeHtml(post.date)}</time>
          ${tags}
        </div>
        <h2><a href="${escapeHtml(post.url)}">${highlight(post.title, terms)}</a></h2>
        <p>${highlight(excerpt, terms)}</p>
        <a class="read-more" href="${escapeHtml(post.url)}">阅读全文 →</a>
      `;
      results.appendChild(article);
    });
  };

  const runSearch = async () => {
    const query = input.value.trim();
    const terms = [...new Set(normalize(query).split(' ').filter(Boolean))];
    const url = new URL(window.location.href);

    if (!terms.length) {
      url.searchParams.delete('q');
      history.replaceState(null, '', url);
      summary.textContent = '输入关键词，查找已归档的技术日报。';
      results.replaceChildren();
      return;
    }

    url.searchParams.set('q', query);
    history.replaceState(null, '', url);
    summary.textContent = '正在搜索…';

    try {
      const posts = await loadIndex();
      render(search(posts, terms), terms, query);
    } catch (error) {
      summary.textContent = '搜索索引加载失败，请稍后重试。';
      console.error('Failed to load search index:', error);
    }
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    runSearch();
  });

  const initialQuery = new URLSearchParams(window.location.search).get('q') || '';
  if (initialQuery) {
    input.value = initialQuery;
    runSearch();
  }
})();
