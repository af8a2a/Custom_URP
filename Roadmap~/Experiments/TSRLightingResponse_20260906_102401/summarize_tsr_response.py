#!/usr/bin/env python3
"""Reduce the full phase-aware report without recomputing or changing its masks."""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
d = json.loads((root / 'lighting-response-analysis.json').read_text())
summary = {'roots': d['roots'], 'method': d['method'], 'static': {}, 'light_step': {}, 'camera_settled': {}}
summary['pairing'] = d['pairing']
summary['capture_audit'] = {}
for label, stages in d['audit'].items():
    summary['capture_audit'][label] = {}
    for stage, a in stages.items():
        compact = {key: value for key, value in a.items() if key != 'control_rgb_trajectory'}
        exposure = [r['pre_exposure'] for r in a['control_rgb_trajectory'] if 'pre_exposure' in r]
        if exposure:
            compact['pre_exposure_min_max'] = [min(exposure), max(exposure)]
        summary['capture_audit'][label][stage] = compact
for region, rr in d['static'].items():
    out = {'common_edge_pixels': rr['common_edge_pixels'], 'variants': {}}
    for variant in ('tent', 'stochastic9'):
        pair = {label: {key: rr['runs'][label][variant]['output'][key]
                        for key in ('same_phase_rms', 'total_rms', 'phase_mean_rms')}
                for label in rr['runs']}
        if 'after' in pair:
            pair['after_to_baseline'] = {key: pair['after'][key] / pair['baseline'][key]
                                         for key in pair['baseline']}
        pair['history_usage'] = {label: {key: rr['runs'][label][variant].get(key, 0.0)
                                        for key in ('accepted_fraction', 'color_rejected_fraction', 'shading_response_fraction')}
                                 for label in rr['runs']}
        out['variants'][variant] = pair
    summary['static'][region] = out
for region, rr in d['light_step'].items():
    out = {}
    for direction, dr in rr.items():
        result = {'common_changed_pixels': dr['common_changed_pixels'], 'trigger': dr['trigger'], 'runs': {}}
        for label, run in dr['runs'].items():
            result['runs'][label] = {}
            for variant, vr in run.items():
                result['runs'][label][variant] = {key: vr[key] for key in (
                    'first_active_step', 'below10pct_three_frames_first_step', 'delay_from_trigger',
                    'source_below5pct_three_frames_first_step', 'tail_frames_after_source')}
                result['runs'][label][variant]['first_active'] = vr['first8_active'][0]
        out[direction] = result
    summary['light_step'][region] = out
for region, rr in d['camera_post'].items():
    out = {}
    for label, run in rr['runs'].items():
        out[label] = {variant: {key: vr['80..95']['output'][key]
                               for key in ('same_phase_rms', 'total_rms')}
                      for variant, vr in run.items()}
    summary['camera_settled'][region] = out
summary['camera_note'] = 'Only the stationary last 16 frames are summarized; normal changes during camera motion are not labeled noise or ghosting.'
summary['lighting_note'] = 'Delays start at the first of three consecutive Active frames with absolute phase-matched output retention below 10%; source arrival uses 5%. This is a region projection, not a per-pixel or permanent-settle guarantee. The light-change frame has a real VSM fallback and is excluded from this Active-frame threshold.'
path = root / 'lighting-response-summary.json'
path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(path)
print(json.dumps(summary['static'], indent=2))
print(json.dumps(summary['camera_settled'], indent=2))
