# VSM baseline report

Status: completed_with_warnings | Reason: all_cases_processed
Cases processed: 4/4 | Sampling goals met: 4 | Timing windows comparable: 0
Frame timing source: editor_frames_unattributed | Quality: not_validated

Whole-frame CPU/GPU, GC and GPU stage totals include Editor and all cameras. FrameTiming/GPU results are delayed and not synchronized to the observation frame. Missing/skipped data is unavailable, not zero. PageCull is nested in caster culling; do not sum stage quantiles.

Comparable is a timing check, not a P5 quality certification. Missing metrics remain blank.

## 4K_Hard_FourHz_R1 — completed_with_warnings
Attempt: 0 | Observations: 689 | Active seconds: 15.019158503401343 | Segments: 1
Reason: 
Recorder repaint: FourHz | Observed repaints: 57 | GPU <1 ms (retained): 56 | Median interval (s, 0=unavailable): 0.262273405612234
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 188/188/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.
- Positive GPU timings below 1 ms retained as diagnostics; no numeric filtering applied.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 689/689 | 21.76380343735218 | 24.565298110246658 | available |
| cpu_frame_ms | 689/689 | 21.7821 | 24.8264 | available |
| gpu_frame_ms | 689/689 | 21.549568 | 24.466176 | available |
| cpu_render_thread_ms | 689/689 | 2.2495 | 2.9226 | available |
| gc_allocated_in_editor_frame_bytes | 689/689 | 16805 | 82043 | available |
| VSM.LayoutRemap_gpu_ms | 689/689 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 689/689 | 4.260096 | 4.3750399999999994 | available |
| VSM.InvalidateStatic_gpu_ms | 0/689 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 689/689 | 0.041215999999999996 | 0.71961599999999992 | available |
| VSM.StaticCasterCull_gpu_ms | 689/689 | 0.158976 | 0.1664 | available |
| VSM.DynamicCasterCull_gpu_ms | 689/689 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 689/689 | 0.138752 | 0.144896 | available |
| VSM.StaticRaster_gpu_ms | 689/689 | 0.007424 | 0.009472 | available |
| VSM.DynamicRaster_gpu_ms | 689/689 | 0.010239999999999999 | 0.011519999999999999 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/689 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 689/689 | 0.0048639999999999994 | 0.005888 | available |
| VSM.ResetFeedback_gpu_ms | 0/689 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 689/689 | 6.8485119999999995 | 8.666368 | available |

## 4K_Hard_Manual_R1 — completed_with_warnings
Attempt: 0 | Observations: 685 | Active seconds: 15.004863201530611 | Segments: 1
Reason: 
Recorder repaint: Manual | Observed repaints: 0 | GPU <1 ms (retained): 0 | Median interval (s, 0=unavailable): 0
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 188/188/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 685/685 | 21.940497681498528 | 24.66609887778759 | available |
| cpu_frame_ms | 685/685 | 21.913 | 24.8954 | available |
| gpu_frame_ms | 685/685 | 21.870592 | 24.613632 | available |
| cpu_render_thread_ms | 685/685 | 2.2655 | 2.9761 | available |
| gc_allocated_in_editor_frame_bytes | 685/685 | 16753 | 53587 | available |
| VSM.LayoutRemap_gpu_ms | 685/685 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 685/685 | 4.259328 | 4.373504 | available |
| VSM.InvalidateStatic_gpu_ms | 0/685 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 685/685 | 0.041728 | 0.666624 | available |
| VSM.StaticCasterCull_gpu_ms | 685/685 | 0.15795199999999998 | 0.1664 | available |
| VSM.DynamicCasterCull_gpu_ms | 685/685 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 685/685 | 0.137728 | 0.14438399999999998 | available |
| VSM.StaticRaster_gpu_ms | 685/685 | 0.007424 | 0.009984 | available |
| VSM.DynamicRaster_gpu_ms | 685/685 | 0.009984 | 0.011519999999999999 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/685 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 685/685 | 0.004608 | 0.005888 | available |
| VSM.ResetFeedback_gpu_ms | 0/685 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 685/685 | 6.876672 | 8.69632 | available |

## 4K_Hard_Manual_R2 — completed_with_warnings
Attempt: 0 | Observations: 688 | Active seconds: 15.007760196995463 | Segments: 1
Reason: 
Recorder repaint: Manual | Observed repaints: 0 | GPU <1 ms (retained): 0 | Median interval (s, 0=unavailable): 0
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 188/188/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 688/688 | 21.741651929914951 | 24.541297927498817 | available |
| cpu_frame_ms | 688/688 | 21.790950000000002 | 24.4987 | available |
| gpu_frame_ms | 688/688 | 21.713152 | 24.50688 | available |
| cpu_render_thread_ms | 688/688 | 2.14055 | 2.7081 | available |
| gc_allocated_in_editor_frame_bytes | 688/688 | 16753 | 82043 | available |
| VSM.LayoutRemap_gpu_ms | 688/688 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 688/688 | 4.262912 | 4.374016 | available |
| VSM.InvalidateStatic_gpu_ms | 0/688 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 688/688 | 0.041215999999999996 | 0.683264 | available |
| VSM.StaticCasterCull_gpu_ms | 688/688 | 0.156416 | 0.164608 | available |
| VSM.DynamicCasterCull_gpu_ms | 688/688 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 688/688 | 0.136704 | 0.14310399999999998 | available |
| VSM.StaticRaster_gpu_ms | 688/688 | 0.007424 | 0.009984 | available |
| VSM.DynamicRaster_gpu_ms | 688/688 | 0.011519999999999999 | 0.013056 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/688 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 688/688 | 0.003328 | 0.004096 | available |
| VSM.ResetFeedback_gpu_ms | 0/688 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 688/688 | 6.887936 | 8.675328 | available |

## 4K_Hard_FourHz_R2 — completed_with_warnings
Attempt: 0 | Observations: 696 | Active seconds: 15.006524298469373 | Segments: 1
Reason: 
Recorder repaint: FourHz | Observed repaints: 58 | GPU <1 ms (retained): 60 | Median interval (s, 0=unavailable): 0.25833769841270282
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 188/188/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.
- Positive GPU timings below 1 ms retained as diagnostics; no numeric filtering applied.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 696/696 | 21.493551321327686 | 24.386599659919739 | available |
| cpu_frame_ms | 696/696 | 21.48555 | 24.5048 | available |
| gpu_frame_ms | 696/696 | 21.24864 | 24.249856 | available |
| cpu_render_thread_ms | 696/696 | 2.2108 | 2.7598 | available |
| gc_allocated_in_editor_frame_bytes | 696/696 | 16948 | 86695 | available |
| VSM.LayoutRemap_gpu_ms | 696/696 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 696/696 | 4.260352 | 4.373504 | available |
| VSM.InvalidateStatic_gpu_ms | 0/696 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 696/696 | 0.041215999999999996 | 0.625408 | available |
| VSM.StaticCasterCull_gpu_ms | 696/696 | 0.150528 | 0.157696 | available |
| VSM.DynamicCasterCull_gpu_ms | 696/696 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 696/696 | 0.130304 | 0.135936 | available |
| VSM.StaticRaster_gpu_ms | 696/696 | 0.007424 | 0.009984 | available |
| VSM.DynamicRaster_gpu_ms | 696/696 | 0.011776 | 0.013056 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/696 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 696/696 | 0.003328 | 0.004096 | available |
| VSM.ResetFeedback_gpu_ms | 0/696 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 696/696 | 6.78336 | 8.44416 | available |

