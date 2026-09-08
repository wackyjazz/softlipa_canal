const ORIGIN='https://wackyjazz.github.io';
export const taipeiDay=(now=new Date())=>new Date(now.getTime()+8*3600000).toISOString().slice(0,10);
const reply=(data,status=200)=>Response.json(data,{status,headers:{'Access-Control-Allow-Origin':ORIGIN,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
export async function visitors(request,env,now=new Date()) {
  if(request.headers.get('Origin')!==ORIGIN)return reply({error:'Forbidden'},403);
  if(!['GET','POST'].includes(request.method))return reply({error:'Method not allowed'},405);
  const day=taipeiDay(now);
  try {
    if(request.method==='POST') {
      if(!request.headers.get('Content-Type')?.startsWith('text/plain'))return reply({error:'Invalid content type'},415);
      // Read at most 128 bytes, including chunked requests.
      const reader=request.body?.getReader();let size=0,parts=[];
      if(!reader)return reply({error:'Invalid visitor'},400);
      while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>128){await reader.cancel();return reply({error:'Too large'},413)}parts.push(value)}
      const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length}
      const id=new TextDecoder().decode(bytes);
      if(!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id))return reply({error:'Invalid visitor'},400);
      // Unique key + trigger are atomic, including simultaneous tabs/retries.
      const result=await env.VISITORS.batch([
        env.VISITORS.prepare('INSERT OR IGNORE INTO daily_visitors(day,visitor) VALUES (?,?)').bind(day,id),
        env.VISITORS.prepare('SELECT visitors FROM daily_totals WHERE day=?').bind(day)
      ]);
      return reply({day,visitors:result[1].results[0]?.visitors||0});
    }
    const row=await env.VISITORS.prepare('SELECT visitors FROM daily_totals WHERE day=?').bind(day).first();
    return reply({day,visitors:row?.visitors||0});
  }catch{return reply({error:'Statistics temporarily unavailable'},503)}
}
export async function cleanup(env,now=new Date()) {
  const cutoff=taipeiDay(new Date(now.getTime()-2*86400000));
  // Bounded daily deletion; aggregated day totals contain no browser identifiers.
  await env.VISITORS.prepare('DELETE FROM daily_visitors WHERE (day,visitor) IN (SELECT day,visitor FROM daily_visitors WHERE day < ? LIMIT 5000)').bind(cutoff).run();
}
