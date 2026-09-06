#!/usr/bin/env python3
"""Analyze manifest-indexed VSM/TSR frame captures; no Unity interaction.
Usage: python analyze_vsm_temporal.py manifest.json [--output report.json]
All texture metrics are descriptive; tent is not treated as ground truth.
"""
import argparse, gzip, json
from pathlib import Path
import numpy as np

ALIASES={'shadow':('shadow','raw_shadow'),'source':('source','tsr_source'),'output':('output','tsr_output','final'),'accept':('accept','reject','rejection'),'history':('history','history_meta')}

def numeric(x):
    if isinstance(x,np.generic): return x.item()
    if isinstance(x,np.ndarray): return x.tolist()
    raise TypeError(type(x).__name__)

def stats(x):
    x=np.asarray(x); x=x[np.isfinite(x)]
    if not x.size:return None
    return {'mean':float(x.mean()),'median':float(np.median(x)),'p95':float(np.quantile(x,.95)),'max':float(x.max())}

class Capture:
    def __init__(self,path):
        self.path=Path(path).resolve(); self.root=self.path.parent
        self.m=json.loads(self.path.read_text(encoding='utf-8-sig'))
        self.frames=[f for f in self.m['frames'] if f.get('valid',True)]
        self.regions=self.m.get('regions',{'full':[0,0,self.m['width'],self.m['height']]})
    def plane(self,f,key,rect):
        defs=self.m.get('textures',{}); values=f.get('textures',{})
        actual=next((a for a in ALIASES[key] if a in values),None)
        if actual is None:return None
        value=values[actual]; value={'path':value} if isinstance(value,str) else value
        spec=dict(defs.get(actual,{}));spec.update(value)
        path=self.root/spec['path']; ext=path.suffix.lower()
        if ext in {'.png','.jpg','.jpeg'}:
            from PIL import Image
            a=np.asarray(Image.open(path)).astype(np.float32)/255
            if a.ndim==2:a=a[:,:,None]
        else:
            dtype=np.dtype(spec.get('dtype',self.m.get('dtype','float32')))
            content=gzip.decompress(path.read_bytes()) if ext=='.gz' else path.read_bytes()
            w=int(spec.get('width',self.m['width']));h=int(spec.get('height',self.m['height']))
            ch=int(spec.get('channels',1 if key in {'shadow','accept'} else 2 if key=='history' else 4))
            a=np.frombuffer(content,dtype=dtype).reshape(h,w,ch)
        if spec.get('flip_y',self.m.get('flip_y',False)):a=a[::-1]
        x,y,w,h=rect;a=a[y:y+h,x:x+w]
        if key in {'source','output'} and a.shape[-1]>=3:
            return np.asarray(a[...,:3],np.float32)@np.array([.2126,.7152,.0722],np.float32)
        return np.asarray(a[...,int(spec.get('channel',0))],np.float32).copy()
    def series(self,frames,key,rect):
        values=[self.plane(f,key,rect) for f in frames]
        return np.stack(values) if values and all(v is not None for v in values) else None

def edge_mask(shadow):
    mean=shadow.mean(0); gx=np.abs(np.diff(mean,axis=1,prepend=mean[:,:1])); gy=np.abs(np.diff(mean,axis=0,prepend=mean[:1,:]));mask=(gx+gy>.05)|((mean>.02)&(mean<.98))
    for _ in range(2):
        p=np.pad(mask,1);mask=p[1:-1,1:-1]|p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:]
    return mask

