#!/usr/bin/env python3
"""Phase-aware TSR lighting response comparison from production GPU readbacks.

Usage: python analyze_tsr_lighting_response.py BASELINE [AFTER] [--output FILE]
Payloads are gzip, top-left ROI 700,170,420,410 with bottom-up binary rows.
"""
import argparse, gzip, json, os
from pathlib import Path
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
import numpy as np

p=argparse.ArgumentParser(); p.add_argument('baseline'); p.add_argument('after',nargs='?'); p.add_argument('--output'); p.add_argument('--scene-linear',action='store_true'); p.add_argument('--static-only',action='store_true'); p.add_argument('--mask-baseline'); p.add_argument('--static-baseline'); args=p.parse_args()
roots={'baseline':Path(args.baseline).resolve()}
if args.after: roots['after']=Path(args.after).resolve()
regions={'roof':(35,20,380,70),'ledge':(15,315,390,80)}
variants=['tent','stochastic9']
colors={'source','output','unsharp','raw_history','accepted_history','spatial','resurrection'}

def frames(root,stage):
    return sorted([json.loads(s) for s in (root/stage/'frames.jsonl').read_text().splitlines()],key=lambda f:f['step'])
def phase(f): return (round(f['jitter']['x'],8),round(f['jitter']['y'],8))
def payload(root,stage,f,key,roi):
    ch=1 if key in ['shadow','accept','depth_error'] else 4;dt=np.float32 if key.startswith('debug') else np.float16
    a=np.frombuffer(gzip.decompress((root/stage/f"{f['prefix']}_{key}.bin.gz").read_bytes()),dt).reshape(410,420,ch)[::-1]
    x,y,w,h=roi;return a[y:y+h,x:x+w].astype(np.float32)
def read(root,stage,f,key,roi):
    a=payload(root,stage,f,key,roi)
    if key in colors:
        color=a[:,:,:3]@np.array([.2126,.7152,.0722],np.float32)
        exposure=root/stage/f"{f['prefix']}_pre_exposure.bin.gz"
        if args.scene_linear:
            if not exposure.exists():raise ValueError('Scene-linear analysis requires pre-exposure for every color frame: '+str(exposure))
            scale=float(np.frombuffer(gzip.decompress(exposure.read_bytes()),np.float32)[0])
            color/=max(scale,1e-4)
        return color
    if key=='motion':return np.linalg.norm(a[:,:,:2]*np.array([1920,1080],np.float32),axis=2)
    return a[:,:,0]
def series(root,stage,ff,key,roi):return np.stack([read(root,stage,f,key,roi) for f in ff])
def available(root,stage,ff,key):return all((root/stage/f"{f['prefix']}_{key}.bin.gz").exists() for f in ff)
def shading_masks(root,stage,f,roi):
    alpha=payload(root,stage,f,'accepted_history',roi)[:,:,3]
    if f.get('stationaryShadingResponse',False):return alpha==-1,alpha==-2
    rejected=alpha<0 if f.get('temporalShadingConfirmation',False) else alpha<.5
    return rejected,np.zeros_like(rejected)
def color_rejected_mask(root,stage,f,roi):return shading_masks(root,stage,f,roi)[0]
def shading_response_mask(root,stage,f,roi):return shading_masks(root,stage,f,roi)[1]
def refs(a,ff,idx=None):
    if idx is None:idx=range(len(ff))
    return {ph:a[[i for i in idx if phase(ff[i])==ph]].mean(0) for ph in {phase(ff[i]) for i in idx}}
def metric(x):
    return {'mean':float(x.mean()),'median':float(np.median(x)),'p95':float(np.quantile(x,.95)),'max':float(x.max())}
def noise(a,ff,mask):
    means=refs(a,ff);r=a-np.stack([means[phase(f)] for f in ff]);within=np.mean(r[:,mask]**2,axis=0);total=np.var(a[:,mask],axis=0)
    phasevar=np.maximum(total-within,0)
    return {'same_phase_variance':float(within.mean()),'same_phase_rms':float(np.sqrt(within.mean())),
            'total_variance':float(total.mean()),'total_rms':float(np.sqrt(total.mean())),
            'phase_mean_variance':float(phasevar.mean()),'phase_mean_rms':float(np.sqrt(phasevar.mean())),
            'same_phase_pixel_std':metric(np.sqrt(within))}
