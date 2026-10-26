#!/usr/bin/env python3
"""Reproduce every computed table, number and figure in the ICAISC 2027 paper.

    python reproduce.py            # verify data, run all steps, then check
    python reproduce.py --jobs 4   # same, running independent steps in parallel
    python reproduce.py --check    # only compare existing out/ with the paper

No network access is needed. Inputs are read from data/ (checksums in
data/SHA256SUMS); outputs are written to out/. Each step's console output goes
to logs/steps/<step>.log and this script's own console to logs/reproduce.log.
"""
import argparse
import hashlib
import os
import platform
import subprocess
import sys
import threading
import time
from datetime import datetime
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CODE, DATA, OUT, LOGS = ROOT / "code", ROOT / "data", ROOT / "out", ROOT / "logs"

# (name, arguments, steps it must wait for, what it backs in the paper)
STEPS = [
    ("scan01", ["scan01.py"], [], "Table I"),
    ("scan02_jma", ["scan02.py", "jma"], [], "Table II"),
    ("scan02_openmeteo", ["scan02.py", "openmeteo"], [], "Open-Meteo check of Table II"),
    ("scan03", ["scan03.py"], [], "Tables III and IV"),
    ("scan04", ["scan04.py"], [], "Fig. 3, lead-time text, gain kept"),
    ("scan05", ["scan05.py"], ["scan04"], "baselines, nested tuning, busy-day definitions"),
    ("scan06", ["scan06.py"], [], "faces vs plates paragraph"),
    ("scan07", ["scan07.py"], [], "window sensitivity, faces warning intervals"),
    ("scan08", ["scan08_data_facts.py"], [], "Data-section facts"),
    ("scan09", ["scan09_faces_warning_counts.py"], [], "faces warning day counts"),
    ("fig_timeseries", ["fig_timeseries.py"], [], "Fig. 2"),
    # scan05 also draws an earlier version of Fig. 3; fig_leadtime must run after it.
    ("fig_leadtime", ["fig_leadtime.py"], ["scan04", "scan05"], "Fig. 3"),
    ("cold_start", ["cold_start.py"], [], "cold start text and Fig. 4"),
]
HEAVY_FIRST = ["cold_start", "scan04", "scan07", "scan03", "scan05", "scan06", "scan09",
               "scan02_jma", "scan02_openmeteo", "scan01", "scan08", "fig_timeseries",
               "fig_leadtime"]

_lock = threading.Lock()
_log = None


def say(msg=""):
    with _lock:
        print(msg, flush=True)
        if _log:
            _log.write(msg + "\n"); _log.flush()


def verify_data():
    bad = 0
    lines = (DATA / "SHA256SUMS").read_text().split("\n")
    for line in filter(None, lines):
        digest, name = line.split(maxsplit=1)
        got = hashlib.sha256((DATA / name).read_bytes()).hexdigest()
        if got != digest:
            say(f"  CHECKSUM MISMATCH {name}"); bad += 1
    say(f"Data: {len(list(filter(None, lines)))} files, "
        + ("all checksums match data/SHA256SUMS" if not bad else f"{bad} mismatches"))
    return bad == 0


def environment():
    say(f"Started {datetime.now().astimezone():%Y-%m-%d %H:%M:%S %Z}")
    say(f"Python {platform.python_version()} on {platform.platform()}, {os.cpu_count()} CPUs")
    pins = [l.split("==")[0] for l in (ROOT / "requirements.txt").read_text().split() if "==" in l]
    say("Packages: " + ", ".join(f"{p} {metadata.version(p)}" for p in pins))


def run_step(name, args, py):
    log = LOGS / "steps" / f"{name}.log"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
    # Override inherited thread counts to reduce BLAS/OpenMP solver variation.
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[key] = "1"
    t0 = time.time()
    say(f"  start  {name}")
    with open(log, "w") as fh:
        rc = subprocess.call([py, *args], cwd=CODE, stdout=fh, stderr=subprocess.STDOUT, env=env)
    dt = time.time() - t0
    say(f"  {'done ' if rc == 0 else 'FAILED'} {name} in {dt / 60:.1f} min" + (f" (exit {rc}, see {log.relative_to(ROOT)})" if rc else ""))
    return rc


def run_all(jobs, py):
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    (OUT / "coldstart").mkdir(parents=True, exist_ok=True)
    (LOGS / "steps").mkdir(parents=True, exist_ok=True)
    spec = {n: (a, d) for n, a, d, _ in STEPS}
    order = [n for n, *_ in STEPS] if jobs == 1 else HEAVY_FIRST
    pending, running, status = list(order), {}, {}
    cond = threading.Condition()

    def worker(n):
        rc = run_step(n, spec[n][0], py)
        with cond:
            status[n] = rc; running.pop(n); cond.notify_all()

    with cond:
        while pending or running:
            ready = [n for n in pending if all(status.get(d) == 0 for d in spec[n][1])]
            blocked = [n for n in pending if any(status.get(d, 0) != 0 for d in spec[n][1])]
            for n in blocked:
                pending.remove(n); status[n] = -1; say(f"  skip   {n} (a prerequisite failed)")
            while ready and len(running) < jobs:
                n = ready.pop(0); pending.remove(n)
                running[n] = threading.Thread(target=worker, args=(n,)); running[n].start()
            if running:
                cond.wait()
            elif pending and not ready:
                break
    return all(rc == 0 for rc in status.values())


def main():
    global _log
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jobs", type=int, default=1, help="steps to run at once (default 1)")
    ap.add_argument("--check", action="store_true", help="skip the run; only compare out/ with the paper")
    args = ap.parse_args()
    LOGS.mkdir(exist_ok=True)
    _log = open(LOGS / ("check.log" if args.check else "reproduce.log"), "w")
    environment()
    ok = verify_data()
    if not ok:
        say("Stopping: data/ does not match the published snapshot."); sys.exit(2)
    if not args.check:
        t0 = time.time()
        say(f"Running {len(STEPS)} steps with {args.jobs} job(s); per-step logs in logs/steps/")
        ok = run_all(max(1, args.jobs), sys.executable)
        say(f"Pipeline {'finished' if ok else 'FAILED'} in {(time.time() - t0) / 60:.1f} min wall time")
    sys.path.insert(0, str(CODE))
    import check
    passed = check.main(ROOT, say)
    say(f"Finished {datetime.now().astimezone():%Y-%m-%d %H:%M:%S %Z}")
    sys.exit(0 if ok and passed else 1)


if __name__ == "__main__":
    main()
