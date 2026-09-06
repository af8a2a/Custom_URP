#!/usr/bin/env python3
"""Matched-jitter, common-edge evidence for the temporary stochastic VSM experiment."""
import argparse,gzip,json
from pathlib import Path
import numpy as np

parser=argparse.ArgumentParser();parser.add_argument('capture');args=parser.parse_args();root=Path(args.capture).resolve()
regions={'roof':(35,20,380,70),'ledge':(15,315,390,80)}
variants=['tent','stochastic9']
def frames(stage):return sorted([json.loads(s) for s in (root/stage/'frames.jsonl').read_text().splitlines()],key=lambda f:f['step'])
def phase(f):return (round(f['jitter']['x'],8),round(f['jitter']['y'],8))
def read(stage,f,key,roi):
    ch=1 if key in ['shadow','accept'] else 4;dtype=np.float32 if key.startswith('debug') or key=='reference' else np.float16
    a=np.frombuffer(gzip.decompress((root/stage/f"{f['prefix']}_{key}.bin.gz").read_bytes()),dtype).reshape(410,420,ch)[::-1]
    x,y,w,h=roi;a=a[y:y+h,x:x+w].astype(np.float32)
    if key in ['source','output','unsharp']:return a[:,:,:3]@np.array([.2126,.7152,.0722],np.float32)
    if key=='motion':return np.linalg.norm(a[:,:,:2]*np.array([1920,1080],np.float32),axis=2)
    if key in ['reference','debug5']:return a
    return a[:,:,0]
def series(stage,ff,key,roi):return np.stack([read(stage,f,key,roi) for f in ff])
def refs(a,ff,indices=None):
    if indices is None:indices=list(range(len(ff)))
    return {p:a[[i for i in indices if phase(ff[i])==p]].mean(0) for p in {phase(ff[i]) for i in indices}}
def residual(a,ff):
    r=refs(a,ff);return a-np.stack([r[phase(f)] for f in ff])
def metric(values):
    x=np.asarray(values);return {'mean':float(x.mean()),'median':float(np.median(x)),'p95':float(np.quantile(x,.95)),'max':float(x.max())}
def noise(a,ff,mask):
    rr=residual(a,ff)[:,mask];var=(rr*rr).mean(0);totalvar=a[:,mask].var(0)
    return {'mean_pixel_variance':float(var.mean()),'rms_pixel_std':float(np.sqrt(var.mean())),'pixel_std':metric(np.sqrt(var)),'total_variance_including_jitter':float(totalvar.mean())}
def edge_mask(mean,valid):
    mask=((mean>.05)&(mean<.95))|((np.abs(np.diff(mean,axis=0,prepend=mean[:1]))+np.abs(np.diff(mean,axis=1,prepend=mean[:,:1])))>.05)
    for _ in range(2):
        a=np.pad(mask,1);mask=a[1:-1,1:-1]|a[:-2,1:-1]|a[2:,1:-1]|a[1:-1,:-2]|a[1:-1,2:]
    return mask&valid
out={'method':{'roi_coordinates_are_relative_to_native_crop':[700,170,420,410],'regions':regions,'static_noise':'Each pixel is demeaned within its exact 8-phase TSR jitter group, then averaged variance over a common disk-reference edge mask. Six samples per phase.','edge_mask':'1024-tap reference average: partial shadow [.05,.95] or gradient>.05; dilated by 2 pixels; valid reference in all eight phases. Same mask for both variants.','reference':'Eight same-kernel 1024-comparison deterministic disk frames; separates disk-kernel change from Monte Carlo estimation. Not a higher-resolution visibility truth.','light_response':'Pre A mean per jitter phase from steps0..15; settled B mean per phase from64..95. Retention is projection of current-B onto A-B, shared raw-shadow-change mask. Step16 is VSM invalidation frame, response summary starts at first Active frame.','variance_limits':'Same-phase variance excludes deterministic jitter shimmer, and includes residual stochastic noise/history evolution. Not a visual-quality score.'},'static':{},'light_step':{},'camera':{},'validation':{}}
for scenario in ['static','camera','light_step']:
    left=frames('tent_'+scenario);right=frames('stochastic9_'+scenario)
    out['validation'][scenario]={'paired_frames':len(left),'steps_match':[f['step'] for f in left]==[f['step'] for f in right],'jitter_matches':all(phase(a)==phase(b) for a,b in zip(left,right)),'camera_pose_matches':all(a['cameraPosition']==b['cameraPosition'] and a['cameraEuler']==b['cameraEuler'] for a,b in zip(left,right)),'light_pose_matches':all(a['lightEuler']==b['lightEuler'] for a,b in zip(left,right)),'all_temporal_paired':all(f['temporalCaptured'] for f in left+right),'all_shader_seeds_match_cameraFrame':all(f['shaderFrameSeed']==f['cameraFrame'] for f in left+right)}
