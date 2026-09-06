#!/usr/bin/env python3
"""Convert VSMStochasticProbe stage JSONL to analyzer manifest and audit reference/replay."""
import argparse, gzip, json
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser();p.add_argument('capture');args=p.parse_args();root=Path(args.capture).resolve()
manifest={'width':420,'height':410,'flip_y':True,'dtype':'float16','regions':{'roof':[35,20,380,70],'ledge':[15,315,390,80]},'comparison_variants':['tent','stochastic9'],'textures':{'shadow':{'channels':1},'source':{'channels':4},'output':{'channels':4},'accept':{'channels':1},'history':{'channels':4},'unsharp':{'channels':4},'motion':{'channels':4}},'frames':[]}
metadata=[]
for stage in sorted(root.iterdir()):
    path=stage/'frames.jsonl'
    if not path.is_file():continue
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        f=json.loads(line);metadata.append((stage,f))
        d={'variant':f['variant'],'scenario':f['scenario'],'phase':f['phase'],'step':f['step'],'camera_frame':f['cameraFrame'],'shader_frame_seed':f.get('shaderFrameSeed'), 'jitter':[f['jitter']['x'],f['jitter']['y']], 'valid':f['temporalCaptured'], 'state':f['state'],'fallback':f['fallback'],'textures':{}}
        for key in manifest['textures']:
            name=stage/f"{f['prefix']}_{key}.bin.gz"
            if name.is_file():d['textures'][key]=str(name.relative_to(root))
        manifest['frames'].append(d)
(root/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

def load(stage,f,name,channels=1,dtype=np.float16):
    raw=gzip.decompress((stage/f"{f['prefix']}_{name}.bin.gz").read_bytes())
    return np.frombuffer(raw,dtype).reshape(410,420,channels)[::-1].astype(np.float32)
def metrics(x):
    return {'mean':float(np.mean(x)),'p95':float(np.quantile(x,.95)),'max':float(np.max(x))} if np.size(x) else None
quality={'frame_count':len(metadata),'stages':{},'reference':{}}
for stage in sorted({s for s,f in metadata}):
    fs=sorted([f for s,f in metadata if s==stage],key=lambda f:f['step'])
    q={'frames':len(fs),'cameraFrames':[f['cameraFrame'] for f in fs],'jitter':[[f['jitter']['x'],f['jitter']['y']] for f in fs],'state_counts':{},'fallback_counts':{},'max_replay_error':0.,'frames_with_replay_missing':[],'frames_without_snapshot':[],'counters':[]}
    for f in fs:
        q['state_counts'][f['state']]=q['state_counts'].get(f['state'],0)+1;q['fallback_counts'][f['fallback']]=q['fallback_counts'].get(f['fallback'],0)+1
        q['max_replay_error']=max(q['max_replay_error'],f.get('replayMaxError',0))
        if f.get('replayMissingPixels',0)>0:q['frames_with_replay_missing'].append([f['step'],f['replayMissingPixels']])
        if not f.get('receiverSnapshot'):q['frames_without_snapshot'].append(f['step'])
        path=stage/f"{f['prefix']}_counters.bin.gz"
        if path.is_file():q['counters'].append([f['step']]+np.frombuffer(gzip.decompress(path.read_bytes()),np.uint32).astype(int).tolist())
    quality['stages'][stage.name]=q
refs=[(s,f) for s,f in metadata if f.get('referenceCaptured')]
if refs:
    data=np.stack([load(s,f,'reference',4,np.float32) for s,f in refs]); ref=data[:,:,:,1];valid=np.all(data[:,:,:,0]>=0,axis=0);mean=ref.mean(0)
    quality['reference']['frames']=[f['step'] for s,f in refs]
    quality['reference']['missing_mask_max']=float(data[:,:,:,0].max())
    for variant in ['tent','stochastic9']:
        ff=[(s,f) for s,f in metadata if f['variant']==variant and f['scenario']=='static'];estimate=np.stack([load(s,f,'shadow')[:,:,0] for s,f in ff]).mean(0)
        comparison={}
        for name,(x,y,w,h) in manifest['regions'].items():
            m=valid[y:y+h,x:x+w];d=(estimate-mean)[y:y+h,x:x+w];comparison[name]={'valid_pixels':int(m.sum()),'signed_error':metrics(d[m]),'absolute_error':metrics(np.abs(d[m])),'rmse':float(np.sqrt(np.mean(d[m]**2))) if m.any() else None}
        quality['reference'][variant+'_mean_vs_disk_reference']=comparison
(root/'capture-audit.json').write_text(json.dumps(quality,indent=2),encoding='utf-8')
print(root/'manifest.json');print(root/'capture-audit.json')