def series_stats(a,mask=None):
    if a is None:return None
    if mask is None:mask=np.ones(a.shape[1:],bool)
    if not mask.any():return {'pixels':0}
    values=a[:,mask]; mean=values.mean(0);std=values.std(0)
    result={'frames':len(a),'pixels':int(mask.sum()),'temporal_std':stats(std),'normalized_temporal_std':stats(std/np.maximum(np.abs(mean),.02)), 'frame_means':values.mean(1).tolist()}
    if len(a)>1:result['adjacent_frame_absolute_change']=stats(np.abs(np.diff(values,axis=0)))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--output');args=p.parse_args();cap=Capture(args.manifest)
    out={'manifest':str(cap.path),'notes':['RejectionMask stores 1=accepted, 0=rejected.','Temporal noise is measured only inside explicitly labeled stationary windows.','Final/source variance ratio is descriptive, not proof of unbiased reconstruction.','Ghost retention is projection onto the pre-to-post lighting change, measured on raw-shadow changed pixels.','Paired variant differences during camera motion are descriptive and are not ghosting ground truth.'],'stationary':{},'light_step':{},'paired_variants':{}}
    combos=sorted({(f['variant'],f['scenario']) for f in cap.frames})
    for variant,scenario in combos:
        frames=sorted([f for f in cap.frames if f['variant']==variant and f['scenario']==scenario],key=lambda f:f['step'])
        stationary_phases=set(cap.m.get('stationary_phases',['pre','post','steady','steady_before','steady_after']))
        if scenario=='static':stationary_phases |= {f.get('phase','steady') for f in frames}
        for phase in sorted(stationary_phases):
            ff=[f for f in frames if f.get('phase','steady')==phase]
            if len(ff)<2:continue
            for name,rect in cap.regions.items():
                shadow=cap.series(ff,'shadow',rect);source=cap.series(ff,'source',rect);output=cap.series(ff,'output',rect)
                edge=edge_mask(shadow) if shadow is not None else None
                result={'steps':[f['step'] for f in ff],'shadow':series_stats(shadow),'source':series_stats(source),'output':series_stats(output)}
                if edge is not None: result['shadow_edges']={k:series_stats(a,edge) for k,a in [('shadow',shadow),('source',source),('output',output)]}
                accept=cap.series(ff,'accept',rect);hist=cap.series(ff,'history',rect)
                if accept is not None:result['accepted_fraction_per_frame']=(accept>.5).mean((1,2)).tolist()
                if hist is not None:result['history_sample_count']=stats(hist)
                out['stationary'][f'{variant}/{scenario}/{phase}/{name}']=result
        if scenario=='light_step':
            pre=[f for f in frames if f.get('phase') in {'pre','steady_before'}];post=[f for f in frames if f.get('phase') in {'post','steady_after'}]
            if not pre or not post:continue
            after=[f for f in frames if f['step']>max(q['step'] for q in pre)]
            for name,rect in cap.regions.items():
                ps=cap.series(pre,'shadow',rect);qs=cap.series(post,'shadow',rect);po=cap.series(pre,'output',rect);qo=cap.series(post,'output',rect)
                if any(v is None for v in [ps,qs,po,qo]):continue
                mask=np.abs(ps.mean(0)-qs.mean(0))>float(cap.m.get('shadow_change_threshold',.2));old=po.mean(0);reference=qo.mean(0);direction=(old-reference)[mask];den=float(np.dot(direction,direction))
                if den<1e-12:continue
                trajectory=[]
                for f in after:
                    value=cap.plane(f,'output',rect);source=cap.plane(f,'source',rect);accept=cap.plane(f,'accept',rect);hist=cap.plane(f,'history',rect)
                    residual=(value-reference)[mask];retention=float(np.dot(residual,direction)/den)
                    row={'step':f['step'],'old_shadow_retention':retention,'residual_rms':float(np.sqrt(np.mean(residual**2)))}
                    if source is not None:row['source_output_luma_mae']=float(np.abs(value-source)[mask].mean())
                    if accept is not None:row['accepted_fraction']=float(np.mean(accept[mask]>.5))
                    if hist is not None:row['history_samples_mean']=float(hist[mask].mean())
                    trajectory.append(row)
                settle=None
                for i in range(len(trajectory)-2):
                    if all(abs(r['old_shadow_retention'])<.1 for r in trajectory[i:i+3]):settle=trajectory[i]['step'];break
                out['light_step'][f'{variant}/{name}']={'changed_pixels':int(mask.sum()),'retention_below_10pct_for_3_captured_frames_step':settle,'trajectory':trajectory}
    variants=sorted({f['variant'] for f in cap.frames})
    if len(variants)>=2:
        left,right=cap.m.get('comparison_variants',variants[:2]);ix={(f['variant'],f['scenario'],f['step']):f for f in cap.frames}
        for scenario in sorted({f['scenario'] for f in cap.frames}):
            common=sorted({f['step'] for f in cap.frames if f['variant']==left and f['scenario']==scenario}&{f['step'] for f in cap.frames if f['variant']==right and f['scenario']==scenario})
            for name,rect in cap.regions.items():
                rows=[]
                for step in common:
                    a=ix[(left,scenario,step)];b=ix[(right,scenario,step)];row={'step':step,'jitter_matches':a.get('jitter')==b.get('jitter')}
                    for key in ['shadow','source','output']:
                        aa=cap.plane(a,key,rect);bb=cap.plane(b,key,rect)
                        if aa is not None and bb is not None:row[key+'_mae']=float(np.mean(np.abs(aa-bb)))
                    rows.append(row)
                out['paired_variants'][f'{scenario}/{name}']={'left':left,'right':right,'frames':rows}
    destination=Path(args.output) if args.output else cap.root/'temporal-analysis.json';destination.write_text(json.dumps(out,indent=2,default=numeric),encoding='utf-8');print(destination)
if __name__=='__main__':main()