def edge_mask(a):
    mask=((a>.05)&(a<.95))|((np.abs(np.diff(a,axis=0,prepend=a[:1]))+np.abs(np.diff(a,axis=1,prepend=a[:,:1])))>.05)
    for _ in range(2):
        q=np.pad(mask,1);mask=q[1:-1,1:-1]|q[:-2,1:-1]|q[2:,1:-1]|q[1:-1,:-2]|q[1:-1,2:]
    return mask
def first_three(active,key,threshold):
    for i in range(len(active)-2):
        if active[i+2]['step']==active[i]['step']+2 and all(r[key] is not None and abs(r[key])<threshold for r in active[i:i+3]):
            return active[i]['step']
    return None
def control_rows(root,stage,ff):
    rows=[]
    for f in ff:
        rgb=payload(root,stage,f,'source',(200,130,100,70))[:,:,:3].mean((0,1))
        r={'step':f['step'],'jitter':list(phase(f)),'source_rgb':rgb.tolist()}
        path=root/stage/f"{f['prefix']}_pre_exposure.bin.gz"
        if path.exists():r['pre_exposure']=float(np.frombuffer(gzip.decompress(path.read_bytes()),np.float32)[0])
        rows.append(r)
    return rows
def audit(root,static_root=None):
    result={}
    for variant in variants:
        for scenario in (['static'] if args.static_only else ['static','camera','light_step']):
            stage=variant+'_'+scenario;stage_root=static_root if scenario=='static' and static_root is not None else root
            ff=frames(stage_root,stage);fallback=[{'step':f['step'],'state':f['state'],'fallback':f['fallback']} for f in ff if f['state']!='Active']
            counters=[np.frombuffer(gzip.decompress((stage_root/stage/f"{f['prefix']}_counters.bin.gz").read_bytes()),np.uint32) for f in ff]
            result[stage]={'frames':len(ff),'unique_unity_frames':len({f['unityFrame'] for f in ff}),
                'unique_camera_frames':len({f['cameraFrame'] for f in ff}),
                'temporal_paired':all(f['temporalCaptured'] for f in ff),
                'history_paired':all(f.get('historyCaptured',False) for f in ff),
                'seed_matches_camera_frame':all(f['shaderFrameSeed']==f['cameraFrame'] for f in ff),
                'replay_max_error':max(f['replayMaxError'] for f in ff),
                'replay_missing_pixels':sum(f['replayMissingPixels'] for f in ff),
                'counter_max':np.stack(counters).max(0).tolist(),'fallback':fallback,
                'resolutions':sorted({f['resolution'] for f in ff}),
                'effectiveAA':sorted({f['effectiveAA'] for f in ff}),
                'first_jitter':list(phase(ff[0])),
                'stage_root':str(stage_root),
                'pre_exposure_recorded_all_frames':available(stage_root,stage,ff,'pre_exposure'),
                'control_rgb_trajectory':control_rows(stage_root,stage,ff)}
    return result
def pair(root_a,root_b,stage):
    a=frames(root_a,stage);b=frames(root_b,stage)
    return {'frame_counts_match':len(a)==len(b),**{k:all(x[k]==y[k] for x,y in zip(a,b)) for k in ['step','jitter','gpuVP','cameraPosition','cameraEuler','lightEuler','depthBias','slopeBias']},
            'actual_random_seeds_match':all(x['shaderFrameSeed']==y['shaderFrameSeed'] for x,y in zip(a,b))}

