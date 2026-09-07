(() => {
  'use strict';
  const data = window.GUIDE_DATA;
  if (!data) return;
  const $ = selector => document.querySelector(selector);
  const events = data.events;
  const byId = new Map(events.map(event => [event.id, event]));
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const plain = value => String(value ?? '').replace(/<[^>]+>/g, '');
  const rich = value => esc(value).replace(/&lt;key&gt;(.*?)&lt;\/key&gt;/g, '<kbd>$1</kbd>').replace(/&lt;[^&]*&gt;/g, '');
  const storeKey = 'canal-field-guide-v1';
  let progress = {read:[], favorite:[], notes:{}};
  try {
    const stored = JSON.parse(localStorage.getItem(storeKey));
    if (stored) progress = normalizeProgress(stored);
  } catch (_) {}
  let limit = 24, current = null, frameIndex = 0, openingFocus = null, chapterIndex = 0;
  const dialog = $('#event-dialog'), lightbox = $('#lightbox');
  const searchIndex = new Map(events.map(event => [event.id, [event.title,event.name,event.place,event.note?.title,event.note?.body,...event.steps,...event.conditions,...event.speakers,...event.texts.map(line => line.lines),...event.texts.flatMap(line => (line.options || []).map(option => option.option))].join(' ').toLowerCase()]));
  const normalize = value => plain(value).normalize('NFKC').toLowerCase();
  const dialogueIndex=events.flatMap(event=>event.frames.map((frame,index)=>({event,frame,index,
    text:[event.id,event.name,event.place,data.speakers[frame.text.speaker]||frame.text.speaker||'旁白',plain(frame.text.lines),...(frame.text.options||[]).map(o=>o.option),frame.option||''].map(normalize).join(' ')})));
  let dialogueLimit=12;
  function highlight(value,terms){
    const text=plain(value),fold=text.toLowerCase(),ranges=[];
    for(const term of terms){let start=0;while((start=fold.indexOf(term,start))!==-1){ranges.push([start,start+term.length]);start+=term.length;}}
    ranges.sort((a,b)=>a[0]-b[0]);const merged=[];
    for(const range of ranges){const last=merged.at(-1);if(last&&range[0]<=last[1])last[1]=Math.max(last[1],range[1]);else merged.push(range.slice());}
    let result='',pos=0;for(const [start,end] of merged){result+=esc(text.slice(pos,start))+'<mark>'+esc(text.slice(start,end))+'</mark>';pos=end;}return result+esc(text.slice(pos));
  }
  function renderDialogueResults(){
    const query=$('#dialogue-query').value.trim(),terms=normalize(query).split(/\s+/).filter(Boolean);
    $('#clear-dialogue-query').hidden=!query;
    if(!terms.length){$('#dialogue-results').innerHTML='';$('#dialogue-result-count').textContent='輸入關鍵字，尋找你記得的那句話。';$('#more-dialogue-results').hidden=true;return;}
    const results=dialogueIndex.filter(row=>terms.every(term=>row.text.includes(term)));
    $('#dialogue-result-count').textContent=results.length?`找到 ${results.length} 個對應畫面，顯示 ${Math.min(results.length,dialogueLimit)} 個。`:'找不到符合的對話。試試較短的關鍵字，或去掉部分標點。';
    $('#dialogue-results').innerHTML=results.slice(0,dialogueLimit).map(({event,frame,index})=>`<button class="dialogue-result" data-event="${event.id}" data-open-frame="${index}" aria-label="開啟 No.${String(event.number).padStart(3,'0')} 第 ${index+1} 張：${esc(plain(frame.text.lines))}"><img src="${frame.image}" width="200" height="150" loading="lazy" decoding="async" alt="${esc(event.title)}，第 ${index+1} 張"><span class="dialogue-result-copy"><span class="dialogue-result-meta">No.${String(event.number).padStart(3,'0')} · ${esc(event.place)} · 第 ${index+1} 張${frame.variant==='option'?' · 選項回覆':''}${event.imageReference?' · 教授版同文對照':''}</span><span class="dialogue-result-title">${highlight(event.title,terms)}</span><span class="dialogue-result-line">${highlight(data.speakers[frame.text.speaker]||frame.text.speaker||'旁白',terms)}：${highlight(frame.text.lines,terms)}</span>${frame.option?`<span class="dialogue-result-meta">選擇「${highlight(frame.option,terms)}」</span>`:''}${frame.text.options?.length?`<span class="dialogue-result-meta">${frame.text.options.map(o=>highlight(o.option,terms)).join(' ／ ')}</span>`:''}<span class="dialogue-result-action">查看這句的畫面 ↗</span></span></button>`).join('');
    $('#more-dialogue-results').hidden=results.length<=dialogueLimit;
  }
  $('#dialogue-query').addEventListener('input',()=>{dialogueLimit=12;renderDialogueResults();});
  $('#clear-dialogue-query').addEventListener('click',()=>{$('#dialogue-query').value='';dialogueLimit=12;renderDialogueResults();$('#dialogue-query').focus();});
  $('#more-dialogue-results').addEventListener('click',()=>{dialogueLimit+=12;renderDialogueResults();});
  const links = ids => ids.filter(id => byId.has(id)).map(id => `<button class="event-link" data-event="${id}">${esc(byId.get(id).title)} ↗</button>`).join('');
  let toastTimer;
  function toast(message) { $('#toast').textContent = message; $('#toast').classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(() => $('#toast').classList.remove('show'), 2700); }
  function normalizeProgress(value) {
    const ids = input => Array.isArray(input) ? [...new Set(input.filter(id => byId.has(id)))] : [];
    const notes = {};
    if (value.notes && typeof value.notes === 'object') for (const [id, text] of Object.entries(value.notes)) if (byId.has(id) && typeof text === 'string') notes[id] = text.slice(0, 6000);
    return {read:ids(value.read), favorite:ids(value.favorite), notes};
  }
  function saveProgress() { try { localStorage.setItem(storeKey, JSON.stringify(progress)); } catch (_) { toast('此瀏覽器無法保存進度，請使用匯出筆記備份。'); } updateProgress(); }
  function updateProgress() { $('#progress-label').textContent = `${progress.read.length} / ${events.length}`; $('#read-progress').value = progress.read.length; }
  function toggleProgress(kind, id) {
    progress[kind] = progress[kind].includes(id) ? progress[kind].filter(item => item !== id) : [...progress[kind], id];
    saveProgress(); renderCards();
    if (current?.id === id) updateDetailActions();
    toast(kind === 'read' ? (progress.read.includes(id) ? '已標記讀完這組事件' : '已取消已讀標記') : (progress.favorite.includes(id) ? '已加入收藏' : '已移出收藏'));
  }
  function resetFilters() { for (const id of ['search','scene-filter','chapter-filter','kind-filter','progress-filter']) $('#'+id).value=''; limit=24; renderCards(); }
  function filteredEvents() {
    const query = $('#search').value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const scene = $('#scene-filter').value, chapter = $('#chapter-filter').value, kind = $('#kind-filter').value, status = $('#progress-filter').value;
    return events.filter(event => (!scene || event.scene === scene)
      && (!chapter || (chapter === 'unknown' ? !event.chapterNumbers.length : event.chapterNumbers.includes(Number(chapter))))
      && (!kind || event.kind === kind)
      && (!status || (status === 'favorite' ? progress.favorite.includes(event.id) : status === 'read' ? progress.read.includes(event.id) : !progress.read.includes(event.id)))
      && query.every(word => searchIndex.get(event.id).includes(word)));
  }
  function renderCards() {
    const found = filteredEvents();
    $('#result-count').textContent = `${found.length} / ${events.length} 組事件`;
    $('#active-filters').textContent = $('#chapter-filter').value ? '章節篩選依已解析的互動規則；未列獨立條件的後續對話請用名稱或場景搜尋。' : '依原始索引順序排列 · 點開事件，閱讀完整圖文。';
    $('#event-grid').innerHTML = found.slice(0,limit).map(event => {
      const read = progress.read.includes(event.id), favorite = progress.favorite.includes(event.id);
      return `<article class="event-card"><button class="card-open" data-event="${event.id}" aria-label="閱讀：${esc(event.title)}"><div class="card-visual"><img src="${event.frames[0].image}" alt="${esc(event.title)}的原版事件重現畫面" loading="lazy" decoding="async" width="1200" height="900"><span class="card-no">NO. ${String(event.number).padStart(3,'0')}</span><span class="card-images">${event.hasImage?event.frames.length+' 張畫面':'截圖待補'}</span></div><div class="card-body"><div class="card-place">${esc(event.place)}</div><h3>${esc(event.title)}</h3><div class="card-meta"><span>${esc(event.kind)}</span>${read ? '<span class="read-tag">✓ 已讀</span>' : `<span>${event.texts.length} 段對話</span>`}</div></div></button><button class="favorite-btn" data-favorite="${event.id}" aria-pressed="${favorite}" aria-label="${favorite?'取消收藏':'收藏'}：${esc(event.title)}">${favorite?'★':'☆'}</button></article>`;
    }).join('');
    $('#empty-state').hidden = found.length !== 0;
    $('#load-more').hidden = found.length <= limit;
    $('#load-more').textContent = `再展開 ${Math.min(24, Math.max(0,found.length-limit))} 組事件 ↓`;
  }
  function renderChapter(index) {
    chapterIndex = index;
    const chapter = data.chapters[index];
    $('#chapter-list').innerHTML = data.chapters.map((item,i) => `<button class="chapter-tab" role="tab" id="chapter-tab-${i}" aria-controls="chapter-detail" aria-selected="${i===index}" tabindex="${i===index?0:-1}" data-chapter="${i}"><b>${String(item.number).padStart(2,'0')}</b><span>${esc(item.title)}</span></button>`).join('');
    $('#chapter-detail').setAttribute('aria-labelledby','chapter-tab-'+index);
    $('#chapter-detail').innerHTML = `<div class="chapter-eyebrow">CHAPTER ${String(chapter.number).padStart(2,'0')}</div><h3>${esc(chapter.title)}</h3><p class="chapter-lead">${esc(chapter.lead)}</p><ol class="route-steps">${chapter.mission.map(step=>`<li>${esc(step.name)}</li>`).join('')}</ol><div class="route-links">${links(chapter.events)}</div><p class="route-note">${esc(chapter.note)}</p>`;
  }
  function updateDetailActions() {
    if (!current) return;
    const read = $('#detail-read'), favorite = $('#detail-favorite');
    if (read) {read.setAttribute('aria-pressed', progress.read.includes(current.id)); read.textContent=progress.read.includes(current.id)?'✓ 已讀完':'標記為已讀';}
    if (favorite) {favorite.setAttribute('aria-pressed', progress.favorite.includes(current.id)); favorite.textContent=progress.favorite.includes(current.id)?'★ 已收藏':'☆ 收藏事件';}
  }
  function openEvent(id, options={}) {
    const event = byId.get(id); if (!event) return;
    if (!dialog.open) openingFocus = document.activeElement;
    current=event; frameIndex=Number.isInteger(options.frame)?Math.max(0,Math.min(event.frames.length-1,options.frame)):0;
    const availability = event.conditions.length ? event.conditions : ['這段未列獨立的互動條件；它可能由前後劇情直接呼叫。'];
    const point=event.points[0];
    const transcript = event.texts.map((line,i) => `<button class="dialogue-line" data-line="${i}" aria-label="查看第 ${i+1} 段截圖"><span class="line-number">${String(i+1).padStart(2,'0')}</span><span class="line-speaker">${esc(data.speakers[line.speaker] || line.speaker || '旁白')}</span><span class="line-text">${rich(line.lines)}${line.options?.length?`<span class="line-options">${line.options.map((option,n)=>`<span>選項 ${n+1}：${esc(option.option)}${option.loop?` → ${esc(option.loop)}`:''}</span>`).join('')}</span>`:''}</span></button>`).join('');
    $('#event-content').innerHTML = `<header class="detail-top"><span class="eyebrow">FIELD NOTE ${String(event.number).padStart(3,'0')}</span><span class="detail-place">${esc(event.place)}</span><button class="icon-button" id="close-event" aria-label="關閉事件">×</button></header><div class="detail-head"><h2 id="detail-title">${esc(event.title)}</h2><div class="detail-badges"><span class="badge">${esc(event.kind)}</span><span class="badge">${event.texts.length} 段原文</span><span class="badge">${event.hasImage?event.frames.length+' 張畫面':'截圖待補'}</span>${event.imageReference?'<span class="badge image-reference-badge">教授版同文對照</span>':''}<span class="badge">原版 SL</span></div></div><div class="detail-grid"><div class="gallery-panel"><button class="screenshot-button" id="zoom-image" aria-label="放大目前截圖"><img id="detail-image" width="1200" height="900" alt=""><span class="zoom-label">點擊放大 ↗</span></button><div class="gallery-controls"><button id="prev-frame" aria-label="上一張截圖">←</button><span class="frame-caption" id="frame-caption" aria-live="polite"></span><button id="next-frame" aria-label="下一張截圖">→</button></div><div class="thumbs" id="thumbs" aria-label="選擇截圖">${event.frames.map((frame,i)=>`<button class="thumb" data-frame="${i}" aria-label="第 ${i+1} 張${frame.variant==='option'?'，選項回覆':''}"><img src="${frame.image}" alt="" loading="lazy" decoding="async"><span>${i+1}</span></button>`).join('')}</div>${event.imageIssue?`<p class="hint">${esc(event.imageIssue)} 舊圖已撤下，以下保留原文。</p>`:''}<p class="capture-note">原版引擎事件重現 · ${event.imageReference?'本組台詞與 No.274 完全相同；此處對照教授版原版畫面，原文保留學生版說話者名稱。':!event.hasImage?'本組尚未取得可驗證畫面，目前僅提供原始對話。':event.scene==='chapter_intro'?'依原版字幕閱讀時段，選取 30 個不同動畫瞬間。':event.capture?.originalTrigger?'已執行原版事件到這段交談，再逐段擷取。':'依原版地圖與人物配置建立現場，保留原始對話。'}${event.points.length?'互動位置參考原版地圖；鏡頭位置經整理。':'本段以相關場景配圖，畫面位置不代表獨立觸發點。'}</p></div><aside class="detail-info"><section><h3>這段怎麼看</h3><ol>${event.steps.map(step=>`<li>${esc(step)}</li>`).join('')}</ol>${point?`<p class="coordinates">互動點參考：${esc(point.map)} · X ${Math.round(point.x)} / Y ${Math.round(point.y)}</p>`:''}</section><section><h3>章節與前置條件</h3><ul class="condition-list">${availability.map(condition=>`<li>${esc(condition)}</li>`).join('')}</ul>${event.rules.length?'<p class="capture-note">以上是互動表的候選條件，較前事件及 NPC 狀態仍可能影響是否出現。</p>':''}</section>${event.note?`<div class="hint"><strong>${esc(event.note.title)}</strong>${esc(event.note.body)}</div>`:''}<div class="detail-actions"><button id="detail-read" aria-pressed="false">標記為已讀</button><button id="detail-favorite" aria-pressed="false">收藏事件</button><button id="print-event">列印本篇</button><button id="copy-event">複製事件代號</button></div><label class="personal-note">我的攻略筆記<textarea id="personal-note" placeholder="記下你實玩時的發現、路線或待確認事項…" maxlength="6000">${esc(progress.notes[event.id] || '')}</textarea><span>自動保存在這個瀏覽器，可隨閱讀進度匯出。</span></label></aside></div><section class="transcript"><div class="transcript-heading"><h3>完整對話</h3><span>點擊任一段，對照畫面</span></div>${transcript}</section>${event.related.length?`<section class="related"><h3>接著查閱</h3><div class="event-links">${links(event.related)}</div></section>`:''}<details class="technical"><summary>事件代號與規則依據</summary><p>原索引代號：<code>${esc(event.name)}</code></p>${event.rules.map(rule=>`<p><code>${esc(rule.trigger)}</code> · ${rule.chapter?'第 '+rule.chapter+' 章':'通用候選'} · 第 ${rule.priority} 順位${rule.condition?' · 前置旗標 '+esc(rule.condition):''}${rule.after_event?' · 後續 '+esc(rule.after_event):''}</p>`).join('')}<p>收錄方式：遊戲內預覽功能重現；未宣稱每條分支均實玩驗證。</p></details>`;
    updateDetailActions(); renderFrame();
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop=0;
    $('#close-event').focus({preventScroll:true});
    if (!options.noHash) writeFrameHash();
  }
  function writeFrameHash(){if(current)history.replaceState(null,'','#'+current.id+(frameIndex?'/frame/'+(frameIndex+1):''));}
  function renderFrame() {
    if (!current) return;
    const frame=current.frames[frameIndex];
    writeFrameHash();
    const image=$('#detail-image'); image.src=frame.image; image.alt=`${current.title}，${frame.variant==='option'?'選項回覆':'第 '+(frame.lineIndex+1)+' 段'}：${plain(frame.text.lines)}`;
    $('#zoom-image').disabled=!current.hasImage;
    $('#frame-caption').textContent=`${current.imageReference?'教授版同文對照 · ':current.hasImage?'':'截圖待補 · '}${frameIndex+1} / ${current.frames.length} · ${frame.variant==='option'?'選擇「'+frame.option+'」後的回覆':'第 '+(frame.lineIndex+1)+' 段對話'}`;
    $('#prev-frame').disabled=frameIndex===0;$('#next-frame').disabled=frameIndex===current.frames.length-1;
    for(const thumb of dialog.querySelectorAll('[data-frame]'))thumb.setAttribute('aria-current',Number(thumb.dataset.frame)===frameIndex);
    for(const line of dialog.querySelectorAll('[data-line]'))line.classList.toggle('is-current',Number(line.dataset.line)===frame.lineIndex);
    const selected=dialog.querySelector(`.thumb[data-frame="${frameIndex}"]`);if(selected)selected.scrollIntoView({block:'nearest',inline:'nearest'});
  }
  function moveFrame(delta) { if (!current) return;frameIndex=Math.max(0,Math.min(current.frames.length-1,frameIndex+delta));renderFrame();if(lightbox.open)showLightbox(); }
  function closeEvent() { if (lightbox.open) lightbox.close(); dialog.close(); current=null; history.replaceState(null,'','#library'); if(openingFocus?.isConnected)openingFocus.focus({preventScroll:true}); }
  function showLightbox() { if(!current||!current.hasImage)return;const frame=current.frames[frameIndex];$('#lightbox-image').src=frame.image;$('#lightbox-image').alt=$('#detail-image').alt;$('#lightbox-caption').textContent=`${current.title} · ${frameIndex+1} / ${current.frames.length} · ${plain(frame.text.lines)}`;if(!lightbox.open)lightbox.showModal(); }
  async function printEvent() {
    const event=current;if(!event)return;
    $('#print-area').innerHTML=`<small>運河散策｜《運河 幻の南都》非官方圖文攻略</small><h1>${esc(event.title)}</h1><p>${esc(event.place)} · ${esc(event.name)}</p><h2>流程與條件</h2><p>${event.steps.map(esc).join('<br>')}</p><p>${event.conditions.map(esc).join('<br>')}</p>${event.note?`<p><strong>${esc(event.note.title)}</strong><br>${esc(event.note.body)}</p>`:''}${event.frames.map((frame,i)=>`<div class="print-frame"><p>${i+1} · ${esc(data.speakers[frame.text.speaker] || frame.text.speaker || '旁白')}：${rich(frame.text.lines)}</p><img src="${frame.image}" alt="${esc(event.title)}第 ${i+1} 張畫面"><small>${event.imageReference?'教授版同文對照（No.274）':'原版引擎事件重現截圖'}${frame.variant==='option'?' · 選項回覆':''}</small></div>`).join('')}`;
    toast('正在準備列印圖片…');
    await Promise.all([...$('#print-area').querySelectorAll('img')].map(img=>img.decode().catch(()=>{})));
    window.print();
  }
  async function copyEvent() {
    const text=current.name;
    try { await navigator.clipboard.writeText(text);toast('已複製：'+text); }
    catch (_) {const field=document.createElement('textarea');field.value=text;document.body.append(field);field.select();const copied=document.execCommand('copy');field.remove();toast(copied?'已複製：'+text:'事件代號：'+text);}
  }
  document.addEventListener('click', event => {
    const target=event.target.closest('button,a');if(!target)return;
    if(target.dataset.query){$('#dialogue-query').value=target.dataset.query;dialogueLimit=12;renderDialogueResults();return;}
    if(target.dataset.event){openEvent(target.dataset.event,{frame:target.dataset.openFrame!==undefined?Number(target.dataset.openFrame):0});return;}
    if(target.dataset.favorite){toggleProgress('favorite',target.dataset.favorite);return;}
    if(target.dataset.chapter!==undefined){renderChapter(Number(target.dataset.chapter));return;}
    if(target.dataset.frame!==undefined){frameIndex=Number(target.dataset.frame);renderFrame();return;}
    if(target.dataset.line!==undefined){frameIndex=current.frames.findIndex(frame=>frame.lineIndex===Number(target.dataset.line)&&frame.variant==='main');renderFrame();$('#detail-image').scrollIntoView({block:'nearest',behavior:'smooth'});return;}
    const actions={'close-event':closeEvent,'prev-frame':()=>moveFrame(-1),'next-frame':()=>moveFrame(1),'zoom-image':showLightbox,'lightbox-close':()=>lightbox.close(),'detail-read':()=>toggleProgress('read',current.id),'detail-favorite':()=>toggleProgress('favorite',current.id),'print-event':printEvent,'copy-event':copyEvent,'reset-filters':resetFilters,'empty-reset':resetFilters,'load-more':()=>{limit+=24;renderCards();}};
    actions[target.id]?.();
  });
  $('#search').addEventListener('input',()=>{limit=24;renderCards();});
  for(const id of ['scene-filter','chapter-filter','kind-filter','progress-filter'])$('#'+id).addEventListener('change',()=>{limit=24;renderCards();});
  dialog.addEventListener('input',event=>{if(event.target.id==='personal-note'&&current){progress.notes[current.id]=event.target.value;saveProgress();}});
  dialog.addEventListener('cancel',event=>{event.preventDefault();closeEvent();});
  dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closeEvent();}});
  lightbox.addEventListener('click',event=>{if(event.target===lightbox)lightbox.close();});
  document.addEventListener('keydown',event=>{
    const typing=/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);
    if(event.key==='/'&&!typing&&!dialog.open){event.preventDefault();$('#dialogue-query').focus();$('#dialogue-search').scrollIntoView();}
    if(dialog.open&&!typing&&(event.key==='ArrowLeft'||event.key==='ArrowRight')){event.preventDefault();moveFrame(event.key==='ArrowLeft'?-1:1);}
    if(document.activeElement.classList.contains('chapter-tab')&&['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(event.key)){
      event.preventDefault();let next=chapterIndex;
      if(event.key==='Home')next=0;else if(event.key==='End')next=data.chapters.length-1;else next=Math.max(0,Math.min(data.chapters.length-1,next+(['ArrowLeft','ArrowUp'].includes(event.key)?-1:1)));
      renderChapter(next);$('#chapter-tab-'+next).focus();
    }
  });
  $('#export-progress').addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify({format:'canal-field-guide',version:1,exportedAt:new Date().toISOString(),...progress},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='運河散策-閱讀筆記.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('閱讀進度與筆記已匯出');
  });
  $('#import-progress').addEventListener('click',()=>$('#progress-file').click());
  $('#progress-file').addEventListener('change',async event=>{
    const file=event.target.files[0];if(!file)return;
    try{if(file.size>2*1024*1024)throw Error();const imported=JSON.parse(await file.text());if(imported.format!=='canal-field-guide')throw Error();const valid=normalizeProgress(imported);progress={read:[...new Set([...progress.read,...valid.read])],favorite:[...new Set([...progress.favorite,...valid.favorite])],notes:{...progress.notes,...valid.notes}};saveProgress();renderCards();toast('已合併匯入的閱讀筆記');}
    catch(_){toast('無法匯入，請選擇本攻略匯出的 JSON 筆記。');}finally{event.target.value='';}
  });
  for(const [key,label] of Object.entries(data.scenes))$('#scene-filter').insertAdjacentHTML('beforeend',`<option value="${key}">${esc(label)}</option>`);
  for(let i=1;i<=12;i++)$('#chapter-filter').insertAdjacentHTML('beforeend',`<option value="${i}">第 ${i} 章</option>`);
  for(const kind of new Set(events.map(event=>event.kind)))$('#kind-filter').insertAdjacentHTML('beforeend',`<option>${esc(kind)}</option>`);
  for(const [key,value] of Object.entries(data.stats)){const node=$('#stat-'+({mapped:'points'}[key]||key));if(node)node.textContent=value;}
  const hero=events.find(event=>event.name==='old_man_bridge') || events.find(event=>event.name==='first_time');
  $('#hero-image').style.backgroundImage=`url("${hero.frames[0].image}")`;
  $('#branch-grid').innerHTML=data.branches.map((branch,i)=>`<article class="branch-card"><span class="branch-no">SIDE NOTE / 0${i+1}</span><h3>${esc(branch.title)}</h3><p>${esc(branch.description)}</p><div class="event-links">${links(branch.events)}</div></article>`).join('');
  updateProgress();renderChapter(0);renderCards();
  function readHash(){const match=/^#(e[0-9]+)(?:\/frame\/([0-9]+))?$/.exec(location.hash);if(match&&byId.has(match[1]))openEvent(match[1],{noHash:true,frame:match[2]?Number(match[2])-1:0});}
  window.addEventListener('hashchange',readHash);readHash();
})();
