import csv, json, math, statistics, pathlib
root = pathlib.Path(__file__).resolve().parent/"raw"
summary = list(csv.DictReader((root/"summary.csv").open(encoding="utf-8-sig", newline="")))
report = []
for i in range(4):
    meta = json.loads((root/f"case_{i:03}.json").read_text(encoding="utf-8-sig"))
    rows = list(csv.DictReader((root/f"case_{i:03}_samples.csv").open(encoding="utf-8-sig",newline="")))
    fields = list(rows[0])[3:]
    metrics = {}
    for field in fields:
        vals = [float(row[field]) for row in rows if row[field] and math.isfinite(float(row[field]))]
        vals.sort()
        computed = {"valid_samples":len(vals), "median": statistics.median(vals) if vals else None,
            "p95": vals[math.ceil(.95*len(vals))-1] if vals else None,
            "min":min(vals) if vals else None, "max":max(vals) if vals else None}
        exported = next(r for r in summary if int(r["case_index"]) == i and r["metric"] == field)
        assert len(vals) == int(exported["valid_samples"])
        for stat in ("median","p95","min","max"):
            assert (not exported[stat]) if computed[stat] is None else math.isclose(float(exported[stat]),computed[stat],rel_tol=1e-12,abs_tol=1e-12)
        metrics[field] = computed
    frames = [int(r["observation_frame"]) for r in rows]
    times = [float(r["unscaled_time"]) for r in rows]
    intervals = [float(r["frame_interval_ms"]) for r in rows]
    missing_run = 0; longest_missing = 0
    for r in rows:
        missing_run = missing_run+1 if r["frame_timing_timestamp"] == "0" else 0
        longest_missing = max(longest_missing, missing_run)
    valid_timestamps = [int(r["frame_timing_timestamp"]) for r in rows if r["frame_timing_timestamp"] != "0"]
    assert frames == sorted(set(frames))
    assert all(b > a for a,b in zip(valid_timestamps, valid_timestamps[1:]))
    stages = [f for f in fields if f.startswith("VSM.")]
    # Stage uniqueness cannot establish freshness; repeats are not discarded.
    def longest_repeat(key):
        last = object(); length = longest = 0
        for row in rows:
            value = row[key]
            length = length+1 if value == last else 1
            longest = max(longest,length); last=value
        return longest
    block = {"case":meta["settings"]["name"],"status":meta["status"],"rows":len(rows),
        "sample_time_span_s":times[-1]-times[0], "sum_frame_intervals_s":sum(intervals)*.001,
        "frames_missing_between_observations":sum(b-a-1 for a,b in zip(frames,frames[1:])),
        "longest_missing_frame_timing_run":longest_missing,
        "frame_interval_gt50ms":sum(v>50 for v in intervals),"frame_interval_gt100ms":sum(v>100 for v in intervals),
        "gpu_frame_below_1ms":sum(0<float(r["gpu_frame_ms"])<1 for r in rows if r["gpu_frame_ms"]),
        "scene_snapshots_equal":meta["start"]["scenes"] == meta["end"]["scenes"],
        "lights_equal_start_end":sorted(meta["start"]["lights"],key=lambda l:(l["scenePath"],l["name"])) == sorted(meta["end"]["lights"],key=lambda l:(l["scenePath"],l["name"])),
        "camera_equal_start_end":meta["start"]["camera"] == meta["end"]["camera"],
        "metrics":metrics}
    report.append(block)
    compact = {k:v for k,v in block.items() if k!="metrics"}
    compact["largest_frame_intervals_ms"] = sorted(intervals,reverse=True)[:4]
    compact["resolve_unique_values"] = len({r["VSM.ResolveAndFeedback_gpu_ms"] for r in rows})
    compact["resolve_longest_repeat"] = longest_repeat("VSM.ResolveAndFeedback_gpu_ms")
    print(json.dumps(compact))
out=pathlib.Path(__file__).resolve().parent
out.mkdir(parents=True, exist_ok=True)
(out/"sample-audit.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("PASS: all 72 metric rows independently recomputed and matched exported summary.")