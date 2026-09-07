import {test} from 'node:test';import assert from 'node:assert/strict';
import manifest from './images-manifest.json' with {type:'json'};import {handle} from './worker.mjs';
const name=Object.keys(manifest)[0],entry=manifest[name],base='https://canal-guide-images.example.workers.dev';
const context={waitUntil(p){return p;}};
function setup(result={body:new Uint8Array([255,216,255])}){let count=0;return {env:{IMAGES:{async get(key){count++;assert.equal(key,entry.key);return result;}}},count:()=>count};}
test('bad paths, writes, ranges and wrong versions never reach R2',async()=>{
 for(const [path,method,headers,status] of [['/no.jpg','GET',{},404],['/images/../worker.mjs','GET',{},404],['/images/'+name,'POST',{},405],['/images/'+name,'GET',{Range:'bytes=0-1'},416],['/images/'+name+'?sha=old','GET',{},410]]){const s=setup();const response=await handle(new Request(base+path,{method,headers}),s.env,context,null);assert.equal(response.status,status);assert.equal(s.count(),0);}
});
test('GET performs exactly one get; never writes/lists/heads R2',async()=>{const s=setup();const r=await handle(new Request(base+'/images/'+name),s.env,context,null);assert.equal(r.status,200);assert.equal(s.count(),1);assert.equal(r.headers.get('Content-Type'),entry.contentType||'image/jpeg');assert.equal(r.headers.get('ETag'),'"'+entry.sha256+'"');});
test('HEAD and conditional response require zero R2 reads',async()=>{for(const request of [new Request(base+'/images/'+name,{method:'HEAD'}),new Request(base+'/images/'+name,{headers:{'If-None-Match':'"'+entry.sha256+'"'}})]){const s=setup();const r=await handle(request,s.env,context,null);assert.equal(s.count(),0);assert.equal(r.status,request.method==='HEAD'?200:304);}});
test('query parameters share one canonical cache key',async()=>{const keys=[];let stored;const cache={async match(r){keys.push(r.url);return stored?.clone();},async put(r,v){stored=v;}};const s=setup();for(const q of ['?a=1','?a=2'])await handle(new Request(base+'/images/'+name+q),s.env,context,cache);assert.equal(keys[0],keys[1]);assert.equal(s.count(),1);});
test('missing R2 object returns 404 and is not cached',async()=>{const s=setup(null);const r=await handle(new Request(base+'/images/'+name),s.env,context,null);assert.equal(r.status,404);assert.equal(s.count(),1);});
test('R2 failure is not retried',async()=>{let calls=0;const env={IMAGES:{async get(){calls++;throw Error('Unavailable')}}};const r=await handle(new Request(base+'/images/'+name),env,context,null);assert.equal(r.status,503);assert.equal(calls,1);});
