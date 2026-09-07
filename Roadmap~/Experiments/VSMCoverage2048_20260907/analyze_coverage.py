"""Analyze the captured 2048 fine-coverage experiment. Does not control Unity."""
from pathlib import Path
import argparse, gzip, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REGIONS={'roof':(735,190,380,70),'ledge':(715,485,390,80)}
VARIANTS=['baseline','half','full']
SCENARIOS={'static':24,'translate':64,'yaw':96}
FONT=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18)

def records(d):
    p=d/'frames.jsonl'
    return {r['step']:r for r in map(json.loads,p.read_text().splitlines())} if p.exists() else {}

def load(d,s,k):
    a=np.frombuffer(gzip.decompress((d/f'frame_{s:03}_{k}.bin.gz').read_bytes()),
        dtype='<u4' if k=='counters' else '<f4' if k.startswith('debug') else '<f2')
    if k=='counters':return a.copy()
    shape=(270,480,4) if k.startswith('debug') else (410,420) if k=='shadow' else (410,420,4)
    return a.reshape(shape)[::-1].astype(np.float32)

def dist(a):
    a=np.asarray(a);a=a[np.isfinite(a)]
    if not len(a):return None
    return dict(zip(['min','median','p95','max','mean'],map(float,[*np.percentile(a,[0,50,95,100]),a.mean()])))

def hist(a):
    v,n=np.unique(a.astype(np.int32),return_counts=True)
    return {str(int(x)):int(y) for x,y in zip(v,n)}

def gridmask(box):
    x,y,w,h=box
    # Native sample is (4*x+2,4*y+2) before flipping the bottom-origin readback.
    yy,xx=np.mgrid[:270,:480];xx=xx*4+2;yy=yy*4+1
    return (xx>=x)&(xx<x+w)&(yy>=y)&(yy<y+h)

def crop(a,r):
    x,y,w,h=REGIONS[r];return a[y-170:y-170+h,x-700:x-700+w]

def dilate(a):
    b=np.pad(a,1);return b[1:-1,1:-1]|b[:-2,1:-1]|b[2:,1:-1]|b[1:-1,:-2]|b[1:-1,2:]

def luma(a):return a[...,:3]@np.array([.2126,.7152,.0722],np.float32)

