"""Build a Pages artifact. No deployment or credentials required."""
from pathlib import Path
import argparse, json, os, re, shutil
from urllib.parse import urlsplit, urlunsplit
ROOT=Path(__file__).resolve().parents[1]

def build(mode,base,output):
    if mode=='r2':
        url=urlsplit(base)
        if url.scheme!='https' or not re.fullmatch(r'[a-z0-9-]+\.[a-z0-9-]+\.workers\.dev',url.netloc) or url.path not in ['', '/'] or url.query or url.fragment:
            raise ValueError('R2 mode needs the deployed https://WORKER.SUBDOMAIN.workers.dev URL (--image-base or R2_IMAGE_BASE).')
        base=base.rstrip('/')
    if output.exists():
        if not (output/'.guide-build').exists():raise ValueError('Refusing to replace a directory not created by this builder.')
        shutil.rmtree(output)
    shutil.copytree(ROOT/'web',output)
    (output/'.guide-build').write_text('Generated Pages output\n')
    (output/'.nojekyll').touch()
    p=output/'data/guide-data.js';raw=p.read_text();data=json.loads(raw.removeprefix('window.GUIDE_DATA=').strip().removesuffix(';'))
    for event in data['events']:
        for frame in event['frames']:
            if frame['image'].startswith('assets/images/') and mode=='r2':frame['image']=base+'/images/'+frame['image'].removeprefix('assets/images/')
    p.write_text('window.GUIDE_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    if mode=='github-only':
        if not (ROOT/'r2-images').is_dir():raise ValueError('github-only mode needs the r2-images folder included in the deployment ZIP.')
        shutil.copytree(ROOT/'r2-images',output/'assets/images')
    size=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    if size>900_000_000:raise ValueError('Pages artifact exceeds this package\'s 900 MB limit.')
    return {'mode':mode,'bytes':size,'events':len(data['events']),'frames':sum(len(e['frames']) for e in data['events']),'imageBase':base if mode=='r2' else 'local'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['r2','github-only'],default='r2');p.add_argument('--image-base',default=os.environ.get('R2_IMAGE_BASE',''));p.add_argument('--output',type=Path,default=ROOT/'_site');a=p.parse_args()
    try:print(json.dumps(build(a.mode,a.image_base,a.output.resolve()),ensure_ascii=False))
    except ValueError as e:raise SystemExit(str(e))
