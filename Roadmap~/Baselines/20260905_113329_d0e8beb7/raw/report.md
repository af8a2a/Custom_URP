# VSM baseline report

Status: completed | Reason: all_cases_processed
Cases processed: 6/6 | Sampling goals met: 6 | Timing windows comparable: 6

Whole-frame CPU/GPU, GC and GPU stage totals include Editor and all cameras. FrameTiming/GPU results are delayed and not synchronized to the observation frame. Missing/skipped data is unavailable, not zero. PageCull is nested in caster culling; do not sum stage quantiles.

Comparable is a timing check, not a P5 quality certification. Missing metrics remain blank.

## 2K_Hard — completed
Attempt: 0 | Observations: 2089 | Active seconds: 10.003807695578232 | Segments: 1
Reason: 

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 2089/2089 | 4.60039684548974 | 5.3119966760277748 | available |
| cpu_frame_ms | 2089/2089 | 4.6844 | 5.6152 | available |
| gpu_frame_ms | 2087/2089 | 4.562944 | 5.151744 | available |
| cpu_render_thread_ms | 2089/2089 | 1.8655 | 2.4602 | available |
| gc_allocated_in_editor_frame_bytes | 2089/2089 | 14555 | 14959 | available |
| VSM.LayoutRemap_gpu_ms | 2089/2089 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 2089/2089 | 0.73651199999999994 | 0.74316799999999994 | available |
| VSM.InvalidateStatic_gpu_ms | 0/2089 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 2089/2089 | 0.033024 | 0.035328 | available |
| VSM.StaticCasterCull_gpu_ms | 2089/2089 | 0.08524799999999999 | 0.09267199999999999 | available |
| VSM.DynamicCasterCull_gpu_ms | 2089/2089 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 2089/2089 | 0.067071999999999993 | 0.072703999999999991 | available |
| VSM.StaticRaster_gpu_ms | 2089/2089 | 0.007424 | 0.0097279999999999988 | available |
| VSM.DynamicRaster_gpu_ms | 2089/2089 | 0.013056 | 0.015104 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/2089 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 2089/2089 | 0.002304 | 0.0025599999999999998 | available |
| VSM.ResetFeedback_gpu_ms | 0/2089 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 2089/2089 | 1.5897599999999998 | 1.8657279999999998 | available |

## 2K_PCF — completed
Attempt: 0 | Observations: 1911 | Active seconds: 10.002773894557826 | Segments: 1
Reason: 

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1911/1911 | 5.1884991116821766 | 5.9379041194915771 | available |
| cpu_frame_ms | 1911/1911 | 5.1626 | 6.2662 | available |
| gpu_frame_ms | 1908/1911 | 4.784128 | 5.445376 | available |
| cpu_render_thread_ms | 1911/1911 | 2.3717 | 2.8742 | available |
| gc_allocated_in_editor_frame_bytes | 1911/1911 | 14555 | 17551 | available |
| VSM.LayoutRemap_gpu_ms | 1911/1911 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1911/1911 | 0.744448 | 0.756736 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1911 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1911/1911 | 0.03328 | 0.03584 | available |
| VSM.StaticCasterCull_gpu_ms | 1911/1911 | 0.08448 | 0.091648 | available |
| VSM.DynamicCasterCull_gpu_ms | 1911/1911 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1911/1911 | 0.066048 | 0.071168 | available |
| VSM.StaticRaster_gpu_ms | 1911/1911 | 0.007424 | 0.010239999999999999 | available |
| VSM.DynamicRaster_gpu_ms | 1911/1911 | 0.012288 | 0.014848 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1911 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1911/1911 | 0.002304 | 0.0025599999999999998 | available |
| VSM.ResetFeedback_gpu_ms | 0/1911 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1911/1911 | 1.60128 | 2.040832 | available |

## 4K_Hard — completed
Attempt: 0 | Observations: 1424 | Active seconds: 10.005437896825399 | Segments: 1
Reason: 

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1424/1424 | 6.9805486127734184 | 7.5740008614957333 | available |
| cpu_frame_ms | 1424/1424 | 6.9325 | 8.1029 | available |
| gpu_frame_ms | 1423/1424 | 6.934784 | 7.42912 | available |
| cpu_render_thread_ms | 1424/1424 | 2.7672 | 3.2928 | available |
| gc_allocated_in_editor_frame_bytes | 1424/1424 | 14555 | 28208 | available |
| VSM.LayoutRemap_gpu_ms | 1424/1424 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1424/1424 | 3.2350719999999997 | 3.292672 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1424 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1424/1424 | 0.03456 | 0.040704 | available |
| VSM.StaticCasterCull_gpu_ms | 1424/1424 | 0.15872 | 0.166656 | available |
| VSM.DynamicCasterCull_gpu_ms | 1424/1424 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1424/1424 | 0.137984 | 0.144896 | available |
| VSM.StaticRaster_gpu_ms | 1424/1424 | 0.0070399999999999994 | 0.010239999999999999 | available |
| VSM.DynamicRaster_gpu_ms | 1424/1424 | 0.011264 | 0.012032 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1424 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1424/1424 | 0.002304 | 0.002816 | available |
| VSM.ResetFeedback_gpu_ms | 0/1424 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1424/1424 | 1.084416 | 1.372928 | available |

