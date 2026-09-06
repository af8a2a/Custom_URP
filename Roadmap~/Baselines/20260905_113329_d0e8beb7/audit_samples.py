"""Recompute schema-2 CSV/JSON/Markdown statistics without Unity or third-party packages."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def same_number(actual, expected):
    if expected is None:
        assert actual in (None, ""), (actual, expected)
    else:
        assert math.isclose(float(actual), expected, rel_tol=1e-12, abs_tol=1e-12), (actual, expected)


def lights(snapshot):
    return sorted(snapshot["lights"], key=lambda light: (light["scenePath"], light["name"]))


manifest = read_json(ROOT / "manifest.json")
for file in manifest["raw_files"]:
    content = (ROOT / file["path"]).read_bytes()
    assert len(content) == file["bytes"]
    assert hashlib.sha256(content).hexdigest() == file["sha256"]

run = read_json(RAW / "run.json")
summary = read_csv(RAW / "summary.csv")
assert run["schemaVersion"] == 2
assert len(summary) == 18 * len(run["cases"])
assert len({(row["case_index"], row["metric"]) for row in summary}) == len(summary)
markdown = {}
case_name = None
for line in (RAW / "report.md").read_text(encoding="utf-8-sig").splitlines():
    if line.startswith("## "):
        case_name = line[3:].split(" — ")[0]
    elif line.startswith("| ") and not line.startswith(("| Metric", "| ---")):
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        markdown[(case_name, cells[0])] = cells[1:]
assert len(markdown) == len(summary)

audit = []
for index, expected_case in enumerate(run["results"]):
    case = read_json(RAW / f"case_{index:03}.json")
    assert case == expected_case
    assert case["settings"] == run["cases"][index]
    rows = read_csv(RAW / f"case_{index:03}_samples.csv")
    assert len(rows) == case["observations"] >= run["minSamplesPerCase"]
    local_summary = read_csv(RAW / f"case_{index:03}_summary.csv")
    exported = [row for row in summary if int(row["case_index"]) == index]
    assert local_summary == exported
    fields = list(rows[0])[4:]  # Schema 2 adds segment after the timing timestamp.
    assert fields == [row["metric"] for row in exported]
    frames = [int(row["observation_frame"]) for row in rows]
    times = [float(row["unscaled_time"]) for row in rows]
    segments = [int(row["segment"]) for row in rows]
    timestamps = [int(row["frame_timing_timestamp"]) for row in rows if int(row["frame_timing_timestamp"]) > 0]
    assert frames == sorted(set(frames))
    assert all(b > a for a, b in zip(times, times[1:]))
    assert timestamps == sorted(set(timestamps))
    assert len(set(segments)) == case["segments"] == len(case["segmentStarts"])
    active_seconds = sum(b - a for a, b, sa, sb in zip(times, times[1:], segments, segments[1:]) if sa == sb)
    same_number(case["measuredSeconds"], active_seconds)
    assert active_seconds >= run["measurementSeconds"]
    metrics = {}
    for field, exported_metric, json_metric in zip(fields, exported, case["metrics"]):
        values = sorted(float(row[field]) for row in rows if row[field] and math.isfinite(float(row[field])))
        stats = {"median": statistics.median(values) if values else None,
                 "p95": values[math.ceil(len(values) * .95) - 1] if values else None,
                 "min": values[0] if values else None, "max": values[-1] if values else None}
        assert int(exported_metric["observations"]) == len(rows)
        assert exported_metric["status"] == case["status"]
        assert exported_metric["case_name"] == case["settings"]["name"]
        assert int(exported_metric["valid_samples"]) == json_metric["validSamples"] == len(values)
        assert json_metric["name"] == field
        md_count, md_median, md_p95, md_availability = markdown[(case["settings"]["name"], field)]
        assert md_count == f"{len(values)}/{len(rows)}"
        assert md_availability == json_metric["availability"]
        same_number(md_median, stats["median"])
        same_number(md_p95, stats["p95"])
        for stat, expected in stats.items():
            same_number(exported_metric[stat], expected)
            same_number(json_metric[stat], expected)
        metrics[field] = {"valid_samples": len(values), "coverage_percent": len(values) / len(rows) * 100, **stats}
    required = ["cpu_frame_ms", "gpu_frame_ms"] + ["VSM." + name + "_gpu_ms" for name in
        ("LayoutRemap", "Allocate", "ClearPhysicalPages", "DynamicRaster", "FinalizePages", "ResolveAndFeedback")]
    assert all(metrics[field]["coverage_percent"] >= 95 for field in required)
    assert case["vsmActiveFrames"] == case["selectedCameraFrames"] > 0
    assert not case["settingsMismatchFrames"] and not case["cameraMoved"] and not case["outputSizeChanged"]
    intervals = [float(row["frame_interval_ms"]) for row in rows]
    assert sum(value > 100 for value in intervals) == case["longFramesOver100ms"] == 0
    assert case["samplingGoalMet"] and case["comparable"] and not case["issues"]
    assert case["finalPageCountersAvailable"] and not case["pageCounterError"]
    snapshots = [case["start"], *case["segmentStarts"], case["end"]]
    snapshot_matches = all(snapshot["camera"] == run["initialScene"]["camera"]
        and snapshot["scenes"] == run["initialScene"]["scenes"]
        and lights(snapshot) == lights(run["initialScene"]) for snapshot in snapshots)
    assert snapshot_matches
    block = {"case": case["settings"]["name"], "rows": len(rows), "active_seconds": active_seconds,
        "frame_gaps": sum(b - a - 1 for a, b in zip(frames, frames[1:])),
        "missing_timestamps": len(rows) - len(timestamps), "max_frame_interval_ms": max(intervals),
        "gpu_frame_below_1ms": sum(0 < float(row["gpu_frame_ms"]) < 1 for row in rows if row["gpu_frame_ms"]),
        "camera_scenes_lights_match_all_snapshots": snapshot_matches,
        "final_page_counters": case["finalPageCounters"], "metrics": metrics,
        "assessment": "over-budget timing reference; quality/residency not certified" if case["finalPageCounters"][3] else "single-run timing reference"}
    audit.append(block)
    print(json.dumps({key: value for key, value in block.items() if key != "metrics"}))

events = [json.loads(line) for line in (RAW / "events.jsonl").read_text(encoding="utf-8-sig").splitlines()]
assert [event["action"] for event in events] == ["case_started", "segment_started", "case_finished"] * 6 + ["session_finished"]
for index, case in enumerate(run["results"]):
    finished = events[index * 3 + 2]
    assert finished["caseIndex"] == index and finished["observations"] == case["observations"]
assert run["processedCases"] == run["completedCases"] == run["comparableCases"] == len(audit)
assert run["status"] == "completed" and run["reason"] == events[-1]["reason"] == "all_cases_processed"
assert not run["lastError"]
(ROOT / "sample-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
print(f"PASS: {sum(case['rows'] for case in audit)} observations; {len(summary)} metric rows match raw CSV, summaries, JSON and Markdown; {len(events)} lifecycle events consistent.")
