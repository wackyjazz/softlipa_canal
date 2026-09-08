(()=>{
  // Offline copies and unrelated hosts must not write production statistics.
  if(location.origin!=='https://wackyjazz.github.io'||!location.pathname.startsWith('/softlipa_canal/'))return;
  const endpoint='https://canal-guide-images.wackyjazz1.workers.dev/api/visitors';
  const key='canal-guide-daily-visitor-v1',display=document.querySelector('[data-today-visitors]');
  const day=()=>new Date(Date.now()+8*3600000).toISOString().slice(0,10);
  async function update(){
    try {
      let saved;try{saved=JSON.parse(localStorage.getItem(key))}catch{}
      const today=day();
      if(saved?.day===today&&saved.counted&&Number.isSafeInteger(saved.total)&&Date.now()-saved.updated<300000){if(display)display.textContent=saved.total.toLocaleString('zh-TW');return;}
      if(saved?.day!==today)saved={day:today,id:crypto.randomUUID(),counted:false};
      // If persistent storage is unavailable, show totals without inflating them.
      let writable=true;try{localStorage.setItem(key,JSON.stringify(saved))}catch{writable=false}
      const response=await fetch(endpoint,{method:writable&&!saved.counted?'POST':'GET',...(writable&&!saved.counted?{headers:{'Content-Type':'text/plain'},body:saved.id}:{}),credentials:'omit',signal:AbortSignal.timeout(8000)});
      if(!response.ok)throw Error('Unavailable');
      const data=await response.json();
      if(!Number.isSafeInteger(data.visitors)||data.visitors<0)throw Error('Invalid count');
      if(writable&&data.day===saved.day){saved.counted=true;saved.total=data.visitors;saved.updated=Date.now();try{localStorage.setItem(key,JSON.stringify(saved))}catch{}}
      if(display){display.textContent=data.visitors.toLocaleString('zh-TW');display.closest('.visitor-count').dataset.day=data.day}
    }catch{if(display)display.textContent='暫時無法取得'}
  }
  update();
  // No polling. A page left open overnight records the next day on return.
  document.addEventListener('visibilitychange',()=>{if(!document.hidden){try{if(JSON.parse(localStorage.getItem(key))?.day!==day())update()}catch{}}});
})();