out={'method':{'native_crop':[700,170,420,410],'regions':regions,
    'mask':'Common for baseline/after and both filters. Static: union of two baseline mean-shadow edge masks, valid baseline tent debug5 pixels. Light: intersection of baseline raw-shadow changes >.2 for both filters, separately for each direction.',
    'static_variance':'Total population temporal variance = same-phase residual variance + phase-mean variance, weighted by actual phase sample count. Same-phase alone can conceal new deterministic jitter shimmer.',
    'units':'Scene-linear color with --scene-linear (requires GPU scalar in every frame), otherwise pre-exposed HDR in all runs. Never compare absolute color variance across unlike exposure scales. Raw shadow is [0,1] visibility. With stationaryShadingResponse=true, alpha=-1 is hard color rejection and alpha=-2 is a separate soft stationary response; the latter may retain acceptance mask=1. Earlier temporalShadingConfirmation captures treat alpha<0 as hard rejection; legacy captures use alpha<.5.',
    'scene_linear_normalization_enabled':args.scene_linear,
    'mask_baseline':str(Path(args.mask_baseline).resolve() if args.mask_baseline else roots['baseline']),
    'static_baseline':str(Path(args.static_baseline).resolve()) if args.static_baseline else None,
    'control_rgb':'Unshadowed wall rectangle x=200,y=130,w=100,h=70 relative to the native crop. Always records raw pre-exposed source RGB, before optional normalization.',
    'response':'Old-state retention is projection of current minus settled-after onto settled-before minus settled-after. References are means per exact jitter phase. First three consecutive Active frames with absolute output retention <.1; not a per-pixel or permanent-settle guarantee.',
    'forward_reference':'A=steps0..15; B=64..95; trigger16.',
    'reverse_reference':'A=steps64..95; B=144..175; trigger96.',
    'camera':'No moving-frame image difference is labelled ghosting/noise. Stationary windows after movement include historical recovery.',
    'limits':['No higher-resolution visibility reference.','Diagnostic capture is unsuitable for performance claims.','Random seeds are actual camera frame indices, which may differ between runs even with matched jitter.']},
    'roots':{k:str(v) for k,v in roots.items()},'audit':{k:audit(v,Path(args.static_baseline).resolve() if k=='baseline' and args.static_baseline else None) for k,v in roots.items()},'pairing':{},'static':{},'light_step':{},'camera_post':{}}
if 'after' in roots:
    out['pairing']={v+'_'+s:pair(Path(args.static_baseline).resolve() if s=='static' and args.static_baseline else roots['baseline'],roots['after'],v+'_'+s) for v in variants for s in (['static'] if args.static_only else ['static','camera','light_step'])}
    for stage,r in out['pairing'].items():
        before=np.array([x['source_rgb'] for x in out['audit']['baseline'][stage]['control_rgb_trajectory']])
        after=np.array([x['source_rgb'] for x in out['audit']['after'][stage]['control_rgb_trajectory']])
        if before.shape==after.shape:
            ratios=after/np.maximum(before,1e-6)
            r['control_rgb_ratio_mean']=ratios.mean(0).tolist()
            r['control_rgb_ratio_min']=ratios.min(0).tolist()
            r['control_rgb_ratio_max']=ratios.max(0).tolist()

