# VSM baseline report

Status: completed_with_warnings | Reason: all_cases_processed
Cases processed: 9/9 | Sampling goals met: 9 | Timing windows comparable: 0
Frame timing source: editor_frames_unattributed | Quality: not_validated

Whole-frame CPU/GPU, GC and GPU stage totals include Editor and all cameras. FrameTiming/GPU results are delayed and not synchronized to the observation frame. Missing/skipped data is unavailable, not zero. PageCull is nested in caster culling; do not sum stage quantiles.

Comparable is a timing check, not a P5 quality certification. Missing metrics remain blank.

## 4K_Hard_FourHz_R1 — completed_with_warnings
Attempt: 0 | Observations: 1256 | Active seconds: 10.006244600340153 | Segments: 1
Reason: Frame Timing Stats is enabled but no fresh GPU timing has arrived, or the API does not provide it.
Recorder repaint: FourHz | Observed repaints: 41 | GPU <1 ms (retained): 41 | Median interval (s, 0=unavailable): 0.25243830073694085
Timing coverage passed: False | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 187/187/0/0
- Frame intervals over 100 ms retained; investigate before comparing.
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.
- Positive GPU timings below 1 ms retained as diagnostics; no numeric filtering applied.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1256/1256 | 7.67499627545476 | 8.3757014945149422 | available |
| cpu_frame_ms | 1256/1256 | 7.6903500000000005 | 8.6711 | available |
| gpu_frame_ms | 1254/1256 | 7.6418560000000006 | 8.254976 | available |
| cpu_render_thread_ms | 1256/1256 | 1.8385 | 2.4843 | available |
| gc_allocated_in_editor_frame_bytes | 1256/1256 | 16387 | 44936 | available |
| VSM.LayoutRemap_gpu_ms | 1256/1256 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1256/1256 | 3.236096 | 3.295232 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1256 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1256/1256 | 0.038911999999999995 | 0.042496 | available |
| VSM.StaticCasterCull_gpu_ms | 1256/1256 | 0.15744 | 0.16819199999999998 | available |
| VSM.DynamicCasterCull_gpu_ms | 1256/1256 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1256/1256 | 0.13747199999999998 | 0.145664 | available |
| VSM.StaticRaster_gpu_ms | 1256/1256 | 0.0076799999999999993 | 0.010752 | available |
| VSM.DynamicRaster_gpu_ms | 1256/1256 | 0.009984 | 0.011519999999999999 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1256 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1256/1256 | 0.004608 | 0.006144 | available |
| VSM.ResetFeedback_gpu_ms | 0/1256 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1256/1256 | 1.9512319999999999 | 2.1675519999999997 | available |

## 4K_Hard_OneHz_R1 — completed_with_warnings
Attempt: 0 | Observations: 1235 | Active seconds: 10.006284998582714 | Segments: 1
Reason: 
Recorder repaint: OneHz | Observed repaints: 32 | GPU <1 ms (retained): 84 | Median interval (s, 0=unavailable): 0.0085508007369412553
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 187/187/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.
- Positive GPU timings below 1 ms retained as diagnostics; no numeric filtering applied.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1235/1235 | 7.9754963517189026 | 8.62179696559906 | available |
| cpu_frame_ms | 1235/1235 | 7.9707 | 8.8673 | available |
| gpu_frame_ms | 1235/1235 | 7.91808 | 8.511744 | available |
| cpu_render_thread_ms | 1235/1235 | 1.8814 | 2.3261 | available |
| gc_allocated_in_editor_frame_bytes | 1235/1235 | 16387 | 44889 | available |
| VSM.LayoutRemap_gpu_ms | 1235/1235 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1235/1235 | 3.23584 | 3.2972799999999998 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1235 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1235/1235 | 0.039168 | 0.043264 | available |
| VSM.StaticCasterCull_gpu_ms | 1235/1235 | 0.15744 | 0.172544 | available |
| VSM.DynamicCasterCull_gpu_ms | 1235/1235 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1235/1235 | 0.13747199999999998 | 0.146944 | available |
| VSM.StaticRaster_gpu_ms | 1235/1235 | 0.0076799999999999993 | 0.010752 | available |
| VSM.DynamicRaster_gpu_ms | 1235/1235 | 0.009984 | 0.011519999999999999 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1235 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1235/1235 | 0.004608 | 0.0076799999999999993 | available |
| VSM.ResetFeedback_gpu_ms | 0/1235 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1235/1235 | 1.9594239999999998 | 2.308864 | available |

