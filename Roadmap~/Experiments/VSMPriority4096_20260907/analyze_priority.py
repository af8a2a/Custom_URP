from pathlib import Path
import sys,json,gzip,importlib.util
import numpy as np
root=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('transition',root/'Roadmap~/Experiments/VSMTransition4096_20260907/analyze_transition.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
base=Path(sys.argv[1]);cand=Path(sys.argv[2]);out=root/'Roadmap~/Experiments/VSMPriority4096_20260907';out.mkdir(parents=True,exist_ok=True)
summary={'baseline':str(base),'candidate':str(cand),'stages':{},'comparison':{}}
for label,path in [('baseline',base),('candidate',cand)]:
 for scenario in ['static','yaw']:
  d=path/f'{label}_{scenario}';recs=t.records(d)
  item={'frames':len(recs)};summary['stages'][d.name]=item
  if len(recs)!=(32 if scenario=='static' else 128):continue
  c=np.stack([t.load(d,s,'counters') for s in sorted(recs)])
  item.update(counters={k:t.dist(c[:,i]) for i,k in enumerate(['allocated','requested','new','overflow'])},states=t.counts([r['state'] for r in recs.values()]),fallback=t.counts([r['fallback'] for r in recs.values()]),replay_max=max(r['replayMaxError'] for r in recs.values()),settings_match=all(r['settingsMatch'] for r in recs.values()))
  item['frames_data']=[]
  for s,r in sorted(recs.items()):
   if not r['capture']:continue
   m=t.load(d,s,'metadata').reshape(-1,4);table=t.load(d,s,'pagetable');live=(table>0)&(m[:,1]==table)&((m[:,0]&6)==2);flags=m[:,3]
   roles=np.where(flags&256,0,np.where(flags&2048,1,np.where(flags&512,2,np.where(flags&1024,3,4))));requested=(flags&1)!=0
   f={'step':s,'resident_by_level':live.reshape(-1,1024).sum(axis=1).tolist(),'roles':{name:{'requests':int((requested&(roles==i)).sum()),'resident':int((requested&(roles==i)&live).sum())} for i,name in enumerate(['terminal','parent','primary','transition','fallback'])},'regions':{}}
   lev=t.load(d,s,'debug0');fp=t.load(d,s,'debug3');ms=t.load(d,s,'debug5')
   for name,mask in {**{n:t.gridmask(b) for n,b in t.REGIONS.items()},'screen':np.ones((270,480),bool)}.items():
    active=mask&(lev[...,0]>=0);valid=active&(lev[...,1]>=0)
    f['regions'][name]={'sampled':t.hist(lev[...,1][active]),'preferred':t.hist(lev[...,0][active]),'fallback_fraction':float(np.mean(lev[...,1][valid]>lev[...,0][valid])),'footprint':t.dist(np.max(fp[...,:2],axis=-1)[valid]),'terminal_samples':int((active&(lev[...,1]==9)).sum()),'unavailable':int((active&(lev[...,1]<0)).sum()),'missing':int((valid&(ms[...,0]>0)).sum())}
   item['frames_data'].append(f)
for scenario in ['static','yaw']:
 b=base/f'baseline_{scenario}';c=cand/f'candidate_{scenario}';br=t.records(b);cr=t.records(c);frames=[]
 for s,r in sorted(cr.items()):
  if not r['capture']:continue
  bl=t.load(b,s,'debug0');cl=t.load(c,s,'debug0');active=bl[...,0]>=0
  f={'step':s,'pose_jitter_match':all(r[k]==br[s][k] for k in ['cameraPosition','cameraEuler','jitter','lightEuler']),'finer':int((active&(cl[...,1]<bl[...,1])&(cl[...,1]>=0)).sum()),'coarser':int((active&(cl[...,1]>bl[...,1])).sum()),'new_unavailable':int((active&(bl[...,1]>=0)&(cl[...,1]<0)).sum()),'regions':{}}
  bs=t.load(b,s,'shadow');cs=t.load(c,s,'shadow')
  for n,box in t.REGIONS.items():
   delta=t.crop(cs-bs,box);f['regions'][n]={'shadow_mae':float(abs(delta).mean()),'shadow_changed_fraction':float((abs(delta)>1/1024).mean())}
  frames.append(f)
 summary['comparison'][scenario]=frames
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('Report:',out/'summary.json')
for k,v in summary['stages'].items():
 print(k,'frames=',v['frames'],'counters=',v.get('counters'))
 if v.get('frames_data'):
  f=v['frames_data'][0];print('  first resident',f['resident_by_level'],'roles',f['roles']);print('  first regions',f['regions'])
for k,frames in summary['comparison'].items():
 if frames:print(k,'all pose match',all(f['pose_jitter_match'] for f in frames),'finer',t.dist([f['finer'] for f in frames]),'coarser',t.dist([f['coarser'] for f in frames]),'newUnavailable',max(f['new_unavailable'] for f in frames))