for name,roi in regions.items():
    baseline=Path(args.mask_baseline).resolve() if args.mask_baseline else roots['baseline'];smasks=[]
    for v in variants:
        stage=v+'_static';ff=frames(baseline,stage);smasks.append(edge_mask(series(baseline,stage,ff,'shadow',roi).mean(0)))
    ff=frames(baseline,'tent_static');valid=np.all(series(baseline,'tent_static',ff,'debug5',roi)>=0,axis=0)
    mask=(smasks[0]|smasks[1])&valid
    out['static'][name]={'common_edge_pixels':int(mask.sum()),'runs':{}}
    out['camera_post'][name]={'common_edge_pixels':int(mask.sum()),'runs':{}}
    for run,root in roots.items():
        static={};camera={}
        for v in variants:
            stage=v+'_static';stage_root=Path(args.static_baseline).resolve() if run=='baseline' and args.static_baseline else root
            ff=frames(stage_root,stage)
            keys=[k for k in ['shadow','source','spatial','output','unsharp'] if available(stage_root,stage,ff,k)]
            static[v]={k:noise(series(stage_root,stage,ff,k,roi),ff,mask) for k in keys}
            static[v]['accepted_fraction']=float((series(stage_root,stage,ff,'accept',roi)[:,mask]>.5).mean())
            if available(stage_root,stage,ff,'accepted_history'):
                flags=np.stack([shading_masks(stage_root,stage,f,roi) for f in ff])
                static[v]['color_rejected_fraction']=float(flags[:,0,mask].mean())
                static[v]['shading_response_fraction']=float(flags[:,1,mask].mean())
            if args.static_only:continue
            stage=v+'_camera';ff=frames(root,stage);camera[v]={}
            for lo,hi in [(64,80),(80,96)]:
                post=[f for f in ff if lo<=f['step']<hi]
                camera[v][f'{lo}..{hi-1}']={k:noise(series(root,stage,post,k,roi),post,mask) for k in ['shadow','source','output']}
                camera[v][f'{lo}..{hi-1}']['accepted_fraction']=float((series(root,stage,post,'accept',roi)[:,mask]>.5).mean())
                flags=np.stack([shading_masks(root,stage,f,roi) for f in post])
                camera[v][f'{lo}..{hi-1}']['color_rejected_fraction']=float(flags[:,0,mask].mean())
                camera[v][f'{lo}..{hi-1}']['shading_response_fraction']=float(flags[:,1,mask].mean())
        out['static'][name]['runs'][run]=static;out['camera_post'][name]['runs'][run]=camera

    if args.static_only:continue
    out['light_step'][name]={}
    for direction,trigger,pre_range,post_range in [('forward',16,(0,16),(64,96)),('reverse',96,(64,96),(144,176))]:
        changed=[];complete=True
        for v in variants:
            stage=v+'_light_step';ff=frames(baseline,stage)
            if len(ff)<post_range[1]:complete=False;break
            pre=[f for f in ff if pre_range[0]<=f['step']<pre_range[1]];post=[f for f in ff if post_range[0]<=f['step']<post_range[1]]
            changed.append(np.abs(series(baseline,stage,pre,'shadow',roi).mean(0)-series(baseline,stage,post,'shadow',roi).mean(0))>.2)
        if not complete:continue
        changed=changed[0]&changed[1];response={'common_changed_pixels':int(changed.sum()),'trigger':trigger,'runs':{}}
        for run,root in roots.items():
            response['runs'][run]={}
            for v in variants:
                stage=v+'_light_step';ff=frames(root,stage)
                keys=[k for k in ['shadow','source','spatial','raw_history','accepted_history','output','unsharp','resurrection'] if available(root,stage,ff,k)]
                a={k:series(root,stage,ff,k,roi) for k in keys};accept=series(root,stage,ff,'accept',roi);motion=series(root,stage,ff,'motion',roi)
                color_flags=np.stack([shading_masks(root,stage,f,roi) for f in ff]) if 'accepted_history' in keys else None
                pre=[i for i,f in enumerate(ff) if pre_range[0]<=f['step']<pre_range[1]];post=[i for i,f in enumerate(ff) if post_range[0]<=f['step']<post_range[1]]
                before={k:refs(a[k],ff,pre) for k in keys};after={k:refs(a[k],ff,post) for k in keys};rows=[]
                for i,f in enumerate(ff):
                    if not trigger<=f['step']<post_range[1]:continue
                    ph=phase(f);r={'step':f['step'],'state':f['state'],'fallback':f['fallback']}
                    for k in keys:
                        d=(before[k][ph]-after[k][ph])[changed];e=(a[k][i]-after[k][ph])[changed];den=float(np.dot(d,d))
                        r[k+'_retention']=float(np.dot(e,d)/den) if den else None
                        r[k+'_normalized_rms']=float(np.sqrt(np.dot(e,e)/den)) if den else None
                    r['accepted_fraction']=float((accept[i][changed]>.5).mean());r['motion_pixels_mean']=float(motion[i][changed].mean())
                    if color_flags is not None:
                        r['color_rejected_fraction']=float(color_flags[i,0][changed].mean())
                        r['shading_response_fraction']=float(color_flags[i,1][changed].mean())
                    rows.append(r)
                active=[r for r in rows if r['state']=='Active'];settle=first_three(active,'output_retention',.1);source_settle=first_three(active,'source_retention',.05)
                response['runs'][run][v]={'first_active_step':active[0]['step'] if active else None,'below10pct_three_frames_first_step':settle,'delay_from_trigger':settle-trigger if settle is not None else None,'source_below5pct_three_frames_first_step':source_settle,'tail_frames_after_source':settle-source_settle if settle is not None and source_settle is not None else None,'first8_active':active[:8],'trajectory':rows}
        out['light_step'][name][direction]=response

target=Path(args.output).resolve() if args.output else list(roots.values())[-1]/'lighting-response-analysis.json'
target.write_text(json.dumps(out,indent=2),encoding='utf-8')
for name,r in out['static'].items():
    for run,vv in r['runs'].items():
        print('STATIC',name,run,{v:{k:x['output'][k] for k in ['same_phase_rms','total_rms','phase_mean_rms']} for v,x in vv.items()})
for name,dd in out['light_step'].items():
    for d,r in dd.items():
        for run,vv in r['runs'].items():print('RESPONSE',name,d,run,{v:x['delay_from_trigger'] for v,x in vv.items()})
print(target)
