#!/usr/bin/env python3
"""Camera motion diagnostics: differences are not labelled noise or ghosting."""
import argparse, gzip, json
from pathlib import Path
import numpy as np

p = argparse.ArgumentParser(); p.add_argument('capture'); root = Path(p.parse_args().capture).resolve()
regions = {'roof': (35,20,380,70), 'ledge': (15,315,390,80)}
variants = ['tent','stochastic9']
def frames(stage):
    return sorted([json.loads(s) for s in (root/stage/'frames.jsonl').read_text().splitlines()], key=lambda f:f['step'])
def phase(f): return (round(f['jitter']['x'],8),round(f['jitter']['y'],8))
def read(stage,f,key,roi):
    ch = 1 if key in ['shadow','accept'] else 4
    dt = np.float32 if key in ['reference','debug5'] else np.float16
    a = np.frombuffer(gzip.decompress((root/stage/f"{f['prefix']}_{key}.bin.gz").read_bytes()),dt).reshape(410,420,ch)[::-1]
    x,y,w,h = roi; a = a[y:y+h,x:x+w].astype(np.float32)
    if key in ['source','output']: return a[:,:,:3] @ np.array([.2126,.7152,.0722],np.float32)
    if key=='motion': return np.linalg.norm(a[:,:,:2]*np.array([1920,1080],np.float32),axis=2)
    return a if key in ['reference','debug5'] else a[:,:,0]
def series(stage,ff,key,roi): return np.stack([read(stage,f,key,roi) for f in ff])
def edges(a):
    mask=((a>.05)&(a<.95))|((np.abs(np.diff(a,axis=0,prepend=a[:1]))+np.abs(np.diff(a,axis=1,prepend=a[:,:1])))>.05)
    for _ in range(2):
        q=np.pad(mask,1); mask=q[1:-1,1:-1]|q[:-2,1:-1]|q[2:,1:-1]|q[1:-1,:-2]|q[1:-1,2:]
    return mask
def rms(a): return float(np.sqrt(np.mean(a*a)))
def phase_refs(a,ff): return {p:a[[i for i,f in enumerate(ff) if phase(f)==p]].mean(0) for p in {phase(f) for f in ff}}
def noise(a,ff,mask):
    ref=phase_refs(a,ff); residual=a-np.stack([ref[phase(f)] for f in ff])
    return rms(residual[:,mask])
out={'method':{'motion_frames':'Steps0..63 with per-frame common edge mask (union of the two raw shadow masks), identical camera/light/jitter paths. Pairwise differences include kernel and Monte Carlo effects and are not ghosting/noise estimates.', 'post_frames':'Steps64..95 camera stationary. Metrics against matching-jitter phase means of each variant static stage include recovery plus any residual state difference; they are not ground-truth error.', 'post_noise':'Same-phase residual RMS on the shared static 1024-disk-reference edge mask; separates steps64..79 and80..95, two frames per jitter phase per window. Values include recovery, not only random noise.', 'units':'Linear HDR luma for source/output; [0,1] visibility for shadow; motion uses UV*1920x1080 pixels.'},'regions':{}}
for name,roi in regions.items():
    ref_frames=[f for f in frames('stochastic9_static') if f['referenceCaptured']]
    ref=series('stochastic9_static',ref_frames,'reference',roi)
    static_mask=edges(ref[:,:,:,1].mean(0)) & np.all(ref[:,:,:,0]>=0,axis=0)
    data={}
    for v in variants:
        stage=v+'_camera'; ff=frames(stage)
        data[v]=(ff,{k:series(stage,ff,k,roi) for k in ['shadow','source','output','motion','accept']})
    moving=[]
    for i in range(64):
        left=data['tent'][1]; right=data['stochastic9'][1]
        mask=edges(left['shadow'][i])|edges(right['shadow'][i])
        row={'step':i,'common_edge_pixels':int(mask.sum()),'pairwise_difference':{},'variants':{}}
        for k in ['shadow','source','output']:
            diff=right[k][i][mask]-left[k][i][mask]
            row['pairwise_difference'][k]={'mae':float(np.abs(diff).mean()),'rms':rms(diff)}
        for v,(ff,a) in data.items():
            motion=a['motion'][i][mask]
            row['variants'][v]={'motion_pixels_mean':float(motion.mean()),'motion_gt1px_fraction':float((motion>1).mean()),'accepted_fraction':float((a['accept'][i][mask]>.5).mean())}
        moving.append(row)
    result={'static_edge_pixels':int(static_mask.sum()),'moving_trajectory':moving,'moving_summary':{},'post_stationary':{}}
    for v in variants:
        result['moving_summary'][v]={k:float(np.mean([r['variants'][v][k] for r in moving])) for k in ['motion_pixels_mean','motion_gt1px_fraction','accepted_fraction']}
    result['moving_summary']['pairwise_output_mae_mean']=float(np.mean([r['pairwise_difference']['output']['mae'] for r in moving]))
    for v,(ff,a) in data.items():
        sf=frames(v+'_static'); baseline={k:phase_refs(series(v+'_static',sf,k,roi),sf) for k in ['shadow','source','output']}
        rows=[]
        for i in range(64,96):
            row={'step':i,'phase':phase(ff[i])}
            for k in ['shadow','source','output']:
                diff=(a[k][i]-baseline[k][phase(ff[i])])[static_mask]
                row[k+'_static_phase_mae']=float(np.abs(diff).mean()); row[k+'_static_phase_rms']=rms(diff)
            rows.append(row)
        result['post_stationary'][v]={'trajectory':rows,'windows':{}}
        for start,stop in [(64,80),(80,96)]:
            window={k+'_same_phase_residual_rms':noise(a[k][start:stop],ff[start:stop],static_mask) for k in ['shadow','source','output']}
            for k in ['shadow','source','output']:
                window[k+'_static_phase_rms_mean']=float(np.mean([r[k+'_static_phase_rms'] for r in rows[start-64:stop-64]]))
            window['accepted_fraction']=float((a['accept'][start:stop,static_mask]>.5).mean())
            window['motion_pixels_mean']=float(a['motion'][start:stop,static_mask].mean())
            result['post_stationary'][v]['windows'][f'{start}..{stop-1}']=window
    out['regions'][name]=result
(root/'camera-evidence.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for name,r in out['regions'].items():
    print(name,'moving',r['moving_summary'])
    for v,x in r['post_stationary'].items(): print(v,x['windows'])
print(root/'camera-evidence.json')
