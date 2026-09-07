"""Analyze native GPU captures. No Unity interaction; no geometric ground truth."""
from pathlib import Path
import argparse,gzip,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

VARIANTS=['baseline','width010','width005','width002']
WIDTHS=[.2,.1,.05,.02]
LENGTHS={'static':32,'translate':96,'yaw':128}
REGIONS={'roof':(735,190,380,70),'ledge':(715,485,390,80),'arches':(730,575,360,110)}
OX,OY,W,H=680,170,560,650
FONT=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18)

def records(d):
    p=d/'frames.jsonl';return {r['step']:r for r in map(json.loads,p.read_text().splitlines())} if p.exists() else {}
def load(d,s,k):
    a=np.frombuffer(gzip.decompress((d/f'frame_{s:03}_{k}.bin.gz').read_bytes()),
        dtype='<u4' if k in ('counters','pagetable','metadata') else '<f4' if k.startswith('debug') else '<f2')
    if k in ('counters','pagetable','metadata'):return a.copy()
    return a.reshape((270,480,4) if k.startswith('debug') else (H,W) if k=='shadow' else (H,W,4))[::-1].astype(np.float32)
def dist(a):
    a=np.asarray(a);a=a[np.isfinite(a)]
    return dict(zip(['min','median','p95','max','mean'],map(float,[*np.percentile(a,[0,50,95,100]),a.mean()]))) if len(a) else None
def hist(a):
    v,n=np.unique(a.astype(np.int32),return_counts=True);return {str(int(x)):int(y) for x,y in zip(v,n)}
def crop(a,box):
    x,y,w,h=box;return a[y-OY:y-OY+h,x-OX:x-OX+w]
def gridmask(box):
    x,y,w,h=box;yy,xx=np.mgrid[:270,:480];xx=xx*4+2;yy=yy*4+1
    return (xx>=x)&(xx<x+w)&(yy>=y)&(yy<y+h)
def dilate(a):
    b=np.pad(a,1);return b[1:-1,1:-1]|b[:-2,1:-1]|b[2:,1:-1]|b[1:-1,:-2]|b[1:-1,2:]
def luma(a):return a[...,:3]@np.array([.2126,.7152,.0722],np.float32)
def counts(a):return {k:a.count(k) for k in sorted(set(a))}
def rms(a):return float(np.sqrt(np.mean(a*a)))

