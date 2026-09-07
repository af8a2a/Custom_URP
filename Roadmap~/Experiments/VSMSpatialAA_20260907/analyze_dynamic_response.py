from pathlib import Path
import sys,json,numpy as np
root=Path('E:/VividRP_Reborn/Packages/VividRP')
sys.path.insert(0,str(Path(__file__).resolve().parent))
import analyze_spatial_aa as a
out=root/'Roadmap~/Experiments/VSMSpatialAA_20260907/analysis'
runs={'tent':root/'Temp~/vsm-spatial-aa/20260907_125631_834','area':root/'Temp~/vsm-spatial-aa/20260907_130637_770'}
masks=np.load(out/'common-static-masks.npz')
report={'method':'Luminance RMSE to each variant own settled output at matching jitter phase; fixed common baseline shadow-edge masks. Light changed pixels selected only from old tent settled SOURCE, delta>0.05 scene-linear. Normalized by old tent settled output light-step RMS on that mask. Settling: first 8 consecutive frames below 10%. Captured phases at 16/96 fallback included. Camera stop residual uses last 16 same-pose frames as phase-specific target; no geometric accuracy claim.','regions':{}}
for region in a.REGIONS:
 data={}
 for label,run in runs.items():
  data[label]={}
  for scenario,count in [('light_step',176),('camera',96)]:
   d=run/f'density_{scenario}';rec=a.records(d)
   keys=[(round(rec[s]['jitter']['x'],7),round(rec[s]['jitter']['y'],7)) for s in range(count)]
   output=np.stack([a.luma(a.crop(a.load(d,s,'output'),region)) for s in range(count)])
   source=np.stack([a.luma(a.crop(a.load(d,s,'source'),region)) for s in range(count)]) if scenario=='light_step' else None
   data[label][scenario]=(keys,output,source)
 keys,base,source=data['tent']['light_step']
 mask=masks[region]& (abs(source[64:96].mean(0)-source[144:176].mean(0))>.05)
 amplitude=float(np.sqrt(np.mean((base[64:96].mean(0)[mask]-base[144:176].mean(0)[mask])**2)))
 rr={'changed_mask_pixels':int(mask.sum()),'reference_step_rms':amplitude,'variants':{}}
 for label in runs:
  keys,output,_=data[label]['light_step'];vr={}
  for name,start,last0,last1 in [('forward',16,64,96),('reverse',96,144,176)]:
   target={key:output[[i for i in range(last0,last1) if keys[i]==key]].mean(0) for key in set(keys)}
   curve=[float(np.sqrt(np.mean((output[i][mask]-target[keys[i]][mask])**2)))/amplitude for i in range(start,last1)]
   settle=next((i for i in range(len(curve)-7) if max(curve[i:i+8])<=.1),None)
   vr[name]={'normalized_error_curve':curve,'settle_frames_after_step':settle,'first_frame_error':curve[0]}
  keys,output,_=data[label]['camera'];maskcam=masks[region]
  target={key:output[[i for i in range(80,96) if keys[i]==key]].mean(0) for key in set(keys)}
  curve=[float(np.sqrt(np.mean((output[i][maskcam]-target[keys[i]][maskcam])**2))) for i in range(64,96)]
  vr['camera_stop']={'luminance_rmse_curve':curve,'first8_mean':float(np.mean(curve[:8])),'last8_mean':float(np.mean(curve[-8:]))}
  rr['variants'][label]=vr
 report['regions'][region]=rr
(out/'dynamic-response.json').write_text(json.dumps(report,indent=2))
for region,r in report['regions'].items():
 print(region, 'mask',r['changed_mask_pixels'],{k:{'forward':v['forward']['settle_frames_after_step'],'reverse':v['reverse']['settle_frames_after_step'],'camera_first8':v['camera_stop']['first8_mean']} for k,v in r['variants'].items()},flush=True)
