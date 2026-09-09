(()=>{
 const key='canal-mainline-progress-v1';const chapters=[...document.querySelectorAll('.chapter')];const inputs=[...document.querySelectorAll('[data-check]')];const valid=new Set(inputs.map(i=>i.dataset.check));let completed=new Set;
 try{const saved=JSON.parse(localStorage.getItem(key)||'[]');if(Array.isArray(saved))completed=new Set(saved.filter(id=>valid.has(id)))}catch{document.querySelector('#storage-note').hidden=false}
 function updateProgress(){
  for(const input of inputs)input.checked=completed.has(input.dataset.check);
  for(const node of document.querySelectorAll('[data-flow]'))node.classList.toggle('completed',completed.has(node.dataset.flow));
  const main=inputs.filter(i=>i.hasAttribute('data-main-step'));
  document.querySelector('#overall-progress').textContent=`主線進度 ${main.filter(i=>i.checked).length} / ${main.length} 步`;
  for(const chapter of chapters){const steps=[...chapter.querySelectorAll('[data-main-step]')];chapter.querySelector('[data-progress]').textContent=`本節已完成 ${steps.filter(i=>i.checked).length} / ${steps.length} 步`}
 }
 for(const input of inputs)input.addEventListener('change',()=>{input.checked?completed.add(input.dataset.check):completed.delete(input.dataset.check);try{localStorage.setItem(key,JSON.stringify([...completed]))}catch{document.querySelector('#storage-note').hidden=false}updateProgress()});
 function selectFromHash(scroll){
  const id=location.hash.slice(1);const requested=id.match(/^(ch\d{2})(?:-s\d{2})?$/)?.[1];const current=chapters.find(c=>c.id===requested)||chapters.find(c=>!c.hidden)||chapters[0];
  for(const chapter of chapters)chapter.hidden=chapter!==current;
  for(const a of document.querySelectorAll('[data-chapter]')){if(a.dataset.chapter===current.id)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')}
  document.title=`${current.querySelector('h2').textContent}・完整攻略與流程圖｜運河散策`;
  if(scroll&&(requested||id==='chapters')){const target=document.getElementById(id)||current;requestAnimationFrame(()=>{target.scrollIntoView({block:'start',behavior:'instant'});if(target.classList.contains('step'))target.focus({preventScroll:true})})}
 }
 window.addEventListener('hashchange',()=>selectFromHash(true));
 document.querySelector('#print-chapter').onclick=()=>{const chapter=chapters.find(c=>!c.hidden);chapter.querySelector('.route-map').open=true;window.print()};
 updateProgress();selectFromHash(!!location.hash);
})();
