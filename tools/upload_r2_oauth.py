"""Upload through the same R2 REST API as Wrangler, using local OAuth credentials.
Default is local preflight only. No credentials are printed or copied into this project.
"""
import argparse,concurrent.futures,hashlib,json,re,threading,urllib.parse,urllib.request,urllib.error
from pathlib import Path
from upload_r2 import local_objects,Budget,MAX_BYTES,MAX_OBJECTS

class Client:
 def __init__(self,account,bucket,auth_file):
  if not re.fullmatch(r'[a-f0-9]{32}',account):raise ValueError('Invalid account ID')
  if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,61}[a-z0-9]',bucket):raise ValueError('Invalid bucket name')
  text=Path(auth_file).read_text();match=re.search(r'^oauth_token\s*=\s*"([^"\n]+)"',text,re.M)
  if not match:raise ValueError('Run wrangler login first')
  self.token=match.group(1);self.base=f'https://api.cloudflare.com/client/v4/accounts/{account}/r2/buckets/{bucket}';self.budget=Budget();self.lock=threading.Lock()
 def request(self,suffix='',method='GET',data=None,headers=None):
  with self.lock:self.budget.use()
  req=urllib.request.Request(self.base+suffix,data=data,method=method,headers={'Authorization':'Bearer '+self.token,**(headers or {})})
  try:
   with urllib.request.urlopen(req,timeout=60) as response:
    raw=response.read();body=json.loads(raw) if raw else {}
  except urllib.error.HTTPError as e:raise ValueError(f'Cloudflare HTTP {e.code}: '+e.read().decode()[:500]) from None
  if body.get('success') is False:raise ValueError('Cloudflare API failed: '+json.dumps(body.get('errors')))
  return body
 def inventory(self):
  items={};cursor=''
  for page in range(10):
   data=self.request('/objects?'+urllib.parse.urlencode({'per_page':1000,**({'cursor':cursor} if cursor else {})}))
   for e in data['result']:items[e['key']]=e
   info=data.get('result_info',{})
   if not info.get('is_truncated'):return items
   cursor=info.get('cursor')
   if not cursor:raise ValueError('Missing pagination cursor')
  raise ValueError('Inventory exceeds ten pages')

def validate_inventory(existing,objects):
 for key,e in existing.items():
  if not re.fullmatch(r'images/[0-9a-f]{64}\.(?:jpg|avif)',key):raise ValueError('Bucket contains other project data')
  if e.get('storage_class')!='Standard':raise ValueError('Bucket contains non-Standard objects')
  if key in objects and (e['size']!=objects[key]['bytes'] or e.get('etag','').strip('"')!=hashlib.md5(objects[key]['path'].read_bytes()).hexdigest()):raise ValueError('Existing object differs; refusing overwrite')
 pending={k:e for k,e in objects.items() if k not in existing}
 if len(existing)+len(pending)>MAX_OBJECTS or sum(e['size'] for e in existing.values())+sum(e['bytes'] for e in pending.values())>MAX_BYTES:raise ValueError('Conservative bucket limit exceeded')
 return pending

def upload(client,objects):
 info=client.request()['result']
 if info.get('storage_class')!='Standard':raise ValueError('Standard bucket required')
 managed=client.request('/domains/managed')['result']
 if managed.get('enabled') is not False:raise ValueError('Public r2.dev must be disabled')
 custom=client.request('/domains/custom')['result']
 if custom.get('domains'):raise ValueError('Dedicated bucket must not have public custom domains')
 pending=validate_inventory(client.inventory(),objects)
 def put(pair):
  key,e=pair;raw=e['path'].read_bytes()
  if hashlib.sha256(raw).hexdigest()!=e['sha256']:raise ValueError('Local file changed during upload')
  client.request('/objects/'+urllib.parse.quote(key,safe='/'),method='PUT',data=raw,headers={'Content-Type':e['contentType'],'Cache-Control':'public, max-age=31536000, immutable','cf-r2-storage-class':'Standard','cf-r2-data-catalog-check':'true'})
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  iterator=iter(pending.items());active=set()
  for _ in range(4):
   item=next(iterator,None)
   if item:active.add(pool.submit(put,item))
  done_count=0
  while active:
   done,active=concurrent.futures.wait(active,return_when=concurrent.futures.FIRST_COMPLETED)
   for future in done:
    future.result();done_count+=1
    if done_count%25==0:print(f'Uploaded {done_count}/{len(pending)}',flush=True)
    item=next(iterator,None)
    if item:active.add(pool.submit(put,item))
 final=client.inventory();remaining=validate_inventory(final,objects)
 if remaining:raise ValueError('Post-upload inventory missing objects')
 for key,e in objects.items():
  if final[key].get('http_metadata',{}).get('contentType')!=e['contentType']:raise ValueError('Incorrect Content-Type')
 return {'uploaded':len(pending),'skipped':len(objects)-len(pending),'verifiedObjects':len(objects),'bytes':sum(e['bytes'] for e in objects.values()),'verification':'All object sizes, single-PUT MD5 ETags and Content-Types match local SHA-validated files'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--free-account-confirmed',action='store_true');p.add_argument('--account');p.add_argument('--bucket',default='canal-guide-images');p.add_argument('--auth-file',type=Path);a=p.parse_args()
 try:
  objects=local_objects();print(json.dumps({'mode':'local preflight','uniqueObjects':len(objects),'bytes':sum(e['bytes'] for e in objects.values()),'remoteCalls':0}),flush=True)
  if a.apply:
   if not a.free_account_confirmed:raise ValueError('Confirm Workers Free/account usage before upload')
   if not a.account or not a.auth_file:raise ValueError('--account and local --auth-file are required')
   print(json.dumps(upload(Client(a.account,a.bucket,a.auth_file),objects)),flush=True)
 except (ValueError,FileNotFoundError) as e:raise SystemExit(str(e))
