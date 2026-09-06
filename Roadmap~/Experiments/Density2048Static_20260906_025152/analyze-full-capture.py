import json
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parent
variants=['coverage','density1','density05','coverage-repeat']
regions={'full':(0,0,1920,1080),'roof':(735,190,1115,260),'ledge':(715,485,1105,565)}
arr={v:{m:np.fromfile(root/v/f'mode{m}.bin',np.float32).reshape(1080,1920,4)[::-1] for m in [0,3,5,6]} for v in variants}
def qs(x):
    x=x[np.isfinite(x)]
    return {k:float(t) for k,t in zip(['min','p10','median','p90','p95','p99','max'],np.quantile(x,[0,.1,.5,.9,.95,.99,1]))} if len(x) else None
def hist(x):
    a,b=np.unique(x,return_counts=True)
    return {str(float(k)):int(n) for k,n in zip(a,b)}
def ratio(mask,base):
    n=int(base.sum()); hit=int((mask&base).sum())
    return {'count':hit,'total':n,'percent':100*hit/n if n else None}
out={'method':{'shape':[1080,1920,4],'flipY':True,'rois':regions,'footprint':'max(projected local x-axis length, projected local y-axis length), actual sampled layer; not every-direction singular value nor transition mixture','targetUnit':'screen pixels per virtual texel','coverageLimited':'mode6.selected > floor(clamp(desiredLOD,0,9)); separate minimumCovered > desired as strong proof','reference':'same-run coverage, coverage-repeat control'},'variants':{},'comparisons':{}}
for v in variants:
    data={'counters':dict(zip(['allocated','requested','newlyAllocated','overflow'],[int(x) for x in np.fromfile(root/v/'counters.bin',np.uint32)])),'regions':{}}
    for roi,(x0,y0,x1,y1) in regions.items():
        a,b,c,d=[arr[v][m][y0:y1,x0:x1].reshape(-1,4) for m in [0,3,5,6]]
        geo=a[:,0]>=0; actual=a[:,1]>=0; valid=actual&(b[:,3]>0); quality=(d[:,2]>=0)&(d[:,3]>=0)
        fp=np.maximum(b[:,0],b[:,1]); desired=np.floor(np.clip(d[:,0],0,9)); target=.5 if v=='density05' else 1.
        base={'pixels':len(a),'nonSky':int((a[:,0]!=-2).sum()),'selected':int(geo.sum()),'sampled':int(actual.sum()),'preferredLevels':hist(a[geo,0]),'sampledLevels':hist(a[actual,1]),'actualFootprintPixels':qs(fp[valid]),'over1Pixel':ratio(fp>1,valid),'over2Pixels':ratio(fp>2,valid),'fallback':ratio(a[:,1]>a[:,0],actual&geo),'terminalNoSample':ratio(a[:,1]<0,geo),'missingMask':hist(c[geo,0]),'sourceMaxError':float(c[geo,3].max()) if geo.any() else None,'transition':ratio((a[:,2]>=0)&(a[:,3]>0),actual),'blendWeight':qs(a[actual,3])}
        if v.startswith('density'):
            base['quality']={'targetPixels':target,'desiredLOD':qs(d[quality,0]),'minimumCovered':hist(d[quality,1]),'selected':hist(d[quality,2]),'selectedFootprintRatio':qs(d[quality,3]),'selectedTargetSatisfied':ratio(d[:,3]<=1+1e-5,quality),'actualTargetSatisfied':ratio(fp<=target+1e-5,valid),'coverageLimited':ratio(d[:,2]>desired,quality),'minimumCoverageExceedsDesired':ratio(d[:,1]>desired,quality),'finestLevelDensityLimited':ratio((d[:,0]<0)&(d[:,2]==0)&(d[:,3]>1+1e-5),quality),'atMinimumCovered':ratio(d[:,2]==d[:,1],quality)}
        data['regions'][roi]=base
    out['variants'][v]=data