## 4K_Hard_Manual_R1 — completed_with_warnings
Attempt: 0 | Observations: 1231 | Active seconds: 10.006508999433095 | Segments: 1
Reason: 
Recorder repaint: Manual | Observed repaints: 0 | GPU <1 ms (retained): 0 | Median interval (s, 0=unavailable): 0
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 187/187/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1231/1231 | 8.0791953951120377 | 8.9439982548356056 | available |
| cpu_frame_ms | 1231/1231 | 8.0818 | 8.9541 | available |
| gpu_frame_ms | 1229/1231 | 8.05632 | 8.903936 | available |
| cpu_render_thread_ms | 1231/1231 | 1.849 | 2.2848 | available |
| gc_allocated_in_editor_frame_bytes | 1231/1231 | 16387 | 33470 | available |
| VSM.LayoutRemap_gpu_ms | 1231/1231 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1231/1231 | 3.237376 | 3.298304 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1231 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1231/1231 | 0.039168 | 0.043519999999999996 | available |
| VSM.StaticCasterCull_gpu_ms | 1231/1231 | 0.157696 | 0.17049599999999998 | available |
| VSM.DynamicCasterCull_gpu_ms | 1231/1231 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1231/1231 | 0.137728 | 0.14668799999999999 | available |
| VSM.StaticRaster_gpu_ms | 1231/1231 | 0.0076799999999999993 | 0.010239999999999999 | available |
| VSM.DynamicRaster_gpu_ms | 1231/1231 | 0.009984 | 0.011264 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1231 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1231/1231 | 0.004608 | 0.00896 | available |
| VSM.ResetFeedback_gpu_ms | 0/1231 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1231/1231 | 1.998848 | 2.4317439999999997 | available |

## 4K_Hard_OneHz_R2 — completed_with_warnings
Attempt: 0 | Observations: 1233 | Active seconds: 10.001859502550985 | Segments: 1
Reason: 
Recorder repaint: OneHz | Observed repaints: 11 | GPU <1 ms (retained): 11 | Median interval (s, 0=unavailable): 1.0026819975907131
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 187/187/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.
- Positive GPU timings below 1 ms retained as diagnostics; no numeric filtering applied.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1233/1233 | 8.0670993775129318 | 8.5468962788581848 | available |
| cpu_frame_ms | 1233/1233 | 8.0566 | 8.7852 | available |
| gpu_frame_ms | 1231/1233 | 8.034048 | 8.4992 | available |
| cpu_render_thread_ms | 1233/1233 | 1.9666 | 2.5245 | available |
| gc_allocated_in_editor_frame_bytes | 1233/1233 | 16387 | 33958 | available |
| VSM.LayoutRemap_gpu_ms | 1233/1233 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1233/1233 | 3.23712 | 3.2967679999999997 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1233 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1233/1233 | 0.039424 | 0.043519999999999996 | available |
| VSM.StaticCasterCull_gpu_ms | 1233/1233 | 0.157184 | 0.169984 | available |
| VSM.DynamicCasterCull_gpu_ms | 1233/1233 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1233/1233 | 0.137216 | 0.146432 | available |
| VSM.StaticRaster_gpu_ms | 1233/1233 | 0.0076799999999999993 | 0.010496 | available |
| VSM.DynamicRaster_gpu_ms | 1233/1233 | 0.009984 | 0.011776 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1233 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1233/1233 | 0.004608 | 0.011776 | available |
| VSM.ResetFeedback_gpu_ms | 0/1233 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1233/1233 | 2.021888 | 2.2986239999999998 | available |

## 4K_Hard_Manual_R2 — completed_with_warnings
Attempt: 0 | Observations: 1253 | Active seconds: 10.004165802154205 | Segments: 1
Reason: 
Recorder repaint: Manual | Observed repaints: 0 | GPU <1 ms (retained): 0 | Median interval (s, 0=unavailable): 0
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 187/187/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1253/1253 | 7.9522039741277695 | 8.4259994328022 | available |
| cpu_frame_ms | 1253/1253 | 7.9509 | 8.6565 | available |
| gpu_frame_ms | 1252/1253 | 7.9330560000000006 | 8.384512 | available |
| cpu_render_thread_ms | 1253/1253 | 1.8667 | 2.2205 | available |
| gc_allocated_in_editor_frame_bytes | 1253/1253 | 16387 | 30967 | available |
| VSM.LayoutRemap_gpu_ms | 1253/1253 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1253/1253 | 3.234816 | 3.2962559999999996 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1253 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1253/1253 | 0.039168 | 0.043519999999999996 | available |
| VSM.StaticCasterCull_gpu_ms | 1253/1253 | 0.157696 | 0.173568 | available |
| VSM.DynamicCasterCull_gpu_ms | 1253/1253 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1253/1253 | 0.13747199999999998 | 0.1472 | available |
| VSM.StaticRaster_gpu_ms | 1253/1253 | 0.0076799999999999993 | 0.010752 | available |
| VSM.DynamicRaster_gpu_ms | 1253/1253 | 0.0097279999999999988 | 0.011007999999999999 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1253 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1253/1253 | 0.0048639999999999994 | 0.012799999999999999 | available |
| VSM.ResetFeedback_gpu_ms | 0/1253 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1253/1253 | 1.9642879999999998 | 2.2515199999999997 | available |

