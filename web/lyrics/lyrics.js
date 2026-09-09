(() => {
  'use strict';
  const tracks = window.LYRICS_DATA;
  const $ = selector => document.querySelector(selector);
  const pad = number => String(number).padStart(2, '0');
  const href = (track, line) => `#track-${pad(track.number)}${line === undefined ? '' : `/line-${line + 1}`}`;
  const time = seconds => `${pad(Math.floor(seconds / 60))}:${(seconds % 60).toFixed(1).padStart(4, '0')}`;
  const node = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };
  let current;
  function setting(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(`canal-lyrics-${key}`);
      localStorage.setItem(`canal-lyrics-${key}`, value);
    } catch (_) { /* Reading remains available when storage is unavailable. */ }
  }
  for (const track of tracks) {
    const link = node('a', 'track'); link.href = href(track);
    link.dataset.number = track.number;
    link.append(node('span', 'number', pad(track.number)));
    const label = node('span', 'name', track.title);
    label.append(node('small', '', track.lyrics.length ? `${track.lyrics.length} 段歌詞` : '未收錄內嵌歌詞'));
    link.append(label); $('#tracks').append(link);
  }
  function render(scroll = true) {
    const match = location.hash.match(/^#track-(\d+)(?:\/line-(\d+))?$/);
    current = tracks.find(track => track.number === Number(match?.[1])) || tracks.find(track => track.lyrics.length);
    const selected = match?.[2] ? Number(match[2]) - 1 : -1;
    $('#song-number').textContent = `TRACK ${pad(current.number)} / 運河`;
    $('#song-title').textContent = current.title;
    document.title = `${current.title}｜歌詞｜運河散策`;
    $('#song-summary').textContent = current.lyrics.length ? `遊戲內嵌歌詞・${current.lyrics.length} 段・可切換字級與時間標記` : '此曲未找到遊戲內嵌歌詞';
    $('#link-status').replaceChildren();
    const fragment = document.createDocumentFragment();
    current.lyrics.forEach((line, index) => {
      const row = node('div', `lyric-line${index === selected ? ' selected' : ''}`);
      row.id = `line-${index + 1}`;
      row.append(node('span', 'time', time(line.time)), node('span', 'lyric-text', line.text));
      fragment.append(row);
    });
    if (!current.lyrics.length) {
      const empty = node('div', 'empty');
      empty.append(node('p', '', '目前的遊戲資料沒有收錄這首歌的歌詞。'), node('p', '', '這不代表此曲是純音樂。正式內容請參考原專輯與官方歌詞本。'));
      fragment.append(empty);
    }
    $('#lyric-lines').replaceChildren(fragment);
    for (const link of document.querySelectorAll('.track')) link.setAttribute('aria-current', String(Number(link.dataset.number) === current.number));
    const index = tracks.indexOf(current);
    $('#previous-song').disabled = index === 0;
    $('#next-song').disabled = index === tracks.length - 1;
    if (scroll) requestAnimationFrame(() => {
      $('#reading').focus({preventScroll: true});
      ($('.lyric-line.selected') || $('#reading')).scrollIntoView({block: 'start'});
    });
  }
  $('#previous-song').onclick = () => { const track = tracks[tracks.indexOf(current) - 1]; if (track) location.hash = href(track); };
  $('#next-song').onclick = () => { const track = tracks[tracks.indexOf(current) + 1]; if (track) location.hash = href(track); };
  window.addEventListener('hashchange', () => render());
  $('#tracks').addEventListener('click', event => {
    if (event.target.closest('a')?.hash === location.hash) render();
  });
  const setFont = font => {
    const plain = font === 'plain';
    $('#lyric-lines').classList.toggle('plain-font', plain);
    document.querySelectorAll('[data-font]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.font === (plain ? 'plain' : 'game')));
    });
  };
  setFont(setting('font'));
  document.querySelectorAll('[data-font]').forEach(button => button.onclick = () => {
    setFont(button.dataset.font);
    setting('font', button.dataset.font);
  });
  const setSize = size => {
    document.documentElement.style.setProperty('--lyric-size', `${size}px`);
    document.querySelectorAll('[data-size]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.size) === size)));
  };
  const savedSize = Number(setting('size'));
  setSize([18, 22, 28].includes(savedSize) ? savedSize : 22);
  document.querySelectorAll('[data-size]').forEach(button => button.onclick = () => {
    const size = Number(button.dataset.size); setSize(size); setting('size', String(size));
  });
  $('#timestamps').checked = setting('timestamps') === 'true';
  const setTime = () => $('#lyric-lines').classList.toggle('show-time', $('#timestamps').checked);
  setTime();
  $('#timestamps').onchange = () => { setTime(); setting('timestamps', String($('#timestamps').checked)); };
  $('#copy-link').onclick = async () => {
    const url = new URL(location.href); url.hash = $('.lyric-line.selected') ? location.hash : href(current);
    try {
      await navigator.clipboard.writeText(url.href);
      $('#link-status').textContent = '已複製連結，可分享這首歌或目前選取的段落。';
    } catch (_) {
      const input = node('input'); input.readOnly = true; input.value = url.href;
      input.setAttribute('aria-label', '可手動複製的歌詞連結'); input.style.width = '100%';
      $('#link-status').replaceChildren(document.createTextNode('請手動複製：'), input);
      input.focus(); input.select();
    }
  };
  function highlight(text, terms) {
    const span = node('span'); const lower = text.toLocaleLowerCase(); let start = 0;
    while (start < text.length) {
      let position = -1, length = 0;
      for (const term of terms) {
        const found = lower.indexOf(term, start);
        if (found !== -1 && (position === -1 || found < position || (found === position && term.length > length))) { position = found; length = term.length; }
      }
      if (position === -1) { span.append(document.createTextNode(text.slice(start))); break; }
      span.append(document.createTextNode(text.slice(start, position)), node('mark', '', text.slice(position, position + length)));
      start = position + length;
    }
    return span;
  }
  function search() {
    const terms = [...new Set($('#lyric-search').value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean))];
    $('#search-results').replaceChildren();
    if (!terms.length) { $('#search-count').textContent = '搜尋曲名或歌詞；多個關鍵字可用空格分開。'; return; }
    const results = [];
    for (const track of tracks) {
      if (terms.every(term => track.title.toLocaleLowerCase().includes(term))) results.push({track, text: track.title});
      track.lyrics.forEach((line, index) => {
        if (terms.every(term => `${track.title} ${line.text}`.toLocaleLowerCase().includes(term))) results.push({track, text: line.text, index});
      });
    }
    $('#search-count').textContent = results.length ? `找到 ${results.length} 筆；點選即可跳到對應曲目或段落。` : '沒有符合的曲名或歌詞，試試較短的關鍵字。';
    const fragment = document.createDocumentFragment();
    for (const result of results) {
      const link = node('a', 'result'); link.href = href(result.track, result.index);
      link.append(node('small', '', `${pad(result.track.number)} ${result.track.title} · ${result.index === undefined ? '曲目' : `第 ${result.index + 1} 段`}`), highlight(result.text, terms));
      fragment.append(link);
    }
    $('#search-results').append(fragment);
  }
  $('#lyric-search').addEventListener('input', search);
  $('#clear-search').onclick = () => { $('#lyric-search').value = ''; search(); $('#lyric-search').focus(); };
  $('#search-results').addEventListener('click', event => { if (event.target.closest('a')?.hash === location.hash) render(); });
  render(Boolean(location.hash)); search();
})();