def analyze(root,out,focused=None):
    out.mkdir(parents=True,exist_ok=True)
    variants=VARIANTS+(['focused020','focused005','repeat020'] if focused else [])
    def directory(v,scenario):return (root if v in VARIANTS or v=='calibration' else focused)/f'{v}_{scenario}'
    result={'capture':str(root),'focused_capture':str(focused) if focused else None,'complete':False,'stages':{},'comparisons':{},'notes':[
        'Coverage width only; LOD-fraction width remains .2. Layouts, PCF and 4096/256 pool unchanged.',
        'Raw ROI at native resolution; full-screen diagnostic is an exact 480x270 native sample grid.',
        'Image difference and temporal RMS measure change/stability, not accuracy. No ray-traced ground truth.',
        'Dynamic raw captures every four steps, not every frame. No claim of eliminating sub-frame/unsampled pops.',
        'GPU timing excluded: capture/readback/compression are intrusive. 7.3 ms is the user-provided reference.']}
    regions={k:gridmask(v) for k,v in REGIONS.items()};regions['full_screen']=np.ones((270,480),bool)
    base=root/'baseline_static';br=records(base)
    if len(br)!=32:return result
    shadow=np.stack([load(base,s,'shadow') for s in range(32)])
    mean=shadow.mean(axis=0);g=np.zeros_like(mean);g[:,:-1]+=abs(np.diff(mean,axis=1));g[:-1]+=abs(np.diff(mean,axis=0))
    edge=dilate(dilate(((mean>.05)&(mean<.95))|(g>.05)))
    masks={k:crop(edge,v) for k,v in REGIONS.items()}
    np.savez_compressed(out/'baseline-edge-masks.npz',**masks)
    temporal={};means={}
    for v in variants:
        for scenario,length in LENGTHS.items():
            d=directory(v,scenario);rec=records(d)
            if set(rec)!=set(range(length)):continue
            c=np.stack([load(d,s,'counters')[:4] for s in sorted(rec)])
            item={'frames':len(rec),'captured':sum(r['capture'] for r in rec.values()),
                'counters':{k:dist(c[:,i]) for i,k in enumerate(['allocated','requested','new','overflow'])},
                'overflow_frames':int((c[:,3]>0).sum()),'states':counts([r['state'] for r in rec.values()]),
                'fallbacks':counts([r['fallback'] for r in rec.values()]),'missing_max':max(r['replayMissingPixels'] for r in rec.values()),
                'replay_error_max':max(r['replayMaxError'] for r in rec.values()),'no_snapshot':[s for s,r in rec.items() if not r['receiverSnapshot']],
                'settings':{k:sorted({r[k] for r in rec.values()}) for k in ['resolution','capacity','firstLevel','screenDensity','targetTexelPixels','resolutionLodBias','pcf','stochasticFiltering','transition','coverageScale','coverageTransition','effectiveAA','tsrQuality','historySampleCount','settingsMatch']}}
            if scenario=='static':
                planes={k:np.stack([load(d,s,k) for s in range(32)]) for k in ['debug0','debug3','debug4','debug5','debug6','debug8']}
                item['regions']={}
                for name,mask in regions.items():
                    lev,fp,work,missing,quality,blend=[planes[k][:,mask,:] for k in ['debug0','debug3','debug4','debug5','debug6','debug8']]
                    valid=(lev[...,1]>=0)&(fp[...,3]>0)
                    coverage_controls=(blend[...,0]>blend[...,1])&(lev[...,0]==lev[...,1])&(lev[...,2]>=0)&valid
                    item['regions'][name]={'samples':int(valid.sum()),'sampled':hist(lev[...,1][valid]),'preferred':hist(lev[...,0][valid]),
                        'minimum_covered':hist(quality[...,1][valid]),'footprint':dist(np.max(fp[...,:2],axis=-1)[valid]),
                        'fallback_fraction':float(np.mean(lev[...,1][valid]>lev[...,0][valid])),
                        'missing_fraction':float(np.mean(missing[...,0][valid]>0)),
                        'coverage_blend':dist(blend[...,0][valid]),'lod_blend':dist(blend[...,1][valid]),
                        'actual_coarse_blend':dist(np.where(lev[...,2]>=0,lev[...,3],0)[valid]),
                        'coverage_controls_fraction':float(coverage_controls.sum()/max(1,valid.sum())),
                        'attempted_taps':dist(work[...,0][valid]),'completed_comparisons':dist(work[...,1][valid])}
                item['temporal']={};temporal[v]={};means[v]={}
                for kind in ['shadow','source','output']:
                    a=np.stack([load(d,s,kind) for s in range(32)])
                    if kind!='shadow':a=luma(a)
                    means[v][kind]=a.mean(axis=0);temporal[v][kind]=a
                    item['temporal'][kind]={}
                    keys=[tuple(rec[s]['jitter'][k] for k in ('x','y')) for s in range(32)]
                    residual=a.copy()
                    for key in set(keys):
                        ids=[i for i,k in enumerate(keys) if k==key];residual[ids]-=a[ids].mean(axis=0)
                    for name,box in REGIONS.items():
                        z=np.stack([crop(t,box) for t in a]);rr=np.stack([crop(t,box) for t in residual]);mask=masks[name]
                        item['temporal'][kind][name]={'total_rms':rms((z-z.mean(axis=0))[:,mask]),'same_phase_rms':rms(rr[:,mask]),'phase_count':len(set(keys))}
            elif v in temporal:
                static_records=records(directory(v,'static'))
                start=64 if scenario=='translate' else 96
                item['post_stop']=[]
                for s in sorted(rec):
                    if s<start or not rec[s]['capture']:continue
                    same=[i for i in range(32) if static_records[i]['jitter']==rec[s]['jitter']]
                    if not same:raise ValueError('No matching static jitter phase')
                    f={'step':s,'frames_after_stop':s-start,
                        'static_pose_match':rec[s]['cameraPosition']==static_records[0]['cameraPosition'] and rec[s]['cameraEuler']==static_records[0]['cameraEuler'],
                        'regions':{k:{} for k in REGIONS}}
                    for kind in ['shadow','source','output']:
                        a=load(d,s,kind)
                        if kind!='shadow':a=luma(a)
                        delta=a-temporal[v][kind][same].mean(axis=0)
                        for name,box in REGIONS.items():
                            e=crop(delta,box)[masks[name]]
                            f['regions'][name][kind]={'mae':float(np.mean(abs(e))),'rms':rms(e)}
                    item['post_stop'].append(f)
            result['stages'][d.name]=item
    for v in variants[1:]:
        reference='focused020' if v=='focused005' else 'baseline'
        comp={'reference':reference}
        for scenario,length in LENGTHS.items():
            b=directory(reference,scenario);d=directory(v,scenario);rb,rc=records(b),records(d)
            if len(rb)!=length or len(rc)!=length:continue
            frames=[]
            for s in sorted(rc):
                r=rc[s]
                if not r['capture'] or not r['receiverSnapshot'] or not rb[s]['receiverSnapshot']:continue
                b0,c0=load(b,s,'debug0'),load(d,s,'debug0');b6,c6=load(b,s,'debug6'),load(d,s,'debug6')
                valid=(b0[...,1]>=0)&(c0[...,1]>=0)
                f={'step':s,'jitter_match':r['jitter']==rb[s]['jitter'],'pose_match':r['cameraPosition']==rb[s]['cameraPosition'] and r['cameraEuler']==rb[s]['cameraEuler'],
                    'preferred_changed':int((valid&(b0[...,0]!=c0[...,0])).sum()),'coverage_changed':int((valid&(b6[...,1]!=c6[...,1])).sum()),
                    'sampled_coarser':int((valid&(c0[...,1]>b0[...,1])).sum()),'sampled_finer':int((valid&(c0[...,1]<b0[...,1])).sum()),
                    'new_unavailable':int(((b0[...,1]>=0)&(c0[...,1]<0)).sum())}
                if (d/f'frame_{s:03}_pagetable.bin.gz').exists():
                    bt,ct=load(b,s,'pagetable'),load(d,s,'pagetable')
                    bm,cm=load(b,s,'metadata').reshape(-1,4),load(d,s,'metadata').reshape(-1,4)
                    bv=(bt>0)&(bm[:,1]==bt)&((bm[:,0]&6)==2)
                    cv=(ct>0)&(cm[:,1]==ct)&((cm[:,0]&6)==2)
                    f['residency']={'different_valid_pages':int((bv!=cv).sum()),'reference_by_level':bv.reshape(-1,1024).sum(axis=1).tolist(),
                        'candidate_by_level':cv.reshape(-1,1024).sum(axis=1).tolist(),
                        'reference_requests_by_level':((bm[:,3]&1)!=0).reshape(-1,1024).sum(axis=1).tolist(),
                        'candidate_requests_by_level':((cm[:,3]&1)!=0).reshape(-1,1024).sum(axis=1).tolist()}
                sb,sc=load(b,s,'shadow'),load(d,s,'shadow')
                ob,oc=luma(load(b,s,'output')),luma(load(d,s,'output'))
                f['regions']={}
                for name,box in REGIONS.items():
                    ds=crop(sc-sb,box);do=crop(oc-ob,box)
                    f['regions'][name]={'shadow_mae':float(np.mean(abs(ds))),'shadow_changed_fraction':float(np.mean(abs(ds)>1/1024)),
                        'output_mae':float(np.mean(abs(do))),'output_max_abs':float(np.max(abs(do)))}
                frames.append(f)
            comp[scenario]={'frames':frames}
        if v in temporal:
            comp['static_edge_differences']={}
            for name,box in REGIONS.items():
                comp['static_edge_differences'][name]={}
                for kind in ['shadow','source','output']:
                    d=np.stack([crop(f,box) for f in temporal[v][kind]-temporal[reference][kind]])[:,masks[name]]
                    comp['static_edge_differences'][name][kind]={'mae':float(np.mean(abs(d))),'rms':rms(d),'max':float(np.max(abs(d)))}
        result['comparisons'][v]=comp
    expected=19 if focused else len(VARIANTS)*len(LENGTHS)-(len(LENGTHS)-1 if 'repeat020' in VARIANTS else 0)
    result['complete']=len(result['stages'])==expected and all((r/'status.txt').exists() and (r/'status.txt').read_text()=='complete' for r in [root]+([focused] if focused else []))
    (out/'summary.json').write_text(json.dumps(result,indent=2))
    if all(v in means for v in VARIANTS):
        # Display native PNG crops and separately the directly captured mean shadow.
        shown=[v for v in VARIANTS if v!='repeat020']
        panel=Image.new('RGB',(W*len(shown),H+40),(18,23,29));draw=ImageDraw.Draw(panel)
        for i,v in enumerate(shown):
            im=Image.open(root/f'{v}_static/last.png').convert('RGB')
            panel.paste(im.crop((OX,OY,OX+W,OY+H)),(i*W,40));draw.text((i*W+8,8),f'{v}: coverage {WIDTHS[i]:.2f} / LOD 0.20',font=FONT,fill='white')
        panel.save(out/'native-comparison.png')
        for name,box in REGIONS.items():
            x,y,w,h=box;panel=Image.new('RGB',(w*4,(h*2+85)*2),(18,23,29));draw=ImageDraw.Draw(panel)
            for i,v in enumerate(shown):
                png=Image.open(root/f'{v}_static/last.png').convert('RGB').crop((x,y,x+w,y+h))
                raw=Image.fromarray(np.round(np.clip(crop(means[v]['shadow'],box),0,1)*255).astype('uint8')).convert('RGB')
                draw.text((i*w+6,5),f'{v} / {WIDTHS[i]:.2f} native',font=FONT,fill='white');panel.paste(png,(i*w,35))
                draw.text((i*w+6,h+42),'raw shadow mean',font=FONT,fill='white');panel.paste(raw,(i*w,h+75))
            # Native rows followed by identical 2x nearest-neighbor magnification of baseline vs narrowest.
            row=panel.crop((0,0,w*4,h*2+85))
            lower=Image.new('RGB',(w*4,h*2+85),(18,23,29))
            for i,v in enumerate(['baseline','width002' if 'width002' in means else 'width005']):
                raw=Image.fromarray(np.round(np.clip(crop(means[v]['shadow'],box),0,1)*255).astype('uint8')).convert('RGB').resize((w*2,h*2),Image.Resampling.NEAREST)
                lower.paste(raw,(i*w*2,40));ImageDraw.Draw(lower).text((i*w*2+8,8),v+' raw shadow / 2x nearest',font=FONT,fill='white')
            panel.paste(lower,(0,h*2+85));panel.save(out/(name+'-comparison.png'))
    if all(v in means for v in ['focused020','focused005']):
        labels=['baseline 0.20','focused 0.20','focused 0.05'];names=['baseline','focused020','focused005']
        panel=Image.new('RGB',(W*3,H+40),(18,23,29));draw=ImageDraw.Draw(panel)
        for i,v in enumerate(names):
            im=Image.open(directory(v,'static')/'last.png').convert('RGB')
            panel.paste(im.crop((OX,OY,OX+W,OY+H)),(i*W,40));draw.text((i*W+8,8),labels[i],font=FONT,fill='white')
        panel.save(out/'focused-native-comparison.png')
        for name,box in REGIONS.items():
            x,y,w,h=box;panel=Image.new('RGB',(w*3,h*2+80),(18,23,29));draw=ImageDraw.Draw(panel)
            for i,v in enumerate(names):
                im=Image.open(directory(v,'static')/'last.png').convert('RGB').crop((x,y,x+w,y+h))
                raw=Image.fromarray(np.round(np.clip(crop(means[v]['shadow'],box),0,1)*255).astype('uint8')).convert('RGB')
                draw.text((i*w+5,5),labels[i]+' final',font=FONT,fill='white');panel.paste(im,(i*w,35))
                draw.text((i*w+5,h+40),'raw shadow mean',font=FONT,fill='white');panel.paste(raw,(i*w,h+75))
            panel.save(out/('focused-'+name+'-comparison.png'))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('capture');p.add_argument('--out',required=True);p.add_argument('--focused');p.add_argument('--controlled',action='store_true');args=p.parse_args()
    if args.controlled:
        VARIANTS=['baseline','width005','focused020','focused005','repeat020'];WIDTHS=[.2,.05,.2,.05,.2];LENGTHS={'static':32,'yaw':128}
    r=analyze(Path(args.capture).resolve(),Path(args.out).resolve(),Path(args.focused).resolve() if args.focused else None)
    print(json.dumps({'complete':r['complete'],'stages':{k:{'requestMax':v['counters']['requested']['max'],'overflowMax':v['counters']['overflow']['max'],'missingMax':v['missing_max']} for k,v in r['stages'].items()}},indent=2))
