import manifest from './images-manifest.json' with {type:'json'};

// Only this read-only Worker may expose the private R2 bucket.
// Workers Free caps requests at 100,000/day; never loop or retry R2 reads here.
export async function handle(request, env, ctx, cache=globalThis.caches?.default) {
  // Reject hotlinks before checking cached responses or reading R2.
  let referrer;
  try{referrer=new URL(request.headers.get('Referer')||'');}catch{}
  if(referrer?.origin!=='https://wackyjazz.github.io')return new Response('Forbidden',{status:403,headers:{'Cache-Control':'no-store'}});
  const url=new URL(request.url);
  if(!['GET','HEAD'].includes(request.method))return new Response('Method not allowed',{status:405,headers:{Allow:'GET, HEAD'}});
  const match=/^\/images\/([0-9]{3}-[a-zA-Z0-9-]+\.(?:jpg|avif))$/.exec(url.pathname);
  const entry=match&&Object.hasOwn(manifest,match[1])?manifest[match[1]]:null;
  if(!entry)return new Response('Image not found',{status:404});
  if(url.searchParams.has('sha')&&url.searchParams.get('sha')!==entry.sha256.slice(0,12))return new Response('Image version changed; reload the guide',{status:410});
  if(request.headers.has('Range'))return new Response('Range requests are not supported',{status:416});
  const headers=new Headers({'Content-Type':entry.contentType||'image/jpeg','Content-Length':String(entry.bytes),'Cache-Control':'public, max-age=86400','ETag':'"'+entry.sha256+'"','Access-Control-Allow-Origin':'*','X-Content-Type-Options':'nosniff'});
  if(request.headers.get('If-None-Match')===headers.get('ETag')){headers.delete('Content-Length');return new Response(null,{status:304,headers});}
  if(request.method==='HEAD')return new Response(null,{headers});
  // Unknown query parameters cannot create an unbounded collection of cache keys.
  const cacheKey=new Request(url.origin+'/images/'+match[1]+'?sha='+entry.sha256.slice(0,12));
  try{const hit=await cache?.match(cacheKey);if(hit)return hit;}catch{/* cache misses remain one R2 read */}
  let object;
  try{object=await env.IMAGES.get(entry.key);}catch{return new Response('Image temporarily unavailable',{status:503,headers:{'Retry-After':'60'}});}
  if(!object)return new Response('Image not uploaded yet',{status:404});
  const response=new Response(object.body,{headers});
  if(cache)ctx.waitUntil(cache.put(cacheKey,response.clone()).catch(()=>{}));
  return response;
}
export default {fetch:handle};