## 4K_Hard_FourHz_R2 — completed_with_warnings
Attempt: 0 | Observations: 1256 | Active seconds: 10.002030293367341 | Segments: 1
Reason: 
Recorder repaint: FourHz | Observed repaints: 41 | GPU <1 ms (retained): 40 | Median interval (s, 0=unavailable): 0.25425940334463348
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 187/187/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.
- Positive GPU timings below 1 ms retained as diagnostics; no numeric filtering applied.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1256/1256 | 7.9452982172369957 | 8.3196992054581642 | available |
| cpu_frame_ms | 1256/1256 | 7.94755 | 8.7175 | available |
| gpu_frame_ms | 1255/1256 | 7.906048 | 8.287232 | available |
| cpu_render_thread_ms | 1256/1256 | 1.8773 | 2.3463 | available |
| gc_allocated_in_editor_frame_bytes | 1256/1256 | 16387 | 45489 | available |
| VSM.LayoutRemap_gpu_ms | 1256/1256 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1256/1256 | 3.235584 | 3.296 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1256 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1256/1256 | 0.039168 | 0.043008 | available |
| VSM.StaticCasterCull_gpu_ms | 1256/1256 | 0.157696 | 0.174848 | available |
| VSM.DynamicCasterCull_gpu_ms | 1256/1256 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1256/1256 | 0.13747199999999998 | 0.1472 | available |
| VSM.StaticRaster_gpu_ms | 1256/1256 | 0.0076799999999999993 | 0.011007999999999999 | available |
| VSM.DynamicRaster_gpu_ms | 1256/1256 | 0.009984 | 0.011264 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1256 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1256/1256 | 0.004608 | 0.013568 | available |
| VSM.ResetFeedback_gpu_ms | 0/1256 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1256/1256 | 1.952 | 2.275584 | available |

## 4K_Hard_Manual_R3 — completed_with_warnings
Attempt: 0 | Observations: 1249 | Active seconds: 10.001774603174567 | Segments: 1
Reason: 
Recorder repaint: Manual | Observed repaints: 0 | GPU <1 ms (retained): 0 | Median interval (s, 0=unavailable): 0
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 187/187/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1249/1249 | 7.9766018316149712 | 8.5044996812939644 | available |
| cpu_frame_ms | 1249/1249 | 7.9739 | 8.6962 | available |
| gpu_frame_ms | 1249/1249 | 7.954432 | 8.475648 | available |
| cpu_render_thread_ms | 1249/1249 | 1.8507 | 2.2172 | available |
| gc_allocated_in_editor_frame_bytes | 1249/1249 | 16387 | 31119 | available |
| VSM.LayoutRemap_gpu_ms | 1249/1249 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1249/1249 | 3.2363519999999997 | 3.2962559999999996 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1249 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1249/1249 | 0.039424 | 0.043264 | available |
| VSM.StaticCasterCull_gpu_ms | 1249/1249 | 0.15692799999999998 | 0.171264 | available |
| VSM.DynamicCasterCull_gpu_ms | 1249/1249 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1249/1249 | 0.13696 | 0.145664 | available |
| VSM.StaticRaster_gpu_ms | 1249/1249 | 0.0076799999999999993 | 0.010752 | available |
| VSM.DynamicRaster_gpu_ms | 1249/1249 | 0.0097279999999999988 | 0.011007999999999999 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1249 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1249/1249 | 0.004608 | 0.011007999999999999 | available |
| VSM.ResetFeedback_gpu_ms | 0/1249 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1249/1249 | 2.016 | 2.2464 | available |

