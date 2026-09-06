"""Compare matched quality trajectories; keep regular anchors separate from dense recovery frames."""
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.dont_write_bytecode = True
from analyze_quality import read_channel


def load(folder):
    return (json.loads((folder / "run.json").read_text(encoding="utf-8-sig")),
            json.loads((folder / "quality-audit.json").read_text(encoding="utf-8-sig")))


def compare(reference, folders, output):
    ref_run, ref_audit = load(reference)
    summary = {"reference": reference.name, "scope": "Regular anchors: 31 steps at stride 20. Dense window: 440..480, not over-weighted in anchor summaries.", "runs": []}
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), layout="constrained")
    for folder in [reference] + folders:
        run, audit = load(folder)
        label = "Density off" if not run["settings"]["screenDensity"] else f"Density {run['settings']['targetTexelPixels']:g} px"
        assert run["status"] == "completed" and audit["saved_captures"] == 69
        assert audit["all_vsm_active"] and audit["all_settings_match"] and audit["all_camera_poses_match"]
        assert audit["dense_consecutive_unity_frames"] and audit["dense_saved_steps"] == list(range(440, 481))
        assert run["start"]["camera"] == ref_run["start"]["camera"]
        assert run["start"]["scenes"] == ref_run["start"]["scenes"]
        key = lambda light: (light["scenePath"], light["name"])
        assert sorted(run["start"]["lights"], key=key) == sorted(ref_run["start"]["lights"], key=key)
        assert len(run["poses"]) == len(ref_run["poses"]) == 601
        assert all(all(a[k] == b[k] for k in ("position", "rotation", "gpuViewProjection"))
                   for a, b in zip(run["poses"], ref_run["poses"]))
        assert all(run["settings"][k] == v for k, v in ref_run["settings"].items()
                   if k not in ("name", "screenDensity", "targetTexelPixels"))
        anchors = [c for c in audit["captures"] if c["step"] % 20 == 0]
        dense = [c for c in audit["captures"] if 440 <= c["step"] <= 480]
        pixel_stats = []
        for c in anchors:
            prefix = f"frame_{c['step']:04d}"
            a = np.frombuffer(read_channel(reference, prefix, 3), dtype="<f4").reshape(-1, 4)
            b = np.frombuffer(read_channel(folder, prefix, 3), dtype="<f4").reshape(-1, 4)
            valid = (a[:, 3] > 0) & (b[:, 3] > 0)
            before, after = a[valid, :2].max(axis=1), b[valid, :2].max(axis=1)
            pixel_stats.append({"step": c["step"], "valid_pixels": int(valid.sum()),
                "improved": int((after < before * .999).sum()),
                "degraded": int((after > before * 1.001).sum())})
        total = sum(c["valid_pixels"] for c in pixel_stats)
        item = {"run": folder.name, "label": label, "inputs_match_except_density": True,
            "anchors": len(anchors), "dense_frames": len(dense),
            "overflow_samples": sum(c["page_counters"][3] > 0 for c in audit["captures"]),
            "requested_min_max": [min(c["page_counters"][1] for c in audit["captures"]), max(c["page_counters"][1] for c in audit["captures"])],
            "overflow_min_max": [min(c["page_counters"][3] for c in audit["captures"]), max(c["page_counters"][3] for c in audit["captures"])],
            "anchor_fallback_percent": sum(c["fallback_pixels"] for c in anchors) / sum(c["surface_pixels"] for c in anchors) * 100,
            "anchor_footprint_improved_percent": sum(c["improved"] for c in pixel_stats) / total * 100,
            "anchor_footprint_degraded_percent": sum(c["degraded"] for c in pixel_stats) / total * 100,
            "dense_missing": [{"step": c["step"], "unmapped": c["unmapped_pixels"], "fallback": c["fallback_pixels"], "counters": c["page_counters"]} for c in dense if c["missing_flag_pixels"]],
            "paired_anchor_pixels": pixel_stats}
        summary["runs"].append(item)
        x = [c["step"] for c in anchors]
        axes[0, 0].plot(x, [c["footprint_median"] for c in anchors], label=label)
        axes[0, 1].plot(x, [c["footprint_p95"] for c in anchors], label=label)
        axes[1, 0].plot(x, [c["page_counters"][1] for c in anchors], label=label)
        axes[1, 1].plot([c["step"] for c in dense], [c["fallback_pixels"] for c in dense], label=label)
    axes[1, 0].axhline(256, color="black", linestyle="--", linewidth=1, label="256-page budget")
    titles = ["ROI median footprint (px / texel)", "ROI P95 footprint (px / texel)", "Requested pages (regular anchors)", "Fallback pixels (consecutive frames)"]
    for ax, title in zip(axes.flat, titles):
        ax.set_title(title); ax.set_xlabel("Trajectory step"); ax.grid(alpha=.2); ax.legend(fontsize=8)
    axes[0, 0].set_yscale("log"); axes[0, 1].set_yscale("log"); axes[1, 1].set_yscale("symlog", linthresh=1)
    fig.suptitle("VSM 4K PCF / same Game camera / diagnostic timing excluded")
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "density-comparison.png", dpi=160)
    (output / "comparison.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"runs": [{k: v for k, v in r.items() if k not in ("dense_missing", "paired_anchor_pixels")} for r in summary["runs"]]}, indent=2))


if __name__ == "__main__":
    compare(Path(sys.argv[1]), [Path(p) for p in sys.argv[3:]], Path(sys.argv[2]))