## 4K_PCF — completed
Attempt: 0 | Observations: 1386 | Active seconds: 10.001485600907031 | Segments: 1
Reason: 

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1386/1386 | 7.1553005836904049 | 7.7615007758140564 | available |
| cpu_frame_ms | 1386/1386 | 7.12405 | 8.2027 | available |
| gpu_frame_ms | 1385/1386 | 7.112704 | 7.61856 | available |
| cpu_render_thread_ms | 1386/1386 | 2.567 | 3.0628 | available |
| gc_allocated_in_editor_frame_bytes | 1386/1386 | 14555 | 28940 | available |
| VSM.LayoutRemap_gpu_ms | 1386/1386 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1386/1386 | 3.233536 | 3.2931839999999997 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1386 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1386/1386 | 0.035072 | 0.041215999999999996 | available |
| VSM.StaticCasterCull_gpu_ms | 1386/1386 | 0.16 | 0.167424 | available |
| VSM.DynamicCasterCull_gpu_ms | 1386/1386 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1386/1386 | 0.139008 | 0.145664 | available |
| VSM.StaticRaster_gpu_ms | 1386/1386 | 0.007424 | 0.009984 | available |
| VSM.DynamicRaster_gpu_ms | 1386/1386 | 0.011264 | 0.012288 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1386 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1386/1386 | 0.002304 | 0.002816 | available |
| VSM.ResetFeedback_gpu_ms | 0/1386 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1386/1386 | 1.0944 | 1.389568 | available |

## 8K_Hard — completed
Attempt: 0 | Observations: 500 | Active seconds: 10.02006379676871 | Segments: 1
Reason: 

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 500/500 | 20.044997334480286 | 20.728897303342819 | available |
| cpu_frame_ms | 500/500 | 20.024949999999997 | 21.6342 | available |
| gpu_frame_ms | 500/500 | 19.921792 | 20.6208 | available |
| cpu_render_thread_ms | 500/500 | 2.9161 | 3.9132 | available |
| gc_allocated_in_editor_frame_bytes | 500/500 | 14555 | 100127 | available |
| VSM.LayoutRemap_gpu_ms | 500/500 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 500/500 | 16.210432 | 16.339968 | available |
| VSM.InvalidateStatic_gpu_ms | 0/500 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 500/500 | 0.035711999999999994 | 0.041471999999999995 | available |
| VSM.StaticCasterCull_gpu_ms | 500/500 | 0.35775999999999997 | 0.37504 | available |
| VSM.DynamicCasterCull_gpu_ms | 500/500 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 500/500 | 0.337024 | 0.35353599999999996 | available |
| VSM.StaticRaster_gpu_ms | 500/500 | 0.007424 | 0.010239999999999999 | available |
| VSM.DynamicRaster_gpu_ms | 500/500 | 0.011264 | 0.012544 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/500 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 500/500 | 0.0025599999999999998 | 0.003328 | available |
| VSM.ResetFeedback_gpu_ms | 0/500 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 500/500 | 1.028864 | 1.3642239999999999 | available |

## 8K_PCF — completed
Attempt: 0 | Observations: 505 | Active seconds: 10.011633000283439 | Segments: 1
Reason: 

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 505/505 | 19.855400547385216 | 20.496698096394539 | available |
| cpu_frame_ms | 505/505 | 19.8415 | 21.0241 | available |
| gpu_frame_ms | 505/505 | 19.794944 | 20.24576 | available |
| cpu_render_thread_ms | 505/505 | 2.0338 | 2.6159 | available |
| gc_allocated_in_editor_frame_bytes | 505/505 | 14555 | 112277 | available |
| VSM.LayoutRemap_gpu_ms | 505/505 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 505/505 | 16.116736 | 16.342271999999998 | available |
| VSM.InvalidateStatic_gpu_ms | 0/505 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 505/505 | 0.03456 | 0.040704 | available |
| VSM.StaticCasterCull_gpu_ms | 505/505 | 0.359936 | 0.374784 | available |
| VSM.DynamicCasterCull_gpu_ms | 505/505 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 505/505 | 0.33971199999999996 | 0.354304 | available |
| VSM.StaticRaster_gpu_ms | 505/505 | 0.007936 | 0.010496 | available |
| VSM.DynamicRaster_gpu_ms | 505/505 | 0.011264 | 0.012032 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/505 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 505/505 | 0.0025599999999999998 | 0.002816 | available |
| VSM.ResetFeedback_gpu_ms | 0/505 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 505/505 | 1.032192 | 1.203968 | available |

