import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Compare isolated production VSM baseline/candidate GPU outputs.")
parser.add_argument("baseline", type=Path)
parser.add_argument("candidate", type=Path)
parser.add_argument("--output", type=Path)
args = parser.parse_args()
baseline = json.loads(args.baseline.read_text(encoding="utf-8-sig"))
candidate = json.loads(args.candidate.read_text(encoding="utf-8-sig"))
def key(group):
    return group["name"], group["mode"], group["frame"]
old = {key(group): group for group in baseline["groups"]}
new = {key(group): group for group in candidate["groups"]}
assert len(old) == len(baseline["groups"]) and len(new) == len(candidate["groups"])
assert old.keys() == new.keys(), "Probe configurations differ"
unchanged = []
nyquist = []
for identity, group in new.items():
    previous = old[identity]
    if group["mode"] != 1:
        assert len(group["values"]) == len(previous["values"])
        differences = sum(a != b for a, b in zip(group["values"], previous["values"]))
        unchanged.append({"name": identity[0], "mode": identity[1], "frame": identity[2],
                          "values": len(group["values"]), "differences": differences})
    elif group["name"] in ("pattern-2", "pattern-3", "pattern-4"):
        old_values = [value["y"] for value in previous["values"]]
        new_values = [value["y"] for value in group["values"]]
        nyquist.append({"name": identity[0], "baselineMin": min(old_values), "baselineMax": max(old_values),
                       "candidateMin": min(new_values), "candidateMax": max(new_values),
                       "candidateMaximumErrorFromHalf": max(abs(v - .5) for v in new_values)})
result = {"baseline": str(args.baseline), "candidate": str(args.candidate),
          "baselineFailedGroups": [key(g) for g in baseline["groups"] if g["failures"]],
          "candidateFailedGroups": [key(g) for g in candidate["groups"] if g["failures"]],
          "candidateSuccess": candidate["success"], "baselineError": baseline.get("error"),
          "candidateError": candidate.get("error"), "comparedUnchangedValues": sum(g["values"] for g in unchanged),
          "unchangedValueDifferences": sum(g["differences"] for g in unchanged),
          "unchangedGroups": unchanged, "nyquist": nyquist}
text = json.dumps(result, indent=2, ensure_ascii=False)
if args.output:
    args.output.write_text(text + "\n", encoding="utf-8")
print(text)