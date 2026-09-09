/* Original game's stele layout: 680×460 text area, 26px Cubic font,
   6px row gap, 18px column gap, 15 right-to-left columns per page. */
(()=>{
const FONT=26,ROW=32,HEIGHT=460,COLUMNS=15;
function segments(line){const chars=Array.from(line),out=[];for(let i=0;i<chars.length;i++){let text=chars[i];if(!/[A-Za-z0-9()~～]/.test(text)){out.push({text,english:false});continue}while(i+1<chars.length&&((chars[i+1].charCodeAt(0)>=32&&chars[i+1].charCodeAt(0)<=126)||chars[i+1]==='～'))text+=chars[++i];out.push({text:text.trimEnd(),english:true});for(let j=text.trimEnd().length;j<text.length;j++)out.push({text:' ',english:false})}return out}
function columns(line){if(!line)return [''];const out=[];let text='',used=0;for(const part of segments(line)){const advance=part.english?Math.max(FONT,part.text.length*FONT*.62)+6:ROW;if(text&&used+advance>HEIGHT){out.push(text);text='';used=0}text+=part.text;used+=advance}if(text)out.push(text);return out}
function paginate(lines){const all=lines.flatMap(columns),pages=[];for(let i=0;i<all.length;i+=COLUMNS)pages.push(all.slice(i,i+COLUMNS));return pages.length?pages:[[]]}
function button(text,fn){const b=document.createElement('button');b.type='button';b.textContent=text;b.onclick=fn;return b}
const reader={entry:null,page:0,mode:'stone',zoomed:false,paginate,
 mount(entry,host){
  this.entry=entry;this.pages=paginate(entry.stele.lines);this.host=host;
  const params=new URLSearchParams(location.hash.slice(1));const same=params.get('asset')===entry.file;
  const requested=Number(params.get('page'));this.page=same&&Number.isInteger(requested)&&requested>=1?Math.min(requested,this.pages.length)-1:0;
  this.mode=same&&params.get('view')==='text'?'text':'stone';this.zoomed=false;
  host.classList.add('stele-interactive');host.classList.remove('stele-reader');
  this.tabs=document.createElement('div');this.tabs.className='stele-modes';this.tabs.setAttribute('role','group');this.tabs.setAttribute('aria-label','石牌閱讀方式');
  this.stoneButton=button('石牌翻頁',()=>this.setMode('stone'));this.textButton=button('原文閱讀',()=>this.setMode('text'));
  this.zoomButton=button('放大石牌',()=>{this.zoomed=!this.zoomed;this.update();this.stage.scrollLeft=this.stage.scrollWidth});
  this.tabs.append(this.stoneButton,this.textButton,this.zoomButton);
  this.stage=document.createElement('div');this.stage.className='stele-stage';this.stage.tabIndex=0;this.stage.setAttribute('aria-label','石牌畫面；左方向鍵下一頁，右方向鍵上一頁');
  this.canvas=document.createElement('canvas');this.canvas.width=960;this.canvas.height=850;this.canvas.setAttribute('role','img');this.stage.append(this.canvas);
  this.copy=document.createElement('div');this.copy.className='stele-copy';this.copy.textContent=entry.stele.lines.join('\n');
  this.nav=document.createElement('div');this.nav.className='stele-pages';this.nav.setAttribute('aria-label','石牌翻頁');
  this.nextButton=button('← 下一頁',()=>this.turn(1));this.prevButton=button('上一頁 →',()=>this.turn(-1));
  // aria-disabled keeps keyboard focus on the button when reaching an endpoint.
  this.indicator=document.createElement('span');this.indicator.setAttribute('role','status');this.indicator.setAttribute('aria-live','polite');
  this.nav.append(this.nextButton,this.indicator,this.prevButton);
  this.hint=document.createElement('p');this.hint.className='stele-hint';this.hint.textContent='直排由右向左閱讀 · ← 下一頁，→ 上一頁';
  host.append(this.tabs,this.stage,this.nav,this.hint,this.copy);
  this.background=new Image();this.background.onload=()=>{if(this.entry===entry)this.draw()};this.background.onerror=()=>{if(this.entry===entry){this.hint.textContent='石牌底圖暫時無法載入，仍可翻頁或切換原文閱讀。';this.draw()}};this.background.src=entry.stele.background;
  document.fonts.load('26px SteleCubic').then(()=>{if(this.entry===entry)this.draw()}).catch(()=>{});
  this.update();
 },
 setMode(mode){this.mode=mode;this.update()},
 turn(delta){const page=Math.max(0,Math.min(this.pages.length-1,this.page+delta));if(page===this.page)return;this.page=page;this.update()},
 update(){
  const stone=this.mode==='stone';this.host.classList.toggle('stele-reader',!stone);
  this.stage.hidden=this.nav.hidden=this.hint.hidden=this.zoomButton.hidden=!stone;this.copy.hidden=stone;
  this.stoneButton.setAttribute('aria-pressed',String(stone));this.textButton.setAttribute('aria-pressed',String(!stone));
  this.stage.classList.toggle('enlarged',this.zoomed);this.zoomButton.textContent=this.zoomed?'適合畫面':'放大石牌';this.zoomButton.setAttribute('aria-pressed',String(this.zoomed));
  this.indicator.textContent=`${this.page+1} / ${this.pages.length}`;
  this.prevButton.setAttribute('aria-disabled',String(this.page===0));this.nextButton.setAttribute('aria-disabled',String(this.page===this.pages.length-1));
  this.draw();this.syncUrl();
 },
 draw(){
  if(!this.canvas?.isConnected)return;const c=this.canvas.getContext('2d');c.clearRect(0,0,960,850);c.imageSmoothingEnabled=false;
  if(this.background?.complete&&this.background.naturalWidth)c.drawImage(this.background,19.2,18.2,921.6,813.6);
  c.font='26px SteleCubic, monospace';c.fillStyle='#F0C311';c.textAlign='center';c.textBaseline='middle';
  const page=this.pages[this.page];page.forEach((line,index)=>{const x=789-index*44;let y=234;for(const part of segments(line)){if(part.english){const width=Math.max(FONT,c.measureText(part.text).width);c.save();c.translate(x,y+(width-FONT)/2);c.rotate(Math.PI/2);c.fillText(part.text,0,0);c.restore();y+=width+6}else{c.save();c.translate(x,y);if(['〈','〉','⋯','（','）'].includes(part.text))c.rotate(Math.PI/2);c.fillText(part.text,0,0);c.restore();y+=ROW}}});
  this.canvas.setAttribute('aria-label',`${this.entry.name}，第 ${this.page+1} 頁，共 ${this.pages.length} 頁。${page.join('\n')}`);
 },
 syncUrl(){if(!this.entry)return;const params=new URLSearchParams();params.set('asset',this.entry.file);if(this.page)params.set('page',String(this.page+1));if(this.mode==='text')params.set('view','text');history.replaceState(null,'','#'+params)},
 close(){this.entry=null;this.canvas=null}
};
document.addEventListener('keydown',event=>{if(!reader.entry||reader.mode!=='stone'||!document.querySelector('#detail')?.open||event.altKey||event.ctrlKey||event.metaKey||/INPUT|TEXTAREA|SELECT/.test(event.target.tagName))return;if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();reader.turn(event.key==='ArrowLeft'?1:-1)}});
window.SteleReader=reader;
})();
