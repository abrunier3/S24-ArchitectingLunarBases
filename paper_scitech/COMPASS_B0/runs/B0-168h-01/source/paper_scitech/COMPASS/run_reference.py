"""Archive the 7-day COMPASS reference through ECLIPSE's scenario dispatcher."""

import argparse
import csv
import gzip
import hashlib
import json
import platform
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import simpy

from S24.DES_pipeline_version.scenario_config import load_scenario_config
from S24.DES_pipeline_version.scenario_runner import run_scenario

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NASA_CASES = {
    "technical": "https://ntrs.nasa.gov/citations/20190029197",
    "journal": "https://doi.org/10.1061/%28ASCE%29AS.1943-5525.0001269",
}


def json_bytes(value):
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()


def archive_code(out):
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    paths = [
        *sorted((ROOT / "S24/DES_pipeline_version").glob("*.py")),
        ROOT / "clean_database/des/scenario_config.json",
        HERE / "run_reference.py",
        ROOT / "tests/test_batch_isru.py",
        ROOT / "pyproject.toml",
    ]
    hashes = {}
    for source in paths:
        relative = source.relative_to(ROOT)
        target = out / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[str(relative)] = hashlib.sha256(target.read_bytes()).hexdigest()
    return revision, hashes


def write_timeseries(out, samples):
    with (out / "hourly.csv").open("w", newline="") as stream:
        rows = []
        for sample in samples:
            row = {"time_hr": sample["time_hr"], "excavated_kg": sample["excavated_kg"],
                   "residue_dumped_kg": sample["residue_dumped_kg"],
                   **sample["liquid_stocks_kg"], **sample["energy"]}
            for actor, stats in sample["lines"].items():
                row.update({f"{actor}.{name}": value for name, value in stats.items()})
            for actor, stats in sample["vehicles"].items():
                row.update({f"{actor}.{name}": value for name, value in stats.items()})
            rows.append(row)
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def comparison(result):
    summary = result["summary"]
    duration = summary["time_hr"]
    days = duration / 24
    completed = sum(line["completed"] for line in summary["lines"].values())
    processed = sum(line["processed_kg"] for line in summary["lines"].values())
    oxygen = sum(line["oxygen_kg"] for line in summary["lines"].values())
    liquid = sum(line["liquid_kg"] for line in summary["lines"].values())
    lines = len(summary["lines"])
    events = result["events"]
    counts = Counter((event["actor"], event["mission"]) for event in events
                     if event["event"] == "mission_completed")
    starts = {}
    elapsed = {"regolith": [], "residue": []}
    for event in events:
        if event["event"] == "mission_started":
            starts[event["actor"]] = event["time_hr"]
        if event["event"] == "mission_completed":
            elapsed[event["mission"]].append(event["time_hr"] - starts[event["actor"]])
    rows = []

    def add(metric, unit, expected, actual):
        rows.append({
            "metric": metric, "unit": unit, "nasa_nominal": expected, "des": actual,
            "relative_delta_percent": (actual - expected) / expected * 100,
        })

    add("Completed batches per line per day", "batch/d", 14, completed / lines / days)
    add("Processed regolith, both lines", "kg/d", 2 * 14 * 9.3, processed / days)
    add("Oxygen extraction yield", "kg O2/kg feed", .121, oxygen / processed)
    add("Liquid oxygen released, full window", "kg/h", 1.30, liquid / duration)
    first_batch = next(event["time_hr"] for event in events if event["event"] == "batch_completed")
    add("Liquid oxygen released, since first oxygen extraction", "kg/h", 1.30,
        liquid / (duration - first_batch))
    add("Core electrical demand, peak", "kWe", 11.544, summary["energy"]["electric_peak_core_kw"])
    add("Heat received at reactors, peak", "kWth", 22.2, summary["energy"]["thermal_peak_to_reactors_kw"])
    for mission, cadence, minutes in (("regolith", 4, 20), ("residue", 3, 17)):
        add(f"Completed {mission} trips per vehicle per day", "trips/d", cadence,
            sum(count for (_, kind), count in counts.items() if kind == mission) / lines / days)
        add(f"{mission} mission service and travel (excluding initial positioning)", "min", minutes,
            60 * sum(elapsed[mission]) / len(elapsed[mission]))
    return rows


def main(out):
    config = json.loads((HERE / "reference.json").read_text())
    options = {"scenario_config": config}
    resolved = load_scenario_config(options)
    result = run_scenario(options)
    out.mkdir(parents=True, exist_ok=False)
    revision, hashes = archive_code(out)
    shutil.copyfile(HERE / "reference.json", out / "reference.json")
    (out / "resolved.json").write_bytes(json_bytes(resolved))
    (out / "summary.json").write_bytes(json_bytes({
        "run_id": out.name, **result["summary"],
        "max_event_mass_residual_kg": result["max_event_mass_residual_kg"],
        "comparison": comparison(result),
    }))
    (out / "results.json.gz").write_bytes(gzip.compress(json_bytes(result), mtime=0))
    write_timeseries(out, result["time_series"])
    artifacts = sorted(path for path in out.iterdir() if path.is_file())
    (out / "provenance.json").write_bytes(json_bytes({
        "run_id": out.name,
        "base_git_revision": revision,
        "source_sha256": hashes,
        "artifact_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in artifacts},
        "python": platform.python_version(),
        "simpy": simpy.__version__,
        "platform": platform.platform(),
        "sources": NASA_CASES,
    }))
    print(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="A new results directory")
    main(parser.parse_args().output)