## 4K_Hard_FourHz_R3 — completed_with_warnings
Attempt: 0 | Observations: 1257 | Active seconds: 10.00633090277779 | Segments: 1
Reason: 
Recorder repaint: FourHz | Observed repaints: 41 | GPU <1 ms (retained): 41 | Median interval (s, 0=unavailable): 0.25488884991494842
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 187/187/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.
- Positive GPU timings below 1 ms retained as diagnostics; no numeric filtering applied.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1257/1257 | 7.9522039741277695 | 8.331802673637867 | available |
| cpu_frame_ms | 1257/1257 | 7.9476 | 8.6221 | available |
| gpu_frame_ms | 1257/1257 | 7.920384 | 8.276224 | available |
| cpu_render_thread_ms | 1257/1257 | 1.8488 | 2.3391 | available |
| gc_allocated_in_editor_frame_bytes | 1257/1257 | 16387 | 45049 | available |
| VSM.LayoutRemap_gpu_ms | 1257/1257 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1257/1257 | 3.23584 | 3.297024 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1257 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1257/1257 | 0.039424 | 0.044288 | available |
| VSM.StaticCasterCull_gpu_ms | 1257/1257 | 0.157184 | 0.169216 | available |
| VSM.DynamicCasterCull_gpu_ms | 1257/1257 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1257/1257 | 0.137216 | 0.146176 | available |
| VSM.StaticRaster_gpu_ms | 1257/1257 | 0.0076799999999999993 | 0.010239999999999999 | available |
| VSM.DynamicRaster_gpu_ms | 1257/1257 | 0.0097279999999999988 | 0.011007999999999999 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1257 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1257/1257 | 0.004608 | 0.011776 | available |
| VSM.ResetFeedback_gpu_ms | 0/1257 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1257/1257 | 1.9491839999999998 | 2.28992 | available |

## 4K_Hard_OneHz_R3 — completed_with_warnings
Attempt: 0 | Observations: 1238 | Active seconds: 10.007837400793619 | Segments: 1
Reason: 
Recorder repaint: OneHz | Observed repaints: 11 | GPU <1 ms (retained): 37 | Median interval (s, 0=unavailable): 0.008579499716574901
Timing coverage passed: True | Source: editor_frames_unattributed | Quality: not_validated
Residency: no_overflow_at_last_frame | Last-frame resident/requested/new/overflow: 187/187/0/0
- Whole-frame timing source is not attributed to the selected camera; coverage alone cannot certify comparability.
- Positive GPU timings below 1 ms retained as diagnostics; no numeric filtering applied.

| Metric | Valid / observations | Median | P95 | Availability |
| --- | --- | --- | --- | --- |
| frame_interval_ms | 1238/1238 | 7.9826000146567822 | 8.5952943190932274 | available |
| cpu_frame_ms | 1238/1238 | 7.978 | 8.7241 | available |
| gpu_frame_ms | 1236/1238 | 7.947904 | 8.476928 | available |
| cpu_render_thread_ms | 1238/1238 | 1.84835 | 2.1442 | available |
| gc_allocated_in_editor_frame_bytes | 1238/1238 | 16387 | 33958 | available |
| VSM.LayoutRemap_gpu_ms | 1238/1238 | 0.001024 | 0.0012799999999999999 | available |
| VSM.Allocate_gpu_ms | 1238/1238 | 3.2368639999999997 | 3.297024 | available |
| VSM.InvalidateStatic_gpu_ms | 0/1238 |  |  | no_samples_or_not_executed |
| VSM.ClearPhysicalPages_gpu_ms | 1238/1238 | 0.03968 | 0.044031999999999995 | available |
| VSM.StaticCasterCull_gpu_ms | 1238/1238 | 0.15692799999999998 | 0.16896 | available |
| VSM.DynamicCasterCull_gpu_ms | 1238/1238 | 0 | 0.000256 | available |
| VSM.PageCull_gpu_ms | 1238/1238 | 0.13696 | 0.145152 | available |
| VSM.StaticRaster_gpu_ms | 1238/1238 | 0.0076799999999999993 | 0.010239999999999999 | available |
| VSM.DynamicRaster_gpu_ms | 1238/1238 | 0.009984 | 0.011264 | available |
| VSM.UnityCompatibilityRaster_gpu_ms | 0/1238 |  |  | no_samples_or_not_executed |
| VSM.FinalizePages_gpu_ms | 1238/1238 | 0.004608 | 0.006144 | available |
| VSM.ResetFeedback_gpu_ms | 0/1238 |  |  | no_samples_or_not_executed |
| VSM.ResolveAndFeedback_gpu_ms | 1238/1238 | 2.015872 | 2.327552 | available |