for name,roi in regions.items():
    rf=frames('stochastic9_static');rf=[f for f in rf if f['referenceCaptured']]
    ref=series('stochastic9_static',rf,'reference',roi);valid=np.all(ref[:,:,:,0]>=0,axis=0);mean=ref[:,:,:,1].mean(0);mask=edge_mask(mean,valid)
    result={'edge_pixels':int(mask.sum()),'valid_pixels':int(valid.sum()),'variants':{}}
    for variant in variants:
        stage=variant+'_static';ff=frames(stage);a={k:series(stage,ff,k,roi) for k in ['shadow','source','output','unsharp','accept','history','motion']}
        v={k:noise(a[k],ff,mask) for k in ['shadow','source','output','unsharp']}
        v['final_to_source_noise_rms_ratio']=v['output']['rms_pixel_std']/max(v['source']['rms_pixel_std'],1e-15)
        v['accepted_fraction']=float((a['accept'][:,mask]>.5).mean());v['history_samples']=metric(a['history'][:,mask]);v['motion_pixels']=metric(a['motion'][:,mask])
        error=a['shadow'].mean(0)-mean
        v['mean_vs_disk_reference']={'edge_mae':float(np.abs(error[mask]).mean()),'edge_rmse':float(np.sqrt(np.mean(error[mask]**2))),'edge_signed_bias':float(error[mask].mean()),'valid_mae':float(np.abs(error[valid]).mean())}
        result['variants'][variant]=v
    out['static'][name]=result
    # Light-step comparison with one shared changed-shadow mask.
    data={}
    for variant in variants:
        stage=variant+'_light_step';ff=frames(stage);a={k:series(stage,ff,k,roi) for k in ['shadow','source','output','accept','history','motion']}
        pre=[i for i,f in enumerate(ff) if f['step']<16];post=[i for i,f in enumerate(ff) if f['step']>=64]
        data[variant]=(ff,a,pre,post)
    changes=[np.abs(a['shadow'][pre].mean(0)-a['shadow'][post].mean(0))>.2 for ff,a,pre,post in data.values()]
    changed=changes[0]&changes[1]
    result={'common_changed_pixels':int(changed.sum()),'variants':{}}
    for variant,(ff,a,pre,post) in data.items():
        before={k:refs(a[k],ff,pre) for k in ['shadow','source','output']};after={k:refs(a[k],ff,post) for k in ['shadow','source','output']};rows=[]
        for i,f in enumerate(ff):
            if f['step']<16:continue
            p=phase(f);row={'step':f['step'],'state':f['state'],'fallback':f['fallback']}
            for k in ['shadow','source','output']:
                direction=(before[k][p]-after[k][p])[changed];r=(a[k][i]-after[k][p])[changed];den=float(np.dot(direction,direction))
                row[k+'_retention']=float(np.dot(r,direction)/den) if den else None
                row[k+'_normalized_residual_rms']=float(np.sqrt(np.dot(r,r)/den)) if den else None
            row['accepted_fraction']=float((a['accept'][i][changed]>.5).mean()) if changed.any() else None
            row['history_samples_mean']=float(a['history'][i][changed].mean()) if changed.any() else None
            row['motion_pixels_mean']=float(a['motion'][i][changed].mean()) if changed.any() else None
            row['motion_under_1px_fraction']=float((a['motion'][i][changed]<=1).mean()) if changed.any() else None
            rows.append(row)
        active=[r for r in rows if r['state']=='Active'];settle=None
        for i in range(len(active)-2):
            if all(r['output_retention'] is not None and abs(r['output_retention'])<.1 for r in active[i:i+3]) and active[i+2]['step']==active[i]['step']+2:
                settle=active[i]['step'];break
        result['variants'][variant]={'first_active_step':active[0]['step'] if active else None,'retention_below10pct_for3frames_step':settle,'delay_frames_from_step16':settle-16 if settle is not None else None,'first8_active':active[:8],'trajectory':rows}
    out['light_step'][name]=result
    # End-of-motion stationary recovery, using common static edge mask.
    result={}
    for variant in variants:
        ff=frames(variant+'_camera');post=[f for f in ff if f['step']>=64];a=series(variant+'_camera',post,'output',roi)
        result[variant]={'post_noise':noise(a,post,mask),'post_steps':[f['step'] for f in post]}
    out['camera'][name]=result
(root/'stochastic-evidence.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for roi,r in out['static'].items():
 print('STATIC',roi,'edge',r['edge_pixels'])
 for v,a in r['variants'].items():print(v,'rawSTD',a['shadow']['rms_pixel_std'],'sourceSTD',a['source']['rms_pixel_std'],'finalSTD',a['output']['rms_pixel_std'],'finalVAR',a['output']['mean_pixel_variance'],'ratio',a['final_to_source_noise_rms_ratio'],'MAE',a['mean_vs_disk_reference']['edge_mae'],'accept',a['accepted_fraction'])
for roi,r in out['light_step'].items():
 print('LIGHT',roi,'mask',r['common_changed_pixels'])
 for v,a in r['variants'].items():print(v,'firstActive',a['first_active_step'],'settle',a['retention_below10pct_for3frames_step'],'first4',[{k:x[k] for k in ['step','shadow_retention','output_retention','accepted_fraction','motion_pixels_mean']} for x in a['first8_active'][:4]])
print(root/'stochastic-evidence.json')
