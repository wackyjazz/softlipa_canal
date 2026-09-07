"""Validate locally by default. Upload immutable JPEG/AVIF images only with --apply."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, re
ROOT=Path(__file__).resolve().parents[1]
MAX_BYTES=1_000_000_000
MAX_OBJECTS=10_000
MAX_MONTHLY_OPERATIONS=10_000

def local_objects():
    manifest=json.loads((ROOT/'cloudflare/images-manifest.json').read_text())
    result={}
    for filename,entry in manifest.items():
        if not re.fullmatch(r'[0-9]{3}-[A-Za-z0-9-]+\.(?:jpg|avif)',filename):raise ValueError('Invalid image filename')
        path=ROOT/'r2-images'/filename;raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['sha256'] or len(raw)!=entry['bytes'] or not (raw.startswith(b'\xff\xd8') if path.suffix=='.jpg' else raw[4:8]==b'ftyp' and b'avif' in raw[8:32]):
            raise ValueError('Image integrity check failed: '+filename)
        if entry['key']!='images/'+entry['sha256']+path.suffix:raise ValueError('Invalid object key')
        if entry.get('contentType')!=('image/avif' if path.suffix=='.avif' else 'image/jpeg'):raise ValueError('Invalid content type')
        result[entry['key']]={'path':path,**entry}
    if len(result)>MAX_OBJECTS or sum(e['bytes'] for e in result.values())>MAX_BYTES:raise ValueError('Package exceeds conservative upload limits')
    return result

class Budget:
    def __init__(self):
        self.path=ROOT/'.upload-ledger.json';month=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m')
        self.data=json.loads(self.path.read_text()) if self.path.exists() else {}
        if self.data.get('month')!=month:self.data={'month':month,'operations':0}
    def use(self):
        if self.data['operations']>=MAX_MONTHLY_OPERATIONS:raise ValueError('Local monthly operation budget exhausted; no more remote calls')
        self.data['operations']+=1
        temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(self.data));temp.replace(self.path)

def upload(client,bucket,objects,budget):
    # At most ten inventory calls; fail before uploads if this is not a small dedicated bucket.
    existing={};token=None
    for page in range(10):
        budget.use();args={'Bucket':bucket,'MaxKeys':1000}
        if token:args['ContinuationToken']=token
        response=client.list_objects_v2(**args)
        for item in response.get('Contents',[]):existing[item['Key']]=item['Size']
        if not response.get('IsTruncated'):break
        token=response.get('NextContinuationToken')
    else:raise ValueError('Bucket inventory is too large; upload stopped')
    if any(not re.fullmatch(r'images/[0-9a-f]{64}\.(?:jpg|avif)',key) for key in existing):raise ValueError('Bucket contains other project data; use a dedicated bucket')
    pending={k:v for k,v in objects.items() if k not in existing}
    projected=sum(existing.values())+sum(v['bytes'] for v in pending.values())
    if projected>MAX_BYTES or len(existing)+len(pending)>MAX_OBJECTS:raise ValueError('Existing + new images exceed the conservative bucket limit; upload stopped')
    for key,entry in objects.items():
        if key in existing and existing[key]!=entry['bytes']:raise ValueError('Existing object size mismatch; refusing to overwrite')
    for n,(key,entry) in enumerate(pending.items(),1):
        budget.use()
        with entry['path'].open('rb') as body:
            client.put_object(Bucket=bucket,Key=key,Body=body,ContentLength=entry['bytes'],ContentType=entry.get('contentType','image/jpeg'),CacheControl='public, max-age=31536000, immutable',StorageClass='STANDARD',Metadata={'sha256':entry['sha256']})
        if n%50==0:print(f'Uploaded {n}/{len(pending)}')
    return {'uploaded':len(pending),'skipped':len(objects)-len(pending),'projectedBucketBytes':projected}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--free-account-confirmed',action='store_true');p.add_argument('--bucket',default='canal-guide-images');a=p.parse_args()
    try:
        objects=local_objects();print(json.dumps({'uniqueObjects':len(objects),'bytes':sum(e['bytes'] for e in objects.values()),'remoteCalls':0,'mode':'local preflight'},ensure_ascii=False))
        if a.apply:
            if not a.free_account_confirmed:raise ValueError('Read FREE-TIER.md and confirm the dedicated free account/private bucket settings before --apply --free-account-confirmed.')
            import boto3
            from botocore.config import Config
            account=os.environ.get('CLOUDFLARE_ACCOUNT_ID','')
            if not re.fullmatch(r'[a-fA-F0-9]{32}',account):raise ValueError('Set CLOUDFLARE_ACCOUNT_ID locally')
            access=os.environ.get('R2_ACCESS_KEY_ID');secret=os.environ.get('R2_SECRET_ACCESS_KEY')
            if not access or not secret:raise ValueError('Set R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY locally; do not put them in GitHub')
            client=boto3.client('s3',endpoint_url=f'https://{account}.r2.cloudflarestorage.com',region_name='auto',aws_access_key_id=access,aws_secret_access_key=secret,config=Config(retries={'total_max_attempts':1},request_checksum_calculation='when_required',response_checksum_validation='when_required'))
            print(json.dumps(upload(client,a.bucket,objects,Budget()),ensure_ascii=False))
    except (ValueError,FileNotFoundError) as e:raise SystemExit(str(e))