for v in variants[1:]:
    comparison={}
    for roi,(x0,y0,x1,y1) in regions.items():
        a0,b0,c0=[arr['coverage'][m][y0:y1,x0:x1].reshape(-1,4) for m in [0,3,5]]
        a,b,c=[arr[v][m][y0:y1,x0:x1].reshape(-1,4) for m in [0,3,5]]
        valid=(a[:,1]>=0)&(a0[:,1]>=0)&(b[:,3]>0)&(b0[:,3]>0)
        fp=np.maximum(b[:,0],b[:,1]); fp0=np.maximum(b0[:,0],b0[:,1]); delta=c[:,1]-c0[:,1]
        comparison[roi]={'actualLevelDelta':hist(a[valid,1]-a0[valid,1]),'footprintRatioVsCoverage':qs(fp[valid]/fp0[valid]),'shadowAbsChange':qs(np.abs(delta[valid])),'shadowPixelsChangedOver1Percent':ratio(np.abs(delta)>.01,valid),'shadowPixelsDarkerOver1Percent':ratio(delta<-.01,valid),'shadowPixelsLighterOver1Percent':ratio(delta>.01,valid)}
    out['comparisons'][v]=comparison
for roi,(x0,y0,x1,y1) in regions.items():
    d1=arr['density1'][6][y0:y1,x0:x1].reshape(-1,4); d05=arr['density05'][6][y0:y1,x0:x1].reshape(-1,4)
    a1=arr['density1'][0][y0:y1,x0:x1].reshape(-1,4); a05=arr['density05'][0][y0:y1,x0:x1].reshape(-1,4)
    q=(d1[:,3]>=0)&(d05[:,3]>=0)
    s1=arr['density1'][5][y0:y1,x0:x1,1].reshape(-1); s05=arr['density05'][5][y0:y1,x0:x1,1].reshape(-1); validShadow=(a1[:,1]>=0)&(a05[:,1]>=0); difference=(s05-s1)[validShadow]
    out.setdefault('density05_vs_density1',{})[roi]={'desiredLODDelta':qs((d05[:,0]-d1[:,0])[q]),'actualLevelDelta':hist((a05[:,1]-a1[:,1])[q]),'shadowMaxAbsDifference':float(np.max(np.abs(difference))),'shadowRmsDifference':float(np.sqrt(np.mean(difference**2)))}
out['observations']=['All variants have zero missing-mask, zero sampled-level fallback and zero allocator overflow; source differences are bounded by 0.0004882216453552246.', 'Roof median projected primary-texel axis footprint halves from 5.3534 to 2.6767 screen pixels; ledge from 5.3896 to 2.6948.', 'At target 1, roof coverage limits 100 percent and ledge 97.83974 percent of valid footprint pixels; at target 0.5 both ROIs are 100 percent coverage limited.', 'The 0.5 target lowers desired LOD by one. Only one full-frame pixel changes its actual sampled layer; both ROIs have identical actual footprints and every pixel of the resolved shadow output is identical to target 1 because minimum coverage is unchanged.', 'Capture metadata reports identical TSR jitter and GPU view-projection in all four variants. See exactControlComparisons for repeatability; raw changed-pixel percentages are still not an aliasing improvement metric.', 'Full-frame high footprint quantiles include grazing receiver planes and geometry discontinuities, not exclusively perceptually relevant shadow boundaries.', 'All reported footprint values describe the actual primary sampled layer. Coarser transition contributions are separately counted and can retain visible coarse-grid structure.']
out['exactControlComparisons']={}
for left,right in [('coverage','coverage-repeat'),('density1','density05')]:
    results={}
    for mode in [0,3,5,6]:
        aa=arr[left][mode]; bb=arr[right][mode]; valid=(arr[left][0][:,:,1]>=0)&(arr[right][0][:,:,1]>=0); difference=bb-aa
        results[str(mode)]={'arrayExactlyEqual':bool(np.array_equal(aa,bb)), 'differingScalarCount':int(np.count_nonzero(difference)), 'maxAbsDifference':float(np.max(np.abs(difference))), 'validChannelsMaxAbsDifference':[float(np.max(np.abs(difference[:,:,i][valid]))) for i in range(4)]}
    out['exactControlComparisons'][left+'__'+right]=results
(root/'analysis-independent.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for v,data in out['variants'].items():
    print(v,data['counters'])
    for roi,r in data['regions'].items():
        print(roi,'footprint',r['actualFootprintPixels'],'fallback',r['fallback']['percent'],'transition',r['transition']['percent'])
        if 'quality' in r:
            q=r['quality'];print('quality',roi,{k:q[k] for k in ['actualTargetSatisfied','coverageLimited','atMinimumCovered']})
for v,r in out['comparisons'].items():
    print('COMPARE',v,{k:{'levels':r[k]['actualLevelDelta'],'footprintRatio':r[k]['footprintRatioVsCoverage'],'changedPercent':r[k]['shadowPixelsChangedOver1Percent']['percent']} for k in regions})
print('DENSITY 05 vs 1',out['density05_vs_density1'])
