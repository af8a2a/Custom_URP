"""Validate capture completeness and summarize raw receiver diagnostics (no visual pass/fail)."""
import json
import gzip
import math
import statistics
import struct
import sys
from pathlib import Path


def read_channel(folder, prefix, mode):
    path = folder / f"{prefix}_mode{mode}.rgba32f"
    return path.read_bytes() if path.exists() else gzip.decompress(Path(str(path) + ".gz").read_bytes())


def percentile(values, p):
    return sorted(values)[max(0, math.ceil(len(values) * p) - 1)] if values else None


def analyze(folder):
    run = json.loads((folder / "run.json").read_text(encoding="utf-8-sig"))
    poses = run["poses"][:run["renderedFrames"]]
    result = {"status": run["status"], "error": run["error"], "rendered_frames": len(poses),
              "saved_captures": run["savedCaptures"], "skipped_captures": run["skippedCaptures"],
              "all_vsm_active": all(p["vsmActive"] for p in poses),
              "all_settings_match": all(p["settingsMatch"] for p in poses),
              "all_camera_poses_match": all(p["cameraMatches"] for p in poses),
              "trajectory_wall_seconds": poses[-1]["wallSeconds"] - poses[0]["wallSeconds"] if poses else None,
              "captures": []}
    expected_bytes = run["roiWidth"] * run["roiHeight"] * 16
    for capture in run["captures"]:
        if capture["status"] != 2:
            continue
        channels = {}
        for mode in run.get("captureModes", [0, 3, 5]):
            data = read_channel(folder, capture['prefix'], mode)
            assert len(data) == expected_bytes, "Invalid ROI byte count"
            channels[mode] = list(struct.iter_unpack("<ffff", data))
            assert all(math.isfinite(v) for pixel in channels[mode] for v in pixel), "Nonfinite diagnostic"
            if not run.get("roiOnly", False):
                assert (folder / f"{capture['prefix']}_mode{mode}.png").is_file()
        if not run.get("roiOnly", False):
            assert (folder / f"{capture['prefix']}_shadow.png").is_file()
        surface = [i for i, p in enumerate(channels[0]) if p[0] >= 0]
        levels = [channels[0][i] for i in surface]
        footprint = [max(channels[3][i][:2]) for i in surface if channels[3][i][3] > 0]
        availability = [channels[5][i] for i in surface]
        policy = [channels[6][i] for i in surface if channels[6][i][1] >= 0] if 6 in channels else []
        result["captures"].append({"step": capture["step"], "surface_pixels": len(surface),
            "preferred_levels": sorted(set(p[0] for p in levels)),
            "sampled_levels": sorted(set(p[1] for p in levels)),
            "requested_blend_pixels": sum(p[3] > 0 for p in levels),
            "applied_blend_pixels": sum(p[0] == p[1] and p[2] >= 0 and p[3] > 0 for p in levels),
            "fallback_pixels": sum(p[1] > p[0] for p in levels),
            "missing_flag_pixels": sum(p[0] > 0 for p in availability),
            "unmapped_pixels": sum(int(p[0]) & 1 != 0 for p in availability),
            "dirty_pixels": sum(int(p[0]) & 2 != 0 for p in availability),
            "ownership_pixels": sum(int(p[0]) & 4 != 0 for p in availability),
            "out_of_map_pixels": sum(int(p[0]) & 8 != 0 for p in availability),
            "shadow_difference_over_001": sum(p[3] > .01 for p in availability),
            "footprint_median": statistics.median(footprint) if footprint else None,
            "footprint_p95": percentile(footprint, .95),
            "footprint_over_1_pixels": sum(v > 1 for v in footprint),
            "footprint_over_4_pixels": sum(v > 4 for v in footprint),
            "page_counters": capture["pageCounters"],
            "policy_valid_pixels": len(policy),
            "desired_finer_than_level0_pixels": sum(p[0] < 0 for p in policy),
            "coverage_limited_pixels": sum(p[1] > max(0, math.floor(p[0])) for p in policy),
            "selected_coarser_than_desired_pixels": sum(p[2] > max(0, math.floor(p[0])) for p in policy),
            "selected_to_target_ratio_median": statistics.median([p[3] for p in policy if p[3] >= 0]) if any(p[3] >= 0 for p in policy) else None})
    pose_by_step = {p["step"]: p for p in poses}
    dense = [pose_by_step[i]["unityFrame"] for i in range(440, 481) if i in pose_by_step]
    result["dense_consecutive_unity_frames"] = len(dense) == 41 and all(b == a + 1 for a, b in zip(dense, dense[1:]))
    result["dense_saved_steps"] = [c["step"] for c in run["captures"] if 440 <= c["step"] <= 480 and c["status"] == 2]
    return result


if __name__ == "__main__":
    folder = Path(sys.argv[1])
    report = analyze(folder)
    text = json.dumps(report, indent=2)
    (folder / "quality-audit.json").write_text(text + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "captures"}, indent=2))
