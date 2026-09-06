"""Audit schema-3 timing experiment without filtering or reassigning GPU samples."""
import csv
import json
import statistics
import sys
from pathlib import Path


def median(values):
    return statistics.median(values) if values else None


def analyze(directory):
    run = json.loads((directory / "run.json").read_text(encoding="utf-8-sig"))
    result = {"run": directory.name, "status": run["status"],
              "project": run["projectPath"], "d3d12_debug": run["d3d12DebugStartupFlag"],
              "scope": "Observation metadata is not GPU-frame attribution. All raw samples retained.", "cases": []}
    for index, case in enumerate(run["results"]):
        raw = directory / f"case_{index:03d}_samples.csv"
        if not raw.exists():
            continue
        with raw.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        valid = [r for r in rows if r["gpu_frame_ms"]]
        low = [r for r in valid if 0 < float(r["gpu_frame_ms"]) < 1]
        intervals = [float(b["unscaled_time"]) - float(a["unscaled_time"])
                     for a, b in zip(low, low[1:]) if a["segment"] == b["segment"]]
        result["cases"].append({"case": case["settings"]["name"], "observations": len(rows),
            "coverage_passed": case["timingCoveragePassed"], "seconds": case["measuredSeconds"],
            "gpu_valid": len(valid), "gpu_median_ms": median([float(r["gpu_frame_ms"]) for r in valid]),
            "low_count": len(low), "low_interval_median_s": median(intervals),
            "repaints": case["observedWindowRepaints"], "segments": case["segments"],
            "allocate_median_ms": median([float(r["VSM.Allocate_gpu_ms"]) for r in rows if r["VSM.Allocate_gpu_ms"]]),
            "resolve_median_ms": median([float(r["VSM.ResolveAndFeedback_gpu_ms"]) for r in rows if r["VSM.ResolveAndFeedback_gpu_ms"]])})
    return result


if __name__ == "__main__":
    folder = Path(sys.argv[1])
    report = analyze(folder)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    (folder / "timing-source-audit.json").write_text(text + "\n", encoding="utf-8")
    print(text)