def main():
    p=argparse.ArgumentParser();p.add_argument('capture');p.add_argument('--out');p.add_argument('--bounded');args=p.parse_args()
    root=Path(args.capture).resolve();out=Path(args.out).resolve() if args.out else root/'analysis'
    bounded=Path(args.bounded).resolve() if args.bounded else None
    variants=VARIANTS+(['bounded'] if bounded else [])
    def directory(v,scenario):return (bounded if v=='bounded' else root)/f'{v}_{scenario}'
    out.mkdir(parents=True,exist_ok=True)
    report={'capture':str(root),'complete':False,'stages':{},'comparisons':{},'limitations':[
        'No geometric or ray-traced ground truth; temporal RMS is stability, not shadow accuracy.',
        'Debug is a 480x270 grid of exact native pixels, not a filtered downsample.',
        'Wall ROIs use native resolution; near-mask uses initial-view calibration depths.',
        '256-page pool and all native TSR/filter settings held constant; readbacks distort frame timing.',
        'Focus depth calibrated once, not an implemented per-frame receiver-focus system.']}
    regions={k:gridmask(v) for k,v in REGIONS.items()}
    calib=records(root/'calibration_static')
    if calib:
        c=calib[0];world=load(root/'calibration_static',0,'debug7')
        pos=np.array([c['cameraPosition'][x] for x in ('x','y','z')]);e=np.deg2rad(c['cameraEuler']['y']);ex=np.deg2rad(c['cameraEuler']['x'])
        forward=np.array([np.sin(e)*np.cos(ex),-np.sin(ex),np.cos(e)*np.cos(ex)])
        depth=(world[...,:3]-pos)@forward
        central=gridmask((768,432,384,216))&(world[...,3]==1)
        median=float(np.median(depth[central]));report['calibration_depth']=median
        regions['initial_near']=(world[...,3]==1)&(depth>.1)&(depth<median*.5)
    regions['full_screen']=np.ones((270,480),bool)
    baseline=root/'baseline_static';br=records(baseline)
    masks={}
    if len(br)==24:
        mean=np.mean([load(baseline,s,'shadow') for s in range(24)],axis=0)
        g=np.zeros_like(mean);g[:,:-1]+=abs(np.diff(mean,axis=1));g[:-1]+=abs(np.diff(mean,axis=0))
        edge=dilate(dilate(((mean>.05)&(mean<.95))|(g>.05)))
        masks={k:crop(edge,k) for k in REGIONS}
        np.savez_compressed(out/'baseline-masks.npz',**masks,**{'grid_'+k:v for k,v in regions.items()})
    for v in variants:
        for scenario,length in SCENARIOS.items():
            d=directory(v,scenario);rec=records(d)
            if set(rec)!=set(range(length)):continue
            counters=np.stack([load(d,s,'counters')[:4] for s in rec])
            item={'frames':len(rec),'captured':sum(r['capture'] for r in rec.values()),
                'counters':{k:dist(counters[:,i]) for i,k in enumerate(['allocated','requested','new','overflow'])},
                'overflow_steps':[int(s) for s,c in zip(rec,counters) if c[3]],
                'states':hist_strings([r['state'] for r in rec.values()]),
                'fallbacks':hist_strings([r['fallback'] for r in rec.values()]),
                'no_snapshot':[s for s,r in rec.items() if not r['receiverSnapshot']],
                'replay_max_error':max(r['replayMaxError'] for r in rec.values()),
                'replay_missing_max':max(r['replayMissingPixels'] for r in rec.values()),
                'settings':{k:sorted({r[k] for r in rec.values()}) for k in ['settingsMatch','resolution','capacity','firstLevel','screenDensity','targetTexelPixels','resolutionLodBias','pcf','stochasticFiltering','transition','effectiveAA','tsrQuality','historySampleCount','focusDistance','focusStrength']}}
            if scenario=='static':
                q=load(d,0,'debug6');lev=load(d,0,'debug0');fp=load(d,0,'debug3')
                item['regions']={}
                for name,mask in regions.items():
                    valid=mask&(lev[...,1]>=0)&(fp[...,3]>0)
                    item['regions'][name]={'pixels':int(valid.sum()),'sampled':hist(lev[...,1][valid]),
                        'minimum_covered':hist(q[...,1][valid]),'desired':dist(q[...,0][valid]),
                        'footprint':dist(np.max(fp[...,:2],axis=-1)[valid]),
                        'transition_level':hist(lev[...,2][valid]),
                        'coarse_blend_weight':dist(np.where(lev[...,2]>=0,lev[...,3],0)[valid]),
                        'primary3_coarse_blend_weight':dist(lev[...,3][valid&(lev[...,1]==3)&(lev[...,2]>=0)])}
                if masks:
                    item['temporal']={}
                    for kind in ['shadow','source','output']:
                        a=np.stack([load(d,s,kind) for s in range(length)])
                        if kind!='shadow':a=luma(a)
                        item['temporal'][kind]={}
                        for name,mask in masks.items():
                            z=np.stack([crop(f,name) for f in a]);z-=z.mean(axis=0)
                            item['temporal'][kind][name]=float(np.sqrt(np.mean(z[:,mask]**2)))
            report['stages'][d.name]=item
    for v in variants[1:]:
        comp={}
        for scenario in SCENARIOS:
            b=root/f'baseline_{scenario}';d=directory(v,scenario);rb=records(b);rc=records(d)
            if len(rb)!=SCENARIOS[scenario] or len(rc)!=len(rb):continue
            results=[]
            for s,r in rc.items():
                if not r['capture'] or not r['receiverSnapshot'] or not rb[s]['receiverSnapshot']:continue
                b0=load(b,s,'debug0');c0=load(d,s,'debug0');b3=load(b,s,'debug3');c3=load(d,s,'debug3')
                valid=(b0[...,1]>=0)&(c0[...,1]>=0)&(b3[...,3]>0)&(c3[...,3]>0)
                delta=c0[...,1]-b0[...,1]
                ratio=np.max(c3[...,:2],axis=-1)/np.maximum(np.max(b3[...,:2],axis=-1),1e-8)
                results.append({'step':s,'jitter_match':r['jitter']==rb[s]['jitter'],
                    'pose_match':r['cameraPosition']==rb[s]['cameraPosition'] and r['cameraEuler']==rb[s]['cameraEuler'],
                    'valid':int(valid.sum()),'finer':int((valid&(delta<0)).sum()),'coarser':int((valid&(delta>0)).sum()),
                    'footprint_ratio':dist(ratio[valid]),
                    'new_unavailable':int(((b0[...,1]>=0)&(c0[...,1]<0)).sum())})
            comp[scenario]=results
        report['comparisons'][v]=comp
    report['bounded_capture']=str(bounded) if bounded else None
    report['complete']=len(report['stages'])==len(variants)*3 and all((r/'status.txt').exists() and (r/'status.txt').read_text()=='complete' for r in [root]+([bounded] if bounded else []))
    (out/'summary.json').write_text(json.dumps(report,indent=2))
    if all(f'{v}_static' in report['stages'] for v in variants):
        panel=Image.new('RGB',(420*len(variants),900),(18,23,29));draw=ImageDraw.Draw(panel)
        for i,v in enumerate(variants):
            d=directory(v,'static');im=Image.open(d/'last.png').convert('RGB')
            draw.text((i*420+8,8),v+' - final frame / native 1:1',font=FONT,fill='white')
            panel.paste(im.crop((700,170,1120,580)),(i*420,35))
            mean=np.mean([load(d,s,'shadow') for s in range(24)],axis=0)
            draw.text((i*420+8,450),'raw shadow - 24 frame mean',font=FONT,fill='white')
            panel.paste(Image.fromarray(np.round(np.clip(mean,0,1)*255).astype('uint8')).convert('RGB'),(i*420,480))
        panel.save(out/'static-comparison.png')
        if bounded:
            pair=Image.new('RGB',(840,900),(18,23,29))
            pair.paste(panel.crop((0,0,420,900)),(0,0))
            pair.paste(panel.crop((1260,0,1680,900)),(420,0))
            pair.save(out/'baseline-bounded.png')
        lev0=load(root/'baseline_static',0,'debug0')[...,1]
        panel=Image.new('RGB',(480*len(variants),335),(18,23,29));draw=ImageDraw.Draw(panel)
        colors=np.array([[85,146,230],[80,209,159],[239,204,78],[242,135,67],[200,64,82],[157,97,208],[120,120,120],[120,120,120],[120,120,120],[120,120,120]],np.uint8)
        for i,v in enumerate(variants):
            level=load(directory(v,'static'),0,'debug0')[...,1];im=colors[np.clip(level.astype(int),0,9)];im[level<0]=0
            panel.paste(Image.fromarray(im),(i*480,35));draw.text((i*480+8,7),v+' - sampled level (same colors)',font=FONT,fill='white')
        for i in range(5):
            draw.rectangle((i*180+8,312,i*180+28,332),fill=tuple(colors[i]));draw.text((i*180+35,308),'Level '+str(i),font=FONT,fill='white')
        panel.save(out/'sampled-levels.png')
    print(json.dumps({'complete':report['complete'],'stages':{k:{'requested_max':v['counters']['requested']['max'],'overflow_max':v['counters']['overflow']['max'],'missing_max':v['replay_missing_max']} for k,v in report['stages'].items()}},indent=2))

def hist_strings(a):return {k:a.count(k) for k in sorted(set(a))}

if __name__=='__main__':main()
