"""Read captured GPU pixels only. No Unity interaction or geometric ground truth.

Usage: python analyze_spatial_aa.py --baseline CAPTURE [--candidate CAPTURE]
Stages still being captured are skipped. Run again after completion.
"""
from pathlib import Path
import argparse, gzip, hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ORIGIN = (700, 170)
SIZE = (420, 410)
REGIONS = {"roof": (735, 190, 380, 70), "ledge": (715, 485, 390, 80)}
LENGTHS = {"static": 48, "camera": 96, "light_step": 176}
BG, FG, MUTED = (17, 21, 27), (230, 235, 241), (171, 182, 197)
FONTS = {s: ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", s) for s in (13, 15, 18)}


def records(directory):
    p = directory / "frames.jsonl"
    if not p.exists():
        return {}
    return {r["step"]: r for r in (json.loads(t) for t in p.read_text().splitlines() if t.strip())}


def ready(directory, scenario):
    r = records(directory)
    return r if set(r) == set(range(LENGTHS[scenario])) else None


def load(directory, step, kind):
    b = gzip.decompress((directory / f"frame_{step:03d}_{kind}.bin.gz").read_bytes())
    if kind in ("counters", "pre_exposure"):
        return np.frombuffer(b, dtype="<u4" if kind == "counters" else "<f4").copy()
    channels = 1 if kind in ("shadow", "accept", "depth_error") else 4
    dtype = "<f4" if kind.startswith("debug") else "<f2"
    a = np.frombuffer(b, dtype=dtype).reshape(SIZE[1], SIZE[0], channels)[::-1].astype(np.float32)
    return a[..., 0] if channels == 1 else a


def crop(a, region):
    x, y, w, h = REGIONS[region]
    return a[y - ORIGIN[1]:y - ORIGIN[1] + h, x - ORIGIN[0]:x - ORIGIN[0] + w]


def luma(a):
    return a[..., :3] @ np.array([.2126, .7152, .0722], dtype=np.float32)


def display(a):
    rgb = np.maximum(a[..., :3], 0)
    rgb = rgb / (1 + rgb)
    rgb = np.where(rgb <= .0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - .055)
    return np.round(np.clip(rgb, 0, 1) * 255).astype(np.uint8)


def image(a, kind):
    if kind == "shadow":
        return Image.fromarray(np.round(np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGB")
    return Image.fromarray(display(a))


def text(im, xy, value, size=15, color=FG):
    ImageDraw.Draw(im).text(xy, value, font=FONTS[size], fill=color)


def dist(a):
    a = np.asarray(a).reshape(-1)
    a = a[np.isfinite(a)]
    if not len(a):
        return None
    return {k: float(v) for k, v in zip(("min", "p05", "median", "p95", "max", "mean"),
        [*np.percentile(a, [0, 5, 50, 95, 100]), np.mean(a)])}


def histogram(a):
    v, n = np.unique(np.round(a).astype(np.int32), return_counts=True)
    return {str(int(x)): int(y) for x, y in zip(v, n)}


def edge_mask(a):
    dx = np.zeros_like(a); dy = np.zeros_like(a)
    dx[:, :-1] = abs(np.diff(a, axis=1)); dy[:-1] = abs(np.diff(a, axis=0))
    return ((a > .05) & (a < .95)) | (dx + dy > .05)


def dilate_cross(a):
    p = np.pad(a, 1)
    return p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]


def make_masks(baseline, out):
    """Candidate pixels never define the evaluation mask."""
    available = [baseline / f"{v}_static" for v in ("coverage", "density")
                 if ready(baseline / f"{v}_static", "static")]
    if not available:
        return None
    valid = np.ones((SIZE[1], SIZE[0]), bool)
    edges = np.zeros_like(valid)
    means = {}
    for directory in available:
        mean = np.mean([load(directory, s, "shadow") for s in range(48)], axis=0)
        means[directory.name] = mean
        edges |= edge_mask(mean)
        for s in range(48):
            valid &= load(directory, s, "debug5")[..., 0] >= 0
    mask = dilate_cross(dilate_cross(edges)) & valid
    result = {r: crop(mask, r) for r in REGIONS}
    result["full_roi"] = valid
    np.savez_compressed(out / "common-static-masks.npz", **result)
    method = {"baseline_only": [str(p) for p in available],
        "provisional": len(available) != 2,
        "definition": "Union of old-kernel mean shadow in(.05,.95) or forward gradient sum>.05; two cross dilations; intersect valid debug5 over all available baseline static frames. Full ROI mask is validity only.",
        "counts": {k: int(v.sum()) for k, v in result.items()}}
    (out / "common-static-masks.json").write_text(json.dumps(method, indent=2))
    return result, method


def phase_statistics(a, rec, mask):
    keys = [(round(rec[s]["jitter"]["x"], 7), round(rec[s]["jitter"]["y"], 7)) for s in range(len(a))]
    residual = a.copy()
    for key in set(keys):
        ids = [i for i, k in enumerate(keys) if k == key]
        residual[ids] -= a[ids].mean(axis=0)
    total = a - a.mean(axis=0)
    rms = np.sqrt(np.mean(residual ** 2, axis=0))
    y, x = np.unravel_index(np.argmax(np.where(mask, rms, -1)), mask.shape)
    return {"total_temporal_rms": float(np.sqrt(np.mean(total[:, mask] ** 2))),
        "same_jitter_phase_rms": float(np.sqrt(np.mean(residual[:, mask] ** 2))),
        "phase_count": len(set(keys)), "peak_local_xy": [int(x), int(y)],
        "peak_same_phase_rms": float(rms[y, x]), "peak_sequence": a[:, y, x].tolist(),
        "phase_keys": [list(k) for k in keys]}


def analyze_stage(directory, rec, masks):
    scenario = rec[0]["scenario"]
    steps = sorted(rec)
    counters = np.stack([load(directory, s, "counters")[:4] for s in steps])
    exposures = np.array([load(directory, s, "pre_exposure")[0] for s in steps])
    report = {"directory": str(directory), "frames": len(steps),
        "state_counts": {v: sum(r["state"] == v for r in rec.values()) for v in sorted({r["state"] for r in rec.values()})},
        "settings": {k: sorted({r[k] for r in rec.values()}) for k in ("settingsMatch", "resolution", "screenDensity", "pcf", "stochasticFiltering", "effectiveAA", "tsrQuality", "firstLevel", "targetTexelPixels", "resolutionLodBias", "transition")},
        "exposure_buffer_x": dist(exposures),
        "counters": {k: dist(counters[:, i]) for i, k in enumerate(("allocated", "requested", "newly_allocated", "overflow"))},
        "replay_checked_frames": sum(r["replayChecked"] for r in rec.values()),
        "no_receiver_snapshot_steps": [s for s in steps if not rec[s]["receiverSnapshot"]],
        "replayed_frame_max_error": max((r["replayMaxError"] for r in rec.values() if r["replayChecked"]), default=None),
        "replayed_frame_missing_roi_pixels": dist([r["replayMissingPixels"] for r in rec.values() if r["replayChecked"]])}
    debug_steps = sorted(set(range(0, len(steps), 8)) | set(s for s in (1, 2, 3, 4, 5, 6, 7, 15, 16, 17, 63, 64, 95, 96, 97, len(steps) - 1) if s in rec))
    debug_steps = [s for s in debug_steps if rec[s]["receiverSnapshot"]]
    debug = {r: {k: [] for k in ("levels", "footprint", "quality", "missing")} for r in (*REGIONS, "full_roi")}
    for s in debug_steps:
        planes = {k: load(directory, s, k) for k in ("debug0", "debug3", "debug5", "debug6")}
        for region in debug:
            p = planes if region == "full_roi" else {k: crop(v, region) for k, v in planes.items()}
            valid = masks[region] & (p["debug5"][..., 0] >= 0)
            debug[region]["levels"].append(p["debug0"][valid])
            debug[region]["footprint"].append(p["debug3"][valid])
            debug[region]["quality"].append(p["debug6"][valid])
            debug[region]["missing"].append(p["debug5"][..., 0][valid])
    report["debug_sampled_steps"] = debug_steps
    report["debug"] = {}
    for region, arrays in debug.items():
        d = {k: np.concatenate(v) for k, v in arrays.items()}
        levels, fp, quality = d["levels"], d["footprint"], d["quality"]
        sampled = levels[:, 1] >= 0
        valid_fp = fp[:, 3] > .5
        qvalid = quality[:, 1] >= 0 if rec[0]["screenDensity"] else np.zeros(len(quality), bool)
        report["debug"][region] = {"preferred_level_counts": histogram(levels[:, 0]),
            "sampled_level_counts": histogram(levels[:, 1]), "blend": dist(levels[:, 3]),
            "fallback_percent": float(np.mean(sampled & (levels[:, 1] > levels[:, 0])) * 100),
            "no_complete_sample_percent": float(np.mean(~sampled) * 100),
            "worst_axis_footprint_pixels": dist(fp[valid_fp, :2].max(axis=1)),
            "world_texel_size": dist(fp[valid_fp, 2]),
            "desired_lod": dist(quality[qvalid, 0]), "minimum_covered_counts": histogram(quality[qvalid, 1]),
            "preferred_footprint_over_target": dist(quality[qvalid & (quality[:, 3] >= 0), 3]),
            "invalid_quality_footprint_percent": float(np.mean(quality[qvalid, 3] < 0) * 100) if np.any(qvalid) else None,
            "missing_bits_counts": histogram(d["missing"])}
    report["regions"] = {}
    for region in REGIONS:
        series = {k: [] for k in ("shadow", "source", "output", "output_display")}
        for s in steps:
            series["shadow"].append(crop(load(directory, s, "shadow"), region))
            for kind in ("source", "output"):
                a = crop(load(directory, s, kind), region)
                series[kind].append(luma(a))
                if kind == "output":
                    series["output_display"].append(luma(display(a).astype(np.float32)))
        series = {k: np.stack(v) for k, v in series.items()}
        mask = masks[region]
        mean = series["shadow"].mean(axis=0)
        result = {"mask_pixels": int(mask.sum()), "mean_shadow": float(mean[mask].mean()),
            "mean_shadow_partial_20_80_percent": float(np.mean((mean[mask] > .2) & (mean[mask] < .8)) * 100),
            "frame_means": {k: a[:, mask].mean(axis=1).tolist() for k, a in series.items()}}
        if scenario == "static":
            result["temporal"] = {k: phase_statistics(a, rec, mask) for k, a in series.items()}
            result["full_rectangle_temporal"] = {k: phase_statistics(a, rec, np.ones_like(mask)) for k, a in series.items()}
            gy, gx = np.gradient(mean)
            result["mean_shadow_gradient_rms"] = float(np.sqrt(np.mean((gx * gx + gy * gy)[mask])))
            result["center_vertical_profiles"] = {k: a.mean(axis=0)[:, a.shape[2] // 2 - 2:a.shape[2] // 2 + 3].mean(axis=1).tolist() for k, a in series.items()}
            result["center_horizontal_profiles"] = {k: a.mean(axis=0)[a.shape[1] // 2 - 2:a.shape[1] // 2 + 3].mean(axis=0).tolist() for k, a in series.items()}
        report["regions"][region] = result
    return report


def check_alignment(left, right):
    a, b = records(left), records(right)
    mismatches = []
    for s in sorted(set(a) & set(b)):
        for key in ("width", "height", "resolution", "effectiveAA", "tsrQuality", "pcf", "stochasticFiltering", "targetTexelPixels", "resolutionLodBias", "firstLevel", "phase", "lightName", "exposureMode", "autoExposureEnabled", "exposureFixedScale", "depthBias", "slopeBias", "transition"):
            if a[s][key] != b[s][key]:
                mismatches.append([s, key, a[s][key], b[s][key]])
        for key in ("cameraPosition", "cameraEuler", "lightEuler", "jitter"):
            if max(abs(a[s][key][axis] - b[s][key][axis]) for axis in a[s][key]) > .001:
                mismatches.append([s, key, a[s][key], b[s][key]])
    return {"matched_steps": len(set(a) & set(b)), "mismatches": mismatches}


def compare_static(report):
    result = {}
    for label, left, right in (("density_policy", "old_coverage_static", "old_density_static"),
        ("area_kernel_density", "old_density_static", "area_density_static"),
        ("combined", "old_coverage_static", "area_density_static")):
        if left not in report["stages"] or right not in report["stages"]:
            continue
        a, b = report["stages"][left], report["stages"][right]
        comparison = {"left": left, "right": right,
            "pre_exposure_ratio": b["exposure_buffer_x"]["median"] / a["exposure_buffer_x"]["median"],
            "allocated_pages": [a["counters"]["allocated"]["median"], b["counters"]["allocated"]["median"]],
            "regions": {}}
        for region in REGIONS:
            r = {"median_footprint": [p["debug"][region]["worst_axis_footprint_pixels"]["median"] for p in (a, b)]}
            for kind in ("shadow", "source", "output", "output_display"):
                r[kind] = {}
                for metric in ("total_temporal_rms", "same_jitter_phase_rms"):
                    v = [p["regions"][region]["temporal"][kind][metric] for p in (a, b)]
                    r[kind][metric] = {"before_after": v, "relative_change_pct": (v[1] / v[0] - 1) * 100 if v[0] > 1e-7 else None}
            comparison["regions"][region] = r
        result[label] = comparison
    return result


def montage(columns, scenario, step, out, mean=False):
    tilew, gap, left = 398, 10, 10
    width = left + len(columns) * (tilew + gap)
    im = Image.new("RGB", (width, 704), BG)
    label = "48-frame static mean" if mean else f"{scenario} captured step {step:03d}"
    title = f"VSM spatial filtering | 2048 + NativeAA | {label}" if len(columns) > 1 else f"VSM2048 | NativeAA | {label}"
    subtitle = "Native 1:1 crops. Fixed HDR mapping c/(1+c), then sRGB; shadow is linear grayscale." if len(columns) > 1 else "Native 1:1; HDR c/(1+c) + sRGB; shadow linear."
    text(im, (10, 8), title, 18 if len(columns) > 1 else 15)
    text(im, (10, 34), subtitle, 13, MUTED)
    for col, (name, directory) in enumerate(columns):
        text(im, (left + col * (tilew + gap), 57), name, 15)
    top = 83
    allplanes = []
    for _, directory in columns:
        allplanes.append({k: np.mean([load(directory, s, k) for s in range(48)], axis=0) if mean else load(directory, step, k)
                          for k in ("shadow", "source", "output")})
    for region in REGIONS:
        for kind in ("shadow", "source", "output"):
            text(im, (10, top), f"{region.capitalize()} | {kind if kind != 'output' else 'TSR output'}", 13)
            for col, planes in enumerate(allplanes):
                im.paste(image(crop(planes[kind], region), kind), (left + col * (tilew + gap), top + 19))
            top += REGIONS[region][3] + 25
    footnote = "No geometric ground truth: softness, thin-shadow contrast and phase variation are tradeoffs, not an accuracy score." if len(columns) > 2 else "Captured pixels only; softer or steadier does not establish accuracy."
    text(im, (10, top + 3), footnote, 13, MUTED)
    path = out / f"native_{scenario}_{'mean48' if mean else f'{step:03d}'}.png"
    im.save(path, optimize=True)
    return str(path)


def profile_plot(report, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    selected = [(k, label) for k, label in (("old_coverage_static", "Old tent / coverage"),
        ("old_density_static", "Old tent / density"), ("area_density_static", "Area / density"))
        if k in report["stages"]]
    if not selected:
        return None
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.2), constrained_layout=True)
    for row, region in enumerate(REGIONS):
        for col, kind in enumerate(("shadow", "output")):
            ax = axes[row, col]
            for key, label in selected:
                values = report["stages"][key]["regions"][region]["center_vertical_profiles"][kind]
                ax.plot(np.arange(len(values)) + REGIONS[region][1], values, label=label, linewidth=1.2)
            ax.set_title(f"{region}: {'raw shadow' if kind == 'shadow' else 'TSR scene-linear luma'}")
            ax.set_xlabel("Native screen Y, top-left origin")
            ax.set_ylabel("Visibility" if kind == "shadow" else "Captured luma")
            ax.grid(alpha=.2)
            if kind == "shadow":
                ax.set_ylim(-.02, 1.02)
            ax.legend(fontsize=8)
    fig.suptitle("Centered 5-pixel strips, 48-frame static mean; shared axes, no exposure normalization\nCaptured edge profiles, not geometric ground truth", fontsize=11)
    path = out / "static_centered_edge_profiles.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return str(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--mode", choices=("all", "stats", "visuals"), default="all")
    ap.add_argument("--scenarios", nargs="+", choices=tuple(LENGTHS), default=list(LENGTHS))
    args = ap.parse_args()
    out = args.output or (args.candidate or args.baseline) / "spatial-analysis"
    out.mkdir(parents=True, exist_ok=True)
    mask_result = make_masks(args.baseline, out)
    if not mask_result:
        print("No complete baseline static stage yet; retry after capture advances.", flush=True)
        return
    masks, mask_method = mask_result
    roots = {"old": args.baseline}
    if args.candidate:
        roots["area"] = args.candidate
    report = {"method": {"roi": [*ORIGIN, *SIZE], "regions": REGIONS,
        "common_mask": mask_method, "temporal": "RMS about temporal mean; same-phase RMS removes mean for each exact recorded jitter phase. No exposure normalization.",
        "dynamic_masks": "Fixed screen ROI and baseline static mask, not tracked world surfaces.",
        "profiles": "Five-pixel-wide centered vertical/horizontal strips of 48-frame means, captured output not geometric truth.",
        "limits": "Gradient/partial coverage decrease can be blur or lost detail. Debug distributions sample listed frames; counters, exposure and metadata cover every saved frame. No runtime performance measurements."}, "stages": {}, "alignment": {}}
    for run, root in roots.items():
        for variant in ("coverage", "density"):
            for scenario in args.scenarios:
                directory = root / f"{variant}_{scenario}"
                rec = ready(directory, scenario)
                if rec and args.mode != "visuals":
                    key = f"{run}_{variant}_{scenario}"
                    print("Analyzing", key, flush=True)
                    report["stages"][key] = analyze_stage(directory, rec, masks)
                    (out / "spatial-metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["visuals"] = []
    report["static_comparisons"] = compare_static(report)
    if args.mode != "visuals":
        plot = profile_plot(report, out)
        if plot:
            report["visuals"].append(plot)
    for scenario in args.scenarios:
        columns = [("Old tent | coverage", args.baseline / f"coverage_{scenario}"),
                   ("Old tent | density", args.baseline / f"density_{scenario}")]
        if args.candidate:
            columns.append(("Area 9-tap | density", args.candidate / f"density_{scenario}"))
        columns = [(name, d) for name, d in columns if ready(d, scenario)]
        if not columns:
            continue
        for name, d in columns[1:]:
            report["alignment"][scenario + "_" + name] = check_alignment(columns[0][1], d)
        if args.mode != "stats":
            steps = (0, 7, 47) if scenario == "static" else (0, 31, 63, 95) if scenario == "camera" else (15, 17, 21, 64, 97, 101, 144)
            for step in steps:
                report["visuals"].append(montage(columns, scenario, step, out))
            if scenario == "static":
                report["visuals"].append(montage(columns, scenario, 0, out, mean=True))
    report["artifacts_sha256"] = {Path(p).name: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in report["visuals"]}
    name = "visualization-method.json" if args.mode == "visuals" else "spatial-metrics.json"
    (out / name).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(out / name, flush=True)


if __name__ == "__main__":
    main()
